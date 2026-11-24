# cl-floor-walls: 教室内部·地面墙面
# 返工 R2-T17 (2026-11-24): 墙面偏青绿只调颜色 -- 见文件末尾
#   BASE_COLOR_FACTOR (暖色补偿, 抵消 Godot 绿天光); 尺寸结构一字未动。
# 返工 R2-T27 (2026-11-25): 后墙偏暗分墙调色 -- 西墙另立材质
#   cl-floor-walls_wall_back, 因子 (1.85, 0.62, 0.45); 南北/东墙
#   因子不动; 天花板顺带去绿 (1.0, 0.85, 0.78); 几何一字未动。
# 纹理已固化进脚本（见文件末尾 _apply_pbr_textures，2026-11-23）：
# 染色贴图 assets/blender/tex/ + 原图 assets/external/，材质节点直连
# Base Color/Roughness/Normal；重跑不再丢贴图。
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
# 西墙（后墙，黑板墙）单独材质 (R2-T27, 2026-11-25)：只靠绿天光照明，
# 与受直射的南北墙光照差 9 倍，单因子无法两边兼顾（见文件末尾注释），
# 故西墙另立材质、另给补偿因子；几何/贴图/尺寸与 MAT_WALL 完全相同。
MAT_WALL_BACK = plaster("cl-floor-walls_wall_back", "#F3E9D2",
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
# R2-T27: 用 MAT_WALL_BACK（另给补偿因子），几何一字未动。
add_box("cl-floor-walls_wall_west", (-4.84, 0, H / 2.0),
        (WT, LY - WT, H), MAT_WALL_BACK, bevel=0.01)

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

# ---- PBR 贴图固化 (2026-11-23)：把上一轮挂在 .blend 上的外部贴图写进脚本 ----
# color 图：assets/blender/tex/ 里的染色图（已按 SPEC §3 目标色染色）；
# rough/normal 图：assets/external/ 原图（CC0）。
# 节点只许 TexCoord→Mapping→Image Texture 直连 BSDF，不加 Hue/Sat/Mix，
# 否则 glTF 导出器不认。Base Color 默认值须置白、Roughness 置 1.0（贴图
# 本身带颜色与粗糙度），否则导出器会把旧纯色写成 baseColorFactor/
# roughnessFactor 与贴图二次相乘；Metallic 保持脚本原值。
# 没有 UV 的网格补 Smart UV Project（已有 UV 的不动）。
TEX_DIR = os.path.join(BASE, "assets/blender/tex")
EXT_DIR = os.path.join(BASE, "assets/external")
# 墙面暖色补偿 (R2-T17, 2026-11-24): 只改颜色, 不动尺寸结构。
# 实测根因不在材质本身 -- 墙贴图 white_stucco__F3E9D2.jpg 100% 像素暖色
# (均值 243,232,210 = #F3E9D2, 0% 像素偏绿), Blender 预览也是米白;
# 但在 Godot 里墙渲成青绿 (94,136,118): 天空材质 ground_bottom_color
# #4a6b38 (绿) 是室内环境光 AMBIENT_SOURCE_SKY 的地面色
# (scripts/weather_system.gd:52), 白墙被绿天光照绿 (白空调壳同渲
# (93,132,124) 作证)。按线性光模型反推: 渲染 = 反照率 x 环境光,
# 环境光线性比约 (0.125, 0.306, 0.281); 要渲染回暖色 (约 97,88,68),
# 反照率须乘线性因子 (1.0, 0.39, 0.32)。做法: 墙材质的 color 贴图后
# 串一个 MixRGB MULTIPLY 节点 (常量 = 该因子), glTF 导出器把它写成
# baseColorFactor 与贴图相乘 (socket 默认值在贴图链接时不被导出, 故
# 不能只改默认值); 等效反照率 sRGB 约 (243,151,123)。代价: Blender 预览
# (中性光) 下墙会直接显出这层暖粉补偿色, Godot 侧验收以
# 03-classroom 为准。只补墙面; 天花板同理发绿但 03 取景内不可见, 不动。
# 分墙调色 (R2-T27, 2026-11-25): T17 单因子在 Godot 里实测两边表现
# 不同 -- 后墙 (西墙) 几乎只靠天光, 实测 (72,70,57), 比目标暖褐
# (97,88,68) 暗约 25%; 右墙 (北墙) 受直射, 实测 (200,132,100) 三文鱼
# 色 (R2-T24 诊断, Web 实拍复核一致)。线性反推: 后墙辐照度约
# (0.072, 0.195, 0.198) (绿天光主导), 右墙约 (0.644, 0.733, 0.618)
# (日光主导, 近中性)。后墙要到 (97,88,68) 需反照率 (1.65, 0.50, 0.29),
# 即因子 (1.85, 0.62, 0.45) -- R 分量 >1 (贴图 R 已 243, 单靠贴图
# 提不上去); 同因子放右墙会算出 (263,163,117), R 溢出吹成粉红,
# 故必须分墙: 西墙单独材质另给因子, 南北/东墙沿用 T17 因子不动
# (右墙维持 (200,132,100), 不冲粉)。天花板顺带去绿: 同法, 辐照度
# (0.078, 0.074, 0.051), 因子 (1.0, 0.85, 0.78) 预测 (71,64,50),
# 只去绿不提亮 (提亮需因子 ~4, 不可行); 三因子全 ≤1, 与墙同 code path。
BASE_COLOR_FACTOR = {
    "cl-floor-walls_wall": (1.0, 0.39, 0.32),  # 线性值，南北/东墙，T17 原值不动
    "cl-floor-walls_wall_back": (1.85, 0.62, 0.45),  # 线性值，西墙（后墙）
    "cl-floor-walls_ceiling": (1.0, 0.85, 0.78),  # 线性值，天花板去绿
}

# ---- GLB baseColorFactor >1 补丁 (R2-T27) ----
# Blender 4.2 glTF 导出器在
# io_scene_gltf2/.../gltf2_blender_gather_materials_pbr_metallic_roughness.py
# __gather_base_color_factor() 里硬 clamp（rgb = [max(min(c, 1.0), 0.0)...]），
# >1 的补偿因子导不出，GLB 里会变成 1.0。后墙要达到目标暖褐必须 R=1.85
# （见上；贴图 R 已 243，单靠贴图提不上去；不改灯光），故导出后直接改
# GLB 的 JSON chunk，把指定材质的 baseColorFactor 写回 .blend 里的真实
# 值。.blend 本就存 1.85（Blender 自身渲染也用它），补丁后 .blend 与
# .glb 一致；重跑本脚本会重新打补丁。只改 JSON chunk，不动 BIN chunk。
# 课堂场景拼装脚本 classroom.py 里有同一份补丁（它从 .blend 重导出，
# 也会触发同一 clamp），两处须保持同步。
GLB_FACTOR_PATCH = {
    "cl-floor-walls_wall_back": [1.85, 0.62, 0.45, 1.0],
}


def _patch_glb_factors(glb_path):
    import json as _json
    import struct as _struct
    with open(glb_path, "rb") as f:
        data = bytearray(f.read())
    assert data[:4] == b"glTF", "not a GLB file: %s" % glb_path
    total_len = _struct.unpack_from("<I", data, 8)[0]
    assert total_len == len(data), "GLB length mismatch: %s" % glb_path
    json_len = _struct.unpack_from("<I", data, 12)[0]
    json_start = 20
    js = _json.loads(bytes(data[json_start:json_start + json_len]))
    patched = []
    for m in js.get("materials", []):
        want = GLB_FACTOR_PATCH.get(m.get("name"))
        if want is not None:
            m.setdefault("pbrMetallicRoughness", {})["baseColorFactor"] = want
            patched.append(m["name"])
    if not patched:
        print("GLB factor patch: no matching material in", glb_path)
        return
    new_json = _json.dumps(js, separators=(",", ":")).encode("utf-8")
    pad = (-len(new_json)) % 4  # JSON chunk 须 4 字节对齐，空格补齐
    new_json += b" " * pad
    rest = bytes(data[json_start + json_len:])
    new_total = 20 + len(new_json) + len(rest)
    out = bytearray()
    out += data[:8]  # magic + version
    out += _struct.pack("<I", new_total)
    out += _struct.pack("<I", len(new_json))
    out += b"JSON"
    out += new_json
    out += rest
    assert len(out) == new_total
    with open(glb_path, "wb") as f:
        f.write(out)
    print("GLB factor patch: %s -> %s" % (patched, glb_path))

PBR_TEXTURES = {
    "cl-floor-walls_floor": ("concrete_wall_007__D8D2C4.jpg",
        "polyhaven/concrete_wall_007_rough_1k.jpg",
        "polyhaven/concrete_wall_007_nor_gl_1k.jpg", (6.0, 5.0)),
    "cl-floor-walls_grout": ("concrete_wall_007__B9B3A8.jpg",
        "polyhaven/concrete_wall_007_rough_1k.jpg",
        "polyhaven/concrete_wall_007_nor_gl_1k.jpg", (1.0, 1.0)),
    "cl-floor-walls_wall": ("white_stucco__F3E9D2.jpg",
        "polyhaven/white_stucco_rough_1k.jpg",
        "polyhaven/white_stucco_nor_gl_1k.jpg", (3.0, 2.0)),
    "cl-floor-walls_wall_back": ("white_stucco__F3E9D2.jpg",
        "polyhaven/white_stucco_rough_1k.jpg",
        "polyhaven/white_stucco_nor_gl_1k.jpg", (3.0, 2.0)),
    "cl-floor-walls_skirt": ("concrete_wall_007__424A52.jpg",
        "polyhaven/concrete_wall_007_rough_1k.jpg",
        "polyhaven/concrete_wall_007_nor_gl_1k.jpg", (2.0, 1.0)),
    "cl-floor-walls_ceiling": ("Plaster001__E8E8E8.jpg",
        "ambientcg/Plaster001/Plaster001_1K-JPG_Roughness.jpg",
        "ambientcg/Plaster001/Plaster001_1K-JPG_NormalGL.jpg", (6.0, 4.0)),
}


_IMG_CACHE = {}


def _pbr_load_image(abs_path, colorspace):
    # 同一文件只加载一次：filepath 改成相对路径后 check_existing 会按路径
    # 字符串比对失效、重复建 .001 副本，故用自带缓存去重
    img = _IMG_CACHE.get(abs_path)
    if img is None:
        img = bpy.data.images.load(abs_path, check_existing=True)
        img.colorspace_settings.name = colorspace
        # 存相对路径进 .blend（// 相对 .blend 所在目录），仓库检出后仍能找到
        rel = os.path.relpath(abs_path, os.path.dirname(BLEND_PATH)).replace(os.sep, "/")
        img.filepath = "//" + rel
        _IMG_CACHE[abs_path] = img
    return img


def _apply_pbr_textures():
    for mat_name, (color_f, rough_f, normal_f, scale) in PBR_TEXTURES.items():
        mat = bpy.data.materials.get(mat_name)
        if mat is None:
            print("PBR SKIP missing material:", mat_name)
            continue
        nt = mat.node_tree
        bsdf = nt.nodes["Principled BSDF"]
        # 清掉旧程序化节点，只留 BSDF 与 Output
        for node in list(nt.nodes):
            if node.type not in ("BSDF_PRINCIPLED", "OUTPUT_MATERIAL"):
                nt.nodes.remove(node)
        bsdf.inputs["Base Color"].default_value = (1.0, 1.0, 1.0, 1.0)
        bsdf.inputs["Roughness"].default_value = 1.0
        texcoord = nt.nodes.new("ShaderNodeTexCoord")
        mapping = nt.nodes.new("ShaderNodeMapping")
        mapping.inputs["Scale"].default_value = (scale[0], scale[1], 1.0)
        nt.links.new(texcoord.outputs["UV"], mapping.inputs["Vector"])
        tex_c = nt.nodes.new("ShaderNodeTexImage")
        tex_c.image = _pbr_load_image(os.path.join(TEX_DIR, color_f), "sRGB")
        nt.links.new(mapping.outputs["Vector"], tex_c.inputs["Vector"])
        # 墙面暖色补偿 (见 BASE_COLOR_FACTOR): Base Color 已链接贴图时,
        # 导出器不读 socket 默认值, 只认新 Mix 节点 (type MIX, 非旧
        # MixRGB) 的 MULTIPLY 常量 (detect_multiply_by_constant), 把它
        # 写成 baseColorFactor 与贴图相乘; 其余材质仍直连。
        # 注意：导出器会把 >1 的常量 clamp 到 1.0，导出后由文件末尾的
        # _patch_glb_factors() 写回（见 BASE_COLOR_FACTOR 上方说明）。
        # 注意: Mix 节点有 10 个输入槽, RGBA 的 A/B 是 inputs[6]/[7]
        # (4 元), 输出 RGBA 是 outputs[2]; 按名字取 "A" 会取到 VALUE 槽。
        factor = BASE_COLOR_FACTOR.get(mat_name)
        if factor is not None:
            mix = nt.nodes.new("ShaderNodeMix")
            mix.data_type = "RGBA"
            mix.blend_type = "MULTIPLY"
            mix.inputs[0].default_value = 1.0  # Fac 须为 1, 导出器才认
            mix.inputs[6].default_value = (1.0, 1.0, 1.0, 1.0)
            mix.inputs[7].default_value = (*factor, 1.0)
            nt.links.new(tex_c.outputs["Color"], mix.inputs[6])
            nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
            print("PBR color-factor:", mat_name, factor)
        else:
            nt.links.new(tex_c.outputs["Color"], bsdf.inputs["Base Color"])
        tex_r = nt.nodes.new("ShaderNodeTexImage")
        tex_r.image = _pbr_load_image(os.path.join(EXT_DIR, rough_f), "Non-Color")
        nt.links.new(mapping.outputs["Vector"], tex_r.inputs["Vector"])
        nt.links.new(tex_r.outputs["Color"], bsdf.inputs["Roughness"])
        tex_n = nt.nodes.new("ShaderNodeTexImage")
        tex_n.image = _pbr_load_image(os.path.join(EXT_DIR, normal_f), "Non-Color")
        nmap = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(mapping.outputs["Vector"], tex_n.inputs["Vector"])
        nt.links.new(tex_n.outputs["Color"], nmap.inputs["Color"])
        nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
        print("PBR textured:", mat_name, color_f, "scale", scale)


def _ensure_uvs(objs):
    """没有 UV 的网格补 Smart UV Project（已有 UV 的不动）。"""
    todo = []
    seen = set()
    for ob in objs:
        if ob.type != "MESH":
            continue
        if id(ob.data) in seen:
            continue
        seen.add(id(ob.data))
        if len(ob.data.uv_layers) == 0:
            todo.append(ob)
    if not todo:
        print("UV OK: all meshes have UVs")
        return
    bpy.ops.object.select_all(action="DESELECT")
    for ob in todo:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = todo[0]
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66.0), island_margin=0.02)
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    print("UV smart-projected:", len(todo), [o.name for o in todo])


_apply_pbr_textures()
_ensure_uvs(piece_objs)

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

# 导出器 clamp 补丁 (R2-T27)：把 >1 的补偿因子写回 GLB，见上。
_patch_glb_factors(GLB_PATH)

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
