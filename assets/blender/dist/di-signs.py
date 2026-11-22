# di-signs: 配电房标识牌 (墙面警示牌 2 块 + 柜门编号牌 6 块)
# 局部坐标: 房中心原点, x=长 16m (-8~+8), y=宽 10m (-5~+5), z 0~8m
# 墙面牌: 北墙 y=+5 内侧 "高压危险" 0.6x0.4m 红底白字框黄边, 中心 (0, 4.97, 2.4)
#         东墙 x=+8 内侧 "禁止合闸 有人工作" 0.6x0.4m 白底红字框, 中心 (7.97, 0, 2.4)
# 编号牌: 6 台配电柜门上各 1 块 0.2x0.12m 蓝底白框, 对齐 di-cabinets 柜子
#         中心 x=-6/-3.6/-1.2/+1.2/+3.6/+6, 贴柜门南面 y~4.08, z=1.35
#         (柜门面 y=4.085, 仪表窗 z 1.6~1.9, 把手 z 1.05~1.09, 编号牌放中间空位)
# 牌面用薄板 + 彩色边框条做, 不用文字纹理, 文字用色块示意
# 只做标识牌: 不做配电柜/变压器/母线线缆/墙面地面
# 材质只用 Principled BSDF
# 渲染: 本地不渲染, 预览图走 GitHub Actions 出图; 本脚本只做建模→存盘→导出→回读验证
# (灯光/相机仍保留在场景里, 供 Actions 渲染用)
import bpy
import math
import os
from mathutils import Vector

BASE = "/home/hatch/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot"
BLEND_PATH = BASE + "/assets/blender/dist/di-signs.blend"
GLB_PATH = BASE + "/assets/models/di-signs.glb"

# ---------- clean scene ----------
bpy.ops.wm.read_factory_settings(use_empty=True)

def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def hex_to_linear(h):
    h = h.lstrip("#")
    return tuple(srgb_to_linear(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4))

def make_material(name, hex_color, roughness=0.5, metallic=0.0,
                  noise_scale=4.0, noise_offset=(0.0, 0.0)):
    """程序化纹理材质 (红线要求): 噪波做轻微粗糙度变化 + 深浅不均 + 轻微凹凸,
    没有任何一个面是全平的; 每种颜色用不同的噪波尺度/偏移区分开.
    只用程序化节点, 不用贴图."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    base = hex_to_linear(hex_color)
    # Base Color 保持纯色数值 (不挂节点): glTF 导出器解析不了噪波混色节点,
    # 一挂节点导出后底色会丢成白 (已实测), 所以底色只走 socket 默认值
    bsdf.inputs["Base Color"].default_value = (*base, 1.0)
    # 噪波源 (Generated 坐标, 粗斑块, 牌面上看得见)
    texcoord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Location"].default_value = (noise_offset[0], noise_offset[1], 0.0)
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = noise_scale
    noise.inputs["Detail"].default_value = 2.5
    noise.inputs["Roughness"].default_value = 0.7
    noise.inputs["Distortion"].default_value = 0.3
    nt.links.new(texcoord.outputs["Generated"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    # Roughness: 噪波映射到 roughness +/-0.3, 光照下形成深浅不均
    # (20px 大的牌面上 +/-0.2 几乎看不出, 必须加到 +/-0.3 才可见)
    rough_range = nt.nodes.new("ShaderNodeMapRange")
    rough_range.clamp = True
    rough_range.inputs["From Min"].default_value = 0.0
    rough_range.inputs["From Max"].default_value = 1.0
    rough_range.inputs["To Min"].default_value = max(0.05, roughness - 0.3)
    rough_range.inputs["To Max"].default_value = min(1.0, roughness + 0.3)
    nt.links.new(noise.outputs["Fac"], rough_range.inputs["Value"])
    nt.links.new(rough_range.outputs[0], bsdf.inputs["Roughness"])
    # 轻微凹凸, 强化漆面/塑料质感
    # (实测: 牌面朝南、太阳在西南, 镜面反射打不到相机, 粗糙度变化在预览里
    #  几乎不可见; 只有凹凸能改漫反射明暗, 强度必须到 1.0 纹理才看得见)
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 1.0
    bump.inputs["Distance"].default_value = 0.1
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Metallic"].default_value = metallic
    return mat

RED_MAT = make_material("Sign_Red", "#C0392B", 0.45, 0.0, noise_scale=2.5, noise_offset=(0.0, 0.0))
WHITE_MAT = make_material("Sign_White", "#F5F5F0", 0.35, 0.0, noise_scale=3.5, noise_offset=(3.7, 1.2))
YELLOW_MAT = make_material("Sign_Yellow", "#E8B400", 0.5, 0.0, noise_scale=3.0, noise_offset=(7.1, 4.3))
BLUE_MAT = make_material("Sign_Blue", "#1F4E79", 0.55, 0.0, noise_scale=3.5, noise_offset=(2.3, 8.9))

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

# ---------- 墙面警示牌 1: 北墙 "高压危险", 红底 + 黄边 + 白字色块 ----------
# 边框底板 (黄, 稍大一圈, 贴墙): 0.66 x 0.015 x 0.46, y 4.978~4.993
objs.append(add_box("Warn_Border", (0.66, 0.015, 0.46), (0.0, 4.985, 2.4), YELLOW_MAT, bevel=0.003))
# 牌面 (红): 0.6 x 0.02 x 0.4, y 4.96~4.98
objs.append(add_box("Warn_Plate", (0.6, 0.02, 0.4), (0.0, 4.97, 2.4), RED_MAT, bevel=0.003))
# 白字色块示意: 上行宽条 + 下行两条短条, 贴牌面南侧 y~4.958
objs.append(add_box("Warn_Text1", (0.46, 0.008, 0.11), (0.0, 4.958, 2.47), WHITE_MAT))
objs.append(add_box("Warn_Text2", (0.30, 0.008, 0.04), (0.0, 4.958, 2.32), WHITE_MAT))
objs.append(add_box("Warn_Text3", (0.30, 0.008, 0.04), (0.0, 4.958, 2.26), WHITE_MAT))

# ---------- 墙面警示牌 2: 东墙 "禁止合闸 有人工作", 白底 + 红边 + 红字色块 ----------
# 边框底板 (红, 稍大一圈, 贴墙): 0.015 x 0.66 x 0.46, x 7.978~7.993
objs.append(add_box("NoClose_Border", (0.015, 0.66, 0.46), (7.985, 0.0, 2.4), RED_MAT, bevel=0.003))
# 牌面 (白): 0.02 x 0.6 x 0.4, x 7.96~7.98
objs.append(add_box("NoClose_Plate", (0.02, 0.6, 0.4), (7.97, 0.0, 2.4), WHITE_MAT, bevel=0.003))
# 红字色块示意: 三行横条, 贴牌面西侧 x~7.958
objs.append(add_box("NoClose_Text1", (0.008, 0.44, 0.07), (7.958, 0.0, 2.49), RED_MAT))
objs.append(add_box("NoClose_Text2", (0.008, 0.44, 0.07), (7.958, 0.0, 2.38), RED_MAT))
objs.append(add_box("NoClose_Text3", (0.008, 0.30, 0.07), (7.958, 0.0, 2.27), RED_MAT))

# ---------- 设备编号牌 6 块: 柜门上, 蓝底白框, 贴门面南侧 ----------
# 柜门面 y=4.085; 边框底板 y 4.080~4.092, 牌面 y 4.069~4.084, 白字条 y 4.066~4.070
for i, cx in enumerate((-6.0, -3.6, -1.2, 1.2, 3.6, 6.0)):
    tag = "Num%d" % (i + 1)
    objs.append(add_box("%s_Border" % tag, (0.24, 0.012, 0.16), (cx, 4.082, 1.35), WHITE_MAT, bevel=0.002))
    objs.append(add_box("%s_Plate" % tag, (0.20, 0.015, 0.12), (cx, 4.077, 1.35), BLUE_MAT, bevel=0.002))
    objs.append(add_box("%s_Text" % tag, (0.12, 0.006, 0.035), (cx, 4.068, 1.35), WHITE_MAT))

print("di-signs objects:", len(objs), [o.name for o in objs])

# ---------- lighting (SPEC §2) ----------
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

# 室内预览补光 (仅预览, 不导出): 一盏点光源在牌前方上方
ld = bpy.data.lights.new("Preview_Point", type='POINT')
ld.energy = 300.0
ld.shadow_soft_size = 0.5
lo = bpy.data.objects.new("Preview_Point", ld)
bpy.context.collection.objects.link(lo)
lo.location = (0.0, 1.5, 5.0)

# ---------- camera: 南侧稍近处广角, 一次看清 8 块牌 ----------
# 北墙牌与编号牌朝南, 东墙牌朝西; 机位放正南, 东墙牌不再斜切成窄条
# 视轴对准最西编号牌 (-6) 与东墙牌 (7.97) 的角平分线, 22mm 刚好框住 8 块牌
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 22.0
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera = cam
cam.location = (0.0, -8.0, 3.2)
target = Vector((2.0, 4.0, 1.9))
cam.rotation_mode = 'QUATERNION'
cam.rotation_quaternion = (target - cam.location).to_track_quat('-Z', 'Y')

# ---------- render settings (仅留给 Actions 渲染用, 本地不执行渲染) ----------
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
assert len(imported) == len(objs), "glb reimport failed: expected %d objects, got %d" % (len(objs), len(imported))
# 回读材质颜色自查: 程序化噪波混色不能把 GLB 底色带偏
for ob in imported:
    for slot in ob.material_slots:
        m = slot.material
        if m and m.use_nodes:
            print("GLB material:", m.name,
                  "base:", tuple(round(v, 3) for v in
                                 m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value[:3]))
# 删掉回读的副本, 恢复干净场景
bpy.ops.object.select_all(action='DESELECT')
for ob in imported:
    ob.select_set(True)
bpy.ops.object.delete()

# 本地不渲染 (预览图走 GitHub Actions); 保存最终工程
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("DONE di-signs")
