# st-cabinet: 储能站柜体 (100kW/215kWh)
# 3 台电池柜 + 1 台 PCS 柜，沿 x 一字排开，Blender 中心 (64, 30)
# 单柜 1.3(x) x 1.0(y) x 2.3(z) m，柜间距 0.3 m，底座留高 0.15 m
# 颜色: 深绿灰 #3E5A50；材质 Principled BSDF, roughness 0.5, metallic 0.2
import bpy
import math
import os
from mathutils import Vector

BLEND_PATH = "/home/hatch/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot/assets/blender/storage/st-cabinet.blend"
GLB_PATH = "/home/hatch/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot/assets/models/st-cabinet.glb"
PNG_PATH = "/home/hatch/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot/screenshots/blender/st-cabinet.png"

# ---------- clean scene ----------
bpy.ops.wm.read_factory_settings(use_empty=True)

def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def hex_to_linear(h):
    h = h.lstrip("#")
    return tuple(srgb_to_linear(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4))

def make_material(name, hex_color, roughness=0.5, metallic=0.2):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*hex_to_linear(hex_color), 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat

CABINET_MAT = make_material("Cabinet_GreenGray", "#3E5A50", 0.5, 0.2)
CAP_MAT = make_material("Cabinet_Cap", "#35483F", 0.55, 0.2)  # 同色系略深的顶盖
GROUND_MAT = make_material("Preview_Ground", "#B9B3A8", 0.9, 0.0)

# ---------- cabinets ----------
# 总宽 4*1.3 + 3*0.3 = 6.1 m，中心 x=64 -> 首柜中心 x=61.6
CAB_W, CAB_D, CAB_H = 1.3, 1.0, 2.3
GAP = 0.3
BASE_Z = 0.15            # 底座留高（基座是 st-base 的活）
CY = 30.0
x0 = 64.0 - (4 * CAB_W + 3 * GAP) / 2.0 + CAB_W / 2.0

cabinet_objs = []
for i in range(4):
    cx = x0 + i * (CAB_W + GAP)
    name = "PCS_Cabinet" if i == 3 else f"Battery_Cabinet_{i + 1}"
    # 柜体
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(cx, CY, BASE_Z + CAB_H / 2.0))
    body = bpy.context.active_object
    body.name = name
    body.dimensions = (CAB_W, CAB_D, CAB_H)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    body.data.materials.append(CABINET_MAT)
    # 小倒角
    bev = body.modifiers.new("EdgeBevel", 'BEVEL')
    bev.width = 0.02
    bev.segments = 2
    bev.limit_method = 'ANGLE'
    # 顶盖小檐：各边伸出 0.05 m，厚 0.06 m
    bpy.ops.mesh.primitive_cube_add(size=1.0,
        location=(cx, CY, BASE_Z + CAB_H + 0.03))
    cap = bpy.context.active_object
    cap.name = name + "_TopCap"
    cap.dimensions = (CAB_W + 0.10, CAB_D + 0.10, 0.06)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    cap.data.materials.append(CAP_MAT)
    bev2 = cap.modifiers.new("EdgeBevel", 'BEVEL')
    bev2.width = 0.015
    bev2.segments = 2
    bev2.limit_method = 'ANGLE'
    cabinet_objs.extend([body, cap])

# ---------- preview-only ground (不导出) ----------
bpy.ops.mesh.primitive_plane_add(size=30.0, location=(64.0, 30.0, 0.0))
ground = bpy.context.active_object
ground.name = "Preview_Ground"
ground.data.materials.append(GROUND_MAT)

# ---------- lighting (SPEC §2) ----------
# 太阳光：能量 3.5，从西南来，仰角约 50°，开阴影
sun_data = bpy.data.lights.new("Sun", type='SUN')
sun_data.energy = 3.5
sun_data.use_shadow = True
sun = bpy.data.objects.new("Sun", sun_data)
bpy.context.collection.objects.link(sun)
sun.location = (64.0 - 20.0, 30.0 - 20.0, 30.0)
light_dir = Vector((math.cos(math.radians(50)) * math.cos(math.radians(45)),
                    math.cos(math.radians(50)) * math.sin(math.radians(45)),
                    -math.sin(math.radians(50))))  # 朝东北下方
sun.rotation_mode = 'QUATERNION'
sun.rotation_quaternion = light_dir.to_track_quat('-Z', 'Y')

# 世界背景：淡蓝 (0.65, 0.78, 0.88)，强度 1.0
world = bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.65, 0.78, 0.88, 1.0)
bg.inputs["Strength"].default_value = 1.0

# ---------- camera: 45° 俯视，看清 4 台柜子 ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35.0
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera = cam
cam.location = (64.0 + 6.5, 30.0 - 9.0, 7.0)
target = Vector((64.0, 30.0, 1.2))
cam.rotation_mode = 'QUATERNION'
cam.rotation_quaternion = (target - cam.location).to_track_quat('-Z', 'Y')

# ---------- render settings ----------
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.eevee.taa_render_samples = 16
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100
scene.render.filepath = PNG_PATH

# ---------- save .blend ----------
os.makedirs(os.path.dirname(BLEND_PATH), exist_ok=True)
os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
os.makedirs(os.path.dirname(PNG_PATH), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)

# ---------- export .glb (只选本件对象) ----------
bpy.ops.object.select_all(action='DESELECT')
for ob in cabinet_objs:
    ob.select_set(True)
bpy.context.view_layer.objects.active = cabinet_objs[0]
bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format='GLB',
                           use_selection=True, export_apply=True)

# ---------- 回读验证 glb ----------
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB_PATH)
imported = [ob for ob in bpy.data.objects if ob not in before]
print("GLB reimport objects:", len(imported),
      [ob.name for ob in imported])
assert len(imported) >= 8, "glb reimport failed: too few objects"
# 删掉回读的副本，恢复干净场景再渲染
bpy.ops.object.select_all(action='DESELECT')
for ob in imported:
    ob.select_set(True)
bpy.ops.object.delete()

# ---------- render preview ----------
bpy.ops.render.render(write_still=True)
print("Preview saved:", PNG_PATH, "exists:", os.path.exists(PNG_PATH),
      "size:", os.path.getsize(PNG_PATH) if os.path.exists(PNG_PATH) else 0)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("DONE st-cabinet")
