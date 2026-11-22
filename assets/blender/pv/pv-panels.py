# pv-panels: 光伏板阵列 (A栋/B栋/实验楼屋顶)
# 只做板本身: 不做支架/逆变器/屋顶面层
# 规约: SPEC.md; 单位米; Blender x东 y北 z上
import bpy
import bmesh
import math
import os
from mathutils import Vector

BASE = os.path.expanduser("~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
BLEND = os.path.join(BASE, "assets/blender/pv/pv-panels.blend")
GLB = os.path.join(BASE, "assets/models/pv-panels.glb")
PNG = os.path.join(BASE, "screenshots/blender/pv-panels.png")

# ---- 清场 ----
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for m in list(bpy.data.meshes):
    bpy.data.meshes.remove(m)

# ---- 材质 (只用 Principled BSDF) ----
def principled(name, rgb, metallic, roughness):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat

def srgb(hexstr):
    """十六进制 sRGB -> 线性值 (Principled Base Color 要线性值, 直接赋 sRGB 会洗白)"""
    h = hexstr.lstrip('#')
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i+2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return tuple(out)

MAT_PANEL = principled("PV_PanelBlue", srgb("1A2F4A"), 0.3, 0.35)   # 板面深蓝
MAT_FRAME = principled("PV_FrameSilver", srgb("C0C5C9"), 0.8, 0.30) # 银色边框
MAT_BUS = principled("PV_Busbar", srgb("7E93A8"), 0.6, 0.40)        # 横向汇流条(浅蓝灰)

# ---- 主板 mesh: 1.134 x 1.762 x 0.035, 银框薄框条 + 4 条横向汇流条 ----
PW, PL, PT = 1.134, 1.762, 0.035

def add_box(bm, cx, cy, cz, sx, sy, sz, mat_idx):
    r = bmesh.ops.create_cube(bm, size=1.0)
    for v in r['verts']:
        v.co = (v.co.x * sx + cx, v.co.y * sy + cy, v.co.z * sz + cz)
    faces = set()
    for v in r['verts']:
        faces.update(v.link_faces)
    for f in faces:
        f.material_index = mat_idx

mesh = bpy.data.meshes.new("PV_PanelMesh")
bm = bmesh.new()
add_box(bm, 0, 0, 0, PW, PL, PT, 0)                                  # 板体
fx = PW / 2 - 0.025
add_box(bm, -fx, 0, 0.0025, 0.05, PL, 0.05, 1)                       # 长边框 x2
add_box(bm, fx, 0, 0.0025, 0.05, PL, 0.05, 1)
fy = PL / 2 - 0.025
add_box(bm, 0, -fy, 0.0025, PW - 0.10, 0.05, 0.05, 1)                # 短边框 x2
add_box(bm, 0, fy, 0.0025, PW - 0.10, 0.05, 0.05, 1)
for by in (-0.66, -0.22, 0.22, 0.66):                                # 横向汇流条 x4
    add_box(bm, 0, by, 0.0205, PW - 0.10, 0.03, 0.006, 2)
bm.to_mesh(mesh)
bm.free()
mesh.materials.append(MAT_PANEL)
mesh.materials.append(MAT_FRAME)
mesh.materials.append(MAT_BUS)

# ---- 布阵 ----
# 倾角 15 度朝南(朝 -y): 绕 X 轴 +15 度, 北边(+y)翘起
TILT = math.radians(15.0)
# 板底留 0.15m 空隙: 板中心高度 = 屋顶 z + 0.15 + (PL/2)*sin15 + PT/2
CENTER_H = 0.15 + (PL / 2) * math.sin(TILT) + PT / 2
PITCH_X = 1.17   # 列距 (板宽 1.134 + 0.036 缝)
PITCH_Y = 1.80   # 行距 (投影长 1.70 + 0.10 缝)
AISLE = 0.90     # 每 3 行后一条检修道

panels = []

def layout_roof(name, cx, cy, roof_z, ncols, nrows):
    # 行: 3 行一组, 组间加检修道
    row_y = []
    y = cy - ( (nrows - 1) * PITCH_Y + ((nrows - 1) // 3) * AISLE ) / 2
    for r in range(nrows):
        row_y.append(y)
        y += PITCH_Y
        if (r + 1) % 3 == 0 and r != nrows - 1:
            y += AISLE
    n = 0
    for r, ry in enumerate(row_y):
        for c in range(ncols):
            x = cx + (c - (ncols - 1) / 2) * PITCH_X
            obj = bpy.data.objects.new(f"PV_{name}_{r:02d}_{c:02d}", mesh)
            bpy.context.collection.objects.link(obj)
            obj.location = (x, ry, roof_z + CENTER_H)
            obj.rotation_euler = (TILT, 0.0, 0.0)
            panels.append(obj)
            n += 1
    print(f"ROOF {name}: {n} panels ({ncols} cols x {nrows} rows)")
    return n

# 屋顶数据 (Blender 中心, 屋顶 z, 屋面尺寸)
# A栋 (-56,30) z=19 40x15 ; B栋 (-12,30) z=19 32x14 ; 实验楼 (-28,62) z=13 42x12
nA = layout_roof("A", -56, 30, 19, 32, 7)
nB = layout_roof("B", -12, 30, 19, 26, 6)
nL = layout_roof("LAB", -28, 62, 13, 34, 5)
print(f"TOTAL panels: {nA + nB + nL} (A={nA} B={nB} LAB={nL})")

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
# 光线从西南高处射向东北低处: 方向 (1, 1, -tan50)
d = Vector((1.0, 1.0, -math.tan(math.radians(50)))).normalized()
sun.rotation_quaternion = Vector((0, 0, -1)).rotation_difference(d)

# ---- 预览相机: 西南高处俯视三栋屋顶 ----
cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 40
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera = cam
target = Vector((-30, 42, 16))
cam.location = (-100, -28, 62)
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

# 预览亮度自查 (不能全黑/全白): 读回落盘的 PNG 检查
chk = bpy.data.images.load(PNG)
px = list(chk.pixels)
npx = len(px) // 4
mean = sum(px[::4]) / npx if npx else 0.0
print(f"PREVIEW mean brightness: {mean:.3f} (pixels {npx})")
assert 0.02 < mean < 0.98, "preview looks black/white!"

# ---- 清掉预览用对象, 只留板件, 存 blend ----
bpy.data.objects.remove(cam, do_unlink=True)
bpy.data.objects.remove(sun, do_unlink=True)
for o in panels:
    o.select_set(True)
bpy.context.view_layer.objects.active = panels[0]
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

print("DONE pv-panels")
