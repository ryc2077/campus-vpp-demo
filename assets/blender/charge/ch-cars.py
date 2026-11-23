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
    strength 0.10）。不贴平铺纹理：碎砖式平铺会毁车漆面。"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    ntree = mat.node_tree
    bsdf = ntree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = srgb_to_linear(hexstr)
    bsdf.inputs["Metallic"].default_value = 0.15
    bsdf.inputs["Roughness"].default_value = 0.35
    bsdf.inputs["Coat Weight"].default_value = 1.0
    bsdf.inputs["Coat Roughness"].default_value = 0.15
    _noise_bump(ntree, bsdf, scale=40.0, strength=0.10)
    return mat


def make_glass(name):
    """Layered glass: Principled (Transmission ~0.9, pale blue-grey)
    mixed with Glass BSDF, so SSR/refraction shows in the render."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    ntree = mat.node_tree
    bsdf = ntree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = srgb_to_linear("#9FC3D8")
    bsdf.inputs["Roughness"].default_value = 0.06
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Transmission Weight"].default_value = 0.9
    bsdf.inputs["IOR"].default_value = 1.45
    glass = ntree.nodes.new("ShaderNodeBsdfGlass")
    glass.inputs["Color"].default_value = srgb_to_linear("#BFD4DE")
    glass.inputs["Roughness"].default_value = 0.05
    glass.inputs["IOR"].default_value = 1.45
    mix = ntree.nodes.new("ShaderNodeMixShader")
    mix.inputs[0].default_value = 0.35  # 35% Glass, 65% Principled
    out = ntree.nodes["Material Output"]
    ntree.links.new(bsdf.outputs["BSDF"], mix.inputs[1])
    ntree.links.new(glass.outputs["BSDF"], mix.inputs[2])
    ntree.links.new(mix.outputs["Shader"], out.inputs["Surface"])
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
        assert abs(_bsdf.inputs["Coat Roughness"].default_value - 0.15) < 1e-6, \
            f"{_m.name}: Coat Roughness != 0.15"
print("MATERIAL CHECK PASS: car paint + hub have solid Base Color + Roughness; "
      "car paint clearcoat Coat Weight 1.0 / Coat Roughness 0.15")

# ---- lighting / world (SPEC section 2) ----
world = bpy.data.worlds.new("ch-cars_world")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.65, 0.78, 0.88, 1.0)
bg.inputs["Strength"].default_value = 1.0

bpy.ops.object.light_add(type='SUN', location=(44 - 20, -76 - 20, 25))
sun = bpy.context.active_object
sun.name = "ch-cars_sun"
sun.data.energy = 3.5
sun.data.use_shadow = True
target = Vector((45, -76, 0.5))
direction = target - sun.location
sun.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

# ---- reflection cubemap (preview only, removed before save/export) ----
bpy.ops.object.lightprobe_add(type='SPHERE', location=(45, -76, 2.5))
probe = bpy.context.active_object
probe.name = "ch-cars_probe_tmp"

# ---- ground plane (preview only, removed before save/export) ----
bpy.ops.mesh.primitive_plane_add(size=40, location=(45, -76, 0))
ground = bpy.context.active_object
ground.name = "ch-cars_ground_tmp"
gmat = make_dark("ch-cars_ground_tmp", "#B9B3A8", roughness=0.95)
ground.data.materials.append(gmat)

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
for obj in (ground, sun, cam, probe):
    bpy.data.objects.remove(obj, do_unlink=True)
bpy.data.worlds.remove(world)

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
