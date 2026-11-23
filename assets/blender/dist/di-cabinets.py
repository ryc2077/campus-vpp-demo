# di-cabinets: 配电房配电柜 (6 台开关柜沿北墙一字排开)
# 纹理已固化进脚本（见文件末尾 _apply_pbr_textures，2026-11-23）：
# 染色贴图 assets/blender/tex/ + 原图 assets/external/，材质节点直连
# Base Color/Roughness/Normal；重跑不再丢贴图。柜体灰绿 #6B7B72 等按
# SPEC §3。仪表玻璃不挂贴图（保持 Transmission/Alpha 透明材质原样）。
# 局部坐标: 房中心原点, x=长 16m (-8~+8), y=宽 10m (-5~+5), z 0~8m
# 单台 1.2(x) x 0.8(y) x 2.2(高)m, 中心 x=-6/-3.6/-1.2/+1.2/+3.6/+6, y=+4.5
# 结构: 底部基座 0.1m 高 + 柜体 2.1m (总高 2.2m)
#   + 前门 (朝南, y=4.1 一侧) 仪表小窗 0.4x0.3m 深色玻璃 + 门把手小横杆
# 颜色: 柜体灰绿 #6B7B72 (拉丝金属, 程序化噪波), 门板略深 #64746B, 基座 #37423B, 仪表窗淡淡蓝灰玻璃 #5B7A8A
#   (透明+镜面反射, SSR+反射探针), 把手金属灰 #8A8F94; 四种材质各自分开、深浅不均, 无全平面
# 只做配电柜: 不做变压器/母线线缆/墙面地面/标识牌
# 材质只用 Principled BSDF
import bpy
import math
import os
from mathutils import Vector

BASE = "/home/hatch/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot"
BLEND_PATH = BASE + "/assets/blender/dist/di-cabinets.blend"
GLB_PATH = BASE + "/assets/models/di-cabinets.glb"
PNG_PATH = BASE + "/screenshots/blender/di-cabinets.png"

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

def _colorramp(nodes, links, src_out, stops):
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = stops[0][0]
    ramp.color_ramp.elements[0].color = (*stops[0][1], 1.0)
    ramp.color_ramp.elements[1].position = stops[1][0]
    ramp.color_ramp.elements[1].color = (*stops[1][1], 1.0)
    links.new(src_out, ramp.inputs["Fac"])
    return ramp

def add_procedural(mat, base_hex, noise_scale, rough_lo, rough_hi,
                   tint_hex=None, tint_fac=0.0, bump_strength=0.0):
    """程序化纹理: 噪波驱动粗糙度 + 底色深浅不均 (+ 可选微凸起)。
    不用贴图, 只用 Noise/Wave 程序节点, 保证没有任何面是全平纯色。"""
    nt = mat.node_tree
    nodes = nt.nodes
    links = nt.links
    bsdf = nodes["Principled BSDF"]
    base_lin = hex_to_linear(base_hex)
    # 纹理坐标 + 拉伸映射 (y 向拉长 -> 拉丝/条纹感)
    texcoord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (noise_scale[0], noise_scale[1], noise_scale[2])
    links.new(texcoord.outputs["Generated"], mapping.inputs["Vector"])
    # 噪波
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 1.0
    noise.inputs["Detail"].default_value = 3.0
    noise.inputs["Roughness"].default_value = 0.75
    links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    # 粗糙度变化
    ramp_r = _colorramp(nodes, links, noise.outputs["Fac"],
                        [(0.0, (rough_lo, rough_lo, rough_lo)),
                         (1.0, (rough_hi, rough_hi, rough_hi))])
    links.new(ramp_r.outputs["Color"], bsdf.inputs["Roughness"])
    # 底色深浅不均: 噪波在底色与微深/微浅色之间混合
    if tint_hex is not None and tint_fac > 0.0:
        mix = nodes.new("ShaderNodeMixRGB")
        mix.blend_type = 'MIX'
        mix.inputs[1].default_value = (*base_lin, 1.0)
        mix.inputs[2].default_value = (*hex_to_linear(tint_hex), 1.0)
        mix.inputs[0].default_value = tint_fac
        # 用同一噪波做混合因子 (经第 2 条 ramp 压到 0~1 中段)
        ramp_m = _colorramp(nodes, links, noise.outputs["Fac"],
                            [(0.0, (0.15, 0.15, 0.15)),
                             (1.0, (0.85, 0.85, 0.85))])
        links.new(ramp_m.outputs["Color"], mix.inputs[0])
        # 返工 2026-11-23: 底色 Mix 不连 Base Color (否则 glTF 丢 baseColorFactor,
        # 柜体/变压器在 Godot 里全白)。深浅不均改走粗糙度/Bump, Base Color 只留纯色默认值。
    # 微凸起
    if bump_strength > 0.0:
        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = bump_strength
        bump.inputs["Distance"].default_value = 0.02
        links.new(noise.outputs["Fac"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat

BODY_MAT = make_material("Cabinet_Body", "#6B7B72", 0.6, 0.35)
# 柜体金属拉丝: y 向拉伸噪波 (条纹), 粗糙度 0.4~0.8, 底色在 #6B7B72/#4E5D55 间不均
# (条纹放粗到 y 8 格、对比拉大, 预览图里拉丝必须看得见)
add_procedural(BODY_MAT, "#6B7B72", (2.0, 8.0, 2.0), 0.4, 0.8,
               tint_hex="#4E5D55", tint_fac=0.7, bump_strength=0.2)
DOOR_MAT = make_material("Cabinet_Door", "#64746B", 0.6, 0.35)
# 门板: 与柜体同系、略深一档, 门缝在预览里能分辨
add_procedural(DOOR_MAT, "#64746B", (2.0, 8.0, 2.0), 0.4, 0.8,
               tint_hex="#4A5951", tint_fac=0.7, bump_strength=0.2)
BASE_MAT = make_material("Cabinet_Base", "#37423B", 0.7, 0.2)
# 基座: 粗糙噪波, 底色在 #37423B/#2B332E 间不均
add_procedural(BASE_MAT, "#37423B", (6.0, 6.0, 6.0), 0.55, 0.9,
               tint_hex="#2B332E", tint_fac=0.5, bump_strength=0.2)
HANDLE_MAT = make_material("Handle_Metal", "#8A8F94", 0.35, 0.85)
# 把手: 细噪波粗糙度 0.2~0.45, 底色在 #8A8F94/#6E7478 间不均
add_procedural(HANDLE_MAT, "#8A8F94", (10.0, 10.0, 10.0), 0.2, 0.45,
               tint_hex="#6E7478", tint_fac=0.4, bump_strength=0.05)

# 仪表玻璃: 淡淡蓝灰 #5B7A8A, 透明 + 镜面反射 (低粗糙度 + 透射), 噪波只做极细微的
# 粗糙度起伏 (0.03~0.08) 和极淡的色调不均, 绝不能出现明显的斑点/霉斑
GLASS_MAT = make_material("Meter_Glass", "#5B7A8A", 0.05, 0.0)
GLASS_MAT.blend_method = 'BLEND'
_glass_bsdf = GLASS_MAT.node_tree.nodes["Principled BSDF"]
_glass_bsdf.inputs["Transmission Weight"].default_value = 0.55
_glass_bsdf.inputs["Alpha"].default_value = 0.8
_glass_bsdf.inputs["Specular IOR Level"].default_value = 1.0
_glass_bsdf.inputs["IOR"].default_value = 1.45
add_procedural(GLASS_MAT, "#5B7A8A", (8.0, 8.0, 8.0), 0.03, 0.08,
               tint_hex="#4E6B7A", tint_fac=0.12, bump_strength=0.0)

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

# ---------- 6 台开关柜, 中心 x=-6/-3.6/-1.2/+1.2/+3.6/+6, y=+4.5 ----------
# 柜体前面朝南 (y=4.1 一侧), 仪表窗与把手装在前面
for i, cx in enumerate((-6.0, -3.6, -1.2, 1.2, 3.6, 6.0)):
    tag = "C%d" % (i + 1)
    # 基座: 1.24 x 0.84 x 0.1, z 0~0.1 (略大于柜体)
    objs.append(add_box("%s_Base" % tag, (1.24, 0.84, 0.1), (cx, 4.5, 0.05), BASE_MAT, bevel=0.01))
    # 柜体: 1.2 x 0.8 x 2.1, z 0.1~2.2
    objs.append(add_box("%s_Body" % tag, (1.2, 0.8, 2.1), (cx, 4.5, 1.15), BODY_MAT, bevel=0.02))
    # 门板: 1.14 x 0.02 x 2.0, 贴前面, y 4.085~4.105, z 0.15~2.15 (略深一档, 门缝可见)
    objs.append(add_box("%s_Door" % tag, (1.14, 0.02, 2.0), (cx, 4.5 - 0.405, 1.15), DOOR_MAT, bevel=0.01))
    # 仪表小窗: 0.4 x 0.02 x 0.3 深色玻璃, y 4.08~4.10, z 1.6~1.9
    objs.append(add_box("%s_Meter" % tag, (0.4, 0.02, 0.3), (cx, 4.5 - 0.41, 1.75), GLASS_MAT))
    # 门把手: 小横杆 0.35 x 0.05 x 0.05, y 4.075~4.125, z 1.045~1.095
    objs.append(add_box("%s_Handle" % tag, (0.35, 0.05, 0.05), (cx, 4.5 - 0.40, 1.07), HANDLE_MAT))

print("di-cabinets objects:", len(objs), [o.name for o in objs])

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

# 室内预览补光 (仅预览, 不导出): 一盏点光源在柜排前方上方
ld = bpy.data.lights.new("Preview_Point", type='POINT')
ld.energy = 300.0
ld.shadow_soft_size = 0.5
lo = bpy.data.objects.new("Preview_Point", ld)
bpy.context.collection.objects.link(lo)
lo.location = (0.0, 1.5, 5.0)

# 玻璃反光: 只用 Screen Space Reflections (追加要求: SSR 与 Cubemap 二选一即可)。
# 探针要多烘 6 面、在 llvmpipe 上拖慢渲染, 故不用探针; SSR 半分辨率追踪再提速,
# 玻璃的淡淡蓝灰透明 + 镜面反射仍由 SSR 提供。
# (注: 2026-11-22 实测: 带探针+折射的 Eevee 渲染在拥挤机器上 10 分钟以上跑不完,
# 多次被 OOM/重启打断, 故改为 SSR 半分辨率、无折射。)

# ---------- camera: 南侧正前方高处 45° 俯视, 6 台柜子全部入画并留边距 ----------
# (旧机位 (7,-3.5,4.5) 太近, 最右一台被裁出画外; 改退到 (5,-9.5,5.5), 镜头 30mm)
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 30.0
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera = cam
cam.location = (5.0, -9.5, 5.5)
target = Vector((0.0, 4.5, 1.1))
cam.rotation_mode = 'QUATERNION'
cam.rotation_quaternion = (target - cam.location).to_track_quat('-Z', 'Y')

# ---------- render settings ----------
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.eevee.taa_render_samples = 16
# 玻璃镜面反射: 开 Screen Space Reflections (半分辨率追踪提速), 不开折射
scene.eevee.use_ssr = True
scene.eevee.use_ssr_refraction = False
if hasattr(scene.eevee, "use_ssr_halfres"):
    scene.eevee.use_ssr_halfres = True
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100
scene.render.filepath = PNG_PATH

# ---- PBR 贴图固化 (2026-11-23)：把上一轮挂在 .blend 上的外部贴图写进脚本 ----
# color 图：assets/blender/tex/ 里的染色图（已按 SPEC §3 目标色染色，柜体
# 灰绿 #6B7B72 等）；rough/normal 图：assets/external/ 原图（CC0）。
# 节点只许 TexCoord→Mapping→Image Texture 直连 BSDF，不加 Hue/Sat/Mix，
# 否则 glTF 导出器不认。Base Color 默认值须置白、Roughness 置 1.0（贴图
# 本身带颜色与粗糙度），否则导出器会把旧纯色写成 baseColorFactor/
# roughnessFactor 与贴图二次相乘；Metallic 保持脚本原值。仪表玻璃跳过。
# 没有 UV 的网格补 Smart UV Project（已有 UV 的不动）。
TEX_DIR = os.path.join(BASE, "assets/blender/tex")
EXT_DIR = os.path.join(BASE, "assets/external")
# 材质名: (tex/ 染色 color 图, external rough 图, external normal 图, Mapping 缩放)
PBR_TEXTURES = {
    "Cabinet_Base": ("corrugated_iron_02__37423B.jpg",
        "polyhaven/corrugated_iron_02_rough_1k.jpg",
        "polyhaven/corrugated_iron_02_nor_gl_1k.jpg", (1.0, 1.0)),
    "Cabinet_Body": ("corrugated_iron_02__6B7B72.jpg",
        "polyhaven/corrugated_iron_02_rough_1k.jpg",
        "polyhaven/corrugated_iron_02_nor_gl_1k.jpg", (2.0, 1.0)),
    "Cabinet_Door": ("corrugated_iron_02__64746B.jpg",
        "polyhaven/corrugated_iron_02_rough_1k.jpg",
        "polyhaven/corrugated_iron_02_nor_gl_1k.jpg", (2.0, 1.0)),
    "Handle_Metal": ("corrugated_iron_02__8A8F94.jpg",
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
# 清理回读留下的孤儿数据 (导入的 .001 网格/材质/打包贴图)，否则最终存盘的
# .blend 里会多出重复材质与打包贴图；先清网格 (材质可能还被孤儿网格引用着)，
# 再清材质，最后清贴图 (本件外链贴图有材质引用，不受影响)
for _mesh in list(bpy.data.meshes):
    if _mesh.users == 0:
        bpy.data.meshes.remove(_mesh)
for _mat in list(bpy.data.materials):
    if _mat.users == 0:
        bpy.data.materials.remove(_mat)
for _img in list(bpy.data.images):
    if _img.users == 0:
        bpy.data.images.remove(_img)
print("orphan purge done, materials:", sorted(m.name for m in bpy.data.materials))

# ---------- render preview ----------
# 本地不渲染: 渲染统一走 GitHub Actions (2026-11-22 用户新决定)。
# 本段默认仍执行 (Actions 跑本脚本时出图); 本地跑时置环境变量
# DI_CABINETS_SKIP_RENDER=1 即可跳过渲染, 只做建模/存盘/导出/回读验证。
if os.environ.get("DI_CABINETS_SKIP_RENDER") != "1":
    bpy.ops.render.render(write_still=True)
    print("Preview saved:", PNG_PATH, "exists:", os.path.exists(PNG_PATH),
          "size:", os.path.getsize(PNG_PATH) if os.path.exists(PNG_PATH) else 0)
else:
    print("Render skipped locally (DI_CABINETS_SKIP_RENDER=1); preview renders on GitHub Actions")
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("DONE di-cabinets")
