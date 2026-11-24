class_name ClassroomInterior
extends Node3D
## 教室內景（模型一 · 一号教学楼）：实测 7.26m × 9.68m，约 70.3㎡，层高 3.5m。
## 南墙留 3m 剖切口（相机经此飞入）；黑板在北墙；2 台 5 匹空调挂北墙两侧；
## 课桌椅 6 排；墙面温度计；冷气/热浪用半透明气流板表示。
## （GlbLoader 用 preload：见 campus_builder.gd 注释。）
const GlbLoader = preload("res://scripts/glb_loader.gd")

var ac_louvers: Array[MeshInstance3D] = []
var ac_leds: Array[MeshInstance3D] = []
var thermo_fill: MeshInstance3D
var cool_fx: MeshInstance3D
var warm_fx: MeshInstance3D

const W := 9.68
const D := 7.26
const H := 3.5

func _ready() -> void:
	_build()

func _mat(c: Color, rough: float = 0.9) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	m.roughness = rough
	return m

func _box(pos: Vector3, size: Vector3, mat: Material) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = size
	mi.mesh = bm
	mi.position = pos
	mi.material_override = mat
	add_child(mi)
	return mi

func _build() -> void:
	# 教室 GLB（局部坐标，房间中心原点）优先；加载失败回退程序化并警告
	var inst := GlbLoader.load_glb(GlbLoader.SCENES["classroom"])
	if inst != null:
		inst.name = "ClassroomGLB"
		add_child(inst)
		_add_fill_light()
		return
	_build_procedural()
	_add_fill_light()

# R2-T30 室内补光：两盏暖色聚光灯，水平对打南/北墙（BLENDER_MODELS.md §30）。
# 只照室内：SpotLight3D 默认 spot_range=5m，灯在房间中心、锥角 120°，
# 锥体基本不出南/北墙；且灯挂在 ClassroomInterior 下，内景在总览等场景
# visible=false 时灯不渲染，室外灯光/草地不受影响（T7 五档 SPEC 不动）。
# 参数是探针实测定案（Omni 会把已达标的西墙一起抬亮，不可用；见 §30）：
# 位置 (0, 1.8, ±0.4)、朝向水平向外（沿 ±z）、色 #ffe0b3、能量 1.5、
# 锥角 120°、衰减 1.0、无阴影。朝向用 rotation 定（Spot 默认沿 -z 出光，
# 向南一盏转 180°），不用 look_at（内景在主场景里有全局位移，look_at
# 的全局目标点在局部坐标下会指错方向）。
const FILL_COLOR := Color("#ffe0b3")
const FILL_ENERGY := 1.5
const FILL_ANGLE := 120.0
const FILL_HEIGHT := 1.8
const FILL_ZOFF := 0.4

func _add_fill_light() -> void:
	for dir in [-1.0, 1.0]:
		var sp := SpotLight3D.new()
		sp.name = "FillSpotNorth" if dir < 0.0 else "FillSpotSouth"
		sp.position = Vector3(0, FILL_HEIGHT, dir * FILL_ZOFF)
		sp.rotation = Vector3(0, PI, 0) if dir > 0.0 else Vector3.ZERO
		sp.light_color = FILL_COLOR
		sp.light_energy = FILL_ENERGY
		sp.spot_angle = FILL_ANGLE
		sp.spot_attenuation = 1.0
		sp.shadow_enabled = false
		add_child(sp)

func _build_procedural() -> void:
	# 地面 / 天花
	_box(Vector3(0, 0.05, 0), Vector3(W, 0.1, D), _mat(Color("#cbb894")))
	_box(Vector3(0, H + 0.05, 0), Vector3(W, 0.1, D), _mat(Color("#f5f2ea")))
	# 北墙（黑板墙，-z）与东、西墙
	_box(Vector3(0, H / 2, -D / 2), Vector3(W, H, 0.15), _mat(Color("#f3ede0")))
	_box(Vector3(-W / 2, H / 2, 0), Vector3(0.15, H, D), _mat(Color("#f3ede0")))
	_box(Vector3(W / 2, H / 2, 0), Vector3(0.15, H, D), _mat(Color("#f3ede0")))
	# 南墙（+z）：左右两段 + 门楣，中间留 3m 剖切口
	var seg_w := (W - 3.0) / 2.0
	_box(Vector3(-(1.5 + seg_w / 2.0), H / 2, D / 2), Vector3(seg_w, H, 0.15), _mat(Color("#f3ede0")))
	_box(Vector3(1.5 + seg_w / 2.0, H / 2, D / 2), Vector3(seg_w, H, 0.15), _mat(Color("#f3ede0")))
	_box(Vector3(0, H - 0.4, D / 2), Vector3(3.0, 0.8, 0.15), _mat(Color("#f3ede0")))
	# 黑板（北墙）
	_box(Vector3(0, 1.7, -D / 2 + 0.12), Vector3(4.6, 1.3, 0.08), _mat(Color("#2e5d43"), 0.6))
	# 讲台
	_box(Vector3(0, 0.5, -D / 2 + 0.9), Vector3(2.0, 1.0, 0.7), _mat(Color("#8a6f4d")))
	# 课桌椅：6 排 × 4 列，朝北
	var desk_mat := _mat(Color("#a9805a"))
	var chair_mat := _mat(Color("#5b7186"))
	var r := 0
	while r < 6:
		var c := 0
		while c < 4:
			var x := -3.3 + c * 2.2
			var z := -1.6 + r * 1.05
			_box(Vector3(x, 0.45, z), Vector3(1.1, 0.08, 0.55), desk_mat)
			_box(Vector3(x - 0.45, 0.25, z), Vector3(0.06, 0.5, 0.5), desk_mat)
			_box(Vector3(x + 0.45, 0.25, z), Vector3(0.06, 0.5, 0.5), desk_mat)
			_box(Vector3(x, 0.4, z + 0.55), Vector3(0.95, 0.07, 0.45), chair_mat)
			_box(Vector3(x, 0.2, z + 0.55), Vector3(0.08, 0.4, 0.4), chair_mat)
			c += 1
		r += 1
	# 2 台空调（北墙两侧，美的 KFR-120LW 柜机示意为壁挂分体）
	var ac_x := [-3.6, 3.6]
	for ax in ac_x:
		_box(Vector3(ax, 2.9, -D / 2 + 0.25), Vector3(1.5, 0.5, 0.35), _mat(Color("#eef2f5"), 0.4))
		var louver := _box(Vector3(ax, 2.68, -D / 2 + 0.42), Vector3(1.3, 0.08, 0.06), _mat(Color("#b8c4ce"), 0.4))
		ac_louvers.append(louver)
		var led_mat := StandardMaterial3D.new()
		led_mat.albedo_color = Color("#888888")
		led_mat.emission_enabled = true
		led_mat.emission = Color("#38f27a")
		led_mat.emission_energy_multiplier = 0.4
		var led := _box(Vector3(ax + 0.55, 2.9, -D / 2 + 0.44), Vector3(0.12, 0.12, 0.05), led_mat)
		ac_leds.append(led)
	# 墙面温度计（东墙）
	_box(Vector3(W / 2 - 0.12, 1.9, 0.5), Vector3(0.06, 1.1, 0.35), _mat(Color("#e8e2d4")))
	var fill_mat := StandardMaterial3D.new()
	fill_mat.albedo_color = Color("#2fbf71")
	fill_mat.emission_enabled = true
	fill_mat.emission = Color("#2fbf71")
	fill_mat.emission_energy_multiplier = 0.5
	thermo_fill = _box(Vector3(W / 2 - 0.12, 1.55, 0.5), Vector3(0.07, 0.5, 0.2), fill_mat)
	# 冷气 / 热浪气流板（半透明，开关由 main 控制显隐）
	var cool_mat := StandardMaterial3D.new()
	cool_mat.albedo_color = Color(0.2, 0.6, 1.0, 0.18)
	cool_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	cool_fx = _box(Vector3(0, 1.9, -1.2), Vector3(8.0, 2.2, 2.4), cool_mat)
	cool_fx.visible = false
	var warm_mat := StandardMaterial3D.new()
	warm_mat.albedo_color = Color(1.0, 0.45, 0.2, 0.15)
	warm_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	warm_fx = _box(Vector3(0, 1.9, 0.5), Vector3(8.0, 2.2, 2.4), warm_mat)
	warm_fx.visible = false
	# 窗户（东、西墙各 2 扇亮窗）
	var win_mat := StandardMaterial3D.new()
	win_mat.albedo_color = Color("#bcdcf5")
	win_mat.emission_enabled = true
	win_mat.emission = Color("#bcdcf5")
	win_mat.emission_energy_multiplier = 0.5
	for wx in [-W / 2 + 0.08, W / 2 - 0.08]:
		for wz in [-1.8, 1.8]:
			_box(Vector3(wx, 2.0, wz), Vector3(0.06, 1.5, 1.4), win_mat)

func set_ac(on: bool, temp_c: float, t: float) -> void:
	for lv in ac_louvers:
		lv.rotation.x = (0.55 + 0.25 * sin(t * 3.0)) if on else 0.05
	for led in ac_leds:
		var m: StandardMaterial3D = led.material_override
		m.emission_energy_multiplier = 1.6 if on else 0.2
		m.albedo_color = Color("#38f27a") if on else Color("#888888")
	if thermo_fill != null:
		var frac := clampf((temp_c - 15.0) / 22.0, 0.04, 1.0)
		thermo_fill.scale.y = frac
		thermo_fill.position.y = 1.35 + 0.55 * frac
		var m2: StandardMaterial3D = thermo_fill.material_override
		var col := Color("#3b82c4") if temp_c < 24.0 else (Color("#e2574c") if temp_c > 28.0 else Color("#2fbf71"))
		m2.albedo_color = col
		m2.emission = col
	# GLB 模式下程序化气流板不存在（_build 已整体换成 GLB），判空避免报错
	if cool_fx != null:
		cool_fx.visible = on
	if warm_fx != null:
		warm_fx.visible = (not on) and temp_c > 26.3
