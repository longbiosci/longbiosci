#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
refresh_counts.py —— 全站计数刷新器（幂等，可重复跑当巡检）

背景
----
站内「N 篇」类计数散落在多处，各自硬编码且互不校准，形成用户可直接感知的矛盾：

  · search.html        写 372 篇（4 处）
  · research/index.html 写 374 篇（2 处）
  · 首页「核心概念」6 卡片 72/43/8/8/6/6
  · 8 个概念页自身页标  64/45/7/8/6/5(/6/5)

而后两者还各自与「页面实际收录的文章链接数」对不上（senolytic 标 64 实链 59、
stemcell 标 45 实链 40、melatonin 标 5 实链 3）——原因均为页面在某次去重删稿后
未同步重建。

事实源约定（本脚本确立，后续以此为准）
--------------------------------------
1. 全站总数      = len(data/articles.json)          —— 唯一事实源
2. 概念收录数    = 该概念页 HTML 中实际出现的 /news/ 链接数（去重）
                   理由：概念页的收录清单是人工策展的结果，不存在可复现的关键词
                   规则（实测关键词法与页面清单互有 12 篇漏收 / 17 篇误收），
                   因此「页面实际列了几篇」就是最诚实、可核验的计数。
                   清单本身是否漏收新文章是另一件事，记入待办，不在此伪造补齐。
3. 概念页证据分解 = 按页面实链 slug 回查 articles.json 的 evidence 字段统计

设计原则：**不发明内容、不增删文章**，只把已存在的事实数字写回各处。

用法：
    python3 scripts/refresh_counts.py [仓库根目录] [--dry-run]
退出码：0 = 全部已对齐（或本次已刷新）；1 = 存在无法自动处理的残留
"""
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(".").resolve()
for _a in sys.argv[1:]:
    if not _a.startswith("-"):
        ROOT = Path(_a).resolve()
        break
DRY = "--dry-run" in sys.argv

# 8 个根级概念页（与 scripts/gen-home.py 的 CONCEPTS 保持同一集合）
CONCEPT_PAGES = [
    "senolytic.html", "stemcell.html", "rapamycin.html", "telomere.html",
    "metformin.html", "nmn.html", "spermidine.html", "melatonin.html",
]

# 正文中的 /news/ 链接（相对与绝对两种写法都算，去重后即为该页实收篇数）
NEWS_LINK_RE = re.compile(
    r'href="(?:https://longbiosci\.com)?/news/([^"#?]+\.html)"')
# 概念页四类计数文案
META_N_RE = re.compile(r"本站收录 (\d+) 篇相关研究解读")
H2_N_RE = re.compile(r"<h2>站内相关研究（(\d+) 篇）</h2>")
EVID_RE = re.compile(
    r"共 <strong>(\d+)</strong> 篇相关解读 —— A 级（人体研究）(\d+) "
    r"· B 级（临床前）(\d+) · C 级（预印本）(\d+)")
# 全站总数文案（按站点当前口径）
TOTAL_SPAN_RE = re.compile(r'(<span id="total-count">)(\d+)(</span>)')
TOTAL_N_RE = re.compile(r"(?<!\d)(\d{3}) 篇")
# 任何页面上的「概念卡片」（首页 / research 索引页均有，文案后缀两种：
# 「72 篇 · 选择性清除…」与「64 篇解读」，故只替换数字、保留后缀）
CONCEPT_CARD_RE = re.compile(
    r'(<a href="/(?:' + "|".join(p[:-5] for p in CONCEPT_PAGES) +
    r')\.html"[^>]*class="topic-card"[^>]*>\s*'
    r'<span class="t-name">[^<]*</span>\s*'
    r'<span class="t-count">)(\d+)( 篇[^<]*</span>)', re.S)


def concept_link_count(path):
    """返回该概念页实际收录的 slug 列表（去重、保序）。"""
    html = path.read_text(encoding="utf-8", errors="ignore")
    return list(dict.fromkeys(NEWS_LINK_RE.findall(html)))


def refresh_concept_pages(by_slug, report):
    """回写 8 个概念页自身的计数与证据分解。"""
    for name in CONCEPT_PAGES:
        p = ROOT / name
        if not p.exists():
            report.append(f"  ⚠️ 概念页缺失：{name}")
            continue
        html = p.read_text(encoding="utf-8", errors="ignore")
        slugs = concept_link_count(p)
        n = len(slugs)
        tiers = Counter(by_slug[s]["evidence"] for s in slugs if s in by_slug)
        a, b, c = tiers.get("A", 0), tiers.get("B", 0), tiers.get("C", 0)
        unknown = [s for s in slugs if s not in by_slug]

        new = META_N_RE.sub(f"本站收录 {n} 篇相关研究解读", html)
        new = H2_N_RE.sub(f"<h2>站内相关研究（{n} 篇）</h2>", new)
        new = EVID_RE.sub(
            f"共 <strong>{n}</strong> 篇相关解读 —— A 级（人体研究）{a} "
            f"· B 级（临床前）{b} · C 级（预印本）{c}", new)
        if new == html:
            report.append(f"  {name:<16} {n:>3} 篇（A{a}/B{b}/C{c}）· 已对齐")
            continue
        if not DRY:
            p.write_text(new, encoding="utf-8", newline="")
        report.append(
            f"  {name:<16} {n:>3} 篇（A{a}/B{b}/C{c}）· 已刷新"
            + (f"  ⚠️ {len(unknown)} 条链接不在 articles.json" if unknown else ""))


def refresh_concept_cards(counts, report):
    """把全站任何页面上指向概念页的卡片计数刷成概念页实数。"""
    changed = 0
    for p in sorted(ROOT.rglob("*.html")):
        if ".git" in p.parts:
            continue
        html = p.read_text(encoding="utf-8", errors="ignore")
        bad = []

        def repl(m):
            slug = re.search(r'href="/([^"]+\.html)"', m.group(1)).group(1)[:-5]
            n = counts[slug]
            if int(m.group(2)) != n:
                bad.append(f"{slug} {m.group(2)}→{n}")
            return m.group(1) + str(n) + m.group(3)

        new = CONCEPT_CARD_RE.sub(repl, html)
        if new == html:
            continue
        changed += 1
        if not DRY:
            p.write_text(new, encoding="utf-8", newline="")
        report.append(f"  {str(p.relative_to(ROOT)):<24} · " + "；".join(bad))
    if not changed:
        report.append("  概念卡片计数已全部对齐")


def refresh_total_pages(total, report):
    """把写死的全站总数刷成 articles.json 实数。"""
    # search.html：372 → total（含 <span id="total-count">）
    p = ROOT / "search.html"
    if p.exists():
        html = p.read_text(encoding="utf-8", errors="ignore")
        new = TOTAL_SPAN_RE.sub(lambda m: m.group(1) + str(total) + m.group(3), html)
        new = TOTAL_N_RE.sub(lambda m: str(total) + " 篇", new)
        if new != html:
            if not DRY:
                p.write_text(new, encoding="utf-8", newline="")
            report.append(f"  search.html          → {total} 篇 · 已刷新")
        else:
            report.append(f"  search.html          {total} 篇 · 已对齐")
    else:
        report.append("  ⚠️ search.html 缺失")

    # research/index.html：374 → total
    p = ROOT / "research" / "index.html"
    if p.exists():
        html = p.read_text(encoding="utf-8", errors="ignore")
        new = TOTAL_N_RE.sub(lambda m: str(total) + " 篇", html)
        if new != html:
            if not DRY:
                p.write_text(new, encoding="utf-8", newline="")
            report.append(f"  research/index.html  → {total} 篇 · 已刷新")
        else:
            report.append(f"  research/index.html  {total} 篇 · 已对齐")
    else:
        report.append("  ⚠️ research/index.html 缺失")


def main():
    aj = ROOT / "data" / "articles.json"
    if not aj.exists():
        print(f"找不到 {aj}", file=sys.stderr)
        return 1
    articles = json.loads(aj.read_text(encoding="utf-8"))
    by_slug = {a["slug"]: a for a in articles}
    total = len(articles)

    print(f"仓库根目录: {ROOT}")
    print(f"articles.json: {total} 篇（全站总数唯一事实源）")
    print(("  [DRY-RUN] 不写盘\n" if DRY else "\n") + "概念页：")
    report = []
    refresh_concept_pages(by_slug, report)
    print("\n".join(report))
    # 首页「核心概念」卡片（72/43/8/8/6/6）与 research 索引页卡片同源于概念页
    report = []
    refresh_concept_cards({n[:-5]: len(concept_link_count(ROOT / n))
                           for n in CONCEPT_PAGES}, report)
    print("\n概念卡片（全站扫描）：")
    print("\n".join(report))
    print("\n全站总数页：")
    report = []
    refresh_total_pages(total, report)
    print("\n".join(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
