#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen-topic-pages.py —— 主题专辑页生成器（逆向重写版 v1.0）

复刻来源：线上 topics/ 下 20 个页面（2026-10-14 基线）。
规则（自基线逆向得出）：
  - 数据源：data/articles.json，按 JSON topic 字段精确匹配筛选，
    保持 JSON 既有次序（date 倒序 + 同日 slug 字母序）
  - 每专题每页 24 篇；第 1 页 = topics/{slug}.html，
    第 N 页（N>=2）= topics/{slug}-{N}.html（实证 53=24+24+5 等）
  - 同时生成 topics/index.html 专辑索引页（8 卡片，desc 截断 40 字符、
    无省略号，实证 epigenetics「…试图直接「重置」恰止于第 40 字）
  - 专题配置表（slug → 标题/描述）共 8 项，展示顺序即索引页顺序
    （非字母序，硬编码）；计数按 JSON topic 字段统计
  - 专题页第 1 页 hero 带「共 N 篇 · 最新更新 D」（D = 该专题最大 date），
    第 2 页起无此行；section-head h2 第 1 页为「全部文章」，
    第 N 页为「全部文章 · 第 N 页」
  - pager 出现在 feed 之前（与 <div class="feed"> 同行）与之后
    （与末 item 的 </div> 同行）各一次；三态：首页 info+next、
    中间 prev+info+next、末页 prev+info；第 2 页 prev 指向 {slug}.html
  - sub-text 仅第 1 页且有：共 N 篇，已分 M 页 — 继续浏览 →
    （margin-top:1.5rem，与 news 页 1rem 不同）
  - feed-item 与 news 页同模板（0 缩进、tag 空回退 topic），但 desc
    截断 130 字符加 …（news 页为 150、首页 feed 为 140，各版面独立常量）
  - 第 2 页起的 canonical/og:url 指向该页自身 URL（{slug}-N.html），
    title 不带页码（与第 1 页相同）
  - 单页专题（当前不存在，8 个专题均 ≥2 页）：不输出 pager 与 sub-text
    （防御性分支，线上不可见）
  - 专题页 footer 无全站计数；brand 单链（首页/news 页为双链怪癖）
"""
import html
import json
import math
import os
import sys

PER_PAGE = 24
DESC_MAX = 130     # 专题页 feed desc 截断长度（实证均恰止于 130；
                   # 注意与 news 列表页 150、首页 feed 140 不同，各版面独立常量）
INDEX_DESC_MAX = 40  # topics/index.html t-count 描述截断（无省略号）

# 专题配置：顺序 = topics/index.html 展示顺序
TOPIC_CONFIG = [
    ("cellular-senescence", "细胞衰老与清除",
     "Senolytic 药物、SASP 因子谱、免疫清除机制与相关临床试验。细胞衰老是当前抗衰老领域最核心的可干预靶点之一。"),
    ("epigenetics", "表观遗传与生物年龄",
     "部分重编程、DNA 甲基化时钟、组学衰老时钟与染色质重塑。这一路线试图直接「重置」细胞的年龄标记。"),
    ("metabolism-nutrition", "代谢干预与营养",
     "NAD+ 前体、mTOR 抑制剂、GLP-1 受体激动剂、热量限制与限时进食。代谢是衰老最核心的驱动因素之一。"),
    ("immunology-inflammation", "免疫衰老与炎症老化",
     "免疫衰老、炎症性老化（inflammaging）与免疫治疗策略。慢性低度炎症被认为是多种年龄相关疾病的共同上游。"),
    ("neurodegeneration", "神经退行性疾病",
     "阿尔茨海默病、帕金森病、认知衰退与神经再生。神经系统退化是衰老研究投入最大的领域之一。"),
    ("organ-aging", "器官特异性衰老",
     "心脏、肝脏、肌肉、骨骼、卵巢等器官的衰老机制与干预。不同器官的衰老速率差异显著。"),
    ("life-course", "生命历程与发育编程",
     "早期生命经历、发育编程、早衰症与健康不平等。衰老并非始于晚年，胎盘与生命早期已埋下伏笔。"),
    ("methods-tools", "方法学与研究工具",
     "单细胞测序、空间转录组、多组学整合与衰老时钟方法学。方法学进步往往是结论可靠性的前提。"),
]

TOPIC_HEAD = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} - LongBiosci</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="https://longbiosci.com/topics/{slug}.html">
<meta name="robots" content="index, follow">
<meta property="og:type" content="website">
<meta property="og:url" content="https://longbiosci.com/topics/{slug}.html">
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

TOPIC_HEADER = '''<body>
<a href="#main-content" class="skip-link">跳转到主要内容</a>
<header class="site-header">
  <div class="wrap">
    <a href="/" class="brand"><img src="/logo-mark.svg" alt="" class="brand-mark" width="28" height="28"><span class="brand-name">LongBiosci</span></a>
    <nav class="main-nav" aria-label="主导航">
      <a href="/">首页</a>
      <a href="/news/">最新</a>
      <a href="/topics/" aria-current="page" aria-label="主题专辑"><span class="nav-mq">主题</span>专辑</a>
      <a href="/guide/" aria-label="热词专题">热词<span class="nav-mq">专题</span></a>
      <a href="/research/" aria-label="概念与工具">概念<span class="nav-mq">与工具</span></a>
      <a href="/daily/">周刊</a>
      <a href="/evidence/" aria-label="证据分级">证据<span class="nav-mq">分级</span></a>
      <a href="/trials.html" aria-label="临床试验">临床<span class="nav-mq">试验</span></a>
      <a href="/industry/">产业</a>
      <a href="/podcast/" aria-label="播客">播<span class="nav-mq">客</span></a>
      <a href="/about/">关于</a>
      <a href="/search.html" class="nav-search" aria-label="站内搜索"><svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true" focusable="false"><circle cx="6.8" cy="6.8" r="4.6" fill="none" stroke="currentColor" stroke-width="1.6"/><line x1="10.3" y1="10.3" x2="14" y2="14" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg><span class="nav-search-text">搜索</span></a>
    </nav>
  </div>
</header>
'''

HERO_P1 = '''<main id="main-content">
<section class="hero"><div class="wrap">
<h1>{title}</h1>
<p>{desc}</p>
<p style="margin-top:.75rem">共 <strong>{count} 篇</strong> · 最新更新 {latest}</p>
</div></section>
'''

HERO_PN = '''<main id="main-content">
<section class="hero"><div class="wrap">
<h1>{title}</h1>
<p>{desc}</p>
</div></section>
'''

SECTION_OPEN = '''<section class="section"><div class="wrap">
<div class="section-head"><h2>全部文章{h2_suffix}</h2><a href="/topics/" class="section-more">← 返回专辑索引</a></div>
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
            '<a href="/topics/{slug}-2.html">继续浏览 →</a></p>\n')

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

# ---- topics/index.html 模板（0 缩进卡片）----
INDEX_HEAD = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>主题专辑 - LongBiosci</title>
<meta name="description" content="按衰老机制归类的研究解读专辑">
<link rel="canonical" href="https://longbiosci.com/topics/">
<meta name="robots" content="index, follow">
<meta property="og:type" content="website">
<meta property="og:url" content="https://longbiosci.com/topics/">
<meta property="og:title" content="主题专辑 - LongBiosci">
<meta property="og:description" content="按衰老机制归类的研究解读专辑">
<meta property="og:image" content="https://longbiosci.com/og-image.png">
<meta property="og:site_name" content="LongBiosci">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="主题专辑 - LongBiosci">
<meta name="twitter:description" content="按衰老机制归类的研究解读专辑">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="stylesheet" href="/style.css">
</head>
'''

INDEX_HERO = '''<main id="main-content">
<section class="hero"><div class="wrap">
<h1>主题专辑</h1>
<p>按衰老机制归类的 {total} 篇研究解读。避免信息流碎片化，让同一机制的证据纵向积累。</p>
</div></section>
<section class="section"><div class="wrap">
<div class="topic-grid">
'''

INDEX_CARD = '''<a href="/topics/{slug}.html" class="topic-card">
<span class="t-name">{title}</span>
<span class="t-count">{count} 篇 · {desc}</span>
</a>'''


def esc(s):
    return html.escape(s or "", quote=True)


def trunc(s, n):
    return s[:n] + "…" if len(s) > n else s


def feed_item(a):
    return FEED_ITEM.format(
        tag=esc(a["tag"] or a["topic"]),
        tier=esc(a["evidence"]),
        date=esc(a["date"]),
        topic=esc(a["topic"]),
        slug=a["slug"],
        title=esc(a["title"]),
        desc=esc(trunc(a["desc"], DESC_MAX)),
    )


def pager(slug, page, total_pages):
    """三态分页；单页专题不输出（防御性分支）。"""
    if total_pages <= 1:
        return ""
    info = f'<span class="pager-info">第 {page} / {total_pages} 页</span>'
    prev_href = (f"/topics/{slug}.html" if page == 2
                 else f"/topics/{slug}-{page - 1}.html")
    prev_link = f'<a href="{prev_href}" rel="prev">← 上一页</a>'
    next_link = f'<a href="/topics/{slug}-{page + 1}.html" rel="next">下一页 →</a>'
    if page == 1:
        body = info + next_link
    elif page == total_pages:
        body = prev_link + info
    else:
        body = prev_link + info + next_link
    return f'<nav class="pager" aria-label="分页">{body}</nav>'


def render_topic_page(slug, title, desc, articles):
    total = len(articles)
    total_pages = max(1, math.ceil(total / PER_PAGE))
    latest = max(a["date"] for a in articles)
    for page in range(1, total_pages + 1):
        # canonical/og:url 指向本页自身 URL（第 2 页起为 {slug}-N.html），title 不变
        page_slug = slug if page == 1 else f"{slug}-{page}"
        head = (TOPIC_HEAD.replace("{title}", title).replace("{desc}", desc)
                .replace("{slug}", page_slug))
        if page == 1:
            hero = (HERO_P1.replace("{title}", title).replace("{desc}", desc)
                    .replace("{count}", str(total))
                    .replace("{latest}", latest))
            h2_suffix = ""
        else:
            hero = (HERO_PN.replace("{title}", title)
                    .replace("{desc}", desc))
            h2_suffix = f" · 第 {page} 页"
        items = articles[(page - 1) * PER_PAGE: page * PER_PAGE]
        pg = pager(slug, page, total_pages)
        out = (head + TOPIC_HEADER + hero
               + SECTION_OPEN.replace("{h2_suffix}", h2_suffix)
               + pg + FEED_OPEN
               + "\n".join(feed_item(a) for a in items)
               + "\n</div>" + pg + "\n")
        if page == 1 and total_pages > 1:
            out += SUB_TEXT.replace("{total}", str(total)).replace(
                "{pages}", str(total_pages)).replace("{slug}", slug)
        out += SECTION_CLOSE + FOOTER
        dst = (os.path.join("topics", f"{slug}.html") if page == 1
               else os.path.join("topics", f"{slug}-{page}.html"))
        yield dst, out


def render_index_page(articles):
    total = len(articles)
    cards = []
    for slug, title, desc in TOPIC_CONFIG:
        count = sum(1 for a in articles if a["topic"] == title_to_topic(title))
        cards.append(INDEX_CARD.format(
            slug=slug, title=title, count=count, desc=desc[:INDEX_DESC_MAX]))
    return (INDEX_HEAD + TOPIC_HEADER
            + INDEX_HERO.replace("{total}", str(total))
            + "\n".join(cards) + "\n</div>\n</div></section>\n" + FOOTER)


# 专题标题 → JSON topic 字段值（短名）的映射
TITLE2TOPIC = {
    "细胞衰老与清除": "细胞衰老",
    "表观遗传与生物年龄": "表观遗传",
    "代谢干预与营养": "代谢与营养",
    "免疫衰老与炎症老化": "免疫与炎症",
    "神经退行性疾病": "神经退行",
    "器官特异性衰老": "器官衰老",
    "生命历程与发育编程": "生命历程",
    "方法学与研究工具": "方法与工具",
}


def title_to_topic(title):
    return TITLE2TOPIC[title]


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    os.chdir(root)
    with open("data/articles.json", encoding="utf-8") as f:
        articles = json.load(f)

    os.makedirs("topics", exist_ok=True)
    for slug, title, desc in TOPIC_CONFIG:
        topic_name = TITLE2TOPIC[title]
        sel = [a for a in articles if a["topic"] == topic_name]
        if not sel:
            print(f"  ! topics/{slug}: 无文章，跳过")
            continue
        for dst, out in render_topic_page(slug, title, desc, sel):
            with open(dst, "w", encoding="utf-8", newline="") as f:
                f.write(out)
        pages = max(1, math.ceil(len(sel) / PER_PAGE))
        print(f"  topics/{slug}.html: {len(sel)} 篇 / {pages} 页")

    with open(os.path.join("topics", "index.html"), "w", encoding="utf-8",
              newline="") as f:
        f.write(render_index_page(articles))
    print("  topics/index.html: 专辑索引")
    print("主题专辑页生成完成")


if __name__ == "__main__":
    main()
