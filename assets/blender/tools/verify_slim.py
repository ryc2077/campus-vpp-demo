# 验证瘦身总览 + 出 gzip 瘦身 .blend（无头，不渲染）。
# 用法：blender -b --python verify_slim.py [-- --expected-objects N]
#   1) 回读瘦身 GLB：对象数、0 无材质 primitive；
#   2) 打开完整版 overview.blend，在原目录内另存 overview-slim.blend
#      （save_as_mainfile(compress=True)；同目录另存才不改写相对贴图路径）；
#   3) 原目录重开瘦身 .blend：对象数、缺失文件 0。
# 只写 overview-slim.blend 一个新文件；完整版 .blend/.glb 不动。
#
# 期望对象数（R2-T39 参数化；原写死 13036 是树重建前的旧口径，
# 总览重拼到 13217 后已过时，R2-T1b 只能用 /tmp 副本绕过）：
#   - 默认不写死：期望值 = 完整版 overview.blend 的实测对象数 n_full。
#     总览重拼脚本 assets/blender/scenes/overview.py 写出该 .blend，
#     其 SCENE objects= 行即同一数字；瘦身只动贴图、不动几何，
#     瘦身 GLB / 瘦身 .blend 的对象数必须与完整版一致，
#     下次重拼改了对象数也不用再改本脚本。
#   - 可选显式钉死：命令行 `... -- --expected-objects 13217`
#     （注意 `--` 分隔符，Blender 自己的参数在前），
#     或环境变量 VERIFY_SLIM_EXPECTED_OBJECTS=13217（命令行优先）。
#     显式值下三处（瘦身 GLB、完整版、瘦身 .blend）都要等于它，
#     否则在写 overview-slim.blend 之前就报错退出。
#   - 当前实测期望值 13217（2026-11-24 R2-T1b 重拼：append 13213 + 拼装 4），
#     仅作注释参考，不参与断言。

import bpy
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
# tools -> blender -> assets -> demo-godot
SCENES = os.path.join(ROOT, "assets", "blender", "scenes")
FULL_GLB = os.path.join(ROOT, "assets", "models", "scenes", "overview.glb")
SLIM_GLB = os.path.join(ROOT, "assets", "models", "scenes",
                        "overview-slim.glb")
FULL_BLEND = os.path.join(SCENES, "overview.blend")
SLIM_BLEND = os.path.join(SCENES, "overview-slim.blend")


def _expected_objects():
    """返回 (期望对象数或 None, 来源说明)。

    优先级：命令行 --expected-objects N（Blender 参数后 `--` 分隔）
    > 环境变量 VERIFY_SLIM_EXPECTED_OBJECTS > None（默认，
    调用处改取完整版 .blend 的实测对象数 n_full）。
    """
    argv = sys.argv
    args = argv[argv.index("--") + 1:] if "--" in argv else []
    for i, a in enumerate(args):
        if a == "--expected-objects" and i + 1 < len(args):
            return int(args[i + 1]), "--expected-objects"
        if a.startswith("--expected-objects="):
            return int(a.split("=", 1)[1]), "--expected-objects"
    env = os.environ.get("VERIFY_SLIM_EXPECTED_OBJECTS", "").strip()
    if env:
        return int(env), "VERIFY_SLIM_EXPECTED_OBJECTS"
    return None, None


EXPECTED, EXPECTED_SRC = _expected_objects()


def count_no_material_prims():
    n = 0
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        mats = obj.data.materials
        if len(mats) == 0:
            n += 1
        else:
            for m in mats:
                if m is None:
                    n += 1
    return n


# ---------- 1. 回读瘦身 GLB ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SLIM_GLB)
n_glb = len(bpy.context.scene.objects)
n_mesh = sum(1 for o in bpy.context.scene.objects if o.type == "MESH")
nomat = count_no_material_prims()
print("VERIFY-GLB objects=%d mesh=%d no_material_prims=%d"
      % (n_glb, n_mesh, nomat))
# 对象数不断言在这里：期望值取自完整版 .blend（下一步才打开），
# 先只断言无材质 primitive；对象数一致性在第 2 步后统一断言。
assert nomat == 0, "slim GLB has %d no-material prims" % nomat

# ---------- 2. gzip 瘦身 .blend（原目录内另存） ----------
bpy.ops.wm.open_mainfile(filepath=FULL_BLEND)
n_full = len(bpy.context.scene.objects)
print("VERIFY-BLEND-FULL objects=%d size=%d"
      % (n_full, os.path.getsize(FULL_BLEND)))
if EXPECTED is None:
    expected, expected_src = n_full, "full-blend"
else:
    expected, expected_src = EXPECTED, EXPECTED_SRC
print("EXPECTED objects=%d source=%s" % (expected, expected_src))
assert n_glb == expected, \
    "slim GLB objects %d != expected %d (%s)" % (n_glb, expected,
                                                 expected_src)
assert n_full == expected, \
    "full blend objects %d != expected %d (%s)" % (n_full, expected,
                                                   expected_src)
bpy.ops.wm.save_as_mainfile(filepath=SLIM_BLEND, compress=True)
print("SAVED-SLIM-BLEND %s size=%d (full %d)"
      % (SLIM_BLEND, os.path.getsize(SLIM_BLEND),
         os.path.getsize(FULL_BLEND)))

# ---------- 3. 原目录重开瘦身 .blend ----------
bpy.ops.wm.open_mainfile(filepath=SLIM_BLEND)
n_slim = len(bpy.context.scene.objects)
missing = []
for img in bpy.data.images:
    if img.packed_file is not None or not img.filepath:
        continue
    if not os.path.exists(bpy.path.abspath(img.filepath)):
        missing.append(img.name)
print("VERIFY-BLEND-SLIM objects=%d images=%d missing_files=%d %s"
      % (n_slim, len(bpy.data.images), len(missing), missing))
assert n_slim == n_full == expected, \
    "slim blend objects %d != full %d (expected %d, %s)" % (
        n_slim, n_full, expected, expected_src)
assert len(missing) == 0, "missing files: %s" % missing
print("DONE verify_slim")
