class_name ChargeDetail
extends Node3D
## 充电区细节组：V2G 能量弧线（充电区 → 储能站方向）+ 充电桩状态灯。
## 弧线由 12 个流光点沿二次贝塞尔曲线运动，放电时橙色、充电时蓝色。

var arc_dots: Array[MeshInstance3D] = []
var arc_mats: Array[StandardMaterial3D] = []
var arc_segs: Array[MeshInstance3D] = []
var arc_from := Vector3(44, 2.0, 76)
var arc_mid := Vector3(54, 9.0, 20)
var arc_to := Vector3(64, 3.0, -30)

func _ready() -> void:
	_build()

func _mat(c: Color) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	m.roughness = 0.5
	return m

func _build() -> void:
	var i := 0
	while i < 12:
		var m := StandardMaterial3D.new()
		m.albedo_color = Color("#fb923c")
		m.emission_enabled = true
		m.emission = Color("#fb923c")
		m.emission_energy_multiplier = 1.5
		var dot := MeshInstance3D.new()
		var sm := SphereMesh.new()
		sm.radius = 0.22
		sm.height = 0.44
		dot.mesh = sm
		dot.material_override = m
		add_child(dot)
		arc_dots.append(dot)
		arc_mats.append(m)
		i += 1
	# 弧线基线（细线用拉长薄盒分段近似）
	var prev := _bezier(0.0)
	var s := 1
	while s <= 16:
		var u := float(s) / 16.0
		var p := _bezier(u)
		var mid := (prev + p) / 2.0
		var seg := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = Vector3(0.12, 0.12, prev.distance_to(p) + 0.2)
		seg.mesh = bm
		seg.position = mid - position # 子节点本地坐标：减去本组原点
		seg.look_at_from_position(mid - position, p - position, Vector3.UP)
		var lm := StandardMaterial3D.new()
		lm.albedo_color = Color(0.98, 0.57, 0.09, 0.35)
		lm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		lm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		seg.material_override = lm
		add_child(seg)
		arc_segs.append(seg)
		prev = p
		s += 1

func _bezier(u: float) -> Vector3:
	var a := arc_from.lerp(arc_mid, u)
	var b := arc_mid.lerp(arc_to, u)
	return a.lerp(b, u)

func update_frame(ev_kw: float, hour: float, t: float, pv_factor: float = 1.0) -> void:
	var discharging := ev_kw > 1.0
	# 天气门控（run 45297927902 修补）：弧线不再随 pv_factor 隐藏——雨天
	# pv_factor=0.30 时旧条件 `pv_factor > 0.30` 为假，整条弧线（流光点 + 基线）
	# 被连同阳光射线一起藏掉，11-charge-rain 放电 54kW 却无线无点；晴天 12 同功率
	# 弧线清晰。V2G 弧线是能量流（放电或日间时段即显示），与光伏出力无关；
	# 阳光射线雨天隐藏仍在 pv_detail.gd 那一行，不动。
	# pv_factor 参数保留（main.gd 调用签名不变），此处不再使用。
	var active := discharging or (hour > 7.5 and hour < 17.5)
	var col := Color("#fb923c") if discharging else Color("#38bdf8")
	for s in arc_segs:
		s.visible = active
	for i in range(arc_dots.size()):
		var d: MeshInstance3D = arc_dots[i]
		var m: StandardMaterial3D = arc_mats[i]
		m.albedo_color = col
		m.emission = col
		d.visible = active
		if active:
			var u := fmod(t * (0.06 + ev_kw / 2200.0) + float(i) / 12.0, 1.0)
			if discharging:
				u = 1.0 - u
			d.position = _bezier(u) - position
