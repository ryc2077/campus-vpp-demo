# ov-lib v2: 图书馆楼体返工 (overview piece)
# 24(x) x 16(y) x 22(z) m, 6 floors, Blender centre (24, -58, 0)
# 位置/尺寸/朝向照旧版，不改楼的位置和占地。
# v2 返工内容 (对照鸟瞰图筛查结论):
# - 红褐色饰带 (本件最关键缺失): 顶层横向饰带 (20.1-21.0) + 中部横向
#   饰带 (10.9-11.55) + 首层顶横向饰带 (3.35-4.0)，三道全周圈出挑；
#   南北正立面另加两道竖向红褐色壁柱条 (x=CX±6.5, 0.5-20.1)。
#   饰带带 Brick 砖缝 + Noise 斑驳 + Bump，不是纯色条。
# - 墙面: 程序化涂料纹 (Noise 斑驳 + 竖向雨水渍 + 细颗粒 Bump +
#   粗糙度变化)，楼层分缝 (檐口线脚 + 线脚下暗色缝线)；墙色浅橙
#   #F6D9C0，sRGB->线性赋值。
# - 女儿墙: 顶面 = 屋顶板顶面 +0.65 m (21.95)，厚 0.3 m，压顶略出挑。
# - 屋顶: 深灰防水卷材 (Brick 搭接缝 + Noise 颗粒 + Bump)，不再是平板。
# - 空调外机: 沿外墙分层挂 (长边每层 3 台 + 短边每层 1 台)：小灰盒 +
#   波纹格栅面板 + 托架 (首层南面正中一台让位给门廊，跳过)。
# - 正门 + 门廊雨棚 + 三级台阶 (南面正中)。
# - 分件边界: 不加窗 (窗归 ov-windows-roofs)；v1 的玻璃窗带已移除。
# - 全部结构件带小倒角 (薄件除外)。
#
# Height note: campus.json 高度为示意；层高照实测 (1F 3.5 m, 2-6F 3.4 m)：
# plinth 0-0.5, F1 0.5-4.0, F2-F6 4.0-21.0 (每层 3.4)，屋顶板 21.0-21.3，
# 女儿墙 21.3-21.95 (顶面 21.95 ≈ 22 m 包络)。
#
# 新规矩: 渲染全部走 GitHub Actions，本地不渲染。本脚本只做
# 建模 -> 存 .blend -> 导出 .glb -> 回读校验，打印 DONE ov-lib。

import bpy
import math
import os
import sys
from mathutils import Vector

PIECE = "ov-lib"
BASE = os.path.expanduser("~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
PY_DIR = os.path.join(BASE, "assets/blender/overview")
BLEND_PATH = os.path.join(PY_DIR, "ov-lib.blend")
GLB_PATH = os.path.join(BASE, "assets/models/ov-lib.glb")

CX, CY = 24.0, -58.0   # building centre (Blender x, y)
W, D = 24.0, 16.0      # footprint x, y


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
    """浅橙涂料墙: 大尺度斑驳 + 细颗粒 Bump + 竖向雨水渍 (墙根加重)."""
    m, bsdf = _new_mat("Lib_Wall_Orange_F6D9C0_tex", "#F6D9C0", 0.85)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n1 = _noise(nt, "Mottle", 0.35, detail=3, rough=0.7)
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    ramp1 = _ramp(nt, "MottleRamp", [(0.0, "#E8C9A8"), (0.5, "#F6D9C0"), (1.0, "#FBEEDC")])
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
    mix.inputs["Color2"].default_value = hex_rgb("#D9B98C")  # 渍痕深橙米色
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


def band_mat():
    """红褐色饰带: Brick 砖缝 + Noise 斑驳 + Bump，绝非纯色条。"""
    m, bsdf = _new_mat("Lib_Band_RedBrown_8A3324_tex", "#8A3324", 0.88)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    brick = nt.nodes.new("ShaderNodeTexBrick")
    brick.inputs["Scale"].default_value = 0.7
    brick.inputs["Mortar Size"].default_value = 0.015
    brick.inputs["Brick Width"].default_value = 0.55
    brick.inputs["Row Height"].default_value = 0.22
    brick.inputs["Color1"].default_value = hex_rgb("#8A3324")
    brick.inputs["Color2"].default_value = hex_rgb("#9A3B2A")
    brick.inputs["Mortar"].default_value = hex_rgb("#5E2118")
    nt.links.new(tc.outputs["Object"], brick.inputs["Vector"])
    n1 = _noise(nt, "Mottle", 0.9, detail=3, rough=0.7)
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    ramp1 = _ramp(nt, "MottleRamp", [(0.0, "#6E2718"), (0.5, "#8A3324"), (1.0, "#A34430")])
    nt.links.new(n1.outputs["Fac"], ramp1.inputs["Fac"])
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MIX"
    mix.inputs["Fac"].default_value = 0.45
    nt.links.new(brick.outputs["Color"], mix.inputs["Color1"])
    nt.links.new(ramp1.outputs["Color"], mix.inputs["Color2"])
    nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    b = _bump(nt, brick.outputs["Fac"], strength=0.5, distance=0.05)
    nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.3
    mr.inputs["From Max"].default_value = 0.7
    mr.inputs["To Min"].default_value = 0.78
    mr.inputs["To Max"].default_value = 0.95
    nt.links.new(n1.outputs["Fac"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])
    return m


def roof_mat():
    """深灰防水屋顶: Noise 颗粒 + Brick 卷材搭接缝 + Bump。"""
    m, bsdf = _new_mat("Lib_Roof_DarkGrey_424A52_tex", "#424A52", 0.92)
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
    """混凝土: 斑驳 + 颗粒 Bump (女儿墙/勒脚/压顶/台阶)。"""
    m, bsdf = _new_mat("Lib_Concrete_B9B3A8_tex", "#B9B3A8", 0.95)
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


def cornice_mat():
    """檐口/线脚: 浅色铺装色，轻微斑驳 + Bump。"""
    m, bsdf = _new_mat("Lib_Cornice_D8D2C4_tex", "#D8D2C4", 0.9)
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


def metal_mat(hexcol="#C0C5C9", name="Lib_MetalGrey_tex", rough=0.55, metallic=0.3):
    m, bsdf = _new_mat(name, hexcol, rough, metallic)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n1 = _noise(nt, "Grain", 3.5, detail=2, rough=0.8)
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    b = _bump(nt, n1.outputs["Fac"], strength=0.15, distance=0.02)
    nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def grille_mat():
    """空调格栅: 深灰 + 横向波纹条纹 (百叶感) + Bump。"""
    m, bsdf = _new_mat("Lib_AC_Grille_3A4046_tex", "#3A4046", 0.7, 0.1)
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
MAT_BAND = band_mat()
MAT_ROOF = roof_mat()
MAT_CONC = conc_mat()
MAT_CORNICE = cornice_mat()
MAT_METAL = metal_mat()
MAT_AC_BODY = metal_mat("#D5D9DC", "Lib_AC_Body_D5D9DC", 0.5, 0.25)
MAT_GRILLE = grille_mat()
MAT_SEAM = _new_mat("Lib_FloorSeam_B7A988", "#B7A988", 0.9)[0]
MAT_DOOR = _new_mat("Lib_Door_Wood_8A6B4A", "#8A6B4A", 0.7)[0]
MAT_DOOR_GLASS = _new_mat("Lib_Door_Glass_9FC3D8", "#9FC3D8", 0.25, 0.1)[0]


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

    def cyl(name, cx, cy, z0, z1, r, mat):
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=z1 - z0,
                                            location=(cx, cy, (z0 + z1) / 2.0))
        o = bpy.context.active_object
        o.name = name
        o.data.materials.append(mat)
        building.append(o)
        return o

    # ---- 勒脚 (0-0.5) + 勒脚压顶 ----
    box("lib_plinth", CX, CY, 0.0, 0.5, W + 0.6, D + 0.6, MAT_CONC, bevel=0.04)
    box("lib_plinth_cap", CX, CY, 0.5, 0.68, W + 0.7, D + 0.7, MAT_CORNICE, bevel=0.03)

    # ---- 楼体: F1 (0.5-4.0, 24x16) + F2-F6 (4.0-21.0, 收分 23.6x15.6) ----
    box("lib_body_F1", CX, CY, 0.5, 4.0, W, D, MAT_WALL, bevel=0.06)
    box("lib_body_F2_F6", CX, CY, 4.0, 21.0, W - 0.4, D - 0.4, MAT_WALL, bevel=0.06)

    # ---- 楼层分缝: 檐口线脚 + 线脚下暗色缝线 ----
    # 10.8 处由中部红褐色饰带承担分缝，不再另做檐口
    for i, zc in enumerate((4.0, 7.4, 14.2, 17.6)):
        box("lib_cornice_z%.1f" % zc, CX, CY, zc - 0.14, zc + 0.14,
            W + 0.3, D + 0.3, MAT_CORNICE, bevel=0.03)
        box("lib_seam_z%.1f" % zc, CX, CY, zc - 0.24, zc - 0.18,
            W + 0.06, D + 0.06, MAT_SEAM, bevel=0.0)

    # ---- 红褐色横向饰带 (三道，全周圈出挑，Brick 砖缝纹理) ----
    # 首层顶饰带 3.35-4.0: F1 面 24x16，出挑 0.15
    box("lib_band_F1_top", CX, CY, 3.35, 4.0, W + 0.3, D + 0.3, MAT_BAND, bevel=0.03)
    # 中部饰带 10.9-11.55: 上层体 23.6x15.6，出挑 0.15
    box("lib_band_mid", CX, CY, 10.9, 11.55, W - 0.4 + 0.3, D - 0.4 + 0.3, MAT_BAND, bevel=0.03)
    # 顶层饰带 20.1-21.0: 上层体 23.6x15.6，出挑 0.2
    box("lib_band_top", CX, CY, 20.1, 21.0, W - 0.4 + 0.4, D - 0.4 + 0.4, MAT_BAND, bevel=0.03)

    # ---- 竖向红褐色壁柱条 (南北立面，x=CX±6.5，0.5-20.1，出挑 0.08) ----
    for sgn, tag in ((-1, "W"), (1, "E")):
        x = CX + sgn * 6.5
        box("lib_pilaster_S_%s" % tag, x, CY - 8.0 - 0.04, 0.5, 20.1,
            0.5, 0.08, MAT_BAND, bevel=0.0)
        box("lib_pilaster_N_%s" % tag, x, CY + 7.8 + 0.04, 0.5, 20.1,
            0.5, 0.08, MAT_BAND, bevel=0.0)

    # ---- 屋顶板 (21.0-21.3，深灰防水卷材纹理) ----
    box("lib_roofslab", CX, CY, 21.0, 21.3, 24.2, 16.2, MAT_ROOF, bevel=0.03)

    # ---- 女儿墙: 顶面 21.95 = 屋顶板顶面 21.3 + 0.65，厚 0.3 m ----
    PW, PD, T = 24.2, 16.2, 0.30
    box("lib_parapet_S", CX, CY - (PD / 2 - T / 2), 21.3, 21.88, PW, T, MAT_CONC, bevel=0.02)
    box("lib_parapet_N", CX, CY + (PD / 2 - T / 2), 21.3, 21.88, PW, T, MAT_CONC, bevel=0.02)
    box("lib_parapet_W", CX - (PW / 2 - T / 2), CY, 21.3, 21.88, T, PD - 2 * T, MAT_CONC, bevel=0.02)
    box("lib_parapet_E", CX + (PW / 2 - T / 2), CY, 21.3, 21.88, T, PD - 2 * T, MAT_CONC, bevel=0.02)
    # 压顶 21.88-21.95，出挑 0.06/边
    box("lib_coping_S", CX, CY - (PD / 2 - T / 2), 21.88, 21.95, PW, T + 0.12, MAT_CONC, bevel=0.02)
    box("lib_coping_N", CX, CY + (PD / 2 - T / 2), 21.88, 21.95, PW, T + 0.12, MAT_CONC, bevel=0.02)
    box("lib_coping_W", CX - (PW / 2 - T / 2), CY, 21.88, 21.95, T + 0.12, PD - 2 * T, MAT_CONC, bevel=0.02)
    box("lib_coping_E", CX + (PW / 2 - T / 2), CY, 21.88, 21.95, T + 0.12, PD - 2 * T, MAT_CONC, bevel=0.02)

    # ---- 屋顶设备盒 (高出女儿墙约 0.8 m，带百叶格栅) + 通风筒 ----
    def roof_equip(prefix, ex, ey, bw, bd, ztop, louvre_side):
        box(prefix, ex, ey, 21.3, ztop, bw, bd, MAT_METAL, bevel=0.04)
        box(prefix + "_lid", ex, ey, ztop, ztop + 0.12, bw + 0.2, bd + 0.2,
            MAT_ROOF, bevel=0.02)
        for k, zl in enumerate((ztop - 0.95, ztop - 0.6, ztop - 0.25)):
            if louvre_side == "S":
                box("%s_louvre_%d" % (prefix, k), ex, ey - bd / 2 - 0.02,
                    zl - 0.06, zl + 0.06, bw - 0.5, 0.05, MAT_GRILLE, bevel=0.0)
            else:
                box("%s_louvre_%d" % (prefix, k), ex, ey + bd / 2 + 0.02,
                    zl - 0.06, zl + 0.06, bw - 0.5, 0.05, MAT_GRILLE, bevel=0.0)

    roof_equip("lib_roof_eq1", CX - 6.0, CY - 2.0, 2.2, 1.6, 22.75, "S")
    roof_equip("lib_roof_eq2", CX + 6.0, CY + 3.0, 1.6, 1.2, 22.6, "N")
    cyl("lib_roof_vent", CX + 2.0, CY - 4.0, 21.3, 22.1, 0.4, MAT_METAL)

    # ---- 空调外机: 每层长边 3 台 + 短边 1 台 ----
    def ac_unit(prefix, ux, uy, zc, facing):
        if facing in ("S", "N"):
            bw, bd = 0.9, 0.28
            gy = uy + (0.15 if facing == "N" else -0.15)
            box(prefix, ux, uy, zc - 0.31, zc + 0.31, bw, bd, MAT_AC_BODY, bevel=0.02)
            box(prefix + "_grille", ux, gy, zc - 0.22, zc + 0.22, 0.78, 0.03,
                MAT_GRILLE, bevel=0.0)
            box(prefix + "_bracket", ux, uy, zc - 0.40, zc - 0.34, 0.9, 0.10,
                MAT_METAL, bevel=0.0)
        else:
            bw, bd = 0.28, 0.9
            gx = ux + (0.15 if facing == "E" else -0.15)
            box(prefix, ux, uy, zc - 0.31, zc + 0.31, bw, bd, MAT_AC_BODY, bevel=0.02)
            box(prefix + "_grille", gx, uy, zc - 0.22, zc + 0.22, 0.03, 0.78,
                MAT_GRILLE, bevel=0.0)
            box(prefix + "_bracket", ux, uy, zc - 0.40, zc - 0.34, 0.10, 0.9,
                MAT_METAL, bevel=0.0)

    n_ac = 0
    for fi, z0 in enumerate((0.5, 4.0, 7.4, 10.8, 14.2, 17.6)):
        zc = z0 + 1.7 if fi > 0 else z0 + 1.5
        hw = 11.8 if fi > 0 else 12.0
        hd = 7.8 if fi > 0 else 8.0
        for j, off in enumerate((-8.0, 0.0, 8.0)):
            # 首层南面正中让位给门廊雨棚
            if fi == 0 and off == 0.0:
                pass
            else:
                ac_unit("lib_ac_F%d_S%d" % (fi + 1, j), CX + off, CY - hd - 0.14, zc, "S")
                n_ac += 1
            ac_unit("lib_ac_F%d_N%d" % (fi + 1, j), CX + off, CY + hd + 0.14, zc, "N")
            n_ac += 1
        ac_unit("lib_ac_F%d_E0" % (fi + 1), CX + hw + 0.14, CY, zc, "E")
        ac_unit("lib_ac_F%d_W0" % (fi + 1), CX - hw - 0.14, CY, zc, "W")
        n_ac += 2
    print("AC outdoor units:", n_ac)

    # ---- 正门 (南面正中) + 门廊雨棚 + 三级台阶 ----
    # 门框 3.4 宽 x 3.2 高，木色双开门 + 玻璃上亮
    box("lib_door_frame", CX, CY - 8.0 - 0.05, 0.5, 3.7, 3.4, 0.12, MAT_DOOR, bevel=0.02)
    box("lib_door_L", CX - 0.75, CY - 8.0 - 0.10, 0.5, 3.0, 1.4, 0.08, MAT_DOOR, bevel=0.0)
    box("lib_door_R", CX + 0.75, CY - 8.0 - 0.10, 0.5, 3.0, 1.4, 0.08, MAT_DOOR, bevel=0.0)
    box("lib_door_glass_L", CX - 0.75, CY - 8.0 - 0.15, 2.2, 2.8, 1.0, 0.04, MAT_DOOR_GLASS, bevel=0.0)
    box("lib_door_glass_R", CX + 0.75, CY - 8.0 - 0.15, 2.2, 2.8, 1.0, 0.04, MAT_DOOR_GLASS, bevel=0.0)
    box("lib_door_lintel", CX, CY - 8.0 - 0.10, 3.0, 3.7, 3.4, 0.14, MAT_BAND, bevel=0.02)
    # 雨棚 6.0 x 2.2，z 3.4-3.65，前沿红褐色檐口
    box("lib_entry_canopy", CX, CY - 8.0 - 1.1, 3.4, 3.65, 6.0, 2.2, MAT_CONC, bevel=0.03)
    box("lib_entry_fascia", CX, CY - 8.0 - 2.18, 3.4, 3.65, 6.0, 0.08, MAT_BAND, bevel=0.0)
    box("lib_entry_col_L", CX - 2.6, CY - 8.0 - 2.0, 0.5, 3.4, 0.3, 0.3, MAT_CONC, bevel=0.02)
    box("lib_entry_col_R", CX + 2.6, CY - 8.0 - 2.0, 0.5, 3.4, 0.3, 0.3, MAT_CONC, bevel=0.02)
    # 三级台阶：逐级收进
    box("lib_steps_1", CX, CY - 8.0 - 1.3, 0.0, 0.17, 6.4, 2.6, MAT_CONC, bevel=0.02)
    box("lib_steps_2", CX, CY - 8.0 - 0.95, 0.17, 0.34, 6.4, 1.9, MAT_CONC, bevel=0.02)
    box("lib_steps_3", CX, CY - 8.0 - 0.6, 0.34, 0.5, 6.4, 1.2, MAT_CONC, bevel=0.02)

    return building


def main():
    building = build()
    print("built objects:", len(building))
    os.makedirs(PY_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print("saved blend:", BLEND_PATH)
    bpy.ops.object.select_all(action="DESELECT")
    for o in building:
        o.select_set(True)
    bpy.context.view_layer.objects.active = building[0]
    bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format="GLB",
                               use_selection=True, export_apply=True)
    print("exported glb:", GLB_PATH, "objects:", len(building))
    # 回读校验
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.import_scene.gltf(filepath=GLB_PATH)
    imported = [o for o in bpy.context.selected_objects]
    print("GLB reimport objects:", len(imported))
    blend1 = BLEND_PATH + "1"
    if os.path.exists(blend1):
        os.remove(blend1)
    print("DONE ov-lib")


main()
