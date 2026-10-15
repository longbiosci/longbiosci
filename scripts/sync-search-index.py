#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync-search-index.py —— 重建 data/search-index.json 并刷新 search.html 计数（v1.0）

为什么需要它：
  - data/search-index.json 原先只由已废弃的 gen_site.py 生成，
    7 阶段管线不覆盖它，导致新文章站内搜索不到（计数长期停在 380）。
  - search.html 里的 meta description / og:description / 正文计数是硬编码数字，
    每次加稿都会变成过期计数，与footer 的「共 N 篇」矛盾。

职责：
  1. 以 data/articles.json 为唯一事实源，重建全部 news 条目；
     保留非 news 的栏目页条目（/search.html、/trials/等）并置顶在前。
  2. 把 search.html 中的 {N} 占位符替换为真实篇数（幂等，可反复运行）。

用法：python3 scripts/sync-search-index.py [ROOT]
"""
import json
import os
import re
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."


def rebuild_index(articles, si_path):
    """保留旧的非 news 条目（栏目页），news 条目按 articles.json 顺序重建"""
    other = []
    if os.path.exists(si_path):
        try:
            old = json.load(open(si_path, encoding="utf-8"))
            other = [r for r in old if not (isinstance(r, list) and r
                     and isinstance(r[1], str) and r[1].startswith("/news/"))]
        except Exception:
            other = []

    news = [
        [a.get("title", ""), f"/news/{a['slug']}", a.get("date", ""),
         str(a.get("tag", "")), str(a.get("topic", "")),
         str(a.get("evidence", "")), str(a.get("desc", ""))]
        for a in articles
    ]
    merged = news + other
    with open(si_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False)
    return len(news), len(other)


def refresh_search_html(root, total):
    """把 search.html 的 {N} 占位符替换为真实篇数；兼容已替换过的旧版本"""
    p = os.path.join(root, "search.html")
    if not os.path.exists(p):
        print("  search.html 不存在，跳过")
        return False
    s = open(p, encoding="utf-8").read()
    orig = s
    s = s.replace("{N}", str(total))
    # 兼容历史硬编码：把「全部 <任意数字> 篇」「total-count">任意数字< 」统一为真实值
    s = re.sub(r'(全部 )\d+( 篇)', rf"\g<1>{total}\g<2>", s)
    s = re.sub(r'(<span id="total-count">)\d+(</span>)', rf"\g<1>{total}\g<2>", s)
    if s != orig:
        with open(p, "w", encoding="utf-8", newline="") as f:
            f.write(s)
        return True
    return False


def main():
    ap = os.path.join(ROOT, "data/articles.json")
    sp = os.path.join(ROOT, "data/search-index.json")
    articles = json.load(open(ap, encoding="utf-8"))

    n_news, n_other = rebuild_index(articles, sp)
    changed = refresh_search_html(ROOT, len(articles))
    print(f"search-index.json: news {n_news} 条 + 栏目页 {n_other} 条 = {n_news + n_other} 条")
    print(f"search.html: {'已刷新计数' if changed else '计数已是最新'}（{len(articles)} 篇）")


if __name__ == "__main__":
    main()