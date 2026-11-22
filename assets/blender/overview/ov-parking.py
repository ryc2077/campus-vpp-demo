# ov-parking: 停车区（总览件）
# Blender 坐标 x 向东、y 向北、z 向上，单位米
# 内容：停车场 20x12m（中心 (-30,-90)，沥青灰）+ 北侧一排 10 个车位白线
#      + 3 辆简易小车（灰 / 蓝 / 红）
# 不做主干道（ov-road-main）、不做充电区。
#
# 尺寸说明：任务给 10 个车位 × 2.5m 宽 = 25m，装不进 20m 宽的停车场；
# 停车场 20x12m 与车位 10 个是硬指标，故车位宽取 20/10 = 2.0m、深 5m，
# 车辆 1.8m 宽仍可停入。车位线贴在沥青面上（z 0.08 -> 0.10），防共面闪烁。
import bpy
import math
import os
from mathutils import Vector

PIECE = "ov-parking"
BASE = os.path.expanduser("~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
PY_DIR = os.path.join(BASE, "assets/blender/overview")
BLEND_PATH = os.path.join(PY_DIR, "ov-parking.blend")
GLB_PATH = os.path.join(BASE, "assets/models/ov-parking.glb")
PNG_PATH = os.path.join(BASE, "screenshots/blender/ov-parking.png")

# 停车场：中心 (-30, -90)，20(x) x 12(y)m，厚 0.08m
LOT_CX, LOT_CY = -30.0, -90.0
LOT_SX, LOT_SY = 20.0, 12.0
LOT_Z0, LOT_Z1 = 0.0, 0.08
# 车位：北侧一排，10 个，2.0m 宽 x 5m 深（见文件头尺寸说明）
N_SPACES = 10
SPACE_W, SPACE_D = 2.0, 5.0
LINE_W = 0.12
LINE_Z0, LINE_Z1 = LOT_Z1, 0.10
# 车位北缘 = 停车场北缘 y=-84，车位向南 5m：y -89..-84
SPACE_Y_NORTH = LOT_CY + LOT_SY / 2.0          # -84
SPACE_Y_SOUTH = SPACE_Y_NORTH - SPACE_D        # -89
SPACE_Y_C = (SPACE_Y_NORTH + SPACE_Y_SOUTH) / 2.0  # -86.5


def hex_rgb(h):
    """Hex sRGB -> linear RGB."""
    h = h.lstrip("#")

    def srgb_to_lin(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (srgb_to_lin(int(h[i:i + 2], 16)) for i in (0, 2, 4))
    return (r, g, b, 1.0)


def make_mat(name, hexcol, rough=0.9, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = hex_rgb(hexcol)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    return m


MAT_ASPHALT = make_mat("Asphalt_424A52", "#424A52", 0.95)
MAT_LINE = make_mat("Line_White", "#FFFFFF", 0.8)
MAT_WHEEL = make_mat("Wheel_Dark", "#2A2E33", 0.9)
MAT_GROUND = make_mat("Ground_Grass_69B45E", "#69B45E", 1.0)
MAT_CAR_GREY = make_mat("Car_Grey_8A8F94", "#8A8F94", 0.5, 0.3)
MAT_CAR_BLUE = make_mat("Car_Blue_3B82C4", "#3B82C4", 0.5, 0.3)
MAT_CAR_RED = make_mat("Car_Red_C4534E", "#C4534E", 0.5, 0.3)

# ---- clean scene ----
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

objs = []  # objects that go into the .glb


def box(name, cx, cy, z0, z1, sx, sy, mat, bevel=0.02):
    bpy.ops.mesh.primitive_cube_add(location=(cx, cy, (z0 + z1) / 2.0))
    o = bpy.context.active_object
    o.name = name
    o.dimensions = (sx, sy, z1 - z0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel and min(sx, sy, z1 - z0) > 2 * bevel + 0.02:
        mod = o.modifiers.new("EdgeSoft", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        mod.limit_method = "ANGLE"
    o.data.materials.append(mat)
    objs.append(o)
    return o


def cylinder_wheel(name, cx, cy, cz, mat):
    """车轮：圆柱，轴沿 x（车宽方向），r=0.33m，宽 0.20m。"""
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.33, depth=0.20,
                                        location=(cx, cy, cz),
                                        rotation=(0.0, math.pi / 2.0, 0.0))
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(mat)
    objs.append(o)
    return o


# ---- 停车场沥青面 ----
box("parking_lot", LOT_CX, LOT_CY, LOT_Z0, LOT_Z1,
    LOT_SX, LOT_SY, MAT_ASPHALT, bevel=0.02)

# ---- 车位线：11 条分隔线（0.12m 宽 x 5m 深）+ 1 条北缘通长线 ----
lot_x0 = LOT_CX - LOT_SX / 2.0  # -40
for i in range(N_SPACES + 1):
    x = lot_x0 + i * SPACE_W
    box(f"space_line_{i:02d}", x, SPACE_Y_C, LINE_Z0, LINE_Z1,
        LINE_W, SPACE_D, MAT_LINE, bevel=0.0)
box("space_line_north", LOT_CX, SPACE_Y_NORTH - LINE_W / 2.0,
    LINE_Z0, LINE_Z1, LOT_SX, LINE_W, MAT_LINE, bevel=0.0)

# ---- 3 辆简易小车：车身 4.2x1.8x0.55 + 车顶 2.0x1.6x0.5 + 4 轮 r=0.33 ----
# 车长沿 y（鼻朝北，停进北侧车位），车宽沿 x；地面为沥青顶面 z=0.08
# 车身 z 0.33..0.88，车顶 z 0.88..1.38，轮心 z 0.41
CAR_BODY_Z0, CAR_BODY_Z1 = 0.33, 0.88
CAR_ROOF_Z0, CAR_ROOF_Z1 = 0.88, 1.38
WHEEL_Z = LOT_Z1 + 0.33  # 0.41


def car(name, cx, mat):
    cy = SPACE_Y_C
    box(f"{name}_body", cx, cy, CAR_BODY_Z0, CAR_BODY_Z1,
        1.8, 4.2, mat, bevel=0.03)
    box(f"{name}_roof", cx, cy - 0.2, CAR_ROOF_Z0, CAR_ROOF_Z1,
        1.6, 2.0, mat, bevel=0.03)
    for wx in (cx - 0.80, cx + 0.80):
        for wy in (cy - 1.35, cy + 1.35):
            cylinder_wheel(f"{name}_wheel", wx, wy, WHEEL_Z, MAT_WHEEL)


def space_center_x(i):
    """第 i 个车位（1 起）中心 x。"""
    return lot_x0 + (i - 0.5) * SPACE_W


car("car_grey", space_center_x(2), MAT_CAR_GREY)   # x=-37
car("car_blue", space_center_x(5), MAT_CAR_BLUE)   # x=-31
car("car_red", space_center_x(9), MAT_CAR_RED)     # x=-23

print("parking objects:", len(objs), "(lot 1, lines 12, cars 3x6)")

# ---- preview-only ground (NOT exported) ----
bpy.ops.mesh.primitive_plane_add(location=(LOT_CX, LOT_CY, -0.01))
ground = bpy.data.objects["Plane"]
ground.name = "Ground_PreviewOnly"
ground.dimensions = (60.0, 50.0, 0.0)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
ground.data.materials.append(MAT_GROUND)

# ---- lighting (SPEC section 2): sun 3.5 from SW, elev ~50 deg ----
target = Vector((LOT_CX, LOT_CY, 0.0))
sun_dir = Vector((-0.64, -0.64, 1.0))  # sun sits SW and up
bpy.ops.object.light_add(type="SUN", location=tuple(target + sun_dir * 80.0))
sun = bpy.context.active_object
sun.name = "Sun_SW"
sun.data.energy = 3.5
sun.data.use_shadow = True
sun.rotation_euler = (target - sun.location).to_track_quat("-Z", "Y").to_euler()

# ---- world: flat light blue (0.65, 0.78, 0.88), strength 1.0 ----
world = bpy.data.worlds.new("World_LightBlue")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.65, 0.78, 0.88, 1.0)
bg.inputs["Strength"].default_value = 1.0

# ---- camera: near top-down (~59 deg elevation) over the lot ----
# 能看清车位线与车辆；640x360 下 20m 宽停车场占画面主体。
bpy.ops.object.camera_add(location=(LOT_CX, LOT_CY - 18.0, 30.0))
cam = bpy.context.active_object
cam.name = "Cam_Preview"
cam.data.lens = 35.0
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
bpy.context.scene.camera = cam

# ---- save .blend ----
os.makedirs(PY_DIR, exist_ok=True)
os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
os.makedirs(os.path.dirname(PNG_PATH), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("saved blend:", BLEND_PATH)
if os.path.exists(BLEND_PATH + "1"):
    os.remove(BLEND_PATH + "1")
    print("removed blend1")

# ---- export .glb (this piece only) ----
bpy.ops.object.select_all(action="DESELECT")
for o in objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format="GLB",
                           use_selection=True, export_apply=True)
print("exported glb:", GLB_PATH, "objects:", len(objs))

# ---- read back the .glb to confirm it opens, then drop the duplicates ----
bpy.ops.object.select_all(action="DESELECT")
bpy.ops.import_scene.gltf(filepath=GLB_PATH)
imported = [o for o in bpy.context.selected_objects]
print("glb re-import OK, imported objects:", len(imported))
bpy.ops.object.delete(use_global=False)  # remove re-imported copies before render
print("re-imported copies deleted, scene objects:", len(bpy.context.scene.objects))

# ---- render preview: Eevee, 640x360, 16 samples ----
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100
scene.eevee.taa_render_samples = 16
scene.render.filepath = PNG_PATH
scene.render.image_settings.file_format = "PNG"
bpy.ops.render.render(write_still=True)
print("rendered preview:", PNG_PATH)

print("DONE ov-parking")
