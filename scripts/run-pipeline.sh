#!/usr/bin/env bash
# ============================================================
# run-pipeline.sh —— LongBiosci 本地管线一键运行器（v1.1）
#
# 用法：
#   ./run-pipeline.sh [仓库根目录] [--date YYYY-MM-DD] [--now "YYYY-MM-DD HH:MM:SS"]
#
#   root   仓库根目录，默认当前目录
#   --date / --now  透传给 add-rss-today-run.py（仅用于确定性复现；
#                   日常运行不要传，脚本会自动取当天 UTC 日期与当前时刻）
#
# 依次执行 14 个环节（顺序与 .github/workflows/regen-index.yml 注释记载一致）：
#   1 build-index.py        从 news/*.html 重建 data/articles.json（追加式）
#   2 sync-evidence.py      把 news/*.html 的分级回写 articles.json（--write；治回退顽疾）
#   3 gen-home.py           生成 index.html
#   4 gen-topic-pages.py    生成 topics/ 8 个专题页 + 12 个分页页 + 索引页
#   5 gen-news-index.py     生成 news/index.html 与 news-2..N.html 分页
#   6 gen-evidence-pages.py 生成 evidence/ 索引页 + A/B/C 分级列表（含分页）
#   7 gen-industry.py       生成产业板块：/industry/ 事件流 + /companies/ 公司档案 + /events/ 会议日历
#   8 rebuild-sitemap.py    重建 sitemap.xml
#   9 add-rss-today-run.py  把当日新文章追加进 rss.xml（无新增则幂等不变）
#  10 inject-poster.py      给文章页注入 /poster.js（已有则跳过）
#  11 sync-search-index.py  重建 data/search-index.json 并刷新 search.html 计数
#  12 refresh_counts.py     把各处「N 篇」计数回写为事实源（幂等；本环节自愈）
#  13 audit-traceability.py 溯源完整性审计（只报告不阻断，产出 data/traceability-audit.json）
#  14 check-links.py        全站死链 + 计数一致性检查（末位硬校验，不通过则本管线失败）
#
# 环节 2 为什么必须放在 3~7 之前（2026-10-17 新增）
# ---------------------------------------------
# build-index.py 把「已登记记录」当权威基线整体保留，HTML 侧的分级更正不回写。
# 于是只要远端带回一份旧 articles.json 快照，分级就会回退 —— 页面显示 A、
# 数据源是 C，站内出现「同一篇文章两个分级」。此坑已复现 3 次
# （2026-10-17 当日 2 次 + 本轮 1 次），靠人工跑一次补丁挡不住。
# 放在环节 2 = 每次构建都以 HTML 为事实源自愈一次，从机制上关掉这条路径。
#
# 环节 6 为什么必须放在 7 之前（2026-10-17 新增）
# ----------------------------------------
# evidence/ 的分级列表页此前是纯静态遗留页，无任何生成器管辖：
# 索引页长期写 A 94 / B 269 / C 17，而事实是 A 131 / B 311 / C 109，
# 三个分页各只列 25 / 25 / 18 条 —— 读者在 /evidence/ 上看不到 B 级其余 286 篇。
# 改为生成后，分页数量会随分级变动而增减，故必须在 sitemap 重建之前产出，
# 否则 sitemap 会收录/遗漏错误分页。
#
# 环节 7 为什么必须放在 8（sitemap）之前、且是产业板块的唯一入口（2026-10-18 新增）
# -----------------------------------------------------------------------
# /companies/、/events/、/investors/ 此前是手写孤儿页：无数据源、无生成器、
# git 各只有 1~2 次提交，内容靠人肉记忆维护。2026-10-18 全站审计时，
# /companies/ 14 条卡片查出 6 处硬伤（Altos Labs 杜撰创始人、NewLimit 技术方向写错、
# 已终止的合作写成在研、年份 2014 应为 2008 …），/investors/ 5 条查出 3 处
# （"Peter Berg" 实为 Peter Thiel、Foresite 负责人写成斯坦福教授 Tony Wyss-Coray、
# 无实据的"Krispy Kreme 家族办公室"）。根因不是写错了，是没有任何机制阻止写错。
# 故本环节从 data/industry.json 事件流重建三页：
#   · 公司卡片只存不随时间变的属性（名称/别名/技术方向/状态）
#   · 融资、收购、临床、监管一律来自 events，且 events 每条必带 source，
#     无来源的事件会被生成器跳过并告警 —— 从机制上杜绝杜撰
# 放在 sitemap 之前，是因为 industry/ 已进 sitemap 列表，
# 先出页面再重建 sitemap，否则 sitemap 会漏收新板块。
#
# 环节 12 为什么放在校验之前（2026-10-16 新增）
# ------------------------------------------
# 概念页页标 / research/index.html / 首页概念卡片的计数此前**不归任何生成器管**，
# 只能靠人手跑 refresh_counts.py，于是每次内容摄入重建站点后都漂一次
# （第一次 380→482 漂、第二次 546 篇时又漂，两次都是人工发现人工修）。
# 接入管线后由环节 9 自动回写，末位再校验——分工是：
#   · 环节 9 负责「自愈」：把计数改成事实源值，并在 stdout 打印改了哪些
#   · 末位负责「兜底」：死链仍会硬失败；若环节 9 之后计数还不一致，
#     说明出现了刷新器覆盖不到的新计数点，必须人工介入而不是静默放过
# 顺序不可颠倒：先刷新后校验。若先校验，漂移会让管线在末位直接红，
# 内容摄入被卡住，而漂移本身又没人修——这正是此前两周的实际状态。
#
# 环节 13 为什么只报告不阻断（2026-10-16 新增）
# -------------------------------------------
# 溯源审计量的是「每篇有没有 DOI / 有没有可点来源」，对照 /about/ 的溯源承诺。
# 现状有缺口（约 138 篇无 DOI、十余篇彻底无来源），但缺口是**历史存量**，
# 不是本次管线跑出来的新伤——让它硬失败等于拿历史问题卡住今天的内容摄入。
# 故只报告、退出码恒 0，把数字固化成 data/traceability-audit.json 供趋势对比；
# 等缺口收敛到可接受水平后再考虑升级为硬校验。
#
# ⚠️ 不要在 GitHub Actions 里跑：checkout 会重置全部文件 mtime，
#    导致环节 5 的非文章页 lastmod 全量漂移到 checkout 当天。
#    本管线只在文件真实所在的机器（本地）运行。
#
# 管线只管「站内一致性」，不管「产出消化」——后者由 cursor.py + 内容摄入巡检任务负责。
# ============================================================
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${1:-$(pwd)}"
if [[ $# -gt 0 ]]; then shift; fi

if [[ ! -d "$ROOT" ]]; then
  echo "根目录不存在: $ROOT" >&2
  exit 1
fi

PYTHON="${PYTHON:-python3}"

# 少数脚本需要额外命令行开关，集中在这里显式声明，别藏在通用逻辑里
# （sync-evidence 必须带 --write，否则只预览不落盘；add-rss 接受透传参数）
step() {
  local n="$1" script="$2" desc="$3"
  shift 3
  printf '\n[%s/14] %-22s %s\n' "$n" "$script" "$desc"
  case "$script" in
    add-rss-today-run.py) "$PYTHON" "$HERE/$script" "$ROOT" "$@" ;;
    sync-evidence.py)     "$PYTHON" "$HERE/$script" "$ROOT" --write ;;
    *)                    "$PYTHON" "$HERE/$script" "$ROOT" ;;
  esac
}

echo "管线根目录: $(cd "$ROOT" && pwd)"

step 1  build-index.py         "重建 data/articles.json"
step 2  sync-evidence.py       "证据分级以 HTML 为事实源回写（自愈回退）"
step 3  gen-home.py            "生成首页 index.html"
step 4  gen-topic-pages.py     "生成 topics/ 专题页与索引页"
step 5  gen-news-index.py      "生成 news 列表分页"
step 6  gen-evidence-pages.py  "生成 evidence/ 分级索引与 A/B/C 分页"
step 7  gen-industry.py        "生成产业板块：事件流 / 公司档案 / 会议日历"
step 8  rebuild-sitemap.py     "重建 sitemap.xml"
step 9  add-rss-today-run.py   "追加当日新文章到 rss.xml"
step 10 inject-poster.py       "注入海报脚本 /poster.js"
step 11 sync-search-index.py   "重建站内搜索索引与计数"
step 12 refresh_counts.py      "各处「N 篇」计数回写事实源（幂等）"
step 13 audit-traceability.py  "溯源完整性审计（只报告，不阻断）"
step 14 check-links.py         "全站死链与计数一致性检查（末位硬校验）"

printf '\n✅ 管线执行完成（14/14）\n'
