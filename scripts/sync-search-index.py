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


def refresh_other_descs(other, total):
    """把栏目页条目描述里写死的旧篇数刷新为当前 total。

    2026-10-21 修复：/search.html 的描述「374 篇解读的全文检索」是历史硬编码，
    rebuild_index 原样保留旧条目的 desc，于是 articles.json 涨到 570 篇后，
    搜索页面上**搜索框下方那句**仍写着 374 篇——而同一页的 total-count 已是 570，
    同一页面自相矛盾。此处按「数字 + 篇」的模式统一回写，使其可自愈。
    """
    fixed = 0
    pat = re.compile(r"(\d+)(\s*篇)")
    out = []
    for r in other:
        if isinstance(r, list) and len(r) >= 7 and isinstance(r[6], str) \
                and re.search(r"\d+\s*篇", r[6]):
            new = pat.sub(f"{total}\\g<2>", r[6])
            if new != r[6]:
                r = list(r)
                r[6] = new
                fixed += 1
        out.append(r)
    return out, fixed


def entry_exists(root, url):
    """站点 URL → 磁盘路径并判断是否存在。

    2026-10-23 新增。非 news 的栏目页条目是**从旧基线整体继承**的，
    此前无条件保留，于是 "/papers/" 这种「承诺过但从未建过」的条目
    会一直留在索引里，读者搜到点进去就是 404。这里让条目必须对得上真实文件。
    """
    u = str(url).split("#")[0].split("?")[0]
    if not u.startswith("/"):
        return True                       # 站外条目不在本判据范围
    disk = os.path.join(root, u.lstrip("/"))
    if u.endswith("/") or u in ("", "/"):
        disk = os.path.join(disk, "index.html")
    return os.path.exists(disk)


def prune_other(other, root):
    """剔除指向不存在页面的栏目页条目，返回 (保留项, 被剔除 URL 列表)。"""
    kept, dropped = [], []
    for r in other:
        if isinstance(r, list) and len(r) > 1 and isinstance(r[1], str) \
                and not entry_exists(root, r[1]):
            dropped.append(r[1])
            continue
        kept.append(r)
    return kept, dropped


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

    root = os.path.dirname(os.path.dirname(os.path.abspath(si_path)))
    other, dropped = prune_other(other, root)

    news = [
        [a.get("title", ""), f"/news/{a['slug']}", a.get("date", ""),
         str(a.get("tag", "")), str(a.get("topic", "")),
         str(a.get("evidence", "")), str(a.get("desc", ""))]
        for a in articles
    ]
    other, n_desc = refresh_other_descs(other, len(news))
    merged = news + other
    with open(si_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False)
    return len(news), len(other), n_desc, dropped


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

    n_news, n_other, n_desc, dropped = rebuild_index(articles, sp)
    changed = refresh_search_html(ROOT, len(articles))
    print(f"search-index.json: news {n_news} 条 + 栏目页 {n_other} 条 = {n_news + n_other} 条"
          + (f"（已刷新 {n_desc} 条栏目描述里的过期篇数）" if n_desc else ""))
    if dropped:
        # 剔除必须吼一声：这些条目背后是「曾被承诺、现已没有页面」的 URL，
        # 静默删掉等于把「页面没了」这个事实藏起来。
        print("  ⚠️ 剔除指向不存在页面的栏目页条目：" + "、".join(dropped))
    print(f"search.html: {'已刷新计数' if changed else '计数已是最新'}（{len(articles)} 篇）")


if __name__ == "__main__":
    main()