class_name Labels3D
extends Node3D
## 屏幕空间标注：Label3D（billboard）+ 每 0.15s 复算。
## 已知问题修复（相对原 Demo）：
## 1) 被遮挡标签：一号教学楼/艺体馆/创造力中心/图书馆曾被别的标签挡住不显示——
##    本版先做深度遮挡射线检测（被楼体挡住才隐藏），再做屏幕空间去重叠：
##    按优先级排序，低优先级标签可上下微调（最多 4 档 × 19px）避让，实在排不开才隐藏。
## 2) 池塘标签被底部场景按钮栏遮住——标签屏上 y 钳制在视口高 − 84px 以上。
## 3) 窄屏：宽度 < 760 时标签字号缩小、只保留 prio ≤ 4 的主标签。
## 4) 标签锚点贴设施顶部，不再悬空。

var camera: Camera3D
var font: Font # Label3D 不走 Control 主题，main.gd 启动时把中文字体直接赋过来
var occluders: Array[Node3D] = []
var defs: Array[Dictionary] = []
var _last_ms := 0
var _bottom_reserve := 84.0 # 底部场景栏高度 + 边距
var _ray: PhysicsRayQueryParameters3D

func add_label(text: String, color: Color, prio: int, anchor: Vector3, dynamic: String = "") -> Dictionary:
	var l := Label3D.new()
	l.text = text
	if font != null:
		l.font = font
	# fixed_size：标签在屏幕上保持恒定像素尺寸（font_size px），不受相机距离影响。
	# 之前用世界尺寸（pixel_size 0.012、font_size 42 → 约 0.5 世界单位），总览距离 235m 时
	# 只有约 2px，缩成看不见的小点。改 16px 固定尺寸，与去重叠估算（est_h 26、fs 13/15）一致。
	l.fixed_size = true
	l.font_size = 16
	l.modulate = color
	l.outline_size = 4
	l.outline_modulate = Color(1, 1, 1, 0.92)
	l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	l.no_depth_test = false
	l.pixel_size = 0.012
	l.position = anchor
	l.visible = false
	add_child(l)
	var d := {"label": l, "text": text, "color": color, "prio": prio, "anchor": anchor, "dynamic": dynamic, "occ": false}
	defs.append(d)
	return d

func set_dynamic_text(d: Dictionary, text: String) -> void:
	var l: Label3D = d["label"]
	if l.text != text:
		l.text = text

func _ready() -> void:
	_ray = PhysicsRayQueryParameters3D.new()

func _process(_delta: float) -> void:
	var now := Time.get_ticks_msec()
	if now - _last_ms < 150:
		return
	_last_ms = now
	_update()

func _update() -> void:
	if camera == null:
		return
	var vp := get_viewport().get_visible_rect().size
	if vp.x <= 0.0 or vp.y <= 0.0:
		return
	var narrow: bool = vp.x < 760.0
	var space := get_world_3d().direct_space_state
	# 1) 深度遮挡：相机→锚点射线，命中楼体且在锚点前 2m 处才算挡住
	for d in defs:
		var anchor: Vector3 = d["anchor"]
		var to: Vector3 = anchor - camera.global_position
		var dist := to.length()
		d["occ"] = false
		if dist > 3.0:
			_ray.from = camera.global_position
			_ray.to = camera.global_position + to.normalized() * (dist - 2.0)
			_ray.collision_mask = 1
			var hit: Dictionary = space.intersect_ray(_ray)
			if not hit.is_empty():
				d["occ"] = true
	# 2) 按优先级排序，做屏幕空间去重叠
	var sorted: Array = defs.duplicate()
	sorted.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return int(a["prio"]) < int(b["prio"]))
	var placed: Array[Rect2] = []
	for d in sorted:
		var l: Label3D = d["label"]
		if bool(d["occ"]):
			l.visible = false
			continue
		if narrow and int(d["prio"]) > 4:
			l.visible = false
			continue
		var anchor: Vector3 = d["anchor"]
		if camera.is_position_behind(anchor):
			l.visible = false
			continue
		var sp: Vector2 = camera.unproject_position(anchor)
		# 估算牌宽：字数 × 字号（窄屏缩小）
		var fs := 13.0 if narrow else 15.0
		var est_w := minf(170.0, float(l.text.length()) * fs * 0.62 + 30.0)
		var est_h := 26.0
		# 池塘修复：y 钳制在视口高 − 底部预留之上；x 钳制在屏内
		sp.x = clampf(sp.x, est_w / 2.0 + 4.0, vp.x - est_w / 2.0 - 4.0)
		sp.y = clampf(sp.y, 48.0, vp.y - _bottom_reserve)
		var done := false
		var dy := 0.0
		for step in range(4):
			dy = step * 19.0
			var r := Rect2(sp.x - est_w / 2.0, sp.y - est_h + dy, est_w, est_h)
			var hit2 := false
			for p in placed:
				if r.intersects(p):
					hit2 = true
					break
			if not hit2:
				placed.append(r)
				# 把微调量折回 3D：沿相机上方向移动锚点。微调量要随距离缩放——
				# 19px 屏幕位移在总览距离（235m）约合 7 世界单位，近景（17m）约合 0.5，
				# 固定 0.045 在总览下几乎不动。按 dist*0.0016 换算（约 2px/世界单位 @75° fov）。
				var up: Vector3 = camera.global_transform.basis.y
				var fwd: Vector3 = -camera.global_transform.basis.z
				var cam_dist := (anchor - camera.global_position).length()
				var world_dy := dy * cam_dist * 0.0016
				l.position = anchor + up * world_dy - fwd * 0.0
				l.visible = true
				done = true
				break
		if not done:
			l.visible = false
