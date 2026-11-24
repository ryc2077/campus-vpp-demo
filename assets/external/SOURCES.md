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

## 10. 链接核验注记（2026-11-24，R2-T16）

> 核验方法：`curl -I -L`（UA 为浏览器）逐条验本文档全部链接；资产页与直链分开计；tevy / 3DAssets 直链另与本地文件逐字节比对（SHA-256）。
> 结论：**死链 0 条**。本文档原有链接一条未改、一条未删；以下只记录核验结果。

- 全部通过（200）：Poly Haven 9 个资产页 + 27 条直链；ambientCG 4 个资产页 + license 页 + 4 条 `get?file=` 直链；
  tevy 4 个模型页（school-building / classroom / school-corridor-lockers / grass-clump）+ 直链；Grab3D 3 个资产页 + 3 条直链；
  kit-predios 仓库页；Render a House 2 个博客页 + PNG ZIP + GLB/FBX 直链；3DAssets 高草丛资产页 + CDN 直链；
  BlendSwap 5 条、Sketchfab 模型页、Open3DModel、itch.io 学校包、Meshy 标签页；Kenney / KayKit / Quaternius 方案页见 BLENDER_MODELS.md §14.6。
- 瞬时失败、重试后 200（非死链）：`ambientcg.com/a/Grass004` 首次 000、重试 200；
  `ambientcg.com/get?file=Grass004_1K-JPG.zip` 与 `WoodFloor051` 同款首次 000、重试 200。
- 站方拦截、非死链（页面本身存在，保留原链接）：`staging.blenderkit.com` 资产页 curl 526/000，
  但浏览器打开确认页面存在（Outdoor Split Air Conditioner，FREE，496 面，2.1 MiB，与 §3 记录一致）；
  `blenderkit.com` 列表页与 `free3d.com` curl 403（反爬墙）；`cgtrader.com` 202（验证页）。
  以上 4 处 curl 未能验证，不判定为死链，待浏览器复核。
- 本次新定位（原只记站名、无单品页，现已逐字节验明，见 BLENDER_MODELS.md §17.5/§17.7）：
  3DAssets 草 4 件（CDN 39457/3849/3848/3847）、tevy 新草 4 件（v1/lod0.glb）、3DAssets 研讨桌椅 2 件（CDN 34746/34749）。
- 未进本文档的新批文件（`desks/`、`grass/` 新草、R2-T3 树方案）已记入 BLENDER_MODELS.md §17.5–§17.7；
  其中 7 项单品页（Poly Pizza 4 件、3DAssets 桌椅 3 件）由同轮 R2-T2（本文档 §7）、R2-T11（本文档 §6）落地时补齐，
  本任务对 7 条直链逐字节验明（SHA-256 与本地文件一致），**待补 0 项**。

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

## 9. 汽车模型 sourcing（R2-T8，2026-11-24 22:46–23:15 CST，只找模型、只下载、记来源）

> 背景：用户 2026-11-24 22:42 硬性要求——车的建模也去网上找，用网上的，不许手捏。
> 现状：充电区 ch-cars 3 辆手捏简易小车（蓝 #3B82C4、红 #C4534E、白 #D7DDE3，见 BLENDER_MODELS.md §3.5）与
> 停车区 ov-parking 3 辆简易小车，全部要换。本轮只 sourcing：下载 + 只读核验 + 选型，不建模、不改
> ch-cars.py/.blend/.glb 与 ov-parking，不碰 Godot scripts/scenes/data。换装是下一波任务。
> 目标：低多边形但结构真实的轿车（车身+车窗+车轮+车灯齐全，不许无轮平板），单车约 4.4×1.8×1.5 m，
> 最好一家出 3 辆不同颜色/款式。全部 `curl` 直链下载，无浏览器、无登录、无付费。
> 授权均为 **CC0 1.0**（可自由改、商用、无需署名）；唯一进实测的非 CC0 候选是 Khronos CarConcept（CC-BY 4.0，
> 需署名，且因面数过高被淘汰，未推仓，见 9.2）。

### 9.1 来源对比（7 家，3 家拿到文件）

| 来源 | 结果 | 授权 / 备注 |
|---|---|---|
| poly.pizza（https://poly.pizza） | **拿到 7 个**：Quaternius Cars 包 7 辆（见 9.2）。站内模型页 HTML 直接含 `static.poly.pizza/*.glb` 直链，无需登录；搜索 API 需 API key（`{"error":"You need an API key to do that dingus"}`），未用 | CC0 1.0（模型页 "Public Domain (CC0)"，作者 Quaternius，https://quaternius.com；整包页 https://poly.pizza/bundle/Cars-Bundle-FE5IWe6OMk） |
| Kenney Car Kit（https://kenney.nl/assets/car-kit） | **拿到整包**：Car Kit 3.1（45 个模型，含 sedan/suv/taxi 等，见 9.2）。官网下载是 JS 门控（`download-link/` 端点 curl 返回 404，旧直链 `kenney_car-kit.zip` 哈希已换，302 回资产页）；实测可用的 curl 直链是 OpenGameArt 镜像 `https://opengameart.org/sites/default/files/kenney_car-kit_3.1.zip`（4,814,237 B，包内 License.txt 载明 CC0） | CC0 1.0（包内 License.txt 全文；署名非强制） |
| Khronos glTF-Sample-Assets（https://github.com/KhronosGroup/glTF-Sample-Assets） | **拿到 1 个**：CarConcept（见 9.2）。`https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/main/Models/CarConcept/glTF-Binary/CarConcept.glb` 直链，11,778,688 B | **CC-BY 4.0**（需署名；若采用须在 SOURCES 与 Godot 内记署名）。本轮因面数过高淘汰，未推仓 |
| Sketchfab（https://sketchfab.com） | **未拿到**：下载 API 无鉴权返回 **401**，需登录/OAuth token，无 curl 直下路径；CC0 可下载车模型存在，但拿不到文件 | 按模型而定（CC0/CC-BY），未拿到，未编造链接 |
| BlendSwap（https://blendswap.com） | **未拿到（需登录）**：上轮已实测下载页返回登录页；本轮车分类页 `https://blendswap.com/blends/category/vehicles/cars` 返回 404（站内结构已改），沿用上轮“需登录”结论 | CC0/CC-BY（需登录后下载，仅作参考） |
| CGTrader 免费区（https://www.cgtrader.com/free-3d-models/car） | **未拿到**：分类页 curl 返回 202（JS 挑战页），免费模型下载均需账号登录，无 curl 直下路径 | 按模型而定，未拿到，未编造链接 |
| BlenderKit（https://www.blenderkit.com） | **未拿到**：搜索 API 无需鉴权可用（`https://www.blenderkit.com/api/v1/search/?query=car` 返回 200，4,118 条），但文件下载需免费账号 + 插件/API token，无直接 .blend/.glb 直链；上轮同结论 | 按资产而定（免费区多为 CC0/CC-BY），未拿到，未编造链接 |

### 9.2 候选实测表（尺寸/面数均为 glTF JSON 直读 + Blender 4.2.0 `--background` 只读导入实测，两者一致；glTF 坐标 X=宽、Y=高、Z=长）

| # | 候选 / 文件（`cars/<来源>/`） | 资产页 | 直链 | 授权 | 尺寸（长×宽×高 m） | 面数 | 结构（mesh / 材质） | 车身色（baseColorFactor 线性值） |
|---|---|---|---|---|---|---|---|---|
| 1 | **Quaternius Car（主选·蓝）** `quaternius/car-quaternius.glb`（164,752 B） | https://poly.pizza/m/Cz6yDaUcM9 | https://static.poly.pizza/59a67a6c-490e-472e-bae6-5a4d2541f1c7.glb | CC0 | **4.22×1.81×1.18** | **2,954** | 4 mesh：车身 + 后轮轴一体 + 左右前轮各一；6 材质 Blue/Windows/Black/Grey/Headlights/TailLights | Blue (0.278, 0.432, 0.640) |
| 2 | **Quaternius SUV（主选·白）** `quaternius/suv-quaternius.glb`（181,608 B） | https://poly.pizza/m/xsMtZhBkxL | https://static.poly.pizza/e5fbf2ee-5c9e-47d5-8ab6-80cacd463baa.glb | CC0 | **4.21×2.11×1.53** | **3,294** | 4 mesh，同上结构；6 材质 White/Windows/Black/Grey/Headlights/TailLights | White (0.559, 0.559, 0.559) |
| 3 | **Quaternius Sports Car 2（主选·橙→红）** `quaternius/sports-car-2-quaternius.glb`（171,300 B） | https://poly.pizza/m/OyqKvX9xNh | https://static.poly.pizza/e6410e19-a88f-4158-bc91-c19fccf85028.glb | CC0 | **3.97×1.80×1.16** | **3,066** | 4 mesh，同上结构；7 材质 Orange/DarkOrange/Windows/Grey/Headlights/TailLights/Black | Orange (0.639, 0.266, 0.086) |
| 4 | Quaternius Taxi（备选） `quaternius/taxi-quaternius.glb`（本地 /tmp，未推仓） | https://poly.pizza/m/x43lOScTpN | https://static.poly.pizza/3622a7bf-f213-44c8-8949-c1bdd1e961a9.glb | CC0 | 4.22×1.81×1.31 | 3,278 | 4 mesh，同上结构；6 材质 Yellow/Windows/Black/Grey/Headlights/TailLights | Yellow (0.640, 0.465, 0.045) |
| 5 | Quaternius Sports Car（备选） `quaternius/sports-car-quaternius.glb`（本地 /tmp，未推仓） | https://poly.pizza/m/1mkmFkAz5v | https://static.poly.pizza/34db1344-31cc-49ac-bc46-c055f68e39ca.glb | CC0 | 3.93×1.87×1.20 | 3,148 | 4 mesh，同上结构；6 材质 White/Windows/Grey/Headlights/TailLights/Black | White (0.549, 0.549, 0.549) |
| 6 | Quaternius Police Car（备选） `quaternius/police-car-quaternius.glb`（本地 /tmp，未推仓） | https://poly.pizza/m/BwwnUrWGmV | https://static.poly.pizza/179e43ce-b9e0-40cf-8b99-641693d3207e.glb | CC0 | 3.73×1.78×1.24 | 3,232 | 4 mesh，同上结构；8 材质 White/Windows/Grey/Headlights/Black/TailLights/WhiteLights/BlueLights | White + 警灯 |
| 7 | Quaternius Car 2（备选） `quaternius/car-2-quaternius.glb`（本地 /tmp，未推仓） | https://poly.pizza/m/unqqkULtRU | https://static.poly.pizza/d35173c8-6078-4367-8b1f2599f0bb7.glb | CC0 | 3.31×1.64×1.15 | 3,124 | 4 mesh，同上结构；7 材质 LightBlue/Windows/Black/Grey/Headlights/Material.007/TailLights | LightBlue (0.459, 0.548, 0.640) |
| 8 | Kenney sedan（次选） `kenney_car-kit_3.1.zip` 内 `Models/GLB format/sedan.glb`（本地 /tmp，未推仓） | https://kenney.nl/assets/car-kit | 镜像直链 https://opengameart.org/sites/default/files/kenney_car-kit_3.1.zip | CC0 | 2.55×1.50×1.45（含原点下沉：Y min −0.30） | 2,032 | 5 mesh：车身 + 4 轮各一；**仅 1 材质 colormap（共享 512² 贴图集）**，车窗/车灯是贴图着色、**无独立材质/几何** | 贴图集着色，无车身单色材质 |
| 9 | Kenney suv / taxi / sedan-sports / hatchback-sports（次选，同包） | https://kenney.nl/assets/car-kit | 同上镜像 zip | CC0 | 均为 2.55–2.85×1.30–1.50×1.25–1.65 | 2,072–2,474 | 5–6 mesh，车身 + 4 轮（+尾翼）；同为单 colormap 材质 | 同上 |
| 10 | Khronos CarConcept（淘汰） `khronos/CarConcept.glb`（本地 /tmp，未推仓） | https://github.com/KhronosGroup/glTF-Sample-Assets （Models/CarConcept） | https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/main/Models/CarConcept/glTF-Binary/CarConcept.glb | **CC-BY 4.0** | 原始包围盒轴向异常：X 2.47 / Y 4.56 / Z 1.74（长在 Y 轴，需重定向） | **213,347** | 97 mesh / 29 材质：全内饰、方向盘、踏板、刹车盘、雨刮一应俱全 | 多色车漆 Paint 1/2（Carmine/Pearl/Graphite 三色版） |

诚实说明（结构口径）：Quaternius 三车“车窗/车灯齐全”指车身 mesh 上以独立材质区分的面（Windows 深色窗面、
Headlights 前灯面、TailLights 尾灯面），不是独立 mesh；车轮是真独立 mesh（轮径 0.52 m，SUV 0.65 m），
不是平板贴图。全部三车**无贴图**，颜色全靠 `baseColorFactor` 纯色材质，Godot 导入无贴图依赖。
Blender 实测与 glTF JSON 直读逐项一致：car 5,662 顶点 / 2,954 面、SUV 6,294 / 3,294、Sports 2 为 5,882 / 3,066
（JSON 的 5,898 顶点含未用顶点，面数一致），Kenney sedan 3,184 / 2,032。

### 9.3 选定与打分（5 分制）

| 候选 | 授权/直下 | 结构完整 | 尺寸贴合（目标 4.4×1.8×1.5） | 面数可控 | 一家出 3 辆 | 换色易度 | 小结 |
|---|---|---|---|---|---|---|---|
| **Quaternius 三车（主选）** | 5 | 5 | 5 | 5 | 5 | 5 | **唯一满分**：同一包出蓝/白/橙三色三款式，车身单色材质可一键改色，3 辆合计 9,314 面 |
| Kenney Car Kit | 5 | 3 | 2 | 5 | 5 | 2 | 次选：轮子独立、面数低，但车窗/车灯只是贴图着色、无独立材质；2.55 m 玩具比例，需 ×1.73 放大，原点还沉在地下 0.30 m；换色要改共享贴图集，会连带改整包车的颜色 |
| Khronos CarConcept | 3 | 5 | 2 | 1 | 1 | 3 | 淘汰：结构最真（全内饰+刹车盘），但单辆 213,347 面、11.7 MB，3 辆 640k 面直接撑爆总览；CC-BY 需署名；只有一款概念车、无三色；轴向还需重定向 |
| Sketchfab / BlendSwap / CGTrader / BlenderKit | 0 | — | — | — | — | — | 未拿到文件：登录/OAuth 墙，无 curl 直下路径（见 9.1） |

**选定：Quaternius Cars 包三辆——Car（蓝）、SUV（白）、Sports Car 2（橙）。**
三辆合计 9,314 面、约 0.52 MB，进充电区 + 停车区共 6 个车位复用也仅约 18.6k 面（两处各 3 辆），
远低于总览现有 13,036 对象的量级。颜色与现行手捏三色对应：蓝车身已是蓝色系（与 #3B82C4 同色系）、
白 SUV 即白车；**包内没有出厂红色车**，最接近红的是橙色 Sports Car 2——换装时把 Orange/DarkOrange
两材质的 `baseColorFactor` 改为 SPEC 红 #C4534E（sRGB，线性约 0.55/0.09/0.08，换装时以 Blender 取色为准），
这是改两个材质数值，不是手捏建模。备选：若不接受改色，Taxi 黄 / Police 白+警灯 / Sports Car 白均可凭直链重下，
但警灯/出租车顶灯与校园充电区场景不搭，不优先。

**比手捏小车好在哪（四项实测对比）：**

| 对比项 | 现行手捏（ch-cars / ov-parking） | 本轮选定（Quaternius 三车） | 结论 |
|---|---|---|---|
| 结构真实度 | 简易几何拼合（SPEC §6 充电区、BLENDER_MODELS.md §3.5）：车身平板 + 贴式车窗 | 车身有真实轿车轮廓（引擎盖/车顶/腰线一体成型），车窗/前后灯为独立材质面，4 轮为独立 mesh（轮径 0.52–0.65 m） | 从“方块小车”变“有轮廓、有灯窗、有真轮子的轿车” |
| 尺寸 | 手捏未按实尺（SPEC 未载实测车长） | 实测 3.97–4.22 m 长、1.80–2.11 m 宽、1.16–1.53 m 高，与目标 4.4×1.8×1.5 m 贴合（按长统一缩放到 4.4 m 仅 ×1.04–1.11） | 接近真车比例；SUV 实测宽 2.11 m，比目标宽 17%，换装时按车位核对 |
| 面数 | 手捏面数未单列（低，但结构假） | 3 辆合计 9,314 面，单辆约 3.0–3.3k 面 | 面数仍是低多边形量级，不拖总览 |
| 换色/复用 | 每辆手写颜色参数 | 车身是单一命名材质（Blue/White/Orange），改一个 `baseColorFactor` 即换整车漆；三款式同包，风格统一 | 充电区与停车区 6 辆可同款不同色复用，不用再手捏 |

**换装提示（下一波任务，不在本轮做）：**① 三车 glTF 前向为 +Z，Blender 导入后长在 Y 轴，Godot 导入时以前向 −Z 为准，
换装脚本需核对朝向（以充电桩前车头朝外为准）；② 统一缩放：按长缩放到 4.4 m（car ×1.043、SUV ×1.045、
Sports 2 ×1.108）或保留原生 3.97–4.22 m（紧凑轿车实尺，差 <10%，可不缩放）；③ Sports 2 改红（见上）；
④ SUV 宽 2.11 m 比目标宽 17%，若车位划线按 1.8 m，换装时可只缩 X 或接受 SUV 本身更宽；
⑤ 三车原点均在地面中心附近（Y min −0.03–−0.01，基本贴地），不用像 Kenney 那样抬 0.30 m；
⑥ 车漆可按 ch-cars 旧配方挂清漆（Coat Weight 1.0 / Coat Roughness 0.05）与车窗深色配方复用，
材质名已是 Blue/White/Orange/Windows/Headlights/TailLights，改色只动数值。

### 9.4 文件清单（本轮新增 3 个文件，约 0.52 MB；全库合计 113 个文件）

- `cars/quaternius/`：3 个文件——`car-quaternius.glb`（164,752 B）、`suv-quaternius.glb`（181,608 B）、
  `sports-car-2-quaternius.glb`（171,300 B），合计 517,660 B。md5：car `782e32948f29775b543d8f61dedf53d1`、
  suv `e4875bde83fa3563be010895619214b5`、sports-2 `c5ae5780adb5350d172f240820e42b4b`。
- 本轮新增合计 3 个 GLB 文件，约 0.52 MB；全库合计 110 + 3 = 113 个文件（不含本文档与 BLENDER_MODELS.md 的改动）。
- **推仓（本轮只推选定 + 两份文档）**：`cars/quaternius/` 下 3 个 GLB + `assets/external/SOURCES.md` +
  `BLENDER_MODELS.md`；其余 7 个候选 GLB（Quaternius Taxi/Sports/Police/Car 2、Kenney 整包、Khronos CarConcept）
  留本地 /tmp，凭本节直链可随时重下。commit 见 BLENDER_MODELS.md §16。
- **未动**：`ch-cars.py` / `.blend` / `.glb`、ov-parking、Godot scripts/scenes/data 一律未碰；换装是下一波任务。

## 8. 云：实拍云照片贴图（R2-T12，2026-11-24 22:46–23:10 CST）

> 用户 2026-11-24 22:43 硬性要求：云也要搞好，用网上的建模；去网上找现成的云模型/云材质
> （CC0，记来源），不许手捏。现状是 Godot 程序化白球（`scripts/weather_system.gd`
> `_build_clouds`：7 个白色半透明球 + 5 个圆柱云影），用户嫌假。
> 方案（GL Compatibility 下体积云不可行——无体渲染管线）：**billboard 贴图云片**，
> 每组云 = 1 张主云片 + 2 张小云片拼成云团，`BILLBOARD_ENABLED`，五档联动。
> 原图未入仓（可按直链重下；SHA256 见下表）；入仓的只有两张衍生 PNG + 本节记录。

### 8.1 候选对比（3 家）

| # | 候选 | 形式 | 授权 | 结论 |
|---|---|---|---|---|
| A | **Wikimedia Commons 实拍云照片**（见 8.2） | 云照片 → 裁切 + 抠天成透明 PNG | CC0 / CC-BY 4.0（逐张见表） | **选定**：真照片、蓬松感最好、curl 直链、无登录、无付费 |
| B | **Poly Haven 云 HDR（`cloud_layers` / `kloofendal_48d_partly_cloudy`）** | 360° 等距圆柱全景天空 HDRI（.hdr/.exr + tonemapped JPG） | CC0 1.0 | 未选：整幅是天空全景（含地面/地平线/太阳眩光），没有孤立云朵可裁；作 billboard 须先裁云块再抠天，与 A 同工作量且等距投影拉伸变形；HDR 格式还须转码。API 本轮实测可用，直链见下（仅作参考，未下载） |
| C | **Sketchfab 云团 3D 模型** | glTF 模型 | 混杂 | 未选：API 搜索 `realistic cloud` 前 3 条无一是云模型（地球模型 ×2 + Standard 授权不可下载）；可下载的云模型须账号 OAuth 才能取下载链接，curl 直下 401；且低多边形卡通云居多，不合“写实蓬松”要求 |
| — | OpenGameArt / Kenney | 像素/卡通云贴图 | CC0 | 未选：搜到的全是像素风、太空星云背景或卡通云，不写实（见 8.4） |

### 8.2 选定文件（`assets/external/clouds/wikimedia-commons/`，共 2 个 PNG + 本目录 README.md）

| 文件 | 尺寸 / 大小 | 原图（资产页 + 直链 + 授权 + SHA256） | 用途 |
|---|---|---|---|
| `cloud_puff.png` | 870×780 RGBA，601,153 B，SHA256 `9dcf668079d912f2ca8521cfa91a75719bcfb78757e63abee3a81b5b4dafdbf4` | 《A single cumulus cloud in a clear daytime sky.jpg》，WarmaFiesta，2025-09-17；资产页 https://commons.wikimedia.org/wiki/File:A_single_cumulus_cloud_in_a_clear_daytime_sky.jpg ；原图直链 https://upload.wikimedia.org/wikipedia/commons/5/5c/A_single_cumulus_cloud_in_a_clear_daytime_sky.jpg （2448×3264，2,606,277 B，SHA256 `a9465995528a7a014a50aa322388c9eb37383abeee31a02e834f375f9e029976`）；**CC-BY 4.0（须署名：WarmaFiesta，见本节与 README.md）** | 晴/多云/阴天用积云 |
| `cloud_storm.png` | 1024×717 RGBA，1,174,189 B，SHA256 `98454c644949515bb9388726302129375c8dab7213fdc8429311f1109c717c95` | 《Cumulonimbus viewed from airplane.jpg》，Shyamal，2016；资产页 https://commons.wikimedia.org/wiki/File:Cumulonimbus_viewed_from_airplane.jpg ；原图直链 https://upload.wikimedia.org/wikipedia/commons/a/a1/Cumulonimbus_viewed_from_airplane.jpg （4354×3136，6,670,299 B，SHA256 `86bc999ead65bdeef6b3c45842e92a52dc7824f5a895285cec894144d9ac8dbb`）；**CC0 1.0（无需署名）** | 雨/暴雨用积雨云团 |

### 8.3 衍生方法（裁切 + 抠天，不是手绘/手捏）

- `cloud_puff.png`：原图 (850,1420)–(1720,2200) 只取孤立积云本体（树与地面已排除）；
  白度键抠天（min 通道 smoothstep 0.30→0.80：深蓝天空 min≈0.1–0.3 透明、白云 min≈0.85–1.0 实）+
  裁切边 9% 羽化 + 轻度去饱和（去蓝调、保留亮度明暗）。本地目视验证：致密花椰菜状云顶、
  底部轻 wispy、背景干净（见本节方法记录；脚本 `/tmp/cloud-cand/make_sprites.py` 未入仓）。
- `cloud_storm.png`：原图 (1500,1000)–(3900,2680) 取中央亮白积雨云塔；白度键（0.32→0.85）+
  羽化 + 去饱和。灰色云幕背景无法用蓝天键分离，保留为半透明云幔，雨天压暗后正好作雨层。
  本地目视验证：致密云团、蓬松感好。
- 试过没成的抠天：`Cumulus congestus clouds (27075262952).jpg`（CC0，Flickr 8469…，
  https://commons.wikimedia.org/wiki/File:Cumulus_congestus_clouds_(27075262952).jpg ）
  塔身是逆光亮边 + 暗蓝灰内腔，白度键与去饱和键都只能抠出细弧、留灰雾，未采用，
  已弃用（原图 SHA256 `bd0bf1717143b81f90ed6961ce1d8405e49ba401f9664703684594c16f5cfbdd`）。
- 直链注意：upload.wikimedia.org 对共享出口 IP 有 429 限流（本轮首两次直下原图即 429）；
  加 UA（`CampusVPP-Demo/1.0 … curl`）+ 间隔 5–8 秒逐张重下即通；1280px 缩略图走
  `…/thumb/<hash>/<name>/1280px-<name>` 同样可用。

### 8.4 其他试过没成的（诚实记录，不编链接）

- Poly Haven `cloud_layers`：资产页 https://polyhaven.com/a/cloud_layers（CC0），
  API `https://api.polyhaven.com/files/cloud_layers` 本轮实测可用；1K tonemapped JPG 直链
  https://dl.polyhaven.org/file/ph-assets/HDRIs/extra/Tonemapped%20JPG/cloud_layers.jpg （8,068,365 B），
  2K HDR 直链 https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/2k/cloud_layers_2k.hdr （6,985,914 B）。
  `kloofendal_48d_partly_cloudy`：资产页 https://polyhaven.com/a/kloofendal_48d_partly_cloudy ，
  1K tonemapped JPG https://dl.polyhaven.org/file/ph-assets/HDRIs/extra/Tonemapped%20JPG/kloofendal_48d_partly_cloudy.jpg （5,275,330 B）。
  两者均未下载（见 8.1 候选 B 未选原因）。
- Sketchfab API 搜索（`https://api.sketchfab.com/v3/search?type=models&q=realistic%20cloud&count=3`，
  无 token）：返回 Realistic Earth 8K（CC-BY，可下载）、Realistic Earth w Terrain Clouds Ocean and Sky
  （CC-BY，可下载）、REALSTICK CLOUD（Standard，不可下载）——无可用云模型；`license=CC0` 参数被拒
  （`Select a valid choice. CC0 is not one of the available choices.`）。
- OpenGameArt 搜 “CC0 cloud texture transparent PNG”：命中全是像素纹理、太空星云背景
  （如 https://lpc.opengameart.org/node/8223），无写实云片。

### 8.5 接入（Godot 侧，R2-T12）

- `scripts/weather_system.gd`：`_build_clouds` 改为 7 组云片（主 + 2 小，同材质）；
  `set_weather` 按档换贴图（雨/暴雨 → storm，其余 → puff）、按 `cloud_cover` 显隐
  （晴 1 / 多云 3 / 阴 5 / 雨 6 / 暴雨 7 组）、按档缩放（0.9/1.0/1.12/1.18/1.25）；
  云影 blob 对齐到前 5 组云的地面投影（x/z ×0.5 收入校园范围）；漂移时小云片跟主云片走。
  `data/weather.json` 业务数、天气切换逻辑、其他系统一律未动。
- `tools/verify_fixes.gd`：+11 项云检查（贴图非空、7 组 + 14 小云片、QuadMesh + BILLBOARD、
  五档云量 1/3/5/6/7、雨/暴雨换 storm 贴图、暴雨 1.25×、回晴天恢复）。
- `tools/shots_all.sh`：+2 张（18-overview-cloudy、19-overview-overcast），旧 shots 只有雨/暴雨档，
  多云/阴两档无图可验。

## 9. R2-T9 PBR 硬性整改衍生贴图（`pbr-tinted/`，2026-11-24）

> 背景：用户 2026-11-24 22:42 硬性要求建筑外立面与沥青路必须挂真实材质。
> 逐件核查结论（见 `BLENDER_MODELS.md` §13）：节点连线全部完整（baseColor+rough+normal
> 均已链接），光板根因是烘焙贴图内容近乎平坦（墙法线图标准差约 0.5–3、沥青 color 图
> 瓦片内标准差约 4）且一张 1024 图拉伸覆盖整面 40 m 墙 / 260 m 路（约 4.6 m/纹素）。
> 本节文件全部由上文 §1 已下载的 CC0 包经脚本衍生（染色到 SPEC §3 配色、对比度提升、
> 法线放大、粗糙度校准），未引入新手绘贴图，授权仍为 CC0 1.0。生成脚本逻辑见
> `assets/blender/overview/_pbr_apply.py` 头注与本节加工说明；原始包见 §1。

### 9.1 加工方法（诚实记录，非手捏材质）

- 染色：按通道增益把原图均值移到 SPEC 十六进制（sRGB 空间），如沥青原图均值
  (89,80,70) → `#424A52` (66,74,82)。
- 对比度提升：以目标均值为中心放大偏差——沥青 ×3.0、灰泥/混凝土/铺装 ×2.0、
  屋顶/砖 ×1.5（原图 1K 下颗粒本身极淡：沥青 diff 标准差约 3.5、白灰泥约 0.9）。
- 大尺度斑驳：可平铺低频正弦叠加（整周期，±5% 墙/沥青/铺装、±3% 屋顶/砖/混凝土），
  让大面在中距离仍有明暗变化；接缝处连续，无可见平铺接缝。
- 法线放大：R/G 偏离 128 的部分放大后重归一化（灰泥 ×2.0、混凝土 ×1.5、沥青 ×2.0、
  铺装 ×2.0），存无损 PNG；屋顶（灰瓦，源法线标准差约 25）与砖（约 11–16）不放大。
- 粗糙度：原包 rough 图直用；唯沥青按任务要求缩放到均值 0.90（源图均值 0.77 →
  `asphalt_rough_090.jpg` 均值 229.5/255）。
- UV：逐面盒式投影按真实米制平铺（墙/混凝土 2 m、沥青 4 m、铺装/屋顶 3 m、砖 1.5 m），
  不再用烘焙分瓦片 UV；贴图 Repeat 平铺，glTF 采样器默认 repeat。

### 9.2 文件清单（`pbr-tinted/`，共 19 个文件）

| 文件 | 来源包 | 用途（SPEC 配色） |
|---|---|---|
| `plaster_F3E9D2_color.jpg` / `plaster_DFE9F2_color.jpg` / `plaster_F6D9C0_color.jpg` | ambientCG Plaster001（https://ambientcg.com/a/Plaster001）Color 图染色 | 外墙灰泥：米白 `#F3E9D2` / 蓝灰 `#DFE9F2` / 浅橙 `#F6D9C0` |
| `plaster_normal_amp2.png` | 同上 NormalGL 图 ×2.0 | 外墙法线 |
| `concrete_B9B3A8_color.jpg` / `concrete_D8D2C4_color.jpg` / `concrete_424A52_color.jpg` | Poly Haven concrete_wall_007（https://polyhaven.com/a/concrete_wall_007）diff 图染色 | 混凝土 `#B9B3A8` / 檐口 `#D8D2C4` / 屋顶防水层深灰 `#424A52` |
| `concrete_normal_amp15.png` | 同上 nor_gl 图 ×1.5 | 混凝土法线 |
| `roof_424A52_color.jpg` | Poly Haven grey_roof_01（https://polyhaven.com/a/grey_roof_01）diff 图染色 | 屋顶深灰 `#424A52` |
| `brick_8E2F28_color.jpg` / `brick_A63A2C_color.jpg` | Poly Haven red_bricks_04（https://polyhaven.com/a/red_bricks_04）diff 图染色 | 艺体馆红墙 `#8E2F28` / 砖砌压边 `#A63A2C` |
| `asphalt_424A52_color.jpg` | Poly Haven asphalt_01（https://polyhaven.com/a/asphalt_01）diff 图染色 | 沥青路 `#424A52` |
| `track_B8543F_color.jpg` | 同上 diff 图染色（R2-T9b，2026-11-25；与 `tint_textures.py` 同款线性空间染色，R 缩放钳制 4.0，实测均值 (170,84,63)） | 跑道红 `#B8543F` |
| `asphalt_normal_amp2.png` | 同上 nor_gl 图 ×2.0 | 沥青法线 |
| `asphalt_rough_090.jpg` | 同上 rough 图缩放至均值 0.90 | 沥青粗糙度 |
| `paving_D8D2C4_color.jpg` / `paving_DCD6C8_color.jpg` / `paving_C9C2B0_color.jpg` / `paving_E8B400_color.jpg` | Poly Haven concrete_pavement_03（https://polyhaven.com/a/concrete_pavement_03）diff 图染色 | 铺装 `#D8D2C4` / 步道 `#DCD6C8` / 压边石 `#C9C2B0` / 盲道黄 `#E8B400` |
| `paving_normal_amp2.png` | 同上 nor_gl 图 ×2.0 | 铺装法线 |

粗糙度与未放大法线直接引用原包文件，不另复制：
Plaster001 Roughness、concrete_wall_007 rough/nor（已放大版除外）、grey_roof_01 rough/nor、
red_bricks_04 rough/nor、concrete_pavement_03 rough。玻璃不贴图（透明材质），与 §1 相同。

## 11. 树模型 sourcing（R2-T15，2026-11-24 22:55–23:38 CST，只下模型、记来源）

> 施工：`assets/blender/overview/ov-trees.py` v3（473 棵：新种 327 + 旧树换模 146）。
> 全部 `curl` 直链下载，无浏览器、无登录、无付费。授权均为 **CC0 1.0**。
> 每个源模型先经 Blender 量包围盒实测高度再缩放（实测表见 §11.3，ov-trees.py
> `MEASURED` 日志逐项打印）；颜色走源模型自带材质直连 Base Color，无 ColorRamp。
> 校验：16 个 Kenney `.glb` 用 Python 直读 JSON（包围盒/三角面/材质 baseColorFactor）+
> Blender 4.2.0 导入探针（每材质 z 范围、冠底）；4 个 Quaternius `.gltf` 同法直读 +
> 导入验证；SHA-256 前 16 位见 §11.4。

### 11.1 Kenney Nature Kit（主力：行道树 + 点缀 211 棵新种 + 密植带 216 棵，见 §11.5）

- 资产页：https://kenney.nl/assets/nature-kit
- 授权：CC0 1.0（随包 `LICENSE-kenney.txt` 原文：License: Creative Commons Zero, CC0，
  http://creativecommons.org/publicdomain/zero/1.0/）
- 直链：站内 `https://kenney.nl/download-link/6173736574732f6e61747572652d6b6974`
  （curl 带 Referer + Cookie 取签名 URL 后下载；签名有时效，过期按同法重取；
  本次下载 `kenney_nature-kit.zip` 10,537,521 B，Nature Kit 2.1，330 个模型）
- 本地：`trees/kenney-nature-kit/`（原包 ZIP + `LICENSE-kenney.txt` + 选用的 16 个 `.glb`）
- 材质：纯色 `baseColorFactor`（无贴图），树干 `woodBark`（线性 0.886/0.514/0.341）、
  阔叶 `leafsGreen`（线性 0.161/0.788/0.671）、松针 `leafsDark`、深树干 `woodBarkDark`；导入 Blender 后同名材质去重。
- 未用模型（有意排除）：`tree_cone`（单圆锥，正是本次要淘汰的形状）、`tree_fat` /
  `tree_simple` / `tree_small`（单团树冠）、`tree_blocks`（方块堆）、全部棕榈
  （`tree_palm*`）、地被松（`tree_pineGroundA/B`，无树干）。

### 11.2 Quaternius Stylized Nature MegaKit Standard（仅 D3 池塘 12 棵特征树）

- 资产页：https://store.godotengine.org/asset/quaternius/stylized-nature-megakit/
  （作者 Quaternius，包主页 https://quaternius.com/packs/stylizednaturemegakit.html）
- 授权：CC0 1.0（随包 `LICENSE-Quaternius-Standard.txt` 原文：License: CC0 1.0 Universal，
  https://creativecommons.org/publicdomain/zero/1.0/；Standard 免费版含 68/116 个模型）
- 直链：Godot 商店下载路由 `https://store.godotengine.org/asset/quaternius/stylized-nature-megakit/download/31/`
  （302 跳转到签名对象存储 URL 后下载 `Stylized_Nature_MegaKitStandard.zip` 104,088,529 B；
  签名有时效，过期按同路由重取）
- 本地：`trees/quaternius-stylized-nature/`（选用的 4 个 `.gltf` + `.bin` + 4 张贴图 +
  `LICENSE-Quaternius-Standard.txt`；全包 ZIP 104 MB 未入库）
- 材质：树皮/叶贴图直连 Base Color，`alphaMode=MASK`、`alphaCutoff=0.2`（叶卡镂空），
  树皮带法线贴图；树皮/松叶贴图由 2048×2048 降采样至 1024×1024（PIL LANCZOS，
  总览尺度够用，GLB 瘦身约 6 MB），叶贴图 `Leaves_NormalTree_C.png` 原生即 1024 不动。
- 取用：`CommonTree_3` / `CommonTree_5`（阔叶）与 `Pine_4` / `Pine_5`（松塔）各 3 棵，
  共 12 棵（D3 池塘，8–12m）。

### 11.3 实测高度与三角面（Blender 4.2.0 导入实测，地上高 = 顶点 zmax；Kenney 树干根部 zmin=0，Quaternius 根系 zmin=-0.24m 埋地下）

| 模型 | 原生高 | 三角面 | 冠底（叶最低处） | 用途 |
|---|---|---|---|---|
| `tree_default` | 1.71m | 114 | 0.80m | 行道/点缀 |
| `tree_oak` | 1.23m | 196 | 0.50m | 行道/点缀/密植 |
| `tree_detailed` | 1.33m | 402 | 0.45m | 行道/点缀 |
| `tree_tall` | 1.69m | 72 | 0.29m | 行道/密植 |
| `tree_pineDefaultA` / `tree_pineDefaultB` | 1.55m | 230 / 246 | 0.54m | 行道/点缀 |
| `tree_plateau` | 1.25m | 215 | 0.42m | 行道/点缀 |
| `tree_thin` | 1.49m | 228 | 0.50m | 行道/点缀 |
| `tree_pineTallA` / `B` / `C` / `D` | 1.53 / 1.93 / 1.67 / 2.08m | 78 / 78 / 98 / 98 | 0.63 / 1.03 / 0.63 / 1.03m | 密植带 |
| `tree_pineTallA/B/C/D_detailed` | 同上 | 134 / 166 / 154 / 170 | 同上 | 密植带 |
| `CommonTree_3` / `CommonTree_5` | 9.18 / 6.76m | 3505 / 3182 | 4.59 / 3.38m | D3 特征树 |
| `Pine_4` / `Pine_5` | 10.00 / 8.49m | 3370 / 1646 | 5.00 / 4.24m | D3 特征树 |

缩放后实测（ov-trees.blend 回读，地上高）：行道树 5.0–8.0m、密植带 8.0–15.0m、
池塘特征树 8.7–12.0m、楼间点缀 4.05–7.9m；逐棵树干露出 ≥1.2m（`crown_z0 × scale`
逐棵过滤，不足者换 fallback 模型）。`ov-trees.glb` 120,634 tris（预算 ≤300k），
473 个对象，20 个共享 mesh，8 种材质。

### 11.4 文件清单与 SHA-256（前 16 位）

- `trees/kenney-nature-kit/`：`kenney_nature-kit.zip`（10,537,521 B）、`LICENSE-kenney.txt`、
  16 个 `.glb`：tree_default `562d29638c902de3`、tree_detailed `c041daf2f0fb1d49`、
  tree_oak `d7fd8773674928c5`、tree_pineDefaultA `60d8f352fa3659ed`、
  tree_pineDefaultB `a752ea5775c6fb17`、tree_pineTallA `e0a56eb196d8a64b`、
  tree_pineTallA_detailed `9ba6337460e718b8`、tree_pineTallB `49b54146351e1e00`、
  tree_pineTallB_detailed `a26b4434e1592ec1`、tree_pineTallC `e8b97fa086e1ac9b`、
  tree_pineTallC_detailed `b538e229a9fb8cbb`、tree_pineTallD `df5ffca50fc2e39a`、
  tree_pineTallD_detailed `a2fac08d7cb337e7`、tree_plateau `7f19e347ff28703d`、
  tree_tall `3515a8826044d91e`、tree_thin `f0f1f6861fe04469`。
- `trees/quaternius-stylized-nature/`：`LICENSE-Quaternius-Standard.txt`、
  CommonTree_3.gltf `17c6537aa8042bb7` / .bin `24541f46fd9553e2`、
  CommonTree_5.gltf `fb7061f2bf9fe850` / .bin `0e617612d50e6bb2`、
  Pine_4.gltf `d8978cfd5a29a224` / .bin `0a04c88f619924d9`、
  Pine_5.gltf `bb060ce1420af32d` / .bin `18982d7f6c430d1a`、
  Bark_NormalTree.png `4e48de28db62dc40`、Bark_NormalTree_Normal.png `e42d10124797a7cf`、
  Leaf_Pine_C.png `8dbee67418b22e73`、Leaves_NormalTree_C.png `983746bcdcb05d94`。

### 11.5 来源偏差（诚实记录：R2-T3 方案原定来源未全部按原计划拿到）

| 方案原定 | 实际 | 原因 |
|---|---|---|
| KayKit Forest Nature Pack 免费档（密植带 104 棵） | **未下载，改用 Kenney 松树**（`tree_pineTall A–D` 及 detailed 版 + oak/tall，共 216 棵含旧树沿线 112 棵） | itch.io 免费档须走 `/purchase` POST 拿下载链接；该 POST 触发过一次访问审批超时未应答，按指令不再重试。页面 HTML 内无 upload_id、AssetSifter / Godot 商店 / GitHub 镜像均无免费档直链。Kenney 松树同为 CC0 低多边形、树干 + 多层松塔冠，三角面更低（78–196 vs KayKit 约 500），风格与行道树统一。KayKit 资产页 https://kaylousberg.itch.io/kaykit-forest（CC0 1.0，页面 200 已核）仍列作备选，若后续拿到直链可再换。 |
| Quaternius Ultimate Nature Pack（2019，D3 12 棵，取 `Tree` / `Pine_Tree_1` / `Birch_Tree_1` / `Tree-Stylized`） | **改用同一作者同一授权的 Stylized Nature MegaKit Standard**（见 §11.2，取 `CommonTree_3/5` + `Pine_4/5`） | 官网下载走 Google Drive 共享文件夹（`1-Kl0L_Jg8awbh0S5T-z3zxh4mVlnxTpa`），实测全部文件报 `Quota exceeded`（公开配额耗尽），curl 无法直下；包内也无上述四个名字。Stylized 包 D3 仍只用 12 棵，未整片铺。另：GitHub 镜像 badestrand/threejs 仅含 `BirchTree_1` 一个文件，不敷使用。 |
| Poly Haven 树木 | **禁用，未用** | 授权 CC0 但单棵数百万 tris（Fir Tree 01 约 700 万、Pine Tree 01 约 1700 万），与方案一致。 |

### 11.6 L1 移位与追加修正（ov-trees.py v3 `RELOC` 日志逐棵列出，共 37 棵）

- L1 南沿线 31 棵 y=-105 → y=-94（x 不变，方案原定），其中东端 2 棵在 y=-94 会压东主路
  （x 102..114）→ (100,-94)/(124,-94)；广场段 5 棵会压南门广场铺装（(0,-94) 正压南门中轴）
  → 移至广场两侧 y=-94（x -44/-36/-28/28/36）。
- L1 北沿线 2 棵照方案移至 (98,105)/(118,105)；相邻 (96,105)/(120,105) 去抖动钉网格点，
  否则与移位树仅 1.7m/0.95m。
- 楼间旧树 (0,12) 压步道 2 → (4,12)；(-80,45) 压新路 R-N1 → (-80,49)。
- 西沿线 3 棵旧树 (-120,-33/-25/-17) 落在操场 3m 缓冲内（跑道面外），系 v2 原位、方案未列，保持不动。
- 密植带新旧交错 3 对间距 1.56–1.81m（D1/D5 与旧沿线柱交错，方案设计间距 2.5m、抖动后收窄），
  在密植带内属冠层交错，保留并记录；新树两两之间最小间距 ≥2m。

## 12. 楼房网上模型第二轮搜寻（R2-T10b，2026-11-24 23:23–24:00 CST，只找模型、只下载、记来源）

> 接替中断的 R2-T10（上一任运行时重启中断，本地 `buildings/` 里只有 11-23 的旧文件，
> 无任何新下载，本轮等于从零开始）。背景：用户 2026-11-24 22:42 硬性要求——楼房
> 全部用网上现成模型或基于下载修改，不再手搓；9 栋楼体（ov-bldA/B/C、ov-lib、ov-gym、
> ov-lab、ov-tower、ov-canteen、ov-dorm）现为手捏量块+窗带，用户嫌光板假。
> 本轮只找模型、只下载、记来源；**未改任何 ov-bld\*.py/.blend/.glb，未碰 Godot
> scripts/scenes/data**。换装是下一波任务。
>
> 尺寸约定：下表尺寸均为 Blender 4.2.0 只读导入实测，**长×深×高**（Blender X×Y×Z，
> Z-up；对应 glTF X=长、Y=高、Z=深）。SPEC §4 目标尺寸（长×深×高，米）：
> bldA 40×15×19（5F）、bldB 32×14×19（5F）、bldC 22×13×14（4F）、lib 24×16×22（6F）、
> gym 36×16×18、lab 42×12×13、tower 14×14×32（8F）、canteen 32×13×15、dorm 20×12×16（5F）。
> 配色一律按 SPEC §3：墙面米白 `#F3E9D2` / 蓝灰 `#DFE9F2` / 浅橙 `#F6D9C0`、
> 艺体馆红墙 `#8E2F28`、屋顶深灰 `#424A52`、玻璃 `#9FC3D8`。

### 12.1 来源对比（8 家，5 家拿到文件）

| # | 来源 | 结果 | 授权 | 直链方式 |
|---|---|---|---|---|
| 1 | Kenney City Kit Commercial（kenney.nl） | **拿到**：整包 ZIP + 19 个主楼 GLB | CC0（包内 License.txt 全文） | 资产页 cookie + `GET /download-link/<hex>` 拿签名链接再下（见 12.6） |
| 2 | vinish.dev 彩色小镇（models.vinish.dev） | **拿到**：6 栋 GLB | CC BY 4.0（署名 vinish.dev） | `https://models.vinish.dev/colorful-town/<slug>.glb` 直接下，无登录 |
| 3 | Grab3D Buildings（grab3d.com） | **拿到**：11 个 GLB（Cozy 系列为主） | CC0 1.0 | `https://grab3d.com/dl/<slug>/<slug>.glb` 直接下，无登录 |
| 4 | tevy.dev（医院楼） | **拿到**：原文件 + 解压后的 plain 版 | CC0 | `https://tevy.dev/models/hospital-building/v2/lod0.glb` 直接下，无登录 |
| 5 | poly.pizza（Google Poly 档案镜像） | **拿到**：9 个 GLB（2 校舍 + 7 CC0 单体） | 按模型：校舍 CC-BY 3.0，其余 7 个 CC0 | 模型页 HTML 内嵌 `https://static.poly.pizza/<uuid>.glb` 直接下，无登录；API 搜索现须 key（401），改走网站搜索页 |
| 6 | Sketchfab CC0/可下载区 | **未下载（须登录）** | — | 搜索 API 可免 key 查到模型（如 `d34ac09a…` "school building"，CC-BY、可下载），但 `/v3/models/<uid>/download` 无 token 返回 401，无免登录直链 |
| 7 | BlendSwap 免费区 | **未下载（须登录）** | — | 搜索页 `curl` 返回 301 空页（跳登录），无直链；与上一轮结论一致 |
| 8 | CGTrader 免费区 | **未下载（页面被挡）** | — | 免费 school-building 页 `curl` 返回 202、0 字节；下载本来就须注册，与上一轮结论一致 |

另查：itch.io reodesuxz Low Poly School Pack（27 件，免署名）下载须走 itch 流程、无 curl
直链，且内容是课桌/书架/校车等小件而非楼体，未下（与 SOURCES.md §6 结论一致）；
Quaternius 官网整包下载走 Google Drive、此前已报配额耗尽，但其单体已通过 poly.pizza
拿到 CC0 版（见 12.2）；3DAssets.dev 只有小件、无楼体。

### 12.2 候选实测表（全部已下载；尺寸/面数均为 Blender 4.2.0 `--background` 只读导入实测）

**（A）vinish.dev（CC BY 4.0，署名 vinish.dev；全部单 mesh——窗/阳台/屋顶花园等均焊在一个 mesh 里、按材质分区，换装时只能整体缩放+整体改色，拆件须切 mesh）**

| 候选 / 文件 | 资产页 | 直链 | 实测尺寸 长×深×高（m） | 面数 / mesh | 结构实测 |
|---|---|---|---|---|---|
| 钟楼 `vinish/clock-tower.glb` | https://vinish.dev/free-3d-models/colorful-town | https://models.vinish.dev/colorful-town/clock-tower.glb | 13.2×13.2×32.7 | 36,620 / 1 | 红砖塔身+石材带+四面钟面+铜绿尖顶+风向标，广场花坛/长椅焊在同一 mesh 里 |
| 办公塔 `vinish/office-tower.glb` | 同上 | https://models.vinish.dev/colorful-town/office-tower.glb | 30.2×30.9×69.7 | 45,190 / 1 | 14 层蓝绿幕墙+白鳍片，2 层石灰岩裙楼带屋顶花园，旋转门雨棚；页标 70m/14 层与实测一致 |
| 阳台公寓 `vinish/balcony-apartments.glb` | 同上 | https://models.vinish.dev/colorful-town/balcony-apartments.glb | 24.0×17.9×18.0 | 44,446 / 1 | 5 层白灰泥公寓，每户阳台+彩色门面+花箱，平屋顶带光伏板；页标 5 层与实测一致 |
| 联排别墅 `vinish/pastel-townhouses.glb` | 同上 | https://models.vinish.dev/colorful-town/pastel-townhouses.glb | 20.9×15.7×13.4 | 51,248 / 1 | 4 栋 2 层粉彩联排，柱廊门廊+凸窗+女儿墙+烟囱，坡顶感来自屋顶造型 |
| 购物中心 `vinish/shopping-mall.glb` | 同上 | https://models.vinish.dev/colorful-town/shopping-mall.glb | 48.0×43.1×15.9 | 22,438 / 1 | 2 层商场，玻璃中庭入口+雨棚、店面石墩、天窗、屋顶风机；含广场铺装/花坛 |
| 超市 `vinish/supermarket.glb` | 同上 | https://models.vinish.dev/colorful-town/supermarket.glb | 36.0×38.1×9.6 | 13,354 / 1 | 单层大卖场，平屋顶+停车场划线焊在同一 mesh 里；层高感只有 1 层 |

**（B）Grab3D（CC0 1.0；全部多 mesh，窗多为独立 mesh 或独立材质，拆件友好；资产页标称尺寸/三角数与 Blender 实测逐项一致，见 12.6）**

| 候选 / 文件 | 资产页 | 直链 | 实测尺寸 长×深×高（m） | 面数 / mesh | 结构实测 |
|---|---|---|---|---|---|
| 办公楼 `grab3d/office-building-grab3d.glb` | https://grab3d.com/models/buildings/office-building/ | https://grab3d.com/dl/office-building/office-building.glb | 36.1×22.2×25.6 | 31,676 / 4 | `body` 29.4×18.7×25.6 + `facade` 32.3×15.4×24.5（玻璃幕墙窗带）+ `shell` 29.8×15.8×18.5（上部玻璃体，z 3.96–22.46）+ 地面基座；现代玻璃办公楼 |
| 公寓楼 `grab3d/apartment-building-grab3d.glb` | https://grab3d.com/models/buildings/apartment-building/ | https://grab3d.com/dl/apartment-building/apartment-building.glb | 15.6×13.8×18.3 | 33,542 / 4 | `body` + `details` + `roof_terrace`（屋顶露台）+ `shrubs`（灌木）；5 层左右砖楼，窗带真实 |
| 博物馆 `grab3d/museum-grab3d.glb` | https://grab3d.com/models/buildings/museum/ | https://grab3d.com/dl/museum/museum.glb | 25.4×24.8×15.0 | 25,838 / 3 | `body` + `details` + `temple_emblem`（三角楣神庙徽）；柱廊入口，石材立面 |
| 银行 `grab3d/bank-grab3d.glb` | https://grab3d.com/models/buildings/bank/ | https://grab3d.com/dl/bank/bank.glb | 16.9×17.0×11.2 | 25,956 / 3 | `body` + `coin_emblem`（硬币徽）+ `details`；低矮石材楼，只有 2–3 层感 |
| 影院 `grab3d/cinema-grab3d.glb` | https://grab3d.com/models/buildings/cinema/ | https://grab3d.com/dl/cinema/cinema.glb | 17.8×24.7×13.4 | 22,558 / 4 | `body` + `details` + `emblems` + `lights`（灯泡招牌）；珊瑚色立面+金色装饰 |
| 街区填充楼 `grab3d/city-block-filler-grab3d.glb` | https://grab3d.com/models/buildings/city-block-filler/ | https://grab3d.com/dl/city-block-filler/city-block-filler.glb | 10.0×14.6×15.7 | 20,642 / 3 | `body` + `details` + **`windows` 独立 mesh**；4–5 层小楼带底层商铺+遮阳篷 |
| 消防站 `grab3d/fire-station-grab3d.glb` | https://grab3d.com/models/buildings/fire-station/ | https://grab3d.com/dl/fire-station/fire-station.glb | 20.4×17.8×18.3 | 23,604 / 4 | `body` + `bay_doors`（车库大门）+ `details` + `sign`；珊瑚色立面 |
| 酒店 `grab3d/hotel-grab3d.glb` | https://grab3d.com/models/buildings/hotel/ | https://grab3d.com/dl/hotel/hotel.glb | 24.0×13.5×30.1 | 36,632 / 6 | `body` 24×12×29.5 + **`detail_windows` 独立 mesh** 23.9×12×26.1 + 细部/灯泡/绿植；约 8 层 |
| 邮局 `grab3d/post-office-grab3d.glb` | https://grab3d.com/models/buildings/post-office/ | https://grab3d.com/dl/post-office/post-office.glb | 12.0×13.3×9.8 | 17,152 / 6 | `body` + `details` + `planters` + `postboxes` + `shrubs` + `windows`；小楼，只有 2–3 层感 |
| 发电厂 `grab3d/power-plant-grab3d.glb` | https://grab3d.com/models/buildings/power-plant/ | https://grab3d.com/dl/power-plant/power-plant.glb | 38.1×16.4×32.0 | 20,930 / 4 | `body` 26.5×16.4×32.0（高窄塔身）+ `bolt_emblem` + `switchyard`（变电场 12×11×9.6）+ `windows` 27×12.3×21.4；工业风 |
| 食堂（室内房间，非楼体）`grab3d/cafeteria-grab3d.glb` | https://grab3d.com/models/buildings/cafeteria/ | https://grab3d.com/dl/cafeteria/cafeteria.glb | 4.0×4.0×3.0 | 40,804 / 4 | **室内取餐间**（取餐台+玻璃罩+饮水机），不是楼体；只作 canteen 室内参考，不参与楼体换装 |

**（C）tevy.dev（CC0；医院楼 6 层，含场地铺装/直升机坪，楼体与场地焊在 `building` 一个 mesh 里）**

| 候选 / 文件 | 资产页 | 直链 | 实测尺寸 长×深×高（m） | 面数 / mesh | 结构实测 |
|---|---|---|---|---|---|
| 医院楼 `tevy/hospital-building-tevy.glb`（原文件） | https://tevy.dev/models/hospital-building | https://tevy.dev/models/hospital-building/v2/lod0.glb | 与 plain 版一致（见下；原文件 Blender 4.2 打不开，见 12.6） | — / 5 | 页标：6 层、50×25m、高 25m、屋顶直升机坪；白预制带+成排亮窗+深色玻璃底层+蓝色楼梯核+救护车雨棚 |
| 医院楼 `tevy/hospital-building-tevy-plain.glb`（解压去贴图版，供 Blender 用） | 同上 | 同上（本地由原文件解压，见 12.6） | 54.0×38.5×32.3（含场地+风向标；`building` 单 mesh 54.0×38.5×28.0） | 54,066 / 5 | `building` + `entrances` 33×9.3×5.3（入口雨棚）+ `entrance_lights` + `helipad_lights` + `roof_plant` 50.5×22.8×32.3（含风向标杆）；实测比页标大是因含场地铺装与屋顶设备 |

**（D）poly.pizza（Google Poly 档案；校舍 CC-BY 3.0 须署名作者，其余 7 个 CC0；全部单 mesh）**

| 候选 / 文件 | 资产页 | 直链 | 实测尺寸 长×深×高 | 面数 / mesh | 结构实测 |
|---|---|---|---|---|---|
| 校舍（Google Poly）`polypizza/schoolhouse-googlepoly.glb` | https://poly.pizza/m/ftnL_OvlkCx | https://static.poly.pizza/60a7b5e3-e062-41eb-804b-b218edac3783.glb | 13.2×15.3×15.0 m | 1,576 / 1 | 2 层小学校舍，单材质 `blinn1SG`，坡顶+钟楼感；CC-BY 3.0（Poly by Google） |
| 校舍（jeremy）`polypizza/schoolhouse-jeremy.glb` | https://poly.pizza/m/5uBxCBp0os0 | https://static.poly.pizza/2cf6c213-5b5c-4ee7-9220-21e36300e2dd.glb | 6.9×6.8×10.1 m | 2,136 / 1 | 小校舍，6 色平面材质；太小，只能作体量参考；CC-BY 3.0（jeremy） |
| Quaternius 大楼 `polypizza/quaternius-big-building.glb` | https://poly.pizza/m/AVCS8jUd2l | https://static.poly.pizza/6c49f4dd-c032-4e50-b257-68bbe01bcf16.glb | 4.71×4.39×5.68 单位 | 7,004 / 1 | 6 色平面材质低多边形楼，窗为色块面；Quaternius 套件比例尺（娃娃屋尺寸，需整体放大）；CC0 |
| Quaternius 商务楼 `polypizza/quaternius-business-building.glb` | https://poly.pizza/m/GoF3zph6WI | https://static.poly.pizza/9cf00975-0f9f-414c-bb2d-84decf12f0e0.glb | 1.81×1.43×0.90 单位 | 8,556 / 1 | 扁平低层办公块，只有 0.9 单位高；CC0 |
| Quaternius 联排 `polypizza/quaternius-town-house.glb` | https://poly.pizza/m/dtVrmnnCZn | https://static.poly.pizza/8919c62b-5754-45f8-8a08-4f337de61bbc.glb | 3.05×4.40×5.68 单位 | 5,242 / 1 | 5 色平面材质联排；CC0 |
| Quaternius 大联排 `polypizza/quaternius-large-town-house.glb` | https://poly.pizza/m/Sl3ZTrWRwn | https://static.poly.pizza/cf011371-80fa-4e00-b96c-581dbb63215b.glb | 5.72×2.22×5.92 单位 | 15,072 / 1 | 同上套件，面数最高；CC0 |
| Quaternius 小楼 `polypizza/quaternius-small-building.glb` | https://poly.pizza/m/6q5cwgep0I | https://static.poly.pizza/5f01edd6-6ffb-41be-b53e-9379f9a06ad1.glb | 3.58×2.49×4.97 单位 | 5,160 / 1 | 同上套件；CC0 |
| KayKit 楼 `polypizza/kay-building.glb` | https://poly.pizza/m/otRsYa6pan | https://static.poly.pizza/1c40976f-9fd1-4779-ba85-8105d523f3d8.glb | 2.01×2.00×3.05 单位 | 1,885 / 1 | Kay Lousberg 城市套件单体，贴图绘制窗；CC0 |
| Kenney 塔 `polypizza/kenney-tower.glb` | https://poly.pizza/m/5lvG0WtuTU | https://static.poly.pizza/87e91b62-442b-4251-bcfc-b89300ad4500.glb | 33.2×33.4×37.2 m | 1,004 / 1 | Kenney 塔，7 材质，含大底座/广场；底座占幅过大；CC0 |

**（E）Kenney City Kit Commercial 2.1（CC0；包内 19 个主楼 GLB 已逐个实测；全部单 mesh + 单张 colormap 贴图，窗为贴图绘制、非几何）**

| 候选 / 文件 | 资产页 | 直链（签名链接，见 12.6） | 实测尺寸 长×深×高（单位） | 面数 / mesh |
|---|---|---|---|---|
| building-a … building-n（14 栋，`kenney/glb/building-{a..n}.glb`） | https://kenney.nl/assets/city-kit-commercial | 整包 ZIP（见 12.5） | a 0.88×0.94×1.29 / b 0.97×0.94×1.29 / c 0.88×1.09×0.89 / d 0.84×0.90×1.29 / e 1.64×1.01×0.89 / f 0.84×1.03×1.69 / g 0.97×0.92×1.69 / h 0.88×1.01×1.29 / i 1.24×1.30×1.68 / j 2.08×1.34×1.69 / k 2.08×0.94×1.47 / l 1.37×1.40×2.27 / m 1.24×1.24×3.15 / n 2.32×1.82×2.48 | 1,100–5,246 / 1 |
| building-skyscraper-a … -e（5 栋，`kenney/glb/building-skyscraper-{a..e}.glb`） | 同上 | 同上 | a 1.36×1.36×2.88 / b 1.36×1.36×4.48 / c 1.28×1.39×4.08 / d 1.28×1.39×5.47 / e 1.29×1.24×4.08 | 1,156–1,892 / 1 |

包内另有 low-detail 版 16 个 + 雨棚/遮阳/阳伞细部 6 个，未逐个核验、未单独入库，
仍在 `city-kit-commercial.zip` 里，需要时再解。

### 12.3 逐栋适配推荐表（目标尺寸为 SPEC §4 实测，绝不能改尺寸去套模型；缩放系数 = 目标÷模型，按 长/深/高）

| 楼栋（目标 长×深×高） | 推荐模型 | 缩放系数（长/深/高） | 改色 / 改结构 | 结论 |
|---|---|---|---|---|
| bldA 一号楼 40×15×19（5F） | Grab3D 办公楼 `office-building`（body 29.4×18.7×25.6；facade 32.3×15.4×24.5） | body ×1.36/×0.80/×0.74；facade ×1.24/×0.98/×0.78 | 玻璃幕墙染 SPEC 玻璃 `#9FC3D8`、墙面染米白 `#F3E9D2`、屋顶改深灰平顶+女儿墙 | **勉强换骨架**：长向拉 36%、高向压 26%，窗带会变宽变矮，需重排窗带；与 lib 共用同一模型、不同缩放与配色 |
| bldB 二号楼 32×14×19（5F） | Grab3D 办公楼 `office-building`（facade 优先） | facade ×0.99/×0.91/×0.78；body ×1.09/×0.75/×0.74 | 同 bldA，另换一面配色（蓝灰 `#DFE9F2`）与 A 区分 | **勉强换骨架**：长/深接近，高向压 22–26%，层高感会矮，需重排窗带 |
| bldC 三号楼 22×13×14（4F） | **沿用 11-23 已入库的 Grab3D 学校楼**（22.9×13.9×16.7，见 §5.2） | ×0.96/×0.94/×0.84 | 黄墙改浅橙 `#F6D9C0`、珊瑚红坡顶改深灰平屋顶+女儿墙、拆屋脊钟楼 | **本轮无新模型胜过旧件**：新候选 pastel-townhouses（×1.05/×0.83/×1.05）尺寸接近但只有 2 层+坡顶烟囱，改 4 层教学楼工作量更大；bldC 仍用旧件 |
| lib 图书馆 24×16×22（6F） | Grab3D 办公楼 `office-building`（body 优先） | body ×0.82/×0.85/×0.86；facade ×0.74/×1.04/×0.90 | 玻璃幕墙染 SPEC 玻璃+蓝灰墙面、入口加 Grab3D 博物馆柱廊/`temple_emblem`部件、屋顶改深灰平顶 | **可直接换骨架**：全轮里最接近等比的一组（0.82–0.86），窗比例基本不坏；备选 tevy 医院楼体（6 层）但楼体与场地焊死、需先切场地 |
| gym 体育馆 36×16×18 | 无整栋可用；量体参考 vinish 超市（36×38.1×9.6，宽恰好 36m、平屋顶）+ Grab3D 影院立面部件 | 超市 ×1.00/×0.42/×1.88（不可行，作废） | 超市只取 36m 宽+平屋顶+屋顶设备的量体概念，深向与高度重建；入口雨棚参考 tevy 医院 `entrances` | **只能参考局部**：所有候选不是深向压一半、就是高向拉一倍，没有大跨度低矮体育馆；量体重建、偷屋顶/入口部件 |
| lab 实验楼 42×12×13 | 无整栋可用；量体参考 Grab3D 发电厂 `windows` mesh（27×12.3×21.4）+ 办公楼 `shell`（29.8×15.8×18.5） | —（均不贴合） | 窗带 mesh 可拆出来改长度拼成长条窗带；屋顶设备参考发电厂 `switchyard` | **只能参考局部**：42m 长条低楼网上没有，量体重建、只偷窗带与屋顶设备 |
| tower 创造力中心 14×14×32（8F） | vinish 钟楼 `clock-tower` | ×1.06/×1.06/×0.98 | 去四面钟面+铜绿尖顶+风向标与广场花坛，加层间带读出 8 层；墙面染米白/浅橙、屋顶深灰 | **可直接换**：全轮唯一近等比（误差 ≤6%），窗比例不坏；备选 Kenney building-m（1.24×1.24×3.15 单位，等比 ×11.29 得 14×14×35.6 再高向 ×0.90），但窗是贴图绘制，弱一档 |
| canteen 食堂 32×13×15 | 无整栋可用；量体参考 Grab3D 博物馆（25.4×24.8×15.0，高恰好）+ vinish 超市（平屋顶大卖场概念） | 博物馆 ×1.26/×0.52/×1.00（深向压一半，作废） | 博物馆只取高度与柱廊入口概念；食堂室内参考 Grab3D 食堂房间 `cafeteria`（4×4×3m 取餐台） | **只能参考局部**：没有 32m 长、13m 深、15m 高的食堂楼，量体重建 |
| dorm 宿舍 20×12×16（5F） | Grab3D 公寓楼 `apartment-building` | ×1.29/×0.87/×0.87 | 墙面染浅橙 `#F6D9C0`、去屋顶露台花坛与 `shrubs` 灌木、屋顶改深灰平顶 | **可直接换**：缩放最均匀的住宅楼，窗带真实；备选 city-block-filler 两栋并排（每栋 10×14.6×15.7，×1.0/×0.82/×1.02 并排拼成 20m 宽，窗比例完全不坏，但接缝要处理） |

### 12.4 换装工作量评估（给下一波换装任务）

- **能直接换（3 栋 + 1 栋沿用旧件）**：tower（钟楼去钟面/尖顶+加层间带）、dorm（公寓楼改色+去露台花坛）、
  lib（办公楼 body 等比缩+改色+加博物馆柱廊入口）；bldC 沿用 11-23 旧件学校楼（已评估过，见 §5.2）。
- **勉强换骨架、窗带须重排（2 栋）**：bldA、bldB 共用 Grab3D 办公楼（不同缩放与配色区分），
  高向压 22–26% 会把层高感压矮，窗带必须按 SPEC 层高重排，不能只缩放了事。
- **只能参考局部、量体重建（3 栋）**：gym、lab、canteen——网上没有对应体量的整栋；
  可偷的部件：gym 取超市 36m 宽量体概念+医院入口雨棚；lab 取发电厂 `windows` 窗带 mesh 改长
  + `switchyard` 屋顶设备；canteen 取博物馆柱廊入口概念 + 食堂房间取餐台。
- **共性工作**：所有 vinish / poly.pizza 单 mesh 模型只能整体缩放改色、拆件须切 mesh；
  Grab3D 多 mesh（`windows`/`facade`/`details` 独立）拆件最友好；Kenney/Quaternius/Kay
  均为贴图绘窗或色块窗，窗带真实度弱一档，只作备选量体。
- **面数**：单栋换装后 17k–54k 面（医院楼 54k 最高、含场地；钟楼 36.6k、办公楼 31.7k、
  公寓楼 33.5k），9 栋全换后总览面数增加约 25–30 万面，在可接受范围（总览现约 13,036 对象）。

### 12.5 文件清单（本轮新增 48 个文件，共 62,640,082 字节，约 59.7 MiB；未覆盖 11-23 旧文件）

| 目录 | 文件 | 字节 |
|---|---|---|
| `buildings/kenney/` | `city-kit-commercial.zip`（整包，含 License.txt CC0） | 4,096,974 |
| `buildings/kenney/glb/` | `building-{a..n}.glb` 14 个 + `building-skyscraper-{a..e}.glb` 5 个 | 3,739,924 |
| `buildings/vinish/` | `clock-tower` / `office-tower` / `balcony-apartments` / `pastel-townhouses` / `shopping-mall` / `supermarket` 各 1 个 `.glb` | 22,229,104 |
| `buildings/grab3d/` | `office-building` / `apartment-building` / `museum` / `bank` / `cinema` / `city-block-filler` / `fire-station` / `hotel` / `post-office` / `power-plant` / `cafeteria` 各 1 个 `-grab3d.glb` | 22,368,448 |
| `buildings/tevy/` | `hospital-building-tevy.glb`（原文件，meshopt+KTX2）+ `hospital-building-tevy-plain.glb`（解压去贴图版） | 6,663,288 |
| `buildings/polypizza/` | `schoolhouse-googlepoly` / `schoolhouse-jeremy` / `quaternius-big-building` / `quaternius-business-building` / `quaternius-town-house` / `quaternius-large-town-house` / `quaternius-small-building` / `kay-building` / `kenney-tower` 各 1 个 `.glb` | 3,799,600 |

授权汇总：CC0——Kenney、Grab3D、tevy、poly.pizza 内 7 个（Quaternius 5 个、Kay 1 个、
Kenney 塔 1 个）；CC BY 4.0——vinish.dev 6 栋（署名 vinish.dev）；CC-BY 3.0——poly.pizza
2 个校舍（署名 Poly by Google / jeremy）。无 CC-BY-NC/ND、无付费、无登录后下载。

### 12.6 核验方法与坑（诚实记录）

- **核验**：Blender 4.2.0（`~/workspace/tools/blender/blender-4.2.0-linux-x64/blender`）
  `--background` 只读导入全部 47 个 GLB（19 Kenney + 6 vinish + 11 Grab3D + 2 tevy +
  9 poly.pizza），其中 46 个成功、1 个失败（tevy 医院楼原文件，meshopt 压缩打不开，
  见下），另逐 mesh 包围盒复核 5 个重点文件
  （发电厂/医院 plain/办公楼/购物中心/酒店）；Grab3D 11 个资产页标称尺寸与三角数与
  Blender 实测**逐项一致**（如办公楼 36.10×22.20×25.61m / 31,676 三角、公寓楼
  15.56×13.83×18.30m / 33,542 三角）；vinish 页标（办公塔 70m/14 层、钟楼 33m、
  商场 48m 宽、公寓 5 层）与实测一致；tevy 医院页标 50×25m/25m/6 层是楼体本身，
  实测 54×38.5×32.3 含场地铺装与屋顶风向标杆。
- **Kenney 下载法**：资产页 Download 按钮是 JS，先 `curl -c` 取 cookie 再
  `GET https://kenney.nl/download-link/<hex(assets/city-kit-commercial)>`（须带 cookie +
  Referer，否则 `{"error":"forbidden"}`），返回签名 URL 再下 ZIP；签名有时效，
  本轮链接 `expires=1795534291`。包内 License.txt 为 CC0 全文。
- **poly.pizza 下载法**：`api.poly.pizza/v1.1/search` 现须 API key（401
  "You need an API key to do that dingus"），改走网站搜索页
  `https://poly.pizza/search/<词>`（200，含 `/m/<id>` 链接），模型页 HTML 内嵌
  `https://static.poly.pizza/<uuid>.glb` 直链；本轮扫了 school / office building /
  library / apartment / tower 5 个搜索词、117 个不重复模型页，挑出 9 个入库。
  许可证以模型页标注为准（CC0 或 CC-BY 3.0）。
- **tevy 医院楼解压（与上一轮教室同坑）**：原文件用 EXT_meshopt_compression +
  KTX2 贴图，Blender 4.2 打不开（`Extension EXT_meshopt_compression is not available`）。
  解法：`npm i @gltf-transform/cli@4` 后 `gltf-transform copy` 解 meshopt，
  再用 gltf-transform 剥全部贴图 + `dequantize()`，最后用 Python 把 GLB JSON 块里残留的
  `KHR_texture_basisu` 从 extensionsUsed/Required 删掉（JSON 块填充必须用空格 0x20，
  用 NUL 填充 Blender 会报 `Bad glTF: json error: Extra data`）；plain 版 3,748,024 B，
  Blender 实测 54.0×38.5×32.34、5 mesh、54,066 面。原文件保留，plain 版只供 Blender
  核验/换装用（贴图已剥，材质只剩 baseColor 数值）。
- **Grab3D 的 .blend 别下**：上一轮已证实其 `.blend` 下载全是占位文件（见 §5.3），
  本轮只下了 `.glb`。
- **Kenney/Quaternius/Kay 的尺寸是套件单位、不是米**：文件内 1–5 个单位是娃娃屋比例尺，
  换装时须整体放大（Kenney building-m 等比 ×11.29 才到 14m）；窗为贴图绘制或色块面，
  非几何窗带，近景真实度弱于 Grab3D/vinish。
- **食堂 Grab3D `cafeteria` 不是楼**：4×4×3m 室内取餐间，误当楼体会错得离谱，
  已在 12.2 表内标明，只作 canteen 室内参考。

