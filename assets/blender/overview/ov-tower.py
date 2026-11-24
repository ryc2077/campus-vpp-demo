# ov-tower v3: 创造力中心楼体换装 (R2-T21a, 2026-11-24)
# 14(x) x 14(y) x 32(z) m, 8 floors, Blender centre (10, 54, 0)
# 网上模型: vinish.dev 彩色小镇钟楼 (CC BY 4.0, 署名 vinish.dev),
#   assets/external/buildings/vinish/clock-tower.glb
# 实测核对 (Blender 4.2.0, 见 BLENDER_MODELS.md §20 / SOURCES.md §12):
#   R2-T10b 表内 "13.2x13.2x32.7" 是整文件包围盒 (含 13.2m 广场铺装/花坛
#   与 13m 高的钟楼/尖顶/风向标); 可用塔身实测只有 4.34x4.34x19.08m
#   (砖砌塔身, z 0.12-19.2; 钟面 z 16.1-18.4; 钟楼/铜绿尖顶 z 19.2-32.7)。
#   因此任务单上的 x1.06/x1.06/x0.98 与 "去钟面/尖顶" 合起来得不到 SPEC
#   尺寸 (只剩 19m 高、4.6m 宽的针塔)。按任务硬性规则 "改模型不改尺寸,
#   楼体尺寸按 SPEC §4 实测", 本件: 去广场/钟面/尖顶/风向标/门廊后,
#   塔身按实测包围盒缩放至 14x14x32 (x/y 约 x3.23, z 约 x1.68)。
#   拉伸的贴图变形由 _pbr_apply hook 的世界尺寸 UV 重投影抵消
#   (墙面改 SPEC 米白 PBR 抹灰, 2m 一贴); 几何拉伸只剩石材线脚比例变化,
#   读作转角壁柱与层间带, 总览距离可接受。钟面不挖洞: 表盘面改墙色盲盘
#   (砖墙在表盘后是完整的, 但不挖洞更稳; 盲盘无指针无数字, 钟面已去除)。
#   尖顶/钟楼/风向标/广场花坛/门廊全部删除。
# 位置/尺寸/朝向按 SPEC §4, 一点不动: 中心 (10, 54), 占地 14x14, 高 32m。
# 层高 (沿用 v2 已确立外包络; F1 净高 3.5m + 0.5m 勒脚 = 4.0m,
#   F2-F8 净高 3.0m + 楼板约 0.9m? 实际 F2-F8 各 3.9m 至 31.8):
#   plinth 0-0.5, F1 0.5-4.5, F2-F8 3.9m each to 31.8, roof slab 31.8-32.0,
#   parapet 32.0-32.65. 窗带/女儿墙/正门/空调/屋顶设备照 v2 做法保留。
# 不做烘焙: 塔身材质走 _pbr_apply hook (真实 PBR 抹灰/屋顶/混凝土);
# 其余小件用纯色 Principled (glTF 可直接导出, 无需烘焙)。
# 本次不渲染 (用户新规: 渲染全部走 GitHub Actions):
#   只做 建模 -> 存 .blend -> 导出 .glb -> 回读校验, 打印 DONE ov-tower。

import bpy
import bmesh
import os
from mathutils import Vector, Matrix

PIECE = "ov-tower"
BASE = os.path.expanduser("~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
PY_DIR = os.path.join(BASE, "assets/blender/overview")
EXT_DIR = os.path.join(BASE, "assets/external/buildings/vinish")
SRC_GLB = os.path.join(EXT_DIR, "clock-tower.glb")
BLEND_PATH = os.path.join(PY_DIR, "ov-tower.blend")
GLB_PATH = os.path.join(BASE, "assets/models/ov-tower.glb")

CX, CY = 10.0, 54.0   # building centre (Blender x, y)
W, D = 14.0, 14.0     # footprint x, y
H = 32.0              # height to roof slab top


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
    """Principled + BaseColor/Roughness/Normal image nodes (placeholders).
    _pbr_apply._swap_material 要求三张图链接齐全, 它会把占位图换成真实
    PBR 贴图并按世界尺寸重投影 UV。"""
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


def glass_mat():
    """窗玻璃: 淡蓝灰 #9FC3D8, 透明度 0.65 + 低粗糙度反光 (不烘焙, 不进 PBR hook)。"""
    m = _new_mat("Glass_Window_9FC3D8", "#9FC3D8", 0.12, 0.0)
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Alpha"].default_value = 0.65
    bsdf.inputs["Specular IOR Level"].default_value = 1.0
    try:
        m.blend_method = "BLEND"
    except Exception:
        pass
    return m


# PBR_MAP["ov-tower"] (见 _pbr_apply.py): 墙 / 屋顶 / 混凝土 / 檐口
MAT_WALL = pbr_ready_mat("Wall_Cream_F7F5EF_tex", "#F3E9D2", 0.85)
MAT_TRIM = pbr_ready_mat("Cornice_D8D2C4_tex", "#D8D2C4", 0.9)
MAT_ROOF = pbr_ready_mat("Roof_DarkGrey_424A52_tex", "#424A52", 0.92)
MAT_CONC = pbr_ready_mat("Concrete_B9B3A8_tex", "#B9B3A8", 0.95)
MAT_BAND = MAT_TRIM
MAT_SEAM = _new_mat("FloorSeam_B7A988", "#B7A988", 0.9)
MAT_METAL = _new_mat("MetalGrey_tex", "#C0C5C9", 0.55, 0.3)
MAT_AC_BODY = _new_mat("AC_Body_D5D9DC", "#D5D9DC", 0.5, 0.25)
MAT_GRILLE = _new_mat("AC_Grille_3A4046_tex", "#3A4046", 0.7, 0.1)
MAT_DOOR = _new_mat("Door_Dark_3A4046", "#3A4046", 0.6, 0.2)
MAT_DOOR_GLASS = _new_mat("Door_Glass_9FC3D8", "#9FC3D8", 0.25, 0.1)
MAT_GLASS = glass_mat()
MAT_WIN_FRAME = _new_mat("WinFrame_E9E6DD_tex", "#E9E6DD", 0.6)
MAT_WIN_MULLION = _new_mat("WinMullion_8A8F94_tex", "#8A8F94", 0.4, 0.35)
MAT_WIN_SILL = _new_mat("WinSill_CFC9BC_tex", "#CFC9BC", 0.9)


def build():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    assert os.path.exists(SRC_GLB), "missing source GLB: %s" % SRC_GLB
    bpy.ops.import_scene.gltf(filepath=SRC_GLB)
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    assert len(meshes) == 1, "clock-tower GLB should have 1 mesh, got %d" % len(meshes)
    shaft = meshes[0]
    shaft.name = "tower_body_src"
    me = shaft.data

    # ---- 删件 (bmesh, 按材质 + 位置) ----
    # 删: 广场/花坛/长椅/路灯/铺装 (Flower_*/Hedge/Soil/Paving/Wood_Bench/
    #   Lamp_Glass/Concrete), 尖顶 (Copper_Green), 风向标/金饰 (Gold z>19.2,
    #   Bronze, Iron), 源木门 (Door_Wood, 另做标准门)。
    # 留: 砖 (Brick_Red) -> 墙面; 石灰石/石材线脚 (Limestone/Stone_Trim,
    #   仅塔身内) -> 浅色线脚; 玻璃小拱窗与钟面改墙色 (不挖洞, 盲拱/盲盘);
    #   金饰仅留 z<=19.2 的钟面边框部分 (改墙色)。
    DELETE_MATS = {"Flower_Red", "Flower_Pink", "Flower_White", "Flower_Purple",
                   "Flower_Orange", "Flower_Blue", "Hedge", "Soil", "Paving",
                   "Wood_Bench", "Lamp_Glass", "Concrete", "Copper_Green",
                   "Bronze", "Iron", "Door_Wood"}
    WALL_MATS = {"Brick_Red", "Glass", "Clock_Face"}
    TRIM_MATS = {"Limestone", "Stone_Trim"}
    SHAFT_HALF = 2.6   # 塔身半宽 2.17 + 余量; 超出即广场/门廊
    TOP_Z = 19.2       # 砖砌塔身顶; 之上是钟楼/尖顶, 全删
    bm = bmesh.new()
    bm.from_mesh(me)
    # 先记每个面的旧材质名 (bmesh 面无材质名, 用原 mesh 的 polygon 对应:
    # bmesh 与原 mesh 面顺序一致, 用索引对齐)
    old_names = []
    for poly in me.polygons:
        old_names.append(me.materials[poly.material_index].name
                         if poly.material_index < len(me.materials) else "")
    kill = []
    for f in bm.faces:
        nm = old_names[f.index]
        c = f.calc_center_median()
        if nm in DELETE_MATS:
            kill.append(f)
        elif nm == "Gold":
            if c.z > TOP_Z:
                kill.append(f)
            # z<=19.2 的金饰 (钟面边框) 留下改墙色
        elif nm in WALL_MATS or nm in TRIM_MATS:
            if abs(c.x) > SHAFT_HALF or abs(c.y) > SHAFT_HALF or c.z > TOP_Z:
                kill.append(f)
        else:
            kill.append(f)
    print("tower: deleting %d / %d faces" % (len(kill), len(bm.faces)))
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    bm.to_mesh(me)
    bm.free()
    print("tower: kept faces %d verts %d" % (len(me.polygons), len(me.vertices)))
    assert len(me.polygons) > 1000, "tower shaft over-deleted"

    # ---- 材质重指派: 砖/玻璃/钟面/金饰 -> 墙面; 石灰石/线脚 -> 浅色线脚 ----
    # 删除后面顺序已变, 以当前 slot 名为准 (bmesh.to_mesh 保留 material_index)。
    for poly in me.polygons:
        cur = me.materials[poly.material_index].name \
            if poly.material_index < len(me.materials) else ""
        if cur in TRIM_MATS:
            poly.material_index = 1
        else:
            poly.material_index = 0
    me.materials.clear()
    me.materials.append(MAT_WALL)
    me.materials.append(MAT_TRIM)

    # ---- 实测包围盒 -> 缩放至 SPEC 14x14x32, 落到 (CX, CY, 0) ----
    # 注意: bmesh 改 mesh 后 Object.bound_box 是旧值, 必须用顶点实算。
    def _vbox(m):
        xs_ = [v.co.x for v in m.vertices]
        ys_ = [v.co.y for v in m.vertices]
        zs_ = [v.co.z for v in m.vertices]
        return min(xs_), max(xs_), min(ys_), max(ys_), min(zs_), max(zs_)

    x0, x1, y0, y1, z0, z1 = _vbox(me)
    print("tower src kept bbox x[%.2f,%.2f] y[%.2f,%.2f] z[%.2f,%.2f]" % (
        x0, x1, y0, y1, z0, z1))
    sx = W / (x1 - x0)
    sy = D / (y1 - y0)
    sz = H / (z1 - z0)
    print("tower scale x%.3f y%.3f z%.3f" % (sx, sy, sz))
    mx = Matrix.Translation((CX, CY, 0.0)) @ Matrix.Diagonal((sx, sy, sz, 1.0)) \
        @ Matrix.Translation((-(x0 + x1) / 2.0, -(y0 + y1) / 2.0, -z0))
    me.transform(mx)
    me.update()
    x0, x1, y0, y1, z0, z1 = _vbox(me)
    print("tower final bbox x[%.2f,%.2f] y[%.2f,%.2f] z[%.2f,%.2f]" % (
        x0, x1, y0, y1, z0, z1))
    assert abs((x1 - x0) - W) < 0.05
    assert abs((y1 - y0) - D) < 0.05
    assert abs((z1 - z0) - H) < 0.05

    building = [shaft]

    def box(name, cx, cy, z0, z1, sx_, sy_, mat, bevel=0.05):
        bpy.ops.mesh.primitive_cube_add(location=(cx, cy, (z0 + z1) / 2.0))
        o = bpy.context.active_object
        o.name = name
        o.dimensions = (sx_, sy_, z1 - z0)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        if bevel and min(sx_, sy_, z1 - z0) > 2 * bevel + 0.02:
            mod = o.modifiers.new("EdgeSoft", "BEVEL")
            mod.width = bevel
            mod.segments = 2
            mod.limit_method = "ANGLE"
        o.data.materials.append(mat)
        building.append(o)
        return o

    # ---- 勒脚 (0-0.5) ----
    box("tower_plinth", CX, CY, 0.0, 0.5, 14.4, 14.4, MAT_CONC, bevel=0.04)
    box("tower_plinth_cap", CX, CY, 0.5, 0.68, 14.5, 14.5, MAT_BAND, bevel=0.03)

    # ---- 楼层分缝: 每层分界处檐口线脚 + 线脚下暗色缝线 (v2 做法, 无收分) ----
    for z in (4.5, 8.4, 12.3, 16.2, 20.1, 24.0, 27.9):
        box("tower_cornice_z%s" % z, CX, CY, z - 0.14, z + 0.14, 14.3, 14.3,
            MAT_BAND, bevel=0.03)
        box("tower_seam_z%s" % z, CX, CY, z - 0.24, z - 0.18, 14.06, 14.06,
            MAT_SEAM, bevel=0.0)
    box("tower_belt_16p2", CX, CY, 16.08, 16.32, 14.0, 14.0, MAT_BAND, bevel=0.03)
    box("tower_cornice_top", CX, CY, 31.71, 31.89, 13.9, 13.9, MAT_CONC, bevel=0.03)

    # ---- 屋顶板 31.8-32.0 + 女儿墙 32.0-32.65 ----
    box("tower_roofslab", CX, CY, 31.8, 31.98, 13.7, 13.7, MAT_ROOF, bevel=0.03)
    PW, PD, T = 13.7, 13.7, 0.30
    box("tower_parapet_S", CX, CY - (PD / 2 - T / 2), 32.0, 32.57, PW, T, MAT_CONC, bevel=0.02)
    box("tower_parapet_N", CX, CY + (PD / 2 - T / 2), 32.0, 32.57, PW, T, MAT_CONC, bevel=0.02)
    box("tower_parapet_W", CX - (PW / 2 - T / 2), CY, 32.0, 32.57, T, PD - 2 * T, MAT_CONC, bevel=0.02)
    box("tower_parapet_E", CX + (PW / 2 - T / 2), CY, 32.0, 32.57, T, PD - 2 * T, MAT_CONC, bevel=0.02)
    box("tower_parapet_cap_S", CX, CY - (PD / 2 - T / 2), 32.57, 32.65, PW, T + 0.12, MAT_CONC, bevel=0.02)
    box("tower_parapet_cap_N", CX, CY + (PD / 2 - T / 2), 32.57, 32.65, PW, T + 0.12, MAT_CONC, bevel=0.02)
    box("tower_parapet_cap_W", CX - (PW / 2 - T / 2), CY, 32.57, 32.65, T + 0.12, PD - 2 * T, MAT_CONC, bevel=0.02)
    box("tower_parapet_cap_E", CX + (PW / 2 - T / 2), CY, 32.57, 32.65, T + 0.12, PD - 2 * T, MAT_CONC, bevel=0.02)

    # ---- 屋顶设备小盒 ----
    box("tower_roof_eq1", CX - 3.5, CY - 2.5, 32.0, 33.0, 2.0, 1.5, MAT_METAL, bevel=0.04)
    box("tower_roof_eq1_lid", CX - 3.5, CY - 2.5, 33.0, 33.12, 2.2, 1.7, MAT_ROOF, bevel=0.02)
    box("tower_roof_eq1_louvre", CX - 3.5, CY - 2.5 - 0.78, 32.35, 32.65, 1.5, 0.05, MAT_GRILLE, bevel=0.0)
    box("tower_roof_eq2", CX + 3.5, CY + 2.5, 32.0, 32.7, 1.6, 1.2, MAT_METAL, bevel=0.04)
    box("tower_roof_eq2_lid", CX + 3.5, CY + 2.5, 32.7, 32.82, 1.8, 1.4, MAT_ROOF, bevel=0.02)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.35, depth=0.8,
                                        location=(CX + 1.0, CY - 3.5, 32.4))
    vent = bpy.context.active_object
    vent.name = "tower_roof_vent"
    vent.data.materials.append(MAT_METAL)
    building.append(vent)

    # ---- 窗带 (v2 做法: 每层横向窗带 + 竖分格条, 嵌进墙面) ----
    # 塔身无收分, 半宽恒 7.0; 每面两段 (中心留 2m 墩, 两侧各留 1.5m),
    # 一层南面正中是正门, 不布窗带。
    BAND_H = 1.4
    n_win = 0

    def win_segment(face, fi, c, w, z0, hw):
        nonlocal n_win
        zb = z0 + 2.05
        zt = zb + BAND_H
        base = "tower_win_F%d_%s_%.2f" % (fi + 1, face, c)
        s = {"S": -1, "N": 1, "W": -1, "E": 1}[face]
        if face in ("S", "N"):
            wall = CY + s * hw
            fy, gy, my, sy = wall + s * 0.02, wall - s * 0.03, wall + s * 0.01, wall + s * 0.06

            def wb(nm, cc, yy, za, zb2, sx_, syy, mat):
                return box(nm, cc, yy, za, zb2, sx_, syy, mat, bevel=0.0)
        else:
            wall = CX + s * hw
            fx, gx, mx, sx0 = wall + s * 0.02, wall - s * 0.03, wall + s * 0.01, wall + s * 0.06

            def wb(nm, cc, yy, za, zb2, sx_, syy, mat):
                return box(nm, cc, yy, za, zb2, sx_, syy, mat, bevel=0.0)

        if face in ("S", "N"):
            wb(base + "_frameB", c, fy, zb, zb + 0.12, w, 0.10, MAT_WIN_FRAME)
            wb(base + "_frameT", c, fy, zt - 0.12, zt, w, 0.10, MAT_WIN_FRAME)
            wb(base + "_frameL", c - (w / 2 - 0.06), fy, zb + 0.12, zt - 0.12, 0.12, 0.10, MAT_WIN_FRAME)
            wb(base + "_frameR", c + (w / 2 - 0.06), fy, zb + 0.12, zt - 0.12, 0.12, 0.10, MAT_WIN_FRAME)
            wb(base + "_glass", c, gy, zb + 0.12, zt - 0.12, w - 0.24, 0.04, MAT_GLASS)
            n_mull = max(1, int(w // 1.5))
            for i in range(n_mull):
                mxp = c - w / 2 + (i + 1) * w / (n_mull + 1)
                wb(base + "_mull%d" % i, mxp, my, zb + 0.12, zt - 0.12, 0.08, 0.06, MAT_WIN_MULLION)
            wb(base + "_sill", c, sy, zb - 0.09, zb, w + 0.12, 0.20, MAT_WIN_SILL)
        else:
            wb(base + "_frameB", fx, c, zb, zb + 0.12, 0.10, w, MAT_WIN_FRAME)
            wb(base + "_frameT", fx, c, zt - 0.12, zt, 0.10, w, MAT_WIN_FRAME)
            wb(base + "_frameL", fx, c - (w / 2 - 0.06), zb + 0.12, zt - 0.12, 0.10, 0.12, MAT_WIN_FRAME)
            wb(base + "_frameR", fx, c + (w / 2 - 0.06), zb + 0.12, zt - 0.12, 0.10, 0.12, MAT_WIN_FRAME)
            wb(base + "_glass", gx, c, zb + 0.12, zt - 0.12, 0.04, w - 0.24, MAT_GLASS)
            n_mull = max(1, int(w // 1.5))
            for i in range(n_mull):
                myp = c - w / 2 + (i + 1) * w / (n_mull + 1)
                wb(base + "_mull%d" % i, mx, myp, zb + 0.12, zt - 0.12, 0.06, 0.08, MAT_WIN_MULLION)
            wb(base + "_sill", sx0, c, zb - 0.09, zb, 0.20, w + 0.12, MAT_WIN_SILL)
        n_win += 6 + n_mull

    win_z0 = [0.5] + [4.5 + i * 3.9 for i in range(7)]
    for fi in range(8):
        z0 = win_z0[fi]
        for face in ("S", "N"):
            if fi == 0 and face == "S":
                # 一层南面正中是正门 (门框至 x=±1.5): 窗带外移避开门
                win_segment(face, fi, CX - 4.75, 3.5, z0, 7.0)
                win_segment(face, fi, CX + 4.75, 3.5, z0, 7.0)
            else:
                win_segment(face, fi, CX - 3.25, 4.5, z0, 7.0)
                win_segment(face, fi, CX + 3.25, 4.5, z0, 7.0)
        for face in ("E", "W"):
            win_segment(face, fi, CY - 3.25, 4.5, z0, 7.0)
            win_segment(face, fi, CY + 3.25, 4.5, z0, 7.0)
    print("Window band objects:", n_win)

    # ---- 正门 (南面正中, 一层) + 门廊雨棚 + 台阶 ----
    door_y = CY - 7.0 - 0.02
    box("tower_door_frame", CX, door_y, 0.5, 3.6, 3.0, 0.18, MAT_DOOR, bevel=0.02)
    box("tower_door_L", CX - 0.65, door_y - 0.06, 0.5, 3.4, 1.2, 0.10, MAT_DOOR_GLASS, bevel=0.0)
    box("tower_door_R", CX + 0.65, door_y - 0.06, 0.5, 3.4, 1.2, 0.10, MAT_DOOR_GLASS, bevel=0.0)
    box("tower_door_mullion", CX, door_y - 0.06, 0.5, 3.4, 0.12, 0.12, MAT_DOOR, bevel=0.0)
    box("tower_door_lintel", CX, door_y, 3.6, 3.85, 3.4, 0.22, MAT_BAND, bevel=0.02)
    box("tower_entry_canopy", CX, CY - 8.0, 3.4, 3.65, 5.0, 2.0, MAT_CONC, bevel=0.03)
    box("tower_entry_canopy_top", CX, CY - 8.0, 3.65, 3.75, 5.2, 2.2, MAT_ROOF, bevel=0.02)
    box("tower_entry_col_L", CX - 2.1, CY - 8.9, 0.5, 3.4, 0.3, 0.3, MAT_CONC, bevel=0.02)
    box("tower_entry_col_R", CX + 2.1, CY - 8.9, 0.5, 3.4, 0.3, 0.3, MAT_CONC, bevel=0.02)
    box("tower_step_1", CX, CY - 8.3, 0.0, 0.17, 5.4, 3.2, MAT_CONC, bevel=0.02)
    box("tower_step_2", CX, CY - 8.0, 0.17, 0.34, 5.4, 2.6, MAT_CONC, bevel=0.02)
    box("tower_step_3", CX, CY - 7.7, 0.34, 0.5, 5.4, 2.0, MAT_CONC, bevel=0.02)

    # ---- 空调外机: 每层每面 2 台 (共 64 台) ----
    def ac_unit(prefix, ux, uy, zc, facing):
        if facing in ("S", "N"):
            gy = uy + (0.15 if facing == "N" else -0.15)
            box(prefix, ux, uy, zc - 0.31, zc + 0.31, 0.9, 0.28, MAT_AC_BODY, bevel=0.02)
            box(prefix + "_grille", ux, gy, zc - 0.22, zc + 0.22, 0.78, 0.03, MAT_GRILLE, bevel=0.0)
            box(prefix + "_bracket", ux, uy, zc - 0.40, zc - 0.34, 0.9, 0.10, MAT_METAL, bevel=0.0)
        else:
            gx = ux + (0.15 if facing == "E" else -0.15)
            box(prefix, ux, uy, zc - 0.31, zc + 0.31, 0.28, 0.9, MAT_AC_BODY, bevel=0.02)
            box(prefix + "_grille", gx, uy, zc - 0.22, zc + 0.22, 0.03, 0.78, MAT_GRILLE, bevel=0.0)
            box(prefix + "_bracket", ux, uy, zc - 0.40, zc - 0.34, 0.10, 0.9, MAT_METAL, bevel=0.0)

    n_ac = 0
    for fi, z0 in enumerate(win_z0):
        zc = z0 + 1.2
        hw = 7.0
        s_offs = (-2.5, 2.5) if fi == 0 else (-1.5, 1.5)
        for j, off in enumerate(s_offs):
            ac_unit("tower_ac_F%d_S%d" % (fi + 1, j), CX + off, CY - hw - 0.14, zc, "S")
            ac_unit("tower_ac_F%d_N%d" % (fi + 1, j), CX + off, CY + hw + 0.14, zc, "N")
            n_ac += 2
        for j, off in enumerate((-1.5, 1.5)):
            ac_unit("tower_ac_F%d_E%d" % (fi + 1, j), CX + hw + 0.14, CY + off, zc, "E")
            ac_unit("tower_ac_F%d_W%d" % (fi + 1, j), CX - hw - 0.14, CY + off, zc, "W")
            n_ac += 2
    print("AC outdoor units:", n_ac)

    return building


def save_and_export(building):
    os.makedirs(PY_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
    # R2-T9 PBR hook: 墙/屋顶/混凝土/檐口换真实 PBR 贴图 + 世界尺寸 UV。
    # 注意: 本件塔身墙面是 pbr_ready 材质 (三张图链接齐全), hook 可直接换。
    _pbr_hook = os.path.join(os.path.dirname(BLEND_PATH), "_pbr_apply.py")
    if os.path.exists(_pbr_hook):
        _pbr_g = {"__name__": "_pbr_apply", "__file__": _pbr_hook}
        exec(compile(open(_pbr_hook).read(), _pbr_hook, "exec"), _pbr_g)
        _pbr_g["apply_pbr"](os.path.splitext(os.path.basename(BLEND_PATH))[0])
    # 清理无用材质/贴图 (被换掉的源模型材质与占位图)
    for im in list(bpy.data.images):
        if im.users == 0 and im.name not in ("Render Result", "Viewer Node"):
            try:
                bpy.data.images.remove(im)
            except Exception as e:
                print("purge image skip:", im.name, e)
    # 贴图打包进 .blend (Actions 渲染用; hook 换入的 PBR 图只存相对路径
    # //../../external/..., 不打包会在 Actions 检出后找不到而渲成品红;
    # R2-T21a 首版漏了这步, run #99 的 ov-tower.png 全塔品红, 此处补上)
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

print("DONE ov-tower")
