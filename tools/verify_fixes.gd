extends SceneTree
## 无头逻辑验证：不渲染，只跑代码并检查运行时的实际状态。
## 用法：godot --headless --path . -s tools/verify_fixes.gd
## 检查：P0 面板数值列/标题颜色、P1-1 HintLabel、P1-2 舒适带绿、P1-3 ABC 保供逻辑、
##      P2-3 标签色、P2-5 WxLabel、labels fixed_size、标题/时钟色、
##      屋顶光伏/艺体馆标签净空（总览 + 冻结帧，1280×720）、
##      池塘标签不进场景栏（总览）+ 屏内标签栏带扫查（储能场景/总览/冻结帧）。
## 每项打印 PASS/FAIL，最后汇总。退出码 0=全过，1=有 FAIL。

var _main: Node = null
var _frames := 0
var _fails := 0
var _passes := 0
var _phase := 0


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


func _labels_rect(labels: Node, d: Dictionary) -> Rect2:
	# 与 labels.gd 同口径的渲染字盒：实测字宽 ×1.25 + 20px 裕量，高 30px，
	# 中心 = 相机对 Label3D 实际位置的投影（不是锚点投影；钳制/档位折回后两者会差几十 px）。
	var l: Label3D = d["label"]
	var cam: Camera3D = labels.camera as Camera3D
	var sp: Vector2 = cam.unproject_position(l.position)
	var w: float = 100.0
	var font: Font = labels.font
	if font != null:
		var m: Vector2 = font.get_string_size(l.text, HORIZONTAL_ALIGNMENT_LEFT, -1, 16)
		w = minf(260.0, m.x * 1.25 + 20.0)
	return Rect2(sp.x - w / 2.0, sp.y - 15.0, w, 30.0)


func _labels_pair(labels: Node) -> Array:
	# [屋顶光伏 def, 艺体馆 def]，找不到时对应位为空字典。
	var pv := {}
	var gym := {}
	for d in labels.defs:
		if String(d["text"]) == "屋顶光伏":
			pv = d
		elif String(d["text"]) == "艺体馆":
			gym = d
	return [pv, gym]


func _labels_pair_clear(labels: Node, min_gap: float) -> bool:
	# 两标签都可见、渲染字盒不相交、且盒间净空 ≥ min_gap（横向重叠时算纵向净空）。
	var pair := _labels_pair(labels)
	var pv: Dictionary = pair[0]
	var gym: Dictionary = pair[1]
	if pv.is_empty() or gym.is_empty():
		return false
	var lp: Label3D = pv["label"]
	var lg: Label3D = gym["label"]
	if not lp.visible or not lg.visible:
		return false
	var rp := _labels_rect(labels, pv)
	var rg := _labels_rect(labels, gym)
	if rp.intersects(rg):
		return false
	if rp.end.x <= rg.position.x or rg.end.x <= rp.position.x:
		return true # 横向不重叠，纵向净空不适用
	var gap: float
	if rp.end.y <= rg.position.y:
		gap = rg.position.y - rp.end.y
	else:
		gap = rp.position.y - rg.end.y
	return gap >= min_gap


func _labels_pair_detail(labels: Node) -> String:
	var pair := _labels_pair(labels)
	var pv: Dictionary = pair[0]
	var gym: Dictionary = pair[1]
	if pv.is_empty() or gym.is_empty():
		return "defs 里没找到"
	var lp: Label3D = pv["label"]
	var lg: Label3D = gym["label"]
	if not lp.visible or not lg.visible:
		return "visible=" + str(lp.visible) + "/" + str(lg.visible)
	return "pv=" + str(_labels_rect(labels, pv)) + " gym=" + str(_labels_rect(labels, gym))


func _labels_band_detail(labels: Node) -> Array:
	# [是否全部通过, 详情]：屏内可见标签的渲染中心不得落进顶栏带（y<72）或
	# 场景栏带（y652–708）；留余量：要求 90≤y≤642。屏外标签（中心越界）不审——
	# 它们不在画面内，x 钳制未折回的已知遗留也不在本轮范围。
	# 口径与 labels.gd 的栏带守卫一致：顶栏守卫保盒顶 ≥80（中心 ≥95），
	# 场景栏守卫保中心 ≤636；渲染中心 = rect 中心时两者即栏带外的保证。
	var cam: Camera3D = labels.camera as Camera3D
	var bad: Array[String] = []
	var n := 0
	for d in labels.defs:
		var l: Label3D = d["label"]
		if not l.visible:
			continue
		var sp: Vector2 = cam.unproject_position(l.position)
		if sp.x < 0.0 or sp.x > 1280.0 or sp.y < 0.0 or sp.y > 720.0:
			continue
		n += 1
		if sp.y < 90.0 or sp.y > 642.0:
			bad.append(String(d["text"]) + " y=" + str(sp.y))
	return [bad.is_empty(), "onscreen=" + str(n) + " bad=[" + ", ".join(bad) + "]"]


func _process(_delta: float) -> bool:
	_frames += 1
	if _frames < 5:
		return false
	# 防空转：检查中途报错会跳过 quit()、下帧重跑、无限循环（曾在 Actions 上刷出 193MB 日志）。
	# 60 帧还没跑完就直接失败退出；场景脚本没挂上也立刻失败退出。
	if _frames > 60:
		print("VERIFY-TIMEOUT: checks did not finish")
		quit(2)
		return true
	if _phase == 2:
		if _frames >= 8:
			# ---- 储能浮动标签不被顶栏遮（run 45226479162 回归）：锚点原投影 y≈48，
			# 旧代码钳制只改判定 rect、不折回 3D 位置，渲染中心 ≈72 正好压顶栏底边、
			# 上半截字被盖住；修后渲染中心应与 rect 一致（钳后 80 + 22 档 = 102），
			# 字盒顶（中心 −15）≥ 80，完全在顶栏（底 72）之下。
			var _labels_st = _main.get_node("Labels")
			_labels_st.call("_update")
			var _sto_lab: Label3D = null
			for _d2 in _labels_st.defs:
				if String(_d2["dynamic"]) == "soc":
					_sto_lab = _d2["label"] as Label3D
			var _sto_sp := Vector2.ZERO
			var _sto_vis := false
			if _sto_lab != null:
				_sto_vis = _sto_lab.visible
				if _sto_vis:
					_sto_sp = (_labels_st.camera as Camera3D).unproject_position(_sto_lab.position)
			var _vp := _labels_st.get_viewport().get_visible_rect().size
			_chk("储能标签渲染中心 y≈102（字盒顶 ≥80，不进顶栏）", _sto_lab != null and _sto_vis and absf(_vp.y - 720.0) < 1.0 and _sto_sp.y >= 97.0 and _sto_sp.y <= 107.0, "vp=" + str(_vp) + " visible=" + str(_sto_vis) + " y=" + str(_sto_sp.y))
			# ---- 储能场景栏带扫查（本轮审计）：修前三号教学楼渲染中心 y≈48、
			# 配电房 y≈70 落进顶栏带（钳制量未折回，与池塘同类）；修后三号 168、
			# 配电房 102，屏内标签应全在 90≤y≤642 内。
			var _band_st: Array = _labels_band_detail(_labels_st)
			_chk("储能场景：屏内标签渲染中心都不进顶栏/场景栏（90≤y≤642）", bool(_band_st[0]), String(_band_st[1]))
			_main.call("enter_scene", "dist")
			_phase = 1
		return false
	if _phase == 1:
		if _frames >= 10:
			# 场景页导航栏与总览同一口径：进配电房后玻璃仍关、实色 fallback 仍开
			#（run 45226479162：旧逻辑进场景恢复玻璃，半透明深色底压住深色字）。
			var _bar_glass2 = _main.get_node("UI/SceneBar/BarGlass")
			var _bar_fb2 = _main.get_node("UI/SceneBar/BarGlassFallback")
			_chk("场景页（配电房）：场景栏玻璃关、实色 fallback 开", not _bar_glass2.visible and _bar_fb2.visible, str(_bar_glass2.visible) + "/" + str(_bar_fb2.visible))
			var panel2 = _main.get_node("UI/ScenePanel")
			_chk("配电房面板宽 ≤372（不撑出屏）", panel2.size.x <= 372.0, str(panel2.size))
			# 储能近拍机位（?close=1）下一 phase 量：先置开关再 _enter_instant，
			# 等几帧让 rig._process 按放宽的 limits 钳制定位后再量。
			_main._close_cam = true
			_main.call("_enter_instant", "storage")
			_phase = 3
		return false
	if _phase == 3:
		if _frames >= 13:
			var _rig = _main.rig
			_chk("储能近拍机位：dist 5m（不是默认 17m）", absf(_rig.dist - 5.0) < 0.01, str(_rig.dist))
			_chk("储能近拍机位：目标柜面中心 (63.2, 1.4, −29.4)", _rig.target.is_equal_approx(Vector3(63.2, 1.4, -29.4)), str(_rig.target))
			_chk("储能近拍机位：正对柜面 az=0", absf(_rig.az) < 0.01, str(_rig.az))
			# 标签净空放到新 phase 再量：_enter_instant 只改轨道状态，相机位置由
			# rig._process 逐帧算出，等几帧再量渲染位置才准（与储能标签同理）。
			# 注意：储能近拍把 limits 钳在储能区（dist [3,36] + target_box），
			# _enter_instant("overview") 不清 limits，rig._process 会把总览机位
			#（dist 235 / target (−6,2,4)）钳回储能区，量到的根本不是总览；
			# 先 _restore_scene_state 解除 limits（_enter_frozen 内部就是这么做的）。
			_main._close_cam = false
			_main.call("_restore_scene_state")
			_main.call("_enter_instant", "overview")
			_phase = 4
		return false
	if _phase == 4:
		if _frames >= 16:
			# ---- 屋顶光伏 / 艺体馆标签净空（总览）：旧去重叠只要求盒不相交，
			# 总览两盒只差 6px、看着挤成一团；修后净空规则（labels.gd _min_gap=20）
			# 应把艺体馆推到 −44 档，盒间净空 ≥20px。渲染位置为准（unproject 实测），
			# 不是锚点投影。视口已是 1280×720（phase 0 末置起）：无头默认 720×1280
			# 竖屏下两标签横向不重叠，量不到本次修的去重叠路径。
			var _labels_ov = _main.get_node("Labels")
			_labels_ov.call("_update")
			# ---- 池塘标签不被场景栏遮（本轮主修）：锚点原投影 y≈660，旧折回丢了
			# 钳制量，渲染中心 659.7 落进场景栏带（y652–708）、被实白底盖住，
			# 总览里看不见；修后渲染中心应与 rect 一致（钳后 636 + 0 档），
			# 字盒底 651 在栏顶 652 之上。视口已是 1280×720（phase 0 末置起）。
			var _pond_sp := Vector2.ZERO
			var _pond_vis := false
			for _d3 in _labels_ov.defs:
				if String(_d3["text"]) == "池塘":
					var _pl: Label3D = _d3["label"]
					_pond_vis = _pl.visible
					if _pond_vis:
						_pond_sp = (_labels_ov.camera as Camera3D).unproject_position(_pl.position)
			var _vp_ov: Vector2 = _labels_ov.get_viewport().get_visible_rect().size
			_chk("总览：池塘标签渲染中心不在场景栏带（580≤y≤642，留 10px 余量）", _pond_vis and absf(_vp_ov.y - 720.0) < 1.0 and _pond_sp.y >= 580.0 and _pond_sp.y <= 642.0, "vp=" + str(_vp_ov) + " visible=" + str(_pond_vis) + " y=" + str(_pond_sp.y))
			var _band_ov: Array = _labels_band_detail(_labels_ov)
			_chk("总览：屏内标签渲染中心都不进顶栏/场景栏（90≤y≤642）", bool(_band_ov[0]), String(_band_ov[1]))
			# 附加 dist 守卫：limits 没解除时总览机位会被钳成 dist 36 的储能近拍，
			# 两标签盒不交就成了空通过；真总览 dist 235，target (−6,2,4)。
			_chk("总览：屋顶光伏与艺体馆字盒不重叠（净空 ≥20px）", _labels_pair_clear(_labels_ov, 20.0) and absf(_main.rig.dist - 235.0) < 0.5, _labels_pair_detail(_labels_ov) + " dist=" + str(_main.rig.dist) + " target=" + str(_main.rig.target))
			_main.call("_enter_frozen", "classroom", 0.5)
			_phase = 5
		return false
	if _phase == 5:
		if _frames >= 19:
			# ---- 同上，冻结帧（总览 → 教室楼前飞行中段，09-freeze 同机位）：
			# 旧去重叠冻结帧两盒只差 16px；修后艺体馆应推到 +44 档，净空 ≥20px。
			var _labels_fz = _main.get_node("Labels")
			_labels_fz.call("_update")
			# 同总览的 dist 守卫：冻结帧 easeOutCubic(0.5)=0.875、弧线抬升后
			# dist = 235 + (38−235)×0.875 + sin(0.875π)×20 ≈ 70.3；若 limits
			# 意外钳住会变成 36，盒不交就是空通过。
			_chk("冻结帧：屋顶光伏与艺体馆字盒不重叠（净空 ≥20px）", _labels_pair_clear(_labels_fz, 20.0) and absf(_main.rig.dist - 70.28) < 1.0, _labels_pair_detail(_labels_fz) + " dist=" + str(_main.rig.dist))
			var _band_fz: Array = _labels_band_detail(_labels_fz)
			_chk("冻结帧：屏内标签渲染中心都不进顶栏/场景栏（90≤y≤642）", bool(_band_fz[0]), String(_band_fz[1]))
			print("VERIFY-SUMMARY: PASS=", _passes, " FAIL=", _fails)
			quit(1 if _fails > 0 else 0)
		return false
	var _panel = _main.get_node("UI/ScenePanel")
	if not _panel.has_method("set_live"):
		print("VERIFY-FAIL: ScenePanel script did not attach (class cache stale?)")
		quit(2)
		return true
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
	# ---- 3D labels: large font + small pixel_size (fixed_size = as if 1m away) ----
	# screen px = font_size * pixel_size * vp_h / (2*tan(fov/2)); 64 * 0.0003615
	# ~= 16px at 720p/55deg. Old 16 * 0.012 rendered ~133px with a ~33px outline.
	var labels = _main.get_node("Labels")
	var found := false
	for d in labels.defs:
		var l = d["label"] as Label3D
		if l != null and l.text == "一号教学楼":
			found = true
			_chk("Label3D 一号教学楼 fixed_size", l.fixed_size == true, "fixed=" + str(l.fixed_size))
			_chk("Label3D font_size 64 (crisp glyphs)", l.font_size == 64, "size=" + str(l.font_size))
			_chk("Label3D pixel_size ~0.00036 (16px @720p)", l.pixel_size > 0.0002 and l.pixel_size < 0.0006, "px=" + str(l.pixel_size))
			_chk("Label3D outline 16 (scales with font)", l.outline_size == 16, "outline=" + str(l.outline_size))
			_chk("Label3D 一号教学楼有中文字体", l.font != null and l.font.has_char(0x4e00), "font=" + str(l.font != null))
	if not found:
		_chk("Label3D 一号教学楼存在", false, "defs 里没找到")
	# ---- Interior cameras must sit inside the room (old ones were outside/above) ----
	var sc = _main.scenes_data["scenes"]
	var dcam = sc["dist"]["cam"]
	_chk("dist cam inside room (dist<=8, target y<2.5)", float(dcam["dist"]) <= 8.0 and float(dcam["target"][1]) < 2.5, str(dcam))
	var ccam = sc["classroom"]["cam"]
	_chk("classroom cam inside room (dist<=8, target y<2.5)", float(ccam["dist"]) <= 8.0 and float(ccam["target"][1]) < 2.5, str(ccam))
	var wsys2 = _main.get_node("Weather")
	_chk("fog density 0.0005 (less haze, round 2)", absf(wsys2.env.environment.fog_density - 0.0005) < 0.00001, str(wsys2.env.environment.fog_density))
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
	# ---- P2-4 按钮样式统一（UITokens 一套 token） ----
	var play_btn := _main.get_node("UI/TopBar/HBox/PlayButton") as Button
	var play_normal := play_btn.get_theme_stylebox("normal") as StyleBoxFlat
	_chk("实色按钮 normal 白底", play_normal != null and _col(play_normal.bg_color) == "#ffffff", _col(play_normal.bg_color) if play_normal != null else "null")
	_chk("实色按钮字色 #1e293b", _col(play_btn.get_theme_color("font_color")) == "#1e293b", _col(play_btn.get_theme_color("font_color")))
	var play_focus := play_btn.get_theme_stylebox("focus") as StyleBoxFlat
	_chk("实色按钮焦点环 ≥2px（P3-6）", play_focus != null and play_focus.border_width_left >= 2, str(play_focus.border_width_left) if play_focus != null else "null")
	var abc_tgl := _main.get_node("UI/TopBar/HBox/ABCToggle") as Button
	var abc_normal := abc_tgl.get_theme_stylebox("normal") as StyleBoxFlat
	_chk("ABCToggle 同款实色按钮", abc_normal != null and _col(abc_normal.bg_color) == "#ffffff", _col(abc_normal.bg_color) if abc_normal != null else "null")
	var scene_btn := _main.get_node("UI/SceneBar/HBox/BtnOverview") as Button
	_chk("玻璃按钮 normal 仍透明", scene_btn.get_theme_stylebox("normal") is StyleBoxEmpty, str(scene_btn.get_theme_stylebox("normal")))
	var glass_focus := scene_btn.get_theme_stylebox("focus") as StyleBoxFlat
	_chk("玻璃按钮焦点环 ≥2px（P3-6）", glass_focus != null and glass_focus.border_width_left >= 2, str(glass_focus.border_width_left) if glass_focus != null else "null")
	# ---- P2-1 窄屏分支（390px） ----
	ui.call("_apply_narrow_layout", 390.0)
	var mode_chip := _main.get_node("UI/TopBar/HBox/ModeChip") as Label
	_chk("390px 模式芯片隐藏", not mode_chip.visible, str(mode_chip.visible))
	var tslider := _main.get_node("UI/TopBar/HBox/TimeSlider") as HSlider
	_chk("390px 时间滑杆隐藏", not tslider.visible, str(tslider.visible))
	_chk("390px 场景按钮字 13px", scene_btn.get_theme_font_size("font_size") == 13, str(scene_btn.get_theme_font_size("font_size")))
	var abc_panel := _main.get_node("UI/ABCPanel") as PanelContainer
	_chk("390px ABC 面板满宽", abc_panel.offset_left == -366.0, str(abc_panel.offset_left))
	_chk("390px ABC 表格字 14px", (grid.get_child(0) as Label).get_theme_font_size("font_size") == 14, str((grid.get_child(0) as Label).get_theme_font_size("font_size")))
	ui.call("_apply_narrow_layout", 1280.0)
	_chk("1280px 恢复：模式芯片可见", mode_chip.visible, str(mode_chip.visible))
	_chk("1280px 恢复：滑杆可见", tslider.visible, str(tslider.visible))
	_chk("1280px 恢复：场景按钮字 16px", scene_btn.get_theme_font_size("font_size") == 16, str(scene_btn.get_theme_font_size("font_size")))
	_chk("1280px 恢复：ABC 面板 548px", abc_panel.offset_left == -560.0, str(abc_panel.offset_left))
	# ---- ABC/场景面板重叠（两者同开时场景面板下移） ----
	var sp_panel := _main.get_node("UI/ScenePanel") as PanelContainer
	abc_panel.visible = true
	sp_panel.visible = true
	ui.call("layout_panels")
	_chk("双开：场景面板顶 = ABC 底 + 12", sp_panel.offset_top == 452.0, str(sp_panel.offset_top))
	_chk("双开：场景面板底贴场景栏上方", sp_panel.anchor_bottom == 1.0 and sp_panel.offset_bottom == -84.0, str(sp_panel.offset_bottom))
	abc_panel.visible = false
	ui.call("layout_panels")
	_chk("单开：场景面板恢复顶 60", sp_panel.offset_top == 60.0, str(sp_panel.offset_top))
	sp_panel.visible = false
	# ---- 总览偏淡修复（天空/地面加深） ----
	var wsys = _main.get_node("Weather")
	var sky_mat = wsys._sky.sky_material as ProceduralSkyMaterial
	_chk("白天天顶色加深 #63a9e6", _col(sky_mat.sky_top_color) == "#63a9e6", _col(sky_mat.sky_top_color))
	var ground_mi := _main.get_node("Campus").get_child(0) as MeshInstance3D
	_chk("地面绿加深 #4f9d43", ground_mi != null and _col((ground_mi.material_override as StandardMaterial3D).albedo_color) == "#4f9d43", _col((ground_mi.material_override as StandardMaterial3D).albedo_color) if ground_mi != null else "null")
	# ---- P3-4 减弱动效：停闪电、云漂移与树摆 ----
	_main.call("_set_reduced_motion", true)
	_chk("减弱模式已贯通 weather", wsys.reduced_motion == true, str(wsys.reduced_motion))
	wsys.call("set_weather", "storm")
	var cx0: float = (wsys.clouds[0] as MeshInstance3D).position.x
	wsys.call("update_frame", 12.0, 1.0)
	wsys.call("update_frame", 12.0, 1.0)
	_chk("减弱模式云不漂移", (wsys.clouds[0] as MeshInstance3D).position.x == cx0, str((wsys.clouds[0] as MeshInstance3D).position.x - cx0))
	_chk("减弱模式暴雨不闪电", wsys.flash_light.light_energy == 0.0, str(wsys.flash_light.light_energy))
	var canopy0 = _main.campus.tree_canopies[0] as Node3D
	_main._t += 1.0
	_main.call("_update_visuals", _main.sim.state_at(9.0), 0.016)
	var rot_a: float = canopy0.rotation.z
	_main._t += 1.0
	_main.call("_update_visuals", _main.sim.state_at(9.0), 0.016)
	_chk("减弱模式树不摆", canopy0.rotation.z == rot_a, str(canopy0.rotation.z - rot_a))
	_main.call("_set_reduced_motion", false)
	wsys.call("set_weather", "sunny")
	# ---- P3-2 colors.csv 落到工程内 ----
	_chk("data/colors.csv 存在", FileAccess.file_exists("res://data/colors.csv"), "")
	var csv_txt := FileAccess.get_file_as_string("res://data/colors.csv")
	_chk("colors.csv 有 SaaS 行", csv_txt.find("SaaS (General)") >= 0, csv_txt.left(60))
	# ---- P3-7 → 字形：界面文字不再用箭头字形 ----
	var main_src := FileAccess.get_file_as_string("res://scripts/main.gd")
	_chk("界面文字无 DC→AC 箭头", main_src.find("DC→AC") < 0, "")
	_chk("逆变器状态改文字 DC 转 AC", main_src.find("DC 转 AC") >= 0, "")
	# ---- 本轮三处修复：储能风扇高度 / 雨天阳光射线 / 雨天 V2G 弧线 ----
	var sto = _main.sto_interior
	_chk("储能风扇中心 y=3.105（盘底 2.555=柜顶 2.55+0.005）", sto != null and absf(sto.fan.position.y - 3.105) < 0.001, str(sto.fan.position.y) if sto != null else "null")
	_chk("储能风扇盘底 2.555m", sto != null and absf((sto.fan.position.y - 0.55) - 2.555) < 0.001, str(sto.fan.position.y - 0.55) if sto != null else "null")
	# ---- GLB 对齐修补：风扇 X / 流光点 / 检修灯带（storage.glb 实测）----
	var sto_hub: MeshInstance3D = null
	var sto_strip: MeshInstance3D = null
	if sto != null:
		for ch in sto.get_children():
			if ch is MeshInstance3D:
				var mi := ch as MeshInstance3D
				if mi.mesh is CylinderMesh and absf((mi.mesh as CylinderMesh).top_radius - 0.55) < 0.001:
					sto_hub = mi
				if mi.mesh is BoxMesh and (mi.mesh as BoxMesh).size.is_equal_approx(Vector3(8.0, 0.08, 0.3)):
					sto_strip = mi
	_chk("风扇盘中心 X=2.4（GLB PCS 柜中心）", sto_hub != null and absf(sto_hub.position.x - 2.4) < 0.001, str(sto_hub.position.x) if sto_hub != null else "null")
	_chk("风扇盘东缘 2.95 在 GLB 壳东墙 4.3 内", sto_hub != null and sto_hub.position.x + 0.55 < 4.3, str(sto_hub.position.x + 0.55) if sto_hub != null else "null")
	_chk("风扇盘 Z 0.26–0.38 与 GLB PCS_FanDisc（Z≤0.2）留隙", sto_hub != null and absf(sto_hub.position.z - 0.32) < 0.001, str(sto_hub.position.z) if sto_hub != null else "null")
	_chk("风扇叶片 Z 0.31–0.49 在柜前脸 0.5 内", sto != null and absf(sto.fan.position.z - 0.40) < 0.001, str(sto.fan.position.z) if sto != null else "null")
	var dot_xs := {}
	var dot_ok: bool = sto != null and sto.flow_dots.size() == 9
	if dot_ok:
		for d in sto.flow_dots:
			var dd := d as MeshInstance3D
			dot_xs[snappedf(dd.position.x, 0.01)] = true
			if absf(dd.position.z - 0.64) >= 0.001:
				dot_ok = false
	_chk("流光点 9 个、X 列 −2.4/−0.8/0.8（3 台电池柜中心）", dot_ok and dot_xs.has(-2.4) and dot_xs.has(-0.8) and dot_xs.has(0.8), str(dot_xs.keys()))
	_chk("流光点 Z=0.64（球后缘恰贴柜前脸 0.5）", dot_ok, "")
	var dot_ys := [0.3, 1.4, 2.5]
	var dot_rows_ok: bool = sto != null and sto.flow_dots.size() == 9
	if dot_rows_ok:
		for k in range(9):
			if absf((sto.flow_dots[k] as MeshInstance3D).position.y - dot_ys[k / 3]) >= 0.001:
				dot_rows_ok = false
	_chk("流光点静态行 Y 0.3/1.4/2.5", dot_rows_ok, "")
	if sto != null:
		sto.call("update_frame", 100.0, 5.0, 0.016)
		var dot_range_ok := true
		for d in sto.flow_dots:
			var yy := (d as MeshInstance3D).position.y
			if yy < 0.3 - 0.001 or yy > 2.5 + 0.001:
				dot_range_ok = false
		_chk("流光点动画行程 Y 0.3–2.5（柜面高度内）", dot_range_ok, "")
	_chk("检修灯带中心 y=5.415（底面 5.375 恰贴 GLB 屋顶顶）", sto_strip != null and absf(sto_strip.position.y - 5.415) < 0.001, str(sto_strip.position.y) if sto_strip != null else "null")
	_chk("检修灯带底面 5.375 不埋入屋顶", sto_strip != null and absf((sto_strip.position.y - 0.04) - 5.375) < 0.001, str(sto_strip.position.y - 0.04) if sto_strip != null else "null")
	var pv = _main.pv_detail
	pv.call("update_frame", 100.0, 0.30, 0.0)
	_chk("雨天 pv_factor=0.30 阳光射线隐藏", not (pv.ray_planes[0] as MeshInstance3D).visible, str((pv.ray_planes[0] as MeshInstance3D).visible))
	pv.call("update_frame", 100.0, 0.45, 0.0)
	_chk("阴天 pv_factor=0.45 阳光射线显示", (pv.ray_planes[0] as MeshInstance3D).visible, str((pv.ray_planes[0] as MeshInstance3D).visible))
	pv.call("update_frame", 100.0, 0.15, 0.0)
	_chk("暴雨 pv_factor=0.15 阳光射线隐藏", not (pv.ray_planes[0] as MeshInstance3D).visible, str((pv.ray_planes[0] as MeshInstance3D).visible))
	var chg = _main.chg_detail
	chg.call("update_frame", 10.0, 12.0, 0.0, 0.30)
	_chk("雨天 V2G 弧线流光点隐藏", not (chg.arc_dots[0] as MeshInstance3D).visible, str((chg.arc_dots[0] as MeshInstance3D).visible))
	_chk("雨天 V2G 弧线基线隐藏", not (chg.arc_segs[0] as MeshInstance3D).visible, str((chg.arc_segs[0] as MeshInstance3D).visible))
	chg.call("update_frame", 10.0, 12.0, 0.0, 0.45)
	_chk("阴天 V2G 弧线流光点显示", (chg.arc_dots[0] as MeshInstance3D).visible, str((chg.arc_dots[0] as MeshInstance3D).visible))
	_chk("阴天 V2G 弧线基线显示", (chg.arc_segs[0] as MeshInstance3D).visible, str((chg.arc_segs[0] as MeshInstance3D).visible))
	chg.call("update_frame", 10.0, 12.0, 0.0, 0.15)
	_chk("暴雨 V2G 弧线隐藏", not (chg.arc_dots[0] as MeshInstance3D).visible, str((chg.arc_dots[0] as MeshInstance3D).visible))
	chg.call("update_frame", 10.0, 12.0, 0.0, 1.0)
	_chk("晴天 12:00 V2G 弧线流光点显示（雨天对照的阳性对照）", (chg.arc_dots[0] as MeshInstance3D).visible, str((chg.arc_dots[0] as MeshInstance3D).visible))
	_chk("晴天 12:00 V2G 弧线基线显示", (chg.arc_segs[0] as MeshInstance3D).visible, str((chg.arc_segs[0] as MeshInstance3D).visible))
	# ---- 覆盖补拍：储能放电时段流光点（验收缺口 3）----
	# 仿真：12:00 待机 batt=0（柜面无流光点，旧截图即此态）；10:00 峰段放电
	# batt=+100kW（唯一放电窗口 10:00–10:30，SOC 0.90→0.556 触保留线停）；
	# 23:00 谷段充电 −80kW 是夜里，不适合截图。故近拍取 hour=10 放电态。
	var _batt10: float = float((_main.sim.state_at(10.0) as Dictionary)["batt"])
	var _batt12: float = float((_main.sim.state_at(12.0) as Dictionary)["batt"])
	_chk("10:00 储能放电 batt=+100kW（流光点近拍时刻）", _batt10 > 1.0, str(_batt10))
	_chk("12:00 储能待机 batt=0（旧截图柜面无流光点的原因）", absf(_batt12) <= 1.0, str(_batt12))
	if sto != null:
		sto.call("update_frame", _batt10, 5.0, 0.016)
		_chk("放电时流光点可见（贴柜面）", (sto.flow_dots[0] as MeshInstance3D).visible, str((sto.flow_dots[0] as MeshInstance3D).visible))
		sto.call("update_frame", _batt12, 5.0, 0.016)
		_chk("待机时流光点隐藏", not (sto.flow_dots[0] as MeshInstance3D).visible, str((sto.flow_dots[0] as MeshInstance3D).visible))
	# ---- V2G 弧线场景门控（run 45232401156 的 02-storage 斜穿细线）----
	# 那束橙色细线 + 黄球不是阳光射线：阳光射线在 pv_detail 里、储能场景
	# pv_detail.visible=false，且射线是 2.2m 宽带（01-pv 的四条宽带）；
	# 储能图里是 0.12m 细基线 + r0.22 #fb923c 流光点、从 (44,2,76) 到
	# (64,3,−30)，正是 charge_detail 的弧线。弧线只留总览与充电区。
	#（用 state_at(_main.hour) 调 _update_visuals：它会顺带按 SOC 重算机架条
	# 位置，后面的 SOC 条检查按同一 hour 的 SOC 算期望值，用 12:00 会污染。）
	_main.active_scene = "storage"
	_main.call("_update_visuals", _main.sim.state_at(_main.hour), 0.016)
	_chk("V2G 弧线：储能场景不画（不再斜穿柜体）", not _main.chg_detail.visible, str(_main.chg_detail.visible))
	_main.active_scene = "charge"
	_main.call("_update_visuals", _main.sim.state_at(_main.hour), 0.016)
	_chk("V2G 弧线：充电区场景仍画", _main.chg_detail.visible, str(_main.chg_detail.visible))
	_main.active_scene = ""
	_main.call("_update_visuals", _main.sim.state_at(_main.hour), 0.016)
	_chk("V2G 弧线：总览仍画（跨校园能量流的原设计意图）", _main.chg_detail.visible, str(_main.chg_detail.visible))
	# ---- 回退演练开关 ?fallback=1（验收缺口 5：S1/S3/S5 演练截图用）----
	# 开关在 GlbLoader.load_glb 入口，不改名/不移走 GLB 文件；main.gd 在
	# campus.build() 之前按 URL 参数置起，正常截图默认关。
	GlbLoader.force_fallback = true
	_chk("回退演练开关：force_fallback 时 load_glb 返回 null", GlbLoader.load_glb("res://assets/models/scenes/storage.glb") == null, "")
	_chk("回退演练开关：was_loaded 记 false（调用方走程序化回退）", not GlbLoader.was_loaded("storage"), str(GlbLoader.was_loaded("storage")))
	GlbLoader.force_fallback = false
	_chk("回退演练开关：main.gd 在 build 前解析 fallback（赶在 GLB 加载前）", main_src.find("force_fallback") >= 0 and main_src.find("_parse_url_params") >= 0, "")
	# ---- 回退分支修补：S1 储能壳落底 / S3 车落底+车轮 / S5 顶层窗不埋屋顶 ----
	var cb = _main.campus
	_chk("S1 储能外壳底 0.40 落在基座顶", cb != null and absf((cb.storage_shell[0] as MeshInstance3D).position.y - 2.20 - 0.40) < 0.001, str((cb.storage_shell[0] as MeshInstance3D).position.y) if cb != null else "null")
	_chk("S1 储能屋顶随壳同降 4.95", cb != null and absf((cb.storage_shell[1] as MeshInstance3D).position.y - 4.95) < 0.001, str((cb.storage_shell[1] as MeshInstance3D).position.y) if cb != null else "null")
	var cg = cb.charge_group
	var bodies := 0
	var wheels := 0
	var wheels_grounded := 0
	for ch in cg.get_children():
		if ch is MeshInstance3D:
			var mi := ch as MeshInstance3D
			if mi.mesh is BoxMesh and (mi.mesh as BoxMesh).size.is_equal_approx(Vector3(3.9, 1.0, 1.8)):
				bodies += 1
				if absf(mi.position.y - 0.5 - 0.10) >= 0.001:
					_chk("S3 车身底 0.10 落在地面垫顶", false, str(mi.position.y))
			if mi.mesh is CylinderMesh and absf((mi.mesh as CylinderMesh).top_radius - 0.35) < 0.001:
				wheels += 1
				if absf(mi.position.y - 0.35 - 0.10) < 0.001:
					wheels_grounded += 1
	_chk("S3 3 辆车身全部落底（底 0.10）", bodies == 3, str(bodies))
	_chk("S3 车轮 12 个且轮底 0.10 落地", wheels == 12 and wheels_grounded == 12, str(wheels) + "/" + str(wheels_grounded))
	var win_bad := 0
	var win_n := 0
	for b in cb.campus["buildings"]:
		var bh: float = b["height"]
		var hg: Node3D = cb.hosts[String(b["id"])]
		for ch2 in hg.get_children():
			if ch2 is MeshInstance3D:
				var mi2 := ch2 as MeshInstance3D
				if mi2.mesh is BoxMesh and (mi2.mesh as BoxMesh).size.is_equal_approx(Vector3(1.9, 1.4, 0.12)):
					win_n += 1
					if mi2.position.y + 0.7 > bh + 0.001:
						win_bad += 1
	_chk("S5 全部窗顶 ≤ 墙顶（无埋入屋顶板）", win_bad == 0, "checked=" + str(win_n) + " bad=" + str(win_bad))
	# ---- 储能外壳开关 + SOC 条（GLB/回退两路，分支感知：GLB 未载入时验回退路） ----
	# 实时 SOC 与填充比：_process 每帧调 _update_visuals，条子中心/缩放都由它定，
	# 检查必须按同一 soc 算期望值，不能写死位置。
	var _vsoc: float = float((_main.sim.state_at(_main.hour) as Dictionary)["soc"])
	var _vf: float = clampf(_vsoc, 0.02, 1.0)
	if cb.storage_glb_active:
		_chk("GLB 模式：储能壳/顶材质已收集 2 个", cb.storage_glb_shell_mats.size() == 2, str(cb.storage_glb_shell_mats.size()))
		_chk("GLB 模式：壳原始 alpha 0.35（半透明）", cb.storage_glb_shell_mats.size() == 2 and absf(cb.storage_glb_shell_base_alpha[0] - 0.35) < 0.001, str(cb.storage_glb_shell_base_alpha) if cb.storage_glb_shell_mats.size() == 2 else "未收集")
		_chk("GLB 模式：顶原始 alpha 1.0（不透明）", cb.storage_glb_shell_mats.size() == 2 and absf(cb.storage_glb_shell_base_alpha[1] - 1.0) < 0.001, str(cb.storage_glb_shell_base_alpha) if cb.storage_glb_shell_mats.size() == 2 else "未收集")
		if cb.storage_glb_shell_mats.size() == 2:
			cb.call("set_shell_translucent", true)
			_chk("GLB 模式：开关开壳 alpha 0.22", absf((cb.storage_glb_shell_mats[0] as StandardMaterial3D).albedo_color.a - 0.22) < 0.001, str((cb.storage_glb_shell_mats[0] as StandardMaterial3D).albedo_color.a))
			_chk("GLB 模式：开关开顶 alpha 0.22", absf((cb.storage_glb_shell_mats[1] as StandardMaterial3D).albedo_color.a - 0.22) < 0.001, str((cb.storage_glb_shell_mats[1] as StandardMaterial3D).albedo_color.a))
			cb.call("set_shell_translucent", false)
			_chk("GLB 模式：开关关壳 alpha 1.0（不透明，与面板“关”一致）", absf((cb.storage_glb_shell_mats[0] as StandardMaterial3D).albedo_color.a - 1.0) < 0.001, str((cb.storage_glb_shell_mats[0] as StandardMaterial3D).albedo_color.a))
			_chk("GLB 模式：开关关顶 alpha 1.0（不透明）", absf((cb.storage_glb_shell_mats[1] as StandardMaterial3D).albedo_color.a - 1.0) < 0.001, str((cb.storage_glb_shell_mats[1] as StandardMaterial3D).albedo_color.a))
			_chk("GLB 模式：开关关壳透明模式已关（不是恢复原生 0.35 半透明）", (cb.storage_glb_shell_mats[0] as StandardMaterial3D).transparency == BaseMaterial3D.TRANSPARENCY_DISABLED, str((cb.storage_glb_shell_mats[0] as StandardMaterial3D).transparency))
			_chk("GLB 模式：开关关顶透明模式已关", (cb.storage_glb_shell_mats[1] as StandardMaterial3D).transparency == BaseMaterial3D.TRANSPARENCY_DISABLED, str((cb.storage_glb_shell_mats[1] as StandardMaterial3D).transparency))
		_chk("GLB 模式：_shell_mat 指 GLB 壳材质 [0]（SOC 变色可见，非已隐藏的程序化壳）", _main._shell_mat != null and cb.storage_glb_shell_mats.size() >= 1 and _main._shell_mat == cb.storage_glb_shell_mats[0], str(_main._shell_mat))
		var bars_ok: bool = cb.storage_rack_bars.size() == 3
		var bars_vis := true
		var bars_fill_ok := true # 左锚定填充：中心 = 柜中心 − 宽×(1−f)/2，scale.x = f（f = SOC）
		var bars_size_ok := true
		var bars_col_ok := true # 颜色与壳体同口径（_soc_color），同一 SOC 绝不两色
		var bx := [-2.4, -0.8, 0.8]
		for k in range(cb.storage_rack_bars.size()):
			var bb := cb.storage_rack_bars[k] as MeshInstance3D
			if not bb.is_visible_in_tree():
				bars_vis = false
			var exp_cx: float = bx[k] - 1.1 * (1.0 - _vf) / 2.0
			if absf(bb.position.x - exp_cx) >= 0.001 or absf(bb.position.y - 2.2) >= 0.001 or absf(bb.position.z - 0.65) >= 0.001 or absf(bb.scale.x - _vf) >= 0.001:
				bars_fill_ok = false
			if not (bb.mesh is BoxMesh and (bb.mesh as BoxMesh).size.is_equal_approx(Vector3(1.1, 0.35, 0.15))):
				bars_size_ok = false
			var bmat := bb.material_override as StandardMaterial3D
			if bmat == null or _col(bmat.albedo_color) != _col(_main.call("_soc_color", _vsoc)):
				bars_col_ok = false
		_chk("GLB 模式：SOC 条 3 条", bars_ok, str(cb.storage_rack_bars.size()))
		_chk("GLB 模式：SOC 条在树上可见（未随程序化组隐藏）", bars_ok and bars_vis, "")
		_chk("GLB 模式：SOC 条左锚定填充（中心 = 柜中心 − 1.1×(1−f)/2，scale.x = f）", bars_ok and bars_fill_ok, str([(cb.storage_rack_bars[0] as MeshInstance3D).position, (cb.storage_rack_bars[1] as MeshInstance3D).position, (cb.storage_rack_bars[2] as MeshInstance3D).position]) if bars_ok else "")
		_chk("GLB 模式：SOC 条 1.1×0.35×0.15（柜宽 1.3 内，不埋柜）", bars_ok and bars_size_ok, "")
		_chk("GLB 模式：SOC 条颜色与壳体同口径", bars_ok and bars_col_ok, "soc=" + str(_vsoc) + " expect=" + _col(_main.call("_soc_color", _vsoc)))
		_chk("GLB 模式：SOC 条组在 storage_group 外", cb.storage_soc_group != null and cb.storage_soc_group != cb.storage_group, str(cb.storage_soc_group))
		var tr_ok: bool = cb.storage_rack_tracks.size() == 3
		var tr_pos_ok := true
		var tr_size_ok := true
		for k in range(cb.storage_rack_tracks.size()):
			var tt := cb.storage_rack_tracks[k] as MeshInstance3D
			if absf(tt.position.x - bx[k]) >= 0.001 or absf(tt.position.y - 2.2) >= 0.001 or absf(tt.position.z - 0.60) >= 0.001:
				tr_pos_ok = false
			if not (tt.mesh is BoxMesh and (tt.mesh as BoxMesh).size.is_equal_approx(Vector3(1.24, 0.47, 0.10))):
				tr_size_ok = false
		_chk("GLB 模式：SOC 条底槽 3 条（只在 3 台电池柜上，PCS 柜无）", tr_ok, str(cb.storage_rack_tracks.size()))
		_chk("GLB 模式：SOC 条底槽 X −2.4/−0.8/0.8、Y 2.2、Z 0.60（柜门前）", tr_ok and tr_pos_ok, "")
		_chk("GLB 模式：SOC 条底槽 1.24×0.47×0.10（比填充条宽一圈，空槽可见）", tr_ok and tr_size_ok, "")
	else:
		# 回退路：程序化壳仍受开关控制，条子在程序化机架位置
		cb.call("set_shell_translucent", true)
		var proc_a := (cb.storage_shell[0].material_override as StandardMaterial3D).albedo_color.a
		_chk("回退模式：开关开程序化壳 alpha 0.22", absf(proc_a - 0.22) < 0.001, str(proc_a))
		cb.call("set_shell_translucent", false)
		var proc_a2 := (cb.storage_shell[0].material_override as StandardMaterial3D).albedo_color.a
		_chk("回退模式：开关关程序化壳 alpha 恢复 1.0", absf(proc_a2 - 1.0) < 0.001, str(proc_a2))
		_chk("回退模式：_shell_mat 指程序化壳材质（GLB 未接管，SOC 变色仍走程序化壳）", _main._shell_mat == (cb.storage_shell[0].material_override as StandardMaterial3D), str(_main._shell_mat))
		var pbx := [-2.6, 0.0, 2.6]
		var pb_ok: bool = cb.storage_rack_bars.size() == 3
		for k in range(cb.storage_rack_bars.size()):
			var bb2 := cb.storage_rack_bars[k] as MeshInstance3D
			var exp2: float = pbx[k] - 2.0 * (1.0 - _vf) / 2.0
			if absf(bb2.position.x - exp2) >= 0.001 or absf(bb2.position.z - (-0.2)) >= 0.001 or absf(bb2.scale.x - _vf) >= 0.001:
				pb_ok = false
		_chk("回退模式：SOC 条左锚定填充（中心 = 柜中心 − 2.0×(1−f)/2，scale.x = f）", pb_ok, "")
		var pt_ok: bool = cb.storage_rack_tracks.size() == 3
		var pt_pos_ok := true
		for k in range(cb.storage_rack_tracks.size()):
			var tt2 := cb.storage_rack_tracks[k] as MeshInstance3D
			if absf(tt2.position.x - pbx[k]) >= 0.001 or absf(tt2.position.z - (-0.22)) >= 0.001:
				pt_pos_ok = false
		_chk("回退模式：SOC 条底槽随条子移回程序化机架位置 X −2.6/0/2.6、Z −0.22", pt_ok and pt_pos_ok, "")
	# ---- SOC 变色 lerp 保留 alpha（回归）：先开壳到 0.22，再连调 10 次 _update_visuals，
	# alpha 必须仍是 0.22（修前会被推向 1.0）；GLB 与回退两路共用 _shell_mat，同一处验证。
	cb.call("set_shell_translucent", true)
	var a0: float = _main._shell_mat.albedo_color.a
	for k in range(10):
		_main.call("_update_visuals", _main.sim.state_at(_main.hour), 0.016)
	_chk("SOC 变色：10 次 lerp 后壳 alpha 不变（仍 0.22）", _main._shell_mat != null and absf(_main._shell_mat.albedo_color.a - a0) < 0.001 and absf(a0 - 0.22) < 0.001, str(a0) + " -> " + str(_main._shell_mat.albedo_color.a))
	cb.call("set_shell_translucent", false)
	# ---- 面板外壳开关文案与实际壳态同步（回归）：进储能场景自动开壳时，
	# 面板是进场前按 shell_open=false 建的，修前文案一直滞后为“关”，
	# 与实际已开的半透明壳矛盾（run 45219977015 的 02-storage.png）。
	_main.call("_show_panel_for", "storage")
	var _sp = _main.get_node("UI/ScenePanel")
	_sp.call("set_shell_open", true)
	var _shell_txt := ""
	for _c in (_sp.get_node("VBox/SPExtra") as HBoxContainer).get_children():
		if _c is Button:
			_shell_txt = (_c as Button).text
	_chk("储能面板：自动开壳后开关文案为“开”", _shell_txt == "外壳半透明：开", _shell_txt)
	_sp.call("set_shell_open", false)
	_shell_txt = ""
	for _c in (_sp.get_node("VBox/SPExtra") as HBoxContainer).get_children():
		if _c is Button:
			_shell_txt = (_c as Button).text
	_chk("储能面板：set_shell_open(false) 后文案为“关”", _shell_txt == "外壳半透明：关", _shell_txt)
	# ---- 面板 SOC 条颜色（run 45226479162 回归）：截图里 y339–348 的红条是
	# 面板 ProgressBar，不是 3D 机架条也不是保留线条；旧版它的颜色在
	# _refresh_panel 里用保留线阈值（≤0.58 红）内联写死，_soc_color() 根本
	# 没作用到它身上，56% 时面板条红、壳与 3D 条绿，同一 SOC 两色。
	# 修后面板条与壳/3D 条共用 _soc_color；保留线仍是条下独立红字 Label，
	# 面板里只有这一根 ProgressBar，不得与保留线共用一根条。
	_chk("SOC 56% 时 _soc_color 为绿 #1d9e63（不再判红）", _col(_main.call("_soc_color", 0.56)) == "#1d9e63", _col(_main.call("_soc_color", 0.56)))
	_main.active_scene = "storage"
	_main.call("_refresh_panel")
	var _live = _main.get_node("UI/ScenePanel/VBox/SPLive")
	var _pbar: ProgressBar = null
	var _pbar_n := 0
	var _resv_lab: Label = null
	for _lc in _live.get_children():
		if _lc is ProgressBar:
			_pbar = _lc as ProgressBar
			_pbar_n += 1
		if _lc is Label and (_lc as Label).text.begins_with("应急保留线"):
			_resv_lab = _lc as Label
	var _fill_col := ""
	if _pbar != null:
		var _fsb := _pbar.get_theme_stylebox("fill") as StyleBoxFlat
		if _fsb != null:
			_fill_col = _col(_fsb.bg_color)
	_chk("储能面板：SOC 条只有 1 根 ProgressBar（保留线不另画条）", _pbar_n == 1, str(_pbar_n))
	_chk("储能面板：SOC 条填充色 = _soc_color(soc)（与壳/3D 条同口径）", _pbar != null and _fill_col == _col(_main.call("_soc_color", _vsoc)), "soc=" + str(_vsoc) + " fill=" + _fill_col + " expect=" + _col(_main.call("_soc_color", _vsoc)))
	_chk("储能面板：SOC 条填充值 = SOC%（value 与 pct 一致）", _pbar != null and absf(_pbar.value - _vsoc * 100.0) < 0.01, str(_pbar.value) if _pbar != null else "无条")
	_chk("储能面板：保留线是条下独立红字 Label（#dc2626）", _resv_lab != null and _col(_label_color(_resv_lab)) == "#dc2626", _resv_lab.text if _resv_lab != null else "无保留线 Label")
	# ---- 池塘遮挡（run 45219977015）：总览时场景栏须走实色 fallback（白 0.93），
	# 玻璃须关，否则亮蓝池塘水面透进导航栏压住“教室舒适度”等文字。
	var _bar_glass = _main.get_node("UI/SceneBar/BarGlass")
	var _bar_fb = _main.get_node("UI/SceneBar/BarGlassFallback")
	_chk("总览：场景栏玻璃关、实色 fallback 开（池塘不透进导航文字）", not _bar_glass.visible and _bar_fb.visible, str(_bar_glass.visible) + "/" + str(_bar_fb.visible))
	# ---- 场景面板不撑出屏（回归检查）：进配电房（修前最宽 511px），
	# 等几帧让容器排完版再量宽。
	# 储能标签放到下一 phase 再量：_enter_instant 只改轨道状态，相机位置由
	# rig._process 逐帧算出，等几帧再量渲染位置才准（与进配电房量面板宽同理）。
	# 另把视口改成 1280×720：无头默认视口是 720×1280（竖屏），储能锚点在那个
	# 尺寸下投影 y≈85、根本不触发顶栏钳制，量不到本次修的钳制路径；
	# 720p 下锚点投影 y≈48，钳制 80 + 22 档才是截图里的真机位。
	root.size = Vector2(1280, 720)
	_main.call("_enter_instant", "storage")
	_phase = 2
	return false
	return true
