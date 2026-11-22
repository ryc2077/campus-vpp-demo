# ch-marking: 充电区车位线与标识 (Blender 坐标, x 东 / y 北 / z 上, 单位米)
# 只做车位线与地面标识, 不做充电桩 (ch-piles) / 车辆 (ch-cars) / 雨棚 (ch-canopy)
#
# 充电区中心 (44, -76)。4 个车位沿 x 排开, 中心 x=38 / 41.5 / 45 / 48.5,
# 每个车位 2.5m 宽 x 5m 深 (y -78.5 ~ -73.5)。
# 白线: 每个车位 1 个框, 线宽 0.12m, 厚 0.01m, 贴地面 (z 0 ~ 0.01)。
#   每框 2 条侧线 (0.12 x 5) + 北缘线 + 南缘线 (2.5 x 0.12);
#   南缘线中心 y=-78.5+0.06, 其外缘正好落在 y=-78.5。
# 绿块: 每个车位地面 1 块 V2G 示意块 1.0 x 0.5m, 绿 #46A04E, 居车位中心,
#   厚 0.01m, 与白线不重叠。
# 黄线: 车位区外缘 1 条, 0.15m 宽, 沿南侧 y=-78.5 外侧,
#   中心 y=-78.575 (北缘贴 y=-78.5), x 从 36.75 到 49.75 (13m), 厚 0.01m,
#   黄 #E8B400 (SPEC 警示黄)。
import bpy
import math
import os
from mathutils import Vector

PIECE = "ch-marking"
BASE = os.path.expanduser("~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
PY_DIR = os.path.join(BASE, "assets/blender/charge")
BLEND_PATH = os.path.join(PY_DIR, "ch-marking.blend")
GLB_PATH = os.path.join(BASE, "assets/models/ch-marking.glb")
PNG_PATH = os.path.join(BASE, "screenshots/blender/ch-marking.png")

# 充电区: 中心 (44, -76); 车位中心 x, 宽 2.5, 深 5 (y -78.5 ~ -73.5)
SPACE_CX = (38.0, 41.5, 45.0, 48.5)
SPACE_W, SPACE_D = 2.5, 5.0
SPACE_Y_SOUTH, SPACE_Y_NORTH = -78.5, -73.5
SPACE_Y_C = (SPACE_Y_SOUTH + SPACE_Y_NORTH) / 2.0  # -76.0
SPACE_X0 = SPACE_CX[0] - SPACE_W / 2.0  # 36.75 (区西缘)
SPACE_X1 = SPACE_CX[-1] + SPACE_W / 2.0  # 49.75 (区东缘)
LINE_W = 0.12
LINE_Z0, LINE_Z1 = 0.0, 0.01
GREEN_SX, GREEN_SY = 1.0, 0.5
YELLOW_W = 0.15
YELLOW_Y_C = SPACE_Y_SOUTH - YELLOW_W / 2.0  # -78.575, 北缘贴 y=-78.5


def hex_rgb(h):
    """Hex sRGB -> linear RGB."""
    h = h.lstrip("#")

    def srgb_to_lin(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (srgb_to_lin(int(h[i:i + 2], 16)) for i in (0, 2, 4))
    return (r, g, b, 1.0)


def _noise(nt, name, scale, detail=3, roughness=0.7, distortion=0.0):
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.name = name
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    n.inputs["Roughness"].default_value = roughness
    n.inputs["Distortion"].default_value = distortion
    return n


def _ramp(nt, name, stops):
    """stops: list of (position, (r,g,b,a)) in linear space."""
    r = nt.nodes.new("ShaderNodeValToRGB")
    r.name = name
    els = r.color_ramp.elements
    els[0].position, els[0].color = stops[0]
    els[1].position, els[1].color = stops[-1]
    for pos, col in stops[1:-1]:
        els.new(pos).color = col
    return r


def make_mat(name, hexcol, rough=0.8, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = hex_rgb(hexcol)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    return m


def make_worn_mat(name, base_hex, worn_hex, rough_lo, rough_hi,
                  noise_scale, bump_strength):
    """程序化磨损: Noise 斑驳调色 + 粗糙度不均 + 轻微凹凸。只改材质节点。"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Metallic"].default_value = 0.0
    coord = nt.nodes.new("ShaderNodeTexCoord")
    coord.name = "TexCoord_Generated"
    noise = _noise(nt, "Noise_Wear", noise_scale, detail=3, roughness=0.7)
    nt.links.new(coord.outputs["Generated"], noise.inputs["Vector"])
    # 斑驳调色: 白/色块与磨损灰之间混合
    ramp_c = _ramp(nt, "Ramp_WearColor",
                   [(0.30, (0.0, 0.0, 0.0, 1.0)), (0.75, (1.0, 1.0, 1.0, 1.0))])
    nt.links.new(noise.outputs["Fac"], ramp_c.inputs["Fac"])
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.name = "Mix_WornColor"
    mix.blend_type = "MIX"
    mix.inputs[1].default_value = hex_rgb(base_hex)
    mix.inputs[2].default_value = hex_rgb(worn_hex)
    nt.links.new(ramp_c.outputs["Color"], mix.inputs[0])
    nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    # 粗糙度不均
    ramp_r = _ramp(nt, "Ramp_WearRough",
                   [(0.0, (rough_lo, rough_lo, rough_lo, 1.0)),
                    (1.0, (rough_hi, rough_hi, rough_hi, 1.0))])
    nt.links.new(noise.outputs["Fac"], ramp_r.inputs["Fac"])
    nt.links.new(ramp_r.outputs["Color"], bsdf.inputs["Roughness"])
    # 轻微凹凸
    bump = nt.nodes.new("ShaderNodeBump")
    bump.name = "Bump_Wear"
    bump.inputs["Strength"].default_value = bump_strength
    bump.inputs["Distance"].default_value = 0.03
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def make_asphalt_mat(name, base_hex, dark_hex, light_hex):
    """沥青: 大尺度深浅斑块 + 细颗粒 Noise + 粗糙度/凹凸变化, 不再是平灰板。"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Metallic"].default_value = 0.0
    coord = nt.nodes.new("ShaderNodeTexCoord")
    coord.name = "TexCoord_Generated"
    # 大斑块: 深浅不均 (约 3-5m 一块)
    patch = _noise(nt, "Noise_Patch", 6.0, detail=3, roughness=0.7,
                   distortion=0.6)
    nt.links.new(coord.outputs["Generated"], patch.inputs["Vector"])
    ramp_p = _ramp(nt, "Ramp_Patch",
                   [(0.35, (0.0, 0.0, 0.0, 1.0)), (0.70, (1.0, 1.0, 1.0, 1.0))])
    nt.links.new(patch.outputs["Fac"], ramp_p.inputs["Fac"])
    mix_p = nt.nodes.new("ShaderNodeMixRGB")
    mix_p.name = "Mix_Patch"
    mix_p.blend_type = "MIX"
    mix_p.inputs[1].default_value = hex_rgb(base_hex)
    mix_p.inputs[2].default_value = hex_rgb(dark_hex)
    nt.links.new(ramp_p.outputs["Color"], mix_p.inputs[0])
    # 细颗粒: 沥青颗粒纹理
    grain = _noise(nt, "Noise_Grain", 140.0, detail=4, roughness=0.8)
    nt.links.new(coord.outputs["Generated"], grain.inputs["Vector"])
    ramp_g = _ramp(nt, "Ramp_Grain",
                   [(0.35, (0.0, 0.0, 0.0, 1.0)), (0.70, (0.45, 0.45, 0.45, 1.0))])
    nt.links.new(grain.outputs["Fac"], ramp_g.inputs["Fac"])
    mix_g = nt.nodes.new("ShaderNodeMixRGB")
    mix_g.name = "Mix_Grain"
    mix_g.blend_type = "MIX"
    mix_g.inputs[2].default_value = hex_rgb(light_hex)
    nt.links.new(mix_p.outputs["Color"], mix_g.inputs[1])
    nt.links.new(ramp_g.outputs["Color"], mix_g.inputs[0])
    nt.links.new(mix_g.outputs["Color"], bsdf.inputs["Base Color"])
    # 粗糙度: 颗粒处 0.85~1.0 变化
    ramp_r = _ramp(nt, "Ramp_GrainRough",
                   [(0.0, (0.85, 0.85, 0.85, 1.0)),
                    (1.0, (1.0, 1.0, 1.0, 1.0))])
    nt.links.new(grain.outputs["Fac"], ramp_r.inputs["Fac"])
    nt.links.new(ramp_r.outputs["Color"], bsdf.inputs["Roughness"])
    # 凹凸: 颗粒 + 斑块叠加感 (只用颗粒, 强度适中)
    bump = nt.nodes.new("ShaderNodeBump")
    bump.name = "Bump_Grain"
    bump.inputs["Strength"].default_value = 0.4
    bump.inputs["Distance"].default_value = 0.06
    nt.links.new(grain.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


MAT_WHITE = make_worn_mat("Marking_White", "#FFFFFF", "#CFCFCF",
                          0.55, 0.95, 22.0, 0.15)
MAT_GREEN = make_worn_mat("Marking_V2G_Green_46A04E", "#46A04E", "#3C8A44",
                          0.70, 0.90, 18.0, 0.10)
MAT_YELLOW = make_worn_mat("Marking_Edge_Yellow_E8B400", "#E8B400", "#D2A300",
                           0.70, 0.90, 18.0, 0.10)
MAT_ASPHALT = make_asphalt_mat("PreviewGround_Asphalt_424A52",
                               "#424A52", "#2E3338", "#5B6169")

# ---- clean scene ----
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

objs = []  # objects that go into the .glb


def box(name, cx, cy, z0, z1, sx, sy, mat):
    bpy.ops.mesh.primitive_cube_add(location=(cx, cy, (z0 + z1) / 2.0))
    o = bpy.context.active_object
    o.name = name
    o.dimensions = (sx, sy, z1 - z0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    objs.append(o)
    return o


# ---- 白线: 每车位 1 框 = 2 条侧线 + 北缘线 + 南缘线 ----
for i, cx in enumerate(SPACE_CX, 1):
    x_west = cx - SPACE_W / 2.0
    x_east = cx + SPACE_W / 2.0
    # 侧线: 中心在框边线上, 0.12 宽 x 5 深
    box("space%02d_line_west" % i, x_west, SPACE_Y_C,
        LINE_Z0, LINE_Z1, LINE_W, SPACE_D, MAT_WHITE)
    box("space%02d_line_east" % i, x_east, SPACE_Y_C,
        LINE_Z0, LINE_Z1, LINE_W, SPACE_D, MAT_WHITE)
    # 北缘线: 中心 y=-73.5-0.06, 外缘落在 y=-73.5
    box("space%02d_line_north" % i, cx, SPACE_Y_NORTH - LINE_W / 2.0,
        LINE_Z0, LINE_Z1, SPACE_W, LINE_W, MAT_WHITE)
    # 南缘线: 中心 y=-78.5+0.06, 外缘落在 y=-78.5
    box("space%02d_line_south" % i, cx, SPACE_Y_SOUTH + LINE_W / 2.0,
        LINE_Z0, LINE_Z1, SPACE_W, LINE_W, MAT_WHITE)

# ---- 绿块: 每车位 1 块 V2G 示意块 1.0 x 0.5m, 居车位中心 ----
for i, cx in enumerate(SPACE_CX, 1):
    box("space%02d_v2g_green" % i, cx, SPACE_Y_C,
        LINE_Z0, LINE_Z1, GREEN_SX, GREEN_SY, MAT_GREEN)

# ---- 黄线: 南侧外缘 1 条, 13m 长 x 0.15m 宽 ----
box("edge_line_yellow_south", (SPACE_X0 + SPACE_X1) / 2.0, YELLOW_Y_C,
    LINE_Z0, LINE_Z1, SPACE_X1 - SPACE_X0, YELLOW_W, MAT_YELLOW)

print("marking objects:", len(objs), "(white lines 16, green blocks 4, yellow edge 1)")

# ---- preview-only ground (NOT exported): 沥青面, 衬托白线/绿块/黄线 ----
bpy.ops.mesh.primitive_plane_add(location=(43.25, -76.0, -0.01))
ground = bpy.data.objects["Plane"]
ground.name = "Ground_PreviewOnly"
ground.dimensions = (30.0, 20.0, 0.0)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
ground.data.materials.append(MAT_ASPHALT)

# ---- lighting (SPEC section 2): sun 3.5 from SW, elev ~50 deg ----
target = Vector((43.25, -76.0, 0.0))
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

# ---- camera: 低机位斜视 (~24 度仰角, 南侧看向北), 4 车位框/绿块/黄基线全入镜 ----
bpy.ops.object.camera_add(location=(43.25, -87.0, 5.0))
cam = bpy.context.active_object
cam.name = "Cam_Preview"
cam.data.lens = 28.0
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
bpy.context.scene.camera = cam

# ---- save .blend ----
os.makedirs(PY_DIR, exist_ok=True)
os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
os.makedirs(os.path.dirname(PNG_PATH), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("saved blend:", BLEND_PATH)
if os.path.exists(BLEND_PATH + "1"):
    os.remove(BLEND_PATH + "1")
    print("removed blend1")

# ---- export .glb (this piece only) ----
bpy.ops.object.select_all(action="DESELECT")
for o in objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format="GLB",
                           use_selection=True, export_apply=True)
print("exported glb:", GLB_PATH, "objects:", len(objs))

# ---- read back the .glb to confirm it opens, then drop the duplicates ----
bpy.ops.object.select_all(action="DESELECT")
bpy.ops.import_scene.gltf(filepath=GLB_PATH)
imported = [o for o in bpy.context.selected_objects]
print("glb re-import OK, imported objects:", len(imported))
assert imported, "GLB reimport returned no objects"
bpy.ops.object.delete(use_global=False)  # remove re-imported copies before render
print("re-imported copies deleted, scene objects:", len(bpy.context.scene.objects))

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

print("DONE ch-marking")
