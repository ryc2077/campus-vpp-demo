# overview 场景拼装（总览场景，只拼 assets/blender/overview/ 的 19 件）
# 用法（无头，不渲染）：
#   xvfb-run -a -s "-screen 0 1280x720x24" <blender> -b --python overview.py
# 做法：全局坐标直接 append，不移位置；只写本脚本、
#   assets/blender/scenes/overview.blend、assets/models/scenes/overview.glb。
# 排除：相机/灯光/光照探针、名字含 preview 的预览物（含各件的
#   Ground_PreviewOnly / PREVIEW_*）、flag-lamp 的 CamTarget 空物体。
#   ov-parking 的 3 个 EMPTY（ov-parking_blue/grey/red）是 3 辆车的父级，
#   必须保留，否则车身子物体会丢变换。
# 拼装补齐（场景内新建，名前缀 OV_ASSEMBLY_，不是单件）：
#   地面 340x340 #69b45e（campus.json ground）；池塘水面椭圆盘
#   （campus.json pond [82,78] rx11 rz8 -> Blender (82,-78)）；配电房外壳
#   （campus.json buildings.dist [48,-30] 16x10 高 8m color #dfe9f2）。
# 缺口：户外变压器（campus.json transformer [74,-30]）无 Blender 件，留空。
# 绿地重叠：实测 ov-dorm 的 dorm_lawn_between 与 ov-lawn 在宿舍区无 XY
#   重叠（见脚本内检查打印），不做高差调整，调整量 0。
#   池塘处 ov-lawn 的 Lawn_Pond_Grass_* 草丛会穿出水面，场景副本内把
#   它们下移 0.5m 藏到水面/地面之下（只动场景副本，不改件文件）。

import bpy
import os
import datetime
from mathutils import Vector

_d = os.path.abspath(__file__)
for _ in range(4):  # scenes -> blender -> assets -> demo-godot
    _d = os.path.dirname(_d)
ROOT = _d
# ROOT = .../files/demo-godot
OV_DIR = os.path.join(ROOT, "assets", "blender", "overview")
OUT_BLEND = os.path.join(ROOT, "assets", "blender", "scenes", "overview.blend")
OUT_GLB = os.path.join(ROOT, "assets", "models", "scenes", "overview.glb")

PARTS = [
    "ov-bldA", "ov-bldB", "ov-bldC", "ov-windows-roofs", "ov-lib",
    "ov-gym", "ov-lab", "ov-tower", "ov-canteen", "ov-dorm",
    "ov-road-main", "ov-road-walk", "ov-track", "ov-field", "ov-trees",
    "ov-lawn", "ov-flag-lamp", "ov-gate", "ov-parking",
]

os.makedirs(os.path.dirname(OUT_BLEND), exist_ok=True)
os.makedirs(os.path.dirname(OUT_GLB), exist_ok=True)


def utc(ts):
    return datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC")


def list_names(path):
    with bpy.data.libraries.load(path, link=False) as (src, _dst):
        return list(src.objects)


def hex_mat(name, hexcolor, rough=0.85):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    h = hexcolor.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    bsdf.inputs["Base Color"].default_value = (r, g, b, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    return mat


def world_bbox(obj):
    pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    xs = [p.x for p in pts]
    ys = [p.y for p in pts]
    zs = [p.z for p in pts]
    return (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))


# ---------- 1. 新建空场景 ----------
bpy.ops.wm.read_factory_settings(use_empty=True)

total_kept = 0
for pid in PARTS:
    path = os.path.join(OV_DIR, pid + ".blend")
    mtime = utc(os.path.getmtime(path))
    names = list_names(path)
    before = len(bpy.context.scene.objects)
    bpy.ops.wm.append(filepath=path, directory=path + "/Object/",
                      files=[{"name": n} for n in names], link=False)
    # 删预览/相机/灯光/探针/CamTarget（只删本次拼进来的场景对象）
    removed = []
    for obj in list(bpy.context.scene.objects):
        if (obj.type in ("CAMERA", "LIGHT", "LIGHT_PROBE")
                or "preview" in obj.name.lower()
                or obj.name == "CamTarget"):
            removed.append(obj.name)
            bpy.data.objects.remove(obj, do_unlink=True)
    kept = len(bpy.context.scene.objects) - before
    total_kept += kept
    print("APPEND %s src=%d kept=%d removed=%d mtime=%s removed_names=%s"
          % (pid, len(names), kept, len(removed), mtime, removed))
print("APPEND TOTAL kept=%d scene_objects=%d"
      % (total_kept, len(bpy.context.scene.objects)))

# ---------- 2. 绿地重叠检查：ov-dorm 楼间绿地 vs ov-lawn ----------
dorm_lawn = bpy.data.objects.get("dorm_lawn_between")
if dorm_lawn is not None:
    dbb = world_bbox(dorm_lawn)
    print("DORM-LAWN dorm_lawn_between bbox x[%.2f,%.2f] y[%.2f,%.2f] z[%.3f,%.3f]"
          % dbb)
    overlap = []
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH" or not obj.name.startswith("Lawn_"):
            continue
        obb = world_bbox(obj)
        if (obb[1] >= dbb[0] and obb[0] <= dbb[1]
                and obb[3] >= dbb[2] and obb[2] <= dbb[3]):
            overlap.append((obj.name, tuple(round(v, 3) for v in obb)))
    print("DORM-LAWN ov-lawn overlap in dorm rect: %s" % (overlap,))
    if overlap:
        # 有穿插才抬高楼间绿地 0.30m（本次实测无重叠，此分支不应触发）
        dorm_lawn.location.z += 0.30
        print("DORM-LAWN ADJUST +0.30m on dorm_lawn_between (scene copy only)")
    else:
        print("DORM-LAWN ADJUST none (no overlap, delta=0)")
else:
    print("DORM-LAWN WARNING dorm_lawn_between not found")

# ---------- 3. 拼装补齐（场景内新建，OV_ASSEMBLY_ 前缀） ----------
# 3a. 地面 340x340，campus.json ground color #69b45e；顶面 z=-0.05，
#     避开各件 z=0 的底面共面（防 z-fighting），视觉上仍为地面。
ground_mat = hex_mat("OV_ASSEMBLY_ground_mat", "#69b45e", 0.95)
bpy.ops.mesh.primitive_plane_add(size=340.0, location=(0.0, 0.0, -0.05))
ground = bpy.context.active_object
ground.name = "OV_ASSEMBLY_ground"
ground.data.materials.append(ground_mat)
print("ASSEMBLY ground 340x340 @z=-0.05 color=#69b45e")

# 3b. 池塘水面椭圆盘：Godot [82,78] rx11 rz8 -> Blender (82,-78)，
#     rx=11（x），ry=8（y）；圆柱顶面 z=0.10、底面 z=-0.02。
#     campus.json 无 pond 颜色，水面蓝 #2F7FC4 为拼装自选。
pond_mat = hex_mat("OV_ASSEMBLY_pond_mat", "#2F7FC4", 0.25)
bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=1.0, depth=0.12,
                                    location=(82.0, -78.0, 0.04))
pond = bpy.context.active_object
pond.name = "OV_ASSEMBLY_pond"
pond.scale = (11.0, 8.0, 1.0)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
pond.data.materials.append(pond_mat)
print("ASSEMBLY pond ellipse center=(82,-78) rx=11 ry=8 top z=0.10 color=#2F7FC4")

# 池塘处 ov-lawn 的草丛（Lawn_Pond_Grass_*，顶高约 0.4）会穿出水面：
# 场景副本内下移 0.5m 藏到水面/地面之下，只动场景副本，不改件文件。
buried = []
for obj in list(bpy.context.scene.objects):
    if obj.name.startswith("Lawn_Pond_Grass_"):
        obj.location.z -= 0.5
        buried.append(obj.name)
print("ASSEMBLY pond grass buried -0.5m: %s" % (buried,))

# 3c. 配电房外壳：campus.json buildings.dist，Godot [48,-30] -> Blender
#     (48,30)，16x10，高 8m，color #dfe9f2；屋顶板深灰 #424A52（SPEC §3）。
dist_mat = hex_mat("OV_ASSEMBLY_dist_mat", "#dfe9f2", 0.85)
roof_mat = hex_mat("OV_ASSEMBLY_dist_roof_mat", "#424A52", 0.8)
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(48.0, 30.0, 4.0))
dist = bpy.context.active_object
dist.name = "OV_ASSEMBLY_dist_body"
dist.dimensions = (16.0, 10.0, 8.0)
dist.data.materials.append(dist_mat)
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(48.0, 30.0, 8.15))
dist_roof = bpy.context.active_object
dist_roof.name = "OV_ASSEMBLY_dist_roof"
dist_roof.dimensions = (16.6, 10.6, 0.3)
dist_roof.data.materials.append(roof_mat)
print("ASSEMBLY dist body 16x10x8 @ (48,30) color=#dfe9f2 + roof slab 16.6x10.6x0.3")

# 缺口：户外变压器 campus.json transformer Godot [74,-30] -> Blender
# (74,30)，无 Blender 件，留空，不编造。
print("GAP transformer at Blender (74,30): no Blender part exists, left empty")

print("SCENE objects=%d (appended=%d + assembly=4)"
      % (len(bpy.context.scene.objects), total_kept))

# ---------- 4. 存 .blend，全选导出 .glb ----------
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
print("SAVED %s" % OUT_BLEND)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(filepath=OUT_GLB, export_format="GLB",
                          use_selection=True, export_apply=True)
print("EXPORTED %s" % OUT_GLB)

# ---------- 5. 回读验证 ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=OUT_GLB)
n = len(bpy.context.scene.objects)
print("VERIFY reimport objects=%d" % n)
if n <= 0:
    raise RuntimeError("glTF reimport returned 0 objects")
print("DONE overview")
