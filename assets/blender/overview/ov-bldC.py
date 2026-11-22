# ov-bldC v2: 三号教学楼楼体返工 (overview piece)
# 22(x) x 13(y) m, Blender centre (26, 30, 0), 浅橙墙 #F6D9C0
# 位置/尺寸/朝向照旧版与 SPEC §4, 不改楼的位置和占地。
# v2 返工内容 (筛查结论: 旧版是白盒子——无窗无门无女儿墙无空调外机,
# 屋顶深灰平板, 所有面放大后均匀纯色):
# - 墙面: 程序化涂料纹 (Noise 斑驳 + Bump, 粗糙度变化),
#   楼层分缝 (檐口线脚 + 线脚下暗色缝线), 雨水渍/风化 (竖向渍痕,
#   墙根加重); 墙色浅橙 #F6D9C0, sRGB->线性赋值。
# - 女儿墙: 顶面 = 屋顶板顶面 +0.75 m (= 14.0 m), 厚 0.3 m, 压顶略出挑,
#   混凝土纹 (光伏屋顶面层 pv-roof 按此收边, 拼装时核对)。
# - 屋顶: 深灰防水卷材纹 (Brick 搭接缝 + Noise 颗粒 + Bump),
#   不再是深灰平板。
# - 空调外机: 每层外墙挂机 (长边每层 3 台 + 短边每层 1 台,
#   F1 南侧正门上方 1 台让位, 共 31 台): 小灰盒 + 波纹格栅 + 托架。
# - 正门 + 门廊雨棚 + 台阶 (南立面正中)。
# - 不加窗 (窗归 ov-windows-roofs), 不动楼体量块。
# - 全部结构件带小倒角 (薄件除外); 没有任何一个面是全平的。
#
# Height (SPEC §4 + ov-windows-roofs C data, verified 2026-11-23):
# 22x13 m, 4F, envelope 14.0 m. Measured floor heights (1F 3.5 m,
# 2-4F 3.0 m): plinth 0-0.5, F1 0.5-4.0, F2 4.0-7.0, F3 7.0-10.0,
# F4 10.0-13.0, roof slab 13.0-13.25, parapet 13.25-13.90 + cap to 14.0.
# Top floor (F4) is inset 0.3 m per side (收分) under the roof overhang.
# Roof plant (tall louvred boxes) rises above the 14.0 m envelope to
# 14.92 m, same pattern as ov-bldA (19.0 m envelope, plant to 20.02 m);
# the SPEC table height is the parapet top.
# (v2 wrongly stretched floors to 4.4 m each inside a 19 m envelope,
# misreading SPEC §6 "PV roof docks at z=19" — that z=19 is bldA's roof,
# not bldC's. ov-windows-roofs was already built to the correct 14 m
# C heights, so v2's body and its window bands were misaligned.)
#
# Modes (args after "--"): full (default) = 建模->存盘->导出->回读->渲染;
#   export-only = 建模->存盘->导出->回读, 不渲染 (落盘优先);
#   render-only = 打开已存 .blend 只渲染预览图 (OOM 补图用)。

import bpy
import os
import sys
from mathutils import Vector

PIECE = "ov-bldC"
BASE = os.path.expanduser("~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
PY_DIR = os.path.join(BASE, "assets/blender/overview")
BLEND_PATH = os.path.join(PY_DIR, "ov-bldC.blend")
GLB_PATH = os.path.join(BASE, "assets/models/ov-bldC.glb")
PNG_PATH = os.path.join(BASE, "screenshots/blender/ov-bldC.png")

CX, CY = 26.0, 30.0   # building centre (Blender x, y)
W, D = 22.0, 13.0     # footprint x, y

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
MODE = argv[0] if argv else "full"


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
    m, bsdf = _new_mat("Wall_Orange_F6D9C0_tex", "#F6D9C0", 0.85)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    # 大斑驳: Object 坐标米制, Noise 尺度 0.35 -> 约 3 m 一块深浅
    n1 = _noise(nt, "Mottle", 0.35, detail=3, rough=0.7)
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    ramp1 = _ramp(nt, "MottleRamp", [(0.0, "#E8C4A2"), (0.5, "#F6D9C0"), (1.0, "#FBE9D6")])
    nt.links.new(n1.outputs["Fac"], ramp1.inputs["Fac"])
    # 竖向渍痕: Z 向拉伸的 Noise (Mapping 缩小 Z -> 痕迹竖长)
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
    # 墙根加重: Generated Z (0 底 -> 1 顶), 底部因子 = 1 - Z
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
    mix.inputs["Color2"].default_value = hex_rgb("#D9B48E")  # 渍痕深橙
    nt.links.new(mul2.outputs["Value"], mix.inputs["Fac"])
    nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    # 细颗粒 Bump
    n3 = _noise(nt, "Grain", 2.2, detail=2, rough=0.8)
    nt.links.new(tc.outputs["Object"], n3.inputs["Vector"])
    b = _bump(nt, n3.outputs["Fac"], strength=0.35, distance=0.06)
    nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    # 粗糙度随斑驳变化 0.72~0.95
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
    """混凝土: 斑驳 + 颗粒 Bump (女儿墙/勒脚/压顶/台阶)."""
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


def wood_mat():
    """正门木色: 暖棕 + 竖纹 Noise + 轻 Bump."""
    m, bsdf = _new_mat("Door_Wood_8A6B4A_tex", "#8A6B4A", 0.7)
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


def metal_mat(hexcol="#C0C5C9", name="MetalGrey_tex", rough=0.55, metallic=0.3):
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
MAT_ROOF = roof_mat()
MAT_CONC = conc_mat()
MAT_BAND = band_mat()
MAT_WOOD = wood_mat()
MAT_METAL = metal_mat()
MAT_AC_BODY = metal_mat("#D5D9DC", "AC_Body_D5D9DC", 0.5, 0.25)
MAT_GRILLE = grille_mat()
MAT_SEAM = _new_mat("FloorSeam_B7A988", "#B7A988", 0.9)[0]
MAT_GROUND = _new_mat("Ground_Grass_69B45E", "#69B45E", 1.0)[0]


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
    box("bldC_plinth", CX, CY, 0.0, 0.5, W + 0.6, D + 0.6, MAT_CONC, bevel=0.04)
    box("bldC_plinth_cap", CX, CY, 0.5, 0.68, W + 0.7, D + 0.7, MAT_BAND, bevel=0.03)

    # ---- main wall block F1-F3 (0.5-10.0): F1 3.5 m, F2-F3 3.0 m each ----
    box("bldC_body_F1_F3", CX, CY, 0.5, 10.0, W, D, MAT_WALL, bevel=0.06)
    # ---- top floor, inset 0.3 m per side (10.0-13.0) ----
    box("bldC_body_F4_inset", CX, CY, 10.0, 13.0, W - 0.6, D - 0.6, MAT_WALL, bevel=0.06)

    # ---- floor cornice bands (檐口线脚) + dark seam groove just below ----
    # named by the floor starting above each band; the top band is the
    # roof eave (no F5 in a 4-storey building)
    for tag, zc in (("F2", 4.0), ("F3", 7.0), ("F4", 10.0), ("roof", 13.0)):
        box("bldC_cornice_%s" % tag, CX, CY, zc - 0.14, zc + 0.14,
            W + 0.3, D + 0.3, MAT_BAND, bevel=0.03)
        # 楼层分缝: 线脚下 0.06 高暗色缝线, 四周出挑 0.03
        box("bldC_seam_%s" % tag, CX, CY, zc - 0.24, zc - 0.18,
            W + 0.06, D + 0.06, MAT_SEAM, bevel=0.0)

    # ---- roof slab (dark grey membrane, inside parapet) ----
    box("bldC_roof_slab", CX, CY, 13.0, 13.25, W - 1.0, D - 1.0, MAT_ROOF, bevel=0.03)

    # ---- parapet (女儿墙): wall 13.25-13.90 + cap 13.90-14.0,
    #      厚 0.3 m, 顶面 = 板顶 +0.75 m = 14.0 ----
    PW, PD = W - 0.6, D - 0.6   # parapet outer footprint = top-floor footprint
    T = 0.30
    box("bldC_parapet_S", CX, CY - (PD / 2 - T / 2), 13.25, 13.90, PW, T, MAT_CONC, bevel=0.02)
    box("bldC_parapet_N", CX, CY + (PD / 2 - T / 2), 13.25, 13.90, PW, T, MAT_CONC, bevel=0.02)
    box("bldC_parapet_W", CX - (PW / 2 - T / 2), CY, 13.25, 13.90, T, PD - 2 * T, MAT_CONC, bevel=0.02)
    box("bldC_parapet_E", CX + (PW / 2 - T / 2), CY, 13.25, 13.90, T, PD - 2 * T, MAT_CONC, bevel=0.02)
    # parapet cap (压顶), top flush at z = 14.0, 出挑 0.06/边
    box("bldC_parapet_cap_S", CX, CY - (PD / 2 - T / 2), 13.90, 14.0, PW, T + 0.12, MAT_CONC, bevel=0.02)
    box("bldC_parapet_cap_N", CX, CY + (PD / 2 - T / 2), 13.90, 14.0, PW, T + 0.12, MAT_CONC, bevel=0.02)
    box("bldC_parapet_cap_W", CX - (PW / 2 - T / 2), CY, 13.90, 14.0, T + 0.12, PD - 2 * T, MAT_CONC, bevel=0.02)
    box("bldC_parapet_cap_E", CX + (PW / 2 - T / 2), CY, 13.90, 14.0, T + 0.12, PD - 2 * T, MAT_CONC, bevel=0.02)

    # ---- roof equipment boxes: tall, louvred, readable above parapet ----
    def roof_equip(prefix, ex, ey, bw, bd, ztop, louvre_side):
        box(prefix, ex, ey, 13.25, ztop, bw, bd, MAT_METAL, bevel=0.04)
        box(prefix + "_lid", ex, ey, ztop, ztop + 0.12, bw + 0.2, bd + 0.2,
            MAT_ROOF, bevel=0.02)
        # 百叶: 外立面 3 道横向深灰条
        for k, zl in enumerate((ztop - 0.95, ztop - 0.6, ztop - 0.25)):
            if louvre_side == "S":
                box("%s_louvre_%d" % (prefix, k), ex, ey - bd / 2 - 0.02,
                    zl - 0.06, zl + 0.06, bw - 0.5, 0.05, MAT_GRILLE, bevel=0.0)
            else:
                box("%s_louvre_%d" % (prefix, k), ex, ey + bd / 2 + 0.02,
                    zl - 0.06, zl + 0.06, bw - 0.5, 0.05, MAT_GRILLE, bevel=0.0)

    roof_equip("bldC_roof_equip_1", 20.0, 32.5, 2.0, 1.6, 14.8, "S")
    roof_equip("bldC_roof_equip_2", 32.0, 27.5, 1.8, 1.4, 14.65, "N")

    # ---- main entrance: south face centre (south = -y) ----
    # door sill at plinth top 0.5; door 2.4 wide x 2.5 high, frame proud of wall
    SY = CY - D / 2  # south wall face y = 23.5
    box("bldC_door_frame", CX, SY - 0.06, 0.5, 3.1, 2.8, 0.22, MAT_BAND, bevel=0.03)
    box("bldC_door_L", CX - 0.6, SY - 0.14, 0.5, 3.0, 1.16, 0.10, MAT_WOOD, bevel=0.02)
    box("bldC_door_R", CX + 0.6, SY - 0.14, 0.5, 3.0, 1.16, 0.10, MAT_WOOD, bevel=0.02)
    # door handles
    box("bldC_door_handle_L", CX - 0.12, SY - 0.24, 1.35, 1.45, 0.05, 0.08, MAT_METAL, bevel=0.0)
    box("bldC_door_handle_R", CX + 0.12, SY - 0.24, 1.35, 1.45, 0.05, 0.08, MAT_METAL, bevel=0.0)
    # canopy slab 4.4 x 1.8 at z 3.2-3.4, out from the wall
    box("bldC_canopy", CX, SY - 0.85, 3.2, 3.4, 4.4, 1.8, MAT_CONC, bevel=0.03)
    box("bldC_canopy_edge", CX, SY - 1.72, 3.2, 3.34, 4.4, 0.12, MAT_BAND, bevel=0.02)
    # canopy columns (0.25 sq) from ground to canopy, at the outer corners
    box("bldC_col_L", CX - 1.9, SY - 1.6, 0.0, 3.2, 0.25, 0.25, MAT_CONC, bevel=0.02)
    box("bldC_col_R", CX + 1.9, SY - 1.6, 0.0, 3.2, 0.25, 0.25, MAT_CONC, bevel=0.02)
    # steps: 3 steps down from plinth top 0.5 to ground, in front of the door
    box("bldC_step_1", CX, SY - 1.0, 0.33, 0.5, 4.0, 0.7, MAT_CONC, bevel=0.02)
    box("bldC_step_2", CX, SY - 1.65, 0.17, 0.33, 4.0, 0.6, MAT_CONC, bevel=0.02)
    box("bldC_step_3", CX, SY - 2.2, 0.0, 0.17, 4.0, 0.5, MAT_CONC, bevel=0.02)

    # ---- AC outdoor units: per floor, long sides 3 each + short sides 1 each ----
    # floor z0s: F1 0.5, F2 4.0, F3 7.0, F4 10.0; unit centre z0+1.0
    # F4 inset faces: half-width 10.7 / half-depth 6.2; F1-F3: 11.0 / 6.5
    # F1 south-centre unit skipped: the main entrance + canopy sit there.
    def ac_unit(prefix, ux, uy, zc, facing):
        # body 0.9 (along wall) x 0.28 (out) x 0.62, grille on outer face,
        # bracket bar under body
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
    for fi, z0 in enumerate((0.5, 4.0, 7.0, 10.0)):
        zc = z0 + 1.0
        hw = 10.7 if fi == 3 else 11.0
        hd = 6.2 if fi == 3 else 6.5
        for j, off in enumerate((-7.5, 0.0, 7.5)):
            if fi == 0 and j == 1:
                # south-centre F1: entrance canopy/door occupies this spot
                ac_unit("bldC_ac_F%d_N%d" % (fi + 1, j), CX + off, CY + hd + 0.14, zc, "N")
                n_ac += 1
                continue
            ac_unit("bldC_ac_F%d_S%d" % (fi + 1, j), CX + off, CY - hd - 0.14, zc, "S")
            ac_unit("bldC_ac_F%d_N%d" % (fi + 1, j), CX + off, CY + hd + 0.14, zc, "N")
            n_ac += 2
        ac_unit("bldC_ac_F%d_E0" % (fi + 1), CX + hw + 0.14, CY, zc, "E")
        ac_unit("bldC_ac_F%d_W0" % (fi + 1), CX - hw - 0.14, CY, zc, "W")
        n_ac += 2
    print("AC outdoor units:", n_ac)

    # ---- preview-only ground (NOT exported) ----
    bpy.ops.mesh.primitive_plane_add(location=(CX, CY, -0.01))
    ground = bpy.context.active_object
    ground.name = "Ground_PreviewOnly"
    ground.dimensions = (140.0, 100.0, 0.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ground.data.materials.append(MAT_GROUND)

    # ---- lighting (SPEC section 2): sun 3.5 from SW, elev ~50 deg ----
    target = Vector((CX, CY, 7.0))
    sun_dir = Vector((-0.64, -0.64, 1.0))  # sun sits SW and up
    bpy.ops.object.light_add(type="SUN", location=tuple(target + sun_dir * 80.0))
    sun = bpy.context.active_object
    sun.name = "Sun_SW"
    sun.data.energy = 3.5
    sun.data.use_shadow = True
    sun.rotation_euler = (target - sun.location).to_track_quat("-Z", "Y").to_euler()

    # ---- world: flat light blue (0.65, 0.78, 0.88), strength 1.0 ----
    world = bpy.data.worlds.new("World_LightBlue")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.65, 0.78, 0.88, 1.0)
    bg.inputs["Strength"].default_value = 1.0

    # ---- camera: from SW so sunlit south + west faces show, lens 35 mm ----
    bpy.ops.object.camera_add(location=(CX - 32.0, CY - 34.0, 44.0))
    cam = bpy.context.active_object
    cam.name = "Cam_Preview"
    cam.data.lens = 35.0
    cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam

    return building


def save_and_export(building):
    os.makedirs(PY_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(PNG_PATH), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print("saved blend:", BLEND_PATH)
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
    _check_glb_images(imported)
    return imported


def render_preview():
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 640
    scene.render.resolution_y = 360
    scene.render.resolution_percentage = 100
    scene.eevee.taa_render_samples = 16
    scene.render.filepath = PNG_PATH
    scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)
    print("rendered preview:", PNG_PATH)


# ---------- 烘焙程序化纹理为图片 (glTF 无法导出 Noise/Voronoi) ----------
# 照抄 dist/di-walls.py 已验证做法: 每种不透明材质选其全部对象 ->
# Cycles CPU 烘焙 color/rough/normal 三张 1024px 图 (margin 16px) ->
# 重建材质为图片纹理节点。玻璃材质不烘焙, 保持原样。
# 立方体自带 UV, 无需重展。烘焙图在 ov-bldC_textures/。
# 金属注意 (di-walls 全是非金属, 没这个问题): Principled 的 diffuse
# lobe 按 (1-metallic) 缩放, 直接烘 DIFFUSE 会把金属底色烘暗
# (实测 MetalGrey metallic 0.3 烘出来线性值正好是 0.7 倍)。
# 所以 color 烘焙时先把 Metallic 临时置 0 (只影响 diffuse 通道,
# rough/normal 与 metallic 无关), 烘完恢复; 重建材质时把原 metallic
# 常数写回 Principled, glTF 照常导出 metallicFactor。
TEX_DIR = os.path.join(PY_DIR, "ov-bldC_textures")


def _bake_images(mat, mat_objs, piece_objs):
    nt = mat.node_tree
    imgs = {}
    specs = [("color", 'DIFFUSE', 1024, 'sRGB'),
             ("rough", 'ROUGHNESS', 1024, 'Non-Color'),
             ("normal", 'NORMAL', 1024, 'Non-Color')]
    bsdf = nt.nodes.get("Principled BSDF")
    _metal_in = bsdf.inputs["Metallic"] if bsdf is not None else None
    _metal_linked = bool(_metal_in is not None and _metal_in.is_linked)
    _metal_val = _metal_in.default_value if (_metal_in is not None and not _metal_linked) else 0.0
    # 烘焙只关心本材质的对象: 把其余件对象 hide_render, Cycles 同步就跳过
    # 它们 (每 bake 少同步 ~200 个带倒角修饰器的对象, 实测不隐藏时单张
    # 烘焙要数分钟), 烘焙完恢复可见。
    _hidden = [ob for ob in piece_objs if ob not in mat_objs]
    for ob in _hidden:
        ob.hide_render = True
    bpy.ops.object.select_all(action='DESELECT')
    for ob in mat_objs:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = mat_objs[0]
    _bake_scene = bpy.context.scene
    _bake_scene.render.engine = 'CYCLES'
    _bake_scene.cycles.device = 'CPU'
    _bake_scene.cycles.samples = 4
    bake = _bake_scene.render.bake
    bake.use_selected_to_active = False
    bake.margin = 16
    for key, btype, size, cs in specs:
        # 断点续烘: 图已存在且能正常读入就复用 (照抄 B 组 ov-gym.py 做法, +1024 尺寸核对);
        # 读入失败/文件过小/尺寸不对则重新烘焙, 不硬复用错图。
        _fpath = os.path.join(TEX_DIR, "%s_%s.png" % (mat.name, key))
        if os.path.exists(_fpath) and os.path.getsize(_fpath) > 1000:
            try:
                _img = bpy.data.images.load(_fpath)
                if _img.size[0] != 1024 or _img.size[1] != 1024:
                    raise ValueError("wrong size %s, expect 1024x1024" % (_img.size,))
                _img.colorspace_settings.name = cs
                imgs[key] = _img
                print("reuse:", mat.name, key, _fpath,
                      os.path.getsize(_fpath))
                continue
            except Exception as _e:
                print("reload failed, re-bake:", mat.name, key, _e)
                try:
                    if '_img' in locals() and _img is not None and _img.name in bpy.data.images:
                        bpy.data.images.remove(_img)
                except Exception:
                    pass
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
            if _metal_in is not None and not _metal_linked:
                _metal_in.default_value = 0.0
        elif btype == 'NORMAL':
            bake.normal_space = 'TANGENT'
        bpy.ops.object.bake(type=btype)
        if btype == 'DIFFUSE' and _metal_in is not None and not _metal_linked:
            _metal_in.default_value = _metal_val
        img.filepath_raw = os.path.join(TEX_DIR, "%s_%s.png" % (mat.name, key))
        img.file_format = 'PNG'
        img.save()
        imgs[key] = img
        nt.nodes.remove(tex)
        print("baked:", mat.name, key, img.filepath_raw,
              os.path.getsize(img.filepath_raw))
    _bake_scene.render.engine = 'BLENDER_EEVEE_NEXT'
    for ob in _hidden:
        ob.hide_render = False
    return imgs


def _rebuild_with_images(mat, imgs, metallic=0.0):
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    bsdf.inputs["Roughness"].default_value = 1.0
    bsdf.inputs["Metallic"].default_value = metallic
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


def bake_piece(piece_objs):
    import time as _time
    _t0 = _time.time()
    os.makedirs(TEX_DIR, exist_ok=True)
    _by_mat = {}
    for _ob in piece_objs:
        if not _ob.data or not _ob.data.materials:
            continue
        _m = _ob.data.materials[0]
        if _m is None:
            continue
        if "glass" in _m.name.lower():
            print("bake skip (glass, kept as-is):", _m.name)
            continue
        _by_mat.setdefault(_m, []).append(_ob)
    _baked = {}
    _metallic = {}
    for _mat in _by_mat:
        _bsdf = _mat.node_tree.nodes.get("Principled BSDF")
        _mi = _bsdf.inputs["Metallic"] if _bsdf is not None else None
        _metallic[_mat.name] = _mi.default_value if (_mi is not None and not _mi.is_linked) else 0.0
    for _mat, _m_objs in _by_mat.items():
        _baked[_mat.name] = _bake_images(_mat, _m_objs, piece_objs)
    for _mat in _by_mat:
        _rebuild_with_images(_mat, _baked[_mat.name], _metallic[_mat.name])
    print("bake done, materials rebuilt with image textures, mats:",
          sorted(_baked.keys()), "elapsed: %.1fs" % (_time.time() - _t0))


def _check_glb_images(imported):
    for ob in imported:
        for slot in ob.material_slots:
            m = slot.material
            if m is None or not m.use_nodes:
                continue
            imgs = [n.image.name for n in m.node_tree.nodes
                    if n.type == 'TEX_IMAGE' and n.image is not None]
            print("GLB reimport mat:", ob.name, m.name, "images:", imgs)
            if "glass" in m.name.lower():
                continue
            assert len(imgs) >= 3, "glb material lost baked textures: %s" % m.name


if MODE == "render-only":
    bpy.ops.wm.open_mainfile(filepath=BLEND_PATH)
    print("opened blend for render-only:", BLEND_PATH)
    render_preview()
    print("DONE ov-bldC")
else:
    building = build()
    bake_piece(building)
    imported = save_and_export(building)
    if MODE == "full":
        # drop the re-imported duplicates before rendering (avoid z-fighting)
        bpy.ops.object.select_all(action="DESELECT")
        for o in imported:
            o.select_set(True)
        bpy.ops.object.delete(use_global=False)
        render_preview()
    print("DONE ov-bldC")
