# cl-desks v3: 教室内部 - 课桌椅 (6列 x 8排 = 48套)
# 换件: 自建平板桌椅 -> tevy 教室模型 (CC0, tevy.dev/models/classroom)
#   的桌椅拆件. 原模型 assets/external/buildings/classroom-tevy.glb
#   (EXT_meshopt_compression + KHR_mesh_quantization + KHR_texture_basisu
#   三重压缩, Blender 4.2 打不开) 已用 gltf-transform 去压缩, 并剥掉
#   KTX2 贴图 (Blender 4.2 不认 KHR_texture_basisu; 贴图反正要按
#   _apply_pbr_textures 重挂自家 CC0 染色贴图, 见下):
#   assets/external/buildings/classroom-tevy-plain.glb (去压缩+去贴图,
#   2.2MB; 复现脚本 assets/external/buildings/tevy-decompress.mjs)。
# 实测结论 (2026-11-23, 见拆件分析):
#   - loose-parts 拆分不可用: tevy 的 mesh 全是未焊接碎面 (desks
#     2832 / chairs 3072 个 loose 碎片), 只能按空间 Voronoi 聚类拆件。
#   - desks: 12 张双人桌 -> 24 张单人桌 (单桌 0.61(x)x0.61(y)x0.71(高)m,
#     顶面 0.71 vs SPEC 0.75, 接受实测值不改比例); 双人桌中心
#     x -2.39/-0.22/+2.02, y -2.48/-1.20/+0.10/+1.39, 单桌在中心 ±0.30。
#   - chairs: 20 张正常单椅 (座高 ~0.45, 靠背顶 0.89, 约 0.48x0.59m),
#     另有 2 个 1.02x0.62x1.16m 高柜混在 chairs mesh 里 (后排左右角,
#     tevy x ±2.4 / y -2.41); 高柜面用两条规则剔除: 柜顶 z>0.95 的面,
#     以及离单椅锚点向后 (tevy -y) 超过 0.50m 的面 (正常椅靠背最远
#     只到锚点后 0.45m)。但高柜正面紧贴在第 2 排外侧 4 张椅的靠背后
#     (共面, y 只差 0.02-0.04m), 切不干净: 拆出的 4 个单椅仍各带
#     135-236 张柜面 (799-900 面 vs 正常 664 面, 其中 1 张还带 1.16m
#     柜顶)。故这 4 张不进复用池, 48 套用其余 16 张干净单椅循环复用
#     (共享网格数据; tevy 单椅本就几乎全同, 16 种已足够)。
#   - 单件锚点取拆分后自身的顶点包围盒中心 (tevy 模型手摆有 ±0.2m
#     抖动, Voronoi 中心不准); 拆分时保留原 custom split normals,
#     座面曲面明暗不变。
#   - teacher_desk (1.5x1.25x0.89, 进深 1.25m 是 SPEC 讲台 0.62m 的
#     两倍, 会吃掉讲台前空地并顶住第一排桌) 与 shelves (4.48m 长柜,
#     无 SPEC 位置, 放北墙会挡窗) 均未采用, cl-board.py 保持原样。
#   - 椅子比 SPEC 自建椅深: 靠背顶离椅心 +0.34m (SPEC 自建约 +0.24m),
#     故 CHAIR_DX 由 0.55 收至 0.44, GROUP_DX 由 -0.15 移至 -0.145,
#     使两端间隙仍达标 (前 0.205m / 后 0.167m, 脚本末尾实测断言)。
# 局部坐标: 房间中心原点, x=长 9.68m (-4.84~+4.84), y=宽 7.26m
#   (-3.63~+3.63), z 0~3.0m; 黑板墙在 x=-4.84 一侧, 学生面向 -x 坐。
# tevy 原朝向: 学生面向 +y (讲台在 +y 侧); 换件时整件绕 Z 转 +90 度
#   (tevy (x,y) -> SPEC (-y,x)), 面向变为 -x, 与 SPEC 一致。
# 材质: 桌面/椅面木色 + 腿深灰金属, 按面中心高度与法线分面指定,
#   再走 _apply_pbr_textures 挂 tex/ 染色贴图 (与 v2 相同三件套)。
# 本脚本不渲染 (渲染走 GitHub Actions), 只建模 + 存 .blend + 导出
#   .glb + 回读校验 96 个对象。
import bpy
import math
import os
from mathutils import Vector

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
SCRIPT_DIR = os.path.join(BASE, "assets/blender/classroom")
TEVY_PLAIN = os.path.join(BASE, "assets/external/buildings/classroom-tevy-plain.glb")
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

# ---------- 导入 tevy 去压缩版, 只留 desks / chairs ----------
bpy.ops.import_scene.gltf(filepath=TEVY_PLAIN)
imported = list(bpy.data.objects)
print("tevy imported:", [(o.name, o.type) for o in imported])
for o in imported:
    if o.name not in ("desks", "chairs"):
        bpy.data.objects.remove(o, do_unlink=True)
for name in ("desks", "chairs"):
    o = bpy.data.objects.get(name)
    assert o is not None and o.type == "MESH", "missing tevy mesh: %s" % name
    # 解除父级 (door empty 等), 烘进 glTF 节点变换 (location/scale)
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    print("tevy mesh kept:", name, "verts:", len(o.data.vertices),
          "faces:", len(o.data.polygons),
          "has_custom_normals:", o.data.has_custom_normals)

DESKS_SRC = bpy.data.objects["desks"]
CHAIRS_SRC = bpy.data.objects["chairs"]

# ---------- 拆件: 面片按最近单件中心做 Voronoi 归属 (tevy 局部坐标) ----------
# 双人桌中心 (实测, 见文件头); 单桌 = 双人桌中心 x ± 0.30
DESK_DCX = [-2.39, -0.22, 2.02]
DESK_DCY = [-2.48, -1.20, 0.10, 1.39]
DESK_CENTRES = [(cx + dx, cy) for cy in DESK_DCY for cx in DESK_DCX
                for dx in (-0.30, 0.30)]
# 单椅中心: 10 对椅子座面聚类中心 (实测) x ± 0.255; 后排外侧两对是高柜,
#   不在其中, 故只有 20 个单椅
CHAIR_PAIRS = [(-0.23, -3.03), (-0.23, -1.86), (-2.44, -1.76),
               (2.00, -1.78), (-2.37, -0.46), (2.05, -0.46),
               (-0.21, -0.44), (-0.23, 0.78), (2.07, 0.80),
               (-2.34, 0.92)]
CHAIR_CENTRES = [(cx + dx, cy) for (cx, cy) in CHAIR_PAIRS
                 for dx in (-0.255, 0.255)]
# 高柜区 (tevy 坐标): 柜顶 z>0.95 的面直接剔除, 不进任何单椅
CABINET_X = [(-3.05, -1.75), (1.85, 2.75)]
CABINET_Y = (-2.85, -2.00)

def _nearest_centre(x, y, centres):
    best, bd = -1, 1e18
    for i, (cx, cy) in enumerate(centres):
        d = (x - cx) ** 2 + (y - cy) ** 2
        if d < bd:
            bd, best = d, i
    return best

def _in_cabinet_zone(x, y, z):
    if z <= 0.95:
        return False
    if not (CABINET_Y[0] <= y <= CABINET_Y[1]):
        return False
    return any(lo <= x <= hi for (lo, hi) in CABINET_X)

def split_mesh(src_obj, centres, name_prefix, drop_cabinet=False,
               rear_cutoff=None):
    """按面中心最近单件中心拆成多个新 mesh 对象 (tevy 坐标, 未旋转)。
    drop_cabinet: 剔除高柜面 (柜顶 z>0.95 落在柜区)。
    rear_cutoff: 椅子用, 剔除离单椅锚点向后 (tevy -y) 超过该距离的面
      (正常椅靠背最远到锚点后 0.45m, 高柜面从 0.51m 起)。
    返回 [(object, bbox_centre_anchor_xy)]。拆分时保留原 custom
    split normals (座面曲面明暗不变)。"""
    mesh = src_obj.data
    # Blender 4.2 已无 calc_normals_split; loops[].normal 按需计算, 可直接读
    n = len(centres)
    buckets = [[] for _ in range(n)]
    dropped = 0
    for pi, poly in enumerate(mesh.polygons):
        c = poly.center  # 变换已烘进网格, local == world
        if drop_cabinet and _in_cabinet_zone(c.x, c.y, c.z):
            dropped += 1
            continue
        ci = _nearest_centre(c.x, c.y, centres)
        if rear_cutoff is not None and (centres[ci][1] - c.y) > rear_cutoff:
            dropped += 1
            continue
        buckets[ci].append(pi)
    print("%s split: dropped faces=%d" % (name_prefix, dropped))
    out = []
    for ci, faces in enumerate(buckets):
        if not faces:
            print("WARNING %s single %d got 0 faces, skipped" % (name_prefix, ci))
            continue
        vmap = {}
        verts = []
        new_faces = []
        smooth = []
        loop_normals = []
        for pi in faces:
            poly = mesh.polygons[pi]
            idxs = []
            for vi in poly.vertices:
                if vi not in vmap:
                    vmap[vi] = len(verts)
                    verts.append(tuple(mesh.vertices[vi].co))
                idxs.append(vmap[vi])
            new_faces.append(tuple(idxs))
            smooth.append(poly.use_smooth)
            for li in poly.loop_indices:
                loop_normals.append(tuple(mesh.loops[li].normal))
        me = bpy.data.meshes.new("%s_%02d" % (name_prefix, ci))
        me.from_pydata(verts, [], new_faces)
        me.update()
        for poly, sm in zip(me.polygons, smooth):
            poly.use_smooth = sm
        try:
            me.normals_split_custom_set(loop_normals)
            print("%s single %2d: custom normals kept (%d loops)" % (
                name_prefix, ci, len(loop_normals)))
        except Exception as e:
            print("%s single %2d: custom normals SKIPPED (%s)" % (
                name_prefix, ci, e))
        ob = bpy.data.objects.new("%s_%02d" % (name_prefix, ci), me)
        bpy.context.collection.objects.link(ob)
        # 自检: 面数与包围盒 (tevy 坐标); 锚点取自身包围盒中心
        xs = [v[0] for v in verts]; ys = [v[1] for v in verts]; zs = [v[2] for v in verts]
        anchor = ((min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0)
        print("%s single %2d: faces=%4d bbox x[%.2f,%.2f] y[%.2f,%.2f] z[%.2f,%.2f] anchor=(%.2f,%.2f)" % (
            name_prefix, ci, len(new_faces),
            min(xs), max(xs), min(ys), max(ys), min(zs), max(zs),
            anchor[0], anchor[1]))
        out.append((ob, anchor, faces))
    return out

desk_singles = split_mesh(DESKS_SRC, DESK_CENTRES, "tevy_desk")
chair_singles = split_mesh(CHAIRS_SRC, CHAIR_CENTRES, "tevy_chair",
                           drop_cabinet=True, rear_cutoff=0.50)
assert len(desk_singles) == 24, "expected 24 desk singles, got %d" % len(desk_singles)
assert len(chair_singles) == 20, "expected 20 chair singles, got %d" % len(chair_singles)
# 椅子复用池: 只留干净的单椅 (正常 664 面 / 靠背顶 0.89m)。
# 第 2 排外侧 4 张带高柜正面碎面 (799-900 面, 其中 1 张高 1.16m),
# 不进复用池 (见文件头)。
chair_pool = []
for ob, anchor, faces in chair_singles:
    zs = [v.co.z for v in ob.data.vertices]
    if 600 <= len(faces) <= 720 and max(zs) <= 0.90:
        chair_pool.append((ob, anchor, faces))
    else:
        print("chair single EXCLUDED from pool: %s faces=%d zmax=%.2f" % (
            ob.name, len(faces), max(zs)))
        bpy.data.objects.remove(ob, do_unlink=True)
print("chair reuse pool: %d clean singles" % len(chair_pool))
assert len(chair_pool) >= 12, "too few clean chairs: %d" % len(chair_pool)
# 删源 mesh 对象 (面已拆进单件)
bpy.data.objects.remove(DESKS_SRC, do_unlink=True)
bpy.data.objects.remove(CHAIRS_SRC, do_unlink=True)

# ---------- 按面分材质 (单件内) ----------
# 桌: 面中心 z>=0.58, 或水平面 z>=0.50 -> 桌面木; 其余 -> 腿金属
# 椅: 面中心 z>=0.40 -> 椅面木 (座面+靠背); 其余 -> 腿金属
def assign_materials(ob, kind):
    me = ob.data
    mats = [MAT_WOOD, MAT_LEG] if kind == "desk" else [MAT_CHAIR, MAT_LEG]
    me.materials.clear()
    for m in mats:
        me.materials.append(m)
    n_wood = 0
    for poly in me.polygons:
        c = poly.center
        nz = abs(poly.normal.z)
        if kind == "desk":
            wood = (c.z >= 0.58) or (nz > 0.5 and c.z >= 0.50)
        else:
            wood = c.z >= 0.40
        poly.material_index = 0 if wood else 1
        n_wood += 1 if wood else 0
    print("%s materials: wood faces=%d metal faces=%d" % (
        ob.name, n_wood, len(me.polygons) - n_wood))

for ob, _anchor, _faces in desk_singles:
    assign_materials(ob, "desk")
for ob, _anchor, _faces in chair_pool:
    assign_materials(ob, "chair")

# ---------- 旋转 +90 度进 SPEC 朝向, 再按 SPEC 排布 ----------
# tevy (x,y) -> SPEC (-y,x): 学生由面向 +y 转为面向 -x (黑板在 -x)。
# 单件锚点 = 拆分后自身的包围盒中心 (tevy 坐标), 旋转后锚点为 (-cy, cx);
# 摆放到目标点时 object.location = 目标 - 旋转后锚点 (几何不动, 只移原点)。
ROT_Z = math.radians(90.0)
GROUP_DX = -0.14
COL_Y = [-2.8, -1.8, -0.8, 0.8, 1.8, 2.8]
ROW_X = [-3.04 + GROUP_DX + i * 1.0 for i in range(8)]
CHAIR_DX = 0.44  # 椅心离桌心 (tevy 椅靠背比 SPEC 自建椅深, 0.55 会顶东墙)

def place_singles(singles, targets, prefix):
    """singles: [(ob, tevy_anchor, faces)]; targets: [(r, c, x, y)] 48 个。
    单件循环复用 (共享网格数据)。命名沿用旧版 desk_r1_c1 / chair_r8_c6,
    scenes/classroom.py 的门洞检查 (chair_r8_ 前缀) 依赖它。返回实例列表。"""
    placed = []
    for ti, (r, c, tx, ty) in enumerate(targets):
        src_ob, (ax, ay), _faces = singles[ti % len(singles)]
        if ti < len(singles):
            ob = src_ob
        else:
            ob = src_ob.copy()
            ob.data = src_ob.data  # 共享网格
            bpy.context.collection.objects.link(ob)
        # 首次: 绕 Z 转 +90 度并烘进网格
        if ti < len(singles):
            ob.rotation_euler = (0.0, 0.0, ROT_Z)
            bpy.context.view_layer.objects.active = ob
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        # 旋转后锚点 (-ay, ax); 移到目标点
        ob.location = (tx - (-ay), ty - ax, 0.0)
        ob.name = "%s_r%d_c%d" % (prefix, r + 1, c + 1)
        placed.append(ob)
    return placed

desk_targets = [(r, c, x, y) for r, x in enumerate(ROW_X)
                for c, y in enumerate(COL_Y)]
desks = place_singles(desk_singles, desk_targets, "desk")
chair_targets = [(r, c, x + CHAIR_DX, y) for (r, c, x, y) in desk_targets]
chairs = place_singles(chair_pool, chair_targets, "chair")

print("desks:", len(desks), "chairs:", len(chairs))
print("GROUP_DX:", GROUP_DX, "CHAIR_DX:", CHAIR_DX)
print("row_x:", ROW_X)
print("col_y:", COL_Y)

# 几何自检: 桌子世界 z 应为 0~0.71, 椅子 0~0.89
bpy.context.view_layer.update()
def world_z_range(obj):
    zs = [(obj.matrix_world @ Vector(c)).z for c in obj.bound_box]
    return min(zs), max(zs)
_dz = world_z_range(desks[0])
_cz = world_z_range(chairs[0])
print("desk world z range:", _dz, "chair world z range:", _cz)
assert abs(_dz[0]) < 0.01 and abs(_dz[1] - 0.71) < 0.02, "desk z range wrong: %s" % (_dz,)
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
# tevy 单件未复用原 atlas UV（atlas 贴图已剥掉），这里补 Smart UV Project
# （_ensure_uvs：已有 UV 的不动，没有 UV 的补），木纹方可正常平铺。
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
