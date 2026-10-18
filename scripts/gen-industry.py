#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen-industry.py —— 产业板块生成器（管线第 14 环节）

用法：python3 scripts/gen-industry.py <仓库根目录>

为什么要有这个生成器
──────────────────
/companies/、/investors/、/events/ 此前都是**手写静态页**：无数据源、无生成器、
不在管线内，git 历史各仅 1~2 次提交。2026-10-18 全站审计时查出：

  · companies 14 条中 6 处不可信断言（Altos 杜撰创始人、NewLimit 技术与资方双错、
    Sirtris 收购年份、CohBar / Amino 收购查无实据、Calico 人名）
  · investors 5 条中 3 条有问题（Peter Berg 实为 Peter Thiel、
    Tony Wyss 身份错配、"Krispy Kreme 家族办公室"查无实据）
  · events 8 场会议日期手写，2026-10-15 的 AGE 年会已过期仍在展示

根因不是"写错了"，而是**这些页面承载会变的事实，却没有数据源**。
手写进去的那天就是错误的开始，且没有任何环节会发现。

本脚本与 data/industry.json 一起重建这一板块：
  · **事件流驱动** —— companies 只存不随时间变的属性（名称、方向）；
    融资额、收购、监管、临床进展一律来自 events
  · **每条事件必带 source**，无来源进不了库（生成器对缺 source 的事件告警并跳过）
  · 三个页面全部由数据生成，新增情报只需往 industry.json 加一条事件

产物：
  /industry/index.html   事件流主页（时间线 + 类型分布 + 公司入口 + 会议入口）
  /companies/index.html  公司档案（由 events 按 entity 聚合）
  /events/index.html     会议日历（按当前日期自动标注「已结束」，只收有来源的）
  /investors/index.html  出资人名录（只收能给公开来源的，附官方链接）

幂等：可反复运行，产物由数据唯一决定。
"""
import html
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import date

# 事件类型展示顺序（决定主页分组与筛选顺序）
TYPE_ORDER = ["融资", "收购", "合作", "临床", "监管", "管线",
              "产品", "商业化", "奖项", "会议", "行业观察"]

EVIDENCE_LABEL = {"A": "A 人体研究", "B": "B 临床前", "C": "C 预印本"}

STATUS_LABEL = {
    "active":   ("活跃", "status-active"),
    "archived": ("已被收购", "status-acquired"),
    "unknown":  ("状态待溯源", "status-unknown"),
}


def esc(s):
    return html.escape(str(s or ""), quote=True)


def amount_val(a):
    """把「27.5 亿美元 / 3600 万美元」折算成亿美元，仅用于排序；原文字照样展示。"""
    if not a:
        return 0.0
    m = re.search(r"([\d.]+)\s*亿美元", str(a))
    if m:
        return float(m.group(1))
    m = re.search(r"([\d.]+)\s*万美元", str(a))
    if m:
        return float(m.group(1)) / 10000.0
    return 0.0


def amount_kind(a):
    """金额口径：里程碑/合作总额是协议上限，估值是定价，都不是已到手的钱。"""
    s = str(a or "")
    if "估值" in s:
        return "估值"
    if any(k in s for k in ("最高", "里程碑", "总额", "超")):
        return "协议上限"
    return "披露金额"


HEAD = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} - LongBiosci</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="https://longbiosci.com{canonical}">
<meta name="robots" content="index, follow">
<meta property="og:type" content="website">
<meta property="og:url" content="https://longbiosci.com{canonical}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="https://longbiosci.com/og-image.png">
<meta property="og:site_name" content="LongBiosci">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<link rel="alternate" type="application/rss+xml" title="LongBiosci RSS" href="/rss.xml">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="stylesheet" href="/style.css">
<style>
.stat-row{{display:flex;gap:var(--s-5);flex-wrap:wrap;margin:var(--s-4) 0 0;
  padding-top:var(--s-4);border-top:1px solid var(--c-line)}}
.stat-n{{font-size:var(--f-xl);font-weight:600;color:var(--c-primary);
  font-variant-numeric:tabular-nums;line-height:1.2}}
.stat-l{{font-size:var(--f-xs);color:var(--c-muted)}}
.entity-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(320px,100%),1fr));gap:var(--s-4)}}
.entity-card{{background:var(--c-bg-raised);border:1px solid var(--c-line);
  border-radius:var(--r-lg);padding:var(--s-4)}}
.entity-logo{{width:2.2rem;height:2.2rem;border-radius:var(--r-md);display:flex;
  align-items:center;justify-content:center;font-weight:700;font-size:var(--f-sm);
  background:var(--c-surface);color:var(--c-primary);margin-bottom:.6rem}}
.entity-name{{font-weight:600;font-size:var(--f-md)}}
.entity-desc{{font-size:var(--f-sm);color:var(--c-muted);margin:.4rem 0}}
.entity-tags{{display:flex;flex-wrap:wrap;gap:.3rem;margin-top:.4rem}}
.status-badge{{display:inline-flex;align-items:center;padding:1px 7px;
  border-radius:var(--r-pill);font-size:var(--f-xs);vertical-align:middle}}
.status-active{{background:var(--c-ev-a-bg);color:var(--c-ev-a)}}
.status-acquired{{background:#f1e8e0;color:#8a5a2b}}
.status-unknown{{background:#eceef0;color:#5c6570}}
@media (prefers-color-scheme:dark){{.status-acquired{{background:#2a1f16;color:#d4a07a}}}}
@media (prefers-color-scheme:dark){{.status-unknown{{background:#20242a;color:#a8b0ba}}}}
.tl{{border-left:2px solid var(--c-line);padding-left:var(--s-4);margin-top:var(--s-4)}}
.tl-item{{position:relative;padding:0 0 var(--s-5) 0}}
.tl-item::before{{content:"";position:absolute;left:calc(-1 * var(--s-4) - 5px);
  top:.5rem;width:8px;height:8px;border-radius:50%;background:var(--c-primary)}}
.tl-date{{font-size:var(--f-xs);color:var(--c-muted);font-variant-numeric:tabular-nums}}
.tl-name{{font-weight:600;margin:.15rem 0}}
.tl-desc{{font-size:var(--f-sm);color:var(--c-muted);margin-top:.25rem}}
.tl-meta{{display:flex;flex-wrap:wrap;gap:.4rem;align-items:center;
  font-size:var(--f-xs);color:var(--c-muted);margin-top:.25rem}}
.ev-amount{{font-weight:600;color:var(--c-primary)}}
.type-bar{{display:flex;flex-wrap:wrap;gap:.5rem;margin:var(--s-4) 0}}
.type-chip{{padding:3px 10px;border-radius:var(--r-pill);font-size:var(--f-xs);
  background:var(--c-surface);border:1px solid var(--c-line)}}
.deal-row{{display:flex;gap:var(--s-3);align-items:baseline;flex-wrap:wrap;
  padding:.55rem 0;border-bottom:1px solid var(--c-line)}}
.deal-row:last-child{{border-bottom:none}}
.deal-amt{{font-weight:600;color:var(--c-primary);font-variant-numeric:tabular-nums;
  min-width:8.5rem;font-size:var(--f-sm)}}
.deal-name{{flex:1;min-width:14rem;font-size:var(--f-sm)}}
.deal-meta{{font-size:var(--f-xs);color:var(--c-muted)}}
.track-block{{margin-top:var(--s-3)}}
.track-title{{font-weight:600;font-size:var(--f-sm);margin-bottom:.3rem}}
</style>
</head>
'''

NAV = '''<body>
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

FOOTER = '''</main><footer class="site-footer">
  <div class="wrap">
    <p>© 2026 LongBiosci 编辑部 · 衰老与长寿科技资讯</p>
    <p class="footer-links">
      <a href="/rss.xml">RSS</a> ·
      匿名访问统计由 <a href="https://umami.is" rel="noopener">Umami</a> 提供（无 Cookie、不收集身份信息，详见 <a href="/privacy/">隐私政策</a>） ·
      <a href="/sitemap.xml">Sitemap</a> ·
      <a href="/privacy/">隐私政策</a> ·
      <a href="/about/">关于</a>
    </p>
  </div>
</footer>
</body>
</html>
'''


def hero(h1, desc, stats=None, extra=""):
    stat = ""
    if stats:
        cells = "".join(
            f'<div><div class="stat-n">{n}</div><div class="stat-l">{esc(l)}</div></div>'
            for n, l in stats)
        stat = f'<div class="stat-row">{cells}</div>'
    return (f'<main id="main-content">\n<section class="hero"><div class="wrap">\n'
            f'<h1>{esc(h1)}</h1>\n<p>{desc}</p>\n{stat}{extra}\n'
            f'</div></section>\n')


def page(title, desc, canonical, cur_industry, hero_html, body_html):
    return (HEAD.format(title=esc(title), desc=esc(desc), canonical=canonical)
            + NAV.format(cur_industry=cur_industry)
            + hero_html
            + '<section class="section"><div class="wrap">\n' + body_html
            + '</div></section>\n' + FOOTER)


# ───────────────────────── 1. /industry/ 事件流主页 ─────────────────────────

def render_industry(evs, comps, invs, cons):
    cnt = Counter(e["type"] for e in evs)
    chips = "".join(
        f'<span class="type-chip">{esc(t)} {cnt[t]}</span>'
        for t in TYPE_ORDER if cnt.get(t))

    items = []
    for e in sorted(evs, key=lambda x: x["date"], reverse=True):
        meta = [f'<span class="tag">{esc(e["type"])}</span>']
        if e.get("entity"):
            meta.append(f'<span>{esc(e["entity"])}</span>')
        if e.get("amount"):
            rnd = (e.get("round") or "") + " " if e.get("round") else ""
            meta.append(f'<span class="ev-amount">{esc(rnd)}{esc(e["amount"])}</span>')
        if e.get("counterparty"):
            meta.append(f'<span>对方：{esc(e["counterparty"])}</span>')
        if e.get("evidence"):
            meta.append(f'<span>{esc(EVIDENCE_LABEL.get(e["evidence"], e["evidence"]))}</span>')
        meta.append(f'<span>来源：{esc(e.get("source") or "—")}</span>')

        title = e.get("headline") or e["id"]
        url = e.get("source_url") or ""
        name_html = (f'<a href="{esc(url)}">{esc(title)}</a>' if url
                     else esc(title))
        items.append(
            f'<div class="tl-item"><div class="tl-date">{esc(e["date"])}</div>'
            f'<div class="tl-name">{name_html}</div>'
            f'<div class="tl-meta">{"".join(meta)}</div></div>')

    timeline = ('<div class="section-head"><h2>事件时间线</h2>'
                '<a href="/companies/" class="section-more">按公司查看 →</a></div>'
                '<div class="tl">' + "".join(items) + '</div>')

    # 会议入口：只放还没开始的（已结束的留在 /events/ 归档）
    today = date.today().isoformat()
    upcoming = sorted([c for c in cons if c.get("start", "") >= today],
                      key=lambda x: x["start"])
    if upcoming:
        conf_items = "".join(
            f'<div class="tl-item"><div class="tl-date">{esc(c["start"])}'
            + (f' → {esc(c["end"])}' if c.get("end") else '') + '</div>'
            f'<div class="tl-name">{esc(c["name"])}</div>'
            f'<div class="tl-meta"><span class="tag">{esc(c.get("kind",""))}</span>'
            f'<span>{esc(c.get("place",""))}</span>'
            f'<span>来源：{esc(c.get("source",""))}</span></div></div>'
            for c in upcoming)
        conf = ('<div class="section-head" style="margin-top:2rem"><h2>即将召开的会议</h2>'
                '<a href="/events/" class="section-more">完整会议日历 →</a></div>'
                '<div class="tl">' + conf_items + '</div>')
    else:
        conf = ('<div class="section-head" style="margin-top:2rem"><h2>会议</h2>'
                '<a href="/events/" class="section-more">完整会议日历 →</a></div>'
                '<p style="font-size:var(--f-sm);color:var(--c-muted)">'
                '暂无已核实来源的待召开会议，'
                '<a href="/events/">查看完整日历</a>。</p>')

    # 公司入口：按关联事件数取前 6
    by_ent = defaultdict(int)
    for e in evs:
        if e.get("entity"):
            by_ent[e["entity"]] += 1
    top = sorted(comps, key=lambda c: (-by_ent.get(c["name"], 0), c["name"]))[:6]
    grid = "".join(
        f'<div class="entity-card"><div class="entity-name">{esc(c["name"])}</div>'
        f'<p class="entity-desc">{esc("、".join(c.get("focus", [])) or "—")}'
        f' · 收录 {by_ent.get(c["name"], 0)} 条事件</p></div>' for c in top)

    # 交易与融资榜：只收披露了金额的事件，按金额倒序
    deals = [e for e in evs if amount_val(e.get("amount")) > 0]
    deals.sort(key=lambda e: -amount_val(e["amount"]))
    deal_rows = "".join(
        f'<div class="deal-row"><span class="deal-amt">{esc(e["amount"])}</span>'
        f'<span class="deal-name"><a href="{esc(e.get("source_url","#"))}">'
        f'{esc(e.get("headline") or e["id"])}</a></span>'
        f'<span class="deal-meta">{esc(e["date"])} · {esc(e["type"])}'
        f' · {esc(e.get("entity") or "")} · {esc(amount_kind(e["amount"]))}'
        f' · 来源 {esc(e.get("source") or "—")}</span></div>'
        for e in deals)
    deal_html = ('<div class="section-head" style="margin-top:2rem">'
                 '<h2>交易与融资榜</h2></div>'
                 + '<div>' + deal_rows + '</div>'
                 + '<p style="font-size:var(--f-xs);color:var(--c-muted);margin-top:.6rem">'
                   '金额栏为公开披露原文，未做换算或加总；标注「协议上限」的是里程碑或'
                   '合作总额的最高值，标注「估值」的是定价，两者都不等于已支付金额。</p>')

    # 赛道分布：按公司技术方向聚合
    tracks = Counter(t for c in comps for t in c.get("focus", []))
    track_chips = "".join(
        f'<span class="type-chip">{esc(t)} {n}</span>'
        for t, n in tracks.most_common())
    track_html = ('<div class="section-head" style="margin-top:2rem"><h2>赛道分布</h2>'
                  '<a href="/companies/" class="section-more">按公司查看 →</a></div>'
                  '<div class="type-bar">' + track_chips + '</div>'
                  '<p style="font-size:var(--f-xs);color:var(--c-muted)">'
                  '按公司档案里的技术方向统计，一家公司可属于多个赛道。</p>')

    notice = ('<p class="notice-box"><strong>关于本页信息的来源</strong>'
              '本页每条事件都关联到站内已发布文章或原始来源，'
              '<strong>没有来源的条目不会进入本页</strong>。'
              '公司档案页只保留不随时间变化的属性，'
              '融资额、收购与管线进展一律由事件流生成。</p>')

    recent = sum(1 for e in evs if (date.today() - date.fromisoformat(e["date"])).days <= 30)
    h = hero("产业",
             "长寿产业事件流：融资、收购、合作、监管与临床进展。"
             "每条事件都带来源，可回溯到原始报道或站内文章。",
             [(len(evs), "条事件"), (recent, "条近 30 天"),
              (len(comps), "家公司"), (len(deals), "笔披露金额"),
              (len(invs), "位可溯源出资人"), (len(cons), "场已核实会议")])
    body = (notice + '<div class="type-bar">' + chips + '</div>'
            + deal_html + track_html + timeline
            + '<div class="section-head" style="margin-top:2rem"><h2>公司档案</h2>'
              '<a href="/companies/" class="section-more">查看全部 →</a></div>'
            + '<div class="entity-grid">' + grid + '</div>' + conf)
    return page("产业", "长寿产业事件流：融资、收购、合作、监管与临床进展，每条事件均带来源。",
                "/industry/", ' aria-current="page"', h, body)


# ───────────────────────── 2. /companies/ 公司档案 ─────────────────────────

def render_companies(comps, evs, invs):
    by_ent = defaultdict(list)
    for e in evs:
        if e.get("entity"):
            by_ent[e["entity"]].append(e)

    def initials(n):
        parts = re.split(r"[\s·]", n)
        if len(parts) >= 2 and parts[0] and parts[1]:
            return (parts[0][0] + parts[1][0]).upper()
        return n[:2].upper()

    cards = []
    for c in sorted(comps, key=lambda x: (-len(by_ent.get(x["name"], [])), x["name"])):
        lv = by_ent.get(c["name"], [])
        label, cls = STATUS_LABEL.get(c.get("status", "active"), ("活跃", "status-active"))
        tags = "".join(f'<span class="tag">{esc(t)}</span>' for t in c.get("focus", []))
        if lv:
            ev = max(lv, key=lambda x: x["date"])
            amt = f' · {esc(ev["amount"])}' if ev.get("amount") else ""
            latest = (f'<p class="entity-desc">最新：{esc(ev["date"])} '
                      f'{esc(ev["type"])}{amt}'
                      f'<br><a href="{esc(ev.get("source_url","#"))}">'
                      f'{esc((ev.get("headline") or "")[:46])}…</a>'
                      f'<br><span style="font-size:var(--f-xs)">'
                      f'收录 {len(lv)} 条事件 · 来源 {esc(ev.get("source") or "—")}</span></p>')
        else:
            latest = '<p class="entity-desc">暂无关联事件</p>'
        cards.append(
            f'<div class="entity-card"><div class="entity-logo">{esc(initials(c["name"]))}</div>'
            f'<div class="entity-name">{esc(c["name"])}</div>'
            f'<div style="margin-bottom:.4rem"><span class="status-badge {cls}">{esc(label)}</span></div>'
            f'{latest}<div class="entity-tags">{tags}</div></div>')

    # 按赛道分组浏览（公司暂无独立详情页，这里用 chips 列出名字）
    tracks = defaultdict(list)
    for c in comps:
        for t in c.get("focus", []):
            tracks[t].append(c["name"])
    blocks = []
    for t in sorted(tracks, key=lambda x: (-len(tracks[x]), x)):
        names = "".join(f'<span class="type-chip">{esc(n)}</span>'
                        for n in sorted(tracks[t]))
        blocks.append(f'<div class="track-block"><div class="track-title">'
                      f'{esc(t)} · {len(tracks[t])} 家</div>'
                      f'<div class="type-bar">{names}</div></div>')
    track_html = ('<div class="section-head" style="margin-top:2rem">'
                  '<h2>按赛道浏览</h2></div>' + "".join(blocks))

    inv_html = ""
    if invs:
        lis = "".join(
            f'<span class="type-chip">{esc(i["name"])}'
            + (f' · {esc(i["via"])}' if i.get("via") else "") + '</span>'
            for i in invs)
        inv_html = ('<div class="section-head" style="margin-top:2rem">'
                    '<h2>可溯源出资人</h2>'
                    '<a href="/investors/" class="section-more">出资人名录 →</a></div>'
                    '<div class="type-bar">' + lis + '</div>'
                    '<p style="font-size:var(--f-sm);color:var(--c-muted)">'
                    '仅列出能给出公开来源的出资人；无法核实的一律不列。</p>')

    notice = ('<p class="notice-box"><strong>关于本页信息的来源</strong>'
              '卡片上的融资额、收购与进展<strong>全部来自事件流</strong>，'
              '并标注来源与关联文章；本页不手写任何金额。'
              '标注「状态待溯源」的企业，其存续情况尚未核实。</p>')

    h = hero("产业 · 公司档案",
             "长寿科技公司档案。每张卡片的动态信息由产业事件流聚合生成。",
             [(len(comps), "家在册"),
              (sum(1 for c in comps if c.get("status") == "active"), "活跃"),
              (sum(1 for c in comps if c.get("status") != "active"), "待溯源或已收购")])
    return page("产业 · 公司档案",
                "长寿科技公司档案，动态信息由产业事件流聚合生成，每条均带来源。",
                "/companies/", '', h,
                notice + '<div class="entity-grid">' + "".join(cards) + '</div>'
                + track_html + inv_html)


# ───────────────────────── 3. /events/ 会议日历 ─────────────────────────

def render_events(cons):
    today = date.today().isoformat()
    items = []
    for c in sorted(cons, key=lambda x: x.get("start", "")):
        start = c.get("start", "")
        ended = start < today
        badge = ('<span class="status-badge status-unknown" style="margin-left:.4rem">'
                 '已结束</span>' if ended else
                 '<span class="status-badge status-active" style="margin-left:.4rem">'
                 '未开始</span>')
        span = start + (f' → {esc(c["end"])}' if c.get("end") else '')
        name = c.get("name", "")
        url = c.get("source_url") or ""
        name_html = (f'<a href="{esc(url)}" rel="noopener">{esc(name)}</a>'
                     if url else esc(name))
        items.append(
            f'<div class="tl-item"><div class="tl-date">{esc(span)}</div>'
            f'<div class="tl-name">{name_html}{badge}</div>'
            f'<div class="tl-meta"><span class="tag">{esc(c.get("kind",""))}</span>'
            f'<span>{esc(c.get("place",""))}</span>'
            f'<span>来源：{esc(c.get("source",""))}</span></div></div>')

    upcoming = sum(1 for c in cons if c.get("start", "") >= today)
    notice = ('<p class="notice-box"><strong>关于本页信息的来源</strong>'
              '本日历只收录<strong>能给出公开来源</strong>的会议，'
              '每条都标注来源域名并可点进主办方页面核对；'
              '核实不到的会议一律不收录（此前手写版本里的 8 场会议'
              '因无来源已全部撤下，其中 IAGG 的日期也是错的）。'
              '日期与地点仍<strong>以主办方官方公告为准</strong>，'
              '页面按当前日期自动标注「已结束」。</p>')

    h = hero("会议日历",
             "衰老生物学与长寿科技领域的学术会议与产业活动日历，每条均带可核对来源。",
             [(len(cons), "场收录"), (upcoming, "场未开始")])
    return page("会议日历",
                "衰老与长寿领域学术会议与产业活动日历，逐条标注来源并自动标注已结束会议。",
                "/events/", '', h,
                notice + '<div class="tl">' + "".join(items) + '</div>')


# ───────────────────────── 4. /investors/ 出资人 ─────────────────────────

def render_investors(invs, comps):
    focus = {c["name"]: c.get("focus", []) for c in comps}
    cards = []
    for i in invs:
        url = i.get("source_url") or ""
        name_html = (f'<a href="{esc(url)}" rel="noopener">{esc(i["name"])}</a>'
                     if url else esc(i["name"]))
        ent = i.get("entity") or ""
        ent_html = ""
        if ent:
            ent_html = (f'<p class="entity-desc">关联：{esc(ent)}'
                        + (f' · {"、".join(focus.get(ent, []))}'
                           if focus.get(ent) else '') + '</p>')
        cards.append(
            f'<div class="entity-card"><div class="entity-name">{name_html}</div>'
            f'<p class="entity-desc">通过：{esc(i.get("via",""))}</p>'
            f'{ent_html}'
            f'<p class="entity-desc" style="font-size:var(--f-xs)">'
            f'来源：{esc(i.get("source",""))}</p></div>')

    notice = ('<p class="notice-box"><strong>为什么这里只有三个人</strong>'
              '本页原为手写名录，2026-10-18 审计时 5 条里查出 3 条有问题'
              '（把 Founders Fund 的 Peter Thiel 写成「Peter Berg」、'
              '把 Foresite Capital 的负责人写成斯坦福教授 Tony Wyss-Coray、'
              '以及查无实据的「Krispy Kreme 家族办公室」）。'
              '现在的原则是：<strong>能给公开来源的才留，给不出的一律删</strong>，'
              '所以只剩下这三位，并且每条都给了官方来源链接。</p>')

    h = hero("产业 · 出资人",
             "长寿科技领域的出资人与机构。仅收录能给出公开来源的条目。",
             [(len(invs), "位在册")])
    return page("产业 · 出资人",
                "长寿科技领域可溯源的出资人与机构名录，每条均给出官方来源。",
                "/investors/", '', h,
                notice + '<div class="entity-grid">' + "".join(cards) + '</div>')


# ───────────────────────── main ─────────────────────────

def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    root = os.path.abspath(root)
    src = os.path.join(root, "data", "industry.json")
    if not os.path.exists(src):
        print(f"❌ 缺少事实源 {src}")
        return 1

    data = json.load(open(src, encoding="utf-8"))
    evs_all = data.get("events", [])
    comps = data.get("companies", [])
    invs = data.get("investors", [])
    cons_all = data.get("conferences", [])

    # 硬校验：无来源的事件 / 会议一律不得进入页面
    bad = [e for e in evs_all if not e.get("source")]
    if bad:
        print(f"⚠️ {len(bad)} 条事件缺 source，已跳过："
              + ", ".join(e.get("id", "?") for e in bad[:5]))
    evs = [e for e in evs_all if e.get("source")]

    bad_c = [c for c in cons_all if not c.get("source")]
    if bad_c:
        print(f"⚠️ {len(bad_c)} 场会议缺 source，已跳过："
              + ", ".join(c.get("name", "?")[:20] for c in bad_c[:5]))
    cons = [c for c in cons_all if c.get("source")]

    os.makedirs(os.path.join(root, "industry"), exist_ok=True)
    os.makedirs(os.path.join(root, "companies"), exist_ok=True)
    os.makedirs(os.path.join(root, "events"), exist_ok=True)
    os.makedirs(os.path.join(root, "investors"), exist_ok=True)

    outs = [
        (os.path.join(root, "industry", "index.html"),
         render_industry(evs, comps, invs, cons)),
        (os.path.join(root, "companies", "index.html"),
         render_companies(comps, evs, invs)),
        (os.path.join(root, "events", "index.html"),
         render_events(cons)),
        (os.path.join(root, "investors", "index.html"),
         render_investors(invs, comps)),
    ]
    for path, content in outs:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✅ {os.path.relpath(path, root)}  ({len(content.encode()):,} 字节)")

    print(f"产业页生成完成：事件 {len(evs)} 条 · 公司 {len(comps)} 家 · "
          f"出资人 {len(invs)} 位 · 会议 {len(cons)} 场")
    return 0


if __name__ == "__main__":
    sys.exit(main())
