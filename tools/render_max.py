# Max-quality Eevee render settings (Actions only; never render locally).
# Usage: blender -b file.blend -E BLENDER_EEVEE_NEXT --python tools/render_max.py -o out/name_ -f 1
# Only touches render settings and (if the file has no camera) adds a
# framing camera; scene content, lights and world are left as built.
import math

import bpy
from mathutils import Vector


def _set(obj, name, value):
    try:
        setattr(obj, name, value)
    except Exception as e:
        print(f"render_max: skip {name}: {e}")


def _ensure_camera(scene):
    """Make sure the scene has an active camera.

    Reuse an existing camera object if the file has one but it is not set
    as active; otherwise create a perspective camera framing the whole
    model (3/4 high view over the scene bounding-box centre).
    """
    if scene.camera is not None:
        return
    for ob in scene.objects:
        if ob.type == 'CAMERA':
            scene.camera = ob
            print(f"render_max: using existing camera {ob.name}")
            return

    # Bounding box of all geometry, in world space.
    mins = Vector((float('inf'),) * 3)
    maxs = Vector((float('-inf'),) * 3)
    for ob in scene.objects:
        if ob.type not in {'MESH', 'CURVE', 'SURFACE', 'FONT', 'META',
                           'LATTICE', 'GPENCIL'}:
            continue
        for corner in ob.bound_box:
            p = ob.matrix_world @ Vector(corner)
            mins = Vector(map(min, mins, p))
            maxs = Vector(map(max, maxs, p))
    if mins.x == float('inf'):
        center = Vector((0.0, 0.0, 0.0))
        radius = 5.0
    else:
        center = (mins + maxs) * 0.5
        radius = max((maxs - mins).length * 0.5, 0.5)

    cam_data = bpy.data.cameras.new("PreviewCamera")
    cam_data.type = 'PERSP'
    cam_data.lens = 50.0
    cam = bpy.data.objects.new("PreviewCamera", cam_data)
    scene.collection.objects.link(cam)
    # 3/4 high view: from +X, -Y, above, looking at the bbox centre.
    direction = Vector((1.0, -1.0, 0.75)).normalized()
    # Fit the bounding sphere inside the frame with margin.
    half_fov = math.radians(cam_data.angle) / 2.0
    dist = radius / math.sin(half_fov) * 1.15
    cam.location = center + direction * dist
    cam.rotation_euler = (center - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam_data.clip_start = max(0.01, dist / 1000.0)
    cam_data.clip_end = max(1000.0, dist * 10.0)
    scene.camera = cam
    print(f"render_max: created camera at {tuple(round(v, 2) for v in cam.location)} "
          f"looking at {tuple(round(v, 2) for v in center)} (radius {radius:.2f})")


scene = bpy.context.scene
_ensure_camera(scene)
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
print("render_max: max quality settings applied")
