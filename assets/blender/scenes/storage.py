# storage 场景拼装：把储能 5 件 append 成一个场景（只做 storage，不碰其他场景/件）
# 做法：bpy.ops.wm.append 各件 .blend 里的本件对象（排除相机/灯光/太阳与 Preview_* 示意件，
#   Preview_* 是各件 .py 里只做预览对照用的示意柜体/地面，不属于本件导出范围，见各件 .py 的
#   part_objs 选择逻辑）；全局坐标直接 append，不移位置；Blender 中心 (64, 30)。
# 待定口径处理（见脚本内注释）：
#   1) 前门面冲突：st-cabinet 南面浮雕（把手/把手座）与 st-doors 双开门板包围盒重叠 →
#      把冲突的柜体浮雕对象在场景副本里沿 +y（柜体法向往里）内缩，数值 = 该对象与门板的 y 向重叠量。
#      只动场景里的副本，不改件的 .py/.blend。
#   2) 拼装补壳体：Godot _build_storage 的 8.6x4.4x4.0 壳体 + 屋顶板（Godot 尺寸 x,y,z；
#      按 SPEC §0 换算 Blender (x,y,z)=Godot(x,-z,y)，即 Blender 尺寸 8.6(x) x 4.0(y) x 4.4(z)，
#      中心 (64,30,2.85)；屋顶板 Godot 9.2x0.35x4.6 → Blender 9.2 x 4.6 x 0.35，中心 (64,30,5.2)）。
#      壳体颜色 SPEC §3 储能柜深绿灰 #3E5A50；屋顶板 #424A52（屋顶深灰）。对象名带 ASSEMBLY_ADDED 注明拼装补的。
# 返修 2026-11-22：① 壳体改半透明（Principled Alpha 0.35，BLEND），屋顶板保持不透明，
#   否则实心壳体会盖住内部 4 台柜/线槽/接线箱；② 柜体竖拉手经 +y 内缩 0.030 后仍有
#   0.002 埋在门板内，本次在场景里再沿 +y 内缩 0.002 清零（st-doors 的 8 根横杆把手与门板相切，无重叠，不动）。
# 交付：本脚本 + storage.blend + assets/models/scenes/storage.glb（全选导出，默认 +Y up，不手动旋转）
# 新规矩：渲染全部走 GitHub Actions，本地不渲染、不出预览图。
import bpy
import math
import os
from mathutils import Vector

ROOT = "/home/hatch/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot"
STORE_DIR = os.path.join(ROOT, "assets/blender/storage")
BLEND_PATH = os.path.join(ROOT, "assets/blender/scenes/storage.blend")
GLB_PATH = os.path.join(ROOT, "assets/models/scenes/storage.glb")

PARTS = ["st-cabinet", "st-doors", "st-cables", "st-base", "st-fence"]

# ---------- clean scene ----------
bpy.ops.wm.read_factory_settings(use_empty=True)


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_to_linear(h):
    h = h.lstrip("#")
    return tuple(srgb_to_linear(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4))


def make_material(name, hex_color, roughness=0.5, metallic=0.2):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*hex_to_linear(hex_color), 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


# ---------- PBR 贴图（2026-11-24 v3b：屋顶板挂下载的 CC0 贴图，替代纯色） ----------
# blue_metal_plate 染 #424A52；Base Color+Roughness+Normal 三件套直连 BSDF。
# 只动不透明屋顶板；半透明壳体（BLEND α=0.35）不动，不贴不透明纹理。
TEX_DIR = os.path.join(ROOT, "assets/blender/scenes/storage_textures")

def _load_tex(fname, colorspace):
    path = os.path.join(TEX_DIR, fname)
    img = bpy.data.images.load(path, check_existing=True)
    img.colorspace_settings.name = colorspace
    img.filepath = "//" + os.path.basename(TEX_DIR) + "/" + fname
    return img

def add_pbr(mat, color=None, rough=None, normal=None):
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    for sock in ("Base Color", "Roughness", "Normal"):
        for link in list(bsdf.inputs[sock].links):
            nt.links.remove(link)
    if color:
        bsdf.inputs["Base Color"].default_value = (1.0, 1.0, 1.0, 1.0)
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = _load_tex(color, "sRGB")
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    if rough:
        bsdf.inputs["Roughness"].default_value = 1.0
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = _load_tex(rough, "Non-Color")
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Roughness"])
    if normal:
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = _load_tex(normal, "Non-Color")
        nmap = nt.nodes.new("ShaderNodeNormalMap")
        nmap.space = "TANGENT"
        nt.links.new(tex.outputs["Color"], nmap.inputs["Color"])
        nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    return mat

def _check_pbr(mat):
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    texs = [n for n in nt.nodes if n.type == "TEX_IMAGE"]
    assert len(texs) >= 3, f"{mat.name}: expected 3 texture nodes, got {len(texs)}"
    assert bsdf.inputs["Base Color"].is_linked, f"{mat.name}: Base Color not linked"
    assert bsdf.inputs["Roughness"].is_linked, f"{mat.name}: Roughness not linked"
    assert bsdf.inputs["Normal"].is_linked, f"{mat.name}: Normal not linked"
    print(f"PBR CHECK PASS: {mat.name} color/rough/normal -> "
          f"{[t.image.name if t.image else '?' for t in texs]}")


def list_part_objects(blend_path):
    """只列出本件对象：排除相机/灯光/太阳与 Preview_* 预览示意件。"""
    with bpy.data.libraries.load(blend_path, link=False) as (data_from, _data_to):
        names = [n for n in data_from.objects]
    # 类型要读出来才能筛 CAMERA/LIGHT：用只读方式再取一次类型信息 via libraries.load 的 data_from 只有名字；
    # 类型改用 append 后筛（见 append_part），这里只筛 Preview_*。
    return [n for n in names if not n.startswith("Preview_")]


def append_part(blend_path):
    names = list_part_objects(blend_path)
    before = set(bpy.data.objects)
    try:
        bpy.ops.wm.append(filepath=blend_path, directory=blend_path + "/Object/",
                          files=[{"name": n} for n in names], link=False)
    except Exception as e:
        print("wm.append failed, fallback to libraries.load:", e)
        with bpy.data.libraries.load(blend_path, link=False) as (data_from, data_to):
            data_to.objects = [n for n in data_from.objects if n in names]
    added = [ob for ob in bpy.data.objects if ob not in before]
    # 排除相机/灯光/太阳（各件目前没有，但按规约筛掉）；漏网的 Preview_* 也筛掉
    kept, dropped = [], []
    for ob in added:
        if ob.type in {"CAMERA", "LIGHT"} or ob.name.startswith("Preview_"):
            dropped.append(ob)
        else:
            kept.append(ob)
    for ob in dropped:
        bpy.data.objects.remove(ob, do_unlink=True)
    # 确保全部挂进场景集合（wm.append 正常已挂接，防御性补挂）
    coll = bpy.context.scene.collection
    for ob in kept:
        if ob.name not in coll.objects:
            coll.objects.link(ob)
    bpy.context.view_layer.update()
    return kept


def world_bbox(ob):
    vs = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return tuple((min(v[i] for v in vs), max(v[i] for v in vs)) for i in range(3))


def overlap_1d(a, b):
    return min(a[1], b[1]) - max(a[0], b[0])


# ---------- 1) append 5 件 ----------
part_counts = {}
all_part_objs = []
for part in PARTS:
    path = os.path.join(STORE_DIR, part + ".blend")
    objs = append_part(path)
    part_counts[part] = len(objs)
    all_part_objs.extend(objs)
    print(f"appended {part}: {len(objs)} objects from {path}")

print("part counts:", part_counts, "total:", len(all_part_objs))

# ---------- 2) 前门面冲突检查：st-cabinet 南面浮雕 vs st-doors 双开门板 ----------
# 门板：st-doors 里名字含 _Door_L/_Door_R 的对象（不含把手/百叶/风扇罩）
# 柜体浮雕：st-cabinet 里名字含 DoorSeam/Grille/Handle/Screen/LED 且位于南面（ymin < 29.5）的对象
bpy.context.view_layer.update()
door_panels = [ob for ob in all_part_objs
               if ("_Door_L" in ob.name or "_Door_R" in ob.name)
               and ob.name.split("_")[0] in ("Battery1", "Battery2", "Battery3", "PCS")]
cab_relief = [ob for ob in all_part_objs
              if any(k in ob.name for k in ("DoorSeam", "Grille", "Handle", "Screen", "LED"))
              and ("Cabinet" in ob.name)
              and world_bbox(ob)[1][0] < 29.5]
print(f"door panels: {len(door_panels)}, cabinet south relief: {len(cab_relief)}")
door_boxes = {ob.name: world_bbox(ob) for ob in door_panels}
conflicts = []  # (relief_ob, door_name, y_overlap)
for rob in cab_relief:
    rb = world_bbox(rob)
    for dname, db in door_boxes.items():
        ox = overlap_1d(rb[0], db[0])
        oy = overlap_1d(rb[1], db[1])
        oz = overlap_1d(rb[2], db[2])
        if ox > 0 and oy > 0 and oz > 0:
            conflicts.append((rob, dname, oy))
            print(f"CONFLICT {rob.name} vs {dname}: "
                  f"x_ov={ox:.4f} y_ov={oy:.4f} z_ov={oz:.4f} "
                  f"relief_y=[{rb[1][0]:.4f},{rb[1][1]:.4f}] door_y=[{db[1][0]:.4f},{db[1][1]:.4f}]")
print(f"front-face conflicts: {len(conflicts)}")
# 另查：st-doors 自身把手/百叶/风扇罩与门板/柜体的关系（只检查、不动）
for ob in all_part_objs:
    if any(k in ob.name for k in ("Louver", "FanDisc", "FanBar", "FanRing", "FanHub")) \
            and ("Battery" in ob.name or "PCS" in ob.name):
        bb = world_bbox(ob)
        # 风扇罩 vs 柜顶盖（TopCap z [2.45,2.55]）：若风扇件 z 区间落在顶盖内即埋入
        if "Fan" in ob.name:
            print(f"FAN-CHECK {ob.name}: z=[{bb[2][0]:.4f},{bb[2][1]:.4f}] "
                  f"(cabinet TopCap z=[2.4500,2.5500])")

# ---------- 3) 内缩修复：冲突浮雕沿 +y（往柜体内）移，数值 = y 向重叠量 ----------
fix_log = []
for rob, dname, oy in conflicts:
    old_y = rob.location.y
    rob.location.y += oy
    fix_log.append((rob.name, dname, oy, old_y, rob.location.y))
    print(f"RECESS {rob.name}: +y {oy:.4f} (vs {dname}), loc.y {old_y:.4f} -> {rob.location.y:.4f}")
bpy.context.view_layer.update()
# 复核：修复后残余重叠
residual = []
for rob, dname, oy in conflicts:
    rb = world_bbox(rob)
    db = door_boxes[dname]
    oy2 = overlap_1d(rb[1], db[1])
    ox2 = overlap_1d(rb[0], db[0])
    oz2 = overlap_1d(rb[2], db[2])
    if ox2 > 0 and oy2 > 0 and oz2 > 0:
        residual.append((rob.name, dname, oy2))
        print(f"RESIDUAL {rob.name} vs {dname}: y_ov={oy2:.4f}")
print(f"residual conflicts after recess: {len(residual)}")

# ---------- 3b) 把手残余 0.002 m 清零 ----------
# 柜体竖拉手（*_Cabinet_Handle，每柜 1 根共 4 根）与门板 y 向重叠原为 0.030，
#   §3 已沿 +y 内缩 0.030；拉手 ymin 29.448+0.030=29.478，仍比门板 ymax 29.48 低 0.002。
#   再沿 +y 内缩 0.002 清零。把手固定座（*_HandleMount_*）内缩后已与门板齐平（残余 0），不动。
HANDLE_LIFT = 0.002
handle_fix = []
for rob, dname, _oy in conflicts:
    if "Cabinet" in rob.name and rob.name.endswith("_Handle"):
        rb = world_bbox(rob)
        db = door_boxes[dname]
        oy2 = overlap_1d(rb[1], db[1])
        ox2 = overlap_1d(rb[0], db[0])
        oz2 = overlap_1d(rb[2], db[2])
        if ox2 > 0 and oy2 > 0 and oz2 > 0:
            print(f"HANDLE-RESIDUAL {rob.name} vs {dname}: y_ov={oy2:.4f}")
            old_y = rob.location.y
            rob.location.y += HANDLE_LIFT
            handle_fix.append((rob.name, dname, oy2, old_y, rob.location.y))
            print(f"HANDLE-RECESS {rob.name}: +y {HANDLE_LIFT:.4f}, loc.y {old_y:.4f} -> {rob.location.y:.4f}")
print(f"handle residual cleared: {len(handle_fix)} handles +y 0.002")
assert len(handle_fix) == 4, f"expected 4 cabinet handle bars with residual, got {len(handle_fix)}"
bpy.context.view_layer.update()
# 复核：把手与门板残余 y 向重叠必须清零（≤0.0005 视为浮点尘埃）
for name, dname, _oy2, _old, _new in handle_fix:
    rob = bpy.data.objects[name]
    rb = world_bbox(rob)
    db = door_boxes[dname]
    oy3 = overlap_1d(rb[1], db[1])
    ox3 = overlap_1d(rb[0], db[0])
    oz3 = overlap_1d(rb[2], db[2])
    print(f"HANDLE-RECHECK {name} vs {dname}: y_ov={oy3:.6f}")
    assert not (ox3 > 0 and oy3 > 0.0005 and oz3 > 0), \
        f"{name} vs {dname} still overlaps y_ov={oy3:.4f}"
print("HANDLE CHECK PASS: 4/4 cabinet handles clear of door panels (residual 0)")

# ---------- 4) 拼装补壳体（注明 ASSEMBLY_ADDED；Godot _build_storage 壳体+屋顶板） ----------
# 返修 2026-11-22：壳体改半透明（Principled Alpha 0.35，BLEND 混合），内部 4 台柜 /
#   线槽 / 接线箱才看得见；屋顶板保持不透明。Alpha<1 时 glTF 导出为 alphaMode BLEND。
shell_mat = make_material("Storage_Shell_ASSEMBLY_ADDED", "#3E5A50", 0.5, 0.2)
shell_mat.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.35
# Blender 4.2 规范属性是 surface_render_method（blend_method 是旧别名且映射有损：
#   实测设 'OPAQUE' 会被忽略、读回仍是 'HASHED'；设 'BLEND' 才生效）。
#   壳体 BLENDED、屋顶 OPAQUE 必须经 surface_render_method 设置。
shell_mat.surface_render_method = "BLENDED"
roof_mat = make_material("Storage_Roof_ASSEMBLY_ADDED", "#424A52", 0.6, 0.2)
# v3b: 屋顶板挂真实 PBR 贴图（blue_metal_plate 染 #424A52）
add_pbr(roof_mat, "roof_color.jpg", "roof_rough.jpg", "roof_nor.jpg")
_check_pbr(roof_mat)
# 屋顶保持不透明：本机 Blender 4.2 的 surface_render_method 只有 DITHERED/BLENDED
#   两档（无 OPAQUE 枚举），新材质默认 DITHERED + Alpha 1.0 即不透明态；
#   glTF 导出时 Alpha=1 且非 BLEND → alphaMode OPAQUE（跑完后直接查 GLB JSON 核对）。
roof_alpha = roof_mat.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value
assert shell_mat.surface_render_method == "BLENDED", "shell must be BLENDED"
assert roof_mat.surface_render_method == "DITHERED" and roof_alpha == 1.0, \
    "roof must stay opaque (DITHERED + alpha 1.0)"
print("shell material: alpha=0.35 surface=BLENDED (transparent); roof material: alpha=1.0 surface=DITHERED (opaque)")


def add_box(name, dims, loc, mat, uv_meter=False):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(mat)
    if uv_meter:
        # 米制盒式投影：立方体默认 UV 是每面 0..1，9.2m 屋顶一 tile 会拉糊；
        # 按主法向取其余两轴的世界坐标作 UV（每 1m 一 tile），与 pv-panels 同口径。
        mesh = ob.data
        uv = mesh.uv_layers.get("UVMap") or mesh.uv_layers.new(name="UVMap")
        for poly in mesh.polygons:
            n = poly.normal
            ax = max(range(3), key=lambda i: abs(n[i]))
            ua, va = [i for i in range(3) if i != ax]
            for li in poly.loop_indices:
                co = mesh.vertices[mesh.loops[li].vertex_index].co
                uv.data[li].uv = (co[ua], co[va])
    return ob


shell = add_box("Storage_Shell_ASSEMBLY_ADDED", (8.6, 4.0, 4.4), (64.0, 30.0, 2.85), shell_mat)
roof = add_box("Storage_Roof_ASSEMBLY_ADDED", (9.2, 4.6, 0.35), (64.0, 30.0, 5.2), roof_mat,
               uv_meter=True)
print("assembly-added shell:", shell.name, "dims", tuple(round(v, 2) for v in shell.dimensions),
      "roof:", roof.name, "dims", tuple(round(v, 2) for v in roof.dimensions))

# ---------- 5) 存 .blend ----------
os.makedirs(os.path.dirname(BLEND_PATH), exist_ok=True)
os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
scene_objs = list(bpy.context.scene.objects)
print("scene objects before save:", len(scene_objs))
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("blend saved:", BLEND_PATH, "size:", os.path.getsize(BLEND_PATH))

# ---------- 6) 全选导出 .glb ----------
bpy.ops.object.select_all(action="DESELECT")
for ob in scene_objs:
    ob.select_set(True)
bpy.context.view_layer.objects.active = scene_objs[0]
bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format="GLB",
                           use_selection=True, export_apply=True)
print("glb exported:", GLB_PATH, "size:", os.path.getsize(GLB_PATH),
      "exported objects:", len(scene_objs))

# ---------- 7) 回读验证 ----------
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB_PATH)
imported = [ob for ob in bpy.data.objects if ob not in before]
print("reimported objects:", len(imported))
for ob in imported:
    bpy.data.objects.remove(ob, do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("blend re-saved after reimport cleanup:", BLEND_PATH,
      "size:", os.path.getsize(BLEND_PATH),
      "scene objects:", len(bpy.context.scene.objects))
print("DONE storage")
