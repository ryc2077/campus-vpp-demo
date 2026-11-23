# di-busbar v2 — 配电房母线线缆返工（局部坐标：房中心原点，x -8~+8，y -5~+5，z 0~8）
# 纹理与线缆转网格已固化进脚本（见文件末尾，2026-11-23）：
# 染色贴图 assets/blender/tex/ + 原图 assets/external/，材质节点直连
# Base Color/Roughness/Normal；34 根线缆导出前由 CURVE 转 MESH；重跑不再丢贴图。
# 返工目标（筛查结论）：旧版墙面线槽和引下线缆缺失、铜排悬空。
# v2 内容：
#  ① 墙面线槽（桥架）：北墙水平线槽 + 东西墙水平线槽 + 4 根竖向墙面线槽，盖板分缝
#  ② 引下线缆：母线→每台配电柜 3 相垂线（带弯曲弧度、线卡固定）；桥架→每台变压器 3 相 + PE 线
#  ③ 铜排不再悬空：每台柜顶、每根母线各 1 个绝缘子支柱（底板+瓷体+伞裙+顶盖），共 18 处
#  ④ 铜排金属拉丝纹理 + 氧化深浅不均（Noise 粗糙度/Bump 变化）
#  ⑤ 线缆外皮纹理（红/黄/绿相色 + 黑色 PE，轻微噪波）
#  ⑥ 所有面不许全平：结构件倒角 + 程序化噪波（粗糙度/底色/Bump）
# 坐标依据：配电柜 6 台中心 x=-6/-3.6/-1.2/1.2/3.6/6，y=4.5，柜顶 z=2.2（di-cabinets）；
# 变压器 4 台中心 x=-4.5/-1.5/1.5/4.5，y=-2.5，套管端子顶 z≈3.14（di-transformer）；
# 配电房 16x10x8m（data/campus.json dist），4 台主变合计 3000kVA、10kV 双路进线。
# 不含配电柜 / 变压器 / 墙地面 / 标识牌。渲染默认跳过（本地不渲染，走 GitHub Actions）：
# 置环境变量 DI_BUSBAR_RENDER=1 才渲染预览图。
import bpy
import math
import os
from mathutils import Vector

BASE = "/home/hatch/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot"
BLEND_PATH = os.path.join(BASE, "assets/blender/dist/di-busbar.blend")
GLB_PATH = os.path.join(BASE, "assets/models/di-busbar.glb")
PNG_PATH = os.path.join(BASE, "screenshots/blender/di-busbar.png")

# ---------- 场景清理 ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------- 颜色：sRGB -> 线性 ----------
def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def hex_to_linear(h):
    h = h.lstrip("#")
    return tuple(srgb_to_linear(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4))

def make_material(name, hex_color, metallic=0.0, roughness=0.5):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*hex_to_linear(hex_color), 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat

def add_noise(mat, dark_hex, mid_hex, light_hex, noise_scale, rough_lo, rough_hi,
              bump_strength, stretch=None, detail=3.0):
    """程序化纹理：同一 Noise Fac 驱动底色深浅不均 + 粗糙度 + Bump，保证没有任何面全平。
    stretch=(sx, sy, sz)：映射拉伸，用于金属拉丝（沿拉丝方向拉长噪波出条纹）。"""
    nt = mat.node_tree
    nodes = nt.nodes
    links = nt.links
    bsdf = nodes["Principled BSDF"]
    texcoord = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = noise_scale
    noise.inputs["Detail"].default_value = detail
    noise.inputs["Roughness"].default_value = 0.7
    if stretch is not None:
        mapping = nodes.new("ShaderNodeMapping")
        mapping.inputs["Scale"].default_value = stretch
        links.new(texcoord.outputs["Generated"], mapping.inputs["Vector"])
        links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    else:
        links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])
    # 底色：三段 ColorRamp（深氧化 / 基色 / 亮面），深浅不均
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (*hex_to_linear(dark_hex), 1.0)
    ramp.color_ramp.elements[1].position = 0.55
    ramp.color_ramp.elements[1].color = (*hex_to_linear(mid_hex), 1.0)
    ramp.color_ramp.elements.new(1.0)
    ramp.color_ramp.elements[2].position = 1.0
    ramp.color_ramp.elements[2].color = (*hex_to_linear(light_hex), 1.0)
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    # 返工 2026-11-23: 底色 Ramp 不连 Base Color (否则 glTF 丢 baseColorFactor,
    # 铜排/线缆/桥架在 Godot 里全白)。深浅不均改走粗糙度/Bump, Base Color 只留纯色默认值。
    # 粗糙度：Fac -> Map Range 窄幅/宽幅浮动
    mr = nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.0
    mr.inputs["From Max"].default_value = 1.0
    mr.inputs["To Min"].default_value = rough_lo
    mr.inputs["To Max"].default_value = rough_hi
    links.new(noise.outputs["Fac"], mr.inputs["Value"])
    links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])
    # 微凸起
    if bump_strength > 0.0:
        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = bump_strength
        bump.inputs["Distance"].default_value = 0.015
        links.new(noise.outputs["Fac"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat

# ---------- 材质 ----------
# ④ 铜排：拉丝（沿 x 拉长噪波）+ 氧化深浅不均（深氧化 #6E3410 / 基色 #B87333 / 亮面 #D99A55）
MAT_COPPER = make_material("CopperBusbar", "#B87333", metallic=0.9, roughness=0.35)
add_noise(MAT_COPPER, "#6E3410", "#B87333", "#D99A55", 3.0, 0.25, 0.55, 0.04,
          stretch=(1.0, 12.0, 12.0))
MAT_CERAMIC = make_material("InsulatorCeramic", "#E8E8E8", metallic=0.0, roughness=0.45)
add_noise(MAT_CERAMIC, "#D2D2D2", "#E8E8E8", "#F5F5F5", 12.0, 0.35, 0.55, 0.02)
MAT_TRAY = make_material("CableTray", "#C0C5C9", metallic=0.6, roughness=0.5)
add_noise(MAT_TRAY, "#A9AEB2", "#C0C5C9", "#D3D7DA", 6.0, 0.4, 0.65, 0.05)
MAT_TRUNK = make_material("Trunking", "#AEB4B8", metallic=0.5, roughness=0.55)
add_noise(MAT_TRUNK, "#989EA3", "#AEB4B8", "#C2C7CB", 6.0, 0.45, 0.7, 0.05)
MAT_CLAMP = make_material("CableClamp", "#8A8F94", metallic=0.85, roughness=0.35)
add_noise(MAT_CLAMP, "#767C81", "#8A8F94", "#9CA2A7", 10.0, 0.25, 0.45, 0.02)
MAT_SEAM = make_material("CoverSeam", "#3A3F44", metallic=0.2, roughness=0.7)
# ⑤ 线缆外皮：红/黄/绿相色 + 黑色 PE，轻微噪波（粗糙度 0.5~0.75，Bump 0.03）
def cable_mat(name, hex_color, dark_hex, light_hex):
    m = make_material(name, hex_color, metallic=0.0, roughness=0.6)
    add_noise(m, dark_hex, hex_color, light_hex, 8.0, 0.5, 0.75, 0.03)
    return m
MAT_CABLE_R = cable_mat("Cable_Red", "#B03A2E", "#8E2B21", "#C65A4A")
MAT_CABLE_Y = cable_mat("Cable_Yellow", "#E8B400", "#C29300", "#F2C531")
MAT_CABLE_G = cable_mat("Cable_Green", "#2E7D32", "#235F26", "#43A047")
MAT_CABLE_K = cable_mat("Cable_Black", "#1A1A1A", "#101010", "#2E2E2E")
PHASE_MATS = [MAT_CABLE_R, MAT_CABLE_Y, MAT_CABLE_G]  # A 红 / B 黄 / C 绿

piece_objects = []
cable_objs = []  # 34 根引下/馈线缆（CURVE 建，导出前转 MESH，见文末固化步骤）

def add_box(name, dims, loc, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0:
        mod = obj.modifiers.new(name="Bevel", type="BEVEL")
        mod.width = bevel
        mod.segments = 2
        mod.limit_method = "ANGLE"
    obj.data.materials.append(mat)
    piece_objects.append(obj)
    return obj

def add_cylinder(name, radius, depth, loc, mat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=radius, depth=depth, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(mat)
    piece_objects.append(obj)
    return obj

def add_cable(name, points, radius, mat):
    """引下线缆：Bezier 曲线 + 倒角成圆管，AUTO 手柄出弯曲弧度。points 为 4 个 (x, y, z)。"""
    cu = bpy.data.curves.new(name, type="CURVE")
    cu.dimensions = "3D"
    cu.resolution_u = 12
    cu.bevel_depth = radius
    cu.bevel_resolution = 2
    spline = cu.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for bp, co in zip(spline.bezier_points, points):
        bp.co = co
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, cu)
    scene.collection.objects.link(obj)
    cu.materials.append(mat)
    piece_objects.append(obj)
    cable_objs.append(obj)
    return obj

CABINET_X = [-6.0, -3.6, -1.2, 1.2, 3.6, 6.0]   # 6 台配电柜中心 x
BUS_Y = [4.2, 4.5, 4.8]                          # A/B/C 三相母线 y
BUS_Z = 2.6                                       # 母线中心 z（底面 2.525，柜顶 2.2）
TRANS_X = [-4.5, -1.5, 1.5, 4.5]                 # 4 台变压器中心 x
BUSH_DX = [-0.7, 0.0, 0.7]                       # 每台 3 个套管 x 偏移

# ---------- 1. 母线排：3 根平行铜排，沿 x，12 x 0.08 x 0.15 m ----------
for i, y in enumerate(BUS_Y):
    add_box(f"Busbar_{i+1}", (12.0, 0.08, 0.15), (0.0, y, BUS_Z), MAT_COPPER, bevel=0.01)

# ---------- 2. 绝缘子支架：每台柜顶 × 每根母线 = 18 处，铜排不再悬空 ----------
# 每处：底板（柜顶 z=2.2）+ 瓷体（z 2.22~2.52）+ 伞裙 + 顶盖（贴母线底 2.525）
n_insulator = 0
for i, y in enumerate(BUS_Y):
    for j, x in enumerate(CABINET_X):
        add_box(f"InsulatorBase_{i+1}_{j+1}", (0.18, 0.18, 0.02), (x, y, 2.21), MAT_CLAMP)
        add_cylinder(f"Insulator_{i+1}_{j+1}", 0.055, 0.30, (x, y, 2.37), MAT_CERAMIC)
        add_cylinder(f"InsulatorShed_{i+1}_{j+1}", 0.095, 0.015, (x, y, 2.37), MAT_CERAMIC)
        add_box(f"InsulatorCap_{i+1}_{j+1}", (0.12, 0.12, 0.02), (x, y, 2.515), MAT_CLAMP)
        n_insulator += 1

# ---------- 3. 北墙顶电缆桥架：通长 12m + 两侧边唇 + 6 段盖板（分缝）+ 墙支架 ----------
add_box("CableTray", (12.0, 0.3, 0.06), (0.0, 4.8, 3.5), MAT_TRAY, bevel=0.01)
for dy in (-0.14, 0.14):
    add_box("CableTrayLip", (12.0, 0.02, 0.08), (0.0, 4.8 + dy, 3.57), MAT_TRAY)
for k in range(6):  # 盖板分 6 段，每段 1.94m，留 0.06 缝
    cx = -5.0 + k * 2.0
    add_box(f"CableTrayCover_{k+1}", (1.94, 0.26, 0.02), (cx, 4.8, 3.575), MAT_TRAY)
for bx in (-5.0, -3.0, -1.0, 1.0, 3.0, 5.0):  # 悬臂支架：北墙 y=5 连到桥架
    add_box(f"CableTrayBracket_{bx}", (0.06, 0.22, 0.06), (bx, 4.9, 3.5), MAT_CLAMP)
for cx in (-4.5, -1.5, 1.5, 4.5):  # 桥架内线卡（压住槽内线缆）
    add_box(f"CableTrayClamp_{cx}", (0.06, 0.32, 0.03), (cx, 4.8, 3.59), MAT_CLAMP)

# ---------- 4. 墙面线槽（水平）：北墙 1 条 + 东西墙各 1 条，带盖板分缝 ----------
add_box("WallTrunk_N", (15.0, 0.18, 0.25), (0.0, 4.9, 3.2), MAT_TRUNK, bevel=0.008)
for sx in (-6.0, -4.0, -2.0, 0.0, 2.0, 4.0, 6.0):  # 北墙盖板分缝条
    add_box(f"WallTrunkSeam_N_{sx}", (0.02, 0.20, 0.27), (sx, 4.9, 3.2), MAT_SEAM)
for sgn, tag in ((1, "E"), (-1, "W")):
    add_box(f"WallTrunk_{tag}", (0.18, 9.0, 0.25), (sgn * 7.9, 0.0, 3.2), MAT_TRUNK, bevel=0.008)
    for sy in (-4.0, -2.0, 0.0, 2.0, 4.0):  # 东西墙盖板分缝条
        add_box(f"WallTrunkSeam_{tag}_{sy}", (0.20, 0.02, 0.27), (sgn * 7.9, sy, 3.2), MAT_SEAM)

# ---------- 5. 墙面线槽（竖向）：东西墙 × 南北端共 4 根，地面到水平线槽 ----------
for sgn, tag in ((1, "E"), (-1, "W")):
    for sy, end in ((4.8, "N"), (-4.8, "S")):
        add_box(f"WallTrunkV_{tag}{end}", (0.2, 0.2, 3.5), (sgn * 7.9, sy, 1.75), MAT_TRUNK, bevel=0.008)
        for sz in (1.2, 2.4):  # 竖槽盖板分缝条
            add_box(f"WallTrunkVSeam_{tag}{end}_{sz}", (0.22, 0.22, 0.02), (sgn * 7.9, sy, sz), MAT_SEAM)

# ---------- 6. 柜顶到桥架的竖向线槽：每台柜 1 根 + 盖板缝 ----------
for i, x in enumerate(CABINET_X):
    add_box(f"RiserTrunk_{i+1}", (0.15, 0.15, 1.3), (x, 4.5, 2.85), MAT_TRUNK, bevel=0.008)
    add_box(f"RiserTrunkSeam_{i+1}", (0.17, 0.17, 0.02), (x, 4.5, 2.85), MAT_SEAM)

# ---------- 7. 南北向主桥架（馈线）：x=-3 / +3 各 1 条，北墙桥架 → 变压器排 ----------
# 吊杆到 z=6.0（顶板示意接天花结构），每条 3 根吊杆
for sx in (-3.0, 3.0):
    add_box(f"SpineTray_{sx}", (0.3, 7.3, 0.06), (sx, 1.15, 3.5), MAT_TRAY, bevel=0.01)
    for dx in (-0.14, 0.14):
        add_box(f"SpineTrayLip_{sx}_{dx}", (0.02, 7.3, 0.08), (sx + dx, 1.15, 3.57), MAT_TRAY)
    for k, cy in enumerate((-1.58, 0.24, 2.06, 3.88)):  # 盖板分 4 段
        add_box(f"SpineTrayCover_{sx}_{k+1}", (0.26, 1.76, 0.02), (sx, cy, 3.575), MAT_TRAY)
    for hy in (-2.0, 1.15, 4.3):
        add_cylinder(f"SpineTrayHanger_{sx}_{hy}", 0.02, 2.45, (sx, hy, 4.775), MAT_CLAMP)
        add_box(f"SpineTrayHangerPlate_{sx}_{hy}", (0.12, 0.12, 0.02), (sx, hy, 6.0), MAT_CLAMP)

# ---------- 8. 引下线缆：母线 → 每台配电柜，3 相 × 6 台 = 18 根 ----------
# 走线：母线底 (x, yb, 2.53) 垂下 → 弯向柜前 (x, 4.08, 2.20) 进柜顶，弯曲弧度由 AUTO 手柄给出
n_drop = 0
for j, x in enumerate(CABINET_X):
    for i, yb in enumerate(BUS_Y):
        add_cable(f"DropCable_C{j+1}_P{i+1}",
                  [(x, yb, 2.53), (x, yb, 2.40), (x, 4.18, 2.32), (x, 4.08, 2.20)],
                  0.03, PHASE_MATS[i])
        # 线卡固定：弯段中点处卡箍
        add_box(f"DropClamp_C{j+1}_P{i+1}", (0.10, 0.06, 0.04), (x, 4.12, 2.30), MAT_CLAMP)
        n_drop += 1

# ---------- 9. 馈线：主桥架 → 每台变压器，3 相 + 1 根黑色 PE = 16 根 ----------
# 走线：桥架内 (sx, -2.5, 3.52) 平行出线 → 套管上方 (tx+dx, -2.5, 3.45) 弯下 → 端子顶 3.16；
# PE 线落到变压器顶盖 (tx, -2.5, 2.68)
n_feeder = 0
for t, tx in enumerate(TRANS_X):
    sx = -3.0 if tx < 0 else 3.0
    for i, dx in enumerate(BUSH_DX):
        add_cable(f"FeederCable_T{t+1}_P{i+1}",
                  [(sx, -2.5, 3.52), (tx, -2.5, 3.52), (tx + dx, -2.5, 3.45), (tx + dx, -2.5, 3.16)],
                  0.035, PHASE_MATS[i])
        add_box(f"FeederClamp_T{t+1}_P{i+1}", (0.10, 0.10, 0.03), (tx + dx, -2.5, 3.32), MAT_CLAMP)
        n_feeder += 1
    add_cable(f"FeederCable_T{t+1}_PE",
              [(sx, -2.5, 3.52), (tx, -2.5, 3.52), (tx, -2.5, 3.0), (tx, -2.5, 2.68)],
              0.025, MAT_CABLE_K)
    n_feeder += 1

print(f"di-busbar counts: total={len(piece_objects)} busbars=3 insulators={n_insulator} "
      f"drop_cables={n_drop} feeder_cables={n_feeder}")

# ---------- 10. 线缆 CURVE 转 MESH + PBR 贴图固化 (2026-11-23) ----------
# 上一轮 .blend 里 34 根线缆已是 MESH；只改 .blend 不改 .py 的话重跑会恢复
# CURVE（且无 UV，贴图也丢）。本步在导出前把 34 根引下/馈线缆转成 MESH
# （名字、材质、倒角半径全部保留），转完再挂贴图、补 UV。
if cable_objs:
    bpy.ops.object.select_all(action="DESELECT")
    for ob in cable_objs:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = cable_objs[0]
    bpy.ops.object.convert(target="MESH")
    bpy.ops.object.select_all(action="DESELECT")
    n_mesh = sum(1 for ob in piece_objects if ob.type == "MESH")
    print("cables converted CURVE->MESH:", len(cable_objs),
          "piece MESH objects: %d/%d" % (n_mesh, len(piece_objects)))
    assert n_mesh == len(piece_objects), "cable convert failed"

# ---- PBR 贴图固化：把上一轮挂在 .blend 上的外部贴图写进脚本 ----
# color 图：assets/blender/tex/ 里的染色图（已按 SPEC §3 目标色染色，铜排
# #B87333、柜体灰绿系等）；rough/normal 图：assets/external/ 原图（CC0）。
# 节点只许 TexCoord→Mapping→Image Texture 直连 BSDF，不加 Hue/Sat/Mix，
# 否则 glTF 导出器不认。Base Color 默认值须置白、Roughness 置 1.0（贴图
# 本身带颜色与粗糙度），否则导出器会把旧纯色写成 baseColorFactor/
# roughnessFactor 与贴图二次相乘；Metallic 保持脚本原值。
# 没有 UV 的网格补 Smart UV Project（已有 UV 的不动）。
TEX_DIR = os.path.join(BASE, "assets/blender/tex")
EXT_DIR = os.path.join(BASE, "assets/external")
# 材质名: (tex/ 染色 color 图, external rough 图, external normal 图, Mapping 缩放)
PBR_TEXTURES = {
    "CopperBusbar": ("corrugated_iron_02__B87333.jpg",
        "polyhaven/corrugated_iron_02_rough_1k.jpg",
        "polyhaven/corrugated_iron_02_nor_gl_1k.jpg", (4.0, 1.0)),
    "CableClamp": ("corrugated_iron_02__8A8F94.jpg",
        "polyhaven/corrugated_iron_02_rough_1k.jpg",
        "polyhaven/corrugated_iron_02_nor_gl_1k.jpg", (1.0, 1.0)),
    "InsulatorCeramic": ("Plaster001__E8E8E8.jpg",
        "ambientcg/Plaster001/Plaster001_1K-JPG_Roughness.jpg",
        "ambientcg/Plaster001/Plaster001_1K-JPG_NormalGL.jpg", (1.0, 1.0)),
    "CableTray": ("white_stucco__C0C5C9.jpg",
        "polyhaven/white_stucco_rough_1k.jpg",
        "polyhaven/white_stucco_nor_gl_1k.jpg", (4.0, 1.0)),
    "Trunking": ("white_stucco__AEB4B8.jpg",
        "polyhaven/white_stucco_rough_1k.jpg",
        "polyhaven/white_stucco_nor_gl_1k.jpg", (2.0, 1.0)),
    "CoverSeam": ("concrete_wall_007__3A3F44.jpg",
        "polyhaven/concrete_wall_007_rough_1k.jpg",
        "polyhaven/concrete_wall_007_nor_gl_1k.jpg", (1.0, 1.0)),
    "Cable_Red": ("white_stucco__B03A2E.jpg",
        "polyhaven/white_stucco_rough_1k.jpg",
        "polyhaven/white_stucco_nor_gl_1k.jpg", (1.0, 1.0)),
    "Cable_Yellow": ("white_stucco__E8B400.jpg",
        "polyhaven/white_stucco_rough_1k.jpg",
        "polyhaven/white_stucco_nor_gl_1k.jpg", (1.0, 1.0)),
    "Cable_Green": ("white_stucco__2E7D32.jpg",
        "polyhaven/white_stucco_rough_1k.jpg",
        "polyhaven/white_stucco_nor_gl_1k.jpg", (1.0, 1.0)),
    "Cable_Black": ("concrete_wall_007__1A1A1A.jpg",
        "polyhaven/concrete_wall_007_rough_1k.jpg",
        "polyhaven/concrete_wall_007_nor_gl_1k.jpg", (1.0, 1.0)),
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
_ensure_uvs(piece_objects)

# ---------- 存 .blend（落盘优先） ----------
os.makedirs(os.path.dirname(BLEND_PATH), exist_ok=True)
os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
os.makedirs(os.path.dirname(PNG_PATH), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("blend saved:", BLEND_PATH, os.path.getsize(BLEND_PATH))

# ---------- 导出 GLB：只选本件 ----------
bpy.ops.object.select_all(action="DESELECT")
for obj in piece_objects:
    obj.select_set(True)
bpy.context.view_layer.objects.active = piece_objects[0]
bpy.ops.export_scene.gltf(
    filepath=GLB_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
)
print("glb exported:", GLB_PATH, os.path.getsize(GLB_PATH))

# ---------- 回读确认 ----------
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB_PATH)
imported = [o for o in bpy.data.objects if o not in before]
print(f"GLB re-import OK: {len(imported)} objects (expected {len(piece_objects)})")
assert len(imported) == len(piece_objects), \
    "glb reimport failed: expected %d, got %d" % (len(piece_objects), len(imported))
# 删掉回读副本 + 清孤儿数据，恢复干净场景
bpy.ops.object.select_all(action="DESELECT")
for ob in imported:
    ob.select_set(True)
bpy.ops.object.delete()
for _mesh in list(bpy.data.meshes):
    if _mesh.users == 0:
        bpy.data.meshes.remove(_mesh)
for _mat in list(bpy.data.materials):
    if _mat.users == 0:
        bpy.data.materials.remove(_mat)
for _img in list(bpy.data.images):
    # 回读导入的 .001 贴图是打包进来的孤儿（无使用者），不清除会随最终存盘
    # 混进 .blend（上一轮的 .blend1 残留即此类）；本件外链贴图有材质引用，不受影响
    if _img.users == 0:
        bpy.data.images.remove(_img)

# ---------- 光照/相机（SPEC §2；仅供 GitHub Actions 渲染用，本地默认不渲染） ----------
sun_data = bpy.data.lights.new(name="Sun", type="SUN")
sun_data.energy = 3.5
sun_data.use_shadow = True
sun = bpy.data.objects.new(name="Sun", object_data=sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(40), 0.0, math.radians(225))
world = bpy.data.worlds.new(name="World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.65, 0.78, 0.88, 1.0)
bg.inputs["Strength"].default_value = 1.0
cam_data = bpy.data.cameras.new(name="Camera")
cam_data.lens = 35
cam = bpy.data.objects.new(name="Camera", object_data=cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
cam.location = (9.5, -5.5, 6.0)
target = Vector((0.0, 4.6, 2.9))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100
scene.eevee.taa_render_samples = 16
scene.render.filepath = PNG_PATH
scene.render.image_settings.file_format = "PNG"
if os.environ.get("DI_BUSBAR_RENDER") == "1":
    bpy.ops.render.render(write_still=True)
    print("Preview saved:", PNG_PATH, "exists:", os.path.exists(PNG_PATH),
          "size:", os.path.getsize(PNG_PATH) if os.path.exists(PNG_PATH) else 0)
else:
    print("Render skipped locally (set DI_BUSBAR_RENDER=1 to render on GitHub Actions)")

# ---------- 最终存盘 + 清理 .blend1 ----------
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
blend1 = BLEND_PATH + "1"
if os.path.exists(blend1):
    os.remove(blend1)

print("DONE di-busbar")
