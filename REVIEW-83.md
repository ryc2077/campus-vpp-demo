# blender-previews run #83 单件渲染图逐张目视复核（R2-T5）

- **复核时间**：2026-11-24 22:39–22:44 CST
- **复核对象**：`blender-previews` run **#83**（run id `45306226357`，工作流 `Blender previews (max quality)`，HEAD `0317452b614d50d1ccefbdf9079a611f3d75869e`，分支 main，创建时间 2026-11-24T01:36:00Z，结论 **success**）
- **复核方式**：6 个 artifacts 全部下载、解包，55 张图逐张目视（先按 6 张一组拼图通读，再对存疑的 5 张读全尺寸原图：ov-lawn、ov-trees、pv-mount、ov-windows-roofs（中栋放大）、ov-road-walk）；另做像素级自动筛查（品红/纯黑/纯白占比、逐像素重图比对）。
- **本地复核目录**：`~/workspace/review-rework-r2/blender-83/`（按组分子目录：`charge/`、`classroom/`、`dist/`、`overview/`、`pv/`、`storage/`；55 张 PNG 本地保留，**不推仓**）
- **通过标准**：主体完整、无黑帧、无品红（缺贴图色）、无全白/全黑、材质纹理可见、无穿模大错。

## 结论总览

| 指标 | 数值 |
|---|---|
| Artifacts | 6 个（blender-previews-overview / dist / classroom / charge / pv / storage），均未过期 |
| 图片总数 | **55 张，齐**（overview 20、dist 13、classroom 6、charge 4、pv 7、storage 5） |
| 规格 | 全部 1280×720 RGBA，文件 477KB–1.28MB |
| 自动筛查 | 品红像素 55 张均为 0.00%；纯黑 ≤0.11%、纯白 ≤0.17%（均为零星像素，无黑帧/白帧）；无缺贴图色 |
| 独立画面 | **53 张**（2 对逐像素重图，见下） |
| **通过** | **52 张** |
| **不通过** | **3 张**：`di-signs`、`pv-inverter`、`pv-mount` |

## 不通过清单（3 张）

1. **`dist/di-signs.png`（dist 组）——重图：与 `di-signs-Warn.png` 逐像素相同。**
   图中只有一块红底黄框“高压危险”警示牌，未呈现任何独立的标识集合。像素比对 maxdiff=0、meandiff=0.00（文件 md5 不同，仅编码/元数据差异：`b0d2ec24…` vs `86213d76…`）。55 张里没有一张真正展示标识合集，`di-signs` 这个名字的渲染实际缺失。
2. **`pv/pv-inverter.png`（pv 组）——重图：与 `pv-inverter-LAB.png` 逐像素相同。**
   图中就是 LAB 那台逆变器（同一角度、同一桥架走向），无独立的通用逆变器渲染。像素比对 maxdiff=0、meandiff=0.00（md5：`6fa94ffe…` vs `5a0b9fb1…`）。
3. **`pv/pv-mount.png`（pv 组）——取景截断 + 对比度过低。**
   ① 左下角第二组支架被画面边缘截断，只剩一角入框，主体未完整入框；② 银灰支架与浅灰背景对比度极低，全图几乎融为一体，支架结构与金属材质难以辨认（同组 `pv-panels`/`pv-roof` 用深灰背景则清晰）。建议重渲时换深色背景、收紧取景把全部支架组收入框内。

> 重图根因推测（未改代码、仅供后续任务核查）：渲染脚本里 `di-signs` 与 `di-signs-Warn`、`pv-inverter` 与 `pv-inverter-LAB` 很可能指向了同一对象/同一相机位，需核对 `blender-previews` 的件名—对象映射表，而非重跑一遍了事。

## 逐张表

### charge 组（4/4 通过）

| 件 ID | 结论 | 目视记录 |
|---|---|---|
| ch-canopy | ✅ 通过 | 雨棚完整，立柱+顶板齐全，地面阴影正常 |
| ch-cars | ✅ 通过 | 蓝/红/白三台车完整，车窗深色、无穿模 |
| ch-marking | ✅ 通过 | 4 个车位白线+黄线+绿色地标完整 |
| ch-piles | ✅ 通过 | 充电桩完整，屏幕、充电枪、指示灯可见 |

### classroom 组（6/6 通过）

| 件 ID | 结论 | 目视记录 |
|---|---|---|
| cl-ac | ✅ 通过 | 立式空调完整 |
| cl-board | ✅ 通过 | 黑板+讲台+两侧白板完整 |
| cl-desks | ✅ 通过 | 课桌椅阵列完整，无缺件 |
| cl-floor-walls | ✅ 通过 | 教室壳体完整，窗洞、门洞齐全 |
| cl-lights | ✅ 通过 | 6 盏灯具完整（细长条形，画面中偏小但齐全） |
| cl-windows | ✅ 通过 | 9 扇窗+1 扇门完整，玻璃有反光层次 |

### dist 组（12/13 通过）

| 件 ID | 结论 | 目视记录 |
|---|---|---|
| di-busbar | ✅ 通过 | 母排框架+铜排+三色电缆完整 |
| di-cabinets | ✅ 通过 | 6 台配电柜完整 |
| di-signs-E | ✅ 通过 | “禁止合闸 有人工作”红框白底，文字清晰 |
| di-signs-Num1 | ✅ 通过 | 蓝底白字“1”清晰 |
| di-signs-Num2 | ✅ 通过 | 蓝底白字“2”清晰 |
| di-signs-Num3 | ✅ 通过 | 蓝底白字“3”清晰 |
| di-signs-Num4 | ✅ 通过 | 蓝底白字“4”清晰 |
| di-signs-Num5 | ✅ 通过 | 蓝底白字“5”清晰 |
| di-signs-Num6 | ✅ 通过 | 蓝底白字“6”清晰 |
| di-signs-Warn | ✅ 通过 | “高压危险”红底黄框，文字清晰（本体重图问题见 `di-signs` 一行） |
| **di-signs** | ❌ **不通过** | **与 `di-signs-Warn.png` 逐像素相同，图中只有“高压危险”一块牌，无独立的标识集合** |
| di-transformer | ✅ 通过 | 4 台变压器，散热片+套管完整 |
| di-walls | ✅ 通过 | 配电房壳体完整，墙面斑驳纹理可见 |

### overview 组（20/20 通过，3 张有弱项备注）

| 件 ID | 结论 | 目视记录 |
|---|---|---|
| ov-bldA | ✅ 通过 | 五层教学楼 A 完整，深色屋顶、窗带、入口雨棚齐全 |
| ov-bldB | ✅ 通过 | 五层教学楼 B 完整，深色瓦屋顶纹理可见 |
| ov-bldC | ✅ 通过 | 五层教学楼 C 完整，屋顶设备盒齐全 |
| ov-canteen | ✅ 通过 | 食堂三层，红柱+灰窗带完整 |
| ov-dorm | ✅ 通过 | 两栋宿舍楼+中间绿地完整 |
| ov-field | ✅ 通过 | 足球场条纹草皮、球门、边线完整 |
| ov-flag-lamp | ✅ 通过 | 3 根旗杆红旗+2 盏路灯完整（画面中偏小） |
| ov-gate | ✅ 通过 | 校门、围墙、门卫室、伸缩门完整 |
| ov-gym | ✅ 通过 | 体育馆红墙+玻璃窗带完整 |
| ov-lab | ✅ 通过 | 实验楼四层，红柱+窗带完整 |
| ov-lawn | ✅ 通过（弱项） | 绿篱环形+矩形布局与 3 块草皮齐全；但全尺寸下绿篱呈虚线状、草叶单体不可辨，主体在画面中偏小、背景空旷。建议重渲拉近镜头 |
| ov-lib | ✅ 通过 | 图书馆塔楼完整，红白立面+窗带齐全 |
| ov-parking | ✅ 通过 | 停车场+3 台车+标线+导向箭头完整 |
| ov-road-main | ✅ 通过 | 环路俯视完整 |
| ov-road-walk | ✅ 通过（弱项） | T 形步道+方形广场（放射状铺装纹）完整，浅色线条在深色背景上清晰；但步道细长、画面留白大 |
| ov-tower | ✅ 通过 | 高层塔楼完整，红/粉竖条立面齐全 |
| ov-track | ✅ 通过 | 红色跑道椭圆+分道线完整 |
| ov-transformer | ✅ 通过 | 户外变压器+散热片+绝缘子+围栏完整 |
| ov-trees | ✅ 通过（弱项） | 约 150 棵树沿矩形周界+内侧成簇分布，每棵树形、树干可辨；但全景尺度下单棵仅为小点 |
| ov-windows-roofs | ✅ 通过（说明） | A/B/C 三栋横向蓝色窗带（每层通长）+深色屋顶+屋顶设备盒齐全；中、右两栋窗带之间可透视见对侧，是因单件渲染隐藏了墙体件 ov-bldA/B/C（与 cl-windows 悬空窗同理），非本件缺失。遗留：faces 表 hx/hy 对调问题（BLENDER_MODELS.md §9 遗留①，已派修复）本图无法核验窗带长短，不计入本次不通过 |

### pv 组（5/7 通过）

| 件 ID | 结论 | 目视记录 |
|---|---|---|
| pv-inverter-A1 | ✅ 通过 | 逆变器+电缆桥架完整 |
| pv-inverter-A2 | ✅ 通过 | 同件另一角度，完整（与 A1 像素比对 meandiff=7.375，确为不同角度） |
| pv-inverter-LAB | ✅ 通过 | LAB 逆变器完整（本体重图问题见 `pv-inverter` 一行） |
| **pv-inverter** | ❌ **不通过** | **与 `pv-inverter-LAB.png` 逐像素相同，图中就是 LAB 那台逆变器，无独立的通用逆变器渲染** |
| **pv-mount** | ❌ **不通过** | **左下角第二组支架被画面边缘截断只剩一角；银灰支架与浅灰背景对比度极低，全图几乎融为一体** |
| pv-panels | ✅ 通过 | 3 组光伏板，蓝色电池片纹理清晰 |
| pv-roof | ✅ 通过 | 3 块深色屋顶板+白边完整 |

### storage 组（5/5 通过，1 张有备注）

| 件 ID | 结论 | 目视记录 |
|---|---|---|
| st-base | ✅ 通过 | 混凝土基座+黄线框+锚栓完整 |
| st-cabinet | ✅ 通过 | 4 台深绿储能柜，百叶窗+锈迹纹理可见 |
| st-cables | ✅ 通过 | 电缆桥架+小柜+三色电缆完整 |
| st-doors | ✅ 通过 | 4 扇柜门+顶部风扇口完整 |
| st-fence | ✅ 通过（备注） | 围栏+4 台柜+黄色警示牌完整；右侧有一根孤立立柱与围栏主体脱开一小段，疑似门柱，待核对 |

## 方法与核查记录

- Artifacts 清单（API 实测）：`blender-previews-overview` 18,408,895 B、`blender-previews-dist` 12,236,572 B、`blender-previews-classroom` 4,028,764 B、`blender-previews-charge` 3,956,060 B、`blender-previews-pv` 4,330,780 B、`blender-previews-storage` 3,685,775 B；6 个均未过期。
- 解包后清点：55 个 PNG，无其他文件；按组：overview 20、dist 13、classroom 6、charge 4、pv 7、storage 5。
- 自动筛查（逐像素统计）：品红（R>180,G<90,B>180）55 张均为 0.00%；纯黑（RGB<8）最高 0.11%（cl-floor-walls）、纯白（RGB>247）最高 0.17%（ov-parking），均为零星像素，无黑帧/白帧；其余 5 对疑似近似图逐像素比对：A1/A2、panels/roof、bldA/bldB 均为不同画面，仅上述 2 对 maxdiff=0。
- 目视覆盖：55/55 张均已看图（10 张 6 图拼图通读 + 5 张全尺寸复看），非仅文件名/尺寸核查。
- 本次只复核、不建模，未改任何模型/Godot 文件；55 张图只留本地，不推仓。

## 后续建议（供下一任务，不在本任务内执行）

1. 核查 `di-signs` 与 `pv-inverter` 的渲染映射（件名—对象/相机），修映射后在新 run 里重出这两张；`di-signs` 若本意是标识合集，应改拍全部标识同框。
2. `pv-mount` 重渲：换深色背景、收紧取景，把全部支架组收入框内。
3. 弱项重渲（非强制）：`ov-lawn`、`ov-road-walk`、`ov-trees` 拉近镜头；`st-fence` 核对右侧孤立立柱是否为门柱。
