# ov-trees: 树木（总览件）
# Blender 坐标 x 向东、y 向北、z 向上，单位米
# 内容：3 个母版（球冠/锥冠/椭圆冠）× 链接复制，约 146 棵
#   校园周边密植带（矩形 x ±120、y ±105，间距约 8m）
#   东侧路旁行道树（x=100、y -90~90，间距 10m）
#   楼间零星点缀 15 棵（教学楼区 y=10~50，避开楼体和道路）
# 不做草坪花坛 / 道路
import bpy
import math
import os
import random

BASE = os.path.expanduser(
    "~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
BLEND_PATH = os.path.join(BASE, "assets/blender/overview/ov-trees.blend")
GLB_PATH = os.path.join(BASE, "assets/models/ov-trees.glb")
PNG_PATH = os.path.join(BASE, "screenshots/blender/ov-trees.png")


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


# ---- 清空场景 ----
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for m in list(bpy.data.materials):
    bpy.data.materials.remove(m)

mat_trunk = make_mat("Trunk_Brown", "#7A5A38", 1.0)
mat_green = make_mat("Crown_Green", "#4E8A3F", 0.95)
mat_yellow = make_mat("Crown_YellowGreen", "#8AA84A", 0.95)

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
    crown.data.materials.append(mat_green)
    masters.append((trunk, crown, crown_z, mheight))


def linked_copy(obj, name):
    c = obj.copy()
    c.data = obj.data  # 共享网格数据：链接复制
    bpy.context.collection.objects.link(c)
    c.name = name
    return c


def plant_tree(idx, x, y, form_idx):
    """在 (x, y) 种一棵树：母版 form_idx，目标成树高 3~6m 随机，冠色绿/黄绿混搭。"""
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
    # 冠色混搭：对象级材质槽覆盖（网格仍共享）
    crown_mat = mat_green if random.random() < 0.6 else mat_yellow
    crown.material_slots[0].link = "OBJECT"
    crown.material_slots[0].material = crown_mat
    return trunk, crown


# ---- 分布 ----
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
    t, c = plant_tree(i, x, y, i % 3)
    objs.append(t)
    objs.append(c)

print(f"TREES: {len(spots)} (perimeter {n_perimeter}, roadside {n_road}, scattered 15)")
print(f"OBJECTS: {len(objs)} (3 masters + {len(spots) - 3} linked copies, x2 parts)")

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

# ---- 相机：高处正交俯视，覆盖整个树带（240 x 210m） ----
cam_data = bpy.data.cameras.new("Camera")
cam_data.type = "ORTHO"
cam_data.ortho_scale = 280
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera = cam
cam.location = (0, 0, 250)
cam.rotation_euler = (0, 0, 0)  # 直视向下（-Z）

# ---- 渲染设置：Eevee，640x360，16 采样 ----
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
os.makedirs(os.path.dirname(PNG_PATH), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)

# ---- 导出 GLB：只选本件 ----
bpy.ops.object.select_all(action="DESELECT")
for o in objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format="GLB",
                          use_selection=True, export_apply=True)

# ---- 渲染预览 ----
bpy.ops.render.render(write_still=True)

# ---- 回读 GLB 确认 ----
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB_PATH)
imported = [o for o in bpy.data.objects if o not in before]
print(f"GLB reimport OK: {len(imported)} objects")
for o in imported:
    bpy.data.objects.remove(o, do_unlink=True)

# ---- 删 .blend1 ----
blend1 = BLEND_PATH + "1"
if os.path.exists(blend1):
    os.remove(blend1)

print("DONE ov-trees")
