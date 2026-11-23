class_name ScenePanel
extends PanelContainer
## 场景面板：只留图表与实时数据行，不写介绍文字段落（用户要求）。
## （UITokens 用 preload：见 ui_controller.gd 注释。）

const UITokens = preload("res://scripts/ui_tokens.gd")
## 内容：标题、附加控件（教室策略下拉 / 储能外壳开关）、实时数据行、
## SOC/负载条、曲线图、返回按钮。窄屏默认收起只留标题与返回。

signal strategy_changed(value: String)
signal shell_toggled(open: bool)
signal back_pressed
signal minimize_toggled(minimized: bool)

## 去 AI 味：面板只在偶尔出现的转场做一次进入动效（180ms 强 ease-out，
## scale 0.95 + opacity，origin 在右缘触发点）；内容行不 stagger（一个容器一次进入，
## 面板自己动，内容已经在里面 —— choreograph）。中途切场景时旧 tween 杀掉、从当前值重定向。
## 按压反馈改用临界阻尼弹簧（PressSpringSet，ω≈31.6，无超调），见 spring.gd。
var reduced_motion := false
var font: Font # 中文字体：main.gd 启动时赋；build()/set_live() 新建的控件创建时直接挂上
var _enter_tween: Tween
var _enter_token := 0
var _springs := PressSpringSet.new()

var title_label: Label
var extra_box: HBoxContainer
var live_box: VBoxContainer
var chart: Charts
var min_btn: Button
var _minimized := false
var _cls_sel: OptionButton
var _shell_btn: Button # 储能外壳开关按钮：进场自动开壳时 main.gd 靠它同步文案

func _ready() -> void:
	custom_minimum_size = Vector2(330, 0)
	title_label = $VBox/SPTitleRow/SPTitle
	extra_box = $VBox/SPExtra
	live_box = $VBox/SPLive
	chart = $VBox/SPChart
	min_btn = $VBox/SPTitleRow/SPMinBtn
	# 面板按钮与顶栏按钮共用 UITokens 一套 token（P2-4），不再用默认主题样式。
	UITokens.style_solid_button(min_btn)
	UITokens.style_solid_button($VBox/SPBack)
	min_btn.pressed.connect(_on_min_pressed)
	$VBox/SPBack.pressed.connect(func() -> void: back_pressed.emit())
	_springs.attach(min_btn)
	_springs.attach($VBox/SPBack)
	# 附加控件里的按钮（储能外壳开关）也在 build() 里挂弹簧，见 build() 末尾

func _process(delta: float) -> void:
	_springs.tick(delta)

func _play_enter() -> void:
	_enter_token += 1
	var token := _enter_token
	if _enter_tween != null and _enter_tween.is_valid():
		_enter_tween.kill()
	# 等一帧拿到布局后的尺寸，origin 定在右缘（面板从右缘生长，不从中心放大）
	await get_tree().process_frame
	await get_tree().process_frame
	if token != _enter_token or not is_inside_tree():
		return
	pivot_offset = Vector2(size.x, 0)
	if reduced_motion:
		modulate.a = 0.0
		scale = Vector2.ONE
		_enter_tween = create_tween()
		_enter_tween.tween_property(self, "modulate:a", 1.0, 0.20)
		return
	scale = Vector2(0.95, 0.95)
	modulate.a = 0.0
	_enter_tween = create_tween()
	_enter_tween.set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	_enter_tween.tween_property(self, "scale", Vector2.ONE, 0.18)
	_enter_tween.parallel().tween_property(self, "modulate:a", 1.0, 0.18)

func build(title: String, extra_kind: String, shell_open: bool) -> void:
	title_label.text = title
	_play_enter()
	for c in extra_box.get_children():
		c.queue_free()
	_cls_sel = null
	_shell_btn = null
	if extra_kind == "classroom":
		var lab := Label.new()
		lab.text = "演示策略"
		if font != null:
			lab.add_theme_font_override("font", font)
		lab.add_theme_color_override("font_color", Color("#1e293b"))
		lab.add_theme_font_size_override("font_size", 16)
		extra_box.add_child(lab)
		var sel := OptionButton.new()
		if font != null:
			sel.add_theme_font_override("font", font)
		UITokens.style_option_button(sel)
		sel.custom_minimum_size = Vector2(0, 44)
		sel.add_item("预冷 + 峰段间歇", 0)
		sel.add_item("恒温 26 ℃", 1)
		sel.add_item("拉闸无节制（现状）", 2)
		sel.selected = 0
		sel.item_selected.connect(func(idx: int) -> void:
			strategy_changed.emit(["opt", "const", "gate"][idx])
		)
		extra_box.add_child(sel)
		_cls_sel = sel
	elif extra_kind == "storage":
		var btn := Button.new()
		btn.text = "外壳半透明：" + ("开" if shell_open else "关")
		if font != null:
			btn.add_theme_font_override("font", font)
		UITokens.style_solid_button(btn)
		btn.toggle_mode = true
		btn.button_pressed = shell_open
		btn.toggled.connect(func(on: bool) -> void:
			btn.text = "外壳半透明：" + ("开" if on else "关")
			shell_toggled.emit(on)
		)
		extra_box.add_child(btn)
		_shell_btn = btn
		_springs.attach(btn)
		btn.custom_minimum_size = Vector2(0, 44)

## 进场自动开壳时同步开关文案（build() 是进场前按旧 shell_open 建的，
## 不调这里文案会一直滞后）。用 set_pressed_no_signal，不再触发 toggled，
## 避免与 main.gd 的 shell_toggled 处理重复调用 set_shell_translucent。
func set_shell_open(open: bool) -> void:
	if _shell_btn == null:
		return
	_shell_btn.set_pressed_no_signal(open)
	_shell_btn.text = "外壳半透明：" + ("开" if open else "关")

func set_strategy_sel(value: String) -> void:
	if _cls_sel != null:
		_cls_sel.selected = ["opt", "const", "gate"].find(value)

func set_live(rows: Array, bars: Array = []) -> void:
	for c in live_box.get_children():
		c.queue_free()
	for r in rows:
		var h := HBoxContainer.new()
		var k := Label.new()
		k.text = String(r[0])
		if font != null:
			k.add_theme_font_override("font", font)
		k.add_theme_color_override("font_color", Color("#475569"))
		k.add_theme_font_size_override("font_size", 16)
		var v := Label.new()
		v.text = String(r[1])
		if font != null:
			v.add_theme_font_override("font", font)
		# P0：数值列必须显式深色——Godot 默认 Label 是白色，白底面板上完全不可读
		v.add_theme_color_override("font_color", Color("#1e293b"))
		v.add_theme_font_size_override("font_size", 16)
		v.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		# 面板定宽 360px：长数值（如“条件触发：充电全部由午间光伏富余承担时才放电”）
		# 不换行会把面板撑到 511px、右缘出屏（Actions 截图实测）。允许换行，宁可多一行。
		v.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		h.add_child(k)
		h.add_child(v)
		live_box.add_child(h)
	for b in bars:
		var bar := ProgressBar.new()
		bar.min_value = 0
		bar.max_value = 100
		bar.value = float(b["pct"])
		bar.show_percentage = false
		bar.custom_minimum_size = Vector2(0, 10)
		var sb := StyleBoxFlat.new()
		sb.bg_color = Color(b["color"])
		sb.corner_radius_top_left = 5
		sb.corner_radius_top_right = 5
		sb.corner_radius_bottom_left = 5
		sb.corner_radius_bottom_right = 5
		bar.add_theme_stylebox_override("fill", sb)
		var bg := StyleBoxFlat.new()
		bg.bg_color = Color("#e2e8f0")
		bg.corner_radius_top_left = 5
		bg.corner_radius_top_right = 5
		bg.corner_radius_bottom_left = 5
		bg.corner_radius_bottom_right = 5
		bar.add_theme_stylebox_override("background", bg)
		live_box.add_child(bar)
		if b.has("resv_pct"):
			var resv := Label.new()
			resv.text = "应急保留线 %.0f%% · %s kWh" % [float(b["resv_pct"]), str(b.get("resv_kwh", ""))]
			if font != null:
				resv.add_theme_font_override("font", font)
			resv.add_theme_color_override("font_color", Color("#dc2626"))
			resv.add_theme_font_size_override("font_size", 16)
			resv.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			live_box.add_child(resv)

func set_minimized(m: bool) -> void:
	_minimized = m
	live_box.visible = not m
	chart.visible = not m
	extra_box.visible = not m
	min_btn.text = "展开详情" if m else "收起详情"
	minimize_toggled.emit(m)


## 窄屏（P2-1）：面板满宽（左右各留 12px），图表取消 320px 强制最小宽，
## 跟着面板宽走；最小宽 330px → 280px。
func apply_narrow_layout(w: float) -> void:
	if w < 672.0:
		offset_left = -(w - 24.0)
		custom_minimum_size = Vector2(280, 0)
		chart.custom_minimum_size = Vector2(0, 200)
	else:
		offset_left = -372.0
		custom_minimum_size = Vector2(330, 0)
		# 图表高 180（原 200）：长行换行后内容高 +20px，储能面板会长到 585、
		# 底边 645 压到场景栏顶（636）上；降 20px 留出余量。
		chart.custom_minimum_size = Vector2(320, 180)

func _on_min_pressed() -> void:
	set_minimized(not _minimized)
