# R2-T9 PBR hard fix (2026-11-24): replace near-flat baked maps on the big
# visible faces with real CC0 photo textures at true world scale.
#
# Root cause (audited 2026-11-24, see BLENDER_MODELS.md §13):
# node wiring was complete everywhere (baseColor+rough+normal all linked),
# but the baked maps were near-flat (wall normal std ~0.5-3, asphalt color
# std ~4 within its tile) and one 1024 texture was stretched over whole
# 40 m walls / 260 m roads (~4.6 m per texel), so everything rendered as
# flat panels. Fix: link Poly Haven / ambientCG photo textures directly
# (pre-tinted to SPEC §3 in assets/external/pbr-tinted/, see SOURCES.md),
# roughness from the real rough map, normal from the real normal map,
# and rewrite UVs by per-face box projection so 1 texture tile covers a
# fixed real-world size (walls 2 m, asphalt 4 m, paving 3 m, roof 3 m,
# brick 1.5 m). No geometry, position or size is touched.
# Idempotent: re-running on an already-fixed file re-links the same
# images and recomputes the same world-scale UVs.
# Used two ways: (1) each ov-*.py execs this file after its bake step;
# (2) the R2-T9 fix run calls apply_pbr(piece) directly on the .blend.
import os

import bpy
from mathutils import Vector

_HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))  # .../demo-godot
EXT = os.path.join(BASE, "assets/external")
PH = os.path.join(EXT, "polyhaven")
AC = os.path.join(EXT, "ambientcg")
TINT = os.path.join(EXT, "pbr-tinted")

# set key -> (color file, rough file, normal file, tile metres, normal strength)
SETS = {
    "PLASTER_F3E9D2": (os.path.join(TINT, "plaster_F3E9D2_color.jpg"),
                       os.path.join(AC, "Plaster001/Plaster001_1K-JPG_Roughness.jpg"),
                       os.path.join(TINT, "plaster_normal_amp2.png"), 2.0, 1.0),
    "PLASTER_DFE9F2": (os.path.join(TINT, "plaster_DFE9F2_color.jpg"),
                       os.path.join(AC, "Plaster001/Plaster001_1K-JPG_Roughness.jpg"),
                       os.path.join(TINT, "plaster_normal_amp2.png"), 2.0, 1.0),
    "PLASTER_F6D9C0": (os.path.join(TINT, "plaster_F6D9C0_color.jpg"),
                       os.path.join(AC, "Plaster001/Plaster001_1K-JPG_Roughness.jpg"),
                       os.path.join(TINT, "plaster_normal_amp2.png"), 2.0, 1.0),
    "CONCRETE_B9B3A8": (os.path.join(TINT, "concrete_B9B3A8_color.jpg"),
                        os.path.join(PH, "concrete_wall_007_rough_1k.jpg"),
                        os.path.join(TINT, "concrete_normal_amp15.png"), 2.0, 1.0),
    "CONCRETE_D8D2C4": (os.path.join(TINT, "concrete_D8D2C4_color.jpg"),
                        os.path.join(PH, "concrete_wall_007_rough_1k.jpg"),
                        os.path.join(TINT, "concrete_normal_amp15.png"), 2.0, 1.0),
    "CONCRETE_424A52": (os.path.join(TINT, "concrete_424A52_color.jpg"),
                        os.path.join(PH, "concrete_wall_007_rough_1k.jpg"),
                        os.path.join(TINT, "concrete_normal_amp15.png"), 2.0, 1.0),
    "ROOF_424A52": (os.path.join(TINT, "roof_424A52_color.jpg"),
                    os.path.join(PH, "grey_roof_01_rough_1k.jpg"),
                    os.path.join(PH, "grey_roof_01_nor_gl_1k.jpg"), 3.0, 0.7),
    "BRICK_8E2F28": (os.path.join(TINT, "brick_8E2F28_color.jpg"),
                     os.path.join(PH, "red_bricks_04_rough_1k.jpg"),
                     os.path.join(PH, "red_bricks_04_nor_gl_1k.jpg"), 1.5, 0.8),
    "BRICK_A63A2C": (os.path.join(TINT, "brick_A63A2C_color.jpg"),
                     os.path.join(PH, "red_bricks_04_rough_1k.jpg"),
                     os.path.join(PH, "red_bricks_04_nor_gl_1k.jpg"), 1.5, 0.8),
    "ASPHALT": (os.path.join(TINT, "asphalt_424A52_color.jpg"),
                os.path.join(TINT, "asphalt_rough_090.jpg"),
                os.path.join(TINT, "asphalt_normal_amp2.png"), 4.0, 1.0),
    "PAVING_D8D2C4": (os.path.join(TINT, "paving_D8D2C4_color.jpg"),
                      os.path.join(PH, "concrete_pavement_03_rough_1k.jpg"),
                      os.path.join(TINT, "paving_normal_amp2.png"), 3.0, 1.0),
    "PAVING_DCD6C8": (os.path.join(TINT, "paving_DCD6C8_color.jpg"),
                      os.path.join(PH, "concrete_pavement_03_rough_1k.jpg"),
                      os.path.join(TINT, "paving_normal_amp2.png"), 3.0, 1.0),
    "PAVING_C9C2B0": (os.path.join(TINT, "paving_C9C2B0_color.jpg"),
                      os.path.join(PH, "concrete_pavement_03_rough_1k.jpg"),
                      os.path.join(TINT, "paving_normal_amp2.png"), 3.0, 1.0),
    "PAVING_E8B400": (os.path.join(TINT, "paving_E8B400_color.jpg"),
                      os.path.join(PH, "concrete_pavement_03_rough_1k.jpg"),
                      os.path.join(TINT, "paving_normal_amp2.png"), 3.0, 1.0),
    # R2-T9b (2026-11-25): running track, same asphalt maps as ASPHALT,
    # color tinted to SPEC track red #B8543F (asphalt_01 diff, linear-space
    # tint, R scale clamped at 4.0 -> achieved mean (170,84,63), dR 14).
    "TRACK_B8543F": (os.path.join(TINT, "track_B8543F_color.jpg"),
                     os.path.join(TINT, "asphalt_rough_090.jpg"),
                     os.path.join(TINT, "asphalt_normal_amp2.png"), 4.0, 1.0),
}

# piece -> {material name: set key}
PBR_MAP = {
    "ov-bldA": {"Wall_Cream_F3E9D2_tex": "PLASTER_F3E9D2",
                "Roof_DarkGrey_424A52_tex": "ROOF_424A52",
                "Concrete_B9B3A8_tex": "CONCRETE_B9B3A8",
                "Cornice_D8D2C4_tex": "CONCRETE_D8D2C4"},
    "ov-bldB": {"Wall_BlueGrey_DFE9F2_tex": "PLASTER_DFE9F2",
                "Roof_DarkGrey_424A52_tex": "ROOF_424A52",
                "Concrete_B9B3A8_tex": "CONCRETE_B9B3A8",
                "Cornice_D8D2C4_tex": "CONCRETE_D8D2C4"},
    "ov-bldC": {"Wall_Orange_F6D9C0_tex": "PLASTER_F6D9C0",
                "Roof_DarkGrey_424A52_tex": "ROOF_424A52",
                "Concrete_B9B3A8_tex": "CONCRETE_B9B3A8",
                "Cornice_D8D2C4_tex": "CONCRETE_D8D2C4"},
    "ov-lib": {"Lib_Wall_Orange_F6D9C0_tex": "PLASTER_F6D9C0",
               "Lib_Roof_DarkGrey_424A52_tex": "ROOF_424A52",
               "Lib_Concrete_B9B3A8_tex": "CONCRETE_B9B3A8",
               "Lib_Cornice_D8D2C4_tex": "CONCRETE_D8D2C4"},
    "ov-gym": {"ov-gym_wall_red": "BRICK_8E2F28",
               "ov-gym_wall_red_dark": "BRICK_8E2F28",
               "ov-gym_roof_dark": "ROOF_424A52",
               "ov-gym_concrete_tex": "CONCRETE_B9B3A8"},
    "ov-lab": {"Wall_White_F6F2E9_tex": "PLASTER_DFE9F2",  # SPEC §5: lab is blue-grey, was near-white
               "Roof_DarkGrey_424A52_tex": "ROOF_424A52",
               "Concrete_B9B3A8_tex": "CONCRETE_B9B3A8",
               "Cornice_D8D2C4_tex": "CONCRETE_D8D2C4",
               "Trim_RedBrick_A63A2C_tex": "BRICK_A63A2C"},
    "ov-tower": {"Wall_Cream_F7F5EF_tex": "PLASTER_F3E9D2",
                 "Roof_DarkGrey_424A52_tex": "ROOF_424A52",
                 "Concrete_B9B3A8_tex": "CONCRETE_B9B3A8",
                 "Cornice_D8D2C4_tex": "CONCRETE_D8D2C4"},
    "ov-canteen": {"Canteen_Wall_Orange_F6D9C0_tex": "PLASTER_F6D9C0",
                   "Canteen_Roof_DarkGrey_424A52_tex": "ROOF_424A52",
                   "Canteen_Concrete_B9B3A8_tex": "CONCRETE_B9B3A8",
                   "Canteen_Cornice_D8D2C4_tex": "CONCRETE_D8D2C4",
                   "Canteen_RedBrick_A63A2C_tex": "BRICK_A63A2C"},
    "ov-dorm": {"Wall_Cream_F3E9D2_tex": "PLASTER_F3E9D2",
                "Wall_BlueGrey_DFE9F2_tex": "PLASTER_DFE9F2",
                "Roof_DarkGrey_424A52_tex": "ROOF_424A52",
                "Concrete_B9B3A8_tex": "CONCRETE_B9B3A8",
                "Cornice_D8D2C4_tex": "CONCRETE_D8D2C4"},
    "ov-road-main": {"Asphalt_424A52": "ASPHALT",
                     "Curb_B9B3A8": "CONCRETE_B9B3A8"},
    "ov-road-walk": {"Paving_D8D2C4": "PAVING_D8D2C4",
                     "Walkway_DCD6C8": "PAVING_DCD6C8",
                     "FrameStone_C9C2B0": "PAVING_C9C2B0",
                     "Tactile_E8B400_EW": "PAVING_E8B400",
                     "Tactile_E8B400_NS": "PAVING_E8B400",
                     "Curb_B9B3A8": "CONCRETE_B9B3A8"},
    "ov-windows-roofs": {"ovw_roof_membrane": "CONCRETE_424A52",
                         "ovw_coping": "CONCRETE_B9B3A8",
                         "ovw_coping.001": "CONCRETE_B9B3A8"},
    # R2-T9b (2026-11-25): task says track follows the same standard as
    # asphalt ("跑道/铺装同理"); only the red ring gets PBR, lane lines and
    # curbs keep their baked maps (thin lines, not big faces).
    "ov-track": {"Track_Red_B8543F": "TRACK_B8543F"},
}

_img_cache = {}


def _load(path, colorspace):
    key = os.path.abspath(path)
    img = _img_cache.get(key)
    if img is None:
        for im in bpy.data.images:
            if os.path.abspath(bpy.path.abspath(im.filepath)) == key:
                img = im
                break
        if img is None:
            assert os.path.exists(key), "PBR texture missing: %s" % key
            img = bpy.data.images.load(key)
        _img_cache[key] = img
    img.colorspace_settings.name = colorspace
    try:
        img.extension = 'REPEAT'
    except Exception:
        pass
    # store a path the saved .blend can resolve (Actions checkout renders the
    # .blend directly, so its image paths must be blend-relative). The old
    # bpy.path.relpath(key) is only correct once a .blend file is open; from
    # a fresh factory-settings session (how the piece scripts run) it returns
    # a home-relative path (//workspace/...), which breaks on save: the save
    # unloads the pixels and the later glTF export drops the textures
    # ("Image has no size and cannot be exported", R2-T21b 2026-11-25).
    # The piece scripts pass their BLEND_PATH into this module's globals, so
    # relativize against the .blend's directory; otherwise fall back to the
    # open .blend, else keep the absolute path.
    _bp = globals().get("BLEND_PATH") or bpy.data.filepath
    try:
        if _bp:
            img.filepath = "//" + os.path.relpath(key, os.path.dirname(_bp))
        else:
            img.filepath = key
    except Exception:
        img.filepath = key
    return img


def _trace_image(bsdf, input_name):
    """Follow the link from a Principled input to its TEX_IMAGE node (if any)."""
    sock = bsdf.inputs.get(input_name)
    if sock is None or not sock.is_linked:
        return None, None
    node = sock.links[0].from_node
    if node.type == 'TEX_IMAGE':
        return node, None
    if node.type == 'NORMAL_MAP':
        src = node.inputs["Color"]
        if src.is_linked and src.links[0].from_node.type == 'TEX_IMAGE':
            return src.links[0].from_node, node
        return None, node
    return None, None


def _swap_material(mat, set_key):
    color_f, rough_f, normal_f, _tile, nstr = SETS[set_key]
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    assert bsdf is not None, "no Principled BSDF in %s" % mat.name
    old = []
    tex_c, _ = _trace_image(bsdf, "Base Color")
    tex_r, _ = _trace_image(bsdf, "Roughness")
    tex_n, nmap = _trace_image(bsdf, "Normal")
    assert tex_c is not None and tex_r is not None and tex_n is not None, \
        "PBR swap: %s lacks image links (color=%s rough=%s normal=%s)" % (
            mat.name, tex_c, tex_r, tex_n)
    for node, f, cs in ((tex_c, color_f, 'sRGB'),
                        (tex_r, rough_f, 'Non-Color'),
                        (tex_n, normal_f, 'Non-Color')):
        if node.image is not None:
            old.append(node.image)
        node.image = _load(f, cs)
    if nmap is not None:
        nmap.inputs["Strength"].default_value = nstr
    bsdf.inputs["Base Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    bsdf.inputs["Roughness"].default_value = 1.0
    bsdf.inputs["Metallic"].default_value = 0.0
    return old


def _reproject_uvs(objs, mat, tile):
    """Per-face box projection of UVs from world coords / tile metres.
    Only faces whose material is `mat` are touched."""
    done = 0
    for ob in objs:
        if ob.type != 'MESH':
            continue
        me = ob.data
        if me.users > 1:
            ob.data = me.copy()
            me = ob.data
        if not me.uv_layers:
            me.uv_layers.new(name="UVMap")
        uv = me.uv_layers.active.data
        loops = me.loops
        mw = ob.matrix_world
        nm = mw.to_3x3().inverted().transposed()
        verts = me.vertices
        for poly in me.polygons:
            if poly.material_index >= len(me.materials) or me.materials[poly.material_index] != mat:
                continue
            n = (nm @ poly.normal).normalized()
            ax = max(range(3), key=lambda i: abs(n[i]))
            # the two world axes spanning this face
            a1, a2 = (1, 2) if ax == 0 else ((0, 2) if ax == 1 else (0, 1))
            for li in poly.loop_indices:
                co = mw @ verts[loops[li].vertex_index].co
                uv[li].uv = (co[a1] / tile, co[a2] / tile)
            done += 1
    return done


def apply_pbr(piece):
    """Swap PBR textures + world-scale UVs for one piece. Returns a report dict."""
    table = PBR_MAP[piece]
    report = {"piece": piece, "materials": {}, "uv_faces": 0, "purged": []}
    # group objects by target material
    mat_objs = {}
    for ob in bpy.data.objects:
        if ob.type != 'MESH':
            continue
        for slot in ob.material_slots:
            if slot.material and slot.material.name in table:
                mat_objs.setdefault(slot.material.name, []).append(ob)
    old_images = []
    for mat_name, set_key in table.items():
        mat = bpy.data.materials.get(mat_name)
        if mat is None:
            print("PBR: material missing, skip:", mat_name)
            continue
        old_images.extend(_swap_material(mat, set_key))
        objs = mat_objs.get(mat_name, [])
        tile = SETS[set_key][3]
        n = _reproject_uvs(objs, mat, tile)
        report["materials"][mat_name] = {"set": set_key, "objects": len(objs),
                                         "faces": n, "tile_m": tile}
        report["uv_faces"] += n
        print("PBR: %s -> %s (%d objs, %d faces, tile %.1fm)"
              % (mat_name, set_key, len(objs), n, tile))
    # purge orphaned baked images replaced above (only when nothing uses them).
    # Collect names first: the same datablock can appear twice in old_images,
    # and touching a removed datablock raises ReferenceError.
    _names = []
    for _im in old_images:
        try:
            if _im.name not in _names:
                _names.append(_im.name)
        except ReferenceError:
            pass
    for _name in _names:
        try:
            _cur = bpy.data.images.get(_name)
            if _cur is not None and _cur.users == 0:
                bpy.data.images.remove(_cur)
                report["purged"].append(_name)
        except Exception as e:
            print("PBR: purge skip %s: %s" % (_name, e))
    print("PBR done %s: %d materials, %d faces reprojected, purged %d images"
          % (piece, len(report["materials"]), report["uv_faces"], len(report["purged"])))
    return report
