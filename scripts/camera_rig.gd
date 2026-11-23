class_name CameraRig
extends Camera3D
## 轨道相机：方位角 az / 俯仰角 el / 距离 dist / 目标点 target。
## fly_to()：强 ease-out 缓动 + 弧线抬升，单段 1000ms；用户拖动/滚轮即取消。
## 场景内限位：轨道状态钳制 + 相机位置盒钳制（防穿模核心，移植原 Demo SCENE_LIM）。

signal flight_finished

var az := 0.78
var el := 0.55
var dist := 275.0
var target := Vector3(-6, 2, 4)

var _fly: Dictionary = {}
var _limits: Dictionary = {}
var _limits_armed := false
var _dragging := false
var _last_pointer: Vector2 = Vector2.ZERO
var _pinch_d := 0.0
var _pointers: Dictionary = {}
var auto_rotate := false
## 去 AI 味 / 无障碍：prefers-reduced-motion 时飞行改为直接落位（不做 swoop），
## 面板只做 200ms 透明度变化。由 main.gd 经 JS matchMedia 或 ?reduced=1 设置。
var reduced_motion := false
## 慢速检查：?slowmo=N 时飞行时长 ×N，供逐帧检查缓动与弧线。
var slowmo := 1.0

func set_limits(lim: Dictionary) -> void:
	_limits = lim

func arm_limits(armed: bool) -> void:
	_limits_armed = armed

func cancel_flight() -> void:
	_fly = {}

func is_flying() -> bool:
	return not _fly.is_empty()

## goal: {"az":..,"el":..,"dist":..,"target":[x,y,z]} ；dur_ms 默认 1000。
## 缓动：强 ease-out cubic-bezier(0.23,1,0.32,1) 的等价曲线（easeOutCubic 近似），
## 进入/退出一律 ease-out，绝不用 ease-in 做进入（emil-design-eng / review-animations）。
func fly_to(goal: Dictionary, dur_ms: int = 1000, on_done: Callable = Callable()) -> void:
	if reduced_motion:
		_snap_to_goal(goal)
		flight_finished.emit()
		if on_done.is_valid():
			on_done.call()
		return
	var d_az: float = atan2(sin(float(goal["az"]) - az), cos(float(goal["az"]) - az))
	var t: Array = goal["target"]
	_fly = {
		"start_ms": Time.get_ticks_msec(),
		"dur_ms": int(dur_ms * slowmo),
		"on_done": on_done,
		"from": {"az": az, "el": el, "dist": dist, "target": target},
		"to": {"az": az + d_az, "el": float(goal["el"]), "dist": float(goal["dist"]), "target": Vector3(t[0], t[1], t[2])},
	}

func _snap_to_goal(goal: Dictionary) -> void:
	var t: Array = goal["target"]
	az = float(goal["az"])
	el = float(goal["el"])
	dist = float(goal["dist"])
	target = Vector3(t[0], t[1], t[2])
	_fly = {}

## 强 ease-out：cubic-bezier(0.23,1,0.32,1) 的近似（easeOutCubic）。
## 起步快、落点速度归零；同曲线用于飞行与 UI（TRANS_CUBIC + EASE_OUT）。
static func _ease_out_strong(u: float) -> float:
	return 1.0 - pow(1.0 - u, 3.0)

## 冻结帧检查：把 from→to 的飞行在进度 u 处求值并直接落位（?freeze=0.5 截图用）。
func apply_eased_between(from_cam: Dictionary, to_cam: Dictionary, u: float) -> void:
	var fe := _ease_out_strong(clampf(u, 0.0, 1.0))
	var arc := sin(fe * PI)
	var ft: Array = from_cam["target"]
	var tt: Array = to_cam["target"]
	var d_az: float = atan2(sin(float(to_cam["az"]) - float(from_cam["az"])), cos(float(to_cam["az"]) - float(from_cam["az"])))
	az = float(from_cam["az"]) + d_az * fe
	el = float(from_cam["el"]) + (float(to_cam["el"]) - float(from_cam["el"])) * fe + arc * 0.10
	dist = float(from_cam["dist"]) + (float(to_cam["dist"]) - float(from_cam["dist"])) * fe + arc * 20.0
	target = Vector3(ft[0], ft[1], ft[2]).lerp(Vector3(tt[0], tt[1], tt[2]), fe)
	_fly = {}

func _clamp_orbit() -> void:
	if _limits.is_empty():
		el = clampf(el, 0.14, 1.25)
		dist = clampf(dist, 95.0, 420.0)
		return
	var lr: Array = _limits.get("dist", [95.0, 420.0])
	var er: Array = _limits.get("el", [0.14, 1.25])
	el = clampf(el, float(er[0]), float(er[1]))
	dist = clampf(dist, float(lr[0]), float(lr[1]))
	if _limits.has("target_box"):
		var tb: Array = _limits["target_box"]
		target.x = clampf(target.x, float(tb[0][0]), float(tb[1][0]))
		target.y = clampf(target.y, float(tb[0][1]), float(tb[1][1]))
		target.z = clampf(target.z, float(tb[0][2]), float(tb[1][2]))

func _process(delta: float) -> void:
	if auto_rotate and _fly.is_empty():
		az += delta * 0.12
	if not _fly.is_empty():
		var now_ms := Time.get_ticks_msec()
		var u: float = clampf(float(now_ms - int(_fly["start_ms"])) / float(_fly["dur_ms"]), 0.0, 1.0)
		var fe := _ease_out_strong(u)
		var arc := sin(fe * PI)
		var f: Dictionary = _fly["from"]
		var t: Dictionary = _fly["to"]
		az = float(f["az"]) + (float(t["az"]) - float(f["az"])) * fe
		el = float(f["el"]) + (float(t["el"]) - float(f["el"])) * fe + arc * 0.10
		dist = float(f["dist"]) + (float(t["dist"]) - float(f["dist"])) * fe + arc * 20.0
		var ft: Vector3 = f["target"]
		var tt: Vector3 = t["target"]
		target = ft.lerp(tt, fe)
		if u >= 1.0:
			var cb: Callable = _fly["on_done"]
			_fly = {}
			flight_finished.emit()
			if cb.is_valid():
				cb.call()
	elif _limits_armed:
		_clamp_orbit()
	# 由轨道状态算相机位置；位置盒钳制（撞墙/撞天花停在墙面内侧滑动）
	var pos := Vector3(
		target.x + dist * cos(el) * sin(az),
		target.y + dist * sin(el),
		target.z + dist * cos(el) * cos(az)
	)
	if _limits_armed and _limits.has("camera_box"):
		var cbx: Array = _limits["camera_box"]
		pos.x = clampf(pos.x, float(cbx[0][0]), float(cbx[1][0]))
		pos.y = clampf(pos.y, float(cbx[0][1]), float(cbx[1][1]))
		pos.z = clampf(pos.z, float(cbx[0][2]), float(cbx[1][2]))
	position = pos
	look_at(target, Vector3.UP)

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.button_index == MOUSE_BUTTON_WHEEL_UP or mb.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			cancel_flight()
			var f := 1.0 + (0.09 if mb.button_index == MOUSE_BUTTON_WHEEL_DOWN else -0.09)
			dist = clampf(dist * f, 30.0, 900.0)
			if _limits_armed:
				_clamp_orbit()
		elif mb.button_index == MOUSE_BUTTON_LEFT:
			if mb.pressed:
				_dragging = true
				cancel_flight()
				_last_pointer = mb.position
			else:
				_dragging = false
	elif event is InputEventMouseMotion:
		var mm := event as InputEventMouseMotion
		if _dragging:
			var d: Vector2 = mm.position - _last_pointer
			_last_pointer = mm.position
			az -= d.x * 0.006
			var el_min := 0.14
			var el_max := 1.25
			if not _limits.is_empty() and _limits.has("el"):
				el_min = float(_limits["el"][0])
				el_max = float(_limits["el"][1])
			el = clampf(el + d.y * 0.004, el_min, el_max)
	elif event is InputEventScreenTouch:
		var st := event as InputEventScreenTouch
		if st.pressed:
			_pointers[st.index] = st.position
			cancel_flight()
		else:
			_pointers.erase(st.index)
			_pinch_d = 0.0
	elif event is InputEventScreenDrag:
		var sd := event as InputEventScreenDrag
		if _pointers.has(sd.index):
			var prev: Vector2 = _pointers[sd.index]
			var dd: Vector2 = sd.position - prev
			_pointers[sd.index] = sd.position
			if _pointers.size() == 1:
				az -= dd.x * 0.006
				el = clampf(el + dd.y * 0.004, 0.14, 1.25)
			elif _pointers.size() == 2:
				var pts: Array = _pointers.values()
				var d := (pts[0] as Vector2).distance_to(pts[1] as Vector2)
				if _pinch_d > 0.0:
					dist = clampf(dist * _pinch_d / maxf(30.0, d), 30.0, 900.0)
				_pinch_d = d
