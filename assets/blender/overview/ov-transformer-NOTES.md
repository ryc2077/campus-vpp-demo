# ov-transformer — 户外变压器组（补件记录，2026-11-23）

> 协调人合并用：本件补 BLENDER_MODELS.md §6 缺口表里户外变压器组那行；
> 不要动 `assets/blender/scenes/overview.py`，拼装时由协调人统一把本件拼进总览。

## 来源

- Godot 程序化对应：`scripts/campus_builder.gd` `_build_transformer`（Godot [74,-30]）
- 尺寸与程序化一致：基座 6.5×4.5×0.4m、箱体 5.6×3.4×3.6m、绝缘子 3 根（r 0.28/0.35、高 1.2m）
- 位置：Blender 全局中心 (74, 30)（Godot (x, -z) 换算）

## 内容（58 个对象）

| 部分 | 对象 | 尺寸/位置 |
|---|---|---|
| 基座 TF_Base | 1 | 6.5×4.5×0.4m，z 0~0.4，混凝土 #B9B3A8 |
| 箱体 TF_Body | 1 | 5.6×3.4×3.6m，z 0.4~4.0，灰绿 #6B7B72 |
| 顶盖 TF_Lid | 1 | 5.66×3.46×0.08m，z 4.0~4.08 |
| 散热片 TF_Fin_S/N 1–9 | 18 | 南北两侧各 9 片，0.06×0.35×2.6m，z 0.7~3.3，深灰 #424A52 |
| 绝缘子 TF_Bushing 1–3 | 15 | 每根：主柱 r0.28 高 1.2m（z 4.08~5.28）+ 3 层伞裙盘 r0.40 + 顶部金属端子；x = -1.8/0/+1.8（相对中心），陶瓷色 #D9D4C7 |
| 接线盒 TF_JunctionBox | 1 | 0.3×0.5×0.8m，箱体东面 |
| 围栏 TF_FencePost 01–12 + 横杆 8 | 20 | 7.5×5.5m 周边，立柱高 1.2m，上下两道横杆（z 0.6/1.1），金属灰 #8A8F94 |
| 警示牌 TF_WarningPlate | 1 | 0.6×0.02×0.4m，南侧围栏中部，警示黄 #E8B400 |
| 总高 | — | 绝缘子端子顶 z = 5.43m |

## 材质（7 种，全部纯色 Base Color，sRGB→线性转换后赋值）

| 材质 | 颜色 | baseColorFactor（线性，GLB JSON 实测） |
|---|---|---|
| Transformer_Body | #6B7B72 | [0.147, 0.198, 0.168, 1] |
| Transformer_Fin | #424A52 | [0.054, 0.068, 0.084, 1] |
| Transformer_Base | #B9B3A8 | [0.485, 0.451, 0.392, 1] |
| Transformer_Bushing | #D9D4C7 | [0.694, 0.658, 0.571, 1] |
| Transformer_Terminal | #8A8F94 | [0.254, 0.275, 0.296, 1] |
| Transformer_Fence | #8A8F94 | [0.254, 0.275, 0.296, 1] |
| Transformer_Warning | #E8B400 | [0.807, 0.456, 0, 1] |

无程序化节点连进 Base Color；无贴图（纯色件，Bump-only 同类件惯例不适用）。

## 验证（2026-11-23 14:14 CST）

- Blender 4.2.0 一次运行建模 + 存 .blend + 导出 .glb + 回读，日志零 Error/Traceback，`DONE ov-transformer`
- `bpy.ops.import_scene.gltf` 回读：58 个对象，与建模数一致
- 直读 GLB JSON：58 meshes / 58 nodes / 7 materials，7 种材质全部含 baseColorFactor，无 baseColorTexture
- 文件：`ov-transformer.py` 10,145 B、`ov-transformer.blend` 923,440 B、`ov-transformer.glb` 173,036 B
- 本地未渲染（按任务要求，渲染走 GitHub Actions）；脚本内已按 SPEC §2 架好太阳光/世界背景/东南侧 45° 俯视相机，置 `OV_TRANSFORMER_RENDER=1` 可本地出图

## 与 di-transformer 的区别

di-transformer 是配电房**室内** 4 台主变（局部坐标、单台 2.5×1.5×2.6m），本件是总览**户外**单组（全局坐标 (74,30)、5.6×3.4×3.6m 箱 + 3 根绝缘子 + 围栏），不可互相顶替。
