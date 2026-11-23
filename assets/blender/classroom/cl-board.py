# cl-board v2: 教室内部 - 讲台黑板 (Blender 4.2, bpy)
# 纹理已固化进脚本（见文件末尾 _apply_pbr_textures，2026-11-23）：
# 染色贴图 assets/blender/tex/ + 原图 assets/external/，材质节点直连
# Base Color/Roughness/Normal；重跑不再丢贴图。
# 局部坐标: 房间中心原点, x=长 9.68m (-4.84~+4.84), y=宽 7.26m (-3.63~+3.63), z 0-3.0m
# 黑板墙在 x=-4.84 一侧. 只做黑板/展示板/讲台桌/台面小物, 不做桌椅/空调/灯具/窗户/地面墙面.
# v2 返工: 粉笔槽加板擦+多支粉笔; 讲台加抽屉缝线与把手; 黑板 Noise 粉笔灰渍,
# 墙面 Noise 混凝土纹, 讲台台面 Wood 程序化木纹.
import bpy
import math
import os
from mathutils import Vector

BASE = os.path.expanduser(
    "~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
BLEND_PATH = os.path.join(BASE, "assets/blender/classroom/cl-board.blend")
GLB_PATH = os.path.join(BASE, "assets/models/cl-board.glb")
PNG_PATH = os.path.join(BASE, "screenshots/blender/cl-board.png")
for p in (os.path.dirname(BLEND_PATH), os.path.dirname(GLB_PATH),
          os.path.dirname(PNG_PATH)):
    os.makedirs(p, exist_ok=True)

# ---------- 场景清空 ----------
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

PARTS = []  # 本件对象, 只导出这些


# ---------- 颜色: sRGB hex -> 线性 ----------
def _srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_lin(hexcolor):
    h = hexcolor.lstrip("#")
    return tuple(_srgb_to_linear(int(h[i:i + 2], 16) / 255.0)
                 for i in (0, 2, 4))


def make_mat(name, hexcolor, roughness=0.8, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*hex_lin(hexcolor), 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def add_noise_rough(mat, scale, r_min, r_max, detail=3.0):
    """Noise -> ColorRamp -> Roughness: 表面粗糙度起伏, 肉眼可见的斑驳."""
    nt = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nt["Principled BSDF"]
    tex = nt.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = scale
    tex.inputs["Detail"].default_value = detail
    tex.inputs["Roughness"].default_value = 0.7
    ramp = nt.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.15
    ramp.color_ramp.elements[0].color = (r_min, r_min, r_min, 1.0)
    ramp.color_ramp.elements[1].position = 0.85
    ramp.color_ramp.elements[1].color = (r_max, r_max, r_max, 1.0)
    links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Roughness"])
    return tex


def add_noise_color_mix(mat, scale, dust_hex, fac_strength):
    """Noise 混合少量浅色: 粉笔灰 / 混凝土斑驳, 只动 Base Color."""
    nt = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nt["Principled BSDF"]
    tex = nt.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = scale
    tex.inputs["Detail"].default_value = 4.0
    tex.inputs["Roughness"].default_value = 0.75
    mult = nt.new("ShaderNodeMath")
    mult.operation = "MULTIPLY"
    mult.inputs[1].default_value = fac_strength
    links.new(tex.outputs["Fac"], mult.inputs[0])
    mix = nt.new("ShaderNodeMixRGB")
    mix.blend_type = "MIX"
    mix.inputs[1].default_value = bsdf.inputs["Base Color"].default_value
    mix.inputs[2].default_value = (*hex_lin(dust_hex), 1.0)
    links.new(mult.outputs["Value"], mix.inputs["Fac"])
    links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    return tex


MAT_BOARD = make_mat("BoardGreen", "#2F3A33", roughness=0.55)   # 黑板墨绿 (SPEC §3)
add_noise_rough(MAT_BOARD, scale=18.0, r_min=0.35, r_max=0.85)
# 返工 2026-11-23: 粉笔灰 MixRGB 连进 Base Color 会导致 glTF 导出丢 baseColorFactor
# (Blender 4.2 导出器: Base Color 已链接时不写 factor, 黑板在 Godot 里变白)。
# 粉笔灰斑驳改走粗糙度起伏表现, Base Color 只留纯色默认值 #2F3A33。
MAT_FRAME = make_mat("FrameSilver", "#C0C5C9", roughness=0.35, metallic=0.6)
add_noise_rough(MAT_FRAME, scale=30.0, r_min=0.30, r_max=0.45)
MAT_WHITEBOARD = make_mat("WhiteBoard", "#DCDCDC", roughness=0.4)
add_noise_rough(MAT_WHITEBOARD, scale=22.0, r_min=0.35, r_max=0.50)
# 讲台台面: 程序化木纹 (Wave 条纹 + Noise 扰动), 不再是纯色
MAT_WOOD = make_mat("DeskWood", "#8B5A2B", roughness=0.6)
_nt = MAT_WOOD.node_tree.nodes
_links = MAT_WOOD.node_tree.links
_bsdf = _nt["Principled BSDF"]
_coord = _nt.new("ShaderNodeTexCoord")
_wave = _nt.new("ShaderNodeTexWave")
_wave.wave_type = "BANDS"
_wave.bands_direction = "X"
_wave.inputs["Scale"].default_value = 6.0
_wave.inputs["Distortion"].default_value = 8.0
_wave.inputs["Detail"].default_value = 4.0
_wave.inputs["Detail Scale"].default_value = 2.0
_links.new(_coord.outputs["Generated"], _wave.inputs["Vector"])
_wramp = _nt.new("ShaderNodeValToRGB")
_wramp.color_ramp.elements[0].position = 0.0
_wramp.color_ramp.elements[0].color = (*hex_lin("#5E3A1A"), 1.0)
_wramp.color_ramp.elements[1].position = 1.0
_wramp.color_ramp.elements[1].color = (*hex_lin("#B98A54"), 1.0)
# 中间再加一档中棕, 木纹层次更明显 (任务木色 #8B5A2B)
_mid = _wramp.color_ramp.elements.new(0.55)
_mid.color = (*hex_lin("#8B5A2B"), 1.0)
# 返工 2026-11-23: 木纹 Ramp 连进 Base Color 会导致 glTF 丢 baseColorFactor
# (导出器不写已链接 socket 的 factor, 讲台在 Godot 里变白)。木纹深浅改走
# 粗糙度起伏表现, Base Color 只留 make_mat 设好的纯色 #8B5A2B。
_links.new(_wave.outputs["Color"], _wramp.inputs["Fac"])
add_noise_rough(MAT_WOOD, scale=25.0, r_min=0.45, r_max=0.75)
add_noise_rough(MAT_WOOD, scale=60.0, r_min=0.40, r_max=0.80)  # 细划痕级粗糙度变化
MAT_DARK = make_mat("DeskDark", "#3F4348", roughness=0.7)       # 深灰侧板
add_noise_rough(MAT_DARK, scale=20.0, r_min=0.60, r_max=0.80)
MAT_DRAWER = make_mat("DrawerFront", "#4A4F54", roughness=0.65)  # 抽屉面板, 略浅于挡板
add_noise_rough(MAT_DRAWER, scale=20.0, r_min=0.55, r_max=0.75)
MAT_SEAM = make_mat("DrawerSeam", "#1E2124", roughness=0.9)     # 抽屉缝线
MAT_CHALKBOX = make_mat("ChalkBoxWhite", "#EDEDE8", roughness=0.8)
MAT_CHALKBOX_LID = make_mat("ChalkBoxLid", "#B9C4CC", roughness=0.6)
MAT_POINTER = make_mat("Pointer", "#8A4A3A", roughness=0.5)
MAT_HANDLE = make_mat("PointerHandle", "#333333", roughness=0.6)
MAT_CHALK = make_mat("ChalkWhite", "#F5F5F0", roughness=0.9)
MAT_CHALK_BLUE = make_mat("ChalkBlue", "#7A9AB5", roughness=0.9)
MAT_ERASER_WOOD = make_mat("EraserWood", "#A97C50", roughness=0.7)
MAT_ERASER_FELT = make_mat("EraserFelt", "#2E2E2E", roughness=1.0)


def box(name, loc, dims, mat, bevel=0.005):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    if bevel:
        mod = o.modifiers.new("Bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 2
    PARTS.append(o)
    return o


def cylinder(name, loc, radius, depth, mat, quat=None, rot_euler=None):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth,
                                        location=loc, vertices=24)
    o = bpy.context.active_object
    o.name = name
    if quat is not None:
        o.rotation_mode = "QUATERNION"
        o.rotation_quaternion = quat
    if rot_euler is not None:
        o.rotation_euler = rot_euler
    o.data.materials.append(mat)
    PARTS.append(o)
    return o


# ---------- 黑板: 3.6(y) x 1.2(高) m, 中心 (-4.80, 0, 1.6), 厚 0.04 ----------
box("Blackboard", (-4.80, 0, 1.6), (0.04, 3.6, 1.2), MAT_BOARD)

# 银灰边框 (框条略凸出板面)
box("BoardFrameTop", (-4.79, 0, 2.23), (0.05, 3.72, 0.06), MAT_FRAME)
box("BoardFrameBottom", (-4.79, 0, 0.97), (0.05, 3.72, 0.06), MAT_FRAME)
box("BoardFrameLeft", (-4.79, -1.83, 1.6), (0.05, 0.06, 1.32), MAT_FRAME)
box("BoardFrameRight", (-4.79, 1.83, 1.6), (0.05, 0.06, 1.32), MAT_FRAME)

# 底部粉笔槽: 托板 + 前沿小唇, 槽深约 0.05m
box("ChalkTray", (-4.78, 0, 0.99), (0.08, 3.6, 0.02), MAT_FRAME)
box("ChalkTrayLip", (-4.745, 0, 1.005), (0.02, 3.6, 0.045), MAT_FRAME)
# 槽里粉笔: 两支白 + 一支蓝 + 一支短的断粉笔
for i, (y, mat, length) in enumerate((
        (-0.8, MAT_CHALK, 0.09), (0.8, MAT_CHALK, 0.09),
        (1.25, MAT_CHALK_BLUE, 0.09), (1.55, MAT_CHALK, 0.045))):
    q = Vector((0.0, 1.0, 0.0)).to_track_quat("Z", "Y")
    cylinder("Chalk%d" % i, (-4.76, y, 1.012), 0.008, length, mat, quat=q)
# 板擦: 放在粉笔槽右段, 木托 + 黑毛毡底
box("EraserFelt", (-4.76, -1.45, 1.008), (0.05, 0.17, 0.012), MAT_ERASER_FELT)
box("EraserWood", (-4.76, -1.45, 1.02), (0.045, 0.16, 0.022), MAT_ERASER_WOOD, bevel=0.004)

# ---------- 展示板: 黑板左右各一, 1.2 x 1.2m, 浅灰 ----------
for side, y in (("Left", -2.55), ("Right", 2.55)):
    box("WhiteBoard%sBack" % side, (-4.83, y, 1.6),
        (0.02, 1.28, 1.28), MAT_FRAME)
    box("WhiteBoard%s" % side, (-4.815, y, 1.6),
        (0.03, 1.2, 1.2), MAT_WHITEBOARD)

# ---------- 讲台桌: 1.8(y) x 0.6(x) x 1.1(高) m, 中心 (-4.0, 0, 0) ----------
# 木台面 (带程序化木纹), 小倒角
box("DeskTop", (-4.0, 0, 1.075), (0.62, 1.84, 0.05), MAT_WOOD, bevel=0.012)
# 深灰侧板 (两端) + 正面挡板 (朝学生一侧 +x)
box("DeskSideL", (-4.0, -0.845, 0.535), (0.56, 0.05, 1.03), MAT_DARK)
box("DeskSideR", (-4.0, 0.845, 0.535), (0.56, 0.05, 1.03), MAT_DARK)
box("DeskFront", (-3.72, 0, 0.535), (0.05, 1.64, 1.03), MAT_DARK)
# 底座踢脚
box("DeskPlinth", (-4.0, 0, 0.025), (0.58, 1.8, 0.05), MAT_DARK)

# ---------- 讲台抽屉: 正面两扇抽屉面板 + 缝线 + 把手 ----------
# 挡板正面 x=-3.695; 抽屉面板略凸出, 中间留 0.04 缝
for i, y in enumerate((-0.41, 0.41)):
    box("DrawerFront%d" % i, (-3.688, y, 0.72),
        (0.014, 0.78, 0.36), MAT_DRAWER, bevel=0.004)
    # 缝线: 抽屉面板上下沿的细黑线 (0.008 厚, 不倒角)
    box("DrawerSeamTop%d" % i, (-3.694, y, 0.905),
        (0.008, 0.80, 0.015), MAT_SEAM, bevel=None)
    box("DrawerSeamBottom%d" % i, (-3.694, y, 0.535),
        (0.008, 0.80, 0.015), MAT_SEAM, bevel=None)
    # 把手: 横向金属小横杆 + 两端小支座
    cylinder("DrawerHandle%d" % i, (-3.672, y, 0.72), 0.011, 0.20,
             MAT_FRAME, rot_euler=(math.radians(90), 0, 0))
    for dy in (-0.09, 0.09):
        box("DrawerHandleMount%d_%s" % (i, "L" if dy < 0 else "R"),
            (-3.68, y + dy, 0.72), (0.018, 0.02, 0.02), MAT_DARK)
# 抽屉区下方横向缝线 (与下挡板分界)
box("DrawerSeamLower", (-3.694, 0, 0.50), (0.008, 1.64, 0.015), MAT_SEAM,
    bevel=None)

# ---------- 台面小物 ----------
# 粉笔盒 (白盒 + 浅灰盖)
box("ChalkBox", (-4.15, 0.55, 1.1275), (0.10, 0.20, 0.055), MAT_CHALKBOX)
box("ChalkBoxLid", (-4.15, 0.55, 1.161), (0.105, 0.205, 0.012),
    MAT_CHALKBOX_LID)
# 教鞭: 细圆柱长 0.85m, 斜放在台面上, 一端带手柄
pointer_dir = Vector((math.sin(math.radians(20)), math.cos(math.radians(20)), 0))
pointer_center = Vector((-3.95, -0.5, 1.112))
q = pointer_dir.to_track_quat("Z", "Y")
cylinder("Pointer", tuple(pointer_center), 0.008, 0.85, MAT_POINTER, quat=q)
handle_center = pointer_center - pointer_dir * (0.85 / 2 - 0.06)
cylinder("PointerHandle", tuple(handle_center), 0.014, 0.12, MAT_HANDLE, quat=q)

# ---------- 预览专用示意 (不导出): 地面 + 黑板墙 (墙面带 Noise 混凝土纹) ----------
def preview_only(name, loc, dims, hexcolor, roughness=0.9):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    mat = make_mat("Preview" + name, hexcolor, roughness)
    o.data.materials.append(mat)
    return o, mat


preview_only("PREVIEW_Floor", (0, 0, -0.011), (9.68, 7.26, 0.02), "#D8D2C4")
_, wall_mat = preview_only("PREVIEW_WallBoard", (-4.845, 0, 1.5),
                           (0.01, 7.26, 3.0), "#F3E9D2")
add_noise_rough(wall_mat, scale=12.0, r_min=0.8, r_max=1.0)
add_noise_color_mix(wall_mat, scale=9.0, dust_hex="#DDD2BC", fac_strength=0.3)

# ---------- 光照 (SPEC §2): 太阳 3.5 从西南来, 世界淡蓝 ----------
sun_data = bpy.data.lights.new("Sun", type="SUN")
sun_data.energy = 3.5
sun_data.use_shadow = True
sun = bpy.data.objects.new("Sun", sun_data)
bpy.context.collection.objects.link(sun)
light_dir = Vector((math.cos(math.radians(50)) / math.sqrt(2),
                    math.cos(math.radians(50)) / math.sqrt(2),
                    -math.sin(math.radians(50))))
sun.rotation_euler = light_dir.to_track_quat("-Z", "Y").to_euler()
sun.location = (-5, -5, 8)

world = bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.65, 0.78, 0.88, 1.0)
bg.inputs["Strength"].default_value = 1.0

# ---------- 预览相机: 教室后方看黑板墙 (斜拍, 让粉笔槽从讲台侧边露出来) ----------
cam_data = bpy.data.cameras.new("PreviewCam")
cam_data.lens = 28
cam = bpy.data.objects.new("PreviewCam", cam_data)
bpy.context.collection.objects.link(cam)
cam.location = (0.0, 3.0, 1.35)
target = Vector((-4.7, 0.4, 1.05))
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
bpy.context.scene.camera = cam

# ---- PBR 贴图固化 (2026-11-23)：把上一轮挂在 .blend 上的外部贴图写进脚本 ----
# color 图：assets/blender/tex/ 里的染色图（已按 SPEC §3 目标色染色，黑板
# 墨绿 #2F3A33 等）；rough/normal 图：assets/external/ 原图（CC0）。
# 节点只许 TexCoord→Mapping→Image Texture 直连 BSDF，不加 Hue/Sat/Mix，
# 否则 glTF 导出器不认。Base Color 默认值须置白、Roughness 置 1.0（贴图
# 本身带颜色与粗糙度），否则导出器会把旧纯色写成 baseColorFactor/
# roughnessFactor 与贴图二次相乘；Metallic 保持脚本原值。
# 没有 UV 的网格补 Smart UV Project（已有 UV 的不动）。
TEX_DIR = os.path.join(BASE, "assets/blender/tex")
EXT_DIR = os.path.join(BASE, "assets/external")
# 材质名: (tex/ 染色 color 图, external rough 图, external normal 图, Mapping 缩放)
PBR_TEXTURES = {
    "BoardGreen": ("white_stucco__2F3A33.jpg",
        "polyhaven/white_stucco_rough_1k.jpg",
        "polyhaven/white_stucco_nor_gl_1k.jpg", (2.0, 1.0)),
    "FrameSilver": ("white_stucco__C0C5C9.jpg",
        "polyhaven/white_stucco_rough_1k.jpg",
        "polyhaven/white_stucco_nor_gl_1k.jpg", (1.0, 1.0)),
    "ChalkWhite": ("Plaster001__F5F5F0.jpg",
        "ambientcg/Plaster001/Plaster001_1K-JPG_Roughness.jpg",
        "ambientcg/Plaster001/Plaster001_1K-JPG_NormalGL.jpg", (1.0, 1.0)),
    "ChalkBlue": ("white_stucco__7A9AB5.jpg",
        "polyhaven/white_stucco_rough_1k.jpg",
        "polyhaven/white_stucco_nor_gl_1k.jpg", (1.0, 1.0)),
    "EraserFelt": ("concrete_wall_007__2E2E2E.jpg",
        "polyhaven/concrete_wall_007_rough_1k.jpg",
        "polyhaven/concrete_wall_007_nor_gl_1k.jpg", (1.0, 1.0)),
    "EraserWood": ("WoodFloor051__A97C50.jpg",
        "ambientcg/WoodFloor051/WoodFloor051_1K-JPG_Roughness.jpg",
        "ambientcg/WoodFloor051/WoodFloor051_1K-JPG_NormalGL.jpg", (1.0, 1.0)),
    "WhiteBoard": ("Plaster001__DCDCDC.jpg",
        "ambientcg/Plaster001/Plaster001_1K-JPG_Roughness.jpg",
        "ambientcg/Plaster001/Plaster001_1K-JPG_NormalGL.jpg", (1.0, 1.0)),
    "DeskWood": ("wooden_floor_01__8B5A2B.jpg",
        "polyhaven/wooden_floor_01_rough_1k.jpg",
        "polyhaven/wooden_floor_01_nor_gl_1k.jpg", (1.0, 1.0)),
    "DeskDark": ("blue_metal_plate__3F4348.jpg",
        "polyhaven/blue_metal_plate_rough_1k.jpg",
        "polyhaven/blue_metal_plate_nor_gl_1k.jpg", (1.0, 1.0)),
    "DrawerFront": ("blue_metal_plate__4A4F54.jpg",
        "polyhaven/blue_metal_plate_rough_1k.jpg",
        "polyhaven/blue_metal_plate_nor_gl_1k.jpg", (1.0, 1.0)),
    "DrawerSeam": ("concrete_wall_007__1E2124.jpg",
        "polyhaven/concrete_wall_007_rough_1k.jpg",
        "polyhaven/concrete_wall_007_nor_gl_1k.jpg", (1.0, 1.0)),
    "ChalkBoxWhite": ("Plaster001__EDEDE8.jpg",
        "ambientcg/Plaster001/Plaster001_1K-JPG_Roughness.jpg",
        "ambientcg/Plaster001/Plaster001_1K-JPG_NormalGL.jpg", (1.0, 1.0)),
    "ChalkBoxLid": ("white_stucco__B9C4CC.jpg",
        "polyhaven/white_stucco_rough_1k.jpg",
        "polyhaven/white_stucco_nor_gl_1k.jpg", (1.0, 1.0)),
    "Pointer": ("WoodFloor051__8A4A3A.jpg",
        "ambientcg/WoodFloor051/WoodFloor051_1K-JPG_Roughness.jpg",
        "ambientcg/WoodFloor051/WoodFloor051_1K-JPG_NormalGL.jpg", (1.0, 1.0)),
    "PointerHandle": ("concrete_wall_007__333333.jpg",
        "polyhaven/concrete_wall_007_rough_1k.jpg",
        "polyhaven/concrete_wall_007_nor_gl_1k.jpg", (1.0, 1.0)),
}


_IMG_CACHE = {}


def _pbr_load_image(abs_path, colorspace):
    # 同一文件只加载一次：filepath 改成相对路径后 check_existing 会按路径
    # 字符串比对失效、重复建 .001 副本，故用自带缓存去重
    img = _IMG_CACHE.get(abs_path)
    if img is None:
        img = bpy.data.images.load(abs_path, check_existing=True)
        img.colorspace_settings.name = colorspace
        # 存相对路径进 .blend（// 相对 .blend 所在目录），仓库检出后仍能找到
        rel = os.path.relpath(abs_path, os.path.dirname(BLEND_PATH)).replace(os.sep, "/")
        img.filepath = "//" + rel
        _IMG_CACHE[abs_path] = img
    return img


def _apply_pbr_textures():
    for mat_name, (color_f, rough_f, normal_f, scale) in PBR_TEXTURES.items():
        mat = bpy.data.materials.get(mat_name)
        if mat is None:
            print("PBR SKIP missing material:", mat_name)
            continue
        nt = mat.node_tree
        bsdf = nt.nodes["Principled BSDF"]
        # 清掉旧程序化节点，只留 BSDF 与 Output
        for node in list(nt.nodes):
            if node.type not in ("BSDF_PRINCIPLED", "OUTPUT_MATERIAL"):
                nt.nodes.remove(node)
        bsdf.inputs["Base Color"].default_value = (1.0, 1.0, 1.0, 1.0)
        bsdf.inputs["Roughness"].default_value = 1.0
        texcoord = nt.nodes.new("ShaderNodeTexCoord")
        mapping = nt.nodes.new("ShaderNodeMapping")
        mapping.inputs["Scale"].default_value = (scale[0], scale[1], 1.0)
        nt.links.new(texcoord.outputs["UV"], mapping.inputs["Vector"])
        tex_c = nt.nodes.new("ShaderNodeTexImage")
        tex_c.image = _pbr_load_image(os.path.join(TEX_DIR, color_f), "sRGB")
        nt.links.new(mapping.outputs["Vector"], tex_c.inputs["Vector"])
        nt.links.new(tex_c.outputs["Color"], bsdf.inputs["Base Color"])
        tex_r = nt.nodes.new("ShaderNodeTexImage")
        tex_r.image = _pbr_load_image(os.path.join(EXT_DIR, rough_f), "Non-Color")
        nt.links.new(mapping.outputs["Vector"], tex_r.inputs["Vector"])
        nt.links.new(tex_r.outputs["Color"], bsdf.inputs["Roughness"])
        tex_n = nt.nodes.new("ShaderNodeTexImage")
        tex_n.image = _pbr_load_image(os.path.join(EXT_DIR, normal_f), "Non-Color")
        nmap = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(mapping.outputs["Vector"], tex_n.inputs["Vector"])
        nt.links.new(tex_n.outputs["Color"], nmap.inputs["Color"])
        nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
        print("PBR textured:", mat_name, color_f, "scale", scale)


def _ensure_uvs(objs):
    """没有 UV 的网格补 Smart UV Project（已有 UV 的不动）。"""
    todo = []
    seen = set()
    for ob in objs:
        if ob.type != "MESH":
            continue
        if id(ob.data) in seen:
            continue
        seen.add(id(ob.data))
        if len(ob.data.uv_layers) == 0:
            todo.append(ob)
    if not todo:
        print("UV OK: all meshes have UVs")
        return
    bpy.ops.object.select_all(action="DESELECT")
    for ob in todo:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = todo[0]
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66.0), island_margin=0.02)
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    print("UV smart-projected:", len(todo), [o.name for o in todo])


_apply_pbr_textures()
_ensure_uvs(PARTS)

# ---------- 存 .blend ----------
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)

# ---------- 导出 .glb (只选本件对象) ----------
bpy.ops.object.select_all(action="DESELECT")
for o in PARTS:
    o.select_set(True)
bpy.context.view_layer.objects.active = PARTS[0]
bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format="GLB",
                           use_selection=True, export_apply=True)
print("EXPORTED", GLB_PATH, "objects:", len(PARTS))

# ---------- 渲染预览 (本地默认跳过, 走 GitHub Actions; 置 CL_BOARD_RENDER=1 才渲染) ----------
if os.environ.get("CL_BOARD_RENDER") == "1":
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 640
    scene.render.resolution_y = 360
    scene.render.resolution_percentage = 100
    scene.eevee.taa_render_samples = 16
    scene.render.filepath = PNG_PATH
    scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)
    print("RENDERED", PNG_PATH)
else:
    print("Render skipped locally (set CL_BOARD_RENDER=1 to render)")

# ---------- 回读 glb 验证 ----------
before = set(bpy.data.objects.keys())
bpy.ops.import_scene.gltf(filepath=GLB_PATH)
imported = [o for o in bpy.data.objects.keys() if o not in before]
print("GLB REIMPORT OK, imported objects:", len(imported))

# 删 Blender 备份
blend1 = BLEND_PATH + "1"
if os.path.exists(blend1):
    os.remove(blend1)
    print("REMOVED", blend1)

print("DONE cl-board")
