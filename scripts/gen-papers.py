#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen-papers.py —— 论文索引页 /papers/ 生成器（管线第 9 环节）

为什么新增这一页
────────────────
`data/search-index.json` 里长期挂着一条栏目页条目：

    ["论文索引（可溯源 DOI）", "/papers/", "2026-10-17", "论文", "栏目", "",
     "核心原始文献索引，每篇给出可直接访问的 DOI 或 PubMed 链接。"]

但仓库里**从来没有 papers/ 这个目录**。后果是：任何人在站内搜索里搜到
「论文索引」并点进去，得到的是 GitHub Pages 的 404 —— 一条由自家搜索
结果直接产出的死链，而且因为 `check-links.py` 只校验 HTML 里的链接、
不校验 `search-index.json` 的条目，它藏了整整一周没人发现。

处理方式有两条路：删掉那条索引条目（诚实但丢掉一个研究者真正需要的工具），
或把页面真的建出来（兑现承诺）。选后者 —— 对一个做文献工作的站来说，
「按 DOI 汇总的全站文献总表」本来就是这个站最该有的东西：

  · 每篇解读都能回溯到原始文献（DOI 直连 doi.org）
  · 可按证据等级筛（A 人体 / B 临床前 / C 预印本）
  · 可一键下载 CSV 进 Excel/Zotero 继续整理

数据口径（严禁发明）
────────────────────
· 全部条目来自 `data/articles.json`，一篇不多、一篇不少
· DOI 只抄 `doi` 字段原值，不做任何猜测性补全；缺 DOI 的篇目如实显示「—」，
  并在表头说明「该类多为预印本 / 行业动态，来源见原文页」
· 覆盖率、分级分布等统计数字全部由数据现算，不写死

幂等：产物完全由 articles.json 决定，可反复运行。
"""
import csv
import html
import json
import os
import sys
from collections import Counter

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
OUT_DIR = os.path.join(ROOT, "papers")

SITE = "https://longbiosci.com"

HEAD = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>论文索引（可溯源 DOI） — LongBiosci</title>
<meta name="description" content="全站 {total} 篇研究解读的原始文献总表，其中 {with_doi} 篇给出可直接访问的 DOI 链接。可按证据等级（A 人体 / B 临床前 / C 预印本）筛选，支持关键词检索与 CSV 下载。">
<link rel="canonical" href="https://longbiosci.com/papers/">
<meta name="robots" content="index, follow">
<meta property="og:type" content="website">
<meta property="og:url" content="https://longbiosci.com/papers/">
<meta property="og:title" content="论文索引（可溯源 DOI） — LongBiosci">
<meta property="og:description" content="全站研究解读的原始文献总表，每篇给出 DOI 或原文链接，可按证据等级筛选并导出 CSV。">
<meta property="og:image" content="https://longbiosci.com/og-image.png">
<meta property="og:site_name" content="LongBiosci">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="论文索引（可溯源 DOI）">
<meta name="twitter:description" content="全站研究解读的原始文献总表，每篇给出 DOI 或原文链接。">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="icon" type="image/svg+xml" href="/favicon-dark.svg" media="(prefers-color-scheme: dark)">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">
{jsonld}
</script>
<!-- longbiosci:analytics 无 Cookie、无跨站追踪、不收集身份信息；详见 /privacy/ -->
<script defer src="https://cloud.umami.is/script.js" data-website-id="bfb60723-d93d-4925-b1a2-d7ef51b9014c" data-do-not-track="true"></script>
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
      <a href="/podcast/" aria-label="播客">播<span class="nav-mq">客</span></a>
      <a href="/about/">关于</a>
      <a href="/search.html" class="nav-search" aria-label="站内搜索"><svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true" focusable="false"><circle cx="6.8" cy="6.8" r="4.6" fill="none" stroke="currentColor" stroke-width="1.6"/><line x1="10.3" y1="10.3" x2="14" y2="14" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg><span class="nav-search-text">搜索</span></a>
    </nav>
  </div>
</header>
'''

FOOTER = '''</main>
<footer class="site-footer">
  <div class="wrap">
    <p>© 2026 LongBiosci · 衰老与长寿科技资讯</p>
    <a href="/rss.xml">RSS</a> · <a href="/sitemap.xml">Sitemap</a> · <a href="/privacy/">隐私政策</a> · <a href="/about/">关于</a>
  </div>
</footer>
</body>
</html>
'''

EXTRA_CSS = '''<style>
.papers-tools{display:flex;flex-wrap:wrap;gap:var(--s-3);align-items:center;margin-bottom:var(--s-4)}
.papers-tools .search-input{flex:1 1 260px;width:auto}
.papers-table-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch;border:1px solid var(--c-line);border-radius:var(--r-md)}
.papers-table{width:100%;border-collapse:collapse;font-size:var(--f-sm);min-width:680px}
.papers-table th,.papers-table td{border-bottom:1px solid var(--c-line);padding:var(--s-2) var(--s-3);text-align:left;vertical-align:top}
.papers-table thead th{background:var(--c-bg-sunken);font-weight:600;position:sticky;top:0;z-index:1;white-space:nowrap}
.papers-table tbody tr:hover{background:var(--c-bg-sunken)}
.papers-table td.p-date{white-space:nowrap;color:var(--c-muted);font-variant-numeric:tabular-nums}
.papers-table td .p-sub{display:block;font-size:var(--f-xs);color:var(--c-faint);margin-top:2px}
.papers-table td.p-doi{white-space:nowrap;font-size:var(--f-xs)}
.papers-table .p-nodoi{color:var(--c-faint)}
.papers-table a{color:var(--c-primary)}
.papers-empty{color:var(--c-muted);padding:var(--s-5) 0}
@media(max-width:600px){.papers-table{min-width:560px}}
</style>
'''


def esc(s):
    return html.escape(str(s or ""), quote=True)


def clean_slug(a):
    s = str(a.get("slug") or "").strip()
    return s.lstrip("/")


def main():
    aj = os.path.join(ROOT, "data", "articles.json")
    if not os.path.exists(aj):
        print(f"找不到 {aj}", file=sys.stderr)
        return 1
    arts = json.load(open(aj, encoding="utf-8"))

    # 排序：日期倒序，同日按 slug 升序（确定性，保证产物可逐字节比对）
    arts = sorted(arts, key=lambda a: (a.get("date") or "", clean_slug(a)), reverse=True)

    total = len(arts)
    with_doi = [a for a in arts if str(a.get("doi") or "").strip()]
    n_doi = len(with_doi)
    pct = (n_doi / total * 100) if total else 0.0
    tiers = Counter((a.get("evidence") or "—").upper() for a in arts)
    topics = Counter(a.get("topic") or "未分类" for a in arts)

    os.makedirs(OUT_DIR, exist_ok=True)

    # ---------- CSV（Excel 友好：带 BOM） ----------
    csv_path = os.path.join(OUT_DIR, "papers.csv")
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["日期", "标题", "主题", "类型", "证据等级", "DOI", "DOI 链接",
                    "来源", "站内解读页"])
        for a in arts:
            doi = str(a.get("doi") or "").strip()
            slug = clean_slug(a)
            w.writerow([
                a.get("date", ""), a.get("title", ""), a.get("topic", ""),
                a.get("type", ""), a.get("evidence", ""), doi,
                f"https://doi.org/{doi}" if doi else "",
                a.get("source", ""),
                f"{SITE}/news/{slug}" if slug else "",
            ])

    # ---------- 表格 ----------
    rows = []
    for a in arts:
        doi = str(a.get("doi") or "").strip()
        slug = clean_slug(a)
        title = a.get("title") or "(无标题)"
        topic = a.get("topic") or ""
        typ = a.get("type") or ""
        tier = (a.get("evidence") or "").upper()
        date = a.get("date") or ""
        # 注意：不再把标题塞进 data-s 属性 —— 那会让每行多出上百字节，
        # 587 行就是 100 KB 的重复文本。过滤改为运行时读 textContent（见脚本末尾 JS）。

        doi_cell = (f'<a href="https://doi.org/{esc(doi)}" target="_blank" '
                    f'rel="noopener noreferrer">{esc(doi)}</a>') if doi \
            else '<span class="p-nodoi">—</span>'
        tier_cell = (f'<span class="tier tier-{esc(tier.lower())}">{esc(tier)}</span>'
                     if tier in ("A", "B", "C") else "—")
        rows.append(
            f'<tr data-e="{esc(tier)}" data-d="{1 if doi else 0}">'
            f'<td class="p-date">{esc(date)}</td>'
            f'<td><a href="/news/{esc(slug)}">{esc(title)}</a>'
            f'<span class="p-sub">{esc(topic)}{(" · " + esc(typ)) if typ else ""}</span></td>'
            f'<td>{tier_cell}</td>'
            f'<td class="p-doi">{doi_cell}</td>'
            f'</tr>'
        )

    jsonld = json.dumps({
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": "论文索引（可溯源 DOI）",
        "description": f"全站 {total} 篇研究解读的原始文献总表，其中 {n_doi} 篇给出可直接访问的 DOI 链接。",
        "url": "https://longbiosci.com/papers/",
        "inLanguage": "zh-CN",
        "isPartOf": {"@type": "WebSite", "name": "LongBiosci",
                     "url": "https://longbiosci.com/"},
    }, ensure_ascii=False, indent=2)

    body = [
        BODY_HEADER,
        '<main id="main-content">',
        '<section class="hero"><div class="wrap">',
        "<h1>论文索引（可溯源 DOI）</h1>",
        f'<p>全站 <strong>{total}</strong> 篇研究解读对应的原始文献总表，'
        f'其中 <strong>{n_doi}</strong> 篇（{pct:.1f}%）可直接跳到 doi.org 取原文。'
        "按时间倒序排列，可按证据等级筛选、按关键词（标题 / DOI / 主题）检索。</p>",
        '</div></section>',
        '<section class="section"><div class="wrap">',
        '<div class="notice-box">',
        "<p><strong>这张表怎么用</strong></p>",
        "<p>做综述时按<strong>主题</strong>或<strong>证据等级</strong>过滤，先拿到候选清单，"
        "再点标题进解读页看方法与局限；需要进 Zotero / Excel 继续整理，"
        '用下方的 <a href="/papers/papers.csv">CSV 下载</a>（含 DOI、来源、站内链接，Excel 可直接打开）。</p>',
        f'<p><strong>关于那 {total - n_doi} 篇没有 DOI 的条目</strong>：多为预印本（'
        "BioRxiv / MedRxiv 的 DOI 形如 10.64898/… 者已收录）与行业动态、观点评论类内容，"
        "原始来源写在各自的解读页「来源」一栏，本表不代为补全 —— 没有的 DOI 就是不写。</p>",
        '</div>',
        '<div class="papers-tools">',
        '<label class="sr-only" for="pq">按标题、DOI 或主题检索</label>',
        '<input type="search" id="pq" class="search-input" autocomplete="off" '
        'placeholder="检索标题 / DOI / 主题…">',
        f'<a href="/papers/papers.csv" class="filter" role="button">↓ 下载 CSV（{total} 条）</a>',
        '</div>',
        '<div class="filter-bar" role="group" aria-label="按证据等级筛选">',
        '<button class="filter" type="button" data-e="all" aria-pressed="true">全部 '
        f'{total}</button>',
        f'<button class="filter" type="button" data-e="A" aria-pressed="false">A 人体 {tiers.get("A", 0)}</button>',
        f'<button class="filter" type="button" data-e="B" aria-pressed="false">B 临床前 {tiers.get("B", 0)}</button>',
        f'<button class="filter" type="button" data-e="C" aria-pressed="false">C 预印本 {tiers.get("C", 0)}</button>',
        '<button class="filter" type="button" data-e="doi" aria-pressed="false">'
        f'仅看有 DOI {n_doi}</button>',
        '</div>',
        '<p class="search-meta" id="pstatus" aria-live="polite">'
        f'共 {total} 条，当前显示 {total} 条</p>',
        EXTRA_CSS,
        '<div class="papers-table-wrap">',
        '<table class="papers-table" id="ptable">',
        "<thead><tr><th>日期</th><th>标题 / 主题</th><th>证据</th><th>DOI</th></tr></thead>",
        "<tbody>",
    ]
    body.extend(rows)
    body.extend([
        "</tbody></table>",
        "</div>",
        '<p class="papers-empty" id="pempty" hidden>没有匹配的条目，换个关键词试试。</p>',
        "</div></section>",
    ])

    # 统计小节（主题分布，给读者一个「这个站在覆盖什么」的轮廓）
    top_topics = topics.most_common(8)
    body.append('<section class="section"><div class="wrap">')
    body.append("<h2>主题分布</h2>")
    body.append('<div class="topic-grid">')
    for name, n in top_topics:
        body.append(f'<div class="topic-card"><span class="t-name">{esc(name)}</span>'
                    f'<span class="t-count">{n} 条</span></div>')
    body.append("</div>")
    body.append('<p style="margin-top:1.5rem;font-size:0.92rem;color:var(--c-muted)">'
                '完整分类见 <a href="/topics/">主题专辑</a>；按干预手段看见 '
                '<a href="/research/">概念与工具</a>；只想要最强证据，见 '
                '<a href="/evidence/A.html">A 级清单</a>。</p>')
    body.append("</div></section>")

    js = '''<script>
(function(){
  var rows = Array.prototype.slice.call(document.querySelectorAll('#ptable tbody tr'));
  var hay = null;   // 懒构建：首行 textContent 拼接，避免在 HTML 里重复存一份标题
  var q = document.getElementById('pq');
  var status = document.getElementById('pstatus');
  var empty = document.getElementById('pempty');
  var chips = Array.prototype.slice.call(document.querySelectorAll('.filter[data-e]'));
  var mode = 'all';
  var total = rows.length;

  function apply(){
    var term = (q.value || '').trim().toLowerCase();
    if (term && !hay) hay = rows.map(function(r){ return (r.textContent || '').toLowerCase(); });
    var shown = 0;
    for (var i = 0; i < rows.length; i++){
      var r = rows[i];
      var ok = true;
      if (mode === 'doi') ok = r.getAttribute('data-d') === '1';
      else if (mode !== 'all') ok = r.getAttribute('data-e') === mode;
      if (ok && term) ok = (hay ? hay[i] : '').indexOf(term) !== -1;
      r.hidden = !ok;
      if (ok) shown++;
    }
    status.textContent = '共 ' + total + ' 条，当前显示 ' + shown + ' 条';
    empty.hidden = shown !== 0;
  }

  q.addEventListener('input', apply);
  chips.forEach(function(c){
    c.addEventListener('click', function(){
      mode = c.getAttribute('data-e');
      chips.forEach(function(x){ x.setAttribute('aria-pressed', x === c ? 'true' : 'false'); });
      apply();
    });
  });
})();
</script>
'''

    html_out = (HEAD.format(total=total, with_doi=n_doi, jsonld=jsonld)
                + ''.join(body) + js + FOOTER)
    out_path = os.path.join(OUT_DIR, "index.html")
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        f.write(html_out)

    print(f"papers/index.html: {total} 条 / 有 DOI {n_doi} 条（{pct:.1f}%）"
          f" · A{tiers.get('A', 0)}/B{tiers.get('B', 0)}/C{tiers.get('C', 0)}"
          f" · {len(html_out) / 1024:.0f} KB")
    print(f"papers/papers.csv: {total} 行 × 9 列（UTF-8 BOM，Excel 可直接打开）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
