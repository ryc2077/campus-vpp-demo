"""把 ov-trees 的 ColorRamp 烘进 sRGB 贴图（glTF 无法表示 ColorRamp，
之前直接导出灰色噪波当 baseColor，Godot 里树冠呈灰白）。
噪波 t(0..1) -> 三档线性插值 -> 线性 RGB -> sRGB 存 PNG。
与 ov-trees.py 的节点停靠点逐字一致（dark 0.0 / mid 0.5 / light 1.0）。"""
import numpy as np
from PIL import Image
import os
BASE = os.path.expanduser("~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot")
TEX = os.path.join(BASE, "assets/blender/overview/ov-trees_textures")

def srgb_to_linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def hex_to_linear(h):
    h = h.lstrip("#")
    return tuple(srgb_to_linear(int(h[i:i+2], 16)) for i in (0, 2, 4))

def linear_to_srgb(a):
    a = np.clip(a, 0.0, 1.0)
    return np.where(a <= 0.0031308, a * 12.92, 1.055 * np.power(a, 1.0/2.4) - 0.055)

def bake(noise_file, out_name, dark, mid, light):
    t = np.asarray(Image.open(os.path.join(TEX, noise_file)).convert("L"), dtype=np.float64) / 255.0
    rgb_lin = np.zeros((*t.shape, 3))
    for ch in range(3):
        stops = [hex_to_linear(dark)[ch], hex_to_linear(mid)[ch], hex_to_linear(light)[ch]]
        rgb_lin[:, :, ch] = np.interp(t, [0.0, 0.5, 1.0], stops)
    out = (linear_to_srgb(rgb_lin) * 255.0 + 0.5).astype(np.uint8)
    p = os.path.join(TEX, out_name)
    Image.fromarray(out, "RGB").save(p)
    m = out.reshape(-1, 3).mean(axis=0)
    print(f"{out_name}: mean=({m[0]:.1f},{m[1]:.1f},{m[2]:.1f}) #%02X%02X%02X" % tuple(int(round(v)) for v in m))
    return p

jobs = [
    ("LeafNoise.png", "Crown_Perimeter_color.png", "#2F6B2A", "#4E8A3F", "#6FA84E"),
    ("LeafNoise.png", "Crown_Perimeter_Light_color.png", "#3A7A33", "#5C9A48", "#82B85E"),
    ("LeafNoise.png", "Crown_Roadside_color.png", "#3F7A32", "#5C9A44", "#8AB85C"),
    ("LeafNoise.png", "Crown_Roadside_Light_color.png", "#4A8540", "#6FAA50", "#9CC46A"),
    ("LeafNoise.png", "Crown_Scattered_color.png", "#557F35", "#7AA84A", "#A8C46A"),
    ("LeafNoise.png", "Crown_Scattered_Light_color.png", "#648C40", "#8AB85A", "#B8D47A"),
    ("BarkNoise.png", "Trunk_Bark_color.png", "#4A2F1C", "#6B4E2E", "#8A6B4A"),
]
for j in jobs:
    bake(*j)
print("DONE bake")
