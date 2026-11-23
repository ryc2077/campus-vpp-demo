# ov-gate v2: 南门门楼 + 门柱 + 伸缩门 + 围墙 (overview piece) -- REWORK
# Blender centre (0, -98, 0); x east, y north, z up; metres.
# v2 changes vs v1 (screening findings):
#  1. guard-room glass -> reflective glass (pale blue-grey, alpha + low
#     roughness + high specular; Eevee SSR on + Reflection Cubemap at the
#     guard room), window mullions (centre vertical + horizontal bars),
#     glass split into panes -- no longer a flat blue slab.
#  2. plaster walls: procedural Noise -> Roughness + Bump variation
#     (stain mottling), base colour stays the SPEC hex so the .glb keeps
#     the right colour (glTF cannot carry procedural nodes).
#  3. perimeter walls: Brick texture + Noise mottling (bump/roughness).
#  4. retractable gate: real cylinder wheel row along the bottom rail +
#     motor housing at the east end with cooling-grille slats.
#  5. red cap / posts / beam get SEPARATE materials, each with its own
#     noise scale/seed so the tone varies piece by piece.
#  6. structural pieces keep small bevels (box() helper).
#
# NOTE: no rendering in this run (all renders go through GitHub Actions).
# This script only builds, saves .blend, exports .glb, re-imports to verify.
#
# Layout (from the aerial photo: south gate on the south main road,
# modest gatehouse, guard room east of the gate, dark flat roof):
# - two posts 1x1x6 m at x = +/-5.5 (inner faces at +/-5.0 -> 10 m opening)
# - lintel beam 12 m span (x -6..+6), z 5.0-6.2, 0.8 m thick, cream + red cap
# - guard room east, 6(x) x 4(y) x 3.5 m, centre (11, -98)
# - retractable gate: nominal 10 m frame, shown HALF-OPEN, gathered to the
#   east half of the opening (x 0..+5), dark grey thin-bar frame, 1.2 m high
# - walls 20 m each side of the posts, 2.2 m high, cream brick + red cap;
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


def add_noise_mottle(mat, scale=6.0, detail=3.0, rough_lo=0.72, rough_hi=0.95,
                     bump_strength=0.25, bump_distance=0.03, seed=0):
    """Procedural plaster/stain variation: Noise -> Roughness + Bump.

    Base Color is left as the plain SPEC hex (glTF-safe); the mottling
    shows in Eevee through roughness and bump only.
    """
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = scale + seed * 0.9  # per-material variation
    tex.inputs["Detail"].default_value = detail
    tex.inputs["Roughness"].default_value = 0.7
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = (rough_lo, rough_lo, rough_lo, 1.0)
    ramp.color_ramp.elements[1].position = 0.65
    ramp.color_ramp.elements[1].color = (rough_hi, rough_hi, rough_hi, 1.0)
    nt.links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Roughness"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = bump_strength
    bump.inputs["Distance"].default_value = bump_distance
    nt.links.new(tex.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def add_brick(mat, brick_scale=14.0, mortar_size=0.02, seed=0):
    """Brick pattern (Brick + Noise mottling) -> Roughness + Bump.

    Base Color stays the cream SPEC hex so the .glb keeps the right
    colour; the brick courses read in Eevee via bump/roughness.
    """
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    brick = nt.nodes.new("ShaderNodeTexBrick")
    brick.offset = 0.5
    brick.inputs["Scale"].default_value = brick_scale
    brick.inputs["Mortar Size"].default_value = mortar_size
    brick.inputs["Brick Width"].default_value = 0.5
    brick.inputs["Row Height"].default_value = 0.22
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 9.0 + seed * 0.8
    noise.inputs["Detail"].default_value = 3.0
    # mottle the brick roughness: brick fac * noise -> roughness ramp
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MULTIPLY"
    nt.links.new(brick.outputs["Color"], mix.inputs[1])
    nt.links.new(noise.outputs["Fac"], mix.inputs[2])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.25
    ramp.color_ramp.elements[0].color = (0.70, 0.70, 0.70, 1.0)
    ramp.color_ramp.elements[1].position = 0.75
    ramp.color_ramp.elements[1].color = (0.96, 0.96, 0.96, 1.0)
    nt.links.new(mix.outputs["Color"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Roughness"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.5
    bump.inputs["Distance"].default_value = 0.04
    nt.links.new(brick.outputs["Color"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def make_glass(name, hexcol="#A9C6D8"):
    """Reflective glass: pale blue-grey, translucent, mirror-like.

    Eevee: low roughness + specular 1.0 + Screen Space Reflections
    (enabled below) + a Reflection Cubemap at the guard room, so it
    reflects the surroundings instead of reading as a flat blue slab.
    glTF: alpha blend + low roughness reads as glossy glass.
    """
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = hex_rgb(hexcol)
    bsdf.inputs["Roughness"].default_value = 0.08
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Alpha"].default_value = 0.65
    bsdf.inputs["Specular IOR Level"].default_value = 1.0
    # faint roughness variation so the reflection is not perfectly uniform
    nt = m.node_tree
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 4.0
    noise.inputs["Detail"].default_value = 2.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.3
    ramp.color_ramp.elements[0].color = (0.04, 0.04, 0.04, 1.0)
    ramp.color_ramp.elements[1].position = 0.7
    ramp.color_ramp.elements[1].color = (0.16, 0.16, 0.16, 1.0)
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Roughness"])
    m.surface_render_method = "DITHERED"
    return m


# ---- materials: red cap / posts / beam get SEPARATE materials (v2 item 5)
MAT_POST_CREAM = add_noise_mottle(make_mat("GatePost_Cream_F3E9D2", "#F3E9D2", 0.85),
                                  scale=5.0, seed=1, bump_strength=0.2)
MAT_BEAM_CREAM = add_noise_mottle(make_mat("GateBeam_Cream_EFE2C8", "#EFE2C8", 0.82),
                                  scale=7.0, seed=2, bump_strength=0.2)
MAT_GUARD_CREAM = add_noise_mottle(make_mat("GuardRoom_Cream_F3E9D2", "#F3E9D2", 0.85),
                                   scale=6.0, seed=4, bump_strength=0.25)
MAT_RED_CAP = add_noise_mottle(make_mat("GateRedCap_8E2F28", "#8E2F28", 0.78),
                               scale=8.0, seed=3, bump_strength=0.15,
                               rough_lo=0.65, rough_hi=0.9)
MAT_RED_POST = add_noise_mottle(make_mat("GatePostRed_7E2A24", "#7E2A24", 0.8),
                                scale=9.0, seed=5, bump_strength=0.15,
                                rough_lo=0.68, rough_hi=0.92)
MAT_WALL_BRICK = add_brick(make_mat("Wall_BrickCream_F3E9D2", "#F3E9D2", 0.88),
                           brick_scale=14.0, seed=6)
MAT_ROOF = make_mat("Roof_DarkGrey_424A52", "#424A52", 0.9)
MAT_CONC = add_noise_mottle(make_mat("Concrete_B9B3A8", "#B9B3A8", 0.95),
                            scale=10.0, seed=7, bump_strength=0.15,
                            rough_lo=0.88, rough_hi=1.0)
MAT_METAL = make_mat("MetalGrey_8A8F94", "#8A8F94", 0.5, 0.4)
MAT_DARK = make_mat("Gate_DarkGrey_424A52", "#424A52", 0.6, 0.4)
MAT_FRAME = make_mat("WindowFrame_Dark_2E3438", "#2E3438", 0.55, 0.3)
MAT_GLASS = make_glass("Glass_Reflective_A9C6D8")
MAT_MOTOR = make_mat("MotorBox_3A4046", "#3A4046", 0.55, 0.5)
MAT_GRILLE = make_mat("MotorGrille_6E757C", "#6E757C", 0.45, 0.6)
MAT_GROUND = make_mat("Ground_Grass_69B45E", "#69B45E", 1.0)

# ---- PBR 贴图挂接（返工）：下载的 CC0 实拍贴图经亮度映射到 SPEC 色
# （assets/external/* -> ov-gate_textures/ 衍生 PNG）；红帽/红柱是细窄
# 色带、砖纹比例不对，留程序化合成 RedCap；玻璃/小金属件/灯不挂图。
# 程序化 Noise 节点不进 glTF，必须换成图片纹理节点。
# UV 按米缩放：1 次贴图重复 = tile 米（盒体默认 UV 每面 0~1）。
import numpy as _np
TEX_DIR = os.path.join(PY_DIR, "ov-gate_textures")


def _load_img(path, colorspace):
    img = bpy.data.images.load(path)
    img.colorspace_settings.name = colorspace
    return img


def _apply_pbr(mat, set_name):
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    out = nt.nodes["Material Output"]
    for n in list(nt.nodes):
        if n not in (bsdf, out):
            nt.nodes.remove(n)
    for link in list(nt.links):
        if link.to_node is bsdf:
            nt.links.remove(link)
    bsdf.inputs["Base Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    c = os.path.join(TEX_DIR, set_name + "_color.png")
    if os.path.exists(c):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = _load_img(c, "sRGB")
        nt.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
    r = os.path.join(TEX_DIR, set_name + "_rough.png")
    if os.path.exists(r):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = _load_img(r, "Non-Color")
        nt.links.new(t.outputs["Color"], bsdf.inputs["Roughness"])
        bsdf.inputs["Roughness"].default_value = 1.0
    n = os.path.join(TEX_DIR, set_name + "_normal.png")
    if os.path.exists(n):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = _load_img(n, "Non-Color")
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.space = "TANGENT"
        nt.links.new(t.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def _ensure_uv(ob):
    me = ob.data
    if me is None or len(me.uv_layers) > 0:
        return
    me.uv_layers.new(name="UVMap")
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.02)
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")


def _scale_uvs_to_meters(obj, tile):
    """每面按世界尺寸把 UV 缩放到 tile 米一重复（REPEAT 平铺）。"""
    me = obj.data
    if me is None or len(me.uv_layers) == 0:
        return 0
    uv = me.uv_layers.active.data
    mw = obj.matrix_world
    for poly in me.polygons:
        idx = list(poly.loop_indices)
        P = _np.array([mw @ me.vertices[me.loops[i].vertex_index].co
                       for i in idx], dtype=float)
        U = _np.array([[uv[i].uv[0], uv[i].uv[1]] for i in idx], dtype=float)
        A = _np.column_stack([_np.ones(len(idx)), U])
        coef, *_ = _np.linalg.lstsq(A, P, rcond=None)
        su = _np.linalg.norm(coef[1]) / tile
        sv = _np.linalg.norm(coef[2]) / tile
        for i in idx:
            u, v = uv[i].uv
            uv[i].uv = (u * su, v * sv)
    return len(me.polygons)


_apply_pbr(MAT_POST_CREAM, "PlasterCream")
_apply_pbr(MAT_BEAM_CREAM, "PlasterCream")
_apply_pbr(MAT_GUARD_CREAM, "PlasterCream")
_apply_pbr(MAT_RED_CAP, "RedCap")
_apply_pbr(MAT_RED_POST, "RedCap")
_apply_pbr(MAT_WALL_BRICK, "BrickCream")
_apply_pbr(MAT_ROOF, "DarkGrey")
_apply_pbr(MAT_CONC, "Concrete")
# 贴图 UV 按米缩放：{材质: 一重复多少米}（砖 0.6m 一重复 = 砖行约 7.5cm）
UV_TILE = {MAT_POST_CREAM: 2.0, MAT_BEAM_CREAM: 2.0, MAT_GUARD_CREAM: 2.0,
           MAT_RED_CAP: 1.0, MAT_RED_POST: 1.0, MAT_WALL_BRICK: 0.6,
           MAT_ROOF: 2.0, MAT_CONC: 2.0}

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


def cylinder(name, loc, radius, depth, mat, rot=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth,
                                        location=loc, rotation=rot,
                                        vertices=20)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(mat)
    building.append(o)
    return o


# ---- gate posts: 1x1x6 m at x = +/-5.5, cream + red top ----
for side, px in (("W", -5.5), ("E", 5.5)):
    box("gate_post_%s_base" % side, px, CY, 0.0, 0.25, 1.3, 1.3, MAT_CONC, bevel=0.02)
    box("gate_post_%s" % side, px, CY, 0.25, 5.9, 1.0, 1.0, MAT_POST_CREAM, bevel=0.04)
    box("gate_post_%s_redband" % side, px, CY, 5.9, 6.2, 1.06, 1.06, MAT_RED_POST, bevel=0.02)
    box("gate_post_%s_cap" % side, px, CY, 6.2, 6.38, 1.25, 1.25, MAT_RED_CAP, bevel=0.02)

# ---- lintel beam: 12 m span, z 5.0-6.2, 0.8 m thick, cream + red cap ----
box("gate_beam", CX, CY, 5.0, 6.2, 12.0, 0.8, MAT_BEAM_CREAM, bevel=0.04)
box("gate_beam_cap", CX, CY, 6.2, 6.35, 12.2, 0.95, MAT_RED_CAP, bevel=0.02)
# thin cream cornice line under the beam
box("gate_beam_cornice", CX, CY, 4.82, 5.0, 12.2, 0.95, MAT_CONC, bevel=0.02)

# ---- guard room (east): 6 x 4 x 3.5 m, centre (11, -98) ----
GX, GY = 11.0, -98.0
box("guard_room_plinth", GX, GY, 0.0, 0.2, 6.3, 4.3, MAT_CONC, bevel=0.02)
box("guard_room_body", GX, GY, 0.2, 3.5, 6.0, 4.0, MAT_GUARD_CREAM, bevel=0.04)
# flat dark-grey roof slab with overhang + thin red trim under it
box("guard_room_roof_trim", GX, GY, 3.5, 3.58, 6.3, 4.3, MAT_RED_CAP, bevel=0.02)
box("guard_room_roof", GX, GY, 3.58, 3.78, 6.4, 4.4, MAT_ROOF, bevel=0.02)

# -- south window (faces the road, y = -100): 1.6 x 1.2 m, frame + mullions
#    + 4 reflective glass panes; wall face at y = GY - 2.0
box("guard_window_frame", GX, GY - 2.02, 1.2, 2.4, 1.8, 0.08, MAT_FRAME, bevel=0.01)
# mullions: centre vertical + centre horizontal, proud of the frame
box("guard_window_mullion_v", GX, GY - 2.07, 1.35, 2.25, 0.06, 0.05, MAT_FRAME, bevel=0.0)
box("guard_window_mullion_h", GX, GY - 2.07, 1.72, 1.88, 1.6, 0.05, MAT_FRAME, bevel=0.0)
# 4 glass panes (0.74 x 0.52 each) set between the mullions
for px_off, pz in ((-0.41, 2.02), (0.41, 2.02), (-0.41, 1.48), (0.41, 1.48)):
    box("guard_window_glass_%+d_%d" % (int(px_off * 100), int(pz * 100)),
        GX + px_off, GY - 2.05, pz - 0.26, pz + 0.26, 0.74, 0.04, MAT_GLASS, bevel=0.0)
box("guard_window_sill", GX, GY - 2.06, 1.1, 1.2, 1.9, 0.14, MAT_CONC, bevel=0.01)
# door on the NORTH face (faces the campus/plaza, y = -96): 0.9 x 2.1 m
box("guard_door", GX - 1.5, GY + 2.02, 0.2, 2.3, 0.95, 0.08, MAT_FRAME, bevel=0.01)
box("guard_door_handle", GX - 1.15, GY + 2.08, 1.0, 1.15, 0.06, 0.1, MAT_METAL, bevel=0.0)
# small window on the WEST face (faces the gate, x = 8): 0.9 x 1.0 m,
# frame + centre mullion + 2 reflective panes
box("guard_window_w_frame", GX - 3.02, GY, 1.4, 2.4, 0.08, 1.1, MAT_FRAME, bevel=0.01)
box("guard_window_w_mullion", GX - 3.07, GY, 1.55, 2.25, 0.05, 0.06, MAT_FRAME, bevel=0.0)
for py_off in (-0.22, 0.22):
    box("guard_window_w_glass_%+d" % int(py_off * 100),
        GX - 3.05, GY + py_off, 1.55, 2.25, 0.06, 0.40, MAT_GLASS, bevel=0.0)

# ---- retractable gate (half-open): thin-bar frame gathered to the east
# half of the 10 m opening (x 0..+5), z 0.1-1.3, dark grey.
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
# v2: real wheel row -- 6 small cylinders (r 0.09 m) on the bottom rail,
# axis along y so they read as wheels from the road side
for i, wx in enumerate((0.4, 1.2, 2.0, 2.8, 3.6, 4.4)):
    cylinder("retract_gate_wheel_%d" % i, (wx, CY, 0.09), 0.09, 0.05,
             MAT_METAL, rot=(1.5707963, 0.0, 0.0))
    # hub cap
    cylinder("retract_gate_wheel_hub_%d" % i, (wx, CY - 0.03, 0.09), 0.035, 0.06,
             MAT_DARK, rot=(1.5707963, 0.0, 0.0))
# v2: motor housing at the east end + cooling-grille slats on its south face
box("retract_gate_motor", 4.82, CY, 0.0, 1.5, 0.42, 0.34, MAT_MOTOR, bevel=0.02)
box("retract_gate_motor_cap", 4.82, CY, 1.5, 1.58, 0.46, 0.38, MAT_DARK, bevel=0.01)
for j in range(5):
    gz = 0.35 + j * 0.18
    box("retract_gate_motor_grille_%d" % j, 4.82, CY - 0.185, gz, gz + 0.05,
        0.30, 0.02, MAT_GRILLE, bevel=0.0)
# small green status lamp on the motor housing
box("retract_gate_motor_lamp", 4.82, CY - 0.185, 1.32, 1.40, 0.06, 0.02,
    make_mat("MotorLamp_Green_2FA04A", "#2FA04A", 0.4), bevel=0.0)

# ---- walls: 20 m each side, 2.2 m high, brick cream + red cap, 0.4 m thick
# west run: x -6..-26
box("wall_W", -16.0, CY, 0.15, 2.2, 20.0, 0.4, MAT_WALL_BRICK, bevel=0.03)
box("wall_W_base", -16.0, CY, 0.0, 0.15, 20.0, 0.5, MAT_CONC, bevel=0.02)
box("wall_W_cap", -16.0, CY, 2.2, 2.32, 20.0, 0.52, MAT_RED_CAP, bevel=0.02)
# east run: x 6..8 and 14..26 (guard room fills 8..14 of the same 20 m run)
box("wall_E1", 7.0, CY, 0.15, 2.2, 2.0, 0.4, MAT_WALL_BRICK, bevel=0.03)
box("wall_E1_base", 7.0, CY, 0.0, 0.15, 2.0, 0.5, MAT_CONC, bevel=0.02)
box("wall_E1_cap", 7.0, CY, 2.2, 2.32, 2.0, 0.52, MAT_RED_CAP, bevel=0.02)
box("wall_E2", 20.0, CY, 0.15, 2.2, 12.0, 0.4, MAT_WALL_BRICK, bevel=0.03)
box("wall_E2_base", 20.0, CY, 0.0, 0.15, 12.0, 0.5, MAT_CONC, bevel=0.02)
box("wall_E2_cap", 20.0, CY, 2.2, 2.32, 12.0, 0.52, MAT_RED_CAP, bevel=0.02)

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

# ---- Eevee reflections for the glass (v2 item 1) ----
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT"
try:
    scene.eevee.use_ssr = True
    scene.eevee.use_ssr_refraction = True
except AttributeError:
    pass
# Reflection Cubemap probe at the guard room so the glass has something
# to reflect (scene-only object, not exported to the .glb)
bpy.ops.object.lightprobe_add(type="SPHERE", location=(GX, GY, 2.0))
probe = bpy.context.active_object
probe.name = "Cubemap_GuardRoom"
probe.data.influence_distance = 12.0
probe.data.falloff = 0.5

# ---- camera: front view from the south (road side), slightly elevated
# and offset east so the beam and the guard room both read clearly ----
bpy.ops.object.camera_add(location=(5.0, CY - 30.0, 7.5))
cam = bpy.context.active_object
cam.name = "Cam_Preview"
cam.data.lens = 35.0
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
bpy.context.scene.camera = cam

# ---- UV 按米缩放（返工）：贴图 1 重复 = tile 米 ----
bpy.context.view_layer.update()
for _o in building:
    if _o.type != "MESH" or not _o.data.materials:
        continue
    _tile = UV_TILE.get(_o.data.materials[0])
    if _tile is None:
        continue
    _ensure_uv(_o)
    _scale_uvs_to_meters(_o, _tile)
print("UV scaled to meters for textured mats")

# ---- save .blend FIRST (crash safety) ----
os.makedirs(PY_DIR, exist_ok=True)
os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
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

# NOTE: no render in this run -- all renders go through GitHub Actions.
print("DONE ov-gate")
