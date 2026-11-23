# pv-inverter v2: 逆变器与线缆返工 (A栋屋顶 2 台 + 实验楼屋顶 1 台)
# 只做逆变器和线缆: 不做板(pv-panels)/支架(pv-mount)/屋顶面层(pv-roof)
# 规约: SPEC.md; 单位米; Blender x东 y北 z上
# v2 返工点(筛查结论):
#   ① 3 台做齐; ② 箱体按真实结构: 散热格栅(南面百叶+东西侧鳍片)+把手
#   (顶把+两侧提手)+接线端子(南北两端子盒+线鼻+铜排)+显示屏/指示灯
#   +底座/支架(钢轨+底座+地脚螺栓); ③ 线槽全程: 北向到女儿墙(已有)
#   + 南向到板阵列(新增, 带盖板分缝); ④ 材质分开: 白色金属箱体(拉丝
#   Bump)、深色散热格栅、灰色线槽; ⑤ 所有面不许全平(门缝、螺钉、盖板缝)。
# 材质铁律(全管线已验证): 程序化 Noise 不进 glTF, Base Color 连 MixRGB/
#   ValToRGB 会丢 baseColorFactor。所以底色/粗糙度保持不链接(默认值=色板
#   值), 纹理变化只走 Bump(法线)。GLB 里 baseColorFactor 保留, .blend 里纹理也在。
# 位置(已核对修正, 不用 brief 原给的 (-56,38), 它在屋顶之外 0.5m 且压板):
#   A栋屋顶: x -76..-36, y 22.5..37.5, 屋顶基准 z=18.35 (pv-roof 板顶面)
#     (-74.75,36.40) 与 (-37.25,36.40), 北侧两角, 在屋顶内
#     (2026-11-23 穿插修正: 原 (-75.0,36.6)/(-37.0,36.6) 箱体西/东缘埋进
#      东西女儿墙, 北端子盒/防水接头埋进北女儿墙; 本次 A1 向东 +0.25、
#      A2 向西 -0.25, 两台再向南 -0.20, 箱体外缘离墙内面 >=0.05m)
#   实验楼屋顶: x -49..-7, y 56..68, 屋顶基准 z=12.30
#     (-28,67.20), 板北缘(约 y=66.90)以北、屋顶内
#     (2026-11-23: 原 (-28,67.3) 北端防水接头擦北墙内面 y=67.70, 本次向南 -0.10)
# 基准修正 (2026-11-22 PV 修复, 按 pv-roof 为准): datum 19/13 -> 18.35/12.30
# (A/B 下调 0.65m, 实验楼下调 0.70m), 箱体/线槽整体随 datum 下调。
# 线槽北向段: 逆变器北面 -> 翻越女儿墙压顶 -> 沿北缘横向 -> 女儿墙外侧
#   竖直上行到墙顶上方 0.35m 即止。
#   女儿墙顶 = 板顶面 +0.65m (A/B 19.00, 实验楼 12.95, 见 pv-roof),
#   压顶顶 = A/B 19.00、实验楼 13.00; 线槽顶端 = 女儿墙顶 +0.35m
#   = datum+1.00m (A/B 19.35, 实验楼 13.30)。
#   旧版按“女儿墙顶约屋顶+1m”假定、顶端高出女儿墙约 1.0m, 已修正。
# 穿插修正 (2026-11-23 pv 拼装顶点级检查): 旧版北向段在屋顶高度平穿女儿墙
#   (A 4 顶点 y=36.91、实验楼 4 顶点 y=67.84 在墙内); 本次北向段改走压顶
#   顶面之上 (立管+平桥+落水管, 桥底 = 压顶顶 +0.04m), 横向段/竖管/顶端
#   走向与高度不变。另查: 实验楼原横向段 run_y=67.85 正压在北墙中心线上,
#   整段埋进北墙 (104 顶点), 必须随桥外移到 run_y=68.20 (压顶外挑 68.06
#   之外); A 横向段原 run_y=37.35 已在压顶外挑 37.26 之外, 不动。
#   整机抬升 LIFT=0.055 (轨底 = 膜顶 +0.005, 轨/座/箱体相对关系不变),
#   线槽抬升 TRUNK_LIFT=0.055 (槽底 = 膜顶 +0.005), 竖管改短 0.05 保顶端 19.35/13.30。
#   对象数 291 -> 297 (每台北向段由 2 件改 4 件: 立管/平桥/桥盖/落水管),
#   拼装 pv.py 的 EXPECTED 需同步改 291 -> 297 (总协调改, 不属本件)。
# 线槽南向段(新增): 逆变器南面端子盒 -> 沿屋顶向南到板阵列北缘, 末端接线盒。
#   A1/A2 线槽走板阵列西/东侧空隙(x=-75/-37, 板西缘 -74.70/东缘 -37.30);
#   LAB 线槽沿 x=-28 向南, 从北行板下穿过(槽顶 z=屋顶+0.08, 板南缘底约
#   屋顶+0.17, 有约 0.09m 空隙)。
# 本次不渲染(新规矩: 渲染全部走 GitHub Actions, 本地不渲染、不出预览图)。
import bpy
import math
import os

BASE = os.path.expanduser("~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
BLEND = os.path.join(BASE, "assets/blender/pv/pv-inverter.blend")
GLB = os.path.join(BASE, "assets/models/pv-inverter.glb")

LIFT = 0.055        # 整机抬升: 轨底原 z=板顶 (A/B 18.35 / 实验楼 12.30), 陷进膜面
                    # 0.05m; 抬后轨底 = 膜顶 (18.40/12.35) +0.005
TRUNK_LIFT = 0.055   # 线槽抬升: 槽底原 z=板顶, 陷进膜面 0.05m; 抬后槽底 = 膜顶 +0.005
                    # (取 0.055 而非 0.05: 槽底恰贴膜顶时 float32 舍入会把个别
                    # 顶点算到膜面之下, 5mm 余量避开边界)

# ---- 清场 ----
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for m in list(bpy.data.meshes):
    bpy.data.meshes.remove(m)

# ---- 材质 (只用 Principled BSDF; sRGB 十六进制先转线性再赋值) ----
def srgb(hexstr):
    h = hexstr.lstrip('#')
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i+2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return tuple(out)

def principled(name, rgb, metallic, roughness, emission=None,
               emission_strength=0.0, bump_scale=None, bump_strength=0.0):
    """底色/粗糙度/金属度只设默认值(不链接任何节点); 纹理变化只走 Bump。
    bump_scale: Noise 纹理 Scale; bump_strength: Bump 强度。"""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission is not None:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    if bump_scale is not None:
        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = bump_scale
        noise.inputs["Detail"].default_value = 2.0
        noise.inputs["Roughness"].default_value = 0.7
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = bump_strength
        bump.inputs["Distance"].default_value = 0.02
        nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat

# ---------- PBR 贴图（2026-11-23 v3 返工：挂下载的 CC0 贴图，替代纯色） ----------
# 底色图已用 PIL 按 SPEC 色调过（assets/blender/tint_textures.py），直接连
# Base Color；rough/normal 用原图（Non-Color）。路径存 // 相对路径，随仓库推送。
# 箱体用 white_stucco 三图；旧拉丝 Bump 已断开 Normal，由 normal 图替代。
# 尺寸适配：箱体 UV 按实尺缩放（tile 约 2m）。
TEX_DIR = os.path.join(BASE, "assets/blender/pv/pv-inverter_textures")

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

# 白色金属箱体: 拉丝纹理只走 Bump(细噪波, 弱强度)
MAT_BODY = principled("INV_BodyWhite", srgb("EDEEF0"), 0.55, 0.38,
                      bump_scale=80.0, bump_strength=0.25)
# v3: 挂真实 PBR 贴图（white_stucco 染 #EDEEF0）
add_pbr(MAT_BODY, "body_color.jpg", "body_rough.jpg", "body_nor.jpg")
_check_pbr(MAT_BODY)
# 深色散热格栅/鳍片
MAT_GRILLE = principled("INV_GrilleDark", srgb("2E3438"), 0.6, 0.50,
                        bump_scale=30.0, bump_strength=0.15)
# 线槽灰色(盖板分缝处用深一档)
MAT_TRUNK = principled("INV_TrunkGrey", srgb("8A8F94"), 0.5, 0.60,
                       bump_scale=25.0, bump_strength=0.10)
MAT_SEAM = principled("INV_SeamDark", srgb("6B7280"), 0.5, 0.65)
# 底座/支架深灰
MAT_BASE = principled("INV_BaseDark", srgb("424A52"), 0.2, 0.80)
# 显示屏深色 + 指示灯(绿运行/琥珀待机/红故障, 带自发光)
MAT_SCREEN = principled("INV_Screen", srgb("1F2A33"), 0.1, 0.20)
MAT_LED_G = principled("INV_LedGreen", srgb("46A04E"), 0.0, 0.40,
                       emission=srgb("46A04E"), emission_strength=1.5)
MAT_LED_A = principled("INV_LedAmber", srgb("E8B400"), 0.0, 0.40,
                       emission=srgb("E8B400"), emission_strength=1.0)
MAT_LED_R = principled("INV_LedRed", srgb("B8543F"), 0.0, 0.40,
                       emission=srgb("B8543F"), emission_strength=0.8)
# 接线端子铜排 + 电缆黑
MAT_COPPER = principled("INV_Copper", srgb("B87333"), 0.9, 0.30)
MAT_CABLE = principled("INV_CableBlack", srgb("1F2224"), 0.0, 0.70)

part_objs = []  # 本件对象(导出用)

def add_box(name, loc, dims, mat, bevel=0.0, uv_scale=None):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.active_object
    o.name = name
    o.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if mat is not None:
        o.data.materials.append(mat)
    if uv_scale is not None:
        scale_uvs(o, uv_scale[0], uv_scale[1])
    if bevel > 0:
        mod = o.modifiers.new("Bevel", 'BEVEL')
        mod.width = bevel
        mod.segments = 2
    part_objs.append(o)
    return o

def add_cyl(name, loc, radius, depth, mat, rot_x=0.0):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth,
                                        location=loc, vertices=16)
    o = bpy.context.active_object
    o.name = name
    o.rotation_euler = (rot_x, 0.0, 0.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if mat is not None:
        o.data.materials.append(mat)
    part_objs.append(o)
    return o

# ---- 逆变器: 单台 1.0(x) x 0.6(y) x 1.4(z) 米, 南面(-y)为操作面 ----
def make_inverter(tag, cx, cy, roof_z):
    # 整机抬升 LIFT (见文件头): 轨底 = 膜顶 +0.005。函数内 roof_z 一律取抬升后
    # 的值, 轨/座/箱体/端子相对关系不变; 线槽函数另用 TRUNK_LIFT, 不受此影响。
    roof_z = roof_z + LIFT
    # --- 底座/支架: 2 条钢轨 + 底座 + 4 颗地脚螺栓 ---
    for ry in (-0.25, 0.25):
        add_box(f"INV_{tag}_Rail_{'S' if ry < 0 else 'N'}",
                (cx, cy + ry, roof_z + 0.03), (1.10, 0.08, 0.06), MAT_BASE)
    add_box(f"INV_{tag}_Base", (cx, cy, roof_z + 0.12),
            (1.10, 0.70, 0.12), MAT_BASE)
    for sx in (-0.48, 0.48):
        for sy in (-0.28, 0.28):
            add_cyl(f"INV_{tag}_Bolt_{'W' if sx < 0 else 'E'}{'S' if sy < 0 else 'N'}",
                    (cx + sx, cy + sy, roof_z + 0.20), 0.02, 0.05, MAT_GRILLE)
    # --- 箱体: 白色金属, 小倒角; 顶盖 + 压边 + 4 颗盖螺钉 ---
    body_z = roof_z + 0.18 + 0.70
    add_box(f"INV_{tag}_Body", (cx, cy, body_z),
            (1.00, 0.60, 1.40), MAT_BODY, bevel=0.02, uv_scale=(0.5, 0.7))
    add_box(f"INV_{tag}_CapRim", (cx, cy, roof_z + 0.18 + 1.40 + 0.015),
            (1.06, 0.66, 0.03), MAT_GRILLE)
    add_box(f"INV_{tag}_Cap", (cx, cy, roof_z + 0.18 + 1.40 + 0.06),
            (1.04, 0.64, 0.06), MAT_BODY, uv_scale=(0.52, 0.32))
    for sx in (-0.46, 0.46):
        for sy in (-0.26, 0.26):
            add_cyl(f"INV_{tag}_CapScrew_{'W' if sx < 0 else 'E'}{'S' if sy < 0 else 'N'}",
                    (cx + sx, cy + sy, roof_z + 0.18 + 1.40 + 0.095),
                    0.015, 0.02, MAT_GRILLE)
    # --- 箱门缝: 南面门框四边细缝(深色细条, 微凸出箱面, 门不再全平) ---
    door_y = cy - 0.305
    add_box(f"INV_{tag}_DoorTop", (cx, door_y, body_z + 0.60), (0.92, 0.012, 0.02), MAT_SEAM)
    add_box(f"INV_{tag}_DoorBottom", (cx, door_y, body_z - 0.60), (0.92, 0.012, 0.02), MAT_SEAM)
    add_box(f"INV_{tag}_DoorLeft", (cx - 0.46, door_y, body_z), (0.02, 0.012, 1.20), MAT_SEAM)
    add_box(f"INV_{tag}_DoorRight", (cx + 0.46, door_y, body_z), (0.02, 0.012, 1.20), MAT_SEAM)
    # --- 散热格栅: 南面下半部百叶(深色背板 + 8 条横向百叶) ---
    add_box(f"INV_{tag}_GrilleBack", (cx, cy - 0.308, body_z - 0.28),
            (0.76, 0.015, 0.72), MAT_GRILLE)
    for i in range(8):
        gz = body_z - 0.56 + i * 0.08
        add_box(f"INV_{tag}_Louver{i}",
                (cx, cy - 0.318, gz), (0.70, 0.025, 0.045), MAT_GRILLE)
    # --- 散热鳍片: 东西两侧面各 6 条竖条 ---
    for side in (-1, 1):
        for i, fy in enumerate((-0.20, -0.12, -0.04, 0.04, 0.12, 0.20)):
            add_box(f"INV_{tag}_Fin_{'W' if side < 0 else 'E'}{i}",
                    (cx + side * 0.515, cy + fy, body_z),
                    (0.03, 0.05, 1.05), MAT_GRILLE)
    # --- 把手: 顶把(两立柱+横杆) + 东西两侧 U 形提手 ---
    for hx in (-0.20, 0.20):
        add_box(f"INV_{tag}_HandlePost_{'W' if hx < 0 else 'E'}",
                (cx + hx, cy, roof_z + 0.18 + 1.40 + 0.12),
                (0.04, 0.04, 0.06), MAT_GRILLE)
    add_box(f"INV_{tag}_HandleBar", (cx, cy, roof_z + 0.18 + 1.40 + 0.17),
            (0.44, 0.05, 0.04), MAT_GRILLE)
    for side in (-1, 1):
        s = 'W' if side < 0 else 'E'
        for dy in (-0.15, 0.15):
            add_box(f"INV_{tag}_GripStub_{s}{'S' if dy < 0 else 'N'}",
                    (cx + side * 0.52, cy + dy, body_z + 0.30),
                    (0.03, 0.04, 0.04), MAT_GRILLE)
        add_box(f"INV_{tag}_GripBar_{s}",
                (cx + side * 0.545, cy, body_z + 0.30),
                (0.03, 0.34, 0.04), MAT_GRILLE)
    # --- 显示屏 + 指示灯(绿/琥珀/红) + 操作按钮: 南面上半部 ---
    add_box(f"INV_{tag}_Screen", (cx, cy - 0.31, body_z + 0.42),
            (0.34, 0.02, 0.24), MAT_SCREEN)
    add_box(f"INV_{tag}_LedG", (cx - 0.14, cy - 0.31, body_z + 0.22),
            (0.05, 0.02, 0.05), MAT_LED_G)
    add_box(f"INV_{tag}_LedA", (cx - 0.05, cy - 0.31, body_z + 0.22),
            (0.05, 0.02, 0.05), MAT_LED_A)
    add_box(f"INV_{tag}_LedR", (cx + 0.04, cy - 0.31, body_z + 0.22),
            (0.05, 0.02, 0.05), MAT_LED_R)
    add_box(f"INV_{tag}_Button", (cx + 0.16, cy - 0.31, body_z + 0.22),
            (0.06, 0.02, 0.06), MAT_GRILLE)
    # --- 接线端子: 南面底部端子盒(DC 输入) + 3 个线鼻 + 铜排 + 黑电缆短头 ---
    #   电缆加长到 0.28m: 整机抬升后仍要够到抬升后的南向线槽 (槽顶 = 板顶+0.13)。
    add_box(f"INV_{tag}_TermBoxS", (cx, cy - 0.32, roof_z + 0.35),
            (0.50, 0.08, 0.16), MAT_BASE)
    for i, tx in enumerate((-0.15, 0.0, 0.15)):
        add_box(f"INV_{tag}_CopperS{i}", (cx + tx, cy - 0.32, roof_z + 0.28),
                (0.06, 0.02, 0.05), MAT_COPPER)
        add_cyl(f"INV_{tag}_CableS{i}", (cx + tx, cy - 0.32, roof_z + 0.16),
                0.02, 0.28, MAT_CABLE)
    # --- 接线端子: 北面底部端子盒(AC 输出, 接北向线槽) + 线鼻 ---
    add_box(f"INV_{tag}_TermBoxN", (cx, cy + 0.32, roof_z + 0.35),
            (0.50, 0.08, 0.16), MAT_BASE)
    for i, tx in enumerate((-0.15, 0.0, 0.15)):
        add_box(f"INV_{tag}_CopperN{i}", (cx + tx, cy + 0.32, roof_z + 0.28),
                (0.06, 0.02, 0.05), MAT_COPPER)
        add_cyl(f"INV_{tag}_GlandN{i}", (cx + tx, cy + 0.36, roof_z + 0.22),
                0.035, 0.08, MAT_BASE, rot_x=math.pi / 2)
    return (cx, cy, roof_z)

# ---- 线槽: 分段槽体 + 盖板 + 盖板分缝(缝处深色窄条), 每段 0.5m 级 ----
def trunk_run_x(tag, cx, run_y, roof_z, dir_x, length=2.0, seg=0.5, w=0.15, h=0.08):
    """沿 x 向的水平线槽: 从 cx 起向 dir_x 方向走 length 米。
    槽底 = 膜顶 (TRUNK_LIFT, 原 z=板顶陷进膜面 0.05m)。"""
    tz = roof_z + TRUNK_LIFT
    n = max(1, int(round(length / seg)))
    seg_len = length / n
    for i in range(n):
        x0 = cx + dir_x * (i * seg_len)
        x1 = cx + dir_x * ((i + 1) * seg_len)
        mx = (x0 + x1) / 2
        add_box(f"INV_{tag}_TrunkX{i}", (mx, run_y, tz + 0.04),
                (seg_len - 0.02, w, h), MAT_TRUNK)
        add_box(f"INV_{tag}_TrunkLidX{i}", (mx, run_y, tz + 0.085),
                (seg_len - 0.02, w + 0.02, 0.015), MAT_TRUNK)
        if i > 0:
            add_box(f"INV_{tag}_TrunkSeamX{i}", (x0, run_y, tz + 0.085),
                    (0.02, w, 0.02), MAT_SEAM)  # 缝宽取槽宽 (旧 w+0.04 会南伸
                    # 0.02m、擦北压顶外挑 37.26, 复查计 24 顶点; 改后与槽面齐平)
    return cx + dir_x * length

def trunk_run_y(tag, cy0, cy1, cx, roof_z, w=0.18, h=0.08, seg=0.4):
    """沿 y 向的水平线槽: 从 cy0 走到 cy1(向南 cy1<cy0)。
    槽底 = 膜顶 (TRUNK_LIFT, 原 z=板顶陷进膜面 0.05m)。"""
    tz = roof_z + TRUNK_LIFT
    length = abs(cy1 - cy0)
    n = max(1, int(round(length / seg)))
    seg_len = length / n
    step = -1 if cy1 < cy0 else 1
    for i in range(n):
        y0 = cy0 + step * i * seg_len
        y1 = cy0 + step * (i + 1) * seg_len
        my = (y0 + y1) / 2
        add_box(f"INV_{tag}_TrunkY{i}", (cx, my, tz + 0.04),
                (w, seg_len - 0.02, h), MAT_TRUNK)
        add_box(f"INV_{tag}_TrunkLidY{i}", (cx, my, tz + 0.085),
                (w + 0.02, seg_len - 0.02, 0.015), MAT_TRUNK)
        if i > 0:
            add_box(f"INV_{tag}_TrunkSeamY{i}", (cx, y0, tz + 0.085),
                    (w + 0.04, 0.02, 0.02), MAT_SEAM)
    return cy1

def make_trunk_north(tag, cx, cy, roof_z, run_y, dir_x, cap_top):
    """北向线槽: 逆变器北面 -> 翻越女儿墙压顶 -> 沿北缘横向 2.0m -> 女儿墙
    外侧竖直上行, 顶端 = 女儿墙顶 +0.35m = roof_z+1.00m (A/B 19.35, 实验楼
    13.30, 顶端高度不动)。
    2026-11-23 穿插修正: 旧版北向段在屋顶高度平穿女儿墙。本次改走压顶顶面
    之上: 立管在逆变器北面 (y0=cy+0.30, 墙内侧) 升到桥面、平桥越过压顶
    (桥底 = 压顶顶 +0.04m)、北侧落水管接回横向段。横向段/竖管/顶端走向与
    高度不变, 只随逆变器 cx 平移 (LAB run_y 外移见调用处注释)。
    run_y: 横向段 y; cap_top: 压顶顶面 z (A/B 19.00, 实验楼 13.00)。"""
    tz = roof_z + TRUNK_LIFT
    y0 = cy + 0.30
    bridge_z = cap_top + 0.08   # 桥面中心: 桥底 = 压顶顶 +0.04
    bridge_top = bridge_z + 0.04
    memb_top = roof_z + TRUNK_LIFT  # 立管底 = 膜顶 +0.005 (同线槽底)
    # 立管: 逆变器北面从膜顶升到桥顶 (贴北端子盒前方上行, 与端子盒相接)
    add_box(f"INV_{tag}_TrunkRiser", (cx, y0, (memb_top + bridge_top) / 2),
            (0.15, 0.08, bridge_top - memb_top), MAT_TRUNK)
    # 平桥: 越过压顶顶面 (桥底高出压顶 0.04m, 全程不碰墙)
    add_box(f"INV_{tag}_TrunkBridge", (cx, (y0 + run_y) / 2, bridge_z),
            (0.15, run_y - y0, 0.08), MAT_TRUNK)
    add_box(f"INV_{tag}_TrunkLidBridge", (cx, (y0 + run_y) / 2, bridge_z + 0.0475),
            (0.17, run_y - y0, 0.015), MAT_TRUNK)
    # 落水管: 桥北端 (run_y, 墙外) 落回横向段高度
    add_box(f"INV_{tag}_TrunkDrop", (cx, run_y, (roof_z + bridge_top) / 2),
            (0.15, 0.08, bridge_top - roof_z), MAT_TRUNK)
    # 横向段沿北缘走 2.0m
    end_x = trunk_run_x(tag + "N", cx, run_y, roof_z, dir_x, length=2.0)
    # 弯头 x2: 北向转横向、横向转竖直
    add_box(f"INV_{tag}_Elbow1", (cx, run_y, tz + 0.04),
            (0.15, 0.15, 0.08), MAT_TRUNK)
    add_box(f"INV_{tag}_Elbow2", (end_x, run_y, tz + 0.04),
            (0.15, 0.15, 0.08), MAT_TRUNK)
    # 竖直线槽: 沿女儿墙外侧上行, 顶端 = 女儿墙顶 +0.35m = roof_z+1.00m。
    #   槽体改短 0.05 (roof_z+0.055 -> roof_z+0.95): 底抬到膜顶+0.005、顶端不动。
    add_box(f"INV_{tag}_TrunkV", (end_x, run_y + 0.075, roof_z + 0.5025),
            (0.15, 0.06, 0.895), MAT_TRUNK)
    add_box(f"INV_{tag}_TrunkTop", (end_x, run_y + 0.075, roof_z + 0.975),
            (0.18, 0.10, 0.05), MAT_TRUNK)

def make_trunk_south(tag, cx, cy, roof_z):
    """南向线槽: 逆变器南面端子盒 -> 沿屋顶向南 1.2m 到板阵列北缘, 末端接线盒。
    槽底 = 膜顶 (TRUNK_LIFT)。"""
    tz = roof_z + TRUNK_LIFT
    y0 = cy - 0.30
    y1 = cy - 1.50
    add_box(f"INV_{tag}_ElbowS", (cx, y0, tz + 0.06),
            (0.18, 0.12, 0.08), MAT_TRUNK)
    trunk_run_y(tag + "S", y0, y1, cx, roof_z, w=0.18, seg=0.4)
    add_box(f"INV_{tag}_JunctionBox", (cx, y1, tz + 0.06),
            (0.30, 0.25, 0.12), MAT_BASE)
    add_box(f"INV_{tag}_JunctionLid", (cx, y1, tz + 0.125),
            (0.32, 0.27, 0.015), MAT_TRUNK)
    for sx in (-0.11, 0.11):
        add_cyl(f"INV_{tag}_JunctionScrew_{'W' if sx < 0 else 'E'}",
                (cx + sx, y1, tz + 0.135), 0.012, 0.015, MAT_GRILLE)

# A栋屋顶北侧两角 (屋顶基准 z=18.35, 北缘 y=37.5; 压顶顶 19.00, 外挑至 y=37.26)
make_inverter("A1", -74.75, 36.40, 18.35)
make_trunk_north("A1", -74.75, 36.40, 18.35, 37.35, +1, 19.00)  # 横向段向东
make_trunk_south("A1", -74.75, 36.40, 18.35)
make_inverter("A2", -37.25, 36.40, 18.35)
make_trunk_north("A2", -37.25, 36.40, 18.35, 37.35, -1, 19.00)  # 横向段向西(朝屋顶中部)
make_trunk_south("A2", -37.25, 36.40, 18.35)
# 实验楼屋顶北侧 (屋顶基准 z=12.30, 北缘 y=68; 压顶顶 13.00, 外挑至 y=68.06)
# LAB 横向段 run_y=68.20: 原 67.85 正压北墙中心线, 整段埋进北墙, 必须外移。
make_inverter("LAB", -28.0, 67.20, 12.30)
make_trunk_north("LAB", -28.0, 67.20, 12.30, 68.20, +1, 13.00)  # 横向段向东
make_trunk_south("LAB", -28.0, 67.20, 12.30)

print(f"INVERTERS: 3 units, {len(part_objs)} part objects")

# ---- 存 .blend (先落盘) ----
for o in part_objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = part_objs[0]
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print(f"BLEND saved: {BLEND}")

# ---- 导出 GLB (只选本件对象) ----
bpy.ops.export_scene.gltf(
    filepath=GLB, export_format='GLB',
    use_selection=True, export_apply=True)
print(f"GLB exported: {GLB}")

# ---- 回读 GLB 验证: 对象数 + 3 台逆变器箱体坐标 ----
before = set(bpy.data.objects.keys())
bpy.ops.import_scene.gltf(filepath=GLB)
imported = [o for o in bpy.data.objects if o.name not in before]
print(f"GLB reimport OK: {len(imported)} objects")
# 注意: 原对象仍在场景中, 回读的同名对象会被加 ".001" 后缀, 故按前缀匹配
import re
bodies = sorted([o for o in imported
                 if re.match(r"^INV_(A1|A2|LAB)_Body(\.\d+)?$", o.name)],
                key=lambda o: o.name)
print(f"GLB reimport bodies: {len(bodies)}")
for o in bodies:
    print(f"  {o.name}: ({o.location.x:.2f}, {o.location.y:.2f}, {o.location.z:.2f})")
expected = {"INV_A1_Body": (-74.75, 36.40, 19.285),
            "INV_A2_Body": (-37.25, 36.40, 19.285),
            "INV_LAB_Body": (-28.0, 67.20, 13.235)}
assert len(bodies) == 3, "expected 3 inverter bodies in GLB!"
for o in bodies:
    ex = expected[o.name.split(".")[0]]
    assert abs(o.location.x - ex[0]) < 0.01 and abs(o.location.y - ex[1]) < 0.01 \
        and abs(o.location.z - ex[2]) < 0.01, f"body position mismatch: {o.name}"

print("DONE pv-inverter")
