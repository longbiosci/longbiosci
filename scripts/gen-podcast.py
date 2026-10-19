#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen-podcast.py —— 播客板块生成器（管线第 8 环节，2026-10-19 新增）

事实源：data/podcast.json（schema 1）+ podcast/transcripts/<slug>.md（文字稿）
产物：
  /podcast/index.html   节目列表页（按系列分组：播放器 + 文字稿 + 来源清单 + 站内延伸阅读）
  podcast.xml           RSS 2.0 + iTunes 扩展（Apple Podcasts / Spotify / 小宇宙通用）

硬规则（与产业事件流同源，杜绝播客凭空杜撰）：
  1. 每期必须带 sources——缺来源的期目告警并跳过；
  2. 每期的 audio 文件必须存在——音频是发布物不是构建物（见 synth_podcast_audio.py），
     文件缺失说明合成漏跑，同样跳过；
  3. article_slugs 指向的站内文章必须存在——缺失则丢弃该链接并告警（不静默）；
  4. duration_sec 以合成时 ffprobe 实测值回填，本脚本只展示、不推算。

页面不重新合成音频：本环节可在任何网络状况下确定性重跑。
author: LongBiosci 网站运营自动化
"""
import html
import json
import os
import re
import sys
from datetime import datetime, timezone
from email.utils import format_datetime

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DATA = os.path.join(REPO, "data", "podcast.json")
TRANSCRIPT_DIR = "podcast/transcripts"
OUT_DIR = os.path.join(REPO, "podcast")
RSS_PATH = os.path.join(REPO, "podcast.xml")
BASE = "https://longbiosci.com"

SERIES_ORDER = ["论文精读", "机制十分钟", "打假与证伪", "产业脉搏"]

# ---------------------------------------------------------------- 页面骨架

HEAD = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canonical}">
<meta name="robots" content="index, follow">
<meta property="og:type" content="website">
<meta property="og:url" content="{canonical}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="https://longbiosci.com/podcast-cover.png">
<meta property="og:site_name" content="LongBiosci">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<link rel="alternate" type="application/rss+xml" title="LongBiosci 播客 RSS" href="/podcast.xml">
<link rel="alternate" type="application/rss+xml" title="LongBiosci 全站 RSS" href="/rss.xml">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="stylesheet" href="/style.css">
<style>
.pod-hero-cover{{width:min(220px,42vw);border-radius:var(--r-lg);
  border:1px solid var(--c-line);display:block;margin:0 auto var(--s-5)}}
.pod-meta{{display:flex;gap:var(--s-4);flex-wrap:wrap;align-items:center;
  justify-content:center;font-size:var(--f-sm);color:var(--c-muted);margin-top:var(--s-4)}}
.pod-meta a{{color:var(--c-primary)}}
.pod-disclaimer{{max-width:46rem;margin:var(--s-4) auto 0;padding:var(--s-3) var(--s-4);
  background:var(--c-surface);border:1px solid var(--c-line);border-radius:var(--r-md);
  font-size:var(--f-xs);color:var(--c-muted);text-align:center}}
.series-head{{display:flex;align-items:baseline;gap:var(--s-3);margin:var(--s-6) 0 var(--s-3)}}
.series-head h2{{font-size:var(--f-lg);margin:0}}
.series-count{{font-size:var(--f-xs);color:var(--c-muted)}}
.ep-card{{background:var(--c-bg-raised);border:1px solid var(--c-line);
  border-radius:var(--r-lg);padding:var(--s-4);margin-bottom:var(--s-4)}}
.ep-top{{display:flex;gap:var(--s-3);align-items:baseline;flex-wrap:wrap}}
.ep-title{{font-weight:600;font-size:var(--f-md);flex:1;min-width:16rem}}
.ep-date{{font-size:var(--f-xs);color:var(--c-muted);font-variant-numeric:tabular-nums}}
.ep-dur{{font-size:var(--f-xs);color:var(--c-muted);font-variant-numeric:tabular-nums}}
.ep-desc{{font-size:var(--f-sm);color:var(--c-muted);margin:var(--s-3) 0}}
.ep-card audio{{width:100%;margin:var(--s-2) 0 var(--s-4)}}
.ep-block-title{{font-weight:600;font-size:var(--f-sm);margin:var(--s-4) 0 var(--s-2)}}
.pod-transcript p{{font-size:var(--f-sm);margin:0 0 var(--s-3);line-height:1.75}}
.pod-src{{list-style:none;padding:0;margin:0}}
.pod-src li{{font-size:var(--f-sm);padding:.4rem 0;border-bottom:1px solid var(--c-line)}}
.pod-src li:last-child{{border-bottom:none}}
.pod-src .src-note{{color:var(--c-muted);font-size:var(--f-xs)}}
.pod-rel{{display:flex;flex-direction:column;gap:.4rem}}
.pod-rel a{{font-size:var(--f-sm)}}
.pod-rel .rel-date{{color:var(--c-muted);font-size:var(--f-xs);margin-left:.5rem}}
</style>
</head>
<body>
'''

NAV = '''<header class="site-header">
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

FOOTER = '''</main><footer class="site-footer">
  <div class="wrap">
    <p>© 2026 LongBiosci 编辑部 · 衰老与长寿科技资讯</p>
    <p class="footer-links">
      <a href="/rss.xml">RSS</a> ·
      匿名访问统计由 <a href="https://umami.is" rel="noopener">Umami</a> 提供（无 Cookie、不收集身份信息，详见 <a href="/privacy/">隐私政策</a>） ·
      <a href="/podcast.xml">播客 RSS</a> ·
      <a href="/sitemap.xml">Sitemap</a> ·
      <a href="/privacy/">隐私政策</a> ·
      <a href="/about/">关于</a>
    </p>
  </div>
</footer>
</body>
</html>
'''

# ---------------------------------------------------------------- 工具


def esc(s):
    return html.escape(str(s), quote=True)


def fmt_dur(sec):
    m, s = divmod(int(sec), 60)
    return "%d 分 %02d 秒" % (m, s) if m else "%d 秒" % s


def load_articles():
    """文章标题索引：slug → (title, date)。延伸阅读链接用。"""
    path = os.path.join(REPO, "data", "articles.json")
    try:
        d = json.load(open(path, encoding="utf-8"))
    except FileNotFoundError:
        return {}
    arts = d if isinstance(d, list) else d.get("articles", [])
    idx = {}
    for a in arts:
        sl = a.get("slug", "")
        if not sl:
            continue
        idx[sl] = a                      # 登记原样（不带目录前缀）
        idx["news/" + sl] = a            # 兼容带 news/ 前缀的引用
    return idx


def read_transcript(slug):
    """读文字稿 → (口播正文 HTML, 是否找到)。`#` 行不渲染为口播文本。"""
    path = os.path.join(REPO, TRANSCRIPT_DIR, slug + ".md")
    if not os.path.exists(path):
        return None
    s = open(path, encoding="utf-8").read()
    s = re.sub(r"^---\s*\n.*?\n---\s*\n", "", s, flags=re.S)
    out = []
    for para in re.split(r"\n\s*\n", s):
        para = para.strip()
        if not para:
            continue
        # 段落内若是标题行则跳过（标题只在文稿文件里有意义）
        if all(l.lstrip().startswith("#") for l in para.splitlines()):
            continue
        # 段内混排：标题行滤掉，其余行合成一段
        lines = [l for l in para.splitlines() if not l.lstrip().startswith("#")]
        text = esc(" ".join(lines))
        out.append("<p>%s</p>" % text)
    return "".join(out) if out else None


# ---------------------------------------------------------------- 校验

def validate(show, episodes, articles):
    """返回 (可用期目列表, 错误列表)。缺来源/缺音频 → 跳过并记录。"""
    ok, errs = [], []
    for ep in episodes:
        slug = ep.get("slug", "?")
        if not ep.get("sources"):
            errs.append("期目 %s：无 sources，跳过（播客内容必须带来源）" % slug)
            continue
        audio_rel = ep.get("audio", "")
        if not audio_rel or not os.path.exists(os.path.join(REPO, audio_rel)):
            errs.append("期目 %s：音频文件缺失（%s），跳过" % (slug, audio_rel))
            continue
        if not ep.get("title") or not ep.get("date"):
            errs.append("期目 %s：缺 title/date，跳过" % slug)
            continue
        # 站内文章链接：缺失则丢弃并告警（不静默）
        kept = []
        for s in ep.get("article_slugs", []):
            if s in articles:
                kept.append(s)
            else:
                errs.append("期目 %s：站内文章 %s 不存在，已丢弃该链接" % (slug, s))
        ep["article_slugs"] = kept
        if not ep.get("duration_sec"):
            errs.append("期目 %s：duration_sec 未回填（ffprobe 实测值），展示将显示 0" % slug)
        ok.append(ep)
    return ok, errs


# ---------------------------------------------------------------- /podcast/ 页面

def render_episode(ep, articles):
    slug = ep["slug"]
    audio_url = "/" + ep["audio"].lstrip("/")
    dur = ep.get("duration_sec") or 0
    date_cn = ep.get("date", "")
    try:
        date_cn = datetime.strptime(ep["date"], "%Y-%m-%d").strftime("%Y 年 %m 月 %d 日")
    except ValueError:
        pass

    transcript = read_transcript(slug)
    transcript_html = ('<div class="pod-transcript">%s</div>' % transcript
                       if transcript else
                       '<p style="font-size:var(--f-sm);color:var(--c-muted)">文字稿整理中。</p>')

    src_items = []
    for s in ep.get("sources", []):
        label = esc(s.get("label", ""))
        doi = s.get("doi", "")
        pmid = s.get("pmid", "")
        url = s.get("url", "")
        note = s.get("note", "")
        bits = []
        if url:
            bits.append('<a href="%s" rel="noopener">原文链接</a>' % esc(url))
        if doi:
            bits.append("DOI %s" % esc(doi))
        if pmid:
            bits.append("PubMed %s" % esc(pmid))
        line = " · ".join(bits)
        if note:
            line += ' <span class="src-note">%s</span>' % esc(note)
        src_items.append('<li>%s%s</li>' % (label, ("<br>" + line) if line else ""))

    rel_items = []
    for s in ep.get("article_slugs", []):
        a = articles[s]
        bare = s[len("news/"):] if s.startswith("news/") else s
        rel_items.append('<a href="/news/%s">%s<span class="rel-date">%s</span></a>'
                         % (esc(bare), esc(a.get("title", bare)), esc(a.get("date", ""))))

    return f'''<article class="ep-card" id="{esc(ep.get('id', slug))}">
  <div class="ep-top">
    <span class="ep-title">{esc(ep['title'])}</span>
    <span class="ep-date">{esc(date_cn)}</span>
    <span class="ep-dur">时长 {esc(fmt_dur(dur))}</span>
  </div>
  <p class="ep-desc">{esc(ep.get('desc', ''))}</p>
  <audio controls preload="none" src="{audio_url}">
    您的浏览器不支持音频播放，请下载 <a href="{audio_url}">MP3 文件</a>。
  </audio>
  <div class="ep-block-title">来源清单</div>
  <ul class="pod-src">{''.join(src_items)}</ul>
  <div class="ep-block-title">站内延伸阅读</div>
  <div class="pod-rel">{''.join(rel_items) or '<span style="font-size:var(--f-sm);color:var(--c-muted)">暂无</span>'}</div>
  <div class="ep-block-title">完整文字稿</div>
  {transcript_html}
</article>'''


def render_page(show, episodes, articles):
    by_series = {}
    for ep in episodes:
        by_series.setdefault(ep.get("series", "其他"), []).append(ep)

    blocks = []
    for series in SERIES_ORDER + [s for s in by_series if s not in SERIES_ORDER]:
        eps = by_series.get(series)
        if not eps:
            continue
        eps = sorted(eps, key=lambda e: e.get("date", ""), reverse=True)
        blocks.append(
            '<div class="series-head"><h2>%s</h2><span class="series-count">%d 期</span></div>'
            % (esc(series), len(eps)))
        blocks.extend(render_episode(ep, articles) for ep in eps)

    stats = ('<div class="stat-row">'
             + "".join('<div><div class="stat-n">%d</div><div class="stat-l">%s</div></div>'
                       % (len(episodes), esc("已播期目")))
             + "".join('<div><div class="stat-n">%d</div><div class="stat-l">%s</div></div>'
                       % (len(by_series), esc("系列")))
             + "</div>")

    title = "%s - LongBiosci 播客" % show.get("title", "播客")
    desc = show.get("tagline", "")
    body = (f'<img class="pod-hero-cover" src="/podcast-cover.png" '
            f'alt="{esc(show.get("title", ""))} 封面" width="220" height="220">\n'
            f'<div class="pod-meta">'
            f'<span>{esc(show.get("author", ""))}</span>'
            f'<span>·</span><a href="/podcast.xml">RSS 订阅</a>'
            f'<span>·</span><a href="https://podcasts.apple.com/" rel="noopener">Apple Podcasts</a>'
            f'<span>·</span><a href="https://open.spotify.com/" rel="noopener">Spotify</a>'
            f'</div>\n'
            f'<div class="pod-disclaimer">{esc(show.get("disclaimer", ""))}</div>\n')
    return (HEAD.format(title=esc(title), desc=esc(desc), canonical=BASE + "/podcast/")
            + NAV
            + '<main id="main-content">\n<section class="hero"><div class="wrap">\n'
            + f'<h1>{esc(show.get("title", ""))}</h1>\n<p>{esc(desc)}</p>\n'
            + stats + body
            + '</div></section>\n<section class="section"><div class="wrap">\n'
            + "".join(blocks)
            + '</div></section>\n' + FOOTER)


# ---------------------------------------------------------------- podcast.xml

def cdata(s):
    return "<![CDATA[%s]]>" % str(s).replace("]]>", "]]]]><![CDATA[>")


def render_rss(show, episodes, articles):
    items = []
    for ep in sorted(episodes, key=lambda e: e.get("date", ""), reverse=True):
        slug = ep["slug"]
        audio_abs = BASE + "/" + ep["audio"].lstrip("/")
        try:
            size = os.path.getsize(os.path.join(REPO, ep["audio"]))
        except OSError:
            size = 0
        try:
            dt = datetime.strptime(ep["date"] + " 00:00:00", "%Y-%m-%d %H:%M:%S").replace(
                tzinfo=timezone.utc)
            pub = format_datetime(dt)
        except ValueError:
            pub = format_datetime(datetime.now(timezone.utc))

        # RSS description：摘要 + 来源 + 站内文章（纯文本，平台兼容性最好）
        lines = [ep.get("desc", ""), "", "来源："]
        for s in ep.get("sources", []):
            extra = []
            if s.get("doi"):
                extra.append("DOI " + s["doi"])
            if s.get("pmid"):
                extra.append("PubMed " + s["pmid"])
            lines.append("· " + s.get("label", "") + ("（" + "；".join(extra) + "）" if extra else ""))
            if s.get("note"):
                lines.append("  注：" + s["note"])
        if ep.get("article_slugs"):
            lines += ["", "站内延伸阅读："]
            for s in ep["article_slugs"]:
                a = articles.get(s, {})
                bare = s[len("news/"):] if s.startswith("news/") else s
                lines.append("· %s %s" % (a.get("title", bare), BASE + "/news/" + bare))
        lines += ["", show.get("disclaimer", ""), "", "完整文字稿：%s/podcast/#%s" % (BASE, ep.get("id", slug))]
        desc_text = "\n".join(lines)

        items.append(f'''  <item>
    <title>{esc(ep["title"])}</title>
    <link>{BASE}/podcast/#{esc(ep.get("id", slug))}</link>
    <guid isPermaLink="false">longbiosci-podcast-{esc(ep.get("id", slug))}</guid>
    <pubDate>{pub}</pubDate>
    <category>{esc(ep.get("series", ""))}</category>
    <description>{cdata(desc_text)}</description>
    <enclosure url="{audio_abs}" length="{size}" type="audio/mpeg"/>
    <itunes:duration>{int(ep.get("duration_sec") or 0)}</itunes:duration>
    <itunes:episodeType>full</itunes:episodeType>
    <itunes:author>{esc(show.get("author", ""))}</itunes:author>
    <itunes:summary>{cdata(ep.get("desc", ""))}</itunes:summary>
  </item>''')

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
     xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
     xmlns:content="http://purl.org/rss/1.0/modules/content/">
<channel>
  <title>{esc(show.get("title", ""))}</title>
  <link>{esc(show.get("site_url", BASE + "/podcast/"))}</link>
  <language>{esc(show.get("language", "zh-cn"))}</language>
  <copyright>{esc(show.get("copyright", ""))}</copyright>
  <description>{cdata(show.get("tagline", "") + " " + show.get("disclaimer", ""))}</description>
  <itunes:author>{esc(show.get("author", ""))}</itunes:author>
  <itunes:summary>{cdata(show.get("tagline", ""))}</itunes:summary>
  <itunes:owner>
    <itunes:name>{esc(show.get("author", ""))}</itunes:name>
    <itunes:email>{esc(show.get("email", ""))}</itunes:email>
  </itunes:owner>
  <itunes:image href="{esc(show.get("cover", BASE + "/podcast-cover.png"))}"/>
  <image>
    <url>{esc(show.get("cover", BASE + "/podcast-cover.png"))}</url>
    <title>{esc(show.get("title", ""))}</title>
    <link>{esc(show.get("site_url", BASE + "/podcast/"))}</link>
  </image>
  <itunes:category text="{esc(show.get("category", "Science"))}"/>
  <itunes:explicit>{'yes' if show.get("explicit") else 'no'}</itunes:explicit>
{chr(10).join(items)}
</channel>
</rss>
'''


# ---------------------------------------------------------------- main

def main():
    root = sys.argv[1] if len(sys.argv) > 1 else REPO
    data = json.load(open(DATA, encoding="utf-8"))
    show = data.get("show", {})
    episodes = data.get("episodes", [])
    articles = load_articles()

    ok, errs = validate(show, episodes, articles)
    for e in errs:
        print("  ⚠️ " + e)
    if not ok:
        print("  ❌ 无可用期目，podcast.xml 不生成")
        sys.exit(1)

    os.makedirs(OUT_DIR, exist_ok=True)
    page = render_page(show, ok, articles)
    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)
    print("  ✅ podcast/index.html（%d 期）" % len(ok))

    rss = render_rss(show, ok, articles)
    with open(RSS_PATH, "w", encoding="utf-8") as f:
        f.write(rss)
    print("  ✅ podcast.xml（RSS 2.0 + iTunes，%d 个 item）" % len(ok))


if __name__ == "__main__":
    main()
