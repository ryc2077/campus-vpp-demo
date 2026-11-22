class_name StorageInterior
extends Node3D
## 储能站内景细节组：置于储能柜原位置，入口时与校园储能组叠加显示。
## 含 PCS 风扇（旋转）、内部能量流光点（充蓝/放绿）、检修灯带。

var fan: MeshInstance3D
var flow_dots: Array[MeshInstance3D] = []
var flow_mats: Array[StandardMaterial3D] = []

func _ready() -> void:
	_build()

func _mat(c: Color, rough: float = 0.6, metal: float = 0.3) -> StandardMaterial3D:
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
	# PCS 风扇（立式圆盘 + 叶片）
	var hub := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = 0.55
	cm.bottom_radius = 0.55
	cm.height = 0.12
	cm.radial_segments = 16
	hub.mesh = cm
	hub.position = Vector3(4.6, 3.4, 0.2)
	hub.rotation_degrees.x = 90
	hub.material_override = _mat(Color("#37424c"), 0.4, 0.5)
	add_child(hub)
	fan = MeshInstance3D.new()
	var fm := BoxMesh.new()
	fm.size = Vector3(0.9, 0.12, 0.18)
	fan.mesh = fm
	fan.position = Vector3(4.6, 3.4, 0.28)
	fan.material_override = _mat(Color("#d7dde3"), 0.4, 0.5)
	add_child(fan)
	# 能量流光点：沿机架竖向 3 条
	var i := 0
	while i < 9:
		var m := StandardMaterial3D.new()
		m.albedo_color = Color("#34d399")
		m.emission_enabled = true
		m.emission = Color("#34d399")
		m.emission_energy_multiplier = 1.4
		var dot := MeshInstance3D.new()
		var sm := SphereMesh.new()
		sm.radius = 0.14
		sm.height = 0.28
		dot.mesh = sm
		dot.material_override = m
		dot.position = Vector3(-2.6 + (i % 3) * 2.6, 1.0 + (i / 3) * 1.4, 0.4)
		add_child(dot)
		flow_dots.append(dot)
		flow_mats.append(m)
		i += 1
	# 检修灯带（柜顶）
	var strip_mat := StandardMaterial3D.new()
	strip_mat.albedo_color = Color("#fff3d6")
	strip_mat.emission_enabled = true
	strip_mat.emission = Color("#fff3d6")
	strip_mat.emission_energy_multiplier = 1.0
	_box(Vector3(0, 5.35, 0), Vector3(8.0, 0.08, 0.3), strip_mat)

func update_frame(batt_kw: float, t: float, delta: float) -> void:
	if fan != null:
		fan.rotation.z -= delta * (9.0 if absf(batt_kw) > 1.0 else 0.6)
	var col := Color("#38bdf8") if batt_kw < -1.0 else Color("#34d399")
	for i in range(flow_dots.size()):
		var d: MeshInstance3D = flow_dots[i]
		var m: StandardMaterial3D = flow_mats[i]
		m.albedo_color = col
		m.emission = col
		var active := absf(batt_kw) > 1.0
		d.visible = active
		if active:
			var u := fmod(t * (0.12 + absf(batt_kw) / 300.0) + float(i) / 9.0, 1.0)
			if batt_kw < -1.0:
				u = 1.0 - u
			d.position.y = 1.0 + u * 3.2
