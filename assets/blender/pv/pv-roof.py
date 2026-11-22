# pv-roof: roof waterproof membrane + drains + maintenance walkways
# Buildings (Blender coords, from SPEC + measured slab tops):
#   A block (-56, 30) 40x15 m, slab top z=18.35, parapet top 19.0
#   B block (-12, 30) 32x14 m, slab top z=18.35, parapet top 19.0
#   Lab   (-28, 62) 42x12 m, slab top z=12.30, parapet top 13.0
# Only the membrane layer, drains and walkways are built here.
# Roof slab and parapet belong to ov-bldA/B/C and are NOT built here
# (dummy slab + parapet are added for the preview only, and excluded
# from the .glb export).
import bpy, math, os
from mathutils import Vector

BASE = os.path.expanduser("~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
BLEND = os.path.join(BASE, "assets/blender/pv/pv-roof.blend")
GLB   = os.path.join(BASE, "assets/models/pv-roof.glb")
PNG   = os.path.join(BASE, "screenshots/blender/pv-roof.png")

# ---- clean scene ----
bpy.ops.wm.read_factory_settings(use_empty=True)
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def srgb_to_linear(hexstr):
    h = hexstr.lstrip('#')
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i+2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return tuple(out) + (1.0,)

def make_mat(name, hexstr, rough=0.9, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = srgb_to_linear(hexstr)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    return m

MAT_MEMBRANE = make_mat("pv_roof_membrane", "#8A8F94", rough=0.95)
MAT_DRAIN    = make_mat("pv_roof_drain",    "#424A52", rough=0.8)
MAT_WALK     = make_mat("pv_roof_walkway",  "#D8D2C4", rough=0.95)
MAT_DUMMY_SLAB    = make_mat("pv_roof_dummy_slab",    "#424A52", rough=0.9)
MAT_DUMMY_PARAPET = make_mat("pv_roof_dummy_parapet", "#6B7280", rough=0.9)

EXPORT_OBJS = []

def box(name, loc, dims, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.active_object
    o.name = name
    o.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    if bevel > 0:
        mod = o.modifiers.new("bevel", 'BEVEL')
        mod.width = bevel
        mod.segments = 2
    EXPORT_OBJS.append(o)
    return o

def cyl(name, loc, radius, depth, mat):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=loc, vertices=16)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(mat)
    EXPORT_OBJS.append(o)
    return o

# Parapet wall thickness (assumed, ov-bld* uses the same): membrane
# is inset by this amount so it sits just inside the parapet.
PARAPET_T = 0.3
MEMBRANE_T = 0.05
WALK_W = 0.8
WALK_T = 0.02

# (name, cx, cy, length_x, width_y, slab_top_z)
ROOFS = [
    ("A",   -56, 30, 40, 15, 18.35),
    ("B",   -12, 30, 32, 14, 18.35),
    ("lab", -28, 62, 42, 12, 12.30),
]

for tag, cx, cy, L, W, ztop in ROOFS:
    ml = L - 2 * PARAPET_T      # membrane length
    mw = W - 2 * PARAPET_T      # membrane width
    mz = ztop + MEMBRANE_T / 2  # membrane centre z
    # 1) waterproof membrane, 0.05 m thick, top flush at ztop + 0.05
    box(f"pv-roof_membrane_{tag}", (cx, cy, mz), (ml, mw, MEMBRANE_T),
        MAT_MEMBRANE, bevel=0.02)
    # 2) maintenance walkways: one strip along the north edge, one
    #    along the south edge, 0.8 m wide, sitting on the membrane.
    walk_len = ml - 2.0
    for side in (+1, -1):
        wy = cy + side * (mw / 2 - PARAPET_T - WALK_W / 2)
        box(f"pv-roof_walkway_{tag}_{'N' if side > 0 else 'S'}",
            (cx, wy, ztop + MEMBRANE_T + WALK_T / 2),
            (walk_len, WALK_W, WALK_T), MAT_WALK, bevel=0.01)
    # 3) drains: 4 per roof, near the corners but clear of the
    #    walkway strips (inset 1.5 m in x, 1.6 m in y from membrane edge).
    dx = ml / 2 - 1.5
    dy = mw / 2 - 1.6
    for i, (sx, sy) in enumerate(((+1, +1), (+1, -1), (-1, +1), (-1, -1)), 1):
        px, py = cx + sx * dx, cy + sy * dy
        # dark square grate, flush just above the membrane
        box(f"pv-roof_drain_{tag}_{i}",
            (px, py, ztop + MEMBRANE_T + 0.01),
            (0.3, 0.3, 0.02), MAT_DRAIN)
        # short vertical drain pipe stub rising from the grate
        cyl(f"pv-roof_drainpipe_{tag}_{i}",
            (px, py, ztop + MEMBRANE_T + 0.10),
            0.06, 0.16, MAT_DRAIN)

# ---- preview-only dummies (NOT exported): A-block slab + parapet ----
# Slab: dark grey, top at 18.35 (same as ov-bldA slab top).
bpy.ops.mesh.primitive_cube_add(location=(-56, 30, 18.35 - 0.15))
slab = bpy.context.active_object
slab.name = "PREVIEW_slab_A"
slab.dimensions = (40, 15, 0.3)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
slab.data.materials.append(MAT_DUMMY_SLAB)
# Parapet: 0.3 thick, 0.65 high (18.35 -> 19.0), around the perimeter.
for name, loc, dims in [
    ("PREVIEW_parapet_A_N", (-56, 30 + 7.5 - 0.15, 18.35 + 0.325), (40, 0.3, 0.65)),
    ("PREVIEW_parapet_A_S", (-56, 30 - 7.5 + 0.15, 18.35 + 0.325), (40, 0.3, 0.65)),
    ("PREVIEW_parapet_A_E", (-56 + 20 - 0.15, 30, 18.35 + 0.325), (0.3, 15 - 0.6, 0.65)),
    ("PREVIEW_parapet_A_W", (-56 - 20 + 0.15, 30, 18.35 + 0.325), (0.3, 15 - 0.6, 0.65)),
]:
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.active_object
    o.name = name
    o.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(MAT_DUMMY_PARAPET)

# ---- lighting (SPEC §2): sun 3.5 from SW, pale-blue world ----
world = bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.65, 0.78, 0.88, 1.0)
bg.inputs["Strength"].default_value = 1.0

bpy.ops.object.light_add(type='SUN', location=(-30, 0, 40))
sun = bpy.context.active_object
sun.data.energy = 3.5
sun.data.use_shadow = True
sun.rotation_euler = Vector((1, 1, -1)).to_track_quat('-Z', 'Y').to_euler()

# ---- preview camera: 45-degree view over the A-block roof ----
bpy.ops.object.camera_add(location=(-56 + 33, 30 - 40, 18.4 + 34))
cam = bpy.context.active_object
cam.name = "PreviewCamera"
target = Vector((-56, 30, 18.4))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.camera = cam

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.eevee.taa_render_samples = 16
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.filepath = PNG
scene.render.image_settings.file_format = 'PNG'

# ---- save .blend ----
bpy.ops.wm.save_as_mainfile(filepath=BLEND)

# ---- export .glb: only this piece's objects ----
bpy.ops.object.select_all(action='DESELECT')
for o in EXPORT_OBJS:
    o.select_set(True)
bpy.context.view_layer.objects.active = EXPORT_OBJS[0]
bpy.ops.export_scene.gltf(filepath=GLB, export_format='GLB',
                           use_selection=True, export_apply=True)

# ---- re-import the .glb to verify it opens ----
_before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB)
_new = [o for o in bpy.data.objects if o not in _before]
print("GLB re-import ok, new objects:", len(_new))
# remove the re-imported copies so the preview renders the originals only
for o in _new:
    bpy.data.objects.remove(o, do_unlink=True)

# ---- render preview ----
bpy.ops.render.render(write_still=True)
print("DONE pv-roof")
