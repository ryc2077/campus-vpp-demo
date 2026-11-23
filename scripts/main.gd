extends Node3D
## 主控制器：读 data/*.json → 建校园 → 跑 96 点仿真 → 场景进出（两段飞入 1 秒）→
## 面板/图表/天气/标签联动。权威数字只来自 JSON，不写死在代码里。

const ClassroomInteriorScene := preload("res://scenes/classroom_interior.tscn")
const DistInteriorScene := preload("res://scenes/dist_interior.tscn")
const StorageInteriorScene := preload("res://scenes/storage_interior.tscn")
const PvDetailScene := preload("res://scenes/pv_detail.tscn")
const ChargeDetailScene := preload("res://scenes/charge_detail.tscn")
const GlbLoader = preload("res://scripts/glb_loader.gd")

var campus_data: Dictionary = {}
var strat_data: Dictionary = {}
var bill_data: Dictionary = {}
var weather_data: Dictionary = {}
var classroom_data: Dictionary = {}
var scenes_data: Dictionary = {}

var sim := SimEngine.new()
var cls_model: ClassroomModel
var cls_results: Dictionary = {}
var cls_strategy := "opt"

var current_wx: Dictionary = {}
var hour := 9.0
var playing := false
var active_scene := ""
var shell_open := false
var _pending_entry := ""
var _pending_exit := false
var _panel_ms := 0
var _t := 0.0
var _shot_mode := false
var _url_params := {} # ?scene=&wx=&hour=&fallback=&close=…：_ready 开头解析一次，build 前置开关用
var _close_cam := false # ?close=1：储能场景改用柜面近拍机位（截图验收用）
var _freeze_u := -1.0 # ?freeze=0..1：冻结在飞行进度 u 处（慢速/逐帧检查缓动与弧线）
var _glass_mode := "auto" # ?glass=0 关闭 / low 低质量 / high 高质量 / auto（窄屏自动降质）
var _reduced := false # 减弱动效：停闪电/云漂移/树摆（P3-4），由 _set_reduced_motion 设置
var _last_vp_w := 0.0
var ui_font: Font # 中文字体：启动时加载，全 UI 的文字控件都显式挂上它

@onready var rig: CameraRig = $CameraRig
@onready var campus: CampusBuilder = $Campus
@onready var weather: WeatherSystem = $Weather
@onready var labels: Labels3D = $Labels
@onready var ui: UIController = $UI
@onready var panel: ScenePanel = $UI/ScenePanel
@onready var sun: DirectionalLight3D = $Sun
@onready var env_node: WorldEnvironment = $WorldEnvironment

var cls_interior: ClassroomInterior
var dist_interior: DistInterior
var sto_interior: StorageInterior
var pv_detail: PvDetail
var chg_detail: ChargeDetail
var _storage_label: Dictionary = {}
var _shell_mat: StandardMaterial3D

func _ready() -> void:
	# 字体兜底：project.godot 的 gui/theme/default_font 在本工程实测未生效
	# （ThemeDB.fallback_font 仍是内置字体，中文变 □；fonttest2 已验证），
	# 启动时显式赋值（在首帧绘制前完成，全部 Control 与 Label3D 都跟新 fallback 走）。
	var _ui_font := load("res://assets/fonts/NotoSansSC-Regular.ttf") as Font
	if _ui_font != null:
		# 脚本支持兜底：字体导入时 script_support 为空（.import 里 language_support/script_support
		# 均为 {}），TextServer 会因此跳过该字体去排 Han 文本，拉丁字符走内置字体能显示，
		# 中文无处可去就画成带十六进制码点的方框。显式声明它覆盖的脚本。
		_ui_font.set_script_support_override("Hani", true) # 汉字
		_ui_font.set_script_support_override("Latn", true) # 拉丁
		_ui_font.set_script_support_override("Zyyy", true) # 通用（数字/标点/℃/·/×/㎡）
		_ui_font.set_script_support_override("Zinh", true) # 继承（组合记号）
		ui_font = _ui_font
		ThemeDB.fallback_font = _ui_font
		# 关键：只改 ThemeDB.fallback_font / Theme.default_font 不够——引擎默认主题里
		# 每个控件类都有一条指向内置字体的 "font" 主题项，查找时先命中它，根本走不到
		# fallback；且 CanvasLayer 会截断窗口主题变更通知，$UI 下的控件在入树时已缓存
		# 了内置字体。必须逐类把 "font" 主题项指到中文字体上（实测 TitleLabel 仍解析到内置字体），
		# 再对全 UI 逐控件加 add_theme_font_override（最高优先级，见 _apply_ui_font）。
		var _ui_theme := Theme.new()
		_ui_theme.set_font("font", "Label", _ui_font)
		_ui_theme.set_font("font", "Button", _ui_font)
		_ui_theme.set_font("font", "OptionButton", _ui_font)
		_ui_theme.set_font("font", "PopupMenu", _ui_font)
		_ui_theme.set_font("font", "MenuButton", _ui_font)
		_ui_theme.default_font = _ui_font
		get_window().theme = _ui_theme
		# Label3D 不走 Control 主题，直接给字体（labels.gd 的 add_label 里用）。
		labels.font = _ui_font
		# 动态生成的行/按钮（scene_panel.build/set_live、ui_controller._mk_label）创建时
		# 也挂字体（各自的 font 变量，见对应文件）。
		panel.font = _ui_font
		ui.font = _ui_font
	# （中文 tofu 已修好：字体见上方三重兜底 + 静态子集；诊断打印已删。）
	campus_data = DataLoader.load_json("res://data/campus.json")
	strat_data = DataLoader.load_json("res://data/strategies.json")
	bill_data = DataLoader.load_json("res://data/bill.json")
	weather_data = DataLoader.load_json("res://data/weather.json")
	classroom_data = DataLoader.load_json("res://data/classroom.json")
	scenes_data = DataLoader.load_json("res://data/scenes.json")
	# 当前天气：可变字典，仿真与教室模型共用同一份引用
	current_wx = (weather_data["presets"]["sunny"] as Dictionary).duplicate()
	# URL 参数必须在 campus.build() 之前解析：?fallback=1 要赶在 GLB 加载前
	# 置起 GlbLoader.force_fallback，否则回退演练来不及生效；?close=1 只记
	# 标志，机位在 _enter_instant 里用。天气/时刻等仍由 _apply_url_params
	# 在后面按同一份 _url_params 应用，不重复解析。
	_url_params = _parse_url_params()
	if str(_url_params.get("fallback", "")) in ["1", "true", "on"]:
		GlbLoader.force_fallback = true
	_close_cam = _url_params.has("close")
	_rebuild_sim()
	cls_model = ClassroomModel.new(classroom_data, current_wx, sim.price_at, sim.sun_shape)
	_rebuild_classroom()
	campus.build(campus_data)
	weather.setup(weather_data, sun, env_node)
	_setup_labels()
	_setup_interiors()
	_setup_ui()
	# _shell_mat：GLB 已接管时指 GLB 壳材质（storage_glb_shell_mats[0]=Storage_Shell），
	# SOC 变色（_update_visuals）才在可见的 GLB 壳上生效；GLB 加载失败走回退时
	# storage_glb_shell_mats 为空，仍指程序化壳材质（storage_group 未隐藏）。
	if not campus.storage_glb_shell_mats.is_empty():
		_shell_mat = campus.storage_glb_shell_mats[0]
	else:
		_shell_mat = (campus.storage_shell[0].material_override as StandardMaterial3D) if not campus.storage_shell.is_empty() else null
	_apply_url_params()
	labels.debug_shot = _shot_mode # Round 2：shot 模式才打印标签去重叠诊断
	_setup_glass()
	if ui_font != null:
		_apply_ui_font($UI)
	if not _shot_mode:
		rig.fly_to(scenes_data["overview"]["cam"], 1000)
	else:
		_snap_to(scenes_data["overview"]["cam"])

func _apply_ui_font(n: Node) -> void:
	# 递归给 $UI 下所有文字控件加字体 override（最高优先级）；场景切换后
	# 新建的行由 scene_panel/ui_controller 创建时自己挂（font 变量），这里只兜底静态部分。
	if n is Label or n is Button or n is OptionButton:
		(n as Control).add_theme_font_override("font", ui_font)
	for c in n.get_children():
		_apply_ui_font(c)

func _rebuild_sim() -> void:
	var p := {
		"cap": 215.0, "pow": 100.0, "reserve_pct": 0.556,
		"pv_cap": float(bill_data["pv"]["capacity_kwp"]), "load_pk": 1100.0,
		"ac_set": 26.5, "ev_rate": 0.30,
		"price_peak": float(bill_data["price"]["peak_yuan_per_kwh"]),
		"price_flat": float(bill_data["price"]["flat_yuan_per_kwh"]),
		"price_valley": float(bill_data["price"]["valley_yuan_per_kwh"]),
		"cf_avg": float(bill_data["carbon_factor_kg_per_kwh"]),
	}
	sim.build(p, current_wx)

func _rebuild_classroom() -> void:
	cls_results = {
		"gate": cls_model.simulate("gate"),
		"const": cls_model.simulate("const"),
		"opt": cls_model.simulate("opt"),
	}

func _setup_labels() -> void:
	labels.camera = rig
	labels.panel_control = panel # 场景面板实时 rect 作标签碰撞区（labels.gd 内取，不硬编码像素）
	labels.abc_panel_control = $UI/ABCPanel # ABC 面板实时 rect 作标签碰撞区，同一模式；关闭时不碰撞
	for b in campus_data["buildings"]:
		var pos: Array = b["pos"]
		var anchor := Vector3(pos[0], float(b["height"]) + 2.0, pos[1])
		if String(b["id"]) == "bldC":
			# F3（三号教学楼总览标签缺失，run 45261531067）：楼顶锚点 (26,16,-30)
			# 在总览屏上被配电房/SOC/餐厅九档全堵死（探针逐档复算），楼顶四个角
			# 与楼顶边缘锚点全军覆没。楼南侧低位 (17,8,-20) 是总览唯一活口：
			# 屏上 (724,346)，+88 档落到 (724,434)，楼南立面正下方空地，
			# 不撞任何标签；但同锚点在 charge 会误现、storage 会落到屏外，
			# 所以锚点按场景分（见 _apply_c3_anchor）：总览用 (17,8,-20)，
			# 其余场景用楼顶 (26,16,-30)。启动即总览，先按总览锚点建。
			anchor = Vector3(17, 8, -20)
		if String(b["id"]) == "bldA":
			# 一号教学楼总览标签修补（F1 取景代价，run 45261531067 之后）：
			# 总览 dist 275 后，楼顶锚点 (-56,21,-30) 屏上与屋顶光伏锚点只差约
			# 10px，九档全堵死（探针逐档复算：0/±22/−44 撞屋顶光伏，
			# +44/+66/+88 只差操场盒 8px 横向重叠，−66/−88 撞艺体馆）。
			# 总览改用屋顶北缘高位 (-53,23,-37)：仍在屋顶上方（x −53 在楼长
			# −76..−36 内、z −37 在楼宽 −37.5..−22.5 内、y 23 为屋顶 +4m，
			# occ=false），屏上 (630,272)，+44 档落到 (630,316)，与屋顶光伏盒底
			# 净空约 39px、与操场盒右缘约 8px、与二号 +88 档约 8px；
			# 唯一连带是二号教学楼 +44→+88（329.8→373.8），其余标签不动。
			# 其余场景用楼顶原锚点（见 _apply_bldA_anchor），启动即总览，先按总览锚点建。
			anchor = Vector3(-53, 23, -37)
		labels.add_label(String(b["name"]), DataLoader.color_from_hex("#17557f"), int(b["label_prio"]), anchor)
	for e in campus_data["labels_extra"]:
		var pos: Array = e["pos"]
		# F2（配电变压器标签错位）：pin 见 labels.gd 规则 6——锚点本身没错，
		# 投影距箱体顶面中心仅约 13px，是去重叠 +44 档把它顶到宿舍楼 A 屋顶。
		var pin := String(e["text"]) == "配电变压器"
		labels.add_label(String(e["text"]), DataLoader.color_from_hex(e["color"]), int(e["prio"]), Vector3(pos[0], pos[1], pos[2]), "", pin)
	labels.add_label("操场 · 田径场", Color("#c2503f"), int(campus_data["playground"]["label_prio"]), Vector3(-80, 5, 25))
	labels.add_label("池塘", Color("#2e7f86"), int(campus_data["pond"]["label_prio"]), Vector3(82, 2.5, 78))
	labels.add_label("充电区 · V2G", Color("#9a3412"), int(campus_data["charge"]["label_prio"]), Vector3(44, 8.4, 76))
	labels.add_label("南门", Color("#17557f"), int(campus_data["gate"]["label_prio"]), Vector3(0, 8.5, 98))
	_storage_label = labels.add_label("储能柜 · SOC 90%", Color("#047857"), 0, Vector3(64, 9.6, -30), "soc")

func _setup_interiors() -> void:
	cls_interior = ClassroomInteriorScene.instantiate()
	cls_interior.position = Vector3(-56, 0, -30)
	cls_interior.visible = false
	add_child(cls_interior)
	dist_interior = DistInteriorScene.instantiate()
	dist_interior.position = Vector3(48, 0, -30)
	dist_interior.visible = false
	add_child(dist_interior)
	sto_interior = StorageInteriorScene.instantiate()
	sto_interior.position = Vector3(64, 0, -30)
	sto_interior.visible = false
	add_child(sto_interior)
	pv_detail = PvDetailScene.instantiate()
	pv_detail.position = Vector3(-56, 19.15, -30)
	pv_detail.visible = false
	add_child(pv_detail)
	chg_detail = ChargeDetailScene.instantiate()
	chg_detail.position = Vector3.ZERO
	chg_detail.visible = true # 弧线在总览也可见
	add_child(chg_detail)

func _setup_ui() -> void:
	ui.setup(strat_data, weather_data["order"], weather_data["presets"])
	ui.scene_selected.connect(enter_scene)
	ui.weather_selected.connect(set_weather)
	ui.play_toggled.connect(func(p: bool) -> void: playing = p)
	ui.time_changed.connect(func(h: float) -> void:
		hour = h
		_refresh_panel()
	)
	panel.strategy_changed.connect(func(v: String) -> void:
		cls_strategy = v
		panel.set_strategy_sel(v)
		_refresh_panel()
	)
	panel.shell_toggled.connect(func(open: bool) -> void:
		shell_open = open
		campus.set_shell_translucent(open)
	)
	panel.back_pressed.connect(func() -> void: exit_scene())

## URL 查询参数解析（web 才有；非 web 返回空字典）。_ready 开头调一次，
## _apply_url_params 复用结果，不重复解析。
func _parse_url_params() -> Dictionary:
	var params := {}
	if not OS.has_feature("web"):
		return params
	var search: String = str(JavaScriptBridge.eval("window.location.search"))
	if search == "" or search == "null":
		return params
	for part in search.trim_prefix("?").split("&"):
		var kv := part.split("=")
		if kv.size() == 2:
			params[kv[0]] = kv[1]
	return params

func _apply_url_params() -> void:
	# 调试图：?scene=pv&wx=rain&hour=12&shot=1（shot=1 时直接落位、不飞行动画，供截图验收）
	# ?freeze=0.5：冻结在飞行中段（慢速/逐帧检查）；?slowmo=3：飞行时长 ×3；
	# ?reduced=1：减弱动效（等价于 prefers-reduced-motion）。
	# ?fallback=1：全部 GLB 加载失败、走程序化回退（回退分支演练截图用）；
	# ?close=1：储能场景改用柜面近拍机位（流光点验收用）。这两项在 _ready
	# 开头已按 _url_params 生效，这里只应用天气/时刻/场景等常规参数。
	if not OS.has_feature("web"):
		return
	# 系统减弱动效偏好：飞行改直接落位、面板只做透明度变化（review-animations 无障碍项）
	var rm: Variant = JavaScriptBridge.eval("window.matchMedia('(prefers-reduced-motion: reduce)').matches")
	if str(rm) == "true":
		_set_reduced_motion(true)
	var params := _url_params
	if params.has("reduced"):
		_set_reduced_motion(true)
	if params.has("slowmo"):
		rig.slowmo = clampf(float(params["slowmo"]), 1.0, 10.0)
	if params.has("freeze"):
		_freeze_u = clampf(float(params["freeze"]), 0.0, 1.0)
	# 天气参数：wx 与 weather 两个名字都接受，weather 优先（Round 2：
	# shots_all.sh 曾传 weather=rain 而这里只读 wx，导致 06/07 与晴天像素几乎相同）。
	if params.has("weather"):
		set_weather(str(params["weather"]))
	elif params.has("wx"):
		set_weather(str(params["wx"]))
	if params.has("hour"):
		hour = clampf(float(params["hour"]), 0.0, 24.0)
	if params.has("shot"):
		_shot_mode = true
	if params.has("glass"):
		match str(params["glass"]):
			"0", "off":
				_glass_mode = "off"
			"low":
				_glass_mode = "low"
			"high":
				_glass_mode = "high"
			_:
				_glass_mode = "auto"
	# 场景进入放到 _ready 之后一帧，避免与开场飞行冲突
	if params.has("scene"):
		var key := str(params["scene"])
		call_deferred("_deferred_enter", key)
	# ?abc=1：截图验收用，打开 ABC 对照面板（直接置 visible，不走进入动效，
	# 拍终态 rect；_deferred_enter 之后执行，场景面板已建好，layout_panels
	# 会把场景面板顶到 ABC 底边之下）。
	if params.has("abc"):
		call_deferred("_deferred_open_abc")

## 液态玻璃：窄屏（<760px）自动降质（5-tap + 4px）；?glass=0 关闭改实色 fallback。
func _setup_glass() -> void:
	var vp_w := get_viewport().get_visible_rect().size.x
	var low := vp_w < 760.0 or _glass_mode == "low"
	var on := _glass_mode != "off"
	# 池塘遮挡（run 45219977015 目视）：总览视角下池塘水面（overview.glb 的
	# OV_ASSEMBLY_pond；程序化池塘在 GLB 接管时已隐藏）投影落在底部场景栏上；
	# BarGlass 是半透明液态玻璃（tint_alpha 0.42）。run 45226479162 目视：
	# 总览改实色后可读，但场景页仍是半透明深色——按钮字是深色 #1e293b，
	# 透进来的光伏板/草地/柜体把非当前项压得几乎看不见，只有绿 pill 可读。
	# 旧逻辑只在总览关玻璃（active_scene == ""）、进场景又恢复玻璃，
	# 错把池塘当成唯一干扰源；场景画面本身同样 busy。所以场景栏全页
	# 走实色 fallback（白 0.93，已有降级件），与总览同一口径；改浅色字
	# 不行：玻璃底色随背景变（深蓝板/亮绿草），没有一种字色能处处达标，
	# 且要动 6 个按钮 + 悬停/按下态，改动远大于关玻璃。WxPill 不受影响。
	# 不移池塘/不改相机：池塘在 GLB 内、相机在 data/scenes.json（禁碰）；
	# 只抬高导航栏也盖不住椭圆（720p 下椭圆约 y 615–710、栏 652–708）。
	var bar_on := false
	for path in ["UI/SceneBar/BarGlass", "UI/WxPill/WxGlass"]:
		var g: GlassSurface = get_node_or_null(path)
		if g != null:
			g.set_quality(low)
			g.set_glass_enabled(bar_on if path == "UI/SceneBar/BarGlass" else on)

func _set_reduced_motion(on: bool) -> void:
	_reduced = on
	rig.reduced_motion = on
	panel.reduced_motion = on
	ui.reduced_motion = on
	weather.reduced_motion = on

func _deferred_enter(key: String) -> void:
	if _shot_mode and _freeze_u >= 0.0:
		_enter_frozen(key, _freeze_u)
	elif _shot_mode:
		_enter_instant(key)
	else:
		enter_scene(key)

func _deferred_open_abc() -> void:
	var abc_panel := get_node_or_null("UI/ABCPanel") as Control
	if abc_panel != null:
		abc_panel.visible = true
		ui.layout_panels()

## 三号教学楼标签锚点按场景分（F3）：总览是 18 标签密排地图，楼顶锚点在
## 总览屏上九档全堵死，改用楼南侧低位 (17,8,-20)；近景里同锚点会误现
##（charge）或落到屏外（storage），所以进场景切回楼顶 (26,16,-30)。
## 锚点是呈现锚点、随场景切，楼体本身不动。探针四场景矩阵（probe4）：
## (17,8,-20)：总览可见 (724,434)、charge 误现、storage 屏外；
## (26,16,-30)：总览藏、charge 藏、storage ABC 终态屏内可见。
## 在每次切场景的入口调用（_enter_instant/_enter_frozen/enter_scene/
## exit_scene），150ms 内下一轮 _update 即按新锚点重排。
func _apply_c3_anchor(overview: bool) -> void:
	for d in labels.defs:
		if String(d["text"]) == "三号教学楼":
			var a := Vector3(17, 8, -20) if overview else Vector3(26, 16, -30)
			d["anchor"] = a
			(d["label"] as Label3D).position = a
			return

## 一号教学楼标签锚点按场景分（F1 取景代价修补，F3 同模式）：总览是 18 标签密排地图，
## 楼顶原锚点 (-56,21,-30) 在总览屏上九档全堵死，改用屋顶北缘高位 (-53,23,-37)；
## 近景里同锚点会偏离楼顶（pv 场景一号楼是主角），所以进场景切回楼顶 (-56,21,-30)。
## 锚点是呈现锚点、随场景切，楼体本身不动。探针（probe_bldA_real / probe_bldA_fine，
## 用完已删）：(-53,23,-37) 总览可见 (630,316)，仅二号教学楼 +44→+88，
## 其余 16 条原地不动；(-52,21,-30) 等仍藏、北侧/西侧低位锚点 occ=true。
## 在每次切场景的入口调用（与 _apply_c3_anchor 同处）。
func _apply_bldA_anchor(overview: bool) -> void:
	for d in labels.defs:
		if String(d["text"]) == "一号教学楼":
			var a := Vector3(-53, 23, -37) if overview else Vector3(-56, 21, -30)
			d["anchor"] = a
			(d["label"] as Label3D).position = a
			return

## 冻结帧：总览 → 目标机位的飞行在进度 u 处定格（内景取第一段：总览 → 楼前）。
func _enter_frozen(key: String, u: float) -> void:
	_apply_c3_anchor(key == "overview")
	_apply_bldA_anchor(key == "overview")
	if key == "overview":
		_snap_to(scenes_data["overview"]["cam"])
		return
	_restore_scene_state()
	active_scene = key
	_show_panel_for(key)
	ui.set_scene_active(key)
	var from_cam: Dictionary = scenes_data["overview"]["cam"]
	var to_cam: Dictionary = scenes_data["scenes"][key]["cam"]
	if scenes_data["scenes"][key].has("front"):
		to_cam = scenes_data["scenes"][key]["front"]
	rig.apply_eased_between(from_cam, to_cam, u)
	_setup_glass() # 场景栏仍走实色底（不恢复玻璃）
	_refresh_panel()

func _snap_to(cam: Dictionary) -> void:
	var t: Array = cam["target"]
	rig.az = float(cam["az"])
	rig.el = float(cam["el"])
	rig.dist = float(cam["dist"])
	rig.target = Vector3(t[0], t[1], t[2])
	rig.cancel_flight()

## 测试模式：直接落位、不飞行动画。
func _enter_instant(key: String) -> void:
	# 直接落位 supersede 之前未完成的飞行入场：_snap_to 会 cancel_flight，
	# 若不清空 _pending_entry，下一帧 _process 会把 _finish_entry 抢跑、
	# 机位被抢回上一个场景（verify 里 enter_scene("dist") 后再
	# _enter_instant("storage") 即复现：机位回到配电房）。
	_pending_entry = ""
	_pending_exit = false
	_apply_c3_anchor(key == "overview")
	_apply_bldA_anchor(key == "overview")
	if key == "overview":
		_snap_to(scenes_data["overview"]["cam"])
		return
	_restore_scene_state()
	active_scene = key
	var sc: Dictionary = scenes_data["scenes"][key]
	_show_panel_for(key)
	if key == "classroom":
		campus.set_host_visible("bldA", false)
		cls_interior.visible = true
	elif key == "dist":
		campus.set_host_visible("dist", false)
		dist_interior.visible = true
	elif key == "storage":
		shell_open = true
		campus.set_shell_translucent(true)
		panel.set_shell_open(true) # 面板是进场前按 shell_open=false 建的，不同步文案会一直写“关”
		sto_interior.visible = true
	elif key == "pv":
		pv_detail.visible = true
	if key == "storage" and _close_cam:
		# 柜面近拍：正对 3 台电池柜前脸（世界 x 61.6–64.8、前脸 z −29.5），
		# 流光点 z −29.36 正贴柜面。dist 5m、目标柜面中心 (63.2, 1.4, −29.4)；
		# limits 的 dist 下限 8m 会把机位钳回 8m，近拍改用放宽的副本
		#（只改运行时 limits，不动 data/scenes.json）。
		_snap_to({"az": 0.0, "el": 0.18, "dist": 5.0, "target": [63.2, 1.4, -29.4]})
		var lim: Dictionary = (sc.get("limits", {}) as Dictionary).duplicate(true)
		lim["dist"] = [3.0, 36.0]
		rig.set_limits(lim)
		rig.arm_limits(true)
	else:
		_snap_to(sc["cam"])
		if sc.has("limits"):
			rig.set_limits(sc["limits"])
			rig.arm_limits(true)
	ui.set_scene_active(key)
	_setup_glass() # 场景栏仍走实色底（不恢复玻璃）
	_refresh_panel()

func set_weather(key: String) -> void:
	if not weather_data["presets"].has(key):
		return
	var p: Dictionary = weather_data["presets"][key]
	for k in p:
		current_wx[k] = p[k]
	weather.set_weather(key)
	_rebuild_sim()
	_rebuild_classroom()
	ui.set_weather_active(key)
	_refresh_panel()

func _scene_cam(key: String) -> Dictionary:
	return scenes_data["scenes"][key]["cam"]

func _restore_scene_state() -> void:
	# 恢复所有宿主楼体、藏起内景、关闭外壳半透明
	for id in ["bldA", "dist"]:
		campus.set_host_visible(id, true)
	cls_interior.visible = false
	dist_interior.visible = false
	sto_interior.visible = false
	pv_detail.visible = false
	if shell_open:
		shell_open = false
		campus.set_shell_translucent(false)
	rig.arm_limits(false)
	rig.set_limits({})

func _show_panel_for(key: String) -> void:
	var sc: Dictionary = scenes_data["scenes"][key]
	panel.visible = true
	var extra := ""
	if key == "classroom":
		extra = "classroom"
	elif key == "storage":
		extra = "storage"
	panel.build(String(sc["title"]), extra, shell_open)
	panel.set_strategy_sel(cls_strategy)
	var narrow := get_viewport().get_visible_rect().size.x < 760.0
	panel.set_minimized(narrow)
	ui.layout_panels()

func enter_scene(key: String) -> void:
	if key == "overview":
		exit_scene()
		return
	if not scenes_data["scenes"].has(key):
		return
	_apply_c3_anchor(false)
	_apply_bldA_anchor(false)
	# 从一个场景直切另一个：先恢复上一个场景的剖切，避免两套内景叠加
	_restore_scene_state()
	_pending_entry = ""
	_pending_exit = false
	active_scene = key
	_show_panel_for(key)
	ui.set_scene_active(key)
	var sc: Dictionary = scenes_data["scenes"][key]
	if key == "classroom" or key == "dist":
		# 两段飞行：楼前 500ms → 剖切 → 内景 500ms（合计 1 秒）
		_pending_entry = key
		rig.fly_to(sc["front"], 500, Callable(self, "_on_entry_phase2").bind(key))
	elif key == "storage":
		shell_open = true
		campus.set_shell_translucent(true)
		panel.set_shell_open(true) # 面板是进场前按 shell_open=false 建的，不同步文案会一直写“关”
		sto_interior.visible = true
		rig.fly_to(sc["cam"], 1000, Callable(self, "_on_landed").bind(key))
	elif key == "pv":
		pv_detail.visible = true
		rig.fly_to(sc["cam"], 1000, Callable(self, "_on_landed").bind(key))
	else:
		rig.fly_to(sc["cam"], 1000, Callable(self, "_on_landed").bind(key))
	_setup_glass() # 场景栏仍走实色底（不恢复玻璃）
	_refresh_panel()

func _on_entry_phase2(key: String) -> void:
	if active_scene != key:
		return
	_pending_entry = ""
	_finish_entry(key)
	rig.fly_to(_scene_cam(key), 500, Callable(self, "_on_landed").bind(key))

func _finish_entry(key: String) -> void:
	# 飞行被用户拖动打断时直接完成剖切并落到内景机位，避免停在实心楼体里贴墙
	if key == "classroom":
		campus.set_host_visible("bldA", false)
		cls_interior.visible = true
	elif key == "dist":
		campus.set_host_visible("dist", false)
		dist_interior.visible = true
	_snap_to(_scene_cam(key))
	rig.set_limits(scenes_data["scenes"][key]["limits"])
	rig.arm_limits(true)

func _on_landed(key: String) -> void:
	if active_scene != key:
		return
	if scenes_data["scenes"][key].has("limits"):
		rig.set_limits(scenes_data["scenes"][key]["limits"])
		rig.arm_limits(true)

func exit_scene() -> void:
	_apply_c3_anchor(true)
	_apply_bldA_anchor(true)
	if active_scene == "" and not _pending_exit:
		rig.fly_to(scenes_data["overview"]["cam"], 1000)
		ui.set_scene_active("overview")
		_setup_glass() # 回到总览：场景栏改实色底（池塘遮挡）
		return
	var key := active_scene
	active_scene = ""
	_pending_entry = ""
	panel.visible = false
	ui.layout_panels()
	ui.set_scene_active("overview")
	if key == "classroom" or key == "dist":
		# 两段退出：藏内景、恢复楼体 → 楼前 500ms → 总览 500ms
		_pending_exit = true
		_restore_scene_state()
		rig.fly_to(scenes_data["scenes"][key]["front"], 500, Callable(self, "_on_exit_phase2"))
	else:
		_restore_scene_state()
		rig.fly_to(scenes_data["overview"]["cam"], 1000)
	_setup_glass() # 回到总览：场景栏改实色底（池塘遮挡）

func _on_exit_phase2() -> void:
	_pending_exit = false
	rig.fly_to(scenes_data["overview"]["cam"], 500)

func _process(delta: float) -> void:
	_t += delta
	# 视口宽度变化超过 50px 时重算玻璃质量（窗口缩放/旋转时降质或恢复）
	var vw := get_viewport().get_visible_rect().size.x
	if absf(vw - _last_vp_w) > 50.0:
		_last_vp_w = vw
		_setup_glass()
	if playing:
		hour += delta * 0.5 # 2 秒推进 1 仿真小时
		if hour >= 24.0:
			hour = 24.0
			playing = false
			ui.set_playing(false)
	# 飞行被打断的收尾（原 Demo finishEntry / finishExit 的等价逻辑）
	if _pending_entry != "" and not rig.is_flying():
		var k := _pending_entry
		_pending_entry = ""
		_finish_entry(k)
	if _pending_exit and not rig.is_flying():
		_pending_exit = false
		rig.fly_to(scenes_data["overview"]["cam"], 500)
	var st: Dictionary = sim.state_at(hour)
	weather.update_frame(hour, delta)
	_update_visuals(st, delta)
	_update_clock(st)
	var now_ms := Time.get_ticks_msec()
	if active_scene != "" and now_ms - _panel_ms > 400:
		_panel_ms = now_ms
		_refresh_panel()

func _update_clock(st: Dictionary) -> void:
	var mode := "平时模式"
	if st["price"] >= float(bill_data["price"]["peak_yuan_per_kwh"]) - 0.001:
		mode = "高峰模式"
	elif st["price"] <= float(bill_data["price"]["valley_yuan_per_kwh"]) + 0.001:
		mode = "谷段模式"
	ui.set_clock(hour, mode + " · B 平急两用")

## SOC 三色口径（壳体变色与机架 SOC 条共用，同一 SOC 绝不两色）：
## 绿 >50%、黄 >28%、红 ≤28%。面板/图表里的“应急保留线 56%”是放电
## 保留概念，不是变色阈值——旧版条子拿保留线当变色阈值（≤0.576 红），
## 56% 时壳绿条红，正是 run 45219977015 截图里贴片全橙的根因之一。
func _soc_color(soc: float) -> Color:
	return Color("#1d9e63") if soc > 0.5 else (Color("#d9a514") if soc > 0.28 else Color("#c23b3b"))

func _update_visuals(st: Dictionary, delta: float) -> void:
	var soc: float = st["soc"]
	# 储能柜颜色随 SOC（绿/黄/红）
	if _shell_mat != null:
		var target_col := _soc_color(soc)
		var c := _shell_mat.albedo_color.lerp(target_col, 0.08)
		c.a = _shell_mat.albedo_color.a
		_shell_mat.albedo_color = c
	# 机架 SOC 条：填充条左锚定在底槽内伸缩（fill = SOC，左缘固定），颜色与
	# 壳体同口径；旧版是居中缩放 + 两色（SOC ≤ 保留线+0.02 就红），56% 时
	# 壳是绿、条是红，自相矛盾，且无底槽、无黄档，肉眼认不出是条。
	for i in range(campus.storage_rack_bars.size()):
		var bar: MeshInstance3D = campus.storage_rack_bars[i]
		var f := clampf(soc, 0.02, 1.0)
		var bm := bar.mesh as BoxMesh
		var full_w: float = bm.size.x if bm != null else 1.1
		bar.scale.x = f
		bar.position.x = campus.storage_rack_bar_cx[i] - full_w * (1.0 - f) / 2.0
		var m: StandardMaterial3D = bar.material_override
		var col := _soc_color(soc)
		m.albedo_color = col
		m.emission = col
	# 车辆 SOC 条
	for c in campus.car_fills:
		var fill: MeshInstance3D = c["fill"]
		var cur_soc := clampf(float(c["base_soc"]) + (hour - 8.0) * 0.014 - (0.10 if (bool(c["v2g"]) and float(st["ev"]) > 1.0) else 0.0), 0.08, 0.97)
		fill.scale.x = cur_soc
		fill.position.x = float(c["cx"]) - 3.4 * (1.0 - cur_soc) / 2.0
		var fm: StandardMaterial3D = fill.material_override
		var fcol := Color("#fb923c") if (bool(c["v2g"]) and float(st["ev"]) > 1.0) else (Color("#e2574c") if cur_soc < 0.3 else Color("#2fbf71"))
		fm.albedo_color = fcol
		fm.emission = fcol
	# 夜晚窗户亮灯（按日光强度）
	var rise: float = current_wx.get("rise", 6.0)
	var set_h: float = current_wx.get("set", 19.0)
	var daylight := clampf(sin(PI * (hour - rise) / maxf(0.1, set_h - rise)) * 1.7, 0.0, 1.0)
	campus.set_night_windows(1.0 - daylight)
	# 树冠微摆（减弱动效时停摆，P3-4）
	if not _reduced:
		var i := 0
		for t in campus.tree_canopies:
			t.rotation.z = sin(_t * 0.7 + i * 1.3) * 0.02
			i += 1
	# 储能标签实时 SOC
	if not _storage_label.is_empty():
		labels.set_dynamic_text(_storage_label, "储能柜 · SOC %d%%" % int(round(soc * 100.0)))
	# 各场景细节动画
	if cls_interior.visible and not cls_results.is_empty():
		var cur: Dictionary = cls_model.at(cls_results[cls_strategy], hour)
		cls_interior.set_ac(bool(cur["on"]), float(cur["T"]), _t)
	if sto_interior.visible:
		sto_interior.update_frame(float(st["batt"]), _t, delta)
	if pv_detail.visible:
		pv_detail.update_frame(float(st["pv"]), float(current_wx.get("pv_factor", 1.0)), _t)
	# V2G 弧线只在总览与充电区可见。弧线是充电区→储能站的跨场景能量流，
	# 旧版 chg_detail 常驻可见、每帧都更新，进储能/光伏/教室/配电房内景
	# 也照画——run 45232401156 的 02-storage.png 里斜穿柜体的那束橙色
	# 细线 + 黄色球就是它（charge_detail.gd：0.12m 细基线 + r0.22 橙色
	# #fb923c 流光点，从 (44,2,76) 贝塞尔到 (64,3,−30)，终点正在储能柜），
	# 不是阳光射线：阳光射线只在 pv_detail 里（储能场景 pv_detail.visible
	# = false，且射线是 2.2m 宽的半透明带，形态与 01-pv 里的四条宽带一致，
	# 与储能图里的细线完全不同）。总览保留弧线（_setup_interiors 注释的
	# 原设计意图：总览可见跨校园能量流），充电区保留，内景不再画。
	var _arc_scene := active_scene == "" or active_scene == "charge"
	chg_detail.visible = _arc_scene
	if _arc_scene:
		chg_detail.update_frame(float(st["ev"]), hour, _t, float(current_wx.get("pv_factor", 1.0)))
	if dist_interior.visible:
		dist_interior.set_load_rate(float(st["grid"]) / 3000.0)

func _refresh_panel() -> void:
	if active_scene == "":
		return
	var st: Dictionary = sim.state_at(hour)
	match active_scene:
		"pv":
			panel.set_live([
				["当前光伏出力", "%d kW" % int(round(float(st["pv"])))],
				["装机容量", "800 kWp（规划）"],
				["当前天气 / 光伏系数", "%s ×%.2f" % [str(current_wx.get("name", "")), float(current_wx.get("pv_factor", 1.0))]],
				["有效日照时段（情景设定）", "%s–%s · %.1f 小时" % [SimEngine.fmt_hour(float(current_wx.get("rise", 6.0))), SimEngine.fmt_hour(float(current_wx.get("set", 19.0))), float(current_wx.get("set", 19.0)) - float(current_wx.get("rise", 6.0))]],
				["今日累计发电", "%s kWh" % _fmt_num(float(sim.plan.get("pv_gen", 0.0)))],
				["逆变器状态", "DC 转 AC 转换中" if float(st["pv"]) > 2.0 else "待机（无光照）"],
			])
			panel.chart.set_day(sim.plan, hour, 0.556)
		"storage":
			var b: float = st["batt"]
			# 面板 SOC 条与壳体/3D 机架条共用 _soc_color（绿 >50%）：56% 为绿。
			# 旧版这里用保留线阈值（≤0.58 红），56% 时面板条红、壳与 3D 条绿，
			# 同一 SOC 两色——run 45226479162 的 02-storage.png 里 y339–348 那条
			# #dc2626 红条就是这根面板 ProgressBar，不是保留线条。
			# 保留线仍是独立元素：条下红字 Label + 图表里红色虚线，不另画条。
			panel.set_live([
				["储能 SOC", "%d%% · %s / 215 kWh" % [int(round(float(st["soc"]) * 100.0)), _fmt_num(float(st["soc"]) * 215.0)]],
				["应急保留线（红区）", "56% · 120 kWh"],
				["当前状态", ("放电 %d kW" % int(round(b))) if b > 1.0 else (("充电 %d kW" % int(round(-b))) if b < -1.0 else "待机")],
				["散热风扇", "高速运转" if absf(b) > 1.0 else "低速待机"],
				["日常放电", "条件触发：充电全部由午间光伏富余承担时才放电"],
			], [
				{"pct": float(st["soc"]) * 100.0, "color": "#" + _soc_color(float(st["soc"])).to_html(false), "resv_pct": 55.6, "resv_kwh": "120"},
			])
			panel.chart.set_day(sim.plan, hour, 0.556)
		"classroom":
			var cur: Dictionary = cls_model.at(cls_results[cls_strategy], hour)
			var T: float = cur["T"]
			var band := "偏冷（过冷不舒适）" if T < 24.0 else ("偏热（不舒适）" if T > 28.0 else "舒适带内")
			var res: Dictionary = cls_results[cls_strategy]
			panel.set_live([
				["当前室温（模型一）", "%.1f ℃" % T],
				["室外温度", "%.1f ℃ · %s" % [cls_model.tout(hour), str(current_wx.get("name", ""))]],
				["空调状态", "2 台运行制冷中" if bool(cur["on"]) else "停机（靠热惯性维持）"],
				["舒适度判定", "%s（舒适带 24–28 ℃）" % band],
				["本策略今日空调电量", "%.1f kWh · %.1f 元" % [float(res["kwh"]), float(res["cost"])]],
			])
			panel.chart.set_temp(cls_results, cls_strategy, hour)
		"charge":
			var rows := [
				["V2G 当前放电", "%d kW" % int(round(float(st["ev"])))],
				["教职工参与率", "30%"],
				["在场车辆", "3 辆（带 SOC 条）"],
			]
			var bars: Array = []
			var ci := 0
			for c in campus.car_fills:
				var cur_soc := clampf(float(c["base_soc"]) + (hour - 8.0) * 0.014 - (0.10 if (bool(c["v2g"]) and float(st["ev"]) > 1.0) else 0.0), 0.08, 0.97)
				rows.append(["车辆 %d%s" % [ci + 1, "（V2G 参与）" if bool(c["v2g"]) else ""], "%d%%" % int(round(cur_soc * 100.0))])
				bars.append({"pct": cur_soc * 100.0, "color": "#ea580c" if (bool(c["v2g"]) and float(st["ev"]) > 1.0) else ("#dc2626" if cur_soc < 0.3 else "#059669")})
				ci += 1
			rows.append(["离校要求", "参与车辆离校电量须达 80%"])
			panel.set_live(rows, bars)
			panel.chart.set_day(sim.plan, hour, 0.556)
		"dist":
			var rate := 100.0 * float(st["grid"]) / 3000.0
			panel.set_live([
				["母线购电功率", "%d kW" % int(round(float(st["grid"])))],
				["变压器负载率", "%d%%（总容量实测 3000 kVA，负载率按 kW/kVA 近似）" % int(round(rate))],
				["储能 SOC", "%d%% · 保留线 56%%" % int(round(float(st["soc"]) * 100.0))],
				["运行模式", "B 平急两用 · %s" % ("高峰模式" if float(st["price"]) > 0.55 else "平时模式")],
			], [
				{"pct": rate, "color": "#dc2626" if rate > 90.0 else "#0284c7"},
			])
			panel.chart.set_day(sim.plan, hour, 0.556)

func _fmt_num(n: float) -> String:
	# 千分位格式化（如 3,399）
	var neg := n < 0.0
	var s := str(int(round(absf(n))))
	var out := ""
	while s.length() > 3:
		out = "," + s.right(3) + out
		s = s.left(s.length() - 3)
	out = s + out
	return ("-" + out) if neg else out
