#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
harvest.py —— 知识库产出自动发现与漏收判定（LongBiosci 内容通道 v1.0）

存在理由
────────
项目里有 6 个自动化任务在持续产出内容（文献层深度卡片、行业情报周报、
临床试验清单、临床×文献交叉追踪、月度热点综述），产出落在网盘 IMA 知识库
目录。但此前这些产出与网站之间**没有通道**：631 条喂料条目全部标记
publish_status=待成稿 / fed_to_daily=false，即一次都没被消化。

本脚本负责通道的前半段——**发现 + 判定**，不做写作：
  1. 扫指定的网盘产出文件，抽出所有候选条目（文献 / 行业 / 试验）
  2. 用三路匹配对站内全库做漏收判定：
       ① DOI 精确匹配（扫 news/*.html 全文）
       ② slug 机制词匹配（分子/基因/方法名）
       ③ 标题 3-gram Jaccard 相似度
  3. 输出漏收清单 JSON，供 gen_articles.py /人工复核使用

三路判定的必要性与教训
──────────────────────
· 只查 data/articles.json 的DOI 字段是错的——该文件根本不存DOI，
  会得出「全是新文献」的错误结论。
· 只用短关键词做硬校验也是错的——`SIRT1` / `猕猴` / `p21` 这类词会命中
  完全不同的文章。本脚本的机制词表按「核心分子/基因/方法名」构造，
  且关键词命中后仍需人工复核（见 --review 产物 basis 字段）。

用法
────
  python3 scripts/harvest.py <ROOT> <产出文件...> [--mech mech.json] [--out out.json]

  mech.json 格式：{"C01": ["Bifidobacterium pseudocatenulatum", "5-AVAB"], ...}
  out.json 默认写到 <ROOT>/data/harvest-report.json
"""
import argparse
import glob
import json
import os
import re
import sys
from collections import Counter

# ---------- 机制词表：条目编号 → 核心分子/基因/方法/物种名 ----------
# 收录标准（两条，缺一不可）：
#   a. 足以把「同一研究的不同表述」归到一条
#   b. **足够具体**——不能用 aging / senolytic / cGAS / autophagy 这类通用词，
#      它们会命中站内任意一篇同领域文章，制造「假已收录」（实测 27 条误判）
# 词表可由 --mech 覆盖；条目编号在查不到时自动回退到全局模糊匹配。
DEFAULT_MECH = {
    "C01": ["pseudocatenulatum", "5-AVAB", "MicroAge"],
    "C05": ["PD-L2", "LINE1"],
    "C07": ["LINE1", "premature aging", "heterochromatin"],
    "C11": ["protein restriction", "adaptive response"],
    "C12": ["fisetin", "phenotypic screen"],
    "C15": ["CD38", "NAD metabolic reprogramming"],
    "C20": ["macaque", "CSF proteom"],
    "C21": ["glutamatergic", "Nefh", "Cdk5"],
    "C23": ["healthspan", "healthspan cliche"],
    "C24": ["LongevityBench"],
    "C25": ["caloric restriction", "somatic mutation"],
}
# 全局兜底：只在 code 查不到时启用，且只允许高特异词
FALLBACK_TERMS = [
    "pseudocatenulatum", "5-AVAB", "LINE1", "PD-L2", "fisetin", "MicroAge",
    "LongevityBench", "Neuromodulator", "CANTAB", "PrecivityAD", "senoMune",
    "SenoMune", "RLS-1496", "ER-100", "OSK", "TRIIM", "caloric restriction",
    "glutamatergic", "macaque", "CD38", "NAD+ precursor", "heart rate variability",
    "biological age", "somatic mutation",
]


def load_slugs_and_dois(root):
    """扫 news/*.html：收集所有站内 slug 与正文中的 DOI"""
    slugs, titles, dois = set(), {}, set()
    for p in sorted(glob.glob(os.path.join(root, "news", "*.html"))):
        slug = os.path.basename(p)
        if slug in ("index.html",) or slug.startswith("news-"):
            continue
        slugs.add(slug)
        h = open(p, encoding="utf-8", errors="ignore").read()
        m = re.search(r"<title>(.*?)</title>", h, re.S)
        if m:
            titles[slug] = re.sub(r"\s+", " ", m.group(1)).split(" — ")[0].strip()
        for d in re.findall(r"10\.\d{4,9}/[^\s\"'<>&]+", h):
            dois.add(d.rstrip(".,);</a>").lower())
    return slugs, titles, dois


def ngrams(s, n=3):
    s = re.sub(r"[^\w一-鿿]+", " ", s.lower()).strip()
    toks = s.split()
    if len(toks) < n:
        return {" ".join(toks)} if toks else set()
    return {" ".join(toks[i:i + n]) for i in range(len(toks) - n + 1)}


def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


# ---------- 产出解析 ----------
ROW = re.compile(r"^\s*\|\s*([A-Za-z]{0,4}\d{1,3})\s*\|", re.M)
# 深度卡片/周报里的编号形如N1、C12、M3、G7、B2（字母前缀）或纯数字（表格序号）
TITLE_HINTS = ("标题", "题目", "公司", "项目·靶点", "监管机构", "事项", "靶点", "名称")


def parse_md_tables(text):
    """解析 markdown 表格，返回 [{header, rows:[[cell,...]]}]
    按表头识别「标题」列，避免误把卷期/序号当标题"""
    tables, cur = [], None
    for line in text.splitlines():
        s = line.strip()
        if not (s.startswith("|") and s.endswith("|")):
            cur = None
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if all(set(c) <= set("-: ") for c in cells):      # 分隔行
            continue
        first = cells[0].strip().replace("*", "")
        # 表头：不含编号但含标题类列名，或首列是「项目/字段」这类说明词
        looks_like_header = (any(h in " ".join(cells) for h in TITLE_HINTS)
                             or re.match(r"^[#\-*|]*\s*(项目|字段|字段名|序号|编号)", first))
        if looks_like_header:
            cur = {"header": cells, "rows": []}
            tables.append(cur)
            continue
        # 数据行：首列必须是编号（N1/M3/C12/1/2/3...）。
        # 缺这一条会把「期号/监控期刊」等元信息表的行当成候选条目。
        if not re.match(r"^[A-Za-z]{0,4}\d{1,3}$", first):
            cur = None
            continue
        if cur is not None:
            cur["rows"].append(cells)
    return tables


def pick_title_col(header):
    for i, h in enumerate(header):
        if any(k in h for k in TITLE_HINTS):
            return i
    return 1 if len(header) > 1 else 0


def extract_doi(cells):
    for c in cells:
        for d in re.findall(r"10\.\d{4,9}/[^\s\"'<>&|\]]+", c):
            return d.rstrip(".,);").lower()
    return ""


def load_candidates(paths):
    """从产出文件（md/xlsx/json）抽候选条目"""
    items = []
    for p in paths:
        if p.endswith(".json"):
            items += json.load(open(p, encoding="utf-8"))
            continue
        text = (open(p, encoding="utf-8", errors="ignore").read()
                if not p.endswith(".xlsx") else _xlsx_text(p))
        for tb in parse_md_tables(text):
            if not tb["rows"]:
                continue
            ti = pick_title_col(tb["header"])
            for cells in tb["rows"]:
                if len(cells) <= ti:
                    continue
                title = re.sub(r"\*\*|\*|\[|\]|\(.*?\)", "",
                               cells[ti]).strip()
                joined = " ".join(cells)
                if len(title) < 12 or len(joined) < 20:
                    continue
                code = cells[0].strip()
                items.append({
                    "source_file": os.path.basename(p),
                    "table_header": " | ".join(tb["header"])[:200],
                    "code": code if re.match(r"^[A-Za-z]{1,4}\d{1,3}$", code) else "",
                    "title": title[:300],
                    "doi": extract_doi(cells),
                    "raw": joined[:600],
                })
    return items


def _xlsx_text(path):
    """极简 xlsx→文本（只用标准库 zipfile+re，避免引入依赖）"""
    import zipfile
    try:
        import openpyxl
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        lines = []
        for ws in wb.worksheets:
            for row in ws.iter_rows(values_only=True):
                cells = ["" if c is None else str(c) for c in row]
                if any(cells):
                    lines.append("| " + " | ".join(cells) + " |")
        return "\n".join(lines)
    except Exception:
        with zipfile.ZipFile(path) as z:
            shared = []
            if "xl/sharedStrings.xml" in z.namelist():
                raw = z.read("xl/sharedStrings.xml").decode("utf-8", "ignore")
                shared = re.findall(r"<t[^>]*>(.*?)</t>", raw, re.S)
            return "\n".join(shared)


# ---------- 判定 ----------
def judge(item, slugs, titles, dois, mech):
    """返回 (status, basis, confidence)
    confidence: high=DOI 精确命中 / medium=机制词命中 / low=标题相似 / none=无法判定

    ⚠️ 已知盲区（必须知道，否则会误信结论）：
    站内文章标题是**中文译名**，而文献产出给的往往是**英文原标题**。
    因此第三路「标题 3-gram 相似度」对英文文献条目**天然失效**
    （实测站内 414 篇标题 vs 英文原标题，相似度普遍 0.00）。
    结论：英文文献条目只能靠 DOI 或机制词判定，两者皆无时必须人工核对，
    harvest 会把 confidence=none 的条目标成「需人工核对」而不是武断判漏收。
    """
    doi = (item.get("doi") or "").lower()
    if doi and doi in dois:
        return "已收录", f"DOI 命中 {doi}", "high"

    code = item.get("code", "")
    # 机制词表按code 查（优先）；查不到则在全局词表里找——
    # 因为不同产出的编号前缀不一致（文献层用 N1/M3/C01，行业层用 1/2/3），
    # 只按 code 查会导致词表大面积失效（实测 45 条漏收里 0 条机制词命中）。
    keys = list(mech.get(code, []))
    if not keys:
        blob = (item["title"] + " " + item.get("raw", "")).lower()
        keys = [t for t in FALLBACK_TERMS if t.lower() in blob]
    hit = [k for k in keys if any(k.lower() in s.lower() for s in slugs)]
    if hit:
        return "已收录", f"slug 机制词命中 {hit}", "medium"

    tn = ngrams(item["title"])
    best, bs = 0.0, ""
    for slug, t in titles.items():
        j = jaccard(tn, ngrams(t))
        if j > best:
            best, bs = j, slug
    if best >= 0.34:
        return "已收录", f"标题 3-gram 相似 {best:.2f} → {bs}", "low"

    if not doi and not code:
        return "需人工核对", \
               f"无 DOI、无条目编号，标题相似度不可用（站内为中文译名 vs 英文原标题）→ {bs or 'N/A'}", "none"
    return "漏收", \
           (f"三路均未命中（标题最高相似 {best:.2f} → {bs or 'N/A'}；"
            f"DOI={doi or '无'} code={code or '无'}）"), "none"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--mech", default=None, help="机制词表 JSON（覆盖内置 DEFAULT_MECH）")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    mech = dict(DEFAULT_MECH)
    if a.mech:
        mech.update(json.load(open(a.mech, encoding="utf-8")))

    slugs, titles, dois = load_slugs_and_dois(a.root)
    print(f"站内：{len(slugs)} 篇文章 / {len(dois)} 个DOI / {len(titles)} 个标题可比对")

    items = load_candidates(a.files)
    print(f"候选条目：{len(items)} 条（来自 {len(a.files)} 个产出文件）")

    for it in items:
        st, basis, conf = judge(it, slugs, titles, dois, mech)
        it["status"], it["basis"], it["confidence"] = st, basis, conf

    cnt = Counter(i["status"] for i in items)
    out = a.out or os.path.join(a.root, "data/harvest-report.json")
    json.dump({
        "scanned_files": a.files,
        "site_articles": len(slugs),
        "site_dois": len(dois),
        "total": len(items),
        "summary": dict(cnt),
        "items": items,
    }, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print(f"判定结果：{dict(cnt)}")
    byc = Counter(i["confidence"] for i in items)
    print(f"置信度分布：{dict(byc)}（high=DOI 精确 / medium=机制词 / low=标题相似 / none=无法判定）")
    print(f"报告已写入 {out}")
    if cnt.get("漏收"):
        print("\n⚠️ 漏收条目必须人工复核后再写稿——三路判定各有已知误判模式，"
              "详见脚本头部「必要性与教训」。")


if __name__ == "__main__":
    main()