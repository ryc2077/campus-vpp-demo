# pv-roof v2: 屋顶面层返工 — 深灰防水卷材纹理 + 立体排水口格栅 + 女儿墙收边
# 返工目标 (筛查结论): v1 膜面均匀纯色、浅灰 #8A8F94 比鸟瞰屋顶深灰亮太多。
# v2 改动:
#   1) 面层改深灰防水卷材: 底色 #424A52 (鸟瞰屋顶深灰, 与 ov-bldA 屋顶同色),
#      卷材搭接缝 (Brick: 1m 宽卷材条、10m 长、0.02 缝) + Noise 颗粒, 全部只走 Bump。
#   2) 排水口改立体格栅: 暗色集水坑 + 金属格栅盖板 (边框 + 5 根栅条), 单 mesh/口。
#   3) 面层边缘按女儿墙厚 0.3m 收边: 膜面内缩 0.3m 贴女儿墙内侧, 另加一圈
#      深色收边压条。已核对 ov-bldA/B/C、ov-lab 四件女儿墙实测均为 0.30m,
#      压顶内挑 0.06m, 膜边与女儿墙内侧贴合, 无缝隙/无嵌入。
#   4) 面层不挡板阵列: 膜顶 A/B 18.40、实验楼 12.35; pv-panels 板底 19.15/13.15,
#      板在膜面之上 0.75m, 无遮挡。
# 导出教训 (全管线已验证): 程序化 Noise 不进 glTF; Base Color 连 MixRGB/
# ValToRGB 会丢 baseColorFactor、Godot 里变白。所以底色/粗糙度保持不链接
# (默认值=色板值), 纹理变化只走 Bump (法线)。GLB 里 baseColorFactor 保留,
# .blend 里纹理也在。
# 本次不渲染 (用户新规矩: 渲染全部走 GitHub Actions, 本地不渲染、不出预览图)。
# 几何 (Blender 坐标, SPEC + ov-bld*/ov-lab 实测):
#   A 栋 (-56, 30) 40x15m, 板顶 z=18.35, 女儿墙顶 19.0
#   B 栋 (-12, 30) 32x14m, 板顶 z=18.35, 女儿墙顶 19.0
#   实验楼 (-28, 62) 42x12m, 板顶 z=12.30, 女儿墙顶 12.95
# 屋顶楼板与女儿墙归 ov-bldA/B/C、ov-lab, 本件只做膜面/步道/排水口/收边。
import bpy, bmesh, os

BASE = os.path.expanduser("~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
BLEND = os.path.join(BASE, "assets/blender/pv/pv-roof.blend")
GLB   = os.path.join(BASE, "assets/models/pv-roof.glb")

# ---- clean scene ----
bpy.ops.wm.read_factory_settings(use_empty=True)
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def srgb_to_linear(hexstr):
    h = hexstr.lstrip('#')
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i+2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return tuple(out) + (1.0,)

def make_mat(name, hexstr, rough=0.9, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = srgb_to_linear(hexstr)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    return m

def add_bump(nt, bsdf, height_socket, strength=0.5, distance=0.05):
    b = nt.nodes.new("ShaderNodeBump")
    b.inputs["Strength"].default_value = strength
    b.inputs["Distance"].default_value = distance
    nt.links.new(height_socket, b.inputs["Height"])
    nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    return b

def membrane_mat():
    """深灰防水卷材: 底色 #424A52 不链接; Brick 卷材缝 + Noise 颗粒只进 Bump。"""
    m = make_mat("pv_roof_membrane_v2", "#424A52", rough=0.92)
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    # 卷材搭接缝: Brick, 卷材条宽 1.0m、长 10m、缝 0.02m (Object 坐标米制)
    brick = nt.nodes.new("ShaderNodeTexBrick")
    brick.inputs["Scale"].default_value = 1.0
    brick.inputs["Mortar Size"].default_value = 0.02
    brick.inputs["Brick Width"].default_value = 10.0
    brick.inputs["Row Height"].default_value = 1.0
    brick.offset = 0.0
    brick.offset_frequency = 0  # 各行不对齐错缝: 卷材条通长对齐
    nt.links.new(tc.outputs["Object"], brick.inputs["Vector"])
    # 颗粒: Noise, 尺度 3.0 (约 0.3m 一粒)
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.0
    noise.inputs["Detail"].default_value = 2.0
    noise.inputs["Roughness"].default_value = 0.8
    nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
    # 缝 (Fac: 砖=1/缝=0) 与颗粒各半权重相加 -> Bump 高度
    mul_b = nt.nodes.new("ShaderNodeMath"); mul_b.operation = "MULTIPLY"
    mul_b.inputs[1].default_value = 0.6
    nt.links.new(brick.outputs["Fac"], mul_b.inputs[0])
    mul_n = nt.nodes.new("ShaderNodeMath"); mul_n.operation = "MULTIPLY"
    mul_n.inputs[1].default_value = 0.4
    nt.links.new(noise.outputs["Fac"], mul_n.inputs[0])
    add = nt.nodes.new("ShaderNodeMath"); add.operation = "ADD"
    nt.links.new(mul_b.outputs["Value"], add.inputs[0])
    nt.links.new(mul_n.outputs["Value"], add.inputs[1])
    add_bump(nt, bsdf, add.outputs["Value"], strength=0.5, distance=0.05)
    return m

def walkway_mat():
    """检修步道: 浅色铺装 #D8D2C4, 轻微颗粒只进 Bump。"""
    m = make_mat("pv_roof_walkway_v2", "#D8D2C4", rough=0.95)
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.0
    noise.inputs["Detail"].default_value = 2.0
    noise.inputs["Roughness"].default_value = 0.8
    nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
    add_bump(nt, bsdf, noise.outputs["Fac"], strength=0.25, distance=0.04)
    return m

MAT_MEMBRANE = membrane_mat()
MAT_WALK     = walkway_mat()
MAT_EDGE     = make_mat("pv_roof_edge_trim", "#2B3138", rough=0.9)   # 收边压条深色
MAT_DRAINPIT = make_mat("pv_roof_drain_pit", "#22262B", rough=0.9)   # 集水坑暗色
MAT_GRATE    = make_mat("pv_roof_grate", "#6B7280", rough=0.5, metallic=0.6)  # 格栅金属灰

EXPORT_OBJS = []

def box(name, loc, dims, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.active_object
    o.name = name
    o.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    if bevel > 0:
        mod = o.modifiers.new("bevel", 'BEVEL')
        mod.width = bevel
        mod.segments = 2
    EXPORT_OBJS.append(o)
    return o

def _bm_box(bm, cx, cy, cz, sx, sy, sz, mat_idx):
    r = bmesh.ops.create_cube(bm, size=1.0)
    for v in r['verts']:
        v.co = (v.co.x * sx + cx, v.co.y * sy + cy, v.co.z * sz + cz)
    faces = set()
    for v in r['verts']:
        faces.update(v.link_faces)
    for f in faces:
        f.material_index = mat_idx

def drain(name, cx, cy, ztop):
    """立体排水口格栅 (单 mesh, 双材质): 0.4x0.4 集水坑 + 盖板边框 + 5 根栅条。
    盖板顶面高出膜面 0.03m, 栅条间留 0.04m 缝, 俯视可见立体格栅。"""
    mesh = bpy.data.meshes.new(name + "_mesh")
    bm = bmesh.new()
    _bm_box(bm, 0, 0, 0.01, 0.40, 0.40, 0.02, 0)          # 集水坑底板 (暗色)
    _bm_box(bm, 0, 0, 0.035, 0.36, 0.36, 0.01, 0)         # 坑内底 (暗色)
    fw = 0.04  # 边框条宽
    _bm_box(bm, 0, 0.16, 0.045, 0.36, fw, 0.03, 1)        # 盖板边框 N/S
    _bm_box(bm, 0, -0.16, 0.045, 0.36, fw, 0.03, 1)
    _bm_box(bm, 0.16, 0, 0.045, fw, 0.28, 0.03, 1)        # 盖板边框 E/W
    _bm_box(bm, -0.16, 0, 0.045, fw, 0.28, 0.03, 1)
    for gx in (-0.096, -0.048, 0.0, 0.048, 0.096):        # 5 根栅条
        _bm_box(bm, gx, 0, 0.045, 0.032, 0.28, 0.03, 1)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(MAT_DRAINPIT)
    mesh.materials.append(MAT_GRATE)
    o = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(o)
    o.location = (cx, cy, ztop)
    EXPORT_OBJS.append(o)
    return o

PARAPET_T = 0.3   # 女儿墙厚 (ov-bldA/B/C、ov-lab 实测均为 0.30m, 已核对)
MEMBRANE_T = 0.05
WALK_W = 0.8
WALK_T = 0.02
EDGE_W = 0.12     # 收边压条宽
EDGE_T = 0.012    # 收边压条厚

# (name, cx, cy, length_x, width_y, slab_top_z)
ROOFS = [
    ("A",   -56, 30, 40, 15, 18.35),
    ("B",   -12, 30, 32, 14, 18.35),
    ("lab", -28, 62, 42, 12, 12.30),
]

for tag, cx, cy, L, W, ztop in ROOFS:
    ml = L - 2 * PARAPET_T      # 膜面长: 内缩 0.3m 贴女儿墙内侧
    mw = W - 2 * PARAPET_T
    mz = ztop + MEMBRANE_T / 2
    mtop = ztop + MEMBRANE_T    # 膜顶: A/B 18.40, 实验楼 12.35
    # 1) 防水卷材面层
    box(f"pv-roof_membrane_{tag}", (cx, cy, mz), (ml, mw, MEMBRANE_T),
        MAT_MEMBRANE, bevel=0.02)
    # 2) 收边压条: 沿膜面四边、贴女儿墙内侧的一圈深色压条
    ez = mtop + EDGE_T / 2
    box(f"pv-roof_edge_{tag}_N", (cx, cy + mw / 2 - EDGE_W / 2, ez),
        (ml, EDGE_W, EDGE_T), MAT_EDGE)
    box(f"pv-roof_edge_{tag}_S", (cx, cy - mw / 2 + EDGE_W / 2, ez),
        (ml, EDGE_W, EDGE_T), MAT_EDGE)
    box(f"pv-roof_edge_{tag}_E", (cx + ml / 2 - EDGE_W / 2, cy, ez),
        (EDGE_W, mw - 2 * EDGE_W, EDGE_T), MAT_EDGE)
    box(f"pv-roof_edge_{tag}_W", (cx - ml / 2 + EDGE_W / 2, cy, ez),
        (EDGE_W, mw - 2 * EDGE_W, EDGE_T), MAT_EDGE)
    # 3) 检修步道: 南北各一条 0.8m 宽, 贴在膜面上
    walk_len = ml - 2.0
    for side in (+1, -1):
        wy = cy + side * (mw / 2 - PARAPET_T - WALK_W / 2)
        box(f"pv-roof_walkway_{tag}_{'N' if side > 0 else 'S'}",
            (cx, wy, mtop + WALK_T / 2),
            (walk_len, WALK_W, WALK_T), MAT_WALK, bevel=0.01)
    # 4) 排水口立体格栅: 每屋顶 4 个, 靠角、避开步道带
    dx = ml / 2 - 1.5
    dy = mw / 2 - 1.6
    for i, (sx, sy) in enumerate(((+1, +1), (+1, -1), (-1, +1), (-1, -1)), 1):
        drain(f"pv-roof_drain_{tag}_{i}", cx + sx * dx, cy + sy * dy, mtop)

print("EXPORT objects:", len(EXPORT_OBJS))

# ---- save .blend FIRST (落盘优先) ----
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("saved blend:", BLEND)

# ---- export .glb: only this piece's objects ----
bpy.ops.object.select_all(action='DESELECT')
for o in EXPORT_OBJS:
    o.select_set(True)
bpy.context.view_layer.objects.active = EXPORT_OBJS[0]
bpy.ops.export_scene.gltf(filepath=GLB, export_format='GLB',
                           use_selection=True, export_apply=True)
print("exported glb:", GLB)

# ---- re-import the .glb to verify it opens ----
_before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB)
_new = [o for o in bpy.data.objects if o not in _before]
print("GLB re-import ok, new objects:", len(_new))
for o in _new:
    bpy.data.objects.remove(o, do_unlink=True)

print("DONE pv-roof")
