# ov-flag-lamp: 旗杆路灯（总览件）
# Blender 坐标 x 向东、y 向北、z 向上，单位米
# 内容：南门广场北侧 3 根旗杆（主杆 12m、两侧 10m，主杆挂红旗 1.8x1.2m）
#       + 南侧主路 y=-108 与东侧主路 x=108 沿路路灯，每 20m 一盏，共 16 盏
# 不做铺装（ov-road-walk）、不做主干道路面（ov-road-main）
import bpy
import math
import os
from mathutils import Vector

ROOT = os.path.expanduser(
    "~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
BLEND_PATH = os.path.join(ROOT, "assets/blender/overview/ov-flag-lamp.blend")
GLB_PATH = os.path.join(ROOT, "assets/models/ov-flag-lamp.glb")
PNG_PATH = os.path.join(ROOT, "screenshots/blender/ov-flag-lamp.png")


def srgb_to_linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_to_linear(h):
    h = h.lstrip("#")
    return tuple(srgb_to_linear(int(h[i:i + 2], 16)) for i in (0, 2, 4))


def make_mat(name, hex_color, roughness=0.9, metallic=0.0,
             emission_hex=None, emission_strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*hex_to_linear(hex_color), 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if emission_hex is not None:
        bsdf.inputs["Emission Color"].default_value = (*hex_to_linear(emission_hex), 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    return m


def box(name, center, size, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    o = bpy.context.active_object
    o.name = name
    o.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    return o


def cylinder(name, center, radius, depth, mat, rotation=(0, 0, 0), vertices=16):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
                                        depth=depth, location=center,
                                        rotation=rotation)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(mat)
    return o


def sphere(name, center, r, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8,
                                         radius=r, location=center)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(mat)
    return o


# ---- 清空场景 ----
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for m in list(bpy.data.materials):
    bpy.data.materials.remove(m)

mat_pole = make_mat("FlagPole_Silver", "#C0C5C9", roughness=0.35, metallic=0.9)
mat_stone = make_mat("FlagBase_Stone", "#B9B3A8", roughness=0.95)
mat_flag = make_mat("Flag_Red", "#C0392B", roughness=0.7)
mat_lamp_pole = make_mat("LampPole_DarkGrey", "#424A52", roughness=0.6, metallic=0.6)
mat_lamp_head = make_mat("LampHead_DarkGrey", "#424A52", roughness=0.6, metallic=0.4)
mat_light = make_mat("Lamp_WarmWhite", "#FFE9C0", roughness=0.4,
                     emission_hex="#FFE9C0", emission_strength=1.5)

objs = []

# ---- 旗杆：南门广场北侧 (0, -88)，间距 2.5m；主杆 12m、两侧 10m ----
flag_x = [-2.5, 0.0, 2.5]
flag_h = [10.0, 12.0, 10.0]
for i, (fx, fh) in enumerate(zip(flag_x, flag_h)):
    base = box(f"FlagBase_{i}", (fx, -88, 0.30), (0.7, 0.7, 0.6), mat_stone)
    bev = base.modifiers.new("Bevel", "BEVEL")
    bev.width = 0.03
    bev.segments = 1
    objs.append(base)
    pole = cylinder(f"FlagPole_{i}", (fx, -88, 0.6 + fh / 2.0), 0.08, fh, mat_pole)
    objs.append(pole)
    finial = sphere(f"FlagPole_Top_{i}", (fx, -88, 0.6 + fh + 0.10), 0.12, mat_pole)
    objs.append(finial)

# ---- 红旗：主杆顶，1.8 x 1.2m，向东展开，薄片微弯（y 向波浪） ----
nx, ny = 13, 9
fw, fhgt = 1.8, 1.2
z_top = 0.6 + 12.0
verts = []
for j in range(ny):
    for i in range(nx):
        x = fw * i / (nx - 1)
        z = (z_top - fhgt) + fhgt * j / (ny - 1)
        # 微弯：中部向北微凸，自由端波幅略大
        y = -88 + 0.10 * math.sin(math.pi * x / fw) * (0.4 + 0.6 * x / fw)
        verts.append((x, y, z))
faces = []
for j in range(ny - 1):
    for i in range(nx - 1):
        a = j * nx + i
        faces.append((a, a + 1, a + nx + 1, a + nx))
mesh = bpy.data.meshes.new("FlagMesh")
mesh.from_pydata(verts, [], faces)
mesh.update()
flag_obj = bpy.data.objects.new("Flag_Main", mesh)
bpy.context.collection.objects.link(flag_obj)
flag_obj.data.materials.append(mat_flag)
sol = flag_obj.modifiers.new("Solidify", "SOLIDIFY")
sol.thickness = 0.01
objs.append(flag_obj)

# ---- 路灯：南侧主路 y=-108，x=-70..70 每 20m，8 盏，横臂向南（伸向路面） ----
#          东侧主路 x=108，y=-80..60 每 20m，8 盏，横臂向东（伸向路面），共 16 盏 ----
def make_lamp(idx, px, py, arm_dir):
    # arm_dir: (dx, dy) 单位方向
    ax, ay = arm_dir
    base = cylinder(f"LampBase_{idx:02d}", (px, py, 0.175), 0.14, 0.35, mat_lamp_pole)
    objs.append(base)
    pole = cylinder(f"LampPole_{idx:02d}", (px, py, 3.0), 0.06, 6.0, mat_lamp_pole)
    objs.append(pole)
    # 横臂：长 1.2m，水平，中心在杆顶外移 0.6m 处
    hx, hy = px + ax * 0.6, py + ay * 0.6
    if ax != 0:  # 沿 x 向：绕 Y 转 90 度
        arm = cylinder(f"LampArm_{idx:02d}", (hx, hy, 6.0), 0.05, 1.2,
                       mat_lamp_pole, rotation=(0, math.radians(90), 0))
        head_size = (0.55, 0.28, 0.12)
        plate_size = (0.45, 0.22, 0.02)
    else:        # 沿 y 向：绕 X 转 90 度
        arm = cylinder(f"LampArm_{idx:02d}", (hx, hy, 6.0), 0.05, 1.2,
                       mat_lamp_pole, rotation=(math.radians(90), 0, 0))
        head_size = (0.28, 0.55, 0.12)
        plate_size = (0.22, 0.45, 0.02)
    objs.append(arm)
    ex, ey = px + ax * 1.2, py + ay * 1.2
    head = box(f"LampHead_{idx:02d}", (ex, ey, 5.95), head_size, mat_lamp_head)
    bev = head.modifiers.new("Bevel", "BEVEL")
    bev.width = 0.02
    bev.segments = 1
    objs.append(head)
    plate = box(f"LampPlate_{idx:02d}", (ex, ey, 5.88), plate_size, mat_light)
    objs.append(plate)


lamp_idx = 0
for x in (-70, -50, -30, -10, 10, 30, 50, 70):
    make_lamp(lamp_idx, x, -108, (0, -1))
    lamp_idx += 1
for y in (-80, -60, -40, -20, 0, 20, 40, 60):
    make_lamp(lamp_idx, 108, y, (1, 0))
    lamp_idx += 1
assert lamp_idx == 16, lamp_idx

print(f"OBJECTS: {len(objs)} (flag 10 incl. flag sheet, lamps 16x5=80)")

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

# ---- 相机：东南高处 45 度俯视，看旗杆 + 南侧路灯一排 + 东侧路灯 ----
cam_data = bpy.data.cameras.new("Camera")
cam_data.type = "PERSP"
cam_data.lens = 35
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera = cam
cam.location = (28, -128, 20)
target_empty = bpy.data.objects.new("CamTarget", None)
bpy.context.collection.objects.link(target_empty)
target_empty.location = (-5, -96, 5)
track = cam.constraints.new("TRACK_TO")
track.target = target_empty
track.track_axis = "TRACK_NEGATIVE_Z"
track.up_axis = "UP_Y"
bpy.context.view_layer.update()

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

print("DONE ov-flag-lamp")
