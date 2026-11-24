extends SceneTree
## R2-T37 桌椅腿像素层定位探针（只诊断，不改模型、不改机位）。
## 用法（在 T24 款最小探针工程里跑，xvfb 下原生渲染 llvmpipe）：
##   xvfb-run -a Godot_v4.4-stable_linux.x86_64 --path . -s tools/probe_pixel_legs.gd -- variant=base out=/abs/a.png
## variant: base（T24 同款光照：晴 10:00，太阳 0.95/#fff3d6/-53.3°/-13.5°，
##   天空 #63a9b4，sky/ground energy 0.85/0.65，ambient 0.28，无阴影）/
##   fill（base + R2-T30 两盏室内补光）/ blobs（base + weather_system 的 5 个
##   云影 blob，alpha 0 的透明圆柱，复刻主场景疑似遮挡物）/
##   fillblobs（fill + blobs）/ red（base + leg_metal 临时改亮红 metallic 0，
##   只改内存材质，不落盘不推仓）/ close（单桌近景，T24 光照）/
##   closered（单桌近景 + 亮红腿）。
## shot 由 variant 决定：close* 用近景机位，其余用精确 03 机位
##   （az 1.352/el 0.382/dist 4.96/target (-3,0.9,-0.2)，局部坐标）。
## 输出：PNG + PROBE-PIX 行（腿应落点屏坐标、RGB、左右 12px 邻点 RGB）。
## 退出码恒 0（结论在输出里）；加载失败打印 PROBE-ERROR 并 quit(1)。

const GLB_PATH := "res://assets/models/scenes/classroom.glb"
const DPOSTS := [Vector2(-0.15, -0.25), Vector2(-0.15, 0.25), Vector2(0.20, -0.25), Vector2(0.20, 0.25)]
const CPOSTS := [Vector2(-0.18, -0.15), Vector2(-0.18, 0.15), Vector2(0.14, -0.15), Vector2(0.14, 0.15)]
const SAMPLE_DESKS := ["desk_r1_c1", "desk_r1_c2", "desk_r3_c4", "desk_r5_c2", "desk_r8_c6"]
const SAMPLE_CHAIRS := ["chair_r1_c1", "chair_r3_c4", "chair_r5_c2"]

var _variant := "base"
var _out := "probe_pixel_legs.png"
var _frames := 0
var _capturing := false
var _cam: Camera3D = null
var _glb_root: Node3D = null
var _load_path := ""


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	for a in args:
		var s := String(a)
		if s.begins_with("variant="):
			_variant = s.trim_prefix("variant=")
		elif s.begins_with("out="):
			_out = s.trim_prefix("out=")
	root.size = Vector2(1280, 720)
	# ---- 环境：T24 同款晴 10:00（与 weather_system sunny hour=10 逐项同值）----
	var wenv := WorldEnvironment.new()
	var e := Environment.new()
	e.background_mode = Environment.BG_SKY
	var sky := Sky.new()
	var smat := ProceduralSkyMaterial.new()
	smat.sky_top_color = Color("#63a9b4")
	smat.sky_horizon_color = Color("#63a9b4").lerp(Color.WHITE, 0.16)
	smat.ground_bottom_color = Color("#4a6b38")
	smat.ground_horizon_color = Color("#a9c6e0")
	smat.sky_energy_multiplier = 0.85
	smat.ground_energy_multiplier = 0.65
	sky.sky_material = smat
	e.sky = sky
	e.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	e.ambient_light_energy = 0.28
	e.fog_enabled = true
	e.fog_light_color = Color("#63a9b4")
	e.fog_density = 0.0002
	wenv.environment = e
	root.add_child(wenv)
	var sun := DirectionalLight3D.new()
	sun.light_energy = 0.95
	sun.light_color = Color("#fff3d6")
	sun.rotation_degrees = Vector3(-53.3, -13.5, 0.0)
	sun.shadow_enabled = false
	root.add_child(sun)
	# ---- R2-T30 室内补光（variant fill/fillblobs 才加）----
	if _variant == "fill" or _variant == "fillblobs":
		for dir in [-1.0, 1.0]:
			var sp := SpotLight3D.new()
			sp.position = Vector3(0, 1.8, dir * 0.4)
			sp.rotation = Vector3(0, PI, 0) if dir > 0.0 else Vector3.ZERO
			sp.light_color = Color("#ffe0b3")
			sp.light_energy = 1.5
			sp.spot_angle = 120.0
			sp.spot_attenuation = 1.0
			sp.shadow_enabled = false
			root.add_child(sp)
		print("PROBE: fill spots added (R2-T30)")
	# ---- 云影 blob（variant blobs/fillblobs 才加；weather_system._build_shadows 同款）----
	if _variant == "blobs" or _variant == "fillblobs":
		var centres := [Vector3(-110, 0.15, -55), Vector3(-75, 0.15, -30), Vector3(-40, 0.15, 0), Vector3(-5, 0.15, 30), Vector3(30, 0.15, -55)]
		for i in range(5):
			var b := MeshInstance3D.new()
			var cm := CylinderMesh.new()
			cm.top_radius = 24.0 + i * 6.0
			cm.bottom_radius = 24.0 + i * 6.0
			cm.height = 0.1
			b.mesh = cm
			var m := StandardMaterial3D.new()
			m.albedo_color = Color(0.11, 0.19, 0.25, 0.0)
			m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			b.material_override = m
			b.position = centres[i]
			root.add_child(b)
		print("PROBE: shadow blobs added (alpha 0, 5x)")
	# ---- 加载 classroom.glb ----
	var packed := load(GLB_PATH) as PackedScene
	if packed != null:
		_load_path = "packedscene-imported"
		_glb_root = packed.instantiate() as Node3D
	else:
		print("PROBE note: PackedScene 加载失败，改走 GLTFDocument 运行时直读")
		var doc := GLTFDocument.new()
		var state := GLTFState.new()
		var err := doc.append_from_file(GLB_PATH, state)
		if err != OK:
			print("PROBE-ERROR: GLTFDocument 直读失败 err=%d" % err)
			quit(1)
			return
		_load_path = "gltfdocument-runtime"
		_glb_root = doc.generate_scene(state) as Node3D
	if _glb_root == null:
		print("PROBE-ERROR: classroom.glb 实例化失败")
		quit(1)
		return
	_glb_root.name = "ClassroomGLB"
	root.add_child(_glb_root)
	print("PROBE: classroom.glb loaded via %s, children=%d" % [_load_path, _glb_root.get_child_count()])
	# ---- A/B：亮红腿（只改内存材质）----
	if _variant == "red" or _variant == "closered":
		var seen := {}
		var n := 0
		for mi in _glb_root.get_children():
			if not (mi is MeshInstance3D):
				continue
			var mesh := (mi as MeshInstance3D).mesh as ArrayMesh
			if mesh == null or mesh.get_surface_count() < 2:
				continue
			var mat := mesh.surface_get_material(1) as StandardMaterial3D
			if mat == null:
				continue
			if seen.has(mat.get_instance_id()):
				continue
			seen[mat.get_instance_id()] = true
			mat.albedo_texture = null
			mat.metallic_roughness_texture = null
			mat.normal_texture = null
			mat.albedo_color = Color(1.0, 0.05, 0.05)
			mat.metallic = 0.0
			mat.roughness = 0.55
			n += 1
		print("PROBE: red-leg A/B applied, unique leg materials mutated=%d" % n)
	# ---- 相机 ----
	_cam = Camera3D.new()
	_cam.fov = 55.0
	_cam.near = 0.1
	_cam.far = 2000.0
	_cam.current = true
	root.add_child(_cam)
	if _variant == "close" or _variant == "closered":
		# 单桌近景：desk_r5_c2（0.82,0,1.8，离 03 机位最近的桌），相机 1.7m 外
		var tgt := Vector3(0.82, 0.35, 1.8)
		_cam.position = Vector3(0.82 + 0.9, 1.0, 1.8 + 1.1)
		_cam.look_at_from_position(_cam.position, tgt, Vector3.UP)
		print("PROBE: close-up cam at %s -> %s" % [str(_cam.position), str(tgt)])
	else:
		var target := Vector3(-3, 0.9, -0.2)
		var az := 1.352
		var el := 0.382
		var dist := 4.96
		_cam.position = Vector3(
			target.x + dist * cos(el) * sin(az),
			target.y + dist * sin(el),
			target.z + dist * cos(el) * cos(az))
		_cam.look_at_from_position(_cam.position, target, Vector3.UP)
		print("PROBE: 03 cam at %s -> %s" % [str(_cam.position), str(target)])
	print("PROBE: variant=%s out=%s" % [_variant, _out])


func _lum(c: Color) -> float:
	return 0.299 * c.r + 0.587 * c.g + 0.114 * c.b


func _process(_delta: float) -> bool:
	_frames += 1
	if _frames % 5 == 0:
		print("PROBE-FRAME %d" % _frames)
	if _frames < 12 or _capturing:
		return false
	_capturing = true
	# 注意：不在 _process 里 await（挂起后函数返回的 FunctionState 转 bool
	# 为真，主循环会当作退出信号、静默退出，见 R2-T37 实测）。改用帧计数：
	# 第 12 帧直接取上一帧已渲染好的根视口纹理同步截图。
	var tex := root.get_texture()
	if tex == null:
		print("PROBE-ERROR: root texture is null")
		quit(1)
		return true
	var img := tex.get_image()
	if img == null:
		print("PROBE-ERROR: get_image returned null")
		quit(1)
		return true
	print("PROBE: captured size=%s viewport=%s" % [str(img.get_size()), str(root.size)])
	var err := img.save_png(_out)
	if err != OK:
		print("PROBE-ERROR: save_png err=%d" % err)
		quit(1)
		return true
	print("PROBE-SAVED: " + _out)
	# ---- 取景校验点（与 Python 投影模型交叉核对）----
	for label in ["blackboard", "room_centre", "desk_r5_c2_top"]:
		var wp := Vector3(-4.79, 1.7, 0.0)
		if label == "room_centre":
			wp = Vector3(0, 0.9, 0)
		elif label == "desk_r5_c2_top":
			wp = Vector3(0.82, 0.7, 1.8)
		var sp := _cam.unproject_position(wp)
		print("PROBE-ANCHOR %s world=%s screen=(%.1f,%.1f)" % [label, str(wp), sp.x, sp.y])
	# ---- 腿应落点逐像素取样 ----
	for dname in SAMPLE_DESKS:
		var node := _glb_root.find_child(dname, true, false) as Node3D
		if node == null:
			print("PROBE-PIX %s NOT-FOUND" % dname)
			continue
		for pi in range(DPOSTS.size()):
			var off: Vector2 = DPOSTS[pi]
			_sample_post(img, dname, pi, node.position + Vector3(off.x, 0, off.y), 0.35)
	for cname in SAMPLE_CHAIRS:
		var node2 := _glb_root.find_child(cname, true, false) as Node3D
		if node2 == null:
			print("PROBE-PIX %s NOT-FOUND" % cname)
			continue
		for pi in range(CPOSTS.size()):
			var off2: Vector2 = CPOSTS[pi]
			_sample_post(img, cname, pi, node2.position + Vector3(off2.x, 0, off2.y), 0.35)
	print("PROBE-DONE variant=%s" % _variant)
	quit(0)
	return true


func _sample_post(img: Image, node_name: String, post_idx: int, base: Vector3, y: float) -> void:
	var wp := Vector3(base.x, y, base.z)
	var sp := _cam.unproject_position(wp)
	var xi := int(round(sp.x))
	var yi := int(round(sp.y))
	var sz := img.get_size()
	if xi < 0 or yi < 0 or xi >= sz.x or yi >= sz.y:
		print("PROBE-PIX %s post%d y=%.2f screen=(%.1f,%.1f) OUT-OF-FRAME" % [node_name, post_idx, y, sp.x, sp.y])
		return
	var c := img.get_pixel(xi, yi)
	var cl := img.get_pixel(maxi(xi - 12, 0), yi)
	var cr := img.get_pixel(mini(xi + 12, sz.x - 1), yi)
	print("PROBE-PIX %s post%d y=%.2f screen=(%d,%d) legRGB=(%d,%d,%d) L12=(%d,%d,%d) R12=(%d,%d,%d) legLum=%.0f" % [
		node_name, post_idx, y, xi, yi,
		int(c.r * 255), int(c.g * 255), int(c.b * 255),
		int(cl.r * 255), int(cl.g * 255), int(cl.b * 255),
		int(cr.r * 255), int(cr.g * 255), int(cr.b * 255),
		_lum(c) * 255.0])
