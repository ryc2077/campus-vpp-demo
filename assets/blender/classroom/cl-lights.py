# cl-lights v2: 教室内部·灯具返工
# 规约: assets/blender/SPEC.md §6 教室局部坐标
#   房间中心原点, x 长 9.68m (-4.84~+4.84), y 宽 7.26m (-3.63~+3.63), z 0-3.0m
#   天花板 z=3.0m; 黑板墙在 x=-4.84 一侧
# 返工目标 (v1 筛查结论): 吊杆缺失、灯直接贴天花板 -> v2 补齐真实结构
#   ① 吊杆: 任务书说 0.3m 又写灯具顶面 z=2.92 到天花板 3.0 (0.08m),
#      以明确的 z 范围为准, 吊杆实长 0.08m (z 2.92 -> 3.0)
#   ② 灯具真实结构: 灯盘(灯壳) + 双灯管(弱自发光) + 灯管端盖 + 吊杆 + 顶座
#   ③ 布局: 2 排(y) x 3 列(x) 共 6 盏, 间距均匀
#      x 列: -3.23 / 0 / +3.23 (9.68/3=3.227, 灯长 1.2, 列间距 3.23)
#      y 排: -1.21 / +1.21 (7.26/6=1.21, 排间距 2.42)
#   ④ 材质分开: 白灯盘(轻微噪波) / 金属吊杆+顶座 / 灯管乳白半透明(弱自发光)
#   ⑤ 所有面加程序化纹理: Noise -> 粗糙度变化 + Bump, 不许全平
#   ⑥ 结构件(灯盘/顶座)给倒角 (modifier 直接 apply, 导出即带倒角)
# 只做灯具 + 吊杆 + 顶座, 不做桌椅/黑板/空调/窗户/地面墙面/天花板本身。
# 新规矩: 渲染全部走 GitHub Actions, 本地不渲染、不出预览图。
#   本脚本只做: 建模 -> 存 .blend -> 导出 .glb -> glTF 回读校验, 末尾打印 DONE cl-lights

import bpy
import math
import os

BASE = os.path.expanduser(
    "~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
BLEND_PATH = os.path.join(BASE, "assets/blender/classroom/cl-lights.blend")
GLB_PATH = os.path.join(BASE, "assets/models/cl-lights.glb")

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

# ---- 材质 (只用 Principled BSDF, 全部带 Noise 程序化纹理) ----
def add_noise(mat, scale=8.0, rough_base=0.5, rough_var=0.15, bump_strength=0.02):
    """Noise 纹理 -> 粗糙度变化 + Bump, 接在 Principled 上。"""
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 2.0
    noise.inputs["Roughness"].default_value = 0.7
    # 粗糙度: base + fac*var
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = 'MULTIPLY'
    mul.inputs[1].default_value = rough_var
    nt.links.new(noise.outputs["Fac"], mul.inputs[0])
    add = nt.nodes.new("ShaderNodeMath")
    add.operation = 'ADD'
    add.inputs[1].default_value = rough_base
    nt.links.new(mul.outputs[0], add.inputs[0])
    nt.links.new(add.outputs[0], bsdf.inputs["Roughness"])
    # Bump: 轻微表面起伏
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = bump_strength
    bump.inputs["Distance"].default_value = 0.05
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat

def principled(name, color_hex, roughness=0.5, metallic=0.0,
               emission_hex=None, emission_strength=0.0,
               transmission=0.0, noise_scale=8.0, rough_var=0.15,
               bump_strength=0.02):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = hex_linear(color_hex)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if transmission:
        bsdf.inputs["Transmission Weight"].default_value = transmission
        bsdf.inputs["IOR"].default_value = 1.4
    if emission_hex is not None:
        bsdf.inputs["Emission Color"].default_value = hex_linear(emission_hex)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    add_noise(mat, scale=noise_scale, rough_base=roughness,
              rough_var=rough_var, bump_strength=bump_strength)
    return mat

# 白灯盘: 轻微噪波
MAT_HOUSING = principled("cl-lights_housing_white", "#E8E8E8",
                         roughness=0.5, noise_scale=6.0, rough_var=0.12,
                         bump_strength=0.015)
# 金属吊杆/顶座: 细噪波
MAT_ROD = principled("cl-lights_rod_metal", "#8A8F94",
                     roughness=0.35, metallic=0.85,
                     noise_scale=20.0, rough_var=0.10, bump_strength=0.008)
# 灯管: 乳白半透明 + 弱自发光 (0.8, v1 是 2.0 过亮, 按返工要求改弱)
MAT_TUBE = principled("cl-lights_tube_milky", "#F5F0E0",
                      roughness=0.3, emission_hex="#FFF2D9",
                      emission_strength=0.8, transmission=0.35,
                      noise_scale=12.0, rough_var=0.08, bump_strength=0.005)
# 灯管端盖: 浅灰塑料
MAT_CAP = principled("cl-lights_endcap_grey", "#C9CDD1",
                     roughness=0.55, noise_scale=10.0, rough_var=0.12,
                     bump_strength=0.01)

# ---- 集合 ----
coll = bpy.data.collections.new("cl-lights")
bpy.context.scene.collection.children.link(coll)
piece_objs = []

def _register(ob):
    coll.objects.link(ob)
    bpy.context.scene.collection.objects.unlink(ob)
    piece_objs.append(ob)
    return ob

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
        mod.limit_method = 'ANGLE'
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.modifier_apply(modifier=mod.name)
    ob.data.materials.append(mat)
    return _register(ob)

def add_cylinder_x(name, loc, radius, depth, mat):
    """沿 x 轴的圆柱 (灯管): 默认圆柱沿 z, 绕 y 转 90°。"""
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth,
                                        location=loc, vertices=16)
    ob = bpy.context.active_object
    ob.name = name
    ob.rotation_euler = (0, math.radians(90), 0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(mat)
    return _register(ob)

def add_cylinder_z(name, loc, radius, depth, mat):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth,
                                        location=loc, vertices=16)
    ob = bpy.context.active_object
    ob.name = name
    ob.data.materials.append(mat)
    return _register(ob)

# ---- 6 组灯具: 2 排 x 3 列 ----
# 灯盘: 1.2(x) x 0.24(y) x 0.06(z), 顶面 z=2.92 -> 中心 z=2.89, 底面 2.86
# 灯管: r=0.016, 长 1.10, 沿 x, y=±0.05, 中心 z=2.845 (底面 2.829, 微凸出灯盘底面)
# 端盖: 0.03 x 0.16 x 0.05, x=±0.565, 中心 z=2.845, 盖住灯管两端
# 吊杆: r=0.012, z 2.92->3.0 (实长 0.08), 中心 z=2.96, 每组 2 根, x 偏移 ±0.45
# 顶座: 0.10 x 0.05 x 0.015, 中心 z=2.9925 (顶面贴天花板 3.0), 每根吊杆 1 个
ROWS_Y = [-1.21, 1.21]
COLS_X = [-3.23, 0.0, 3.23]

for ri, y in enumerate(ROWS_Y, start=1):
    for ci, x in enumerate(COLS_X, start=1):
        tag = "r%dc%d" % (ri, ci)
        add_box("cl-lights_housing_%s" % tag, (x, y, 2.89),
                (1.2, 0.24, 0.06), MAT_HOUSING, bevel=0.008)
        for k, dy in enumerate((-0.05, 0.05), start=1):
            add_cylinder_x("cl-lights_tube_%s_%d" % (tag, k),
                           (x, y + dy, 2.845), 0.016, 1.10, MAT_TUBE)
        for k, dx in enumerate((-0.565, 0.565), start=1):
            add_box("cl-lights_endcap_%s_%d" % (tag, k),
                    (x + dx, y, 2.845), (0.03, 0.16, 0.05), MAT_CAP)
        for k, dx in enumerate((-0.45, 0.45), start=1):
            add_cylinder_z("cl-lights_rod_%s_%d" % (tag, k),
                           (x + dx, y, 2.96), 0.012, 0.08, MAT_ROD)
            add_box("cl-lights_mount_%s_%d" % (tag, k),
                    (x + dx, y, 2.9925), (0.10, 0.05, 0.015), MAT_ROD,
                    bevel=0.004)

print("fixtures built: %d objects" % len(piece_objs))  # 6*(1+2+2+2+2)=54
assert len(piece_objs) == 54, "object count wrong: %d" % len(piece_objs)

# 几何自查: 灯盘顶面 2.92, 吊杆顶 3.0, 全部在房间内 (x ±4.84, y ±3.63)
for ob in piece_objs:
    assert -4.84 <= ob.location.x <= 4.84, "out of room x: %s" % ob.name
    assert -3.63 <= ob.location.y <= 3.63, "out of room y: %s" % ob.name
    assert 2.82 <= ob.location.z <= 3.0, "out of room z: %s" % ob.name
print("layout rows y=%s cols x=%s" % (ROWS_Y, COLS_X))

# ---- 存 .blend (只含本件, 先落盘) ----
os.makedirs(os.path.dirname(BLEND_PATH), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("blend saved:", BLEND_PATH, os.path.getsize(BLEND_PATH))

# ---- 导出 .glb (只选本件对象) ----
bpy.ops.object.select_all(action='DESELECT')
for ob in piece_objs:
    ob.select_set(True)
bpy.context.view_layer.objects.active = piece_objs[0]
os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format='GLB',
                           use_selection=True, export_apply=True)
print("glb exported:", GLB_PATH, os.path.getsize(GLB_PATH))

# ---- 回读校验 ----
n_before = len(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB_PATH)
n_imported = len(bpy.data.objects) - n_before
print("gltf reimport: %d objects imported" % n_imported)
assert n_imported == len(piece_objs), \
    "glTF reimport count mismatch: %d vs %d" % (n_imported, len(piece_objs))
imported = [o for o in bpy.data.objects if o not in piece_objs]
for ob in imported:
    print("  imported:", ob.name, "loc:",
          tuple(round(v, 3) for v in ob.location))

print("DONE cl-lights")
