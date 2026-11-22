# cl-ac v2: 教室内部 - 空调 (2 台美的 5 匹柜机 KFR-120LW/BP3SDN8Y-PA401(2))
# 返工: 旧版只有方块柜体, 本版按真实结构做: 圆角柜体 + 出风口格栅 + 显示屏
#       + 底座 + 背面铜管/线缆 + 遥控器; 材质全加程序化 Noise 纹理, 结构件倒角
# 局部坐标: 房间中心原点, x=长 9.68m (-4.84~+4.84), y=宽 7.26m (-3.63~+3.63), z 0~3.0m
# 黑板墙在 x=-4.84 一侧; 窗沿 y=-3.63 一侧; 门在 x=+4.84 墙上
# 实测数据 (data/classroom.json): 制冷 12.15kW / 输入 3.5kW, 制热 14.15kW / 输入 3.85kW, 每间 2 台
# 位置: 1 号黑板侧墙角 (-4.4, -3.2), 2 号后墙角 (4.4, 3.2), 对角布置, 出风面朝房间中心
# 交付: 本脚本 + cl-ac.blend + assets/models/cl-ac.glb; 不渲染预览 (渲染走 GitHub Actions)
import bpy
import math
import os
from mathutils import Quaternion, Vector

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
SCRIPT_DIR = os.path.join(BASE, "assets/blender/classroom")
MODEL_PATH = os.path.join(BASE, "assets/models/cl-ac.glb")
BLEND_PATH = os.path.join(SCRIPT_DIR, "cl-ac.blend")
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

# ---------- 材质: Principled BSDF + 程序化 Noise (粗糙度/Bump 变化, 不许全平) ----------
def make_material(name, hex_color, roughness=0.5, metallic=0.0,
                  noise_scale=8.0, noise_strength=0.15, rough_lo=0.0, rough_hi=0.0,
                  alpha=1.0, specular=0.5):
    """rough_lo/hi: Noise 映射到粗糙度的范围; 为 0 时用固定 roughness."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = hex_to_linear(hex_color)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Specular IOR Level"].default_value = specular
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = noise_scale
    noise.inputs["Detail"].default_value = 2.0
    noise.inputs["Roughness"].default_value = 0.7
    if rough_lo or rough_hi:
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.25
        ramp.color_ramp.elements[0].color = (rough_lo, rough_lo, rough_lo, 1.0)
        ramp.color_ramp.elements[1].position = 0.75
        ramp.color_ramp.elements[1].color = (rough_hi, rough_hi, rough_hi, 1.0)
        nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], bsdf.inputs["Roughness"])
    else:
        bsdf.inputs["Roughness"].default_value = roughness
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = noise_strength
    bump.inputs["Distance"].default_value = 0.02
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat

# 白色塑料外壳: 轻微噪波
MAT_SHELL = make_material("ac_shell_white", "#EDEDED", noise_scale=6.0,
                          noise_strength=0.10, rough_lo=0.28, rough_hi=0.42)
# 前面板: 同色, 纹理略细
MAT_PANEL = make_material("ac_front_panel", "#E4E4E4", noise_scale=10.0,
                          noise_strength=0.08, rough_lo=0.30, rough_hi=0.44)
# 金属出风口格栅: 银灰金属
MAT_METAL = make_material("ac_grille_metal", "#9AA0A6", metallic=0.85,
                          noise_scale=14.0, noise_strength=0.12,
                          rough_lo=0.30, rough_hi=0.48)
# 格栅深底
MAT_DARK = make_material("ac_grille_dark", "#2E3338", noise_scale=12.0,
                         noise_strength=0.10, rough_lo=0.55, rough_hi=0.70)
# 深色显示屏玻璃: 淡蓝灰, 透明度 + 镜面反射
MAT_SCREEN = make_material("ac_display_glass", "#8FA8B8", roughness=0.06,
                           metallic=0.15, noise_scale=20.0, noise_strength=0.03,
                           alpha=0.92, specular=1.0)
# 底座: 深灰塑料
MAT_BASE = make_material("ac_base", "#3A3F44", noise_scale=8.0,
                         noise_strength=0.12, rough_lo=0.55, rough_hi=0.70)
# 铜管: 铜色金属
MAT_COPPER = make_material("ac_copper", "#B87333", metallic=0.9,
                           noise_scale=18.0, noise_strength=0.10,
                           rough_lo=0.25, rough_hi=0.40)
# 保温管: 米白
MAT_PIPE = make_material("ac_pipe_white", "#D8D2C4", noise_scale=8.0,
                         noise_strength=0.10, rough_lo=0.55, rough_hi=0.70)
# 线缆: 黑
MAT_CABLE = make_material("ac_cable", "#1E1E1E", noise_scale=10.0,
                          noise_strength=0.10, rough_lo=0.60, rough_hi=0.75)
# 铭牌色块
MAT_PLATE = make_material("ac_nameplate", "#2F4A5A", noise_scale=10.0,
                          noise_strength=0.08, rough_lo=0.40, rough_hi=0.55)

# ---------- 小工具 ----------
def add_box(name, loc, dims, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if mat:
        obj.data.materials.append(mat)
    return obj

def add_cyl(name, loc, radius, depth, mat, rot=(0, 0, 0), vertices=24):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
                                        depth=depth, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    if mat:
        obj.data.materials.append(mat)
    return obj

def add_bevel(obj, width=0.015, segments=2):
    bpy.context.view_layer.objects.active = obj
    mod = obj.modifiers.new("bevel", "BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"
    bpy.ops.object.modifier_apply(modifier=mod.name)

# ---------- 单台柜机原型 (局部: 原点在底部中心, 前面板朝 +y, 顶面 z=1.80) ----------
# 柜体: 0.55(x) x 0.38(y) x 1.72(z), 圆角 (倒角 0.03), 白色塑料
proto_parts = []
body = add_box("ac_body", (0, 0, 0.92), (0.55, 0.38, 1.72), MAT_SHELL)
add_bevel(body, width=0.03, segments=3)
proto_parts.append(body)
# 前面板: 微凸圆角板 0.50 x 0.02 x 1.45, z 0.30~1.75
panel = add_box("ac_front_panel", (0, 0.195, 1.02), (0.50, 0.02, 1.45), MAT_PANEL)
add_bevel(panel, width=0.008, segments=2)
proto_parts.append(panel)
# 顶部出风口: 前面板上部深底凹槽 0.42 x 0.20 (z 1.50~1.70)
proto_parts.append(add_box("ac_top_recess", (0, 0.206, 1.60), (0.42, 0.008, 0.20), MAT_DARK))
# 顶部出风口格栅: 5 根金属横条 (沿 x, z 排布), 微凸
for i in range(5):
    z = 1.525 + i * 0.0375
    proto_parts.append(add_box("ac_top_slat", (0, 0.210, z), (0.40, 0.010, 0.016), MAT_METAL))
# 出风口两侧导风小翼: 左右各一竖条
for x in (-0.20, 0.20):
    proto_parts.append(add_box("ac_top_wing", (x, 0.210, 1.60), (0.012, 0.010, 0.20), MAT_METAL))
# 显示屏: 上部深色玻璃 0.14 x 0.06, z=1.42, 淡蓝灰带反光
proto_parts.append(add_box("ac_display", (-0.12, 0.208, 1.42), (0.14, 0.008, 0.06), MAT_SCREEN))
# 显示屏下小指示灯: 2 个小圆点 (小圆柱朝 +y)
for x in (-0.02, 0.03):
    proto_parts.append(add_cyl("ac_led", (x, 0.208, 1.42), 0.006, 0.010, MAT_SCREEN,
                               rot=(math.radians(90), 0, 0), vertices=12))
# 前面板竖向接缝: 中线偏右细缝, z 0.45~1.30
proto_parts.append(add_box("ac_front_seam", (0.12, 0.207, 0.875), (0.006, 0.006, 0.85), MAT_DARK))
# 底部进风口格栅: 深底面板 + 4 根金属横条, z 0.12~0.42
proto_parts.append(add_box("ac_intake_panel", (0, 0.206, 0.27), (0.46, 0.008, 0.30), MAT_DARK))
for i in range(4):
    z = 0.16 + i * 0.07
    proto_parts.append(add_box("ac_intake_slat", (0, 0.210, z), (0.44, 0.010, 0.018), MAT_METAL))
# 底座: 0.56 x 0.39 x 0.06, 深灰, 倒角
base = add_box("ac_base", (0, 0, 0.03), (0.56, 0.39, 0.06), MAT_BASE)
add_bevel(base, width=0.01, segments=2)
proto_parts.append(base)
# 侧面铭牌色块: -x 侧面, 靠前下方
proto_parts.append(add_box("ac_nameplate", (-0.276, -0.05, 1.15), (0.006, 0.12, 0.18), MAT_PLATE))
# 背面铜管/线缆 (背面 -y 侧, 贴后壁, z 0.10~1.30):
#   2 根铜管 (气管/液管, 直径 0.016/0.012) + 1 根白保温管 (直径 0.03) + 1 根黑电源线 (直径 0.01)
proto_parts.append(add_cyl("ac_copper_gas", (0.10, -0.205, 0.70), 0.008, 1.20, MAT_COPPER, vertices=12))
proto_parts.append(add_cyl("ac_copper_liquid", (0.14, -0.205, 0.70), 0.006, 1.20, MAT_COPPER, vertices=12))
proto_parts.append(add_cyl("ac_pipe_insul", (-0.10, -0.210, 0.70), 0.015, 1.20, MAT_PIPE, vertices=12))
proto_parts.append(add_cyl("ac_cable_power", (-0.15, -0.205, 0.70), 0.005, 1.20, MAT_CABLE, vertices=10))
# 背面管口小弯头: 顶部横向短管, 连向墙面方向
proto_parts.append(add_cyl("ac_copper_elbow", (0.12, -0.205, 1.32), 0.008, 0.10, MAT_COPPER,
                           rot=(0, math.radians(90), 0), vertices=12))
# 遥控器: 平放在柜顶, 0.05 x 0.16 x 0.02, 白壳 + 深色小屏 + 2 钮, 倒角
remote = add_box("ac_remote", (0.12, 0.0, 1.795), (0.05, 0.16, 0.02), MAT_SHELL)
add_bevel(remote, width=0.005, segments=2)
proto_parts.append(remote)
proto_parts.append(add_box("ac_remote_screen", (0.12, 0.03, 1.806), (0.032, 0.05, 0.006), MAT_SCREEN))
proto_parts.append(add_cyl("ac_remote_btn", (0.12, -0.04, 1.807), 0.008, 0.006, MAT_DARK, vertices=12))

# ---------- 排布 (出风面朝房间中心, 对角布置, 不挡黑板/窗) ----------
# 1 号: 黑板侧墙角 (-4.4, -3.2), 前面板朝 +x -> 绕 Z 转 -90 度
# 2 号: 后墙角 (4.4, 3.2), 前面板朝 -x -> 绕 Z 转 +90 度
units = []  # (unit_name, [objects])
for prefix, loc, rot_z in (
    ("ac_front", (-4.4, -3.2, 0), math.radians(-90)),
    ("ac_rear", (4.4, 3.2, 0), math.radians(90)),
):
    rz = Quaternion((0, 0, 1), rot_z)  # 绕 Z 的整体朝向
    loc_v = Vector(loc)
    objs = []
    for part in proto_parts:
        u = part.copy()
        u.data = part.data  # 共享网格
        u.name = "%s_%s" % (prefix, part.name)
        # 原型件带局部偏移 (如柜体中心 z=0.92): 偏移也要绕 Z 旋转后再加到角点上
        u.location = loc_v + rz @ Vector(part.location)
        u.rotation_mode = "QUATERNION"
        u.rotation_quaternion = rz @ part.rotation_quaternion
        bpy.context.collection.objects.link(u)
        objs.append(u)
    units.append((prefix, objs))

# 删原型件
for part in proto_parts:
    bpy.data.objects.remove(part, do_unlink=True)

# ---------- 自查: 两台都在、落地、高度 1.80 ----------
bpy.context.view_layer.update()  # 刷新 matrix_world, 否则 bound_box 还是单位矩阵
all_objs = [o for _, objs in units for o in objs]
print("ac unit count:", len(units), "object count:", len(all_objs))
for prefix, objs in units:
    body_obj = next(o for o in objs if o.name.endswith("_ac_body"))
    ws = [body_obj.matrix_world @ Vector(c) for c in body_obj.bound_box]
    xs = [v.x for v in ws]; ys = [v.y for v in ws]
    zs = [v.z for v in ws]
    # 整台最低点 (底座底) 应贴地, 最高点 (遥控器屏) 约 1.81
    all_ws_z = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    zmin = min(v.z for v in all_ws_z); zmax = max(v.z for v in all_ws_z)
    print(prefix, "body loc:", tuple(round(v, 3) for v in body_obj.location),
          "rot_z_deg:", round(math.degrees(body_obj.matrix_world.to_euler()[2]), 1),
          "x:", round(min(xs), 2), "-", round(max(xs), 2),
          "y:", round(min(ys), 2), "-", round(max(ys), 2),
          "unit world z:", round(zmin, 2), "-", round(zmax, 2))
    assert abs(zmin) < 0.02, "unit not standing on floor: zmin=%s" % zmin
    assert abs(zmax - 1.81) < 0.03, "unit height wrong: zmax=%s" % zmax
# 位置自查: 1 号贴黑板墙 (x -4.6~-4.2, 距墙 0.24m) 与窗墙 (y -3.5~-2.9);
# 2 号贴后墙 (x 4.2~4.6) 与对侧墙 (y 2.9~3.5); 均不挡黑板 (黑板在 x=-4.84 墙面中央) 与窗 (y=-3.63 墙面)

# ---------- 存 .blend (先落盘) ----------
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("blend saved:", BLEND_PATH, os.path.getsize(BLEND_PATH))

# ---------- 导出 .glb (只选本件对象) ----------
bpy.ops.object.select_all(action="DESELECT")
for o in all_objs:
    o.select_set(True)
bpy.ops.export_scene.gltf(
    filepath=MODEL_PATH,
    export_format="GLB",
    use_selection=True,
    export_apply=True,
)
print("glb exported:", MODEL_PATH, os.path.getsize(MODEL_PATH))

# ---------- 回读校验: GLB 节点坐标验证两台柜机位置都在 ----------
bpy.ops.object.select_all(action="DESELECT")
bpy.ops.import_scene.gltf(filepath=MODEL_PATH)
imported = list(bpy.context.selected_objects)
print("gltf reimport objects:", len(imported))
assert len(imported) > 0, "glTF reimport failed: no objects"
bodies = [o for o in imported if "ac_body" in o.name]  # 回读时同名原对象仍在场景, 导入件带 .001 后缀
print("gltf reimport ac_body nodes:", len(bodies))
for b in sorted(bodies, key=lambda o: o.name):
    print("reimport", b.name, "loc:",
          tuple(round(v, 3) for v in b.location),
          "dims:", tuple(round(v, 3) for v in b.dimensions))
assert len(bodies) == 2, "expected 2 AC bodies in GLB, got %s" % len(bodies)
locs = sorted((round(o.location.x, 2), round(o.location.y, 2)) for o in bodies)
assert (-4.4, -3.2) in locs and (4.4, 3.2) in locs, "AC positions wrong in GLB: %s" % (locs,)
print("GLB positions verified: ac_front (-4.4, -3.2), ac_rear (4.4, 3.2)")

# 删回读的临时对象
bpy.ops.object.delete()
# 删 Blender 产生的 .blend1 备份
blend1 = BLEND_PATH + "1"
if os.path.exists(blend1):
    os.remove(blend1)
    print("removed .blend1 backup")
print("DONE cl-ac")
