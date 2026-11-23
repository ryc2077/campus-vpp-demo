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
	if _phase == 1:
		if _frames >= 10:
			var panel2 = _main.get_node("UI/ScenePanel")
			_chk("配电房面板宽 ≤372（不撑出屏）", panel2.size.x <= 372.0, str(panel2.size))
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
	# ---- 场景面板不撑出屏（回归检查）：进配电房（修前最宽 511px），
	# 等几帧让容器排完版再量宽。
	_main.call("enter_scene", "dist")
	_phase = 1
	return false
	return true
