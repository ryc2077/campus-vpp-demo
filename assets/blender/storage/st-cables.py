# st-cables: 储能站线缆与接线箱
# 柜间线槽 + 柜顶竖管 + 北侧接线箱 + 地面电缆沟盖板
# 柜体位置尺寸取自 st-cabinet.py: 4 台柜, 单柜 1.3(x)x1.0(y)x2.3(z)m,
# 柜中心 x = 61.6 / 63.2 / 64.8 / 66.4, y = 30.0, 柜底 z = 0.15,
# 柜体顶 z = 2.45, 顶盖顶 z = 2.51, 柜北沿 y = 30.5
# 本件只做线槽/竖管/接线箱/电缆沟盖板, 不做柜体/门/基座/围栏
# 颜色: 线槽浅灰 #C0C5C9, 接线箱/沟盖板深灰 #424A52
# 材质 Principled BSDF; 十六进制 sRGB 先转线性再赋值
import bpy
import math
import os
from mathutils import Vector

BASE = "/home/hatch/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot"
BLEND_PATH = BASE + "/assets/blender/storage/st-cables.blend"
GLB_PATH = BASE + "/assets/models/st-cables.glb"
PNG_PATH = BASE + "/screenshots/blender/st-cables.png"

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

TRAY_MAT = make_material("CableTray_LightGray", "#C0C5C9", 0.6, 0.3)
RISER_MAT = make_material("Riser_MetalGray", "#8A8F94", 0.45, 0.6)
BOX_MAT = make_material("JunctionBox_DarkGray", "#424A52", 0.55, 0.25)
BOX_DARK_MAT = make_material("JunctionBox_Dark", "#363D44", 0.6, 0.25)  # 箱门/顶盖略深
SEAM_MAT = make_material("DoorSeam", "#2B3136", 0.7, 0.1)
TRENCH_MAT = make_material("TrenchCover_DarkGray", "#424A52", 0.8, 0.1)
CABINET_MAT = make_material("Preview_Cabinet", "#3E5A50", 0.5, 0.2)  # 仅预览示意柜
GROUND_MAT = make_material("Preview_Ground", "#B9B3A8", 0.9, 0.0)

CAB_X = [61.6, 63.2, 64.8, 66.4]
CY = 30.0
CAB_TOP = 2.45          # 柜体顶
CAP_TOP = 2.51          # 顶盖顶

part_objs = []

def add_box(name, dims, loc, mat, bevel=0.015, rot_z=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.dimensions = dims
    if rot_z:
        ob.rotation_euler = (0.0, 0.0, rot_z)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(mat)
    if bevel:
        bev = ob.modifiers.new("EdgeBevel", 'BEVEL')
        bev.width = bevel
        bev.segments = 2
        bev.limit_method = 'ANGLE'
    return ob

# ---------- 柜间线槽: 沿 x 通长 6.1m, 0.2(y) x 0.15(z), 柜顶后方(y+ 侧) ----------
# y 中心 30.40: y 范围 30.30-30.50, 贴着柜北沿; 底部 z=2.675, 高出顶盖留竖管接头
TRAY_Y = 30.40
TRAY_Z = 2.75
tray = add_box("CableTray", (6.1, 0.2, 0.15), (64.0, TRAY_Y, TRAY_Z), TRAY_MAT)
part_objs.append(tray)
# 线槽两端堵板(略厚一圈, 读出端头)
for ex in (60.95, 67.05):
    cap = add_box("CableTray_EndCap", (0.04, 0.24, 0.19),
                  (ex, TRAY_Y, TRAY_Z), TRAY_MAT, bevel=0.01)
    part_objs.append(cap)

# ---------- 柜顶竖管: 每台柜顶一根, r=0.05, 从顶盖接到线槽底 ----------
for i, cx in enumerate(CAB_X):
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.05, depth=0.20,
                                        location=(cx, TRAY_Y, 2.58))
    riser = bpy.context.active_object
    riser.name = f"CabinetRiser_{i + 1}"
    riser.data.materials.append(RISER_MAT)
    part_objs.append(riser)

# ---------- 接线箱: 0.8(x) x 0.5(y) x 1.2(z), 中心 (64, 31.5), 底 z=0 ----------
BOX_X, BOX_Y = 64.0, 31.5
box = add_box("JunctionBox", (0.8, 0.5, 1.2), (BOX_X, BOX_Y, 0.6), BOX_MAT)
part_objs.append(box)
# 顶盖: 各边伸出 0.03, 厚 0.05
box_cap = add_box("JunctionBox_TopCap", (0.86, 0.56, 0.05),
                  (BOX_X, BOX_Y, 1.225), BOX_DARK_MAT, bevel=0.01)
part_objs.append(box_cap)
# 箱门: 朝北面(外侧检修面, y=31.75 面), 0.6 x 1.0 的门板, 略深色读出门缝
# (门朝南会被柜子挡住, 预览与检修都看不到; 朝北为外侧检修面)
door = add_box("JunctionBox_Door", (0.6, 0.02, 1.0),
               (BOX_X, BOX_Y + 0.26, 0.6), SEAM_MAT, bevel=0.005)
part_objs.append(door)
# 门把手: 门板外侧横向小把手, 金属灰
handle = add_box("JunctionBox_Handle", (0.14, 0.04, 0.03),
                 (BOX_X + 0.18, BOX_Y + 0.28, 0.65), RISER_MAT, bevel=0.005)
part_objs.append(handle)

# ---------- 地面电缆沟盖板: 接线箱南面 -> 每台柜子北沿, 扇形各引一根 ----------
# 盖板 0.3m 宽, 0.05m 高, 沿地面(z=0.025); 起点柜北沿(cx, 30.5),
# 终点接线箱南面 y=31.25, x 在箱南面 spread 开(63.7/63.9/64.1/64.3)
BOX_TARGETS = [63.7, 63.9, 64.1, 64.3]
for i, cx in enumerate(CAB_X):
    sx, sy = cx, 30.5
    tx, ty = BOX_TARGETS[i], 31.25
    dx, dy = tx - sx, ty - sy
    length = math.hypot(dx, dy) + 0.20  # 两端各伸 0.1 埋进箱面/柜沿, 读出对接
    mx, my = (sx + tx) / 2.0, (sy + ty) / 2.0
    ang = math.atan2(dy, dx)
    strip = add_box(f"TrenchCover_{i + 1}", (length, 0.3, 0.05),
                    (mx, my, 0.025), TRENCH_MAT, bevel=0.01, rot_z=ang)
    part_objs.append(strip)

# ---------- preview-only 示意柜体 (不导出) ----------
preview_objs = []
for i, cx in enumerate(CAB_X):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(cx, CY, 0.15 + 2.3 / 2.0))
    body = bpy.context.active_object
    body.name = f"Preview_Cabinet_{i + 1}"
    body.dimensions = (1.3, 1.0, 2.3)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    body.data.materials.append(CABINET_MAT)
    preview_objs.append(body)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(cx, CY, 2.48))
    cap = bpy.context.active_object
    cap.name = f"Preview_Cabinet_{i + 1}_TopCap"
    cap.dimensions = (1.4, 1.1, 0.06)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    cap.data.materials.append(CABINET_MAT)
    preview_objs.append(cap)

# ---------- preview-only ground (不导出) ----------
bpy.ops.mesh.primitive_plane_add(size=30.0, location=(64.0, 30.0, 0.0))
ground = bpy.context.active_object
ground.name = "Preview_Ground"
ground.data.materials.append(GROUND_MAT)

# ---------- lighting (SPEC §2) ----------
sun_data = bpy.data.lights.new("Sun", type='SUN')
sun_data.energy = 3.5
sun_data.use_shadow = True
sun = bpy.data.objects.new("Sun", sun_data)
bpy.context.collection.objects.link(sun)
sun.location = (64.0 - 20.0, 30.0 - 20.0, 30.0)
light_dir = Vector((math.cos(math.radians(50)) * math.cos(math.radians(45)),
                    math.cos(math.radians(50)) * math.sin(math.radians(45)),
                    -math.sin(math.radians(50))))
sun.rotation_mode = 'QUATERNION'
sun.rotation_quaternion = light_dir.to_track_quat('-Z', 'Y')

world = bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.65, 0.78, 0.88, 1.0)
bg.inputs["Strength"].default_value = 1.0

# ---------- camera: 北侧偏东 45° 俯视, 前景接线箱 + 沟盖板, 后景柜顶线槽 ----------
# 接线箱在柜子北侧(高 1.2m 会被 2.3m 柜子挡住), 必须从北侧拍
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35.0
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera = cam
cam.location = (64.0 + 7.0, 30.0 + 8.5, 6.5)
target = Vector((64.0, 30.8, 1.3))
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
for ob in part_objs:
    ob.select_set(True)
bpy.context.view_layer.objects.active = part_objs[0]
bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format='GLB',
                           use_selection=True, export_apply=True)

# ---------- 回读验证 glb ----------
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB_PATH)
imported = [ob for ob in bpy.data.objects if ob not in before]
print("GLB reimport objects:", len(imported),
      [ob.name for ob in imported])
assert len(imported) >= 12, "glb reimport failed: too few objects"
# 删掉回读的副本, 恢复干净场景再渲染
bpy.ops.object.select_all(action='DESELECT')
for ob in imported:
    ob.select_set(True)
bpy.ops.object.delete()

# ---------- render preview ----------
bpy.ops.render.render(write_still=True)
print("Preview saved:", PNG_PATH, "exists:", os.path.exists(PNG_PATH),
      "size:", os.path.getsize(PNG_PATH) if os.path.exists(PNG_PATH) else 0)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("DONE st-cables")
