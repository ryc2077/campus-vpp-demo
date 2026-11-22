class_name CampusBuilder
extends Node3D
## 校园 3D 建模：按 campus.json 的平面坐标与尺寸程序化搭建。
## 配色按航拍图：米色教学楼、红艺体馆、绿草地、红跑道、蓝灰配电。
## 坐标：米制，x 向东、z 向南（与原 Three.js Demo 同一套平面坐标）。

var campus: Dictionary = {}
var hosts: Dictionary = {} # id -> Node3D（剖切时隐藏的宿主楼体）
var host_bodies: Dictionary = {} # id -> StaticBody3D（隐藏宿主时同步禁用，避免隐藏的楼还挡标签射线）
var pv_arrays: Dictionary = {} # id -> Node3D（屋顶光伏阵列）
var window_mats: Array[StandardMaterial3D] = []
var tree_canopies: Array[Node3D] = []
var storage_shell: Array[MeshInstance3D] = []
var storage_rack_bars: Array[MeshInstance3D] = []
var car_fills: Array[Dictionary] = [] # {fill: MeshInstance3D, base_soc, v2g}
var storage_group: Node3D
var transformer_group: Node3D

func build(data: Dictionary) -> void:
	campus = data
	_build_ground()
	_build_roads()
	for b in campus["buildings"]:
		_build_building(b)
	_build_playground()
	_build_pond()
	_build_storage()
	_build_charge()
	_build_transformer()
	_build_trees()
	_build_flag_and_gate()

func _mat(color: Color, rough: float = 0.85, metal: float = 0.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = color
	m.roughness = rough
	m.metallic = metal
	return m

func _box(parent: Node3D, pos: Vector3, size: Vector3, mat: Material) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = size
	mi.mesh = bm
	mi.position = pos
	mi.material_override = mat
	parent.add_child(mi)
	return mi

func _cyl(parent: Node3D, pos: Vector3, r_top: float, r_bot: float, h: float, mat: Material, sides: int = 20) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = r_top
	cm.bottom_radius = r_bot
	cm.height = h
	cm.radial_segments = sides
	mi.mesh = cm
	mi.position = pos
	mi.material_override = mat
	parent.add_child(mi)
	return mi

func _build_ground() -> void:
	var ground := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(float(campus["ground"]["size"]), float(campus["ground"]["size"]))
	ground.mesh = pm
	ground.material_override = _mat(DataLoader.color_from_hex(campus["ground"]["color"]))
	add_child(ground)
	# 中央广场（浅灰）
	_box(self, Vector3(-6, 0.03, -4), Vector3(150, 0.06, 26), _mat(Color("#d7dee3")))

func _build_roads() -> void:
	var road_mat := _mat(DataLoader.color_from_hex(campus["ground"]["road_color"]))
	_box(self, Vector3(0, 0.05, 42), Vector3(10, 0.1, 110), road_mat) # 南北主路
	_box(self, Vector3(2, 0.05, -44), Vector3(200, 0.1, 7), road_mat) # 东西主路
	_box(self, Vector3(0, 0.05, 116), Vector3(340, 0.1, 26), road_mat) # 南门外道路

func _build_building(b: Dictionary) -> void:
	var pos: Array = b["pos"]
	var size: Array = b["size"]
	var w: float = size[0]
	var d: float = size[1]
	var h: float = b["height"]
	var g := Node3D.new()
	g.name = String(b["id"])
	g.position = Vector3(pos[0], 0, pos[1])
	add_child(g)
	hosts[String(b["id"])] = g
	var wall := _mat(DataLoader.color_from_hex(b["color"]))
	_box(g, Vector3(0, h / 2.0, 0), Vector3(w, h, d), wall)
	# 碰撞体：标签深度遮挡射线用；隐藏宿主时由 set_host_visible() 同步禁用
	var body := StaticBody3D.new()
	body.name = "body"
	var shape := CollisionShape3D.new()
	var bs := BoxShape3D.new()
	bs.size = Vector3(w, h, d)
	shape.shape = bs
	shape.position = Vector3(0, h / 2.0, 0)
	body.add_child(shape)
	g.add_child(body)
	host_bodies[String(b["id"])] = body
	# 屋顶板（略深一档）
	_box(g, Vector3(0, h + 0.15, 0), Vector3(w + 0.6, 0.3, d + 0.6), _mat(DataLoader.color_from_hex(b["color"]).darkened(0.12)))
	# 窗户带：南立面（+z）每层一排亮窗；北立面少半排
	var win_mat := StandardMaterial3D.new()
	win_mat.albedo_color = Color("#8cc8f0")
	win_mat.emission_enabled = true
	win_mat.emission = Color("#8cc8f0")
	win_mat.emission_energy_multiplier = 0.15
	window_mats.append(win_mat)
	var floors: int = b["floors"]
	var cols: int = max(3, int(w / 4.5))
	var fy := 0
	while fy < floors:
		var wy: float = 2.6 + float(fy) * (h - 3.0) / maxf(1.0, float(floors - 1))
		var cx := 0
		while cx < cols:
			var wx: float = -w / 2.0 + 2.2 + float(cx) * (w - 4.4) / maxf(1.0, float(cols - 1))
			_box(g, Vector3(wx, wy, d / 2.0 + 0.06), Vector3(1.9, 1.4, 0.12), win_mat)
			cx += 1
		fy += 1
	# 楼名牌：南立面顶部横牌（深色底 + 白字用 Label3D 由 labels.gd 另行处理，这里只留牌体）
	_box(g, Vector3(0, h - 1.2, d / 2.0 + 0.12), Vector3(minf(w * 0.6, 14.0), 1.6, 0.15), _mat(Color("#17557f")))
	if bool(b.get("pv", false)):
		_build_pv_array(g, w, d, h, String(b["id"]))

func _build_pv_array(host: Node3D, w: float, d: float, h: float, bid: String) -> void:
	var arr := Node3D.new()
	arr.name = "pvArray"
	host.add_child(arr)
	pv_arrays[bid] = arr
	var panel_mat := _mat(Color("#1d4e89"), 0.35, 0.55)
	var frame_mat := _mat(Color("#c8d2dc"), 0.5, 0.3)
	var rows := 2
	var cols := 4
	var r := 0
	while r < rows:
		var c := 0
		while c < cols:
			var px := -w * 0.28 + c * w * 0.19
			var pz := -d * 0.22 + r * d * 0.44
			_box(arr, Vector3(px, h + 0.75, pz), Vector3(w * 0.16, 0.18, d * 0.32), panel_mat)
			_box(arr, Vector3(px, h + 0.55, pz), Vector3(0.3, 0.5, 0.3), frame_mat)
			c += 1
		r += 1

func _build_playground() -> void:
	var pg: Dictionary = campus["playground"]
	var pos: Array = pg["pos"]
	var g := Node3D.new()
	g.name = "playground"
	g.position = Vector3(pos[0], 0, pos[1])
	add_child(g)
	var track_mat := _mat(DataLoader.color_from_hex(campus["ground"]["track_color"]))
	var field_mat := _mat(DataLoader.color_from_hex(campus["ground"]["field_color"]))
	# 跑道：扁圆柱；内场：略小的绿扁圆柱
	_cyl(g, Vector3(0, 0.06, 0), float(pg["rx"]), float(pg["rx"]), 0.12, track_mat, 40)
	_cyl(g, Vector3(0, 0.10, 0), float(pg["rx"]) * 0.78, float(pg["rx"]) * 0.78, 0.12, field_mat, 40)
	g.scale.z = float(pg["rz"]) / float(pg["rx"])
	# 足球门
	_box(g, Vector3(-18, 0.6, 0), Vector3(0.25, 1.2, 7), _mat(Color.WHITE))
	_box(g, Vector3(18, 0.6, 0), Vector3(0.25, 1.2, 7), _mat(Color.WHITE))

func _build_pond() -> void:
	var pd: Dictionary = campus["pond"]
	var pos: Array = pd["pos"]
	var g := Node3D.new()
	g.name = "pond"
	g.position = Vector3(pos[0], 0, pos[1])
	add_child(g)
	_cyl(g, Vector3(0, 0.05, 0), float(pd["rx"]), float(pd["rx"]), 0.1, _mat(Color("#8a9a6b")), 32)
	_cyl(g, Vector3(0, 0.1, 0), float(pd["rx"]) * 0.9, float(pd["rx"]) * 0.9, 0.12, _mat(Color("#9fd8d0"), 0.15, 0.1), 32)
	g.scale.z = float(pd["rz"]) / float(pd["rx"])

func _build_storage() -> void:
	var st: Dictionary = campus["storage"]
	var pos: Array = st["pos"]
	storage_group = Node3D.new()
	storage_group.name = "storageGroup"
	storage_group.position = Vector3(pos[0], 0, pos[1])
	add_child(storage_group)
	var st_body := StaticBody3D.new()
	var st_shape := CollisionShape3D.new()
	var st_bs := BoxShape3D.new()
	st_bs.size = Vector3(10, 5.5, 6)
	st_shape.shape = st_bs
	st_shape.position = Vector3(0, 2.75, 0)
	st_body.add_child(st_shape)
	storage_group.add_child(st_body)
	host_bodies["storage"] = st_body
	# 基座
	_box(storage_group, Vector3(0, 0.2, 0), Vector3(10, 0.4, 6), _mat(Color("#37424c")))
	# 柜体外壳（可半透明切换）
	var shell_mat := StandardMaterial3D.new()
	shell_mat.albedo_color = Color("#059669")
	shell_mat.roughness = 0.45
	shell_mat.metallic = 0.3
	var shell := _box(storage_group, Vector3(0, 2.85, 0), Vector3(8.6, 4.4, 4.0), shell_mat)
	storage_shell.append(shell)
	var roof_mat := StandardMaterial3D.new()
	roof_mat.albedo_color = Color("#37424c")
	roof_mat.roughness = 0.6
	var roof := _box(storage_group, Vector3(0, 5.2, 0), Vector3(9.2, 0.35, 4.6), roof_mat)
	storage_shell.append(roof)
	# 内部电池簇：3 组机架 + SOC 条
	var i := 0
	while i < 3:
		var x := -2.6 + i * 2.6
		_box(storage_group, Vector3(x, 2.2, -0.6), Vector3(2.2, 3.6, 0.7), _mat(Color("#2b3a46"), 0.5, 0.4))
		var bar_mat := StandardMaterial3D.new()
		bar_mat.albedo_color = Color("#34d399")
		bar_mat.emission_enabled = true
		bar_mat.emission = Color("#34d399")
		bar_mat.emission_energy_multiplier = 0.6
		var bar := _box(storage_group, Vector3(x, 2.2, -0.2), Vector3(2.0, 0.35, 0.15), bar_mat)
		storage_rack_bars.append(bar)
		# 风扇
		var fan := _cyl(storage_group, Vector3(x, 4.3, 0.4), 0.55, 0.55, 0.15, _mat(Color("#d7dde3"), 0.4, 0.5), 12)
		fan.rotation_degrees.x = 90
		i += 1
	# PCS 柜
	_box(storage_group, Vector3(4.6, 1.6, -1.2), Vector3(1.6, 3.2, 1.4), _mat(Color("#5b7186"), 0.45, 0.4))
	# 状态灯
	var dot_mat := StandardMaterial3D.new()
	dot_mat.albedo_color = Color("#38f27a")
	dot_mat.emission_enabled = true
	dot_mat.emission = Color("#38f27a")
	dot_mat.emission_energy_multiplier = 1.5
	_box(storage_group, Vector3(0, 5.45, 1.6), Vector3(0.4, 0.4, 0.4), dot_mat)

func _build_charge() -> void:
	var ch: Dictionary = campus["charge"]
	var pos: Array = ch["pos"]
	var g := Node3D.new()
	g.name = "chargeGroup"
	g.position = Vector3(pos[0], 0, pos[1])
	add_child(g)
	_box(g, Vector3(0, 0.05, 0), Vector3(30, 0.1, 18), _mat(Color("#3a4550")))
	var cars: Array = ch["cars"]
	var i := 0
	while i < cars.size():
		var car: Dictionary = cars[i]
		var cx := -9.0 + i * 9.0
		# 充电桩
		_box(g, Vector3(cx, 1.0, -6.5), Vector3(0.9, 2.0, 0.8), _mat(Color("#0f8a7d")))
		# 车身
		_box(g, Vector3(cx, 0.85, 0), Vector3(3.9, 1.0, 1.8), _mat(DataLoader.color_from_hex(car["color"]), 0.35, 0.4))
		_box(g, Vector3(cx - 0.2, 1.65, 0), Vector3(2.0, 0.7, 1.6), _mat(DataLoader.color_from_hex(car["color"]).darkened(0.15), 0.35, 0.4))
		# 车顶 SOC 条（缩放 x 反映 SOC）
		var fill_mat := StandardMaterial3D.new()
		fill_mat.albedo_color = Color("#2fbf71")
		fill_mat.emission_enabled = true
		fill_mat.emission = Color("#2fbf71")
		fill_mat.emission_energy_multiplier = 0.8
		var fill := _box(g, Vector3(cx, 2.15, 0), Vector3(3.4, 0.18, 0.3), fill_mat)
		fill.scale.x = float(car["base_soc"])
		fill.position.x = cx - 3.4 * (1.0 - float(car["base_soc"])) / 2.0
		car_fills.append({"fill": fill, "base_soc": float(car["base_soc"]), "v2g": bool(car.get("v2g", false)), "cx": cx})
		i += 1

func _build_transformer() -> void:
	var tf: Dictionary = campus["transformer"]
	var pos: Array = tf["pos"]
	transformer_group = Node3D.new()
	transformer_group.name = "transformerGroup"
	transformer_group.position = Vector3(pos[0], 0, pos[1])
	add_child(transformer_group)
	var tf_body := StaticBody3D.new()
	var tf_shape := CollisionShape3D.new()
	var tf_bs := BoxShape3D.new()
	tf_bs.size = Vector3(6.5, 4.5, 4.5)
	tf_shape.shape = tf_bs
	tf_shape.position = Vector3(0, 2.25, 0)
	tf_body.add_child(tf_shape)
	transformer_group.add_child(tf_body)
	host_bodies["transformer"] = tf_body
	_box(transformer_group, Vector3(0, 0.2, 0), Vector3(6.5, 0.4, 4.5), _mat(Color("#37424c")))
	_box(transformer_group, Vector3(0, 2.0, 0), Vector3(5.6, 3.4, 3.6), _mat(Color("#7d8fa0"), 0.45, 0.55))
	# 绝缘子
	var j := 0
	while j < 3:
		_cyl(transformer_group, Vector3(-1.8 + j * 1.8, 4.3, 0), 0.28, 0.35, 1.2, _mat(Color("#d7dde3"), 0.4, 0.2), 10)
		j += 1

func _build_trees() -> void:
	var spots: Array = [
		[-90, -74], [-40, -74], [30, -74], [80, -74], [-110, 20], [109, 0], [-40, 26], [90, 26],
		[-100, -20], [100, -50], [-30, 90], [60, 90], [-95, 60], [110, 70],
	]
	for s in spots:
		var t := Node3D.new()
		t.position = Vector3(s[0], 0, s[1])
		add_child(t)
		_cyl(t, Vector3(0, 1.0, 0), 0.28, 0.35, 2.0, _mat(Color("#7a5a38")), 8)
		var canopy := MeshInstance3D.new()
		var sm := SphereMesh.new()
		sm.radius = 2.0
		sm.height = 3.6
		canopy.mesh = sm
		canopy.position = Vector3(0, 3.6, 0)
		canopy.material_override = _mat(Color("#3e8e4f"))
		t.add_child(canopy)
		tree_canopies.append(t)

func _build_flag_and_gate() -> void:
	# 旗杆 + 旗（广场中央）
	_cyl(self, Vector3(-6, 6.0, 8), 0.12, 0.15, 12.0, _mat(Color("#c8d2dc"), 0.4, 0.6), 10)
	var flag := _box(self, Vector3(-4.4, 10.6, 8), Vector3(3.0, 1.8, 0.08), _mat(Color("#de2910")))
	flag.name = "flag"
	# 南门：门柱 + 横梁（校门原位置，近景组常驻）
	var gate := Node3D.new()
	gate.name = "gateGroup"
	gate.position = Vector3(0, 0, 98)
	add_child(gate)
	_box(gate, Vector3(-7, 3.0, 0), Vector3(1.2, 6.0, 1.2), _mat(Color("#17557f")))
	_box(gate, Vector3(7, 3.0, 0), Vector3(1.2, 6.0, 1.2), _mat(Color("#17557f")))
	_box(gate, Vector3(0, 6.2, 0), Vector3(15.2, 1.0, 1.0), _mat(Color("#17557f")))
	_box(gate, Vector3(0, 5.4, 0), Vector3(10.0, 0.7, 0.2), _mat(Color("#f3e9d2")))

func set_shell_translucent(open: bool) -> void:
	for m in storage_shell:
		var mat: StandardMaterial3D = m.material_override as StandardMaterial3D
		if mat == null:
			continue
		if open:
			mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			mat.albedo_color.a = 0.22
			mat.depth_draw_mode = 2 # BaseMaterial3D.DEPTH_DRAW_DISABLED
		else:
			mat.transparency = BaseMaterial3D.TRANSPARENCY_DISABLED
			mat.albedo_color.a = 1.0
			mat.depth_draw_mode = 0 # BaseMaterial3D.DEPTH_DRAW_OPAQUE

func set_host_visible(id: String, visible: bool) -> void:
	var g: Node3D = hosts.get(id)
	if g != null:
		g.visible = visible
	var body: StaticBody3D = host_bodies.get(id)
	if body != null:
		body.set_deferred("disabled", not visible)

func set_night_windows(night_f: float) -> void:
	for m in window_mats:
		m.emission_energy_multiplier = 0.15 + night_f * 1.6
