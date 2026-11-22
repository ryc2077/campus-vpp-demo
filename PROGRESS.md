# 进度日志（Godot 重写 Demo · 5 小时任务，2026-11-22 17:02–22:02）

## 17:02–17:15 任务开始：读旧 Demo + 搭骨架
- 读完 `../demo/demo.html` 应用逻辑（3300–4527 行 + 仿真引擎 517–840 行 + 模型一 900–1010 行）：
  轨道相机、两段飞入、SCENE_LIM 限位盒、标签防重叠、天气五档、96 点仿真引擎、教室模型一。
- 权威数字核对：`1031.docx` 含 D-09、2868；`1.docx` 含 1344000、2868、D-09；与任务给定的口径一致。
- Godot 4.4 stable 已装到 `~/workspace/tools/godot/`，`godot --version` = `4.4.stable.official.4c311cbee`。
  导出模板下载中（`export_templates.tpz`）。
- 工程骨架完成：`project.godot`、6 个 `data/*.json`（权威数字全部进 JSON）、
  11 个 `scripts/*.gd`、6 个 `scenes/*.tscn`、`export_presets.cfg`、`README.md`、本日志。
- 待做：`--headless --import` 验证 → 修脚本报错 → Web 导出 → 无头 Chrome 逐场景截图验收 →
  修已知问题（标签遮挡/窄屏/池塘/穿模/返航）→ 天气与细节打磨。

## 17:10–17:25 去 AI 味（追加要求，优先级最高）
- 已读品味技能：`emil-design-eng/SKILL.md`、`review-animations/SKILL.md` + `STANDARDS.md`、
  `animate/SKILL.md`、`choreograph/SKILL.md`、`apple-design/SKILL.md`。
- 文案/配色审计（grep 实测）：全工程无“赋能/引领未来/让节能与舒适同行”类空话，
  无紫蓝渐变大色块（无任何 gradient）；面板为白色 0.93 扁平 + 6px 淡阴影，配色取航拍图。
- 自审表（review-animations 要求格式）：

| Before | After | Why |
| --- | --- | --- |
| 飞行缓动 `smootherstep`（ease-in-out，起步慢） | 强 ease-out `1-(1-u)^3` ≈ cubic-bezier(0.23,1,0.32,1)，`TRANS_CUBIC + EASE_OUT` | 进入一律 ease-out；ease-in 会拖住用户最关注的起步瞬间，感觉迟钝 |
| 场景面板 / A-B-C 面板瞬现，无反馈 | 180ms 进入：`scale 0.95 + opacity 0 → 1`，origin 在右缘触发点；退出直接隐藏（比进入更快，不对称） | 偶尔出现的面板给一点动效防“瞬变像坏掉”；从触发点生长，不从中心放大；UI 动效 <300ms |
| 按钮无按压反馈 | 按下 `scale 0.97`（100ms）、松开回弹 160ms，强 ease-out；只动 transform，不动 layout | 按压必须立刻有反馈，界面才像“听见了”；中途再按杀掉旧 tween 从当前值重定向 |
| 飞行被打断后从头重播（旧 Demo 隐患） | `fly_to` 每次从当前 az/el/dist/target 起飞；中途点别的场景直接平滑改向；拖动即取消 | 可中断是第一原则：飞行/过渡从当前位置改向，不从头重播 |
| 减弱动效偏好未处理 | Web 端读 `prefers-reduced-motion`，`?reduced=1` 同效：飞行改直接落位，面板只做 200ms 透明度变化 | 无障碍项：减弱动效不是零动效，保留帮助理解的透明度变化 |
| 无慢速检查手段 | `?slowmo=N`（飞行 ×N）、`?freeze=0.5`（冻结飞行中段）供逐帧检查 | 慢速/逐帧才能看清缓动、弧线、origin 是否正确 |

- 编排（choreograph）：

| Element | Role | Starts | Duration | Motion | Relationship |
| --- | --- | --- | --- | --- | --- |
| 镜头飞行 | Lead | 0ms | 1000ms（内景 500+500） | ease-out 弧线飞入 | — |
| 场景面板 | Support | 与飞行同时 | 180ms | scale 0.95 + opacity，右缘 origin | 与飞行重叠，不等飞行结束 |
| 面板内数据行/图表 | Static | — | — | 无动效，随面板一起出现 | 一个容器一次进入，不 stagger 子项 |
| 场景栏/天气按钮 | Feedback | 按下即时 | 100ms + 160ms 回弹 | scale 0.97 | 按压反馈 |
| 树摆/云漂/雨幕 | Decoration | 持续 | 环境 | 微幅循环 | 天气驱动，非 UI 动效 |

- 刻意不动的东西：场景栏 6 个按钮（高频切换，不做进入动画）；面板内数据行与图表
  （一个容器一次进入，面板自己动、内容已经在里面）；时间滑杆与播放头（连续操作，
  1:1 跟手）；顶栏（常驻 chrome，不动）。
- 待验证：慢速/冻结帧截图（`screenshots/`，见下节验收）。

## 17:25–17:35 液态玻璃（martin65536/liquid-glass-webgl，追加要求 1）
- 已读技能 `~/workspace/custom-skills/liquid-glass/SKILL.md`；源码 `~/workspace/liquid-glass-webgl/`：
  `renderer/spring.ts`（全文：闭式解弹簧，SPRING_K=300、阻尼比 0.5 欠阻尼用于按压/缩放；
  临界阻尼 springStepCritical，TOGGLE_VALUE_K=1000、ωn≈31.623 用于 toggle 值/按压；
  沉降阈值 SPRING_THRESHOLD=0.003）、`shaders/separable-blur.ts`（全文：可分离两遍高斯模糊，
  Skia convertRadiusToSigma σ=radius*0.57735+0.5，N=2·ceil(3σ)+1 上限 33；预乘 alpha 保护；
  highlight 模糊只模糊 alpha）、`shaders/sdf.ts`（全文：sdRoundedRect、sdContinuousRoundedRect
  （与圆弧差 <0.5% 半径，亚像素）、gradSdRoundedRect、erfApprox、coverUv；G2 连续曲率靠预计算
  SDF 纹理，analytic 近似已足够）、`shaders/element.ts`（前 130 行：流程为 SDF 裁剪→背景模糊→
  饱和度 1.5→透镜折射（7 通道色散，只在边缘）→tint/surfaceColor→高光→边缘抗锯齿；内阴影是
  Canvas2D 后处理；外阴影是单独扩展 quad）、`renderer/continuous-curve.ts`（G2 圆角 = 3 段三次贝塞尔）。
  注意：源码里没有名为 `capsule-tessellator.ts` 的文件（find 只找到 `capsule-sdf-debug-overlay.tsx`
  与 `renderer/continuous-curve.ts`）。
- 落地到代码：`shaders/liquid_glass.gdshader`（canvas-item shader：SCREEN_TEXTURE 9-tap 十字高斯近似——
  中心 0.32、±r/2 各 0.13、±r 各 0.04，低质量 5-tap；SDF 圆角矩形 + 1px smoothstep 抗锯齿；边缘折射往中心
  2.5px、仅 rim 带内 R/B 色差 1.2px；饱和度只取 1.15（源码 1.5 太强）；白色提亮 tint_alpha 0.42；
  细亮边左上 0.28 + 内阴影右下 0.10）、`scripts/glass_surface.gd`（class_name GlassSurface，
  extends ColorRect；**作为内容节点的 sibling，不做父容器**，避免 shader 被子节点继承糊到文字上；
  `?glass=0` 时隐藏自己并显示同级 fallback 实色 Panel；窄屏 <760px 自动降质 5-tap + 4px）、
  `scripts/spring.gd`（class_name PressSpringSet：临界阻尼弹簧 step_critical 闭式解，ω=31.623，
  沉降阈值 0.003；attach/tick 驱动按钮按压 0.97，替代旧版 tween 按压）。
- 应用对象（已定案，克制）：**玻璃只 2 处**——场景栏（底部，`UI/SceneBar/BarGlass`）与天气切换胶囊
  （右上，`UI/WxPill/WxGlass`，从顶栏拆出独立浮层）；场景栏按钮本身是扁平透明按钮（hover 白 0.25、
  激活态实色深绿 #0f766e 胶囊 + 白字，**不用第二层玻璃**，避免玻璃叠玻璃）；文字为主的场景面板/A-B-C 面板
  保持实色白底（可读优先）；图表卡片留在实色面板内、不做玻璃（取舍理由：图表文字需稳定底色保 4.5:1，
  模糊 3D 背景会破对比度）。
- Shader 两个坑已修：① Godot shader 不允许 fragment 里 `return`（报错 "Using 'return' in the
  'fragment' processor function is incorrect"），已删 early return；② Godot 4.4 移除了 SCREEN_TEXTURE
  内建量，须显式声明 `uniform sampler2D SCREEN_TEXTURE: hint_screen_texture, filter_linear_mipmap;`。
- 截屏验证（`screenshots/00-overview.png`，17:35）：玻璃已生效——天气胶囊透出模糊的天空蓝、
  场景栏透出模糊的绿草地与白色云团；控制台 shader 报错清零。
- 待验证：玻璃两种背景（繁忙楼/树 vs 纯天空）对比截图；窄屏降质截图。

## 17:25–17:35 taste-skill（Leonxlnx/taste-skill v2.5.1，追加要求 2）
- 技能在 `~/workspace/custom-skills/design-taste-frontend/`（SKILL.md 已读全文 + references/ +
  scripts/gate.mjs），源码 `~/workspace/taste-skill/`。核心家规拿来用在 Demo UI 上：
  文案说人话、不写 AI 腔；一屏一个重点；左右边对齐；真实数据/真实图表、不堆装饰；hover 微动克制
  （卡片抬 2px、图放大 1.02–1.03、按钮按压），不要倾斜/轮播/定时切换；shader 和大场面只留给
  技术主题的亮点时刻，不要处处都是。跑它的 gate/check 思路自查一遍（真实浏览器截屏核对）。
- 注意：该技能原是静态网站技能（Node 22+、Chrome、gate.mjs、deal/check 流程）；用到 Godot Demo
  上时只取家规与自查思路，不照搬其建站流程。
- 实际改动：场景面板删掉所有“用电情况”长段介绍文字（只留图表与数据行）；顶栏/场景栏/天气胶囊
  左右边对齐（顶栏 12px 等边距）；hover 只保留按钮按压 scale 0.97 与场景栏按钮 hover 白 0.25，
  无倾斜、无轮播、无定时切换。

## 17:25–17:35 UI/UX Pro Max（nextlevelbuilder/ui-ux-pro-max-skill v2.15.0，追加要求 3，必装）
- 技能：`~/workspace/custom-skills/ui-ux-pro-max/SKILL.md`（已读全文），源码
  `~/workspace/ui-ux-pro-max-skill/`。**注意：文字版安装，没跑 CLI、没跑 search.py、没跑任何脚本，
  只读规则文本和 CSV**；本任务也一样，只读文本和 CSV，不执行它的任何脚本。
- 已读：SKILL.md 优先级表（1 无障碍、2 触摸交互、3 性能、4 风格、5 布局响应、6 字体颜色、7 动画、
  8 表单反馈、9 导航、10 图表）；`references/quick-reference.md`（275 行，全 10 类规则）；
  `references/pro-rules.md`（117 行，pre-delivery checklist）；CSV 抽查：styles.csv（Minimalism &
  Swiss 行契合 Operate 仪表盘；Glassmorphism 行：backdrop blur 10–20px、半透明白 15–30%，但警告
  低对比度背景/关键无障碍慎用；Flat Design 行：无渐变/阴影、150–200ms ease）、charts.csv 行 1
  （“用实线、虚线、点线 + 直接系列标注；绝不只靠色相区分”）、colors.csv 行 1 SaaS（背景 #F8FAFC、
  前景 #1E293B、次要 #475569、边框 #E2E8F0，与现有配色同系）。
- 拨盘已定：variance 中低、motion 中低、density 高（仪表盘要密而清晰）。
- 落地到代码：
  - 触摸目标：场景栏/天气按钮/Play/ABC/面板按钮一律 `custom_minimum_size.y=44`，间距 8px；
    TimeSlider 最小 (150,44)；顶栏高 48→60（offset_bottom 72，顶部留 12px 边距，左右各 12px 等边距）；
    场景栏 672×56、天气胶囊 352×56。
  - 正文：面板数据行、A/B/C 表格、按钮文字一律 16px；ABC 面板加宽到 548px（offset_left -560）
    以容纳 16px 七列表格；标签/微文案（ModeChip、TimeLabel、WxLabel、ABCNote、保留线注）14px；
    图表轴字 12px（数据可视化微标签，与正文区分，已记录边界）。
  - 对比度：图表轴字 #7d97ad（白底约 3.3:1，不达标）→ #64748b（约 4.8:1）；图例改色块 +
    深色文字 + 当前值（不再用彩色文字）；激活态深绿 #0f766e 上白字约 5.9:1；#475569/#1e293b 系
    白底均 ≥4.5:1。
  - 图表不只靠颜色（charts.gd 重写）：负荷/光伏/购电实线、储能虚线（新 `_draw_dashed_series`）、
    SOC 面积+实线；温度图拉闸虚线、恒温点线（2px dash/3px gap）、当前策略实线 2.4px + 8/12/14/17.5 时
    关键点圆点；图例两行带当前值（pad_t 22→36，SPChart 高 180→200）。
  - 退出比进入快：A/B/C 进入 180ms、退出改为 120ms（约 67%，只淡出不缩放，中途再打开杀掉退出 tween）；
    场景面板切换仍瞬时隐藏（内容替换，非关闭）。
  - 无 emoji/字形图标：PlayButton “▶ 开始仿真/⏸ 暂停”→“开始仿真/暂停仿真”；SPMinBtn
    “收起详情 ▴/展开详情 ▾”→纯文字；SPBack “← 返回总览”→“返回总览”；A/B/C 保供 “✓/✗”→
    “达标/不达标”文字（另因字体缺 ✗ 字形，见字体一节）。
  - 按压反馈改临界阻尼弹簧（spring.gd，见液态玻璃一节）；`?glass=0/low/high` 参数与窄屏自动降质
    已接进 main.gd（`_setup_glass()`，视口变化 >50px 时重算）。
  - 字体：Godot 默认字体不用 Inter（Godot 默认不是 Inter）；深色文字、单字体族（operate.md）。
  - 已知重叠问题记录：ABC 面板（548 宽）与 ScenePanel（360 宽）同处右侧 top 60，可同时出现互相遮挡
    ——此前已存在（旧 470 vs 372），列为 P2，待截屏确认后处理。
- pre-delivery checklist（pro-rules.md）**尚未跑**，收尾时按清单逐项打勾记在这里。

## 17:35–18:35 字体排查（P0 阻塞：Web 导出后中文全是方框）
**现象**：Web 导出后所有中文显示为方框；拉丁字母/数字正常（"09:00"、"B"、"A/B/C"、"V2G" 均可读）。
3D 标签（Label3D）完全不可见。

**已验证的事实**：
- 放大截图（PIL 裁剪 3 倍）显示方框内是**十六进制 Unicode 码点**（如 平→"5E 73"、时→"65 F6"、
  校→"68 21"、光→"51 49"），即 Godot 缺字形时的 hex-box 回退渲染，不是普通 .notdef 空框。
- 系统有 Noto Sans CJK SC：`/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc`（含 Regular/Bold；
  SC 面是 TTC 索引 2；✓ U+2713 在字库里，✗ U+2717 不在，℃ U+2103 在）。
- 子集化字符表：从 data/*.json + scripts/*.gd + scenes/*.tscn 收集非 ASCII 字符 + ASCII 全集，
  851 个字符，存 `tools/chars.txt`（持久化在工程内；早期的 /tmp/chars.txt 已被约 09:34 UTC 的
  服务重启清空）。
- fontTools 4.46.0 可用。子集字体 cmap 完整（校/园/虚/拟/电/厂/晴均在），轮廓真实存在
  （校 10 个轮廓、园 6、晴 11）。

**已尝试且均未解决（每次都重新导入 + 重新导出 + 全新 Chrome profile 截屏）**：
1. 从系统 TTC 提取 SC 面（CFF 轮廓）→ pyftsubset 子集化 → 146KB，
   `assets/fonts/NotoSansSC-Regular.ttf`，`project.godot` 设 `theme/default_font` + MSDF 开 → 仍方框。
2. MSDF 关（`theme/default_font_multichannel_signed_distance_field=false`）→ 仍方框；且发现 MSDF
   开/关两版截图字节完全相同，说明字体渲染路径根本没变。
3. 从 Google Fonts 下载变量 TTF `NotoSansSC[wght].ttf`（17.8MB，glyf 轮廓、fvar 变量，存
   `~/workspace/tools/fonts/NotoSansSC-wght.ttf`）→ 子集化（350KB，glyf）→ 仍方框。
4. instancer 静态化 wght=400（fvar 去掉，208KB）→ 仍方框。
5. 换回完整 17.8MB 原始变量 TTF 直接作 asset（pck 13.5MB）→ **仍方框**。证明问题不在子集化/静态化流程。
6. 发现 `project.godot` 的 `gui/theme/default_font` **在编辑器里也不生效**：fonttest2
   （/tmp/fonttest2.gd）显示 SETTING 正确，但 `ThemeDB.fallback_font.resource_path` 为空、name 为空、
   与显式 load 的对象不相同。
7. 在 main.gd `_ready()` 开头加显式赋值 `ThemeDB.fallback_font = load("res://assets/fonts/NotoSansSC-Regular.ttf")`；
   编辑器 fonttest3 验证赋值有效（path 正确、same=true、中文宽度 96.0）。Web 端诊断打印（临时加在
   main.gd，**确认后删除**）显示：`FONT-DIAG loaded=true fallback-path=res://assets/fonts/NotoSansSC-Regular.ttf`、
   `cn-size=(96.0, 24.0) has-char=true`——**Web 运行时字体对象正确、度量正确、字形存在，但渲染仍是 hex-box**。
8. 储能场景截图（`screenshots/02-storage.png`）放大后给出决定性区分：**图表的 draw_string 文字
   （`ThemeDB.fallback_font` 直接传给 draw_string）中文完全正常**——“负荷 1125、光伏 775、购电 257、
   储能 0（虚线）、SOC 56%、保留线 56%”全部可读；**而 Label/Button/Label3D 的中文全是 hex-box**。
   结论：字体本身没问题，问题在控件取字体的路径。
9. 诊断打印 `title-label-font-path=`（空）vs `window-theme` 的 `win-font-path=`（正确）：即使把字体挂到
   窗口主题的 `default_font` 上，TitleLabel 解析到的仍是内置字体。编辑器 fonttest7 证明：
   `Theme.set_font("font","Label",f)` 本身有效，Window 里新建的 Label 能解析到正确字体；
   但 Web 导出里 `$UI` 下的控件在入树时已缓存内置字体，且 CanvasLayer 截断了窗口主题变更通知。
   另发现 `.import` 里 `language_support={}`、`script_support={}` 均为空——TextServer 可能因此跳过
   该字体去排 Han 文本。
10. 最终修复（三重兜底，已写进代码，待导出验证）：
    - `main.gd`：加载字体后 `set_script_support_override("Hani"/"Latn"/"Zyyy"/"Zinh", true)`；
      `ThemeDB.fallback_font = 字体`；新建 Theme 逐类 `set_font("font", "Label"/"Button"/"OptionButton"/
      "PopupMenu"/"MenuButton", 字体)` + `default_font`，赋给 `get_window().theme`；
      `_apply_ui_font($UI)` 递归给所有 Label/Button/OptionButton 加 `add_theme_font_override("font", 字体)`
      （最高优先级）；`labels.font` / `panel.font` / `ui.font` 逐个传给 Label3D 与动态创建控件。
    - `labels.gd`：`var font: Font`，`add_label` 里 `l.font = font`（Label3D 不走 Control 主题）。
    - `scene_panel.gd`：`var font: Font`，`build()`（策略下拉/外壳开关）与 `set_live()`（数据行/保留线注）
      新建控件时加字体 override。
    - `ui_controller.gd`：`var font: Font`，`_mk_label`（ABC 表格行）新建时加字体 override。
    - 字体换回轻量静态子集版：`tools/fonts/NotoSansSC-static.ttf`（instancer wght=400，10.6MB）→
      `tools/fonts/NotoSansSC-subset.ttf`（`python3 -m fontTools.subset`，282KB，cmap 848 字含校/学，
      glyf 轮廓，无 fvar）→ `assets/fonts/NotoSansSC-Regular.ttf`。完整 17.8MB 变量 TTF 只作诊断用，
      不再进包（它还导致 Web 端主线程疑似阻塞、CDP evaluate 无响应，见下）。

**环境事故（18:0x–18:30）**：
- `/tmp` 是 512MB tmpfs，被 10 多个旧 Chrome 截图 profile（各 45–57MB）塞满 → Chrome 写不了盘，
  shot.mjs 挂起、CDP evaluate 无响应。已清掉，/tmp 回到 10%。教训：shot.mjs 每次新建 profile
  却不清理，需补清理（待办）；中间产物一律放 `~/workspace`，不要放 /tmp。
- 导出变慢：之前约 60–75 秒，现在两次 `timeout 115/280` 都被杀（exit 124），pck 仍是 10:07 旧版
  （11.5MB）。原因待查（机器负载当时 4.26、CPU 只有 1.5 核共享；`.godot/imported/` 里 fontdata
  仍是 09:52 的 13.2MB 旧版，说明重导入没生效）。当前导出以 nohup 后台跑（PID 22107，
  日志 /tmp/export2.log），待它完成后再截屏验证字体。
- 另：`pkill -f "shot.mjs"` 会误杀自己的 shell（模式串出现在自身命令行里），之后只用 PID 或
  `pkill -x chrome`（注意名字超 15 字符的警告）。

**当前状态（约 18:35）**：导出在后台跑；字体修复待导出完成 + 截屏验证。之后：逐场景截图验收 →
修已知问题（标签遮挡/窄屏/池塘/穿模/返航）→ impeccable 双子代理终审（critique + audit）→
UI/UX Pro Max pre-delivery checklist → 22:02 前汇报。

## 18:35–19:00 导出被并行 Blender 任务拖慢（环境，非代码问题）
- 导出（nohup PID 22107/22108，日志 /tmp/export2.log）26 分钟只积累约 46 秒 CPU（约 3% 份额），
  pck 仍是 10:07 旧版。原因：同机有并行 Blender 渲染批处理（另一任务的，脚本在
  `assets/blender/`，共 15 个 .py：ov-bldA/B/C、ov-gym、ov-lab、ov-lib、ov-tower、pv-mount、
  pv-panels、st-cabinet 等，另有 `assets/models/`），持续占满 1.5 核共享 CPU，负载一度 9.02。
  **不杀它们**（不是我的任务，是同工程的并行工作）。
- 导出进程本身活着（State R，13 线程，已读 54MB、只写 36KB，正在准备/打包阶段），不是死锁，
  只是被 CPU 饥饿拖慢；此前两次 `timeout 115/280` 被杀也是同一原因，不是导出本身失败。
  预计再等 10–15 分钟完成。之后尽量少做导出循环（把修复批量攒到一次导出）。
- 数据口径复核（grep 实测，导出等待期间）：旧数字 1969/1877/1805、D-10、168000/183250 只出现在
  “已废弃，不得使用”的注释/note 里，展示值里没有；“净收益”只出现在“文件里没有这个概念”的 note 里；
  权威数字 D-09、1344000、2868、0.5483、0.5827 均在 data/*.json 里。
- 工具修补：`tools/shot.mjs` 的 finally 里加了 Chrome profile 清理（`fs.rm(PROFILE, recursive)`），
  防 /tmp 再次被塞满；另写好 `tools/shots_all.sh`（总览+6 场景+雨/暴雨+窄屏+冻结帧，一键 10 张），
  等导出完成就跑。

## 18:35–19:30 字体修好 + 导出被并行任务拖慢（已解决）
**字体根因（已定位）**：不是字体文件问题，是控件取字体的路径。决定性证据是储能截图放大后：
图表的 `draw_string`（直接传 `ThemeDB.fallback_font`）中文完全正常，而 Label/Button/Label3D
全是 hex-box。原因是引擎默认主题里每个控件类都有一条指向内置字体的 `"font"` 主题项，查找时先命中它，
根本走不到 fallback；且 CanvasLayer 会截断窗口主题变更通知，`$UI` 下的控件在入树时已缓存内置字体。
另 `.import` 里 `language_support`/`script_support` 均为空，TextServer 可能跳过该字体排 Han 文本。
**修复（三重兜底，已落地）**：`main.gd` 里 `set_script_support_override(Hani/Latn/Zyyy/Zinh)` +
`ThemeDB.fallback_font` + 新建 Theme 逐类 `set_font("font", Label/Button/OptionButton/PopupMenu/MenuButton)`
+ `_apply_ui_font($UI)` 递归逐控件 `add_theme_font_override`；`labels.gd`/`scene_panel.gd`/
`ui_controller.gd` 各加 `font` 变量，动态创建的 Label3D/行/按钮创建时直接挂字体。
**字体换回轻量静态子集**：`tools/fonts/NotoSansSC-subset.ttf`（282KB，cmap 848 字，glyf，无 fvar），
完整 17.8MB 变量 TTF 只作诊断用，不再进包。pck 从 11.5MB 缩到 337KB。
**验证（`screenshots/00-overview.png`，11:30）**：中文全部正常——顶栏“平时模式 · B 平急两用 09:00”、
天气胶囊“天气 晴 多云 阴 雨 暴雨”、场景栏“校园总览 光伏屋顶 储能站 教室舒适度 充电区 V2G 配电房”、
提示“拖动旋转 · 滚轮缩放 · 点击设施进入场景”均可读；控制台 0 报错。
**新发现（同张截图放大后）**：
- 标题“校园虚拟电厂 · 源网荷储车协同调度”与时间“09:00”渲染出中文但颜色是默认白字，白底玻璃上几乎看不见
  （对比度 ~1:1）。已修：`main.tscn` 里 TitleLabel 加 `#0f172a`、ClockLabel/TimeLabel 加 `#1e293b`。
- 3D 标签在总览下缩成 2px 小点：Label3D 之前用世界尺寸（pixel_size 0.012、font_size 42 → 约 0.5 世界单位），
  总览距离 235m 时只有约 2px。已修：`labels.gd` 改 `fixed_size = true` + `font_size = 16`（恒定屏幕尺寸，
  与去重叠估算 est_h 26 / fs 13–15 一致）+ outline 10→4；去重叠微调 `world_dy` 改随距离缩放
  （`dy * dist * 0.0016`，之前固定 0.045 在总览下几乎不动）。
- 两处修复已重新导出（pck 356KB，0 报错），待截屏验证（机器被并行 Blender 任务占满，见下）。
**导出慢的根因**：同机并行 Blender 渲染批（另一任务，`assets/blender/` 共 41 个脚本）持续占满 1.5 核
CPU 与内存，负载一度 31，内存只剩约 300MB–1GB，期间还发生两次运行环境重启（11:17、11:25 前后，
后台任务被杀、托管服务被杀后已重启）。原工程直接导出 40 分钟只积累 46 秒 CPU、读盘 7.2GB 仍未写出 pck
（疑似 Blender 持续写文件触发反复重导入），最终被一次 strace 尝试中断。**改用副本导出**：
`~/workspace/demo-godot-export/`（rsync 排除 assets/blender、assets/models、export、screenshots、
.godot、tools；本工程代码不引用 .glb/.blend，已 grep 确认），副本里导入 18 秒、导出 13 秒完成，
再把 export/web/ 拷回真实工程。教训：`rsync 多源多目标`会把倒数第二个参数当源——一次误操作把全部 .gd
拷进副本的 scenes/ 导致 class_name 重复（"hides a global script class"），已删干净并重新导入。
**当前瓶颈**：Blender 批（39/41 个 .blend 已生成，但渲染进程增到 19 个、负载 28–32、内存 <1GB 可用）
导致 Chrome 截图起不来（DevTools 端点 10 秒内不起、一次 OOM 被杀）。已给 shot.mjs 加
`--disable-dev-shm-usage` 与 DevTools 等待 10 秒→60 秒；正在等负载窗口重拍。标题/标签两处修复
已导出、代码层面已核对，截屏验证待补。

## UI/UX Pro Max pre-delivery checklist（pro-rules.md，源码层面逐项）
- [x] 无 emoji 当图标（▶ ⏸ ▴ ▾ ← ✓ ✗ 已全改文字动词，grep 实测）
- [x] 触摸目标 ≥44×44px、间距 8px（场景栏/天气/Play/ABC/面板按钮一律 44px 高）
- [x] 按压反馈 80–150ms 内（弹簧 scale 0.97，按下 100ms、回弹 160ms），只动 transform 不动 layout
- [x] 正文对比度 ≥4.5:1（#1e293b/#475569 白底；图表轴字 #64748b 约 4.8:1；激活态深绿上白字约 5.9:1）
- [x] 图表不只靠颜色（实线/虚线/点线 + 图例色块 + 末端直标值）
- [x] 减弱动效（`?reduced=1` / prefers-reduced-motion：飞行改直接落位，面板只 200ms 透明度）
- [x] 8px 间距节奏（8px 间距、12px 边距）；滚动内容不被固定栏遮（池塘标签 y 钳制、底部预留 84px）
- [ ] 窄屏 375px 与横屏验证——待截屏（机器负载原因，待补）
- [ ] 深色模式——不适用（本 Demo 单一浅色主题，设计决策，非遗漏）
- [ ] 图标统一族——不适用（无图标，全部文字按钮，设计决策）
- 其余 native/app 专属项（安全区、读屏顺序、密码管理器、表单等）不适用（Web 仪表盘，无表单/无原生壳）。

## 19:30–21:00 impeccable 终审：Assessment B 完成，全部 P0/P1 已修并验证
- **Assessment B（确定性源码扫描 + 截屏证据）已完成**：Audit 总分 **10/20**（Acceptable 档）。
  维度：无障碍 1/4、性能 3/4、主题 2/4、响应式 2/4、实现完整性 2/4。
  62 条防 AI 味规则大面积通过（无渐变/紫蓝、无 Inter、无 emoji、无卡中卡、无 kicker、无 AI 腔文案；
  动效全 ease-out、退出 120ms=进入 67%、按压弹簧 0.97；触摸目标 19 个全部 44px；数据口径干净）。
- **P0（阻塞）已修**：面板数值列与 SPTitle/ABCTitle/ABCNote/教室“演示策略” lab 全是默认白字、白底上不可读。
  修法：数值列补 `#1e293b`（scene_panel.gd set_live），标题补 `#0f172a`、ABCNote 补 `#475569` 并提到 16px
  （main.tscn），教室 lab 补 `#1e293b`。
- **P1 已修**：① HintLabel 白字压 3D 浅色场景（1.4–2.1:1）→ 改深色 `#1e293b` + 白描边 4px；
  ② 舒适带绿字 `#059669`（3.77:1）→ `#047857`（约 5:1）；③ ABC 保供列颜色逻辑错误（`_mk_label` 的 bold
  分支无条件覆盖颜色，B 行绿高亮是死代码；A 缺 `backup_ok` 字段默认 false 被误标红）→ 删 bold 颜色覆盖，
  保供按 `backup_h ≥ 4h` 判定（A 7.9h、B 4.4h 达标绿，C 1.6h 不达标红），B 行名绿改 `#047857`。
- **P2 已修**：P2-2（ABCNote 与保留线行 14px→16px）、P2-3（储能标签 `#059669`→`#047857`、充电区标签
  `#ea580c`→`#9a3412`，其余标签色白底均达标）、P2-5（WxLabel“天气”补深色 `#1e293b`）。
  P2-1（TopBar/场景栏/ABC 固定宽、窄屏 <975px/<672px/<560px 溢出）与 P2-4（两套按钮样式并存）**未修**：
  P2-1 需窄屏分支重构、无截屏可验证，列为已知遗留；P2-4 是样式 token 化重构，收尾时间不够，列为已知遗留。
- **P3 已修**：P3-1（激活态对比度注释 5.9:1→5.5:1）、P3-3（面板 VBox 间距 6px→8px）、P3-5（图表 x 轴
  “24:00”末刻度钳制进图内）。P3-2（colors.csv 引用）、P3-4（减弱模式不停闪电/环境摆动）、P3-6（键盘焦点）、
  P3-7（→ 字形）为文档/ minor 项，已记录，未改代码。
- **无头逻辑验证（`tools/verify_fixes.gd`，跑真实代码查运行时状态，不渲染）**：**21/21 全过**。
  覆盖：标题/时钟/WxLabel/HintLabel/SPTitle/ABCTitle/ABCNote 颜色、面板数值列颜色与 16px、Label3D
  fixed_size + font_size 16 + 中文字体、ABC 网格 28 格、A/B/C 保供文字与颜色、B 行名绿、舒适带绿。
  过程中抓到两个真问题并修好：① tscn 里 `#1e293b` 的十进制 B 分量我写成 0.227（应为 0.231，59/255），
  导致实际色是 #1e293a（4 处，已改 0.231）；② 验证脚本自己的 float 取整用截断会差 1（改四舍五入）。
  另：真实工程的 .godot 字体缓存曾过期（`No loader found for resource`），已从副本拷回 .import 与
  199KB fontdata 修好；Web 导出本身一直正常（副本导出）。
- **Assessment A（设计评审）两次派发均未产出**：两个子代理都以 completed 状态结束但无 final answer
  （环境不稳定所致，非任务问题）。按 critique 要求，本应双子代理并行；此处如实记为
  `⚠️ DEGRADED: Assessment A missing (two attempts, no final answer); B complete (10/20)`。
  协调人自己的简要设计复核（单上下文，非 A 子代理）：信息层级清晰（标题/模式芯片/时钟/控制分层明确）、
  配色克制（航拍图系，无紫蓝渐变）、动效克制（仅飞行/面板/按压三处，全部 ease-out）、Operate 仪表盘
  可扫读；遗留设计债是 P2-1 窄屏溢出与 P2-4 两套按钮样式。
- **截屏验收未完成（环境原因，非代码原因）**：除 11:30 总览（字体修复已验证）与 09:58 储能（修复前）外，
  6 场景 + 天气 + 窄屏 + 冻结帧均未拍到。并行 Blender 批（另一任务，41 脚本，`assets/blender/`）持续占满
  机器（负载 8–51、内存常 <1GB 可用），Chrome 多次 OOM 被杀、两次运行环境重启、多次 exec 超时；
  原生 Godot 截图（Xvfb + llvmpipe）170 秒跑不完 30–60 帧。标题/标签/颜色类修复已由无头逻辑验证 21/21
  覆盖，视觉验收待机器空闲后重拍（`tools/shots_all.sh` 一键 10 张已备好）。

## 23:18– 补漏任务：P2-1/P2-4/偏淡/重叠 + P3 小项（与 Blender 拼装并行，验证走 Actions）
- **P2-1 窄屏分支重构**（ui_controller.gd `_apply_narrow_layout` + scene_panel.gd `apply_narrow_layout`，
  视口 resize 信号触发，`_ready` 时 deferred 调一次）：<975 滑杆 150→100；<672 模式芯片隐藏、标题 14px、
  场景栏按钮取消固定宽均分整栏、ABC/场景面板满宽（左右留 12px）；<560 滑杆与时间标签隐藏、天气标签隐藏、
  ABC 表格字 14px（重建一次）、天气按钮 40px。恢复时全部还原因子。
- **P2-4 样式 token 化**（新增 scripts/ui_tokens.gd，单一来源；配色见 data/colors.csv 第 1 行 SaaS）：
  玻璃按钮（场景栏/天气）与实色按钮（顶栏操作/面板按钮）共用 token：实色白底 + #e2e8f0 描边 + 10px 圆角，
  hover #f1f5f9，激活态与玻璃按钮同款深绿 #0f766e + 白字；两类按钮都有 2px #2563eb 键盘焦点环（P3-6）。
  ui_controller/scene_panel 里原来 `_style_glass_button` 的实现与默认主题按钮全部改走 UITokens；
  UITokens 用 preload 引用（新文件进不了本地陈旧的 .godot 类缓存，headless 报未声明；Actions 新检出不受影响）。
- **总览偏淡**：天顶 #8ec9f0→#63a9e6（weather_system.gd `day`，每帧覆盖处）、初始天空材质加深、
  tscn Environment 背景/环境/雾色加深；地面绿 #69b45e→#4f9d43、内场绿 #46a04e→#3d8f43（data/campus.json）。
- **ABC/场景面板重叠**（ui_controller.gd `layout_panels`，main.gd 在面板显隐处调用）：双开时场景面板顶 =
  ABC 底 + 12（452）、底贴场景栏上方（anchor_bottom=1.0、offset_bottom=-84）；单开恢复顶 60、底 620。
- **P3**：P3-2 data/colors.csv 落到工程内（SaaS 行原样复制），ui_controller 注释改指 res://data/colors.csv；
  P3-4 减弱动效贯通 weather（`reduced_motion` 标志：停闪电、云漂移、云影漂移）+ main 树摆停摆；
  P3-6 焦点环见上；P3-7 界面文字 "DC→AC" 改 "DC 转 AC"（子集字体含 转/直/流/交 字形，已核对 cmap）。
- **修法中的两个坑（已修好）**：① 第一版误删了 `_abc_tween/_abc_token/_abc_exit_token` 声明（已补回）；
  ② verify 脚本 detail 参数误传 Color（`_chk` 要求 String）导致每帧报错循环、到不了 quit（已包 `_col()`）。
- **无头逻辑验证 49/49 全过**（原 21 + 新 28）：token、窄屏 390/1280 双向、双开重叠、 sky/地面色、
  减弱动效四项、colors.csv、→ 字形。本地只跑无头验证，未渲染未截图（按任务要求走 Actions）。
- **Actions 首跑踩坑（已定位，在修）**：新检出没有 `.godot/` 类缓存，`--headless -s` 直接跑验证时
  全部 class_name（SimEngine、ScenePanel……）解析不到，脚本编译失败；且验证脚本中途报错会跳过 quit()
  下帧重跑、无限循环，首跑刷出 193MB 日志、两路运行卡在 Headless verify 步 25 分钟以上。
  修复：① workflow 在验证前加 `--import` 建缓存；② 验证步加 `timeout-minutes: 10`；③ 验证脚本加防空转
  （60 帧未完成 quit(2)；ScenePanel 没挂上 set_live 立刻 quit(2)）。已取消三路卡住的运行，重推重跑。
- **--import 本身也卡（已定位，在修）**：本地全新导入复现——有 `assets/blender/` 时 300 秒零导入；
  去掉它后开始走（145 个已导入），但 43 个 .glb + 烘焙贴图在 1.5 核本机上极慢（又 240 秒只到 163 个），
  且 `tools/fonts/NotoSansSC-static.ttf`（17.8MB 全量字体）导入也很慢。
  修复：三个 `.gdignore` 提交进仓库——`assets/blender/`（.blend 不是 Godot 运行时内容，Godot 只用 .glb）、
  `export/`（54MB 导出产物）、`tools/fonts/`（运行时只用 `assets/fonts/` 的子集字体）；
  import 步加 `timeout-minutes: 20`。本地因 CPU 被 Blender 烘焙占满、多次被运行时重启打断，未能跑完一次全量导入；
  以 Actions 跑 4 核无争用为准验收。
- 待 Actions：推仓库 → 触发 godot-verify → 验证脚本 + Web 导出 + 10 张截图验收。

## 收尾状态（22:02 前）
- 工程：`demo-godot/`（project.godot、6 scenes、11 scripts、6 data JSON、shaders、assets/fonts 282KB 子集字体）。
- Web 导出：`export/web/`（index.html + index.js + index.wasm 41MB + index.pck **362KB**，2026-11-22 13:02，
  0 报错；用 `python3 serve_web.py` 起 127.0.0.1:8931，加 COOP/COEP 头，线程版）。
- 数据口径：已纠正并 grep 复核（D-09、1344000、2868、0.5483/0.5583/0.3583、0.5827；旧数字只在“已废弃”注释里）。
- 已知遗留（诚实写）：① 6 场景 + 天气 + 窄屏 + 冻结帧截屏未验收（环境原因）；② P2-1 窄屏 TopBar/场景栏/ABC
  溢出未修；③ P2-4 两套按钮样式未统一；④ Assessment A 缺失（两次派发无产出）；⑤ 总览画面偏淡
  （地面绿与天空蓝过浅，可加深饱和/光照，未做）；⑥ ABC 面板与 ScenePanel 右侧重叠（P2，旧问题）。
- 副本导出目录 `~/workspace/demo-godot-export/`（排除 Blender 资产的干净副本，供导出用；真实工程里的
  Blender 资产是并行任务的，不要删）。
- 21:25 第三次运行环境重启（前两次约 11:17、11:25），后台截图与托管服务被杀后已重启
  （serve 127.0.0.1:8931 正常，pck 362272 字节最新版）。原生 Godot 截图（Xvfb + llvmpipe）试了
  10/30/60/150 帧三档均未在 170 秒内完成（llvmpipe 在负载下帧率过低），Chrome 截图则因 DevTools
  起不来/OOM 被杀多次失败；截屏验收至此停止，不再重复尝试，待机器空闲后用 `tools/shots_all.sh` 重拍。


