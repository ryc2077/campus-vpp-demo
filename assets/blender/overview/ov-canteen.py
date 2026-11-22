# ov-canteen v2: 餐厅楼体返工 (overview piece)
# 32(x) x 13(y) m, Blender 中心 (60, 56, 0), 3F, 示意总高 15 m
# 位置/尺寸/朝向照旧版与 SPEC §4 + campus.json, 不改楼的位置和占地。
# campus.json 餐厅色 #E8C9C0(淡粉) 与 SPEC §3/#F6D9C0(浅橙) 不一致,
# 墙面以 SPEC §5 浅橙为准, 红饰按鸟瞰图补。
# v2 返工内容 (筛查结论: 旧版是白盒子——所有面放大后均匀纯色,
# 屋顶是深灰平板, 缺红饰):
# - 红饰 (按鸟瞰图位置, 砖纹材质不是纯色条): 四角红墩柱 + 东西两端
#   红山墙板 + 南北长面红竖墩 (x ±5.5/±13.5) + 檐下红腰线 (13.7-14.0)。
#   红砖 #A63A2C, Brick 砖缝 + Noise 斑驳 + Bump。
# - 墙面: 程序化涂料纹 (Noise 斑驳 + Bump, 粗糙度变化),
#   楼层分缝 (檐口线脚 + 线脚下暗色缝线), 雨水渍/风化 (竖向渍痕,
#   墙根加重); 墙色浅橙 #F6D9C0, sRGB->线性赋值。
# - 女儿墙: 顶面 = 屋顶板顶面 +0.65 m (=14.95), 厚 0.3 m, 压顶略出挑。
# - 屋顶: 深灰防水卷材纹 (Brick 搭接缝 + Noise 颗粒 + Bump),
#   不再是深灰平板。
# - 窗带 (本件自带, SPEC §5: 餐厅"带简单窗带"; ov-windows-roofs 只做
#   A/B/C 三栋的窗, 不含餐厅): 每层横向窗带 + 竖分格条, 嵌进墙面
#   (框板 + 上下框 + 侧框 + 窗台, 玻璃内凹 0.06); 玻璃淡蓝灰
#   #9FC3D8, 透明度 0.8 + 镜面反射 (Specular 1.0, 粗糙度 0.08-0.22 变化),
#   不是平蓝板。F1 南侧窗带在正门处断开 (x ±1.6 留门洞); 东西短面
#   窗带分两段, 避开中央红色山墙板。
# - 空调外机: 每层长边 3 台 + 短边每层 1 台, F1 南侧正门上方 1 台让位,
#   共 23 台: 小灰盒 + 波纹格栅 + 托架。外机贴墙下沿 (z0+0.75),
#   避开窗带高度 (窗带见本件窗带段, 外机贴墙下沿 z0+0.75)。
# - 正门 + 门廊雨棚 + 台阶 (南立面正中, 南 = -y, 朝校园内侧)。
# - 全部结构件带小倒角 (薄件除外)。
#
# Height note: campus.json 高度为"示意"; 实测层高 (1F 3.5 m, 2-3F 3.0 m)
# 只加到 9.5 m, SPEC §4 信封 15 m / 3F, 楼层在信封内拉长:
# 基座 0-0.5, F1 0.5-5.0, F2 5.0-9.5, F3 9.5-14.0 (每层 4.5 m, 餐厅层高
# 本就大于教室), 屋顶板 14.0-14.3, 女儿墙顶 14.95。
# 本次不渲染 (新规矩: 渲染全部走 GitHub Actions, 本地不渲染):
# 只建模 -> 存 .blend -> 导出 .glb -> 回读校验, 打印 DONE ov-canteen。

import bpy
import os

PIECE = "ov-canteen"
BASE = os.path.expanduser("~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
PY_DIR = os.path.join(BASE, "assets/blender/overview")
BLEND_PATH = os.path.join(PY_DIR, "ov-canteen.blend")
GLB_PATH = os.path.join(BASE, "assets/models/ov-canteen.glb")

CX, CY = 60.0, 56.0   # building centre (Blender x, y)
W, D = 32.0, 13.0     # footprint x, y


def hex_rgb(h):
    """Hex sRGB -> linear RGB (Blender stores Base Color linear)."""
    h = h.lstrip("#")

    def srgb_to_lin(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (srgb_to_lin(int(h[i:i + 2], 16)) for i in (0, 2, 4))
    return (r, g, b, 1.0)


def _ramp(nt, name, stops):
    """stops: list of (pos, hex). Returns ColorRamp node."""
    n = nt.nodes.new("ShaderNodeValToRGB")
    n.name = name
    cr = n.color_ramp
    while len(cr.elements) > 1:
        cr.elements.remove(cr.elements[-1])
    cr.elements[0].position, cr.elements[0].color = stops[0][0], hex_rgb(stops[0][1])
    for pos, hx in stops[1:]:
        e = cr.elements.new(pos)
        e.color = hex_rgb(hx)
    return n


def _noise(nt, name, scale, detail=3, rough=0.7, distort=0.0):
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.name = name
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    n.inputs["Roughness"].default_value = rough
    n.inputs["Distortion"].default_value = distort
    return n


def _bump(nt, height_socket, strength=0.4, distance=0.08):
    b = nt.nodes.new("ShaderNodeBump")
    b.inputs["Strength"].default_value = strength
    b.inputs["Distance"].default_value = distance
    nt.links.new(height_socket, b.inputs["Height"])
    return b


def _new_mat(name, hexcol, rough=0.85, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = hex_rgb(hexcol)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    return m, bsdf


def wall_mat():
    """浅橙涂料墙: 大尺度斑驳 + 细颗粒 Bump + 竖向雨水渍 (墙根加重)."""
    m, bsdf = _new_mat("Canteen_Wall_Orange_F6D9C0_tex", "#F6D9C0", 0.85)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n1 = _noise(nt, "Mottle", 0.35, detail=3, rough=0.7)
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    ramp1 = _ramp(nt, "MottleRamp", [(0.0, "#E8C4A2"), (0.5, "#F6D9C0"), (1.0, "#FBE9D6")])
    nt.links.new(n1.outputs["Fac"], ramp1.inputs["Fac"])
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.6, 1.6, 0.25)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    n2 = _noise(nt, "Streaks", 1.1, detail=2, rough=0.75)
    nt.links.new(mp.outputs["Vector"], n2.inputs["Vector"])
    ramp2 = _ramp(nt, "StreakRamp", [(0.0, "#000000"), (0.62, "#000000"), (0.85, "#FFFFFF")])
    ramp2.color_ramp.elements[0].color = (0, 0, 0, 1)
    ramp2.color_ramp.elements[1].color = (0, 0, 0, 1)
    ramp2.color_ramp.elements[2].color = (1, 1, 1, 1)
    nt.links.new(n2.outputs["Fac"], ramp2.inputs["Fac"])
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
    sub = nt.nodes.new("ShaderNodeMath")
    sub.operation = "SUBTRACT"
    sub.inputs[0].default_value = 1.0
    nt.links.new(sep.outputs["Z"], sub.inputs[1])
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    nt.links.new(ramp2.outputs["Color"], mul.inputs[0])
    nt.links.new(sub.outputs["Value"], mul.inputs[1])
    mul2 = nt.nodes.new("ShaderNodeMath")
    mul2.operation = "MULTIPLY"
    mul2.inputs[1].default_value = 0.55
    nt.links.new(mul.outputs["Value"], mul2.inputs[0])
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MIX"
    nt.links.new(ramp1.outputs["Color"], mix.inputs["Color1"])
    mix.inputs["Color2"].default_value = hex_rgb("#D9B48E")
    nt.links.new(mul2.outputs["Value"], mix.inputs["Fac"])
    nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    n3 = _noise(nt, "Grain", 2.2, detail=2, rough=0.8)
    nt.links.new(tc.outputs["Object"], n3.inputs["Vector"])
    b = _bump(nt, n3.outputs["Fac"], strength=0.35, distance=0.06)
    nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.3
    mr.inputs["From Max"].default_value = 0.7
    mr.inputs["To Min"].default_value = 0.72
    mr.inputs["To Max"].default_value = 0.95
    nt.links.new(n1.outputs["Fac"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])
    return m


def roof_mat():
    """深灰防水屋顶: Noise 颗粒 + Brick 卷材搭接缝 + Bump."""
    m, bsdf = _new_mat("Canteen_Roof_DarkGrey_424A52_tex", "#424A52", 0.92)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    brick = nt.nodes.new("ShaderNodeTexBrick")
    brick.inputs["Scale"].default_value = 0.7
    brick.inputs["Mortar Size"].default_value = 0.02
    brick.inputs["Brick Width"].default_value = 1.0
    brick.inputs["Row Height"].default_value = 1.0
    brick.inputs["Color1"].default_value = hex_rgb("#424A52")
    brick.inputs["Color2"].default_value = hex_rgb("#4B545E")
    brick.inputs["Mortar"].default_value = hex_rgb("#2B3138")
    nt.links.new(tc.outputs["Object"], brick.inputs["Vector"])
    n1 = _noise(nt, "Grain", 1.4, detail=3, rough=0.75)
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    ramp1 = _ramp(nt, "GrainRamp", [(0.0, "#3A4048"), (0.5, "#454D57"), (1.0, "#525B66")])
    nt.links.new(n1.outputs["Fac"], ramp1.inputs["Fac"])
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MIX"
    mix.inputs["Fac"].default_value = 0.4
    nt.links.new(brick.outputs["Color"], mix.inputs["Color1"])
    nt.links.new(ramp1.outputs["Color"], mix.inputs["Color2"])
    nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    n2 = _noise(nt, "BumpGrain", 3.0, detail=2, rough=0.8)
    nt.links.new(tc.outputs["Object"], n2.inputs["Vector"])
    b = _bump(nt, n2.outputs["Fac"], strength=0.5, distance=0.05)
    nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def conc_mat():
    """混凝土: 斑驳 + 颗粒 Bump (基座/女儿墙/压顶/台阶/雨棚)."""
    m, bsdf = _new_mat("Canteen_Concrete_B9B3A8_tex", "#B9B3A8", 0.95)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n1 = _noise(nt, "Mottle", 0.6, detail=3, rough=0.7)
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    ramp1 = _ramp(nt, "MottleRamp", [(0.0, "#A39D90"), (0.5, "#B9B3A8"), (1.0, "#C9C3B6")])
    nt.links.new(n1.outputs["Fac"], ramp1.inputs["Fac"])
    nt.links.new(ramp1.outputs["Color"], bsdf.inputs["Base Color"])
    n2 = _noise(nt, "Grain", 3.0, detail=2, rough=0.8)
    nt.links.new(tc.outputs["Object"], n2.inputs["Vector"])
    b = _bump(nt, n2.outputs["Fac"], strength=0.4, distance=0.05)
    nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def band_mat():
    """檐口/线脚: 浅色铺装色, 轻微斑驳."""
    m, bsdf = _new_mat("Canteen_Cornice_D8D2C4_tex", "#D8D2C4", 0.9)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n1 = _noise(nt, "Mottle", 0.8, detail=2, rough=0.7)
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    ramp1 = _ramp(nt, "MottleRamp", [(0.0, "#C6BFA9"), (0.5, "#D8D2C4"), (1.0, "#E6E0CE")])
    nt.links.new(n1.outputs["Fac"], ramp1.inputs["Fac"])
    nt.links.new(ramp1.outputs["Color"], bsdf.inputs["Base Color"])
    b = _bump(nt, n1.outputs["Fac"], strength=0.25, distance=0.04)
    nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def red_brick_mat():
    """红饰: 砖红 #A63A2C, Brick 砖缝 + Noise 斑驳 + Bump, 不是纯色条。
    砖缝深红, 砖面两档红深浅交错, 再叠大尺度斑驳。"""
    m, bsdf = _new_mat("Canteen_RedBrick_A63A2C_tex", "#A63A2C", 0.85)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (0.8, 0.8, 0.8)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    brick = nt.nodes.new("ShaderNodeTexBrick")
    brick.offset = 0.5
    brick.inputs["Scale"].default_value = 1.6
    brick.inputs["Mortar Size"].default_value = 0.025
    brick.inputs["Brick Width"].default_value = 0.6
    brick.inputs["Row Height"].default_value = 0.22
    brick.inputs["Color1"].default_value = hex_rgb("#A63A2C")
    brick.inputs["Color2"].default_value = hex_rgb("#B04936")
    brick.inputs["Mortar"].default_value = hex_rgb("#7E2A20")
    nt.links.new(mp.outputs["Vector"], brick.inputs["Vector"])
    n1 = _noise(nt, "Mottle", 0.9, detail=3, rough=0.7)
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    ramp1 = _ramp(nt, "MottleRamp", [(0.0, "#8E2F22"), (0.5, "#A63A2C"), (1.0, "#BC5240")])
    nt.links.new(n1.outputs["Fac"], ramp1.inputs["Fac"])
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MIX"
    mix.inputs["Fac"].default_value = 0.45
    nt.links.new(brick.outputs["Color"], mix.inputs["Color1"])
    nt.links.new(ramp1.outputs["Color"], mix.inputs["Color2"])
    nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    n2 = _noise(nt, "Grain", 3.0, detail=2, rough=0.8)
    nt.links.new(tc.outputs["Object"], n2.inputs["Vector"])
    b = _bump(nt, n2.outputs["Fac"], strength=0.45, distance=0.05)
    nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def wood_mat():
    """正门木色: 暖棕 + 竖纹 Noise + 轻 Bump."""
    m, bsdf = _new_mat("Canteen_Door_Wood_8A6B4A_tex", "#8A6B4A", 0.7)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (2.0, 0.6, 2.0)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    n1 = _noise(nt, "WoodGrain", 1.2, detail=3, rough=0.7)
    nt.links.new(mp.outputs["Vector"], n1.inputs["Vector"])
    ramp1 = _ramp(nt, "WoodRamp", [(0.0, "#6E5334"), (0.5, "#8A6B4A"), (1.0, "#A5865F")])
    nt.links.new(n1.outputs["Fac"], ramp1.inputs["Fac"])
    nt.links.new(ramp1.outputs["Color"], bsdf.inputs["Base Color"])
    b = _bump(nt, n1.outputs["Fac"], strength=0.3, distance=0.04)
    nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def metal_mat(hexcol="#C0C5C9", name="Canteen_MetalGrey_tex", rough=0.55, metallic=0.3):
    m, bsdf = _new_mat(name, hexcol, rough, metallic)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n1 = _noise(nt, "Grain", 3.5, detail=2, rough=0.8)
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    b = _bump(nt, n1.outputs["Fac"], strength=0.15, distance=0.02)
    nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def grille_mat():
    """空调格栅: 深灰 + 横向波纹条纹 (百叶感) + Bump."""
    m, bsdf = _new_mat("Canteen_AC_Grille_3A4046_tex", "#3A4046", 0.7, 0.1)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wv = nt.nodes.new("ShaderNodeTexWave")
    wv.wave_type = "BANDS"
    wv.bands_direction = "Z"
    wv.inputs["Scale"].default_value = 14.0
    wv.inputs["Distortion"].default_value = 0.0
    wv.inputs["Detail"].default_value = 0.0
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    ramp = _ramp(nt, "SlatRamp", [(0.0, "#23282D"), (0.5, "#4A525A"), (1.0, "#23282D")])
    nt.links.new(wv.outputs["Color"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    b = _bump(nt, wv.outputs["Color"], strength=0.6, distance=0.03)
    nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def glass_mat():
    """窗玻璃: 淡蓝灰 #9FC3D8, 透明度 0.8 + 镜面反射 + 粗糙度变化。
    不是平蓝板: Specular IOR Level 1.0, 粗糙度随 Noise 在 0.08-0.22 变化。"""
    m, bsdf = _new_mat("Canteen_Glass_9FC3D8_tex", "#9FC3D8", 0.12, 0.0)
    bsdf.inputs["Alpha"].default_value = 0.8
    bsdf.inputs["Specular IOR Level"].default_value = 1.0
    try:
        m.surface_render_method = "BLENDED"
    except Exception:
        pass
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n1 = _noise(nt, "Grain", 2.5, detail=2, rough=0.8)
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.3
    mr.inputs["From Max"].default_value = 0.7
    mr.inputs["To Min"].default_value = 0.08
    mr.inputs["To Max"].default_value = 0.22
    nt.links.new(n1.outputs["Fac"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])
    return m


MAT_WALL = wall_mat()
MAT_ROOF = roof_mat()
MAT_CONC = conc_mat()
MAT_BAND = band_mat()
MAT_RED = red_brick_mat()
MAT_WOOD = wood_mat()
MAT_METAL = metal_mat()
MAT_AC_BODY = metal_mat("#D5D9DC", "Canteen_AC_Body_D5D9DC", 0.5, 0.25)
MAT_GRILLE = grille_mat()
MAT_GLASS = glass_mat()
MAT_FRAME = metal_mat("#C0C5C9", "Canteen_Frame_C0C5C9", 0.45, 0.35)
MAT_SEAM = _new_mat("Canteen_FloorSeam_B7A988", "#B7A988", 0.9)[0]


def build():
    # ---- clean scene ----
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    building = []  # objects that go into the .glb

    def box(name, cx, cy, z0, z1, sx, sy, mat, bevel=0.05):
        bpy.ops.mesh.primitive_cube_add(location=(cx, cy, (z0 + z1) / 2.0))
        o = bpy.context.active_object
        o.name = name
        o.dimensions = (sx, sy, z1 - z0)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        if bevel and min(sx, sy, z1 - z0) > 2 * bevel + 0.02:
            mod = o.modifiers.new("EdgeSoft", "BEVEL")
            mod.width = bevel
            mod.segments = 2
            mod.limit_method = "ANGLE"
        o.data.materials.append(mat)
        building.append(o)
        return o

    # ---- plinth (0-0.5) + cap ----
    box("canteen_plinth", CX, CY, 0.0, 0.5, W + 0.6, D + 0.6, MAT_CONC, bevel=0.04)
    box("canteen_plinth_cap", CX, CY, 0.5, 0.68, W + 0.7, D + 0.7, MAT_BAND, bevel=0.03)

    # ---- main wall blocks: F1 0.5-5.0 (32x13), F2 5.0-9.5 (31.8x12.8),
    #      F3 9.5-14.0 (31.6x12.6), 收分 0.1/边 ----
    box("canteen_body_F1", CX, CY, 0.5, 5.0, 32.0, 13.0, MAT_WALL, bevel=0.06)
    box("canteen_body_F2", CX, CY, 5.0, 9.5, 31.8, 12.8, MAT_WALL, bevel=0.06)
    box("canteen_body_F3", CX, CY, 9.5, 14.0, 31.6, 12.6, MAT_WALL, bevel=0.06)

    # ---- floor cornice bands (檐口线脚) + dark seam groove just below ----
    for i, zc in enumerate((0.5, 5.0, 9.5)):
        box("canteen_cornice_F%d" % (i + 1), CX, CY, zc - 0.09, zc + 0.09,
            32.3, 13.3, MAT_BAND, bevel=0.03)
        box("canteen_seam_F%d" % (i + 1), CX, CY, zc - 0.24, zc - 0.18,
            32.06, 13.06, MAT_SEAM, bevel=0.0)
    # top cornice (14.0, 混凝土色)
    box("canteen_cornice_top", CX, CY, 13.91, 14.09, 32.3, 13.3, MAT_CONC, bevel=0.03)

    # ---- red accents (鸟瞰图: 两端山墙红 + 立面红墩 + 檐下红腰线) ----
    # 四角红墩柱 1.4x1.4, 通高 0.5-14.0, 两面各出挑约 0.2
    for sxn, syn in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        box("canteen_red_corner_%s%s" % ("E" if sxn > 0 else "W", "N" if syn > 0 else "S"),
            CX + sxn * 15.5, CY + syn * 6.0, 0.5, 14.0, 1.4, 1.4, MAT_RED, bevel=0.04)
    # 东西两端红山墙板: 端面正中, 宽 8.0(y), 通高 0.5-14.0, 出挑 0.12
    box("canteen_red_gable_E", CX + 16.06, CY, 0.5, 14.0, 0.12, 8.0, MAT_RED, bevel=0.0)
    box("canteen_red_gable_W", CX - 16.06, CY, 0.5, 14.0, 0.12, 8.0, MAT_RED, bevel=0.0)
    # 南北长面红竖墩: x = ±5.5 / ±13.5, 宽 0.9, 通高 0.5-14.0, 出挑 0.12
    for sgn in (1, -1):
        for off in (5.5, 13.5):
            box("canteen_red_pier_%s_%d" % ("N" if sgn > 0 else "S", int(off * 10)),
                CX + off, CY + sgn * 6.56, 0.5, 14.0, 0.9, 0.12, MAT_RED, bevel=0.0)
            box("canteen_red_pier_%s_m%d" % ("N" if sgn > 0 else "S", int(off * 10)),
                CX - off, CY + sgn * 6.56, 0.5, 14.0, 0.9, 0.12, MAT_RED, bevel=0.0)
    # 檐下红腰线 13.7-14.0, 四面, 出挑 0.06 (F3 墙面 31.6x12.6)
    box("canteen_red_frieze_N", CX, CY + 6.36, 13.7, 14.0, 31.72, 0.12, MAT_RED, bevel=0.0)
    box("canteen_red_frieze_S", CX, CY - 6.36, 13.7, 14.0, 31.72, 0.12, MAT_RED, bevel=0.0)
    box("canteen_red_frieze_E", CX + 15.86, CY, 13.7, 14.0, 0.12, 12.72, MAT_RED, bevel=0.0)
    box("canteen_red_frieze_W", CX - 15.86, CY, 13.7, 14.0, 0.12, 12.72, MAT_RED, bevel=0.0)

    # ---- roof slab (dark grey membrane, inside parapet) 14.0-14.3 ----
    box("canteen_roof_slab", CX, CY, 14.0, 14.3, 31.0, 12.0, MAT_ROOF, bevel=0.03)

    # ---- parapet (女儿墙): 顶面 = 板顶 14.3 + 0.65 = 14.95, 厚 0.3 m,
    #      墙 14.3-14.87 + 压顶 14.87-14.95 (出挑 0.06/边) ----
    PW, PD = 31.6, 12.6   # parapet outer footprint = top-floor footprint
    T = 0.30
    box("canteen_parapet_S", CX, CY - (PD / 2 - T / 2), 14.3, 14.87, PW, T, MAT_CONC, bevel=0.02)
    box("canteen_parapet_N", CX, CY + (PD / 2 - T / 2), 14.3, 14.87, PW, T, MAT_CONC, bevel=0.02)
    box("canteen_parapet_W", CX - (PW / 2 - T / 2), CY, 14.3, 14.87, T, PD - 2 * T, MAT_CONC, bevel=0.02)
    box("canteen_parapet_E", CX + (PW / 2 - T / 2), CY, 14.3, 14.87, T, PD - 2 * T, MAT_CONC, bevel=0.02)
    box("canteen_parapet_cap_S", CX, CY - (PD / 2 - T / 2), 14.87, 14.95, PW, T + 0.12, MAT_CONC, bevel=0.02)
    box("canteen_parapet_cap_N", CX, CY + (PD / 2 - T / 2), 14.87, 14.95, PW, T + 0.12, MAT_CONC, bevel=0.02)
    box("canteen_parapet_cap_W", CX - (PW / 2 - T / 2), CY, 14.87, 14.95, T + 0.12, PD - 2 * T, MAT_CONC, bevel=0.02)
    box("canteen_parapet_cap_E", CX + (PW / 2 - T / 2), CY, 14.87, 14.95, T + 0.12, PD - 2 * T, MAT_CONC, bevel=0.02)

    # ---- roof equipment boxes: tall, louvred, readable above parapet ----
    def roof_equip(prefix, ex, ey, bw, bd, ztop, louvre_side):
        box(prefix, ex, ey, 14.3, ztop, bw, bd, MAT_METAL, bevel=0.04)
        box(prefix + "_lid", ex, ey, ztop, ztop + 0.12, bw + 0.2, bd + 0.2,
            MAT_ROOF, bevel=0.02)
        for k, zl in enumerate((ztop - 0.95, ztop - 0.6, ztop - 0.25)):
            if louvre_side == "S":
                box("%s_louvre_%d" % (prefix, k), ex, ey - bd / 2 - 0.02,
                    zl - 0.06, zl + 0.06, bw - 0.5, 0.05, MAT_GRILLE, bevel=0.0)
            else:
                box("%s_louvre_%d" % (prefix, k), ex, ey + bd / 2 + 0.02,
                    zl - 0.06, zl + 0.06, bw - 0.5, 0.05, MAT_GRILLE, bevel=0.0)

    roof_equip("canteen_roof_eq1", 52.0, 54.0, 2.6, 2.0, 15.5, "S")
    roof_equip("canteen_roof_eq2", 68.0, 58.0, 2.0, 1.6, 15.3, "N")

    # ---- main entrance: south face centre (south = -y, 朝校园内侧) ----
    SY = CY - D / 2  # south wall face y = 49.5
    box("canteen_door_frame", CX, SY - 0.06, 0.5, 3.1, 2.8, 0.22, MAT_BAND, bevel=0.03)
    box("canteen_door_L", CX - 0.6, SY - 0.14, 0.5, 3.0, 1.16, 0.10, MAT_WOOD, bevel=0.02)
    box("canteen_door_R", CX + 0.6, SY - 0.14, 0.5, 3.0, 1.16, 0.10, MAT_WOOD, bevel=0.02)
    box("canteen_door_handle_L", CX - 0.12, SY - 0.24, 1.35, 1.45, 0.05, 0.08, MAT_METAL, bevel=0.0)
    box("canteen_door_handle_R", CX + 0.12, SY - 0.24, 1.35, 1.45, 0.05, 0.08, MAT_METAL, bevel=0.0)
    # canopy slab 8.0 x 2.4 at z 3.6-3.85, out from the wall
    box("canteen_entry_canopy", CX, SY - 1.2, 3.6, 3.85, 8.0, 2.4, MAT_CONC, bevel=0.03)
    box("canteen_canopy_edge", CX, SY - 2.34, 3.6, 3.74, 8.0, 0.12, MAT_BAND, bevel=0.02)
    # canopy columns (0.3 sq) from ground to canopy, at the outer corners
    box("canteen_entry_col_L", CX - 3.5, SY - 2.2, 0.0, 3.6, 0.3, 0.3, MAT_CONC, bevel=0.02)
    box("canteen_entry_col_R", CX + 3.5, SY - 2.2, 0.0, 3.6, 0.3, 0.3, MAT_CONC, bevel=0.02)
    # steps: 3 steps down from plinth top 0.5 to ground, in front of the door
    box("canteen_step_1", CX, SY - 1.0, 0.33, 0.5, 4.0, 0.7, MAT_CONC, bevel=0.02)
    box("canteen_step_2", CX, SY - 1.65, 0.17, 0.33, 4.0, 0.6, MAT_CONC, bevel=0.02)
    box("canteen_step_3", CX, SY - 2.2, 0.0, 0.17, 4.0, 0.5, MAT_CONC, bevel=0.02)

    # ---- AC outdoor units: per floor, long sides 3 each + short sides 1 each ----
    # floor z0s: F1 0.5, F2 5.0, F3 9.5; unit centre z0+0.75 (below window band).
    # F1 south-centre unit skipped: the main entrance + canopy sit there.
    def ac_unit(prefix, ux, uy, zc, facing):
        if facing in ("S", "N"):
            bw, bd = 0.9, 0.28
            gx, gy = ux, uy + (0.15 if facing == "N" else -0.15)
            box(prefix, ux, uy, zc - 0.31, zc + 0.31, bw, bd, MAT_AC_BODY, bevel=0.02)
            box(prefix + "_grille", gx, gy, zc - 0.22, zc + 0.22, 0.78, 0.03,
                MAT_GRILLE, bevel=0.0)
            box(prefix + "_bracket", ux, uy, zc - 0.40, zc - 0.34, 0.9, 0.10,
                MAT_METAL, bevel=0.0)
        else:
            bw, bd = 0.28, 0.9
            gx, gy = ux + (0.15 if facing == "E" else -0.15), uy
            box(prefix, ux, uy, zc - 0.31, zc + 0.31, bw, bd, MAT_AC_BODY, bevel=0.02)
            box(prefix + "_grille", gx, gy, zc - 0.22, zc + 0.22, 0.03, 0.78,
                MAT_GRILLE, bevel=0.0)
            box(prefix + "_bracket", ux, uy, zc - 0.40, zc - 0.34, 0.10, 0.9,
                MAT_METAL, bevel=0.0)

    n_ac = 0
    for fi, z0 in enumerate((0.5, 5.0, 9.5)):
        zc = z0 + 0.75
        hw = 15.8 if fi == 2 else (15.9 if fi == 1 else 16.0)
        hd = 6.3 if fi == 2 else (6.4 if fi == 1 else 6.5)
        for j, off in enumerate((-12.0, 0.0, 12.0)):
            if fi == 0 and j == 1:
                # south-centre F1: entrance canopy/door occupies this spot
                ac_unit("canteen_ac_F%d_N%d" % (fi + 1, j), CX + off, CY + hd + 0.14, zc, "N")
                n_ac += 1
                continue
            ac_unit("canteen_ac_F%d_S%d" % (fi + 1, j), CX + off, CY - hd - 0.14, zc, "S")
            ac_unit("canteen_ac_F%d_N%d" % (fi + 1, j), CX + off, CY + hd + 0.14, zc, "N")
            n_ac += 2
        ac_unit("canteen_ac_F%d_E0" % (fi + 1), CX + hw + 0.14, CY, zc, "E")
        ac_unit("canteen_ac_F%d_W0" % (fi + 1), CX - hw - 0.14, CY, zc, "W")
        n_ac += 2
    print("AC outdoor units:", n_ac)

    # ---- window bands (本件自带, SPEC §5): 横向窗带 + 竖分格, 嵌进墙面 ----
    # 框板 (墙面内) + 玻璃 (内凹, 外表面比框外表面低 0.06) + 上下框 +
    # 侧框 + 窗台 (出挑 0.14 的小檐) + 竖挺 (每 3 m, 避开红墩位置)。
    # 每层窗带 z: F1 1.75-3.55 (避雨棚 3.6 / 外机顶 1.56),
    # F2 6.1-7.9, F3 10.6-12.4。
    def window_band(prefix, c_along, face, z0, z1, length, facing, mullions=True):
        # facing N/S: 沿 x 走, face = 墙面 y; facing E/W: 沿 y 走, face = 墙面 x
        h = z1 - z0
        if facing in ("N", "S"):
            sgn = 1 if facing == "N" else -1
            yf = face
            # 框板: 长 length, 高 h+0.24, 厚 0.08, 外表面 +0.04
            box(prefix + "_frame_back", c_along, yf + sgn * 0.0, z0 - 0.12, z1 + 0.12,
                length, 0.08, MAT_FRAME, bevel=0.0)
            # 玻璃: 长 length-0.3, 高 h, 厚 0.06, 外表面 +0.03 (内凹 0.06)
            box(prefix + "_glass", c_along, yf, z0, z1,
                length - 0.3, 0.06, MAT_GLASS, bevel=0.0)
            # 上下框: 厚 0.14, 外表面 +0.09
            box(prefix + "_rail_top", c_along, yf + sgn * 0.02, z1 - 0.0, z1 + 0.14,
                length, 0.14, MAT_FRAME, bevel=0.0)
            box(prefix + "_rail_bot", c_along, yf + sgn * 0.02, z0 - 0.14, z0,
                length, 0.14, MAT_FRAME, bevel=0.0)
            # 侧框: 宽 0.14, 两端
            box(prefix + "_jamb_L", c_along - length / 2 + 0.07, yf + sgn * 0.02,
                z0 - 0.14, z1 + 0.14, 0.14, 0.14, MAT_FRAME, bevel=0.0)
            box(prefix + "_jamb_R", c_along + length / 2 - 0.07, yf + sgn * 0.02,
                z0 - 0.14, z1 + 0.14, 0.14, 0.14, MAT_FRAME, bevel=0.0)
            # 窗台: 长 length+0.24, 高 0.10, 厚 0.20, 外表面 +0.14
            box(prefix + "_sill", c_along, yf + sgn * 0.04, z0 - 0.22, z0 - 0.12,
                length + 0.24, 0.20, MAT_BAND, bevel=0.02)
            # 竖挺: 每 3 m 一根, 避开红墩 (x = CX±5.5 / ±13.5, 0.75 m 内跳过)
            if mullions:
                x = c_along - length / 2 + 1.5
                n = 0
                while x < c_along + length / 2 - 0.5:
                    if min(abs(x - (CX + p)) for p in (-13.5, -5.5, 5.5, 13.5)) > 0.75:
                        box("%s_mull_%d" % (prefix, n), x, yf + sgn * 0.02,
                            z0, z1, 0.12, 0.10, MAT_METAL, bevel=0.0)
                    x += 3.0
                    n += 1
        else:
            sgn = 1 if facing == "E" else -1
            xf = face
            box(prefix + "_frame_back", xf + sgn * 0.0, c_along, z0 - 0.12, z1 + 0.12,
                0.08, length, MAT_FRAME, bevel=0.0)
            box(prefix + "_glass", xf, c_along, z0, z1,
                0.06, length - 0.3, MAT_GLASS, bevel=0.0)
            box(prefix + "_rail_top", xf + sgn * 0.02, c_along, z1 - 0.0, z1 + 0.14,
                0.14, length, MAT_FRAME, bevel=0.0)
            box(prefix + "_rail_bot", xf + sgn * 0.02, c_along, z0 - 0.14, z0,
                0.14, length, MAT_FRAME, bevel=0.0)
            box(prefix + "_jamb_L", xf + sgn * 0.02, c_along - length / 2 + 0.07,
                z0 - 0.14, z1 + 0.14, 0.14, 0.14, MAT_FRAME, bevel=0.0)
            box(prefix + "_jamb_R", xf + sgn * 0.02, c_along + length / 2 - 0.07,
                z0 - 0.14, z1 + 0.14, 0.14, 0.14, MAT_FRAME, bevel=0.0)
            box(prefix + "_sill", xf + sgn * 0.04, c_along, z0 - 0.22, z0 - 0.12,
                0.20, length + 0.24, MAT_BAND, bevel=0.02)
            if mullions:
                box(prefix + "_mull_0", xf + sgn * 0.02, c_along, z0, z1,
                    0.10, 0.12, MAT_METAL, bevel=0.0)

    n_win = 0
    for fi, (wz0, wz1) in enumerate(((1.75, 3.55), (6.1, 7.9), (10.6, 12.4))):
        hw = 15.8 if fi == 2 else (15.9 if fi == 1 else 16.0)
        hd = 6.3 if fi == 2 else (6.4 if fi == 1 else 6.5)
        blen = 27.6 if fi == 2 else (27.8 if fi == 1 else 28.0)
        # 北面: 整条
        window_band("canteen_win_F%d_N" % (fi + 1), CX, CY + hd, wz0, wz1, blen, "N")
        n_win += 1
        # 南面: F1 在正门处断开 (两段, 各 12.4 m, 中间留 ±1.6 门洞); F2/F3 整条
        if fi == 0:
            window_band("canteen_win_F1_S_L", CX - 7.8, CY - hd, wz0, wz1, 12.4, "S")
            window_band("canteen_win_F1_S_R", CX + 7.8, CY - hd, wz0, wz1, 12.4, "S")
            n_win += 2
        else:
            window_band("canteen_win_F%d_S" % (fi + 1), CX, CY - hd, wz0, wz1, blen, "S")
            n_win += 1
        # 东西短面: 两段, 避开中央红山墙板 (y 52-60); 段长 2.2, 中心 CY±5.3
        for side, sgn in (("E", 1), ("W", -1)):
            for k, off in enumerate((-5.3, 5.3)):
                window_band("canteen_win_F%d_%s%d" % (fi + 1, side, k),
                            CY + off, CX + sgn * hw, wz0, wz1, 2.2, side)
                n_win += 1
    print("window bands:", n_win)

    return building


def save_and_export(building):
    os.makedirs(PY_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print("saved blend:", BLEND_PATH, "objects:", len(building))
    bpy.ops.object.select_all(action="DESELECT")
    for o in building:
        o.select_set(True)
    bpy.context.view_layer.objects.active = building[0]
    bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format="GLB",
                               use_selection=True, export_apply=True)
    print("exported glb:", GLB_PATH, "objects:", len(building))
    # read back the .glb to confirm it opens
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.import_scene.gltf(filepath=GLB_PATH)
    imported = [o for o in bpy.context.selected_objects]
    print("glb re-import OK, imported objects:", len(imported))
    return imported


building = build()
imported = save_and_export(building)

# 清理 .blend1 备份
blend1 = BLEND_PATH + "1"
if os.path.exists(blend1):
    os.remove(blend1)

print("DONE ov-canteen")
