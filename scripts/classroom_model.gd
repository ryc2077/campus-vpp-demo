class_name ClassroomModel
extends RefCounted
## 模型一：教室 2 台 5 匹空调 · 一阶热惯性 · 三种策略同台对比。
## 移植自原 Demo simulateClassroom()：铭牌单台制冷 12.15kW / 输入 3.5kW，
## 每间 2 台；降温速率 3.1℃/h 为模型参数，温度序列未实测、待校准。
## 舒适带 24–28℃；作息 8–12、14–17.5 上课（情景设定）。

var cfg: Dictionary = {}
var wx: Dictionary = {}
var price_fn: Callable
var sun_fn: Callable

func _init(c: Dictionary, w: Dictionary, pfn: Callable, sfn: Callable) -> void:
	cfg = c
	wx = w
	price_fn = pfn
	sun_fn = sfn

func tout(h: float) -> float:
	var peak := 35.0 + float(wx.get("tout_delta", 0.0))
	if h >= 6.0 and h <= 21.0:
		var s := sin(PI * (h - 8.5) / 13.0)
		if s < 0.0:
			s *= 0.4
		return peak - 7.0 + 7.0 * s
	return peak - 8.5

func occ(h: float) -> float:
	if h >= 8.0 and h < 12.0:
		return 1.0
	if h >= 12.0 and h < 14.0:
		return 0.15
	if h >= 14.0 and h < 17.5:
		return 1.0
	if h >= 7.0 and h < 8.0:
		return 0.1
	return 0.05

func simulate(strategy: String) -> Dictionary:
	var dt: float = cfg["model"]["step_h"]
	var start_h: float = cfg["model"]["start_h"]
	var steps := int(round((cfg["model"]["end_h"] - start_h) / dt))
	var T := tout(start_h) - 1.0
	var on := false
	var temps: Array[float] = []
	var ac_on: Array[int] = []
	var kwh := 0.0
	var cost := 0.0
	var class_steps := 0
	var comfort_steps := 0
	var discomfort := 0.0
	var elec_kw: float = cfg["ac"]["units_per_room"] * cfg["ac"]["cool_input_kw_each"]
	var s := 0
	while s <= steps:
		var h: float = start_h + s * dt
		temps.append(T)
		ac_on.append(1 if on else 0)
		if s == steps:
			break
		var in_class := (h >= 8.0 and h < 12.0) or (h >= 14.0 and h < 17.5)
		var allowed := false
		var set := 26.0
		if strategy == "gate":
			allowed = in_class
			set = 23.0
		elif strategy == "const":
			allowed = h >= 7.5 and h < 17.5
			set = 26.0
		else:
			if h >= 7.0 and h < 8.0:
				allowed = true
				set = 24.8
			elif h >= 8.0 and h < 17.5:
				allowed = true
				var pr: Dictionary = price_fn.call(h)
				set = 27.4 if pr["name"] == "峰段" else 26.2
		if not allowed:
			on = false
		else:
			if not on and T > set + 0.35:
				on = true
			if on and T < set - 0.35:
				on = false
		var daylight: float = sun_fn.call(h)
		T += (cfg["model"]["thermal_k"] * (tout(h) - T) + cfg["model"]["occupancy_gain"] * occ(h) + cfg["model"]["solar_gain"] * daylight * float(wx.get("pv_factor", 1.0)) - (cfg["model"]["cool_rate_c_per_h"] if on else 0.0)) * dt
		if on:
			var e := elec_kw * dt
			kwh += e
			var pr2: Dictionary = price_fn.call(h)
			cost += e * float(pr2["p"])
		if in_class:
			class_steps += 1
			if T >= 24.0 and T <= 28.0:
				comfort_steps += 1
			discomfort += maxf(0.0, maxf(24.0 - T, T - 28.0)) * dt
		s += 1
	return {
		"temps": temps, "ac_on": ac_on, "start_h": start_h, "step_h": dt,
		"kwh": kwh, "cost": cost,
		"comfort_pct": 100.0 * comfort_steps / class_steps if class_steps > 0 else 0.0,
		"discomfort": discomfort,
	}

func at(res: Dictionary, h: float) -> Dictionary:
	var idx := clampi(int(round((h - float(res["start_h"])) / float(res["step_h"]))), 0, (res["temps"] as Array).size() - 1)
	return {"T": res["temps"][idx], "on": res["ac_on"][idx] == 1}
