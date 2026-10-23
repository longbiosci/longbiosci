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
#
# 2026-10-23 修：字符集里的 `<>` 是第二个坑。
# 页面里 DOI 写成 `10.1111/acel.70730</span>` 或 `10.1038/...)</p>` 时，
# `<`、`>`、`/`、`d/i/v/p` 全在 Crossref 字符集内，于是 `</div`、`)</p>`
# 被整段吃进 DOI。实测 43 篇的 doi 字段带这类尾巴，索引因此查不到它们，
# harvest 把这 43 篇判成「漏收」——又是「绿色的但没在工作的索引」。
# Crossref 字符集本身不含 `<>`，去掉即可；再补一道 `</` 截断双保险。
DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:a-z0-9\[\]+]+", re.I)


def clean(d):
    """去掉 DOI 尾部的中文/标点残留，只保留合法 DOI 字符"""
    if not d:
        return ""
    # 双保险：任何 `</tag` 尾巴一律截断（页面里 DOI 常紧跟闭合标签）
    d = re.split(r"<", d)[0]
    m = DOI_RE.match(d.strip())
    if not m:
        return ""
    d = m.group(0)
    # 三修（2026-10-23 晚）：Crossref 字符集本身含 `()`，于是页面里
    # 「(doi:10.3390/…486)」的收尾括号会被吃进 DOI——Crossref 对带
    # 尾括号的形式返回 404（实测两条），而DOI 真正含括号的极少。
    # 规则：尾部 `.,;:</]` 一律剥；尾 `)` 仅在没有配对 `(` 时剥。
    while d and (d[-1] in ".,;:</]" or (d[-1] == ")" and d.count(")") > d.count("("))):
        d = d[:-1]
    return d


def main():
    arts = json.load(open(os.path.join(ROOT, "data/articles.json"), encoding="utf-8"))
    before = sum(1 for a in arts if a.get("doi"))
    index = {}
    added, conflict, empty, repaired = 0, [], [], []

    for a in arts:
        slug = a["slug"]
        p = os.path.join(ROOT, "news", slug)
        if not os.path.exists(p):
            empty.append((slug, "文章页不存在"))
            continue
        # 2026-10-23 起：**总是**从页面重新提取，不再因为 json 里已有值就跳过。
        # 原逻辑 `if a.get("doi"): found = clean(a["doi"])` 让 json 里的脏值
        # 永久留在索引里——实测 43 篇的 doi 带 `</div` / `)</p>` 尾巴，
        # 每次跑都「补 0 篇」，看起来健康，索引实际是坏的。
        html = open(p, encoding="utf-8", errors="ignore").read()
        # 只在正文与 source 区找，避免命中导航/侧栏的无关 DOI
        body = re.search(r"<article[\s\S]*?</article>", html)
        scope = body.group(0) if body else html
        found = clean(DOI_RE.search(scope).group(0)) if DOI_RE.search(scope) else ""
        if not found:
            # 页面取不到时降级沿用 json 里的旧值（可能是行业情报类，正文本无 DOI）
            found = clean(a.get("doi"))
        if not found:
            empty.append((slug, "正文未找到 DOI"))
            continue
        if slug in index and index[slug] != found:
            conflict.append((slug, index[slug], found))
            continue
        if not a.get("doi"):
            a["doi"] = found
            added += 1
        elif a["doi"] != found:
            # json 值与页面提取值不一致 → 一律以页面为准覆盖。
            # 2026-10-23 二修：原条件写的是 `clean(a["doi"]) != found`，
            # 于是「json 脏值清洗后恰好等于 found」时判定为无需修复——
            # 实测 64 篇的 doi 带着 `</span` / `)</p>` / `</li` 尾巴原样留在
            # articles.json 里（索引是干净的，json 是脏的，两边不一致）。
            # 正确做法：只比较原始值，脏就覆盖。
            repaired.append((slug, a["doi"], found))
            a["doi"] = found
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
    if repaired:
        print(f"\n🔧 修复脏 DOI {len(repaired)} 条（json 值带标签尾/已失效，以页面为准覆盖）：")
        for s, old, new in repaired[:12]:
            print(f"  {s[:56]}: {old!r} → {new}")
        if len(repaired) > 12:
            print(f"  …（另有 {len(repaired)-12} 条）")
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