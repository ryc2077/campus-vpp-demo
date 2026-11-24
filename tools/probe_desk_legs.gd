extends SceneTree
## R2-T36 桌椅腿导入运行时探针（只诊断，不改模型、不改机位、不改 verify_fixes.gd）。
## 用法：Godot_v4.4-stable_linux.x86_64 --headless --path . -s tools/probe_desk_legs.gd
## 只加载 res://assets/models/scenes/classroom.glb 一个文件（不跑全量 --import、不跑 Web 导出）。
## 遍历 ClassroomGLB 的 desk/chair 节点，逐项打印每个 MeshInstance3D 的
## surface 数、三角/顶点数、AABB、材质与 visible，确认 student-desk_0 的
## leg_metal 面是否进场景、变换是否正确、材质是否与椅腿相同。
## 对照真值（GLB JSON 直读，本地 classroom.glb blob 52d0ac03，R2-T28 版）：
##   desk mesh 73 "student-desk_0": prim0 desk_wood 235v/96t y[0.67,0.70]；
##     prim1 leg_metal 1610v/684t y[0,0.67]；chair mesh 74 "student-chair_0":
##     prim0 chair_wood 466v/192t y[0.398,0.888]；prim1 leg_metal 922v/388t y[0,0.882]。
##   leg_metal: opaque、doubleSided、metallicFactor 0.75、无 roughnessFactor、
##     baseColorTexture + metallicRoughnessTexture + normalTexture。
## 退出码恒为 0（诊断脚本，结论在输出里，不判 PASS/FAIL）；超时/加载失败时
## 打印 PROBE-ERROR 并 quit(1)。

var _frames := 0
var _done := false
var _root: Node = null
var _issues: Array[String] = []


const GLB_PATH := "res://assets/models/scenes/classroom.glb"

var _load_path := ""


func _init() -> void:
	# 路径 1：已导入的 PackedScene（游戏/CI 实际走的路；需 .godot/imported 里有该文件）。
	var packed := load(GLB_PATH) as PackedScene
	if packed != null:
		_load_path = "packedscene-imported"
		_root = packed.instantiate() as Node3D
	else:
		# 路径 2：本地 .godot 从未导入过 classroom.glb 时 ResourceLoader 无
		# loader（见 PROBE-ERROR 实测），改走运行时 GLTFDocument 直读——与编
		# 辑器导入同用 glTF 解析器（无 .import 文件即默认设置），只不走贴图
		# 转码；结构/变换/材质参数与导入路径同源。编辑器导入路径另用最小
		# 工程复核（见 §37）。
		print("PROBE note: PackedScene 加载失败，改走 GLTFDocument 运行时直读")
		var doc := GLTFDocument.new()
		var state := GLTFState.new()
		var err := doc.append_from_file(GLB_PATH, state)
		if err != OK:
			print("PROBE-ERROR: GLTFDocument 直读失败 err=%d" % err)
			quit(1)
			return
		_load_path = "gltfdocument-runtime"
		_root = doc.generate_scene(state) as Node3D
	if _root == null:
		print("PROBE-ERROR: classroom.glb 实例化失败（根节点不是 Node3D）")
		quit(1)
		return
	_root.name = "ClassroomGLB"
	root.add_child(_root)


func _v3(v: Vector3) -> String:
	return "(%.3f, %.3f, %.3f)" % [v.x, v.y, v.z]


func _aabb_str(a: AABB) -> String:
	return "pos%s size%s" % [_v3(a.position), _v3(a.size)]


func _surf_aabb(mesh: ArrayMesh, surf: int) -> AABB:
	var arrs: Array = mesh.surface_get_arrays(surf)
	var verts: PackedVector3Array = arrs[Mesh.ARRAY_VERTEX]
	var a := AABB()
	if verts.is_empty():
		return a
	a.position = verts[0]
	a.size = Vector3.ZERO
	for v in verts:
		a = a.expand(v)
	return a


func _surf_counts(mesh: ArrayMesh, surf: int) -> Array:
	# [顶点数, 三角数, 索引数（-1=无索引）, 法线数, UV 数]
	var arrs: Array = mesh.surface_get_arrays(surf)
	var verts: PackedVector3Array = arrs[Mesh.ARRAY_VERTEX]
	var idx: PackedInt32Array = arrs[Mesh.ARRAY_INDEX]
	var nrm: PackedVector3Array = arrs[Mesh.ARRAY_NORMAL]
	var uv: PackedVector2Array = arrs[Mesh.ARRAY_TEX_UV]
	var tris := -1
	if idx != null and not idx.is_empty():
		tris = idx.size() / 3
	elif not verts.is_empty():
		tris = verts.size() / 3
	return [verts.size(), tris, (idx.size() if idx != null else -1), nrm.size(), uv.size()]


func _degenerate_frac(mesh: ArrayMesh, surf: int) -> Array:
	# [退化三角数, 总三角数, 退化比例]：面积 <1e-9 m^2 的三角计为退化。
	var arrs: Array = mesh.surface_get_arrays(surf)
	var verts: PackedVector3Array = arrs[Mesh.ARRAY_VERTEX]
	var idx: PackedInt32Array = arrs[Mesh.ARRAY_INDEX]
	var total := 0
	var degen := 0
	if idx != null and not idx.is_empty():
		total = idx.size() / 3
		for t in range(total):
			var a: Vector3 = verts[idx[t * 3]]
			var b: Vector3 = verts[idx[t * 3 + 1]]
			var c: Vector3 = verts[idx[t * 3 + 2]]
			if (b - a).cross(c - a).length() * 0.5 < 1e-9:
				degen += 1
	elif not verts.is_empty():
		total = verts.size() / 3
		for t in range(total):
			var a2: Vector3 = verts[t * 3]
			var b2: Vector3 = verts[t * 3 + 1]
			var c2: Vector3 = verts[t * 3 + 2]
			if (b2 - a2).cross(c2 - a2).length() * 0.5 < 1e-9:
				degen += 1
	return [degen, total, (float(degen) / float(total) if total > 0 else 0.0)]


func _normal_stats(mesh: ArrayMesh, surf: int) -> Array:
	# [零长法线数, 法线总数, 平均模长]
	var arrs: Array = mesh.surface_get_arrays(surf)
	var nrm: PackedVector3Array = arrs[Mesh.ARRAY_NORMAL]
	var zero := 0
	var sum := 0.0
	for n in nrm:
		sum += n.length()
		if n.length() < 1e-6:
			zero += 1
	return [zero, nrm.size(), (sum / float(nrm.size()) if not nrm.is_empty() else 0.0)]


func _mat_str(mat: Material) -> String:
	if mat == null:
		return "mat=null"
	var sm := mat as StandardMaterial3D
	if sm == null:
		return "mat=" + mat.get_class() + " (not StandardMaterial3D)"
	var transp := "?"
	match sm.transparency:
		BaseMaterial3D.TRANSPARENCY_DISABLED:
			transp = "DISABLED(opaque)"
		BaseMaterial3D.TRANSPARENCY_ALPHA:
			transp = "ALPHA"
		BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR:
			transp = "ALPHA_SCISSOR"
		BaseMaterial3D.TRANSPARENCY_ALPHA_HASH:
			transp = "ALPHA_HASH"
		_:
			transp = "OTHER(%d)" % int(sm.transparency)
	var cull := "?"
	match sm.cull_mode:
		BaseMaterial3D.CULL_BACK:
			cull = "BACK"
		BaseMaterial3D.CULL_FRONT:
			cull = "FRONT"
		BaseMaterial3D.CULL_DISABLED:
			cull = "DISABLED(double-sided)"
	return ("mat='%s' id=%d albedo=%s a=%.2f metallic=%.2f roughness=%.2f transp=%s cull=%s "
		+ "shading=%d albedo_tex=%s metal_tex=%s rough_tex=%s normal_tex=%s emission=%s") % [
		sm.resource_name, sm.get_instance_id(), str(sm.albedo_color), sm.albedo_color.a,
		sm.metallic, sm.roughness, transp, cull, int(sm.shading_mode),
		("YES" if sm.albedo_texture != null else "NO"),
		("YES" if sm.metallic_texture != null else "NO"),
		("YES" if sm.roughness_texture != null else "NO"),
		("YES" if sm.normal_texture != null else "NO"),
		("YES" if sm.emission_enabled else "NO")]


func _surf_report(mi: MeshInstance3D, surf: int) -> String:
	var mesh := mi.mesh as ArrayMesh
	var smat := mesh.surface_get_material(surf)
	var ovr := mi.get_surface_override_material(surf)
	var cnt: Array = _surf_counts(mesh, surf)
	var aabb := _surf_aabb(mesh, surf)
	var line := "  surf%d: %s | verts=%d tris=%d idx=%d normals=%d uvs=%d | localAABB %s | override=%s" % [
		surf, _mat_str(smat), cnt[0], cnt[1], cnt[2], cnt[3], cnt[4], _aabb_str(aabb),
		("YES:" + _mat_str(ovr) if ovr != null else "none")]
	return line


func _mi_report(mi: MeshInstance3D, detail: bool) -> String:
	var mesh := mi.mesh as ArrayMesh
	var sc := mi.global_transform.basis.get_scale()
	var out := "MI %s: visible=%s in_tree=%s pos=%s scale=%s mesh_id=%d surf=%d meshAABB=%s cast_shadow=%d layers=%d vis_range=[%.1f,%.1f] mat_override=%s" % [
		mi.name, str(mi.visible), str(mi.is_visible_in_tree()), _v3(mi.global_transform.origin),
		_v3(sc), (mi.mesh.get_instance_id() if mi.mesh != null else -1),
		(mesh.get_surface_count() if mesh != null else -1),
		(_aabb_str(mesh.get_aabb()) if mesh != null else "null"),
		int(mi.cast_shadow), int(mi.layers), mi.visibility_range_begin, mi.visibility_range_end,
		("YES" if mi.material_override != null else "none")]
	if detail and mesh != null:
		for s in range(mesh.get_surface_count()):
			out += "\n" + _surf_report(mi, s)
	return out


func _collect(root_node: Node, out_mi: Array, out_all: Array) -> void:
	var stack: Array[Node] = [root_node]
	while not stack.is_empty():
		var n: Node = stack.pop_back()
		out_all.append(n)
		if n is MeshInstance3D:
			out_mi.append(n)
		for ch in n.get_children():
			stack.push_back(ch)


func _process(_delta: float) -> bool:
	_frames += 1
	if _frames < 3 or _done:
		return false
	_done = true
	if _frames > 30:
		print("PROBE-ERROR: 超时未完成")
		quit(2)
		return true

	var ver: Dictionary = Engine.get_version_info()
	print("PROBE godot=%s.%s.%s %s load_path=%s" % [ver["major"], ver["minor"], ver["patch"], ver["status"], _load_path])
	print("PROBE root: name=%s class=%s children=%d" % [_root.name, _root.get_class(), _root.get_child_count()])

	var all_nodes: Array = []
	var mis: Array = []
	_collect(_root, mis, all_nodes)
	print("PROBE counts: nodes=%d MeshInstance3D=%d" % [all_nodes.size(), mis.size()])

	# ---- 隐藏/异常节点全扫 ----
	var hidden: Array[String] = []
	var null_mesh: Array[String] = []
	var zero_surf: Array[String] = []
	var zero_scale: Array[String] = []
	for n in all_nodes:
		if n is Node3D and not (n as Node3D).visible:
			hidden.append(n.name)
		if n is MeshInstance3D:
			var m := n as MeshInstance3D
			if m.mesh == null:
				null_mesh.append(m.name)
			elif (m.mesh as ArrayMesh).get_surface_count() == 0:
				zero_surf.append(m.name)
			var s := m.global_transform.basis.get_scale()
			if s.x < 1e-6 or s.y < 1e-6 or s.z < 1e-6:
				zero_scale.append("%s scale=%s" % [m.name, _v3(s)])
	print("PROBE hidden-nodes(visible=false): n=%d %s" % [hidden.size(), str(hidden)])
	print("PROBE null-mesh: n=%d %s" % [null_mesh.size(), str(null_mesh)])
	print("PROBE zero-surface: n=%d %s" % [zero_surf.size(), str(zero_surf)])
	print("PROBE zero-scale: n=%d %s" % [zero_scale.size(), str(zero_scale)])
	if not hidden.is_empty():
		_issues.append("有 %d 个节点 visible=false：%s" % [hidden.size(), str(hidden)])
	if not null_mesh.is_empty():
		_issues.append("有 %d 个 MeshInstance3D mesh 为空" % null_mesh.size())
	if not zero_surf.is_empty():
		_issues.append("有 %d 个 MeshInstance3D surface 数为 0" % zero_surf.size())

	# ---- desk / chair 分组 ----
	var desks: Array = []
	var chairs: Array = []
	for m in mis:
		var mi := m as MeshInstance3D
		if String(mi.name).begins_with("desk_"):
			desks.append(mi)
		elif String(mi.name).begins_with("chair_"):
			chairs.append(mi)
	print("PROBE desks=%d chairs=%d (GLB 真值各 48)" % [desks.size(), chairs.size()])

	# 逐项：desk_r1_c1（首桌）全量细节 + desk_r8_c6（GLB 首节点）对照
	var d1: MeshInstance3D = null
	var d8: MeshInstance3D = null
	var c1: MeshInstance3D = null
	for mi in desks:
		if mi.name == "desk_r1_c1":
			d1 = mi
		if mi.name == "desk_r8_c6":
			d8 = mi
	for mi in chairs:
		if mi.name == "chair_r1_c1":
			c1 = mi
	if d1 != null:
		print("PROBE --- desk_r1_c1 全量 ---")
		print(_mi_report(d1, true))
	else:
		print("PROBE-ERROR: desk_r1_c1 未找到")
		_issues.append("desk_r1_c1 未找到")
	if d8 != null:
		print("PROBE --- desk_r8_c6 全量 ---")
		print(_mi_report(d8, true))
	if c1 != null:
		print("PROBE --- chair_r1_c1 全量（对照组） ---")
		print(_mi_report(c1, true))
	else:
		print("PROBE-ERROR: chair_r1_c1 未找到")
		_issues.append("chair_r1_c1 未找到")

	# ---- 48 桌聚合：surface 数 / 材质 / 腿面 AABB ----
	var desk_surf2 := 0
	var desk_leg_ok := 0
	var desk_leg_y_min := 1e9
	var desk_leg_y_max := -1e9
	var desk_mesh_ids := {}
	var desk_leg_mat_ids := {}
	var desk_wood_mat_ids := {}
	var desk_gpos_min := Vector3(1e9, 1e9, 1e9)
	var desk_gpos_max := Vector3(-1e9, -1e9, -1e9)
	for mi in desks:
		var mesh := mi.mesh as ArrayMesh
		if mesh == null:
			continue
		desk_mesh_ids[mesh.get_instance_id()] = true
		desk_gpos_min = desk_gpos_min.min(mi.global_transform.origin)
		desk_gpos_max = desk_gpos_max.max(mi.global_transform.origin)
		if mesh.get_surface_count() == 2:
			desk_surf2 += 1
		for s in range(mesh.get_surface_count()):
			var smat := mesh.surface_get_material(s) as StandardMaterial3D
			if smat == null:
				continue
			if smat.resource_name == "leg_metal":
				desk_leg_mat_ids[smat.get_instance_id()] = true
				var ga: AABB = mi.global_transform * _surf_aabb(mesh, s)
				desk_leg_y_min = minf(desk_leg_y_min, ga.position.y)
				desk_leg_y_max = maxf(desk_leg_y_max, ga.end.y)
				desk_leg_ok += 1
			elif smat.resource_name == "desk_wood":
				desk_wood_mat_ids[smat.get_instance_id()] = true
	print("PROBE desks-agg: surf==2 的桌数=%d/48 leg_metal 面总数=%d（真值 48） wood 面材质实例=%d 个 leg 材质实例=%d 个 共享 mesh 实例=%d 个" % [
		desk_surf2, desk_leg_ok, desk_wood_mat_ids.size(), desk_leg_mat_ids.size(), desk_mesh_ids.size()])
	print("PROBE desks-agg: leg 全局 AABB y[%.3f, %.3f]（真值 [0, 0.67]） desk 全局位置 x[%.2f, %.2f] z[%.2f, %.2f]（真值 x[-3.18,3.82] z[-2.80,2.80]）" % [
		desk_leg_y_min, desk_leg_y_max, desk_gpos_min.x, desk_gpos_max.x, desk_gpos_min.z, desk_gpos_max.z])
	if desk_surf2 != 48:
		_issues.append("desk surface==2 的只有 %d/48" % desk_surf2)
	if desk_leg_ok != 48:
		_issues.append("leg_metal 面只有 %d/48" % desk_leg_ok)
	if desk_mesh_ids.size() != 1:
		_issues.append("desk 共享 mesh 实例数=%d（真值 1）" % desk_mesh_ids.size())
	if absf(desk_leg_y_min) > 0.01 or absf(desk_leg_y_max - 0.67) > 0.01:
		_issues.append("desk leg 全局 AABB y[%.3f, %.3f] 与真值 [0, 0.67] 不符" % [desk_leg_y_min, desk_leg_y_max])

	var chair_surf2 := 0
	var chair_leg_ok := 0
	var chair_leg_y_min := 1e9
	var chair_leg_y_max := -1e9
	var chair_mesh_ids := {}
	var chair_leg_mat_ids := {}
	for mi in chairs:
		var mesh := mi.mesh as ArrayMesh
		if mesh == null:
			continue
		chair_mesh_ids[mesh.get_instance_id()] = true
		if mesh.get_surface_count() == 2:
			chair_surf2 += 1
		for s in range(mesh.get_surface_count()):
			var smat := mesh.surface_get_material(s) as StandardMaterial3D
			if smat == null:
				continue
			if smat.resource_name == "leg_metal":
				chair_leg_mat_ids[smat.get_instance_id()] = true
				var ga: AABB = mi.global_transform * _surf_aabb(mesh, s)
				chair_leg_y_min = minf(chair_leg_y_min, ga.position.y)
				chair_leg_y_max = maxf(chair_leg_y_max, ga.end.y)
				chair_leg_ok += 1
	print("PROBE chairs-agg: surf==2 的椅数=%d/48 leg_metal 面总数=%d（真值 48） leg 材质实例=%d 个 共享 mesh 实例=%d 个 leg 全局 AABB y[%.3f, %.3f]（真值 [0, 0.882]）" % [
		chair_surf2, chair_leg_ok, chair_leg_mat_ids.size(), chair_mesh_ids.size(), chair_leg_y_min, chair_leg_y_max])
	# 桌腿与椅腿是否同一材质实例
	var same_leg_mat := false
	for k in desk_leg_mat_ids.keys():
		if chair_leg_mat_ids.has(k):
			same_leg_mat = true
	print("PROBE leg-material-identity: desk-leg 与 chair-leg 同一材质实例=%s（desk %d 个 / chair %d 个实例）" % [
		str(same_leg_mat), desk_leg_mat_ids.size(), chair_leg_mat_ids.size()])
	if not same_leg_mat:
		_issues.append("桌腿与椅腿不是同一 leg_metal 材质实例（需逐项比对参数）")

	# ---- 共享网格几何深查（只查一份，48 套共享同一 mesh）：退化三角 + 法线 ----
	if d1 != null and c1 != null:
		var dm := d1.mesh as ArrayMesh
		var cm := c1.mesh as ArrayMesh
		for s in range(dm.get_surface_count()):
			var smat := dm.surface_get_material(s) as StandardMaterial3D
			var nm := smat.resource_name if smat != null else "?"
			var dg: Array = _degenerate_frac(dm, s)
			var ns: Array = _normal_stats(dm, s)
			print("PROBE desk-mesh surf%d(%s): 退化三角 %d/%d (%.4f) 零长法线 %d/%d 平均模长 %.3f" % [
				s, nm, dg[0], dg[1], dg[2], ns[0], ns[1], ns[2]])
			if dg[2] > 0.01:
				_issues.append("desk surf%d(%s) 退化三角比例 %.4f" % [s, nm, dg[2]])
			if ns[0] > 0:
				_issues.append("desk surf%d(%s) 零长法线 %d 条" % [s, nm, ns[0]])
		for s in range(cm.get_surface_count()):
			var smat2 := cm.surface_get_material(s) as StandardMaterial3D
			var nm2 := smat2.resource_name if smat2 != null else "?"
			var dg2: Array = _degenerate_frac(cm, s)
			var ns2: Array = _normal_stats(cm, s)
			print("PROBE chair-mesh surf%d(%s): 退化三角 %d/%d (%.4f) 零长法线 %d/%d 平均模长 %.3f" % [
				s, nm2, dg2[0], dg2[1], dg2[2], ns2[0], ns2[1], ns2[2]])

	# ---- desk_r1_c1 祖先链可见性 ----
	if d1 != null:
		var chain: Array[String] = []
		var cur: Node = d1
		while cur != null:
			if cur is Node3D:
				chain.append("%s visible=%s" % [cur.name, str((cur as Node3D).visible)])
			else:
				chain.append("%s (non-3D)" % cur.name)
			cur = cur.get_parent()
		print("PROBE ancestor-chain desk_r1_c1: %s" % " <- ".join(chain))

	# ---- 汇总 ----
	if _issues.is_empty():
		print("PROBE-SUMMARY: 导入/变换/可见性/材质/几何五层全部与 GLB 真值一致，无异常")
	else:
		print("PROBE-SUMMARY: 发现 %d 项异常：" % _issues.size())
		for it in _issues:
			print("PROBE-ISSUE: " + it)
	print("PROBE-DONE")
	quit(0)
	return true
