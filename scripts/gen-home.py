#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen-home.py —— 首页生成器（逆向重写版 v1.0）

复刻来源：线上 index.html（2026-10-14 基线）。
规则（自基线逆向得出）：
  - 数据源：data/articles.json（380 篇，date 倒序 + 同日 slug 字母序）
  - 「今日必读」lead-grid：取 JSON 前 6 篇；desc 按原文截断 96 字符加 …
    （实证 6/6 张卡 shown=97 含省略号；先截断后转义，与 news 页同规则）
  - 「主题专辑」topic-grid：8 个专题硬编码展示顺序（非字母序），
    计数按 JSON topic 字段统计（53/34/48/45/66/37/67/30，合计 380）
  - 「核心概念」topic-grid：6 张静态卡片，计数为硬编码值——
    概念页（senolytic.html 等）是管线外静态页，其自身计数（64/45/7/8/6/5）
    与首页卡片（72/43/8/8/6/6）已漂移，且无关键词规则可复现任一侧，
    故按线上首页原样硬编码，漂移问题记入运营待办
  - 「证据分级」ev-grid：A/B/C 计数按 JSON evidence 字段统计（94/269/17）
  - 「最新收录」feed：取 JSON 第 7–18 篇（跳过已上 lead 的 6 篇），
    desc 截断 140 字符加 …（实证均恰止于 140；news 列表页为 150、
    专题页为 130，各版面独立常量），feed-item 为 8 空格缩进变体
    （news 页是 0 缩进，两处模板不同）
  - hero 与 footer 的「全站 N 篇」= len(records)；「更新至 D」= 全站最大 date
  - title/desc/tag/topic 走 html.escape(quote=True)；tag 为空时回退 topic
    （与 news 页一致的兜底，首页场景暂不可见，按同源逻辑推断）
  - 首页头部/brand 双链、hero 未闭合 <p>、footer 未闭合 <p> 等历史怪癖
    均按原样复刻
"""
import html
import json
import os
import sys
from collections import Counter

LEAD_COUNT = 6        # 今日必读卡片数
FEED_COUNT = 12       # 最新收录 feed 条数
FEED_SKIP = 6         # feed 跳过前 6 篇（已上 lead）
LEAD_DESC_MAX = 96    # lead-card desc 截断长度（原文字符数）
FEED_DESC_MAX = 140   # 首页 feed desc 截断长度（实证均恰止于 140；
                      # 注意与 news 列表页 150、专题页 130 不同，各版面独立常量）

# 专题配置：顺序 = 首页展示顺序；短名同时是 JSON topic 字段值
TOPICS = [
    ("cellular-senescence", "细胞衰老", "Senolytic、SASP 与免疫清除"),
    ("epigenetics", "表观遗传", "重编程、DNA 甲基化与生物年龄"),
    ("metabolism-nutrition", "代谢与营养", "NAD+、mTOR、GLP-1 与饮食干预"),
    ("immunology-inflammation", "免疫与炎症", "免疫衰老、炎症老化与免疫治疗"),
    ("neurodegeneration", "神经退行", "阿尔茨海默、帕金森与认知衰退"),
    ("organ-aging", "器官衰老", "心脏、肝脏、肌肉、卵巢等器官"),
    ("life-course", "生命历程", "发育编程、早衰与健康公平"),
    ("methods-tools", "方法与工具", "单细胞、多组学与研究方法"),
]

# 核心概念静态卡片（计数硬编码，见模块 docstring）
CONCEPTS = [
    ("/senolytic.html", "Senolytic 清除", "72 篇 · 选择性清除衰老细胞的药物类别"),
    ("/stemcell.html", "干细胞与细胞替代", "43 篇 · 再生医学抗衰主线"),
    ("/rapamycin.html", "Rapamycin 雷帕霉素", "8 篇 · mTOR 抑制剂，模型生物延寿最稳"),
    ("/telomere.html", "端粒与端粒酶", "8 篇 · 最经典的衰老标志物"),
    ("/metformin.html", "Metformin 二甲双胍", "6 篇 · AMPK 通路抗衰候选，TAME 试验待验证"),
    ("/nmn.html", "NMN 与 NAD+", "6 篇 · 消费级抗衰最大品类，人体证据弱"),
]

# 证据分级静态文案（计数按 JSON evidence 字段统计）
EVIDENCE = [
    ("A", "a", "同行评议人体研究",
     "已发表的人体研究，含随机对照试验与队列分析。结论可信度最高。"),
    ("B", "b", "同行评议临床前研究",
     "动物或体外实验的同行评议研究。机制清晰，但尚不能外推至人体。"),
    ("C", "c", "预印本（未经同行评议）",
     "预印本，未经同行评议。结论可能随审稿而改变，仅供跟踪参考。"),
]

HOME_HEAD = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LongBiosci - 衰老生物学与长寿科技</title>
<meta name="description" content="追踪衰老与长寿科技领域的前沿进展：细胞衰老、表观遗传重编程、代谢干预、临床试验与产业动态。每篇标注证据分级。">
<link rel="canonical" href="https://longbiosci.com/">
<meta name="robots" content="index, follow">

<!-- Open Graph -->
<meta property="og:type" content="website">
<meta property="og:url" content="https://longbiosci.com/">
<meta property="og:title" content="LongBiosci - 衰老生物学与长寿科技">
<meta property="og:description" content="追踪衰老与长寿科技领域的前沿进展，每篇标注证据分级。">
<meta property="og:image" content="https://longbiosci.com/og-image.png">
<meta property="og:site_name" content="LongBiosci">
<meta property="og:locale" content="zh_CN">

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="LongBiosci - 衰老生物学与长寿科技">
<meta name="twitter:description" content="追踪衰老与长寿科技领域的前沿进展，每篇标注证据分级。">
<meta name="twitter:image" content="https://longbiosci.com/og-image.png">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="stylesheet" href="/style.css">
<link rel="alternate" type="application/rss+xml" title="LongBiosci RSS" href="/rss.xml">
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "@id": "https://longbiosci.com/#website",
  "url": "https://longbiosci.com",
  "name": "LongBiosci",
  "description": "衰老生物学与长寿科技资讯平台",
  "inLanguage": "zh-CN",
  "publisher": { "@id": "https://longbiosci.com/#organization" }
}
</script>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "@id": "https://longbiosci.com/#organization",
  "name": "LongBiosci",
  "alternateName": "LongBiosci 编辑部",
  "url": "https://longbiosci.com",
  "description": "衰老与长寿科技领域的科研资讯平台"
}
</script>
<!-- longbiosci:analytics 无 Cookie、无跨站追踪、不收集身份信息；详见 /privacy/ -->
<script defer src="https://cloud.umami.is/script.js" data-website-id="bfb60723-d93d-4925-b1a2-d7ef51b9014c" data-do-not-track="true"></script></head>
'''

HOME_HEADER = '''<body>
<a href="#main-content" class="skip-link">跳转到主要内容</a>
<header class="site-header">
  <div class="wrap">
    <a href="/" class="brand"><img src="/logo-mark.svg" alt="" class="brand-mark" width="28" height="28"><span class="brand-name">LongBiosci</span></a>
    <nav class="main-nav" aria-label="主导航">
      <a href="/" aria-current="page">首页</a>
      <a href="/news/">最新</a>
      <a href="/topics/">主题专辑</a><a href="/research/">概念与工具</a><a href="/daily/">周刊</a>
      <a href="/evidence/">证据分级</a>
      <a href="/trials.html">临床试验</a>
      <a href="/companies/">产业</a>
      <a href="/about/">关于</a>
    </nav>
  </div>
</header>
'''

HERO = '''<main id="main-content">
  <section class="hero">
    <div class="wrap">
      <h1>衰老生物学与长寿科技</h1>
      <p>追踪细胞衰老、表观遗传重编程、代谢干预与临床试验的前沿进展。全站 {total} 篇研究解读，每篇标注证据分级——同行评议人体研究、临床前研究或预印本，来源可溯。
    </div>
  </section>
'''

LEAD_SECTION = '''  <section class="section">
    <div class="wrap">
      <div class="section-head">
        <h2>今日必读</h2>
        <span class="section-note">最新 {lead} 篇 · 更新至 {maxdate}</span>
        <a href="/news/" class="section-more">查看全部 →</a>
      </div>
      <div class="lead-grid">
'''

LEAD_CARD = '''        <a href="/news/{slug}" class="lead-card">
          <div class="item-meta">
            <span class="tag">{tag}</span>
            <span class="tier tier-{tier}">{tier}</span>
          </div>
          <h3>{title}</h3>
          <p>{desc}</p>
          <div class="card-foot">
            <span>{date}</span>
            <span>·</span>
            <span>{topic}</span>
            <span>·</span>
            <span>{source}</span>
          </div>
        </a>'''

SECTION_CLOSE = '''      </div>
    </div>
  </section>
'''

TOPIC_SECTION = '''  <section class="section">
    <div class="wrap">
      <div class="section-head">
        <h2>主题专辑</h2>
        <span class="section-note">按衰老机制归类，避免信息流碎片化</span>
      </div>
      <div class="topic-grid">
'''

TOPIC_CARD = '''        <a href="/topics/{slug}.html" class="topic-card">
          <span class="t-name">{name}</span>
          <span class="t-count">{count} 篇 · {desc}</span>
        </a>'''

CONCEPT_SECTION = '''  <section class="section">
    <div class="wrap">
      <div class="section-head">
        <h2>核心概念</h2>
        <span class="section-note">按干预手段归类 —— 「某个热门方案到底有没有依据」从这里查</span>
      </div>
      <div class="topic-grid">
'''

CONCEPT_CARD = '''        <a href="{href}" class="topic-card">
          <span class="t-name">{name}</span>
          <span class="t-count">{count}</span>
        </a>'''

EVIDENCE_SECTION = '''  <section class="section">
    <div class="wrap">
      <div class="section-head">
        <h2>证据分级</h2>
        <span class="section-note">本站对每篇文章标注证据强度，读者可按需筛选</span>
        <a href="/about/#editorial-policy" class="section-more">分级标准 →</a>
      </div>
      <div class="ev-grid">
'''

EV_CARD = '''        <a href="/evidence/{tier}.html" class="ev-card">
          <div class="ev-head">
            <span class="ev-tier ev-{cls}">{tier}</span>
            <h3>{name}</h3>
          </div>
          <p>{desc}</p>
          <span class="ev-n">{count} 篇</span>
        </a>'''

FEED_SECTION = '''  <section class="section">
    <div class="wrap">
      <div class="section-head">
        <h2>最新收录</h2>
        <span class="section-note">持续更新</span>
        <a href="/news/" class="section-more">更多 →</a>
      </div>
      <div class="feed">
'''

# 首页 feed-item 是 8 空格缩进变体（news 列表页为 0 缩进，两者不同源）
HOME_FEED_ITEM = '''        <div class="feed-item">
          <div class="item-meta">
            <span class="tag">{tag}</span>
            <span class="tier tier-{tier}">{tier}</span>
            <span class="tag-date">{date}</span>
            <span>{topic}</span>
          </div>
          <div class="feed-title"><a href="/news/{slug}">{title}</a></div>
          <p class="feed-desc">{desc}</p>
        </div>'''

FOOTER = '''</main>
<footer class="site-footer">
  <div class="wrap">
    <p>© 2026 LongBiosci · 衰老与长寿科技资讯 · 全站 {total} 篇
    <a href="/rss.xml">RSS</a> · <a href="/sitemap.xml">Sitemap</a> · <a href="/about/">关于</a>
  </div>
</footer>
</body>
</html>
'''


def esc(s):
    return html.escape(s or "", quote=True)


def trunc(s, n):
    return s[:n] + "…" if len(s) > n else s


def render_lead_card(a):
    return LEAD_CARD.format(
        slug=a["slug"],
        tag=esc(a["tag"] or a["topic"]),
        tier=esc(a["evidence"]),
        title=esc(a["title"]),
        desc=esc(trunc(a["desc"], LEAD_DESC_MAX)),
        date=esc(a["date"]),
        topic=esc(a["topic"]),
        source=esc(a["source"]),
    )


def render_feed_item(a):
    return HOME_FEED_ITEM.format(
        tag=esc(a["tag"] or a["topic"]),
        tier=esc(a["evidence"]),
        date=esc(a["date"]),
        topic=esc(a["topic"]),
        slug=a["slug"],
        title=esc(a["title"]),
        desc=esc(trunc(a["desc"], FEED_DESC_MAX)),
    )


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    with open(os.path.join(root, "data/articles.json"), encoding="utf-8") as f:
        articles = json.load(f)
    total = len(articles)
    maxdate = max(a["date"] for a in articles)
    topic_counts = Counter(a["topic"] for a in articles)
    ev_counts = Counter(a["evidence"] for a in articles)

    out = HOME_HEAD + HOME_HEADER
    out += HERO.replace("{total}", str(total))
    out += LEAD_SECTION.replace("{lead}", str(LEAD_COUNT)).replace(
        "{maxdate}", maxdate)
    out += "\n".join(render_lead_card(a) for a in articles[:LEAD_COUNT]) + "\n"
    out += SECTION_CLOSE
    out += TOPIC_SECTION
    out += "\n".join(
        TOPIC_CARD.format(slug=slug, name=name,
                          count=topic_counts.get(name, 0), desc=desc)
        for slug, name, desc in TOPICS) + "\n"
    out += SECTION_CLOSE
    out += CONCEPT_SECTION
    out += "\n".join(
        CONCEPT_CARD.format(href=href, name=name, count=count)
        for href, name, count in CONCEPTS) + "\n"
    out += SECTION_CLOSE
    out += EVIDENCE_SECTION
    out += "\n".join(
        EV_CARD.format(tier=t, cls=cls, name=name, desc=desc,
                       count=ev_counts.get(t, 0))
        for t, cls, name, desc in EVIDENCE) + "\n"
    out += SECTION_CLOSE
    out += FEED_SECTION
    out += "\n".join(
        render_feed_item(a) for a in articles[FEED_SKIP:FEED_SKIP + FEED_COUNT]
    ) + "\n"
    out += SECTION_CLOSE
    out += FOOTER.replace("{total}", str(total))

    dst = os.path.join(root, "index.html")
    with open(dst, "w", encoding="utf-8", newline="") as f:
        f.write(out)
    print(f"  index.html: lead {min(LEAD_COUNT, total)} 篇 + feed "
          f"{max(0, min(FEED_COUNT, total - FEED_SKIP))} 篇 / 全站 {total} 篇")
    print("首页生成完成")


if __name__ == "__main__":
    main()
