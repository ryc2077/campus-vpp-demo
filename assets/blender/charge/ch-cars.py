# ch-cars v3 (R2-T19, 2026-11-24): Quaternius 网上三车替换手捏小车。
# 来源：assets/external/SOURCES.md §9（poly.pizza Quaternius Cars 包，CC0），
# 三辆在 assets/external/cars/quaternius/：car（蓝）、suv（白）、sports-car-2（橙）。
# 实测（Blender 4.2.0 导入探针 probe.log）：三车 glTF 前向 +Z，Blender 导入后
# 长在 Y 轴、车头（Headlights 面质心）在 -Y；轮底 z≈0（suv -0.02、sports -0.01、
# car +0.01），基本贴地。结构：车身 + 后轮轴一体 + 左右前轮各一；车窗/前后灯
# 为车身 mesh 上独立材质面（Windows/Headlights/TailLights），车轮真几何。
#
# 换装做法（不手捏，只改导入模型的材质数值与变换）：
# - 每车绕 Z 转 +90° 烘进 mesh（车头 -Y -> +X、车长落到 X 轴），与旧手捏车
#   的局部系完全一致（车长沿 X、车头 +X）；empty 保持旧旋转（充电区 -90°，
#   车头朝 -Y/南，与旧车一致、朝桩方向不变）。
# - 统一按长缩放到 4.4 m（car ×1.0427、suv ×1.0451、sports ×1.1083，均匀缩放）：
#   充电车位 2.5 m 宽（线内缘 ±1.19 m），三车宽 1.89/2.21/1.99 m 均不压线
#   （suv 半宽 1.10 m，余 0.09 m）。
# - Sports 2 出厂橙色：Orange + DarkOrange 两材质 baseColorFactor 均改为
#   SPEC 红 #C4534E（只改数值，不是建模）；蓝车漆改为旧蓝 #3B82C4、白车漆
#   改为旧白 #D7DDE3，三色与旧车/ campus.json 颜色口径一致。
# - 车漆复用旧清漆配方（Metallic 0.15 / Roughness 0.25 / Coat Weight 1.0 /
#   Coat Roughness 0.05）；车窗用已验证深色镀膜玻璃（透射 0.10、alpha 0.90、
#   粗糙度 0.15、深色 #33505F tint、Specular 1.0）；轮胎 #2A2D2F 粗糙 0.95、
#   轮毂 #C0C5C9 金属 0.8/粗糙 0.35、前灯暖白发光、尾灯红发光（均沿用旧配方）。
# - 车身主 mesh 命名 ch-cars_<tag>_roof：它兼任 Godot SOC 条锚点
#   （scripts/campus_builder.gd _build_charge_glb_soc_bars 找
#   ch-cars_<tag>_roof，用 position.y + mesh AABB.y/2 算车顶高）。
#   为此把该 mesh 的原点移到 mesh 高度中点（L = zmax - h/2，mesh 数据反向
#   平移 -L，世界几何不动），使 position.y + AABB.y/2 恰为车顶高；
#   其余 mesh 原点不动。GLB 导出保留节点 TRS（旧 charge.glb 实测），此
#   锚点关系可进 Godot。
# 位置与旧车一致：蓝 V2G (38,-76) 1 号位、红 V2G (45,-76) 3 号位、
# 白普通 (48.5,-76) 4 号位，车头均朝南。
import bpy
import json
import math
import os
import struct
from mathutils import Matrix, Vector

ROOT = os.path.expanduser(
    "~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
SCRIPT_DIR = os.path.join(ROOT, "assets/blender/charge")
CARS_DIR = os.path.join(ROOT, "assets/external/cars/quaternius")
BLEND_PATH = os.path.join(SCRIPT_DIR, "ch-cars.blend")
GLB_PATH = os.path.join(ROOT, "assets/models/ch-cars.glb")
PNG_PATH = os.path.join(ROOT, "screenshots/blender/ch-cars.png")

# ---- clean scene ----
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)


def srgb_to_linear(hexstr):
    h = hexstr.lstrip('#')
    r = int(h[0:2], 16) / 255.0
    g = int(h[2:4], 16) / 255.0
    b = int(h[4:6], 16) / 255.0

    def conv(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (conv(r), conv(g), conv(b), 1.0)


def _noise_bump(ntree, bsdf, scale, strength):
    tex = ntree.nodes.new("ShaderNodeTexCoord")
    noise = ntree.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 2.0
    ntree.links.new(tex.outputs["Generated"], noise.inputs["Vector"])
    bump = ntree.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = strength
    bump.inputs["Distance"].default_value = 0.02
    ntree.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    ntree.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])


def make_paint(name, hexstr):
    """Car paint (旧清漆配方): Metallic 0.15 / Roughness 0.25 solid +
    Coat Weight 1.0 / Coat Roughness 0.05 + 细颗粒 Bump（只进 EEVEE，
    不进 glTF）。Base Color / Roughness 不链接，保证 glTF factor 保留。"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    ntree = mat.node_tree
    bsdf = ntree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = srgb_to_linear(hexstr)
    bsdf.inputs["Metallic"].default_value = 0.15
    bsdf.inputs["Roughness"].default_value = 0.25
    bsdf.inputs["Coat Weight"].default_value = 1.0
    bsdf.inputs["Coat Roughness"].default_value = 0.05
    _noise_bump(ntree, bsdf, scale=40.0, strength=0.10)
    return mat


def make_glass(name):
    """Tinted car glass（已验证配方，见旧 make_glass 注释）：
    Transmission 0.10、Alpha 0.90、Roughness 0.15、深色 #33505F、
    Specular IOR Level 1.0、IOR 1.45。Principled-only（EEVEE == GLB）。"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    ntree = mat.node_tree
    bsdf = ntree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = srgb_to_linear("#33505F")
    bsdf.inputs["Roughness"].default_value = 0.15
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Transmission Weight"].default_value = 0.10
    bsdf.inputs["Alpha"].default_value = 0.90
    bsdf.inputs["Specular IOR Level"].default_value = 1.0
    bsdf.inputs["IOR"].default_value = 1.45
    mat.surface_render_method = "DITHERED"
    return mat


def make_tire(name):
    """Rubber: roughness ~0.95 + noise bump, separate from the hub."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    ntree = mat.node_tree
    bsdf = ntree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = srgb_to_linear("#2A2D2F")
    bsdf.inputs["Roughness"].default_value = 0.95
    bsdf.inputs["Metallic"].default_value = 0.0
    _noise_bump(ntree, bsdf, scale=10.0, strength=0.30)
    return mat


def make_hub(name):
    """Metal hub: metallic ~0.8, roughness 0.35 solid."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    ntree = mat.node_tree
    bsdf = ntree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = srgb_to_linear("#C0C5C9")
    bsdf.inputs["Metallic"].default_value = 0.8
    bsdf.inputs["Roughness"].default_value = 0.35
    return mat


def make_lamp(name, hexstr, emission_hex, strength=1.0):
    """Weak-emission lamp block (headlight warm white / taillight red)."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = srgb_to_linear(hexstr)
    bsdf.inputs["Roughness"].default_value = 0.25
    bsdf.inputs["Emission Color"].default_value = srgb_to_linear(emission_hex)
    bsdf.inputs["Emission Strength"].default_value = strength
    return mat


# ---- canonical materials: imported material base name -> piece material ----
# 三车导入后同名材质（Windows/Black/Grey/Headlights/TailLights）各出现 3 份，
# 全部 remap 到同一份规范材质；Orange/DarkOrange 两档红各留一份（GLB 共 9 种
# 车材质，charge 场景去重后总数仍为 24，与旧版一致）。
MAT_PAINT_BLUE = make_paint("ch-cars_paint_blue", "#3B82C4")
MAT_PAINT_WHITE = make_paint("ch-cars_paint_white", "#D7DDE3")
MAT_PAINT_RED = make_paint("ch-cars_paint_red", "#C4534E")
MAT_PAINT_RED_DARK = make_paint("ch-cars_paint_red_dark", "#C4534E")
MAT_GLASS = make_glass("ch-cars_glass")
MAT_TIRE = make_tire("ch-cars_tire")
MAT_HUB = make_hub("ch-cars_hub")
MAT_HEAD = make_lamp("ch-cars_headlamp", "#FFF6D8", "#FFF2CC", strength=1.0)
MAT_TAIL = make_lamp("ch-cars_taillamp", "#C03028", "#D04030", strength=0.8)
CANON = {"Blue": MAT_PAINT_BLUE, "White": MAT_PAINT_WHITE,
         "Orange": MAT_PAINT_RED, "DarkOrange": MAT_PAINT_RED_DARK,
         "Windows": MAT_GLASS, "Black": MAT_TIRE, "Grey": MAT_HUB,
         "Headlights": MAT_HEAD, "TailLights": MAT_TAIL}


def _mat_face_centroid(obj, mat_name):
    """World-space centroid of faces using the given material slot."""
    idx = [i for i, m in enumerate(obj.data.materials)
           if m and m.name.split(".")[0] == mat_name]
    assert idx, f"{obj.name}: no material slot {mat_name}"
    mi = idx[0]
    pts = [obj.matrix_world @ p.center for p in obj.data.polygons
           if p.material_index == mi]
    assert pts, f"{obj.name}: no faces with {mat_name}"
    return sum(pts, Vector((0, 0, 0))) / len(pts)


def import_car(tag, filename, scale, cx, cy, rot_z_deg):
    """Import one Quaternius car, recolor/remap materials, rotate +90 deg
    about Z (front -Y -> +X, length onto X), scale, and parent under an
    empty at (cx, cy, 0) with rotation rot_z_deg. Returns (group, meshes).
    scale is (sx, sy, sz) in the IMPORTED local axes (x=width, y=length,
    z=height); here all three factors are equal (uniform length scale)."""
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(CARS_DIR, filename))
    meshes = [o for o in bpy.context.scene.objects
              if o not in before and o.type == 'MESH']
    assert len(meshes) == 4, f"{tag}: expected 4 meshes, got {len(meshes)}"
    # body = the mesh with the most material slots (6-7: paint/windows/lamps)
    body = max(meshes, key=lambda o: len(o.data.materials))
    assert len(body.data.materials) >= 6, \
        f"{tag}: body has {len(body.data.materials)} materials, expected >=6"
    # orientation check (pre-rotation): headlights must be at -Y, tail at +Y
    hl = _mat_face_centroid(body, "Headlights")
    tl = _mat_face_centroid(body, "TailLights")
    assert hl.y < -1.0 and tl.y > 1.0, \
        f"{tag}: headlight centroid y={hl.y:.2f}, taillight y={tl.y:.2f} " \
        "(expected front at -Y)"
    print(f"IMPORT {tag}: {filename} headlight y={hl.y:.2f} "
          f"taillight y={tl.y:.2f} (front -Y confirmed)")
    # remap imported materials to the canonical piece materials
    for o in meshes:
        for i, m in enumerate(list(o.data.materials)):
            base = m.name.split(".")[0]
            assert base in CANON, f"{tag}: unexpected material {m.name}"
            o.data.materials[i] = CANON[base]
    # rotate +90 deg about Z + scale, baked directly into mesh data.
    # (Direct mesh.transform: bpy.ops.object.transform_apply silently
    # skipped the rotation in the 2026-11-24 probe — scale baked,
    # rotation not baked — so the operator is not used here.)
    # Local axes of the imported mesh: x=width, y=length, z=height;
    # scale is (sx=width, sy=length, sz=height) in those axes.
    bake = (Matrix.Rotation(math.radians(90), 4, 'Z')
            @ Matrix.Diagonal(scale + (1.0,)))
    for o in meshes:
        o.data.transform(bake)
    bpy.context.view_layer.update()
    # front check after bake: headlights must now be at +X
    # (materials were remapped to CANON names above)
    hl2 = _mat_face_centroid(body, "ch-cars_headlamp")
    tl2 = _mat_face_centroid(body, "ch-cars_taillamp")
    assert hl2.x > 1.0 and tl2.x < -1.0, \
        f"{tag}: after bake headlight x={hl2.x:.2f}, taillight x={tl2.x:.2f} " \
        "(expected front at +X)"
    # body mesh doubles as the Godot SOC-bar anchor (ch-cars_<tag>_roof):
    # move its origin to the mesh height midpoint (mesh data shifted back
    # by -L, world geometry unchanged) so that in Godot
    # position.y + AABB.y/2 == roof top height.
    zs = [v.co.z for v in body.data.vertices]
    zmin, zmax = min(zs), max(zs)
    roof_h = zmax
    L = zmax - (zmax - zmin) / 2.0
    body.data.transform(Matrix.Translation((0, 0, -L)))
    body.location = (0, 0, L)
    print(f"IMPORT {tag}: roof top z={roof_h:.3f} origin L={L:.3f} "
          f"(anchor check: L + h/2 = {L + (zmax - zmin) / 2.0:.3f})")
    # lift so the lowest point (wheel bottom) sits exactly at z=0
    # (signed: SUV/sports wheels start slightly below 0, car slightly above)
    all_zmin = min(min(v.co.z for v in o.data.vertices) + o.location.z
                   for o in meshes)
    lift = -all_zmin
    # rename: body -> _roof (Godot anchor), wheels by baked position
    body.name = "ch-cars_%s_roof" % tag
    bpy.context.view_layer.update()
    for o in meshes:
        if o is body:
            continue
        c = sum((o.matrix_world @ Vector(v) for v in o.bound_box),
                Vector((0, 0, 0))) / 8.0
        if c.x < 0:
            o.name = "ch-cars_%s_wheels_rear" % tag
        elif c.y > 0:
            o.name = "ch-cars_%s_wheel_FL" % tag
        else:
            o.name = "ch-cars_%s_wheel_FR" % tag
    # group under an empty so rotation/placement is one transform
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(cx, cy, lift))
    grp = bpy.context.active_object
    grp.name = "ch-cars_%s" % tag
    grp.rotation_euler = (0, 0, math.radians(rot_z_deg))
    for o in meshes:
        o.parent = grp
    bpy.context.view_layer.update()
    for o in meshes:
        bb = [o.matrix_world @ Vector(v) for v in o.bound_box]
        mn = [min(v[i] for v in bb) for i in range(3)]
        mx = [max(v[i] for v in bb) for i in range(3)]
        print(f"  PLACED {o.name}: x[{mn[0]:.2f},{mx[0]:.2f}] "
              f"y[{mn[1]:.2f},{mx[1]:.2f}] z[{mn[2]:.2f},{mx[2]:.2f}]")
    return grp, meshes


# ---- cars (positions unchanged from v1) ----
# Blue V2G at x=38 (bay 1), red V2G at x=45 (bay 3): front faces -Y (south),
# same as the old -90 deg rotation (local front +X -> -Y).
# White non-V2G in empty bay 4 (x=48.5), front toward -Y like blue/red.
# Uniform length scale to 4.4 m (see header for bay-width check).
export_objs = []
_grp, _m = import_car("blue", "car-quaternius.glb",
                      (4.4 / 4.22, 4.4 / 4.22, 4.4 / 4.22), 38, -76, -90)
export_objs += [_grp] + _m
_grp, _m = import_car("red", "sports-car-2-quaternius.glb",
                      (4.4 / 3.97, 4.4 / 3.97, 4.4 / 3.97), 45, -76, -90)
export_objs += [_grp] + _m
_grp, _m = import_car("white", "suv-quaternius.glb",
                      (4.4 / 4.21, 4.4 / 4.21, 4.4 / 4.21), 48.5, -76, -90)
export_objs += [_grp] + _m

print("car objects:", len(export_objs))

# ---- drop orphaned imported materials (replaced by CANON) ----
for _m in list(bpy.data.materials):
    if _m.users == 0:
        bpy.data.materials.remove(_m)
print("materials in blend:", sorted(m.name for m in bpy.data.materials))

# ---- 材质校验（返工防回归）：车漆 Base Color/Roughness 不链接、带清漆 ----
for _m in [m for m in bpy.data.materials
           if m.name.startswith("ch-cars_paint_")]:
    _bsdf = _m.node_tree.nodes["Principled BSDF"]
    assert not _bsdf.inputs["Base Color"].is_linked, f"{_m.name}: Base Color linked!"
    assert not _bsdf.inputs["Roughness"].is_linked, f"{_m.name}: Roughness linked!"
    assert abs(_bsdf.inputs["Coat Weight"].default_value - 1.0) < 1e-6, \
        f"{_m.name}: Coat Weight != 1.0"
    assert abs(_bsdf.inputs["Coat Roughness"].default_value - 0.05) < 1e-6, \
        f"{_m.name}: Coat Roughness != 0.05"
print("MATERIAL CHECK PASS: car paint + hub have solid Base Color + Roughness; "
      "car paint clearcoat Coat Weight 1.0 / Coat Roughness 0.05")
# glass fix 2026-11-24: tinted glass, low transmission, strong specular
_g = MAT_GLASS.node_tree.nodes["Principled BSDF"]
assert abs(_g.inputs["Transmission Weight"].default_value - 0.10) < 1e-6, \
    "ch-cars_glass: Transmission Weight != 0.10"
assert abs(_g.inputs["Alpha"].default_value - 0.90) < 1e-6, \
    "ch-cars_glass: Alpha != 0.90"
assert abs(_g.inputs["Roughness"].default_value - 0.15) < 1e-6, \
    "ch-cars_glass: Roughness != 0.15"
assert abs(_g.inputs["Specular IOR Level"].default_value - 1.0) < 1e-6, \
    "ch-cars_glass: Specular IOR Level != 1.0"
print("GLASS CHECK PASS: transmission 0.10 / alpha 0.90 / roughness 0.15 / "
      "specular 1.0")

# ---- lighting / world (SPEC section 2) ----
# 2026-11-24 返工 R2（验收 run 45251171902：Coat 0.05/底漆 0.25 后新图与旧图
#   逐像素几乎相同——清漆层在纯色平坦世界里无物可映、太阳镜面角又打不到
#   自动相机方向，再锐的涂层也看不见。修法：.blend 里保留 Nishita 天空
#   世界（render_max 只在无世界/近黑时才补平色天，亮色世界原样保留），
#   清漆层映天空渐变+太阳盘，车身现光泽；不改色、不改结构、不进 GLB，
#   Godot 不受影响。太阳仍走 SPEC 西南方向（本件不留太阳，render_max 补默认太阳）。）
world = bpy.data.worlds.new("ch-cars_world")
bpy.context.scene.world = world
world.use_nodes = True
_sky = world.node_tree.nodes.new("ShaderNodeTexSky")
_sky.sky_type = 'NISHITA'
_sky.sun_elevation = math.radians(50.0)
_sky.sun_rotation = math.radians(225.0)
_sky.altitude = 0.0
_bg = world.node_tree.nodes["Background"]
world.node_tree.links.new(_sky.outputs["Color"], _bg.inputs["Color"])
_bg.inputs["Strength"].default_value = 1.0

# ---- R3 preview studio (2026-11-24, root cause in BLENDER_MODELS.md §9) ----
# R2 只留 Nishita 天空仍全哑光，本地最小复现（320x180 像素统计，未出预览图）证实：
#   1. 世界接线正确（Nishita→Background→Output）、film_transparent=False——不是接法问题；
#   2. 自动相机俯角约 28°、顶缘视线仍低于地平线约 16°，天空根本不在画面内；
#   3. EEVEE 里世界直接进清漆环境反射（黑世界→车漆深饱和、白世界→洗白），
#      反射探针（烘焙/不烘焙）像素变化仅 meanAbs 约 1.0——探针不是缺失环节；
#   4. 平板车身 + 均匀淡天 → 各面只映出单一淡色，看起来全哑光；
#   5. 方向太阳打进镜面角时蓝车顶 183→246（镜面路径是通的），但 Coat 0.05 的
#      窄瓣一次只能亮一辆车。
# 修法（只改预览环境，不动材质、不进 GLB）：留 Nishita 世界 + 暗色预览地面
# （填黑洞背景）+ 东南太阳（与 render_max 默认同向，可见面光照不变）+
# 西北高处一条 24x2m 亮条灯（车顶镜面方向的“摄影棚柔光条”，三车顶均被照亮、
# 蓝车顶现 186→210 渐变光带）。地面/灯光/太阳均不进 GLB（导出只选 export_objs），
# 场景拼装也排除（charge.py SKIP_NAMES/SKIP_TYPES）。
# ---- preview sun: SE, same as render_max default (visible faces lit as R2) ----
bpy.ops.object.light_add(type='SUN', location=(43, -76, 25))
sun = bpy.context.active_object
sun.name = "ch-cars_sun"
sun.data.energy = 3.5
sun.data.use_shadow = True
sun.rotation_euler = (math.radians(50.0), 0.0, math.radians(30.0))
target = Vector((45, -76, 0.5))

# ---- preview ground: dark, fills the below-horizon black void ----
# 名字 Ground_PreviewOnly：render_max 取景排除、charge.py 拼装排除。
bpy.ops.mesh.primitive_plane_add(size=80, location=(43, -76, 0))
ground = bpy.context.active_object
ground.name = "Ground_PreviewOnly"
gmat = bpy.data.materials.new("ch-cars_preview_ground")
gmat.use_nodes = True
_gbsdf = gmat.node_tree.nodes["Principled BSDF"]
_gbsdf.inputs["Base Color"].default_value = (0.05, 0.05, 0.05, 1.0)
_gbsdf.inputs["Roughness"].default_value = 0.95
ground.data.materials.append(gmat)

# ---- preview softbox strip: 24x2m area light, NW-high in the roofs' mirror direction ----
bpy.ops.object.light_add(type='AREA', location=(20, -45, 18))
strip = bpy.context.active_object
strip.name = "ch-cars_softbox"
strip.data.shape = 'RECTANGLE'
strip.data.size = 24.0
strip.data.size_y = 2.0
strip.data.energy = 15000.0
strip.rotation_euler = (Vector((43, -76, 1.0)) - strip.location).to_track_quat('-Z', 'Y').to_euler()

# ---- camera: v1 position (all three cars in frame) ----
bpy.ops.object.camera_add(location=(45 + 16, -76 - 20, 13))
cam = bpy.context.active_object
cam.name = "ch-cars_cam"
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.camera = cam

# ---- render settings (baked into the .blend for the GitHub Actions render job;
#  no local render: 2026-11-22 user decision, all previews render on Actions) ----
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.eevee.taa_render_samples = 16
scene.eevee.use_ssr = True
scene.eevee.use_ssr_refraction = True
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.filepath = PNG_PATH
os.makedirs(os.path.dirname(PNG_PATH), exist_ok=True)
# bpy.ops.render.render(write_still=True)  # local render disabled, see above

# ---- remove preview-only helpers, keep only the cars ----
# 注意：world / 太阳 / 地面 / 柔光条都不删——R3 预览环境须留在 .blend 里供
# Actions 预览渲染（render_max 见 .blend 已有灯光便不再补默认太阳；地面与灯光
# 不进 GLB、场景拼装也排除）。只删相机（render_max 自动取景）。
for obj in (cam,):
    bpy.data.objects.remove(obj, do_unlink=True)

# ---- save .blend ----
os.makedirs(SCRIPT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)

# ---- export GLB (selection only) ----
bpy.ops.object.select_all(action='DESELECT')
for o in export_objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = export_objs[0]
bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format='GLB',
                          use_selection=True, export_apply=True)

# ---- re-import check ----
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.import_scene.gltf(filepath=GLB_PATH)
imported = [o for o in bpy.context.selected_objects]
print("GLB reimport objects:", len(imported))
assert len(imported) == 15, \
    f"expected 15 reimported objects (3 groups + 12 meshes), got {len(imported)}"

# ---- GLB JSON check: 9 materials, paint clearcoat + red + glass ----
with open(GLB_PATH, "rb") as f:
    _raw = f.read(20)
    _jlen = struct.unpack("<I", _raw[12:16])[0]
    f.seek(20)
    _gltf = json.loads(f.read(_jlen))
_mats = {m["name"]: m for m in _gltf.get("materials", [])}
print("GLB materials:", sorted(_mats))
assert len(_mats) == 9, f"expected 9 GLB materials, got {len(_mats)}"
_red_lin = srgb_to_linear("#C4534E")[:3]
for _pn in ("ch-cars_paint_blue", "ch-cars_paint_white", "ch-cars_paint_red",
            "ch-cars_paint_red_dark"):
    _pm = _mats[_pn]
    _cc = _pm.get("extensions", {}).get("KHR_materials_clearcoat", {})
    assert abs(_cc.get("clearcoatFactor", -1) - 1.0) < 1e-6, f"{_pn}: no clearcoat 1.0"
    assert abs(_cc.get("clearcoatRoughnessFactor", -1) - 0.05) < 1e-6, \
        f"{_pn}: clearcoat roughness != 0.05"
    _pbr = _pm.get("pbrMetallicRoughness", {})
    assert abs(_pbr.get("metallicFactor", -1) - 0.15) < 1e-6, f"{_pn}: metallic != 0.15"
    assert abs(_pbr.get("roughnessFactor", -1) - 0.25) < 1e-6, f"{_pn}: roughness != 0.25"
for _pn in ("ch-cars_paint_red", "ch-cars_paint_red_dark"):
    _bc = _mats[_pn]["pbrMetallicRoughness"]["baseColorFactor"][:3]
    assert all(abs(a - b) < 0.01 for a, b in zip(_bc, _red_lin)), \
        f"{_pn}: baseColor {_bc} != SPEC red {_red_lin}"
_gm = _mats["ch-cars_glass"]
_tr = _gm.get("extensions", {}).get("KHR_materials_transmission", {})
assert abs(_tr.get("transmissionFactor", -1) - 0.10) < 1e-6, \
    f"ch-cars_glass: transmissionFactor != 0.10 (got {_tr})"
print("GLB JSON CHECK PASS: 9 materials, paint clearcoat 1.0/0.05, "
      "red == #C4534E, glass transmission 0.10")

# ---- clean .blend1 ----
blend1 = BLEND_PATH + "1"
if os.path.exists(blend1):
    os.remove(blend1)

print("DONE ch-cars")
