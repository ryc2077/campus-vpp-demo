class_name CampusBuilder
extends Node3D
## 校园 3D 建模：按 campus.json 的平面坐标与尺寸程序化搭建。
## 配色按航拍图：米色教学楼、红艺体馆、绿草地、红跑道、蓝灰配电。
## 坐标：米制，x 向东、z 向南（与原 Three.js Demo 同一套平面坐标）。
## （GlbLoader 用 preload 而不用全局 class_name：新文件进不了本地陈旧的
##  .godot 类缓存，headless 报未声明；见 ui_controller.gd 的 UITokens 注释。）
const GlbLoader = preload("res://scripts/glb_loader.gd")

var campus: Dictionary = {}
var hosts: Dictionary = {} # id -> Node3D（剖切时隐藏的宿主楼体）
var host_bodies: Dictionary = {} # id -> StaticBody3D（隐藏宿主时同步禁用，避免隐藏的楼还挡标签射线）
var pv_arrays: Dictionary = {} # id -> Node3D（屋顶光伏阵列）
var window_mats: Array[StandardMaterial3D] = []
var tree_canopies: Array[Node3D] = []
var storage_shell: Array[MeshInstance3D] = []
var storage_rack_bars: Array[MeshInstance3D] = []
var storage_rack_tracks: Array[MeshInstance3D] = [] # SOC 条底槽：固定不动的深色轨道，填充条左锚定在槽内伸缩
var storage_rack_bar_cx: Array[float] = [] # 填充条左锚定的基准中心 X（GLB 模式 −2.4/−0.8/0.8，回退时随 _move_soc_bars_to_proc 改写）
var car_fills: Array[Dictionary] = [] # {fill: MeshInstance3D, base_soc, v2g}
var storage_group: Node3D
var storage_soc_group: Node3D # SOC 条组：GLB 成功时 storage_group 隐藏，条子留在组外才可见
var storage_glb_active := false # storage.glb 已接管储能站时，程序化储能组保持隐藏
var storage_glb_shell_mats: Array[StandardMaterial3D] = [] # GLB 壳/顶材质（外壳开关控制用，[0]=壳 [1]=顶）
var storage_glb_shell_base_alpha: Array[float] = [] # 开关关时恢复的原始 alpha
var storage_glb_shell_base_transp: Array[int] = [] # 开关关时恢复的原始透明模式
var storage_glb_shell_base_depth: Array[int] = [] # 开关关时恢复的原始深度模式
var transformer_group: Node3D
var charge_group: Node3D
var charge_glb_active := false # charge.glb 已接管充电区时，程序化充电组保持隐藏
var overview_glb_active := false # overview.glb 已接管总览时，程序化宿主保持隐藏
var _proc_overview_nodes: Array[Node] = [] # 程序化总览件（地面/道路/操场/池塘/树/旗门），overview.glb 成功后隐藏

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
	_load_scene_glbs()

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
	_proc_overview_nodes.append(ground)
	# 中央广场（浅灰）
	_proc_overview_nodes.append(_box(self, Vector3(-6, 0.03, -4), Vector3(150, 0.06, 26), _mat(Color("#d7dee3"))))

func _build_roads() -> void:
	var road_mat := _mat(DataLoader.color_from_hex(campus["ground"]["road_color"]))
	_proc_overview_nodes.append(_box(self, Vector3(0, 0.05, 42), Vector3(10, 0.1, 110), road_mat)) # 南北主路
	_proc_overview_nodes.append(_box(self, Vector3(2, 0.05, -44), Vector3(200, 0.1, 7), road_mat)) # 东西主路
	_proc_overview_nodes.append(_box(self, Vector3(0, 0.05, 116), Vector3(340, 0.1, 26), road_mat)) # 南门外道路

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
		# 顶层窗顶不得超过墙顶：窗半高 0.7，旧公式顶层 wy = h-0.4、窗顶 h+0.30 埋入屋顶板；
		# 钳制到 h-0.75，顶层窗顶 = h-0.05（留 5cm），只影响顶层，其余楼层不变
		wy = minf(wy, h - 0.75)
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
	_proc_overview_nodes.append(g)
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
	_proc_overview_nodes.append(g)
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
	# 柜体外壳（可半透明切换）：壳底 2.60-2.20=0.40 落在基座顶（0.40），旧值 2.85 时壳底 0.65 悬空 0.25；屋顶/状态灯随壳体同降 0.25，相对位置不变
	var shell_mat := StandardMaterial3D.new()
	shell_mat.albedo_color = Color("#059669")
	shell_mat.roughness = 0.45
	shell_mat.metallic = 0.3
	var shell := _box(storage_group, Vector3(0, 2.60, 0), Vector3(8.6, 4.4, 4.0), shell_mat)
	storage_shell.append(shell)
	var roof_mat := StandardMaterial3D.new()
	roof_mat.albedo_color = Color("#37424c")
	roof_mat.roughness = 0.6
	var roof := _box(storage_group, Vector3(0, 4.95, 0), Vector3(9.2, 0.35, 4.6), roof_mat)
	storage_shell.append(roof)
	# 内部电池簇：3 组机架 + SOC 条
	# SOC 条单独成组（与 storage_group 同原点 (64,0,-30)）：storage.glb 加载成功时
	# storage_group 整体隐藏，条子留在组外才可见。条子位置按 GLB 实测对齐
	# （storage.glb）：3 台电池柜局部中心 X −2.4/−0.8/0.8、柜顶 2.55、前脸 Z 0.5；
	# 填充条宽 1.1（柜宽 1.3，左右各留 0.1）、中心 Z 0.65（厚 0.15，背面 0.575，
	# 距门板前脸 0.545 留 0.03，不埋进柜体）、Y 2.2（顶 2.375 < 柜顶 2.55，不悬空）。
	# 每台柜门上另有一条固定底槽（1.24×0.47×0.10，深色 #1f2937，Z 0.60）：
	# 填充条左锚定在槽内按 SOC 伸缩（main.gd _update_visuals），空槽部分可见，
	# 肉眼才能读出“条 + 填充比例”；旧版只有居中缩放的实心块，看着像贴片。
	# GLB 加载失败走回退时，_load_scene_glbs() 把条子与底槽移回程序化机架位置。
	var soc_group := Node3D.new()
	soc_group.name = "storageSocGroup"
	soc_group.position = Vector3(pos[0], 0, pos[1])
	add_child(soc_group)
	storage_soc_group = soc_group
	var i := 0
	while i < 3:
		var x := -2.6 + i * 2.6
		_box(storage_group, Vector3(x, 2.2, -0.6), Vector3(2.2, 3.6, 0.7), _mat(Color("#2b3a46"), 0.5, 0.4))
		# 底槽：固定不动（Z 0.60，厚 0.10，背面 0.55 距门板前脸 0.545 留 0.005，
		# 前面 0.65；填充条前面 0.725，比槽面凸出 0.075，无共面、不 z-fight）
		var track := _box(soc_group, Vector3(-2.4 + i * 1.6, 2.2, 0.60), Vector3(1.24, 0.47, 0.10), _mat(Color("#1f2937"), 0.6, 0.0))
		storage_rack_tracks.append(track)
		var bar_mat := StandardMaterial3D.new()
		bar_mat.albedo_color = Color("#34d399")
		bar_mat.emission_enabled = true
		bar_mat.emission = Color("#34d399")
		bar_mat.emission_energy_multiplier = 0.6
		var bar := _box(soc_group, Vector3(-2.4 + i * 1.6, 2.2, 0.65), Vector3(1.1, 0.35, 0.15), bar_mat)
		storage_rack_bars.append(bar)
		storage_rack_bar_cx.append(-2.4 + i * 1.6)
		# 风扇
		var fan := _cyl(storage_group, Vector3(x, 4.3, 0.4), 0.55, 0.55, 0.15, _mat(Color("#d7dde3"), 0.4, 0.5), 12)
		fan.rotation_degrees.x = 90
		i += 1
	# PCS 柜：柜底 2.0-1.6=0.40 落在基座顶（0.40），旧值 1.6 时柜底 0.0 埋入基座 0.40
	_box(storage_group, Vector3(4.6, 2.0, -1.2), Vector3(1.6, 3.2, 1.4), _mat(Color("#5b7186"), 0.45, 0.4))
	# 状态灯
	var dot_mat := StandardMaterial3D.new()
	dot_mat.albedo_color = Color("#38f27a")
	dot_mat.emission_enabled = true
	dot_mat.emission = Color("#38f27a")
	dot_mat.emission_energy_multiplier = 1.5
	_box(storage_group, Vector3(0, 5.20, 1.6), Vector3(0.4, 0.4, 0.4), dot_mat)

func _build_charge() -> void:
	var ch: Dictionary = campus["charge"]
	var pos: Array = ch["pos"]
	var g := Node3D.new()
	g.name = "chargeGroup"
	g.position = Vector3(pos[0], 0, pos[1])
	add_child(g)
	charge_group = g
	_box(g, Vector3(0, 0.05, 0), Vector3(30, 0.1, 18), _mat(Color("#3a4550")))
	var cars: Array = ch["cars"]
	var i := 0
	while i < cars.size():
		var car: Dictionary = cars[i]
		var cx := -9.0 + i * 9.0
		# 充电桩
		_box(g, Vector3(cx, 1.0, -6.5), Vector3(0.9, 2.0, 0.8), _mat(Color("#0f8a7d")))
		# 车身：车身底 0.60-0.50=0.10 落在地面垫顶（0.10），旧值 0.85 时底 0.35 悬空 0.25；车舱/SOC 条随车身同降 0.25，相对位置不变
		_box(g, Vector3(cx, 0.60, 0), Vector3(3.9, 1.0, 1.8), _mat(DataLoader.color_from_hex(car["color"]), 0.35, 0.4))
		_box(g, Vector3(cx - 0.2, 1.40, 0), Vector3(2.0, 0.7, 1.6), _mat(DataLoader.color_from_hex(car["color"]).darkened(0.15), 0.35, 0.4))
		# 车轮：圆柱横置（轴沿 z），轮底 = 0.45-0.35 = 0.10 落在地面垫顶
		var wheel_mat := _mat(Color("#1c2126"), 0.6, 0.2)
		for wx_off in [-1.2, 1.2]:
			for wz_off in [-0.95, 0.95]:
				_cyl(g, Vector3(cx + wx_off, 0.45, wz_off), 0.35, 0.35, 0.25, wheel_mat, 16).rotation_degrees.x = 90
		# 车顶 SOC 条（缩放 x 反映 SOC）：条底 1.84-0.09=1.75 贴合车舱顶（1.75），旧值 1.90 时条底 1.81 悬空 0.06
		var fill_mat := StandardMaterial3D.new()
		fill_mat.albedo_color = Color("#2fbf71")
		fill_mat.emission_enabled = true
		fill_mat.emission = Color("#2fbf71")
		fill_mat.emission_energy_multiplier = 0.8
		var fill := _box(g, Vector3(cx, 1.84, 0), Vector3(3.4, 0.18, 0.3), fill_mat)
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
		_proc_overview_nodes.append(t)
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
	_proc_overview_nodes.append(flag)
	# 南门：门柱 + 横梁（校门原位置，近景组常驻）
	var gate := Node3D.new()
	gate.name = "gateGroup"
	gate.position = Vector3(0, 0, 98)
	add_child(gate)
	_proc_overview_nodes.append(gate)
	_box(gate, Vector3(-7, 3.0, 0), Vector3(1.2, 6.0, 1.2), _mat(Color("#17557f")))
	_box(gate, Vector3(7, 3.0, 0), Vector3(1.2, 6.0, 1.2), _mat(Color("#17557f")))
	_box(gate, Vector3(0, 6.2, 0), Vector3(15.2, 1.0, 1.0), _mat(Color("#17557f")))
	_box(gate, Vector3(0, 5.4, 0), Vector3(10.0, 0.7, 0.2), _mat(Color("#f3e9d2")))

func set_shell_translucent(open: bool) -> void:
	# GLB 已接管：改 GLB 壳/顶材质——程序化组已隐藏，改它无可见效果。
	# 开：与程序化路同款半透明（alpha 0.22）；关：不透明（alpha 1.0、透明关、
	# 深度不透明），与程序化路一致。注意 GLB 壳原生 alpha 就是 0.35 半透明，
	# 所以“关”不能恢复原始值——恢复 0.35 等于开关失灵（面板写“关”、盒子
	# 仍半透明，run 45219977015 的 02-storage.png 正是此状）；原始值只作
	# 记录（storage_glb_shell_base_*），不再作为关态。
	if not storage_glb_shell_mats.is_empty():
		for i in range(storage_glb_shell_mats.size()):
			var mat: StandardMaterial3D = storage_glb_shell_mats[i]
			if open:
				mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
				mat.albedo_color.a = 0.22
				mat.depth_draw_mode = 2 # BaseMaterial3D.DEPTH_DRAW_DISABLED
			else:
				mat.transparency = BaseMaterial3D.TRANSPARENCY_DISABLED
				mat.albedo_color.a = 1.0
				mat.depth_draw_mode = 0 # BaseMaterial3D.DEPTH_DRAW_OPAQUE
		return
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

## 收集 GLB 储能壳/顶的材质：节点名 Storage_Shell_ASSEMBLY_ADDED /
## Storage_Roof_ASSEMBLY_ADDED（storage.glb 实测）；导入的 glTF 材质在 mesh 表面
## 上（不在 material_override 上），用 get_active_material(0) 取；并记下原始
## alpha/透明/深度模式，开关关时原样恢复。先壳后顶，顺序固定（[0]=壳，[1]=顶）。
func _collect_glb_shell_mats(root: Node) -> void:
	_collect_glb_shell_named(root, "Storage_Shell")
	_collect_glb_shell_named(root, "Storage_Roof")
	if storage_glb_shell_mats.is_empty():
		push_warning("[CampusBuilder] storage.glb 里没找到 Storage_Shell/Storage_Roof 材质节点，外壳开关将无可见效果")

func _collect_glb_shell_named(root: Node, prefix: String) -> void:
	var stack: Array[Node] = [root]
	while not stack.is_empty():
		var n: Node = stack.pop_back()
		if n is MeshInstance3D and n.name.begins_with(prefix):
			var mat := (n as MeshInstance3D).get_active_material(0) as StandardMaterial3D
			if mat != null:
				storage_glb_shell_mats.append(mat)
				storage_glb_shell_base_alpha.append(mat.albedo_color.a)
				storage_glb_shell_base_transp.append(mat.transparency)
				storage_glb_shell_base_depth.append(mat.depth_draw_mode)
		for ch in n.get_children():
			stack.append(ch)

## GLB 加载失败回退：SOC 条与底槽移回程序化机架位置（x −2.6/0/+2.6，条宽 2.0、
## 槽宽 2.14，条 z −0.2、槽 z −0.22，条前面 −0.125 比槽面 −0.17 凸出 0.045），
## 否则条子会悬在机架前方空中；基准中心 storage_rack_bar_cx 同步改写，
## main.gd 的左锚定填充才不会按 GLB 中心错位。
func _move_soc_bars_to_proc() -> void:
	var i := 0
	for bar in storage_rack_bars:
		bar.position = Vector3(-2.6 + i * 2.6, 2.2, -0.2)
		var bm := bar.mesh as BoxMesh
		if bm != null:
			bm.size = Vector3(2.0, 0.35, 0.15)
		if i < storage_rack_bar_cx.size():
			storage_rack_bar_cx[i] = -2.6 + i * 2.6
		i += 1
	var j := 0
	for track in storage_rack_tracks:
		track.position = Vector3(-2.6 + j * 2.6, 2.2, -0.22)
		var tm := track.mesh as BoxMesh
		if tm != null:
			tm.size = Vector3(2.14, 0.47, 0.10)
		j += 1

func set_host_visible(id: String, visible: bool) -> void:
	# overview.glb 已接管时，程序化宿主不恢复可见（否则与 GLB 楼体重叠成双份）；
	# 隐藏方向不受影响（进教室/配电房时仍可调 false）。
	if visible and overview_glb_active and hosts.has(id):
		return
	var g: Node3D = hosts.get(id)
	if g != null:
		g.visible = visible
	var body: StaticBody3D = host_bodies.get(id)
	if body != null:
		body.set_deferred("disabled", not visible)

func set_night_windows(night_f: float) -> void:
	for m in window_mats:
		m.emission_energy_multiplier = 0.15 + night_f * 1.6

## 场景 GLB 接线（BLENDER_MODELS.md §7）：全局坐标场景一律挂 Campus 原点，
## 不移位置、不旋转；加载成功就隐藏对应的程序化模型（不要双份），
## 失败则保留程序化作回退（GlbLoader 已打印警告）。
## 户外变压器组 [74,-30] 无 Blender 件（§6 缺口），始终保留程序化。
func _load_scene_glbs() -> void:
	# R2-T38 探针第 1 步：不加载 overview.glb（attach 跳过），但程序化总览件
	# 与宿主仍按 GLB 已接管处理（隐藏 + 碰撞禁用，overview_glb_active=true），
	# 使除 GLB 本体外的一切状态与基线一致：标签遮挡射线（mask 1，命中宿主
	# 碰撞体）与 verify 口径不变；单因素去除，只缺 GLB 本体。
	# 探针分支专用，绝不合入 main。
	overview_glb_active = true
	for n in _proc_overview_nodes:
		n.visible = false
	for id in hosts.keys():
		set_host_visible(id, false)
	# 储能站（全局坐标，Blender 中心 (64,30)；含拼装补的半透明壳体）
	var st_glb := GlbLoader.attach(self, "storage", "StorageGLB")
	if st_glb != null and storage_group != null:
		storage_group.visible = false
		storage_glb_active = true
		_collect_glb_shell_mats(st_glb)
	else:
		# GLB 回退：SOC 条移回程序化机架位置，否则条子会悬在机架前方空中。
		_move_soc_bars_to_proc()
	# 光伏屋顶（全局坐标，A/B/实验楼屋顶机位）
	if GlbLoader.attach(self, "pv", "PvGLB") != null:
		for arr in pv_arrays.values():
			(arr as Node3D).visible = false
	# 充电区（全局坐标，Blender 中心 (44,-76)）
	var ch_glb := GlbLoader.attach(self, "charge", "ChargeGLB")
	if ch_glb != null and charge_group != null:
		charge_group.visible = false
		charge_glb_active = true
		_build_charge_glb_soc_bars(ch_glb)

## GLB 分支车顶 SOC 条（run 45297927902 修补：主场景车顶条缺失，回退分支有、主场景无）。
## 根因：charge.glb 加载成功时上面把整个程序化 charge_group 藏掉，车顶 SOC 条
## （car_fills）是该组子节点，连带被藏；GLB 车自带车顶，无条。S4 只量条位置不量
## 可见，整组隐藏时也全过，故回归未被拦住。
## 修法：GLB 车组（ch-cars_blue/red/white，各自绕 Y 转 −90°、车身长沿全局 z）
## 下挂与程序化条同尺寸 (3.4, 0.18, 0.3) 的条子，作车组子节点——车组局部系里
## 条仍沿 x，仍用 main.gd _update_visuals 的 scale.x / position.x 驱动，零改动。
## 条底 = GLB 车顶 1.375（车顶节点 y 1.125 + 网格半高 0.25，运行时由 mesh AABB 算，
## 不写死），中心 y 1.465；程序化 car_fills 由此三条替换（仍为 3 条），回退分支不动。
## 车色按 campus.json hex 认组（蓝 #3b82c4 / 红 #c4534e / 白 #d7dde3），找不到组时
## 警告并跳过该车（verify 的 3 条计数会拦住，不静默错挂）。
func _build_charge_glb_soc_bars(ch_glb: Node3D) -> void:
	var color_key := {"#3b82c4": "blue", "#c4534e": "red", "#d7dde3": "white"}
	var cars: Array = campus["charge"]["cars"]
	var glb_fills: Array[Dictionary] = []
	var i := 0
	while i < cars.size():
		var car: Dictionary = cars[i]
		var key: String = String(color_key.get(String(car["color"]).to_lower(), ""))
		if key == "":
			push_warning("[CampusBuilder] GLB 车顶 SOC 条：颜色 %s 未认出，跳过该车" % str(car["color"]))
			i += 1
			continue
		var grp := ch_glb.find_child("ch-cars_" + key, true, false) as Node3D
		var roof := ch_glb.find_child("ch-cars_" + key + "_roof", true, false) as MeshInstance3D
		if grp == null or roof == null or roof.mesh == null:
			push_warning("[CampusBuilder] GLB 车顶 SOC 条：%s 车组/车顶未找到，跳过该车" % key)
			i += 1
			continue
		var roof_top: float = roof.position.y + roof.mesh.get_aabb().size.y / 2.0
		var fill_mat := StandardMaterial3D.new()
		fill_mat.albedo_color = Color("#2fbf71")
		fill_mat.emission_enabled = true
		fill_mat.emission = Color("#2fbf71")
		fill_mat.emission_energy_multiplier = 0.8
		var fill := _box(grp, Vector3(roof.position.x, roof_top + 0.09, roof.position.z), Vector3(3.4, 0.18, 0.3), fill_mat)
		fill.scale.x = float(car["base_soc"])
		fill.position.x = roof.position.x - 3.4 * (1.0 - float(car["base_soc"])) / 2.0
		glb_fills.append({"fill": fill, "base_soc": float(car["base_soc"]), "v2g": bool(car.get("v2g", false)), "cx": roof.position.x})
		i += 1
	car_fills = glb_fills
