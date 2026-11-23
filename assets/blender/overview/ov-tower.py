# ov-tower v2: 创造力中心楼体返工 (overview piece)
# 14(x) x 14(y) x 32(z) m, 8 floors, Blender centre (10, 54, 0)
# 位置/尺寸/朝向照旧版, 不改楼的位置和占地。campus.json 墙色 #F7F5EF。
# v2 返工内容 (筛查结论: 旧版是白盒子, 全面均匀纯色, 屋顶深灰平板):
#  1. 红/粉竖向饰带 (按鸟瞰图: 中央塔楼竖向红/粉条带): 南北面各一红一粉,
#     东西面各一红, 全高分段贴合收分, 带纹理 (Noise 斑驳 + 竖向渍痕 + Bump),
#     不是纯色条。
#  2. 墙面程序化纹理: 涂料斑驳 + 细颗粒 Bump + 竖向雨水渍 (墙根加重) +
#     楼层分缝 (檐口线脚 + 线脚下暗色缝线); sRGB->线性赋值。
#  3. 女儿墙: 顶面 = 屋顶板顶面 +0.65 m (32.0 -> 32.65), 厚 0.3 m, 压顶出挑。
#  4. 空调外机: 每层每面 2 台 (共 64 台): 小灰盒 + 波纹格栅面板 + 托架。
#  5. 屋顶: 深灰防水卷材纹理 (Brick 搭接缝 + Noise 颗粒 + Bump), 不再是平板。
#  6. 正门 + 门廊雨棚 + 台阶 (南面正中)。
#  7. 全部结构件带小倒角 (薄件除外)。
#  8. 窗带补回 (SPEC §5 归属: 本件自带简单窗带; 按 v1 做法):
#     每层横向窗带 + 竖分格条, 嵌进墙面 (框厚/窗台/内凹, 不贴墙);
#     玻璃淡蓝灰带反光 (透明度 + 镜面反射 + 反射探针); 窗框/竖挺/窗台
#     材质分开; 窗带在红/粉竖向饰带之间分段布置, 不压饰带。
# 分件边界: 窗带归本件, 其余只做墙体/纹理/女儿墙/空调/正门。
# 本次不渲染 (用户新规: 渲染全部走 GitHub Actions, 本地不渲染):
#   只做 建模 -> 存 .blend -> 导出 .glb -> 回读校验, 打印 DONE ov-tower。
#
# Height envelope (kept from v1): plinth 0-0.5, F1 0.5-4.5 (4.0 m),
# F2-F8 3.9 m each to 31.8, roof slab 31.8-32.0, parapet 32.0-32.65.
# Setbacks: F1 14.0, F2-F4 13.8, F5-F8 13.5.

import bpy
import os

PIECE = "ov-tower"
BASE = os.path.expanduser("~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
PY_DIR = os.path.join(BASE, "assets/blender/overview")
BLEND_PATH = os.path.join(PY_DIR, "ov-tower.blend")
GLB_PATH = os.path.join(BASE, "assets/models/ov-tower.glb")

CX, CY = 10.0, 54.0   # building centre (Blender x, y)
W, D = 14.0, 14.0     # footprint x, y


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
    """近白涂料墙 #F7F5EF: 大尺度斑驳 + 细颗粒 Bump + 竖向雨水渍 (墙根加重)."""
    m, bsdf = _new_mat("Wall_Cream_F7F5EF_tex", "#F7F5EF", 0.85)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n1 = _noise(nt, "Mottle", 0.35, detail=3, rough=0.7)
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    ramp1 = _ramp(nt, "MottleRamp", [(0.0, "#E2D9C2"), (0.5, "#F7F5EF"), (1.0, "#FCFAF2")])
    nt.links.new(n1.outputs["Fac"], ramp1.inputs["Fac"])
    # 竖向渍痕: Z 向拉伸的 Noise
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.6, 1.6, 0.25)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    n2 = _noise(nt, "Streaks", 1.1, detail=2, rough=0.75)
    nt.links.new(mp.outputs["Vector"], n2.inputs["Vector"])
    ramp2 = _ramp(nt, "StreakRamp", [(0.0, "#000000"), (0.62, "#000000"), (0.85, "#FFFFFF")])
    nt.links.new(n2.outputs["Fac"], ramp2.inputs["Fac"])
    # 墙根加重: Generated Z, 底部因子 = 1 - Z
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
    mix.inputs["Color2"].default_value = hex_rgb("#CFC2A2")  # 渍痕深米色
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


def accent_mat(name, base, dark, light):
    """红/粉竖向饰带: 斑驳 + 竖向渍痕 + Bump, 不是纯色条."""
    m, bsdf = _new_mat(name, base, 0.8)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n1 = _noise(nt, "Mottle", 0.5, detail=3, rough=0.7)
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    ramp1 = _ramp(nt, "MottleRamp", [(0.0, dark), (0.5, base), (1.0, light)])
    nt.links.new(n1.outputs["Fac"], ramp1.inputs["Fac"])
    # 竖向深浅条纹: Z 拉伸 Noise
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (2.0, 2.0, 0.3)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    n2 = _noise(nt, "Streaks", 1.2, detail=2, rough=0.75)
    nt.links.new(mp.outputs["Vector"], n2.inputs["Vector"])
    ramp2 = _ramp(nt, "StreakRamp", [(0.0, "#000000"), (0.6, "#000000"), (0.9, "#FFFFFF")])
    nt.links.new(n2.outputs["Fac"], ramp2.inputs["Fac"])
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MIX"
    nt.links.new(ramp1.outputs["Color"], mix.inputs["Color1"])
    mix.inputs["Color2"].default_value = hex_rgb(dark)
    nt.links.new(ramp2.outputs["Color"], mix.inputs["Fac"])
    nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    n3 = _noise(nt, "Grain", 2.5, detail=2, rough=0.8)
    nt.links.new(tc.outputs["Object"], n3.inputs["Vector"])
    b = _bump(nt, n3.outputs["Fac"], strength=0.4, distance=0.05)
    nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.3
    mr.inputs["From Max"].default_value = 0.7
    mr.inputs["To Min"].default_value = 0.68
    mr.inputs["To Max"].default_value = 0.92
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
    """混凝土: 斑驳 + 颗粒 Bump (女儿墙/勒脚/压顶/雨棚/台阶)."""
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
    """窗玻璃: 淡蓝灰 #9FC3D8, 透明度 0.65 + 低粗糙度镜面反光 + 细微明暗变化."""
    m, bsdf = _new_mat("Glass_Window_9FC3D8", "#9FC3D8", 0.12, 0.0)
    bsdf.inputs["Alpha"].default_value = 0.65
    bsdf.inputs["Specular IOR Level"].default_value = 1.0
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n1 = _noise(nt, "Sheen", 1.5, detail=2, rough=0.8)
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.35
    mr.inputs["From Max"].default_value = 0.65
    mr.inputs["To Min"].default_value = 0.06
    mr.inputs["To Max"].default_value = 0.22
    nt.links.new(n1.outputs["Fac"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])
    try:
        m.blend_method = "BLEND"
    except Exception:
        pass
    return m


def win_frame_mat():
    """窗框: 米白 #E9E6DD, 轻微斑驳 + 颗粒 Bump, 粗糙度 0.5~0.7."""
    m, bsdf = _new_mat("WinFrame_E9E6DD_tex", "#E9E6DD", 0.6)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n1 = _noise(nt, "Mottle", 1.2, detail=2, rough=0.7)
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    ramp1 = _ramp(nt, "MottleRamp", [(0.0, "#DCD8CB"), (0.5, "#E9E6DD"), (1.0, "#F2EFE6")])
    nt.links.new(n1.outputs["Fac"], ramp1.inputs["Fac"])
    nt.links.new(ramp1.outputs["Color"], bsdf.inputs["Base Color"])
    b = _bump(nt, n1.outputs["Fac"], strength=0.25, distance=0.03)
    nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.3
    mr.inputs["From Max"].default_value = 0.7
    mr.inputs["To Min"].default_value = 0.5
    mr.inputs["To Max"].default_value = 0.7
    nt.links.new(n1.outputs["Fac"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])
    return m


def win_mullion_mat():
    """竖挺: 金属灰 #8A8F94, 金属感 0.35, 细颗粒 Bump, 粗糙度 ~0.4."""
    m, bsdf = _new_mat("WinMullion_8A8F94_tex", "#8A8F94", 0.4, 0.35)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n1 = _noise(nt, "Grain", 4.0, detail=2, rough=0.8)
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    b = _bump(nt, n1.outputs["Fac"], strength=0.2, distance=0.02)
    nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def win_sill_mat():
    """窗台: 浅灰 #CFC9BC, 斑驳 + 颗粒 Bump, 粗糙度 0.9 (与窗框/竖挺分开)."""
    m, bsdf = _new_mat("WinSill_CFC9BC_tex", "#CFC9BC", 0.9)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n1 = _noise(nt, "Mottle", 1.0, detail=3, rough=0.7)
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    ramp1 = _ramp(nt, "MottleRamp", [(0.0, "#BFB8A8"), (0.5, "#CFC9BC"), (1.0, "#DDD7C8")])
    nt.links.new(n1.outputs["Fac"], ramp1.inputs["Fac"])
    nt.links.new(ramp1.outputs["Color"], bsdf.inputs["Base Color"])
    n2 = _noise(nt, "Grain", 3.0, detail=2, rough=0.8)
    nt.links.new(tc.outputs["Object"], n2.inputs["Vector"])
    b = _bump(nt, n2.outputs["Fac"], strength=0.35, distance=0.04)
    nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    return m


MAT_WALL = wall_mat()
MAT_RED = accent_mat("Accent_Red_B8543F_tex", "#B8543F", "#8E3527", "#C97A63")
MAT_PINK = accent_mat("Accent_Pink_D98E8E_tex", "#D98E8E", "#B96A6A", "#E8B4B0")
MAT_ROOF = roof_mat()
MAT_CONC = conc_mat()
MAT_BAND = band_mat()
MAT_METAL = metal_mat()
MAT_AC_BODY = metal_mat("#D5D9DC", "AC_Body_D5D9DC", 0.5, 0.25)
MAT_GRILLE = grille_mat()
MAT_SEAM = _new_mat("FloorSeam_B7A988", "#B7A988", 0.9)[0]
MAT_DOOR = metal_mat("#3A4046", "Door_Dark_3A4046", 0.6, 0.2)
MAT_DOOR_GLASS = _new_mat("Door_Glass_9FC3D8", "#9FC3D8", 0.25, 0.1)[0]
MAT_GLASS = glass_mat()
MAT_WIN_FRAME = win_frame_mat()
MAT_WIN_MULLION = win_mullion_mat()
MAT_WIN_SILL = win_sill_mat()


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

    # ---- 勒脚 (0-0.5) ----
    box("tower_plinth", CX, CY, 0.0, 0.5, 14.4, 14.4, MAT_CONC, bevel=0.04)
    box("tower_plinth_cap", CX, CY, 0.5, 0.68, 14.5, 14.5, MAT_BAND, bevel=0.03)

    # ---- 楼体分层 (收分: 一层 14.0, 二至四层 13.8, 五至八层 13.5) ----
    box("tower_floor1", CX, CY, 0.5, 4.5, 14.0, 14.0, MAT_WALL, bevel=0.06)
    for i in range(3):  # 二至四层 4.5-16.2
        z0 = 4.5 + i * 3.9
        box("tower_floor%d" % (i + 2), CX, CY, z0, z0 + 3.9, 13.8, 13.8, MAT_WALL, bevel=0.05)
    for i in range(4):  # 五至八层 16.2-31.8
        z0 = 16.2 + i * 3.9
        box("tower_floor%d" % (i + 5), CX, CY, z0, z0 + 3.9, 13.5, 13.5, MAT_WALL, bevel=0.05)

    # ---- 楼层分缝: 每层分界处檐口线脚 + 线脚下暗色缝线 ----
    # (z, 该层楼面半宽): 分界线按下方楼层外廓出挑
    for z, half in ((4.5, 7.0), (8.4, 6.9), (12.3, 6.9), (16.2, 6.9),
                    (20.1, 6.75), (24.0, 6.75), (27.9, 6.75)):
        s = half * 2 + 0.3
        box("tower_cornice_z%s" % z, CX, CY, z - 0.14, z + 0.14, s, s, MAT_BAND, bevel=0.03)
        box("tower_seam_z%s" % z, CX, CY, z - 0.24, z - 0.18,
            half * 2 + 0.06, half * 2 + 0.06, MAT_SEAM, bevel=0.0)
    # 中部转换腰带 (16.2, 收分处加厚)
    box("tower_belt_16p2", CX, CY, 16.08, 16.32, 14.0, 14.0, MAT_BAND, bevel=0.03)
    # 顶层檐口 (31.8, 混凝土色)
    box("tower_cornice_top", CX, CY, 31.71, 31.89, 13.9, 13.9, MAT_CONC, bevel=0.03)

    # ---- 屋顶板 31.8-32.0 (防水卷材纹理) ----
    box("tower_roofslab", CX, CY, 31.8, 32.0, 13.7, 13.7, MAT_ROOF, bevel=0.03)

    # ---- 女儿墙: 32.0-32.57 墙体 + 32.57-32.65 压顶, 厚 0.3 m ----
    # 外廓 = 屋顶板外廓 13.7, 顶面 32.65 = 屋顶板顶面 +0.65
    PW, PD, T = 13.7, 13.7, 0.30
    box("tower_parapet_S", CX, CY - (PD / 2 - T / 2), 32.0, 32.57, PW, T, MAT_CONC, bevel=0.02)
    box("tower_parapet_N", CX, CY + (PD / 2 - T / 2), 32.0, 32.57, PW, T, MAT_CONC, bevel=0.02)
    box("tower_parapet_W", CX - (PW / 2 - T / 2), CY, 32.0, 32.57, T, PD - 2 * T, MAT_CONC, bevel=0.02)
    box("tower_parapet_E", CX + (PW / 2 - T / 2), CY, 32.0, 32.57, T, PD - 2 * T, MAT_CONC, bevel=0.02)
    box("tower_parapet_cap_S", CX, CY - (PD / 2 - T / 2), 32.57, 32.65, PW, T + 0.12, MAT_CONC, bevel=0.02)
    box("tower_parapet_cap_N", CX, CY + (PD / 2 - T / 2), 32.57, 32.65, PW, T + 0.12, MAT_CONC, bevel=0.02)
    box("tower_parapet_cap_W", CX - (PW / 2 - T / 2), CY, 32.57, 32.65, T + 0.12, PD - 2 * T, MAT_CONC, bevel=0.02)
    box("tower_parapet_cap_E", CX + (PW / 2 - T / 2), CY, 32.57, 32.65, T + 0.12, PD - 2 * T, MAT_CONC, bevel=0.02)

    # ---- 屋顶设备小盒 (坐于屋顶板上, 加百叶, 高出女儿墙可读) ----
    box("tower_roof_eq1", CX - 3.5, CY - 2.5, 32.0, 33.0, 2.0, 1.5, MAT_METAL, bevel=0.04)
    box("tower_roof_eq1_lid", CX - 3.5, CY - 2.5, 33.0, 33.12, 2.2, 1.7, MAT_ROOF, bevel=0.02)
    box("tower_roof_eq1_louvre", CX - 3.5, CY - 2.5 - 0.78, 32.35, 32.65, 1.5, 0.05, MAT_GRILLE, bevel=0.0)
    box("tower_roof_eq2", CX + 3.5, CY + 2.5, 32.0, 32.7, 1.6, 1.2, MAT_METAL, bevel=0.04)
    box("tower_roof_eq2_lid", CX + 3.5, CY + 2.5, 32.7, 32.82, 1.8, 1.4, MAT_ROOF, bevel=0.02)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.35, depth=0.8,
                                        location=(CX + 1.0, CY - 3.5, 32.4))
    vent = bpy.context.active_object
    vent.name = "tower_roof_vent"
    vent.data.materials.append(MAT_METAL)
    building.append(vent)

    # ---- 红/粉竖向饰带 (鸟瞰图对照): 分段贴合收分, 略出挑 0.06 ----
    # 南北面: 西侧红带 (x=CX-4.0) + 东侧粉带 (x=CX+4.0), 宽 1.6;
    # 东西面: 居中红带 (宽 1.6)。全高 0.5-31.8, 三段按收分半宽走。
    segs = ((0.5, 4.5, 7.0), (4.5, 16.2, 6.9), (16.2, 31.8, 6.75))
    for si, (z0, z1, half) in enumerate(segs):
        for nm, sgn, dx, mat in (("S_red", -1, -4.0, MAT_RED),
                                 ("S_pink", -1, 4.0, MAT_PINK),
                                 ("N_red", 1, -4.0, MAT_RED),
                                 ("N_pink", 1, 4.0, MAT_PINK)):
            box("tower_accent_%s_seg%d" % (nm, si), CX + dx, CY + sgn * (half + 0.03),
                z0, z1, 1.6, 0.06, mat, bevel=0.0)
        for nm, sgn, mat in (("E_red", 1, MAT_RED), ("W_red", -1, MAT_RED)):
            box("tower_accent_%s_seg%d" % (nm, si), CX + sgn * (half + 0.03), CY,
                z0, z1, 0.06, 1.6, mat, bevel=0.0)

    # ---- 窗带 (SPEC §5: 本件自带简单窗带; 按 v1 做法补回) ----
    # 每层横向窗带 + 竖分格条, 嵌进墙面: 框条出挑 0.07 / 嵌进墙 0.03,
    # 玻璃内凹 (框前 0.08, 墙面内 0.01), 窗台出挑 0.16。
    # 饰带宽 1.6 全高连续: 南北面饰带在 x=CX±4.0 (占 ±3.2~±4.8),
    # 东西面饰带在 y=CY±0.8; 窗带在饰带之间分段, 两侧各留 0.15 缝。
    # 带底 z0+2.05 (空调外机顶 z0+1.51, 不压空调), 带高 1.4,
    # 带顶 z0+3.45 (楼层线脚底 z0+3.76, 不压线脚)。
    BAND_H = 1.4
    n_win = 0

    def win_segment(face, fi, c, w, z0, hw):
        nonlocal n_win
        zb = z0 + 2.05
        zt = zb + BAND_H
        base = "tower_win_F%d_%s_%.2f" % (fi + 1, face, c)
        s = {"S": -1, "N": 1, "W": -1, "E": 1}[face]
        if face in ("S", "N"):
            wall = CY + s * hw
            fy, gy, my, sy = wall + s * 0.02, wall - s * 0.03, wall + s * 0.01, wall + s * 0.06

            def wb(nm, cc, yy, za, zb2, sx, syy, mat):
                return box(nm, cc, yy, za, zb2, sx, syy, mat, bevel=0.0)
        else:
            wall = CX + s * hw
            fx, gx, mx, sx0 = wall + s * 0.02, wall - s * 0.03, wall + s * 0.01, wall + s * 0.06

            def wb(nm, cc, yy, za, zb2, sx, syy, mat):
                # E/W 面: 长度沿 y, 厚度沿 x; 调用时 (cc=厚度坐标, yy=长度坐标,
                # sx=厚度, syy=长度)
                return box(nm, cc, yy, za, zb2, sx, syy, mat, bevel=0.0)

        if face in ("S", "N"):
            wb(base + "_frameB", c, fy, zb, zb + 0.12, w, 0.10, MAT_WIN_FRAME)
            wb(base + "_frameT", c, fy, zt - 0.12, zt, w, 0.10, MAT_WIN_FRAME)
            wb(base + "_frameL", c - (w / 2 - 0.06), fy, zb + 0.12, zt - 0.12, 0.12, 0.10, MAT_WIN_FRAME)
            wb(base + "_frameR", c + (w / 2 - 0.06), fy, zb + 0.12, zt - 0.12, 0.12, 0.10, MAT_WIN_FRAME)
            wb(base + "_glass", c, gy, zb + 0.12, zt - 0.12, w - 0.24, 0.04, MAT_GLASS)
            n_mull = max(1, int(w // 1.5))
            for i in range(n_mull):
                mxp = c - w / 2 + (i + 1) * w / (n_mull + 1)
                wb(base + "_mull%d" % i, mxp, my, zb + 0.12, zt - 0.12, 0.08, 0.06, MAT_WIN_MULLION)
            wb(base + "_sill", c, sy, zb - 0.09, zb, w + 0.12, 0.20, MAT_WIN_SILL)
        else:
            wb(base + "_frameB", fx, c, zb, zb + 0.12, 0.10, w, MAT_WIN_FRAME)
            wb(base + "_frameT", fx, c, zt - 0.12, zt, 0.10, w, MAT_WIN_FRAME)
            wb(base + "_frameL", fx, c - (w / 2 - 0.06), zb + 0.12, zt - 0.12, 0.10, 0.12, MAT_WIN_FRAME)
            wb(base + "_frameR", fx, c + (w / 2 - 0.06), zb + 0.12, zt - 0.12, 0.10, 0.12, MAT_WIN_FRAME)
            wb(base + "_glass", gx, c, zb + 0.12, zt - 0.12, 0.04, w - 0.24, MAT_GLASS)
            n_mull = max(1, int(w // 1.5))
            for i in range(n_mull):
                myp = c - w / 2 + (i + 1) * w / (n_mull + 1)
                wb(base + "_mull%d" % i, mx, myp, zb + 0.12, zt - 0.12, 0.06, 0.08, MAT_WIN_MULLION)
            wb(base + "_sill", sx0, c, zb - 0.09, zb, 0.20, w + 0.12, MAT_WIN_SILL)
        n_win += 6 + n_mull

    win_z0 = [0.5] + [4.5 + i * 3.9 for i in range(7)]
    win_hw = [7.0, 6.9, 6.9, 6.9, 6.75, 6.75, 6.75, 6.75]
    for fi in range(8):
        z0 = win_z0[fi]
        hw = win_hw[fi]
        for face in ("S", "N"):
            win_segment(face, fi, CX - (hw + 4.95) / 2.0, hw - 4.95, z0, hw)
            win_segment(face, fi, CX + (hw + 4.95) / 2.0, hw - 4.95, z0, hw)
            if not (fi == 0 and face == "S"):  # 一层南面正中是正门, 不布窗带
                win_segment(face, fi, CX, 6.1, z0, hw)
        for face in ("E", "W"):
            win_segment(face, fi, CY - (hw + 0.95) / 2.0, hw - 0.95, z0, hw)
            win_segment(face, fi, CY + (hw + 0.95) / 2.0, hw - 0.95, z0, hw)
    print("Window band objects:", n_win)

    # ---- 正门 (南面正中, 一层): 门框 + 双开门扇 + 玻璃 + 门楣 ----
    door_y = CY - 7.0 - 0.02
    box("tower_door_frame", CX, door_y, 0.5, 3.6, 3.0, 0.18, MAT_DOOR, bevel=0.02)
    box("tower_door_L", CX - 0.65, door_y - 0.06, 0.5, 3.4, 1.2, 0.10, MAT_DOOR_GLASS, bevel=0.0)
    box("tower_door_R", CX + 0.65, door_y - 0.06, 0.5, 3.4, 1.2, 0.10, MAT_DOOR_GLASS, bevel=0.0)
    box("tower_door_mullion", CX, door_y - 0.06, 0.5, 3.4, 0.12, 0.12, MAT_DOOR, bevel=0.0)
    box("tower_door_lintel", CX, door_y, 3.6, 3.85, 3.4, 0.22, MAT_BAND, bevel=0.02)

    # ---- 门廊雨棚 + 立柱 + 三级台阶 (南面) ----
    box("tower_entry_canopy", CX, CY - 8.0, 3.4, 3.65, 5.0, 2.0, MAT_CONC, bevel=0.03)
    box("tower_entry_canopy_top", CX, CY - 8.0, 3.65, 3.75, 5.2, 2.2, MAT_ROOF, bevel=0.02)
    box("tower_entry_col_L", CX - 2.1, CY - 8.9, 0.5, 3.4, 0.3, 0.3, MAT_CONC, bevel=0.02)
    box("tower_entry_col_R", CX + 2.1, CY - 8.9, 0.5, 3.4, 0.3, 0.3, MAT_CONC, bevel=0.02)
    box("tower_step_1", CX, CY - 8.3, 0.0, 0.17, 5.4, 3.2, MAT_CONC, bevel=0.02)
    box("tower_step_2", CX, CY - 8.0, 0.17, 0.34, 5.4, 2.6, MAT_CONC, bevel=0.02)
    box("tower_step_3", CX, CY - 7.7, 0.34, 0.5, 5.4, 2.0, MAT_CONC, bevel=0.02)

    # ---- 空调外机: 每层每面 2 台 (共 64 台): 灰盒 + 格栅 + 托架 ----
    def ac_unit(prefix, ux, uy, zc, facing):
        if facing in ("S", "N"):
            gy = uy + (0.15 if facing == "N" else -0.15)
            box(prefix, ux, uy, zc - 0.31, zc + 0.31, 0.9, 0.28, MAT_AC_BODY, bevel=0.02)
            box(prefix + "_grille", ux, gy, zc - 0.22, zc + 0.22, 0.78, 0.03, MAT_GRILLE, bevel=0.0)
            box(prefix + "_bracket", ux, uy, zc - 0.40, zc - 0.34, 0.9, 0.10, MAT_METAL, bevel=0.0)
        else:
            gx = ux + (0.15 if facing == "E" else -0.15)
            box(prefix, ux, uy, zc - 0.31, zc + 0.31, 0.28, 0.9, MAT_AC_BODY, bevel=0.02)
            box(prefix + "_grille", gx, uy, zc - 0.22, zc + 0.22, 0.03, 0.78, MAT_GRILLE, bevel=0.0)
            box(prefix + "_bracket", ux, uy, zc - 0.40, zc - 0.34, 0.10, 0.9, MAT_METAL, bevel=0.0)

    n_ac = 0
    floor_z0 = [0.5] + [4.5 + i * 3.9 for i in range(7)]  # F1..F8
    for fi, z0 in enumerate(floor_z0):
        zc = z0 + 1.2
        hw = 7.0 if fi == 0 else (6.9 if fi < 4 else 6.75)
        # 一层南面有正门 (门框至 x=±1.5), 空调外移到 ±2.5 避开门框与饰带
        s_offs = (-2.5, 2.5) if fi == 0 else (-1.5, 1.5)
        for j, off in enumerate(s_offs):
            ac_unit("tower_ac_F%d_S%d" % (fi + 1, j), CX + off, CY - hw - 0.14, zc, "S")
            ac_unit("tower_ac_F%d_N%d" % (fi + 1, j), CX + off, CY + hw + 0.14, zc, "N")
            n_ac += 2
        for j, off in enumerate((-1.5, 1.5)):
            ac_unit("tower_ac_F%d_E%d" % (fi + 1, j), CX + hw + 0.14, CY + off, zc, "E")
            ac_unit("tower_ac_F%d_W%d" % (fi + 1, j), CX - hw - 0.14, CY + off, zc, "W")
            n_ac += 2
    print("AC outdoor units:", n_ac)

    return building


def save_and_export(building):
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
    print("glb re-import OK, imported objects:", len(imported))
    win_imp = [o for o in imported if "tower_win" in o.name]
    print("glb re-import window objects:", len(win_imp))
    return imported


building = build()
print("built objects:", len(building))

# 反射探针 (Eevee 玻璃反光用; 不进导出选择集, 只留在 .blend 场景里;
# Blender 4.2 里反射探针类型名是 SPHERE; 包一层 try, 探针失败也不许挡存盘/导出)
try:
    bpy.ops.object.lightprobe_add(type="SPHERE", location=(CX, CY, 16.0))
    _probe = bpy.context.active_object
    _probe.name = "tower_reflection_probe"
except Exception as e:
    print("reflection probe skipped:", e)

# ---------- 烘焙程序化纹理为图片 (glTF 无法导出 Noise/Brick/Voronoi) ----------
# 照抄 di-walls 已验证做法: 每种不透明材质选其全部对象 -> Cycles CPU
# samples 4 -> 烘焙 color/rough/normal 三张 1024px 图 (margin 16px) ->
# 重建材质为图片纹理。玻璃材质 (名含 Glass, 如 Glass_Window_9FC3D8 /
# Door_Glass_9FC3D8) 不烘焙, 保持原样。烘焙图在 ov-tower_textures/。
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

TEX_DIR = os.path.join(PY_DIR, "ov-tower_textures")
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

imported = save_and_export(building)
for _ob in imported:
    for _slot in _ob.material_slots:
        _m = _slot.material
        if _m and _m.use_nodes:
            _imgs = [n.image.name for n in _m.node_tree.nodes
                     if n.type == 'TEX_IMAGE' and n.image is not None]
            print("GLB reimport mat:", _ob.name, _m.name, "images:", _imgs)
            if "glass" in _m.name.lower():
                print("  (glass, unbaked by design)")
                continue
            assert len(_imgs) >= 3, "glb material lost baked textures: %s" % _m.name
assert len(imported) == len(building), "glb reimport failed: expected %d objects, got %d" % (len(building), len(imported))

# 清理 .blend1 备份
blend1 = BLEND_PATH + "1"
if os.path.exists(blend1):
    os.remove(blend1)

print("DONE ov-tower")
