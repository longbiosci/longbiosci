#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_articles_intake_2026-10-31a.py —— 内容摄入第 20 批
（元层《预印本全文级解读_2026-10-31》，73 篇解读 → 72 篇上站）

来源与判空
────────
事实源：元层目录 `预印本全文级解读_2026-10-31/`（78 条目），经实际下载核验：
  · 运行摘要 dptYMNcBrauv 6,931 B、总索引 dOPAHGhHVZOl 17,412 B、
    全集打包 dcMpxitvxhSW 163,130 B（解包 78 文件）、日志副本 dKxOKqqdZpcV 278 B
  · 上游《预印本速递_2026-10-31》dENskhRbTohZ 232,160 B、总表 dzHcjRDLvvGu 98,681 B
字节数与 dir_list 缓存一致，且内容非空 → 三道闸全过（非空产、非错位、载体正确）。

成稿范围（产能不设上限）
────────
上游交付 74 条（主榜 21 + 观察哨 53），元层成稿 73 条（1 条按 DOI 去重跳过）。
本批把 73 条**全部逐条过查重**，不做抽样、不设篇数上限：
  · 真重复跳过 1 条：主榜 19（10.64898/2026.05.01.26352140）——DOI 精确命中站内
    `Peripheral-Epigenetic-Aging-Centenarians-2026.html`，且该页正文含该 DOI → 跳过并计数。
  · 词元疑似命中 7 条，逐条 grep 正文核验后确认**均为误命中**（站内文章 DOI 与
    新条目 DOI 不同、且站内文早于预印本上线）→ 全部成篇。
  · 实上站 **72 篇**。

证据分级口径
────────
全部 73 条均为**摘要级**（元层未取得任何 PDF 全文，medRxiv/bioRxiv 主站 Cloudflare 403）。
站内只有 A/B/C 三级，且 C 的定义即「预印本 / 观点评论，非原始研究」，故：
  · 上游评级 C/D → **C 级**（69 条）
  · 上游评级 A/B 且为人体观察研究 → **B 级**（3 条：主榜 5 / 7 / 21）
差别在正文明示，不用分级掩盖「这是未经同行评审的预印本」。

规则③时间标签
────────
每篇正文首行写明：**数据日期 YYYY-MM-DD · 生成时间 2026-10-31 05:30**，
数据日期取上游解读自述的 `data_date`（10-28 / 10-29 / 10-30 三窗口），
不用发布日期冒充情报发生日。
"""
import html
import importlib.util
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATE = "2026-10-31"
GEN_AT = "2026-10-31 05:30"
BATCH_DIR = os.path.join(ROOT, ".intake/raw/tar1031/预印本全文级解读_2026-10-31")

# 真重复：DOI 精确命中站内且正文含该 DOI
SKIP_DOIS = {"10.64898/2026.05.01.26352140"}


# ───────────────────────── 主题映射 ─────────────────────────
TOPIC_RULES = [
    ("神经退行", ["阿尔茨海默", "痴呆", "帕金森", "认知", "脑", "神经", "tau", "淀粉样",
               "突触", "海马", "TREM2", "synuclein", "AD ", "AD病", "额", "皮层",
               "neurodegenerat", "dementia", "Alzheimer", "Parkinson", "cogniti",
               "brain", "neuro", "hippocamp", "cortex", "cortical"]),
    ("表观遗传", ["甲基化", "表观", "时钟", "DNAm", "GrimAge", "DunedinPACE", "染色质",
               "methylation", "epigenetic", "clock", "chromatin"]),
    ("细胞衰老", ["衰老细胞", "senolytic", "senescen", "SASP", "p16", "p21", "SA-β-gal",
               "细胞衰老", "senomorph", "senotype", "衰老型", "senCAF"]),
    ("免疫与炎症", ["炎症", "免疫", "T 细胞", "T细胞", "巨噬", "小胶质", "细胞因子",
                 "IFN", "CXCL", "CXCR3", "淋巴", "inflamm", "immun", "macrophage",
                 "microglia", "cytokine", "lymphocyte"]),
    ("线粒体", ["线粒体", "mitochondri", "呼吸链", "ROS", "氧化磷酸化"]),
    ("干细胞", ["干细胞", "造血", "HSC", "stem cell", "hematopoiet", "重编程",
              "Yamanaka", "reprogram"]),
    ("代谢与营养", ["饮食", "营养", "膳食", "代谢", "BMI", "蛋白质摄入", "肥胖", "葡萄",
                 "胰岛素", "脂", "diet", "nutrition", "metabol", "obesity",
                 "glucose", "insulin", "lipid"]),
    ("器官衰老", ["肌肉", "骨骼", "骨", "心肌", "心", "肝", "肾", "肺", "皮肤", "卵巢",
               "肌少", "脆弱", "衰弱", "内皮", "脂肪", "muscle", "bone", "skeletal",
               "cardiac", "liver", "kidney", "ovarian", "adipo", "endothel",
               "sarcopenia", "frail"]),
    ("方法与工具", ["时钟", "模型", "算法", "工具", "平台", "测序", "影像", "MRI",
                 "图谱", "单细胞", "snRNA", "空间转录", "model", "algorithm",
                 "atlas", "single-cell", "sequencing", "imaging", "framework"]),
    ("生命历程", ["寿命", "死亡率", "百岁", "队列", "流行病", "跨代", "生育", "生命历程",
                "lifespan", "mortality", "centenarian", "cohort", "epidemiolog"]),
]
CAT_FALLBACK = {
    "neuroscience": "神经退行", "neurology": "神经退行",
    "immunology": "免疫与炎症", "inflammation": "免疫与炎症",
    "genetics": "表观遗传", "epigenetics": "表观遗传", "genomics": "表观遗传",
    "cell biology": "细胞衰老", "cancer biology": "细胞衰老",
    "metabolism": "代谢与营养", "nutrition": "代谢与营养",
    "physiology": "器官衰老", "musculoskeletal": "器官衰老",
    "systems biology": "方法与工具", "bioinformatics": "方法与工具",
    "epidemiology": "生命历程", "public health": "生命历程",
    "stem cells": "干细胞", "development": "干细胞",
}


def pick_topic(title_cn, title_en, cat):
    blob = f"{title_cn} {title_en}".lower()
    best, hits = None, 0
    for topic, kws in TOPIC_RULES:
        n = sum(1 for k in kws if k.lower() in blob)
        if n > hits:
            best, hits = topic, n
    if best:
        return best
    return CAT_FALLBACK.get((cat or "").strip().lower(), "生命历程")


# ───────────────────────── Markdown → HTML ─────────────────────────
def md_inline(s):
    s = html.escape(s.strip(), quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
               r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>', s)
    s = re.sub(r"(?<![\"=])https?://[^\s<）)]+",
               lambda m: (f'<a href="{m.group(0)}" target="_blank" '
                          f'rel="noopener noreferrer">{m.group(0)}</a>'), s)
    return s


def md_block(text):
    """把一段 Markdown 正文转成 HTML 段落/列表/引用。"""
    out, buf, inlist = [], [], False

    def flush():
        nonlocal buf
        if buf:
            t = md_inline(" ".join(buf))
            if t:
                out.append(f"<p>{t}</p>")
            buf = []

    for raw in text.split("\n"):
        line = raw.rstrip()
        if not line.strip():
            flush()
            if inlist:
                out.append("</ul>")
                inlist = False
            continue
        if line.startswith("```"):
            continue
        if re.match(r"^\s*[-*]\s+", line):
            flush()
            if not inlist:
                out.append("<ul>")
                inlist = True
            item = re.sub(r"^\s*[-*]\s+", "", line)
            out.append(f"<li>{md_inline(item)}</li>")
            continue
        if line.startswith(">"):
            flush()
            if inlist:
                out.append("</ul>")
                inlist = False
            q = line.lstrip("> ").strip()
            if q:
                out.append(f"<blockquote><p>{md_inline(q)}</p></blockquote>")
            continue
        if inlist:
            out.append("</ul>")
            inlist = False
        buf.append(line.strip())
    flush()
    if inlist:
        out.append("</ul>")
    return "\n".join(out)


# ───────────────────────── 解析解读文件 ─────────────────────────
SEC_RE = re.compile(r"^##\s*(\d+)\.\s*(.+?)\s*$")


def parse_md(path):
    txt = open(path, encoding="utf-8").read()
    m = re.match(r"^#\s*预印本解读\s*·\s*(.+?)\s*·\s*(.+?)\s*$", txt, re.M)
    key = m.group(1).strip() if m else ""
    title_cn = m.group(2).strip() if m else ""
    secs, cur, buf = {}, None, []
    for line in txt.split("\n"):
        s = SEC_RE.match(line)
        if s:
            if cur is not None:
                secs[cur] = "\n".join(buf).strip()
            cur = int(s.group(1))
            buf = []
        elif cur is not None:
            buf.append(line)
    if cur is not None:
        secs[cur] = "\n".join(buf).strip()
    return key, title_cn, secs


def meta_table(sec0):
    """解析第 0 节元信息表 → dict"""
    d = {}
    for line in (sec0 or "").split("\n"):
        m = re.match(r"^\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*$", line)
        if not m:
            continue
        k, v = m.group(1).strip(), m.group(2).strip()
        if k in ("项", "值") or set(k) <= set("-: "):
            continue
        d[k] = v
    return d


def strip_md(s):
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s or "")
    s = s.replace("`", "").strip()
    return s


# ───────────────────────── slug ─────────────────────────
STOP = {"the", "a", "an", "of", "in", "on", "and", "or", "for", "to", "with",
        "by", "at", "from", "as", "is", "are", "be", "does", "do", "but",
        "not", "via", "its", "it", "that", "this", "their", "our", "we",
        "across", "during", "after", "before", "between", "into", "over",
        "under", "upon", "than", "then", "when", "which", "who", "how"}


def slugify(title_en, year=2026):
    words = re.findall(r"[A-Za-z][A-Za-z0-9\-]*", title_en or "")
    words = [w for w in words if w.lower() not in STOP]
    out, seen = [], set()
    for w in words:
        lw = w.lower()
        if lw in seen:
            continue
        seen.add(lw)
        out.append(w[:1].upper() + w[1:])
        if len("-".join(out)) > 58:
            break
    s = "-".join(out) or "Preprint"
    s = re.sub(r"-+", "-", s).strip("-")
    return f"{s}-{year}.html"


# ───────────────────────── 主流程 ─────────────────────────
def notice(ev, mode="abstract"):
    """签名与 gen_articles.build 的调用保持一致（build 传两个位置参数）。"""
    t = {"A": "A 级（同行评议人体研究）",
         "B": "B 级（人体观察性研究，未经同行评审的预印本）",
         "C": "C 级（预印本，未经同行评审；本页为摘要级，未核至全文）"}[ev]
    extra = {
        "B": ("<p><strong>本文为预印本，未经同行评审。</strong>上游评级较高（人体研究、"
              "摘要含定量），但本页仍<strong>只依据官方摘要原文</strong>撰写，"
              "<strong>未取得并核对 PDF 全文</strong>，结论可能在正式发表时变更。</p>"),
        "C": ("<p><strong>本文为预印本，未经同行评审；且本页为「摘要级」——"
              "未取得 PDF 全文（源站封锁），全部结论只依据官方 API 摘要原文。</strong>"
              "效应量、样本量、统计方法与多重比较校正在多数条目中仍未知，"
              "摘要未给出之处一律写「未给出」/「待补全文」，<strong>未做任何数值推算补全</strong>。</p>"),
    }[ev]
    return (f'<div class="notice-box">\n'
            f'    <p><span class="tier tier-{ev.lower()}">{ev} 级</span>'
            f'<strong>证据分级：{t}</strong></p>\n'
            f'    {extra}\n'
            f'    <p><strong>关于本文的文献来源：</strong>本站依据元层'
            f'《预印本全文级解读_2026-10-31》（上游《预印本速递_2026-10-31》）撰写，'
            f'附官方 abstract 原文供逐字回溯。</p>\n'
            f'</div>')


def main():
    items = json.load(open(os.path.join(BATCH_DIR, "_items.json"), encoding="utf-8"))
    arts = json.load(open(os.path.join(ROOT, "data/articles.json"), encoding="utf-8"))
    existing = {a["slug"] for a in arts}

    A, skipped_dup, planned = {}, [], 0
    used_slugs = set(existing)

    for it in items:
        doi = it["doi"]
        if doi in SKIP_DOIS:
            skipped_dup.append((it["key"], doi, "站内 DOI 精确命中 + 正文含该 DOI"))
            continue
        planned += 1
        path = os.path.join(BATCH_DIR, it["file"])
        if not os.path.exists(path):
            print(f"  ⚠ 缺文件 {it['file']}")
            continue
        key, title_cn, secs = parse_md(path)
        meta = meta_table(secs.get(0, ""))
        title_en = strip_md(meta.get("标题（原文）", "")) or (it.get("title_orig") or "")
        cat = strip_md(meta.get("分类", ""))
        corr = strip_md(meta.get("通讯作者", ""))
        plat = strip_md(meta.get("预印本平台", "")) or it.get("server", "预印本")
        data_date = it.get("data_date") or DATE

        topic = pick_topic(title_cn or it.get("title", ""), title_en, cat)
        ev = "B" if it.get("rating") in ("A", "B") else "C"

        # slug 唯一化
        base = slugify(title_en)
        slug, n = base, 1
        while slug in used_slugs:
            n += 1
            slug = base.replace(".html", f"-{n}.html")
        used_slugs.add(slug)

        # desc：取「一句话贡献」或编辑研判首句
        s3 = secs.get(3, "")
        contrib = ""
        for line in s3.split("\n"):
            if "一句话贡献" in line:
                contrib = re.sub(r"^\s*[-*]\s*", "", line)
                contrib = re.sub(r"^\*\*一句话贡献\*\*[：:]\s*", "", contrib)
                break
        fallback = strip_md(secs.get(6, "").split("\n")[0]) if secs.get(6) else ""
        desc = strip_md(contrib) or fallback or strip_md(it.get("title", ""))
        desc = re.sub(r"\s+", " ", desc)[:120]

        tier_cn = "主榜" if it.get("tier") == "主榜" else "观察哨"
        crumb = f"预印本{tier_cn}·{data_date}"

        src = (f'<em>{html.escape(plat)}</em> · 预印本（{html.escape(cat or "未分类")}）：'
               f'{html.escape(title_en)} · DOI '
               f'<a href="https://doi.org/{doi}" target="_blank" '
               f'rel="noopener noreferrer">{doi}</a>'
               + (f' · 通讯 {html.escape(corr[:60])}' if corr else "")
               + f' · 来源：《预印本全文级解读_2026-10-31》（{tier_cn}{it.get("no", "")}）')

        parts = []
        parts.append(
            f'<p><strong>时间标签：数据日期 {data_date} · 生成时间 {GEN_AT}</strong>'
            f'（Asia/Shanghai）｜ 档位：{tier_cn}{it.get("no", "")} ｜ '
            f'窗口 {it.get("window", "")} ｜ 上游评级 {it.get("rating", "")}</p>')
        for num, h in ((1, "这项研究想回答什么"),
                       (2, "方法与数据"),
                       (3, "核心结论")):
            if secs.get(num):
                parts.append(f"<h2>{h}</h2>\n{md_block(secs[num])}")
        if secs.get(4):
            parts.append(f"<h2>局限与未核验项</h2>\n{md_block(secs[4])}")
        if secs.get(5):
            parts.append(f"<h2>对本领域的价值</h2>\n{md_block(secs[5])}")
        if secs.get(6):
            parts.append(f"<h2>编辑研判</h2>\n{md_block(secs[6])}")
        if secs.get(7):
            abs_txt = secs[7]
            m = re.search(r"```text\n(.*?)```", abs_txt, re.S)
            raw = m.group(1).strip() if m else abs_txt
            parts.append(
                "<h2>官方摘要原文（逐字，供回溯）</h2>\n"
                f"<details><summary>展开 api.biorxiv.org / api.medrxiv.org 返回的 "
                f"abstract 原文</summary>\n<blockquote><p>"
                f"{html.escape(raw).replace(chr(10), '<br>')}</p></blockquote>\n</details>")
        parts.append(
            f'<p class="muted">本文为<strong>预印本</strong>，未经同行评审，'
            f'结论可能在正式发表时变更。生成任务 12819187（预印本全文级解读）· '
            f'上游 12784209（预印本速递）。</p>')

        A[slug] = dict(
            topic=topic, ev=ev, tag="预印本",
            title=(title_cn or it.get("title", ""))[:80],
            crumb=crumb, desc=desc, source=src,
            body="\n".join(parts),
            related=[],
        )

    print(f"计划成篇 {planned} 篇；查重跳过 {len(skipped_dup)} 条：")
    for k, d, why in skipped_dup:
        print(f"   ⏭ {k} {d} —— {why}")

    sys.argv = ["gen_articles.py", ROOT, "/dev/null", DATE]
    spec = importlib.util.spec_from_file_location(
        "ga", os.path.join(ROOT, "scripts", "gen_articles.py"))
    ga = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ga)
    ga.A = A
    ga.notice = notice
    ga.main()


if __name__ == "__main__":
    main()
