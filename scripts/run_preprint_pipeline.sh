#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# run_preprint_pipeline.sh —— 衰老预印本「抓取→全文→定级→解读→发布」每日流水线
#
# 用法：bash scripts/run_preprint_pipeline.sh [YYYY-MM-DD]
#   不带日期 = 跑昨天（与每日自动化节奏一致：早上跑前一日）
#
# 流程：
#   1. preprint_daily.py          抓当日 bioRxiv/medRxiv 宽口径命中（翻页）
#   2. fetch_medrxiv_fulltext.py  medRxiv JATS 全文抓取（串行 30s 限速）
#   3. fetch_medrxiv_retry.py     退避补抓（30/60/120s，本轮实测 13/13 救回）
#   4. jats_to_text.py            完整性定级 full/partial/empty（判据是正文长度）
#   5. build_fulltext_summary.py  重建累积池 _final_summary.json
#   6. gen_daily_fulltext.py      生成当日全文级速递页 + 自动发布 index/rss（幂等）
#   7. rebuild-sitemap.py         新页进 sitemap
#
# 纪律（2026-10-19 实测，勿改）：
#   - medRxiv 必须串行 + 条间 sleep≥30；429 是瞬时的，退避后必恢复，别放弃
#   - bioRxiv 内容页/JATS 恒定 403（IP 封禁），流水线不尝试、不重试，直接按 0 全文处理
#   - 探测 medRxiv 必须用真实 DOI（假 DOI 吃 Cloudflare 403，会误判成封禁）
#   - HTTP 200 ≠ 全文到手，定级只看正文文本长度
#
# 日志：/tmp/preprint_<date>.log
# ═══════════════════════════════════════════════════════════════════
set -uo pipefail   # 故意不用 -e：全文抓取允许部分失败，由后续汇总如实反映

DATE=${1:-$(date -d "yesterday" +%F)}
ROOT=/workspace
cd "$ROOT" || exit 1
LOG=/tmp/preprint_${DATE}.log
: > "$LOG"

step() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }

step "流水线启动：目标日期 $DATE"

step "1/7 抓取当日命中（bioRxiv + medRxiv details API，翻页）"
python3 scripts/preprint_daily.py "$DATE" >> "$LOG" 2>&1
HITS=/tmp/preprint_hits_${DATE}_${DATE}.json
if [ ! -f "$HITS" ]; then
    step "✗ 抓取未产出 JSON（API 故障？），流水线中止，日志见 $LOG"
    exit 1
fi
step "  命中 JSON：$HITS（$(python3 -c "import json;print(len(json.load(open('$HITS'))))") 条）"

step "2/7 medRxiv 全文抓取（串行 30s）"
python3 scripts/fetch_medrxiv_fulltext.py "$HITS" --sleep 30 >> "$LOG" 2>&1

step "3/7 medRxiv 退避补抓（30/60/120s）"
python3 scripts/fetch_medrxiv_retry.py "$HITS" >> "$LOG" 2>&1

step "4/7 全文完整性定级"
python3 scripts/jats_to_text.py >> "$LOG" 2>&1

step "5/7 重建全文汇总池"
python3 scripts/build_fulltext_summary.py >> "$LOG" 2>&1

step "6/7 生成当日全文级速递页并发布（index/rss 幂等）"
python3 scripts/gen_daily_fulltext.py --date "$DATE" >> "$LOG" 2>&1

step "7/7 重建 sitemap"
python3 scripts/rebuild-sitemap.py >> "$LOG" 2>&1

step "流水线完成。日志：$LOG"
grep -E "完成：|已生成|汇总池|sitemap.xml 重建" "$LOG" || true
