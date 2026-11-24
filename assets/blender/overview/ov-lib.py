# ov-lib v3: 图书馆楼体换装 (R2-T21a, 2026-11-24)
# 24(x) x 16(y) x 22(z) m, 6 floors, Blender centre (24, -58, 0)
# 网上模型:
#   楼体: Grab3D 办公楼 (CC0 1.0),
#     assets/external/buildings/grab3d/office-building-grab3d.glb
#     (与 A/B 栋同款; 实测见 ov-bldA.py 头注: body + facade + shell
#     三件合起来才是整栋楼, ground_slab 删除)
#   入口柱廊: Grab3D 博物馆 (CC0 1.0),
#     assets/external/buildings/grab3d/museum-grab3d.glb
#     (实测: body 25.35x20.53x14.95 粉色坡顶; details 24.88x24.8x8.8
#     含柱廊/门/窗/横幅; temple_emblem 3.03x0.08x2.75 庙宇纹章;
#     正面为 -y 侧)
# 楼体换装: 三件在 z=21.75 处横切 (bisect, 保住 F1-F6 六层, 去掉 F7),
#   再整体缩至 24x16x21.0 (x 约 x0.74, y 约 x0.84, z 约 x0.97)。
#   窗高向基本不压 (F1 5.25m 高入口层, 其余 2.75-3.5m, 约合 SPEC 3.0m
#   净高 + 楼板; F1 偏高是模型入口层的特征, 已注明)。
#   任务单的 office 单件缩放 x0.82/x0.85/x0.86 是另一算法 (单件各缩到
#   目标盒), 会把三件压进同一个盒子造成共面, 不采用。
# 配色: 楼体保留模型自带白框 + 蓝玻璃幕墙 (即 SPEC 玻璃 #9FC3D8 系);
#   SPEC §5 的浅橙墙面由幕墙玻璃色承接, 旧件三道红褐饰带与竖向壁柱
#   不再复刻 (会压在玻璃幕墙上, 冲突); 新增件按 SPEC: 屋顶深灰
#   #424A52、女儿墙混凝土、檐口浅色。柱廊保留博物馆自带石材/白饰
#   PBR (米白 + 浅灰石), 与幕墙形成入口重点。
# 柱廊做法 (只取博物馆的正立面, 不取整栋):
#   - details: 保留面心 y<-7 的面 (3,652 面: 台阶 + 基座 + 柱 + 门窗
#     + 横幅, x ±12.44, y -13.70..-7.01, z 0-8.80, 局部坐标)
#   - body: 保留面心 y 在 (-9.5,-8.5) 且 z 在 (2,10) 的面 (554 面:
#     前基座 + 檐部 + 壁柱条, z 2-4 与 8-10 两带)
#   - temple_emblem: 整件保留, 下移使底边落在檐部顶 (~z 8.77)
#   三者 X 缩 0.65 (柱廊宽 16.2m, 居中), Y/Z 不缩, 平移至南立面
#   (墙面 y=-66, 柱廊墙面贴至 -66.2, 台阶向南伸至约 -70.8; 南侧为
#   开阔草坪, 环南路在 y=-76, 不冲突)。
# 层高 (沿用旧件外包络): 楼体顶 21.0, 屋顶板 21.0-21.3, 女儿墙 21.3-21.95。
# 正门: 柱廊即正门 (南立面中部); 不另加南门。
# 屋顶设备: 沿用旧件两盒 + 通风管 (高出女儿墙)。
# 注意 (留给终轮整合): ov-windows-roofs 只有 C 栋的窗带与屋顶细部与
#   本件相关? 不, ov-windows-roofs 只做 A/B/C, 图书馆不在其中; 本件
#   自带窗 (幕墙) 与屋顶, 无冲突。
# 不做烘焙: 模型自带真实 PBR 贴图 (2048 atlas, 本件降采样至 1024);
#   新增小件走 _pbr_apply hook (屋顶/混凝土/檐口) 或纯色。
# 本次不渲染 (用户新规: 渲染全部走 GitHub Actions):
#   只做 建模 -> 存 .blend -> 导出 .glb -> 回读校验, 打印 DONE ov-lib。

import bpy
import bmesh
import os
from mathutils import Vector, Matrix

PIECE = "ov-lib"
BASE = os.path.expanduser("~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
PY_DIR = os.path.join(BASE, "assets/blender/overview")
EXT_DIR = os.path.join(BASE, "assets/external/buildings/grab3d")
OFFICE_GLB = os.path.join(EXT_DIR, "office-building-grab3d.glb")
MUSEUM_GLB = os.path.join(EXT_DIR, "museum-grab3d.glb")
BLEND_PATH = os.path.join(PY_DIR, "ov-lib.blend")
GLB_PATH = os.path.join(BASE, "assets/models/ov-lib.glb")

CX, CY = 24.0, -58.0   # building centre (Blender x, y)
W, D = 24.0, 16.0      # footprint x, y
BODY_TOP = 21.0        # 楼体顶 (屋顶板底)
CUT_Z = 21.75          # 横切高度: 保住 F1-F6, 去掉 F7
WALL_Y = -66.0         # 南立面 y
PORTICO_X_SCALE = 0.65
PORTICO_WALL_Y = -66.2  # 柱廊墙面贴合 y (微出墙 0.2, 防共面)


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


# PBR_MAP["ov-lib"]: 屋顶 / 混凝土 / 檐口 (墙面/玻璃/柱廊用模型自带 PBR)
MAT_ROOF = pbr_ready_mat("Lib_Roof_DarkGrey_424A52_tex", "#424A52", 0.92)
MAT_CONC = pbr_ready_mat("Lib_Concrete_B9B3A8_tex", "#B9B3A8", 0.95)
MAT_BAND = pbr_ready_mat("Lib_Cornice_D8D2C4_tex", "#D8D2C4", 0.9)
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


def _bake_transform(objs):
    """把导入对象的 object transform 烘进 mesh 并清零 (GLB 导入常带 loc
    偏移; 不烘的话 _vbox(世界) 与 data.transform(局部) 口径不一致)。"""
    for o in objs:
        if o.data.users > 1:
            o.data = o.data.copy()
        o.data.transform(o.matrix_world)
        o.parent = None
        o.matrix_world = Matrix.Identity(4)
        o.data.update()


def _downscale_images(tag):
    for im in list(bpy.data.images):
        if im.name in ("Render Result", "Viewer Node"):
            continue
        if max(im.size) > 1024:
            print("%s: downscale image %s %s" % (tag, im.name, im.size[:]))
            im.scale(1024, 1024)


def _keep_faces_by_center(ob, keep_fn, tag):
    """只保留面心满足 keep_fn 的面 (其余删除 + 清理孤立顶点)。"""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    kill = [f for f in bm.faces if not keep_fn(f.calc_center_median())]
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    loose = [v for v in bm.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context="VERTS")
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    print("%s: kept %d faces on %s" % (tag, len(ob.data.polygons), ob.name))


def build():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    assert os.path.exists(OFFICE_GLB), "missing source GLB: %s" % OFFICE_GLB
    assert os.path.exists(MUSEUM_GLB), "missing source GLB: %s" % MUSEUM_GLB

    # ---- 1. 办公楼楼体: 删基座, 横切 F7, 整体缩至 24x16x21.0 ----
    bpy.ops.import_scene.gltf(filepath=OFFICE_GLB)
    for o in list(bpy.context.scene.objects):
        if o.type != "MESH":
            bpy.data.objects.remove(o, do_unlink=True)
    keep = []
    for o in list(bpy.context.scene.objects):
        if o.type != "MESH":
            continue
        if "ground_slab" in o.name:
            print("lib: removing", o.name)
            bpy.data.objects.remove(o, do_unlink=True)
        else:
            keep.append(o)
            print("lib: keeping", o.name)
    assert len(keep) == 3, "expected body+facade+shell, got %d" % len(keep)
    _bake_transform(keep)
    _downscale_images("lib-office")
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
    x0, x1, y0, y1, z0, z1 = _vbox(keep)
    print("lib cut union bbox x[%.2f,%.2f] y[%.2f,%.2f] z[%.2f,%.2f]" % (
        x0, x1, y0, y1, z0, z1))
    sx = W / (x1 - x0)
    sy = D / (y1 - y0)
    sz = BODY_TOP / (z1 - z0)
    print("lib scale x%.3f y%.3f z%.3f" % (sx, sy, sz))
    for o in keep:
        m = Matrix.Translation((CX, CY, 0.0)) @ Matrix.Diagonal((sx, sy, sz, 1.0)) \
            @ Matrix.Translation((-(x0 + x1) / 2.0, -(y0 + y1) / 2.0, -z0))
        o.data.transform(m)
        o.data.update()
    x0, x1, y0, y1, z0, z1 = _vbox(keep)
    print("lib final bbox x[%.2f,%.2f] y[%.2f,%.2f] z[%.2f,%.2f]" % (
        x0, x1, y0, y1, z0, z1))
    assert abs((x1 - x0) - W) < 0.05
    assert abs((y1 - y0) - D) < 0.05
    assert abs((z1 - z0) - BODY_TOP) < 0.05
    assert abs((x0 + x1) / 2.0 - CX) < 0.05
    assert abs((y0 + y1) / 2.0 - CY) < 0.05

    building = list(keep)

    # ---- 2. 博物馆柱廊: 只取正立面, X 缩 0.65, 贴南立面 ----
    _before_museum = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=MUSEUM_GLB)
    _new_objs = [o for o in bpy.context.scene.objects if o not in _before_museum]
    _new_mesh = [o for o in _new_objs if o.type == "MESH"]
    for o in _new_objs:
        if o.type != "MESH":
            bpy.data.objects.remove(o, do_unlink=True)
    mus = {}
    for o in _new_mesh:
        if "body" in o.name:
            mus["body"] = o
        elif "details" in o.name:
            mus["details"] = o
        elif "emblem" in o.name:
            mus["emblem"] = o
        else:
            print("lib: removing unexpected museum object", o.name)
            bpy.data.objects.remove(o, do_unlink=True)
    assert set(mus) == {"body", "details", "emblem"}, "museum parts: %s" % list(mus)
    # 注意顺序: 先按局部坐标选面 (与实测一致), 再烘 transform;
    # 烘后 y 全体 +1.3, 选面判据会失效 (body 前面烘后 y≈-7.78)。
    _keep_faces_by_center(mus["details"],
                          lambda c: c.y < -7.0, "lib-portico")
    _keep_faces_by_center(mus["body"],
                          lambda c: -9.5 < c.y < -8.5 and 2.0 < c.z < 10.0,
                          "lib-portico")
    _bake_transform(list(mus.values()))
    _downscale_images("lib-museum")
    # 柱廊墙面 (body 前基座/檐部面) 的烘后 y: 取 body 前向面的 y 中位
    # 实测烘后 body 前面 y ≈ -7.78; 以此为基准贴墙。
    # 柱廊变换: X x0.65, Y/Z x1.0; 墙面基准 y=-7.78 -> PORTICO_WALL_Y;
    # x 中心 0 -> CX; emblem 另下移 2.3 (底边落檐部顶 ~8.77)。
    REF_WALL_Y = -7.78
    ty = PORTICO_WALL_Y - REF_WALL_Y
    m_portico = Matrix.Translation((CX, ty, 0.0)) \
        @ Matrix.Diagonal((PORTICO_X_SCALE, 1.0, 1.0, 1.0))
    for key in ("details", "body"):
        o = mus[key]
        o.data.transform(m_portico)
        o.data.update()
        o.name = "lib_portico_" + key
        building.append(o)
    m_emblem = Matrix.Translation((CX, ty, -2.3)) \
        @ Matrix.Diagonal((PORTICO_X_SCALE, 1.0, 1.0, 1.0))
    mus["emblem"].data.transform(m_emblem)
    mus["emblem"].data.update()
    mus["emblem"].name = "lib_portico_emblem"
    building.append(mus["emblem"])
    x0, x1, y0, y1, z0, z1 = _vbox(building[-3:])
    print("lib portico bbox x[%.2f,%.2f] y[%.2f,%.2f] z[%.2f,%.2f]" % (
        x0, x1, y0, y1, z0, z1))

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

    def cyl(name, cx, cy, z0_, z1_, r, mat, bevel=0.0):
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=r, depth=z1_ - z0_,
                                            location=(cx, cy, (z0_ + z1_) / 2.0))
        o = bpy.context.active_object
        o.name = name
        o.data.materials.append(mat)
        building.append(o)
        return o

    # ---- 勒脚 (0-0.5) ----
    box("lib_plinth", CX, CY, 0.0, 0.5, W + 0.6, D + 0.6, MAT_CONC, bevel=0.04)
    box("lib_plinth_cap", CX, CY, 0.5, 0.68, W + 0.7, D + 0.7, MAT_BAND, bevel=0.03)
    # ---- 屋顶板 21.0-21.3 (封横切口) + 女儿墙 21.3-21.95 ----
    box("lib_roof_slab", CX, CY, 21.0, 21.3, W, D, MAT_ROOF, bevel=0.03)
    PW, PD, T = W - 0.6, D - 0.6, 0.30
    box("lib_parapet_S", CX, CY - (PD / 2 - T / 2), 21.3, 21.87, PW, T, MAT_CONC, bevel=0.02)
    box("lib_parapet_N", CX, CY + (PD / 2 - T / 2), 21.3, 21.87, PW, T, MAT_CONC, bevel=0.02)
    box("lib_parapet_W", CX - (PW / 2 - T / 2), CY, 21.3, 21.87, T, PD - 2 * T, MAT_CONC, bevel=0.02)
    box("lib_parapet_E", CX + (PW / 2 - T / 2), CY, 21.3, 21.87, T, PD - 2 * T, MAT_CONC, bevel=0.02)
    box("lib_parapet_cap_S", CX, CY - (PD / 2 - T / 2), 21.87, 21.95, PW, T + 0.12, MAT_CONC, bevel=0.02)
    box("lib_parapet_cap_N", CX, CY + (PD / 2 - T / 2), 21.87, 21.95, PW, T + 0.12, MAT_CONC, bevel=0.02)
    box("lib_parapet_cap_W", CX - (PW / 2 - T / 2), CY, 21.87, 21.95, T + 0.12, PD - 2 * T, MAT_CONC, bevel=0.02)
    box("lib_parapet_cap_E", CX + (PW / 2 - T / 2), CY, 21.87, 21.95, T + 0.12, PD - 2 * T, MAT_CONC, bevel=0.02)

    # ---- 屋顶设备 (沿用旧件位置: 两盒 + 通风管) ----
    def roof_equip(prefix, ex, ey, bw, bd, ztop):
        box(prefix, ex, ey, 21.3, ztop, bw, bd, MAT_METAL, bevel=0.04)
        box(prefix + "_lid", ex, ey, ztop, ztop + 0.12, bw + 0.2, bd + 0.2,
            MAT_ROOF, bevel=0.02)
        for k, zl in enumerate((ztop - 0.95, ztop - 0.6, ztop - 0.25)):
            box("%s_louvre_%d" % (prefix, k), ex, ey - bd / 2 - 0.02,
                zl - 0.06, zl + 0.06, bw - 0.5, 0.05, MAT_GRILLE, bevel=0.0)

    roof_equip("lib_roof_equip_1", CX - 6.0, CY - 2.0, 2.2, 1.6, 22.75)
    roof_equip("lib_roof_equip_2", CX + 6.0, CY + 3.0, 2.0, 1.6, 22.6)
    cyl("lib_roof_vent", CX + 2.0, CY - 4.0, 21.3, 22.4, 0.28, MAT_METAL)
    cyl("lib_roof_vent_cap", CX + 2.0, CY - 4.0, 22.4, 22.55, 0.38, MAT_ROOF)

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

print("DONE ov-lib")
