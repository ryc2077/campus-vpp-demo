# st-doors v2: 储能站电池舱门与散热 (st-cabinet 的配套件，只做门/把手/风扇罩/百叶)
# v2 返工（2026-11-22）：结构与旧版完全一致，只补纹理 + 坐标验证北面百叶。
#   旧版筛查：双开门 + 门缝 + 横杆把手 + 顶风扇罩齐全，光影 9 件里最好；
#   只差：① 北面百叶背面看不到 → 本次用 GLB 节点坐标验证（不渲染）；
#          ② 补纹理：金属拉丝（门板）、门缝深浅、把手金属、风扇罩格栅纹理。
# 纹理铁律（全管线已验证）：程序化 Noise 不进 glTF 导出，且 Base Color 连
#   MixRGB/ValToRGB 时导出器会丢 baseColorFactor、Godot 里变白。
#   → 底色/粗糙度/金属度保持不链接（默认值=色板值），纹理变化只走 Bump（法线）。
#   这样 GLB 里 baseColorFactor 能保留、.blend 里纹理也在。绝不把噪波连进 Base Color。
# 新规矩：渲染全部走 GitHub Actions，本地不渲染、不出预览图。本脚本只做：
#   建模 → 存 .blend → 导出 .glb → 回读验证（含北面百叶坐标验证）。
# 柜体数据取自 st-cabinet.py（只读，不重算）：
#   4 台柜一字排开，单柜 1.3(x) x 1.0(y) x 2.3(z) m，柜中心 x = 61.6 / 63.2 / 64.8 / 66.4
#   柜中心 y = 30.0，柜底 z = 0.15，柜顶 z = 2.45
#   顶盖顶面：st-cabinet v2 已把顶盖加厚到 0.10（中心 z=2.50），实际顶面 z = 2.55；
#   本件旧假设 2.51 已过时（见下方 FAN_LIFT），只改风扇组 z 偏移补偿，不动其他件。
#   南面 y = 29.5，北面 y = 30.5
# 本件：
#   南面双开门：每扇 0.6 x 2.0 x 0.03 m，门缝居中（缝宽 0.02），门板贴在柜面外 0.02 m
#   门把手：小横杆（沿 x 的圆柱，r=0.015，长 0.20），贴门板南面
#   顶部风扇罩：直径 0.4 m 浅灰圆盘 + 同心格栅环 + 十字条 + 中心毂，置于顶盖顶面
#   北面散热百叶：3 条横向细条，深灰，贴北面外 0.02 m（中心 y = 30.53）
# 颜色：门板 #35483F（比柜体 #3E5A50 略深）；风扇盘 #C0C5C9；格栅/百叶 #424A52；把手金属灰 #8A8F94
# 材质只用 Principled BSDF；十六进制 sRGB 先转线性再赋值
import bpy
import math
import os

BLEND_PATH = "/home/hatch/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot/assets/blender/storage/st-doors.blend"
GLB_PATH = "/home/hatch/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot/assets/models/st-doors.glb"

# ---------- clean scene ----------
bpy.ops.wm.read_factory_settings(use_empty=True)

def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def hex_to_linear(h):
    h = h.lstrip("#")
    return tuple(srgb_to_linear(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4))

def add_bump(mat, noise_scale, bump_strength, bump_distance=0.02, detail=2.0, distortion=0.0):
    """只走 Bump（法线）的程序化纹理：Noise -> Bump -> BSDF.Normal。
    Base Color / Roughness / Metallic 全程不链接，保持默认值=色板值，
    这样 glTF 导出保留 baseColorFactor，Godot 里不变白。"""
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes["Principled BSDF"]
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = noise_scale
    noise.inputs["Detail"].default_value = detail
    noise.inputs["Roughness"].default_value = 0.7
    noise.inputs["Distortion"].default_value = distortion
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = bump_strength
    bump.inputs["Distance"].default_value = bump_distance
    links.new(noise.outputs["Color"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat

def make_material(name, hex_color, roughness=0.5, metallic=0.2,
                  bump=None):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    # 底色/粗糙度/金属度：只设默认值，不链接任何节点（保 baseColorFactor）
    bsdf.inputs["Base Color"].default_value = (*hex_to_linear(hex_color), 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if bump:
        add_bump(mat, *bump)
    return mat

# v2 纹理（只走 Bump，参数 = (noise_scale, bump_strength, bump_distance, detail, distortion)）：
#   门板：细密拉丝——高频噪波 + 弱 Bump，沿面拉丝感；门缝深浅靠缝两侧的
#         倒角 + Bump 落差呈现（几何缝宽 0.02 不动）
DOOR_MAT = make_material("Door_DarkGreenGray", "#35483F", 0.55, 0.2,
                         bump=(35.0, 0.25, 0.015, 3.0, 0.6))
#   把手：抛光金属细纹——低频弱 Bump，保留金属光泽
HANDLE_MAT = make_material("Handle_MetalGray", "#8A8F94", 0.35, 0.7,
                           bump=(8.0, 0.15, 0.01, 2.0, 0.0))
#   风扇盘：浅灰金属板——中频轻纹
FAN_MAT = make_material("Fan_LightGray", "#C0C5C9", 0.5, 0.4,
                        bump=(20.0, 0.2, 0.015, 2.0, 0.3))
#   风扇罩格栅：格栅纹理——强 Bump，格栅环/十字条/中心毂的粗糙颗粒感
GRILLE_MAT = make_material("Grille_DarkGray", "#424A52", 0.6, 0.3,
                           bump=(12.0, 0.45, 0.03, 2.0, 0.5))
#   北面百叶：散热片纹理——横向条纹感（噪波拉伸由 Bump 强度呈现）
LOUVER_MAT = make_material("Louver_DarkGray", "#424A52", 0.6, 0.3,
                           bump=(15.0, 0.35, 0.025, 2.0, 0.4))
CABINET_MAT = make_material("Preview_Cabinet_GreenGray", "#3E5A50", 0.5, 0.2)
CAP_MAT = make_material("Preview_Cabinet_Cap", "#35483F", 0.55, 0.2)

# ---------- PBR 贴图（2026-11-23 v3 返工：挂下载的 CC0 贴图，替代纯色） ----------
# 底色图已用 PIL 按 SPEC 色调过（assets/blender/tint_textures.py），直接连
# Base Color；rough/normal 用原图（Non-Color）。路径存 // 相对路径，随仓库推送。
# 门板用 blue_metal_plate 三图；旧程序化 Bump 已断开 Normal，由 normal 图替代。
# 尺寸适配：门扇 UV 按实尺缩放（tile 约 2m）。把手/风扇/格栅/百叶保持纯色。
TEX_DIR = os.path.join(os.path.dirname(BLEND_PATH), "st-doors_textures")

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
    """UV 整体缩放：贴图按实尺重复（tile 约 2m 时 sx=宽/2, sy=高/2）。"""
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

# v3: 门板挂真实 PBR 贴图（blue_metal_plate 染 #35483F）
add_pbr(DOOR_MAT, "door_color.jpg", "door_rough.jpg", "door_nor.jpg")
_check_pbr(DOOR_MAT)

# ---------- 柜体基准（抄 st-cabinet.py） ----------
CAB_W, CAB_D, CAB_H = 1.3, 1.0, 2.3
GAP = 0.3
BASE_Z = 0.15
CY = 30.0
SOUTH_Y = CY - CAB_D / 2.0   # 29.5
NORTH_Y = CY + CAB_D / 2.0   # 30.5
CAP_TOP_Z = BASE_Z + CAB_H + 0.06  # 2.51，本件旧假设的顶盖顶面（已过时，仅作风扇组基准）
# 返修 2026-11-22（风扇罩埋顶盖）：实测 st-cabinet v2 顶盖 z=[2.45, 2.55]，顶面 2.55；
#   风扇盘原底面 2.510 落在顶盖内，只有毂顶露出 0.005。抬高量以盘底高出顶盖顶面为准：
#   盘底 2.510 + FAN_LIFT 0.045 = 2.555，高出顶盖顶面 0.005。只改风扇组 z 偏移。
FAN_LIFT = 0.045
x0 = 64.0 - (4 * CAB_W + 3 * GAP) / 2.0 + CAB_W / 2.0
CENTERS_X = [x0 + i * (CAB_W + GAP) for i in range(4)]  # 61.6 / 63.2 / 64.8 / 66.4

def add_box(name, dims, loc, mat, bevel=None, uv_scale=None):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(mat)
    if uv_scale is not None:
        scale_uvs(ob, uv_scale[0], uv_scale[1])
    if bevel:
        bev = ob.modifiers.new("EdgeBevel", 'BEVEL')
        bev.width = bevel
        bev.segments = 2
        bev.limit_method = 'ANGLE'
    return ob

part_objs = []

# ---------- 每台柜：双开门 + 把手 + 风扇罩 + 百叶（几何与 v1 完全一致） ----------
DOOR_W, DOOR_H, DOOR_T = 0.6, 2.0, 0.03
DOOR_GAP = 0.02            # 门缝宽
DOOR_Z = BASE_Z + CAB_H / 2.0   # 1.30，上下各留 0.15 m
DOOR_Y = SOUTH_Y - 0.02 - DOOR_T / 2.0  # 29.465，门板北面距柜面 0.02 m
HANDLE_Z = 1.25
HANDLE_Y = SOUTH_Y - 0.02 - DOOR_T - 0.015  # 29.435，横杆贴门板南面（相切）
LOUVER_Y = NORTH_Y + 0.02 + 0.01  # 30.53，百叶北面距柜面 0.02 m

for i, cx in enumerate(CENTERS_X):
    tag = "PCS" if i == 3 else f"Battery{i + 1}"
    # --- 双开门：左扇中心 cx-0.31，右扇 cx+0.31（缝 0.02 居中） ---
    for side, dx in (("L", -0.31), ("R", 0.31)):
        door = add_box(f"{tag}_Door_{side}",
                       (DOOR_W, DOOR_T, DOOR_H),
                       (cx + dx, DOOR_Y, DOOR_Z), DOOR_MAT, bevel=0.005,
                       uv_scale=(DOOR_W / 2.0, DOOR_H / 2.0))
        part_objs.append(door)
        # --- 把手：沿 x 的小横杆，靠近门缝一侧 ---
        hx = cx + dx * 0.32  # 左扇把手在 cx-0.10，右扇在 cx+0.10
        bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.015, depth=0.20,
                                            location=(hx, HANDLE_Y, HANDLE_Z),
                                            rotation=(0.0, math.radians(90), 0.0))
        handle = bpy.context.active_object
        handle.name = f"{tag}_Handle_{side}"
        handle.data.materials.append(HANDLE_MAT)
        part_objs.append(handle)
    # --- 顶部风扇罩：圆盘 + 格栅环 + 十字条 + 中心毂，置于顶盖顶面之上（FAN_LIFT 抬高后） ---
    fan_z = CAP_TOP_Z + 0.015 + FAN_LIFT  # 圆盘中心 2.570，盘底 2.555（顶盖顶面 2.55 之上 0.005）
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.20, depth=0.03,
                                        location=(cx, CY, fan_z))
    disc = bpy.context.active_object
    disc.name = f"{tag}_FanDisc"
    disc.data.materials.append(FAN_MAT)
    part_objs.append(disc)
    # 同心格栅环（两道）
    for r in (0.13, 0.07):
        bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=0.008,
                                         major_segments=32, minor_segments=8,
                                         location=(cx, CY, fan_z + 0.015))
        ring = bpy.context.active_object
        ring.name = f"{tag}_FanRing_{int(r * 100)}"
        ring.data.materials.append(GRILLE_MAT)
        part_objs.append(ring)
    # 十字格栅条
    for j, rot in enumerate((0.0, math.radians(90))):
        bar = add_box(f"{tag}_FanBar_{j}", (0.38, 0.025, 0.012),
                      (cx, CY, fan_z + 0.018), GRILLE_MAT)
        bar.rotation_euler = (0.0, 0.0, rot)
        part_objs.append(bar)
    # 中心毂
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.05, depth=0.02,
                                        location=(cx, CY, fan_z + 0.02))
    hub = bpy.context.active_object
    hub.name = f"{tag}_FanHub"
    hub.data.materials.append(GRILLE_MAT)
    part_objs.append(hub)
    # --- 北面散热百叶：3 条横向细条 ---
    for k, lz in enumerate((1.70, 1.95, 2.20)):
        louver = add_box(f"{tag}_Louver_{k + 1}", (1.0, 0.02, 0.10),
                         (cx, LOUVER_Y, lz), LOUVER_MAT)
        part_objs.append(louver)

print("part objects:", len(part_objs))
assert len(part_objs) == 4 * (2 + 2 + 6 + 3), "part count mismatch"

# ---------- v2 纹理自查：纯色材质 Base Color / Roughness 必须无链接，Bump 必须已连 Normal ----------
# （v3：门板改挂 PBR 贴图，不再走此自查，改由 _check_pbr 校验图片链接）
for mat in (HANDLE_MAT, FAN_MAT, GRILLE_MAT, LOUVER_MAT):
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    assert not bsdf.inputs["Base Color"].is_linked, f"{mat.name}: Base Color linked!"
    assert not bsdf.inputs["Roughness"].is_linked, f"{mat.name}: Roughness linked!"
    assert bsdf.inputs["Normal"].is_linked, f"{mat.name}: Bump not linked!"
    print(f"material OK: {mat.name} base={tuple(round(v, 3) for v in bsdf.inputs['Base Color'].default_value[:3])} "
          f"rough={bsdf.inputs['Roughness'].default_value} bump_linked=True")

# ---------- preview-only 示意柜体（不导出，仅 .blend 内参照） ----------
preview_objs = []
for i, cx in enumerate(CENTERS_X):
    name = "PCS_Cabinet" if i == 3 else f"Battery_Cabinet_{i + 1}"
    body = add_box("Preview_" + name, (CAB_W, CAB_D, CAB_H),
                   (cx, CY, BASE_Z + CAB_H / 2.0), CABINET_MAT)
    cap = add_box("Preview_" + name + "_TopCap", (CAB_W + 0.10, CAB_D + 0.10, 0.06),
                  (cx, CY, BASE_Z + CAB_H + 0.03), CAP_MAT)
    preview_objs.extend([body, cap])

# ---------- save .blend（先落盘） ----------
os.makedirs(os.path.dirname(BLEND_PATH), exist_ok=True)
os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("blend saved:", BLEND_PATH, "size:", os.path.getsize(BLEND_PATH))

# ---------- export .glb（只选本件对象，示意柜体不导出） ----------
bpy.ops.object.select_all(action='DESELECT')
for ob in part_objs:
    ob.select_set(True)
bpy.context.view_layer.objects.active = part_objs[0]
bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format='GLB',
                           use_selection=True, export_apply=True)
print("glb exported:", GLB_PATH, "size:", os.path.getsize(GLB_PATH))

# ---------- 回读验证 glb ----------
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB_PATH)
imported = [ob for ob in bpy.data.objects if ob not in before]
print("GLB reimport objects:", len(imported), [ob.name for ob in imported])
assert len(imported) == len(part_objs), \
    f"glb reimport count mismatch: {len(imported)} != {len(part_objs)}"

# 北面百叶坐标验证：百叶必须在北面（y > 30.5），中心 y 应为 30.53
louvers = [ob for ob in imported if "Louver" in ob.name]
print("louver count:", len(louvers))
assert len(louvers) == 12, f"expected 12 louvers, got {len(louvers)}"
for ob in sorted(louvers, key=lambda o: (round(o.location.x, 2), round(o.location.z, 2))):
    print(f"  louver {ob.name}: x={ob.location.x:.2f} y={ob.location.y:.3f} z={ob.location.z:.2f}")
    assert abs(ob.location.y - LOUVER_Y) < 0.01, f"{ob.name} y wrong: {ob.location.y}"
    assert ob.location.y > NORTH_Y, f"{ob.name} not on north face: y={ob.location.y}"
print(f"LOUVER CHECK PASS: 12/12 louvers at y={LOUVER_Y} (north of cabinet north face y={NORTH_Y})")

# 风扇罩抬高验证：风扇盘底面必须高出柜顶盖顶面 z=2.55（st-cabinet v2 顶盖 z=[2.45,2.55]）
TOPCAP_TOP_Z = 2.55
fan_discs = [ob for ob in imported if "FanDisc" in ob.name]  # 回读名带 .001 后缀，用子串匹配
print("fan disc count:", len(fan_discs))
assert len(fan_discs) == 4, f"expected 4 fan discs, got {len(fan_discs)}"
for ob in sorted(fan_discs, key=lambda o: round(o.location.x, 2)):
    bottom = ob.location.z - ob.dimensions.z / 2.0
    top = ob.location.z + ob.dimensions.z / 2.0
    print(f"  fan {ob.name}: disc z=[{bottom:.3f},{top:.3f}] (TopCap top={TOPCAP_TOP_Z})")
    assert bottom > TOPCAP_TOP_Z, f"{ob.name} disc bottom {bottom:.3f} not above TopCap top {TOPCAP_TOP_Z}"
print(f"FAN LIFT CHECK PASS: 4/4 fan discs above TopCap top (lift +{FAN_LIFT})")

# 底色保留验证（v3 贴图版）：回读后门板材质必须连着 door_color 贴图
# （贴图挂上后 Base Color 默认值是纯白，不再是 #35483F 的线性值）
door_mats = [m for m in bpy.data.materials if "Door" in m.name and m.use_nodes]
for m in door_mats:
    texs = [n for n in m.node_tree.nodes if n.type == "TEX_IMAGE"]
    names = [t.image.name if t.image else "?" for t in texs]
    print(f"reimported door material {m.name}: texture nodes={names}")
    assert any("door_color" in n for n in names), \
        f"door material {m.name} missing door_color texture: {names}"
print("BASE COLOR CHECK PASS: door material retains door_color texture link")

# 删掉回读的副本，恢复干净场景再存盘（否则 .blend 会多出 52 个重复对象）
bpy.ops.object.select_all(action='DESELECT')
for ob in imported:
    ob.select_set(True)
bpy.ops.object.delete()
print("reimported copies deleted, scene objects:", len(bpy.data.objects))

bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("DONE st-doors")
