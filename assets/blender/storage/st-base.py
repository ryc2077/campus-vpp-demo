# st-base: 储能站地面基座 (concrete platform + yellow warning lines)
# 4 台柜子共用一个混凝土基座平台，Blender 中心 (64, 30)
# 平台 7.0(x) x 2.0(y) x 0.15(z) m，中心 (64, 30, 0.075)，顶面 z=0.15 正好接住柜底
# 颜色: 混凝土 #B9B3A8；警示黄 #E8B400；材质 Principled BSDF
import bpy
import math
import os
from mathutils import Vector

BLEND_PATH = "/home/hatch/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot/assets/blender/storage/st-base.blend"
GLB_PATH = "/home/hatch/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot/assets/models/st-base.glb"
PNG_PATH = "/home/hatch/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot/screenshots/blender/st-base.png"

# ---------- clean scene ----------
bpy.ops.wm.read_factory_settings(use_empty=True)

def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def hex_to_linear(h):
    h = h.lstrip("#")
    return tuple(srgb_to_linear(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4))

def make_material(name, hex_color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*hex_to_linear(hex_color), 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat

CONCRETE_MAT = make_material("Base_Concrete", "#B9B3A8", 0.9, 0.0)
YELLOW_MAT = make_material("Warning_Yellow", "#E8B400", 0.6, 0.0)
CABINET_MAT = make_material("Preview_Cabinet", "#3E5A50", 0.5, 0.2)
GROUND_MAT = make_material("Preview_Ground", "#D8D2C4", 0.95, 0.0)

# ---------- base platform ----------
# 平台 7.0 x 2.0 x 0.15 m，中心 (64, 30, 0.075)，顶面 z=0.15
PLATFORM_W, PLATFORM_D, PLATFORM_H = 7.0, 2.0, 0.15
CX, CY = 64.0, 30.0
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(CX, CY, PLATFORM_H / 2.0))
platform = bpy.context.active_object
platform.name = "Storage_Base_Platform"
platform.dimensions = (PLATFORM_W, PLATFORM_D, PLATFORM_H)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
platform.data.materials.append(CONCRETE_MAT)
# 边缘 0.05 m 倒角（只倒顶/底边角，板厚 0.15 留 0.05 平直侧面）
bev = platform.modifiers.new("EdgeBevel", 'BEVEL')
bev.width = 0.05
bev.segments = 2
bev.limit_method = 'ANGLE'

base_objs = [platform]

# ---------- warning lines ----------
# 沿平台外缘 0.3 m 处围成矩形框：线宽 0.1 m、厚 0.01 m、贴地面 (z 0~0.01)
# 平台外缘 x 60.5~67.5, y 29~31；线框内缘距平台 0.3 m：
# 南北两条 x 60.1~67.9 (长 7.8)，y 28.6~28.7 / 31.3~31.4
# 东西两条 y 28.7~31.3 (长 2.6)，x 60.1~60.2 / 67.8~67.9
LINE_W, LINE_T = 0.1, 0.01
strips = [
    ("Warning_Line_North", (7.8, LINE_W, LINE_T), (CX, CY + 1.0 + 0.35, LINE_T / 2.0)),
    ("Warning_Line_South", (7.8, LINE_W, LINE_T), (CX, CY - 1.0 - 0.35, LINE_T / 2.0)),
    ("Warning_Line_East",  (LINE_W, 2.6, LINE_T), (CX + 3.5 + 0.35, CY, LINE_T / 2.0)),
    ("Warning_Line_West",  (LINE_W, 2.6, LINE_T), (CX - 3.5 - 0.35, CY, LINE_T / 2.0)),
]
for name, dims, loc in strips:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    strip = bpy.context.active_object
    strip.name = name
    strip.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    strip.data.materials.append(YELLOW_MAT)
    base_objs.append(strip)

# ---------- preview-only schematic cabinets (不导出) ----------
# 按 st-cabinet.py 的精确位置：单柜 1.3 x 1.0 x 2.3 m，中心 x=61.6/63.2/64.8/66.4，y=30，柜底 z=0.15
for i, cx in enumerate((61.6, 63.2, 64.8, 66.4)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(cx, CY, 0.15 + 2.3 / 2.0))
    cab = bpy.context.active_object
    cab.name = "Preview_Cabinet_%d" % (i + 1)
    cab.dimensions = (1.3, 1.0, 2.3)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    cab.data.materials.append(CABINET_MAT)

# ---------- preview-only ground (不导出) ----------
bpy.ops.mesh.primitive_plane_add(size=30.0, location=(CX, CY, 0.0))
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
sun.location = (CX - 20.0, CY - 20.0, 30.0)
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

# ---------- camera: 45° 俯视，看清基座与警戒线 ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35.0
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera = cam
cam.location = (CX + 5.5, CY - 7.5, 5.5)
target = Vector((CX, CY, 0.3))
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

# ---------- export .glb (只选本件对象：平台 + 4 条警戒线) ----------
bpy.ops.object.select_all(action='DESELECT')
for ob in base_objs:
    ob.select_set(True)
bpy.context.view_layer.objects.active = base_objs[0]
bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format='GLB',
                           use_selection=True, export_apply=True)

# ---------- 回读验证 glb ----------
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB_PATH)
imported = [ob for ob in bpy.data.objects if ob not in before]
print("GLB reimport objects:", len(imported),
      [ob.name for ob in imported])
assert len(imported) == 5, "glb reimport failed: expected 5 objects, got %d" % len(imported)
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
print("DONE st-base")
