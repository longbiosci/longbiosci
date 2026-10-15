#!/usr/bin/env bash
# ============================================================
# run-pipeline.sh —— LongBiosci 本地管线一键运行器（v1.0）
#
# 用法：
#   ./run-pipeline.sh [仓库根目录] [--date YYYY-MM-DD] [--now "YYYY-MM-DD HH:MM:SS"]
#
#   root   仓库根目录，默认当前目录
#   --date / --now  透传给 add-rss-today-run.py（仅用于确定性复现；
#                   日常运行不要传，脚本会自动取当天 UTC 日期与当前时刻）
#
# 依次执行 7 个环节（顺序与 .github/workflows/regen-index.yml 注释记载一致）：
#   1 build-index.py        从 news/*.html 重建 data/articles.json（追加式）
#   2 gen-home.py           生成 index.html
#   3 gen-topic-pages.py    生成 topics/ 8 个专题页 + 12 个分页页 + 索引页
#   4 gen-news-index.py     生成 news/index.html 与 news-2..N.html 分页
#   5 rebuild-sitemap.py    重建 sitemap.xml
#   6 add-rss-today-run.py  把当日新文章追加进 rss.xml（无新增则幂等不变）
#   7 inject-poster.py      给文章页注入 /poster.js（已有则跳过）
#   8 sync-search-index.py  重建 data/search-index.json 并刷新 search.html 计数
#   9 check-links.py        全站死链 + 计数一致性检查（不通过则本管线失败）
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

step() {
  local n="$1" script="$2" desc="$3"
  shift 3
  printf '\n[%s/9] %-22s %s\n' "$n" "$script" "$desc"
  if [[ "$script" == "add-rss-today-run.py" ]]; then
    "$PYTHON" "$HERE/$script" "$ROOT" "$@"
  else
    "$PYTHON" "$HERE/$script" "$ROOT"
  fi
}

echo "管线根目录: $(cd "$ROOT" && pwd)"

step 1 build-index.py        "重建 data/articles.json"
step 2 gen-home.py           "生成首页 index.html"
step 3 gen-topic-pages.py    "生成 topics/ 专题页与索引页"
step 4 gen-news-index.py     "生成 news 列表分页"
step 5 rebuild-sitemap.py    "重建 sitemap.xml"
step 6 add-rss-today-run.py  "追加当日新文章到 rss.xml"
step 7 inject-poster.py      "注入海报脚本 /poster.js"
step 8 sync-search-index.py  "重建站内搜索索引与计数"
step 9 check-links.py        "全站死链与计数一致性检查"

printf '\n✅ 管线执行完成（9/9）\n'
