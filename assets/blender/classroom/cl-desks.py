# cl-desks v4: 教室内部 - 课桌椅 (6列 x 8排 = 48套)
# 换装 (R2-T17, 2026-11-24): tevy 教室模型拆件 -> 3DAssets Student Desk +
#   Student Chair (CC0, 见 assets/external/SOURCES.md §7, R2-T2 选定)。
#   文件: assets/external/desks/3dassets/student-desk.glb (51,796 B)
#         assets/external/desks/3dassets/student-chair.glb (43,632 B)
#   选定理由: 真正的学校课桌椅、弯钢圆管桌架/椅架真腿落地 (各 508 个
#   顶点在地面 z<0.02)、桌带钢丝书篮、椅带横撑脚踏杆、米制实尺无需缩放。
# tevy 拆件否决原因 (见 SOURCES.md §7.3): 未焊接碎面 (desks 2832 /
#   chairs 3072 个 loose 碎片, 只能 Voronoi 聚类硬拆)、椅 mesh 混进
#   1.16m 高柜 (4 张椅带 135-236 张柜面)、桌腿是碎面拼出来的不是完整
#   几何 ("悬浮金色平板" 即源于此)。本版彻底换掉, 不留任何 tevy 碎片。
# 实测尺寸 (Blender 4.2 只读导入, glTF X=宽/Y=深/Z=高, 米):
#   单桌 0.60 x 0.50 x 0.70 (桌面 0.03 厚 z 0.67-0.70; 钢架 684 面);
#   单椅 0.38 x 0.42 x 0.89 (座高约 0.42, 靠背顶 0.888; 钢架 388 面)。
#   单套 780+580=1360 面, 48 套合计 65,280 面。
# 口径说明: 任务口径 "桌 1.1-1.3m" 指双人桌 -- 两张 0.60m 单人桌并排
#   = 1.20m 正好落入口径; 桌高 0.70 vs SPEC 0.75 差 5cm, 接受为偏差
#   (实测值不改比例)。布局沿用 v3 (6 列 x 8 排, 留讲台前空地与过道)。
# 朝向 (实测): 椅靠背 (z>0.65 的木面 y 0.148-0.196) 与桌钢丝书篮
#   (z 0.225-0.255 的钢丝 y 0.146-0.175) 都在 Blender +Y 一侧 = 学生侧,
#   学生面向 -Y。SPEC 要求学生面向 -x, 故整件绕 Z 转 -90 度
#   (Blender (x,y) -> SPEC (y,-x)): 面向 -Y -> -X, 学生侧 +Y -> +X
#   (椅在桌的 +x 一侧, 与 CHAIR_DX 一致)。
# 局部坐标: 房间中心原点, x=长 9.68m (-4.84~+4.84), y=宽 7.26m
#   (-3.63~+3.63), z 0-3.0m; 黑板墙在 x=-4.84 一侧, 学生面向 -x 坐。
# 材质: 桌面木面 #C8A06A、椅面深色 #7A4A2B、钢架深灰金属 #424A52
#   (SPEC §3), 再走 _apply_pbr_textures 挂 tex/ 染色贴图 (与 v3 相同
#   三件套)。两件原材质只有 timber/steel 两种、无贴图, 染色即可。
# 本脚本不渲染 (渲染走 GitHub Actions), 只建模 + 存 .blend + 导出
#   .glb + 回读校验 96 个对象。
import bpy
import math
import os
from mathutils import Matrix, Vector

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
SCRIPT_DIR = os.path.join(BASE, "assets/blender/classroom")
DESK_GLB = os.path.join(BASE, "assets/external/desks/3dassets/student-desk.glb")
CHAIR_GLB = os.path.join(BASE, "assets/external/desks/3dassets/student-chair.glb")
MODEL_PATH = os.path.join(BASE, "assets/models/cl-desks.glb")
BLEND_PATH = os.path.join(SCRIPT_DIR, "cl-desks.blend")
for p in (SCRIPT_DIR, os.path.dirname(MODEL_PATH)):
    os.makedirs(p, exist_ok=True)

# ---------- 场景清理 ----------
bpy.ops.wm.read_factory_settings(use_empty=True)

# ---------- sRGB 十六进制 -> 线性 ----------
def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def hex_to_linear(h):
    h = h.lstrip("#")
    r = int(h[0:2], 16) / 255.0
    g = int(h[2:4], 16) / 255.0
    b = int(h[4:6], 16) / 255.0
    return (srgb_to_linear(r), srgb_to_linear(g), srgb_to_linear(b), 1.0)

def make_material(name, hex_color, roughness=0.7, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = hex_to_linear(hex_color)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat

# 桌面木纹 #C8A06A, 椅面木纹 #7A4A2B, 桌腿/椅腿深灰金属 #424A52
# (_apply_pbr_textures 会把 Base Color/Roughness/Normal 改挂贴图,
#  这里只留底色与 Metallic; leg_metal 保持金属度 0.75)
MAT_WOOD = make_material("desk_wood", "#C8A06A", 0.55)
MAT_CHAIR = make_material("chair_wood", "#7A4A2B", 0.60)
MAT_LEG = make_material("leg_metal", "#424A52", 0.45, metallic=0.75)

# ---------- 导入 3DAssets 单件, 合并成一件模板 ----------
def load_template(glb_path, wood_mat, label, backrest_z=None):
    """导入一件 (timber + steel 两个 mesh), 解除父级并烘变换, 合并成
    一个对象 (2 个材质槽), 换成本件 SPEC 材质, 移到原点 (包围盒中心
    落 x/y 原点, z 保持 0 落地), 绕 Z 转 -90 度 (面向 -x) 并烘进网格。
    返回模板对象 (已摆正, 可直接按目标点 location 放置)。
    注意: join 后的网格上 bpy.ops.object.transform_apply(rotation=True)
    会静默失效 (rotation_euler 清零但顶点不动, 已复现), 故居中与旋转
    一律用 mesh.transform(矩阵) 直接烘顶点, 不用 operator。
    backrest_z: 椅子传 0.65, 断言靠背 (高处木面) 转后落在 +X 一侧。"""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=glb_path)
    new_objs = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new_objs if o.type == "MESH"]
    print("%s imported: %s" % (label, [(o.name, o.type) for o in new_objs]))
    assert len(meshes) == 2, "%s expected 2 meshes, got %d" % (label, len(meshes))
    for o in meshes:
        bpy.ops.object.select_all(action="DESELECT")
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        zs = [v.co.z for v in o.data.vertices]
        print("%s mesh %s: faces=%d z[%.3f, %.3f] ground verts(z<0.02)=%d/%d" % (
            label, o.name, len(o.data.polygons), min(zs), max(zs),
            sum(1 for z in zs if z < 0.02), len(zs)))
    # 删空父级 (EMPTY, 不进导出)
    for o in new_objs:
        if o.type != "MESH":
            bpy.data.objects.remove(o, do_unlink=True)
    # 合并: timber + steel -> 一个对象, 2 个材质槽
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()
    ob = bpy.context.active_object
    ob.name = label + "_template"
    # 换材质: 原 timber/steel (椅子导入时可能已是 .001 后缀, 按前缀认)
    # 按槽位逐个替换
    mat_names = [m.name if m else None for m in ob.data.materials]
    for i, mn in enumerate(mat_names):
        if mn is None:
            continue
        if mn.startswith("timber"):
            ob.data.materials[i] = wood_mat
        elif mn.startswith("steel"):
            ob.data.materials[i] = MAT_LEG
        else:
            raise RuntimeError("%s unexpected material slot: %s" % (label, mn))
    print("%s joined: %s faces=%d mats=%s" % (
        label, ob.name, len(ob.data.polygons),
        [m.name if m else None for m in ob.data.materials]))
    # 包围盒中心移到 x/y 原点 (z 不动, 保持 0 落地)
    vs = [v.co for v in ob.data.vertices]
    xs = [v.x for v in vs]; ys = [v.y for v in vs]; zs = [v.z for v in vs]
    cx, cy = (min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0
    print("%s bbox before centering: x[%.3f, %.3f] y[%.3f, %.3f] z[%.3f, %.3f] centre=(%.3f, %.3f)" % (
        label, min(xs), max(xs), min(ys), max(ys), min(zs), max(zs), cx, cy))
    assert abs(min(zs)) < 0.01, "%s not grounded: zmin=%.3f" % (label, min(zs))
    # 居中 + 旋转一律用 mesh.transform 直接烘顶点 (见函数头注: join 后
    # transform_apply(rotation=True) 静默失效)
    ob.data.transform(Matrix.Translation((-cx, -cy, 0.0)))
    ob.data.transform(Matrix.Rotation(math.radians(-90.0), 4, "Z"))
    ob.data.update()
    vs = [v.co for v in ob.data.vertices]
    xs = [v.x for v in vs]; ys = [v.y for v in vs]; zs = [v.z for v in vs]
    print("%s template ready: x[%.3f, %.3f] y[%.3f, %.3f] z[%.3f, %.3f]" % (
        label, min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
    if backrest_z is not None:
        # 靠背 (高处顶点) 必须在 +X 一侧 (学生侧, 椅在桌的 +x 一侧)
        hx = [v.co.x for v in ob.data.vertices if v.co.z > backrest_z]
        print("%s backrest verts: n=%d x[%.3f, %.3f]" % (label, len(hx), min(hx), max(hx)))
        assert min(hx) > 0.05, "%s backrest not on +X side: xmin=%.3f" % (label, min(hx))
    return ob

desk_template = load_template(DESK_GLB, MAT_WOOD, "desk")
chair_template = load_template(CHAIR_GLB, MAT_CHAIR, "chair", backrest_z=0.65)
DESK_FACES = len(desk_template.data.polygons)
CHAIR_FACES = len(chair_template.data.polygons)
print("single desk faces=%d single chair faces=%d per-set=%d 48-set total=%d" % (
    DESK_FACES, CHAIR_FACES, DESK_FACES + CHAIR_FACES,
    (DESK_FACES + CHAIR_FACES) * 48))
assert DESK_FACES == 780, "desk faces changed: %d" % DESK_FACES
assert CHAIR_FACES == 580, "chair faces changed: %d" % CHAIR_FACES

# ---------- 按 SPEC 排布 (与 v3 同布局) ----------
GROUP_DX = -0.14
COL_Y = [-2.8, -1.8, -0.8, 0.8, 1.8, 2.8]
ROW_X = [-3.04 + GROUP_DX + i * 1.0 for i in range(8)]
CHAIR_DX = 0.44  # 椅心离桌心

def place(template, targets, prefix):
    """模板循环复用 (共享网格数据)。命名沿用旧版 desk_r1_c1 /
    chair_r8_c6, scenes/classroom.py 的门洞检查 (chair_r8_ 前缀) 依赖它。"""
    placed = []
    for ti, (r, c, tx, ty) in enumerate(targets):
        if ti == 0:
            ob = template
        else:
            ob = template.copy()
            ob.data = template.data  # 共享网格
            bpy.context.collection.objects.link(ob)
        ob.location = (tx, ty, 0.0)
        ob.name = "%s_r%d_c%d" % (prefix, r + 1, c + 1)
        placed.append(ob)
    return placed

desk_targets = [(r, c, x, y) for r, x in enumerate(ROW_X)
                for c, y in enumerate(COL_Y)]
desks = place(desk_template, desk_targets, "desk")
chair_targets = [(r, c, x + CHAIR_DX, y) for (r, c, x, y) in desk_targets]
chairs = place(chair_template, chair_targets, "chair")

print("desks:", len(desks), "chairs:", len(chairs))
print("GROUP_DX:", GROUP_DX, "CHAIR_DX:", CHAIR_DX)
print("row_x:", ROW_X)
print("col_y:", COL_Y)

# 几何自检: 桌子世界 z 应为 0~0.70, 椅子 0~0.89 (SPEC 桌高 0.75, 差 5cm
#   为接受的实测偏差, 见文件头)
bpy.context.view_layer.update()
def world_z_range(obj):
    zs = [(obj.matrix_world @ Vector(c)).z for c in obj.bound_box]
    return min(zs), max(zs)
_dz = world_z_range(desks[0])
_cz = world_z_range(chairs[0])
print("desk world z range:", _dz, "chair world z range:", _cz)
assert abs(_dz[0]) < 0.01 and abs(_dz[1] - 0.70) < 0.02, "desk z range wrong: %s" % (_dz,)
assert abs(_cz[0]) < 0.01 and abs(_cz[1] - 0.89) < 0.02, "chair z range wrong: %s" % (_cz,)

# 间隙实测 (与 classroom.py 同口径): 讲台桌前沿 x=-3.695, 东墙内面 x=4.765
def world_bbox(objects):
    mins = Vector((1e9, 1e9, 1e9))
    maxs = Vector((-1e9, -1e9, -1e9))
    for o in objects:
        if o.type != "MESH":
            continue
        for v in o.bound_box:
            w = o.matrix_world @ Vector(v)
            for i in range(3):
                mins[i] = min(mins[i], w[i])
                maxs[i] = max(maxs[i], w[i])
    return mins, maxs
_dmn, _dmx = world_bbox(desks)
_cmn, _cmx = world_bbox(chairs)
_gap_front = _dmn.x - (-3.695)
_gap_rear = 4.765 - _cmx.x
print("desks bbox x[%.3f, %.3f] y[%.3f, %.3f] z[%.3f, %.3f]" % (
    _dmn.x, _dmx.x, _dmn.y, _dmx.y, _dmn.z, _dmx.z))
print("chairs bbox x[%.3f, %.3f] y[%.3f, %.3f] z[%.3f, %.3f]" % (
    _cmn.x, _cmx.x, _cmn.y, _cmx.y, _cmn.z, _cmx.z))
print("gap front (nearest desk edge to podium front -3.695): %.3f" % _gap_front)
print("gap rear (last chair back to east wall 4.765): %.3f" % _gap_rear)
assert _gap_front >= 0.19, "front gap too small: %.3f" % _gap_front
assert _gap_rear >= 0.15, "rear gap too small: %.3f" % _gap_rear

# ---- PBR 贴图固化 (2026-11-23)：把上一轮挂在 .blend 上的外部贴图写进脚本 ----
# color 图：assets/blender/tex/ 里的染色图（已按 SPEC §3 目标色染色）；
# rough/normal 图：assets/external/ 原图（CC0）。
# 节点只许 TexCoord→Mapping→Image Texture 直连 BSDF，不加 Hue/Sat/Mix，
# 否则 glTF 导出器不认。Base Color 默认值须置白、Roughness 置 1.0（贴图
# 本身带颜色与粗糙度），否则导出器会把旧纯色写成 baseColorFactor/
# roughnessFactor 与贴图二次相乘；Metallic 保持脚本原值。
# 3DAssets 两件自带 UV（glTF 导入已有），这里只补缺失的。
TEX_DIR = os.path.join(BASE, "assets/blender/tex")
EXT_DIR = os.path.join(BASE, "assets/external")
# 材质名: (tex/ 染色 color 图, external rough 图, external normal 图, Mapping 缩放)
PBR_TEXTURES = {
    "desk_wood": ("wooden_floor_01__C8A06A.jpg",
        "polyhaven/wooden_floor_01_rough_1k.jpg",
        "polyhaven/wooden_floor_01_nor_gl_1k.jpg", (1.0, 1.0)),
    "leg_metal": ("blue_metal_plate__424A52.jpg",
        "polyhaven/blue_metal_plate_rough_1k.jpg",
        "polyhaven/blue_metal_plate_nor_gl_1k.jpg", (1.0, 1.0)),
    "chair_wood": ("WoodFloor051__7A4A2B.jpg",
        "ambientcg/WoodFloor051/WoodFloor051_1K-JPG_Roughness.jpg",
        "ambientcg/WoodFloor051/WoodFloor051_1K-JPG_NormalGL.jpg", (1.0, 1.0)),
}


_IMG_CACHE = {}


def _pbr_load_image(abs_path, colorspace):
    # 同一文件只加载一次：filepath 改成相对路径后 check_existing 会按路径
    # 字符串比对失效、重复建 .001 副本，故用自带缓存去重
    img = _IMG_CACHE.get(abs_path)
    if img is None:
        img = bpy.data.images.load(abs_path, check_existing=True)
        img.colorspace_settings.name = colorspace
        # 存相对路径进 .blend（// 相对 .blend 所在目录），仓库检出后仍能找到
        rel = os.path.relpath(abs_path, os.path.dirname(BLEND_PATH)).replace(os.sep, "/")
        img.filepath = "//" + rel
        _IMG_CACHE[abs_path] = img
    return img


def _apply_pbr_textures():
    for mat_name, (color_f, rough_f, normal_f, scale) in PBR_TEXTURES.items():
        mat = bpy.data.materials.get(mat_name)
        if mat is None:
            print("PBR SKIP missing material:", mat_name)
            continue
        nt = mat.node_tree
        bsdf = nt.nodes["Principled BSDF"]
        # 清掉旧程序化节点，只留 BSDF 与 Output
        for node in list(nt.nodes):
            if node.type not in ("BSDF_PRINCIPLED", "OUTPUT_MATERIAL"):
                nt.nodes.remove(node)
        bsdf.inputs["Base Color"].default_value = (1.0, 1.0, 1.0, 1.0)
        bsdf.inputs["Roughness"].default_value = 1.0
        texcoord = nt.nodes.new("ShaderNodeTexCoord")
        mapping = nt.nodes.new("ShaderNodeMapping")
        mapping.inputs["Scale"].default_value = (scale[0], scale[1], 1.0)
        nt.links.new(texcoord.outputs["UV"], mapping.inputs["Vector"])
        tex_c = nt.nodes.new("ShaderNodeTexImage")
        tex_c.image = _pbr_load_image(os.path.join(TEX_DIR, color_f), "sRGB")
        nt.links.new(mapping.outputs["Vector"], tex_c.inputs["Vector"])
        nt.links.new(tex_c.outputs["Color"], bsdf.inputs["Base Color"])
        tex_r = nt.nodes.new("ShaderNodeTexImage")
        tex_r.image = _pbr_load_image(os.path.join(EXT_DIR, rough_f), "Non-Color")
        nt.links.new(mapping.outputs["Vector"], tex_r.inputs["Vector"])
        nt.links.new(tex_r.outputs["Color"], bsdf.inputs["Roughness"])
        tex_n = nt.nodes.new("ShaderNodeTexImage")
        tex_n.image = _pbr_load_image(os.path.join(EXT_DIR, normal_f), "Non-Color")
        nmap = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(mapping.outputs["Vector"], tex_n.inputs["Vector"])
        nt.links.new(tex_n.outputs["Color"], nmap.inputs["Color"])
        nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
        print("PBR textured:", mat_name, color_f, "scale", scale)


def _ensure_uvs(objs):
    """没有 UV 的网格补 Smart UV Project（已有 UV 的不动）。"""
    todo = []
    seen = set()
    for ob in objs:
        if ob.type != "MESH":
            continue
        if id(ob.data) in seen:
            continue
        seen.add(id(ob.data))
        if len(ob.data.uv_layers) == 0:
            todo.append(ob)
    if not todo:
        print("UV OK: all meshes have UVs")
        return
    bpy.ops.object.select_all(action="DESELECT")
    for ob in todo:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = todo[0]
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66.0), island_margin=0.02)
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    print("UV smart-projected:", len(todo), [o.name for o in todo])


_apply_pbr_textures()
_ensure_uvs(desks + chairs)

# ---------- 存 .blend ----------
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)

# ---------- 导出 .glb (只选本件对象) ----------
bpy.ops.object.select_all(action="DESELECT")
for o in desks + chairs:
    o.select_set(True)
bpy.ops.export_scene.gltf(
    filepath=MODEL_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
)

# ---------- 回读校验 (应为 96 个对象) ----------
bpy.ops.import_scene.gltf(filepath=MODEL_PATH)
imported = [o for o in bpy.context.selected_objects]
print("gltf reimport objects:", len(imported))
assert len(imported) == 96, "glTF reimport expected 96 objects, got %d" % len(imported)
# 删回读的临时对象
bpy.ops.object.delete()

# 删 Blender 备份
blend1 = BLEND_PATH + "1"
if os.path.exists(blend1):
    os.remove(blend1)
    print("REMOVED", blend1)

print("DONE cl-desks")
