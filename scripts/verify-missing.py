#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify-missing.py —— 对 harvest 判「漏收」的条目做硬核验

为什么必须有这一步
──────────────────
harvest.py 的四路判定各有盲区，输出 confidence=none 时**什么都没证明**：
  · 站内 <title> 是中文译名，英文原标题的 3-gram 相似度恒为 0
  · slug 只保留 3~5 个关键词，长标题的专有名词常被截断
  · 机制词表是人工维护的，新领域必然缺词
所以「四路未命中」既可能是真漏收，也可能是**查重没查到**。
直接把 confidence=none 当漏收去写稿 = 制造重复内容。

本脚本做的是 harvest 没做的那一半：**拿高特异关键词去搜 news/*.html 的全文**，
而不是只比对标题和 slug。命中的条目连证据一起列出，由人做最终判断。

用法
────
  python3 scripts/verify-missing.py <harvest-report.json> [--min 2] [--top 3]

输出：每条候选的站内命中文件（含命中词），未命中的标「站内无痕」。
"""
import glob
import json
import os
import re
import sys

# 领域通用词：命中它们毫无信息量，必须排除在「高特异关键词」之外
GENERIC = {
    "aging", "ageing", "age", "aged", "senescence", "senescent", "longevity",
    "lifespan", "healthspan", "cells", "cell", "tissue", "tissues", "mouse",
    "mice", "human", "study", "model", "models", "associated", "related",
    "reveals", "identifies", "during", "across", "through", "between",
    "using", "based", "novel", "analysis", "profile", "profiling", "role",
    "mechanism", "mechanisms", "disease", "dna", "rna", "gene", "genes",
    "protein", "proteins", "expression", "levels", "effects", "impact",
    "preprint", "biorxiv", "medrxiv", "arxiv", "review", "research",
    "brain", "cognitive", "memory", "adults", "older", "changes", "change",
    "increased", "reduced", "high", "low", "early", "late", "single",
}


def keywords(title):
    """从英文标题里挑高特异词：长度≥5、非通用词、非纯数字"""
    toks = re.findall(r"[a-z][a-z0-9\-]{4,}", (title or "").lower())
    out, seen = [], set()
    for t in toks:
        t = t.strip("-")
        if len(t) < 5 or t in GENERIC or t in seen or t.isdigit():
            continue
        seen.add(t)
        out.append(t)
    return out


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    rep = json.load(open(sys.argv[1], encoding="utf-8"))
    min_hit = 2
    if "--min" in sys.argv:
        min_hit = int(sys.argv[sys.argv.index("--min") + 1])
    top = 3
    if "--top" in sys.argv:
        top = int(sys.argv[sys.argv.index("--top") + 1])

    root = "."
    docs = {}
    for p in sorted(glob.glob(os.path.join(root, "news", "*.html"))):
        b = os.path.basename(p)
        if b == "index.html" or b.startswith("news-"):
            continue
        txt = open(p, encoding="utf-8", errors="ignore").read().lower()
        docs[b] = txt
    print(f"站内文章 {len(docs)} 篇待搜\n")

    for it in rep["items"]:
        title = it.get("title", "")
        # 跳过源产出自己标定的假阳性/说明性条目
        if re.match(r"^(假阳性|与同日并发|口径核对)", title):
            continue
        kws = keywords(title)
        if len(kws) < 2:
            print(f"— 特异词不足，跳过：{title[:70]}")
            continue
        hits = []
        for slug, txt in docs.items():
            got = [k for k in kws if k in txt]
            if len(got) >= min_hit:
                hits.append((len(got), slug, got))
        hits.sort(reverse=True)
        doi = it.get("doi") or "无DOI"
        if hits:
            print(f"⚠️ 疑似已收录  {doi}")
            print(f"   {title[:96]}")
            for n, slug, got in hits[:top]:
                print(f"     → {slug}  命中 {n} 词 {got[:6]}")
        else:
            print(f"✅ 站内无痕（{len(kws)} 特异词）  {doi}")
            print(f"   {title[:96]}")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
