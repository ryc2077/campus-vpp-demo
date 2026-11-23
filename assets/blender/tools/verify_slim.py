# 验证瘦身总览 + 出 gzip 瘦身 .blend（无头，不渲染）。
# 用法：blender -b --python verify_slim.py
#   1) 回读瘦身 GLB：对象数、0 无材质 primitive；
#   2) 打开完整版 overview.blend，在原目录内另存 overview-slim.blend
#      （save_as_mainfile(compress=True)；同目录另存才不改写相对贴图路径）；
#   3) 原目录重开瘦身 .blend：对象数、缺失文件 0。
# 只写 overview-slim.blend 一个新文件；完整版 .blend/.glb 不动。

import bpy
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
# tools -> blender -> assets -> demo-godot
SCENES = os.path.join(ROOT, "assets", "blender", "scenes")
FULL_GLB = os.path.join(ROOT, "assets", "models", "scenes", "overview.glb")
SLIM_GLB = os.path.join(ROOT, "assets", "models", "scenes",
                        "overview-slim.glb")
FULL_BLEND = os.path.join(SCENES, "overview.blend")
SLIM_BLEND = os.path.join(SCENES, "overview-slim.blend")


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
assert n_glb == 13036, "slim GLB objects %d != 13036" % n_glb
assert nomat == 0, "slim GLB has %d no-material prims" % nomat

# ---------- 2. gzip 瘦身 .blend（原目录内另存） ----------
bpy.ops.wm.open_mainfile(filepath=FULL_BLEND)
n_full = len(bpy.context.scene.objects)
print("VERIFY-BLEND-FULL objects=%d size=%d"
      % (n_full, os.path.getsize(FULL_BLEND)))
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
assert n_slim == n_full == 13036, \
    "slim blend objects %d != full %d" % (n_slim, n_full)
assert len(missing) == 0, "missing files: %s" % missing
print("DONE verify_slim")
