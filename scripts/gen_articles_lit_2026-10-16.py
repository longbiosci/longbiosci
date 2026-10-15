#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_articles_lit_2026-10-16.py —— 内容摄入第 14 批（文献层《五刊监控·深度文献卡片》2026-10-16 期）

来源与判定
────────
事实源：文献层《文献层_五刊监控_深度文献卡片_2026-10-16.md》
（file_id dHQVvLfIkFGi，实测 249,984 B，任务 7762989 于 2026-10-16 05:50 交付）。
该期 67 张摘要级卡片（Nat Aging 17 / Cell Metab 1 / Aging Cell 22 / GeroScience 22 / Cell 5），
67 个 DOI 均经 CrossRef 逐条核验，与上两期合并的 87 个基线 DOI 零重叠。

查重结论（四路查重 + 关键词硬核验）：
  · **N02 / N04 / N10 共 3 条已在站**，不重复写：
      N02 RamanOmics          → news/RamanOmics-Senescence-Detection-Nature-Aging-2026.html（DOI 精确命中）
      N10 SPRINTT 多病模式     → news/Multimorbidity-Patterns-SPRINTT-Mobility-Nature-Aging-2026.html（DOI 精确命中）
      N04 运动-卵巢衰老-脂联素 → news/Exercise-Slows-Ovarian-Aging-Nature-Aging-2026.html
        ⚠️ 该文是「DOI 未命中但内容同篇」的典型：站内文未写 DOI，四路查重判不出来，
        靠 AdipoRon / 卵巢衰老 / 15 万人 UKB 三个高特异词硬核验才确认已收录。
  · 其余 **64 条为真漏收**，本批全部入站。

⚠️ 本轮必须先修的查重缺陷（已在 harvest.py 修复，此处记档）
────────────────────────────────────────────────────────────
产出侧 DOI 字段写作 Markdown 链接 `[10.1038/xxx](https://doi.org/10.1038/xxx)`。
harvest.normalize_doi 先剥 `](...)` 再按 `[` 切分，于是**开头残留的 `[` 让首段为空**，
67 个 DOI 全部被吞成空串 —— 四路查重的头一路（唯一的高置信路径）整体失效，
判定结果退化成 115 条 confidence=none。这不是「产出真的漏了」，是正则被语法字符污染。

纪律
────
· 只写期刊公开摘要与 PubMed 元数据给出的事实；付费墙未获取处一律标「待补全文」，定量不臆测。
· 证据分级：A=人体研究 / B=临床前（动物·细胞·体外）/ C=综述·观点·方案（依全站 notice-box 口径）。
· 内部链接 slug 全部取自 data/articles.json 且经 news/ 目录实际存在性校验。
"""
import html
import importlib.util
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATE = "2026-10-16"
CARDS = os.path.join(ROOT, ".intake/raw/lit-2026-10-16.cards.json")

# ── 已在站、不重复写的卡片（DOI 精确命中 2 条 + 内容硬核验命中 1 条）──
SKIP = {
    "N02": "DOI 精确命中 news/RamanOmics-Senescence-Detection-Nature-Aging-2026.html",
    "N10": "DOI 精确命中 news/Multimorbidity-Patterns-SPRINTT-Mobility-Nature-Aging-2026.html",
    "N04": "站内文无 DOI，四路查重判不出；AdipoRon/卵巢衰老/15万人UKB 硬核验为同篇 "
           "news/Exercise-Slows-Ovarian-Aging-Nature-Aging-2026.html",
}

# ── 主题 ──
TOPIC = {
    "N01": "表观遗传", "N03": "免疫与炎症", "N05": "免疫与炎症", "N06": "器官衰老",
    "N07": "器官衰老", "N08": "器官衰老", "N09": "免疫与炎症", "N11": "生命历程",
    "N12": "神经退行", "N13": "神经退行", "N14": "神经退行", "N15": "神经退行",
    "N16": "方法与工具", "N17": "免疫与炎症", "M01": "代谢与营养",
    "C01": "神经退行", "C02": "神经退行", "C03": "表观遗传", "C04": "神经退行",
    "C05": "神经退行",
    "A01": "细胞衰老", "A02": "细胞衰老", "A03": "器官衰老", "A04": "表观遗传",
    "A05": "神经退行", "A06": "细胞衰老", "A07": "器官衰老", "A08": "免疫与炎症",
    "A09": "方法与工具", "A10": "器官衰老", "A11": "细胞衰老", "A12": "生命历程",
    "A13": "细胞衰老", "A14": "细胞衰老", "A15": "代谢与营养", "A16": "器官衰老",
    "A17": "器官衰老", "A18": "表观遗传", "A19": "器官衰老", "A20": "方法与工具",
    "A21": "免疫与炎症", "A22": "器官衰老",
    "G01": "临床与转化", "G02": "器官衰老", "G03": "临床与转化", "G04": "方法与工具",
    "G05": "临床与转化", "G06": "代谢与营养", "G07": "器官衰老", "G08": "代谢与营养",
    "G09": "生命历程", "G10": "生命历程", "G11": "神经退行", "G12": "代谢与营养",
    "G13": "生命历程", "G14": "神经退行", "G15": "临床与转化", "G16": "神经退行",
    "G17": "代谢与营养", "G18": "表观遗传", "G19": "生命历程", "G20": "临床与转化",
    "G21": "临床与转化", "G22": "生命历程",
}

# ── 证据分级：A 人体 / B 临床前 / C 综述·观点·方案 ──
EV = {
    # A：以人体队列、RCT、人体组织/尸检样本为主要证据
    "N09": "A", "N13": "A", "N14": "A", "N15": "A", "C04": "A", "C05": "A",
    "A05": "A", "A08": "A", "A10": "A", "A12": "A", "A18": "A", "A19": "A",
    "G05": "A", "G07": "A", "G08": "A", "G09": "A", "G10": "A", "G11": "A",
    "G12": "A", "G15": "A", "G16": "A", "G17": "A", "G18": "A", "G19": "A",
    "G20": "A", "G22": "A",
    # C：综述 / 观点 / 概念框架 / 试验方案
    "N11": "C", "C02": "C", "A02": "C", "A04": "C", "A13": "C", "A15": "C",
    "G01": "C", "G03": "C", "G04": "C", "G06": "C", "G13": "C", "G21": "C",
}
DEFAULT_EV = "B"      # 其余为动物 / 细胞 / 体外 / 类器官模型

# ── 栏目标签 ──
TAG_METHOD = {"N16", "A09", "A20", "G04"}
TAG_TRIAL = {"G21"}

JOURNAL = {"N": "NatureAging", "M": "CellMetabolism", "C": "Cell",
           "A": "AgingCell", "G": "GeroScience"}
JOURNAL_CN = {"N": "Nature Aging", "M": "Cell Metabolism", "C": "Cell",
              "A": "Aging Cell", "G": "GeroScience"}

STOP = {"the", "and", "for", "with", "from", "that", "this", "into", "across",
        "during", "using", "based", "between", "within", "through", "their",
        "its", "via", "not", "but", "how", "what", "when", "why", "can", "does"}


def md_bold(s):
    """Markdown 粗体 → <strong>；其余原样（站内正文统一用 HTML）"""
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s or "")


def plain(s):
    return re.sub(r"\*+", "", s or "").strip()


def bullets(body):
    """从卡片正文抽出 8 个标准字段的条目文本"""
    out = {}
    for line in body.splitlines():
        m = re.match(r"^- \*\*(.+?)\*\*[：:]\s*(.*)$", line.strip())
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


def make_slug(code, title_en, used):
    words = [w for w in re.findall(r"[A-Za-z0-9⁺\-]+", title_en)
             if w.lower() not in STOP]
    keep, n = [], 0
    for w in words:
        w = w.replace("⁺", "").strip("-")
        if not w or len(w) < 2:
            continue
        keep.append(w[:1].upper() + w[1:])
        n += 1
        if n >= 5:
            break
    base = "-".join(keep) + "-" + JOURNAL[code[0]] + "-2026"
    slug = base
    i = 2
    while slug + ".html" in used:
        slug = f"{base}-{i}"
        i += 1
    return slug + ".html"


def main():
    cards = json.load(open(CARDS, encoding="utf-8"))
    arts = json.load(open(os.path.join(ROOT, "data/articles.json"), encoding="utf-8"))
    bytopic = {}
    for a in arts:
        p = os.path.join(ROOT, "news", a["slug"])
        if os.path.exists(p):                      # slug 必须真实存在，不靠记忆
            bytopic.setdefault(a.get("topic", ""), []).append((a["slug"], a["title"]))

    sys.argv = ["gen_articles.py", ROOT, "/dev/null", DATE]
    _spec = importlib.util.spec_from_file_location(
        "ga", os.path.join(ROOT, "scripts", "gen_articles.py"))
    ga = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(ga)

    A, used = {}, {a["slug"] for a in arts}
    skipped = []
    for c in cards:
        code = c["code"]
        if code in SKIP:
            skipped.append(code)
            continue
        b = bullets(c["body"])
        # ⚠️ 产出侧 DOI 是 Markdown 链接 `[10.xxxx/y](https://doi.org/10.xxxx/y)`。
        # 字符集里若带上 `[` `]`，匹配会把 `](https://doi.org/...` 整段吞进来
        # （与 harvest.normalize_doi 同一个坑），DOI 显示成乱码。到 `]` 必须停。
        doi = re.search(r"10\.\d{4,9}/[^\s\])\[<]+", c["doi"] or "")
        doi = doi.group(0).rstrip(".,;:") if doi else ""
        pmid = (c["pmid"] or "").split("｜")[0].strip()
        jcn = JOURNAL_CN[code[0]]
        ev = EV.get(code, DEFAULT_EV)
        topic = TOPIC[code]
        tag = ("方法学" if code in TAG_METHOD else
               "临床试验" if code in TAG_TRIAL else
               "综述" if ev == "C" else "研究进展")
        slug = make_slug(code, c["title_en"] or c["title_cn"], used)
        used.add(slug)

        rel = [(s, t) for s, t in bytopic.get(topic, [])[:3]]
        title = c["title_cn"].strip()
        desc = plain(b.get("一句话核心结论", ""))[:150]

        src = (f'<em>{html.escape(jcn)}</em> · 论文：{html.escape(c["title_en"])}'
               + (f' · DOI <a href="https://doi.org/{doi}" target="_blank" '
                  f'rel="noopener noreferrer">{doi}</a>' if doi else "")
               + (f' · PMID {html.escape(pmid)}' if pmid else "")
               + ' · 来源：IMA 知识库《五刊监控·深度文献卡片》2026-10-16 期（摘要级）')

        body = f"""<p><strong>一句话结论：</strong>{md_bold(b.get('一句话核心结论', ''))}</p>

<h2>这项研究想回答什么</h2>
<p>{md_bold(b.get('研究问题', ''))}</p>

<h2>他们怎么做的</h2>
<p>{md_bold(b.get('方法', ''))}</p>

<h2>核心发现</h2>
<p>{md_bold(b.get('核心发现', ''))}</p>

<h2>定量结果与证据边界</h2>
<p>{md_bold(b.get('定量', ''))}</p>
<p><strong>局限：</strong>{md_bold(b.get('局限', ''))}</p>

<h2>为什么值得关注</h2>
<p>{md_bold(b.get('对我的价值', ''))}</p>

<p><strong>全文状态：</strong>{md_bold(b.get('全文状态', '摘要级'))}。本文依据期刊公开摘要与 PubMed 元数据撰写，未获取付费墙全文，<strong>所有未在摘要中给出的定量一律标注「待补全文」，未做任何推算补全</strong>。</p>"""

        A[slug] = dict(topic=topic, ev=ev, tag=tag, title=title,
                       crumb=title[:20], desc=desc, source=src,
                       body=body, related=rel)

    print(f"卡片 {len(cards)} 张 · 已在站跳过 {len(skipped)} 张（{skipped}）"
          f" · 本批新写 {len(A)} 篇")
    ga.A = A
    ga.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
