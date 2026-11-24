# st-fence v2: 储能站围栏标识 —— 纹理/材质返工
# v1 结构已通过筛查（立柱每 2m、上下横杆、竖条、警示黄牌，8x3m、高 1.8m），
# v2 只做纹理/材质提升，不改结构与位置：
#  1 金属拉丝（立柱/横杆/竖条） 2 地面混凝土噪波 3 黄牌磨损（主牌+编号小牌）
#  4 标识牌特写细节：主牌双面闪电纹、编号牌“储能站 01”、铆钉
#  5 所有面不许全平：每个材质都带噪波 Bump
# 关键管线规则（已验证）：程序化 Noise 不进 glTF；Base Color 连 MixRGB/ValToRGB
# 会丢 baseColorFactor。所以底色/粗糙度/金属度保持不链接（默认值=色板值），
# 纹理变化只走 Bump（法线）：Noise -> Bump -> Principled Normal。
# 本次不渲染（用户新规：渲染全部走 GitHub Actions，本地不渲染、不出预览图）。
# 围栏范围 x 60.0-68.0m、y 28.5-31.5m，高 1.8m；柜子位置取自 st-cabinet.py
# （4 台柜中心 x = 61.6 / 63.2 / 64.8 / 66.4，柜 y 宽 1.0m、中心 y=30，柜底 z=0.15）
# 颜色: 立柱/横杆深灰 #424A52，竖条金属灰 #8A8F94，标识牌警示黄 #E8B400
# 材质 Principled BSDF, 十六进制 sRGB 先转线性再赋值
import bpy
import math
import os
from mathutils import Vector

BLEND_PATH = "/home/hatch/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot/assets/blender/storage/st-fence.blend"
GLB_PATH = "/home/hatch/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot/assets/models/st-fence.glb"

# ---------- clean scene ----------
bpy.ops.wm.read_factory_settings(use_empty=True)

def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def hex_to_linear(h):
    h = h.lstrip("#")
    return tuple(srgb_to_linear(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4))

def make_material(name, hex_color, roughness=0.5, metallic=0.2,
                  noise_scale=10.0, noise_detail=3.0, noise_roughness=0.7,
                  noise_distortion=0.0, map_scale=(3.0, 3.0, 3.0),
                  bump_strength=0.3, bump_distance=0.02):
    """Principled BSDF：底色/粗糙度/金属度只设默认值（不链接，保证 GLB baseColorFactor）。
    纹理只走 Bump：TexCoord(Generated) -> Mapping -> Noise -> Bump -> Normal。"""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*hex_to_linear(hex_color), 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    texcoord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = map_scale
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = noise_scale
    noise.inputs["Detail"].default_value = noise_detail
    noise.inputs["Roughness"].default_value = noise_roughness
    noise.inputs["Distortion"].default_value = noise_distortion
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = bump_strength
    bump.inputs["Distance"].default_value = bump_distance
    nt.links.new(texcoord.outputs["Generated"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat

# 拉丝金属：Mapping 沿 Z 拉长（竖向拉丝纹），Noise 细密
POST_MAT = make_material("Fence_DarkGray", "#424A52", 0.6, 0.4,
                         noise_scale=18.0, noise_detail=3.0, noise_roughness=0.6,
                         map_scale=(2.0, 2.0, 10.0),
                         bump_strength=0.25, bump_distance=0.015)
BAR_MAT = make_material("Fence_MetalGray", "#8A8F94", 0.4, 0.7,
                        noise_scale=30.0, noise_detail=3.0, noise_roughness=0.6,
                        map_scale=(2.0, 2.0, 14.0),
                        bump_strength=0.20, bump_distance=0.010)
# 黄牌磨损：噪波粗、带一点扭曲，模拟日晒雨淋的斑驳
YELLOW_MAT = make_material("Sign_Yellow", "#E8B400", 0.5, 0.1,
                           noise_scale=10.0, noise_detail=4.0, noise_roughness=0.8,
                           noise_distortion=0.5, map_scale=(4.0, 4.0, 4.0),
                           bump_strength=0.35, bump_distance=0.020)
BLACK_MAT = make_material("Sign_Black", "#1A1A1A", 0.6, 0.1,
                          noise_scale=15.0, noise_detail=3.0, noise_roughness=0.7,
                          map_scale=(4.0, 4.0, 4.0),
                          bump_strength=0.20, bump_distance=0.015)
# 编号牌白底：细噪波，旧白漆微糙
WHITE_MAT = make_material("Sign_White", "#E8E8E8", 0.55, 0.05,
                          noise_scale=12.0, noise_detail=3.0, noise_roughness=0.7,
                          map_scale=(4.0, 4.0, 4.0),
                          bump_strength=0.25, bump_distance=0.015)
# 铆钉亮面金属：细拉丝
RIVET_MAT = make_material("Sign_RivetMetal", "#C0C5C9", 0.3, 0.9,
                          noise_scale=25.0, noise_detail=2.0, noise_roughness=0.5,
                          map_scale=(3.0, 3.0, 3.0),
                          bump_strength=0.15, bump_distance=0.010)
# 地面混凝土：大尺度噪波，粗糙起伏
GROUND_MAT = make_material("Preview_Ground", "#B9B3A8", 0.9, 0.0,
                           noise_scale=5.0, noise_detail=4.0, noise_roughness=0.8,
                           noise_distortion=0.3, map_scale=(2.0, 2.0, 1.0),
                           bump_strength=0.60, bump_distance=0.030)
CABINET_MAT = make_material("Preview_Cabinet", "#3E5A50", 0.5, 0.2,
                            noise_scale=8.0, noise_detail=3.0, noise_roughness=0.7,
                            map_scale=(3.0, 3.0, 3.0),
                            bump_strength=0.30, bump_distance=0.020)

# ---------- PBR 贴图（2026-11-24 返工 R1，验收 run #72） ----------
# 根因：围栏内 4 台柜与地面用的都是本件自建的 Preview_* 简化材质
# （Preview_Cabinet #3E5A50 纯色 + Bump-only、Preview_Ground #B9B3A8 纯色
# + Bump-only），与 st-cabinet 的锈蚀 PBR 根本不是同一材质——不是“同材质
# 丢贴图”，是压根没挂。修法：复用已入库的 CC0 贴图（与 st-cabinet /
# st-base 同一套，无新素材）：柜体挂 st-cabinet_textures 的锈蚀三件套，
# 地面挂 st-base_textures 的混凝土三件套。预览物不进 GLB，只影响 .blend
# 预览渲染与 storage 场景外的单件验收；场景拼装筛掉 Preview_*，不受影响。
def _load_img(path, colorspace):
    base = os.path.basename(path)
    for img in bpy.data.images:
        if img.filepath and os.path.basename(img.filepath) == base:
            img.colorspace_settings.name = colorspace
            return img
    img = bpy.data.images.load(path, check_existing=True)
    img.colorspace_settings.name = colorspace
    img.filepath = "//" + os.path.basename(os.path.dirname(path)) + "/" + base
    return img


def _apply_pbr_images(mat, tex_dir, color, rough, normal):
    """删掉程序化 Bump 节点，改挂图片三件套（color/rough/normal）。"""
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
    bsdf.inputs["Roughness"].default_value = 1.0
    tc = nt.nodes.new("ShaderNodeTexImage")
    tc.image = _load_img(os.path.join(tex_dir, color), "sRGB")
    nt.links.new(tc.outputs["Color"], bsdf.inputs["Base Color"])
    tr = nt.nodes.new("ShaderNodeTexImage")
    tr.image = _load_img(os.path.join(tex_dir, rough), "Non-Color")
    nt.links.new(tr.outputs["Color"], bsdf.inputs["Roughness"])
    tn = nt.nodes.new("ShaderNodeTexImage")
    tn.image = _load_img(os.path.join(tex_dir, normal), "Non-Color")
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nm.space = "TANGENT"
    nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    texs = [n for n in nt.nodes if n.type == "TEX_IMAGE"]
    assert len(texs) == 3, "%s: expected 3 texture nodes, got %d" % (mat.name, len(texs))
    print("PBR CHECK PASS:", mat.name, "->",
          [t.image.name if t.image else "?" for t in texs])
    return mat


_CAB_TEX = os.path.join(os.path.dirname(BLEND_PATH), "st-cabinet_textures")
_BASE_TEX = os.path.join(os.path.dirname(BLEND_PATH), "st-base_textures")
_apply_pbr_images(CABINET_MAT, _CAB_TEX,
                  "cabinet_color.jpg", "cabinet_rough.jpg", "cabinet_nor.jpg")
_apply_pbr_images(GROUND_MAT, _BASE_TEX,
                  "concrete_color.jpg", "concrete_rough.jpg", "concrete_nor.jpg")

def add_box(name, dims, loc, mat, rot_y=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.dimensions = dims
    if rot_y:
        ob.rotation_euler = (0.0, rot_y, 0.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if mat is not None:
        ob.data.materials.append(mat)
    return ob

def add_rivet(name, loc):
    """铆钉：小圆柱，轴线沿 Y（贴牌面），亮面金属。"""
    bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=0.012,
                                        vertices=12, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(RIVET_MAT)
    return ob

def add_bolt_segment(name, p1, p2, width, y, mat):
    """闪电纹一段：p1/p2 为 (x, z)，在牌面平面内拉一条斜向黑条。"""
    x1, z1 = p1
    x2, z2 = p2
    length = math.hypot(x2 - x1, z2 - z1)
    mx, mz = (x1 + x2) / 2.0, (z1 + z2) / 2.0
    angle = math.atan2(x2 - x1, z2 - z1)  # 绕 Y 的倾角
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(mx, y, mz))
    ob = bpy.context.active_object
    ob.name = name
    ob.dimensions = (width, 0.012, length)
    ob.rotation_euler = (0.0, angle, 0.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(mat)
    return ob

def join_objects(objs, name):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objs:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    joined = bpy.context.active_object
    joined.name = name
    return joined

# ---------- fence layout (v1 结构原样保留) ----------
# 五段栏杆：北整段、南左、南右（中间 x 63.25-64.75 留 1.5m 出入口）、西、东
X0, X1 = 60.0, 68.0
Y_S, Y_N = 28.5, 31.5
GATE_X0, GATE_X1 = 63.25, 64.75   # 南面出入口
FENCE_H = 1.8
POST_SIZE = 0.08
RAIL_Z = (0.15, 1.70)             # 上下两道横杆高度
BAR_Z0, BAR_Z1 = 0.10, 1.75       # 竖条上下端
BAR_STEP = 0.15

runs = [
    ("North", X0, Y_N, X1, Y_N),
    ("SouthLeft", X0, Y_S, GATE_X0, Y_S),
    ("SouthRight", GATE_X1, Y_S, X1, Y_S),
    ("West", X0, Y_S, X0, Y_N),
    ("East", X1, Y_S, X1, Y_N),
]

def run_length(x1, y1, x2, y2):
    return math.hypot(x2 - x1, y2 - y1)

def point_on_run(x1, y1, x2, y2, t):
    return (x1 + (x2 - x1) * t, y1 + (y2 - y1) * t)

# ---------- posts: 每段均分布点，首末正好落角点 ----------
# R2-T20 修 v1 bug：旧循环 t=(i*2.0)/L 在段长非 2m 倍数时末点越界
# （t>1），实测 17 根中有 4 根 stray：(60,32.5)/(68,32.5) 北出角 1.0m、
# (68.75,28.5) 东出角 0.75m、(64,28.5) 立在南门洞正中；包围盒 8.83x4.08。
# 新法：每段按段长均分 n=max(1,round(L/2)) 段，立柱 t=i/n，
# 间距约 2m、首末精确落角点、无一根越界、无一根挡门洞。
# 各段布点（去重后共 13 根）：北 60/62/64/66/68@31.5；南左 60/61.625/63.25@28.5；
# 南右 64.75/66.375/68@28.5；西 28.5/30/31.5@60；东 28.5/30/31.5@68。
# 包围盒应为 8.08x3.08（立柱 0.08 宽）。
post_positions = set()
for _name, x1, y1, x2, y2 in runs:
    L = run_length(x1, y1, x2, y2)
    n = max(1, int(round(L / 2.0)))
    for i in range(n + 1):
        px, py = point_on_run(x1, y1, x2, y2, i / n)
        post_positions.add((round(px, 3), round(py, 3)))
# 校验：无越界、无挡门洞
for _px, _py in sorted(post_positions):
    assert X0 - 1e-6 <= _px <= X1 + 1e-6 and Y_S - 1e-6 <= _py <= Y_N + 1e-6, \
        "post out of bounds: (%s, %s)" % (_px, _py)
    assert not (abs(_py - Y_S) < 1e-6 and GATE_X0 < _px < GATE_X1), \
        "post blocks gate: (%s, %s)" % (_px, _py)
print("post positions:", sorted(post_positions))

post_objs = []
for i, (px, py) in enumerate(sorted(post_positions)):
    post_objs.append(add_box(f"Fence_Post_{i:02d}",
                             (POST_SIZE, POST_SIZE, FENCE_H),
                             (px, py, FENCE_H / 2.0), POST_MAT))
print("posts:", len(post_objs))

# ---------- rails: 上下两道横杆 ----------
rail_objs = []
for rname, x1, y1, x2, y2 in runs:
    L = run_length(x1, y1, x2, y2)
    mx, my = (x1 + x2) / 2.0, (y1 + y2) / 2.0
    along_x = abs(x2 - x1) > abs(y2 - y1)
    dims = (L, 0.05, 0.05) if along_x else (0.05, L, 0.05)
    for j, rz in enumerate(RAIL_Z):
        rail_objs.append(add_box(f"Fence_Rail_{rname}_{j}",
                                 dims, (mx, my, rz), POST_MAT))

# ---------- vertical bars: 每 0.15m 一根细杆，避开立柱 ----------
bar_objs = []
for rname, x1, y1, x2, y2 in runs:
    L = run_length(x1, y1, x2, y2)
    n = int(L / BAR_STEP)
    for k in range(1, n + 1):
        d = k * BAR_STEP
        if d >= L - 0.02:
            continue
        bx, by = point_on_run(x1, y1, x2, y2, d / L)
        if any(abs(bx - px) < 0.07 and abs(by - py) < 0.07 for px, py in post_positions):
            continue
        bar_objs.append(add_box(f"Fence_Bar_{rname}_{k:03d}",
                                (0.02, 0.02, BAR_Z1 - BAR_Z0),
                                (bx, by, (BAR_Z0 + BAR_Z1) / 2.0), BAR_MAT))
print("vertical bars:", len(bar_objs))

posts_joined = join_objects(post_objs, "Fence_Posts")
rails_joined = join_objects(rail_objs, "Fence_Rails")
bars_joined = join_objects(bar_objs, "Fence_VerticalBars")
for ob in (posts_joined, rails_joined, bars_joined):
    bev = ob.modifiers.new("EdgeBevel", 'BEVEL')
    bev.width = 0.01
    bev.segments = 1
    bev.limit_method = 'ANGLE'

# ---------- main sign: 南面出入口东侧旁，“高压危险”牌 ----------
# 立杆 (65.35, 28.15)，牌面 0.6x0.4 朝南，牌顶不超过立杆顶 1.6m
SIGN_X, SIGN_Y = 65.35, 28.15
sign_objs = []
sign_objs.append(add_box("Sign_Pole", (0.06, 0.06, 1.6),
                         (SIGN_X, SIGN_Y, 0.8), POST_MAT))
sign_objs.append(add_box("Sign_BoardFrame", (0.66, 0.02, 0.46),
                         (SIGN_X, SIGN_Y, 1.35), BLACK_MAT))
sign_objs.append(add_box("Sign_BoardYellow", (0.60, 0.03, 0.40),
                         (SIGN_X, SIGN_Y - 0.005, 1.35), YELLOW_MAT))
# 文字用黑色横条示意（南/北两面各两道），下移给顶部闪电纹留位
for face, dy in (("South", -0.025), ("North", 0.015)):
    for j, bz in enumerate((1.30, 1.19)):
        sign_objs.append(add_box(f"Sign_TextBar_{face}_{j}",
                                 (0.40, 0.012, 0.06),
                                 (SIGN_X, SIGN_Y + dy, bz), BLACK_MAT))
# v2 新增：闪电纹（双面），牌面上部 z 1.36-1.52 折线三段
# 南面 y = SIGN_Y-0.026（黄牌南面 -0.020 外侧），北面 y = SIGN_Y+0.016
BOLT = [((0.03, 1.52), (-0.02, 1.44)),
        ((-0.02, 1.44), (0.02, 1.44)),
        ((0.02, 1.44), (-0.03, 1.36))]
for face, by in (("South", SIGN_Y - 0.026), ("North", SIGN_Y + 0.016)):
    for s, (p1, p2) in enumerate(BOLT):
        q1 = (SIGN_X + p1[0], p1[1])
        q2 = (SIGN_X + p2[0], p2[1])
        sign_objs.append(add_bolt_segment(f"Sign_Bolt_{face}_{s}", q1, q2,
                                          0.035, by, BLACK_MAT))
# v2 新增：编号牌“储能站 01”——立杆下部白底牌 0.34x0.18 + 黑框 + 两道编号横条
sign_objs.append(add_box("Sign_NumberFrame", (0.38, 0.02, 0.22),
                         (SIGN_X, SIGN_Y, 0.98), BLACK_MAT))
sign_objs.append(add_box("Sign_NumberPlate", (0.34, 0.025, 0.18),
                         (SIGN_X, SIGN_Y - 0.002, 0.98), WHITE_MAT))
for face, dy in (("South", -0.020), ("North", 0.015)):
    for j, bz in enumerate((1.02, 0.94)):
        sign_objs.append(add_box(f"Sign_NumberBar_{face}_{j}",
                                 (0.24, 0.012, 0.04),
                                 (SIGN_X, SIGN_Y + dy, bz), BLACK_MAT))
# v2 新增：铆钉——主牌四角（南面）+ 编号牌四角（南面），单独成组后并入
rivet_objs = []
for rx in (SIGN_X - 0.26, SIGN_X + 0.26):
    for rz in (1.19, 1.51):
        rivet_objs.append(add_rivet(f"Sign_Rivet_{rx:.2f}_{rz:.2f}",
                                    (rx, SIGN_Y - 0.024, rz)))
for rx in (SIGN_X - 0.14, SIGN_X + 0.14):
    for rz in (0.91, 1.05):
        rivet_objs.append(add_rivet(f"Sign_NumberRivet_{rx:.2f}_{rz:.2f}",
                                    (rx, SIGN_Y - 0.019, rz)))
rivets_joined = join_objects(rivet_objs, "Sign_Rivets")

# ---------- small plaques: 每台柜子北侧围栏上 1 块小黄牌 0.3x0.2 ----------
CABINET_X = [61.6, 63.2, 64.8, 66.4]
plaque_objs = []
for i, cx in enumerate(CABINET_X):
    plaque_objs.append(add_box(f"Plaque_Frame_{i + 1}",
                               (0.34, 0.015, 0.24), (cx, Y_N + 0.012, 1.20), BLACK_MAT))
    plaque_objs.append(add_box(f"Plaque_Yellow_{i + 1}",
                               (0.30, 0.02, 0.20), (cx, Y_N + 0.025, 1.20), YELLOW_MAT))
    plaque_objs.append(add_box(f"Plaque_Bar_{i + 1}",
                               (0.20, 0.012, 0.05), (cx, Y_N + 0.040, 1.20), BLACK_MAT))
# v2 新增：每块小黄牌顶部两角各 1 颗铆钉（北面）
plaque_rivet_objs = []
for i, cx in enumerate(CABINET_X):
    for dx in (-0.12, 0.12):
        plaque_rivet_objs.append(add_rivet(f"Plaque_Rivet_{i + 1}_{dx:+.2f}",
                                           (cx + dx, Y_N + 0.040, 1.27)))
plaque_rivets_joined = join_objects(plaque_rivet_objs, "Plaque_Rivets")

part_objs = [posts_joined, rails_joined, bars_joined] + sign_objs + \
    [rivets_joined] + plaque_objs + [plaque_rivets_joined]
print("part objects:", len(part_objs))

# ---------- preview-only: 示意地面 + 示意基座 + 4 台示意柜体（不导出） ----------
bpy.ops.mesh.primitive_plane_add(size=30.0, location=(64.0, 30.0, 0.0))
ground = bpy.context.active_object
ground.name = "Preview_Ground"
ground.data.materials.append(GROUND_MAT)
# 地面混凝土贴图按实尺平铺：30m 平面默认 UV 0~1 会把整张图拉满 30m、近乎纯色；
# 缩到 2m 一重复（x15），与 st-base 同口径。
for _layer in ground.data.uv_layers:
    for _loop in _layer.data:
        _loop.uv = (_loop.uv[0] * 15.0, _loop.uv[1] * 15.0)

add_box("Preview_Base", (7.0, 1.8, 0.15), (64.0, 30.0, 0.075), GROUND_MAT)
for i, cx in enumerate(CABINET_X):
    add_box(f"Preview_Cabinet_{i + 1}", (1.3, 1.0, 2.3),
            (cx, 30.0, 0.15 + 2.3 / 2.0), CABINET_MAT)

# ---------- save .blend (先落盘) ----------
os.makedirs(os.path.dirname(BLEND_PATH), exist_ok=True)
os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("blend saved:", BLEND_PATH, os.path.getsize(BLEND_PATH))

# ---------- export .glb (只选本件对象) ----------
bpy.ops.object.select_all(action='DESELECT')
for ob in part_objs:
    ob.select_set(True)
bpy.context.view_layer.objects.active = part_objs[0]
bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format='GLB',
                           use_selection=True, export_apply=True)
print("glb exported:", GLB_PATH, os.path.getsize(GLB_PATH))

# ---------- 回读验证 glb ----------
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB_PATH)
imported = [ob for ob in bpy.data.objects if ob not in before]
print("GLB reimport objects:", len(imported),
      [ob.name for ob in imported])
assert len(imported) >= 20, "glb reimport failed: too few objects"
bpy.ops.object.select_all(action='DESELECT')
for ob in imported:
    ob.select_set(True)
bpy.ops.object.delete()

bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
blend1 = BLEND_PATH + "1"
if os.path.exists(blend1):
    os.remove(blend1)
    print("Removed backup:", blend1)
print("DONE st-fence")
