class_name GlassSurface
extends ColorRect
## 液态玻璃表面：ColorRect + shaders/liquid_glass.gdshader。
## 结构要求：作为独立 sibling 放在内容节点之下（不做父容器），因为 Godot 的
## CanvasItem material 会被子节点继承——玻璃做父容器会把模糊/折射也糊到文字上。
## 降级：glass_enabled=false 时隐藏自己，显示同级的 fallback 实色 Panel
## （由 main.gd 在 ?glass=0 或窄屏低端时切换；fallback 节点名约定为同 parent 下的
## "<自身名>Fallback"，如 BarGlassFallback）。

const SHADER := preload("res://shaders/liquid_glass.gdshader")

@export var corner_radius := 28.0
@export var tint_alpha := 0.42

var _mat: ShaderMaterial

func _ready() -> void:
	_mat = ShaderMaterial.new()
	_mat.shader = SHADER
	material = _mat
	color = Color.WHITE # shader 不用 COLOR 输入，只借 ColorRect 的绘制矩形
	mouse_filter = MOUSE_FILTER_IGNORE
	resized.connect(_apply_uniforms)
	_apply_uniforms()

func _apply_uniforms() -> void:
	if _mat == null:
		return
	_mat.set_shader_parameter("rect_size", size)
	_mat.set_shader_parameter("corner_radius", corner_radius)
	_mat.set_shader_parameter("tint_alpha", tint_alpha)

## low=true：5-tap + 4px 模糊（窄屏/低端）；false：9-tap + 6px（默认）
func set_quality(low: bool) -> void:
	if _mat == null:
		return
	_mat.set_shader_parameter("tap_mode", 0 if low else 1)
	_mat.set_shader_parameter("blur_radius", 4.0 if low else 6.0)

func set_glass_enabled(on: bool) -> void:
	visible = on
	var fb := get_parent().get_node_or_null(String(name) + "Fallback")
	if fb != null:
		fb.visible = not on
