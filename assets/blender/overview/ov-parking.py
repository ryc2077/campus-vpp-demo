# ov-parking v2: 停车区返工（总览件）
# Blender 坐标 x 向东、y 向北、z 向上，单位米
# 内容：停车场 20x12m（中心 (-30,-90)，程序化沥青）+ 北侧一排 10 个车位
#      + 白色车位线（轻微磨损）+ 每个车位末端轮挡 + 南侧行车道导向箭头/虚线
#      + 3 辆升级小车（灰 / 蓝 / 红，按 ch-cars v2 做法：倒角车身 + 分层车窗
#        + 车灯 + 后视镜 + 轮胎/轮毂分开）
# 不做主干道（ov-road-main）、不做充电区。
# 新规矩：渲染全部走 GitHub Actions，本地不渲染、不出预览图。
#
# 尺寸说明：任务给 10 个车位 × 2.5m 宽 = 25m，装不进 20m 宽的停车场；
# 停车场 20x12m 与车位 10 个是硬指标，故车位宽取 20/10 = 2.0m、深 5m，
# 车辆 1.8m 宽仍可停入。车位线贴在沥青面上（z 0.08 -> 0.10），防共面闪烁。
# 轮挡在车位北端（车头一侧），导向箭头在南侧行车道（y=-92.5），指向东。
import bpy
import math
import os
from mathutils import Vector

PIECE = "ov-parking"
BASE = os.path.expanduser("~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
PY_DIR = os.path.join(BASE, "assets/blender/overview")
BLEND_PATH = os.path.join(PY_DIR, "ov-parking.blend")
GLB_PATH = os.path.join(BASE, "assets/models/ov-parking.glb")

# 停车场：中心 (-30, -90)，20(x) x 12(y)m，厚 0.08m
LOT_CX, LOT_CY = -30.0, -90.0
LOT_SX, LOT_SY = 20.0, 12.0
LOT_Z0, LOT_Z1 = 0.0, 0.08
# 车位：北侧一排，10 个，2.0m 宽 x 5m 深
N_SPACES = 10
SPACE_W, SPACE_D = 2.0, 5.0
LINE_W = 0.12
LINE_Z0, LINE_Z1 = LOT_Z1, 0.10
# 车位北缘 = 停车场北缘 y=-84，车位向南 5m：y -89..-84
SPACE_Y_NORTH = LOT_CY + LOT_SY / 2.0          # -84
SPACE_Y_SOUTH = SPACE_Y_NORTH - SPACE_D        # -89
SPACE_Y_C = (SPACE_Y_NORTH + SPACE_Y_SOUTH) / 2.0  # -86.5
# 行车道（车位南侧空地）：y -96..-89，导向标线中心线 y=-92.5
LANE_Y = -92.5
# 轮挡：车位北端，贴着前轮胎面（前轮前缘 y=-84.67），y=-84.75
STOP_Y = SPACE_Y_NORTH - 0.75


def srgb_to_linear(hexstr):
    """Hex sRGB -> linear RGB（Principled Base Color 必须是线性值）。"""
    h = hexstr.lstrip("#")
    r = int(h[0:2], 16) / 255.0
    g = int(h[2:4], 16) / 255.0
    b = int(h[4:6], 16) / 255.0

    def conv(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (conv(r), conv(g), conv(b), 1.0)


def _noise_roughness(ntree, bsdf, scale, r_min, r_max):
    """Noise Texture -> Map Range -> Roughness."""
    tex = ntree.nodes.new("ShaderNodeTexCoord")
    noise = ntree.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 2.0
    noise.inputs["Roughness"].default_value = 0.7
    ntree.links.new(tex.outputs["Generated"], noise.inputs["Vector"])
    rng = ntree.nodes.new("ShaderNodeMapRange")
    rng.inputs["From Min"].default_value = 0.0
    rng.inputs["From Max"].default_value = 1.0
    rng.inputs["To Min"].default_value = r_min
    rng.inputs["To Max"].default_value = r_max
    ntree.links.new(noise.outputs["Fac"], rng.inputs["Value"])
    ntree.links.new(rng.outputs["Result"], bsdf.inputs["Roughness"])


def _noise_bump(ntree, bsdf, scale, strength, detail=2.0):
    tex = ntree.nodes.new("ShaderNodeTexCoord")
    noise = ntree.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = detail
    ntree.links.new(tex.outputs["Generated"], noise.inputs["Vector"])
    bump = ntree.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = strength
    bump.inputs["Distance"].default_value = 0.02
    ntree.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    ntree.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])


def make_asphalt(name):
    """程序化沥青：Base Color 保持纯值（保证 glTF 导出颜色正确），
    颗粒 / 磨损斑块 / 细裂纹全部走 Roughness 与 Bump：
    - Noise scale 60：细颗粒 Bump
    - Noise scale 4：大尺度磨损斑块 -> Roughness 0.80..1.0
    - Voronoi scale 90：细裂纹 -> Bump（小强度）"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    ntree = mat.node_tree
    bsdf = ntree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = srgb_to_linear("#424A52")
    bsdf.inputs["Roughness"].default_value = 0.95
    bsdf.inputs["Metallic"].default_value = 0.0
    # 细颗粒
    _noise_bump(ntree, bsdf, scale=60.0, strength=0.25, detail=2.0)
    # 磨损斑块：大尺度 Noise -> Roughness 0.80..1.0
    _noise_roughness(ntree, bsdf, scale=4.0, r_min=0.80, r_max=1.0)
    # 细裂纹：Voronoi -> 第二个 Bump 节点串联到 Normal
    tex = ntree.nodes.new("ShaderNodeTexCoord")
    vor = ntree.nodes.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = 90.0
    vor.feature = "DISTANCE_TO_EDGE"
    ntree.links.new(tex.outputs["Generated"], vor.inputs["Vector"])
    bump2 = ntree.nodes.new("ShaderNodeBump")
    bump2.inputs["Strength"].default_value = 0.12
    bump2.inputs["Distance"].default_value = 0.01
    ntree.links.new(vor.outputs["Distance"], bump2.inputs["Height"])
    # 把裂纹 Bump 接到第一个 Bump 的 Normal 输入上（串联）
    first_bump = None
    for n in ntree.nodes:
        if n.bl_idname == "ShaderNodeBump" and n is not bump2:
            first_bump = n
            break
    if first_bump is not None:
        ntree.links.new(bump2.outputs["Normal"], first_bump.inputs["Normal"])
    return mat


def make_worn_white(name, hexstr="#F2F2F2"):
    """磨损白漆：纯色 Base Color + Noise 粗糙度变化（轻微磨损感）。"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    ntree = mat.node_tree
    bsdf = ntree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = srgb_to_linear(hexstr)
    bsdf.inputs["Roughness"].default_value = 0.8
    _noise_roughness(ntree, bsdf, scale=8.0, r_min=0.65, r_max=0.95)
    return mat


def make_paint(name, hexstr):
    """车漆：Principled，Noise 粗糙度 0.35 +/- 0.08，轻 Bump（同 ch-cars v2）。
    2026-11-24 返工 R1（验收 run #72：本件车漆根本无 clearcoat——060877f4
    只给 ch-cars 挂了清漆，ov-parking 的 make_paint 从没设 Coat，且
    _apply_pbr 挂图时也不会补；GLB 实测无 KHR_materials_clearcoat）：
    make_car 里挂图后补 Coat Weight 1.0 / Coat Roughness 0.05（与 ch-cars
    同口径），底漆粗糙度仍由 Paint* rough 贴图驱动。"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    ntree = mat.node_tree
    bsdf = ntree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = srgb_to_linear(hexstr)
    bsdf.inputs["Metallic"].default_value = 0.15
    _noise_roughness(ntree, bsdf, scale=6.0, r_min=0.27, r_max=0.43)
    _noise_bump(ntree, bsdf, scale=18.0, strength=0.06)
    return mat


def make_glass(name):
    """车窗玻璃：透明材质（Alpha 0.65、粗糙度低），与 ov-gate 的
    Glass_Reflective 做法一致。v2 的 Transmission 0.9 + Glass BSDF
    混合导出后是 OPAQUE（alpha 1.0），Godot 里不透明，改回 Alpha 混合。
    2026-11-24 返工 R1（验收 run #72：车窗纯色平板）：加细噪波 Bump
    （scale 20、strength 0.10）给窗面纹理/反光变化，粗糙度 0.06→0.05；
    Alpha 混合不动，Godot 里仍透明。"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    ntree = mat.node_tree
    bsdf = ntree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = srgb_to_linear("#9FC3D8")
    bsdf.inputs["Roughness"].default_value = 0.05
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Alpha"].default_value = 0.65
    bsdf.inputs["Specular IOR Level"].default_value = 1.0
    _noise_bump(ntree, bsdf, scale=20.0, strength=0.10)
    mat.surface_render_method = "DITHERED"
    return mat


def make_tire(name):
    """橡胶轮胎：粗糙度 0.95 + Noise Bump，与轮毂分开（同 ch-cars v2）。"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    ntree = mat.node_tree
    bsdf = ntree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = srgb_to_linear("#2A2D2F")
    bsdf.inputs["Roughness"].default_value = 0.95
    _noise_bump(ntree, bsdf, scale=10.0, strength=0.30)
    return mat


def make_hub(name):
    """金属轮毂：metallic 0.8，粗糙度 0.35 +/- 0.08（同 ch-cars v2）。"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    ntree = mat.node_tree
    bsdf = ntree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = srgb_to_linear("#C0C5C9")
    bsdf.inputs["Metallic"].default_value = 0.8
    _noise_roughness(ntree, bsdf, scale=6.0, r_min=0.27, r_max=0.43)
    return mat


def make_lamp(name, hexstr, emission_hex, strength=1.0):
    """弱发光灯块（前灯暖白 / 尾灯红）。"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = srgb_to_linear(hexstr)
    bsdf.inputs["Roughness"].default_value = 0.25
    bsdf.inputs["Emission Color"].default_value = srgb_to_linear(emission_hex)
    bsdf.inputs["Emission Strength"].default_value = strength
    return mat


def make_simple(name, hexstr, roughness=0.9, metallic=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = srgb_to_linear(hexstr)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


# ---- 材质（车位线 / 轮挡 / 导向标线各自分开）----
MAT_ASPHALT = make_asphalt("ov-parking_asphalt")
MAT_LINE = make_worn_white("ov-parking_line_white")        # 车位线
MAT_MARKING = make_worn_white("ov-parking_marking_white")  # 导向箭头/虚线
MAT_STOP = make_simple("ov-parking_wheelstop_concrete", "#B9B3A8", 0.95)  # 轮挡
MAT_GLASS = make_glass("ov-parking_glass")
MAT_TIRE = make_tire("ov-parking_tire")
MAT_HUB = make_hub("ov-parking_hub")
MAT_HEAD = make_lamp("ov-parking_headlamp", "#FFF6D8", "#FFF2CC", strength=1.0)
MAT_TAIL = make_lamp("ov-parking_taillamp", "#C03028", "#D04030", strength=0.8)
MAT_DARK = make_simple("ov-parking_dark", "#3A3F42", 0.7)

# ---- PBR 贴图挂接（返工）：下载的 CC0 实拍贴图经亮度映射到 SPEC 色
# （assets/external/* -> ov-parking_textures/ 衍生 PNG）；车漆/轮胎/
# 轮毂/磨损白线无对应下载，用程序化合成贴图补位；程序化 Noise 节点
# 不进 glTF，必须换成图片纹理节点。UV 按米缩放（见 _scale_uvs_to_meters）。
import numpy as _np
TEX_DIR = os.path.join(PY_DIR, "ov-parking_textures")


def _load_img(path, colorspace):
    img = bpy.data.images.load(path)
    img.colorspace_settings.name = colorspace
    return img


def _apply_pbr(mat, set_name):
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    out = nt.nodes["Material Output"]
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
    n = os.path.join(TEX_DIR, set_name + "_normal.png")
    if os.path.exists(n):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = _load_img(n, "Non-Color")
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.space = "TANGENT"
        nt.links.new(t.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def _ensure_uv(ob):
    me = ob.data
    if me is None or len(me.uv_layers) > 0:
        return
    me.uv_layers.new(name="UVMap")
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.02)
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")


def _scale_uvs_to_meters(obj, tile):
    """每面按世界尺寸把 UV 缩放到 tile 米一重复（REPEAT 平铺）。"""
    me = obj.data
    if me is None or len(me.uv_layers) == 0:
        return 0
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
    return len(me.polygons)


_apply_pbr(MAT_ASPHALT, "Asphalt")
_apply_pbr(MAT_LINE, "WhiteWorn")
_apply_pbr(MAT_MARKING, "WhiteWorn")
_apply_pbr(MAT_STOP, "Concrete")
_apply_pbr(MAT_TIRE, "Tire")
_apply_pbr(MAT_HUB, "HubMetal")
# 车漆在 make_car 里现做现挂（PaintGrey/PaintBlue/PaintRed）。
# 贴图 UV 按米缩放：{材质: 一重复多少米}
UV_TILE = {MAT_ASPHALT: 3.0, MAT_LINE: 1.0, MAT_MARKING: 1.0,
           MAT_STOP: 2.0, MAT_TIRE: 1.0, MAT_HUB: 1.0}

# ---- clean scene ----
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

objs = []  # objects that go into the .glb


def box(name, loc, dims, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.active_object
    o.name = name
    o.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0:
        mod = o.modifiers.new(name="bevel", type="BEVEL")
        mod.width = bevel
        mod.segments = 3
    if mat:
        o.data.materials.append(mat)
    objs.append(o)
    return o


# ---- 停车场沥青面 ----
box("ov-parking_lot", (LOT_CX, LOT_CY, (LOT_Z0 + LOT_Z1) / 2.0),
    (LOT_SX, LOT_SY, LOT_Z1 - LOT_Z0), MAT_ASPHALT, bevel=0.02)

# ---- 车位线：11 条分隔线（0.12m 宽 x 5m 深）+ 1 条北缘通长线 ----
lot_x0 = LOT_CX - LOT_SX / 2.0  # -40
for i in range(N_SPACES + 1):
    x = lot_x0 + i * SPACE_W
    box(f"ov-parking_space_line_{i:02d}", (x, SPACE_Y_C, (LINE_Z0 + LINE_Z1) / 2.0),
        (LINE_W, SPACE_D, LINE_Z1 - LINE_Z0), MAT_LINE)
box("ov-parking_space_line_north",
    (LOT_CX, SPACE_Y_NORTH - LINE_W / 2.0, (LINE_Z0 + LINE_Z1) / 2.0),
    (LOT_SX, LINE_W, LINE_Z1 - LINE_Z0), MAT_LINE)

# ---- 轮挡：每个车位北端（车头一侧）一个混凝土挡块 1.6 x 0.15 x 0.12m ----
for i in range(N_SPACES):
    x = lot_x0 + (i + 0.5) * SPACE_W
    box(f"ov-parking_wheelstop_{i + 1:02d}",
        (x, STOP_Y, LOT_Z1 + 0.06), (1.6, 0.15, 0.12), MAT_STOP, bevel=0.02)

# ---- 导向标线：南侧行车道，两个指向东的箭头 + 两段虚线 ----
def guide_arrow(name, cx, cy):
    """箭头：杆 1.2 x 0.25m + 三角头（显式坐标三角棱柱），指向 +X（东）。"""
    box(f"{name}_shaft", (cx - 0.35, cy, 0.11), (1.2, 0.25, 0.02), MAT_MARKING)
    # 三角头：底边 x=cx+0.10、半宽 0.45，顶点 x=cx+1.10，厚 0.02（z 0.10..0.12）
    verts = [(cx + 0.10, cy - 0.45, 0.10), (cx + 0.10, cy + 0.45, 0.10),
             (cx + 1.10, cy, 0.10),
             (cx + 0.10, cy - 0.45, 0.12), (cx + 0.10, cy + 0.45, 0.12),
             (cx + 1.10, cy, 0.12)]
    faces = [(0, 2, 1), (3, 4, 5), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)]
    mesh = bpy.data.meshes.new(f"{name}_head_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    head = bpy.data.objects.new(f"{name}_head", mesh)
    bpy.context.collection.objects.link(head)
    head.data.materials.append(MAT_MARKING)
    objs.append(head)


guide_arrow("ov-parking_arrow_1", -35.0, LANE_Y)
guide_arrow("ov-parking_arrow_2", -25.0, LANE_Y)
# 行车道虚线：沿 y=-92.5，6 段，每段 1.0m、间隔 1.0m，跳过箭头位置
for k, dx in enumerate((-9.0, -7.0, -3.0, -1.0, 3.0, 5.0, 7.0, 9.0)):
    box(f"ov-parking_lane_dash_{k + 1:02d}",
        (LOT_CX + dx, LANE_Y, 0.11), (1.0, 0.12, 0.02), MAT_MARKING)


# ---- 车辆（同 ch-cars v2 做法；局部坐标车长沿 X、车头 +X）----
def wheel(name, loc):
    """轮胎圆柱 + 金属轮毂盘 + 每面 5 根辐条。"""
    parts = []
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.33, depth=0.22,
                                        location=loc)
    tire = bpy.context.active_object
    tire.name = name + "_tire"
    tire.rotation_euler = (math.radians(90), 0, 0)  # 轴沿 Y
    tire.data.materials.append(MAT_TIRE)
    objs.append(tire)
    parts.append(tire)
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.19, depth=0.24,
                                        location=loc)
    hub = bpy.context.active_object
    hub.name = name + "_hub"
    hub.rotation_euler = (math.radians(90), 0, 0)
    hub.data.materials.append(MAT_HUB)
    objs.append(hub)
    parts.append(hub)
    for side in (+1, -1):
        for k in range(5):
            ang = math.radians(k * 72.0)
            sp = box("%s_spoke_%s%d" % (name, "L" if side > 0 else "R", k),
                     (loc[0], loc[1] + side * 0.125, loc[2]),
                     (0.34, 0.02, 0.08), MAT_HUB)
            sp.rotation_euler = (0, ang, 0)
            parts.append(sp)
    return parts


def make_car(tag, color_hex, cx, cy, rot_z_deg):
    """整车挂在一个 empty 下，旋转/摆放一次完成。车头朝北（+Y）故 rot_z=+90。"""
    mat_body = make_paint("ov-parking_body_" + tag, color_hex)
    # 车漆挂图（返工）：细噪波车漆纹理，颜色即车身色
    _apply_pbr(mat_body, "Paint" + tag.capitalize())
    # 返工 R1：挂图后补清漆（_apply_pbr 只动 Base Color/Roughness/Normal，
    # Coat 默认值须另设；此前从未设过，GLB 里无 clearcoat）
    _paint_bsdf = mat_body.node_tree.nodes["Principled BSDF"]
    _paint_bsdf.inputs["Coat Weight"].default_value = 1.0
    _paint_bsdf.inputs["Coat Roughness"].default_value = 0.05
    UV_TILE[mat_body] = 1.0
    parts = []
    # 车身 4.5 x 1.8 x 0.55，中心 z 0.60，倒角
    parts.append(box("ov-parking_%s_body" % tag, (0, 0, 0.60),
                     (4.5, 1.8, 0.55), mat_body, bevel=0.04))
    # 车顶 2.2 x 1.6 x 0.5，中心 z 1.125，略偏后（x -0.2）
    parts.append(box("ov-parking_%s_roof" % tag, (-0.2, 0, 1.125),
                     (2.2, 1.6, 0.5), mat_body, bevel=0.04))
    # 分层车窗：每侧前后两块（B 柱留缝）
    for side in (+1, -1):
        s = "L" if side > 0 else "R"
        parts.append(box("ov-parking_%s_glass_front_%s" % (tag, s),
                         (0.35, side * 0.805, 1.12),
                         (0.85, 0.02, 0.35), MAT_GLASS))
        parts.append(box("ov-parking_%s_glass_rear_%s" % (tag, s),
                         (-0.75, side * 0.805, 1.12),
                         (0.85, 0.02, 0.35), MAT_GLASS))
    # 前风挡 + 后窗
    parts.append(box("ov-parking_%s_glass_wind" % tag,
                     (0.91, 0, 1.12), (0.02, 1.40, 0.38), MAT_GLASS))
    parts.append(box("ov-parking_%s_glass_back" % tag,
                     (-1.31, 0, 1.12), (0.02, 1.40, 0.38), MAT_GLASS))
    # 前灯（+X）与尾灯（-X），弱发光
    for side in (+1, -1):
        s = "L" if side > 0 else "R"
        parts.append(box("ov-parking_%s_head_%s" % (tag, s),
                         (2.26, side * 0.55, 0.78),
                         (0.06, 0.50, 0.12), MAT_HEAD))
        parts.append(box("ov-parking_%s_tail_%s" % (tag, s),
                         (-2.26, side * 0.55, 0.78),
                         (0.06, 0.50, 0.12), MAT_TAIL))
    # 前格栅
    parts.append(box("ov-parking_%s_grille" % tag,
                     (2.26, 0, 0.45), (0.06, 1.20, 0.15), MAT_DARK))
    # 后视镜：支杆 + 镜体，A 柱两侧
    for side in (+1, -1):
        s = "L" if side > 0 else "R"
        parts.append(box("ov-parking_%s_mirror_stalk_%s" % (tag, s),
                         (0.75, side * 0.90, 1.02),
                         (0.10, 0.14, 0.05), MAT_DARK))
        parts.append(box("ov-parking_%s_mirror_%s" % (tag, s),
                         (0.75, side * 0.98, 1.04),
                         (0.16, 0.06, 0.14), mat_body, bevel=0.02))
    # 4 轮：r 0.33，x +-1.5，y +-0.80，z 0.33（局部坐标；整车由 empty 抬高 LOT_Z1）
    for i, wx in enumerate((-1.5, 1.5)):
        for j, wy in enumerate((-0.80, 0.80)):
            parts.extend(wheel("ov-parking_%s_wheel_%d%d" % (tag, i, j),
                               (wx, wy, 0.33)))
    # empty 抬高 LOT_Z1（0.08）：轮底正好落在沥青顶面，车身不悬空、不下陷
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(cx, cy, LOT_Z1))
    grp = bpy.context.active_object
    grp.name = "ov-parking_%s" % tag
    grp.rotation_euler = (0, 0, math.radians(rot_z_deg))
    for p in parts:
        p.parent = grp
    objs.append(grp)
    return grp


def space_center_x(i):
    """第 i 个车位（1 起）中心 x。"""
    return lot_x0 + (i - 0.5) * SPACE_W


# 3 辆车：灰 2 号位、蓝 5 号位、红 9 号位（位置与 v1 一致），车头朝北
make_car("grey", "#8A8F94", space_center_x(2), SPACE_Y_C, 90)
make_car("blue", "#3B82C4", space_center_x(5), SPACE_Y_C, 90)
make_car("red", "#C4534E", space_center_x(9), SPACE_Y_C, 90)

print("parking objects:", len(objs))

# ---- UV 按米缩放（返工）：贴图 1 重复 = tile 米，无 UV 的箭头先补 UV ----
bpy.context.view_layer.update()
for _o in objs:
    if _o.type != "MESH" or not _o.data.materials:
        continue
    _tile = UV_TILE.get(_o.data.materials[0])
    if _tile is None:
        continue
    _ensure_uv(_o)
    _scale_uvs_to_meters(_o, _tile)
print("UV scaled to meters for textured mats")

# ---- 材质校验（返工 R1 防回归）：3 台车漆须带 clearcoat ----
for _m in [m for m in bpy.data.materials
           if m.name.startswith("ov-parking_body_")]:
    _b = _m.node_tree.nodes["Principled BSDF"]
    assert abs(_b.inputs["Coat Weight"].default_value - 1.0) < 1e-6, \
        f"{_m.name}: Coat Weight != 1.0"
    assert abs(_b.inputs["Coat Roughness"].default_value - 0.05) < 1e-6, \
        f"{_m.name}: Coat Roughness != 0.05"
print("MATERIAL CHECK PASS: car paint clearcoat Coat Weight 1.0 / "
      "Coat Roughness 0.05")

# ---- 世界背景：Nishita 天空（返工 R2，与 ch-cars 同口径） ----
# 返工 R2（验收 run 45251171902：ov-parking 同 ch-cars 一样，纯色平坦世界里
# 清漆无物可映；.blend 里留 Nishita 天空世界供 Actions 预览渲染，
# render_max 对亮色世界原样保留；不进 GLB，Godot 不受影响。太阳仍走
# render_max 默认（西南方向），本件不自带太阳。）
_world = bpy.data.worlds.new("ov-parking_world")
bpy.context.scene.world = _world
_world.use_nodes = True
_sky = _world.node_tree.nodes.new("ShaderNodeTexSky")
_sky.sky_type = 'NISHITA'
_sky.sun_elevation = math.radians(50.0)
_sky.sun_rotation = math.radians(225.0)
_sky.altitude = 0.0
_bg = _world.node_tree.nodes["Background"]
_world.node_tree.links.new(_sky.outputs["Color"], _bg.inputs["Color"])
_bg.inputs["Strength"].default_value = 1.0

# ---- R3 preview studio（2026-11-24，与 ch-cars 同根因同修法，见 BLENDER_MODELS.md §9）----
# 根因（ch-cars 本地最小复现 320x180 像素统计）：世界接线正确、film_transparent=False；
# 自动相机俯角约 28°、顶缘视线低于地平线约 16°，天空不在画面内；EEVEE 里世界直接进清漆
# 环境反射，探针（烘焙/不烘焙）像素变化仅 meanAbs 约 1.0；平板车身 + 均匀淡天 → 各面只映
# 单一淡色＝看起来全哑光；方向太阳进镜面角时车顶 183→246（镜面路径通），但 Coat 0.05
# 窄瓣一次只能亮一辆车。修法只改预览环境：留 Nishita 世界 + 暗色预览地面（填黑洞背景，
# 本件已有沥青 lot、地面只补 lot 外围，z=0 在 lot 顶 0.08 之下、无共面）+ 东南太阳
# （与 render_max 默认同向）+ 西北高处 24x2m 亮条灯（车顶镜面方向的柔光条；与 ch-cars
# 相同相对位置：中心 (-30,-90) 偏 NW (-23,+31,+17)）。地面/灯光/太阳不进 GLB（导出只选
# objs），总览拼装也排除（overview.py 删 LIGHT/LIGHT_PROBE/含 preview 的名字）。
# ---- preview ground: dark, fills the below-horizon black void outside the lot ----
bpy.ops.mesh.primitive_plane_add(size=80, location=(LOT_CX, LOT_CY, 0))
_ground = bpy.context.active_object
_ground.name = "Ground_PreviewOnly"
_gmat = bpy.data.materials.new("ov-parking_preview_ground")
_gmat.use_nodes = True
_gbsdf = _gmat.node_tree.nodes["Principled BSDF"]
_gbsdf.inputs["Base Color"].default_value = (0.05, 0.05, 0.05, 1.0)
_gbsdf.inputs["Roughness"].default_value = 0.95
_ground.data.materials.append(_gmat)

# ---- preview sun: SE, same as render_max default ----
bpy.ops.object.light_add(type='SUN', location=(LOT_CX, LOT_CY, 25))
_sun = bpy.context.active_object
_sun.name = "ov-parking_sun"
_sun.data.energy = 3.5
_sun.data.use_shadow = True
_sun.rotation_euler = (math.radians(50.0), 0.0, math.radians(30.0))

# ---- preview softbox strip: 24x2m area light, NW-high in the roofs' mirror direction ----
bpy.ops.object.light_add(type='AREA', location=(LOT_CX - 23, LOT_CY + 31, 18))
_strip = bpy.context.active_object
_strip.name = "ov-parking_softbox"
_strip.data.shape = 'RECTANGLE'
_strip.data.size = 24.0
_strip.data.size_y = 2.0
_strip.data.energy = 15000.0
_strip.rotation_euler = (Vector((LOT_CX, LOT_CY, 1.0)) - _strip.location).to_track_quat('-Z', 'Y').to_euler()

# ---- save .blend ----
os.makedirs(PY_DIR, exist_ok=True)
os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("saved blend:", BLEND_PATH)
if os.path.exists(BLEND_PATH + "1"):
    os.remove(BLEND_PATH + "1")
    print("removed blend1")

# ---- export .glb (this piece only) ----
bpy.ops.object.select_all(action="DESELECT")
for o in objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format="GLB",
                           use_selection=True, export_apply=True)
print("exported glb:", GLB_PATH, "objects:", len(objs))

# ---- read back the .glb to confirm it opens, then drop the duplicates ----
bpy.ops.object.select_all(action="DESELECT")
bpy.ops.import_scene.gltf(filepath=GLB_PATH)
imported = [o for o in bpy.context.selected_objects]
print("glb re-import OK, imported objects:", len(imported))
bpy.ops.object.delete(use_global=False)
print("re-imported copies deleted, scene objects:", len(bpy.context.scene.objects))

print("DONE ov-parking")
