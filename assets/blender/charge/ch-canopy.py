# ch-canopy v2: 充电区雨棚重做 (Blender 坐标, x 东 / y 北 / z 上, 单位米)
# 占地/位置照旧版: 顶板 16(x) x 6.5(y) m, 中心 (43.25, -76), 北侧高 0.15 m 排水
# v2 按真实雨棚结构: 厚顶板 + 四周边梁 + 檩条 + 分块接缝 + 钢柱 + 柱脚底板 + 地脚螺栓
# 只做雨棚, 不做充电桩 / 车辆 / 车位线
import bpy
import math
import os
from mathutils import Vector

ROOT = os.path.expanduser(
    "~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
BLEND = os.path.join(ROOT, "assets/blender/charge/ch-canopy.blend")
GLB = os.path.join(ROOT, "assets/models/ch-canopy.glb")
PNG = os.path.join(ROOT, "screenshots/blender/ch-canopy.png")
for p in (BLEND, GLB, PNG):
    os.makedirs(os.path.dirname(p), exist_ok=True)

# ---------- 清空场景 ----------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# ---------- sRGB -> 线性 ----------
def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def hex_to_linear(h):
    h = h.lstrip('#')
    return tuple(srgb_to_linear(int(h[i:i + 2], 16) / 255.0)
                 for i in (0, 2, 4))

def _shade(hex_color, f):
    r, g, b = hex_to_linear(hex_color)
    return (min(max(r * f, 0.0), 1.0), min(max(g * f, 0.0), 1.0),
            min(max(b * f, 0.0), 1.0), 1.0)

def _ramp(nt, c0, c1):
    node = nt.nodes.new('ShaderNodeValToRGB')
    node.color_ramp.elements[0].position = 0.0
    node.color_ramp.elements[0].color = c0
    node.color_ramp.elements[1].position = 1.0
    node.color_ramp.elements[1].color = c1
    return node

def _noise(nt, mapping, scale, detail=3.0, distortion=0.0):
    node = nt.nodes.new('ShaderNodeTexNoise')
    node.inputs["Scale"].default_value = scale
    node.inputs["Detail"].default_value = detail
    node.inputs["Distortion"].default_value = distortion
    nt.links.new(mapping.outputs["Vector"], node.inputs["Vector"])
    return node

def _rough_map(nt, fac_out, lo, hi):
    node = nt.nodes.new('ShaderNodeMapRange')
    node.inputs["From Min"].default_value = 0.0
    node.inputs["From Max"].default_value = 1.0
    node.inputs["To Min"].default_value = lo
    node.inputs["To Max"].default_value = hi
    nt.links.new(fac_out, node.inputs["Value"])
    return node

def _bump(nt, height_out, strength, distance):
    node = nt.nodes.new('ShaderNodeBump')
    node.inputs["Strength"].default_value = strength
    node.inputs["Distance"].default_value = distance
    nt.links.new(height_out, node.inputs["Height"])
    return node

def make_mat(name, hex_color, roughness=0.6, metallic=0.0, kind='flat'):
    """Principled BSDF + 程序化纹理(无贴图): 没有任何一个面是全平的.
    roof: 拉丝波纹(Wave 沿 y 变化, 丝线沿长边 x 走向, 有方向感) + 双层噪波,
          颜色深浅不均 + 粗糙度 0.30~0.48 变化 + 凹凸
    steel: 轻微噪波, 颜色微差 + 粗糙度变化 + 轻微凹凸
    concrete: 粗细双层噪波颗粒, 深浅斑驳 + 粗糙度变化 + 明显凹凸颗粒"""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    base = (*hex_to_linear(hex_color), 1.0)
    bsdf.inputs["Base Color"].default_value = base
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if kind == 'flat':
        return mat

    tex_coord = nt.nodes.new('ShaderNodeTexCoord')
    mapping = nt.nodes.new('ShaderNodeMapping')
    nt.links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    if kind == 'roof':
        mapping.inputs["Scale"].default_value = (0.6, 0.6, 0.6)
        n_coarse = _noise(nt, mapping, 2.5, detail=3.0, distortion=0.3)
        n_fine = _noise(nt, mapping, 8.0, detail=4.0)
        wave = nt.nodes.new('ShaderNodeTexWave')
        wave.wave_type = 'BANDS'
        wave.bands_direction = 'Y'  # 波纹沿 y 变化, 拉丝线沿长边(x)走向
        wave.inputs["Scale"].default_value = 5.0
        wave.inputs["Distortion"].default_value = 3.0
        wave.inputs["Detail"].default_value = 3.0
        wave.inputs["Detail Scale"].default_value = 1.0
        nt.links.new(mapping.outputs["Vector"], wave.inputs["Vector"])
        # 颜色: 粗噪波深浅斑块 -> 拉丝波纹明暗条纹, 两级混合
        mix1 = nt.nodes.new('ShaderNodeMixRGB')
        mix1.blend_type = 'MIX'
        mix1.inputs[0].default_value = 0.35
        mix1.inputs[1].default_value = base
        ramp1 = _ramp(nt, _shade(hex_color, 0.78), _shade(hex_color, 1.12))
        nt.links.new(n_coarse.outputs["Fac"], ramp1.inputs["Fac"])
        nt.links.new(ramp1.outputs["Color"], mix1.inputs[2])
        mix2 = nt.nodes.new('ShaderNodeMixRGB')
        mix2.blend_type = 'MIX'
        mix2.inputs[0].default_value = 0.40
        nt.links.new(mix1.outputs["Color"], mix2.inputs[1])
        ramp2 = _ramp(nt, _shade(hex_color, 0.85), _shade(hex_color, 1.10))
        nt.links.new(wave.outputs["Fac"], ramp2.inputs["Fac"])
        nt.links.new(ramp2.outputs["Color"], mix2.inputs[2])
        nt.links.new(mix2.outputs["Color"], bsdf.inputs["Base Color"])
        # 粗糙度: 粗噪波映射 0.30~0.48
        nt.links.new(_rough_map(nt, n_coarse.outputs["Fac"], roughness - 0.08,
                                roughness + 0.10).outputs["Result"],
                     bsdf.inputs["Roughness"])
        # 凹凸: 细噪波 + 拉丝波纹 * 0.4
        mult = nt.nodes.new('ShaderNodeMath')
        mult.operation = 'MULTIPLY'
        mult.inputs[1].default_value = 0.4
        nt.links.new(wave.outputs["Fac"], mult.inputs[0])
        add = nt.nodes.new('ShaderNodeMath')
        add.operation = 'ADD'
        nt.links.new(n_fine.outputs["Fac"], add.inputs[0])
        nt.links.new(mult.outputs["Value"], add.inputs[1])
        nt.links.new(_bump(nt, add.outputs["Value"], 0.25, 0.03).outputs["Normal"],
                     bsdf.inputs["Normal"])
    elif kind == 'steel':
        mapping.inputs["Scale"].default_value = (1.5, 1.5, 1.5)
        n = _noise(nt, mapping, 3.0, detail=3.0, distortion=0.5)
        mix1 = nt.nodes.new('ShaderNodeMixRGB')
        mix1.blend_type = 'MIX'
        mix1.inputs[0].default_value = 0.30
        mix1.inputs[1].default_value = base
        ramp1 = _ramp(nt, _shade(hex_color, 0.85), _shade(hex_color, 1.12))
        nt.links.new(n.outputs["Fac"], ramp1.inputs["Fac"])
        nt.links.new(ramp1.outputs["Color"], mix1.inputs[2])
        nt.links.new(mix1.outputs["Color"], bsdf.inputs["Base Color"])
        nt.links.new(_rough_map(nt, n.outputs["Fac"], roughness - 0.06,
                                roughness + 0.08).outputs["Result"],
                     bsdf.inputs["Roughness"])
        nt.links.new(_bump(nt, n.outputs["Fac"], 0.12, 0.02).outputs["Normal"],
                     bsdf.inputs["Normal"])
    elif kind == 'concrete':
        mapping.inputs["Scale"].default_value = (3.0, 3.0, 3.0)
        n_coarse = _noise(nt, mapping, 1.5, detail=3.0, distortion=0.4)
        n_fine = _noise(nt, mapping, 8.0, detail=4.0)
        mix1 = nt.nodes.new('ShaderNodeMixRGB')
        mix1.blend_type = 'MIX'
        mix1.inputs[0].default_value = 0.35
        mix1.inputs[1].default_value = base
        ramp1 = _ramp(nt, _shade(hex_color, 0.80), _shade(hex_color, 1.15))
        nt.links.new(n_coarse.outputs["Fac"], ramp1.inputs["Fac"])
        nt.links.new(ramp1.outputs["Color"], mix1.inputs[2])
        mix2 = nt.nodes.new('ShaderNodeMixRGB')
        mix2.blend_type = 'MIX'
        mix2.inputs[0].default_value = 0.35
        nt.links.new(mix1.outputs["Color"], mix2.inputs[1])
        ramp2 = _ramp(nt, _shade(hex_color, 0.88), _shade(hex_color, 1.10))
        nt.links.new(n_fine.outputs["Fac"], ramp2.inputs["Fac"])
        nt.links.new(ramp2.outputs["Color"], mix2.inputs[2])
        nt.links.new(mix2.outputs["Color"], bsdf.inputs["Base Color"])
        nt.links.new(_rough_map(nt, n_fine.outputs["Fac"], roughness - 0.05,
                                min(roughness + 0.05, 1.0)).outputs["Result"],
                     bsdf.inputs["Roughness"])
        mult = nt.nodes.new('ShaderNodeMath')
        mult.operation = 'MULTIPLY'
        mult.inputs[1].default_value = 0.5
        nt.links.new(n_coarse.outputs["Fac"], mult.inputs[0])
        add = nt.nodes.new('ShaderNodeMath')
        add.operation = 'ADD'
        nt.links.new(n_fine.outputs["Fac"], add.inputs[0])
        nt.links.new(mult.outputs["Value"], add.inputs[1])
        nt.links.new(_bump(nt, add.outputs["Value"], 0.5, 0.04).outputs["Normal"],
                     bsdf.inputs["Normal"])
    return mat

# 材质区分: 顶板浅灰蓝金属(拉丝+噪波) / 钢构深灰钢(轻微噪波) / 柱脚底板混凝土(噪波颗粒), 全部 Principled BSDF + 程序化纹理
MAT_ROOF = make_mat("CanopyRoof_BlueGrayMetal", "#C8D2D8",
                    roughness=0.38, metallic=0.60, kind='roof')
MAT_SEAM = make_mat("CanopyRoofSeam_Darker", "#9FB0B8",
                    roughness=0.50, metallic=0.50, kind='steel')
MAT_STEEL = make_mat("CanopySteel_DarkGray", "#4A4F55",
                     roughness=0.45, metallic=0.60, kind='steel')
MAT_BOLT = make_mat("CanopyBolt_Dark", "#33383D",
                    roughness=0.40, metallic=0.70, kind='steel')
MAT_CONC = make_mat("CanopyBase_Concrete", "#B9B3A8",
                    roughness=0.95, metallic=0.0, kind='concrete')

def add_box(name, dims, loc, mat, rot_x=0.0, bevel=0.02):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if rot_x:
        obj.rotation_euler.x = rot_x
    if bevel and bevel > 0:
        bev = obj.modifiers.new("Bevel", 'BEVEL')
        bev.width = bevel
        bev.segments = 2
    obj.data.materials.append(mat)
    return obj

# ---------- 尺寸常量 (照旧版) ----------
ROOF_C = (43.25, -76.0, 3.2)      # 顶板中心
ROOF_L, ROOF_W, ROOF_T = 16.0, 6.5, 0.15   # 长 x 宽 x 板厚 (板厚 0.15 >= 0.08)
TILT = math.atan(0.15 / 6.5)      # 约 1.32 度, 绕 x 轴正转 -> 北(+y)侧抬高
TAN_T = math.tan(TILT)
# 顶板底面 z(中心 y 处) = 3.2 - 0.075 = 3.125; 随 y 的变化: z = 3.125 + (y+76)*TAN_T
def slab_bottom_z(y):
    return 3.125 + (y + 76.0) * TAN_T

CANOPY_OBJS = []

# ---------- 顶板 (厚板, 不是纸片) ----------
roof = add_box("CanopyRoof", (ROOF_L, ROOF_W, ROOF_T), ROOF_C, MAT_ROOF,
               rot_x=TILT, bevel=0.02)
CANOPY_OBJS.append(roof)

# ---------- 顶板分块接缝: 沿长边每 2m 一道, 薄板条, 略深一号金属 ----------
for i, sx in enumerate([37.25, 39.25, 41.25, 43.25, 45.25, 47.25, 49.25], 1):
    seam = add_box("CanopyRoofSeam_%d" % i, (0.04, ROOF_W, 0.02),
                   (sx, -76.0, 3.275 + 0.01), MAT_SEAM,
                   rot_x=TILT, bevel=0)
    CANOPY_OBJS.append(seam)

# ---------- 边缘梁: 四周下翻, 高 0.15m, 厚 0.10m, 深灰钢 ----------
# 南/北长梁 (沿 x): 顶面贴顶板底, 梁高向下 0.15
for name, by in (("CanopyEdgeBeam_S", -79.20), ("CanopyEdgeBeam_N", -72.80)):
    bz = slab_bottom_z(by) - 0.075
    beam = add_box(name, (ROOF_L, 0.10, 0.15), (43.25, by, bz), MAT_STEEL,
                   rot_x=TILT, bevel=0.015)
    CANOPY_OBJS.append(beam)
# 东/西短梁 (沿 y)
for name, bx in (("CanopyEdgeBeam_W", 35.30), ("CanopyEdgeBeam_E", 51.20)):
    beam = add_box(name, (0.10, ROOF_W - 0.20, 0.15),
                   (bx, -76.0, 3.125 - 0.075), MAT_STEEL,
                   rot_x=TILT, bevel=0.015)
    CANOPY_OBJS.append(beam)

# ---------- 檩条: 顶板下沿短边(y)方向, 每 1.5m 一根, 0.08 x 0.12 断面 ----------
for i, px in enumerate([36.0 + k * 1.5 for k in range(11)], 1):
    purlin = add_box("CanopyPurlin_%02d" % i, (0.08, ROOF_W - 0.20, 0.12),
                     (px, -76.0, 3.125 - 0.06), MAT_STEEL,
                     rot_x=TILT, bevel=0.01)
    CANOPY_OBJS.append(purlin)

# ---------- 钢柱 + 柱脚底板 + 地脚螺栓 ----------
# 柱位照旧版: (36.5, -78.5) (36.5, -73.5) (50.0, -78.5) (50.0, -73.5)
COLS = [(36.5, -78.5), (36.5, -73.5), (50.0, -78.5), (50.0, -73.5)]
for i, (cx, cy) in enumerate(COLS, 1):
    z_under = slab_bottom_z(cy)          # 该柱位置处的顶板底面高度
    col_h = z_under - 0.02               # 柱从底板顶面 (z=0.02) 立到顶板底
    col = add_box("CanopyColumn_%d" % i, (0.15, 0.15, col_h),
                  (cx, cy, 0.02 + col_h / 2.0), MAT_STEEL, bevel=0.01)
    CANOPY_OBJS.append(col)
    # 柱脚底板: 0.3 x 0.3 x 0.02 m, 混凝土
    base = add_box("CanopyBasePlate_%d" % i, (0.30, 0.30, 0.02),
                   (cx, cy, 0.01), MAT_CONC, bevel=0.008)
    CANOPY_OBJS.append(base)
    # 地脚螺栓: 底板四角各 1 块 0.04 x 0.04 x 0.06 m
    for j, (dx, dy) in enumerate(
            [(-0.10, -0.10), (-0.10, 0.10), (0.10, -0.10), (0.10, 0.10)], 1):
        bolt = add_box("CanopyBolt_%d_%d" % (i, j), (0.04, 0.04, 0.06),
                       (cx + dx, cy + dy, 0.05), MAT_BOLT, bevel=0)
        CANOPY_OBJS.append(bolt)

print("Canopy parts:", len(CANOPY_OBJS),
      "columns: 4, purlins: 11, seams: 7, edge beams: 4, bolts: 16")

# ---------- 光照 (SPEC §2) ----------
sun_dir = Vector((math.cos(math.radians(50)) / math.sqrt(2),
                  math.cos(math.radians(50)) / math.sqrt(2),
                  -math.sin(math.radians(50))))
bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
sun = bpy.context.active_object
sun.name = "Sun"
sun.data.energy = 3.5
sun.data.use_shadow = True
sun.rotation_euler = sun_dir.to_track_quat('-Z', 'Y').to_euler()

world = bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.65, 0.78, 0.88, 1.0)
bg.inputs["Strength"].default_value = 1.0

# ---------- 预览相机: 低机位近景, 从充电区前侧(西南)约 2m 高、平面 45 度看过去 ----------
# 仰视顶板底, 能看到棚顶厚度、边梁、檩条、柱子、柱脚; 阴影落在地面上
TARGET = Vector((43.25, -76.0, 2.1))
cam_loc = Vector((33.25, -86.0, 2.0))
bpy.ops.object.camera_add(location=cam_loc)
cam = bpy.context.active_object
cam.name = "PreviewCamera"
cam.data.lens = 26.0
cam.rotation_euler = (TARGET - cam_loc).to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.camera = cam

# ---------- 预览用地垫 (仅衬托预览, 不导出、不属于本件) ----------
bpy.ops.mesh.primitive_plane_add(size=40.0, location=(43.25, -76.0, -0.01))
ground = bpy.context.active_object
ground.name = "PREVIEW_Ground"
ground.data.materials.append(
    make_mat("PreviewGround_Asphalt", "#424A52", roughness=0.9))

# ---------- 存盘 ----------
bpy.ops.wm.save_as_mainfile(filepath=BLEND)

# ---------- 导出 GLB (只选本件) ----------
bpy.ops.object.select_all(action='DESELECT')
for obj in CANOPY_OBJS:
    obj.select_set(True)
bpy.context.view_layer.objects.active = roof
bpy.ops.export_scene.gltf(filepath=GLB, export_format='GLB',
                          use_selection=True, export_apply=True)

# ---------- 回读确认 ----------
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB)
imported = [o for o in bpy.data.objects if o not in before]
print("GLB reimport objects:", len(imported), [o.name for o in imported])
assert imported, "GLB reimport returned no objects"
for o in imported:
    bpy.data.objects.remove(o, do_unlink=True)

# ---------- 渲染预览 ----------
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100
scene.eevee.taa_render_samples = 16
scene.render.filepath = PNG
scene.render.image_settings.file_format = 'PNG'
bpy.ops.render.render(write_still=True)

blend1 = BLEND + "1"
if os.path.exists(blend1):
    os.remove(blend1)

print("DONE ch-canopy")
