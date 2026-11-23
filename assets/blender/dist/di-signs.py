# di-signs: 配电房标识牌 (墙面警示牌 2 块 + 柜门编号牌 6 块)
# 局部坐标: 房中心原点, x=长 16m (-8~+8), y=宽 10m (-5~+5), z 0~8m
# 墙面牌: 北墙 y=+5 内侧 "高压危险" 0.6x0.4m 红底白字框黄边, 中心 (0, 4.79, 2.4)
#         东墙 x=+8 内侧 "禁止合闸 有人工作" 0.6x0.4m 白底红字框, 中心 (7.79, 0, 2.4)
#         (2026-11-22 修复: di-walls 墙内表面实际在 y=4.8/x=7.8, 原 4.97/7.97 整组埋墙,
#          现整组向室内平移 0.18m, 牌背恰贴内表面, 不埋墙不飘离)
# 编号牌: 6 台配电柜门上各 1 块 0.2x0.12m 蓝底白框, 对齐 di-cabinets 柜子
#         中心 x=-6/-3.6/-1.2/+1.2/+3.6/+6, 贴柜门南面 y~4.08, z=1.35
#         (柜门面 y=4.085, 仪表窗 z 1.6~1.9, 把手 z 1.05~1.09, 编号牌放中间空位)
# 牌面用薄板 + 彩色边框条做, 不用文字纹理; 牌面文字是真实 Text 对象
# (bpy.data.curves.new type 'FONT'), 随牌导出进 GLB, 不再是占位色块
# 字体: 工程 tools/fonts/NotoSansSC-static.ttf (全量, 10MB; 注意 assets/fonts/
# NotoSansSC-Regular.ttf 是子集, 经 fontTools 核查缺 危/险/止/人 四字, 会出方框, 不能用)
# 该字体已推上仓库 (tools/fonts/NotoSansSC-static.ttf) 且打包进 .blend (双保险);
# 缺字体时 Blender 静默用内置 Noto Sans CJK Regular 替代, 同 size 字形大 ~2.85 倍.
# 系统备用: /usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc (仅应急, 会打乱尺寸)
# 只做标识牌: 不做配电柜/变压器/母线线缆/墙面地面
# 材质只用 Principled BSDF
# 渲染: 本地不渲染, 预览图走 GitHub Actions 出图; 本脚本只做建模→存盘→导出→回读验证
# (灯光/相机仍保留在场景里, 供 Actions 渲染用)
import bpy
import math
import os
from mathutils import Vector

BASE = "/home/hatch/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot"
BLEND_PATH = BASE + "/assets/blender/dist/di-signs.blend"
GLB_PATH = BASE + "/assets/models/di-signs.glb"

# ---------- clean scene ----------
bpy.ops.wm.read_factory_settings(use_empty=True)

def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def hex_to_linear(h):
    h = h.lstrip("#")
    return tuple(srgb_to_linear(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4))

def make_material(name, hex_color, roughness=0.5, metallic=0.0,
                  noise_scale=4.0, noise_offset=(0.0, 0.0)):
    """程序化纹理材质 (红线要求): 噪波做轻微粗糙度变化 + 深浅不均 + 轻微凹凸,
    没有任何一个面是全平的; 每种颜色用不同的噪波尺度/偏移区分开.
    只用程序化节点, 不用贴图."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    base = hex_to_linear(hex_color)
    # Base Color 保持纯色数值 (不挂节点): glTF 导出器解析不了噪波混色节点,
    # 一挂节点导出后底色会丢成白 (已实测), 所以底色只走 socket 默认值
    bsdf.inputs["Base Color"].default_value = (*base, 1.0)
    # 噪波源 (Generated 坐标, 粗斑块, 牌面上看得见)
    texcoord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Location"].default_value = (noise_offset[0], noise_offset[1], 0.0)
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = noise_scale
    noise.inputs["Detail"].default_value = 2.5
    noise.inputs["Roughness"].default_value = 0.7
    noise.inputs["Distortion"].default_value = 0.3
    nt.links.new(texcoord.outputs["Generated"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    # Roughness: 噪波映射到 roughness +/-0.3, 光照下形成深浅不均
    # (20px 大的牌面上 +/-0.2 几乎看不出, 必须加到 +/-0.3 才可见)
    rough_range = nt.nodes.new("ShaderNodeMapRange")
    rough_range.clamp = True
    rough_range.inputs["From Min"].default_value = 0.0
    rough_range.inputs["From Max"].default_value = 1.0
    rough_range.inputs["To Min"].default_value = max(0.05, roughness - 0.3)
    rough_range.inputs["To Max"].default_value = min(1.0, roughness + 0.3)
    nt.links.new(noise.outputs["Fac"], rough_range.inputs["Value"])
    nt.links.new(rough_range.outputs[0], bsdf.inputs["Roughness"])
    # 轻微凹凸, 强化漆面/塑料质感
    # (实测: 牌面朝南、太阳在西南, 镜面反射打不到相机, 粗糙度变化在预览里
    #  几乎不可见; 只有凹凸能改漫反射明暗, 强度必须到 1.0 纹理才看得见)
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 1.0
    bump.inputs["Distance"].default_value = 0.1
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Metallic"].default_value = metallic
    return mat

RED_MAT = make_material("Sign_Red", "#C0392B", 0.45, 0.0, noise_scale=2.5, noise_offset=(0.0, 0.0))
WHITE_MAT = make_material("Sign_White", "#F5F5F0", 0.35, 0.0, noise_scale=3.5, noise_offset=(3.7, 1.2))
YELLOW_MAT = make_material("Sign_Yellow", "#E8B400", 0.5, 0.0, noise_scale=3.0, noise_offset=(7.1, 4.3))
BLUE_MAT = make_material("Sign_Blue", "#1F4E79", 0.55, 0.0, noise_scale=3.5, noise_offset=(2.3, 8.9))

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

def add_text(name, body, size, loc, quat, mat, fit_width=None,
             fit_height=None, space_line=1.0):
    """真实文字: Font 曲线对象, 贴牌面表面 (origin 离牌面 0.0015m, 挤出
    0.0005m, 最远 0.002m, 防 z-fighting); 字色与底色对比鲜明 (红牌/蓝标
    白字, 白牌红字). quat 由 to_track_quat 给出: 局部 -Z 沿视线反方向,
    局部 Y 尽量朝世界 +Z (字正, 阅读方向正确).
    字号自校准: Blender 字号与字宽不是 1:1 (实测 size=1.0 时 4 字中文宽
    仅 1.3725m, 约 0.343x), 所以建完按实测尺寸把 size 缩放到目标宽度
    (约牌面宽度的 70%) / 高度, 不靠字号换算猜."""
    cu = bpy.data.curves.new(name, type='FONT')
    cu.body = body
    cu.font = FONT
    cu.size = size
    cu.align_x = 'CENTER'
    cu.align_y = 'CENTER'
    cu.extrude = 0.0005
    cu.space_line = space_line
    ob = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = quat
    cu.materials.append(mat)
    if fit_width or fit_height:
        bpy.context.view_layer.update()
        w, h = ob.dimensions.x, ob.dimensions.y  # 局部 X=行向, Y=字高向
        s = cu.size
        if fit_width and w > 1e-6:
            # 以宽度为准缩放到目标宽; 高度只作上限 (超了再按高度往下压)
            s = s * fit_width / w
            if fit_height and h > 1e-6:
                h_after_w = h * (s / cu.size)
                if h_after_w > fit_height:
                    s = s * fit_height / h_after_w
        elif fit_height and h > 1e-6:
            # 只给高度时以高度为准 (单个数字: 字高受牌面高度限制)
            s = s * fit_height / h
        cu.size = s
        bpy.context.view_layer.update()
        print("text fit:", name, "size", round(cu.size, 3),
              "dims", tuple(round(v, 3) for v in ob.dimensions))
    return ob

# 字体: 全量思源黑体 (核查过: 高压危险/禁止合闸/有人工作/数字全覆盖)
FONT_PATH = BASE + "/tools/fonts/NotoSansSC-static.ttf"
if not os.path.exists(FONT_PATH):
    FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FONT = bpy.data.fonts.load(FONT_PATH)
print("di-signs font:", FONT_PATH)

# 朝南牌面 (北墙牌 / 编号牌): 字面法线 -Y, 字顶 +Z, 阅读方向 +X (向东)
QUAT_SOUTH = Vector((0.0, 1.0, 0.0)).to_track_quat('-Z', 'Y')
# 朝西牌面 (东墙牌): 字面法线 -X, 字顶 +Z, 阅读方向 -Y (向南, 观者右手向)
QUAT_WEST = Vector((1.0, 0.0, 0.0)).to_track_quat('-Z', 'Y')

objs = []

# ---------- 墙面警示牌 1: 北墙 "高压危险", 红底 + 黄边 + 白字 ----------
# 边框底板 (黄, 稍大一圈, 贴墙): 0.66 x 0.015 x 0.46, y 4.798~4.813
objs.append(add_box("Warn_Border", (0.66, 0.015, 0.46), (0.0, 4.805, 2.4), YELLOW_MAT, bevel=0.003))
# 牌面 (红): 0.6 x 0.02 x 0.4, y 4.78~4.80; 南面 y=4.78, 文字 origin y=4.7785
objs.append(add_box("Warn_Plate", (0.6, 0.02, 0.4), (0.0, 4.79, 2.4), RED_MAT, bevel=0.003))
objs.append(add_text("Warn_Text", "高压危险", 0.105, (0.0, 4.7785, 2.4),
                     QUAT_SOUTH, WHITE_MAT, fit_width=0.42, fit_height=0.30))

# ---------- 墙面警示牌 2: 东墙 "禁止合闸 有人工作", 白底 + 红边 + 红字 ----------
# 边框底板 (红, 稍大一圈, 贴墙): 0.015 x 0.66 x 0.46, x 7.798~7.813
objs.append(add_box("NoClose_Border", (0.015, 0.66, 0.46), (7.805, 0.0, 2.4), RED_MAT, bevel=0.003))
# 牌面 (白): 0.02 x 0.6 x 0.4, x 7.78~7.80; 西面 x=7.78, 文字 origin x=7.7785
objs.append(add_box("NoClose_Plate", (0.02, 0.6, 0.4), (7.79, 0.0, 2.4), WHITE_MAT, bevel=0.003))
# 两行: "禁止合闸" / "有人工作", 每行宽≤0.42m (占牌面长边 0.6m 的 70%),
# 行距 0.8, 整块高约 0.28m (占牌面高 0.4m 的 70%)
# (2026-11-23 复核: 原 fit_height=0.34 占牌面高 85%, 超 70% 上限, 改 0.28)
objs.append(add_text("NoClose_Text", "禁止合闸\n有人工作", 0.105, (7.7785, 0.0, 2.4),
                     QUAT_WEST, RED_MAT, fit_width=0.42, fit_height=0.28,
                     space_line=0.8))

# ---------- 设备编号牌 6 块: 柜门上, 蓝底白框, 贴门面南侧 ----------
# 柜门面 y=4.085; 边框底板 y 4.080~4.092, 牌面 y 4.069~4.084, 南面 y=4.0695, 文字 origin y=4.068
# 牌面 0.20x0.12m, 单个数字: 以高度为准 (字高约 0.075m, 占牌面高 62%),
# 宽度由字形决定 (约 0.04m), 不硬撑 70% 宽度
for i, cx in enumerate((-6.0, -3.6, -1.2, 1.2, 3.6, 6.0)):
    tag = "Num%d" % (i + 1)
    objs.append(add_box("%s_Border" % tag, (0.24, 0.012, 0.16), (cx, 4.082, 1.35), WHITE_MAT, bevel=0.002))
    objs.append(add_box("%s_Plate" % tag, (0.20, 0.015, 0.12), (cx, 4.077, 1.35), BLUE_MAT, bevel=0.002))
    objs.append(add_text("%s_Text" % tag, "%d" % (i + 1), 0.10, (cx, 4.068, 1.35),
                         QUAT_SOUTH, WHITE_MAT, fit_height=0.075))

print("di-signs objects:", len(objs), [o.name for o in objs])

# ---------- 文字尺寸硬校验 (2026-11-23 第六轮复核教训) ----------
# 上一版 .blend 在本地量着全对, 渲染机上却溢出约 2.85 倍: 原因是渲染机
# 上 tools/fonts/NotoSansSC-static.ttf 缺失, Blender 用内置 Noto Sans CJK
# Regular 替代, 同样 size 下字形大 ~2.85 倍. 尺寸必须在建完当场按实测
# 包围盒校验, 且字体必须随 .blend 打包 + 推上仓库, 否则下次还会复发.
bpy.context.view_layer.update()
_TEXT_LIMITS = {"Warn_Text": (0.42, 0.20), "NoClose_Text": (0.42, 0.28)}
for _ob in objs:
    if not _ob.name.endswith("_Text"):
        continue
    _w, _h = _ob.dimensions.x, _ob.dimensions.y  # 局部 X=行向, Y=字高向
    if _ob.name in _TEXT_LIMITS:
        _mw, _mh = _TEXT_LIMITS[_ob.name]
        assert _w <= _mw + 1e-6 and _h <= _mh + 1e-6, \
            "text oversize: %s %.3fx%.3f > %.3fx%.3f" % (_ob.name, _w, _h, _mw, _mh)
    else:  # Num*_Text: 字高 0.072~0.084m (牌面高 0.12m 的 60~70%), 宽 <=0.14m
        assert 0.072 <= _h <= 0.084 and _w <= 0.14, \
            "text oversize: %s %.3fx%.3f" % (_ob.name, _w, _h)
    print("text check OK:", _ob.name, "%.3fx%.3f" % (_w, _h))

# ---------- lighting (SPEC §2) ----------
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

# 室内预览补光 (仅预览, 不导出): 一盏点光源在牌前方上方
ld = bpy.data.lights.new("Preview_Point", type='POINT')
ld.energy = 300.0
ld.shadow_soft_size = 0.5
lo = bpy.data.objects.new("Preview_Point", ld)
bpy.context.collection.objects.link(lo)
lo.location = (0.0, 1.5, 5.0)

# ---------- camera: 南侧稍近处广角, 一次看清 8 块牌 ----------
# 北墙牌与编号牌朝南, 东墙牌朝西; 机位放正南, 东墙牌不再斜切成窄条
# 视轴对准最西编号牌 (-6) 与东墙牌 (7.79) 的角平分线, 22mm 刚好框住 8 块牌
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 22.0
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera = cam
cam.location = (0.0, -8.0, 3.2)
target = Vector((2.0, 4.0, 1.9))
cam.rotation_mode = 'QUATERNION'
cam.rotation_quaternion = (target - cam.location).to_track_quat('-Z', 'Y')

# ---------- render settings (仅留给 Actions 渲染用, 本地不执行渲染) ----------
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.eevee.taa_render_samples = 16
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100

# ---------- 字体打包进 .blend (双保险, 与推仓库并行) ----------
# 渲染机只读 .blend 时若 tools/fonts/ 文件缺失, Blender 静默用内置
# Noto Sans CJK Regular 替代, 同 size 字形大 ~2.85 倍 -> 全牌溢出.
# 打包后 .blend 自带字体, 不依赖外部文件.
for _f in bpy.data.fonts:
    if _f.filepath and _f.filepath != '<builtin>' and _f.packed_file is None:
        _f.pack()
        print("font packed:", _f.name, "packed:", _f.packed_file is not None)

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
assert len(imported) == len(objs), "glb reimport failed: expected %d objects, got %d" % (len(objs), len(imported))
# 回读材质颜色自查: 程序化噪波混色不能把 GLB 底色带偏
for ob in imported:
    for slot in ob.material_slots:
        m = slot.material
        if m and m.use_nodes:
            print("GLB material:", m.name,
                  "base:", tuple(round(v, 3) for v in
                                 m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value[:3]))
# 文字对象核查: 8 个文字对象 (Warn/NoClose/Num1-6) 必须随牌进 GLB,
# 且尺寸符合设计 (Warn 宽 0.42m/高<=0.20m; NoClose 每行宽<=0.42m/总高 0.28m;
# 数字高 0.075m, 占牌面高 62%)
text_objs = [ob for ob in imported
             if ob.name.split(".")[0].endswith("_Text")]  # 回读名带 .001 后缀
print("GLB text objects:", len(text_objs), [ob.name for ob in text_objs])
assert len(text_objs) == 8, "glb text missing: expected 8, got %d" % len(text_objs)
for ob in text_objs:
    print("GLB text dims:", ob.name,
          tuple(round(v, 3) for v in ob.dimensions))
# 删掉回读的副本, 恢复干净场景
bpy.ops.object.select_all(action='DESELECT')
for ob in imported:
    ob.select_set(True)
bpy.ops.object.delete()

# 本地不渲染 (预览图走 GitHub Actions); 保存最终工程
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("DONE di-signs")
