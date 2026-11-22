# ov-lab: 实验楼楼体 42x12x13m, 3F, Blender 中心 (-28, 62, 0)
# 蓝灰墙 #DFE9F2 + 深灰平屋顶 #424A52 + 女儿墙 + 每层横向窗带
import bpy, math, os, mathutils

CX, CY = -28.0, 62.0
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
BLEND = os.path.join(OUT_DIR, "ov-lab.blend")
GLB = os.path.abspath(os.path.join(OUT_DIR, "..", "..", "models", "ov-lab.glb"))
PNG = os.path.abspath(os.path.join(OUT_DIR, "..", "..", "..", "screenshots", "blender", "ov-lab.png"))

# ---------- clean scene ----------
bpy.ops.wm.read_factory_settings(use_empty=True)

# ---------- sRGB -> linear ----------
def srgb_to_linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def hex_lin(h):
    h = h.lstrip("#")
    return tuple(srgb_to_linear(int(h[i:i+2], 16)) for i in (0, 2, 4))

def make_mat(name, hexcolor, rough=0.85, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*hex_lin(hexcolor), 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    return m

MAT_WALL   = make_mat("lab_wall_bluegray", "#DFE9F2", 0.9)
MAT_ROOF   = make_mat("lab_roof_dark",     "#424A52", 0.9)
MAT_GLASS  = make_mat("lab_glass",         "#9FC3D8", 0.25, 0.1)
MAT_CONC   = make_mat("lab_concrete",      "#B9B3A8", 0.95)
MAT_METAL  = make_mat("lab_metal_gray",    "#8A8F94", 0.6, 0.4)
MAT_COPING = make_mat("lab_coping",        "#C0C5C9", 0.5, 0.3)
MAT_PAVE   = make_mat("lab_ground",        "#D8D2C4", 1.0)

OBJS = []

def box(name, cx, cy, z0, z1, sx, sy, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=(cx, cy, (z0 + z1) / 2.0))
    o = bpy.context.active_object
    o.name = name
    o.dimensions = (sx, sy, z1 - z0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0:
        mod = o.modifiers.new("bev", 'BEVEL')
        mod.width = bevel
        mod.segments = 2
    o.data.materials.append(mat)
    OBJS.append(o)
    return o

def cyl(name, cx, cy, z0, z1, r, mat):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=z1 - z0,
                                        location=(cx, cy, (z0 + z1) / 2.0))
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(mat)
    OBJS.append(o)
    return o

# ---------- 楼体分层（收分/檐口） ----------
# 基座 0-0.5（略外扩）
box("lab_plinth", CX, CY, 0.0, 0.5, 42.4, 12.4, MAT_CONC, bevel=0.05)
# 一层 0.5-4.0（42x12）
box("lab_floor1", CX, CY, 0.5, 4.0, 42.0, 12.0, MAT_WALL, bevel=0.05)
# 二层 4.0-8.0，收分 0.1/边 -> 41.8x11.8
box("lab_floor2", CX, CY, 4.0, 8.0, 41.8, 11.8, MAT_WALL, bevel=0.04)
# 三层 8.0-12.0，再收分 0.1/边 -> 41.6x11.6
box("lab_floor3", CX, CY, 8.0, 12.0, 41.6, 11.6, MAT_WALL, bevel=0.04)
# 檐口线脚：每层分界处薄板（略出挑）
for z in (0.5, 4.0, 8.0):
    box(f"lab_cornice_z{z}", CX, CY, z - 0.09, z + 0.09, 42.3, 12.3, MAT_WALL)
# 顶层檐口（12.0，混凝土色）
box("lab_cornice_top", CX, CY, 11.91, 12.09, 42.3, 12.3, MAT_CONC)

# ---------- 屋顶：屋顶板 12.0-12.3 深灰 ----------
box("lab_roofslab", CX, CY, 12.0, 12.3, 42.0, 12.0, MAT_ROOF)
# 女儿墙 12.3-12.85（厚 0.25），压顶 12.85-13.0
box("lab_parapet_N", CX, CY + 12.0/2 - 0.125, 12.3, 12.85, 42.0, 0.25, MAT_ROOF)
box("lab_parapet_S", CX, CY - 12.0/2 + 0.125, 12.3, 12.85, 42.0, 0.25, MAT_ROOF)
box("lab_parapet_E", CX + 42.0/2 - 0.125, CY, 12.3, 12.85, 0.25, 11.5, MAT_ROOF)
box("lab_parapet_W", CX - 42.0/2 + 0.125, CY, 12.3, 12.85, 0.25, 11.5, MAT_ROOF)
box("lab_coping_N", CX, CY + 12.0/2 - 0.125, 12.85, 13.0, 42.2, 0.45, MAT_COPING)
box("lab_coping_S", CX, CY - 12.0/2 + 0.125, 12.85, 13.0, 42.2, 0.45, MAT_COPING)
box("lab_coping_E", CX + 42.0/2 - 0.125, CY, 12.85, 13.0, 0.45, 11.7, MAT_COPING)
box("lab_coping_W", CX - 42.0/2 + 0.125, CY, 12.85, 13.0, 0.45, 11.7, MAT_COPING)
# 屋顶设备小盒 2 个 + 通风筒 1 个
box("lab_roof_eq1", CX - 10.0, CY - 2.0, 12.3, 13.4, 2.4, 1.8, MAT_METAL)
box("lab_roof_eq2", CX + 10.0, CY + 2.5, 12.3, 13.2, 1.8, 1.4, MAT_METAL)
cyl("lab_roof_vent", CX + 3.0, CY - 3.0, 12.3, 13.1, 0.4, MAT_METAL)

# ---------- 横向窗带（每层，四面） ----------
def window_band(floor_idx, zc, half_w, half_d, band_len_long, band_len_short):
    h = 1.6 if floor_idx == 1 else 1.8
    z0, z1 = zc - h/2, zc + h/2
    # 南北长面（y=±half_d）
    for sgn in (1, -1):
        y = CY + sgn * (half_d + 0.03)
        box(f"lab_win_f{floor_idx}_{'N' if sgn>0 else 'S'}",
            CX, y, z0, z1, band_len_long, 0.06, MAT_GLASS)
        # 竖向分格条（每 3m 一根）
        x = CX - band_len_long/2 + 1.5
        n = 0
        while x < CX + band_len_long/2 - 0.5:
            box(f"lab_mull_f{floor_idx}_{'N' if sgn>0 else 'S'}_{n}",
                x, y, z0, z1, 0.12, 0.10, MAT_METAL)
            x += 3.0
            n += 1
    # 东西短面（x=±half_w）
    for sgn in (1, -1):
        x = CX + sgn * (half_w + 0.03)
        box(f"lab_win_f{floor_idx}_{'E' if sgn>0 else 'W'}",
            x, CY, z0, z1, 0.06, band_len_short, MAT_GLASS)

window_band(1, 2.2, 21.0, 6.0, 38.0, 8.0)
window_band(2, 6.0, 20.9, 5.9, 37.8, 7.8)
window_band(3, 10.0, 20.8, 5.8, 37.6, 7.6)

# ---------- 入口雨棚（南面正中，朝校园内侧） ----------
box("lab_entry_canopy", CX, CY - 6.0 - 1.0, 3.4, 3.65, 6.0, 2.0, MAT_CONC)
box("lab_entry_col_L", CX - 2.6, CY - 6.9, 0.5, 3.4, 0.3, 0.3, MAT_CONC)
box("lab_entry_col_R", CX + 2.6, CY - 6.9, 0.5, 3.4, 0.3, 0.3, MAT_CONC)
box("lab_entry_steps", CX, CY - 6.0 - 1.3, 0.0, 0.5, 6.4, 2.6, MAT_CONC)

# ---------- 地面（仅预览衬底，不导出） ----------
bpy.ops.mesh.primitive_plane_add(size=140, location=(CX, CY, -0.02))
ground = bpy.context.active_object
ground.name = "lab_ground_preview"
ground.data.materials.append(MAT_PAVE)

# ---------- 光照（SPEC §2） ----------
sun_data = bpy.data.lights.new("sun", 'SUN')
sun_data.energy = 3.5
sun_data.use_shadow = True
sun = bpy.data.objects.new("sun", sun_data)
bpy.context.collection.objects.link(sun)
sun.rotation_euler = (math.radians(40), 0, math.radians(-45))  # 西南来，仰角 ~50°

world = bpy.data.worlds.new("world")
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.65, 0.78, 0.88, 1.0)
bg.inputs["Strength"].default_value = 1.0
bpy.context.scene.world = world

# ---------- 相机：45°俯视（楼长 42m，拉远一点） ----------
cam_data = bpy.data.cameras.new("cam")
cam_data.lens = 35
cam = bpy.data.objects.new("cam", cam_data)
bpy.context.collection.objects.link(cam)
cam.location = (CX + 36, CY - 36, 36)
d = mathutils.Vector((CX, CY, 6)) - cam.location
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.camera = cam

# ---------- 渲染设置 ----------
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.eevee.taa_render_samples = 16
scene.render.filepath = PNG
os.makedirs(os.path.dirname(PNG), exist_ok=True)
os.makedirs(os.path.dirname(GLB), exist_ok=True)

# ---------- 存 .blend ----------
bpy.ops.wm.save_as_mainfile(filepath=BLEND)

# ---------- 导出 .glb（只选本件对象，不含地面/灯光/相机） ----------
bpy.ops.object.select_all(action='DESELECT')
for o in OBJS:
    o.select_set(True)
bpy.context.view_layer.objects.active = OBJS[0]
bpy.ops.export_scene.gltf(filepath=GLB, export_format='GLB',
                           use_selection=True, export_apply=True)

# ---------- 回读校验 ----------
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.import_scene.gltf(filepath=GLB)
imported = [o for o in bpy.context.selected_objects]
print("GLB reimport objects:", len(imported))
bpy.ops.object.delete()

# ---------- 渲染预览 ----------
bpy.ops.render.render(write_still=True)

# 清理 .blend1 备份
blend1 = BLEND + "1"
if os.path.exists(blend1):
    os.remove(blend1)

print("DONE ov-lab")
