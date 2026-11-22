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
    d, l = GRASS_VAR[k]
    add_color_var(m, d, l, noise_scale=3.0)
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
for o in imported:
    bpy.data.objects.remove(o, do_unlink=True)

# ---- 删 .blend1 ----
blend1 = BLEND_PATH + "1"
if os.path.exists(blend1):
    os.remove(blend1)

print("DONE ov-lawn")
