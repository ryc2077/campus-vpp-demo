# ov-dorm v2: 宿舍楼 A、B 返工 (overview piece)
# Each 20(x) x 12(y) x 16(z) m, 5 floors.
#   dormA centre Blender (84, -8, 0),  cream wall #F3E9D2 (色值不变)
#   dormB centre Blender (84, -44, 0), blue-grey wall #DFE9F2 (色值不变)
# Both: long axis E-W, no rotation, in a N-S row on the east side.
# v2 返工内容 (筛查结论逐条改, 不改位置/尺寸/朝向/墙色):
# - 墙面: 程序化涂料纹 (Noise 大斑驳 + 竖向雨水渍/墙根加重 + 细颗粒
#   Bump, 粗糙度随斑驳变化); 楼层分缝 (檐口线脚 + 线脚下暗色缝线)。
#   墙色只加深浅变化, 不改色值 (米白与蓝灰在强光下区分淡是色值
#   本身, 已核对, 不擅自改色)。Base Color 全部 sRGB->线性赋值。
# - 楼间绿地: 草地噪波纹理 + 轻微起伏 (顶点置换, 边缘收至 0) +
#   灌木点缀, 不再是平绿板。绿地范围 x 74-94, y -38..-14 (两栋之间)。
# - 女儿墙: 顶面 = 屋顶板顶面 (15.75) + 0.65 = 16.40 m, 厚 0.30 m,
#   混凝土纹 + 压顶略出挑。注: 总高 16.40 m, 比 SPEC §4 的 16 m
#   示意高度高 0.4 m, 按返工任务指令 (屋顶板顶面 +0.65 m) 执行。
# - 空调外机: 每层长边各 4 台 + 短边各 1 台 (每栋 50 台, 共 100 台):
#   灰白机身 + 波纹格栅面板 + 托架, 挂在窗下 (中心 z0+0.55, 顶边
#   仅贴窗台下沿, 不挡窗玻璃)。
# - 屋顶: 深灰防水卷材纹理 (Brick 搭接缝 + Noise 颗粒 + Bump),
#   不再是深灰平板。
# - 正门: 西立面 (朝校园内侧) 正门 + 门廊雨棚 (2 根柱) + 3 级台阶。
# - 全部结构件带小倒角 (薄件: 缝线/格栅/托架除外)。
# - 分件边界: 窗带归本件 (SPEC.md 第 70 行: 宿舍 A、B 两栋
#   “带简单窗带”, 归属栏“本件自带简单窗带”; ov-windows-roofs
#   只做 A/B/C 三栋的窗, 不碰宿舍窗)。窗带做法: 每层横向通长
#   玻璃带 + 框 + 竖挺 + 窗台, 玻璃嵌在框面之后 0.04 m (内凹读感),
#   玻璃淡蓝灰半透明 + 高镜面反射 + 粗糙度变化, 不是平蓝板;
#   窗框/竖挺/窗台三个材质分开, 粗糙度/Bump 各有变化。
# - 不渲染: 本地一张图都不渲染 (用户新规矩, 渲染走 GitHub Actions)。
#   本脚本只做 建模 -> 存 .blend -> 导出 .glb -> 回读确认。
#
# Height envelope (v1 结论保留): plinth 0-0.5, F1 0.5-4.0 (3.5 m),
# F2-F5 3.0 m each (4.0-7.0-10.0-13.0-16.0). Top floor body ends at
# 15.7, roof slab is its dark top slice, raised 0.05 m to 15.75 so its
# top face is NOT coplanar with the body top face (coplanar faces
# z-fight and the roof renders white with dark stripes -- seen in the
# first preview). F5 is inset 0.3 m per side (收分); cornice bands at
# each floor line.

import bpy
import math
import os
import random
from mathutils import Vector

PIECE = "ov-dorm"
BASE = os.path.expanduser("~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
PY_DIR = os.path.join(BASE, "assets/blender/overview")
BLEND_PATH = os.path.join(PY_DIR, "ov-dorm.blend")
GLB_PATH = os.path.join(BASE, "assets/models/ov-dorm.glb")

W, D = 20.0, 12.0      # footprint x, y
MID = (84.0, -26.0)    # midpoint of the two buildings


def hex_rgb(h):
    """Hex sRGB -> linear RGB (Blender stores Base Color linear; assigning
    raw sRGB values would wash every colour out)."""
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


def wall_mat(name, base, mottle_stops, stain_hex):
    """涂料墙: 大尺度斑驳 + 竖向雨水渍 (墙根加重) + 细颗粒 Bump.
    色值只加深浅变化, 不改 base 色。"""
    m, bsdf = _new_mat(name, base, 0.85)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    # 大斑驳: Object 坐标米制, Noise 尺度 0.35 -> 约 3 m 一块深浅
    n1 = _noise(nt, "Mottle", 0.35, detail=3, rough=0.7)
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    ramp1 = _ramp(nt, "MottleRamp", mottle_stops)
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
    mix.inputs["Color2"].default_value = hex_rgb(stain_hex)
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
    """檐口/线脚/雨棚: 浅色铺装色, 轻微斑驳."""
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


def win_frame_mat():
    """窗框: 米白 UPVC, 轻微斑驳 + 细 Bump."""
    m, bsdf = _new_mat("WinFrame_E9E9E6_tex", "#E9E9E6", 0.55)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n1 = _noise(nt, "Mottle", 2.0, detail=2, rough=0.8)
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    ramp1 = _ramp(nt, "MottleRamp", [(0.0, "#DCDCD6"), (0.5, "#E9E9E6"), (1.0, "#F4F4F0")])
    nt.links.new(n1.outputs["Fac"], ramp1.inputs["Fac"])
    nt.links.new(ramp1.outputs["Color"], bsdf.inputs["Base Color"])
    b = _bump(nt, n1.outputs["Fac"], strength=0.2, distance=0.03)
    nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def win_mullion_mat():
    """竖挺: 浅灰金属, 粗糙度低一点 + 细颗粒 Bump, 与窗框区分开."""
    m, bsdf = _new_mat("WinMullion_C9CDD0_tex", "#C9CDD0", 0.45, 0.2)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n1 = _noise(nt, "Grain", 4.0, detail=2, rough=0.8)
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    b = _bump(nt, n1.outputs["Fac"], strength=0.15, distance=0.02)
    nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def win_sill_mat():
    """窗台: 浅灰石材, 斑驳 + 颗粒 Bump, 与窗框/竖挺区分开."""
    m, bsdf = _new_mat("WinSill_CFC8B8_tex", "#CFC8B8", 0.9)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n1 = _noise(nt, "Mottle", 1.0, detail=3, rough=0.7)
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    ramp1 = _ramp(nt, "MottleRamp", [(0.0, "#BDB5A2"), (0.5, "#CFC8B8"), (1.0, "#DDD6C6")])
    nt.links.new(n1.outputs["Fac"], ramp1.inputs["Fac"])
    nt.links.new(ramp1.outputs["Color"], bsdf.inputs["Base Color"])
    n2 = _noise(nt, "Grain", 3.0, detail=2, rough=0.8)
    nt.links.new(tc.outputs["Object"], n2.inputs["Vector"])
    b = _bump(nt, n2.outputs["Fac"], strength=0.4, distance=0.05)
    nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def win_glass_mat():
    """窗玻璃: 淡蓝灰半透明 + 高镜面反射 + 粗糙度变化, 不是平蓝板.
    Alpha 0.72 (BLENDED), Specular IOR Level 1.0, Noise 斑驳调色 +
    粗糙度 0.08~0.25 变化。"""
    m, bsdf = _new_mat("WinGlass_9FC3D8_tex", "#9FC3D8", 0.15)
    nt = m.node_tree
    bsdf.inputs["Alpha"].default_value = 0.72
    bsdf.inputs["Specular IOR Level"].default_value = 1.0
    try:
        m.surface_render_method = "BLENDED"
    except Exception:
        pass
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n1 = _noise(nt, "Mottle", 0.8, detail=3, rough=0.7)
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    ramp1 = _ramp(nt, "MottleRamp", [(0.0, "#8FB4C8"), (0.5, "#9FC3D8"), (1.0, "#B7D4E2")])
    nt.links.new(n1.outputs["Fac"], ramp1.inputs["Fac"])
    nt.links.new(ramp1.outputs["Color"], bsdf.inputs["Base Color"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.3
    mr.inputs["From Max"].default_value = 0.7
    mr.inputs["To Min"].default_value = 0.08
    mr.inputs["To Max"].default_value = 0.25
    nt.links.new(n1.outputs["Fac"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])
    return m


def grass_mat():
    """楼间草地: 两档绿噪波 + 细颗粒 Bump, 不再是平绿板."""
    m, bsdf = _new_mat("Lawn_Grass_69B45E_tex", "#69B45E", 1.0)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n1 = _noise(nt, "Patches", 0.45, detail=3, rough=0.7)
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    ramp1 = _ramp(nt, "PatchRamp",
                   [(0.0, "#4E9A44"), (0.45, "#69B45E"), (1.0, "#7FC46A")])
    nt.links.new(n1.outputs["Fac"], ramp1.inputs["Fac"])
    # 细草叶颗粒: 高频 Noise 叠加, 压暗/提亮交错
    n2 = _noise(nt, "Blades", 6.0, detail=2, rough=0.85)
    nt.links.new(tc.outputs["Object"], n2.inputs["Vector"])
    ramp2 = _ramp(nt, "BladeRamp", [(0.0, "#000000"), (0.5, "#000000"), (1.0, "#FFFFFF")])
    ramp2.color_ramp.elements[0].color = (0, 0, 0, 1)
    ramp2.color_ramp.elements[1].color = (0, 0, 0, 1)
    ramp2.color_ramp.elements[2].color = (1, 1, 1, 1)
    nt.links.new(n2.outputs["Fac"], ramp2.inputs["Fac"])
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "OVERLAY"
    mix.inputs["Fac"].default_value = 0.35
    nt.links.new(ramp1.outputs["Color"], mix.inputs["Color1"])
    nt.links.new(ramp2.outputs["Color"], mix.inputs["Color2"])
    nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    b = _bump(nt, n2.outputs["Fac"], strength=0.6, distance=0.04)
    nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def bush_mat():
    """灌木: 深绿斑驳 + 颗粒 Bump."""
    m, bsdf = _new_mat("Bush_Green_4A8F43_tex", "#4A8F43", 1.0)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n1 = _noise(nt, "Mottle", 1.2, detail=3, rough=0.75)
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    ramp1 = _ramp(nt, "MottleRamp", [(0.0, "#356E30"), (0.5, "#4A8F43"), (1.0, "#5FA354")])
    nt.links.new(n1.outputs["Fac"], ramp1.inputs["Fac"])
    nt.links.new(ramp1.outputs["Color"], bsdf.inputs["Base Color"])
    b = _bump(nt, n1.outputs["Fac"], strength=0.5, distance=0.05)
    nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    return m


MAT_WALL_A = wall_mat("Wall_Cream_F3E9D2_tex", "#F3E9D2",
                      [(0.0, "#E0CFAB"), (0.5, "#F3E9D2"), (1.0, "#FAF2DE")],
                      "#D3C096")
MAT_WALL_B = wall_mat("Wall_BlueGrey_DFE9F2_tex", "#DFE9F2",
                      [(0.0, "#C3D2DE"), (0.5, "#DFE9F2"), (1.0, "#EDF3F8")],
                      "#AFC4D2")
MAT_ROOF = roof_mat()
MAT_CONC = conc_mat()
MAT_BAND = band_mat()
MAT_METAL = metal_mat()
MAT_AC_BODY = metal_mat("#D5D9DC", "AC_Body_D5D9DC", 0.5, 0.25)
MAT_GRILLE = grille_mat()
MAT_SEAM = _new_mat("FloorSeam_B7A988", "#B7A988", 0.9)[0]
MAT_DOOR = _new_mat("Door_Dark_424A52", "#424A52", 0.8)[0]
MAT_WIN_FRAME = win_frame_mat()
MAT_WIN_MULLION = win_mullion_mat()
MAT_WIN_SILL = win_sill_mat()
MAT_WIN_GLASS = win_glass_mat()
MAT_GRASS = grass_mat()
MAT_BUSH = bush_mat()

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


def window_band(tag, fi, cx, cy, zc, hw, hd):
    """每层横向窗带: 玻璃带 + 框 (上下横档 + 两侧竖框, 非整块板,
    否则会盖住玻璃) + 竖挺 + 窗台。框/挺外表面比玻璃外表面出 0.04 m,
    玻璃读作内凹。长边 6 扇 (竖挺 5 根), 短边 2 扇 (竖挺 1 根)。
    hw/hd: 该层墙面半宽/半深 (F5 收分层用 9.7/5.7, 其余 10.0/6.0)。"""
    # ---- long faces (S/N): band along x ----
    for sgn, side in ((-1, "S"), (1, "N")):
        # top / bottom rails: 17.6 long, 0.10 high, front at hd+0.06
        box("%s_winband_F%d_%s_railT" % (tag, fi, side), cx, cy + sgn * (hd + 0.01),
            zc + 0.75, zc + 0.85, 17.6, 0.10, MAT_WIN_FRAME, bevel=0.02)
        box("%s_winband_F%d_%s_railB" % (tag, fi, side), cx, cy + sgn * (hd + 0.01),
            zc - 0.85, zc - 0.75, 17.6, 0.10, MAT_WIN_FRAME, bevel=0.02)
        # side stiles: 0.30 wide, 1.7 high
        for s in (-1, 1):
            box("%s_winband_F%d_%s_stile%d" % (tag, fi, side, s),
                cx + s * 8.65, cy + sgn * (hd + 0.01), zc - 0.85, zc + 0.85,
                0.30, 0.10, MAT_WIN_FRAME, bevel=0.02)
        # glass band: 17.0 x 1.5, front 0.04 behind frame front (内凹)
        box("%s_winband_F%d_%s_glass" % (tag, fi, side), cx, cy + sgn * (hd - 0.01),
            zc - 0.75, zc + 0.75, 17.0, 0.06, MAT_WIN_GLASS, bevel=0.0)
        # mullions: 5, at window midpoints, front flush with frame front
        for j, off in enumerate((-5.67, -2.83, 0.0, 2.83, 5.67)):
            box("%s_winband_F%d_%s_mull%d" % (tag, fi, side, j),
                cx + off, cy + sgn * (hd + 0.02), zc - 0.75, zc + 0.75,
                0.08, 0.08, MAT_WIN_MULLION, bevel=0.0)
        # sill: ledge below bottom rail, proud 0.13
        box("%s_winband_F%d_%s_sill" % (tag, fi, side), cx, cy + sgn * (hd + 0.05),
            zc - 0.93, zc - 0.85, 17.8, 0.16, MAT_WIN_SILL, bevel=0.0)
    # ---- short faces (W/E): band along y ----
    for sgn, side in ((-1, "W"), (1, "E")):
        box("%s_winband_F%d_%s_railT" % (tag, fi, side), cx + sgn * (hw + 0.01), cy,
            zc + 0.75, zc + 0.85, 0.10, 9.0, MAT_WIN_FRAME, bevel=0.02)
        box("%s_winband_F%d_%s_railB" % (tag, fi, side), cx + sgn * (hw + 0.01), cy,
            zc - 0.85, zc - 0.75, 0.10, 9.0, MAT_WIN_FRAME, bevel=0.02)
        for s in (-1, 1):
            box("%s_winband_F%d_%s_stile%d" % (tag, fi, side, s),
                cx + sgn * (hw + 0.01), cy + s * 4.35, zc - 0.85, zc + 0.85,
                0.10, 0.30, MAT_WIN_FRAME, bevel=0.02)
        box("%s_winband_F%d_%s_glass" % (tag, fi, side), cx + sgn * (hw - 0.01), cy,
            zc - 0.75, zc + 0.75, 0.06, 8.4, MAT_WIN_GLASS, bevel=0.0)
        box("%s_winband_F%d_%s_mull0" % (tag, fi, side),
            cx + sgn * (hw + 0.02), cy, zc - 0.75, zc + 0.75,
            0.08, 0.08, MAT_WIN_MULLION, bevel=0.0)
        box("%s_winband_F%d_%s_sill" % (tag, fi, side), cx + sgn * (hw + 0.05), cy,
            zc - 0.93, zc - 0.85, 0.16, 9.2, MAT_WIN_SILL, bevel=0.0)


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


def build_dorm(tag, cx, cy, mat_wall):
    # ---- plinth (0-0.5) + cap ----
    box(tag + "_plinth", cx, cy, 0.0, 0.5, W + 0.6, D + 0.6, MAT_CONC, bevel=0.04)
    box(tag + "_plinth_cap", cx, cy, 0.5, 0.66, W + 0.7, D + 0.7, MAT_BAND, bevel=0.03)
    # ---- main body F1-F4 (0.5-13.0) ----
    box(tag + "_body_F1_F4", cx, cy, 0.5, 13.0, W, D, mat_wall, bevel=0.06)
    # ---- top floor, inset 0.3 m per side (13.0-15.7) ----
    box(tag + "_body_F5_inset", cx, cy, 13.0, 15.7, W - 0.6, D - 0.6, mat_wall, bevel=0.06)
    # ---- floor cornice bands (檐口线脚) + dark seam groove just below ----
    for i, zc in enumerate((4.0, 7.0, 10.0, 13.0)):
        box("%s_cornice_F%d" % (tag, i + 2), cx, cy, zc - 0.14, zc + 0.14,
            W + 0.3, D + 0.3, MAT_BAND, bevel=0.03)
        box("%s_seam_F%d" % (tag, i + 2), cx, cy, zc - 0.24, zc - 0.18,
            W + 0.06, D + 0.06, MAT_SEAM, bevel=0.0)
    # ---- roof slab: dark top slice of top floor (15.55-15.75, inset) ----
    box(tag + "_roof_slab", cx, cy, 15.55, 15.75, W - 1.0, D - 1.0, MAT_ROOF, bevel=0.03)
    # ---- parapet (女儿墙): wall 15.7-16.32 + cap 16.32-16.40, 厚 0.30 m ----
    # 顶面 16.40 = 屋顶板顶面 15.75 + 0.65 (按返工任务指令)
    PW, PD = W - 0.6, D - 0.6
    T = 0.30
    box(tag + "_parapet_S", cx, cy - (PD / 2 - T / 2), 15.7, 16.32, PW, T, MAT_CONC, bevel=0.02)
    box(tag + "_parapet_N", cx, cy + (PD / 2 - T / 2), 15.7, 16.32, PW, T, MAT_CONC, bevel=0.02)
    box(tag + "_parapet_W", cx - (PW / 2 - T / 2), cy, 15.7, 16.32, T, PD - 2 * T, MAT_CONC, bevel=0.02)
    box(tag + "_parapet_E", cx + (PW / 2 - T / 2), cy, 15.7, 16.32, T, PD - 2 * T, MAT_CONC, bevel=0.02)
    box(tag + "_parapet_cap_S", cx, cy - (PD / 2 - T / 2), 16.32, 16.40, PW, T + 0.12, MAT_CONC, bevel=0.02)
    box(tag + "_parapet_cap_N", cx, cy + (PD / 2 - T / 2), 16.32, 16.40, PW, T + 0.12, MAT_CONC, bevel=0.02)
    box(tag + "_parapet_cap_W", cx - (PW / 2 - T / 2), cy, 16.32, 16.40, T + 0.12, PD - 2 * T, MAT_CONC, bevel=0.02)
    box(tag + "_parapet_cap_E", cx + (PW / 2 - T / 2), cy, 16.32, 16.40, T + 0.12, PD - 2 * T, MAT_CONC, bevel=0.02)
    # ---- roof equipment box: tall enough to read over the parapet + louvres ----
    ex, ey = cx - 5.0, cy + 2.0
    box(tag + "_roof_equip", ex, ey, 15.75, 17.10, 2.2, 1.6, MAT_METAL, bevel=0.04)
    box(tag + "_roof_equip_lid", ex, ey, 17.10, 17.22, 2.4, 1.8, MAT_ROOF, bevel=0.02)
    for k, zl in enumerate((16.35, 16.65, 16.95)):
        box("%s_roof_equip_louvre_%d" % (tag, k), ex, ey - 0.82,
            zl - 0.06, zl + 0.06, 1.7, 0.05, MAT_GRILLE, bevel=0.0)
    # ---- AC outdoor units: per floor, long sides 4 each + short sides 1 each
    # floor z0s: F1 0.5, F2 4.0, F3 7.0, F4 10.0, F5 13.0; unit centre z0+0.55
    # (under the window sill, top edge just meets the sill line)
    # F5 inset faces: half-width 9.7 / half-depth 5.7; F1-F4: 10.0 / 6.0
    n_ac = 0
    for fi, z0 in enumerate((0.5, 4.0, 7.0, 10.0, 13.0)):
        zc = z0 + 0.55
        hw = 9.7 if fi == 4 else 10.0
        hd = 5.7 if fi == 4 else 6.0
        for j, off in enumerate((-7.5, -2.5, 2.5, 7.5)):
            ac_unit("%s_ac_F%d_S%d" % (tag, fi + 1, j), cx + off, cy - hd - 0.14, zc, "S")
            ac_unit("%s_ac_F%d_N%d" % (tag, fi + 1, j), cx + off, cy + hd + 0.14, zc, "N")
            n_ac += 2
        ac_unit("%s_ac_F%d_E0" % (tag, fi + 1), cx + hw + 0.14, cy, zc, "E")
        ac_unit("%s_ac_F%d_W0" % (tag, fi + 1), cx - hw - 0.14, cy, zc, "W")
        n_ac += 2
    print(tag, "AC outdoor units:", n_ac)
    # ---- window bands: one horizontal band per floor, all four faces ----
    # band centres z0+1.75: F1 2.25, F2 5.75, F3 8.75, F4 11.75, F5 14.75.
    # Band bottom (z0+1.0) clears the AC top (z0+0.86) by 0.14 m.
    for fi, zc in enumerate((2.25, 5.75, 8.75, 11.75, 14.75)):
        hw = 9.7 if fi == 4 else 10.0
        hd = 5.7 if fi == 4 else 6.0
        window_band(tag, fi + 1, cx, cy, zc, hw, hd)
    # ---- entrance: west face (towards campus interior), F1 centre ----
    # door + canopy slab + 2 posts + 3 steps down to ground
    box(tag + "_door", cx - (W / 2 + 0.02), cy, 0.5, 2.9, 0.14, 1.8, MAT_DOOR, bevel=0.0)
    box(tag + "_canopy", cx - (W / 2 + 0.7), cy, 3.0, 3.16, 1.5, 3.4, MAT_BAND, bevel=0.03)
    for sgn in (-1, 1):
        box("%s_canopy_post_%s" % (tag, "S" if sgn < 0 else "N"),
            cx - (W / 2 + 0.5), cy + sgn * 1.5, 0.5, 3.0, 0.12, 0.12,
            MAT_METAL, bevel=0.0)
    # steps: from plinth face (x = cx-10.3) down westward, 0.35 deep each
    box(tag + "_step_1", cx - (W / 2 + 0.475), cy, 0.34, 0.5, 0.35, 2.8, MAT_CONC, bevel=0.02)
    box(tag + "_step_2", cx - (W / 2 + 0.825), cy, 0.17, 0.34, 0.35, 2.8, MAT_CONC, bevel=0.02)
    box(tag + "_step_3", cx - (W / 2 + 1.175), cy, 0.0, 0.17, 0.35, 2.8, MAT_CONC, bevel=0.02)


build_dorm("dormA", 84.0, -8.0, MAT_WALL_A)
build_dorm("dormB", 84.0, -44.0, MAT_WALL_B)

# ---- inter-building lawn: textured + gently undulating, NOT a flat board ----
# strip x 74-94, y -38..-14 (between the two dorms), base z +0.02,
# grid 24x28 verts displaced by deterministic sine noise, edges taper to 0.
bpy.ops.mesh.primitive_grid_add(x_subdivisions=24, y_subdivisions=28, size=2.0,
                                location=(MID[0], MID[1], 0.02))
lawn = bpy.context.active_object
lawn.name = "dorm_lawn_between"
lawn.dimensions = (20.0, 24.0, 0.0)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
for v in lawn.data.vertices:
    lx, ly = v.co.x, v.co.y  # local: x in [-10, 10], y in [-12, 12]
    edge = max(0.0, (1.0 - (lx / 10.0) ** 2) * (1.0 - (ly / 12.0) ** 2))
    # 起伏 0~0.24 m (基值 0.12 保证全程不低于地面 z=0, 边缘收至 0.02)
    v.co.z = 0.02 + edge * (0.12 + 0.07 * math.sin(lx * 0.9) * math.cos(ly * 0.7)
                            + 0.05 * math.sin(lx * 2.3 + ly * 1.7))
lawn.data.materials.append(MAT_GRASS)
building.append(lawn)

# ---- shrubs dotted on the lawn (deterministic layout, seed 7) ----
rng = random.Random(7)
n_bush = 0
for i in range(14):
    bx = MID[0] + rng.uniform(-8.5, 8.5)
    by = MID[1] + rng.uniform(-10.5, 10.5)
    # keep the middle walkway (y near -26, x 82-86) clear-ish: skip centre band
    if abs(bx - 84.0) < 1.6 and abs(by + 26.0) < 3.0:
        continue
    r = rng.uniform(0.45, 0.75)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0,
                                          location=(bx, by, r * 0.55))
    b = bpy.context.active_object
    b.name = "dorm_bush_%02d" % i
    b.scale = (r, r, r * 0.62)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    b.data.materials.append(MAT_BUSH)
    building.append(b)
    n_bush += 1
print("shrubs:", n_bush)

# ---------- 烘焙程序化纹理为图片 (glTF 无法导出 Noise/Brick/Voronoi) ----------
# 照抄 di-walls 已验证做法: 每种不透明材质选其全部对象 -> Cycles CPU
# samples 4 -> 烘焙 color/rough/normal 三张 1024px 图 (margin 16px) ->
# 重建材质为图片纹理。玻璃材质 (WinGlass_9FC3D8_tex) 不烘焙, 保持原样。
# 烘焙图在 ov-dorm_textures/。
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

TEX_DIR = os.path.join(PY_DIR, "ov-dorm_textures")
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

# ---- save .blend FIRST (crash safety: results on disk before export) ----
os.makedirs(PY_DIR, exist_ok=True)
os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("saved blend:", BLEND_PATH, "objects:", len(building))

# ---- export .glb (building objects only) ----
bpy.ops.object.select_all(action="DESELECT")
for o in building:
    o.select_set(True)
bpy.context.view_layer.objects.active = building[0]
bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format="GLB",
                           use_selection=True, export_apply=True)
print("exported glb:", GLB_PATH, "objects:", len(building))

# ---- read back the .glb to confirm it opens ----
bpy.ops.object.select_all(action="DESELECT")
bpy.ops.import_scene.gltf(filepath=GLB_PATH)
imported = [o for o in bpy.context.selected_objects]
print("glb re-import OK, imported objects:", len(imported))
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

print("DONE ov-dorm")
