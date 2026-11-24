# _steal.py — 网上模型拆件共用帮手 (R2-T21b, 2026-11-25)
# 用法: 各 ov-*.py 用 exec(compile(open(...).read(), ...)) 载入本文件
# (与 _pbr_apply.py 同款做法), 再调 import_crop / place / dup_place。
# 只做三件事: (1) 导入源 GLB 并按世界坐标包围盒裁出指定部件;
# (2) 按源材质名重映射到本件材质; (3) 按目标包围盒做仿射放置
# (逐轴缩放 + 平移, 随后 transform_apply 烘进 mesh)。
# 不改源文件, 不碰本件量体; 裁切只删面, 不改剩余面的顶点/UV/材质。
import re

import bpy
import bmesh
from mathutils import Vector, Matrix


def _base_name(n):
    return re.sub(r"\.\d+$", "", n)


def bbox_world(obj):
    """世界坐标包围盒。直接读 mesh 顶点算, 不用 obj.bound_box——bmesh 改完
    mesh 后 bound_box 还是旧值 (stale), 会导致 place() 按错尺寸缩放
    (R2-T21b: gym 雨棚因此只剩 4.45m 宽)。"""
    mw = obj.matrix_world
    pts = [mw @ v.co for v in obj.data.vertices]
    xs = [p.x for p in pts]
    ys = [p.y for p in pts]
    zs = [p.z for p in pts]
    return (Vector((min(xs), min(ys), min(zs))),
            Vector((max(xs), max(ys), max(zs))))


def affine_for(smin, smax, tmin, tmax):
    """仿射矩阵: 源包围盒 -> 目标包围盒 (逐轴缩放 + 平移, 绕各自包围盒中心)。"""
    smin, smax = Vector(smin), Vector(smax)
    tmin, tmax = Vector(tmin), Vector(tmax)
    sc = Vector(((tmax[i] - tmin[i]) / (smax[i] - smin[i])) for i in range(3))
    smid = (smin + smax) / 2.0
    tmid = (tmin + tmax) / 2.0
    S = Matrix(((sc.x, 0.0, 0.0, 0.0),
                (0.0, sc.y, 0.0, 0.0),
                (0.0, 0.0, sc.z, 0.0),
                (0.0, 0.0, 0.0, 1.0)))
    return Matrix.Translation(tmid) @ S @ Matrix.Translation(-smid)


def apply_matrix(obj, mat):
    """把矩阵作用到对象并烘进 mesh (location/rotation/scale 全部 apply)。"""
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.matrix_world = mat @ obj.matrix_world
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.select_all(action='DESELECT')


def place(obj, tmin, tmax, name):
    """按当前世界包围盒 -> 目标包围盒放置, 改名, 返回对象。"""
    bmin, bmax = bbox_world(obj)
    apply_matrix(obj, affine_for(bmin, bmax, tmin, tmax))
    obj.name = name
    return obj


def dup_place(src, tmin, tmax, name):
    """复制 src (mesh 深拷贝) 再按目标包围盒放置, 改名, 返回新对象。"""
    new = src.copy()
    new.data = src.data.copy()
    bpy.context.collection.objects.link(new)
    bmin, bmax = bbox_world(new)
    apply_matrix(new, affine_for(bmin, bmax, tmin, tmax))
    new.name = name
    return new


def _import_meshes(glb_path, mesh_names):
    """导入 GLB, 返回 {mesh 名: 对象}; 删掉其余导入对象; 只清本次新入库
    且 users==0 的材质 (绝不碰本件已有的材质)。"""
    mats_before = set(bpy.data.materials)
    objs_before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=glb_path)
    added = [o for o in bpy.data.objects if o not in objs_before]
    found = {}
    for o in added:
        if o.type == 'MESH' and _base_name(o.name) in mesh_names:
            found[_base_name(o.name)] = o
    missing = [n for n in mesh_names if n not in found]
    assert not missing, "mesh not found in %s: %s" % (glb_path, missing)
    for o in added:
        if o not in found.values():
            bpy.data.objects.remove(o, do_unlink=True)
    for m in list(bpy.data.materials):
        if m not in mats_before and m.users == 0:
            bpy.data.materials.remove(m)
    return found


def import_crop(glb_path, mesh_name, box_min, box_max, remap=None):
    """导入 GLB 的 mesh_name, 删掉包围盒 (世界坐标) 之外的面, 按 remap
    {源材质基名: 本件材质} 重映射材质, 返回裁好的对象 (未放置)。"""
    obj = _import_meshes(glb_path, [mesh_name])[mesh_name]
    me = obj.data
    mw = obj.matrix_world
    bmin = Vector(box_min)
    bmax = Vector(box_max)
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    # 只留全部顶点都在盒内的面: 按面中心判会把横跨整排的大三角 (如雨棚整块
    # 膜面) 连同盒外顶点一起留下来, 盒子就切不干净。
    kill = []
    for f in bm.faces:
        ok = True
        for v in f.verts:
            c = mw @ v.co
            if not (bmin.x <= c.x <= bmax.x and
                    bmin.y <= c.y <= bmax.y and
                    bmin.z <= c.z <= bmax.z):
                ok = False
                break
        if not ok:
            kill.append(f)
    bmesh.ops.delete(bm, geom=kill, context='FACES')
    orphans = [v for v in bm.verts if not v.link_faces]
    if orphans:
        bmesh.ops.delete(bm, geom=orphans, context='VERTS')
    bm.to_mesh(me)
    bm.free()
    if remap:
        for slot in obj.material_slots:
            m = slot.material
            if m is not None and _base_name(m.name) in remap:
                slot.material = remap[_base_name(m.name)]
    print("steal crop: %s from %s -> %d faces, bbox %s..%s"
          % (mesh_name, glb_path, len(me.polygons),
             tuple(round(v, 2) for v in bbox_world(obj)[0]),
             tuple(round(v, 2) for v in bbox_world(obj)[1])))
    return obj


def import_whole(glb_path, mesh_name):
    """导入 GLB 的 mesh_name, 不裁切, 返回对象 (未放置)。"""
    return _import_meshes(glb_path, [mesh_name])[mesh_name]
