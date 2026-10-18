#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
jats_to_text.py —— 扫描 data/fulltext/medrxiv/*.xml，抽正文、判完整性、产 .full.txt

为什么需要它（2026-10-19 实测教训）：
HTTP 200 + 字节数 ≠ 全文到手。实测有稿 source.xml 的 <body> 里只有一个
supplementary-material 引用，正文一字没有（如 10.64898/2026.10.14.26364960，
17 KB XML 抽出 22 字符）。所以判据是**正文文本长度**，不是 HTTP 状态。

完整性判据（保守）：
  full    : 正文 ≥ 4000 字符（可支撑深度解读）
  partial : 500 ≤ 正文 < 4000（可能是短通讯/特例，人工过目）
  empty   : 正文 < 500（源残缺，只能按摘要卡片处理，标 D 级）

用法：python3 scripts/jats_to_text.py [目录]
"""
import json
import re
import sys
from pathlib import Path

DEFAULT_DIR = Path("/workspace/data/fulltext/medrxiv")
FULL_MIN = 4000
PARTIAL_MIN = 500


def extract_body_text(xml_bytes: bytes) -> str:
    t = xml_bytes.decode("utf-8", "replace")
    m = re.search(r"<body>(.*?)</body>", t, re.S)
    if m:
        t = m.group(1)
    # 标题层级化
    t = re.sub(r"<title[^>]*>(.*?)</title>", r"\n\n## \1\n", t, flags=re.S)
    t = re.sub(r"<sec[^>]*>", "\n", t)
    t = re.sub(r"</p>", "\n", t)
    t = re.sub(r"<[^>]+>", "", t)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def main():
    d = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DIR
    rows = []
    for xml in sorted(d.glob("*.xml")):
        if xml.name.startswith("_"):
            continue
        name = xml.stem
        txt = extract_body_text(xml.read_bytes())
        n = len(txt)
        src = "jats_xml"
        # 内容页补救优先：若存在 .page.txt 且比 XML 正文长，以补救稿为准
        # （jats_to_text 曾把 5 篇 html_page 补救稿错误打回 empty——它不知道 page.txt 存在）
        page_txt_path = d / f"{name}.page.txt"
        if page_txt_path.exists():
            page_txt = page_txt_path.read_text(encoding="utf-8")
            if len(page_txt) > n:
                txt, n, src = page_txt, len(page_txt), "html_page"
        grade = "full" if n >= FULL_MIN else ("partial" if n >= PARTIAL_MIN else "empty")
        if src == "html_page":
            (d / f"{name}.page.txt").write_text(txt, encoding="utf-8")
        else:
            (d / f"{name}.full.txt").write_text(txt, encoding="utf-8")
        meta_path = d / f"{name}.meta.json"
        if meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            meta["fulltext_chars"] = n
            meta["fulltext_grade"] = grade
            if src == "html_page":
                meta["fulltext_source"] = "html_page"
            meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
        rows.append((name, n, grade))
    counts = {}
    for _, n, g in rows:
        counts[g] = counts.get(g, 0) + 1
    print(f"扫描 {d}：{len(rows)} 篇")
    for name, n, g in rows:
        print(f"  [{g:7s}] {n:>7d} 字符  {name}")
    print("汇总：", counts)


if __name__ == "__main__":
    main()
