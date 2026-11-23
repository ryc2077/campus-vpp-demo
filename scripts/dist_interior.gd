class_name DistInterior
extends Node3D
## 配电房内景（调度中心）：10kV 总变电所示意。
## 开关柜一排、母线铜排、计量表盘、电缆沟；南墙留门洞。
## （GlbLoader 用 preload：见 campus_builder.gd 注释。）
const GlbLoader = preload("res://scripts/glb_loader.gd")

var meter_needles: Array[MeshInstance3D] = []
var busbar_mat: StandardMaterial3D

const W := 15.0
const D := 9.0
const H := 4.5

func _ready() -> void:
	_build()

func _mat(c: Color, rough: float = 0.85, metal: float = 0.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	m.roughness = rough
	m.metallic = metal
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
	# 配电房 GLB（局部坐标，房中心原点）优先；加载失败回退程序化并警告
	var inst := GlbLoader.load_glb(GlbLoader.SCENES["dist"])
	if inst != null:
		inst.name = "DistGLB"
		add_child(inst)
		return
	_build_procedural()

func _build_procedural() -> void:
	_box(Vector3(0, 0.05, 0), Vector3(W, 0.1, D), _mat(Color("#9aa5ad")))
	_box(Vector3(0, H + 0.05, 0), Vector3(W, 0.1, D), _mat(Color("#e8e2d4")))
	_box(Vector3(0, H / 2, -D / 2), Vector3(W, H, 0.15), _mat(Color("#dfe9f2")))
	_box(Vector3(-W / 2, H / 2, 0), Vector3(0.15, H, D), _mat(Color("#dfe9f2")))
	_box(Vector3(W / 2, H / 2, 0), Vector3(0.15, H, D), _mat(Color("#dfe9f2")))
	# 南墙：门洞左右两段 + 门楣
	var seg := (W - 2.4) / 2.0
	_box(Vector3(-(1.2 + seg / 2.0), H / 2, D / 2), Vector3(seg, H, 0.15), _mat(Color("#dfe9f2")))
	_box(Vector3(1.2 + seg / 2.0, H / 2, D / 2), Vector3(seg, H, 0.15), _mat(Color("#dfe9f2")))
	_box(Vector3(0, H - 0.5, D / 2), Vector3(2.4, 1.0, 0.15), _mat(Color("#dfe9f2")))
	# 开关柜：北墙一排 4 台
	var i := 0
	while i < 4:
		var x := -5.4 + i * 3.6
		_box(Vector3(x, 1.4, -D / 2 + 0.6), Vector3(2.6, 2.8, 1.0), _mat(Color("#5b7186"), 0.45, 0.4))
		# 表盘
		_box(Vector3(x, 2.2, -D / 2 + 1.12), Vector3(1.6, 0.9, 0.06), _mat(Color("#f5f2ea")))
		var needle_mat := StandardMaterial3D.new()
		needle_mat.albedo_color = Color("#dc2626")
		needle_mat.emission_enabled = true
		needle_mat.emission = Color("#dc2626")
		needle_mat.emission_energy_multiplier = 0.6
		var needle := _box(Vector3(x, 2.2, -D / 2 + 1.16), Vector3(0.06, 0.7, 0.03), needle_mat)
		needle.position.y = 2.2
		meter_needles.append(needle)
		# 状态灯
		var led_mat := StandardMaterial3D.new()
		led_mat.albedo_color = Color("#38f27a")
		led_mat.emission_enabled = true
		led_mat.emission = Color("#38f27a")
		led_mat.emission_energy_multiplier = 1.2
		_box(Vector3(x + 1.0, 2.6, -D / 2 + 1.12), Vector3(0.18, 0.18, 0.05), led_mat)
		i += 1
	# 母线铜排（沿北墙顶部）
	busbar_mat = _mat(Color("#b87333"), 0.35, 0.85)
	_box(Vector3(0, 3.6, -D / 2 + 0.5), Vector3(13.0, 0.18, 0.18), busbar_mat)
	# 电缆沟（地面暗槽）
	_box(Vector3(0, 0.12, 1.5), Vector3(12.0, 0.06, 1.2), _mat(Color("#37424c")))
	# 调度台
	_box(Vector3(3.5, 0.6, 2.2), Vector3(3.4, 1.2, 1.0), _mat(Color("#2b3a46"), 0.5, 0.3))
	_box(Vector3(3.5, 1.35, 2.0), Vector3(3.0, 0.9, 0.08), _mat(Color("#0e7490"), 0.3, 0.2))
	# 警示牌
	_box(Vector3(-6.0, 2.6, -D / 2 + 0.12), Vector3(1.8, 1.0, 0.06), _mat(Color("#facc15")))

func set_load_rate(rate: float) -> void:
	# 表针随负载率摆动（-35° ~ +35°）
	for n in meter_needles:
		n.rotation.z = deg_to_rad(lerpf(-35.0, 35.0, clampf(rate, 0.0, 1.2) / 1.2))
