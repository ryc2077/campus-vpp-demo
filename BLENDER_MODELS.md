# BLENDER_MODELS.md — Blender 模型接线说明（校园虚拟电厂 Demo）

> 状态：拼装收尾进行中。单件 44 件已交付（43 件 + ov-transformer 补件；2026-11-22 18:11 前完成，窗带修复 5 件已验收入库）；总览场景 13,036 对象（见 §4/§10）；6 场景拼装、纹理烘焙、6 个待定口径正在并行处理，截止 2026-11-23 18:11。
> 本文件边做边写；每节标注状态（已完成 / 进行中 / 待核对）。不要把“进行中”读成“已完成”。
> 工程根目录：`~/workspace/goals/campus-virtual-power-plant-competition/files/demo-godot/`
> 公开仓库：`https://github.com/ryc2077/campus-vpp-demo`（渲染全部走 GitHub Actions，本地不渲染）

## 1. 坐标系与单位

- 单位：米。Blender 坐标：x 向东、y 向北、z 向上。Godot 坐标：x 向东、y 向上、z 向南。
- 换算：**Blender (x, y, z) = Godot (x, -z, y)**，原点同为校园原点。
- 单件建模全部用全局坐标，只有教室、配电房两板块用局部坐标（见 §3 备注）。
- glTF 导出：`export_format='GLB'`、`use_selection=True`、`export_apply=True`，默认 +Y up，不要手动旋转。按此导出后，GLB 导入 Godot 时位置即正确，不用再移位置、不用再旋转。
- 颜色：Principled BSDF 的 Base Color 必须先做 sRGB→线性转换再赋值，直接赋 sRGB 十六进制值会被洗白（已踩过坑，ov-bldA 第一版屋顶洗成浅灰蓝）。

## 2. 文件布局

| 内容 | 位置 |
|---|---|
| 单件脚本（可复现全部建模） | `assets/blender/<板块>/<件ID>.py` |
| 单件工程 | `assets/blender/<板块>/<件ID>.blend` |
| 单件导出 | `assets/models/<件ID>.glb` |
| 场景拼装脚本 | `assets/blender/scenes/<场景>.py` |
| 场景工程 | `assets/blender/scenes/<场景>.blend` |
| 场景合并导出 | `assets/models/scenes/<场景>.glb` |
| 规约（坐标/配色/位置总表） | `assets/blender/SPEC.md` |
| 单件预览图（旧，本地渲染；新图走 Actions） | `screenshots/blender/<件ID>.png` |

单件共 44 件：总览 20（含 ov-transformer 补件）、光伏 4、储能 5、教室 6、充电 4、配电 5。

## 3. 单件 → Godot 程序化模型对照表

说明：“Godot 对应”指明天整合时要被替换掉的程序化代码位置（`scripts/campus_builder.gd` 为总览程序化搭建，`scripts/*_interior.gd` / `*_detail.gd` 为各内景程序化搭建）。标“新增细节”的是 Blender 多做的、Godot 程序化版里没有的东西，整合时直接新增，不用找对应物替换。

### 3.1 总览（全局坐标）

| 件 ID | 内容 | Godot 对应 | 场景 | 纹理管线 |
|---|---|---|---|---|
| ov-bldA | 一号教学楼楼体 40×15×19m，5 层 | `campus_builder._build_building(bldA)` 墙体量块 + 屋顶板 | overview | **烘焙完成**（2026-11-23 03:17 CST：24 张齐全，新增 10/复用 14，8/9 全套；回读 222。首跑 23/24 张时遇重启被杀，续跑只烘 1 张） |
| ov-bldB | 二号教学楼楼体 32×14×19m，5 层 | `_build_building(bldB)` | overview | **烘焙完成**（2026-11-23 04:24 CST：27 张，9/9 全套，bake 3957.4s；回读 180） |
| ov-bldC | 三号教学楼楼体 22×13×14m，4 层 | `_build_building(bldC)` | overview | **楼高已修正并烘焙**（2026-11-23 03:36 CST：旧件实测总高 20.02m，根因是 v2 脚本从 ov-bldA（5F/19m）照抄后未按 4F/14m 缩放、每层 4.4m，注释称“19m 包络是因光伏屋顶在 z=19 对接”是误读 SPEC §6——那个 z=19 是 A 栋屋顶机位；已改回墙体 F1–F3 0.5–10.0、F4 10.0–13.0、檐口 4.0/7.0/10.0/13.0（F5 檐口更名为 cornice_roof，4 层楼不再有 F5 对象）、屋顶板 13.0–13.25、女儿墙 13.25–13.90、压顶顶面恰好 14.00m，空调中心 1.5/5.0/8.0/11.0；平面 22×13 与浅橙墙色不动。重出 .blend 1,992,496 B、.glb 3,731,892 B，回读 136 个对象，9 种材质各含 color/rough/normal 3 张烘焙图（27 张，耗时 1657.9s），DONE ov-bldC。烘焙亦完成（2026-11-23 04:24 CST：27 张复用、9/9 全套，回读 136；A 组续跑任务复用并行另一工人先烘好的贴图只重出，未并发写同一文件）。GLB 总高 14.92m——其中 14.00m 是楼体包络，多出 0.92m 是屋顶设备盖，与 A 件同例（A 包络 19.0m、设备盖至 20.02m），SPEC 表格高度指包络。首跑在 19:04 遇运行时重启被杀后用同一修正脚本重跑成功） |
| ov-windows-roofs | A/B/C 三栋窗户与屋顶细部（横向窗带、女儿墙压顶、屋顶设备小盒） | `_build_building` 里的窗户带（南立面每层一排亮窗贴片）+ 屋顶板 | overview | **窗带修复已核验通过**（2026-11-23 01:18 CST：GLB 回读 127 个对象，112 窗 + 15 屋顶；56 条玻璃逐条实测，S/N = 楼面长−2、E/W = 楼面宽−2，最大悬空量 0；旧 .blend1 实测证实旧 bug 确实对调。烘焙：贴图 18 张已齐，待 A 组续跑任务重出 .blend/.glb） |烘焙亦完成（2026-11-23 05:39 CST：18 张复用只重出，6/7 全套，回读 127）。
| ov-lib | 图书馆 24×16×22m，6 层 | `_build_building(lib)` | overview | **烘焙完成**（2026-11-23 05:39 CST：39 张，新增 15/复用 24，13/15 全套，bake 1998.0s；回读 289。24/39 张时遇重启被杀，续跑只烘 15 张） |
| ov-gym | 艺体馆 36×16×18m，3 层 | `_build_building(gym)` | overview | **烘焙完成**（2026-11-23 01:58 CST：18 张，6/6 全套；.glb 已重出，回读 192） **换装 R2-T21b**（2026-11-25，见 §21）：入口雨棚换成 tevy 医院楼偷件雨棚，烘焙改 PBR 直挂；回读 181，零 Error/Traceback |
| ov-lab | 实验楼 42×12×13m，3 层 | `_build_building(lab)` | overview | **烘焙完成**（2026-11-23 04:59 CST：36 张，12/12 全套；.glb 已重出，回读 358） **换装 R2-T21b**（2026-11-25，见 §21）：长面窗带换成 Grab3D 发电厂偷件窗行改长，烘焙改 PBR 直挂；回读 286，零 Error/Traceback |
| ov-tower | 创造力中心 14×14×32m，8 层（窗带已修复：79 段，666 个窗带对象） | `_build_building(tower)` | overview | **烘焙完成**（2026-11-23 07:50 CST：42 张，14/14 全套；.glb 已重出，回读 929） |
| ov-canteen | 餐厅 32×13×15m，3 层 | `_build_building(canteen)` | overview | **烘焙完成**（2026-11-23 08:44 CST：33 张，11/11 全套；.glb 已重出，回读 322） **换装 R2-T21b**（2026-11-25，见 §21）：正门换成 Grab3D 博物馆偷件柱廊 + 食堂房间偷件取餐台，烘焙改 PBR 直挂；回读 321，零 Error/Traceback |
| ov-dorm | 宿舍 A、B 两栋，各 20×12×16m，5 层（总高 16.40m，见 §5.5） | `_build_building(dormA)` + `_build_building(dormB)` | overview | **烘焙完成**（2026-11-23 11:14 CST：45 张，15/15 全套；.glb 已重出，回读 739） |
| ov-road-main | 主干道（环校主路 + 东侧、南侧主路，沥青 + 黄色中心线 + 路缘石） | `_build_roads` | overview | **烘焙完成**（2026-11-23 00:20 CST：Asphalt/YellowLine/Curb 各 3 张，61 分钟；回读 33/33。**已返工 UV 分瓦片**（2026-11-23 04:13 CST：照抄 road-walk/track 的 `_pack_uvs`，Asphalt 10 对象→4×3 瓦片、YellowLine 2→2×1、Curb 21→5×5，烘焙 384.2s、全程约 6 分 49 秒；新 .glb 802,176 B、回读 33、3 材质各 3 张贴图齐全）。**已修沥青纯色+补环路中心线**（2026-11-23 06:59 CST：根因是 DIFFUSE 烘焙只取 Base Color、管线为保 glTF baseColorFactor 刻意不链接底色，color 图只能是平底色（唯一色 70、非黑区标准差仅 1.96），颗粒只走 Bump 但法线图也几乎是平的；材质链接本身没问题。修法：烘焙前把颗粒/磨损以 MixRGB 乘进 Base Color（重建时会删节点只连烘焙贴图，glTF 不受影响），Bump 加强 0.4→0.9、distance 0.08→0.20；第二轮重烘顶面标准差 1.8→4.1~4.4、Asphalt 唯一色 70→337、Curb 140→882、黄线 9→187、法线 R/G 标准差 1→9.04/8.61。环路中心线原为 0 个对象（.py 旧设计称“按鸟瞰图不画黄线”，但内环路基本被楼体遮挡、说法站不住），按 SPEC §5 补 8 个对象（4 直段＋4 拐角斜段）。对象 33→41，回读 41，DONE ov-road-main） **返工 R2-T14b（2026-11-24）**：环校路内缘路缘石在 5 处新路口断开（R-N1 两端 y 42.5..45.5、R-N2 口 x -34.5..-31.5、R-N3 口 56.5..59.5、R-N4 spur 口 66.7..69.3、R-N4 东接口 y -70..-68），内缘 S/W/E 由 3 条整段改为 4+2+3 段分段；.blend 实测断口与新步道口同宽（S_0..S_3、W_0..W_1、E_0..E_2 位置尺寸均与设计一致）。重建：烘焙 9/9（384.3s），回读 47/47（.blend 另含预览地面/太阳/相机 3 件，共 50 对象），3 材质 base/rough/normal 齐全、9 张贴图具名；.glb 7,181,756 B；Curb 烘焙图 3 张更新。本件 .py 同补 R2-T14b PBR 路径修正（见 ov-road-walk 行）。 **品红修复跟进（2026-11-24，R2-T14b）**：run 45440253728 目视本件全路品红（5.8%）；根因已查实：仓库版 .blend 9 张图全未打包（packed: False，尺寸 0×0），且 PBR 源文件（pbr-tinted/* 等）不在仓库，runner 检出后找不到文件；对照：打包版 bldA（16/16 打包）同批渲染正常，未打包但贴图文件在仓的 track/lawn 也正常。R2-T9b 18:56 已补打包 8 个 .blend（含本件）并推仓（commit 7eec73f8），仓库版 .blend 现与本地打包版 SHA 一致；本件 .py 另补存盘前打包步骤（与 ov-tower.py 同款），防下次重建复发。目视验证见 ov-road-walk 行（run 45464884225 全组 0.0% 品红）。 |
| ov-road-walk | 步道与铺装（南门广场浅色铺装、楼间步道、路缘） | `_build_roads` 铺装部分 | overview | **烘焙完成**（2026-11-23 03:35 CST：7 材质各 3 张，28 分钟；回读 149/149。UV 分瓦片后从 111 分钟被杀→28 分钟跑完） **返工 R2-T14b（2026-11-24，R2-T14 续跑）**：接半成品——前任已把 6 条新路（R-N1/R-N2/R-N3/R-N3x/R-N4/R-N5，约 438m）与路缘全部写进 .py，但 .blend/.glb 仍是 11-22 旧版（149 对象、0 条新路），重建被运行时重启中断。几何复核全过：R-N3 距配电房东墙 0.5m、储能围栏 0.5m/平台 1.0m（方案写的 0.2m 是另一口径，实测更宽松，无需改线）、R-N2 距操场缓冲 2.5m/bldA 东墙 1.5m、R-N1 距 tower 南墙 1.5m、R-N5 距 bldB/bldC 各 4m、R-N4 spur 在池塘+0.5m 椭圆外（最小归一化值 1.44）。重建：烘焙 24/24（首跑 1910.8s、复核重跑 648.9s）；首跑在回读断言失败——_pbr_apply 的 relpath 以 CWD 为基准，CWD=工程根时 PBR 贴图写成 //assets/...（应为 //../../assets/...），GLB 里 6 种 PBR 材质只剩 1 张空白图（已实测复现）；已在两件 .py 的 hook 后加路径修正（.blend 所在目录 + CWD 双候选解析、幂等），并用同逻辑修复已存 .blend 后重出 .glb；为验证 .py 自洽又全量重跑一遍，DONE，复核重跑出的 .glb 与修复版字节相同（sha256 ecefcfc6…）。回读 171/171（旧 149，+22 件新路对象），8 材质 base/rough/normal 齐全、15 张贴图具名；.glb 11,029,616 B；Curb 烘焙图 3 张更新、PavingNew 三件套 3 张新增。 **品红修复跟进（2026-11-24，R2-T14b）**：run 45440253728 目视本件全幅品红；根因同 ov-road-main 行：仓库版 .blend 15 张图全未打包，PBR 源文件不在仓库；R2-T9b 18:56 补打包并推仓（commit 7eec73f8），仓库版 .blend 现与本地打包版 SHA 一致；本件 .py 另补存盘前打包步骤（与 ov-tower.py 同款），防下次重建复发。验证：run 45464884225（head 7eec73f8，R2-T9b 补打包版）overview 组 completed success；20 张全量品红扫描 0.0%，逐张目视：ov-road-walk 浅色铺装+黄色触感线正常，R-N1 北横贯通、R-N2/R-N3 两纵、R-N5 中部连接、R-N4 池塘北岸弧均在位、无压线；ov-road-main 深色沥青+黄中心线正常，环路完整；附带修复：canteen/gym/lab/tower 同批品红一并消失（tower 目视：米色墙面、蓝窗、深灰屋顶均正常）。 |
| ov-track | 操场跑道（400m 椭圆，跑道红 + 白色分道线，中心 (-80,-25)，rx40 rz28） | `_build_playground` 跑道环 | overview | **烘焙完成**（2026-11-23 03:38 CST：Track_Red/LaneLine/Curb 各 3 张，约 2 分钟；回读 17/17） |
| ov-field | 球场与看台（跑道内侧条纹足球场、球门、简易看台） | `_build_playground` 场内 | overview | **烘焙完成**（2026-11-23 03:47 CST：深/浅草皮/白线/门框/看台各 3 张，约 4 分钟；回读 30/30。半透明球网按设计跳过） |
| ov-trees | 树木（校园周边密植树带 + 东侧路旁行道树） | `_build_trees` | overview | Bump-only（小件保底） |
| ov-lawn | 草坪花坛（大面积草地、门前花坛、灌木球；v3 加密版草） | `_build_ground` 草地部分 | overview | **烘焙完成**（2026-11-23 04:04 CST：Lawn_Green/边框/土面/3 色花/灌木各 3 张，16 分钟；回读 129/129，111,917 tris。6 种草叶程序化保留；烘焙范围含花坛边框等，见 §5.1 待确认项） |
| ov-flag-lamp | 旗杆路灯（南门广场 3 根旗杆、沿路路灯杆） | `_build_flag_and_gate` | overview | Bump-only |
| ov-gate | 校门（南门门楼 + 门柱 + 伸缩门示意 + 围墙一段） | `_build_flag_and_gate` | overview | Bump-only |
| ov-parking | 停车区（南门广场旁停车位划线 + 3 辆简易小车） | Godot 无对应程序化模型（新增细节） | overview | **PBR 已挂**（Paint* 三件套）+ **返工 R1**（2026-11-24，验收 run #72：本件车漆从未挂清漆，GLB 实测无 KHR_materials_clearcoat——060877f4 只给 ch-cars 挂了；make_car 挂图后补 Coat Weight 1.0 / Coat Roughness 0.05，车窗加细噪波 Bump、粗糙度 0.06→0.05；回读 233，零 Error/Traceback）**返工 R2**（2026-11-24：与 ch-cars 同因同修，.blend 留 Nishita 天空世界；回读 233，零 Error/Traceback）**返工 R3**（2026-11-24：与 ch-cars 同根因同修（见 §9），预览环境加暗色地面 Ground_PreviewOnly + 东南太阳 + 西北 24×2m 亮条灯（15000）；本地验证三车顶均有亮度起伏；GLB blob 与仓库相同未推。回读 236，零 Error/Traceback）**车窗玻璃修补**（2026-11-24，commit `77dc9b9d`：与 ch-cars 同配方，alpha 0.65→0.90、粗糙度→0.15、specular 1.0、深色 #33505F tint；删 Glass-BSDF mix + 玻璃 Bump；本任务重拼 overview 场景 GLB，GLB JSON 实测 alpha 0.90、车漆清漆 1.0/0.05） **换装 R2-T19**（2026-11-24：3 辆手捏小车换成 Quaternius 网上车——灰 SUV/蓝 Car/红 Sports 2；长 4.4 m、宽 1.80 m，灰 SUV 前轮离轮挡 0.06 m、中心南移 0.10 m；车漆清漆 1.0/0.05、车窗透射 0.10/alpha 0.90；回读 50，零 Error/Traceback；ov-parking.glb 3,367,900 B / .blend 2,446,596 B，见 §19） |
| ov-transformer | 户外变压器组（Blender 中心 (74,30)：基座 6.5×4.5×0.4m + 箱体 5.6×3.4×3.6m + 散热片南北各 9 片共 18 片 + 绝缘子 3 根 + 围栏 12 立柱 + 南侧警示黄牌；58 个对象，commit `7228f6b`） | `_build_transformer` | overview | 纯程序化（7 种材质全含 baseColorFactor，无贴图；审计确认 0 贴图、0 带贴图节点材质，无纹理风险） |

### 3.2 光伏屋顶（全局坐标，机位 A 栋屋顶）

| 件 ID | 内容 | Godot 对应 | 场景 | 纹理管线 |
|---|---|---|---|---|
| pv-panels | 板阵列（标准板 1.134×1.762m，深蓝 + 银框，倾角约 15° 朝南） | `campus_builder._build_pv_array`（bldA/bldB/lab 屋顶） | pv | **PBR 已挂**（commit `060877f`：PV_FrameSilver #C0C5C9、PV_Busbar #7E93A8 用 blue_metal_plate 染色三件套；新增 frame/busbar color 图各 1 张，rough/nor 复用 panel_rough.jpg / panel_nor.jpg，见 §9 核实） |
| pv-mount | 支架边框（每排支架横梁、倾斜支腿、压块） | Godot 只有板阵列，无独立支架模型（新增细节） | pv | **PBR 已挂**（commit `060877f`：PV_RailSteel #B9BEC2、PV_LegSteel #6E7478 新建 pv-mount_textures/ 三件套各 3 张，rail/leg × color/nor/rough） |
| pv-inverter | 逆变器与线缆（屋顶逆变器箱 3 台、线槽、引下线缆） | `pv_detail.gd` 逆变器箱 + 屋顶逆变器（新增细节为主） | pv | Bump-only |
| pv-roof | 屋顶面层（女儿墙、灰色防水卷材面层、排水口、检修步道） | `_build_building` 屋顶板 + 女儿墙/防水层（新增细节） | pv | Bump-only |

### 3.3 储能站（全局坐标，Blender 中心 (64,30)）

| 件 ID | 内容 | Godot 对应 | 场景 | 纹理管线 |
|---|---|---|---|---|
| st-cabinet | 柜体（3 台电池柜 + 1 台 PCS 柜一字排开，单柜约 1.3×1.0×2.3m） | `campus_builder._build_storage` 柜体 + `storage_interior.gd` 柜体 | storage | **PBR 已挂**（commit `060877f`：Cabinet_Cap_Paint #35483F、Cabinet_Kick #2E3F38 新增 cap/kick color 图各 1 张，rough/nor 复用 cabinet_rough.jpg / cabinet_nor.jpg，见 §9 核实） |
| st-doors | 电池舱门与散热（每柜双开门、门把手、散热百叶、顶部风扇罩） | `storage_interior.gd` 舱门（Godot 只有柜体盒，无门细节；新增细节为主） | storage | Bump-only |
| st-cables | 线缆与接线箱（柜间线槽、接线箱、接地线、进线电缆沟） | `storage_interior.gd` 线缆（新增细节） | storage | Bump-only |
| st-base | 地面基座（混凝土基座平台 + 黄色警戒线） | `_build_storage` 基座 | storage | Bump-only |
| st-fence | 围栏标识（三面围栏 + “高压危险”标识牌） | Godot 无围栏（新增细节） | storage | **PBR 已挂**（返工 R1，2026-11-24，验收 run #72：围栏内 4 台柜与地面用的本件自建 Preview_* 纯色材质，与 st-cabinet 的锈蚀 PBR 根本不是同一材质；柜体复用 st-cabinet_textures 锈蚀三件套、地面复用 st-base_textures 混凝土三件套，地面 UV 按 2m 平铺 x15；无新素材。预览物不进 GLB、不进 storage 场景。回读 36，零 Error/Traceback）**返工 R2-T20（2026-11-24，见 §9）**：修 v1 立柱越界 bug——每段按段长均分布点（n=max(1,round(L/2))，t=i/n），立柱 17 根→13 根，包围盒回到 8.08×3.08m，4 根 stray 全清、门洞正中无立柱；新件 .blend 1,211,208 B / .glb 552,460 B，回读 36、零 Error/Traceback。 |

### 3.4 教室内部（局部坐标：房间中心原点，x=长 9.68m，y=宽 7.26m，z 0–3.0m；黑板墙 x=-4.84，窗户沿 y=-3.63，门在 x=+4.84 墙上）

| 件 ID | 内容 | Godot 对应 | 场景 | 纹理管线 |
|---|---|---|---|---|
| cl-floor-walls | 地面墙面（浅色地砖地面、四面墙、踢脚线、天花板） | `classroom_interior.gd._build` 地面/墙面/天花板 | classroom | Bump-only |
| cl-desks | 桌椅（6 列 × 8 排课桌椅，48 套，留讲台前空地与过道）— **R2-T17 已换成 3DAssets 课桌椅**（见 §18；tevy 拆件已彻底换掉） | `classroom_interior.gd` 桌椅 | classroom | Bump-only（3DAssets 两件 + 自家 CC0 染色贴图，见 cl-desks.py 头注） |
| cl-board | 讲台黑板（黑板墨绿 + 讲台桌 + 粉笔槽） | `classroom_interior.gd` 黑板 + 讲台 | classroom | Bump-only |
| cl-ac | 空调（2 台美的 5 匹柜机 KFR-120LW，白，约 0.6×0.4×1.8m） | `classroom_interior.gd` 空调 | classroom | Bump-only |
| cl-lights | 灯具（天花板 2 排日光灯管 + 吊杆） | `classroom_interior.gd` 灯具 | classroom | Bump-only |
| cl-windows | 窗户窗帘（南侧 4 扇大窗 + 浅色窗帘）+ **门（tevy 拆件，见本节下注）** | `classroom_interior.gd` 窗户 | classroom | Bump-only |

**tevy 教室换件已完成**（2026-11-23，commits `cf0d432`、`c2d99fa`、`e2bce23`、`5d0e1fc`、`c046118`）：桌椅换成 tevy 现成模型拆件（CC0，tevy.dev/models/classroom；原模型三重压缩 Blender 4.2 打不开，已用 gltf-transform 去压缩并剥掉 KTX2 贴图，见 `assets/external/buildings/tevy-decompress.mjs`）。桌：12 张双人桌 → 24 张单桌循环复用 48 套；椅：20 张单椅中 4 张被高柜面污染（柜面与椅背共面、y 只差 0.02–0.04m，切不干净）不进复用池，其余 16 张干净单椅循环复用 48 套。48 套间隙前 0.208m / 后 0.204m（commit `e2bce23`）。门装进 cl-windows.py（tevy 门 + 门框，commit `5d0e1fc`）。讲台桌 / 书架 / 高柜未采用：讲台桌进深 1.25m 是 SPEC 讲台 0.62m 的两倍，会吃掉讲台前空地并顶住第一排桌；书架（4.48m 长柜）无 SPEC 位置，放北墙会挡窗；高柜与椅背共面切不干净（见上）。classroom 场景 440 对象（原 436，+门 1 +填缝 3），见 §4。
**tevy 拆件已被 R2-T17 彻底换掉**（2026-11-24，见 §18）：桌椅改用 3DAssets Student Desk + Student Chair（CC0），tevy 拆件的碎面/高柜污染/悬浮平板问题随之消失；门仍是 tevy 门（在 cl-windows.py 里，未动）。

### 3.5 充电区 V2G（全局坐标，Blender 中心 (44,-76)）

| 件 ID | 内容 | Godot 对应 | 场景 | 纹理管线 |
|---|---|---|---|---|
| ch-piles | 充电桩（4 台直流桩一字排开，白 + 充电枪线） | `campus_builder._build_charge` 充电桩 + `charge_detail.gd` | charge | Bump-only |
| ch-cars | 车辆（3 辆简易小车，蓝/红/白，2 辆 V2G 在桩前） | `_build_charge` 车辆 + `charge_detail.gd` | charge | **PBR（参数化清漆）已挂**（commit `060877f`：3 台车共用参数化清漆，Metallic 0.15 / Roughness 0.35、Coat Weight 1.0 / Coat Roughness 0.15，GLB 带 KHR_materials_clearcoat；不贴平铺纹理）**返工 R1**（2026-11-24，验收 run #72：GLB 里 clearcoat 明明在，EEVEE 预览仍全哑光——根因是预览只有单太阳+纯色平坦世界，清漆层无物可映、涂层高光被底漆粗糙度冲淡；Godot 04-charge 远景也看不出光泽。Coat Roughness 0.15→0.05、底漆 Roughness 0.35→0.25，Godot 侧同向变亮；回读 198，零 Error/Traceback）**返工 R2**（2026-11-24：run 45251171902 新图与旧图逐像素几乎相同（平均差 0.02），涂层再锐也看不见——纯色平坦世界无物可映；.blend 改留 Nishita 天空世界（仰角 50°，render_max 对亮色世界原样保留），清漆映天空渐变+太阳盘；不进 GLB，Godot 不受影响。回读 198，零 Error/Traceback）**返工 R3**（2026-11-24：R2 仍全哑光，根因见 §9——天空不在画面内（相机俯角 28°、顶缘视线低于地平线 16°）、平板车身映均匀淡天、探针无用；修法只改预览环境：留 Nishita + 暗色地面 Ground_PreviewOnly + 东南太阳 + 西北 24×2m 亮条灯（15000），本地 320×180 验证蓝车顶现 184→209 渐变光带；GLB blob 与仓库相同未推。回读 201，零 Error/Traceback）**车窗玻璃修补**（2026-11-24，commit `77dc9b9d`：`make_glass` 统一配方，透射 0.9→0.10、粗糙度→0.15、specular 1.0、深色 #33505F tint；删 Glass-BSDF mix + 玻璃 Bump；本任务重拼 charge/overview 场景 GLB，GLB JSON 实测 transmission 0.10、车漆清漆 1.0/0.05） **换装 R2-T19**（2026-11-24：3 辆手捏小车换成 Quaternius 网上车——蓝 Car/红 Sports 2（橙改 SPEC 红 #C4534E）/白 SUV；均匀按长缩到 4.4 m，充电车位 2.5 m 宽均不压线；车漆清漆 1.0/0.05、车窗透射 0.10/alpha 0.90；车身主 mesh 改名 _roof 兼任 Godot SOC 条锚点（原点移到高度中点）；回读 15，零 Error/Traceback；ch-cars.glb 531,580 B / .blend 2,096,408 B，见 §19） |
| ch-marking | 车位线与标识（4 个车位白线、地面标识线框） | `_build_charge` 车位线（新增细节为主） | charge | Bump-only |
| ch-canopy | 雨棚（4 车位通长雨棚，钢柱 + 浅灰棚顶） | Godot 无雨棚（新增细节） | charge | Bump-only |

### 3.6 配电房（局部坐标：房中心原点，x=长 16m，y=宽 10m，z 0–8m；房外壳在总览 dist 建筑里，本板块只做室内）

| 件 ID | 内容 | Godot 对应 | 场景 | 纹理管线 |
|---|---|---|---|---|
| di-walls | 地面墙面（室内地面浅灰环氧、四面墙、踢脚线） | `dist_interior.gd._build` 地面/墙面 | dist | **已烘焙**（首件走通路线：color/rough/normal 三张贴图全在，margin=4px；见 §5.1）**返工 R1**（2026-11-24，验收 run #72：预览所见“屋顶”实为天花板顶面，纯白平板；墙面云纹过淡。顶面与墙面同级纹理：天花板混合强度 0.25→0.6、第二色加深 #D8D8D8→#C6C6C6、Bump 0.06→0.15；墙面斑驳 Ramp 收窄、污渍/水渍色加深、Bump 0.12→0.20；15 张烘焙图重出。回读 17，零 Error/Traceback） |
| di-cabinets | 配电柜（沿北墙一排开关柜 6 台，灰绿，带仪表小窗与把手） | `dist_interior.gd` 开关柜 | dist | Bump-only |
| di-transformer | 变压器（4 台主变一字排开，单台约 2.5×1.5×2.6m，局部坐标 x=-4.5/-1.5/1.5/4.5、y=-2.5） | `dist_interior.gd` 变压器（室内 4 台） | dist | Bump-only |
| di-busbar | 母线线缆（柜顶母线排、电缆桥架、墙面线槽） | `dist_interior.gd` 母线 | dist | Bump-only |
| di-signs | 标识牌（“高压危险”黄牌、设备铭牌色块、操作规程框） | `dist_interior.gd` 标识牌（新增细节） | dist | Bump-only |

注意：di-transformer 是配电房**室内**局部坐标的 4 台主变，不要把它当成 Godot 总览里 `[74,-30]` 的户外变压器组（`_build_transformer`，单组 5.6×3.4×3.6 箱 + 3 根绝缘子）。户外那组已有 Blender 件 ov-transformer（见 §3.1），不要拿 di-transformer 顶替。

## 4. 场景拼装表（进行中）

| 场景 | 组成件 | 场景文件 | 状态 |
|---|---|---|---|
| overview 校园总览 | 20 件 ov-*（§3.1）+ 拼装补的地面/池塘水面盘/配电房外壳 | `assets/blender/scenes/overview.blend`、`assets/models/scenes/overview.glb` | **已完成，最终刷新**（2026-11-23 11:18 CST，工人 d644ce2d：.blend 51,360,304 B、.glb **102,672,808 B**（上次 25,914,236 B，暴涨主因 B 组烘焙贴图嵌进 .glb，各件 .glb 之和约 102MB），回读 **4837** 个对象（append 4833 + 拼装补 4），脚本内置 VERIFY 与独立回读一致，DONE overview，日志零 Error/Traceback（`assets/blender/scenes/overview-refresh-20261123.log`）；3 分钟跑完、单进程错峰。差额 +8 全部来自 ov-road-main（src 36→44、kept 33→41，含环路中心线等新增对象），其余 18 件 kept 数与上次逐件核对完全相同。**2026-11-23 14:54 UTC 总览重刷**（`assets/blender/scenes/overview-refresh-transformer-20261123.log`）：.blend 66,234,504 B、.glb **123,019,340 B**（完整版；瘦身版见 §10），回读 **13,036**（append 13,032 + 拼装补 4；ov-transformer 58 件、其余 12,978 件），DONE overview，日志零 Error/Traceback；增量主因 ov-lawn 真草（kept 8,270 件）等 PBR 返工件 + ov-transformer 58 件。**202 种材质**（本地完整版 GLB JSON 实测；瘦身只动贴图、不动材质），贴图引用审计 0 缺失（见 §9）。**已解决（瘦身入仓，见 §10）**：完整版 .glb 123.0MB / .blend 66.2MB 仍超 API blob 上限，瘦身版 .glb 37,538,508 B / .blend 9,736,002 B 已随 commit `e56912f` 入仓（该版为池塘返工前）；**2026-11-23 23:58 CST 池塘草坪返工后重刷**（commit `8390649`）：完整版 .glb **121,570,192 B**、.blend 64,530,392 B，瘦身版 .glb **36,459,020 B** / .blend 9,092,702 B 已入仓（仓库核对一致，见 §9），回读仍 13,036 对象。草密度核查实测总计 **102,901**（程序化 94,761 叶、约 42/m² + 真素材 8,140 株）；22,500 一数口径**待确认**（丛 vs 叶未分清，不采用）；20 件全部全局坐标直接 append、未移位置，剔除 52 个预览地面/重复件/相机/灯光/探针；拼装补：地面 340×340（#69b45e，顶面 z=-0.05 防 z-fighting）、池塘椭圆盘（中心 (82,-78)、rx11/ry8、顶面 z=0.05，水面蓝 #2F7FC4 为拼装自选、campus.json 无池塘颜色；ov-lawn 池塘草坪已返工（2026-11-23 23:58 CST）：撒点排除水面椭圆（+1m 边距）只留环形带，4,662 叶、42.1 叶/m²，拼装不再下移草丛——旧 -0.5m 下移曾把 18,863 叶全埋地下）、配电房外壳 16×10×8m（#dfe9f2）+ 屋顶板 16.6×10.6×0.3m（#424A52）。户外变压器已补 ov-transformer（58 件，见 §3.1）。**2026-11-24 停车返工后重刷**：ov-parking R1 .blend（2026-11-23 19:31 UTC，补 Coat Weight 1.0 / Coat Roughness 0.05、车窗 Bump）拼入总览，overview.py 未改动（已是最新拼装逻辑、逐件 append 最新 .blend，仓库 SHA 一致）；20 件 kept 数与上次逐件核对完全相同（ov-parking src/kept 233/233——R1 只改材质参数、对象数不变），回读 **13,036**（append 13,032 + 拼装补 4），日志零 Error/Traceback（`assets/blender/scenes/overview-refresh-parking-20261124.log`）；完整版 .glb **121,570,548 B**（+356 B，清漆扩展数据）、.blend 64,546,472 B；GLB JSON 实测 13,036 节点 / **202 种材质** / 427 贴图（全内嵌、0 缺失）、KHR_materials_clearcoat 在列（ov-parking_body_red/grey/blue 3 种车漆）；瘦身版 .glb 36,044,776 B / .blend 9,093,786 B 见 §10。遗留：①ov-windows-roofs 件内 faces 表把半长半宽用反（东西向窗带用了 hx、南北向用了 hy，A/B/C 三栋窗带长短全部对调，修复任务已派）；②池塘椭圆南缘压到 ov-road-main 南环路带（y -84~-76 一段），水面顶 0.10 略高于路面顶 0.08，水面盖住一小段路缘，属件间布局冲突——**已解决（2026-11-24，commit `bea25274`）**：仅改 `assets/blender/scenes/overview.py` §3b，池塘圆柱 location z 0.04→-0.01，顶面 0.10→**0.05**（低于路面 0.08，净空 0.03），depth 保持 0.12，加断言 `pond top < 0.08`；椭圆形状/中心/尺寸、`ov-road-main`、SPEC、草坪排除区一字未动；总览重刷回读 13,036 对象零 Error，瘦身 GLB 36,081,140 B（<40MB），`verify_slim.py` 全绿。注意：blender-previews 只渲染单件 .blend，不渲染拼装总览，本次 run 出图里无池塘水面盘，无法从图上直接目视水面高低（见 §9）；水面与路缘的同框目视须走 Godot 侧拼装截图复核） |
| pv 光伏屋顶 | pv-roof、pv-panels、pv-mount、pv-inverter | `assets/blender/scenes/pv.blend`、`assets/models/scenes/pv.glb` | **已完成（最终干净快照）**（2026-11-23 01:33 CST：.blend 112,997,536 B、.glb 12,226,304 B，回读 **881** 个对象（roof 33、panels 548、mount 3、inverter 297），DONE pv；第一跑约 31 分钟时被服务重启 SIGTERM 杀掉、未写出任何文件，第二跑用 setsid nohup 脱离会话重跑成功，四件 SRC-UNCHANGED 全绿、干净单版本快照。pv.py 同步改动：EXPECTED["pv-inverter"] 291→297，三处总量 assert 875→881。最终版特征实测全过：板 548、北行横梁 35.124m、线槽顶端 19.350/13.300、逆变器箱体 A1 (−74.75,36.40)、A2 (−37.25,36.40)、LAB (−28,67.20)，北向段确为新 4 件。遗留小项：pv.py 头注释里的旧版源版本说明已过期（仍写上一轮混合版时间戳/md5），下次刷新时更新为本次实际拼入版本（roof d2681c69…、panels f042b491…、mount 009873e8…、inverter d12fc0f9…）或删掉）**2026-11-23 场景重出**（pv-scene-pbr-20261123.log，15:14 UTC）：.blend 13,562,916 B、.glb 19,774,596 B，回读 881 对象 / 25 种材质，DONE pv；场景 .blend 已随 commit `c0cd01d` 刷新入仓（仓库 13,562,916 B，与本地重出一致）；**场景 .glb 已刷新入仓**（commit `7227239`，仓库 19,774,596 B，与本地重出一致，旧 12,226,304 B 已替换）。**材质去重已修**（commits `8805b66`、`7bcd65c`、`1f36cb2`）：scenes/pv.py 与 scenes/charge.py 在 append 后去重，pv 材质 3,094→25（场景重出实测 25 种）、charge 117→24（见 §9 晚间记录）。**2026-11-24 00:30 CST P0/P1 材质补挂后重出**（commit `060877f`）：scenes/pv.blend 15,323,932 B、scenes/pv.glb **24,051,408 B**（仓库核对一致，旧 19,774,596 B 已替换），单件 pv-mount.glb 9,787,184 B，回读零 Error/Traceback（见 §9）。 |
| storage 储能站 | st-cabinet、st-doors、st-cables、st-base、st-fence + 拼装补的壳体 | `assets/blender/scenes/storage.blend`、`assets/models/scenes/storage.glb` | **已完成并已刷新**（拼装 2026-11-22 23:22 CST：.blend 4,731,368 B、.glb 1,773,372 B，回读 269 个对象；跟进修复 23:31 CST：st-doors 风扇组抬高 +0.045（盘底 2.555，高出顶盖顶面 2.55 共 0.005，防 z-fighting），回读 52 个对象；壳体改半透明 Alpha 0.35 BLEND（GLB JSON 已核对 alphaMode=BLEND），屋顶板保持不透明；门把手残余 0.002m 已清零（复核 0.000000）。场景重出后回读仍为 269 个对象，DONE storage。遗留：st-doors.py 里的 Preview 顶盖仍是旧 0.06 厚（顶面 2.51），与 st-cabinet v2 实际顶盖（0.10 厚、顶面 2.55）不一致，只作 .blend 内参照、不导出，留待以后统一；风扇盘底与顶盖顶面之间现为 5mm 悬空间隙，有意为之）**2026-11-23 场景重出**（storage-scene-pbr-20261123.log，15:20 UTC）：.blend 10,382,492 B、.glb 7,237,164 B，回读 269 对象，DONE storage；**仓库已刷新入仓**（commit `1f36cb2`：storage.glb 仓库 7,237,164 B、storage.blend 仓库 10,382,492 B，均与本地重出一致）。**2026-11-24 00:30 CST P0/P1 材质补挂后重出**（commit `060877f`）：storage.blend 11,886,071 B、storage.glb 8,623,960 B（仓库核对一致），回读零 Error/Traceback（见 §9）。**返工 R2-T4（2026-11-24，见 §9）**：st-fence R1（19:31 UTC）后重跑 `scenes/storage.py`，回读 269 对象（cabinet 83 / doors 52 / cables 64 / base 32 / fence 36 + 拼装壳体/屋顶 2），零 Error/Traceback；实测 R1 只改 Preview_* 材质，36 件围栏本体与场景内逐项一致、零差异，新 GLB 与仓库版字节相同（blob `b2c1d149`，8,623,960 B），.blend 同体积、blob 已更新。**返工 R2-T20（2026-11-24，见 §9）**：st-fence 立柱修后重拼，269 对象（cabinet 83 / doors 52 / cables 64 / base 32 / fence 36 + 壳体/屋顶 2），回读 269、零 Error/Traceback；新场景 .blend 11,883,543 B / .glb 8,610,616 B。 |
| classroom 教室内部 | cl-floor-walls、cl-desks、cl-board、cl-ac、cl-lights、cl-windows（局部坐标） | `assets/blender/scenes/classroom.blend`、`assets/models/scenes/classroom.glb` | **已完成并已刷新**（拼装 2026-11-22 23:22 CST：.blend 4,870,036 B、.glb 2,689,528 B，回读 436 个对象；cl-desks 修复后场景已刷新：.glb 2,689,484 B，回读仍为 436 个对象，桌椅包围盒 x[-3.490, 4.598]，最近桌沿离讲台 0.205m、最后一排椅背离东墙 0.167m，DONE classroom。**tevy 换件已完成**（2026-11-23，commits `cf0d432`、`c2d99fa`、`e2bce23`、`5d0e1fc`、`c046118`）：新 classroom.blend 7,349,592 B、classroom.glb 20,164,540 B，回读 **440** 个对象（原 436，+门 1 +填缝 3）；桌椅换成 tevy 现成模型拆件（24 张单桌循环复用 48 套、16 张干净单椅循环复用），48 套间隙前 0.208m / 后 0.204m，门装进 cl-windows.py（见 §3.4）。遗留：cl-windows 南北各 4 扇窗，SPEC 只写南侧 4 扇，北侧窗与北墙窗洞对齐、位置没错，但北侧 4 扇无窗帘）**R2-T17 刷新**（2026-11-24，见 §18）：cl-desks 换 3DAssets 课桌椅 + cl-floor-walls 墙面暖色补偿后重拼，classroom.blend 5,465,640 B、classroom.glb 19,090,632 B，回读仍 **440** 对象（73+96+39+58+54+120），桌椅间隙前 0.265m / 后 0.293m，零 Error/Traceback，commit `72897e90`。遗留：①cl-windows 南北各 4 扇窗，SPEC 只写南侧 4 扇，北侧窗与北墙窗洞对齐、位置没错，但北侧 4 扇无窗帘；②黑板盒埋进西墙（见 §18，cl-board 范围外，未修） |
| charge 充电区 | ch-piles、ch-cars、ch-marking、ch-canopy | `assets/blender/scenes/charge.blend`、`assets/models/scenes/charge.glb` | **已完成**（2026-11-22 23:36 CST 刷新后：.blend 7,930,116 B、.glb 934,624 B，回读 306 个对象（桩 40、车 198、标线 21、雨棚 47），DONE charge；4 台桩中心 y 均为 -73.25、与车位中心 x 偏差 0.00，桩南缘 -73.50 与车北端 -73.75 净空 0.25m（先前任务书写的 0.20m 为约数，实测 0.25m 更宽松、无穿插，脚本 12 组车–桩检查全部 no overlap）；白车 (48.5,-76) 在 4 号车位内朝南，蓝 (38,-76) 1 号、红 (45,-76) 3 号同样朝南；雨棚覆盖 4 个车位及 3 辆车全部 True）**2026-11-23 场景重出**（charge-scene-pbr-20261123.log，15:25 UTC）：.blend 7,439,548 B、.glb 7,126,168 B，回读 306 对象，DONE charge；**仓库已刷新入仓**（commit `1f36cb2`，含材质去重 117→24：仓库 charge.glb 7,105,356 B、charge.blend 3,376,684 B，均为去重后版本，见 §9）。**2026-11-24 00:30 CST P0/P1 材质补挂后重出**（commit `060877f`）：charge.blend 3,376,684 B（与去重版同体积）、charge.glb 7,105,712 B（仓库核对一致），回读零 Error/Traceback（见 §9）。**返工 R1 场景重刷**（2026-11-24：ch-cars 清漆 0.05/底漆 0.25 后重拼，charge.blend 3,376,684 B、charge.glb 7,105,672 B，回读 306 对象/24 材质，GLB 车漆 clearcoat 0.05 已核，零 Error/Traceback）。 **返工 R2-T19 场景重刷**（2026-11-24：ch-cars 换装后重拼，charge.py 车位检查改取 empty 下 4 mesh 并集；回读 123 对象（桩 40、车 15、标线 21、雨棚 47），三车各在 1/3/4 号位内、车头朝南、无桩穿插、雨棚全覆盖，材质去重 24；charge.blend 3,002,296 B、charge.glb 7,093,272 B，见 §19） |
| dist 配电房 | di-walls、di-cabinets、di-transformer、di-busbar、di-signs（局部坐标） | `assets/blender/scenes/dist.blend`、`assets/models/scenes/dist.glb` | **已完成并已刷新**（拼装 2026-11-22 23:25 CST：.blend 6,872,100 B、.glb 4,060,180 B，回读 379 个对象；di-signs 修复后场景已刷新：.glb 4,060,188 B，回读仍为 379 个对象，两块牌实测 Warn_Plate y=4.79、NoClose_Plate x=7.79，牌背恰贴墙内表面，DONE dist；dist.py 里两块牌的 CHECK 打印文案已由硬编码“BURIED”改成按实测跨度动态判定。**返工 R1 场景重刷**（2026-11-24：di-walls 天花板/墙面纹理加重后重拼，dist.blend 8,109,300 B、dist.glb 16,192,560 B，回读 375 对象——与上次 pbr 刷新逐件核对完全相同，零 Error/Traceback）。di-walls 的 5 种墙面材质各带 color+rough+normal 共 3 张烘焙贴图，GLB 里齐全；开关柜沿北墙一排，变压器 4 台对面无冲突、通道 5.84m，母线在柜顶；边框底板仍有 12.5mm 埋进墙（被牌面遮住、室内不可见，接受现状）。遗留：开关柜本体后沿 0.10m 嵌入北墙、母线/桥架 0.04–0.15m 嵌入北墙，墙内部分不可见、视觉上贴墙过紧，不影响导出，暂不改） |

拼装方法：新建场景 .blend 脚本（`assets/blender/scenes/<场景>.py`），用 `bpy.ops.wm.append` 把各件 .blend 里的对象 append 进来（只选本件对象，排除相机/灯光/太阳），存场景 .blend；全选导出场景 .glb 后用 `bpy.ops.import_scene.gltf` 回读验证，无 Error/Traceback 才算。
刷新说明：PV 修正与烘焙正在并行改件，拼装先按当时的 .blend 拼（各拼装任务已记录组成件时间戳），修正/烘焙落地后会再派一次刷新任务重出场景 .glb。

## 5. 六个待定口径的处理（默认值）

### 5.1 纹理管线（进行中）
- di-walls 已走通烘焙路线：程序化纹理烘焙成贴图，GLB 里 color/rough/normal 三张贴图全在，Godot 里能看到真实纹理（Cycles CPU、samples 4，约 6 分钟/件，贴图约 2.4MB；61% 纯黑死区是立方体默认 UV 十字展开留白，采样区颜色正确；margin=4px 偏小）。
- 默认值：大件、显眼件（楼体 9 件 + ov-windows-roofs、道路 2 件、草皮、跑道、球场，共 15 件）改成烘焙路线，margin 用 16px；小内饰件（树木、旗杆路灯、校门、停车区、光伏 4 件、储能 5 件、教室 6 件、充电 4 件、配电其余 4 件）可用 Bump-only 保底，逐件见 §3 标注。
- 玻璃材质不烘焙，保持透明材质原样。ov-lawn 只烘焙地面基底材质，草叶保持程序化。
- 烘焙做法以 `assets/blender/dist/di-walls.py` 第 300–480 行为参考实现，逐件把烘焙段追加进自己的 .py 再重跑。
- 状态：地面组 5/5 已完成（2026-11-23 04:04 CST）；楼体 A 组 5/5 已完成（2026-11-23 05:40 CST）；楼体 B 组 **5/5 已完成**（2026-11-23 11:15 CST，工人 f7870f36，提前约 7 小时）：gym 18 张 / lab 36 张 / tower 42 张 / canteen 33 张 / dorm 45 张，合计 174 张（color/rough/normal 各 58 张，约 42.9MB，全部 1024px、margin 16px、Cycles CPU、samples 4）；5 件 .blend/.glb 全部重出并经独立 Blender 会话逐件重读 GLB 复核（对象数 gym 192 / lab 358 / tower 929 / canteen 322 / dorm 739，全 MESH，无 Error/Traceback、无杂物对象、无 stray 材质）。玻璃按名含 "glass" 跳过烘焙。与 di-walls 的两处偏离：烘焙前加 Smart UV Project（立方体默认 UV 每面占满 0~1 会反复覆盖，改后同材质约 7 分钟出图）；断点续烘（PNG 已存在 >1000 字节且可读入就复用）。虚拟机约 2 小时一重启共 5 次，已烘好的图一张未丢（断点续烘全复用）。ov-gym 补窗核对已解决：实测 192 对象中有 16 个玻璃/窗对象（12 条窗带玻璃＋4 扇正门玻璃），无需补窗。烘焙版推送与总览最终刷新已派（见 §9）。
- B 组进度（2026-11-23 05:43 CST 只读核查）：gym 18/18（6/6 全套，.glb 01:58 CST 已重出）、lab 36/36（12/12 全套，.glb 04:59 CST 已重出）、tower 17/42（5 件全套＋MetalGrey 2/3，唯一 Blender 进程在烘，solo 约 1.8 分钟/张）、canteen 0/33、dorm 0/45。预计 B 组全部完成在 08:15–09:45 CST（tower 剩余约 30–60 分钟、canteen 约 40–80 分钟、dorm 约 60–105 分钟；最慢可拖到约 12:00 CST）。总览最终刷新仍在等 B 组全部落地。注意：B 组无落盘日志（stdout/stderr 接 pipe），进度只能以贴图落盘＋进程状态为准。
- A 组完成情况（2026-11-23 05:40 CST）：5 件全部 DONE、EXIT=0、无 Error/Traceback、GLB 直读 JSON 逐材质核对全部通过。先给 5 个脚本加了复用逻辑（照抄 B 组 ov-gym.py，盘上 PNG 存在且 >1000 字节就 load 复用，另加 1024×1024 尺寸核对；复用前逐张核对文件名与材质名一一对应、非空白）。bldA 新增 10/复用 14（24 张齐全，8/9 全套）；bldB 新增 27/复用 0（9/9 全套，bake 3957.4s）；bldC 新增 0/复用 27（并行另一工人先烘好的 27 张，9/9 全套）；lib 新增 15/复用 24（13/15 全套，39 图，bake 1998.0s）；windows-roofs 新增 0/复用 18（只重出，6/7 全套，新 .glb 21:39:50 晚于最晚贴图 17:10:53，已含最终烘焙结果）。两次运行环境重启杀进程（bldA 23/24 张时、lib 24/39 张时），复用逻辑使恢复只补缺失 pass。注意：bldB/bldC 脚本默认 MODE 是 `full`（会本地渲染），以后重跑务必带 `-- export-only`。
- 地面组完成情况（2026-11-23 04:04 CST）：road-main（Asphalt/YellowLine/Curb 各 3 张，61 分钟）、road-walk（7 材质各 3 张，28 分钟）、track（Track_Red/LaneLine/Curb 各 3 张，约 2 分钟）、field（深/浅草皮/白线/门框/看台各 3 张，约 4 分钟；半透明球网按设计跳过）、lawn（Lawn_Green/边框/土面/3 色花/灌木各 3 张，16 分钟；6 种草叶程序化保留）。全部回读验证通过。关键做法：UV 分瓦片（同材质各对象缩进 1024 图不重叠瓦片、瓦片间留 32px 间隙容纳 16px margin），road-walk 从 111 分钟被杀→28 分钟跑完；wear 顶点色随 DIFFUSE 烘进 color 贴图后删掉顶点色属性防 Godot 二次乘暗；from_pydata 无 UV 的网格烘焙前 smart_project 补 UV。注意：Blender 脚本抛异常时退出码仍为 0，验收必须读日志确认无 Traceback，不能只看退出码。
- 两处待确认：①ov-lawn 烘焙范围做了扩展——除地面基底外，花坛边框/土面/花瓣/灌木球也一起烘了（这些材质 Base Color 也是程序化链接，不烘焙在 Godot 里会丢色）；如需严格只留 Lawn_Green 需返工。②road-main 是唯一没用 UV 分瓦片的件（按 di-walls 原样跑通），3 张贴图是各面重叠 UV 烘出来的，视觉上是噪波但不是逐面位置精确；如需与后 4 件一致可重跑一次（加分瓦片后预计 20–30 分钟），已派返工任务。
- 历史：2026-11-23 01:16 CST 只读核查时 15 件中真正已完成的只有 ov-road-main；掉线的是楼体 A 组（b56ede15，重启后零写入、零进程），已补派续跑（5 件：bldA 续烘、bldB/bldC/lib 全量、windows-roofs 只重出；bldC 已由楼高修正任务顺带烘焙完成）。

### 5.2 pv 屋顶基准（已完成）
- 默认值：以 pv-roof 为准，把 pv 板块（板/支架/逆变器）整体下调约 0.65m 落到防水层上（A 栋板顶面 18.35、实验楼 12.30；女儿墙顶 19.0/13.0），逆变器线槽竖直段顶端高出女儿墙顶 0.35m。
- 结果（2026-11-22 23:28 PV 修正任务）：新 datum 按 pv-roof 板顶面为准——A/B 栋 18.35，实验楼 12.30；下调量 A/B 0.65m、实验楼 0.70m；板底（南缘最低点）现为 A/B 18.50、实验楼 12.45，即膜顶（18.40/12.35）之上 0.10m；线槽竖直段顶端 A1/A2 19.35、LAB 13.30，即女儿墙顶 +0.35m。三件串行重跑，全部 DONE，无 Error/Traceback：pv-panels.glb 99,088 B（回读 548）、pv-mount.glb 5,784,188 B（回读 3）、pv-inverter.glb 577,600 B（回读 291）。pv-roof 一个字未动。
- 已知偏差（接受现状）：datum 取的是板顶面而非膜顶（18.40/12.35），支架脚板、逆变器底轨/接线盒底面落在 datum，即膜顶之下 0.05m，视觉上被膜盖住、看不见；若要求与膜面齐平需 datum 改 18.40/12.35 再跑一遍，0.05m 不可见偏差暂不返工。另：实验楼女儿墙顶 pv-roof 写 12.95、任务文本写 13.0，相差 0.05m，线槽顶按 12.95+0.35=13.30 做，若以 13.0 为准则只高出 0.30m，待与 ov-lab 核对。
- **后续发现（2026-11-23 00:06 pv 拼装顶点级检查）**：下调后 A 栋出现真穿插——板 62 块（南排 row 00 共 32 块埋进南女儿墙 0.26m、北排 row 06 共 30 块擦北女儿墙压顶 0.25–0.26m）、支架南北沿（南沿整条 2022 顶点、北沿 816 顶点）、逆变器箱体底角（A1 西/A2 东）与北向线槽 TrunkY0（A 栋、实验楼）。根因：阵列平面 footprint 顶到女儿墙内面，下调前板/箱在压顶顶面（19.00）之上所以没碰，下调 0.65m 后落到压顶高度区间内、平面重叠变成真穿插；B/实验楼板与支架干净。修正方向：阵列整体向内收（南排北移、北排南移各约 0.3m 以上）、轨道随之缩短、逆变器箱体与线槽避开东西/北女儿墙；修正任务已派，修完三件重出、pv 场景再刷新做干净快照。

### 5.3 pv-inverter 与角部板重叠约 0.2m（已完成，横梁悬伸已收尾，pv 场景待刷新）
- 默认值：把 pv-panels 里那两块角部板挪开（优先挪到同排空位）或删除，不要留穿插。位置：A1 东缘 -74.50 与北行首列板西缘 -74.70、A2 西缘 -37.50 与末列板东缘 -37.30。
- 结果（2026-11-22 23:28）：删板，未找到同排空位可挪——A 行 32 列排满，B/实验楼端隙均 < 板宽 1.134m。删除 PV_A_06_00、PV_A_06_31（A 北行 r06 首末列板），总数 548 块（A 222 / B 156 / 实验楼 170）；pv-mount 里对应的 8 个压块 + 8 颗螺柱同步跳过（A 压块 888 = 222×4），不留悬空压块。独立 GLB 实测：两块角部板已不存在，北行剩余 30 块 x -73.532…-38.468，与逆变器净距两侧均为 0.968m。旧穿插是真实三维穿插（板 y 35.45…37.15 与逆变器 y 36.30…36.90、z 均重叠），删板必要。
- 横梁缩短已完成（2026-11-22 23:38 CST）：pv-mount.py 改为每行按实际板列算 row_len（与 pv-panels 删板条件同步，不写死数值），北行 r06 横梁 37.464m → 35.124m，两端各缩 1.17m，悬伸西/东均为 0.030m ≤0.1m，与新端板对齐；A 栋横梁 14 根、压块 888 不变，北行站数 16→15（端部支腿随梁内移，否则会悬空在梁外）、纵梁/横拉杆 112→111、支腿 224→222、螺栓 1336→1332；B/LAB 计数与旧版完全一致。pv-mount.blend 4,847,592 B、.glb 5,776,364 B，回读 3 个对象，DONE pv-mount。**pv 场景 .glb 仍是旧件拼装的，刷新任务已派。**

### 5.4 st-cabinet 与 st-doors 前门面重叠（已检查，收尾修复进行中）
- 默认值：拼装时检查门缝/格栅/把手浮雕与双开门是否视觉冲突，有冲突就调门浮雕内缩（在场景 .blend 里移，只动场景副本，不改件）。
- 结果（2026-11-22 23:22 storage 拼装实测）：门板 y[29.450, 29.480]，柜体南面 y=29.5；逐对算包围盒，12 处冲突全是柜体浮雕撞门板，都在右扇门上——把手 ×4（y 重叠 0.030m）、把手座 ×8（y 重叠 0.004m）。已在场景里沿 +y 内缩处理（把手 +0.030、把手座 +0.004），把手座 8 处清零，把手残余 0.002m 重叠埋在门板内、视觉不可见；门缝/格栅/屏/LED 与门板背面有 0.006–0.012m 间隙；北面百叶在柜北面外 0.02m，无重叠。
- 收尾：把手残余 0.002m（再 +0.002 清零）与风扇罩抬高、壳体改透明同一路跟进修复任务进行中。

### 5.5 ov-dorm 总高 16.40m（已定）
- 默认值：保持现状，记为与 SPEC §4 的 16m 示意高度偏差 0.4m（按屋顶板顶面 +0.65m 执行），不改女儿墙。
- 状态：已定，不改。

### 5.6 ov-dorm 楼间绿地与 ov-lawn 重叠（已完成，无重叠）
- 默认值：拼装时调整高差消除穿插（本件绿地已抬高 0.04~0.25m；总装时如有穿插再调）。
- 结果（2026-11-22 23:39 overview 拼装实测）：`dorm_lawn_between` 包围盒 x[74.00,94.00]、y[-38.00,-14.00]、z[0.040,0.253]；ov-lawn 在该矩形内没有任何对象（ov-lawn 的草坪只在南门、教学楼南、池塘三处），无 XY 重叠、无穿插，**不调整，高差调整量 0**。宿舍灌木（底部 z 约 -0.05）插进楼间绿地（顶 0.253）属于正常栽种，未动。

## 6. 缺口（无 Blender 件的程序化模型；户外变压器组已补，见划掉行）

以下 Godot 程序化模型没有对应的 Blender 单件，整合时要么保留程序化、要么用拼装补的简单几何（已注明）：

| 程序化模型 | 位置 | 处理 |
|---|---|---|
| ~~户外变压器组 `_build_transformer`（单组 5.6×3.4×3.6 箱 + 3 根绝缘子）~~ | [74,-30] | **已补**：ov-transformer（commit `7228f6b`，58 个对象，见 §3.1），已拼进总览场景；整合时用 Blender 件，不再保留程序化（di-transformer 仍是室内 4 台，不要混淆） |
| 池塘 `_build_pond`（rx11 rz8 椭圆） | [82,78] | overview 拼装补一个蓝色水面椭圆盘（拼装补的） |
| 地面 `_build_ground`（340×340，#69b45e） | 全校园 | overview 拼装补一块 340×340 地面（拼装补的） |
| 配电房外壳 `_build_building(dist)`（16×10×8m） | [48,-30] | overview 拼装补简单楼体盒 + 屋顶板（拼装补的，颜色读 campus.json dist 项） |
| 储能站外壳 `_build_storage`（8.6×4.4×4.0 壳体 + 屋顶板） | [64,-30] | storage 拼装补简单壳体盒（拼装补的） |

## 7. 明天整合（2026-11-23 18:15，4 小时）的替换步骤

1. 把 `assets/models/scenes/<场景>.glb`（6 个）导入 Godot，放在场景原点，不移位置、不旋转（全局坐标 + glTF 默认方向与 Godot 一致，见 §1）。
2. 隐藏对应的程序化节点：总览用 `set_host_visible()` 同步隐藏宿主（`campus_builder.hosts` 里的 bldA/bldB/bldC/lib/gym/lab/tower/canteen/dist/dormA/dormB/storage/transformer 等）及其碰撞体；内景把 `classroom_interior.gd` / `dist_interior.gd` / `storage_interior.gd` / `pv_detail.gd` / `charge_detail.gd` 的 `_build()` 程序化内容换成 GLB 实例（局部坐标场景放在内景原点）。
3. 模拟、天气、图表、标签、飞入逻辑一律不动；只换模型。
4. 逐场景在无头浏览器截图验收 6 场景；中文方框字体问题、窄屏溢出（P2-1）、两套按钮样式（P2-4）、总览偏淡都在整合里一起修。
5. 整合前先核对本文件 §5 六个口径的处理结果是否都已填好，缺什么记下来，不谎称齐全。

## 8. 注意事项

- 不要在本地渲染任何预览图（本地渲染会卡死机器）。渲染全部走 GitHub Actions：公开仓库 `ryc2077/campus-vpp-demo` 的 `.github/workflows/blender-previews.yml`（改 `assets/blender/**` 自动触发，最高画质渲染），推上去等出图再复核视觉。
- 推送用 custom.github 连接器：`python3 ~/workspace/custom-connectors/custom.github/bin/gh.py push-files --repo ryc2077/campus-vpp-demo --branch main --message "..." 本地路径:仓库路径`，分批推，不要用 git push。
- 玻璃透明材质导出为 BLEND 混合透明；Godot 侧的实际反光效果取决于其环境/反射设置，.blend 里的反射探针不随 GLB 导出。
- Blender 4.2 材质混合属性有坑（2026-11-22 储能修复时踩到）：新材质默认 `blend_method='HASHED'` / `surface_render_method='DITHERED'`，不是 OPAQUE；且 `blend_method` 设 `'OPAQUE'` 会被静默忽略（读回仍是 HASHED），`surface_render_method` 只有 DITHERED/BLENDED 两档、无 OPAQUE 枚举。不透明靠 DITHERED + Alpha 1.0 实现；不要写 `blend_method == 'OPAQUE'` 断言，以 `surface_render_method` 为准。
- ov-gym v2 窗对象待核对：烘焙 B 组任务先检查，没有就按 SPEC §5 补简单窗带。
- 窗带修复已验收入库 5 件：ov-canteen、ov-lab、ov-lib、ov-tower（79 段，666 个窗带对象，回读总数 929）、ov-dorm。

## 9. 推送与 Actions 渲染记录

- 2026-11-22 23:41 CST：3 批共 20 个文件推上公开仓库 main（推送前与 HEAD `5430e7b5` 逐文件比对 blob SHA，确认全部是新版/新增，无重复推送）。
  - 第 1 批 `d7633b40`：charge 修复 6 件（ch-piles/ch-cars 的 .py/.blend/.glb，桩北移、白车进 4 号车位）。
  - 第 2 批 `42eacffe`：4 个已完成场景 .blend + 对应 .glb（classroom、storage、dist、charge）。
  - 第 3 批 `c1a9ca82`：di-signs（两块牌移 0.18m）、cl-desks（平移 0.15m）各 .py/.blend/.glb。
  - 触发 blender-previews 3 个 run：[45039531352](https://github.com/ryc2077/campus-vpp-demo/actions/runs/45039531352)（第 1 批，查询时 completed/success）、[45039622787](https://github.com/ryc2077/campus-vpp-demo/actions/runs/45039622787)（第 2 批，in_progress）、[45039659685](https://github.com/ryc2077/campus-vpp-demo/actions/runs/45039659685)（第 3 批，in_progress）。
  - **待核实**：第 1 批 run 约 2 分钟即 success，6 组最高画质渲染 2 分钟完成速度异常，未核实 artifact 内容是否真实产出渲染图——已派核查任务。
  - 未推：pv/overview 场景拼装（未 DONE，不推半成品）、pv-mount.blend（23:37:53 刚改过，待下一轮核对）。

- 2026-11-22 23:45 CST 核查结论：**三个 run 的 success 全是假的——一张图都没渲染出来**（核查任务，18 个 job 日志逐个核对）。
  - run #8 46 秒、#9 76 秒、#10 47 秒，6 个 job 全 success，但 artifacts 全部 `total_count: 0`，43 个 .blend 文件全部失败、0 张 PNG。
  - 失败模式 1（多数）：缺 `libEGL.so.1`，EEVEE_NEXT 一启动就 core dump（workflow 只装了 xvfb，没装 EGL/OpenGL 库）。各组 abort 数：overview 14/19、storage 5/5、dist 5/5、charge 3/4、pv 1/4、classroom 1/6。
  - 失败模式 2（其余）：场景里没有相机，`Error: Cannot render, no camera`（classroom 5/6、pv 3/4、overview 5/19、charge 1/4 无相机）。两个问题叠加：只修一个仍渲染不了。
  - 为什么全败还能 success：渲染循环用 `|| echo "FAILED: $name"` 吞掉了 Blender 非零退出码；`upload-artifact` 用 `if-no-files-found: warn`，空目录也 success。
  - 另有非致命警告：`tools/render_max.py` 与 Blender 4.2 不兼容（`taa_reprojection`、`shadow_pool_size` 属性不存在，最高画质设置只部分生效）。
  - 修复任务已派：workflow 加 `libegl1`/`libgl1` 等 EGL 依赖、渲染脚本无相机时自动建相机、去掉吞错改失败即失败、`upload-artifact` 加 `if-no-files-found: error`、顺手修 render_max.py 的 4.2 不兼容设置；修完重新触发验证 artifacts 是否出现。

- 2026-11-23 01:13 CST：守护进程重启（restart drain）导致 3 路工人掉线失败，文件已落盘的部分不受影响：①pv 场景首轮刷新（96a4a2a4）——scenes/pv.blend 16:32 UTC、pv.glb 16:34 UTC 已写出（第一版逆变器），最终刷新（613021ec）已派、会用最终版重拼；②窗带修复（d44fa081）——ov-windows-roofs.py 已改好（faces 表 hx/hy 纠正，注释写明旧 bug），.blend 16:54 UTC、.glb 16:55 UTC 已写出，掉线前未来得及汇报回读验证，已派核验任务；③烘焙一路（b56ede15）掉线，具体是哪组待核查任务确认后补派（.py 编辑时间戳：地面组 16:21–16:24、楼体 B 组 16:25、楼体 A 组 16:32；已完成重出的只有 ov-road-main.glb 16:20 UTC）。

- 2026-11-23 01:18 CST 窗带核验时顺带发现（未核实）：ov-bldC.blend 里有 `bldC_cornice_F5`（z=18.1）与 `bldC_roof_slab`（z=18.23），C 栋 GLB 整体高 20.02m，与 SPEC §4 的 C 栋 22×13×14m、4F 对不上（4 层楼不应有 F5 檐口）。已派核查+修正任务。
- 2026-11-23 03:36 CST 核查结论：确认超高，已修好（见 §3.1 ov-bldC 行）。旧件每层 4.4m、F5 檐口、压顶 19.0m；新件压顶顶面恰好 14.00m，GLB 总高 14.92m（含屋顶设备盖，与 A 件同例）。overview 场景 .glb 仍是旧件拼的（含 20.02m 的旧 C 栋），待烘焙落地后刷新。

- 2026-11-23 02:55 CST：渲染链修通，最终验证 run [45052162219](https://github.com/ryc2077/campus-vpp-demo/actions/runs/45052162219) success，6 个 job 全绿，**43/43 张 PNG 全部有真实画面内容，无黑帧**（逐张像素统计，全部 1280×720 真 PNG）。
  - 改了两个仓库侧文件（未动任何 .blend）：`.github/workflows/blender-previews.yml`（加 libegl1/libgl1/mesa 等 EGL 依赖、去掉 `|| echo` 吞错、加上传前校验、`upload-artifact` 加 `if-no-files-found: error`、push 触发路径补 tools/render_max.py）；`tools/render_max.py`（无相机时按包围盒自动建 3/4 俯视相机、无灯光时加默认太阳光能量 3.5、无 world 或背景近黑时补天蓝背景；修 4.2 不兼容：`taa_reprojection`→`use_taa_reprojection`、`shadow_pool_size` 4096→枚举 `'1024'`）。
  - 三轮才修通：`7c2e415e`（主修复，run 45040243462 success 但抽查黑帧）→ `8e5349e9`（修相机距离 bug：`Camera.angle` 本已是弧度，`math.radians()` 多转一次使相机远约 56 倍，run 45045216348 仍有黑帧）→ `d092e22`（加默认太阳光 + world 背景，最终通过）。第一轮黑帧根因是相机 1117m 外；第二轮黑帧根因是 .blend 里无灯光/world（cl-ac、cl-desks 的 .blend 比 .py 生成器版本旧，从 `read_factory_settings(use_empty=True)` 起步就没加）。
  - 最终 artifacts：overview 19 张 18.5MB、pv 4 张 3.7MB、storage 5 张 4.7MB、classroom 6 张 4.2MB、charge 4 张 3.5MB、dist 5 张 4.8MB，合计约 39.4MB。本轮自动建相机 14 次、补太阳光 14 次、新建 world 6 次。
  - 遗留：软件 GL（llvmpipe）渲染慢，整 run 约 1 小时（overview 组单 job 55–70 分钟）；classroom 组偏暗（新 world 背景亮度约 0.05，未触发 0.02 阈值，背景深灰但模型可见）；.blend 本身仍缺相机/灯光/world，预览能力依赖 render_max.py 运行时补全，根治需重跑各组 .py 生成脚本重建 .blend（不在本次范围）。

- 2026-11-23 03:04 CST 第二轮推送：5 批、19/21 个文件上 main（与 HEAD `0163903` 逐文件比对 SHA，15 个 CHANGED、6 个 NEW）。
  - `7f6ce5c1` 光伏三件修复版 9 文件；`66db2196` pv 场景最终版（pv.py + pv.glb 881）；`a726f9cc` 总览场景（overview.py + overview.glb 4829，烘焙前快照）；`d09c8799` 窗带修复版 3 文件；`5cb5f01` ov-road-main 烘焙完成版 3 文件。仓库 HEAD 现为 `5cb5f01`。
  - **未推出的 2 个文件**：`assets/blender/scenes/pv.blend`（113 MB）、`assets/blender/scenes/overview.blend`（51 MB），Git Data API 建 blob 报 HTTP 422 "input too large"（仓库无 LFS，现有最大 blob 约 12 MB，上限在约 26–51 MB 之间）。需带登录的 git push 或接 LFS 才能落地，待父 agent 决定。
  - 触发 5 个 run：[45058043817](https://github.com/ryc2077/campus-vpp-demo/actions/runs/45058043817)（7f6ce5c1）、[45058283212](https://github.com/ryc2077/campus-vpp-demo/actions/runs/45058283212)（66db2196）、[45058515105](https://github.com/ryc2077/campus-vpp-demo/actions/runs/45058515105)（a726f9cc)、[45058554745](https://github.com/ryc2077/campus-vpp-demo/actions/runs/45058554745)（d09c8799）、**[45058590662](https://github.com/ryc2077/campus-vpp-demo/actions/runs/45058590662)（5cb5f01，最终 HEAD，含全部已推文件）**。整 run 约 1 小时，未等出图；只有最新 run 覆盖全部文件，前 4 个是否取消以省 runner 时间待定。渲染出图复核任务已派（等 45058590662 跑完，验 artifacts 并抽看关键预览图）。

- 2026-11-23 04:08 CST 第三轮推送：3 批、15 个文件上 main（与 HEAD `5cb5f014` 逐文件比对 SHA，只推变了的）。
  - `4781a03f`：ov-road-walk、ov-track 各 .py/.blend/.glb；`4957206f`：ov-field、ov-lawn 各 .py/.blend/.glb；`696b9d8e`：ov-bldC .py/.blend/.glb（压顶顶面 14.00m 已核实）。
  - 跳过：ov-road-main 三件（SHA 与第二轮已推的烘焙版完全一致，未重复推）。
  - 触发 3 个 run：[45064606750](https://github.com/ryc2077/campus-vpp-demo/actions/runs/45064606750)（4781a03f）、[45064678219](https://github.com/ryc2077/campus-vpp-demo/actions/runs/45064678219)（4957206f）、[45064708913](https://github.com/ryc2077/campus-vpp-demo/actions/runs/45064708913)（696b9d8e，最新 HEAD）。另有 2 个更早的 run（45058590662、45058554745）仍在跑，渲染出图复核任务盯的是最新 run。

- 2026-11-23 04:15 CST 第四轮推送：只推 road-main UV 分瓦片新版 3 文件，commit `cdd23fa1`（.py 含 `_pack_uvs` 定义第 333 行、调用第 429 行；.blend 同为 1,211,540 B 但内容已变；.glb 802,176 B，新 SHA-256 前缀 6ca1ae94…与返工汇报一致）。触发 run [45065322605](https://github.com/ryc2077/campus-vpp-demo/actions/runs/45065322605)（queued）。注：工程目录本身不是 git 仓库，无法用本地 git diff 枚举其他本地文件相对 HEAD 是否还有未推改动；已知未推：A 组续跑件、B 组烘焙件、总览最终刷新（待烘焙落地）。

- 2026-11-23 04:22 CST 渲染出图复核（run 45058590662，HEAD 5cb5f01）：success，总耗时 69 分 44 秒，6 个 job 全绿，43/43 张真 PNG、1280×720、无黑帧、无纯白帧。Artifacts 合计约 35.5 MiB（overview 19、classroom 6、pv 4、dist 5、storage 5、charge 4）。19 张目视抽查结论：
  - 通过：ov-lawn（草可见、密度中等、无大片裸露绿底）、cl-desks（椅腿可见、椅面离地、靠背立起）、cl-windows（玻璃深蓝带反光 streaks）、pv-panels（阵列整齐、电芯网格可见）、ch-cars（三分开、无穿插）、ch-marking（车位线+绿垫+黄线、沥青有斑驳颗粒感）、ch-piles（4 桩齐整）、ov-parking（各车在位内无压线）、ov-bldA/B（屋面瓦纹清晰）、ch-canopy、ov-lib（红砖腰线带砖纹，质感最好）。
  - **必须修：①ov-road-main 整条路品红**（无沥青颗粒、无标线，疑似烘焙贴图缺失——Blender 缺贴图的典型品红；本轮就是为修主路而推，结果未修好）；**②ov-windows-roofs 屋面整片品红、窗框描边泛品红**（疑似同一批材质/贴图缺失；bldA/B/C 屋顶深色瓦面正常，说明是局部材质问题）。疑似根因：烘焙贴图 PNG（`*_textures/` 目录）从未推上仓库，runner 上的 .blend 找不到贴图；另需核查 .blend 里贴图路径是相对还是绝对。修复任务已派。③取景过远：pv-inverter、di-signs 主体 <2% 画面，无法复核，需拉近重拍。④取景裁切：pv-roof 第二块屋面被裁一半，需后退/移位重拍。
  - 可接受：楼体墙面全平无砖纹（风格化平涂）、road-walk 步道无铺装纹理偏细、pv-panels 颜色偏浅、pv-mount 对比度太低、ch-piles 最右桩似微倾（疑似透视）。
  - 无法核对：白车是否在充电区 4 号车位内、桩与车是否穿插——43 张里没有充电区合成图（ch-* 全是隔离单体），需补一张充电区合成渲染（桩+车+车位同框）才能 verdict；光伏横梁悬伸量也因 pv-mount 太暗看不清。
  - 另：品红像素全量扫描只有 2 张含品红（ov-road-main 11.9%、ov-windows-roofs 4.5%），其余 41 张为 0；3 张低标准差（pv-inverter 2.7、pv-mount 1.6、di-signs 2.9）均非空白帧，而是取景过远导致大面积均匀背景。

- 2026-11-23 04:46 CST 品红根因修复完成：三条证据查实——①本地共 13 个 `*_textures/` 目录、254 张 PNG（约 41MB），凡是 .blend 引用的本地全部存在；②仓库 push 前 0 张贴图（无 .gitignore，不是忽略规则，是历次推送根本没推过贴图目录）；③.blend 路径 DNA 级直读全是相对路径（`//*_textures/*.png`，`/home/hatch/...` 残片是 name 缓冲区 NUL 后的 stale 字节，不是有效路径），不需要改 .blend。日志旁证：run 45058590662 overview job 里 `GPUTexture: Blender Texture Not Loaded!` 在 ov-road-main 出现恰好 9 次、ov-windows-roofs 恰好 18 次，与贴图数一一对应。根因定论：贴图缺失 → EEVEE 加载失败 → 品红。
  - 推贴图 5 批全部入库：`1cfc060`（road-main 9 + windows-roofs 18）、`83ae046`（bldA/B/C、field、gym，111 张）、`77d052c`（lab/lawn/road-walk/track、di-walls，96 张 + render_max.py）、`6bf28c7`（lib 18 张）、`8f349eb`（最后 2 张）。最终仓库 254 张 = 本地 254 张，HEAD `8f349eb`。未动任何 .blend。
  - 取景修 tools/render_max.py（仅 `_ensure_camera` 拟合段）：旧包围球一刀切拿水平视场角当限制角用，垂直方向近约 33%——就是 pv-roof 被裁一半的成因；新取包围盒 8 角投影、水平/垂直各用自己的半视场角拟合、边距 1.10 按轴算、加近角深度补偿。离线验算 40×15×0.5m 扁平件 72.5m→76.7m（裁切修正方向正确）。
  - 触发 run：手动 dispatch [45067957716](https://github.com/ryc2077/campus-vpp-demo/actions/runs/45067957716)（HEAD 6bf28c7）与自动触发 [45068200471](https://github.com/ryc2077/campus-vpp-demo/actions/runs/45068200471)（HEAD 8f349eb，最新）。验证复核任务已派（等 45068200471 跑完，验品红是否消失、取景是否改善）。
  - 遗留：①pv-inverter 的 <2% 修不掉——3 台逆变器分处 A1/A2/LAB，包围盒横跨 47×31m，任何整场拟合都会让 1.4m 箱体只占百分之一二，需按簇取景或生成器侧加相机，待定；②di-signs 自带 22mm 相机，render_max.py 按设计复用已有相机，想放大得改 di-signs.py 的相机，本次未动；③并行烘焙仍在写文件（任务期间 ov-lab/ov-lib 贴图持续落盘，20:45 UTC 已追平；如继续落盘需再同步推一次；ov-lab 31 张、ov-lib 19 张目前是孤儿贴图——对应 .blend 引用 0 张图，今天不影响渲染）；④未解小疑问：bldA/B/C 等 9 件也引用贴图且同样缺失，但上轮渲染 0% 品红、日志 0 条报错（贴图已一并推上，无论哪种成因都覆盖，不阻塞验证）。

- 2026-11-23 05:47 CST 第五轮推送：4 批全部成功，HEAD `588a7f27`（推前 `8f349eb`，已复核一致）。
  - `4eaddcea` ov-gym 烘焙完成版 3 文件；`3a3f9470` ov-lab 烘焙完成版 3 文件；`4b16a0ae` 补推 ov-lab 缺失贴图 5 张（AC_Grille normal/rough、DoorFrame 3 张）；`588a7f27` 补推 ov-lib 缺失贴图 21 张。
  - 贴图比对：本地 13 个目录逐张比对仓库全量 tree（502 条），254 张 SHA 相同、42 张缺失，共补推 26 张；仓库贴图总数现为 279 张（lab 36、lib 39、gym 18 齐全）。ov-gym 18 张全部已在库（与预判不同）；其余目录无缺失。
  - 触发 4 个 run，最新 [45074011767](https://github.com/ryc2077/campus-vpp-demo/actions/runs/45074011767)（HEAD 588a7f27，含全部补推贴图）。未推：ov-tower（进行中，16 张贴图本地有、仓库缺，待烘完后推）、canteen/dorm（未开始）。

- 2026-11-23 06:22 CST 第二轮渲染复核（run 45068200471，HEAD 8f349eb）：success，执行约 1 小时 07 分，6 个 job 全绿，43/43 张真 PNG、1280×720、黑帧 0 张。**品红彻底消失**：严格阈值与宽松阈值下 43 张全部 0 品红像素，ov-road-main 与 ov-windows-roofs 均为 0px；6 个 job 日志 `GPUTexture` 出现 0 次。
  - 目视抽查通过：ov-road-main（品红消失）、ov-windows-roofs（屋面灰蓝斑驳贴图正常）、ov-bldA（取景饱满、无接缝）、ov-lib、ov-lawn（草丛簇密布、满幅无接缝）、ov-road-walk（广场放射铺装可见）。
  - **必须修 3 项**：①pv-inverter/di-signs 取景——稀疏多件组按整体包围盒取景，主体仅 0.2%/0.5%，应单件取景、按件分图或收紧相机（同类较轻：pv-mount 1.7%、ov-road-walk 2.8%）；②pv-roof 第二块屋面仍被裁——主屋面已完整，但右侧第二块只露约 1/4，应纳入取景包围盒或移出画面；③ov-road-main 沥青无颗粒、无路缘石、环路无中心线——全图仅 830 个唯一色，2 倍放大仍为纯色，需工程侧确认是烘焙贴图本身就是纯色还是材质未挂贴图。修复任务已派。
  - 可接受：road-main 环路转角接缝细白斜线（两处）、各组背景地面不一致（绿草地 vs 深灰虚空）。
  - 复核报告在 `~/workspace/vpp-recheck/report-run-45068200471.md`（全量扫描表 scan-all.txt）。

- 2026-11-23 06:59 CST 复核问题修复完成，commit `81b7ac08`（15 个文件：ov-road-main 的 .py/.blend/.glb＋7 张变了的贴图、pv-roof v2 的 .py/.blend/.glb、tools/render_max.py、工作流），触发 run [45080689179](https://github.com/ryc2077/campus-vpp-demo/actions/runs/45080689179)。
  - road-main 根因：贴图本身（几乎）纯色（见上行），材质链接没问题；路缘石 21 个都在，复核说的“无路缘石”是 0.3m 宽在 260m 俯视里约 1.4px、看不清；黄线缺一半是对象缺失（环路中心线 0 个对象），已按 SPEC §5 补 8 个。
  - pv-roof 裁切根因：仓库里的 pv-roof.py/.blend 仍是 v1（自带只拍 A 栋的 PreviewCamera），本地 v2（无相机、33 个对象）从未推上；render_max 见自带相机就直接信任。本次把本地 v2 一并推上；实测 v2 无相机时自动取景三块屋面 NDC 全部在 [0.17,0.79]×[0.17,0.67] 内，无裁切。
  - render_max.py：`_fit_camera` 抽成函数、`_projected_stats` 新增投影占比判定、`_ensure_camera` 自带相机只在“无整件出画且投影占比 ≥2%”时保留（di-signs 22mm 相机占比 0.010 被覆盖）、`_clusters`（包围盒间隙 3m 单链聚类）＋`_cluster_label`（最长公共前缀），稀疏多件组逐簇成图（pv-inverter → A1/A2/LAB 3 张；di-signs → N 23 件 / E 5 件）；工作流收集 `${name}-*.png` 簇分图。最高画质设置原样不动。
  - 遗留：簇分图在 Actions 里的确切文件名待 run 证实（`pv-inverter-A1.png` 或 `pv-inverter-A1_0001.png`，工作流两种都收）；pv-mount（1.7%）、ov-road-walk（2.8%）本次未单独处理（通用规则下是整图单图，若复核仍嫌主体小，需按对象像素占比而非包围盒再定规则）；本地 screenshots/blender/ 仍是旧图，别拿它们当新结果。

- 2026-11-23 07:02 CST 第三轮渲染复核（run 45074011767，HEAD 588a7f27）：success，1 小时 6 分 41 秒，6 个 job 全绿，43/43 张真 PNG、1280×720、黑帧 0 张。**品红全部为零**（严格与宽松两档阈值均为 0），ov-road-main 与 ov-windows-roofs 品红已消失——贴图缺失根因确认修好，279 张贴图已推齐。
  - 目视抽查通过：ov-gym（红砖竖纹墙面清晰）、ov-lab（米白墙面 + 红竖条）、ov-bldA（屋顶瓦片纹清晰）、ov-bldB、ov-lib、ov-road-main（品红消失、深灰沥青 + 黄色中心线）、ov-windows-roofs（屋面深灰蓝混凝土纹、5 条窗带浅蓝玻璃纹理清晰）。
  - 本轮仍有问题但**均属预期内**：pv-roof 第二块屋面仍被裁、pv-inverter 主体 0.19%、di-signs 0.37%——因为本轮 HEAD 588a7f27 **早于**修复提交 81b7ac08（相机取景、pv-roof v2、簇分图、road-main 重烘都在 81b7ac08 里），修复是否生效由第四轮复核（run 45080689179）验证。
  - 另记：ov-bldA/B 窗户呈小黑方块、无玻璃纹理——应是空调外机（AC_Grille/AC_Body），窗带在 ov-windows-roofs 件里，不视为缺陷，不处理。

- 2026-11-23 08:09 CST 第四轮渲染复核（run 45080689179，HEAD 81b7ac08）：success，约 66.5 分钟，6 个 job 全绿，43 张主图真 PNG、1280×720、无黑帧；品红全部 0.0000%。修复验证 3 项中 2 项生效、1 项未生效：
  - ✅ ov-road-main 沥青颗粒+环路中心线生效：2 倍放大见沥青明显斑驳颗粒，黄色中心线沿环路四边连续、转角跟随倒角，白色边线清晰；路带灰度 std 22.54 vs 草地 2.67。
  - ✅ pv-roof 推 v2 去旧特写相机生效：三块屋面全部完整入画，无裁切（日志 frame share 0.732）。
  - ❌ 稀疏多件组按簇取景未生效——**簇分图 0 张，全部缺失**：簇渲染本身跑了（pv-inverter A1/A2/LAB、di-signs N/E 的相机与对象数日志俱全，约 2 分钟/张），但写错了地方。根因：`tools/render_max.py` 第 296/321 行用 `scene.render.filepath` 派生簇路径；工作流命令是 `blender -b "$f" -E BLENDER_EEVEE_NEXT --python tools/render_max.py -o "/tmp/render/${name}_" -f 1`，Blender 按顺序处理参数，`--python` 执行时 `-o` 还没生效，脚本读到的是 .blend 里存的旧 filepath（`/tmp/`），簇图写成 `/tmp/-LAB.png` 等；其后 `-f 1` 才用 `-o` 正确写出主图。工作流收集 glob `/tmp/render/${name}-*.png` 自然匹配不到。修法（二选一或都做）：工作流把 `-o` 移到 `--python` 之前（一行改动）；或 render_max.py 从 `sys.argv` 解析 `-o` 的值。修复任务已派。
  - di-signs 主图近乎空白灰底（仅中央一块约 40px 宽红牌 + 6 块微型蓝牌，文字不可读）——是簇分图缺失的直接后果，需等簇分图修好重跑后用 N/E 分图复核。pv-inverter 主图=最大簇取景生效（一台柜大而清晰），但 A2/LAB 两台无分图、无法验收。
  - 可接受：路缘石只表现为白色边线；pv-mount 对比度低；ov-flag-lamp 主体占比 0.2%（簇数超 8 上限未触发分簇，后续单独立方案）。

- 2026-11-23 08:11 CST 簇分图路径 bug 修复完成，commit `2f0bb575`（2 个文件），触发 run [45087237792](https://github.com/ryc2077/campus-vpp-demo/actions/runs/45087237792)（in_progress）。
  - 工作流第 58 行：`-o "/tmp/render/${name}_"` 移到 `--python tools/render_max.py` 之前，只改参数顺序。
  - render_max.py：顶部加 `import sys`，新增 `_output_base(scene)`（约第 261 行），优先从 `sys.argv` 解析 `-o` / `--render-output`（支持 `-o value`、`-o=value`、`--render-output=value` 三种形式，无论 `-o` 在 `--python` 之前、之后还是 `--` 之后都能拿到），解析不到才回退到 `scene.render.filepath`；第 324 行簇路径派生改用它。`py_compile` 通过。
  - 本地模拟验证（AST 提取真实函数执行，假 scene filepath 设为旧值 `/tmp/`）：7/7 通过——新顺序、旧顺序、`--` 之后、`--render-output=`、`-o=` 均能拿到正确 base；无 `-o` 时回退到 `/tmp/`（预期回退行为，仅无 `-o` 时出现，工作流里不存在这种调用）。
  - 验证复核任务已派（等 45087237792 跑完，确认各 group artifact 里出现 `<name>-<label>.png` 簇图、cluster 日志路径正确）。

- 2026-11-23 09:18 CST 第五轮渲染复核（run 45087237792，HEAD 2f0bb575）：success，62 分 01 秒，6 个 job 全绿。**簇分图路径修复确认生效**：48 张 = 43 张主图 + 5 张簇分图，文件名均为 `<name>-<label>.png`（无 `_0001` 后缀）；pv/dist 两组 job 日志里 cluster 路径均为 `/tmp/render/<name>-<label>.png`，`/tmp/-<label>.png` 模式零命中。全部真 PNG、1280×720、RGBA，无黑帧；品红 48 张全部 0.0%。
  - 通过：pv-inverter-A1/A2/LAB（三要素齐全，柜体约占画面高 40%）、ov-road-main（无回归）、pv-roof（无回归）。
  - **必须修 2 项（均为 di-signs）**：①N 簇取景太远——簇相机距墙 20.5m，23 个对象沿墙排开整排一次框入，蓝牌仅约 15×8px、中央红牌约 55×35px，文字完全不可读，需收紧 N 簇取景（或按单块牌拆簇 / 拉近相机）；②牌面文字是占位色块而非真实文字——E 簇近景（1.45m）放大证实：红底白面上的“文字”是三条实心红横条，N 簇红牌上是白横条，均无字形，即使修好取景也读不出字，需在模型里把文字做成真实文本或贴图。修复任务已派。
  - 可接受：主图与最大簇像素完全相同（`main view = largest cluster`，设计如此）；pv-inverter A1 与 LAB 视角几乎相同（同款逆变器、相似相对机位）；逆变器簇图背景空旷；pv-mount std 1.3、ov-flag-lamp 4.5（画面近乎纯色，仅列为待查）。

- 2026-11-23 09:26 CST di-signs 两项必须修完成，commit `4a82fafc`（4 个文件：di-signs 的 .py/.blend/.glb、tools/render_max.py），触发 run [45094589856](https://github.com/ryc2077/campus-vpp-demo/actions/runs/45094589856)（推送时 in_progress）。
  - 牌面文字（出处：脚本注释 + SPEC §7，未自编）：Warn_Plate“高压危险”、NoClose_Plate“禁止合闸 / 有人工作”（两行）、Num1–Num6 为“1–6”（与 di-cabinets 柜号对齐）。
  - 真实文字做法：8 个占位色块条全部删除，改成 Blender Text 对象（origin 离牌面 0.0015m + 挤出 0.0005m，防 z-fighting；红牌/蓝标白字、白牌红字；居中对齐）。字体坑已避开：工程 `assets/fonts/NotoSansSC-Regular.ttf` 是子集，经 fontTools 核查缺 危/险/止/人 四字，改用工程内全量字体 `tools/fonts/NotoSansSC-static.ttf`（10MB，14 个所需字全覆盖），系统 NotoSansCJK 作备用。字号自校准：Blender 字号与字宽不是 1:1（实测 size=1.0 时 4 字中文仅宽 1.3725m），脚本建完按实测尺寸自动缩放（Warn 0.42×0.10m 占牌面宽 70%、NoClose 每行 0.416m 整块高 0.34m、数字高 0.075m）。朝向数值验证：Warn/Num 行向 +X、字顶 +Z、法线 −Y（朝南）；NoClose 行向 −Y、字顶 +Z、法线 −X（朝西），无镜像。
  - 回读 GLB 24 个对象（含 8 个文字对象，Font 曲线已转网格），无 Error/Traceback，DONE di-signs；.glb 904,408 B（旧 144,116 B，文字字形网格所致）。
  - N 簇取景：新增 `_subdivide_flat_row`（扁平簇最长边 > 4×次长边时按 0.5m 间隙拆成单块牌子簇；N 簇 23 个对象、沿墙 12.24m 拆成 Warn + Num1–Num6 共 7 个子簇，E 簇保持 1 个，总共 8 张簇图达上限）；新增 `_flat_direction`（沿簇薄轴从牌面一侧取景、略带仰角；朝向投影接近 0 时改朝场景原点）。干跑验证：相机距牌 Warn/E 1.30m、Num 0.46m（旧 20.5m），按 50mm 镜头、1280 宽换算牌宽约 820/928px，均 ≥150px 目标。`py_compile` 通过。
  - 遗留：dist 场景 .glb 仍是旧件拼的（含占位色块、无文字对象），需刷新；牌面像素数（820/928px）是干跑换算估算，未经真实渲染图确认，最终可读性以复核 run 的簇图为准；本次推送触发的 run 45094589856 是 Godot verify + export，blender-previews 是否也在 HEAD 4a82fafc 上触发了待第六轮复核确认（未触发则需手动 dispatch）。

- 2026-11-23 10:19 CST 第六轮渲染复核（run 45094589895，HEAD 4a82fafc）：success（47 分钟，6 个 job 全绿），blender-previews run 存在（不是推送工人汇报的 Godot verify run 45094589856）。dist artifact 13 张 = 5 主图 + 8 簇图，簇数量与路径均正确；13 张全部 1280×720 真 PNG，无黑帧，品红全 0。**结论：未通过，有必须修的问题。**
  - **文字比牌子大 2 倍以上、全部溢出牌面（8 张簇图系统性缺陷）**：Warn“高压危险”四字比红牌宽约 2 倍，“高”和“险”完全悬在牌外；Num1 的“1”只剩一根竖条、无法辨认；E 两行“禁止合闸 / 有人工作”严重溢出白牌、互相重叠，字高约为牌高的 2.5 倍；Num2–Num6 字高约牌高的 2.5 倍、上下溢出。文字本身确实渲染出来了（字形正确，不是缺字），但尺寸完全不对。最可能的原因是 Text 对象的 size/scale 没按牌面尺寸换算（或用了默认 1m 字号、未缩放适配牌面）。修法：按每块牌的实际宽高缩放 Text 对象，让文字落在牌面内并留边；Num 牌数字约为牌高的 60–70%。修复任务已派。
  - **Runner 上字体外部路径不存在（日志 Error/WARN）**：`Error: Unable to pack file, source path '/home/runner/work/campus-vpp-demo/campus-vpp-demo/tools/fonts/NotoSansSC-static.ttf' not found`；`WARN vfont_get_data: Font file doesn't exist: //../../../tools/fonts/NotoSansSC-static.ttf`。本轮字形仍正确渲染，说明字形数据很可能已 pack 进 .blend（或走了别的回退），但外部路径引用是断的，是隐患。修法：确认字体已 pack 进 .blend（或把字体文件放进仓库正确相对路径、改相对引用），并让日志不再出现该 Error。
  - 可接受：N 簇按单块牌拆分已生效（8 个子簇、每簇 3 个对象、路径正确）；相机实际距离（1.92m / 0.57m）与干跑值（1.30m / 0.46m）有出入，但牌面在画面中占比正常，不影响结论；主图抽查 2 张通过、无回归。

- 2026-11-23 10:26 CST di-signs 文字溢出修复完成（工人 4ec65f94，commit `ec12509b`）：**根因不是尺寸算错，是字体文件没在仓库里**。本地实测修前 .blend 里 8 个文字尺寸本来就是对的（Warn 0.42×0.10 占牌宽 70%、Num 高 0.075 占牌高 62.5%）；隔离复现（把 .blend 拷到无字体文件的目录打开，模拟 runner）同样 size 下 Warn 宽 1.1995m（牌面 2.00 倍）、Num 高约 0.20m（牌面 1.65–1.68 倍），与第六轮复核完全吻合——Blender 4.2 静默用内置 Noto Sans CJK Regular 替代，同样 size 下字形大 **约 2.85 倍**。查库确认 `tools/fonts/` 里只有 `.gdignore`，`NotoSansSC-static.ttf`（10,595,948 B，Noto Sans SC Thin、UPM 1000）根本没推上仓库。修复：字体推上仓库＋`VectorFont.pack()` 打包进 .blend（双保险），隔离目录打开 8 个文字尺寸全部恢复正确、无字体报错；另把唯一真超标的 NoClose 总高 0.34→0.28m（占牌高 70%）；脚本新增 8 项 `text check OK` 硬校验＋字体打包确认。重出 di-signs.blend 11,415,596 B、di-signs.glb 904,316 B，回读 24 个对象、8 个文字对象齐全，GLB 内文字尺寸与 .blend 一致。一次 push-files 推 4 文件（.py/.blend/.glb/字体），commit `ec12509b`，触发 blender-previews run **45100150060**（in_progress，未等出图，待第七轮复核）。
  - **dist 场景仍是旧件拼的**（2026-11-22 15:31 用旧版 di-signs.blend 拼成），已派 dist 刷新工人（94bcf0eb）重跑 `assets/blender/scenes/dist.py` 刷新 dist.blend/dist.glb 并推送，待回报。
  - 附带教训：以后改 `tools/fonts/` 或重跑不带打包的旧脚本，字体缺失溢出会复发；现脚本已内置打包＋硬校验。
- 2026-11-23 10:31 CST dist 场景刷新完成（工人 94bcf0eb，commit `0268b464`）：重跑 `assets/blender/scenes/dist.py`（append 最新 di-signs.blend md5 `dbf6fcbe…`，纯 export-only、无本地渲染），`DONE dist`，日志零 Error/Traceback（`assets/blender/scenes/dist-refresh-20261123.log`）。新 dist.blend 17,422,756 B（旧 6,872,100 B，变大主因字体打包进 blend）、dist.glb 4,820,504 B（旧 4,060,188 B）。回读 **375 个对象**（上次 379，少 4 个全部来自 di-signs：旧版 28 个对象→新版 24 个，其余四件 kept 数与上次一致 walls 17 / cabinets 30 / transformer 76 / busbar 228，**不是拼装丢失**）。文字尺寸逐项核对与修复报告一致：Warn 0.42×0.10、NoClose 0.343×0.28、Num1–6 高 0.075，文字对象 8 个齐全；字体数据块 `Noto Sans SC Thin` 在 dist.blend 内 packed=True。两文件一次提交推上仓库，dist.blend 17.4MB 未触约 26MB 的 422 上限，触发 blender-previews run **45100689015**（queued，未等出图，待第七轮复核）。
- 2026-11-23 11:21 CST 楼体 B 组烘焙版推送完成（工人 cada6cae）：5 批共 189 文件一次成功、无 422、无遗漏——gym 21 文件 commit `074055bb`、lab 39 文件 `fa21da0f`、tower 45 文件 `3b4a8017`、canteen 36 文件 `c49e09ac`、dorm 48 文件 `5d338d50`（每批 .py+.blend+.glb+全部贴图，贴图共 174 张）。最新 run **45105477296**（Blender previews #41，head `5d338d50`，queued，未等出图）。总览最终刷新另一路进行中（工人 d644ce2d）。
- 2026-11-23 11:30 CST 总览最终刷新完成（工人 d644ce2d）：`assets/blender/scenes/overview.py` 无需改动（19 件全部就位且均为最新版时间戳，排除逻辑与上次一致），setsid nohup 单进程错峰约 3 分钟跑完（上次 17.7 分钟是 20 多个并行进程挤占所致），`DONE overview`，日志零 Error/Traceback（`assets/blender/scenes/overview-refresh-20261123.log`）。新 overview.blend 51,360,304 B、overview.glb **102,672,808 B**（上次 25,914,236 B，暴涨主因 B 组烘焙贴图嵌进 .glb，各件 .glb 之和约 102MB）。回读 **4837**（脚本内置 VERIFY 与独立回读一致，4 个 `OV_ASSEMBLY_*` 齐全），差额 +8 全部来自 ov-road-main（src 36→44、kept 33→41，含环路中心线等新增对象），其余 18 件 kept 数与上次逐件核对完全相同。**推送失败（各试一次，未重试）**：overview.glb 102.7MB 与 overview.blend 51.4MB 在建 blob 步骤均报 HTTP 422 "input too large"，无 commit、无 run；仓库 HEAD 仍为 `5d338d50`，仓库里 overview.glb 仍是旧版 25,914,236 B。**需父 agent 决策**：①把 .glb 瘺身（贴图不内嵌、或降分辨率）后再推；②走本地 clone + git push（需另行安排凭证与通道，本机无此连接器的 git 推送通道）；③接受仓库里的总览 .glb 暂留旧版。另：文档里旧写的仓库 HEAD（`5cb5f01`）已过时，实际 HEAD 为 `5d338d50`。
- 2026-11-23 11:37 CST **第七轮渲染复核通过 ✅**（工人 f3497ec9，run 45100150060 + 45100689015，两 run 均 completed/success）：两 run 各 6 个 artifact、54 张 PNG，全部下载到 `~/workspace/review-r7/`。**di-signs 8 张簇图全部通过**：上一轮文字比牌子大 2 倍全部溢出已修好，Warn 字宽/牌宽 0.67、字高/牌高 0.23，NoClose 两行总高/牌高 0.69，Num1–6 字高 0.61–0.66，全部落在牌面内、四边留边。**dist 场景无回归**：抽查 di-cabinets/di-transformer/di-busbar/di-walls/di-signs 均正常；两 run 13 张 dist 图逐像素对比，仅 di-cabinets.png 完全相同、其余差异 ≤0.002%（PNG 重编码噪声级）。**品红 0**：108 张逐张统计品红像素全部 0.0000%。**尺寸与黑帧通过**：108 张全部 1280×720 真 PNG，黑像素占比最高仅 0.27%（画面内深色区域），无黑帧。无必须修的问题。

- 2026-11-23 23:30 CST 返工审计与推送核对（审计报告 `~/workspace/vpp-audit/texture-repo-audit-20261123.md`，审计时间 2026-11-23 23:03 CST、当时 HEAD `e56912f0`）：审计发现 36 张新烘 .jpg + 20 个新 .blend 待推，charge/pv/storage 三处场景 .blend 是 11-22 旧快照待刷新。**核对结果（gh.py 查询，HEAD `c046118`，2026-11-23 23:26 CST）：36 张贴图已全部随 commit `c9390d6`（2026-11-23T15:16:12Z）入仓；20 个新 .blend 已全部入仓（19 个在 `c9390d6`，st-cables.blend 在 `13c960b`，2026-11-23T15:21:41Z）。场景刷新：pv 场景 .blend 本地已刷新（15:14 UTC，881 对象 / 25 种材质，DONE pv）并随 `c9390d6` 入仓；charge / storage 场景 .blend 本地已刷新（charge 15:25 UTC，306 对象，DONE charge；storage 15:20 UTC，269 对象，DONE storage），仓库仍是 11-22 旧版、待推；pv / charge / storage 三处场景 .glb 仓库仍是 11-22 旧版、待推。光伏 3,094 材质问题（3,094 个 primitive 各带材质槽，见 pv-scene-pbr-20261123.log）：已通知光伏路重出时合并，待核对。教室 tevy 换件 5 个提交 `cf0d432`、`c2d99fa`、`e2bce23`、`5d0e1fc`、`c046118` 已入仓（见 §3.4、§4）。
- 2026-11-23 23:58 CST 池塘草坪返工推送完成（commit `8390649`）：ov-lawn.py 撒点排除水面椭圆（+1m 边距）+ overview.py 删除 -0.5m 下移，池塘草坪 4,662 叶、42.1 叶/m²、叶面 Y 0.05–0.40m、水面椭圆内 0 叶；另两片草坪（50,568 / 25,330 叶）与真草 8,140 株分毫不差；总览重刷回读 13,036 对象、零 Error/Traceback。7 文件一次提交（ov-lawn .py/.blend/.glb、overview.py、瘦身 overview.glb 36,459,020 B、瘦身 overview.blend 9,092,702 B、BLENDER_MODELS.md），仓库核对 HEAD 与三处大小/SHA 一致。本次推送触发新的 blender-previews run，最终渲染验收应盯新 run。瘦身口径变化见 §10（normal/mr 改 256px）。

- 2026-11-23 晚间推送记录（gh.py 核实，main HEAD `1b3ad57`，commit 时间 2026-11-23T15:59:20Z，查询于 2026-11-24 00:02 CST / 2026-11-23 16:02 UTC；以下 8 个提交均在 main 历史前 20 内）：
  - `8805b66`（15:34:37Z）：Blender 返工——PV+储能+充电 12 个件的 PBR 贴图脚本 + pv/charge 场景材质去重（scenes/pv.py、scenes/charge.py，append 后去重）。
  - `7bcd65c`（15:35:15Z）：刷新 PBR 件 GLB（pv 3 件、storage 4 件、charge 4 件）。
  - `1f36cb2`（15:35:48Z）：刷新 storage + charge 场景 .blend/.glb，charge 材质去重 117→24；pv 材质 3,094→25（场景重出实测 25 种，见 §4；去重修法在 scenes/pv.py）。仓库核对（gh.py contents）：pv.glb 19,774,596 B（另经 `7227239` 推送）、charge.glb 7,105,356 B、storage.glb 7,237,164 B；pv/storage .glb 与本地重出一致，charge.glb 为去重后版本。
  - `31a52648`（15:42:02Z，Godot 侧）：储能风扇落到柜顶（盘底 2.555m）+ 雨天/暴雨隐藏阳光射线与 V2G 弧线（pv_factor>0.30 门控）。
  - `013e1369`（15:47:41Z，Godot 侧）：回退分支修补——S1 储能外壳落基座顶（2.85→2.60，屋顶/状态灯同降），S3 车身落垫顶（0.85→0.60，车舱/SOC 条同降）+ 每车 4 个车轮，S5 顶层窗钳制 wy≤h-0.75（窗顶 h-0.05，不再埋入屋顶板）；verify 70/70。
  - `49549323`（15:53:54Z，Godot 侧）：储能内景对齐 GLB——灯带 y 5.415 贴屋顶顶、PCS 风扇 X 移 2.4 避 FanDisc、流光点改 3 柜中心/行程 0.3–2.5；验证 +10 项。
  - `8390649`（15:58:56Z）：池塘草坪返工（详见上一条：4,662 叶、42.1 叶/m²、水面椭圆内 0 叶；瘦身总览 .glb 36,459,020 B / .blend 9,092,702 B）。
  - `1b3ad57`（15:59:20Z）：文档提交——把 8390649 池塘返工记入 BLENDER_MODELS.md §9（即上一条）；此即本次查询时的 main HEAD。
  - 草密度核查实测（Godot 侧汇报）：总计 102,901（程序化 94,761 叶、约 42/m² + 真素材 8,140 株）；22,500 一数口径**待确认**（丛 vs 叶未分清），不采用、不编结论。

- 2026-11-24 00:30 CST P0/P1 材质补挂完成并入仓，commit `060877f`（全 SHA `060877f4b07ef20114eddd2d4e4af40534340786`，commit 时间 2026-11-23T16:30:17Z；gh.py 查询于 2026-11-24 00:31 CST，main HEAD 即 `060877f`，父提交 `e706c82`；32 个文件，+446/−6）：
  - 8 个材质全部完成：PV_FrameSilver（#C0C5C9）、PV_Busbar（#7E93A8）、PV_RailSteel（#B9BEC2）、PV_LegSteel（#6E7478）用 Poly Haven blue_metal_plate 三件套染色；3 台车共用同一参数化清漆（Metallic 0.15 / Roughness 0.35、Coat Weight 1.0 / Coat Roughness 0.15，GLB 带 KHR_materials_clearcoat；ch-cars.py 注释：旧版 Roughness 连 Noise→MapRange，glTF 丢 roughnessFactor、Godot 里车漆归 1 全哑光，改回 0.35 固定值，只留 Bump）；Cabinet_Cap_Paint（#35483F）、Cabinet_Kick（#2E3F38）复用 cabinet rough/nor；Storage_Roof_ASSEMBLY_ADDED（#424A52，scenes/storage.py 总装脚本里改动）。
  - 4 件（pv-panels、pv-mount、ch-cars、st-cabinet 的 .py/.blend/.glb）+ 3 场景（pv、storage、charge 的 .blend/.glb）全部重跑重出，回读零 Error/Traceback，GLB JSON 全过；最大单 blob scenes/pv.glb 24,051,408 B，未触发 40MB 上限；PV_Glass 与 Storage_Shell 全程没碰、仍是 BLEND 无贴图。
  - 途中修掉两个坑：① 浅色染色翻车——tint_textures.py 原 tint 法按通道线性缩放有 4 倍钳制，染浅色时三张图染出来一模一样，改用比值压缩法（out = target × (src/mean)^0.5）重染，四张均值与目标色误差 ≤1；② 贴图重复嵌三份——_load_tex 按路径串匹配、绝对路径与已存 // 相对路径对不上，复用 rough/nor 时造 .001/.002 重复块，在 pv-panels.py 与 st-cabinet.py 里加了按 basename 复用已载入 image 的逻辑。
  - scenes/storage.py 在仓库里之前不存在，本次是以 added 状态入仓的（commit 文件清单：added `assets/blender/scenes/storage.py`）。
  - 仓库文件清单（gh.py contents，ref 060877f）：scenes/pv.glb 24,051,408 B、pv-mount.glb 9,787,184 B、scenes/storage.glb 8,623,960 B、scenes/charge.glb 7,105,712 B；scenes/pv.blend 15,323,932 B、scenes/storage.blend 11,886,071 B、scenes/charge.blend 3,376,684 B（与去重版同体积）；单件 pv-panels.glb 1,516,160 B、st-cabinet.glb 1,618,552 B、ch-cars.glb 543,252 B。新增贴图：pv-mount_textures 6 张（rail/leg × color/nor/rough）、pv-panels_textures 2 张（frame/busbar color）、st-cabinet_textures 2 张（cap/kick color）、storage_textures 3 张（roof color/nor/rough）。**已核实（2026-11-24 00:32 CST）**：pv-panels 与 st-cabinet 只新增了 color 图，rough/nor 确为复用同套贴图、无新增文件——commit `060877f` 文件清单（gh.py，32 个文件）里 pv-panels 只新增 `frame_color.jpg` / `busbar_color.jpg`，st-cabinet 只新增 `cap_color.jpg` / `kick_color.jpg`；本地脚本实测：pv-panels.py:207/209 的 frame/busbar 均 `add_pbr(…, "panel_rough.jpg", "panel_nor.jpg")`（复用 v3 板面 blue_metal_plate 的 rough/nor），st-cabinet.py:149/151 的 cap/kick 均 `add_pbr(…, "cabinet_rough.jpg", "cabinet_nor.jpg")`（复用 cabinet 的 rough/nor）。两处“待核”均已核实，无遗留。
  - §4 体积已同步更新为本次重出后仓库核对值（见 pv/storage/charge 三行）。遗留：§3 里 pv-panels、pv-mount、st-cabinet、ch-cars 四行仍写 Bump-only，已过期，本次任务限定只补 §9 与 §4 体积，未改表，待下次顺手改。

- 2026-11-24 01:23 CST 配电房标牌返工（run 45219977015 的 05-dist 目视：“高压危险”第 3、4 字残缺，放大看是“高压危□金”）：
  - **根因不是字体缺字、不是贴图/UV（本件文字是真实 Font 曲线对象、无贴图）——是 Blender 4.2 的 Font 曲线填充把 NotoSansSC-static.ttf（Thin 全量）的字形算坏了**。字体本身没错：fontTools 核查 14 字全覆盖、FreeType/PIL 渲染 危/险与系统思源完全一致；但同一文本、同一 Blender、只换字体：static 版 Warn 前盖 1442 多边形、最大单片占总面积 8.6%，高/压/危/险全部算坏（孔洞填实、笔画被巨型三角桥接、危中间一横缩成发丝、险的阝只剩竖杆）；系统 NotoSansCJK-Regular.ttc（CFF 版）767 多边形、最大单片 2.6%，四字全对；assets/fonts 子集版同样算坏（高压最大单片 13.4%）。尺寸校验全绿也拦不住（上一轮只量尺寸的复核就是这么漏过去的）。
  - **修复：换字体**。从系统 TTC 第 2 面（SC）抽出 Noto Sans CJK SC Regular，用 fontTools pyftsubset 只留本件 19 字（高压危险/禁止合闸/有人工作/0-6），`tools/fonts/NotoSansCJKSC-signs.ttf`（5,876 B，OFL），di-signs.py 改指新字体；旧 static 字体文件留仓不动、仅停用（其余脚本无一用字体，缺陷只影响 di-signs 一件）。脚本新增字形三角化硬校验：Warn/NoClose 前盖单多边形面积 ≤ 总面积 5%（好字体实测 2.6%/1.7%），转网格量前盖、原对象保持 FONT 曲线。
  - **验证**：重跑 di-signs.py，`DONE di-signs`，零 Error/Traceback；尺寸与旧版逐项相同（Warn 0.42×0.10、NoClose 0.343×0.28、Num 高 0.075）；字形校验 Warn 0.026、NoClose 0.017；GLB 回读 24 对象、8 文字齐全；新 di-signs.glb 前盖光栅化目视：高压危险/禁止合闸/有人工作/1–6 共 19 字全部完整清晰；GLB JSON 24 primitive、0 无材质。dist 场景重跑 `assets/blender/scenes/dist.py`，`DONE dist`，回读 375 对象（walls 17 / cabinets 30 / transformer 76 / busbar 228 / signs 24，与上次一致），dist.glb 内 Warn_Text 网格与新 di-signs.glb 逐项一致（3256 顶点 / 3164 三角 / 前盖 780（前盖三角数；Blender 源文件里同一前盖计为 767 个多边形，三角化后 754 三角 + 13 四边形 = 780，口径一致）），GLB JSON 375 primitive、0 无材质；两 .blend 内新字体均 packed=True。体积反而变小：di-signs.blend 11,415,596→825,524 B、di-signs.glb 904,316→481,196 B、dist.blend 18,463,980→7,873,908 B、dist.glb 16,380,284→15,957,168 B。**视觉验收待 Actions 出图**（新 run 的 05-dist 与 di-signs 簇图）。

- 2026-11-24 04:4x CST 返工 R1 推送完成（commit `d74ab2a6`，32 文件一次提交）：di-walls（.py/.blend/.glb + 15 张重烘焙图：天花板顶面与墙面纹理加重）、ch-cars（.py/.blend/.glb：Coat Roughness 0.15→0.05、底漆 0.35→0.25）、ov-parking（.py/.blend/.glb：补 Coat Weight 1.0 / Coat Roughness 0.05、车窗 Bump）、st-fence（.py/.blend/.glb：柜体复用 st-cabinet 锈蚀贴图、地面复用 st-base 混凝土贴图，无新素材）、dist/charge 场景（.blend/.glb 重刷：dist 回读 375、charge 回读 306，逐件与上次一致）、BLENDER_MODELS.md。仓库 HEAD 与 dist.glb（16,192,560 B）/ ov-parking.glb（3,645,908 B）大小核对一致。推送触发新的 blender-previews run，最终渲染验收盯新 run，只看返工 4 件 + 回归（di-signs 字形、st-cabinet 锈蚀、pv 车漆对照）。遗留：overview 场景未重刷（ov-parking 车漆未进总览场景 GLB；瘦身脚本 /tmp/slim_glb.py 已丢，需重写，见 §10 口径）。

- 2026-11-24 04:36 CST 总览停车返工重刷 + 瘦身脚本重写入仓（commit `54fad3d3`；首推遇 HEAD 前进 422 not fast-forward，重读 HEAD e49d2d00 后重试成功。注：BLENDER_MODELS.md 与父提交 e49d2d00 的同文件字节一致，故 commit 文件清单只列其余 4 件，文档内容已在树内）：
  - 总览重刷：重跑 `assets/blender/scenes/overview.py`（脚本本身未改动，与仓库字节一致，append 的就是最新 R1 ov-parking.blend），20 件 kept 数与上次逐件相同（ov-parking 233/233，R1 只改材质参数），回读 13,036，零 Error/Traceback（`assets/blender/scenes/overview-refresh-parking-20261124.log`）；完整版 .glb 121,570,548 B / .blend 64,546,472 B 留本地（Godot 整合输入，不推仓）；GLB JSON 实测 202 种材质、427 贴图 0 缺失、KHR_materials_clearcoat 在列（3 种车漆）。
  - 瘦身脚本重写：`/tmp/slim_glb.py` 已丢，重写为 `assets/blender/tools/slim_glb.py`（+ `assets/blender/tools/verify_slim.py`），口径见 §10（color 512px JPEG q80、normal/mr 256px PNG、草叶 alpha 永不 JPEG、双槽贴图按 normal）；瘦身版 .glb **36,044,776 B** / .blend **9,093,786 B** 已入仓，仓库核对大小/SHA 一致（glb `bff6e1e3…`、blend `4ce13bc2…`）；瘦身 GLB JSON 对比（节点/访问器/材质槽全同）+ Blender 回读 13,036 对象、0 无材质 primitive；瘦身 .blend 原目录打开 13,036 对象、465 贴图、缺失 0。临时瘦身文件推完已删，本地完整版未动。
  - 推送触发新的 blender-previews run，最终渲染验收盯新 run（总览车漆 + 回归）。

- 2026-11-24 04:2x CST di-signs 板面凹凸调弱（run 45227196322 最终渲染验收非阻塞观察：板面波浪状凹凸过重、像皱箔，字形本身完整）：
  - **根因**：`make_material` 里 4 种牌面材质（Sign_Red/White/Yellow/Blue）共用同一 Bump 节点，Strength 1.0 / Distance 0.1，由 scale 2.5~3.5 的粗噪波驱动；Distance 0.1m 对 0.6m 的牌面太大，粗噪波被放大成肉眼可见的波浪起伏；文字对象共用同材质，字形表面也被带皱。无 normal 贴图、无置换，只有 Bump。
  - **改动**：只改 Bump 两值 Strength 1.0→0.3、Distance 0.1→0.02（凹凸幅度约为旧值 1/17）；噪波尺度、粗糙度映射、字体、字形、字号、板面尺寸与颜色全不动。
  - **验证**：重跑 di-signs.py，`DONE di-signs`，零 Error/Traceback；字形校验 Warn 0.026 / NoClose 0.017（≤5% 判据，与好字体一致）；尺寸 Warn 0.42×0.10、NoClose 0.343×0.28、Num 高 0.075，全与旧版相同；GLB 回读 24 对象、8 文字齐全；.blend 回读核实 4 材质 Bump 均为 0.3/0.02。dist 场景重跑 `assets/blender/scenes/dist.py`，`DONE dist`，回读 375 对象（walls 17 / cabinets 30 / transformer 76 / busbar 228 / signs 24，与上次一致），dist.blend 内 4 材质 Bump 同为 0.3/0.02。体积：di-signs.blend 825,524 B、di-signs.glb 481,196 B、dist.blend 8,109,300 B、dist.glb 16,192,560 B（与返工 R1 版同体积——Bump 节点不进 glTF，GLB 字节未变，渲染看 .blend）。
  - **视觉验收通过 ✅**（run 45258042699，success；artifact `blender-previews-dist`，本地 `~/workspace/review-bump-20261124/dist/`）：di-signs 簇图 8 张逐张目视——Warn 红牌基本平整、“高压危险”四字完整清晰；E 白牌平整、“禁止合闸 / 有人工作”两行可读；Num1–6 数字 1–6 全部完整；与返工前原图（`~/workspace/review-rework-r1/acceptance/dist/`）逐张对照，皱箔感明显减弱——旧图蓝牌深波纹、白边框重皱、字形本身也被带皱，新图只剩轻微柔和明暗起伏（蓝牌稍明显，红/白牌近乎平整），未变全平。回归抽查 di-transformer（4 台变压器、散热片、套管正常）、di-cabinets（6 台柜、仪表窗、把手正常）无异常。

- 2026-11-24 04:4x CST 返工 R2 推送（commit `717c7728`，6 文件）：ch-cars / ov-parking 的 .py/.blend/.glb——.blend 改留 Nishita 天空世界（仰角 50°）供 EEVEE 清漆反光，GLB 内容未变（ov-parking.glb blob 与 R1 相同）。触发新的 blender-previews run，车漆两件待新 run 出图再验。另：R1 run 45251171902 的 dist/charge/storage/pv/classroom 5 组已 success，仅 overview 组仍在跑；R1 目视验收：di-walls 通过（顶面云纹清晰、墙面加重）、st-fence 通过（地面混凝土纹理、柜体锈蚀纹理）、ch-cars 未通过（新旧图逐像素几乎相同，涂层不可见——R2 已修）。

- 2026-11-24 06:0x CST 返工 R3 推送（commit `06a7631a`，4 文件：ch-cars / ov-parking 各 .py/.blend；两件 GLB blob 与仓库完全相同，未推）：
  - **根因（先查后改，本地最小复现 320×180 像素统计，未出预览图；复现与 R2 图逐项吻合：整体均值 (33,32,33)、顶缘 (61,59,52)、底缘纯黑、纯黑像素 35.1%）**：①世界接线正确（Nishita→Background→Output，Strength 1.0）、render_max 设 film_transparent=False——不是接法问题，R2 的两个候选（film 透明/世界未接背景）均已证伪；②自动相机俯角约 28°、50mm 镜头垂直视场约 23°，顶缘视线仍低于地平线约 16°——天空根本不在画面内，背景下黑上淡暖（R2 图顶缘 69,67,59）只是近地平线辉光；③EEVEE 里世界直接进清漆环境反射（黑世界→车漆深饱和蓝 (27,95,139)/深红 (143,56,48)、白世界→洗白），反射探针（烘焙/不烘焙）像素变化仅 meanAbs 约 1.0——探针不是缺失环节，R2 的“天空没进镜面反射路径”实为“天空在镜面方向上是均匀淡色”；④平板车身 + 均匀淡天 → 各面只映出单一淡色，看起来全哑光；⑤方向太阳打进镜面角时蓝车顶 183→246（镜面路径是通的），但 Coat 0.05 的窄瓣一次只能亮一辆车（三车顶镜面方位角 123°/132°/143°）。R1 的“清漆无物可映”只对了一半：有物可映，但映的是无结构的均匀淡天。
  - **修法（只改 .blend 预览环境，不动材质、不动 render_max、不进 GLB）**：留 Nishita 世界 + 暗色预览地面 `Ground_PreviewOnly`（80m、线性 0.05、粗糙 0.95，填地平线下黑洞；render_max 取景排除、场景拼装排除）+ 东南太阳（能量 3.5、旋转 (50°,0,30°)，与 render_max 默认同向，可见面光照不变；render_max 见 .blend 已有灯光不再补太阳）+ 西北高处 24×2m 亮条灯（RECTANGLE 面光源、能量 15000，车顶镜面方向的“摄影棚柔光条”；ch-cars 在 (20,-45,18) 瞄 (43,-76,1)，ov-parking 同相对位置在 (-53,-59,18) 瞄 (-30,-90,1)）。对照实验：600 能量面光源仅 +3（太弱）、40000 全车顶 245+ 过曝、24×2/15000 最均衡；方向太阳单车过曝 246、三车不可兼得。
  - **本地验证（走真实 render_max 路径，320×180 像素统计）**：ch-cars 蓝车顶行 184→209 渐变光带（R2 为均匀 183）、红车顶 229、白车顶 225，纯黑像素 35.1%→0；ov-parking 灰/蓝/红车顶均值 (205,212,219)/(244,246,249)/(221,188,193)，三行均有亮度起伏（蓝车顶 219→249→232）。回读：ch-cars 201 对象（198 车 + 地面/太阳/柔光条）、ov-parking 236 对象（233 + 3），零 Error/Traceback；GLB JSON 清漆 factor 1.0 / roughness 0.05，blob SHA 与仓库一致。
  - 触发 blender-previews run **#45275914559**（run #78），待出图验收：只看 ch-cars 与 ov-parking 两张 + 回归（di-signs、st-cabinet、pv-panels）。
  - **复验通过 ✅**（2026-11-24 07:06 CST，run completed/success，约 63 分钟）：ch-cars 蓝车顶行 186→208 渐变光带、红车顶 229、白车顶 224，纯黑像素 35.5%→0，与 R1 图平均绝对差 94.933；ov-parking 蓝车顶 198→249 亮带、灰车顶 139→207、红车顶 144→221，与 #72 原图平均绝对差 98.534；回归 di-signs 与 R2 图逐像素相同（0.000，Warn 四字清晰）、st-cabinet 0.000、pv-panels 0.002。遗留弱项：车窗只有纵向天空渐变（蓝车侧窗顶部 (200,214,232)/底部 (101,142,181)）、一眼仍是淡灰绿平板、无亮带——竖直面镜面方向映不到柔光条，改玻璃材质会进 GLB，需另定。

- 2026-11-24 05:4x CST 取景修补（验收 run 45227196322 / #72 非阻塞观察：cl-ac、ov-flag-lamp、pv-mount、ch-piles 取景过远/对比低，细节无法核验）：
  - **根因**：`tools/render_max.py` 按整件包围盒定相机距离（`_fit_camera`，margin 1.10）；四件主体细小且分散在很大的包围盒里——cl-ac 两台空调分处教室对角（包围盒对角 11.72m）、ov-flag-lamp 375 杆件散布全校（对角 303.91m）、pv-mount 三屋顶支架阵（对角 89.6m）、ch-piles 4 台桩排成 11.4m 长行——整件取景下主体只占画面约 5% 以下。模型本身没问题，纯渲染脚本 framing 问题。
  - **改动：只改 `tools/render_max.py` 一个文件**（commit `ceeb81df`，父 `89a06cf8`，仅该文件；改前本地与仓库 blob `64dbc665` 核对一致；`.py`/`.blend`/`.glb`、6 组 matrix、产物规格全不动）：新增白名单 `_DETAIL_FRAMING = {cl-ac, ov-flag-lamp, pv-mount, ch-piles}` + `_DETAIL_BRIGHT_BG = {pv-mount}`；`_ensure_camera` 对白名单件跳过内置相机保留检测、走新增 `_frame_detail_view`：取最大簇（扁长行先 `_subdivide_flat_row` 拆单件），主视图只拍该簇、**不增发分镜**；`_ensure_world` 仅对 pv-mount 把深灰世界（lum 0.0509）提亮为天蓝；cl-ac 不提亮（白空调在深灰底上对比更好）。其余 40 件走原逻辑，一字未动。
  - **干跑验证**（本地 Blender 无头，只算相机参数、一张图未渲染；`/tmp/framing_probe*.py`）：cl-ac 相机 24.42→5.98m、框内占比 0.0458→0.2848；ov-flag-lamp 600.26→49.38m、0.0023→0.0454（最大簇即南门 3 根旗杆 + 附近路灯，42 对象）；pv-mount 170.95→69.33m（最大簇 LAB 屋顶阵列）、0.2153→0.4574，世界亮度 0.0509→0.7596；ch-piles 整件 19.47m→单桩取景（框内占比 0.131→0.243）。相机离模型最近距离均 ≥4.5m（cl-ac 5.32m、ov-flag-lamp 27.72m、pv-mount 29.3m、ch-piles 4.56m），未怼进模型。对照件干跑参数与改前完全一致（ov-bldA 内置相机占比 4.8559、pv-panels 整件 170.92m/0.2035、st-cabinet 15.61m/0.6359、di-cabinets 内置相机 0.2247）。
  - **Actions**：run **#75 / 45259258530**（HEAD `ceeb81df`），6 组全部 success（pv/charge/classroom/storage 约 20:46Z、dist 约 21:1xZ、overview 约 21:39Z，全程约 74 分钟）；产物 **55 张、1280×720**，与旧版张数一致（overview 20 / pv 7 / storage 5 / classroom 6 / charge 4 / dist 13，含 di-signs 8 簇图 + pv-inverter 3 簇图）。
  - **验收**（逐张目视，新图在 `~/workspace/review-rework-r1/framing-fix/`，旧图对照 `~/workspace/review-rework-r1/acceptance/`；非背景像素占比为角点背景色 ±40 阈值实测）：cl-ac 单台空调占满画面高度 77%（旧 26%）、非背景像素 1.2%→9.8%，前面板/显示屏/顶栅/铜管/底座均清晰，无过曝无裁切；ov-flag-lamp 3 根旗杆 + 红旗 + 2 根路灯占满画面高度 71%（旧 47%）、非背景像素 0.01%→1.65%，旗面纹理可读，无裁切；pv-mount LAB 阵列横梁/支腿/压块网格清晰可辨（旧图支架与背景灰度差 <40、基本融进背景）、非背景像素 ~0→2.1%，背景已提亮，无过曝、主体完整；ch-piles 单台桩占满画面高度 76%（旧 25%）、非背景像素 2.1%→4.4%，屏幕/绿灯/充电枪/枪线/顶盖/底座均清晰，无过曝无裁切。**4 件全部通过**。
  - **取舍**：主视图只含一件主体——另一台空调、其余 3 台桩、其余两屋顶支架阵列、其余路灯不在主图内；数量与全校/全屋顶位置仍以旧整件图 + 模型文件为准，主图只负责细节核验。pv-mount 左下角有相邻屋顶阵列一角入画（被框边裁切），主体 LAB 阵列本身完整，未动——属构图小瑕，不返工。
  - **回归抽查**：随机 4 件目视正常（pv-panels、cl-desks、ch-cars、st-cabinet）；另 ov-trees、ov-bldA 新旧图逐像素对比 mean|diff| = 0.00，pv-panels、cl-desks、st-cabinet 同为 0.00——其余件取景未被带坏。

- 2026-11-24 06:1x CST 总览地面偏淡 F4 + 树木灰白 F5 根因调查修补（验收 run 45261531067 拼装总览全景）：
  - **F5 根因（Blender 侧，已证实）**：6 种树冠 + 1 种树干材质把灰色噪波图（LeafNoise/BarkNoise，均值 #7C7C7C）直接当 baseColorTexture 导出、无 baseColorFactor；绿色只存在于 .blend 里的 ColorRamp 节点，glTF 无法表示，导出即丢。Blender 单件预览是绿的、Godot 总览里是灰白锥体，两边不一致即由此而来。树干同病（灰噪波→棕褐 Ramp）。
  - **F5 修复（只改 Blender 侧）**：`assets/blender/overview/bake_trees.py` 把每档 Ramp 烘成 sRGB 彩色噪波贴图（噪波 t→三档线性插值→线性转 sRGB；7 张 `ov-trees_textures/Crown_*_color.png` + `Trunk_Bark_color.png`，均值与各档 mid 色差 ≤1，如 Crown_Perimeter #4F8A3E 对 #4E8A3F）；`ov-trees.py` 的 Base Color 改直连烘焙图（Ramp 节点删除），灰噪波图只留给 Bump。重跑 ov-trees.py：回读 292 对象、零 Error/Traceback；新 ov-trees.glb（386,908 B）JSON 实测 7 材质 baseColor 贴图均已绿（树冠 #4F8A3E/#5D9A48/#5F9A45/#71A852/#7CA64C/#8CB55B，树干 #6B4E30）。
  - **F4 根因（Godot 侧光照，非贴图）**：地面贴图实测均值正是 #69B45D（`GroundGrass_color`，UV 85×85 平铺、法线朝上均正确）；同 run 回退帧（程序化平色地面 #4F9D43、粗糙度 0.85、无任何 GLB）一样洗白成 (130,255,164)、G 截顶；跑道（采样实测 #B8543F）与楼体基本正确、暴雨帧地面色相正确只是偏暗。晴天总光照约 2.3×（太阳 1.38 + 天光 0.73，偏蓝的天光是主因），地面粗糙度 0.26 的镜面反射不是主因（洗白在近/远处均匀、与掠射角无关；暴雨天光一暗即正常）。地面基色不动。
  - **F4 修复（只改 Godot 侧）**：`scripts/weather_system.gd`：太阳 `(0.18+1.2*daylight)`→`(0.18+0.65*daylight)`（晴天 1.38→0.83）、天光 `0.28+0.45*daylight`→`0.12+0.16*daylight`（晴天 0.73→0.28）、雾密度 0.0005→0.0002（`scenes/main.tscn` 同步）；标定目标晴天总光照约 1.1×，预测草地约 (112,191,112)，待新 run 截图实测复核。
  - **总览重刷 + 瘦身**：重跑 `assets/blender/scenes/overview.py`，回读 13,036 对象、零 Error/Traceback；完整版 .glb 121,831,988 B / .blend 64,568,788 B 留本地；GLB JSON 实测 202 材质 / 434 贴图（+7 烘焙图）、树冠贴图已绿、地面仍 #69B45D。瘦身（§10 口径）：.glb **36,070,084 B**（<40MB）、.blend 8,978,835 B；`verify_slim.py` 全绿（瘦身 GLB 13,036 对象 / 0 无材质 primitive；瘦身 .blend 13,036 对象 / 472 贴图 / 缺失 0）；瘦身后树冠贴图仍绿（JPEG q80 均值漂移 ≤1）、地面 #68B45C（漂移 1）。
  - **推送与验证（已填，run 45279712436 success）**：主推 `39346cfb` + 跟进 `aec109a5`（雾基线）；godot-verify run #81 success，artifact 17 图。F5 通过：树冠绿像素 11,920→26,016，均值 (91,183,129)，放大目视均为绿锥。F4 部分通过：回退帧平色地面 (129,252,164) G 截顶 93%→(105,226,136) 截顶 1%（R 恰好等于 SPEC 105，光照洗白已除），但 GLB 草地 (152,249,194)→(128,248,168)，G 仍截顶 85%、未进 SPEC ±15。残留根因（Blender 侧）：地面粗糙度 0.26（GroundGrass_rough 灰度 67.1，glossy 镜面反射蓝天；metallicFactor=0 已排除金属）+ 亮黄绿草叶档（Lime #A8C25D、YellowGreen #89A749）。收尾待做：地面粗糙度→约 0.85 + 亮草叶压暗，重出总览/重瘦身/推仓/新 run 复核。见 `~/workspace/review-rework-r1/godot-acceptance/ACCEPTANCE.md` 新节。
  - **F4 收尾修补（只改 Blender 侧，2026-11-24 07:xx CST，已推仓待新 run 复核）**：① `assets/blender/scenes/overview_textures/GroundGrass_rough.png` 整图缩放（×3.305，上限 255 钳制）：均值 67.1→**217.0（粗糙度 0.26→0.85）**，纹理起伏保留（24→79、131→255）；`GroundGrass_color` 均值仍 #69B45D、基色不动，`OV_ASSEMBLY_ground_mat` metallicFactor=0、粗糙贴图直连。② 亮草叶压暗 ×0.80（只改两档）：`ov-lawn_textures/Grass_Lime_color.png` 均值 (167.5,193.5,93.5)→(134.0,154.8,74.8)，`Grass_YellowGreen_color.png` (137.5,167.5,73.5)→(110.0,134.0,58.8)；六色加权均值 (107.6,164.7,80.9)→(101.0,156.9,77.3)；`ov-lawn.py` 的 `GRASS_COLORS` 两档 hex 同步改（#A8C25E→#869B4B、#8AA84A→#6E863B，仅初始值，渲染以贴图为准）。光照/雾/树冠一行未动。重跑 ov-lawn.py：零 Error/Traceback，草丛 50,568/25,330/4,662 叶与上次分毫不差，GLB 回读 8,269 对象；重刷总览：零 Error/Traceback，回读 **13,036** 对象（append 13,032 + 拼装 4）；完整版 GLB 内嵌 GroundGrass_rough G 通道 217.0、草叶贴图均值与改后 PNG 一致；瘦身（§10 口径）：GLB 121,839,788→**36,081,136 B**（<40MB），节点/访问器/材质槽全同，瘦身后粗糙仍 217.0、地面色漂移 ≤1.2、草叶漂移 ≤0.6；`verify_slim.py` 全绿（瘦身 GLB 13,036 对象 / 0 无材质；瘦身 .blend 9,013,739 B、13,036 对象 / 472 贴图 / 缺失 0）。推送文件：3 张贴图 + ov-lawn.py/.blend/.glb + 瘦身 overview.glb/.blend + 本文档 + PROGRESS.md（完整版 .glb/.blend 留本地未推）。待新 godot-verify run success 后下载截图复核（run #83 `45288051056` success，VERIFY-SUMMARY PASS=187 FAIL=0，artifact 17 图）**结果：F4 仍未通过**——晴天总览 GLB 草地均值 (128,247,162)、G 截顶 86.6%（#81 为 (128,248,168)/85%），中心草坪 (121,225,159) 与 #81 (121,227,163) 几乎相同；新旧总览逐像素对比 mean|diff| 仅 0.87、>10 的像素只 2.4%（集中在 y120–360 草坪带，草叶压暗确已生效、GLB 已换新），地面主体一分未动。**残留根因不在地面粗糙度**：回退帧（粗糙 0.85 平色地面、无 GLB）与 GLB 草地呈现同一量级抬升（基色→渲染 R +24、G +67、B +68，B 抬升最大），抬升与地面材质无关、与掠射角无关，源在 Godot 侧环境（天光/环境光向漫反射里加的蓝绿分量），须另开 Godot 侧调查，不在“只改 Blender 侧”范围内。树冠仍绿，无其他回归。详见 `~/workspace/review-rework-r1/godot-acceptance/ACCEPTANCE.md`“F4 地面偏淡收尾修补验收 — run 45288051056”一节。已知未动：`Lawn_Green_rough.png` 均值仍 63.8（0.25，3 块草坪底板烘焙粗糙图；底板多被草丛遮盖、本次范围只含 GroundGrass 一处，未改）。**F4 Godot 侧根因（2026-11-24 08:xx CST，commit `2bc241c0`，run #90 `45295945269` success，PASS=202 FAIL=0）**：探针证实洗白源是太阳阴影通路（最小对照：#4F9D43 阴影关 (75,156,87)、开 (99,226,121)；#69B45D 关 (95,177,111)、开 (128,255,156)；bias/ortho/maxdist/blur 均无效；另证伪天光能量档对 SKY 源无效）。只改 `scenes/main.tscn` Sun `shadow_enabled=false` + verify 新检查 + weather_system 注释更正。复核：晴天草地 (128,247,162)→**(96,176,120)**，G 截顶 86.6%→**0.0%**，R/G 进 SPEC ±15；B 仍 +26（天空环境光蓝色分量，单调 sky_contribution 会连带压垮 G，需另定夺）；回退帧 (77,157,100) 近反照率，跑道更近本色，天空/树冠无回归。F4 基本通过。详见 `~/workspace/review-rework-r1/godot-acceptance/ACCEPTANCE.md`“F4 地面偏淡 Godot 侧根因修补验收 — run 45295945269”一节。**F4 最终定夺（2026-11-24 09:xx CST，选②改天空颜色，commit `4a14678e`，run #92 `45301489573` success）**：只降白天顶色 B（`weather_system.gd` 的 `day` #63a9e6→**#63a9b4**，B 230→180；地平线/雾色由顶色派生同向跟降），探针逐档量过——草地 B 120.7→101.5、R/G 纹丝不动（B=170 时天空 B≈G 已不像蓝天，故取 180）。复核：晴天草地 (96,176,120)→**(95.9,174.8,101.2)**，R/G/B 全进 SPEC ±15（B +26→+7.2）；回退帧 (77,157,100)→(78.6,156.6,85.7)；天空 (111,176,232)→(111,176,186)，仍是蓝色。**F4 关闭**。详见 ACCEPTANCE.md“F4 B 通道残留定夺验收 — run 45301489573”一节。

- 2026-11-24 07:3x CST ov-windows-roofs hx/hy 核验与 GLB 同步完成（commit `14f74bda`）：
  - **结论先行：faces 表的 hx/hy 对调在本次任务开工前已经修好（d44fa081/d09c8799），本轮未改 .py。**独立重测（非复述旧结论）：本地 .py + .blend + .glb + 仓库 .glb（raw 下载实测）+ 总览完整版 .glb，**56 条玻璃尺寸+中心点全部与期望值一致（0 偏差）**，56 个窗框切向长 = band_len+0.24、中心点一致；总览回读 13,036 对象、ovw_* 127 件。旧 bug（S/N 带只有 2*hy-2、E/W 带长达 2*hx-2 而悬空）在现行产物里均不存在；.blend1 已是修复后版本（21:39 UTC 重出时覆盖），旧 bug 的证据只剩 §3 记录与 .py 注释。
  - **本轮真正修的差额：仓库 .glb 是中断的修复 run 导出的旧版，与仓库 .blend 不一致。**GLB JSON 对比（节点/网格/访问器/贴图/纹理全同）：仓库版 3,310,888 B（blob `d6b3b147`）5 种材质 metallicFactor 全为 0（ovw_frame/coping/coping.001/equip/fan），本地重出版 3,318,672 B 为 0.85/0.95/0.95/0.55/0.70，与 .py 源码及仓库 .blend（实测 metallic 0.85/0.95/0.55/0.70）一致；另 1 张烘焙图字节不同（bufferView 5：23,179→30,877 B，其余为偏移连带）。几何零改动。
  - **推送**：本地 .glb 一次 push-files 入仓，commit `14f74bda`（`14f74bda5e9c90197ad90936c4f52a1c1db46b01`，父 `3444113ea`），仓库核对大小 3,318,672 B / blob `78075ebf…` 一致。.py/.blend 与仓库 blob 已一致，未动；总览无需重刷（.blend 未变，总览已含修复窗带，13,036 核对无差额），完整版总览留本地，未推。
  - **渲染验收**：本次推送只改 `assets/models/**`，不在 blender-previews 触发路径内，未触发新 run；验收用推送前已在跑的 run **#79 / 45276363035**（HEAD `39346cfbd`，F4+F5，含修复窗带 .blend 与瘦身总览），completed/success，约 58.5 分钟（22:06:18→23:04:53 UTC），6 job 全绿；overview artifact 18,407,231 B、20 张 1280×720 真 PNG。目视（本地 `~/workspace/review-windows-fix/overview/`）：ov-windows-roofs——三栋窗带方向正确（南北面通长、东西端面短带、两端各留约 1m、零悬空），A 5 层、B 5 层、C 4 层，屋面深灰膜 + 压顶 + 设备盒 + 风扇正常，品红 0.0000%；ov-bldA/B/C——楼体量块正常（墙/屋顶/空调小方块/门廊），窗带本就不在三件内、无回归，品红 0.0000%。B/C 在单件图里呈玻璃骨架（无墙体量块）属件归属所致，非缺陷。
  - **遗留**：①§9 遗留①“修复任务已派”现可销账（修复 d44fa081/d09c8799 + 本轮独立实测 + GLB 同步 14f74bda）；②今后 .glb 重出后须与 .blend 核对 metallicFactor 再推（本次即中断 run 的导出残留）。

- 2026-11-24 08:54 CST 池塘压路修补验收（run **#81 / 45289044112**，HEAD `bea25274`）：completed/success，约 74 分钟（23:27:59→00:42:00Z），6 job 全绿；overview artifact 18,407,044 B（与 API 一致），20 张 1280×720 真 PNG，品红 0、黑帧 0。ov-road-main：南环路沥青/黄中线/白边线完整露出、2x 放大无水面覆盖，与修补前 run77 同图逐像素相同（0.0000）；ov-lawn：池塘环形草带完整、椭圆中心留空，与 run77 近乎相同（0.0066，>10 的像素 0）。**局限（须如实记）**：workflow 只渲染 `assets/blender/overview/*.blend` 单件，不渲染拼装 `scenes/overview.blend`，池塘水面盘是拼装补件、20 张里一张都没有——本次出图无法直接目视水面是否低于路缘；修补前 run77 的 ov-road-main 同样像素相同且同样无水，证明这类图对本次修补本就不敏感。修补本身的证据是本地重刷（顶面 0.05 < 路面 0.08、断言通过、回读 13,036 对象零 Error、瘦身 GLB 36,081,140 B）；水面与路缘同框目视须走 Godot 侧拼装截图复核。本地目录 `~/workspace/review-rework-r1/acceptance-overview/pond-fix/`，验收续节见该目录 `ACCEPTANCE-OVERVIEW.md` §6。

- 2026-11-24 09:0x CST 总览车漆入仓核查（核查员 5b45411e，HEAD `d49ee011`）：**结论：三色车漆清漆已进总览，无需补推，本遗留项关闭。**核查方法：raw 下载仓库最新瘦身版 `assets/models/scenes/overview.glb`（36,081,140 B，git blob SHA `2e97d781…` 与 contents API 一致，确为 `bea25274` 池塘重刷版），直接读 GLB JSON chunk；实测 `ov-parking_body_red/grey/blue` 三种材质全在列，均带 `KHR_materials_clearcoat`，`clearcoatFactor=1.0`、`clearcoatRoughnessFactor=0.05`（另 `metallicFactor=0.15`、`roughnessFactor=0.5`）；`extensionsUsed` 含 `KHR_materials_clearcoat`，材质 202 种 / 节点 13,036 / 访问器 13,872，与本地完整版（121,839,788 B，`2ec2ef70…`，同值同口径）一致——瘦身只动贴图、不动材质。旧说法“车漆未进总览 GLB”已过时：`54fad3d3`（停车返工重刷）→ `39346cfb`（F4 重出总览）→ `bea25274`（池塘重刷）三次重刷均 append 最新 `ov-parking.blend`，清漆一直都在。未推任何模型文件，未重刷总览。注：本地完整版比 §4 记录的停车返工版（121,570,548 B）大 269,240 B，属池塘重刷重出时的字节波动，节点/材质/访问器数与仓库版完全一致，不影响结论。
- 2026-11-24 09:0x CST 单件预览“缺图”核查（工人 6617cf26）：任务书称 di-cabinets / ov-flag-lamp / ov-trees 三张缺失，经核查**不成立、无需修补、未改任何代码**：workflow matrix 6 组 glob 枚举全部 44 个 .blend（含三件，仓库 git tree 已核对尺寸）；render_max.py 无按名跳过逻辑（仅 PREVIEW 脚手架不参与取景；ov-flag-lamp 在 _DETAIL_FRAMING 白名单只改取景、仍出一张主图）；最近两次 success run 均 55/55——run #81/45289044112（bea25274）与 run #82/45292518351（77dc9b9d），overview 20 / dist 13 / pv 7 / storage 5 / classroom 6 / charge 4，三张均在列、逐张目视内容正确（di-cabinets 6 台柜+仪表窗+把手；ov-flag-lamp 3 旗杆+红旗+2 路灯；ov-trees 两排树冠），全部 1280×720、黑像素 0.0000、品红 0.0000；run #75（ceeb81df 取景修补）同样 20/13 齐全。唯一“缺图”处是本地未入仓的 screenshots/blender/（40 张，还缺 ov-transformer），属陈旧本地目录、非 Actions 产物，不作为缺图依据。

- 2026-11-24 09:3x CST 车窗玻璃修补进场景 GLB（件级修补 commit `77dc9b9d`，工人 f328c270；本任务重拼场景）：
  - **根因**：R3 复验遗留弱项——车窗只有纵向天空渐变、淡灰绿平板无亮带；件级修补已改玻璃材质（两件 `make_glass` 统一配方：透射 0.9→0.10、alpha 0.65→0.90、粗糙度→0.15、specular 1.0、深色 #33505F tint；删 Glass-BSDF mix + 玻璃 Bump），Blender 单件预览通过，但 Godot 04-charge 与上一轮逐像素相同——Godot 不读件 GLB（`scripts/glb_loader.gd` 读拼装场景 GLB），仓库 charge.glb 仍是 11-23 19:34 旧版，godot-verify 不重拼场景 GLB。
  - **重拼**：重跑 `assets/blender/scenes/charge.py` 与 `overview.py`（append 最新件 .blend，脚本未改；首跑 overview 在导出中途被运行时重启打断、.blend 已存、.glb 仍旧版，重跑一次完成）。
  - **验证**：charge 回读 306 对象（24 材质）、overview 回读 13,036 对象（append 13,032 + 拼装 4），零 Error/Traceback；GLB JSON 实测 ch-cars_glass transmission 0.10 / 粗糙度 0.15、ov-parking_glass alpha 0.90 / 粗糙度 0.15、两件三台车漆清漆 factor 1.0 / roughness 0.05；瘦身（§10 口径）：overview 完整版 121,839,792 B → 瘦身版 36,081,144 B（<40MB），.blend 64,576,376 B → 压缩版 9,058,074 B；`verify_slim.py` 全绿（瘦身 GLB 13,036 对象 / 0 无材质 primitive；瘦身 .blend 13,036 对象 / 472 贴图 / 缺失 0）。
  - **推送**：charge.glb 7,105,740 B + charge.blend 3,373,068 B + 瘦身 overview.glb/.blend + 本文档一次提交；完整版 overview .glb/.blend 留本地未推。
  - **Godot 验收**：待新 godot-verify run success 后下载截图复核（04-charge 与 00-overview 车窗应为深色镀膜、有反射层次；回归 01/02/03），见 `~/workspace/review-rework-r1/godot-acceptance/ACCEPTANCE.md` 新节。

- 2026-11-24 09:46 CST 本地陈旧截图目录清理（工人 a84d39f1）：本地 `screenshots/blender/` 40 张全是 640×360 旧渲染（2026-11-22，另 ch-marking 一张 11-23 本地重渲），对应 .blend 全部在仓（ch-marking.blend blob SHA 与仓库一致），Actions run #81/#82 单件预览均 55/55（含全部 40 个名字），无孤本；但该路径仍被 17 个渲染脚本作 PNG 写出目标、被 `blender-previews.yml` 作 Actions 暂存目录、被 SPEC/本文档述及，按任务分支不删目录，改为在目录内放 README.md 标注已废弃、缺图核查以 Actions artifact 清单为准。

- 2026-11-24 22:4x CST 储能场景 GLB 刷新（返工 R2-T4，上一轮遗留第 1 项销账）：
  - **核对（开工前，HEAD `2261d7ff`）**：场景 `scenes/storage.blend`/`.glb` 建于 2026-11-23 16:14 UTC，st-fence R1 `.blend`/`.glb` 建于同日 19:31 UTC（晚 3 小时 17 分），仓库核对：storage.glb 8,623,960 B / blob `b2c1d149`、storage.blend 11,886,071 B / blob `bf497c61`，与本地旧版字节相同；st-fence R1 单件 `.blend` 1,213,736 B / `.glb` 565,804 B 已在仓（commit `d74ab2a6`）。
  - **R1 差了什么（实测，非推测）**：R1 只改 `st-fence.py` 的两处 Preview_* 材质——`Preview_Cabinet` 挂 st-cabinet 锈蚀三件套、`Preview_Ground` 挂 st-base 混凝土三件套、地面 UV 按 2m 平铺 ×15，无新素材；两处材质只供 6 个 Preview_* 示意物（`Preview_Ground`/`Preview_Base`/4 台示意柜）。Blender 双开实测：场景内 36 件围栏本体与 R1 件内 36 件逐项一致——同名、同位、同尺寸、同顶点数、同首末顶点坐标，6 种材质（Fence_DarkGray / Fence_MetalGray / Sign_Black / Sign_RivetMetal / Sign_White / Sign_Yellow）底色/粗糙度/金属度全同、均无贴图节点；场景内 Preview_* 为 0。`storage.py` 与 `st-fence.py` 导出均排除 Preview_*，所以 R1 对 storage.glb 的内容差为零——“过期”只在时间戳上成立，几何与材质上不成立。
  - **重拼**：重跑 `assets/blender/scenes/storage.py`（脚本未改，`assets/blender/scenes/storage-scene-r2t4-20261124.log`），append 计数 cabinet 83 / doors 52 / cables 64 / base 32 / fence 36 = 267 + 拼装壳体/屋顶 2 = **269 对象**；前门面冲突 12 处按旧口径内缩（把手 4 根再 +y 0.002 清零，复核 0.000000）；壳体 Alpha 0.35 BLEND、屋顶板不透明挂 PBR 三件套；日志零 Error/Traceback，`DONE storage`。新 GLB JSON 与旧版全同（269 节点 / 269 网格 / 39 材质 / 17 贴图 / 21 纹理，围栏节点 36、Preview 节点 0，壳体 alphaMode BLEND），sha256 与旧版相同、git blob 仍为 `b2c1d149`（8,623,960 B）；.blend 同体积 11,886,071 B、blob 更新（`bf497c61`→`28a0465b`）。
  - **推送**：storage.glb（字节与仓库相同，随单提交复核）+ storage.blend + 本文档一次 push-files 入仓，commit `ea6758fc`（父 `2261d7ff`，2026-11-24T14:44:35Z）；推后核对：commit 文件清单含 BLENDER_MODELS.md + storage.blend——storage.glb 因 blob 与旧版相同、git 树无变化而不入清单，属正常；contents 核对 storage.glb 8,623,960 B / `b2c1d149`、storage.blend 11,886,071 B / `28a0465b` 一致。注：随后 R2-T5 推送 `ab1cf8c3`（父 `ea6758fc`，BLENDER_MODELS.md + REVIEW-83.md），HEAD 已前移，本条记录以 `ea6758fc` 为准。
  - **验证（Godot）**：godot-verify run **#106 / 45417710346**（workflow_dispatch，HEAD `ab1cf8c3`，含本次推送），completed/**success**，单 job verify-export 全绿；artifact godot-screenshots 18 张 1280×720 全部下载目视——02-storage：4 台柜 + 三面围栏（北/西/东整段、南分两段留 1.5m 门洞）+ 半透明壳体 + 屋顶板齐全，南门洞东侧立杆挂黄色“高压危险”主牌（黑闪电条 + 白编号牌），无缺件、无回归；10-storage-discharge-closeup：近景围栏立柱/双横杆/竖条密排、柜门绿板、黄色警戒线、能量流光点均正常；13-fallback-storage 与上一 run 逐像素相同（0.000）。回归像素对比（vs run #105 / 45320653975，HEAD `2261d7ff`）：02-storage mean|diff|=0.001（>10 的像素 0.00%）、10-closeup 0.010（0.03%，流光点相位噪声）、00-overview 0.002、01-pv 0.059、04-charge 0.000——与 GLB 字节相同一致，零回归。
  - **验证（Blender）**：blender-previews run **#84 / 45417503305**（push 触发，HEAD `ea6758fc`）：render (storage) 组 completed/**success**；artifact blender-previews-storage 5 张 1280×720 齐全（st-base / st-cabinet / st-cables / st-doors / st-fence），逐张目视：st-fence——围栏五段 + 黄牌 + 编号牌齐全，4 台示意柜见锈蚀纹理、地面见混凝土噪波（R1 PBR 已进单件预览）；st-cabinet 锈蚀绿柜 + 百叶/把手/屏显正常；st-base 混凝土基座 + 黄警戒线正常。注：run #84 整体截至本条写入时仍在跑（dist/overview 组 in_progress），与本任务无关。
  - **新发现遗留（本次目视+实测，不属 R1 改动，本任务未修）**：st-fence v1 立柱布点 bug——`st-fence.py` 立柱循环 `t=(i*2.0)/L` 在段长非 2m 倍数时末点越界（t>1），`Fence_Posts` 实测 17 根中有 4 根 stray：(60.0, 32.5) 北出角 1.0m、(68.0, 32.5) 北出角 1.0m、(68.75, 28.5) 东出角 0.75m、(64.0, 28.5) 立在南门洞正中（门洞 63.25–64.75）；`Fence_Posts` 包围盒实测 (8.83, 4.08, 1.8)m（应为 8.08×3.08）；run #84 st-fence.png 东侧两根孤立杆即 (68.75, 28.5) 与 (68, 32.5)。根因在 v1 结构，R1 未动布点、场景重拼如实复现；修法：立柱 t 钳制 ≤1.0（或按段长均分布点），重跑 st-fence.py → 重拼 storage → 重推 → 新 run 复核，另派任务。上一轮“v1 结构已通过筛查”未发现此 4 根，筛查口径待补（立柱逐根坐标核对）。**已修（返工 R2-T20，2026-11-24，见本节 R2-T20 条目）**：立柱改按段长均分布点（n=max(1,round(L/2))，t=i/n），17 根→13 根，包围盒回到 8.08×3.08m，4 根 stray 全清，场景已重拼重推。

- 2026-11-24 23:3x CST st-fence 立柱布点 bug 修复（返工 R2-T20，本任务遗留销账）：
  - **根因（实测）**：`st-fence.py` 立柱循环 `t=(i*2.0)/L`，段长非 2m 倍数时末点越界（t>1）：南左/南右段 L=3.25（n=round(1.625)=2，i=2 时 t=1.231）、西/东段 L=3.0（n=round(1.5)=2，i=2 时 t=1.333），北段 L=8.0 整除无越界。`Fence_Posts` 17 根中 4 根 stray：(60.0, 32.5) 北出角 1.0m、(68.0, 32.5) 北出角 1.0m、(68.75, 28.5) 东出角 0.75m、(64.0, 28.5) 立在南门洞正中（门洞 63.25–64.75）；包围盒 (8.83, 4.08, 1.8)m。
  - **修法**：每段按段长均分布点，`n=max(1,round(L/2))` 段、立柱 `t=i/n`（i=0..n），首末精确落角点、中间均匀分布；脚本内加断言校验（全部立柱在 [60,68]×[28.5,31.5] 内、南门洞 63.25–64.75 间无立柱），其余结构/材质/竖条/标识牌一字未动。
  - **修正后立柱 13 根（逐根）**：北 y=31.5：(60,31.5) (62,31.5) (64,31.5) (66,31.5) (68,31.5)；南 y=28.5：(60,28.5) (61.625,28.5) (63.25,28.5)（门洞西缘）(64.75,28.5)（门洞东缘）(66.375,28.5) (68,28.5)；西 x=60：(60,30)；东 x=68：(68,30)。角点 4 根由相邻段共享去重。4 根 stray 全清，门洞正中无立柱。
  - **重建（Blender 4.2.0，`st-fence-r2t20-20261124.log`）**：`st-fence.py` 重跑，立柱 13 根、竖条 125 根、本件对象仍 36，GLB 回读 36，日志零 Error/Traceback；`Fence_Posts` 包围盒实测 (8.08, 3.08, 1.8)m（x[59.96,68.04] y[28.46,31.54]，立柱 0.08 宽）；新件 st-fence.blend 1,211,208 B、st-fence.glb 552,460 B（旧 565,804 B，少 4 根立柱所致）。
  - **重拼（`storage-scene-r2t20-20261124.log`）**：`scenes/storage.py` 未改，重跑 append cabinet 83 / doors 52 / cables 64 / base 32 / fence 36 + 拼装壳体/屋顶 2 = **269 对象**，回读 269，日志零 Error/Traceback；新场景 storage.blend 11,883,543 B、storage.glb 8,610,616 B（旧 8,623,960 B）。
  - **推送**：commit `587007d9`（父 `f5b6e03f`，2026-11-24T15:3xZ），6 文件一次提交：st-fence .py/.blend/.glb + storage .blend/.glb + 本文档；推后核对：commit 文件清单 6 项齐全，contents 核对 st-fence.glb 552,460 B / `1a93bbad`、st-fence.blend 1,211,208 B / `308f9de9`、storage.glb 8,610,616 B / `11499441`、storage.blend 11,883,543 B / `ca82cc60`，均与本地一致。
  - **验证（Blender）**：blender-previews run **#88 / 45426566158**（push 触发，HEAD `587007d9`）：render (storage) 组 completed/**success**；artifact blender-previews-storage 5 张 1280×720 齐全，逐张目视 st-fence.png：围栏五段 + 黄牌 + 编号牌齐全，4 台示意柜锈蚀纹理、地面混凝土噪波正常；东侧再无孤立杆（旧 (68.75,28.5) 与 (68,32.5) 已无），北侧无出角立柱，南门洞正中无立柱、门洞畅通。注：run #88 整体截至本条写入时仍在跑（其余组 in_progress），与本任务无关。
  - **验证（Godot）**：godot-verify run **#109 / 45426566166**（push 触发，HEAD `587007d9`），completed/**success**，单 job verify-export 全绿；artifact godot-screenshots 18 张全部下载，逐张目视 02-storage 与 10-storage-discharge-closeup：02——4 台柜 + 三面围栏 + 半透明壳体 + 屋顶板齐全，南门洞留空、黄色“高压危险”主牌在门洞东侧立杆上，东侧围栏到角点结束、无孤立杆；10 近景——南面围栏立柱间距均匀、双横杆/竖条密排、无孤立杆；与旧 run #106 逐像素对比：02 mean|diff|=0.36、10 mean|diff|=2.00，差异集中在两处——差分热力图上两道整根立柱高的红色条带，一道在旧 (62,28.5) 柱位（西移 0.375m 至 61.625），一道正在门洞正中旧 (64,28.5) stray 位（已拔除），其余为能量流光点相位噪声；无回归。

- 2026-11-24 23:2x–24:0x CST 操场收界（返工 R2-T1b，接替中断的 R2-T1，只改 ov-track、ov-field 与总览拼装）：
  - **半成品核查（开工前，HEAD `98a50540`）**：R2-T1 已改 `ov-track.py`/`ov-field.py`（11-24 14:42）并重建 `ov-track.glb`（14:44，1,142,348 B）/`ov-field.glb`（14:48，2,515,508 B）与 24 张重烘焙贴图（ov-track 9 张、ov-field 15 张），未推仓、未重拼总览。实测回读包围盒（Blender 坐标，GLB 回读）：ov-track 17 对象 x[-90.30,-33.70] y[-65.30,15.30] z[0.00,0.15]；ov-field 30 对象 x[-77.07,-44.10] y[-54.51,4.51] z[0.00,2.50]（场内 x[-77.07,-46.92] y[-53.08,3.08]、球门 y 伸至 ±54.51/4.51 为南北球网外伸 1.5m、看台 x[-46.50,-44.10] y[-37.00,-13.00]）。与脚本常量逐项一致（中心 (-62,-25)、跑道外 rx28/ry40 + 路缘 0.3、场 30×56、看台前缘 -46.5），**半成品正确、无需再改**，两件脚本未动。
  - **出界根因与量值（实测）**：v1/v2 按 SPEC §4 / campus.json playground (rx40 rz28) 建成长轴东西向，中心 (-80,-25) 时西缘 -120.3（含路缘）；环校路西段内缘路缘石中心线 x=-90.85、路缘盒实测 x[-91.00,-90.70]，旧西缘超出路缘石中心线 **29.45m**，建到校园外面去了。另长轴方向与鸟瞰图不符（鸟瞰图操场在西侧、完全在西界路以内，跑道长轴大致南北向：北端贴艺体馆、南端近南环路）。
  - **改后包围盒（v3，实测）**：长短轴对调（rx28/ry40，长轴南北向）+ 中心东移 18m 至 (-62,-25)。跑道含路缘西缘 **-90.30**，距路缘石中心线 -90.85 净空 0.55m、距路缘盒东面 -90.70 净空 0.40m；东缘 -33.70、北端 y=15.30（教学楼 bldA 南缘 y=22.5，净空 7.2m）、南端 y=-65.30（南环路内缘路缘约 y=-84，净空 ~18.7m）。球场 x[-77,-47]、y[-53,3]，球网南北外伸后 y[-54.51,4.51] 仍在内椭圆内（角点归一化半径 0.885 <1）；看台后缘 -44.10，距内椭圆东缘在看台两端净空 0.64m。起跑线改到东直道、弯道标记改到南北两端弯道中点。
  - **重拼（`assets/blender/scenes/overview-refresh-r2t1b-20261124.log`）**：重跑 `assets/blender/scenes/overview.py`（脚本未改），`DONE overview`，日志零 Error/Traceback；append 13,213 + 拼装补 4 = 回读 **13,217** 对象（GLB JSON：13,217 节点 / 4,623 网格 / 203 材质 / 325 贴图 / 14,015 访问器；track 17 节点、field 30 节点齐全）。注：13,217 不是旧 13,036，差额 **+181 全是 ov-trees**（kept 292→473，`.blend` 在本轮拼装进行中由并行工人重建、mtime 2026-11-24 15:26:55 UTC，本轮 append 如实取到新版；其余 19 件 kept 数与 01:31 玻璃版逐件相同，ov-track 17 / ov-field 30 不变）。完整版 .glb 102,553,484 B（旧 121,839,792 B，-19.3MB：并行重建的楼体/路/树件烘焙贴图 427→325 张所致，非本任务改动）、.blend 68,983,428 B（旧 64,576,376 B，+181 棵树所致）。另：上一任 R2-T1 中断前已把总览 `.blend` 存到 14:57 版（内含新跑道/球场，包围盒与新版一致），但 `.glb` 仍是 01:31 旧版——本轮重跑后两者一致。
  - **瘦身（§10 口径）**：完整版 102,553,484 B → 瘦身版 **37,024,624 B**（36.1%，<40MB）；325 张贴图：5 张 alpha→PNG512、114 张 color→JPEG512 q80、184 张 normal/mr→PNG256、22 张已达标原字节保留；节点/材质/访问器全同。`verify_slim.py` 本体硬编码 13036 断言（树重建前口径）已过时——**未改共享脚本**，用 /tmp 副本（仅断言 13036→13217，用完即删）跑完验证，全绿：瘦身 GLB 13,217 对象 / 13,213 mesh / 0 无材质 primitive；瘦身 .blend 11,923,658 B、13,217 对象 / 446 贴图 / 缺失 0（`assets/blender/scenes/overview-slim-verify-r2t1b-20261124.log`，exit 0，`DONE verify_slim`）。
  - **推送**：commit `3a20fea3`（父 `e2172026`，2026-11-24T16:05:24Z），33 文件一次提交（commit 内文件清单 27 项——其中 6 张贴图 FieldLine/GoalFrame 各 3 张与仓库字节相同、git 树无变化而不入清单，属正常）：ov-track .py/.blend/.glb + 9 张重烘焙贴图、ov-field .py/.blend/.glb + 15 张重烘焙贴图、瘦身 overview.glb 37,024,624 B→`assets/models/scenes/overview.glb`、压缩 overview-slim.blend 11,923,658 B→`assets/blender/scenes/overview.blend`、本文档；完整版 overview .glb/.blend 留本地未推；overview.py 未改不推。推后核对：commit 文件清单含全部改动文件；contents 核对 overview.glb 37,024,624 B / blob `8791a4b8…`、overview.blend 11,923,658 B / `17c442e6…`、ov-track.glb 1,142,348 B / `98821dbf…`、ov-field.glb 2,515,508 B / `ee2bb9bf…`，均与本地一致。
  - **验证（Godot）**：godot-verify run **#116 / 45433047551**（push 触发，HEAD `3a20fea3`），completed/**failure**——卡在第 7 步 Headless verify，VERIFY-SUMMARY **PASS=269 FAIL=2**，两项 FAIL 均为 **S4 车顶 SOC 条**（回退 1.84 / GLB 1.465，3 辆；条底贴合车舱顶 top=1.375），属充电区汽车件，与本次跑道/球场改动无关。**已证伪为旧失败**：上一 run #115 / 45431057864（HEAD `25badadb`，R2-T7 灯光提交，本次推送前）同样 failure、同样 PASS=269 FAIL=2、同样两项 S4、数值一字相同（1.84/1.465、top=1.375）；#112/#113/#114 也全部 failure。S4 根因在汽车件（R2-T19 换装 Quaternius 三车后车顶高度与 verify 旧期望不符）或 verify 期望本身，不属本任务范围（禁动 Godot scripts/scenes/data、只改 ov-track/ov-field 与总览拼装），未修；需父 agent 另派 S4 修复后重跑。因 verify 未过，Export/Screenshots 步被跳过，**#116 无 00-overview 截图 artifact**，本次 Godot 侧目视未能走 Actions。
  - **验证（边界目视，诊断渲染）**：因 #116 无图，改用本地诊断渲染补目视（`/tmp/r2t1b-diagnostic-overview-west.png`，仅诊断、不入仓）：打开已拼好的总览 `.blend`，只留 road-main + track + field + 拼装地面（92 对象），正交俯视 150×150m（中心 (-65,-25)，覆盖 x[-140,10] y[-100,50]）、Eevee 1024×1024 渲染。目视结论：红色椭圆跑道长轴竖直（南北向），整体位于西环路（左）与南环路（下）之内、四周均留绿草带，**无出界**；场内条纹球场 + 南北两端球门 + 东侧看台齐全，球场在跑道环内。0.4–0.55m 的西缘净空在该比例下不可见，以上面实测包围盒为准（跑道西缘 -90.30 vs 路缘盒东面 -90.70）。
  - **验证（Blender）**：blender-previews run **#93 / 45433047733**（push 触发，HEAD `3a20fea3`），completed/**success**，6 组全部 success（pv / storage / charge / dist / overview / classroom）；artifact blender-previews-overview 20 张 1280×720 RGBA 齐全，逐张数过。目视 ov-track.png：红色椭圆跑道环完整，4 条跑道 + 白色分道线/内外边线齐全，弯道标记在两端、起跑线在东直道，无黑帧、无缺件；ov-field.png：8 条深浅绿相间条带 + 白色边线/中线齐全，南北两端各 1 个球门、东侧 3 级看台齐全。两图与实测包围盒一致。注：ov-track.png 白色分道线上有 2 处针尖大深色点（西南弯与东北弯各一），疑似烘焙贴图噪点/UV 边缘渗色，不影响形状与边界，记为外观小注、不阻塞。Godot 侧 00-overview 仍待 S4 修复后重跑复核（见上）。
  - **后续（R2-T9b 覆盖，不属本任务）**：commit `f39cd380`（2026-11-24T16:51:18Z，R2-T9b PBR hard-fix）改了 `ov-track.py`：跑道红环改挂 asphalt_01  tint #B8543F，仓库 ov-track.glb 已是新版 4,540,664 B。实测新版包围盒 x[-90.30,-33.70] y[-65.30,15.30]、17 对象，与 v3 一字相同——**几何/收界结论未动**；但本任务推送的总览瘦身 GLB 仍含旧版跑道贴图，需待 R2-T9b 收敛后另起总览重拼（重跑 overview.py + 瘦身 + 推仓），不由本任务补推。

## §10 总览大文件瘦身入仓（2026-11-23 11:39–12:00 CST，瘦身任务 8bb03134）

- **根因**：Git Data API 建 blob 有实际大小上限，实测探针（孤 blob，不污染仓库）：40MB 原始文件 OK（base64 约 55.9MB），46MB 报 HTTP 422 "input too large"。阈值在 40–46MB 之间，**不是 100MB**；先前文档里写的"约 26MB 上限"是低估，实际可推到 40MB。另一次 37.8MB 推送曾遇 HTTP 502 "Server Error"，属 GitHub 侧临时错误，重试一次即成功（凡推必核 commit）。
- **overview.glb 123,019,340 B → 37,538,508 B**（30.5%；上一版瘦身 102,672,808 B → 37,833,636 B，commit `4765d7b`）：只动贴图、不动几何。369 张贴图全为 1024×1024 RGB PNG（无 alpha）：color 121 张（27.9MB）→ 512px + JPEG q80（1.19MB）；normal 127 张（36.4MB）→ 512px PNG（7.92MB）；metallicRoughness 121 张（11.9MB）→ 512px PNG（2.31MB）。贴图合计 76.25MB → 11.42MB；几何 22.76MB 与 JSON 3.66MB 未动。脚本 `/tmp/slim_glb.py`（MAX_DIM=512，JPEG_Q=80）。
  - 旧版（`4765d7b`，blob `793d5ae9`）验证：Blender 回读 4837 对象 / 4563 mesh / 191 材质 / 369 贴图，零尺寸贴图 0、空 mesh 0、无贴图纹理节点 0；Godot 4.4 无头 GLTFDocument 加载 ERR 0、4838 节点（含根）、369 贴图 / 4563 mesh / 191 材质——JPEG 贴图在 Godot 里正常加载，仓库核对 size 37,833,636 一致。
  - 新版（commit `e56912f`，2026-11-23 14:59 UTC）：仓库 slim GLB 37,538,508 B、slim .blend 9,736,002 B（gh.py contents 核对，2026-11-23 23:26 CST，HEAD `c046118`）；本地完整版 GLB JSON 实测 13,036 节点 / 202 种材质；瘦身只动贴图、不动几何。
- **overview.blend 66,234,504 B → 9,736,002 B**（上一版 51,360,304 B → 6,410,318 B）、**pv.blend 本地 13,562,916 B / 仓库瘦身版 5,526,866 B**（上一版 112,997,536 B → 5,529,013 B）：两 .blend 均无 packed 贴图（0 字节，贴图全是 `//../overview/...` / `//../pv/...` 相对路径外链，仓库里对应贴图目录齐全），体积全是几何数据；改用 Blender gzip 压缩保存（`save_as_mainfile(compress=True)`），**几何零改动**。注意：save_as 到不同目录会改写相对路径（`//../overview/...` 被改成 `//../home/hatch/...` 形式），必须在原目录内另存为临时文件再推，推完删临时文件。
  - 旧版（`7070732`）验证（原目录内打开）：overview-slim 4837 对象 / 4548 mesh（与原 .blend 一致，与 .glb 的 4563 之差是导出前就有的旧差）/ 386 贴图、缺失文件 0；pv-slim 881 对象 / 881 mesh、0 贴图、缺失 0。两文件一次提交 commit `7070732`（overview blob `122db062`、pv blob `f3b7309d`），仓库核对一致；项目内临时文件已删。
- **口径**：本地完整版文件（overview.glb 121,570,192 B / overview.blend 64,530,392 B，池塘返工后；pv.blend 13.6MB）未动，仍是明天 18:15 Godot 整合的输入；仓库里是瘦身版，仅供 Actions 渲染/导出验证。仓库 HEAD 现为 `e01d014c`（gh.py 查询，2026-11-24 01:10 CST / 2026-11-23 17:10 UTC，commit 时间 2026-11-23T17:09:49Z，`PROGRESS: run 45219977015 success, VERIFY-SUMMARY PASS=94 FAIL=0 (ed7c8479)`）。
- **池塘返工后瘦身（2026-11-23 23:58 CST）**：贴图数 369→427，512px 法线 PNG 单独 12.9MB，按旧口径整包 47.5MB 会超 40MB 上限；本次瘦身 color 仍 512px JPEG q80，normal/metallicRoughness 改 256px PNG（脚本 `/tmp/slim_glb.py`，NORM_DIM=256），几何零改动。完整版 overview.glb 121,570,192 B → 瘦身版 36,459,020 B（30.0%），.blend 64,530,392 B → gzip 瘦身版 9,092,702 B；瘦身 GLB 经 JSON 对比（节点/访问器/材质槽全同）+ Blender 回读 13,036 对象、0 无材质 primitive，瘦身 .blend 原目录打开 13,036 对象、465 贴图、缺失 0、池塘草 z=0。
- **瘦身脚本已重写并持久化（2026-11-24）**：旧 `/tmp/slim_glb.py` 已丢，重写为 `assets/blender/tools/slim_glb.py`（另有 `assets/blender/tools/verify_slim.py`：回读瘦身 GLB + 出压缩 .blend + 原目录重开验证）。口径不变：color 512px JPEG q80，normal/metallicRoughness 256px PNG，几何零改动，草叶 alpha 贴图永不转 JPEG；双槽贴图按 normal 走 256px PNG；已达标贴图原字节保留。实测本版唯一带 alpha 贴图是 `grass-side-colour`（2000×456 RGBA，baseColor 槽），已按 512px PNG 处理；2 张同时挂 baseColor+normal 的贴图按 normal 走 256px PNG。注意：Blender 4.2 的 `save_as_mainfile(compress=True)` 实际写出 ZSTD 压缩（文件头 `(\xb5/\xfd`），不是 gzip，Blender 原生可读；文档里“gzip 瘦身版”沿用旧称，指压缩保存的 .blend。
- **停车返工后瘦身（2026-11-24）**：完整版 .glb 121,570,548 B → 瘦身版 **36,044,776 B**（29.6%），.blend 64,546,472 B → 压缩版 **9,093,786 B**；427 张贴图：color 146 张转 JPEG q80、normal/mr 256 张转 256px PNG、草叶 alpha 1 张 512px PNG、24 张已达标原字节保留；瘦身 GLB JSON 对比（节点 13,036 / 访问器 13,873 / 材质 202 / 材质槽全同、clearcoat 3 种保留）+ Blender 回读 13,036 对象、0 无材质 primitive；瘦身 .blend 原目录打开 13,036 对象、465 贴图、缺失 0、贴图全相对路径（`//../…`）。
- **仍未推**：overview 的 .glb/.blend 均已入仓（瘦身版，见上）；pv 的 .blend/.glb 均已入仓（.glb 19,774,596 B，commit `7227239`）；charge/storage 场景 .blend/.glb 均已入仓（commit `1f36cb2`，见 §9）。B 组烘焙版 run 45105477296 出图后仍需第八轮复核（见 §9 末尾）。

## §11 返工路线（用户 2026-11-23 22:16 定死，全程不许偏离）
- 最终目标：把 Demo 打磨好——精致、动画流畅、优雅、美观大方。昨天那版效果差的原因：全靠自己手捏模型、没有材质纹理。
- 实现路线（定死）：尽量用网上现成的材质包和现成的 Blender 建模（CC0 优先），在此基础上手动修改适配，绝不从零手捏大件。楼体尺寸仍按 SPEC 实测，改模型不改尺寸。
- 检查：每 10 分钟有人检查是否偏离；发现又回头全手捏、或交出来的还是平板 AI 味，立刻纠正路线。
- 其余不变：草一根一根建模铺满、丢色一起修、渲染全走 Actions、本地不渲染。
- 注：ov-transformer 补件（commit 7228f6b）是本指令下达前手捏完成的，不返工；自本节起一律按上述路线。

## §12 blender-previews run #83 单件渲染图逐张目视复核（2026-11-24 22:39–22:44 CST，R2-T5）

- **对象**：run #83（45306226357，`Blender previews (max quality)`，HEAD `0317452b`，结论 success）；6 个 artifacts 全部下载解包，**55 张齐**（overview 20、dist 13、classroom 6、charge 4、pv 7、storage 5），全部 1280×720 RGBA；55/55 逐张目视（10 张拼图通读 + 5 张全尺寸复看）+ 像素级筛查（品红 0.00%、无黑/白帧）。
- **结论：通过 52 张，不通过 3 张；独立画面 53 张**（详见 `REVIEW-83.md`，与本文档同次提交；55 张图本身不推仓，只留本地 `~/workspace/review-rework-r2/blender-83/`）。
- **不通过**：
  1. `dist/di-signs.png`——与 `di-signs-Warn.png` 逐像素相同（maxdiff=0），图中只有“高压危险”一块牌，无独立的标识集合渲染。
  2. `pv/pv-inverter.png`——与 `pv-inverter-LAB.png` 逐像素相同（maxdiff=0），图中就是 LAB 那台逆变器，无独立的通用逆变器渲染。
  3. `pv/pv-mount.png`——左下角第二组支架被画面边缘截断只剩一角；银灰支架与浅灰背景对比度极低，全图几乎融为一体。
  - 重图根因推测：渲染脚本里 `di-signs`/`di-signs-Warn`、`pv-inverter`/`pv-inverter-LAB` 很可能指向同一对象/相机位，需核对件名—对象映射表；`pv-mount` 重渲建议换深色背景、收紧取景。
- **通过但有弱项备注**：`ov-lawn`（绿篱远景呈虚线状、草叶单体不可辨、主体偏小）、`ov-road-walk`（步道细长、留白大）、`ov-trees`（全景尺度下单棵仅为小点）；`ov-windows-roofs` 中、右两栋窗带间可透视见对侧，是单件渲染隐藏墙体件 ov-bldA/B/C 所致（与 cl-windows 悬空窗同理），非本件缺失；`st-fence` 右侧一根孤立立柱疑似门柱待核对。faces 表 hx/hy 对调遗留（§9 遗留①）本图无法核验长短，不计入本次不通过。
- **只复核、不建模**：未改任何模型/Godot 文件。

## §12b R2-T13：修 R2-T5 复核出的 3 张不通过单件渲染图（2026-11-24 22:46–2026-11-25 00:40 CST）

- **根因（已核对脚本与建模脚本确认，非推测）**：
  1. `di-signs` / `pv-inverter` 重图：不是映射表写重，而是 `tools/render_max.py` 稀疏分簇分支的 bug——簇分图渲完后，主图相机被设成最大簇的相机，随后 `-f 1` 主渲染用的就是该相机，所以主图与最大簇分图逐像素相同（run #83：`di-signs == di-signs-Warn`、`pv-inverter == pv-inverter-LAB`，maxdiff=0）。模型本身没错：`di-signs` 是北墙 Warn + 东墙 NoClose + 6 块 Num 牌（`di-signs.py`），`pv-inverter` 是 A1/A2/LAB 3 台逆变器（`pv-inverter.py`）。
  2. `pv-mount` 截断 + 低对比：两点。① 细节取景只框最大一组（LAB 屋顶阵列），其余两组仍在场景里渲染，B 组阵列闯入取景框左下角、只露一角（run #83 目视 + 几何核对：相机在 LAB 东南上方约 69m，B 组在其视锥内）；② 对比：`_DETAIL_BRIGHT_BG` 曾把 pv-mount 的世界背景提亮成天空浅蓝，但支架主材是浅银（#B9BEC2），浅轨配浅背景根本看不清（run #72 的“暗主体需提亮”假设对这件是反的；同组 `pv-panels`/`pv-roof` 用深灰背景则清晰）。
- **改动（只改 `tools/render_max.py`，不改任何 .blend/.glb 模型、不碰 Godot 文件；`py_compile` 通过）**：
  1. 稀疏分支主图改用整件相机（whole-piece view），不再用最大簇相机；另优先用件自带的内置相机（当它能框住全部主体对象时）：`di-signs` 自带 22mm 南侧广角相机正是为“一次看清 8 块牌”设计的，从南侧看东墙牌牌面可见，而自动 3/4 整件视角（东南上方）只能看到东墙牌的红色背面、无字；无内置相机的件（`pv-inverter`）仍用整件相机。
  2. `pv-mount` 细节取景时隐藏其余两组（`hide_render`，仅渲染会话内有效，.blend 不保存、不改模型）；只对 pv-mount 生效，其余细节件（cl-ac、ov-flag-lamp、ch-piles）的相邻同组单元仍保留在画面内。
  3. `pv-mount` 移出 `_DETAIL_BRIGHT_BG`，恢复深灰世界背景（与 pv-panels/pv-roof 一致）；该集合现为空，机制保留。
- **推仓**：commit `fa406e99`（第 1 批改动）→ run #85；commit `1c39c0dd`（内置相机优先）→ run #89。两 commit 均经 API 核对真实存在，单文件 `tools/render_max.py`。
- **验证 run #85（id 45418605110，HEAD `fa406e99`，2026-11-24T14:50:34Z–16:04:18Z，success）**：pv/dist 两组已验，overview 未等完（run #89 全量重验）。
  - `pv/pv-inverter.png`：不再重图（vs LAB maxdiff=157、meandiff=3.845；vs A1/A2 亦不同），目视：整件视角下 3 台逆变器箱（A1 左、LAB 中下、A2 右）各带线槽入画，放大裁切核对 3 台均为带散热格栅/显示屏/线槽的真逆变器；弱项：3 台在整幅 1280×720 里都很小（约 25px/台，整件跨度约 50m、单台仅 1m，单帧无法同时放大），细节仍由 A1/A2/LAB 分图承载。
  - `pv/pv-mount.png`：单组 LAB 阵列完整入画，左下角无第二组闯入；背景已是深灰（四角均值 RGB≈59，与 pv-panels 一致），银灰支架横梁/斜撑支腿/压块清晰可辨。✅ 通过。
  - `dist/di-signs.png`（run #85 版，整件 3/4 视角）：不再重图（vs Warn maxdiff=152、meandiff=58.3），8 块牌全入画（Warn 红牌字迹可读、6 块蓝牌成排、东墙牌在右下角）；弱项：东墙“禁止合闸”牌只能看到红色背面、无字——这正是 commit `1c39c0dd` 要修的，见 run #89。
- **验证 run #89（id 45426806918，HEAD `1c39c0dd`，2026-11-24T15:33:04Z–16:33:46Z，success；6 组全 success）**：
  - `dist/di-signs.png`：✅ 通过。dist job 日志实录 `main view = built-in camera Camera`；目视：内置 22mm 南侧视角下 8 块牌全部正面入画——Warn 红牌“高压危险”黄边白字、6 块蓝牌一字排开（数字可辨）、东墙白牌“禁止合闸 / 有人工作”红字红边（放大裁切核对两行字均清晰）；vs Warn/E/Num1 均不再重图（maxdiff 153/153/155）。55 张图本地留 `~/workspace/review-rework-r2/blender-89/`（不推仓）。
  - `pv/pv-inverter.png`、`pv/pv-mount.png`：与 run #85 逐像素相同（maxdiff≤1），两项修复在 #89 里保持不变。✅ 通过。
  - **全量回归（#89 55 张 vs #83 55 张逐像素比对 + 品红/黑/白筛查 + 全量重图对筛）**：55 张齐（overview 20、dist 13、classroom 6、charge 4、pv 7、storage 5）；变化仅 5 张——本任务 3 张 + `st-fence`（并行任务 R2-T20 模型修复 commit `587007d9`：立柱越界 17 根→13 根、4 根 stray 全清，#89 图上孤立立柱已消失、围栏+4 柜完整，非本任务改动、无回归）+ `ov-windows-roofs`（maxdiff=2、meandiff=0.003，纯渲染噪点）；其余 50 张逐像素相同；#89 内无逐像素重图对（NONE）；品红 0.00%、纯黑最高 0.11%（cl-floor-walls）、纯白最高 0.17%（ov-parking），与 #83 筛查口径一致。
- **还剩什么**：① `pv-inverter` 主图 3 台偏小（见上，结构性限制，单帧无法同时放大；如需大图看 A1/A2/LAB 分图）；② R2-T5 弱项备注（ov-lawn、ov-road-walk、ov-trees 拉近镜头；st-fence 门柱核对已由 R2-T20 的清 stray 解决）不在本任务范围内，未动。

## §13 R2-T6 总览标签微叠 + 配电房黄雾（Godot 侧，2026-11-24）

- **标签**：删 pin 机制（`scripts/labels.gd` + `scripts/main.gd`），GLB/回退总览同走正常去重叠；变压器 +44 档（868.9,435.1），与 SOC 盒底净空 26.8px，宿舍楼 A/B +66，18 条全可见、0 重叠。详见 PROGRESS.md 同名一节。
- **配电房**：黄雾根因是暖米色墙（Wall_Cream 亮部 #D7C8A5）× F4 关阴影后漏进来的暖阳光 × 天顶 B 下调，非雾密度问题；`scripts/dist_interior.gd` 在 GLB 加载后复制墙/顶 7 个材质做冷色补偿（墙 0.88/0.90/1.15、顶 0.90/0.92/1.20），目标中性浅灰（#B9B3A8 系）。模型文件、data、weather/灯光全局一律未动（灯光由 R2-T7 另做）。
- **验证**：本地无头 PASS=232 FAIL=0；CI godot-verify run #108（45419601737）success，VERIFY-SUMMARY PASS=252 FAIL=0；目视 18/18：00 两标签分开无叠字，05 墙 (156,163,159) 中性浅灰、黄雾已去，余 16 张无回归（03/09 逐字节同 #105）。详见 PROGRESS.md 同名一节。

## §17 外部素材来源总表（2026-11-24，R2-T16）

> 本节补齐此前缺失的来源记录：此前 BLENDER_MODELS.md 只在 §3.4 提 tevy 名字、§3 提 blue_metal_plate 等贴图名、§10 提 grass-side-colour，
> Poly Haven 9 套、ambientCG 4 套、Grab3D/kit-predios 楼体、Render a House 草的逐项链接全在 `assets/external/SOURCES.md` 里，不在本文档；
> `desks/`、`grass/` 新批草、R2-T3 树来源则连 SOURCES.md 里也没有。本节是全库唯一逐项总表，逐项可查。
> 核验（2026-11-24 23:0x CST，`curl -I -L`）：**死链 0 条**。核验分三档：● 直链与本地文件逐字节一致（SHA-256 比对）；
> ○ 资产页＋直链均返回 200；△ 单品页未定位，写“待补”（不编链接）——本节 △ 现为 0 项（盘点时 7 项待补，同轮 R2-T2/R2-T11 落地时已补齐单品页，本任务逐字节验明）。
> 首次 000 均属瞬时失败，重试后 200，见 SOURCES.md §10。
> 授权总则：除特别注明外，本节全部素材为 **CC0 1.0**（可自由改、商用、无需署名）；Render a House 另有“禁转售/禁并入模型库再分发”限制；
> Poly Pizza 逐模型分 CC0 或 CC-BY，需逐项确认（见表内 △ 项）。

### 17.1 PBR 贴图：Poly Haven 9 套（SOURCES.md §1.1，全 ○）

直链格式：`https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k/<slug>/<slug>_<diff|rough|nor_gl>_1k.jpg`；
资产页：`https://polyhaven.com/a/<slug>`。每套 3 张（diff=baseColor、rough、nor_gl=OpenGL 法线），1024×1024。

| 素材 | 用途（件） | 资产页 | 授权 |
|---|---|---|---|
| asphalt_01 | ov-road-main 沥青 | https://polyhaven.com/a/asphalt_01 | CC0 |
| concrete_wall_007 | st-base、di-walls 混凝土 | https://polyhaven.com/a/concrete_wall_007 | CC0 |
| white_stucco | 楼体墙面（ov-bldA/B/C、ov-lib 等，需染色） | https://polyhaven.com/a/white_stucco | CC0 |
| red_bricks_04 | ov-gym 红砖墙（需染色加深） | https://polyhaven.com/a/red_bricks_04 | CC0 |
| grey_roof_01 | pv-roof 屋顶面层、楼体屋顶（灰瓦面代防水卷材） | https://polyhaven.com/a/grey_roof_01 | CC0 |
| wooden_floor_01 | cl-desks 桌面、cl-floor-walls 木面 | https://polyhaven.com/a/wooden_floor_01 | CC0 |
| blue_metal_plate | pv-panels 框/汇流条、pv-mount 钢轨/支腿（已核实挂载，见 §9 `060877f`） | https://polyhaven.com/a/blue_metal_plate | CC0 |
| corrugated_iron_02 | ch-canopy 雨棚、支架/屋顶金属件（SOURCES.md 记载用途） | https://polyhaven.com/a/corrugated_iron_02 | CC0 |
| concrete_pavement_03 | ov-road-walk 南门广场/步道铺装 | https://polyhaven.com/a/concrete_pavement_03 | CC0 |

另：Poly Haven 草丛模型 Grass Medium 01（https://polyhaven.com/a/grass_medium_01，CC0）**未下载**——资产页 200，但直链多种格式均 404，`api.polyhaven.org` 本机 522/403，见 SOURCES.md §3。

### 17.2 PBR 贴图：ambientCG 4 套（SOURCES.md §1.2，全 ○）

直链格式：`https://ambientcg.com/get?file=<AssetID>_1K-JPG.zip`（302 跳转）；资产页：`https://ambientcg.com/a/<AssetID>`；
授权依据：https://ambientcg.com/license（全站 CC0 1.0）。`*_Color.jpg`=baseColor、`*_Roughness.jpg`、`*_NormalGL.jpg`（另有 NormalDX 备用，勿混用）。

| 素材 | 用途（件） | 资产页 | 授权 |
|---|---|---|---|
| Grass004 | ov-lawn / ov-field 草地地面（需染色调绿） | https://ambientcg.com/a/Grass004 | CC0 |
| WoodFloor051 | 木地板备用（与 wooden_floor_01 二选一，未挂载） | https://ambientcg.com/a/WoodFloor051 | CC0 |
| Plaster001 | 外墙灰泥备用（与 white_stucco 二选一，未挂载） | https://ambientcg.com/a/Plaster001 | CC0 |
| Concrete034 | 混凝土备用（与 concrete_wall_007 二选一，未挂载；1024×512） | https://ambientcg.com/a/Concrete034 | CC0 |

### 17.3 教学楼 / 教室模型（SOURCES.md §5“教学楼 / 教室模型”，全 ○；整栋均不直接采用，见 SOURCES.md §5.2）

| 模型（本地文件） | 用途（件） | 资产页 | 直链 | 授权 |
|---|---|---|---|---|
| tevy 学校楼 `buildings/school-building-tevy.glb` | 整栋不采用；入口雨棚/屋顶光伏板/体育馆侧翼可拆作部件参考（ov-gate、pv-panels、ov-gym） | https://tevy.dev/models/school-building | https://tevy.dev/models/school-building/v1/lod0.glb | CC0 |
| tevy 教室 `buildings/classroom-tevy.glb` | cl-desks 桌椅、cl-windows 门（已换件，见 §3.4）；讲台桌/书架/高柜未采用 | https://tevy.dev/models/classroom | https://tevy.dev/models/classroom/v2/lod0.glb | CC0 |
| tevy 走廊储物柜 `buildings/school-corridor-lockers-tevy.glb` | 备选：单柜可放走廊/教室后墙（未施工） | https://tevy.dev/models/school-corridor-lockers | https://tevy.dev/models/school-corridor-lockers/v1/lod0.glb | CC0 |
| Grab3D 学校楼 `buildings/school-building-grab3d.glb` | bldC 整栋候选（尺寸最接近，改色/改顶后可用；未施工） | https://grab3d.com/models/buildings/school-building/ | https://grab3d.com/dl/school-building/school-building.glb | CC0 |
| Grab3D 图书馆 `buildings/library-grab3d.glb` | 整栋不采用；柱廊/拱窗/天窗作部件参考 | https://grab3d.com/models/buildings/library/ | https://grab3d.com/dl/library/library.glb | CC0 |
| Grab3D 大学楼 `buildings/university-building-grab3d.glb` | 整栋不采用；窗户 mesh 可单独拆用 | https://grab3d.com/models/buildings/university-building/ | https://grab3d.com/dl/university-building/university-building.glb | CC0 |
| kit-predios 州立学校 `buildings/escola-estadual-kitpredios.glb` | 只作体量参考（bldC / ov-field 草稿） | https://github.com/kayquer/kit-predios-brasil-lowpoly | 仓库内 `models/publico/escola_estadual.glb` | CC0 |
| kit-predios 技术学校 `buildings/escola-tecnica-kitpredios.glb` | 只作体量参考（lab / ov-gym 草稿） | https://github.com/kayquer/kit-predios-brasil-lowpoly | 仓库内 `models/publico/escola_tecnica.glb` | CC0 |

注意：Grab3D 的 3 个 `.blend`（同目录）**全部是同一个 67,137 字节占位文件，不可用**，用同目录 `.glb`（见 SOURCES.md §5.3）。
tevy 的 `.glb` 用 `EXT_meshopt_compression` 压缩，Blender 4.2 自带导入器打不开，先用 gltf-transform 去压缩（见 SOURCES.md §5.3）。

### 17.4 草：草叶 alpha 贴图与草丛模型（SOURCES.md §5“草补找”，全 ○；用途 ov-lawn）

| 素材（本地文件） | 用途 | 资产页 | 直链 | 授权 |
|---|---|---|---|---|
| Render a House 草 PNG 切块 `grass/renderahouse-grass/`（7 张 RGBA：立面 2000×456、俯视 2000×1973） | ov-lawn 交叉面片贴图首选（`grass-side-colour.png`，1.02m 宽草坪条） | https://www.renderahouse.com/blog/free-grass-png | https://www.renderahouse.com/downloads/free-png-cutouts/grass/grass-png-cutouts.zip | 免费商用、无需署名，**禁转售/禁并入模型库再分发** |
| Render a House 草坪块 `grass/renderahouse-grass.glb`（另有 .fbx / -obj.zip 备用） | ov-lawn 边缘真草（150 株，0.2m 高草坪块） | https://www.renderahouse.com/blog/free-grass-3d-model | https://www.renderahouse.com/downloads/free-3d-models/grass/grass.glb | 同上（免费商用，禁转售/禁并入模型库再分发） |
| tevy 野草丛 `grass/tevy-wild-grass-clump.glb` | ov-lawn 自然野草丛点缀（0.6m，带贴图） | https://tevy.dev/models/grass-clump | https://tevy.dev/models/grass-clump/v1/lod0.glb | CC0 |
| 3DAssets 高草丛 `grass/3dassets-tall-grass-clump.glb` | ov-lawn 高草丛点缀（1m，纯色，染色后混用） | https://3dassets.dev/assets/wipe-day-survival-island-tall-grass-clump-99fa2311 | https://cdn.3dassets.dev/assets/27439/v1/model.glb | CC0 |

### 17.5 草：R2-T11 草重铺候选新批（2026-11-24 落盘，已由同轮 R2-T11 记入 SOURCES.md §6；R2-T11 施工中，尚未铺入 ov-lawn）

| 素材（本地文件） | 资产页 | 直链 | 授权 | 核验 |
|---|---|---|---|---|
| 3DAssets 沙丘草 `grass/3dassets/3dassets-dune-grass-tuft.glb` | https://3dassets.dev/assets/beach-surf-and-paddle-kit-dune-grass-tuft-ae12b134 | https://cdn.3dassets.dev/assets/39457/v1/model.glb | CC0 | ● 与本地逐字节一致 |
| 3DAssets 紫沼草 `grass/3dassets/3dassets-purple-moor-grass-tussock.glb` | https://3dassets.dev/assets/temperate-forest-ecology-purple-moor-grass-tussock-56681188 | https://cdn.3dassets.dev/assets/3849/v1/model.glb | CC0 | ● 与本地逐字节一致 |
| 3DAssets 木苔草 `grass/3dassets/3dassets-wood-sedge-clump.glb` | https://3dassets.dev/assets/temperate-forest-ecology-wood-sedge-clump-9f0b2abd | https://cdn.3dassets.dev/assets/3848/v1/model.glb | CC0 | ● 与本地逐字节一致 |
| 3DAssets 簇生发草 `grass/3dassets/3dassets-tufted-hair-grass.glb` | https://3dassets.dev/assets/temperate-forest-ecology-tufted-hair-grass-7d62ee65 | https://cdn.3dassets.dev/assets/3847/v1/model.glb | CC0 | ● 与本地逐字节一致 |
| tevy 草坪簇 `grass/tevy/tevy-lawn-tufts.glb`（另有 `-decoded.glb` 解压版） | https://tevy.dev/models/lawn-tufts | https://tevy.dev/models/lawn-tufts/v1/lod0.glb | CC0 | ● 与本地逐字节一致 |
| tevy 草甸草块 `grass/tevy/tevy-meadow-grass-patch.glb`（另有 lod1/lod2 及 `-decoded` 版） | https://tevy.dev/models/meadow-grass-patch | https://tevy.dev/models/meadow-grass-patch/v1/lod0.glb | CC0 | ● 与本地逐字节一致 |
| tevy 红燕麦草丛 `grass/tevy/tevy-red-oat-grass-clump.glb`（另有 lod1/lod2 及 `-decoded` 版） | https://tevy.dev/models/red-oat-grass-clump | https://tevy.dev/models/red-oat-grass-clump/v1/lod0.glb | CC0 | ● 与本地逐字节一致 |
| tevy 茅草簇 `grass/tevy/tevy-thatching-grass-tussock.glb`（另有 `-decoded.glb` 解压版） | https://tevy.dev/models/thatching-grass-tussock | https://tevy.dev/models/thatching-grass-tussock/v1/lod0.glb | CC0 | ● 与本地逐字节一致 |
| Poly Pizza 高草 `grass/poly-pizza/quaternius-grass-tall.glb`（mesh `Grass_Common_Short`） | https://poly.pizza/m/vUJjrRsFp4 | https://static.poly.pizza/0a84d74b-eb09-4794-ad58-dd10eed6b11e.glb | CC0（Quaternius，页内 "CC0 1.0"） | ● 与本地逐字节一致 |
| Poly Pizza 草簇 `grass/poly-pizza/quaternius-grass-tufts.glb`（mesh `Grass_Large_Extruded`、`Grass_Small`） | https://poly.pizza/m/UGTOzcO3P2 | https://static.poly.pizza/99357ca2-6364-4990-8d4c-9bc5a1a5e859.glb | CC0（Quaternius，页内 "CC0 1.0"） | ● 与本地逐字节一致 |

注：tevy 新草 4 件的本地文件与直链逐字节一致的 SHA-256 前 16 位：lawn-tufts `97cc610a0fe67957`、
meadow-grass-patch `9eae3876877776ad`、red-oat-grass-clump `ec0a0519ac57da76`、thatching-grass-tussock `29981ada7cd8dd39`。
3DAssets 4 件直链 CDN ID 与本地逐字节一致（dune 39457、purple 3849、wood 3848、tufted 3847）。
`grass/tevy/` 内 `-decoded.glb` 为 meshopt 解压后的同模型副本，无独立来源。

### 17.6 树：R2-T15 施工落地（2026-11-24 23:38 CST；R2-T3 方案来源已定，模型文件已下载入仓，ov-trees v3 已重建）

> 施工结论：473 棵（新种 327 + 旧树换模 146），ov-trees.py v3 + ov-trees.blend +
> ov-trees.glb（3,546,916 B）已重出，回读 473 个对象、零 Error/Traceback；
> 地上高实测行道树 5.0–8.0m、密植带 8.0–15.0m、池塘特征树 8.7–12.0m、楼间点缀
> 4.05–7.9m（抽查每区首棵 12 棵全在档内）；三角面 120,634（≤300k 预算）；
> L1 南沿线 31 棵已移出南主路（y=-94）、北沿线 2 棵已移出东主路（(98,105)/(118,105)），
> 两路面上残留 0 棵；来源与授权逐项见 SOURCES.md §11。
> 两处来源偏差（诚实记录）：① KayKit 免费档未拿到直链（itch `/purchase` POST 审批超时，
> 不再重试），密植带 216 棵改用 Kenney 松树（同 CC0，三角面更低）；② Quaternius
> Ultimate Nature Pack 的 Drive 配额耗尽，D3 改用同一作者同授权的 Stylized Nature
> MegaKit Standard（CommonTree_3/5 + Pine_4/5 各 3 棵）。
> L1 追加修正 4 处（校验发现，ov-trees.py `RELOC` 日志 37 棵逐棵列出）：南行东端 2 棵
> 在 y=-94 会压东主路 → (100,-94)/(124,-94)；广场段 5 棵会压南门广场铺装 →
> 广场两侧（x -44/-36/-28/28/36）；北沿线移位点与抖动邻树仅 1.7m/0.95m →
> (96,105)/(120,105) 去抖动钉网格点；旧树 (0,12) 压步道 2 → (4,12)，(-80,45) 压
> 新路 R-N1 → (-80,49)。遗留：西沿线 3 棵旧树在操场 3m 缓冲内（跑道面外，v2 原位，
> 保持不动）；密植带新旧交错 3 对间距 1.56–1.81m（方案设计 2.5m、抖动后收窄，冠层
> 交错，保留记录）。

| 来源 | 用途（ov-trees，473 棵实际） | 链接 | 授权 | 核验 |
|---|---|---|---|---|
| Kenney Nature Kit | 主力：全部行道树 + 楼间点缀 211 棵新种（`tree-default`、`tree-oak`、`tree-pineDefaultA/B`、`tree-detailed`、`tree-tall`、`tree-plateau`、`tree-thin`；原生 1.23–1.71m，放大至 5–8m / 点缀 4–7m）+ 密植带 216 棵（`tree-pineTall A–D` 及 detailed 版 + oak/tall，8–15m；KayKit 备用方案）+ 旧树换模 34 棵（路旁 19 + 楼间 15）；合计 461 棵 | https://kenney.nl/assets/nature-kit | CC0 1.0 | ● 直链下载，16 个 `.glb` SHA-256 见 SOURCES.md §11.4；包围盒/三角面/冠底逐项实测 |
| KayKit Forest Nature Pack（免费档） | **未下载**：原定密植带 104 棵改用 Kenney 松树（见上行与 SOURCES.md §11.5） | https://kaylousberg.itch.io/kaykit-forest | CC0 1.0 | ○ 页面 200；无直链（itch `/purchase` POST 审批超时，不再重试） |
| Quaternius Stylized Nature MegaKit Standard（代 Ultimate Nature Pack） | 仅 D3 池塘 12 棵特征树（`CommonTree_3/5`、`Pine_4/5` 各 3 棵，8–12m；原生 6.76–10.00m、1646–3505 tris）；严禁整片铺 | https://store.godotengine.org/asset/quaternius/stylized-nature-megakit/ | CC0 1.0 | ● Godot 商店直链下载，4 个 `.gltf` + 贴图 SHA-256 见 SOURCES.md §11.4；Ultimate Nature Pack 原定取 `Tree` / `Pine_Tree_1` / `Birch_Tree_1` / `Tree-Stylized`，其 Drive 配额耗尽无法直下，包内亦无此四名 |
| Blendkit（原 BlenderKit）免费区 | 备用：站内搜 tree，只取明确标 CC0 的资产；RF（Royalty Free）资产禁止用于本项目 | https://www.blendkit.com | 按单个资产，仅 CC0 可用 | ○ 首页 200 |
| Sketchfab CC0 区 | 备用：筛选 Downloadable + CC0 的树模型，逐模型确认授权页为 CC0 | https://sketchfab.com | 按单个模型，仅 CC0 可用 | ○ 首页 200 |
| Poly Haven 树木 | **禁用**：授权是 CC0，但扫描模型面数极大（Fir Tree 01 约 700 万 tris、Pine Tree 01 约 1,700 万 tris），总览用不上 | https://polyhaven.com/models | CC0 1.0（但不用） | ○ 页面 200 |

### 17.7 桌椅：R2-T2 换装候选（2026-11-24 落盘，已由同轮 R2-T2 记入 SOURCES.md §7；尚未换入 cl-desks）

| 素材（本地文件） | 资产页 | 直链 | 授权 | 核验 |
|---|---|---|---|---|
| Kenney 椅 `desks/kenney/chair.glb`、桌 `desks/kenney/desk.glb`、椅桌一体 `desks/kenney/chair-desk.glb` | https://kenney.nl/assets/furniture-kit | 套件 ZIP 在 `desks/kenney/furniture-kit.zip`（本地 GLB 由套件转换，UniGLTF 生成） | CC0（随包 `LICENSE-kenney.txt`：Furniture Kit 2.0，kenney.nl） | ○ 页面经浏览器打开确认存在且标 CC0（curl 403 系站方反爬） |
| 3DAssets 研讨桌 `desks/3dassets/seminar-table.glb`（Seminar Room Table，1.8m） | https://3dassets.dev/assets/university-lecture-hall-and-campus-seminar-table-1c6ce71f | https://cdn.3dassets.dev/assets/34746/v1/model.glb | CC0 | ● 与本地逐字节一致 |
| 3DAssets 研讨椅 `desks/3dassets/seminar-chair.glb`（Stacking Seminar Chair，mesh `stackable-chair`） | https://3dassets.dev/assets/university-lecture-hall-and-campus-stackable-chair-cb3333fb | https://cdn.3dassets.dev/assets/34749/v1/model.glb | CC0 | ● 与本地逐字节一致 |
| 3DAssets 1400 桌 `desks/3dassets/desk-1400.glb`（Computers and Desk Gadgets 系列，1.40×0.70m 板脚办公桌，备选） | https://3dassets.dev/assets/computers-and-desk-gadgets-desk-1400-c38edf1c | https://cdn.3dassets.dev/assets/38859/v1/model.glb | CC0 | ● 与本地逐字节一致 |
| 3DAssets 学生椅 `desks/3dassets/student-chair.glb`（Japanese School and City Street 系列，**选定**，见 SOURCES.md §7.1） | https://3dassets.dev/assets/japanese-school-and-city-street-student-chair-826ccbf4 | https://cdn.3dassets.dev/assets/30083/v1/model.glb | CC0 | ● 与本地逐字节一致 |
| 3DAssets 学生桌 `desks/3dassets/student-desk.glb`（Japanese School and City Street 系列，**选定**，见 SOURCES.md §7.1） | https://3dassets.dev/assets/japanese-school-and-city-street-student-desk-9e5d008a | https://cdn.3dassets.dev/assets/30081/v1/model.glb | CC0 | ● 与本地逐字节一致 |
| Poly Pizza 椅 `desks/polypizza/quaternius-chair.glb`（mesh `Chair_1`，约 2 倍比例尺木餐椅，不选） | https://poly.pizza/m/iMNqRzPwwe | https://static.poly.pizza/84ecc6a3-2751-4f50-912a-b9f4ff033d7a.glb | CC0（Quaternius，页内 "CC0 1.0"） | ● 与本地逐字节一致 |
| Poly Pizza 桌 `desks/polypizza/quaternius-desk.glb`（mesh `Desk_Drawer1-4`，古董办公桌，不选） | https://poly.pizza/m/V86Go2rlnq | https://static.poly.pizza/91c2bf8d-0876-4801-abd3-8dd5d017ecbd.glb | CC0（Quaternius，页内 "CC0 1.0"） | ● 与本地逐字节一致 |

### 17.8 未采用的参考源（未下载，仅作记录，避免后人重复找；见 SOURCES.md §3 及 §6 原版“教学楼模型：试过没成的渠道”）

| 渠道 | 结果 | 参考链接 |
|---|---|---|
| BlendSwap 学校/草丛模型 | 未下载（需登录） | Grass by gholm（CC0）https://blendswap.com/blend/4641 ；Realistic Grass Field（CC0）https://blendswap.com/blend/4678 ；Crenshaw High School（CC-BY）https://blendswap.com/blend/17192 ；Anime Classroom（CC0）https://blendswap.com/blend/19436 ；学校分类页 https://blendswap.com/3d/school-project |
| BlenderKit 窗/门/空调外机等部件 | 未下载（需免费账号 + 插件） | Outdoor Split Air Conditioner（FREE）https://staging.blenderkit.com/asset-gallery-detail/e9331d55-f079-4d03-aa06-3e063ae1f636/ ；Old Air conditioner exterior unit https://staging.blenderkit.com/get-blenderkit/82a5e776-362a-4b13-855e-09e8643158f3/ ；免费空调列表 https://www.blenderkit.com/asset-gallery-pure?query=tags%3AAC&page=1 ；建筑免费区 https://www.blenderkit.com/asset-gallery-pure?query=category_subtree%3Aarchitecture&page=6 |
| Sketchfab 免费下载区（knjaq 3 栋游戏建筑） | 未下载（需登录） | https://sketchfab.com/3d-models/3-unique-game-ready-buildings-73a2d53e6a5047789782329d0f268b93 |
| Open3DModel / Free3D / CGTrader 学校楼 | 未下载（无直链 / 需登录 / 页面被挡） | https://open3dmodel.com/3d-models/school-building ；https://free3d.com/3d-models/school ；https://www.cgtrader.com/free-3d-models/school-building |
| itch.io Low Poly Library & School Pack | 未下载（须走 itch 购买页） | https://reodesuxz.itch.io/low-poly-library-school-pack |
| Meshy.ai Classroom / University 模型库 | 未下载（须注册，AI 生成、质量未验证） | https://www.meshy.ai/tags/classroom |

### 17.9 本轮盘点结论（R2-T16 缺失清单结账）

- A 类（只有名字、BLENDER_MODELS 无链接；SOURCES.md 有）：Poly Haven 9 套、ambientCG 4 套、tevy 教室 3 件、Grab3D 3 件、kit-predios 2 件、Render a House 草 2 组、tevy 野草丛、3DAssets 高草丛——本节已全部补上（§17.1–17.4，共 25 项）。
- B 类（SOURCES.md 有、BLENDER_MODELS 完全没提）：同 A 类中的 Grab3D/kit-predios/ambientCG 备用套 + §17.8 未采用参考源——本节已补上。
- C 类（盘点时只有名字、连 SOURCES.md 也没有）：desks/ 8 行、grass/ 新批 10 行、R2-T3 树 6 行，共 24 行——本节已补上（§17.5–17.7）。
  盘点时其中 7 行单品页待补（Poly Pizza 草 2 + 桌椅 2、3DAssets 桌椅 3）；同轮 R2-T2（SOURCES.md §7）与 R2-T11（SOURCES.md §6）
  落地时已补齐这 7 个单品页，本任务对 7 条直链逐字节验明（SHA-256 与本地文件一致），**待补现为 0 项**。
  C 类核验：● 17 行（直链与本地逐字节一致）、○ 7 行（Kenney 桌椅套件 1 行 + 树方案 6 行，方案页/套件页 200）。
- 本节新增有据可查项 49 项（§17.1–17.7）+ §17.8 参考链接 9 组；待补 0 项。
- 本次核验死链 0 条；SOURCES.md 同步修正见其 §10（仅加核验注记，未改原有链接）。

### 17.10 还剩什么（待补 0 项）

1. R2-T3 树模型文件尚未下载（Kenney/KayKit/Quaternius）：本节只有方案页链接；R2-T15 施工下载落盘后，须在 SOURCES.md 补逐项下载记录。
2. 本文档编号重叠（非本节内容问题，留待后续整理）：同轮 R2-T2 与 R2-T11 各写了一个“§14”（课桌椅 / 草第二轮），
   R2-T8 写了“§16”、R2-T12 写了“§15”，顺序颠倒；本任务只把自己一节编号为 §17（空闲号），未动他人小节标题。
   SOURCES.md 同样存在两个“§6”与两个“§7”（原版 + R2-T11/R2-T2 新节），本任务的核验注记编号为 §10（空闲号）。

## §14 课桌椅网上模型 sourcing（R2-T2，2026-11-24 22:39–23:10 CST）

- **起因**：用户 2026-11-24 22:36 反馈桌椅建模还是不对，要求去网上找现成的桌椅 Blender 模型。
  上一轮 tevy 教室拆件用户仍不满意，本次只找模型、只下载、记来源，不建模、不手捏。
- **选定（3DAssets.dev，CC0）**：Student Desk + Student Chair（Japanese School and City Street 系列，
  同款层压木面 + 弯钢圆管架）：桌 0.60×0.50×0.70m、780 面，椅 0.38×0.42×0.89m、座高 0.42、580 面；
  48 套合计 65,280 面。文件 `assets/external/desks/3dassets/student-desk.glb` /
  `student-chair.glb`（资产页与直链见 `assets/external/SOURCES.md` §7.1）。
- **为什么 tevy 不行**：`desks`/`chairs` mesh 全是未焊接碎面（2,832/3,072 个 loose 碎片），只能 Voronoi
  聚类硬拆；椅 mesh 混进 2 个 1.16m 高柜、4 张椅各带 135–236 张柜面切不干净；单桌是双人桌一切二
  （0.61m 宽），桌腿不是完整几何；GLB 三重压缩（meshopt + quantization + KTX2）Blender 4.2 打不开；
  tevy 站内也没有独立的课桌椅模型。详见 SOURCES.md §7.3 与 `assets/blender/classroom/cl-desks.py` 头注。
- **对比过的其他家**：② 3DAssets Seminar Table + Chair（CC0，桌 1.8m 带桌面隔断屏，81 分）；
  ③ 3DAssets 1400mm desk + ②的椅（CC0，板脚办公桌，87 分）；④ poly.pizza Quaternius Desk + Chair
  （CC0，古董办公桌 + 2 倍比例尺餐椅，70 分）；⑤ Kenney Furniture Kit（CC0，玩具比例尺卡通方块，
  须约 ×2 缩放，74 分）。打分：结构真实度 40 / 尺寸合规 30 / 面数 15 / 授权与可取性 15。
  试过没成的：BlendSwap / Sketchfab / CGTrader（须登录或页面被挡，2026-11-24 复测）、
  Poly Haven（API 522）、BlenderKit（须账号 + 插件）、polyfork（CC-BY 且只有教师桌）、
  Vorpal 3D（授权不明）、itch.io 学校包（无直链）。全部见 SOURCES.md §7.2/§7.5。
- **核验**：10 个 `.glb` 全部 Blender 4.2.0 `--background` 只读导入实测（对象/面数/包围盒/
  逐 mesh 落地顶点数）+ Eevee 预览各 1 张（`assets/external/desks/previews/`，640×360），
  明细 `assets/external/desks/verify_results.json`。选定两件均真腿落地（各 508 个顶点在地面 z<0.02），
  目视确认桌架 4 管腿 + 钢丝书篮、椅架 4 管腿 + 横撑。
- **换装提示（下一波任务）**：两件米制实尺、落地点 y=0，单桌 0.60×0.50 与现行 tevy 单桌 0.61×0.61
  同级，6 列×8 排=48 套布局不用重排；桌高 0.70（SPEC 0.75，差 5cm 实测值不改比例）、椅座高 0.42；
  材质按 SPEC §3 染色（桌面 `#C8A06A`、椅面深色、钢架浅灰），原材质仅 2 种、无贴图。
  任务口径“桌 1.1–1.3m”指双人桌：两张选定单桌并排 = 1.20m，或改用备选 ③（1.40m 单张双人桌）。
- **未动**：`cl-desks.py` / `.blend` / `.glb`、Godot scripts/scenes/data 一律未碰；换装是下一波任务。

## §14 R2-T11 草地网上模型第二轮搜寻（2026-11-24 22:46–23:05 CST，只 sourcing，不建模）

- **起因**：用户 2026-11-24 22:42 硬性要求——草地去网上搜更好的现成模型，全部用网上的或基于网上下载的再改，
  不要再手搓。上一轮草（程序化 94,761 叶 0.15–0.35 m + 真草丛 8,140 株）总览仍是平板绿。
- **来源（7 家，3 家拿到）**：poly.pizza（Quaternius 草，CC0，直链）、tevy.dev（CC0，直链）、3DAssets.dev（CC0，直链）拿到文件；
  Poly Haven API 本轮连接失败（000）、Sketchfab 可下载模型是 CC-BY 且下载 401 需登录、CGTrader 空响应、
  BlendSwap 需登录（沿用上轮记录），均未拿到。详见 `assets/external/SOURCES.md` §6（含每家链接与授权）。
- **选定（CC0，可自由改）**：主选 **tevy 草甸草块 Meadow Grass Patch**（lod1 大面积 + lod0 近景 + lod2 远景），
  点缀 **tevy 红燕麦草丛 Red Oat Grass Clump**（lod1，lod0/lod2 备用）。文件在 `assets/external/grass/tevy/`，
  原文件（pinned v1）+ `-decoded.glb` 各一份，共 12 个 GLB 已推仓。
- **实测（Blender 4.2.0 只读）**：草甸 0.76 m 高、1.89×1.95 m 幅、lod1 2,030 面 / lod0 11,024 面 / lod2 304 面，
  核心 1×1 m 可 1 m 网格无缝拼，1024 KTX2 贴图（绿→枯黄叶尖 + 干草叶 + 穗）；红燕麦 0.98 m 高、0.98×0.93 m、
  lod1 824 面，锈红贴图点缀。比上一轮好在：高 0.76 m（程序化最高档 2.2 倍）、单丛覆盖大 19 倍、
  贴图渐变代替六色平片、整块草坪可拼满成片可见。完整对比表与打分见 SOURCES.md §6.2–6.3。
- **解码说明（格式转换，非手捏）**：tevy 原文件是 `EXT_meshopt_compression` + KTX2，Blender 4.2 与 Godot 内置导入器
  均不直读；用 glTF-Transform 4.5.1 无损解码 meshopt 生成 `-decoded.glb`（几何零改动，面数与原文件 accessor 计数一致，
  KTX2 贴图原样保留；Blender 实测包围盒与页标一致）。Godot 4.4 读 KTX2 以整合时 CI run 为准。
- **密度估算（草坪 1,911 m²，现行 ov-lawn.py 口径；R2-T3 GREEN_PLAN 未出，以它为准再定）**：
  lod1 拼满 1/m² = 3.88M 面；lod2 拼满 = 0.58M 面；推荐混合（程序化底保留 + lod1 0.25/m² + 红燕麦 lod1 0.05/m²）
  新增约 1.05M 面。换装/重铺是下一波施工任务，本轮未动 ov-lawn.py/.blend/.glb、ov-field 与任何 Godot 文件。
- **推仓**：12 个选定 GLB + `assets/external/SOURCES.md` + 本文档，一次 push-files，commit `8e84da3e`
  （`8e84da3e521a7c3edab1cd3f546c08fc1d573250`，父 `b346200a`；首推因 HEAD 被 R2-T2 抢先而 422 非快进，重推成功；
  仓库核对：草甸 lod1 大小 309,904 B / blob `11641d0d…`、lod1-decoded 369,960 B / blob `7c314874…` 均一致）。
  其余 10 个候选 GLB（poly-pizza 2、3dassets 4、tevy 茅草/剪草坪簇 4）留本地，凭 SOURCES.md §6 直链可重下。
- **还剩什么**：① 下一波施工按 GREEN_PLAN 把选定模型铺进 ov-lawn（换装/重铺）并重出总览；② 整合时 CI run 核对
  Godot 4.4 对 `-decoded.glb`（KTX2 贴图）的导入；③ R2-T3 绿化方案出后复核本轮密度估算档位。

## §16 R2-T8 汽车网上模型 sourcing（2026-11-24 22:46–23:15 CST，只 sourcing，不建模）

- **起因**：用户 2026-11-24 22:42 硬性要求——车的建模也去网上找，用网上的，不许手捏。现状是充电区
  ch-cars 3 辆手捏简易小车（蓝 #3B82C4、红 #C4534E、白 #D7DDE3）与停车区 ov-parking 3 辆简易小车，全部要换。
- **来源（7 家，3 家拿到）**：poly.pizza（Quaternius Cars 包，CC0，直链）、Kenney Car Kit 3.1（CC0，
  官网 JS 门控、经 OpenGameArt 镜像直链拿到整包）、Khronos glTF-Sample-Assets CarConcept（CC-BY 4.0，直链）拿到文件；
  Sketchfab 下载 API 401 需登录、BlendSwap 需登录（车分类页已 404）、CGTrader 免费区 202 JS 挑战页需登录、
  BlenderKit 搜索 API 可用但下载需账号，均未拿到。详见 `assets/external/SOURCES.md` §9（含每家链接与授权）。
- **选定（CC0，可自由改）**：Quaternius Cars 包三辆——**Car（蓝）** `cars/quaternius/car-quaternius.glb`、
  **SUV（白）** `cars/quaternius/suv-quaternius.glb`、**Sports Car 2（橙）** `cars/quaternius/sports-car-2-quaternius.glb`，
  共 3 个 GLB 已推仓。同一包出三色三款式，风格统一。
- **实测（Blender 4.2.0 只读导入，与 glTF JSON 直读一致）**：Car 4.22×1.81×1.18 m、2,954 面；
  SUV 4.21×2.11×1.53 m、3,294 面；Sports 2 为 3.97×1.80×1.16 m、3,066 面；三辆合计 9,314 面。
  结构：每辆 4 mesh（车身 + 后轮轴一体 + 左右前轮各一），车轮真几何（轮径 0.52 m，SUV 0.65 m）；
  车窗/前后灯是车身 mesh 上的独立材质面（Windows/Headlights/TailLights），非独立 mesh；
  车身单色材质（Blue/White/Orange）改一个 `baseColorFactor` 即换整车漆；全车无贴图，Godot 导入无贴图依赖。
  尺寸与目标 4.4×1.8×1.5 m 贴合（按长缩放到 4.4 m 仅 ×1.04–1.11）；SUV 宽 2.11 m，比目标宽 17%，换装时按车位核对。
- **为什么选这家、另外几家差在哪**：Kenney 次选——轮子独立、面数更低（2,032–2,474），但车窗/车灯只是共享
  512² colormap 贴图着色、无独立材质，2.55 m 玩具比例需 ×1.73 放大且原点沉在地下 0.30 m，换色要改共享贴图集；
  Khronos CarConcept 淘汰——结构最真（97 mesh 全内饰+刹车盘），但单辆 213,347 面、11.7 MB，3 辆 640k 面撑爆总览，
  且 CC-BY 需署名、只有一款概念车、包围盒轴向异常需重定向。完整打分见 SOURCES.md §9.3。
- **颜色对应**：蓝车身已是蓝色系、SUV 白即白车；包内无出厂红车，最接近红的是橙色 Sports 2，
  换装时把 Orange/DarkOrange 两材质的 `baseColorFactor` 改为 SPEC 红 #C4534E（改材质数值，不是手捏建模）。
  备选 Taxi 黄 / Police 白+警灯 / Sports Car 白均可凭 SOURCES.md §9.2 直链重下，但警灯/出租车顶灯与校园充电区不搭，不优先。
- **推仓**：3 个选定 GLB + `assets/external/SOURCES.md` + 本文档，一次 push-files，commit `445bad47`（2026-11-24 15:04:15Z，HEAD 核对一致；三车 blob SHA 与本地 md5 一致）。
  其余 7 个候选 GLB（Quaternius Taxi/Sports/Police/Car 2、Kenney 整包、Khronos CarConcept）留本地 /tmp，
  凭 SOURCES.md §9 直链可重下。
- **还剩什么**：① 下一波换装：把选定三车装进 ch-cars（充电区 3 辆）与 ov-parking（停车区 3 辆），
  核对朝向（glTF 前向 +Z，Blender 导入后长在 Y 轴）、统一缩放（按长到 4.4 m 或保留原生）、Sports 2 改红、
  SUV 宽度按车位核对，车漆可复用 ch-cars 旧清漆配方；② 换装后重出 charge/overview 场景 GLB 并走 CI 验收；
  ③ 本轮未动 `ch-cars.py` / `.blend` / `.glb`、ov-parking 与任何 Godot 文件。

## §15 R2-T12 云返工：网上实拍云照片 + Godot 侧接入（2026-11-24 22:46–24:00 CST）

- **起因**：用户 2026-11-24 22:43 硬性要求——云也要搞好，用网上的建模；去网上找现成的云模型/云材质
  （CC0，记来源），不许手捏。现状是 Godot 程序化白球（7 个白色半透明球 + 5 个圆柱云影），用户嫌假。
- **候选对比（3 家，详见 `assets/external/SOURCES.md` §8）**：
  ① Wikimedia Commons 实拍云照片（CC0/CC-BY）——**选定**，真照片、蓬松感最好、curl 直链；
  ② Poly Haven 云 HDR（`cloud_layers` / `kloofendal_48d_partly_cloudy`，CC0）——未选：360° 全景含地面/太阳，
  无孤立云朵可裁，等距投影还会拉伸；③ Sketchfab 云团模型——未选：搜到的前 3 条无一是云模型，
  可下载的须账号 OAuth（401），且多为低多边形卡通云。OpenGameArt/Kenney 只有像素/卡通云，未选。
- **选定（`assets/external/clouds/wikimedia-commons/`）**：
  `cloud_puff.png`（870×780，积云，晴/多云/阴用）——原图 WarmaFiesta《A single cumulus cloud in a clear
  daytime sky.jpg》，**CC-BY 4.0（须署名 WarmaFiesta）**；`cloud_storm.png`（1024×717，积雨云团，雨/暴雨用）——
  原图 Shyamal《Cumulonimbus viewed from airplane.jpg》，**CC0 1.0**。两张均由原图裁切 + 白度键抠天
  （min 通道 smoothstep + 裁切边羽化 + 去饱和），无手绘/手捏；本地目视验证：puff 为致密花椰菜状云顶、
  storm 为致密云团。试过没成的：CC0《Cumulus congestus clouds》塔身逆光亮边 + 暗蓝灰内腔，
  白度键与去饱和键都只能抠出细弧、留灰雾，已弃用。原图未入仓（直链 + SHA256 见 SOURCES.md §8，可重下）。
- **接入（只动云的部分）**：`scripts/weather_system.gd`——`_build_clouds` 改为 7 组云片（每组 1 主 + 2 小，
  同材质拼云团，`BILLBOARD_ENABLED`；体积云在 GL Compatibility 下不可行，故用贴图云片）；
  `set_weather` 按档换贴图（雨/暴雨 → storm）、按 `cloud_cover` 显隐（晴 1 / 多云 3 / 阴 5 / 雨 6 / 暴雨 7 组，
  中心向外）、按档缩放（0.9/1.0/1.12/1.18/1.25）；云影 blob 对齐到前 5 组云的地面投影；
  漂移时小云片跟主云片走。`data/weather.json`、天气切换逻辑、其他系统未动；
  贴图缺失时回退旧球体（`_build_clouds_legacy`）。
  `tools/verify_fixes.gd` +11 项云检查；`tools/shots_all.sh` +2 张（18 多云 / 19 阴天总览，旧 shots 无此两档）。
- **验证**：本地无头 verify **PASS=243 FAIL=0**（基线 232 项 + 云 11 项全过；首跑 240/243，
  3 项失败是本地全量导入未完成导致两张云贴图未加载，`No loader found`，同批 6 个场景 GLB 也未加载、
  非代码问题；后用同版本导入器对两张 PNG 定向导入生成 .import/.ctex，复跑 243/243）。
  CI godot-verify run **#111 / 45427988771**（HEAD `9bde93fa`，2026-11-24 23:39–23:57 CST，约 18 分钟）
  **completed/success**，VERIFY-SUMMARY **PASS=263 FAIL=0**（基线 252 + 云 11 项全过，云 11 项逐项见 job log）。
  截图 artifact `godot-screenshots` 20 张齐（含新拍 18/19），逐张目视天气档：
  18 多云通过（左上大朵蓬松白积云、实拍花椰菜纹理、边缘柔和，无生硬白球）、19 阴通过（同朵云压灰
  `#9fb2c0`、右侧第二朵云团入框、天空整体压暗，与阴档匹配）、07 暴雨通过（顶部多团深灰积雨云 +
  雨丝、画面压暗有暴雨感）、00 晴通过（仅 1 朵小积云，晴天少云）、06 雨 / 11 雨：雨丝与 V2G 弧线正常、
  无回归，但细节机位俯视屋顶、云不在帧内，雨档云片未直接目视（雨与暴雨共用 storm 贴图，仅 tint 与
  组数不同，07 已验证该贴图）。其余帧（01/02/03/04/05/08/09/10/12/13–17）布局、标签、面板与旧 run
  一致，无回归。
- **推仓**：commit `9bde93fa`（父 `1c39c0dd`），10 文件一次提交：`scripts/weather_system.gd`
  （blob `5e3dd6b5`）、`tools/verify_fixes.gd`（`af0bc6d5`）、`tools/shots_all.sh`（`c0cfbf7b`）、
  两张云 PNG（`082e96d6` / `180c4ec7`，601,153 B / 1,174,189 B）+ 两张 `.import`（`d3e23d84` / `de2bf8f8`）+
  `clouds/wikimedia-commons/README.md`（`56cc9b73`）+ `BLENDER_MODELS.md`（`2a4bfd2b`）+
  `assets/external/SOURCES.md`（`b0b36a69`）；推后 contents 核对 5 项 blob 与大小全部一致。
  （基底说明：推前 HEAD 已是 `1c39c0dd`；R2-T8 的 `445bad47` 曾连带发布本节草稿、R2-T20 的 `587007d9`
  又连带发布了本地同步版，本轮推仓改用仓库基底 staging、只动本节，其余任务的未推内容未带入。）
- **还剩什么**：① 总览取景天空带窄，静态截图一次只能看到 1–2 组云（其余组在帧外漂移，直播时会轮流飘入），
  云量档位以 verify 计数为准，不以单帧云朵数为准；② 雨档云片无总览帧直接目视（只有 06/11 细节帧），
  如需补一张雨天总览可在 shots 里加 `wx=rain` 总览帧；③ R2-T7 灯光（`25badadb`，本推之后落地）改了
  天空 tint 与暴雨天光/雾色，未动云代码，但会轻微改变云的观感，以它自己的 CI run 为准；④ 抠天脚本
  `/tmp/cloud-cand/make_sprites.py` 随一次服务重启 /tmp 清空而丢失，方法已全文记在 SOURCES.md §8.3，
  可凭原图直链重下复现。

## §18 R2-T18 草地重铺（2026-11-24，只改草地相关件）

- **起因**：GREEN_PLAN.md §4.3 的 21,555 丛新高草是按 4 tris/丛（程序化交叉面片）算的，
  与 R2-T11 选定的 tevy 真模型（lod2 304 / lod1 2,030 / lod0 11,024 面/丛）直接冲突——
  详见 GREEN_PLAN.md §8.1：R2-T11 推荐混合在新区 23,392 m² 上是 12.84M 面，
  21,555 丛全 lod2 也要 6.55M 面，而 ov-lawn headroom 只有 161,724 面。
- **最终混合配比（GREEN_PLAN.md §8.3，施工与验收以此为准）**：tevy 草甸 lod2 340 丛
  （drift 带 326 + 旧草坪叠加 14）103,360 面 + lod1 10 丛 20,300 面 + lod0 2 丛 22,048 面
  + 红燕麦 lod1 8 丛 6,592 面 + 红燕麦 lod2 10 丛 1,100 面 = **tevy 370 丛、153,400 面**；
  色带底板 163 块 1,956 面（4m 相间 `#69B45E`/`#57A04B`，每 5 条 `#7FC46A`，覆盖 22,472 m²）；
  既有程序化草 + 边缘真草 + 花坛/灌木/旧底板 238,276 面全留；**ov-lawn 总计 393,632 面 ≤400k**。
  （初版写 164 块 / 1,968 面 / 22,829 m² / 总计 393,644 面是旧跑道椭圆口径的估算；
  R2-T1b 操场收界后禁入椭圆改走新跑道（中心 (-62,-25)、长轴南北向、外椭圆 rx28/ry40 +1m），
  实测为 163 块 / 1,956 面 / 22,472 m² / 总计 393,632 面，余量 6,368。）
  §7 验收条“新高草丛 ≥21,500 丛”作废，改为 370 丛 + drift 带覆盖 + 4m 色带 100%。
  lod2 按区：G1 64 / G2 65 / G3 96 / G4 29 / G5 21 / G6 36 / G7 15；红燕麦点缀见 §8.3。
- **施工（`assets/blender/overview/ov-lawn.py`，只改本件；ov-field.py 未动）**：
  色带底板按区沿长边切 4m 条、0.5m 采样断开（路/楼/池塘/操场/花坛/灌木处不铺，连续段 ≥1m 才成块）；
  drift 带 3m 宽、带间距 12m（G7 20m），lod2 沿带中心线点状布放（丛距约 5.6m，丛距 ≥1.5m 去重）；
  lod1/lod0 只放旧草坪机位前方（TeachSouth 机位目标 (-16,5) 旁 2 丛 lod0 + 6 丛 lod1，
  GateNorth 4 丛 lod1）；新路 R-N1..R-N5 按 GREEN_PLAN 线位预留排除（路未进 ov-road-walk 前草先让开）。
  tevy 几何走 `-decoded.glb` 临时剥贴图版进 Blender 4.2（原文件不动），材质挂 ktx CLI 4.4.2
  解压的 PNG（`ov-lawn_textures/TEVY_*_color/normal.png`，色图直连 Base Color + Alpha 经 ROUND 进 Alpha、
  法线图直连 NormalMap，双面；绝不走 ColorRamp）。KTX2 贴图实测尺寸：草甸 lod0 色 1024²/法线 256²、
  lod1 色 512²/法线 256²、lod2 色 256²/法线 128²；红燕麦 lod1 色 512²、lod2 色 256²
  （SOURCES.md §6.2“1024 KTX2”只对 lod0 成立，已按实测更正）。
  禁入椭圆跟 R2-T1b 新跑道走（中心 (-62,-25)、rx28/ry40 +1m；旧椭圆 (-80,-25) rx40/ry28 已废，
  旧口径草会压到新跑道东沿/南北端）。另：5 个 tevy 材质加同色图自发光 0.35——
  本地 Cycles 预览发现密丛斜视/近景下丛心全黑（卡片互遮、太阳背面，俯视正常偏绿），
  单丛特写实测 0.35 后丛心变暗绿、结构可见（Translucent BSDF 试过，会把镂空区染成灰卡片，已否决）；
  GLB 直读确认 5 个 tevy 材质均带 emissiveTexture + emissiveFactor 0.35，alphaMode 仍为 MASK。
- **KTX2 导入结论（实测，非猜）**：Godot 4.4 **认 KTX2**（KHR_texture_basisu）——
  去量化后的 `-dequant.glb`（见下）本地 Godot 4.4 `--headless --import` 5 个全部通过，
  贴图转码为 `.ctex`（`.scn` + grass_color/normal `.ctex` 齐全，日志里只有无头 progress-dialog 噪音，
  与 CI 日志同款，无 KTX2/basisu 报错）；但 R2-T11 的 `-decoded.glb` 原样**进不了** Godot 4.4——
  解析在 `KHR_mesh_quantization`（extensionsRequired）处先失败，与 KTX2 无关
  （CI godot-verify run 45418604838 日志里 0 条 ktx/basisu/meshopt，因为当时还没有任何 KTX2 文件进项目，
  日志不能作证，需本地实测——已做）。ov-lawn.glb 本身走 Blender 导出（浮点几何 + PNG 贴图，
  无量化、无 KTX2），不受影响。
- **`-dequant.glb`（新增 5 个，`assets/external/grass/tevy/`，CC0 同源）**：
  glTF-Transform 4.5.1 `dequantize()`（`@gltf-transform/core/functions/extensions`，NodeIO 注册
  KHRMeshQuantization + KHRTextureBasisu + KHRMaterialsSpecular）：只去量化，KTX2 贴图、
  材质（含 specularFactor 0.3）与几何原样保留；`extensionsUsed/Required` 去量化后仅剩
  `KHR_materials_specular` + `KHR_texture_basisu`。5 个文件均经本地 Godot 4.4 导入验证通过，
  供以后直接进 Godot 用；`-decoded.glb` 原文件不动。文件：
  `tevy-meadow-grass-patch-dequant.glb`（1,626,412 B）、
  `tevy-meadow-grass-patch-lod1-dequant.glb`（455,636 B）、
  `tevy-meadow-grass-patch-lod2-dequant.glb`（109,948 B）、
  `tevy-red-oat-grass-clump-lod1-dequant.glb`（172,260 B）、
  `tevy-red-oat-grass-clump-lod2-dequant.glb`（45,128 B）。
- **验证**：本地 Blender 4.2.0 第 5 次运行（`ov-lawn-r2t18e.log`，2026-11-24 16:34 CST）：
  `blender_exit=0`、`DONE ov-lawn`，回读 8,802 对象 / 393,632 tris / 968,314 verts，0 Error / 0 Traceback，
  tevy 370 丛断言全过；本地 Cycles 双视角预览已目视（近景单丛结构可见、远景色带与草层可见，
  自发光修复后近景丛心由纯黑变暗绿）。Actions `blender-previews` run **45439933216**
  （head `4374a14b`）：**overview 组 success**，artifact `blender-previews-overview`（17,608,316 B）已下载逐张目视——
  `ov-lawn.png`：4m 色带全区清晰、drift 带点状草层沿带可见、旧草坪两块深绿区、池塘环、花坛与边缘真草都在，
  新跑道/球场禁入区干净无草；整 run 当时仍在等无关的 dist 组，结论以 overview 组为准。
- **推仓**：两 commit——`b93368de`（2026-11-24 16:25 UTC，22 文件：ov-lawn.py/.blend/.glb + GREEN_PLAN.md §8 +
  13 张新 PNG + 5 个 `-dequant.glb`）与 `4374a14b`（2026-11-24 16:40 UTC，4 文件：ov-lawn.py/.blend/.glb +
  GREEN_PLAN.md，自发光 0.35 修复 + §8 补记）；推仓时两次撞上并行任务的 422 not-a-fast-forward，重试后成功。
  另：BLENDER_MODELS.md §18 本段在 R2-T1b 提交 `3a20fea3` 时已被顺带推入（共享工作区文件被其 push-files 读到），
  本轮只补填本段的验证/推仓/还剩什么。
- **还剩什么**：总览重拼与 godot-verify 总览验收由终轮整合做；R-N2 路（x=-33）与新跑道 +3m 缓冲东尖（x=-31）
  约 1.5m 重叠，是路任务的遗留问题，本轮草地已同时避开路廊与新椭圆，不受影响。

## §18 R2-T17 桌椅换装（3DAssets）+ 教室墙面偏青绿修复（2026-11-24，只做教室）

- **桌椅换装**：`assets/blender/classroom/cl-desks.py` v3 → v4，tevy 拆件彻底换掉，改用 R2-T2 选定的 3DAssets Student Desk + Student Chair（CC0，`assets/external/desks/3dassets/student-desk.glb` 51,796 B + `student-chair.glb` 43,632 B；来源与选定理由见 SOURCES.md §7）。两件 timber + steel 各 1 网格，脚本内合并成一件模板（2 材质槽：desk_wood #C8A06A / chair_wood #7A4A2B / leg_metal #424A52，SPEC §3），沿用 v3 布局（6 列 × 8 排 = 48 套，ROW_X -3.18…3.82、COL_Y ±0.8/1.8/2.8、CHAIR_DX 0.44）。
- **朝向实测**：椅靠背（z>0.65 木面 y 0.148–0.196）与桌钢丝书篮（z 0.225–0.255 钢丝 y 0.146–0.175）都在 Blender +Y 一侧 = 学生侧，学生面向 -Y；绕 Z 转 -90°（Blender (x,y) → SPEC (y,-x)）后面向 -x、学生侧 +Y → +X，椅背断言（靠背顶点 x>0.05）通过。**坑**：join 后的网格上 `bpy.ops.object.transform_apply(rotation=True)` 静默失效（rotation_euler 清零但顶点不动，已用最小复现确认；单 mesh 上该 operator 正常）；居中与旋转改用 `mesh.transform(矩阵)` 直接烘顶点。第一版未转（桌宽 0.60 落在 x 向、椅子侧向）已废弃重出。
- **换装前后对比**：tevy 版：桌椅是 Voronoi 聚类拆出的碎面（单桌/单椅边界是猜的）、椅 mesh 混 1.16m 高柜（4 张带 135–236 张柜面）、桌腿不是完整几何（“悬浮金色平板”）、48 套间隙前 0.208m / 后 0.204m、cl-desks.glb 5,605,220 B / .blend 2,817,888 B；3DAssets 版：单桌 0.60×0.50×0.70m（780 面）、单椅 0.38×0.42×0.89m（580 面）、弯钢圆管桌架/椅架真腿落地（各 508 顶点 z<0.02）、桌带钢丝书篮、椅带横撑脚踏杆，48 套合计 65,280 面，间隙前 0.265m / 后 0.293m、桌椅包围盒 x[-3.430, 4.472]、cl-desks.glb 4,532,308 B / .blend 935,956 B，回读 96 对象（2 共享网格），零 Error/Traceback。口径偏差（接受，记入文档）：任务口径“桌 1.1–1.3m”指双人桌，两张 0.60m 单人桌并排 = 1.20m 正好落入口径；桌高 0.70 vs SPEC 0.75 差 5cm。
- **墙面偏青绿修复**：只改颜色，不动尺寸结构。根因不在材质本身：墙贴图 `white_stucco__F3E9D2.jpg` 100% 像素暖色（均值 243,232,210，0% 像素偏绿），Blender 预览也是米白；Godot 里墙渲成青绿 (94,136,118) 是因为天空材质 `ground_bottom_color #4a6b38`（绿）是室内环境光 `AMBIENT_SOURCE_SKY` 的地面色（`scripts/weather_system.gd:52`），白墙被绿天光照绿（白空调壳同渲 (93,132,124) 作证；PROGRESS.md 丢色一节同根因）。修法：墙材质 color 贴图后串 MixRGB MULTIPLY，线性补偿因子 (1.0, 0.39, 0.32)（按“渲染 = 反照率 × 环境光”反推，目标渲染约 (97,88,68) 暖色），导出器写成 `baseColorFactor [1, 0.39, 0.32, 1]` 与贴图相乘，等效反照率 sRGB 约 (243,151,123)。**两个导出器坑**：① Base Color 已链接贴图时 socket 默认值不被导出，只认 Mix 节点里的 MULTIPLY 常量；② 须用新 `ShaderNodeMix`（type MIX），旧 `ShaderNodeMixRGB`（type MIX_RGB）不被认，且 RGBA 的 A/B 是 inputs[6]/[7]（4 元）、输出 RGBA 是 outputs[2]，按名取 "A" 会取到 VALUE 槽。只补墙面；天花板同理发绿但 03 取景内不可见，不动。**代价**：Blender 预览（中性光）下墙直接显出暖粉补偿色，Godot 侧验收以 03-classroom 为准。改前改后：改前墙 baseColorFactor 缺省（贴图原色 #F3E9D2，Godot 渲青绿 (94,136,118)）；改后 baseColorFactor [1, 0.39, 0.32, 1]，cl-floor-walls.glb 7,491,220 B（改前 7,491,156 B）/ .blend 1,038,708 B，回读 73 对象，零 Error/Traceback。
- **场景重拼**：`assets/blender/scenes/classroom.py` 未改（已是最新拼装逻辑），重跑重拼：classroom.blend 5,465,640 B（改前 7,349,592 B）、classroom.glb 19,090,632 B（改前 20,164,540 B），回读 440 对象（73+96+39+58+54+120），桌椅间隙前 0.265m / 后 0.293m、门洞 clear，零 Error/Traceback；场景 GLB 实测墙因子在、48 桌 + 48 椅节点、0 个 tevy 残留。
- **推仓**：commit `72897e90`（https://github.com/ryc2077/campus-vpp-demo/commit/72897e9058371b8d65f0915733229c3f43f46e52），父 commit f868be10，12 个文件：cl-desks.py/.blend/.glb + 日志、cl-floor-walls.py/.blend/.glb + 日志、scenes/classroom.blend/.glb + 日志、BLENDER_MODELS.md §18；blob SHA 已逐项核对一致。推送时 HEAD 链：任务书 b346200a → 实测 2f436af7 → 1c39c0dd → 9bde93fa（R2-T12）→ f868be10；推后 HEAD 先后被 R2-T19、R2-T1b 推到 3a20fea3，本 commit 已在历史中。
- **验证**：blender-previews run #91（45428771914，head 72897e90）：classroom 组 completed success；artifact `blender-previews-classroom`（14938698965，4,064,908 B）6 张已逐张目视——cl-desks：48 套真桌椅，钢圆管桌腿/椅腿落地、桌下钢丝书篮与椅横撑近景放大可见，无悬浮平板；cl-floor-walls：Blender 预览（中性光）下墙面呈暖粉补偿色（亮面采样 (150,113,101)），属已记代价、预期内，几何完好（4 窗洞 + 门洞、天花板白）。godot-verify run #113（45428771704，head 72897e90）：VERIFY-SUMMARY PASS=261 FAIL=2，两项 FAIL 全是 R2-T19 的 S4 车顶 SOC 条（与本任务无关），教室零 FAIL、classroom 相机检查 PASS；但 workflow 顺序执行，verify 失败后 Export/截图步未跑，无 godot-screenshots artifact——03-classroom 目视未能完成。最新 run #116（45433047551，head 3a20fea3）同样 2 项 SOC FAIL、无产物。03-classroom 的 Godot 侧目视须等 SOC 条修好、某次 godot-verify 全绿出图后再补。
- **还剩什么**：① 03-classroom Godot 侧目视未完成（见验证；阻塞在 R2-T19 的 S4 车顶 SOC 条，非本任务范围）；② 黑板盒埋进西墙 15mm（cl-board 范围外，未修；03 目视时“黑板墨绿”一项可能因此不通过）；③ 天花板同理发绿未动（03 取景内不可见）。
- **本任务发现、范围外未修**：黑板盒埋进西墙——`cl-board.py` 的 Blackboard 盒中心 x=-4.80、厚 0.04（x[-4.82,-4.78]），西墙内面 x=-4.765，黑板正面埋进墙内 15mm；run #107 的 03-classroom 里黑板面与墙同色 (94,136,118)（只剩框/粉笔槽 faint 可见），属 cl-board 问题，不在本任务三件范围内，未动。

## §19 R2-T19 汽车换装（Quaternius 三车，2026-11-24，只改汽车两件 + 充电场景）

- **任务**：R2-T8 选定的 Quaternius Cars 包三辆（SOURCES.md §9，CC0）替换 ch-cars 与
  ov-parking 的 3+3 辆手捏小车；重拼 charge 场景；总览场景不拼（ov-parking 进总览由
  终轮整合任务统一做；R2-T1 也在重拼总览，不要抢）。产品代码（Godot scripts/scenes/data）
  一字未动；验收脚本 tools/verify_fixes.gd 随 S4 修复改了一处（见验证，协调者紧急授权）。
- **朝向实测（Blender 4.2.0 导入探针）**：三车 glTF 前向 +Z，导入后长在 Y 轴、车头
  （Headlights 面质心）在 -Y（car y=-1.99、suv y=-1.91、sports y=-1.80；尾灯在 +Y）；
  轮底 z≈0（car +0.01、suv -0.02、sports -0.01），基本贴地；每车 4 mesh（车身 +
  后轮轴一体 + 左右前轮各一）。换装时每车绕 Z 转 +90° 烘进 mesh（车头 -Y -> +X、
  车长落到 X 轴），与旧手捏车局部系完全一致；empty 保持旧旋转（充电区 -90° 车头
  朝南、停车区 +90° 车头朝北），位置与旧车一致。
- **缩放与改色方案**：
  - 充电区（车位 2.5 m 宽，线内缘 ±1.19 m）：三车均匀按长缩到 4.4 m（car ×1.0427、
    suv ×1.0451、sports ×1.1083），宽 1.89/2.21/1.99 m 均不压线（suv 半宽 1.10 m，余 0.09 m）。
  - 停车区（车位 2.0 m 宽，线内缘 ±0.94 m；均匀缩放后 suv 2.21 m、sports 1.99 m
    都会压线）：三车长 4.4 m、宽统一夹到 1.80 m（与旧手捏车同宽，每侧余 0.04 m）——
    灰 SUV (0.8531, 1.0451, 1.0451)、蓝 Car (0.9945, 1.0427, 1.0427)、
    红 Sports (1.0, 1.1083, 1.1083)（sx=宽、sy=长、sz=高，按导入轴向）。
  - 改色（只改材质数值）：Sports 2 的 Orange + DarkOrange 两材质 baseColorFactor 均改
    SPEC 红 #C4534E（GLB 实测线性 0.552/0.087/0.076）；蓝车漆改为旧蓝 #3B82C4、
    白车漆改为旧白 #D7DDE3（停车区 SUV 白改灰 #8A8F94），三色与旧车/campus.json 一致。
  - 车漆复用旧清漆配方（Metallic 0.15 / Roughness 0.25 / Coat Weight 1.0 /
    Coat Roughness 0.05）；车窗用已验证深色镀膜玻璃（透射 0.10、alpha 0.90、
    粗糙度 0.15、深色 #33505F、Specular 1.0）；轮胎 #2A2D2F/0.95、轮毂 #C0C5C9/
    金属 0.8/0.35、前灯暖白发光、尾灯红发光（均沿用旧配方）。
- **SUV 宽度核对**：充电车位 2.5 m——suv 均匀缩放后 2.21 m 宽，半宽 1.10 m < 线内缘
  1.19 m，通过（余 0.09 m）；停车车位 2.0 m——原生 2.11 m（半宽 1.055 m）已压进
  0.12 m 宽的车位线（线带 0.94–1.06 m），故宽向压到 1.80 m；灰 SUV 前轮北缘原
  在 -84.79 m、会顶轮挡南缘 -84.825 m（约 0.04 m），中心南移 0.10 m 至 y=-86.6
  后前轮北缘 -84.886 m、离轮挡 0.061 m，仍在 2 号位内（南缘 -88.8 > -89）。
- **Godot SOC 条锚点（关键）**：`scripts/campus_builder.gd _build_charge_glb_soc_bars`
  找 `ch-cars_<blue/red/white>` 组 + `ch-cars_<key>_roof` mesh，用
  `position.y + mesh AABB.y/2` 算车顶高、沿组局部 x 挂 3.4 m SOC 条。Quaternius
  无独立车顶 mesh，故车身主 mesh 改名 `_roof`、原点移到 mesh 高度中点
  （L = zmax - h/2，mesh 数据反向平移 -L，世界几何不动），使
  `position.y + AABB.y/2` 恰为车顶高（Godot 实测蓝 1.233/红 1.269/白 1.578 m，含轮底 lift）。
  GLB 导出保留节点 TRS（旧 charge.glb 实测），锚点关系可进 Godot：GLB 里
  `_roof` 节点 T=(0, L, 0)（L=0.705/0.729/0.912）、组节点绕 Y 转 -90°，与旧车一致。
  ov-parking 的车身主 mesh 同命名 `_roof`（仅为两件统一；总览不挂 SOC 条）。
  charge.py 车位检查改取 empty 下 4 mesh 并集（旧 `_body` 已无独立 mesh）。
- **坑（已踩，已修）**：`bpy.ops.object.transform_apply(rotation=True)` 在导入
  mesh 上静默失效（rotation_euler 清零、顶点不动；最小复现确认：scale 烘进去了、
  rotation 没烘进去；R2-T17 桌椅任务同坑）。旋转+缩放改用 `mesh.transform(矩阵)`
  直接烘顶点（`Matrix.Rotation(90°, 4, 'Z') @ Matrix.Diagonal(scale)`）。
  另：`transform_apply` 后 `matrix_world` 是旧值，须 `view_layer.update()` 再读。
- **重建结果（本地 Blender 4.2.0，零 Error/Traceback）**：
  - ch-cars：15 对象（3 组 + 12 mesh），GLB 9 材质（4 漆清漆 1.0/0.05、红=#C4534E、
    玻璃透射 0.10），ch-cars.glb 531,580 B / .blend 2,096,408 B；三车各在 1/3/4
    号位内、车头朝南、轮底 z=0.00。
  - ov-parking：50 对象（35 场 + 15 车），GLB 13 材质（漆/玻璃同上），
    ov-parking.glb 3,367,900 B / .blend 2,446,596 B；灰 2 号位、蓝 5 号位、
    红 9 号位，车头朝北、轮底落在沥青顶面 z=0.08。Paint* 三件套贴图已不再引用
    （文件留磁盘未删）；ov-parking 材质总数 13（旧约 13，车漆 3 种→4 种，
    总览重刷时材质总数 202 会变，终轮整合注意）。
  - charge 场景：重跑 charge.py（只改车位检查段），回读 123 对象（桩 40、车 15、
    标线 21、雨棚 47），三车各在位内、车头朝南、无桩穿插、雨棚全覆盖，材质去重
    117→24（车 9 种与旧版一致），charge.blend 3,002,296 B、charge.glb 7,093,272 B。
- **推仓**：commit `f868be10`（`f868be109c56d37da82491ed62385def671d1800`，父 `9bde93fa`）：
  10 文件一次提交——ch-cars / ov-parking 各 .py/.blend/.glb、charge .py/.blend/.glb、
  本文档；推后核对：HEAD 即该 commit，6 个大文件仓库大小与本地一致
  （ch-cars.glb 531,580 B / blob `5be9ed4a…`、ov-parking.glb 3,367,900 B /
  charge.glb 7,093,272 B、ch-cars.blend 2,096,408 B、ov-parking.blend 2,446,596 B、
  charge.blend 3,002,296 B）；ch-cars.glb 本地重出后 531,580 B（首版记录 531,560 B
  为旧值，已修正）。
- **验证**：
  - blender-previews run **45428349915**（push 触发，HEAD `f868be10`）：completed/**success**，
    6 组全绿（charge 组 success、overview 组 success）。artifact `blender-previews-charge`
    （3,942,972 B）：ch-cars.png 已目视——蓝/红/白三色分明，各车 4 轮 + 深色车窗 + 前后灯
    齐全，车头朝南，红车呈红非橙（#C4534E 改色生效）；artifact `blender-previews-overview`
    （18,405,530 B）：ov-parking.png 已目视——灰 SUV 2 号位/蓝 5 号位/红 9 号位，各在
    划线内无压线（灰 SUV 两侧留空隙），三色分明，车轮车窗车灯齐全，车头朝北。
  - godot-verify run **45428350351**（HEAD `f868be10`）：completed/**failure**——VERIFY-SUMMARY
    **PASS=261 FAIL=2**，两项 FAIL 全是 S4 车顶 SOC 条（回退 1.84 / GLB 1.465，条底
    top=1.375）。根因：`tools/verify_fixes.gd` S4 GLB 分支写死旧手捏小车车顶 1.375/
    条中心 1.465，而三辆 Quaternius 真车车顶高不同（蓝 1.233/红 1.269/白 1.578）；
    `campus_builder.gd` 本就逐车算（`position.y + AABB.y/2`），条子实际位置正确，
    错的是检查的期望值。该失败还阻塞全线：verify 失败后 Export/截图步不跑、0 artifact，
    run #112–#116 全部同因同败（R2-T17/T18 核实）。
  - **S4 修法**（commit `0b6b8ae8`，`0b6b8ae8acee34015eb89455a5d73f3eb9ba1dae`，父 `b93368de`，
    协调者紧急授权）：只改 `tools/verify_fixes.gd` S4 GLB 分支——逐车从本车 `_roof` mesh
    算期望车顶（`roof.position.y + mesh.get_aabb().size.y/2`，与 campus_builder 同口径），
    条中心期望 = 车顶+0.09、条底期望 = 车顶，不再写死 1.375/1.465；回退分支（1.84/1.75）
    不动；产品代码与车几何一字未动。本地 Godot 4.4 `--check-only` 校验通过（exit 0）。
    曾考虑的另两条路均否决：① 锚点谎报 1.375——条子会浮在蓝/红车顶上 0.15/0.10 m、
    埋进白 SUV 车顶内（条顶 1.555 < 车顶 1.578），CI 绿但图错；② 三车高向压到统一
    1.375——SUV 被压扁 13%、轿车拉长 8–11%，违背任务缩放口径。
  - godot-verify run **#119 / 45437816576**（HEAD `0b6b8ae8`）：completed/**success**，
    VERIFY-SUMMARY **PASS=271 FAIL=0**；S4 三项 PASS（条底 ch-cars_blue=1.233、
    ch-cars_red=1.269、ch-cars_white=1.578）；godot-screenshots artifact（12,362,828 B）
    19 张。04-charge.png 已目视——三车在桩前雨棚下，蓝/红/白分明，车顶 SOC 条各贴在
    各自车顶（白 SUV 条子位置更高），V2G 桩前位置正确，面板“在场车辆 3 辆（带 SOC 条）”；
    12-charge-sunny.png 同视角确认（V2G 放电 54 kW）。
- **还剩什么**：总览场景重拼由终轮整合任务做，本任务未拼；ov-parking GLB 材质 13
  （车漆 3→4 种），总览重刷时材质总数 202 会变，终轮整合注意。S4 已全绿，run #112–#116
  的阻塞已解除，其他任务的 Godot 目视可在后续全绿 run 出图后补。

## §20 R2-T10b 楼房网上模型第二轮搜寻（2026-11-24 23:23–24:00 CST，只 sourcing，不建模）

- **任务**：接替中断的 R2-T10（上一任运行时重启中断，无任何新下载，本轮从零开始）。
  用户 2026-11-24 22:42 硬性要求：楼房全部用网上现成模型或基于下载修改，不再手搓。
  9 栋手捏量块楼体（ov-bldA/B/C、ov-lib、ov-gym、ov-lab、ov-tower、ov-canteen、ov-dorm）
  要找网上模型替换。只找模型、只下载、记来源；**未改任何 ov-bld\*.py/.blend/.glb，
  未碰 Godot scripts/scenes/data**。换装是下一波任务。
- **来源（8 家对比，5 家拿到文件；详见 SOURCES.md §12）**：Kenney City Kit Commercial
  2.1（CC0，cookie+签名链接下载整包）、vinish.dev 彩色小镇 6 栋（CC BY 4.0，直链）、
  Grab3D Cozy 系列 11 个（CC0，直链 `grab3d.com/dl/<slug>/<slug>.glb`）、tevy 医院楼
  （CC0，直链）、poly.pizza 9 个（Google Poly 档案，模型页内嵌 static 直链；API 搜索
  现须 key，改走网站搜索页，扫了 5 个词、117 个模型页）。拿不到的 3 家均已亲手确认：
  Sketchfab 下载接口无 token 返 401、BlendSwap 搜索页 301 空页、CGTrader 免费页 202 空页。
- **核验（Blender 4.2.0 `--background` 只读导入）**：47 个 GLB 全部实测，46 个成功、
  1 个失败（tevy 医院楼原文件 meshopt+KTX2 打不开，已按上一轮教室的办法解压出
  plain 版：`gltf-transform copy` 解 meshopt → 剥贴图 + dequantize → Python 删
  `KHR_texture_basisu` 声明，JSON 块填充须用空格、NUL 会报 `Bad glTF: Extra data`；
  plain 版 54.0×38.5×32.34、5 mesh、54,066 面）。另逐 mesh 复核 5 个重点文件
  （发电厂/医院 plain/办公楼/购物中心/酒店）。Grab3D 11 个资产页标称尺寸与三角数
  与实测逐项一致；vinish 页标（办公塔 70m/14 层、钟楼 33m、商场 48m 宽）与实测一致。
- **逐栋推荐（SPEC §4 尺寸是实测，绝不能改尺寸去套模型；详见 SOURCES.md §12.3）**：
  - **可直接换**：tower ← vinish 钟楼 13.2×13.2×32.7（×1.06/×1.06/×0.98，全轮唯一
    近等比；去钟面/尖顶/风向标、加层间带读 8 层）；dorm ← Grab3D 公寓楼
    15.6×13.8×18.3（×1.29/×0.87/×0.87；改浅橙 `#F6D9C0`、去屋顶露台花坛）；
    lib ← Grab3D 办公楼 body 29.4×18.7×25.6（×0.82/×0.85/×0.86；改色+博物馆柱廊入口）。
  - **bldC 沿用旧件**：本轮无新模型胜过 11-23 已入库的 Grab3D 学校楼
    （22.9×13.9×16.7，×0.96/×0.94/×0.84）；新候选 pastel-townhouses 只有 2 层+坡顶，
    改 4 层教学楼工作量更大。
  - **勉强换骨架、窗带须重排**：bldA / bldB 共用 Grab3D 办公楼（facade/body，不同缩放
    与配色区分），高向压 22–26% 会把层高感压矮，窗带须按 SPEC 层高重排。
  - **只能参考局部、量体重建**：gym（超市 36m 宽量体概念+医院入口雨棚）、lab
    （发电厂 `windows` 窗带 mesh 改长 + `switchyard` 屋顶设备）、canteen
    （博物馆柱廊入口概念 + 食堂房间取餐台）；网上没有对应体量的整栋。
- **选定文件（48 个，共 62,640,082 字节，约 59.7 MiB；未覆盖 11-23 旧文件）**：
  `buildings/kenney/`（整包 ZIP + 19 个主楼 GLB）、`buildings/vinish/`（6 栋）、
  `buildings/grab3d/`（11 个，含食堂室内房间 1 个、只作室内参考）、`buildings/tevy/`
  （医院楼原文件 + plain 版）、`buildings/polypizza/`（9 个）。
  授权：CC0（Kenney、Grab3D、tevy、poly.pizza 内 7 个）；CC BY 4.0（vinish 6 栋，
  署名 vinish.dev）；CC-BY 3.0（poly.pizza 2 个校舍，署名 Poly by Google / jeremy）。
- **推仓**：5 批 push-files，48 个文件一次未超 40MB 单 blob（最大单文件 4,789,136 B）：
  Kenney `f16a77d6`（20 文件）、vinish `27ac65e6`（6 文件）、Grab3D `b58612df`（11 文件）、
  tevy `4ebc7ea0`（2 文件）、poly.pizza `a81ebbdc`（9 文件）；两份文档随第 6 批推，
  commit `1e0cdb93`（`1e0cdb9352128abadc8997e79b0d16930dbd7d29`，父 `a81ebbdc`）。
  推后核对：HEAD 即 `1e0cdb93`；contents API 逐目录核对 48 个文件大小与本地逐项一致
  （kenney/glb 19/19、vinish 6/6、grab3d 11/11、tevy 2/2、polypizza 9/9、zip 1/1），
  SOURCES.md 119,546 B 一致；本段为补记 docs commit 的 follow-up 提交，见下。
- **验证**：待填（换装任务不在本轮；本轮只核验了文件可导入与尺寸/面数，未做换装后渲染）。
- **还剩什么**：换装待下一波任务——tower/dorm/lib 直接换、bldA/bldB 换骨架+重排窗带、
  bldC 沿用旧件、gym/lab/canteen 量体重建+偷部件；Godot 侧总览重刷与目视由终轮整合做。

## §21 R2-T21b 楼房换装：gym / lab / canteen 量体重建+偷部件（2026-11-25 00:00–01:30 CST，只改这 3 栋）

- **任务**：R2-T10b（SOURCES.md §12 / 本文件 §20）结论——gym、lab、canteen 网上没有
  对应体量的整栋，只能参考局部、按 SPEC §4 实测量体重建并偷部件。用户硬性要求：
  全部用网上的、或基于网上下载的再做修改，不要再手搓大件。本任务只改
  `ov-gym.py/.blend/.glb`、`ov-lab.py/.blend/.glb`、`ov-canteen.py/.blend/.glb`
  + 共用帮手 `_steal.py`（新增）、`_pbr_apply.py`（R2-T9 的本地帮手，仓库里此前
  没有，本次首次入仓，含 R2-T21b 的 `_load` 修法）+ 本文件记录；
  未动 tower/dorm/lib/bldA/bldB、跑道/道路/树草、Godot scripts/scenes/data、
  未拼总览场景（总览重拼由终轮整合做）。
- **量体一字未动**：gym 36×16×18m 3F（中心 (-70,60)）、lab 42×12×13m 3F
  （中心 (-28,62)）、canteen 32×13×15m 3F（中心 (60,56)）；层高/檐口/女儿墙/
  屋顶板/台阶/空调外机/屋顶设备全部保留原样。新旧 GLB 节点逐名比对：除下述
  入口/窗带替换外无任何对象丢失（gym 188→181、lab 358→286、canteen 322→321，
  差额与替换清单逐项对得上；旧 GLB 节点数以仓库实测为准，gym 本文件旧文称 192
  是 11-23 烘焙跑时的计数，仓库旧 GLB 实际为 188）。
- **偷件做法（共用帮手 `assets/blender/overview/_steal.py`）**：`import_crop`
  导入源 GLB、按世界坐标包围盒裁出部件（只留全部顶点都在盒内的面）、按源材质名
  重映射到本件材质；`place`/`dup_place` 按目标包围盒逐轴缩放+平移并烘进 mesh。
  不改源文件，不改本件量体。

### 逐栋结果

- **ov-gym 艺体馆（回读 181，.blend 2,643,384 B / .glb 6,920,824 B）**：
  入口雨棚+双柱（8 件手捏）换成 tevy 医院楼 `entrances` mesh 裁出的主雨棚
  （`buildings/tevy/hospital-building-tevy-plain.glb`，CC0；裁盒 x 10..24、
  y -21.5..-12.25、z -0.04..5.2，1692 面：雨棚板+钢柱+玻璃），按
  (0.75, 0.486, 0.72) 缩到 10.5×4.5×3.78m，放在南立面正门前
  （x -75.25..-64.75、y 47.4..51.9、顶 3.80m，离墙 0.1m）；台阶与玻璃正门保留。
  vinish 超市只作量体参考（36m 宽+平屋顶与本件一致，单 mesh 不可拆，未偷件）。
  红墙 #8E2F28 + 深灰屋顶 #424A52 不变。
- **ov-lab 实验楼（回读 286，.blend 4,315,977 B / .glb 11,995,028 B）**：
  长面 7 段窗带的玻璃盒+竖挺+横中挺（84 件手捏）换成 Grab3D 发电厂 `windows`
  mesh 裁出的一行真窗（`buildings/grab3d/power-plant-grab3d.glb`，CC0；裁盒
  y<-7、z 3.0..6.0，16.55×0.21×2.40m，158 面：白框+玻璃+薄荷绿件，薄荷绿件
  重映射为窗框、玻璃重映射为本件玻璃 #9FC3D8），每段 1~2 块并排拼到 SPEC 带长
  （改长：F1 南两段各 1 块、其余每段 2 块），z 拉到带高；12 条偷窗带落位实测：
  F1 带 z 1.4..3.0、F2 带 z 5.1..6.9、F3 带 z 9.1..10.9，F1 南门洞 x -31.5..-24.5
  留空，窗带出墙 0.03..0.15m；短面窗带、红饰带、檐口、女儿墙（顶 13.0m）、
  空调外机 42 台、正门+台阶、屋顶设备全部保留。发电厂 `switchyard` 只作屋顶设备
  参考，未偷件。蓝灰墙（SPEC §5，`_pbr_apply` 映射 PLASTER_DFE9F2）。
- **ov-canteen 餐厅（回读 321，.blend 7,605,835 B / .glb 13,925,492 B）**：
  手捏雨棚+双柱（4 件）换成 Grab3D 博物馆 `museum_body` 前廊
  （`buildings/grab3d/museum-grab3d.glb`，CC0；裁盒 y<-8、z<9，24.74×1.75×8.48m，
  3730 面：16 柱+额枋+台阶，原石材 atlas 材质保留），均匀约 ×0.55 缩到
  13.6×1.0×4.66m，立在南门台阶外（x 53.2..66.8、y 47.0..48.0）；正门与台阶保留。
  另加室外取餐台：Grab3D 食堂房间 `cafeteria_body` 裁取餐区
  （`buildings/grab3d/cafeteria-grab3d.glb`，CC0，4×4×3m 室内房间；裁盒
  x -0.6..1.9、y 0.2..1.9、z 0.3..1.8，2.48×1.64×1.43m，14396 面）+ 同变换的
  取餐台玻璃罩 `cafeteria_food_well_guard_glass`，约 ×1.21 缩到 3.0×2.0×1.73m，
  放在南门西侧（x 49.5..52.5、y 46.5..48.5）——楼体是实心量块、室内放不下，
  故作室外取餐台，与台阶/柱廊无穿插。浅橙墙 #F6D9C0 不变。

### 材质：烘焙取消，改 PBR 直挂

- 三件的 Cycles 烘焙（每件约 1 小时）全部取消：PBR 材质在脚本里直接链真实 CC0
  照片贴图（`_pbr_link_direct`，与 `_pbr_apply.SETS` 同源），`_pbr_hook` 随后把
  同一批图再 swap 一次（幂等）并按世界尺寸重投 UV；玻璃与素色金属/框料保持原样。
  GLB 实测：gym 9 张图（4 种 PBR 材质各 color/rough/normal 全套）、lab 13 张图
  （5 种 PBR 材质全套）、canteen 19 张图（5 种 PBR 材质全套 + 博物馆 atlas 3 张 +
  食堂 atlas 1 张）；回读校验改为只有 PBR 直挂材质须带 3 张图（旧校验要求全部
  非玻璃材质带 3 张图是烘焙时代的假设；另修了校验里回读材质名带 `.001` 后缀
  导致名字比对失效的 bug）。
- 旧 `ov-*_textures/` 烘焙图已无任何引用，留待以后清理（本次未删）。

### 修掉的两个 bug（都在共用帮手里，R2-T21b 实测定位）

- **`_pbr_apply.py` 的 `_load` 存了坏的相对路径**：`bpy.path.relpath(key)` 在无
  .blend 打开的 fresh 会话里返回家目录相对路径（`//workspace/...`），存盘后
  解析不到文件，存盘时即卸掉像素，导出时报 `Image has no size and cannot be
  exported`、GLB 只剩 1 张 243 字节空白图（首版 gym GLB 仅 440KB）。修法：
  `_load` 改按 BLEND_PATH（由件脚本传入 exec globals）或已打开的 .blend 所在
  目录算 `//../../../assets/...` 相对路径；无 BLEND_PATH 时留绝对路径。修后
  gym GLB 6.9MB、9 张图全套，零警告。此修也惠及以后所有用 `_pbr_hook` 的件。
- **`_steal.py` 的 `bbox_world` 用了 stale 的 `bound_box`**：bmesh 改完 mesh 后
  `obj.bound_box` 还是旧值，`place()` 按错尺寸缩放（gym 雨棚首版只剩 4.45m 宽、
  偏到东侧）。修法：直接读 mesh 顶点算包围盒。另：lab 窗行裁盒初版 z 只取玻璃
  行 [3.8, 5.2]，把窗框面切掉只剩东侧 3.5m/84 面，改取整行 [3.0, 6.0] 后为
  16.55m/158 面。

### 推仓

- 5 批 push-files，12 个文件一次未超 40MB 单 blob（最大单文件 13,925,492 B）：
  脚本 `7aa927fe`（ov-gym/lab/canteen.py + `_steal.py` 新增 + `_pbr_apply.py`
  首次入仓）、.blend `7d5de9cf`、.glb `1a8e3b98`、本文档 `4e4dfcc7`；
  另 1 批补推 PBR 贴图 `4228878e`（见下“品红”一段，25 张），
  1 批 fix-up `60896d31`（恢复 `4e4dfcc7` 误覆盖的 R2-T1b 填充
  `192bb97b`——两批在同一分钟内先后写同一文件，事后已核对恢复；
  另 §21 一处措辞修正：`_pbr_apply.py` 是首次入仓非修改）。
  推后核对：HEAD 即 `60896d31`；contents API 逐文件核对 12 个文件大小与本地
  逐项一致（.py 5/5、.blend 3/3、.glb 3/3、BLENDER_MODELS.md blob
  `105db052…`）；`_pbr_apply.py` 与 `_steal.py` 在推前查仓库树确认此前不存在。
- **品红事故与补推**：首版 Actions 渲染（run #95，head `7d5de9cf`）3 栋楼墙面全
  品红——缺图色。根因：`_pbr_apply.SETS` 引用的 27 张贴图里 25 张只在本地、
  从未入仓（`pbr-tinted/` 20 张 + polyhaven 粗糙/法线 5 张；R2-T9 只建未推；
  仓库里只有 ambientcg Plaster001 rough 与 polyhaven concrete_wall_007 rough
  2 张）。GLB 不受影响（贴图已内嵌，Godot 侧无恙），只坏 Blender 预览渲染
  （.blend 存 `//../../external/...` 相对路径，Actions 检出后找不到文件）。
  已补推 25 张（commit `4228878e`，CC0，SOURCES.md §9 已有 pbr-tinted 记录）；
  注意该提交只动 `assets/external/**`，不触发 blender-previews（workflow 只监听
  `assets/blender/**`），故另用 workflow_dispatch 触发 run #104。
  另：R2-T21a 的 ov-tower 同病（commit `77c73269`）改用“打包进 .blend”修法，
  本任务仍用“补推贴图”修法，两法都通，不必统一。

### 验证

- blender-previews run **#104 / 45448772104**（workflow_dispatch，head `e0eaadf1`，
  含贴图补推）：completed/**success**；artifact `blender-previews-overview`
  （17,975,067 B）20 张
  已下载，3 栋逐张目视通过——
  - **gym**：红砖墙 #8E2F28 + 深灰屋顶，3 层蓝玻璃窗带，tevy 偷件雨棚（浅灰
    混凝土板 + 3 根细柱）正门前落位正确，无穿模。遗留小瑕疵：雨棚下地面有
    3 条细黄线（tevy 雨棚自带的 yellow_paint 地面标线，贴地、读作停车线，
    不影响结构，暂留）。
  - **lab**：蓝灰墙 + 深灰屋顶 + 红饰带，3 层清晰；长面 12 条偷窗带为白框+
    蓝玻璃小窗格的通长带窗（发电厂窗行本色，白框占面大、远看偏白，近看蓝
    玻璃格可见），短面为整片蓝玻璃带，正门雨棚+台阶+玻璃门齐全，无穿模。
    法向核过：偷窗带玻璃/框面为闭合小盒（±x/±y/±z 各 8/18 面），正反两面
    都有面，Godot 单面渲染也不丢。
  - **canteen**：浅橙墙 + 深灰屋顶 + 红饰带，3 层清晰；博物馆偷件柱廊 8 根
    白石柱 + 台座正门前落位正确，室外取餐台（红柜 + 台面食物 + 玻璃罩）在
    柱廊西侧可见，长面灰玻璃带窗齐全，无穿模。
- godot-verify 总览验收由终轮整合做（本任务未做）。
- **还剩什么**：tower/dorm/lib/bldA/bldB 换装（R2-T21a 另做）；总览重拼与 Godot
  侧验收由终轮整合做；旧 `ov-gym/lab/canteen_textures/` 烘焙图已无引用，待清理。

## §22 R2-T22 教室黑板盒埋墙修复（2026-11-25，只改 cl-board.py + 教室场景重拼）

- **问题**：`assets/blender/classroom/cl-board.py` 的 Blackboard 盒中心 x=-4.80、厚 0.04（x[-4.82,-4.78]），西墙内面 x=-4.765，板面埋进墙内 15mm；run #107 的 03-classroom 里黑板面与墙同色，只剩框/粉笔槽 faint 可见（R2-T17 §18 遗留②）。
- **修法**：只改 cl-board.py，黑板组整体沿 +x 平移 0.018m（黑板尺寸、墙一字未动）：Blackboard 中心 -4.80→-4.782（盒 x[-4.802,-4.762]，板面露出墙面 3mm、背面仍在墙内）；4 条银灰框 -4.79→-4.772（框面 -4.747，原与墙面齐平 -4.765、易 z-fight）；粉笔槽 -4.78→-4.762、槽唇 -4.745→-4.727、4 支粉笔与板擦 -4.76→-4.742；相对位置与尺寸全未动。展示板（WhiteBoard，板面 -4.80）同样埋墙，但需 +35mm 以上才露出、属另一处，未动，见还剩什么。
- **重建**：重跑 cl-board.py（`assets/blender/classroom/cl-board-r2t22.log`），`DONE cl-board`，零 Error/Traceback；GLB 回读 39 对象（与 R2-T17 相同），GLB 内实测 Blackboard x[-4.802,-4.762]、BoardFrameTop x[-4.797,-4.747]、ChalkTray x[-4.802,-4.722]；cl-board.glb 12,450,368 B（改前 12,450,364 B）、cl-board.blend 1,874,776 B。
- **场景重拼**：classroom.py 未改，重跑重拼（`assets/blender/scenes/classroom-r2t22.log`），`DONE classroom`，零 Error/Traceback；回读 440 对象（73+96+39+58+54+120，与 R2-T17 一致），门洞 clear（后排椅 y 列 ±0.8/1.8/2.8），board/desk 包围盒 x[-4.802,-3.690]；classroom.blend 5,465,640 B、classroom.glb 19,090,632 B。
- **推仓**：待填（推后补 commit 号与核对结果）。
- **验证**：待填（blender-previews classroom 组 + godot-verify run 号与目视结论）。
- **还剩什么**：① 展示板 WhiteBoard/WhiteBoardBack（板面 x=-4.80）仍埋在西墙内 35mm，Godot 里不可见，属 cl-board.py 内同类问题、需另立任务修（移出量 ≥35mm）；② 03-classroom 的 Godot 侧目视须等 R2-T19 的 S4 车顶 SOC 条修好、某次 godot-verify 全绿出图后再补（见验证）。

## §23 R2-T21a 楼房换装：tower/dorm/lib/bldA/bldB（2026-11-24/25，只改 5 件）

- **范围**：只换 `assets/blender/overview/` 下 ov-tower.py、ov-dorm.py、ov-lib.py、ov-bldA.py、ov-bldB.py 的楼体（各重建 .blend/.glb）；bldC（11-23 旧件）不动，gym/lab/canteen（R2-T21b）、跑道/道路/树草、Godot scripts/scenes/data 全不动；只重建件级 .glb，不拼总览场景（总览重拼由终轮整合做）。
- **来源**：R2-T10b 选定模型（SOURCES.md §12）：vinish 钟楼（CC BY 4.0，署名 vinish.dev）、Grab3D 办公楼/公寓楼/博物馆（CC0 1.0）。不做烘焙：模型自带真实 PBR 贴图（2048 atlas → 本件降采样至 1024 控体积，打包进 .blend；源 GLB 贴图无文件路径，不打包会在 Actions 检出后丢失）；新增小件（勒脚/屋顶板/女儿墙/设备）走 R2-T9 `_pbr_apply.py` hook（屋顶/混凝土/檐口三键，模型自带材质原名、不进 hook）。

### tower 创造力中心 14×14×32m 8F @ (10, 54)——vinish 钟楼

- **偏差（重要）**：R2-T10b 的“13.2×13.2×32.7m ×1.06/×1.06/×0.98”是文件包围盒（含广场 + 尖顶），不是塔身。实测可用砖塔身仅约 4.52×4.52×19.08m（x ±2.26，z 0.12–19.2；钟面 z 16.1–18.4，钟楼/尖顶 z 19.2–32.7）。按任务硬性规则“改模型不改尺寸”：删广场/钟面/钟楼/尖顶/风向标/门廊/花草后，塔身按实测保留包围盒缩放 **×3.097/×3.097/×1.677** 至 14×14×32（终包围盒 x[3.00,17.00] y[47.00,61.00] z[0.00,32.00]）；照搬 ×1.06 会得到 4.6m 宽、19m 高的针塔，违反 SPEC。钟面未挖洞（背后砖墙完整性未验证）：表盘面重赋墙色，成空白墙面圆盘，无指针/数字。石材收边几何比例拉长，读作角隅壁柱 + 层间带。
- **新增**：勒脚 0–0.5、层间檐口 + 缝线（F1 0.5–4.5、F2–F8 每层 3.9m 至 31.8）、屋顶板 31.8–32.0、女儿墙至 32.65、屋顶设备 + 通风管（顶 33.12）、南门 + 雨棚 + 台阶（F1 南面窗段外移 ±4.75 让位）、64 台空调外机（沿外墙分层挂）。
- **文件**：812 对象（回读 812/812），ov-tower.blend 6,622,648 B、ov-tower.glb 11,347,476 B；零 Error/Traceback，`DONE ov-tower`。
- **返工（品红缺陷，2026-11-24 晚）**：run #99 的 ov-tower.png 全塔品红——墙/屋顶/混凝土/檐口四种 hook 换入材质全品红。根因：ov-tower.py 首版 `save_and_export` 漏了贴图打包循环（其余 4 件首版即有），10 张 PBR 图只存相对路径 `//../../external/...`、未打包进 .blend；Actions 检出后路径找不到，渲成品红（缺失贴图色）。修法：补打包循环（与 dorm/bldA/bldB/lib 同款），重建后 10 张图全 packed（`packed: 10 unpacked: 0`）、.blend 6.6MB→14.2MB（.glb 未变，blob 同值）；`DONE ov-tower`，812/812 回读。教训：凡 hook 换入的图必须打包，仅靠相对路径不可靠。

### dorm 宿舍 A/B 各 20×12×16m 5F @ (84, -8)/(84, -44)——Grab3D 公寓楼

- **做法**：删屋顶露台 + 灌木；body + details 联合包围盒实测 15.56×13.82×16.57，缩放 **×1.285/×0.868/×0.947** 至 20×12×15.7（终包围盒 x[-10,10] y[-5.98,6.02] z[0,15.70]；**Z 用 body 高 16.57，不是任务单 ×0.87——那是按含已删露台的 18.30 联合高算的**）。保留模型自带桃砖 PBR（读作浅橙 #F6D9C0 系）；A/B 同款同色（真实宿舍 A/B 同型，旧件奶油/蓝灰分色废止）。西立面入口（朝校园内侧）+ 雨棚台阶；两栋共用一次导入、链接复制；两栋间草坪保留（x 74–94，y −38..−14，起伏网格 + 12 丛灌木，seed 7；灌木底 -0.05m 属埋土种植，不悬空）。
- **文件**：69 对象（回读 69/69），ov-dorm.blend 9,701,473 B、ov-dorm.glb 7,357,272 B；屋顶设备顶 17.12、女儿墙顶 16.40；零 Error/Traceback，`DONE ov-dorm`。

### lib 图书馆 24×16×22m 6F @ (24, -58)——Grab3D 办公楼 + 博物馆柱廊

- **楼体**：与 A/B 同款办公楼（body + facade + shell 三件合起来才是整栋楼，ground_slab 删除）；三件在 **z=21.75 横切**（bisect，保住 F1–F6，去掉 F7），联合包围盒整体缩放 **×0.740/×0.839/×0.968** 至 24×16×21.0（终包围盒 x[12,36] y[-66,-50] z[0,21]）。保留模型自带白框 + 蓝玻璃幕墙（即 SPEC 玻璃 #9FC3D8 系）；**SPEC §5 的浅橙墙面由幕墙玻璃色承接，旧件三道红褐饰带 + 竖向壁柱不再复刻**（会压在玻璃幕墙上冲突）。
- **柱廊**（只取博物馆正立面，不取整栋）：details 保留面心 y<−7 的面（3,652 面：台阶 + 基座 + 柱 + 门窗 + 横幅，x ±12.44，z 0–8.80）+ body 保留面心 y 在 (−9.5,−8.5) 且 z 在 (2,10) 的面（554 面：前基座 + 檐部 + 壁柱条）+ temple_emblem 整件（下移 2.3m，底边落檐部顶 ~8.77）；X 缩 0.65（柱廊宽 16.18m，居中 x[15.91,32.09]），Y/Z 不缩，墙面贴至 y=−66.2（微出南墙 0.2 防共面），台阶向南伸至 y≈−70.82（南侧开阔草坪，环南路在 y=−76，不冲突）；纹章顶 z 11.52。保留博物馆自带石材/白饰 PBR。
- **新增**：勒脚、屋顶板 21.0–21.3、女儿墙至 21.95、屋顶设备两盒 + 通风管（顶 22.87）。
- **文件**：29 对象（回读 29/29），ov-lib.blend 11,566,232 B、ov-lib.glb 7,761,784 B；零 Error/Traceback，`DONE ov-lib`。

### bldA 一号楼 40×15×19m 5F @ (-56, 30) / bldB 二号楼 32×14×19m 5F @ (-12, 30)——Grab3D 办公楼换骨架

- **做法（两栋同法）**：任务单的单件缩放（A：body ×1.36/×0.80/×0.74；B：facade ×0.99/×0.91/×0.78）是把三件各缩到目标盒，会压进同一个盒子造成共面 z-fighting，不采用。改用**整体 + 横切**：删 ground_slab，三件在 **z=18.1 横切**（bisect，保住 F1–F5 五层窗带，去掉 F6–F7），联合包围盒整体缩放至目标盒——bldA **×1.233/×0.786/×1.003** 至 40×15×18.1（终包围盒 x[−76,−36] y[22.5,37.5] z[0,18.1]），bldB **×0.986/×0.734/×1.003** 至 32×14×18.1（终包围盒 x[−28,4] y[23,37] z[0,18.1]）。窗带重排即横切（7 行 → 5 行）；Z 向基本不压，层高感保留：**F1 5.25m 高入口层**（模型入口层特征，SPEC 一楼 3.5m 未达成，已注明），其余 2.75–3.5m（约 SPEC 3.0m 净高 + 楼板）。
- **配色/入口**：保留模型自带白框 + 蓝玻璃幕墙（A 旧件米白 #F3E9D2、B 旧件蓝灰 #DFE9F2 墙色均由幕墙玻璃色承接，两栋以尺寸区分）；正门用模型自带**东立面雨棚入口**（东侧短边），不另加南门（旧件南门由模型入口取代）。
- **新增**：勒脚 + 压顶、屋顶板 18.1–18.35（封横切口）、女儿墙至 19.0；bldA 另有屋顶设备两盒（顶 20.02，沿用旧件 v2），bldB 无（旧件分工：B 栋屋顶设备归 ov-windows-roofs，本件不自带）。
- **文件**：bldA 24 对象（回读 24/24），.blend 9,749,635 B、.glb 7,062,004 B；bldB 14 对象（回读 14/14），.blend 9,649,963 B、.glb 7,020,996 B；零 Error/Traceback，`DONE ov-bldA` / `DONE ov-bldB`。

### 通用技术坑（两处实测教训，后续件注意）

- **GLB 导入对象的 object transform 非单位阵**：办公楼三件带 loc (−0.95, 1.5, 0.06)、博物馆三件带 loc (0, 1.3, 0)。`_vbox`（世界坐标）与 `data.transform`（局部坐标）口径不一致时中心会偏 t×(1−D)——bldA 首版中心偏 +0.22/+0.32 触发断言。修法：缩放前先把 object transform 烘进 mesh 并清零（`o.data.transform(o.matrix_world)` 后 `o.matrix_world = Identity`）。tower/dorm 的导入 transform 为单位阵，不受影响。
- **多源导入时清理循环必须限定新导入对象**：ov-lib 首版在博物馆导入后用全场景循环删“非预期对象”，误删了已建好的办公楼 facade/shell（ReferenceError）；次版用 `_new_objs` 快照又因已删对象仍在列表里再次 ReferenceError。定型做法：导入前快照场景集合，导入后先分出 mesh 列表再删非 mesh。

### 推仓

- **ba5f08b2**（tower + dorm：6 文件，父 71952d0d）与 **b9748d4d**（lib + bldA + bldB：9 文件，父 ba5f08b2），均经 API 核对 commit 真建出、父链连续；远端 ov-lib.glb 大小 7,761,784 B 与本地一致。单 blob 均 <40MB（最大 11.3MB）。
- **77c73269**（塔品红修复：ov-tower.py/.blend/.glb，父 a16a56c8；.glb blob 与首版同值，只改 .blend 打包）。
- 本记录 §23 随推 bb61bd8e（首版；本行补填在后续 docs 提交）。

### 验证

- **blender-previews run #99**（head b9748d4d，overview 作业 success；artifact `blender-previews-overview` 17.6MB，2026-11-24 17:51）：下载逐张目视——dorm ✓（两栋桃砖 + 白饰 + 薄荷阳台，5 层可读，深灰屋顶 + 设备盒，两栋间绿草坪）、lib ✓（6 层蓝玻璃幕墙 + 白框，深灰屋顶 + 两设备盒，柱廊台阶 + 蓝雨棚 + 木门 + 横幅 + 白柱 + 山花 + 纹章）、bldA ✓（5 层蓝玻璃幕墙 + 白横带，深灰屋顶 + 两设备盒，东雨棚入口）、bldB ✓（同款 5 层，较短，无屋顶设备）；**tower ✗ 全塔品红**（见上返工），其余 4 件通过。
- **blender-previews run #106**（head 77c73269，整 run completed success；overview 作业 success，artifact `blender-previews-overview` 18.0MB，2026-11-24 19:15）：下载复查——**tower ✓ 已修复**：米白灰泥墙（PBR 灰泥纹 + 石材收边读作角隅壁柱 + 层间带），8 层窗带、空白钟面圆盘（淡圆轮廓）、深灰屋顶 + 设备、64 台空调、南门深灰雨棚 + 台阶，比例 14×14×32 正确；dorm/bldA/bldB 三图与 #99 **逐像素一致**（mean abs diff 0.00），lib 复看一致（柱廊裁切放大确认：台阶、雨棚、木门、横幅、白柱、山花、纹章俱在；山花斜边近看略碎，鸟瞰距离可接受）。**5 栋楼全部目视通过。**
- godot-verify 总览验收由终轮整合做。
- **还剩什么**：① 终轮整合：总览重拼 + Godot 侧验收；② **ov-windows-roofs 的 A/B 窗带与屋顶膜是按旧实心楼体做的，与本件玻璃幕墙重叠**（窗带双层、屋顶膜与本件屋顶板 18.1–18.35 共面）——终轮须更新 ov-windows-roofs（A/B 窗带与屋顶膜改 C 栋专用或删除），本任务未动它；③ 塔 F1 南面窗段为让位正门外移 ±4.75、塔钟面为空白圆盘，目视已确认读感可接受。

## §24 R2-T9b PBR 材质硬性整改收尾（2026-11-25 00:18–01:00 CST，接替中断的 R2-T9；只改材质与贴图挂接）

- **任务**：用户 2026-11-24 22:42 硬性要求：建筑外立面、沥青路必须挂真实 PBR
  材质，不许留光板。上一任 R2-T9（agent 69c868fd）23:21 死于运行时重启，
  BLENDER_MODELS.md 全文无 "T9" 记录。本任务先核查半成品归属与逐件材质实态，
  再只修无人认领的光板件；未动楼体/道路尺寸与位置，未动 Godot scripts/scenes/data，
  未拼总览场景。开工 HEAD `7d5de9cf`（2026-11-24T16:20:55Z，R2-T21b 换装 .blend 入仓后）。

### 半成品归属核查结论（以文件时间戳 + 日志 + 代码注释三方对证，均为 CST）

- **`_pbr_apply.py` 原件属 T9**：文件头即写 "R2-T9 PBR hard fix (2026-11-24)"，
  含全套 `SETS`（14 种）与 `PBR_MAP`（12 件），12 个 `ov-*.py` 里同名 hook
  注释均写 R2-T9；`pbr-tinted/` 19 个染色贴图同日落盘。**00:11 的一次改动属
  R2-T21b**：`_load` 用 `BLEND_PATH` / 已打开 .blend 算相对路径的修法，
  本文件 §21 已记（修前 gym 首版 GLB 仅 440KB、只剩 1 张 243 字节空白图）。
  本任务只追加 1 个 TRACK 集 + 1 条 ov-track 映射（见下），其余一字未动。
- **沥青贴图组 00:03–00:10 的改动属 R2-T14b**：`ov-road-main.py` /
  `ov-road-walk.py` 内 "R2-T14b" 补丁注释（`_load` 相对路径 bug 的存盘前
  改写）+ `/tmp/r2t14b-main.log`（00:12，`DONE ov-road-main`，Asphalt 三图
  全套回读通过）+ `/tmp/r2t14b-walk.log`（23:56 首跑）/
  `r2t14b-walk-repair.log` + `/tmp/r2t14b-fix-walk.py`（修后 171 对象、
  每种材质 ≥3 图）+ `/tmp/r2t14b-walk2.log`（00:18–00:29 重跑，
  `DONE ov-road-walk`）。T14b 未在本文档留节，本段即补记。
- **T9 中断前已跑完 bldA/bldB/bldC/lib/tower**：五件 .blend/.glb 时间戳
  23:11–23:19 CST，GLB 实测 PBR 贴图全套（见下）。**ov-dorm.blend 在 23:20
  有一次改动但 .glb 未更新**，疑似 T9 正在跑 dorm 脚本时中断，无日志留存，
  内容无法确认；随后 T21a 00:26 完整重建覆盖，本任务不追认。
  **ov-road-main/walk 的 .py 在 00:05 被 T14b 改过**（补丁注释为证），
  与 T9 无关。**ov-gym/lab/canteen 的 00:13–00:15 改动属 T21b**（§21）。

### 核查方法（不猜，全实测）

- GLB 直读：`/tmp/audit_glb.py` 解析各件 `.glb` JSON——每种材质
  baseColor / metallicRoughness / normal 三槽贴图名 + 内嵌字节数，
  <2KB 判空白坏图；同时计无材质 primitive 数。
- .blend 直读：`/tmp/audit_blend3.py`（Blender 4.2.0 `--background` 只读
  打开，不保存）——每种材质 Principled 三路链接、粗糙度默认值、
  Normal Map 强度、**逐面** UV tile（世界跨度/UV 跨度中位数；按对象
  取并集会把不同朝向面的 UV 轴混在一起，初版误报 0.08m，已修正）。
- 贴图平坦度：PIL 实测烘焙图均值/std；渲染图 ROI 统计 + 高频残差。

### 光板清单（改前，2026-11-25 00:20 CST 实测）

| 件 | 面 | 缺什么（实测） |
|---|---|---|
| ov-windows-roofs | 屋顶膜 ovw_roof_membrane（3 栋屋顶，39/31/21m） | 烘焙三图仍在但近乎平色：color 均值 (67,74,81)、std 8–10，UV 单张 1024 铺 39m |
| ov-windows-roofs | 女儿墙压顶 ovw_coping / ovw_coping.001（39/31/21m） | 烘焙 color 均值 (7,7,8)——近乎纯黑（旧烘焙 bug），std 16，UV 单张铺 39m |
| ov-track（任务书“跑道同理”，12 件清单外追加，见下） | 跑道红 Track_Red_B8543F（400m 环） | 烘焙 color 仅 28,634 B，UV 单张铺整环；分道线/路缘为细线，不算光板 |
| ov-dorm | 全件（米白/蓝灰墙、屋顶、檐口） | 旧烘焙图（11-23 版，.glb 2026-11-23 03:14），但**属 T21a 换装范围，本任务只核查不修** |
| ov-road-main / ov-road-walk | — | 改前已由 T14b 修完（见归属段），本任务只复核 |

### 逐件核查结果（其余 10 件改前即已达标，不动）

- **ov-bldA / ov-bldB / ov-bldC / ov-lib / ov-tower（T9，23:11–23:19 跑完）**：
  GLB 内墙/檐口/混凝土/屋顶四种大面材质均为 PBR 三图全套实尺寸
  （如 plaster_F3E9D2_color 347,347 B、plaster_normal_amp2 2,723,411 B、
  concrete_B9B3A8_color 480,874 B、roof_424A52_color 359,855 B），
  0 张 <2KB 坏图，0 无材质 primitive；.blend 逐面 tile 中位数**墙 2.00m /
  混凝土 2.00m / 屋顶 3.00m**（p10=p90，分毫不差，与 `SETS` 一致），
  法线强度墙/混凝土 1.0、屋顶 0.7，粗糙度默认值 1.0（以 rough 贴图为准）。
  玻璃（Door_Glass / Lib_Glass / Glass_Window）无贴图——素色玻璃按设计，
  不算光板。小件（AC 机身/格栅、门、金属灰、窗框）保留烘焙三图。
  bldC 本地 640×360 预览已出（`screenshots/blender/ov-bldC.png`）：
  屋顶灰瓦纹理成片可见、浅橙墙面有灰泥起伏。
- **ov-gym / ov-lab / ov-canteen（T21b，§21）**：GLB 实测墙/屋顶/混凝土/
  砖红 4–5 种 PBR 材质各三图全套（gym 9 图、lab 13 图、canteen 19 图），
  与 §21 记录一致；玻璃/金属/框料素色保留，不动。
- **ov-road-main（T14b，00:12）**：Asphalt_424A52 三图全套
  （asphalt_424A52_color 518,470 B、asphalt_rough_090 591,733 B、
  asphalt_normal_amp2 2,621,275 B），路缘混凝土三图全套，黄线烘焙三图；
  asphalt_rough_090.jpg 实测均值 229.5 → **粗糙度 0.90**、std 0.5（按
  0.9 档设计），法线强度 1.0。
- **ov-road-walk（T14b，walk2 00:29 重跑完）**：8 种材质全部三图全套
  （铺装/步道/压边石/盲道用 concrete_pavement_03 染色 + paving_normal_amp2，
  PavingNew 直接用 concrete_pavement_03 三图，JointLine 烘焙三图），
  0 坏图；回读 171 对象。
- **ov-windows-roofs 其余材质**：ovw_frame 烘焙 color 均值 (65,67,69)、
  std ~70（有明暗变化，非平色，窗框细条，保留）；ovw_equip / ovw_fan
  小设备盒 std 21–27，保留；ovw_glass 素色玻璃按设计；ovw_preview_*
  4 种为预览辅助质量，不进 GLB（GLB 7 材质无它们）。
- **ov-track 追加说明**：12 件清单无跑道，但任务书 §2 明写“跑道/铺装
  同理”，且跑道红是校园内最大一片单色面（400m 环），留烘焙 flat 图
  即违背“不许再留光板”，故纳入本次修复；ov-field（球场草皮，烘焙
  color 228–244KB，非平色）不在任务书点名范围，本次未动，留作残留。

### 修复（只改材质挂接；楼体/道路尺寸位置一字未动）

- **ov-windows-roofs（直接对 .blend 应用 `_pbr_apply`，不重跑建模+烘焙）**：
  ovw_roof_membrane → CONCRETE_424A52（concrete_424A52_color +
  concrete_wall_007_rough + concrete_normal_amp15，tile 2.0m，法线 1.0），
  ovw_coping / ovw_coping.001 → CONCRETE_B9B3A8（同源，tile 2.0m）。
  90 面重投 UV，9 张旧烘焙图 purge；路径断言全过
  （`//../../external/` + 1024×1024 有像素）。`.blend` 1,975,928 B、
  `.glb` 4,156,720 B（原 3,318,672 B），回读 127 对象（与原脚本
  piece_objs 127 一致），除玻璃外每种材质 ≥3 图。
  `.py` 未改（hook 早已在内，重跑可复现）。
- **ov-track（同上 + 两处新增）**：`_pbr_apply.py` 新增 `TRACK_B8543F` 集
  （`pbr-tinted/track_B8543F_color.jpg` + asphalt_rough_090 +
  asphalt_normal_amp2，tile 4.0m，法线 1.0）与 `PBR_MAP["ov-track"]`；
  染色用 `tint_textures.py` 同款线性空间逐通道缩放（asphalt_01 diff →
  SPEC 跑道红 `#B8543F`，R 缩放钳制 4.0，实测均值 (170,84,63)，ΔR 14，
  在 SPEC 常用 ±15 容差内）；`ov-track.py` 在烘焙与存盘之间插入
  `_pbr_hook` + R2-T14b 路径改写块（与 road 两件同款，幂等）。
  Track_Red_B8543F 512 面重投 UV（tile 4.0m），3 张旧烘焙图 purge。
  `.blend` 1,477,780 B、`.glb` 4,540,664 B（原 1,142,348 B），回读 17 对象，
  track_ring 三图为 track_B8543F_color / asphalt_rough_090 / asphalt_normal_amp2。
- **来源**：全部沿用已下载 CC0 包，无新下载——Poly Haven asphalt_01
  （https://polyhaven.com/a/asphalt_01）与 concrete_wall_007
  （https://polyhaven.com/a/concrete_wall_007），见 SOURCES.md §1.1/§9.2
  （本任务在 §9.2 补 `track_B8543F_color.jpg` 一行）。

### 本地验证（Actions 为准之前，先本地看过图）

- `ov-windows-roofs.png`（640×360，Eevee 16 采样）：屋顶膜整片深灰颗粒
  可见（ROI std R 13.1 / G 11.7 / B 10.5），压顶浅色边条清晰，不再光板。
- `ov-track.png`（同规格）+ 临时近摄 `/tmp/track_closeup.png`（未保存进
  工程）：远景红环 + 白分道线完整；近摄红面细颗粒 mottling 清晰，
  高频残差 std G 6.0 / B 7.2（R 通道近饱和，std 1.5，属沥青原图低对比，
  非挂接失败）；渲染均值 R 184.3 与目标 `#B8543F` 的 R=184 一致。
- `ov-bldC.png`（同规格，T9 成果复核）：屋顶灰瓦纹理成片、墙面灰泥可见。
- 三图均非黑非白。注：本地渲染未走 xvfb（沿用已有 Blender 直跑，
  日志有 1 条 EGL_BAD_MATCH 警告，PNG 均正常写出，319,858 / 258,865 /
  273,934 B）；验收仍以 Actions 为准。

### 推仓

- commit `f39cd380`（`f39cd380ed410edc8eee538006646f16a2f2aea8`，父 `0ed69b0a`，
  2026-11-24T16:51:18Z = 2026-11-25 00:51 CST）：12 文件一次 push-files——
  `_pbr_apply.py`、`ov-track.py`、ov-windows-roofs / ov-track 的 `.blend` +
  `.glb`、新染色 `pbr-tinted/track_B8543F_color.jpg`、3 张本地预览 PNG
  （ov-windows-roofs / ov-track / ov-bldC）、本文档 + SOURCES.md。
  推后核对：commit 真建出，父链连续；contents 逐项核对大小/SHA 与本地一致
  （ov-track.glb 4,540,664 B `fd5c6e6e`、ov-windows-roofs.glb 4,156,720 B
  `c4afaf5a`、两 .blend、`track_B8543F_color.jpg` 315,282 B `bb3cce97`、
  BLENDER_MODELS.md 247,651 B、SOURCES.md 119,744 B）。单 blob 均 <40MB
  （最大 4.5MB）。本段推仓记录随后续 docs 提交补填。

### 验证

- **blender-previews #102 / 45441951337（HEAD `f39cd380`）：success（约 2026-11-25 02:2x CST 完成），但目视发现品红——不是本任务两件的挂接错，是仓库缺贴图文件（见下）**。artifact `blender-previews-overview`（17,667,643 B）已下载，20 张 PNG 逐张目视：
  - **ov-track.png 通过**：红环 + 白色分道线清晰，环面有细颗粒（track_B8543F_color.jpg 是本次 push 里唯一随 .blend 一起进仓的色图，rough/normal 当时缺也不致品红，只损微观起伏）。
  - **ov-windows-roofs.png 不通过（品红）**：三块屋顶膜呈亮品红（取样 (196,124,205)/(197,125,206)），压顶边带同色；窗带玻璃/框架正常（烘焙贴图在仓内）。本地同 .blend 渲染深灰颗粒膜正常——差异在仓库，不在挂接。
  - **ov-road-main.png 不通过（品红）**：整条沥青环路 + 主路亮品红（取样 (197,120,206)/(198,123,207)），地面绿地正常。
  - **ov-road-walk.png 不通过（品红）**：步道/路缘呈淡品红细线（铺装色图缺失），背景偏暗。
  - **ov-gym.png 不通过（品红）**：整栋墙/顶/雨棚/地面全品红，只剩窗玻璃与屋顶设备盒正常。
  - **ov-bldC.png 不通过（不是品红，是旧件）**：墙面平米白、屋顶平深灰，无 PBR 纹理——仓库里的 bldC .blend/.glb 仍是 2026-11-23 版（见“补推 bldC”）。
  - **根因（两件，已实锤）**：① T9 在本地生成了 `pbr-tinted/` 20 张 + polyhaven 5 张却没推仓，#102 检出时 `assets/external/` 里没有这些文件，Eevee 缺图渲成品红；T21b 已于 2026-11-24T17:24:26Z 在 `4228878e` 补推 24 文件（19 张 pbr-tinted + 5 张 polyhaven），其 message 自述“此前只在本地，Actions 渲染缺图致墙面品红”；② 本地 .blend 逐项 fresh-open 核查：road-main/walk、gym、bldC 全部存相对路径 `//../../external/...`（无绝对路径、无 packed 缺失），路径本身正确——排除“路径写错”假说。另 T21a 在 `77c73269`（17:58Z）把 tower 的 10 张 PBR 图打包进 .blend，称“首版只存相对路径，Actions 检出后找不到渲成品红（run #99）”，其余 4 件“首版已打包不受影响”——#99 时贴图文件同样不在仓内，缺文件即可解释品红，打包是等效的兜底修法。
- **godot-verify #125 / 45441951343（HEAD `f39cd380`）：success**。artifact `godot-screenshots`（12,348,571 B）已下载，20 张 PNG；**00-overview 目视**：楼体窗带/墙面/屋顶、沥青路、跑道红环均有材质可见（非光板），裁放确认：跑道红环有分道线与颗粒、创造力中心楼面有灰泥斑驳与屋顶灰瓦纹理、主路沥青有深浅变化。**但 00-overview 的总览场景用的是 `assets/models/scenes/overview.glb`（T1b 2026-11-24T16:05Z 重拼版），早于本次 push（16:51Z），本次 windows-roofs 膜/压顶与 track 红环尚未进入总览场景**——Godot 侧只能确认总览整体有材质，本次两件进总览须终轮整合重拼后复验。
- **补推 bldC（T9 遗留，2026-11-25 02:3x CST）**：本地 T9 版 ov-bldC .blend（1,962,120 B，2026-11-24 23:14 CST）/.glb（10,926,252 B，23:15 CST）/.py（23:11 CST 钩子版）从未推仓——仓库版仍是 2026-11-23T15:16:12Z `c9390d62` 的 1,992,496 B .blend / 3,731,892 B .glb（.py 更是 11-22 版，无 PBR 钩子）。本地 fresh-open 核查：26 张图全相对路径、尺寸 1024；GLB 审计：墙/檐口/混凝土/屋顶全 PBR 三件套、贴图真实尺寸、UV 平铺中位墙 2.00m/混凝土 2.00m/屋顶 3.00m——推仓条件具备。本次一并推 `ov-bldC.py` + `.blend` + `.glb`（.py 只加打包段，见下；.blend/.glb 是 T9 原文件，未重建）。
- **打包兜底（2026-11-25 02:3x CST，与 T21a tower 修法同款）**：8 个 PBR 件的 .blend 逐个打开、把全部在用贴图打包进文件（`im.pack()`，几何/材质/节点一字未动），共 106 张：windows-roofs 13、track 9、bldC 25、road-main 9、road-walk 15、gym 9、lab 13（+3 已打包）、canteen 13（+9 已打包）。打包后尺寸：bldC 11,008,332 B、canteen 15,938,654 B、lab 12,752,436 B、road-walk 11,846,320 B、road-main 7,287,152 B、gym 6,687,636 B、windows-roofs 5,046,268 B、track 4,800,132 B——均 <40MB。fresh-open 复核 windows-roofs 的 concrete_424A52/B9B3A8 均为 packed=True、1024×1024。独立验证：把打包后的 ov-track.blend 单独拷到 /tmp/packtest（无 external 目录，相对路径解析不到任何文件），用 .blend 自带相机渲染，红环颗粒清晰、无品红——证明打包自带贴图、脱离仓库文件也能渲（`/tmp/packtest/track_0001.png`，2,057,034 B）。另 `ov-windows-roofs.py` / `ov-track.py` / `ov-bldC.py` 各加 8 行打包段（T21a bldA/tower 同款，保存前 `im.pack()`），使以后重跑也保持打包；road-main/walk、gym/lab/canteen 的 .py 未动（T14b/T21b 的文件，.blend 已打包；若其主人重跑脚本，未打包的 .blend 会再产生，见“还剩什么”⑤）。
- **本次推仓**：已推 `7eec73f8`（8 个打包 .blend + bldC .glb + 3 个 .py + 本文档），已核对建出；触发 blender-previews run **#107**（45464884225，02:56 CST 触发），截至 03:53 仍 in_progress（5/6 组 success：classroom/dist/charge/pv/storage；仅 overview 组仍在渲染——以该组复验品红是否消失 + bldC PBR 是否可见）。
- **#107 复验结论（2026-11-25 04:4x CST，R2-T9b 收尾）**：run **#107 / 45464884225 全部 success**（6/6 组，overview 组约 04:44 CST 完成）。artifact `blender-previews-overview`（18,064,602 B）已下载，20 张 PNG 全量品红扫描（R>150、G<140、B>150）**全部 0.0000%**——品红彻底消失。逐张目视（8 件 PBR 件全看）：**ov-windows-roofs 通过**——三块屋顶膜深灰颗粒、压顶浅色边带清晰，窗带蓝玻璃正常；**ov-track 通过**——红环 + 白分道线，环面颗粒可见；**ov-bldC 通过**——新 PBR 件终于进仓：屋顶灰瓦纹理成片、墙面浅橙灰泥有斑驳、檐口/混凝土分层清晰，与 #102 的平米白/平深灰判若两件；**ov-road-main 通过**——沥青深灰蓝颗粒、黄中线/白边线/路缘齐全；**ov-road-walk 通过**——步道浅色混凝土铺装纹理、路缘与盲道可见（背景深灰为本件自带 world，非缺陷）；**ov-gym 通过**——红砖墙竖纹、灰瓦屋顶、玻璃窗带、混凝土雨棚齐全；**ov-lab 通过**——米白灰泥墙 + 红砖柱、灰瓦屋顶；**ov-canteen 通过**——红砖/灰泥墙、灰瓦屋顶、入口立柱。godot-verify **#128 / 45464883948（HEAD `7eec73f8`）success**：artifact `godot-screenshots`（12,389,181 B）已下载，20 张；**00-overview 目视无回归**——楼体窗带/墙面/屋顶、沥青路、跑道红环、树木标签均正常渲染。但同 #125：总览场景仍用 T1b 16:05Z 重拼的 `overview.glb`，本次 windows-roofs/track/bldC 尚未进入总览，须终轮整合重拼后复验（见“还剩什么”④）。
- **还剩什么**：① ov-field 草皮仍用烘焙图（未在任务书点名，本次未动）；② T21a §23 ②：ov-windows-roofs 的 A/B 窗带与屋顶膜与新换装 bldA/bldB 玻璃幕墙重叠（窗带双层、屋顶膜与屋顶板共面），终轮整合须更新本件（改 C 栋专用或删除），本次只换了膜/压顶的贴图、几何一字未动，不加重也不解决该重叠；③ T21a 换装 5 栋的细部素色材质（tower/dorm/lib/bldA/bldB 的 MetalGrey/AC/窗框/门等源模型自带平色）不在本任务范围，其 §23 验证仍待填；④ 总览重拼与 Godot 侧验收由终轮整合做（本次两件进 00-overview 须重拼后复验）；⑤ road-main/walk、gym/lab/canteen 的 .py 未加打包段（T14b/T21b 的文件未动），若其主人重跑脚本会产出未打包 .blend，建议其主人照 T21a 款式补 8 行，或下次推仓前由整合复核 packed 状态；⑥ #103（HEAD `6eb9850d`，17:20Z）检出时贴图文件仍未进仓（`4228878e` 17:24Z 才到），其 overview 组如出品红属预期，不另修，以本次推仓触发的新 run 为准；⑦ **注意**：本次 §24 验证段曾被并行任务的 docs 推送覆盖回“待填”（2026-11-25 02:5x CST 发现，文件从 1,335 行变 1,369 行、§24 验证段回退），已按当前文件重写本段；推仓前须重读 HEAD，推后核对远端 §24 内容。

## §25 R2-T23：03-classroom Godot 侧目视补验（2026-11-25 00:57–01:30 CST，只验证与记录，不改模型、不推模型）

- **来源**：godot-verify run **#119 / 45437816576**（HEAD `0b6b8ae8`，R2-T19 S4 修复后首个全绿 run），VERIFY-SUMMARY **PASS=271 FAIL=0**。artifact `godot-screenshots`（zip **12,362,828 B**）已用 custom.github `download-artifact` 重新下载核对：解压 **20 张** PNG（`00`–`19`，合计 **12,360,376 B**），md5 与本地副本 `assets/blender/charge/r2t19/godot-screenshots-119/` 逐项一致。**注意张数**：任务书称 19 张，实为 20 张（多 `19-overview-overcast.png`）；本地副本先前即为这 20 张，目录名无误、张数以实测为准。教室相关仅 `03-classroom.png` 一张——任务书所称“13-classroom 近景”不存在，13 号是 `13-fallback-storage.png`。以下逐项均为亲眼看图结论（03 全图 + 2 倍放大 + 单桌 4 倍放大），非仅凭 Actions 绿。
- **① 48 套桌椅真腿落地、无悬浮平板——不通过（目视）**：03 图内约 20 余张桌面入镜（48 套总数无法单图数清，房间只拍到局部）；可见的每张桌面均为木纹平板、**桌腿一根未见**，桌面贴地呈悬浮薄板状（单桌 4 倍放大：桌面近沿下只有一条细暗边、直通地面，无任何支撑）。同角度椅背两根立柱清晰落地，说明不是分辨率或角度遮挡。Blender 侧 T17 run #91 曾见钢圆管腿落地，Godot 侧未见——可能原因：Godot 场景 classroom.glb 未含腿几何、或腿渲染过细过暗，需 T17 或终轮查 Godot 侧 cl-desks 节点；本任务只记录，不改模型、不判 Blender 件有错。
- **② 黑板墨绿可见——待 R2-T22 修复后复验（不判 T17 不合格）**：板面与墙同色（板面区取样 (56,70,69) vs 墙 (72,70,58)），只剩左右两条框线 + 底部粉笔槽横杆可见，无墨绿板面。与 §22 所述一致：#119 的 HEAD `0b6b8ae8` 仍在 R2-T22 黑板埋墙修复之前（黑板盒埋进西墙 15mm）。复验待 R2-T22 新 run 出图。
- **③ 墙面米白/暖色、无青绿——部分通过**：无青绿 ✓（墙取样 (72,70,57)/(72,70,58)，R≈G、B 更低，无绿偏；与 T17 目标暖褐 (97,88,68) 同色系，补偿方向正确）；但墙面是**深橄榄褐、不是米白/浅暖色**，比 T17 目标暗约 25%。按任务书字面判部分通过，深暖褐是否接受由终轮定。
- **④ 门洞 clear——无法确认**：左侧整面蓝绿玻璃窗/门无家具遮挡、通道无堵，AC 柜机立于窗旁不挡路；但图中未见明确门洞轮廓/门框开启，门洞本身无法独立确认。§18/§22 的“门洞 clear”是 Blender 回读结论，Godot 图内无法背书，需一张带门洞的近景或以回读为准。
- **⑤ 桌下钢丝书篮、椅横撑可见——不通过（目视未见）**：放大后桌下空无一物、无钢丝篮；椅仅见两根立柱、无横撑脚踏杆。同 ①，Blender 侧曾见、Godot 侧未见，原因待查（见 ①）。
- **其余 19 张扫视——无明显回归**：04-charge 三车 SOC 条各贴各自车顶（蓝/红绿条、白 SUV 条更高，独立复核 T19 修复成立）；11-charge-rain / 12-charge-sunny 同视角条变橙——对应 SOC 58/51/77%，色随电量变、属显示逻辑非回归；14-fallback-charge 块状 fallback 车三车顶条也在位。00/18/19 总览（晴/多云/阴）、01/06 光伏（雨天出力 775→231 kW 一致）、02/10/13 储能、05/17 配电、07 暴雨、08 窄屏、09 教学楼外观、15 fallback 总览、16 A/B/C 对照均正常渲染，面板数字与曲线一致，未见穿模/黑图/缺件。
- **推仓**：commit `faed898d`（`faed898dbd36bb76fa02b2830abcee2425c84ad5`，父 `783aa8ab`，2026-11-25 01:30 CST 前后）：只推本文档 1 文件（BLENDER_MODELS.md，255,419 B，blob `3e156ee9`）；推后核对：commit 真建出、父链连续、远端文件与本地逐字节一致、含 §25。
- **还剩什么**：① ①⑤ 两项目视不通过，需 T17 或终轮查 Godot 侧桌椅几何（cl-desks 节点是否含腿/篮/横撑、是否进 classroom.glb）；② ② 待 R2-T22 修复后新 run 复验；③ ③ 深暖褐墙色是否接受待终轮定；④ ④ 门洞需近景图或以 Blender 回读背书；⑤ 48 套总数单图数不清，以 Blender 回读 96 对象为准。

## §26 R2-T25 教室展示板埋墙修复（2026-11-25，只改 cl-board.py + 教室场景重拼）

- **问题**：`assets/blender/classroom/cl-board.py` 的展示板 WhiteBoard/WhiteBoardBack 板面 x=-4.80，埋进西墙内面 (-4.765) 35mm，Godot 里不可见（§22 R2-T22 修黑板时留下的同类问题，见 §22“还剩什么”①；与黑板的 18mm 不是同一修法）。
- **修法**：只改 cl-board.py，展示板组整体沿 +x 平移 0.038m（黑板组、墙、尺寸一字未动）：WhiteBoard 中心 -4.815→-4.777（盒 x[-4.792,-4.762]，板面露出墙面 3mm，与黑板同量）；WhiteBoardBack 中心 -4.83→-4.792（盒 x[-4.802,-4.782]，背板框边仍在墙内，与黑板背面同例）；左右两块同量平移，相对位置与尺寸全未动。
- **重建**：重跑 cl-board.py（`assets/blender/classroom/cl-board-r2t25.log`），`DONE cl-board`，零 Error/Traceback；GLB 回读 39 对象（与 R2-T22 相同）；独立回读 GLB 实测 WhiteBoardLeft/Right x[-4.792,-4.762]、WhiteBoardLeftBack/RightBack x[-4.802,-4.782]，Blackboard x[-4.802,-4.762]、BoardFrameTop x[-4.797,-4.747]、ChalkTray x[-4.802,-4.722] 均与 R2-T22 一致未动；cl-board.glb 12,450,368 B、cl-board.blend 1,874,776 B（与 R2-T22 同体积，只改位置）。
- **场景重拼**：classroom.py 未改，重跑重拼（`assets/blender/scenes/classroom-r2t25.log`），`DONE classroom`，零 Error/Traceback；回读 440 对象（73+96+39+58+54+120，与 R2-T22 一致），门洞 clear（后排椅 y 列 ±0.8/1.8/2.8），board/desk 包围盒 x[-4.802,-3.690]；classroom.blend 5,465,640 B、classroom.glb 19,090,636 B（R2-T22 版 19,090,632 B，+4 B 只因位置数变）。
- **推仓**：commit `6eb9850d`（`6eb9850d071b1a0479382fd3bb944f3b8c30dacb`，父 `84e0df65`，2026-11-25 01:20 CST 前后）：8 文件（cl-board.py/.blend/.glb、cl-board-r2t25.log、classroom.blend/.glb、classroom-r2t25.log、BLENDER_MODELS.md §26）；推后核对：commit 真建出、父链连续、远端 8 文件 SHA 与本地逐项一致（cl-board.py `b0ba36cf`、cl-board.glb `68e00918`、classroom.glb `72424ca2`、BLENDER_MODELS.md `c8f92f3c`）。单 blob 均 <40MB（最大 classroom.glb 19,090,636 B）。
- **验证**：blender-previews run **#103 / 45447416449**（HEAD `6eb9850d`）：classroom 组 **success**（job 138634893269，17:35–17:55 UTC），artifact `blender-previews-classroom`（4,941,055 B）已下载核对——内含本次 run 新渲染的 6 张 cl-*.png（另 3 张 ov-* 为检出时带入的仓库旧图，非本次渲染）；**cl-board.png 逐张目视通过**：左右两块白板均清晰可见（取样左 (167,173,176)、右 (163,170,174)，浅灰磨砂面）、黑板墨绿 (36,47,45)、讲台/粉笔盒正常。godot-verify run **#126 / 45447416434 success**（约 17:39 UTC 完成）：artifact `godot-screenshots`（zip 12,391,627 B）已下载，20 张 PNG；**03-classroom 逐张目视通过**：两块白板在 Godot 里可见（取样左 (64,102,100)、右 (63,99,97)）、黑板墨绿 (33,44,35)、墙面暖褐 (101,82,66)，三者区分明显；其余 19 张扫视无回归（总览/光伏/储能/充电/配电/fallback/窄屏均正常渲染，充电车顶 SOC 条在位）。注：blender #103 整体结论待 dist/overview 两组完成（与本次改动无关，本任务只认 classroom 组 success + 目视）。
- **还剩什么**：① §25 ①⑤ 桌椅腿/篮/横撑 Godot 侧未见、③ 深暖褐墙色、④ 门洞 Godot 图内无法独立确认，均不在本次范围，仍待 T17/终轮；② 本次只露出白板面，背板框边仍在墙内（与黑板背面同例），属有意保留，不另修。

## §27 R2-T27 教室墙面偏暗调色（2026-11-25，只改墙面材质参数，不改结构）

- **问题**：R2-T23 目视：墙面无青绿 ✓，但呈深橄榄褐、比 T17 目标暖褐 (97,88,68) 暗约 25%，判“部分通过”。R2-T24 诊断确认取样真实：后墙 (72,70,57)，右墙受光面三文鱼色 (200,132,100)，天花板同因偏绿 (71,69,57)。
- **成因（只读分析，线性光模型反推，Web 实拍复核一致）**：墙贴图 `white_stucco__F3E9D2.jpg` 均值 sRGB (243,232,210)，线性 (0.896, 0.807, 0.644)；T17 因子 (1.0, 0.39, 0.32) → 反照率线性 (0.896, 0.315, 0.206)。后墙（西墙）几乎只靠天光，辐照度约 (0.072, 0.195, 0.198)（绿天光主导）；右墙（北墙）受直射，辐照度约 (0.644, 0.733, 0.618)（日光主导，近中性）。后墙要到 (97,88,68) 需反照率 (1.65, 0.50, 0.29)，即因子 (1.85, 0.62, 0.45)；同因子放右墙会算出 (263,163,117)，R 溢出吹成粉红——故必须分墙，不能一刀切改全局 tint。
- **修法（只改材质参数，几何/灯光一字未动）**：① 西墙另立材质 `cl-floor-walls_wall_back`（同贴图、同缩放、同尺寸，仅 `cl-floor-walls_wall_west` 一个盒子换材质），因子 **(1.85, 0.62, 0.45)**，预测后墙 (97,88,68)；② 南北/东墙沿用 T17 因子 (1.0, 0.39, 0.32) 不动，右墙维持 (200,132,100)，不冲粉；③ 天花板顺带去绿，因子 (1.0, 0.85, 0.78)，预测 (71,64,50)，只去绿不提亮（提亮需因子 ~4，不可行）。
- **关键坑——Blender 4.2 导出器硬 clamp**：`__gather_base_color_factor()` 里 `rgb = [max(min(c, 1.0), 0.0) for c in rgb]`，>1 的因子导不出，GLB 里会变 1.0（实测：.blend 存 1.85，首版 GLB 只有 1.0）。`cl-floor-walls.py` 与 `classroom.py` 各加 `_patch_glb_factors()`：导出后直接改 GLB 的 JSON chunk，把 `cl-floor-walls_wall_back` 的 baseColorFactor 写回 (1.85, 0.62, 0.45, 1.0)，只动 JSON chunk、不动 BIN chunk；两处补丁须保持同步（classroom.py 从 .blend 重导出，同样触发 clamp）。Godot 4.4 实测认 >1 因子（见本地探针）。
- **重建**：重跑 cl-floor-walls.py（`assets/blender/classroom/cl-floor-walls-r2t27.log`），`DONE cl-floor-walls`，零 Error/Traceback；GLB 回读 73 对象；`cl-floor-walls.glb` 7,491,808 B，JSON 实测 wall_back [1.85, 0.62, 0.45, 1.0]、wall [1, 0.39, 0.32]、ceiling [1, 0.85, 0.78]。重跑 classroom.py（`assets/blender/scenes/classroom-r2t27.log`，只加补丁函数、其余未改），`DONE classroom`，零 Error/Traceback；APPEND 73+96+39+58+54+120，TOTAL/回读 **440** 对象（与 R2-T22/R2-T25 一致）；classroom.glb 19,091,228 B、classroom.blend 5,527,432 B；门洞 clear、board/desk 包围盒 x[-4.802,-3.690] 与 T25 一致。
- **本地 Web 探针（复用 R2-T24 最小探针工程，Godot 4.4 Web 导出 + headless Chrome，0 console errors）**：后墙 (72,70,57)→**(96,86,67)**，与目标 (97,88,68) 差 ≤2；右墙 (200,132,100)→**(199,131,100)**，未动；天花板顶带 (41,63,29)→(41,58,25)，略去绿；黑板 (28,41,34) 仍墨绿；桌椅/空调/窗户无回归。截图 `~/workspace/review-rework-r2/r2t27-web-new-classroom.png`。
- **推仓**：commit `a16a56c8`（`a16a56c8122a9c18be536e5f377a0ad3e50b3b6a`，父 `e0eaadf1`，2026-11-25 01:57 CST 前后）：9 文件，blob SHA 已逐项核对与本地一致（cl-floor-walls.py `ba5807cb`、cl-floor-walls.blend `38aee4fa`、cl-floor-walls.glb `847566a2`、cl-floor-walls-r2t27.log `fc3458d2`、classroom.py `a63b44cf`、classroom.blend `2cf5d932`、classroom.glb `15ae8571`、classroom-r2t27.log `b26e9720`、BLENDER_MODELS.md `c243c502`）；推后核对 HEAD 即 a16a56c8（之后又有 T21a/T18/T25/T21b/T9b 等多笔，当前 HEAD `7eec73f8`，本提交仍在历史中）。
- **验证**：**blender-previews #105**（run 45454180216，head a16a56c8）classroom 组 job completed success，6 张逐张目视通过——cl-floor-walls：墙在中性光下呈暖粉补偿色（属预期，Godot 为准）、几何完好（4 窗洞/侧、门洞、地面、天花板齐全）；cl-board（黑板墨绿、白板面白、讲台齐全）、cl-desks（48 套、腿落地）、cl-ac、cl-lights、cl-windows 均无回归（注：整 run 仍 in_progress，只剩 overview job 在跑，与本次无关）。**godot-verify #127**（run 45454180234，head a16a56c8）：completed success，**PASS=271 FAIL=0**；20 张截图已下载，03-classroom 目视通过：后墙 **(95,86,67)**（目标 (97,88,68)，差 ≤2），黑板 (29,41,34) 墨绿，桌椅/讲台/空调/窗户无回归；右墙在 CI 03 图内被信息面板遮挡，以本地 Web 探针复核 (199,131,100)，与改前 (200,132,100) 一致、未冲粉。
- **还剩什么**：① 白板面仍显暗灰绿（(62,86,81)，白板材质本身在绿天光下偏色，与墙同因、但属 cl-board 材质，不在本任务“只调墙面”范围，留终轮）；② 南墙遮光面/北墙遮光面仍偏暗橄榄（侧墙因子未动，遮光面辐照度与后墙同级，单靠墙材质无法在不吹亮受光面的前提下提亮，根治需动灯光/天光，不在本任务范围）；③ 天花板只略去绿、仍暗（提亮需因子 ~4 或补光，不在本任务范围）。
## §28 R2-T28 教室白板面偏暗灰绿修复（2026-11-25，只调白板材质参数，不改结构）

- **问题**：R2-T27 留尾：白板面在 Godot 03 图里仍显暗灰绿（点取样 (62,86,81)；#127 图区域均值左 (86,115,112)、右 (75,102,97)，G 比 R 高约 25–30），与黑板墨绿、墙面暖褐区分不开。属 cl-board 的 WhiteBoard 材质本身在绿天光下偏色，不在 T27“只调墙面”范围。
- **成因（线性光模型反推，本地 Web 探针复核一致）**：白板贴图 `Plaster001__DCDCDC.jpg` 均值 (219,219,219)，线性反照率约 0.71；白板在西墙、面朝东，几乎只靠绿天光（`weather_system.gd:52`，ProceduralSkyMaterial ground_bottom_color #4a6b38，AMBIENT_SOURCE_SKY），探针反推西墙面辐照度线性约 (0.10, 0.20, 0.19)（G/B 约为 R 的 2 倍）；出射线性约 (0.07, 0.14, 0.13) → sRGB (76,109,106)，与实测一致。黑板不偏是因其反照率本身低且偏绿（贴图均值 (46,57,49)）；墙面已由 T27 因子补偿过。
- **修法（只改材质参数，几何/墙/灯光一字未动）**：WhiteBoard 贴图后串 Mix MULTIPLY 常量（复用 R2-T27 做法，见 `cl-board.py` 的 BASE_COLOR_FACTOR 分支），因子 **(8.6, 3.5, 3.6)**——R 抬最多以抵绿天光的 R 缺口，G/B 只补亮度；粗糙度、法线、贴图、WhiteBoardBack（FrameSilver）均不动。本地 Web 探针（复用 R2-T24 最小探针工程，Godot 4.4 Web 导出 + headless Chrome，0 console errors）两轮实测：候选 A (6.8, 3.4, 3.5) → 白板 (154,168,167)/(159,166,163)，仍偏绿约 10；候选 B (8.6, 3.5, 3.6) → **(166,170,169)/(171,168,165)**，三通道差 ≤4，浅灰白、不偏绿，遂采用 B。注意：因子 >1 时 Blender 预览下白板会显过曝粉白（属预期，Godot 为准）；亮面下 Plaster 贴图的法线/粗糙斑驳会显出来，呈细腻磨砂白板面，非缺陷。
- **关键坑——Blender 4.2 导出器硬 clamp（与 T27 同坑）**：`__gather_base_color_factor()` 里 `rgb = [max(min(c, 1.0), 0.0) for c in rgb]`，>1 的因子导不出。`cl-board.py` 与 `classroom.py` 各加 `_patch_glb_factors()`（与 T27 的 `cl-floor-walls.py` 同款）：导出后直接改 GLB 的 JSON chunk，把 `WhiteBoard` 的 baseColorFactor 写回 (8.6, 3.5, 3.6, 1.0)，只动 JSON chunk、不动 BIN chunk；两处补丁须保持同步（classroom.py 从 .blend 重导出，同样触发 clamp）。因子存在 .blend 的 Mix MULTIPLY 常量里，补丁后 .blend 与 .glb 一致。
- **重建**：重跑 cl-board.py（`assets/blender/classroom/cl-board-r2t28.log`），`DONE cl-board`，零 Error/Traceback；GLB 回读 39 对象；`cl-board.glb` 12,450,404 B，JSON 实测 WhiteBoard [8.6, 3.5, 3.6, 1.0]、BoardGreen 无因子（未动）；独立核对 WhiteBoardLeft/Right x[-4.792,-4.762]、Blackboard x[-4.802,-4.762]，与 R2-T25 一致、几何一字未动。重跑 classroom.py（`assets/blender/scenes/classroom-r2t28.log`），`DONE classroom`，零 Error/Traceback；APPEND 73+96+39+58+54+120，TOTAL/回读 **440** 对象（与 R2-T22/R2-T25/R2-T27 一致）；补丁命中 ['cl-floor-walls_wall_back', 'WhiteBoard']；classroom.glb 19,091,264 B、classroom.blend 5,536,236 B；wall_back [1.85, 0.62, 0.45, 1.0] 未动。
- **本地 Web 探针（最终重建件复核，非候选副本）**：把重建后的 classroom.glb（md5 `fe4ecb4751bce256ead0c1cac24b9807`）拷回探针工程重导出实拍，0 console errors，与候选 B 逐字节同图：白板左 **(166,170,169)**、右 **(171,168,165)**（改前 (76,109,106)/(75,103,98)）；黑板 (22,36,30) 仍墨绿；后墙 (94,86,68)、右墙 (170,154,137) 均未动；桌椅/讲台/空调/窗户无回归。截图 `~/workspace/review-rework-r2/r2t28-web-final-classroom.png`。
- **推仓**：commit `d25cb58a`（`d25cb58a2f03761525ce139c20c1c0b3253a9804`，父 `17723f0a`，2026-11-25 约 03:15 CST）：9 文件，blob SHA 已逐项核对与本地一致（cl-board.py `b8d4fcfe`、cl-board.blend `7d5810ac`、cl-board.glb `bfb7193a`、cl-board-r2t28.log `d69b193b`、classroom.py `50f2a5b1`、classroom.blend `6a93b1bb`、classroom.glb `52d0ac03`、classroom-r2t28.log `556f3517`、BLENDER_MODELS.md `40a09a2b`）；推后核对 HEAD 即 d25cb58a。注：推前重读 HEAD 为 `3a454919`，推仓瞬间并行任务 R2-T14b 的 `17723f0a`（道路两件 .py + BLENDER_MODELS.md 表格行）先落库，本提交以其为父、未撞车；已逐行 diff 核对：远端 BLENDER_MODELS.md 含 T14b 表格行与本 §28 两者，无覆盖丢失。
- **验证**：**blender-previews #109**（run 45467842214，head d25cb58a）classroom 组 job completed success，6 张逐张目视通过——cl-board：白板在中性光下呈过曝粉白（补偿因子本色，属预期，Godot 为准）、黑板墨绿、讲台/粉笔盒齐全、几何未动；cl-floor-walls：墙暖粉补偿色、4 窗洞/侧、门洞、地面、天花板齐全；cl-desks（48 套、腿落地）、cl-ac、cl-lights、cl-windows 均无回归（注：整 run 仍 in_progress，只剩 overview/dist 两 job 在跑，与本次无关）。**godot-verify #129**（run 45467841856，head d25cb58a）：completed success，**PASS=271 FAIL=0**；20 张截图已下载，03-classroom 目视通过：白板左 **(182,182,180)**、右 **(164,162,159)**（改前左 (86,115,112)、右 (75,102,97)），浅灰白、三通道差 ≤5、不偏绿；黑板 (32,45,38) 仍墨绿；后墙与 #127 同框取样 (80,89,78) 未动；桌椅/讲台/空调/窗户无回归。
- **还剩什么**：① 南墙/北墙遮光面仍偏暗橄榄、天花板仍暗（T27 遗留②③，根治需动灯光/天光，不在本任务范围）；② 白板因子 R=8.6 极大，若未来某时段直射阳光打上西墙白板（如清晨东向日光），板面会过曝成纯白、贴图斑驳消失——03 图 10:00 验收时段无此问题，属已知边界，不另修；③ Blender 中性光预览下白板显过曝粉白，属补偿因子本色，验收以 Godot 为准。

## §29 R2-T29 ov-windows-roofs 与新玻璃幕墙楼体重叠修复（2026-11-25，只改 ov-windows-roofs 一件）

- **范围**：只改 `assets/blender/overview/ov-windows-roofs.py`（+ 重建 .blend/.glb + 日志）；不改任何楼体 .glb/尺寸、不改其他件；只重建件级 .glb，不拼总览场景（总览重拼由终轮整合做）。
- **重叠清单（改前实测，Blender 4.2.0，ov-windows-roofs.glb + ov-bldA/B/C.glb 回读，包围盒 + BVH 面片相交）**：
  - ① A/B 窗带 80 件（frame 40 + glass 40）与新玻璃幕墙同墙面双层：BVH 面片相交 **7,242 对**（A frame 3,218、A glass 236、B frame 3,495、B glass 293）；全部集中在 F5 顶层（A F5 frame 3,218 对、B F5 frame 3,375 对 + glass 529 对：旧 F5 按收分 0.3m 做、半宽 A 19.7/B 15.7，埋进新楼体满幅 40×15/32×14 的幕墙里）与 B 东面（F1–F4 E 框各 28–36 对：东立面雨棚入口结构相交）。F1–F4 其余面 0 面片相交，但仍是双层：新幕墙面在 F2 带最外沿约 y 37.25–37.36（A 北，名义墙面 37.50 以内 0.14–0.25m），旧窗带框背 37.50、玻璃 37.53–37.57、框前沿 37.68、窗台板 37.74——旧带整体浮在幕墙外 ≥0.14m，是一层悬空的第二套窗。
  - ② A/B 屋顶膜 2 件与新屋顶板共面：膜底面 z=**18.3500** = 新屋顶板顶面 z=**18.3500**（板 18.10–18.35，膜 18.35–18.40，39×14 / 31×13）；0 面片相交（接触面被夹住），但膜是新板上多余的第二层板（新板已是成品深灰 PBR 面）。
  - ③ 不重叠（实测 0 面片相交，保留）：A/B 压顶盖板 4 件（底面 19.00 = 新混凝土压顶顶面 19.00，隐蔽接触；盖板 0.49 宽于压顶 0.42、外伸 0.035/边，与旧设计同款叠合）；A/B 设备盒 + 风扇 4 件（A 旧设备 x −61.2..−58.8 vs 新设备 1 号 −69.2..−66.8 / 2 号 −45..−43，A 风扇 −52.85..−51.15，B 无新设备，均无足迹重叠）；C 栋全部 37 件（窗带 32 + 屋顶 5，0 面片相交，C 栋旧件未换装）；lib/tower/dorm——本件无任何对象在其附近（本件 x −76.24..37.24、y 22.26..37.74；塔 y≥47、宿舍 x≥74、图书馆 y≤−50），零重叠。
- **修法（只改本件）**：删 A/B 窗带 80 件（C 栋专用：只留 C 窗带 32 件）；删 A/B 屋顶膜 2 件；A/B 设备盒 + 风扇保留，落座由膜顶 18.40 降 **0.05** 至板顶 **18.35**（贴板顶、不悬空、不下沉）；A/B 压顶盖板保留（19.00–19.12 不动）；C 栋一字未动。`_pbr_apply` 按材质名工作、删件不影响（膜材质仍由 C 膜在用）。
- **重建**：重跑 ov-windows-roofs.py（`assets/blender/overview/ov-windows-roofs-r2t29.log`），`DONE ov-windows-roofs`，零 Error/Traceback；窗 32、件 **45**、GLB 回读 **45**（改前 127）；`ov-windows-roofs.glb` 4,156,720 → **3,679,744 B**，`.blend` 5,046,268 → **4,306,308 B**。复测新 .glb：全部 12 组（A/B/C × frame/glass/roofdeck/coping/equip/fan）BVH 面片相交 **0 对**；A/B 设备/风扇底座 z=**18.35**，正好贴新屋顶板顶面；仅存膜为 C 膜（13.25–13.30，C 板顶 13.25，旧设计不变）。
- **推仓**：已推 `f9cfc1e0`，已核对建出；触发 blender-previews run **#110**（45470423796，19:27Z 触发），截至 03:53 仍 in_progress（4/6 组 success：classroom/pv/storage/charge；overview + dist 仍在渲染）。
- **验证**：blender-previews run **#110**（45470423796，head f9cfc1e0）completed **success**（6/6 组；overview 最晚完成）；artifact `blender-previews-overview` 17,945,247 B、20 张，下载逐张目视——**ov-windows-roofs.png ✓**：A 示意量块无窗（裸墙）、屋顶单层深灰板 + 压顶 + 设备/风扇，无双层窗带、无共面闪烁；C 栋 4 层蓝窗带 + 膜 + 压顶 + 设备/风扇齐全（render_max 聚类取景含 C 栋，与 .py 相机取景不同）；B 压顶框 + 设备/风扇在位，框内见地面（本件无 B 楼体衬底、膜已删；拼装后 B 屋顶板在下承托，落座已实测 18.35）；框外地面两处浅色影为 B 压顶/设备的日光投影、非几何。另目视 bldA/bldB/lib/tower/dorm/bldC 6 张：5 栋换装楼与 #106 一致，无回归。本地复核：同 .blend 本地 Eevee 渲 A 取景（裸量块 + 屋顶细部）与 C 取景（4 层窗带齐全）均与 Actions 图一致。godot-verify 总览验收由终轮整合做。
- **还剩什么**：① 总览重拼 + Godot 侧验收由终轮整合做；② 本件预览相机仍框 A 栋南立面（仅预览衬底，不导出），Actions 的 ov-windows-roofs.png 将显示无窗的 A 栋示意量块 + 屋顶细部，C 栋窗带不在该取景内，属修法本意、不另改取景（实测 render_max 聚类取景与 .py 相机不同，C 栋窗带实际入镜、见验证行）；③ 旧 A/B 窗带几何已从脚本删去，如终轮整合想恢复 A/B 窗带需按新幕墙面重做、不可直接 revert。

## §30 R2-T30 教室南/北墙遮光面与天花板偏暗补光（2026-11-25，只加室内补光，不动室外灯光、不改材质模型）

- **问题（T27/T28 遗留②③）**：南墙窗间墙仍暗橄榄绿、北墙顶带与天花板仍暗。本地探针实测（晴 10:00，03 机位 + 南/北反向机位，见 `~/workspace/review-rework-r2/r2t30-web-final-classroom.png`）：南墙窗间墙 **(65,87,82)**（G 比 R 高 22，暗绿）、南/北墙顶带（窗上沿至天花板）**(44,61,28)/(49,63,29)**（极暗绿）、天花板 **(40,58,24)**（暗绿）；对照：西墙（后墙）已达标 (96,86,67)、北墙窗间墙受光面 (170,152,133) 本已暖褐、北墙受光面 (199,131,100)。
- **成因（实测定位）**：太阳 `shadow_enabled=false`，无遮挡——朝日面（北墙内面、东墙）直接受光，背日面（南墙内面）与朝下的天花板只靠绿天光（`weather_system.gd:52`，地面半球 #4a6b38，AMBIENT_SOURCE_SKY）。T7 已证室外全局参数动不得（环境光再降 44% 或太阳再升 78% 会把草地推出 SPEC），且单靠墙材质分墙补偿也已到头（T27：提亮遮光面会同时吹亮同一面墙的受光面），根治只能室内补光。教室内原无任何 Light3D（cl-lights 只有发光灯管 mesh，不发光照），故走方案①“加灯”，方案②无物可调。
- **方案选型（全部本地探针实测，Godot 4.4 原生 + Web 双链路，数值一致 ±1）**：① 1 盏 Omni（中心，E=0.6，range 7，y=1.8，暖 #ffe0b3）→ 天花板 (40,58,24)→(133,117,82) 好了，但西墙 (96,86,67)→**(129,98,74)**（+33，已达标的墙被抬亮，不可用）；② 2 盏 Omni（x=±2.2，E=0.6）→ 西墙 (165,111,82)，更糟；③ 4 盏 Spot 分置（x=±2.4，南北各两盏，E=0.7）→ 西墙 (122,96,73)，仍超标。④ **两盏 Spot 水平对打（定案）**：只动南/北墙与天花板，西墙 +2、北墙受光面 +11、白板/黑板一字不动。
- **修法（只改 `scripts/classroom_interior.gd`，+`_add_fill_light()`，GLB/材质/室外参数一字未动）**：两盏 SpotLight3D，位置 **(0, 1.8, ±0.4)**（房间中心、高 1.8m，南北各偏 0.4m），水平向外（沿 ±z）、色 **#ffe0b3**、能量 **1.5**、锥角 **120°**、衰减 1.0、无阴影。朝向用 `rotation` 定（Spot 默认沿 -z 出光，向南一盏转 180°），不用 `look_at`（内景在主场景有全局位移 (-56,0,-30)，`look_at` 的全局目标点在局部坐标下会指错方向；探针已用 rotation 版复核，数值与 look_at 版逐值相同）。两盏灯挂在 ClassroomInterior 下：① 内景只在教室场景可见，总览/其他场景 `visible=false` 时灯不渲染，室外与草地零影响；② Spot 默认 `spot_range=5m`，锥体基本不出南/北墙（墙距 3.63m），漏到墙外的光只剩 1.37m，且教室场景下宿主楼体已隐藏、相机在室内。GLB 回退（程序化）分支同样加灯。
- **本地探针（改前→改后，Web 实拍 `r2t30-web-final-classroom.png`，0 console errors；原生同参数逐值一致）**：南墙窗间墙 (65,87,82)→**(129,118,101)**、(120,114,101)；南/北墙顶带 (44,61,28)/(49,63,29)→**(114,103,70)/(118,105,72)**；天花板 (40,58,24)→主视角 **(136,119,84)**、南/北视角 (176,149,109)/(175,149,109)，三通道 R>G，去绿提亮；西墙 (96,86,67)→**(98,89,70)**（+2）；北墙受光面 (199,131,100)→**(208,137,103)**（+9）；北墙窗间墙 (170,152,133)→(198,168,145)（+28，未过曝）；白板左 (195,191,192)→(195,191,192)、右 (118,121,117)→(118,121,117)；黑板 (29,42,34)→(29,42,35)；地板 (178,175,143)→(196,185,149)、桌面 (167,160,125)→(186,171,131)，仅随室内整体提亮，无色偏。`godot --headless --check-only` 语法通过。探针工程 `~/workspace/r2t30-webprobe/`（原生）与 `~/workspace/r2t30-webprobe-web/`（Web 导出，补光参数默认写入），截图 `~/workspace/review-rework-r2/r2t30-web-{main,south,north}.png` + `r2t30-web-final-classroom.png`。
- **推仓**：commit `bc21ea14`（`bc21ea145405872a3aacc3e2ee627f3423a5c777`，父 `a4ceb4af`，2026-11-25 约 04:10 CST）：2 文件，blob SHA 已逐项核对与本地一致（scripts/classroom_interior.gd `33c007a3`、BLENDER_MODELS.md `ff580d2f`）；推后核对 HEAD 即 bc21ea14（之后 R2-T31 推到 ff89d969，本提交仍在历史中）。推前重读 HEAD 为 `a4ceb4af`，与实测父提交一致，未撞车。
- **验证**：**godot-verify #134**（run 45477898696，head bc21ea14）：completed success，**PASS=271 FAIL=0**（job 日志 `VERIFY-SUMMARY: PASS=271 FAIL=0`）；20 张截图已下载逐张目视通过——03-classroom：西墙 (97,87,67)（改前 (96,86,67)，+1）、白板左 (172,172,170) 与 #129 相同、黑板 (29,42,35) 仍墨绿、桌椅/讲台/空调/窗户无回归；地板 (187,187,156)→(208,200,164)、桌面 (197,190,152)→(226,208,163)，与探针预测的补光增量（+18/+19）一致，证实补光灯在 CI 构建里已生效。草地五档 G（同框取样，与 #129 逐值相同）：晴 175 / 多云 151 / 阴 121 / 暴雨 88，单调拉开、在 T7 范围内（晴 174–175 / 多云 151–157 / 阴 120–132 / 暴雨 87–105）；其余 19 张（00/01/02/04–19）逐张扫视无回归。注：CI 03 图取景内看不到天花板与南墙窗间墙（顶栏/信息面板遮挡 + 机位朝西），南墙窗间墙与天花板的改后数字以本地 Web 探针南/北反向机位为准（见上），CI 图只作无回归与灯光生效的佐证。
- **还剩什么**：① 南墙西端窄条（03 图左缘、窗下墙，(73,69,54)，R 已略大于 G、不发绿但仍暗）——聚光锥角边缘 + 掠射角所致，再抬能量会先吹亮北墙窗间墙与天花板中央，留终轮定夺；② 天花板四角仍略暗（锥角边缘，目视已不发绿）；③ 窗玻璃仍蓝绿（玻璃材质本身不吃灯光，非墙面，不在范围）；④ 补光不随天气变（晴/雨/暴雨档教室内亮度相同，03 图只验晴 10:00；教室无雨天截图在 shots 清单内，CI 不覆盖）。

## §31 R2-T31 PBR 源文件入仓审计 + 补推（2026-11-25 04:14–04:35 CST，只审计与补推源文件，不改模型、不重跑烘焙/渲染）

- **背景**：R2-T14b 查实 PBR 源文件有一批只在本地、未入仓；`.blend` 现靠打包自给自足，渲染不受影响，但干净检出重跑烘焙 / PBR hook 会因文件缺失失败（hook 有断言）。另 R2-T9b 称 R2-T21b 已于 17:24Z 在 `4228878e` 补推过 24 个文件——本次先审计、再补推缺的，不重复推已入仓的。
- **审计（HEAD `defe5ad1`，2026-11-25 04:14 CST）**：本地 `assets/external/` 下 PBR 贴图原图共 **73 张**（`pbr-tinted/` 20 + `polyhaven/` 27 + `ambientcg/` 4 套共 26 张 JPG/PNG；ambientCG 各套附带的 `.blend` / `.mtlx` / `.tres` / `.usdc` 共 16 个文件是厂商格式包、不是贴图原图，不在本次范围）。本地逐文件算 git blob SHA，与远端递归 tree 逐项比对：**46 张已入仓、27 张缺失、0 张内容漂移**（已入仓的本地与远端 SHA 全部一致，无需重推）。
- **已入仓的 46 张**：`pbr-tinted/` 19 张 → `4228878e`（其消息称“25 张”，实推 24 个文件：19 张 pbr-tinted + 5 张 polyhaven，数字以实推为准）；`pbr-tinted/track_B8543F_color.jpg` → `f39cd380`；`polyhaven/` 15 张（blue_metal_plate / concrete_wall_007 / corrugated_iron_02 / white_stucco / wooden_floor_01 各 3 图）→ `967a3f28`；`polyhaven/` 5 张（concrete_pavement_03_rough、grey_roof_01_nor_gl、grey_roof_01_rough、red_bricks_04_nor_gl、red_bricks_04_rough）→ `4228878e`；`ambientcg/` 6 张（Plaster001 与 WoodFloor051 各 Color / NormalGL / Roughness）→ `967a3f28`。
- **缺失的 27 张（本次补推）**：`polyhaven/` 7 张——`asphalt_01_diff/_nor_gl/_rough_1k.jpg`（asphalt 染色源图）、`concrete_pavement_03_diff/_nor_gl_1k.jpg`（ov-road-walk 步道铺装，`ov-road-walk.py` 直接引用，其中 nor_gl 是 hook 活引用缺图）、`grey_roof_01_diff_1k.jpg`（roof 染色源图，`tint_textures.py` 引用）、`red_bricks_04_diff_1k.jpg`（brick 染色源图）；`ambientcg/` 20 张——Concrete034 全套 6 张、Grass004 全套 7 张、Plaster001 剩余 3 张（预览图 / Displacement / NormalDX）、WoodFloor051 剩余 4 张（预览图 / AO / Displacement / NormalDX）。缺失成因：此前只推了 hook 当时直接引用的图，染色源图与非 hook 用图一直只在本地。单张最大 2,339,612 B（Grass004 NormalGL），合计 22,028,101 B，均 <40MB 单 blob 上限，无跳过文件。
- **推仓**：已推 **`3360dea6`**（一次 push-files 提交，27 个文件，父 commit `defe5ad1`），已核对建出：HEAD 即 `3360dea6`，27/27 blob SHA 与本地一致；仓库内 PBR 贴图现为 73/73 全量。文件级来源、授权（全部 CC0）与 blob SHA 见 `assets/external/SOURCES.md` 新增“PBR 源文件入仓记录”一节。
- **验证**：本次未改任何 `.blend` / `.glb` / `.py`，未重跑烘焙与渲染；补推未触发任何 workflow run（blender-previews 只监听 `assets/blender/**` 等路径，本次只动 `assets/external/**`，按 head SHA 查 runs 为 0），无需等 run。
- **编号说明**：任务书称“新起 §30”，但 §30 已被 R2-T30（教室补光）占用，故本节顺延为 §31；§24/§29 一字未动。
- **还剩什么**：ambientCG 4 套附带的 `.blend` / `.mtlx` / `.tres` / `.usdc` 共 16 个文件仍只在本地（非贴图源文件）；如以后需要干净检出重建厂商材质包，再另行补推。

## §33 R2-T33 R-N2 路与新跑道 +3m 缓冲东尖重叠修复（2026-11-25，只改规划缓冲口径，不动任何几何）

- **问题**：终轮整合已知待办：R-N2 路与 R2-T1b 收界后的新跑道 +3m 缓冲东尖重叠，GREEN_PLAN.md §8.3 称“约 1.5m 重叠，是路任务的遗留问题”。R-N2 按旧椭圆（中心 (-80,-25)、rx40、+3m 缓冲东尖 -37）选线，路西缘 -34.5 距旧尖 2.5m；R2-T1b 把跑道东移至中心 (-62,-25)、外椭圆 rx28/ry40，东尖东移 6m，路落进新缓冲的东尖区内。
- **实测（Blender 4.2.0，`assets/models/` 三件 GLB 回读 + 椭圆解析几何；回读数与 .py 常量逐项一致）**：
  - R-N2 铺装 `walkway_RN2_x-33` x[-34.500,-31.500]、y[-76.000,18.500]、z[0,0.100]；西路缘 x[-34.650,-34.500]、东路缘 x[-31.500,-31.350]、y[-75.700,18.350]；`ov-road-walk.glb` 回读 **171** 对象（与 R2-T14b 一致）。
  - 跑道 `ov-track.glb` 回读 **17** 对象：环 `track_ring` x[-90,-34]（外椭圆 rx28/ry40，东尖 -34.0）、外缘路缘石 `track_curb_outer` x[-90.3,-33.7]（东尖 -33.7）、外分道线东尖 -33.925；`ov-field.glb` 回读 **30** 对象，场东缘 x=-47、看台至 -44.1，球场与路无交集。
  - **路 vs +3m 缓冲（外椭圆 +3m：rx31/ry43，东尖 (-31,-25)）**：路铺装在缓冲内 y **-44.85..-5.15（39.70m）**，其中全宽 3.0m 都在缓冲内 y **-32.69..-17.31（15.38m）**；含路缘（x -34.65..-31.35）为 y -45.24..-4.76（40.49m）。y=-25 处路全宽都在缓冲内（缓冲东尖 -31 在路东缘 -31.5 以东 0.5m）。
  - **“约 1.5m”的出处（实测还原）**：+1m 缓冲（草地排除用口径，GREEN_PLAN §8.2：外椭圆 +1m，东尖 -33）下路西缘 -34.5 侵入恰好 **1.5m**（y -38.02..-11.98，26.03m）；+3m 缓冲下侵入量是全宽 3.0m。简述的 1.5m 是 +1m 口径的数，+3m 口径以本节实测为准。
  - **路 vs 跑道几何（BVH 面片相交，另见“还剩什么”①）**：路铺装 + 西路缘 vs 跑道环/外缘路缘石/外分道线/起跑线共 **415 对**（铺装 vs 环 51、vs 外缘路缘石 126、vs 外分道线 33、vs 起跑线 5；西路缘 vs 环 56、vs 外缘路缘石 132、vs 外分道线 8、vs 起跑线 4；东路缘 0 对）。最大交叠：路缘石 0.8m 宽 × y -34.51..-15.49（19.03m）、环 0.5m × y -32.53..-17.47（15.05m），路缘石顶 z=0.15 高出路面 0.05m。这是路与跑道几何的既存物理交叠，不在本任务命名的“缓冲重叠”之内，本次未动。
- **修法（选 ②，不选 ①；二选一，以实测定；不两边同改）**：
  - **选 ② 缓冲尖局部修形**：缓冲是规划量，**无任何几何**在 .glb 里（track 17 件、field 30 件回读，0 件是缓冲）；只改 GREEN_PLAN.md 与 green_layout.json 的缓冲口径文字，路与跑道几何、对象数、其余件一字不动，零新压线、零重建风险。修形定义：禁入区 = +3m 缓冲椭圆（中心 (-62,-25)、rx31/ry43）− R-N2 路廊矩形 **x[-34.65,-31.35]×y[-76,18.5]**（铺装 -34.5..-31.5 + 两侧路缘石各 0.15m）；路廊内缓冲东界以路西缘为准，该处距跑道外缘东尖（-34.0）0.5m（其余地段仍为 3m）；路廊外缓冲一字不动。路与跑道“各在位”。
  - **① 不选（按字面“东缘西移”）**：方向反了。路已在缓冲东尖以西，西移是往跑道/缓冲深处走：西移 1.5m（路 -36..-33）则缓冲内路段从 39.70m 拉长到 **46.83m**（y -48.42..-1.58），与跑道环最大交叠从 0.5m 扩到 **2.0m**，BVH 对数约翻 3 倍。实测否决。
  - **① 不选（改读作东移，唯一能让路出缓冲的方向）**：出 +3m 缓冲尖须整路东移 ≥3.5m（路西缘 -34.5→≥-31.0），东缘到 -28.0，正压 R-N2-T 东列树干（`ov-trees.glb` 实测在位：x=-28，y -48..0 共 7 棵在重叠带内），且 1m 东移就会压草地色带 `Slab_G2_053`（西缘 -31.0，路东缘 -30.5，0.5m 交叠，y -45..-5 一带）并错开环南路内缘石 R-N2 缺口（x -34.5..-31.5，`ov-road-main.py:305` 分段 (-87.0,-34.5)/(-31.5,56.5)）；另 GREEN_PLAN §2 线位、R-N2-T 东西两列、D6 备注全要改。只东移 1.0m（中心 -32）也救不了：仅清跑道外缘路缘石 0.2m，路仍在 +3m 缓冲内 33.83m（y -41.92..-8.08），且照样新压 `Slab_G2_053` 0.5m。东移要么不清缓冲、要么制造新压线，均违反“无新压线”与“改动量最小”。
- **改动（只改规划口径 2 文件 + 本节；无 .py/.blend/.glb 改动、无重建）**：
  - `assets/blender/overview/GREEN_PLAN.md`：① §2 R-N2 行：西侧“2.5m 避开旧缓冲东尖（-37）”改为已作废口径 + R2-T33 路廊例外修形（§5）；② §5 禁入行：操场 +3m 缓冲后加“（R-N2 路廊例外见下条，R2-T33）”；③ §5 R2-T1 衔接整段重写：原“终版椭圆只会更小、不会冲突”假设已证伪（东尖东移 6m），写入修形定义与实测数；④ §8.3 末行：遗留问题改为 R2-T33 已闭环 + “约 1.5m”出处说明。
  - `assets/blender/overview/green_layout.json`（JSON 校验通过，diff 仅 3 行）：`meta.playground_assumption`、`exclusions.playground` 由旧椭圆 (-80,-25) rx40 rz28 改为新椭圆 (-62,-25) rx28 ry40 +3m 缓冲 + 路廊例外；`roads[1]`（R-N2）`note` 同步改写。`polyline`（(-33,-76)→(-33,18.5)）、线宽、衔接点一字未动。
  - 无重建：缓冲无几何，路/跑道几何不动，故 `ov-road-walk.py/.blend/.glb` 与 `ov-track.py/.blend/.glb` 均未重跑；回读对象数改前改后一致（road-walk 171、track 17、field 30）。`ov-road-walk.py:409-410` 的旧注释（“R-N2 西缘距操场缓冲椭圆东尖 (-37) 2.5m”）仍引旧尖，属文字滞后，本次未动 .py（只改注释也要走全量重建流程，零几何收益），见“还剩什么”③。
- **推仓**：已推 `490d4677`（GREEN_PLAN.md + green_layout.json + 本文档一次 push-files），已核对建出；触发 blender-previews run **#112**（45483359861，04:41 CST 触发）。
- **验证**：blender-previews run **#112**（45483359861，head 490d4677）：**completed success（6/6 组，约 05:51 CST 完成）**。artifact `blender-previews-overview`（17,945,158 B）已下载，20 张 PNG 全量品红扫描（R>150、G<140、B>150）**全部 0.0000%**；逐张目视：**ov-road-walk.png 通过**——步道网在位（R-N1 北横、R-N2/R-N3 两纵、R-N5 中部连接、R-N4 池塘北岸弧、南门广场铺装），浅色铺装 + 黄色触感线正常，与 #110 基线同取景、目视一致；**ov-track.png 通过**——红环 + 白分道线 + 起跑线完整，环面颗粒可见，与 #110 基线一致；其余 18 张扫视无回归（road-main 环路沥青 + 黄中线完整、field 球场/球门/看台在位、lawn 色带与路/楼缺口正常、trees 全布局在位、bldA/bldB 玻璃幕墙、bldC 灰泥 + 灰瓦顶、canteen 红砖 + 柱廊、dorm 双栋、gym 红砖、lab 白墙红柱、flag-lamp 三旗两灯、gate 门楼 + 传达室、lib 玻璃楼、parking 三车入位、tower 米色高层、transformer 变压器 + 围栏、windows-roofs 按 R2-T29 修后状态：A 栋无窗带量块 + C 栋窗带在右下角可见）。结论：本次几何一字未动，规划缓冲重叠已按本节修形消除，路与跑道各在位、无新压线、无回归。注：#112 与 #110 的 20 张 md5 均不同，属 Eevee 采样噪声 + 其间 ov-trees（R2-T32 移 3 棵树）与 windows-roofs（R2-T29）的 .blend 变化，逐张目视均与基线一致，非回归。
- **还剩什么**：① 路 vs 跑道几何 415 对面片相交（上文）未修——修它须另立任务：路局部东移（须联动草地 `Slab_G2_053` 西缘与环南路内缘石缺口）或跑道外缘路缘石局部修形，二者都动别的件，按本任务“不要同时改两边”不在此做；② 附带发现（实测，非本任务范围）：R-N2-T 西列 5 棵树压在新跑道环面上——`ov-trees.glb` 实测 x=-38，y=-40/-32/-16/-8/0，环东臂在 y=-32 处 x -42.48..-34.43（mesh 顶点复核 y≈-32 处东臂至 -34.30），5 棵树干均落在环面内（y=-48 在环带外，安全；y=-24 按旧缓冲跳过）；东列 x=-28 的 7 棵在 +3m 缓冲内但不在环面上。树是 ov-trees 件，本次未动，留终轮整合；③ `ov-road-walk.py:409-410` 旧注释（-37 尖、2.5m）待路件下次重建时刷新；④ 总览重拼 + Godot 侧验收由终轮整合做（本次两件几何未变，总览场景不受影响）。

## §34 R2-T34 ambientCG 厂商格式文件是否需补推评估（2026-11-25 04:29–04:40 CST，只审计与记录，不改模型、不补推文件）

- **背景**：R2-T31 遗留：ambientCG 4 套（Concrete034、Grass004、Plaster001、WoodFloor051）附带的 `.blend` / `.mtlx` / `.tres` / `.usdc` 共 16 个文件仍只在本地，未入仓；R2-T31 已把 73 张贴图原图全量入仓（73/73），这 16 个是厂商格式包、不是贴图原图。本任务实证：干净检出重建时到底用不用得上它们。
- **16 个文件清单**（本地 `assets/external/ambientcg/` 下，合计 4,441,243 B，单文件最大 1,109,220 B，均远 <40MB Git Data API 单 blob 上限；blob SHA 为本地算出，仅作审计记录，未入仓故远端无对应 blob）：

| 文件 | 大小 (B) | 本地 blob SHA |
|---|---|---|
| `ambientcg/Concrete034/Concrete034_1K-JPG.blend` | 1,099,204 | `c80336d3bd41bb922c652249d5839449b8ac93c6` |
| `ambientcg/Concrete034/Concrete034_1K-JPG.mtlx` | 2,302 | `4aaac41af2546c09b6cd006a7cf53ce2a875652f` |
| `ambientcg/Concrete034/Concrete034_1K-JPG.tres` | 816 | `f60366fe60191172490993b322384d8f08713c41` |
| `ambientcg/Concrete034/Concrete034_1K-JPG.usdc` | 2,907 | `ae805f74a4355b4a5dce30ce7a88756a73b5b00a` |
| `ambientcg/Grass004/Grass004_1K-JPG.blend` | 1,109,012 | `3957698a5fa3f38cbd15372512c774a0b953f2c3` |
| `ambientcg/Grass004/Grass004_1K-JPG.mtlx` | 2,257 | `9a23c5aaa90bde8c423c3fc02288cf09fe33679a` |
| `ambientcg/Grass004/Grass004_1K-JPG.tres` | 1,015 | `903bc5df8fc12157b696f2305ca6c7118b63eb5c` |
| `ambientcg/Grass004/Grass004_1K-JPG.usdc` | 2,969 | `5457c57a59c60f211260c04d1ddb4ae245944d55` |
| `ambientcg/Plaster001/Plaster001_1K-JPG.blend` | 1,099,204 | `71d7b834a52b56475cd7239bfbec5eff8c42f44e` |
| `ambientcg/Plaster001/Plaster001_1K-JPG.mtlx` | 2,287 | `1810e4bc69ff14ed579a279c099785df5f3ea71f` |
| `ambientcg/Plaster001/Plaster001_1K-JPG.tres` | 812 | `f4f9bec5337eec566aea468277ec4db3d12813ff` |
| `ambientcg/Plaster001/Plaster001_1K-JPG.usdc` | 2,903 | `8833dc6ce59ceed8988c23a7b1566349c833a0e8` |
| `ambientcg/WoodFloor051/WoodFloor051_1K-JPG.blend` | 1,109,220 | `1353ade85dce8c83e27981a90c4fa53759ebd472` |
| `ambientcg/WoodFloor051/WoodFloor051_1K-JPG.mtlx` | 2,317 | `3449b8bd288b475d2d5d6b75ff208752d894b9aa` |
| `ambientcg/WoodFloor051/WoodFloor051_1K-JPG.tres` | 1,035 | `d471f1cef3e7d95f5ea7fa038b4e52bc09f8e28f` |
| `ambientcg/WoodFloor051/WoodFloor051_1K-JPG.usdc` | 2,983 | `0076031d8cfc339b007f9335ad8dedd9fd700b07` |

- **审计证据（HEAD `c31ea9bf`，2026-11-25 约 04:30 CST，工程根目录下 grep，全部零命中）**：
  1. 厂商格式精确文件名（`Concrete034_1K-JPG.(blend|mtlx|tres|usdc)` 等 4 套，`.py` / `.gd` / `.sh` / `.cfg` / `.tscn` / `.tres`，除 `assets/external/ambientcg/` 自身外）：**0 命中**。
  2. `.mtlx` / `.usdc`（全工程 `.py` / `.gd` / `.sh`）：**0 命中**；`.gd` 中 `blend|mtlx|usdc`：**0 命中**；`.github` / `tools` / `scripts` / `scenes` / `shaders` / `data` 中 `.mtlx` / `.usdc` / `ambientcg.*.(blend|tres)`：**0 命中**；`.import` / `.tscn` / `.godot` / `.cfg` 引用厂商格式：**0 命中**。
  3. 工程内 50 个 `.blend` 二进制 `strings` 审计：厂商格式文件名 **0 命中**；`ambientcg` 字符串只见于 12 个 `.blend`（ov-tower / ov-bldC / ov-lab / ov-canteen / cl-windows / cl-desks / cl-floor-walls / cl-board / di-busbar / scenes/dist / scenes/overview / scenes/classroom），**全部是 `*_Roughness.jpg` / `*_NormalGL.jpg` 贴图路径**（hook 换入的 JPG，相对 `//../../external/ambientcg/...`），无一指向厂商格式。
  4. `_pbr_apply.py` 加载逻辑：`SETS` 只列 JPG（Plaster001 只用 `Plaster001_1K-JPG_Roughness.jpg`，其余为 `pbr-tinted/` 与 `polyhaven/` 的 JPG）；`_load` 用 `bpy.data.images.load`（图片加载器，读不了 `.blend` / `.mtlx` / `.usdc`）。其余引用 ambientCG 的脚本（cl-desks / cl-board / cl-windows / cl-floor-walls / di-busbar / `tint_textures.py`）也只引 `*_Color` / `*_Roughness` / `*_NormalGL.jpg`。代码里出现的 `.blend` 引用全部是工程自有件（ov-*/cl-*/di-*/ch-*/st-*/pv-*/scenes/*.blend），无一指向 `ambientcg/`。
  5. 厂商文件自身只指向 JPG：4 个 `.tres` 是 Godot `StandardMaterial3D`，只引用同目录 JPG（`./*_Color/_Displacement/_Roughness/_NormalGL.jpg`），且未被任何场景/脚本引用；4 个 `.blend` 只引用同目录 JPG（相对 `//*_Color/_Displacement/_NormalGL/_Roughness.jpg`）。它们是同一材质的另一种格式封装（Blender / MaterialX / Godot / USD），不是重建流程的输入。
  6. 远端 tree 核对（HEAD `c31ea9bf`，递归 tree，未截断，共 1028 个 blob）：PBR 贴图 **73/73 在仓**（`pbr-tinted/` 20 + `polyhaven/` 27 + `ambientcg/` 26，张数与 R2-T31 结论一致）；`assets/external/ambientcg/` 下厂商格式文件 **0 个在仓**。
- **结论①：不需要补推**。干净检出重建（重跑烘焙 / PBR hook、Actions 渲染）只读 JPG 贴图；工程内没有任何脚本、流程、场景或 `.blend` 读取这 16 个厂商格式文件。16 个文件继续只放本地即可；万一以后真要厂商材质包，可从 ambientCG 官网原包重下（CC0），无需为它们占仓库。
- **验证**：本次未改任何 `.blend` / `.glb` / `.py`，未重跑烘焙与渲染；只改两处文档（本节 + `assets/external/SOURCES.md` 新增同名一节），一次 push-files 提交，推后以 API 核对 HEAD 与两文档 blob SHA 与本地一致。
- **编号说明**：§32 已派给 R2-T32、§33 已派给 R2-T33，本节顺延为 §34；§24/§29 一字未动。R2-T31 §31 末尾与 SOURCES.md 末尾的“还剩 16 个文件”两处旧行是历史记录、原文保留，本节为其闭环结论。

## §32 R2-T32 T15 遗留树位修正（2026-11-25，只改 ov-trees 一件 + 本节）

- **背景**：R2-T15（§17.6）完工时如实留下 2 项：① 西沿线 3 棵旧树落在操场 3m 缓冲内（跑道面外，v2 原位）；② 密植带新旧交错 3 对间距 1.56–1.81m（设计 2.5m、抖动后收窄，冠层交错）。
- **定位（Blender 回读实测，非脚本复算）**：改前 `.blend` 回读 474 对象 / 473 棵树。② 3 对已逐棵确认——D1 新树 `Tree_114` (117.50,-40.50) ↔ 旧沿线 `Tree_404` (119.06,-40.40) = **1.56m**；D1 `Tree_131` (117.50,78.50) ↔ 旧 `Tree_434` (119.12,79.11) = **1.73m**；D1 `Tree_107` (117.50,-89.50) ↔ 旧 `Tree_392` (119.27,-89.11) = **1.81m**，与 R2-T15 记录一字不差。① 3 棵为旧西沿线 `Tree_405` (-119.52,-33.96，高 12.45m)、`Tree_407` (-119.30,-24.29，高 8.06m)、`Tree_409` (-119.48,-16.71，高 11.83m)。
- **① 的实测结论：已合规，不移动（任务前提被后来的跑道改动 supersede，如实记录）**：R2-T15 写遗留时按 GREEN_PLAN 旧椭圆（中心 (-80,-25)、rx40/ry28、+3m 缓冲）算，3 棵树归一化半径 r² 0.84–0.93（<1，在旧缓冲内）；但现行跑道已是 R2-T1b 新椭圆（`ov-track.py`：中心 (-62,-25)、rx28/ry40，西缘 -90.30），禁入椭圆也已按 R2-T18 §8.3 改走新跑道 +1m（旧椭圆已废）。按现行几何复算：3 棵树 r² **3.91–3.98**（>1 即在缓冲外），距新跑道西缘约 **29m**。把它们西移出“旧缓冲”（约 x=-123，距校园边界仅 2m）只会打散西沿线、毫无收益，故 3 棵位置一字不动；`.py` 文件头与 §17.6 旁注已同步改写这一结论。若父 agent 仍要求按旧椭圆移，另派任务注明以旧椭圆为准。
- **② 修法（只动旧树，D1 网格不动）**：3 棵旧沿线树沿 x 东移、y 不变，与 D1 伙伴间距拉到 **2.60m**（留 0.10m 余量），仍在密植带内、距东主路东缘（x=114）≥6m、距校园边界（x=125）≥4.9m、不压路/缓冲；高度档与模型一字不改（`fixed` 列表顺序与数量不变，`rng_h` / `rng` 消费顺序不变，其余 470 棵位置、模型、高度全部不变）。旧→新坐标：`Tree_404` (119.06,-40.40) → **(120.10,-40.40)**（+1.04m）；`Tree_434` (119.12,79.11) → **(120.03,79.11)**（+0.91m）；`Tree_392` (119.27,-89.11) → **(120.07,-89.11)**（+0.80m）。实现：`ov-trees.py` 升 v4，新增 `R32_D1` 映射（键为抖动前坐标、值为 D1 伙伴 y）+ 一条 `elif` 分支，`nx = 117.5 + sqrt(2.6² − (y − d1y)²)`，RELOC 日志打 `R2-T32-dense-pair-2.6m`。
- **重建（`assets/blender/overview/ov-trees-r2t32.log`，Blender 4.2.0 本地 `-b`）**：EXIT=0，日志零 Error/Traceback；新种 327 + 旧树换模 146 = **473 棵**，三角面 **120,634**（与 v3 一字相同，≤300k 预算），GLB 回读 **473** 棵树对象；RELOC 共 40 条（L1 37 + R2-T32 3）。改后独立回读复核：3 棵新位 (120.10,-40.40)/(120.03,79.11)/(120.07,-89.11) 与 D1 伙伴间距均为 **2.60m**；3 棵西沿线树位置与高度与改前逐值相同；全量两两间距复核：<2.5m 的 16 对全部是改前已有的 ≥2.0m 对（北沿线 2.00m×5、D3 2.14–2.19m×4、其余 2.03–2.39m，设计下限 2m，见 GREEN_PLAN §6 校验条），无新增 <2.0m 对、无新遮挡引入。
- **推仓**：commit `4be595be`（`4be595be9cd674ba10f8d44da799b5c191191f1e`，父 `a48fe1b1`，2026-11-25 约 04:37 CST）：5 文件，blob SHA 已逐项核对与本地一致（ov-trees.py `27f63138`、ov-trees.blend `ee718d0a`、ov-trees.glb `5a608d5d`、ov-trees-r2t32.log `67b0edb9`、BLENDER_MODELS.md `2a8fa77f`）；推后核对 HEAD 即 4be595be。推前重读 HEAD 为 `a48fe1b1`（R2-T34），与实测父提交一致，未撞车。ov-trees.blend 6,005,372 B / ov-trees.glb 3,546,916 B（与 v3 同体积，只改 3 棵位置）。
- **验证**：**blender-previews #111**（run 45482654452，head 4be595be）：completed **success**，6 组全部 success（overview 约 55 分钟）；artifact `blender-previews-overview`（17,944,824 B）已下载，20 张 PNG 逐张目视 + 品红像素扫描（20 张全部 0 品红像素）——**ov-trees ✓**：473 棵全在位、绿冠完整无品红无缺失，东密植带双排行间已见空隙、无冠层交错团块（说明：总览 1280×720 下 1m 位移约 1–2px，单棵的精确 2.60m 以 Blender 回读数值为准，渲染图只作无压线、无新遮挡、无品红的佐证）；西沿线 3 棵仍在原位成行。其余 19 张扫视无回归（bldA/bldB/lib 蓝玻璃幕墙、dorm 桃砖、canteen/gym/lab 红砖、field 球场、track 新椭圆长轴南北向、parking 三车、road-main 环路、tower、transformer、windows-roofs 均正常）。
- **编号说明**：本节即预留的 §32（§33 已派 R2-T33、§34 已是 R2-T34，两节先落）；§24/§29 一字未动；只改 ov-trees 一件（`.py` / `.blend` / `.glb` + 本轮日志），未拼总览、未动 Godot。

## §35 R2-T26：03-classroom 桌椅腿不可见——机位遮挡说实证与推翻（2026-11-25，只探针与记录，不改模型、不改 03 机位）

- **任务**：R2-T23 用 godot-verify #119 的 03-classroom.png 目视判桌椅腿/书篮/横撑“不通过”（桌面呈悬浮薄板）；R2-T24 诊断称“截图过期、假阳性”。本任务实证机位遮挡说：严格复现 CI 的 03 机位，再用放低放平的对比机位截图；若证实是机位遮挡就修 03 机位，否则如实写、给下一步方向，不硬拗结论。
- **① R2-T24“截图过期”说的更正（API 实测，非转述）**：run **45437816576 = #119**，head `0b6b8ae8`，success；run **45426566166 = #109**（head `587007d9`），不是 #119；compare `72897e90...0b6b8ae8`：status `ahead`、ahead **21**、behind **0**、merge-base = `72897e90`——T17 换装提交确在 #119 的 checkout 祖先链里，新桌椅确在 #119 的 checkout 里，R2-T24“截图过期”不成立。R2-T23 的不通过判据有效。
- **② 模型里腿几何确实存在（GLB 直接解析，非目视推测）**：当前 main 的 classroom.glb（19,091,264 B，R2-T28 版；本地副本是 R2-T25 版 19,090,636 B，已过期——只用于解析对照，截图一律走 CI）：440 节点；48 套 student-desk（mesh 73 `student-desk_0`，8 行×6 列）+ 48 椅（mesh 74）；桌腿 prim（`leg_metal`，684 三角、1610 顶点）包围盒 x[-0.25,0.246]、y[0,0.67]、z[-0.275,0.275]，管径约 25×30mm，从地面直通桌面底；椅腿同材质（material 7 `leg_metal`，metallic 0.75）——椅腿在所有截图里都清晰落地（椅背两根立柱），同材质同文件，腿“渲染全灭”不成立。
- **③ 探针 A（严格复现 CI 03 机位）**：workflow_dispatch 触发 godot-verify run **#130 / 45469752343**（HEAD `76214f6c`，当前 GLB），success；artifact `godot-screenshots`（12,404,407 B，20 张）已下载。03 图（`scene=classroom&shot=1&hour=10`，机位按 scenes.json 原值 az 1.352/el 0.382/dist 4.96/target [-59.0,0.9,-30.2]，相机 (-54.51,2.75,-29.20)，经 `_enter_instant`→`_snap_to(sc["cam"])`，一字未改）：3 倍放大后每张桌面下均无腿、无篮、无横撑，桌面悬浮薄板状；椅背立柱清晰落地。黑板已墨绿、两块白板已亮白、墙面暖褐（R2-T22/T25/T27/T28 修复均在图内可见）。结论与 R2-T23 一致。
- **④ 探针 B（放低放平：中央走廊机位）**：探针分支 `r2t26-probe-aisle`（基 f9cfc1e0），commit `1298122a` 只改 `data/scenes.json` classroom.cam 一行：az 1.5708/el 0.15/dist 7.03/target [-59.0,0.9,-30.0]，相机 (-52.05,1.95,-30.0)，俯角 21.9°→8.6°，沿中央走廊直视黑板；godot-verify run **#132 / 45472938652** success，20 张已下载。03 新图：黑板居中墨绿、整间教室全入框、双侧窗+顶灯+空调全可见，取景本身很好；但**腿/篮/横撑仍一根不见**。逐点投影核对（FOV 55° 投影模型已用黑板中心+桌心标记验证，落点与实物吻合）：走廊侧桌腿（c3/c4 贴走廊面）在图中的投影位置（r2–r5，x≈520–585/695–760，y≈390–690）5 倍放大后全是空地板；光线追踪盒模型曾预测 122 个可见采样点，实测为 0——2–3cm 级遮挡裕度（椅背/桌面边缘）加 25mm 细管在 720p 下的组合，使“几何上可达”不等于“看得见”。
- **⑤ 探针 C（近景，r1c3 桌 1m）**：同分支 commit `3ee5b816`，cam az -1.5708/el 0.15/dist 3.5/target [-59.18,0.7,-29.2]（相机经 camera_box 钳到西墙 (-60.2,1.22,-29.2)）；run **#133 / 45476952901** success。03 图：前景是讲台教鞭（木杆+黑柄）特写，目标桌腿落在框底之外——取景失误，未能复现 R2-T24 所称“低机位近景腿清晰”；同图 2–4m 远的 r1/r2 排桌面下仍无腿。R2-T24 的近景结论本任务既未证实也未证伪，不作为本次结论依据。
- **⑥ 探针 D（坐姿视高走廊机位，最后一个机位假说）**：同分支 commit `7feb1fa8`，cam az 1.5708/el 0.05/dist 3.5/target [-59.0,0.7,-30.0]，相机 (-55.51,0.88,-30.0)，俯角 2.9°，距目标桌腿 0.5m、视线离遮挡物裕度 0.27m 以上；run **#135 / 45480562230** success，20 张已下载。03 图：黑板墨绿居中、讲台+空调+白板全在；4 倍放大后，0.5m 外桌面下仍无腿、无篮、无横撑——同一框内椅背立柱清晰落地（同材质 leg_metal）。四个机位（俯角 21.9°/8.6°/近景/2.9°视高）全部失败，机位假说穷尽。
- **结论（机位遮挡说不成立——作为唯一解释）**：原 03 高位机位看不见腿是事实，但放低放平（探针 B/D）仍看不见腿；腿在文件里、在 Blender 渲染里（T17 run #91），在 Godot 里从 1–8m、多角度均不出现，而同材质椅腿一直可见。03 机位不是主因，**本次不改 03 机位**（不推一个“看起来修了、实际没修好”的机位）；走廊机位图虽好，但腿仍不可见，不能作为修复交付。探针分支 `r2t26-probe-aisle` 保留作证据（#132/#133/#135）。
- **下一步排查方向（按优先级）**：① Godot 侧运行时探针：在 `tools/verify_fixes.gd` 风格的无头脚本里加载当前 classroom.glb，遍历 `ClassroomGLB` 的 desk 节点，打印每个 `MeshInstance3D` 的 surface 数、AABB、材质与 `visible`，确认 leg_metal 面是否进场景、变换是否正确（重点查 student-desk_0 prim 1 在 Godot 导入后的去向）；② 若导入无问题，在 Blender 侧把腿管加粗（Ø25→Ø40mm）并改浅色重出 GLB 做 A/B 对照，看 Godot 图内是否出现；③ 备选（不推荐）：放宽 classroom limits（camera_box/dist 下限）允许贴桌低机位——会丢黑板与整间，不符合 03 定位；或另增“桌椅特写”入口，需新需求。
- **推仓**：commit c4d14746（c4d14746859110daf99acc9f7f5df538cd575fd1，父 e3213bde，2026-11-25）：只推本文档 1 文件（BLENDER_MODELS.md，326,777 B，blob 1ea9e5ba，+15/-0），不改机位故无 scenes.json 提交、不推模型；推后核对：commit 真建出、父链连续、远端文件与本地逐字节一致、含 §35 全文与 4 个 run 号。
- **验证**：#130/#132/#133/#135 截图均已下载并逐张目视（03 全图 + 3–5 倍放大 + 投影标记叠加核对）；其余 19 张（#130）扫视无回归——黑板/白板/墙面三项修复均在图内，04-charge 三车 SOC 条、11/12 雨晴对照、00/18/19 总览均正常。
- **还剩什么**：① 桌椅腿/篮/横撑 Godot 侧不可见的根因未定位（见下一步①②）；② R2-T24 近景结论未复现；③ 03 机位未动，R2-T23 的①⑤两项仍不通过，待根因定位后由终轮定夺（模型侧加粗/换色，或接受远景只求房间全貌）。

## §36 R2-T35 gym 雨棚下 3 条黄线小修（2026-11-25，只改 ov-gym 一件 + 本节）

- **任务**：R2-T21b 完工时留下的可选小修（见 §21“验证·gym”）：艺体馆南门雨棚下
  有 3 条黄线（tevy 医院楼雨棚部件自带），在预览图里显眼、与雨棚不搭。本任务只改
  `ov-gym.py/.blend/.glb` + 本轮日志 + 本节；不改 gym 量体/位置、不拼总览场景
  （终轮整合的事）、不动 Godot、不动其他件。
- **实测定（GLB/.blend 双回读，不猜）**：3 条黄线是雨棚对象 `ov-gym_canopy_stolen`
  （tevy `entrances` mesh 裁出，世界包围盒 x[-75.25,-64.75] y[47.40,51.90]
  z[0.02,3.80]）的 `yellow_paint` 材质槽，共 **44 面**，全贴地 z=0.056，7 个连通块
  拼成 3 个停车位标线——4 条纵线（x≈-74.83/-71.83/-68.83/-65.83，各 0.09×3.02m，
  y 47.64..50.66）+ 3 条横线（y≈50.64，各 3.07×0.06m）。黄色不是底色：材质底色
  是 (0.8,0.8,0.8) 灰，Mix(MULTIPLY) 的 B 常量 (0.75,0.55,0.04) 经白顶点色相乘
  出黄；源文件 `hospital-building-tevy-plain.glb` 的 `entrances` 里同材质也是 44 面，
  裁切时全数带入。GLB 回读对象数 181。
- **修法与理由（删面，不改色）**：44 面是医院停车场地面漆线、无厚度、无结构作用，
  下方 `ov-gym_ground` 地面完整，删面不留洞；改色会留下 5.6cm 高的凸起色条，
  不如删干净。`ov-gym.py` 在雨棚 `place()` 后加 R2-T35 块：bmesh 按材质名删 44 面
  （assert 44 面，漂移即报错）+ 删孤立顶点 + 去空材质槽；其余面/材质/雨棚几何一字未动。
- **重建（`assets/blender/overview/ov-gym-r2t35.log`，Blender 4.2.0 本地 `-b`）**：
  EXIT=0，零 Error/Traceback；删面 44、空槽 1，雨棚 1692→**1648 面**、2025→**1931 顶点**；
  脚本内 GLB 回读 **181** 对象（与改前一致、只差修掉的线）；独立复核：新 GLB 回读仍
  181 对象、`yellow_paint` 材质已无、雨棚包围盒 x[-75.25,-64.75] y[47.40,51.90]
  z[0.020,3.800] 一字未动，楼体 `ov-gym_floor1` 36×16×8m、屋顶板、地面尺寸位置全未动。
  .blend 6,649,304 B、.glb 6,926,120 B。注意：脚本新出的 .blend（2,638,144 B）把 9 张
  PBR 图留成了外部相对路径，而仓库 HEAD 版（6,687,636 B）是打包进 .blend 的；已用
  `pack_all` 补打包 + 孤儿清理×3（30 材质→7，23 个 tevy 遗留孤儿材质含已无用户的
  yellow_paint 尽除；仓库版第 8 个材质正是 yellow_paint 本身，故 7 是准确数），
  再存盘，.glb 未受此步影响。
- **推仓**：commit `a59137dd`（`a59137dd9fcf62a65e762194149bb3fde204ae01`，父 `cd349d4a`，
  2026-11-24T20:49:48Z）：1 批 push-files，5 个文件一次未超 40MB 单 blob（最大单文件
  .glb 6,926,120 B）；推后核对：HEAD 即 `a59137dd`、父链连续、contents API 逐文件核对
  5 个文件大小与 blob SHA 与本地逐项一致（.py `3f2f6b83…`、.blend `2e9ce834…`、
  .glb `330cfd4d…`、日志 `35b12832…`、本文档 `48e82c37…`）。
- **验证**：blender-previews run **#113** / 45484839169（head `a59137dd`），completed/**success**
  （6/6 组全绿，overview 组约 70 分钟）；artifact `blender-previews-overview`
  （17,944,600 B）20 张已下载。**ov-gym.png 逐张目视通过**：雨棚下地面 3 条黄线已消除
  （全图强黄像素 0/921,600，雨棚区 2 倍放大亦无黄线），雨棚（浅灰混凝土板 + 细柱）与馆体、
  台阶、玻璃正门完好，红砖墙 #8E2F28 + 深灰屋顶 + 3 层蓝玻璃窗带正常，无穿模。其余 19 张
  扫视无回归——无空白/品红/缺件（bldA/bldB、canteen、lab、lib、tower、dorm、track、
  parking 三车、trees 等均正常）。
- **编号说明**：本节即 §36（§35 已是 R2-T26，见协调者提示；写前已查仓库版文档确认
  §36 空闲）；§24/§29 一字未动；只改 gym 一件（`.py` / `.blend` / `.glb` + 本轮日志），
  未拼总览、未动 Godot。

## §37 R2-T36 Godot 侧桌椅腿导入运行时探针（2026-11-25，只诊断、不改模型、不改机位、不改 verify_fixes.gd）

- **任务**：R2-T26 §35 已证伪机位遮挡说（4 个机位 #130/#132/#133/#135 全部看不见腿），按 §35“下一步①”最优先方向做 Godot 侧导入/运行时探针：加载当前 classroom.glb，遍历 ClassroomGLB 的 desk 节点，逐项打印每个 MeshInstance3D 的 surface 数、AABB、材质与 visible，确认 student-desk_0 的 leg_metal 面是否进场景、变换是否正确、材质是否与椅腿相同。只诊断，不动手修。
- **探针对象（推前核对）**：本地 `assets/models/scenes/classroom.glb` 19,091,264 B、md5 `fe4ecb47…`、blob `52d0ac03`（R2-T28 版）；与远端 HEAD `cd349d4a`（探针时）及 `a59137dd`（R2-T35 推后复核）的远端 blob 一致——R2-T35 只动 ov-gym + 本文档，未动 classroom.glb。Godot `4.4.stable.official.4c311cbee`，`~/workspace/tools/godot/`。
- **探针脚本**：`tools/probe_desk_legs.gd`（verify_fixes.gd 风格，`extends SceneTree`，`-s` 无头跑，只加载 classroom.glb 一个文件，不跑全量 `--import`、不跑 Web 导出；退出码恒 0，结论在输出里）。对照真值取自 GLB JSON 直读：desk mesh 73 `student-desk_0` prim0 desk_wood 235v/96t y[0.67,0.70]、prim1 leg_metal 1610v/684t y[0,0.67]；chair mesh 74 `student-chair_0` prim0 chair_wood 466v/192t y[0.398,0.888]、prim1 leg_metal 922v/388t y[0,0.882]；leg_metal 为 opaque、doubleSided、metallicFactor 0.75、无 roughnessFactor、带 baseColor + metallicRoughness + normal 三贴图。跑通前修了脚本自身两处 4.4 API 错：`TRANSPARENCY_ALPHA_PRE_PASS` 在 4.4 不存在、`surface_get_count()` 应为 `get_surface_count()`。
- **方法上的两个实测发现**：① 主工程 `.godot/imported/` 里从未导入过 classroom.glb（18 个文件全是贴图/字体，无 classroom），`ResourceLoader.load("res://assets/models/scenes/classroom.glb")` 在无头 `-s` 下报 `ERROR: No loader found for resource`、返回 null——脚本改走运行时 `GLTFDocument` 直读（与编辑器导入同用 glTF 解析器，无 `.import` 文件即默认设置，只不走贴图转码），先出第一份结果。② 为复核游戏/CI 实际走的编辑器导入路径，另建最小工程 `/tmp/r2t36-import-probe`（只含 classroom.glb 一份 + 同脚本，`project.godot` 渲染段照抄主工程：gl_compatibility、ETC2/ASTC、MSAA 2x），`--headless --import` 只导这一个 GLB 约 40 秒（无头 progress-dialog 报错是编辑器噪音，`.scn` + 40 张 `.ctex` 均已生成），再走 `PackedScene` 路径重跑。两份原始日志随本轮入仓：`tools/probe_desk_legs-r2t36.log`（运行时直读）、`tools/probe_desk_legs-r2t36-import.log`（编辑器导入）。
- **逐项结果（两路径除资源实例 id 外数字一字相同；`load_path=gltfdocument-runtime` / `packedscene-imported`）**：
  - 节点总数：441 节点 / 440 MeshInstance3D（GLB 真值 440 节点，全带 mesh）；desk 48、chair 48。
  - `desk_r1_c1` 全量：visible=true、in_tree=true，pos (-3.180, 0, 2.800)、scale (1,1,1)，mesh 2 surfaces，meshAABB pos(-0.250, 0, -0.300) size(0.500, 0.700, 0.600)，cast_shadow=1、layers=1、vis_range [0,0]、material_override 无。surf0 `desk_wood`：235v/96t/288 索引，法线 235、UV 235，局部 AABB pos(-0.170, 0.670, -0.300) size(0.420, 0.030, 0.600)（仅桌面）。surf1 `leg_metal`：**1610v/684t/2052 索引，法线 1610、UV 1610，局部 AABB pos(-0.250, 0, -0.275) size(0.496, 0.670, 0.551)，即 y[0, 0.67] 从地面直通桌面底**；材质 albedo (1,1,1,1)、a=1.00、metallic 0.75、roughness 1.00、transp DISABLED（不透明）、cull DISABLED（双面）、shading=1，albedo/metal/rough/normal 四贴图全 YES、无自发光、surface override 无。`desk_r8_c6` 同 mesh（共享）、pos (3.820, 0, -2.800)，两面数字与 r1c1 一字相同。
  - `chair_r1_c1` 全量（对照组）：pos (-2.740, 0, 2.800)、scale 1，2 surfaces；surf0 `chair_wood` 466v/192t、局部 AABB y[0.398, 0.888]；surf1 `leg_metal` **922v/388t、局部 AABB y[0, 0.882]**，材质参数与桌腿一字相同，且**与桌腿是同一材质实例**（两路径均 `same_leg_mat=true`）。
  - 48 桌聚合：surf==2 的桌 48/48；leg_metal 面 48/48；desk_wood 与 leg_metal 材质实例各 1 个；共享 mesh 实例 1 个；桌腿全局 AABB y[0.000, 0.670]；桌全局位置 x[-3.18, 3.82]、z[-2.80, 2.80]（与 GLB 真值一致）。48 椅聚合：surf==2 的椅 48/48；leg_metal 面 48/48；共享 mesh 1 个；椅腿全局 AABB y[0.000, 0.882]。
  - 共享网格几何深查（48 套共用同一 mesh，只查一份即覆盖全部）：4 个面退化三角均为 0（桌 wood 0/96、桌 leg 0/684、椅 wood 0/192、椅 leg 0/388）；零长法线均为 0；法线平均模长均为 1.000。
  - 全扫：visible=false 节点 0 个；mesh 为空 0 个；surface 数为 0 的 0 个；任一轴 scale≈0 的 0 个；`desk_r1_c1` 祖先链 `desk_r1_c1 visible=true <- ClassroomGLB visible=true <- root`。另已读 `scripts/classroom_interior.gd` 与 `scripts/glb_loader.gd`：GLB 分支只做 `load_glb` + 挂 `ClassroomGLB` + 加两盏补光，无任何按名隐藏或材质覆盖——独立加载的探针结论可直接代表游戏内 ClassroomGLB 的运行时状态。
  - 两 run 汇总行均为 `PROBE-SUMMARY: 导入/变换/可见性/材质/几何五层全部与 GLB 真值一致，无异常`。
- **根因结论（定位到哪一层）**：**导入层、变换层、可见性层、材质层、几何层五层全部无罪**。腿几何进了场景（48 面、684 三角/面、1610 顶点/面，一个不少）、变换正确（单位缩放、y 从 0 落地、位置与 GLB 一致）、没被隐藏（全链 visible=true）、材质与椅腿同一实例且不透明（不是透明/alpha 0/单面剔除/贴图丢失）、三角形与法线完好（无退化、无零法线）。R2-T23 ①⑤在 Godot 图里看不见腿，**原因不在导入/运行时状态**。本探针无头不光栅化，像素层无法定夺，根因必在渲染侧三者之一：① 光照/材质交互（metallic 0.75 的深灰细管在桌面阴影下过暗）；② 光栅化/分辨率（Ø25–30mm 管在 720p + SwiftShader 下过细）；③ 取景/投影（#135 的 0.5m 近景仍无腿，需先排除腿不在框内）。其中①②与“同材质椅腿可见”并不矛盾：椅背立柱是竖向通长管、迎光面大，桌腿是桌面正下方的短管、又被桌面挡光——同一材质在不同受光/遮挡下表现可以不同，椅腿可见不能反证桌腿应可见。
- **修复建议（按优先级，修复另派任务，本轮不动手）**：① 像素层 A/B 定位（最优先）：用 T24 款最小渲染探针在精确 03 机位渲染单桌近景并逐像素取样桌下区域，对比腿像素与椅腿像素；或把 leg_metal 临时换成亮色非金属材质重出 03 图——腿出现即①（金属暗/光照）问题，仍无即②③（光栅化/取景）问题。② 若确认为细/暗：按 §35 ② 腿管加粗 Ø25→Ø40mm + 改浅色（可并降 metallic 0.75→约 0.2 或补桌下环境光），重出 GLB 做 A/B 对照。③ 复核 #135 取景：把目标腿 3D 坐标投影到 #135 截图上确认腿确在框内（#133 已有取景失误前科，只算 3D 裕度不够），再定夺是否还需更低机位。④ 流程：本地 `.godot` 从未导入 classroom.glb，本地无头跑 `main.tscn` 会静默回退到程序化教室（箱式桌腿，非 GLB 腿），本地复现教室视觉前须先单导 classroom.glb（本任务最小工程约 40 秒）或跑全量 `--import`；CI 不受影响（先 `--import` 再验证）。
- **推仓**：commit `02820e44`（`02820e446bf4b83f89b959cd9010aa93418226fd`，父 `a59137dd`，2026-11-24T20:54:33Z）：1 批 push-files，4 文件（BLENDER_MODELS.md `fdccf998`、tools/probe_desk_legs.gd `df2b1e2d`、tools/probe_desk_legs-r2t36.log `4e2024d2`、tools/probe_desk_legs-r2t36-import.log `b17d0b05`，单 blob 均 <40MB）；推后核对：HEAD 即 `02820e44`、父链连续、contents API 逐文件核对 4 文件大小与 blob SHA 与本地逐项一致、远端文档落盘解码含 §37 全文且 §35/§36 一字未动。注：推前重读 HEAD 为 `a59137dd`；本次推送把远端 §36 仍“待填”的推仓行按本地已填版一并带上（R2-T35 的记录，未改其内容）。
- **验证**：本任务只诊断，无头探针两 run 全量输出在上（运行时直读 + 编辑器导入，两路径逐项一致）；渲染侧根因待下一任务像素层定位后复验。
- **还剩什么**：① R2-T23 的①⑤两项仍不通过，03 机位未动；② 渲染侧根因未定位（见修复建议①）；③ 模型侧加粗/换色（建议②）待根因定位后由终轮定夺。
- **编号说明**：本节即 §37（§35 已是 R2-T26、§36 已是 R2-T35 gym；写前已查仓库版文档确认 §37 空闲；推前重读 HEAD 为 `a59137dd`，其 §36 推仓行本地已填、远端仍“待填”，本次推送会把该行一并带上，见推仓行备注）；§24/§29 一字未动；只加探针脚本 + 两份日志 + 本节，未动模型、未动机位、未改 verify_fixes.gd。

## §38 R2-T37 桌椅腿像素层 A/B 定位（2026-11-25，只诊断、不改模型、不改机位、不改 verify_fixes.gd）

- **任务**：R2-T36 §37 已排除导入/变换/可见性/材质/几何五层，根因必在渲染侧三者之一（① 光照/材质交互、② 光栅化/分辨率、③ 取景/投影）。本任务做像素层定位：用 T24 款最小渲染探针在精确 03 机位渲染单桌近景并逐像素取样桌下区域，A/B 对照亮红腿，复核 #135 取景。只诊断，不动手修。
- **探针对象（推前核对）**：本地 `assets/models/scenes/classroom.glb` 19,091,264 B、md5 `fe4ecb47…`、blob `52d0ac03`（R2-T28 版）；与 #130 HEAD `76214f6c` 的远端 blob 一字相同。Godot `4.4.stable.official.4c311cbee`，`~/workspace/tools/godot/`。探针工程为 T24 最小工程复刻 `~/workspace/review-rework-r2/r2t37/probe/`（classroom.glb 已导入，`.scn` hash `defe388a`，与 #130 CI job-log 里的导入 `.scn` hash 一字相同——见下“CI 导入核对”）。
- **探针脚本**：`tools/probe_pixel_legs.gd`（`extends SceneTree`，xvfb + llvmpipe 原生渲染，1280×720，第 12 帧同步截图，退出码恒 0，结论在输出里）。取样方法：GLB 直读腿柱中心（桌柱 x −0.15/+0.20、z ±0.25，椅柱 x −0.18/+0.14、z ±0.15），每柱 y 0.05–0.62 取 9 点、7×7 窗口取最暗亮度，中位亮度 <90 判暗腿；另用 Godot 自身 `unproject_position` 打印腿点屏坐标（与 Python 投影模型交叉核对）。黑板中心投影 (575.3, 207.4)，与 T24/#130 的 (575, 207) 一致，投影模型已验证。变体：base（T24 同款晴 10:00 光照：太阳 0.95/#fff3d6/−53.3°/−13.5°、天空 #63a9b4、sky/ground energy 0.85/0.65、ambient 0.28、无阴影——经代码核对与 `weather_system.gd` sunny hour=10 逐项同值）、fill（base + R2-T30 两盏室内补光）、blobs（base + weather_system 的 5 个云影 blob，alpha 0 透明圆柱）、fillblobs、red（base + leg_metal 临时改亮红 metallic 0，只改内存材质）、close/closered（单桌近景：desk_r5_c2，相机 1.7m 外）。7 张截图与 7 份日志在 `~/workspace/review-rework-r2/r2t37/shots/` 与 `logs/`，不推仓。
- **逐像素结果（03 机位，同一取样器、同一阈值；“暗”= 柱中位窗口最暗亮度 <90）**：
  - T24 Web 实拍（对照，R2-T25 版 GLB；腿与现版一致，白板色不同是 R2-T28 修复之后）：桌柱 72/74 暗（97%），柱中点 RGB 均值 (52,54,38)；椅柱 59/65 暗（91%），(101,88,60)。
  - **S1 base（原生最小探针，精确 03 机位）**：桌柱 **72/74 暗（97%）**，柱中点 RGB 均值 **(52,54,38)**——与 T24 Web 一字相同；椅柱 59/65 暗（91%）。原生 llvmpipe ≡ Web SwiftShader。举例：desk_r1_c1 post0 屏 (252,446) 腿 RGB (8,21,18) 亮度 17，左右 12px 邻点 (214,217,191)/(44,60,65)；#130 同点为 (181,158,106) 地板色。
  - **S2 red（亮红腿 A/B）**：桌柱 72/74（97%），柱中点 RGB 均值 **(109,47,28)**——R 通道从 52 翻倍，腿确在取样点上；近景 S7 腿点 (168,29,28)/(208,18,8)/(184,13,5)。目视：全部桌腿/椅腿/书篮呈亮红，位置与 S1 暗腿一一对应。
  - **S3 fill（+R2-T30 补光）**：桌柱 72/74（97%），柱中点 (69,63,42)——补光只提亮，不灭腿；椅柱 55/65（85%，4 柱因提亮越过 90 阈值，仍呈暗色）。
  - **S4 blobs（+5 个 alpha 0 云影）**：桌柱 72/74（97%），柱中点 (52,54,38)——与 base 一字相同，云影无影响。
  - **S5 fill+blobs**：同 S3（桌柱 72/74，(69,63,42)）。
  - **S6 单桌近景（desk_r5_c2，距相机 1.1–1.8m）**：4/4 桌柱 + 4/4 椅柱全暗（中位亮度 17–34），腿管粗壮、脚垫与横撑清晰；S7 红腿同点变红。② 在近景尺度下亦不成立。
  - **#130 CI 03（对照，同一取样器）**：桌柱 **5/74 暗（7%）**，柱中点 RGB 均值 **(185,185,162) = 地板**；椅柱 5/65 暗（8%）。黑板左右缘 y=150/200 两图 1px 级一致（(382,537)/(362,763)），取景相同，腿只在 CI 图里缺席。
  - 附：03 机位下离相机最近的 desk_r5_c2 整桌在框底之外（腿点屏 y 1283–1752），但 r1/r3 排在框内且已取样充分，不影响结论。
- **#135 取景复核（3D 投影 → #135 实图取样，投影模型先用黑板中心验证：投影 (640,216)，实物约 (630,220)，吻合）**：距相机 2.05m 的 desk_r3_c3/r3_c4 四柱投影 x 152–1130、y 371–702，全部在框内；视线核对：由相机 (−55.51,0.88,−30) 至柱中点的视线在桌面（y 0.67–0.70）下方通过，不穿桌面、不穿椅背（椅背在 z ±0.19 之外），无遮挡；但柱中段 6 点亮度 170–215，全是地板（仅柱顶/柱脚两端偶有暗点，是桌面底缘与地砖缝，非腿）。2.93m 的 r2 排同。1.36m 的 r4 排（相机两侧）柱投影出框（x<0/>1280，y 至 1432）——§35⑥“距目标桌腿 0.5m”若指 r4 柱，其取景本身出框；但 r2/r3 柱在框内仍无腿，结论不受影响。**③ 取景排除**。
- **CI 导入核对（#130 job-log，run 45469752343，job 138714185662，0 error 行）**：CI `--import` 正常导出 `classroom.glb-defe388a…scn` 及全部 `blue_metal_plate` 贴图 `.ctex`（与本地探针工程的导入 hash 一致）；仅 tevy 草地 6 件因 `KHR_mesh_quantization`/`EXT_meshopt_compression` 不支持而导入失败（室外草，与教室无关）；其余为无头 progress-dialog 噪音。导入侧无 classroom 异常。
- **代码排查（只读，未改）**：`glb_loader.gd`/`classroom_interior.gd` 无按名隐藏、无材质覆盖（§37 已查）；`campus_builder.gd` 的 `set_host_visible` 只动程序化宿主节点（`hosts` 字典），不动 GLB 节点；`labels.gd` 无教室锚点；UI 液态玻璃是 `ColorRect`（2D），不碰 3D 像素；`weather_system.gd` 的云影 blob 已实测无影响。以上均不能解释 CI 图里 leg_metal 两面独缺。
- **根因结论（定位到哪一层）**：**R2-T36 的三假说全部证伪**——① 光照/材质交互：同款晴 10:00 光照下腿亮度约 17、与地板对比约 10:1，补光只提亮，红腿 A/B 定位准确；② 光栅化/分辨率：03 机位腿宽 4–6px、97% 柱可取样，近景 12–30px 全暗；③ 取景/投影：#135 在框内、无遮挡仍无腿。**新定位：差分只剩主场景上下文**——同一 GLB、同一导入（`.scn` hash `defe388a` 两边一致）、同一机位/FOV（黑板 1px 级一致）、同一光照数值、同一渲染器族（GL Compatibility；原生最小 ≡ Web 最小），最小场景腿可见、main.tscn 腿不可见；且消失的是 **leg_metal 两个面**（桌 prim1 + 椅 prim1）——同一 mesh 的 desk_wood/chair_wood 面正常渲染。根因在 **main.tscn 内与 leg_metal 的交互（具体节点待定）**，不在模型、不在机位、不在光照、不在分辨率、不在导入。
- **修复建议（按优先级，修复另派任务，本轮不动手）**：① 不要动腿管加粗/换色（本任务证伪：腿在正确渲染下已足够可见，改模型治标且改错方向）。② CI 侧二分（最优先）：探针分支在 main.tscn 里逐项去掉 overview.glb / labels / UI 后重出 03 图，看腿在哪一步回来；或本地全量 Web 导出对照最小探针——本地最小探针的全部变量均已测完且腿都在，无法再推进。③ 红腿 A/B 可作回归探针：修后先在探针分支把 leg_metal 临时改红出图，红腿出现即渲染通路恢复，再改回深灰出终版。
- **探针工程细节（两处实测教训，后续探针注意）**：① `_process` 里 `await process_frame` 会静默退出：挂起后函数返回的 FunctionState 转 bool 为真，主循环当作退出信号，进程 0 码退出、无任何输出（R2-T37 实测：帧 10 进入 await 后即退出；`tools/capture.gd` 同款写法亦有此坑）。改帧计数第 12 帧同步取根视口纹理。② 红腿变体按 surface 序号选材，共改了 2 个材质实例——leg_metal + cl-windows_glass（mesh 300 `door_geo` 的 surface 1，S2 窗玻璃变红即此；腿结论不受影响，因腿点 RGB 已证实变红）。下次探针应按材质名 `leg_metal` 精确匹配。
- **推仓**：commit `1a59ada7`（`1a59ada781e9384c8d11c7bc26ffd4ae9a39e08c`，父 `1ca56546`，2026-11-24T21:13:54Z）：1 批 push-files，2 文件（BLENDER_MODELS.md `bca12445` 349,000 B、tools/probe_pixel_legs.gd `7381e502` 9,979 B，单 blob 均 <40MB）；推后核对：HEAD 即 `1a59ada7`、父链连续、contents API 逐文件核对大小与 blob SHA 与本地逐项一致、远端文档落盘解码含 §38 全文且 §35/§36/§37 一字未动。
- **还剩什么**：① R2-T23 的①⑤两项仍不通过，03 机位未动；② 根因已收窄到 main.tscn 上下文，具体交互节点待 CI 二分；③ 模型侧加粗/换色不做（已证伪）。
- **编号说明**：本节即 §38（§35 已是 R2-T26、§36 已是 R2-T35、§37 已是 R2-T36；写前已查远端仓库版文档确认 §38 空闲）；§24/§29 一字未动；只加探针脚本 + 本节，未动模型、未动机位、未改 verify_fixes.gd；7 张截图与 7 份日志只放 `~/workspace/review-rework-r2/r2t37/shots/` 与 `logs/`，不推仓。

## §39 R2-T38 main.tscn 内 leg_metal 消失的 CI 侧二分定位（2026-11-25，只诊断、不改模型、不改机位、不改 verify_fixes.gd）

- **任务**：R2-T37 §38 已把根因收窄到 main.tscn 上下文（同一 GLB、同一导入、同一机位/FOV、同一光照、同一渲染器族，最小探针腿可见、main.tscn 腿不可见）。本任务按 §38 修复建议②最优先方向做 CI 侧二分：探针分支在 main.tscn 里逐项去掉 overview.glb / labels / UI，每去一项重出 03 图，看腿在哪一步回来。只诊断，定位到具体节点/层即停。
- **探针分支**：`r2t38-bisect`，基 main HEAD `2ea8340e`（推前重读确认），只推探针分支，绝不动 main（除本文档 §39 一节外）。
- **二分设计（单因素去除 + verify 门控预判，推前已逐项核对）**：三步各只去一项、各自独立（后一步先恢复前一步的改动，不累积），以便归因干净：
  - ① overview.glb 不在 main.tscn 里，是 `campus_builder.gd::_load_scene_glbs` 经 `GlbLoader.attach(self, "overview", "OverviewGLB")` 挂上的。去除法：跳过 attach 一行，但程序化总览件与宿主仍按 GLB 已接管处理（隐藏 + 碰撞禁用，`overview_glb_active=true`），使除 GLB 本体外一切状态与基线一致——`labels.gd` 的深度遮挡射线（mask 1，命中宿主碰撞体）与 verify 口径不变；`overview_glb_active` 全仓只用于 `set_host_visible` 的恢复守卫（另见 452 行），置 true 即基线行为。verify 预判：T2 检查以 `was_loaded("overview")` 分支——GLB 不加载时跳过围栏节点检查、走回退分支查程序化变压器组在 (74,0,−30)（`data/campus.json` transformer pos [74,−30]，已核对），不致假失败。
  - ② labels：`main.tscn` 里 Labels 节点加 `visible = false` 一行（不删节点——`main.gd:46 @onready var labels = $Labels`，删节点会炸启动；`verify_fixes.gd` 的标签检查只读各 Label3D 自身 `.visible` 属性，不读父节点可见性，`visible=false` 不影响判定口径）。已备好未推。
  - ③ UI：`main.tscn` 里 UI（CanvasLayer）节点加 `visible = false` 一行（同理不删节点；verify 只读 UI 子件 `.visible`/布局 rect，面板/ABC 的 `is_visible_in_tree()` 判空时检查按“面板隐藏”直接通过）。已备好未推。
  - 每次 push 即触发一次 godot-verify（push 事件，paths 含 scripts/** 与 scenes/**；不另行 workflow_dispatch，避免双跑）。
- **第 1 步结果（去 overview.glb，腿回来了——即停，第 2/3 步不再跑）**：探针分支 commit `20784914`（`2078491471739d81a83ead335fc0af0bd8f47efe`，父 `2ea8340e`，2026-11-24T21:26:42Z = 2026-11-25 05:26 CST）：只改 `scripts/campus_builder.gd` 1 文件（+10/−7，blob `aa392592`，25,704 B）。godot-verify run **#140 / 45491165835**（head 即 `20784914`，push 触发，2026-11-24T21:26:46Z–21:41:24Z）：**success**；job `138789559148 verify-export success`；**VERIFY-SUMMARY: PASS=268 FAIL=0**（0 error 行；`T2-SKIP: overview.glb 未加载…围栏节点检查跳过` + `PASS: T2（回退）：程序化变压器组在场、位置 (74,0,−30)`，与预判一致）；job-log 另见 classroom.glb 导入为 `classroom.glb-defe388a…scn`，与 #130 的导入 hash 一字相同。artifact `godot-screenshots`（6,764,763 B，20 张）已下载。
- **03 取样（沿用 §38 同款取样器与阈值：GLB 直读腿柱中心，每柱 9 点、7×7 窗口最暗亮度，中位 <90 判暗腿；同一 03 机位，黑板中心投影 (575,207)，与 #130 1px 级一致，机位未动）**：
  - **#140（去 overview.glb）**：桌柱 **53/74 暗（71%）**，柱中点 RGB 均值 **(112,108,93)**；椅柱 **40/65 暗（61%）**，(173,159,134)。对照 #130 基线：桌柱 5/74（7%），(185,185,162) = 地板；椅柱 5/65（8%）。
  - 53/74 不是 72/74 的原因已逐柱核对：21 根非暗柱里 **17 根投影落在右侧场景面板之后**（x≥900、y 60–620，面板白底不可量；#130 里同样 17 根在面板后，两边口径一致），其余 4 根在底缘/底栏区（r3_c2 (346,682)、r3_c3 (466,608)、r4_c4 (974,695)、r4_c5 (1169,655)，框底切边或前景遮挡）。**排除面板后：#140 暗腿 53/57（93%），#130 仅 5/57（9%）**——与最小探针 S1 的 72/74（97%，无面板遮挡）同一量级。
  - **目视**：03 全图 + 2 倍放大裁图逐张看过——每张桌下 4 条黑腿 + 横撑清晰落地，椅腿亦可见，不再是悬浮薄板。00-overview 为探针预期态：无 GLB 且程序化件仍隐藏，只剩 PV/储能/充电三件 GLB 与悬空标签（标签层本身未动，仍在渲染），不可作总览验收；其余 18 张未逐张目视。
- **根因结论（定位到哪一层）**：**致因层就是 overview.glb（总览场景 GLB 本体）**。只去这一项、labels/UI 一字未动，腿即回来：同一 GLB、同一导入、同一机位、同一光照下，main.tscn 里 leg_metal 两面（桌 prim1 + 椅 prim1）的消失由 overview.glb 的存在与否决定。labels/UI 不是必要条件（它们在场时腿已回来），第 2/3 步不再跑。**具体是 overview.glb 内的哪个对象/材质在作怪，尚未定位**（本轮只到 GLB 一层；待终轮在 Blender 里查 overview.glb 在教室体积 (-56,0,−30) 内的几何，或在探针分支把 overview.glb 内对象逐组隐藏出 03 图）。
- **修复建议（按优先级，修复另派任务，本轮不动手）**：① 不要动腿管加粗/换色、不要动机位/光照（§37/§38 已证伪，§39 再证：腿本身渲染正常，是被 overview.glb 抹掉）。② 终轮定位 overview.glb 内交互：先在 Blender 里查 overview.glb 在教室体积内的几何（教学楼 A 壳体/楼板是否伸入教室、y≈0.67 附近有无水平面只盖腿不盖桌面——桌面在腿回来前后一直正常）；再查材质/贴图是否与 leg_metal 共享实例或导入后改写全局状态；或探针分支逐组隐藏 overview.glb 内对象出 03 图。③ 修后回归用红腿 A/B（§38 建议③）+ 本轮取样器复核：暗腿应回 53/74 以上（面板后 17 柱不可量，口径见上）。④ 探针分支的 00-overview 是放空态，修完须在 main 上重跑 godot-verify 复验总览。
- **推仓（探针分支）**：commit `20784914`（`2078491471739d81a83ead335fc0af0bd8f47efe`，父 `2ea8340e`，2026-11-24T21:26:42Z）：1 批 push-files，1 文件（`scripts/campus_builder.gd` `aa392592` 25,704 B，单 blob <40MB）；推后核对：分支 HEAD 即 `20784914`、父链连续、contents API 核对大小与 blob SHA 与本地逐项一致。探针分支的提交留在分支上，不合入 main。第 2/3 步文件（`main.tscn.step2/step3`，各只差一行 `visible = false`）已备好未推，见 `~/workspace/review-rework-r2/r2t38/`。
- **推仓（main 文档）**：commit `2f8cb573`（`2f8cb573d1c13a2b69e2d4f56cccb070dc3e0c76`，父 `f0577e06`，2026-11-24T21:47:27Z）：1 批 push-files，1 文件（BLENDER_MODELS.md `aabcf620` 364,626 B，单 blob <40MB）；推后核对：HEAD 即 `2f8cb573`、父链连续、contents API 核对大小与 blob SHA 与本地逐项一致、远端文档含 §39 全文；§35/§37/§38 一字未动，§36/§32 的补填与 §40 均在（见注）。注：推前重读 HEAD 已是 `f0577e06`（R2-T39 §40，21:47:01Z）而非 `2ea8340e`——并行任务同期写共享本地文件，本次推送读文件时 §40 与 §32/§36 补填已在其中，随本次一并入仓（§40 内容未动）；推后核对远端文档含 §39 + §40 + 两处补填，无内容丢失。本行系推后补填，随第二次推送（仅本文档）入仓；§40 推仓行已由 R2-T39 的 `16d8a4b7` 先行入仓，本次只改本行。
- **验证**：#140 success，VERIFY-SUMMARY 268/0；artifact 20 张已下载，03 全图 + 2 倍放大裁图已目视 + 逐柱取样（数字见上）；00-overview 已扫视（探针预期态）；其余 18 张未逐张目视（第 1 步即停，非终轮验收）。
- **还剩什么**：① overview.glb 内具体哪个对象/材质抹掉 leg_metal 尚未定位（见修复建议②）；② R2-T23 的①⑤两项待终轮修 overview.glb 后在 main 上复验；③ labels/UI 二分未跑（已无必要：腿回来时二者均在场）；④ 探针分支 `r2t38-bisect` 保留作证据（#140）。
- **编号说明**：本节即 §39（§35 已是 R2-T26、§36 已是 R2-T35、§37 已是 R2-T36、§38 已是 R2-T37；写前已查远端仓库版文档确认 §39 空闲，远端文档 350,899 B、blob `b44e06d5` 与本地逐字节一致）；§24/§29 一字未动；探针分支只改 `scripts/campus_builder.gd` 1 文件，本文档只加本节，未动模型、未动机位、未改 verify_fixes.gd；截图、取样脚本与 job 日志只放 `~/workspace/review-rework-r2/r2t38/`（`s140/`、`shots/`、`logs/`、`r2t38_sample.py`），不推仓。

## §40 R2-T39 verify_slim.py 对象数断言参数化（2026-11-25，只改校验脚本 + 本节，不动模型、不动 .glb、不拼总览）

- **任务**：终轮整合已知待办——`verify_slim.py` 里写死的对象数断言 13036 已过时（总览重拼后是 13,217 对象），R2-T1b 重拼时未改共享脚本、用 /tmp 副本绕过，下次重拼会撞同一断言。本任务把期望对象数参数化。注：任务单写的路径 `tools/verify_slim.py` 不存在，实际文件是 `assets/blender/tools/verify_slim.py`。
- **断言位置与含义（改前）**：`assets/blender/tools/verify_slim.py` 第 46 行 `assert n_glb == 13036`（瘦身 GLB 回读对象数）与第 70 行 `assert n_slim == n_full == 13036`（瘦身 .blend 与完整版 .blend 对象数）。13036 是树重建前的旧口径（append 13,032 + 拼装 4）；现总览为 13,217（append 13,213 + 拼装 4，`assets/blender/scenes/overview-refresh-r2t1b-20261124.log` 的 `SCENE objects=13217`）。调用方：无——除文件头用法注释外，没有任何脚本、工作流或文档调用 `verify_slim.py`，它是人工在 Blender 无头下跑的校验脚本（`blender -b --python verify_slim.py`）。
- **参数化方案（未把 13036 简单改成 13217 写死）**：① 默认不写死——期望值取完整版 `overview.blend` 的实测对象数 `n_full`（总览重拼脚本 `assets/blender/scenes/overview.py` 写出该 `.blend`，其 `SCENE objects=` 行即同一数字；瘦身只动贴图、不动几何，三处对象数必须一致，下次重拼改了对象数也不用再改本脚本）。② 可选显式钉死：命令行 `blender -b --python verify_slim.py -- --expected-objects 13217`（注意 `--` 分隔符），或环境变量 `VERIFY_SLIM_EXPECTED_OBJECTS=13217`（命令行优先）；显式值下瘦身 GLB、完整版、瘦身 .blend 三处都要等于它，且在写 `overview-slim.blend` 之前就报错退出。③ 为此把第 1 步的对象数断言后移至第 2 步（`n_full` 已知后）统一断言，第 1 步只保留 `no_material_prims == 0`；新增 `EXPECTED objects=N source=full-blend|--expected-objects|VERIFY_SLIM_EXPECTED_OBJECTS` 一行输出。④ 13036 在文件里只剩一处——文件头注释里的历史说明（“原写死 13036 是树重建前的旧口径”，另注当前实测期望值 13217 仅作注释参考，不参与断言）；`grep 13036` 全仓除旧日志与旧章节外，正文只剩这一行注释。
- **本地验证（Blender 4.2.0，`~/workspace/tools/blender/blender-4.2.0-linux-x64/blender`，三 run 全在 `~/workspace/review-rework-r2/r2t39/`）**：验证输入的瘦身 GLB 是从仓库现取的远端 `assets/models/scenes/overview.glb`（37,024,624 B，blob `8791a4b8`，即 R2-T1b 瘦身版；GLB JSON 直读 nodes 13,217 / meshes 4,623 / images 325，与 R2-T1b 日志一致；本地 `assets/models/scenes/overview-slim.glb` 与远端均不存在，验证用下载副本、跑完已删）。完整版输入是本地 `overview.blend` 68,983,428 B 与 `overview.glb` 102,553,484 B（均与 R2-T1b 日志尺寸一致，仓库里这两处是瘦身版，完整版只留本地）。① 默认 run（`verify-default-20261125.log`，exit 0）：瘦身 GLB 13,217 对象 / 13,213 mesh / 0 无材质 primitive；完整版 13,217 对象；`EXPECTED objects=13217 source=full-blend`；瘦身 `.blend` 11,929,387 B、13,217 对象 / 446 贴图 / 缺失 0；`DONE verify_slim`。② 环境变量钉死 run（`VERIFY_SLIM_EXPECTED_OBJECTS=13217`，`verify-env-pin-20261125.log`，exit 0）：`EXPECTED objects=13217 source=VERIFY_SLIM_EXPECTED_OBJECTS`，三处 13,217 全绿，瘦身 `.blend` 11,929,340 B（与①差 47 B，系 Blender 保存布局非确定性，对象数相同）。③ 命令行钉死旧值反测（`-- --expected-objects 13036`，`verify-cli-stale-20261125.log`）：`AssertionError: slim GLB objects 13217 != expected 13036 (--expected-objects)`，且 `overview-slim.blend` 未写出——旧值如今会明确报错，不再静默通过。另交叉核对：本地完整版 `overview.glb` 的 GLB JSON 直读 nodes 也是 13,217，与 Blender 回读一致。
- **实测发现（Blender 退出码，旧脚本亦然，非本次引入）**：Blender 4.2.0 无头跑 `--python` 时，脚本里 `assert` 失败只打 Traceback、`Blender quit`，进程退出码仍是 0；另实测 `sys.exit(3)` 与自定义 `sys.excepthook` 也都被吞掉、退出码仍 0（探针 `/tmp/r2t39-exit-probe.py`、`/tmp/r2t39-hook-probe.py`）。因此判断 `verify_slim.py` 成败**不能只看退出码**，须以日志里有 `DONE verify_slim` 且无 Traceback 为准；失败时 `overview-slim.blend` 不写出（③已证实）。本次未改退出码通路（唯一能生效的改法是把全部断言改写成 `os._exit(1)`，超出“最小改法”范围，留给终轮定夺）。
- **临时文件（已清）**：验证用的 `assets/models/scenes/overview-slim.glb`（下载的远端瘦身版副本，37,024,624 B，blob `8791a4b8` 与远端逐字节一致）与两次生成的 `assets/blender/scenes/overview-slim.blend`（11,929,387 / 11,929,340 B）跑完已删，本地树恢复原状；完整版 `.blend`/`.glb` 一字未动，总览未重拼。
- **推仓**：commit `f0577e06`（`f0577e065802677d435072144f3ce318e5f7c370`，父 `5217a62f`，2026-11-24T21:47:01Z）：1 批 push-files，2 文件（`assets/blender/tools/verify_slim.py` blob `9fdb5f1c` 5,607 B、BLENDER_MODELS.md blob `aabcf620` 364,626 B，单 blob 均 <40MB）；推后核对：HEAD 即 `f0577e06`、父链连续、contents API 逐文件核对大小与 blob SHA 与本地逐项一致、远端 `verify_slim.py` 落盘含参数化代码且无写死断言、远端文档含 §40 全文。只改校验脚本 + 文档，未触发须等的工作流 run。本行系推后补填，随第二次推送（仅本文档）入仓。另：§39 文本系 R2-T38 同期写入共享本地文件、在本次推送读文件时已在其中，随 `f0577e06` 一并入仓（§39 内容本身未动）；随后 R2-T38 的 `2f8cb573` 提交为其后 HEAD，文档 blob 未变。
- **编号说明**：本节即 §40（§39 已派给 R2-T38；写前已查远端仓库版文档确认 §39/§40 均空闲）；§24/§29/§33 一字未动；只改 `assets/blender/tools/verify_slim.py` + 本节，未动模型、未动 `.glb`、未拼总览。

## §43 R2-T42 路 vs 跑道几何 415 对面片相交处理（2026-11-25，只复现、判可见性与记录，不动几何、不重建、不推模型）

- **任务**：R2-T33 §33“还剩什么”①：路 vs 跑道几何 BVH 面片相交 415 对未修。本任务只处理这一处：复现、判 #112 图上是否可见、可见则最小修、不可见则接受并记录。约束：**不许动路**（§33 已证实东移不可行）、**不许动树**（R-N2-T 西列 5 棵树压环面是 ov-trees 件，留终轮整合）。
- **复现（Blender 4.2.0，`~/workspace/.tools/blender-4.2.0-linux-x64/blender`，本地 `assets/models/` 两件 GLB；与远端 HEAD `72dfcae9` 的 blob 逐项一致：ov-track.glb `fd5c6e6e`、ov-road-walk.glb `4eb45308`）**：
  - 世界坐标系 BVH `overlap()`：**415 对，与 §33 分项一字不差**（铺装 vs 环 51、vs 外缘路缘石 126、vs 外分道线 33、vs 起跑线 5；西路缘 vs 环 56、vs 外缘路缘石 132、vs 外分道线 8、vs 起跑线 4；东路缘 0 对；1–3 号分道线与内缘线 0 对）。口径注：`BVHTree.FromObject` 建的是对象局部坐标 BVH，初试只得 60 对且全是起跑线（误报）；必须用 `BVHTree.FromPolygons` + `matrix_world` 后的世界坐标顶点才复现 415。
  - 位置：交叠带集中在跑道东尖，解析几何复核（外椭圆中心 (-62,-25)、rx28/ry40；路缘石外椭圆 rx28.3/ry40.3）：环 0.5m 宽 × y -32.53..-17.47（15.05m）、路缘石 0.8m 宽 × y -34.51..-15.49（19.03m），与 §33 一致；+3m 缓冲内路全宽段 y -32.69..-17.31（15.38m）。
  - 高度：路缘石顶 z=0.15，高出铺装顶（z=0.10）0.05m；**环顶 z=0.10 与铺装顶 z=0.10 严格共面**；外分道线/起跑线 z 0.10..0.12（高出铺装 0.02m）。
- **可视性（#112，run 45483359861，`~/workspace/review-rework-r2/r2t33-112/`）**：**两张图均不可见**——blender-previews 是单件渲染，ov-track.png 只有跑道、ov-road-walk.png 只有路，对侧几何根本不在图里；东尖 3 倍放大裁图（ov-track.png）与 R-N2 放大裁图（ov-road-walk.png）均干净，无闪烁/穿插/黑线。按任务单 step 3，本应至此完工；但单件图结构上看不见跨件相交，为免接受结论立不住，另做本地合渲探针。
- **合渲探针（本地，两件 GLB 同场景，Cycles CPU——本机无 libEGL，Eevee 跑不起来；太阳光 + 浅绿 world，证据在 `~/workspace/review-rework-r2/r2t42/`）**：
  - 40m 正顶合渲（`combined-top.png`，0.03125m/px）：交叠带可见一条近黑带——环顶与铺装顶共面透镜区（y -32.5..-17.5 一带，宽约 0.4m）渲染为黑：像素取样（y=-21.56 行）世界 x -34.41..-34.25 处 RGB 0–1、x -34.56 处暗红 26–40，而正常环面 170–174；起跑线与分道线交叉处另有约 0.1m 黑点（两白线 z 0.10..0.12 共面）。
  - 130m 斜视总览视角（`diag-oblique.png`，相机 (40,-110,75) 望向 (-33,-25,0)）：黑带收为一条细黑缝，路带斜压过跑道东尖，起跑线白线在路缘处截断；远看不刺眼，但缝真实存在。
  - 定因诊断（`diag-nocurb-top.png`）：藏起 `track_curb_outer` 重渲，黑带像素逐点与全量图相同——**黑带是环/铺装共面透镜所致，与路缘石无关**。
- **结论：接受、不修（已知问题，留终轮定夺）**：
  - 任务单 step 4 的修法（跑道外缘路缘石局部修形/顶高修整）**修不掉这条黑带**：它最多清 258 对路缘石相交，环/铺装 107 对共面透镜与黑带原样保留；要清黑带须把环东尖切回路西缘（x≤-34.5）或动路——前者改跑道定义轮廓（东尖 15m 一段削平，ov-track.png 即见，且分道线/起跑线穿路仍在）、后者 §33 已证实不可行且本任务禁动。做一次修不掉问题的重建没有意义。
  - 因此**零几何改动、零重建、零模型推送**；415 对相交与合渲黑带作为已知问题留终轮整合定夺（终轮拥有总览重拼 + Godot 验收，在合景里判这条缝是接受、切环尖还是另议）。R-N2-T 西列 5 棵树压环面（§33②）同样未动。另注：`ov-road-walk.py:409-410` 旧注释（-37 尖、2.5m）仍是 §33③ 的遗留，未动。
- **推仓**：commit `153529f4`（`153529f46377e1f2961cde3efc61a6e3555027b7`，父 `72dfcae9`，2026-11-24T22:07:10Z）：1 批 push-files，1 文件（BLENDER_MODELS.md blob `20dadfa3` 372,595 B，单 blob <40MB）；推后核对：HEAD 即 `153529f4`、父链连续、contents API 核对大小与 blob SHA 与本地一致、远端文档含 §43 全文与 §40。只推文档，未触发须等的工作流 run。本行系推后补填，随第二次推送（仅本文档）入仓。
- **编号说明**：本节即 §43（§41 已派给 R2-T40、§42 已派给 R2-T41；写前已查远端仓库版文档确认 §41/§42 尚未入仓、§43 空闲，远端文档 blob `4329fea9` 与本地逐字节一致）；§24/§29/§33 一字未动；未动模型、未动 `.glb`、未拼总览；复现与合渲脚本、像素取样所用渲染图与 #112 放大裁图只放 `~/workspace/review-rework-r2/r2t42/`，不推仓。

## §44 R2-T43 R-N2-T 西列 5 棵树移出新跑道环面（2026-11-25，只改 ov-trees 一件 + 本节）

- **背景**：R2-T33 §33“还剩什么”②：R-N2-T 西列 5 棵树压在新跑道环面上（x=-38，y=-40/-32/-16/-8/0），东列 7 棵在 +3m 缓冲内但不在环面上、本次不动。本任务只移这 5 棵，y 不变优先，其余 468 棵一字不动。
- **定位（Blender 4.2.0，`assets/models/` GLB 回读 + 网格 ray-cast，非解析几何推测）**：改前 `ov-trees.glb` 回读 **473** 棵；西列 11 棵（x=-38，y -72..16，缺 y=-24）中 5 棵为 `Tree_285_tree_plateau` (-38.00,-40.00，高 5.70m)、`Tree_286_tree_default` (-38.00,-32.00，高 6.10m)、`Tree_287_tree_default` (-38.00,-16.00，高 6.00m)、`Tree_288_tree_pineDefaultB` (-38.00,-8.00，高 6.40m)、`Tree_289_tree_default` (-38.00,0.00，高 5.80m)，均为 R-N2-T 区新种树（`green_layout.json` 原坐标）。环面实测（`track_ring` 东西向 ray-cast，命中 x 即环壁）：y=-40 环带 [-44.33,-36.05]、y=-32 [-42.49,-34.44]、y=-16 [-42.81,-34.73]、y=-8 [-45.06,-36.66]，四棵树干确在环面内；**y=0 一棵不在环面上**：该处环带 [-49.52,-40.15]，树在环外缘以东 2.15m（外椭圆归一化半径 r²=1.125），§33“5 棵均在环面内”对这一棵不成立——它在 +3m 缓冲内（缓冲东界 -37.80，树在 -38.00），按任务书 5 棵仍全移（见修法末条）。
- **移向选择（两边实测后定，非先定后证；树干半径实测 0.42–0.49m——GLB 回读 z<1m 顶点最大水平距；冠底 1.89–2.86m，高于看台顶 1.2m，冠层悬挑不碰件；以下净空均为树干边到件面的距离）**：
  - **向东不可行（y=-40/-32/-16/-8 四棵）**：y=-32/-16 处外缘路缘石东缘（网格 ray-cast：-34.14/-34.42）已在 R-N2 路廊西缘（`curb_RN2_west` x[-34.65,-34.50]）以东，**零间隙**——出环即进路廊；y=-40 东侧间隙仅 1.09m（外缘路缘石 -35.74 至路廊 -34.65），树干半径 0.42m，只剩 0.03m；y=-8 东侧有 `Shrub_01`（x[-35.50,-34.50] y[-7.50,-6.50]），东移只剩 0.06m。东移要么进路廊、要么零净空，均否决。
  - **向西可行（y=-40/-32/-16/-8 四棵）**：西侧是内缘路缘石与球场/看台之间的草地槽。内缘路缘石内壁（网格 ray-cast）：y=-40 -44.65、y=-32 -42.79、y=-16 -43.11、y=-8 -45.38；球场东缘 -47.00（东线 -47.08..-46.92，`field_line_east`）、看台三级台阶东缘 -44.10（`stand_step_3` x[-44.90,-44.10]，y[-37,-13]，顶高 1.20m）。
  - **y=0 一棵向东**：向西须过内缘路缘石 -49.90，落到球场东缘 -47 以西的球场条带上，不可行；向东 -36.00：外缘路缘石 -39.81，净空 3.34m；R-N2 西路缘 -34.65，净空 0.88m；亦出 +3m 缓冲（缓冲东界 -37.80）。
- **新位（y 不变，唯 T287 例外）**：
  - `Tree_285` (-38.00,-40.00) → **(-45.80,-40.00)** 西 7.80m：内缘路缘石净空 0.73m，球场东线净空 0.70m（y=-40 在看台 y 段 [-37,-13] 之外，西槽 2.35m 宽）。
  - `Tree_286` (-38.00,-32.00) → **(-43.44,-32.00)** 西 5.44m：内缘路缘石 -42.79 / 看台 step_3 东缘 -44.10，净空各约 **0.16m（紧，实测无接触，树干边到件面；见“还剩什么”②）**。
  - `Tree_287` (-38.00,-16.00) → **(-45.50,-12.00)** 西 7.50m + **y 北移 4m**：y=-16 处西槽（内缘路缘石 -43.11 至看台 -44.10）仅 0.99m 宽，树干直径 0.96m，只剩 0.03m，y 不变不可行；y=-12 已出看台 y 段，西槽（内缘路缘石 -44.04 至球场东缘 -47.00）2.93m 宽，净空各约 0.98m；距新位 T288 4.05m（≥2.60m 目标），看台角点净空 0.69m。
  - `Tree_288` (-38.00,-8.00) → **(-46.16,-8.00)** 西 8.16m：内缘路缘石净空 0.34m，球场东线净空 0.32m，`Shrub_00`（x[-45.50,-44.50] y[-7.50,-6.50]）净空 0.39m。
  - `Tree_289` (-38.00,0.00) → **(-36.00,0.00)** 东 2.00m：见上条；立于 `Lawn_TeachSouth` 草坪板上（平地 z 0.05，树本就立于草坪板）。
  - 其余约束复核：新位与 R-N2 路廊（x[-34.65,-31.35]）最近 0.88m（T289，树干边）；与草地色带 `Slab_G2_053`（西缘 -31.0）最近 4.47m；不越校园边界（最西 -46.16，距西沿线 -120 约 74m）；新位 2m 内无其他树（最近邻见重建段）。
- **并行耦合（R2-T42）**：本任务开工时 HEAD 为 `72dfcae9`；施工期间 R2-T42 落地（commit `153529f4`，§43），**零几何改动**——推前重读 HEAD 已是 `d7a2c8d3`，远端 tree 核对 `ov-track.glb` 仍为 `fd5c6e6e`、`ov-road-walk.glb` 仍为 `4eb45308`、`ov-field.glb` 仍为 `ee2bb9bf`、`ov-lawn.glb` 仍为 `8ed78367`，与 `72dfcae9` 一字相同；本地 `assets/models/` 四件 GLB 的 blob 与远端逐项一致，环面几何即定稿几何，本节新位按定稿环面所定，无须返工。R2-T42 接受的 415 对路/跑道相交与合渲黑带未动（环东尖几何一字未动）。
- **实现（`ov-trees.py` 升 v5，只加 `R43_RELOC` 映射 + 新种循环里一条 remap 分支 + 计数断言；`green_layout.json` 原坐标一字未动，照 R2-T32 款式——设计源不动、修位置于脚本）**：键为布局原坐标、值为新位；`plant()` 调用顺序、随机数消费、模型/高度档一字不改；断言 `n_r43 == 5`。文件头已同步记录 y=0 复核结论与 T287 移 y 原因。
- **重建（`assets/blender/overview/ov-trees-r2t43.log`，Blender 4.2.0 本地 `-b`）**：EXIT=0，日志零 Error/Traceback；RELOC 共 45 条（R2-T43 5 + L1/R2-T32 40，一字未变）；新种 327 + 旧树换模 146 = **473 棵**，三角面 **120,634**（与 v4 一字相同，≤300k 预算），GLB 回读 **473** 棵树对象；`.blend` 6,005,372 B（与 v4 同体积，4 张贴图全打包，474 对象/20 mesh）、`.glb` 3,546,964 B（v4 3,546,916 B，+48 B，仅 5 棵坐标浮点变化）。
- **重建回读（独立复核脚本，新 GLB vs 远端 v4 GLB `5a608d5d` 全量逐棵比对，非脚本自带回读）**：位置/高度差异**恰好 5 棵**，即上表 5 棵、仅坐标变、高度一字不变（5.70/6.10/6.00/6.40/5.80m），其余 468 棵逐值相同；5 棵新位 ray-cast 复核**全部出环面**（`in_band=False`），树干边到路缘石净空 0.73/0.16/0.98/0.34/3.34m；新位最近邻 8.34/8.34/4.05/4.05/8.00m（目标 2.60m，下限 2.0m）；全量两两间距复核：<2.0m 对改前改后均为 **0 对**，<2.6m 对均为 **21 对、无新增无减少**（与 R2-T32 的 21 对同一集合，含 3 对 2.60m 密植带对）。
- **推仓**：commit `f573508d`（`f573508d46f1a384ace1f3b21a047a6e48ddaab5`，父 `d7a2c8d3`，2026-11-24T22:12:59Z）：1 批 push-files，5 文件（ov-trees.py `b0b94584` 24,524 B、ov-trees.blend `23e8bb9e` 6,005,372 B、ov-trees.glb `0ed3fac6` 3,546,964 B、ov-trees-r2t43.log `6915af8e` 16,288 B、BLENDER_MODELS.md `89d91004` 380,973 B，单 blob 均 <40MB）；推后核对：HEAD 即 `f573508d`、父链连续、递归 tree 逐文件核对 5 文件大小与 blob SHA 与本地逐项一致。注：推前重读 HEAD 为 `d7a2c8d3`（R2-T42 §43，22:07Z），施工期间 R2-T42 落地、环面几何未变（见“并行耦合”）。本行系推后补填，随第二次推送（仅本文档）入仓。
- **验证**：blender-previews run **#115**（45498809396，head `f573508d`，2026-11-24T22:13:04Z 起跑、23:22:34Z 完成，约 69 分钟）：completed **success**，6/6 job 全绿（classroom/pv/dist/charge/overview/storage）。artifact `blender-previews-overview`（17,942,593 B）已下载，20 张 PNG 全量品红扫描（R>150、G<140、B>150）**全部 0 像素**；逐张目视：**ov-trees.png 通过**——473 棵全在位、绿冠完整无品红无缺失；与 #112 基线逐像素比对仅 590 像素变化（0.0640%），全在 x[460,566] y[331,381] 一个框内（即移位的 5 棵树所在处），3 倍放大裁图前后对照树木完好、无新遮挡；**ov-track.png 通过**——红环 + 白分道线 + 起跑线完整，与 #112 逐像素一字相同（跑道未动）；其余 18 张扫视无回归——17 张与 #112 逐像素一字相同，ov-gym.png 与 #113 逐像素一字相同（其与 #112 的 539 像素差即 R2-T35 雨棚黄线消除，已在 §36 验收；雨棚下无黄线）；road-walk 步道网、field 球场/球门/看台、lawn 色带、bldA/bldB 玻璃幕墙、canteen/gym/lab 红砖、dorm 双栋、tower、transformer、windows-roofs 均正常。结论：5 棵树已出环面、无新压线、无回归。（注：本行原为协调者 06:44 CST 填的中期注记“run 进行中、结论预计 07:10–07:25 CST”，现按实测结论改写；run 实际 07:22 CST 完成，在预计窗内。）
- **还剩什么**：① R2-T42 接受的路 vs 跑道 415 对相交与合渲黑带仍在（环东尖未动），留终轮整合定夺（§43）；② `Tree_286` 新位 (-43.44,-32.00) 树干边到内缘路缘石与看台 step_3 各仅约 0.16m——实测无接触、渲染图上约 1–2px，终轮若重排看台东缘或内缘路缘石（>0.16m）须复核此棵；③ 西列 4 棵新位仍在 +3m 缓冲内（内侧，与东列 7 棵先例一致：缓冲内、环面外，见 §33），`Tree_289` 已出缓冲；④ `green_layout.json` R-N2-T 区仍列 5 棵旧坐标（设计源未动，修位置于 `ov-trees.py` 的 `R43_RELOC`，照 R2-T32 款式）；⑤ 总览重拼 + Godot 侧验收由终轮整合做（本次只改 ov-trees 一件，未拼总览、未动 Godot）。
- **编号说明**：本节即 §44（§41 已派给 R2-T40、§42 已派给 R2-T41、§43 已是 R2-T42；写前已查远端 HEAD `d7a2c8d3` 的仓库版文档确认 §41/§42 尚未入仓、§44 空闲，远端文档 blob `e151cc38` 与本地逐字节一致）；§24/§29/§33 一字未动；只改 ov-trees 一件（`.py` / `.blend` / `.glb` + 本轮日志）+ 本节，未拼总览、未动 Godot。

## §45 R2-T44 教室南墙西端窄条偏暗复测与定夺（2026-11-25，只诊断、不改模型、不改灯光）

- **任务**：复测 §30 遗留①（南墙西端窄条仍暗约 (73,69,54)，目标暖褐约 (97,88,68)，留终轮定夺），二选一：接受留档，或需修并给最小修复方案（只给方案、不实施）。
- **定位（§30 口径复核）**：窄条 = 南墙西端、西数第一扇窗（最西窗）的窗下墙。03 图里它是左缘一条斜向暗带，从 (0,430–480) 到 (135,345–395)，东端贴相机侧、西端顶到空调柜角（空调遮住其西端以外墙面）；取样口径与 §30 同款：沿带中线 7×7 窗口多点取中位 + 整带分段中位。§30 的 (73,69,54) 在本次复测里对位在窄条西段平台 (72,70,58)，差 1–4，确为同一位置、同一块墙。
- **复测（godot-verify #139，run 45488975086，head `1a59ada7`，completed success；main 上最新一次 godot-verify run；其 03-classroom.png md5 `e581a4a78d39d08f6ab6db95931d7d4d`，与 R2-T30 的 #134 run 45477898696 同图逐字节相同，复测值双 run 一致）**：
  - 中线 E→W（7×7 窗口中位）：(15,455) (92,77,61)；(30,445) (87,75,60)；(45,435) (83,74,59)；(60,415) (79,72,59)；(75,405) (75,71,58)；(90,395) (72,70,58)；(105,385) (71,70,58)；(120,372) (72,70,58)；(130,360) (72,70,58)；(133,352) (71,70,57)。
  - 分段中位：东段 x0–45 **(90,76,61)**；中段 x46–90 **(77,72,58)**；西段 x91–140 **(72,70,58)**；整带 **(78,72,59)**。沿带自东向西单调变暗，西段成平台，与 §30 的 (73,69,54) 一字未变（±1–4）。
  - 与目标 (97,88,68) 对比：东段 -7/-12/-7；中段 -20/-16/-10；西段 **-25/-18/-10**；整带 -19/-16/-9。
  - 对照（同图复核）：西墙 (96,86,67)（§30 已达标，本次同区复核 (96,87,67)，一字未变）；南墙窗间墙 §30 改后 (129,118,101)/(120,114,101)——03 取景内只见最西一扇窗，窗间墙不在图内，本次未重测，以 §30 探针值为准。窄条西段比已达标西墙暗 24（R），比窗间墙暗约 50（R）。
- **目视（正常观看距离，全图 1280×720）**：左缘窗下暗带可见——暗褐斜带，与亮地板（约 210）与暖褐西墙（96,86,67）都有可见亮度台阶；不是画面第一眼焦点（黑板/桌椅居中），但看左缘时明显偏暗；3 倍放大裁图（`~/workspace/review-rework-r2/r2t44/crop139_left.png`）暗带边界清晰。20 张中仅 03 见窄条（08-narrow 为总览窄屏图，无教室内容）；其余 19 张本次未逐张复核（只诊断 03）。
- **定夺：需修（不接受）**：① 西段 (72,70,58) 距目标 -25/-18/-10，超出可接受范围（已达标西墙距目标仅 1–2）；② 与 §30 残留值 (73,69,54) 差 1–4，即 T30 补光没修到这一段（窗间墙 65→129，窄条西段 73→72，未动）；③ 目视有可见亮度台阶。东段 (90,76,61) 虽近目标，但整带中位 (78,72,59) 仍 -19/-16/-9，不能只取东段说达标。
- **最小修复方案（终轮执行，本轮不实施；只加一盏灯，不动室外灯光、不改模型、不改 .glb）**：
  - 第三盏 SpotLight3D，加进 `scripts/classroom_interior.gd` 的 `_add_fill_light()`（GLB 回退分支同加，照 §30 款式；只改该函数）。
  - 位置（Godot 局部坐标，房间中心原点）：**(-2.2, 1.8, +1.0)**（西偏 2.2m、南偏 1.0m、高 1.8m，与现有两盏同高）。
  - 朝向：指局部点 **(-3.8, 0.7, +3.6)**（窄条西段中心：南墙面 z=+3.63，窗下高约 0.7m）；用 `rotation` 定向，不用 `look_at`（§30 教训：内景全局位移 (-56,0,-30) 下 `look_at` 的全局目标点会指错方向）。
  - 参数：色 **#ffe0b3**（同现有两盏暖色）、能量 **1.0** 起（探针扫 0.8/1.0/1.2，照 T30 候选 sweep 款式）、锥角 **50°**（窄锥，只罩窄条约 1.5m 宽；现有两盏 120°）、spot_range 4m、衰减 1.0、无阴影。
  - 为什么不吹亮邻居：锥轴指向西南下方窄条；东侧窗间墙在锥外（与锥轴夹角约 37° > 半角 25°）；北墙窗间墙与天花板中央在锥轴反向/锥外；西墙南缘最多吃锥边 +5–10（现 (96,86,67)，仍 ≤~105）；锥内窗玻璃下缘不吃灯光（§30 ③）；地板已 190+，+10 不可见。
  - 验收口径（探针先验、CI 复验）：窄条西段 → 90–100（R，目标 97,88,68）；整带中位 R ≥85；南墙窗间墙 ≤135（R，现 129/120）；天花板中央 ≤145；西墙 ≤105；北墙窗间墙变化 ±5 内。探针不达标就调能量/锥角/位置三选一重扫。
  - 明确不许：**不许抬现有两盏 Spot 能量**（§30 已证：窗间墙已 129、天花板中央已亮，先吹亮它们；窄条西段是掠射角 + 锥角边缘，能量到不了）；不动室外灯光、不改模型、不改 .glb。
  - 备选：若探针证实窄锥仍 spill 到窗间墙/天花板（能量 0.8 仍超验收口径），则改接受（留档为已知问题），不再追加第四盏。
- **附带发现（只记一行，不扩范围）**：窗上沿顶带西端在 03 图左上（x 0–100, y 80–130）同为 (72,70,58)，与窄条同因（锥角边缘 + 掠射角）；§30 顶带 (114,103,70) 是中墙取样，西端未报；本次不管，留终轮注记。§30 遗留②天花板四角仍略暗本次未重测。
- **推仓**：commit `ad588cd3`（`ad588cd3b97ed59ec65f556bf898a6af40244ef4`，父 `f573508d`，2026-11-24T22:17:47Z）：1 批 push-files，1 文件（BLENDER_MODELS.md blob `c93e0159` 386,771 B，单 blob <40MB）；推后核对：HEAD 即 `ad588cd3`、父链连续、contents API 核对大小与 blob SHA 与本地逐项一致、远端文档含 §45 全文且 §44 一字未动。只推文档，未触发须等的工作流 run（本次未改任何 Godot/模型文件；§44 随 R2-T43 的 `f573508d` 已先行入仓，本次推送读文件时远端文档 blob 与本地推前版逐字节一致，未撞车）。本行系推后补填，随第二次推送（仅本文档）入仓。
- **编号说明**：本节即 §45（§41 已派给 R2-T40、§42 已派给 R2-T41、§43 已是 R2-T42、§44 已是 R2-T43，已随 commit `f573508d` 入仓；本次只加 §45）；§24/§29/§33 一字未动；只加本节，未动模型、未动灯光、未动 .glb；取样裁图与两份 artifact 只放 `~/workspace/review-rework-r2/r2t44/`，不推仓。

## §46 R2-T45 verify_slim.py 断言失败退出码修复（2026-11-25，只改校验脚本 + 本节，不动模型、不动 .glb、不拼总览）

- **任务**：§40 留给终轮定夺的实测发现——Blender 4.2.0 无头跑 `--python` 时，断言失败只打 Traceback、进程退出码仍是 0；`sys.exit(3)` 与自定义 `sys.excepthook` 也都被吞掉，终轮 CI 没法靠退出码判 `verify_slim.py` 成败。本任务实施 §40 指出的唯一生效改法：全部断言改写成 `os._exit(1)`。
- **改法（最小改法，只动 `assets/blender/tools/verify_slim.py`）**：① 新增 `_fail(msg)`：先 `print("VERIFY-FAIL " + msg, flush=True)` 再 `sys.stdout.flush()`，最后 `os._exit(1)`（先 flush 再 `_exit`，失败行才不会丢在缓冲里；`os._exit` 跳过清理——本脚本是无头校验脚本，无需保存中间状态）。② 5 处 `assert` 全改成 `if` + `_fail`，失败文案与原 `assert` 消息一字相同（瘦身 GLB 无材质 primitive、瘦身 GLB 对象数、完整版对象数、瘦身 .blend 对象数、缺失文件），断言口径与期望值来源一字未动（默认取完整版 `overview.blend` 实测 `n_full`，可选 `--expected-objects` / `VERIFY_SLIM_EXPECTED_OBJECTS` 钉死）。③ 附带：`--expected-objects` / 环境变量的 `int()` 解析包进 `_parse_expected`，非整数值同样走 `_fail`（原 `ValueError` 也会被吞成 exit 0，同属一类漏报）。④ 文件头补一段退出码说明（R2-T45）；脚本里不再有任何 `assert` 语句（`grep assert` 只剩注释与 `_fail` 文档字符串里的提及）；成功仍打印 `DONE verify_slim` 后正常退出 0。文件 5,607 B → 6,809 B，`python3 -m py_compile` 通过（生成的 `__pycache__/*.pyc` 已删）。
- **本地验证（Blender 4.2.0，`~/workspace/tools/blender/blender-4.2.0-linux-x64/blender`，三 run 全在 `~/workspace/review-rework-r2/r2t45/`，R2-T39 同款输入）**：验证输入的瘦身 GLB 是从仓库现取的远端 `assets/models/scenes/overview.glb`（37,024,624 B，blob `8791a4b8`，GLB JSON 直读 nodes 13,217 / meshes 4,623 / images 325，与 R2-T39 一致；本地 `assets/models/scenes/overview-slim.glb` 与远端均不存在，验证用下载副本、跑完已删）。完整版输入是本地 `overview.blend` 68,983,428 B 与 `overview.glb` 102,553,484 B（与 R2-T39 日志尺寸一致，仓库里这两处是瘦身版，完整版只留本地）。① 默认 run（`verify-default-20261125.log`，**exit 0**）：瘦身 GLB 13,217 对象 / 13,213 mesh / 0 无材质 primitive；完整版 13,217 对象；`EXPECTED objects=13217 source=full-blend`；瘦身 `.blend` 11,926,907 B、13,217 对象 / 446 贴图 / 缺失 0；`DONE verify_slim`，无 Traceback。② 命令行钉死旧值反测（`-- --expected-objects 13036`，`verify-cli-stale-20261125.log`，**exit 1**）：`EXPECTED objects=13036 source=--expected-objects`，随后 `VERIFY-FAIL slim GLB objects 13217 != expected 13036 (--expected-objects)`，无 `DONE`、无 Traceback、无 `AssertionError`，且 `overview-slim.blend` 未写出（跑前已删、跑后仍不存在）——失败如今确能带出退出码 1。③ 环境变量钉死错误值反测（`VERIFY_SLIM_EXPECTED_OBJECTS=13036`，`verify-env-stale-20261125.log`，**exit 1**）：`VERIFY-FAIL slim GLB objects 13217 != expected 13036 (VERIFY_SLIM_EXPECTED_OBJECTS)`，无 `DONE`、无 Traceback，`overview-slim.blend` 未写出。三份日志 `grep -c Traceback` 全是 0。另：失败 run 的日志尾不再有 `Blender quit` 行（`os._exit` 直接结束进程，属预期行为）。
- **临时文件（已清）**：验证用的 `assets/models/scenes/overview-slim.glb`（下载的远端瘦身版副本，37,024,624 B，blob `8791a4b8` 与远端逐字节一致）与 run ① 生成的 `assets/blender/scenes/overview-slim.blend`（11,926,907 B）跑完已删；run ②/③ 未写出瘦身 `.blend`；完整版 `.blend`/`.glb` 尺寸与时间戳一字未动（`overview.blend` 68,983,428 B，`overview.glb` 102,553,484 B），总览未重拼，本地树恢复原状。
- **推仓**：commit `7d97b75c`（`7d97b75c8c88296c91a2a3552cd9c35c6273aa34`，父 `56bfb69f`，2026-11-24T22:22:53Z）：1 批 push-files，2 文件（`assets/blender/tools/verify_slim.py` blob `b2252a57` 6,809 B、BLENDER_MODELS.md blob `945c6a1f` 392,058 B，单 blob 均 <40MB）；推后核对：HEAD 即 `7d97b75c`、父链连续（父 `56bfb69f` 是 R2-T40 同期推送，本次推前重读 HEAD 已是 `56bfb69f` 而非 `d1a0ff07`；该推送只删 42 张贴图、未动本文档，远端文档推前仍是 blob `f8f3606b` 与本地推前版逐字节一致，无撞车）、contents API 逐文件核对大小与 blob SHA 与本地逐项一致、远端 `verify_slim.py` 落盘含 `os._exit(1)` 与 `VERIFY-FAIL` 且无 `assert` 语句、与本地逐字节一致。改动触发工作流 run：`Blender previews (max quality)` run 45500394665（run_number 117，head_sha `7d97b75c`，触发时状态 queued），按任务要求只记 run 号、不等它。本行系推后补填，随第二次推送（仅本文档）入仓。
- **编号说明**：本节即 §46（§41 已派给 R2-T40、§42 已派给 R2-T41、§43 已是 R2-T42、§44 已是 R2-T43、§45 已是 R2-T44；写前已查远端仓库版文档确认 §46 空闲，远端文档 blob `f8f3606b` 387,431 B 与本地逐字节一致）；§24/§29/§33 一字未动；只改 `assets/blender/tools/verify_slim.py` + 本节，未动模型、未动 `.glb`、未拼总览；三份验证日志只放 `~/workspace/review-rework-r2/r2t45/`，不推仓。

## §41 R2-T40 清理旧 ov-gym/lab/canteen 烘焙图（2026-11-25，只删 42 张零引用图 + 本节，不改模型、不重建 .glb、不拼总览）

- **任务**：终轮整合已知待办——R2-T21b 换装 gym/lab/canteen 后，旧的 `ov-gym_textures/`（18 张）、`ov-lab_textures/`（36 张）、`ov-canteen_textures/`（33 张）烘焙图待清理。T21b 已把三件的材质改挂 PBR，本任务先核实再删。
- **定位（远端 tree 为准，开工 HEAD `16d8a4b7`，推前重读已是 `d1a0ff07`）**：三目录共 87 张、24,826,507 B（canteen 33 张 9,120,357 B、gym 18 张 9,709,988 B、lab 36 张 5,996,162 B）。
- **引用审计（结论：87 张里 45 张仍被引用、42 张零引用，只删 42 张）**：
  - 三件本体干净：`ov-gym/lab/canteen.blend` 与 `ov-gym/lab/canteen.glb`（本地与远端 blob 逐字节一致）经 strings + GLB JSON 直读，零贴图路径、零贴图名——T21b 的 PBR 改挂已证实（`_pbr_apply.py` 直挂 CC0 照片贴图，烘焙已取消；`ov-gym.py:19` 只剩一行历史注释“烘焙图在 ov-gym_textures/”，不加载任何文件）。
  - Godot 侧干净：全工程 `.gd`/`.tscn`/`.py`/`.md`/`.cfg`/`.json` 文本 grep，零文件引用三目录或 87 个文件名；3 个 Kenney zip 与 4 个 Quaternius `.gltf` 无命中；Kenney `.glb` 的唯一外部 URI 是 `Textures/colormap.png`，与本任务无关。
  - 剔除项（45 张，6,027,127 B）：远端总览 `assets/blender/scenes/overview.blend`（R2-T1b 瘦身版，Zstd 压缩，解压后 68,616,380 B）内含 45 个文件名作贴图路径（`//../overview/ov-gym_textures/…` 等，gym 12 次、lab 46 次、canteen 36 次），远端总览 `assets/models/scenes/overview.glb`（37,024,624 B，blob `8791a4b8`）内嵌同名贴图 45 个（stem 集合与 .blend 一字相同，两处独立信号完全一致）。按“凡有一处引用即剔除”，这 45 张全部保留：gym 6 张（metal/metal_dark 各 3）、lab 21 张（AC_Body/AC_Grille/DoorFrame/FloorSeam/MetalGrey/WinFrame/WinMullion 各 3）、canteen 18 张（AC_Body/AC_Grille/Door_Wood/FloorSeam/Frame/MetalGrey 各 3）。总览是终轮整合待重拼的旧件（T21b 前拼装），重拼后这 45 张由终轮再清，本任务不动。
  - 删除项（42 张，18,799,380 B，零引用）：canteen 15 张（Concrete/Cornice/RedBrick/Roof_DarkGrey/Wall_Orange 各 3）、gym 12 张（concrete_tex/roof_dark/wall_red/wall_red_dark 各 3）、lab 15 张（Concrete/Cornice/Roof_DarkGrey/Trim_RedBrick/Wall_White 各 3）。核对口径：① 远端总览 .blend 解压全文无这 42 个文件名；② 全仓 165 个 `.glb` JSON 直读（image name + uri）无这 42 个 stem、无指向它们的外部 URI；③ 全仓 57 个 `.blend` strings 裸文件名扫查，只 ov-bldC.blend（`//ov-bldC_textures/…` 自家同名文件，属同名误撞）与本地总览 .blend 有命中；④ 文本 grep 零命中。注：本地-only 历史文件 `assets/blender/charge/r2t19/godot-45437816576-logs.txt`（未入仓）里出现过其中部分文件名，是 2026-11-24T16:40Z 一次旧 Godot 导入的打包记录（当时件级 .glb 还是 T21b 前版），不是现行引用，不拦删除。
  - 另：本地-only 完整版总览 `overview.blend`（68,983,428 B）与 `overview.glb`（102,553,484 B）仍引用/内嵌同一批 45 张——二者均未入仓（仓库里是瘦身版），是 T21b 前的旧拼装输出、终轮重拼即丢弃；删除只动仓库文件，本地文件原地不动，本地总览仍能打开。
- **推仓（删除走 Git Data API 手动建提交，push-files 不支持删除）**：commit `56bfb69f`（`56bfb69f1d2dafd821d3e2cdd424d5e8f4a82836`，父 `d1a0ff07`，2026-11-24T22:20:05Z）：base_tree 取父提交 tree `efddd17f`，42 条 `"sha": null` 删项建新 tree `ebbc9b5e`，再建 commit、更新 main ref（force=false）。推后核对：HEAD 即 `56bfb69f`、父链连续、递归 tree 核对删项与清单一字相同（42 删、0 增、0 改）、其余 993 个 blob SHA 一字未动、45 张保留文件在位且 SHA 未变。注：推仓途中 HEAD 四次前移（`16d8a4b7`→`0fae1e42` R2-T33 §33 →`f573508d` R2-T43 §44 →`ad588cd3` R2-T44 §45 →`d1a0ff07` R2-T44 §45 推仓行补填），每次重读 HEAD、重取 tree、重建删除 tree；首次建出的 commit `34ed93c1`（父 `ad588cd3`）因 HEAD 已前移未推 ref，已成孤 commit，未入 main。
- **触发的工作流**：删除提交触发 blender-previews run **#116 / 45499984974**（head `56bfb69f`，push 触发，2026-11-24T22:20:23Z 起，查时 in_progress）；只记 run 号，未等结果（删除不改模型/贴图挂接，预览内容不变）。
- **还剩什么**：45 张保留图待终轮总览重拼后复核再清（重拼后总览 .blend/.glb 不应再含旧烘焙贴图）；三目录届时若已空，空目录随 Git 自动消失。
- **编号说明**：本节即 §41（§39 已是 R2-T38、§40 已是 R2-T39、§42 已派给 R2-T41、§43 已是 R2-T42、§44 已是 R2-T43、§45 已是 R2-T44；写前已查远端仓库版文档确认 §41 空闲）；§24/§29/§33 一字未动；只删 42 张烘焙图 + 本节，未动模型、未重建 `.glb`、未拼总览；审计用的远端总览 .blend/.glb 下载副本与解压件只放 `/tmp/r2t40_*`，不推仓。

## §42 R2-T41 overview.glb 内抹掉 leg_metal 的交互定位（2026-11-25，只诊断、不改模型、不改机位、不改 main 分支）

- **任务**：R2-T38 §39 已定位到 overview.glb 一层（去 overview.glb 一项、labels/UI 一字未动，桌椅腿即回来，#140 暗腿 53/74、面板后 53/57）。本任务在 Blender 里查 overview.glb 在教室体积内的几何与材质，定位到具体对象/材质。只诊断，不改模型、不改 .glb、不改 main 分支。
- **探针对象（推前核对）**：仓库现版 `assets/models/scenes/overview.glb`（37,024,624 B，blob `8791a4b8`，R2-T1b 瘦身版；GLB JSON 直读 nodes 13,217 / meshes 4,623 / materials 203 / images 325，与 §40 一致）；本地 `assets/models/scenes/overview.glb` 是 102,553,484 B 完整版，几何与瘦身版一致（对象数同为 13,217），本次 Blender 检查用仓库瘦身版下载副本（验后已删）。
- **教室体积（Blender 坐标，换算见 §1：Blender (x,y,z) = Godot (x,−z,y)）**：教室內景节点在 Godot (−56,0,−30)（`main.gd:_setup_interiors`），房间 9.68（Godot x）× 7.26（Godot z）× 3.5 高 → Blender x[−60.84,−51.16]、y[26.37,33.63]、z[0,3.5]；腿带 Godot y[0,0.67] → Blender z[0,0.67]；桌面 Godot y[0.67,0.70]（§37）；03 机位 target Godot (−59.0,0.9,−30.2)、az 1.352、el 0.382、dist 4.96，相机高约 Godot y 2.75，在盖面之上。
- **Blender 静态检查（Blender 4.2.0，`r2t41_blender_intersect.py`，13,213 个 MESH 对象逐个算世界包围盒）**：与教室体积包围盒相交的只有 3 个对象，全部是教学楼 A 的实心盒体，且 3 者顶点无一落在教室体积内（0/216）——包围盒相交只是盒体跨越，真正的面在下条：
  - `bldA_body_F1_F4`：包围盒 x[−76.0,−36.0]、y[22.5,37.5]、z[0.5,14.7]（40×15×14.2m），材质 `Wall_Cream_F3E9D2_tex`。
  - `bldA_plinth`：包围盒 x[−76.3,−35.7]、y[22.2,37.8]、z[0.0,0.5]（40.6×15.6×0.5m），材质 `Concrete_B9B3A8_tex`。
  - `bldA_plinth_cap`：包围盒 x[−76.35,−35.65]、y[22.15,37.85]、z[0.5,0.68]（40.7×15.7×0.18m），材质 `Cornice_D8D2C4_tex`。
  - 1m 内近邻仅 3 件：`bldA_cornice_F2`（z 4.36–4.64，在天花板 3.5 之上）、`bldA_seam_F2`（z 4.26–4.32，同上）、`OV_ASSEMBLY_ground`（z=−0.05，在教室地面之下），均与腿无关。
- **面级检查（`r2t41_blender_faces.py`，三件各 216 顶点/108 面）**：三件都是闭合实心盒（顶/底盖为整幅矩形、非镂空环），各有一张整幅水平盖面横穿教室体积（两张三角面拼成整幅矩形，面积和 = 足迹面积）：
  - `bldA_plinth_cap` 顶盖：Blender z=**0.680**、法线 +Z（朝上）、2 面面积各 317.81 m²（和 635.6 = 40.64×15.64 足迹），XY 全幅覆盖教室。
  - `bldA_plinth` 顶盖：Blender z=**0.500**、法线 +Z、2 面面积各 314.44 m²（和 628.9 = 足迹），XY 全幅覆盖教室。
  - `bldA_body_F1_F4` 底盖：Blender z=**0.500**、法线 −Z（朝下）、2 面面积各 296.71 m²（和 593.4 = 足迹），XY 全幅覆盖教室。
  - 其余水平面均为墙顶/墙底窄条（面积 0.18–0.92 m²，在墙体轮廓线上），不进教室。
  - 换算成 Godot y：三盖面在 y=0.50 / 0.50 / **0.68**；腿 y[0,0.67] 全在 0.68 盖面之下，桌面顶 y=0.70 在 0.68 盖面之上 0.02——只盖腿、不盖桌面，与 §39“桌面一直正常”完全吻合；椅腿 y[0,0.882] 只有 0.68 以上一段露出，与 §35⑥“椅背立柱清晰落地”（实为落在 0.68 盖面上）吻合；#130 腿点取样 (185,185,162) 不是教室地板，是盖面顶（被盖住的地板在 y=0，看不见）。
- **材质/共享实例核对（GLB JSON 直读，203 种材质）**：三盖材质 `Wall_Cream_F3E9D2_tex` / `Concrete_B9B3A8_tex` / `Cornice_D8D2C4_tex` 均为 **alphaMode OPAQUE、doubleSided=true、metallic 0、带 baseColor 贴图**——不透明实面；双面使朝下的 body 底盖（y=0.50）从上往下看也渲染，三盖面自上而下是 0.68 → 0.50 → 0.50 三层不透明遮挡，相机（y≈2.75）到腿的视线必穿 0.68 盖面。overview 里**没有**名为 `leg_metal` 的材质（0 个），三盖材质与 classroom 的 `leg_metal` 无任何共享实例、无共享贴图；全 GLB 仅 11 种非不透明材质（5 玻璃 BLEND、3 树叶/草 MASK、1 球网 BLEND 等），三盖均不在其中；无 transmission 材质作怪。结论：**不是材质共享、不是透明排序、不是全局状态改写，是纯几何遮挡**——实心盒顶/底盖面。
- **根因结论（定位到具体对象）**：**致因对象是 `bldA_plinth_cap`（主因，顶盖 y=0.68）**，其下 `bldA_plinth`（顶盖 y=0.50）与 `bldA_body_F1_F4`（底盖 y=0.50，朝下但双面）为同层叠加的第二/第三道遮挡。建模根源：ov-bldA 把墙裙/压顶/楼体做成了**实心盒**（Box 原语自带顶/底盖），裙座本应只是绕楼周圈的窄条，却以整幅 40×15m 实心板填满了楼体足迹、顶面抬到 y=0.68，恰好埋住一层教室的全部桌椅腿；从总览外观看不见（盖面藏在楼体下、地面上），只有进一层教室才暴露。同款实心裙座遍布各楼（bldB/bldC/lib/gym/lab/tower/canteen/dormA/dormB 均有 plinth/plinth_cap 节点），但只有 bldA 足迹内有一层教室，故只有此处致病；配电房外壳（`OV_ASSEMBLY_dist_body`/`_roof`）无 plinth 节点，dist 内景不受同因影响。
- **CI 探针验证（Blender 静态检查已定位，本探针为定因复核）**：探针分支 `r2t41-plinth-probe`（基 main HEAD `72dfcae9`），commit `6cb08b86`（`6cb08b86aaef691488ef03108d57052d3a6e21a9`，父 `72dfcae9`）：只改 `scripts/campus_builder.gd`（+10/−1，blob `7b07b2b0`，25,945 B）——overview attach 成功后在运行时藏起三件（`find_child` 递归找 `bldA_body_F1_F4` / `bldA_plinth` / `bldA_plinth_cap` 置 `visible=false`），其余一字未动。godot-verify run **#141 / 45498626070**（head 即 `6cb08b86`，push 触发，2026-11-24T22:11:57Z–22:27:19Z）：**success**；job `138815653859 verify-export success`；**VERIFY-SUMMARY: PASS=271 FAIL=0**（0 error 行；比 #140 的 268 多 3 项——overview 正常加载，T2 检查走加载分支而非跳过）；artifact `godot-screenshots`（12,362,846 B，20 张）已下载。
- **03 取样（§38 同款取样器与阈值，黑板中心投影 (575,207)，与 #130/#140 1px 级一致，机位未动）**：**#141 桌柱 53/74 暗（71%），柱中点 RGB 均值 (112,108,93)；椅柱 40/65 暗（61%），(173,159,134)——与 #140（去整个 overview.glb）逐数一字相同**；对照 #130 基线桌柱 5/74（7%）、(185,185,162)。53/74 未到 72/74 的原因与 §39 相同（17 根在右侧场景面板后不可量、4 根在框底切边，面板后 53/57 = 93%）。**目视**：03 全图逐张看过——每张桌下 4 条黑腿 + 横撑清晰落地，椅腿亦可见，浅色地砖地面恢复可见，不再是悬浮薄板。00-overview 为探针预期态：bldA 壳体被藏（“一号教学楼”标签下为空地、光伏阵列悬在原楼位上空），其余楼体/道路/操场/池塘均正常，不可作总览验收。
- **修复建议（按优先级，修复另派任务，本轮不动手）**：① 修 ov-bldA 建模：把 `bldA_plinth` / `bldA_plinth_cap` 改成绕周圈的窄环（或删顶/底盖、只留四面裙墙），`bldA_body_F1_F4` 删底盖（或把楼体底抬出首层净空）；只动 ov-bldA 一件 + 重拼 overview，总览外观不变（盖面本就不可见），教室腿即回来。② 同款检查各楼 plinth：有内景的楼只有 bldA（教室）与 dist（无 plinth），其余楼无内景、不急，但重拼时可顺手把各楼 plinth 一并改环，防后患。③ 不要动腿管加粗/换色、不要动机位/光照（§37/§38/§39 已三度证伪）。④ 修后回归：main 上重跑 godot-verify，03 取样暗腿 ≥53/74、红腿 A/B 可选；00-overview 须复验总览外观无回归（bldA 壳体须回来）。
- **推仓（探针分支）**：commit `6cb08b86`（`6cb08b86aaef691488ef03108d57052d3a6e21a9`，父 `72dfcae9`，2026-11-24T22:11:57Z）：1 批 push-files，1 文件（`scripts/campus_builder.gd` `7b07b2b0` 25,945 B，单 blob <40MB）；推后核对：分支 HEAD 即 `6cb08b86`、父链连续、contents API 核对大小与 blob SHA 与本地逐项一致。探针分支的提交留在分支上，不合入 main。
- **推仓（main 文档）**：commit `1049edd4`（`1049edd435c2e2bbb86cb9b4c3a132c3f81780bb`，父 `94762754`，2026-11-24T22:32:17Z）：1 批 push-files，1 文件（BLENDER_MODELS.md `c90b4abb` 407,877 B，单 blob <40MB）；推后核对：HEAD 即 `1049edd4`、父链连续、contents API 核对大小与 blob SHA 与本地逐项一致、远端文档含 §42 全文且 §41/§43–§46 一字未动。只推文档，未触发须等的工作流 run。本行系推后补填，随第二次推送（仅本文档）入仓。
- **还剩什么**：① 修复任务待派：修 ov-bldA 实心裙座为窄环（+ body 删底盖）并重拼 overview，main 上复验；② R2-T23 的①⑤两项待修后在 main 上复验；③ 探针分支 `r2t41-plinth-probe` 保留作证据（#141）。
- **编号说明**：本节即 §42（§39 已是 R2-T38、§40 已是 R2-T39、§41 已是 R2-T40，写前已查远端仓库版文档确认 §42 空闲，远端文档 398,409 B、blob `3ff67ddf` 与本地逐字节一致；§43–§46 已由 R2-T42–R2-T45 先行写入，本节按惯例追加在文末）；§24/§29/§33 一字未动；探针分支只改 `scripts/campus_builder.gd` 1 文件，本文档只加本节，未动模型、未动 `.glb`、未动机位、未改 verify_fixes.gd；Blender 脚本、交集/面级 JSON、job 日志与截图只放 `~/workspace/review-rework-r2/r2t41/`，不推仓。

## §48 R2-T47 ov-road-walk.py:409-410 旧注释更新（2026-11-25，只改 2 行注释 + 本节，不改逻辑、不重建、不推模型）

- **任务**：§33③ 与 §43 留下的遗留收尾：`assets/blender/overview/ov-road-walk.py:409-410` 的旧注释仍引 R-N2/跑道重叠问题修之前的旧口径，与现行口径不符。本任务只改这两行注释。
- **旧注释原文（远端 HEAD `1049edd4` 版逐字核对一致）**：
  - `#  结论: 按原线施工, 无调整。另: R-N2 西缘距操场缓冲椭圆东尖 (-37) 2.5m、距 bldA`
  - `#  东墙 (-36) 1.5m; R-N1 距 tower 南墙 1.5m、距 canteen 南墙 4m; R-N5 走 bldB/bldC`
- **旧在哪里**：(-37) 尖与 2.5m 是旧椭圆口径（中心 (-80,-25)、rx40、+3m 缓冲东尖 -37）；R2-T1b 已把跑道东移至中心 (-62,-25)、外椭圆 rx28/ry40，+3m 缓冲东尖现为 -31，路全宽落在缓冲内（§33 实测：缓冲内路段 y -44.85..-5.15，全宽段 y -32.69..-17.31），“距东尖 2.5m”已不存在。现行口径是 §33 修法②：禁入区 = +3m 缓冲椭圆（中心 (-62,-25)、rx31/ry43）− R-N2 路廊矩形 x[-34.65,-31.35]×y[-76,18.5]。另：路 vs 跑道几何 415 对相交已在 §43 复现并接受为已知问题（留终轮定夺），合渲黑带系环顶（z=0.10）与铺装顶（z=0.10）共面透镜所致，藏起路缘石重渲黑带像素相同、切路缘石无效——旧注释对此一字未提。
- **新注释（只改 409-410 两行；其余净空数 bldA 1.5m / tower 1.5m / canteen 4m 与 R-N5/R-N4 句一字未动，411 行仍续接“之间 11m 缺口”）**：
  - `#  结论: 按原线施工, 无调整。（旧口径“R-N2 西缘距缓冲椭圆东尖 (-37) 2.5m”已作废：禁入区口径为 §33 修法②缓冲椭圆 (+3m, 中心 (-62,-25) rx31/ry43) − R-N2 路廊矩形 x[-34.65,-31.35]×y[-76,18.5]；路 vs 跑道几何 415 对相交已复现并接受为已知问题（§43），黑带系环/铺装共面透镜，切路缘石无效。）`
  - `#  另: R-N2 西缘距 bldA 东墙 (-36) 1.5m; R-N1 距 tower 南墙 1.5m、距 canteen 南墙 4m; R-N5 走 bldB/bldC`
- **验证**：`python3 -m py_compile assets/blender/overview/ov-road-walk.py` 通过（生成的 `__pycache__/*.pyc` 已删）；本地 diff 与远端版 diff 均恰好只有 409-410 两行注释，零逻辑改动。
- **推仓**：commit `03bd7510`（`03bd751084258ba89b9fdad0bb8269f6dd46515a`，父 `bfb14f14`，2026-11-24T22:34:38Z）：1 批 push-files，2 文件（`assets/blender/overview/ov-road-walk.py` blob `54fd5c17` 38,166 B、BLENDER_MODELS.md blob `5503e37c` 411,350 B，单 blob 均 <40MB）；推后核对：HEAD 即 `03bd7510`、父链连续（父 `bfb14f14` 是 R2-T41 的 §42 推仓行补填推送，本次推前 HEAD 已是 `bfb14f14` 而非 `1049edd4`；该推送只改本文档 §42 末行一处、未动其余章节，远端文档推前与本地推前版逐字节一致，无撞车）、contents API 逐文件核对大小与 blob SHA 与本地逐项一致、远端 `.py` 落盘含新注释且与本地逐字节一致、远端文档含 §48 全文。注：推前重读 HEAD 时 `bfb14f14` 尚未建出（22:32:59Z 建出，本次推送 22:34:38Z 建出），push-files 以推送时 HEAD 为基建提交，父链已连续，无孤 commit。本行系推后补填，随第二次推送（仅本文档）入仓。
- **触发的工作流**：`Blender previews (max quality)` run **#118 / 45502232523**（head `03bd7510`，push 触发，2026-11-24T22:34:42Z 起，查时 in_progress）；只记 run 号，未等结果（注释改动不影响渲染）。
- **编号说明**：本节即 §48（§41 已是 R2-T40、§42 已是 R2-T41、§43 已是 R2-T42、§44 已是 R2-T43、§45 已是 R2-T44、§46 已是 R2-T45、§47 已派给 R2-T46；写前已查远端 HEAD `1049edd4` 的仓库版文档确认 §47/§48 均未入仓、§48 空闲，远端文档 blob `c90b4abb` 与本地推前版仅差 §42 末行 R2-T41 的推仓行补填一行）；§24/§29/§33 一字未动；只改 `ov-road-walk.py` 2 行注释 + 本节，未动模型、未动 `.glb`、未拼总览。

## §47 R2-T46 教室第三盏补光实施（2026-11-25，只加一盏 SpotLight3D + 本节，不动室外灯光、不改模型、不改 .glb）

- **任务**：执行 §45 定夺的最小修复方案（第三盏 SpotLight3D），只加这一盏灯。§45 定夺：南墙西端窄条复测西段 (72,70,58)、整带 (78,72,59)，与目标 (97,88,68) 差 -25/-18/-10 与 -19/-16/-9，T30 两盏补光没修到这一段，需修。
- **探针（R2-T30 harness 复制品，`~/workspace/review-rework-r2/r2t46/probe/`，Godot 4.4 原生 llvmpipe，1280×720，main/south/north/up 四机位；取样口径与 §45/R2-T37 同款：7×7 窗口中位）**：基线（只开 T30 两盏）复现 §45 #139 窄条 10 点逐值 ±1（西段 (71,70,57) 对 §45 (72,70,58)，整带中位 (75,71,58) 对 §45 (78,72,59)——§45 整带是更密取样的中位，点值一致为准）。南墙窗户布局以 GLB 回读为准（glass_s1 x -4.5..-2.7、s2 -2.1..-0.3、s3 0.3..2.1、s4 2.7..4.5，窗高 y 0.9..2.4）：南墙窗间墙共 3 条 0.6m 竖缝（S1/S2 间 x -2.7..-2.1、S2/S3 间 -0.3..0.3、S3/S4 间 2.1..2.7）+ 两端墙；本次取样 S1/S2 缝（south 屏 (920,300)/(920,360)，世界 (-2.27,1.89,3.63)/(-2.29,1.40,3.63)，离锥轴 36.6°/30.7°）与 S3/S4 缝（屏 (360,300)，世界 (+2.27,1.89,3.63)，离轴 91.4°）。
- **§45 原定锥角 50° 档：三档全 spill（§45 前提有误，见下）**：窄条西段/整带 R——基线 71/75；E=0.8 **96/115**；E=1.0 101/122；E=1.2 105/129。窄条本身只有 E=0.8 在 90–100 内（1.0/1.2 已超）；但 S1/S2 窗间墙——基线 (113,85,66)/(111,84,65)；E=0.8 **(138,94,71)/(143,96,72)**；E=1.0 (143,97,72)/(149,99,74)；E=1.2 (148,99,74)/(156,102,75)——**三档全超 §45 上限 135**。另西墙南缘（main 屏 (200,150)，西墙南段上部）基线 (96,86,67)→E=0.8 (114,91,70)、1.0 (118,93,70)、1.2 (122,94,71)，超 §45 预估的 +5–10（西墙三点中位仍 (97,87,68)，≤105）；左白板亦被吹粉（(250,200) (211,198,201)→(250,213,213)）。天花板（主视角 (128,113,79)、仰拍 (137,120,85)）与北墙窗间墙（(215,139,104)，Δ0）三档全程一字未动。
- **根因（Godot 4.4 锥角口径实测，§45“半角 25°”的前提不成立）**：spot_angle=50° 时离轴角–ΔR（E=0.8）：0° +29–35、30.4° +25、30.7° +32、36.6° +25、38.4° +14、46.5° +3–4、60.4° 0——有效半角约 **50°**（非 25°），50° 档实为约 100° 宽的锥，+8R 足迹 x[0,440] y[30,604]（36,384 px）。§45“东侧窗间墙在锥外（与锥轴夹角约 37° > 半角 25°）”是按 full-angle 理解写的，Godot 里不成立。
- **重扫（§45“探针不达标就调能量/锥角/位置三选一重扫”条款）：锥角 50°→25°（即 §45 想要的半角 25°），能量再扫 0.8/1.0，全口径通过**：窄条西段/整带 R——25°/E=0.8 **(95,78,62)/(112,84,65)**；25°/E=1.0 (100,80,63)/(117,86,66)。S1/S2 窗间墙两档**一字未动**（(113,85,66)/(111,84,65)）；S3/S4 缝、北墙窗间墙、天花板（主/仰拍）、西墙（三点中位与南缘 (96,86,67)）、左白板（(211,198,201)）两档**全部一字未动**。+8R 足迹收至 x[0,316] y[208,528]（12,993 px，约 50° 档的 1/3）。**选定 25°/E=0.8**（西段 95 居 90–100 正中；E=1.0 的西段 100 已顶上限，CI 与探针 ±1–3 的偏差即超标，无余量）。
- **附带复核（协调者追加点：§45 附带发现——窗上沿顶带西端，03 图左上 x 0–100, y 80–130）**：7 点中位——基线 **(71,70,58)**；50° 档 E=0.8 (78,74,60)、1.0 (80,75,60)、1.2 (81,76,61)（最西点 (20,100) 71→89/93/97）；**25° 两档一字未动 (71,70,58)**。结论：**顶带西端仍暗**，25° 窄锥够不着它（离轴约 50°+、且在锥顶之外），留终轮注记；不另加灯、不改验收口径。
- **实施（只改 `scripts/classroom_interior.gd` 的 `_add_fill_light()`，GLB 分支与程序化回退分支同走该函数，故一次改动两处生效）**：新增常量 `FILL3_POS (-2.2, 1.8, +1.0)`、`FILL3_TARGET (-3.8, 0.7, +3.6)`、`FILL3_ENERGY 0.8`、`FILL3_ANGLE 25.0`、`FILL3_RANGE 4.0`；第三盏 `FillSpotSouthWest`：色 #ffe0b3（`FILL_COLOR`）、衰减 1.0、无阴影；朝向用 `rotation` 定——`Basis.looking_at(FILL3_TARGET - FILL3_POS, Vector3.UP).get_euler()`，不用 `look_at`（§30 教训）；探针核对 rot_deg **(-19.81, 148.39, 0)**、出光方向与目标方向点积 **1.0**，与手算 yaw 148.39°/pitch -19.81° 一致。`godot --headless --check-only` 退出 0，无脚本报错（本地 .godot 未导入 classroom.glb 的 GLB 加载警告是 R2-T36 已知本地现象，与本次改动无关）。
- **推仓**：commit `73892b81`（`73892b817007261db852424e880b3239500523c6`，父 `187e3a4a`，2026-11-24T22:58:33Z）：1 批 push-files，2 文件（`scripts/classroom_interior.gd` blob `1593a229` 8,724 B、BLENDER_MODELS.md blob `3cef6811` 418,781 B，单 blob 均 <40MB）；推后核对：HEAD 即 `73892b81`、父链连续、contents API 逐文件核对大小与 blob SHA 与本地逐项一致、远端 `.gd` 落盘含 `FillSpotSouthWest` 且与本地逐字节一致、远端文档含 §47 全文。注：推前重读 HEAD 为 `187e3a4a`；推仓时远端已是 `187e3a4a`（§42 R2-T41 与 §48 R2-T47 在其前落地），本地文档已先按远端版重取（blob `29206db4`，含 §42/§48）再追加 §47，未覆盖他人章节。本行系推后补填，随第二次推送（仅本文档）入仓。
- **验证**：**godot-verify #143**（run 45505844903，head `73892b81`，push 触发）：completed **success**，job `verify-export` success，job 日志 `VERIFY-SUMMARY: PASS=271 FAIL=0`；job 日志 387 行 ERROR 全是已知导入噪音（tevy 草地 `KHR_mesh_quantization`/`EXT_meshopt_compression` 不支持、Kenney `colormap.png` 缺失、无头 progress-dialog、“Parameter t is null”，与 §37/§38 所述同类），无新增失败；`classroom.glb` 导入为 `classroom.glb-defe388a…scn`（与 #130 同 hash），`classroom_interior.gd` 已编入 `.gdc` 并导出，第三盏灯在 CI 构建里已生效。artifact `godot-screenshots`（12,419,211 B，20 张）已下载。**03-classroom.png 复核（R2-T44 同款取样器，7×7 窗口中位；与 #139 基线同图比）**：窄条东段 (115,85,65)、中段 (113,84,65)、西段 **(95,81,63)**、整带 **(113,84,65)**——与 25°/E=0.8 探针值（西段 (95,78,62)、整带 (112,84,65)）逐值一致（±1；西段 G 的 81 对 78 是末点 (133,352) 7×7 窗口跨到最西窗玻璃边的取样伪影，该窗内墙像素实为 (87,75,60)，与探针西端一致，段中位 R=95 不受影响）；顶带西端 (72,70,58) 与 #139 一字未变——**仍暗，留终轮注记**（与探针 25° 档一致）；西墙 (96,86,67) 一字未变；左白板 (209,200,203)/(191,195,202) 与 #139 一字相同，无 50° 档的吹粉；黑板 (13,31,29)、地板 (234,230,193) 正常。**目视**：03 全图逐张看过——窄条已由暗带变为暖褐（与西墙 (96,86,67) 亮度台阶基本抹平），窗间墙/天花板在 CI 取景内不可见（R2-T30 已述），以探针 south/north/up 视图为准（两档 25° 下一字未动）；桌椅/讲台/空调/窗户无回归。其余 19 张：00/01/02/04 逐张扫视正常（总览、光伏屋顶、储能柜、充电区均在位，无缺件、无品红）；05/09 与 #139 md5 一字相同；其余 md5 不同属渲染噪声 + 其间 R2-T43 的 5 棵树移位（总览图），无回归。本行系推后补填，随第二次推送（仅本文档）入仓。
- **还剩什么**：① 窗上沿顶带西端仍暗 (71,70,58)，与窄条同因（锥角边缘 + 掠射角），25° 锥够不着，留终轮注记（§45 附带发现仍有效）；② 50° 档 spill 数据已成 Godot 锥角口径教训：`spot_angle` 按有效半角理解，写 50° 即约 100° 宽锥——后续任务凡写锥角须先实测有效半角，不得按 full-angle 臆断；③ 窄条东段超出 03 取景的部分（south 视图下窗下墙带东段）本次未验——03 图只见西段，探针 south 视图 y=445 一带低处多为桌椅遮挡，取样口径只覆盖 03 可见段；④ §30 遗留②天花板四角仍略暗本次未重测。
- **编号说明**：本节即 §47（§41 已是 R2-T40、§42 已是 R2-T41、§43 已是 R2-T42、§44 已是 R2-T43、§45 已是 R2-T44、§46 已是 R2-T45、§48 已是 R2-T47；写前已查远端 HEAD `187e3a4a` 的仓库版文档确认 §47 空闲，远端文档 blob `29206db4` 与本地推前版逐字节一致）；§24/§29/§33 一字未动；只改 `scripts/classroom_interior.gd` + 本节，未动模型、未动 `.glb`、未拼总览；探针工程、24 张出图与取样脚本只放 `~/workspace/review-rework-r2/r2t46/`，不推仓。

## §51 R2-T50 树太小整改：行道/点缀树放大到真实树高（2026-11-25，只改 ov-trees 一件 + 本节，不拼总览、不动 Godot、不动其他件）

- **起因**：用户 2026-11-25 06:42 直接反馈“树还是太小了”，看的是 blender-previews #112 的 `ov-trees.png` 与 Godot #134 总览。上一轮 T15 曾在文档里写高度档“全数实测在档”（行道 5–8m、密植 8–15m、D3 8.7–12m、点缀 4–7m），T32 也写西沿线 3 棵高 12.45/8.06/11.83m——但用户在图里仍觉得树太小。本次不许只在文档里写“已按真实树高”，以下全部是 Blender 4.2.0 实测数（地上高度 = 树顶 z，Quaternius 埋地根系不计）。
- **审计（v5 `ov-trees.blend` 实测，473 棵；对照：校园常见悬铃木、香樟成熟株 10–15m+，行道/大乔木应 8–15m 级，点缀小乔木至少 6–8m）**：
  | 类别 | 棵数 | v5 高度范围 | v5 中位 | 结论 |
  |---|---|---|---|---|
  | street（新种行道 T-A/T-B/T-C/R-N1-T/R-N2-T/R-N3-T） | 192 | 5.00–8.00m | 6.50m | 偏小约 40–50%，放大 |
  | road（旧树路旁） | 19 | 5.13–7.95m | 6.72m | 偏小，放大 |
  | ornamental（D6 楼间点缀） | 19 | 4.30–7.00m | 5.10m | 偏小，放大 |
  | scattered（旧树楼间） | 15 | 4.05–6.98m | 5.60m | 偏小，放大 |
  | dense_belt（D1/D4/D5/D5b 密植） | 104 | 8.10–14.90m | 10.60m | 已在档，保留 |
  | perimeter（旧树沿线） | 112 | 8.02–14.99m | 11.75m | 已在档，保留 |
  | feature（D3 池塘特征树） | 12 | 8.70–12.00m | 10.10m | 已在档，保留 |
  分模型（v5 → v6，棵数/范围/中位）：CommonTree_3 5 棵 8.70–10.80/10.10 → 不变；CommonTree_5 3 棵 9.10–12.00/11.10 → 不变；Pine_4 2 棵 10.00–11.20/10.60 → 不变；Pine_5 2 棵 9.70–10.10/9.90 → 不变；tree_default 34 棵 5.00–8.00/6.70 → 6.73–15.00/12.75；tree_detailed 39 棵 4.50–7.90/6.40 → 6.33–14.83/12.33；tree_oak 48 棵 4.50–14.99/7.65 → 6.33–14.99/12.15；tree_pineDefaultA 38 棵 4.30–7.80/6.38 → 6.20–14.67/11.75；tree_pineDefaultB 34 棵 4.05–8.00/6.25 → 6.03–15.00/11.91；tree_plateau 31 棵 4.60–7.90/6.30 → 6.40–14.83/12.00；tree_thin 36 棵 4.53–7.90/6.15 → 6.35–14.83/11.91；tree_tall 29 棵 7.10–14.54/9.80 → 8.10–14.91/11.50；8 种 pineTall（A–D 及 detailed）共 172 棵 8.02–14.99 → 一字不变。高度档统计：≥10m 的树由 159 棵 → **367 棵**；<6m 的树由 85 棵 → **0 棵**。基线单件图绿冠像素：#112 `ov-trees.png` 绿冠（G>R+10 且 G>B+5）占全帧 **2.01%**（18,541/921,600px），绿冠包围盒 870×447px（新图对比见验证节）。
- **放大口径（`ov-trees.py` 升 v6，只改缩放，模型/来源/棵数/位置布局一字不动）**：street/road 原档 [5,8] → [10,15] 线性重映射，ornamental/scattered 原档 [4,7] → [6,8] 线性重映射，dense_belt/perimeter/feature 原样；重映射只在 `plant()` 内、模型选中后再算缩放——模型选择仍用原目标高过滤（`crown_z0×s ≥ 1.2m`），`rng` 消费与每棵模型/位置/朝向与 v5 一字相同；`green_layout.json` 与 `HEIGHT_OLD` 原档一字不动。3 棵槽位帽（见复核①/⑤）：T286 (-43.44,-32) 帽 9.0m、T288 (-46.16,-8) 帽 9.0m、Tree_284 (-38,-48) 帽 9.5m。
- **重建（`assets/blender/overview/ov-trees-r2t50.log`，Blender 4.2.0 本地 `-b`）**：EXIT=0，日志零 Error/Traceback；RELOC 共 45 条（R2-T43 5 + L1/R2-T32 40，一字未变）；新种 327 + 旧树换模 146 = **473 棵**，三角面 **120,634**（与 v5 一字相同，≤300k 预算——缩放不增面），GLB 回读 **473** 棵树对象；`.blend` 6,005,372 B（与 v4/v5 同体积）、`.glb` 3,546,820 B。文件头已同步记录放大口径与复核结论。
- **重建回读（独立复核脚本，新 GLB vs 远端 v5 GLB `0ed3fac6` 全量逐棵比对，非脚本自带回读）**：位置差异 **0 棵**、模型差异 **0 棵**、高度与重映射公式差异 **0 棵**（容差 0.06m）；分档新中位：street 12.50m、road 12.87m、ornamental 6.73m、scattered 7.07m，dense_belt 10.60m、perimeter 11.75m、feature 10.10m 一字不变。
- **约束复核① R2-T43 移的 5 棵（树干位置不动；干半径取半剖面实测：tree_default 地上干半径 local 0.0973、tree_pineDefaultB 0.1061、tree_plateau 0.0922；净空 = BVH 精确量取的树干中心到件面距离 − 干半径，z=0.12m 量取）**：
  | 树 | 新位 | 高 | 干半径 | 冠半径/冠底 | 精确净空（最小→最大） | 结论 |
  |---|---|---|---|---|---|---|
  | Tree_285 tree_plateau | (-45.80,-40) | 5.70→11.17m | 0.42→0.82m | 3.54m / 3.71m | 内缘路缘石 0.27m、球场东线 0.31m | 通过 |
  | Tree_286 tree_default | (-43.44,-32) | 6.10→**9.0m（帽）** | 0.49→0.51m | 1.99m / 4.22m | 内缘路缘石 0.13m、看台 step_3 0.15m、step_2 0.95m | 通过（紧，见下） |
  | Tree_287 tree_default | (-45.50,-12) | 6.00→11.67m | 0.48→0.66m | 2.58m / 5.47m | 看台 step_2 0.34m、step_3 0.51m、内缘路缘石 0.75m、球场东线 0.77m | 通过 |
  | Tree_288 tree_pineDefaultB | (-46.16,-8) | 6.40→**9.0m（帽）** | 0.44→0.62m | 1.55m / 3.17m | 内缘路缘石 0.11m、球场东线 0.15m、Shrub_00 0.46m | 通过（紧，见下） |
  | Tree_289 tree_default | (-36.00,0) | 5.80→11.33m | 0.47→0.65m | 2.51m / 5.31m | R-N2 西路缘 0.70m、外缘路缘石 3.20m | 通过 |
  帽的算法：T286 槽宽仅 1.31m（内缘路缘石面 -42.76 至看台 step_3 东缘 -44.10），若按档放大到 11.83m、干半径 0.67m，两侧净空为 -0.02/-0.01m（压线）；帽 9.0m 后干半径 0.51m、净空 0.13/0.15m。T288 若按档放大到 12.33m、干半径 0.65m，路缘石/球场东线净空为 -0.07/-0.09m（压线）；帽 9.0m 后干半径 0.62m、净空 0.11/0.15m。两处帽顶净空均 ≥0.11m，与 §44 接受的 0.16m 紧净空同档（§44 亦为实测无接触）。树冠悬挑：5 棵冠底 3.17–5.47m，冠层水平悬挑过跑道环面（环面 z≈0.1m、路缘石顶 ≤0.15m）与 R-N2 路廊上空，垂向净空 ≥3m，**无三维接触**；T289 冠西缘 -38.51m 未及路廊（西缘 -34.65m）。
- **约束复核② R-N2-T 东列（x=-28，共 17 棵：16 棵 R-N2-T 行道 + 1 棵 D6 点缀 Tree_227 (-28,16)，后者 4.50→6.33m、非行道）**：干边到 R-N2 路廊东缘（-31.35m）最近 **1.41m**（y=-64 tree_oak，干半径 1.94m——Kenney oak 原生干粗，实测值），其余 2.26–2.94m；到草地色带 `Slab_G2_053` 西缘（-31.0m）最近 1.06m。冠层最远西悬至 -32.70m（y=-24，冠底 4.93m），入路廊上空 1.35m、入色带上空 1.70m，冠底 >4.4m，路面/色带面 z≈0.1m，**无接触**，属行道树正常悬挑。
- **约束复核③ T32 西沿线 3 棵**：Tree_405 (-119.52,-33.96) **12.45m**、Tree_407 (-119.30,-24.29) **8.06m**、Tree_409 (-119.48,-16.71) **11.83m**——与任务书数字逐值相符（此前“东沿线被移 3 棵 14.65/8.13/14.09m”是另一组，本次亦核对无误）；3 棵均为 perimeter 档、位置/高度一字不动，距新跑道西缘（-90.3m）约 29m，§32 的缓冲归一化半径 r² 3.91–3.98 不变，已合规。
- **约束复核④ 全量两两间距（终版 `.blend` 全精度复核）**：<2.0m 对 **0 对**、≤2.6m 对 **21 对**，与 v5（§44）同一集合、无新增无减少（含 3 对 2.60m 密植带对与 5 对 2.00m 对，设计下限 2m）。位置一字未动，故间距必然不变，本次仍实测复核。
- **约束复核⑤ 全局安全扫描（路/跑道/球场/步道顶点云筛查 + BVH 精确复核；8 处旗标逐一排查）**：Tree_284 (-38,-48，同列未移树）**帽 9.5m**——按档放大到 12.00m 时干半径 0.68m、距跑道外缘路缘石仅 **0.01m**（v5 为 0.19m，放大吃掉 0.18m），帽顶后干半径 0.54m、净空 **0.15m**；同列其余 5 棵（x=-38）距外缘路缘石净空 3.91–14.88m。其余 8 处为 **v2/v3 既有布位问题、非本次放大新造**（“树干正下方为何物”只与位置有关，位置自 v2/v3 未动；本次不移动，布位改动归终轮/T52）：D4 4 棵 Tree_160–163（(-72/-64/-56/-48, 8)）与 OLD-scattered Tree_460 (-60,12) 共 5 棵立于跑道环面北弯段——y=8 处内椭圆（ry 32）不到，环面为整段弦宽（x -77.83..-46.17），y=12 同理；5 棵高度/位置与 v5 一字相同（D4 密植档未放大）。OLD-road Tree_445 (99.29,-30.33) 与 Tree_453 (99.20,49.39) 干心距环路东缘路缘石面仅 0.02/0.06m，即立于石线上（v5 已分别嵌入 -0.42/-0.39m，今 -0.56/-0.81m）；OLD-road Tree_440 (99.27,-80.51) 干心距东南角倒角石 0.25m、干身压线（v5 -0.12m，今 -0.49m）。Pine_4 两处 Tree_139/145 为误报：干心距石/路面 1.41/1.07m，地上干半径约 0.44m，低枝（r=2.05m）在 0.75m 高、石顶 ≤0.15m，垂向净空约 0.6m，无接触。
- **推仓**：待填。
- **验证**：blender-previews run **#120 / 45506952839**（head `f7145a6e`，2026-11-24T23:05:52Z = 07:05 CST 起跑，约 08:04 CST 完成）：completed **success**，6 组全部 success。artifact `blender-previews-overview`（18,001,174 B）已下载，20 张 PNG 全量品红扫描（R>150、G<140、B>150）**全部 0.0000%**；逐张目视：**ov-trees ✓ 通过**——与 #112 基线同取景、473 棵全在位，行道树一眼变大（原先细针状小冠、现为宽圆冠 + 可见树干；绿冠像素占全帧 **2.01% → 4.71%（18,541 → 43,367px，2.34 倍）**，绿冠包围盒同为 x[207,1076]、y 略收 188–634 → 188–626；行道中位高 6.50 → 12.50m，1.92 倍），密植带与 D3 特征树无变化、形态无失真、无缺失无品红；**ov-track ✓**——红环 + 白分道线完整，单件渲染不含树件，无回归；ov-road-main / ov-field 扫视正常（环路沥青 + 黄中线、球场/球门/看台在位）；其余 16 张品红 0 且未改动、无回归。结论：单件图验收通过。**总览视角待 T52 复验**（见“还剩什么”①）。
- **还剩什么**：① **总览视角待 T52 复验**——本轮只改了 ov-trees 单件，总览 GLB 仍是 R2-T1b 的 `3a20fea3` 旧版（不含 T15 的 473 棵新树），在 T52 重拼总览出图之前不许声称总览已确认；② 复核⑤ 的 8 处既有布位问题（5 棵立于跑道环面：160–163/460；3 棵干身压环路东缘石线：440/445/453，其中 445/453 干心正在石线上）留终轮定夺（移位须联动行道树列线与 D4 密植带，不在本任务“只放大”范围内）；③ T286/T288/T284 的紧净空（0.11–0.15m）终轮若重排路缘石/看台东缘（>0.11m）须复核此三棵；④ `green_layout.json` R-N2-T 区仍列 5 棵旧坐标（设计源未动，修位置于 `ov-trees.py` 的 `R43_RELOC`，照 R2-T32 款式）。
- **编号说明**：本节即 §51（§49=R2-T48、§50=R2-T49、§51 即本任务；§52 已是 R2-T51，先落本地、尚未推仓——本节按编号插在 §52 之前；写前已查远端 HEAD `5508bc60` 的仓库版文档确认 §51 空闲，远端文档 blob `3cef6811`、418,781 B，与本地除 §52 外逐字节一致；远端 ov-trees 三件 blob（`0ed3fac6`/`b0b94584`/`23e8bb9e`）与 v5 基线 f573508d 一字相同，无撞车）；§24/§29/§33/§44 一字未动；只改 ov-trees 一件（`.py` / `.blend` / `.glb` + 本轮日志）+ 本节，未拼总览、未动 Godot。

## §52 R2-T51 草在总览里不可见整改（2026-11-25，只改 ov-lawn 一件 + 本节，不拼总览、不动 Godot、不动其他件）

- **起因**：用户 2026-11-25 06:42 直接反馈“草还是没有”——在总览里看不到草。上一轮 T18 的 ov-lawn 单件图目视通过，但总览里仍是平绿。最高优先级，今晚 22:00 交版前必须改到位。
- **审计① 总览视角（Godot 侧实证）**：godot-verify run **#142 / 45498809451**（head `f573508d`，success）的 `godot-screenshots` artifact（12,422,014 B）中 `00-overview.png`（1280×720）逐像素分析——草色掩码（G>90 且 G>R+8 且 G>B+8）占全帧 **33.9%**；草区 8×8 块（≥80% 草色）4,049 块中 **74.1% 是平色块（块内 G 标准差 <3，中位仅 0.52）**，有纹理块（std≥3）仅 25.9%，std≥6 仅 23.2%；草色像素 G 均值 169.6、p5=133/p50=174/p95=178，深绿（G<135）只占草色像素 5.5%。目视：整片地面一色浅绿，只有树点与跑道有变化，草确实不可见。**结论：用户反馈属实。**
- **审计② 单件图（Blender 侧实证）**：blender-previews run **#113 / 45484839169**（head `a59137dd`，success）的 `blender-previews-overview` artifact（17,944,600 B）中 `ov-lawn.png`（1280×720）同口径分析——草色掩码仅占全帧 **10.6%**；草区 1,170 块中 std≥3 占 82.6%、std≥6 占 23.7%、std≥10 仅 8.7%；草色 G 均值 174.7、标准差 12.4；G 直方图双峰：主峰 180–185（38,413px）与次峰 170–175（29,500px），即 A/B 两档色带渲染后 ΔG 仅约 **10**（基色 ΔG=20，渲染压缩约一半），C 档（基色 196）无像素 >190、完全并入 A 档；深绿草丛像素（G<120 且 G>R+15）只占草色像素 **1.27%**（1,231px）。目视：4m 色带条纹可见、drift 带呈 faint 点线、两块旧草坪深绿区可见，但单丛只有约 1–3px、370 丛只占草地像素约 1.8%。**结论：T18 单件图“通过”是近景尺度下的通过，总览尺度下草层信号太弱。**
- **审计③ 总览 GLB 是否含 T18 新草（节点核对，实测）**：下载远端 `assets/models/scenes/overview.glb`（37,024,624 B，blob `8791a4b8`，与远端 tree 一致），GLB JSON 实测 13,217 节点 / 4,623 mesh / 203 材质；`Tevy*` = **0**、`Slab*` = **0**、`Drift` = 0、`RedOat` = 0；仅有旧程序化草（`Lawn*` 21 个、`GrassEdgeAlpha*` 7,840 个）。对照本地 T18 版 ov-lawn.glb：8,802 节点，`Tevy*` = 370、`Slab*` = 163、`RedOat` = 18。另核对：远端 ov-lawn.glb blob `8ed78367` 与本地逐字节一致，确为 T18 版。**结论：仓库现总览 GLB 是 R2-T1b 的 `3a20fea3` 版（2026-11-25 00:05 CST），不含 T18 的任何新草——用户在 Godot 总览里看到的还是旧平绿；这一点由终轮总览重拼（R2-T52）解决。** 另记：blender-previews 只渲染单件 `.blend`，artifact 里没有拼装总览图；任务书所说的“总览图”实为 godot-verify 的 `00-overview.png`（本节审计①），特此更正。
- **根因（两点，都有数）**：① 总览 GLB 根本没进新草（审计③）；② 即使进了，0.76m 草丛在总览约 4.6px/m 下单丛仅 ~3×5px、370 丛覆盖率约 1.8%，色带 A/B ΔG 渲染后仅 ~10、易被 Godot 洗白进一步压缩——草在总览尺度下物理上就不可见。GREEN_PLAN.md §7 的“新高草 ≥21,500 丛”验收条已被 T18 作废（全 lod2 也要 6.55M 面），**本轮不复活**，在面数预算内想办法。
- **整改（只动 ov-lawn，3 手段，面数账先算再铺）**：① **色带对比加强（0 面）**：A `#69B45E`→`#86CC74`、B `#57A04B`→`#3E7A32`、C `#7FC46A`→`#A9BE4A`——新 A/B 基色 ΔG=82（旧 20），C 另成黄绿色相；3 张 `Lawn_Strip_?_color.png`（64×64 平色）已同步换色，GLB 回读确认内嵌贴图均值 A (134,204,116)/B (62,122,50)/C (169,190,74) 与新色一致。② **色带棋盘化（+3,480 面）**：每条色带沿长边 ≤16m 切段、段间 A↔B 交错（C 条用 C↔A），由整条一色条纹改 4m×16m 棋盘格斑驳；段长 16m 经离线仿真核定（仿真复现 T18 恰好 163 块/393,632 面；12m 段会到 398,540、8m 段超预算 401,408，故取 16m）；163→**453 块**。③ **tevy 放大（0 面）**：lod2 ×1.5–2.0、lod1 ×1.25–1.65、lod0 ×1.1–1.35、红燕麦 ×1.5–2.0——lod2 高 0.76m→1.14–1.52m、幅 1.21m→1.8–2.4m，总览下单丛由 ~3×5px 变 ~6×10px；drift 带由 faint 点线变为可见草线。**面数：整改前 393,632 → 整改后 397,112（+3,480，全是色带切段），≤400k，余量 2,888，未超预算。** 禁入椭圆一字不动：GLB 回读核对色带/tevy 落在新跑道椭圆（中心 (-62,-25)、rx29/ry41，含 +1m）内 0 个、池塘椭圆（中心 (82,-78)、rx12/ry9）内 0 个，与 T18 旧版同样 0 个；注：初版探针误把 glTF Y-up 坐标当 Blender 坐标读（取 translation[1] 当 y），曾误报 64 块越界，已按 glTF→Blender 映射（x, y, z）=（tx, −tz, ty）更正为 0。
- **重建**：本地 Blender 4.2.0 一次运行（`~/workspace/review-rework-r2/r2t51/ov-lawn-r2t51.log`，2026-11-25 06:55 CST）：`blender_exit=0`、`DONE ov-lawn`，**0 Error / 0 Traceback**；SLABS 453 块 / 22,472 m² / 5,436 tris；tevy 370 丛 / 153,400 面，分区 lod2 与 T18 分毫不差（G1 64 / G2 65 / G3 96 / G4 29 / G5 21 / G6 36 / G7 15，hero lod0 2 / lod1 10 / lod2 14）；GLB 回读 **9,092 对象 / 397,112 tris / 975,274 verts**，断言 `≤400000` 通过；GLB 内 tevy lod2 实例 scale x 1.50–2.00（均值 1.75）、lod1 1.26–1.64，与放大表一致；旧草坪/花坛/灌木/边缘真草一字未动（tevy 分区数与 T18 相同即证）。`.blend` 29,197,324 B、`.glb` 23,861,724 B，均 <40MB。
- **推仓**：commit `5508bc60`（`5508bc6052a5ccaf60601563636a4290f93cde9f`，父 `73892b81`，2026-11-24T22:59:34Z）：1 批 push-files，6 文件（ov-lawn.py blob `9036efee` 65,729 B、ov-lawn.blend blob `11b132b9` 29,197,324 B、ov-lawn.glb blob `32a74c8a` 23,861,724 B、3 张色带 PNG blob `f79631d2`/`06830b48`/`06b83cb7` 各 156 B）；推前重读 HEAD 已是 `73892b81`（任务书给的 `187e3a4a` 之后 R2-T46 已推 `73892b81`，父即 `187e3a4a`，教室补光、未动 ov-lawn 任何文件——推前逐文件核对 6 个 blob 与 `187e3a4a` 版一字相同，无撞车）；推后核对：HEAD 即 `5508bc60`、父链连续、6 个 blob SHA 与本地逐项一致。触发 blender-previews run **#119 / 45505991244**（head `5508bc60`，2026-11-24T22:59:38Z 起，查时 in_progress）。
- **验证**：blender-previews run **#119 / 45505991244**（head `5508bc60`）：**completed/success，6 job 全绿**，约 70 分钟（22:59:38Z→00:09:36Z）；artifact `blender-previews-overview`（17,955,322 B）20 张已下载逐项核对——`ov-lawn.png` 一眼可见变化：整片草地由旧版淡绿条纹变为深绿/浅绿/黄绿三色 4m×16m 棋盘格，drift 带点状草线沿带可见，池塘环深绿弧、两块旧草坪深绿区、花坛与边缘真草都在，新跑道/球场禁入区干净无草；**前后像素对比（同口径，#113→#119）**：草色掩码 10.56%→10.48%（覆盖面积不变）；有纹理块 std≥3 占比 82.6%→**89.3%**、std≥6 占比 23.7%→**78.9%**（+55.2pt）、std≥10 占比 8.7%→**70.8%**（+62.1pt）；草色 G 标准差 12.4→**22.0**（近翻倍）；色带双峰由 170–175/180–185（ΔG≈10）变为 145–150/190–195（**ΔG≈45**，约 4.5 倍），C 黄绿档在 180–190 一带可辨；深绿（G<135）占比 2.26%→3.44%，草丛暗像素（G<120 且 G>R+15）1.27%（1,231px）→1.51%（1,462px）。**全量品红扫描：20 张图品红像素 0**（ov-lawn 0，黑像素 0；仅 canteen 2px、dorm 11px 黑点，与本件无关）。**结论：单件图验收通过，草在单件尺度下明显可见；总览视角仍待 T52 复验（见下）。**
- **还剩什么**：**总览视角待 T52 复验**——本轮只改了 ov-lawn 单件，总览 GLB 仍是旧版（审计③），在 T52 重拼总览出图之前不许声称总览已确认；单件图前后像素对比见验证节。
- **编号说明**：本节即 §52（§49=R2-T48、§50=R2-T49、§51=R2-T50、§48 已是 R2-T47、§47 已是 R2-T46；初版写前已查远端 HEAD `73892b81` 的仓库版文档确认 §49/§50/§51/§52 均未入仓、§52 空闲，远端文档 blob `3cef6811`、418,781 B）；**合入说明（防撞车）**：本节初版（含“验证：待填”）在 R2-T50 的 commit `f7145a6e` 推仓时被顺带推上远端（共享工作目录的本地文档被其 push-files 读到），本次推仓前重读远端 HEAD `47b970dd` 的仓库版文档确认本地与远端逐字节一致（457,183 B、blob `2a1ef319`，§51/§52 全文在位），本次只改本节“验证”一行（补填 #119 结论）与本编号说明行，其余章节、§51 全文一字未动；只改 ov-lawn 一件（.py/.blend/.glb + 3 张色带 PNG）+ 本节，未拼总览、未动 Godot、未动其他件；审计证据（#113 artifact、#142 截图、远端 overview.glb、像素分析脚本）与重建日志只放 `~/workspace/review-rework-r2/r2t51/`，不推仓。

## §50 R2-T49 run #116/#117/#118 结论跟进（2026-11-25，只跟进、不改模型、不重建、不拼总览）

- **背景**：三路 `Blender previews (max quality)` run 由已完工任务触发、触发者未等结果，本任务终轮跟进结论；三路均为 push 触发。
- **#116 / 45499984974**（head `56bfb69f`，R2-T40 删除 42 张零引用烘焙图后触发，2026-11-24T22:20:23Z 起）：completed **success**（2026-11-24T23:15:15Z，约 55 分钟）；6/6 job 全绿：overview（138820381109）、dist（138820381429）、storage（138820381576）、pv（138820381636）、charge（138820381709）、classroom（138820381715）。
- **#117 / 45500394665**（head `7d97b75c`，R2-T45 verify_slim.py 退出码修复后触发，2026-11-24T22:22:56Z 起）：completed **success**（2026-11-24T23:15:31Z，约 53 分钟）；6/6 job 全绿：overview（138821818406）、pv（138821818827）、storage（138821818927）、classroom（138821819025）、charge（138821819056）、dist（138821819113）。只改校验脚本 + 文档，无回归。
- **#118 / 45502232523**（head `03bd7510`，R2-T47 只改 ov-road-walk.py 两行注释后触发，2026-11-24T22:34:42Z 起）：completed **success**（2026-11-24T23:28:40Z，约 54 分钟）；6/6 job 全绿：classroom（138828200121）、pv（138828200334）、overview（138828200441）、dist（138828200495）、charge（138828200589）、storage（138828200631）。只改注释，无回归。
- **Artifact 目视**：三路 `blender-previews-overview` artifact 各含 20 张 1280×720 PNG（#116 artifact 14972209336、17,942,757 B；#117 artifact 14974105599、17,942,476 B；#118 artifact 14975890042、17,944,494 B）。#116 逐张看过 20/20：gym/lab/canteen 三件完整带烘焙贴图、无缺件；ov-lawn 总览地坪完整；其余 tower/dorm/lib/bldA/bldB/bldC/field/flag-lamp/gate/parking/road-main/road-walk/track/transformer/trees/windows-roofs 均正常——删 42 张图未影响渲染。#117 抽查 gym/lab/canteen/lawn、#118 抽查 gym/lab/canteen/road-walk/lawn，均与 #116 视觉一致，无回归。注：artifact 内无单张合成全景图，overview 组出图即这 20 张分件渲染；ov-lawn 为全站地坪总览。
- **品红扫描**（R>150、G<140、B>150）：三路 60 张全量扫描，品红像素均为 0。PNG 字节三路互不相同（Blender 重渲染噪声），同名文件大小三路相差 <0.1%，非回归信号。
- **推仓**：commit `5c5659eb`（`5c5659eb8cc83aeeb9410a440389e68589cfa68f`，父 `384ea9d5`，2026-11-24T23:34:31Z）：1 批 push-files，1 文件（BLENDER_MODELS.md blob `a7b0ff88` 444,630 B，单 blob <40MB）；推后核对：HEAD 即 `5c5659eb`、父链连续、远端文档 blob SHA 与本地一致、内容与本地逐字节一致、含 §50 全文。本行系推后补填，随第二次推送（仅本文档）入仓。
- **编号说明**：本节即 §50（§41 已是 R2-T40、§42 已是 R2-T41、§43 已是 R2-T42、§44 已是 R2-T43、§45 已是 R2-T44、§46 已是 R2-T45、§47 已是 R2-T46、§48 已是 R2-T47、§49 已派给 R2-T48、§51 已是 R2-T50、§52 已是 R2-T51；写前已查远端 HEAD `384ea9d5` 的仓库版文档确认 §49/§50 均未入仓、§50 空闲，远端文档 blob `dbdfaca3`、266,438 B，本地算出的 blob SHA 与远端一致；本地版只到 §48 已过期，基底直接取远端版全文追加，未覆盖他人章节）；§24/§29/§33 一字未动；只跟进结论 + 本节，未动模型、未重建、未拼总览；artifact 与扫描脚本只放 /tmp/r2t49/，不推仓。

## §49 R2-T48 bldA 裙座盖面修复：plinth/plinth_cap 改周圈窄环（2026-11-25，只改 ov-bldA 一件 + 本节，不推总览 GLB 到 main）

- **任务**：执行 R2-T41 §42 修复建议①：教学楼 A 的实心裙座顶盖埋住一层教室全部桌椅腿（腿 y[0,0.67] 全在 0.68 盖面之下、桌面顶 y=0.70 在面之上 0.02，只盖腿、不盖桌面）。只修 ov-bldA 一件，楼体尺寸/量体一字不动；不改腿管加粗/换色、不动机位/光照。探针分支上本地重拼总览验证，**不推总览 GLB 到 main**（终轮整合做权威重拼）。
- **修前核对（Blender 4.2.0 面级探针，修前 `ov-bldA.blend`，教室体积 Blender x[−60.84,−51.16]、y[26.37,33.63]、z[0,3.5]；水平面判据 |nz|>0.99、z≥0.5−1e-3、XY 与教室矩形相交）**：`bldA_plinth` 顶盖 z=0.500、1 面 628.87 m²；`bldA_plinth_cap` 顶盖 z=0.680、1 面 635.61 m²（另有底盖 z=0.500、1 面 635.61 m²，与 plinth 顶盖共面、夹在实心叠层内，不可见）；两盖面均为整幅足迹面，全幅覆盖教室。余下面：`office-building_body` 入口雨棚片 z=2.609/2.96（65 面、共 13.5 m²，南缘小片 x[−59.34,−56.05]、y[25.11,27.19]，见下条）、`office-building_shell` 底盖 z=3.913（2 面 425.92 m²，在教室顶 3.5 之上）、`bldA_roof_slab` z=18.1/18.35（屋顶，与教室无关）。另：探针阈值须带 epsilon——cap 底盖世界 z 是 0.5−浮点误差（0.4999999…），无 epsilon 的 `z<0.5` 会把它漏掉（本次初版探针即漏报，复核已纠正；修前实为 72 面次，修后 69 面次）。
- **关键发现：`bldA_body_F1_F4` 在现版 ov-bldA 里不存在**：§42 的第三道盖（底盖 z=0.500）是旧 v2 实心楼体的残留，只在 2026-11-24 15:35 拼出的总览 .glb 里（当时 `ov-bldA.blend` 有 225 件，`APPEND ov-bldA src=225 kept=222`；现版总览 .glb 节点 13,217、含 `bldA_body_F1_F4`、0 个 `office-building_*` 节点）。现版 ov-bldA v3（R2-T21a 换装，Grab3D 办公楼）`.blend` 只有 24 件，无此对象；任务单“删底盖”一项因此无物可删——本次重拼总览即随之消失（探针总览 GLB JSON 已核对：`bldA_body_F1_F4` 不在）。楼体三件（`office-building_body/facade/shell`）一字未动。
- **修法（`assets/blender/overview/ov-bldA.py`，只改此文件两处调用 + 新增 `ring()`）**：`bldA_plinth` / `bldA_plinth_cap` 由实心盒改矩形环棱柱（bmesh 单 mesh，顶/底各 4 梯形 + 外墙 4 + 内墙 4，共 16 面，无拼合内含面；bevel 与旧 `box()` 同款 EdgeSoft ANGLE）。外框/高度/材质一字未动：勒脚外 40.6×15.6、z 0–0.5、混凝土 `Concrete_B9B3A8_tex`、bevel 0.04，内空 40×15（=楼体足迹），带宽 0.30；压顶外 40.7×15.7、z 0.5–0.68、檐口 `Cornice_D8D2C4_tex`、bevel 0.03，内空 40×15，带宽 0.35。顶面只剩周圈窄条（bevel 后平顶宽 0.22/0.29m）。各楼 plinth **未**一并改环（§42②“可顺手”未做：只动 ov-bldA 一件，其余楼无内景、不急，留后任务）；对象数、对象名、材质一字未动。
- **重建（Blender 4.2.0，`~/workspace/review-rework-r2/r2t48/ov-bldA-r2t48.log`）**：EXIT=0、**0 Error / 0 Traceback**、`DONE ov-bldA`；`built objects: 24`、GLB 回读 24 对象。`.blend` 9,750,555 B、`.glb` 7,079,152 B（旧 9,749,635 B / 7,062,004 B）。**回读核对**：24 件包围盒与修前逐项一字相同（含 plinth x[−76.30,−35.70] y[22.20,37.80] z[0.00,0.50]、cap x[−76.35,−35.65] y[22.15,37.85] z[0.50,0.68]，外框未动）；GLB JSON 24 节点 / 24 mesh / 8 材质，plinth/cap 在位、无 `bldA_body_F1_F4`。面级探针（同口径）：**plinth/cap 0 面**——两盖面清零；顶面只剩周圈带：勒脚 4 面 z=0.5（n=+1，2×8.87+2×3.37=24.48 m²）、压顶 4 面 z=0.68（n=+1，2×11.70+2×4.45=32.30 m²），法线 +Z/−Z 正确；底面只在环带上（勒脚 z=0、压顶 z=0.5）。教室体积内 z[0.5,3.5] 水平面只剩雨棚片 63 面（修前 65 面，差 2 面是修前探针把两张 0.00 m² 退化三角面重复计了两次，同一片、同 z、同面积）。
- **雨棚片无害证明（未动它：它是 Grab3D 模型自带入口雨棚，可见外饰，删面会改外观）**：雨棚片在 z=2.609/2.96、x[−59.34,−56.05]、y[25.11,27.19]；03 相机 Godot (−54.51,2.75,−29.20)（target (−59.0,0.9,−30.2)、az 1.352、el 0.382、dist 4.96，按 `verify_fixes.gd` 相机公式算得），距雨棚片 XY 最近 2.53m；任何相机→腿（z≤0.67）的视线在该水平距离上已降到 z≤2.07（最浅一条：到最远腿角 D=7.73m、z=2.75−2.53×(2.08/7.73)=2.07），恒在 2.609 之下，不可能穿过雨棚片。CI 03 取样是实证（见下条 53/74，与藏起三件的 #141 逐数相同）。
- **探针分支验证（只在探针分支/本地做，总览 GLB 不推 main）**：分支 `r2t48-plinth-ring-probe`（基 main HEAD `f7145a6e`，R2-T50 §51），commit `1827ed4c`（`1827ed4ca3ddb0f14916e76f65d61335dfc43055`，父 `f7145a6e`，2026-11-24T23:10:03Z）：1 批 push-files，4 文件（`ov-bldA.py` blob `ad63bcc4` 17,306 B、`ov-bldA.blend` blob `ee98fe86` 9,750,555 B、`ov-bldA.glb` blob `7013d895` 7,079,152 B、瘦身总览 GLB `assets/models/scenes/overview.glb` blob `e29c4e37` 40,467,380 B，单 blob 均 <46MB）；推后核对：分支 HEAD 即 `1827ed4c`、父链连续、contents API 逐文件核对大小与 blob SHA 与本地逐项一致。注：首推 40.47MB blob 遇 HTTP 502 `Server Error`（GitHub 侧临时错误，§10 同款），重试一次即成功；40MB 文件 OK、46MB 报 422 的实测阈值仍成立（40.47MB 在 40–46MB 区间内被接受）。本地探针总览重拼（`assets/blender/scenes/overview.py`，`~/workspace/review-rework-r2/r2t48/overview-refresh-r2t48.log`，EXIT=0、0 Error/Traceback）：`APPEND ov-bldA src=24 kept=24`、`SCENE objects=12312`（append 12,308 + 拼装 4；由 13,217 降 905：bldA 222→24、ov-windows-roofs kept 127→45、ov-trees/ov-lawn 为 R2-T43/R2-T51 现版）；探针总览面级核对：教室体积内 z[0.5,3.5] 水平面只剩雨棚片 63 面，`bldA_body_F1_F4` 已无。瘦身（§10 口径，`slim_glb.py`）：完整版 94,758,908 B → 瘦身版 **40,467,380 B**（69 张 color→JPEG512 q80、87 张 normal/mr→PNG256、6 张 alpha→PNG512、27 张原字节保留）；`verify_slim.py` 全绿（`~/workspace/review-rework-r2/r2t48/verify-slim-r2t48.log`，EXIT=0、`DONE verify_slim`：瘦身 GLB 12,312 对象 / 12,308 mesh / 0 无材质 primitive；完整版 12,312 对象；瘦身 .blend 12,312 对象 / 306 贴图 / 缺失 0）。瘦身 .blend 76,160,026 B 超 blob 上限未推（探针分支只推瘦身 GLB，不推 .blend；Godot 侧只用 .glb）。另：探针总览由当前各件 .blend 重拼，含 R2-T50 树高与 R2-T51 草地棋盘（非本次改动；探针基 `f7145a6e` 已含 R2-T50，拼装时本地 ov-trees 还是 R2-T50 之前版，树高以分支版为准）。
- **CI 验证（探针分支）**：godot-verify run **#146 / 45507594582**（head `1827ed4c`，push 触发，2026-11-24T23:10:07Z–23:28:35Z）：**success**；job `138846706412 verify-export success`；**VERIFY-SUMMARY: PASS=271 FAIL=0**（与 #141 相同）；artifact `godot-screenshots`（10,703,939 B，20 张）已下载。
- **03 取样（`r2t38_sample.py`，§38 同款取样器与阈值）**：黑板中心投影 **(575,207)**，与 #130/#140/#141 1px 级一致（机位未动）；**桌柱 53/74 暗（71%），柱中点 RGB 均值 (111,108,93)；椅柱 40/65 暗（61%），(173,159,134)**——与 #141（藏起三件）逐数相同（桌柱 R 差 1：111 vs 112，G/B 一字相同），验收阈值 ≥53/74 **达成**；对照 #130 基线桌柱 5/74（7%）、(185,185,162)。**目视**：03 全图逐张看过——每张桌下 4 条黑腿 + 横撑清晰落地、椅腿亦可见，蓝色地砖地面恢复可见，不再是悬浮薄板。**00-overview 目视**：bldA 壳体回来（“一号教学楼”标签下蓝玻璃楼体在位，与 #141 藏起态的空地不同），与 main 最新 run #142（head `f573508d`）的 00-overview 裁图逐像素比对：bldA 楼体、屋顶、基座一字相同，无草槽、无缺口、无移位；帧内其余差异均来自同期他任务的件（R2-T51 草地棋盘、R2-T50 树高、tower 立面），与本次环改无关。blender-previews run **#121 / 45507594417**（探针分支，push 触发）写本节时仍 in_progress，ov-bldA 单件渲染图未等（环几何已由面级探针实数核对，不依赖它）。
- **推仓（main）**：commit `c2364b87`（`c2364b879a1d055edc0379a9c4d1201ac9c49c84`，父 `07d48f58`，2026-11-24T23:37:07Z）：1 批 push-files，4 文件（`ov-bldA.py` blob `ad63bcc4` 17,306 B、`ov-bldA.blend` blob `ee98fe86` 9,750,555 B、`ov-bldA.glb` blob `7013d895` 7,079,152 B、BLENDER_MODELS.md blob `9d150870` 455,335 B，单 blob 均 <40MB）；推后核对：HEAD 即 `c2364b87`、父链连续、contents API 逐文件核对大小与 blob SHA 与本地逐项一致、远端文档含 §49 全文且 §50 一字未动。只推 ov-bldA 三件 + 本文档，未推总览 GLB。注：本次推送触发 main 上新的 godot-verify / blender-previews run（未等结果）——main 的总览 GLB 仍是 R2-T1b 旧版（含实心裙座），其 03 取样仍会是旧数，属预期，验收以探针分支 #146 为准，待终轮重拼后在 main 上复验。本行系推后补填，随第二次推送（仅本文档）入仓。
- **还剩什么**：① 终轮整合做权威重拼（探针总览 GLB 只在分支上，main 的总览 GLB 仍是 R2-T1b 瘦身版、含旧 v2 bldA 残留 `bldA_body_F1_F4` 与实心裙座，本次只把修复后的 ov-bldA 三件 + 本节推 main；终轮重拼后 03 须在 main 上复验 ≥53/74、00-overview 复验 bldA 外观）；② 各楼实心裙座未动（bldB/bldC/lib/gym/lab/tower/canteen/dormA/dormB 仍是实心 plinth/plinth_cap，只 bldA 足迹内有教室、只此处致病，其余楼无内景、不急，留后任务按本节 `ring()` 同款改）；③ 雨棚片（z=2.609/2.96，63 面）仍在（已证无害，不动）；④ 探针分支 `r2t48-plinth-ring-probe` 保留作证据（#146）；⑤ 本地完整版总览 .glb/.blend 现为探针重拼输出（本地留存，未推 main；瘦身临时文件 `overview-slim.glb`/`.blend` 推完已删）。
- **编号说明**：本节即 §49（§47 已是 R2-T46、§48 已是 R2-T47、§50 已是 R2-T49、§51 已是 R2-T50、§52 已是 R2-T51；写前已查远端 HEAD `07d48f58` 的仓库版文档确认 §49 空闲，远端文档 blob `02239197`、445,028 B，本地推前版 = 远端版 + 本节（§50 已是 R2-T49，随本次一并入仓、内容未动））；§24/§29/§33 一字未动；只改 ov-bldA 一件（`.py` / `.blend` / `.glb` + 本节）+ 探针分支（总览 GLB 只在分支上），未动机位、未动光照、未动腿管、未动其他楼；探针脚本、交集/面级 JSON、job 日志与截图只放 `~/workspace/review-rework-r2/r2t48/`，不推仓。
