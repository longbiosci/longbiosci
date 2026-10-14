#!/usr/bin/env python3
"""热词专题页生成器：从 data/articles.json + data/hotwords.json 生成 /guide/。

与既有页面的分工（避免重复）-------------------------------
| 层            | 路径              | 定位                     | 组织维度           |
|---------------|-------------------|--------------------------|--------------------|
| 概念科普(已有)| /research/ + 词条 | 回答「这是什么」         | 人工撰写词条       |
| 机制专辑(已有)| /topics/{slug}    | 按 8 大机制归档全库      | topic 字段，纵向   |
| 热词专题(本)  | /guide/{slug}     | 回答「证据走到哪了」     | 关键词跨 topic，横向|

一个热词（如运动干预）会横跨多个机制专辑，任何单个 /topics/ 页都无法呈现其全貌——
这正是本层存在的理由。

内容原则：**零编造**。页面上的每一条研究都来自 articles.json；
「证据红线」由 A/B/C 实际构成自动推导，不写未经数据支持的断言。
定位句 lead 由人工维护在 hotwords.json，只描述范围与口径。

用法：python3 scripts/gen_guide.py
"""
import json
import re
import sys
from collections import Counter
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://longbiosci.com"
sys.path.insert(0, str(ROOT / "scripts"))
from gen_site import head, feed_item, FOOTER, TOPICS  # noqa: E402

TOPIC_SLUG = {k: v[0] for k, v in TOPICS.items()}


def redline(counts, total):
    """按证据构成推导红线句——只陈述数据本身支持的结论。"""
    a, b, c = counts.get("A", 0), counts.get("B", 0), counts.get("C", 0)
    if total == 0:
        return "本站尚未收录该方向的解读。"
    if a == 0:
        return (f"本专题 {total} 篇全部为临床前研究或预印本，尚无人体证据。"
                "不能作为任何健康决策的依据。")
    if a / total >= 0.35:
        return (f"本专题 {total} 篇中 {a} 篇为同行评议人体研究，人体证据相对充分；"
                f"但 {b} 篇为动物或体外实验，长期安全性与个体差异仍待更多数据。")
    return (f"本专题 {total} 篇中仅 {a} 篇为人体研究，{b} 篇停留在动物或体外实验。"
            "结论尚不能外推至人体，请勿据此自行干预。")


def match(art, keywords):
    blob = f"{art.get('title', '')} {art.get('desc', '')}".lower()
    return any(k.lower() in blob for k in keywords)


def main():
    arts = json.loads((ROOT / "data" / "articles.json").read_text(encoding="utf-8"))
    arts.sort(key=lambda a: a.get("date", ""), reverse=True)
    cfg = json.loads((ROOT / "data" / "hotwords.json").read_text(encoding="utf-8"))
    topics = [t for t in cfg["topics"] if not t["slug"].startswith("_")]
    out_dir = ROOT / "guide"
    out_dir.mkdir(exist_ok=True)
    cards, total_pages = [], 0

    for t in topics:
        items = [a for a in arts if match(a, t["keywords"])]
        if not items:
            print("skip (0 篇):", t["slug"])
            continue
        n = len(items)
        counts = Counter(a.get("evidence", "") for a in items)
        dates = sorted(a.get("date", "") for a in items)
        a, b, c = counts.get("A", 0), counts.get("B", 0), counts.get("C", 0)

        # 证据分布条
        bar = "".join(
            f'<span class="ev-seg ev-{x.lower()}" style="width:'
            f'{max(counts.get(x, 0) / n * 100, 0):.1f}%" title="{x} 级 {counts.get(x, 0)} 篇">'
            f'</span>' for x in "ABC")
        snapshot = (
            '<div class="ev-snapshot">\n'
            f'<div class="ev-bar">{bar}</div>\n'
            '<div class="ev-legend">\n'
            f'<span class="tier tier-A">A</span> 人体研究 {a} 篇 · '
            f'<span class="tier tier-B">B</span> 临床前 {b} 篇 · '
            f'<span class="tier tier-C">C</span> 预印本 {c} 篇\n'
            f'<span class="ev-range">收录区间 {dates[0]} — {dates[-1]}</span>\n'
            '</div>\n</div>\n')

        # 交叉分布：命中最多的 3 个机制专辑
        tc = Counter(a.get("topic", "") for a in items).most_common(3)
        cross = "".join(
            f'<a href="/topics/{TOPIC_SLUG.get(name, "")}.html">{escape(name)}'
            f'<span>{cnt}</span></a>\n' for name, cnt in tc if name in TOPIC_SLUG)

        body = (
            head(f"{t['name']} - LongBiosci",
                 f"{t['name']}方向的研究解读汇总，按证据分级标注。",
                 f"{BASE}/guide/{t['slug']}.html", "topics")
            + '<section class="hero"><div class="wrap">\n'
            f'<h1>{escape(t["name"])}</h1>\n<p>{escape(t["lead"])}</p>\n</div></section>\n'
            + '<section class="section"><div class="wrap">\n'
            + f'<h2>证据快照 · {n} 篇</h2>\n' + snapshot
            + f'<p class="notice-line"><strong>证据边界</strong>：{escape(redline(counts, n))}</p>\n'
            + '<h2>横跨的机制专辑</h2>\n<div class="filter-bar">\n' + cross + '</div>\n'
            + f'<h2>全部收录（{n} 篇，按时间倒序）</h2>\n'
            + '<div class="feed">\n' + "".join(feed_item(a) for a in items) + "</div>\n"
            + '<p class="notice-line">专题页按关键词自动聚合，可能漏收或误收；'
            '发现错漏请通过「关于」页反馈。</p>\n'
            + "</div></section>\n" + FOOTER)
        (out_dir / f"{t['slug']}.html").write_text(body, encoding="utf-8")
        total_pages += 1
        cards.append((t, n, a, b, c))
        print(f"generated: guide/{t['slug']}.html  ({n} 篇 A{a}/B{b}/C{c})")

    # ---- 索引页 ----
    cards.sort(key=lambda x: -x[1])
    grid = "".join(
        f'<a href="/guide/{t["slug"]}.html" class="topic-card">\n'
        f'<span class="t-name">{escape(t["name"])}</span>\n'
        f'<span class="t-count">{n} 篇 · A {a} / B {b} / C {c}</span>\n</a>\n'
        for t, n, a, b, c in cards)
    idx = (head("热词专题 - LongBiosci",
                "按具体干预与技术关键词横向聚合的研究专题，跨机制专辑呈现证据全貌。",
                f"{BASE}/guide/", "topics")
           + '<section class="hero"><div class="wrap">\n<h1>热词专题</h1>\n'
           '<p>按具体干预手段与关键技术横向聚合。与「主题专辑」按机制纵向归档互为补充——'
           '一个热词往往横跨多个机制。</p>\n</div></section>\n'
           + '<section class="section"><div class="wrap">\n<div class="topic-grid">\n'
           + grid + "</div>\n"
           + '<div class="notice-box" style="margin-top:2rem">\n'
           '<p><strong>与主题专辑的区别</strong></p>\n'
           '<p><a href="/topics/">主题专辑</a>按衰老机制纵向归档，回答「这条通路上有什么研究」；'
           '本页按干预与技术横向聚合，回答「这个方向证据走到哪了」。'
           '<a href="/research/">概念与工具</a>则负责回答「这是什么」。</p>\n</div>\n'
           + "</div></section>\n" + FOOTER)
    (out_dir / "index.html").write_text(idx, encoding="utf-8")
    print(f"done: {total_pages} 热词专题页 + guide/index.html")


if __name__ == "__main__":
    main()
