import bpy
import math
import os
from mathutils import Vector

ROOT = os.path.expanduser(
    "~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
SCRIPT_DIR = os.path.join(ROOT, "assets/blender/charge")
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


def _noise_roughness(ntree, bsdf, scale, r_min, r_max):
    """Noise Texture -> Map Range -> Roughness (r_mid +/- spread)."""
    tex = ntree.nodes.new("ShaderNodeTexCoord")
    noise = ntree.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 2.0
    noise.inputs["Roughness"].default_value = 0.7
    ntree.links.new(tex.outputs["Generated"], noise.inputs["Vector"])
    rng = ntree.nodes.new("ShaderNodeMapRange")
    rng.inputs["From Min"].default_value = 0.0
    rng.inputs["From Max"].default_value = 1.0
    rng.inputs["To Min"].default_value = r_min
    rng.inputs["To Max"].default_value = r_max
    ntree.links.new(noise.outputs["Fac"], rng.inputs["Value"])
    ntree.links.new(rng.outputs["Result"], bsdf.inputs["Roughness"])


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
    """Car paint: Principled, Roughness 0.35 solid + light bump.
    2026-11-23 返工：旧版 Roughness 连 Noise->MapRange（0.27~0.43），glTF 丢
    roughnessFactor，Godot 里车漆粗糙度归 1（全哑光）；改回区间中值 0.35
    固定值，只留 Bump。Base Color 本就未链接，不动。
    2026-11-24 返工：参数化车漆——Metallic 0.15 / Roughness 0.35 不变（仍不
    链接，保证 glTF factor 保留），加清漆层 Coat Weight 1.0 / Coat Roughness
    0.15（glTF KHR_materials_clearcoat），珠光片只走细颗粒 Bump（scale 40、
    strength 0.10）。不贴平铺纹理：碎砖式平铺会毁车漆面。
    2026-11-24 返工 R1（验收 run #72：GLB 里 clearcoat 明明在，EEVEE 预览仍
    全哑光——根因是预览只有单太阳+纯色平坦世界，清漆层无物可映、0.15 的
    涂层高光又被 0.35 的底漆粗糙度冲淡，见汇报；Godot 04-charge 远景也看
    不出光泽）：Coat Roughness 0.15→0.05、底漆 Roughness 0.35→0.25，
    清漆高光更锐更亮，Godot 侧同向变亮，不改色、不改结构。"""
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
    """Tinted car glass (2026-11-24 glass fix, R3 leftover):
    R3 acceptance: side windows had a sky gradient (top (200,214,232) /
    bottom (101,142,181)) but still read as a flat pale grey-green slab,
    no bright band. Root cause: vertical faces, seen from the SE camera,
    mirror toward the ground below the horizon, so they reflect dark
    ground -- and Transmission 0.9 let the dark interior dominate.
    Fix (glass material only, paint + preview studio untouched):
    Transmission 0.9 -> 0.10 (stop seeing the dark interior),
    Base Color #9FC3D8 -> #33505F dark tint (dark field so the bright
    horizon glow / lit-ground reflection reads as a band, not a wash),
    Roughness 0.06 -> 0.15 (a SHARPER mirror would only mirror the dark
    ground more faithfully; a slightly wider lobe blends in the bright
    near-horizon sky glow), Specular IOR Level 0.5 -> 1.0 (stronger
    Fresnel, grazing top brighter). Metallic stays 0.
    The old 35% Glass BSDF mix is dropped: it is not exported to glTF
    (only the Principled BSDF survives), and its pale #BFD4DE refraction
    diluted the tint in EEVEE -- Principled-only keeps EEVEE == GLB ==
    Godot."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    ntree = mat.node_tree
    bsdf = ntree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = srgb_to_linear("#33505F")
    bsdf.inputs["Roughness"].default_value = 0.15
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Transmission Weight"].default_value = 0.10
    bsdf.inputs["Specular IOR Level"].default_value = 1.0
    bsdf.inputs["IOR"].default_value = 1.45
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
    """Metal hub: metallic ~0.8, roughness 0.35 solid.
    2026-11-23 返工：旧版 Roughness 连 Noise->MapRange，glTF 丢 roughnessFactor；
    改回 0.35 固定值。"""
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


def make_dark(name, hexstr="#3A3F42", roughness=0.7):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = srgb_to_linear(hexstr)
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


MAT_GLASS = make_glass("ch-cars_glass")
MAT_TIRE = make_tire("ch-cars_tire")
MAT_HUB = make_hub("ch-cars_hub")
MAT_HEAD = make_lamp("ch-cars_headlamp", "#FFF6D8", "#FFF2CC", strength=1.0)
MAT_TAIL = make_lamp("ch-cars_taillamp", "#C03028", "#D04030", strength=0.8)
MAT_DARK = make_dark("ch-cars_dark")


def box(name, loc, dims, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False,
                                   scale=True)
    if bevel > 0:
        mod = obj.modifiers.new(name="bevel", type='BEVEL')
        mod.width = bevel
        mod.segments = 3
    if mat:
        obj.data.materials.append(mat)
    return obj


def wheel(name, loc):
    """Tire cylinder + metal hub disc + 5 spokes per outer face."""
    parts = []
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.33, depth=0.22,
                                        location=loc)
    tire = bpy.context.active_object
    tire.name = name + "_tire"
    tire.rotation_euler = (math.radians(90), 0, 0)  # axis along Y
    tire.data.materials.append(MAT_TIRE)
    parts.append(tire)
    # hub disc, slightly proud of the tire on both sides
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.19, depth=0.24,
                                        location=loc)
    hub = bpy.context.active_object
    hub.name = name + "_hub"
    hub.rotation_euler = (math.radians(90), 0, 0)
    hub.data.materials.append(MAT_HUB)
    parts.append(hub)
    # 5 spokes on each outer face, radiating in the XZ plane
    for side in (+1, -1):
        for k in range(5):
            ang = math.radians(k * 72.0)
            sp = box("%s_spoke_%s%d" % (name, "L" if side > 0 else "R", k),
                     (loc[0], loc[1] + side * 0.125, loc[2]),
                     (0.34, 0.02, 0.08), MAT_HUB, bevel=0.0)
            sp.rotation_euler = (0, ang, 0)
            parts.append(sp)
    return parts


def make_car(tag, color_hex, cx, cy, rot_z_deg):
    """Local car: length along X, front at +X. rot_z rotates whole car."""
    mat_body = make_paint("ch-cars_body_" + tag, color_hex)
    parts = []
    # body 4.5 x 1.8 x 0.55, centre z 0.60, bevelled
    parts.append(box("ch-cars_%s_body" % tag, (0, 0, 0.60),
                     (4.5, 1.8, 0.55), mat_body, bevel=0.04))
    # roof 2.2 x 1.6 x 0.5, centre z 1.125, slightly rearward (x -0.2)
    parts.append(box("ch-cars_%s_roof" % tag, (-0.2, 0, 1.125),
                     (2.2, 1.6, 0.5), mat_body, bevel=0.04))
    # layered glass (no longer one black band):
    #  front side windows + rear side windows, per side (B-pillar gap)
    for side in (+1, -1):
        s = "L" if side > 0 else "R"
        parts.append(box("ch-cars_%s_glass_front_%s" % (tag, s),
                         (0.35, side * 0.805, 1.12),
                         (0.85, 0.02, 0.35), MAT_GLASS))
        parts.append(box("ch-cars_%s_glass_rear_%s" % (tag, s),
                         (-0.75, side * 0.805, 1.12),
                         (0.85, 0.02, 0.35), MAT_GLASS))
    # windshield (front of roof) + rear window
    parts.append(box("ch-cars_%s_glass_wind" % tag,
                     (0.91, 0, 1.12), (0.02, 1.40, 0.38), MAT_GLASS))
    parts.append(box("ch-cars_%s_glass_back" % tag,
                     (-1.31, 0, 1.12), (0.02, 1.40, 0.38), MAT_GLASS))
    # headlights (front, +X) and taillights (rear, -X), weak emission
    for side in (+1, -1):
        s = "L" if side > 0 else "R"
        parts.append(box("ch-cars_%s_head_%s" % (tag, s),
                         (2.26, side * 0.55, 0.78),
                         (0.06, 0.50, 0.12), MAT_HEAD))
        parts.append(box("ch-cars_%s_tail_%s" % (tag, s),
                         (-2.26, side * 0.55, 0.78),
                         (0.06, 0.50, 0.12), MAT_TAIL))
    # front grille
    parts.append(box("ch-cars_%s_grille" % tag,
                     (2.26, 0, 0.45), (0.06, 1.20, 0.15), MAT_DARK))
    # mirrors: stalk + head at the A-pillar, both sides
    for side in (+1, -1):
        s = "L" if side > 0 else "R"
        parts.append(box("ch-cars_%s_mirror_stalk_%s" % (tag, s),
                         (0.75, side * 0.90, 1.02),
                         (0.10, 0.14, 0.05), MAT_DARK))
        parts.append(box("ch-cars_%s_mirror_%s" % (tag, s),
                         (0.75, side * 0.98, 1.04),
                         (0.16, 0.06, 0.14), mat_body, bevel=0.02))
    # 4 wheels, r 0.33, at x +-1.5, y +-0.80, z 0.33
    for i, wx in enumerate((-1.5, 1.5)):
        for j, wy in enumerate((-0.80, 0.80)):
            parts.extend(wheel("ch-cars_%s_wheel_%d%d" % (tag, i, j),
                               (wx, wy, 0.33)))
    # group under an empty so rotation/placement is one transform
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(cx, cy, 0))
    grp = bpy.context.active_object
    grp.name = "ch-cars_%s" % tag
    grp.rotation_euler = (0, 0, math.radians(rot_z_deg))
    for p in parts:
        p.parent = grp
    return grp


# ---- cars (positions unchanged from v1) ----
# Blue V2G at x=38, red V2G at x=45: front faces the piles, i.e. -Y.
# Local front is +X, so rotate -90 deg about Z (+X -> -Y).
make_car("blue", "#3B82C4", 38, -76, -90)
make_car("red", "#C4534E", 45, -76, -90)
# White non-V2G moved into empty bay 4 (x=48.5), front toward -Y like blue/red.
# (2026-11-22 fix: was at x=52 outside bay 4, facing +Y; now -90 deg = south.)
make_car("white", "#D7DDE3", 48.5, -76, -90)

car_objs = [o for o in bpy.data.objects
            if o.name.startswith("ch-cars_")]
print("car objects:", len(car_objs))

# ---- 材质校验（2026-11-23 返工防回归）：导出件的 Base Color/Roughness
#   一律不链接程序化节点，否则 glTF 丢 baseColorFactor/roughnessFactor ----
for _m in [m for m in bpy.data.materials
           if m.name.startswith("ch-cars_body_") or m.name == "ch-cars_hub"]:
    _bsdf = _m.node_tree.nodes["Principled BSDF"]
    assert not _bsdf.inputs["Base Color"].is_linked, f"{_m.name}: Base Color linked!"
    assert not _bsdf.inputs["Roughness"].is_linked, f"{_m.name}: Roughness linked!"
    if _m.name.startswith("ch-cars_body_"):
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
assert abs(_g.inputs["Roughness"].default_value - 0.15) < 1e-6, \
    "ch-cars_glass: Roughness != 0.15"
assert abs(_g.inputs["Specular IOR Level"].default_value - 1.0) < 1e-6, \
    "ch-cars_glass: Specular IOR Level != 1.0"
print("GLASS CHECK PASS: transmission 0.10 / roughness 0.15 / specular 1.0")

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
# 蓝车顶现 186→210 渐变光带）。地面/灯光/太阳均不进 GLB（导出只选 car_objs），
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
for o in car_objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = car_objs[0]
bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format='GLB',
                          use_selection=True, export_apply=True)

# ---- re-import check ----
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.import_scene.gltf(filepath=GLB_PATH)
imported = [o for o in bpy.context.selected_objects]
print("GLB reimport objects:", len(imported))

# ---- clean .blend1 ----
blend1 = BLEND_PATH + "1"
if os.path.exists(blend1):
    os.remove(blend1)

print("DONE ch-cars")
