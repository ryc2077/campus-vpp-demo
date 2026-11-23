# ov-flag-lamp v2: 旗杆路灯（总览件）——返工版
# Blender 坐标 x 向东、y 向北、z 向上，单位米
# 返工目标（对照旧版筛查）：
#   ① 3 根旗杆各挂一面旗，旗面波浪几何 + 噪波位移（不再是平板），国旗红 + 五星贴色块
#   ② 路灯沿环路成排补齐，间距 25m，每盏带基座 + 灯杆 + 灯头（灯罩 + 灯珠）
#   ③ 金属拉丝纹理：旗杆不锈钢、灯杆深灰金属（拉丝噪波走 Bump，粗糙度分档）
#   ④ 旗杆基座：混凝土双层台座，带骨料纹理
#   ⑤ 结构件全部倒角，不留全平面
# 位置依据：SPEC §6 + 鸟瞰图 + ov-road-main 道路数据
#   旗杆：南门广场北侧 (0, -88)，南门 Godot [0,98] -> Blender (0,-98)，旗杆在其北 10m
#   路灯：南主路北缘 y=-101.4（路 y -114..-102，杆在路缘外，横臂向南伸向路面）
#         东主路西缘 x=101.4（路 x 102..114，横臂向东伸向路面）
#         环路北段外缘 y=84.9 / 南段外缘 y=-84.9 / 西段外缘 x=-99.9（横臂向内伸向路面）
#         环路东段与东主路仅隔 3m，不再重复布灯
# 不做铺装（ov-road-walk）、不做主干道路面（ov-road-main）
# 新规矩：渲染全部走 GitHub Actions，本脚本不渲染、不出预览图
import bpy
import math
import os

ROOT = os.path.expanduser(
    "~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
BLEND_PATH = os.path.join(ROOT, "assets/blender/overview/ov-flag-lamp.blend")
GLB_PATH = os.path.join(ROOT, "assets/models/ov-flag-lamp.glb")


def srgb_to_linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_to_linear(h):
    h = h.lstrip("#")
    return tuple(srgb_to_linear(int(h[i:i + 2], 16)) for i in (0, 2, 4))


def _bump(nt, bsdf, tex, strength, distance):
    """纹理只走 Bump（法线）：baseColor 保持默认值，glTF 导出不丢色（见 ov-road-main 教训）。"""
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = strength
    bump.inputs["Distance"].default_value = distance
    nt.links.new(tex, bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])


def make_brushed_metal(name, hex_color, roughness, metallic):
    """拉丝金属：Mapping 拉伸噪波 -> 竖向拉丝纹理进 Bump，粗糙度用默认值分档。"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*hex_to_linear(hex_color), 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    texcoord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (10.0, 10.0, 0.6)
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.0
    noise.inputs["Detail"].default_value = 2.0
    noise.inputs["Roughness"].default_value = 0.7
    nt.links.new(texcoord.outputs["Object"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    _bump(nt, bsdf, noise.outputs["Fac"], 0.15, 0.02)
    return m


def make_concrete(name, hex_color, roughness=0.95):
    """混凝土：细骨料噪波 + 小 Voronoi 麻点进 Bump。"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*hex_to_linear(hex_color), 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    texcoord = nt.nodes.new("ShaderNodeTexCoord")

    def _noise(scale, detail=2.0):
        n = nt.nodes.new("ShaderNodeTexNoise")
        n.inputs["Scale"].default_value = scale
        n.inputs["Detail"].default_value = detail
        n.inputs["Roughness"].default_value = 0.7
        nt.links.new(texcoord.outputs["Object"], n.inputs["Vector"])
        return n

    def _voronoi(scale):
        v = nt.nodes.new("ShaderNodeTexVoronoi")
        v.feature = "F1"
        v.inputs["Scale"].default_value = scale
        nt.links.new(texcoord.outputs["Object"], v.inputs["Vector"])
        return v

    def _sock(x):
        return x.outputs[0] if isinstance(x, bpy.types.Node) else x

    def _math(op, a, b=None, clamp=False):
        node = nt.nodes.new("ShaderNodeMath")
        node.operation = op
        if isinstance(a, float):
            node.inputs[0].default_value = a
        else:
            nt.links.new(_sock(a), node.inputs[0])
        if b is not None:
            if isinstance(b, float):
                node.inputs[1].default_value = b
            else:
                nt.links.new(_sock(b), node.inputs[1])
        node.use_clamp = clamp
        return node

    agg = _noise(1.5).outputs["Fac"]
    speck = _voronoi(5.0).outputs["Distance"]
    blotch = _noise(0.6).outputs["Fac"]
    h = _math("ADD",
              _math("MULTIPLY", _math("ADD", agg, speck), 0.35),
              _math("MULTIPLY", blotch, 0.3), clamp=True)
    _bump(nt, bsdf, h.outputs[0], 0.2, 0.03)
    return m


def make_mat(name, hex_color, roughness=0.9, metallic=0.0,
             emission_hex=None, emission_strength=0.0, fabric=False):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*hex_to_linear(hex_color), 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if emission_hex is not None:
        bsdf.inputs["Emission Color"].default_value = (*hex_to_linear(emission_hex), 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    if fabric:
        # 旗面织物：细噪波起伏进 Bump，配合几何波浪
        texcoord = nt.nodes.new("ShaderNodeTexCoord")
        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 8.0
        noise.inputs["Detail"].default_value = 2.0
        nt.links.new(texcoord.outputs["Object"], noise.inputs["Vector"])
        _bump(nt, bsdf, noise.outputs["Fac"], 0.08, 0.01)
    return m


def bevel(obj, width, segments=1):
    mod = obj.modifiers.new("EdgeSoft", "BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"
    return mod


# ---- PBR 贴图挂接（返工）：下载的 CC0 实拍贴图经亮度映射到 SPEC 色
# （assets/external/* -> *_textures/ 衍生 PNG，见 gen_textures.py），
# 无对应下载的用程序化合成贴图补位；程序化 Noise 节点不进 glTF，
# 必须换成图片纹理节点，否则 Godot 里只剩纯色 baseColorFactor。
# UV 按米缩放：1 次贴图重复 = tile 米（盒体默认 UV 每面 0~1，
# 不缩放时 12m 的梁会把整张砖纹拉满 12m）。逐面最小二乘拟合
# UV->3D，不依赖 UV 朝向；共享网格只算一次。
import numpy as _np
TEX_DIR = os.path.join(ROOT, "assets", "blender", "overview",
                       "ov-flag-lamp_textures")


def _load_img(path, colorspace):
    img = bpy.data.images.load(path)
    img.colorspace_settings.name = colorspace
    return img


def _apply_pbr(mat, set_name):
    """把材质精简为 Principled+Output，挂 color/rough/normal 三张图。
    rough 图存的是绝对粗糙度，挂上后 Roughness 系数置 1.0；
    Metallic 保持原标量（下载包无 metalness 图）。缺图时保持原标量。"""
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


def box(name, center, size, mat, bev=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    o = bpy.context.active_object
    o.name = name
    o.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bev:
        bevel(o, bev)
    o.data.materials.append(mat)
    return o


def cylinder(name, center, radius, depth, mat, rotation=(0, 0, 0),
             vertices=16, bev=0.0, radius_top=None):
    if radius_top is not None:
        bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius,
                                        radius2=radius_top, depth=depth,
                                        location=center, rotation=rotation)
    else:
        bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
                                            depth=depth, location=center,
                                            rotation=rotation)
    o = bpy.context.active_object
    o.name = name
    if bev:
        bevel(o, bev)
    o.data.materials.append(mat)
    return o


def sphere(name, center, r, mat, scale=(1.0, 1.0, 1.0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8,
                                         radius=r, location=center)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    return o


# ---- 清空场景 ----
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for m in list(bpy.data.materials):
    bpy.data.materials.remove(m)

# 材质：旗杆不锈钢拉丝（亮）、灯杆深灰金属拉丝（哑）、混凝土台座、旗红织物、星黄、灯罩、灯珠
mat_pole = make_brushed_metal("FlagPole_Steel_Brushed", "#C0C5C9", 0.30, 0.9)
mat_stone = make_concrete("FlagBase_Concrete", "#B9B3A8")
mat_flag = make_mat("Flag_Red", "#C0392B", roughness=0.7, fabric=True)
mat_star = make_mat("FlagStar_Yellow", "#F7D117", roughness=0.6)
mat_lamp_pole = make_brushed_metal("LampPole_DarkGrey_Brushed", "#424A52", 0.55, 0.6)
mat_lamp_head = make_brushed_metal("LampHead_DarkGrey_Brushed", "#3A4046", 0.5, 0.5)
mat_light = make_mat("Lamp_WarmWhite", "#FFE9C0", roughness=0.4,
                     emission_hex="#FFE9C0", emission_strength=1.5)

# PBR 挂图（返工）：混凝土/不锈钢/旗红/深灰金属挂图片纹理；
# 五星与灯珠太小，保持纯色 + 自发光，不挂图。
_apply_pbr(mat_stone, "Concrete")
_apply_pbr(mat_pole, "SteelBrushed")
_apply_pbr(mat_flag, "FlagRed")
_apply_pbr(mat_lamp_pole, "DarkMetal")
_apply_pbr(mat_lamp_head, "DarkMetal")
# 贴图 UV 按米缩放：{材质: 一重复多少米}
UV_TILE = {mat_stone: 2.0, mat_pole: 1.0, mat_flag: 1.0,
           mat_lamp_pole: 1.0, mat_lamp_head: 1.0}

objs = []

# ================= 旗杆：南门广场北侧 (0, -88)，间距 2.5m；主杆 12m、两侧 10m =================
FLAG_Y = -88.0
flag_x = [-2.5, 0.0, 2.5]
flag_h = [10.0, 12.0, 10.0]
flag_size = [(1.44, 0.96), (1.92, 1.28), (1.44, 0.96)]  # 宽 x 高：主杆 3 号旗，两侧 4 号旗


def flag_wave(x, zr, fw, fhgt):
    """旗面波浪：主波（自由端波幅大）+ 横向涟漪 + 细噪波（正弦组合，确定性）。"""
    u = x / fw
    v = zr / fhgt
    y = 0.10 * math.sin(math.pi * u) * (0.4 + 0.6 * u)
    y += 0.045 * math.sin(2 * math.pi * u * 1.6 + 0.9) * math.sin(math.pi * v) * (0.3 + 0.7 * u)
    y += 0.02 * math.sin(2 * math.pi * (u * 2.3 + v * 0.7) + 1.7) * u
    return y


def make_star(name, cx, cy, cz, r_outer, rot_z, mat):
    """五角星贴色块：10 点星形 + 中心扇形面，薄片，贴在旗面波浪上。"""
    r_in = r_outer * 0.382
    verts = [(cx, cy, cz)]
    for k in range(10):
        ang = rot_z + math.pi / 2 + k * math.pi / 5
        r = r_outer if k % 2 == 0 else r_in
        verts.append((cx + r * math.cos(ang), cy, cz + r * math.sin(ang)))
    faces = [(0, 1 + k, 1 + (k + 1) % 10) for k in range(10)]
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    o = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(mat)
    sol = o.modifiers.new("Solidify", "SOLIDIFY")
    sol.thickness = 0.004
    return o


for i, (fx, fh, (fw, fhgt)) in enumerate(zip(flag_x, flag_h, flag_size)):
    # 混凝土双层台座：下层 1.2x1.2x0.25 + 上层 0.8x0.8x0.5，均倒角
    base1 = box(f"FlagBase_{i}_Slab", (fx, FLAG_Y, 0.125), (1.2, 1.2, 0.25),
                mat_stone, bev=0.04)
    objs.append(base1)
    base2 = box(f"FlagBase_{i}_Pedestal", (fx, FLAG_Y, 0.50), (0.8, 0.8, 0.5),
                mat_stone, bev=0.04)
    objs.append(base2)
    # 不锈钢锥形杆（下粗上细）+ 顶部金球 + 杆底套环
    pole = cylinder(f"FlagPole_{i}", (fx, FLAG_Y, 0.75 + fh / 2.0), 0.09, fh,
                    mat_pole, vertices=20, bev=0.015, radius_top=0.055)
    objs.append(pole)
    collar = cylinder(f"FlagPole_Collar_{i}", (fx, FLAG_Y, 0.85), 0.11, 0.18,
                      mat_pole, vertices=20, bev=0.015)
    objs.append(collar)
    finial = sphere(f"FlagPole_Top_{i}", (fx, FLAG_Y, 0.75 + fh + 0.10), 0.12,
                    mat_pole)
    objs.append(finial)

    # 旗面：25x13 网格波浪几何，旗杆侧贴杆、向东展开
    z_top = 0.75 + fh
    z0 = z_top - fhgt
    nx, ny = 25, 13
    verts = []
    for j in range(ny):
        for k in range(nx):
            x = fw * k / (nx - 1)
            zr = fhgt * j / (ny - 1)
            y = FLAG_Y + flag_wave(x, zr, fw, fhgt)
            verts.append((fx + x, y, z0 + zr))
    faces = []
    for j in range(ny - 1):
        for k in range(nx - 1):
            a = j * nx + k
            faces.append((a, a + 1, a + nx + 1, a + nx))
    mesh = bpy.data.meshes.new(f"Flag_{i}_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    flag_obj = bpy.data.objects.new(f"Flag_{i}", mesh)
    bpy.context.collection.objects.link(flag_obj)
    flag_obj.data.materials.append(mat_flag)
    sol = flag_obj.modifiers.new("Solidify", "SOLIDIFY")
    sol.thickness = 0.008
    objs.append(flag_obj)

    # 五星贴色块：大星 + 四小星弧形环绕，沿旗面波浪贴放
    big_r = fw * 0.068
    small_r = fw * 0.026
    bx, bz = fw * 0.18, z0 + fhgt * 0.72
    by = FLAG_Y + flag_wave(bx, bz - z0, fw, fhgt) + 0.015
    objs.append(make_star(f"FlagStar_{i}_Big", fx + bx, by, bz, big_r, 0.0, mat_star))
    for s, (dx, dz) in enumerate([(0.24, 0.10), (0.30, -0.02), (0.24, -0.14), (0.10, -0.16)]):
        sx = fw * (0.18 + dx * fw / 1.92)
        sz = bz + dz * fw / 1.92
        sy = FLAG_Y + flag_wave(sx, sz - z0, fw, fhgt) + 0.015
        # 小星尖角朝向大星
        rot = math.atan2(bz - sz, bx - sx) - math.pi / 2
        objs.append(make_star(f"FlagStar_{i}_S{s}", fx + sx, sy, sz, small_r, rot, mat_star))

# ================= 路灯：间距 25m，基座 + 灯杆 + 灯头（灯罩 + 灯珠） =================
def make_lamp(idx, px, py, arm_dir):
    ax, ay = arm_dir
    # 混凝土方形基座（倒角）+ 金属套环
    base = box(f"LampBase_{idx:02d}", (px, py, 0.175), (0.42, 0.42, 0.35),
               mat_stone, bev=0.03)
    objs.append(base)
    collar = cylinder(f"LampCollar_{idx:02d}", (px, py, 0.45), 0.10, 0.20,
                      mat_lamp_pole, vertices=16, bev=0.015)
    objs.append(collar)
    # 灯杆：锥形深灰金属，高 6m（0.35..6.35），顶盖小球
    pole = cylinder(f"LampPole_{idx:02d}", (px, py, 3.35), 0.075, 6.0,
                    mat_lamp_pole, vertices=16, bev=0.015, radius_top=0.05)
    objs.append(pole)
    cap = sphere(f"LampCap_{idx:02d}", (px, py, 6.38), 0.07, mat_lamp_pole)
    objs.append(cap)
    # 横臂：长 1.5m，水平伸向路面；末端竖管下接灯头
    hx, hy = px + ax * 0.75, py + ay * 0.75
    if ax != 0:
        arm = cylinder(f"LampArm_{idx:02d}", (hx, hy, 6.30), 0.045, 1.5,
                       mat_lamp_pole, rotation=(0, math.radians(90), 0), bev=0.01)
        head_size = (0.62, 0.30, 0.14)
        bulb_scale = (1.3, 1.0, 0.7)
    else:
        arm = cylinder(f"LampArm_{idx:02d}", (hx, hy, 6.30), 0.045, 1.5,
                       mat_lamp_pole, rotation=(math.radians(90), 0, 0), bev=0.01)
        head_size = (0.30, 0.62, 0.14)
        bulb_scale = (1.0, 1.3, 0.7)
    objs.append(arm)
    ex, ey = px + ax * 1.5, py + ay * 1.5
    drop = cylinder(f"LampDrop_{idx:02d}", (ex, ey, 6.22), 0.04, 0.16,
                    mat_lamp_pole, bev=0.01)
    objs.append(drop)
    # 灯头：倒角灯壳 + 下口喇叭灯罩（截锥）+ 椭圆暖白灯珠
    head = box(f"LampHead_{idx:02d}", (ex, ey, 6.10), head_size, mat_lamp_head, bev=0.03)
    objs.append(head)
    shade = cylinder(f"LampShade_{idx:02d}", (ex, ey, 5.98), 0.17, 0.12,
                     mat_lamp_head, vertices=16, bev=0.01, radius_top=0.09)
    objs.append(shade)
    bulb = sphere(f"LampBulb_{idx:02d}", (ex, ey, 5.94), 0.08, mat_light,
                  scale=bulb_scale)
    objs.append(bulb)


lamp_idx = 0
# 南主路北缘 y=-101.4，x=-112.5..112.5 每 25m（错开中轴 0 点，避开校门轴线），横臂向南，10 盏
for x in (-112.5, -87.5, -62.5, -37.5, -12.5, 12.5, 37.5, 62.5, 87.5, 112.5):
    make_lamp(lamp_idx, x, -101.4, (0, -1))
    lamp_idx += 1
# 东主路西缘 x=101.4，y=-100..100 每 25m，横臂向东，9 盏
for y in (-100, -75, -50, -25, 0, 25, 50, 75, 100):
    make_lamp(lamp_idx, 101.4, y, (1, 0))
    lamp_idx += 1
# 环路北段外缘 y=84.9，x=-75..75 每 25m，横臂向南（伸向环路），7 盏
for x in (-75, -50, -25, 0, 25, 50, 75):
    make_lamp(lamp_idx, x, 84.9, (0, -1))
    lamp_idx += 1
# 环路南段外缘 y=-84.9，x=-75..75 每 25m，横臂向北，7 盏
for x in (-75, -50, -25, 0, 25, 50, 75):
    make_lamp(lamp_idx, x, -84.9, (0, 1))
    lamp_idx += 1
# 环路西段外缘 x=-99.9，y=-50..50 每 25m，横臂向东，5 盏
for y in (-50, -25, 0, 25, 50):
    make_lamp(lamp_idx, -99.9, y, (1, 0))
    lamp_idx += 1
assert lamp_idx == 38, lamp_idx

print(f"OBJECTS: {len(objs)} (flags 3x11=33 incl. stars, lamps 38x9=342)")

# ---- 光照：太阳 3.5，自西南，仰角约 50 度（SPEC §2，预览用，导出不含） ----
sun_data = bpy.data.lights.new("Sun", type="SUN")
sun_data.energy = 3.5
sun_data.use_shadow = True
sun = bpy.data.objects.new("Sun", sun_data)
bpy.context.collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), 0, math.radians(225))

# ---- 世界背景：淡蓝纯色 ----
world = bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.65, 0.78, 0.88, 1.0)
bg.inputs["Strength"].default_value = 1.0

# ---- 相机：东南高处 45 度俯视（预览用，导出不含；渲染走 GitHub Actions） ----
cam_data = bpy.data.cameras.new("Camera")
cam_data.type = "PERSP"
cam_data.lens = 35
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera = cam
cam.location = (28, -128, 20)
target_empty = bpy.data.objects.new("CamTarget", None)
bpy.context.collection.objects.link(target_empty)
target_empty.location = (-5, -96, 5)
track = cam.constraints.new("TRACK_TO")
track.target = target_empty
track.track_axis = "TRACK_NEGATIVE_Z"
track.up_axis = "UP_Y"
bpy.context.view_layer.update()

# ---- UV 按米缩放（返工）：贴图 1 重复 = tile 米，无 UV 的旗面先补 UV ----
bpy.context.view_layer.update()
for _o in objs:
    if _o.type != "MESH" or not _o.data.materials:
        continue
    _tile = UV_TILE.get(_o.data.materials[0])
    if _tile is None:
        continue
    _ensure_uv(_o)
    _scale_uvs_to_meters(_o, _tile)
print("UV scaled to meters for textured mats")

# ---- 存盘（先落盘） ----
os.makedirs(os.path.dirname(BLEND_PATH), exist_ok=True)
os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("saved blend:", BLEND_PATH)

# ---- 导出 GLB：只选本件 ----
bpy.ops.object.select_all(action="DESELECT")
for o in objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format="GLB",
                          use_selection=True, export_apply=True)
print("exported glb:", GLB_PATH)

# ---- 回读 GLB 确认 ----
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB_PATH)
imported = [o for o in bpy.data.objects if o not in before]
# 注意：回读时原对象仍在场景里，导入名会带 .001 后缀，先去掉后缀再计数
def _base(n):
    return n.split(".")[0]
n_poles = sum(1 for o in imported if _base(o.name).startswith("FlagPole_") and "_Top" not in _base(o.name) and "Collar" not in _base(o.name))
n_flags = sum(1 for o in imported if _base(o.name).startswith("Flag_") and _base(o.name).split("_")[1].isdigit())
n_stars = sum(1 for o in imported if _base(o.name).startswith("FlagStar_"))
n_lamps = sum(1 for o in imported if _base(o.name).startswith("LampPole_"))
n_bulbs = sum(1 for o in imported if _base(o.name).startswith("LampBulb_"))
n_shades = sum(1 for o in imported if _base(o.name).startswith("LampShade_"))
print(f"GLB reimport OK: {len(imported)} objects; "
      f"flag poles={n_poles} flags={n_flags} stars={n_stars} "
      f"lamps={n_lamps} shades={n_shades} bulbs={n_bulbs}")
for o in imported:
    bpy.data.objects.remove(o, do_unlink=True)

# ---- 删 .blend1 ----
blend1 = BLEND_PATH + "1"
if os.path.exists(blend1):
    os.remove(blend1)

print("DONE ov-flag-lamp")
