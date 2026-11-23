# overview 场景拼装（总览场景，只拼 assets/blender/overview/ 的 20 件）
# 用法（无头，不渲染）：
#   xvfb-run -a -s "-screen 0 1280x720x24" <blender> -b --python overview.py
# 做法：全局坐标直接 append，不移位置；只写本脚本、
#   assets/blender/scenes/overview.blend、assets/models/scenes/overview.glb。
# 排除：相机/灯光/光照探针、名字含 preview 的预览物（含各件的
#   Ground_PreviewOnly / PREVIEW_*）、flag-lamp 的 CamTarget 空物体。
#   ov-parking 的 3 个 EMPTY（ov-parking_blue/grey/red）是 3 辆车的父级，
#   必须保留，否则车身子物体会丢变换。
# 拼装补齐（场景内新建，名前缀 OV_ASSEMBLY_，不是单件）：
#   地面 340x340 草地纹理（Grass004 亮度映射到 SPEC 草地绿 #69b45e，
#   均值即 #69B45E，不再是平色；campus.json ground）；池塘水面椭圆盘
#   （campus.json pond [82,78] rx11 rz8 -> Blender (82,-78)，水纹理）；
#   配电房外壳（campus.json buildings.dist [48,-30] 16x10 高 8m，
#   Plaster001 映射到 #dfe9f2；屋顶 grey_roof_01 映射到深灰 #424A52）。
#   拼装件贴图在 assets/blender/scenes/overview_textures/（返工挂图）。
# 缺口已补：户外变压器（campus.json transformer [74,-30]）由 ov-transformer
# 件提供（Blender (74,30)，58 个对象），见 PARTS 末尾。
# 绿地重叠：实测 ov-dorm 的 dorm_lawn_between 与 ov-lawn 在宿舍区无 XY
#   重叠（见脚本内检查打印），不做高差调整，调整量 0。
#   池塘草坪已返工：ov-lawn.py 撒点排除水面椭圆（含 1m 边距），只留
#   环形草坪带，场景内不再下移 Lawn_Pond_Grass_*（旧 -0.5m 下移曾把
#   18,863 叶全埋进地下，2026-11-23 返工删除）。

import bpy
import os
import datetime
import numpy as _np
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
    "ov-lawn", "ov-flag-lamp", "ov-gate", "ov-parking", "ov-transformer",
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


TEX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "overview_textures")


def _load_img(path, colorspace):
    img = bpy.data.images.load(path)
    img.colorspace_settings.name = colorspace
    return img


def pbr_mat(name, set_name, rough_scalar=None):
    """拼装件 PBR 材质（返工）：下载 CC0 贴图经亮度映射到 SPEC 色后挂图，
    与各件的 _apply_pbr 同做法；颜色/粗糙/法线三图，贴图在
    assets/blender/scenes/overview_textures/。"""
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    out = nt.nodes.get("Material Output")
    for n in list(nt.nodes):
        if n not in (bsdf, out):
            nt.nodes.remove(n)
    for link in list(nt.links):
        if link.to_node is bsdf:
            nt.links.remove(link)
    bsdf.inputs["Base Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    c = os.path.join(TEX_DIR, set_name + "_color.png")
    if os.path.exists(c):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = _load_img(c, "sRGB")
        nt.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
    r = os.path.join(TEX_DIR, set_name + "_rough.png")
    if os.path.exists(r):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = _load_img(r, "Non-Color")
        nt.links.new(t.outputs["Color"], bsdf.inputs["Roughness"])
        bsdf.inputs["Roughness"].default_value = 1.0
    elif rough_scalar is not None:
        bsdf.inputs["Roughness"].default_value = rough_scalar
    n = os.path.join(TEX_DIR, set_name + "_normal.png")
    if os.path.exists(n):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = _load_img(n, "Non-Color")
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.space = "TANGENT"
        nt.links.new(t.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def _scale_uvs_to_meters(obj, tile):
    """每面按世界尺寸把 UV 缩放到 tile 米一重复（REPEAT 平铺）。"""
    me = obj.data
    if me is None or len(me.uv_layers) == 0:
        return
    uv = me.uv_layers.active.data
    mw = obj.matrix_world
    for poly in me.polygons:
        idx = list(poly.loop_indices)
        P = _np.array([mw @ me.vertices[me.loops[i].vertex_index].co
                       for i in idx], dtype=float)
        U = _np.array([[uv[i].uv[0], uv[i].uv[1]] for i in idx], dtype=float)
        A = _np.column_stack([_np.ones(len(idx)), U])
        coef, *_ = _np.linalg.lstsq(A, P, rcond=None)
        su = _np.linalg.norm(coef[1]) / tile
        sv = _np.linalg.norm(coef[2]) / tile
        for i in idx:
            u, v = uv[i].uv
            uv[i].uv = (u * su, v * sv)


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
#     返工：Grass004 亮度映射到 #69B45E 的草地纹理，4m 一重复，不再平色。
ground_mat = pbr_mat("OV_ASSEMBLY_ground_mat", "GroundGrass")
bpy.ops.mesh.primitive_plane_add(size=340.0, location=(0.0, 0.0, -0.05))
ground = bpy.context.active_object
ground.name = "OV_ASSEMBLY_ground"
ground.data.materials.append(ground_mat)
print("ASSEMBLY ground 340x340 @z=-0.05 color=#69b45e")

# 3b. 池塘水面椭圆盘：Godot [82,78] rx11 rz8 -> Blender (82,-78)，
#     rx=11（x），ry=8（y）；圆柱顶面 z=0.10、底面 z=-0.02。
#     campus.json 无 pond 颜色，水面蓝 #2F7FC4 为拼装自选。
#     返工：水纹理（均值 #2F7FC4），2m 一重复。
pond_mat = pbr_mat("OV_ASSEMBLY_pond_mat", "PondWater")
bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=1.0, depth=0.12,
                                    location=(82.0, -78.0, 0.04))
pond = bpy.context.active_object
pond.name = "OV_ASSEMBLY_pond"
pond.scale = (11.0, 8.0, 1.0)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
pond.data.materials.append(pond_mat)
print("ASSEMBLY pond ellipse center=(82,-78) rx=11 ry=8 top z=0.10 color=#2F7FC4")

# 池塘草坪不再下移：ov-lawn.py 撒点已排除水面椭圆（含 1m 边距），环形带
# 上的草丛扎在草坪底板顶面 z=0.05、丛高 0.15-0.35m，不再穿出水面；
# 旧版 -0.5m 下移把 18,863 叶全埋进地下，已删除（2026-11-23 返工）。
# 校验：Lawn_Pond_Grass_* 的 location.z 必须为 0，与另两片草坪一致。
for obj in list(bpy.context.scene.objects):
    if obj.name.startswith("Lawn_Pond_Grass_"):
        assert obj.location.z == 0.0, "pond grass moved: %s z=%s" % (
            obj.name, obj.location.z)
print("ASSEMBLY pond grass kept at z=0 (no bury, ring-only scatter)")

# 3c. 配电房外壳：campus.json buildings.dist，Godot [48,-30] -> Blender
#     (48,30)，16x10，高 8m，color #dfe9f2；屋顶板深灰 #424A52（SPEC §3）。
#     返工：墙体 Plaster001 映射到 #dfe9f2、屋顶 grey_roof_01 映射到
#     #424A52，均 2m 一重复。
dist_mat = pbr_mat("OV_ASSEMBLY_dist_mat", "DistPlaster")
roof_mat = pbr_mat("OV_ASSEMBLY_dist_roof_mat", "DistRoofDark")
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

# 返工：拼装件 UV 按米缩放（贴图按 tile 米一重复平铺）。
bpy.context.view_layer.update()
_scale_uvs_to_meters(ground, 4.0)
_scale_uvs_to_meters(pond, 2.0)
_scale_uvs_to_meters(dist, 2.0)
_scale_uvs_to_meters(dist_roof, 2.0)
print("ASSEMBLY UV scaled to meters (ground 4m, pond/dist/roof 2m)")

# 户外变压器已拼入：campus.json transformer Godot [74,-30] -> Blender
# (74,30)，ov-transformer 件（58 个对象，TF_* 前缀）。
print("GAP transformer at Blender (74,30): included via ov-transformer")

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
