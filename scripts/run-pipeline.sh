#!/usr/bin/env bash
# ============================================================
# run-pipeline.sh —— LongBiosci 本地管线一键运行器（v1.3）
#
# 用法：
#   ./run-pipeline.sh [仓库根目录] [--date YYYY-MM-DD] [--now "YYYY-MM-DD HH:MM:SS"]
#
#   root   仓库根目录，默认当前目录
#   --date / --now  透传给 add-rss-today-run.py（仅用于确定性复现；
#                   日常运行不要传，脚本会自动取当天 UTC 日期与当前时刻）
#
# 依次执行 20 个环节（顺序与 .github/workflows/regen-index.yml 注释记载一致）：
#   1 build-index.py        从 news/*.html 重建 data/articles.json（追加式）
#   2 sync-evidence.py      把 news/*.html 的分级回写 articles.json（--write；治回退顽疾）
#   3 gen-home.py           生成 index.html
#   4 gen-topic-pages.py    生成 topics/ 8 个专题页 + 12 个分页页 + 索引页
#   5 gen-news-index.py     生成 news/index.html 与 news-2..N.html 分页
#   6 gen-evidence-pages.py 生成 evidence/ 索引页 + A/B/C 分级列表（含分页）
#   7 gen-industry.py       生成产业板块：事件流 / 公司档案 / 会议日历
#   8 gen-podcast.py        生成播客列表页 + podcast.xml RSS
#   9 gen-papers.py         生成 /papers/ 论文索引（DOI 总表 + papers.csv）
#  10 add-rss-today-run.py  把当日新文章追加进 rss.xml（无新增则幂等不变）
#  11 inject-poster.py      给文章页注入 /poster.js（已有则跳过）
#  12 normalize_nav.py      全站主导航归一化（--apply）
#  13 sync-search-index.py  重建 data/search-index.json 并刷新 search.html 计数
#  14 refresh_counts.py     把各处「N 篇」计数回写为事实源（幂等；本环节自愈）
#  15 audit-traceability.py 溯源完整性审计（只报告不阻断，产出 data/traceability-audit.json）
#  16 fix_related.py        死链修复：按 data/redirects.json 重定向 + 去重 + 补位（幂等）
#  17 gen-redirects.py      为已删/更名 URL 生成「页面已迁移」守卫页（外链不再 404）
#  18 rebuild-sitemap.py    重建 sitemap.xml（**必须在所有改页环节之后**，见下方注释）
#  19 check-links.py --self-test  检查器自检：用反例页证明各判定真的会报错
#  20 check-links.py        全站死链 + 计数一致性 + canonical 硬校验（末位，不通过则失败）
#
# ⚠️ 编号变更（2026-10-23）：两处改动，均当天完成、一次性同步。
#    ① 新增第 9 环节 gen-papers.py（/papers/ 论文索引），原 9~19 顺延为 10~20；
#    ② sitemap 重建从第 10 位后移到第 18 位（所有改页环节之后），
#       原 10~18 各自前移一位。**本节以下的历史注释写于改号之前**，其中的环节号
#       （如「环节 9 自动回写」实指现在的 14 refresh_counts）按旧号理解；
#       只有「环节 17/18/19/20」四段是新号。改号比改文案安全——
#       凭记忆重写历史注释，比留一个明确的「本文按旧号」提示更容易出错。
#
# 环节 19 为什么必须存在（2026-10-22 新增）
# ----------------------------------------
# 「输出里没有红色」从来不等于「检查被执行了」。本仓库已四次栽在这件事上：
#   ① 首页计数只认「共 N 篇」，而首页写的是「全站 N 篇」→ 正则失配静默跳过
#   ② canonical 自指判定把绝对 URL 塞给只接受 / 开头的 url_to_disk → 恒 None，
#      整个分支从未进入（分支内还藏着一个未定义变量 tpath，两者互相掩护）
#   ③ 迁移页三条约束沿用了 ② 的失效路径
#   ④ page_self_url() 对已相对的路径再做一次 relpath → cwd != ROOT 时算垃圾
# 四次都是「绿色的、但没在工作的检查」。环节 19 在真正检查之前，
# 先造 8 个已知好坏的页面，断言「该报的必须报、不该报的必须不报」，
# 任一条不符就 exit 1 —— 检查器自己先被检查，它的输出才可信。
# 放在 20 之前而非之后：自检失败时不必再跑一遍全量扫描，直接停。
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
# 环节 7/8 为什么必须放在 9（sitemap）之前（2026-10-19 产业 + 2026-10-19 播客）
# ----------------------------------------------------------------
# 产业板块四页此前是纯静态遗留页，无数据源、无生成器，各页面各写各的
# （companies 曾写 14 家、investors 3 位、events 7 场会议无来源），
# 2026-10-18 重建为 data/industry.json 事件流驱动；播客同理——
# podcast/index.html 与 podcast.xml 必须先生成，sitemap 才能收录 /podcast/。
# 且并行批次合并（远端 4b09568）曾整段丢掉产业文件，接入管线后每次构建
# 都会重新产出四页，从机制上防止「板块悄悄消失」。
#
# 环节 8 为什么不合成音频
# ----------------------
# 音频是发布物不是构建物：文稿定稿后由 scripts/synth_podcast_audio.py
# 手动合成一次入 git（TTS 走外部端点，无 SLA，进管线会被网络波动阻断）。
# gen-podcast.py 只生成页面与 RSS，并硬校验音频文件存在。
#
# 环节 9 为什么放在校验之前（2026-10-16 新增）
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
# 环节 10 为什么只报告不阻断（2026-10-16 新增）
# -------------------------------------------
# 溯源审计量的是「每篇有没有 DOI / 有没有可点来源」，对照 /about/ 的溯源承诺。
# 现状有缺口（约 138 篇无 DOI、十余篇彻底无来源），但缺口是**历史存量**，
# 不是本次管线跑出来的新伤——让它硬失败等于拿历史问题卡住今天的内容摄入。
# 故只报告、退出码恒 0，把数字固化成 data/traceability-audit.json 供趋势对比；
# 等缺口收敛到可接受水平后再考虑升级为硬校验。
#
# ⚠️ 旧版警告（2026-10-23 已解除，留此存证）
#    「不要在 GitHub Actions 里跑：checkout 会重置全部文件 mtime，
#      导致非文章页 lastmod 全量漂移到 checkout 当天。」
#    该风险已由 rebuild-sitemap.py 改为**内容指纹**判定后消除：lastmod 现在只在
#    页面内容真的变化时才前移，与 mtime / checkout 时刻无关。线上 sitemap 里
#    残留的 86 条 2026-10-23 就是旧逻辑被 CI 污染的痕迹（不改写，避免又一次全站跳变）。
#    管线仍建议在本地跑：只有本地才有 data/fulltext/ 与 .intake/ 这类不入库的材料。
#
# 管线只管「站内一致性」，不管「产出消化」——后者由 cursor.py + 内容摄入巡检任务负责。
#
# 环节 17 为什么必须排在 16 之后、18 之前（2026-10-22 新增，2026-10-23 改号）
# ---------------------------------------------------
# 三个环节读的都是同一份 data/redirects.json，但服务对象不同：
#   16 fix_related    —— 把**站内**链接从旧 slug 改指保留版本，读者不必绕跳转页
#   17 gen-redirects  —— 为**站外**流量生成守卫页，旧 URL 不再 404 且传导外链权重
#   19/20 check-links —— 19 自检（先证明检查器活着），20 才是全量硬校验，
#                        含守卫页的 canonical/refresh 一致性
# 顺序反了会出两件事：守卫页先进 sitemap 前却没被校验（sitemap 只收
# articles.json 登记项，故守卫页不进 sitemap，这里无妨）；更关键的是
# 守卫页必须先存在，check-links 才能验证它——否则 39 条守卫页的
# 「canonical 指向保留版本 + refresh 一致」约束无人把关，
# 而这段约束恰恰最容易被后来者改坏（见 check-links 的 STUB_MARK 说明）。
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
  printf '\n[%s/20] %-22s %s\n' "$n" "$script" "$desc"
  case "$script" in
    add-rss-today-run.py) "$PYTHON" "$HERE/$script" "$ROOT" "$@" ;;
    sync-evidence.py)     "$PYTHON" "$HERE/$script" "$ROOT" --write ;;
    # gen-home 前先补「收录日」字段（build-index 重建 articles.json 不保留新增字段）
    gen-home.py)          "$PYTHON" "$HERE/backfill-added.py" "$ROOT" && "$PYTHON" "$HERE/$script" "$ROOT" ;;
    normalize_nav.py)     "$PYTHON" "$HERE/$script" "$ROOT" --apply ;;
    # fix_related.py 自己按 __file__ 推导仓库根，不接受位置参数
    fix_related.py)       "$PYTHON" "$HERE/$script" "$@" ;;
    # check-links 有两种模式：带 --self-test 是自检，不带是全量校验
    check-links.py)       "$PYTHON" "$HERE/$script" "$ROOT" "$@" ;;
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
step 8  gen-podcast.py         "生成播客：节目列表页 + podcast.xml RSS"
step 9  gen-papers.py          "生成 /papers/ 论文索引（DOI 总表 + CSV）"
step 10 add-rss-today-run.py   "追加当日新文章到 rss.xml"
step 11 inject-poster.py       "注入海报脚本 /poster.js"
step 12 normalize_nav.py       "全站主导航归一化（--apply）"
step 13 sync-search-index.py   "重建站内搜索索引与计数"
step 14 refresh_counts.py      "各处「N 篇」计数回写事实源（幂等）"
step 15 audit-traceability.py  "溯源完整性审计（只报告，不阻断）"
step 16 fix_related.py         "死链修复（重定向 / 去重 / 补位，幂等）"
step 17 gen-redirects.py       "已删 URL 的迁移守卫页（外链不再 404，传导权重）"
step 18 rebuild-sitemap.py     "重建 sitemap.xml（在全部改页环节之后）"
step 19 check-links.py         "检查器自检：反例探针证明各判定真的会报错" --self-test
step 20 check-links.py         "全站死链 + 计数一致性 + canonical 硬校验（末位）"

# 末位守卫：补转发分享条（防 step16 fix_related 等重写 news 冲掉；幂等，已含 share-bar 跳过）
echo "[末尾守卫] inject-share-bar      补文章页转发分享条（复制链接 + 二维码）"
"$PYTHON" "$HERE/inject-share-bar.py" "$ROOT"

# 末位守卫 2：文章页上/下篇导航 + 情报发生日期（2026-10-24 新增，待办 P2 #10）
#   同样排在末尾，理由与 share-bar 一致：step16 fix_related 会重写 news 正文区。
#   它排在 check-links（20）之后，所以链接可达性由**脚本自己**硬校验
#   （目标文件不存在就不注入该侧），不把死链风险留给看不见它的检查器。
echo "[末尾守卫] inject-article-nav   补文章页上下篇导航 + 情报发生日期"
"$PYTHON" "$HERE/inject-article-nav.py" "$ROOT"

printf "\n✅ 管线执行完成（20/20）· 末位两条守卫已补（分享条 + 上下篇/发生日期）\n"
