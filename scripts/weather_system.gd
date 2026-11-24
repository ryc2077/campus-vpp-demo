class_name WeatherSystem
extends Node3D
# 注意：仓库根工程内 demo-godot/ 副本不得带全局类名——根 scripts/ 已有同名类，
# 重复声明会使 CI 导出包天气系统加载失败（run #97 全帧洗白回归）；推 demo 副本前须去掉首行。
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
var rain_quad: QuadMesh
var rain_dm: StandardMaterial3D
var clouds: Array[MeshInstance3D] = []
var cloud_mats: Array[StandardMaterial3D] = []
# R2-T12 云返工：网上实拍云照片贴图（assets/external/clouds/wikimedia-commons/，
# CC0/CC-BY，见 SOURCES.md §6）。每组云 = 1 张主云片 + 2 张小云片（同材质拼成云团），
# GL Compatibility 下体积云不可行，故用 BILLBOARD_ENABLED 贴图云片。
# clouds[i] 为每组的主云片（verify 用 clouds[0].position.x 测漂移，口径不变）；
# cloud_sats 为全部小云片（每组 2 张），_cloud_sat_off 为其相对主云片的偏移，
# 漂移时由主云片位置重算，保证云团不散开。
var puff_tex: Texture2D
var storm_tex: Texture2D
var cloud_sats: Array[MeshInstance3D] = []
var _cloud_sat_off: Array[Vector3] = []
var _cloud_sat_base_scale: Array[Vector3] = []
const CLOUD_SHOW_ORDER: Array[int] = [3, 0, 5, 1, 6, 2, 4] # 云量由少到多时按中心向外显现
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
	sky_mat.sky_horizon_color = Color("#bcd9f2")
	sky_mat.ground_bottom_color = Color("#4a6b38")
	sky_mat.ground_horizon_color = Color("#a9c6e0")
	_sky.sky_material = sky_mat
	env.environment.background_mode = Environment.BG_SKY
	env.environment.sky = _sky
	env.environment.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.environment.ambient_light_energy = 0.55
	env.environment.fog_enabled = true
	env.environment.fog_light_color = Color("#cfe0ee")
	# Fog 0.0009 -> 0.0005 (Round 2)：总览距离 235m 处透过率
	# exp(-0.0005*235) = 0.89（之前 0.81），地面不再被雾洗白。
	# F4 返工（2026-11-24）：雾再降到 0.0002——雾色偏蓝（#cfe0ee），
	# 晴天总览实测 B 通道仍比 SPEC 高约 +40，雾是其中一份。
	# 与 scenes/main.tscn 的 Environment_main 保持同步。
	env.environment.fog_density = 0.0002
	# R2-T7：色调映射保持 LINEAR（默认），不用 ACES。探针实测：GL Compatibility
	# 下 LINEAR 输出近似原始线性值，ACES 反而全帧提亮（天空 (112,176,186)→
	# (164,217,223)、草地 G 176→225），会冲破 F4 的 SPEC 锚点、更洗白。
	# 高光滚降改由太阳/天光配比 + 雾来做，不动 tonemap。
	_build_clouds()
	_build_rain()
	_build_shadows()
	flash_light = DirectionalLight3D.new()
	flash_light.light_energy = 0.0
	flash_light.rotation_degrees = Vector3(-60, 30, 0)
	add_child(flash_light)
	set_weather("sunny")

func _build_clouds() -> void:
	# R2-T12：7 组实拍云片（原 7 个白色半透明球，用户嫌假）。
	# 贴图缺失时回退旧球体（资源漏推时不至于整片天空空白）。
	puff_tex = load("res://assets/external/clouds/wikimedia-commons/cloud_puff.png") as Texture2D
	storm_tex = load("res://assets/external/clouds/wikimedia-commons/cloud_storm.png") as Texture2D
	if puff_tex == null or storm_tex == null:
		push_warning("R2-T12: cloud textures missing, falling back to sphere clouds")
		_build_clouds_legacy()
		return
	var i := 0
	while i < 7:
		var pos := Vector3(-220.0 + i * 70.0, 95.0 + (i % 3) * 12.0, -120.0 + (i % 4) * 60.0)
		var w := 66.0 + i * 7.0 # 主云片宽 66–108m（旧球体直径约 45–100m 同量级）
		var h := w * 0.72
		var m := StandardMaterial3D.new()
		m.albedo_texture = puff_tex
		m.albedo_color = Color(1, 1, 1, 0.85)
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		m.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
		cloud_mats.append(m)
		var main := _make_cloud_quad(m, Vector2(w, h), pos)
		clouds.append(main)
		# 两张小云片拼云团：左右错开、略低、尺寸 0.55–0.62×（只用节点缩放定尺寸，
		# QuadMesh 本身保持主云片尺寸，不双重缩放），一张水平翻转换形。
		var off_a := Vector3(-w * 0.32, -h * 0.18, -4.0)
		var sat_a := _make_cloud_quad(m, Vector2(w, h), pos + off_a)
		sat_a.scale = Vector3(0.62, 0.62, 1.0)
		cloud_sats.append(sat_a)
		_cloud_sat_off.append(off_a)
		_cloud_sat_base_scale.append(sat_a.scale)
		var off_b := Vector3(w * 0.30, -h * 0.12, 5.0)
		var sat_b := _make_cloud_quad(m, Vector2(w, h), pos + off_b)
		sat_b.scale = Vector3(-0.55, 0.55, 1.0) # 负 x 翻转贴图，同组两朵不重样
		cloud_sats.append(sat_b)
		_cloud_sat_off.append(off_b)
		_cloud_sat_base_scale.append(sat_b.scale)
		i += 1

func _make_cloud_quad(mat: StandardMaterial3D, size: Vector2, pos: Vector3) -> MeshInstance3D:
	var c := MeshInstance3D.new()
	var q := QuadMesh.new()
	q.size = size
	c.mesh = q
	c.material_override = mat
	c.position = pos
	add_child(c)
	return c

func _build_clouds_legacy() -> void:
	# 旧版白球云（仅贴图缺失时回退）；小云片数组留空，set_weather/update_frame 按空处理。
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
	rain_quad = QuadMesh.new()
	rain_quad.size = Vector2(0.12, 1.6)
	rain.draw_pass_1 = rain_quad
	rain_dm = StandardMaterial3D.new()
	rain_dm.albedo_color = Color(0.86, 0.94, 1.0, 0.7)
	rain_dm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	rain_dm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	rain_dm.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	rain.material_override = rain_dm
	rain.position = Vector3(0, 45, 0)
	# 雨丝不可见的真根因（run #97 实测：参数已进包、verify 235 全过，06/11
	# 仍零雨丝）：GPUParticles3D 默认 visibility_aabb 只有 8m 立方，位于节点
	# 原点 (0,45,0)；总览机位能看到该点所以暴雨有雨丝，PV/充电区细节机位
	# 根本看不到该点——整个粒子系统被视锥裁剪。雨丝发射盒 340×260m、
	# 下落约 50m，必须把可见 AABB 放到覆盖发射盒 + 下落全程（局部坐标：
	# x ±170、z ±130、y +1 至 −50）。
	rain.visibility_aabb = AABB(Vector3(-170, -50, -130), Vector3(340, 51, 260))
	rain.emitting = false
	add_child(rain)

func _build_shadows() -> void:
	# R2-T12：云影 blob 对齐到前 5 组云的地面投影（云 x/z 各 ×0.5 收入校园范围，
	# 原固定位置与新云团位置无关，阴天云影会飘在无云处）。
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
		var gp: Vector3 = clouds[i].position if i < clouds.size() else Vector3(-120.0 + i * 55.0, 95.0, -60.0 + (i % 3) * 55.0)
		b.position = Vector3(clampf(gp.x * 0.5, -110.0, 110.0), 0.15, clampf(gp.z * 0.5, -55.0, 55.0))
		add_child(b)
		shadow_blobs.append(b)
		i += 1

func set_weather(key: String) -> void:
	if not presets.has(key):
		return
	current_key = key
	current = presets[key]
	rain.emitting = bool(current.get("rain", false))
	# 雨丝可见性修补（2026-11-24，run #91 遗留：06/11 小雨雨丝未见、07 暴雨明显）：
	# 真根因在 _build_rain：默认 visibility_aabb 只有 8m 立方，细节机位看不到
	# 节点原点 (0,45,0) 时整个粒子系统被视锥裁剪（run #97 证实：参数已进包
	# 且 verify 全过，06/11 仍零雨丝）。密度是次要因素：雨天 820 粒 ×
	# 0.12m 细丝在细节机位帧内也偏稀，故一并提到 1800 粒、丝 0.15×1.9m、
	# alpha 0.85、颜色压深一档蓝灰；暴雨 2800 粒、丝与色原样，粒数仍高于雨天。
	# 五档 pv_factor/时长、阳光射线门控、V2G 弧线均未动。
	if key == "rain":
		rain.amount = 1800
		rain_quad.size = Vector2(0.15, 1.9)
		rain_dm.albedo_color = Color(0.70, 0.80, 0.92, 0.85)
	elif key == "storm":
		rain.amount = 2800
		rain_quad.size = Vector2(0.12, 1.6)
		rain_dm.albedo_color = Color(0.86, 0.94, 1.0, 0.7)
	rain_mat.gravity = Vector3(0, -82, 0) if key == "storm" else Vector3(0, -55, 0)
	if rain.emitting:
		rain.restart()
	var cloud_col := Color.WHITE
	match key:
		"sunny": cloud_col = Color("#ffffff")
		"cloudy": cloud_col = Color("#f2f5f7")
		"overcast": cloud_col = Color("#9fb2c0")
		"rain": cloud_col = Color("#8296a8")
		"storm": cloud_col = Color("#5f7488")
	for m in cloud_mats:
		m.albedo_color = Color(cloud_col.r, cloud_col.g, cloud_col.b, 0.95 if key != "sunny" else 0.85)
	# R2-T12 云联动（只动云，不动 pv_factor/雨/闪电等业务逻辑）：
	# 贴图：雨/暴雨换积雨云团，晴/多云/阴用积云；云量按 weather.json cloud_cover
	# 显隐（晴 1 / 多云 3 / 阴 5 / 雨 6 / 暴雨 7 组，中心向外）；云团随档放大
	#（阴天盖顶、雨天压暗已由上方 tint 负责，缩放只改覆盖感）。
	if puff_tex != null and storm_tex != null:
		var tex: Texture2D = storm_tex if (key == "rain" or key == "storm") else puff_tex
		for m in cloud_mats:
			m.albedo_texture = tex
	var cover: float = clampf(float(current.get("cloud_cover", 0.08)), 0.0, 1.0)
	var n_show: int = clampi(int(round(cover * 7.0)), 1, 7)
	var f := 0.9 if key == "sunny" else (1.0 if key == "cloudy" else (1.12 if key == "overcast" else (1.18 if key == "rain" else 1.25)))
	for i in clouds.size():
		var vis: bool = CLOUD_SHOW_ORDER.find(i) < n_show
		clouds[i].visible = vis
		clouds[i].scale = Vector3.ONE * f
		for j in 2:
			var si := i * 2 + j
			if si < cloud_sats.size():
				cloud_sats[si].visible = vis
				cloud_sats[si].scale = _cloud_sat_base_scale[si] * f

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
	# F4 返工（2026-11-24）：晴天总览地面实测约 #9FFFCD、G 通道截顶，
	# 远淡于 SPEC #69B45E。根因在 Godot 侧光照，不在贴图：
	# 地面贴图均值实测正是 #69B45D、UV/法线正确；同 run 回退帧（程序化
	# 平色地面 #4F9D43）一样洗白，而跑道（#B8543F 采样实测）与楼体
	# 基本正确、暴雨帧地面色相正确只是偏暗——晴天总光强过高且天光
	# 偏蓝。标定：晴天总光照约需从 2.3× 降到约 1.0×（SPEC 即反照率），
	# 其中太阳 1.38→0.83、天光 0.73→0.28；其余天气按同一公式走，
	# 暴雨会再暗一点（本就偏暗，属可接受的情景对比）。
	# R2-T7 灯光自然化（2026-11-24，用户：灯光太假、光照要自然）：
	# 诊断（run9 目视 00/06/07/11 + 探针逐档量测）：
	#  1. 太阳阴影关（main.tscn Sun shadow_enabled=false）且 F4 探针证实
	#     GL Compatibility 下开阴影反把地面洗白（平色地面 G 156→226 截顶，
	#     bias/ortho/maxdist/blur 全测无效），阴影必须保持关闭（verify 有锁）。
	#     层次改由"直射/天光比"补：晴天太阳抬、天光压，楼体向阳面与背阴面
	#     拉开（探针双墙比 1.15→目标 ≥1.30）；阴雨天反过来，天光主导、本就该平。
	#  2. 天光能量之前是常量：ProceduralSkyMaterial sky/ground energy 默认
	#     1.0 全天气、全时刻不变，只有太阳随天气变——雨/暴雨只剩"整体加灰
	#     滤镜"感（探针：阴天与雨天草地 G 同为 117，五档拉不开）。现 sky/ground
	#     energy 随天气 + 昼夜走。
	#  3. 雾色恒蓝白：雨/暴雨远景也被雾漂蓝。现雾色随天气由蓝白 → 灰，雾密度
	#     随天气加厚（晴 0.0002 → 暴雨 0.0011）。
	#  4. 无色调映射：高光直截顶。ACES 已探针证伪（见 setup 注释：全帧提亮、
	#     破 SPEC），保持 LINEAR，高光改由太阳/天光配比 + 雾来收。
	# 晴天正午地面总光照保持 F4 标定（太阳 0.83→0.95、天光 1.0→0.85，
	# 地面反照率 SPEC #69B45E 不动），只改直射/漫射配比。
	var pvf: float = float(current.get("pv_factor", 1.0))
	sun.light_energy = (0.15 + 0.80 * daylight) * wx_dim * lf
	var warm := Color("#ffb347")
	var noon := Color("#fff3d6")
	var sun_col := warm.lerp(noon, daylight)
	# 雨/暴雨太阳发灰，不再暖白（去饱和向 #c9d1d8 走 (1-pv)*0.45）。
	sun_col = sun_col.lerp(Color("#c9d1d8"), (1.0 - pvf) * 0.45)
	sun.light_color = sun_col
	# 太阳方位：东升西落
	sun.rotation_degrees = Vector3(-55.0 * maxf(sun_el, 0.05) - 8.0, -35.0 + 70.0 * clampf((hour - rise) / maxf(0.1, set_h - rise), 0.0, 1.0), 0.0)
	# 天空颜色：昼夜 + 天气压暗（白天顶色加深一档，之前 #8ec9f0 偏淡）
	var night := Color("#33507c")
	# F4 B 通道残留定夺（2026-11-24，选②改天空颜色，探针逐档量过）：
	# 顶色 B 230→180（#63a9e6→#63a9b4），只动 B、R/G 一分不动。最小探针
	# （平色地面 + 复刻晴天 09:00 环境/太阳/总览机位，xvfb + llvmpipe）：
	# 草地 #69B45D (96.4,177.7,120.7)→(96.4,177.7,101.5)，R/G 纹丝不动、
	# B +26→+7.5（SPEC (105,180,94) ±15 全进）；回退地面 #4F9D43
	# (77.1,157.5,100.6)→(77.1,157.5,83.6)。天空 (111,176,232)→
	# (111,176,186)，仍是蓝色（B−G +10），未变青灰；B 再降到 170 时
	# 天空 B≈G 已不像蓝天，故取 180 不再降。地平线/雾色由顶色派生，
	# 同向跟降；太阳/雾密度/色调映射/地面材质一概不动。
	var day := Color("#63a9b4")
	var dusk := Color("#f6bd8a")
	var sky_col := night.lerp(day, daylight)
	var dusk_f: float = (1.0 - absf(sun_el - 0.16) / 0.24) if (sun_el > -0.05 and sun_el < 0.38) else 0.0
	sky_col = sky_col.lerp(dusk, clampf(dusk_f, 0.0, 1.0) * 0.45)
	if current_key != "sunny":
		sky_col = sky_col.lerp(Color("#4d6072"), (1.0 - pvf) * 0.55)
	var sky_mat: ProceduralSkyMaterial = _sky.sky_material
	sky_mat.sky_top_color = sky_col
	# 地平线混白 0.22 -> 0.16（R2-T7：天空下半仍偏淡、发白）。
	sky_mat.sky_horizon_color = sky_col.lerp(Color.WHITE, 0.16)
	# R2-T7：天光能量随天气 + 昼夜（之前恒 1.0）。地面 horizon/bottom 也随
	# 天气由蓝白/亮绿向灰走，雨/暴雨地平线不再泛蓝。
	sky_mat.ground_horizon_color = Color("#a9c6e0").lerp(Color("#75828d"), (1.0 - pvf) * 0.8)
	sky_mat.ground_bottom_color = Color("#4a6b38").lerp(Color("#3a4c34"), (1.0 - pvf) * 0.8)
	var sky_e := 0.85
	var gnd_e := 0.65
	match current_key:
		"cloudy":
			sky_e = 0.72
			gnd_e = 0.55
		"overcast":
			sky_e = 0.58
			gnd_e = 0.45
		"rain":
			sky_e = 0.48
			gnd_e = 0.35
		"storm":
			sky_e = 0.45
			gnd_e = 0.32
	# 昼夜系数放缓（0.15+0.85*daylight 在暴雨清晨 daylight 0.58 时把天光
	# 压到 0.24、草地 G 只剩 49，死黑；现 0.45+0.55*daylight，暴雨清晨约 0.77）。
	var day_f: float = 0.45 + 0.55 * daylight
	sky_mat.sky_energy_multiplier = sky_e * day_f
	sky_mat.ground_energy_multiplier = gnd_e * day_f
	# F4 后续（2026-11-24，探针证实）：天光能量这档对 SKY 天光源不起作用
	# （ambient_light_energy 在 GL Compatibility 下 0↔2 渲染分毫不差；
	# 真正的天光强度由 ProceduralSkyMaterial 的 sky/ground energy 控制），
	# 此处数值保留只为不扰动其他天气档。地面偏淡的残留根因是太阳阴影
	# （见 scenes/main.tscn：Sun shadow_enabled=false），不在此改。
	env.environment.ambient_light_energy = 0.12 + 0.16 * daylight
	# R2-T7：雾密度随天气加厚；雾色 tint 由白 → 灰（雨/暴雨远景不再漂蓝）。
	var fog_d := 0.0002
	match current_key:
		"cloudy":
			fog_d = 0.00035
		"overcast":
			fog_d = 0.0005
		"rain":
			fog_d = 0.0008
		"storm":
			fog_d = 0.0011
	env.environment.fog_density = fog_d
	var fog_tint := Color.WHITE.lerp(Color("#9aa7b2"), (1.0 - pvf) * 0.7)
	env.environment.fog_light_color = sky_col.lerp(fog_tint, 0.10)
	# 云漂移 + 云影（减弱动效时冻结，P3-4）
	if not reduced_motion:
		var spd := 2.6 if current_key == "storm" else (1.5 if current_key == "cloudy" or current_key == "overcast" else 1.0)
		var i := 0
		for c in clouds:
			c.position.x += delta * (1.0 + i * 0.17) * spd * 2.0
			if c.position.x > 300.0:
				c.position.x = -300.0
			# R2-T12：小云片跟主云片走（由主云片位置 + 固定偏移重算，云团不散开、
			# 越界折回时整团一起折回；旧球体回退时 cloud_sats 为空，本段无操作）。
			for j in 2:
				var si := i * 2 + j
				if si < cloud_sats.size():
					cloud_sats[si].position = c.position + _cloud_sat_off[si]
			i += 1
		# R2-T7：云影加深一档（阴天云影是太阳阴影关闭后唯一的地面明暗变化，
		# 原 0.13/0.17 几乎看不见；雨/暴雨保持 0，全天本就是阴影）。
		var blob_target := 0.18 if current_key == "cloudy" else (0.24 if current_key == "overcast" else 0.0)
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
