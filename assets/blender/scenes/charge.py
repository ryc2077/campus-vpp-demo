# charge 场景拼装：把充电区 4 件 append 成一个场景（全局坐标，不移位置）
# 件：ch-piles / ch-cars / ch-marking / ch-canopy，Blender 中心 (44, -76)
# 排除：相机 / 灯光 / 太阳 / 反射探针 / 预览用地坪（Ground_PreviewOnly、PREVIEW_Ground）
# 做法：wm.append 逐个 append（ch-cars 因父子层级须批量 append，见下文）；存 charge.blend；
# 全选导出 charge.glb（GLB，use_selection=True，export_apply=True，默认 +Y up，不手动旋转）；
# 导出后 import_scene.gltf 回读验证，无 Error/Traceback 才算，末尾打印 DONE charge。
# 运行：xvfb-run -a -s "-screen 0 1280x720x24" <blender> -b --python charge.py
import bpy
import json
import os
import struct
from mathutils import Vector

ROOT = os.path.dirname(os.path.abspath(__file__))          # .../assets/blender/scenes
BLENDER_DIR = os.path.dirname(ROOT)                        # .../assets/blender
ASSETS_DIR = os.path.dirname(BLENDER_DIR)                  # .../assets
PARTS = ["ch-piles", "ch-cars", "ch-marking", "ch-canopy"]
BLEND_OUT = os.path.join(ROOT, "charge.blend")
GLB_OUT = os.path.join(ASSETS_DIR, "models", "scenes", "charge.glb")

SKIP_TYPES = {"CAMERA", "LIGHT", "LIGHT_PROBE"}
SKIP_NAMES = {"Ground_PreviewOnly", "PREVIEW_Ground"}


def wbbox(o):
    vs = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return (min(v.x for v in vs), max(v.x for v in vs),
            min(v.y for v in vs), max(v.y for v in vs),
            min(v.z for v in vs), max(v.z for v in vs))


def overlap3(a, b):
    ox = min(a[1], b[1]) - max(a[0], b[0])
    oy = min(a[3], b[3]) - max(a[2], b[2])
    oz = min(a[5], b[5]) - max(a[4], b[4])
    return (ox, oy, oz) if (ox > 0 and oy > 0 and oz > 0) else None


# --- 新建空场景 ---
bpy.ops.wm.read_factory_settings(use_empty=True)

# --- append 各件对象 ---
# ch-piles / ch-marking / ch-canopy：对象均无父级，逐个 bpy.ops.wm.append，结果与源文件一致。
# ch-cars：65 个 mesh 都父级于 3 个 EMPTY，逐个 wm.append 会给每个 mesh 各复制一份父级
#   EMPTY（实测 195 个 mesh → 195 个重复父级）；改用一次 libraries.load(link=False)
#   批量 append（与 wm.append 同一套底层库加载机制），实测父子关系完整、无重复。
#   排除：相机 / 灯光 / 太阳 / 反射探针 / 预览用地坪（Ground_PreviewOnly、PREVIEW_Ground）
appended = {}
for part in PARTS:
    path = os.path.join(BLENDER_DIR, "charge", part + ".blend")
    with bpy.data.libraries.load(path) as (src, _dst):
        names = [n for n in src.objects
                 if n not in SKIP_NAMES and not n.startswith("PREVIEW")]
    if part == "ch-cars":
        with bpy.data.libraries.load(path, link=False) as (_src, dst):
            dst.objects = list(names)
        kept = 0
        for o in list(dst.objects):
            if o is None or o.type in SKIP_TYPES:
                continue
            bpy.context.scene.collection.objects.link(o)
            kept += 1
        appended[part] = kept
        print(f"APPEND {part}: batch-append {len(names)} names, kept {kept}")
        continue
    for name in names:
        bpy.ops.wm.append(filepath=os.path.join(path, "Object", name),
                          directory=os.path.join(path, "Object"),
                          filename=name)
    # 删掉本件带进来的相机 / 灯光 / 太阳 / 反射探针
    removed = []
    for o in list(bpy.context.scene.objects):
        if o.type in SKIP_TYPES:
            removed.append(f"{o.type}:{o.name}")
            bpy.data.objects.remove(o, do_unlink=True)
    appended[part] = len(names) - len(removed)
    print(f"APPEND {part}: appended {len(names)}, removed {removed}, kept {appended[part]}")

bpy.context.view_layer.update()
scene_objs = list(bpy.context.scene.objects)
print(f"SCENE total objects: {len(scene_objs)}")

# --- 位置检查（只读，不改件） ---
# 车位：space0i_line_west/east/south/north
bays = {}
for i in (1, 2, 3, 4):
    w = bpy.data.objects.get(f"space0{i}_line_west")
    e = bpy.data.objects.get(f"space0{i}_line_east")
    s = bpy.data.objects.get(f"space0{i}_line_south")
    n = bpy.data.objects.get(f"space0{i}_line_north")
    if w and e and s and n:
        bays[i] = (wbbox(w)[0], wbbox(e)[1], wbbox(s)[2], wbbox(n)[3])  # xmin,xmax,ymin,ymax
        print(f"CHECK bay{i}: x[{bays[i][0]:.2f},{bays[i][1]:.2f}] y[{bays[i][2]:.2f},{bays[i][3]:.2f}] "
              f"center_x={(bays[i][0]+bays[i][1])/2:.2f} w={bays[i][1]-bays[i][0]:.2f} l={bays[i][3]-bays[i][2]:.2f}")

# 充电桩：pN_body
piles = {}
for i in (1, 2, 3, 4):
    o = bpy.data.objects.get(f"ch-piles_p{i}_body")
    if o:
        bb = wbbox(o)
        piles[i] = bb
        cx = (bb[0] + bb[1]) / 2
        print(f"CHECK pile{i}: center_x={cx:.2f} y=[{bb[2]:.2f},{bb[3]:.2f}] z=[{bb[4]:.2f},{bb[5]:.2f}] "
              f"vs bay{i} center_x={(bays[i][0]+bays[i][1])/2:.2f} dx={cx-(bays[i][0]+bays[i][1])/2:.2f}")

# 车辆：ch-cars_<color>_roof 是车身主 mesh（R2-T19 换装后兼任 Godot
# SOC 条锚点，见 ch-cars.py 头注；旧 _body 已无独立 mesh）。整车包围盒
# 取 empty 下全部子 mesh 的并集（车身 + 3 个轮 mesh）。
cars = {}
for color in ("blue", "red", "white"):
    main = bpy.data.objects.get(f"ch-cars_{color}_roof")
    empty = bpy.data.objects.get(f"ch-cars_{color}")
    if main and empty:
        kids = [c for c in empty.children if c.type == 'MESH']
        assert len(kids) == 4, f"car {color}: expected 4 child meshes, got {len(kids)}"
        bbs = [wbbox(c) for c in kids]
        full = (min(b[0] for b in bbs), max(b[1] for b in bbs),
                min(b[2] for b in bbs), max(b[3] for b in bbs),
                min(b[4] for b in bbs), max(b[5] for b in bbs))
        cars[color] = full
        rot_z = empty.matrix_world.to_euler().z if empty else 0.0
        front = "north(+y)" if rot_z > 0 else "south(-y)"
        cx = (full[0] + full[1]) / 2
        cy = (full[2] + full[3]) / 2
        print(f"CHECK car {color}: center=({cx:.2f},{cy:.2f}) x[{full[0]:.2f},{full[1]:.2f}] "
              f"y[{full[2]:.2f},{full[3]:.2f}] z[{full[4]:.2f},{full[5]:.2f}] front={front} rot_z={rot_z:.2f}")
        # 落在哪个车位内
        inside = [i for i, b in bays.items()
                  if full[0] >= b[0] and full[1] <= b[1] and full[2] >= b[2] and full[3] <= b[3]]
        print(f"CHECK car {color}: inside bays {inside if inside else 'NONE'}")
        # 与各桩 body/roof 的三维穿插
        for i, pb in piles.items():
            ov = overlap3(full, pb)
            print(f"CHECK car {color} vs pile{i}: {'INTERSECT overlap x/y/z = (%.2f, %.2f, %.2f)m' % ov if ov else 'no 3D overlap'}")

# 雨棚：CanopyRoof + 立柱
roof = bpy.data.objects.get("CanopyRoof")
if roof:
    rb = wbbox(roof)
    print(f"CHECK canopy roof: x[{rb[0]:.2f},{rb[1]:.2f}] y[{rb[2]:.2f},{rb[3]:.2f}] z[{rb[4]:.2f},{rb[5]:.2f}]")
    for i, b in bays.items():
        cov = rb[0] <= b[0] and rb[1] >= b[1] and rb[2] <= b[2] and rb[3] >= b[3]
        print(f"CHECK canopy covers bay{i}: {cov} (margin x-={b[0]-rb[0]:.2f} x+={rb[1]-b[1]:.2f} "
              f"y-={b[2]-rb[2]:.2f} y+={rb[3]-b[3]:.2f})")
    for color, cb in cars.items():
        cov = rb[0] <= cb[0] and rb[1] >= cb[1] and rb[2] <= cb[2] and rb[3] >= cb[3]
        print(f"CHECK canopy covers car {color}: {cov} (car x[{cb[0]:.2f},{cb[1]:.2f}] roof x[{rb[0]:.2f},{rb[1]:.2f}])")
for i in (1, 2, 3, 4):
    c = bpy.data.objects.get(f"CanopyColumn_{i}")
    if c:
        print(f"CHECK canopy column{i}: mw={tuple(round(v, 2) for v in c.matrix_world.translation)}")

# --- 材质去重 (2026-11-23)：与 pv 场景同一根因 —— ch-piles/ch-marking/
#   ch-canopy 是逐个 bpy.ops.wm.append，每次 append 都把材质当新数据块
#   载入，场景 GLB 曾有 117 个材质（仅 24 个唯一，93 个重复）。
#   把 "Name.NNN" 重复项 remap 到规范 "Name" 材质再删无用副本。
#   件内材质基名互不重叠（ch-piles_*/Car*/Marking_*/Canopy*），按基名合并安全。
#   预期唯一：piles 7 + cars 9 + marking 3 + canopy 5 = 24。 ---
n_mat_before = len(bpy.data.materials)
canon = {}
for mat in list(bpy.data.materials):
    base = mat.name.split(".")[0]
    if base in canon:
        mat.user_remap(canon[base])
    else:
        canon[base] = mat
for mat in list(bpy.data.materials):
    if mat.users == 0:
        bpy.data.materials.remove(mat)
print(f"MATERIAL DEDUPE: {n_mat_before} -> {len(bpy.data.materials)} "
      f"unique: {sorted(canon)}")
assert len(bpy.data.materials) == 24, (
    f"expected 24 unique materials, got {len(bpy.data.materials)}")

# --- 存 .blend ---
os.makedirs(os.path.dirname(BLEND_OUT), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_OUT)
print(f"SAVED {BLEND_OUT}")

# --- 全选导出 .glb（默认 +Y up，不手动旋转） ---
bpy.ops.object.select_all(action="SELECT")
os.makedirs(os.path.dirname(GLB_OUT), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=GLB_OUT, export_format="GLB",
                          use_selection=True, export_apply=True)
print(f"EXPORTED {GLB_OUT}")

# --- 直读 GLB JSON 核对材质数 ---
with open(GLB_OUT, "rb") as f:
    _raw = f.read(20)
    _jlen = struct.unpack("<I", _raw[12:16])[0]
    f.seek(20)
    _gltf = json.loads(f.read(_jlen))
print(f"GLB JSON materials: {len(_gltf.get('materials', []))} "
      f"meshes: {len(_gltf.get('meshes', []))} "
      f"nodes: {len(_gltf.get('nodes', []))}")
assert len(_gltf.get("materials", [])) == 24, (
    f"GLB has {len(_gltf.get('materials', []))} materials, expected 24")

# --- 回读验证 ---
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB_OUT)
n = len(bpy.context.scene.objects)
print(f"REIMPORT charge.glb objects: {n}, materials: {len(bpy.data.materials)}")
assert len(bpy.data.materials) == 24, (
    f"reimported {len(bpy.data.materials)} materials, expected 24")
for o in bpy.context.scene.objects:
    if o.type not in ("MESH", "EMPTY", "CURVE"):
        print(f"REIMPORT note: {o.type} {o.name}")
print("DONE charge")
