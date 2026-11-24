# 教室场景拼装 classroom（SPEC.md §6 局部坐标，§8）
# 做法：把 assets/blender/classroom/ 下 6 件 .blend 里的本件对象直接 append
# 进来，不移位置；排除相机/灯光/太阳/光照探针和 cl-board 的 PREVIEW 辅助物
# （PREVIEW_Floor / PREVIEW_WallBoard 与 cl-floor-walls 重合，会 z-fight）。
# 存 assets/blender/scenes/classroom.blend，导出 assets/models/scenes/classroom.glb，
# 再用 import_scene.gltf 回读验证。末尾打印 DONE classroom。
# 运行：xvfb-run -a -s "-screen 0 1280x720x24" <blender> -b --python classroom.py
import bpy
import os
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# ROOT = assets/blender ; 工程根目录 = demo-godot/
BLEND_DIR = os.path.join(ROOT, "classroom")
OUT_BLEND = os.path.join(ROOT, "scenes", "classroom.blend")
OUT_GLB = os.path.join(os.path.dirname(os.path.dirname(ROOT)),
                       "assets", "models", "scenes", "classroom.glb")

PIECES = [
    "cl-floor-walls",
    "cl-desks",
    "cl-board",
    "cl-ac",
    "cl-lights",
    "cl-windows",
]

# ---- GLB baseColorFactor >1 补丁 (R2-T27) ----
# 与 assets/blender/classroom/cl-floor-walls.py 里的同名补丁同步：
# Blender 4.2 glTF 导出器硬 clamp baseColorFactor 到 [0, 1]，西墙补偿
# 因子 R=1.85 导不出；导出后直接改 GLB 的 JSON chunk 写回真实值。
# .blend 里本就存 1.85，补丁后 .blend 与 .glb 一致；重跑本脚本会重打。
GLB_FACTOR_PATCH = {
    "cl-floor-walls_wall_back": [1.85, 0.62, 0.45, 1.0],
}


def _patch_glb_factors(glb_path):
    import json as _json
    import struct as _struct
    with open(glb_path, "rb") as f:
        data = bytearray(f.read())
    assert data[:4] == b"glTF", "not a GLB file: %s" % glb_path
    total_len = _struct.unpack_from("<I", data, 8)[0]
    assert total_len == len(data), "GLB length mismatch: %s" % glb_path
    json_len = _struct.unpack_from("<I", data, 12)[0]
    json_start = 20
    js = _json.loads(bytes(data[json_start:json_start + json_len]))
    patched = []
    for m in js.get("materials", []):
        want = GLB_FACTOR_PATCH.get(m.get("name"))
        if want is not None:
            m.setdefault("pbrMetallicRoughness", {})["baseColorFactor"] = want
            patched.append(m["name"])
    if not patched:
        print("GLB factor patch: no matching material in", glb_path)
        return
    new_json = _json.dumps(js, separators=(",", ":")).encode("utf-8")
    pad = (-len(new_json)) % 4  # JSON chunk 须 4 字节对齐，空格补齐
    new_json += b" " * pad
    rest = bytes(data[json_start + json_len:])
    new_total = 20 + len(new_json) + len(rest)
    out = bytearray()
    out += data[:8]  # magic + version
    out += _struct.pack("<I", new_total)
    out += _struct.pack("<I", len(new_json))
    out += b"JSON"
    out += new_json
    out += rest
    assert len(out) == new_total
    with open(glb_path, "wb") as f:
        f.write(out)
    print("GLB factor patch: %s -> %s" % (patched, glb_path))

EXCLUDE_TYPES = {"CAMERA", "LIGHT", "LIGHT_PROBE"}
EXCLUDE_PREFIXES = ("PREVIEW_",)


def is_piece_object(obj):
    if obj.type in EXCLUDE_TYPES:
        return False
    if obj.name.startswith(EXCLUDE_PREFIXES):
        return False
    return True


def world_bbox(objects):
    mins = Vector((1e9, 1e9, 1e9))
    maxs = Vector((-1e9, -1e9, -1e9))
    for o in objects:
        if o.type != "MESH":
            continue
        for v in o.bound_box:
            w = o.matrix_world @ Vector(v)
            for i in range(3):
                mins[i] = min(mins[i], w[i])
                maxs[i] = max(maxs[i], w[i])
    return mins, maxs


def fmt(v):
    return "(%.3f, %.3f, %.3f)" % (v[0], v[1], v[2])


# --- 新建空场景 ---
bpy.ops.wm.read_factory_settings(use_empty=True)
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

counts = {}
for piece in PIECES:
    path = os.path.join(BLEND_DIR, piece + ".blend")
    with bpy.data.libraries.load(path, link=False) as (src, _dst):
        names = [n for n in src.objects
                 if n not in EXCLUDE_TYPES and not n.startswith(EXCLUDE_PREFIXES)]
        # libraries.load 的 src.objects 只有名字，没有 type；type 过滤靠
        # append 后按实际对象复核（见下），这里先按名字排除已知的非几何对象：
        # cl-board 的 Sun / PreviewCam、cl-windows 的 reflection probe、
        # PREVIEW_ 辅助物。
        names = [n for n in names
                 if n not in ("Sun", "PreviewCam", "cl-windows_reflection_probe")]
    bpy.ops.wm.append(filepath=path,
                      directory=os.path.join(path, "Object") + os.sep,
                      files=[{"name": n} for n in names],
                      link=False, autoselect=False)
    got = [o for o in bpy.context.scene.objects
           if o.name in names or any(o.name.startswith(n) for n in names)]
    # append 后若有重名会自动加 .001 后缀；按件前缀/名字归属统计更可靠：
    counts[piece] = len(names)
    print("APPEND %s: requested=%d file=%s" % (piece, len(names), path))

# append 后实际对象（应只有 MESH；若混入相机/灯光则报错退出）
bad = [o for o in bpy.context.scene.objects if o.type != "MESH"]
if bad:
    raise RuntimeError("non-mesh objects appended: %s"
                       % [(o.name, o.type) for o in bad])
print("TOTAL objects in scene: %d" % len(bpy.context.scene.objects))
for piece in PIECES:
    print("  %s: %d" % (piece, counts[piece]))

# --- 位置检查（只读，不改任何对象）---
bpy.context.view_layer.update()
groups = {}
for o in bpy.context.scene.objects:
    key = o.name.split("_")[0] if "_" in o.name else o.name
    # desks/board/ac 用名字前缀归组；其余按件名前缀
    groups.setdefault(o.name, o)

def by_prefix(prefix):
    return [o for o in bpy.context.scene.objects if o.name.startswith(prefix)]

checks = []
# 1. 桌椅整体范围（讲台桌前沿 x=-3.695，见 cl-board DeskFront）
desks = by_prefix("desk_") + by_prefix("chair_")
mn, mx = world_bbox(desks)
checks.append("desks+chairs bbox x[%.3f, %.3f] y[%.3f, %.3f] z[%.3f, %.3f]"
              % (mn.x, mx.x, mn.y, mx.y, mn.z, mx.z))
checks.append("desks nearest board: min_x=%.3f vs podium front x=-3.695, gap=%.3f"
              % (mn.x, mn.x - (-3.695)))
checks.append("chairs nearest east wall: max_x=%.3f vs east inner face x=4.765, gap=%.3f"
              % (mx.x, 4.765 - mx.x))
# 门洞在东墙 y[-0.5, 0.5]；最近一排椅子（r8, x~4.51）各列 y
door_cols = sorted({round(o.location.y, 2) for o in by_prefix("chair_r8_")})
checks.append("rear-row chairs (r8) y columns: %s; door opening y[-0.5, 0.5] clear=%s"
              % (door_cols, all(abs(y) >= 0.5 for y in door_cols)))
# 2. 空调两台机身中心
for name in ("ac_front_ac_body", "ac_rear_ac_body"):
    o = bpy.data.objects.get(name)
    if o:
        checks.append("AC %s centre=%s size=%s" % (name, fmt(o.location), fmt(o.dimensions)))
# 3. 窗户：南侧 y=-3.58 组与北侧 y=+3.58 组
for side, y in (("south", -3.58), ("north", 3.58)):
    ws = [o for o in by_prefix("cl-windows_glass_")
          if abs(o.location.y - y) < 0.01]
    checks.append("windows %s (y=%.2f): %d glass panes, x=%s"
                  % (side, y, len(ws), sorted(round(o.location.x, 2) for o in ws)))
curt = by_prefix("cl-windows_curtain_")
checks.append("curtains: %d, y=%s"
              % (len(curt), sorted({round(o.location.y, 2) for o in curt})))
# 4. 灯具 z 范围（天花板 z=3.0）
mn, mx = world_bbox(by_prefix("cl-lights_"))
checks.append("lights bbox z[%.3f, %.3f] (ceiling z=3.0)" % (mn.z, mx.z))
# 5. 讲台黑板
mn, mx = world_bbox([o for o in bpy.context.scene.objects
                     if o.name in ("Blackboard", "DeskTop", "DeskFront")])
checks.append("board/desk bbox x[%.3f, %.3f] y[%.3f, %.3f] z[%.3f, %.3f]"
              % (mn.x, mx.x, mn.y, mx.y, mn.z, mx.z))
# 6. 整体
mn, mx = world_bbox(list(bpy.context.scene.objects))
checks.append("OVERALL bbox x[%.3f, %.3f] y[%.3f, %.3f] z[%.3f, %.3f]"
              % (mn.x, mx.x, mn.y, mx.y, mn.z, mx.z))
for c in checks:
    print("CHECK " + c)

# --- 存 .blend ---
os.makedirs(os.path.dirname(OUT_BLEND), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
print("SAVED " + OUT_BLEND)

# --- 导出 .glb（全选，默认 +Y up，不手动旋转）---
bpy.ops.object.select_all(action="SELECT")
os.makedirs(os.path.dirname(OUT_GLB), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=OUT_GLB, export_format="GLB",
                          use_selection=True, export_apply=True)
print("EXPORTED " + OUT_GLB)

# 导出器 clamp 补丁 (R2-T27)：把 >1 的墙补偿因子写回 GLB，见上。
_patch_glb_factors(OUT_GLB)

# --- 回读验证 ---
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=OUT_GLB)
n = len(bpy.context.scene.objects)
print("REIMPORT objects: %d" % n)
for o in bpy.context.scene.objects:
    if o.type != "MESH":
        print("REIMPORT non-mesh: %s %s" % (o.name, o.type))
print("DONE classroom")
