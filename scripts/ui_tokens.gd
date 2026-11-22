class_name UITokens
## UI 样式 token 单一来源（P2-4：此前玻璃按钮与默认主题按钮两套样式并存）。
## 配色取值见 res://data/colors.csv 第 1 行 SaaS（背景 #F8FAFC、前景 #1e293b、
## 次前景 #475569、描边 #e2e8f0、危险 #dc2626、焦点环 #2563eb）；激活绿 #0f766e /
## #047857 是本 Demo 沿用至今的语义色（白底上白字约 5.5:1、绿字约 5:1）。
## 两类按钮共用同一套 token：玻璃按钮（场景栏/天气胶囊，透明底露玻璃）与
## 实色按钮（顶栏操作、面板按钮，白底 + 描边）。键盘焦点环两类都有（P3-6）。

const FONT_DARK := Color("#1e293b")
const FONT_TITLE := Color("#0f172a")
const FONT_MID := Color("#475569")
const ACCENT := Color("#0f766e")
const ACCENT_TEXT := Color("#047857")
const BORDER := Color("#e2e8f0")
const PANEL_BG := Color(1, 1, 1, 0.93)
const DANGER := Color("#dc2626")
const FOCUS_RING := Color("#2563eb")
const BTN_FONT_SIZE := 16
const BTN_HEIGHT := 44
const RADIUS_SOLID := 10
const RADIUS_GLASS := 22


static func _flat(bg: Color, radius: int, border: Color = Color(0, 0, 0, 0), border_w: int = 0) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = bg
	sb.corner_radius_top_left = radius
	sb.corner_radius_top_right = radius
	sb.corner_radius_bottom_left = radius
	sb.corner_radius_bottom_right = radius
	if border_w > 0:
		sb.border_color = border
		sb.set_border_width_all(border_w)
	return sb


static func _focus_ring(radius: int) -> StyleBoxFlat:
	# 键盘焦点必须可见：透明底 + 2px 蓝色环（colors.csv Ring #2563eb）。
	return _flat(Color(0, 0, 0, 0), radius, FOCUS_RING, 2)


## 玻璃上的按钮：平时透明（直接露玻璃），hover 白 0.25，激活态实色深绿胶囊 + 白字。
## （激活态不用第二层玻璃，避免玻璃叠玻璃；深绿 #0f766e 上白字对比度约 5.5:1。）
static func style_glass_button(b: Button) -> void:
	b.add_theme_stylebox_override("normal", StyleBoxEmpty.new())
	b.add_theme_stylebox_override("hover", _flat(Color(1, 1, 1, 0.25), RADIUS_GLASS))
	b.add_theme_stylebox_override("pressed", _flat(ACCENT, RADIUS_GLASS))
	b.add_theme_stylebox_override("focus", _focus_ring(RADIUS_GLASS))
	b.add_theme_color_override("font_color", FONT_DARK)
	b.add_theme_color_override("font_hover_color", FONT_TITLE)
	b.add_theme_color_override("font_pressed_color", Color.WHITE)
	b.add_theme_font_size_override("font_size", BTN_FONT_SIZE)


## 实色按钮：白底 + 细描边，hover 浅灰，激活态与玻璃按钮同款深绿 + 白字。
static func style_solid_button(b: Button) -> void:
	b.add_theme_stylebox_override("normal", _flat(Color.WHITE, RADIUS_SOLID, BORDER, 1))
	b.add_theme_stylebox_override("hover", _flat(Color("#f1f5f9"), RADIUS_SOLID, BORDER, 1))
	b.add_theme_stylebox_override("pressed", _flat(ACCENT, RADIUS_SOLID))
	b.add_theme_stylebox_override("disabled", _flat(Color("#f1f5f9"), RADIUS_SOLID, BORDER, 1))
	b.add_theme_stylebox_override("focus", _focus_ring(RADIUS_SOLID))
	b.add_theme_color_override("font_color", FONT_DARK)
	b.add_theme_color_override("font_hover_color", FONT_TITLE)
	b.add_theme_color_override("font_pressed_color", Color.WHITE)
	b.add_theme_color_override("font_disabled_color", FONT_MID)
	b.add_theme_font_size_override("font_size", BTN_FONT_SIZE)


## 下拉框：与实色按钮同款（白底 + 描边 + 深色字），弹层字体由主主题兜底。
static func style_option_button(sel: OptionButton) -> void:
	sel.add_theme_stylebox_override("normal", _flat(Color.WHITE, RADIUS_SOLID, BORDER, 1))
	sel.add_theme_stylebox_override("hover", _flat(Color("#f1f5f9"), RADIUS_SOLID, BORDER, 1))
	sel.add_theme_stylebox_override("pressed", _flat(Color.WHITE, RADIUS_SOLID, BORDER, 1))
	sel.add_theme_stylebox_override("focus", _focus_ring(RADIUS_SOLID))
	sel.add_theme_color_override("font_color", FONT_DARK)
	sel.add_theme_font_size_override("font_size", BTN_FONT_SIZE)
