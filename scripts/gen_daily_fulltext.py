#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_daily_fulltext.py —— 全文级速递专页生成器（2026-10-19 建）

输入：data/fulltext/medrxiv/_final_summary.json（本轮全文抓取汇总）
输出：daily/fulltext-batch-<date>.html（全文级结构化摘编专页）

设计纪律（遵守项目「数据真实可溯源」铁律）：
  - 卡片中的一句话贡献、核心要点、局限**均为全文原文句子摘录**（英文保真），
    不做转写、不补全；数字全部来自正文，未报告的不猜。
  - 「数据速览」由 NUM 正则从正文抽取，原样呈现。
  - 价值星级为**自动评估**（full+核心=★★★ / full+宽=★★☆ / partial=★☆☆），
    已在卡片标注，非人工判断。
  - 本页为「自动摘编」档；人工精读版后续升级，两者在页面顶部明确区分。

用法：python3 scripts/gen_daily_fulltext.py [汇总json路径] [输出html路径]
"""
import html
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DAILY = ROOT / "daily"
FT = ROOT / "data" / "fulltext" / "medrxiv"

# 与 preprint_daily.py 一致的定量正则
NUM = re.compile(
    r"(?<![\w.])(\d+(?:\.\d+)?\s*(?:%|fold|-fold|mmHg|mg/kg|nM|µM|μM|days|weeks|months|years))"
    r"|(?:[nN]\s*=\s*\d+)|(?:p\s*[<=]\s*0?\.\d+)|(?:[×x]\s*10\^?-?\d+)|(?:\b\d{2,}\b)")

# 领域词 → 中文标签（命中即贴，可多贴）
DOMAIN_MAP = [
    (r"senescen|senolytic|SASP|p16INK4a|p21", "细胞衰老"),
    (r"aging|ageing|longevity|lifespan|healthspan|geroscience", "衰老与长寿"),
    (r"epigenetic clock|methylation|DNAm", "表观遗传时钟"),
    (r"telomere", "端粒"),
    (r"mitochondri|OXPHOS|metabol", "线粒体与能量代谢"),
    (r"autophagy|proteostasis|aggregate", "蛋白稳态与自噬"),
    (r"stem cell|progenitor|regenerat", "干细胞与再生"),
    (r"Alzheimer|dementia|cognitive|neurodegener|Parkinson", "神经退行与认知"),
    (r"frailty|sarcopenia|muscle|gait|walking", "衰弱与肌骨"),
    (r"cardiovascular|heart|atrial|stroke|vascular|blood pressure", "心血管"),
    (r"gut|microbiome|microbiota", "微生物组"),
    (r"inflammat|immune|cytokine|NF-κB", "免疫与炎症"),
    (r"rapamycin|mTOR|NAD\+|sirtuin|metformin|caloric|dietary", "干预靶点与代谢"),
    (r"single-cell|single cell|scRNA", "单细胞组学"),
    (r"Mendelian|GWAS|genetic|polygenic", "遗传与多组学"),
    (r"cohort|epidemiolog|UK Biobank|Framingham|NHANES", "流行病学队列"),
    (r"machine learning|deep learning|neural network|AI\b", "计算方法学"),
    (r"fibrosis|lung|pulmonary", "肺与纤维化"),
    (r"kidney|renal|liver|hepatic", "肝肾功能"),
    (r"HIV|virus|infection", "感染与免疫衰老"),
    (r"reprogramming|Yamanaka|OSK|pluripotent", "重编程"),
    (r"women|sex difference|gender", "性别差异"),
]

# 研究类型词表（正文前 3000 字符内命中）
TYPE_MAP = [
    (r"\bmice\b|\bmouse\b|\bmurine\b|knockout|\bKO\b|wild-type", "动物实验"),
    (r"randomi[sz]ed|placebo|double-blind|trial\b", "临床试验/干预"),
    (r"cohort|participants|respondents|questionnaire", "人群队列/调查"),
    (r"Mendelian randomi", "孟德尔随机化"),
    (r"scRNA|single-cell RNA|single cell transcript", "单细胞测序"),
    (r"proteomic|metabolomic|transcriptomic|multi-omics", "多组学"),
    (r"machine learning|deep learning|random forest|neural network", "机器学习/计算"),
    (r"meta-analysis|systematic review|scoping review|narrative review", "综述/荟萃"),
    (r"organoid|classoid", "类器官"),
    (r"post-mortem|autopsy|brain bank", "人体组织"),
]


def split_sections(txt: str):
    """按 '## 标题' 切节，返回 [(标题, 正文), ...]。"""
    parts = re.split(r"\n## ", txt)
    secs = []
    for p in parts[1:]:
        lines = p.split("\n", 1)
        title = lines[0].strip()
        body = lines[1].strip() if len(lines) > 1 else ""
        secs.append((title, body))
    return secs


def sentences(text: str):
    # 先把 markdown 化的小节标题行抹掉，避免标题粘进句子
    text = re.sub(r"\n## [^\n]*\n", " ", text)
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 40]


TOP_RE = re.compile(
    r"^(introduction|background|methods?|materials and methods|results?|discussion|"
    r"conclusions?|limitations?|strengths|references|acknowledg|data availability|"
    r"code availability|supporting information|figure legends?|supplementary|abstract)", re.I)

CAPTION_RE = re.compile(
    r"\(?(?:top|bottom|left|right)\)|shown (?:separately|in)|depicted|centile curves|"
    r"Population centile|schematic|workflow overview|representative images?", re.I)


def top_sections(txt: str):
    """按顶层节（Introduction/Methods/Results/...）聚合文本，子节归并到当前顶层节。"""
    parts = re.split(r"\n## ", txt)
    out = []
    cur_top, cur_buf = "PREAMBLE", ([parts[0]] if parts else [])
    for p in parts[1:]:
        lines = p.split("\n", 1)
        title = lines[0].strip()
        if TOP_RE.match(title):
            out.append((cur_top, "\n".join(cur_buf)))
            cur_top, cur_buf = title, [p]
        else:
            cur_buf.append(p)
    out.append((cur_top, "\n".join(cur_buf)))
    return out


def pick_core_points(txt: str, k: int = 5):
    """只从 Results/Discussion/Conclusions 顶层节挑含数字的句子（每个子节至多 1 条）。

    为什么不再全文乱挑：实测 HighWire 稿的 Methods 里嵌图注、图注节标题不带
    "Figure" 字样（如 "Basal forebrain compartments GM volume normative trajectories..."），
    靠节名过滤不准；限定结果类顶层节 + 图注特征句过滤后干净得多。
    """
    picks, seen = [], set()
    for top, body in top_sections(txt):
        if not re.search(r"result|discussion|conclusion|finding", top, re.I):
            continue
        # 顶层节内再按子节分，每个子节挑 1 条
        for sub in re.split(r"\n## ", body)[1:] or [body]:
            lines = sub.split("\n", 1)
            sub_body = lines[1] if len(lines) > 1 else lines[0]
            for s in sentences(sub_body):
                if not NUM.search(s):
                    continue
                if CAPTION_RE.search(s) and not re.search(r"[nN]\s*=\s*\d+|p\s*[<=]", s):
                    continue
                if s not in seen:
                    seen.add(s)
                    picks.append((top, s))
                break
            if len(picks) >= k:
                break
        if len(picks) >= k:
            break
    # 不够则从全文数字句补足（仍过滤图注与重复）
    if len(picks) < k:
        for s in sentences(txt):
            if len(picks) >= k:
                break
            if s in seen or not NUM.search(s):
                continue
            if CAPTION_RE.search(s) and not re.search(r"[nN]\s*=\s*\d+|p\s*[<=]", s):
                continue
            seen.add(s)
            picks.append(("（全文补选）", s))
    return picks[:k]


def extract_abstract_from_xml(xml_path: Path, limit: int = 400) -> str:
    """从 JATS source.xml 提取结构化 <abstract> 文本。

    为什么不用 API 的 abstract：实测 medRxiv details API 有 5 条把 abstract
    字段回退成了正文首段（INTRODUCTION 开头），结构化摘要以 XML 为准。
    """
    if not xml_path.exists():
        return ""
    try:
        t = xml_path.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"<abstract[^>]*>(.*?)</abstract>", t, re.S)
        if not m:
            return ""
        s = re.sub(r"<[^>]+>", " ", m.group(1))
        s = re.sub(r"\s+", " ", s).strip()
        return s[:limit]
    except Exception:
        return ""


def pick_limits(txt: str, k: int = 2):
    secs = split_sections(txt)
    # 优先局限专节
    for title, body in secs:
        if re.search(r"LIMITATION|STRENGTHS", title, re.I):
            ss = sentences(body)
            if ss:
                return ss[:k]
    # 否则全文搜关键词句
    hits = [s for s in sentences(txt)
            if re.search(r"limitation|caveat|cannot be excluded|should be interpreted with caution|"
                         r"not without|warrants? further|remains? (unclear|to be)", s, re.I)]
    return hits[:k] if hits else ["（全文未设专门局限节，亦未检出限定表述句——按纪律不做推断，标「未报告」。）"]


def data_snapshot(txt: str, k: int = 6):
    seen, out = set(), []
    for m in NUM.finditer(txt):
        v = m.group(0).strip()
        if v not in seen:
            seen.add(v)
            out.append(v)
        if len(out) >= k:
            break
    return out


def domain_tags(title: str, abstract: str):
    text = f"{title} {abstract}"
    return [zh for pat, zh in DOMAIN_MAP if re.search(pat, text, re.I)][:3] or ["衰老与长寿"]


def type_tags(title: str, txt_head: str):
    return [zh for pat, zh in TYPE_MAP if re.search(pat, txt_head, re.I)][:2] or ["观察性研究"]


def star(grade: str, core: bool):
    if grade == "full":
        return "★★★" if core else "★★☆"
    return "★☆☆"


def esc(s):
    return html.escape(s or "", quote=False)


def render_card(item, idx):
    txt_path = FT / item["txt_file"]
    txt = txt_path.read_text(encoding="utf-8") if txt_path.exists() else ""
    if not txt:
        return None
    core = pick_core_points(txt)
    lims = pick_limits(txt)
    snap = data_snapshot(txt)
    tags = domain_tags(item["title"], item.get("abstract", ""))
    ttags = type_tags(item["title"], txt[:3000])
    grade_zh = {"full": "全文完整", "partial": "全文（内容页补救）"}.get(item["grade"], item["grade"])
    doi = item["doi"]
    link = f"https://www.medrxiv.org/content/{doi}v1"
    # 贡献句优先级：JATS 结构化 abstract > API abstract > 标题
    xml_abs = extract_abstract_from_xml(FT / (item["txt_file"].replace(".full.txt", ".xml").replace(".page.txt", ".xml")))
    if xml_abs:
        contrib = re.sub(r"^(Abstract\s+)?(ABSTRACT\s+)?(INTRODUCTION|BACKGROUND|Introduction|Background)\s+",
                         "", xml_abs).split(". ")[0].strip()
    else:
        api_abs = item.get("abstract") or ""
        if re.match(r"^(INTRODUCTION|BACKGROUND|ABSTRACT)", api_abs.strip()):
            api_abs = ""  # API 回退成正文首段的，弃用
        contrib = (api_abs.split(". ")[0].strip() or item["title"])
    if len(contrib) > 300:
        contrib = contrib[:297] + "…"
    core_html = "".join(
        f"<br>{'①②③④⑤'[i] if i < 5 else '·'} [{esc(t)}] {esc(s)}"
        for i, (t, s) in enumerate(core)) or "<br>（正文过短，未检出含定量的结果句——按纪律不推断。）"
    lim_html = "<br>".join(f"{'①②'[i]} {esc(s)}" for i, s in enumerate(lims))
    snap_html = " · ".join(f"<code>{esc(v)}</code>" for v in snap) or "（未检出显式定量）"
    return f"""<div class="paper">
<div class="paper num">{idx}</div>
<div class="paper-title">{esc(item['title'])}</div>
<div class="paper-meta">来源：medRxiv ｜ DOI：<a href="https://doi.org/{esc(doi)}" target="_blank" rel="noopener noreferrer">{esc(doi)}</a> ｜ 上线：{esc(item['date'])} ｜ 正文 {item.get('chars') or 0:,} 字符（{grade_zh}）</div>
<div class="paper-tags"><span>{esc('；'.join(tags))}</span><span>{esc('；'.join(ttags))}</span><span>预印本 · 未同行评审 · 全文级自动摘编</span></div>
<p class="contrib"><strong>一句话贡献（摘要首句摘录）：</strong>{esc(contrib)}.</p>
<p class="core"><strong>核心要点（正文原句摘录）：</strong>{core_html}</p>
<p class="core"><strong>数据速览（正文抽取）：</strong>{snap_html}</p>
<p class="limit"><strong>保留意见/局限（原文摘录）：</strong>{lim_html}</p>
<p class="value"><strong>对本栏价值（自动评估）：</strong>{star(item['grade'], item.get('core'))}</p>
<a href="{link}" rel="noopener noreferrer" target="_blank" class="source-link">🔗 阅读原文（medRxiv）</a>
</div>"""


def get_style_block():
    """复用现有 daily 页的 CSS，保证视觉一致。"""
    ref = DAILY / "2026-10-15.html"
    if ref.exists():
        m = re.search(r"<style>.*?</style>", ref.read_text(encoding="utf-8"), re.S)
        if m:
            return m.group(0)
    return "<style>body{font-family:sans-serif;max-width:860px;margin:0 auto;padding:20px;}</style>"


def publish_to_index(page_url: str, title: str, desc: str, date_str: str):
    """幂等发布：daily/index.html 锚点后插条目 + rss.xml 插 item。"""
    # 1) daily/index.html（锚点注释后插 feed-item）
    idx = DAILY / "index.html"
    t = idx.read_text(encoding="utf-8")
    anchor = "<!-- longbiosci:preprint-express-series -->"
    if page_url not in t and anchor in t:
        entry = (f'{anchor}\n<div class="feed-item">\n'
                 f'<div class="item-meta">\n<span class="tag">全文级速递</span>\n'
                 f'<span class="tag-date">{date_str}</span>\n</div>\n'
                 f'<div class="feed-title"><a href="{page_url}">{html.escape(title)}</a></div>\n'
                 f'<p class="feed-desc">{html.escape(desc)}</p>\n</div>')
        t = t.replace(anchor, entry, 1)
        idx.write_text(t, encoding="utf-8")
        print(f"  已插入 daily/index.html：{title}")

    # 2) rss.xml（首个 item 前插入，倒序）
    rss = ROOT / "rss.xml"
    t = rss.read_text(encoding="utf-8")
    if page_url not in t:
        item = (f'<item><title>{html.escape(title)} - LongBiosci</title>'
                f'<link>https://longbiosci.com{page_url}</link>'
                f'<guid isPermaLink="true">https://longbiosci.com{page_url}</guid>'
                f'<pubDate>{time.strftime("%a, %d %b %Y 00:00:00 +0000")}</pubDate>'
                f'<description>{html.escape(desc)}</description></item>')
        i = t.index("<item>")
        t = t[:i] + item + t[i:]
        rss.write_text(t, encoding="utf-8")
        print(f"  已插入 rss.xml：{title}")


def main():
    today = time.strftime("%Y-%m-%d")
    args = sys.argv[1:]
    # 参数：--date YYYY-MM-DD 只收录该上线日期的条目；--no-publish 只生成页面不发布
    want_date = None
    if "--date" in args:
        want_date = args[args.index("--date") + 1]
    no_publish = "--no-publish" in args
    rest = [a for a in args if a not in ("--no-publish",) and not (a == "--date" or (want_date and a == want_date and "--date" in args))]
    summary_path = rest[0] if rest else FT / "_final_summary.json"
    page_date = want_date or today
    out_path = rest[1] if len(rest) > 1 else DAILY / f"{page_date}-fulltext-batch.html"
    s = json.load(open(summary_path, encoding="utf-8"))
    items = s["items"]
    if want_date:
        items = [i for i in items if i.get("date") == want_date]
        if not items:
            print(f"日期 {want_date} 无已取全文条目，不生成页面（bioRxiv 独大的日子会如此）")
            return
    main_items = [i for i in items if i["grade"] == "full" and i.get("core")]
    watch_items = [i for i in items if not (i["grade"] == "full" and i.get("core"))]

    main_cards = "\n".join(render_card(i, n) for n, i in enumerate(main_items, 1))
    watch_cards = "\n".join(render_card(i, n) for n, i in enumerate(watch_items, 1))
    n_main, n_watch = len(main_items), len(watch_items)
    win = f"{want_date} 当日" if want_date else s.get("window", today)

    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>全文级速递 · medRxiv {n_main + n_watch} 篇（{win}） — LongBiosci</title>
<meta name="description" content="LongBiosci 衰老与长寿领域 medRxiv 预印本全文级速递：{win} 窗口 {n_main + n_watch} 篇命中取得全文，结构化摘编。">
<link rel="canonical" href="https://longbiosci.com/daily/{out_path.name}">
<meta property="og:type" content="article"><meta property="og:url" content="https://longbiosci.com/daily/{out_path.name}">
<meta property="og:title" content="全文级速递 · medRxiv {n_main + n_watch} 篇"><meta property="og:description" content="{win} medRxiv {n_main + n_watch} 篇衰老相关预印本取得全文的结构化摘编。">
<meta property="og:image" content="https://longbiosci.com/og-image.png"><meta property="og:site_name" content="LongBiosci">
<meta name="twitter:card" content="summary_large_image">
{get_style_block()}
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="icon" type="image/svg+xml" href="/favicon-dark.svg" media="(prefers-color-scheme: dark)">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<script defer src="https://cloud.umami.is/script.js" data-website-id="bfb60723-d93d-4925-b1a2-d7ef51b9014c" data-do-not-track="true"></script>
</head>
<body>
<a href="#main-content" class="skip-link">跳转到主要内容</a>
<header class="header"><button class="back-btn" onclick="history.back()">←</button><h1>LongBiosci</h1></header>
<article class="article"><div class="article-header">
<div class="article-tags"><span class="tag tag-tech">全文级速递</span><span class="tag tag-tech">{n_main + n_watch} 篇</span><span class="tag tag-sup">medRxiv</span></div>
<h1 class="article-title">《全文级速递》{win} · medRxiv {n_main + n_watch} 篇</h1>
<div class="article-meta">LongBiosci · {today} · 收录 {n_main + n_watch} 篇（主榜 {n_main} · 观察哨 {n_watch}）· 正文合计 {sum(i.get('chars') or 0 for i in items):,} 字符</div>
</div><div class="article-content">
<p class="intro">本批为 <strong>medRxiv 全文级结构化摘编</strong>：{win}内衰老宽口径命中 {n_main + n_watch} 篇，<strong>全部取得全文</strong>（JATS XML {n_main + n_watch - len([i for i in items if i["source"] == "html_page"])} 篇 + 内容页 HTML 补救 {len([i for i in items if i["source"] == "html_page"])} 篇），贡献句、核心要点、局限均为<strong>全文原文句子摘录</strong>，数据速览由正则从正文抽取，未报告项不推断。价值星级为自动评估。bioRxiv 同窗口命中 146 篇，因源站 IP 级封锁<strong>全文不可得</strong>，未入本批（见页尾说明）。</p>
<section class="tier-sec"><h2>主榜（Main）· 核心档 · 全文完整 {n_main} 篇</h2>
{main_cards}
</section>
<section class="tier-sec"><h2>观察哨（Watch）· {n_watch} 篇</h2>
{watch_cards}
</section>
<section class="tier-sec"><h2>关于 bioRxiv 的缺席说明</h2>
<div class="paper">
<p>同窗口 bioRxiv 宽口径命中 <strong>146 篇</strong>，均为衰老相关预印本，但本环境出口 IP 被 bioRxiv Cloudflare WAF 封禁（真实 DOI 连续探测恒定 403，内容页/JATS/PDF 全链路），<strong>全文无法取得</strong>。按「取不到全文就不做深度解读」的纪律，本批不纳入 bioRxiv 条目；待通道恢复（代理或官方 S3）后单独补发。本条为说明，不是内容缺失的借口。</p>
</div>
</section>
</div></article>
</body>
</html>"""
    out_path.write_text(page, encoding="utf-8")
    print(f"已生成 {out_path}（主榜 {n_main} + 观察哨 {n_watch} = {n_main + n_watch} 篇）")
    if not no_publish:
        publish_to_index(
            f"/daily/{out_path.name}",
            f"全文级速递：medRxiv {n_main + n_watch} 篇取得全文（{win}）",
            f"衰老宽口径命中中 medRxiv {n_main + n_watch} 篇全部取到全文，贡献句/核心要点/局限均为正文原句摘录。bioRxiv 条目因源站 IP 级封锁全文不可得，未纳入。",
            today)


if __name__ == "__main__":
    main()
