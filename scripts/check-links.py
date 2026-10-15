#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check-links.py —— 全站死链与计数一致性检查（管线第 9 步）

为什么必须有这一步
────────────────
2026-10-15 补写文章时，手写正文里的一个 `/news/xxx.html` 链接少写了作者名
（`Protein-Diet-Longevity-Cell-Review` 漏了 `-Lamming-`），生成时无感、
管线无感、推送无感，直到手工扫全站才发现。

**只要检查不自动化，遗漏就会重演。** 这一步把「死链」和「计数不一致」
变成管线级别的硬失败，而不是靠人眼。

检查项
──────
1. 内部链接：所有 href="/xxx.html" 指向的文件必须存在
2. 内部资源：/style.css /poster.js /logo-mark.svg 等必须存在
3. 计数一致：articles.json / search-index.json / sitemap.xml / 首页 / 搜索页
4. 产出纪律：news/ 下 HTML 文件数与 articles.json 条目数必须相等

退出码：0 = 全通过；1 = 有问题（清单打印到stdout）
"""
import glob
import json
import os
import re
import sys
from collections import Counter

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."


def rel_targets():
    """站内绝对路径（/xxx.html）→ 对应磁盘文件"""
    t = set()
    for p in (glob.glob(os.path.join(ROOT, "*.html"))
              + glob.glob(os.path.join(ROOT, "news", "*.html"))
              + glob.glob(os.path.join(ROOT, "topics", "*.html"))):
        h = open(p, encoding="utf-8", errors="ignore").read()
        for m in re.findall(r'(?:href|src)="(/[^"#?]+)"', h):
            t.add(m)
    return t


def main():
    problems = Counter()
    details = []

    # ---- 1) 内部链接与资源 ----
    checked = 0
    for t in sorted(rel_targets()):
        if t.startswith("//"):
            continue
        checked += 1
        disk = os.path.join(ROOT, t.lstrip("/"))
        if t.endswith("/"):                      # 目录链接：看有没有 index.html
            disk = os.path.join(disk, "index.html")
        if not os.path.exists(disk):
            problems["死链"] += 1
            details.append(f"死链  {t}")
    print(f"[链接] 检查 {checked} 个站内绝对路径引用")

    # ---- 2) articles.json 与 news/ 文件数一致 ----
    # news/ 下有一批刻意的「页面已迁移」占位页（旧 URL 保留以防外链失效），
    # 它们不是文章，不参与计数。
    MIGRATED = "页面已迁移"
    arts = json.load(open(os.path.join(ROOT, "data/articles.json"), encoding="utf-8"))
    files, migrated = [], 0
    for p in glob.glob(os.path.join(ROOT, "news", "*.html")):
        base = os.path.basename(p)
        if base.startswith("news-") or base == "index.html":
            continue
        head = open(p, encoding="utf-8", errors="ignore").read(2000)
        if MIGRATED in head:
            migrated += 1
            continue
        files.append(p)
    print(f"[计数] articles.json {len(arts)} 条 / news/ 文章文件 {len(files)} 个"
          f"（另有 {migrated} 个迁移占位页，不计入）")
    if len(arts) != len(files):
        problems["计数不一致"] += 1
        only_a = {a["slug"] for a in arts} - {os.path.basename(p) for p in files}
        only_f = {os.path.basename(p) for p in files} - {a["slug"] for a in arts}
        details.append(f"计数不一致 articles={len(arts)} files={len(files)}"
                       + (f" 仅在 articles: {sorted(only_a)[:3]}" if only_a else "")
                       + (f" 仅在磁盘: {sorted(only_f)[:3]}" if only_f else ""))

    # ---- 3) 搜索索引 / sitemap / 首页 / 搜索页计数 ----
    si_path = os.path.join(ROOT, "data/search-index.json")
    n_index = 0
    if os.path.exists(si_path):
        si = json.load(open(si_path, encoding="utf-8"))
        n_index = sum(1 for r in si if isinstance(r, list) and len(r) > 1
                      and str(r[1]).startswith("/news/"))
        print(f"[计数] search-index {n_index} 条 news")
        if n_index != len(arts):
            problems["搜索索引不一致"] += 1
            details.append(f"search-index {n_index} != articles {len(arts)}")

    sm = os.path.join(ROOT, "sitemap.xml")
    if os.path.exists(sm):
        n_url = open(sm, encoding="utf-8").read().count("<loc>")
        print(f"[计数] sitemap {n_url} 条 URL")
        # sitemap 含栏目页等非文章 URL，只要求不少于文章数
        if n_url < len(arts):
            problems["sitemap 偏少"] += 1
            details.append(f"sitemap {n_url} < articles {len(arts)}")

    home = os.path.join(ROOT, "index.html")
    if os.path.exists(home):
        h = open(home, encoding="utf-8").read()
        m = re.search(r"共\s*([\d,]+)\s*篇", h)
        if m:
            n_home = int(m.group(1).replace(",", ""))
            print(f"[计数] 首页声明 {n_home} 篇")
            if n_home != len(arts):
                problems["首页计数不一致"] += 1
                details.append(f"首页 {n_home} != articles {len(arts)}")

    search = os.path.join(ROOT, "search.html")
    if os.path.exists(search):
        h = open(search, encoding="utf-8").read()
        m = re.search(r'id="total-count"[^>]*>([\d,]+)', h)
        if m:
            n = int(m.group(1).replace(",", ""))
            print(f"[计数] 搜索页声明 {n} 篇")
            if n != len(arts):
                problems["搜索页计数不一致"] += 1
                details.append(f"搜索页 {n} != articles {len(arts)}")

    # ---- 汇总 ----
    print()
    if not problems:
        print("✅ 检查通过：死链 0 · 计数全一致")
        return 0
    print(f"❌ 发现 {sum(problems.values())} 类问题：{dict(problems)}")
    for d in details[:30]:
        print("   " + d)
    return 1


if __name__ == "__main__":
    sys.exit(main())
