# di-walls: 配电房地面墙面 (floor + 4 walls + skirting + ceiling)
# 局部坐标: 房中心原点, x=长 16m (-8~+8), y=宽 10m (-5~+5), z 0~8m
# 墙体外缘即房间外缘 (16x10), 墙厚 0.2m, 内缘 x=+-7.8 / y=+-4.8
# 南墙 (y=-5) 门洞 1.2m 宽 x 2.4m 高, 位于 x=0 处, 上方门楣; 其余三面墙完整
# 墙体用分段盒子搭, 不用布尔切割
# 警戒线: 变压器区假设为 4 台主变一字排开 (单台 2.5x1.5m, 间距 0.5m,
#   区心 (0, 0.5), 占地 x -5.75~+5.75, y -0.25~+1.25; di-transformer 件
#   若排布不同, 警戒框需随之改), 线框沿区外缘 0.3m 处, 线宽 0.1m, 贴地面
# 颜色: 地面浅灰环氧 #B9B3A8, 墙米白 #F3E9D2, 踢脚深灰 #424A52,
#   天花板白 #E8E8E8, 警示黄 #E8B400; 材质只用 Principled BSDF
# 纹理 pass (2026-11-22): 程序化纹理, 不动结构
#   墙面: Noise 涂料斑驳 + 近地面水渍深浅, 粗糙度/Bump 有变化
#   地面: Noise 防滑颗粒 + Voronoi 细裂纹 + 大尺度磨损
#   警戒黄线: 边缘斑驳磨损; 踢脚线: 轻微噪波; 天花板: 轻微噪波
#   注意: 程序化 Noise/Voronoi 节点是纹理的生成源, 只存在于脚本里;
#   glTF 导出器不导出程序化纹理 (链上出现不支持节点就整条丢弃,
#   底色/粗糙度回退成白/1.0, 实测如此), 所以建模后把五种材质
#   烘焙成图片纹理 (color/rough/normal), .blend 与 .glb 里用图片
#   纹理节点, Godot 才能看到纹理。烘焙图在 di-walls_textures/。
# 渲染新规矩: 全部走 GitHub Actions, 本地不渲染、不出预览图。
import bpy
import math
import os
from mathutils import Vector

BASE = "/home/hatch/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot"
BLEND_PATH = BASE + "/assets/blender/dist/di-walls.blend"
GLB_PATH = BASE + "/assets/models/di-walls.glb"

# ---------- clean scene ----------
bpy.ops.wm.read_factory_settings(use_empty=True)

def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def hex_to_linear(h):
    h = h.lstrip("#")
    return tuple(srgb_to_linear(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4))

def make_material(name, hex_color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*hex_to_linear(hex_color), 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat

# ---------- 纹理节点小工具 ----------
def _link(nt, src, src_out, dst, dst_in):
    nt.links.new(src.outputs[src_out], dst.inputs[dst_in])

def _noise(nt, scale, detail=2.0, roughness=0.7):
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    n.inputs["Roughness"].default_value = roughness
    return n

def _voronoi_edge(nt, scale):
    v = nt.nodes.new("ShaderNodeTexVoronoi")
    v.feature = 'DISTANCE_TO_EDGE'
    v.inputs["Scale"].default_value = scale
    return v

def _ramp(nt, stops):
    """stops: [(pos, value 0..1), ...] 黑白渐变, 用于控制混合强度。"""
    r = nt.nodes.new("ShaderNodeValToRGB")
    els = r.color_ramp.elements
    while len(els) < len(stops):
        els.new(0.5)
    for el, (pos, val) in zip(els, stops):
        el.position = pos
        el.color = (val, val, val, 1.0)
    return r

def _mix(nt, col1_hex, col2_hex, fac_node, fac_out="Color"):
    m = nt.nodes.new("ShaderNodeMixRGB")
    m.blend_type = 'MIX'
    m.inputs[1].default_value = (*hex_to_linear(col1_hex), 1.0)
    m.inputs[2].default_value = (*hex_to_linear(col2_hex), 1.0)
    if fac_node is not None:
        _link(nt, fac_node, fac_out, m, 0)
    return m

def _scale_fac(nt, src_node, src_out, factor):
    """把 0..1 的因子乘以 factor, 限制混合强度。"""
    m = nt.nodes.new("ShaderNodeMath")
    m.operation = 'MULTIPLY'
    m.inputs[1].default_value = factor
    _link(nt, src_node, src_out, m, 0)
    return m

def _rough_map(nt, noise_node, lo, hi):
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.clamp = True
    mr.inputs["From Min"].default_value = 0.0
    mr.inputs["From Max"].default_value = 1.0
    mr.inputs["To Min"].default_value = lo
    mr.inputs["To Max"].default_value = hi
    _link(nt, noise_node, "Fac", mr, 0)
    return mr

def _bump(nt, noise_node, strength, distance):
    b = nt.nodes.new("ShaderNodeBump")
    b.inputs["Strength"].default_value = strength
    b.inputs["Distance"].default_value = distance
    _link(nt, noise_node, "Fac", b, "Height")
    return b

def _texcoord_mapped(nt, scale):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    _link(nt, tc, "Generated", mp, "Vector")
    return tc, mp

def _finish(mat, color_node, rough_node, bump_node):
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    nt = mat.node_tree
    _link(nt, color_node, "Color", bsdf, "Base Color")
    if rough_node is not None:
        _link(nt, rough_node, "Result", bsdf, "Roughness")
    if bump_node is not None:
        _link(nt, bump_node, "Normal", bsdf, "Normal")

# ---------- 墙面纹理: 涂料斑驳 + 近地面水渍 ----------
# 2026-11-24 返工（验收 run #72：墙面云纹过淡）: 斑驳 Ramp 收窄、污渍色加深、
#   水渍色加深、Bump 加倍，烘焙后墙面云纹在预览里清晰可见。
def tex_wall(mat):
    nt = mat.node_tree
    tc, mp = _texcoord_mapped(nt, 3.0)
    # 大尺度斑驳: Noise -> Ramp(0.30~0.60) -> 底色/污渍色混合
    n1 = _noise(nt, 3.0, 2.0, 0.7)
    _link(nt, mp, "Vector", n1, "Vector")
    r1 = _ramp(nt, [(0.30, 0.0), (0.60, 1.0)])
    _link(nt, n1, "Fac", r1, "Fac")
    mix1 = _mix(nt, "#F3E9D2", "#C9B586", r1)
    # 近地面水渍: Z 越低越重 (0~0.25m 渐变) x 细 Noise
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    _link(nt, tc, "Generated", sep, "Vector")
    hm = nt.nodes.new("ShaderNodeMapRange")
    hm.clamp = True
    hm.inputs["From Min"].default_value = 0.0
    hm.inputs["From Max"].default_value = 0.25
    hm.inputs["To Min"].default_value = 1.0
    hm.inputs["To Max"].default_value = 0.0
    _link(nt, sep, "Z", hm, 0)
    n2 = _noise(nt, 1.5, 2.0, 0.7)
    _link(nt, mp, "Vector", n2, "Vector")
    r2 = _ramp(nt, [(0.5, 0.0), (0.8, 1.0)])
    _link(nt, n2, "Fac", r2, "Fac")
    mult = nt.nodes.new("ShaderNodeMath")
    mult.operation = 'MULTIPLY'
    _link(nt, hm, "Result", mult, 0)
    _link(nt, r2, "Color", mult, 1)
    mix2 = nt.nodes.new("ShaderNodeMixRGB")
    mix2.blend_type = 'MIX'
    mix2.inputs[1].default_value = (*hex_to_linear("#F3E9D2"), 1.0)
    mix2.inputs[2].default_value = (*hex_to_linear("#AF9C6B"), 1.0)
    _link(nt, mix1, "Color", mix2, 1)
    _link(nt, mult, "Value", mix2, 0)
    # 粗糙度 0.78~0.95, Bump 细颗粒
    n3 = _noise(nt, 6.0, 2.0, 0.7)
    _link(nt, mp, "Vector", n3, "Vector")
    rough = _rough_map(nt, n3, 0.78, 0.95)
    n4 = _noise(nt, 14.0, 3.0, 0.6)
    _link(nt, mp, "Vector", n4, "Vector")
    bump = _bump(nt, n4, 0.20, 0.03)
    _finish(mat, mix2, rough, bump)

# ---------- 地面纹理: 防滑颗粒 + 细裂纹 + 磨损 ----------
def tex_floor(mat):
    nt = mat.node_tree
    tc, mp = _texcoord_mapped(nt, 2.0)
    # 细裂纹: Voronoi 距边 -> Ramp(0~0.05 白->黑, 白=裂纹) x0.55 混入深色
    v = _voronoi_edge(nt, 8.0)
    _link(nt, mp, "Vector", v, "Vector")
    rc = _ramp(nt, [(0.0, 1.0), (0.05, 0.0)])
    _link(nt, v, "Distance", rc, "Fac")
    fc = _scale_fac(nt, rc, "Color", 0.55)
    mix1 = _mix(nt, "#B9B3A8", "#8F887B", fc, "Value")
    # 大尺度磨损: Noise -> Ramp x0.5 混入浅色
    n1 = _noise(nt, 1.2, 2.0, 0.7)
    _link(nt, mp, "Vector", n1, "Vector")
    r1 = _ramp(nt, [(0.45, 0.0), (0.75, 1.0)])
    _link(nt, n1, "Fac", r1, "Fac")
    fw = _scale_fac(nt, r1, "Color", 0.5)
    mix2 = nt.nodes.new("ShaderNodeMixRGB")
    mix2.blend_type = 'MIX'
    mix2.inputs[2].default_value = (*hex_to_linear("#CFC8BA"), 1.0)
    _link(nt, mix1, "Color", mix2, 1)
    _link(nt, fw, "Value", mix2, 0)
    # 粗糙度 0.82~0.97, Bump 防滑颗粒
    n3 = _noise(nt, 10.0, 2.0, 0.7)
    _link(nt, mp, "Vector", n3, "Vector")
    rough = _rough_map(nt, n3, 0.82, 0.97)
    n4 = _noise(nt, 30.0, 2.0, 0.6)
    _link(nt, mp, "Vector", n4, "Vector")
    bump = _bump(nt, n4, 0.30, 0.02)
    _finish(mat, mix2, rough, bump)

# ---------- 警戒黄线纹理: 边缘斑驳磨损 ----------
def tex_yellow(mat):
    nt = mat.node_tree
    tc, mp = _texcoord_mapped(nt, 6.0)
    n1 = _noise(nt, 8.0, 2.0, 0.7)
    _link(nt, mp, "Vector", n1, "Vector")
    r1 = _ramp(nt, [(0.45, 0.0), (0.70, 1.0)])
    _link(nt, n1, "Fac", r1, "Fac")
    fw = _scale_fac(nt, r1, "Color", 0.5)
    mix1 = _mix(nt, "#E8B400", "#8A8378", fw, "Value")
    n3 = _noise(nt, 6.0, 2.0, 0.7)
    _link(nt, mp, "Vector", n3, "Vector")
    rough = _rough_map(nt, n3, 0.50, 0.75)
    n4 = _noise(nt, 18.0, 2.0, 0.6)
    _link(nt, mp, "Vector", n4, "Vector")
    bump = _bump(nt, n4, 0.12, 0.02)
    _finish(mat, mix1, rough, bump)

# ---------- 踢脚线纹理: 轻微噪波 ----------
def tex_skirt(mat):
    nt = mat.node_tree
    tc, mp = _texcoord_mapped(nt, 5.0)
    n1 = _noise(nt, 5.0, 2.0, 0.7)
    _link(nt, mp, "Vector", n1, "Vector")
    r1 = _ramp(nt, [(0.40, 0.0), (0.70, 1.0)])
    _link(nt, n1, "Fac", r1, "Fac")
    fw = _scale_fac(nt, r1, "Color", 0.4)
    mix1 = _mix(nt, "#424A52", "#33393F", fw, "Value")
    n3 = _noise(nt, 8.0, 2.0, 0.7)
    _link(nt, mp, "Vector", n3, "Vector")
    rough = _rough_map(nt, n3, 0.60, 0.80)
    n4 = _noise(nt, 10.0, 2.0, 0.6)
    _link(nt, mp, "Vector", n4, "Vector")
    bump = _bump(nt, n4, 0.10, 0.02)
    _finish(mat, mix1, rough, bump)

# ---------- 天花板纹理: 轻微噪波 ----------
# 2026-11-24 返工（验收 run #72：天花板顶面在预览里是大面积纯白平板）:
#   顶面即预览所见“屋顶”，与墙面同级纹理：噪波混合强度 0.25→0.6、第二色
#   加深到 #C6C6C6、Ramp 收窄、Bump 0.06→0.15，烘焙后顶面可见云纹。
def tex_ceiling(mat):
    nt = mat.node_tree
    tc, mp = _texcoord_mapped(nt, 4.0)
    n1 = _noise(nt, 4.0, 2.0, 0.7)
    _link(nt, mp, "Vector", n1, "Vector")
    r1 = _ramp(nt, [(0.30, 0.0), (0.60, 1.0)])
    _link(nt, n1, "Fac", r1, "Fac")
    fw = _scale_fac(nt, r1, "Color", 0.6)
    mix1 = _mix(nt, "#E8E8E8", "#C6C6C6", fw, "Value")
    n3 = _noise(nt, 8.0, 2.0, 0.7)
    _link(nt, mp, "Vector", n3, "Vector")
    rough = _rough_map(nt, n3, 0.85, 0.95)
    n4 = _noise(nt, 8.0, 2.0, 0.6)
    _link(nt, mp, "Vector", n4, "Vector")
    bump = _bump(nt, n4, 0.15, 0.02)
    _finish(mat, mix1, rough, bump)

FLOOR_MAT = make_material("Floor_Epoxy", "#B9B3A8", 0.9, 0.0)
WALL_MAT = make_material("Wall_Cream", "#F3E9D2", 0.85, 0.0)
SKIRT_MAT = make_material("Skirting_DarkGrey", "#424A52", 0.7, 0.0)
CEIL_MAT = make_material("Ceiling_White", "#E8E8E8", 0.9, 0.0)
YELLOW_MAT = make_material("Warning_Yellow", "#E8B400", 0.6, 0.0)

tex_floor(FLOOR_MAT)
tex_wall(WALL_MAT)
tex_skirt(SKIRT_MAT)
tex_ceiling(CEIL_MAT)
tex_yellow(YELLOW_MAT)

def add_box(name, dims, loc, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(mat)
    if bevel:
        bev = ob.modifiers.new("EdgeBevel", 'BEVEL')
        bev.width = bevel
        bev.segments = 2
        bev.limit_method = 'ANGLE'
    return ob

objs = []

# ---------- 地面: 16x10m, 厚 0.05m, 顶面 z=0 ----------
objs.append(add_box("Floor", (16.0, 10.0, 0.05), (0.0, 0.0, -0.025), FLOOR_MAT, bevel=0.02))

# ---------- 四面墙: 高 8m, 厚 0.2m ----------
# 北墙完整 (y=+5 外缘, 中心 y=4.9)
objs.append(add_box("Wall_North", (16.0, 0.2, 8.0), (0.0, 4.9, 4.0), WALL_MAT, bevel=0.02))
# 东墙 / 西墙 (夹在南北墙之间, 长 9.6m)
objs.append(add_box("Wall_East", (0.2, 9.6, 8.0), (7.9, 0.0, 4.0), WALL_MAT, bevel=0.02))
objs.append(add_box("Wall_West", (0.2, 9.6, 8.0), (-7.9, 0.0, 4.0), WALL_MAT, bevel=0.02))
# 南墙 (y=-5): 门洞 1.2 宽 x 2.4 高, x=0 处; 左右两段 + 上方门楣
# 左段 x -8~-0.6 (长 7.4, 中心 -4.3), 右段 x 0.6~8 (中心 4.3)
objs.append(add_box("Wall_South_Left", (7.4, 0.2, 8.0), (-4.3, -4.9, 4.0), WALL_MAT, bevel=0.02))
objs.append(add_box("Wall_South_Right", (7.4, 0.2, 8.0), (4.3, -4.9, 4.0), WALL_MAT, bevel=0.02))
# 门楣: x -0.6~0.6 (宽 1.2), z 2.4~8.0 (高 5.6, 中心 5.2)
objs.append(add_box("Wall_South_Lintel", (1.2, 0.2, 5.6), (0.0, -4.9, 5.2), WALL_MAT, bevel=0.02))

# ---------- 踢脚线: 高 0.15m, 深灰, 贴墙内面 (厚 0.02m), 门洞处断开 ----------
# 北墙内面 y=4.8 -> 条中心 y=4.79; 南墙内面 y=-4.8 -> y=-4.79; 东西墙内面 x=+-7.8 -> x=+-7.79
objs.append(add_box("Skirting_North", (15.6, 0.02, 0.15), (0.0, 4.79, 0.075), SKIRT_MAT))
objs.append(add_box("Skirting_South_Left", (7.2, 0.02, 0.15), (-4.2, -4.79, 0.075), SKIRT_MAT))
objs.append(add_box("Skirting_South_Right", (7.2, 0.02, 0.15), (4.2, -4.79, 0.075), SKIRT_MAT))
objs.append(add_box("Skirting_East", (0.02, 9.6, 0.15), (7.79, 0.0, 0.075), SKIRT_MAT))
objs.append(add_box("Skirting_West", (0.02, 9.6, 0.15), (-7.79, 0.0, 0.075), SKIRT_MAT))

# ---------- 天花板: 16x10m 白色平板, 底面 z=8.0, 厚 0.1m ----------
objs.append(add_box("Ceiling", (16.0, 10.0, 0.1), (0.0, 0.0, 8.05), CEIL_MAT, bevel=0.02))

# ---------- 黄色警戒线框: 沿变压器区外缘 0.3m, 线宽 0.1m, 厚 0.01m 贴地面 ----------
# 区外缘框 x -6.05~+6.05, y -0.55~+1.55; 南北条长 12.1m, 东西条长 1.9m (角部不错缝)
objs.append(add_box("Warning_Line_North", (12.1, 0.1, 0.01), (0.0, 1.50, 0.005), YELLOW_MAT))
objs.append(add_box("Warning_Line_South", (12.1, 0.1, 0.01), (0.0, -0.50, 0.005), YELLOW_MAT))
objs.append(add_box("Warning_Line_East", (0.1, 1.9, 0.01), (6.00, 0.5, 0.005), YELLOW_MAT))
objs.append(add_box("Warning_Line_West", (0.1, 1.9, 0.01), (-6.00, 0.5, 0.005), YELLOW_MAT))

print("di-walls objects:", len(objs), [o.name for o in objs])

# ---------- 烘焙程序化纹理为图片 (glTF 无法导出 Noise/Voronoi) ----------
# 流程: 每种材质选其全部对象 -> Cycles 烘焙 color/rough/normal 三张图
# (diffuse 只取 color 通道, 不带光照) -> 重建材质为图片纹理节点。
# 立方体自带 UV (每面 0~1), 噪波类纹理可直接烘焙, 无需重展 UV。
TEX_DIR = BASE + "/assets/blender/dist/di-walls_textures"
os.makedirs(TEX_DIR, exist_ok=True)
_bake_scene = bpy.context.scene

def _bake_images(mat, mat_objs, color_size):
    nt = mat.node_tree
    imgs = {}
    specs = [("color", 'DIFFUSE', color_size, 'sRGB'),
             ("rough", 'ROUGHNESS', 512, 'Non-Color'),
             ("normal", 'NORMAL', 512, 'Non-Color')]
    bpy.ops.object.select_all(action='DESELECT')
    for ob in mat_objs:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = mat_objs[0]
    _bake_scene.render.engine = 'CYCLES'
    _bake_scene.cycles.device = 'CPU'
    _bake_scene.cycles.samples = 4
    bake = _bake_scene.render.bake
    bake.use_selected_to_active = False
    bake.margin = 4
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
for _ob in objs:
    _by_mat.setdefault(_ob.data.materials[0], []).append(_ob)
_baked = {}
for _mat, _m_objs in _by_mat.items():
    _size = 1024 if _mat.name in ("Floor_Epoxy", "Wall_Cream") else 512
    _baked[_mat.name] = _bake_images(_mat, _m_objs, _size)
for _mat in _by_mat:
    _rebuild_with_images(_mat, _baked[_mat.name])
print("bake done, materials rebuilt with image textures")

# ---------- lighting (SPEC §2; 仅供 GH Actions 渲染用, 本地不渲染) ----------
# 太阳光: 能量 3.5, 从西南来, 仰角约 50°, 开阴影
sun_data = bpy.data.lights.new("Sun", type='SUN')
sun_data.energy = 3.5
sun_data.use_shadow = True
sun = bpy.data.objects.new("Sun", sun_data)
bpy.context.collection.objects.link(sun)
sun.location = (-20.0, -20.0, 30.0)
light_dir = Vector((math.cos(math.radians(50)) * math.cos(math.radians(45)),
                    math.cos(math.radians(50)) * math.sin(math.radians(45)),
                    -math.sin(math.radians(50))))
sun.rotation_mode = 'QUATERNION'
sun.rotation_quaternion = light_dir.to_track_quat('-Z', 'Y')

# 世界背景: 淡蓝 (0.65, 0.78, 0.88), 强度 1.0
world = bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.65, 0.78, 0.88, 1.0)
bg.inputs["Strength"].default_value = 1.0

# 室内预览补光 (仅预览, 不导出: 房间有天花板, 太阳光进不来)
for i, lx in enumerate((-4.0, 4.0)):
    ld = bpy.data.lights.new("Preview_Point_%d" % i, type='POINT')
    ld.energy = 500.0
    ld.shadow_soft_size = 0.5
    lo = bpy.data.objects.new("Preview_Point_%d" % i, ld)
    bpy.context.collection.objects.link(lo)
    lo.location = (lx, 0.0, 6.0)

# ---------- camera: 室内视角, 东北角高处看向南墙门洞 ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 24.0
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera = cam
cam.location = (6.2, 3.8, 5.0)
target = Vector((-2.0, -4.8, 1.0))
cam.rotation_mode = 'QUATERNION'
cam.rotation_quaternion = (target - cam.location).to_track_quat('-Z', 'Y')

# ---------- render settings (仅保留配置供 GH Actions 用, 本地不执行渲染) ----------
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.eevee.taa_render_samples = 16
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100

# ---------- save .blend ----------
os.makedirs(os.path.dirname(BLEND_PATH), exist_ok=True)
os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)

# ---------- export .glb (只选本件对象) ----------
bpy.ops.object.select_all(action='DESELECT')
for ob in objs:
    ob.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format='GLB',
                           use_selection=True, export_apply=True)

# ---------- 回读验证 glb ----------
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB_PATH)
imported = [ob for ob in bpy.data.objects if ob not in before]
print("GLB reimport objects:", len(imported),
      [ob.name for ob in imported])
for ob in imported:
    for slot in ob.material_slots:
        m = slot.material
        if m and m.use_nodes:
            imgs = [n.image.name for n in m.node_tree.nodes
                    if n.type == 'TEX_IMAGE' and n.image is not None]
            print("GLB reimport mat:", ob.name, m.name, "images:", imgs)
            assert len(imgs) >= 3, "glb material lost baked textures: %s" % m.name
assert len(imported) == len(objs), "glb reimport failed: expected %d objects, got %d" % (len(objs), len(imported))
# 删掉回读的副本, 恢复干净场景
bpy.ops.object.select_all(action='DESELECT')
for ob in imported:
    ob.select_set(True)
bpy.ops.object.delete()

bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("DONE di-walls")
