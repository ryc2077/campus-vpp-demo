# ov-dorm v3: 宿舍 A、B 楼体换装 (R2-T21a, 2026-11-24)
# 各 20(x) x 12(y) x 16(z) m, 5 floors.
#   dormA centre Blender (84, -8, 0), dormB centre Blender (84, -44, 0)
# 网上模型: Grab3D 公寓楼 (CC0 1.0),
#   assets/external/buildings/grab3d/apartment-building-grab3d.glb
# 实测 (Blender 4.2.0, 见 BLENDER_MODELS.md §20 / SOURCES.md §12):
#   body 15.56x11.56x16.57 + details 15.26x13.82x14.77 (真窗带/阳台/白线脚)
#   + roof_terrace 13.6x9.97x2.78 (屋顶露台, z 15.52-18.30, 删除)
#   + shrubs 13.62x11.11x12.23 (灌木/窗边绿植, 删除)。
#   联合包围盒 15.56x13.82x18.30; 任务单缩放 x1.29/x0.87/x0.87 是按含露台
#   的联合高 18.30 算的, 露台删除后剩余体高 16.57, 故 z 改按体高缩放
#   (15.7/16.57 = x0.947), 楼体顶落到旧外包络的 15.7, 再加屋顶板与女儿墙
#   至 16.40 (SPEC 高 16m 为楼体高, 女儿墙顶 16.40 沿用旧件)。
#   x 20/15.56 = x1.285, y 12/13.82 = x0.868 (与任务单一致)。
# 配色: 模型自带蜜桃色砖墙 + 白线脚 + 薄荷绿阳台 + 蓝玻璃, 即浅橙系
#   (任务单 "改浅橙 #F6D9C0"), 保留原 PBR 贴图不重染; A/B 两栋同模型同色
#   (真实宿舍 A/B 本就同型; 旧件米白/蓝灰分色由模型自带蜜桃色取代)。
# 层高 (沿用旧件外包络): F1 0.5-4.0 (净高 3.5m), F2-F5 各 3.0m 至 16.0;
#   楼体顶 15.7, 屋顶板 15.7-15.85, 女儿墙 15.85-16.40。
# 窗带/阳台是模型自带真实几何, 不另加窗带; 只加勒脚/楼层分缝/屋顶板/
# 女儿墙/屋顶设备/正门 (西立面, 朝校园内侧, 沿用旧件)/台阶。
# 楼间绿地 (x 74-94, y -38..-14, 起伏草坪 + 灌木) 沿用旧件, 不动范围。
# 两栋共用一套导入几何 (linked duplicate)。
# 不做烘焙: 模型自带真实 PBR 贴图 (2048 atlas, 本件降采样至 1024 以控
#   .glb 体积); 新增小件走 _pbr_apply hook (屋顶/混凝土/檐口) 或纯色。
# 本次不渲染 (用户新规: 渲染全部走 GitHub Actions):
#   只做 建模 -> 存 .blend -> 导出 .glb -> 回读校验, 打印 DONE ov-dorm。

import bpy
import math
import os
import random
from mathutils import Vector, Matrix

PIECE = "ov-dorm"
BASE = os.path.expanduser("~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
PY_DIR = os.path.join(BASE, "assets/blender/overview")
EXT_DIR = os.path.join(BASE, "assets/external/buildings/grab3d")
SRC_GLB = os.path.join(EXT_DIR, "apartment-building-grab3d.glb")
BLEND_PATH = os.path.join(PY_DIR, "ov-dorm.blend")
GLB_PATH = os.path.join(BASE, "assets/models/ov-dorm.glb")

W, D = 20.0, 12.0      # footprint x, y
BODY_TOP = 15.7        # 楼体顶 (屋顶板底)
MID = (84.0, -26.0)    # 两栋中点 (楼间绿地中心)
DORMS = (("dormA", 84.0, -8.0), ("dormB", 84.0, -44.0))


def hex_rgb(h):
    """Hex sRGB -> linear RGB (Blender stores Base Color linear)."""
    h = h.lstrip("#")

    def srgb_to_lin(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (srgb_to_lin(int(h[i:i + 2], 16)) for i in (0, 2, 4))
    return (r, g, b, 1.0)


def _new_mat(name, hexcol, rough=0.85, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = hex_rgb(hexcol)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    return m


_BLANK = None


def _blank_image():
    global _BLANK
    if _BLANK is None:
        _BLANK = bpy.data.images.new("pbr_placeholder", width=4, height=4, alpha=False)
    return _BLANK


def pbr_ready_mat(name, hexcol, rough=0.85):
    """Principled + BaseColor/Roughness/Normal image nodes (placeholders),
    _pbr_apply 会把占位图换成真实 PBR 贴图并按世界尺寸重投影 UV。"""
    m = _new_mat(name, hexcol, rough)
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    for inp, cs in (("Base Color", "sRGB"), ("Roughness", "Non-Color"),
                    ("Normal", "Non-Color")):
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = _blank_image()
        tex.image.colorspace_settings.name = cs
        if inp == "Normal":
            nmap = nt.nodes.new("ShaderNodeNormalMap")
            nt.links.new(tex.outputs["Color"], nmap.inputs["Color"])
            nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
        else:
            nt.links.new(tex.outputs["Color"], bsdf.inputs[inp])
    return m


# PBR_MAP["ov-dorm"]: 屋顶 / 混凝土 / 檐口 (墙面用模型自带 PBR, 不进 hook)
MAT_ROOF = pbr_ready_mat("Roof_DarkGrey_424A52_tex", "#424A52", 0.92)
MAT_CONC = pbr_ready_mat("Concrete_B9B3A8_tex", "#B9B3A8", 0.95)
MAT_BAND = pbr_ready_mat("Cornice_D8D2C4_tex", "#D8D2C4", 0.9)
MAT_METAL = _new_mat("MetalGrey_tex", "#C0C5C9", 0.55, 0.3)
MAT_GRILLE = _new_mat("AC_Grille_3A4046_tex", "#3A4046", 0.7, 0.1)
MAT_DOOR = _new_mat("Door_Dark_3A4046", "#3A4046", 0.6, 0.2)
MAT_DOOR_GLASS = _new_mat("Door_Glass_9FC3D8", "#9FC3D8", 0.25, 0.1)
MAT_GRASS = _new_mat("Grass_69B45E", "#69B45E", 1.0)
MAT_BUSH = _new_mat("Bush_4F7D3A", "#4F7D3A", 0.9)


def _vbox(objs):
    """顶点实算包围盒 (bmesh/transform 后 bound_box 会 stale, 不能用)。"""
    xs, ys, zs = [], [], []
    for o in objs:
        for v in o.data.vertices:
            w = o.matrix_world @ v.co
            xs.append(w.x)
            ys.append(w.y)
            zs.append(w.z)
    return min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)


def build():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    assert os.path.exists(SRC_GLB), "missing source GLB: %s" % SRC_GLB
    bpy.ops.import_scene.gltf(filepath=SRC_GLB)
    # 删导入的空父物体与屋顶露台/灌木 (只留 body + details)
    for o in list(bpy.context.scene.objects):
        if o.type != "MESH":
            bpy.data.objects.remove(o, do_unlink=True)
    keep = []
    for o in list(bpy.context.scene.objects):
        if o.type != "MESH":
            continue
        if "roof_terrace" in o.name or "shrubs" in o.name:
            print("dorm: removing", o.name)
            bpy.data.objects.remove(o, do_unlink=True)
        else:
            keep.append(o)
            print("dorm: keeping", o.name)
    assert len(keep) == 2, "expected body+details, got %d" % len(keep)
    # 贴图降采样至 1024 (控 .glb 体积; 总览距离足够)
    for im in list(bpy.data.images):
        if im.name in ("Render Result", "Viewer Node"):
            continue
        if max(im.size) > 1024:
            print("dorm: downscale image", im.name, im.size[:])
            im.scale(1024, 1024)
    # 实测联合包围盒 -> 缩放至 20x12x15.7
    x0, x1, y0, y1, z0, z1 = _vbox(keep)
    print("dorm src union bbox x[%.2f,%.2f] y[%.2f,%.2f] z[%.2f,%.2f]" % (
        x0, x1, y0, y1, z0, z1))
    sx = W / (x1 - x0)
    sy = D / (y1 - y0)
    sz = BODY_TOP / (z1 - z0)
    print("dorm scale x%.3f y%.3f z%.3f" % (sx, sy, sz))
    for o in keep:
        m = Matrix.Diagonal((sx, sy, sz, 1.0)) @ Matrix.Translation(
            (-(x0 + x1) / 2.0, -(y0 + y1) / 2.0, -z0))
        o.data.transform(m)
        o.data.update()
    x0, x1, y0, y1, z0, z1 = _vbox(keep)
    print("dorm scaled union bbox x[%.2f,%.2f] y[%.2f,%.2f] z[%.2f,%.2f]" % (
        x0, x1, y0, y1, z0, z1))
    assert abs((x1 - x0) - W) < 0.05
    assert abs((y1 - y0) - D) < 0.05
    assert abs((z1 - z0) - BODY_TOP) < 0.05

    building = []

    def box(name, cx, cy, z0_, z1_, sx_, sy_, mat, bevel=0.05):
        bpy.ops.mesh.primitive_cube_add(location=(cx, cy, (z0_ + z1_) / 2.0))
        o = bpy.context.active_object
        o.name = name
        o.dimensions = (sx_, sy_, z1_ - z0_)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        if bevel and min(sx_, sy_, z1_ - z0_) > 2 * bevel + 0.02:
            mod = o.modifiers.new("EdgeSoft", "BEVEL")
            mod.width = bevel
            mod.segments = 2
            mod.limit_method = "ANGLE"
        o.data.materials.append(mat)
        building.append(o)
        return o

    def place_dorm(tag, cx, cy, src_objs):
        """把缩放好的 body+details 移到 (cx, cy); 首栋直接移, 次栋 linked 复制。"""
        if tag == "dormA":
            for o in src_objs:
                o.location = (cx, cy, 0.0)
                building.append(o)
            return src_objs
        bpy.ops.object.select_all(action="DESELECT")
        for o in src_objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = src_objs[0]
        bpy.ops.object.duplicate(linked=True)
        dup = []
        for o in bpy.context.selected_objects:
            o.name = tag + "_" + o.name
            o.location = (cx, cy, 0.0)
            dup.append(o)
            building.append(o)
        bpy.ops.object.select_all(action="DESELECT")
        return dup

    def finish_dorm(tag, cx, cy):
        # ---- 勒脚 (0-0.5) ----
        box(tag + "_plinth", cx, cy, 0.0, 0.5, W + 0.6, D + 0.6, MAT_CONC, bevel=0.04)
        box(tag + "_plinth_cap", cx, cy, 0.5, 0.68, W + 0.7, D + 0.7, MAT_BAND, bevel=0.03)
        # ---- 楼层分缝 (檐口线脚, 层线 4.0/7.0/10.0/13.0) ----
        for z in (4.0, 7.0, 10.0, 13.0):
            box("%s_cornice_z%s" % (tag, z), cx, cy, z - 0.14, z + 0.14,
                W + 0.3, D + 0.3, MAT_BAND, bevel=0.03)
        # ---- 屋顶板 15.7-15.85 + 女儿墙 15.85-16.40 ----
        box(tag + "_roof_slab", cx, cy, 15.7, 15.85, W, D, MAT_ROOF, bevel=0.03)
        PW, PD, T = W - 0.6, D - 0.6, 0.30
        box(tag + "_parapet_S", cx, cy - (PD / 2 - T / 2), 15.85, 16.32, PW, T, MAT_CONC, bevel=0.02)
        box(tag + "_parapet_N", cx, cy + (PD / 2 - T / 2), 15.85, 16.32, PW, T, MAT_CONC, bevel=0.02)
        box(tag + "_parapet_W", cx - (PW / 2 - T / 2), cy, 15.85, 16.32, T, PD - 2 * T, MAT_CONC, bevel=0.02)
        box(tag + "_parapet_E", cx + (PW / 2 - T / 2), cy, 15.85, 16.32, T, PD - 2 * T, MAT_CONC, bevel=0.02)
        box(tag + "_parapet_cap_S", cx, cy - (PD / 2 - T / 2), 16.32, 16.40, PW, T + 0.12, MAT_CONC, bevel=0.02)
        box(tag + "_parapet_cap_N", cx, cy + (PD / 2 - T / 2), 16.32, 16.40, PW, T + 0.12, MAT_CONC, bevel=0.02)
        box(tag + "_parapet_cap_W", cx - (PW / 2 - T / 2), cy, 16.32, 16.40, T + 0.12, PD - 2 * T, MAT_CONC, bevel=0.02)
        box(tag + "_parapet_cap_E", cx + (PW / 2 - T / 2), cy, 16.32, 16.40, T + 0.12, PD - 2 * T, MAT_CONC, bevel=0.02)
        # ---- 屋顶设备小盒 ----
        box(tag + "_roof_equip", cx - 5.0, cy - 2.0, 15.85, 17.0, 2.2, 1.6, MAT_METAL, bevel=0.04)
        box(tag + "_roof_equip_lid", cx - 5.0, cy - 2.0, 17.0, 17.12, 2.4, 1.8, MAT_ROOF, bevel=0.02)
        box(tag + "_roof_equip_louvre", cx - 5.0, cy - 2.0 - 0.82, 16.2, 16.5, 1.5, 0.05, MAT_GRILLE, bevel=0.0)
        # ---- 正门: 西立面 (朝校园内侧, 沿用旧件) + 雨棚 + 台阶 ----
        box(tag + "_door", cx - (W / 2 + 0.02), cy, 0.5, 2.9, 0.14, 1.8, MAT_DOOR, bevel=0.0)
        box(tag + "_door_glass", cx - (W / 2 + 0.08), cy, 1.2, 2.5, 0.04, 1.2, MAT_DOOR_GLASS, bevel=0.0)
        box(tag + "_canopy", cx - (W / 2 + 0.7), cy, 3.0, 3.16, 1.5, 3.4, MAT_BAND, bevel=0.03)
        for sgn in (-1, 1):
            box("%s_canopy_post_%s" % (tag, "S" if sgn < 0 else "N"),
                cx - (W / 2 + 0.5), cy + sgn * 1.5, 0.5, 3.0, 0.12, 0.12,
                MAT_METAL, bevel=0.0)
        box(tag + "_step_1", cx - (W / 2 + 0.475), cy, 0.34, 0.5, 0.35, 2.8, MAT_CONC, bevel=0.02)
        box(tag + "_step_2", cx - (W / 2 + 0.825), cy, 0.17, 0.34, 0.35, 2.8, MAT_CONC, bevel=0.02)
        box(tag + "_step_3", cx - (W / 2 + 1.175), cy, 0.0, 0.17, 0.35, 2.8, MAT_CONC, bevel=0.02)

    for tag, cx, cy in DORMS:
        place_dorm(tag, cx, cy, keep)
        finish_dorm(tag, cx, cy)

    # ---- 楼间绿地 (沿用旧件): x 74-94, y -38..-14, 起伏草坪 + 灌木 ----
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=24, y_subdivisions=28, size=2.0,
                                    location=(MID[0], MID[1], 0.02))
    lawn = bpy.context.active_object
    lawn.name = "dorm_lawn_between"
    lawn.dimensions = (20.0, 24.0, 0.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for v in lawn.data.vertices:
        lx, ly = v.co.x, v.co.y
        edge = max(0.0, (1.0 - (lx / 10.0) ** 2) * (1.0 - (ly / 12.0) ** 2))
        v.co.z = 0.02 + edge * (0.12 + 0.07 * math.sin(lx * 0.9) * math.cos(ly * 0.7)
                                + 0.05 * math.sin(lx * 2.3 + ly * 1.7))
    lawn.data.materials.append(MAT_GRASS)
    building.append(lawn)
    rng = random.Random(7)
    n_bush = 0
    for i in range(14):
        bx = MID[0] + rng.uniform(-8.5, 8.5)
        by = MID[1] + rng.uniform(-10.5, 10.5)
        if abs(bx - 84.0) < 1.6 and abs(by + 26.0) < 3.0:
            continue
        r = rng.uniform(0.45, 0.75)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0,
                                              location=(bx, by, r * 0.55))
        b = bpy.context.active_object
        b.name = "dorm_bush_%02d" % i
        b.scale = (r, r, r * 0.62)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        b.data.materials.append(MAT_BUSH)
        building.append(b)
        n_bush += 1
    print("shrubs:", n_bush)

    return building


def save_and_export(building):
    os.makedirs(PY_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
    # R2-T9 PBR hook: 只处理本件新增小件的屋顶/混凝土/檐口材质;
    # 模型自带 PBR 材质 (原名) 不在 PBR_MAP 里, 不动。
    _pbr_hook = os.path.join(os.path.dirname(BLEND_PATH), "_pbr_apply.py")
    if os.path.exists(_pbr_hook):
        _pbr_g = {"__name__": "_pbr_apply", "__file__": _pbr_hook}
        exec(compile(open(_pbr_hook).read(), _pbr_hook, "exec"), _pbr_g)
        _pbr_g["apply_pbr"](os.path.splitext(os.path.basename(BLEND_PATH))[0])
    # 模型贴图打包进 .blend (Actions 渲染用; 源 GLB 贴图无文件路径, 不打包会丢)
    for im in list(bpy.data.images):
        if im.users == 0 and im.name not in ("Render Result", "Viewer Node"):
            try:
                bpy.data.images.remove(im)
            except Exception as e:
                print("purge image skip:", im.name, e)
    for im in list(bpy.data.images):
        if im.name in ("Render Result", "Viewer Node"):
            continue
        if im.packed_file is None:
            try:
                im.pack()
                print("packed image:", im.name, im.size[:])
            except Exception as e:
                print("pack image skip:", im.name, e)
    for m in list(bpy.data.materials):
        if m.users == 0:
            try:
                bpy.data.materials.remove(m)
            except Exception as e:
                print("purge material skip:", m.name, e)

    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print("saved blend:", BLEND_PATH)
    bpy.ops.object.select_all(action="DESELECT")
    for o in building:
        o.select_set(True)
    bpy.context.view_layer.objects.active = building[0]
    bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format="GLB",
                               use_selection=True, export_apply=True)
    print("exported glb:", GLB_PATH, "objects:", len(building))
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.import_scene.gltf(filepath=GLB_PATH)
    imported = [o for o in bpy.context.selected_objects]
    print("glb re-import OK, imported objects:", len(imported))
    return imported


building = build()
print("built objects:", len(building))

imported = save_and_export(building)
assert len(imported) == len(building), "glb reimport failed: expected %d objects, got %d" % (len(building), len(imported))

blend1 = BLEND_PATH + "1"
if os.path.exists(blend1):
    os.remove(blend1)

print("DONE ov-dorm")
