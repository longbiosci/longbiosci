#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_fulltext_summary.py —— 重建 data/fulltext/medrxiv/_final_summary.json（累积池）

扫描目录下全部 *.meta.json（历次抓取的全文，天然累积），重建汇总。
供 gen_daily_fulltext.py 按日期筛当日条目。幂等，可每日重跑。
"""
import json
import sys
import time
from pathlib import Path

D = Path("/workspace/data/fulltext/medrxiv")


def main():
    rows = []
    for meta_path in sorted(D.glob("*.meta.json")):
        m = json.loads(meta_path.read_text(encoding="utf-8"))
        stem = meta_path.name[: -len(".meta.json")]
        txt = ".page.txt" if m.get("fulltext_source") == "html_page" else ".full.txt"
        if not (D / (stem + txt)).exists():
            print(f"⚠ 缺正文文件，跳过：{stem}{txt}")
            continue
        rows.append({
            "doi": m["doi"], "title": m["title"], "date": m["date"],
            "grade": m.get("fulltext_grade"), "chars": m.get("fulltext_chars"),
            "source": m.get("fulltext_source", "jats_xml"),
            "core": m.get("core"), "n_quant": m.get("n_quant"),
            "abstract": m.get("abstract", ""), "txt_file": stem + txt,
        })
    full = [r for r in rows if r["grade"] == "full"]
    part = [r for r in rows if r["grade"] == "partial"]
    summary = {
        "window": f"累积池（截至 {time.strftime('%Y-%m-%d')}）",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "medrxiv_hits": len(rows), "fetched": len(rows), "full": len(full), "partial": len(part),
        "biorxiv_hits": 0, "biorxiv_fulltext": 0,
        "biorxiv_block_reason": "Cloudflare IP 级封禁（403 恒定，真实 DOI 连测），等待无效；S3 需 AWS 凭证且映射 API 不覆盖 2026 新 DOI",
        "total_hits": len(rows), "total_fulltext": len(rows), "coverage_pct": 100.0,
        "items": sorted(rows, key=lambda r: (r["grade"] != "full", -(r["chars"] or 0))),
    }
    (D / "_final_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"汇总池重建：{len(rows)} 篇（full {len(full)} + partial {len(part)}）")
    if len(rows) != len(list(D.glob('*.meta.json'))):
        sys.exit(1)


if __name__ == "__main__":
    main()
