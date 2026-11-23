# st-cabinet v2: 储能站柜体返工 (100kW/215kWh)
# 3 台电池柜 + 1 台 PCS 柜，沿 x 一字排开，Blender 中心 (64, 30)
# 单柜 1.3(x) x 1.0(y) x 2.3(z) m，柜间距 0.3 m，底座留高 0.15 m
# v2 改动（相对 v1 方块版）：
#   1. 柜体按真实结构做：侧板分缝 + 顶檐加厚(0.06->0.10) + 底座踢脚
#      + 前门门缝 + 散热格栅 + 把手
#   2. 材质：深绿灰金属漆面橘皮纹理 — Noise 细颗粒只连 Bump（法线），
#      Base Color / Roughness / Metallic 保持不链接（默认值=色板值），
#      否则 glTF 导出器丢 baseColorFactor、Godot 里变白（全管线已验证的教训）
#   3. 全部结构件倒角加大到看得见（主体 0.04、顶檐 0.03、踢脚 0.03），薄件除外
#   4. 数量/尺寸/位置按 SPEC §6 + data（100kW/215kWh 基准模块），与 v1 一致
# 交付：本脚本 + st-cabinet.blend + assets/models/st-cabinet.glb
# 新规矩：渲染全部走 GitHub Actions，本地不渲染、不出预览图
import bpy
import os

BLEND_PATH = "/home/hatch/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot/assets/blender/storage/st-cabinet.blend"
GLB_PATH = "/home/hatch/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot/assets/models/st-cabinet.glb"

# ---------- clean scene ----------
bpy.ops.wm.read_factory_settings(use_empty=True)


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_to_linear(h):
    h = h.lstrip("#")
    return tuple(srgb_to_linear(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4))


def make_paint_material(name, hex_color, roughness=0.5, metallic=0.2,
                        noise_scale=60.0, bump_strength=0.25):
    """金属漆面橘皮纹理：底色/粗糙度/金属度一律不链接（默认值），
    Noise 细颗粒只进 Bump -> BSDF Normal。"""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*hex_to_linear(hex_color), 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    # 橘皮：细颗粒 Noise -> Bump（只走法线，不碰 Base Color）
    tex = nt.nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = noise_scale
    tex.inputs["Detail"].default_value = 2.0
    tex.inputs["Roughness"].default_value = 0.7
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = bump_strength
    bump.inputs["Distance"].default_value = 0.02
    nt.links.new(tex.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def make_material(name, hex_color, roughness=0.5, metallic=0.2):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*hex_to_linear(hex_color), 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


CABINET_MAT = make_paint_material("Cabinet_GreenGray_Paint", "#3E5A50",
                                  0.5, 0.2, noise_scale=60.0, bump_strength=0.25)
CAP_MAT = make_paint_material("Cabinet_Cap_Paint", "#35483F",
                              0.55, 0.2, noise_scale=60.0, bump_strength=0.2)
KICK_MAT = make_material("Cabinet_Kick", "#2E3F38", 0.6, 0.15)
SEAM_MAT = make_material("Cabinet_Seam", "#26332E", 0.7, 0.1)
GRILLE_MAT = make_material("Cabinet_Grille", "#232D29", 0.65, 0.3)
HANDLE_MAT = make_material("Cabinet_Handle", "#C0C5C9", 0.35, 0.9)
SCREEN_MAT = make_material("Cabinet_Screen", "#14202E", 0.3, 0.4)
LED_MAT = make_material("Cabinet_LED", "#3FAE5A", 0.4, 0.0)

# ---------- PBR 贴图（2026-11-23 v3 返工：挂下载的 CC0 贴图，替代纯色） ----------
# 底色图已用 PIL 按 SPEC 色调过（assets/blender/tint_textures.py），直接连
# Base Color；rough/normal 用原图（Non-Color）。路径存 // 相对路径，随仓库推送。
# 柜体用 blue_metal_plate 三图；旧程序化 Bump 已断开 Normal，由 normal 图替代。
# 尺寸适配：柜体 UV 按实尺缩放（tile 约 2m）。顶檐/踢脚同口径（tile 约 2m）；
# 缝/格栅/把手/屏/灯保持纯色。
TEX_DIR = os.path.join(os.path.dirname(BLEND_PATH), "st-cabinet_textures")

def _load_tex(fname, colorspace):
    # 同一文件被多个材质复用时（cap/kick 复用 cabinet rough/nor）必须复用已载入
    # 的 image 数据块：bpy.data.images.load(check_existing=True) 只按传入路径串
    # 匹配，绝对路径与已存的 // 相对路径对不上，会造出 .001/.002 重复块，GLB 里
    # 同一张图嵌三份。先按 basename 找已载入的。
    for img in bpy.data.images:
        if img.filepath and os.path.basename(img.filepath) == fname:
            img.colorspace_settings.name = colorspace
            return img
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

# v3: 柜体挂真实 PBR 贴图（blue_metal_plate 染 #3E5A50）
add_pbr(CABINET_MAT, "cabinet_color.jpg", "cabinet_rough.jpg", "cabinet_nor.jpg")
_check_pbr(CABINET_MAT)
# v3b (2026-11-24): 顶檐/踢脚挂真实 PBR 贴图（blue_metal_plate 染 #35483F/#2E3F38，
# 复用 cabinet rough/nor；三件套节点直连 BSDF）。缝/格栅/把手/屏/灯保持纯色。
add_pbr(CAP_MAT, "cap_color.jpg", "cabinet_rough.jpg", "cabinet_nor.jpg")
_check_pbr(CAP_MAT)
add_pbr(KICK_MAT, "kick_color.jpg", "cabinet_rough.jpg", "cabinet_nor.jpg")
_check_pbr(KICK_MAT)


def add_box(name, loc, dims, mat, bevel=None, bevel_segments=2, uv_scale=None):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if mat is not None:
        ob.data.materials.append(mat)
    if uv_scale is not None:
        scale_uvs(ob, uv_scale[0], uv_scale[1])
    if bevel:
        bev = ob.modifiers.new("EdgeBevel", 'BEVEL')
        bev.width = bevel
        bev.segments = bevel_segments
        bev.limit_method = 'ANGLE'
    return ob


# ---------- cabinets ----------
# 总宽 4*1.3 + 3*0.3 = 6.1 m，中心 x=64 -> 首柜中心 x=61.6
CAB_W, CAB_D, CAB_H = 1.3, 1.0, 2.3
GAP = 0.3
BASE_Z = 0.15            # 底座留高（基座是 st-base 的活）
CY = 30.0
x0 = 64.0 - (4 * CAB_W + 3 * GAP) / 2.0 + CAB_W / 2.0
FRONT_Y = CY - CAB_D / 2.0   # 前门朝南（y- 侧）

cabinet_objs = []
for i in range(4):
    cx = x0 + i * (CAB_W + GAP)
    is_pcs = (i == 3)
    name = "PCS_Cabinet" if is_pcs else f"Battery_Cabinet_{i + 1}"

    # ① 柜体主体：倒角 0.02 -> 0.04（看得见），3 段
    body = add_box(name, (cx, CY, BASE_Z + CAB_H / 2.0),
                   (CAB_W, CAB_D, CAB_H), CABINET_MAT,
                   bevel=0.04, bevel_segments=3,
                   uv_scale=(CAB_W / 2.0, CAB_H / 2.0))
    cabinet_objs.append(body)

    # ② 顶檐加厚：0.06 -> 0.10 m，每边伸出 0.06 m，倒角 0.03
    cap = add_box(name + "_TopCap",
                  (cx, CY, BASE_Z + CAB_H + 0.05),
                  (CAB_W + 0.12, CAB_D + 0.12, 0.10), CAP_MAT,
                  bevel=0.03, bevel_segments=2,
                  uv_scale=((CAB_W + 0.12) / 2.0, (CAB_D + 0.12) / 2.0))
    cabinet_objs.append(cap)

    # ③ 底座踢脚：内收 0.04 m 的底座，高 0.15 m（与留高齐平），倒角 0.03
    kick = add_box(name + "_Kick",
                   (cx, CY, BASE_Z / 2.0),
                   (CAB_W - 0.08, CAB_D - 0.08, BASE_Z), KICK_MAT,
                   bevel=0.03, bevel_segments=2,
                   uv_scale=((CAB_W - 0.08) / 2.0, (CAB_D - 0.08) / 2.0))
    cabinet_objs.append(kick)

    # ④ 侧板分缝：左右侧面各一条竖缝 + 一条横缝（薄暗条，微凸 0.004）
    for sx in (-1, 1):
        seam_v = add_box(name + ("_SideSeam_L" if sx < 0 else "_SideSeam_R"),
                         (cx + sx * (CAB_W / 2.0 + 0.002), CY,
                          BASE_Z + CAB_H / 2.0),
                         (0.004, 0.02, 1.90), SEAM_MAT)
        cabinet_objs.append(seam_v)
        seam_h = add_box(name + ("_SideSeamH_L" if sx < 0 else "_SideSeamH_R"),
                         (cx + sx * (CAB_W / 2.0 + 0.002), CY,
                          BASE_Z + 1.30),
                         (0.004, 0.90, 0.02), SEAM_MAT)
        cabinet_objs.append(seam_h)

    # ⑤ 前门门缝：中央竖缝（双开门中缝）+ 顶部横缝，薄暗条微凸
    door_v = add_box(name + "_DoorSeam_V",
                     (cx, FRONT_Y - 0.004, BASE_Z + 1.05),
                     (0.025, 0.008, 1.80), SEAM_MAT)
    cabinet_objs.append(door_v)
    door_h = add_box(name + "_DoorSeam_H",
                     (cx, FRONT_Y - 0.004, BASE_Z + 2.00),
                     (1.10, 0.008, 0.025), SEAM_MAT)
    cabinet_objs.append(door_h)

    # ⑥ 散热格栅：前门上部暗色底板 + 横向百叶条
    grille_back = add_box(name + "_GrilleBack",
                          (cx, FRONT_Y - 0.003, BASE_Z + 1.78),
                          (1.00, 0.006, 0.42), GRILLE_MAT)
    cabinet_objs.append(grille_back)
    n_slats = 5 if is_pcs else 8
    slat_h = 0.34 if is_pcs else 0.36
    z_top = BASE_Z + 1.78 + slat_h / 2.0
    for s in range(n_slats):
        z = z_top - 0.025 - s * (slat_h / max(n_slats - 1, 1) if n_slats > 1 else 0)
        # 百叶条：薄件，不倒角
        slat = add_box(name + f"_GrilleSlat_{s + 1}",
                       (cx, FRONT_Y - 0.008, z),
                       (0.92, 0.012, 0.028), GRILLE_MAT)
        cabinet_objs.append(slat)

    # ⑦ 把手：右门扇竖向拉手（金属条 + 上下两个固定座），薄件不倒角
    hx = cx + 0.28
    for mz, tag in ((1.28, "Top"), (1.02, "Bottom")):
        mount = add_box(name + f"_HandleMount_{tag}",
                        (hx, FRONT_Y - 0.012, BASE_Z + mz),
                        (0.05, 0.024, 0.05), HANDLE_MAT)
        cabinet_objs.append(mount)
    handle = add_box(name + "_Handle",
                     (hx, FRONT_Y - 0.032, BASE_Z + 1.15),
                     (0.04, 0.04, 0.30), HANDLE_MAT)
    cabinet_objs.append(handle)

    # PCS 柜额外：前门小显示屏 + 运行指示灯（与电池柜区分）
    if is_pcs:
        screen = add_box(name + "_Screen",
                         (cx - 0.30, FRONT_Y - 0.006, BASE_Z + 1.15),
                         (0.34, 0.012, 0.24), SCREEN_MAT)
        cabinet_objs.append(screen)
        led = add_box(name + "_LED",
                      (cx - 0.30, FRONT_Y - 0.010, BASE_Z + 0.88),
                      (0.20, 0.012, 0.03), LED_MAT)
        cabinet_objs.append(led)

print("cabinet objects:", len(cabinet_objs))

# ---------- save .blend ----------
os.makedirs(os.path.dirname(BLEND_PATH), exist_ok=True)
os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)

# ---------- export .glb (只选本件对象) ----------
bpy.ops.object.select_all(action='DESELECT')
for ob in cabinet_objs:
    ob.select_set(True)
bpy.context.view_layer.objects.active = cabinet_objs[0]
bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format='GLB',
                           use_selection=True, export_apply=True)

# ---------- 回读验证 glb ----------
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB_PATH)
imported = [ob for ob in bpy.data.objects if ob not in before]
print("GLB reimport objects:", len(imported),
      [ob.name for ob in imported])
assert len(imported) == len(cabinet_objs), \
    "glb reimport mismatch: %d vs %d" % (len(imported), len(cabinet_objs))
# 删掉回读的副本，恢复干净场景再存盘
bpy.ops.object.select_all(action='DESELECT')
for ob in imported:
    ob.select_set(True)
bpy.ops.object.delete()
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("DONE st-cabinet")
