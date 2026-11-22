# pv scene assembly (campus VPP demo, Blender 4.2.0)
# Puts the 4 PV pieces together into one scene, global coords, no moves.
# Pieces (assets/blender/pv/; MESH objects only -- cameras / lights / sun
# and light probes are excluded):
#   pv-roof     (datum piece, untouched)  - 33 objects
#   pv-panels   (panel array)             - 548 objects
#   pv-mount    (mounts)                  - 3 objects
#   pv-inverter (inverters + trunking)    - 297 objects
# Total: 881 MESH objects.
#
# Source .blend versions ACTUALLY APPENDED (verified from the assembled
# scene: mount z 18.34-19.02, inverter base z 18.41-18.53 -- i.e. the
# -0.65 m lowered versions, NOT the ones current when the run started):
#   pv-roof.blend     2026-11-22 15:07:20 UTC  d2681c695bf10f9b9b6452b750c9ea88
#   pv-panels.blend   2026-11-22 15:18:54 UTC  e3cdb078289ed18bce18524a1e86f8f8
#   pv-mount.blend    2026-11-22 15:37:53 UTC  23a4fd6338016bfb1f6397737945b77b
#   pv-inverter.blend 2026-11-22 15:27:11 UTC  cd9529465217e76ffeb072d4690946d8
# NOTE: the parallel PV fix task rewrote pv-mount (15:37:53) and
# pv-inverter (15:27:11) WHILE this run was appending (the 548-panel
# append loop takes ~30 min). The script's start-of-run stamps for those
# two pieces (mount 15:09:54 8d12f53c..., inverter 15:09:19 ab6e8a1f...)
# are therefore stale; the run printed SRC-UNCHANGED only for roof and
# panels and WARNING for mount/inverter. The .blend/.glb below contain
# the NEW lowered mount/inverter. A refresh re-run is still worthwhile
# once the fix task finishes, to get a clean single-version snapshot
# (and to pick up any corner-panel move in pv-panels, which has not
# changed since 15:18:54).
#
# Outputs:
#   assets/blender/scenes/pv.blend
#   assets/models/scenes/pv.glb   (GLB, use_selection, export_apply, +Y up)
# No rendering in this script (all renders go through GitHub Actions).

import bpy
import hashlib
import os

BASE = os.path.expanduser(
    "~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
PV_DIR = os.path.join(BASE, "assets/blender/pv")
BLEND_PATH = os.path.join(BASE, "assets/blender/scenes/pv.blend")
GLB_PATH = os.path.join(BASE, "assets/models/scenes/pv.glb")

PIECES = ["pv-roof", "pv-panels", "pv-mount", "pv-inverter"]
EXPECTED = {"pv-roof": 33, "pv-panels": 548, "pv-mount": 3, "pv-inverter": 297}


def file_stamp(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    st = os.stat(path)
    return st.st_mtime, st.st_size, h.hexdigest()


def preview_object_names(blend_path):
    """Data-block object names in a .blend, without loading anything."""
    with bpy.data.libraries.load(blend_path, link=False) as (src, _dst):
        return list(src.objects)


def main():
    # ---- record source versions (before append) ----
    stamps_before = {}
    for piece in PIECES:
        path = os.path.join(PV_DIR, piece + ".blend")
        stamps_before[piece] = file_stamp(path)
        mtime, size, md5 = stamps_before[piece]
        print(f"SRC {piece}.blend mtime={mtime:.0f} size={size} md5={md5}")

    # ---- fresh scene ----
    bpy.ops.wm.read_factory_settings(use_empty=True)

    total_appended = 0
    for piece in PIECES:
        path = os.path.join(PV_DIR, piece + ".blend")
        names = preview_object_names(path)
        kept = 0
        for name in names:
            bpy.ops.wm.append(
                filepath=os.path.join(path, "Object", name),
                directory=os.path.join(path, "Object") + "/",
                filename=name,
                link=False,
            )
            obj = bpy.data.objects.get(name)
            if obj is None:
                # Appended under a renamed data-block; find newest object.
                print(f"WARN {piece}: appended {name!r} not found by name")
                continue
            if obj.type != "MESH":
                print(f"SKIP non-mesh {piece}: {obj.type} {obj.name}")
                bpy.data.objects.remove(obj, do_unlink=True)
            else:
                kept += 1
        print(f"APPEND {piece}: {kept} mesh objects "
              f"(expected {EXPECTED[piece]})")
        assert kept == EXPECTED[piece], (
            f"{piece}: appended {kept}, expected {EXPECTED[piece]}")
        total_appended += kept

    print(f"TOTAL appended mesh objects: {total_appended}")
    assert total_appended == 881, f"expected 881, got {total_appended}"
    assert len(bpy.data.objects) == 881, (
        f"scene has {len(bpy.data.objects)} objects, expected 881")

    # ---- save .blend (no moves, no edits) ----
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print(f"SAVED {BLEND_PATH} size={os.path.getsize(BLEND_PATH)}")

    # ---- export GLB: all selected, apply transforms, default +Y up ----
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.gltf(
        filepath=GLB_PATH,
        export_format="GLB",
        use_selection=True,
        export_apply=True,
    )
    print(f"EXPORTED {GLB_PATH} size={os.path.getsize(GLB_PATH)}")

    # ---- confirm sources did not change mid-run (parallel fix task) ----
    for piece in PIECES:
        path = os.path.join(PV_DIR, piece + ".blend")
        after = file_stamp(path)
        if after != stamps_before[piece]:
            print(f"WARNING source changed during run: {piece}.blend "
                  f"before={stamps_before[piece]} after={after}")
        else:
            print(f"SRC-UNCHANGED {piece}.blend")

    # ---- re-import GLB to verify it opens ----
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=GLB_PATH)
    imported = [o for o in bpy.data.objects]
    print(f"REIMPORT {GLB_PATH}: {len(imported)} objects")
    assert len(imported) == 881, (
        f"reimported {len(imported)} objects, expected 881")

    print("DONE pv")


main()
