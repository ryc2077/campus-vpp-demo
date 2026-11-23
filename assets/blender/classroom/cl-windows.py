# cl-windows v2: 教室内部·窗户窗帘（返工）
# 纹理已固化进脚本（见文件末尾 _apply_pbr_textures，2026-11-23）：
# 染色贴图 assets/blender/tex/ + 原图 assets/external/，材质节点直连
# Base Color/Roughness/Normal；重跑不再丢贴图。玻璃材质不挂贴图（保持
# Transmission/Alpha 透明材质原样）。
# 规约: assets/blender/SPEC.md §6 教室局部坐标
#   房间中心原点, x 长 9.68m (-4.84~+4.84), y 宽 7.26m (-3.63~+3.63), z 0-3.0m
#   黑板墙在 x=-4.84 一侧, 南侧窗户沿 y=-3.63 墙面, 北侧沿 y=+3.63 墙面
#   每扇窗 1.8(x) x 1.5(高)m, 窗台高 0.9m (窗 z 0.9-2.4), x 中心 -3.6, -1.2, +1.2, +3.6
# v2 返工 (旧版 60 对象布局保持, 只补结构与材质):
#   1. 真实结构: 窗框加厚 (y 向 0.14m) + 窗洞内凹 (框面退进墙面 0.05m, 不贴墙)
#      + 上/侧 jamb 内衬 + 窗台板 (外伸 0.14m) + 竖中梃 + 横中梃 (2x2 分格)
#   2. 玻璃反光: Principled Transmission 0.9 + 低粗糙度 + 淡淡蓝灰,
#      Eevee 开 Screen Space Reflections/Refraction + Reflection Cubemap 探针
#   3. 窗帘: 南侧带帘 (杆 + 托架 + 端头 + 波浪/褶皱几何布帘 + 布纹噪波), 北侧无帘
#   4. 材质分开: 框 (塑钢/金属噪波 Bump + 粗糙度变化) / 玻璃 (微噪波) /
#      窗帘 (布纹噪波 Bump + 颜色微变化) / 杆 (金属), 不许全平
#   5. 结构件倒角 (bevel)
#   6. 门 (2026-11-23 tevy 换件): tevy 教室 door_geo (CC0, 开约 26°),
#      绕 Z +90° 转进东墙门洞, 铰链在北 jamb; 门洞两侧 + 顶部缝用墙色盒填满
# 只做窗户/窗框/玻璃/窗帘杆/窗帘/门, 不做桌椅/黑板/空调/灯具/地面墙面。
# 新规矩: 渲染全部走 GitHub Actions, 本脚本不渲染、不出预览图。
#   只交付: 脚本 + .blend + .glb, 导出后回读校验并做 GLB 节点坐标验证。

import bpy
import math
import mathutils
import os

BASE = os.path.expanduser(
    "~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
BLEND_PATH = os.path.join(BASE, "assets/blender/classroom/cl-windows.blend")
GLB_PATH = os.path.join(BASE, "assets/models/cl-windows.glb")

# ---- sRGB hex -> linear (SPEC 坑: Principled Base Color 要线性值) ----
def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def hex_linear(h):
    h = h.lstrip("#")
    r = int(h[0:2], 16) / 255.0
    g = int(h[2:4], 16) / 255.0
    b = int(h[4:6], 16) / 255.0
    return (srgb_to_linear(r), srgb_to_linear(g), srgb_to_linear(b), 1.0)

# ---- 清空场景 ----
bpy.ops.wm.read_factory_settings(use_empty=True)

# ---- 材质工具 ----
def principled(name, color_hex, roughness=0.6, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = hex_linear(color_hex)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat

def add_noise_bump(mat, scale, strength, distance=0.05):
    """噪波 -> Bump, 让表面不全平. 返回 noise 节点 (供复用)."""
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = scale
    tex.inputs["Detail"].default_value = 2.0
    tex.inputs["Roughness"].default_value = 0.7
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = strength
    bump.inputs["Distance"].default_value = distance
    nt.links.new(tex.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return tex

def add_roughness_variation(mat, tex, lo, hi):
    """噪波 Fac -> Map Range -> 粗糙度, 粗糙度有变化."""
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.0
    mr.inputs["From Max"].default_value = 1.0
    mr.inputs["To Min"].default_value = lo
    mr.inputs["To Max"].default_value = hi
    nt.links.new(tex.outputs["Fac"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])

# 窗框: 塑钢白, 微金属感, 噪波 Bump + 粗糙度 0.35~0.6 变化
MAT_FRAME = principled("cl-windows_frame_white", "#E8E8E8",
                        roughness=0.45, metallic=0.15)
_tex_f = add_noise_bump(MAT_FRAME, scale=8.0, strength=0.15, distance=0.02)
add_roughness_variation(MAT_FRAME, _tex_f, 0.35, 0.6)

# 玻璃: 淡淡蓝灰 #9FC3D8, Principled Transmission 0.9, 粗糙度 0.05,
#   IOR 1.45, 微噪波 Bump (0.03) 模拟玻璃不绝对平整
MAT_GLASS = principled("cl-windows_glass", "#9FC3D8",
                        roughness=0.05, metallic=0.0)
_bsdf_g = MAT_GLASS.node_tree.nodes["Principled BSDF"]
_bsdf_g.inputs["Transmission Weight"].default_value = 0.9
_bsdf_g.inputs["IOR"].default_value = 1.45
# 返工 2026-11-23: 玻璃透明化, Alpha 0.65 + BLEND (之前 Alpha 默认 1.0,
# GLB 里 alphaMode 缺失、整片不透明)。粗糙度仍 0.05 低粗糙反光。
_bsdf_g.inputs["Alpha"].default_value = 0.65
_bsdf_g.inputs["Specular IOR Level"].default_value = 1.0
try:
    MAT_GLASS.surface_render_method = 'BLENDED'
except Exception:
    pass
add_noise_bump(MAT_GLASS, scale=15.0, strength=0.03, distance=0.01)

# 窗帘布: 米白, 高粗糙, 布纹噪波 Bump (0.3) + 噪波颜色微变化
MAT_CURTAIN = principled("cl-windows_curtain_cream", "#F3E9D2", roughness=0.95)
_tex_c = add_noise_bump(MAT_CURTAIN, scale=6.0, strength=0.3, distance=0.05)
_nt_c = MAT_CURTAIN.node_tree
_bsdf_c = _nt_c.nodes["Principled BSDF"]
_mix = _nt_c.nodes.new("ShaderNodeMixRGB")
_mix.blend_type = 'MIX'
_mix.inputs[1].default_value = hex_linear("#F3E9D2")
_mix.inputs[2].default_value = hex_linear("#E2D5B8")
_nt_c.links.new(_tex_c.outputs["Fac"], _mix.inputs[0])
# 返工 2026-11-23: 窗帘 Mix 不连 Base Color (否则 glTF 丢 baseColorFactor)。
# 布纹深浅改走 Bump, Base Color 只留纯色 #F3E9D2。

# 窗帘杆: 金属灰, 金属度 0.85, 细噪波 Bump
MAT_ROD = principled("cl-windows_rod_metal", "#8A8F94",
                      roughness=0.35, metallic=0.85)
add_noise_bump(MAT_ROD, scale=12.0, strength=0.08, distance=0.01)

# ---- Eevee 反射设置 (玻璃反光用; 本脚本不渲染, 只留设置进 .blend) ----
scene = bpy.context.scene
try:
    scene.eevee.use_ssr = True
    scene.eevee.use_ssr_refraction = True
    scene.eevee.use_ssr_halfres = False
except Exception as e:
    print("eevee ssr setup skipped:", e)

# ---- 集合 ----
coll = bpy.data.collections.new("cl-windows")
bpy.context.scene.collection.children.link(coll)

piece_objs = []

def add_box(name, loc, dims, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0:
        mod = ob.modifiers.new("bevel", 'BEVEL')
        mod.width = bevel
        mod.segments = 2
    ob.data.materials.append(mat)
    coll.objects.link(ob)
    bpy.context.scene.collection.objects.unlink(ob)
    piece_objs.append(ob)
    return ob

def add_cylinder_x(name, loc, radius, depth, mat):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth,
                                        location=loc, vertices=16,
                                        rotation=(0, math.radians(90), 0))
    ob = bpy.context.active_object
    ob.name = name
    ob.data.materials.append(mat)
    coll.objects.link(ob)
    bpy.context.scene.collection.objects.unlink(ob)
    piece_objs.append(ob)
    return ob

def add_sphere(name, loc, radius, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=loc,
                                         segments=16, ring_count=12)
    ob = bpy.context.active_object
    ob.name = name
    ob.data.materials.append(mat)
    coll.objects.link(ob)
    bpy.context.scene.collection.objects.unlink(ob)
    piece_objs.append(ob)
    return ob

def add_curtain(name, cx, y, z_top, width, height, mat):
    """波浪/褶皱布帘: 网格平面, y 向按正弦起伏 (4 个褶, 振幅向底部渐大),
    加 Solidify 给布厚 0.012m. 法线朝室内 (+y, 南侧)."""
    nx, nz = 16, 20
    verts = []
    for j in range(nz + 1):
        t = j / nz  # 0 顶部 -> 1 底部
        amp = 0.03 + 0.015 * t
        for i in range(nx + 1):
            s = i / nx
            # 顶点用局部坐标, 对象原点放在 (cx, y, z_top), 避免原点落在房间中心
            verts.append(((s - 0.5) * width,
                          amp * math.sin(s * math.pi * 2 * 4),
                          -t * height))
    faces = []
    for j in range(nz):
        for i in range(nx):
            a = j * (nx + 1) + i
            b = a + 1
            c = a + (nx + 1) + 1
            d = a + (nx + 1)
            faces.append((a, b, c, d))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    # UV: x 归一化 / z 归一化, 供布纹噪波贴图
    uv_layer = mesh.uv_layers.new(name="UVMap")
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            v = mesh.vertices[mesh.loops[li].vertex_index].co
            uv_layer.data[li].uv = ((v.x + width / 2.0) / width,
                                    -v.z / height)
    ob = bpy.data.objects.new(name, mesh)
    ob.location = (cx, y, z_top)
    coll.objects.link(ob)
    sol = ob.modifiers.new("solidify", 'SOLIDIFY')
    sol.thickness = 0.012
    sol.offset = 0.0
    ob.data.materials.append(mat)
    piece_objs.append(ob)
    return ob

# ---- 窗户参数 ----
WIN_W = 1.8        # 窗宽 (x)
WIN_H = 1.5        # 窗高 (z)
WIN_Z0 = 0.9       # 窗台高
WIN_ZC = WIN_Z0 + WIN_H / 2.0   # 窗中心 z = 1.65
FRAME_W = 0.06     # 边框宽
FRAME_T = 0.14     # 窗框 y 向厚度 (加厚, 有框厚)
GLASS_T = 0.02
RECESS = 0.05      # 窗洞内凹: 框面退进墙面 0.05m, 不贴墙面
WALL_Y_S = -3.63   # 南墙面
WALL_Y_N = 3.63    # 北墙面
COLS_X = [-3.6, -1.2, 1.2, 3.6]

def build_window(side_tag, xc, y_wall, inward):
    """一扇窗: 玻璃 + 4 根边框 + 竖中梃 + 横中梃 + 窗台 + 上/侧 jamb 内衬.
    inward: +1 南侧 (室内为 +y), -1 北侧 (室内为 -y).
    框中心 y = 墙面 + inward*RECESS, 即嵌进墙洞 0.05m."""
    y_f = y_wall + inward * RECESS
    # 玻璃: 整扇 1.8 x 1.5, 薄片, 居于框厚中央
    add_box("cl-windows_glass_%s" % side_tag, (xc, y_f, WIN_ZC),
            (WIN_W, GLASS_T, WIN_H), MAT_GLASS)
    # 边框: 上/下横框 (全宽), 左/右竖框 (扣除横框后的净高), 倒角 0.008
    add_box("cl-windows_frame_top_%s" % side_tag,
            (xc, y_f, WIN_Z0 + WIN_H - FRAME_W / 2.0),
            (WIN_W, FRAME_T, FRAME_W), MAT_FRAME, bevel=0.008)
    add_box("cl-windows_frame_bottom_%s" % side_tag,
            (xc, y_f, WIN_Z0 + FRAME_W / 2.0),
            (WIN_W, FRAME_T, FRAME_W), MAT_FRAME, bevel=0.008)
    add_box("cl-windows_frame_left_%s" % side_tag,
            (xc - WIN_W / 2.0 + FRAME_W / 2.0, y_f, WIN_ZC),
            (FRAME_W, FRAME_T, WIN_H - 2 * FRAME_W), MAT_FRAME, bevel=0.008)
    add_box("cl-windows_frame_right_%s" % side_tag,
            (xc + WIN_W / 2.0 + FRAME_W / 2.0 - FRAME_W, y_f, WIN_ZC),
            (FRAME_W, FRAME_T, WIN_H - 2 * FRAME_W), MAT_FRAME, bevel=0.008)
    # 竖中梃 + 横中梃: 2x2 分格, 倒角 0.005
    add_box("cl-windows_mullion_%s" % side_tag,
            (xc, y_f, WIN_ZC),
            (FRAME_W, FRAME_T, WIN_H - 2 * FRAME_W), MAT_FRAME, bevel=0.005)
    add_box("cl-windows_transom_%s" % side_tag,
            (xc, y_f, WIN_ZC),
            (WIN_W - 2 * FRAME_W, FRAME_T, FRAME_W), MAT_FRAME, bevel=0.005)
    # 窗台板: 宽出窗洞 0.09/侧, 厚 0.045, 深 0.18 (室内外伸约 0.14m), 倒角
    add_box("cl-windows_sill_%s" % side_tag,
            (xc, y_wall + inward * 0.05, WIN_Z0 - 0.0225),
            (WIN_W + 0.18, 0.18, 0.045), MAT_FRAME, bevel=0.008)
    # jamb 内衬: 左右侧衬 (窗洞侧面) + 顶部衬 (窗洞顶面), 框白
    add_box("cl-windows_jamb_left_%s" % side_tag,
            (xc - WIN_W / 2.0 - 0.025, y_f, WIN_ZC),
            (0.05, FRAME_T, WIN_H), MAT_FRAME, bevel=0.004)
    add_box("cl-windows_jamb_right_%s" % side_tag,
            (xc + WIN_W / 2.0 + 0.025, y_f, WIN_ZC),
            (0.05, FRAME_T, WIN_H), MAT_FRAME, bevel=0.004)
    add_box("cl-windows_jamb_top_%s" % side_tag,
            (xc, y_f, WIN_Z0 + WIN_H + 0.025),
            (WIN_W + 0.10, FRAME_T, 0.05), MAT_FRAME, bevel=0.004)

# ---- 南侧 4 扇窗 + 窗帘杆 + 托架 + 端头 + 波浪窗帘 ----
ROD_Z = 2.5
ROD_Y = -3.55
CURTAIN_Z_TOP = 2.4
CURTAIN_H = 1.2
CURTAIN_W = 0.5

for i, xc in enumerate(COLS_X, start=1):
    tag = "s%d" % i
    build_window(tag, xc, WALL_Y_S, +1)
    add_cylinder_x("cl-windows_rod_%s" % tag, (xc, ROD_Y, ROD_Z),
                   0.015, 2.0, MAT_ROD)
    # 托架: 杆两端各一, 连墙到杆
    for dx in (-0.95, 0.95):
        add_box("cl-windows_bracket_%s_%s" % (tag, "l" if dx < 0 else "r"),
                (xc + dx, -3.59, ROD_Z),
                (0.03, 0.09, 0.03), MAT_ROD, bevel=0.004)
    # 端头球: 杆两端各一
    for dx in (-1.0, 1.0):
        add_sphere("cl-windows_finial_%s_%s" % (tag, "l" if dx < 0 else "r"),
                   (xc + dx, ROD_Y, ROD_Z), 0.025, MAT_ROD)
    # 波浪窗帘两片, 收在窗两侧, 中心 x = xc ± 0.65
    for k, dx in enumerate((-0.65, 0.65), start=1):
        add_curtain("cl-windows_curtain_%s_%d" % (tag, k),
                    xc + dx, ROD_Y, CURTAIN_Z_TOP, CURTAIN_W, CURTAIN_H,
                    MAT_CURTAIN)

# ---- 北侧 4 扇窗 (只要窗, 不做窗帘) ----
for i, xc in enumerate(COLS_X, start=1):
    build_window("n%d" % i, xc, WALL_Y_N, -1)

# ---- 门: tevy 教室 door_geo (CC0, assets/external/buildings/classroom-tevy-plain.glb,
#   已去压缩版, 见 assets/external/buildings/tevy-decompress.mjs) ----
# tevy 门: 0.82(x) x 0.44(y) x 2.09(z)m, 门扇开约 26°, 玻璃竖条 0.06x0.26m,
# 铰链在 tevy +x 端。只取 door_geo, 其余导入对象 (含 door 空物体) 全删。
# 旋转 +90° (tevy (x,y) -> SPEC (-y,x)): 门宽 0.82 落在 SPEC y 向, 门扇
# 伸进室内方向落在 SPEC x 向, 铰链转到 SPEC +y 端 (北 jamb)。
TEVY_PLAIN = os.path.join(BASE, "assets/external/buildings/classroom-tevy-plain.glb")

# 门漆: 淡蓝灰 #9FB2C0, 金属度 0.3 (PBR 见下, 白 stucco 染色图)
MAT_DOOR = principled("cl-windows_door_paint", "#9FB2C0",
                      roughness=0.6, metallic=0.3)
# 门洞填缝: 墙色 #F3E9D2 (PBR 见下, 白 stucco 染色图)
MAT_JAMB = principled("cl-windows_door_jamb", "#F3E9D2", roughness=0.9)

_before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=TEVY_PLAIN)
_new = [ob for ob in bpy.data.objects if ob not in _before]
door_ob = None
for ob in _new:
    if ob.name == "door_geo" and ob.type == "MESH":
        door_ob = ob
assert door_ob is not None, "tevy door_geo not imported"
# 先解除父级 (door 空物体), 保持世界变换, 再烘变换
bpy.ops.object.select_all(action="DESELECT")
door_ob.select_set(True)
bpy.context.view_layer.objects.active = door_ob
bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
# 删其余导入对象 (含 door 空物体与 bags_bin/ceiling/chairs/desks/shell/
# shelves/teacher_desk/wall_front)
for ob in list(_new):
    if ob is not door_ob:
        bpy.data.objects.remove(ob, do_unlink=True)
# 材质槽重映射: classroom -> 门漆, classroom_glass -> 复用现有玻璃材质
for i, slot in enumerate(door_ob.data.materials):
    if slot is None:
        continue
    if slot.name == "classroom":
        door_ob.data.materials[i] = MAT_DOOR
    elif slot.name == "classroom_glass":
        door_ob.data.materials[i] = MAT_GLASS
# 清掉导入带来的无用材质 (classroom* 已无使用者) 与无主网格
for mat in list(bpy.data.materials):
    if mat.users == 0 and mat.name.startswith("classroom"):
        bpy.data.materials.remove(mat)
for me in list(bpy.data.meshes):
    if me.users == 0:
        bpy.data.meshes.remove(me)
# 删原 atlas UV, 走 _ensure_uvs 补 Smart UV Project
while len(door_ob.data.uv_layers) > 0:
    door_ob.data.uv_layers.remove(door_ob.data.uv_layers[0])
# 烘掉导入变换 (位置/缩放烘进网格)。注意: 实测 Blender 4.2 后台跑
# transform_apply(location=False, rotation=True) 会把 rotation_euler
# 清零却不转网格顶点 (静默失效, cl-desks 里同款调用也一样, 旋转是靠
# 对象 transform 进 GLB 的)。门这里必须把旋转真正烘进网格, 改用
# mesh.transform, 自定义法线会一并转 (已实测: 法线 (-0.874,0.486,0)
# -> (-0.486,-0.874,0), 与旋转矩阵一致)。
bpy.ops.object.select_all(action="DESELECT")
door_ob.select_set(True)
bpy.context.view_layer.objects.active = door_ob
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
door_ob.data.transform(mathutils.Matrix.Rotation(math.radians(90.0), 4, 'Z'))
# 定位: 墙侧 x_max 对准 4.88 (东墙中心 4.84 + 墙厚 0.15/2 - 门扇伸进室内量),
# y 中心对准 0。实测 tevy 门 z 0~2.09, 不用动 z。
_dx = [v.co.x for v in door_ob.data.vertices]
_dy = [v.co.y for v in door_ob.data.vertices]
_dz = [v.co.z for v in door_ob.data.vertices]
print("door bbox before place: x[%.3f, %.3f] y[%.3f, %.3f] z[%.3f, %.3f]"
      % (min(_dx), max(_dx), min(_dy), max(_dy), min(_dz), max(_dz)))
assert abs(min(_dz)) < 0.01, "door z_min not on floor: %f" % min(_dz)
assert 2.0 < max(_dz) < 2.15, "door height wrong: %f" % max(_dz)
# 旋转后核对: x 向应为门扇伸进室内量 ~0.44, y 向应为门宽 ~0.82
# (转错会静默变成 x 0.82 / y 0.44, 门就横插进屋里)
assert 0.40 < max(_dx) - min(_dx) < 0.48, "door rotated x extent wrong: %.3f" % (max(_dx) - min(_dx))
assert 0.78 < max(_dy) - min(_dy) < 0.86, "door rotated y extent wrong: %.3f" % (max(_dy) - min(_dy))
_door_dx = 4.88 - max(_dx)
_door_dy = 0.0 - (min(_dy) + max(_dy)) / 2.0
door_ob.location = (_door_dx, _door_dy, 0.0)
print("door placed: translate (%.3f, %.3f), x_max -> 4.88, y center -> 0"
      % (_door_dx, _door_dy))
door_ob.name = "cl-windows_door"
try:
    coll.objects.link(door_ob)
except RuntimeError:
    pass
if door_ob.name in bpy.context.scene.collection.objects:
    bpy.context.scene.collection.objects.unlink(door_ob)
piece_objs.append(door_ob)
# 门洞填缝 (只读 cl-floor-walls.py 的门洞尺寸, 不改它): 东墙门洞 y[-0.5,0.5]
# 高 2.2, 墙中心 x=4.84 厚 0.15; tevy 门宽 0.82, 两侧各留 0.09 缝,
# 顶部留 0.11 缝, 用墙色盒子填满
add_box("cl-windows_door_jamb_left", (4.84, -0.455, 1.1),
        (0.15, 0.09, 2.2), MAT_JAMB, bevel=0.004)
add_box("cl-windows_door_jamb_right", (4.84, 0.455, 1.1),
        (0.15, 0.09, 2.2), MAT_JAMB, bevel=0.004)
add_box("cl-windows_door_jamb_top", (4.84, 0.0, 2.145),
        (0.15, 0.82, 0.11), MAT_JAMB, bevel=0.004)

# ---- Reflection Cubemap 探针 (玻璃反光用, 不导出, 只进 .blend) ----
bpy.ops.object.lightprobe_add(type='SPHERE', location=(0, 0, 1.6))
probe = bpy.context.active_object
probe.name = "cl-windows_reflection_probe"
try:
    probe.data.influence_distance = 6.0
    probe.data.falloff = 0.5
except Exception:
    pass

from collections import Counter
kinds = Counter(ob.name.split("_")[1] if "_" in ob.name else ob.name
                for ob in piece_objs)
print("windows built: %d objects" % len(piece_objs))
print("object kinds:", dict(kinds))
# 预期: 每扇窗 11 件 x8 = 88; 南侧每扇杆 1 + 托架 2 + 端头 2 + 窗帘 2 = 7 x4 = 28; 门 1 + 门洞填缝 3 = 4; 合计 120

# ---- PBR 贴图固化 (2026-11-23)：把上一轮挂在 .blend 上的外部贴图写进脚本 ----
# color 图：assets/blender/tex/ 里的染色图（已按 SPEC §3 目标色染色）；
# rough/normal 图：assets/external/ 原图（CC0）。
# 节点只许 TexCoord→Mapping→Image Texture 直连 BSDF，不加 Hue/Sat/Mix，
# 否则 glTF 导出器不认。Base Color 默认值须置白、Roughness 置 1.0（贴图
# 本身带颜色与粗糙度），否则导出器会把旧纯色写成 baseColorFactor/
# roughnessFactor 与贴图二次相乘；Metallic 保持脚本原值。玻璃材质跳过。
# 没有 UV 的网格补 Smart UV Project（已有 UV 的不动，如窗帘自定义 UV）。
TEX_DIR = os.path.join(BASE, "assets/blender/tex")
EXT_DIR = os.path.join(BASE, "assets/external")
# 材质名: (tex/ 染色 color 图, external rough 图, external normal 图, Mapping 缩放)
PBR_TEXTURES = {
    "cl-windows_frame_white": ("white_stucco__E8E8E8.jpg",
        "polyhaven/white_stucco_rough_1k.jpg",
        "polyhaven/white_stucco_nor_gl_1k.jpg", (2.0, 1.0)),
    "cl-windows_rod_metal": ("corrugated_iron_02__8A8F94.jpg",
        "polyhaven/corrugated_iron_02_rough_1k.jpg",
        "polyhaven/corrugated_iron_02_nor_gl_1k.jpg", (1.0, 1.0)),
    "cl-windows_curtain_cream": ("Plaster001__F3E9D2.jpg",
        "ambientcg/Plaster001/Plaster001_1K-JPG_Roughness.jpg",
        "ambientcg/Plaster001/Plaster001_1K-JPG_NormalGL.jpg", (2.0, 2.0)),
    # 门漆与门洞填缝 (2026-11-23 tevy 换件新增): 白 stucco 染色图 + 同款原图
    "cl-windows_door_paint": ("white_stucco__B9C4CC.jpg",
        "polyhaven/white_stucco_rough_1k.jpg",
        "polyhaven/white_stucco_nor_gl_1k.jpg", (1.0, 1.0)),
    "cl-windows_door_jamb": ("white_stucco__F3E9D2.jpg",
        "polyhaven/white_stucco_rough_1k.jpg",
        "polyhaven/white_stucco_nor_gl_1k.jpg", (1.0, 1.0)),
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
    """没有 UV 的网格补 Smart UV Project（已有 UV 的不动，如窗帘自定义 UV）。"""
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
_ensure_uvs(piece_objs)

# ---- 存 .blend (只含本件 + 探针) ----
os.makedirs(os.path.dirname(BLEND_PATH), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("blend saved:", BLEND_PATH, "size", os.path.getsize(BLEND_PATH))

# ---- 导出 .glb (只选本件对象, 不含探针) ----
bpy.ops.object.select_all(action='DESELECT')
for ob in piece_objs:
    ob.select_set(True)
bpy.context.view_layer.objects.active = piece_objs[0]
os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format='GLB',
                           use_selection=True, export_apply=True)
print("glb exported:", GLB_PATH, "size", os.path.getsize(GLB_PATH))

# ---- 回读校验 + GLB 节点坐标验证 (南北两侧窗都在) ----
n_before = len(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB_PATH)
imported = [ob for ob in bpy.data.objects if ob not in piece_objs
            and ob.name != "cl-windows_reflection_probe"]
print("gltf reimport: %d objects imported" % len(imported))
assert len(imported) > 0, "glTF reimport failed"

def _count(objs, pred):
    return sum(1 for ob in objs if pred(ob))

south = [ob for ob in imported if ob.location.y < 0]
north = [ob for ob in imported if ob.location.y > 0]
glass_s = _count(imported, lambda o: "glass" in o.name and o.location.y < 0)
glass_n = _count(imported, lambda o: "glass" in o.name and o.location.y > 0)
curtain_s = _count(imported, lambda o: "curtain" in o.name)
curtain_n = _count(imported, lambda o: "curtain" in o.name and o.location.y > 0)
rod_s = _count(imported, lambda o: "rod" in o.name)
door_n = _count(imported, lambda o: o.name.startswith("cl-windows_door")
               and "jamb" not in o.name)
jamb_n = _count(imported, lambda o: "door_jamb" in o.name)
print("reimport south objects: %d, north objects: %d" % (len(south), len(north)))
print("reimport glass south: %d, glass north: %d" % (glass_s, glass_n))
print("reimport curtains south: %d, curtains north: %d" % (curtain_s, curtain_n))
print("reimport rods: %d, doors: %d, door jambs: %d" % (rod_s, door_n, jamb_n))
print("reimport total: %d (expect 120)" % len(imported))
assert len(imported) == 120, "total count wrong: %d" % len(imported)
assert len(south) > 0 and len(north) > 0, "missing south or north windows"
assert glass_s == 4 and glass_n == 4, "glass count wrong: S=%d N=%d" % (glass_s, glass_n)
assert curtain_s == 8 and curtain_n == 0, "curtain layout wrong: S=%d N=%d" % (curtain_s, curtain_n)
assert rod_s == 4, "rod count wrong: %d" % rod_s
assert door_n == 1, "door count wrong: %d" % door_n
assert jamb_n == 3, "door jamb count wrong: %d" % jamb_n
# 门位置抽查: x_max 对准 4.88, y 中心对准 0, z 0~2.09
_door = [o for o in imported if o.name.startswith("cl-windows_door")
         and "jamb" not in o.name][0]
_bb = [ _door.matrix_world @ mathutils.Vector(c) for c in _door.bound_box ]
_bx = [v.x for v in _bb]; _by = [v.y for v in _bb]; _bz = [v.z for v in _bb]
print("reimport door bbox: x[%.3f, %.3f] y[%.3f, %.3f] z[%.3f, %.3f]"
      % (min(_bx), max(_bx), min(_by), max(_by), min(_bz), max(_bz)))
assert abs(max(_bx) - 4.88) < 0.03, "door x_max wrong: %.3f" % max(_bx)
assert abs((min(_by) + max(_by)) / 2.0) < 0.03, "door y center wrong"
assert abs(min(_bz)) < 0.01 and 2.0 < max(_bz) < 2.15, "door z wrong"
# 位置抽查: 南侧玻璃 y 应在 -3.6 附近 (内凹 -3.58), 北侧在 +3.58 附近
ys = sorted(round(ob.location.y, 2) for ob in imported if "glass" in ob.name)
print("reimport glass y values:", ys)
assert all(abs(y) > 3.5 and abs(y) < 3.65 for y in ys), "glass y out of range"

print("DONE cl-windows")
