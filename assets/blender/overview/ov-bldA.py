# ov-bldA v2: 一号教学楼楼体返工 (overview piece)
# 40(x) x 15(y) x 19(z) m, 5 floors, Blender centre (-56, 30, 0)
# 位置/尺寸/朝向照旧版，不改楼的位置和占地。
# v2 返工内容:
# - 墙面: 程序化混凝土/涂料纹 (Noise 斑驳 + Bump, 粗糙度变化),
#   楼层分缝 (檐口线脚 + 线脚下暗色缝线), 雨水渍/风化 (竖向渍痕,
#   墙根加重); 墙色米白 #F3E9D2, sRGB->线性赋值。
# - 女儿墙: 0.9 m 高 (顶 19.0 = 屋顶板顶 18.35 + 0.65)，厚 0.3 m，
#   压顶略出挑，混凝土纹。
# - 正门 (南面中部): 玻璃双开门 + 浅色门框/过梁 + 门廊雨棚
#   (两柱支撑) + 三级台阶; 正门占中开间，一层南面中部空调外机
#   因此省去 1 台。
# - 屋顶: 深灰防水层 + Noise 颗粒 + 卷材搭接缝 (Brick 分缝) + Bump。
# - "V"形折片查清: 不是放错的几何体, 是旧版屋顶设备盒
#   (bldA_roof_equip_1/2): 盒体仅 0.35 m 露出女儿墙, 顶盖与屋顶
#   同色 #424A52, 远看只剩两条受光边, 读成 "V"。v2 把两盒做高
#   (高出女儿墙约 0.9 m)、加百叶格栅, 做成像样的设备盒。
# - 空调外机: 沿外墙分层挂 (长边每层 5 台 + 短边每层 1 台,
#   共 59 台，见正门说明): 小灰盒 + 波纹格栅面板 + 托架。
# - 不加窗 (窗归 ov-windows-roofs), 不动楼体量块。
# - 全部结构件带小倒角; 没有任何一个面是全平的 (墙/顶/女儿墙/
#   混凝土/金属/格栅全部程序化纹理)。
#
# Height note (documented, not hidden): campus.json says building height is
# "示意" (indicative) while classroom.json floor heights are measured
# (1F 3.5 m, 2-5F 3.0 m -> wall 15.5 m). The 19 m envelope is kept because
# SPEC section 6 (pv) places the A-roof at z=19, so the PV piece docks here.
# Floors are therefore stretched evenly inside the 19 m envelope:
# plinth 0-0.5, F1 0.5-4.5 (4.0 m), F2-F5 3.4 m each to 18.1,
# roof slab 18.1-18.35, parapet 18.1-19.0 (0.9 m). Top overall = 19.0 m.
# Top floor (5F) is inset 0.3 m per side (收分) under the roof overhang.
#
# Modes (args after "--"): export-only (default) = 建模->存盘->导出->回读,
#   不渲染 (新规矩: 渲染全部走 GitHub Actions, 本地不渲染);
#   full = 建模->存盘->导出->回读->渲染 (仅显式调用);
#   render-only = 打开已存 .blend 只渲染预览图 (OOM 补图用)。

import bpy
import math
import os
import sys
from mathutils import Vector

PIECE = "ov-bldA"
BASE = os.path.expanduser("~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
PY_DIR = os.path.join(BASE, "assets/blender/overview")
BLEND_PATH = os.path.join(PY_DIR, "ov-bldA.blend")
GLB_PATH = os.path.join(BASE, "assets/models/ov-bldA.glb")
PNG_PATH = os.path.join(BASE, "screenshots/blender/ov-bldA.png")

CX, CY = -56.0, 30.0   # building centre (Blender x, y)
W, D = 40.0, 15.0      # footprint x, y

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
MODE = argv[0] if argv else "export-only"


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
    """米白涂料墙: 大尺度斑驳 + 细颗粒 Bump + 竖向雨水渍 (墙根加重)."""
    m, bsdf = _new_mat("Wall_Cream_F3E9D2_tex", "#F3E9D2", 0.85)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    # 大斑驳: Object 坐标米制, Noise 尺度 0.35 -> 约 3 m 一块深浅
    n1 = _noise(nt, "Mottle", 0.35, detail=3, rough=0.7)
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    ramp1 = _ramp(nt, "MottleRamp", [(0.0, "#E0CFAB"), (0.5, "#F3E9D2"), (1.0, "#FAF2DE")])
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
    mix.inputs["Color2"].default_value = hex_rgb("#D3C096")  # 渍痕深米色
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
    """混凝土: 斑驳 + 颗粒 Bump (女儿墙/勒脚/压顶)."""
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


def glass_mat():
    """Entrance door glass: pale blue-grey #9FC3D8, low roughness, fine grain Bump."""
    m, bsdf = _new_mat("Door_Glass_9FC3D8_tex", "#9FC3D8", 0.18, 0.1)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n1 = _noise(nt, "Grain", 4.0, detail=2, rough=0.8)
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    b = _bump(nt, n1.outputs["Fac"], strength=0.12, distance=0.02)
    nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    return m


MAT_WALL = wall_mat()
MAT_ROOF = roof_mat()
MAT_CONC = conc_mat()
MAT_BAND = band_mat()
MAT_METAL = metal_mat()
MAT_AC_BODY = metal_mat("#D5D9DC", "AC_Body_D5D9DC", 0.5, 0.25)
MAT_GRILLE = grille_mat()
MAT_GLASS = glass_mat()
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
    box("bldA_plinth", CX, CY, 0.0, 0.5, W + 0.6, D + 0.6, MAT_CONC, bevel=0.04)
    box("bldA_plinth_cap", CX, CY, 0.5, 0.68, W + 0.7, D + 0.7, MAT_BAND, bevel=0.03)

    # ---- main wall block F1-F4 (0.5-14.7) ----
    box("bldA_body_F1_F4", CX, CY, 0.5, 14.7, W, D, MAT_WALL, bevel=0.06)
    # ---- top floor, inset 0.3 m per side (14.7-18.1) ----
    box("bldA_body_F5_inset", CX, CY, 14.7, 18.1, W - 0.6, D - 0.6, MAT_WALL, bevel=0.06)

    # ---- floor cornice bands (檐口线脚) + dark seam groove just below ----
    for i, zc in enumerate((4.5, 7.9, 11.3, 14.7)):
        box("bldA_cornice_F%d" % (i + 2), CX, CY, zc - 0.14, zc + 0.14,
            W + 0.3, D + 0.3, MAT_BAND, bevel=0.03)
        # 楼层分缝: 线脚下 0.06 高暗色缝线, 四周出挑 0.03
        box("bldA_seam_F%d" % (i + 2), CX, CY, zc - 0.24, zc - 0.18,
            W + 0.06, D + 0.06, MAT_SEAM, bevel=0.0)

    # ---- main entrance (south face, centre bay): door + canopy + steps ----
    # South wall face F1-F4 is y = CY - D/2 = 22.5; plinth face 22.2.
    # Door sill at plinth-cap top 0.68; steps rise 0 -> 0.68 in 3 treads.
    EY = CY - D / 2  # 22.5, south wall face
    # door leaf: double glass door, 3.6 wide x 3.0 high, proud of wall
    box("bldA_entrance_door", CX, EY - 0.06, 0.68, 3.68, 3.6, 0.12, MAT_GLASS, bevel=0.02)
    # frame: two pilasters + lintel, light stone band colour
    box("bldA_entrance_pilaster_W", CX - 1.95, EY - 0.12, 0.68, 3.85, 0.3, 0.25, MAT_BAND, bevel=0.02)
    box("bldA_entrance_pilaster_E", CX + 1.95, EY - 0.12, 0.68, 3.85, 0.3, 0.25, MAT_BAND, bevel=0.02)
    box("bldA_entrance_lintel", CX, EY - 0.12, 3.68, 3.98, 4.2, 0.25, MAT_BAND, bevel=0.02)
    # centre mullion + transom bar + two pull handles (thin parts: no bevel)
    box("bldA_entrance_mullion", CX, EY - 0.14, 0.68, 3.68, 0.08, 0.05, MAT_METAL, bevel=0.0)
    box("bldA_entrance_transom", CX, EY - 0.14, 2.55, 2.65, 3.6, 0.05, MAT_METAL, bevel=0.0)
    box("bldA_entrance_handle_W", CX - 0.25, EY - 0.16, 1.45, 1.95, 0.05, 0.05, MAT_METAL, bevel=0.0)
    box("bldA_entrance_handle_E", CX + 0.25, EY - 0.16, 1.45, 1.95, 0.05, 0.05, MAT_METAL, bevel=0.0)
    # canopy slab (6.4 x 2.4, z 3.98-4.16) on two columns standing on platform
    box("bldA_entrance_canopy", CX, EY - 1.2, 3.98, 4.16, 6.4, 2.4, MAT_BAND, bevel=0.03)
    box("bldA_entrance_column_W", CX - 2.9, EY - 1.6, 0.68, 3.98, 0.28, 0.28, MAT_CONC, bevel=0.02)
    box("bldA_entrance_column_E", CX + 2.9, EY - 1.6, 0.68, 3.98, 0.28, 0.28, MAT_CONC, bevel=0.02)
    # steps: 3 treads, each 0.35 deeper out, width 6.0, top flush with sill 0.68
    box("bldA_entrance_step_top", CX, EY - 1.05, 0.45, 0.68, 6.0, 1.5, MAT_CONC, bevel=0.02)
    box("bldA_entrance_step_mid", CX, EY - 1.225, 0.22, 0.45, 6.0, 1.85, MAT_CONC, bevel=0.02)
    box("bldA_entrance_step_low", CX, EY - 1.4, 0.0, 0.22, 6.0, 2.2, MAT_CONC, bevel=0.02)

    # ---- roof slab (dark grey, inside parapet) ----
    box("bldA_roof_slab", CX, CY, 18.1, 18.35, W - 1.0, D - 1.0, MAT_ROOF, bevel=0.03)

    # ---- parapet (top 19.0 = roof slab top 18.35 + 0.65, thickness 0.3) ----
    PW, PD = W - 0.6, D - 0.6   # parapet outer footprint = top-floor footprint
    T = 0.30
    box("bldA_parapet_S", CX, CY - (PD / 2 - T / 2), 18.1, 18.92, PW, T, MAT_CONC, bevel=0.02)
    box("bldA_parapet_N", CX, CY + (PD / 2 - T / 2), 18.1, 18.92, PW, T, MAT_CONC, bevel=0.02)
    box("bldA_parapet_W", CX - (PW / 2 - T / 2), CY, 18.1, 18.92, T, PD - 2 * T, MAT_CONC, bevel=0.02)
    box("bldA_parapet_E", CX + (PW / 2 - T / 2), CY, 18.1, 18.92, T, PD - 2 * T, MAT_CONC, bevel=0.02)
    # parapet cap (压顶), top flush at z = 19.0, 出挑 0.06/边
    box("bldA_parapet_cap_S", CX, CY - (PD / 2 - T / 2), 18.92, 19.0, PW, T + 0.12, MAT_CONC, bevel=0.02)
    box("bldA_parapet_cap_N", CX, CY + (PD / 2 - T / 2), 18.92, 19.0, PW, T + 0.12, MAT_CONC, bevel=0.02)
    box("bldA_parapet_cap_W", CX - (PW / 2 - T / 2), CY, 18.92, 19.0, T + 0.12, PD - 2 * T, MAT_CONC, bevel=0.02)
    box("bldA_parapet_cap_E", CX + (PW / 2 - T / 2), CY, 18.92, 19.0, T + 0.12, PD - 2 * T, MAT_CONC, bevel=0.02)

    # ---- roof equipment boxes (reworked, v2): tall, louvred, readable ----
    # v1 查清结论见文件头: 旧盒仅 0.35 m 露出女儿墙且顶盖同屋顶色,
    # 远看只剩两条受光边成 "V"。v2 盒体高出女儿墙约 0.9 m + 百叶。
    def roof_equip(prefix, ex, ey, bw, bd, ztop, louvre_side):
        box(prefix, ex, ey, 18.35, ztop, bw, bd, MAT_METAL, bevel=0.04)
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

    roof_equip("bldA_roof_equip_1", -68.0, 26.5, 2.4, 1.8, 19.9, "S")
    roof_equip("bldA_roof_equip_2", -44.0, 33.5, 2.0, 1.6, 19.75, "N")

    # ---- AC outdoor units: per floor, long sides 5 each + short sides 1 each ----
    # floor z0s: F1 0.5, F2 4.5, F3 7.9, F4 11.3, F5 14.7; unit centre z0+1.0
    # F5 inset faces: half-width 19.7 / half-depth 7.2; F1-F4: 20.0 / 7.5
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
    for fi, z0 in enumerate((0.5, 4.5, 7.9, 11.3, 14.7)):
        zc = z0 + 1.0
        hw = 19.7 if fi == 4 else 20.0
        hd = 7.2 if fi == 4 else 7.5
        for j, off in enumerate((-16.0, -8.0, 0.0, 8.0, 16.0)):
            # F1 south centre bay is the main entrance: that AC unit is omitted
            if not (fi == 0 and j == 2):
                ac_unit("bldA_ac_F%d_S%d" % (fi + 1, j), CX + off, CY - hd - 0.14, zc, "S")
                n_ac += 1
            ac_unit("bldA_ac_F%d_N%d" % (fi + 1, j), CX + off, CY + hd + 0.14, zc, "N")
            n_ac += 1
        ac_unit("bldA_ac_F%d_E0" % (fi + 1), CX + hw + 0.14, CY, zc, "E")
        ac_unit("bldA_ac_F%d_W0" % (fi + 1), CX - hw - 0.14, CY, zc, "W")
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
    target = Vector((CX, CY, 9.0))
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

    # ---- camera: 45 deg down, from SW so sunlit faces show, lens 35 mm ----
    bpy.ops.object.camera_add(location=(CX - 40.0, CY - 40.0, 65.0))
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


if MODE == "render-only":
    bpy.ops.wm.open_mainfile(filepath=BLEND_PATH)
    print("opened blend for render-only:", BLEND_PATH)
    render_preview()
    print("DONE ov-bldA")
else:
    building = build()
    imported = save_and_export(building)
    if MODE == "full":
        # drop the re-imported duplicates before rendering (avoid z-fighting)
        bpy.ops.object.select_all(action="DESELECT")
        for o in imported:
            o.select_set(True)
        bpy.ops.object.delete(use_global=False)
        render_preview()
    print("DONE ov-bldA")
