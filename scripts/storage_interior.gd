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
	# 高度换算（Blender st-doors 实测）：柜顶 2.55m、风扇盘底 2.555m（高出柜顶 0.005m
	# 防 z-fighting）；Godot Y = Blender Z（同原点、1:1，储能内景置于 (64,0,-30)
	# 与柜体同原点），盘半径 0.55m，故中心 y = 2.555 + 0.55 = 3.105m，盘底恰为 2.555m。
	# （原 y=3.4 时盘底为 2.85m，盘底偏高 0.30m；3.4-2.55=0.85m 是中心到柜顶之差。）
	# X 对齐 GLB（storage.glb 实测）：PCS 柜局部 X 1.75–3.05，中心 2.4（原 4.6 是按
	# 程序化 PCS 标的，盘东缘 5.15 已穿出 GLB 壳东墙 4.3）。
	# Z 避让 GLB 自带 PCS_FanDisc（局部 X 2.2–2.6、Y 2.555–2.585、Z ±0.2，水平小盘）：
	# 本盘竖立、盘底 2.555 与小盘顶 2.585 在 Y 上重叠 0.03m，故把盘沿 Z 前移——hub z 0.32
	#（盘厚 0.12，Z 0.26–0.38）与小盘 Z 上缘 0.2 留 0.06m 间隙，不再相交；叶片 z 0.40
	#（Z 0.31–0.49）仍在柜前脸 0.5 以内，不穿墙。
	var hub := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = 0.55
	cm.bottom_radius = 0.55
	cm.height = 0.12
	cm.radial_segments = 16
	hub.mesh = cm
	hub.position = Vector3(2.4, 3.105, 0.32)
	hub.rotation_degrees.x = 90
	hub.material_override = _mat(Color("#37424c"), 0.4, 0.5)
	add_child(hub)
	fan = MeshInstance3D.new()
	var fm := BoxMesh.new()
	fm.size = Vector3(0.9, 0.12, 0.18)
	fan.mesh = fm
	fan.position = Vector3(2.4, 3.105, 0.40)
	fan.material_override = _mat(Color("#d7dde3"), 0.4, 0.5)
	add_child(fan)
	# 能量流光点：沿机架竖向 3 条
	# 对齐 GLB（storage.glb 实测）：3 台电池柜局部中心 X −2.4/−0.8/0.8（柜体 X 依次
	# −3.05–−1.75、−1.45–−0.15、0.15–1.45；GLB 只有 3 台电池柜，另 1 台是 PCS 柜，
	# 中心 2.4，不放流光点），柜前脸局部 Z 0.5，柜顶 Y 2.55。
	# 球 r0.08，z=0.58 时球后缘恰贴前脸 0.5（格栅条最凸 0.514，球面仅在 y 1.71–2.10
	# 段与格栅平面相交 ≤0.014m，可忽略，与 r0.14/z=0.64 旧口径同值）；球前缘只探出
	# 柜面 0.16m（旧 0.28m）、近拍直径约 23px（旧约 40px），不再是浮空大圆点。
	# y 行程 0.3–2.37：球顶缘 2.37+0.08=2.45，柜顶 2.55 下留 0.10m 余量
	#（上一轮 2.47 时球顶缘 2.55 恰贴柜顶线，#101/#102 近拍仍见个别点顶端
	# 贴线；本轮行程顶端再下压 0.10m，球顶缘 ≤ 柜顶 −0.05m）；下缘 0.22
	# 仍高于踢脚顶 0.15。X 列/灯带/风扇一行未动。
	var i := 0
	while i < 9:
		var m := StandardMaterial3D.new()
		m.albedo_color = Color("#34d399")
		m.emission_enabled = true
		m.emission = Color("#34d399")
		m.emission_energy_multiplier = 1.4
		var dot := MeshInstance3D.new()
		var sm := SphereMesh.new()
		sm.radius = 0.08
		sm.height = 0.16
		dot.mesh = sm
		dot.material_override = m
		dot.position = Vector3(-2.4 + (i % 3) * 1.6, 0.3 + (i / 3) * 1.035, 0.58)
		add_child(dot)
		flow_dots.append(dot)
		flow_mats.append(m)
		i += 1
	# 检修灯带（柜顶）
	# 对齐 GLB（storage.glb 实测）：屋顶板顶 Y 5.375（板 Y 5.025–5.375）。灯带厚 0.08，
	# 中心 y=5.415 时底面 5.375 恰贴屋顶顶面（原 5.35 时 81% 埋没，仅露 0.015m）；
	# 底面与屋顶顶面法向相反（下 vs 上），共面不产生可见 z-fighting，故不另留间隙。
	var strip_mat := StandardMaterial3D.new()
	strip_mat.albedo_color = Color("#fff3d6")
	strip_mat.emission_enabled = true
	strip_mat.emission = Color("#fff3d6")
	strip_mat.emission_energy_multiplier = 1.0
	_box(Vector3(0, 5.415, 0), Vector3(8.0, 0.08, 0.3), strip_mat)

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
			d.position.y = 0.3 + u * 2.07
