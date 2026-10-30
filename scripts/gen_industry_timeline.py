#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_industry_timeline.py —— /industry/timeline/ 行业时间线页（管线第 7 环节附属产物）

用法：python3 scripts/gen_industry_timeline.py <仓库根目录>

为什么要有这一页
────────────────
/industry/ 主页是 **data/industry.json 事件流**驱动的，而 industry.json 靠人工补录事件，
2026-10-30 实测其最后一条事件停在 **2026-10-18** —— 也就是说，站上已有的产业/监管/临床
稿件比这份手抄数据源**新了 12 天**，读者在产业板块看不到最近两周发生的事。
「手抄事实」必然滞后（gen-industry.py 文档里已写过这个根因），本页不再走那条路：

  · **数据源 = data/articles.json**（管线第 1 环节 build-index 从 news/*.html 重建的事实源）；
  · 选取口径：tag / type / topic 命中产业、行业、监管、政策、融资、公司、临床类关键词；
  · **按情报发生日期（data-lb-event-date 同源的 date 字段）倒序、按月分组**，
    每条同时给出「发生日期」与「发布日期」两个时间戳——产业稿最常出现的误读就是
    「10-21 的事 10-30 才上站，读者以为新闻是今天的」；
  · 幂等：产物由 articles.json 唯一决定，可反复运行。

产物：
  /industry/timeline/index.html   行业时间线（全量回溯，按月分组，带类型锚点）
  并向 /industry/index.html 注入一个带 lb-timeline-entry 标记的入口链接（幂等，
  必须在 gen-industry.py 之后运行，否则会被主页重新生成覆盖掉）。

不做什么：不改 industry.json（人工补录的数据源本页不依赖，也不去修它）；
不动全站导航（新增导航项会挤压移动端两行预算，入口放在产业板块内部即可）。
"""
import html
import json
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# 复用 gen-industry.py 的页头/导航/页脚模板，保证与产业板块视觉与导航完全一致
import importlib.util as _ilu


def _load(name, path):
    spec = _ilu.spec_from_file_location(name, path)
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_gi = _load("gen_industry", os.path.join(HERE, "gen-industry.py"))

EVIDENCE_LABEL = getattr(_gi, "EVIDENCE_LABEL",
                         {"A": "A 人体研究", "B": "B 临床前", "C": "C 预印本"})

# 选取口径：命中任一关键词即入时间线（tag / type / topic 三处任一命中）
KEYWORDS = ("产业", "行业", "监管", "政策", "融资", "公司", "商业", "临床")

# 时间线上的类型徽章（按命中关键词归并，顺序即锚点顺序）
BUCKETS = [
    ("融资", ("融资",)),
    ("管线与临床", ("临床", "管线")),
    ("监管与政策", ("监管", "政策")),
    ("公司与合作", ("公司", "合作", "商业")),
    ("产业与行业", ("产业", "行业")),
]


def esc(s):
    return html.escape(str(s or ""), quote=True)


def bucket_of(a):
    text = " ".join(str(a.get(k) or "") for k in ("tag", "type", "topic", "title"))
    for label, kws in BUCKETS:
        for kw in kws:
            if kw in text:
                return label
    return "产业与行业"


def selected(a):
    blob = " ".join(str(a.get(k) or "") for k in ("tag", "type", "topic"))
    if a.get("topic") == "产业":
        return True
    return any(kw in blob for kw in KEYWORDS)


def month_label(d):
    y, m = d[:4], d[5:7]
    return f"{y} 年 {int(m)} 月"


def build(root):
    data = json.load(open(os.path.join(root, "data", "articles.json"),
                          encoding="utf-8"))
    items = [a for a in data if selected(a)]
    items.sort(key=lambda a: (a.get("date") or "", a.get("added") or ""), reverse=True)

    counts = Counter(bucket_of(a) for a in items)
    months = defaultdict(list)
    for a in items:
        months[(a.get("date") or "")[:7]].append(a)

    # ── 锚点条 ──
    anchors = "".join(
        f'<a href="#b-{i}" class="tl-chip">{esc(label)} <span>{counts.get(label,0)}</span></a>'
        for i, (label, _) in enumerate(BUCKETS) if counts.get(label, 0))
    chips = f'<div class="tl-chips">{anchors}</div>' if anchors else ""

    # ── 按月分组的正文 ──
    body = []
    for idx, (label, _) in enumerate(BUCKETS):
        if counts.get(label, 0):
            body.append(f'<h2 id="b-{idx}" class="tl-anchor">{esc(label)}'
                        f'<span class="tl-n">{counts[label]} 条</span></h2>')
    body.append('<div class="tl">')
    cur_bucket = None
    for a in items:
        b = bucket_of(a)
        if b != cur_bucket:
            cur_bucket = b
        d = a.get("date") or ""
        added = a.get("added") or ""
        ev = a.get("evidence") or ""
        ev_label = EVIDENCE_LABEL.get(ev, ev)
        slug = a.get("slug") or ""
        same = "（同日上站）" if d == added else f"发布于 {esc(added)}"
        body.append(
            f'<article class="tl-item" data-lb-event-date="{esc(d)}" '
            f'data-lb-pub-date="{esc(added)}">'
            f'<div class="tl-date"><time datetime="{esc(d)}">{esc(d)}</time>'
            f'<span class="tl-pub">{esc(same)}</span></div>'
            f'<div class="tl-main"><span class="tl-badge">{esc(b)}</span>'
            f'<h3><a href="/news/{esc(slug)}">{esc(a.get("title") or "")}</a></h3>'
            f'<p>{esc(a.get("desc") or "")}</p>'
            f'<div class="tl-meta">{esc(ev_label)}'
            f'{(" · " + esc(a.get("source") or "")) if a.get("source") else ""}'
            f'{(" · " + esc(a.get("tag") or "")) if a.get("tag") else ""}</div>'
            f'</div></article>')
    body.append("</div>")

    style = """<style>
.tl-chips{display:flex;flex-wrap:wrap;gap:.5rem;margin:0 0 var(--s-3)}
.tl-chip{display:inline-flex;align-items:center;gap:.35rem;padding:.35rem .7rem;
  border:1px solid var(--c-border);border-radius:999px;font-size:var(--f-sm);
  color:var(--c-text);text-decoration:none}
.tl-chip:hover{border-color:var(--c-primary);color:var(--c-primary)}
.tl-chip span{font-variant-numeric:tabular-nums;color:var(--c-muted);font-size:var(--f-xs)}
.tl-anchor{font-size:var(--f-lg);margin:var(--s-4) 0 var(--s-2);scroll-margin-top:5rem}
.tl-anchor .tl-n{font-size:var(--f-sm);color:var(--c-muted);font-weight:400;margin-left:.5rem}
.tl{border-left:2px solid var(--c-border);padding-left:var(--s-3);margin-top:var(--s-2)}
.tl-item{display:flex;gap:var(--s-3);padding:.75rem 0;border-bottom:1px solid var(--c-border)}
.tl-item:last-child{border-bottom:0}
.tl-date{flex:0 0 8.5rem;font-size:var(--f-sm);font-variant-numeric:tabular-nums}
.tl-pub{display:block;color:var(--c-muted);font-size:var(--f-xs)}
.tl-main{flex:1;min-width:0}
.tl-main h3{font-size:var(--f-md);margin:.1rem 0 .3rem}
.tl-main p{font-size:var(--f-sm);color:var(--c-muted);margin:0 0 .3rem}
.tl-badge{display:inline-block;font-size:var(--f-xs);padding:.1rem .45rem;
  border:1px solid var(--c-border);border-radius:4px;color:var(--c-muted)}
.tl-meta{font-size:var(--f-xs);color:var(--c-muted)}
@media(max-width:640px){.tl{flex-direction:column}.tl-item{flex-direction:column;gap:.25rem}
  .tl-date{flex:none}}
</style>
"""

    hero_html = _gi.hero(
        "行业时间线",
        f"长寿产业 / 监管 / 临床里程碑全量回溯：{len(items)} 条，按<strong>情报发生日期</strong>倒序、"
        f"按月分组。每条同时标注发生日期与发布日期——产业动态常滞后数日上站，两个时间戳分开写，"
        f"避免把旧闻读成新闻。",
        [(len(items), "条时间线事件"),
         (len(months), "个月份"),
         (len([c for c in counts.values() if c]), "个类型"),
         ((items[0].get("date") or "") if items else "", "最新发生日期")],
        extra=chips)

    page = _gi.page(
        "行业时间线 · LongBiosci",
        f"长寿产业事件全量时间线：融资、管线与临床、监管与政策、公司合作，"
        f"共 {len(items)} 条，按情报发生日期倒序。",
        "/industry/timeline/",
        "",
        hero_html,
        style + "\n".join(body))

    out_dir = os.path.join(root, "industry", "timeline")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)

    # ── 向 /industry/index.html 注入入口（幂等）──
    ipath = os.path.join(root, "industry", "index.html")
    if os.path.exists(ipath):
        src = open(ipath, encoding="utf-8").read()
        link = (f'<p class="lb-timeline-entry" style="margin-top:.6rem">'
                f'<a href="/industry/timeline/">→ 查看完整行业时间线'
                f'（{len(items)} 条，按情报发生日期倒序，含监管与临床里程碑）</a></p>')
        if "lb-timeline-entry" in src:
            import re
            src = re.sub(r'<p class="lb-timeline-entry".*?</p>', link, src, count=1,
                         flags=re.S)
        elif "<h1>产业</h1>" in src:
            src = src.replace("<h1>产业</h1>", "<h1>产业</h1>\n" + link, 1)
        else:
            import re
            src = re.sub(r'(<h1>[^<]*</h1>)', r'\1\n' + link, src, count=1)
        open(ipath, "w", encoding="utf-8").write(src)

    print(f"[timeline] 事件 {len(items)} 条 · 月份 {len(months)} 个 · "
          f"类型分布 {dict(counts)}")
    print(f"[timeline] 产出 industry/timeline/index.html；入口已注入 industry/index.html")
    return 0


if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    sys.exit(build(root))
