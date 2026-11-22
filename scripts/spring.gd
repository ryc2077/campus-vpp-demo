class_name PressSpringSet
extends RefCounted
## 临界阻尼弹簧（移植 liquid-glass-webgl renderer/spring.ts 的 springStepCritical）。
## 源码参数：TOGGLE_VALUE_K = 1000，ωn = sqrt(1000) ≈ 31.623；沉降阈值 0.003。
## 临界阻尼：无超调、不会弹过头，适合按压反馈（按下 0.97 / 松开 1.0）。
## 闭式解：x(t) = target + (A + B·t)·e^(-ωt)，A = x0 - target，B = v0 + ω·(x0 - target)。
## 替代旧版 tween 按压（TRANS_QUAD 100ms/160ms）：弹簧在中途再按时直接从当前值
## 与当前速度重定向，不需要杀 tween；时间常数 1/ω ≈ 32ms，视觉上约 100–150ms 落位，
## 与 Emil 规则（按钮反馈 100–250ms）一致。

const OMEGA := 31.623
const SETTLE := 0.003

static func step_critical(x: float, v: float, target: float, dt: float, omega: float = OMEGA) -> Vector2:
	var d: float = x - target
	var a: float = d
	var b: float = v + omega * d
	var e: float = exp(-omega * dt)
	var nx: float = target + (a + b * dt) * e
	var nv: float = (b - omega * (a + b * dt)) * e
	if absf(nx - target) < SETTLE and absf(nv) < SETTLE:
		nx = target
		nv = 0.0
	return Vector2(nx, nv)

var _state: Dictionary = {} # Button -> [x, v, target]

func attach(b: Button) -> void:
	_state[b] = [1.0, 0.0, 1.0]
	b.button_down.connect(func() -> void: _set_target(b, 0.97))
	b.button_up.connect(func() -> void: _set_target(b, 1.0))

func _set_target(b: Button, t: float) -> void:
	if _state.has(b):
		(_state[b] as Array)[2] = t

func tick(delta: float) -> void:
	for b in _state.keys():
		if not is_instance_valid(b):
			_state.erase(b)
			continue
		var s: Array = _state[b]
		var r := PressSpringSet.step_critical(float(s[0]), float(s[1]), float(s[2]), delta)
		s[0] = r.x
		s[1] = r.y
		# 按钮缩放只动 transform；pivot 每帧对齐中心，避免尺寸变化后偏心
		b.pivot_offset = b.size / 2.0
		b.scale = Vector2(r.x, r.x)
