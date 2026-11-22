# ov-road-walk v2: 步道与铺装 (overview piece)
# 返工目标: 旧版南门广场是均匀 2m 小方格, 与鸟瞰图浅色石材大广场带拼花对不上。
# v2 改动:
#  ① 南门广场改浅色石材大板铺装: 大板缝走程序化 Voronoi(材质 Bump),
#     几何拼花 = 以广场中心 (0,-98) 为圆心的 16 条放射缝 + r=4/7.5/11 三圈环形缝,
#     旗杆基座 (0,-88) 加 r=1.2 环形拼花; 板缝顶面高度错开 (0.112/0.114/0.116), 深浅不均。
#  ② 盲道条带: 黄色警示条带 (0.4m 宽, 高出铺装 0.025m), 波纹条纹 Bump,
#     沿步道 2 东侧 + 广场南门轴线 + 步道 1 通长, 丁字路口处断开不重叠。
#  ③ 收边石: 广场四边 + 两条步道两侧路缘石, 带 0.03m 倒角; 广场南缘留 6m 校门开口。
#  ④ 步道石材纹理: 噪波斑驳 + Voronoi 板缝 + 粗糙度/Bump 变化, 程序化材质, 不许大面积纯色平板。
#  ⑤ 所有面程序化纹理, 颜色按鸟瞰图浅色石材取; Base Color 只用默认值(线性值),
#     纹理只走 Bump->Normal (导出器遇 MixRGB/ValToRGB 链 Base Color 会丢 baseColorFactor)。
# 几何沿用 v1 (SPEC §6 + 鸟瞰图: 丁字形步道 + 南门广场):
#  南门广场中心 (0,-98), 40x25m; 步道 1 y=20, x -80..50, 宽 3m; 步道 2 x=0, y -85.5..18.5, 宽 3m。
# 只做铺装和步道; 不做主干道 (ov-road-main)、不做路灯/旗杆 (ov-flag-lamp)、不做花坛 (ov-lawn)。
# 本版不渲染 (新规矩: 渲染全部走 GitHub Actions, 本地不渲染、不出预览图)。
# 浅色铺装 #D8D2C4、步道 #DCD6C8、边框石 #C9C2B0、缝线 #6E6A62、路缘石 #B9B3A8、盲道黄 #E8B400。
#
# 接缝处理 (避免共面 z-fighting / 内部重叠):
# - 步道 2 从广场北缘 y=-85.5 起, 至步道 1 南缘 y=18.5 止, 形成丁字路口。
# - 广场北缘路缘石在步道 2 口 (x -1.5..1.5) 断开; 步道 1 南缘路缘石在步道 2 口同样断开。
# - 步道 2 两侧路缘石南端止于广场北缘路缘石北面 (y=-85.35), 北端止于步道 1 南缘路缘石南面 (y=18.35)。
# - 放射缝顶面 z=0.116, 环形缝 0.112, 边框带 0.114, 盲道 0.125, 交叉处顶面高度各不相同。
# - 放射缝起角 11.25° 错开坐标轴, 不与盲道条带、步道 2 口正对重合。
# 注意 (跨件, 供总协调处理): 广场按任务给定几何 y -110.5..-85.5, 与 ov-road-main
# 南侧主路 (y -114..-102) 在 x -20..20、y -110.5..-102 重叠; 本件广场顶面 z=0.1
# 高于主路顶面 z=0.08, 拼装时该重叠带以广场铺装面为准。

import bpy
import math
import os

PIECE = "ov-road-walk"
BASE = os.path.expanduser("~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
PY_DIR = os.path.join(BASE, "assets/blender/overview")
BLEND_PATH = os.path.join(PY_DIR, "ov-road-walk.blend")
GLB_PATH = os.path.join(BASE, "assets/models/ov-road-walk.glb")

PAVE_Z0, PAVE_Z1 = 0.0, 0.10       # 铺装/步道厚 0.1m
FRAME_Z0, FRAME_Z1 = 0.10, 0.114   # 广场边框石带
RAY_Z0, RAY_Z1 = 0.10, 0.116       # 放射缝 (最深/最高, 与环形缝错开)
RING_Z0, RING_Z1 = 0.10, 0.112     # 环形缝
TACT_Z0, TACT_Z1 = 0.10, 0.125     # 盲道条带 (高出铺装 0.025m)
CURB_Z0, CURB_Z1 = 0.0, 0.10       # 路缘石高 0.1m


def hex_rgb(h):
    """Hex sRGB -> linear RGB (c<=0.04045 时 c/12.92, 否则 ((c+0.055)/1.055)^2.4)。"""
    h = h.lstrip("#")

    def srgb_to_lin(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (srgb_to_lin(int(h[i:i + 2], 16)) for i in (0, 2, 4))
    return (r, g, b, 1.0)


def _noise(nt, texcoord, scale, detail=2.0):
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    n.inputs["Roughness"].default_value = 0.7
    nt.links.new(texcoord.outputs["Object"], n.inputs["Vector"])
    return n


def _voronoi(nt, texcoord, scale, feature="F1"):
    v = nt.nodes.new("ShaderNodeTexVoronoi")
    v.feature = feature
    v.inputs["Scale"].default_value = scale
    nt.links.new(texcoord.outputs["Object"], v.inputs["Vector"])
    return v


def _sock(x):
    return x.outputs[0] if isinstance(x, bpy.types.Node) else x


def _math(nt, op, a, b=None, clamp=False):
    m = nt.nodes.new("ShaderNodeMath")
    m.operation = op
    if isinstance(a, float):
        m.inputs[0].default_value = a
    else:
        nt.links.new(_sock(a), m.inputs[0])
    if b is not None:
        if isinstance(b, float):
            m.inputs[1].default_value = b
        else:
            nt.links.new(_sock(b), m.inputs[1])
    m.use_clamp = clamp
    return m


def make_mat(name, hexcol, rough=0.95, kind="plaza", wave_rot_z=0.0):
    """程序化石材纹理 (只动材质节点, 不动几何):
    - Base Color / Roughness 只用默认值 (线性值): 导出器遇到 MixRGB/ValToRGB 链接会丢
      baseColorFactor (Godot 里变白), 所以颜色因子不链接, 纹理全部走 Bump(法线)。
    - plaza: Voronoi 大板 (2m 胞, F1 明暗) + Voronoi 边距板缝 (2m 胞网, 边缘下陷成缝)
      + 大尺度噪波斑驳 (4m 斑块, 深浅不均)。
    - walk: 噪波斑驳 (0.8m) + Voronoi 板缝 (1.25m 胞网) + 细噪波骨料, 板缝 + 斑驳双层。
    - joint/frame/curb: 细噪波骨料 + 小 Voronoi 麻点 + 斑驳, 无裂纹网, 与铺装区分。
    - tactile: 波纹条纹 (Wave Bands, 条纹间距约 0.28m) + 噪波磨损, 条纹方向由 wave_rot_z 定。"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = hex_rgb(hexcol)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = 0.0

    texcoord = nt.nodes.new("ShaderNodeTexCoord")
    vec = texcoord.outputs["Object"]

    if kind == "plaza":
        grain = _voronoi(nt, texcoord, 0.5, "F1").outputs["Distance"]
        blotch = _noise(nt, texcoord, 0.25, 2.0).outputs["Fac"]
        seam_dist = _voronoi(nt, texcoord, 0.5, "DISTANCE_TO_EDGE").outputs["Distance"]
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.0
        ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
        ramp.color_ramp.elements[1].position = 0.12
        ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
        nt.links.new(seam_dist, ramp.inputs["Fac"])
        seam = _math(nt, "SUBTRACT", 1.0, ramp.outputs["Color"])
        h = _math(nt, "ADD",
                  _math(nt, "MULTIPLY", grain, 0.45),
                  _math(nt, "MULTIPLY", blotch, 0.55))
        h = _math(nt, "SUBTRACT", h, _math(nt, "MULTIPLY", seam, 0.55), clamp=True)
        strength, dist = 0.35, 0.06
    elif kind == "walk":
        blotch = _noise(nt, texcoord, 1.2, 2.0).outputs["Fac"]
        agg = _noise(nt, texcoord, 3.0, 2.0).outputs["Fac"]
        seam_dist = _voronoi(nt, texcoord, 0.8, "DISTANCE_TO_EDGE").outputs["Distance"]
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.0
        ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
        ramp.color_ramp.elements[1].position = 0.10
        ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
        nt.links.new(seam_dist, ramp.inputs["Fac"])
        seam = _math(nt, "SUBTRACT", 1.0, ramp.outputs["Color"])
        h = _math(nt, "ADD",
                  _math(nt, "MULTIPLY", blotch, 0.5),
                  _math(nt, "MULTIPLY", agg, 0.3))
        h = _math(nt, "SUBTRACT", h, _math(nt, "MULTIPLY", seam, 0.5), clamp=True)
        strength, dist = 0.3, 0.05
    elif kind == "tactile":
        mapping = nt.nodes.new("ShaderNodeMapping")
        mapping.inputs["Rotation"].default_value = (0.0, 0.0, wave_rot_z)
        nt.links.new(texcoord.outputs["Object"], mapping.inputs["Vector"])
        wave = nt.nodes.new("ShaderNodeTexWave")
        wave.wave_type = "BANDS"
        wave.bands_direction = "X"
        wave.inputs["Scale"].default_value = 3.5
        wave.inputs["Distortion"].default_value = 0.15
        nt.links.new(mapping.outputs["Vector"], wave.inputs["Vector"])
        wear = _noise(nt, texcoord, 2.0, 2.0).outputs["Fac"]
        h = _math(nt, "ADD",
                  _math(nt, "MULTIPLY", wave.outputs["Color"], 0.7),
                  _math(nt, "MULTIPLY", wear, 0.3), clamp=True)
        strength, dist = 0.5, 0.05
    else:  # joint / frame / curb: 细骨料 + 麻点 + 斑驳
        agg = _noise(nt, texcoord, 1.5, 2.0).outputs["Fac"]
        speck = _voronoi(nt, texcoord, 5.0, "F1").outputs["Distance"]
        blotch = _noise(nt, texcoord, 0.6, 2.0).outputs["Fac"]
        h = _math(nt, "ADD",
                  _math(nt, "MULTIPLY", _math(nt, "ADD", agg, speck), 0.35),
                  _math(nt, "MULTIPLY", blotch, 0.3), clamp=True)
        strength, dist = 0.2, 0.03

    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = strength
    bump.inputs["Distance"].default_value = dist
    nt.links.new(_sock(h), bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


MAT_PAVE = make_mat("Paving_D8D2C4", "#D8D2C4", 0.95, kind="plaza")
MAT_WALK = make_mat("Walkway_DCD6C8", "#DCD6C8", 0.95, kind="walk")
MAT_JOINT = make_mat("JointLine_6E6A62", "#6E6A62", 0.95, kind="joint")
MAT_FRAME = make_mat("FrameStone_C9C2B0", "#C9C2B0", 0.95, kind="joint")
MAT_CURB = make_mat("Curb_B9B3A8", "#B9B3A8", 0.95, kind="joint")
# 盲道: 南北向条带 (步道 2 / 广场) 条纹沿东西向 -> 波纹旋转 90°; 东西向条带 (步道 1) 不旋转
MAT_TACT_NS = make_mat("Tactile_E8B400_NS", "#E8B400", 0.85, kind="tactile",
                       wave_rot_z=math.pi / 2)
MAT_TACT_EW = make_mat("Tactile_E8B400_EW", "#E8B400", 0.85, kind="tactile",
                       wave_rot_z=0.0)

# ---- clean scene ----
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

walk = []  # objects that go into the .glb


def box(name, cx, cy, z0, z1, sx, sy, mat, bevel=0.02, rot_z=0.0):
    bpy.ops.mesh.primitive_cube_add(location=(cx, cy, (z0 + z1) / 2.0))
    o = bpy.context.active_object
    o.name = name
    o.dimensions = (sx, sy, z1 - z0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if rot_z:
        o.rotation_euler = (0.0, 0.0, rot_z)
    if bevel and min(sx, sy, z1 - z0) > 2 * bevel + 0.02:
        mod = o.modifiers.new("EdgeSoft", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        mod.limit_method = "ANGLE"
    o.data.materials.append(mat)
    walk.append(o)
    return o


def ring(name, cx, cy, r, n, z0, z1, w, mat):
    """环形缝: n 段弦拼成的圆环, 每段为细长盒, 长轴沿切线方向。"""
    for i in range(n):
        a_mid = 2.0 * math.pi * (i + 0.5) / n
        chord = 2.0 * r * math.sin(math.pi / n) + 0.01
        box("%s_%02d" % (name, i),
            cx + r * math.cos(a_mid), cy + r * math.sin(a_mid),
            z0, z1, chord, w, mat, bevel=0.0, rot_z=a_mid + math.pi / 2)


# ---- 南门广场: 中心 (0,-98), 40(x) x 25(y)m, x -20..20, y -110.5..-85.5 ----
box("plaza_south_gate", 0.0, -98.0, PAVE_Z0, PAVE_Z1, 40.0, 25.0, MAT_PAVE)
# ---- 楼间步道 1: y=20, x -80..50, 宽 3m (y 18.5..21.5) ----
box("walkway_1_y20", -15.0, 20.0, PAVE_Z0, PAVE_Z1, 130.0, 3.0, MAT_WALK)
# ---- 楼间步道 2: x=0, y -85.5..18.5 (自广场北缘至步道 1 南缘, 不重叠), 宽 3m ----
box("walkway_2_x0", 0.0, -33.5, PAVE_Z0, PAVE_Z1, 3.0, 104.0, MAT_WALK)

# ---- 广场边框石带: 距边缘内收 0.7m 中心线, 0.8m 宽, 颜色略深一档 ----
box("plaza_frame_north", 0.0, -86.2, FRAME_Z0, FRAME_Z1, 38.6, 0.8, MAT_FRAME, bevel=0.0)
box("plaza_frame_south", 0.0, -109.8, FRAME_Z0, FRAME_Z1, 38.6, 0.8, MAT_FRAME, bevel=0.0)
box("plaza_frame_west", -19.3, -98.0, FRAME_Z0, FRAME_Z1, 0.8, 23.6, MAT_FRAME, bevel=0.0)
box("plaza_frame_east", 19.3, -98.0, FRAME_Z0, FRAME_Z1, 0.8, 23.6, MAT_FRAME, bevel=0.0)

# ---- 广场放射缝: 以广场中心 (0,-98) 为圆心, 16 条, 起角 11.25° 错开坐标轴 ----
# 广场半宽 hx=20 (x), hy=12.5 (y); 每条射线自 r=2.5 起, 至矩形边内 1.3m 止 (不碰边框带)。
PCX, PCY, HX, HY = 0.0, -98.0, 20.0, 12.5
for k in range(16):
    ang = math.radians(11.25 + k * 22.5)
    ca, sa = math.cos(ang), math.sin(ang)
    t = min(HX / abs(ca), HY / abs(sa))
    r_end = t - 1.3
    r0 = 2.5
    length = r_end - r0
    r_mid = (r0 + r_end) / 2.0
    box("plaza_ray_%02d" % k,
        PCX + r_mid * ca, PCY + r_mid * sa,
        RAY_Z0, RAY_Z1, length, 0.06, MAT_JOINT, bevel=0.0, rot_z=ang)

# ---- 广场环形缝: r=4 / 7.5 / 11, 每圈 32 段 ----
for j, rr in enumerate((4.0, 7.5, 11.0)):
    ring("plaza_ring%d" % j, PCX, PCY, rr, 32, RING_Z0, RING_Z1, 0.06, MAT_JOINT)

# ---- 旗杆基座环形拼花: 中旗杆 (0,-88) 为圆心, r=1.2, 16 段 ----
ring("plaza_flag_ring", 0.0, -88.0, 1.2, 16, RING_Z0, RING_Z1, 0.06, MAT_JOINT)

# ---- 盲道条带 (0.4m 宽, 高出铺装 0.025m, 黄色 + 波纹条纹 Bump) ----
# 广场: 沿南门轴线东侧 x 0.7..1.1, y -110.5..-85.5 (南门直通步道 2)
box("tactile_plaza", 0.9, -98.0, TACT_Z0, TACT_Z1, 0.4, 25.0, MAT_TACT_NS, bevel=0.0)
# 步道 2: 东侧 x 0.7..1.1, y -85.5..18.5 (止于步道 1 南缘, 与步道 1 盲道留 1.3m 缺口)
box("tactile_walk2", 0.9, -33.5, TACT_Z0, TACT_Z1, 0.4, 104.0, MAT_TACT_NS, bevel=0.0)
# 步道 1: y 19.8..20.2, x -80..50 通长
box("tactile_walk1", -15.0, 20.0, TACT_Z0, TACT_Z1, 130.0, 0.4, MAT_TACT_EW, bevel=0.0)

# ---- 路缘石 (0.15m 宽, 0.1m 高, 浅灰, 0.03m 倒角) ----
# 广场: 北缘在步道 2 口断开为两段; 西/东缘通长; 南缘留 6m 校门开口 (x -3..3), 其余两段
box("curb_plaza_north_W", -10.75, -85.425, CURB_Z0, CURB_Z1, 18.5, 0.15, MAT_CURB, bevel=0.03)
box("curb_plaza_north_E", 10.75, -85.425, CURB_Z0, CURB_Z1, 18.5, 0.15, MAT_CURB, bevel=0.03)
box("curb_plaza_west", -20.075, -98.0, CURB_Z0, CURB_Z1, 0.15, 25.0, MAT_CURB, bevel=0.03)
box("curb_plaza_east", 20.075, -98.0, CURB_Z0, CURB_Z1, 0.15, 25.0, MAT_CURB, bevel=0.03)
box("curb_plaza_south_W", -11.5, -110.575, CURB_Z0, CURB_Z1, 17.0, 0.15, MAT_CURB, bevel=0.03)
box("curb_plaza_south_E", 11.5, -110.575, CURB_Z0, CURB_Z1, 17.0, 0.15, MAT_CURB, bevel=0.03)
# 步道 1: 北缘通长; 南缘在步道 2 口 (x -1.5..1.5) 断开为两段
box("curb_walk1_north", -15.0, 21.575, CURB_Z0, CURB_Z1, 130.0, 0.15, MAT_CURB, bevel=0.03)
box("curb_walk1_south_W", -40.75, 18.425, CURB_Z0, CURB_Z1, 78.5, 0.15, MAT_CURB, bevel=0.03)
box("curb_walk1_south_E", 25.75, 18.425, CURB_Z0, CURB_Z1, 48.5, 0.15, MAT_CURB, bevel=0.03)
# 步道 2: 东西两侧, y -85.35..18.35 (两端顶住相邻路缘石, 不重叠)
box("curb_walk2_west", -1.575, -33.5, CURB_Z0, CURB_Z1, 0.15, 103.7, MAT_CURB, bevel=0.03)
box("curb_walk2_east", 1.575, -33.5, CURB_Z0, CURB_Z1, 0.15, 103.7, MAT_CURB, bevel=0.03)

print("walk objects:", len(walk))

# ---- save .blend (落盘优先, 先存盘再导出) ----
os.makedirs(PY_DIR, exist_ok=True)
os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("saved blend:", BLEND_PATH)
if os.path.exists(BLEND_PATH + "1"):
    os.remove(BLEND_PATH + "1")
    print("removed blend1")

# ---- export .glb (walk objects only) ----
bpy.ops.object.select_all(action="DESELECT")
for o in walk:
    o.select_set(True)
bpy.context.view_layer.objects.active = walk[0]
bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format="GLB",
                           use_selection=True, export_apply=True)
print("exported glb:", GLB_PATH, "objects:", len(walk))

# ---- read back the .glb to confirm it opens, then drop the duplicates ----
bpy.ops.object.select_all(action="DESELECT")
bpy.ops.import_scene.gltf(filepath=GLB_PATH)
imported = [o for o in bpy.context.selected_objects]
print("glb re-import OK, imported objects:", len(imported))
bpy.ops.object.delete(use_global=False)  # remove re-imported copies
print("re-imported copies deleted, scene objects:", len(bpy.context.scene.objects))

print("DONE ov-road-walk")
