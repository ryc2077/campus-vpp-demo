# 外部素材来源记录（assets/external/）

> 任务：校园虚拟电厂 Blender 返工素材 sourcing。只找素材、只下载、记来源。
> 下载时间：2026-11-23（CST）。下载方式：全部 `curl` 直链，无浏览器、无登录、无付费。
> 授权总则：本目录所有已下载文件均为 **CC0 1.0**（可自由改、商用、无需署名）。
> 未改任何 `.blend` / `.glb`，未碰其他任务文件。
> 校验：49 张 JPG 全部经 Python PIL 打开验证（尺寸见下，无损坏、无 0 字节）；
> 4 个 ambientCG 附带 `.blend` 经 Blender 4.2.0 `--background` 只读打开验证（均为 0 对象 / 3 材质的材质包，无报错）。
> ambientCG 的原始 ZIP 已删（内容已解压，ZIP 可按表中直链重新下载）。

## 使用说明（给返工工人）

- Poly Haven：`_diff_1k.jpg` = baseColor，`_rough_1k.jpg` = roughness，`_nor_gl_1k.jpg` = normal（OpenGL，
  Blender 法线贴图节点用 Non-Color + 正常强度即可）。全部 1024×1024。
- ambientCG：`*_Color.jpg` = baseColor，`*_Roughness.jpg` = roughness，`*_NormalGL.jpg` = normal（OpenGL；
  同目录另有 `*_NormalDX.jpg` 备用，不要两个混用）。另含 `*_Displacement.jpg` / `*_AmbientOcclusion.jpg`
  （Concrete034、Plaster001 无 AO 图），以及同名 `.blend`（Blender 材质包，可直接 append 材质）、`.mtlx` / `.tres` / `.usdc`。
- 配色以 SPEC §3 为准：贴图本身颜色与 SPEC 十六进制不完全一致时，在 Principled BSDF 里用 Hue/Saturation 或
  MixRGB 把 baseColor 往 SPEC 色上靠（例如 white_stucco 染成 `#F3E9D2` 米白 / `#DFE9F2` 蓝灰，
  grey_roof_01 染成 `#424A52` 深灰，red_bricks_04 染成 `#8E2F28` 艺体馆红）。
- 玻璃不贴图（Blender 里透明材质即可），本目录无玻璃贴图。
- Concrete034 全套是 1024×512（非正方形），贴墙面/地面时注意 UV 比例。

## 1. PBR 材质 / 纹理包（已下载）

### 1.1 Poly Haven（https://polyhaven.com，CC0，免登录直下）

直链格式：`https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k/<slug>/<slug>_<diff|rough|nor_gl>_1k.jpg`
资产页：`https://polyhaven.com/a/<slug>`

| 用途（SPEC 对应） | slug / 文件 | 来源链接 | 授权 |
|---|---|---|---|
| 沥青路（`#424A52`，ov-road-main） | `asphalt_01`：`asphalt_01_diff_1k.jpg` / `_rough_1k.jpg` / `_nor_gl_1k.jpg` | https://polyhaven.com/a/asphalt_01 | CC0 |
| 混凝土（`#B9B3A8`，基座/墙面，st-base、di-walls） | `concrete_wall_007`：`concrete_wall_007_diff_1k.jpg` / `_rough_1k.jpg` / `_nor_gl_1k.jpg` | https://polyhaven.com/a/concrete_wall_007 | CC0 |
| 外墙涂料/灰泥（米白 `#F3E9D2` / 蓝灰 `#DFE9F2` / 浅橙 `#F6D9C0`，楼体墙面，需染色） | `white_stucco`：`white_stucco_diff_1k.jpg` / `_rough_1k.jpg` / `_nor_gl_1k.jpg` | https://polyhaven.com/a/white_stucco | CC0 |
| 砖墙（艺体馆红墙 `#8E2F28`，需染色加深） | `red_bricks_04`：`red_bricks_04_diff_1k.jpg` / `_rough_1k.jpg` / `_nor_gl_1k.jpg` | https://polyhaven.com/a/red_bricks_04 | CC0 |
| 屋顶（深灰 `#424A52`，平屋顶面层；注：这是灰瓦面，不是防水卷材，见 §3 未找到） | `grey_roof_01`：`grey_roof_01_diff_1k.jpg` / `_rough_1k.jpg` / `_nor_gl_1k.jpg` | https://polyhaven.com/a/grey_roof_01 | CC0 |
| 木地板（教室木面 `#C8A06A`，cl-desks 桌面 / cl-floor-walls） | `wooden_floor_01`：`wooden_floor_01_diff_1k.jpg` / `_rough_1k.jpg` / `_nor_gl_1k.jpg` | https://polyhaven.com/a/wooden_floor_01 | CC0 |
| 刷漆金属（蓝漆金属板，储能柜/配电柜/充电桩金属件，需染色） | `blue_metal_plate`：`blue_metal_plate_diff_1k.jpg` / `_rough_1k.jpg` / `_nor_gl_1k.jpg` | https://polyhaven.com/a/blue_metal_plate | CC0 |
| 镀锌金属（波纹镀锌铁皮，雨棚/支架/屋顶金属件） | `corrugated_iron_02`：`corrugated_iron_02_diff_1k.jpg` / `_rough_1k.jpg` / `_nor_gl_1k.jpg` | https://polyhaven.com/a/corrugated_iron_02 | CC0 |
| 浅色铺装（`#D8D2C4`，南门广场/步道，ov-road-walk） | `concrete_pavement_03`：`concrete_pavement_03_diff_1k.jpg` / `_rough_1k.jpg` / `_nor_gl_1k.jpg` | https://polyhaven.com/a/concrete_pavement_03 | CC0 |

### 1.2 ambientCG（https://ambientcg.com，CC0，免登录直下）

授权依据：https://ambientcg.com/license ——“All ambientCG assets are provided under the Creative
Commons CC0 1.0 Universal License”。
直链格式：`https://ambientcg.com/get?file=<AssetID>_1K-JPG.zip`（302 跳转到下载站）；资产页：`https://ambientcg.com/a/<AssetID>`

| 用途（SPEC 对应） | AssetID / 目录 | 来源链接 | 授权 |
|---|---|---|---|
| 草地地面（`#69B45E`，ov-lawn / ov-field；需染色调绿） | `Grass004`：`ambientcg/Grass004/`（Color / Roughness / NormalGL / NormalDX / Displacement / AmbientOcclusion，1024×1024，附 `.blend` 材质包） | https://ambientcg.com/a/Grass004 | CC0 |
| 木地板（备用，与 wooden_floor_01 二选一） | `WoodFloor051`：`ambientcg/WoodFloor051/`（同上 6 图 + `.blend`，1024×1024） | https://ambientcg.com/a/WoodFloor051 | CC0 |
| 外墙灰泥（备用，与 white_stucco 二选一） | `Plaster001`：`ambientcg/Plaster001/`（Color / Roughness / NormalGL / NormalDX / Displacement，无 AO，1024×1024，附 `.blend`） | https://ambientcg.com/a/Plaster001 | CC0 |
| 混凝土（备用，与 concrete_wall_007 二选一；注意 1024×512） | `Concrete034`：`ambientcg/Concrete034/`（Color / Roughness / NormalGL / NormalDX / Displacement，无 AO，1024×512，附 `.blend`） | https://ambientcg.com/a/Concrete034 | CC0 |

## 2. 草（已下载地面贴图；草丛模型 / 草叶 alpha 贴图未找到，见 §3）

> 更新 2026-11-23 22:25：本节已过时——补找（§5）已拿到真草叶 alpha 贴图与 3 个草丛模型，均在 `grass/`。
> 下两行保留为当时的原始记录。

- 草地地面贴图：`ambientcg/Grass004/` 全套（见上表），CC0，可供 ov-lawn 地面基底直接使用。
- Poly Haven 有草丛模型 **Grass Medium 01**（`https://polyhaven.com/a/grass_medium_01`，CC0，几何节点散布草丛），
  但直链下载失败（见 §3），未入库。
- 草叶 alpha 贴图（带透明通道、供交叉面片实例化）：未找到（见 §3）。ov-lawn 现有的 6 种程序化草叶先保留，
  返工时可用 Grass004 地面贴图 + 程序化草叶组合。

## 3. 未找到 / 未下载（诚实记录，不编链接）

| 想要的东西 | 结果 | 备注 / 可查的参考链接（仅作参考，未下载） |
|---|---|---|
| 屋顶防水卷材专用贴图 | **未找到** | Poly Haven / ambientCG 热门库里没有以防水卷材（bitumen membrane / roofing felt）命名的贴图；暂用 `grey_roof_01`（灰瓦面，需染色至 `#424A52`）或纯色 + roughness 代替，pv-roof 防水层仍以 SPEC 为准 |
| 草丛 / 单株草模型（.blend / .glb） | **未下载** | Poly Haven Grass Medium 01（CC0）页面存在，但 `dl.polyhaven.org` 直链多种格式均 404（`Models/blend/grass_medium_01.zip`、`Models/gltf/grass_medium_01/grass_medium_01.glb`、`Models/blend/grass_medium_01/grass_medium_01.blend`）；`api.polyhaven.org` 在本机返回 522/403，无法取文件清单。需在站内点下载或用 Poly Haven Blender 插件拉取。参考：https://polyhaven.com/a/grass_medium_01 |
| 草叶 alpha 贴图（透明通道） | **未找到** | ambientCG 搜索接口在本机不接受 query 参数（`?search=` / `?queryString=` 均返回全库热门前 100，未含草叶 alpha）；Poly Haven 无草叶贴图分类。未编造任何链接 |
| BlendSwap 学校/教学楼/草丛模型 | **未下载（需登录）** | BlendSwap 免费模型下载页实测返回 HTML 登录页（`curl` 跟随跳转后仍是 `Download "Grass by gholm"` 页面，`Sign in to download`），无账号无法直下。参考（CC0/CC-BY，需登录后下载，仅作部件来源）：Grass by gholm（CC0）https://blendswap.com/blend/4641 ；Realistic Grass Field by CraigForster（CC0）https://blendswap.com/blend/4678 ；Crenshaw High School by jackalzweb（CC-BY）https://blendswap.com/blend/17192 ；Anime Classroom by argonius（CC0）https://blendswap.com/blend/19436 ；学校分类页 https://blendswap.com/3d/school-project |
| BlenderKit 窗/门/空调外机/栏杆等部件 | **未下载（需免费账号 + 插件）** | BlenderKit 免费区确有对应部件，但须注册免费账号并在 Blender 内装 BlenderKit 插件才能拉取，无直接 .blend 下载链接。参考：Outdoor Split Air Conditioner（FREE，496 面，2.1 MiB）https://staging.blenderkit.com/asset-gallery-detail/e9331d55-f079-4d03-aa06-3e063ae1f636/ ；Old Air conditioner exterior unit（FREE）https://staging.blenderkit.com/get-blenderkit/82a5e776-362a-4b13-855e-09e8643158f3/ ；免费空调列表 https://www.blenderkit.com/asset-gallery-pure?query=tags%3AAC&page=1 ；建筑免费区 https://www.blenderkit.com/asset-gallery-pure?query=category_subtree%3Aarchitecture&page=6 。注意：其中个别标 “Full Plan” 的为空调变体需付费订阅，下载时只选标 Free 的 |
| 学校/教学楼整体模型（按 SPEC 实测尺寸） | **不采用** | 主体楼体仍按 SPEC §4 实测尺寸自建；网上模型（BlendSwap Crenshaw High School 等）均非按本校尺寸，仅作部件与比例参考，不直接采用 |

## 4. 文件清单（共 69 个文件，约 41 MB）

- `polyhaven/`：27 张 JPG（9 套 × diff/rough/nor_gl，全部 1024×1024，PIL 验证通过）。
- `ambientcg/Grass004/`：11 个文件；`ambientcg/WoodFloor051/`：11 个文件；
  `ambientcg/Plaster001/`：10 个文件（无 AO）；`ambientcg/Concrete034/`：10 个文件（无 AO，1024×512）。
- 其余文件：本 `SOURCES.md`、`READY.md`（不计入 69 个素材文件）。

## 5. 教学楼 / 教室模型（已下载，2026-11-23 22:17–22:30 CST）

> 全部经 `curl` 直链下载，无登录、无付费。授权均为 **CC0 1.0**（可自由改、商用、无需署名）。
> 尺寸写法：glTF 坐标 X=宽、Y=高、Z=深（米）；下表尺寸均按此顺序。
> 校验：6 个 `.glb` 全部用 Python 直读 JSON（Grab3D 三个另经 Blender 4.2.0 `--background` 导入验证，
> 对象数与包围盒与页面标注一致）；tevy 三个 `.glb` 用 meshopt 解码顶点实测包围盒（见下方注意）；
> 3 个 Grab3D `.blend` 经 Blender 4.2.0 只读打开——**全部是同一个 67KB 占位文件，见 5.3，不可用**。
> 未改任何 `.blend` / `.glb`，只读验证。

### 5.1 已下载文件清单（`buildings/`，共 13 个文件，约 20.9 MB）

| 文件 | 大小 | 来源 | 授权 |
|---|---|---|---|
| `school-building-tevy.glb` | 2,907,008 B | tevy.dev（见 5.2） | CC0 |
| `classroom-tevy.glb` | 2,789,056 B | tevy.dev（见 5.2） | CC0 |
| `school-corridor-lockers-tevy.glb` | 2,129,948 B | tevy.dev（见 5.2） | CC0 |
| `school-building-grab3d.glb` | 4,031,352 B | Grab3D（见 5.2） | CC0 |
| `library-grab3d.glb` | 1,444,160 B | Grab3D（见 5.2） | CC0 |
| `university-building-grab3d.glb` | 2,586,384 B | Grab3D（见 5.2） | CC0 |
| `school-building-grab3d.blend` | 2,129,031 B | Grab3D | CC0（但文件是占位，见 5.3） |
| `library-grab3d.blend` | 1,064,502 B | Grab3D | CC0（但文件是占位，见 5.3） |
| `university-building-grab3d.blend` | 1,668,680 B | Grab3D | CC0（但文件是占位，见 5.3） |
| `LICENSE-school-building-grab3d.txt` | 760 B | Grab3D 随包 LICENSE | CC0 1.0 全文 |
| `LICENSE-library-grab3d.txt` | 760 B | Grab3D 随包 LICENSE | CC0 1.0 全文 |
| `escola-estadual-kitpredios.glb` | 80,476 B | GitHub kayquer/kit-predios-brasil-lowpoly（见 5.2） | CC0 |
| `escola-tecnica-kitpredios.glb` | 74,736 B | GitHub kayquer/kit-predios-brasil-lowpoly（见 5.2） | CC0 |

### 5.2 逐个适配评估（对照 SPEC §4：楼体尺寸是实测，绝不能改尺寸去套模型）

SPEC §4 目标尺寸（长×宽×高，米）：bldA 40×15×19（5F）、bldB 32×14×19（5F）、bldC 22×13×14（4F）、
lib 24×16×22（6F）、gym 36×16×18、lab 42×12×13、tower 14×14×32、canteen 32×13×15、dorm 20×12×16（5F）。
教室内部：9.68×7.26m、层高 3.0m（一楼 3.5m）。

| 模型 | 实测包围盒（宽×高×深） | 来源链接 | 适配评估 |
|---|---|---|---|
| tevy 学校楼 `school-building-tevy.glb` | 42.6 × 10.12 × 24.34（含院子；楼体约 40×20） | https://tevy.dev/models/school-building（直链 https://tevy.dev/models/school-building/v1/lod0.glb） | **整栋不采用**：只有 2 层、高仅 10.1m，改到 19m 需纵向拉伸 ×1.9，窗带比例全坏。**部件可用**：5 个分离 mesh（`classrooms` / `entrance` / `outdoor_lights` / `roof_and_yard` / `sports_hall`）——入口雨棚、屋顶光伏板、体育馆侧翼可拆出来做 ov-gate 入口 / pv-panels / ov-gym 的参考与部件 |
| tevy 教室 `classroom-tevy.glb` | 8.15 × 3.6 × 8.2 | https://tevy.dev/models/classroom（直链 https://tevy.dev/models/classroom/v2/lod0.glb） | **教室部件首选**：尺寸与 SPEC 教室 9.68×7.26×3.0 很接近（长 ×1.19、宽 ×0.89、高 ×0.83，非均匀缩放可接受）；9 个分离 mesh（`desks` / `chairs` / `teacher_desk` / `shelves` / `door_geo` / `shell` / `wall_front` / `ceiling` / `bags_bin`），桌椅、讲台桌、书架、门可直接拆给 cl-desks / cl-board / cl-windows 用。整间照搬需把近方形 8.15×8.2 拉成 9.68×7.26，桌椅排布会变形，建议只拆部件 |
| tevy 走廊储物柜 `school-corridor-lockers-tevy.glb` | 4.1 × 3.6 × 4.0 | https://tevy.dev/models/school-corridor-lockers（直链 https://tevy.dev/models/school-corridor-lockers/v1/lod0.glb） | **部件可用**：26 个储物柜各自独立 mesh（`locker_01_geo` … `locker_26_geo`）+ 外壳，可直接取单个柜子放走廊/教室后墙；层高 3.6m 与 SPEC 3.0/3.5m 接近 |
| Grab3D 学校楼 `school-building-grab3d.glb` | 22.9 × 16.69 × 13.86 | https://grab3d.com/models/buildings/school-building/（直链 https://grab3d.com/dl/school-building/school-building.glb） | **最接近 bldC 的整栋候选**：目标 bldC 22×13×14，实测 22.9×13.86 footprint 只差约 4–6%、高 16.69 改到 14 只需 ×0.84，是一批里唯一“改尺寸不伤比例”的整栋。待改：黄色墙改浅橙 `#F6D9C0`、珊瑚红坡顶改深灰平屋顶 + 女儿墙、拆掉屋脊钟楼/铃塔。2 个 mesh（`school-building_body` / `school-building_details`），窗与墙体未分离，改窗需重做窗带 |
| Grab3D 图书馆 `library-grab3d.glb` | 18.8 × 9.82 × 20.32 | https://grab3d.com/models/buildings/library/（直链 https://grab3d.com/dl/library/library.glb） | **整栋不采用**：目标 lib 24×16×22（6F），实测只有 9.82m 高，拉到 22m 需 ×2.24，楼层数对不上。**部件可用**：3 个 mesh（`library_body` / `library_book_emblem` / `library_details`），柱廊、拱窗、天窗可拆给 lib / ov-gate 做部件参考 |
| Grab3D 大学楼 `university-building-grab3d.glb` | 30.9 × 24.3 × 19.8 | https://grab3d.com/models/buildings/university-building/（直链 https://grab3d.com/dl/university-building/university-building.glb） | **整栋不采用，量块/部件次选**：高 24.3m 与 lib 目标 22m 接近（×0.91），但 footprint 30.9×19.8 改到 24×16 需 ×0.78/×0.81，且只有 3 层、带钟塔圆顶，改 6 层图书馆要拆塔、重排窗带。4 个 mesh，`university-building_windows` 独立成 mesh，窗户部件可单独拆用 |
| kit-predios 州立学校 `escola-estadual-kitpredios.glb` | 1.41 × 0.74 × 1.41（单位，非米） | https://github.com/kayquer/kit-predios-brasil-lowpoly（直链 models/publico/escola_estadual.glb，仓库 LICENSE 为 CC0 1.0） | **只作体量参考**：低多边形套件比例尺（README 明说一栋房子约 1.3 单位宽），放大 ×28 才到 40m 级；单 mesh（`corpo`，1176 tris）、窗/门/墙全焊在一起不可拆。L 形单层校舍 + 有顶连廊 + 带拱顶球场，可作 bldC / ov-field 的体量草稿 |
| kit-predios 技术学校 `escola-tecnica-kitpredios.glb` | 1.42 × 0.91 × 1.08（单位，非米） | https://github.com/kayquer/kit-predios-brasil-lowpoly（直链 models/publico/escola_tecnica.glb） | **只作体量参考**：同上套件比例尺；单 mesh（`corpo`，1128 tris）不可拆。两层砖楼 + 锯齿形玻璃顶车间 + 自行车棚，可作 lab（实验楼）/ ov-gym 的体量草稿 |

**结论（给返工工人）**：没有一个模型能直接按 SPEC §4 尺寸整栋采用——所有网上教学楼都不是 5 层 19m
的本校楼体，楼体量块仍按 SPEC 自建。最有用的三件：① Grab3D 学校楼改 bldC（尺寸最接近）；
② tevy 教室拆桌椅/讲台/门（cl-desks、cl-board、cl-windows 的部件来源）；③ tevy 走廊储物柜拆单柜。
其余只作部件与体量参考。

### 5.3 重要坑：Grab3D 的 .blend 下载全是占位文件

- 三个 `.blend`（school-building / library / university-building）下载后解压验证：
  zstd 解压均为 **同一个 67,137 字节文件**（sha256 前 16 位 `a967ef2232d7cd5d`），
  文件头 `BLENDER17-01v0502REND`，Blender 4.2.0 `--background` 只读打开报
  `Failed to read blend file ... not a blend file`，三个文件内容完全相同——是服务端返回的占位/错误文件，
  不是真正的模型。**不要用这三个 .blend**，用同目录的 `.glb`（已验证可导入）。
- tevy 的 `.glb` 用了 `EXT_meshopt_compression` 压缩：Blender 4.2.0 自带 glTF 导入器打不开
  （`Extension EXT_meshopt_compression is not available on this addon version`），
  本次用 Python `meshopt` 库解码顶点实测了包围盒。返工时如需进 Blender，
  先用 gltf-transform（`gltf-transform optimize --no-compress` 或 `copy` 去压缩）转一次，
  或用 Blender 4.5+ 导入；Godot 4 侧导入前同样建议先解压。

## 6. 教学楼模型：试过没成的渠道（补充 §3，不编链接）

| 渠道 | 结果 | 备注 |
|---|---|---|
| GitHub 代码/仓库搜索（`school building blender` / `classroom blender`） | **只找到 1 个可用仓库** | kayquer/kit-predios-brasil-lowpoly（CC0，见 5.2，含 `escola_estadual` / `escola_tecnica` 两个学校模型）；其余结果多为无授权的课程作业仓库（如 rwny/blender-classroom、amcnabbbaltar-vanier 的课堂作业），未下载 |
| Sketchfab 免费下载区（knjaq 的 3 栋游戏建筑，含 1 栋学校，CC0） | **未下载（需登录）** | 页面 https://sketchfab.com/3d-models/3-unique-game-ready-buildings-73a2d53e6a5047789782329d0f268b93 含 “Log in”，HTML 里无直链，只有缩略图 `media.sketchfab.com/.../thumbnails/...`；Sketchfab 下载须登录账号，无免登录直链 |
| Open3DModel 免费区（school building 搜索页） | **未下载（无直链）** | https://open3dmodel.com/3d-models/school-building 页面可打开，但 HTML 里无任何 download 链接（JS 渲染 + 须账号），未找到可直接下的文件 |
| Free3D（school 搜索页） | **未下载（页面被挡）** | https://free3d.com/3d-models/school 经 curl 只返回 778 字节空页，无下载链接；该站下载本来就需要登录 |
| CGTrader 免费区 | **未下载（页面被挡）** | https://www.cgtrader.com/free-3d-models/school-building 经 curl 返回 0 字节；该站免费模型下载须注册账号 |
| archive.org（Blender 模型合集） | **无可用模型** | `title:(school building) AND mediatype:data` 搜到 12 条，全是 Thingiverse 的 STL 3D 打印模型（如 Hill Valley 高中楼、Alberta 小学），不是 Blender 建筑模型、授权也不明，未下载 |
| Poly Haven 模型区 | **跳过（与任务要求一致）** | 只有贴图/HDR，无学校楼模型（草丛模型直链问题见 §3） |
| itch.io Low Poly Library & School Pack（reodesuxz，27 个教室/图书馆小道具，FBX/GLB/OBJ/.blend） | **未下载（须走 itch 购买页）** | https://reodesuxz.itch.io/low-poly-library-school-pack 免费但须经 itch.io 下载流程，无 curl 直链；内容是书架/课桌/黑板等小道具而非楼体，留作备用参考，未下 |
| Meshy.ai 免费 Classroom / University 模型库 | **未下载** | AI 生成模型、CC0 宣称但须注册账号才能下载，且单体质量未经验证，未下；参考 https://www.meshy.ai/tags/classroom |

## 5. 草补找（2026-11-23 22:15–22:25 CST，GRASS-TRY：拿到真草叶 alpha 贴图 + 真草丛模型）

> 补找结果：**已拿到**。草叶 alpha 贴图（Render a House 草坪切块 RGBA PNG，立面 2000×456 可直接贴交叉面片）
> 与草丛模型（3 个 GLB：Render a House 草坪块、tevy 野草丛 CC0、3DAssets 高草丛 CC0）全部存入 `grass/`，
> 共新增 14 个文件、约 11 MB。**程序化保底贴图未做**——已拿到下载素材，不需要保底。
> 以下每种办法的结果如实记录；未改任何 `.blend` / `.glb`（只新增了 `grass/` 下的文件）。

### 5.1 各办法结果

| # | 办法 | 结果 |
|---|---|---|
| 1 | Poly Haven API（`curl` + 浏览器 UA 请求 `https://api.polyhaven.org/api/v1/asset/grass_medium_01`） | **失败，同 §3**：HTTP 522，`error code: 522`，16 字节。API 在本机仍不可达，Grass Medium 01 依旧未拿到 |
| 2 | ambientCG 猜直链 `https://ambientcg.com/get?file=Grass004_2K-PNG.zip` 等 | **链接格式有效，但无草叶 alpha**：`Grass004_{1K,2K,4K}-PNG.zip` 均 HTTP 200 正常下载（1K 19.6 MB / 2K 73 MB / 4K 279 MB），ZIP 内只有地面贴图的 Color/Roughness/NormalGL/NormalDX/Displacement/AO + `.blend`，无 alpha 贴图；且与已有的 `ambientcg/Grass004/` JPG 套系重复，三个 ZIP 已删除，未入库。另查：`Grass003` / `Grass006` / `Grass008` 资产页存在（`Grass001` 空回复、`Grass002/005/007/009/010` 301 后页面无标题，疑似不存在或被墙），均为地面贴图、非草叶，未下载 |
| 3 | GitHub 搜 CC0 草模型 / 草叶贴图 | **仓库搜索 0 结果**：`api.github.com/search/repositories?q=grass+blender+CC0` 返回 `total_count: 0`；代码搜索接口未登录返回 401 `Requires authentication`，未继续。GitHub 这路未拿到文件（但见 5.3，CC0 草丛改由 tevy / 3DAssets 直链拿到） |
| 4 | OpenGameArt / textures.com 免费区 | **未单独跑**：`browser_search` 查 OpenGameArt 时工具报错失败，未重试（按规则不重复）；此前搜索已在别路拿到目标（见下），不再补跑 |
| — | 搜索中发现的免费可商用来源（Render a House / tevy / 3DAssets） | **成功，见 5.2**：Render a House 草 PNG 切块 + 草 3D 模型（免费商用、无需署名/注册，禁转售打包）；tevy 野草丛与 3DAssets 高草丛均为 **CC0**，直链可下 |

### 5.2 新入库文件（`grass/`，全部已校验）

**（A）Render a House 草叶 alpha 贴图（免费商用、无需署名/注册，禁转售或并入其他模型库再分发）**

来源页：https://www.renderahouse.com/blog/free-grass-png
授权原文：页面 "Free commercial use" 一节——"Free for personal and commercial architectural projects. No attribution or signup required"。
直链：`https://www.renderahouse.com/downloads/free-png-cutouts/grass/grass-png-cutouts.zip`（4,478,035 字节，与页面标注一致）及同目录下各单张 PNG。

| 文件 | 内容 / 校验 |
|---|---|
| `renderahouse-grass/grass-side-colour.png` | 立面彩色草叶条，2000×456，RGBA，alpha 0–255，PIL 验证通过；**供交叉面片贴图首选**（1.02 m 宽 × 0.20 m 高草坪条，源 mesh 尺寸见同目录 README.txt） |
| `renderahouse-grass/grass-side-massing.png` | 立面中性灰白版，2000×456，RGBA，alpha 0–255；可自行染色 |
| `renderahouse-grass/grass-side-silhouette.png` | 立面纯黑剪影版，2000×456，RGBA，alpha 0–255；可作遮罩/染色底 |
| `renderahouse-grass/grass-top-colour.png` | 俯视彩色草坪块，2000×1973，RGBA，alpha 0–255；方形草坪块俯视图（重复铺会露方形边界，需遮罩裁不规则边） |
| `renderahouse-grass/grass-top-massing.png` | 俯视中性版，2000×1973，RGBA，alpha 0–255 |
| `renderahouse-grass/grass-top-silhouette.png` | 俯视剪影版，2000×1973，RGBA，alpha 0–255 |
| `renderahouse-grass/grass-top-shadow-only.png` | 俯视投影层，2000×1973，RGBA，alpha 0–64；须与同尺寸俯视图叠放，不可单独裁剪 |
| `renderahouse-grass/README.txt` | 随 ZIP 附带的说明（尺寸、alpha 说明、授权一句话） |
| `renderahouse-grass-png-cutouts.zip` | 原始 ZIP 保留（4.48 MB），可按上表直链重新下载 |

注意：这是风格化低多边形渲染切块（非照片级草叶），源 mesh 带一层薄的不透明草皮底座；立面条适合贴在草坪边缘/交叉面片上做“看得见草叶”的近景，远景大草坪仍用 Grass004 地面贴图。

**（B）Render a House 草坪块 3D 模型（同上授权：免费商用、无需署名/注册，禁转售打包）**

来源页：https://www.renderahouse.com/blog/free-grass-3d-model
直链：`https://www.renderahouse.com/downloads/free-3d-models/grass/grass.{glb,fbx}`、`grass-obj.zip`

| 文件 | 内容 / 校验 |
|---|---|
| `renderahouse-grass.glb` | 339,544 字节，glTF 2.0，`file` 识别为 glTF binary，JSON 头校验：501 个 mesh/primitive，材质 `leaf` + `green`，无 Draco；页面标称 512 三角、1.022×1.0037×0.1998 m，方形草皮底座 + 独立低多边形草叶几何，Blender 直接 File → Import → glTF 2.0 |
| `renderahouse-grass.fbx` | 900,076 字节，Kaydara FBX 7400，备用格式 |
| `renderahouse-grass-obj.zip` | 24,931 字节，内含 `grass.obj`（89,390 字节）+ `grass.mtl`，备用格式 |

**（C）CC0 草丛 GLB（直链，无需登录）**

| 文件 | 来源 / 授权 | 内容 / 校验 |
|---|---|---|
| `tevy-wild-grass-clump.glb` | https://tevy.dev/models/grass-clump ，直链 `https://tevy.dev/models/grass-clump/v1/lod0.glb`（pinned v1，内容固定）；**CC0 1.0**（站内每模型均 CC0）。描述：约 0.6 m 高混合野草丛，拱形草叶、绿转枯草色叶尖，带提摩西/鸡脚草/草地早熟禾/绒毛草穗 | 882,196 字节，glTF 2.0，1 mesh，材质 `grass`，内嵌 2 张贴图；`file` 识别通过 |
| `3dassets-tall-grass-clump.glb` | https://3dassets.dev/assets/wipe-day-survival-island-tall-grass-clump-99fa2311 ，直链 `https://cdn.3dassets.dev/assets/27439/v1/model.glb`；**CC0 1.0**（站内 "Every model on 3DAssets.dev is released under CC0 1.0"）。描述：18 片扇形高草丛，约 0.9 m 宽 × 1 m 高 | 11,472 字节，glTF 2.0，1 mesh，材质 `leaf`，无贴图（纯色低多边形）；`file` 识别通过 |

### 5.3 给返工工人的用法建议（只建议，不改文件）

- 近景草叶：`renderahouse-grass/grass-side-colour.png` 贴交叉面片（Alpha 混合，Non-Color 关、Base Color 接贴图 RGB，Alpha 接贴图 Alpha），按 README 的 1.02 m 宽对齐缩放；或直接导入 `renderahouse-grass.glb`（带真实草叶几何，0.2 m 高草坪块，沿草坪边缘旋转摆放、去 tiling 感）。
- 自然野草丛点缀：`tevy-wild-grass-clump.glb`（0.6 m，带贴图、颜色最自然）为主；`3dassets-tall-grass-clump.glb`（1 m 高草，纯色）为辅，染色后混用。
- 远景大草坪：仍用 `ambientcg/Grass004/` 地面贴图（见 §1.2），草丛只放视线可及处。
- 授权提醒：tevy 与 3DAssets 两件是 CC0，可任意改、商用；Render a House 三件是“免费商用、无需署名”但**禁转售/禁并入其他模型库再分发**，用在 Demo 渲染里没问题，不要把这三个文件单独打包分发。

### 5.4 文件清单（本次新增 14 个文件，约 11 MB；全库合计 83 个文件）

- `grass/renderahouse-grass/`：8 个文件（7 张 RGBA PNG + README.txt，PIL 全验证通过）。
- `grass/renderahouse-grass-png-cutouts.zip`、`renderahouse-grass.glb`、`renderahouse-grass.fbx`、`renderahouse-grass-obj.zip`：4 个文件。
- `grass/tevy-wild-grass-clump.glb`、`grass/3dassets-tall-grass-clump.glb`：2 个 CC0 GLB（`file` + glTF JSON 头验证通过）。
- 程序化保底草叶贴图：**未做**（已拿到真实下载素材，无需保底）。

## 7. 课桌椅模型 sourcing（R2-T2，2026-11-24 22:39–23:10 CST）

> 背景：用户 2026-11-24 22:36 反馈桌椅建模还是不对，要求去网上找现成的桌椅 Blender 模型。
> 上一轮 tevy 教室模型拆件（§5.2）用户仍不满意，本次换一家、找更完整结构真实的桌椅。
> 规约：SPEC §6 教室内部，房间 7.26×9.68m、层高 3.0m，6 列×8 排=48 套课桌椅，木面桌 + 深色椅；
> 桌椅必须有真实结构（桌腿/横撑/椅腿/椅背，绝不许平板贴地、无腿悬浮）。任务要求桌约 1.1–1.3×0.55–0.65m、
> 高约 0.75m（双人桌口径；单人桌见 7.4 注）。
> 全部 `curl` 直链下载，无浏览器、无登录、无付费（Kenney 走页面 JS 里公开的 `download-link` 签名接口，
> 见 7.5）。校验：10 个 `.glb` 全部用 Blender 4.2.0 `--background` 只读导入验证（对象数/面数/包围盒/
> 落地结构逐 mesh 实测）+ Eevee 预览各 1 张（`desks/previews/`），结果见 `desks/verify_results.json`。
> 未改任何 `.blend` / `.glb`，未碰 `cl-desks.py` / `.blend` / `.glb`，未碰 Godot scripts/scenes/data。

### 7.1 选定：3DAssets Student Desk + Student Chair（Japanese School and City Street）

| 件 | 资产页 | 直链（CDN） | 授权 |
|---|---|---|---|
| Student Desk（学生课桌） | https://3dassets.dev/assets/japanese-school-and-city-street-student-desk-9e5d008a | https://cdn.3dassets.dev/assets/30081/v1/model.glb | CC0 1.0，无需署名 |
| Student Chair（学生椅） | https://3dassets.dev/assets/japanese-school-and-city-street-student-chair-826ccbf4 | https://cdn.3dassets.dev/assets/30083/v1/model.glb | CC0 1.0，无需署名 |

授权依据：站内 "Every model on 3DAssets.dev is released under CC0 1.0"；API 返回每件
`license.slug=cc0-1.0, attributionRequired=false`（`det-studentdesk.json` 等见 /tmp/r2t2，
API：`https://3dassets.dev/api/v1/assets/<slug>`，公开读、无需 key）。
本地文件：`desks/3dassets/student-desk.glb`（51,796 B，与 API `fileSize` 一致）、
`desks/3dassets/student-chair.glb`（43,632 B，与 API 一致）。

实测（Blender 4.2.0 只读导入，glTF 坐标 X=宽、Y=深、Z=高，米）：

| 件 | 包围盒（宽×深×高） | 对象/网格/面数 | 结构（目视 + 逐 mesh 实测） |
|---|---|---|---|
| Student Desk | 0.600 × 0.500 × 0.700 | 3 对象 / 2 网格 / 780 面 | 木面桌板（0.03 厚，z 0.67–0.70）+ 弯钢圆管桌架（684 面，z 0–0.67，508 个顶点落在地面 z<0.02，4 条管腿 + 脚垫 + 下方钢丝书篮），**真腿落地**，预览 `previews/student-desk.png` |
| Student Chair | 0.380 × 0.424 × 0.888 | 3 对象 / 2 网格 / 580 面 | 模压胶合板座面 + 靠背（座高约 0.42，靠背顶 0.888）+ 弯钢圆管椅架（388 面，z 0–0.882，508 个顶点落地，4 条管腿 + 横撑脚踏杆），**真腿落地**，预览 `previews/student-chair.png` |

48 套合计：(780+580)×48 = **65,280 面**，两文件共 95,428 B。
两人一对：同一系列（Japanese School and City Street）、同一材质（层压木面 + 弯钢圆管架），
颜色可直接按 SPEC §3 课桌木面 `#C8A06A` 染色、椅面染深色。

### 7.2 候选对比（打分：结构真实度 40 / 尺寸合规 30 / 面数 15 / 授权与可取性 15 = 100）

| 候选 | 来源 / 授权 | 单套尺寸（宽×深×高）/ 面数 | 48 套面数 | 结构实测 | 得分 | 结论 |
|---|---|---|---|---|---|---|
| **① 3DAssets Student Desk + Student Chair** | 3DAssets.dev，CC0（见 7.1） | 桌 0.60×0.50×0.70 / 780 面；椅 0.38×0.42×0.89 / 580 面 | 65,280 | 弯钢圆管桌架/椅架真腿落地 + 钢丝书篮 + 横撑，目视确认 | **96** | **选定** |
| ② 3DAssets Seminar Room Table + Stacking Seminar Chair | 3DAssets.dev，CC0；桌 https://3dassets.dev/assets/university-lecture-hall-and-campus-seminar-table-1c6ce71f（直链 `https://cdn.3dassets.dev/assets/34746/v1/model.glb`）；椅 https://3dassets.dev/assets/university-lecture-hall-and-campus-stackable-chair-cb3333fb（直链 `https://cdn.3dassets.dev/assets/34749/v1/model.glb`） | 桌 1.80×0.80×0.94 / 912 面；椅 0.44×0.49×0.94 / 848 面 | 84,480 | 焊接管腿架真落地，但桌带一块高出桌面 0.21m 的白色隔断屏（z 0.64–0.94），挡学生视线；大学研讨桌风格 | 81 | 备选：隔断须拆、1.8m 超宽 |
| ③ 3DAssets 1400 mm desk + ②的椅 | 3DAssets.dev，CC0；桌 https://3dassets.dev/assets/computers-and-desk-gadgets-desk-1400-c38edf1c（直链 `https://cdn.3dassets.dev/assets/38859/v1/model.glb`） | 桌 1.40×0.70×0.736 / 680 面；椅同② | 73,344 | 两侧实心板脚 + 后挡板落地（非管腿），带线孔，是办公室桌不是课桌 | 87 | 备选：尺寸最贴任务口径（1.4m），但造型是办公桌 |
| ④ poly.pizza Quaternius Desk + Quaternius Chair | poly.pizza，CC0；桌 https://poly.pizza/m/V86Go2rlnq（直链 `https://static.poly.pizza/91c2bf8d-0876-4801-abd3-8dd5d017ecbd.glb`）；椅 https://poly.pizza/m/iMNqRzPwwe（直链 `https://static.poly.pizza/84ecc6a3-2751-4f50-912a-b9f4ff033d7a.glb`） | 桌 1.82×0.85×0.92 / 2,640 面；椅 0.76×0.83×1.77 / 216 面 | 137,088 | 桌是带 4 个抽屉的古董式办公桌（顶高 0.92）；椅是木餐椅但**约 2 倍比例尺**（高 1.77m），须整体 ×0.5 缩放 | 70 | 不选：桌椅都不是课桌椅 |
| ⑤ Kenney Furniture Kit desk + chair（+ chairDesk） | Kenney，CC0；包 https://kenney.nl/assets/furniture-kit（签名下载接口见 7.5）；`desks/kenney/desk.glb` / `chair.glb` / `chair-desk.glb`，整包 `furniture-kit.zip`（5,130,729 B，140 件，附 `LICENSE-kenney.txt`） | 桌 0.73×0.39×0.38 / 198 面；椅 0.20×0.20×0.47 / 170 面；chairDesk 0.34×0.31×0.61 / 588 面 | 17,664 | 有真腿（桌 60 个顶点落地），但**玩具比例尺**（桌高仅 0.38m，须整体约 ×2 缩放）、方块卡通造型、桌深仅 0.39m | 74 | 不选：须重缩放 + 风格卡通 |
| ⑥ tevy 教室拆件（上一轮，现行 cl-desks） | tevy.dev，CC0；https://tevy.dev/models/classroom（直链 `https://tevy.dev/models/classroom/v2/lod0.glb`，已入库 `buildings/classroom-tevy.glb`） | 拆出单桌 0.61×0.61×0.71；单椅约 0.48×0.59×0.89 | —（碎面） | 见 7.3，**结构不可信** | 57 | 不选：用户已否决 |

### 7.3 为什么 tevy 的不行（上一轮拆件的实测结论，引自 `assets/blender/classroom/cl-desks.py` 头注）

1. **mesh 全是未焊接碎面**：`desks` 2,832 个 / `chairs` 3,072 个 loose 碎片，没有“一张桌 / 一把椅”的
   独立对象，只能按空间 Voronoi 聚类硬拆——拆出来的单件边界是猜出来的，不是模型自带的结构。
2. **椅子被高柜污染**：`chairs` mesh 里混进 2 个 1.02×0.62×1.16m 的高柜（后排左右角），
   高柜正面与第 2 排外侧 4 张椅的靠背共面（y 只差 0.02–0.04m），切不干净——拆出的 4 张椅各带
   135–236 张柜面（799–900 面 vs 正常 664 面，其中 1 张还带 1.16m 柜顶），只能弃用、拿其余 16 张循环复用。
3. **桌子是双人桌一切二**：原模型 12 张双人桌，拆成 24 张 0.61m 宽单桌，桌腿是碎面聚类拼出来的，
   不是完整的桌腿几何；用户看到的“悬浮金色平板”即源于此。
4. **格式进不了 Blender 4.2**：`.glb` 用 `EXT_meshopt_compression` + `KHR_mesh_quantization` +
   `KHR_texture_basisu` 三重压缩，Blender 4.2 自带导入器打不开，须先用 gltf-transform 去压缩、剥 KTX2 贴图
   （`buildings/classroom-tevy-plain.glb`，`tevy-decompress.mjs`）。
5. **tevy 站内没有独立的课桌椅模型**：站内搜到的只有教室整间（本件）、Office Chair（转椅，错）、
   Scholar's Writing Desk（1.15m 橡木古董书桌，带蜡烛墨水瓶，错）、Pine Spindle-Back Chair
   （厨房椅，错）——换一家是唯一出路。

### 7.4 为什么选 ①、另外几家差在哪

- **选 ①**：唯一同时满足四条的——①是**真正的学校课桌椅**（不是办公桌/餐椅/玩具），
  桌椅成对、同一系列同一材质；②桌架/椅架都是**完整弯钢圆管、真腿落地**（508 个顶点在地面），
  不是碎面拼出来的腿；③**米制实尺、无需缩放**，桌 0.70 高（SPEC 0.75，差 5cm，实测值不改比例）、
  椅座高 0.42，尺寸与上一轮 tevy 单桌（0.61 宽 / 0.71 高）同级，**可直接沿用现行 6 列×8 排=48 套布局**，
  不用重排教室；④面数最低档之一（65,280/48 套）；⑤CC0、直链、无登录。
- **② 差在哪**：桌子 1.8m 宽（双人桌口径 1.1–1.3m 的 1.4 倍）、自带桌面隔断屏挡视线，
  须拆隔断 + 改布局才能用；椅子本身不错（塑料壳 + 镀铬管腿），但配 ① 的桌椅对子更协调。
- **③ 差在哪**：桌子尺寸最贴任务口径（1.40×0.70，高 0.736），但它是**板脚办公桌**（两侧实心板 +
  后挡板、无管腿、无书篮），教室里一眼就是办公室；且椅子须另配（②的椅），不成对。
- **④ 差在哪**：桌是古董办公桌（4 抽屉、顶高 0.92m），椅是 2 倍比例尺的木餐椅（高 1.77m），
  两件都要大改（去抽屉、降顶高、×0.5 缩放），改完也不像课桌椅。poly.pizza 本身可用
  （`static.poly.pizza/<uuid>.glb` 直链、无登录；但站内 CC0 与 CC-BY 混排，须逐件核授权）。
- **⑤ 差在哪**：Kenney 包是 CC0 且下载通了，但桌椅是**玩具比例尺卡通方块**（桌高 0.38m、
  椅高 0.47m，整体须约 ×2 缩放；桌深 0.39m 偏浅），风格与 Demo 其他写实件不搭。
- **单桌宽度说明**：任务口径“桌约 1.1–1.3m”指**双人桌**；①是 0.60m 单人桌。
  现行教室布局本就是 24 张双人桌拆成的 48 张单桌（tevy 单桌 0.61m），① 单桌 0.60m 可 1:1 替换。
  若换装任务想改回双人桌：两张 ① 并排 = 1.20m 正好落在口径内；或改用备选 ③（1.40m 单张双人桌）。

### 7.5 其他渠道（试过没成的，如实记录，不编链接）

| 渠道 | 结果 | 备注 |
|---|---|---|
| BlenderKit 免费区 | **未下载（须免费账号 + Blender 内插件拉取）** | 站内确有免费桌椅部件，但无直接 .blend/.glb 直链；见 §3 同款结论。参考：免费建筑区 https://www.blenderkit.com/asset-gallery-pure?query=category_subtree%3Aarchitecture&page=6 |
| BlendSwap 免费区 | **未下载（须登录）** | 2026-11-24 复测：`https://blendswap.com/blend/19436/download`（Anime Classroom，CC0）经 curl 返回 52,152 字节 HTML 下载落地页、不是文件；站内下载须登录。见 §3 |
| Sketchfab CC0 区 | **未下载（须登录）** | 2026-11-24 复测：模型页 HTML 含 `Log in`，下载须登录账号，无免登录直链。参考 https://sketchfab.com/3d-models/3-unique-game-ready-buildings-73a2d53e6a5047789782329d0f268b93（见 §6） |
| CGTrader 免费区 | **未下载（页面被挡）** | 2026-11-24 复测：`https://www.cgtrader.com/free-3d-models/interior/other/school-chair-for-student` 经 curl 返回 HTTP 202、0 字节；下载本来就须注册。见 §6 |
| Poly Haven 模型区 | **未下载（API 不通）** | 2026-11-24 复测：`https://api.polyhaven.org/api/v1/assets?t=model` 返回 HTTP 522（与 §3 草模型时相同）；站内模型页是 JS 渲染，`dl.polyhaven.org` 直链须先拿到资产清单。参考 https://polyhaven.com/models |
| Kenney Furniture Kit | **已下载（见 7.2 ⑤）** | 下载不是普通直链：页面 JS `initiateDownload` 调 `GET https://kenney.nl/download-link/<hex-id>`（hex 解码为 `assets/furniture-kit`）返回签名 URL `https://kenney.nl/download/<id>/<sig>?expires=…`，再 curl 该 URL 得 ZIP。签名会过期，ZIP 已入库 `desks/kenney/furniture-kit.zip` |
| polyfork.dev | **未下载（授权非 CC0 + 只有教师桌）** | Teacher's Desk（1.4×0.7m、高 0.75m、532 面）GLB 直链可下（`https://polyfork.dev/cdn/teacher-s-desk-381eeb.glb`，无需账号），但 API 的 `license` 字段写明 GLB 是 **CC BY 4.0**（须署名）或 Polyfork licence（禁再分发），且是教师桌不是学生桌。参考 https://polyfork.dev/asset/teacher-s-desk-381eeb，授权页 https://polyfork.dev/licensing |
| Vorpal 3D（Wooden Classroom Desk With Attached Chair） | **未下载（授权不明）** | 页称免费、无注册、无下载限制，GLB 可下，但页面 JSON-LD 的 `license` 字段指向的是 `/privacy`（不是 CC 协议），授权无法确认，不敢入库。参考 https://vorpal3d.com/models/wooden-classroom-desk-with-attached-chair-lowpoly |
| itch.io Low Poly School Pack（reodesuxz） | **未下载（须走 itch 购买页）** | 27 件学校小道具、免费商用无需署名（禁转售），但无 curl 直链。参考 https://reodesuxz.itch.io/low-poly-school-pack（见 §6） |

### 7.6 文件清单（本次新增，`assets/external/desks/`，共 26 个文件，约 7.6 MB）

- `3dassets/`：`student-desk.glb`（51,796 B，**选定**）、`student-chair.glb`（43,632 B，**选定**）、
  `seminar-table.glb`（38,748 B）、`seminar-chair.glb`（34,900 B）、`desk-1400.glb`（30,204 B）。
- `polypizza/`：`quaternius-desk.glb`（135,916 B）、`quaternius-chair.glb`（13,360 B）。
- `kenney/`：`desk.glb`（15,048 B）、`chair.glb`（10,756 B）、`chair-desk.glb`（39,016 B）、
  `LICENSE-kenney.txt`（随包 CC0 说明）、`furniture-kit.zip`（5,130,729 B，整包 140 件；已解压取件后删提取目录，ZIP 保留）。
- `previews/`：10 张 640×360 Eevee 预览 PNG（每件 1 张，太阳光 3.5 + 淡蓝世界，见 7.2 结构栏）。
- `verify_results.json`：Blender 核验逐 mesh 明细（对象/面数/包围盒/落地顶点数/结论）。

### 7.7 给换装任务（下一波）的注意事项（只建议，不改文件）

- 直接用 `desks/3dassets/student-desk.glb` + `student-chair.glb` 替换 `cl-desks.py` 里的 tevy 拆件；
  两件均为 glTF（+Y up、米制、落地点 y=0），按 SPEC 局部坐标（房间中心原点、黑板墙 x=-4.84、学生面向 -x）
  旋转摆放；3DAssets 描述称用户面朝 +Z，换装时注意朝向。
- 布局不用重排：单桌 0.60×0.50 与现行 tevy 单桌 0.61×0.61 同级，6 列×8 排=48 套照旧；
  椅座高 0.42（tevy 0.45）、桌高 0.70（tevy 0.71、SPEC 0.75），均在 5cm 内。
- 材质按 SPEC §3：桌面木面 `#C8A06A`、椅面深色、钢架浅灰金属；两件原材质只有 2 种、无贴图，
  染色即可，无需重挂 PBR 贴图。
- 备选 ③ 的桌是板脚办公桌、备选 ② 的桌带隔断屏，换用前须先处理；④⑤ 均须重缩放，不推荐。

## 6. 草第二轮搜寻（2026-11-24 22:46–23:05 CST，R2-T11：只找模型、只下载、记来源）

> 背景：用户 2026-11-24 22:42 硬性要求——草地去网上搜更好的现成模型，全部用网上的或基于网上下载的再改，不要再手搓。
> 现状不满：上一轮草已有程序化 94,761 叶（单面三角，0.15–0.35 m）+ 真草丛 8,140 株，但总览视角仍是平板绿。
> 本轮只 sourcing：下载 + 只读核验 + 选型，不建模、不改 ov-lawn.py/.blend/.glb 与 ov-field，不碰 Godot scripts/scenes/data。
> R2-T3 总览绿化方案（`assets/blender/overview/GREEN_PLAN.md` / `green_layout.json`）本轮开工时尚未写出，
> 选型按“总览视角可见、有高度与颜色变化”选；密度估算沿用现行 ov-lawn.py 口径（草坪总面积 1,911 m²，
> 10 丛/m²，见 6.3）。
> 全部 `curl` 直链下载，无浏览器、无登录、无付费。授权均为 **CC0 1.0**（可自由改、商用、无需署名），
> Sketchfab 唯一命中的可下载草模型是 CC-BY（且下载要登录，未拿到，见 6.1）。

### 6.1 来源对比（7 家，3 家拿到文件）

| 来源 | 结果 | 授权 / 备注 |
|---|---|---|
| poly.pizza（https://poly.pizza） | **拿到 2 个**：Quaternius 草（见 6.2）。站内模型页 HTML 直接含 `static.poly.pizza/*.glb` 直链，无需登录；搜索 API 需 API key（`{"error":"You need an API key to do that dingus"}`），未用 | CC0 1.0（两模型页内嵌 `"CC0 1.0"`，作者 Quaternius，https://quaternius.com） |
| tevy.dev（https://tevy.dev） | **拿到 4 个模型共 9 个文件**（lod0/1/2，见 6.2）。`https://tevy.dev/models/<slug>/v1/lod<0/1/2>.glb` 直链，200，无需登录 | CC0 1.0（站内每模型均 CC0，页内 “License CC0 1.0”） |
| 3DAssets.dev（https://3dassets.dev） | **拿到 4 个**（见 6.2）。`https://cdn.3dassets.dev/assets/<id>/v1/model.glb` 直链，200，无需登录 | CC0 1.0（站内 “Every model on 3DAssets.dev is released under CC0 1.0”） |
| Poly Haven（https://polyhaven.com） | **未拿到**：`api.polyhaven.org/api/v1/asset/grass_medium_01` 本轮 curl 连接失败（000，0 字节），与上轮 522 同类失败；Grass Medium 01 依旧未拿到 | CC0（页面存在，https://polyhaven.com/a/grass_medium_01，仅作参考） |
| Sketchfab（https://sketchfab.com） | **未拿到**：搜索 API 可用，命中 “Tuft Of Grass”（uid `92ef3a61d1244e8186b4129b56e2c83d`，可下载）；但其授权是 **CC-BY 4.0**（非 CC0，需署名），且下载端点无鉴权返回 **401**，需登录/OAuth，未继续 | CC-BY 4.0（https://sketchfab.com/3d-models/none-92ef3a61d1244e8186b4129b56e2c83d，仅作参考） |
| CGTrader 免费区（https://www.cgtrader.com/free-3d-models/grass） | **未拿到**：curl 返回 HTTP 200 但 body 0 字节（空响应，疑似机器人拦截），未获文件列表 | 未知，未编造链接 |
| BlendSwap（https://blendswap.com） | **未拿到（需登录）**：上轮已实测下载页返回登录页，本轮未重测，沿用上轮记录；参考：Grass by gholm（CC0）https://blendswap.com/blend/4641 ；Realistic Grass Field by CraigForster（CC0）https://blendswap.com/blend/4678 | CC0（需登录后下载，仅作参考） |

### 6.2 候选实测表（全部已下载；尺寸/面数均为 Blender 4.2.0 只读实测，见 6.4 解码说明）

草坪总面积 1,911 m² = 教学楼南 60×20 + 南门北 40×15 + 池塘环带 25×18−π·12·9≈111（ov-lawn.py `lawns` / `TUFTS_PER_M2=10.0`）。
“1/m² 换算”指按 1,911 份铺满的总面数，仅作量级对照，实际部署密度见 6.3。

| # | 候选 / 文件（`grass/<来源>/`） | 资产页 | 直链 | 授权 | 单丛高 | 丛幅（宽×深） | 面数 | 颜色 | 总览可见性 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **tevy 草甸草块 lod1（主选）** `tevy/tevy-meadow-grass-patch-lod1.glb`（+ `-decoded.glb`） | https://tevy.dev/models/meadow-grass-patch | https://tevy.dev/models/meadow-grass-patch/v1/lod1.glb | CC0 | **0.76 m** | **1.89×1.96 m**（含 45 cm 外倾叶；核心 1×1 m，可 1 m 网格无缝拼） | **2,030** | 贴图：绿→枯黄叶尖 + 干草叶 + 穗（1024 KTX2 color+normal；预览非背景像素均值 #585828，橄榄绿→黄绿多档） | ★★★★★ |
| 2 | tevy 草甸草块 lod0（近景） `tevy/tevy-meadow-grass-patch.glb`（+ `-decoded.glb`） | 同上 | https://tevy.dev/models/meadow-grass-patch/v1/lod0.glb | CC0 | 0.76 m | 1.89×1.95 m | 11,024 | 同上（同套贴图） | ★★★★★ |
| 3 | tevy 草甸草块 lod2（远景） `tevy/tevy-meadow-grass-patch-lod2.glb`（+ `-decoded.glb`） | 同上 | https://tevy.dev/models/meadow-grass-patch/v1/lod2.glb | CC0 | 0.76 m | 1.21×1.21 m | 304 | 同上 | ★★★★ |
| 4 | **tevy 红燕麦草丛 lod1（点缀）** `tevy/tevy-red-oat-grass-clump-lod1.glb`（+ `-decoded.glb`） | https://tevy.dev/models/red-oat-grass-clump | https://tevy.dev/models/red-oat-grass-clump/v1/lod1.glb | CC0 | 0.98 m | 0.98×0.93 m | 824 | 贴图：锈红叶 + 下垂穗 + 深色芒（1024 KTX2；预览均值 #6F4E31，锈红/棕多档） | ★★★★ |
| 5 | tevy 红燕麦草丛 lod0 `tevy/tevy-red-oat-grass-clump.glb`（+ `-decoded.glb`） | 同上 | https://tevy.dev/models/red-oat-grass-clump/v1/lod0.glb | CC0 | 0.98 m | 0.98×0.93 m | 2,704 | 同上 | ★★★★ |
| 6 | tevy 红燕麦草丛 lod2 `tevy/tevy-red-oat-grass-clump-lod2.glb`（+ `-decoded.glb`） | 同上 | https://tevy.dev/models/red-oat-grass-clump/v1/lod2.glb | CC0 | 0.98 m | 0.98×0.93 m | 110 | 同上 | ★★★ |
| 7 | tevy 茅草丛 `tevy/tevy-thatching-grass-tussock.glb`（+ `-decoded.glb`） | https://tevy.dev/models/thatching-grass-tussock | https://tevy.dev/models/thatching-grass-tussock/v1/lod0.glb | CC0 | **1.60 m** | 1.69×1.63 m | 3,572 | 贴图：稻草 + 风化灰叶 + 锈色羽状穗（预览均值 #837662，稻草灰多档） | ★★★★★，但太高太干，不宜作草坪主草，备选池塘边点缀 |
| 8 | tevy 剪草坪簇 `tevy/tevy-lawn-tufts.glb`（+ `-decoded.glb`） | https://tevy.dev/models/lawn-tufts | https://tevy.dev/models/lawn-tufts/v1/lod0.glb | CC0 | 0.12 m | 1.03×1.02 m | 4,096 | 贴图：短亮绿剪草，平切叶尖带淡色（512 KTX2） | ★（太矮，总览不可见，淘汰） |
| 9 | poly.pizza Quaternius 高草 `poly-pizza/quaternius-grass-tall.glb` | https://poly.pizza/m/vUJjrRsFp4 | https://static.poly.pizza/0a84d74b-eb09-4794-ad58-dd10eed6b11e.glb | CC0 | 1.33 m | 0.64×0.74 m | 155 | 贴图：1024×1024 RGB PNG（无 alpha），深绿 #2D4312 + 黄绿 #7A8D2E 等 636 色，扁平风格化 | ★★★（高但窄，丛幅小） |
| 10 | poly.pizza Quaternius 草簇 `poly-pizza/quaternius-grass-tufts.glb` | https://poly.pizza/m/UGTOzcO3P2 | https://static.poly.pizza/99357ca2-6364-4990-8d4c-9bc5a1a5e859.glb | CC0 | 0.51 m | 1.84×0.50 m | 574 | 同上套 PNG 贴图（2 mesh 同材质 Grass） | ★★★（宽带状，扁） |
| 11 | 3dassets 沙丘草簇 `3dassets/3dassets-dune-grass-tuft.glb` | https://3dassets.dev/assets/beach-surf-and-paddle-kit-dune-grass-tuft-ae12b134 | https://cdn.3dassets.dev/assets/39457/v1/model.glb | CC0 | 0.91 m | 0.53×0.64 m | 1,380 | 纯色无贴图：草 #596B40 / 沙 #C2A36B / 浮木 #948C7D（3 材质）；26 叶 + 4 穗，带沙丘底座 | ★★★（沙丘底座不适合草坪） |
| 12 | 3dassets 紫沼草丛 `3dassets/3dassets-purple-moor-grass-tussock.glb` | https://3dassets.dev/assets/temperate-forest-ecology-purple-moor-grass-tussock-56681188 | https://cdn.3dassets.dev/assets/3849/v1/model.glb | CC0 | 1.01 m | 0.86×0.79 m | 779 | 纯色无贴图：干草 #B3A161 / 枯叶层 #735435；54 叶直立 | ★★★★（高，但纯色、无贴图） |
| 13 | 3dassets 丛生发草 `3dassets/3dassets-tufted-hair-grass.glb` | https://3dassets.dev/assets/temperate-forest-ecology-tufted-hair-grass-7d62ee65 | https://cdn.3dassets.dev/assets/3847/v1/model.glb | CC0 | 1.14 m | 0.75×0.72 m | 752 | 纯色无贴图：草 #759448 / 干草 #B3A161 双色；46 叶 + 14 花茎 | ★★★★（高，双色但纯色） |
| 14 | 3dassets 林地苔草丛 `3dassets/3dassets-wood-sedge-clump.glb` | https://3dassets.dev/assets/temperate-forest-ecology-wood-sedge-clump-9f0b2abd | https://cdn.3dassets.dev/assets/3848/v1/model.glb | CC0 | 0.56 m | 0.90×1.27 m | 480 | 纯色无贴图：单色橄榄 #5C7038 | ★★★（单色） |

上一轮基线（实测，供对比；文件在 `grass/` 根目录，未动）：程序化草叶原型 5 种，每叶 1 个三角，
每丛 3–5 叶、高 0.15–0.35 m、6 种平色（#3E6B2E–#869B4B），94,761 叶 ≈ 94,761 面；
`renderahouse-grass.glb` 高 0.20 m、1.02×1.00 m、512 面（501 mesh，低多边形草坪块）；
`tevy-wild-grass-clump.glb` 约 0.6 m 高、4,916 面、贴图草（meshopt，Blender 4.2 亦无法直读）；
`3dassets-tall-grass-clump.glb` 高 1.13 m、1.26×1.02 m、216 面、纯色、18 叶。

### 6.3 选定与打分（5 分制）

| 候选 | 高度 | 丛幅 | 颜色变化 | 总览可见性 | 面数可控 | 授权/直下 | 工具直用 | 小结 |
|---|---|---|---|---|---|---|---|---|
| **tevy 草甸草块 lod1（主选）** | 5 | 5 | 5 | 5 | 4 | 5 | 3* | 唯一为“铺满草坪”设计的模型：1 m 网格无缝拼 |
| tevy 草甸草块 lod0 | 5 | 5 | 5 | 5 | 2 | 5 | 3* | 同上，面数高，只放近景 |
| tevy 草甸草块 lod2 | 5 | 4 | 5 | 4 | 5 | 5 | 3* | 远景/大面积打底 |
| **tevy 红燕麦 lod1（点缀）** | 5 | 4 | 5 | 4 | 5 | 5 | 3* | 锈红色差，打破满眼纯绿 |
| tevy 茅草丛 | 5 | 5 | 3 | 5 | 4 | 5 | 3* | 备选：池塘边高草点缀，不作主草 |
| tevy 剪草坪簇 | 1 | 4 | 3 | 1 | 3 | 5 | 3* | 淘汰：0.12 m 总览不可见 |
| Quaternius 高草 | 5 | 2 | 3 | 3 | 5 | 5 | 5 | 备选：155 面极省，风格扁平、丛幅窄 |
| Quaternius 草簇 | 3 | 3 | 3 | 3 | 5 | 5 | 5 | 备选：574 面，宽带状 |
| 3dassets 紫沼/发草 | 5 | 3 | 2 | 4 | 5 | 5 | 5 | 备选：纯色无贴图，靠染色才有变化 |
| 3dassets 沙丘草/苔草 | 4/3 | 2/4 | 2 | 3 | 4/5 | 5 | 5 | 备选：沙丘底座/单色，不优先 |

\* 工具直用 3 分的原因见 6.4：tevy 原文件是 meshopt + KTX2，Blender 4.2 与 Godot 4.x 内置导入器均不直接支持
EXT_meshopt_compression（Blender 4.2 报错 “Extension EXT_meshopt_compression is not available”；
Godot 4.7.2 实测亦拒 meshopt，见 mint.gg 指南）；本轮已随附无损解码版 `-decoded.glb`（几何与原文件一致，
KTX2 贴图原样保留），Godot 4.4 读 KTX2（KHR_texture_basisu）以整合时 CI run 为准。

**选定：主选 tevy 草甸草块（lod1 大面积 + lod0 近景 + lod2 远景），点缀 tevy 红燕麦草丛（lod1，lod0/lod2 备用）。**
其余 8 个候选文件已下载在本地（`grass/poly-pizza/`、`grass/3dassets/`、tevy 茅草/剪草坪簇），
本轮只推选定模型 + 两份文档（见 6.5），其余凭本节直链可随时重下。

**比上一轮的草好在哪（四项实测对比）：**

| 对比项 | 上一轮最好（tevy 野草丛 / 3dassets 高草 / 程序化） | 本轮选定（tevy 草甸草块 lod1） | 结论 |
|---|---|---|---|
| 高度 | 程序化 0.15–0.35 m；野草丛约 0.6 m；高草 1.13 m 但纯色 | **0.76 m**（lod0/1/2 同高），是程序化最高档的 2.2 倍 | 总览视角下叶尖高出地面底板两倍多，不再贴地 |
| 颜色变化 | 程序化 6 种平色单面三角；高草单色；野草丛贴图绿→枯黄 | 1024 KTX2 真贴图：**绿→枯黄叶尖 + 干草叶 + 穗**，单丛内即有深浅冷暖变化；另有红燕麦锈红点缀破纯绿 | 从“六色平片”变“贴图渐变 + 干叶 + 锈红点缀” |
| 丛幅 | 程序化单丛约 0.1 m 宽；野草丛未实测（约 0.6 m 级）；高草 1.26×1.02 m | **1.89×1.96 m**（外倾叶），核心 1×1 m **可 1 m 网格无缝拼**，一片顶约 19 丛程序化草的覆盖 | 单丛覆盖大，总览下成片而不是碎点 |
| 总览可见性 | 程序化叶是单面三角、总览下呈平板绿；8,140 株真草丛只占草坪一小部分 | 整块草坪可由 1 m 拼块铺满：每块 0.76 m 高、有贴图明暗、有干叶穗影，远景亦有 lod2（304 面）保底 | 从“点缀”变“成片可见的草层” |

**密度 / 总面数估算（按 R2-T3 密度口径未出，先按现行 ov-lawn.py 面积与密度给三档，下一波施工时以 GREEN_PLAN 为准）：**

| 方案 | 铺法 | 总面数 |
|---|---|---|
| A. 全换 lod1（1/m² 拼满） | 1,911 块 × 2,030 面 | **3.88M 面** |
| B. 全换 lod2（1/m² 拼满） | 1,911 块 × 304 面 | **0.58M 面** |
| C. 全换 lod0（1/m² 拼满，仅近景） | 1,911 块 × 11,024 面 | 21.1M 面（太高，不推荐全铺） |
| **D. 推荐混合（程序化底 + 新草叠加）** | 程序化 94,761 面保留 + lod1 按 0.25/m²（478 块，0.97M 面）+ 红燕麦 lod1 按 0.05/m²（96 块，0.08M 面） | **新增约 1.05M 面**，草总计约 1.15M 面（现行 95k 面的约 12 倍；单丛面数仍远低于野草丛 4,916 面/丛的旧点缀） |
| E. 点缀 only（lod1 0.1/m² + 红燕麦 0.05/m²） | 191 块 lod1（0.39M）+ 96 块红燕麦（0.08M） | 新增约 0.47M 面 |

注：以上是 Blender 侧面数；Godot 侧以整合 run 实测为准。lod1/lod2 同包围盒（lod2 幅面略小 1.21 m），
混用三档 LOD 不会穿帮；红燕麦 lod2 仅 110 面，适合远景撒点。

### 6.4 核验方法与解码说明（诚实记录）

- 直下文件：20 个 GLB 全部 `file` 识别为 glTF binary，0 字节文件 0 个；poly-pizza / 3dassets 共 6 个
  （无 meshopt）直接用 Blender 4.2.0 `--background` 只读导入实测包围盒与面数（见 6.2 表）。
- tevy 文件：原文件含 `EXT_meshopt_compression` + `KHR_mesh_quantization` + `KHR_texture_basisu`（KTX2 贴图），
  Blender 4.2.0 直接导入失败（先报 meshopt，解码后报 basisu）。本轮用 glTF-Transform 4.5.1
  （`npx @gltf-transform/cli@4 copy`，无损解码 meshopt，几何零改动）生成 `-decoded.glb`：
  解码后 JSON 面数与原文件 accessor 计数一致（草甸 11,024/2,030/304；红燕麦 2,704/824/110；茅草 3,572；剪草坪 4,096），
  再剥贴图引用做 /tmp 临时量测版，Blender 实测包围盒与页标尺寸一致（草甸 0.76 m 高、1.89×1.95 m；
  红燕麦 0.98 m；茅草 1.60 m；剪草坪 0.12 m）。**解码是格式转换，不是手捏建模**：几何、UV、材质名与原文件一致，
  KTX2 贴图原样保留在 `-decoded.glb` 内；原文件（pinned v1）同时保留，可按直链重下核对。
- 颜色核验：Quaternius 贴图 PNG 直接 PIL 采样（1024×1024 RGB，636 色，主色深绿 #2D4312、黄绿 #7A8D2E）；
  3dassets 纯色取 glTF `baseColorFactor`（见 6.2 表）；tevy KTX2 贴图本机无 `ktx` CLI 未能直接解码采样，
  颜色以站方描述（绿→枯黄叶尖/干草叶/锈红）+ 官方预览图非背景像素采样为准（草甸均值 #585828 橄榄绿多档；
  红燕麦 #6F4E31 锈红多档；茅草 #837662 稻草灰多档），未编造贴图像素值。
- 未改任何 `.blend` / `.glb` 原文件与任何其他任务文件；只新增 `grass/tevy/`、`grass/poly-pizza/`、`grass/3dassets/` 下的文件与本文档。

### 6.5 文件清单（本轮新增 27 个文件，约 6.2 MB；全库合计 110 个文件）

- `grass/tevy/`：16 个文件——草甸草块 lod0/1/2 原文件 + `-decoded.glb`（6 个）、红燕麦草丛 lod0/1/2 原文件 + `-decoded.glb`（6 个）、
  茅草丛原文件 + `-decoded.glb`（2 个）、剪草坪簇原文件 + `-decoded.glb`（2 个），约 5.3 MB。
- `grass/poly-pizza/`：2 个文件（Quaternius 高草 79,796 B、草簇 767,660 B），约 0.85 MB。
- `grass/3dassets/`：4 个文件（沙丘 27,800 B、紫沼 39,264 B、发草 37,904 B、苔草 24,120 B），约 0.13 MB。
- 本轮新增合计 22 个 GLB 文件，约 6.2 MB；全库合计 83 + 22 = 105 个文件（不含本文档与 BLENDER_MODELS.md 的改动）。
- **推仓（本轮只推选定 + 两份文档）**：`grass/tevy/` 下草甸草块 lod0/1/2 原文件 + `-decoded.glb`（6 个）与
  红燕麦草丛 lod0/1/2 原文件 + `-decoded.glb`（6 个），共 12 个 GLB + `assets/external/SOURCES.md` +
  `BLENDER_MODELS.md`；其余 10 个候选 GLB 留本地，凭本节直链可重下。commit 见 BLENDER_MODELS.md §14。
