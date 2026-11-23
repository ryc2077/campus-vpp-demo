#!/bin/bash
# 逐场景截图验收（总览+6场景+天气+窄屏+冻结帧），每张全新 Chrome profile，自动清理。
# 用法：bash tools/shots_all.sh [base_url]，默认 http://127.0.0.1:8931
BASE="${1:-http://127.0.0.1:8931}"
cd "$(dirname "$0")/.."
mkdir -p screenshots # 新检出仓库里没有 screenshots/ 目录，shot.mjs 写文件会 ENOENT（rc=2）
FAILED=0
shot() { # $1=query $2=outfile $3=w $4=h $5=wait $6=settle
  # 诊断行不过滤：[shot-fail]/[page]/[chrome] 曾被旧 grep 吞掉，10 张全挂还显示 done。
  node tools/shot.mjs "${BASE}/?$1" "screenshots/$2" "${3:-1280}" "${4:-720}" "${5:-20000}" "${6:-3000}" 2>&1 | grep -E "\[shot\]|shot-fail|\[page\]|\[console\]|\[chrome\]|FONT-DIAG" | head -8
  rc=${PIPESTATUS[0]}
  if [ "$rc" -ne 0 ] || [ ! -f "screenshots/$2" ]; then echo "--- $2 FAILED rc=$rc"; FAILED=1; else echo "--- $2 done"; fi
}
shot "shot=1&hour=9" 00-overview.png
shot "scene=pv&shot=1&hour=12" 01-pv.png
shot "scene=storage&shot=1&hour=12" 02-storage.png
shot "scene=classroom&shot=1&hour=10" 03-classroom.png
shot "scene=charge&shot=1&hour=18" 04-charge.png
shot "scene=dist&shot=1&hour=15" 05-dist.png
shot "scene=pv&shot=1&hour=12&wx=rain" 06-pv-rain.png
shot "scene=overview&shot=1&hour=9&wx=storm" 07-overview-storm.png
shot "shot=1&hour=9" 08-narrow.png 390 844 20000 3000
shot "scene=classroom&shot=1&hour=10&freeze=0.5" 09-freeze.png
# --- 覆盖补拍（2026-11-24，验收缺口 3/4/5）---
# 10：储能放电时段柜面近拍（hour=10 时 batt=+100kW 放电，流光点可见；
#   12:00 待机 batt=0 柜面无流光点；23:00 谷段充电是夜里不适合拍。
#   ?close=1 用柜面近拍机位 dist 5m 正对 3 台电池柜前脸）
shot "scene=storage&shot=1&hour=10&close=1" 10-storage-discharge-closeup.png
# 11：charge 雨天（hour=12 时 V2G 放电 54kW、弧线晴天应显示，雨天 pv_factor=0.30 应隐藏）
shot "scene=charge&shot=1&hour=12&wx=rain" 11-charge-rain.png
# 12：charge 晴天对照（与 11 同机位同时刻：弧线本身存在性的阳性对照，
#   否则 11 里弧线缺席无法区分“雨天隐藏”还是“弧线根本不存在”）
shot "scene=charge&shot=1&hour=12" 12-charge-sunny.png
# 13–15：GLB 回退分支演练（?fallback=1 强制全部 GLB 加载失败、走程序化回退；
#   开关在代码里，不改名/不移走 GLB 文件，正常截图不受影响）
shot "scene=storage&shot=1&hour=12&fallback=1" 13-fallback-storage.png
shot "scene=charge&shot=1&hour=12&fallback=1" 14-fallback-charge.png
shot "shot=1&hour=9&fallback=1" 15-fallback-overview.png
if [ "$FAILED" -ne 0 ]; then echo "SHOTS FAILED"; exit 1; fi
echo "ALL DONE"
