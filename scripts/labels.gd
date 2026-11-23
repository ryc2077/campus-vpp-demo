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
	# Root cause of the giant blurry labels (see _update for the per-frame correction):
	# docs say fixed_size renders "the same size as if the camera was 1.0 units away",
	# so screen px = font_size * pixel_size * vp_h / (2*tan(fov/2)) at any distance.
	# Old values font_size 16 * pixel_size 0.012 = 0.192 world units -> ~133 screen px
	# at 720p / 55 deg fov, and outline 4 -> ~33 screen px of outline: huge + blurry.
	# Fix: large font_size (64, crisp glyph raster) with a matching small pixel_size so
	# the on-screen height is ~16px; outline scaled in proportion (4 @ 16 -> 16 @ 64)
	# to keep the same ~4px screen outline. pixel_size below is the 720p reference
	# value; _update() recomputes it from the live viewport height every 0.15s.
	l.fixed_size = true
	l.font_size = 64
	l.modulate = color
	l.outline_size = 16
	l.outline_modulate = Color(1, 1, 1, 0.92)
	l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	l.no_depth_test = false
	l.pixel_size = 0.0003615
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
	# Screen size correction (fixed_size normalises distance to 1.0, so distance
	# drops out; only viewport height and fov matter):
	#   screen_px = font_size * pixel_size * vp_h / (2*tan(fov/2))
	# Solve pixel_size for the target on-screen height (16px, 13px narrow).
	# This also keeps the size right if the window is resized to another height.
	var target_px := 13.0 if narrow else 16.0
	var px_per_world := vp.y / (2.0 * tan(deg_to_rad(camera.fov * 0.5)))
	var px_size := target_px / (64.0 * px_per_world)
	for d0 in defs:
		(d0["label"] as Label3D).pixel_size = px_size
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
		# Estimate the on-screen box from the real font metrics at the target
		# screen size. The old estimate (chars * 15 * 0.62 + 30) under-measured
		# CJK text: one hanzi is ~1em wide, not 0.62em, so long labels overlapped
		# even when the estimator thought they were clear. +12px covers the
		# white outline + a small gap; est_h = text height + outline.
		var est_w: float
		var est_h: float = target_px + 10.0
		if font != null:
			var m := font.get_string_size(l.text, HORIZONTAL_ALIGNMENT_LEFT, -1, int(target_px))
			est_w = minf(220.0, m.x + 12.0)
		else:
			est_w = minf(220.0, float(l.text.length()) * target_px + 30.0)
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
				# 把微调量折回 3D：沿相机上方向移动锚点。19px 屏幕位移对应的世界位移
				# 是 dy * dist / px_per_world（px_per_world = vp_h / (2*tan(fov/2))，
				# 上面已算出；旧系数 0.0016 是 vp_h≈650 时的近似值，现用精确值）。
				var up: Vector3 = camera.global_transform.basis.y
				var fwd: Vector3 = -camera.global_transform.basis.z
				var cam_dist := (anchor - camera.global_position).length()
				var world_dy := dy * cam_dist / px_per_world
				l.position = anchor + up * world_dy - fwd * 0.0
				l.visible = true
				done = true
				break
		if not done:
			l.visible = false
