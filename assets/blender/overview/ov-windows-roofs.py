# ov-windows-roofs.py -- v2: A/B/C 三栋教学楼窗户与屋顶细部（返工）
# 归属：只做 A/B/C 的窗与屋顶件，不动楼体（ov-bldA/B/C 负责楼体量块）。
# 位置尺寸来源：旧版脚本 + ov-bldA/B/C.py 实测对齐——
#   A/B 顶层（5F）收分 0.3m/边，C 每层收分 0.1m/边，窗带按各层实际墙面落位
#   （旧版 5F/C 上层窗带按满幅外墙放，会悬空 0.3m，本版修正）；
#   女儿墙压顶：楼体件已有混凝土压顶（顶面 A/B z=19.0、C z=14.0），
#   本件金属盖板叠在其上（+0.12m），不重叠、不 z-fight。
# 窗做法（定型做法，后面 8 栋楼的窗玻璃照此复用）：
#   立体窗框：金属灰框体出墙 0.18m（上下框+侧框，0.12 宽）；
#   玻璃后退 0.1m（玻璃前表面墙+0.07，框前沿墙+0.18）；
#   竖中挺每 3m 一根 + 横中挺一道，均凸出玻璃面；
#   窗台板：出墙 0.24m、宽出窗带 0.12m/边。
# 玻璃材质：Principled（透光 0.55 + Noise 粗糙度变化 + 淡蓝灰）与
#   Glass BSDF 按 0.35 混合；Eevee 开 SSR + 折射，楼前放 Reflection
#   Cubemap + Irradiance Volume（GRID），玻璃反射须在渲染里看出来。
# 屋顶：女儿墙金属拉丝压顶盖板（独立盒）+ 防水层板（Noise+Voronoi）
#   + 设备盒（百叶+排气管）与风扇罩（圆筒+锥盖）。
# 坐标：Blender 米制，x 东 / y 北 / z 上；Godot (x,-z) 换算见 SPEC.md
import bpy
import bmesh
import math
import os
from mathutils import Matrix, Vector

BASE = os.path.expanduser(
    "~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
BLEND_PATH = os.path.join(BASE, "assets/blender/overview/ov-windows-roofs.blend")
GLB_PATH = os.path.join(BASE, "assets/models/ov-windows-roofs.glb")
PNG_PATH = os.path.join(BASE, "screenshots/blender/ov-windows-roofs.png")

# ---------- sRGB hex -> Principled 线性值 ----------
def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def hex_linear(h):
    h = h.lstrip("#")
    return tuple(srgb_to_linear(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4)) + (1.0,)

# ---------- 场景清理（必须在建材质之前，否则材质会被清掉） ----------
bpy.ops.wm.read_factory_settings(use_empty=True)

def _link(nt, out_node, out_sock, in_node, in_sock):
    nt.links.new(out_node.outputs[out_sock], in_node.inputs[in_sock])

def _noise_roughness(nt, bsdf, name, map_scale, noise_scale, lo, hi):
    """TexCoord -> Mapping -> Noise -> ColorRamp -> Roughness。返回 ramp。"""
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = map_scale
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = noise_scale
    nz.inputs["Detail"].default_value = 3.0
    nz.inputs["Roughness"].default_value = 0.7
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (lo, lo, lo, 1.0)
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = (hi, hi, hi, 1.0)
    _link(nt, tc, "Generated", mp, "Vector")
    _link(nt, mp, "Vector", nz, "Vector")
    _link(nt, nz, "Fac", ramp, "Fac")
    _link(nt, ramp, "Color", bsdf, "Roughness")
    return ramp, nz

def make_simple(name, hex_color, metallic, roughness):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = hex_linear(hex_color)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat

# ---------- 玻璃：Principled/Glass 混合（定型做法） ----------
def make_glass():
    mat = bpy.data.materials.new("ovw_glass")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    out = nt.nodes["Material Output"]
    bsdf.inputs["Base Color"].default_value = hex_linear("#9FC3D8")
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Transmission Weight"].default_value = 0.55
    bsdf.inputs["IOR"].default_value = 1.45
    bsdf.inputs["Specular IOR Level"].default_value = 1.0
    glass = nt.nodes.new("ShaderNodeBsdfGlass")
    glass.inputs["Color"].default_value = hex_linear("#9FC3D8")
    glass.inputs["IOR"].default_value = 1.45
    glass.distribution = "GGX"
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.inputs[0].default_value = 0.35  # 0.35 Glass + 0.65 Principled
    # Noise 粗糙度变化：同一条 ramp 同时驱动 Principled 与 Glass 的粗糙度
    ramp, _nz = _noise_roughness(nt, bsdf, "glass", (3.0, 3.0, 1.0), 6.0, 0.03, 0.16)
    _link(nt, ramp, "Color", glass, "Roughness")
    _link(nt, glass, "BSDF", mix, 1)
    _link(nt, bsdf, "BSDF", mix, 2)
    _link(nt, mix, "Shader", out, "Surface")
    return mat

# ---------- 窗框：金属灰，轻微 Noise 粗糙度变化 ----------
def make_frame():
    mat = bpy.data.materials.new("ovw_frame")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = hex_linear("#8A8F94")
    bsdf.inputs["Metallic"].default_value = 0.85
    _noise_roughness(nt, bsdf, "frame", (8.0, 8.0, 8.0), 5.0, 0.35, 0.55)
    return mat

# ---------- 女儿墙压顶盖板：拉丝金属（Noise 沿长度方向拉伸） ----------
def make_coping(map_scale):
    mat = bpy.data.materials.new("ovw_coping")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = hex_linear("#C0C5C9")
    bsdf.inputs["Metallic"].default_value = 0.95
    _noise_roughness(nt, bsdf, "coping", map_scale, 2.0, 0.22, 0.45)
    return mat

# ---------- 屋顶防水层：Noise 色差 + Voronoi 粗糙度 + 轻微 Bump ----------
def make_membrane():
    mat = bpy.data.materials.new("ovw_roof_membrane")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Metallic"].default_value = 0.0
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (5.0, 5.0, 5.0)
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 5.0
    nz.inputs["Detail"].default_value = 3.0
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].position = 0.0
    cr.color_ramp.elements[0].color = hex_linear("#3A4046")
    cr.color_ramp.elements[1].position = 1.0
    cr.color_ramp.elements[1].color = hex_linear("#4E565E")
    vo = nt.nodes.new("ShaderNodeTexVoronoi")
    vo.feature = "F1"
    vo.distance = "EUCLIDEAN"
    vo.inputs["Scale"].default_value = 14.0
    vr = nt.nodes.new("ShaderNodeValToRGB")
    vr.color_ramp.elements[0].position = 0.0
    vr.color_ramp.elements[0].color = (0.65, 0.65, 0.65, 1.0)
    vr.color_ramp.elements[1].position = 1.0
    vr.color_ramp.elements[1].color = (0.95, 0.95, 0.95, 1.0)
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.25
    bump.inputs["Distance"].default_value = 0.03
    _link(nt, tc, "Generated", mp, "Vector")
    _link(nt, mp, "Vector", nz, "Vector")
    _link(nt, mp, "Vector", vo, "Vector")
    _link(nt, nz, "Fac", cr, "Fac")
    _link(nt, cr, "Color", bsdf, "Base Color")
    _link(nt, vo, "Distance", vr, "Fac")
    _link(nt, vr, "Color", bsdf, "Roughness")
    _link(nt, nz, "Fac", bump, "Height")
    _link(nt, bump, "Normal", bsdf, "Normal")
    return mat

GLASS = make_glass()
FRAME = make_frame()
COPING_X = make_coping((30.0, 3.0, 3.0))   # 南北向盖板：拉丝沿 x
COPING_Y = make_coping((3.0, 30.0, 3.0))   # 东西向盖板：拉丝沿 y
MEMBRANE = make_membrane()
EQUIP = make_simple("ovw_equip", "#6B7076", 0.55, 0.5)
LOUVER = make_simple("ovw_louver", "#424A52", 0.3, 0.6)
FAN = make_simple("ovw_fan", "#8A8F94", 0.7, 0.4)

# ---------- 楼栋数据 ----------
# 每层：(层底 z, 层顶 z, 半长 hx, 半宽 hy)——按楼体件各层实际收分
# cap_z0：楼体件混凝土压顶顶面（本件金属盖板叠在其上）；slab：屋顶板尺寸/顶面
BUILDINGS = [
    {"name": "A", "cx": -56.0, "cy": 30.0,
     "floors": [(0.5, 4.5, 20.0, 7.5), (4.5, 7.9, 20.0, 7.5),
                (7.9, 11.3, 20.0, 7.5), (11.3, 14.7, 20.0, 7.5),
                (14.7, 18.1, 19.7, 7.2)],
     "cap_z0": 19.0, "parapet": (39.4, 14.4),
     "slab_top": 18.35, "slab": (39.0, 14.0),
     "equip": (-60.0, 33.5, 2.2, 1.6, 1.0), "fan": (-52.0, 26.5)},
    {"name": "B", "cx": -12.0, "cy": 30.0,
     "floors": [(0.5, 4.5, 16.0, 7.0), (4.5, 7.9, 16.0, 7.0),
                (7.9, 11.3, 16.0, 7.0), (11.3, 14.7, 16.0, 7.0),
                (14.7, 18.1, 15.7, 6.7)],
     "cap_z0": 19.0, "parapet": (31.4, 13.4),
     "slab_top": 18.35, "slab": (31.0, 13.0),
     "equip": (-14.0, 33.5, 2.0, 1.5, 0.9), "fan": (-24.0, 33.5)},
    {"name": "C", "cx": 26.0, "cy": 30.0,
     "floors": [(0.5, 4.0, 11.0, 6.5), (4.0, 7.0, 10.9, 6.4),
                (7.0, 10.0, 10.8, 6.3), (10.0, 13.0, 10.7, 6.2)],
     "cap_z0": 14.0, "parapet": (21.4, 12.4),
     "slab_top": 13.25, "slab": (21.4, 12.4),
     "equip": (26.0, 34.8, 1.8, 1.4, 0.8), "fan": (19.0, 27.5)},
]

def add_box(bm, center, size):
    r = bmesh.ops.create_cube(bm, size=1.0)
    mat = Matrix.Diagonal((size[0], size[1], size[2], 1.0))
    mat.translation = Vector(center)
    bmesh.ops.transform(bm, matrix=mat, verts=r["verts"])
    return r

def add_cyl(bm, center, radius1, radius2, depth, segments=24):
    r = bmesh.ops.create_cone(bm, cap_ends=True, segments=segments,
                              radius1=radius1, radius2=radius2, depth=depth)
    mat = Matrix.Translation(Vector(center))
    bmesh.ops.transform(bm, matrix=mat, verts=r["verts"])
    return r

def new_mesh_object(name, mat):
    me = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    if mat:
        me.materials.append(mat)
    return ob, me

piece_objs = []

# ---------- 窗：每面每层一个框体对象 + 一个玻璃对象 ----------
# 框出墙 0.18（墙面..+0.18），玻璃前表面墙+0.07（后退 0.11m），
# 中挺前沿 +0.15，窗台板出墙 0.24；两端离墙角各留 1.0m
for b in BUILDINGS:
    bname, cx, cy = b["name"], b["cx"], b["cy"]
    for fi, (z0, z1, hx, hy) in enumerate(b["floors"], start=1):
        band_h = 2.0 if fi == 1 else 1.6
        zc = (z0 + z1) / 2.0
        # faces: (名, 外法向 n, 沿带切向 t, 墙面偏移半距 off, 沿带半长 half)
        # S/N 面在 y=±hy 处、窗带沿 x 走、半长 hx；E/W 面在 x=±hx 处、
        # 窗带沿 y 走、半长 hy。旧版只用一个 half 兼作偏移与半长，
        # 把 hx/hy 用反：S/N 带只有 2*hy-2、E/W 带长达 2*hx-2 而悬空。
        faces = [
            ("S", Vector((0, -1, 0)), Vector((1, 0, 0)), hy, hx),
            ("N", Vector((0, 1, 0)), Vector((1, 0, 0)), hy, hx),
            ("E", Vector((1, 0, 0)), Vector((0, 1, 0)), hx, hy),
            ("W", Vector((-1, 0, 0)), Vector((0, 1, 0)), hx, hy),
        ]
        for fname, n, t, off, half in faces:
            base = Vector((cx, cy, 0.0)) + n * off
            band_len = 2.0 * half - 2.0

            def obox(bm, u, off, z, length, depth, height):
                c = base + t * u + n * off + Vector((0, 0, z))
                sx = abs(t.x) * length + abs(n.x) * depth
                sy = abs(t.y) * length + abs(n.y) * depth
                add_box(bm, (c.x, c.y, c.z), (sx, sy, height))

            # 框体：上下框 + 左右侧框 + 竖中挺（每 3m）+ 横中挺 + 窗台板
            bm = bmesh.new()
            obox(bm, 0, 0.09, zc + band_h / 2 + 0.06, band_len + 0.12, 0.18, 0.12)
            obox(bm, 0, 0.09, zc - band_h / 2 - 0.06, band_len + 0.12, 0.18, 0.12)
            obox(bm, -(band_len / 2 + 0.06), 0.09, zc, 0.12, 0.18, band_h)
            obox(bm, band_len / 2 + 0.06, 0.09, zc, 0.12, 0.18, band_h)
            k = 1
            while -band_len / 2 + 3.0 * k < band_len / 2 - 0.01:
                obox(bm, -band_len / 2 + 3.0 * k, 0.10, zc, 0.07, 0.10, band_h)
                k += 1
            obox(bm, 0, 0.10, zc, band_len, 0.10, 0.07)  # 横中挺
            obox(bm, 0, 0.11, zc - band_h / 2 - 0.16, band_len + 0.24, 0.26, 0.08)  # 窗台板
            fob, fme = new_mesh_object("ovw_frame_%s_F%d_%s" % (bname, fi, fname), FRAME)
            bm.to_mesh(fme)
            bm.free()
            piece_objs.append(fob)
            # 玻璃：单片，后退 0.1m
            bm = bmesh.new()
            obox(bm, 0, 0.05, zc, band_len, 0.04, band_h)
            gob, gme = new_mesh_object("ovw_glass_%s_F%d_%s" % (bname, fi, fname), GLASS)
            bm.to_mesh(gme)
            bm.free()
            piece_objs.append(gob)

print("window objects:", len(piece_objs))  # (5+5+4)*4*2 = 112

# ---------- 屋顶：金属压顶盖板 + 防水层板 + 设备盒 + 风扇罩 ----------
for b in BUILDINGS:
    bname, cx, cy = b["name"], b["cx"], b["cy"]
    pw, pd = b["parapet"]
    cz = b["cap_z0"]
    # 女儿墙压顶：独立金属盖板盒，叠在楼体件混凝土压顶顶面，宽 0.49（出墙 0.12/边）
    bm = bmesh.new()
    add_box(bm, (cx, cy - (pd / 2 - 0.245), cz + 0.06), (pw, 0.49, 0.12))
    add_box(bm, (cx, cy + (pd / 2 - 0.245), cz + 0.06), (pw, 0.49, 0.12))
    ob, me = new_mesh_object("ovw_coping_%s_NS" % bname, COPING_X)
    bm.to_mesh(me); bm.free(); piece_objs.append(ob)
    bm = bmesh.new()
    add_box(bm, (cx - (pw / 2 - 0.245), cy, cz + 0.06), (0.49, pd - 0.98, 0.12))
    add_box(bm, (cx + (pw / 2 - 0.245), cy, cz + 0.06), (0.49, pd - 0.98, 0.12))
    ob, me = new_mesh_object("ovw_coping_%s_EW" % bname, COPING_Y)
    bm.to_mesh(me); bm.free(); piece_objs.append(ob)
    # 防水层板：铺在屋顶板顶面，0.05 厚
    sw, sd = b["slab"]
    st = b["slab_top"]
    bm = bmesh.new()
    add_box(bm, (cx, cy, st + 0.025), (sw, sd, 0.05))
    ob, me = new_mesh_object("ovw_roofdeck_%s" % bname, MEMBRANE)
    bm.to_mesh(me); bm.free(); piece_objs.append(ob)
    # 设备盒：箱体 + 顶盖 + 南面百叶 4 片 + 顶部排气管
    ex, ey, ew, ed, eh = b["equip"]
    z0 = st + 0.05
    bm = bmesh.new()
    add_box(bm, (ex, ey, z0 + eh / 2), (ew, ed, eh))
    add_box(bm, (ex, ey, z0 + eh + 0.04), (ew + 0.2, ed + 0.2, 0.08))
    for i in range(4):
        lz = z0 + 0.25 + i * 0.22
        if lz > z0 + eh - 0.15:
            break
        add_box(bm, (ex, ey - ed / 2 - 0.02, lz), (ew * 0.8, 0.06, 0.09))
    add_cyl(bm, (ex + ew / 4, ey, z0 + eh + 0.08 + 0.25), 0.09, 0.09, 0.5, 16)
    ob, me = new_mesh_object("ovw_equip_%s" % bname, EQUIP)
    bm.to_mesh(me); bm.free(); piece_objs.append(ob)
    # 风扇罩：底座 + 圆筒 + 锥形风帽
    fx, fy = b["fan"]
    bm = bmesh.new()
    add_box(bm, (fx, fy, z0 + 0.125), (1.5, 1.5, 0.25))
    add_cyl(bm, (fx, fy, z0 + 0.25 + 0.425), 0.65, 0.65, 0.85, 24)
    add_cyl(bm, (fx, fy, z0 + 1.10 + 0.175), 0.85, 0.12, 0.35, 24)
    ob, me = new_mesh_object("ovw_fan_%s" % bname, FAN)
    bm.to_mesh(me); bm.free(); piece_objs.append(ob)

print("piece objects total:", len(piece_objs))  # 112 窗 + 15 屋顶 = 127

# ---------- 示意楼体量块（仅预览衬底，不导出）：只做 A 栋 ----------
WALL_COLORS = {"A": "#F3E9D2"}
ROOF = make_simple("ovw_preview_roof", "#424A52", 0.1, 0.8)
CONC = make_simple("ovw_preview_conc", "#B9B3A8", 0.0, 0.95)
cx, cy = -56.0, 30.0
wall_mat = make_simple("ovw_preview_wall_A", WALL_COLORS["A"], 0.0, 0.9)
def preview_box(name, cx_, cy_, z0, z1, sx, sy, mat):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(cx_, cy_, (z0 + z1) / 2.0))
    o = bpy.context.active_object
    o.name = name
    o.dimensions = (sx, sy, z1 - z0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    return o

preview_box("PREVIEW_mass_A_plinth", cx, cy, 0.0, 0.5, 40.6, 15.6, CONC)
preview_box("PREVIEW_mass_A_F1F4", cx, cy, 0.5, 14.7, 40.0, 15.0, wall_mat)
preview_box("PREVIEW_mass_A_F5", cx, cy, 14.7, 18.1, 39.4, 14.4, wall_mat)
preview_box("PREVIEW_roof_A", cx, cy, 18.1, 18.35, 39.0, 14.0, ROOF)
# 女儿墙 + 混凝土压顶（本件金属盖板叠在其上）
preview_box("PREVIEW_parapet_A_S", cx, cy - 7.075, 18.1, 18.92, 39.4, 0.25, wall_mat)
preview_box("PREVIEW_parapet_A_N", cx, cy + 7.075, 18.1, 18.92, 39.4, 0.25, wall_mat)
preview_box("PREVIEW_parapet_A_W", cx - 19.575, cy, 18.1, 18.92, 0.25, 13.9, wall_mat)
preview_box("PREVIEW_parapet_A_E", cx + 19.575, cy, 18.1, 18.92, 0.25, 13.9, wall_mat)
preview_box("PREVIEW_parapetcap_A_S", cx, cy - 7.075, 18.92, 19.0, 39.4, 0.37, CONC)
preview_box("PREVIEW_parapetcap_A_N", cx, cy + 7.075, 18.92, 19.0, 39.4, 0.37, CONC)
preview_box("PREVIEW_parapetcap_A_W", cx - 19.575, cy, 18.92, 19.0, 0.37, 13.9, CONC)
preview_box("PREVIEW_parapetcap_A_E", cx + 19.575, cy, 18.92, 19.0, 0.37, 13.9, CONC)

ground_mat = make_simple("ovw_preview_ground", "#B9B3A8", 0.0, 0.95)
preview_box("PREVIEW_ground", -56.0, 30.0, -0.2, 0.0, 120.0, 80.0, ground_mat)

# ---------- 光照（SPEC §2）：太阳 3.5 从西南来、仰角约 50°；世界淡蓝 ----------
sun_data = bpy.data.lights.new("ovw_sun", type="SUN")
sun_data.energy = 3.5
sun_data.use_shadow = True
sun = bpy.data.objects.new("ovw_sun", sun_data)
bpy.context.collection.objects.link(sun)
light_dir = Vector((math.cos(math.radians(50)) * math.cos(math.radians(45)),
                    math.cos(math.radians(50)) * math.sin(math.radians(45)),
                    -math.sin(math.radians(50)))).normalized()
sun.rotation_mode = "QUATERNION"
sun.rotation_quaternion = Vector((0, 0, -1)).rotation_difference(light_dir)

world = bpy.data.worlds.new("ovw_world")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.65, 0.78, 0.88, 1.0)
bg.inputs["Strength"].default_value = 1.0

# ---------- 反射探针：楼前 Reflection Cubemap + Irradiance Volume ----------
try:
    bpy.ops.object.lightprobe_add(type="SPHERE", location=(-56.0, 8.0, 9.0))
    cube = bpy.context.active_object
    cube.name = "ovw_probe_cubemap"
    cube.data.clip_start = 0.5
    cube.data.clip_end = 100.0
    cube.data.influence_distance = 45.0
    try:
        cube.data.resolution = 128
    except Exception:
        pass
    print("cubemap probe ok")
except Exception as e:
    print("cubemap probe failed:", e)
try:
    bpy.ops.object.lightprobe_add(type="VOLUME", location=(-56.0, 12.0, 9.0))
    grid = bpy.context.active_object
    grid.name = "ovw_probe_irradiance"
    try:
        # 影响距离 10m：4.27M surfels / 912MB 显存需求的根源就是影响盒太大；
        # 35m 时 IrradianceBake 直接报显存不足（912/30MB），10m 时约 10 万 surfels / 约 21MB
        grid.data.influence_distance = 10.0
    except Exception:
        pass
    # Irradiance Volume 用 1x1x1：单探针即可覆盖南立面均匀辐照；
    # 2x2x2 时 48 次捕获在共享单元上烘焙/渲染都跑不完（实测 OOM），1 探针仍是有效体积探针
    for attr, val in (("resolution_x", 1), ("resolution_y", 1), ("resolution_z", 1)):
        try:
            setattr(grid.data, attr, val)
        except Exception:
            pass
    print("irradiance probe ok")
except Exception as e:
    print("irradiance probe failed:", e)

# ---------- 预览相机：45° 俯视，正南看 A 栋（只拍一栋） ----------
# 相机 (-56,-14,53.5) -> 目标 (-56,30,9.5)：水平距 44m、高差 44m = 45°；
# 50mm 镜头，640x360 下水平视野约 44.7m：A 栋 40m 完整入镜，
# B 栋西缘 x=-28 在画面右缘（约 -33.6）之外 5m+，不会切进第二栋楼。
cam_data = bpy.data.cameras.new("ovw_cam")
cam_data.lens = 50
cam = bpy.data.objects.new("ovw_cam", cam_data)
bpy.context.collection.objects.link(cam)
cam.location = (-56.0, -14.0, 53.5)
target = Vector((-56.0, 30.0, 9.5))
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
bpy.context.scene.camera = cam

# ---------- 渲染设置：Eevee + SSR + 折射 ----------
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.eevee.taa_render_samples = 16
try:
    scene.eevee.use_ssr = True
    scene.eevee.use_ssr_refraction = True
    scene.eevee.use_ssr_halfres = True  # 半分辨率 SSR，省内存（共享单元常年满载）
    print("SSR on:", scene.eevee.use_ssr, "refraction:", scene.eevee.use_ssr_refraction)
except Exception as e:
    print("SSR setting failed:", e)
scene.render.filepath = PNG_PATH

# ---------- 烘焙程序化纹理为图片 (glTF 无法导出 Noise/Voronoi) ----------
# 照抄 dist/di-walls.py 已验证做法: 每种不透明材质选其全部对象 ->
# Cycles CPU 烘焙 color/rough/normal 三张 1024px 图 (margin 16px) ->
# 重建材质为图片纹理节点。玻璃材质不烘焙, 保持原样。
# 立方体自带 UV, 无需重展。烘焙图在 ov-windows-roofs_textures/。
# 金属注意 (di-walls 全是非金属, 没这个问题): Principled 的 diffuse
# lobe 按 (1-metallic) 缩放, 直接烘 DIFFUSE 会把金属底色烘暗
# (实测 MetalGrey metallic 0.3 烘出来线性值正好是 0.7 倍)。
# 所以 color 烘焙时先把 Metallic 临时置 0 (只影响 diffuse 通道,
# rough/normal 与 metallic 无关), 烘完恢复; 重建材质时把原 metallic
# 常数写回 Principled, glTF 照常导出 metallicFactor。
TEX_DIR = os.path.join(BASE, "assets/blender/overview/ov-windows-roofs_textures")


def _ensure_uv(ob):
    """bmesh 手建网格没有 UV 层, 烘焙前用 Smart UV Project 补一层。
    立方体/圆柱自带 UV 的直接跳过。只加 UV 层, 不动几何。"""
    me = ob.data
    if getattr(me, "uv_layers", None) and len(me.uv_layers) > 0:
        return
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=1.152, island_margin=0.02)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    print("uv added:", ob.name)


def _bake_images(mat, mat_objs, piece_objs):
    nt = mat.node_tree
    imgs = {}
    specs = [("color", 'DIFFUSE', 1024, 'sRGB'),
             ("rough", 'ROUGHNESS', 1024, 'Non-Color'),
             ("normal", 'NORMAL', 1024, 'Non-Color')]
    bsdf = nt.nodes.get("Principled BSDF")
    _metal_in = bsdf.inputs["Metallic"] if bsdf is not None else None
    _metal_linked = bool(_metal_in is not None and _metal_in.is_linked)
    _metal_val = _metal_in.default_value if (_metal_in is not None and not _metal_linked) else 0.0
    # 烘焙只关心本材质的对象: 把其余件对象 hide_render, Cycles 同步就跳过
    # 它们 (每 bake 少同步 ~200 个带倒角修饰器的对象, 实测不隐藏时单张
    # 烘焙要数分钟), 烘焙完恢复可见。
    _hidden = [ob for ob in piece_objs if ob not in mat_objs]
    for ob in _hidden:
        ob.hide_render = True
    bpy.ops.object.select_all(action='DESELECT')
    for ob in mat_objs:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = mat_objs[0]
    _bake_scene = bpy.context.scene
    _bake_scene.render.engine = 'CYCLES'
    _bake_scene.cycles.device = 'CPU'
    _bake_scene.cycles.samples = 4
    bake = _bake_scene.render.bake
    bake.use_selected_to_active = False
    bake.margin = 16
    for key, btype, size, cs in specs:
        # 断点续烘: 图已存在且能正常读入就复用 (照抄 B 组 ov-gym.py 做法, +1024 尺寸核对);
        # 读入失败/文件过小/尺寸不对则重新烘焙, 不硬复用错图。
        _fpath = os.path.join(TEX_DIR, "%s_%s.png" % (mat.name, key))
        if os.path.exists(_fpath) and os.path.getsize(_fpath) > 1000:
            try:
                _img = bpy.data.images.load(_fpath)
                if _img.size[0] != 1024 or _img.size[1] != 1024:
                    raise ValueError("wrong size %s, expect 1024x1024" % (_img.size,))
                _img.colorspace_settings.name = cs
                imgs[key] = _img
                print("reuse:", mat.name, key, _fpath,
                      os.path.getsize(_fpath))
                continue
            except Exception as _e:
                print("reload failed, re-bake:", mat.name, key, _e)
                try:
                    if '_img' in locals() and _img is not None and _img.name in bpy.data.images:
                        bpy.data.images.remove(_img)
                except Exception:
                    pass
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
            if _metal_in is not None and not _metal_linked:
                _metal_in.default_value = 0.0
        elif btype == 'NORMAL':
            bake.normal_space = 'TANGENT'
        bpy.ops.object.bake(type=btype)
        if btype == 'DIFFUSE' and _metal_in is not None and not _metal_linked:
            _metal_in.default_value = _metal_val
        img.filepath_raw = os.path.join(TEX_DIR, "%s_%s.png" % (mat.name, key))
        img.file_format = 'PNG'
        img.save()
        imgs[key] = img
        nt.nodes.remove(tex)
        print("baked:", mat.name, key, img.filepath_raw,
              os.path.getsize(img.filepath_raw))
    _bake_scene.render.engine = 'BLENDER_EEVEE_NEXT'
    for ob in _hidden:
        ob.hide_render = False
    return imgs


def _rebuild_with_images(mat, imgs, metallic=0.0):
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    bsdf.inputs["Roughness"].default_value = 1.0
    bsdf.inputs["Metallic"].default_value = metallic
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


def bake_piece(piece_objs):
    import time as _time
    _t0 = _time.time()
    os.makedirs(TEX_DIR, exist_ok=True)
    _by_mat = {}
    for _ob in piece_objs:
        if not _ob.data or not _ob.data.materials:
            continue
        _m = _ob.data.materials[0]
        if _m is None:
            continue
        if "glass" in _m.name.lower():
            print("bake skip (glass, kept as-is):", _m.name)
            continue
        _by_mat.setdefault(_m, []).append(_ob)
    for _m_objs in _by_mat.values():
        for _ob in _m_objs:
            _ensure_uv(_ob)
    _baked = {}
    _metallic = {}
    for _mat in _by_mat:
        _bsdf = _mat.node_tree.nodes.get("Principled BSDF")
        _mi = _bsdf.inputs["Metallic"] if _bsdf is not None else None
        _metallic[_mat.name] = _mi.default_value if (_mi is not None and not _mi.is_linked) else 0.0
    for _mat, _m_objs in _by_mat.items():
        _baked[_mat.name] = _bake_images(_mat, _m_objs, piece_objs)
    for _mat in _by_mat:
        _rebuild_with_images(_mat, _baked[_mat.name], _metallic[_mat.name])
    print("bake done, materials rebuilt with image textures, mats:",
          sorted(_baked.keys()), "elapsed: %.1fs" % (_time.time() - _t0))


def _check_glb_images(imported):
    for ob in imported:
        for slot in ob.material_slots:
            m = slot.material
            if m is None or not m.use_nodes:
                continue
            imgs = [n.image.name for n in m.node_tree.nodes
                    if n.type == 'TEX_IMAGE' and n.image is not None]
            print("GLB reimport mat:", ob.name, m.name, "images:", imgs)
            if "glass" in m.name.lower():
                continue
            assert len(imgs) >= 3, "glb material lost baked textures: %s" % m.name


# ---------- 烘焙程序化纹理 (存盘/导出之前) ----------
bake_piece(piece_objs)

# ---------- 存 .blend ----------
os.makedirs(os.path.dirname(BLEND_PATH), exist_ok=True)
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

# R2-T9b pack fix (2026-11-25): pack images into the .blend so Actions
# renders do not depend on external files (same fix as R2-T21a tower,
# commit 77c73269: relative //../../external/... paths rendered pink in
# run #99 when the texture files were not yet in the repo).
for _im in list(bpy.data.images):
    if _im.name in ("Render Result", "Viewer Node"):
        continue
    if _im.packed_file is None:
        try:
            _im.pack()
            print("packed image:", _im.name, _im.size[:])
        except Exception as e:
            print("pack image skip:", _im.name, e)

bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)

# ---------- 导出 .glb（只选本件对象） ----------
bpy.ops.object.select_all(action="DESELECT")
for ob in piece_objs:
    ob.select_set(True)
bpy.context.view_layer.objects.active = piece_objs[0]
os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format="GLB",
                           use_selection=True, export_apply=True)

# ---------- 回读校验 ----------
bpy.ops.object.select_all(action="DESELECT")
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB_PATH)
imported = [ob for ob in bpy.data.objects if ob not in before]
print("gltf reimport objects:", len(imported))
_check_glb_images(imported)
for ob in imported:
    bpy.data.objects.remove(ob, do_unlink=True)

# ---------- 渲染预览 (本地不渲染, 走 GitHub Actions;
# 显式设 OV_RENDER_PREVIEW=1 才在本地渲染) ----------
if os.environ.get("OV_RENDER_PREVIEW") == "1":
    bpy.ops.render.render(write_still=True)

print("DONE ov-windows-roofs")
