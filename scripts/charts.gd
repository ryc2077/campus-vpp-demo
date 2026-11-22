class_name Charts
extends Control
## 自定义曲线图（Control._draw）：24 小时运行曲线 + 教室温度曲线。
## 窄屏修复：宽度 < 560 时横轴只标 0/6/12/18/24 时，避免时间字拥挤；
## 图例改放图内左上角横排，不与刻度重叠。
##
## UI/UX Pro Max §10（图表不只靠颜色区分）：
##  - 每条系列有线型：负荷/光伏/购电实线、储能虚线、SOC 面积+实线；
##    温度图：拉闸虚线、恒温点线、当前策略实线+关键点圆点。
##  - 图例 = 色块 + 深色文字 + 当前值（不再用彩色文字当唯一标识）；
##    轴字 #64748b 在白底上约 4.8:1（旧 #7d97ad 只有约 3.3:1，不达标）。
##  - 图例两行（带当前值放不下一行时），pad_t 相应加到 36。

var mode := "day" # "day" | "temp"
var plan: Dictionary = {}
var cls_results: Dictionary = {}
var cls_strategy := "opt"
var hour := 12.0
var reserve_pct := 0.556

const AXIS_COL := Color("#64748b") # 轴字/刻度：白底约 4.8:1
const TEXT_COL := Color("#1e293b") # 图例/标注文字
const LABEL_SIZE := 12

func set_day(p: Dictionary, h: float, res_pct: float) -> void:
	mode = "day"
	plan = p
	hour = h
	reserve_pct = res_pct
	queue_redraw()

func set_temp(results: Dictionary, strategy: String, h: float) -> void:
	mode = "temp"
	cls_results = results
	cls_strategy = strategy
	hour = h
	queue_redraw()

func _draw() -> void:
	if mode == "temp":
		_draw_temp()
	else:
		_draw_day()

func _x_ticks(w: float) -> Array:
	# 窄屏只标 6 小时间隔
	if w < 560.0:
		return [0, 6, 12, 18, 24]
	return [0, 3, 6, 9, 12, 15, 18, 21, 24]

## 图例项：色块（10×10）+ 深色文字（含当前值）。返回画完后的 x。
func _legend_item(font: Font, x: float, y: float, text: String, col: Color) -> float:
	draw_rect(Rect2(x, y - 9, 10, 10), col)
	draw_string(font, Vector2(x + 14, y), text, HORIZONTAL_ALIGNMENT_LEFT, -1, LABEL_SIZE, TEXT_COL)
	return x + 14.0 + float(text.length()) * 7.0 + 14.0

func _draw_dashed_series(arr: Array, x_of: Callable, y_of: Callable, col: Color, width: float, dash_len: float = 6.0, gap_len: float = 4.0) -> void:
	# 沿折线走虚线：dash 实、gap 空，按线段长度切分
	var prev := Vector2.ZERO
	var have_prev := false
	var remain_dash := dash_len
	var drawing := true
	for i in range(arr.size()):
		var p := Vector2(x_of.call(i), y_of.call(float(arr[i])))
		if have_prev:
			var seg: Vector2 = p - prev
			var seg_len := seg.length()
			var dir: Vector2 = seg / maxf(seg_len, 0.001)
			var pos := prev
			var left := seg_len
			while left > 0.001:
				var step := minf(remain_dash, left)
				var nxt: Vector2 = pos + dir * step
				if drawing:
					draw_line(pos, nxt, col, width, true)
				pos = nxt
				left -= step
				remain_dash -= step
				if remain_dash <= 0.001:
					drawing = not drawing
					remain_dash = dash_len if drawing else gap_len
		prev = p
		have_prev = true

func _draw_day() -> void:
	var W := size.x
	var H := size.y
	if W < 40.0 or H < 40.0 or plan.is_empty():
		return
	draw_rect(Rect2(0, 0, W, H), Color.WHITE)
	var pad_l := 40.0
	var pad_r := 8.0
	var pad_t := 36.0
	var pad_b := 20.0
	var iw := W - pad_l - pad_r
	var ih := H - pad_t - pad_b
	var max_p := 300.0
	for k in ["load", "pv", "grid", "batt"]:
		var arr: Array = plan[k]
		for v in arr:
			max_p = maxf(max_p, float(v))
	max_p *= 1.08
	var x_of := func(i: int) -> float: return pad_l + iw * float(i) / 95.0
	var y_of := func(v: float) -> float: return pad_t + ih * (1.0 - v / max_p)
	var y_soc := func(s: float) -> float: return pad_t + ih * (1.0 - s)
	# 峰谷底色带（按 15 分钟点）
	for i in range(96):
		var h := i * 0.25
		var col := Color(0, 0, 0, 0)
		if h >= 23.0 or h < 7.0:
			col = Color(0.02, 0.59, 0.42, 0.07)
		elif (h >= 10.0 and h < 14.0) or (h >= 18.0 and h < 21.0):
			col = Color(0.86, 0.15, 0.15, 0.06)
		else:
			continue
		draw_rect(Rect2(x_of.call(i), pad_t, iw / 96.0 + 1.0, ih), col)
	# 网格 + 纵轴
	var font := ThemeDB.fallback_font
	for gi in range(5):
		var v: float = max_p * float(gi) / 4.0
		var y: float = y_of.call(v)
		draw_line(Vector2(pad_l, y), Vector2(pad_l + iw, y), Color("#dde9f2"), 1.0)
		draw_string(font, Vector2(4, y + 4), str(int(v)), HORIZONTAL_ALIGNMENT_LEFT, -1, LABEL_SIZE, AXIS_COL)
	# 横轴（窄屏自适应间隔）；末刻度 "24:00" 约 30px 宽，左对齐画在 x-13 会超出右缘约 14px，
	# 钳制到 W-32 让它右对齐收进图内（clip_contents=false 时本会透出绘制）。
	for hx in _x_ticks(W):
		var hx_f: float = float(hx)
		var x: float = pad_l + iw * hx_f / 24.0
		var tx: float = minf(x - 13.0, W - 32.0)
		draw_string(font, Vector2(tx, H - 5), "%02d:00" % hx, HORIZONTAL_ALIGNMENT_LEFT, -1, LABEL_SIZE, AXIS_COL)
	# 保留线
	var res_y: float = y_soc.call(reserve_pct)
	draw_dashed_line(Vector2(pad_l, res_y), Vector2(pad_l + iw, res_y), Color(0.86, 0.15, 0.15, 0.7), 1.5, 5.0)
	draw_string(font, Vector2(pad_l + 4, res_y - 4), "保留线 %.0f%%" % (reserve_pct * 100.0), HORIZONTAL_ALIGNMENT_LEFT, -1, LABEL_SIZE, Color("#dc2626"))
	# 图例（两行，色块 + 深色文字 + 当前值；不只靠颜色）
	var idx := clampi(int(round(clampf(hour, 0.0, 24.0) * 4.0)), 0, 95)
	var lx := pad_l + 4.0
	lx = _legend_item(font, lx, pad_t - 20, "负荷 %d" % int(round(float((plan["load"] as Array)[idx]))), Color("#db2777"))
	lx = _legend_item(font, lx, pad_t - 20, "光伏 %d" % int(round(float((plan["pv"] as Array)[idx]))), Color("#ca8a04"))
	lx = _legend_item(font, lx, pad_t - 20, "购电 %d" % int(round(float((plan["grid"] as Array)[idx]))), Color("#0284c7"))
	lx = pad_l + 4.0
	lx = _legend_item(font, lx, pad_t - 6, "储能 %d（虚线）" % int(round(float((plan["batt"] as Array)[idx]))), Color("#ea580c"))
	lx = _legend_item(font, lx, pad_t - 6, "SOC %d%%" % int(round(float((plan["soc"] as Array)[idx]) * 100.0)), Color("#059669"))
	# SOC 面积
	var soc_pts := PackedVector2Array()
	var soc_arr: Array = plan["soc"]
	for i in range(96):
		soc_pts.append(Vector2(x_of.call(i), y_soc.call(float(soc_arr[i]))))
	soc_pts.append(Vector2(x_of.call(95), pad_t + ih))
	soc_pts.append(Vector2(x_of.call(0), pad_t + ih))
	draw_colored_polygon(soc_pts, Color(0.02, 0.59, 0.42, 0.10))
	_draw_series(plan["load"], x_of, y_of, Color("#db2777"), 1.8)
	_draw_series(plan["pv"], x_of, y_of, Color("#ca8a04"), 1.8)
	_draw_series(plan["grid"], x_of, y_of, Color("#0284c7"), 1.8)
	_draw_dashed_series(plan["batt"], x_of, y_of, Color("#ea580c"), 1.8)
	_draw_series(plan["soc"], x_of, y_soc, Color("#059669"), 1.6)
	# 播放头
	var xi := pad_l + iw * clampf(hour, 0.0, 24.0) / 24.0
	draw_line(Vector2(xi, pad_t), Vector2(xi, pad_t + ih), Color(0.01, 0.52, 0.78, 0.55), 1.2)

func _draw_series(arr: Array, x_of: Callable, y_of: Callable, col: Color, width: float) -> void:
	var pts := PackedVector2Array()
	for i in range(arr.size()):
		pts.append(Vector2(x_of.call(i), y_of.call(float(arr[i]))))
	if pts.size() > 1:
		draw_polyline(pts, col, width, true)

func _temp_at(temps: Array, h: float) -> float:
	var i := clampi(int(round((h - 6.0) * 12.0)), 0, temps.size() - 1)
	return float(temps[i])

func _draw_temp() -> void:
	var W := size.x
	var H := size.y
	if W < 40.0 or H < 40.0 or cls_results.is_empty():
		return
	draw_rect(Rect2(0, 0, W, H), Color.WHITE)
	var pad_l := 34.0
	var pad_r := 8.0
	var pad_t := 36.0
	var pad_b := 20.0
	var iw := W - pad_l - pad_r
	var ih := H - pad_t - pad_b
	var t_min := 20.0
	var t_max := 37.0
	var x_of := func(h: float) -> float: return pad_l + iw * (h - 6.0) / 13.0
	var y_of := func(t: float) -> float: return pad_t + ih * (1.0 - (t - t_min) / (t_max - t_min))
	# 舒适带 24–28
	draw_rect(Rect2(pad_l, y_of.call(28.0), iw, y_of.call(24.0) - y_of.call(28.0)), Color(0.02, 0.59, 0.42, 0.10))
	var font := ThemeDB.fallback_font
	for tv in range(22, 37, 4):
		draw_line(Vector2(pad_l, y_of.call(float(tv))), Vector2(pad_l + iw, y_of.call(float(tv))), Color("#dde9f2"), 1.0)
		draw_string(font, Vector2(4, y_of.call(float(tv)) + 4), str(tv) + "°", HORIZONTAL_ALIGNMENT_LEFT, -1, LABEL_SIZE, AXIS_COL)
	for hx in _x_ticks(W):
		if hx < 6 or hx > 19:
			continue
		draw_string(font, Vector2(x_of.call(float(hx)) - 10, H - 5), str(hx) + "时", HORIZONTAL_ALIGNMENT_LEFT, -1, LABEL_SIZE, AXIS_COL)
	draw_string(font, Vector2(pad_l + 4, y_of.call(28.0) - 5), "24–28℃ 舒适带", HORIZONTAL_ALIGNMENT_LEFT, -1, LABEL_SIZE, Color("#047857"))
	# 图例（色块 + 深色文字 + 当前时刻温度；线型各不相同）
	var gate_t := _temp_at(cls_results["gate"]["temps"], hour)
	var const_t := _temp_at(cls_results["const"]["temps"], hour)
	var cur_t := _temp_at(cls_results[cls_strategy]["temps"], hour)
	var lx := pad_l + 4.0
	lx = _legend_item(font, lx, pad_t - 20, "拉闸 %.1f℃（虚线）" % gate_t, Color("#dc2626"))
	lx = _legend_item(font, lx, pad_t - 20, "恒温26℃ %.1f℃（点线）" % const_t, Color("#d97706"))
	lx = pad_l + 4.0
	lx = _legend_item(font, lx, pad_t - 6, "预冷+间歇 %.1f℃（实线）" % cur_t, Color("#059669"))
	var draw_temps := func(temps: Array, col: Color, width: float) -> void:
		var pts := PackedVector2Array()
		for i in range(temps.size()):
			var h := 6.0 + float(i) / 12.0
			pts.append(Vector2(x_of.call(h), y_of.call(clampf(float(temps[i]), t_min, t_max))))
		if pts.size() > 1:
			draw_polyline(pts, col, width, true)
	# 拉闸虚线（淡）、恒温点线（淡）、当前策略实线（粗）+ 关键点圆点
	_draw_dashed_series(cls_results["gate"]["temps"], func(i: int) -> float: return x_of.call(6.0 + float(i) / 12.0), func(v: float) -> float: return y_of.call(clampf(v, t_min, t_max)), Color(0.86, 0.15, 0.15, 0.45), 1.8, 6.0, 4.0)
	_draw_dashed_series(cls_results["const"]["temps"], func(i: int) -> float: return x_of.call(6.0 + float(i) / 12.0), func(v: float) -> float: return y_of.call(clampf(v, t_min, t_max)), Color(0.85, 0.47, 0.02, 0.55), 1.8, 2.0, 3.0)
	draw_temps.call(cls_results[cls_strategy]["temps"], Color("#059669"), 2.4)
	for mh in [8.0, 12.0, 14.0, 17.5]:
		var mt := _temp_at(cls_results[cls_strategy]["temps"], mh)
		draw_circle(Vector2(x_of.call(mh), y_of.call(clampf(mt, t_min, t_max))), 3.0, Color("#059669"))
	var px: float = x_of.call(clampf(hour, 6.0, 19.0))
	draw_line(Vector2(px, pad_t), Vector2(px, pad_t + ih), Color(0.01, 0.52, 0.78, 0.6), 1.6)
