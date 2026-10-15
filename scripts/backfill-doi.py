#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
backfill-doi.py —— 给站内文章补全DOI 索引（防漏基建）

问题
────
站内 411 篇文章里，有 141 篇（34%）正文没有暴露任何 DOI。
后果：查重最可靠的那一路（DOI 精确匹配）对这141 篇**完全失效**——
产出里明明有它们的 DOI，站内也明明有这篇文章，判定却是「漏收」。
实测 2026-10-15 补建台账时，187 条产出里一度判出 164 条「漏收」，
其中绝大多数是这类假漏收。

做法
────
1. 从每篇 news/*.html 的正文与source 区正则提取 DOI（取第一个）
2. 写回 data/articles.json 的 doi 字段（**只增字段，不改其他任何内容**）
3. 生成 data/doi-index.json：DOI → slug，供harvest.py 直接查表

不做的事
────────
不改正文、不改标题、不改任何既有字段值。纯增量。
无法提取 DOI 的文章保持为空，并在报告里列出——它们只能靠机制词与人工核对。
"""
import glob
import json
import os
import re
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
# 只允许 Crossref 认可的 DOI 字符集。曾经用 [^…]+ 贪婪匹配，把
# 「10.1016/j.ymthe.2026.05.025）·研究：MIT」整段当成 DOI 写进索引，
# 导致站内自己建的索引就是脏的、DOI 精确匹配对站内自己失效。
DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:a-z0-9<>\[\]+]+", re.I)


def clean(d):
    """去掉 DOI 尾部的中文/标点残留，只保留合法 DOI 字符"""
    m = DOI_RE.match((d or "").strip())
    return m.group(0).rstrip(".,;:</a>") if m else ""


def main():
    arts = json.load(open(os.path.join(ROOT, "data/articles.json"), encoding="utf-8"))
    before = sum(1 for a in arts if a.get("doi"))
    index = {}
    added, conflict, empty = 0, [], []

    for a in arts:
        slug = a["slug"]
        p = os.path.join(ROOT, "news", slug)
        if not os.path.exists(p):
            empty.append((slug, "文章页不存在"))
            continue
        found = None
        if a.get("doi"):
            found = clean(a["doi"])
        else:
            html = open(p, encoding="utf-8", errors="ignore").read()
            # 只在正文与 source 区找，避免命中导航/侧栏的无关 DOI
            body = re.search(r"<article[\s\S]*?</article>", html)
            scope = body.group(0) if body else html
            m = DOI_RE.search(scope)
            if m:
                found = clean(m.group(0))
        if not found:
            empty.append((slug, "正文未找到 DOI"))
            continue
        if slug in index and index[slug] != found:
            conflict.append((slug, index[slug], found))
            continue
        if not a.get("doi"):
            a["doi"] = found
            added += 1
        index[slug] = found

    arts.sort(key=lambda a: (a.get("date", ""), a.get("slug", "")), reverse=True)
    json.dump(arts, open(os.path.join(ROOT, "data/articles.json"), "w",
                        encoding="utf-8"), ensure_ascii=False, indent=2)

    doi_index = {v: k for k, v in sorted(index.items())}
    json.dump(doi_index, open(os.path.join(ROOT, "data/doi-index.json"), "w",
                              encoding="utf-8"), ensure_ascii=False, indent=1)

    print(f"articles.json: {len(arts)} 篇 | 原已有 DOI {before} 篇 | 本次补入 {added} 篇")
    print(f"doi-index.json: {len(doi_index)} 条 DOI → slug 映射")
    print(f"仍无 DOI：{len(empty)} 篇（{len(empty)/len(arts)*100:.0f}%）"
          f" —— 这些只能靠机制词与人工核对")
    if conflict:
        print(f"\n⚠️ slug 与 DOI 冲突 {len(conflict)} 处（未改动，取先出现的）：")
        for s, a_, b_ in conflict[:10]:
            print(f"  {s}: {a_} vs {b_}")
    if empty:
        print("\n无 DOI 文章（供人工判断是否需要补记）：")
        for s, why in empty[:15]:
            print(f"  {s[:62]}  ({why})")


if __name__ == "__main__":
    main()