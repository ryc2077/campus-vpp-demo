# ov-road-main: 主干道 (overview piece)
# 南侧主路 y=-108 (x -130..130, 宽 12m) + 东侧主路 x=108 (y -102..110, 宽 12m)
# + 环校路矩形环 x ±95 / y ±80 (宽 8m, 拐角 45°倒角) + 黄色中心线 + 路缘石
# 只做路面、中心线、路缘石；不做步道铺装 (ov-road-walk)、不做路灯 (ov-flag-lamp)。
# 沥青灰 #424A52, 黄线 #E8B400, 路缘石浅灰 #B9B3A8 (SPEC §3)。
#
# 接缝处理 (避免共面 z-fighting):
# - 东侧主路从 y=-102 起 (南侧主路北缘), 不与南侧主路重叠, 形成丁字路口。
# - 环校路 4 段直路 + 4 个倒角五边形角块拼成, 直路段端头与角块端点精确对接, 互不重叠。
# - 南侧主路北侧路缘石在东侧主路口断开 (x 102..114 留出路口)。
# - 黄色中心线只做南、东两条主路 ("主路各一条"); 环校路为校内路, 按鸟瞰图不画黄线。
#   (2026-11-23 修正: 鸟瞰图里内环路基本被楼体遮挡, 无法确认有无黄线;
#   SPEC §5 本件写明含"黄色中心线", 第二轮复核点名环路无中心线, 故按 SPEC 补齐
#   环路中心线: 4 直段 + 4 拐角斜段, 与主路同宽 0.15m。)
# - 烘焙颜色变化 (2026-11-23 修复, 见 make_mat): DIFFUSE 烘焙只取 Base Color,
#   底色不链接时烘出的 color 图是纯色 (实测 Asphalt 59% 纯黑未烘焙区 + 其余纯底色),
#   法线图也近乎平坦 (灰度标准差约 1), 所以渲染全图纯色。修复: 烘焙前把颗粒/磨损
#   以 MixRGB 乘进 Base Color (只为烘焙提供颜色变化), 并加强 Bump;
#   _rebuild_with_images 会删掉全部节点用烘好的贴图重建, 最终材质只连烘焙贴图,
#   glTF 不受影响。

import bpy
import math
import os
from mathutils import Vector

PIECE = "ov-road-main"
BASE = os.path.expanduser("~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
PY_DIR = os.path.join(BASE, "assets/blender/overview")
BLEND_PATH = os.path.join(PY_DIR, "ov-road-main.blend")
GLB_PATH = os.path.join(BASE, "assets/models/ov-road-main.glb")
PNG_PATH = os.path.join(BASE, "screenshots/blender/ov-road-main.png")

ROAD_Z0, ROAD_Z1 = 0.0, 0.08      # 沥青路面厚 0.08m
LINE_Z0, LINE_Z1 = 0.08, 0.105    # 黄线贴在路面上
CURB_Z0, CURB_Z1 = 0.0, 0.12      # 路缘石高 0.12m
CH = 4.0 * math.sqrt(2.0)         # 拐角斜段长 (4m 倒角的斜边)


def hex_rgb(h):
    """Hex sRGB -> linear RGB."""
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
    # Math 节点 -> 取其输出 socket; socket 本身 -> 原样返回
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


def make_mat(name, hexcol, rough=0.9, metallic=0.0, kind="asphalt"):
    """程序化纹理材质 (只动材质节点, 不动几何):
    - 底色/粗糙度保持不链接 (默认值=色板值): 实测导出器遇到 MixRGB/ValToRGB 链接会丢
      baseColorFactor (Godot 里变白), 只有不链接或直连 RGB 节点才保留, 所以颜色因子走默认值。
    - 纹理全部走 Bump(法线): 噪波 + Voronoi, Object 坐标(米制), 各件尺度一致, 预览图可见。
    - asphalt: Voronoi 颗粒(0.5m 胞) + Voronoi 边距细裂纹(2.2m 胞网) + 大尺度噪波磨损/修补痕。
    - concrete(路缘石): 细噪波骨料 + 小 Voronoi 麻点 + 斑驳, 无裂纹网, 与沥青不同。
    - paint(标线): 粗噪波磨损漆面, 轻微凹凸。
    - grass(草地): 单层噪波斑驳(省求值)。"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = hex_rgb(hexcol)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic

    texcoord = nt.nodes.new("ShaderNodeTexCoord")

    if kind == "asphalt":
        # 颗粒: Voronoi F1 距离 (0.5m 胞, 每格明暗起伏)
        grain = _voronoi(nt, texcoord, 2.0, "F1").outputs["Distance"]
        # 磨损/修补: 大尺度噪波 (4m 斑块)
        wear = _noise(nt, texcoord, 0.25, 2.0).outputs["Fac"]
        # 大斑块: 极低频噪波 (20m 级明暗, 顶面 UV 沿路向每纹素约 4.6m,
        # 4m 斑块会被抹平, 只有 20m 级能在渲染尺度留住明暗变化)
        patch_big = _noise(nt, texcoord, 0.05, 2.0).outputs["Fac"]
        # 细裂纹: Voronoi 边距 (2.2m 胞网), 边缘处下陷成沟
        crack_dist = _voronoi(nt, texcoord, 0.45, "DISTANCE_TO_EDGE").outputs["Distance"]
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.0
        ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
        ramp.color_ramp.elements[1].position = 0.15
        ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
        nt.links.new(crack_dist, ramp.inputs["Fac"])
        crack = _math(nt, "SUBTRACT", 1.0, ramp.outputs["Color"])
        # 修补痕: 复用磨损噪波做阈值斑块 (8m 级修补区, 胞内整体抬升, 与周围颗粒感不同)
        ramp_p = nt.nodes.new("ShaderNodeValToRGB")
        ramp_p.color_ramp.elements[0].position = 0.55
        ramp_p.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
        ramp_p.color_ramp.elements[1].position = 0.75
        ramp_p.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
        nt.links.new(wear, ramp_p.inputs["Fac"])
        h = _math(nt, "ADD",
                  _math(nt, "MULTIPLY", grain, 0.5),
                  _math(nt, "MULTIPLY", wear, 0.5))
        h = _math(nt, "SUBTRACT", h, _math(nt, "MULTIPLY", crack, 0.5), clamp=True)
        h = _math(nt, "ADD", h, _math(nt, "MULTIPLY", ramp_p.outputs["Color"], 0.15), clamp=True)
        # 烘焙用颜色因子 (2026-11-23 探针实测: Noise Fac 线性标准差约 0.09~0.10、
        # Voronoi F1 Distance 约 0.19, 均值约 0.5; 所以因子以 1.0 为中心放大偏差,
        # 均值不变、底色不变。大斑块 1.0±0.10 × 磨损 1.0±0.09 × 颗粒 1.0±0.10
        # × 修补 1.00~1.12, 合计线性标准差约 0.17)
        color_factor = _math(nt, "MULTIPLY",
            _math(nt, "MULTIPLY",
                  _math(nt, "ADD", _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", patch_big, 0.5), 1.1), 1.0),
                  _math(nt, "ADD", _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", wear, 0.5), 0.9), 1.0)),
            _math(nt, "MULTIPLY",
                  _math(nt, "ADD", _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", grain, 0.5), 0.55), 1.0),
                  _math(nt, "ADD", _math(nt, "MULTIPLY", ramp_p.outputs["Color"], 0.12), 1.0)))
        strength, dist = 0.9, 0.20
    elif kind == "concrete":
        # 混凝土路缘石: 细骨料噪波 + 小 Voronoi 麻点 + 斑驳, 无裂纹网
        agg = _noise(nt, texcoord, 1.5, 2.0).outputs["Fac"]
        speck = _voronoi(nt, texcoord, 5.0, "F1").outputs["Distance"]
        blotch = _noise(nt, texcoord, 0.6, 2.0).outputs["Fac"]
        h = _math(nt, "ADD",
                  _math(nt, "MULTIPLY", _math(nt, "ADD", agg, speck), 0.35),
                  _math(nt, "MULTIPLY", blotch, 0.3), clamp=True)
        # 烘焙用颜色因子 (以 1.0 为中心放大偏差, 均值不变): 骨料 ±0.08
        # × 麻点 ±0.08 × 斑驳 ±0.06
        color_factor = _math(nt, "MULTIPLY",
            _math(nt, "MULTIPLY",
                  _math(nt, "ADD", _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", agg, 0.5), 0.8), 1.0),
                  _math(nt, "ADD", _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", speck, 0.2), 1.0), 1.0)),
            _math(nt, "ADD", _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", blotch, 0.5), 0.7), 1.0))
        strength, dist = 0.4, 0.08
    elif kind == "paint":
        # 磨损漆面标线: 粗噪波斑驳, 轻微凹凸
        w1 = _noise(nt, texcoord, 3.0, 2.0).outputs["Fac"]
        h = _math(nt, "MULTIPLY", w1, 0.7, clamp=True)
        # 烘焙用颜色因子 (以 1.0 为中心放大偏差, 均值不变): 磨损 ±0.08 (掉漆斑驳)
        color_factor = _math(nt, "ADD", _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", w1, 0.5), 1.5), 1.0)
        strength, dist = 0.15, 0.05
    else:  # grass (单层噪波斑驳即可, 省求值)
        g1 = _noise(nt, texcoord, 0.5, 2.0).outputs["Fac"]
        h = _math(nt, "MULTIPLY", g1, 0.8, clamp=True)
        color_factor = _math(nt, "ADD", _math(nt, "MULTIPLY", _math(nt, "SUBTRACT", g1, 0.5), 0.8), 1.0)
        strength, dist = 0.12, 0.05

    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = strength
    bump.inputs["Distance"].default_value = dist
    nt.links.new(_sock(h), bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    # ---- 烘焙用颜色变化 (只为烘焙服务, 见文件头注释) ----
    # Base Color = 底色 RGB × 颜色因子 (MixRGB 乘法)。烘焙时 DIFFUSE/color
    # 通道取到这个值; 烘焙后 _rebuild_with_images 删掉全部节点, 最终材质
    # Base Color 只连烘焙贴图, 这条临时链不进 .blend/.glb。
    base_rgb = nt.nodes.new("ShaderNodeRGB")
    base_rgb.outputs[0].default_value = hex_rgb(hexcol)
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = 'MULTIPLY'
    mix.inputs["Fac"].default_value = 1.0
    nt.links.new(base_rgb.outputs["Color"], mix.inputs["Color1"])
    nt.links.new(_sock(color_factor), mix.inputs["Color2"])
    nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    return m


MAT_ROAD = make_mat("Asphalt_424A52", "#424A52", 0.9, kind="asphalt")
MAT_LINE = make_mat("YellowLine_E8B400", "#E8B400", 0.8, kind="paint")
MAT_CURB = make_mat("Curb_B9B3A8", "#B9B3A8", 0.95, kind="concrete")
MAT_GROUND = make_mat("Ground_Grass_69B45E", "#69B45E", 1.0, kind="grass")

# ---- clean scene ----
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

roads = []  # objects that go into the .glb


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
    roads.append(o)
    return o


def prism(name, pts, z0, z1, mat):
    """Flat prism from a CCW 2D polygon (x, y) list, z0..z1. No bevel."""
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
    roads.append(o)
    return o


# ---- 南侧主路: y=-108, x -130..130, 宽 12m ----
box("road_S_main", 0.0, -108.0, ROAD_Z0, ROAD_Z1, 260.0, 12.0, MAT_ROAD)
# ---- 东侧主路: x=108, y -102..110 (从南路北缘起, 不重叠), 宽 12m ----
box("road_E_main", 108.0, 4.0, ROAD_Z0, ROAD_Z1, 12.0, 212.0, MAT_ROAD)

# ---- 环校路直路 4 段 (宽 8m) ----
box("road_ring_N", 0.0, 80.0, ROAD_Z0, ROAD_Z1, 182.0, 8.0, MAT_ROAD)
box("road_ring_S", 0.0, -80.0, ROAD_Z0, ROAD_Z1, 182.0, 8.0, MAT_ROAD)
box("road_ring_W", -95.0, 0.0, ROAD_Z0, ROAD_Z1, 8.0, 152.0, MAT_ROAD)
box("road_ring_E", 95.0, 0.0, ROAD_Z0, ROAD_Z1, 8.0, 152.0, MAT_ROAD)
# ---- 环校路拐角: 4m 45°倒角五边形角块 (8x8 角区, 外角切掉) ----
prism("road_ring_corner_NE", [(91, 76), (99, 76), (99, 80), (95, 84), (91, 84)],
      ROAD_Z0, ROAD_Z1, MAT_ROAD)
prism("road_ring_corner_NW", [(-91, 76), (-91, 84), (-95, 84), (-99, 80), (-99, 76)],
      ROAD_Z0, ROAD_Z1, MAT_ROAD)
prism("road_ring_corner_SE", [(91, -76), (91, -84), (95, -84), (99, -80), (99, -76)],
      ROAD_Z0, ROAD_Z1, MAT_ROAD)
prism("road_ring_corner_SW", [(-91, -76), (-99, -76), (-99, -80), (-95, -84), (-91, -84)],
      ROAD_Z0, ROAD_Z1, MAT_ROAD)

# ---- 黄色中心线 (0.15m 宽, 主路各一条 + 环路一圈) ----
box("line_S_main", 0.0, -108.0, LINE_Z0, LINE_Z1, 260.0, 0.15, MAT_LINE, bevel=0.0)
box("line_E_main", 108.0, 4.0, LINE_Z0, LINE_Z1, 0.15, 212.0, MAT_LINE, bevel=0.0)
# 环路中心线 (2026-11-23 补, 见文件头): 4 直段沿环路中心, 4 斜段过拐角
# (斜段中心 (93,78) 等、长 CH, 与路缘石斜段平行且居中, 方向与路缘石斜段一致)
box("line_ring_N", 0.0, 80.0, LINE_Z0, LINE_Z1, 182.0, 0.15, MAT_LINE, bevel=0.0)
box("line_ring_S", 0.0, -80.0, LINE_Z0, LINE_Z1, 182.0, 0.15, MAT_LINE, bevel=0.0)
box("line_ring_W", -95.0, 0.0, LINE_Z0, LINE_Z1, 0.15, 152.0, MAT_LINE, bevel=0.0)
box("line_ring_E", 95.0, 0.0, LINE_Z0, LINE_Z1, 0.15, 152.0, MAT_LINE, bevel=0.0)
box("line_ring_chamfer_NE", 93.0, 78.0, LINE_Z0, LINE_Z1,
    CH, 0.15, MAT_LINE, bevel=0.0, rot_z=-math.pi / 4)
box("line_ring_chamfer_NW", -93.0, 78.0, LINE_Z0, LINE_Z1,
    CH, 0.15, MAT_LINE, bevel=0.0, rot_z=math.pi / 4)
box("line_ring_chamfer_SE", 93.0, -78.0, LINE_Z0, LINE_Z1,
    CH, 0.15, MAT_LINE, bevel=0.0, rot_z=math.pi / 4)
box("line_ring_chamfer_SW", -93.0, -78.0, LINE_Z0, LINE_Z1,
    CH, 0.15, MAT_LINE, bevel=0.0, rot_z=-math.pi / 4)

# ---- 路缘石 (0.3m 宽, 0.12m 高, 浅灰) ----
# 南侧主路: 南缘通长; 北缘在东侧主路口 (x 102..114) 断开
box("curb_S_south", 0.0, -114.15, CURB_Z0, CURB_Z1, 260.0, 0.3, MAT_CURB)
box("curb_S_north_W", -14.0, -101.85, CURB_Z0, CURB_Z1, 232.0, 0.3, MAT_CURB)
box("curb_S_north_E", 122.0, -101.85, CURB_Z0, CURB_Z1, 16.0, 0.3, MAT_CURB)
# 东侧主路: 东西两侧
box("curb_E_west", 101.85, 4.0, CURB_Z0, CURB_Z1, 0.3, 212.0, MAT_CURB)
box("curb_E_east", 114.15, 4.0, CURB_Z0, CURB_Z1, 0.3, 212.0, MAT_CURB)
# 环校路: 内外缘直段 8 条
box("curb_ring_outer_N", 0.0, 84.15, CURB_Z0, CURB_Z1, 190.0, 0.3, MAT_CURB)
box("curb_ring_outer_S", 0.0, -84.15, CURB_Z0, CURB_Z1, 190.0, 0.3, MAT_CURB)
box("curb_ring_outer_W", -99.15, 0.0, CURB_Z0, CURB_Z1, 0.3, 160.0, MAT_CURB)
box("curb_ring_outer_E", 99.15, 0.0, CURB_Z0, CURB_Z1, 0.3, 160.0, MAT_CURB)
box("curb_ring_inner_N", 0.0, 75.85, CURB_Z0, CURB_Z1, 174.0, 0.3, MAT_CURB)
box("curb_ring_inner_S", 0.0, -75.85, CURB_Z0, CURB_Z1, 174.0, 0.3, MAT_CURB)
box("curb_ring_inner_W", -90.85, 0.0, CURB_Z0, CURB_Z1, 0.3, 144.0, MAT_CURB)
box("curb_ring_inner_E", 90.85, 0.0, CURB_Z0, CURB_Z1, 0.3, 144.0, MAT_CURB)
# 环校路: 倒角斜段 8 条 (长 4*sqrt(2)=5.657m, 沿倒角线, 向内外各偏 0.15m)
OFF = 0.15 / math.sqrt(2.0)
box("curb_ring_chamfer_outer_NE", 97 + OFF, 82 + OFF, CURB_Z0, CURB_Z1,
    CH, 0.3, MAT_CURB, rot_z=-math.pi / 4)
box("curb_ring_chamfer_outer_NW", -97 - OFF, 82 + OFF, CURB_Z0, CURB_Z1,
    CH, 0.3, MAT_CURB, rot_z=math.pi / 4)
box("curb_ring_chamfer_outer_SE", 97 + OFF, -82 - OFF, CURB_Z0, CURB_Z1,
    CH, 0.3, MAT_CURB, rot_z=math.pi / 4)
box("curb_ring_chamfer_outer_SW", -97 - OFF, -82 - OFF, CURB_Z0, CURB_Z1,
    CH, 0.3, MAT_CURB, rot_z=-math.pi / 4)
box("curb_ring_chamfer_inner_NE", 89 - OFF, 74 - OFF, CURB_Z0, CURB_Z1,
    CH, 0.3, MAT_CURB, rot_z=-math.pi / 4)
box("curb_ring_chamfer_inner_NW", -89 + OFF, 74 - OFF, CURB_Z0, CURB_Z1,
    CH, 0.3, MAT_CURB, rot_z=math.pi / 4)
box("curb_ring_chamfer_inner_SE", 89 - OFF, -74 + OFF, CURB_Z0, CURB_Z1,
    CH, 0.3, MAT_CURB, rot_z=math.pi / 4)
box("curb_ring_chamfer_inner_SW", -89 + OFF, -74 + OFF, CURB_Z0, CURB_Z1,
    CH, 0.3, MAT_CURB, rot_z=-math.pi / 4)

print("road objects:", len(roads))

# ---- preview-only ground (NOT exported) ----
bpy.ops.mesh.primitive_plane_add(location=(0.0, 0.0, -0.01))
ground = bpy.context.active_object
ground.name = "Ground_PreviewOnly"
ground.dimensions = (320.0, 280.0, 0.0)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
ground.data.materials.append(MAT_GROUND)

# ---- lighting (SPEC section 2): sun 3.5 from SW, elev ~50 deg ----
target = Vector((0.0, 0.0, 0.0))
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

# ---- camera: top-down (task: 俯视能看清路网), 400m up, lens 35mm ----
# vertical FOV ~37.8 deg -> covers ~274m at ground, road net spans 228m.
bpy.ops.object.camera_add(location=(0.0, 0.0, 400.0))
cam = bpy.context.active_object
cam.name = "Cam_Preview"
cam.data.lens = 35.0
# 深度精度: 机位 400m 高, 默认 clip 0.1~1000 时深度缓冲在 400m 处精度约 10cm,
# 分辨不出高出地面仅 0.08m 的路面 (地面会盖掉路面, 已实测复现); 收紧到 300~500m 即可。
cam.data.clip_start = 300.0
cam.data.clip_end = 500.0
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
bpy.context.scene.camera = cam

# ---------- 烘焙程序化纹理为图片 (照抄 dist/di-walls.py 已验证做法) ----------
# glTF 无法导出 Noise/Voronoi 程序化节点: 每种不透明材质选其全部对象,
# Cycles CPU (samples 4) 烘焙 color/rough/normal 三张 1024px 图
# (diffuse 只取 color 通道, 不带光照; margin 16px), 再重建材质为图片纹理节点。
# 立方体自带 UV (每面 0~1); from_pydata 的棱柱角块没有 UV, 先补 UV 再烘焙。
# 同材质各对象先经 _pack_uvs 缩进 1024 图的不重叠瓦片再烘焙 (照抄 ov-road-walk),
# 每纹素只烘焙一次, 否则各面重叠 UV 会让同一纹理区被反复烘焙。
import time
TEX_DIR = os.path.join(PY_DIR, "ov-road-main_textures")
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
    0~1 全图重叠, 不分瓦片时同一纹素会被每个对象反复烘焙, 对象越多越慢;
    分瓦片后每纹素只烘焙一次。只改 UV, 不动几何/配色/位置; 导出 GLB 时
    UV 随贴图一起走, Godot 采样正确。(照抄 ov-road-walk.py / ov-track.py)"""
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
for _ob in roads:
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

# ---- save .blend ----
os.makedirs(PY_DIR, exist_ok=True)
os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
os.makedirs(os.path.dirname(PNG_PATH), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("saved blend:", BLEND_PATH)
if os.path.exists(BLEND_PATH + "1"):
    os.remove(BLEND_PATH + "1")
    print("removed blend1")

# ---- export .glb (road objects only) ----
bpy.ops.object.select_all(action="DESELECT")
for o in roads:
    o.select_set(True)
bpy.context.view_layer.objects.active = roads[0]
bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format="GLB",
                           use_selection=True, export_apply=True)
print("exported glb:", GLB_PATH, "objects:", len(roads))

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
assert len(imported) == len(roads), "glb reimport failed: expected %d objects, got %d" % (len(roads), len(imported))
bpy.ops.object.select_all(action='DESELECT')
for ob in imported:
    ob.select_set(True)
bpy.ops.object.delete()
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
# 本地不渲染预览图 (渲染全部走 GitHub Actions); 上面的渲染设置留给 Actions 用。
print("preview render skipped (GitHub Actions renders):", PNG_PATH)

print("DONE ov-road-main")
