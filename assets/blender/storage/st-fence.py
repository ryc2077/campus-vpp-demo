# st-fence: 储能站围栏标识
# 三面围栏（南面留 1.5m 出入口，不做门）+ “高压危险”标识牌 + 每柜北侧小黄牌
# 围栏范围 x 60.0-68.0m、y 28.5-31.5m，高 1.8m；柜子位置取自 st-cabinet.py
# （4 台柜中心 x = 61.6 / 63.2 / 64.8 / 66.4，柜 y 宽 1.0m、中心 y=30，柜底 z=0.15）
# 颜色: 立柱/横杆深灰 #424A52，竖条金属灰 #8A8F94，标识牌警示黄 #E8B400
# 材质 Principled BSDF, 十六进制 sRGB 先转线性再赋值
import bpy
import math
import os
from mathutils import Vector

BLEND_PATH = "/home/hatch/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot/assets/blender/storage/st-fence.blend"
GLB_PATH = "/home/hatch/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot/assets/models/st-fence.glb"
PNG_PATH = "/home/hatch/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot/screenshots/blender/st-fence.png"

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

POST_MAT = make_material("Fence_DarkGray", "#424A52", 0.6, 0.4)   # 立柱/横杆
BAR_MAT = make_material("Fence_MetalGray", "#8A8F94", 0.4, 0.7)   # 竖条
YELLOW_MAT = make_material("Sign_Yellow", "#E8B400", 0.5, 0.1)    # 标识牌黄底
BLACK_MAT = make_material("Sign_Black", "#1A1A1A", 0.6, 0.1)      # 边框/示意横条
GROUND_MAT = make_material("Preview_Ground", "#B9B3A8", 0.9, 0.0)
CABINET_MAT = make_material("Preview_Cabinet", "#3E5A50", 0.5, 0.2)

def add_box(name, dims, loc, mat):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if mat is not None:
        ob.data.materials.append(mat)
    return ob

def join_objects(objs, name):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objs:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    joined = bpy.context.active_object
    joined.name = name
    return joined

# ---------- fence layout ----------
# 五段栏杆：北整段、南左、南右（中间 x 63.25-64.75 留 1.5m 出入口）、西、东
X0, X1 = 60.0, 68.0
Y_S, Y_N = 28.5, 31.5
GATE_X0, GATE_X1 = 63.25, 64.75   # 南面出入口
FENCE_H = 1.8
POST_SIZE = 0.08
RAIL_Z = (0.15, 1.70)             # 上下两道横杆高度
BAR_Z0, BAR_Z1 = 0.10, 1.75       # 竖条上下端
BAR_STEP = 0.15

# 每段：(x1, y1, x2, y2)
runs = [
    ("North", X0, Y_N, X1, Y_N),
    ("SouthLeft", X0, Y_S, GATE_X0, Y_S),
    ("SouthRight", GATE_X1, Y_S, X1, Y_S),
    ("West", X0, Y_S, X0, Y_N),
    ("East", X1, Y_S, X1, Y_N),
]

def run_length(x1, y1, x2, y2):
    return math.hypot(x2 - x1, y2 - y1)

def point_on_run(x1, y1, x2, y2, t):
    return (x1 + (x2 - x1) * t, y1 + (y2 - y1) * t)

# ---------- posts: 每 2m 一根，含端点 ----------
post_positions = set()
for _name, x1, y1, x2, y2 in runs:
    L = run_length(x1, y1, x2, y2)
    n = int(round(L / 2.0))
    for i in range(n + 1):
        px, py = point_on_run(x1, y1, x2, y2, (i * 2.0) / L if L > 0 else 0)
        post_positions.add((round(px, 3), round(py, 3)))
    # 端点（出入口两侧的门柱）
    post_positions.add((round(x2, 3), round(y2, 3)))

post_objs = []
for i, (px, py) in enumerate(sorted(post_positions)):
    post_objs.append(add_box(f"Fence_Post_{i:02d}",
                             (POST_SIZE, POST_SIZE, FENCE_H),
                             (px, py, FENCE_H / 2.0), POST_MAT))
print("posts:", len(post_objs))

# ---------- rails: 上下两道横杆 ----------
rail_objs = []
for rname, x1, y1, x2, y2 in runs:
    L = run_length(x1, y1, x2, y2)
    mx, my = (x1 + x2) / 2.0, (y1 + y2) / 2.0
    along_x = abs(x2 - x1) > abs(y2 - y1)
    dims = (L, 0.05, 0.05) if along_x else (0.05, L, 0.05)
    for j, rz in enumerate(RAIL_Z):
        rail_objs.append(add_box(f"Fence_Rail_{rname}_{j}",
                                 dims, (mx, my, rz), POST_MAT))

# ---------- vertical bars: 每 0.15m 一根细杆，避开立柱 ----------
bar_objs = []
for rname, x1, y1, x2, y2 in runs:
    L = run_length(x1, y1, x2, y2)
    along_x = abs(x2 - x1) > abs(y2 - y1)
    n = int(L / BAR_STEP)
    for k in range(1, n + 1):
        d = k * BAR_STEP
        if d >= L - 0.02:
            continue
        bx, by = point_on_run(x1, y1, x2, y2, d / L)
        # 避开立柱（0.08 宽 + 余量）
        if any(abs(bx - px) < 0.07 and abs(by - py) < 0.07 for px, py in post_positions):
            continue
        dims = (0.02, 0.02, BAR_Z1 - BAR_Z0)
        bar_objs.append(add_box(f"Fence_Bar_{rname}_{k:03d}",
                                dims, (bx, by, (BAR_Z0 + BAR_Z1) / 2.0), BAR_MAT))
print("vertical bars:", len(bar_objs))

posts_joined = join_objects(post_objs, "Fence_Posts")
rails_joined = join_objects(rail_objs, "Fence_Rails")
bars_joined = join_objects(bar_objs, "Fence_VerticalBars")
for ob in (posts_joined, rails_joined, bars_joined):
    bev = ob.modifiers.new("EdgeBevel", 'BEVEL')
    bev.width = 0.01
    bev.segments = 1
    bev.limit_method = 'ANGLE'

# ---------- main sign: 南面出入口东侧旁，“高压危险”牌 ----------
# 立杆 (65.35, 28.15)，牌面 0.6x0.4 朝南，牌顶不超过立杆顶 1.6m
SIGN_X, SIGN_Y = 65.35, 28.15
sign_objs = []
sign_objs.append(add_box("Sign_Pole", (0.06, 0.06, 1.6),
                         (SIGN_X, SIGN_Y, 0.8), POST_MAT))
# 黑色底框（比黄牌面略大一圈，露出黑边）
sign_objs.append(add_box("Sign_BoardFrame", (0.66, 0.02, 0.46),
                         (SIGN_X, SIGN_Y, 1.35), BLACK_MAT))
# 黄牌面（朝南一面在前）
sign_objs.append(add_box("Sign_BoardYellow", (0.60, 0.03, 0.40),
                         (SIGN_X, SIGN_Y - 0.005, 1.35), YELLOW_MAT))
# 文字用黑色横条示意（南/北两面各两道）
for face, dy in (("South", -0.025), ("North", 0.015)):
    for j, bz in enumerate((1.43, 1.27)):
        sign_objs.append(add_box(f"Sign_TextBar_{face}_{j}",
                                 (0.40, 0.012, 0.06),
                                 (SIGN_X, SIGN_Y + dy, bz), BLACK_MAT))

# ---------- small plaques: 每台柜子北侧围栏上 1 块小黄牌 0.3x0.2 ----------
CABINET_X = [61.6, 63.2, 64.8, 66.4]
plaque_objs = []
for i, cx in enumerate(CABINET_X):
    plaque_objs.append(add_box(f"Plaque_Frame_{i + 1}",
                               (0.34, 0.015, 0.24), (cx, Y_N + 0.012, 1.20), BLACK_MAT))
    plaque_objs.append(add_box(f"Plaque_Yellow_{i + 1}",
                               (0.30, 0.02, 0.20), (cx, Y_N + 0.025, 1.20), YELLOW_MAT))
    plaque_objs.append(add_box(f"Plaque_Bar_{i + 1}",
                               (0.20, 0.012, 0.05), (cx, Y_N + 0.040, 1.20), BLACK_MAT))

part_objs = [posts_joined, rails_joined, bars_joined] + sign_objs + plaque_objs
print("part objects:", len(part_objs))

# ---------- preview-only: 示意地面 + 示意基座 + 4 台示意柜体（不导出） ----------
bpy.ops.mesh.primitive_plane_add(size=30.0, location=(64.0, 30.0, 0.0))
ground = bpy.context.active_object
ground.name = "Preview_Ground"
ground.data.materials.append(GROUND_MAT)

# 示意基座：仅柜体下方，7.0 x 1.8 m，顶面 z=0.15
add_box("Preview_Base", (7.0, 1.8, 0.15), (64.0, 30.0, 0.075), GROUND_MAT)
for i, cx in enumerate(CABINET_X):
    add_box(f"Preview_Cabinet_{i + 1}", (1.3, 1.0, 2.3),
            (cx, 30.0, 0.15 + 2.3 / 2.0), CABINET_MAT)

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

# ---------- camera: 45° 俯视，从南侧看清围栏、出入口与标识牌 ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35.0
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera = cam
cam.location = (64.0 + 5.0, 30.0 - 10.0, 6.5)
target = Vector((64.0, 30.0, 1.0))
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
assert len(imported) >= 20, "glb reimport failed: too few objects"
bpy.ops.object.select_all(action='DESELECT')
for ob in imported:
    ob.select_set(True)
bpy.ops.object.delete()

# ---------- render preview ----------
bpy.ops.render.render(write_still=True)
print("Preview saved:", PNG_PATH, "exists:", os.path.exists(PNG_PATH),
      "size:", os.path.getsize(PNG_PATH) if os.path.exists(PNG_PATH) else 0)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
# 删掉 Blender 产生的 .blend1 备份
blend1 = BLEND_PATH + "1"
if os.path.exists(blend1):
    os.remove(blend1)
    print("Removed backup:", blend1)
print("DONE st-fence")
