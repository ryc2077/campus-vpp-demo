class_name UIController
extends CanvasLayer
## 顶栏 / 场景栏 / 天气胶囊 / 时间控制 / A-B-C 对照面板。
## 只发信号、不算数；仿真与场景切换由 main.gd 驱动。
## （UITokens 用 preload 而不用全局 class_name：新文件进不了本地陈旧的
## .godot 类缓存，headless 下会报未声明；preload 在本地与 Actions 都稳。）

const UITokens = preload("res://scripts/ui_tokens.gd")
##
## UI/UX Pro Max（Operate 仪表盘，拨盘 variance 中低 / motion 中低 / density 高）：
##  - 触摸目标 ≥44×44px、间距 8px（tscn 里已定死）；正文 16px、行高 1.5；
##    正文与白底对比度 ≥4.5:1（#1e293b/#475569 系，见 res://data/colors.csv 第 1 行 SaaS）。
##  - 图表不只靠颜色：见 charts.gd（虚线/点线 + 图例色块 + 末端直标值）。
##  - 退出比进入快：A/B/C 进入 180ms、退出 120ms（约 67%）；动效只动 transform/opacity。
##  - 无 emoji/字形图标（▶ ⏸ ▴ ▾ ← 全部改文字动词）；无卡中卡；无紫蓝渐变。
##  - 玻璃只在两处浮层控件（场景栏、天气胶囊），文字面板保持实色可读。

signal scene_selected(key: String)
signal weather_selected(key: String)
signal play_toggled(playing: bool)
signal time_changed(hour: float)
signal abc_toggle_pressed

var strategies: Dictionary = {}
var weather_order: Array = []
var weather_names: Dictionary = {}
var font: Font # 中文字体：main.gd 启动时赋；_mk_label 新建的 ABC 表格行创建时直接挂上
var playing := false
var reduced_motion := false
var _wx_buttons: Dictionary = {}
var _scene_buttons: Dictionary = {}
var _springs := PressSpringSet.new()
var _abc_font_size := 16
var _narrow_w := -1.0
var _scene_panel: PanelContainer
var _abc_tween: Tween
var _abc_token := 0
var _abc_exit_token := 0

@onready var clock_label: Label = %ClockLabel
@onready var mode_chip: Label = %ModeChip
@onready var time_slider: HSlider = %TimeSlider
@onready var time_label: Label = %TimeLabel
@onready var play_button: Button = %PlayButton
@onready var abc_panel: PanelContainer = %ABCPanel
@onready var abc_grid: GridContainer = %ABCGrid
@onready var abc_note: Label = %ABCNote

func _ready() -> void:
	_scene_panel = get_node_or_null("ScenePanel") as PanelContainer
	# 实色按钮（顶栏操作 / 面板关闭）与玻璃按钮共用 UITokens 一套 token（P2-4）；
	# 此前这里是 Godot 默认主题按钮，与玻璃按钮两套样式并存。
	UITokens.style_solid_button(play_button)
	UITokens.style_solid_button(%ABCToggle)
	UITokens.style_solid_button(%ABCClose)
	get_viewport().size_changed.connect(_on_vp_resized)
	call_deferred("_on_vp_resized")
	time_slider.value_changed.connect(func(v: float) -> void:
		time_changed.emit(v * 0.25)
	)
	play_button.pressed.connect(func() -> void:
		playing = not playing
		play_button.text = "暂停仿真" if playing else "开始仿真"
		play_toggled.emit(playing)
	)
	%ABCToggle.pressed.connect(func() -> void:
		if abc_panel.visible:
			_close_abc()
		else:
			abc_panel.visible = true
			_play_abc_enter()
		abc_toggle_pressed.emit()
		layout_panels()
	)
	%ABCClose.pressed.connect(func() -> void: _close_abc())
	for key in ["sunny", "cloudy", "overcast", "rain", "storm"]:
		var b: Button = get_node("%Wx" + key.capitalize())
		_wx_buttons[key] = b
		_style_glass_button(b)
		_springs.attach(b)
		b.pressed.connect(func() -> void: weather_selected.emit(key))
	for key in ["overview", "pv", "storage", "classroom", "charge", "dist"]:
		var b: Button = get_node("%Btn" + key.capitalize())
		_scene_buttons[key] = b
		_style_glass_button(b)
		_springs.attach(b)
		b.pressed.connect(func() -> void: scene_selected.emit(key))
	_springs.attach(play_button)
	_springs.attach(%ABCToggle)
	_springs.attach(%ABCClose)

func _process(delta: float) -> void:
	_springs.tick(delta)

## 样式统一走 UITokens（P2-4）：玻璃按钮与实色按钮同一套 token。
func _style_glass_button(b: Button) -> void:
	UITokens.style_glass_button(b)

## 窄屏分支（P2-1）：按视口宽分三档重构，全部只改尺寸/显隐，不动布局结构。
## 975：时间滑杆缩短；672：模式芯片隐藏、标题 14px、场景栏按钮均分、ABC/场景面板满宽；
## 560：时间滑杆与时间标签隐藏、天气标签隐藏、ABC 表格字 14px。
func _on_vp_resized() -> void:
	_apply_narrow_layout(get_viewport().get_visible_rect().size.x)


func _apply_narrow_layout(w: float) -> void:
	var title := get_node("TopBar/HBox/TitleLabel") as Label
	var slider := %TimeSlider as HSlider
	if w < 560.0:
		mode_chip.visible = false
		slider.visible = false
		time_label.visible = false
		title.add_theme_font_size_override("font_size", 14)
	elif w < 672.0:
		mode_chip.visible = false
		slider.visible = true
		slider.custom_minimum_size = Vector2(80, 44)
		time_label.visible = true
		title.add_theme_font_size_override("font_size", 14)
	elif w < 975.0:
		mode_chip.visible = true
		slider.visible = true
		slider.custom_minimum_size = Vector2(100, 44)
		time_label.visible = true
		title.add_theme_font_size_override("font_size", 16)
	else:
		mode_chip.visible = true
		slider.visible = true
		slider.custom_minimum_size = Vector2(150, 44)
		time_label.visible = true
		title.add_theme_font_size_override("font_size", 16)
	# 场景栏：672 以下按钮取消固定宽、均分整栏；恢复时还原因子。
	# Round 2：栏宽 672 -> 720（±360，与 main.tscn 一致），内容实测需 660px，
	# 旧栏内宽 648 < 660 已溢出 12px；按钮 96/116 -> 92/112、间距 8 -> 6，
	# 内容合计 626px，内宽 696px，留 70px 裕量，不再顶出右缘。
	var scene_bar := get_node("SceneBar") as Control
	var scene_hbox := get_node("SceneBar/HBox") as HBoxContainer
	var narrow_scene := w < 672.0
	var half_w := maxf(0.0, w * 0.5 - 12.0)
	scene_bar.offset_left = -half_w if narrow_scene else -360.0
	scene_bar.offset_right = half_w if narrow_scene else 360.0
	scene_hbox.add_theme_constant_override("separation", 4 if narrow_scene else 6)
	for k in _scene_buttons:
		var b: Button = _scene_buttons[k]
		if narrow_scene:
			b.custom_minimum_size = Vector2(0, 44)
			b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			b.add_theme_font_size_override("font_size", 13)
		else:
			b.custom_minimum_size = Vector2(112 if k == "classroom" else 92, 44)
			b.size_flags_horizontal = Control.SIZE_FILL
			b.add_theme_font_size_override("font_size", 16)
	# 天气胶囊：560 以下藏“天气”标签、按钮缩到 40px，胶囊随之收窄。
	var wx_hbox := get_node("WxPill/HBox") as HBoxContainer
	var wx_label := get_node("WxPill/HBox/WxLabel") as Label
	var wx_pill := get_node("WxPill") as Control
	var narrow_wx := w < 560.0
	wx_label.visible = not narrow_wx
	wx_hbox.add_theme_constant_override("separation", 4 if narrow_wx else 8)
	for k in _wx_buttons:
		var b: Button = _wx_buttons[k]
		b.custom_minimum_size = Vector2(40 if narrow_wx else 48, 44)
	wx_pill.offset_left = -308.0 if narrow_wx else -364.0
	# ABC 面板：672 以下满宽（左右各留 12px）；560 以下表格字 14px（重建一次）。
	var new_size := 14 if w < 560.0 else 16
	abc_panel.offset_left = -(w - 24.0) if w < 672.0 else -560.0
	if new_size != _abc_font_size:
		_abc_font_size = new_size
		if not strategies.is_empty():
			_build_abc()
	# 场景面板：窄屏满宽 + 图表不强制 320px（scene_panel 内部处理）。
	if _scene_panel != null and _scene_panel.has_method("apply_narrow_layout"):
		_scene_panel.call("apply_narrow_layout", w)
	layout_panels()
	_narrow_w = w


## ABC 面板与场景面板同在右侧重叠（P2 旧问题）：两者同时可见时，
## 场景面板下移到 ABC 面板下方（顶 = ABC 底 + 12），底贴到场景栏上方；
## 只剩一个可见时恢复原位（顶 60、底 620 固定高）。
func layout_panels() -> void:
	if _scene_panel == null:
		return
	var both := abc_panel.visible and _scene_panel.visible
	if both:
		_scene_panel.offset_top = abc_panel.offset_bottom + 12.0
		_scene_panel.anchor_bottom = 1.0
		_scene_panel.offset_bottom = -84.0
	else:
		_scene_panel.offset_top = 60.0
		_scene_panel.anchor_bottom = 0.0
		_scene_panel.offset_bottom = 620.0

## A/B/C 面板：偶尔打开的对照面板，一次进入（180ms 强 ease-out，
## scale 0.95 + opacity，origin 右缘）；内容表格不 stagger。
func _play_abc_enter() -> void:
	_abc_token += 1
	_abc_exit_token += 1
	var token := _abc_token
	if _abc_tween != null and _abc_tween.is_valid():
		_abc_tween.kill()
	await get_tree().process_frame
	await get_tree().process_frame
	if token != _abc_token or not is_inside_tree():
		return
	abc_panel.pivot_offset = Vector2(abc_panel.size.x, 0)
	if reduced_motion:
		abc_panel.modulate.a = 0.0
		abc_panel.scale = Vector2.ONE
		_abc_tween = abc_panel.create_tween()
		_abc_tween.tween_property(abc_panel, "modulate:a", 1.0, 0.20)
		return
	abc_panel.scale = Vector2(0.95, 0.95)
	abc_panel.modulate.a = 0.0
	_abc_tween = abc_panel.create_tween()
	_abc_tween.set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	_abc_tween.tween_property(abc_panel, "scale", Vector2.ONE, 0.18)
	_abc_tween.parallel().tween_property(abc_panel, "modulate:a", 1.0, 0.18)

## 退出比进入快：120ms（进入的 67%），只淡出不缩放；中途再打开会杀掉退出 tween。
func _close_abc() -> void:
	if not abc_panel.visible:
		return
	_abc_exit_token += 1
	_abc_token += 1
	var token := _abc_exit_token
	if _abc_tween != null and _abc_tween.is_valid():
		_abc_tween.kill()
	if reduced_motion:
		abc_panel.visible = false
		layout_panels()
		return
	_abc_tween = abc_panel.create_tween()
	_abc_tween.set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	_abc_tween.tween_property(abc_panel, "modulate:a", 0.0, 0.12)
	_abc_tween.tween_callback(func() -> void:
		if token == _abc_exit_token:
			abc_panel.visible = false
			abc_panel.modulate.a = 1.0
			layout_panels()
	)

func setup(strat: Dictionary, wx_order: Array, wx_presets: Dictionary) -> void:
	strategies = strat
	weather_order = wx_order
	for k in wx_presets:
		weather_names[k] = wx_presets[k]["name"]
	_build_abc()

func set_weather_active(key: String) -> void:
	for k in _wx_buttons:
		var b: Button = _wx_buttons[k]
		b.button_pressed = (k == key)

func set_scene_active(key: String) -> void:
	for k in _scene_buttons:
		var b: Button = _scene_buttons[k]
		b.button_pressed = (k == key)

func set_clock(hour: float, mode_text: String) -> void:
	clock_label.text = SimEngine.fmt_hour(hour)
	mode_chip.text = mode_text
	time_label.text = SimEngine.fmt_hour(hour)
	if absf(time_slider.value - hour * 4.0) > 0.6:
		time_slider.value = hour * 4.0

func set_playing(p: bool) -> void:
	playing = p
	play_button.text = "暂停仿真" if p else "开始仿真"

## 正文 16px（UI/UX Pro Max 硬性线）；密集数据表也不例外——ABC 面板已加宽到 548px 容纳。
## bold 只表示“本行是重点行”，不改颜色：之前 bold 分支无条件把颜色盖成 #0f172a，
## 导致 B 行的绿色名与保供列的语义色（绿/红）全是死代码，且 A 行因缺 backup_ok 字段被误标红。
## 语义色由调用方传入的 color 决定，bold 不再覆盖。
func _mk_label(text: String, bold: bool = false, color: Color = Color("#1e293b"), size: int = 16) -> Label:
	var l := Label.new()
	l.text = text
	if font != null:
		l.add_theme_font_override("font", font)
	l.add_theme_color_override("font_color", color)
	l.add_theme_font_size_override("font_size", size)
	return l

func _build_abc() -> void:
	# 立即释放旧格（不用 queue_free）：窄屏切换会同帧重建并读回字号，延迟释放会读到旧标签。
	for c in abc_grid.get_children():
		c.free()
	var s: Dictionary = strategies["strategies"]
	var fs := _abc_font_size
	var headers := ["策略", "外购\nkWh/日", "电费\n元/日", "碳\nkg/日", "峰值\nkW", "自用率", "保供"]
	for h in headers:
		abc_grid.add_child(_mk_label(h, true, Color("#0f172a"), fs))
	for key in ["A", "B", "C"]:
		var st: Dictionary = s[key]
		# B 行名用深绿 #047857（白底约 5:1；之前 #059669 仅 3.77:1 未达 AA）
		var name_col := Color("#047857") if key == "B" else Color("#1e293b")
		abc_grid.add_child(_mk_label(String(st["name"]), key == "B", name_col, fs))
		abc_grid.add_child(_mk_label(str(int(st["grid_kwh_day"])), key == "B", Color("#1e293b"), fs))
		abc_grid.add_child(_mk_label(str(int(st["cost_yuan_day"])), key == "B", Color("#1e293b"), fs))
		abc_grid.add_child(_mk_label(str(int(st["co2_kg_day"])), key == "B", Color("#1e293b"), fs))
		abc_grid.add_child(_mk_label(str(int(st["peak_kw"])), key == "B", Color("#1e293b"), fs))
		abc_grid.add_child(_mk_label("%.1f%%" % float(st["self_use_pct"]), key == "B", Color("#1e293b"), fs))
		# 保供是否达标按保留线 4h 判定（A 7.9h、B 4.4h 达标，C 1.6h 不达标）；
		# 之前按 backup_ok 字段判定，A 缺该字段默认 false 被误标红。
		var ok := float(st["backup_h"]) >= 4.0
		var bk := "%.1fh 达标" % float(st["backup_h"]) if ok else "%.1fh 不达标" % float(st["backup_h"])
		abc_grid.add_child(_mk_label(bk, key == "B", Color("#047857") if ok else Color("#dc2626"), fs))
	var d: Dictionary = strategies["delta_B_vs_A"]
	abc_note.text = "B 相对 A：日减外购 %d kWh、日省 %d 元、日减碳 %d kg、削峰 %d kW。按 250 教学日：年省电约 22,000 kWh、年减碳约 13 吨。B 保供 4.4h 达标，C 仅 1.6h 不达标。" % [
		-int(d["grid_kwh_day"]), -int(d["cost_yuan_day"]), -int(d["co2_kg_day"]), -int(d["peak_kw"])
	]
