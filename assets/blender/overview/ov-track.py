# ov-track v2: 操场跑道返工 (overview piece)
# 椭圆跑道环, Blender 中心 (-80, -25, 0):
#   外椭圆 rx=40, ry=28; 内椭圆 rx=32, ry=20; 环宽 8 m; 跑道红 #B8543F; 厚 0.1 m
# v1 几何保持不变 (精确椭圆环网格, 不用缩放圆环做法).
# v2 新增:
#   (1) 跑道面塑胶颗粒纹理: Noise 细颗粒 -> 粗糙度变化 + Bump;
#       磨损深浅: 顶点色属性 "wear", 弯道 (东西两端, |cos a| 大) 磨损重、
#       直道 (南北两边) 磨损轻, 混入偏暗的磨损红.
#   (2) 跑道线: 保留 v1 的 3 条分道线 + 内外边缘线; 新增起跑线
#       (南直道横贯 4 条跑道) 与弯道分道标记 (东西弯道中点每道一条径向短线).
#   (3) 0.3 m 混凝土路缘: 内外圈各一条, 高 0.15 m, 小倒角, 混凝土 Noise 纹.
# 只做跑道环 + 线 + 路缘: 不做场内球场 (ov-field)、不做看台 (ov-field)、
# 不做草坪 (ov-lawn). 圈内绿地仅预览用、不导出.
# 本地不渲染 (渲染走 GitHub Actions): 本脚本只建模 + 存 .blend + 导出 .glb + 回读确认.

import bpy
import math
import os
from mathutils import Vector

PIECE = "ov-track"
BASE = os.path.expanduser("~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
PY_DIR = os.path.join(BASE, "assets/blender/overview")
BLEND_PATH = os.path.join(PY_DIR, "ov-track.blend")
GLB_PATH = os.path.join(BASE, "assets/models/ov-track.glb")

CX, CY = -80.0, -25.0   # track centre (Blender x, y)
RX_OUT, RY_OUT = 40.0, 28.0
RX_IN, RY_IN = 32.0, 20.0
TRACK_Z0, TRACK_Z1 = 0.0, 0.1
LINE_W = 0.15           # lane-line width
LINE_H = 0.02           # lane lines sit 0.02 m above the track surface
NSEG = 128
CURB_W = 0.3            # concrete curb width
CURB_H = 0.15           # curb height above ground


def hex_lin(h):
    """Hex sRGB -> linear RGB (Blender stores Base Color linear)."""
    h = h.lstrip("#")

    def srgb_to_lin(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    return tuple(srgb_to_lin(int(h[i:i + 2], 16)) for i in (0, 2, 4))


def make_mat(name, hexcol, rough=0.85, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*hex_lin(hexcol), 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    return m


def add_noise_rough_bump(mat, scale, rough_lo, rough_hi, bump_strength):
    """Fine granule: Noise -> roughness variation + Bump. Returns nothing."""
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 2.0
    noise.inputs["Roughness"].default_value = 0.7
    # roughness: noise Fac mapped to [rough_lo, rough_hi]
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (rough_lo, rough_lo, rough_lo, 1.0)
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = (rough_hi, rough_hi, rough_hi, 1.0)
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Roughness"])
    # bump: noise Fac -> Bump -> Normal
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = bump_strength
    bump.inputs["Distance"].default_value = 0.02
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return noise


# ---- materials ----
# track red #B8543F (SPEC section 3), worn red slightly darker/desaturated.
MAT_TRACK = make_mat("Track_Red_B8543F", "#B8543F", 0.9)
add_noise_rough_bump(MAT_TRACK, scale=120.0, rough_lo=0.78, rough_hi=0.95,
                     bump_strength=0.25)
# wear mix: vertex-color attribute "wear" (R channel) mixes fresh -> worn red
nt = MAT_TRACK.node_tree
bsdf = nt.nodes["Principled BSDF"]
attr = nt.nodes.new("ShaderNodeAttribute")
attr.attribute_name = "wear"
sep = nt.nodes.new("ShaderNodeSeparateColor")
nt.links.new(attr.outputs["Color"], sep.inputs["Color"])
mix = nt.nodes.new("ShaderNodeMixRGB")
mix.blend_type = "MIX"
mix.inputs[1].default_value = (*hex_lin("#B8543F"), 1.0)   # fresh
mix.inputs[2].default_value = (*hex_lin("#96503F"), 1.0)   # worn (darker)
nt.links.new(sep.outputs["Red"], mix.inputs["Fac"])
nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])

MAT_LINE = make_mat("LaneLine_White_FFFFFF", "#FFFFFF", 0.8)
MAT_CURB = make_mat("Curb_Concrete_B9B3A8", "#B9B3A8", 0.95)
add_noise_rough_bump(MAT_CURB, scale=60.0, rough_lo=0.85, rough_hi=1.0,
                     bump_strength=0.2)
MAT_GROUND = make_mat("Ground_Grass_69B45E", "#69B45E", 1.0)

# ---- clean scene ----
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

track_objs = []  # objects that go into the .glb


def ellipse_ring(name, rx_out, ry_out, rx_in, ry_in, z0, z1, mat):
    """Flat elliptical annulus solid: top/bottom ring faces + outer/inner walls."""
    n = NSEG
    verts = []
    for i in range(n):
        a = 2.0 * math.pi * i / n
        ca, sa = math.cos(a), math.sin(a)
        verts.append((CX + rx_out * ca, CY + ry_out * sa, z1))  # outer top
        verts.append((CX + rx_in * ca, CY + ry_in * sa, z1))   # inner top
        verts.append((CX + rx_out * ca, CY + ry_out * sa, z0))  # outer bottom
        verts.append((CX + rx_in * ca, CY + ry_in * sa, z0))   # inner bottom
    faces = []
    for i in range(n):
        j = (i + 1) % n
        ot_i, it_i, ob_i, ib_i = 4 * i, 4 * i + 1, 4 * i + 2, 4 * i + 3
        ot_j, it_j, ob_j, ib_j = 4 * j, 4 * j + 1, 4 * j + 2, 4 * j + 3
        faces.append((ot_i, ot_j, it_j, it_i))   # top
        faces.append((ob_i, ib_i, ib_j, ob_j))   # bottom
        faces.append((ot_i, ob_i, ob_j, ot_j))   # outer wall
        faces.append((it_i, it_j, ib_j, ib_i))   # inner wall
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    track_objs.append(obj)
    return obj


def add_wear(obj):
    """Per-vertex wear 0..1: bends (E/W ends, |cos a|~1) wear heavy,
    straights (N/S, |cos a|~0) wear light, plus small deterministic jitter."""
    mesh = obj.data
    col = mesh.color_attributes.new(name="wear", type="FLOAT_COLOR",
                                    domain="POINT")
    for i, v in enumerate(mesh.vertices):
        seg = i // 4
        a = 2.0 * math.pi * seg / NSEG
        bend = abs(math.cos(a)) ** 1.5
        jitter = (math.sin(seg * 12.9898) * 43758.5453) % 1.0 * 0.12
        w = max(0.0, min(1.0, 0.22 + 0.66 * bend + jitter))
        col.data[i].color = (w, w, w, 1.0)
    return col


def add_box(name, dims, loc, mat, rot_z=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.active_object
    o.name = name
    o.dimensions = dims
    if rot_z:
        o.rotation_euler[2] = rot_z
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    track_objs.append(o)
    return o


# ---- track ring: red, 0.1 m thick, with granule + wear ----
ring = ellipse_ring("track_ring", RX_OUT, RY_OUT, RX_IN, RY_IN,
                    TRACK_Z0, TRACK_Z1, MAT_TRACK)
add_wear(ring)

# ---- 3 lane divider lines, evenly spaced (4 lanes of 2 m each) ----
for k, t in enumerate((0.25, 0.5, 0.75), start=1):
    rx = RX_IN + (RX_OUT - RX_IN) * t
    ry = RY_IN + (RY_OUT - RY_IN) * t
    ellipse_ring("track_lane_line_%d" % k,
                 rx + LINE_W / 2, ry + LINE_W / 2,
                 rx - LINE_W / 2, ry - LINE_W / 2,
                 TRACK_Z1, TRACK_Z1 + LINE_H, MAT_LINE)

# ---- edge lines: outer + inner ----
ellipse_ring("track_edge_line_outer",
             RX_OUT + LINE_W / 2, RY_OUT + LINE_W / 2,
             RX_OUT - LINE_W / 2, RY_OUT - LINE_W / 2,
             TRACK_Z1, TRACK_Z1 + LINE_H, MAT_LINE)
ellipse_ring("track_edge_line_inner",
             RX_IN + LINE_W / 2, RY_IN + LINE_W / 2,
             RX_IN - LINE_W / 2, RY_IN - LINE_W / 2,
             TRACK_Z1, TRACK_Z1 + LINE_H, MAT_LINE)

# ---- start line: south straight, across all 4 lanes ----
# south straight spans y = CY-28 .. CY-20 (centre -49); bar 0.15 m wide in x.
add_box("track_start_line", (0.15, RX_OUT - RX_IN, LINE_H),
        (CX, CY - (RY_OUT + RY_IN) / 2.0, TRACK_Z1 + LINE_H / 2.0), MAT_LINE)

# ---- bend lane marks: radial ticks at E and W bend midpoints, one per lane ----
# lane centres (rx): 33, 35, 37, 39; tick 1.0 m radial x 0.12 m tangential.
for side, sx in (("E", 1), ("W", -1)):
    for li, rc in enumerate((33.0, 35.0, 37.0, 39.0), start=1):
        add_box("track_bend_mark_%s%d" % (side, li),
                (1.0, 0.12, LINE_H),
                (CX + sx * rc, CY, TRACK_Z1 + LINE_H / 2.0), MAT_LINE)

# ---- concrete curbs 0.3 m wide, inner + outer, with small bevel ----
curb_out = ellipse_ring("track_curb_outer",
                        RX_OUT + CURB_W, RY_OUT + CURB_W, RX_OUT, RY_OUT,
                        0.0, CURB_H, MAT_CURB)
curb_in = ellipse_ring("track_curb_inner",
                       RX_IN, RY_IN, RX_IN - CURB_W, RY_IN - CURB_W,
                       0.0, CURB_H, MAT_CURB)
for curb in (curb_out, curb_in):
    bev = curb.modifiers.new("CurbBevel", "BEVEL")
    bev.width = 0.03
    bev.segments = 2

print("track objects:", len(track_objs),
      "ring outer rx/ry:", RX_OUT, RY_OUT, "inner rx/ry:", RX_IN, RY_IN)

# ---- preview-only ground (NOT exported) ----
bpy.ops.mesh.primitive_plane_add(location=(CX, CY, -0.01))
ground = bpy.context.active_object
ground.name = "Ground_PreviewOnly"
ground.dimensions = (170.0, 130.0, 0.0)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
ground.data.materials.append(MAT_GROUND)

# ---- lighting (SPEC section 2): sun 3.5 from SW, elev ~50 deg ----
target = Vector((CX, CY, 0.0))
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

# ---- camera (for later GitHub Actions render; NOT rendered locally) ----
bpy.ops.object.camera_add(location=(CX - 30.0, CY - 30.0, 120.0))
cam = bpy.context.active_object
cam.name = "Cam_Preview"
cam.data.lens = 35.0
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
bpy.context.scene.camera = cam

# ---- save .blend ----
os.makedirs(PY_DIR, exist_ok=True)
os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("saved blend:", BLEND_PATH)

# ---- export .glb (track objects only) ----
bpy.ops.object.select_all(action="DESELECT")
for o in track_objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = track_objs[0]
bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format="GLB",
                           use_selection=True, export_apply=True)
print("exported glb:", GLB_PATH, "objects:", len(track_objs))

# ---- read back the .glb to confirm it opens ----
bpy.ops.object.select_all(action="DESELECT")
bpy.ops.import_scene.gltf(filepath=GLB_PATH)
imported = [o for o in bpy.context.selected_objects]
print("glb re-import OK, imported objects:", len(imported),
      [o.name for o in imported])

print("DONE ov-track")
