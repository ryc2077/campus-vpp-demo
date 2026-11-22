# ov-gate: 南门门楼 + 门柱 + 伸缩门示意 + 围墙 (overview piece)
# Blender centre (0, -98, 0); x east, y north, z up; metres.
# Colours / lighting per SPEC.md. Gate, guard room, retractable gate,
# walls ONLY -- NO plaza paving (ov-road-walk), NO flag poles (ov-flag-lamp).
#
# Layout (from the aerial photo: south gate on the south main road,
# modest gatehouse, guard room east of the gate, dark flat roof):
# - two posts 1x1x6 m at x = +/-5.5 (inner faces at +/-5.0 -> 10 m opening)
# - lintel beam 12 m span (x -6..+6), z 5.0-6.2, 0.8 m thick, cream + red cap
# - guard room east, 6(x) x 4(y) x 3.5 m, centre (11, -98)
# - retractable gate: nominal 10 m frame, shown HALF-OPEN, gathered to the
#   east half of the opening (x 0..+5), dark grey thin-bar frame, 1.2 m high
# - walls 20 m each side of the posts, 2.2 m high, cream + red cap;
#   east run is 6-8 m + 14-26 m of wall with the guard room (x 8..14)
#   filling the middle 6 m of the same 20 m run

import bpy
import os
from mathutils import Vector

PIECE = "ov-gate"
BASE = os.path.expanduser("~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
PY_DIR = os.path.join(BASE, "assets/blender/overview")
BLEND_PATH = os.path.join(PY_DIR, "ov-gate.blend")
GLB_PATH = os.path.join(BASE, "assets/models/ov-gate.glb")
PNG_PATH = os.path.join(BASE, "screenshots/blender/ov-gate.png")

CX, CY = 0.0, -98.0   # gate centre (Blender x, y)


def hex_rgb(h):
    """Hex sRGB -> linear RGB (Blender stores Base Color linear)."""
    h = h.lstrip("#")

    def srgb_to_lin(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (srgb_to_lin(int(h[i:i + 2], 16)) for i in (0, 2, 4))
    return (r, g, b, 1.0)


def make_mat(name, hexcol, rough=0.85, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = hex_rgb(hexcol)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    return m


MAT_CREAM = make_mat("Wall_Cream_F3E9D2", "#F3E9D2", 0.85)
MAT_RED = make_mat("Red_8E2F28", "#8E2F28", 0.8)
MAT_ROOF = make_mat("Roof_DarkGrey_424A52", "#424A52", 0.9)
MAT_CONC = make_mat("Concrete_B9B3A8", "#B9B3A8", 0.95)
MAT_METAL = make_mat("MetalGrey_8A8F94", "#8A8F94", 0.55, 0.35)
MAT_DARK = make_mat("Gate_DarkGrey_424A52", "#424A52", 0.6, 0.4)
MAT_GLASS = make_mat("Glass_9FC3D8", "#9FC3D8", 0.15, 0.1)
MAT_GROUND = make_mat("Ground_Grass_69B45E", "#69B45E", 1.0)

# ---- clean scene ----
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

building = []  # objects that go into the .glb


def box(name, cx, cy, z0, z1, sx, sy, mat, bevel=0.03):
    bpy.ops.mesh.primitive_cube_add(location=(cx, cy, (z0 + z1) / 2.0))
    o = bpy.context.active_object
    o.name = name
    o.dimensions = (sx, sy, z1 - z0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel and min(sx, sy, z1 - z0) > 2 * bevel + 0.02:
        mod = o.modifiers.new("EdgeSoft", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        mod.limit_method = "ANGLE"
    o.data.materials.append(mat)
    building.append(o)
    return o


# ---- gate posts: 1x1x6 m at x = +/-5.5, cream + red top ----
for side, px in (("W", -5.5), ("E", 5.5)):
    box("gate_post_%s_base" % side, px, CY, 0.0, 0.25, 1.3, 1.3, MAT_CONC, bevel=0.02)
    box("gate_post_%s" % side, px, CY, 0.25, 5.9, 1.0, 1.0, MAT_CREAM, bevel=0.04)
    box("gate_post_%s_redband" % side, px, CY, 5.9, 6.2, 1.06, 1.06, MAT_RED, bevel=0.02)
    box("gate_post_%s_cap" % side, px, CY, 6.2, 6.38, 1.25, 1.25, MAT_RED, bevel=0.02)

# ---- lintel beam: 12 m span, z 5.0-6.2, 0.8 m thick, cream + red cap ----
box("gate_beam", CX, CY, 5.0, 6.2, 12.0, 0.8, MAT_CREAM, bevel=0.04)
box("gate_beam_cap", CX, CY, 6.2, 6.35, 12.2, 0.95, MAT_RED, bevel=0.02)
# thin cream cornice line under the beam
box("gate_beam_cornice", CX, CY, 4.82, 5.0, 12.2, 0.95, MAT_CONC, bevel=0.02)

# ---- guard room (east): 6 x 4 x 3.5 m, centre (11, -98) ----
GX, GY = 11.0, -98.0
box("guard_room_plinth", GX, GY, 0.0, 0.2, 6.3, 4.3, MAT_CONC, bevel=0.02)
box("guard_room_body", GX, GY, 0.2, 3.5, 6.0, 4.0, MAT_CREAM, bevel=0.04)
# flat dark-grey roof slab with overhang + thin red trim under it
box("guard_room_roof_trim", GX, GY, 3.5, 3.58, 6.3, 4.3, MAT_RED, bevel=0.02)
box("guard_room_roof", GX, GY, 3.58, 3.78, 6.4, 4.4, MAT_ROOF, bevel=0.02)
# window on the SOUTH face (faces the road, y = -100): 1.6 x 1.2 m glass
# with a dark frame; wall face at y = GY - 2.0
box("guard_window_frame", GX, GY - 2.02, 1.2, 2.4, 1.8, 0.08, MAT_DARK, bevel=0.01)
box("guard_window_glass", GX, GY - 2.05, 1.35, 2.25, 1.6, 0.06, MAT_GLASS, bevel=0.0)
box("guard_window_sill", GX, GY - 2.06, 1.1, 1.2, 1.9, 0.14, MAT_CONC, bevel=0.01)
# door on the NORTH face (faces the campus/plaza, y = -96): 0.9 x 2.1 m
box("guard_door", GX - 1.5, GY + 2.02, 0.2, 2.3, 0.95, 0.08, MAT_DARK, bevel=0.01)
box("guard_door_handle", GX - 1.15, GY + 2.08, 1.0, 1.15, 0.06, 0.1, MAT_METAL, bevel=0.0)
# small window on the WEST face (faces the gate, x = 8): 0.9 x 1.0 m
box("guard_window_w_frame", GX - 3.02, GY, 1.4, 2.4, 0.08, 1.1, MAT_DARK, bevel=0.01)
box("guard_window_w_glass", GX - 3.05, GY, 1.55, 2.25, 0.06, 0.9, MAT_GLASS, bevel=0.0)

# ---- retractable gate (half-open): thin-bar frame gathered to the east
# half of the 10 m opening (x 0..+5), z 0.1-1.3, dark grey.
# Top + bottom rails, vertical bars every 0.5 m, diagonal scissor bars,
# small wheels at the base and a drive head box at the east end.
GX0, GX1 = 0.0, 5.0
box("retract_gate_rail_top", (GX0 + GX1) / 2, CY, 1.15, 1.3, GX1 - GX0, 0.06, MAT_DARK, bevel=0.0)
box("retract_gate_rail_bottom", (GX0 + GX1) / 2, CY, 0.1, 0.25, GX1 - GX0, 0.06, MAT_DARK, bevel=0.0)
box("retract_gate_rail_mid", (GX0 + GX1) / 2, CY, 0.68, 0.76, GX1 - GX0, 0.05, MAT_DARK, bevel=0.0)
n_bars = int((GX1 - GX0) / 0.5) + 1
for i in range(n_bars):
    bx = GX0 + i * 0.5
    box("retract_gate_bar_%02d" % i, bx, CY, 0.25, 1.15, 0.05, 0.05, MAT_DARK, bevel=0.0)
# scissor diagonals (thin, rotated ~35 deg in the x-z plane)
for i in range(5):
    dx = GX0 + 0.5 + i * 1.0
    bpy.ops.mesh.primitive_cube_add(location=(dx, CY, 0.7))
    o = bpy.context.active_object
    o.name = "retract_gate_diag_%d" % i
    o.dimensions = (1.15, 0.04, 0.05)
    o.rotation_euler = (0.0, 0.0, 0.65)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(MAT_DARK)
    building.append(o)
for i, wx in enumerate((0.5, 2.5, 4.5)):
    box("retract_gate_wheel_%d" % i, wx, CY, 0.0, 0.12, 0.14, 0.14, MAT_METAL, bevel=0.0)
box("retract_gate_drive", 4.85, CY, 0.0, 1.5, 0.35, 0.3, MAT_DARK, bevel=0.02)

# ---- walls: 20 m each side, 2.2 m high, cream + red cap, 0.4 m thick ----
# west run: x -6..-26
box("wall_W", -16.0, CY, 0.15, 2.2, 20.0, 0.4, MAT_CREAM, bevel=0.03)
box("wall_W_base", -16.0, CY, 0.0, 0.15, 20.0, 0.5, MAT_CONC, bevel=0.02)
box("wall_W_cap", -16.0, CY, 2.2, 2.32, 20.0, 0.52, MAT_RED, bevel=0.02)
# east run: x 6..8 and 14..26 (guard room fills 8..14 of the same 20 m run)
box("wall_E1", 7.0, CY, 0.15, 2.2, 2.0, 0.4, MAT_CREAM, bevel=0.03)
box("wall_E1_base", 7.0, CY, 0.0, 0.15, 2.0, 0.5, MAT_CONC, bevel=0.02)
box("wall_E1_cap", 7.0, CY, 2.2, 2.32, 2.0, 0.52, MAT_RED, bevel=0.02)
box("wall_E2", 20.0, CY, 0.15, 2.2, 12.0, 0.4, MAT_CREAM, bevel=0.03)
box("wall_E2_base", 20.0, CY, 0.0, 0.15, 12.0, 0.5, MAT_CONC, bevel=0.02)
box("wall_E2_cap", 20.0, CY, 2.2, 2.32, 12.0, 0.52, MAT_RED, bevel=0.02)

# ---- preview-only ground (NOT exported) ----
bpy.ops.mesh.primitive_plane_add(location=(CX, CY, -0.01))
ground = bpy.context.active_object
ground.name = "Ground_PreviewOnly"
ground.dimensions = (90.0, 50.0, 0.0)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
ground.data.materials.append(MAT_GROUND)

# ---- lighting (SPEC section 2): sun 3.5 from SW, elev ~50 deg ----
target = Vector((2.0, CY, 3.0))
sun_dir = Vector((-0.64, -0.64, 1.0))  # sun sits SW and up
bpy.ops.object.light_add(type="SUN", location=tuple(target + sun_dir * 80.0))
sun = bpy.context.active_object
sun.name = "Sun_SW"
sun.data.energy = 3.5
sun.data.use_shadow = True
sun.rotation_euler = (target - sun.location).to_track_quat("-Z", "Y").to_euler()

# ---- world: flat light blue (0.65, 0.78, 0.88), strength 1.0 ----
world = bpy.data.worlds.new("World_LightBlue")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.65, 0.78, 0.88, 1.0)
bg.inputs["Strength"].default_value = 1.0

# ---- camera: front view from the south (road side), slightly elevated
# and offset east so the beam and the guard room both read clearly ----
bpy.ops.object.camera_add(location=(5.0, CY - 30.0, 7.5))
cam = bpy.context.active_object
cam.name = "Cam_Preview"
cam.data.lens = 35.0
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
bpy.context.scene.camera = cam

# ---- save .blend ----
os.makedirs(PY_DIR, exist_ok=True)
os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
os.makedirs(os.path.dirname(PNG_PATH), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("saved blend:", BLEND_PATH)

# ---- export .glb (building objects only) ----
bpy.ops.object.select_all(action="DESELECT")
for o in building:
    o.select_set(True)
bpy.context.view_layer.objects.active = building[0]
bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format="GLB",
                           use_selection=True, export_apply=True)
print("exported glb:", GLB_PATH, "objects:", len(building))

# ---- read back the .glb to confirm it opens ----
bpy.ops.object.select_all(action="DESELECT")
bpy.ops.import_scene.gltf(filepath=GLB_PATH)
imported = [o for o in bpy.context.selected_objects]
print("glb re-import OK, imported objects:", len(imported))

# ---- render preview: Eevee, 640x360, 16 samples ----
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100
scene.eevee.taa_render_samples = 16
scene.render.filepath = PNG_PATH
scene.render.image_settings.file_format = "PNG"
bpy.ops.render.render(write_still=True)
print("rendered preview:", PNG_PATH)

print("DONE ov-gate")
