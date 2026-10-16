#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit-traceability.py —— 溯源完整性审计（只报告，不改任何内容）

背景
────
`/about/#editorial-policy` 对读者承诺「**溯源优先 · 每篇文章均标注原始来源
并给出可点击的原始链接**」。这条承诺此前从未被机器核验过——每轮运营靠人手写
一段正则临场统计，于是同一个指标在不同运行里出现过 22 / 151 / 138 三个数，
彼此对不上，谁也说不清到底差在哪、差多少。本脚本把它固化成一条可复现的命令。

口径
────
对 data/articles.json 里每篇文章，读取 news/<slug> 判定三项：
  1. 有无 DOI          —— 与 backfill-doi.py 用同一条 DOI_RE，保证口径一致
  2. 有无可点来源链接  —— 页面里指向站外的 <a href="http(s)://...">
                          （排除本站域名与统计脚本，它们不是来源）
  3. 来源强弱          —— 有 DOI 视为强；只有站外链接视为中；都没有视为断链

只报告，不修改任何文章、不修改 articles.json（除写出本审计报告本身）。
「断链」类不自动补 DOI：slug 关键词检索会返回多个候选，自动挂上去等于猜，
挂错比不挂更伤可信度。补挂需人工或用户对账后执行。

用法：
    python3 scripts/audit-traceability.py [仓库根目录]
    python3 scripts/audit-traceability.py . --suggest      # 额外联网给「断链」篇找 DOI 候选
输出：
    data/traceability-audit.json   （结构化，供后续对账与趋势对比）
    data/doi-candidates.json       （仅 --suggest 时产出，候选清单，**不会自动写入文章**）
退出码：0 = 审计完成（有缺口也返回 0，本脚本只审计不卡管线）
"""
import json
import os
import re
import sys
from collections import Counter

# 与 backfill-doi.py 保持同一条正则，避免两套口径各说各话
DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:a-z0-9<>\[\]+]+", re.I)

# 既不是来源也不是阅读对象的站内/统计域名，统计外链时要剔除
NOT_SOURCE = (
    "longbiosci.com",
    "umami.is",
    "www.longbiosci.com",
)

TIER_ORDER = {"A": 0, "B": 1, "C": 2}


def source_links(html):
    """页面里指向站外、且不是本站/统计的链接（去重保序）"""
    out, seen = [], set()
    for m in re.finditer(r'href="(https?://[^"]+)"', html):
        u = m.group(1)
        if any(d in u for d in NOT_SOURCE):
            continue
        dom = re.sub(r"^https?://", "", u).split("/")[0]
        if dom in seen:
            continue
        seen.add(dom)
        out.append(u)
    return out


def audit(ROOT):
    arts = json.load(open(os.path.join(ROOT, "data/articles.json"), encoding="utf-8"))
    rows = []
    for a in arts:
        p = os.path.join(ROOT, "news", a["slug"])
        if not os.path.exists(p):
            rows.append({"slug": a["slug"], "title": a.get("title", ""),
                         "evidence": a.get("evidence", ""),
                         "page_exists": False, "doi": None,
                         "source_links": [], "level": "缺页"})
            continue
        html = open(p, encoding="utf-8", errors="ignore").read()
        dois = sorted({m.group(0).rstrip(".,;:") for m in DOI_RE.finditer(html)})
        links = source_links(html)
        if dois:
            level = "强"
        elif links:
            level = "中"
        else:
            level = "断链"
        rows.append({"slug": a["slug"], "title": a.get("title", ""),
                     "evidence": a.get("evidence", ""),
                     "page_exists": True,
                     "doi": a.get("doi") or (dois[0] if dois else None),
                     "doi_in_page": bool(dois),
                     "source_links": links,
                     "level": level})
    return arts, rows


def summarize(rows):
    lv = Counter(r["level"] for r in rows)
    by_tier = {}
    for r in rows:
        t = r["evidence"] or "?"
        d = by_tier.setdefault(t, Counter())
        d[r["level"]] += 1
    return {
        "total": len(rows),
        "level_counts": dict(lv),
        "by_tier": {t: dict(c) for t, c in sorted(
            by_tier.items(), key=lambda kv: TIER_ORDER.get(kv[0], 9))},
        "missing_doi": [{"slug": r["slug"], "title": r["title"],
                         "evidence": r["evidence"]}
                        for r in rows if not r.get("doi_in_page")],
        "no_source": [{"slug": r["slug"], "title": r["title"],
                       "evidence": r["evidence"]}
                      for r in rows if r["level"] == "断链"],
    }


def main():
    ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
    SUGGEST = "--suggest" in sys.argv
    arts, rows = audit(ROOT)
    rep = summarize(rows)

    print(f"仓库根目录: {ROOT}")
    print(f"articles.json: {len(arts)} 篇\n")
    print("溯源强度分布：")
    for k in ("强", "中", "断链", "缺页"):
        if k in rep["level_counts"]:
            print(f"  {k:<4} {rep['level_counts'][k]:>4} 篇")
    print("\n按证据分级：")
    print(f"  {'分级':<6}{'强(有DOI)':>12}{'中(仅外链)':>12}{'断链':>8}{'缺页':>8}")
    for t, c in rep["by_tier"].items():
        print(f"  {t:<6}{c.get('强',0):>12}{c.get('中',0):>12}"
              f"{c.get('断链',0):>8}{c.get('缺页',0):>8}")
    print(f"\n页面内无 DOI: {len(rep['missing_doi'])} 篇")
    print(f"无任何可点来源（断链）: {len(rep['no_source'])} 篇  ← 与 /about/ 的溯源承诺直接冲突")

    out = os.path.join(ROOT, "data", "traceability-audit.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"summary": rep, "articles": rows}, f,
                  ensure_ascii=False, indent=1)
    print(f"\n已写出 {out}")

    if SUGGEST:
        suggest(ROOT, [r for r in rows if r["level"] == "断链"])
    return 0


def suggest(ROOT, targets):
    """给「断链」篇联网找 DOI 候选。**只写候选清单，绝不自动写入文章页**。

    依据：文章 slug 是英文关键词串，比中文标题更适合检索。
    候选不自动采纳——同一 slug 常返回多篇同名不同刊的结果，
    采纳与否需人工或用户对账。
    """
    import urllib.parse
    import urllib.request

    print(f"\n联网检索 DOI 候选（{len(targets)} 篇断链）…")
    cands = []
    for r in targets:
        q = re.sub(r"[-_]", " ", re.sub(r"\.html$", "", r["slug"]))
        q = re.sub(r"\b20\d\d\b", "", q).strip()
        url = ("https://www.ebi.ac.uk/europepmc/webservices/rest/search?query="
               + urllib.parse.quote(q) + "&format=json&pageSize=3")
        try:
            with urllib.request.urlopen(url, timeout=25) as fp:
                d = json.load(fp)
        except Exception as e:                       # 网络问题不应让审计失败
            cands.append({"slug": r["slug"], "query": q, "error": str(e)})
            continue
        items = []
        for it in d.get("resultList", {}).get("result", [])[:3]:
            items.append({"doi": it.get("doi"),
                          "title": (it.get("title") or "")[:120],
                          "journal": it.get("journalTitle"),
                          "year": it.get("pubYear")})
        cands.append({"slug": r["slug"], "title": r["title"],
                      "evidence": r["evidence"], "query": q, "candidates": items})
        print(f"  {r['slug'][:52]}")
        for it in items:
            print(f"      {it['doi']} | {(it['title'] or '')[:62]} | {it['journal']} {it['year']}")
    p = os.path.join(ROOT, "data", "doi-candidates.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(cands, f, ensure_ascii=False, indent=1)
    print(f"\n候选清单已写出 {p}（**未写入任何文章页**）")


if __name__ == "__main__":
    sys.exit(main())
