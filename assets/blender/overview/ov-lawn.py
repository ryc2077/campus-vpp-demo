# ov-lawn v3: 草坪花坛（总览件）——密度版重做（只改密度和分布）
# v3 改动（用户反馈 v2 草太稀）：草丛密度从 2 丛/m2（0.5 m2/丛，4500 丛）
#   提到 10 丛/m2（0.1 m2/丛），三块草皮总计 22500 丛（5 倍），铺满整块草皮；
#   6 种绿色变体，丛高 0.15-0.35m 随机，丛幅随机；分布加簇状聚集（60% 丛落在簇心
#   半径 1.5m 内，另 40% 均匀撒满全块），不均匀成地毯；花坛土面/灌木球/底板
#   几何位置照旧，只加密草。三角面预算 <15 万（实测见运行日志）。
#   渲染全部走 GitHub Actions，本地不渲染：本脚本只建模 + 存 .blend + 导出 .glb + 回读确认。
#   （磁盘上曾有一份未跑通的 v4 草稿头注释，密度参数仍是 v2 的 0.5，已按本任务 v3 规约覆盖。）
# 2026-11-23 池塘返工：主撒点排除池塘水面椭圆（Blender 中心 (82,-78)，
#   水面 rx11/ry8 + 1m 安全边距），只留环形草坪带；拼装不再下移
#   Lawn_Pond_Grass_*（见 scenes/overview.py，旧 -0.5m 下移曾把
#   18,863 叶全埋进地下）。另两片草坪与真草素材（8,140 株）不动。
# R2-T1b 2026-11-24 操场收界：禁入椭圆跟新跑道走——中心 (-62,-25)、
#   长轴南北向、外椭圆 rx28/ry40 +1m（旧 (-80,-25) rx40/ry28 已废）。
# R2-T18 2026-11-24 草地重铺：见文件末尾 R2-T18 段（色带底板 + tevy 高草）。
# Blender 坐标 x 向东、y 向北、z 向上，单位米
# 内容：3 块草地（实体草丛铺满）、南门广场两侧 4 个花坛、20 个灌木球
# v3 改动：草地底板/土面/灌木/花/草丛加程序化噪波纹理（颜色+粗糙度+轻微凹凸），
#   草丛密度 2 丛/m2（0.5 m2/丛，约 4500 丛）；几何、位置、相机照 v2
# v2 改动：草叶是 3-5 片交叉细三角面组成的草丛，3 种原型，
#   按颜色/草地合并成 9 个网格导出；预览机位改低改近，不再高空俯视
# 不做树木 / 球场 / 铺装
import bpy
import math
import os
import random
import numpy as np
from mathutils import Vector, Matrix

BLEND_PATH = os.path.expanduser(
    "~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot/assets/blender/overview/ov-lawn.blend")
GLB_PATH = os.path.expanduser(
    "~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot/assets/models/ov-lawn.glb")
PNG_PATH = os.path.expanduser(
    "~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot/screenshots/blender/ov-lawn.png")


def srgb_to_linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_to_linear(h):
    h = h.lstrip("#")
    return tuple(srgb_to_linear(int(h[i:i + 2], 16)) for i in (0, 2, 4))


def make_mat(name, hex_color, roughness=0.9):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*hex_to_linear(hex_color), 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    return m


def add_noise_tex(mat, dark_hex, light_hex, noise_scale, detail=4.0,
                  rough_lo=0.85, rough_hi=1.0, bump_strength=0.0,
                  bump_dist=0.02):
    """程序化噪波纹理：颜色深浅不均 + 粗糙度变化 + 可选轻微凹凸。
    用 Object 坐标（米），noise_scale 为每米频率：草地斑块 ~1-2m、
    土壤颗粒 ~0.05m、灌木叶面 ~0.15m。只改节点，不动几何。"""
    nt = mat.node_tree
    nodes = nt.nodes
    links = nt.links
    bsdf = nodes["Principled BSDF"]
    tex = nodes.new("ShaderNodeTexCoord")
    tex.location = (-650, 250)
    noise = nodes.new("ShaderNodeTexNoise")
    noise.location = (-450, 250)
    noise.inputs["Scale"].default_value = noise_scale
    noise.inputs["Detail"].default_value = detail
    noise.inputs["Roughness"].default_value = 0.7
    ramp_c = nodes.new("ShaderNodeValToRGB")
    ramp_c.location = (-220, 250)
    ramp_c.color_ramp.elements[0].position = 0.25
    ramp_c.color_ramp.elements[0].color = (*hex_to_linear(dark_hex), 1.0)
    ramp_c.color_ramp.elements[1].position = 0.75
    ramp_c.color_ramp.elements[1].color = (*hex_to_linear(light_hex), 1.0)
    ramp_r = nodes.new("ShaderNodeValToRGB")
    ramp_r.location = (-220, -50)
    ramp_r.color_ramp.elements[0].position = 0.2
    ramp_r.color_ramp.elements[0].color = (rough_lo, rough_lo, rough_lo, 1.0)
    ramp_r.color_ramp.elements[1].position = 0.8
    ramp_r.color_ramp.elements[1].color = (rough_hi, rough_hi, rough_hi, 1.0)
    links.new(tex.outputs["Object"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp_c.inputs["Fac"])
    links.new(noise.outputs["Fac"], ramp_r.inputs["Fac"])
    links.new(ramp_c.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(ramp_r.outputs["Color"], bsdf.inputs["Roughness"])
    if bump_strength > 0.0:
        bump = nodes.new("ShaderNodeBump")
        bump.location = (-220, -250)
        bump.inputs["Strength"].default_value = bump_strength
        bump.inputs["Distance"].default_value = bump_dist
        links.new(noise.outputs["Fac"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def add_color_var(mat, dark_hex, light_hex, noise_scale, detail=3.0):
    """仅颜色深浅不均（花瓣用），不改粗糙度/法线。"""
    nt = mat.node_tree
    nodes = nt.nodes
    links = nt.links
    bsdf = nodes["Principled BSDF"]
    tex = nodes.new("ShaderNodeTexCoord")
    tex.location = (-650, 250)
    noise = nodes.new("ShaderNodeTexNoise")
    noise.location = (-450, 250)
    noise.inputs["Scale"].default_value = noise_scale
    noise.inputs["Detail"].default_value = detail
    noise.inputs["Roughness"].default_value = 0.7
    ramp_c = nodes.new("ShaderNodeValToRGB")
    ramp_c.location = (-220, 250)
    ramp_c.color_ramp.elements[0].position = 0.3
    ramp_c.color_ramp.elements[0].color = (*hex_to_linear(dark_hex), 1.0)
    ramp_c.color_ramp.elements[1].position = 0.7
    ramp_c.color_ramp.elements[1].color = (*hex_to_linear(light_hex), 1.0)
    links.new(tex.outputs["Object"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp_c.inputs["Fac"])
    links.new(ramp_c.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def _attach_grass_color(mat, key):
    """草叶丢色修复：Noise->ColorRamp 不进 glTF（导出后既无 baseColorFactor
    也无贴图，Godot 里是白色——教室/配电房丢色同根因，另路已按此修）。
    改挂 Grass_<key>_color.png（绿斑纹理，均值即该色 SPEC 绿），保留双面。"""
    texdir = os.path.join(os.path.dirname(BLEND_PATH), "ov-lawn_textures")
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    out = nt.nodes["Material Output"]
    for n in list(nt.nodes):
        if n not in (bsdf, out):
            nt.nodes.remove(n)
    for link in list(nt.links):
        if link.to_node is bsdf:
            nt.links.remove(link)
    bsdf.inputs["Base Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.95
    p = os.path.join(texdir, "Grass_%s_color.png" % key)
    img = bpy.data.images.load(p)
    img.colorspace_settings.name = "sRGB"
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = img
    nt.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def box(name, center, size, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    o = bpy.context.active_object
    o.name = name
    o.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    return o


def sphere(name, center, r, mat, scale_z=1.0):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8,
                                         radius=r, location=center)
    o = bpy.context.active_object
    o.name = name
    if scale_z != 1.0:
        o.scale = (1.0, 1.0, scale_z)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    return o


# ---- 清空场景 ----
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for m in list(bpy.data.materials):
    bpy.data.materials.remove(m)

mat_lawn = make_mat("Lawn_Green", "#69B45E", 0.95)
# 草地底板：深绿/浅绿斑块（约 1-2m 一块）+ 粗糙度 0.8-1.0 + 轻微凹凸
add_noise_tex(mat_lawn, "#3F7A33", "#7FC46A", noise_scale=0.9, detail=4.0,
              rough_lo=0.80, rough_hi=1.0, bump_strength=0.25, bump_dist=0.02)
mat_border = make_mat("Bed_Border", "#C8C8C8", 0.85)
mat_soil = make_mat("Bed_Soil", "#5A4632", 1.0)
# 花坛土面：土褐色颗粒（约 5cm 颗粒）+ 粗糙度 0.9-1.0 + 轻微凹凸
add_noise_tex(mat_soil, "#3E2E1E", "#7A6248", noise_scale=18.0, detail=5.0,
              rough_lo=0.90, rough_hi=1.0, bump_strength=0.35, bump_dist=0.015)
mat_flower_r = make_mat("Flower_Red", "#C0392B", 0.7)
mat_flower_y = make_mat("Flower_Yellow", "#E8B400", 0.7)
mat_flower_p = make_mat("Flower_Pink", "#E8A0B0", 0.7)
# 花瓣：仅颜色深浅不均
add_color_var(mat_flower_r, "#8E2418", "#D95A45", noise_scale=8.0)
add_color_var(mat_flower_y, "#B98A00", "#F5C93A", noise_scale=8.0)
add_color_var(mat_flower_p, "#C47A8E", "#F2C2CE", noise_scale=8.0)
mat_shrub = make_mat("Shrub_DarkGreen", "#3E6B34", 0.95)
# 灌木球：深浅绿叶面（约 15cm 一团）+ 粗糙度 0.85-1.0 + 轻微凹凸
add_noise_tex(mat_shrub, "#2A4F26", "#5A8A48", noise_scale=6.0, detail=4.0,
              rough_lo=0.85, rough_hi=1.0, bump_strength=0.3, bump_dist=0.02)
flower_mats = [mat_flower_r, mat_flower_y, mat_flower_p]

# 草丛六色（深绿→黄绿 6 种变体，混搭比例：中间绿为主，深/浅为辅）
# 2026-11-24 F4 收尾：Lime/YellowGreen 两档亮黄绿压暗 ×0.80（贴图
#   Grass_Lime/YellowGreen_color.png 均值同步改，见下；_attach_grass_color
#   以贴图为准，此处 hex 只作初始值、渲染以贴图为准）
GRASS_COLORS = [
    ("DarkGreen", "#3E6B2E", 0.12),
    ("Dark", "#4E8A3F", 0.20),
    ("Green", "#69B45E", 0.28),
    ("Light", "#7FC46A", 0.18),
    ("YellowGreen", "#6E863B", 0.14),
    ("Lime", "#869B4B", 0.08),
]
# 草丛六色深浅对（仅轻微颜色不均，混搭比例不变）
GRASS_VAR = {
    "DarkGreen": ("#2E5222", "#4E7A3A"),
    "Dark": ("#3A6B2E", "#5F9C4C"),
    "Green": ("#4E8A3F", "#82C46E"),
    "Light": ("#64A854", "#97D484"),
    "YellowGreen": ("#6E8A38", "#A8C25E"),
    "Lime": ("#8AA84A", "#C2D478"),
}
grass_mats = {k: make_mat("Grass_" + k, hx, 0.95) for k, hx, _ in GRASS_COLORS}
for k, m in grass_mats.items():
    _attach_grass_color(m, k)
    # 草叶是单面三角面片：关闭背面剔除，glTF 导出 doubleSided=true；
    # 拼装进 Godot 时草材质仍须设为双面（关闭背面剔除），否则侧面看草会消失
    m.use_backface_culling = False
color_weights = [w for _, _, w in GRASS_COLORS]
color_keys = [k for k, _, _ in GRASS_COLORS]

objs = []

# ---- 大面积草地：3 块，厚 0.05m（位置尺寸照旧版）----
lawns = [
    ("Lawn_TeachSouth", (-20, 5), (60, 20)),    # 教学楼南侧草坪
    ("Lawn_GateNorth", (0, -80), (40, 15)),     # 南门广场北侧草坪
    ("Lawn_Pond", (82, -78), (25, 18)),         # 池塘周边草坪
]
for name, (cx, cy), (sx, sy) in lawns:
    o = box(name, (cx, cy, 0.025), (sx, sy, 0.05), mat_lawn)
    bev = o.modifiers.new("Bevel", "BEVEL")
    bev.width = 0.02
    bev.segments = 1
    objs.append(o)

# ---- 草丛原型：每丛 3-5 片交叉细三角面（单面三角，材质不剔除背面）
# 每片：底边半宽 w、高 h、顶端沿片面方向 lean；azimuth 为片面绕 Z 的朝向
# 原型 A：高窄 4 片，h=0.30；原型 B：矮宽 3 片，h=0.20；原型 C：中高 5 片，h=0.26
# 原型 D：高瘦 5 片，h=0.32；原型 E：矮胖 4 片，h=0.18
# 叠加 z 缩放 0.75-1.05 后丛高 0.15-0.35m（原型最高片 0.33m×1.05≈0.35m，矮丛 0.20m×0.75=0.15m）
def blade_verts(az_deg, half_w, height, lean):
    a = math.radians(az_deg)
    ca, sa = math.cos(a), math.sin(a)

    def rot(p):
        x, y, z = p
        return (x * ca - y * sa, x * sa + y * ca, z)

    return [rot((-half_w, 0.0, 0.0)),
            rot((half_w, 0.0, 0.0)),
            rot((lean, 0.0, height))]


PROTOTYPES = [
    # (name, [(azimuth, half_w, height, lean), ...])
    ("Tuft_Tall", [(0, 0.035, 0.30, 0.06), (60, 0.032, 0.28, -0.05),
                   (120, 0.035, 0.31, 0.04), (30, 0.030, 0.26, -0.06)]),
    ("Tuft_Short", [(0, 0.065, 0.20, 0.05), (90, 0.060, 0.21, -0.04),
                    (45, 0.062, 0.18, 0.06)]),
    ("Tuft_Mid", [(0, 0.045, 0.26, 0.05), (36, 0.042, 0.24, -0.06),
                  (72, 0.045, 0.27, 0.04), (108, 0.040, 0.25, -0.05),
                  (144, 0.043, 0.23, 0.06)]),
    ("Tuft_Slim", [(0, 0.028, 0.32, 0.07), (45, 0.026, 0.30, -0.06),
                   (90, 0.028, 0.33, 0.05), (135, 0.025, 0.29, -0.05),
                   (20, 0.027, 0.31, 0.06)]),
    ("Tuft_Bushy", [(0, 0.070, 0.18, 0.06), (70, 0.068, 0.19, -0.05),
                    (140, 0.072, 0.17, 0.05), (35, 0.065, 0.20, -0.06)]),
]
# 原型共享顶点数据：展平成每原型一个 (verts, faces) 列表
PROTO_MESHES = []
for _pname, blades in PROTOTYPES:
    verts, faces = [], []
    for b in blades:
        base = len(verts)
        verts.extend(blade_verts(*b))
        faces.append((base, base + 1, base + 2))
    PROTO_MESHES.append((verts, faces))
    print(f"PROTO {_pname}: {len(blades)} blades, {len(verts)} verts, "
          f"height {max(v[2] for v in verts):.2f}m")

# ---- 实体草丛：按 (草地, 颜色) 直接合并成网格，不产生几千个对象 ----
# 密度 10 丛/m2（0.1 m2/丛，v2 的 5 倍）；分布：60% 丛聚在簇心周围（簇心按约
# 12 m2 一个均匀撒在整块草皮上，高斯偏移 sigma=0.9m，约 2/3 落在簇心 1.5m 内），
# 40% 全块均匀随机，保证任何位置都不裸露；丛位钳制在草皮内缩 0.15m 范围内。
random.seed(20261122)
TUFTS_PER_M2 = 10.0  # 丛/m2（v2 为 2 丛/m2）
CLUSTER_FRAC = 0.60
CLUSTER_SIGMA = 0.9  # m，簇内散布标准差
# 池塘排除（Blender 坐标）：水面椭圆中心 (82,-78)，rx=11、ry=8（SPEC §4，
# campus.json pond Godot [82,78]）；留 1m 安全边距，与本文件 _blocked()
# 的池塘排除 (12,9) 一致。环形带面积 = 草坪矩形 − 边距椭圆。
POND_CX, POND_CY = 82.0, -78.0
POND_RX, POND_RY = 12.0, 9.0  # 水面 rx11/ry8 + 1m 边距
grass_counts = {}
target_total = 0
for lawn_name, (cx, cy), (sx, sy) in lawns:
    area = sx * sy
    n_tufts = int(area * TUFTS_PER_M2)
    if lawn_name == "Lawn_Pond":
        # 环带目标丛数 = 环带面积 × 密度（旧版按整块矩形算 4500 丛，其中
        # 68.4% 落在水面椭圆内；且簇心内缩 1m、簇生点更难落进环带，只靠
        # 跳过会只剩 778 丛（29.5 叶/m2），故拒绝采样补满到环带目标）。
        n_tufts = int((area - math.pi * POND_RX * POND_RY) * TUFTS_PER_M2)
    target_total += n_tufts
    # 簇心：约每 12 m2 一个，覆盖整块草皮
    n_clusters = max(8, int(area / 12))
    clusters = [(cx + random.uniform(-sx / 2 + 1.0, sx / 2 - 1.0),
                 cy + random.uniform(-sy / 2 + 1.0, sy / 2 - 1.0))
                for _ in range(n_clusters)]
    # 每色一个 (verts, faces) 累积器
    buckets = {k: ([], []) for k in color_keys}
    tufts_per_color = {k: 0 for k in color_keys}
    # 池塘草坪拒绝采样直到种满环带目标（密度与另两片一致）；其余草坪
    # 每抽必中，while 与原 for 消耗的随机流完全相同。
    placed_count = 0
    tries = 0
    while placed_count < n_tufts and tries < n_tufts * 30:
        tries += 1
        if random.random() < CLUSTER_FRAC:
            ccx, ccy = random.choice(clusters)
            px = ccx + random.gauss(0, CLUSTER_SIGMA)
            py = ccy + random.gauss(0, CLUSTER_SIGMA)
        else:
            px = cx + random.uniform(-sx / 2 + 0.15, sx / 2 - 0.15)
            py = cy + random.uniform(-sy / 2 + 0.15, sy / 2 - 0.15)
        # 钳制在草皮内，避免簇偏移出界
        px = max(cx - sx / 2 + 0.15, min(cx + sx / 2 - 0.15, px))
        py = max(cy - sy / 2 + 0.15, min(cy + sy / 2 - 0.15, py))
        proto_idx = random.randrange(len(PROTOTYPES))
        pverts, pfaces = PROTO_MESHES[proto_idx]
        ckey = random.choices(color_keys, weights=color_weights, k=1)[0]
        verts, faces = buckets[ckey]
        # 随机旋转 + 缩放（xy 0.85-1.2，z 0.75-1.05：原型丛高 0.20-0.33m
        #  → 实际丛高 0.15-0.35m，丛幅随机）
        rot = Matrix.Rotation(random.uniform(0, math.tau), 4, 'Z')
        scl = Matrix.Diagonal((random.uniform(0.85, 1.2),
                               random.uniform(0.85, 1.2),
                               random.uniform(0.75, 1.05),
                               1.0))
        loc = Matrix.Translation((px, py, 0.05))  # 扎在草地底板顶面
        mat = loc @ rot @ scl
        # 池塘排除：落在水面椭圆（含 1m 边距）内的丛跳过不种，只留环形带。
        # 检查放在全部随机抽取之后；拒绝采样会多消耗随机数，下游花坛抖动
        # 随之重抽（仍在 ±0.15m 规格内），其余两片草坪与真草素材不受影响。
        # 跳过的丛不计入 tufts_per_color，且不计入 placed_count，while
        # 循环会继续抽，直到种满环带目标丛数。
        if lawn_name == "Lawn_Pond" and (
                (px - POND_CX) / POND_RX) ** 2 + (
                (py - POND_CY) / POND_RY) ** 2 <= 1.0:
            continue
        tufts_per_color[ckey] += 1
        placed_count += 1
        base = len(verts)
        verts.extend(mat @ Vector(v) for v in pverts)
        faces.extend(tuple(base + i for i in f) for f in pfaces)
    if placed_count < n_tufts:
        print(f"WARNING {lawn_name}: only {placed_count}/{n_tufts} tufts "
              f"after {tries} tries")
    for ckey in color_keys:
        verts, faces = buckets[ckey]
        if not verts:
            continue
        mesh = bpy.data.meshes.new(f"{lawn_name}_Grass_{ckey}")
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        # 草叶 UV：按世界坐标 0.5m 一重复（贴图绿斑随位置变化，不整片同色）
        uvl = mesh.uv_layers.new(name="UVMap")
        _co = np.empty(len(mesh.vertices) * 3, dtype=np.float64)
        mesh.vertices.foreach_get("co", _co)
        _co = _co.reshape(-1, 3)
        _vi = np.empty(len(mesh.loops), dtype=np.int32)
        mesh.loops.foreach_get("vertex_index", _vi)
        _uv = np.empty(len(mesh.loops) * 2, dtype=np.float64)
        _uv[0::2] = _co[_vi, 0] * 2.0
        _uv[1::2] = _co[_vi, 1] * 2.0
        uvl.data.foreach_set("uv", _uv)
        o = bpy.data.objects.new(f"{lawn_name}_Grass_{ckey}", mesh)
        bpy.context.collection.objects.link(o)
        o.data.materials.append(grass_mats[ckey])
        objs.append(o)
        grass_counts[f"{lawn_name}_{ckey}"] = tufts_per_color[ckey]
    total = sum(len(buckets[k][1]) for k in color_keys)
    placed = sum(tufts_per_color.values())
    extra = ""
    if lawn_name == "Lawn_Pond":
        ring = area - math.pi * POND_RX * POND_RY
        extra = (f", ring area {ring:.1f}m2, placed density "
                 f"{total / ring:.1f} blades/m2")
    print(f"GRASS {lawn_name}: {placed}/{n_tufts} tufts placed, {total} tris, "
          f"area {area:.0f}m2 ({TUFTS_PER_M2:.1f} tufts/m2, "
          f"{n_clusters} clusters){extra}")

print(f"GRASS TOTAL: {sum(grass_counts.values())}/{target_total} tufts placed, "
      f"18 merged meshes (3 lawns x 6 colors), tuft height 0.15-0.35m")

# ---- 花坛：南门广场两侧各 2 个，6x2m（照旧版）----
beds = [
    ("Bed_W1", (-14, -86)),
    ("Bed_W2", (-14, -95)),
    ("Bed_E1", (14, -86)),
    ("Bed_E2", (14, -95)),
]
for name, (cx, cy) in beds:
    border = box(name + "_Border", (cx, cy, 0.15), (6.0, 2.0, 0.30), mat_border)
    bev = border.modifiers.new("Bevel", "BEVEL")
    bev.width = 0.03
    bev.segments = 1
    objs.append(border)
    soil = box(name + "_Soil", (cx, cy, 0.28), (5.6, 1.6, 0.10), mat_soil)
    objs.append(soil)
    # 坛内花丛：小球簇，约 20 朵，5 列 x 4 行，轻微随机偏移
    n = 0
    for ix in range(5):
        for iy in range(4):
            fx = cx - 2.2 + ix * 1.1 + random.uniform(-0.15, 0.15)
            fy = cy - 0.6 + iy * 0.4 + random.uniform(-0.08, 0.08)
            fz = 0.42 + random.uniform(0.0, 0.06)
            f = sphere(f"{name}_Flower_{n:02d}", (fx, fy, fz), 0.15,
                       flower_mats[(ix + iy) % 3])
            objs.append(f)
            n += 1

# ---- 灌木球：20 个，深绿 r=0.5m，沿步道两侧（照旧版）----
shrub_spots = [
    # 教学楼南侧草坪南缘步道
    (-45, -7), (-35, -7), (-25, -7), (-15, -7), (-5, -7), (5, -7),
    # 南门广场两侧步道
    (-22, -70), (-22, -80), (-22, -90), (-22, -100),
    (22, -70), (22, -80), (22, -90), (22, -100),
    # 池塘周边
    (68, -70), (68, -86), (96, -70), (96, -86),
    # 楼间绿地两点
    (-50, 16), (30, 16),
]
assert len(shrub_spots) == 20, len(shrub_spots)
for i, (sx, sy) in enumerate(shrub_spots):
    s = sphere(f"Shrub_{i:02d}", (sx, sy, 0.42), 0.5, mat_shrub, scale_z=0.85)
    objs.append(s)

print(f"OBJECTS: {len(objs)} (lawns 3, grass meshes 18, beds 4+4 soil, "
      f"flowers 80, shrubs 20)")

# ---- 光照：太阳 3.5，自西南，仰角约 50 度 ----
sun_data = bpy.data.lights.new("Sun", type="SUN")
sun_data.energy = 3.5
sun_data.use_shadow = True
sun = bpy.data.objects.new("Sun", sun_data)
bpy.context.collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), 0, math.radians(225))

# ---- 世界背景：淡蓝纯色 ----
world = bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.65, 0.78, 0.88, 1.0)
bg.inputs["Strength"].default_value = 1.0

# ---- 相机：低角度近景，35° 俯角贴近教学楼南侧草坪，看草叶高度与疏密 ----
cam_data = bpy.data.cameras.new("Camera")
cam_data.type = "PERSP"
cam_data.lens = 28
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera = cam
cam.location = (-23.2, -0.4, 6.3)  # 距目标约 11m，俯角约 35°
target = Vector((-16.0, 5.0, 0.0))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
print(f"CAMERA loc={tuple(round(v, 1) for v in cam.location)} "
      f"target={tuple(target)} pitch~35deg")

# ---- 渲染设置：Eevee，640x360，16 采样（仅供 GitHub Actions 渲染用，本地不渲染） ----
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100
scene.eevee.taa_render_samples = 16
scene.render.filepath = PNG_PATH

# ---------- 烘焙程序化纹理为图片 (照抄 dist/di-walls.py 已验证做法) ----------
# glTF 无法导出 Noise 程序化节点: 只烘焙地面基底材质 (草地底板/花坛边框/
# 花坛土面/花瓣/灌木球), Cycles CPU (samples 4) 烘焙 color/rough/normal
# 三张 1024px 图 (diffuse 只取 color 通道, 不带光照; margin 16px),
# 再重建材质为图片纹理节点。
# 草叶 6 色材质 (Grass_*) 不烘焙: 22500 丛实例化草叶逐叶烘焙太慢,
# 且草叶是无 UV 的单面三角面片, 保持程序化绿色深浅变化。
import time
TEX_DIR = os.path.join(os.path.dirname(BLEND_PATH), "ov-lawn_textures")
os.makedirs(TEX_DIR, exist_ok=True)
_bake_scene = bpy.context.scene
_bake_t0 = time.time()


def _ensure_uv(ob):
    me = ob.data
    if me is None or not hasattr(me, "uv_layers") or len(me.uv_layers) > 0:
        return
    me.uv_layers.new(name="UVMap")
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.02)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    print("uv added:", ob.name)


def _pack_uvs(mat_objs):
    """把同材质各对象的 UV 分别缩放到一张 1024 图里的不重叠瓦片 (网格排布,
    瓦片间留 32px 间隙, 容纳两侧各 16px 烘焙 margin)。立方体默认 UV 是每面
    0~1 全图重叠, 不分瓦片时同一纹素会被每个对象反复烘焙, 对象越多越慢
    (128 个缝线对象曾让一遍烘焙超过 1 小时); 分瓦片后每纹素只烘焙一次。
    只改 UV, 不动几何/配色/位置; 导出 GLB 时 UV 随贴图一起走, Godot 采样正确。"""
    n = len(mat_objs)
    cols = int(math.ceil(math.sqrt(n)))
    rows = int(math.ceil(n / cols))
    gap = 32.0 / 1024.0  # 瓦片间隙 (UV 单位)
    su = 1.0 / cols - gap
    sv = 1.0 / rows - gap
    for idx, ob in enumerate(mat_objs):
        u_off = (idx % cols) / cols + gap / 2.0
        v_off = (idx // cols) / rows + gap / 2.0
        uv = ob.data.uv_layers.active
        if uv is None:
            continue
        for luv in uv.data:
            u, v = luv.uv
            luv.uv = (u * su + u_off, v * sv + v_off)
    print("uv packed:", len(mat_objs), "objects into", cols, "x", rows, "tiles")


def _bake_images(mat, mat_objs, color_size=1024):
    nt = mat.node_tree
    imgs = {}
    specs = [("color", 'DIFFUSE', color_size, 'sRGB'),
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


def _load_baked(mat):
    """复用已烘焙 PNG（上次跑的烘焙约 16 分钟）：3 张都存在且 >1KB 才复用，
    否则返回 None 走烘焙。UV 打包是确定性的（同对象顺序），复用贴图对得上。"""
    out = {}
    for key, cs in (("color", "sRGB"), ("rough", "Non-Color"), ("normal", "Non-Color")):
        p = os.path.join(TEX_DIR, "%s_%s.png" % (mat.name, key))
        if not (os.path.exists(p) and os.path.getsize(p) > 1000):
            return None
        img = bpy.data.images.load(p)
        img.colorspace_settings.name = cs
        out[key] = img
    return out


_BAKE_MATS = {mat_lawn, mat_border, mat_soil, mat_shrub} | set(flower_mats)
_by_mat = {}
for _ob in objs:
    _m = _ob.data.materials[0]
    if _m in _BAKE_MATS:
        _by_mat.setdefault(_m, []).append(_ob)
_baked = {}
for _mat, _m_objs in _by_mat.items():
    for _ob in _m_objs:
        _ensure_uv(_ob)
    _pack_uvs(_m_objs)
    _loaded = _load_baked(_mat)
    if _loaded is not None:
        _baked[_mat.name] = _loaded
        print("bake reused:", _mat.name)
    else:
        _baked[_mat.name] = _bake_images(_mat, _m_objs)
for _mat in _by_mat:
    _rebuild_with_images(_mat, _baked[_mat.name])
print("bake done, ground materials rebuilt with image textures, "
      "grass now textured, elapsed %.1fs" % (time.time() - _bake_t0))

# ---------- 新增草区（返工）：下载的真草素材实例化 ----------
# 路线：Render-a-House 草叶 alpha 贴图做交叉面片（MASK 镂空）+ 两个下载
# 草丛模型（RAH 草坪块 join 成 1 mesh、3DAssets 高草丛）作点缀；
# tevy 野草丛因 meshopt 压缩、Blender 4.2 导不进，已跳过（见汇报）。
# 已有的 22500 丛程序化草叶（v3）按“已手捏不返工”保留，只修丢色。
# 草区：跑道外环、环路路缘、南门广场南沿；已有 3 块草坪与楼体/道路/
# 池塘/停车场/充电区均排除，不重叠。采样用独立 Random(20261123)，
# 在所有既有 random 消耗之后取用，既有草坪/花坛/灌木布局位不变。
import random as _random
GRASS_DIR = os.path.expanduser(
    "~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot/assets/external/grass")
GRASS_STRIP_PNG = os.path.join(GRASS_DIR, "renderahouse-grass",
                               "grass-side-colour.png")

# alpha 交叉面片材质：贴图 RGB 进 Base Color，Alpha 经 ROUND 数学节点
# 进 Alpha（导出器据此判 MASK、cutoff 0.5）；贴图打包进 .blend，
# Render-a-House 文件不单独分发。
mat_grass_alpha = bpy.data.materials.new("Grass_AlphaStrip")
mat_grass_alpha.use_nodes = True
_nt = mat_grass_alpha.node_tree
_bsdf = _nt.nodes["Principled BSDF"]
_bsdf.inputs["Roughness"].default_value = 0.9
_bsdf.inputs["Metallic"].default_value = 0.0
_tex = _nt.nodes.new("ShaderNodeTexImage")
_img = bpy.data.images.load(GRASS_STRIP_PNG)
_img.colorspace_settings.name = "sRGB"
_img.pack()
_tex.image = _img
_tex.extension = "REPEAT"
_nt.links.new(_tex.outputs["Color"], _bsdf.inputs["Base Color"])
_rnd = _nt.nodes.new("ShaderNodeMath")
_rnd.operation = "ROUND"
_nt.links.new(_tex.outputs["Alpha"], _rnd.inputs[0])
_nt.links.new(_rnd.outputs["Value"], _bsdf.inputs["Alpha"])
mat_grass_alpha.use_backface_culling = False


def _alpha_tuft_mesh():
    """交叉面片草丛母版：2 片 0.8x0.22m 交叉面，UV 0-1 整张草叶条。"""
    verts = [(-0.4, 0, 0), (0.4, 0, 0), (0.4, 0, 0.22), (-0.4, 0, 0.22),
             (0, -0.4, 0), (0, 0.4, 0), (0, 0.4, 0.22), (0, -0.4, 0.22)]
    faces = [(0, 1, 2, 3), (4, 5, 6, 7)]
    mesh = bpy.data.meshes.new("GrassAlpha_Tuft")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    uvl = mesh.uv_layers.new(name="UVMap")
    for li, uv in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)] * 2):
        uvl.data[li].uv = uv
    mesh.materials.append(mat_grass_alpha)
    return mesh


def _recenter_mesh(mesh):
    """把 mesh 顶点移到包围盒 XY 中心、Z 底 = 0，便于按采样点摆放实例。"""
    n = len(mesh.vertices)
    co = np.empty(n * 3, dtype=np.float64)
    mesh.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    cx = (co[:, 0].min() + co[:, 0].max()) / 2
    cy = (co[:, 1].min() + co[:, 1].max()) / 2
    co[:, 0] -= cx
    co[:, 1] -= cy
    co[:, 2] -= co[:, 2].min()
    mesh.vertices.foreach_set("co", co.ravel())


def _import_clump_meshes():
    """导入下载的草丛模型，只留 mesh 数据块（源对象随后删除，不进导出）。"""
    out = {}
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(GRASS_DIR, "renderahouse-grass.glb"))
    new = [o for o in bpy.context.scene.objects if o not in before and o.type == "MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for o in new:
        o.select_set(True)
    bpy.context.view_layer.objects.active = new[0]
    bpy.ops.object.join()
    joined = bpy.context.active_object
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    _recenter_mesh(joined.data)
    out["rah"] = joined.data
    bpy.data.objects.remove(joined, do_unlink=True)
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(GRASS_DIR, "3dassets-tall-grass-clump.glb"))
    new = [o for o in bpy.context.scene.objects if o not in before and o.type == "MESH"]
    tall = new[0]
    bpy.ops.object.select_all(action="DESELECT")
    tall.select_set(True)
    bpy.context.view_layer.objects.active = tall
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    _recenter_mesh(tall.data)
    out["tall"] = tall.data
    bpy.data.objects.remove(tall, do_unlink=True)
    for o in list(bpy.context.scene.objects):
        if o not in before and o.type == "EMPTY":
            bpy.data.objects.remove(o, do_unlink=True)
    print("clump meshes: rah verts=%d tris=%d, tall verts=%d tris=%d"
          % (len(out["rah"].vertices), len(out["rah"].polygons),
             len(out["tall"].vertices), len(out["tall"].polygons)))
    return out


# 排除区（Blender 坐标）：楼体 footprint（SPEC §4）、道路、跑道内圈、
# 池塘、停车场、充电区、已有 3 块草坪与宿舍间草坪。
BLOCK_RECTS = [
    (-76, -36, 22.5, 37.5), (-28, 4, 23, 37), (15, 37, 23.5, 36.5),
    (12, 36, -66, -50), (-88, -52, 52, 68), (-49, -7, 56, 68),
    (3, 17, 47, 61), (44, 76, 49.5, 62.5), (40, 56, 25, 35),
    (74, 94, -14, -2), (74, 94, -50, -38), (59.7, 68.3, 27.8, 32.2),
    (-130, 130, -114, -102), (102, 114, -102, 110),
    (-91, 91, 76, 84), (-91, 91, -84, -76),
    (-99, -91, -76, 76), (91, 99, -76, 76),
    (-40, -20, -96, -84), (69.5, 94.5, -87, -69),
    (-50, 10, -5, 15), (-20, 20, -87.5, -72.5),
    (36, 52, -80, -72), (74, 94, -38, -14),
]


def _blocked(x, y):
    for (x0, x1, y0, y1) in BLOCK_RECTS:
        if x0 <= x <= x1 and y0 <= y <= y1:
            return True
    if ((x + 62) / 29.0) ** 2 + ((y + 25) / 41.0) ** 2 <= 1.0:
        return True  # 跑道+球场外椭圆+1m（R2-T1b 2026-11-24：中心 (-62,-25)，
        # 长轴转南北向 rx28/ry40，东移 18m；旧椭圆 (-80,-25) rx40/ry28 已废，
        # 旧口径草会压到新跑道东沿/南北端，故跟新椭圆）
    if ((x - POND_CX) / POND_RX) ** 2 + ((y - POND_CY) / POND_RY) ** 2 <= 1.0:
        return True  # 池塘（含 1m 余量，与主撒点排除同口径）
    return False


_VERGE_RECTS = [(-91, 91, 84, 88), (-91, 91, -88, -84),
                (-103, -99, -76, 76), (99, 103, -76, 76)]
_VERGE_W = [728, 728, 608, 608]


def _sample_ring(rng):
    x = rng.uniform(-125, -35)
    y = rng.uniform(-58, 8)
    e_in = ((x + 80) / 40.0) ** 2 + ((y + 25) / 28.0) ** 2
    e_out = ((x + 80) / 45.0) ** 2 + ((y + 25) / 33.0) ** 2
    if e_in <= 1.0 or e_out > 1.0 or _blocked(x, y):
        return None
    return (x, y)


def _sample_verge(rng):
    (x0, x1, y0, y1) = rng.choices(_VERGE_RECTS, weights=_VERGE_W, k=1)[0]
    x = rng.uniform(x0, x1)
    y = rng.uniform(y0, y1)
    if _blocked(x, y):
        return None
    return (x, y)


def _sample_gate(rng):
    x = rng.uniform(-20, 20)
    y = rng.uniform(-101, -98.5)
    if _blocked(x, y):
        return None
    return (x, y)


def _place_instances(mesh, target, sampler, rng, prefix,
                     scale=(0.85, 1.2), zscale=(0.75, 1.05)):
    made = 0
    tries = 0
    while made < target and tries < target * 30:
        tries += 1
        pt = sampler(rng)
        if pt is None:
            continue
        x, y = pt
        o = bpy.data.objects.new("%s_%05d" % (prefix, made), mesh)
        bpy.context.collection.objects.link(o)
        o.location = (x, y, 0.05)
        o.rotation_euler = (0, 0, rng.uniform(0, math.tau))
        s = rng.uniform(*scale)
        o.scale = (s, s, rng.uniform(*zscale))
        objs.append(o)
        made += 1
    return made


_rng = _random.Random(20261123)
_tuft_mesh = _alpha_tuft_mesh()
_clumps = _import_clump_meshes()
_n_alpha_ring = _place_instances(_tuft_mesh, 3440, _sample_ring, _rng,
                                 "GrassEdgeAlphaRing", scale=(0.85, 1.25),
                                 zscale=(0.75, 1.1))
_n_alpha_verge = _place_instances(_tuft_mesh, 4000, _sample_verge, _rng,
                                  "GrassEdgeAlphaVerge", scale=(0.85, 1.25),
                                  zscale=(0.75, 1.1))
_n_alpha_gate = _place_instances(_tuft_mesh, 400, _sample_gate, _rng,
                                 "GrassEdgeAlphaGate", scale=(0.85, 1.25),
                                 zscale=(0.75, 1.1))
_n_rah = _place_instances(_clumps["rah"], 150, _sample_ring, _rng,
                          "GrassClumpRAH", scale=(0.8, 1.3),
                          zscale=(0.9, 1.2))
_n_tall_verge = _place_instances(_clumps["tall"], 120, _sample_verge, _rng,
                                 "GrassTallVerge", scale=(0.8, 1.2),
                                 zscale=(0.8, 1.2))
_n_tall_gate = _place_instances(_clumps["tall"], 30, _sample_gate, _rng,
                                "GrassTallGate", scale=(0.8, 1.2),
                                zscale=(0.8, 1.2))
print("EDGE GRASS: alpha tufts ring=%d verge=%d gate=%d (target 3440/4000/400), "
      "rah clumps=%d, tall grass verge=%d gate=%d, scene objects now %d"
      % (_n_alpha_ring, _n_alpha_verge, _n_alpha_gate, _n_rah,
         _n_tall_verge, _n_tall_gate, len(objs)))

# ---- R2-T18 草地重铺：色带底板 + tevy 高草 drift 带（GREEN_PLAN.md §8）----
# 面数账（先算再铺，见 GREEN_PLAN.md §8.1–8.3）：现有 238,276 tris，
# headroom 161,724；tevy 370 丛 153,400 面 + 色带底板约 164 块 1,968 面，
# 总计约 393,644 ≤ 400k。R2-T11 的 lod1 0.25/m² 在 23,392 m² 新区上是
# 11.87M 面，GREEN_PLAN 原 21,555 丛即使全 lod2 也要 6.55M 面——两者都
# 不可能；可见性改由 4m 色带（零面数主手段）+ drift 带点状 0.76m 草层承担。
# tevy 来源：assets/external/grass/tevy/（CC0，R2-T11 选定）。
# Blender 4.2 导不进 -decoded.glb（KHR_texture_basisu / KTX2 报错），
# 故本节在内存里剥掉贴图引用再导几何（strip 只动临时副本，原文件不动），
# 材质改挂 ktx CLI 4.4.2 解压出的 PNG（ov-lawn_textures/TEVY_*，见 §8.3）：
# 色图直连 Base Color + Alpha 经 ROUND 进 Alpha（照抄 Grass_AlphaStrip 的
# MASK 做法）+ 法线图直连 NormalMap；双面材质。颜色绝不走 ColorRamp。
import json as _json
import struct as _struct
import tempfile as _tempfile

TEVY_DIR = os.path.join(os.path.dirname(BLEND_PATH), "..", "..", "external",
                        "grass", "tevy")
TEVY_TEXDIR = os.path.join(os.path.dirname(BLEND_PATH), "ov-lawn_textures")


def _strip_tevy_glb(src, dst):
    """Blender 4.2 读不了 KTX2：剥掉 images/textures/贴图引用（只动临时
    副本，原 -decoded.glb 不动）。几何、量化、UV、材质名原样保留；
    Blender 4.2 实测可导（lod1 2,030 面、1.89×1.96×0.76m）。"""
    data = open(src, 'rb').read()
    assert data[:4] == b'glTF'
    jlen = _struct.unpack('<I', data[12:16])[0]
    js = _json.loads(data[20:20 + jlen])
    for k in ('extensionsUsed', 'extensionsRequired'):
        if 'KHR_texture_basisu' in js.get(k, []):
            js[k].remove('KHR_texture_basisu')
    js.pop('images', None)
    js.pop('textures', None)
    js.pop('samplers', None)
    for m in js.get('materials', []):
        pbr = m.get('pbrMetallicRoughness', {})
        pbr.pop('baseColorTexture', None)
        pbr.pop('metallicRoughnessTexture', None)
        for k in ('normalTexture', 'occlusionTexture', 'emissiveTexture'):
            m.pop(k, None)
    jbytes = _json.dumps(js, separators=(',', ':')).encode()
    jbytes += b' ' * (-len(jbytes) % 4)
    off = 20 + jlen
    blen = _struct.unpack('<I', data[off:off + 4])[0]
    binchunk = data[off:off + 8 + blen]
    out = (b'glTF' + _struct.pack('<II', 2, 12 + 8 + len(jbytes) + len(binchunk))
           + _struct.pack('<I', len(jbytes)) + b'JSON' + jbytes + binchunk)
    open(dst, 'wb').write(out)


def _import_tevy_mesh(decoded_name, mesh_name):
    """导入一个 tevy -decoded.glb，只留 mesh 数据块（源对象随后删除）。"""
    before = set(bpy.context.scene.objects)
    tmp = _tempfile.NamedTemporaryFile(suffix='.glb', delete=False)
    tmp.close()
    _strip_tevy_glb(os.path.join(TEVY_DIR, decoded_name), tmp.name)
    bpy.ops.import_scene.gltf(filepath=tmp.name)
    os.remove(tmp.name)
    new = [o for o in bpy.context.scene.objects
           if o not in before and o.type == 'MESH']
    assert len(new) == 1, "tevy import: expected 1 mesh, got %d (%s)" % (
        len(new), decoded_name)
    o = new[0]
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    # 导入器把 glTF 节点位移留在对象上（lod1 对象 loc z≈0.34，mesh 本体
    # Z 向关于原点居中）：先把旋转/缩放烘进 mesh，再 XY 居中、Z 底归零，
    # 否则实例化后半丛埋进地下（照抄 _import_clump_meshes + _recenter_mesh）。
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    _recenter_mesh(o.data)
    mesh = o.data
    mesh.name = mesh_name
    bpy.data.objects.remove(o, do_unlink=True)
    print("tevy mesh:", mesh_name, "verts=%d tris=%d" % (
        len(mesh.vertices), len(mesh.polygons)))
    return mesh


def _tevy_mat(name, color_png, normal_png, roughness):
    """tevy 材质：PNG 色图直连 Base Color，Alpha 经 ROUND 进 Alpha
    （MASK、cutoff 0.5，照抄 Grass_AlphaStrip），法线图直连 NormalMap，
    双面；另加同色图自发光 0.35（密丛自遮光、丛心发黑的实测修复）。
    贴图 pack 进 .blend，随件走。"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = 0.0
    img_c = bpy.data.images.load(os.path.join(TEVY_TEXDIR, color_png))
    img_c.colorspace_settings.name = "sRGB"
    img_c.pack()
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = img_c
    nt.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
    rnd = nt.nodes.new("ShaderNodeMath")
    rnd.operation = "ROUND"
    nt.links.new(t.outputs["Alpha"], rnd.inputs[0])
    nt.links.new(rnd.outputs["Value"], bsdf.inputs["Alpha"])
    # 自发光 0.35（同色图）：密丛卡片互相遮光，斜视/近景下丛心全黑；
    # 2026-11-24 单丛特写实测：无自发光时丛心纯黑、仅轮廓见绿，
    # 加 0.35 后丛心变暗绿、结构可见，亮面仍自然。强度 0.35 为实测值。
    # glTF 导出为 emissiveTexture + emissiveFactor，Godot 与 Blender 一致；
    # 镂空仍由 Alpha/MASK 控制，自发光不影响透明裁剪。
    nt.links.new(t.outputs["Color"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = 0.35
    img_n = bpy.data.images.load(os.path.join(TEVY_TEXDIR, normal_png))
    img_n.colorspace_settings.name = "Non-Color"
    img_n.pack()
    tn = nt.nodes.new("ShaderNodeTexImage")
    tn.image = img_n
    nmap = nt.nodes.new("ShaderNodeNormalMap")
    nmap.space = 'TANGENT'
    nt.links.new(tn.outputs["Color"], nmap.inputs["Color"])
    nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    m.use_backface_culling = False
    return m


def _strip_mat(name, color_png):
    """色带底板材质：纯色 PNG 直连 Base Color（不走 ColorRamp，glTF
    导出 baseColor 贴图；贴图 pack 进 .blend）。"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.95
    img = bpy.data.images.load(os.path.join(TEVY_TEXDIR, color_png))
    img.colorspace_settings.name = "sRGB"
    img.pack()
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = img
    nt.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
    return m


# 新路排除（R-N1..R-N5，GREEN_PLAN.md §2；路还没进 ov-road-walk，
# 草先按规划线位让开，免得压路）：_blocked() 已含楼/路/跑道/池塘/
# 旧草坪；此处只补新路走廊。R-N4 用弧外包矩形 + spur 线段距离近似。
def _seg_dist(px, py, x0, y0, x1, y1):
    dx, dy = x1 - x0, y1 - y0
    dd = dx * dx + dy * dy
    t = 0.0 if dd == 0 else max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy) / dd))
    return math.hypot(px - (x0 + t * dx), py - (y0 + t * dy))


def _blocked_new(x, y):
    if _blocked(x, y):
        return True
    if -91 <= x <= 91 and abs(y - 44) <= 1.5:
        return True  # R-N1
    if abs(x + 33) <= 1.5 and -76 <= y <= 18.5:
        return True  # R-N2
    if abs(x - 58) <= 1.5 and -76 <= y <= 20:
        return True  # R-N3
    if abs(y - 20) <= 1.5 and 50 <= x <= 58:
        return True  # R-N3x
    if abs(x - 9.5) <= 1.5 and 18.5 <= y <= 44:
        return True  # R-N5
    if 68 <= x <= 91 and -71 <= y <= -67:
        return True  # R-N4 北岸弧（外包矩形近似）
    if _seg_dist(x, y, 71.3, -70.9, 68, -76) <= 1.0:
        return True  # R-N4 spur
    for (bx0, bx1, by0, by1) in BED_RECTS_R218:
        if bx0 <= x <= bx1 and by0 <= y <= by1:
            return True  # 花坛（6×2m 框）
    for (sx, sy) in SHRUB_SPOTS_R218:
        if (x - sx) ** 2 + (y - sy) ** 2 <= 0.8 ** 2:
            return True  # 灌木球
    return False


BED_RECTS_R218 = [(-17, -11, -87, -85), (-17, -11, -96, -94),
                  (11, 17, -87, -85), (11, 17, -96, -94)]
SHRUB_SPOTS_R218 = [(-45, -7), (-35, -7), (-25, -7), (-15, -7), (-5, -7),
                     (5, -7), (-22, -70), (-22, -80), (-22, -90),
                     (-22, -100), (22, -70), (22, -80), (22, -90),
                     (22, -100), (68, -70), (68, -86), (96, -70),
                     (96, -86), (-50, 16), (30, 16)]

# G1–G7 分区矩形（green_layout.json grass.zones[].rects，[x0,x1,y0,y1]）
GRASS_ZONES_R218 = {
    'G1': ([(-91, 91, 38, 76)], 64, 2, 2),
    'G2': ([(-91, -3, -76, 18.5), (-91, -40, 18.5, 38)], 65, 1, 2),
    'G3': ([(3, 91, -76, 18.5)], 96, 2, 2),
    'G4': ([(-118, -99, -76, 76)], 29, 1, 0),
    'G5': ([(99, 102, -102, 105), (114, 118, -102, 105)], 21, 0, 1),
    'G6': ([(-91, 91, -102, -84)], 36, 1, 2),
    'G7': ([(-125, -99, 84, 110), (99, 125, 84, 110),
            (99, 125, -110, -84), (-125, -99, -110, -84)], 15, 1, 1),
}
# 每区元组：(矩形, lod2 丛数, 红燕麦 lod1 丛数, 红燕麦 lod2 丛数)
# lod2 合计 326 + 旧草坪叠加 14 = 340；红燕麦 lod1 8、lod2 10。

mat_strip_a = _strip_mat("Lawn_Strip_A", "Lawn_Strip_A_color.png")
mat_strip_b = _strip_mat("Lawn_Strip_B", "Lawn_Strip_B_color.png")
mat_strip_c = _strip_mat("Lawn_Strip_C", "Lawn_Strip_C_color.png")
strip_mats = [mat_strip_a, mat_strip_b]


def _slab_unit_mesh(mat):
    """色带底板共用单位立方 mesh（1×1×1，中心原点）：每色一个 mesh，
    实例只改 location/scale 共享 mesh。注意：不要用 box() 逐块建——
    box() 每块调两次 bpy.ops，8k 对象场景下每 call 都要过依赖图，
    172 块曾让整轮多烧约 3 分钟 CPU；共用 mesh + 缩放零算子。"""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    o = bpy.context.active_object
    mesh = o.data
    mesh.name = "SlabUnit_" + mat.name
    mesh.materials.clear()
    mesh.materials.append(mat)
    bpy.data.objects.remove(o, do_unlink=True)
    return mesh


_slab_meshes = {"A": _slab_unit_mesh(mat_strip_a),
                "B": _slab_unit_mesh(mat_strip_b),
                "C": _slab_unit_mesh(mat_strip_c)}

# ---- 色带底板：每区沿长边切 4m 条带，对缝拼接不重叠；沿带每 0.5m
# 采样，_blocked_new() 命中的点断开（路/楼/池塘/操场/花坛/灌木处
# 不铺），连续未命中段 ≥1m 才成块；每区第 5 条带用亮色 C。----
_rng18 = _random.Random(20261124)
slab_count = 0
slab_area = 0.0
for _zid, (_rects, _n2, _nr1, _nr2) in GRASS_ZONES_R218.items():
    for (_x0, _x1, _y0, _y1) in _rects:
        _w, _h = _x1 - _x0, _y1 - _y0
        _along_x = _w >= _h
        _short = _h if _along_x else _w
        _nstrips = max(1, math.ceil(_short / 4.0))
        for _s in range(_nstrips):
            _c = (_y0 + _s * 4 + 2.0) if _along_x else (_x0 + _s * 4 + 2.0)
            _wid = min(4.0, _short - _s * 4)
            _lo, _hi = (_x0, _x1) if _along_x else (_y0, _y1)
            _n = int((_hi - _lo) / 0.5)
            _runs = []
            _cur = None
            for _i in range(_n + 1):
                _t = _lo + _i * 0.5
                _x, _y = (_t, _c) if _along_x else (_c, _t)
                if not _blocked_new(_x, _y) and _cur is None:
                    _cur = _t
                if _blocked_new(_x, _y) and _cur is not None:
                    _runs.append((_cur, _t))
                    _cur = None
            if _cur is not None:
                _runs.append((_cur, _hi))
            _key = 'C' if (_s + 1) % 5 == 0 else ('A' if _s % 2 == 0 else 'B')
            for (_a, _b) in _runs:
                if _b - _a < 1.0:
                    continue
                _mid = (_a + _b) / 2.0
                _ln = _b - _a
                _o = bpy.data.objects.new(
                    "Slab_%s_%03d" % (_zid, slab_count), _slab_meshes[_key])
                bpy.context.collection.objects.link(_o)
                if _along_x:
                    _o.location = (_mid, _c, 0.025)
                    _o.scale = (_ln, _wid, 0.05)
                else:
                    _o.location = (_c, _mid, 0.025)
                    _o.scale = (_wid, _ln, 0.05)
                objs.append(_o)
                slab_count += 1
                slab_area += _ln * _wid
print("SLABS R2-T18: %d boxes, %.0f m2, %d tris (4m stripes A/B, every 5th C)"
      % (slab_count, slab_area, slab_count * 12))

# ---- tevy 网格与材质（只导 5 个用到的 LOD；其余候选不进件）----
_tevy_meshes = {
    'lod0': _import_tevy_mesh("tevy-meadow-grass-patch-decoded.glb",
                              "TEVY_Meadow_LOD0"),
    'lod1': _import_tevy_mesh("tevy-meadow-grass-patch-lod1-decoded.glb",
                              "TEVY_Meadow_LOD1"),
    'lod2': _import_tevy_mesh("tevy-meadow-grass-patch-lod2-decoded.glb",
                              "TEVY_Meadow_LOD2"),
    'oat1': _import_tevy_mesh("tevy-red-oat-grass-clump-lod1-decoded.glb",
                              "TEVY_RedOat_LOD1"),
    'oat2': _import_tevy_mesh("tevy-red-oat-grass-clump-lod2-decoded.glb",
                              "TEVY_RedOat_LOD2"),
}
_tevy_mats = {
    'lod0': _tevy_mat("TEVY_Meadow_LOD0", "TEVY_Meadow_LOD0_color.png",
                      "TEVY_Meadow_LOD0_normal.png", 0.7),
    'lod1': _tevy_mat("TEVY_Meadow_LOD1", "TEVY_Meadow_LOD1_color.png",
                      "TEVY_Meadow_LOD1_normal.png", 0.7),
    'lod2': _tevy_mat("TEVY_Meadow_LOD2", "TEVY_Meadow_LOD2_color.png",
                      "TEVY_Meadow_LOD2_normal.png", 0.7),
    'oat1': _tevy_mat("TEVY_RedOat_LOD1", "TEVY_RedOat_LOD1_color.png",
                      "TEVY_RedOat_LOD1_normal.png", 0.75),
    'oat2': _tevy_mat("TEVY_RedOat_LOD2", "TEVY_RedOat_LOD2_color.png",
                      "TEVY_RedOat_LOD2_normal.png", 0.75),
}
for _k, _mesh in _tevy_meshes.items():
    _mesh.materials.clear()
    _mesh.materials.append(_tevy_mats[_k])


def _place_tevy(mesh, prefix, points, z0=0.05, smin=0.85, smax=1.15):
    """按给定 (x, y) 点表放实例：共享 mesh，随机 Z 向旋转 + 缩放；
    丛高随缩放 0.65–0.87m（lod1 原高 0.76m）。"""
    n = 0
    for (_i, (_x, _y)) in enumerate(points):
        o = bpy.data.objects.new("%s_%04d" % (prefix, _i), mesh)
        bpy.context.collection.objects.link(o)
        o.location = (_x, _y, z0)
        o.rotation_euler = (0, 0, _rng18.uniform(0, math.tau))
        _s = _rng18.uniform(smin, smax)
        o.scale = (_s, _s, _rng18.uniform(smin, smax))
        objs.append(o)
        n += 1
    return n


def _drift_candidates(rects, pitch):
    """drift 带候选点：每区沿长边、按 pitch 间距排 3m 宽带，沿带中心线
    每 0.5m 采样，_blocked_new() 命中的点剔除。窄区（短边 < pitch，
    如 G5 仅 3m 宽）排不出带时退回短边中线，保证总有候选点。"""
    pts = []
    for (_x0, _x1, _y0, _y1) in rects:
        _w, _h = _x1 - _x0, _y1 - _y0
        _along_x = _w >= _h
        _short = _h if _along_x else _w
        _slo, _shi = (_y0, _y1) if _along_x else (_x0, _x1)
        _centers = [_slo + pitch * (_b + 0.5)
                    for _b in range(max(1, int(_short / pitch)))]
        _centers = [_c for _c in _centers if _slo + 1.5 <= _c <= _shi - 1.5]
        if not _centers:
            _centers = [(_slo + _shi) / 2.0]
        for _c in _centers:
            _lo, _hi = (_x0, _x1) if _along_x else (_y0, _y1)
            _n = int((_hi - _lo) / 0.5)
            for _i in range(_n + 1):
                _t = _lo + _i * 0.5
                _x, _y = (_t, _c) if _along_x else (_c, _t)
                if not _blocked_new(_x, _y):
                    pts.append((_x, _y, _along_x))
    return pts


def _pick_spaced(cands, n, phase, min_dist, placed_xy):
    """从候选点表里取 n 个点：目标下标均匀分布；若目标点离已放点
    < min_dist，沿表向两侧找最近的空点（不再直接丢弃——上一版直接
    丢弃曾让红燕麦 G1 oat1=0、G3 oat1=1，缺数）。找不到才缺数。"""
    out = []
    if n <= 0 or not cands:
        return out
    for i in range(n):
        _tgt = min(len(cands) - 1, int((i + phase) * len(cands) / n))
        _found = None
        for _d in range(len(cands)):
            for _j in (_tgt + _d, _tgt - _d):
                if 0 <= _j < len(cands):
                    _p = (cands[_j][0], cands[_j][1])
                    if all((_p[0] - _qx) ** 2 + (_p[1] - _qy) ** 2
                           >= min_dist ** 2 for (_qx, _qy) in placed_xy):
                        _found = _j
                        break
            if _found is not None:
                break
        if _found is None:
            continue
        _jp = _jittered(cands[_found], 1.2, 0.5)
        out.append(_jp)
        placed_xy.append(_jp)
    return out


def _jittered(pt, perp, along):
    _x, _y, _along_x = pt
    _jx = _rng18.uniform(-along, along)
    _jy = _rng18.uniform(-perp, perp)
    if not _along_x:
        _jx, _jy = _jy, _jx
    _nx, _ny = _x + _jx, _y + _jy
    if _blocked_new(_nx, _ny):
        return (_x, _y)
    return (_nx, _ny)


# ---- drift 带布放：lod2 主力 + 红燕麦点缀（同带不同相位，丛距 ≥1.5m）----
_placed_xy = []
_tevy_counts = {}
_tevy_by_mesh = {'lod0': 0, 'lod1': 0, 'lod2': 0, 'oat1': 0, 'oat2': 0}
_MESH_TRIS = {'lod0': 11024, 'lod1': 2030, 'lod2': 304, 'oat1': 824,
              'oat2': 110}
for _zid, (_rects, _n2, _nr1, _nr2) in GRASS_ZONES_R218.items():
    _pitch = 20.0 if _zid == 'G7' else 12.0
    _cands = _drift_candidates(_rects, _pitch)
    assert len(_cands) >= max(_n2, _nr1, _nr2, 1), (
        "drift candidates too few in %s: %d" % (_zid, len(_cands)))
    _picks = {'lod2': [], 'oat1': [], 'oat2': []}
    for _key, _n, _phase in (('lod2', _n2, 0.5), ('oat1', _nr1, 0.15),
                             ('oat2', _nr2, 0.85)):
        _picks[_key] = _pick_spaced(_cands, _n, _phase, 1.5, _placed_xy)
    for _key, _mesh_key, _prefix in (
            ('lod2', 'lod2', "TevyMeadowLOD2_%s" % _zid),
            ('oat1', 'oat1', "TevyRedOatLOD1_%s" % _zid),
            ('oat2', 'oat2', "TevyRedOatLOD2_%s" % _zid)):
        _tevy_counts[_prefix] = _place_tevy(_tevy_meshes[_mesh_key],
                                             _prefix, _picks[_key])
        _tevy_by_mesh[_mesh_key] += _tevy_counts[_prefix]
    print("TEVY %s: drift cands=%d lod2=%d oat1=%d oat2=%d" % (
        _zid, len(_cands), _tevy_counts["TevyMeadowLOD2_%s" % _zid],
        _tevy_counts["TevyRedOatLOD1_%s" % _zid],
        _tevy_counts["TevyRedOatLOD2_%s" % _zid]))

# ---- 旧草坪叠加高草（预览机位前方，近景特写位）----
# TeachSouth (-50..10, -5..15)：lod0 2 丛在机位目标 (-16,5) 旁；
# lod1 6、lod2 8。GateNorth (-20..20, -87.5..-72.5)：lod1 4、lod2 6。
# 点位已避开 R-N2 路（x -34.5..-31.5）与楼体；抖动 ±0.7m 后仍须落在
# 本草坪内缩 0.5m 范围内，否则回落原点。
_HEROES = [
    ('lod0', "TevyHeroLOD0_TeachSouth", [(-17.5, 5.0), (-14.5, 5.0)],
     (-50, 10, -5, 15)),
    ('lod1', "TevyHeroLOD1_TeachSouth",
     [(-24, 2), (-20, 8), (-12, 2), (-8, 8), (-28, 8), (-4, 3)],
     (-50, 10, -5, 15)),
    ('lod2', "TevyHeroLOD2_TeachSouth",
     [(-30, 0), (-26, 10), (-18, 0), (-10, 10), (-6, 0), (0, 8),
      (-30, 5), (2, 2)], (-50, 10, -5, 15)),
    ('lod1', "TevyHeroLOD1_GateNorth",
     [(-12, -80), (-4, -76), (8, -80), (14, -76)], (-20, 20, -87.5, -72.5)),
    ('lod2', "TevyHeroLOD2_GateNorth",
     [(-16, -76), (-8, -84), (0, -78), (4, -84), (12, -84), (16, -78)],
     (-20, 20, -87.5, -72.5)),
]
for _mesh_key, _prefix, _pts, (_lx0, _lx1, _ly0, _ly1) in _HEROES:
    _final = []
    for (_x, _y) in _pts:
        # 抖动 ±0.7m，最多试 8 次取不撞点的；都撞则回落未抖动原点
        # （原点之间 ≥2.83m、与 drift 点 ≥6m，必不撞）；原点也撞才丢弃。
        _placed_pt = None
        for _attempt in range(8):
            _nx = _x + _rng18.uniform(-0.7, 0.7)
            _ny = _y + _rng18.uniform(-0.7, 0.7)
            if not (_lx0 + 0.5 <= _nx <= _lx1 - 0.5
                    and _ly0 + 0.5 <= _ny <= _ly1 - 0.5):
                continue
            if all((_nx - _qx) ** 2 + (_ny - _qy) ** 2 >= 2.0 ** 2
                   for (_qx, _qy) in _placed_xy):
                _placed_pt = (_nx, _ny)
                break
        if _placed_pt is None:
            if all((_x - _qx) ** 2 + (_y - _qy) ** 2 >= 2.0 ** 2
                   for (_qx, _qy) in _placed_xy):
                _placed_pt = (_x, _y)
        if _placed_pt is None:
            continue
        _final.append(_placed_pt)
        _placed_xy.append(_placed_pt)
    _tevy_counts[_prefix] = _place_tevy(_tevy_meshes[_mesh_key], _prefix,
                                         _final)
    _tevy_by_mesh[_mesh_key] += _tevy_counts[_prefix]
    print("TEVY hero %s: %d placed" % (_prefix, _tevy_counts[_prefix]))

_n_tevy = sum(_tevy_counts.values())
assert _tevy_by_mesh == {'lod0': 2, 'lod1': 10, 'lod2': 340, 'oat1': 8,
                         'oat2': 10}, "tevy counts off plan: %s" % _tevy_by_mesh
_n_tevy_tris = sum(_tevy_by_mesh[_k] * _MESH_TRIS[_k] for _k in _MESH_TRIS)
print("TEVY TOTAL R2-T18: %d tufts, %d tris (lod2 304 / lod1 2030 / "
      "lod0 11024 / oat1 824 / oat2 110); slabs %d boxes %d tris"
      % (_n_tevy, _n_tevy_tris, slab_count, slab_count * 12))

# ---- 存盘 ----
os.makedirs(os.path.dirname(BLEND_PATH), exist_ok=True)
os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)

# ---- 导出 GLB：只选本件 ----
bpy.ops.object.select_all(action="DESELECT")
for o in objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format="GLB",
                          use_selection=True, export_apply=True)

# ---- 回读 GLB 确认（对象数 + 三角面数） ----
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB_PATH)
imported = [o for o in bpy.data.objects if o not in before]
n_tris = sum(len(o.data.polygons) for o in imported
             if o.type == 'MESH' and o.data is not None)
n_verts = sum(len(o.data.vertices) for o in imported
              if o.type == 'MESH' and o.data is not None)
print(f"GLB reimport OK: {len(imported)} objects, "
      f"{n_tris} tris, {n_verts} verts")
# R2-T18 预算：ov-lawn ≤400k tris（GREEN_PLAN.md §8.3 约 393,644）。
assert n_tris <= 400000, "ov-lawn over tri budget: %d tris" % n_tris
# 回读验证 (di-walls 做法): 地面基底材质的贴图数 >= 3 (烘焙贴图齐全);
# 草叶材质已挂绿斑贴图，alpha 草丛材质带 MASK 镂空贴图，均要求有贴图。
_BAKED_MAT_NAMES = {"Lawn_Green", "Bed_Border", "Bed_Soil",
                    "Flower_Red", "Flower_Yellow", "Flower_Pink",
                    "Shrub_DarkGreen"}
for ob in imported:
    for slot in ob.material_slots:
        m = slot.material
        if m and m.use_nodes:
            # 回读时材质名会带 .001 后缀 (原材质仍在场景中), 比较时先去掉后缀。
            _mbase = m.name.rpartition(".")[0] or m.name
            imgs = [n.image.name for n in m.node_tree.nodes
                    if n.type == 'TEX_IMAGE' and n.image is not None]
            if _mbase in _BAKED_MAT_NAMES:
                print("GLB reimport mat:", ob.name, m.name, "images:", imgs)
                assert len(imgs) >= 3, "glb material lost baked textures: %s" % m.name
            else:
                print("GLB reimport mat (grass/alpha, textured):", ob.name,
                      m.name, "images:", imgs)
assert len(imported) == len(objs), "glb reimport failed: expected %d objects, got %d" % (len(objs), len(imported))
for o in imported:
    bpy.data.objects.remove(o, do_unlink=True)

# ---- 删 .blend1 ----
blend1 = BLEND_PATH + "1"
if os.path.exists(blend1):
    os.remove(blend1)

print("DONE ov-lawn")
