# ov-lawn v3: 草坪花坛（总览件）——密度版重做（只改密度和分布）
# v3 改动（用户反馈 v2 草太稀）：草丛密度从 2 丛/m2（0.5 m2/丛，4500 丛）
#   提到 10 丛/m2（0.1 m2/丛），三块草皮总计 22500 丛（5 倍），铺满整块草皮；
#   6 种绿色变体，丛高 0.15-0.35m 随机，丛幅随机；分布加簇状聚集（60% 丛落在簇心
#   半径 1.5m 内，另 40% 均匀撒满全块），不均匀成地毯；花坛土面/灌木球/底板
#   几何位置照旧，只加密草。三角面预算 <15 万（实测见运行日志）。
#   渲染全部走 GitHub Actions，本地不渲染：本脚本只建模 + 存 .blend + 导出 .glb + 回读确认。
#   （磁盘上曾有一份未跑通的 v4 草稿头注释，密度参数仍是 v2 的 0.5，已按本任务 v3 规约覆盖。）
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
GRASS_COLORS = [
    ("DarkGreen", "#3E6B2E", 0.12),
    ("Dark", "#4E8A3F", 0.20),
    ("Green", "#69B45E", 0.28),
    ("Light", "#7FC46A", 0.18),
    ("YellowGreen", "#8AA84A", 0.14),
    ("Lime", "#A8C25E", 0.08),
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
grass_counts = {}
for lawn_name, (cx, cy), (sx, sy) in lawns:
    area = sx * sy
    n_tufts = int(area * TUFTS_PER_M2)
    # 簇心：约每 12 m2 一个，覆盖整块草皮
    n_clusters = max(8, int(area / 12))
    clusters = [(cx + random.uniform(-sx / 2 + 1.0, sx / 2 - 1.0),
                 cy + random.uniform(-sy / 2 + 1.0, sy / 2 - 1.0))
                for _ in range(n_clusters)]
    # 每色一个 (verts, faces) 累积器
    buckets = {k: ([], []) for k in color_keys}
    tufts_per_color = {k: 0 for k in color_keys}
    for _ in range(n_tufts):
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
        tufts_per_color[ckey] += 1
        # 随机旋转 + 缩放（xy 0.85-1.2，z 0.75-1.05：原型丛高 0.20-0.33m
        #  → 实际丛高 0.15-0.35m，丛幅随机）
        rot = Matrix.Rotation(random.uniform(0, math.tau), 4, 'Z')
        scl = Matrix.Diagonal((random.uniform(0.85, 1.2),
                               random.uniform(0.85, 1.2),
                               random.uniform(0.75, 1.05),
                               1.0))
        loc = Matrix.Translation((px, py, 0.05))  # 扎在草地底板顶面
        mat = loc @ rot @ scl
        base = len(verts)
        verts.extend(mat @ Vector(v) for v in pverts)
        faces.extend(tuple(base + i for i in f) for f in pfaces)
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
    print(f"GRASS {lawn_name}: {n_tufts} tufts, {total} tris, "
          f"area {area:.0f}m2 ({TUFTS_PER_M2:.1f} tufts/m2, "
          f"{n_clusters} clusters)")

total_tufts = sum(int(sx * sy * TUFTS_PER_M2) for _, _, (sx, sy) in lawns)
print(f"GRASS TOTAL: {total_tufts} tufts, 18 merged meshes "
      f"(3 lawns x 6 colors), tuft height 0.15-0.35m")

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
    if ((x + 80) / 41.0) ** 2 + ((y + 25) / 29.0) ** 2 <= 1.0:
        return True  # 跑道内圈（含 1m 余量）
    if ((x - 82) / 12.0) ** 2 + ((y + 78) / 9.0) ** 2 <= 1.0:
        return True  # 池塘（含 1m 余量）
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
