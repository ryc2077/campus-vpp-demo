# 注意（2026-11-23 纹理升级）：本件 .blend 已挂外部 PBR 贴图
# （染色贴图 assets/blender/tex/ + 原图 assets/external/，材质节点直连
# Base Color/Roughness/Normal）。重跑本脚本会从零重建、丢失全部贴图，
# 重跑前须先把纹理步骤补进脚本再跑；不要只重跑本脚本就推。
# cl-floor-walls: 教室内部·地面墙面
# 规约: assets/blender/SPEC.md §6 教室局部坐标
#   房间中心原点, x 长 9.68m (-4.84~+4.84), y 宽 7.26m (-3.63~+3.63), z 0-3.0m
#   黑板墙在 x=-4.84 一侧 (西墙, 无洞口)
#   南墙 y=-3.63 / 北墙 y=+3.63 各留 4 个窗洞: 1.8 宽 x 1.5 高, 窗台高 0.9m
#   (窗 z 0.9-2.4), x 中心 -3.6, -1.2, +1.2, +3.6, 与 cl-windows 件一一对应
#   东墙 x=+4.84 留 1 个门洞: 1.0 宽 x 2.2 高, y=0 处
#   墙体用分段盒子搭, 不用布尔切割
# 只做地面/墙体/踢脚线/天花板, 不做桌椅/黑板/空调/灯具/窗户窗帘。
# 本次返工: 只补材质程序化纹理 (墙面/天花板 Noise 乳胶漆 + Bump,
#   地面 Voronoi/Noise 石材纹), 不动任何几何、位置、相机。
# 预览里的灯光/相机不导出。

import bpy
import math
import os

BASE = os.path.expanduser(
    "~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
BLEND_PATH = os.path.join(BASE, "assets/blender/classroom/cl-floor-walls.blend")
GLB_PATH = os.path.join(BASE, "assets/models/cl-floor-walls.glb")
# 新规矩: 渲染全部走 GitHub Actions, 本地不渲染、不出预览图。

# ---- sRGB hex -> linear (SPEC 坑: Principled Base Color 要线性值) ----
def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def hex_linear(h):
    h = h.lstrip("#")
    r = int(h[0:2], 16) / 255.0
    g = int(h[2:4], 16) / 255.0
    b = int(h[4:6], 16) / 255.0
    return (srgb_to_linear(r), srgb_to_linear(g), srgb_to_linear(b), 1.0)

# ---- 清空场景 ----
bpy.ops.wm.read_factory_settings(use_empty=True)

# ---- 材质 (只用 Principled BSDF; 程序化纹理, 无外部贴图) ----
def principled(name, color_hex, roughness=0.9, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = hex_linear(color_hex)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat

def _noise(nt, scale, detail=4.0, roughness=0.7, distortion=0.0):
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    n.inputs["Roughness"].default_value = roughness
    n.inputs["Distortion"].default_value = distortion
    return n

def _ramp_grey(nt, lo, hi):
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (lo, lo, lo, 1.0)
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = (hi, hi, hi, 1.0)
    return ramp

def _multiply(nt, base_color, ramp_out):
    """base_color * ramp 灰度 -> Color 输出 (颜色深浅不均)。"""
    m = nt.nodes.new("ShaderNodeMixRGB")
    m.blend_type = 'MULTIPLY'
    m.inputs[0].default_value = 1.0
    m.inputs[1].default_value = base_color
    nt.links.new(ramp_out, m.inputs[2])
    return m

def _roughness_from_noise(nt, tc, scale, lo, hi):
    nz = _noise(nt, scale, detail=3.0, roughness=0.7)
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    ramp = _ramp_grey(nt, lo, hi)
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    return ramp.outputs["Color"]

def _bump(nt, height_out, strength, distance):
    b = nt.nodes.new("ShaderNodeBump")
    b.inputs["Strength"].default_value = strength
    b.inputs["Distance"].default_value = distance
    nt.links.new(height_out, b.inputs["Height"])
    return b

def plaster(name, color_hex, noise_scale=2.5, mottle_lo=0.80,
            bump_strength=0.2):
    """墙面/天花板: Noise 乳胶漆/混凝土纹 + Bump, 颜色深浅不均 + 粗糙度变化。
    用 Object 坐标 (盒子已 apply scale, 局部坐标即米制), 各墙块纹理尺度一致。"""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    base = hex_linear(color_hex)
    # 兜底默认值 (与 cl-board/cl-desks 同款做法): glTF 导出器导不出
    # 程序化节点链时回落到 socket 默认值, 不设就是白 + 粗糙度 1.0;
    # Blender 内连线优先, 纹理变化不受影响
    bsdf.inputs["Base Color"].default_value = base
    bsdf.inputs["Roughness"].default_value = 0.9
    bsdf.inputs["Metallic"].default_value = 0.0
    tc = nt.nodes.new("ShaderNodeTexCoord")
    # 大尺度色斑: Noise -> 灰度 Ramp(0.80~1.00) -> 与底色相乘
    nz = _noise(nt, noise_scale, detail=5.0, roughness=0.75, distortion=0.4)
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    ramp = _ramp_grey(nt, mottle_lo, 1.0)
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    # 返工 2026-11-23: 色斑 Mix 不连 Base Color (Blender 4.2 glTF 导出器:
    # Base Color 已链接时不写 baseColorFactor, 墙/天花板在 Godot 里变白;
    # 旧注释称“回落默认值”是错的, 实测 GLB 证实)。色斑只留粗糙度/Bump 变化,
    # Base Color 用上面设好的纯色默认值。
    # 漆面微起伏
    bump = _bump(nt, nz.outputs["Fac"], bump_strength, 0.05)
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    # 粗糙度变化
    nt.links.new(_roughness_from_noise(nt, tc, noise_scale * 2.5, 0.82, 0.97),
                 bsdf.inputs["Roughness"])
    return mat

def stone_tile(name, color_hex):
    """地面瓷砖: Voronoi 石材纹 (每格色调随机, 格 ~0.6m 贴合砖缝间距)
    + 细 Noise 石材颗粒, 缝线几何不动。"""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    base = hex_linear(color_hex)
    # glTF 回落兜底: 见 plaster() 注释; 地面釉面砖粗糙度中值 0.75
    bsdf.inputs["Base Color"].default_value = base
    bsdf.inputs["Roughness"].default_value = 0.75
    bsdf.inputs["Metallic"].default_value = 0.0
    tc = nt.nodes.new("ShaderNodeTexCoord")
    # 每块石材色调不均: Voronoi F1, scale 1.7 -> 格约 0.59m
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.feature = 'F1'
    vor.inputs["Scale"].default_value = 1.7
    vor.inputs["Randomness"].default_value = 1.0
    nt.links.new(tc.outputs["Object"], vor.inputs["Vector"])
    ramp_v = _ramp_grey(nt, 0.74, 1.0)
    nt.links.new(vor.outputs["Color"], ramp_v.inputs["Fac"])
    mix1 = _multiply(nt, base, ramp_v.outputs["Color"])
    # 细颗粒: Noise scale 12 -> 灰度 0.88~1.00 再乘一次
    nz = _noise(nt, 12.0, detail=3.0, roughness=0.7)
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    ramp_n = _ramp_grey(nt, 0.88, 1.0)
    nt.links.new(nz.outputs["Fac"], ramp_n.inputs["Fac"])
    mix2 = nt.nodes.new("ShaderNodeMixRGB")
    mix2.blend_type = 'MULTIPLY'
    mix2.inputs[0].default_value = 1.0
    nt.links.new(mix1.outputs["Color"], mix2.inputs[1])
    nt.links.new(ramp_n.outputs["Color"], mix2.inputs[2])
    # 返工 2026-11-23: 石材 Mix 不连 Base Color (同上, 否则 glTF 丢 factor 地面变白)。
    # 石材微起伏
    bump = _bump(nt, nz.outputs["Fac"], 0.25, 0.03)
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    # 粗糙度变化 (釉面砖局部光泽不一)
    nt.links.new(_roughness_from_noise(nt, tc, 5.0, 0.62, 0.88),
                 bsdf.inputs["Roughness"])
    return mat

MAT_FLOOR = stone_tile("cl-floor-walls_floor", "#D8D2C4")
MAT_GROUT = principled("cl-floor-walls_grout", "#B9B3A8", roughness=0.9)
MAT_WALL = plaster("cl-floor-walls_wall", "#F3E9D2",
                   noise_scale=2.5, mottle_lo=0.80, bump_strength=0.2)
# 踢脚线: 深灰漆面 + Noise 轻微污渍深浅 + Bump + 粗糙度变化;
# 分缝靠几何: 踢脚线已按墙垛分段 (窗洞/门洞处断开), 段间即缝
MAT_SKIRT = plaster("cl-floor-walls_skirt", "#424A52",
                    noise_scale=6.0, mottle_lo=0.85, bump_strength=0.15)
MAT_CEIL = plaster("cl-floor-walls_ceiling", "#E8E8E8",
                   noise_scale=3.0, mottle_lo=0.82, bump_strength=0.15)

# ---- 集合 ----
coll = bpy.data.collections.new("cl-floor-walls")
bpy.context.scene.collection.children.link(coll)

piece_objs = []

def add_box(name, loc, dims, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0:
        mod = ob.modifiers.new("bevel", 'BEVEL')
        mod.width = bevel
        mod.segments = 2
    ob.data.materials.append(mat)
    coll.objects.link(ob)
    bpy.context.scene.collection.objects.unlink(ob)
    piece_objs.append(ob)
    return ob

# ---- 尺寸 ----
LX = 9.68        # x 长, -4.84 ~ +4.84
LY = 7.26        # y 宽, -3.63 ~ +3.63
H = 3.0          # 墙高
WT = 0.15        # 墙厚
WIN_W = 1.8      # 窗宽
WIN_H = 1.5      # 窗高
WIN_Z0 = 0.9     # 窗台高
WIN_X = [-3.6, -1.2, 1.2, 3.6]   # 窗 x 中心, 与 cl-windows 一致
# 窗洞 x 范围: [-4.5,-2.7] [-2.1,-0.3] [0.3,2.1] [2.7,4.5]
# 墙垛 x 范围: [-4.84,-4.5] [-2.7,-2.1] [-0.3,0.3] [2.1,2.7] [4.5,4.84]
PIERS = [(-4.67, 0.34), (-2.4, 0.6), (0.0, 0.6), (2.4, 0.6), (4.67, 0.34)]
DOOR_W = 1.0     # 门宽 (y 向)
DOOR_H = 2.2     # 门高

# ---- 地面: 9.68 x 7.26, 厚 0.05, 顶面 z=0 ----
add_box("cl-floor-walls_floor", (0, 0, -0.025), (LX, LY, 0.05), MAT_FLOOR,
        bevel=0.01)

# ---- 地砖缝: 0.6m 间距浅灰线, 薄片贴于地面上 (z 0.001-0.003, 防共面) ----
n_grout = 0
k = 1
while -4.84 + 0.6 * k < 4.84 - 0.01:
    add_box("cl-floor-walls_grout_x%02d" % k, (-4.84 + 0.6 * k, 0, 0.002),
            (0.015, LY, 0.002), MAT_GROUT)
    n_grout += 1
    k += 1
k = 1
while -3.63 + 0.6 * k < 3.63 - 0.01:
    add_box("cl-floor-walls_grout_y%02d" % k, (0, -3.63 + 0.6 * k, 0.002),
            (LX, 0.015, 0.002), MAT_GROUT)
    n_grout += 1
    k += 1
print("grout lines: %d" % n_grout)  # x 向 16 条 + y 向 12 条 = 28

# ---- 南墙 / 北墙 (各 4 窗洞): 墙垛通高 + 窗下槛墙 + 窗上过梁 ----
for side, y_wall, tag in ((-3.63, -3.63, "s"), (3.63, 3.63, "n")):
    for i, (xc, w) in enumerate(PIERS, start=1):
        add_box("cl-floor-walls_wall_%s_pier%d" % (tag, i),
                (xc, y_wall, H / 2.0), (w, WT, H), MAT_WALL, bevel=0.01)
    for i, xc in enumerate(WIN_X, start=1):
        add_box("cl-floor-walls_wall_%s_sill%d" % (tag, i),
                (xc, y_wall, WIN_Z0 / 2.0), (WIN_W, WT, WIN_Z0), MAT_WALL,
                bevel=0.01)
        add_box("cl-floor-walls_wall_%s_lintel%d" % (tag, i),
                (xc, y_wall, WIN_Z0 + WIN_H + (H - WIN_Z0 - WIN_H) / 2.0),
                (WIN_W, WT, H - WIN_Z0 - WIN_H), MAT_WALL, bevel=0.01)

# ---- 西墙 (黑板墙, 无洞口): 夹在南北墙之间, y -3.555~+3.555 ----
add_box("cl-floor-walls_wall_west", (-4.84, 0, H / 2.0),
        (WT, LY - WT, H), MAT_WALL, bevel=0.01)

# ---- 东墙 (门洞 y -0.5~+0.5, z 0-2.2): 两侧通高墙垛 + 门上过梁 ----
add_box("cl-floor-walls_wall_east_south", (4.84, -2.0275, H / 2.0),
        (WT, 3.055, H), MAT_WALL, bevel=0.01)
add_box("cl-floor-walls_wall_east_north", (4.84, 2.0275, H / 2.0),
        (WT, 3.055, H), MAT_WALL, bevel=0.01)
add_box("cl-floor-walls_wall_east_lintel", (4.84, 0, DOOR_H + (H - DOOR_H) / 2.0),
        (WT, DOOR_W, H - DOOR_H), MAT_WALL, bevel=0.01)

# ---- 踢脚线: 高 0.1m, 厚 0.02, 贴墙内面; 门洞和窗洞处断开 ----
# 南/北墙: 只在墙垛段 (窗洞 x 范围内断开); 东墙: 门洞 y 范围内断开; 西墙: 通长
for tag, y_wall, y_skirt in (("s", -3.63, -3.545), ("n", 3.63, 3.545)):
    for i, (xc, w) in enumerate(PIERS, start=1):
        add_box("cl-floor-walls_skirt_%s%d" % (tag, i),
                (xc, y_skirt, 0.05), (w, 0.02, 0.1), MAT_SKIRT)
add_box("cl-floor-walls_skirt_west", (-4.755, 0, 0.05),
        (0.02, LY - WT, 0.1), MAT_SKIRT)
add_box("cl-floor-walls_skirt_east_south", (4.755, -2.0275, 0.05),
        (0.02, 3.055, 0.1), MAT_SKIRT)
add_box("cl-floor-walls_skirt_east_north", (4.755, 2.0275, 0.05),
        (0.02, 3.055, 0.1), MAT_SKIRT)

# ---- 天花板: 9.68 x 7.26 白色平板, 厚 0.05, 底面 z=3.0 ----
add_box("cl-floor-walls_ceiling", (0, 0, 3.025), (LX, LY, 0.05), MAT_CEIL,
        bevel=0.01)

print("floor-walls built: %d objects" % len(piece_objs))
# 地面 1 + 砖缝 28 + 南墙 13 + 北墙 13 + 西墙 1 + 东墙 3 + 踢脚 13 + 天花板 1 = 73

# ---- 存 .blend (只含本件) ----
os.makedirs(os.path.dirname(BLEND_PATH), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)

# ---- 导出 .glb (只选本件对象) ----
bpy.ops.object.select_all(action='DESELECT')
for ob in piece_objs:
    ob.select_set(True)
bpy.context.view_layer.objects.active = piece_objs[0]
os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format='GLB',
                           use_selection=True, export_apply=True)

# ---- 回读校验 ----
n_before = len(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB_PATH)
n_imported = len(bpy.data.objects) - n_before
print("gltf reimport: %d objects imported" % n_imported)
assert n_imported > 0, "glTF reimport failed"
# 删掉回读进来的对象, 不污染预览/工程
imported = [ob for ob in bpy.data.objects if ob not in piece_objs]
for ob in imported:
    bpy.data.objects.remove(ob, do_unlink=True)

# ---- 预览/渲染: 不做 (走 GitHub Actions), 本脚本只建模+存盘+导出 ----
print("DONE cl-floor-walls")
