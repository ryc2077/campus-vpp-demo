# ov-track v3: 操场跑道返工 R2-T1 收界 (overview piece)
# 椭圆跑道环, Blender 中心 (-62, -25, 0):
#   外椭圆 rx=28, ry=40; 内椭圆 rx=20, ry=32; 环宽 8 m; 跑道红 #B8543F; 厚 0.1 m
# v2 -> v3 改动 (只改位置/尺寸, 不改配色/纹理/做法):
#   根因: v1/v2 按 SPEC §4 / campus.json playground (rx40 rz28) 建成长轴
#   东西向, 但鸟瞰图第一依据是长轴大致南北向; 且中心 x=-80 时西缘 -120.3,
#   超出环校路西段内缘路缘石 (-90.85) 达 29.45 m, 建到校园外面去了。
#   修正: 长短轴对调 (rx28/ry40, 长轴南北向, 与鸟瞰图一致); 中心东移
#   18 m 至 x=-62, 西缘 (含路缘) -90.3, 距环校路西段内缘路缘石 -90.85
#   净空 0.55 m; 东缘 -33.7, 北端 y=15、南端 y=-65, 不压教学楼 (bldA
#   y>=22.5、gym y>=52) 与环校路 (北 y<=76、南 y>=-76)。起跑线改到东直道,
#   弯道标记改到南北两端弯道中点, 磨损弯道判据由 |cos a| 改为 |sin a|。
# v2 新增 (保留):
#   (1) 跑道面塑胶颗粒纹理: Noise 细颗粒 -> Bump;
#       磨损深浅: 顶点色属性 "wear" (0.76..1.0 乘子), 弯道 (东西两端)
#       磨损重、直道 (南北两边) 磨损轻; glTF 会把 COLOR_0 乘进基础红,
#       故 Base Color / Roughness 保持纯色值 (连线会被导出器丢弃).
#   (2) 跑道线: 保留 v1 的 3 条分道线 + 内外边缘线; 新增起跑线
#       (南直道横贯 4 条跑道) 与弯道分道标记 (东西弯道中点每道一条径向短线).
#   (3) 0.3 m 混凝土路缘: 内外圈各一条, 高 0.15 m, 小倒角, 混凝土 Noise 纹.
# 只做跑道环 + 线 + 路缘: 不做场内球场 (ov-field)、不做看台 (ov-field)、
# 不做草坪 (ov-lawn). 圈内绿地仅预览用、不导出.
# 本地不渲染 (渲染走 GitHub Actions): 本脚本只建模 + 存 .blend + 导出 .glb + 回读确认.

import bpy
import math
import os
from mathutils import Vector

PIECE = "ov-track"
BASE = os.path.expanduser("~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
PY_DIR = os.path.join(BASE, "assets/blender/overview")
BLEND_PATH = os.path.join(PY_DIR, "ov-track.blend")
GLB_PATH = os.path.join(BASE, "assets/models/ov-track.glb")

CX, CY = -62.0, -25.0   # track centre (Blender x, y) — v3: east 18 m, long axis N-S
RX_OUT, RY_OUT = 28.0, 40.0
RX_IN, RY_IN = 20.0, 32.0
TRACK_Z0, TRACK_Z1 = 0.0, 0.1
LINE_W = 0.15           # lane-line width
LINE_H = 0.02           # lane lines sit 0.02 m above the track surface
NSEG = 128
CURB_W = 0.3            # concrete curb width
CURB_H = 0.15           # curb height above ground


def hex_lin(h):
    """Hex sRGB -> linear RGB (Blender stores Base Color linear)."""
    h = h.lstrip("#")

    def srgb_to_lin(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    return tuple(srgb_to_lin(int(h[i:i + 2], 16)) for i in (0, 2, 4))


def make_mat(name, hexcol, rough=0.85, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*hex_lin(hexcol), 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    return m


def add_noise_bump(mat, scale, bump_strength):
    """Fine granule: Noise -> Bump only. Roughness/Base Color stay plain
    values on purpose: glTF export drops any socket driven by a node link,
    so linking them would lose the red base colour / roughness in the .glb.
    Bump is a Blender-render effect; in the .glb the granule survives only
    as the baked-in look of the plain values + wear vertex colours."""
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 2.0
    noise.inputs["Roughness"].default_value = 0.7
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = bump_strength
    bump.inputs["Distance"].default_value = 0.02
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return noise


# ---- materials ----
# NOTE on glTF: Base Color / Roughness must stay plain socket values, or the
# exporter drops them (defaults to white / 1.0). The one supported exception
# is the exporter's "factor x colour attribute" pattern, which is exactly
# what the wear uses: Base Color <- MixRGB MULTIPLY (Fac 1) of constant red
# x Attribute "wear". The exporter then writes BOTH baseColorFactor = red
# AND the wear attribute as COLOR_0, so Godot multiplies bends darker.
# Wear values are a 0.76..1.0 multiplier (bends ~0.76, straights ~1.0).
MAT_TRACK = make_mat("Track_Red_B8543F", "#B8543F", 0.88)
add_noise_bump(MAT_TRACK, scale=120.0, bump_strength=0.25)
_nt = MAT_TRACK.node_tree
_bsdf = _nt.nodes["Principled BSDF"]
_wear_mix = _nt.nodes.new("ShaderNodeMix")  # NOT ShaderNodeMixRGB: the
_wear_mix.data_type = "RGBA"                  # exporter only recognises the
_wear_mix.blend_type = "MULTIPLY"             # new Mix node (Factor/A/B).
_wear_mix.inputs["Factor"].default_value = 1.0
_wear_mix.inputs["A"].default_value = (*hex_lin("#B8543F"), 1.0)  # A: red
_wear_attr = _nt.nodes.new("ShaderNodeAttribute")
_wear_attr.attribute_name = "wear"
_nt.links.new(_wear_attr.outputs["Color"], _wear_mix.inputs["B"])  # B: wear
_nt.links.new(_wear_mix.outputs[0], _bsdf.inputs["Base Color"])
MAT_LINE = make_mat("LaneLine_White_FFFFFF", "#FFFFFF", 0.8)
MAT_CURB = make_mat("Curb_Concrete_B9B3A8", "#B9B3A8", 0.95)
add_noise_bump(MAT_CURB, scale=60.0, bump_strength=0.2)
MAT_GROUND = make_mat("Ground_Grass_69B45E", "#69B45E", 1.0)

# ---- clean scene ----
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

track_objs = []  # objects that go into the .glb


def ellipse_ring(name, rx_out, ry_out, rx_in, ry_in, z0, z1, mat):
    """Flat elliptical annulus solid: top/bottom ring faces + outer/inner walls."""
    n = NSEG
    verts = []
    for i in range(n):
        a = 2.0 * math.pi * i / n
        ca, sa = math.cos(a), math.sin(a)
        verts.append((CX + rx_out * ca, CY + ry_out * sa, z1))  # outer top
        verts.append((CX + rx_in * ca, CY + ry_in * sa, z1))   # inner top
        verts.append((CX + rx_out * ca, CY + ry_out * sa, z0))  # outer bottom
        verts.append((CX + rx_in * ca, CY + ry_in * sa, z0))   # inner bottom
    faces = []
    for i in range(n):
        j = (i + 1) % n
        ot_i, it_i, ob_i, ib_i = 4 * i, 4 * i + 1, 4 * i + 2, 4 * i + 3
        ot_j, it_j, ob_j, ib_j = 4 * j, 4 * j + 1, 4 * j + 2, 4 * j + 3
        faces.append((ot_i, ot_j, it_j, it_i))   # top
        faces.append((ob_i, ib_i, ib_j, ob_j))   # bottom
        faces.append((ot_i, ob_i, ob_j, ot_j))   # outer wall
        faces.append((it_i, it_j, ib_j, ib_i))   # inner wall
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    track_objs.append(obj)
    return obj


def add_wear(obj):
    """Per-vertex wear multiplier 0.76..1.0: bends (N/S ends, |sin a|~1) wear
    heavy (darker, ~0.76), straights (E/W, |sin a|~0) stay ~1.0, plus small
    deterministic jitter. glTF multiplies COLOR_0 into the red base colour."""
    mesh = obj.data
    col = mesh.color_attributes.new(name="wear", type="FLOAT_COLOR",
                                    domain="POINT")
    # Make it the active/render colour: the glTF exporter only puts the
    # render colour in COLOR_0 (otherwise it fakes an all-white COLOR_0
    # and pushes the real attribute to COLOR_1, which Godot ignores).
    idx = mesh.color_attributes.find("wear")
    mesh.color_attributes.active_color_index = idx
    mesh.color_attributes.render_color_index = idx
    for i, v in enumerate(mesh.vertices):
        seg = i // 4
        a = 2.0 * math.pi * seg / NSEG
        bend = abs(math.sin(a)) ** 1.5
        jitter = ((math.sin(seg * 12.9898) * 43758.5453) % 1.0 - 0.5) * 0.04
        w = max(0.76, min(1.0, 1.0 - 0.22 * bend + jitter))
        col.data[i].color = (w, w, w, 1.0)
    return col


def add_box(name, dims, loc, mat, rot_z=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.active_object
    o.name = name
    o.dimensions = dims
    if rot_z:
        o.rotation_euler[2] = rot_z
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    track_objs.append(o)
    return o


# ---- track ring: red, 0.1 m thick, with granule + wear ----
ring = ellipse_ring("track_ring", RX_OUT, RY_OUT, RX_IN, RY_IN,
                    TRACK_Z0, TRACK_Z1, MAT_TRACK)
add_wear(ring)

# ---- 3 lane divider lines, evenly spaced (4 lanes of 2 m each) ----
for k, t in enumerate((0.25, 0.5, 0.75), start=1):
    rx = RX_IN + (RX_OUT - RX_IN) * t
    ry = RY_IN + (RY_OUT - RY_IN) * t
    ellipse_ring("track_lane_line_%d" % k,
                 rx + LINE_W / 2, ry + LINE_W / 2,
                 rx - LINE_W / 2, ry - LINE_W / 2,
                 TRACK_Z1, TRACK_Z1 + LINE_H, MAT_LINE)

# ---- edge lines: outer + inner ----
ellipse_ring("track_edge_line_outer",
             RX_OUT + LINE_W / 2, RY_OUT + LINE_W / 2,
             RX_OUT - LINE_W / 2, RY_OUT - LINE_W / 2,
             TRACK_Z1, TRACK_Z1 + LINE_H, MAT_LINE)
ellipse_ring("track_edge_line_inner",
             RX_IN + LINE_W / 2, RY_IN + LINE_W / 2,
             RX_IN - LINE_W / 2, RY_IN - LINE_W / 2,
             TRACK_Z1, TRACK_Z1 + LINE_H, MAT_LINE)

# ---- start line: east straight, across all 4 lanes ----
# east straight spans x = CX+20 .. CX+28 (centre -38); bar 0.15 m wide in y.
add_box("track_start_line", (RX_OUT - RX_IN, 0.15, LINE_H),
        (CX + (RX_OUT + RX_IN) / 2.0, CY, TRACK_Z1 + LINE_H / 2.0), MAT_LINE)

# ---- bend lane marks: radial ticks at N and S bend midpoints, one per lane ----
# lane centres (ry): 33, 35, 37, 39; tick 1.0 m radial y 0.12 m tangential.
for side, sy in (("N", 1), ("S", -1)):
    for li, rc in enumerate((33.0, 35.0, 37.0, 39.0), start=1):
        add_box("track_bend_mark_%s%d" % (side, li),
                (0.12, 1.0, LINE_H),
                (CX, CY + sy * rc, TRACK_Z1 + LINE_H / 2.0), MAT_LINE)

# ---- concrete curbs 0.3 m wide, inner + outer, with small bevel ----
curb_out = ellipse_ring("track_curb_outer",
                        RX_OUT + CURB_W, RY_OUT + CURB_W, RX_OUT, RY_OUT,
                        0.0, CURB_H, MAT_CURB)
curb_in = ellipse_ring("track_curb_inner",
                       RX_IN, RY_IN, RX_IN - CURB_W, RY_IN - CURB_W,
                       0.0, CURB_H, MAT_CURB)
for curb in (curb_out, curb_in):
    bev = curb.modifiers.new("CurbBevel", "BEVEL")
    bev.width = 0.03
    bev.segments = 2

print("track objects:", len(track_objs),
      "ring outer rx/ry:", RX_OUT, RY_OUT, "inner rx/ry:", RX_IN, RY_IN)

# ---- preview-only ground (NOT exported) ----
bpy.ops.mesh.primitive_plane_add(location=(CX, CY, -0.01))
ground = bpy.context.active_object
ground.name = "Ground_PreviewOnly"
ground.dimensions = (170.0, 130.0, 0.0)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
ground.data.materials.append(MAT_GROUND)

# ---- lighting (SPEC section 2): sun 3.5 from SW, elev ~50 deg ----
target = Vector((CX, CY, 0.0))
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

# ---- camera (for later GitHub Actions render; NOT rendered locally) ----
bpy.ops.object.camera_add(location=(CX - 30.0, CY - 30.0, 120.0))
cam = bpy.context.active_object
cam.name = "Cam_Preview"
cam.data.lens = 35.0
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
bpy.context.scene.camera = cam

# ---------- 烘焙程序化纹理为图片 (照抄 dist/di-walls.py 已验证做法) ----------
# glTF 无法导出 Noise 程序化节点: 每种不透明材质选其全部对象,
# Cycles CPU (samples 4) 烘焙 color/rough/normal 三张 1024px 图
# (diffuse 只取 color 通道, 不带光照; margin 16px), 再重建材质为图片纹理节点。
# from_pydata 的椭圆环网格没有 UV, 先 smart_project 补 UV 再烘焙。
# 跑道 wear 顶点色 (Mix MULTIPLY 进 Base Color) 会随 DIFFUSE 一起烘进 color 贴图。
import time
TEX_DIR = os.path.join(PY_DIR, "ov-track_textures")
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


_by_mat = {}
for _ob in track_objs:
    _by_mat.setdefault(_ob.data.materials[0], []).append(_ob)
_baked = {}
for _mat, _m_objs in _by_mat.items():
    for _ob in _m_objs:
        _ensure_uv(_ob)
    _pack_uvs(_m_objs)
    _baked[_mat.name] = _bake_images(_mat, _m_objs)
for _mat in _by_mat:
    _rebuild_with_images(_mat, _baked[_mat.name])
# 跑道磨损 (wear 顶点色) 已烘进 color 贴图, 删掉顶点色属性,
# 避免 glTF 导出 COLOR_0 后 Godot 里二次乘暗。
_wear_attr = ring.data.color_attributes.get("wear")
if _wear_attr is not None:
    ring.data.color_attributes.remove(_wear_attr)
    print("wear color attribute removed (baked into texture)")
print("bake done, materials rebuilt with image textures, elapsed %.1fs"
      % (time.time() - _bake_t0))

# R2-T9b PBR hard fix (2026-11-25): baked track map was near-flat (28KB
# color over a 400 m ring). Re-link real CC0 photo texture (asphalt_01
# tinted to SPEC track red #B8543F) + world-scale UVs after the bake step,
# before save/export. Idempotent; see _pbr_apply.py in this dir.
_pbr_hook = os.path.join(os.path.dirname(BLEND_PATH), "_pbr_apply.py")
if os.path.exists(_pbr_hook):
    _pbr_g = {"__name__": "_pbr_apply", "__file__": _pbr_hook}
    exec(compile(open(_pbr_hook).read(), _pbr_hook, "exec"), _pbr_g)
    _pbr_g["apply_pbr"](os.path.splitext(os.path.basename(BLEND_PATH))[0])

# R2-T14b path fix-up (same as ov-road-main/walk.py): _pbr_apply._load()
# may store a wrong-base "//" path when run from a fresh session; resolve
# against the .blend directory / CWD and rewrite before save. Idempotent.
for _im in bpy.data.images:
    _fp = _im.filepath
    if not _fp.startswith("//"):
        continue
    _rel = _fp[2:]
    _abs = None
    for _base in (PY_DIR, os.getcwd()):
        _cand = os.path.join(_base, _rel)
        if os.path.exists(_cand):
            _abs = os.path.normpath(_cand)
            break
    if _abs is None:
        print("PBR path fix: file not found, keep:", _im.name, _fp)
        continue
    _new = "//" + os.path.relpath(_abs, PY_DIR)
    if _new != _fp:
        print("PBR path fix:", _im.name, _fp, "->", _new)
        _im.filepath = _new

# ---- save .blend ----
os.makedirs(PY_DIR, exist_ok=True)
os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("saved blend:", BLEND_PATH)

# ---- export .glb (track objects only) ----
bpy.ops.object.select_all(action="DESELECT")
for o in track_objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = track_objs[0]
bpy.ops.export_scene.gltf(filepath=GLB_PATH, export_format="GLB",
                           use_selection=True, export_apply=True)
print("exported glb:", GLB_PATH, "objects:", len(track_objs))

# ---- read back the .glb to confirm it opens ----
# 回读验证 (di-walls 做法): 对象数一致, 且每种材质的贴图数 >= 3 (烘焙贴图齐全)。
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB_PATH)
imported = [o for o in bpy.data.objects if o not in before]
print("glb re-import OK, imported objects:", len(imported),
      [o.name for o in imported])
for ob in imported:
    for slot in ob.material_slots:
        m = slot.material
        if m and m.use_nodes:
            imgs = [n.image.name for n in m.node_tree.nodes
                    if n.type == 'TEX_IMAGE' and n.image is not None]
            print("GLB reimport mat:", ob.name, m.name, "images:", imgs)
            assert len(imgs) >= 3, "glb material lost baked textures: %s" % m.name
assert len(imported) == len(track_objs), "glb reimport failed: expected %d objects, got %d" % (len(track_objs), len(imported))
bpy.ops.object.select_all(action='DESELECT')
for ob in imported:
    ob.select_set(True)
bpy.ops.object.delete()
print("re-imported copies deleted, scene objects:", len(bpy.context.scene.objects))

print("DONE ov-track")
