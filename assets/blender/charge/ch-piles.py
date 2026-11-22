# ch-piles: 4x DC charging piles, charging area, Blender coords (x east, y north, z up, metres)
# Charge area centre Blender (44, -76). Piles at x=38, 41.5, 45, 48.5, y=-73.25
# (moved 2026-11-22: north of the bays, outside the bay north line -73.50,
#  so piles no longer intersect the V2G cars; car north end is -73.75).
# Only piles + gun cables + concrete plinths. No cars, no bay lines, no canopy.
# Texture pass (2026-11-22): procedural textures only, geometry/camera untouched.
#   - white paint: BRUSHED metal streaks (noise stretched vertically via Mapping)
#     + patchy roughness + slight Bump
#   - screen glass: light blue-grey + specular/coat + cubemap reflection (no longer black slab)
#   - cable rubber: dark rubber, noise roughness + grain bump
#   - plinth concrete: speckled variation + granular bump
#   - preview ground asphalt: Noise grain + wear patches + uneven light/dark
# Order: save .blend + export .glb. NO local render in this script
# (2026-11-22 user decision: all previews render on GitHub Actions).
# Render settings are baked into the .blend so the Actions job picks them up;
# the temp preview ground material below is kept for that Actions render job.
import bpy, math, os
from mathutils import Vector

ROOT = os.path.expanduser("~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
BLEND = os.path.join(ROOT, "assets/blender/charge/ch-piles.blend")
GLB = os.path.join(ROOT, "assets/models/ch-piles.glb")
PNG = os.path.join(ROOT, "screenshots/blender/ch-piles.png")
for d in (os.path.dirname(BLEND), os.path.dirname(GLB), os.path.dirname(PNG)):
    os.makedirs(d, exist_ok=True)

def srgb2lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def hex2lin(h):
    h = h.lstrip("#")
    return tuple(srgb2lin(int(h[i:i+2], 16) / 255.0) for i in (0, 2, 4)) + (1.0,)

def mat(name, hexcol, rough=0.6, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = hex2lin(hexcol)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    return m

def _noise(nt, name, scale, detail=2.0, roughness=0.7):
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.name = name
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    n.inputs["Roughness"].default_value = roughness
    return n

def _ramp(nt, name, stops):
    """stops: list of (position, hexcolor) sorted by position ascending."""
    r = nt.nodes.new("ShaderNodeValToRGB")
    r.name = name
    cr = r.color_ramp
    while len(cr.elements) < len(stops):
        cr.elements.new(0.5)
    for el, (pos, col) in zip(cr.elements, stops):
        el.position = pos
        el.color = hex2lin(col)
    return r

def _bump(nt, name, noise_node, strength, distance):
    b = nt.nodes.new("ShaderNodeBump")
    b.name = name
    b.inputs["Strength"].default_value = strength
    b.inputs["Distance"].default_value = distance
    nt.links.new(noise_node.outputs["Fac"], b.inputs["Height"])
    return b

def mat_white_textured():
    """White paint with BRUSHED-METAL streaks: noise stretched vertically
    (Mapping scale x/y large, z small) so streaks run along the pile height,
    plus patchy roughness variation and a fine orange-peel bump."""
    m = bpy.data.materials.new("ch-piles_white")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    # stretched coordinates -> vertical brushed streaks
    tc = nt.nodes.new("ShaderNodeTexCoord")
    tc.name = "texcoord"
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.name = "mapping_brush"
    mp.inputs["Scale"].default_value = (28.0, 28.0, 1.2)
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    # base colour: faint brushed tonal variation, stays near #E8E8E8
    n_tint = _noise(nt, "noise_tint", 6.0, 2.0, 0.7)
    nt.links.new(mp.outputs["Vector"], n_tint.inputs["Vector"])
    r_tint = _ramp(nt, "ramp_tint", [(0.0, "#D9D9D9"), (1.0, "#F6F6F6")])
    nt.links.new(n_tint.outputs["Fac"], r_tint.inputs["Fac"])
    nt.links.new(r_tint.outputs["Color"], bsdf.inputs["Base Color"])
    # roughness: streaky 0.32 .. 0.60 (brushed metal reads as uneven sheen)
    n_rough = _noise(nt, "noise_rough", 10.0, 3.0, 0.7)
    nt.links.new(mp.outputs["Vector"], n_rough.inputs["Vector"])
    r_rough = _ramp(nt, "ramp_rough", [(0.0, "#525252"), (1.0, "#999999")])
    nt.links.new(n_rough.outputs["Fac"], r_rough.inputs["Fac"])
    nt.links.new(r_rough.outputs["Color"], bsdf.inputs["Roughness"])
    # slight bump: fine orange-peel
    n_bump = _noise(nt, "noise_bump", 25.0, 2.0, 0.7)
    b = _bump(nt, "bump_paint", n_bump, 0.4, 0.015)
    nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Metallic"].default_value = 0.0
    return m

def mat_rubber_textured():
    """Charging cable rubber: dark, fine noise roughness + grain bump."""
    m = bpy.data.materials.new("ch-piles_rubber")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = hex2lin("#1C1C1C")
    n_rough = _noise(nt, "noise_rough", 40.0, 3.0, 0.8)
    r_rough = _ramp(nt, "ramp_rough", [(0.0, "#B3B3B3"), (1.0, "#FFFFFF")])
    nt.links.new(n_rough.outputs["Fac"], r_rough.inputs["Fac"])
    nt.links.new(r_rough.outputs["Color"], bsdf.inputs["Roughness"])
    n_bump = _noise(nt, "noise_grain", 90.0, 2.0, 0.8)
    b = _bump(nt, "bump_rubber", n_bump, 0.5, 0.008)
    nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Metallic"].default_value = 0.0
    return m

def mat_concrete_textured():
    """Plinth concrete: speckled grey variation + granular bump."""
    m = bpy.data.materials.new("ch-piles_concrete")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    n_tint = _noise(nt, "noise_tint", 9.0, 3.0, 0.7)
    r_tint = _ramp(nt, "ramp_tint", [(0.0, "#A39D92"), (0.5, "#B9B3A8"),
                                     (1.0, "#C9C3B6")])
    nt.links.new(n_tint.outputs["Fac"], r_tint.inputs["Fac"])
    nt.links.new(r_tint.outputs["Color"], bsdf.inputs["Base Color"])
    n_rough = _noise(nt, "noise_rough", 60.0, 2.0, 0.8)
    r_rough = _ramp(nt, "ramp_rough", [(0.0, "#D9D9D9"), (1.0, "#FFFFFF")])
    nt.links.new(n_rough.outputs["Fac"], r_rough.inputs["Fac"])
    nt.links.new(r_rough.outputs["Color"], bsdf.inputs["Roughness"])
    n_bump = _noise(nt, "noise_grain", 70.0, 2.0, 0.8)
    b = _bump(nt, "bump_concrete", n_bump, 0.6, 0.02)
    nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Metallic"].default_value = 0.0
    return m

def mat_screen_glass():
    """Screen glass: light blue-grey (SPEC glass #9FC3D8 family), low roughness,
    full specular + clearcoat so sun/sky reflect; slight alpha, NOT a black slab."""
    m = bpy.data.materials.new("ch-piles_screen")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    n_tint = _noise(nt, "noise_sheen", 4.0, 2.0, 0.6)
    r_tint = _ramp(nt, "ramp_sheen", [(0.0, "#7FA3B8"), (1.0, "#AAC7D8")])
    nt.links.new(n_tint.outputs["Fac"], r_tint.inputs["Fac"])
    nt.links.new(r_tint.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.06
    bsdf.inputs["Metallic"].default_value = 0.0
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 1.0
    if "Coat weight" in bsdf.inputs:
        bsdf.inputs["Coat weight"].default_value = 1.0
    if "Coat roughness" in bsdf.inputs:
        bsdf.inputs["Coat roughness"].default_value = 0.05
    bsdf.inputs["Alpha"].default_value = 0.95
    # transparency method (4.2 renamed blend_method -> surface_render_method)
    try:
        m.surface_render_method = "BLENDED"
    except Exception:
        try:
            m.blend_method = "BLEND"
        except Exception as e:
            print("screen blend method skipped:", e)
    return m

def mat_asphalt_textured():
    """Preview ground asphalt (Actions render job only, never in .blend/.glb):
    large wear patches + fine grain bump + speckled roughness."""
    m = bpy.data.materials.new("ch-piles_temp_ground")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    # uneven light/dark + worn lighter patches (large-scale noise, SPEC asphalt #424A52 mid)
    n_patch = _noise(nt, "noise_patch", 4.0, 2.0, 0.7)
    r_patch = _ramp(nt, "ramp_patch", [(0.0, "#2F3338"), (0.45, "#424A52"),
                                       (0.7, "#565E66"), (1.0, "#3A4046")])
    nt.links.new(n_patch.outputs["Fac"], r_patch.inputs["Fac"])
    nt.links.new(r_patch.outputs["Color"], bsdf.inputs["Base Color"])
    # speckled roughness 0.85 .. 1.0 (fine noise)
    n_rough = _noise(nt, "noise_rough", 120.0, 2.0, 0.8)
    r_rough = _ramp(nt, "ramp_rough", [(0.0, "#D9D9D9"), (1.0, "#FFFFFF")])
    nt.links.new(n_rough.outputs["Fac"], r_rough.inputs["Fac"])
    nt.links.new(r_rough.outputs["Color"], bsdf.inputs["Roughness"])
    # fine grain bump
    n_bump = _noise(nt, "noise_grain", 250.0, 2.0, 0.8)
    b = _bump(nt, "bump_grain", n_bump, 0.6, 0.01)
    nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Metallic"].default_value = 0.0
    return m

WHITE = mat_white_textured()
DARK = mat("ch-piles_darkbase", "#3A3F45", 0.7)
BLACK = mat("ch-piles_black", "#141414", 0.35)
SCREEN = mat_screen_glass()
CONC = mat_concrete_textured()
RUBBER = mat_rubber_textured()
GREEN = mat("ch-piles_led", "#46A04E", 0.4)

# clean scene
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for coll in (bpy.data.meshes, bpy.data.curves, bpy.data.cameras, bpy.data.lights):
    pass

def box(name, loc, size, material, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.active_object
    o.name = name
    o.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0:
        mod = o.modifiers.new("bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 2
    o.data.materials.append(material)
    return o

pile_objs = []
XS = [38.0, 41.5, 45.0, 48.5]
Y = -73.25
for i, cx in enumerate(XS):
    p = f"ch-piles_p{i+1}"
    # concrete plinth 0.8 x 0.6 x 0.1
    pile_objs.append(box(p + "_plinth", (cx, Y, 0.05), (0.8, 0.6, 0.1), CONC))
    # dark grey base 0.55 x 0.45 x 0.12
    pile_objs.append(box(p + "_base", (cx, Y, 0.16), (0.55, 0.45, 0.12), DARK))
    # white body 0.6 x 0.5 x 1.6, sits on base (z 0.22 .. 1.82)
    pile_objs.append(box(p + "_body", (cx, Y, 1.02), (0.6, 0.5, 1.6), WHITE, bevel=0.02))
    # dark top cap
    pile_objs.append(box(p + "_cap", (cx, Y, 1.845), (0.62, 0.52, 0.05), DARK))
    # front screen frame + glass screen on south face (y- side, facing parking)
    pile_objs.append(box(p + "_screenframe", (cx, Y - 0.255, 1.25), (0.36, 0.015, 0.46), DARK))
    pile_objs.append(box(p + "_screen", (cx, Y - 0.265, 1.25), (0.30, 0.02, 0.40), SCREEN))
    # green status LED on front, above screen
    pile_objs.append(box(p + "_led", (cx, Y - 0.258, 1.62), (0.05, 0.015, 0.05), GREEN))
    # charging gun: small black box on +x side face + nozzle tip below
    pile_objs.append(box(p + "_gun", (cx + 0.33, Y, 1.18), (0.10, 0.18, 0.30), BLACK, bevel=0.015))
    pile_objs.append(box(p + "_gun_nozzle", (cx + 0.33, Y, 0.99), (0.07, 0.10, 0.10), BLACK))
    # cable: black tube from pile top, hanging down in a U to the gun
    cu = bpy.data.curves.new(p + "_cable_curve", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 0.018
    cu.bevel_resolution = 2
    cu.resolution_u = 4
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(3)
    pts = [
        (cx + 0.28, Y, 1.80),   # leaves pile top edge
        (cx + 0.40, Y, 1.35),   # drops down the +x side
        (cx + 0.42, Y, 0.95),   # bottom of the U
        (cx + 0.36, Y, 1.10),   # back up to the gun
    ]
    for bp, co in zip(sp.bezier_points, pts):
        bp.co = co
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
    co_obj = bpy.data.objects.new(p + "_cable", cu)
    bpy.context.collection.objects.link(co_obj)
    co_obj.data.materials.append(RUBBER)
    pile_objs.append(co_obj)

# ---- lighting (SPEC section 2) ----
sun_data = bpy.data.lights.new("sun", "SUN")
sun_data.energy = 3.5
sun_data.use_shadow = True
sun = bpy.data.objects.new("sun", sun_data)
bpy.context.collection.objects.link(sun)
sun.rotation_euler = (math.radians(40), 0, math.radians(225))  # from southwest, ~50 deg elevation

world = bpy.data.worlds.new("world")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.65, 0.78, 0.88, 1.0)
bg.inputs["Strength"].default_value = 1.0

# ---- reflection probe so the glass screens pick up the sky/surroundings ----
# (data-API creation: bpy.ops.object.lightprobe_add silently failed in the
#  14:08 background run and no probe landed in the .blend)
try:
    lp_data = bpy.data.lightprobes.new("ch-piles_reflection_probe", "SPHERE")
    probe = bpy.data.objects.new("ch-piles_reflection_probe", lp_data)
    bpy.context.collection.objects.link(probe)
    probe.location = (43.25, Y, 1.5)
    if hasattr(probe.data, "influence_distance"):
        probe.data.influence_distance = 14.0
except Exception as e:
    print("reflection probe skipped:", e)

# ---- preview camera: 45 deg view from the south-east so screens + guns read ----
# (unchanged from the verified framing: all 4 piles in frame)
target = Vector((43.25, Y, 0.9))
cam_data = bpy.data.cameras.new("cam")
cam_data.lens = 35
cam = bpy.data.objects.new("cam", cam_data)
bpy.context.collection.objects.link(cam)
cam.location = Vector((43.25, Y - 12.0, 7.0))
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
bpy.context.scene.camera = cam

# ---- render settings baked into the .blend for the GitHub Actions render job
# (no bpy.ops.render call here: local rendering is disabled by user decision)
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100
scene.render.filepath = PNG
scene.eevee.taa_render_samples = 16
# reflections for the glass screens (Eevee Next raytracing + cubemap probe)
for _attr in ("use_ssr", "use_raytracing"):
    if hasattr(scene.eevee, _attr):
        try:
            setattr(scene.eevee, _attr, True)
        except Exception as e:
            print("eevee reflection opt skipped:", _attr, e)
scene.render.image_settings.file_format = "PNG"

# ---- STEP 1: save + export (memory is tight, restarts are frequent) ----
# save blend (piles only + lights/camera/probe kept in blend; export is selection-only)
bpy.ops.wm.save_as_mainfile(filepath=BLEND)

# export selection only (40 pile objects)
bpy.ops.object.select_all(action="DESELECT")
for o in pile_objs:
    o.select_set(True)
bpy.ops.export_scene.gltf(filepath=GLB, export_format="GLB",
                           use_selection=True, export_apply=True)
print("exported GLB objects:", len(pile_objs))

# re-import check
bpy.ops.object.select_all(action="DESELECT")
bpy.ops.import_scene.gltf(filepath=GLB)
imported = [o for o in bpy.context.selected_objects]
print("GLB reimport objects:", len(imported))

# cleanup .blend1
blend1 = BLEND + "1"
if os.path.exists(blend1):
    os.remove(blend1)

print("DONE ch-piles")
