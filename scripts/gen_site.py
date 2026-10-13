#!/usr/bin/env python3
"""全站索引生成器：从 data/articles.json 重建所有静态列表页。

生成范围（共 391 篇规模）：
- news/index.html + news-{2..N}.html        最新收录，30 篇/页
- topics/{slug}.html (+分页)                8 大主题专辑
- topics/index.html                         主题专辑索引（计数刷新）
- evidence/{A,B,C}.html (+分页)             证据分级页，30 篇/页
- evidence/index.html                       分级索引（计数刷新）
- index.html                                首页计数 + 今日必读 6 卡

由 .github/workflows/regen-index.yml 在 articles.json 变更时自动调用。
过期分页文件会被自动删除（仅限本生成器管理的路径）。
"""
import json
import re
import shutil
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://longbiosci.com"
PER_PAGE = 30

TOPICS = {
    "细胞衰老": ("cellular-senescence", "细胞衰老与清除",
                 "Senolytic 药物、SASP 因子谱、免疫清除机制与相关临床试验。"),
    "表观遗传": ("epigenetics", "表观遗传与生物年龄",
                 "部分重编程、DNA 甲基化时钟、组学衰老时钟与染色质重塑。这一路线试图直接「重置」细胞的年龄标记。"),
    "代谢与营养": ("metabolism-nutrition", "代谢干预与营养",
                   "NAD+ 前体、mTOR 抑制剂、GLP-1 受体激动剂、热量限制与限时进食。"),
    "免疫与炎症": ("immunology-inflammation", "免疫衰老与炎症老化",
                   "免疫衰老、炎症性老化（inflammaging）与免疫治疗策略。"),
    "神经退行": ("neurodegeneration", "神经退行性疾病",
                 "阿尔茨海默病、帕金森病、认知衰退与神经再生。神经系统退化是衰老研究投入最大的领域之一。"),
    "器官衰老": ("organ-aging", "器官特异性衰老",
                 "心脏、肝脏、肌肉、骨骼、卵巢等器官的衰老机制与干预。不同器官的衰老速率差异显著。"),
    "生命历程": ("life-course", "生命历程与发育编程",
                 "早期生命经历、发育编程、早衰症与健康不平等。衰老并非始于晚年。"),
    "方法与工具": ("methods-tools", "方法学与研究工具",
                   "单细胞测序、空间转录组、多组学整合与衰老时钟方法学。方法学进步往往是结论可靠性的前提。"),
}
EVID_META = {
    "A": ("同行评议人体研究",
          "已在同行评议期刊发表的人体研究，包括随机对照试验、队列分析与临床试验中期数据。这是本站证据等级中可信度最高的一类。"),
    "B": ("同行评议临床前研究",
          "已发表但限于动物模型或体外实验的研究。机制描述清晰、可信度高，但结论尚不能外推至人体。"),
    "C": ("预印本（未经同行评议）",
          "发布在 bioRxiv、medRxiv 等预印本平台的论文，尚未经过同行评议。此类结论可能随审稿意见而改变，仅供领域跟踪参考。"),
}
FILTER_BAR = (
    '<div class="filter-bar">\n<span class="filter-label">按主题浏览：</span>\n'
    '<a href="/topics/">全部主题</a>\n<a href="/evidence/A.html">A 级人体研究</a>\n'
    '<a href="/evidence/B.html">B 级临床前</a>\n<a href="/evidence/C.html">C 级预印本</a>\n'
    '<a href="/search.html">站内搜索</a>\n</div>\n'
)
FOOTER = (
    '</main><footer class="site-footer">\n  <div class="wrap">\n'
    "    <p>© 2026 LongBiosci · 衰老与长寿科技资讯</p>\n"
    '    <a href="/rss.xml">RSS</a> · <a href="/sitemap.xml">Sitemap</a> · <a href="/about/">关于</a>\n'
    "  </div>\n</footer>\n</body>\n</html>\n"
)


def head(title, desc, canonical, active):
    nav = {
        "news": ("最新", "/news/"), "topics": ("主题专辑", "/topics/"),
        "evidence": ("证据分级", "/evidence/"),
    }
    def a(href, label):
        cur = ' aria-current="page"' if nav.get(active, ("", "")) == (label, href) else ""
        return f'      <a href="{href}"{cur}>{label}</a>'
    navs = {
        "news": a("/news/", "最新"), "topics": a("/topics/", "主题专辑"),
        "evidence": a("/evidence/", "证据分级"),
    }
    nav_html = f'''      <a href="/">首页</a>
      <a href="/news/"{' aria-current="page"' if active == "news" else ""}>最新</a>
      <a href="/topics/"{' aria-current="page"' if active == "topics" else ""}>主题专辑</a><a href="/research/">概念与工具</a><a href="/daily/">周刊</a>
      <a href="/evidence/"{' aria-current="page"' if active == "evidence" else ""}>证据分级</a>
      <a href="/search.html">搜索</a>
      <a href="/trials.html">临床试验</a>
      <a href="/about/">关于</a>'''
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="referrer" content="strict-origin-when-cross-origin">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(title)}</title>
<meta name="description" content="{escape(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website">
<meta property="og:url" content="{canonical}">
<meta property="og:title" content="{escape(title)}">
<meta property="og:description" content="{escape(desc)}">
<meta property="og:image" content="{BASE}/og-image.png">
<meta property="og:site_name" content="LongBiosci">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{escape(title)}">
<meta name="twitter:description" content="{escape(desc)}">
<link rel="alternate" type="application/rss+xml" title="LongBiosci RSS" href="/rss.xml">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="stylesheet" href="/style.css">
<script defer src="https://cloud.umami.is/script.js" data-website-id="bfb60723-d93d-4925-b1a2-d7ef51b9014c" data-do-not-track="true"></script>
</head>
<body>
<a href="#main-content" class="skip-link">跳转到主要内容</a>
<header class="site-header">
  <div class="wrap">
    <a href="/" class="brand"><img src="/logo-mark.svg" alt="" class="brand-mark" width="28" height="28"><span class="brand-name">LongBiosci</span></a>
    <nav class="main-nav" aria-label="主导航">
{nav_html}
    </nav>
  </div>
</header>
<main id="main-content">
'''


def feed_item(a, with_topic=True):
    e = a.get("evidence", "B")
    topic = a.get("topic", "")
    meta = (f'<span class="tag">{escape(str(a.get("tag", "研究进展")))}</span>\n'
            f'<span class="tier tier-{e}">{e}</span>\n'
            f'<span class="tag-date">{a.get("date", "")}</span>\n')
    if with_topic and topic:
        meta += f"<span>{escape(str(topic))}</span>\n"
    return (f'<div class="feed-item">\n<div class="item-meta">\n{meta}</div>\n'
            f'<div class="feed-title"><a href="/news/{a["slug"]}">{escape(str(a["title"]))}</a></div>\n'
            f'<p class="feed-desc">{escape(str(a.get("desc", "")))}</p>\n</div>\n')


def pager(cur, total_pages, url_for):
    parts = ['<nav class="pager" aria-label="分页">']
    if cur > 1:
        prev = url_for(1) if cur == 2 else url_for(cur - 1)
        parts.append(f'<a href="{prev}" rel="prev">← 上一页</a>')
    parts.append(f'<span class="pager-info">第 {cur} / {total_pages} 页</span>')
    if cur < total_pages:
        parts.append(f'<a href="{url_for(cur + 1)}" rel="next">下一页 →</a>')
    parts.append("</nav>")
    return "".join(parts)


def paginate(items, url_for, page_path, first_path, title_base, desc, hero_h1,
             hero_p_fmt, active, with_topic=True, sub_text_total=None):
    total = len(items)
    pages = max(1, -(-total // PER_PAGE))
    written = {}
    for p in range(1, pages + 1):
        chunk = items[(p - 1) * PER_PAGE: p * PER_PAGE]
        feed = '<div class="feed">\n' + "".join(feed_item(a, with_topic) for a in chunk) + "</div>\n"
        pg = pager(p, pages, url_for)
        if p == 1:
            hero_p = hero_p_fmt.format(n=total)
            title = title_base
            canonical = f"{BASE}{first_path}"
        else:
            s, e_ = (p - 1) * PER_PAGE + 1, min(p * PER_PAGE, total)
            hero_p = f"共 {total} 篇，本页第 {s}–{e_} 篇。每篇标注证据分级。"
            title = f"{title_base} 第 {p} 页"
            canonical = f"{BASE}{page_path.format(k=p)}"
        sub = ""
        if sub_text_total and pages > 1:
            sub = (f'<p class="sub-text" style="text-align:center;margin-top:1rem">'
                   f"共 {total} 篇 — <a href=\"{url_for(2)}\">查看第 2 页 →</a></p>\n")
        html = (head(title, desc, canonical, active)
                + f'<section class="hero"><div class="wrap">\n<h1>{escape(hero_h1)}</h1>\n'
                + f"<p>{escape(hero_p)}</p>\n</div></section>\n"
                + '<section class="section"><div class="wrap">\n'
                + (FILTER_BAR if p == 1 else "")
                + pg + "\n" + feed + sub
                + "</div></section>\n" + FOOTER)
        out = (first_path.lstrip("/") if p == 1 else page_path.format(k=p).lstrip("/"))
        if out.endswith("/"):
            out += "index.html"
        written[out] = html
    return written


def main():
    arts = json.loads((ROOT / "data" / "articles.json").read_text(encoding="utf-8"))
    arts.sort(key=lambda a: a.get("date", ""), reverse=True)
    n = len(arts)
    generated = {}

    # ---- news ----
    generated.update(paginate(
        arts, lambda k: "/news/" if k == 1 else f"/news-{k}.html",
        "/news-{k}.html", "/news/", "最新收录",
        "全部抗衰老与长寿科技研究解读，按时间倒序，每篇标注证据分级。",
        "最新收录", "全部 {n} 篇研究解读，按时间倒序。每篇标注证据分级——同行评议人体研究、临床前研究或预印本。",
        "news", with_topic=True, sub_text_total=n))

    # ---- topics ----
    for topic, (slug, disp, hero_desc) in TOPICS.items():
        items = [a for a in arts if a.get("topic") == topic]
        if not items:
            continue
        generated.update(paginate(
            items, lambda k, s=slug: f"/topics/{s}.html" if k == 1 else f"/topics/{s}-{k}.html",
            f"/topics/{slug}-{{k}}.html", f"/topics/{slug}.html", disp,
            f"{disp}主题下的全部研究解读，按时间倒序，每篇标注证据分级。",
            disp, "{n} 篇研究解读。" + hero_desc, "topics", with_topic=True))

    # ---- evidence ----
    for tier, (disp, hero_desc) in EVID_META.items():
        items = [a for a in arts if a.get("evidence") == tier]
        generated.update(paginate(
            items, lambda k, t=tier: f"/evidence/{t}.html" if k == 1 else f"/evidence/{t}-{k}.html",
            f"/evidence/{tier}-{{k}}.html", f"/evidence/{tier}.html", disp,
            f"{disp}：全部研究解读，按时间倒序。",
            disp, "{n} 篇。" + hero_desc, "evidence", with_topic=False))

    # ---- topics/index.html ----
    cards = []
    for topic, (slug, disp, hero_desc) in TOPICS.items():
        cnt = sum(1 for a in arts if a.get("topic") == topic)
        cards.append(f'<a href="/topics/{slug}.html" class="topic-card">\n'
                     f'<span class="t-name">{disp}</span>\n'
                     f'<span class="t-count">{cnt} 篇 · {escape(hero_desc)}</span>\n</a>\n')
    generated["topics/index.html"] = (
        head("主题专辑 - LongBiosci", "按衰老机制归类的研究解读专辑", f"{BASE}/topics/", "topics")
        + '<section class="hero"><div class="wrap">\n<h1>主题专辑</h1>\n'
        + f"<p>按衰老机制归类的 {n} 篇研究解读。避免信息流碎片化，让同一机制的证据纵向积累。</p>\n</div></section>\n"
        + '<section class="section"><div class="wrap">\n<div class="topic-grid">\n'
        + "".join(cards) + "</div>\n</div></section>\n" + FOOTER)

    # ---- evidence/index.html ----
    counts = {t: sum(1 for a in arts if a.get("evidence") == t) for t in "ABC"}
    ev_cards = "".join(
        f'<a href="/evidence/{t}.html" class="ev-card">\n<div class="ev-head">\n'
        f'<span class="ev-tier ev-{t.lower()}">{t}</span>\n<h3>{EVID_META[t][0]}</h3>\n</div>\n'
        f"<p>{EVID_META[t][1]}</p>\n"
        f'<span class="ev-n">{counts[t]} 篇</span>\n</a>\n' for t in "ABC")
    generated["evidence/index.html"] = (
        head("证据分级 - LongBiosci", "LongBiosci 证据分级标准与全部文章索引", f"{BASE}/evidence/", "evidence")
        + '<section class="hero"><div class="wrap">\n<h1>证据分级</h1>\n'
        + "<p>本站对每一篇研究解读标注证据强度。这不是形式——它决定了你能否把一条信息当作结论使用。</p>\n</div></section>\n"
        + '<section class="section"><div class="wrap">\n<div class="ev-grid">\n'
        + ev_cards + "</div>\n"
        + '<div class="notice-box" style="margin-top:2rem">\n<p><strong>为什么坚持做分级</strong></p>\n'
        + "<p>衰老领域的营销话术与真实进展混杂在一起。一个\"逆转衰老\"的标题，可能来自 3 名受试者的一期临床，也可能来自分子通路层面的体外实验。把证据等级标出来，是为了让读者在读第一段时就知道该多信它。</p>\n</div>\n"
        + "</div></section>\n" + FOOTER)

    # ---- index.html（首页：计数 + 今日必读）----
    idx_path = ROOT / "index.html"
    idx = idx_path.read_text(encoding="utf-8")
    idx = re.sub(r"全站 \d+ 篇", f"全站 {n} 篇", idx)
    latest_date = arts[0].get("date", "") if arts else ""
    idx = re.sub(r"更新至 [\d-]+", f"更新至 {latest_date}", idx)
    cards6 = []
    for a in arts[:6]:
        short = str(a.get("desc", ""))[:60] + "…"
        cards6.append(
            f'        <a href="/news/{a["slug"]}" class="lead-card">\n'
            "          <div class=\"item-meta\">\n"
            f'            <span class="tag">{escape(str(a.get("tag", "研究进展")))}</span>\n'
            f'            <span class="tier tier-{a.get("evidence", "B")}">{a.get("evidence", "B")}</span>\n'
            "          </div>\n"
            f"          <h3>{escape(str(a['title']))}</h3>\n"
            f"          <p>{escape(short)}</p>\n"
            "          <div class=\"card-foot\">\n"
            f"            <span>{a.get('date', '')}</span>\n<span>·</span>\n"
            f"            <span>{escape(str(a.get('topic', '')))}</span>\n<span>·</span>\n"
            f"            <span>{escape(str(a.get('source', '')))}</span>\n"
            "          </div>\n        </a>\n")
    m = re.search(r'<div class="lead-grid">[\s\S]*?</section>', idx)
    if m:
        idx = idx[:m.start()] + '<div class="lead-grid">\n' + "".join(cards6) + "      </div>\n      </div></section>" + idx[m.end():]
    generated["index.html"] = idx

    # ---- data/search-index.json（站内搜索数据源）----
    search_idx = [
        [str(a["title"]), f"/news/{a['slug']}", a.get("date", ""),
         str(a.get("tag", "")), str(a.get("topic", "")),
         str(a.get("evidence", "")), str(a.get("desc", ""))]
        for a in arts
    ]
    si_path = ROOT / "data" / "search-index.json"
    new_si = json.dumps(search_idx, ensure_ascii=False)
    if not si_path.exists() or si_path.read_text(encoding="utf-8") != new_si:
        si_path.write_text(new_si, encoding="utf-8")
        print("updated: data/search-index.json")

    # ---- 写入 ----
    for rel, html in generated.items():
        p = ROOT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.exists() and p.read_text(encoding="utf-8") == html:
            continue
        p.write_text(html, encoding="utf-8")
        print("updated:", rel)

    # ---- 清理过期分页文件 ----
    managed = set(generated)
    stale = []
    for pat, prefix_ok in [("news-*.html", None), ("topics/*.html", None), ("evidence/*.html", None)]:
        for p in ROOT.glob(pat):
            rel = str(p.relative_to(ROOT)).replace("\\", "/")
            if rel not in managed:
                stale.append(rel)
    for rel in stale:
        (ROOT / rel).unlink()
        print("removed stale:", rel)
    print(f"done: {n} articles, {len(generated)} pages generated, {len(stale)} stale removed")


if __name__ == "__main__":
    main()
