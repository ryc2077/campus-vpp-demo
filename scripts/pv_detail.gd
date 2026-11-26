class_name PvDetail
extends Node3D
## 光伏屋顶细节组：置于一号教学楼屋顶，入口光伏场景时显示。
## 含逆变器箱、阳光光尘粒子（GPUParticles3D，随出力与天气联动）。
## （GlbLoader 用 preload：见 campus_builder.gd 注释。）
const GlbLoader = preload("res://scripts/glb_loader.gd")

# 阳光光尘：两层 GPUParticles3D（主层 + 稀疏大颗粒层，做疏密层次）。
# 旧的 ray_planes（半透明斜板）与 flow_dots（黄色发光小球）已全部移除：
# 斜板像贴上去的纸片、小球像散落的圆点，光都太假，改由粒子光尘替代。
var sun_dust: GPUParticles3D
var sun_dust_far: GPUParticles3D
var _dust_mat: StandardMaterial3D

func _ready() -> void:
	_build()

func _mat(c: Color, rough: float = 0.5, metal: float = 0.3) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	m.roughness = rough
	m.metallic = metal
	return m

func _box(pos: Vector3, size: Vector3, mat: Material) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = size
	mi.mesh = bm
	mi.position = pos
	mi.material_override = mat
	add_child(mi)
	return mi

# 程序化粒子贴图：64×64 径向渐变柔边圆点（中心实、边缘淡出），不依赖外部素材。
func _make_dust_texture() -> Texture2D:
	var img := Image.create(64, 64, false, Image.FORMAT_RGBA8)
	var c := Vector2(32.0, 32.0)
	for y in 64:
		for x in 64:
			var d := Vector2(float(x) + 0.5, float(y) + 0.5).distance_to(c) / 32.0
			var a := clampf(1.0 - d, 0.0, 1.0)
			a = a * a * (3.0 - 2.0 * a) # smoothstep，柔边无硬环
			img.set_pixel(x, y, Color(1, 1, 1, a))
	return ImageTexture.create_from_image(img)

# 生灭淡入淡出 ramp：0 处透明 → 0.22 渐亮 → 0.65 维持 → 1.0 淡出。
# 颜色暖金 #ffd98a → #fff3c4；peak_alpha 区分两层亮度（远层更淡）。
func _make_dust_ramp(peak_alpha: float) -> GradientTexture1D:
	var grad := Gradient.new()
	grad.offsets = PackedFloat32Array([0.0, 0.22, 0.65, 1.0])
	grad.colors = PackedColorArray([
		Color(1.0, 0.85, 0.54, 0.0),
		Color(1.0, 0.89, 0.63, peak_alpha),
		Color(1.0, 0.95, 0.77, peak_alpha * 0.6),
		Color(1.0, 0.95, 0.77, 0.0),
	])
	var tex := GradientTexture1D.new()
	tex.gradient = grad
	return tex

# 一层光尘：draw pass 为 1×1 QuadMesh + 共享的 ADD 混合柔边材质，
# 尺寸由 ParticleProcessMaterial.scale_min/max 定（0.15–0.5m）。
func _make_dust_layer(amount: int, lifetime: float, scale_min: float, scale_max: float,
		vel_min: float, vel_max: float, extents: Vector3, peak_alpha: float) -> GPUParticles3D:
	var p := GPUParticles3D.new()
	p.amount = amount
	p.lifetime = lifetime
	p.preprocess = lifetime # 进场景即布满，不用等一个寿命周期才显形
	p.explosiveness = 0.0
	p.randomness = 0.45
	p.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var pm := ParticleProcessMaterial.new()
	# 沿阳光方向斜向下缓慢漂移（0.1–0.3 m/s）+ spread 做微小随机扰动；
	# 重力为零，速度即漂移速度，8 秒寿命只漂约 1–2m，仍留在阵列上方。
	pm.direction = Vector3(0.45, -1.0, 0.18).normalized()
	pm.spread = 18.0
	pm.gravity = Vector3.ZERO
	pm.initial_velocity_min = vel_min
	pm.initial_velocity_max = vel_max
	pm.scale_min = scale_min
	pm.scale_max = scale_max
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	pm.emission_box_extents = extents
	pm.color_ramp = _make_dust_ramp(peak_alpha)
	p.process_material = pm
	var quad := QuadMesh.new()
	quad.size = Vector2(1.0, 1.0)
	p.draw_pass_1 = quad
	p.material_override = _dust_mat
	# 发射盒覆盖阵列上方（pv_detail 局部坐标 x -12..+14、z -6..+6、y 1..6）；
	# 节点置于盒中心 (1, 3.5, 0)。visibility_aabb 必须覆盖发射盒 + 漂移全程，
	# 否则细节机位看不到节点原点时整个系统会被视锥裁剪（同 weather 雨丝教训）。
	p.position = Vector3(1.0, 3.5, 0.0)
	p.visibility_aabb = AABB(Vector3(-15, -6, -7), Vector3(30, 11, 14))
	p.emitting = false
	add_child(p)
	return p

func _build() -> void:
	# 逆变器箱：pv.glb 里已有三台真实逆变器（A1/A2/LAB），程序化箱子只在
	# pv.glb 加载失败时保留作回退，避免与 GLB 逆变器重叠。
	# （main._ready 里 campus.build() 先于内景实例化，was_loaded 此时已有结果；
	#  standalone 实例化时未尝试过则返回 false，默认保留箱子。）
	if not GlbLoader.was_loaded("pv"):
		_box(Vector3(14, 1.0, 0), Vector3(2.4, 2.0, 1.4), _mat(Color("#5b7186"), 0.45, 0.4))
		var led_mat := StandardMaterial3D.new()
		led_mat.albedo_color = Color("#38f27a")
		led_mat.emission_enabled = true
		led_mat.emission = Color("#38f27a")
		led_mat.emission_energy_multiplier = 1.4
		_box(Vector3(14, 1.6, 0.75), Vector3(0.3, 0.3, 0.06), led_mat)
	# 阳光光尘共享材质：unshaded + ADD 混合 + 程序化柔边圆点贴图，
	# 暖金不刺眼（albedo alpha 由 update_frame 随 pv_factor 缩放）。
	_dust_mat = StandardMaterial3D.new()
	_dust_mat.albedo_texture = _make_dust_texture()
	_dust_mat.albedo_color = Color(1.0, 0.92, 0.72, 0.85)
	_dust_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_dust_mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	_dust_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_dust_mat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	_dust_mat.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_DISABLED
	# 主层：140 粒、寿命 8s、0.15–0.35m；远层：40 粒、寿命 9s、0.30–0.50m
	# 更大更稀更慢更淡，两层合计 180 粒，疏密有层次，不成均匀雾、不成雪花。
	sun_dust = _make_dust_layer(140, 8.0, 0.15, 0.35, 0.10, 0.30,
		Vector3(13.0, 2.5, 6.0), 0.9)
	sun_dust_far = _make_dust_layer(40, 9.0, 0.30, 0.50, 0.08, 0.20,
		Vector3(11.0, 2.0, 5.0), 0.5)

func update_frame(pv_kw: float, pv_factor: float, t: float) -> void:
	# 天气门控：与 data/weather.json 的 pv_factor 同口径——雨天 0.30、暴雨 0.15
	# 均不显示；阴天 0.45、多云 0.75、晴天 1.00 仍显示。（旧 ray_planes 的原阈值
	# 0.18 时雨天 0.30 仍通过，雨天阳光残留，故沿用修过的 0.30 口径。）
	# 出力门控沿用旧 flow_dots 的 on 条件：pv_kw <= 2.0 时也视为关。
	var on := pv_kw > 2.0 and pv_factor > 0.30
	sun_dust.emitting = on
	sun_dust_far.emitting = on
	if on:
		# 强度随 pv_factor 缩放：0.30→刚过门槛最淡，1.00→最亮；
		# 透明度（材质 alpha）与密度（amount_ratio）同时跟 pv_factor 走。
		var f := clampf((pv_factor - 0.30) / 0.70, 0.0, 1.0)
		_dust_mat.albedo_color.a = 0.18 + 0.67 * f
		sun_dust.amount_ratio = 0.45 + 0.55 * f
		sun_dust_far.amount_ratio = 0.45 + 0.55 * f
