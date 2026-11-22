# pv-inverter: 逆变器与线缆 (A栋屋顶 2 台 + 实验楼屋顶 1 台)
# 只做逆变器和线缆: 不做板(pv-panels)/支架(pv-mount)/屋顶面层(pv-roof)
# 规约: SPEC.md; 单位米; Blender x东 y北 z上
# 位置说明(对照 pv-panels.py 的布阵自查后定):
#   A栋屋顶: x -76..-36, y 22.5..37.5, z=19; 板阵列 x -74.14..-37.87,
#   北侧末行中心 y=36.3, 板北缘约 y=37.15。任务给的 (-56,38) 在屋顶北缘
#   (37.5) 之外 0.5m, 且会压到板阵列, 故两台改放北侧两角:
#   (-75.0,36.6) 与 (-37.0,36.6), 全在屋顶上、与板阵列 x 向留空 0.36m 以上。
#   实验楼屋顶: x -49..-7, y 56..68, z=13; 板北缘约 y=66.90, 任务给的
#   (-28,66) 落在北侧末行板上, 故北移至 (-28,67.3), 板北缘以北、屋顶内。
# 线槽: 每台逆变器北侧出线, 沿屋顶走到女儿墙内侧, 再沿女儿墙内侧
#   向上 1m 到女儿墙顶(女儿墙顶约屋顶+1m)即止, 不做楼体外立面线缆。
import bpy
import math
import os
from mathutils import Vector

BASE = os.path.expanduser("~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
BLEND = os.path.join(BASE, "assets/blender/pv/pv-inverter.blend")
GLB = os.path.join(BASE, "assets/models/pv-inverter.glb")
PNG = os.path.join(BASE, "screenshots/blender/pv-inverter.png")

# ---- 清场 ----
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for m in list(bpy.data.meshes):
    bpy.data.meshes.remove(m)

# ---- 材质 (只用 Principled BSDF; sRGB 十六进制先转线性再赋值) ----
def srgb(hexstr):
    h = hexstr.lstrip('#')
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i+2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return tuple(out)

def principled(name, rgb, metallic, roughness, emission=None, emission_strength=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission is not None:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat

MAT_BODY = principled("INV_Body", srgb("C0C5C9"), 0.6, 0.35)   # 浅灰金属箱体
MAT_FIN = principled("INV_Fin", srgb("8A8F94"), 0.7, 0.40)      # 散热鳍片金属灰
MAT_BASE = principled("INV_Base", srgb("424A52"), 0.2, 0.80)    # 底座深灰
MAT_TRUNK = principled("INV_Trunk", srgb("C0C5C9"), 0.5, 0.45)  # 浅灰线槽
MAT_SCREEN = principled("INV_Screen", srgb("1F2A33"), 0.1, 0.20)  # 显示小屏深色
MAT_LED = principled("INV_Led", srgb("46A04E"), 0.0, 0.40,
                     emission=srgb("46A04E"), emission_strength=1.5)  # 运行绿灯
# 预览示意用(不导出): 屋顶深灰 / 板深蓝
MAT_ROOF = principled("PREV_Roof", srgb("424A52"), 0.0, 0.90)
MAT_PANEL = principled("PREV_Panel", srgb("1A2F4A"), 0.3, 0.35)

part_objs = []  # 本件对象(导出用)

def add_box(name, loc, dims, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.active_object
    o.name = name
    o.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if mat is not None:
        o.data.materials.append(mat)
    if bevel > 0:
        mod = o.modifiers.new("Bevel", 'BEVEL')
        mod.width = bevel
        mod.segments = 2
    part_objs.append(o)
    return o

# ---- 逆变器: 单台 1.0(x) x 0.6(y) x 1.4(z) 米 ----
def make_inverter(tag, cx, cy, roof_z):
    # 底座 1.10 x 0.70 x 0.12
    add_box(f"INV_{tag}_Base", (cx, cy, roof_z + 0.06),
            (1.10, 0.70, 0.12), MAT_BASE)
    # 箱体 1.00 x 0.60 x 1.40, 小倒角
    body_z = roof_z + 0.12 + 0.70
    add_box(f"INV_{tag}_Body", (cx, cy, body_z),
            (1.00, 0.60, 1.40), MAT_BODY, bevel=0.02)
    # 顶盖 1.04 x 0.64 x 0.06
    add_box(f"INV_{tag}_Cap", (cx, cy, roof_z + 0.12 + 1.40 + 0.03),
            (1.04, 0.64, 0.06), MAT_FIN)
    # 散热鳍片: 东西两侧面各 6 条细条 0.03 x 0.50 x 1.05
    for side in (-1, 1):
        for i, fy in enumerate((-0.20, -0.12, -0.04, 0.04, 0.12, 0.20)):
            add_box(f"INV_{tag}_Fin_{'W' if side < 0 else 'E'}{i}",
                    (cx + side * 0.515, cy + fy, body_z),
                    (0.03, 0.05, 1.05), MAT_FIN)
    # 显示小屏: 南面(-y) 0.34 x 0.02 x 0.24, 偏上
    add_box(f"INV_{tag}_Screen", (cx, cy - 0.31, body_z + 0.18),
            (0.34, 0.02, 0.24), MAT_SCREEN)
    # 运行指示绿灯 + 小按钮: 南面屏下方
    add_box(f"INV_{tag}_Led", (cx - 0.12, cy - 0.31, body_z - 0.05),
            (0.05, 0.02, 0.05), MAT_LED)
    add_box(f"INV_{tag}_Button", (cx + 0.10, cy - 0.31, body_z - 0.05),
            (0.06, 0.02, 0.06), MAT_FIN)
    # 电缆接头: 北面(+y)底部小盒, 线槽由此出线
    add_box(f"INV_{tag}_Gland", (cx, cy + 0.32, roof_z + 0.22),
            (0.16, 0.06, 0.14), MAT_BASE)
    return (cx, cy, roof_z)

# ---- 线槽: 北向短段 + 沿北缘横向段 + 弯头 + 竖直段(女儿墙内侧上行 1m 到墙顶) ----
# 横向段沿北缘走(板北缘 y=37.15/66.90 之外、女儿墙之内), 从西南预览机位可见
def make_trunk(tag, cx, cy, roof_z, parapet_y, dir_x):
    run_y = parapet_y - 0.05  # A栋 37.35, 实验楼 67.85: 板北缘之外、女儿墙内侧
    # 北向短段: 逆变器北面 -> 横向段
    y0 = cy + 0.30
    add_box(f"INV_{tag}_TrunkH", (cx, (y0 + run_y) / 2, roof_z + 0.04),
            (0.15, run_y - y0, 0.08), MAT_TRUNK)
    # 横向段: 沿北缘走 2.0m
    end_x = cx + dir_x * 2.0
    add_box(f"INV_{tag}_TrunkRun", (cx + dir_x * 1.0, run_y, roof_z + 0.04),
            (2.0, 0.15, 0.08), MAT_TRUNK)
    # 弯头 x2: 北向转横向、横向转竖直
    add_box(f"INV_{tag}_Elbow1", (cx, run_y, roof_z + 0.04),
            (0.15, 0.15, 0.08), MAT_TRUNK)
    add_box(f"INV_{tag}_Elbow2", (end_x, run_y, roof_z + 0.04),
            (0.15, 0.15, 0.08), MAT_TRUNK)
    # 竖直线槽: 沿女儿墙内侧上行 1m, 0.15(x) x 0.06(y) x 1.0(z), 到墙顶即止
    add_box(f"INV_{tag}_TrunkV", (end_x, run_y + 0.075, roof_z + 0.50),
            (0.15, 0.06, 1.00), MAT_TRUNK)
    # 墙顶压盖小盒
    add_box(f"INV_{tag}_TrunkTop", (end_x, run_y + 0.075, roof_z + 1.02),
            (0.18, 0.10, 0.05), MAT_TRUNK)

# A栋屋顶北侧两角 (屋顶 z=19, 北缘 y=37.5, 女儿墙内侧 y=37.4)
make_inverter("A1", -75.0, 36.6, 19.0)
make_trunk("A1", -75.0, 36.6, 19.0, 37.4, +1)  # 横向段向东
make_inverter("A2", -37.0, 36.6, 19.0)
make_trunk("A2", -37.0, 36.6, 19.0, 37.4, -1)  # 横向段向西(朝屋顶中部)
# 实验楼屋顶北侧 (屋顶 z=13, 北缘 y=68, 女儿墙内侧 y=67.9)
make_inverter("LAB", -28.0, 67.3, 13.0)
make_trunk("LAB", -28.0, 67.3, 13.0, 67.9, +1)  # 横向段向东
print(f"INVERTERS: 3 units, {len(part_objs)} part objects")

# ---- 光照 (SPEC §2): 太阳 3.5 从西南来, 仰角约 50 度; 世界淡蓝 ----
world = bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.65, 0.78, 0.88, 1.0)
bg.inputs["Strength"].default_value = 1.0

sun_data = bpy.data.lights.new("Sun", type='SUN')
sun_data.energy = 3.5
sun_data.use_shadow = True
sun = bpy.data.objects.new("Sun", sun_data)
bpy.context.collection.objects.link(sun)
sun.rotation_mode = 'QUATERNION'
d = Vector((1.0, 1.0, -math.tan(math.radians(50)))).normalized()
sun.rotation_quaternion = Vector((0, 0, -1)).rotation_difference(d)

# ---- 预览示意(不导出): A栋屋顶 slab + 几块示意板, 只为看清逆变器与线槽 ----
preview_objs = []
def prev_box(name, loc, dims, mat, rot_x=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.active_object
    o.name = name
    o.dimensions = dims
    o.rotation_euler = (rot_x, 0.0, 0.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    preview_objs.append(o)
    return o

# A栋屋顶 slab 40 x 15, 顶面 z=19
prev_box("PREV_RoofA", (-56, 30, 18.8), (40, 15, 0.4), MAT_ROOF)
# 示意女儿墙: 北缘 y=37.5, 高 1m(顶 z=20), 只为看清线槽竖直段到墙顶
prev_box("PREV_ParapetA", (-56, 37.50, 19.5), (40, 0.15, 1.0), MAT_ROOF)
# 示意板: 2 行 x 8 列, 倾角 15 度朝南, 位于逆变器以南, 显出板与逆变器的空隙
for r, ry in enumerate((30.0, 33.6)):
    for c in range(8):
        prev_box(f"PREV_Panel_{r}_{c}",
                 (-70 + c * 4.6, ry, 19 + 0.15 + (1.762 / 2) * math.sin(math.radians(15)) + 0.02),
                 (1.134, 1.762, 0.035), MAT_PANEL, rot_x=math.radians(15))

# ---- 预览相机: 西南近景看 A 栋西侧逆变器(A1)与线槽, 东侧 A2 在背景中 ----
cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 40
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera = cam
target = Vector((-72, 36.8, 19.6))
cam.location = (-80, 26, 25)
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()

# ---- 渲染 (Eevee, 640x360, 16 采样) ----
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100
scene.eevee.taa_render_samples = 16
scene.render.filepath = PNG
bpy.ops.render.render(write_still=True)

# 预览亮度自查 (不能全黑/全白)
chk = bpy.data.images.load(PNG)
px = list(chk.pixels)
npx = len(px) // 4
mean = sum(px[::4]) / npx if npx else 0.0
print(f"PREVIEW mean brightness: {mean:.3f} (pixels {npx})")
assert 0.02 < mean < 0.98, "preview looks black/white!"

# ---- 清掉预览用对象(示意板/屋顶/相机/太阳), 只留本件, 存 blend ----
for o in preview_objs:
    bpy.data.objects.remove(o, do_unlink=True)
bpy.data.objects.remove(cam, do_unlink=True)
bpy.data.objects.remove(sun, do_unlink=True)
for o in part_objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = part_objs[0]
bpy.ops.wm.save_as_mainfile(filepath=BLEND)

# ---- 导出 GLB (只选本件对象) ----
bpy.ops.export_scene.gltf(
    filepath=GLB, export_format='GLB',
    use_selection=True, export_apply=True)

# ---- 回读 GLB 验证 ----
before = set(bpy.data.objects.keys())
bpy.ops.import_scene.gltf(filepath=GLB)
after = set(bpy.data.objects.keys())
imported = after - before
print(f"GLB reimport OK: {len(imported)} objects")
assert len(imported) > 0, "GLB reimport failed!"

print("DONE pv-inverter")
