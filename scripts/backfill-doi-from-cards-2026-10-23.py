#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
backfill-doi-from-cards-2026-10-23.py —— 用 10-23 五刊卡片 DOI 回填站内缺 DOI 页面

背景（摄入巡检第 11 轮对账发现）
──────────────────────────────
ledger audit 的词元重叠路径把 5 个 10-23 卡片条目判为「已收录」。
人工逐条核验后：
  · N02（10.1038/s43587-026-01220-0，微黄奈瑟菌）→ 站内
    Oral-Microbiome-Neisseria-flavescens-Geroprotective-NatureAging-2026.html
    确为同论文（Nature Aging 2026-09-24，北大韩敬东团队，AURORA），
    但页面无 DOI，且 nature.com 链接后缀错标为 s43587-026-01010-1；
  · N03（10.1038/s43587-026-01227-7，心磷脂-ERRγ）→ 站内
    Cardiolipin-ERRgamma-Muscle-Fiber-Switch-Nature-Aging-2026.html
    确为同论文（哥本哈根 Finger/Gerhart-Hines 团队），页面无 DOI；
  · A27/A28/G14 为误配（不同论文或仅同主题综述页），计真漏收，不回填。

回填动作（每篇）：
  1. data/articles.json 补 doi 字段；
  2. data/doi-index.json 补 doi→slug 映射（修 DOI 查重盲区）；
  3. 页面 <p class="source"> 行补「，DOI: …」，Oral-Microbiome 页
     另修正 nature.com 链接后缀（01010-1 → 01220-0）。
"""
import json
import re
import sys

ROOT = "/workspace/repo"

# (slug, doi, journal, fix_href_suffix or None)
TARGETS = [
    ("Oral-Microbiome-Neisseria-flavescens-Geroprotective-NatureAging-2026.html",
     "10.1038/s43587-026-01220-0", "Nature Aging", "s43587-026-01010-1"),
    ("Cardiolipin-ERRgamma-Muscle-Fiber-Switch-Nature-Aging-2026.html",
     "10.1038/s43587-026-01227-7", "Nature Aging", None),
]

def main():
    arts_path = f"{ROOT}/data/articles.json"
    arts = json.load(open(arts_path, encoding="utf-8"))
    alist = arts["articles"] if isinstance(arts, dict) else arts

    idx_path = f"{ROOT}/data/doi-index.json"
    idx = json.load(open(idx_path, encoding="utf-8"))

    changed = []
    for slug, doi, journal, bad_suffix in TARGETS:
        # 1) articles.json
        hit = [a for a in alist if slug in str(a.get("slug") or a.get("file") or a.get("url") or "")]
        if not hit:
            sys.exit(f"✗ articles.json 找不到 {slug}")
        a = hit[0]
        if a.get("doi"):
            print(f"· {slug[:50]} 已有 DOI {a['doi']}，跳过")
            continue
        a["doi"] = doi
        # 2) doi-index.json
        if doi.lower() not in idx:
            idx[doi.lower()] = slug
        # 3) HTML 来源行
        p = f"{ROOT}/news/{slug}"
        t = open(p, encoding="utf-8").read()
        if bad_suffix:
            good = f"https://www.nature.com/articles/{doi.split('/', 1)[1]}"
            t = t.replace(f"https://www.nature.com/{bad_suffix}", good)
        # 在期刊名后的（）内补 DOI（若无）
        if f"DOI: {doi}" not in t:
            t2 = re.sub(
                r"(<a href=\"https://[^\"]*\"[^>]*>" + journal + r"</a>)（([0-9\-]+)）",
                r"\1（\2，DOI: " + doi + r"）",
                t, count=1)
            if t2 == t:
                sys.exit(f"✗ {slug} 来源行未匹配到「{journal}（日期）」模式")
            t = t2
        open(p, "w", encoding="utf-8").write(t)
        changed.append((slug, doi))

    json.dump(arts, open(arts_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(idx, open(idx_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"✅ 回填 {len(changed)} 篇：")
    for slug, doi in changed:
        print(f"   {slug[:58]} ← {doi}")

if __name__ == "__main__":
    main()
