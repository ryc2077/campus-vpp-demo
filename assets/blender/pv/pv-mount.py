# pv-mount v2: 光伏支架边框 (A栋/B栋/实验楼屋顶) —— 返工版
# 返工目标: ① 去掉旧版中央深蓝实心示意板(支架本身是主角, 不再放示意板);
# ② 按真实结构做: 横梁 + 纵梁 + 支腿(单向斜撑) + 横拉杆 + 压块 + 螺栓点;
# ③ 支腿/横梁材质分开; ④ 所有面不许全平(横梁顶加凸筋、螺栓/压块破面、
#    金属拉丝走 Bump 法线)。
# 材质教训(已验证): 程序化 Noise 不进 glTF; Base Color 连 MixRGB/ValToRGB 会丢
# baseColorFactor。所以底色/粗糙度保持不链接(默认值=色板值), 纹理变化只走
# Bump(法线), GLB 里 baseColorFactor 保留、.blend 里纹理也在。
# 不做板本身(pv-panels)/屋顶面层(pv-roof)/逆变器线缆(pv-inverter)。
# 不做小倒角(保合并性能), 保持合并做法。
# 本次不渲染预览图(渲染全部走 GitHub Actions): 只建模→存 .blend→导出 .glb→回读验证。
# 规约: SPEC.md; 单位米; Blender x东 y北 z上
# 排布与 pv-panels.py 完全一致: 行距 1.80m, 列距 1.17m, 倾角 15度朝南, 板底离屋顶 0.15m
# 基准修正 (2026-11-22 PV 修复, 按 pv-roof 板顶面为准): datum 19/13 -> 18.35/12.30
# (A/B 下调 0.65m, 实验楼下调 0.70m); A 北行两角板已删, 对应压块/螺柱同步跳过。
# 横梁缩短 (2026-11-22): A 北行(r06)两角板已删, 该行横梁按实际板列(c01..c30)
# 算 row_len, 两端各缩 1.17m 与新端板对齐(悬伸 0.03m); 其余行 row_len 不变。
# 穿插修正 (2026-11-23 pv 拼装顶点级检查): A 栋南沿轨道埋进南女儿墙
# (2022 顶点)、北沿 816 顶点擦北女儿墙压顶; 脚板底 z=板顶, 陷进膜面 0.05m。
# 本次: ① A 栋两端行横梁/支腿/压块跟随板同步内移 (row 00 +0.35 / row 06
# -0.35, 与 pv-panels 同量), 其余行、其余栋不动; ② 脚板底/支腿底/地脚螺栓
# 一律抬到膜顶之上 (膜顶 = 板顶 +0.05, A/B 18.40、实验楼 12.35, 脚底 18.405/
# 12.405); ③ A 南排 row 00 南轨斜撑外伸单用 0.25m (见 build_roof 内注释),
# 否则脚板南缘仍擦墙 (只差 1mm)。
import bpy
import bmesh
import math
import os
from mathutils import Vector, Matrix, Euler

BASE = os.path.expanduser("~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
BLEND = os.path.join(BASE, "assets/blender/pv/pv-mount.blend")
GLB = os.path.join(BASE, "assets/models/pv-mount.glb")

# ---- 清场 ----
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for m in list(bpy.data.meshes):
    bpy.data.meshes.remove(m)

# ---- 材质 (只用 Principled BSDF; 底色/粗糙度不链接, 拉丝只走 Bump) ----
def srgb(hexstr):
    """十六进制 sRGB -> 线性值 (Principled Base Color 要线性值, 直接赋 sRGB 会洗白)"""
    h = hexstr.lstrip('#')
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i+2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return tuple(out)

def brushed_metal(name, hexstr, metallic, roughness,
                  noise_scale, bump_strength, map_scale):
    """拉丝金属: 底色/金属度/粗糙度取默认值(不链接, 保证 glTF baseColorFactor);
    拉丝纹理 = TexCoord(Generated) -> Mapping(沿一轴拉长) -> Noise -> Bump -> Normal"""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*srgb(hexstr), 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    tex = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = map_scale
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = noise_scale
    noise.inputs["Detail"].default_value = 2.0
    noise.inputs["Roughness"].default_value = 0.7
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = bump_strength
    bump.inputs["Distance"].default_value = 0.02
    nt.links.new(tex.outputs["Generated"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat

# 横梁/纵梁: 镀锌亮银; 支腿/脚板/拉杆: 深灰钢(分开材质); 压块: 深灰阳极;
# 螺栓: 亮银高金属
MAT_RAIL = brushed_metal("PV_RailSteel", "B9BEC2", 0.85, 0.35,
                         8.0, 0.25, (1.0, 24.0, 24.0))
MAT_LEG = brushed_metal("PV_LegSteel", "6E7478", 0.70, 0.45,
                        5.0, 0.35, (1.0, 12.0, 12.0))
MAT_CLAMP = brushed_metal("PV_ClampDark", "3A3F44", 0.60, 0.50,
                          6.0, 0.20, (4.0, 4.0, 4.0))
MAT_BOLT = brushed_metal("PV_BoltBright", "C0C5C9", 0.90, 0.30,
                         10.0, 0.15, (6.0, 6.0, 6.0))
MATS = [MAT_RAIL, MAT_LEG, MAT_CLAMP, MAT_BOLT]
I_RAIL, I_LEG, I_CLAMP, I_BOLT = 0, 1, 2, 3

# ---------- PBR 贴图（2026-11-24 v3b：挂下载的 CC0 贴图，替代纯色） ----------
# blue_metal_plate 按 SPEC 色染色（rail #B9BEC2 / leg #6E7478），Base Color+
# Roughness+Normal 三件套节点直连 BSDF；旧 Noise 拉丝 Bump 链接由 add_pbr 断开
# （孤节点留在 .blend 里，不进 glTF）。CLAMP/BOLT 不在本次 8 材质内，保持纯色。
TEX_DIR = os.path.join(BASE, "assets/blender/pv/pv-mount_textures")

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

add_pbr(MAT_RAIL, "rail_color.jpg", "rail_rough.jpg", "rail_nor.jpg")
_check_pbr(MAT_RAIL)
add_pbr(MAT_LEG, "leg_color.jpg", "leg_rough.jpg", "leg_nor.jpg")
_check_pbr(MAT_LEG)

# ---- 与 pv-panels.py 相同的板参数与布阵 ----
PW, PL, PT = 1.134, 1.762, 0.035
TILT = math.radians(15.0)
CENTER_H = 0.15 + (PL / 2) * math.sin(TILT) + PT / 2   # 板中心离屋顶高度
PITCH_X = 1.17
PITCH_Y = 1.80
AISLE = 0.90

def row_ys(cy, nrows):
    ys = []
    y = cy - ((nrows - 1) * PITCH_Y + ((nrows - 1) // 3) * AISLE) / 2
    for r in range(nrows):
        ys.append(y)
        y += PITCH_Y
        if (r + 1) % 3 == 0 and r != nrows - 1:
            y += AISLE
    return ys

# ---- bmesh helpers ----
def add_box(bm, mat4, sx, sy, sz, mat_idx):
    r = bmesh.ops.create_cube(bm, size=1.0)
    for v in r['verts']:
        v.co = mat4 @ Vector((v.co.x * sx, v.co.y * sy, v.co.z * sz))
    faces = set()
    for v in r['verts']:
        faces.update(v.link_faces)
    for f in faces:
        f.material_index = mat_idx

def add_prism(bm, mat4, diameter, depth, mat_idx, segments=6):
    """六棱螺栓头/螺柱: 轴沿局部 z, 原点在底面中心"""
    r = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False,
                              segments=segments, radius1=diameter / 2,
                              radius2=diameter / 2, depth=depth)
    for v in r['verts']:
        v.co = mat4 @ Vector((v.co.x, v.co.y, v.co.z + depth / 2))
    faces = set()
    for v in r['verts']:
        faces.update(v.link_faces)
    for f in faces:
        f.material_index = mat_idx

def tilt_mat(loc):
    """绕 X 轴 +15 度的板面坐标系, 原点在 loc"""
    return Matrix.Translation(Vector(loc)) @ Euler((TILT, 0.0, 0.0)).to_matrix().to_4x4()

# ---- 结构尺寸 ----
RAIL_DY = 0.55          # 横梁位于板面局部 y=±0.55
RAIL_H = 0.05           # 横梁截面高
RAIL_W = 0.06           # 横梁截面宽(板面方向)
RIB_W, RIB_H = 0.02, 0.012   # 横梁顶凸筋(破平板面)
PURL_SECT = 0.05        # 纵梁截面(沿坡向, 宽 x)
PURL_H = 0.04           # 纵梁截面高
LEG_SECT = 0.05
LEG_BASE_OFF = 0.35     # 支腿底座相对横梁垂点向南偏移, 形成单向斜撑
LEG_STEP = 2.34         # 约 2.3m 一站
TIE_SECT = 0.04         # 横拉杆截面
FOOT = 0.14             # 脚板边长

mount_objs = []

def build_roof(name, cx, cy, roof_z, ncols, nrows, row_dy=None):
    # row_dy: {行: y 方向移动量}, 2026-11-23 穿插修正: A 栋两端行跟随板同步
    # 内移 (row 00 +0.35 / row 06 -0.35), 其余行、其余栋传 None, 一概不动。
    # 膜顶 = 板顶面 +0.05 (A/B 18.40, 实验楼 12.35): 脚板底/支腿底/螺栓一律
    # 落在膜顶之上, 不再陷进膜面 (旧版脚底 z=板顶, 陷 0.05m; 支腿最低角 18.34)。
    MEMB = roof_z + 0.05
    FOOT_Z = MEMB + 0.015    # 脚板中心 (厚 0.02, 底面 = 膜顶 +0.005)
    LEG_BASE_Z = MEMB + 0.035  # 支腿底端面中心 (斜腿截面最低角仍高于膜顶约 0.013)
    BOLT_Z = MEMB + 0.025    # 脚板螺栓底面 = 脚板顶面 (MEMB+0.02, 向上留 0.005)
    mesh = bpy.data.meshes.new(f"PV_MountMesh_{name}")
    bm = bmesh.new()
    n_rail = n_purl = n_leg = n_tie = n_clamp = n_bolt = 0
    st_counts = []
    for ri, ry in enumerate(row_ys(cy, nrows)):
        ry = ry + (row_dy or {}).get(ri, 0.0)
        # 南侧斜撑外伸量: A 南排 row 00 南轨若仍用 0.35, 脚板南缘
        # y = 24.05-0.531-0.35-0.07 = 23.099, 仍擦女儿墙 (墙内面 23.10 /
        # 压顶外挑 23.16, 只差 1mm), 故该轨单用 0.25 (脚板南缘 23.20,
        # 离压顶外挑余 0.04m); 其余轨一律 0.35, 横梁/压块仍与板对齐。
        off_s = 0.25 if (name == "A" and ri == 0) else LEG_BASE_OFF
        off_n = LEG_BASE_OFF
        # -- 该行实际板列(与 pv-panels 的删板同步: A 北行跳过 c0/c31) --
        #    横梁跨度按实际板列算, 不写死: row_len=(末列-首列)*列距+板宽,
        #    行中心取实际首末列的中点(对称删角时仍为 cx)。
        cols = [c for c in range(ncols)
                if not (name == "A" and ri == nrows - 1 and c in (0, ncols - 1))]
        row_len = (cols[-1] - cols[0]) * PITCH_X + PW
        row_cx = cx + ((cols[0] + cols[-1]) / 2 - (ncols - 1) / 2) * PITCH_X
        n_stations = int(row_len // LEG_STEP) + 1
        st_counts.append(n_stations)
        st_x0 = row_cx - row_len / 2 + 0.3
        st_x1 = row_cx + row_len / 2 - 0.3
        st_xs = [st_x0 + (st_x1 - st_x0) * i / (n_stations - 1) for i in range(n_stations)] \
            if n_stations > 1 else [row_cx]
        if name == "A" and ri == nrows - 1:
            overhang = (row_len + 0.06) / 2 - ((cols[-1] - cols[0]) * PITCH_X / 2 + PW / 2)
            print(f"  NORTH ROW r{ri:02d}: rail_len={row_len + 0.06:.3f} "
                  f"row_cx={row_cx:.3f} cols={cols[0]}..{cols[-1]} "
                  f"overhang={overhang:.3f} stations={n_stations}")
        # -- 两根横梁 + 顶凸筋 --
        for dy in (-RAIL_DY, RAIL_DY):
            loc = (row_cx,
                   ry + dy * math.cos(TILT),
                   roof_z + CENTER_H + dy * math.sin(TILT) - PT / 2 - RAIL_H / 2)
            add_box(bm, tilt_mat(loc), row_len + 0.06, RAIL_W, RAIL_H, I_RAIL)
            n_rail += 1
            rib_loc = (row_cx,
                       ry + dy * math.cos(TILT),
                       roof_z + CENTER_H + dy * math.sin(TILT) - PT / 2 + RIB_H / 2)
            add_box(bm, tilt_mat(rib_loc), row_len + 0.06, RIB_W, RIB_H, I_RAIL)
            # -- 每站一对斜撑支腿 + 脚板 + 地脚螺栓 --
            rail_bot_z = roof_z + CENTER_H + dy * math.sin(TILT) - PT / 2 - RAIL_H
            rail_y = ry + dy * math.cos(TILT)
            leg_off = off_s if dy < 0 else off_n
            for sx in st_xs:
                top = Vector((sx, rail_y, rail_bot_z))
                base = Vector((sx, rail_y - leg_off, LEG_BASE_Z))
                d = top - base
                leng = d.length
                mid = (top + base) / 2
                q = Vector((0, 0, 1)).rotation_difference(d.normalized())
                m = Matrix.Translation(mid) @ q.to_matrix().to_4x4()
                add_box(bm, m, LEG_SECT, LEG_SECT, leng, I_LEG)
                n_leg += 1
                # 脚板
                foot_c = Vector((sx, rail_y - leg_off, FOOT_Z))
                add_box(bm, Matrix.Translation(foot_c), FOOT, FOOT, 0.02, I_LEG)
                # 脚板对角两颗地脚螺栓(六棱头, 竖直)
                for ox, oy in ((-0.045, -0.045), (0.045, 0.045)):
                    add_prism(bm, Matrix.Translation(
                        Vector((sx + ox, rail_y - leg_off + oy, BOLT_Z))),
                        0.03, 0.015, I_BOLT)
                    n_bolt += 1
        # -- 每站一根纵梁(沿坡向连两根横梁) + 一根横拉杆(连同站两条斜撑腿中点) --
        #   注意: 只在行级做一次, 不能放在上面的 dy 循环里(否则每站重复两根)
        for sx in st_xs:
            ploc = (sx, ry, roof_z + CENTER_H - PT / 2 - RAIL_H - PURL_H / 2)
            add_box(bm, tilt_mat(ploc), PURL_SECT, 1.20, PURL_H, I_RAIL)
            n_purl += 1
            z_hi = roof_z + CENTER_H + RAIL_DY * math.sin(TILT) - PT / 2 - RAIL_H
            z_lo = roof_z + CENTER_H - RAIL_DY * math.sin(TILT) - PT / 2 - RAIL_H
            z_mid = ((z_hi + z_lo) / 2 + LEG_BASE_Z) / 2
            y_hi = ry + RAIL_DY * math.cos(TILT) - off_n / 2
            y_lo = ry - RAIL_DY * math.cos(TILT) - off_s / 2
            tie_len = y_hi - y_lo
            add_box(bm, Matrix.Translation(
                Vector((sx, (y_hi + y_lo) / 2, z_mid))),
                TIE_SECT, tie_len, TIE_SECT, I_LEG)
            n_tie += 1
        # -- 每块板四角压块 + 压块顶螺柱 (A 北行两角板已删, 对应压块同步跳过) --
        for c in range(ncols):
            if name == "A" and ri == nrows - 1 and c in (0, ncols - 1):
                continue
            px = cx + (c - (ncols - 1) / 2) * PITCH_X
            panel_mat = tilt_mat((px, ry, roof_z + CENTER_H))
            for ox in (-(PW / 2 - 0.07), PW / 2 - 0.07):
                for oy in (-(PL / 2 - 0.07), PL / 2 - 0.07):
                    cm = panel_mat @ Matrix.Translation(Vector((ox, oy, PT / 2 + 0.012)))
                    add_box(bm, cm, 0.09, 0.09, 0.024, I_CLAMP)
                    n_clamp += 1
                    stud = panel_mat @ Matrix.Translation(
                        Vector((ox, oy, PT / 2 + 0.024)))
                    add_prism(bm, stud, 0.024, 0.02, I_BOLT)
                    n_bolt += 1
    bm.to_mesh(mesh)
    bm.free()
    # UV：bmesh 建的 mesh 没有 UV 层；按米制盒式投影补一层（每 1m 一贴图 tile，
    # 与 pv-panels.py 同口径），供 PBR 贴图使用（横梁最长约 37m，沿长度方向出拉丝变化）。
    _uv = mesh.uv_layers.new(name="UVMap")
    for _poly in mesh.polygons:
        _n = _poly.normal
        _ax = max(range(3), key=lambda i: abs(_n[i]))
        _ua, _va = [i for i in range(3) if i != _ax]
        for _li in _poly.loop_indices:
            _co = mesh.vertices[mesh.loops[_li].vertex_index].co
            _uv.data[_li].uv = (_co[_ua], _co[_va])
    for m in MATS:
        mesh.materials.append(m)
    obj = bpy.data.objects.new(f"PV_Mount_{name}", mesh)
    bpy.context.collection.objects.link(obj)
    mount_objs.append(obj)
    print(f"ROOF {name}: rails={n_rail} purlins={n_purl} legs={n_leg} ties={n_tie} "
          f"clamps={n_clamp} bolts={n_bolt} ({ncols} cols x {nrows} rows, "
          f"stations/row={sorted(set(st_counts))}) verts={len(mesh.vertices)}")

build_roof("A", -56, 30, 18.35, 32, 7, row_dy={0: 0.35, 6: -0.35})
build_roof("B", -12, 30, 18.35, 26, 6)
build_roof("LAB", -28, 62, 12.30, 34, 5)

# ---- 只留支架, 存 blend ----
for o in mount_objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = mount_objs[0]
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print(f"BLEND saved: {BLEND}")

# ---- 导出 GLB (只选本件对象) ----
bpy.ops.export_scene.gltf(
    filepath=GLB, export_format='GLB',
    use_selection=True, export_apply=True)
print(f"GLB exported: {GLB}")

# ---- 回读 GLB 验证 ----
before = set(bpy.data.objects.keys())
bpy.ops.import_scene.gltf(filepath=GLB)
after = set(bpy.data.objects.keys())
imported = after - before
print(f"GLB reimport OK: {len(imported)} objects: {sorted(imported)}")
assert len(imported) > 0, "GLB reimport failed!"

print("DONE pv-mount")
