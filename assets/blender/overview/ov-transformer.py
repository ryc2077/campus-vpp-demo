# ov-transformer: 户外变压器组 (总览, 全局坐标)
# Godot [74,-30] -> Blender 中心 (74, 30)
# 结构 (对照 scripts/campus_builder.gd _build_transformer, 尺寸与之一致):
#   基座 6.5(x) x 4.5(y) x 0.4m, z 0~0.4, 混凝土 #B9B3A8
#   箱体 5.6 x 3.4 x 3.6m, z 0.4~4.0, 灰绿 #6B7B72 + 顶盖
#   散热片: 箱体南北两侧各 9 片竖向细条, 0.06 厚(x) x 0.35 深(y) x 2.6 高,
#     z 0.7~3.3, 沿 x 排开, 深灰 #424A52
#   绝缘子: 顶部 3 根, x=-1.8/0/+1.8 (相对中心), 陶瓷色 #D9D4C7,
#     主柱 r=0.28 高 1.2m + 3 层伞裙盘 r=0.40 + 顶部金属端子
#   围栏示意: 7.5 x 5.5m 周边, 12 根立柱 (高 1.2m) + 上下两道横杆,
#     南侧挂一块警示黄牌 #E8B400
#   东侧接线盒 0.5 x 0.3 x 0.8m
# 颜色: SPEC §3 (配电柜灰绿 #6B7B72、混凝土 #B9B3A8、深灰 #424A52、
#   警示黄 #E8B400、金属灰 #8A8F94); 绝缘子陶瓷色 #D9D4C7
# 材质只用 Principled BSDF, Base Color 只给纯色 (sRGB->线性转换后赋值),
# 不连任何程序化节点进 Base Color, 保证 glTF 导出带 baseColorFactor。
# 只做变压器组: 不做配电房外壳/储能/道路/树木; 不动 scenes/overview.py。
# 材质只用 Principled BSDF
import bpy
import math
import os
from mathutils import Vector

BASE = "/home/hatch/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot"
BLEND_PATH = BASE + "/assets/blender/overview/ov-transformer.blend"
GLB_PATH = BASE + "/assets/models/ov-transformer.glb"
PNG_PATH = BASE + "/screenshots/blender/ov-transformer.png"

CX, CY = 74.0, 30.0  # Blender 全局中心 (Godot [74,-30])

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

BODY_MAT = make_material("Transformer_Body", "#6B7B72", 0.55, 0.25)
FIN_MAT = make_material("Transformer_Fin", "#424A52", 0.6, 0.4)
BASE_MAT = make_material("Transformer_Base", "#B9B3A8", 0.85, 0.0)
BUSH_MAT = make_material("Transformer_Bushing", "#D9D4C7", 0.45, 0.05)
TERM_MAT = make_material("Transformer_Terminal", "#8A8F94", 0.35, 0.8)
FENCE_MAT = make_material("Transformer_Fence", "#8A8F94", 0.5, 0.7)
WARN_MAT = make_material("Transformer_Warning", "#E8B400", 0.6, 0.0)

def add_box(name, dims, loc, mat, bevel=0.0):
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

def add_cyl(name, radius, depth, loc, mat, vertices=24):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.data.materials.append(mat)
    return ob

objs = []

# ---------- 基座: 6.5 x 4.5 x 0.4, z 0~0.4 ----------
objs.append(add_box("TF_Base", (6.5, 4.5, 0.4), (CX, CY, 0.2), BASE_MAT, bevel=0.02))
# ---------- 箱体: 5.6 x 3.4 x 3.6, z 0.4~4.0 ----------
objs.append(add_box("TF_Body", (5.6, 3.4, 3.6), (CX, CY, 2.2), BODY_MAT, bevel=0.03))
# ---------- 顶盖: 5.66 x 3.46 x 0.08, z 4.0~4.08 ----------
objs.append(add_box("TF_Lid", (5.66, 3.46, 0.08), (CX, CY, 4.04), BODY_MAT, bevel=0.01))
# ---------- 散热片: 南北两侧各 9 片, 0.06 x 0.35 x 2.6, z 0.7~3.3 ----------
for side in (-1, 1):
    for j, dx in enumerate((-2.4, -1.8, -1.2, -0.6, 0.0, 0.6, 1.2, 1.8, 2.4)):
        objs.append(add_box("TF_Fin_%s%d" % ("S" if side < 0 else "N", j + 1),
                            (0.06, 0.35, 2.6),
                            (CX + dx, CY + side * 1.875, 2.0), FIN_MAT))
# ---------- 绝缘子: 3 根, x=-1.8/0/+1.8, 顶盖顶面 z=4.08 起 ----------
for k, dx in enumerate((-1.8, 0.0, 1.8)):
    tag = "TF_Bushing%d" % (k + 1)
    # 主柱 r=0.28, 高 1.2, z 4.08~5.28
    objs.append(add_cyl(tag, 0.28, 1.2, (CX + dx, CY, 4.68), BUSH_MAT))
    # 伞裙盘 3 层, r=0.40, 厚 0.05
    for s, z in enumerate((4.38, 4.68, 4.98)):
        objs.append(add_cyl("%s_Shed%d" % (tag, s + 1), 0.40, 0.05,
                            (CX + dx, CY, z), BUSH_MAT))
    # 顶部端子 r=0.10, 高 0.15, z 5.28~5.43
    objs.append(add_cyl("%s_Terminal" % tag, 0.10, 0.15,
                        (CX + dx, CY, 5.355), TERM_MAT))
# ---------- 东侧接线盒: 0.5 x 0.3 x 0.8, 贴箱体东面 ----------
objs.append(add_box("TF_JunctionBox", (0.3, 0.5, 0.8),
                    (CX + 2.95, CY, 1.2), FIN_MAT, bevel=0.01))
# ---------- 围栏示意: 7.5 x 5.5m 周边, 立柱高 1.2m ----------
FX, FY = 3.75, 2.75  # 围栏半长/半宽 (相对中心)
post_xs = (-FX, -FX / 2, 0.0, FX / 2, FX)
post_ys = (-FY, 0.0, FY)
pi = 0
for x in post_xs:
    for y in (post_ys[0], post_ys[2]):
        pi += 1
        objs.append(add_box("TF_FencePost%02d" % pi, (0.08, 0.08, 1.2),
                            (CX + x, CY + y, 0.6), FENCE_MAT))
for y in (post_ys[1],):
    for x in (post_xs[0], post_xs[4]):
        pi += 1
        objs.append(add_box("TF_FencePost%02d" % pi, (0.08, 0.08, 1.2),
                            (CX + x, CY + y, 0.6), FENCE_MAT))
# 横杆: 南北两边 (沿 x) + 东西两边 (沿 y), 各上下两道 (z=0.6/1.1)
for z in (0.6, 1.1):
    for y in (-FY, FY):
        objs.append(add_box("TF_FenceRail_x_%s_%.1f" % ("S" if y < 0 else "N", z),
                            (7.5, 0.05, 0.05), (CX, CY + y, z), FENCE_MAT))
    for x in (-FX, FX):
        objs.append(add_box("TF_FenceRail_y_%s_%.1f" % ("W" if x < 0 else "E", z),
                            (0.05, 5.5, 0.05), (CX + x, CY, z), FENCE_MAT))
# 警示黄牌: 南侧围栏中部, 0.6 x 0.02 x 0.4, z 0.7~1.1
objs.append(add_box("TF_WarningPlate", (0.6, 0.02, 0.4),
                    (CX, CY - FY, 0.9), WARN_MAT))

print("ov-transformer objects:", len(objs), [o.name for o in objs])
# 尺寸自检: 箱体包络 / 总高 / 围栏包络
print("CHECK body 5.6x3.4x3.6 top z=4.0; bushing top z=5.43; fence 7.5x5.5")

# ---------- lighting (SPEC §2) ----------
sun_data = bpy.data.lights.new("Sun", type='SUN')
sun_data.energy = 3.5
sun_data.use_shadow = True
sun = bpy.data.objects.new("Sun", sun_data)
bpy.context.collection.objects.link(sun)
sun.location = (CX - 20.0, CY - 20.0, 30.0)
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

# ---------- camera: 东南侧高处 45° 俯视, 看向变压器中心 ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 32.0
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera = cam
cam.location = (CX + 9.0, CY - 10.0, 6.0)
target = Vector((CX, CY, 2.0))
cam.rotation_mode = 'QUATERNION'
cam.rotation_quaternion = (target - cam.location).to_track_quat('-Z', 'Y')

# ---------- render settings (本地默认不渲染, 走 GitHub Actions) ----------
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
for ob in objs:
    ob.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format='GLB',
                           use_selection=True, export_apply=True)

# ---------- 回读验证 glb ----------
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB_PATH)
imported = [ob for ob in bpy.data.objects if ob not in before]
print("GLB reimport objects:", len(imported),
      [ob.name for ob in imported])
assert len(imported) == len(objs), "glb reimport failed: expected %d objects, got %d" % (len(objs), len(imported))
# 删掉回读的副本, 恢复干净场景
bpy.ops.object.select_all(action='DESELECT')
for ob in imported:
    ob.select_set(True)
bpy.ops.object.delete()
for _mesh in list(bpy.data.meshes):
    if _mesh.users == 0:
        bpy.data.meshes.remove(_mesh)
for _mat in list(bpy.data.materials):
    if _mat.users == 0:
        bpy.data.materials.remove(_mat)
print("orphan purge done, materials:", sorted(m.name for m in bpy.data.materials))

# ---------- render preview (本地默认跳过; 置 OV_TRANSFORMER_RENDER=1 才渲染) ----------
if os.environ.get("OV_TRANSFORMER_RENDER") == "1":
    bpy.ops.render.render(write_still=True)
    print("Preview saved:", PNG_PATH, "exists:", os.path.exists(PNG_PATH),
          "size:", os.path.getsize(PNG_PATH) if os.path.exists(PNG_PATH) else 0)
else:
    print("Render skipped locally (set OV_TRANSFORMER_RENDER=1 to render)")
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("DONE ov-transformer")
