# ov-bldA v3: 一号教学楼楼体换装 (R2-T21a, 2026-11-24)
# 40(x) x 15(y) x 19(z) m, 5 floors, Blender centre (-56, 30, 0)
# 网上模型: Grab3D 办公楼 (CC0 1.0),
#   assets/external/buildings/grab3d/office-building-grab3d.glb
# 实测 (Blender 4.2.0, 见 BLENDER_MODELS.md §20 / SOURCES.md §12):
#   body 29.42x18.74x25.55 (底层蓝玻璃核 + 屋顶 deck/ pergola/设备)
#   + facade 32.29x15.38x24.50 (白框玻璃幕墙, 约 7 层, 层线约
#   0/5.25/8/11.4/14.9/18.1/21.75/24.5)
#   + shell 29.78x15.78x18.50 (上部玻璃体, z 3.96-22.46)
#   + ground_slab 36.10x22.20x0.06 (地面基座, 删除)。
#   三件合起来才是整栋楼 (body 单独只有底层核 + 屋顶件, 不能单用);
#   任务单 "body/facade" 的缩放是按单件算的, 本件按联合包围盒整体缩放
#   (保住模型的内外构成, 不产生共面 z-fighting)。
# 窗带重排: 三件在 z=18.1 处横切 (bisect, 保住 F1-F5 五层, 去掉 F6-F7),
#   再整体缩至 40x15x18.1 (x 约 x1.24, y 约 x0.78, z 约 x1.00)。
#   窗高向基本不压 (层高感保留: F1 5.25m 高入口层, 其余 2.75-3.5m,
#   约合 SPEC 3.0m 净高 + 楼板; F1 偏高是模型入口层的特征, 已注明)。
#   任务单的 body 单件缩放 x1.36/x0.80/x0.74 是另一算法 (单件各缩到目标盒),
#   会把三件压进同一个盒子造成共面, 不采用。
# 配色: 模型自带白框 + 蓝玻璃幕墙 (即 SPEC 玻璃 #9FC3D8 系 + 米白框),
#   保留原 PBR 贴图不重染; 新增件按 SPEC: 屋顶深灰 #424A52、女儿墙混凝土、
#   檐口浅色; 与 B 栋以尺寸与檐口/勒脚色区分。
# 层高 (沿用旧件外包络): 楼体顶 18.1, 屋顶板 18.1-18.35, 女儿墙 18.35-19.0。
# 正门: 模型自带东立面雨棚入口 (东侧短边), 保留; 不另加南门。
#   (旧件南门由模型入口取代; 详见 BLENDER_MODELS.md §21。)
# 屋顶设备: 沿用旧件两盒 (高出女儿墙 + 百叶)。
# 注意 (留给终轮整合): ov-windows-roofs 的 A/B 窗带与屋顶细部是按旧实心
#   楼体做的, 与本件玻璃幕墙重叠 (窗带双层、屋顶膜共面); 终轮须更新
#   ov-windows-roofs (A/B 窗带与屋顶膜改 C 栋专用或删除), 本任务不动它。
# 不做烘焙: 模型自带真实 PBR 贴图 (2048 atlas, 本件降采样至 1024 以控
#   .glb 体积); 新增小件走 _pbr_apply hook (屋顶/混凝土/檐口) 或纯色。
# 本次不渲染 (用户新规: 渲染全部走 GitHub Actions):
#   只做 建模 -> 存 .blend -> 导出 .glb -> 回读校验, 打印 DONE ov-bldA。

import bpy
import bmesh
import os
from mathutils import Vector, Matrix

PIECE = "ov-bldA"
BASE = os.path.expanduser("~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
PY_DIR = os.path.join(BASE, "assets/blender/overview")
EXT_DIR = os.path.join(BASE, "assets/external/buildings/grab3d")
SRC_GLB = os.path.join(EXT_DIR, "office-building-grab3d.glb")
BLEND_PATH = os.path.join(PY_DIR, "ov-bldA.blend")
GLB_PATH = os.path.join(BASE, "assets/models/ov-bldA.glb")

CX, CY = -56.0, 30.0   # building centre (Blender x, y)
W, D = 40.0, 15.0      # footprint x, y
BODY_TOP = 18.1        # 楼体顶 (屋顶板底)
CUT_Z = 18.1           # 横切高度: 保住 F1-F5, 去掉 F6-F7


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


# PBR_MAP["ov-bldA"]: 屋顶 / 混凝土 / 檐口 (墙面/玻璃用模型自带 PBR, 不进 hook)
MAT_ROOF = pbr_ready_mat("Roof_DarkGrey_424A52_tex", "#424A52", 0.92)
MAT_CONC = pbr_ready_mat("Concrete_B9B3A8_tex", "#B9B3A8", 0.95)
MAT_BAND = pbr_ready_mat("Cornice_D8D2C4_tex", "#D8D2C4", 0.9)
MAT_METAL = _new_mat("MetalGrey_tex", "#C0C5C9", 0.55, 0.3)
MAT_GRILLE = _new_mat("AC_Grille_3A4046_tex", "#3A4046", 0.7, 0.1)


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
    for o in list(bpy.context.scene.objects):
        if o.type != "MESH":
            bpy.data.objects.remove(o, do_unlink=True)
    keep = []
    for o in list(bpy.context.scene.objects):
        if o.type != "MESH":
            continue
        if "ground_slab" in o.name:
            print("bldA: removing", o.name)
            bpy.data.objects.remove(o, do_unlink=True)
        else:
            keep.append(o)
            print("bldA: keeping", o.name)
    assert len(keep) == 3, "expected body+facade+shell, got %d" % len(keep)
    # 导入对象的 object transform (本例 loc (-0.95, 1.5, 0.06)) 须先烘进
    # mesh 并清零, 否则 _vbox (世界坐标) 与 data.transform (局部坐标)
    # 口径不一致, 中心会偏 t*(1-D) (实测 x 偏 +0.22, y 偏 +0.32)。
    for o in keep:
        if o.data.users > 1:
            o.data = o.data.copy()
        o.data.transform(o.matrix_world)
        o.parent = None
        o.matrix_world = Matrix.Identity(4)
        o.data.update()
    # 贴图降采样至 1024 (控 .glb 体积; 总览距离足够)
    for im in list(bpy.data.images):
        if im.name in ("Render Result", "Viewer Node"):
            continue
        if max(im.size) > 1024:
            print("bldA: downscale image", im.name, im.size[:])
            im.scale(1024, 1024)
    # 横切: 去掉 F6-F7 (bisect 在切面处截断穿面, 不留超高残面)
    for o in keep:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, CUT_Z),
                               plane_no=(0, 0, 1),
                               clear_outer=True, clear_inner=False)
        bm.to_mesh(o.data)
        bm.free()
        o.data.update()
    # 实测联合包围盒 -> 整体缩放至 W x D x BODY_TOP, 落到 (CX, CY, 0)
    x0, x1, y0, y1, z0, z1 = _vbox(keep)
    print("bldA cut union bbox x[%.2f,%.2f] y[%.2f,%.2f] z[%.2f,%.2f]" % (
        x0, x1, y0, y1, z0, z1))
    sx = W / (x1 - x0)
    sy = D / (y1 - y0)
    sz = BODY_TOP / (z1 - z0)
    print("bldA scale x%.3f y%.3f z%.3f" % (sx, sy, sz))
    for o in keep:
        m = Matrix.Translation((CX, CY, 0.0)) @ Matrix.Diagonal((sx, sy, sz, 1.0)) \
            @ Matrix.Translation((-(x0 + x1) / 2.0, -(y0 + y1) / 2.0, -z0))
        o.data.transform(m)
        o.data.update()
    x0, x1, y0, y1, z0, z1 = _vbox(keep)
    print("bldA final bbox x[%.2f,%.2f] y[%.2f,%.2f] z[%.2f,%.2f]" % (
        x0, x1, y0, y1, z0, z1))
    assert abs((x1 - x0) - W) < 0.05
    assert abs((y1 - y0) - D) < 0.05
    assert abs((z1 - z0) - BODY_TOP) < 0.05
    assert abs((x0 + x1) / 2.0 - CX) < 0.05
    assert abs((y0 + y1) / 2.0 - CY) < 0.05

    building = list(keep)

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

    # ---- 勒脚 (0-0.5) ----
    box("bldA_plinth", CX, CY, 0.0, 0.5, W + 0.6, D + 0.6, MAT_CONC, bevel=0.04)
    box("bldA_plinth_cap", CX, CY, 0.5, 0.68, W + 0.7, D + 0.7, MAT_BAND, bevel=0.03)
    # ---- 屋顶板 18.1-18.35 (封横切口) + 女儿墙 18.35-19.0 ----
    box("bldA_roof_slab", CX, CY, 18.1, 18.35, W, D, MAT_ROOF, bevel=0.03)
    PW, PD, T = W - 0.6, D - 0.6, 0.30
    box("bldA_parapet_S", CX, CY - (PD / 2 - T / 2), 18.35, 18.92, PW, T, MAT_CONC, bevel=0.02)
    box("bldA_parapet_N", CX, CY + (PD / 2 - T / 2), 18.35, 18.92, PW, T, MAT_CONC, bevel=0.02)
    box("bldA_parapet_W", CX - (PW / 2 - T / 2), CY, 18.35, 18.92, T, PD - 2 * T, MAT_CONC, bevel=0.02)
    box("bldA_parapet_E", CX + (PW / 2 - T / 2), CY, 18.35, 18.92, T, PD - 2 * T, MAT_CONC, bevel=0.02)
    box("bldA_parapet_cap_S", CX, CY - (PD / 2 - T / 2), 18.92, 19.0, PW, T + 0.12, MAT_CONC, bevel=0.02)
    box("bldA_parapet_cap_N", CX, CY + (PD / 2 - T / 2), 18.92, 19.0, PW, T + 0.12, MAT_CONC, bevel=0.02)
    box("bldA_parapet_cap_W", CX - (PW / 2 - T / 2), CY, 18.92, 19.0, T + 0.12, PD - 2 * T, MAT_CONC, bevel=0.02)
    box("bldA_parapet_cap_E", CX + (PW / 2 - T / 2), CY, 18.92, 19.0, T + 0.12, PD - 2 * T, MAT_CONC, bevel=0.02)

    # ---- 屋顶设备盒 (沿用旧件 v2: 高出女儿墙 + 百叶) ----
    def roof_equip(prefix, ex, ey, bw, bd, ztop, louvre_side):
        box(prefix, ex, ey, 18.35, ztop, bw, bd, MAT_METAL, bevel=0.04)
        box(prefix + "_lid", ex, ey, ztop, ztop + 0.12, bw + 0.2, bd + 0.2,
            MAT_ROOF, bevel=0.02)
        for k, zl in enumerate((ztop - 0.95, ztop - 0.6, ztop - 0.25)):
            if louvre_side == "S":
                box("%s_louvre_%d" % (prefix, k), ex, ey - bd / 2 - 0.02,
                    zl - 0.06, zl + 0.06, bw - 0.5, 0.05, MAT_GRILLE, bevel=0.0)
            else:
                box("%s_louvre_%d" % (prefix, k), ex, ey + bd / 2 + 0.02,
                    zl - 0.06, zl + 0.06, bw - 0.5, 0.05, MAT_GRILLE, bevel=0.0)

    roof_equip("bldA_roof_equip_1", -68.0, 26.5, 2.4, 1.8, 19.9, "S")
    roof_equip("bldA_roof_equip_2", -44.0, 33.5, 2.0, 1.6, 19.75, "N")

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

print("DONE ov-bldA")
