#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给文章页注入 ①上/下篇导航 ②「情报发生日期」时间标签。

为什么单独做成一个注入器而不是改 gen_articles.py
------------------------------------------------
本站的 news/*.html 是**发布物**：由各批次 gen_articles_*.py 一次性写出后入库，
管线（run-pipeline.sh）里并没有 gen_articles.py 这一环——它只从既有 HTML 反向
重建 articles.json。所以「改存量文章页」只能走注入器模式（与 inject-poster /
inject-share-bar 同源），不能指望下次生成时自然带上。

① 上/下篇（待办 P2 #10）
    同专题优先、全站兜底：读者读完一篇，最可能想看的是同一条线索上的下一篇，
    而不是随机跳到别的栏目。同专题缺一侧时回退全站时间序，保证两端永不为空
    （首尾两篇除外，这是事实不是缺陷）。
    顺序约定：**上一篇 = 更早发布，下一篇 = 更新发布**。与列表页的倒序一致。

② 情报发生日期（2026-10-24 晨间验收发现的缺口）
    pre 交付的预印本解读页只有 `<time datetime="2026-10-24">`（**发布日**），
    而研究本身发生在更早（如 10-20 上线的 medRxiv 预印本）。读者看到「10-24」
    会以为是当天冒出来的新研究，与「预印本未经同行评审」的标注也对不上。
    数据源只认 **DOI 内嵌日期**：medRxiv `10.64898/YYYY.MM.DD.N`、
    bioRxiv `10.1101/YYYY.MM.DD.N` 的日期段就是预印本上线日，是 DOI 的一部分，
    不依赖任何外部查询、不会猜错。**解析不出就不显示**——宁可少标，不可错标；
    因此本项只覆盖预印本类文章（约 100 篇），其余保持原样。

自校验（硬门禁）
    生成的每个链接必须先落到磁盘上（`news/<slug>` 存在）才允许注入，
    否则跳过该侧。因为本脚本排在 check-links（管线第 20 步）**之后**运行，
    死链检查器看不到它产出的链接——自检必须自己做，不能把风险留给自己兜不住的人。

幂等：带 `lb-article-nav` / `lb-event-date` 标记；重跑时先摘旧块再注入，
      不会层层叠加。

用法：python3 scripts/inject-article-nav.py [repo_root]
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")

NAV_MARK = "lb-article-nav"
DATE_MARK = "lb-event-date"
STUB_MARK = "lb-redirect-stub"  # 迁移守卫页，与 gen-redirects.py 同名同义

# 只认 DOI 里内嵌日期的两种预印本前缀（medRxiv / bioRxiv）
DOI_DATE = re.compile(r"^10\.(?:64898|1101)/(\d{4})\.(\d{2})\.(\d{2})\.")

CSS = (
    "<style>.article-nav{display:flex;flex-wrap:wrap;gap:12px;margin:26px 0 0;"
    "padding:0;list-style:none}.article-nav a{flex:1 1 260px;display:block;"
    "padding:12px 16px;border:1px solid #e6e8ef;border-radius:10px;"
    "text-decoration:none;color:#111;background:#fbfcfe;font-size:14px;"
    "line-height:1.5;min-height:44px}.article-nav a:hover{border-color:#0f3460;"
    "background:#f4f7fc}.article-nav .nav-dir{display:block;font-size:12px;"
    "color:#777;margin-bottom:4px}.article-nav .nav-newer{text-align:right}"
    "@media(max-width:600px){.article-nav{flex-direction:column}"
    ".article-nav .nav-newer{text-align:left}}</style>"
)

CSS_DATE = (
    "<style>.event-date{display:inline-block;margin-left:10px;font-size:12px;"
    "color:#8a6d3b;background:#fdf6e3;border:1px solid #f0e2c0;border-radius:6px;"
    "padding:2px 8px;vertical-align:middle}</style>"
)


def load_articles():
    path = os.path.join(ROOT, "data", "articles.json")
    with open(path, encoding="utf-8") as fh:
        rows = json.load(fh)
    out = []
    for a in rows:
        slug = (a.get("slug") or "").strip()
        if not slug:
            continue
        disk = os.path.join(ROOT, "news", slug)
        if not os.path.isfile(disk):
            continue  # 已删/未落盘的不进序列，避免造出死链
        out.append(a)
    return out


def sort_key(a):
    # 同日多篇用 slug 兜底，保证排序稳定（否则每次跑结果都漂）
    return (str(a.get("date") or ""), str(a.get("added") or ""), a["slug"])


def build_neighbors(rows):
    """返回 slug -> {'older': slug|None, 'newer': slug|None}"""
    all_rows = sorted(rows, key=sort_key, reverse=True)  # 新 → 旧
    by_topic = {}
    for a in all_rows:
        by_topic.setdefault(a.get("topic") or "", []).append(a)

    nb = {}
    for a in all_rows:
        slug = a["slug"]
        topic = a.get("topic") or ""
        # 同专题优先，缺一侧回退全站
        pool = by_topic.get(topic) or []
        res = {}
        for side, pick_from_topic in (("older", True), ("newer", True)):
            cand = None
            for use_topic in (pick_from_topic, False):
                seq = pool if use_topic else all_rows
                i = next((k for k, r in enumerate(seq) if r["slug"] == slug), None)
                if i is None:
                    continue
                j = i + 1 if side == "older" else i - 1
                if 0 <= j < len(seq) and seq[j]["slug"] != slug:
                    cand = seq[j]
                    break
            res[side] = cand
        nb[slug] = res
    return nb


def nav_block(older, newer):
    items = []
    if older:
        items.append(
            '<li><a class="nav-older" href="/news/%s">'
            '<span class="nav-dir">← 上一篇（更早）</span>%s</a></li>'
            % (older["slug"], esc(older.get("title") or older["slug"]))
        )
    if newer:
        items.append(
            '<li><a class="nav-newer" href="/news/%s">'
            '<span class="nav-dir">下一篇（更新）→</span>%s</a></li>'
            % (newer["slug"], esc(newer.get("title") or newer["slug"]))
        )
    if not items:
        return ""
    return (
        '<nav class="%s" aria-label="上下篇导航"><ul>%s</ul></nav>\n'
        % (NAV_MARK, "".join(items))
    )


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def event_date_of(a, pub_date, html=""):
    """情报发生日期：优先取 DOI 内嵌日期，无 DOI 时退回正文「数据日期」标签。

    2026-10-30 补：产业/监管类稿件（行业周报、午刊快讯）**没有 DOI**，
    原有逻辑只能返回 None，导致这大批条目拿不到机器可读的发生日期——
    而它们恰恰是最需要「事件发生日」与「发布日」分开标注的一类：
    一条 10-21 的 FDA IND 放行，可能 10-30 才随周报上站，
    只标发布日会让读者误判时效。正文里由 gen_articles_* 写下的
    「数据日期 YYYY-MM-DD」正是这个字段的事实源，此处直接复用。
    """
    doi = str(a.get("doi") or "").strip()
    m = DOI_DATE.match(doi)
    if not m:
        m2 = re.search(r"数据日期\s*(\d{4})-(\d{2})-(\d{2})", html or "")
        if not m2:
            return None
        d = "%s-%s-%s" % m2.groups()
    else:
        d = "%s-%s-%s" % m.groups()
    if d == pub_date:
        return None  # 与发布日同日，标注没有信息量
    return d


RE_NAV = re.compile(
    r'<nav class="%s"[^>]*>.*?</nav>\s*' % NAV_MARK, re.S
)
RE_DATE = re.compile(
    # 不吃尾部空白：后面的换行/缩进属于原有排版，删标签时要还给 <h1>
    r'<span class="event-date"[^>]*>.*?</span>', re.S
)


def process(path, nb, by_slug, stats):
    with open(path, encoding="utf-8", errors="ignore") as fh:
        html = fh.read()
    if STUB_MARK in html or "article-header" not in html:
        return False  # 守卫页 / 非文章页不处理

    slug = os.path.basename(path)
    a = by_slug.get(slug)
    out = html
    changed = False

    # —— ① 上/下篇 ——
    old_nav = RE_NAV.search(out)
    if old_nav:
        out = out[: old_nav.start()] + out[old_nav.end():]
        changed = True
    block = ""
    if a and slug in nb:
        block = nav_block(nb[slug].get("older"), nb[slug].get("newer"))
    if block:
        anchor = '<footer class="article-footer">'
        if anchor in out:
            out = out.replace(anchor, block + anchor, 1)
        elif "</article>" in out:
            out = out.replace("</article>", block + "</article>", 1)
        else:
            block = ""
        if block:
            changed = True
            stats["nav"] += 1
    # 未引用 style.css 的页面才内联样式；以选择器为幂等标记，重跑不会叠第二份
    if block and "style.css" not in out and ".article-nav{" not in out \
            and "</head>" in out:
        out = out.replace("</head>", CSS + "\n</head>", 1)

    # —— ② 情报发生日期 ——
    out = RE_DATE.sub("", out)
    CSS_DATE_local = "" if "style.css" in out else CSS_DATE
    ed = event_date_of(a or {}, str((a or {}).get("date") or ""), html)
    if ed:
        # 2026-10-27 修复（待办 P2-18 根治）：此处原为 data-{mark}="1" 硬编码占位值，
        # 导致注入出来的情报发生日期机器不可读（人读文案正确、机器读到 "1"）。
        # 存量 SPA 由 scripts/fix_event_date.py 修复，这里修的是「每轮再生一遍」的源头。
        tag = (
            '<span class="event-date" data-%s="%s">情报发生 %s · 发布于 %s</span>'
            % (DATE_MARK, ed, ed, str((a or {}).get("date") or ""))
        )
        # 分组 2 把 time 后原有的换行/缩进原样带回去，别把 <h1> 挤到同一行
        m = re.search(
            r'(<time datetime="[^"]*"[^>]*>.*?</time>\s*</span>)(\s*)', out, re.S
        )
        if m:
            out = out[: m.end(1)] + tag + m.group(2) + out[m.end(2):]
            changed = True
            stats["date"] += 1
        else:
            m2 = re.search(r'<time datetime="[^"]*"[^>]*>.*?</time>', out, re.S)
            if m2:
                out = out[: m2.end()] + tag + out[m2.end():]
                changed = True
                stats["date"] += 1
    if CSS_DATE_local and "</head>" in out and "event-date{" not in out:
        out = out.replace("</head>", CSS_DATE_local + "\n</head>", 1)

    if not changed:
        return False
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(out)
    return True


def main():
    rows = load_articles()
    by_slug = {a["slug"]: a for a in rows}
    nb = build_neighbors(rows)

    stats = {"nav": 0, "date": 0, "files": 0, "skipped": 0}
    for path in sorted(glob.glob(os.path.join(ROOT, "news", "*.html"))):
        if os.path.basename(path) in ("index.html",):
            continue
        if process(path, nb, by_slug, stats):
            stats["files"] += 1
        else:
            stats["skipped"] += 1

    # 样式落到 style.css（一次性），避免 592 个页面各内联一份
    css_path = os.path.join(ROOT, "style.css")
    if os.path.isfile(css_path):
        with open(css_path, encoding="utf-8") as fh:
            css = fh.read()
        add = ""
        if ".article-nav{" not in css:
            add += CSS.replace("<style>", "").replace("</style>", "") + "\n"
        if ".event-date{" not in css:
            add += CSS_DATE.replace("<style>", "").replace("</style>", "") + "\n"
        if add:
            with open(css_path, "a", encoding="utf-8") as fh:
                fh.write("\n/* 上下篇导航 + 情报发生日期（inject-article-nav.py） */\n" + add)

    print(
        "inject-article-nav: 上下篇 %d 篇 · 情报发生日期 %d 篇 · "
        "改写 %d 个文件 · 未变 %d 个"
        % (stats["nav"], stats["date"], stats["files"], stats["skipped"])
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
