#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_cards.py —— 把「#### 编号 · 中文标题 + 字段表」结构的深度卡片抽成可查重的形态

存在理由
────────
文献层产出的卡片结构会随期次变化：
  · 2026-10-09 期用 `### C01 · 中文标题` + 字段表（含 DOI）
  · 2026-10-16 期改用 `#### N01 · 中文标题` + 字段表，
    且「总览速览」表格里**没有 DOI 列**（只有 # / 卷期 / 标题 / 结论 / 全文）。

harvest.py 的 parse_section_items 只认 `^###`，遇到 `####` 一张卡都解析不到；
总览表虽然能被 parse_md_tables 扫到，但 **67 条全部没有 DOI** ——
于是四路查重的头一路（DOI 精确匹配，唯一的高置信路径）整体失效，
判定结果会退化成一堆 confidence=none 的「需人工核对」，
真漏收与假漏收混在一起，人工复核成本回到原点。

本脚本把两种结构统一成 harvest 能吃的形式，不改变任何事实字段：
  1. cards.json —— {code, title_cn, title_en, doi, journal, pmid, 结论…}
  2. cards.md   —— `### <code> · <英文原标题>` + 原字段表（供 harvest 解析）

用法
────
  python3 scripts/extract_cards.py <产出.md> [--outdir .intake/raw]
"""
import argparse
import json
import os
import re

HEAD = re.compile(r"^####\s+([A-Za-z]{0,4}\d{1,3})\s*·\s*(.+)$", re.M)
FIELD = re.compile(r"^\|\s*([^|]{2,12}?)\s*\|\s*([^|]*?)\s*\|$", re.M)


def clean(s):
    return re.sub(r"\*\*|\*|`", "", s or "").strip()


def parse(path):
    text = open(path, encoding="utf-8", errors="ignore").read()
    heads = list(HEAD.finditer(text))
    cards = []
    for i, m in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        block = text[m.end():end]
        fields = {k.strip(): clean(v) for k, v in FIELD.findall(block)}
        cards.append({
            "code": m.group(1).strip(),
            "title_cn": clean(m.group(2)),
            "title_en": clean(fields.get("标题", "")),
            "doi": fields.get("DOI", ""),
            "journal": fields.get("期刊卷期", ""),
            "pmid": fields.get("PMID", ""),
            "team": fields.get("团队", ""),
            "fields": fields,
            "body": block.strip(),
        })
    return cards


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--outdir", default=None)
    ap.add_argument("--prefix", default=None)
    a = ap.parse_args()

    cards = parse(a.src)
    outdir = a.outdir or os.path.dirname(os.path.abspath(a.src))
    prefix = a.prefix or os.path.splitext(os.path.basename(a.src))[0]
    os.makedirs(outdir, exist_ok=True)

    jp = os.path.join(outdir, prefix + ".cards.json")
    json.dump(cards, open(jp, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    # harvest 形态：`### code · 英文原标题` + 原字段表
    lines = []
    for c in cards:
        lines.append(f"\n### {c['code']} · {c['title_en'] or c['title_cn']}\n")
        lines.append("| 字段 | 内容 |\n|---|---|")
        for k, v in c["fields"].items():
            lines.append(f"| {k} | {v} |")
        lines.append("")
    mp = os.path.join(outdir, prefix + ".cards.md")
    open(mp, "w", encoding="utf-8").write("\n".join(lines))

    nodoi = [c["code"] for c in cards if not c["doi"]]
    print(f"抽出 {len(cards)} 张卡片 → {jp} / {mp}")
    if nodoi:
        print(f"  ⚠️ 无 DOI 的卡片 {len(nodoi)} 张：{nodoi[:20]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
