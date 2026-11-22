extends SceneTree
## 无头逻辑验证：不渲染，只跑代码并检查运行时的实际状态。
## 用法：godot --headless --path . -s tools/verify_fixes.gd
## 检查：P0 面板数值列/标题颜色、P1-1 HintLabel、P1-2 舒适带绿、P1-3 ABC 保供逻辑、
##      P2-3 标签色、P2-5 WxLabel、labels fixed_size、标题/时钟色。
## 每项打印 PASS/FAIL，最后汇总。退出码 0=全过，1=有 FAIL。

var _main: Node = null
var _frames := 0
var _fails := 0
var _passes := 0


func _chk(name: String, ok: bool, detail: String = "") -> void:
	if ok:
		_passes += 1
		print("PASS: ", name, " ", detail)
	else:
		_fails += 1
		print("FAIL: ", name, " ", detail)


func _init() -> void:
	var packed := load("res://scenes/main.tscn") as PackedScene
	_main = packed.instantiate()
	root.add_child(_main)


func _col(c: Color) -> String:
	# 注意：Godot Color 是 float32，hex 解析后 ×255 会差 1（如 0x17→22.99），必须四舍五入不能截断
	return "#%02x%02x%02x" % [int(c.r * 255.0 + 0.5), int(c.g * 255.0 + 0.5), int(c.b * 255.0 + 0.5)]


func _label_color(n: Node) -> Color:
	if n is Label:
		return (n as Label).get_theme_color("font_color")
	return Color(0, 0, 0, 0)


func _process(_delta: float) -> bool:
	_frames += 1
	if _frames < 5:
		return false
	# ---- 顶栏 / 天气 / 提示 ----
	var title := _main.get_node("UI/TopBar/HBox/TitleLabel") as Label
	_chk("TitleLabel 深色 #0f172a", _col(_label_color(title)) == "#0f172a", _col(_label_color(title)))
	var clock := _main.get_node("UI/TopBar/HBox/ClockLabel") as Label
	_chk("ClockLabel 深色 #1e293b", _col(_label_color(clock)) == "#1e293b", _col(_label_color(clock)))
	var tl := _main.get_node("UI/TopBar/HBox/TimeLabel") as Label
	_chk("TimeLabel 深色 #1e293b", _col(_label_color(tl)) == "#1e293b", _col(_label_color(tl)))
	var wx := _main.get_node("UI/WxPill/HBox/WxLabel") as Label
	_chk("WxLabel 深色 #1e293b", _col(_label_color(wx)) == "#1e293b", _col(_label_color(wx)))
	var hint := _main.get_node("UI/HintLabel") as Label
	_chk("HintLabel 深色 #1e293b", _col(_label_color(hint)) == "#1e293b", _col(_label_color(hint)))
	_chk("HintLabel 有白描边", hint.get_theme_color("font_outline_color").a > 0.5 and hint.get_theme_constant("outline_size") >= 4, "outline=" + str(hint.get_theme_constant("outline_size")))
	# ---- 面板标题 ----
	var sp_title := _main.get_node("UI/ScenePanel/VBox/SPTitleRow/SPTitle") as Label
	_chk("SPTitle 深色 #0f172a", _col(_label_color(sp_title)) == "#0f172a", _col(_label_color(sp_title)))
	var abc_title := _main.get_node("UI/ABCPanel/VBox/ABCTitle") as Label
	_chk("ABCTitle 深色 #0f172a", _col(_label_color(abc_title)) == "#0f172a", _col(_label_color(abc_title)))
	var abc_note := _main.get_node("UI/ABCPanel/VBox/ABCNote") as Label
	_chk("ABCNote 深色 #475569", _col(_label_color(abc_note)) == "#475569", _col(_label_color(abc_note)))
	_chk("ABCNote 16px", abc_note.get_theme_font_size("font_size") == 16, str(abc_note.get_theme_font_size("font_size")))
	# ---- 场景面板数值列（调 set_live 生成一行再查） ----
	var panel = _main.get_node("UI/ScenePanel")
	panel.call("set_live", [["储能 SOC", "56% · 215 kWh"]], [])
	var live_box = _main.get_node("UI/ScenePanel/VBox/SPLive")
	var row = live_box.get_child(0)
	var vlab := row.get_child(1) as Label
	_chk("面板数值列深色 #1e293b", _col(_label_color(vlab)) == "#1e293b", _col(_label_color(vlab)))
	_chk("面板数值列 16px", vlab.get_theme_font_size("font_size") == 16, str(vlab.get_theme_font_size("font_size")))
	# ---- 3D 标签 fixed_size ----
	var labels = _main.get_node("Labels")
	var found := false
	for d in labels.defs:
		var l = d["label"] as Label3D
		if l != null and l.text == "一号教学楼":
			found = true
			_chk("Label3D 一号教学楼 fixed_size", l.fixed_size == true, "fixed=" + str(l.fixed_size))
			_chk("Label3D 一号教学楼 font_size 16", l.font_size == 16, "size=" + str(l.font_size))
			_chk("Label3D 一号教学楼有中文字体", l.font != null and l.font.has_char(0x4e00), "font=" + str(l.font != null))
	if not found:
		_chk("Label3D 一号教学楼存在", false, "defs 里没找到")
	# ---- ABC 表格保供列 ----
	var ui = _main.get_node("UI")
	var grid = _main.get_node("UI/ABCPanel/VBox/ABCGrid") as GridContainer
	# 网格按行排列：表头 7 个，A/B/C 各 7 个。保供列是每行第 7 个（索引 6、13、20）
	var cells := grid.get_children()
	_chk("ABC 网格 28 个格（7 表头 + 21 数据）", cells.size() == 28, "size=" + str(cells.size()))
	if cells.size() == 28:
		var a_bk := cells[13] as Label
		var b_bk := cells[20] as Label
		var c_bk := cells[27] as Label
		_chk("A 保供 7.9h 达标（绿）", a_bk.text.find("达标") >= 0 and _col(_label_color(a_bk)) == "#047857", a_bk.text + " " + _col(_label_color(a_bk)))
		_chk("B 保供 4.4h 达标（绿）", b_bk.text.find("达标") >= 0 and _col(_label_color(b_bk)) == "#047857", b_bk.text + " " + _col(_label_color(b_bk)))
		_chk("C 保供 1.6h 不达标（红）", c_bk.text.find("不达标") >= 0 and _col(_label_color(c_bk)) == "#dc2626", c_bk.text + " " + _col(_label_color(c_bk)))
		var b_name := cells[14] as Label
		_chk("B 行名绿色 #047857（bold 不覆盖）", _col(_label_color(b_name)) == "#047857", _col(_label_color(b_name)))
	# ---- 图表舒适带绿（源码级：只查“24–28℃ 舒适带”那行文字色；SOC 线/图例色块用 #059669 是合法的，
	#      它们不是文字，B 报告也认可“色块 + 深色字”模式） ----
	var charts_src := FileAccess.get_file_as_string("res://scripts/charts.gd")
	var band_idx := charts_src.find("24–28℃ 舒适带")
	var band_line := charts_src.substr(band_idx, 120) if band_idx >= 0 else ""
	_chk("charts.gd 舒适带文字用 #047857", band_idx >= 0 and band_line.find("047857") >= 0, band_line.left(80))
	print("VERIFY-SUMMARY: PASS=", _passes, " FAIL=", _fails)
	quit(1 if _fails > 0 else 0)
	return true
