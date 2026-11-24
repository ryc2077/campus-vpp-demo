# 云贴图（R2-T12，2026-11-24）

两张云片贴图均由网上现成的实拍云照片裁切 + 抠天制成，**没有手捏、手绘**。
原图未入仓（可按 SOURCES.md §6 直链重新下载，原图 SHA256 见该节）。

- `cloud_puff.png`（870×780 RGBA，约 0.6 MB）：晴/多云/阴天用。
  原图：Wikimedia Commons《A single cumulus cloud in a clear daytime sky.jpg》，
  WarmaFiesta，**CC-BY 4.0**（署名见 SOURCES.md §6）。
  裁切：原图 2448×3264 的 (850,1420)–(1720,2200)，只取孤立积云本体，树与地面已排除。
  抠天：白度键（min 通道 smoothstep 0.30→0.80）+ 裁切边 9% 羽化 + 轻度去饱和
  （去蓝调、保留亮度明暗），见 `/tmp/cloud-cand/make_sprites.py`（方法记录在 SOURCES.md）。
- `cloud_storm.png`（1024×717 RGBA，约 1.2 MB）：雨/暴雨用。
  原图：Wikimedia Commons《Cumulonimbus viewed from airplane.jpg》，
  Shyamal，**CC0 1.0**。
  裁切：原图 4354×3136 的 (1500,1000)–(3900,2680)，取中央亮白积雨云塔。
  抠天：同上白度键（0.32→0.85）+ 羽化 + 去饱和；灰色云幕背景无法用蓝天键分离，
  保留为半透明云幔，雨天压暗后正好作雨层。

接入：`scripts/weather_system.gd` 的 `_build_clouds`——每组云 = 1 张主云片 +
2 张小云片（同材质、同贴图、左右错开拼成云团），StandardMaterial3D
`BILLBOARD_ENABLED`，`set_weather` 按天气档换贴图（雨/暴雨换 storm）、
按 `cloud_cover` 显隐（晴 1 组 / 多云 3 组 / 阴 5 组 / 雨 6 组 / 暴雨 7 组）、
按档缩放（晴 0.9 / 多云 1.0 / 阴 1.12 / 雨 1.18 / 暴雨 1.25）。
体积云在 GL Compatibility 渲染器下不可行（无体渲染管线），故用 billboard 贴图云片。
