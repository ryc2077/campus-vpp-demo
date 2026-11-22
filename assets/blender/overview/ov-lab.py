# ov-lab v2: 实验楼楼体返工 (overview piece)
# 42(x) x 12(y) x 13(z) m, 3 floors, Blender centre (-28, 62, 0)
# 位置/尺寸/朝向照 v1, 不改楼的位置和占地; 屋顶板顶面 z=12.3,
# 女儿墙顶面 z=13.0 (与 pv-panels / pv-inverter 的屋顶 z=13 假设一致)。
#
# v2 返工内容 (对照鸟瞰图):
# - 墙面: 白色 #F6F2E9 (鸟瞰图里实验楼是白墙配红饰, 不是 v1 的蓝灰):
#   程序化涂料纹 (Noise 大斑驳 + 竖向雨水渍/墙根加重 + 细颗粒 Bump,
#   粗糙度随斑驳变化), 楼层分缝 (檐口线脚 + 线脚下暗色缝线)。
# - 红饰: 砖纹红 #A63A2C 竖向饰带 (南北长面每 6 m 一道 + 四角包角,
#   Brick + Noise 深浅 + Bump, 不是纯色条) + 顶层下红色横向饰带
#   + 门廊雨棚前缘红边。
# - 女儿墙: 厚 0.3 m, 顶面 = 屋顶板顶面 +0.65 m (12.95), 混凝土纹压顶至 13.0。
# - 屋顶: 深灰防水卷材纹 (Brick 搭接缝 + Noise 颗粒 + Bump), 不再是平板。
# - 窗带 (本件自带, SPEC §5/§6: ov-windows-roofs 只做 A/B/C):
#   每层横向窗带 + 竖分格条, 框出墙 0.18 / 玻璃内凹 0.11 / 窗台出墙 0.24;
#   玻璃淡蓝灰, 透明度 0.85 + 镜面 (Specular IOR Level 1.0, 粗糙度 0.12);
#   窗框/竖挺/窗台材质分开, 各有粗糙度/Bump 变化。
#   南面一层窗带在正门处断开 (±3.5 m 留门洞)。
# - 空调外机: 每层每长面 6 台 + 每短面 1 台 (共 42 台), 挂在窗带下方
#   (不挡窗), 小灰盒 + 波纹格栅面板 + 托架。
# - 正门: 双开玻璃门 + 门廊雨棚 + 双柱 + 三级台阶 (南面正中)。
# - 屋顶设备只放 PV 空隙处 (检修道/南缘), 顶面 ≤13.0, 不碰板阵列
#   (板最低边 ~13.15) 和北侧逆变器 (-28, 67.3) 及线槽。
# - 全部结构件带小倒角 (薄件除外); 没有任何一个面是全平的。
#
# 交付 (新规矩: 渲染全部走 GitHub Actions, 本地不渲染):
#   .py / .blend / .glb 三件; 脚本末尾打印 DONE ov-lab。
#   建模 -> 存盘 -> 导出 -> 回读校验, 一次 Blender 运行内完成。

import bpy
import math
import os

PIECE = "ov-lab"
BASE = os.path.expanduser("~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
PY_DIR = os.path.join(BASE, "assets/blender/overview")
BLEND_PATH = os.path.join(PY_DIR, "ov-lab.blend")
GLB_PATH = os.path.join(BASE, "assets/models/ov-lab.glb")

CX, CY = -28.0, 62.0   # building centre (Blender x, y)
W, D = 42.0, 12.0      # footprint x, y


def hex_rgb(h):
    """Hex sRGB -> linear RGB (Blender stores Base Color linear)."""
    h = h.lstrip("#")

    def srgb_to_lin(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (srgb_to_lin(int(h[i:i + 2], 16)) for i in (0, 2, 4))
    return (r, g, b, 1.0)


def _ramp(nt, name, stops):
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
    """白墙涂料: 大尺度斑驳 + 细颗粒 Bump + 竖向雨水渍 (墙根加重)."""
    m, bsdf = _new_mat("Wall_White_F6F2E9_tex", "#F6F2E9", 0.85)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n1 = _noise(nt, "Mottle", 0.35, detail=3, rough=0.7)
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    ramp1 = _ramp(nt, "MottleRamp", [(0.0, "#E7DFCB"), (0.5, "#F6F2E9"), (1.0, "#FBF7EC")])
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
    mix.inputs["Color2"].default_value = hex_rgb("#CFC3A8")  # 渍痕深米色
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


def red_brick_mat():
    """红饰带: 砖纹 (Brick) + Noise 深浅不均 + Bump, 砖红 #A63A2C."""
    m, bsdf = _new_mat("Trim_RedBrick_A63A2C_tex", "#A63A2C", 0.85)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    brick = nt.nodes.new("ShaderNodeTexBrick")
    brick.inputs["Scale"].default_value = 2.0
    brick.inputs["Mortar Size"].default_value = 0.02
    brick.inputs["Brick Width"].default_value = 0.5
    brick.inputs["Row Height"].default_value = 0.5
    brick.inputs["Color1"].default_value = hex_rgb("#A63A2C")
    brick.inputs["Color2"].default_value = hex_rgb("#8E2F24")
    brick.inputs["Mortar"].default_value = hex_rgb("#6E231B")
    nt.links.new(mp.outputs["Vector"], brick.inputs["Vector"])
    n1 = _noise(nt, "Mottle", 6.0, detail=3, rough=0.7)
    nt.links.new(mp.outputs["Vector"], n1.inputs["Vector"])
    ramp = _ramp(nt, "ShadeRamp", [(0.30, "#000000"), (0.70, "#737373")])
    ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
    ramp.color_ramp.elements[1].color = (0.45, 0.45, 0.45, 1)
    nt.links.new(n1.outputs["Fac"], ramp.inputs["Fac"])
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MIX"
    nt.links.new(brick.outputs["Color"], mix.inputs["Color1"])
    mix.inputs["Color2"].default_value = hex_rgb("#5E1F19")
    nt.links.new(ramp.outputs["Color"], mix.inputs["Fac"])
    nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    b = _bump(nt, n1.outputs["Fac"], strength=0.4, distance=0.08)
    nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def roof_mat():
    """深灰防水屋顶: Noise 颗粒 + Brick 卷材搭接缝 + Bump."""
    m, bsdf = _new_mat("Roof_DarkGrey_424A52_tex", "#424A52", 0.92)
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
    """混凝土: 斑驳 + 颗粒 Bump (勒脚/檐口/压顶/台阶)."""
    m, bsdf = _new_mat("Concrete_B9B3A8_tex", "#B9B3A8", 0.95)
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
    m, bsdf = _new_mat("Cornice_D8D2C4_tex", "#D8D2C4", 0.9)
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


def metal_mat(hexcol="#C0C5C9", name="MetalGrey_tex", rough=0.55, metallic=0.3):
    m, bsdf = _new_mat(name, hexcol, rough, metallic)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n1 = _noise(nt, "Grain", 3.5, detail=2, rough=0.8)
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    b = _bump(nt, n1.outputs["Fac"], strength=0.15, distance=0.02)
    nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def glass_mat():
    """窗玻璃: 淡蓝灰, 透明度 0.85 + 镜面 (Specular IOR Level 1.0)."""
    m, bsdf = _new_mat("Glass_A8C8DC", "#A8C8DC", 0.12, 0.0)
    bsdf.inputs["Alpha"].default_value = 0.85
    try:
        bsdf.inputs["Specular IOR Level"].default_value = 1.0
    except Exception:
        pass
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n1 = _noise(nt, "Sheen", 1.2, detail=2, rough=0.8)
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    # 极轻的明暗变化 (反光不均), 不做纯色板
    ramp = _ramp(nt, "GlassRamp", [(0.0, "#9DBED6"), (0.5, "#A8C8DC"), (1.0, "#B4D2E2")])
    nt.links.new(n1.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    return m


def frame_mat():
    """窗框: 浅灰白铝框, 粗糙度 0.45, 细颗粒 Bump."""
    m, bsdf = _new_mat("WinFrame_D8DDE0", "#D8DDE0", 0.45, 0.25)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n1 = _noise(nt, "Grain", 4.0, detail=2, rough=0.8)
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    b = _bump(nt, n1.outputs["Fac"], strength=0.2, distance=0.02)
    nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def mullion_mat():
    """竖挺: 中灰金属, 粗糙度 0.5, 金属感 0.5, 颗粒 Bump."""
    m, bsdf = _new_mat("WinMullion_7E8387", "#7E8387", 0.5, 0.5)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n1 = _noise(nt, "Grain", 5.0, detail=2, rough=0.8)
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    b = _bump(nt, n1.outputs["Fac"], strength=0.25, distance=0.02)
    nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def grille_mat():
    """空调格栅: 深灰 + 横向波纹条纹 (百叶感) + Bump."""
    m, bsdf = _new_mat("AC_Grille_3A4046_tex", "#3A4046", 0.7, 0.1)
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


MAT_WALL = wall_mat()
MAT_RED = red_brick_mat()
MAT_ROOF = roof_mat()
MAT_CONC = conc_mat()
MAT_BAND = band_mat()
MAT_METAL = metal_mat()
MAT_AC_BODY = metal_mat("#D5D9DC", "AC_Body_D5D9DC", 0.5, 0.25)
MAT_GRILLE = grille_mat()
MAT_GLASS = glass_mat()
MAT_FRAME = frame_mat()
MAT_MULLION = mullion_mat()
MAT_SEAM = _new_mat("FloorSeam_B7A988", "#B7A988", 0.9)[0]
MAT_DOOR = metal_mat("#3A4046", "DoorFrame_3A4046", 0.5, 0.4)


def build():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    building = []

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

    def cyl(name, cx, cy, z0, z1, r, mat, bevel=0.0):
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=z1 - z0,
                                            location=(cx, cy, (z0 + z1) / 2.0))
        o = bpy.context.active_object
        o.name = name
        o.data.materials.append(mat)
        building.append(o)
        return o

    # ---- 勒脚 (0-0.5) + 压顶 (0.5-0.68) ----
    box("lab_plinth", CX, CY, 0.0, 0.5, W + 0.4, D + 0.4, MAT_CONC, bevel=0.04)
    box("lab_plinth_cap", CX, CY, 0.5, 0.68, W + 0.7, D + 0.7, MAT_BAND, bevel=0.03)

    # ---- 楼体分层 (收分 0.1/边) ----
    # F1 0.5-4.0 (42x12), F2 4.0-8.0 (41.8x11.8), F3 8.0-12.0 (41.6x11.6)
    box("lab_floor1", CX, CY, 0.5, 4.0, 42.0, 12.0, MAT_WALL, bevel=0.06)
    box("lab_floor2", CX, CY, 4.0, 8.0, 41.8, 11.8, MAT_WALL, bevel=0.05)
    box("lab_floor3", CX, CY, 8.0, 12.0, 41.6, 11.6, MAT_WALL, bevel=0.05)

    # ---- 檐口线脚 + 楼层分缝 (线脚下暗色缝线) ----
    for i, zc in enumerate((4.0, 8.0)):
        box("lab_cornice_F%d" % (i + 2), CX, CY, zc - 0.14, zc + 0.14,
            42.3, 12.3, MAT_BAND, bevel=0.03)
        box("lab_seam_F%d" % (i + 2), CX, CY, zc - 0.24, zc - 0.18,
            42.06, 12.06, MAT_SEAM, bevel=0.0)
    # 顶层檐口 (12.0, 混凝土色)
    box("lab_cornice_top", CX, CY, 11.91, 12.09, 42.3, 12.3, MAT_CONC, bevel=0.03)

    # ---- 红色横向饰带 (顶层下, 南北长面, 11.55-11.95) ----
    for sgn, tag in ((1, "N"), (-1, "S")):
        box("lab_frieze_%s" % tag, CX, CY + sgn * 6.04, 11.55, 11.95,
            41.4, 0.08, MAT_RED, bevel=0.02)

    # ---- 红色竖向饰带 (0.5-12.0, 出墙 0.12) ----
    # 南北长面: 间距 6 m; 南面正中留正门, 跳过 0 号位
    for off in (-18.0, -12.0, -6.0, 0.0, 6.0, 12.0, 18.0):
        box("lab_pilaster_N_%+d" % off, CX + off, CY + 6.06, 0.5, 12.0,
            0.6, 0.12, MAT_RED, bevel=0.02)
    for off in (-18.0, -12.0, -6.0, 6.0, 12.0, 18.0):
        box("lab_pilaster_S_%+d" % off, CX + off, CY - 6.06, 0.5, 12.0,
            0.6, 0.12, MAT_RED, bevel=0.02)
    # 四角: 长面端头 + 短面包角
    for sx in (-1, 1):
        box("lab_pilaster_corner_N_%s" % ("E" if sx > 0 else "W"),
            CX + sx * 20.4, CY + 6.06, 0.5, 12.0, 0.6, 0.12, MAT_RED, bevel=0.02)
        box("lab_pilaster_corner_S_%s" % ("E" if sx > 0 else "W"),
            CX + sx * 20.4, CY - 6.06, 0.5, 12.0, 0.6, 0.12, MAT_RED, bevel=0.02)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box("lab_pilaster_wrap_%s%s" % ("E" if sx > 0 else "W", "N" if sy > 0 else "S"),
                CX + sx * 21.06, CY + sy * 5.4, 0.5, 12.0, 0.12, 0.6, MAT_RED, bevel=0.02)

    # ---- 屋顶板 (12.0-12.3, 防水卷材纹) ----
    box("lab_roofslab", CX, CY, 12.0, 12.3, 42.0, 12.0, MAT_ROOF, bevel=0.03)

    # ---- 女儿墙 (12.3-12.95, 厚 0.3) + 压顶 (12.95-13.0, 宽 0.42) ----
    box("lab_parapet_N", CX, CY + 5.85, 12.3, 12.95, 42.0, 0.3, MAT_CONC, bevel=0.02)
    box("lab_parapet_S", CX, CY - 5.85, 12.3, 12.95, 42.0, 0.3, MAT_CONC, bevel=0.02)
    box("lab_parapet_E", CX + 20.85, CY, 12.3, 12.95, 0.3, 11.4, MAT_CONC, bevel=0.02)
    box("lab_parapet_W", CX - 20.85, CY, 12.3, 12.95, 0.3, 11.4, MAT_CONC, bevel=0.02)
    box("lab_coping_N", CX, CY + 5.85, 12.95, 13.0, 42.12, 0.42, MAT_CONC, bevel=0.02)
    box("lab_coping_S", CX, CY - 5.85, 12.95, 13.0, 42.12, 0.42, MAT_CONC, bevel=0.02)
    box("lab_coping_E", CX + 20.85, CY, 12.95, 13.0, 0.42, 11.52, MAT_CONC, bevel=0.02)
    box("lab_coping_W", CX - 20.85, CY, 12.95, 13.0, 0.42, 11.52, MAT_CONC, bevel=0.02)

    # ---- 屋顶设备 (只放 PV 空隙处, 顶面 <=13.0) ----
    # 通风筒: 检修道空隙 (y 62.4-63.4), 顶 12.9
    cyl("lab_roof_vent", -46.0, 62.9, 12.3, 12.9, 0.25, MAT_METAL)
    cyl("lab_roof_vent_cap", -46.0, 62.9, 12.9, 12.98, 0.30, MAT_ROOF)
    # 低设备盒: 南缘空隙 (y 56.4-57.0), 顶 12.95
    box("lab_roof_eq1", -12.0, 56.7, 12.3, 12.95, 1.6, 0.6, MAT_METAL, bevel=0.03)
    box("lab_roof_eq1_lid", -12.0, 56.7, 12.95, 13.0, 1.7, 0.7, MAT_ROOF, bevel=0.02)

    # ---- 窗带 (本件自带): 每层每面, 框出墙 0.18 / 玻璃内凹 / 窗台出墙 ----
    # (层, 中心 z, 带高, 长面带长, 短面带长, 长面半宽, 短面半宽)
    FLOORS = [
        (1, 2.2, 1.6, 38.0, 8.0, 21.0, 6.0),
        (2, 6.0, 1.8, 37.8, 7.8, 20.9, 5.9),
        (3, 10.0, 1.8, 37.6, 7.6, 20.8, 5.8),
    ]

    def window_band(fi, zc, h, face, half, band_len, segments):
        """segments: [(中心偏移, 长度)] 沿面方向; face: N/S/E/W.
        框: 上下框 + 左右侧框 + 竖挺(每 3m) + 横中挺; 玻璃内凹; 窗台出墙。"""
        z0, z1 = zc - h / 2, zc + h / 2
        for si, (off, blen) in enumerate(segments):
            tag = "%s_%d" % (face, si) if len(segments) > 1 else face
            if face in ("N", "S"):
                sgn = 1 if face == "N" else -1
                yf = CY + sgn * half  # 墙面
                cx = CX + off
                # 玻璃: 前表面墙 +0.07 (框前沿 +0.18, 内凹 0.11)
                box("lab_win_glass_F%d_%s" % (fi, tag), cx, yf + sgn * 0.05,
                    z0, z1, blen, 0.04, MAT_GLASS, bevel=0.0)
                # 上下框
                box("lab_win_frameT_F%d_%s" % (fi, tag), cx, yf + sgn * 0.09,
                    z1, z1 + 0.12, blen + 0.12, 0.18, MAT_FRAME, bevel=0.0)
                box("lab_win_frameB_F%d_%s" % (fi, tag), cx, yf + sgn * 0.09,
                    z0 - 0.12, z0, blen + 0.12, 0.18, MAT_FRAME, bevel=0.0)
                # 左右侧框
                for end in (-1, 1):
                    box("lab_win_frameE_F%d_%s_%d" % (fi, tag, end),
                        cx + end * (blen / 2 + 0.06), yf + sgn * 0.09,
                        z0, z1, 0.12, 0.18, MAT_FRAME, bevel=0.0)
                # 竖挺: 每 3 m 一根
                u = -blen / 2 + 3.0
                k = 0
                while u < blen / 2 - 0.01:
                    box("lab_win_mull_F%d_%s_%d" % (fi, tag, k),
                        cx + u, yf + sgn * 0.10, z0, z1, 0.07, 0.10, MAT_MULLION, bevel=0.0)
                    u += 3.0
                    k += 1
                # 横中挺
                box("lab_win_rail_F%d_%s" % (fi, tag), cx, yf + sgn * 0.10,
                    zc - 0.035, zc + 0.035, blen, 0.10, MAT_MULLION, bevel=0.0)
                # 窗台板: 出墙 0.24
                box("lab_win_sill_F%d_%s" % (fi, tag), cx, yf + sgn * 0.11,
                    z0 - 0.24, z0 - 0.16, blen + 0.24, 0.26, MAT_CONC, bevel=0.02)
            else:
                sgn = 1 if face == "E" else -1
                xf = CX + sgn * half
                cy_ = CY + off
                box("lab_win_glass_F%d_%s" % (fi, tag), xf + sgn * 0.05, cy_,
                    z0, z1, 0.04, blen, MAT_GLASS, bevel=0.0)
                box("lab_win_frameT_F%d_%s" % (fi, tag), xf + sgn * 0.09, cy_,
                    z1, z1 + 0.12, 0.18, blen + 0.12, MAT_FRAME, bevel=0.0)
                box("lab_win_frameB_F%d_%s" % (fi, tag), xf + sgn * 0.09, cy_,
                    z0 - 0.12, z0, 0.18, blen + 0.12, MAT_FRAME, bevel=0.0)
                for end in (-1, 1):
                    box("lab_win_frameE_F%d_%s_%d" % (fi, tag, end),
                        xf + sgn * 0.09, cy_ + end * (blen / 2 + 0.06),
                        z0, z1, 0.18, 0.12, MAT_FRAME, bevel=0.0)
                u = -blen / 2 + 3.0
                k = 0
                while u < blen / 2 - 0.01:
                    box("lab_win_mull_F%d_%s_%d" % (fi, tag, k),
                        xf + sgn * 0.10, cy_ + u, z0, z1, 0.10, 0.07, MAT_MULLION, bevel=0.0)
                    u += 3.0
                    k += 1
                box("lab_win_rail_F%d_%s" % (fi, tag), xf + sgn * 0.10, cy_,
                    zc - 0.035, zc + 0.035, 0.10, blen, MAT_MULLION, bevel=0.0)
                box("lab_win_sill_F%d_%s" % (fi, tag), xf + sgn * 0.11, cy_,
                    z0 - 0.24, z0 - 0.16, 0.26, blen + 0.24, MAT_CONC, bevel=0.02)

    for fi, zc, h, blong, bshort, hw, hd in FLOORS:
        # 南面一层在正门处断开: 两段各 15.5, 中心 ±11.25
        seg_s = [(-11.25, 15.5), (11.25, 15.5)] if fi == 1 else [(0.0, blong)]
        window_band(fi, zc, h, "S", hd, blong, seg_s)
        window_band(fi, zc, h, "N", hd, blong, [(0.0, blong)])
        window_band(fi, zc, h, "E", hw, bshort, [(0.0, bshort)])
        window_band(fi, zc, h, "W", hw, bshort, [(0.0, bshort)])

    # ---- 空调外机 (窗带下方, 每层每长面 6 台 + 每短面 1 台, 共 42 台) ----
    def ac_unit(prefix, ux, uy, zc, facing):
        if facing in ("S", "N"):
            sgn = -1 if facing == "S" else 1
            box(prefix, ux, uy, zc - 0.25, zc + 0.25, 0.9, 0.28, MAT_AC_BODY, bevel=0.02)
            box(prefix + "_grille", ux, uy + sgn * 0.15, zc - 0.20, zc + 0.20,
                0.78, 0.03, MAT_GRILLE, bevel=0.0)
            box(prefix + "_bracket", ux, uy, zc - 0.34, zc - 0.28, 0.9, 0.10,
                MAT_METAL, bevel=0.0)
        else:
            sgn = 1 if facing == "E" else -1
            box(prefix, ux, uy, zc - 0.25, zc + 0.25, 0.28, 0.9, MAT_AC_BODY, bevel=0.02)
            box(prefix + "_grille", ux + sgn * 0.15, uy, zc - 0.20, zc + 0.20,
                0.03, 0.78, MAT_GRILLE, bevel=0.0)
            box(prefix + "_bracket", ux, uy, zc - 0.34, zc - 0.28, 0.10, 0.9,
                MAT_METAL, bevel=0.0)

    n_ac = 0
    for fi, (z0, z1, hw, hd) in enumerate(
            [(0.5, 4.0, 21.0, 6.0), (4.0, 8.0, 20.9, 5.9), (8.0, 12.0, 20.8, 5.8)], start=1):
        zc = (0.95, 4.55, 8.55)[fi - 1]  # 窗带下方 (一层窗带底 1.4, 窗台底 ~1.16)
        for j, off in enumerate((-15.0, -9.0, -3.0, 3.0, 9.0, 15.0)):
            ac_unit("lab_ac_F%d_S%d" % (fi, j), CX + off, CY - hd - 0.14, zc, "S")
            ac_unit("lab_ac_F%d_N%d" % (fi, j), CX + off, CY + hd + 0.14, zc, "N")
            n_ac += 2
        ac_unit("lab_ac_F%d_E0" % fi, CX + hw + 0.14, CY, zc, "E")
        ac_unit("lab_ac_F%d_W0" % fi, CX - hw - 0.14, CY, zc, "W")
        n_ac += 2
    print("AC outdoor units:", n_ac)

    # ---- 正门 (南面正中) + 门廊雨棚 + 双柱 + 三级台阶 ----
    # 双开玻璃门: 框 2.7x3.1, 两扇玻璃门, 横梁, 把手
    box("lab_door_frame", CX, CY - 6.05, 0.5, 3.6, 2.7, 0.15, MAT_DOOR, bevel=0.02)
    box("lab_door_leaf_L", CX - 0.62, CY - 6.10, 0.55, 3.45, 1.15, 0.06, MAT_GLASS, bevel=0.0)
    box("lab_door_leaf_R", CX + 0.62, CY - 6.10, 0.55, 3.45, 1.15, 0.06, MAT_GLASS, bevel=0.0)
    box("lab_door_transom", CX, CY - 6.10, 3.0, 3.12, 2.4, 0.08, MAT_DOOR, bevel=0.0)
    box("lab_door_handle_L", CX - 0.12, CY - 6.16, 1.35, 1.75, 0.05, 0.05, MAT_METAL, bevel=0.0)
    box("lab_door_handle_R", CX + 0.12, CY - 6.16, 1.35, 1.75, 0.05, 0.05, MAT_METAL, bevel=0.0)
    # 雨棚 6.0x2.0 (z 3.4-3.65) + 前缘红边 + 双柱
    box("lab_entry_canopy", CX, CY - 7.0, 3.4, 3.65, 6.0, 2.0, MAT_CONC, bevel=0.03)
    box("lab_entry_fascia", CX, CY - 7.97, 3.45, 3.59, 6.0, 0.06, MAT_RED, bevel=0.0)
    box("lab_entry_col_L", CX - 2.6, CY - 6.9, 0.5, 3.4, 0.3, 0.3, MAT_CONC, bevel=0.03)
    box("lab_entry_col_R", CX + 2.6, CY - 6.9, 0.5, 3.4, 0.3, 0.3, MAT_CONC, bevel=0.03)
    # 三级台阶 (每级高 0.17, 逐级收进)
    box("lab_steps_1", CX, CY - 7.3, 0.0, 0.17, 6.6, 2.6, MAT_CONC, bevel=0.02)
    box("lab_steps_2", CX, CY - 6.9, 0.17, 0.34, 6.6, 1.8, MAT_CONC, bevel=0.02)
    box("lab_steps_3", CX, CY - 6.5, 0.34, 0.5, 6.6, 1.0, MAT_CONC, bevel=0.02)

    return building


building = build()

# ---------- 烘焙程序化纹理为图片 (glTF 无法导出 Noise/Brick/Voronoi) ----------
# 照抄 di-walls 已验证做法: 每种不透明材质选其全部对象 -> Cycles CPU
# samples 4 -> 烘焙 color/rough/normal 三张 1024px 图 (margin 16px) ->
# 重建材质为图片纹理。玻璃材质 (Glass_A8C8DC) 不烘焙, 保持原样。
# 烘焙图在 ov-lab_textures/。
# ---------- UV 展开 (烘焙前) ----------
# 立方体默认 UV 每面都占满 0~1: 同材质多对象烘焙时, 每对象 6 个面在同一张
# 图上反复覆盖, 烘焙量随对象数膨胀 (实测 ov-gym: 1 对象屋顶约 1 分钟/张,
# 29 对象混凝土约 10 分钟/张, 122 对象金属 20 分钟仍未出图)。
# 先对本件全部对象做 Smart UV Project (各面不重叠), 烘焙量回到约 1 张图;
# 只改 UV, 不改几何/配色/位置。烘焙参数本身 (Cycles CPU/4 采样/
# margin 16px/1024px/color+rough+normal) 与 di-walls 完全一致。
for _ob in building:
    if _ob.type != 'MESH':
        continue
    try:
        if not _ob.data.uv_layers:
            _ob.data.uv_layers.new()
        bpy.ops.object.select_all(action='DESELECT')
        _ob.select_set(True)
        bpy.context.view_layer.objects.active = _ob
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.001)
        bpy.ops.object.mode_set(mode='OBJECT')
    except Exception as _e:
        print("smart uv skipped:", _ob.name, _e)
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except Exception:
            pass
bpy.ops.object.select_all(action='DESELECT')
print("smart uv done")

TEX_DIR = os.path.join(PY_DIR, "ov-lab_textures")
os.makedirs(TEX_DIR, exist_ok=True)
_bake_scene = bpy.context.scene

def _bake_images(mat, mat_objs):
    nt = mat.node_tree
    imgs = {}
    specs = [("color", 'DIFFUSE', 1024, 'sRGB'),
             ("rough", 'ROUGHNESS', 1024, 'Non-Color'),
             ("normal", 'NORMAL', 1024, 'Non-Color')]
    bpy.ops.object.select_all(action='DESELECT')
    for ob in mat_objs:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = mat_objs[0]
    _bake_scene.render.engine = 'CYCLES'
    _bake_scene.cycles.device = 'CPU'
    _bake_scene.cycles.samples = 4
    bake = _bake_scene.render.bake
    bake.use_selected_to_active = False
    bake.margin = 16
    for key, btype, size, cs in specs:
        # 断点续烘: 图已存在且能正常读入就复用 (虚拟机重启/中断后重跑不用重烘);
        # 读入失败或文件为空则重新烘焙。
        _fpath = os.path.join(TEX_DIR, "%s_%s.png" % (mat.name, key))
        if os.path.exists(_fpath) and os.path.getsize(_fpath) > 1000:
            try:
                _img = bpy.data.images.load(_fpath)
                _img.colorspace_settings.name = cs
                imgs[key] = _img
                print("reuse:", mat.name, key, _fpath,
                      os.path.getsize(_fpath))
                continue
            except Exception as _e:
                print("reload failed, re-bake:", mat.name, key, _e)
        img = bpy.data.images.new("%s_%s" % (mat.name, key),
                                  width=size, height=size, alpha=False)
        img.colorspace_settings.name = cs
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = img
        nt.nodes.active = tex
        if btype == 'DIFFUSE':
            bake.use_pass_direct = False
            bake.use_pass_indirect = False
            bake.use_pass_color = True
        elif btype == 'NORMAL':
            bake.normal_space = 'TANGENT'
        bpy.ops.object.bake(type=btype)
        img.filepath_raw = os.path.join(TEX_DIR, "%s_%s.png" % (mat.name, key))
        img.file_format = 'PNG'
        img.save()
        imgs[key] = img
        nt.nodes.remove(tex)
        print("baked:", mat.name, key, img.filepath_raw,
              os.path.getsize(img.filepath_raw))
    _bake_scene.render.engine = 'BLENDER_EEVEE_NEXT'
    return imgs

def _rebuild_with_images(mat, imgs):
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    bsdf.inputs["Roughness"].default_value = 1.0
    bsdf.inputs["Metallic"].default_value = 0.0
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    tex_c = nt.nodes.new("ShaderNodeTexImage")
    tex_c.image = imgs["color"]
    nt.links.new(tex_c.outputs["Color"], bsdf.inputs["Base Color"])
    tex_r = nt.nodes.new("ShaderNodeTexImage")
    tex_r.image = imgs["rough"]
    nt.links.new(tex_r.outputs["Color"], bsdf.inputs["Roughness"])
    tex_n = nt.nodes.new("ShaderNodeTexImage")
    tex_n.image = imgs["normal"]
    nmap = nt.nodes.new("ShaderNodeNormalMap")
    nmap.space = 'TANGENT'
    nt.links.new(tex_n.outputs["Color"], nmap.inputs["Color"])
    nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])

_by_mat = {}
for _ob in building:
    if _ob.data and _ob.data.materials:
        _by_mat.setdefault(_ob.data.materials[0], []).append(_ob)
_baked = {}
for _mat, _m_objs in _by_mat.items():
    if "glass" in _mat.name.lower():
        print("skip bake (glass):", _mat.name)
        continue
    _baked[_mat.name] = _bake_images(_mat, _m_objs)
for _mat in _by_mat:
    if _mat.name in _baked:
        _rebuild_with_images(_mat, _baked[_mat.name])
print("bake done, materials rebuilt with image textures")

# ---------- 存 .blend (落盘优先) ----------
os.makedirs(PY_DIR, exist_ok=True)
os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("saved blend:", BLEND_PATH, "objects:", len(building))

# ---------- 导出 .glb (只选本件对象) ----------
bpy.ops.object.select_all(action="DESELECT")
for o in building:
    o.select_set(True)
bpy.context.view_layer.objects.active = building[0]
bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format="GLB",
                           use_selection=True, export_apply=True)
print("exported glb:", GLB_PATH, "objects:", len(building))

# ---------- 回读校验 ----------
bpy.ops.object.select_all(action="DESELECT")
bpy.ops.import_scene.gltf(filepath=GLB_PATH)
imported = [o for o in bpy.context.selected_objects]
print("GLB reimport objects:", len(imported))
for ob in imported:
    for slot in ob.material_slots:
        m = slot.material
        if m and m.use_nodes:
            imgs = [n.image.name for n in m.node_tree.nodes
                    if n.type == 'TEX_IMAGE' and n.image is not None]
            print("GLB reimport mat:", ob.name, m.name, "images:", imgs)
            if "glass" in m.name.lower():
                print("  (glass, unbaked by design)")
                continue
            assert len(imgs) >= 3, "glb material lost baked textures: %s" % m.name
assert len(imported) == len(building), "glb reimport failed: expected %d objects, got %d" % (len(building), len(imported))

# 清理 .blend1 备份
blend1 = BLEND_PATH + "1"
if os.path.exists(blend1):
    os.remove(blend1)

print("DONE ov-lab")
