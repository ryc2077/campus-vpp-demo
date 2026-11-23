# st-base v2: 储能站地面基座返工 (100kW/215kWh, Blender 中心 (64, 30))
# v1 问题：0.15 m 薄白板，无厚度感、无纹理、无锚栓、无排水。
# v2 改动：
#   1. 加厚：平台总厚 0.30 m（z -0.15 ~ +0.15），顶面仍为 z=0.15，
#      与 st-cabinet v2 的柜底（BASE_Z=0.15）接口不变；侧面 0.30 高可见。
#   2. 混凝土纹理：三层 Noise 串联 Bump（粗颗粒 + 细颗粒 + 大尺度波纹裂纹感），
#      只走法线；Base Color / Roughness / Metallic 保持不链接（默认值=色板值），
#      否则 glTF 导出器丢 baseColorFactor、Godot 里变白（全管线已验证的教训）。
#   3. 锚栓：一排 8 颗（每柜前沿 2 颗），垫圈 + 六角头，金属灰。
#   4. 排水坡：顶面中央柜垫平（z=0.15），四周坡面北高南低
#      （北缘 0.135、南缘 0.12，约 2~3% 坡），东南角设排水口 + 格栅。
#   5. 边缘倒角：平台外缘 bevel 0.03 m；伸缩缝 2 道（南-北向，三段贴合坡面）。
#   6. 所有面不许全平：顶面带坡、侧面带倒角、表面带 Bump 起伏。
# 交付：本脚本 + st-base.blend + assets/models/st-base.glb
# 新规矩：渲染全部走 GitHub Actions，本地不渲染、不出预览图。
import bpy
import math
import os

BLEND_PATH = "/home/hatch/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot/assets/blender/storage/st-base.blend"
GLB_PATH = "/home/hatch/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot/assets/models/st-base.glb"

# ---------- clean scene ----------
bpy.ops.wm.read_factory_settings(use_empty=True)


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_to_linear(h):
    h = h.lstrip("#")
    return tuple(srgb_to_linear(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4))


def make_concrete_material(name, hex_color, roughness=0.9):
    """混凝土：底色/粗糙度不链接（默认值），三层 Noise 只进串联 Bump。"""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*hex_to_linear(hex_color), 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = 0.0
    # 粗颗粒
    n1 = nt.nodes.new("ShaderNodeTexNoise")
    n1.inputs["Scale"].default_value = 30.0
    n1.inputs["Detail"].default_value = 3.0
    n1.inputs["Roughness"].default_value = 0.8
    b1 = nt.nodes.new("ShaderNodeBump")
    b1.inputs["Strength"].default_value = 0.35
    b1.inputs["Distance"].default_value = 0.02
    nt.links.new(n1.outputs["Fac"], b1.inputs["Height"])
    # 大尺度波纹 / 细裂纹感（高畸变低频 Noise）
    n2 = nt.nodes.new("ShaderNodeTexNoise")
    n2.inputs["Scale"].default_value = 7.0
    n2.inputs["Detail"].default_value = 5.0
    n2.inputs["Roughness"].default_value = 0.7
    n2.inputs["Distortion"].default_value = 1.0
    b2 = nt.nodes.new("ShaderNodeBump")
    b2.inputs["Strength"].default_value = 0.3
    b2.inputs["Distance"].default_value = 0.02
    nt.links.new(n2.outputs["Fac"], b2.inputs["Height"])
    nt.links.new(b1.outputs["Normal"], b2.inputs["Normal"])
    # 细颗粒
    n3 = nt.nodes.new("ShaderNodeTexNoise")
    n3.inputs["Scale"].default_value = 150.0
    n3.inputs["Detail"].default_value = 2.0
    n3.inputs["Roughness"].default_value = 0.7
    b3 = nt.nodes.new("ShaderNodeBump")
    b3.inputs["Strength"].default_value = 0.25
    b3.inputs["Distance"].default_value = 0.01
    nt.links.new(n3.outputs["Fac"], b3.inputs["Height"])
    nt.links.new(b2.outputs["Normal"], b3.inputs["Normal"])
    nt.links.new(b3.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def make_material(name, hex_color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*hex_to_linear(hex_color), 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


CONCRETE_MAT = make_concrete_material("Base_Concrete", "#B9B3A8", 0.9)
YELLOW_MAT = make_material("Warning_Yellow", "#E8B400", 0.6, 0.0)
BOLT_MAT = make_material("Anchor_Bolt_Steel", "#8A8F94", 0.35, 0.9)
DRAIN_MAT = make_material("Drain_Dark", "#3A3A3A", 0.8, 0.1)
GRATE_MAT = make_material("Drain_Grate", "#6B6F73", 0.5, 0.7)
JOINT_MAT = make_material("Expansion_Joint", "#7A7468", 0.95, 0.0)

# ---------- PBR 贴图（2026-11-23 v3 返工：挂下载的 CC0 贴图，替代纯色） ----------
# 底色图已用 PIL 按 SPEC 色调过（assets/blender/tint_textures.py），直接连
# Base Color；rough/normal 用原图（Non-Color）。路径存 // 相对路径，随仓库推送。
# 基座用 Concrete034 三图；旧程序化 Bump 已断开 Normal，由 normal 图替代。
# 尺寸适配：平台是 from_pydata 自定义网格（无 UV 层），按米制盒式投影补 UV
# （每 1m 一 tile）；警戒黄线/锚栓/排水/格栅/伸缩缝保持纯色。
TEX_DIR = os.path.join(os.path.dirname(BLEND_PATH), "st-base_textures")

def _load_tex(fname, colorspace):
    path = os.path.join(TEX_DIR, fname)
    img = bpy.data.images.load(path, check_existing=True)
    img.colorspace_settings.name = colorspace
    img.filepath = "//" + os.path.basename(TEX_DIR) + "/" + fname
    return img

def add_pbr(mat, color=None, rough=None, normal=None):
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    for sock in ("Base Color", "Roughness", "Normal"):
        for link in list(bsdf.inputs[sock].links):
            nt.links.remove(link)
    if color:
        bsdf.inputs["Base Color"].default_value = (1.0, 1.0, 1.0, 1.0)
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = _load_tex(color, "sRGB")
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    if rough:
        bsdf.inputs["Roughness"].default_value = 1.0
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = _load_tex(rough, "Non-Color")
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Roughness"])
    if normal:
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = _load_tex(normal, "Non-Color")
        nmap = nt.nodes.new("ShaderNodeNormalMap")
        nmap.space = "TANGENT"
        nt.links.new(tex.outputs["Color"], nmap.inputs["Color"])
        nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    return mat

def _check_pbr(mat):
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    texs = [n for n in nt.nodes if n.type == "TEX_IMAGE"]
    assert len(texs) >= 3, f"{mat.name}: expected 3 texture nodes, got {len(texs)}"
    assert bsdf.inputs["Base Color"].is_linked, f"{mat.name}: Base Color not linked"
    assert bsdf.inputs["Roughness"].is_linked, f"{mat.name}: Roughness not linked"
    assert bsdf.inputs["Normal"].is_linked, f"{mat.name}: Normal not linked"
    print(f"PBR CHECK PASS: {mat.name} color/rough/normal -> "
          f"{[t.image.name if t.image else '?' for t in texs]}")

# v3: 基座挂真实 PBR 贴图（Concrete034 染 #B9B3A8）
add_pbr(CONCRETE_MAT, "concrete_color.jpg", "concrete_rough.jpg", "concrete_nor.jpg")
_check_pbr(CONCRETE_MAT)

CX, CY = 64.0, 30.0
base_objs = []


def add_box(name, loc, dims, mat, bevel=None, bevel_segments=2, rot_x=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.dimensions = dims
    if rot_x:
        ob.rotation_euler = (rot_x, 0.0, 0.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if mat is not None:
        ob.data.materials.append(mat)
    if bevel:
        bev = ob.modifiers.new("EdgeBevel", 'BEVEL')
        bev.width = bevel
        bev.segments = bevel_segments
        bev.limit_method = 'ANGLE'
    base_objs.append(ob)
    return ob


def add_strip_between(name, p1, p2, width, thick, mat):
    """沿 y 向（带 z 坡度）的薄条：两点定中点、长度与绕 X 转角。"""
    mx = (p1[0] + p2[0]) / 2.0
    my = (p1[1] + p2[1]) / 2.0
    mz = (p1[2] + p2[2]) / 2.0
    dy = p2[1] - p1[1]
    dz = p2[2] - p1[2]
    length = math.hypot(dy, dz)
    rot_x = math.atan2(dz, dy)
    return add_box(name, (mx, my, mz), (width, length, thick), mat,
                   rot_x=rot_x)


# ---------- 1. 平台主体：自定义网格，厚 0.30，顶面带排水坡 ----------
# 外缘 7.0 x 2.0 (x 60.5~67.5, y 29~31)；中央柜垫 6.5 x 1.4 平顶 z=0.15；
# 坡面：北缘 z=0.135，南缘 z=0.12；底面 z=-0.15。
B = [(60.5, 29.0, -0.15), (67.5, 29.0, -0.15),
     (67.5, 31.0, -0.15), (60.5, 31.0, -0.15)]
T = [(60.5, 29.0, 0.12), (67.5, 29.0, 0.12),
     (67.5, 31.0, 0.135), (60.5, 31.0, 0.135)]
P = [(60.75, 29.3, 0.15), (67.25, 29.3, 0.15),
     (67.25, 30.7, 0.15), (60.75, 30.7, 0.15)]
verts = B + T + P
faces = [
    (0, 3, 2, 1),        # 底面
    (8, 9, 10, 11),      # 中央柜垫顶面（平）
    (4, 5, 9, 8),        # 南坡面
    (7, 6, 10, 11),      # 北坡面
    (5, 6, 10, 9),       # 东坡面
    (7, 4, 8, 11),       # 西坡面
    (0, 1, 5, 4),        # 南侧面
    (1, 2, 6, 5),        # 东侧面
    (2, 3, 7, 6),        # 北侧面
    (3, 0, 4, 7),        # 西侧面
]
mesh = bpy.data.meshes.new("Storage_Base_Platform_Mesh")
mesh.from_pydata(verts, [], faces)
mesh.update()
# UV：from_pydata 的网格没有 UV 层；按米制盒式投影补一层（每 1m 一贴图 tile），
# 供混凝土 PBR 贴图使用（平台 7.0x2.0m，顶面约 7x2 tile）。
_uv = mesh.uv_layers.new(name="UVMap")
for _poly in mesh.polygons:
    _n = _poly.normal
    _ax = max(range(3), key=lambda i: abs(_n[i]))
    _ua, _va = [i for i in range(3) if i != _ax]
    for _li in _poly.loop_indices:
        _co = mesh.vertices[mesh.loops[_li].vertex_index].co
        _uv.data[_li].uv = (_co[_ua], _co[_va])
platform = bpy.data.objects.new("Storage_Base_Platform", mesh)
bpy.context.collection.objects.link(platform)
platform.data.materials.append(CONCRETE_MAT)
base_objs.append(platform)
# 统一法线朝外
bpy.context.view_layer.objects.active = platform
platform.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode='OBJECT')
platform.select_set(False)
# 边缘倒角 0.03 m（外缘上下边；坡面间小夹角不参与）
bev = platform.modifiers.new("EdgeBevel", 'BEVEL')
bev.width = 0.03
bev.segments = 2
bev.limit_method = 'ANGLE'

# ---------- 2. 警戒线（v1 原样保留）：平台外缘 0.3 m 处矩形框 ----------
LINE_W, LINE_T = 0.1, 0.01
strips = [
    ("Warning_Line_North", (7.8, LINE_W, LINE_T), (CX, CY + 1.0 + 0.35, LINE_T / 2.0)),
    ("Warning_Line_South", (7.8, LINE_W, LINE_T), (CX, CY - 1.0 - 0.35, LINE_T / 2.0)),
    ("Warning_Line_East",  (LINE_W, 2.6, LINE_T), (CX + 3.5 + 0.35, CY, LINE_T / 2.0)),
    ("Warning_Line_West",  (LINE_W, 2.6, LINE_T), (CX - 3.5 - 0.35, CY, LINE_T / 2.0)),
]
for name, dims, loc in strips:
    add_box(name, loc, dims, YELLOW_MAT)

# ---------- 3. 锚栓：一排 8 颗，每柜前沿 2 颗 ----------
# 柜中心 x=61.6/63.2/64.8/66.4（st-cabinet v2），前沿 y=29.55 在平顶垫上
bolt_xs = []
for ccx in (61.6, 63.2, 64.8, 66.4):
    bolt_xs += [ccx - 0.55, ccx + 0.55]
for i, bx in enumerate(bolt_xs, 1):
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.055, depth=0.012,
                                        location=(bx, 29.55, 0.156))
    washer = bpy.context.active_object
    washer.name = "AnchorBolt_%02d_Washer" % i
    washer.data.materials.append(BOLT_MAT)
    base_objs.append(washer)
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.04, depth=0.05,
                                        location=(bx, 29.55, 0.187))
    head = bpy.context.active_object
    head.name = "AnchorBolt_%02d_Head" % i
    head.data.materials.append(BOLT_MAT)
    base_objs.append(head)

# ---------- 4. 排水口：南坡面东南角 (66.9, 29.15)，顺坡倾斜 ----------
# 南坡面 z(y) = 0.12 + (y-29.0)/0.3*0.03；y=29.15 处 z=0.135，坡角 atan(0.1)
SLOPE_ANG = math.atan(0.1)
add_box("Drain_Outlet", (66.9, 29.15, 0.1315), (0.35, 0.18, 0.012),
        DRAIN_MAT, rot_x=SLOPE_ANG)
for j, gy in enumerate((29.09, 29.13, 29.17, 29.21), 1):
    gz = 0.1375 + 0.1 * (gy - 29.15) + 0.001
    add_box("Drain_Grate_%d" % j, (66.9, gy, gz), (0.30, 0.02, 0.006),
            GRATE_MAT, rot_x=SLOPE_ANG)

# ---------- 5. 伸缩缝：2 道，南北向，三段贴合坡面 ----------
# 南坡 z(y)=0.12+(y-29)/0.3*0.03；北坡 z(y)=0.15-(y-30.7)/0.3*0.015；垫面 z=0.15
for k, jx in enumerate((62.9, 65.1), 1):
    add_strip_between("ExpansionJoint_%d_South" % k,
                      (jx, 29.02, 0.123), (jx, 29.28, 0.149),
                      0.025, 0.005, JOINT_MAT)
    add_strip_between("ExpansionJoint_%d_Pad" % k,
                      (jx, 29.3, 0.151), (jx, 30.7, 0.151),
                      0.025, 0.005, JOINT_MAT)
    add_strip_between("ExpansionJoint_%d_North" % k,
                      (jx, 30.72, 0.150), (jx, 30.98, 0.137),
                      0.025, 0.005, JOINT_MAT)

print("base objects:", len(base_objs))

# ---------- save .blend ----------
os.makedirs(os.path.dirname(BLEND_PATH), exist_ok=True)
os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)

# ---------- export .glb (只选本件对象) ----------
bpy.ops.object.select_all(action='DESELECT')
for ob in base_objs:
    ob.select_set(True)
bpy.context.view_layer.objects.active = base_objs[0]
bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format='GLB',
                           use_selection=True, export_apply=True)

# ---------- 回读验证 glb ----------
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB_PATH)
imported = [ob for ob in bpy.data.objects if ob not in before]
print("GLB reimport objects:", len(imported),
      [ob.name for ob in imported])
assert len(imported) == len(base_objs), \
    "glb reimport mismatch: %d vs %d" % (len(imported), len(base_objs))
# 删掉回读的副本，恢复干净场景再存盘
bpy.ops.object.select_all(action='DESELECT')
for ob in imported:
    ob.select_set(True)
bpy.ops.object.delete()
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("DONE st-base")
