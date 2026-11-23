# di-transformer: 配电房变压器 (4 台主变, 合计 3000kVA, 一字排开)
# 纹理已固化进脚本（见文件末尾 _apply_pbr_textures，2026-11-23）：
# 染色贴图 assets/blender/tex/ + 原图 assets/external/，材质节点直连
# Base Color/Roughness/Normal；重跑不再丢贴图。
# 局部坐标: 房中心原点, x=长 16m (-8~+8), y=宽 10m (-5~+5), z 0~8m
# 单台 2.5(x) x 1.5(y) x 2.6(高)m, 中心 x=-4.5/-1.5/+1.5/+4.5, y=-2.5
# 结构: 基座 0.15m 高 + 本体 2.45m (总高 2.6m) + 顶盖 + 两侧散热片
#   (每侧 5 片竖向细条, 0.05m 厚) + 顶部 3 个套管 (小圆柱, 高 0.4m)
# 颜色: 本体/散热片 深灰绿 #4A5A50, 基座 #37423B, 套管 #424A52, 端子 #8A8F94
# 只做变压器: 不做配电柜/母线/墙面地面/标识牌
# 材质只用 Principled BSDF
import bpy
import math
import os
from mathutils import Vector

BASE = "/home/hatch/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot"
BLEND_PATH = BASE + "/assets/blender/dist/di-transformer.blend"
GLB_PATH = BASE + "/assets/models/di-transformer.glb"
PNG_PATH = BASE + "/screenshots/blender/di-transformer.png"

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

def add_paint_texture(mat, dark_hex, light_hex, noise_scale,
                      rough_min, rough_max, bump_strength, bump_distance=0.02,
                      stretch=None):
    """程序化漆面/陶瓷纹理: 同一 Noise Fac 驱动颜色深浅 + 粗糙度 + Bump。
    只改材质节点, 不动几何。Noise Scale 越大纹理越细, 本件取中值,
    避免大色块糊成一片, 也避免高频噪点糊掉。
    stretch=(sx, sy, sz): 映射拉伸, 用于金属拉丝 (如 (1,1,12) 拉出竖纹)。"""
    nt = mat.node_tree
    nodes = nt.nodes
    bsdf = nodes["Principled BSDF"]
    texcoord = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = noise_scale
    noise.inputs["Detail"].default_value = 3.0
    noise.inputs["Roughness"].default_value = 0.7
    noise.inputs["Distortion"].default_value = 0.15
    if stretch is not None:
        mapping = nodes.new("ShaderNodeMapping")
        mapping.inputs["Scale"].default_value = stretch
        nt.links.new(texcoord.outputs["Object"], mapping.inputs["Vector"])
        nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    else:
        nt.links.new(texcoord.outputs["Object"], noise.inputs["Vector"])
    # 颜色深浅: Fac -> ColorRamp(深/浅两端收窄, 只做轻微不均)
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (*hex_to_linear(dark_hex), 1.0)
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = (*hex_to_linear(light_hex), 1.0)
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    # 返工 2026-11-23: 漆面 Ramp 不连 Base Color (否则 glTF 丢 baseColorFactor,
    # 变压器在 Godot 里全白)。深浅不均改走粗糙度/Bump, Base Color 只留纯色默认值。
    # 粗糙度: Fac -> Map Range, 在基值上下窄幅浮动
    mr = nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.0
    mr.inputs["From Max"].default_value = 1.0
    mr.inputs["To Min"].default_value = rough_min
    mr.inputs["To Max"].default_value = rough_max
    nt.links.new(noise.outputs["Fac"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])
    # 凹凸: 同一 Fac -> Bump, 强度压得很低, 只留漆面颗粒感
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = bump_strength
    bump.inputs["Distance"].default_value = bump_distance
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat

BODY_MAT = make_material("Transformer_Body", "#4A5A50", 0.6, 0.3)
# 箱体漆面: Scale 4.5 中等斑块, 粗糙度 0.50~0.70, Bump 0.10
# (色阶拉开一档, 保证 640x360 预览里斑驳肉眼可见, 仍是轻微不均)
add_paint_texture(BODY_MAT, "#3A4840", "#5E7066", 4.5, 0.50, 0.70, 0.10, 0.02)
# 散热片单独材质: 金属拉丝, 竖向拉伸 Noise (1,1,12) 出竖纹, 与箱体漆面分开
FIN_MAT = make_material("Transformer_Fin", "#4A5A50", 0.55, 0.45)
add_paint_texture(FIN_MAT, "#3C4941", "#5A6A5C", 8.0, 0.45, 0.65, 0.05, 0.015,
                  stretch=(1.0, 1.0, 12.0))
BASE_MAT = make_material("Transformer_Base", "#37423B", 0.7, 0.2)
# 底座混凝土: 粗 Noise (Scale 6) + 强 Bump, 深浅不均
add_paint_texture(BASE_MAT, "#2C352F", "#46534A", 6.0, 0.72, 0.92, 0.12, 0.03)
BUSH_MAT = make_material("Bushing_DarkGrey", "#424A52", 0.5, 0.1)
# 套管陶瓷: 细 Noise (Scale 18), 粗糙度只在 0.42~0.58 窄幅变化, Bump 0.03 极弱
add_paint_texture(BUSH_MAT, "#3D454D", "#475058", 18.0, 0.42, 0.58, 0.03, 0.01)
TERM_MAT = make_material("Terminal_Metal", "#8A8F94", 0.35, 0.8)
# 端子金属拉丝: 竖向拉伸细 Noise, 粗糙度 0.25~0.45
add_paint_texture(TERM_MAT, "#767C81", "#9CA2A7", 10.0, 0.25, 0.45, 0.02, 0.01,
                  stretch=(1.0, 1.0, 10.0))

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

def add_cyl(name, radius, depth, loc, mat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=radius, depth=depth, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.data.materials.append(mat)
    return ob

objs = []

# ---------- 4 台主变, 中心 x=-4.5/-1.5/+1.5/+4.5, y=-2.5 ----------
for i, cx in enumerate((-4.5, -1.5, 1.5, 4.5)):
    tag = "T%d" % (i + 1)
    # 基座: 2.6 x 1.6 x 0.15, 顶面 z=0.15 (略大于本体,  realistic plinth)
    objs.append(add_box("%s_Base" % tag, (2.6, 1.6, 0.15), (cx, -2.5, 0.075), BASE_MAT, bevel=0.02))
    # 本体: 2.5 x 1.5 x 2.45, z 0.15~2.6
    objs.append(add_box("%s_Body" % tag, (2.5, 1.5, 2.45), (cx, -2.5, 1.375), BODY_MAT, bevel=0.02))
    # 顶盖: 2.56 x 1.56 x 0.06, z 2.60~2.66
    objs.append(add_box("%s_Lid" % tag, (2.56, 1.56, 0.06), (cx, -2.5, 2.63), BODY_MAT, bevel=0.01))
    # 散热片: 两侧 (y 向) 各 5 片竖向细条, 0.05m 厚(x) x 0.30m 深(y) x 1.9m 高,
    #   z 0.15~2.05, 沿 x 排开, 贴本体前后侧面 (y=+-0.75), 外缘 y=+-1.05
    for side in (-1, 1):
        for j, dx in enumerate((-0.8, -0.4, 0.0, 0.4, 0.8)):
            objs.append(add_box("%s_Fin_%s%d" % (tag, "S" if side < 0 else "N", j + 1),
                                (0.05, 0.30, 1.9), (cx + dx, -2.5 + side * 0.90, 1.10), FIN_MAT))
    # 顶部套管: 3 个小圆柱, r=0.09, 高 0.4m, z 2.66~3.06, 沿 x 排开
    for k, dx in enumerate((-0.7, 0.0, 0.7)):
        objs.append(add_cyl("%s_Bushing%d" % (tag, k + 1), 0.09, 0.4,
                            (cx + dx, -2.5, 2.86), BUSH_MAT))
        # 套管顶端子: r=0.05, 高 0.08, z 3.06~3.14
        objs.append(add_cyl("%s_Terminal%d" % (tag, k + 1), 0.05, 0.08,
                            (cx + dx, -2.5, 3.10), TERM_MAT))

print("di-transformer objects:", len(objs), [o.name for o in objs])

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

# 室内预览补光 (仅预览, 不导出): 一盏点光源在变压器排上方
ld = bpy.data.lights.new("Preview_Point", type='POINT')
ld.energy = 300.0
ld.shadow_soft_size = 0.5
lo = bpy.data.objects.new("Preview_Point", ld)
bpy.context.collection.objects.link(lo)
lo.location = (0.0, -2.5, 5.5)

# ---------- camera: 东南侧高处 45° 俯视, 看向变压器排中心 ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 32.0
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera = cam
cam.location = (8.0, -9.5, 5.0)
target = Vector((0.0, -2.5, 1.3))
cam.rotation_mode = 'QUATERNION'
cam.rotation_quaternion = (target - cam.location).to_track_quat('-Z', 'Y')

# ---------- render settings ----------
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.eevee.taa_render_samples = 16
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100
scene.render.filepath = PNG_PATH

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
    "Transformer_Base": ("concrete_wall_007__37423B.jpg",
        "polyhaven/concrete_wall_007_rough_1k.jpg",
        "polyhaven/concrete_wall_007_nor_gl_1k.jpg", (1.0, 1.0)),
    "Transformer_Body": ("blue_metal_plate__4A5A50.jpg",
        "polyhaven/blue_metal_plate_rough_1k.jpg",
        "polyhaven/blue_metal_plate_nor_gl_1k.jpg", (2.0, 2.0)),
    "Transformer_Fin": ("corrugated_iron_02__4A5A50.jpg",
        "polyhaven/corrugated_iron_02_rough_1k.jpg",
        "polyhaven/corrugated_iron_02_nor_gl_1k.jpg", (2.0, 1.0)),
    "Bushing_DarkGrey": ("concrete_wall_007__424A52.jpg",
        "polyhaven/concrete_wall_007_rough_1k.jpg",
        "polyhaven/concrete_wall_007_nor_gl_1k.jpg", (1.0, 1.0)),
    "Terminal_Metal": ("corrugated_iron_02__8A8F94.jpg",
        "polyhaven/corrugated_iron_02_rough_1k.jpg",
        "polyhaven/corrugated_iron_02_nor_gl_1k.jpg", (1.0, 1.0)),
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
_ensure_uvs(objs)

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
# 删掉回读的副本, 恢复干净场景再渲染
bpy.ops.object.select_all(action='DESELECT')
for ob in imported:
    ob.select_set(True)
bpy.ops.object.delete()
# 清理回读留下的孤儿数据 (导入的 .001 网格/材质), 否则最终 .blend 里
# 会多出 5 份重复材质; 先清网格 (材质可能还被孤儿网格引用着)
for _mesh in list(bpy.data.meshes):
    if _mesh.users == 0:
        bpy.data.meshes.remove(_mesh)
for _mat in list(bpy.data.materials):
    if _mat.users == 0:
        bpy.data.materials.remove(_mat)
for _img in list(bpy.data.images):
    # 回读导入的 .001 贴图是打包进来的孤儿（无使用者），不清除会随最终存盘
    # 混进 .blend；本件外链贴图有材质引用，不受影响
    if _img.users == 0:
        bpy.data.images.remove(_img)
print("orphan purge done, materials:", sorted(m.name for m in bpy.data.materials))

# ---------- render preview (本地默认跳过, 走 GitHub Actions; 置 DI_TRANSFORMER_RENDER=1 才渲染) ----------
if os.environ.get("DI_TRANSFORMER_RENDER") == "1":
    bpy.ops.render.render(write_still=True)
    print("Preview saved:", PNG_PATH, "exists:", os.path.exists(PNG_PATH),
          "size:", os.path.getsize(PNG_PATH) if os.path.exists(PNG_PATH) else 0)
else:
    print("Render skipped locally (set DI_TRANSFORMER_RENDER=1 to render)")
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("DONE di-transformer")
