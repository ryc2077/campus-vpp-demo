# ov-road-walk v2: 步道与铺装 (overview piece)
# R2-T14 (2026-11-24): 按 GREEN_PLAN.md §2 / green_layout.json roads[] 新增 6 条步道
#  (R-N1/R-N2/R-N3/R-N3x/R-N4/R-N5, 约 438m 中心线长), 全部归本件 (ov-road-walk 分工);
#  新路面用已下载的 Poly Haven concrete_pavement_03 (CC0, SOURCES.md §1.1),
#  经本件既有烘焙管线进 GLB; 环路内缘路缘石在 5 处新路口断开, 改动在 ov-road-main.py。
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

# ---- R2-T14 新路铺装: 已下载的 Poly Haven concrete_pavement_03 (CC0) ----
# SOURCES.md §1.1 指定本贴图对应浅色铺装 #D8D2C4 (南门广场/步道)。
# TexCoord Object -> Mapping(1/2m) -> TexImage, 贴图每 2m 重复一次 (与 st-base 平台
# 每 1m 一 tile 的米制投影同思路); 之后走本件既有 _bake_images/_rebuild_with_images
# 烘焙管线, 最终 GLB 里是烘焙版贴图, 与旧步道做法一致 (烘焙时只读本地 JPG, 不进 .blend)。
PAVE_TEX_DIR = os.path.join(BASE, "assets/external/polyhaven")


def make_pbr_pave(name, tile_m=2.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 1.0
    bsdf.inputs["Metallic"].default_value = 0.0
    texcoord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (1.0 / tile_m, 1.0 / tile_m, 1.0 / tile_m)
    nt.links.new(texcoord.outputs["Object"], mapping.inputs["Vector"])

    def _img(fname, colorspace):
        path = os.path.join(PAVE_TEX_DIR, fname)
        assert os.path.exists(path), "missing paving texture: %s" % path
        img = bpy.data.images.load(path, check_existing=True)
        img.colorspace_settings.name = colorspace
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = img
        nt.links.new(mapping.outputs["Vector"], t.inputs["Vector"])
        return t

    tex_c = _img("concrete_pavement_03_diff_1k.jpg", "sRGB")
    tex_r = _img("concrete_pavement_03_rough_1k.jpg", "Non-Color")
    tex_n = _img("concrete_pavement_03_nor_gl_1k.jpg", "Non-Color")
    nt.links.new(tex_c.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(tex_r.outputs["Color"], bsdf.inputs["Roughness"])
    nmap = nt.nodes.new("ShaderNodeNormalMap")
    nmap.space = 'TANGENT'
    nt.links.new(tex_n.outputs["Color"], nmap.inputs["Color"])
    nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    return m


MAT_PAVE_NEW = make_pbr_pave("PavingNew_ConcretePavement03")

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


def _signed_area(pts):
    return 0.5 * sum(x1 * y2 - x2 * y1
                     for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]))


def _seg_intersect(p1, p2, p3, p4):
    """两线段交点 (2D); 平行或交点落在线段外返回 None。"""
    d1 = (p2[0] - p1[0], p2[1] - p1[1])
    d2 = (p4[0] - p3[0], p4[1] - p3[1])
    den = d1[0] * d2[1] - d1[1] * d2[0]
    if abs(den) < 1e-12:
        return None
    t = ((p3[0] - p1[0]) * d2[1] - (p3[1] - p1[1]) * d2[0]) / den
    u = ((p3[0] - p1[0]) * d1[1] - (p3[1] - p1[1]) * d1[0]) / den
    if -1e-9 <= t <= 1 + 1e-9 and -1e-9 <= u <= 1 + 1e-9:
        return (p1[0] + t * d1[0], p1[1] + t * d1[1])
    return None


def _poly_simple(pts):
    """简单多边形校验: 不相邻边无交点 (R-N4 并集轮廓用, 自交会让棱柱法线翻转)。"""
    n = len(pts)
    for i in range(n):
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue
            if _seg_intersect(pts[i], pts[(i + 1) % n], pts[j], pts[(j + 1) % n]):
                return False
    return True


def ribbon(name, pts, z0, z1, mat):
    """扁平棱柱: 2D 多边形 (x, y) 列表, z0..z1。无倒角。
    (照抄 ov-road-main.py 的 prism, 归属本件 walk 列表; 多边形须为 CCW,
    顺时针传进来时自动反转, 并校验简单多边形。)"""
    pts = list(pts)
    if _signed_area(pts) < 0:
        pts = list(reversed(pts))
    assert _signed_area(pts) > 0, "ribbon %s: degenerate polygon" % name
    assert _poly_simple(pts), "ribbon %s: self-intersecting polygon" % name
    n = len(pts)
    verts = [(x, y, z0) for x, y in pts] + [(x, y, z1) for x, y in pts]
    faces = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    me = bpy.data.meshes.new(name + "_mesh")
    me.from_pydata(verts, [], faces)
    me.update()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(mat)
    walk.append(o)
    return o


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

# ---- R2-T14 新路 (GREEN_PLAN.md §2 / green_layout.json roads[], 2026-11-24) ----
# 全部 3m 铺装步道 (R-N4 2m), 顶面 z=0.10 与旧步道同高, 路面 concrete_pavement_03
# (MAT_PAVE_NEW), 两侧路缘石 0.15m #B9B3A8 (MAT_CURB, 与旧件同款)。
# 接缝规矩照旧件: 端头与相邻路面精确对接、互不重叠; 路缘石在路口处断开、顶住相邻
# 路缘石面 (南/北端照 walkway_2 做法: 路缘止于相邻路缘石面, 不重叠)。
# 实施几何 (中心线长; 铺装以对接计, 两端已是既有路面的 3m/1.5m 不重复铺):
#  R-N1 y=44, x -91..91 (182m): 两端顶环西/东路内缘 (x=±91)。
#  R-N2 x=-33, y -76..18.5 (94.5m): 南端顶环南路北缘 (y=-76), 北端顶步道 1 南缘。
#  R-N3 x=58, y -76..18.5 (94.5m): 同上; 复核见本段末尾。
#  R-N3x y=20, x 50..59.5 (9.5m): 西端接步道 1 东端 (x=50), 东端齐 R-N3 东缘 (59.5)。
#  R-N5 x=9.5, y 21.5..42.5 (21m 新铺装; 中心线 18.5..44 共 25.5m): 南端顶步道 1
#    北缘, 北端顶 R-N1 南缘。
#  R-N4 池塘北岸弧 (2m): 弧线点取自 green_layout.json arc.points (55°~140°),
#    中心 (82,-78) rx14/ry11; 西侧斜 spur (71.3,-70.9)->(68,-76), 末端齐环南路北缘;
#    东接 (90,-69)->(91,-69) 顶环东路内缘。弧+spur+东接拼成一条并集轮廓棱柱 (无重叠)。
# R-N3 复核 (GREEN_PLAN §2 施工注意事项第 1 条, 2026-11-24 实测):
#  配电房 dist 外轮廓 SPEC §4: 中心 (48,30) 16x10m -> 东墙 x=56, R-N3 西缘 56.5,
#  净空 0.5m; 储能站 st-base 平台 x 60.5..67.5 / st-fence 围栏 x 60..68, R-N3 东缘
#  59.5, 距围栏 0.5m、距平台 1.0m (方案写的 0.2m 是按另一口径, 实测更宽松, 无需改线);
#  且 R-N3 北端 y=18.5 距两建筑南缘 (y=25/28.5) 6.5m 以上, 纵向无交集。
#  结论: 按原线施工, 无调整。（旧口径“R-N2 西缘距缓冲椭圆东尖 (-37) 2.5m”已作废：禁入区口径为 §33 修法②缓冲椭圆 (+3m, 中心 (-62,-25) rx31/ry43) − R-N2 路廊矩形 x[-34.65,-31.35]×y[-76,18.5]；路 vs 跑道几何 415 对相交已复现并接受为已知问题（§43），黑带系环/铺装共面透镜，切路缘石无效。）
#  另: R-N2 西缘距 bldA 东墙 (-36) 1.5m; R-N1 距 tower 南墙 1.5m、距 canteen 南墙 4m; R-N5 走 bldB/bldC
#  之间 11m 缺口, 距两墙各 4m; R-N4 弧线距水面 3m、spur 在池塘椭圆+0.5m 外 (已采样复核)。
# ---- 直道铺装 ----
box("walkway_RN1_y44", 0.0, 44.0, PAVE_Z0, PAVE_Z1, 182.0, 3.0, MAT_PAVE_NEW)
box("walkway_RN2_x-33", -33.0, -28.75, PAVE_Z0, PAVE_Z1, 3.0, 94.5, MAT_PAVE_NEW)
box("walkway_RN3_x58", 58.0, -28.75, PAVE_Z0, PAVE_Z1, 3.0, 94.5, MAT_PAVE_NEW)
box("walkway_RN3x_y20", 54.75, 20.0, PAVE_Z0, PAVE_Z1, 9.5, 3.0, MAT_PAVE_NEW)
box("walkway_RN5_x9p5", 9.5, 32.0, PAVE_Z0, PAVE_Z1, 3.0, 21.0, MAT_PAVE_NEW)
# ---- 直道路缘石 (0.15m 宽; 在路口处断开) ----
# R-N1: 南北缘在 R-N5 口 (x 8..11) 断开
box("curb_RN1_north_W", -41.5, 45.575, CURB_Z0, CURB_Z1, 99.0, 0.15, MAT_CURB, bevel=0.03)
box("curb_RN1_north_E", 51.0, 45.575, CURB_Z0, CURB_Z1, 80.0, 0.15, MAT_CURB, bevel=0.03)
box("curb_RN1_south_W", -41.5, 42.425, CURB_Z0, CURB_Z1, 99.0, 0.15, MAT_CURB, bevel=0.03)
box("curb_RN1_south_E", 51.0, 42.425, CURB_Z0, CURB_Z1, 80.0, 0.15, MAT_CURB, bevel=0.03)
# R-N2/R-N3: 两侧路缘 y -75.7..18.35 (南端止于环南路内缘石北面, 北端止于步道 1 南缘石南面)
box("curb_RN2_west", -34.575, -28.675, CURB_Z0, CURB_Z1, 0.15, 94.05, MAT_CURB, bevel=0.03)
box("curb_RN2_east", -31.425, -28.675, CURB_Z0, CURB_Z1, 0.15, 94.05, MAT_CURB, bevel=0.03)
box("curb_RN3_west", 56.425, -28.675, CURB_Z0, CURB_Z1, 0.15, 94.05, MAT_CURB, bevel=0.03)
box("curb_RN3_east", 59.575, -28.675, CURB_Z0, CURB_Z1, 0.15, 94.05, MAT_CURB, bevel=0.03)
# R-N3x: 北缘通长 (x 50..59.5); 南缘只到 R-N3 西缘 (x 50..56.5), 东段是 R-N3 路口
box("curb_RN3x_north", 54.75, 21.575, CURB_Z0, CURB_Z1, 9.5, 0.15, MAT_CURB, bevel=0.03)
box("curb_RN3x_south", 53.25, 18.425, CURB_Z0, CURB_Z1, 6.5, 0.15, MAT_CURB, bevel=0.03)
# R-N5: 两侧路缘 y 21.65..42.35 (南端顶步道 1 北缘石, 北端顶 R-N1 南缘石)
box("curb_RN5_west", 7.925, 32.0, CURB_Z0, CURB_Z1, 0.15, 20.7, MAT_CURB, bevel=0.03)
box("curb_RN5_east", 11.075, 32.0, CURB_Z0, CURB_Z1, 0.15, 20.7, MAT_CURB, bevel=0.03)
# ---- R-N4 池塘北岸步道 (2m): 弧 + spur + 东接, 一条并集轮廓棱柱 ----
# 弧线点照抄 green_layout.json R-N4 arc.points (18 点, 55°~140°)。
ARC_PTS = [(90.03, -68.99), (89.0, -68.47), (87.92, -68.03), (86.79, -67.66),
           (85.62, -67.37), (84.43, -67.17), (83.22, -67.04), (82.0, -67.0),
           (80.78, -67.04), (79.57, -67.17), (78.38, -67.37), (77.21, -67.66),
           (76.08, -68.03), (75.0, -68.47), (73.97, -68.99), (73.0, -69.57),
           (72.1, -70.22), (71.28, -70.93)]
POND_C = (82.0, -78.0)
ARC_RX, ARC_RY = 14.0, 11.0


def _arc_n(px, py):
    """池塘椭圆外法向 ∝ ((x-cx)/rx², (y-cy)/ry²), 归一化。"""
    nx = (px - POND_C[0]) / ARC_RX ** 2
    ny = (py - POND_C[1]) / ARC_RY ** 2
    l = math.hypot(nx, ny)
    return (nx / l, ny / l)


_arc_nrm = [_arc_n(x, y) for x, y in ARC_PTS]
_arc_outer = [(x + nx, y + ny) for (x, y), (nx, ny) in zip(ARC_PTS, _arc_nrm)]
_arc_inner = [(x - nx, y - ny) for (x, y), (nx, ny) in zip(ARC_PTS, _arc_nrm)]
# spur: A=(71.3,-70.9) -> B=(68,-76); 末端切齐环南路北缘 y=-76 (不伸进环路)。
SPUR_A = (71.3, -70.9)
_spur_d = (68.0 - SPUR_A[0], -76.0 - SPUR_A[1])
_spur_l = math.hypot(*_spur_d)
_spur_dir = (_spur_d[0] / _spur_l, _spur_d[1] / _spur_l)
_spur_out = (_spur_dir[1], -_spur_dir[0])    # 西北侧, 远离池塘
_spur_in = (-_spur_dir[1], _spur_dir[0])     # 东南侧, 朝向池塘


def _spur_side_pt(side, y_target):
    px = SPUR_A[0] + side[0]
    py = SPUR_A[1] + side[1]
    t = (y_target - py) / _spur_dir[1]
    return (px + _spur_dir[0] * t, y_target)


_spur_out_end = _spur_side_pt(_spur_out, -76.0)
_spur_in_end = _spur_side_pt(_spur_in, -76.0)
# 东接: 弧东端盖线 (过 ARC_PTS[0], 方向为该点外法向) 与 y=-70 (东接南缘) 的交点。
_n0 = _arc_nrm[0]
_tcap = (-70.0 - ARC_PTS[0][1]) / _n0[1]
_cap_s = (ARC_PTS[0][0] + _n0[0] * _tcap, -70.0)
# spur 内侧边与弧内缘最后一段的交点: spur 走向与弧切向约差 13°, 内侧边会切过弧内缘
# 最后一段, 并集轮廓须走交点 (不走弧内缘末点, 否则轮廓自交)。
_spur_in_start = (SPUR_A[0] + _spur_in[0], SPUR_A[1] + _spur_in[1])
_rn4_join = _seg_intersect(_arc_inner[-2], _arc_inner[-1],
                           _spur_in_start, _spur_in_end)
assert _rn4_join is not None, "R-N4: spur inner edge misses arc inner edge"
print("R-N4 spur/arc inner join:", _rn4_join,
      "spur tip x range: %.2f..%.2f" % (min(_spur_out_end[0], _spur_in_end[0]),
                                        max(_spur_out_end[0], _spur_in_end[0])))
_rn4_outline = [
    (91.0, -68.0), (91.0, -70.0), _cap_s,
    _arc_inner[0],
] + _arc_inner[1:-1] + [
    _rn4_join,
    _spur_in_end, _spur_out_end,
    (SPUR_A[0] + _spur_out[0], SPUR_A[1] + _spur_out[1]),
    _arc_outer[-1],
] + list(reversed(_arc_outer[:-1]))
ribbon("walkway_RN4_pond_arc", _rn4_outline, PAVE_Z0, PAVE_Z1, MAT_PAVE_NEW)
# R-N4 路缘石: 弧两侧各一条带状棱柱 (距中心线 1.0~1.15m); 1m 东接 stub 不另做路缘
# (两端分别是弧端路缘与环路内缘石); spur 两侧各一条斜盒, 南端止于环南路内缘石北面。
_rn4_curb_out = [(x + nx * 1.15, y + ny * 1.15) for (x, y), (nx, ny)
                 in zip(ARC_PTS, _arc_nrm)]
_rn4_curb_out += [(x + nx * 1.0, y + ny * 1.0) for (x, y), (nx, ny)
                  in zip(reversed(ARC_PTS), reversed(_arc_nrm))]
ribbon("curb_RN4_outer", _rn4_curb_out, CURB_Z0, CURB_Z1, MAT_CURB)
_rn4_curb_in = [(x - nx * 1.0, y - ny * 1.0) for (x, y), (nx, ny)
                in zip(ARC_PTS, _arc_nrm)]
_rn4_curb_in += [(x - nx * 1.15, y - ny * 1.15) for (x, y), (nx, ny)
                 in zip(reversed(ARC_PTS), reversed(_arc_nrm))]
ribbon("curb_RN4_inner", _rn4_curb_in, CURB_Z0, CURB_Z1, MAT_CURB)
_spur_curb_len = 5.72  # 自 spur 起点 A 至 y=-75.7 (环南路内缘石北面)
_spur_curb_c = (SPUR_A[0] + _spur_dir[0] * _spur_curb_len / 2.0,
                SPUR_A[1] + _spur_dir[1] * _spur_curb_len / 2.0)
_spur_ang = math.atan2(_spur_dir[1], _spur_dir[0])
box("curb_RN4_spur_out",
    _spur_curb_c[0] + _spur_out[0] * 1.075, _spur_curb_c[1] + _spur_out[1] * 1.075,
    CURB_Z0, CURB_Z1, _spur_curb_len, 0.15, MAT_CURB, bevel=0.0, rot_z=_spur_ang)
box("curb_RN4_spur_in",
    _spur_curb_c[0] + _spur_in[0] * 1.075, _spur_curb_c[1] + _spur_in[1] * 1.075,
    CURB_Z0, CURB_Z1, _spur_curb_len, 0.15, MAT_CURB, bevel=0.0, rot_z=_spur_ang)

print("walk objects:", len(walk))

# ---------- 烘焙程序化纹理为图片 (照抄 dist/di-walls.py 已验证做法) ----------
# glTF 无法导出 Noise/Voronoi/Wave 程序化节点: 每种不透明材质选其全部对象,
# Cycles CPU (samples 4) 烘焙 color/rough/normal 三张 1024px 图
# (diffuse 只取 color 通道, 不带光照; margin 16px), 再重建材质为图片纹理节点。
# 立方体自带 UV (每面 0~1); 本件全部是立方体, 无需补 UV (_ensure_uv 备用)。
import time
TEX_DIR = os.path.join(PY_DIR, "ov-road-walk_textures")
os.makedirs(TEX_DIR, exist_ok=True)
_bake_scene = bpy.context.scene
_bake_t0 = time.time()


def _ensure_uv(ob):
    me = ob.data
    if me is None or not hasattr(me, "uv_layers") or len(me.uv_layers) > 0:
        return
    me.uv_layers.new(name="UVMap")
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.02)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    print("uv added:", ob.name)


def _pack_uvs(mat_objs):
    """把同材质各对象的 UV 分别缩放到一张 1024 图里的不重叠瓦片 (网格排布,
    瓦片间留 32px 间隙, 容纳两侧各 16px 烘焙 margin)。立方体默认 UV 是每面
    0~1 全图重叠, 不分瓦片时同一纹素会被每个对象反复烘焙, 对象越多越慢
    (128 个缝线对象曾让一遍烘焙超过 1 小时); 分瓦片后每纹素只烘焙一次。
    只改 UV, 不动几何/配色/位置; 导出 GLB 时 UV 随贴图一起走, Godot 采样正确。"""
    n = len(mat_objs)
    cols = int(math.ceil(math.sqrt(n)))
    rows = int(math.ceil(n / cols))
    gap = 32.0 / 1024.0  # 瓦片间隙 (UV 单位)
    su = 1.0 / cols - gap
    sv = 1.0 / rows - gap
    for idx, ob in enumerate(mat_objs):
        u_off = (idx % cols) / cols + gap / 2.0
        v_off = (idx // cols) / rows + gap / 2.0
        uv = ob.data.uv_layers.active
        if uv is None:
            continue
        for luv in uv.data:
            u, v = luv.uv
            luv.uv = (u * su + u_off, v * sv + v_off)
    print("uv packed:", len(mat_objs), "objects into", cols, "x", rows, "tiles")


def _bake_images(mat, mat_objs, color_size=1024):
    nt = mat.node_tree
    imgs = {}
    specs = [("color", 'DIFFUSE', color_size, 'sRGB'),
             ("rough", 'ROUGHNESS', 1024, 'Non-Color'),
             ("normal", 'NORMAL', 1024, 'Non-Color')]
    bpy.ops.object.select_all(action='DESELECT')
    for ob in mat_objs:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = mat_objs[0]
    _bake_scene.render.engine = 'CYCLES'
    _bake_scene.cycles.device = 'CPU'
    _bake_scene.cycles.samples = 4
    bake = _bake_scene.render.bake
    bake.use_selected_to_active = False
    bake.margin = 16
    for key, btype, size, cs in specs:
        img = bpy.data.images.new("%s_%s" % (mat.name, key),
                                  width=size, height=size, alpha=False)
        img.colorspace_settings.name = cs
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = img
        nt.nodes.active = tex
        if btype == 'DIFFUSE':
            bake.use_pass_direct = False
            bake.use_pass_indirect = False
            bake.use_pass_color = True
        elif btype == 'NORMAL':
            bake.normal_space = 'TANGENT'
        bpy.ops.object.bake(type=btype)
        img.filepath_raw = os.path.join(TEX_DIR, "%s_%s.png" % (mat.name, key))
        img.file_format = 'PNG'
        img.save()
        imgs[key] = img
        nt.nodes.remove(tex)
        print("baked:", mat.name, key, img.filepath_raw,
              os.path.getsize(img.filepath_raw))
    _bake_scene.render.engine = 'BLENDER_EEVEE_NEXT'
    return imgs


def _rebuild_with_images(mat, imgs):
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    bsdf.inputs["Roughness"].default_value = 1.0
    bsdf.inputs["Metallic"].default_value = 0.0
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    tex_c = nt.nodes.new("ShaderNodeTexImage")
    tex_c.image = imgs["color"]
    nt.links.new(tex_c.outputs["Color"], bsdf.inputs["Base Color"])
    tex_r = nt.nodes.new("ShaderNodeTexImage")
    tex_r.image = imgs["rough"]
    nt.links.new(tex_r.outputs["Color"], bsdf.inputs["Roughness"])
    tex_n = nt.nodes.new("ShaderNodeTexImage")
    tex_n.image = imgs["normal"]
    nmap = nt.nodes.new("ShaderNodeNormalMap")
    nmap.space = 'TANGENT'
    nt.links.new(tex_n.outputs["Color"], nmap.inputs["Color"])
    nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])


_by_mat = {}
for _ob in walk:
    _by_mat.setdefault(_ob.data.materials[0], []).append(_ob)
_baked = {}
for _mat, _m_objs in _by_mat.items():
    for _ob in _m_objs:
        _ensure_uv(_ob)
    _pack_uvs(_m_objs)
    _baked[_mat.name] = _bake_images(_mat, _m_objs)
for _mat in _by_mat:
    _rebuild_with_images(_mat, _baked[_mat.name])
print("bake done, materials rebuilt with image textures, elapsed %.1fs"
      % (time.time() - _bake_t0))

# ---- save .blend (落盘优先, 先存盘再导出) ----
os.makedirs(PY_DIR, exist_ok=True)
os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
# R2-T9 PBR hard fix (2026-11-24): baked maps on big faces were near-flat
# (wall normal std ~0.5-3, asphalt color std ~4 in-tile, one 1024 texture
# stretched over 40 m walls / 260 m roads) so everything rendered as flat
# panels. Re-link real CC0 photo textures + world-scale UVs after the bake
# step, before save/export. Idempotent; see _pbr_apply.py in this dir.
_pbr_hook = os.path.join(os.path.dirname(BLEND_PATH), "_pbr_apply.py")
if os.path.exists(_pbr_hook):
    _pbr_g = {"__name__": "_pbr_apply", "__file__": _pbr_hook}
    exec(compile(open(_pbr_hook).read(), _pbr_hook, "exec"), _pbr_g)
    _pbr_g["apply_pbr"](os.path.splitext(os.path.basename(BLEND_PATH))[0])

# R2-T14b: _pbr_apply._load() 用 bpy.path.relpath() 写 PBR 贴图路径, 而本脚本
# 从空场景起步 (bpy.data.filepath 为空), relpath 以 CWD 为基准: CWD 若是工程
# 根目录会得到 "//assets/..."(相对 .blend 所在 overview/ 目录是错的, 应为
# "//../../assets/..."), 导致导出时贴图找不到、GLB 里 6 种 PBR 材质只剩 1 张
# 空白图 (回读断言 Curb_B9B3A8 贴图 <3 张即为此因, 2026-11-24 实测复现)。
# 此处按 .blend 所在目录 + CWD 双候选解析已存在的真实文件, 改写为正确的
# 相对路径 (存盘时 Blender 不动已是相对的路径, 故须在存盘前修好); 已正确
# 的路径 (如 //ov-road-walk_textures/ 与 //../../assets/) 原样不动, 幂等。
for _im in bpy.data.images:
    _fp = _im.filepath
    if not _fp.startswith("//"):
        continue
    _rel = _fp[2:]
    _abs = None
    for _base in (PY_DIR, os.getcwd()):
        _cand = os.path.join(_base, _rel)
        if os.path.exists(_cand):
            _abs = os.path.normpath(_cand)
            break
    if _abs is None:
        print("PBR path fix: file not found, keep:", _im.name, _fp)
        continue
    _new = "//" + os.path.relpath(_abs, PY_DIR)
    if _new != _fp:
        print("PBR path fix:", _im.name, _fp, "->", _new)
        _im.filepath = _new

# R2-T14b: 贴图打包进 .blend (Actions 渲染用; hook 换入的 PBR 图只存相对路径
# //../../external/..., 而 pbr-tinted/concrete_pavement_03 等源文件不在仓库里,
# 不打包会在 Actions 检出后找不到而渲成品红; run 45440253728 的 ov-road-walk
# 品红即为此因, R2-T9b 18:56 补打包 8 个 .blend 后才修复; 与 ov-tower.py 同款)。
for _im in list(bpy.data.images):
    if _im.name in ("Render Result", "Viewer Node"):
        continue
    if _im.packed_file is None:
        try:
            _im.pack()
            print("packed image:", _im.name, _im.size[:])
        except Exception as _e:
            print("pack image skip:", _im.name, _e)

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
# 回读验证 (di-walls 做法): 对象数一致, 且每种材质的贴图数 >= 3 (烘焙贴图齐全)。
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB_PATH)
imported = [o for o in bpy.data.objects if o not in before]
print("glb re-import OK, imported objects:", len(imported),
      [o.name for o in imported])
for ob in imported:
    for slot in ob.material_slots:
        m = slot.material
        if m and m.use_nodes:
            imgs = [n.image.name for n in m.node_tree.nodes
                    if n.type == 'TEX_IMAGE' and n.image is not None]
            print("GLB reimport mat:", ob.name, m.name, "images:", imgs)
            assert len(imgs) >= 3, "glb material lost baked textures: %s" % m.name
assert len(imported) == len(walk), "glb reimport failed: expected %d objects, got %d" % (len(walk), len(imported))
bpy.ops.object.select_all(action='DESELECT')
for ob in imported:
    ob.select_set(True)
bpy.ops.object.delete()
print("re-imported copies deleted, scene objects:", len(bpy.context.scene.objects))

print("DONE ov-road-walk")
