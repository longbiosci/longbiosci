#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen-evidence-pages.py —— 证据分级页生成器（管线第 6 环节）

用法：python3 scripts/gen-evidence-pages.py <仓库根目录>

为什么要有这个生成器
──────────────────
`evidence/*.html` 此前是**纯静态遗留页**，没有任何管线脚本负责它们。后果是：
2026-10-17 把 PROMETHEUS 方案的分级从 C 更正为 A 之后，`evidence/index.html`
仍写着"A 94 篇 / B 269 篇 / C 17 篇"，而 `data/articles.json` 的事实是
"A 131 / B 311 / C 109"；三个分页还各只列 25 / 25 / 18 条，
**读者在 /evidence/ 上永远看不到 B 级的另外 286 篇**。

根因不是"数字写错了"，而是**这些页面不在任何生成器的管辖范围内** ——
改一次就漂一次，且 `check-links.py` 当时只扫根目录 /news/ /topics/，
连扫都没扫到 evidence/，所以漂了也没人知道。

本脚本把 `/evidence/` 索引页与 A / B / C 三个分级列表（含分页）全部改为
**由 data/articles.json 生成**，从此分级一变，页面自动跟随。

幂等：可反复运行，产物由数据唯一决定。
"""
import html
import json
import math
import os
import sys

PER_PAGE = 24          # 与 topics 分页保持一致，避免两个栏目每页条数不同
DESC_MAX = 150         # 列表摘要截断长度

# 分级配置：(代码, 页面标题, 页面描述, 「如何解读这一层级」正文)
TIER_CONFIG = [
    ("A",
     "同行评议人体研究",
     "已在同行评议期刊发表的人体研究，包括随机对照试验、队列分析与临床试验中期数据。这是本站证据等级中可信度最高的一类。",
     "需注意：即使是 A 级人体研究，样本量与随访时长仍可能不足以支撑强结论。涉及企业发布的中期数据时，本站会在正文中另行标注。"),
    ("B",
     "同行评议临床前研究",
     "已发表但限于动物模型或体外实验的研究。机制描述清晰、可信度高，但结论尚不能外推至人体。",
     "⚠️ 临床前证据不等于人体效果。小鼠与人类在寿命跨度、代谢机制与疾病谱上差异巨大，动物实验中的寿命延长在人类语境下没有直接对应换算。"),
    ("C",
     "预印本（未经同行评议）",
     "发布在 bioRxiv、medRxiv 等预印本平台的论文，尚未经过同行评议。此类结论可能随审稿意见而改变，仅供领域跟踪参考。",
     "⚠️ 本站对所有预印本内容均显式标注「未经同行评议」。预印本不应作为决策依据，引用时须注明其未同行评议的状态。"),
]

HEAD = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} - LongBiosci</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="https://longbiosci.com/evidence/{page_slug}.html">
<meta name="robots" content="index, follow">
<meta property="og:type" content="website">
<meta property="og:url" content="https://longbiosci.com/evidence/{page_slug}.html">
<meta property="og:title" content="{title} - LongBiosci">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="https://longbiosci.com/og-image.png">
<meta property="og:site_name" content="LongBiosci">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title} - LongBiosci">
<meta name="twitter:description" content="{desc}">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="stylesheet" href="/style.css">
</head>
'''

BODY_HEADER = '''<body>
<a href="#main-content" class="skip-link">跳转到主要内容</a>
<header class="site-header">
  <div class="wrap">
    <a href="/" class="brand"><img src="/logo-mark.svg" alt="" class="brand-mark" width="28" height="28"><span class="brand-name">LongBiosci</span></a>
    <nav class="main-nav" aria-label="主导航">
      <a href="/">首页</a>
      <a href="/news/">最新</a>
      <a href="/topics/" aria-label="主题专辑"><span class="nav-mq">主题</span>专辑</a>
      <a href="/guide/" aria-label="热词专题">热词<span class="nav-mq">专题</span></a>
      <a href="/research/" aria-label="概念与工具">概念<span class="nav-mq">与工具</span></a>
      <a href="/daily/">周刊</a>
      <a href="/evidence/" aria-label="证据分级">证据<span class="nav-mq">分级</span></a>
      <a href="/trials.html" aria-label="临床试验">临床<span class="nav-mq">试验</span></a>
      <a href="/industry/">产业</a>
      <a href="/about/">关于</a>
      <a href="/search.html" class="nav-search" aria-label="站内搜索"><svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true" focusable="false"><circle cx="6.8" cy="6.8" r="4.6" fill="none" stroke="currentColor" stroke-width="1.6"/><line x1="10.3" y1="10.3" x2="14" y2="14" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg><span class="nav-search-text">搜索</span></a>
    </nav>
  </div>
</header>
'''

HERO_P1 = '''<main id="main-content">
<section class="hero"><div class="wrap">
<div class="item-meta" style="margin-bottom:.5rem">
<span class="ev-tier ev-{lc}" style="width:2rem;height:2rem;display:inline-flex;align-items:center;justify-content:center;border-radius:var(--r-md);font-weight:700">{code}</span>
<span style="font-size:var(--f-sm);color:var(--c-muted)">共 {count} 篇</span>
</div>
<h1>{title}</h1>
<p>{desc}</p>
</div></section>
'''

HERO_PN = '''<main id="main-content">
<section class="hero"><div class="wrap">
<h1>{title}</h1>
<p>{desc}</p>
</div></section>
'''

SECTION_OPEN = '''<section class="section"><div class="wrap">
<div class="notice-box"><p><strong>如何解读这一层级</strong></p><p>{notice}</p></div>
<div class="section-head"><h2>全部文章{h2_suffix}</h2><a href="/evidence/" class="section-more">← 返回分级说明</a></div>
'''

FEED_OPEN = '<div class="feed">\n'

FEED_ITEM = '''<div class="feed-item">
<div class="item-meta">
<span class="tag">{tag}</span>
<span class="tier tier-{tier}">{tier}</span>
<span class="tag-date">{date}</span>
<span>{topic}</span>
</div>
<div class="feed-title"><a href="/news/{slug}">{title}</a></div>
<p class="feed-desc">{desc}</p>
</div>'''

SUB_TEXT = ('<p class="sub-text" style="text-align:center;margin-top:1.5rem">'
            '共 {total} 篇，已分 {pages} 页 — '
            '<a href="/evidence/{slug}-2.html">继续浏览 →</a></p>\n')

SECTION_CLOSE = '</div></section>\n'

FOOTER = '''</main><footer class="site-footer">
  <div class="wrap">
    <p>© 2026 LongBiosci · 衰老与长寿科技资讯</p>
    <a href="/rss.xml">RSS</a> · <a href="/sitemap.xml">Sitemap</a> · <a href="/about/">关于</a>
  </div>
</footer>
</body>
</html>
'''

# ---- evidence/index.html 专用模板 ----
INDEX_HEAD = HEAD.replace("证据分级说明占位", "")

INDEX_HERO = '''<main id="main-content">
<section class="hero"><div class="wrap">
<h1>证据分级</h1>
<p>本站对每一篇研究解读标注证据强度。这不是形式——它决定了你能否把一条信息当作结论使用。</p>
</div></section>
<section class="section"><div class="wrap">
<div class="ev-grid">
'''

INDEX_CARD = '''<a href="/evidence/{code}.html" class="ev-card">
<div class="ev-head">
<span class="ev-tier ev-{lc}">{code}</span>
<h3>{title}</h3>
</div>
<p>{desc}</p>
<span class="ev-n">{count} 篇</span>
</a>'''

INDEX_TAIL = '''</div>
<div class="notice-box" style="margin-top:2rem">
<p><strong>为什么坚持做分级</strong></p>
<p>衰老领域的营销话术与真实进展混杂在一起。一个"逆转衰老"的标题，可能来自 3 名受试者的一期临床，也可能来自分子通路层面的体外实验。把证据等级标出来，是为了让读者在读第一段时就知道该多信它。</p>
</div>
</div></section>
'''


def esc(s):
    return html.escape(s or "", quote=True)


def trunc(s, n=DESC_MAX):
    s = s or ""
    return s[:n] + "…" if len(s) > n else s


def feed_item(a):
    return FEED_ITEM.format(
        tag=esc(a.get("tag") or a.get("topic")),
        tier=esc(a.get("evidence")),
        date=esc(a.get("date")),
        topic=esc(a.get("topic")),
        slug=a["slug"],
        title=esc(a.get("title")),
        desc=esc(trunc(a.get("desc"), DESC_MAX)),
    )


def pager(code, page, total_pages):
    """三态分页；单页时不输出。"""
    if total_pages <= 1:
        return ""
    info = f'<span class="pager-info">第 {page} / {total_pages} 页</span>'
    prev_href = (f"/evidence/{code}.html" if page == 2
                 else f"/evidence/{code}-{page - 1}.html")
    prev_link = f'<a href="{prev_href}" rel="prev">← 上一页</a>'
    next_link = f'<a href="/evidence/{code}-{page + 1}.html" rel="next">下一页 →</a>'
    if page == 1:
        body = info + next_link
    elif page == total_pages:
        body = prev_link + info
    else:
        body = prev_link + info + next_link
    return f'<nav class="pager" aria-label="分页">{body}</nav>'


def render_tier_pages(code, title, desc, notice, articles):
    """生成一个分级的全部分页。返回 [(相对路径, html), ...]"""
    total = len(articles)
    total_pages = max(1, math.ceil(total / PER_PAGE))
    lc = code.lower()
    for page in range(1, total_pages + 1):
        page_slug = code if page == 1 else f"{code}-{page}"
        head = HEAD.format(title=esc(title), desc=esc(desc), page_slug=page_slug)
        if page == 1:
            hero = HERO_P1.format(code=code, lc=lc, count=total,
                                  title=esc(title), desc=esc(desc))
            h2_suffix = ""
        else:
            hero = HERO_PN.format(title=esc(title), desc=esc(desc))
            h2_suffix = f" · 第 {page} 页"
        items = articles[(page - 1) * PER_PAGE: page * PER_PAGE]
        pg = pager(code, page, total_pages)
        out = (head + BODY_HEADER + hero
               + SECTION_OPEN.format(notice=notice, h2_suffix=h2_suffix)
               + pg + FEED_OPEN
               + "\n".join(feed_item(a) for a in items)
               + "\n</div>" + pg + "\n")
        if page == 1 and total_pages > 1:
            out += SUB_TEXT.format(total=total, pages=total_pages, slug=code)
        out += SECTION_CLOSE + FOOTER
        dst = (f"evidence/{code}.html" if page == 1
               else f"evidence/{code}-{page}.html")
        yield dst, out
    return total_pages


def render_index_page(articles):
    cards = []
    for code, title, desc, _notice in TIER_CONFIG:
        count = sum(1 for a in articles if (a.get("evidence") or "").upper() == code)
        cards.append(INDEX_CARD.format(code=code, lc=code.lower(),
                                       title=esc(title), desc=esc(desc),
                                       count=count))
    head = HEAD.format(title="证据分级",
                       desc="LongBiosci 证据分级标准与全部文章索引",
                       page_slug="")
    head = head.replace('<link rel="canonical" href="https://longbiosci.com/evidence/.html">',
                        '<link rel="canonical" href="https://longbiosci.com/evidence/">')
    head = head.replace('<meta property="og:url" content="https://longbiosci.com/evidence/.html">',
                        '<meta property="og:url" content="https://longbiosci.com/evidence/">')
    return head + BODY_HEADER + INDEX_HERO + "\n".join(cards) + "\n" + INDEX_TAIL + FOOTER


def cleanup_orphans(keep):
    """删除不再存在的分级分页（例如分级数变少后残留的旧分页）。"""
    removed = []
    if not os.path.isdir("evidence"):
        return removed
    for name in sorted(os.listdir("evidence")):
        if name == "index.html" or not name.endswith(".html"):
            continue
        if name not in keep:
            os.remove(os.path.join("evidence", name))
            removed.append(name)
    return removed


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    os.chdir(root)

    with open("data/articles.json", encoding="utf-8") as f:
        articles = json.load(f)

    os.makedirs("evidence", exist_ok=True)
    keep = set()
    counts = {}

    for code, title, desc, notice in TIER_CONFIG:
        sel = [a for a in articles if (a.get("evidence") or "").upper() == code]
        sel.sort(key=lambda a: (a.get("date", ""), a.get("slug", "")), reverse=True)
        counts[code] = len(sel)
        for dst, out in render_tier_pages(code, title, desc, notice, sel):
            with open(dst, "w", encoding="utf-8", newline="") as f:
                f.write(out)
            keep.add(os.path.basename(dst))
        pages = max(1, math.ceil(len(sel) / PER_PAGE))
        print(f"  evidence/{code}.html: {len(sel)} 篇 / {pages} 页")

    with open("evidence/index.html", "w", encoding="utf-8", newline="") as f:
        f.write(render_index_page(articles))
    keep.add("index.html")
    print("  evidence/index.html: 分级索引")

    removed = cleanup_orphans(keep)
    if removed:
        print(f"  清理孤儿分页 {len(removed)} 个: {removed}")

    total = sum(counts.values())
    print(f"证据分级页生成完成：A {counts['A']} / B {counts['B']} / C {counts['C']}"
          f"（共 {total} 篇）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
