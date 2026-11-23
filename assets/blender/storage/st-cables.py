# st-cables v2: 储能站线缆与接线箱（返工）
# 返工目标（筛查结论）:
#   旧版线槽 y=30.40 还压在柜体 footprint(y 29.5-30.5)内, 预览 dummy 绿柜挡住线槽大半;
#   接地线脚本和图里都没找到; 接线箱缺进线口。
# v2 改动:
#   1) 线槽改到柜顶后方: 中心 y=30.72 (柜北沿 30.5 外侧 0.12 间隙, y 范围 30.62-30.82),
#      z=2.62 紧贴顶盖顶 (2.51) 上方, 沿柜顶走线, 不再被柜体遮挡; 每柜一根竖管 + 水平弯头接进线槽;
#      线槽盖板分 4 段, 段间留 0.065 缝 (分缝可读)。
#   2) 补接地线: 黄绿双色扁线 (黄/绿两条并排扁条组成一条接地扁线),
#      每柜: 后壁竖向扁线 (z 0.125-0.675) + 端子 (柜端螺栓) -> 地面横向扁线 -> 接地排端子;
#      接地排为铜排 (64, 30.98), 另有一条黄绿主接地线从接地排引到接线箱南面。
#   3) 接线箱: 箱体 + 箱门(北面) + 把手 + 合页 x2 + 底座 + 顶盖 + 南面进线口 x2
#      (进线格兰头圆筒 + 黑/红电缆短头各一根)。
#   4) 线缆外皮纹理: 黑/红/黄绿三种电缆材质, 轻微噪波 + 粗糙度变化——但只走 Bump(法线):
#      Base Color / Roughness / Metallic 一律保持不链接 (默认值=色板值), Noise 只连 Bump.Height,
#      这样 glTF 导出保留 baseColorFactor, Godot 里不变白。不要把噪波连进 Base Color。
#   5) 所有面不许全平: 每个材质都带 Bump 噪波, 盒体带小倒角。
# 柜体位置尺寸取自 st-cabinet.py: 4 台柜, 单柜 1.3(x)x1.0(y)x2.3(z)m,
# 柜中心 x = 61.6 / 63.2 / 64.8 / 66.4, y = 30.0, 柜底 z = 0.15,
# 柜体顶 z = 2.45, 顶盖顶 z = 2.51, 柜北沿 y = 30.5。
# 本件只做线槽/竖管/弯头/接线箱/接地线/接地排/电缆沟盖板, 不做柜体/门/基座/围栏,
# 场景里不再放预览 dummy 绿柜 (v1 挡线槽的根源)。
# 颜色: 线槽浅灰 #C0C5C9, 接线箱/沟盖板深灰 #424A52, 接地黄 #E8B400 / 接地绿 #2E7D32,
# 铜排 #B87333, 电缆黑 #1A1A1A / 电缆红 #A33327。
# 本次不渲染 (用户新规矩: 渲染全部走 GitHub Actions, 本地不渲染、不出预览图)。
# 交付: 本脚本 + st-cables.blend + assets/models/st-cables.glb, 以 GLB 回读节点坐标核对为准。
import bpy
import math
import os

BASE = "/home/hatch/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot"
BLEND_PATH = BASE + "/assets/blender/storage/st-cables.blend"
GLB_PATH = BASE + "/assets/models/st-cables.glb"

# ---------- clean scene ----------
bpy.ops.wm.read_factory_settings(use_empty=True)

def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def hex_to_linear(h):
    h = h.lstrip("#")
    return tuple(srgb_to_linear(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4))

def make_material(name, hex_color, roughness=0.5, metallic=0.2,
                  bump_strength=0.25, bump_distance=0.08, noise_scale=8.0):
    """Principled BSDF; Base Color/Roughness/Metallic 只设默认值不链接。
    纹理变化只走 Bump: Noise -> Bump.Height -> BSDF.Normal。"""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*hex_to_linear(hex_color), 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = noise_scale
    noise.inputs["Detail"].default_value = 2.0
    noise.inputs["Roughness"].default_value = 0.7
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = bump_strength
    bump.inputs["Distance"].default_value = bump_distance
    nt.links.new(noise.outputs["Color"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat

TRAY_MAT   = make_material("CableTray_LightGray", "#C0C5C9", 0.6, 0.3,
                           bump_strength=0.15, noise_scale=6.0)
RISER_MAT  = make_material("Riser_MetalGray", "#8A8F94", 0.45, 0.6,
                           bump_strength=0.15, noise_scale=6.0)
BOX_MAT    = make_material("JunctionBox_DarkGray", "#424A52", 0.55, 0.25,
                           bump_strength=0.2, noise_scale=5.0)
BOX_DARK   = make_material("JunctionBox_Dark", "#363D44", 0.6, 0.25,
                           bump_strength=0.2, noise_scale=5.0)
SEAM_MAT   = make_material("DoorSeam", "#2B3136", 0.7, 0.1,
                           bump_strength=0.2, noise_scale=5.0)
TRENCH_MAT = make_material("TrenchCover_DarkGray", "#424A52", 0.8, 0.1,
                           bump_strength=0.2, noise_scale=5.0)
GND_Y_MAT  = make_material("Ground_Yellow", "#E8B400", 0.55, 0.1,
                           bump_strength=0.3, bump_distance=0.05, noise_scale=12.0)
GND_G_MAT  = make_material("Ground_Green", "#2E7D32", 0.55, 0.1,
                           bump_strength=0.3, bump_distance=0.05, noise_scale=12.0)
COPPER_MAT = make_material("GroundBus_Copper", "#B87333", 0.35, 0.8,
                           bump_strength=0.15, noise_scale=6.0)
TERM_MAT   = make_material("Terminal_MetalGray", "#8A8F94", 0.4, 0.7,
                           bump_strength=0.15, noise_scale=6.0)
CABLE_BLACK = make_material("Cable_Black", "#1A1A1A", 0.6, 0.05,
                            bump_strength=0.3, bump_distance=0.05, noise_scale=14.0)
CABLE_RED   = make_material("Cable_Red", "#A33327", 0.55, 0.05,
                            bump_strength=0.3, bump_distance=0.05, noise_scale=14.0)

# ---------- PBR 贴图（2026-11-23 v3 返工：挂下载的 CC0 贴图，替代纯色） ----------
# 底色图已用 PIL 按 SPEC 色调过（assets/blender/tint_textures.py），直接连
# Base Color；rough/normal 用原图（Non-Color）。路径存 // 相对路径，随仓库推送。
# 线槽用 white_stucco 三图；旧程序化 Bump 已断开 Normal，由 normal 图替代。
# 尺寸适配：线槽顶面 UV 按实尺缩放（tile 约 2m）。接线箱/电缆/铜排/接地保持纯色。
TEX_DIR = os.path.join(os.path.dirname(BLEND_PATH), "st-cables_textures")

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

def scale_uvs(obj, sx, sy):
    """UV 整体缩放：贴图按实尺重复（tile 约 2m 时 sx=长/2, sy=宽/2）。"""
    for layer in obj.data.uv_layers:
        for loop in layer.data:
            u, v = loop.uv
            loop.uv = (u * sx, v * sy)

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

# v3: 线槽挂真实 PBR 贴图（white_stucco 染 #C0C5C9）
add_pbr(TRAY_MAT, "tray_color.jpg", "tray_rough.jpg", "tray_nor.jpg")
_check_pbr(TRAY_MAT)

CAB_X = [61.6, 63.2, 64.8, 66.4]
CY = 30.0
CAB_TOP = 2.45
CAP_TOP = 2.51
CAB_NORTH = 30.5

part_objs = []

def add_box(name, dims, loc, mat, bevel=0.015, rot_z=0.0, uv_scale=None):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.dimensions = dims
    if rot_z:
        ob.rotation_euler = (0.0, 0.0, rot_z)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(mat)
    if uv_scale is not None:
        scale_uvs(ob, uv_scale[0], uv_scale[1])
    if bevel:
        bev = ob.modifiers.new("EdgeBevel", 'BEVEL')
        bev.width = bevel
        bev.segments = 2
        bev.limit_method = 'ANGLE'
    part_objs.append(ob)
    return ob

def add_cyl(name, radius, depth, loc, mat, rot=(0.0, 0.0, 0.0), vertices=16):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
                                        depth=depth, location=loc,
                                        rotation=rot)
    ob = bpy.context.active_object
    ob.name = name
    ob.data.materials.append(mat)
    part_objs.append(ob)
    return ob

# ---------- 1) 柜顶后方线槽: 沿 x 通长 6.1m, 中心 (64, 30.72, 2.62) ----------
TRAY_Y = 30.72
TRAY_Z = 2.62
tray = add_box("CableTray", (6.1, 0.20, 0.12), (64.0, TRAY_Y, TRAY_Z), TRAY_MAT,
               uv_scale=(3.05, 0.1))
for ex in (60.93, 67.07):
    add_box("CableTray_EndCap", (0.04, 0.24, 0.16), (ex, TRAY_Y, TRAY_Z),
            TRAY_MAT, bevel=0.01)
# 盖板分缝: 4 段盖板, 每段 1.45m, 段间留缝约 0.065, 盖在槽顶 (z=2.69)
LID_LEN = 1.45
x_start = 60.95 + 0.02
pitch = (6.1 - 0.04) / 4.0
for i in range(4):
    cx = x_start + i * pitch + LID_LEN / 2.0
    add_box(f"CableTray_Lid_{i + 1}", (LID_LEN, 0.24, 0.02),
            (cx, TRAY_Y, 2.69), BOX_DARK, bevel=0.005)

# ---------- 柜顶竖管 + 水平弯头: 每柜一套, 从顶盖后沿接进线槽 ----------
for i, cx in enumerate(CAB_X):
    # 竖管: r=0.05, 从顶盖顶 2.51 升到 2.67, 立在柜顶后沿 y=30.44
    add_cyl(f"CabinetRiser_{i + 1}", 0.05, 0.18, (cx, 30.44, 2.59), RISER_MAT)
    # 弯头: 水平小盒 y 30.40-30.76, 把竖管顶连到线槽南侧
    add_box(f"CabinetRiser_Elbow_{i + 1}", (0.10, 0.36, 0.08),
            (cx, 30.58, 2.62), RISER_MAT, bevel=0.01)

# ---------- 2) 接地: 接地排 + 每柜黄绿双色扁线 + 端子 + 主接地线 ----------
BUS_Y, BUS_Z = 30.98, 0.10
add_box("GroundBusbar", (5.4, 0.08, 0.05), (64.0, BUS_Y, BUS_Z), COPPER_MAT,
        bevel=0.01)
for sx in (61.8, 66.2):
    add_box("GroundBusbar_Support", (0.10, 0.10, 0.08), (sx, BUS_Y, 0.04),
            TRENCH_MAT, bevel=0.01)

for i, cx in enumerate(CAB_X):
    # 竖向扁线: 贴柜后壁 (y=30.515), z 0.125-0.675; 黄/绿两条并排 = 黄绿双色
    add_box(f"GroundStrap_Vert_Yellow_{i + 1}", (0.025, 0.015, 0.55),
            (cx - 0.013, 30.515, 0.40), GND_Y_MAT, bevel=0.003)
    add_box(f"GroundStrap_Vert_Green_{i + 1}", (0.025, 0.015, 0.55),
            (cx + 0.013, 30.515, 0.40), GND_G_MAT, bevel=0.003)
    # 柜端端子: 压片 + 螺栓 (螺栓轴沿 y)
    add_box(f"GroundTerminal_Cabinet_{i + 1}", (0.10, 0.03, 0.06),
            (cx, 30.52, 0.68), TERM_MAT, bevel=0.005)
    add_cyl(f"GroundTerminal_CabinetBolt_{i + 1}", 0.02, 0.05,
            (cx, 30.53, 0.68), TERM_MAT, rot=(math.radians(90), 0.0, 0.0),
            vertices=12)
    # 地面横向扁线: y 30.51-30.97, z=0.06, 黄/绿并排, 从柜后壁引到接地排
    add_box(f"GroundStrap_Horiz_Yellow_{i + 1}", (0.025, 0.46, 0.015),
            (cx - 0.013, 30.74, 0.06), GND_Y_MAT, bevel=0.003)
    add_box(f"GroundStrap_Horiz_Green_{i + 1}", (0.025, 0.46, 0.015),
            (cx + 0.013, 30.74, 0.06), GND_G_MAT, bevel=0.003)
    # 排端端子: 压在接地排上的压片
    add_box(f"GroundTerminal_Busbar_{i + 1}", (0.10, 0.03, 0.05),
            (cx, 30.96, 0.10), TERM_MAT, bevel=0.005)

# 主接地线: 接地排 -> 接线箱南面, 黄/绿并排扁线, y 31.01-31.29, z=0.06
add_box("GroundStrap_Main_Yellow", (0.025, 0.28, 0.015),
        (64.0 - 0.013, 31.15, 0.06), GND_Y_MAT, bevel=0.003)
add_box("GroundStrap_Main_Green", (0.025, 0.28, 0.015),
        (64.0 + 0.013, 31.15, 0.06), GND_G_MAT, bevel=0.003)
add_box("GroundTerminal_JunctionBox", (0.10, 0.03, 0.05),
        (64.0, 31.26, 0.08), TERM_MAT, bevel=0.005)

# ---------- 3) 接线箱: 箱体 + 底座 + 顶盖 + 箱门 + 合页 + 把手 + 进线口 ----------
BOX_X, BOX_Y = 64.0, 31.5
add_box("JunctionBox", (0.8, 0.5, 1.2), (BOX_X, BOX_Y, 0.6), BOX_MAT)
add_box("JunctionBox_Base", (0.9, 0.6, 0.10), (BOX_X, BOX_Y, 0.05),
        BOX_DARK, bevel=0.01)
add_box("JunctionBox_TopCap", (0.86, 0.56, 0.05), (BOX_X, BOX_Y, 1.225),
        BOX_DARK, bevel=0.01)
# 箱门: 北面 (y=31.75 外侧检修面), 0.6 x 1.0
add_box("JunctionBox_Door", (0.6, 0.02, 1.0), (BOX_X, BOX_Y + 0.26, 0.6),
        SEAM_MAT, bevel=0.005)
# 合页 x2: 门左沿
for hz in (0.25, 0.95):
    add_box("JunctionBox_Hinge", (0.04, 0.03, 0.10),
            (BOX_X - 0.28, BOX_Y + 0.26, hz), TERM_MAT, bevel=0.005)
# 把手: 门板外侧横向
add_box("JunctionBox_Handle", (0.14, 0.04, 0.03),
        (BOX_X + 0.18, BOX_Y + 0.28, 0.65), RISER_MAT, bevel=0.005)
# 进线口 x2: 南面 (y=31.25, 朝柜子/电缆沟), 格兰头圆筒轴沿 y + 电缆短头
for j, (gx, cmat) in enumerate(((63.75, CABLE_BLACK), (64.25, CABLE_RED))):
    add_cyl(f"JunctionBox_Inlet_{j + 1}", 0.07, 0.16, (gx, 31.18, 0.35),
            TERM_MAT, rot=(math.radians(90), 0.0, 0.0))
    add_cyl(f"JunctionBox_InletCable_{j + 1}", 0.045, 0.20, (gx, 31.05, 0.35),
            cmat, rot=(math.radians(90), 0.0, 0.0))

# ---------- 地面电缆沟盖板: 接线箱南面 -> 每台柜子北沿 (v1 保留) ----------
BOX_TARGETS = [63.7, 63.9, 64.1, 64.3]
for i, cx in enumerate(CAB_X):
    sx, sy = cx, 30.5
    tx, ty = BOX_TARGETS[i], 31.25
    dx, dy = tx - sx, ty - sy
    length = math.hypot(dx, dy) + 0.20
    mx, my = (sx + tx) / 2.0, (sy + ty) / 2.0
    ang = math.atan2(dy, dx)
    add_box(f"TrenchCover_{i + 1}", (length, 0.3, 0.05),
            (mx, my, 0.025), TRENCH_MAT, bevel=0.01, rot_z=ang)

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
print("glb exported:", GLB_PATH, os.path.getsize(GLB_PATH),
      "part objects:", len(part_objs))

# ---------- 回读验证 glb: 按节点坐标核对线槽/接地线/接线箱 ----------
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB_PATH)
imported = [ob for ob in bpy.data.objects if ob not in before]
print("GLB reimport objects:", len(imported))
tray = [o for o in imported if o.name.startswith("CableTray")]
gnd = [o for o in imported if o.name.startswith("Ground")]
jbox = [o for o in imported if o.name.startswith("JunctionBox")]
print("tray count:", len(tray),
      [(o.name, tuple(round(v, 3) for v in o.location)) for o in tray])
print("ground count:", len(gnd),
      [(o.name, tuple(round(v, 3) for v in o.location)) for o in gnd])
print("junctionbox count:", len(jbox),
      [(o.name, tuple(round(v, 3) for v in o.location)) for o in jbox])
assert len(imported) == len(part_objs), \
    f"glb reimport count mismatch: {len(imported)} vs {len(part_objs)}"
assert len(tray) >= 7, "tray objects missing"
assert len(gnd) >= 27, "ground objects missing"
assert len(jbox) >= 10, "junction box objects missing"
# 线槽必须在柜北沿外侧 (y>30.5), 且高于顶盖顶 (回读名带 .001 后缀, 用前缀匹配)
tray_main = [o for o in tray if o.name.startswith("CableTray")
             and "EndCap" not in o.name and "Lid" not in o.name]
assert tray_main and abs(tray_main[0].location.y - 30.72) < 0.01 \
    and abs(tray_main[0].location.z - 2.62) < 0.01, "tray position wrong"
assert all(abs(o.location.y - 30.72) < 0.01 for o in tray
           if o.name.startswith("CableTray_Lid")), "tray lid y wrong"
# 接地线必须存在且接地排在位
bus = [o for o in gnd if o.name.startswith("GroundBusbar")
       and "Support" not in o.name]
assert bus and abs(bus[0].location.y - 30.98) < 0.01, "ground busbar missing/wrong"
assert any(o.name.startswith("GroundStrap_Vert_Yellow") for o in gnd), \
    "vertical ground strap missing"
assert any(o.name.startswith("GroundStrap_Horiz_Green") for o in gnd), \
    "horizontal ground strap missing"
# 接线箱必须在 (64, 31.5, 0.6), 进线口在南面 y<31.25
box_main = [o for o in jbox if o.name.startswith("JunctionBox")
            and o.name.split(".")[0] == "JunctionBox"]
assert box_main and abs(box_main[0].location.x - 64.0) < 0.01 \
    and abs(box_main[0].location.y - 31.5) < 0.01 \
    and abs(box_main[0].location.z - 0.6) < 0.01, "junction box position wrong"
assert any(o.name.startswith("JunctionBox_Inlet") and o.location.y < 31.25
           for o in jbox), "junction box inlet missing"
# 底色保留检查: 回读材质底色不得丢（纯色件 default 不得全白且不得有链接；
#   贴图件线槽允许 Base Color 连贴图，核对 tray_color 链接存在）
for o in imported:
    for slot in o.material_slots:
        m = slot.material
        if m and m.use_nodes:
            bsdf = m.node_tree.nodes.get("Principled BSDF")
            if bsdf:
                texs = [n for n in m.node_tree.nodes if n.type == "TEX_IMAGE"]
                if any((t.image and "tray_color" in t.image.name) for t in texs):
                    print(f"reimported textured material {m.name}: tray_color link OK")
                    continue
                bc = bsdf.inputs["Base Color"].default_value
                assert not (bc[0] > 0.99 and bc[1] > 0.99 and bc[2] > 0.99), \
                    f"material {m.name} base color lost (white)"
                # Base Color 必须无输入链接
                assert not bsdf.inputs["Base Color"].is_linked, \
                    f"material {m.name} base color linked"
print("GLB reimport check PASSED")
# 删掉回读副本, 恢复干净场景再存盘
bpy.ops.object.select_all(action='DESELECT')
for ob in imported:
    ob.select_set(True)
bpy.ops.object.delete()
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("DONE st-cables")
