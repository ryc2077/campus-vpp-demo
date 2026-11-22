class_name DataLoader
extends RefCounted
## JSON 数据加载：所有权威数字只存在 data/*.json，代码只读不写死。

static func load_json(path: String) -> Dictionary:
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		push_error("DataLoader: cannot open " + path)
		return {}
	var text := f.get_as_text()
	var parsed: Variant = JSON.parse_string(text)
	if parsed == null or not (parsed is Dictionary):
		push_error("DataLoader: bad JSON in " + path)
		return {}
	return parsed

static func color_from_hex(hex: String) -> Color:
	var c := Color.html(hex)
	return c
