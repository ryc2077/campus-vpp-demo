extends SceneTree
## 原生截图：绕开 Chrome/wasm，直接用 Godot 渲染器出图。
## 用法（需 X 显示，机器负载高时用 xvfb-run）：
##   xvfb-run -a godot --path . -s tools/capture.gd -- <out.png> [wait_frames] [scene]
##   out.png 默认 screenshots/capture.png；wait_frames 默认 150（约 2.5s，飞行 1s 落位后标签已复算多轮）
##   scene 可选 overview/pv/storage/classroom/charge/dist（缺省 overview；切场景需等飞行 1s，wait_frames 建议 ≥180）
## 注意：主场景在 web 下读 URL 参数（?shot=1 等），原生下 JavaScriptBridge 不存在，
## _apply_url_params 会跳过，所以这里直接调 main 的公开方法切场景（若存在）或只拍总览。

var _out := "screenshots/capture.png"
var _wait_frames := 150
var _scene := "overview"
var _frames := 0
var _main: Node = null
var _switched := false


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() > 0:
		_out = String(args[0])
	if args.size() > 1:
		_wait_frames = int(args[1])
	if args.size() > 2:
		_scene = String(args[2])
	var packed := load("res://scenes/main.tscn") as PackedScene
	_main = packed.instantiate()
	root.add_child(_main)
	print("CAPTURE: scene=", _scene, " wait_frames=", _wait_frames, " out=", _out)


func _process(_delta: float) -> bool:
	_frames += 1
	# 第 10 帧切到目标场景（若不是总览），让飞行有时间跑完
	if not _switched and _scene != "overview" and _frames >= 10:
		_switched = true
		if _main.has_method("enter_scene"):
			_main.call("enter_scene", _scene)
		else:
			print("CAPTURE: no enter_scene method on main, staying on overview")
	if _frames >= _wait_frames:
		# 再等两帧确保本帧已渲染完
		await process_frame
		await process_frame
		var tex := root.get_texture()
		if tex == null:
			print("CAPTURE-FAIL: root texture is null")
			quit(1)
			return true
		var img := tex.get_image()
		if img == null:
			print("CAPTURE-FAIL: get_image returned null")
			quit(1)
			return true
		var err := img.save_png(_out)
		if err != OK:
			print("CAPTURE-FAIL: save_png err=", err)
			quit(1)
			return true
		print("CAPTURED: ", _out, " size=", img.get_size())
		quit(0)
		return true
	return false
