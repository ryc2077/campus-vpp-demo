class_name Labels3D
extends Node3D
## 屏幕空间标注：Label3D（billboard）+ 每 0.15s 复算。
## 已知问题修复（相对原 Demo）：
## 1) 被遮挡标签：一号教学楼/艺体馆/创造力中心/图书馆曾被别的标签挡住不显示——
##    本版先做深度遮挡射线检测（被楼体挡住才隐藏），再做屏幕空间去重叠：
##    按优先级排序，低优先级标签可上下微调（最多 9 档，见 _update）避让，实在排不开才隐藏。
##    去重叠要求最小净空：两标签字盒之间至少留 _min_gap（20px @720p），
##    只“刚好不交”（总览屋顶光伏/艺体馆曾只差 6px、冻结帧只差 16px，看着挤成一团）
##    也算撞上，继续试下一档；66/88 档是收紧后的逃生口，免得被挤的标签直接隐藏。
## 2) 标签屏上 y 钳制（顶栏 80 / 场景栏 视口高 − 84）必须折回 3D 位置：
##    旧代码只改判定 rect、不改锚点，渲染中心与 rect 脱节——池塘总览 659.7 落进
##    场景栏带、储能场景三号教学楼 48.3 / 配电房 69.7 落进顶栏带。本版全标签
##    用视线深度把（钳制量 + 档位）一次折回，渲染中心 = rect 中心。
## 3) 窄屏：宽度 < 760 时标签字号缩小、只保留 prio ≤ 4 的主标签。
## 4) 标签锚点贴设施顶部，不再悬空。
## 5) 面板进场动效（180ms scale 0.95→1.0，origin 在右缘）期间，
##    get_global_rect() 比终态 rect 小一圈，终态应藏掉的标签会先可见、
##    等下一轮 _update（150ms 间隔）才藏掉，闪现约 150ms。本版碰撞
##    用“动效结束后的终态 rect”（_final_rect 按 scale 关于 pivot 反推），
##    动效本身与时长一行不动；ABC 面板同理（储能 ABC 打开态 SOC 标签
##    终态 overlap 仅 0.09，动效中段实测会闪现，见 verify 检查）。
## 6) 锚点钉住（pin）：配电变压器与储能 SOC 锚点在总览屏上只差约 32px，
##    两字盒（高 30px）无论如何排不开——0/±22/±44 档全撞 SOC，+44 落到
##    宿舍楼 A 屋顶、−66 落到餐厅屋顶（探针：箱体附近 18 组锚点全量扫查，
##    无一落在箱体上）。故变压器标签允许在锚点原位（dy 0）与 SOC 标签叠放
##    一行（字距约 3px，两色区分）：仅 dy 0、仅撞 SOC 时放行，顶栏/场景栏/
##    面板守卫一律不绕过，全局净空规则与档位表一行不动。

var camera: Camera3D
var font: Font # Label3D 不走 Control 主题，main.gd 启动时把中文字体直接赋过来
var occluders: Array[Node3D] = []
var defs: Array[Dictionary] = []
var debug_shot := false # shot 模式才打印去重叠诊断（main.gd 据 _shot_mode 置位）
var _last_ms := 0
var _bottom_reserve := 84.0 # 底部场景栏高度 + 边距
var _top_reserve := 80.0 # 顶栏底 72px + 8px：标签不得躲进半透明顶栏后面
var panel_control: Control = null # 场景面板（右侧固定 UI）：main.gd 把 $UI/ScenePanel 赋过来；
# _update 里取其实时 get_global_rect() 作碰撞区，不硬编码像素 rect（面板宽随窗口变，
# ABC 双开时还会下移）。为 null 或面板不可见时（总览）不碰撞。
var abc_panel_control: Control = null # ABC 面板（右侧浮层 UI）：main.gd 把 $UI/ABCPanel 赋过来；
# 与场景面板同一模式：_update 里取其实时 get_global_rect() 作碰撞区，打开时才碰撞，
# 关闭时不碰撞；双开时场景面板下移、ABC 面板 rect 本身不动，实时取都跟得上。
var _min_gap := 20.0 # 去重叠最小净空（屏上 px，720p 口径）：候选字盒与已放字盒之间
# 至少留 20px 空隙才算排开，否则继续试下一档。只扩判定用的盒，不改 est_h。
# （02-storage 实测：储能柜标签 y≈48 落在顶栏带内，隔着 93% 白面板只剩约 7% 可见度，白字压白底）
var _ray: PhysicsRayQueryParameters3D

func add_label(text: String, color: Color, prio: int, anchor: Vector3, dynamic: String = "", pin: bool = false) -> Dictionary:
	var l := Label3D.new()
	l.text = text
	if font != null:
		l.font = font
	# Root cause of the giant blurry labels (see _update for the per-frame correction):
	# docs say fixed_size renders "the same size as if the camera was 1.0 units away",
	# so screen px = font_size * pixel_size * vp_h / (2*tan(fov/2)) at any distance.
	# Old values font_size 16 * pixel_size 0.012 = 0.192 world units -> ~133 screen px
	# at 720p / 55 deg fov, and outline 4 -> ~33 screen px of outline: huge + blurry.
	# Fix: large font_size (64, crisp glyph raster) with a matching small pixel_size so
	# the on-screen height is ~16px; outline scaled in proportion (4 @ 16 -> 16 @ 64)
	# to keep the same ~4px screen outline. pixel_size below is the 720p reference
	# value; _update() recomputes it from the live viewport height every 0.15s.
	l.fixed_size = true
	l.font_size = 64
	l.modulate = color
	l.outline_size = 16
	l.outline_modulate = Color(1, 1, 1, 0.92)
	l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	# Round 3：标签不做 3D 深度测试。锚点被别的楼挡住时仍由 _update 的射线检测隐藏；
	# 但下移避让的标签若留在自家楼体前会被楼面深度裁掉、只剩“一号/二号”两个字
	# （Round 2 总览截图实测），所以文字本身不参与深度裁剪。
	l.no_depth_test = true
	l.pixel_size = 0.0003615
	l.position = anchor
	l.visible = false
	add_child(l)
	var d := {"label": l, "text": text, "color": color, "prio": prio, "anchor": anchor, "dynamic": dynamic, "occ": false, "pin": pin}
	defs.append(d)
	return d

func set_dynamic_text(d: Dictionary, text: String) -> void:
	var l: Label3D = d["label"]
	if l.text != text:
		l.text = text

func _ready() -> void:
	_ray = PhysicsRayQueryParameters3D.new()

func _process(_delta: float) -> void:
	var now := Time.get_ticks_msec()
	if now - _last_ms < 150:
		return
	_last_ms = now
	_update()

func _final_rect(c: Control) -> Rect2:
	# 动效结束后的 rect：当前 rect 按 scale 关于 pivot 反推回 scale=1。
	# scale=1 时就是当前 rect；scale 异常（0）时退回当前 rect。
	# （实测 @720p：场景面板 scale 0.95 时 rect 左缘 +18px、底边 −28px；
	# ABC 面板左缘 +27px、底边 −19px；pivot 在右缘，右缘与顶边不动。）
	if c.scale == Vector2.ONE:
		return c.get_global_rect()
	var s: Vector2 = c.scale
	if absf(s.x) < 0.001 or absf(s.y) < 0.001:
		return c.get_global_rect()
	var t: Transform2D = c.get_global_transform_with_canvas()
	var pivot_g: Vector2 = t * c.pivot_offset
	var r: Rect2 = c.get_global_rect()
	var mn := Vector2(INF, INF)
	var mx := Vector2(-INF, -INF)
	for corner in [r.position, Vector2(r.end.x, r.position.y), Vector2(r.position.x, r.end.y), r.end]:
		var p: Vector2 = pivot_g + (corner - pivot_g) / s
		mn = mn.min(p)
		mx = mx.max(p)
	return Rect2(mn, mx - mn)


func _update() -> void:
	if camera == null:
		return
	var vp := get_viewport().get_visible_rect().size
	if vp.x <= 0.0 or vp.y <= 0.0:
		return
	var narrow: bool = vp.x < 760.0
	var space := get_world_3d().direct_space_state
	# 场景面板碰撞区：进场动效终态 rect（动效期间实时 rect 偏小，见 _final_rect；
	# 动效本身不动，只改碰撞口径）。面板隐藏时（总览）不碰撞。
	var panel_rect := Rect2()
	var panel_on := false
	if panel_control != null and panel_control.is_visible_in_tree():
		panel_rect = _final_rect(panel_control)
		panel_on = true
	# ABC 面板碰撞区：与场景面板同一模式，终态 rect（打开时才碰撞，
	# 关闭时不碰撞；双开时场景面板下移、ABC 面板 rect 本身不动，实时取都跟得上）。
	var abc_rect := Rect2()
	var abc_on := false
	if abc_panel_control != null and abc_panel_control.is_visible_in_tree():
		abc_rect = _final_rect(abc_panel_control)
		abc_on = true
	# Screen size correction (fixed_size normalises distance to 1.0, so distance
	# drops out; only viewport height and fov matter):
	#   screen_px = font_size * pixel_size * vp_h / (2*tan(fov/2))
	# Solve pixel_size for the target on-screen height (16px, 13px narrow).
	# This also keeps the size right if the window is resized to another height.
	var target_px := 13.0 if narrow else 16.0
	var px_per_world := vp.y / (2.0 * tan(deg_to_rad(camera.fov * 0.5)))
	var px_size := target_px / (64.0 * px_per_world)
	for d0 in defs:
		(d0["label"] as Label3D).pixel_size = px_size
	# 1) 深度遮挡：相机→锚点射线，命中楼体且在锚点前 2m 处才算挡住
	for d in defs:
		var anchor: Vector3 = d["anchor"]
		var to: Vector3 = anchor - camera.global_position
		var dist := to.length()
		d["occ"] = false
		if dist > 3.0:
			_ray.from = camera.global_position
			_ray.to = camera.global_position + to.normalized() * (dist - 2.0)
			_ray.collision_mask = 1
			var hit: Dictionary = space.intersect_ray(_ray)
			if not hit.is_empty():
				d["occ"] = true
	# 2) 按优先级排序，做屏幕空间去重叠
	# 根因（Round 2 实测）：旧代码符号反了——判定用的 rect 是
	#   Rect2(sp.x - w/2, sp.y - est_h + dy)（dy>0 表示 rect 向屏下移），
	# 但折回 3D 却是 anchor + up * world_dy（沿相机上方向 = 向屏上移）。
	# 判定以为标签被推下去了，实际却被推上去，正好压到上一行标签上，
	# 两者错开 2*dy（第 3 档差 114px），所以实测分离只有约 5-12px。
	# 本轮：rect 与 3D 位移同向（dy>0 = 向屏下 = anchor - up * world_dy），
	# 且 Label3D 默认双向居中，rect 改为以锚点屏上点为中心；
	# 候选档改为上下双向 6 档 × 22px，排不开才隐藏。
	var sorted: Array = defs.duplicate()
	sorted.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return int(a["prio"]) < int(b["prio"]))
	var placed: Array[Rect2] = []
	var placed_defs: Array = [] # 与 placed 一一对应：pin 判定要知道撞上的是谁（只撞 SOC 才放行）
	var dbg: Array[String] = []
	var n_visible := 0
	for d in sorted:
		var l: Label3D = d["label"]
		if bool(d["occ"]):
			l.visible = false
			continue
		if narrow and int(d["prio"]) > 4:
			l.visible = false
			continue
		var anchor: Vector3 = d["anchor"]
		if camera.is_position_behind(anchor):
			l.visible = false
			continue
		var sp: Vector2 = camera.unproject_position(anchor)
		# 屏上盒估计：实测字宽仍被低估（描边 4px/边 + 字体 advance 取整 +
		# Label3D 光栅化垫边），故实测串宽 ×1.25 再 +20px 裕量；
		# est_h = 字高 + 描边上下 + 裕量 = 16+14=30px。
		var est_w: float
		var est_h: float = target_px + 14.0
		if font != null:
			var m := font.get_string_size(l.text, HORIZONTAL_ALIGNMENT_LEFT, -1, int(target_px))
			est_w = minf(260.0, m.x * 1.25 + 20.0)
		else:
			est_w = minf(260.0, float(l.text.length()) * target_px * 1.25 + 20.0)
		# y 钳制：顶栏下限 80px（顶栏底 72 + 8），场景栏上限 视口高 − 84；
		# x 钳制在屏内。注意：钳制只改判定用的 rect（sp），没改锚点本身；
		# 折回 3D 时必须把钳制量也算进去，否则渲染位置与 rect 脱节——
		# 池塘、储能场景的三号教学楼与配电房都是这么落进栏带里的，
		# 见 dy 循环里的全标签折回。
		var sp_orig_y := sp.y
		sp.x = clampf(sp.x, est_w / 2.0 + 4.0, vp.x - est_w / 2.0 - 4.0)
		sp.y = clampf(sp.y, _top_reserve, vp.y - _bottom_reserve)
		var done := false
		# 双向 9 档：原位、上 22、下 22、上 44、下 44、上 66、下 66、上 88、下 88（px，屏上）。
		# 66/88 档是净空规则的逃生口：档位收紧后被挤的标签有地方去，不直接隐藏。
		var steps: Array[float] = [0.0, -22.0, 22.0, -44.0, 44.0, -66.0, 66.0, -88.0, 88.0]
		for dy in steps:
			# Label3D 默认水平/垂直均居中：盒以屏上锚点为中心。
			var r := Rect2(sp.x - est_w / 2.0, sp.y - est_h / 2.0 + dy, est_w, est_h)
			# Round 3：盒顶不得进顶栏（y < 80）。只钳制锚点中心不够——
			# dy 取负档时会把盒顶再拉进顶栏后面，绿字隔着 93% 白面板只剩约 7%
			# 可见度（Round 2 储能截图顶栏“储能柜 · SOC 56%”白字实测）。
			# 盒顶进顶栏按“撞上”处理，继续试下一档；都进顶栏则隐藏。
			if r.position.y < _top_reserve:
				continue
			# 场景栏修复：盒底不得进场景栏（y652–708 @720p）。只钳制锚点中心不够——
			# dy 取正档时会把盒底再推进场景栏后面（池塘总览即此例：中心钳在 636，
			# +22 档会把中心推到 658）。盒底进场景栏按“撞上”处理，继续试下一档；
			# 都进场景栏则隐藏。口径与中心钳制一致：盒底 ≤ vp.y − 84 + est_h/2
			#（720p 下为 651，场景栏顶 652 之上 1px）。
			if r.end.y > vp.y - _bottom_reserve + est_h / 2.0:
				continue
			# 场景面板修复（run 45247090332 的 02-storage 半截“餐厅”标签）：
			# 候选盒与实时面板 rect 相交按“撞上”处理，与顶栏/场景栏守卫同类，继续试下一档；
			# dy 档只能上下移、面板纵贯 y60–620，档位逃不出的标签按现有机制隐藏（不新写隐藏逻辑）。
			# 同类旧局限一并收敛：02-storage 配电变压器、04-charge 三号/配电房/配电变压器/
			# 储能 SOC、09-freeze 二号/创造力中心在面板后的，整条藏掉而非半截。
			if panel_on and r.intersects(panel_rect):
				continue
			# ABC 面板修复：与场景面板同一模式，候选盒与实时 ABC rect 相交按“撞上”
			# 处理，继续试下一档；ABC 纵贯 y60–440、档位逃不出的标签按现有机制隐藏
			#（不新写隐藏逻辑）。注意双开时 ABC 打开会把场景面板顶到 452，原先被
			# 场景面板藏掉的标签会复活到 ABC 矩形里——正是本修要藏掉的那批。
			if abc_on and r.intersects(abc_rect):
				continue
			# 净空规则：候选盒上下各扩 _min_gap 再判交——只“刚好不交”
			#（总览屋顶光伏/艺体馆曾只差 6px、冻结帧只差 16px）也算撞上，
			# 继续试下一档。扩的是判定用的盒，est_h 与顶栏检查口径不变。
			var hit2 := false
			var hit_soc_only := true # 撞上的是否全是 SOC 标签（pin 放行的前提）
			var rg := r.grow_individual(0.0, _min_gap, 0.0, _min_gap)
			for k in range(placed.size()):
				if rg.intersects(placed[k]):
					hit2 = true
					if String(placed_defs[k].get("dynamic", "")) != "soc":
						hit_soc_only = false
			# pin（规则 6，配电变压器专用）：dy 0 是箱体上唯一位置，撞的又只有
			# SOC 时原位叠放；顶栏/场景栏/面板守卫在上面已 continue，不绕过；
			# 其余档位、其余标签一律走原规则。
			if hit2 and not (bool(d.get("pin", false)) and dy == 0.0 and hit_soc_only):
				continue
			placed.append(r)
			placed_defs.append(d)
			# 把微调量折回 3D：dy>0 是向屏下移，对应 anchor 沿相机上方向的
			# 反方向（anchor - up * world_dy）；旧代码这里是 + 号，方向反了。
			# px_per_world = vp_h / (2*tan(fov/2))。
			var up: Vector3 = camera.global_transform.basis.y
			# 钳制折回（全标签通用；原先只修了 dynamic=="soc" 的储能标签，
			# run 45226479162）：sp 经顶栏/场景栏钳制后与锚点原投影 sp_orig_y
			# 脱节，旧折回只用了 dy，丢了钳制量，渲染中心与判定 rect 差几十 px——
			# 池塘总览锚点 y≈660 被钳到 636、取 0 档，渲染仍在 659.7 落进场景栏带；
			# 储能场景三号教学楼锚点 y≈−78 被钳到 80、取 +88 档，渲染只到 48.3
			# 落进顶栏带；配电房锚点 y≈43 被钳到 80、取 +22 档，渲染只到 69.7
			# 压在顶栏底边上。这里把钳制量也折回去，并用视线深度（非相机距离）
			# 换算：沿相机上方向位移 w 时屏上位移恰为 w*px_per_world/depth，
			# 渲染中心与 rect 一致（= sp.y + dy）。
			var fwd: Vector3 = -camera.global_transform.basis.z
			var depth: float = (anchor - camera.global_position).dot(fwd)
			var world_dy: float = (sp.y + dy - sp_orig_y) * depth / px_per_world
			l.position = anchor - up * world_dy
			l.visible = true
			n_visible += 1
			if debug_shot:
				dbg.append("%s@%d,%d,%d,%d" % [String(l.text), int(r.position.x), int(r.position.y), int(r.size.x), int(r.size.y)])
			done = true
			break
		if not done:
			l.visible = false
	if debug_shot:
		# 每 0.15s 一行汇总：可见数 + 各可见标签屏上 rect（x,y,w,h，整数 px）。
		# shot.mjs 抓 [console] 行，Actions 日志里可直接核对去重叠是否生效。
		print("[labels] n=%d %s" % [n_visible, " ".join(dbg)])
