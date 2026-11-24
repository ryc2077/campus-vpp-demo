extends SceneTree
## 无头逻辑验证：不渲染，只跑代码并检查运行时的实际状态。
## 用法：godot --headless --path . -s tools/verify_fixes.gd
## 检查：P0 面板数值列/标题颜色、P1-1 HintLabel、P1-2 舒适带绿、P1-3 ABC 保供逻辑、
##      P2-3 标签色、P2-5 WxLabel、labels fixed_size、标题/时钟色、
##      屋顶光伏/艺体馆标签净空（总览 + 冻结帧，1280×720）、
##      池塘标签不进场景栏（总览）+ 屏内标签栏带扫查（储能场景/总览/冻结帧）、
##      总览池塘水面底缘 y<640（F1 取景修补：总览 dist 235→275）、
##      F2/F3 标签锚点修补：总览变压器标签渲染中心距箱体顶面中心 ≤30px、
##      三号教学楼总览屏内可见、屏内可见标签两两无新重叠（SOC/变压器有意叠放除外）、
##      回退总览 pin 关：变压器 +44 档与 SOC 字盒分开（净空 ≥20px），
##      宿舍楼 A/B +66 未被误藏（GLB 总览 F2 叠放不变，分支按 overview_glb_active 判定）、
##      一号教学楼总览锚点修补（F1 取景代价）：总览一号屏内可见（+44 档 y≈316）、
##      二号教学楼 +88 档未被误藏、一号与屋顶光伏纵向净空 ≥20px、ABC 打开/关闭基线 18 条、
##      ABC 面板遮挡（充电区 + 总览 ABC 打开态：屏内可见标签无一与 ABC 面板相交）、
##      冻结帧屏外标签审计（x 钳制不折回的基线：屏内 4 / 屏外 2，锚点在画面外）、
##      面板进场动效（场景面板 + ABC 面板 scale 0.95 中段：_final_rect = 终态 rect、
##      标签可见集合与终态一致，储能 ABC 打开态 SOC 不闪现）。
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


func _labels_panel_detail(labels: Node) -> Array:
	# [是否全部通过, 详情]：面板打开时，屏内可见标签的渲染字盒不得与场景面板实时 rect 相交；
	# 面板隐藏时（总览）不审。口径与 labels.gd 的面板守卫一致（判定盒与面板 rect 相交即撞上）。
	var panel: Control = _main.get_node("UI/ScenePanel")
	if not panel.is_visible_in_tree():
		return [true, "panel hidden"]
	var pr: Rect2 = panel.get_global_rect()
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
		var r := _labels_rect(labels, d)
		if r.intersects(pr):
			bad.append(String(d["text"]) + " overlap=" + str(snappedf(r.intersection(pr).get_area() / r.get_area(), 0.01)))
	return [bad.is_empty(), "panel=" + str(pr) + " onscreen=" + str(n) + " bad=[" + ", ".join(bad) + "]"]


func _labels_abc_detail(labels: Node) -> Array:
	# [是否全部通过, 详情]：ABC 面板打开时，屏内可见标签的渲染字盒不得与 ABC 面板实时 rect 相交；
	# ABC 关闭时不审。口径与 labels.gd 的 ABC 守卫一致（判定盒与面板 rect 相交即撞上）。
	# 注意双开时 ABC 打开会把场景面板顶到 y452，原先被场景面板藏掉的标签会复活到
	# ABC 矩形里——探针里储能/充电区/冻结帧 ABC 打开态的屏内可见数因此比关闭态还多，
	# 正是本修要藏掉的那批（储能 5、充电区 7、冻结帧 6，关闭态各为 3/3/4）。
	var abc: Control = _main.get_node("UI/ABCPanel")
	if not abc.is_visible_in_tree():
		return [true, "abc hidden"]
	var ar: Rect2 = abc.get_global_rect()
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
		var r := _labels_rect(labels, d)
		if r.intersects(ar):
			bad.append(String(d["text"]) + " overlap=" + str(snappedf(r.intersection(ar).get_area() / r.get_area(), 0.01)))
	return [bad.is_empty(), "abc=" + str(ar) + " onscreen=" + str(n) + " bad=[" + ", ".join(bad) + "]"]


func _soc_sp(labels: Node) -> Vector2:
	# SOC 标签渲染中心（动态文本，按 dynamic=="soc" 找）；不可见时返回 Vector2.ZERO。
	var cam: Camera3D = labels.camera as Camera3D
	for d in labels.defs:
		if String(d["dynamic"]) == "soc":
			var l: Label3D = d["label"]
			if l.visible:
				return cam.unproject_position(l.position)
	return Vector2.ZERO


func _label_visible(labels: Node, text: String) -> bool:
	for d in labels.defs:
		if String(d["text"]) == text:
			return bool((d["label"] as Label3D).visible)
	return false


func _label_onscreen_visible(labels: Node, text: String) -> bool:
	var cam: Camera3D = labels.camera as Camera3D
	for d in labels.defs:
		if String(d["text"]) == text:
			var l: Label3D = d["label"]
			if not l.visible:
				return false
			var sp: Vector2 = cam.unproject_position(l.position)
			return sp.x >= 0.0 and sp.x <= 1280.0 and sp.y >= 0.0 and sp.y <= 720.0
	return false


func _soc_visible(labels: Node) -> bool:
	# SOC 标签是动态文本（l.text 随 SOC 变），按 dynamic=="soc" 找，不按文案找。
	for d in labels.defs:
		if String(d["dynamic"]) == "soc":
			return bool((d["label"] as Label3D).visible)
	return false


func _soc_onscreen_visible(labels: Node) -> bool:
	var cam: Camera3D = labels.camera as Camera3D
	for d in labels.defs:
		if String(d["dynamic"]) == "soc":
			var l: Label3D = d["label"]
			if not l.visible:
				return false
			var sp: Vector2 = cam.unproject_position(l.position)
			return sp.x >= 0.0 and sp.x <= 1280.0 and sp.y >= 0.0 and sp.y <= 720.0
	return false


func _vis_set(labels: Node) -> Array:
	# 屏内可见标签集合（已排序；SOC 是动态文本，用 [soc] 作稳定键，
	# 免得 SOC 百分比随 hour 变导致集合比对抖动）。
	var cam: Camera3D = labels.camera as Camera3D
	var out: Array[String] = []
	for d in labels.defs:
		var l: Label3D = d["label"]
		if not l.visible:
			continue
		var sp: Vector2 = cam.unproject_position(l.position)
		if sp.x >= 0.0 and sp.x <= 1280.0 and sp.y >= 0.0 and sp.y <= 720.0:
			out.append("[soc]" if String(d["dynamic"]) == "soc" else String(d["text"]))
	out.sort()
	return out


func _offscreen_visible_texts(labels: Node) -> Array:
	# visible=true 但渲染中心在屏外的标签（已排序；x 钳制未折回的遗留审计用）。
	var cam: Camera3D = labels.camera as Camera3D
	var out: Array[String] = []
	for d in labels.defs:
		var l: Label3D = d["label"]
		if not l.visible:
			continue
		var sp: Vector2 = cam.unproject_position(l.position)
		if sp.x < 0.0 or sp.x > 1280.0 or sp.y < 0.0 or sp.y > 720.0:
			out.append(String(d["text"]))
	out.sort()
	return out


func _rect_close(a: Rect2, b: Rect2, tol: float) -> bool:
	return absf(a.position.x - b.position.x) < tol and absf(a.position.y - b.position.y) < tol and absf(a.size.x - b.size.x) < tol and absf(a.size.y - b.size.y) < tol


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
			# ---- 场景面板遮挡（run 45247090332 的 02-storage 半截“餐厅”标签）：
			# 面板 rect 作碰撞区，档位逃不出的标签整条藏掉。修前餐厅 overlap 0.69、
			# 配电变压器 overlap 0.64，均在面板后；修后两者都应隐藏，SOC 标签仍在面板外可见。
			var _panel_st: Array = _labels_panel_detail(_labels_st)
			_chk("02-storage：屏内可见标签无一与场景面板相交", bool(_panel_st[0]), String(_panel_st[1]))
			_chk("02-storage：餐厅标签藏掉（面板后半截标签不留）", not _label_visible(_labels_st, "餐厅 · 学术报告厅"), "visible=" + str(_label_visible(_labels_st, "餐厅 · 学术报告厅")))
			_chk("02-storage：配电变压器标签藏掉（同在面板后）", not _label_visible(_labels_st, "配电变压器"), "visible=" + str(_label_visible(_labels_st, "配电变压器")))
			_chk("02-storage：储能 SOC 标签仍屏内可见（在面板外，未被误藏）", _soc_onscreen_visible(_labels_st), "visible=" + str(_soc_visible(_labels_st)))
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
			#（dist 275 / target (−6,2,4)）钳回储能区，量到的根本不是总览；
			# 先 _restore_scene_state 解除 limits（_enter_frozen 内部就是这么做的）。
			_main._close_cam = false
			_main.call("_restore_scene_state")
			# 总览无面板：exit_scene 会藏面板，_enter_instant("overview") 不动面板；
			# 不藏会让总览标签误撞 stale 面板 rect（餐厅在总览本在面板外可见）。
			(_main.get_node("UI/ScenePanel") as Control).visible = false
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
			# ---- 总览池塘水面底缘（F1 取景修补：总览机位 dist 235→275）----
			# 水面椭圆（campus.json 口径：中心 (82,78)、水面 rx 9.9/rz 7.2、y=0.1），
			# 采样 72 点取最大屏 y；修前底缘 708（程序化水面）/713（全尺寸椭圆），
			# 被场景栏（y652–708）盖住约 56px；修后应 <640（栏顶 652 之上，留余量）。
			# dist 守卫同上：本 phase 进总览前已 _restore_scene_state 解除近拍 limits，
			# 量之前不再重复解除；limits 未解除时量到的是钳回的近拍机位。
			var _pond_bottom := 0.0
			for _i in range(72):
				var _a := TAU * float(_i) / 72.0
				var _sp9: Vector2 = (_labels_ov.camera as Camera3D).unproject_position(Vector3(82 + 9.9 * cos(_a), 0.1, 78 + 7.2 * sin(_a)))
				_pond_bottom = maxf(_pond_bottom, _sp9.y)
			_chk("总览：池塘水面底缘 y<640（完整露出在场景栏之上）", _pond_bottom < 640.0 and absf(_main.rig.dist - 275.0) < 0.5, "bottom=" + str(_pond_bottom) + " dist=" + str(_main.rig.dist))
			var _band_ov: Array = _labels_band_detail(_labels_ov)
			_chk("总览：屏内标签渲染中心都不进顶栏/场景栏（90≤y≤642）", bool(_band_ov[0]), String(_band_ov[1]))
			# ---- F2/F3 标签锚点修补（run 45261531067）----
			# F2：变压器标签锚点 (74,8.8,-30) 投影距箱体顶面中心仅约 13px，
			# 错位是去重叠 +44 档顶到宿舍楼 A 屋顶；修后 pin 原位叠放（dy 0，
			# 仅撞 SOC 时放行，见 labels.gd 规则 6），渲染中心应贴在箱体上
			#（距顶面中心 (74,3.6,-30) 投影 ≤30px）。
			# 回退总览修补（2026-11-24）：pin 只在 GLB 总览放行
			#（labels.pin_enabled = campus.overview_glb_active）；回退总览
			# pin 关，变压器走正常档位：探针实测 +44 档（渲染中心 y≈435.1，
			# 字盒 y420.1–450.1，与 SOC 字盒底 393.3 纵向净空 26.8px），
			# 宿舍楼 A/B 各被顶到 +66（494.8/551.9），无标签被藏。
			# 分支用 _main.campus.overview_glb_active 判定（GLB 接管才 true；
			# 本地无头未 --import 时 false，走回退口径，CI 跑 GLB 口径）。
			var _glb_ov4: bool = _main.campus.overview_glb_active
			var _tf_sp := Vector2.ZERO
			var _tf_vis := false
			for _d8 in _labels_ov.defs:
				if String(_d8["text"]) == "配电变压器":
					var _tl: Label3D = _d8["label"]
					_tf_vis = _tl.visible
					if _tf_vis:
						_tf_sp = (_labels_ov.camera as Camera3D).unproject_position(_tl.position)
			var _box_sp: Vector2 = (_labels_ov.camera as Camera3D).unproject_position(Vector3(74, 3.6, -30))
			if _glb_ov4:
				_chk("总览：配电变压器标签渲染中心贴在箱体上（距箱体顶面中心 ≤30px）", _tf_vis and _tf_sp.distance_to(_box_sp) <= 30.0, "render=" + str(_tf_sp) + " box=" + str(_box_sp) + " dist=" + str(_tf_sp.distance_to(_box_sp)))
			else:
				var _soc_r4 := Rect2()
				var _tf_r4 := Rect2()
				for _dR in _labels_ov.defs:
					if String(_dR["dynamic"]) == "soc":
						_soc_r4 = _labels_rect(_labels_ov, _dR)
					if String(_dR["text"]) == "配电变压器":
						_tf_r4 = _labels_rect(_labels_ov, _dR)
				_chk("回退总览：配电变压器与 SOC 字盒不重叠（pin 关，纵向净空 ≥20px）", _tf_vis and _label_onscreen_visible(_labels_ov, "配电变压器") and not _soc_r4.intersects(_tf_r4) and _tf_r4.position.y - _soc_r4.end.y >= 20.0, "soc=" + str(_soc_r4) + " tf=" + str(_tf_r4))
				_chk("回退总览：配电变压器走 +44 档（渲染中心 y≈435，430≤y≤440）", _tf_vis and _tf_sp.y >= 430.0 and _tf_sp.y <= 440.0, "render=" + str(_tf_sp))
				var _dormA_sp := Vector2.ZERO
				var _dormB_sp := Vector2.ZERO
				for _dD in _labels_ov.defs:
					if String(_dD["text"]) == "宿舍楼 A":
						_dormA_sp = (_labels_ov.camera as Camera3D).unproject_position((_dD["label"] as Label3D).position)
					if String(_dD["text"]) == "宿舍楼 B":
						_dormB_sp = (_labels_ov.camera as Camera3D).unproject_position((_dD["label"] as Label3D).position)
				_chk("回退总览：宿舍楼 A/B 未被误藏（被变压器顶到 +66，仍屏内可见）", _label_onscreen_visible(_labels_ov, "宿舍楼 A") and _label_onscreen_visible(_labels_ov, "宿舍楼 B") and _dormA_sp.y >= 490.0 and _dormA_sp.y <= 500.0 and _dormB_sp.y >= 547.0 and _dormB_sp.y <= 557.0, "A=" + str(_dormA_sp) + " B=" + str(_dormB_sp))
			# F3：三号教学楼锚点总览用楼南侧低位 (17,8,-20)（其余场景楼顶原锚点，
			# 见 main.gd _apply_c3_anchor），+88 档落到楼南立面正下方空地；
			# 修后总览应屏内可见。
			_chk("总览：三号教学楼标签屏内可见（F3 锚点修补）", _label_onscreen_visible(_labels_ov, "三号教学楼"), "visible=" + str(_label_visible(_labels_ov, "三号教学楼")))
			# 一号教学楼标签修补（F1 取景代价，main.gd _apply_bldA_anchor）：
			# 总览锚点改用屋顶北缘高位 (-53,23,-37)，屏上 (630,272)，+44 档落到
			# (630,316)；唯一连带是二号教学楼 +44→+88（329.8→373.8），其余标签不动。
			_chk("总览：一号教学楼标签屏内可见（一号锚点修补）", _label_onscreen_visible(_labels_ov, "一号教学楼") and absf(_main.rig.dist - 275.0) < 0.5, "visible=" + str(_label_visible(_labels_ov, "一号教学楼")) + " dist=" + str(_main.rig.dist))
			var _bldA_sp := Vector2.ZERO
			var _bldB_sp := Vector2.ZERO
			for _dA in _labels_ov.defs:
				if String(_dA["text"]) == "一号教学楼":
					_bldA_sp = (_labels_ov.camera as Camera3D).unproject_position((_dA["label"] as Label3D).position)
				if String(_dA["text"]) == "二号教学楼":
					_bldB_sp = (_labels_ov.camera as Camera3D).unproject_position((_dA["label"] as Label3D).position)
			_chk("总览：一号教学楼渲染中心 y≈316（+44 档，308≤y≤324）", _label_onscreen_visible(_labels_ov, "一号教学楼") and _bldA_sp.y >= 308.0 and _bldA_sp.y <= 324.0, "y=" + str(_bldA_sp.y))
			_chk("总览：二号教学楼仍屏内可见（被一号顶到 +88 档，y≈374）", _label_onscreen_visible(_labels_ov, "二号教学楼") and _bldB_sp.y >= 365.0 and _bldB_sp.y <= 382.0, "y=" + str(_bldB_sp.y))
			var _bldA_r := Rect2()
			var _pv_r := Rect2()
			for _dB in _labels_ov.defs:
				if String(_dB["text"]) == "一号教学楼":
					_bldA_r = _labels_rect(_labels_ov, _dB)
				if String(_dB["text"]) == "屋顶光伏":
					_pv_r = _labels_rect(_labels_ov, _dB)
			_chk("总览：一号教学楼与屋顶光伏字盒不重叠（纵向净空 ≥20px）", not _bldA_r.intersects(_pv_r) and _bldA_r.position.y - _pv_r.end.y >= 20.0, "bldA=" + str(_bldA_r) + " pv=" + str(_pv_r))
			# 无新重叠：屏内可见标签两两字盒不相交——GLB 总览里 SOC/变压器是 pin
			# 有意叠放的一对（F2），排除在外；回退总览 pin 关，两盒须分开，
			# 不排除。其余任何一对相交即新重叠。
			var _ov_bad: Array[String] = []
			var _ov_defs: Array = []
			for _d9 in _labels_ov.defs:
				var _l9: Label3D = _d9["label"]
				if not _l9.visible:
					continue
				var _spx: Vector2 = (_labels_ov.camera as Camera3D).unproject_position(_l9.position)
				if _spx.x < 0.0 or _spx.x > 1280.0 or _spx.y < 0.0 or _spx.y > 720.0:
					continue
				_ov_defs.append(_d9)
			for _k in range(_ov_defs.size()):
				for _m in range(_k + 1, _ov_defs.size()):
					var _a1: Dictionary = _ov_defs[_k]
					var _a2: Dictionary = _ov_defs[_m]
					var _t1 := String(_a1["text"])
					var _t2 := String(_a2["text"])
					if _glb_ov4 and ((_t1 == "配电变压器" and String(_a2["dynamic"]) == "soc") or (_t2 == "配电变压器" and String(_a1["dynamic"]) == "soc")):
						continue
					if _labels_rect(_labels_ov, _a1).intersects(_labels_rect(_labels_ov, _a2)):
						_ov_bad.append(_t1 + "/" + _t2)
			_chk("总览：屏内可见标签两两无重叠（GLB 分支 SOC/变压器有意叠放除外，回退分支不除外）", _ov_bad.is_empty(), "bad=[" + ", ".join(_ov_bad) + "]")
			# 附加 dist 守卫：limits 没解除时总览机位会被钳成 dist 36 的储能近拍，
			# 两标签盒不交就成了空通过；真总览 dist 275，target (−6,2,4)。
			_chk("总览：屋顶光伏与艺体馆字盒不重叠（净空 ≥20px）", _labels_pair_clear(_labels_ov, 20.0) and absf(_main.rig.dist - 275.0) < 0.5, _labels_pair_detail(_labels_ov) + " dist=" + str(_main.rig.dist) + " target=" + str(_main.rig.target))
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
			# dist = 275 + (38−275)×0.875 + sin(0.875π)×20 ≈ 75.3；若 limits
			# 意外钳住会变成 36，盒不交就是空通过。
			_chk("冻结帧：屋顶光伏与艺体馆字盒不重叠（净空 ≥20px）", _labels_pair_clear(_labels_fz, 20.0) and absf(_main.rig.dist - 75.28) < 1.0, _labels_pair_detail(_labels_fz) + " dist=" + str(_main.rig.dist))
			var _band_fz: Array = _labels_band_detail(_labels_fz)
			_chk("冻结帧：屏内标签渲染中心都不进顶栏/场景栏（90≤y≤642）", bool(_band_fz[0]), String(_band_fz[1]))
			# ---- 09-freeze 面板遮挡（同类旧局限）：修前二号 overlap 1.0、创造力中心 0.88，
			# 整条在面板后；修后两者都应隐藏，一号教学楼仍在面板外可见。
			var _panel_fz: Array = _labels_panel_detail(_labels_fz)
			_chk("09-freeze：屏内可见标签无一与场景面板相交", bool(_panel_fz[0]), String(_panel_fz[1]))
			_chk("09-freeze：二号教学楼标签藏掉（整条在面板后）", not _label_visible(_labels_fz, "二号教学楼"), "visible=" + str(_label_visible(_labels_fz, "二号教学楼")))
			_chk("09-freeze：创造力中心标签藏掉（整条在面板后）", not _label_visible(_labels_fz, "创造力中心"), "visible=" + str(_label_visible(_labels_fz, "创造力中心")))
			_chk("09-freeze：一号教学楼仍屏内可见（在面板外，未被误藏）", _label_onscreen_visible(_labels_fz, "一号教学楼"), "visible=" + str(_label_visible(_labels_fz, "一号教学楼")))
			# ---- 冻结帧屏外标签审计（x 钳制未折回的已知遗留；探针结论：不修）：
			# 修前审计（1280×720，无头探针，7 视图全量）：屏外可见共 8 条——
			# pv 二号/操场、storage 操场、classroom 操场、charge 池塘/南门、
			# freeze 宿舍楼 A/操场；锚点投影全在画面外几百～几千 px（宿舍楼 A
			# x=9135、操场 x=−284/y=741），楼根本不在本帧内。临时折回实验：
			# 折回后 freeze 4→6（宿舍楼 A 落 (1227,636)、操场落 (79,636)，
			# 双双贴底边）、classroom 0→1（操场凭空出现在内景）、pv 3→5、
			# charge 3→5——多出来的全是贴边浮标，不指向任何可见楼体；
			# y 折回不同：锚点 x 在屏内、只 y 出带，楼在帧内才值得拉回。
			# 故不修 x 折回；以下三项把审计基线锁死，防后人误修。
			var _fz_on := 0
			for _d5 in _labels_fz.defs:
				var _l5: Label3D = _d5["label"]
				if not _l5.visible:
					continue
				var _sp5: Vector2 = (_labels_fz.camera as Camera3D).unproject_position(_l5.position)
				if _sp5.x >= 0.0 and _sp5.x <= 1280.0 and _sp5.y >= 0.0 and _sp5.y <= 720.0:
					_fz_on += 1
			var _fz_off: Array = _offscreen_visible_texts(_labels_fz)
			_chk("冻结帧审计：屏内可见 4 条、屏外可见 2 条（宿舍楼 A / 操场 · 田径场）", _fz_on == 4 and _fz_off == ["宿舍楼 A", "操场 · 田径场"], "onscreen=" + str(_fz_on) + " offscreen=" + str(_fz_off))
			var _fz_ap_out := true
			for _d6 in _labels_fz.defs:
				if _fz_off.has(String(_d6["text"])):
					var _anch6: Vector3 = _d6["anchor"]
					var _ap6: Vector2 = (_labels_fz.camera as Camera3D).unproject_position(_anch6)
					if _ap6.x >= 0.0 and _ap6.x <= 1280.0 and _ap6.y >= 0.0 and _ap6.y <= 720.0:
						_fz_ap_out = false
			_chk("冻结帧审计：屏外可见标签的锚点投影都在画面外（楼不在本帧内，不值得折回）", _fz_ap_out, "offscreen=" + str(_fz_off))
			var _fz_x_ok := true
			for _d7 in _labels_fz.defs:
				var _l7: Label3D = _d7["label"]
				if not _l7.visible:
					continue
				var _rp7: Vector2 = (_labels_fz.camera as Camera3D).unproject_position(_l7.position)
				if _rp7.x < 0.0 or _rp7.x > 1280.0 or _rp7.y < 0.0 or _rp7.y > 720.0:
					continue
				var _anch7: Vector3 = _d7["anchor"]
				var _ap7: Vector2 = (_labels_fz.camera as Camera3D).unproject_position(_anch7)
				if absf(_rp7.x - _ap7.x) >= 1.0:
					_fz_x_ok = false
			_chk("冻结帧审计：屏内标签渲染 x = 锚点投影 x（x 未折回，无边角浮标）", _fz_x_ok, "")
			# 04-charge 放到新 phase 再量：切场景后等 4 帧再量（与储能标签同理），
			# 04 用 shots_all.sh 的 hour=18。
			_main.hour = 18.0
			_main.call("_restore_scene_state")
			_main.call("_enter_instant", "charge")
			_phase = 6
		return false
	if _phase == 6:
		if _frames >= 23:
			# ---- 04-charge 面板遮挡（同类旧局限）：修前三号右缘约 16px 被面板切
			# （overlap 0.20，档位上下逃不出纵贯面板）、配电房 / 配电变压器 /
			# 储能 SOC 整条在面板后（overlap 1.0/0.97/1.0）；修后四者都应隐藏，
			# 创造力中心与充电区 · V2G 在面板外仍可见（创造力因三号让位从 y168 上移到 y102，
			# 仍在面板外、无新重叠，见探针逐项对照）。
			var _labels_ch = _main.get_node("Labels")
			_labels_ch.call("_update")
			var _panel_ch: Array = _labels_panel_detail(_labels_ch)
			_chk("04-charge：屏内可见标签无一与场景面板相交", bool(_panel_ch[0]), String(_panel_ch[1]))
			_chk("04-charge：三号教学楼标签藏掉（右缘曾被面板切）", not _label_visible(_labels_ch, "三号教学楼"), "visible=" + str(_label_visible(_labels_ch, "三号教学楼")))
			_chk("04-charge：配电房标签藏掉（整条在面板后）", not _label_visible(_labels_ch, "配电房"), "visible=" + str(_label_visible(_labels_ch, "配电房")))
			_chk("04-charge：配电变压器标签藏掉（整条在面板后）", not _label_visible(_labels_ch, "配电变压器"), "visible=" + str(_label_visible(_labels_ch, "配电变压器")))
			_chk("04-charge：储能 SOC 标签藏掉（整条在面板后）", not _soc_visible(_labels_ch), "visible=" + str(_soc_visible(_labels_ch)))
			_chk("04-charge：创造力中心仍屏内可见（在面板外，未被误藏）", _label_onscreen_visible(_labels_ch, "创造力中心"), "visible=" + str(_label_visible(_labels_ch, "创造力中心")))
			_chk("04-charge：充电区 · V2G 仍屏内可见（在面板外，未被误藏）", _label_onscreen_visible(_labels_ch, "充电区 · V2G"), "visible=" + str(_label_visible(_labels_ch, "充电区 · V2G")))
			var _band_ch: Array = _labels_band_detail(_labels_ch)
			_chk("04-charge：屏内标签渲染中心都不进顶栏/场景栏（90≤y≤642）", bool(_band_ch[0]), String(_band_ch[1]))
			# ---- 04-charge ABC 打开放到新 phase 再量：ABC 打开会把场景面板顶到 y452，
			# 切面板后等 4 帧再量（与切场景同理）。
			(_main.get_node("UI/ABCPanel") as Control).visible = true
			_main.get_node("UI").call("layout_panels")
			_phase = 7
		return false
	if _phase == 7:
		if _frames >= 27:
			# ---- 04-charge ABC 打开（本轮主修）：ABC rect (720,60,548,380) 与场景面板
			# 同一模式作碰撞区。修前 ABC 打开态屏内可见 7 条，其中 5 条在 ABC 矩形里
			#（三号/创造力中心/配电房/配电变压器/储能 SOC，overlap 1.0/1.0/1.0/0.97/1.0，
			# 其中三号等 4 条是场景面板下移后从面板后复活的）；修后 5 条都应隐藏，
			# 只剩操场与充电区 · V2G 在 ABC 外可见，场景面板（已下移）也仍无相交。
			var _labels_ab = _main.get_node("Labels")
			_labels_ab.call("_update")
			var _abc_ch: Array = _labels_abc_detail(_labels_ab)
			_chk("04-charge ABC 打开：屏内可见标签无一与 ABC 面板相交", bool(_abc_ch[0]), String(_abc_ch[1]))
			var _panel_ab: Array = _labels_panel_detail(_labels_ab)
			_chk("04-charge ABC 打开（双开）：屏内可见标签无一与场景面板相交", bool(_panel_ab[0]), String(_panel_ab[1]))
			_chk("04-charge ABC 打开：三号教学楼标签藏掉（在 ABC 矩形里）", not _label_visible(_labels_ab, "三号教学楼"), "visible=" + str(_label_visible(_labels_ab, "三号教学楼")))
			_chk("04-charge ABC 打开：创造力中心标签藏掉（在 ABC 矩形里）", not _label_visible(_labels_ab, "创造力中心"), "visible=" + str(_label_visible(_labels_ab, "创造力中心")))
			_chk("04-charge ABC 打开：配电房标签藏掉（在 ABC 矩形里）", not _label_visible(_labels_ab, "配电房"), "visible=" + str(_label_visible(_labels_ab, "配电房")))
			_chk("04-charge ABC 打开：配电变压器标签藏掉（在 ABC 矩形里）", not _label_visible(_labels_ab, "配电变压器"), "visible=" + str(_label_visible(_labels_ab, "配电变压器")))
			_chk("04-charge ABC 打开：储能 SOC 标签藏掉（在 ABC 矩形里）", not _soc_visible(_labels_ab), "visible=" + str(_soc_visible(_labels_ab)))
			_chk("04-charge ABC 打开：操场 · 田径场仍屏内可见（在 ABC 外，未被误藏）", _label_onscreen_visible(_labels_ab, "操场 · 田径场"), "visible=" + str(_label_visible(_labels_ab, "操场 · 田径场")))
			_chk("04-charge ABC 打开：充电区 · V2G 仍屏内可见（在 ABC 外，未被误藏）", _label_onscreen_visible(_labels_ab, "充电区 · V2G"), "visible=" + str(_label_visible(_labels_ab, "充电区 · V2G")))
			var _band_ab: Array = _labels_band_detail(_labels_ab)
			_chk("04-charge ABC 打开：屏内标签渲染中心都不进顶栏/场景栏（90≤y≤642）", bool(_band_ab[0]), String(_band_ab[1]))
			# 总览 ABC 打开放到新 phase 再量：先关 ABC、回总览（_restore_scene_state
			# 解除近拍 rig limits + 藏场景面板，见 phase 3 同款陷阱），切场景后等 4 帧。
			(_main.get_node("UI/ABCPanel") as Control).visible = false
			_main.get_node("UI").call("layout_panels")
			_main.call("_restore_scene_state")
			(_main.get_node("UI/ScenePanel") as Control).visible = false
			_main.call("_enter_instant", "overview")
			_phase = 8
		return false
	if _phase == 8:
		if _frames >= 31:
			# 总览无场景面板：ABC 单开，rect 同为 (720,60,548,380)。
			(_main.get_node("UI/ABCPanel") as Control).visible = true
			_main.get_node("UI").call("layout_panels")
			_phase = 9
		return false
	if _phase == 9:
		if _frames >= 35:
			# ---- 总览 ABC 打开（本轮主修，标签最密的一处）：当前总览屏内可见
			# 18 条（一号锚点修补后），其中 7 条在 ABC 矩形里（二号 0.29、实验楼 0.45、
			# 创造力中心 1.0、餐厅 1.0、配电房 1.0、配电变压器 0.46、储能 SOC 1.0）；
			# 修后 6 条藏掉，储能 SOC 走 +88 档逃到 ABC 底边之下（y381→469，字盒顶 454 ≥ ABC 底 440），
			# 宿舍楼 A/B 各被它顶下 +22（511→533、563→585），仍在面板外、无新重叠；
			# 一号教学楼盒右缘 688.5 < ABC 左缘 720，不在 ABC 矩形里，打开态仍可见。
			var _labels_ov2 = _main.get_node("Labels")
			_labels_ov2.call("_update")
			var _abc_ov: Array = _labels_abc_detail(_labels_ov2)
			_chk("总览 ABC 打开：屏内可见标签无一与 ABC 面板相交", bool(_abc_ov[0]), String(_abc_ov[1]))
			_chk("总览 ABC 打开：二号教学楼标签藏掉（在 ABC 矩形里）", not _label_visible(_labels_ov2, "二号教学楼"), "visible=" + str(_label_visible(_labels_ov2, "二号教学楼")))
			_chk("总览 ABC 打开：实验楼标签藏掉（在 ABC 矩形里）", not _label_visible(_labels_ov2, "实验楼"), "visible=" + str(_label_visible(_labels_ov2, "实验楼")))
			_chk("总览 ABC 打开：创造力中心标签藏掉（在 ABC 矩形里）", not _label_visible(_labels_ov2, "创造力中心"), "visible=" + str(_label_visible(_labels_ov2, "创造力中心")))
			_chk("总览 ABC 打开：餐厅标签藏掉（在 ABC 矩形里）", not _label_visible(_labels_ov2, "餐厅 · 学术报告厅"), "visible=" + str(_label_visible(_labels_ov2, "餐厅 · 学术报告厅")))
			_chk("总览 ABC 打开：配电房标签藏掉（在 ABC 矩形里）", not _label_visible(_labels_ov2, "配电房"), "visible=" + str(_label_visible(_labels_ov2, "配电房")))
			_chk("总览 ABC 打开：配电变压器标签藏掉（在 ABC 矩形里）", not _label_visible(_labels_ov2, "配电变压器"), "visible=" + str(_label_visible(_labels_ov2, "配电变压器")))
			var _soc_sp2 := _soc_sp(_labels_ov2)
			_chk("总览 ABC 打开：储能 SOC 走 +88 档逃到 ABC 底边之下（455≤y≤485）", _soc_onscreen_visible(_labels_ov2) and _soc_sp2.y >= 455.0 and _soc_sp2.y <= 485.0, "y=" + str(_soc_sp2.y))
			# 一号教学楼标签（F1 取景代价已修回，main.gd _apply_bldA_anchor）：
			# 总览锚点改用屋顶北缘高位 (-53,23,-37)，+44 档落到 (630,316)，盒右缘
			# 688.5 < ABC 左缘 720，不在 ABC 矩形里；ABC 打开态仍可见，不是误藏。
			_chk("总览 ABC 打开：一号教学楼仍屏内可见（一号锚点修补，在 ABC 矩形外）", _label_onscreen_visible(_labels_ov2, "一号教学楼"), "visible=" + str(_label_visible(_labels_ov2, "一号教学楼")))
			_chk("总览 ABC 打开：宿舍楼 A 仍屏内可见（被 SOC 顶下 +22，仍在面板外）", _label_onscreen_visible(_labels_ov2, "宿舍楼 A"), "visible=" + str(_label_visible(_labels_ov2, "宿舍楼 A")))
			var _band_ov2: Array = _labels_band_detail(_labels_ov2)
			_chk("总览 ABC 打开：屏内标签渲染中心都不进顶栏/场景栏（90≤y≤642）", bool(_band_ov2[0]), String(_band_ov2[1]))
			# 关闭 ABC：总览应恢复 18 条（一号锚点修补已修回、三号 F3 已修回；
			# 关上面板不误藏的回归对照）。
			(_main.get_node("UI/ABCPanel") as Control).visible = false
			_main.get_node("UI").call("layout_panels")
			_labels_ov2.call("_update")
			var _n_back := 0
			for _d4 in _labels_ov2.defs:
				var _l4: Label3D = _d4["label"]
				if not _l4.visible:
					continue
				var _sp4: Vector2 = (_labels_ov2.camera as Camera3D).unproject_position(_l4.position)
				if _sp4.x >= 0.0 and _sp4.x <= 1280.0 and _sp4.y >= 0.0 and _sp4.y <= 720.0:
					_n_back += 1
			_chk("总览 ABC 关闭后：屏内可见恢复 18 条（一号锚点修补已修回，三号 F3 已修回）", _n_back == 18, "onscreen=" + str(_n_back))
			# 动效闪现放到新 phase 再量：进储能场景、等 4 帧让面板排版定型。
			_main.call("_restore_scene_state")
			(_main.get_node("UI/ABCPanel") as Control).visible = false
			_main.get_node("UI").call("layout_panels")
			_main.call("_enter_instant", "storage")
			_phase = 10
		return false
	if _phase == 10:
		if _frames >= 39:
			# ---- 场景面板进场动效（180ms scale 0.95→1.0，origin 右缘）：
			# 动效期间 get_global_rect() 比终态小一圈（左缘 +18px、底边 −28px），
			# 修前标签按实时 rect 碰撞，终态应藏掉的可能先可见、下一轮 _update
			# 才藏掉（闪现约 150ms）。修后 labels.gd 用 _final_rect（终态 rect）
			# 碰撞，动效中与终态的可见集合应一致。直接置 scale 0.95 模拟动效中段
			#（与 _play_enter 同值同 pivot；真 tween 的时序不等，机制等价），
			# 不等真 tween 跑完，免得帧预算超 60。
			var _labels_an = _main.get_node("Labels")
			var _p_an: Control = _main.get_node("UI/ScenePanel")
			_p_an.pivot_offset = Vector2(_p_an.size.x, 0)
			_p_an.scale = Vector2(0.95, 0.95)
			var _fr_an = _labels_an.call("_final_rect", _p_an)
			_labels_an.call("_update")
			var _mid_an: Array = _vis_set(_labels_an)
			_p_an.scale = Vector2.ONE
			var _fin_rect_an: Rect2 = _p_an.get_global_rect()
			_labels_an.call("_update")
			var _fin_an: Array = _vis_set(_labels_an)
			_chk("场景面板动效中：_final_rect(0.95) = 终态 rect（±1px）", _fr_an is Rect2 and _rect_close(_fr_an, _fin_rect_an, 1.0), "mid=" + str(_fr_an) + " fin=" + str(_fin_rect_an))
			_chk("场景面板动效中：标签可见集合与终态一致（无闪现）", _mid_an == _fin_an, "mid=" + str(_mid_an) + " fin=" + str(_fin_an))
			_chk("场景面板动效中：储能 SOC 终态仍可见（未被终态 rect 误藏）", _fin_an.has("[soc]"), "fin=" + str(_fin_an))
			# ABC 动效放到新 phase 再量：打开 ABC、等 4 帧让面板排版定型。
			(_main.get_node("UI/ABCPanel") as Control).visible = true
			_main.get_node("UI").call("layout_panels")
			_phase = 11
		return false
	if _phase == 11:
		if _frames >= 43:
			# ---- ABC 面板进场动效（同 180ms scale 0.95→1.0，origin 右缘）：
			# 动效期间 rect 左缘 +27px、底边 −19px；修前储能 ABC 打开态 SOC 标签
			# 终态 overlap 仅 0.09，动效中段实测会闪现（mid 含 SOC、fin 不含）。
			# 修后 _final_rect 碰撞，mid 与 fin 应一致、SOC 动效中也不出现。
			# ABC 是直接置 visible（?abc=1 同款，不走进入 tween），无真 tween 在跑。
			var _labels_ab2 = _main.get_node("Labels")
			var _a_an: Control = _main.get_node("UI/ABCPanel")
			_a_an.pivot_offset = Vector2(_a_an.size.x, 0)
			_a_an.scale = Vector2(0.95, 0.95)
			var _fr_ab = _labels_ab2.call("_final_rect", _a_an)
			_labels_ab2.call("_update")
			var _mid_ab: Array = _vis_set(_labels_ab2)
			_a_an.scale = Vector2.ONE
			var _fin_rect_ab: Rect2 = _a_an.get_global_rect()
			_labels_ab2.call("_update")
			var _fin_ab: Array = _vis_set(_labels_ab2)
			_chk("ABC 面板动效中：_final_rect(0.95) = 终态 rect（±1px）", _fr_ab is Rect2 and _rect_close(_fr_ab, _fin_rect_ab, 1.0), "mid=" + str(_fr_ab) + " fin=" + str(_fin_rect_ab))
			_chk("ABC 面板动效中：标签可见集合与终态一致（无闪现）", _mid_ab == _fin_ab, "mid=" + str(_mid_ab) + " fin=" + str(_fin_ab))
			_chk("ABC 面板动效中：储能 SOC 不闪现（终态藏掉，动效中也不出现）", not _mid_ab.has("[soc]"), "mid=" + str(_mid_ab))
			_chk("ABC 面板动效终态：只剩三号教学楼 / 配电房（与 89a06cf 探针一致）", _fin_ab == ["三号教学楼", "配电房"], "fin=" + str(_fin_ab))
			# ---- T2 变压器近景放到新 phase 再量：先关 ABC、回总览（_restore_scene_state
			# 解除储能区 rig limits + 藏场景面板，见 phase 3 同款陷阱），置 _close_cam
			# 再 _enter_instant("overview")，等 4 帧让 rig._process 按放宽 limits 定位后再量。
			(_main.get_node("UI/ABCPanel") as Control).visible = false
			_main.get_node("UI").call("layout_panels")
			_main.call("_restore_scene_state")
			(_main.get_node("UI/ScenePanel") as Control).visible = false
			_main._close_cam = true
			_main.call("_enter_instant", "overview")
			_phase = 12
		return false
	if _phase == 12:
		if _frames >= 47:
			# ---- T2 变压器围栏近景（总览全景验收待确认项 1b6fee23）----
			# GLB 实测口径（ov-transformer.glb 与 overview.glb 同值）：围栏 7.5×5.5m、
			# 12 立柱（x 70.25–77.75、z −32.75–−27.25）+ 上下两道横杆（y 0.6/1.1），
			# 立柱中心 y 0.6、底 y 0（贴地、不埋地、不悬空）；箱体 x 71.2–76.8、
			# z −31.7–−28.3，四边净空 x 0.95m、z 1.05m，围栏完整包住箱体。
			var _rig12 = _main.rig
			_chk("T2 近景机位：dist 14m（不是总览 275m）", absf(_rig12.dist - 14.0) < 0.01, str(_rig12.dist))
			_chk("T2 近景机位：目标箱体中心 (74, 2.0, −30)", _rig12.target.is_equal_approx(Vector3(74.0, 2.0, -30.0)), str(_rig12.target))
			_chk("T2 近景机位：东南侧高处 az≈0.73 / el≈0.29", absf(_rig12.az - 0.73) < 0.01 and absf(_rig12.el - 0.29) < 0.01, "az=" + str(_rig12.az) + " el=" + str(_rig12.el))
			var _cam12: Camera3D = _main.rig as Camera3D
			# 围栏包住箱体：立柱矩形（x 70.25–77.75、z −32.75–−27.25）四边都比
			# 箱体（x 71.2–76.8、z −31.7–−28.3）各外扩 ≥0.9m（GLB 实测值，非估算）。
			_chk("T2：围栏完整包住箱体（四边净空 x 0.95m / z 1.05m）", 70.25 < 71.2 and 77.75 > 76.8 and -32.75 < -31.7 and -27.25 > -28.3, "fence x 70.25–77.75 z −32.75–−27.25 / body x 71.2–76.8 z −31.7–−28.3")
			# 近景取景：围栏四角、箱体顶角、绝缘子顶（y 5.43）全在屏内；南侧横杆
			# 屏上跨度 >250px（围栏不是远处小点，是可看清的近景）。
			var _frame_pts: Array = [Vector3(70.25, 0.0, -27.25), Vector3(77.75, 0.0, -27.25), Vector3(70.25, 1.2, -32.75), Vector3(77.75, 1.2, -32.75), Vector3(71.2, 4.0, -28.3), Vector3(76.8, 4.0, -31.7), Vector3(74.0, 5.43, -30.0)]
			var _frame_ok := true
			var _frame_detail := ""
			for _fp in _frame_pts:
				var _sp12: Vector2 = _cam12.unproject_position(_fp)
				if _sp12.x < 0.0 or _sp12.x > 1280.0 or _sp12.y < 0.0 or _sp12.y > 720.0:
					_frame_ok = false
					_frame_detail += str(_fp) + "->" + str(_sp12) + " "
			_chk("T2 近景：围栏四角 + 箱体顶角 + 绝缘子顶全在屏内", _frame_ok, _frame_detail)
			var _s_a: Vector2 = _cam12.unproject_position(Vector3(70.25, 0.6, -27.25))
			var _s_b: Vector2 = _cam12.unproject_position(Vector3(77.75, 0.6, -27.25))
			_chk("T2 近景：南侧围栏屏上跨度 >250px（可看清，非远处小点）", _s_a.distance_to(_s_b) > 250.0, "span=" + str(_s_a.distance_to(_s_b)) + " a=" + str(_s_a) + " b=" + str(_s_b))
			# GLB/回退双分支（套件现有模式：storage 壳检查同款）：CI 先 --import，
			# overview.glb 能加载、走 GLB 路径查围栏节点；本地无头未 --import 时
			# 6 个场景 GLB 全加载失败、走程序化回退，围栏是 GLB 专属件（程序化
			# _build_transformer 只建基座/箱体/绝缘子、无围栏），节点检查不适用、
			# 只查程序化箱体在场 + 注明跳过原因，不把环境缺失记成产品失败。
			var _glb12: bool = GlbLoader.was_loaded("overview")
			var _ov12 = _main.get_node_or_null("Campus/OverviewGLB")
			if _glb12:
				_chk("T2：总览 GLB 已接管（OverviewGLB 在场）", _ov12 != null, "node=" + str(_ov12))
			if not _glb12:
				print("T2-SKIP: overview.glb 未加载（本地无头未 --import），围栏节点检查跳过，CI 跑 GLB 路径")
				var _tf12: Node3D = _main.campus.transformer_group
				_chk("T2（回退）：程序化变压器组在场、位置 (74,0,−30)", _tf12 != null and _tf12.global_position.is_equal_approx(Vector3(74.0, 0.0, -30.0)), str(_tf12))
			if _glb12 and _ov12 != null:
				var _post_xz: Array = [[70.25, -27.25], [70.25, -32.75], [72.125, -27.25], [72.125, -32.75], [74.0, -27.25], [74.0, -32.75], [75.875, -27.25], [75.875, -32.75], [77.75, -27.25], [77.75, -32.75], [70.25, -30.0], [77.75, -30.0]]
				var _posts_ok := true
				var _posts_bad := ""
				for _pi in range(12):
					var _pn: Node3D = _ov12.find_child("TF_FencePost%02d" % (_pi + 1), true, false) as Node3D
					if _pn == null or not _pn.visible or absf(_pn.global_position.y - 0.6) > 0.01 or absf(_pn.global_position.x - float(_post_xz[_pi][0])) > 0.01 or absf(_pn.global_position.z - float(_post_xz[_pi][1])) > 0.01:
						_posts_ok = false
						_posts_bad += "Post%02d " % (_pi + 1)
				_chk("T2：围栏 12 立柱全在场、可见、贴地（中心 y 0.6，底 y 0）", _posts_ok, _posts_bad)
				# 横杆不按名查找：GLB 里名含小数点（TF_FenceRail_x_S_0.6），Godot 导入
				# 改名、find_child 找不到（CI run 45289609797：8 根全报缺失，而无点号
				# 的立柱/箱体全找到；GLB 文件里 8 根都在）。改按位置 + 长边尺寸找：
				# x 向横杆中心 (74, y, ±27.25/32.75)、长边 x>7m；y 向横杆中心
				# (±70.25/77.75, y, -30)、长边 z>5m；立柱细（0.08）高（1.2），
				# 尺寸上不会误认。detail 打印导入后的真名，供后人核对。
				var _ov_all: Array[Node] = [_ov12]
				var _ov_i := 0
				while _ov_i < _ov_all.size():
					for _ov_c in _ov_all[_ov_i].get_children():
						_ov_all.append(_ov_c)
					_ov_i += 1
				var _rail_specs: Array = [[Vector3(74.0, 0.6, -27.25), "x"], [Vector3(74.0, 0.6, -32.75), "x"], [Vector3(70.25, 0.6, -30.0), "y"], [Vector3(77.75, 0.6, -30.0), "y"], [Vector3(74.0, 1.1, -27.25), "x"], [Vector3(74.0, 1.1, -32.75), "x"], [Vector3(70.25, 1.1, -30.0), "y"], [Vector3(77.75, 1.1, -30.0), "y"]]
				var _rails_ok := true
				var _rails_bad := ""
				var _rails_found := ""
				for _rs in _rail_specs:
					var _rc: Vector3 = _rs[0]
					var _r_found := false
					for _nd in _ov_all:
						var _mi := _nd as MeshInstance3D
						if _mi == null or not _mi.visible:
							continue
						if not _mi.global_position.is_equal_approx(_rc):
							continue
						var _sz: Vector3 = _mi.get_aabb().size
						if String(_rs[1]) == "x" and _sz.x > 7.0 and _sz.y < 0.1:
							_r_found = true
							_rails_found += _mi.name + " "
						elif String(_rs[1]) == "y" and _sz.z > 5.0 and _sz.y < 0.1:
							_r_found = true
							_rails_found += _mi.name + " "
					if not _r_found:
						_rails_ok = false
						_rails_bad += str(_rc) + " "
				_chk("T2：围栏 8 横杆全在场、可见（上下两道 y 0.6/1.1）", _rails_ok, _rails_bad + "found=[" + _rails_found + "]")
				var _body12: Node3D = _ov12.find_child("TF_Body", true, false) as Node3D
				var _body_sp := Vector2(-1, -1)
				if _body12 != null:
					_body_sp = _cam12.unproject_position(_body12.global_position)
				_chk("T2 近景：箱体在场、可见、屏内（无回归）", _body12 != null and _body12.visible and _body_sp.x >= 0.0 and _body_sp.x <= 1280.0 and _body_sp.y >= 0.0 and _body_sp.y <= 720.0, "body=" + str(_body12) + " sp=" + str(_body_sp))
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
	# F4（2026-11-24）：雾 0.0005→0.0002——晴天总览地面偏淡，雾色偏蓝是其中一份。
	_chk("fog density 0.0002 (F4: less blue haze)", absf(wsys2.env.environment.fog_density - 0.0002) < 0.00001, str(wsys2.env.environment.fog_density))
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
	# ---- 回退分支修补：S2 PCS 柜落基座顶 / S4 车顶 SOC 条贴车舱顶 ----
	var pcs_box: MeshInstance3D = null
	var st_base: MeshInstance3D = null
	for ch3 in cb.storage_group.get_children():
		if ch3 is MeshInstance3D:
			var mi3 := ch3 as MeshInstance3D
			if mi3.mesh is BoxMesh and (mi3.mesh as BoxMesh).size.is_equal_approx(Vector3(1.6, 3.2, 1.4)):
				pcs_box = mi3
			if mi3.mesh is BoxMesh and (mi3.mesh as BoxMesh).size.is_equal_approx(Vector3(10, 0.4, 6)):
				st_base = mi3
	_chk("S2 PCS 柜中心 y=2.0", pcs_box != null and absf(pcs_box.position.y - 2.0) < 0.001, str(pcs_box.position.y) if pcs_box != null else "null")
	_chk("S2 PCS 柜底 0.40 落在基座顶（不埋入）", pcs_box != null and st_base != null and absf((pcs_box.position.y - 1.6) - (st_base.position.y + 0.2)) < 0.001, str(pcs_box.position.y - 1.6) + " vs " + str(st_base.position.y + 0.2) if pcs_box != null and st_base != null else "null")
	var cabin_top_y := 0.0
	for ch4 in cg.get_children():
		if ch4 is MeshInstance3D:
			var mi4 := ch4 as MeshInstance3D
			if mi4.mesh is BoxMesh and (mi4.mesh as BoxMesh).size.is_equal_approx(Vector3(2.0, 0.7, 1.6)):
				cabin_top_y = mi4.position.y + 0.35
				break
	var fills_ok: bool = cb.car_fills.size() == 3
	var fills_y_ok := true
	for c in cb.car_fills:
		var fl := c["fill"] as MeshInstance3D
		if absf(fl.position.y - 1.84) >= 0.001 or absf((fl.position.y - 0.09) - cabin_top_y) >= 0.001:
			fills_y_ok = false
	_chk("S4 车顶 SOC 条中心 y=1.84（3 辆）", fills_ok and fills_y_ok, str(cb.car_fills.size()))
	_chk("S4 车顶 SOC 条底 1.75 贴合车舱顶（不悬空）", fills_ok and fills_y_ok, "cabin_top=" + str(cabin_top_y))
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
