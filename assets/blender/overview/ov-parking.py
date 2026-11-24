# ov-parking v3: 停车区返工（总览件）——R2-T19 汽车换装
# Blender 坐标 x 向东、y 向北、z 向上，单位米
# 内容：停车场 20x12m（中心 (-30,-90)，程序化沥青）+ 北侧一排 10 个车位
#      + 白色车位线（轻微磨损）+ 每个车位末端轮挡 + 南侧行车道导向箭头/虚线
#      + 3 辆 Quaternius 网上车（灰 SUV / 蓝 Car / 红 Sports 2，见下文换装说明）
# 不做主干道（ov-road-main）、不做充电区。
# 新规矩：渲染全部走 GitHub Actions，本地不渲染、不出预览图。
#
# 换装（R2-T19，2026-11-24；来源 assets/external/SOURCES.md §9，CC0）：
# 三辆手捏小车换成 poly.pizza Quaternius Cars 包：car-quaternius.glb（蓝）、
# suv-quaternius.glb（白→灰）、sports-car-2-quaternius.glb（橙→红）。
# 实测：glTF 前向 +Z，Blender 导入后长在 Y 轴、车头在 -Y；每车绕 Z 转 +90°
# 烘进 mesh（车头 -Y -> +X、车长落到 X 轴），与旧手捏车局部系一致，
# empty 保持旧旋转 +90°（车头朝 +Y/北）。车身主 mesh 命名 _roof（与 ch-cars
# 同口径的 Godot SOC 锚点命名，原点移到 mesh 高度中点；本件总览不挂 SOC 条，
# 仅为两件命名统一）。
# 缩放：车位 2.0 m 宽（线内缘 ±0.94 m），三车长统一缩到 4.4 m、宽统一夹到
# 1.80 m（与旧手捏车同宽，每侧余 0.04 m 不压线）：灰 SUV (0.8531, 1.0451,
# 1.0451)、蓝 Car (0.9945, 1.0427, 1.0427)、红 Sports (1.0, 1.1083, 1.1083)
# （sx=宽、sy=长、sz=高，按导入轴向）。Sports 橙改 SPEC 红 #C4534E（Orange
# + DarkOrange 两材质均改，只改数值）；灰 #8A8F94、蓝 #3B82C4 沿用旧色。
# 车漆复用 ch-cars 旧清漆配方（1.0/0.05），车窗用已验证深色镀膜玻璃
# （透射 0.10、alpha 0.90、粗糙度 0.15、#33505F）。
# 位置：灰 2 号位、蓝 5 号位、红 9 号位（与 v1 一致），车头朝北；灰 SUV
# 前轮北缘离轮挡仅 0.04 m（原 -86.5 时会顶轮挡 0.04 m），故 SUV 中心
# 南移 0.10 m 至 y=-86.6（仍在 2 号位内，南缘 -88.8 > -89）。
#
# 尺寸说明：任务给 10 个车位 × 2.5m 宽 = 25m，装不进 20m 宽的停车场；
# 停车场 20x12m 与车位 10 个是硬指标，故车位宽取 20/10 = 2.0m、深 5m，
# 车辆 1.8m 宽仍可停入。车位线贴在沥青面上（z 0.08 -> 0.10），防共面闪烁。
# 轮挡在车位北端（车头一侧），导向箭头在南侧行车道（y=-92.5），指向东。
import bpy
import math
import os
from mathutils import Matrix, Vector

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
    """车漆（ch-cars 旧清漆配方）：Metallic 0.15 / Roughness 0.25 固定值 +
    Coat Weight 1.0 / Coat Roughness 0.05 + 细颗粒 Bump（只进 EEVEE）。
    Base Color / Roughness 不链接，保证 glTF factor 保留。
    注意：旧版曾挂 Paint* PBR 贴图（_apply_pbr），R2-T19 换装后车漆改用
    导入材质直接染色，不再挂图；ov-parking_textures/ 下 Paint* 三件套
    留在磁盘未删，但本件已不再引用。"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    ntree = mat.node_tree
    bsdf = ntree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = srgb_to_linear(hexstr)
    bsdf.inputs["Metallic"].default_value = 0.15
    bsdf.inputs["Roughness"].default_value = 0.25
    bsdf.inputs["Coat Weight"].default_value = 1.0
    bsdf.inputs["Coat Roughness"].default_value = 0.05
    _noise_bump(ntree, bsdf, scale=40.0, strength=0.10)
    return mat


def make_glass(name):
    """车窗玻璃：深色镀膜玻璃（2026-11-24 glass fix，R3 遗留弱项）。
    R3 验收：侧窗有天空纵向渐变（顶部 (200,214,232)/底部 (101,142,181)）
    但一眼仍是淡灰绿平板、无亮带。根因：竖直面从东南相机看镜面方向
    指向地平线以下暗地面，且旧 Alpha 0.65 透出暗内饰。
    修法（只改玻璃材质，车漆与预览环境不动）：Alpha 0.65→0.90（少透暗
    内饰）、底色 #9FC3D8→#33505F 深色镀膜（暗底衬出顶部辉光亮带）、
    Roughness 0.05→0.15（镜面越锐越忠实映出暗地面；稍放宽 lobe 才能
    蹭进地平线附近亮天光）、Specular IOR Level 1.0 不变（掠射更亮）。
    Metallic 仍 0。R1 加的细噪波 Bump 删掉：它把镜面 lobe 打散成均匀
    雾面，正是“平板感”的帮凶。另加 Transmission 0.10（与 ch-cars 同配方）。"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    ntree = mat.node_tree
    bsdf = ntree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = srgb_to_linear("#33505F")
    bsdf.inputs["Roughness"].default_value = 0.15
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Transmission Weight"].default_value = 0.10
    bsdf.inputs["Alpha"].default_value = 0.90
    bsdf.inputs["Specular IOR Level"].default_value = 1.0
    bsdf.inputs["IOR"].default_value = 1.45
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
    """金属轮毂：metallic 0.8，粗糙度 0.35 固定值（同 ch-cars v2）。"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    ntree = mat.node_tree
    bsdf = ntree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = srgb_to_linear("#C0C5C9")
    bsdf.inputs["Metallic"].default_value = 0.8
    bsdf.inputs["Roughness"].default_value = 0.35
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
# ---- 车材质（R2-T19 换装：导入材质 base 名 -> 本件规范材质）----
# 三车导入后同名材质（Windows/Black/Grey/Headlights/TailLights）各出现 3 份，
# 全部 remap 到同一份规范材质；Orange/DarkOrange 两档红各留一份。
MAT_PAINT_GREY = make_paint("ov-parking_paint_grey", "#8A8F94")
MAT_PAINT_BLUE = make_paint("ov-parking_paint_blue", "#3B82C4")
MAT_PAINT_RED = make_paint("ov-parking_paint_red", "#C4534E")
MAT_PAINT_RED_DARK = make_paint("ov-parking_paint_red_dark", "#C4534E")
MAT_GLASS = make_glass("ov-parking_glass")
MAT_TIRE = make_tire("ov-parking_tire")
MAT_HUB = make_hub("ov-parking_hub")
MAT_HEAD = make_lamp("ov-parking_headlamp", "#FFF6D8", "#FFF2CC", strength=1.0)
MAT_TAIL = make_lamp("ov-parking_taillamp", "#C03028", "#D04030", strength=0.8)

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
# 车材质（车漆/车窗/轮胎/轮毂/车灯）不挂图：导入材质直接染色（见上文）。
# 贴图 UV 按米缩放：{材质: 一重复多少米}
UV_TILE = {MAT_ASPHALT: 3.0, MAT_LINE: 1.0, MAT_MARKING: 1.0,
           MAT_STOP: 2.0}

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


# ---- 车辆（R2-T19 换装：Quaternius 网上车；局部坐标车长沿 X、车头 +X）----
# 导入材质 base 名 -> 本件规范材质（White 只出现在 SUV 上，染成灰色）。
CANON = {"Blue": MAT_PAINT_BLUE, "White": MAT_PAINT_GREY,
         "Orange": MAT_PAINT_RED, "DarkOrange": MAT_PAINT_RED_DARK,
         "Windows": MAT_GLASS, "Black": MAT_TIRE, "Grey": MAT_HUB,
         "Headlights": MAT_HEAD, "TailLights": MAT_TAIL}
CARS_DIR = os.path.join(BASE, "assets/external/cars/quaternius")


def _mat_face_centroid(obj, mat_name):
    """World-space centroid of faces using the given material slot."""
    idx = [i for i, m in enumerate(obj.data.materials)
           if m and m.name.split(".")[0] == mat_name]
    assert idx, f"{obj.name}: no material slot {mat_name}"
    mi = idx[0]
    pts = [obj.matrix_world @ p.center for p in obj.data.polygons
           if p.material_index == mi]
    assert pts, f"{obj.name}: no faces with {mat_name}"
    return sum(pts, Vector((0, 0, 0))) / len(pts)


def import_car(tag, filename, scale, cx, cy, rot_z_deg):
    """Import one Quaternius car (same pipeline as ch-cars v3, see its
    header): remap materials, bake +90 deg Z-rotation (front -Y -> +X)
    + scale into mesh data, body mesh origin shifted to height midpoint
    (named _roof, Godot anchor convention), parent under an empty at
    (cx, cy, LOT_Z1) with rotation rot_z_deg. scale is (sx, sy, sz) in
    the IMPORTED local axes (x=width, y=length, z=height)."""
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(CARS_DIR, filename))
    meshes = [o for o in bpy.context.scene.objects
              if o not in before and o.type == 'MESH']
    assert len(meshes) == 4, f"{tag}: expected 4 meshes, got {len(meshes)}"
    body = max(meshes, key=lambda o: len(o.data.materials))
    assert len(body.data.materials) >= 6, \
        f"{tag}: body has {len(body.data.materials)} materials, expected >=6"
    hl = _mat_face_centroid(body, "Headlights")
    tl = _mat_face_centroid(body, "TailLights")
    assert hl.y < -1.0 and tl.y > 1.0, \
        f"{tag}: headlight centroid y={hl.y:.2f}, taillight y={tl.y:.2f} " \
        "(expected front at -Y)"
    print(f"IMPORT {tag}: {filename} headlight y={hl.y:.2f} "
          f"taillight y={tl.y:.2f} (front -Y confirmed)")
    for o in meshes:
        for i, m in enumerate(list(o.data.materials)):
            base = m.name.split(".")[0]
            assert base in CANON, f"{tag}: unexpected material {m.name}"
            o.data.materials[i] = CANON[base]
    # bake rotation + scale directly into mesh data (deterministic;
    # bpy.ops.object.transform_apply silently skipped the rotation
    # in the 2026-11-24 ch-cars probe — scale baked, rotation not baked).
    bake = (Matrix.Rotation(math.radians(90), 4, 'Z')
            @ Matrix.Diagonal(scale + (1.0,)))
    for o in meshes:
        o.data.transform(bake)
    bpy.context.view_layer.update()
    hl2 = _mat_face_centroid(body, "ov-parking_headlamp")
    tl2 = _mat_face_centroid(body, "ov-parking_taillamp")
    assert hl2.x > 1.0 and tl2.x < -1.0, \
        f"{tag}: after bake headlight x={hl2.x:.2f}, taillight x={tl2.x:.2f} " \
        "(expected front at +X)"
    zs = [v.co.z for v in body.data.vertices]
    zmin, zmax = min(zs), max(zs)
    L = zmax - (zmax - zmin) / 2.0
    body.data.transform(Matrix.Translation((0, 0, -L)))
    body.location = (0, 0, L)
    print(f"IMPORT {tag}: roof top z={zmax:.3f} origin L={L:.3f}")
    all_zmin = min(min(v.co.z for v in o.data.vertices) + o.location.z
                   for o in meshes)
    lift = -all_zmin  # lowest point (wheel bottom) exactly at z=0, pre-empty
    body.name = "ov-parking_%s_roof" % tag
    bpy.context.view_layer.update()
    for o in meshes:
        if o is body:
            continue
        c = sum((o.matrix_world @ Vector(v) for v in o.bound_box),
                Vector((0, 0, 0))) / 8.0
        if c.x < 0:
            o.name = "ov-parking_%s_wheels_rear" % tag
        elif c.y > 0:
            o.name = "ov-parking_%s_wheel_FL" % tag
        else:
            o.name = "ov-parking_%s_wheel_FR" % tag
    # empty 抬高 LOT_Z1（0.08）：轮底正好落在沥青顶面，车身不悬空、不下陷
    bpy.ops.object.empty_add(type="PLAIN_AXES",
                             location=(cx, cy, LOT_Z1 + lift))
    grp = bpy.context.active_object
    grp.name = "ov-parking_%s" % tag
    grp.rotation_euler = (0, 0, math.radians(rot_z_deg))
    for o in meshes:
        o.parent = grp
    objs.append(grp)
    objs.extend(meshes)
    bpy.context.view_layer.update()
    for o in meshes:
        bb = [o.matrix_world @ Vector(v) for v in o.bound_box]
        mn = [min(v[i] for v in bb) for i in range(3)]
        mx = [max(v[i] for v in bb) for i in range(3)]
        print(f"  PLACED {o.name}: x[{mn[0]:.2f},{mx[0]:.2f}] "
              f"y[{mn[1]:.2f},{mx[1]:.2f}] z[{mn[2]:.2f},{mx[2]:.2f}]")
    return grp


def space_center_x(i):
    """第 i 个车位（1 起）中心 x。"""
    return lot_x0 + (i - 0.5) * SPACE_W


# 3 辆车：灰 SUV 2 号位（y -86.6，南移 0.10 避轮挡）、蓝 5 号位、红 9 号位
# （位置与 v1 一致），车头朝北（rot +90°：局部 +X -> +Y）。
# 缩放（sx=宽、sy=长、sz=高）：长 4.4 m、宽 1.80 m（见文件头换装说明）。
import_car("grey", "suv-quaternius.glb",
           (1.80 / 2.11, 4.4 / 4.21, 4.4 / 4.21),
           space_center_x(2), SPACE_Y_C - 0.10, 90)
import_car("blue", "car-quaternius.glb",
           (1.80 / 1.81, 4.4 / 4.22, 4.4 / 4.22),
           space_center_x(5), SPACE_Y_C, 90)
import_car("red", "sports-car-2-quaternius.glb",
           (1.80 / 1.80, 4.4 / 3.97, 4.4 / 3.97),
           space_center_x(9), SPACE_Y_C, 90)

print("parking objects:", len(objs))

# ---- drop orphaned imported materials (replaced by CANON) ----
for _m in list(bpy.data.materials):
    if _m.users == 0:
        bpy.data.materials.remove(_m)
print("materials in blend:", sorted(m.name for m in bpy.data.materials))

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

# ---- 材质校验（R2-T19 换装防回归）：4 种车漆须带清漆、颜色不链接 ----
for _m in [m for m in bpy.data.materials
           if m.name.startswith("ov-parking_paint_")]:
    _b = _m.node_tree.nodes["Principled BSDF"]
    assert not _b.inputs["Base Color"].is_linked, f"{_m.name}: Base Color linked!"
    assert not _b.inputs["Roughness"].is_linked, f"{_m.name}: Roughness linked!"
    assert abs(_b.inputs["Coat Weight"].default_value - 1.0) < 1e-6, \
        f"{_m.name}: Coat Weight != 1.0"
    assert abs(_b.inputs["Coat Roughness"].default_value - 0.05) < 1e-6, \
        f"{_m.name}: Coat Roughness != 0.05"
print("MATERIAL CHECK PASS: car paint clearcoat Coat Weight 1.0 / "
      "Coat Roughness 0.05")
# glass fix 2026-11-24: tinted glass, low see-through, strong specular
_g = MAT_GLASS.node_tree.nodes["Principled BSDF"]
assert abs(_g.inputs["Transmission Weight"].default_value - 0.10) < 1e-6, \
    "ov-parking_glass: Transmission Weight != 0.10"
assert abs(_g.inputs["Alpha"].default_value - 0.90) < 1e-6, \
    "ov-parking_glass: Alpha != 0.90"
assert abs(_g.inputs["Roughness"].default_value - 0.15) < 1e-6, \
    "ov-parking_glass: Roughness != 0.15"
assert abs(_g.inputs["Specular IOR Level"].default_value - 1.0) < 1e-6, \
    "ov-parking_glass: Specular IOR Level != 1.0"
assert not _g.inputs["Normal"].is_linked, "ov-parking_glass: Normal linked (bump)!"
print("GLASS CHECK PASS: transmission 0.10 / alpha 0.90 / roughness 0.15 / "
      "specular 1.0, no bump")

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
