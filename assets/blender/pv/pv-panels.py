# pv-panels v2: 光伏板阵列返工 (A栋/B栋/实验楼屋顶)
# 只做板本身: 不做支架/逆变器/屋顶面层
# 规约: SPEC.md; 单位米; Blender x东 y北 z上
# v2 返工点 (筛查结论: 旧版板面均匀深蓝、无电池片明暗、无玻璃反光):
#  ① 电池片纹理: Noise + Voronoi 电池片 + Brick 细栅线, 只走 Bump(法线)
#  ② 玻璃反光: 板面之上加一层淡蓝灰透明玻璃盖板 (alpha 0.35, 粗糙度 0.08,
#     Specular IOR 1.0) + Eevee 开 Screen Space Reflections + 每栋屋顶一个
#     Reflection Cubemap, 不再是一块平蓝板
#  ③ 板框(旧版已有) + 新增背面接线盒
#  ④ 铺设数 548 块 (A 222 / B 156 / 实验楼 170): 2026-11-22 PV 修复删 A 北行
#     两块角部板 PV_A_06_00 / PV_A_06_31 —— 与逆变器 A1/A2 平面重叠约 0.2m
#     (A1 东缘 -74.50 vs 首列板西缘 -74.70; A2 西缘 -37.50 vs 末列板东缘
#     -37.30), 同排无空位可挪 (A 行 32 列排满, B/实验楼端隙 < 板宽 1.134m)。
#     原 550 块 (A 224) 已作废。
#     (brief 名义数 300/220/250 是算错的: 300块x2㎡=600㎡等于A栋整面屋顶,
#      留缝和检修道排不下)
# 穿插修正 (2026-11-23 pv 拼装顶点级检查): A 栋南排 row 00 低边埋进南女儿墙
#     0.26m、北排 row 06 顶边擦北女儿墙压顶 0.25-0.26m。本次只移 A 栋两排的 y:
#     row 00 向北 +0.35m (0.26 穿插 + 0.09 余量, 低边 y 22.85 -> 23.20,
#     离南墙内面 23.10 余 0.10m)、row 06 向南 -0.35m (顶边 y 37.15 -> 36.80,
#     离北压顶内挑 36.84 余 0.04m); 其余排、其余栋一概不动, 总数仍 548 块。
# 基准修正 (2026-11-22 PV 修复, 按 pv-roof 为准): 屋顶 datum 由 19/13 改为
# 板顶面 18.35/12.30 (A/B 下调 0.65m, 实验楼下调 0.70m); 膜顶 18.40/12.35,
# 板底 = datum+0.15, 即膜面上 0.10m。女儿墙顶 A/B 19.00 / 实验楼 12.95。
# 管线教训 (必须遵守):
#  程序化 Noise 节点不进 glTF 导出, 且 Base Color 连 MixRGB/ValToRGB 时
#  导出器会丢 baseColorFactor、Godot 里变白。所以底色/粗糙度/金属度/
#  高光/透明度一律保持不链接 (默认值=色板值), 纹理变化只走 Bump。
# 渲染全部走 GitHub Actions, 本地不渲染: 本脚本不建相机/太阳/世界背景,
#  不出预览图, 只建模 -> 存 .blend -> 导出 .glb -> 回读验证。
import bpy
import bmesh
import math
import os
from mathutils import Vector

BASE = os.path.expanduser("~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
BLEND = os.path.join(BASE, "assets/blender/pv/pv-panels.blend")
GLB = os.path.join(BASE, "assets/models/pv-panels.glb")

# ---- 清场 ----
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for m in list(bpy.data.meshes):
    bpy.data.meshes.remove(m)

# ---- 材质 (只用 Principled BSDF; Base Color/Roughness/Metallic/Specular/
#      Alpha 一律只设 default_value, 不连任何节点, 保证 glTF baseColorFactor 保留) ----
def principled(name, rgb, metallic, roughness, alpha=1.0, specular=0.5):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Alpha"].default_value = alpha
    try:
        bsdf.inputs["Specular IOR Level"].default_value = specular
    except Exception as e:
        print(f"WARN specular input: {e}")
    return mat

def srgb(hexstr):
    """十六进制 sRGB -> 线性值 (Principled Base Color 要线性值, 直接赋 sRGB 会洗白)"""
    h = hexstr.lstrip('#')
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i+2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return tuple(out)

# 板面: 深蓝灰 (比旧版 #1A2F4A 略亮, 配合玻璃盖板呈淡蓝灰反光), 低粗糙度+满高光=玻璃感
MAT_PANEL = principled("PV_PanelBlue", srgb("2C4A68"), 0.15, 0.18, specular=1.0)
MAT_FRAME = principled("PV_FrameSilver", srgb("C0C5C9"), 0.8, 0.30)
MAT_BUS = principled("PV_Busbar", srgb("7E93A8"), 0.6, 0.40)
# 玻璃盖板: 淡蓝灰 #9FC3D8, 透明 alpha 0.35, 粗糙度 0.08, 满高光
MAT_GLASS = principled("PV_Glass", srgb("9FC3D8"), 0.0, 0.08, alpha=0.35, specular=1.0)
try:
    MAT_GLASS.surface_render_method = 'BLENDED'
except Exception:
    try:
        MAT_GLASS.blend_method = 'BLEND'
    except Exception as e:
        print(f"WARN glass blend method: {e}")
# 接线盒: 深灰
MAT_JBOX = principled("PV_JunctionBox", srgb("2A2E33"), 0.2, 0.60)

# ---- ① 电池片纹理: 只走 Bump (法线), 不连 Base Color / Roughness ----
# 节点链: Generated 坐标 -> Mapping(6,10,1: 6列x10行电池片)
#   -> Voronoi(每片随机色=片间深浅) + Noise(颗粒) + Brick(栅线/片缝)
#   -> Math 相加 -> Bump -> Principled Normal
nt = MAT_PANEL.node_tree
bsdf = nt.nodes["Principled BSDF"]
texcoord = nt.nodes.new("ShaderNodeTexCoord")
mapping = nt.nodes.new("ShaderNodeMapping")
mapping.inputs["Scale"].default_value = (6.0, 10.0, 1.0)   # 6 列 x 10 行电池片
mapping2 = nt.nodes.new("ShaderNodeMapping")
mapping2.inputs["Scale"].default_value = (12.0, 18.0, 1.0)
noise = nt.nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 5.0
noise.inputs["Detail"].default_value = 2.0
noise.inputs["Roughness"].default_value = 0.7
voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
voronoi.feature = 'F1'
voronoi.distance = 'EUCLIDEAN'
voronoi.inputs["Scale"].default_value = 1.0
voronoi.inputs["Randomness"].default_value = 0.9
brick = nt.nodes.new("ShaderNodeTexBrick")
brick.inputs["Scale"].default_value = 1.0
brick.inputs["Mortar Size"].default_value = 0.015
brick.inputs["Mortar Smooth"].default_value = 0.0
brick.inputs["Bias"].default_value = 0.0
brick.inputs["Brick Width"].default_value = 0.5
brick.inputs["Row Height"].default_value = 0.5
m_add1 = nt.nodes.new("ShaderNodeMath")
m_add1.operation = 'ADD'
m_sub = nt.nodes.new("ShaderNodeMath")
m_sub.operation = 'SUBTRACT'
m_sub.inputs[0].default_value = 1.0
m_mul = nt.nodes.new("ShaderNodeMath")
m_mul.operation = 'MULTIPLY'
m_mul.inputs[1].default_value = 0.4
m_add2 = nt.nodes.new("ShaderNodeMath")
m_add2.operation = 'ADD'
bump = nt.nodes.new("ShaderNodeBump")
bump.inputs["Strength"].default_value = 0.5
bump.inputs["Distance"].default_value = 0.02
L = nt.links.new
L(texcoord.outputs["Generated"], mapping.inputs["Vector"])
L(texcoord.outputs["Generated"], mapping2.inputs["Vector"])
L(mapping.outputs["Vector"], voronoi.inputs["Vector"])
L(mapping.outputs["Vector"], brick.inputs["Vector"])
L(mapping2.outputs["Vector"], noise.inputs["Vector"])
L(noise.outputs["Fac"], m_add1.inputs[0])
L(voronoi.outputs["Color"], m_add1.inputs[1])   # 每片随机色 -> 片间深浅 (只进 Bump)
L(brick.outputs["Fac"], m_sub.inputs[1])        # 砖缝 = 细栅线/片缝
L(m_sub.outputs[0], m_mul.inputs[0])
L(m_add1.outputs[0], m_add2.inputs[0])
L(m_mul.outputs[0], m_add2.inputs[1])
L(m_add2.outputs[0], bump.inputs["Height"])
L(bump.outputs["Normal"], bsdf.inputs["Normal"])
print("MATERIAL PV_PanelBlue: Bump chain = Noise + Voronoi cells + Brick gridlines; "
      "Base Color/Roughness unlinked (defaults kept for glTF)")

# ---- 主板 mesh: 1.134 x 1.762 x 0.035, 银框 + 4 条横向汇流条
#      + 玻璃盖板 + 背面接线盒 (同 mesh, 548 块实例共享, 不增对象数) ----
PW, PL, PT = 1.134, 1.762, 0.035

def add_box(bm, cx, cy, cz, sx, sy, sz, mat_idx):
    r = bmesh.ops.create_cube(bm, size=1.0)
    for v in r['verts']:
        v.co = (v.co.x * sx + cx, v.co.y * sy + cy, v.co.z * sz + cz)
    faces = set()
    for v in r['verts']:
        faces.update(v.link_faces)
    for f in faces:
        f.material_index = mat_idx

mesh = bpy.data.meshes.new("PV_PanelMesh")
bm = bmesh.new()
add_box(bm, 0, 0, 0, PW, PL, PT, 0)                                  # 板体
fx = PW / 2 - 0.025
add_box(bm, -fx, 0, 0.0025, 0.05, PL, 0.05, 1)                       # 长边框 x2
add_box(bm, fx, 0, 0.0025, 0.05, PL, 0.05, 1)
fy = PL / 2 - 0.025
add_box(bm, 0, -fy, 0.0025, PW - 0.10, 0.05, 0.05, 1)                # 短边框 x2
add_box(bm, 0, fy, 0.0025, PW - 0.10, 0.05, 0.05, 1)
for by in (-0.66, -0.22, 0.22, 0.66):                                # 横向汇流条 x4
    add_box(bm, 0, by, 0.0205, PW - 0.10, 0.03, 0.006, 2)
add_box(bm, 0, 0, 0.020, PW - 0.02, PL - 0.02, 0.006, 3)             # ② 玻璃盖板
add_box(bm, 0, 0, -PT / 2 - 0.025, 0.20, 0.14, 0.05, 4)              # ③ 背面接线盒
bm.to_mesh(mesh)
bm.free()
mesh.materials.append(MAT_PANEL)
mesh.materials.append(MAT_FRAME)
mesh.materials.append(MAT_BUS)
mesh.materials.append(MAT_GLASS)
mesh.materials.append(MAT_JBOX)

# ---- 布阵 (A 北行两角已删板, 其余与 v1 相同, 共 548 块) ----
# 倾角 15 度朝南(朝 -y): 绕 X 轴 +15 度, 北边(+y)翘起
TILT = math.radians(15.0)
# 板底留 0.15m 空隙: 板中心高度 = 屋顶 z + 0.15 + (PL/2)*sin15 + PT/2
CENTER_H = 0.15 + (PL / 2) * math.sin(TILT) + PT / 2
PITCH_X = 1.17   # 列距 (板宽 1.134 + 0.036 缝)
PITCH_Y = 1.80   # 行距 (投影长 1.70 + 0.10 缝)
AISLE = 0.90     # 每 3 行后一条检修道

panels = []

def layout_roof(name, cx, cy, roof_z, ncols, nrows, skip=frozenset(), row_dy=None):
    # skip: (行, 列) 集合, 被跳过的板位不建板。2026-11-22: A 北行两角
    # (6,0)/(6,31) 与逆变器 A1/A2 平面重叠约 0.2m, 同排无空位, 直接删板。
    # row_dy: {行: y 方向移动量}, 2026-11-23 穿插修正只用于 A 栋两端排
    # (row 00 +0.35 / row 06 -0.35), 其余行、其余栋传 None, 一概不动。
    # 行: 3 行一组, 组间加检修道
    row_y = []
    y = cy - ( (nrows - 1) * PITCH_Y + ((nrows - 1) // 3) * AISLE ) / 2
    for r in range(nrows):
        row_y.append(y)
        y += PITCH_Y
        if (r + 1) % 3 == 0 and r != nrows - 1:
            y += AISLE
    n = 0
    for r, ry in enumerate(row_y):
        ry_eff = ry + (row_dy or {}).get(r, 0.0)
        for c in range(ncols):
            if (r, c) in skip:
                print(f"SKIP {name} r{r:02d} c{c:02d}: removed (clash with inverter)")
                continue
            x = cx + (c - (ncols - 1) / 2) * PITCH_X
            obj = bpy.data.objects.new(f"PV_{name}_{r:02d}_{c:02d}", mesh)
            bpy.context.collection.objects.link(obj)
            obj.location = (x, ry_eff, roof_z + CENTER_H)
            obj.rotation_euler = (TILT, 0.0, 0.0)
            panels.append(obj)
            n += 1
    print(f"ROOF {name}: {n} panels ({ncols} cols x {nrows} rows)")
    return n

# 屋顶数据 (Blender 中心, 屋顶 z = pv-roof 板顶面, 屋面尺寸)
# A栋 (-56,30) z=18.35 40x15 ; B栋 (-12,30) z=18.35 32x14 ; 实验楼 (-28,62) z=12.30 42x12
nA = layout_roof("A", -56, 30, 18.35, 32, 7, skip={(6, 0), (6, 31)},
                   row_dy={0: 0.35, 6: -0.35})
nB = layout_roof("B", -12, 30, 18.35, 26, 6)
nL = layout_roof("LAB", -28, 62, 12.30, 34, 5)
TOTAL = nA + nB + nL
print(f"TOTAL panels: {TOTAL} (A={nA} B={nB} LAB={nL})")
assert TOTAL == 548 and (nA, nB, nL) == (222, 156, 170), "panel count changed!"

# ---- ② 玻璃反光: Eevee 开 Screen Space Reflections + 每栋屋顶一个 Reflection Cubemap ----
# (不渲染预览, 只把设置留在工程里供 GitHub Actions 渲染用; Cubemap 不参与 GLB 导出)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT'
try:
    scene.eevee.use_ssr = True
    print(f"Eevee SSR: {scene.eevee.use_ssr}")
except Exception as e:
    print(f"WARN eevee.use_ssr not available: {e}")
try:
    scene.eevee.use_ssr_halfres = False
except Exception:
    pass
probes = []
for pname, (px, py, pz) in {"A": (-56, 30, 20.35), "B": (-12, 30, 20.35),
                            "LAB": (-28, 62, 14.30)}.items():  # datum+2.0, 随 datum 下调
    try:
        pdata = bpy.data.lightprobes.new(f"PV_Probe_{pname}", 'SPHERE')
        pdata.influence_distance = 30.0
        pdata.clip_start = 0.1
        pdata.clip_end = 60.0
        pobj = bpy.data.objects.new(f"PV_Probe_{pname}", pdata)
        bpy.context.collection.objects.link(pobj)
        pobj.location = (px, py, pz)
        probes.append(pobj)
        print(f"Reflection Cubemap {pname} at ({px}, {py}, {pz})")
    except Exception as e:
        print(f"WARN cubemap {pname}: {e}")

# ---- 先存盘 .blend (落盘优先), 再导出 ----
for o in panels:
    o.select_set(True)
bpy.context.view_layer.objects.active = panels[0]
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print(f"Saved blend: {BLEND}")

# ---- 导出 GLB (只选本件对象: 548 块板; Cubemap 不选中, 不进导出) ----
for p in probes:
    p.select_set(False)
bpy.ops.export_scene.gltf(
    filepath=GLB, export_format='GLB',
    use_selection=True, export_apply=True)

# ---- 回读 GLB 验证 ----
before = set(bpy.data.objects.keys())
bpy.ops.import_scene.gltf(filepath=GLB)
after = set(bpy.data.objects.keys())
imported = after - before
imported_pv = [n for n in imported if n.startswith("PV_")]
print(f"GLB reimport OK: {len(imported)} objects, PV panels: {len(imported_pv)}")
assert len(imported_pv) == 548, f"GLB panel count mismatch: {len(imported_pv)} != 548"

print("DONE pv-panels")
