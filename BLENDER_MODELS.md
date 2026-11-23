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
| ov-gym | 艺体馆 36×16×18m，3 层 | `_build_building(gym)` | overview | **烘焙完成**（2026-11-23 01:58 CST：18 张，6/6 全套；.glb 已重出，回读 192） |
| ov-lab | 实验楼 42×12×13m，3 层 | `_build_building(lab)` | overview | **烘焙完成**（2026-11-23 04:59 CST：36 张，12/12 全套；.glb 已重出，回读 358） |
| ov-tower | 创造力中心 14×14×32m，8 层（窗带已修复：79 段，666 个窗带对象） | `_build_building(tower)` | overview | **烘焙完成**（2026-11-23 07:50 CST：42 张，14/14 全套；.glb 已重出，回读 929） |
| ov-canteen | 餐厅 32×13×15m，3 层 | `_build_building(canteen)` | overview | **烘焙完成**（2026-11-23 08:44 CST：33 张，11/11 全套；.glb 已重出，回读 322） |
| ov-dorm | 宿舍 A、B 两栋，各 20×12×16m，5 层（总高 16.40m，见 §5.5） | `_build_building(dormA)` + `_build_building(dormB)` | overview | **烘焙完成**（2026-11-23 11:14 CST：45 张，15/15 全套；.glb 已重出，回读 739） |
| ov-road-main | 主干道（环校主路 + 东侧、南侧主路，沥青 + 黄色中心线 + 路缘石） | `_build_roads` | overview | **烘焙完成**（2026-11-23 00:20 CST：Asphalt/YellowLine/Curb 各 3 张，61 分钟；回读 33/33。**已返工 UV 分瓦片**（2026-11-23 04:13 CST：照抄 road-walk/track 的 `_pack_uvs`，Asphalt 10 对象→4×3 瓦片、YellowLine 2→2×1、Curb 21→5×5，烘焙 384.2s、全程约 6 分 49 秒；新 .glb 802,176 B、回读 33、3 材质各 3 张贴图齐全）。**已修沥青纯色+补环路中心线**（2026-11-23 06:59 CST：根因是 DIFFUSE 烘焙只取 Base Color、管线为保 glTF baseColorFactor 刻意不链接底色，color 图只能是平底色（唯一色 70、非黑区标准差仅 1.96），颗粒只走 Bump 但法线图也几乎是平的；材质链接本身没问题。修法：烘焙前把颗粒/磨损以 MixRGB 乘进 Base Color（重建时会删节点只连烘焙贴图，glTF 不受影响），Bump 加强 0.4→0.9、distance 0.08→0.20；第二轮重烘顶面标准差 1.8→4.1~4.4、Asphalt 唯一色 70→337、Curb 140→882、黄线 9→187、法线 R/G 标准差 1→9.04/8.61。环路中心线原为 0 个对象（.py 旧设计称“按鸟瞰图不画黄线”，但内环路基本被楼体遮挡、说法站不住），按 SPEC §5 补 8 个对象（4 直段＋4 拐角斜段）。对象 33→41，回读 41，DONE ov-road-main） |
| ov-road-walk | 步道与铺装（南门广场浅色铺装、楼间步道、路缘） | `_build_roads` 铺装部分 | overview | **烘焙完成**（2026-11-23 03:35 CST：7 材质各 3 张，28 分钟；回读 149/149。UV 分瓦片后从 111 分钟被杀→28 分钟跑完） |
| ov-track | 操场跑道（400m 椭圆，跑道红 + 白色分道线，中心 (-80,-25)，rx40 rz28） | `_build_playground` 跑道环 | overview | **烘焙完成**（2026-11-23 03:38 CST：Track_Red/LaneLine/Curb 各 3 张，约 2 分钟；回读 17/17） |
| ov-field | 球场与看台（跑道内侧条纹足球场、球门、简易看台） | `_build_playground` 场内 | overview | **烘焙完成**（2026-11-23 03:47 CST：深/浅草皮/白线/门框/看台各 3 张，约 4 分钟；回读 30/30。半透明球网按设计跳过） |
| ov-trees | 树木（校园周边密植树带 + 东侧路旁行道树） | `_build_trees` | overview | Bump-only（小件保底） |
| ov-lawn | 草坪花坛（大面积草地、门前花坛、灌木球；v3 加密版草） | `_build_ground` 草地部分 | overview | **烘焙完成**（2026-11-23 04:04 CST：Lawn_Green/边框/土面/3 色花/灌木各 3 张，16 分钟；回读 129/129，111,917 tris。6 种草叶程序化保留；烘焙范围含花坛边框等，见 §5.1 待确认项） |
| ov-flag-lamp | 旗杆路灯（南门广场 3 根旗杆、沿路路灯杆） | `_build_flag_and_gate` | overview | Bump-only |
| ov-gate | 校门（南门门楼 + 门柱 + 伸缩门示意 + 围墙一段） | `_build_flag_and_gate` | overview | Bump-only |
| ov-parking | 停车区（南门广场旁停车位划线 + 3 辆简易小车） | Godot 无对应程序化模型（新增细节） | overview | **PBR 已挂**（Paint* 三件套）+ **返工 R1**（2026-11-24，验收 run #72：本件车漆从未挂清漆，GLB 实测无 KHR_materials_clearcoat——060877f4 只给 ch-cars 挂了；make_car 挂图后补 Coat Weight 1.0 / Coat Roughness 0.05，车窗加细噪波 Bump、粗糙度 0.06→0.05；回读 233，零 Error/Traceback）**返工 R2**（2026-11-24：与 ch-cars 同因同修，.blend 留 Nishita 天空世界；回读 233，零 Error/Traceback）**返工 R3**（2026-11-24：与 ch-cars 同根因同修（见 §9），预览环境加暗色地面 Ground_PreviewOnly + 东南太阳 + 西北 24×2m 亮条灯（15000）；本地验证三车顶均有亮度起伏；GLB blob 与仓库相同未推。回读 236，零 Error/Traceback） |
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
| st-fence | 围栏标识（三面围栏 + “高压危险”标识牌） | Godot 无围栏（新增细节） | storage | **PBR 已挂**（返工 R1，2026-11-24，验收 run #72：围栏内 4 台柜与地面用的本件自建 Preview_* 纯色材质，与 st-cabinet 的锈蚀 PBR 根本不是同一材质；柜体复用 st-cabinet_textures 锈蚀三件套、地面复用 st-base_textures 混凝土三件套，地面 UV 按 2m 平铺 x15；无新素材。预览物不进 GLB、不进 storage 场景。回读 36，零 Error/Traceback） |

### 3.4 教室内部（局部坐标：房间中心原点，x=长 9.68m，y=宽 7.26m，z 0–3.0m；黑板墙 x=-4.84，窗户沿 y=-3.63，门在 x=+4.84 墙上）

| 件 ID | 内容 | Godot 对应 | 场景 | 纹理管线 |
|---|---|---|---|---|
| cl-floor-walls | 地面墙面（浅色地砖地面、四面墙、踢脚线、天花板） | `classroom_interior.gd._build` 地面/墙面/天花板 | classroom | Bump-only |
| cl-desks | 桌椅（6 列 × 8 排课桌椅，48 套，留讲台前空地与过道）— **tevy 换件已完成**（见本节下注） | `classroom_interior.gd` 桌椅 | classroom | Bump-only（tevy 拆件 + 自家 CC0 染色贴图，见 cl-desks.py 头注） |
| cl-board | 讲台黑板（黑板墨绿 + 讲台桌 + 粉笔槽） | `classroom_interior.gd` 黑板 + 讲台 | classroom | Bump-only |
| cl-ac | 空调（2 台美的 5 匹柜机 KFR-120LW，白，约 0.6×0.4×1.8m） | `classroom_interior.gd` 空调 | classroom | Bump-only |
| cl-lights | 灯具（天花板 2 排日光灯管 + 吊杆） | `classroom_interior.gd` 灯具 | classroom | Bump-only |
| cl-windows | 窗户窗帘（南侧 4 扇大窗 + 浅色窗帘）+ **门（tevy 拆件，见本节下注）** | `classroom_interior.gd` 窗户 | classroom | Bump-only |

**tevy 教室换件已完成**（2026-11-23，commits `cf0d432`、`c2d99fa`、`e2bce23`、`5d0e1fc`、`c046118`）：桌椅换成 tevy 现成模型拆件（CC0，tevy.dev/models/classroom；原模型三重压缩 Blender 4.2 打不开，已用 gltf-transform 去压缩并剥掉 KTX2 贴图，见 `assets/external/buildings/tevy-decompress.mjs`）。桌：12 张双人桌 → 24 张单桌循环复用 48 套；椅：20 张单椅中 4 张被高柜面污染（柜面与椅背共面、y 只差 0.02–0.04m，切不干净）不进复用池，其余 16 张干净单椅循环复用 48 套。48 套间隙前 0.208m / 后 0.204m（commit `e2bce23`）。门装进 cl-windows.py（tevy 门 + 门框，commit `5d0e1fc`）。讲台桌 / 书架 / 高柜未采用：讲台桌进深 1.25m 是 SPEC 讲台 0.62m 的两倍，会吃掉讲台前空地并顶住第一排桌；书架（4.48m 长柜）无 SPEC 位置，放北墙会挡窗；高柜与椅背共面切不干净（见上）。classroom 场景 440 对象（原 436，+门 1 +填缝 3），见 §4。

### 3.5 充电区 V2G（全局坐标，Blender 中心 (44,-76)）

| 件 ID | 内容 | Godot 对应 | 场景 | 纹理管线 |
|---|---|---|---|---|
| ch-piles | 充电桩（4 台直流桩一字排开，白 + 充电枪线） | `campus_builder._build_charge` 充电桩 + `charge_detail.gd` | charge | Bump-only |
| ch-cars | 车辆（3 辆简易小车，蓝/红/白，2 辆 V2G 在桩前） | `_build_charge` 车辆 + `charge_detail.gd` | charge | **PBR（参数化清漆）已挂**（commit `060877f`：3 台车共用参数化清漆，Metallic 0.15 / Roughness 0.35、Coat Weight 1.0 / Coat Roughness 0.15，GLB 带 KHR_materials_clearcoat；不贴平铺纹理）**返工 R1**（2026-11-24，验收 run #72：GLB 里 clearcoat 明明在，EEVEE 预览仍全哑光——根因是预览只有单太阳+纯色平坦世界，清漆层无物可映、涂层高光被底漆粗糙度冲淡；Godot 04-charge 远景也看不出光泽。Coat Roughness 0.15→0.05、底漆 Roughness 0.35→0.25，Godot 侧同向变亮；回读 198，零 Error/Traceback）**返工 R2**（2026-11-24：run 45251171902 新图与旧图逐像素几乎相同（平均差 0.02），涂层再锐也看不见——纯色平坦世界无物可映；.blend 改留 Nishita 天空世界（仰角 50°，render_max 对亮色世界原样保留），清漆映天空渐变+太阳盘；不进 GLB，Godot 不受影响。回读 198，零 Error/Traceback）**返工 R3**（2026-11-24：R2 仍全哑光，根因见 §9——天空不在画面内（相机俯角 28°、顶缘视线低于地平线 16°）、平板车身映均匀淡天、探针无用；修法只改预览环境：留 Nishita + 暗色地面 Ground_PreviewOnly + 东南太阳 + 西北 24×2m 亮条灯（15000），本地 320×180 验证蓝车顶现 184→209 渐变光带；GLB blob 与仓库相同未推。回读 201，零 Error/Traceback） |
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
| overview 校园总览 | 20 件 ov-*（§3.1）+ 拼装补的地面/池塘水面盘/配电房外壳 | `assets/blender/scenes/overview.blend`、`assets/models/scenes/overview.glb` | **已完成，最终刷新**（2026-11-23 11:18 CST，工人 d644ce2d：.blend 51,360,304 B、.glb **102,672,808 B**（上次 25,914,236 B，暴涨主因 B 组烘焙贴图嵌进 .glb，各件 .glb 之和约 102MB），回读 **4837** 个对象（append 4833 + 拼装补 4），脚本内置 VERIFY 与独立回读一致，DONE overview，日志零 Error/Traceback（`assets/blender/scenes/overview-refresh-20261123.log`）；3 分钟跑完、单进程错峰。差额 +8 全部来自 ov-road-main（src 36→44、kept 33→41，含环路中心线等新增对象），其余 18 件 kept 数与上次逐件核对完全相同。**2026-11-23 14:54 UTC 总览重刷**（`assets/blender/scenes/overview-refresh-transformer-20261123.log`）：.blend 66,234,504 B、.glb **123,019,340 B**（完整版；瘦身版见 §10），回读 **13,036**（append 13,032 + 拼装补 4；ov-transformer 58 件、其余 12,978 件），DONE overview，日志零 Error/Traceback；增量主因 ov-lawn 真草（kept 8,270 件）等 PBR 返工件 + ov-transformer 58 件。**202 种材质**（本地完整版 GLB JSON 实测；瘦身只动贴图、不动材质），贴图引用审计 0 缺失（见 §9）。**已解决（瘦身入仓，见 §10）**：完整版 .glb 123.0MB / .blend 66.2MB 仍超 API blob 上限，瘦身版 .glb 37,538,508 B / .blend 9,736,002 B 已随 commit `e56912f` 入仓（该版为池塘返工前）；**2026-11-23 23:58 CST 池塘草坪返工后重刷**（commit `8390649`）：完整版 .glb **121,570,192 B**、.blend 64,530,392 B，瘦身版 .glb **36,459,020 B** / .blend 9,092,702 B 已入仓（仓库核对一致，见 §9），回读仍 13,036 对象。草密度核查实测总计 **102,901**（程序化 94,761 叶、约 42/m² + 真素材 8,140 株）；22,500 一数口径**待确认**（丛 vs 叶未分清，不采用）；20 件全部全局坐标直接 append、未移位置，剔除 52 个预览地面/重复件/相机/灯光/探针；拼装补：地面 340×340（#69b45e，顶面 z=-0.05 防 z-fighting）、池塘椭圆盘（中心 (82,-78)、rx11/ry8、顶面 z=0.10，水面蓝 #2F7FC4 为拼装自选、campus.json 无池塘颜色；ov-lawn 池塘草坪已返工（2026-11-23 23:58 CST）：撒点排除水面椭圆（+1m 边距）只留环形带，4,662 叶、42.1 叶/m²，拼装不再下移草丛——旧 -0.5m 下移曾把 18,863 叶全埋地下）、配电房外壳 16×10×8m（#dfe9f2）+ 屋顶板 16.6×10.6×0.3m（#424A52）。户外变压器已补 ov-transformer（58 件，见 §3.1）。**2026-11-24 停车返工后重刷**：ov-parking R1 .blend（2026-11-23 19:31 UTC，补 Coat Weight 1.0 / Coat Roughness 0.05、车窗 Bump）拼入总览，overview.py 未改动（已是最新拼装逻辑、逐件 append 最新 .blend，仓库 SHA 一致）；20 件 kept 数与上次逐件核对完全相同（ov-parking src/kept 233/233——R1 只改材质参数、对象数不变），回读 **13,036**（append 13,032 + 拼装补 4），日志零 Error/Traceback（`assets/blender/scenes/overview-refresh-parking-20261124.log`）；完整版 .glb **121,570,548 B**（+356 B，清漆扩展数据）、.blend 64,546,472 B；GLB JSON 实测 13,036 节点 / **202 种材质** / 427 贴图（全内嵌、0 缺失）、KHR_materials_clearcoat 在列（ov-parking_body_red/grey/blue 3 种车漆）；瘦身版 .glb 36,044,776 B / .blend 9,093,786 B 见 §10。遗留：①ov-windows-roofs 件内 faces 表把半长半宽用反（东西向窗带用了 hx、南北向用了 hy，A/B/C 三栋窗带长短全部对调，修复任务已派）；②池塘椭圆南缘压到 ov-road-main 南环路带（y -84~-76 一段），水面顶 0.10 略高于路面顶 0.08，水面盖住一小段路缘，属件间布局冲突，拼装未改路，待定） |
| pv 光伏屋顶 | pv-roof、pv-panels、pv-mount、pv-inverter | `assets/blender/scenes/pv.blend`、`assets/models/scenes/pv.glb` | **已完成（最终干净快照）**（2026-11-23 01:33 CST：.blend 112,997,536 B、.glb 12,226,304 B，回读 **881** 个对象（roof 33、panels 548、mount 3、inverter 297），DONE pv；第一跑约 31 分钟时被服务重启 SIGTERM 杀掉、未写出任何文件，第二跑用 setsid nohup 脱离会话重跑成功，四件 SRC-UNCHANGED 全绿、干净单版本快照。pv.py 同步改动：EXPECTED["pv-inverter"] 291→297，三处总量 assert 875→881。最终版特征实测全过：板 548、北行横梁 35.124m、线槽顶端 19.350/13.300、逆变器箱体 A1 (−74.75,36.40)、A2 (−37.25,36.40)、LAB (−28,67.20)，北向段确为新 4 件。遗留小项：pv.py 头注释里的旧版源版本说明已过期（仍写上一轮混合版时间戳/md5），下次刷新时更新为本次实际拼入版本（roof d2681c69…、panels f042b491…、mount 009873e8…、inverter d12fc0f9…）或删掉）**2026-11-23 场景重出**（pv-scene-pbr-20261123.log，15:14 UTC）：.blend 13,562,916 B、.glb 19,774,596 B，回读 881 对象 / 25 种材质，DONE pv；场景 .blend 已随 commit `c0cd01d` 刷新入仓（仓库 13,562,916 B，与本地重出一致）；**场景 .glb 已刷新入仓**（commit `7227239`，仓库 19,774,596 B，与本地重出一致，旧 12,226,304 B 已替换）。**材质去重已修**（commits `8805b66`、`7bcd65c`、`1f36cb2`）：scenes/pv.py 与 scenes/charge.py 在 append 后去重，pv 材质 3,094→25（场景重出实测 25 种）、charge 117→24（见 §9 晚间记录）。**2026-11-24 00:30 CST P0/P1 材质补挂后重出**（commit `060877f`）：scenes/pv.blend 15,323,932 B、scenes/pv.glb **24,051,408 B**（仓库核对一致，旧 19,774,596 B 已替换），单件 pv-mount.glb 9,787,184 B，回读零 Error/Traceback（见 §9）。 |
| storage 储能站 | st-cabinet、st-doors、st-cables、st-base、st-fence + 拼装补的壳体 | `assets/blender/scenes/storage.blend`、`assets/models/scenes/storage.glb` | **已完成并已刷新**（拼装 2026-11-22 23:22 CST：.blend 4,731,368 B、.glb 1,773,372 B，回读 269 个对象；跟进修复 23:31 CST：st-doors 风扇组抬高 +0.045（盘底 2.555，高出顶盖顶面 2.55 共 0.005，防 z-fighting），回读 52 个对象；壳体改半透明 Alpha 0.35 BLEND（GLB JSON 已核对 alphaMode=BLEND），屋顶板保持不透明；门把手残余 0.002m 已清零（复核 0.000000）。场景重出后回读仍为 269 个对象，DONE storage。遗留：st-doors.py 里的 Preview 顶盖仍是旧 0.06 厚（顶面 2.51），与 st-cabinet v2 实际顶盖（0.10 厚、顶面 2.55）不一致，只作 .blend 内参照、不导出，留待以后统一；风扇盘底与顶盖顶面之间现为 5mm 悬空间隙，有意为之）**2026-11-23 场景重出**（storage-scene-pbr-20261123.log，15:20 UTC）：.blend 10,382,492 B、.glb 7,237,164 B，回读 269 对象，DONE storage；**仓库已刷新入仓**（commit `1f36cb2`：storage.glb 仓库 7,237,164 B、storage.blend 仓库 10,382,492 B，均与本地重出一致）。**2026-11-24 00:30 CST P0/P1 材质补挂后重出**（commit `060877f`）：storage.blend 11,886,071 B、storage.glb 8,623,960 B（仓库核对一致），回读零 Error/Traceback（见 §9）。 |
| classroom 教室内部 | cl-floor-walls、cl-desks、cl-board、cl-ac、cl-lights、cl-windows（局部坐标） | `assets/blender/scenes/classroom.blend`、`assets/models/scenes/classroom.glb` | **已完成并已刷新**（拼装 2026-11-22 23:22 CST：.blend 4,870,036 B、.glb 2,689,528 B，回读 436 个对象；cl-desks 修复后场景已刷新：.glb 2,689,484 B，回读仍为 436 个对象，桌椅包围盒 x[-3.490, 4.598]，最近桌沿离讲台 0.205m、最后一排椅背离东墙 0.167m，DONE classroom。**tevy 换件已完成**（2026-11-23，commits `cf0d432`、`c2d99fa`、`e2bce23`、`5d0e1fc`、`c046118`）：新 classroom.blend 7,349,592 B、classroom.glb 20,164,540 B，回读 **440** 个对象（原 436，+门 1 +填缝 3）；桌椅换成 tevy 现成模型拆件（24 张单桌循环复用 48 套、16 张干净单椅循环复用），48 套间隙前 0.208m / 后 0.204m，门装进 cl-windows.py（见 §3.4）。遗留：cl-windows 南北各 4 扇窗，SPEC 只写南侧 4 扇，北侧窗与北墙窗洞对齐、位置没错，但北侧 4 扇无窗帘） |
| charge 充电区 | ch-piles、ch-cars、ch-marking、ch-canopy | `assets/blender/scenes/charge.blend`、`assets/models/scenes/charge.glb` | **已完成**（2026-11-22 23:36 CST 刷新后：.blend 7,930,116 B、.glb 934,624 B，回读 306 个对象（桩 40、车 198、标线 21、雨棚 47），DONE charge；4 台桩中心 y 均为 -73.25、与车位中心 x 偏差 0.00，桩南缘 -73.50 与车北端 -73.75 净空 0.25m（先前任务书写的 0.20m 为约数，实测 0.25m 更宽松、无穿插，脚本 12 组车–桩检查全部 no overlap）；白车 (48.5,-76) 在 4 号车位内朝南，蓝 (38,-76) 1 号、红 (45,-76) 3 号同样朝南；雨棚覆盖 4 个车位及 3 辆车全部 True）**2026-11-23 场景重出**（charge-scene-pbr-20261123.log，15:25 UTC）：.blend 7,439,548 B、.glb 7,126,168 B，回读 306 对象，DONE charge；**仓库已刷新入仓**（commit `1f36cb2`，含材质去重 117→24：仓库 charge.glb 7,105,356 B、charge.blend 3,376,684 B，均为去重后版本，见 §9）。**2026-11-24 00:30 CST P0/P1 材质补挂后重出**（commit `060877f`）：charge.blend 3,376,684 B（与去重版同体积）、charge.glb 7,105,712 B（仓库核对一致），回读零 Error/Traceback（见 §9）。**返工 R1 场景重刷**（2026-11-24：ch-cars 清漆 0.05/底漆 0.25 后重拼，charge.blend 3,376,684 B、charge.glb 7,105,672 B，回读 306 对象/24 材质，GLB 车漆 clearcoat 0.05 已核，零 Error/Traceback）。 |
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
  - **推送与验证待填**：本次随 Godot 侧改动一次推送，待 godot-verify 新 run 出图后像素复核晴天草地均值（目标 SPEC #69B45E ±15）与树冠绿色，见 `~/workspace/review-rework-r1/godot-acceptance/ACCEPTANCE.md` 新节。

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
