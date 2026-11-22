# Max-quality Eevee render settings (Actions only; never render locally).
# Usage: blender -b file.blend -E BLENDER_EEVEE_NEXT --python tools/render_max.py -o out/name_ -f 1
# Only touches render settings and (if the file lacks them) adds a framing
# camera, a default sun and a sky world background so the preview is
# visible; scene content, lights and world are left as built when present.
import math

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

_MESH_TYPES = {'MESH', 'CURVE', 'SURFACE', 'FONT', 'META',
               'LATTICE', 'GPENCIL'}
# Objects that are preview scaffolding, not the piece itself: they must
# not drive framing decisions (e.g. ov-road-main's 320x280 ground plane
# would otherwise swallow the road net).
_PREVIEW_PREFIXES = ('PREVIEW', 'Preview')
_PREVIEW_NAMES = {'Ground_PreviewOnly'}


def _set(obj, name, value):
    try:
        setattr(obj, name, value)
    except Exception as e:
        print(f"render_max: skip {name}: {e}")


def _is_preview_only(ob):
    if ob.name in _PREVIEW_NAMES:
        return True
    return ob.name.startswith(_PREVIEW_PREFIXES)


def _subject_objects(scene):
    """Mesh-like objects that ARE the piece (preview scaffolding excluded)."""
    objs = [ob for ob in scene.objects
            if ob.type in _MESH_TYPES and not _is_preview_only(ob)]
    if not objs:  # piece with nothing but scaffolding: fall back to all meshes
        objs = [ob for ob in scene.objects if ob.type in _MESH_TYPES]
    return objs


def _objects_bbox(objs):
    """World-space bbox (mins, maxs) of a list of objects, or None."""
    mins = Vector((float('inf'),) * 3)
    maxs = Vector((float('-inf'),) * 3)
    for ob in objs:
        for corner in ob.bound_box:
            p = ob.matrix_world @ Vector(corner)
            mins = Vector(map(min, mins, p))
            maxs = Vector(map(max, maxs, p))
    if mins.x == float('inf'):
        return None
    return mins, maxs


def _fit_camera(scene, objs, name, direction=None):
    """Create a perspective camera framing exactly `objs` (3/4 high view
    over their bounding-box centre) and return it. Does not set
    scene.camera; the caller does.

    `direction` is the (unnormalised) camera offset direction; default
    (1, -1, 0.75) is the 3/4 high view from +X, -Y, above. Flat
    clusters (wall signs) pass a direction that looks at their face
    instead of their back (see _ensure_camera).

    Framing fit (2026-11-23 magenta-root-cause fix):
    project the 8 bbox corners onto the camera right/up axes and fit
    each axis against its OWN half-FOV, derived from the render aspect
    ratio. Near corners stick out toward the camera by hd, so the
    centre-plane distance is raised by hd as well.
    NOTE: Camera.angle is already in radians; do NOT math.radians() it
    (that put the camera ~56x too far away and the model was invisible).
    """
    bbox = _objects_bbox(objs)
    cam_data = bpy.data.cameras.new(name)
    cam_data.type = 'PERSP'
    cam_data.lens = 50.0
    cam = bpy.data.objects.new(name, cam_data)
    scene.collection.objects.link(cam)
    # 3/4 high view: from +X, -Y, above, looking at the bbox centre.
    if direction is None:
        direction = Vector((1.0, -1.0, 0.75))
    direction = direction.normalized()
    fwd = -direction  # camera -> bbox centre
    world_up = Vector((0.0, 0.0, 1.0))
    right = fwd.cross(world_up).normalized()
    up = right.cross(fwd).normalized()
    aspect = (scene.render.resolution_x * scene.render.resolution_percentage
              / max(1.0, scene.render.resolution_y
                    * scene.render.resolution_percentage))
    aspect = min(max(aspect, 0.25), 4.0)  # guard against degenerate resolutions
    if aspect >= 1.0:
        h_half = cam_data.angle / 2.0
        v_half = math.atan(math.tan(h_half) / aspect)
    else:
        v_half = cam_data.angle / 2.0
        h_half = math.atan(math.tan(v_half) * aspect)
    if bbox is None:
        center = Vector((0.0, 0.0, 0.0))
        dist = 5.0 / math.sin(min(h_half, v_half)) * 1.10
    else:
        mins, maxs = bbox
        center = (mins + maxs) * 0.5
        hw = hh = hd = 0.0
        for sx in (mins.x, maxs.x):
            for sy in (mins.y, maxs.y):
                for sz in (mins.z, maxs.z):
                    v = Vector((sx, sy, sz)) - center
                    hw = max(hw, abs(v.dot(right)))
                    hh = max(hh, abs(v.dot(up)))
                    hd = max(hd, -v.dot(fwd))
        margin = 1.10
        dist = max(hw / math.tan(h_half), hh / math.tan(v_half)) * margin + hd
    cam.location = center + direction * dist
    cam.rotation_euler = (center - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam_data.clip_start = max(0.01, dist / 1000.0)
    cam_data.clip_end = max(1000.0, dist * 10.0)
    print(f"render_max: created camera {name} at "
          f"{tuple(round(v, 2) for v in cam.location)} "
          f"looking at {tuple(round(v, 2) for v in center)} (dist {dist:.2f}, "
          f"aspect {aspect:.2f})")
    return cam


def _projected_stats(scene, cam, objs):
    """How much of `objs` a camera actually shows.

    Returns (frac_corners_inside, total_clipped_area, n_fully_outside):
    the fraction of bbox corners inside the frame, the sum over objects
    of their bbox's projected area clipped to the frame (an upper bound
    on the subject's share of the frame; thin plates on walls score low
    even when their bbox spans the room, which is exactly the di-signs
    case), and how many objects lie entirely outside the frame (the
    pv-roof v1 signature: whole roofs missing, not just edge-clipped).
    """
    bpy.context.view_layer.update()
    corners_total = 0
    corners_inside = 0
    total_area = 0.0
    n_fully_outside = 0
    for ob in objs:
        xs, ys = [], []
        inside = 0
        for corner in ob.bound_box:
            p = ob.matrix_world @ Vector(corner)
            ndc = world_to_camera_view(scene, cam, p)
            corners_total += 1
            if ndc.z > 0.0 and 0.0 <= ndc.x <= 1.0 and 0.0 <= ndc.y <= 1.0:
                corners_inside += 1
                inside += 1
            xs.append(ndc.x)
            ys.append(ndc.y)
        if inside == 0:
            n_fully_outside += 1
        x0, x1 = max(0.0, min(xs)), min(1.0, max(xs))
        y0, y1 = max(0.0, min(ys)), min(1.0, max(ys))
        if x1 > x0 and y1 > y0:
            total_area += (x1 - x0) * (y1 - y0)
    frac = corners_inside / max(1, corners_total)
    return frac, total_area, n_fully_outside


def _bbox_gap(a_min, a_max, b_min, b_max):
    """Euclidean gap between two world-space bboxes (0 if they overlap)."""
    d2 = 0.0
    for i in range(3):
        sep = max(a_min[i] - b_max[i], b_min[i] - a_max[i], 0.0)
        d2 += sep * sep
    return math.sqrt(d2)


def _clusters(objs, gap=3.0):
    """Single-linkage clusters of objects by bbox gap (2026-11-23 fix).

    Sparse multi-piece groups (pv-inverter: 3 inverters 30m+ apart,
    di-signs: north wall vs east wall) must not share one whole-bbox
    camera: each cluster gets its own framing. Objects whose bboxes
    nearly touch (panels on one roof, trees, a continuous road net)
    stay in one cluster.
    """
    boxes = []
    for ob in objs:
        bb = _objects_bbox([ob])
        boxes.append(bb)
    n = len(objs)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(n):
        for j in range(i + 1, n):
            if _bbox_gap(boxes[i][0], boxes[i][1],
                         boxes[j][0], boxes[j][1]) <= gap:
                ri, rj = find(i), find(j)
                if ri != rj:
                    parent[ri] = rj
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(objs[i])
    return list(groups.values())


def _cluster_label(cluster, clusters):
    """Short filename suffix for one cluster, e.g. A1 / LAB / N / E.

    Prefers a token shared by the cluster's names (INV_A1_* -> A1);
    otherwise the cluster's compass direction from the scene centre
    (di-signs north wall -> N, east wall -> E); else C1, C2, ...
    """
    names = [ob.name for ob in cluster]
    # Longest common prefix STRING (not token-wise: trunk parts are
    # tagged A1N/A1S, so a token-wise prefix stops at "INV"; the string
    # prefix still yields "INV_A1" -> A1).
    prefix = names[0]
    for nm in names[1:]:
        i = 0
        while i < len(prefix) and i < len(nm) and prefix[i] == nm[i]:
            i += 1
        prefix = prefix[:i]
    token = prefix.rstrip('_-').split('_')[-1] if prefix else ''
    if token and len(token) <= 6 and token.isalnum():
        # the token must actually distinguish this cluster from the others
        others = [c for c in clusters if c is not cluster]
        other_names = {ob.name for c in others for ob in c}
        if not any(token in nm.split('_') for nm in other_names):
            return token
    # compass direction from the scene centre
    mins, maxs = _objects_bbox(cluster)
    centre = (mins + maxs) * 0.5
    all_mins, all_maxs = _objects_bbox(
        [ob for c in clusters for ob in c])
    scene_centre = (all_mins + all_maxs) * 0.5
    d = centre - scene_centre
    label = 'N' if abs(d.y) >= abs(d.x) else 'E'
    if abs(d.y) >= abs(d.x):
        label = 'N' if d.y >= 0 else 'S'
    else:
        label = 'E' if d.x >= 0 else 'W'
    taken = set()
    for c in clusters:
        if c is cluster:
            break
        taken.add(_cluster_label(c, clusters))
    if label in taken:
        k = 2
        while f"{label}{k}" in taken:
            k += 1
        label = f"{label}{k}"
    return label


def _ensure_camera(scene):
    """Make sure the scene has an active camera that shows the piece.

    (1) A built-in camera is kept unless it hides the piece: at least
    one subject object entirely outside the frame (pv-roof v1
    PreviewCamera, which framed only the A-block roof and left the
    B/lab roofs out of frame) or under 2% projected subject share
    (di-signs 22mm, subject share ~0.5%). A camera that merely clips
    a few bbox corners at the frame edge (ov-track) is kept. A stale
    camera that fails the test is overridden by the automatic camera
    instead of being trusted.
    (2) If the piece is sparse -- several well-separated clusters whose
    projected share under one whole-bbox camera is <2% -- each cluster
    is rendered as its own still (<name>-<cluster>.png) at max quality,
    and the main <name>.png keeps the largest cluster's view.
    Flat clusters (wall signs: one bbox dimension far smaller than the
    others) are viewed from the room side -- from the cluster toward
    the whole-piece centre -- so the camera sees the sign faces, not
    their backs through the wall.
    Otherwise a single automatic camera frames the whole piece.
    """
    objs = _subject_objects(scene)
    cam = scene.camera
    if cam is not None and cam.type == 'CAMERA':
        frac, area, n_out = _projected_stats(scene, cam, objs)
        if n_out == 0 and area >= 0.02:
            print(f"render_max: using existing camera {cam.name} "
                  f"(corners inside {frac:.2f}, frame share {area:.3f})")
            return
        print(f"render_max: overriding existing camera {cam.name} "
              f"(corners inside {frac:.2f}, frame share {area:.3f}, "
              f"objects fully outside: {n_out})")

    clusters = _clusters(objs)
    whole_cam = _fit_camera(scene, objs, "PreviewCamera")
    scene.camera = whole_cam
    _, whole_area, _ = _projected_stats(scene, whole_cam, objs)
    if 2 <= len(clusters) <= 8 and whole_area < 0.02:
        # Sparse multi-cluster piece: one still per cluster.
        base = scene.render.filepath
        stem = base[:-1] if base.endswith("_") else base
        labels = [_cluster_label(c, clusters) for c in clusters]
        whole_mins, whole_maxs = _objects_bbox(objs)
        whole_centre = (whole_mins + whole_maxs) * 0.5
        order = sorted(
            range(len(clusters)),
            key=lambda i: -(_objects_bbox(clusters[i])[1]
                            - _objects_bbox(clusters[i])[0]).length)
        main_cam = None
        for idx in order:
            cmins, cmaxs = _objects_bbox(clusters[idx])
            csize = cmaxs - cmins
            direction = None
            if min(csize) < 0.25 * max(csize):
                # flat cluster: face it from the piece-centre side
                to_centre = whole_centre - (cmins + cmaxs) * 0.5
                flat = Vector((to_centre.x, to_centre.y, 0.0))
                if flat.length > 0.1:
                    direction = Vector((flat.x, flat.y, 0.75))
            ccam = _fit_camera(scene, clusters[idx],
                               "PreviewCamera_" + labels[idx], direction)
            scene.camera = ccam
            if main_cam is None:
                main_cam = ccam
            scene.render.filepath = stem + "-" + labels[idx]
            print(f"render_max: rendering cluster {labels[idx]} "
                  f"({len(clusters[idx])} objects) -> "
                  f"{scene.render.filepath}.png")
            bpy.ops.render.render(write_still=True)
        scene.camera = main_cam
        scene.render.filepath = base
        print(f"render_max: sparse piece: {len(clusters)} cluster renders "
              f"({', '.join(labels)}), main view = largest cluster")
        return
    print(f"render_max: whole-piece framing, frame share {whole_area:.3f}")


def _ensure_light(scene):
    """Add a default sun if the file has no light at all.

    Several .blend files were built from factory-empty scenes with no
    lights, so EEVEE rendered a black frame. Energy 3.5 matches the sun
    the good generator scripts use.
    """
    for ob in scene.objects:
        if ob.type == 'LIGHT':
            return
    light_data = bpy.data.lights.new("PreviewSun", type='SUN')
    light_data.energy = 3.5
    sun = bpy.data.objects.new("PreviewSun", light_data)
    scene.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(50.0), 0.0, math.radians(30.0))
    print("render_max: added default sun (energy 3.5)")


def _ensure_world(scene):
    """Add a sky background if the file has no world or a black one.

    Same black-frame cause as _ensure_light: factory-empty scenes have
    no world, so the background renders pure black. Sky colour/strength
    match what the good generator scripts use.
    """
    world = scene.world
    if world is None:
        world = bpy.data.worlds.new("PreviewWorld")
        scene.world = world
        print("render_max: created world")
    world.use_nodes = True
    nodes = world.node_tree.nodes
    bg = nodes.get("Background")
    if bg is None:
        bg = nodes.new("ShaderNodeBackground")
        out = nodes.get("World Output")
        if out is not None:
            world.node_tree.links.new(bg.outputs["Background"],
                                      out.inputs["Surface"])
    color = bg.inputs["Color"].default_value
    lum = 0.2126 * color[0] + 0.7152 * color[1] + 0.0722 * color[2]
    if lum < 0.02:
        bg.inputs["Color"].default_value = (0.65, 0.78, 0.88, 1.0)
        bg.inputs["Strength"].default_value = 1.0
        print("render_max: set world background to sky (was near-black)")


def _apply_max_settings(scene):
    """Max-quality Eevee settings. Applied before _ensure_camera so that
    per-cluster stills render at max quality too, not at the .blend's
    stored preview settings."""
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False

    eevee = scene.eevee
    _set(eevee, 'taa_render_samples', 256)
    _set(eevee, 'use_taa_reprojection', True)
    _set(eevee, 'use_bloom', True)
    _set(eevee, 'bloom_intensity', 0.05)
    _set(eevee, 'use_ssr', True)
    _set(eevee, 'use_ssr_refraction', True)
    _set(eevee, 'use_gtao', True)
    _set(eevee, 'gtao_distance', 0.5)
    _set(eevee, 'use_shadows', True)
    # 4.2: shadow_pool_size is an enum of strings, max '1024' (was int 4096).
    _set(eevee, 'shadow_pool_size', '1024')
    _set(eevee, 'use_soft_shadows', True)


scene = bpy.context.scene
_ensure_light(scene)
_ensure_world(scene)
_apply_max_settings(scene)
_ensure_camera(scene)
print("render_max: max quality settings applied")
