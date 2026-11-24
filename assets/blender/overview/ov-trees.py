# ov-trees v4 (R2-T32, 2026-11-25): v3 + 密植带 3 对拉开至 2.60m（只动 3 棵旧树位置，
#   数量/模型/高度一字不改）；西沿线 3 棵经实测已在现行跑道缓冲外，不动（见下）。
# ov-trees v3 (R2-T15, 2026-11-24): 树木（总览件）— 网上现成 CC0 模型换模重建
# Blender 坐标 x 向东、y 向北、z 向上，单位米
# 内容：473 棵（新种 327 + 旧树换模 146），全部用下载的现成模型，零手搓树
#   Kenney Nature Kit (CC0 1.0, https://kenney.nl/assets/nature-kit)
#       assets/external/trees/kenney-nature-kit/*.glb（原包 ZIP 同目录，LICENSE-kenney.txt）
#       主力：全部行道树 + 楼间点缀（211 棵）+ 密植带（216 棵，KayKit 备用方案，见下）
#   Quaternius Stylized Nature MegaKit Standard (CC0 1.0, Godot 商店直链见 SOURCES.md)
#       assets/external/trees/quaternius-stylized-nature/*.gltf（+ .bin + 4 张贴图，
#       树皮/松叶贴图 2048→1024 降采样，LICENSE-Quaternius-Standard.txt）
#       仅 D3 池塘 12 棵特征树（CommonTree_3/5、Pine_4/5 各 3 棵）
# 来源偏差（诚实记录，R2-T3 方案原定来源未全部拿到直链）：
#   ① KayKit Forest Nature Pack 免费档：itch.io 免费档须走 /purchase POST 拿下载链接，
#      该 POST 触发过一次访问审批超时未应答，按指令不再重试；其余 GET 渠道（GitHub 镜像、
#      Godot 商店、AssetSifter 直链）均未找到免费档直链。密植带 104 棵新种 + 沿线 112 棵
#      旧树改用 Kenney 松树（tree_pineTall A–D 及 detailed 版 + oak/tall），同为 CC0
#      低多边形、树干 + 多层松塔冠，三角面反而更低（~78–196 vs KayKit 约 500）。
#   ② Quaternius Ultimate Nature Pack（2019）：官网下载走 Google Drive 共享文件夹，
#      实测全部文件报 "Quota exceeded"（公开配额耗尽），无法 curl 直下；改用同一作者
#      同一授权（CC0 1.0）的 Stylized Nature MegaKit Standard（Godot 商店直链可下，
#      68/116 模型），D3 仍只用 12 棵。包内无 Tree / Pine_Tree_1 / Birch_Tree_1 /
#      Tree-Stylized 这四个名字，取用等价物 CommonTree_3/5（阔叶）与 Pine_4/5（松塔）。
#   Poly Haven 树木禁用（单棵数百万 tris），未用。
# 尺寸：每个源模型先量包围盒实测高度（MEASURED 日志），再统一缩放到布局高度档
#   行道树 5–8m、密植带乔木 8–15m（D4/D5b 8–12m）、池塘特征树 8–12m、楼间点缀 4–7m。
#   布局高度逐棵见 assets/blender/overview/green_layout.json（zones[].positions [x, y, 高]）。
# 树形：树干 + 多层分层树冠（Kenney 每模型实测冠层 ≥2 档，见探针记录），树干露出地面
#   ≥1.2m（逐棵校验：crown_z0 × scale ≥ 1.2，否则换 fallback 模型）；禁止单圆锥插地
#   （tree_cone / tree_fat / tree_simple / tree_small / tree_blocks / 棕榈 / 地被松均未用）。
# 颜色：源模型自带材质直连 Base Color（Kenney 纯色 baseColorFactor；
#   Quaternius 烘焙贴图直连 Base Color + MASK alphaCutoff 0.2），无 ColorRamp——
#   F5 教训：ColorRamp 不进 glTF。导入后按材质名根去重（woodBark 等同名材质只留一份）。
# 旧树换模：146 棵位置按 v2 脚本同种子（20261122）同调用顺序复现，高度档按原分区重做
#   （沿线 8–15m、路旁 5–8m、楼间 4–7m）；L1 移位：南沿线 31 棵 y=-105 → y=-94（x 不变），
#   北沿线 (104,105)→(98,105)、(112,105)→(118,105)。L1 执行时校验发现方案未覆盖的
#   4 处冲突，本脚本一并修正（RELOC 日志逐棵列出）：①南行东端 2 棵在 y=-94 会压东主路
#   （x 102..114）→ (100,-94)/(124,-94)；②南行广场段 5 棵会压南门广场铺装（其中
#   (0,-94) 正压南门中轴）→ 移至广场两侧 y=-94（x -44/-36/-28/28/36）；③北沿线
#   移位点与抖动后邻树仅 1.7m/0.95m → 相邻 (96,105)/(120,105) 去抖动钉网格点；
#   ④楼间旧树 (0,12) 压步道 2 → (4,12)，(-80,45) 压新路 R-N1 → (-80,49)。
#   西沿线 3 棵旧树 (-120,-33/-25/-17) 在旧椭圆 (-80,-25) rx40/ry28 +3m 缓冲内（r² 0.84–0.93），
#   系 v2 原位、方案未列。R2-T32 实测：现行跑道已是 R2-T1b 新椭圆（中心 (-62,-25)、
#   rx28/ry40，禁入椭圆 +1m，见 R2-T18 §8.3；旧椭圆已废），3 棵树距新跑道西缘 -90.3
#   约 29m、缓冲归一化半径 r² 3.91–3.98（>1 即在缓冲外），已合规，不移动（见 §32）。
# 链接复制：每源模型只留一个 master mesh，其余全部 obj.copy() 共享 mesh 数据。
# 三角面预算：ov-trees GLB ≤300k tris（实测见 TREES/TRIS 日志）。
# v2 规矩保留：渲染走 GitHub Actions，本地不渲染、不出预览图（太阳/世界背景保留进 .blend，
#   相机与渲染块不建）；本脚本只建模 + 存 .blend + 导出 .glb + 回读验证。
import bpy
import json
import math
import os
import random
import re

BASE = os.path.expanduser(
    "~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
BLEND_PATH = os.path.join(BASE, "assets/blender/overview/ov-trees.blend")
GLB_PATH = os.path.join(BASE, "assets/models/ov-trees.glb")
LAYOUT_PATH = os.path.join(BASE, "assets/blender/overview/green_layout.json")
TREES_DIR = os.path.join(BASE, "assets/external/trees")

# ---- 源模型池（文件名不带扩展名；Kenney=.glb，Quaternius=.gltf） ----
STREET_MODELS = ["tree_default", "tree_oak", "tree_detailed", "tree_tall",
                 "tree_pineDefaultA", "tree_pineDefaultB", "tree_plateau",
                 "tree_thin"]
DENSE_MODELS = ["tree_pineTallA", "tree_pineTallB", "tree_pineTallC",
                "tree_pineTallD", "tree_pineTallA_detailed",
                "tree_pineTallB_detailed", "tree_pineTallC_detailed",
                "tree_pineTallD_detailed", "tree_oak", "tree_tall"]
QUAT_MODELS = ["CommonTree_3", "CommonTree_5", "Pine_4", "Pine_5"]
FALLBACK = {"street": "tree_default", "dense_belt": "tree_pineTallB",
            "feature": "Pine_4", "ornamental": "tree_default"}
POOL_BY_KIND = {"street": STREET_MODELS, "dense_belt": DENSE_MODELS,
                "feature": QUAT_MODELS, "ornamental": STREET_MODELS}
POOL_BY_SOURCE = {"kenney_nature_kit": STREET_MODELS,
                  "kaykit_forest": DENSE_MODELS,   # KayKit 未拿到直链，见文件头①
                  "quaternius_ultimate_nature": QUAT_MODELS}

# ---- 清空场景 ----
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for m in list(bpy.data.materials):
    bpy.data.materials.remove(m)
for img in list(bpy.data.images):
    bpy.data.images.remove(img)


def _mat_root(name):
    return re.sub(r"\.\d{3}$", "", name)


def dedupe_materials():
    """同名根材质只留一份（Kenney 各 GLB 自带 woodBark/leafsGreen 等同名材质）。"""
    canon = {}
    for m in list(bpy.data.materials):
        root = _mat_root(m.name)
        if root == m.name:
            canon.setdefault(root, m)
    for m in list(bpy.data.materials):
        root = _mat_root(m.name)
        if root != m.name and root in canon and canon[root] is not m:
            for o in bpy.data.objects:
                if o.type != "MESH":
                    continue
                for slot in o.material_slots:
                    if slot.material is m:
                        slot.material = canon[root]
            if m.users == 0:
                bpy.data.materials.remove(m)
    return canon


def import_model(kind, name):
    """导入一个源模型，量包围盒/三角面/冠底，返回 master 对象与实测数据。"""
    if kind == "quat":
        path = os.path.join(TREES_DIR, "quaternius-stylized-nature", name + ".gltf")
    else:
        path = os.path.join(TREES_DIR, "kenney-nature-kit", name + ".glb")
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new_objs = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new_objs if o.type == "MESH"]
    assert meshes, f"import {name}: no mesh"
    # 删导入附带的非网格对象（空父级等），网格去父级并应用变换
    for o in new_objs:
        if o.type != "MESH":
            bpy.data.objects.remove(o, do_unlink=True)
    for o in meshes:
        o.parent = None
    # 多网格（如树干/树冠分开）合并成一个 master
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    master = bpy.context.active_object
    master.name = f"Master_{name}"
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    # 实测：用 mesh 本地顶点量（不用 matrix_world @ bound_box——Kenney GLB 导入后
    # 对象自带 location.z=-0.05，包围盒 zmax 会少算 0.05m，导致全树高估约 4%
    # 如 target 15m 实成 15.63m；本地顶点 zmax 即种下后（location.z=0）的地上高度）
    vzs = [v.co.z for v in master.data.vertices]
    zmin = min(vzs)
    zmax = max(vzs)
    native_h = zmax  # 原点即地面（Kenney zmin=0；Quaternius 根系 zmin≈-0.24 埋地下）
    tris = sum(len(p.vertices) - 2 for p in master.data.polygons)
    # 冠底：叶材质面的最低 z（叶材质名含 leaf）
    crown_z0 = None
    for p in master.data.polygons:
        slot = master.material_slots[p.material_index]
        mname = slot.material.name if slot.material else ""
        if "leaf" in mname.lower():
            z0 = min(master.data.vertices[v].co.z for v in p.vertices)
            crown_z0 = z0 if crown_z0 is None else min(crown_z0, z0)
    if crown_z0 is None:
        crown_z0 = 0.5 * native_h
    mats = [s.material.name if s.material else "?" for s in master.material_slots]
    print(f"MEASURED {name}: native_h={native_h:.2f} zmin={zmin:.2f} "
          f"tris={tris} crown_z0={crown_z0:.2f} mats={mats}")
    return master, {"height": native_h, "tris": tris, "crown_z0": crown_z0}


masters = {}   # model name -> (object, measured dict)
measured = {}
for m in STREET_MODELS + [x for x in DENSE_MODELS if x not in STREET_MODELS]:
    obj, info = import_model("kenney", m)
    masters[m] = obj
    measured[m] = info
for m in QUAT_MODELS:
    obj, info = import_model("quat", m)
    masters[m] = obj
    measured[m] = info
dedupe_materials()
print(f"MASTERS: {len(masters)} models imported")
for m in sorted(bpy.data.materials, key=lambda x: x.name):
    print(f"MAT {m.name}: use_nodes={m.use_nodes}")

rng = random.Random(20261124)
used_masters = set()


def linked_copy(obj, name):
    c = obj.copy()
    c.data = obj.data  # 共享网格数据：链接复制
    bpy.context.collection.objects.link(c)
    c.name = name
    return c


def plant(idx, x, y, target_h, pool_kind):
    """种一棵树：按高度档过滤（树干露出 ≥1.2m），取 master 或链接复制，缩放至目标高。"""
    pool = POOL_BY_KIND[pool_kind]
    fallback = FALLBACK[pool_kind]
    ok = []
    for m in pool:
        s = target_h / measured[m]["height"]
        if measured[m]["crown_z0"] * s >= 1.2:
            ok.append(m)
    choices = ok if ok else [fallback]
    model = rng.choice(choices)
    s = target_h / measured[model]["height"]
    rot_z = rng.uniform(0, math.pi * 2)
    if model not in used_masters:
        obj = masters[model]
        used_masters.add(model)
    else:
        obj = linked_copy(masters[model], f"Tree_{idx:03d}")
    obj.location = (x, y, 0.0)
    obj.scale = (s, s, s)
    obj.rotation_euler = (0, 0, rot_z)
    obj.name = f"Tree_{idx:03d}_{model}"
    actual_h = measured[model]["height"] * s
    return obj, model, actual_h


# ---- 布局：新种 327 棵（green_layout.json） ----
with open(LAYOUT_PATH, encoding="utf-8") as f:
    layout = json.load(f)

planted = []       # (obj, zone_id, model, target_h, actual_h)
spot_checks = []   # 每区首棵 + 抽查
idx = 0
zone_counts = {}
for zone in layout["trees"]["zones"]:
    zid = zone["id"]
    kind = zone["kind"]
    positions = zone["positions"]
    assert len(positions) == zone["count"], f"{zid} count mismatch"
    zone_counts[zid] = {"n": len(positions), "models": {}}
    for j, (x, y, h) in enumerate(positions):
        obj, model, actual = plant(idx, x, y, h, kind)
        zone_counts[zid]["models"][model] = zone_counts[zid]["models"].get(model, 0) + 1
        planted.append((obj, zid, model, h, actual))
        if j == 0:
            spot_checks.append((zid, model, h, actual))
        idx += 1
print(f"NEW TREES: {idx} (zones {len(layout['trees']['zones'])})")
for zid, c in zone_counts.items():
    print(f"ZONE {zid}: n={c['n']} models={c['models']}")

# ---- 旧树换模 146 棵：v2 同种子同顺序复现位置，L1 移位 ----
random.seed(20261122)
spots = []   # (x, y, kind, pre_x, pre_y)
xs = [round(-120 + i * 8, 1) for i in range(31)]   # -120..120
ys = [round(-97 + i * 8, 1) for i in range(25)]    # -97..97（避开四角重复）
for x in xs:
    spots.append((x, 105, "perimeter", x, 105))
    spots.append((x, -105, "perimeter", x, -105))
for y in ys:
    spots.append((-120, y, "perimeter", -120, y))
    spots.append((120, y, "perimeter", 120, y))
n_perimeter = len(spots)
assert n_perimeter == 112, n_perimeter
spots = [(x + random.uniform(-1.2, 1.2), y + random.uniform(-1.2, 1.2), k, px, py)
         for (x, y, k, px, py) in spots]
road_spots = [(100 + random.uniform(-0.8, 0.8),
               y + random.uniform(-1.0, 1.0), "road", 100, y)
              for y in range(-90, 91, 10)]
n_road = len(road_spots)
assert n_road == 19, n_road
spots.extend(road_spots)
scattered = [
    (-80, 15), (-80, 45), (-60, 12), (-60, 48), (-40, 12),
    (-40, 48), (-32, 48), (-20, 12), (-20, 48), (0, 12),
    (0, 48), (8, 12), (20, 12), (22, 48), (40, 12),
]
assert len(scattered) == 15
spots.extend([(x, y, "scattered", x, y) for (x, y) in scattered])
assert len(spots) == 146, len(spots)

# L1 移位（GREEN_PLAN §1.2 / §3.3）+ 校验发现的 4 处追加修正（见文件头）：
#   南沿线 y=-105 → y=-94（x 不变），其中：
#     - 东端两棵 (104,-105)/(112,-105) 在 y=-94 会落在东主路（x 102..114）内，
#       改移至 (100,-94)/(124,-94)；
#     - 广场段 5 棵（x -16..16）会落在南门广场铺装（x -20..20，y -110.5..-85.5）内、
#       其中 (0,-94) 正压南门中轴，改移至广场两侧 y=-94（x -44/-36/-28/28/36，
#       与邻树 ≥2.8m）；
#   北沿线 (104,105)→(98,105)、(112,105)→(118,105)（照方案），另把相邻两棵
#   (96,105)/(120,105) 去抖动钉到网格点——否则与移位树仅 1.7m/0.95m（实测）。
#   楼间两棵旧树亦压路：(0,12) 压步道 2（x=0 宽 3m）→ (4,12)；
#   (-80,45) 压新路 R-N1（y=44 宽 3m）→ (-80,49)。
#   另：西沿线 3 棵旧树 (-120,-33/-25/-17) 在旧椭圆 +3m 缓冲内（但在跑道面外），
#   系 v2 原位、方案未列；R2-T32 实测现行新跑道（中心 (-62,-25) rx28/ry40 +1m）
#   下 r² 3.91–3.98，已在缓冲外，不移动（见文件头）。
# R2-T32：D1/旧沿线 3 对间距 1.56–1.81m → 旧树东移，距 D1 伙伴 2.60m（y 不变，
#   仍在密植带内、不压路/缓冲；键为抖动前坐标，值为 D1 伙伴 y）：
R32_D1 = {(120, -41): -40.5, (120, 79): 78.5, (120, -89): -89.5}
PLAZA_FLANK = {-16: -28, -8: -36, 0: -44, 8: 28, 16: 36}
relocated = []
fixed = []
for (x, y, k, px, py) in spots:
    if k == "perimeter" and py == -105 and px in (104, 112):
        nx = 100.0 if px == 104 else 124.0
        fixed.append((nx, -94.0, k))
        relocated.append((px, py, nx, -94.0, "L1-east-end-off-road"))
    elif k == "perimeter" and py == -105 and px in PLAZA_FLANK:
        nx = float(PLAZA_FLANK[px])
        fixed.append((nx, -94.0, k))
        relocated.append((px, py, nx, -94.0, "L1-plaza-flank"))
    elif k == "perimeter" and py == -105:
        fixed.append((x, -94.0, k))
        relocated.append((px, py, x, -94.0, "L1-south-row"))
    elif k == "perimeter" and (px, py) == (104, 105):
        fixed.append((98.0, 105.0, k))
        relocated.append((px, py, 98.0, 105.0, "L1-north"))
    elif k == "perimeter" and (px, py) == (112, 105):
        fixed.append((118.0, 105.0, k))
        relocated.append((px, py, 118.0, 105.0, "L1-north"))
    elif k == "perimeter" and (px, py) in R32_D1:
        d1y = R32_D1[(px, py)]
        nx = 117.5 + math.sqrt(2.6 ** 2 - (y - d1y) ** 2)
        fixed.append((nx, y, k))
        relocated.append((px, py, round(nx, 2), round(y, 2), "R2-T32-dense-pair-2.6m"))
    elif k == "perimeter" and (px, py) in ((96, 105), (120, 105)):
        fixed.append((float(px), float(py), k))  # 去抖动钉网格点（保与 L1 移位树 ≥2m）
        relocated.append((px, py, float(px), float(py), "L1-dejitter"))
    elif k == "scattered" and (px, py) == (0, 12):
        fixed.append((4.0, 12.0, k))
        relocated.append((px, py, 4.0, 12.0, "walkway2"))
    elif k == "scattered" and (px, py) == (-80, 45):
        fixed.append((-80.0, 49.0, k))
        relocated.append((px, py, -80.0, 49.0, "newroad-R-N1"))
    else:
        fixed.append((x, y, k))
print(f"L1+R2-T32 RELOCATED: {len(relocated)}")
for r in relocated:
    print(f"  RELOC {r[0]},{r[1]} -> {r[2]},{r[3]} ({r[4]})")

rng_h = random.Random(20261124)
HEIGHT_OLD = {"perimeter": (8.0, 15.0), "road": (5.0, 8.0),
              "scattered": (4.0, 7.0)}
POOL_OLD = {"perimeter": "dense_belt", "road": "street",
            "scattered": "ornamental"}
old_counts = {"perimeter": 0, "road": 0, "scattered": 0}
for (x, y, k) in fixed:
    lo, hi = HEIGHT_OLD[k]
    h = rng_h.uniform(lo, hi)
    obj, model, actual = plant(idx, x, y, h, POOL_OLD[k])
    old_counts[k] += 1
    planted.append((obj, "OLD-" + k, model, h, actual))
    idx += 1
print(f"OLD RESKIN: {sum(old_counts.values())} {old_counts}")
print(f"TREES TOTAL: {len(planted)} (new 327 + old 146)")

# ---- 高度抽查：每区首棵 + 旧树各区首棵（实测缩放后高度必须在档内） ----
ok_check = True
for zid, model, target, actual in spot_checks:
    print(f"CHECK {zid}: model={model} target={target:.1f} actual={actual:.2f}")
# 全量校验：actual 必须等于 target（构造保证），且在分区档内
for (obj, zid, model, target, actual) in planted:
    if abs(actual - target) > 0.01:
        ok_check = False
        print(f"HEIGHT MISMATCH {obj.name}: target={target} actual={actual}")
assert ok_check, "height check failed"

# ---- 三角面统计（按导出展开计：共享 mesh 每实例计一次） ----
total_tris = 0
for (obj, zid, model, target, actual) in planted:
    total_tris += sum(len(p.vertices) - 2 for p in obj.data.polygons)
print(f"TRIS TOTAL: {total_tris} (budget <= 300000)")
assert total_tris <= 300000, f"tris over budget: {total_tris}"
by_source = {"kenney": 0, "quaternius": 0}
for (obj, zid, model, target, actual) in planted:
    by_source["quaternius" if model in QUAT_MODELS else "kenney"] += 1
print(f"BY SOURCE: kenney={by_source['kenney']} quaternius={by_source['quaternius']}")

# ---- 光照：太阳 3.5，自西南，仰角约 50 度（进 .blend，不渲染） ----
sun_data = bpy.data.lights.new("Sun", type="SUN")
sun_data.energy = 3.5
sun_data.use_shadow = True
sun = bpy.data.objects.new("Sun", sun_data)
bpy.context.collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), 0, math.radians(225))

# ---- 世界背景：淡蓝纯色 ----
world = bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.65, 0.78, 0.88, 1.0)
bg.inputs["Strength"].default_value = 1.0

objs = [o for (o, _, _, _, _) in planted]

# ---- 存盘 ----
os.makedirs(os.path.dirname(BLEND_PATH), exist_ok=True)
os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)

# ---- 导出 GLB：只选本件 ----
bpy.ops.object.select_all(action="DESELECT")
for o in objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format="GLB",
                          use_selection=True, export_apply=True)

# ---- 回读 GLB 确认 ----
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB_PATH)
imported = [o for o in bpy.data.objects if o not in before]
print(f"GLB reimport OK: {len(imported)} objects")
n_trees = len([o for o in imported if o.name.startswith("Tree_")])
print(f"GLB reimport trees: {n_trees} tree objects")
assert n_trees == 473, f"reimport tree count {n_trees} != 473"
for m in sorted({o.active_material for o in imported if o.active_material},
                key=lambda m: m.name):
    has_img = any(n.type == "TEX_IMAGE" for n in m.node_tree.nodes) if m.use_nodes else False
    base = None
    if m.use_nodes:
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        if bsdf is not None:
            base = tuple(round(v, 4) for v in bsdf.inputs["Base Color"].default_value[:3])
    print(f"GLB MAT {m.name}: has_image_texture={has_img} base_color_linear={base}")
for o in imported:
    bpy.data.objects.remove(o, do_unlink=True)

# ---- 删 .blend1 ----
blend1 = BLEND_PATH + "1"
if os.path.exists(blend1):
    os.remove(blend1)

print("DONE ov-trees v4")
