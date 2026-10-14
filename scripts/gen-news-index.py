#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen-news-index.py —— 新闻列表页生成器（逆向重写版 v1.0）

复刻来源：线上 news/index.html + news-2..news-13.html（2026-10-14 基线）
规则（自 13 个页面与 git HEAD 逐字节比对得出）：
  - 数据源：data/articles.json（380 篇，date 倒序 + 同日 slug 字母序）
  - 每页 30 篇；总页数 = ceil(total/30)；首页 = news/index.html，
    第 N 页（N>=2）= news-N.html
  - 首页特有：filter-bar（按主题浏览）、sub-text（共 N 篇 — 查看第 2 页，位于 pager 之后）
  - hero 文案：首页「全部 N 篇研究解读，按时间倒序。每篇标注证据分级——同行评议
    人体研究、临床前研究或预印本。」；归档页「共 N 篇，本页第 X–Y 篇」（en dash）
  - pager 三态：首页只有 next；中间页 prev+next（第 2 页 prev 指向 /news/）；
    末页只有 prev
  - feed-item：tag 为空时显示 topic 值（兜底）；desc 按原文截断 150 字符加 …
    （先截断后转义，实证 16+3 篇）；title/desc 走 html.escape(quote=True)
  - feed 区闭合：</div>\n</div>\n（item 尾 + 容器尾，换行分隔）
  - footer 计数「共 N 篇」随总数刷新
  - 不重生 news-14.html（10-13 去重后的过期遗留页，391 旧计数，留待办跟踪去留）
  页面骨架模板自 git HEAD 版本逐字节提取（news_page_templates.json 同源生成）。
"""
import html
import json
import math
import os
import sys

PER_PAGE = 30
DESC_MAX = 150  # feed-desc 截断长度（原文字符数，先截断后转义，超出加 …）

# ---- 页面骨架（提取自 git HEAD:news-2.html，变量区已参数化）----
PAGE_HEAD = '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n<title>{title}</title>\n<meta name="description" content="{description}">\n<link rel="canonical" href="{canonical}">\n<meta name="robots" content="index, follow">\n<meta property="og:type" content="website">\n<meta property="og:url" content="{canonical}">\n<meta property="og:title" content="{title}">\n<meta property="og:description" content="{description}">\n<meta property="og:image" content="https://longbiosci.com/og-image.png">\n<meta property="og:site_name" content="LongBiosci">\n<meta name="twitter:card" content="summary_large_image">\n<meta name="twitter:title" content="{title}">\n<meta name="twitter:description" content="{description}">\n<link rel="alternate" type="application/rss+xml" title="LongBiosci RSS" href="/rss.xml">\n<link rel="icon" type="image/svg+xml" href="/favicon.svg">\n<link rel="stylesheet" href="/style.css">\n</head>\n<body>\n<a href="#main-content" class="skip-link">跳转到主要内容</a>\n<header class="site-header">\n  <div class="wrap">\n    <a href="/" class="brand"><img src="/logo-mark.svg" alt="" class="brand-mark" width="28" height="28"><span class="brand-name">LongBiosci</span></a>\n    <nav class="main-nav" aria-label="主导航">\n      <a href="/">首页</a>\n      <a href="/news/" aria-current="page">最新</a>\n      <a href="/topics/">主题专辑</a><a href="/research/">概念与工具</a><a href="/daily/">周刊</a>\n      <a href="/evidence/">证据分级</a>\n      <a href="/search.html">搜索</a>\n      <a href="/trials.html">临床试验</a>\n      <a href="/about/">关于</a>\n    </nav>\n  </div>\n</header>\n<main id="main-content">\n<section class="hero"><div class="wrap">\n<h1>{h1}</h1>\n<p>{hero_p}</p>\n</div></section>\n<section class="section"><div class="wrap">\n'

FEED_OPEN = '<div class="feed">\n'

PAGE_TAIL = '</div></section>\n</main><footer class="site-footer">\n  <div class="wrap">\n    <p>© 2026 LongBiosci · 衰老与长寿科技资讯 · 共 {total} 篇</p>\n    <a href="/rss.xml">RSS</a> · <a href="/sitemap.xml">Sitemap</a> · <a href="/about/">关于</a>\n  </div>\n</footer>\n</body>\n</html>\n'

FILTER_BAR = '<div class="filter-bar">\n<span class="filter-label">按主题浏览：</span>\n<a href="/topics/">全部主题</a>\n<a href="/evidence/A.html">A 级人体研究</a>\n<a href="/evidence/B.html">B 级临床前</a>\n<a href="/evidence/C.html">C 级预印本</a>\n<a href="/search.html">站内搜索</a>\n</div>\n'

SUB_TEXT = '<p class="sub-text" style="text-align:center;margin-top:1rem">共 380 篇 — <a href="/news-2.html">查看第 2 页 →</a></p>\n'

FEED_ITEM = """<div class="feed-item">
<div class="item-meta">
<span class="tag">{tag}</span>
<span class="tier tier-{tier}">{tier}</span>
<span class="tag-date">{date}</span>
<span>{topic}</span>
</div>
<div class="feed-title"><a href="/news/{slug}">{title}</a></div>
<p class="feed-desc">{desc}</p>
</div>"""


def esc(s):
    return html.escape(s or "", quote=True)


def render_page(articles, page, total_pages):
    total = len(articles)
    is_first = page == 1
    if is_first:
        title = "最新收录 - LongBiosci"
        description = "全部抗衰老与长寿科技研究解读，按时间倒序，每篇标注证据分级。"
        canonical = "https://longbiosci.com/news/"
        h1 = "最新收录"
        start, end = 1, min(PER_PAGE, total)
        hero_p = (f"全部 {total} 篇研究解读，按时间倒序。每篇标注证据分级——"
                  "同行评议人体研究、临床前研究或预印本。")
    else:
        title = f"最新收录 第 {page} 页 - LongBiosci"
        description = f"全部抗衰老与长寿科技研究解读，第 {page} 页。"
        canonical = f"https://longbiosci.com/news-{page}.html"
        h1 = f"最新收录 · 第 {page} 页"
        start = (page - 1) * PER_PAGE + 1
        end = min(page * PER_PAGE, total)
        hero_p = f"共 {total} 篇，本页第 {start}–{end} 篇"

    head = (PAGE_HEAD
            .replace("{title}", esc(title))
            .replace("{description}", esc(description))
            .replace("{canonical}", canonical)
            .replace("{h1}", esc(h1))
            .replace("{hero_p}", esc(hero_p)))

    # feed 区
    items = []
    for a in articles[(page - 1) * PER_PAGE: page * PER_PAGE]:
        desc = a["desc"]
        if len(desc) > DESC_MAX:
            desc = desc[:DESC_MAX] + "…"
        items.append(FEED_ITEM.format(
            tag=esc(a["tag"] or a["topic"]),
            tier=esc(a["evidence"]),
            date=esc(a["date"]),
            topic=esc(a["topic"]),
            slug=a["slug"],
            title=esc(a["title"]),
            desc=esc(desc),
        ))
    middle = ""
    if is_first:
        middle += FILTER_BAR
    middle += FEED_OPEN + "\n".join(items) + "\n</div>\n"

    # pager 三态
    pager_info = f'<span class="pager-info">第 {page} / {total_pages} 页</span>'
    prev_link = ('<a href="/news/" rel="prev">← 上一页</a>' if page == 2
                 else f'<a href="/news-{page-1}.html" rel="prev">← 上一页</a>')
    next_link = f'<a href="/news-{page+1}.html" rel="next">下一页 →</a>'
    if is_first:
        pager = f'<nav class="pager" aria-label="分页">{pager_info}{next_link}</nav>\n'
    elif page == total_pages:
        pager = f'<nav class="pager" aria-label="分页">{prev_link}{pager_info}</nav>\n'
    else:
        pager = f'<nav class="pager" aria-label="分页">{prev_link}{pager_info}{next_link}</nav>\n'

    tail = PAGE_TAIL.replace("{total}", str(total))

    out = head + middle + pager
    if is_first and total_pages > 1:
        out += SUB_TEXT.replace("{total}", str(total))
    out += tail
    return out


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    with open(os.path.join(root, "data/articles.json"), encoding="utf-8") as f:
        articles = json.load(f)
    total = len(articles)
    total_pages = max(1, math.ceil(total / PER_PAGE))

    for page in range(1, total_pages + 1):
        out = os.path.join(root, "news/index.html" if page == 1 else f"news-{page}.html")
        with open(out, "w", encoding="utf-8", newline="") as f:
            f.write(render_page(articles, page, total_pages))
        print(f"  {os.path.relpath(out, root)}: 第 {page}/{total_pages} 页")

    print(f"新闻列表页生成完成: {total_pages} 页 / {total} 篇")


if __name__ == "__main__":
    main()
