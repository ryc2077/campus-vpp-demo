# Max-quality Eevee render settings (Actions only; never render locally).
# Usage: blender -b file.blend -E BLENDER_EEVEE_NEXT --python tools/render_max.py -o out/name_ -f 1
# Only touches render settings; scene content, lights, world and camera are left as built.
import bpy


def _set(obj, name, value):
    try:
        setattr(obj, name, value)
    except Exception as e:
        print(f"render_max: skip {name}: {e}")


scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.film_transparent = False

eevee = scene.eevee
_set(eevee, 'taa_render_samples', 256)
_set(eevee, 'taa_reprojection', True)
_set(eevee, 'use_bloom', True)
_set(eevee, 'bloom_intensity', 0.05)
_set(eevee, 'use_ssr', True)
_set(eevee, 'use_ssr_refraction', True)
_set(eevee, 'use_gtao', True)
_set(eevee, 'gtao_distance', 0.5)
_set(eevee, 'use_shadows', True)
_set(eevee, 'shadow_pool_size', 4096)
_set(eevee, 'use_soft_shadows', True)
print("render_max: max quality settings applied")
