class_name WeatherSystem
extends Node3D
## 天气系统：晴/多云/阴/雨/暴雨五档（weather.json）。
## 联动：太阳光强度与颜色、天空/雾色、云层颜色与漂移、云影、雨幕粒子、
## 暴雨闪电。光伏出力系数 pv_factor 由仿真引擎共用同一份数据。

var presets: Dictionary = {}
var order: Array = []
var current_key := "sunny"
var current: Dictionary = {}

var sun: DirectionalLight3D
var env: WorldEnvironment
var rain: GPUParticles3D
var rain_mat: ParticleProcessMaterial
var clouds: Array[MeshInstance3D] = []
var cloud_mats: Array[StandardMaterial3D] = []
var shadow_blobs: Array[MeshInstance3D] = []
var flash_light: DirectionalLight3D
var reduced_motion := false # P3-4：减弱动效时停闪电、云漂移与云影漂移（由 main._set_reduced_motion 设置）
var _flash_until := -1.0
var _next_flash := 6.0
var _t := 0.0
var _sky: Sky

func setup(data: Dictionary, p_sun: DirectionalLight3D, p_env: WorldEnvironment) -> void:
	presets = data["presets"]
	order = data["order"]
	sun = p_sun
	env = p_env
	_sky = Sky.new()
	var sky_mat := ProceduralSkyMaterial.new()
	# 总览偏淡修复：天顶/地平加深一档（之前 #6db9f2/#dff2ff 洗得发白）
	sky_mat.sky_top_color = Color("#4f9fe8")
	sky_mat.sky_horizon_color = Color("#cfe8fb")
	sky_mat.ground_bottom_color = Color("#4a6b38")
	sky_mat.ground_horizon_color = Color("#b7d2e8")
	_sky.sky_material = sky_mat
	env.environment.background_mode = Environment.BG_SKY
	env.environment.sky = _sky
	env.environment.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.environment.ambient_light_energy = 0.6
	env.environment.fog_enabled = true
	env.environment.fog_light_color = Color("#cfe0ee")
	env.environment.fog_density = 0.0012
	_build_clouds()
	_build_rain()
	_build_shadows()
	flash_light = DirectionalLight3D.new()
	flash_light.light_energy = 0.0
	flash_light.rotation_degrees = Vector3(-60, 30, 0)
	add_child(flash_light)
	set_weather("sunny")

func _build_clouds() -> void:
	var i := 0
	while i < 7:
		var c := MeshInstance3D.new()
		var sm := SphereMesh.new()
		sm.radius = 14.0 + i * 3.0
		sm.height = 5.0
		c.mesh = sm
		var m := StandardMaterial3D.new()
		m.albedo_color = Color(1, 1, 1, 0.92)
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		c.material_override = m
		cloud_mats.append(m)
		c.position = Vector3(-220.0 + i * 70.0, 95.0 + (i % 3) * 12.0, -120.0 + (i % 4) * 60.0)
		c.scale = Vector3(1.6, 1.0, 1.1)
		add_child(c)
		clouds.append(c)
		i += 1

func _build_rain() -> void:
	rain = GPUParticles3D.new()
	rain.amount = 2200
	rain.lifetime = 0.9
	rain.explosiveness = 0.0
	rain.randomness = 0.4
	rain_mat = ParticleProcessMaterial.new()
	rain_mat.direction = Vector3(0.12, -1, 0.05)
	rain_mat.spread = 4.0
	rain_mat.gravity = Vector3(0, -55, 0)
	rain_mat.initial_velocity_min = 42.0
	rain_mat.initial_velocity_max = 68.0
	rain_mat.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	rain_mat.emission_box_extents = Vector3(170, 1, 130)
	rain.process_material = rain_mat
	var draw := ParticleProcessMaterial.new()
	var quad := QuadMesh.new()
	quad.size = Vector2(0.12, 1.6)
	rain.draw_pass_1 = quad
	var dm := StandardMaterial3D.new()
	dm.albedo_color = Color(0.86, 0.94, 1.0, 0.7)
	dm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	dm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	dm.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	rain.material_override = dm
	rain.position = Vector3(0, 45, 0)
	rain.emitting = false
	add_child(rain)

func _build_shadows() -> void:
	var i := 0
	while i < 5:
		var b := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = 24.0 + i * 6.0
		cm.bottom_radius = 24.0 + i * 6.0
		cm.height = 0.1
		b.mesh = cm
		var m := StandardMaterial3D.new()
		m.albedo_color = Color(0.11, 0.19, 0.25, 0.0)
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		b.material_override = m
		b.position = Vector3(-120.0 + i * 55.0, 0.15, -60.0 + (i % 3) * 55.0)
		add_child(b)
		shadow_blobs.append(b)
		i += 1

func set_weather(key: String) -> void:
	if not presets.has(key):
		return
	current_key = key
	current = presets[key]
	rain.emitting = bool(current.get("rain", false))
	rain.amount = 2200 if key == "storm" else 820
	rain_mat.gravity = Vector3(0, -82, 0) if key == "storm" else Vector3(0, -55, 0)
	var cloud_col := Color.WHITE
	match key:
		"sunny": cloud_col = Color("#ffffff")
		"cloudy": cloud_col = Color("#f2f5f7")
		"overcast": cloud_col = Color("#9fb2c0")
		"rain": cloud_col = Color("#8296a8")
		"storm": cloud_col = Color("#5f7488")
	for m in cloud_mats:
		m.albedo_color = Color(cloud_col.r, cloud_col.g, cloud_col.b, 0.95 if key != "sunny" else 0.85)

## 每帧：按仿真时刻与天气调光。hour 为 0–24；daylight 由日出/日落正弦弧算出。
func update_frame(hour: float, delta: float) -> void:
	_t += delta
	var rise: float = current.get("rise", 6.0)
	var set_h: float = current.get("set", 19.0)
	var sa := PI * (hour - rise) / maxf(0.1, set_h - rise)
	var sun_el := sin(sa)
	var daylight := clampf(sun_el * 1.7, 0.0, 1.0)
	var wx_dim: float = 0.45 + 0.55 * float(current.get("pv_factor", 1.0))
	var lf: float = current.get("light_factor", 1.0)
	sun.light_energy = (0.18 + 1.2 * daylight) * wx_dim * lf
	var warm := Color("#ffb347")
	var noon := Color("#fff3d6")
	sun.light_color = warm.lerp(noon, daylight)
	# 太阳方位：东升西落
	sun.rotation_degrees = Vector3(-55.0 * maxf(sun_el, 0.05) - 8.0, -35.0 + 70.0 * clampf((hour - rise) / maxf(0.1, set_h - rise), 0.0, 1.0), 0.0)
	# 天空颜色：昼夜 + 天气压暗（白天顶色加深一档，之前 #8ec9f0 偏淡）
	var night := Color("#33507c")
	var day := Color("#63a9e6")
	var dusk := Color("#f6bd8a")
	var sky_col := night.lerp(day, daylight)
	var dusk_f: float = (1.0 - absf(sun_el - 0.16) / 0.24) if (sun_el > -0.05 and sun_el < 0.38) else 0.0
	sky_col = sky_col.lerp(dusk, clampf(dusk_f, 0.0, 1.0) * 0.45)
	if current_key != "sunny":
		sky_col = sky_col.lerp(Color("#5d7488"), (1.0 - float(current.get("pv_factor", 1.0))) * 0.30)
	var sky_mat: ProceduralSkyMaterial = _sky.sky_material
	sky_mat.sky_top_color = sky_col
	sky_mat.sky_horizon_color = sky_col.lerp(Color.WHITE, 0.45)
	env.environment.ambient_light_energy = 0.32 + 0.5 * daylight
	env.environment.fog_light_color = sky_col.lerp(Color.WHITE, 0.25)
	# 云漂移 + 云影（减弱动效时冻结，P3-4）
	if not reduced_motion:
		var spd := 2.6 if current_key == "storm" else (1.5 if current_key == "cloudy" or current_key == "overcast" else 1.0)
		var i := 0
		for c in clouds:
			c.position.x += delta * (1.0 + i * 0.17) * spd * 2.0
			if c.position.x > 300.0:
				c.position.x = -300.0
			i += 1
		var blob_target := 0.13 if current_key == "cloudy" else (0.17 if current_key == "overcast" else 0.0)
		for b in shadow_blobs:
			var m: StandardMaterial3D = b.material_override
			var a: float = m.albedo_color.a
			a += (blob_target - a) * 0.03
			m.albedo_color.a = a
			b.visible = a > 0.01
			b.position.x += delta * 3.2 * spd
			if b.position.x > 240.0:
				b.position.x = -240.0
	# 暴雨闪电（减弱动效时不闪，P3-4）
	if current_key == "storm" and not reduced_motion:
		if _t > _next_flash:
			_flash_until = _t + 0.14
			_next_flash = _t + 3.0 + randf() * 6.0
		flash_light.light_energy = 2.2 if _t < _flash_until else 0.0
	else:
		flash_light.light_energy = 0.0
