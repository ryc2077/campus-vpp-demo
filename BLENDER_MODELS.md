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
| ov-road-main | 主干道（环校主路 + 东侧、南侧主路，沥青 + 黄色中心线 + 路缘石） | `_build_roads` | overview | **烘焙完成**（2026-11-23 00:20 CST：Asphalt/YellowLine/Curb 各 3 张，61 分钟；回读 33/33。**已返工 UV 分瓦片**（2026-11-23 04:13 CST：照抄 road-walk/track 的 `_pack_uvs`，Asphalt 10 对象→4×3 瓦片、YellowLine 2→2×1、Curb 21→5×5，烘焙 384.2s、全程约 6 分 49 秒；新 .glb 802,176 B、回读 33、3 材质各 3 张贴图齐全）。**已修沥青纯色+补环路中心线**（2026-11-23 06:59 CST：根因是 DIFFUSE 烘焙只取 Base Color、管线为保 glTF baseColorFactor 刻意不链接底色，color 图只能是平底色（唯一色 70、非黑区标准差仅 1.96），颗粒只走 Bump 但法线图也几乎是平的；材质链接本身没问题。修法：烘焙前把颗粒/磨损以 MixRGB 乘进 Base Color（重建时会删节点只连烘焙贴图，glTF 不受影响），Bump 加强 0.4→0.9、distance 0.08→0.20；第二轮重烘顶面标准差 1.8→4.1~4.4、Asphalt 唯一色 70→337、Curb 140→882、黄线 9→187、法线 R/G 标准差 1→9.04/8.61。环路中心线原为 0 个对象（.py 旧设计称“按鸟瞰图不画黄线”，但内环路基本被楼体遮挡、说法站不住），按 SPEC §5 补 8 个对象（4 直段＋4 拐角斜段）。对象 33→41，回读 41，DONE ov-road-main） **返工 R2-T14b（2026-11-24）**：环校路内缘路缘石在 5 处新路口断开（R-N1 两端 y 42.5..45.5、R-N2 口 x -34.5..-31.5、R-N3 口 56.5..59.5、R-N4 spur 口 66.7..69.3、R-N4 东接口 y -70..-68），内缘 S/W/E 由 3 条整段改为 4+2+3 段分段；.blend 实测断口与新步道口同宽（S_0..S_3、W_0..W_1、E_0..E_2 位置尺寸均与设计一致）。重建：烘焙 9/9（384.3s），回读 47/47（.blend 另含预览地面/太阳/相机 3 件，共 50 对象），3 材质 base/rough/normal 齐全、9 张贴图具名；.glb 7,181,756 B；Curb 烘焙图 3 张更新。本件 .py 同补 R2-T14b PBR 路径修正（见 ov-road-walk 行）。 **品红修复跟进（2026-11-24，R2-T14b）**：run 45440253728 目视本件全路品红（5.8%）；根因已查实：仓库版 .blend 9 张图全未打包（packed: False，尺寸 0×0），且 PBR 源文件（pbr-tinted/* 等）不在仓库，runner 检出后找不到文件；对照：打包版 bldA（16/16 打包）同批渲染正常，未打包但贴图文件在仓的 track/lawn 也正常。R2-T9b 18:56 已补打包 8 个 .blend（含本件）并推仓（commit 7eec73f8），仓库版 .blend 现与本地打包版 SHA 一致；本件 .py 另补存盘前打包步骤（与 ov-tower.py 同款），防下次重建复发。 |
| ov-road-walk | 步道与铺装（南门广场浅色铺装、楼间步道、路缘） | `_build_roads` 铺装部分 | overview | **烘焙完成**（2026-11-23 03:35 CST：7 材质各 3 张，28 分钟；回读 149/149。UV 分瓦片后从 111 分钟被杀→28 分钟跑完） **返工 R2-T14b（2026-11-24，R2-T14 续跑）**：接半成品——前任已把 6 条新路（R-N1/R-N2/R-N3/R-N3x/R-N4/R-N5，约 438m）与路缘全部写进 .py，但 .blend/.glb 仍是 11-22 旧版（149 对象、0 条新路），重建被运行时重启中断。几何复核全过：R-N3 距配电房东墙 0.5m、储能围栏 0.5m/平台 1.0m（方案写的 0.2m 是另一口径，实测更宽松，无需改线）、R-N2 距操场缓冲 2.5m/bldA 东墙 1.5m、R-N1 距 tower 南墙 1.5m、R-N5 距 bldB/bldC 各 4m、R-N4 spur 在池塘+0.5m 椭圆外（最小归一化值 1.44）。重建：烘焙 24/24（首跑 1910.8s、复核重跑 648.9s）；首跑在回读断言失败——_pbr_apply 的 relpath 以 CWD 为基准，CWD=工程根时 PBR 贴图写成 //assets/...（应为 //../../assets/...），GLB 里 6 种 PBR 材质只剩 1 张空白图（已实测复现）；已在两件 .py 的 hook 后加路径修正（.blend 所在目录 + CWD 双候选解析、幂等），并用同逻辑修复已存 .blend 后重出 .glb；为验证 .py 自洽又全量重跑一遍，DONE，复核重跑出的 .glb 与修复版字节相同（sha256 ecefcfc6…）。回读 171/171（旧 149，+22 件新路对象），8 材质 base/rough/normal 齐全、15 张贴图具名；.glb 11,029,616 B；Curb 烘焙图 3 张更新、PavingNew 三件套 3 张新增。 **品红修复跟进（2026-11-24，R2-T14b）**：run 45440253728 目视本件全幅品红；根因同 ov-road-main 行：仓库版 .blend 15 张图全未打包，PBR 源文件不在仓库；R2-T9b 18:56 补打包并推仓（commit 7eec73f8），仓库版 .blend 现与本地打包版 SHA 一致；本件 .py 另补存盘前打包步骤（与 ov-tower.py 同款），防下次重建复发。验证待 run 45464884225（head 7eec73f8）overview 组出图后逐张目视。 |
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
- **本次推仓**：待填（8 个打包 .blend + bldC .glb + 3 个 .py + 本文档，推后补 commit 号与核对结果；该 push 会触发新的 blender-previews，届时以新 run 复验品红是否消失 + bldC PBR 是否可见）。
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
- **推仓**：待填（推后补 commit 号与核对结果）。
- **验证**：待填（blender-previews overview 组 run 号 + ov-windows-roofs.png 目视结论；godot-verify 总览验收由终轮整合做）。
- **还剩什么**：① 总览重拼 + Godot 侧验收由终轮整合做；② 本件预览相机仍框 A 栋南立面（仅预览衬底，不导出），Actions 的 ov-windows-roofs.png 将显示无窗的 A 栋示意量块 + 屋顶细部，C 栋窗带不在该取景内，属修法本意、不另改取景；③ 旧 A/B 窗带几何已从脚本删去，如终轮整合想恢复 A/B 窗带需按新幕墙面重做、不可直接 revert。
