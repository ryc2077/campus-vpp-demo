class_name SimEngine
extends RefCounted
## 96 点（15 分钟一步）能量平衡仿真引擎。
## 移植自原 Three.js Demo buildPlan()：负荷形状、价格时段、碳因子曲线、
## 储能充放电规则与保留线约束保持一致；电价改用 bill.json 的居民峰谷电价
## （平 0.5483 / 峰 0.5583 / 谷 0.3583），碳因子 0.5827。
## 注意：A/B/C 对照表的展示值以 strategies.json 的权威文件值为准，
## 本引擎的实时曲线是日内形状演示，不冒充实测曲线。

const N := 96
const DT := 0.25

var params: Dictionary = {}
var wx: Dictionary = {}
var plan: Dictionary = {}

static func gauss(x: float, mu: float, sig: float) -> float:
	var d: float = (x - mu) / sig
	return exp(-0.5 * d * d)

func sun_shape(h: float) -> float:
	if h > wx["rise"] and h < wx["set"]:
		return sin(PI * (h - wx["rise"]) / (wx["set"] - wx["rise"]))
	return 0.0

func price_at(h: float) -> Dictionary:
	if h >= 23.0 or h < 7.0:
		return {"p": params["price_valley"], "name": "谷段"}
	if (h >= 10.0 and h < 14.0) or (h >= 18.0 and h < 21.0):
		return {"p": params["price_peak"], "name": "峰段"}
	return {"p": params["price_flat"], "name": "平段"}

func cf_at(h: float) -> float:
	var f: float = 1.18 - 0.55 * gauss(h, 12.5, 3.2) + 0.22 * gauss(h, 2.5, 3.0) + 0.10 * gauss(h, 20.0, 2.6)
	return params["cf_avg"] * clampf(f, 0.45, 1.45)

func load_shape(h: float) -> float:
	return 0.30 + 0.16 * gauss(h, 7.8, 1.0) + 0.52 * gauss(h, 10.8, 2.3) + 0.60 * gauss(h, 15.0, 2.6) + 0.34 * gauss(h, 19.6, 1.7)

func shape_max() -> float:
	var m := 0.0
	var h := 0.0
	while h < 24.0:
		m = maxf(m, load_shape(h))
		h += 0.25
	return m

func build(p: Dictionary, weather: Dictionary) -> Dictionary:
	params = p
	wx = weather
	var cap_line := 3000.0 # 实测：4 台主变合计 3000kVA
	var soc_min := 0.10
	var soc_max := 0.95
	var eff := 0.92
	var floor_soc: float = params["reserve_pct"] # B: 0.556 保留线；C: 0.10
	var load: Array[float] = []
	var pv: Array[float] = []
	var price: Array[float] = []
	var cf: Array[float] = []
	var smax := shape_max()
	var day_f: Dictionary = {"load": 1.0, "pv": 1.0}
	var i := 0
	while i < N:
		var h: float = i * DT
		var base: float = params["load_pk"] * day_f["load"] * float(wx["load_factor"]) * load_shape(h) / smax
		var ev_kw: float = 130.0 * params["ev_rate"] * 2.2 * (gauss(h, 9.0, 1.3) + 0.6 * gauss(h, 13.5, 1.6))
		load.append(base + ev_kw)
		var sun_base := sun_shape(h)
		var sun: float = pow(sun_base, 1.3) if sun_base > 0.0 else 0.0
		pv.append(params["pv_cap"] * day_f["pv"] * float(wx["pv_factor"]) * sun * (1.0 + 0.03 * sin(i * 2.7)))
		price.append(price_at(h)["p"])
		cf.append(cf_at(h))
		i += 1
	var ac_flex: float = clampf((params["ac_set"] - 25.5) * 0.09, 0.0, 0.16) * 0.38
	var grid: Array[float] = []
	var batt: Array[float] = []
	var soc_a: Array[float] = []
	var ev_dis: Array[float] = []
	var curt: Array[float] = []
	var soc := 0.90
	i = 0
	while i < N:
		var h: float = i * DT
		var pr: Dictionary = price_at(h)
		var is_peak: bool = pr["name"] == "峰段"
		var is_valley: bool = pr["name"] == "谷段"
		var L: float = load[i]
		var PV: float = pv[i]
		var b := 0.0
		var evd := 0.0
		var g := 0.0
		var ct := 0.0
		var eff_load := L
		if is_peak:
			eff_load = L * (1.0 - ac_flex)
		var net: float = eff_load - PV
		if is_peak and h >= 8.0 and h < 17.0:
			evd = minf(90.0 * params["ev_rate"] * 2.0, maxf(0.0, net) * 0.35)
		if net < 0.0:
			var chg := minf(minf(params["pow"], -net), maxf(0.0, soc_max - soc) * params["cap"] / eff / DT)
			soc += chg * eff * DT / params["cap"]
			b = -chg
			ct = -net - chg
			g = 0.0
		elif is_valley:
			# 条件触发（权威口径）：日常放电只在充电能全部由午间光伏富余承担时进行；
			# 谷段充电仍按规则进行，但放电窗口由峰段规则 + 保留线锁死。
			var room: float = maxf(0.0, 0.90 - soc) * params["cap"] / eff / DT
			var chg3 := minf(params["pow"] * 0.8, room)
			soc += chg3 * eff * DT / params["cap"]
			b = -chg3
			g = net + chg3
		elif is_peak or net + evd > cap_line * 0.92:
			var dis := minf(minf(params["pow"], maxf(0.0, soc - floor_soc) * params["cap"] * eff / DT), maxf(0.0, net - evd))
			soc -= dis * DT / (params["cap"] * eff)
			b = dis
			g = maxf(0.0, net - dis - evd)
		else:
			g = maxf(0.0, net - evd)
		soc = clampf(soc, 0.0, 1.0)
		grid.append(g)
		batt.append(b)
		soc_a.append(soc)
		ev_dis.append(evd)
		curt.append(maxf(0.0, ct))
		i += 1
	var cost := 0.0
	var cost_b := 0.0
	var co2 := 0.0
	var co2_b := 0.0
	var peak := 0.0
	var peak_b := 0.0
	var pv_gen := 0.0
	var thr := 0.0
	var curt_sum := 0.0
	i = 0
	while i < N:
		var g_b: float = maxf(0.0, load[i] - pv[i])
		cost += grid[i] * DT * price[i]
		cost_b += g_b * DT * price[i]
		co2 += grid[i] * DT * cf[i]
		co2_b += g_b * DT * cf[i]
		peak = maxf(peak, grid[i])
		peak_b = maxf(peak_b, g_b)
		pv_gen += pv[i] * DT
		curt_sum += curt[i]
		if batt[i] > 0.0:
			thr += batt[i] * DT
		i += 1
	var self_use: float = clampf((pv_gen - curt_sum * DT) / pv_gen, 0.0, 1.0) if pv_gen > 0.0 else 0.0
	plan = {
		"load": load, "pv": pv, "price": price, "cf": cf,
		"grid": grid, "batt": batt, "soc": soc_a, "ev_dis": ev_dis, "curt": curt,
		"cost": cost, "cost_b": cost_b, "co2": co2, "co2_b": co2_b,
		"peak": peak, "peak_b": peak_b, "cap_line": cap_line,
		"pv_gen": pv_gen, "self_use": self_use, "curt_kwh": curt_sum * DT,
		"cycles": thr / params["cap"] if params["cap"] > 0.0 else 0.0,
		"floor_soc": floor_soc,
	}
	return plan

## 当前时刻（小时，0-24）的仿真状态，供 3D 与面板读取。
func state_at(hour: float) -> Dictionary:
	if plan.is_empty():
		return {"soc": 0.9, "pv": 0.0, "load": 0.0, "grid": 0.0, "batt": 0.0, "ev": 0.0, "hour": hour, "price": 0.0, "cf": 0.0}
	var idx := clampi(int(hour / DT), 0, N - 1)
	return {
		"soc": plan["soc"][idx], "pv": plan["pv"][idx], "load": plan["load"][idx],
		"grid": plan["grid"][idx], "batt": plan["batt"][idx], "ev": plan["ev_dis"][idx],
		"hour": hour, "price": plan["price"][idx], "cf": plan["cf"][idx],
	}

static func fmt_hour(h: float) -> String:
	var hh := int(h)
	var mm := int(round((h - hh) * 60.0))
	if mm == 60:
		hh += 1
		mm = 0
	return "%02d:%02d" % [hh, mm]
