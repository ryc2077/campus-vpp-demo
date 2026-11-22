# 校园虚拟电厂 Demo — Godot 重写版

苏州大学附属中学 · 启明队 · 全国青少年科学探究建模能力大赛（高中组）。
原 Three.js 单文件 Demo（`../demo/demo.html`，约 906KB）的 Godot 4.4 工程重写版：
一批文件（场景 / 脚本 / 数据 JSON），Web 导出也是一批文件（index.html + .js + .wasm + .pck）。

## 数据口径（权威来源，勿混用旧版）

以 **2026-10-31 三份手工修改版核心文件**为准：`~/workspace/user/files/upload.docx`（申报书）、
`~/workspace/user/files/1031.docx`（研究报告）、`~/workspace/user/files/1.docx`（科学探究日志）。
演讲 / PPT 以 `~/workspace/user/files/1.pptx` 为准。原 `demo.html` 里的旧数字
（D-10、1969/1877/1805 元、61 元/日净收益、168000/183250 元）已废弃，本工程一律不用。
权威数字全部放在 `data/*.json` 里，脚本只读数：

| 数据 | 文件 | 关键值 |
|---|---|---|
| 台账 | `data/bill.json` | D-09；2025 合计 1,344,000 元；9 月 177,000 元（1.58 倍）、7 月 50,000 元（0.45 倍）、极差比 3.54 |
| 电价 | `data/bill.json` | 居民峰谷：平 0.5483 / 峰 0.5583 / 谷 0.3583 元/kWh；碳因子 0.5827 |
| A/B/C 典型日 | `data/strategies.json` | A 2868/1250/1673/335kW/78.7%/7.9h；B 2780/1201/1622/280kW/81.8%/4.4h 达标；C 2710/1162/1581/255kW/84.2%/1.6h 不达标；B 相对 A 日减外购 88kWh、日省 49 元、日减碳 51kg、削峰 55kW；年化（250 教学日）年省电约 22,000kWh、年减碳约 13 吨 |
| 保留线 | `data/strategies.json` | 核心负荷 25kW × 4h ÷ 0.92 × 1.10 ≈ 120kWh（占 55.6%），日常可用约 95kWh |
| 光伏 | `data/bill.json` | 800kWp 是团队实测屋顶 4856m² 算出的**规划容量**，学校现状无装机；典型日光伏约 3399kWh（自用 2675、余量 724） |
| 教室 | `data/classroom.json` | 约 70.3㎡（7.26m × 9.68m），有效教室 53 间；美的 KFR-120LW/BP3SDN8Y-PA401(2)，制冷 12150W/输入 3500W，每间 2 台 5 匹 |
| 配电 | `data/campus.json` | 10kV 双路进线、4 台主变合计 3000kVA |
| 天气 | `data/weather.json` | 晴 13.0h/1.00、多云 12.0h/0.75、阴 11.0h/0.45、雨 10.0h/0.30、暴雨 9.0h/0.15（情景设定，非实测） |

三份文件里**没有“净收益”概念**，没有五项新增节能、没有 168000/183250 元——本工程不写。
峰谷价差仅 0.2 元/kWh，低于循环损耗 0.35 元/kWh：日常放电为**条件触发**
（只有充电能全部由午间光伏富余承担时才放电）。

## 工程结构

```
demo-godot/
  project.godot            Godot 4.4 工程（Compatibility 渲染器，Web 友好）
  export_presets.cfg       Web 导出预设 → export/web/
  scenes/
    main.tscn              总览 + 全部 UI（顶栏/场景栏/天气栏/时间控制/A-B-C 面板/场景面板）
    classroom_interior.tscn  教室內景（模型一）
    dist_interior.tscn       配电房內景（调度中心）
    storage_interior.tscn    储能站內景细节（PCS 风扇/流光点）
    pv_detail.tscn           光伏屋顶细节（逆变器/流光点/阳光射线）
    charge_detail.tscn       充电区细节（V2G 能量弧线）
  scripts/
    main.gd                主控制器：数据→仿真→场景进出→面板刷新
    data_loader.gd         JSON 加载
    sim_engine.gd          96 点能量平衡仿真（移植原 Demo buildPlan，电价已换权威值）
    classroom_model.gd     模型一：一阶热惯性，三策略对比
    camera_rig.gd          轨道相机：飞入 1 秒、拖动取消、场景限位防穿模
    campus_builder.gd      校园程序化建模（建筑/道路/操场/池塘/储能/充电/变压器）
    labels.gd              标签：深度遮挡 + 屏幕去重叠 + 底部预留（修池塘遮挡）
    weather_system.gd      五档天气：光照/云/云影/雨幕/暴雨闪电
    charts.gd              曲线图（24h 运行曲线 / 教室温度曲线，窄屏自适应刻度）
    scene_panel.gd         场景面板：只留图表与数据行，无介绍文字
    ui_controller.gd       顶栏/场景栏/天气栏/时间控制/A-B-C 对照
  data/  campus.json  strategies.json  bill.json  weather.json  classroom.json  scenes.json
  assets/  （贴图/图标预留，目前程序化建模无外部贴图）
  export/web/  Web 导出产物（index.html + .js + .wasm + .pck）
  screenshots/ 验收截图
```

## 怎么打开

### 方式一：Godot 编辑器运行（推荐开发）
1. 安装 Godot 4.4：https://godotengine.org/download/linux/ （本机已装在 `~/workspace/tools/godot/Godot_v4.4-stable_linux.x86_64`）
2. `godot --path demo-godot` 打开工程，按 F5 运行（或点 ▶）。

### 方式二：Web 导出（给评委/用户看）
1. 下载导出模板（Godot 4.4 stable export templates），解压到 `~/.local/share/godot/export_templates/4.4.stable/`。
2. 在工程目录执行：
   `~/workspace/tools/godot/Godot_v4.4-stable_linux.x86_64 --headless --path . --export-release Web export/web/index.html`
3. 用 HTTP 服务托管 `export/web/`（Godot Web 导出需 http(s)，不能直接 file:// 打开）：
   本工程自带 `serve_web.py`（加 COOP/COEP 头，线程版必需）：`python3 serve_web.py` → http://127.0.0.1:8931/
   注意：线程版导出需要跨域隔离头；如浏览器报 SharedArrayBuffer 相关错误，用
   `--threads` 关掉线程或改用单线程导出（见 export_presets.cfg 的 `variant/thread_support`）。

**导出注意（2026-11-22 实测）**：本工程目录里有并行任务的 Blender 资产（`assets/blender/`、`assets/models/`，
本 Demo 代码不引用），直接在原工程导出会被持续写入的文件拖慢甚至拖死（实测 40 分钟未完成）。
改用干净副本导出：`rsync` 排除 blender/models/export/screenshots/.godot/tools 到
`~/workspace/demo-godot-export/`，在副本里 `--import` + `--export-release`，再把 `export/web/` 拷回。
副本导出约 1 分钟。不要删 `assets/blender/`、`assets/models/`（并行任务的）。

### 无头逻辑验证（不渲染，跑真实代码查运行时状态）
`godot --headless --path . -s tools/verify_fixes.gd`：检查标题/数值列颜色、Label3D fixed_size、
ABC 保供逻辑等 21 项。2026-11-22 收尾时 **21/21 全过**。截图验收脚本见 `tools/shots_all.sh`
（总览+6 场景+雨/暴雨+窄屏+冻结帧，一键 10 张；截图驱动 `tools/shot.mjs`，无头 Chrome + CDP）。

## 当前状态（2026-11-22 22:02 收尾）
- Web 导出：`export/web/`（index.html + index.js + index.wasm 41MB + index.pck **362KB**，13:02，
  0 报错；中文字体为 282KB 静态子集 Noto Sans SC，pck 从 11.5MB 缩到 362KB）。
- 中文字体已修并验证：11:30 总览截图中文全部正常（顶栏/天气胶囊/场景栏/提示）。根因是控件取字体路径
  （默认主题的 `"font"` 项先命中内置字体 + CanvasLayer 截断主题变更通知），修法见 PROGRESS.md（字体一节）。
- impeccable 终审 Assessment B：10/20；P0/P1 全部修完并经 `verify_fixes.gd` 21/21 验证。
  Assessment A 两次派发均未产出（环境不稳定），设计复核为协调人单上下文简述，见 PROGRESS.md。
- **未完成（诚实写）**：6 场景 + 天气 + 窄屏 + 冻结帧截屏未验收——并行 Blender 任务持续占满机器
  （负载 8–51、内存常 <1GB），Chrome 多次 OOM 被杀、两次环境重启；`tools/shots_all.sh` 已备好，
  待机器空闲后重拍。另：窄屏 TopBar/场景栏/ABC 溢出（P2-1）与两套按钮样式（P2-4）未修，见 PROGRESS.md。

### 调试图（URL 参数，仅 Web 导出）
`?scene=pv&wx=rain&hour=12` 直接进场景并切天气；`&shot=1` 再加直接落位不飞行动画（截图验收用）。
例：`http://localhost:8932/?scene=classroom&wx=sunny&hour=12&shot=1`

## 操作

- 场景栏（底部，6 个入口）：校园总览 / 光伏屋顶 / 储能站 / 教室舒适度 / 充电区 V2G / 配电房。
  教学楼、餐厅、图书馆、实验室、宿舍区、艺体馆、校门 7 个入口已删，建筑外形保留。
- 飞入 1 秒：单段 1000ms；教室/配电房两段各 500ms（楼前 → 剖切口 → 内景），退出同理；拖动/滚轮即取消。
- 顶栏：天气五档切换、时间滑杆（96 点）、播放、A/B/C 对照面板。
- 场景面板：只留图表与实时数据行（教室温度曲线 + 策略下拉、储能 SOC 条、车辆 SOC 条、配电房负载数据、光伏发电曲线、A/B/C 对照），无介绍文字段落。
- 窄屏（<760px）：场景面板默认收起、标签只留主标签、曲线图横轴改 6 小时间隔。

## 已修的原 Demo 已知问题

1. 总览下 4 个标签（一号教学楼、艺体馆、创造力中心、图书馆）被别的标签挡住不显示 →
   标签改为深度遮挡射线检测（被楼体挡住才隐藏）+ 屏幕空间去重叠（低优先级标签上下微调避让），见 `scripts/labels.gd`。
2. 窄屏曲线图时间字拥挤 → `scripts/charts.gd` 宽度 <560 时横轴只标 0/6/12/18/24 时。
3. 池塘标签被场景按钮栏遮住 → 标签屏上 y 钳制在视口高 − 84px 以上。
4. 真实浏览器里穿模手感、返回总览飞行效果 → 场景限位（轨道钳制 + 相机位置盒）+
   两段退出飞行（内景 → 楼前 500ms → 总览 500ms）；飞行被打断时立即完成剖切/恢复，不停在墙里。
   （以上修复均以本机截图验收为准，见 `screenshots/` 与 `PROGRESS.md`；未验证的项如实记在 PROGRESS.md，不谎称修好。）

## 诚信红线

- 网上/公开数据不得标成实测；账单、铭牌、测绘等真实数据可按实测写，仿真情景必须标情景/暂估。
- 储能 100kW/215kWh 是公开典型模块，非学校实测；学校储能真实容量未提供。
- 光伏 800kWp 是规划容量（实测屋顶折算），学校现状无装机。
- 96 点仿真曲线是日内形状演示，不冒充实测曲线；教室温度序列未实测、待校准。
- 场景面板与 A/B/C 对照只写三份核心文件里有的数。
