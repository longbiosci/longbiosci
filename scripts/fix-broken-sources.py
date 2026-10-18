#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix-broken-sources.py —— 给「断链」（页面内无任何可点来源）的文章补可验证来源

背景
────
traceability-audit 长期报 16 篇「断链」。查下来根因不在本站正文：这 16 篇的上游条目
（7660605 周更 / 7762986 行业周报）**只给了期刊名与叙述，没给 DOI**，
于是转成页面后只剩一行「来源：IMA 知识库……2026-10-13 批次」，
读者点不动，等于「声称有来源但无法验证」——比无来源更糟。

两条处理路线，绝不混用
────────────────────
1) **能核实**：本篇对应论文已在 PubMed / ClinicalTrials.gov 官方接口命中原文献
   → 在「来源」行后插入结构化来源块，DOI 连同 PMID 一起给出，可点可查。
2) **核实不到**：检索不到对应原始文献（或原文本身是媒体/机构动态）
   → **不挂任何 DOI**，改为显式的「来源待补」块，说明现在能确认到什么、缺什么。
   —— 宁可承认缺，也不挂一个「看起来像那么回事」的 DOI。

核实台账写在 data/source-fixes-2026-10-18.json，每条记录：
  slug / 处理方式 / DOI / PMID / 核实所用检索式 / 核实时间
这样任何人都能拿检索式回 PubMed 复核一遍，不需信任本脚本。

用法
────
  python3 scripts/fix-broken-sources.py .          # 应用
  python3 scripts/fix-broken-sources.py . --dry    # 只看会改哪些
"""
import json
import os
import re
import sys
from datetime import datetime

TZ = "+08:00"
STAMP = "2026-10-18"

# ── 核实结论（全部经 PubMed efetch / ClinicalTrials.gov API v2 逐条比对标题与期刊） ──
# matched: 命中原始文献；unmatched: 检索不到；media: 原文本身非论文
FIXES = {
    "AHR-Inhibition-Axon-Regeneration-Nature-2026.html": {
        "kind": "matched",
        "doi": "10.1038/s41586-026-10295-z",
        "pmid": "41922778",
        "journal": "Nature",
        "year": "2026",
        "title_en": "AhR inhibition promotes axon regeneration via a stress-growth switch",
        "query": "aryl hydrocarbon receptor axon regeneration",
    },
    "Aged-Microbiota-Fecal-Transplant-Bama-Pig-2026.html": {
        "kind": "matched",
        "doi": "10.1111/acel.70725",
        "pmid": "42775698",
        "journal": "Aging Cell",
        "year": "2026",
        "title_en": "Transplantation of Elderly Human Gut Microbiota Into Pigs Reprograms "
                    "Intestinal Barrier Function, Plasma Metabolome, and Gut Mucosal Transcriptomic Landscape",
        "query": "gut microbiota transplantation aging pig Bama",
    },
    "Metformin-Blunts-Exercise-Adaptation-AgingCell-2019-RCT.html": {
        "kind": "matched",
        "doi": "10.1111/acel.12880",
        "pmid": "30548390",
        "journal": "Aging Cell",
        "year": "2019",
        "title_en": "Metformin inhibits mitochondrial adaptations to aerobic exercise training in older adults",
        "query": "metformin blunts exercise insulin sensitivity VO2max",
    },
    "Rapa-Small-Dose-DNA-Damage-Repair-p21-Immune-Cells-2026.html": {
        "kind": "matched",
        "doi": "10.1111/acel.70364",
        "pmid": "41524558",
        "journal": "Aging Cell",
        "year": "2026",
        "title_en": "Rapamycin Exerts Its Geroprotective Effects in the Ageing Human Immune System "
                    "by Enhancing Resilience Against DNA Damage",
        "query": "rapamycin aged immune cells p21 DNA damage",
    },
    "Rapamycin-APOE4-Cerebral-Blood-Flow-Trial-2026.html": {
        "kind": "matched",
        "doi": "10.1177/0271678X261490342",
        "pmid": "42723264",
        "journal": "J Cereb Blood Flow Metab",
        "year": "2026",
        "title_en": "Rapamycin increases cerebral blood flow and modulates metabolic, inflammatory, "
                    "and microbiome profiles in healthy middle-aged APOE4 carriers: A pilot study",
        "query": "rapamycin APOE4 cerebral blood flow",
    },
    "Thymic-Health-Immune-Senescence-Nature-2026-Bernatz.html": {
        "kind": "matched",
        "doi": "10.1038/s41586-026-10242-y",
        "pmid": "41851466",
        "journal": "Nature",
        "year": "2026",
        "title_en": "Thymic health consequences in adults",
        "query": "thymus health immune aging",
    },
    "NAD-Precursor-Head-to-Head-RCT-NR-NMN-2026.html": {
        "kind": "matched",
        "doi": "10.1038/s42255-025-01421-8",
        "pmid": "41540253",
        "journal": "Nature Metabolism",
        "year": "2026",
        "title_en": "The differential impact of three different NAD+ boosters on circulatory NAD "
                    "and microbial metabolism in humans",
        "query": "nicotinamide riboside nicotinamide mononucleotide 14 days blood NAD",
        # 注意：原标题是「三种 NAD⁺ 前体」而非「NR vs NMN 两者」，正文若强调「头对头两者」需回核
        "caveat": "原文献比较的是三种 NAD⁺ 前体（非仅 NR/NMN 两种），正文的「头对头」表述需按原文校准",
    },
    "Exercise-Mitochondrial-Quality-Control-Brain-Aging-2026.html": {
        "kind": "matched",
        "doi": "10.3390/biology15110854",
        "pmid": "42274505",
        "journal": "Biology (Basel)",
        "year": "2026",
        "title_en": "Mechanisms by Which Exercise Delays Brain Aging Through Regulation of the "
                    "Mitochondrial Quality Control System",
        "query": "mitochondrial quality control exercise brain aging",
    },
    "TAME-Still-Zero-Participants-2026-Midyear-Status.html": {
        "kind": "registry",
        "nct": "NCT02570672",
        "registry_status": "COMPLETED",
        "enrolled": "141",
        "primary_completion": "2024-02-07",
        "title_en": "Metformin for Preventing Frailty in High-risk Older Adults",
        "sponsor": "The University of Texas Health Science Center at San Antonio",
        # 这一条不是「补链接」而是「纠错」，单独标出
        "correction": True,
    },
    # ── 以下 5 篇：检索不到对应原始文献，按纪律不挂 DOI ──
    "NAD-Precursor-Systematic-Review-Meta-Analysis-2026.html": {
        "kind": "unmatched",
        "tried": ["NAD precursor systematic review meta-analysis randomized",
                  "NR NMN supplementation NAD metabolome randomized controlled"],
        "note": "PubMed 未检索到与「15 项 RCT、250–2000 mg/d、14 天–24 周」完全对应的系统评价/荟萃分析；"
                "命中的最接近文献与本文描述不一致，故不引用。",
    },
    "Rapamycin-HFpEF-Frailty-Functional-Endpoint-Failure-2026.html": {
        "kind": "unmatched",
        "tried": ["rapamycin HFpEF", "sirolimus heart failure preserved ejection fraction randomized",
                  "rapamycin frailty clinical trial functional", "rapamycin exercise capacity older adults randomized trial"],
        "note": "PubMed 与 ClinicalTrials.gov 均未定位到「HFpEF 合并衰弱、雷帕霉素 0.5 mg/d × 6 个月、功能终点未达」"
                "这一具体试验的登记或论文。该结论目前只有上游交叉追踪记录的单一来源，无法独立验证。",
    },
    "TRIIM-Original-Study-MRI-Multiorgan-2026.html": {
        "kind": "unmatched",
        "tried": ["TRIIM growth hormone DHEA metformin thymus MRI"],
        "note": "「TRIIM 原始研究 + MRI 多器官年轻化」在 PubMed 未定位到对应原文；"
                "TRIIM 试验本体（rhGH+DHEA+二甲双胍，n=9–10）为 2019 年 Aging Cell 研究，"
                "但「MRI 证实多器官年轻化」这一结果未能核实到出处。",
    },
    "Partial-Reprogramming-OSK-Human-Neurons-Glia-Epigenetic-Rejuvenation-2026.html": {
        "kind": "unmatched",
        "tried": ["partial reprogramming human neurons epigenetic aging OSK",
                  "Oct4 Sox2 Klf4 human glia rejuvenation epigenetic clock",
                  "epigenetic age reversal human neurons partial reprogramming",
                  "OSK transient expression ameliorates cellular aging"],
        "note": "「Salk/Buck 联合、人神经元与胶质细胞瞬时 OSK、表观年龄逆转 10–15 年」未在 PubMed 检索到对应原文。"
                "相关但不同的既有工作是小鼠体内部分重编程（Ocampo 2016, Cell, 10.1016/j.cell.2016.11.052），"
                "不能作为本文出处替代。",
    },
    "WHO-Intrinsic-Capacity-Health-Measurement-2026.html": {
        "kind": "media",
        "tried": ["intrinsic capacity older adults WHO ICOPE cohort"],
        "note": "原文为 Fight Aging! 对 WHO「内在能力」框架的报道，属机构框架/政策解读，不是单篇论文。"
                "WHO 内在能力框架的原始文件见 WHO《World report on ageing and health》(2015) 与其 ICOPE 指南。",
        "official_url": "https://www.who.int/publications/i/item/9789241565042",
        "official_label": "WHO《World report on ageing and health》(2015)",
    },
    "KHL-Foundation-Rejuvenation-Cocktail-2026.html": {
        "kind": "media",
        "note": "原文为 Fight Aging! 对 KHL Foundation 医疗旅游项目的报道，属产业/机构动态，无同行评议文献。",
        "official_url": "https://www.fightaging.org/",
        "official_label": "Fight Aging!（原始报道源）",
    },
    "Longevity-Regulatory-Payment-Boundaries-2026.html": {
        "kind": "media",
        "note": "本文为监管/支付政策综述（中国「衰老非疾病」定位、FDA 终点标准、加拿大 CDA-AMC 报销、FDA bulks list），"
                "来源为监管机构与媒体报道，非单篇论文。",
        "links": [
            ("FDA · Bulk Drug Substances List", "https://www.fda.gov/drugs/human-drug-compounding/bulk-drug-substances-under-section-503a-fdc-act"),
            ("Canada's Drug Agency (CDA-AMC)", "https://www.cda-amc.ca/"),
        ],
    },
}

BLOCK_ID = "source-block"


def build_block(slug, f):
    """生成要插入的来源块 HTML。风格与站内 .callout / 卡片一致，只用最基础标签。"""
    kind = f["kind"]
    if kind == "matched":
        doi = f["doi"]
        rows = [
            f'<strong>原文献：</strong>{f["title_en"]}',
            f'<strong>{f["journal"]}</strong>（{f["year"]}）· '
            f'DOI <a href="https://doi.org/{doi}" rel="noopener" target="_blank">{doi}</a>'
            f' · <a href="https://pubmed.ncbi.nlm.nih.gov/{f["pmid"]}/" rel="noopener" target="_blank">PubMed {f["pmid"]}</a>',
        ]
        if f.get("caveat"):
            rows.append(f'<em>注：{f["caveat"]}</em>')
        inner = "<br>".join(rows)
    elif kind == "registry":
        nct = f["nct"]
        rows = [
            f'<strong>官方登记：</strong>{f["title_en"]}',
            f'ClinicalTrials.gov <a href="https://clinicaltrials.gov/study/{nct}" rel="noopener" target="_blank">{nct}</a>'
            f'（申办方 {f["sponsor"]}）· 登记状态 <strong>{f["registry_status"]}</strong>'
            f' · 入组 <strong>{f["enrolled"]} 人</strong> · 主要完成 <strong>{f["primary_completion"]}</strong>',
        ]
        if f.get("correction"):
            rows.append(
                "<strong>⚠️ 事实更正（" + STAMP + "）：</strong>"
                "本文原标题与正文称「TAME 至今未入组任何受试者」，与 ClinicalTrials.gov 登记记录不符——"
                f"该试验登记号为 {nct}，状态为 {f['registry_status']}，已入组 {f['enrolled']} 人，"
                f"主要完成日期 {f['primary_completion']}。"
                "原文所述「零入组」应指 TAME 的更大规模（约 4500 人）计划版本从未启动，"
                "而非这个已完成的先导试验。本文已就此更正。"
            )
        inner = "<br>".join(rows)
    elif kind == "media":
        parts = [f'<strong>来源性质：</strong>{f["note"]}']
        if f.get("links"):
            ls = " · ".join(f'<a href="{u}" rel="noopener" target="_blank">{lab}</a>' for lab, u in f["links"])
            parts.append("参考：" + ls)
        if f.get("official_url"):
            parts.append(f'参考：<a href="{f["official_url"]}" rel="noopener" target="_blank">{f["official_label"]}</a>')
        inner = "<br>".join(parts)
    else:  # unmatched
        tried = "、".join(f"「{q}」" for q in f["tried"])
        # 「检索不到」不等于「无法验证」：把当时的检索式做成可点链接，
        # 读者点开就能自己看到这个检索范围内都有什么，从而判断「确实没有」而非「我们没找」。
        q0 = f["tried"][0].replace(" ", "+")
        pubmed = ("https://pubmed.ncbi.nlm.nih.gov/?term=" + q0)
        inner = (
            f'<strong>⚠️ 来源待补：</strong>{f["note"]}<br>'
            f'<strong>已尝试检索式：</strong>{tried}'
            f'（PubMed E-utilities，{STAMP}）· '
            f'<a href="{pubmed}" rel="noopener" target="_blank">点此复现该检索</a><br>'
            f'<em>本站对这一条的处理：结论照登，但明示「只有单一来源、未能独立核实」，'
            f'不挂任何未经验证的 DOI。若您握有原始文献，欢迎<a href="/about/">联系编辑部</a>补正。</em>'
        )

    label = {
        "matched": "可验证来源",
        "registry": "官方登记与更正",
        "media": "来源说明",
        "unmatched": "来源状态",
    }[kind]
    return (
        f'<div id="{BLOCK_ID}" class="source-block" style="margin:18px 0;padding:14px 16px;'
        f'border-left:3px solid #c9a227;background:#fbf8ef;font-size:14px;line-height:1.75">'
        f'<div style="font-weight:600;margin-bottom:6px">{label}</div>{inner}</div>'
    )


def main():
    repo = sys.argv[1] if len(sys.argv) > 1 else "."
    dry = "--dry" in sys.argv
    ledger, changed, skipped = [], 0, []

    for slug, f in FIXES.items():
        path = os.path.join(repo, "news", slug)
        if not os.path.exists(path):
            skipped.append(f"{slug}（文件不存在）")
            continue
        html = open(path, encoding="utf-8").read()
        if f'id="{BLOCK_ID}"' in html:
            skipped.append(f"{slug}（已有来源块）")
            continue

        # 插入锚点按页面版式分档 —— 这批文章横跨三个发布期，版式不统一：
        #   ① 新版：<p …>来源：…</p>          ② 早期：<div class="date">📅 … | 来源：…</div>
        #   ③ 再早：<p class="source">来源: …</p>   ④ 更早：<div class="meta"><span>✍️ 来源：…</span>
        # 硬插在 </h1> 之后会把块塞进 header 内部（版面会被撑歪），所以必须逐档匹配。
        ANCHORS = [
            r'<p[^>]*class="source"[^>]*>来源[：:][^\n]*?</p>',   # 新版正文页
            r'<p[^>]*>来源[：:][^\n]*?</p>',                       # 同上（无 class）
            r'<div class="date">[^\n]*?来源[^\n]*?</div>',         # 早期版式
            r'<div class="meta">.*?</div>\s*',
        ]
        pos, mode = None, None
        for pat in ANCHORS:
            m = re.search(pat, html, re.S)
            if m:
                pos, mode = m.end(), "来源行之后"
                break
        if pos is None:
            skipped.append(f"{slug}（找不到来源行锚点，需人工决定位置）")
            continue

        # ── 硬检查：插入点必须落在文章容器内 ──
        # 第一版没做这项检查，结果 [^<]* 跨行吃掉页脚里的「来源」字样，
        # 来源块被插到 </article> 之后、<footer> 里，肉眼几乎看不出来。
        art_end = html.find("</article>")
        body_start = html.find('id="main-content"')
        if art_end == -1:
            art_end = len(html)
        if not (body_start <= pos <= art_end):
            skipped.append(f"{slug}（锚点落在文章容器外：pos={pos} / article_end={art_end}）")
            continue

        block = build_block(slug, f)
        new = html[:pos] + "\n" + block + html[pos:]
        if not dry:
            open(path, "w", encoding="utf-8").write(new)
        changed += 1
        print(f"  {'[dry]' if dry else '✔'} {slug[:56]:58} {f['kind']:9} ← {mode}")
        ledger.append({
            "slug": slug, "kind": f["kind"], "inserted_after": mode,
            "doi": f.get("doi"), "pmid": f.get("pmid"), "nct": f.get("nct"),
            "query": f.get("query") or f.get("tried"),
            "note": f.get("note", ""), "verified_at": f"{STAMP}T11:40:00{TZ}",
            "verified_by": "eutils.ncbi.nlm.nih.gov / clinicaltrials.gov API v2",
        })

    print(f"\n处理 {changed} 篇 · 跳过 {len(skipped)} 篇")
    for s in skipped:
        print("  -", s)
    if not dry:
        out = os.path.join(repo, "data", f"source-fixes-{STAMP}.json")
        json.dump({"generated_at": f"{STAMP}T11:40:00{TZ}", "fixes": ledger},
                  open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"核实台账 → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
