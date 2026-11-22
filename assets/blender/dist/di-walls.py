# di-walls: 配电房地面墙面 (floor + 4 walls + skirting + ceiling)
# 局部坐标: 房中心原点, x=长 16m (-8~+8), y=宽 10m (-5~+5), z 0~8m
# 墙体外缘即房间外缘 (16x10), 墙厚 0.2m, 内缘 x=+-7.8 / y=+-4.8
# 南墙 (y=-5) 门洞 1.2m 宽 x 2.4m 高, 位于 x=0 处, 上方门楣; 其余三面墙完整
# 墙体用分段盒子搭, 不用布尔切割
# 警戒线: 变压器区假设为 4 台主变一字排开 (单台 2.5x1.5m, 间距 0.5m,
#   区心 (0, 0.5), 占地 x -5.75~+5.75, y -0.25~+1.25; di-transformer 件
#   若排布不同, 警戒框需随之改), 线框沿区外缘 0.3m 处, 线宽 0.1m, 贴地面
# 颜色: 地面浅灰环氧 #B9B3A8, 墙米白 #F3E9D2, 踢脚深灰 #424A52,
#   天花板白 #E8E8E8, 警示黄 #E8B400; 材质只用 Principled BSDF
# 纹理 pass (2026-11-22): 程序化纹理, 不动结构
#   墙面: Noise 涂料斑驳 + 近地面水渍深浅, 粗糙度/Bump 有变化
#   地面: Noise 防滑颗粒 + Voronoi 细裂纹 + 大尺度磨损
#   警戒黄线: 边缘斑驳磨损; 踢脚线: 轻微噪波; 天花板: 轻微噪波
#   注意: 程序化 Noise/Voronoi 节点只保存在 .blend 里供渲染用,
#   glTF 导出器不导出程序化纹理, GLB 里只保留底色/粗糙度默认值。
# 渲染新规矩: 全部走 GitHub Actions, 本地不渲染、不出预览图。
import bpy
import math
import os
from mathutils import Vector

BASE = "/home/hatch/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot"
BLEND_PATH = BASE + "/assets/blender/dist/di-walls.blend"
GLB_PATH = BASE + "/assets/models/di-walls.glb"

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

# ---------- 纹理节点小工具 ----------
def _link(nt, src, src_out, dst, dst_in):
    nt.links.new(src.outputs[src_out], dst.inputs[dst_in])

def _noise(nt, scale, detail=2.0, roughness=0.7):
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    n.inputs["Roughness"].default_value = roughness
    return n

def _voronoi_edge(nt, scale):
    v = nt.nodes.new("ShaderNodeTexVoronoi")
    v.feature = 'DISTANCE_TO_EDGE'
    v.inputs["Scale"].default_value = scale
    return v

def _ramp(nt, stops):
    """stops: [(pos, value 0..1), ...] 黑白渐变, 用于控制混合强度。"""
    r = nt.nodes.new("ShaderNodeValToRGB")
    els = r.color_ramp.elements
    while len(els) < len(stops):
        els.new(0.5)
    for el, (pos, val) in zip(els, stops):
        el.position = pos
        el.color = (val, val, val, 1.0)
    return r

def _mix(nt, col1_hex, col2_hex, fac_node, fac_out="Color"):
    m = nt.nodes.new("ShaderNodeMixRGB")
    m.blend_type = 'MIX'
    m.inputs[1].default_value = (*hex_to_linear(col1_hex), 1.0)
    m.inputs[2].default_value = (*hex_to_linear(col2_hex), 1.0)
    if fac_node is not None:
        _link(nt, fac_node, fac_out, m, 0)
    return m

def _scale_fac(nt, src_node, src_out, factor):
    """把 0..1 的因子乘以 factor, 限制混合强度。"""
    m = nt.nodes.new("ShaderNodeMath")
    m.operation = 'MULTIPLY'
    m.inputs[1].default_value = factor
    _link(nt, src_node, src_out, m, 0)
    return m

def _rough_map(nt, noise_node, lo, hi):
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.clamp = True
    mr.inputs["From Min"].default_value = 0.0
    mr.inputs["From Max"].default_value = 1.0
    mr.inputs["To Min"].default_value = lo
    mr.inputs["To Max"].default_value = hi
    _link(nt, noise_node, "Fac", mr, 0)
    return mr

def _bump(nt, noise_node, strength, distance):
    b = nt.nodes.new("ShaderNodeBump")
    b.inputs["Strength"].default_value = strength
    b.inputs["Distance"].default_value = distance
    _link(nt, noise_node, "Fac", b, "Height")
    return b

def _texcoord_mapped(nt, scale):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    _link(nt, tc, "Generated", mp, "Vector")
    return tc, mp

def _finish(mat, color_node, rough_node, bump_node):
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    nt = mat.node_tree
    _link(nt, color_node, "Color", bsdf, "Base Color")
    if rough_node is not None:
        _link(nt, rough_node, "Result", bsdf, "Roughness")
    if bump_node is not None:
        _link(nt, bump_node, "Normal", bsdf, "Normal")

# ---------- 墙面纹理: 涂料斑驳 + 近地面水渍 ----------
def tex_wall(mat):
    nt = mat.node_tree
    tc, mp = _texcoord_mapped(nt, 3.0)
    # 大尺度斑驳: Noise -> Ramp(0.45~0.75) -> 底色/污渍色混合
    n1 = _noise(nt, 3.0, 2.0, 0.7)
    _link(nt, mp, "Vector", n1, "Vector")
    r1 = _ramp(nt, [(0.45, 0.0), (0.75, 1.0)])
    _link(nt, n1, "Fac", r1, "Fac")
    mix1 = _mix(nt, "#F3E9D2", "#DCCFA9", r1)
    # 近地面水渍: Z 越低越重 (0~0.25m 渐变) x 细 Noise
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    _link(nt, tc, "Generated", sep, "Vector")
    hm = nt.nodes.new("ShaderNodeMapRange")
    hm.clamp = True
    hm.inputs["From Min"].default_value = 0.0
    hm.inputs["From Max"].default_value = 0.25
    hm.inputs["To Min"].default_value = 1.0
    hm.inputs["To Max"].default_value = 0.0
    _link(nt, sep, "Z", hm, 0)
    n2 = _noise(nt, 1.5, 2.0, 0.7)
    _link(nt, mp, "Vector", n2, "Vector")
    r2 = _ramp(nt, [(0.5, 0.0), (0.8, 1.0)])
    _link(nt, n2, "Fac", r2, "Fac")
    mult = nt.nodes.new("ShaderNodeMath")
    mult.operation = 'MULTIPLY'
    _link(nt, hm, "Result", mult, 0)
    _link(nt, r2, "Color", mult, 1)
    mix2 = nt.nodes.new("ShaderNodeMixRGB")
    mix2.blend_type = 'MIX'
    mix2.inputs[1].default_value = (*hex_to_linear("#F3E9D2"), 1.0)
    mix2.inputs[2].default_value = (*hex_to_linear("#C4B48C"), 1.0)
    _link(nt, mix1, "Color", mix2, 1)
    _link(nt, mult, "Value", mix2, 0)
    # 粗糙度 0.78~0.95, Bump 细颗粒
    n3 = _noise(nt, 6.0, 2.0, 0.7)
    _link(nt, mp, "Vector", n3, "Vector")
    rough = _rough_map(nt, n3, 0.78, 0.95)
    n4 = _noise(nt, 14.0, 3.0, 0.6)
    _link(nt, mp, "Vector", n4, "Vector")
    bump = _bump(nt, n4, 0.12, 0.03)
    _finish(mat, mix2, rough, bump)

# ---------- 地面纹理: 防滑颗粒 + 细裂纹 + 磨损 ----------
def tex_floor(mat):
    nt = mat.node_tree
    tc, mp = _texcoord_mapped(nt, 2.0)
    # 细裂纹: Voronoi 距边 -> Ramp(0~0.05 白->黑, 白=裂纹) x0.55 混入深色
    v = _voronoi_edge(nt, 8.0)
    _link(nt, mp, "Vector", v, "Vector")
    rc = _ramp(nt, [(0.0, 1.0), (0.05, 0.0)])
    _link(nt, v, "Distance", rc, "Fac")
    fc = _scale_fac(nt, rc, "Color", 0.55)
    mix1 = _mix(nt, "#B9B3A8", "#8F887B", fc, "Value")
    # 大尺度磨损: Noise -> Ramp x0.5 混入浅色
    n1 = _noise(nt, 1.2, 2.0, 0.7)
    _link(nt, mp, "Vector", n1, "Vector")
    r1 = _ramp(nt, [(0.45, 0.0), (0.75, 1.0)])
    _link(nt, n1, "Fac", r1, "Fac")
    fw = _scale_fac(nt, r1, "Color", 0.5)
    mix2 = nt.nodes.new("ShaderNodeMixRGB")
    mix2.blend_type = 'MIX'
    mix2.inputs[2].default_value = (*hex_to_linear("#CFC8BA"), 1.0)
    _link(nt, mix1, "Color", mix2, 1)
    _link(nt, fw, "Value", mix2, 0)
    # 粗糙度 0.82~0.97, Bump 防滑颗粒
    n3 = _noise(nt, 10.0, 2.0, 0.7)
    _link(nt, mp, "Vector", n3, "Vector")
    rough = _rough_map(nt, n3, 0.82, 0.97)
    n4 = _noise(nt, 30.0, 2.0, 0.6)
    _link(nt, mp, "Vector", n4, "Vector")
    bump = _bump(nt, n4, 0.30, 0.02)
    _finish(mat, mix2, rough, bump)

# ---------- 警戒黄线纹理: 边缘斑驳磨损 ----------
def tex_yellow(mat):
    nt = mat.node_tree
    tc, mp = _texcoord_mapped(nt, 6.0)
    n1 = _noise(nt, 8.0, 2.0, 0.7)
    _link(nt, mp, "Vector", n1, "Vector")
    r1 = _ramp(nt, [(0.45, 0.0), (0.70, 1.0)])
    _link(nt, n1, "Fac", r1, "Fac")
    fw = _scale_fac(nt, r1, "Color", 0.5)
    mix1 = _mix(nt, "#E8B400", "#8A8378", fw, "Value")
    n3 = _noise(nt, 6.0, 2.0, 0.7)
    _link(nt, mp, "Vector", n3, "Vector")
    rough = _rough_map(nt, n3, 0.50, 0.75)
    n4 = _noise(nt, 18.0, 2.0, 0.6)
    _link(nt, mp, "Vector", n4, "Vector")
    bump = _bump(nt, n4, 0.12, 0.02)
    _finish(mat, mix1, rough, bump)

# ---------- 踢脚线纹理: 轻微噪波 ----------
def tex_skirt(mat):
    nt = mat.node_tree
    tc, mp = _texcoord_mapped(nt, 5.0)
    n1 = _noise(nt, 5.0, 2.0, 0.7)
    _link(nt, mp, "Vector", n1, "Vector")
    r1 = _ramp(nt, [(0.40, 0.0), (0.70, 1.0)])
    _link(nt, n1, "Fac", r1, "Fac")
    fw = _scale_fac(nt, r1, "Color", 0.4)
    mix1 = _mix(nt, "#424A52", "#33393F", fw, "Value")
    n3 = _noise(nt, 8.0, 2.0, 0.7)
    _link(nt, mp, "Vector", n3, "Vector")
    rough = _rough_map(nt, n3, 0.60, 0.80)
    n4 = _noise(nt, 10.0, 2.0, 0.6)
    _link(nt, mp, "Vector", n4, "Vector")
    bump = _bump(nt, n4, 0.10, 0.02)
    _finish(mat, mix1, rough, bump)

# ---------- 天花板纹理: 轻微噪波 ----------
def tex_ceiling(mat):
    nt = mat.node_tree
    tc, mp = _texcoord_mapped(nt, 4.0)
    n1 = _noise(nt, 4.0, 2.0, 0.7)
    _link(nt, mp, "Vector", n1, "Vector")
    r1 = _ramp(nt, [(0.40, 0.0), (0.70, 1.0)])
    _link(nt, n1, "Fac", r1, "Fac")
    fw = _scale_fac(nt, r1, "Color", 0.25)
    mix1 = _mix(nt, "#E8E8E8", "#D8D8D8", fw, "Value")
    n3 = _noise(nt, 8.0, 2.0, 0.7)
    _link(nt, mp, "Vector", n3, "Vector")
    rough = _rough_map(nt, n3, 0.85, 0.95)
    n4 = _noise(nt, 8.0, 2.0, 0.6)
    _link(nt, mp, "Vector", n4, "Vector")
    bump = _bump(nt, n4, 0.06, 0.02)
    _finish(mat, mix1, rough, bump)

FLOOR_MAT = make_material("Floor_Epoxy", "#B9B3A8", 0.9, 0.0)
WALL_MAT = make_material("Wall_Cream", "#F3E9D2", 0.85, 0.0)
SKIRT_MAT = make_material("Skirting_DarkGrey", "#424A52", 0.7, 0.0)
CEIL_MAT = make_material("Ceiling_White", "#E8E8E8", 0.9, 0.0)
YELLOW_MAT = make_material("Warning_Yellow", "#E8B400", 0.6, 0.0)

tex_floor(FLOOR_MAT)
tex_wall(WALL_MAT)
tex_skirt(SKIRT_MAT)
tex_ceiling(CEIL_MAT)
tex_yellow(YELLOW_MAT)

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

objs = []

# ---------- 地面: 16x10m, 厚 0.05m, 顶面 z=0 ----------
objs.append(add_box("Floor", (16.0, 10.0, 0.05), (0.0, 0.0, -0.025), FLOOR_MAT, bevel=0.02))

# ---------- 四面墙: 高 8m, 厚 0.2m ----------
# 北墙完整 (y=+5 外缘, 中心 y=4.9)
objs.append(add_box("Wall_North", (16.0, 0.2, 8.0), (0.0, 4.9, 4.0), WALL_MAT, bevel=0.02))
# 东墙 / 西墙 (夹在南北墙之间, 长 9.6m)
objs.append(add_box("Wall_East", (0.2, 9.6, 8.0), (7.9, 0.0, 4.0), WALL_MAT, bevel=0.02))
objs.append(add_box("Wall_West", (0.2, 9.6, 8.0), (-7.9, 0.0, 4.0), WALL_MAT, bevel=0.02))
# 南墙 (y=-5): 门洞 1.2 宽 x 2.4 高, x=0 处; 左右两段 + 上方门楣
# 左段 x -8~-0.6 (长 7.4, 中心 -4.3), 右段 x 0.6~8 (中心 4.3)
objs.append(add_box("Wall_South_Left", (7.4, 0.2, 8.0), (-4.3, -4.9, 4.0), WALL_MAT, bevel=0.02))
objs.append(add_box("Wall_South_Right", (7.4, 0.2, 8.0), (4.3, -4.9, 4.0), WALL_MAT, bevel=0.02))
# 门楣: x -0.6~0.6 (宽 1.2), z 2.4~8.0 (高 5.6, 中心 5.2)
objs.append(add_box("Wall_South_Lintel", (1.2, 0.2, 5.6), (0.0, -4.9, 5.2), WALL_MAT, bevel=0.02))

# ---------- 踢脚线: 高 0.15m, 深灰, 贴墙内面 (厚 0.02m), 门洞处断开 ----------
# 北墙内面 y=4.8 -> 条中心 y=4.79; 南墙内面 y=-4.8 -> y=-4.79; 东西墙内面 x=+-7.8 -> x=+-7.79
objs.append(add_box("Skirting_North", (15.6, 0.02, 0.15), (0.0, 4.79, 0.075), SKIRT_MAT))
objs.append(add_box("Skirting_South_Left", (7.2, 0.02, 0.15), (-4.2, -4.79, 0.075), SKIRT_MAT))
objs.append(add_box("Skirting_South_Right", (7.2, 0.02, 0.15), (4.2, -4.79, 0.075), SKIRT_MAT))
objs.append(add_box("Skirting_East", (0.02, 9.6, 0.15), (7.79, 0.0, 0.075), SKIRT_MAT))
objs.append(add_box("Skirting_West", (0.02, 9.6, 0.15), (-7.79, 0.0, 0.075), SKIRT_MAT))

# ---------- 天花板: 16x10m 白色平板, 底面 z=8.0, 厚 0.1m ----------
objs.append(add_box("Ceiling", (16.0, 10.0, 0.1), (0.0, 0.0, 8.05), CEIL_MAT, bevel=0.02))

# ---------- 黄色警戒线框: 沿变压器区外缘 0.3m, 线宽 0.1m, 厚 0.01m 贴地面 ----------
# 区外缘框 x -6.05~+6.05, y -0.55~+1.55; 南北条长 12.1m, 东西条长 1.9m (角部不错缝)
objs.append(add_box("Warning_Line_North", (12.1, 0.1, 0.01), (0.0, 1.50, 0.005), YELLOW_MAT))
objs.append(add_box("Warning_Line_South", (12.1, 0.1, 0.01), (0.0, -0.50, 0.005), YELLOW_MAT))
objs.append(add_box("Warning_Line_East", (0.1, 1.9, 0.01), (6.00, 0.5, 0.005), YELLOW_MAT))
objs.append(add_box("Warning_Line_West", (0.1, 1.9, 0.01), (-6.00, 0.5, 0.005), YELLOW_MAT))

print("di-walls objects:", len(objs), [o.name for o in objs])

# ---------- lighting (SPEC §2; 仅供 GH Actions 渲染用, 本地不渲染) ----------
# 太阳光: 能量 3.5, 从西南来, 仰角约 50°, 开阴影
sun_data = bpy.data.lights.new("Sun", type='SUN')
sun_data.energy = 3.5
sun_data.use_shadow = True
sun = bpy.data.objects.new("Sun", sun_data)
bpy.context.collection.objects.link(sun)
sun.location = (-20.0, -20.0, 30.0)
light_dir = Vector((math.cos(math.radians(50)) * math.cos(math.radians(45)),
                    math.cos(math.radians(50)) * math.sin(math.radians(45)),
                    -math.sin(math.radians(50))))
sun.rotation_mode = 'QUATERNION'
sun.rotation_quaternion = light_dir.to_track_quat('-Z', 'Y')

# 世界背景: 淡蓝 (0.65, 0.78, 0.88), 强度 1.0
world = bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.65, 0.78, 0.88, 1.0)
bg.inputs["Strength"].default_value = 1.0

# 室内预览补光 (仅预览, 不导出: 房间有天花板, 太阳光进不来)
for i, lx in enumerate((-4.0, 4.0)):
    ld = bpy.data.lights.new("Preview_Point_%d" % i, type='POINT')
    ld.energy = 500.0
    ld.shadow_soft_size = 0.5
    lo = bpy.data.objects.new("Preview_Point_%d" % i, ld)
    bpy.context.collection.objects.link(lo)
    lo.location = (lx, 0.0, 6.0)

# ---------- camera: 室内视角, 东北角高处看向南墙门洞 ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 24.0
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera = cam
cam.location = (6.2, 3.8, 5.0)
target = Vector((-2.0, -4.8, 1.0))
cam.rotation_mode = 'QUATERNION'
cam.rotation_quaternion = (target - cam.location).to_track_quat('-Z', 'Y')

# ---------- render settings (仅保留配置供 GH Actions 用, 本地不执行渲染) ----------
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.eevee.taa_render_samples = 16
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100

# ---------- save .blend ----------
os.makedirs(os.path.dirname(BLEND_PATH), exist_ok=True)
os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
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
for ob in imported:
    for slot in ob.material_slots:
        m = slot.material
        if m and m.use_nodes:
            bsdf = m.node_tree.nodes.get("Principled BSDF")
            if bsdf:
                print("GLB reimport mat:", ob.name, m.name,
                      "base_color=", tuple(round(v, 4) for v in bsdf.inputs["Base Color"].default_value),
                      "roughness=", round(bsdf.inputs["Roughness"].default_value, 3))
assert len(imported) == len(objs), "glb reimport failed: expected %d objects, got %d" % (len(objs), len(imported))
# 删掉回读的副本, 恢复干净场景
bpy.ops.object.select_all(action='DESELECT')
for ob in imported:
    ob.select_set(True)
bpy.ops.object.delete()

bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("DONE di-walls")
