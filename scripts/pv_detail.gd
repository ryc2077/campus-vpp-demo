class_name PvDetail
extends Node3D
## 光伏屋顶细节组：置于一号教学楼屋顶，入口光伏场景时显示。
## 含逆变器箱、直流/交流流光点（随出力联动）。

var flow_dots: Array[MeshInstance3D] = []
var flow_mats: Array[StandardMaterial3D] = []
var ray_planes: Array[MeshInstance3D] = []

func _ready() -> void:
	_build()

func _mat(c: Color, rough: float = 0.5, metal: float = 0.3) -> StandardMaterial3D:
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
	# 逆变器箱（屋顶东侧）
	_box(Vector3(14, 1.0, 0), Vector3(2.4, 2.0, 1.4), _mat(Color("#5b7186"), 0.45, 0.4))
	var led_mat := StandardMaterial3D.new()
	led_mat.albedo_color = Color("#38f27a")
	led_mat.emission_enabled = true
	led_mat.emission = Color("#38f27a")
	led_mat.emission_energy_multiplier = 1.4
	_box(Vector3(14, 1.6, 0.75), Vector3(0.3, 0.3, 0.06), led_mat)
	# 直流流光点：沿阵列排布 8 个
	var i := 0
	while i < 8:
		var m := StandardMaterial3D.new()
		m.albedo_color = Color("#fbbf24")
		m.emission_enabled = true
		m.emission = Color("#fbbf24")
		m.emission_energy_multiplier = 1.5
		var dot := MeshInstance3D.new()
		var sm := SphereMesh.new()
		sm.radius = 0.18
		sm.height = 0.36
		dot.mesh = sm
		dot.material_override = m
		dot.position = Vector3(-12.0 + i * 3.4, 1.2, 0)
		add_child(dot)
		flow_dots.append(dot)
		flow_mats.append(m)
		i += 1
	# 阳光射线：4 面半透明斜板
	var j := 0
	while j < 4:
		var rm := StandardMaterial3D.new()
		rm.albedo_color = Color(1.0, 0.9, 0.4, 0.10)
		rm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		rm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		var plane := MeshInstance3D.new()
		var pm := PlaneMesh.new()
		pm.size = Vector2(2.2, 14.0)
		plane.mesh = pm
		plane.material_override = rm
		plane.position = Vector3(-10.0 + j * 6.0, 7.0, -2.0)
		plane.rotation_degrees = Vector3(28, 0, 0)
		add_child(plane)
		ray_planes.append(plane)
		j += 1

func update_frame(pv_kw: float, pv_factor: float, t: float) -> void:
	var on := pv_kw > 2.0
	for i in range(flow_dots.size()):
		var d: MeshInstance3D = flow_dots[i]
		d.visible = on
		if on:
			var u := fmod(t * (0.1 + pv_kw / 2500.0) + float(i) / 8.0, 1.0)
			d.position.x = -12.0 + u * 26.0
	for p in ray_planes:
		var m: StandardMaterial3D = p.material_override
		m.albedo_color.a = 0.04 + 0.20 * pv_factor
		p.visible = pv_factor > 0.18
