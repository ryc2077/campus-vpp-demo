# pv-mount: 光伏支架边框 (A栋/B栋/实验楼屋顶)
# 只做支架: 每行两根横梁 + 每隔约2.3m一对倾斜支腿 + 每块板四角压块
# 不做板本身(pv-panels)/屋顶面层(pv-roof)/逆变器线缆(pv-inverter)
# 规约: SPEC.md; 单位米; Blender x东 y北 z上
# 排布与 pv-panels.py 完全一致: 行距 1.80m, 列距 1.17m, 倾角 15度朝南, 板底离屋顶 0.15m
import bpy
import bmesh
import math
import os
from mathutils import Vector, Matrix, Euler

BASE = os.path.expanduser("~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
BLEND = os.path.join(BASE, "assets/blender/pv/pv-mount.blend")
GLB = os.path.join(BASE, "assets/models/pv-mount.glb")
PNG = os.path.join(BASE, "screenshots/blender/pv-mount.png")

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

MAT_MOUNT = principled("PV_MountGray", srgb("8A8F94"), 0.6, 0.40)  # 支架银灰金属
MAT_PANEL = principled("PV_PanelBluePrev", srgb("1A2F4A"), 0.3, 0.35)  # 预览示意板(不导出)
MAT_ROOF = principled("PV_RoofGrayPrev", srgb("424A52"), 0.0, 0.90)    # 预览示意屋顶(不导出)

# ---- 与 pv-panels.py 相同的板参数与布阵 ----
PW, PL, PT = 1.134, 1.762, 0.035
TILT = math.radians(15.0)
CENTER_H = 0.15 + (PL / 2) * math.sin(TILT) + PT / 2   # 板中心离屋顶高度
PITCH_X = 1.17
PITCH_Y = 1.80
AISLE = 0.90

def row_ys(cy, nrows):
    ys = []
    y = cy - ((nrows - 1) * PITCH_Y + ((nrows - 1) // 3) * AISLE) / 2
    for r in range(nrows):
        ys.append(y)
        y += PITCH_Y
        if (r + 1) % 3 == 0 and r != nrows - 1:
            y += AISLE
    return ys

# ---- bmesh 盒子 helper: 给定 4x4 变换矩阵 + 尺寸, 往 bm 里加一个立方体 ----
def add_box(bm, mat4, sx, sy, sz):
    r = bmesh.ops.create_cube(bm, size=1.0)
    for v in r['verts']:
        v.co = mat4 @ Vector((v.co.x * sx, v.co.y * sy, v.co.z * sz))

def tilt_mat(loc):
    """绕 X 轴 +15 度的板面坐标系, 原点在 loc"""
    return Matrix.Translation(Vector(loc)) @ Euler((TILT, 0.0, 0.0)).to_matrix().to_4x4()

# ---- 每栋屋顶建一个支架 mesh ----
# 横梁: 沿行长(x)方向, 截面 0.06(板面方向) x 0.05(高), 顶面贴板底, 位于板面局部 y=±0.55
# 支腿: 每对横梁下一对, 沿行每约 2.34m(2 列)一站, 底座落在屋顶面, 向南偏 0.35m 形成斜撑
# 压块: 每块板四角, 0.09x0.09x0.024, 压在板顶边角上
RAIL_DY = 0.55
RAIL_H = 0.05
RAIL_W = 0.06
LEG_SECT = 0.05
LEG_BASE_OFF = 0.35   # 支腿底座相对横梁垂点向南偏移, 形成倾斜
LEG_STEP = 2.34       # 约 2.3m 一站

mount_objs = []

def build_roof(name, cx, cy, roof_z, ncols, nrows):
    mesh = bpy.data.meshes.new(f"PV_MountMesh_{name}")
    bm = bmesh.new()
    n_rail = n_leg = n_clamp = 0
    row_len = (ncols - 1) * PITCH_X + PW
    n_stations = int(row_len // LEG_STEP) + 1
    st_x0 = cx - row_len / 2 + 0.3
    st_x1 = cx + row_len / 2 - 0.3
    st_xs = [st_x0 + (st_x1 - st_x0) * i / (n_stations - 1) for i in range(n_stations)] \
        if n_stations > 1 else [cx]
    for ry in row_ys(cy, nrows):
        # -- 两根横梁 --
        for dy in (-RAIL_DY, RAIL_DY):
            # 横梁中心: 板面局部 (0, dy, -PT/2 - RAIL_H/2), 换算到世界
            loc = (cx,
                   ry + dy * math.cos(TILT),
                   roof_z + CENTER_H + dy * math.sin(TILT) - PT / 2 - RAIL_H / 2)
            add_box(bm, tilt_mat(loc), row_len + 0.06, RAIL_W, RAIL_H)
            n_rail += 1
            # -- 每站一对支腿 + 底座脚板 --
            rail_bot_z = roof_z + CENTER_H + dy * math.sin(TILT) - PT / 2 - RAIL_H
            rail_y = ry + dy * math.cos(TILT)
            for sx in st_xs:
                top = Vector((sx, rail_y, rail_bot_z))
                base = Vector((sx, rail_y - LEG_BASE_OFF, roof_z + 0.01))
                d = top - base
                leng = d.length
                mid = (top + base) / 2
                q = Vector((0, 0, 1)).rotation_difference(d.normalized())
                m = Matrix.Translation(mid) @ q.to_matrix().to_4x4()
                add_box(bm, m, LEG_SECT, LEG_SECT, leng)
                n_leg += 1
                # 脚板
                add_box(bm, Matrix.Translation(Vector((sx, rail_y - LEG_BASE_OFF, roof_z + 0.01))),
                        0.14, 0.14, 0.02)
        # -- 每块板四角压块 --
        for c in range(ncols):
            px = cx + (c - (ncols - 1) / 2) * PITCH_X
            panel_mat = tilt_mat((px, ry, roof_z + CENTER_H))
            for ox in (-(PW / 2 - 0.07), PW / 2 - 0.07):
                for oy in (-(PL / 2 - 0.07), PL / 2 - 0.07):
                    cm = panel_mat @ Matrix.Translation(Vector((ox, oy, PT / 2 + 0.012)))
                    add_box(bm, cm, 0.09, 0.09, 0.024)
                    n_clamp += 1
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(MAT_MOUNT)
    obj = bpy.data.objects.new(f"PV_Mount_{name}", mesh)
    bpy.context.collection.objects.link(obj)
    mount_objs.append(obj)
    print(f"ROOF {name}: rails={n_rail} legs={n_leg} clamps={n_clamp} "
          f"({ncols} cols x {nrows} rows, {n_stations} leg stations/row)")

build_roof("A", -56, 30, 19, 32, 7)
build_roof("B", -12, 30, 19, 26, 6)
build_roof("LAB", -28, 62, 13, 34, 5)

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

# ---- 预览: 示意屋顶 slab + 几块示意板(只为看清支架, 不导出) ----
preview_objs = []
slab = bpy.data.objects.new("Prev_RoofSlab_A", bpy.data.meshes.new("PrevSlab"))
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1.0)
bm.to_mesh(slab.data)
bm.free()
slab.data.materials.append(MAT_ROOF)
slab.scale = (40, 15, 0.3)
slab.location = (-56, 30, 19 - 0.15)
bpy.context.collection.objects.link(slab)
preview_objs.append(slab)

demo = bpy.data.objects.new("Prev_PanelDemo", bpy.data.meshes.new("PrevPanel"))
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1.0)
bm.to_mesh(demo.data)
bm.free()
demo.data.materials.append(MAT_PANEL)
demo.scale = (PW, PL, PT)
demo.rotation_euler = (TILT, 0.0, 0.0)
# A 栋中间两行、中间 4 列各放一块示意板
rys = row_ys(30, 7)
for r in (3, 4):
    for c in (14, 15, 16, 17):
        o = bpy.data.objects.new(f"Prev_Panel_{r}_{c}", demo.data)
        bpy.context.collection.objects.link(o)
        o.location = (-56 + (c - 15.5) * PITCH_X, rys[r], 19 + CENTER_H)
        o.rotation_euler = (TILT, 0.0, 0.0)
        preview_objs.append(o)
bpy.data.objects.remove(demo, do_unlink=True)

# ---- 预览相机: 西南高处近景看 A 栋屋顶支架细部 ----
cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 40
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera = cam
target = Vector((-56, 30, 19.4))
cam.location = (-63.5, 21.5, 26.5)
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

# ---- 清掉预览用对象, 只留支架, 存 blend ----
bpy.data.objects.remove(cam, do_unlink=True)
bpy.data.objects.remove(sun, do_unlink=True)
for o in preview_objs:
    bpy.data.objects.remove(o, do_unlink=True)
for o in mount_objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = mount_objs[0]
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

print("DONE pv-mount")
