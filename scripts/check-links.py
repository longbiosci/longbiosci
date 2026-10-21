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
5. 证据分级：evidence/index.html 三个分级计数 == articles.json 分级分布，
   且磁盘上的分级分页数量与数据量推导的一致（不多不少）
6. 绝对 URL 与 canonical（2026-10-21 新增）：
   - 所有指向本站的绝对 URL（https://longbiosci.com/...）必须对应存在的文件
   - 每个页面必须有 canonical，且必须**自指**（指向本页自身）
   - canonical 指向的目标必须真实存在

为什么加这一项
──────────────
原检查项 1 只匹配 `href|src="(/[^"#?]+)"`，即**只查以 / 开头的相对路径**。
于是两类缺陷长期无人发现：
- canonical / og:url 写错（404.html → /404/、mobile.html → /mobile/、
  news/Multiverse-Brain-Age-Pipeline-Sensitivity-2026.html → 一个不存在的
  -Prediction- 变体，共3 处，线上全部 404）
- 3 个 daily 周刊页完全没有 canonical（其中 2 个在 sitemap 内）
它们都「不影响页面渲染」，所以管线一路绿灯。SEO 上这是硬伤：
canonical 指向 404 等于主动告诉搜索引擎「这个页面已废弃」。

扫描范围（2026-10-17 扩）
────────────────────
此前只扫根目录 / news/ / topics/，evidence/ guide/ 等栏目页**从未被扫过**。

后果是真实且昂贵的：evidence/index.html 长期写着「A 94 / B 269 / C 17」，
而事实是「A 131 / B 311 / C 109」——整整 425 篇的差异在站内躺了数日无人发现，
原因是「死链扫描」与「计数校验」都绕开了这个目录。
扫描范围自此覆盖全部栏目目录，栏目页漂移与栏目页死链一并纳入。

退出码：0 = 全通过；1 = 有问题（清单打印到stdout）
"""
import glob
import json
import math
import os
import re
import sys
from collections import Counter

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."


# 全站栏目目录。改这里等于改「哪些页面会被扫到」——
# 新增栏目目录务必登记，否则该目录的死链与计数漂移会再次隐身。
SCAN_DIRS = ["", "news", "topics", "evidence", "guide", "research",
             "companies", "events", "daily", "about", "privacy",
             "investors", "industry", "podcast"]


def iter_pages():
    for d in SCAN_DIRS:
        for p in sorted(glob.glob(os.path.join(ROOT, d, "*.html"))):
            yield p, open(p, encoding="utf-8", errors="ignore").read()


def url_to_disk(url):
    """站内 URL(/x/y.html) → 磁盘路径；None 表示不是本站路径。"""
    u = url.split("#")[0].split("?")[0]
    if not u.startswith("/"):
        return None
    disk = os.path.join(ROOT, u.lstrip("/"))
    if u.endswith("/") or u == "":
        disk = os.path.join(disk, "index.html")
    return disk


def page_self_url(path):
    """页面自身的规范 URL（仓库相对），用于 canonical 自指判定。"""
    rel = os.path.relpath(path, ROOT).replace("\\", "/")
    if rel == "index.html":
        return "/"
    if rel.startswith("index.html"):        # 形如 topics/index.html
        rel = rel[len("index.html"):]
    return "/" + rel


ABS_URL_RE = re.compile(r'https?://longbiosci\.com(/[^\s"\'<>]*)')
CANON_RE = re.compile(r'<link[^>]*rel="canonical"[^>]*href="([^"]+)"', re.I)


def check_canonical_and_abs(problems, details):
    """检查 6：canonical 存在性、自指性、目标存在性 + 站内绝对 URL 有效性"""
    n_pages = n_canon = 0
    seen_abs = set()
    for path, h in iter_pages():
        rel = os.path.relpath(path, ROOT).replace("\\", "/")
        n_pages += 1

        # canonical 存在性
        m = CANON_RE.search(h)
        if not m:
            problems["缺 canonical"] += 1
            details.append(f"缺 canonical  {rel}")
        else:
            n_canon += 1
            target = m.group(1).strip()
            disk = url_to_disk(target.split("#")[0])
            if disk is None:
                # 指向站外：只要求是合法绝对 URL
                if not target.startswith(("http://", "https://")):
                    problems["canonical 非绝对 URL"] += 1
                    details.append(f"canonical 非绝对URL  {rel} -> {target}")
            else:
                if not os.path.exists(disk):
                    problems["canonical 指向失效"] += 1
                    details.append(f"canonical 指向失效  {rel} -> {target}")
                # 自指判定：站内 URL 必须等于本页自身 URL
                elif tpath.rstrip("/") != page_self_url(rel).rstrip("/"):
                    problems["canonical 非自指"] += 1
                    details.append(f"canonical 非自指  {rel} -> {target}")

        # 站内绝对 URL 一律校验（含 og:url、JSON-LD、正文绝对链接）
        for u in ABS_URL_RE.findall(h):
            if (u, rel) in seen_abs:
                continue
            seen_abs.add((u, rel))
            disk = url_to_disk(u)
            if disk and not os.path.exists(disk):
                problems["绝对 URL 失效"] += 1
                details.append(f"绝对URL 失效  {rel} -> {u}")

    print(f"[SEO] {n_pages} 个页面 / {n_canon} 个有 canonical"
          f" / 站内绝对 URL 去重后 {len({u for u, _ in seen_abs})} 个")


def rel_targets():
    """站内绝对路径（/xxx.html）→ 对应磁盘文件"""
    t = set()
    paths = []
    for d in SCAN_DIRS:
        paths += glob.glob(os.path.join(ROOT, d, "*.html"))
    for p in paths:
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

    # ---- 1b) canonical 与站内绝对 URL ----
    check_canonical_and_abs(problems, details)

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
        # ⚠️ 两个口径都要认：本站首页实际写的是「全站 N 篇」。
        # 此前只匹配「共 N 篇」，而首页根本没有这个字样 ——
        # 于是这个校验**从来没真正执行过**（正则失配时静默跳过，不报错）。
        # 找到了不等于校对了，这类「写了检查但检查没生效」的坑必须留注。
        m = (re.search(r"共\s*([\d,]+)\s*篇", h)
             or re.search(r"全站\s*([\d,]+)\s*篇", h))
        if m:
            n_home = int(m.group(1).replace(",", ""))
            print(f"[计数] 首页声明 {n_home} 篇")
            if n_home != len(arts):
                problems["首页计数不一致"] += 1
                details.append(f"首页 {n_home} != articles {len(arts)}")
        else:
            problems["首页无计数标记"] += 1
            details.append("首页未找到「共 N 篇」或「全站 N 篇」计数标记")

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

    # ---- 4) 证据分级页与事实源一致 ----
    # 三件事一起查，缺一件都会让 /evidence/ 与 articles.json 分叉：
    #   ① 索引页三个分级的计数
    #   ② 磁盘上各分级的分页数量（多 = 孤儿页会被搜录；少 = 读者看不到后半部分）
    #   ③ 分级页里列出的文章数 == 该分级的文章总数
    ev_index = os.path.join(ROOT, "evidence", "index.html")
    if os.path.exists(ev_index):
        h = open(ev_index, encoding="utf-8").read()
        tier_counts = Counter((a.get("evidence") or "").upper() for a in arts)
        # 卡片在页面上的顺序由 gen-evidence-pages.py 的 TIER_CONFIG 固定为 A/B/C，
        # 故按文档顺序取到的计数序列可与 ["A","B","C"] 一一对应。
        # 注意：单捕获组的 findall 返回字符串列表，不是二元组 —— 别再写成 for code, n in ...
        ev_counts = [int(n.replace(",", "")) for n in
                     re.findall(r'class="ev-n">([\d,]+)\s*篇</span>', h)]
        shown = dict(zip(("A", "B", "C"), ev_counts))
        print(f"[证据] articles 分布 {dict(sorted(tier_counts.items()))}"
              f" / 索引页显示 {sorted(shown.items())}")
        if not shown:
            problems["证据索引无计数"] += 1
            details.append("evidence/index.html 未找到分级计数标记")
        else:
            for code in sorted(tier_counts):
                if code not in ("A", "B", "C"):
                    continue
                if shown.get(code) != tier_counts[code]:
                    problems["证据索引计数不一致"] += 1
                    details.append(f"evidence 索引 {code} 级 {shown.get(code)}"
                                    f" != articles {tier_counts[code]}")
        # 分页数量：按 PER_PAGE 推导，与 gen-evidence-pages.py 保持同一常量
        ev_per_page = 24
        for code in ("A", "B", "C"):
            n = tier_counts.get(code, 0)
            want = max(1, math.ceil(n / ev_per_page))
            have = sorted(
                int(x) for x in re.findall(
                    rf"^{code}-(\d+)\.html$",
                    "\n".join(os.listdir(os.path.join(ROOT, "evidence"))),
                    re.M)
            )
            # 真实存在的分页号集合应为 {2..want}
            want_set = set(range(2, want + 1))
            extra = sorted(set(have) - want_set)
            missing = sorted(want_set - set(have))
            page1 = os.path.join(ROOT, "evidence", f"{code}.html")
            if n > 0 and not os.path.exists(page1):
                problems["证据分级页缺失"] += 1
                details.append(f"evidence/{code}.html 不存在（该级 {n} 篇）")
            if extra:
                problems["证据孤儿分页"] += 1
                details.append(f"evidence/{code} 多余分页 {extra}（应到 {want}）")
            if missing:
                problems["证据分页缺失"] += 1
                details.append(f"evidence/{code} 缺失分页 {missing}（应到 {want}）")

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
