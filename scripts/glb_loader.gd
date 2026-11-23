class_name GlbLoader
extends RefCounted
## 场景 .glb 集中加载：成功返回实例化的 Node3D，失败返回 null 并打印明确警告，
## 调用方负责回退到程序化模型（缺 GLB 也不能让整个场景起不来）。
## 路径集中在 SCENES，加载结果记在 _results（供 pv_detail 等查询回退状态）。
## 坐标口径（BLENDER_MODELS.md §1）：Blender (x,y,z)=Godot (x,-z,y)，
## glTF 默认 +Y up 导出后导入即正确，实例一律放原点、不移位置、不旋转。
## 全局坐标场景（overview/storage/pv/charge）挂 Campus（原点）；
## 局部坐标场景（classroom/dist）挂各自内景节点原点。

const SCENES := {
	"overview": "res://assets/models/scenes/overview.glb",
	"pv": "res://assets/models/scenes/pv.glb",
	"storage": "res://assets/models/scenes/storage.glb",
	"classroom": "res://assets/models/scenes/classroom.glb",
	"charge": "res://assets/models/scenes/charge.glb",
	"dist": "res://assets/models/scenes/dist.glb",
}

static var _results: Dictionary = {} # path -> bool（是否加载成功）
## 回退演练开关：为真时 load_glb 一律返回 null（调用方走程序化回退），
## 不读磁盘、不改名 GLB。由 main.gd 在 campus.build() 之前按 URL 参数
## ?fallback=1 置起（web 截图用）；无头验证可直接赋值演练。
## 正常截图不传该参数，开关默认关，GLB 正常加载。
static var force_fallback := false

static func load_glb(path: String) -> Node3D:
	if force_fallback:
		_results[path] = false
		push_warning("[GlbLoader] 回退演练：force_fallback 开，跳过 %s，调用方将回退到程序化模型" % path)
		return null
	var packed := ResourceLoader.load(path, "PackedScene") as PackedScene
	if packed == null:
		_results[path] = false
		push_warning("[GlbLoader] 加载失败：%s 未能载入（文件缺失或导入失败），调用方将回退到程序化模型" % path)
		return null
	var inst := packed.instantiate() as Node3D
	if inst == null:
		_results[path] = false
		push_warning("[GlbLoader] 实例化失败：%s 根节点不是 Node3D，调用方将回退到程序化模型" % path)
		return null
	_results[path] = true
	return inst

## 加载并作为子节点挂到 parent 原点（不移位置、不旋转）；失败返回 null。
static func attach(parent: Node, key: String, node_name: String) -> Node3D:
	var inst := load_glb(SCENES[key])
	if inst == null:
		return null
	inst.name = node_name
	inst.position = Vector3.ZERO
	inst.rotation = Vector3.ZERO
	parent.add_child(inst)
	return inst

## 查询某场景 GLB 是否已加载成功（key 或完整路径均可；从未尝试过返回 false，
## 调用方按“未加载成功”走程序化回退）。
static func was_loaded(key_or_path: String) -> bool:
	var path: String = SCENES.get(key_or_path, key_or_path)
	return bool(_results.get(path, false))
