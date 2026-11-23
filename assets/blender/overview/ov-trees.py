# ov-trees v2: 树木（总览件）— 纹理 pass
# Blender 坐标 x 向东、y 向北、z 向上，单位米
# 内容：3 个母版（球冠/锥冠/椭圆冠）× 链接复制，146 棵
#   校园周边密植带 112 棵、东侧路旁行道树 19 棵、楼间零星点缀 15 棵
# v1 几何/位置/数量/随机种子原样保留，只补纹理（不重排、不增减）：
#   ① 树冠：噪波贴图（numpy 值噪波，ov-trees_textures/LeafNoise.png，
#      与 v2 同种子；v2 的内存生成图实测全黑，树冠只能是最深绿纯色，
#      本次改从文件加载）→ ColorRamp 深浅不均 + Bump 叶簇起伏
#   ② 树干：纵纹树皮噪波贴图（横向密、纵向疏 → 竖纹）→ ColorRamp 棕褐深浅 + Bump
#   ③ 三区绿色拉开：密植带深绿 / 行道树中绿 / 楼间点缀浅黄绿，各带一档浅色变体
#   ④ 所有面都有 Noise + Bump，不许全平
# v2 新规矩：渲染走 GitHub Actions，本地不渲染、不出预览图
#   （太阳/世界背景保留进 .blend，相机与渲染块已删）
# 注意：Principled Base Color / ColorRamp 停靠点全部用线性值，
#   十六进制 sRGB 先转线性：c<=0.04045 时 c/12.92，否则 ((c+0.055)/1.055)^2.4
import bpy
import math
import os
import random

import numpy as np

BASE = os.path.expanduser(
    "~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
BLEND_PATH = os.path.join(BASE, "assets/blender/overview/ov-trees.blend")
GLB_PATH = os.path.join(BASE, "assets/models/ov-trees.glb")


def srgb_to_linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_to_linear(h):
    h = h.lstrip("#")
    return tuple(srgb_to_linear(int(h[i:i + 2], 16)) for i in (0, 2, 4))


# ---- 程序化噪波（numpy 值噪波，周期性网格可无缝平铺） ----
def _value_noise(size, gw, gh, seed):
    rng = np.random.default_rng(seed)
    grid = rng.random((gh + 1, gw + 1))
    grid[-1, :] = grid[0, :]
    grid[:, -1] = grid[:, 0]
    xs = np.linspace(0, gw, size, endpoint=False)
    ys = np.linspace(0, gh, size, endpoint=False)
    x0 = xs.astype(int)
    fx = xs - x0
    y0 = ys.astype(int)
    fy = ys - y0
    fx = fx * fx * (3 - 2 * fx)  # smoothstep
    fy = fy * fy * (3 - 2 * fy)
    x1 = x0 + 1
    y1 = y0 + 1
    g00 = grid[np.ix_(y0, x0)]
    g10 = grid[np.ix_(y0, x1)]
    g01 = grid[np.ix_(y1, x0)]
    g11 = grid[np.ix_(y1, x1)]
    top = g00 * (1 - fx)[None, :] + g10 * fx[None, :]
    bot = g01 * (1 - fx)[None, :] + g11 * fx[None, :]
    return top * (1 - fy)[:, None] + bot * fy[:, None]


def _normalize(a):
    lo, hi = float(a.min()), float(a.max())
    return (a - lo) / (hi - lo) if hi > lo else a


def make_leaf_noise(size=256, seed=11):
    """叶簇噪波：三倍频叠加，0..1 灰度。"""
    a = _value_noise(size, 6, 6, seed)
    b = _value_noise(size, 12, 12, seed + 1)
    c = _value_noise(size, 24, 24, seed + 2)
    return _normalize(0.55 * a + 0.30 * b + 0.15 * c)


def make_bark_noise(size=256, seed=77):
    """树皮纵纹噪波：横向密（24/48 列）、纵向疏（3/6 行）→ 竖纹。"""
    a = _value_noise(size, 24, 3, seed)
    b = _value_noise(size, 48, 6, seed + 1)
    return _normalize(0.7 * a + 0.3 * b)


def make_noise_image(name, array):
    """Load the real noise PNG (same seeds as make_leaf/bark_noise).
    v2 generated this image in-memory with foreach_set and it came out
    ALL BLACK (verified in .blend and in the exported GLB: crowns render
    flat darkest-green). The PNGs in ov-trees_textures/ are generated
    from the same numpy value-noise by gen_textures.py; loading them
    keeps the ColorRamp pipeline (and the exported baseColorTexture)
    identical, only the pixels become real noise."""
    path = os.path.join(os.path.dirname(BLEND_PATH), "ov-trees_textures",
                        name + ".png")
    img = bpy.data.images.load(path)
    img.colorspace_settings.name = "Non-Color"
    return img


def make_crown_mat(name, dark_hex, mid_hex, light_hex, noise_img,
                   map_scale=(1.6, 1.6, 1.6), bump_strength=0.5):
    """树冠材质：噪波贴图 → ColorRamp 深/中/浅三档绿 → Base Color；
    同贴图进 Bump 做叶簇起伏。Base Color 默认值填中绿，作 GLB 回退色。"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*hex_to_linear(mid_hex), 1.0)
    bsdf.inputs["Roughness"].default_value = 0.95
    texcoord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (*map_scale,)
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = noise_img
    tex.extension = "REPEAT"
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (*hex_to_linear(dark_hex), 1.0)
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = (*hex_to_linear(light_hex), 1.0)
    mid_el = ramp.color_ramp.elements.new(0.5)
    mid_el.color = (*hex_to_linear(mid_hex), 1.0)
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = bump_strength
    bump.inputs["Distance"].default_value = 0.4
    nt.links.new(texcoord.outputs["Generated"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
    nt.links.new(tex.outputs["Color"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(tex.outputs["Color"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def make_trunk_mat(name, dark_hex, mid_hex, light_hex, bark_img):
    """树干材质：纵纹树皮噪波 → ColorRamp 棕褐深浅 → Base Color + Bump 竖纹。"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*hex_to_linear(mid_hex), 1.0)
    bsdf.inputs["Roughness"].default_value = 1.0
    texcoord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (2.0, 2.0, 1.0)
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bark_img
    tex.extension = "REPEAT"
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (*hex_to_linear(dark_hex), 1.0)
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = (*hex_to_linear(light_hex), 1.0)
    mid_el = ramp.color_ramp.elements.new(0.5)
    mid_el.color = (*hex_to_linear(mid_hex), 1.0)
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.8
    bump.inputs["Distance"].default_value = 0.15
    nt.links.new(texcoord.outputs["Generated"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
    nt.links.new(tex.outputs["Color"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(tex.outputs["Color"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


# ---- 清空场景 ----
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for m in list(bpy.data.materials):
    bpy.data.materials.remove(m)
for img in list(bpy.data.images):
    bpy.data.images.remove(img)

# ---- 纹理贴图（各一张 256×256，打包进 .blend） ----
leaf_img = make_noise_image("LeafNoise", make_leaf_noise())
bark_img = make_noise_image("BarkNoise", make_bark_noise())

# ---- 材质：树干 1 种；树冠 3 区 × 主/浅变体 = 6 种 ----
# 绿按鸟瞰图拉开：密植带深绿 / 行道树中绿 / 楼间点缀浅黄绿
mat_trunk = make_trunk_mat("Trunk_Bark", "#4A2F1C", "#6B4E2E", "#8A6B4A", bark_img)
CROWN_MATS = {
    # (主, 浅变体)：深 / 中 / 浅 三档绿（sRGB 十六进制，转线性后进节点）
    "perimeter": (
        make_crown_mat("Crown_Perimeter", "#2F6B2A", "#4E8A3F", "#6FA84E", leaf_img),
        make_crown_mat("Crown_Perimeter_Light", "#3A7A33", "#5C9A48", "#82B85E", leaf_img),
    ),
    "road": (
        make_crown_mat("Crown_Roadside", "#3F7A32", "#5C9A44", "#8AB85C", leaf_img),
        make_crown_mat("Crown_Roadside_Light", "#4A8540", "#6FAA50", "#9CC46A", leaf_img),
    ),
    "scattered": (
        make_crown_mat("Crown_Scattered", "#557F35", "#7AA84A", "#A8C46A", leaf_img),
        make_crown_mat("Crown_Scattered_Light", "#648C40", "#8AB85A", "#B8D47A", leaf_img),
    ),
}

random.seed(20261122)

# ---- 3 个母版：树干圆柱（r0.18，高 1.5m）+ 树冠二十面体/锥 ----
# 母版直接种在前 3 个周边点位上，其余全部链接复制
# (form, crown_z, master_height)
FORMS = [
    ("Sphere", 3.00, 4.53),   # 球冠：二十面体 r1.7，z 压扁 0.9
    ("Cone", 2.90, 4.30),     # 锥冠：8 边锥 r1.5、高 2.8
    ("Ellipse", 3.30, 5.33),  # 椭圆冠：二十面体 r1.5，拉长 (1.15, 1.15, 1.35)
]

masters = []  # [(trunk_obj, crown_obj, crown_z, master_height)]
for form, crown_z, mheight in FORMS:
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.18, depth=1.5,
                                        location=(0, 0, 0.75))
    trunk = bpy.context.active_object
    trunk.name = f"TreeMaster_{form}_Trunk"
    trunk.data.materials.append(mat_trunk)
    if form == "Cone":
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=1.5, radius2=0.0,
                                        depth=2.8, location=(0, 0, crown_z))
    else:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1.7 if form == "Sphere" else 1.5,
                                              location=(0, 0, crown_z))
    crown = bpy.context.active_object
    crown.name = f"TreeMaster_{form}_Crown"
    if form == "Sphere":
        crown.scale = (1.0, 1.0, 0.9)
    elif form == "Ellipse":
        crown.scale = (1.15, 1.15, 1.35)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    crown.data.materials.append(CROWN_MATS["perimeter"][0])
    masters.append((trunk, crown, crown_z, mheight))


def linked_copy(obj, name):
    c = obj.copy()
    c.data = obj.data  # 共享网格数据：链接复制
    bpy.context.collection.objects.link(c)
    c.name = name
    return c


def zone_of(idx, n_perimeter, n_road):
    if idx < n_perimeter:
        return "perimeter"
    if idx < n_perimeter + n_road:
        return "road"
    return "scattered"


def plant_tree(idx, x, y, form_idx, n_perimeter, n_road):
    """在 (x, y) 种一棵树：母版 form_idx，目标成树高 3~6m 随机，冠色按区域 + 主/浅变体。
    注意：random() 调用次数与 v1 完全一致（每棵恰好 3 次：高、转角、变体抽取），
    保证树的位置/尺寸/朝向与 v1 逐棵相同。"""
    trunk_m, crown_m, crown_z, mheight = masters[form_idx]
    target_h = random.uniform(3.0, 6.0)
    s = target_h / mheight
    rot_z = random.uniform(0, math.pi * 2)
    if idx < 3:
        # 前 3 棵直接用母版对象（3 个母版各一棵）
        trunk, crown = trunk_m, crown_m
        trunk.name = f"Tree_{idx:03d}_Trunk"
        crown.name = f"Tree_{idx:03d}_Crown"
    else:
        trunk = linked_copy(trunk_m, f"Tree_{idx:03d}_Trunk")
        crown = linked_copy(crown_m, f"Tree_{idx:03d}_Crown")
    trunk.location = (x, y, 0.75 * s)
    trunk.scale = (s, s, s)
    trunk.rotation_euler = (0, 0, rot_z)
    crown.location = (x, y, crown_z * s)
    crown.scale = (s, s, s)
    crown.rotation_euler = (0, 0, rot_z)
    # 冠色：按区域选材质对，主/浅变体 60/40（与 v1 绿/黄绿 60/40 同一抽取）
    main_mat, light_mat = CROWN_MATS[zone_of(idx, n_perimeter, n_road)]
    crown_mat = main_mat if random.random() < 0.6 else light_mat
    crown.material_slots[0].link = "OBJECT"
    crown.material_slots[0].material = crown_mat
    return trunk, crown


# ---- 分布（与 v1 逐点相同） ----
spots = []  # (x, y)

# 1) 校园周边密植带：矩形 x ±120、y ±105，间距约 8m
xs = [round(-120 + i * 8, 1) for i in range(31)]   # -120..120
ys = [round(-97 + i * 8, 1) for i in range(25)]    # -97..97（避开四角重复）
for x in xs:
    spots.append((x, 105))
    spots.append((x, -105))
for y in ys:
    spots.append((-120, y))
    spots.append((120, y))
n_perimeter = len(spots)
# 轻微抖动（±1.2m），保持树带不呆板
spots = [(x + random.uniform(-1.2, 1.2), y + random.uniform(-1.2, 1.2))
         for (x, y) in spots]

# 2) 东侧路旁行道树：x=100、y -90~90，间距 10m
road_spots = [(100 + random.uniform(-0.8, 0.8),
               y + random.uniform(-1.0, 1.0))
              for y in range(-90, 91, 10)]
n_road = len(road_spots)
spots.extend(road_spots)

# 3) 楼间零星点缀 15 棵（教学楼区 y=10~50，避开楼体）
# 楼体（Blender）：A(-56,30)40x15；B(-12,30)32x14；C(26,30)22x13；
#   tower(10,54)14x14；lab(-28,62)42x12；gym(-70,60)36x16；dist(48,30)16x10
scattered = [
    (-80, 15), (-80, 45), (-60, 12), (-60, 48), (-40, 12),
    (-40, 48), (-32, 48), (-20, 12), (-20, 48), (0, 12),
    (0, 48), (8, 12), (20, 12), (22, 48), (40, 12),
]
assert len(scattered) == 15
spots.extend(scattered)

objs = []
for i, (x, y) in enumerate(spots):
    t, c = plant_tree(i, x, y, i % 3, n_perimeter, n_road)
    objs.append(t)
    objs.append(c)

print(f"TREES: {len(spots)} (perimeter {n_perimeter}, roadside {n_road}, scattered 15)")
print(f"OBJECTS: {len(objs)} (3 masters + {len(spots) - 3} linked copies, x2 parts)")
print(f"MATERIALS: trunk 1 + crown 6 = {1 + sum(len(v) for v in CROWN_MATS.values())}")
for m in bpy.data.materials:
    kinds = sorted({n.type for n in m.node_tree.nodes}) if m.use_nodes else []
    print(f"MAT {m.name}: nodes={kinds}")

# ---- 光照：太阳 3.5，自西南，仰角约 50 度（进 .blend，不渲染） ----
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

# ---- 回读 GLB 确认 ----
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB_PATH)
imported = [o for o in bpy.data.objects if o not in before]
print(f"GLB reimport OK: {len(imported)} objects")
n_trees = len([o for o in imported if o.name.startswith("Tree_")])
print(f"GLB reimport trees: {n_trees} tree objects")
for m in sorted({o.active_material for o in imported if o.active_material},
                key=lambda m: m.name):
    has_img = any(n.type == "TEX_IMAGE" for n in m.node_tree.nodes) if m.use_nodes else False
    base = None
    if m.use_nodes:
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        if bsdf is not None:
            base = tuple(round(v, 4) for v in bsdf.inputs["Base Color"].default_value[:3])
    print(f"GLB MAT {m.name}: has_image_texture={has_img} base_color_linear={base}")
for o in imported:
    bpy.data.objects.remove(o, do_unlink=True)

# ---- 删 .blend1 ----
blend1 = BLEND_PATH + "1"
if os.path.exists(blend1):
    os.remove(blend1)

print("DONE ov-trees")
