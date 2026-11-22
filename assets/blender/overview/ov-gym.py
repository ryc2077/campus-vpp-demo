# ov-gym v2: 艺体馆楼体 (overview) — 返工版
# 36(x) x 16(y) x 18(z) m, 3 层, 中心 Blender (-70, 60, 0)
# 红墙 #8E2F28 + 深灰屋顶 #424A52 + 女儿墙, 带简单窗带
# 层高: 基座 0-0.5 / 一层大厅 0.5-8.5 / 二层 8.5-13.0 / 三层 13.0-17.5
#       屋顶板 17.5-17.8 / 女儿墙顶 18.0
# v2 改动: 红墙 Brick+Noise 纹理/Bump; 玻璃 Principled/Glass 混合+窗框/竖挺/窗台
#         +SSR+楼前 Reflection Cubemap; 雨棚加厚/柱加粗+柱础; 正门玻璃门+门框;
#         屋顶 Noise 防水层+设备盒百叶; 地面混凝土纹 (Noise+Voronoi+Bump)
# 2026-11-22 晚: 本地渲染停用, 预览改走 GitHub Actions; 本脚本只建模/存盘/导出/回读验证, 不渲染。
import bpy
import math
import os
from mathutils import Vector

ITEM = "ov-gym"
CX, CY = -70.0, 60.0

BASE = os.path.expanduser("~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
BLEND_PATH = os.path.join(BASE, "assets/blender/overview/ov-gym.blend")
GLB_PATH = os.path.join(BASE, "assets/models/ov-gym.glb")
PNG_PATH = os.path.join(BASE, "screenshots/blender/ov-gym.png")
for p in (BLEND_PATH, GLB_PATH, PNG_PATH):
    os.makedirs(os.path.dirname(p), exist_ok=True)

# ---------- clean scene ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

# ---------- color helpers (sRGB hex -> linear) ----------
def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def hex_lin(h):
    h = h.lstrip("#")
    r = int(h[0:2], 16) / 255.0
    g = int(h[2:4], 16) / 255.0
    b = int(h[4:6], 16) / 255.0
    return (srgb_to_linear(r), srgb_to_linear(g), srgb_to_linear(b), 1.0)

def set_in(node, name, val):
    try:
        node.inputs[name].default_value = val
    except Exception:
        pass

def ramp_stops(ramp, stops):
    els = ramp.color_ramp.elements
    while len(els) > len(stops):
        ramp.color_ramp.elements.remove(els[-1])
    while len(els) < len(stops):
        els.new(0.5)
    for el, (pos, col) in zip(els, stops):
        el.position = pos
        el.color = hex_lin(col) if isinstance(col, str) else col

def new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    return m, nt

def principled(m):
    return m.node_tree.nodes["Principled BSDF"]

def make_plain(name, hexcolor, roughness=0.85, metallic=0.0):
    m, nt = new_mat(name)
    bsdf = principled(m)
    bsdf.inputs["Base Color"].default_value = hex_lin(hexcolor)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return m

# ---------- 红墙: Brick Texture + Noise 深浅不均 + Bump ----------
def make_brick_wall(name, c1, c2, mortar):
    m, nt = new_mat(name)
    nodes, links = nt.nodes, nt.links
    bsdf = principled(m)
    tc = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (1.0, 1.0, 1.0)
    brick = nodes.new("ShaderNodeTexBrick")
    set_in(brick, "Color1", hex_lin(c1))
    set_in(brick, "Color2", hex_lin(c2))
    set_in(brick, "Mortar", hex_lin(mortar))
    set_in(brick, "Scale", 2.0)
    set_in(brick, "Mortar Size", 0.02)
    set_in(brick, "Mortar Thickness", 0.06)
    set_in(brick, "Brick Width", 0.5)
    set_in(brick, "Row Height", 0.5)
    set_in(brick, "Bias", 0.0)
    noise = nodes.new("ShaderNodeTexNoise")
    set_in(noise, "Scale", 6.0)
    set_in(noise, "Detail", 3.0)
    set_in(noise, "Roughness", 0.7)
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp_stops(ramp, [(0.30, (0.0, 0.0, 0.0, 1.0)), (0.70, (0.45, 0.45, 0.45, 1.0))])
    mix = nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MIX"
    set_in(mix, "Color2", hex_lin("#5E1F19"))
    bump = nodes.new("ShaderNodeBump")
    set_in(bump, "Strength", 0.4)
    set_in(bump, "Distance", 0.08)
    links.new(tc.outputs["Object"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], brick.inputs["Vector"])
    links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    links.new(brick.outputs["Color"], mix.inputs["Color1"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], mix.inputs["Fac"])
    links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = 0.85
    return m

MAT_WALL = make_brick_wall("ov-gym_wall_red", "#8E2F28", "#7E2A23", "#5C1F1A")
MAT_WALL2 = make_brick_wall("ov-gym_wall_red_dark", "#7A2822", "#68211C", "#4E1B16")
MAT_ROOF = None
MAT_CONC = make_plain("ov-gym_concrete", "#B9B3A8", 0.95)

# ---------- 屋顶: Noise 防水层纹 + Bump ----------
def make_roof_mat():
    m, nt = new_mat("ov-gym_roof_dark")
    nodes, links = nt.nodes, nt.links
    bsdf = principled(m)
    tc = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    noise = nodes.new("ShaderNodeTexNoise")
    set_in(noise, "Scale", 3.0)
    set_in(noise, "Detail", 3.0)
    set_in(noise, "Roughness", 0.75)
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp_stops(ramp, [(0.30, "#33393F"), (0.70, "#4E565E")])
    bump = nodes.new("ShaderNodeBump")
    set_in(bump, "Strength", 0.6)
    set_in(bump, "Distance", 0.10)
    links.new(tc.outputs["Object"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = 0.9
    return m
MAT_ROOF = make_roof_mat()

# ---------- 地面/饰面混凝土: Noise + Voronoi 斑点 + Bump ----------
def make_concrete_tex(name):
    m, nt = new_mat(name)
    nodes, links = nt.nodes, nt.links
    bsdf = principled(m)
    tc = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    noise = nodes.new("ShaderNodeTexNoise")
    set_in(noise, "Scale", 4.0)
    set_in(noise, "Detail", 3.0)
    set_in(noise, "Roughness", 0.7)
    nramp = nodes.new("ShaderNodeValToRGB")
    ramp_stops(nramp, [(0.35, "#A29C8E"), (0.65, "#C9C3B6")])
    vor = nodes.new("ShaderNodeTexVoronoi")
    set_in(vor, "Scale", 12.0)
    set_in(vor, "Detail", 0.0)
    set_in(vor, "Feature", "F1")
    vramp = nodes.new("ShaderNodeValToRGB")
    ramp_stops(vramp, [(0.00, "#8F897D"), (0.18, "#C2BCB0"), (1.00, "#C2BCB0")])
    mix = nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MIX"
    mix.inputs["Fac"].default_value = 0.5
    bump = nodes.new("ShaderNodeBump")
    set_in(bump, "Strength", 0.4)
    set_in(bump, "Distance", 0.08)
    links.new(tc.outputs["Object"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    links.new(mapping.outputs["Vector"], vor.inputs["Vector"])
    links.new(noise.outputs["Fac"], nramp.inputs["Fac"])
    links.new(vor.outputs["Distance"], vramp.inputs["Fac"])
    links.new(nramp.outputs["Color"], mix.inputs["Color1"])
    links.new(vramp.outputs["Color"], mix.inputs["Color2"])
    links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = 0.95
    return m
MAT_CONC_TEX = make_concrete_tex("ov-gym_concrete_tex")

# ---------- 金属灰 (窗框/门框): 轻微 Noise 粗糙度变化 ----------
def make_metal_mat():
    m, nt = new_mat("ov-gym_metal")
    nodes, links = nt.nodes, nt.links
    bsdf = principled(m)
    bsdf.inputs["Base Color"].default_value = hex_lin("#8A8F94")
    bsdf.inputs["Metallic"].default_value = 0.65
    tc = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    set_in(noise, "Scale", 10.0)
    set_in(noise, "Detail", 2.0)
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp_stops(ramp, [(0.30, (0.35, 0.35, 0.35, 1.0)), (0.70, (0.60, 0.60, 0.60, 1.0))])
    links.new(tc.outputs["Object"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Roughness"])
    return m
MAT_METAL = make_metal_mat()
MAT_METAL_DARK = make_plain("ov-gym_metal_dark", "#424A52", 0.6, 0.5)

# ---------- 玻璃: Principled / Glass 混合, 低粗糙度 + Noise 粗糙度变化, 淡蓝灰 ----------
def make_glass_mat():
    m, nt = new_mat("ov-gym_glass")
    nodes, links = nt.nodes, nt.links
    out = nt.nodes["Material Output"]
    bsdf = principled(m)
    bsdf.inputs["Base Color"].default_value = hex_lin("#A9C6D6")
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Transmission Weight"].default_value = 0.15
    set_in(bsdf, "IOR", 1.45)
    try:
        bsdf.inputs["Specular IOR Level"].default_value = 1.0
    except Exception:
        pass
    tc = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    set_in(noise, "Scale", 5.0)
    set_in(noise, "Detail", 3.0)
    set_in(noise, "Roughness", 0.7)
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp_stops(ramp, [(0.30, (0.05, 0.05, 0.05, 1.0)), (0.70, (0.22, 0.22, 0.22, 1.0))])
    bump = nodes.new("ShaderNodeBump")
    set_in(bump, "Strength", 0.15)
    set_in(bump, "Distance", 0.05)
    glass = nodes.new("ShaderNodeBsdfGlass")
    set_in(glass, "Color", hex_lin("#C2DCEA"))
    set_in(glass, "Roughness", 0.06)
    set_in(glass, "IOR", 1.45)
    mix = nodes.new("ShaderNodeMixShader")
    mix.inputs[0].default_value = 0.40
    links.new(tc.outputs["Object"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Roughness"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    links.new(bump.outputs["Normal"], glass.inputs["Normal"])
    links.new(glass.outputs["BSDF"], mix.inputs[1])
    links.new(bsdf.outputs["BSDF"], mix.inputs[2])
    links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return m
MAT_GLASS = make_glass_mat()

objs = []

def box(name, cx, cy, z0, z1, sx, sy, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=(cx, cy, (z0 + z1) / 2.0))
    o = bpy.context.active_object
    o.name = name
    o.dimensions = (sx, sy, z1 - z0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0:
        mod = o.modifiers.new("bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 1
    if mat:
        o.data.materials.append(mat)
    objs.append(o)
    return o

# ---------- ground apron 地面 (混凝土纹, 48x28, 顶面 z=0) ----------
box("ov-gym_ground", CX, CY, -0.2, 0.0, 48.0, 28.0, MAT_CONC_TEX, bevel=0.02)

# ---------- masses (setback per floor + cornice lines) ----------
box("ov-gym_plinth", CX, CY, 0.0, 0.5, 36.6, 16.6, MAT_CONC_TEX, bevel=0.05)
box("ov-gym_floor1", CX, CY, 0.5, 8.5, 36.0, 16.0, MAT_WALL, bevel=0.08)
box("ov-gym_cornice1", CX, CY, 8.5, 8.8, 36.5, 16.5, MAT_CONC_TEX, bevel=0.04)
box("ov-gym_floor2", CX, CY, 8.8, 13.0, 35.4, 15.4, MAT_WALL, bevel=0.08)
box("ov-gym_cornice2", CX, CY, 13.0, 13.3, 35.9, 15.9, MAT_CONC_TEX, bevel=0.04)
box("ov-gym_floor3", CX, CY, 13.3, 17.5, 34.8, 14.8, MAT_WALL, bevel=0.08)
box("ov-gym_roofslab", CX, CY, 17.5, 17.8, 35.2, 15.2, MAT_ROOF, bevel=0.04)

# ---------- parapet 女儿墙 17.5-18.0 + 压顶 ----------
PW, PH = 34.8, 14.8
t = 0.25
box("ov-gym_parapet_N", CX, CY + PH / 2 - t / 2, 17.5, 17.92, PW, t, MAT_WALL2)
box("ov-gym_parapet_S", CX, CY - PH / 2 + t / 2, 17.5, 17.92, PW, t, MAT_WALL2)
box("ov-gym_parapet_E", CX + PW / 2 - t / 2, CY, 17.5, 17.92, t, PH - 2 * t, MAT_WALL2)
box("ov-gym_parapet_W", CX - PW / 2 + t / 2, CY, 17.5, 17.92, t, PH - 2 * t, MAT_WALL2)
box("ov-gym_coping_N", CX, CY + PH / 2 - t / 2, 17.92, 18.0, PW + 0.15, 0.4, MAT_CONC_TEX)
box("ov-gym_coping_S", CX, CY - PH / 2 + t / 2, 17.92, 18.0, PW + 0.15, 0.4, MAT_CONC_TEX)
box("ov-gym_coping_E", CX + PW / 2 - t / 2, CY, 17.92, 18.0, 0.4, PH - 2 * t, MAT_CONC_TEX)
box("ov-gym_coping_W", CX - PW / 2 + t / 2, CY, 17.92, 18.0, 0.4, PH - 2 * t, MAT_CONC_TEX)

# ---------- roof equipment: 2 boxes + louver slats + cap ----------
def roof_unit(name, cx, cy, z0, z1, sx, sy):
    box(name, cx, cy, z0, z1, sx, sy, MAT_METAL, bevel=0.05)
    box(name + "_cap", cx, cy, z1, z1 + 0.10, sx + 0.2, sy + 0.2, MAT_METAL_DARK, bevel=0.03)
    # 百叶: 南面 + 东面各 4 条横向薄板
    for i, z in enumerate([z0 + 0.35, z0 + 0.65, z0 + 0.95, z0 + 1.25]):
        if z > z1 - 0.1:
            continue
        box("%s_louverS_%d" % (name, i), cx, cy - sy / 2 - 0.04, z - 0.06, z + 0.06,
            sx - 0.3, 0.08, MAT_METAL_DARK)
        box("%s_louverE_%d" % (name, i), cx + sx / 2 + 0.04, cy, z - 0.06, z + 0.06,
            0.08, sy - 0.3, MAT_METAL_DARK)

roof_unit("ov-gym_roofunit1", CX - 9.0, CY - 2.0, 17.8, 18.9, 2.4, 1.6)
roof_unit("ov-gym_roofunit2", CX + 10.0, CY + 3.0, 17.8, 18.7, 2.0, 1.4)

# ---------- window bands: glass + metal frame + mullions + sill ----------
def window_band_long(name, cy_face, z0, z1, length):
    outward = 1.0 if cy_face > CY else -1.0
    # glass strip, slightly proud of the wall
    bpy.ops.mesh.primitive_cube_add(location=(CX, cy_face, (z0 + z1) / 2.0))
    o = bpy.context.active_object
    o.name = name + "_glass"
    o.dimensions = (length, 0.12, z1 - z0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(MAT_GLASS)
    objs.append(o)
    # 金属灰框体: 上下横框 (出墙 0.14)
    for zc in (z0 + 0.09, z1 - 0.09):
        box(name + "_rail_%d" % int(zc * 10), CX, cy_face + outward * 0.05,
            zc - 0.09, zc + 0.09, length + 0.3, 0.24, MAT_METAL)
    # 窗台板 (混凝土纹, 出墙 0.34)
    box(name + "_sill", CX, cy_face + outward * 0.10,
        z0 - 0.16, z0 - 0.02, length + 0.5, 0.34, MAT_CONC_TEX, bevel=0.02)
    # 竖挺: 金属灰, 每 3 m 一根, 出墙
    n = int(length // 3)
    for i in range(n + 1):
        x = CX - length / 2 + i * 3.0
        box(name + "_mullion_%02d" % i, x, cy_face + outward * 0.05,
            z0, z1, 0.22, 0.24, MAT_METAL)
    return o

def window_band_end(name, cx_face, z0, z1, length):
    outward = 1.0 if cx_face > CX else -1.0
    bpy.ops.mesh.primitive_cube_add(location=(cx_face, CY, (z0 + z1) / 2.0))
    o = bpy.context.active_object
    o.name = name + "_glass"
    o.dimensions = (0.12, length, z1 - z0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(MAT_GLASS)
    objs.append(o)
    for zc in (z0 + 0.09, z1 - 0.09):
        box(name + "_rail_%d" % int(zc * 10), cx_face + outward * 0.05, CY,
            zc - 0.09, zc + 0.09, 0.24, length + 0.3, MAT_METAL)
    box(name + "_sill", cx_face + outward * 0.10, CY,
        z0 - 0.16, z0 - 0.02, 0.34, length + 0.5, MAT_CONC_TEX, bevel=0.02)
    n = int(length // 3)
    for i in range(n + 1):
        y = CY - length / 2 + i * 3.0
        box(name + "_mullion_%02d" % i, cx_face + outward * 0.05, y,
            z0, z1, 0.24, 0.22, MAT_METAL)
    return o

# floor 1: tall band 2.0-7.0 on both long faces (hall glazing)
window_band_long("ov-gym_w1S", CY - 8.0, 2.0, 7.0, 32.0)
window_band_long("ov-gym_w1N", CY + 8.0, 2.0, 7.0, 32.0)
# floor 2: band 9.6-12.2 (footprint 35.4 x 15.4 -> faces y = CY +/- 7.7)
window_band_long("ov-gym_w2S", CY - 7.7, 9.6, 12.2, 30.0)
window_band_long("ov-gym_w2N", CY + 7.7, 9.6, 12.2, 30.0)
# floor 3: band 14.1-16.7 (footprint 34.8 x 14.8 -> faces y = CY +/- 7.4)
window_band_long("ov-gym_w3S", CY - 7.4, 14.1, 16.7, 29.0)
window_band_long("ov-gym_w3N", CY + 7.4, 14.1, 16.7, 29.0)
# end faces (east/west) small bands per floor
window_band_end("ov-gym_w1E", CX + 18.0, 2.5, 6.5, 10.0)
window_band_end("ov-gym_w1W", CX - 18.0, 2.5, 6.5, 10.0)
window_band_end("ov-gym_w2E", CX + 17.7, 9.8, 12.0, 9.0)
window_band_end("ov-gym_w2W", CX - 17.7, 9.8, 12.0, 9.0)
window_band_end("ov-gym_w3E", CX + 17.4, 14.3, 16.5, 8.0)
window_band_end("ov-gym_w3W", CX - 17.4, 14.3, 16.5, 8.0)

# ---------- entrance (south face): thick canopy + thick columns + bases + glass doors ----------
# 雨棚加厚 3.15-3.70 (0.55), 外挑 2.8 m
box("ov-gym_canopy", CX, CY - 8.0 - 1.4, 3.15, 3.70, 10.5, 2.8, MAT_CONC_TEX, bevel=0.04)
# 雨棚前沿深灰压边
box("ov-gym_canopy_fascia", CX, CY - 8.0 - 2.75, 3.40, 3.70, 10.5, 0.12, MAT_METAL_DARK)
# 柱子加粗 0.6 + 柱础 0.9 + 柱头 0.8
for sxn, xn in (("E", CX + 4.4), ("W", CX - 4.4)):
    box("ov-gym_col_%s_base" % sxn, xn, CY - 8.0 - 2.3, 0.0, 0.5, 0.9, 0.9, MAT_CONC_TEX, bevel=0.04)
    box("ov-gym_col_%s" % sxn, xn, CY - 8.0 - 2.3, 0.5, 3.15, 0.6, 0.6, MAT_CONC_TEX, bevel=0.04)
    box("ov-gym_col_%s_cap" % sxn, xn, CY - 8.0 - 2.3, 3.0, 3.2, 0.8, 0.8, MAT_CONC_TEX, bevel=0.03)
# 台阶两级
box("ov-gym_step1", CX, CY - 8.0 - 0.55, 0.25, 0.5, 7.0, 1.1, MAT_CONC_TEX, bevel=0.03)
box("ov-gym_step2", CX, CY - 8.0 - 1.45, 0.0, 0.25, 7.6, 0.9, MAT_CONC_TEX, bevel=0.03)
# 正门: 金属灰门框 (两侧门垛 + 顶梁) + 4 扇玻璃门 + 中挺 + 横推杆
box("ov-gym_door_jamb_E", CX + 3.05, CY - 8.0, 0.5, 3.15, 0.3, 0.26, MAT_METAL)
box("ov-gym_door_jamb_W", CX - 3.05, CY - 8.0, 0.5, 3.15, 0.3, 0.26, MAT_METAL)
box("ov-gym_door_header", CX, CY - 8.0, 2.95, 3.15, 6.4, 0.26, MAT_METAL)
for i, lx in enumerate([-2.175, -0.725, 0.725, 2.175]):
    box("ov-gym_door_leaf_%d" % i, CX + lx - 0.725 + 0.725, CY - 8.0, 0.5, 2.95, 1.35, 0.10, MAT_GLASS)
for mx in (-2.175, -0.725, 0.725, 2.175):
    pass
# 中挺在叶扇交界处 (x = CX-1.45, CX, CX+1.45)
for i, mx in enumerate([-1.45, 0.0, 1.45]):
    box("ov-gym_door_mullion_%d" % i, CX + mx, CY - 8.0 - 0.02, 0.5, 2.95, 0.18, 0.22, MAT_METAL)
# 横推杆 (每扇一根, 金属灰, 出墙)
for i, lx in enumerate([-2.175, -0.725, 0.725, 2.175]):
    box("ov-gym_door_bar_%d" % i, CX + lx, CY - 8.0 - 0.12, 1.08, 1.22, 1.1, 0.08, MAT_METAL)

# ---------- lighting (SPEC §2) ----------
sun_data = bpy.data.lights.new("ov-gym_sun", type="SUN")
sun_data.energy = 3.5
sun_data.use_shadow = True
sun = bpy.data.objects.new("ov-gym_sun", sun_data)
bpy.context.collection.objects.link(sun)
sun.location = (CX - 40.0, CY - 40.0, 45.0)
target = Vector((CX, CY, 4.0))
d = (target - sun.location).normalized()
sun.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

world = bpy.data.worlds.new("ov-gym_world")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.65, 0.78, 0.88, 1.0)
bg.inputs["Strength"].default_value = 1.0

# ---------- reflection cubemaps (楼前一处 + 屋顶一处, 不进导出) ----------
def add_cubemap(name, loc, dist):
    bpy.ops.object.lightprobe_add(type="SPHERE", location=loc)  # 4.2 Eevee Next: SPHERE = reflection cubemap
    p = bpy.context.active_object
    p.name = name
    try:
        p.data.influence_distance = dist
    except Exception:
        pass
    try:
        p.data.resolution = 256
    except Exception:
        pass
    try:
        p.data.clip_end = 120.0
    except Exception:
        pass
    return p

add_cubemap("ov-gym_probe_front", (CX, CY - 16.0, 5.0), 45.0)
add_cubemap("ov-gym_probe_roof", (CX, CY, 22.0), 35.0)

# ---------- camera: 45 deg overview from SE so south + east faces visible ----------
cam_data = bpy.data.cameras.new("ov-gym_cam")
cam_data.lens = 35.0
cam = bpy.data.objects.new("ov-gym_cam", cam_data)
bpy.context.collection.objects.link(cam)
cam.location = (CX + 38.0, CY - 38.0, 34.0)
ct = Vector((CX, CY, 7.0))
cd = (ct - cam.location).normalized()
cam.rotation_euler = cd.to_track_quat("-Z", "Y").to_euler()
bpy.context.scene.camera = cam

# ---------- save .blend ----------
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("SAVED", BLEND_PATH)

# ---------- export .glb (only this item's objects) ----------
bpy.ops.object.select_all(action="DESELECT")
for o in objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format="GLB",
                           use_selection=True, export_apply=True)
print("EXPORTED", GLB_PATH)

# ---------- render settings only (Eevee + SSR) ----------
# 本地不渲染: 预览图改走 GitHub Actions, 这里只把渲染参数存进 .blend 供 Actions 用
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100
try:
    scene.eevee.taa_render_samples = 16
except Exception:
    pass
try:
    scene.eevee.use_ssr = True
except Exception as e:
    print("SSR not set:", e)
try:
    scene.eevee.use_ssr_refraction = True
except Exception as e:
    print("SSR refraction not set:", e)
try:
    scene.eevee.use_ssr_halfres = False
except Exception:
    pass
scene.render.filepath = PNG_PATH
scene.render.image_settings.file_format = "PNG"
print("RENDER SKIPPED (local render disabled; preview via GitHub Actions)")

# ---------- verify glb by re-importing ----------
before = set(o.name for o in bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB_PATH)
imported = [o for o in bpy.data.objects if o.name not in before]
print("GLB REIMPORT OK, objects:", len(imported))
for o in imported:
    print("  imported:", o.name)

print("DONE ov-gym")
