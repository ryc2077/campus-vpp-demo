# ov-field: 球场与看台 (overview piece)
# 足球场, Blender 中心 (-80, -25, 0), 56 (x) x 30 (y) m:
#   8 条相间条带沿 x 方向, 每条 7 m 宽, 深绿 #46A04E / 浅绿 #57B25E 交替, 厚 0.08 m
#   白色边线 0.15 m 宽围一圈 + 中线 1 条 (贴草皮面, 高 0.02 m)
# 球门: 东西两端各 1 个, 7.32 m 宽, 2.44 m 高, 白色圆管门框 + 浅灰半透明网面
# 看台: 场南侧 (y=-45 附近), 长 30 m, 3 级台阶 (每级 0.4 m 高, 0.8 m 深), 混凝土 #B9B3A8
# 只做球场 + 球门 + 看台: 不做跑道环 (ov-track)、不做草坪花坛 (ov-lawn).
# 材质: 程序化纹理 (Noise, 无贴图)——草皮条带/看台/地面各自分开的噪波:
#   大尺度斑驳 (颜色深浅不均 + 粗糙度变化) + 细颗粒噪波 (Bump 凹凸);
#   白线/门框/球网保持纯色, 只改材质节点, 不动几何和位置.

import bpy
import math
import os
from mathutils import Vector

PIECE = "ov-field"
BASE = os.path.expanduser("~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
PY_DIR = os.path.join(BASE, "assets/blender/overview")
BLEND_PATH = os.path.join(PY_DIR, "ov-field.blend")
GLB_PATH = os.path.join(BASE, "assets/models/ov-field.glb")
PNG_PATH = os.path.join(BASE, "screenshots/blender/ov-field.png")

CX, CY = -80.0, -25.0   # field centre (Blender x, y)
FIELD_LX, FIELD_LY = 56.0, 30.0
TURF_T = 0.08            # turf slab thickness
N_STRIPES = 8
LINE_W = 0.15            # white line width
LINE_H = 0.02            # white lines sit 0.02 m above the turf surface
GOAL_W, GOAL_H = 7.32, 2.44
GOAL_DEPTH = 1.5         # net depth behind the goal line
POST_R = 0.06            # goal post tube radius
STAND_LEN = 30.0
STAND_CY = -45.0         # stand centre y (south of the field)
STEP_H, STEP_D = 0.4, 0.8
N_STEPS = 3


def hex_rgb(h):
    """Hex sRGB -> linear RGB (Blender stores Base Color linear)."""
    h = h.lstrip("#")

    def srgb_to_lin(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (srgb_to_lin(int(h[i:i + 2], 16)) for i in (0, 2, 4))
    return (r, g, b, 1.0)


def make_mat(name, hexcol, rough=0.85, metallic=0.0, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = hex_rgb(hexcol)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        m.blend_method = "BLEND"
    return m


def add_procedural(mat, base_hex, dx, dy, blotch_m, grain_m,
                   color_var, rough_lo, rough_hi, bump_strength):
    """Procedural texture only (no image textures, no geometry change).

    Two Noise branches, both driven by Generated coords through a Mapping
    node scaled per-axis so features stay ~isotropic in metres:
      * blotch noise (features ~blotch_m): mottled brightness via
        Map Range -> MixRGB MULTIPLY into Base Color, and the same Fac
        via Map Range into Roughness (rough_lo..rough_hi).
      * grain noise (features ~grain_m): Fac -> Bump -> BSDF Normal.
    dx, dy are the object footprint in metres the material is used on.
    """
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    base = hex_rgb(base_hex)
    tex = nt.nodes.new("ShaderNodeTexCoord")

    # ---- blotch branch: colour mottle + roughness variation ----
    map_b = nt.nodes.new("ShaderNodeMapping")
    map_b.inputs["Scale"].default_value = (dx / blotch_m, dy / blotch_m, 1.0)
    nt.links.new(tex.outputs["Generated"], map_b.inputs["Vector"])
    noise_b = nt.nodes.new("ShaderNodeTexNoise")
    noise_b.inputs["Scale"].default_value = 1.0
    noise_b.inputs["Detail"].default_value = 2.5
    noise_b.inputs["Roughness"].default_value = 0.7
    nt.links.new(map_b.outputs["Vector"], noise_b.inputs["Vector"])

    mr_col = nt.nodes.new("ShaderNodeMapRange")
    mr_col.inputs["From Min"].default_value = 0.0
    mr_col.inputs["From Max"].default_value = 1.0
    mr_col.inputs["To Min"].default_value = 1.0 - color_var
    mr_col.inputs["To Max"].default_value = 1.0
    nt.links.new(noise_b.outputs["Fac"], mr_col.inputs["Value"])
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MULTIPLY"
    mix.inputs[0].default_value = 1.0
    mix.inputs[1].default_value = base
    nt.links.new(mr_col.outputs["Result"], mix.inputs[2])
    nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])

    mr_rgh = nt.nodes.new("ShaderNodeMapRange")
    mr_rgh.inputs["From Min"].default_value = 0.0
    mr_rgh.inputs["From Max"].default_value = 1.0
    mr_rgh.inputs["To Min"].default_value = rough_lo
    mr_rgh.inputs["To Max"].default_value = rough_hi
    nt.links.new(noise_b.outputs["Fac"], mr_rgh.inputs["Value"])
    nt.links.new(mr_rgh.outputs["Result"], bsdf.inputs["Roughness"])

    # ---- grain branch: fine noise -> bump (surface grain) ----
    map_g = nt.nodes.new("ShaderNodeMapping")
    map_g.inputs["Scale"].default_value = (dx / grain_m, dy / grain_m, 1.0)
    nt.links.new(tex.outputs["Generated"], map_g.inputs["Vector"])
    noise_g = nt.nodes.new("ShaderNodeTexNoise")
    noise_g.inputs["Scale"].default_value = 1.0
    noise_g.inputs["Detail"].default_value = 2.0
    noise_g.inputs["Roughness"].default_value = 0.7
    nt.links.new(map_g.outputs["Vector"], noise_g.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = bump_strength
    bump.inputs["Distance"].default_value = 0.03
    nt.links.new(noise_g.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])


MAT_DARK = make_mat("Turf_Dark_46A04E", "#46A04E", 0.95)
add_procedural(MAT_DARK, "#46A04E", 7.0, 30.0, blotch_m=1.5, grain_m=0.35,
               color_var=0.22, rough_lo=0.80, rough_hi=1.0, bump_strength=0.6)
MAT_LIGHT = make_mat("Turf_Light_57B25E", "#57B25E", 0.95)
add_procedural(MAT_LIGHT, "#57B25E", 7.0, 30.0, blotch_m=1.5, grain_m=0.35,
               color_var=0.22, rough_lo=0.80, rough_hi=1.0, bump_strength=0.6)
MAT_LINE = make_mat("FieldLine_White_FFFFFF", "#FFFFFF", 0.8)
MAT_GOAL = make_mat("GoalFrame_White_FFFFFF", "#FFFFFF", 0.4, metallic=0.1)
MAT_NET = make_mat("GoalNet_Grey_D0D0D0", "#D0D0D0", 0.6, alpha=0.35)
MAT_STAND = make_mat("Stand_Concrete_B9B3A8", "#B9B3A8", 0.95)
add_procedural(MAT_STAND, "#B9B3A8", 30.0, 0.8, blotch_m=1.2, grain_m=0.4,
               color_var=0.20, rough_lo=0.85, rough_hi=1.0, bump_strength=0.5)
MAT_GROUND = make_mat("Ground_Grass_69B45E", "#69B45E", 1.0)
add_procedural(MAT_GROUND, "#69B45E", 170.0, 130.0, blotch_m=3.0, grain_m=0.8,
               color_var=0.25, rough_lo=0.90, rough_hi=1.0, bump_strength=0.5)

# ---- clean scene ----
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

field_objs = []  # objects that go into the .glb


def add_box(name, cx, cy, z0, dx, dy, dz, mat):
    bpy.ops.mesh.primitive_cube_add(location=(cx, cy, z0 + dz / 2.0))
    obj = bpy.context.active_object
    obj.name = name
    obj.dimensions = (dx, dy, dz)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    field_objs.append(obj)
    return obj


def add_cylinder(name, loc, radius, depth, rotation, mat):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=16, radius=radius, depth=depth, location=loc, rotation=rotation)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(mat)
    field_objs.append(obj)
    return obj


# ---- turf: 8 stripes along x, each 7 m wide x 30 m, alternating dark/light ----
stripe_w = FIELD_LX / N_STRIPES
for i in range(N_STRIPES):
    x0 = CX - FIELD_LX / 2.0 + i * stripe_w
    mat = MAT_DARK if i % 2 == 0 else MAT_LIGHT
    add_box("field_stripe_%d" % (i + 1), x0 + stripe_w / 2.0, CY, 0.0,
            stripe_w, FIELD_LY, TURF_T, mat)

# ---- white lines: perimeter + centre line, on top of the turf ----
x0, x1 = CX - FIELD_LX / 2.0, CX + FIELD_LX / 2.0
y0, y1 = CY - FIELD_LY / 2.0, CY + FIELD_LY / 2.0
lz = TURF_T
# north / south touchlines (along x)
add_box("field_line_south", CX, y0, lz, FIELD_LX, LINE_W, LINE_H, MAT_LINE)
add_box("field_line_north", CX, y1, lz, FIELD_LX, LINE_W, LINE_H, MAT_LINE)
# west / east goal lines (along y)
add_box("field_line_west", x0, CY, lz, LINE_W, FIELD_LY, LINE_H, MAT_LINE)
add_box("field_line_east", x1, CY, lz, LINE_W, FIELD_LY, LINE_H, MAT_LINE)
# halfway line (along y, through the centre)
add_box("field_line_centre", CX, CY, lz, LINE_W, FIELD_LY, LINE_H, MAT_LINE)

# ---- goals: one at each end (west x0, east x1), mouth on the goal line ----
# net extends outward (away from the field) by GOAL_DEPTH.
for side, gx, outward in (("west", x0, -1.0), ("east", x1, +1.0)):
    y_a, y_b = CY - GOAL_W / 2.0, CY + GOAL_W / 2.0
    # two upright posts (vertical tubes)
    add_cylinder("goal_%s_post_a" % side, (gx, y_a, GOAL_H / 2.0),
                 POST_R, GOAL_H, (0.0, 0.0, 0.0), MAT_GOAL)
    add_cylinder("goal_%s_post_b" % side, (gx, y_b, GOAL_H / 2.0),
                 POST_R, GOAL_H, (0.0, 0.0, 0.0), MAT_GOAL)
    # crossbar (tube along y at the top)
    add_cylinder("goal_%s_crossbar" % side, (gx, CY, GOAL_H),
                 POST_R, GOAL_W + 2 * POST_R, (math.radians(90), 0.0, 0.0),
                 MAT_GOAL)
    # net: back plane + top plane + two side planes (thin boxes, translucent)
    back_x = gx + outward * GOAL_DEPTH
    add_box("goal_%s_net_back" % side, back_x, CY, 0.0,
            0.02, GOAL_W, GOAL_H, MAT_NET)
    add_box("goal_%s_net_top" % side, gx + outward * GOAL_DEPTH / 2.0, CY,
            GOAL_H - 0.01, GOAL_DEPTH, GOAL_W, 0.02, MAT_NET)
    for sy in (y_a, y_b):
        add_box("goal_%s_net_side_%s" % (side, "a" if sy == y_a else "b"),
                gx + outward * GOAL_DEPTH / 2.0, sy, 0.0,
                GOAL_DEPTH, 0.02, GOAL_H, MAT_NET)

# ---- stand: south side, 30 m long, 3 steps rising away from the field ----
# step 0 (front, nearest the field) is 0.4 m high; each step back adds 0.4 m.
stand_x0 = CX - STAND_LEN / 2.0
front_y = STAND_CY + N_STEPS * STEP_D / 2.0  # north edge of the stand
for i in range(N_STEPS):
    step_cy = front_y - STEP_D / 2.0 - i * STEP_D
    add_box("stand_step_%d" % (i + 1), CX, step_cy, 0.0,
            STAND_LEN, STEP_D, STEP_H * (i + 1), MAT_STAND)

print("field objects:", len(field_objs),
      "stripes:", N_STRIPES, "goals: 2, stand steps:", N_STEPS)

# ---- preview-only ground (NOT exported) ----
bpy.ops.mesh.primitive_plane_add(location=(CX, CY, -0.01))
ground = bpy.context.active_object
ground.name = "Ground_PreviewOnly"
ground.dimensions = (170.0, 130.0, 0.0)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
ground.data.materials.append(MAT_GROUND)

# ---- lighting (SPEC section 2): sun 3.5 from SW, elev ~50 deg ----
target = Vector((CX, -27.0, 0.0))
sun_dir = Vector((-0.64, -0.64, 1.0))  # sun sits SW and up
bpy.ops.object.light_add(type="SUN", location=tuple(target + sun_dir * 80.0))
sun = bpy.context.active_object
sun.name = "Sun_SW"
sun.data.energy = 3.5
sun.data.use_shadow = True
sun.rotation_euler = (target - sun.location).to_track_quat("-Z", "Y").to_euler()

# ---- world: flat light blue (0.65, 0.78, 0.88), strength 1.0 ----
world = bpy.data.worlds.new("World_LightBlue")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.65, 0.78, 0.88, 1.0)
bg.inputs["Strength"].default_value = 1.0

# ---- camera: steep top-down view; field (59 m incl. nets) + stand must fit ----
# offset (-18,-30,+70): ~24 deg off vertical, distance ~78 m; 35 mm lens
# covers ~85 m across the 640x360 frame.
bpy.ops.object.camera_add(location=(CX - 18.0, CY - 30.0, 70.0))
cam = bpy.context.active_object
cam.name = "Cam_Preview"
cam.data.lens = 35.0
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
bpy.context.scene.camera = cam

# ---------- 烘焙程序化纹理为图片 (照抄 dist/di-walls.py 已验证做法) ----------
# glTF 无法导出 Noise 程序化节点: 每种不透明材质选其全部对象,
# Cycles CPU (samples 4) 烘焙 color/rough/normal 三张 1024px 图
# (diffuse 只取 color 通道, 不带光照; margin 16px), 再重建材质为图片纹理节点。
# 立方体/圆柱自带 UV; GoalNet 球网是半透明材质 (alpha 0.35), 不烘焙, 保持原样。
import time
TEX_DIR = os.path.join(PY_DIR, "ov-field_textures")
os.makedirs(TEX_DIR, exist_ok=True)
_bake_scene = bpy.context.scene
_bake_t0 = time.time()


def _ensure_uv(ob):
    me = ob.data
    if me is None or not hasattr(me, "uv_layers") or len(me.uv_layers) > 0:
        return
    me.uv_layers.new(name="UVMap")
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.02)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    print("uv added:", ob.name)


def _pack_uvs(mat_objs):
    """把同材质各对象的 UV 分别缩放到一张 1024 图里的不重叠瓦片 (网格排布,
    瓦片间留 32px 间隙, 容纳两侧各 16px 烘焙 margin)。立方体默认 UV 是每面
    0~1 全图重叠, 不分瓦片时同一纹素会被每个对象反复烘焙, 对象越多越慢
    (128 个缝线对象曾让一遍烘焙超过 1 小时); 分瓦片后每纹素只烘焙一次。
    只改 UV, 不动几何/配色/位置; 导出 GLB 时 UV 随贴图一起走, Godot 采样正确。"""
    n = len(mat_objs)
    cols = int(math.ceil(math.sqrt(n)))
    rows = int(math.ceil(n / cols))
    gap = 32.0 / 1024.0  # 瓦片间隙 (UV 单位)
    su = 1.0 / cols - gap
    sv = 1.0 / rows - gap
    for idx, ob in enumerate(mat_objs):
        u_off = (idx % cols) / cols + gap / 2.0
        v_off = (idx // cols) / rows + gap / 2.0
        uv = ob.data.uv_layers.active
        if uv is None:
            continue
        for luv in uv.data:
            u, v = luv.uv
            luv.uv = (u * su + u_off, v * sv + v_off)
    print("uv packed:", len(mat_objs), "objects into", cols, "x", rows, "tiles")


def _bake_images(mat, mat_objs, color_size=1024):
    nt = mat.node_tree
    imgs = {}
    specs = [("color", 'DIFFUSE', color_size, 'sRGB'),
             ("rough", 'ROUGHNESS', 1024, 'Non-Color'),
             ("normal", 'NORMAL', 1024, 'Non-Color')]
    bpy.ops.object.select_all(action='DESELECT')
    for ob in mat_objs:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = mat_objs[0]
    _bake_scene.render.engine = 'CYCLES'
    _bake_scene.cycles.device = 'CPU'
    _bake_scene.cycles.samples = 4
    bake = _bake_scene.render.bake
    bake.use_selected_to_active = False
    bake.margin = 16
    for key, btype, size, cs in specs:
        img = bpy.data.images.new("%s_%s" % (mat.name, key),
                                  width=size, height=size, alpha=False)
        img.colorspace_settings.name = cs
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = img
        nt.nodes.active = tex
        if btype == 'DIFFUSE':
            bake.use_pass_direct = False
            bake.use_pass_indirect = False
            bake.use_pass_color = True
        elif btype == 'NORMAL':
            bake.normal_space = 'TANGENT'
        bpy.ops.object.bake(type=btype)
        img.filepath_raw = os.path.join(TEX_DIR, "%s_%s.png" % (mat.name, key))
        img.file_format = 'PNG'
        img.save()
        imgs[key] = img
        nt.nodes.remove(tex)
        print("baked:", mat.name, key, img.filepath_raw,
              os.path.getsize(img.filepath_raw))
    _bake_scene.render.engine = 'BLENDER_EEVEE_NEXT'
    return imgs


def _rebuild_with_images(mat, imgs):
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    bsdf.inputs["Roughness"].default_value = 1.0
    bsdf.inputs["Metallic"].default_value = 0.0
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    tex_c = nt.nodes.new("ShaderNodeTexImage")
    tex_c.image = imgs["color"]
    nt.links.new(tex_c.outputs["Color"], bsdf.inputs["Base Color"])
    tex_r = nt.nodes.new("ShaderNodeTexImage")
    tex_r.image = imgs["rough"]
    nt.links.new(tex_r.outputs["Color"], bsdf.inputs["Roughness"])
    tex_n = nt.nodes.new("ShaderNodeTexImage")
    tex_n.image = imgs["normal"]
    nmap = nt.nodes.new("ShaderNodeNormalMap")
    nmap.space = 'TANGENT'
    nt.links.new(tex_n.outputs["Color"], nmap.inputs["Color"])
    nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])


_BAKE_MATS = {MAT_DARK, MAT_LIGHT, MAT_LINE, MAT_GOAL, MAT_STAND}
# GoalNet_Grey_D0D0D0 是半透明网面 (alpha 0.35), 不属于不透明材质, 不烘焙。
_by_mat = {}
for _ob in field_objs:
    _m = _ob.data.materials[0]
    if _m in _BAKE_MATS:
        _by_mat.setdefault(_m, []).append(_ob)
_baked = {}
for _mat, _m_objs in _by_mat.items():
    for _ob in _m_objs:
        _ensure_uv(_ob)
    _pack_uvs(_m_objs)
    _baked[_mat.name] = _bake_images(_mat, _m_objs)
for _mat in _by_mat:
    _rebuild_with_images(_mat, _baked[_mat.name])
print("bake done, materials rebuilt with image textures, elapsed %.1fs"
      % (time.time() - _bake_t0))

# ---- save .blend ----
os.makedirs(PY_DIR, exist_ok=True)
os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
os.makedirs(os.path.dirname(PNG_PATH), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("saved blend:", BLEND_PATH)

# ---- export .glb (field objects only) ----
bpy.ops.object.select_all(action="DESELECT")
for o in field_objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = field_objs[0]
bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format="GLB",
                           use_selection=True, export_apply=True)
print("exported glb:", GLB_PATH, "objects:", len(field_objs))

# ---- read back the .glb to confirm it opens ----
# 回读验证 (di-walls 做法): 对象数一致, 且每种不透明材质的贴图数 >= 3。
# 半透明球网 (GoalNet_Grey_D0D0D0) 不烘焙, 跳过贴图检查。
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB_PATH)
imported = [o for o in bpy.data.objects if o not in before]
print("glb re-import OK, imported objects:", len(imported),
      [o.name for o in imported])
for ob in imported:
    for slot in ob.material_slots:
        m = slot.material
        if m and m.use_nodes:
            # 回读时材质名会带 .001 后缀 (原材质仍在场景中), 比较时先去掉后缀。
            _mbase = m.name.rpartition(".")[0] or m.name
            imgs = [n.image.name for n in m.node_tree.nodes
                    if n.type == 'TEX_IMAGE' and n.image is not None]
            if _mbase == "GoalNet_Grey_D0D0D0":
                print("GLB reimport mat (translucent, not baked):", ob.name,
                      m.name, "images:", imgs)
                continue
            print("GLB reimport mat:", ob.name, m.name, "images:", imgs)
            assert len(imgs) >= 3, "glb material lost baked textures: %s" % m.name
assert len(imported) == len(field_objs), "glb reimport failed: expected %d objects, got %d" % (len(field_objs), len(imported))
bpy.ops.object.select_all(action='DESELECT')
for ob in imported:
    ob.select_set(True)
bpy.ops.object.delete()
print("re-imported copies deleted, scene objects:", len(bpy.context.scene.objects))

# ---- render preview: Eevee, 640x360, 16 samples ----
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100
scene.eevee.taa_render_samples = 16
scene.render.filepath = PNG_PATH
scene.render.image_settings.file_format = "PNG"
# 本地不渲染预览图 (渲染全部走 GitHub Actions); 上面的渲染设置留给 Actions 用。
print("preview render skipped (GitHub Actions renders):", PNG_PATH)

print("DONE ov-field")
