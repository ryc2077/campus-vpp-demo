# st-doors: 储能站电池舱门与散热 (st-cabinet 的配套件，只做门/把手/风扇罩/百叶)
# 柜体数据取自 st-cabinet.py（只读，不重算）：
#   4 台柜一字排开，单柜 1.3(x) x 1.0(y) x 2.3(z) m，柜中心 x = 61.6 / 63.2 / 64.8 / 66.4
#   柜中心 y = 30.0，柜底 z = 0.15，柜顶 z = 2.45，顶盖顶面 z = 2.51
#   南面 y = 29.5，北面 y = 30.5
# 本件：
#   南面双开门：每扇 0.6 x 2.0 x 0.03 m，门缝居中（缝宽 0.02），门板贴在柜面外 0.02 m
#   门把手：小横杆（沿 x 的圆柱，r=0.015，长 0.20），贴门板南面
#   顶部风扇罩：直径 0.4 m 浅灰圆盘 + 同心格栅环 + 十字条 + 中心毂，置于顶盖顶面
#   北面散热百叶：3 条横向细条，深灰，贴北面外 0.02 m
# 颜色：门板 #35483F（比柜体 #3E5A50 略深）；风扇盘 #C0C5C9；格栅/百叶 #424A52；把手金属灰 #8A8F94
# 材质只用 Principled BSDF；十六进制 sRGB 先转线性再赋值
import bpy
import math
import os
from mathutils import Vector

BLEND_PATH = "/home/hatch/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot/assets/blender/storage/st-doors.blend"
GLB_PATH = "/home/hatch/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot/assets/models/st-doors.glb"
PNG_PATH = "/home/hatch/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot/screenshots/blender/st-doors.png"

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

DOOR_MAT = make_material("Door_DarkGreenGray", "#35483F", 0.55, 0.2)
HANDLE_MAT = make_material("Handle_MetalGray", "#8A8F94", 0.35, 0.7)
FAN_MAT = make_material("Fan_LightGray", "#C0C5C9", 0.5, 0.4)
GRILLE_MAT = make_material("Grille_DarkGray", "#424A52", 0.6, 0.3)
LOUVER_MAT = make_material("Louver_DarkGray", "#424A52", 0.6, 0.3)
CABINET_MAT = make_material("Preview_Cabinet_GreenGray", "#3E5A50", 0.5, 0.2)
CAP_MAT = make_material("Preview_Cabinet_Cap", "#35483F", 0.55, 0.2)
GROUND_MAT = make_material("Preview_Ground", "#B9B3A8", 0.9, 0.0)

# ---------- 柜体基准（抄 st-cabinet.py） ----------
CAB_W, CAB_D, CAB_H = 1.3, 1.0, 2.3
GAP = 0.3
BASE_Z = 0.15
CY = 30.0
SOUTH_Y = CY - CAB_D / 2.0   # 29.5
NORTH_Y = CY + CAB_D / 2.0   # 30.5
CAP_TOP_Z = BASE_Z + CAB_H + 0.06  # 2.51，顶盖顶面
x0 = 64.0 - (4 * CAB_W + 3 * GAP) / 2.0 + CAB_W / 2.0
CENTERS_X = [x0 + i * (CAB_W + GAP) for i in range(4)]  # 61.6 / 63.2 / 64.8 / 66.4

def add_box(name, dims, loc, mat, bevel=None):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(mat)
    if bevel:
        bev = ob.modifiers.new("EdgeBevel", 'BEVEL')
        bev.width = bevel
        bev.segments = 2
        bev.limit_method = 'ANGLE'
    return ob

part_objs = []

# ---------- 每台柜：双开门 + 把手 + 风扇罩 + 百叶 ----------
DOOR_W, DOOR_H, DOOR_T = 0.6, 2.0, 0.03
DOOR_GAP = 0.02            # 门缝宽
DOOR_Z = BASE_Z + CAB_H / 2.0   # 1.30，上下各留 0.15 m
DOOR_Y = SOUTH_Y - 0.02 - DOOR_T / 2.0  # 29.465，门板北面距柜面 0.02 m
HANDLE_Z = 1.25
HANDLE_Y = SOUTH_Y - 0.02 - DOOR_T - 0.015  # 29.435，横杆贴门板南面（相切）
LOUVER_Y = NORTH_Y + 0.02 + 0.01  # 30.53，百叶北面距柜面 0.02 m

for i, cx in enumerate(CENTERS_X):
    tag = "PCS" if i == 3 else f"Battery{i + 1}"
    # --- 双开门：左扇中心 cx-0.31，右扇 cx+0.31（缝 0.02 居中） ---
    for side, dx in (("L", -0.31), ("R", 0.31)):
        door = add_box(f"{tag}_Door_{side}",
                       (DOOR_W, DOOR_T, DOOR_H),
                       (cx + dx, DOOR_Y, DOOR_Z), DOOR_MAT, bevel=0.005)
        part_objs.append(door)
        # --- 把手：沿 x 的小横杆，靠近门缝一侧 ---
        hx = cx + dx * 0.32  # 左扇把手在 cx-0.10，右扇在 cx+0.10
        bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.015, depth=0.20,
                                            location=(hx, HANDLE_Y, HANDLE_Z),
                                            rotation=(0.0, math.radians(90), 0.0))
        handle = bpy.context.active_object
        handle.name = f"{tag}_Handle_{side}"
        handle.data.materials.append(HANDLE_MAT)
        part_objs.append(handle)
    # --- 顶部风扇罩：圆盘 + 格栅环 + 十字条 + 中心毂，置于顶盖顶面 ---
    fan_z = CAP_TOP_Z + 0.015  # 圆盘中心 2.525
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.20, depth=0.03,
                                        location=(cx, CY, fan_z))
    disc = bpy.context.active_object
    disc.name = f"{tag}_FanDisc"
    disc.data.materials.append(FAN_MAT)
    part_objs.append(disc)
    # 同心格栅环（两道）
    for r in (0.13, 0.07):
        bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=0.008,
                                         major_segments=32, minor_segments=8,
                                         location=(cx, CY, fan_z + 0.015))
        ring = bpy.context.active_object
        ring.name = f"{tag}_FanRing_{int(r * 100)}"
        ring.data.materials.append(GRILLE_MAT)
        part_objs.append(ring)
    # 十字格栅条
    for j, rot in enumerate((0.0, math.radians(90))):
        bar = add_box(f"{tag}_FanBar_{j}", (0.38, 0.025, 0.012),
                      (cx, CY, fan_z + 0.018), GRILLE_MAT)
        bar.rotation_euler = (0.0, 0.0, rot)
        part_objs.append(bar)
    # 中心毂
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.05, depth=0.02,
                                        location=(cx, CY, fan_z + 0.02))
    hub = bpy.context.active_object
    hub.name = f"{tag}_FanHub"
    hub.data.materials.append(GRILLE_MAT)
    part_objs.append(hub)
    # --- 北面散热百叶：3 条横向细条 ---
    for k, lz in enumerate((1.70, 1.95, 2.20)):
        louver = add_box(f"{tag}_Louver_{k + 1}", (1.0, 0.02, 0.10),
                         (cx, LOUVER_Y, lz), LOUVER_MAT)
        part_objs.append(louver)

print("part objects:", len(part_objs))
assert len(part_objs) == 4 * (2 + 2 + 6 + 3), "part count mismatch"

# ---------- preview-only 示意柜体（不导出） ----------
preview_objs = []
for i, cx in enumerate(CENTERS_X):
    name = "PCS_Cabinet" if i == 3 else f"Battery_Cabinet_{i + 1}"
    body = add_box("Preview_" + name, (CAB_W, CAB_D, CAB_H),
                   (cx, CY, BASE_Z + CAB_H / 2.0), CABINET_MAT)
    cap = add_box("Preview_" + name + "_TopCap", (CAB_W + 0.10, CAB_D + 0.10, 0.06),
                  (cx, CY, BASE_Z + CAB_H + 0.03), CAP_MAT)
    preview_objs.extend([body, cap])

# ---------- preview-only ground（不导出） ----------
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

# ---------- camera：南侧 45° 俯视，看清双开门与顶部风扇罩 ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35.0
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera = cam
cam.location = (64.0 + 4.5, 30.0 - 7.0, 5.0)
target = Vector((64.0, 30.0, 1.3))
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

# ---------- export .glb（只选本件对象，示意柜体/地面不导出） ----------
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
assert len(imported) >= len(part_objs), "glb reimport failed: too few objects"
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
print("DONE st-doors")
