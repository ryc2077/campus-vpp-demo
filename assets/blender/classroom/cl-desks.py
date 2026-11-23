# cl-desks v2: 教室内部 - 课桌椅 (6列 x 8排 = 48套)
# 纹理已固化进脚本（见文件末尾 _apply_pbr_textures，2026-11-23）：
# 染色贴图 assets/blender/tex/ + 原图 assets/external/，材质节点直连
# Base Color/Roughness/Normal；重跑不再丢贴图。
# 局部坐标: 房间中心原点, x=长 9.68m (-4.84~+4.84), y=宽 7.26m (-3.63~+3.63), z 0~3.0m
# 黑板墙在 x=-4.84 一侧, 学生面向 -x 方向坐
# v2 重做 (用户反馈: 旧版凳子像平板贴地): 按真实课桌椅结构
# v2.2 相机: 前排左前方 3/4 侧视角、贴近第一组桌椅 (见相机段注释)
# v2.3 原点修正 (实测发现): join 后原点留在首个零件处 (桌面 z=0.735 /
#   椅面 z=0.435), 复制时 location z=0 会把整套压到地下 0.735/0.435m,
#   桌腿椅腿全埋进地板、桌面椅面贴地; 必须把原点移回世界原点 (几何不动)
# 课桌 0.6(x) x 0.45(y) x 0.75(高)m: 桌面木面 #C8A06A 厚 0.03 (顶面 z=0.75)
#   + 4 条桌腿 #424A52 0.04x0.04, 从地面立到桌面底面 (z 0~0.72)
#   + 桌腿间下部横撑 1 根 (前侧, z=0.15)
# 椅子 0.4 x 0.4: 椅面木色 #7A4A2B 厚 0.03 (顶面 z=0.45)
#   + 4 条椅腿 0.03x0.03, 从地面立到椅面底面 (z 0~0.42)
#   + 靠背背板 0.4 宽 x 0.4 高 x 0.02 厚, 从椅面向上立起, 顶到 z=0.85, 向后 (+x) 微倾 5 度
#   + 2 根背杆 (与靠背同倾 5 度, 椅面底到背顶)
# 排布照旧版: 6 列 y 中心 -2.8/-1.8/-0.8/+0.8/+1.8/+2.8; 8 排 x 中心 -3.04 起间距 1.0m 至 +3.96
import bpy
import math
import os
from mathutils import Vector

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
SCRIPT_DIR = os.path.join(BASE, "assets/blender/classroom")
MODEL_PATH = os.path.join(BASE, "assets/models/cl-desks.glb")
BLEND_PATH = os.path.join(SCRIPT_DIR, "cl-desks.blend")
PREVIEW_PATH = os.path.join(BASE, "screenshots/blender/cl-desks.png")
for p in (SCRIPT_DIR, os.path.dirname(MODEL_PATH), os.path.dirname(PREVIEW_PATH)):
    os.makedirs(p, exist_ok=True)

# ---------- 场景清理 ----------
bpy.ops.wm.read_factory_settings(use_empty=True)

# ---------- sRGB 十六进制 -> 线性 (Principled Base Color 必须是线性值) ----------
def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def hex_to_linear(h):
    h = h.lstrip("#")
    r = int(h[0:2], 16) / 255.0
    g = int(h[2:4], 16) / 255.0
    b = int(h[4:6], 16) / 255.0
    return (srgb_to_linear(r), srgb_to_linear(g), srgb_to_linear(b), 1.0)

def make_material(name, hex_color, roughness=0.7):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = hex_to_linear(hex_color)
    bsdf.inputs["Roughness"].default_value = roughness
    return mat

# ---------- 程序化材质 (全局新标准, 红线: 没有任何一个面是全平的) ----------
# 木纹: 拉伸噪波模拟木纹 (纹理走向沿 X, 深浅不均 + 粗糙度变化 + 轻微凹凸)
# 金属腿: 噪波拉丝, 粗糙度轻微变化; 只用程序化节点, 不用贴图
def make_wood_material(name, base_hex, dark_hex, light_hex, roughness=0.55,
                       grain_scale=(1.5, 6.0, 1.5)):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Metallic"].default_value = 0.0
    # 返工 2026-11-23: 木纹 Ramp 连进 Base Color 会导致 glTF 丢 baseColorFactor,
    # Base Color 只留纯色默认值 (木纹深浅改走粗糙度/Bump)。
    bsdf.inputs["Base Color"].default_value = hex_to_linear(base_hex)
    texcoord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = grain_scale
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 1.0
    noise.inputs["Detail"].default_value = 4.0
    noise.inputs["Roughness"].default_value = 0.7
    noise.inputs["Distortion"].default_value = 0.4
    # 颜色: 深 -> 本色 -> 浅, 三档木纹深浅
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.30
    ramp.color_ramp.elements[0].color = hex_to_linear(dark_hex)
    ramp.color_ramp.elements[1].position = 0.72
    ramp.color_ramp.elements[1].color = hex_to_linear(light_hex)
    mid = ramp.color_ramp.elements.new(0.52)
    mid.color = hex_to_linear(base_hex)
    # 粗糙度: 同一噪波映射到灰度区间, 木面粗糙度不均
    lo = max(0.05, roughness - 0.20)
    hi = min(1.0, roughness + 0.15)
    rramp = nt.nodes.new("ShaderNodeValToRGB")
    rramp.color_ramp.elements[0].position = 0.0
    rramp.color_ramp.elements[0].color = (lo, lo, lo, 1.0)
    rramp.color_ramp.elements[1].position = 1.0
    rramp.color_ramp.elements[1].color = (hi, hi, hi, 1.0)
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.05
    bump.inputs["Distance"].default_value = 0.02
    nt.links.new(texcoord.outputs["Generated"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(noise.outputs["Fac"], rramp.inputs["Fac"])
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(rramp.outputs["Color"], bsdf.inputs["Roughness"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat

def make_metal_material(name, base_hex, dark_hex, light_hex, roughness=0.45):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    # 返工 2026-11-23: 同上, Base Color 只留纯色默认值, 不连程序化 Ramp。
    bsdf.inputs["Base Color"].default_value = hex_to_linear(base_hex)
    bsdf.inputs["Metallic"].default_value = 0.75
    # 拉丝: 噪波沿腿长方向 (Z) 拉伸, 横向变化快、纵向变化慢
    texcoord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (12.0, 12.0, 1.5)
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 1.0
    noise.inputs["Detail"].default_value = 3.0
    noise.inputs["Roughness"].default_value = 0.7
    noise.inputs["Distortion"].default_value = 0.1
    # 颜色只做轻微深浅变化 (金属腿不是均匀纯色)
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.30
    ramp.color_ramp.elements[0].color = hex_to_linear(dark_hex)
    ramp.color_ramp.elements[1].position = 0.72
    ramp.color_ramp.elements[1].color = hex_to_linear(light_hex)
    mid = ramp.color_ramp.elements.new(0.52)
    mid.color = hex_to_linear(base_hex)
    lo = max(0.05, roughness - 0.10)
    hi = min(1.0, roughness + 0.10)
    rramp = nt.nodes.new("ShaderNodeValToRGB")
    rramp.color_ramp.elements[0].position = 0.0
    rramp.color_ramp.elements[0].color = (lo, lo, lo, 1.0)
    rramp.color_ramp.elements[1].position = 1.0
    rramp.color_ramp.elements[1].color = (hi, hi, hi, 1.0)
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.01
    bump.inputs["Distance"].default_value = 0.01
    nt.links.new(texcoord.outputs["Generated"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(noise.outputs["Fac"], rramp.inputs["Fac"])
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    # 返工 2026-11-23: 金属拉丝 Ramp 不连 Base Color (否则 glTF 丢 baseColorFactor)。
    nt.links.new(rramp.outputs["Color"], bsdf.inputs["Roughness"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat

# 桌面木纹 #C8A06A (深 #8A5F33 / 浅 #DDB67F), 椅面木纹 #7A4A2B (深 #54301A / 浅 #96683F)
MAT_WOOD = make_wood_material("desk_wood", "#C8A06A", "#8A5F33", "#DDB67F", 0.55)
MAT_CHAIR = make_wood_material("chair_wood", "#7A4A2B", "#54301A", "#96683F", 0.60)
# 桌腿/椅腿/横撑: 深灰金属 #424A52 (深 #363D44 / 浅 #565E66), 轻微拉丝粗糙度变化
MAT_LEG = make_metal_material("leg_metal", "#424A52", "#363D44", "#565E66", 0.45)

# ---------- 小工具 ----------
def add_box(name, loc, dims, mat, rot_y_deg=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.dimensions = dims
    if rot_y_deg:
        # 绕自身中心转 Y 轴 (靠背/背杆向后 +x 微倾), 再烘进网格
        obj.rotation_euler = (0.0, math.radians(rot_y_deg), 0.0)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    if mat:
        obj.data.materials.append(mat)
    return obj

def join_objects(objs, name):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    joined = bpy.context.active_object
    joined.name = name
    return joined

def add_bevel(obj, width=0.008, segments=2):
    mod = obj.modifiers.new("bevel", "BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)

def reset_origin_to_world(obj):
    # join 后原点在首个零件处; 移回世界原点, 几何在世界坐标里不动,
    # 之后复制件 location=(x, y, 0) 才不会把整套压进地下
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    print(obj.name, "origin reset, location now:", tuple(obj.location))

# ---------- 课桌原型 (中心在原点, 桌面顶 z=0.75) ----------
desk_parts = []
# 桌面: 0.6 x 0.45 x 0.03, 顶面 z=0.75 (中心 z=0.735)
desk_parts.append(add_box("desk_top", (0, 0, 0.735), (0.6, 0.45, 0.03), MAT_WOOD))
# 4 条桌腿: 0.04 x 0.04, 从地面立到桌面底面 z=0.72 (高 0.72, 中心 z=0.36)
for sx in (-1, 1):
    for sy in (-1, 1):
        desk_parts.append(add_box(
            "desk_leg",
            (sx * 0.25, sy * 0.175, 0.36),
            (0.04, 0.04, 0.72), MAT_LEG))
# 下部横撑 1 根: 前侧 (-x, 黑板一侧) 两条桌腿之间, 沿 y 向,
#   0.04 x 0.39 x 0.04, 中心 z=0.15 (离地 0.13~0.17, 两端搭在桌腿上)
desk_parts.append(add_box("desk_brace", (-0.25, 0, 0.15), (0.04, 0.39, 0.04), MAT_LEG))
desk_proto = join_objects(desk_parts, "desk_proto")
add_bevel(desk_proto, width=0.008, segments=2)
reset_origin_to_world(desk_proto)

# ---------- 椅子原型 (中心在原点, 椅背在 +x 一侧, 椅面顶 z=0.45, 背顶 z=0.85) ----------
chair_parts = []
# 椅面: 0.4 x 0.4 x 0.03, 顶面 z=0.45 (中心 z=0.435)
chair_parts.append(add_box("chair_seat", (0, 0, 0.435), (0.4, 0.4, 0.03), MAT_CHAIR))
# 4 条椅腿: 0.03 x 0.03, 从地面立到椅面底面 z=0.42 (高 0.42, 中心 z=0.21)
for sx in (-1, 1):
    for sy in (-1, 1):
        chair_parts.append(add_box(
            "chair_leg",
            (sx * 0.165, sy * 0.165, 0.21),
            (0.03, 0.03, 0.42), MAT_LEG))
# 靠背背板: 0.02(x) x 0.4(y) x 0.40(z), 底 z=0.45 / 顶 z=0.85,
#   中心 (0.19, 0, 0.65), 向后 (+x) 微倾 5 度 (顶端约 +0.017m)
chair_parts.append(add_box("chair_back", (0.19, 0, 0.65), (0.02, 0.4, 0.40),
                           MAT_CHAIR, rot_y_deg=5.0))
# 2 根背杆: 0.03 x 0.03, 从椅面底 z=0.42 立到背顶 z=0.85 (高 0.43),
#   位于背板后侧 (+x), y=+-0.15, 与靠背同倾 5 度
for sy in (-1, 1):
    chair_parts.append(add_box(
        "chair_back_post",
        (0.205, sy * 0.15, 0.635),
        (0.03, 0.03, 0.43), MAT_CHAIR, rot_y_deg=5.0))
chair_proto = join_objects(chair_parts, "chair_proto")
add_bevel(chair_proto, width=0.008, segments=2)
reset_origin_to_world(chair_proto)

# ---------- 排布 (照旧版, 不改) ----------
# v2.4 间隙修复 (2026-11-22): 整组沿 x 向黑板方向 (负 x) 平移 0.15m,
#   只改本整体偏移常数, 不逐个改桌椅坐标. 移前最后一排椅背 x=4.748,
#   离东墙内表面 x=4.765 仅 1.7cm; 移后约 4.598, 间隙约 16.7cm.
#   移前最近桌沿离讲台桌前沿 (x=-3.695) 0.355m; 移后约 0.205m.
GROUP_DX = -0.15
COL_Y = [-2.8, -1.8, -0.8, 0.8, 1.8, 2.8]
ROW_X = [-3.04 + GROUP_DX + i * 1.0 for i in range(8)]
# 椅子在桌子 +x 一侧 (学生面向 -x): 桌后沿 +0.05 间隙 + 椅深/2
CHAIR_DX = 0.3 + 0.05 + 0.2  # = 0.55

desks = []
chairs = []
for r, x in enumerate(ROW_X):
    for c, y in enumerate(COL_Y):
        d = desk_proto.copy()
        d.data = desk_proto.data  # 共享网格
        d.name = "desk_r%d_c%d" % (r + 1, c + 1)
        d.location = (x, y, 0)
        bpy.context.collection.objects.link(d)
        desks.append(d)

        ch = chair_proto.copy()
        ch.data = chair_proto.data
        ch.name = "chair_r%d_c%d" % (r + 1, c + 1)
        ch.location = (x + CHAIR_DX, y, 0)
        bpy.context.collection.objects.link(ch)
        chairs.append(ch)

# 删原型 (只留 48+48 个实例)
bpy.data.objects.remove(desk_proto, do_unlink=True)
bpy.data.objects.remove(chair_proto, do_unlink=True)

print("desks:", len(desks), "chairs:", len(chairs))
print("GROUP_DX:", GROUP_DX)
print("row_x:", ROW_X)
print("col_y:", COL_Y)
print("desk top z=0.75, legs 0~0.72; chair seat top z=0.45, legs 0~0.42, back top z=0.85 tilt 5deg")

# 几何自检 (v2.3 教训: 原点错会把桌腿埋进地下, 渲染图上桌面贴地):
# 桌子世界 z 范围应为 0~0.75, 椅子 0~0.85, 否则直接报错停住
def world_z_range(obj):
    zs = [(obj.matrix_world @ Vector(c)).z for c in obj.bound_box]
    return min(zs), max(zs)
_dz = world_z_range(desks[0])
_cz = world_z_range(chairs[0])
print("desk world z range:", _dz, "chair world z range:", _cz)
assert abs(_dz[0]) < 0.01 and abs(_dz[1] - 0.75) < 0.01, "desk z range wrong: %s" % (_dz,)
assert abs(_cz[0]) < 0.01 and abs(_cz[1] - 0.85) < 0.02, "chair z range wrong: %s" % (_cz,)

# ---- PBR 贴图固化 (2026-11-23)：把上一轮挂在 .blend 上的外部贴图写进脚本 ----
# color 图：assets/blender/tex/ 里的染色图（已按 SPEC §3 目标色染色）；
# rough/normal 图：assets/external/ 原图（CC0）。
# 节点只许 TexCoord→Mapping→Image Texture 直连 BSDF，不加 Hue/Sat/Mix，
# 否则 glTF 导出器不认。Base Color 默认值须置白、Roughness 置 1.0（贴图
# 本身带颜色与粗糙度），否则导出器会把旧纯色写成 baseColorFactor/
# roughnessFactor 与贴图二次相乘；Metallic 保持脚本原值。
# 没有 UV 的网格补 Smart UV Project（已有 UV 的不动）。
TEX_DIR = os.path.join(BASE, "assets/blender/tex")
EXT_DIR = os.path.join(BASE, "assets/external")
# 材质名: (tex/ 染色 color 图, external rough 图, external normal 图, Mapping 缩放)
PBR_TEXTURES = {
    "desk_wood": ("wooden_floor_01__C8A06A.jpg",
        "polyhaven/wooden_floor_01_rough_1k.jpg",
        "polyhaven/wooden_floor_01_nor_gl_1k.jpg", (1.0, 1.0)),
    "leg_metal": ("blue_metal_plate__424A52.jpg",
        "polyhaven/blue_metal_plate_rough_1k.jpg",
        "polyhaven/blue_metal_plate_nor_gl_1k.jpg", (1.0, 1.0)),
    "chair_wood": ("WoodFloor051__7A4A2B.jpg",
        "ambientcg/WoodFloor051/WoodFloor051_1K-JPG_Roughness.jpg",
        "ambientcg/WoodFloor051/WoodFloor051_1K-JPG_NormalGL.jpg", (1.0, 1.0)),
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
_ensure_uvs(desks + chairs)

# ---------- 存 .blend ----------
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)

# ---------- 导出 .glb (只选本件对象) ----------
bpy.ops.object.select_all(action="DESELECT")
for o in desks + chairs:
    o.select_set(True)
bpy.ops.export_scene.gltf(
    filepath=MODEL_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
)

# ---------- 回读校验 (应为 96 个对象) ----------
bpy.ops.import_scene.gltf(filepath=MODEL_PATH)
imported = [o for o in bpy.context.selected_objects]
print("gltf reimport objects:", len(imported))
assert len(imported) == 96, "glTF reimport expected 96 objects, got %d" % len(imported)
# 删回读的临时对象
bpy.ops.object.delete()

# ---------- 预览: 光照/世界/相机/示意地面墙面 (不导出) ----------
# 拆分模式: 环境变量 CL_DESKS_NO_RENDER=1 时跳过渲染 (内存紧张时先导出、再单独渲染)
NO_RENDER = os.environ.get("CL_DESKS_NO_RENDER") == "1"
if not NO_RENDER:
    # 太阳光: 能量 3.5, 从西南来, 仰角约 50 度, 开阴影
    sun_data = bpy.data.lights.new("sun", type="SUN")
    sun_data.energy = 3.5
    sun_data.use_shadow = True
    sun = bpy.data.objects.new("sun", sun_data)
    bpy.context.collection.objects.link(sun)
    sun.location = (-6.0, -6.0, 7.0)
    sun.rotation_euler = (0.0, 0.0, 0.0)
    direction = Vector((0, 0, 0.4)) - sun.location
    sun.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

    # 世界背景: 淡蓝 (0.65, 0.78, 0.88), 强度 1.0
    world = bpy.data.worlds.new("world")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.65, 0.78, 0.88, 1.0)
    bg.inputs["Strength"].default_value = 1.0
    bpy.context.scene.world = world

    # 示意地面 (浅色) 与示意墙面 (黑板墙), 仅预览用
    floor = add_box("PREVIEW_floor", (0, 0, -0.01), (9.68, 7.26, 0.02),
                    make_material("preview_floor", "#D8D2C4", 0.9))
    wall_b = add_box("PREVIEW_wall_board", (-4.85, 0, 1.5), (0.02, 7.26, 3.0),
                     make_material("preview_wall", "#F3E9D2", 0.9))
    # 注: 后墙不放示意墙, 否则会挡住相机视线

    # 相机 v2: 低机位近景, 从教室前侧 (黑板一侧) 约 1.1m 高平视/微俯看过去,
    #   让桌腿/椅腿/离地高度/靠背立起一眼可见, 不再用高空俯视
    #   v2.2: 改为前排左前方 3/4 侧视角、贴近第一组桌椅, 桌腿/椅腿不再被
    #   成排遮挡、能直接看到桌面/椅面离地 (上一版沿排看去腿全被挡住)
    cam_data = bpy.data.cameras.new("cam")
    cam_data.lens = 32
    cam = bpy.data.objects.new("cam", cam_data)
    bpy.context.collection.objects.link(cam)
    cam.location = (-4.6, -4.2, 1.1)
    direction = Vector((-2.6, -2.6, 0.45)) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam

    # ---------- 渲染预览 ----------
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 640
    scene.render.resolution_y = 360
    scene.render.resolution_percentage = 100
    scene.eevee.taa_render_samples = 16
    scene.render.filepath = PREVIEW_PATH
    scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)

    print("preview saved:", PREVIEW_PATH, os.path.exists(PREVIEW_PATH))
print("DONE cl-desks")
