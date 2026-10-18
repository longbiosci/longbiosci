#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_medrxiv_fulltext.py —— medRxiv JATS 全文抓取（降级通道，2026-10-19 实测打通）

实测结论（本机出口，2026-10-19 凌晨）：
  - medRxiv 内容页 / JATS XML **可达**（真实 DOI 200；假 DOI 会吃 Cloudflare 403，别用假 DOI 探测）
  - API 给的 jatsxml 链接 `.../content/early/<date>/<doi>.source.xml` 会 **301** 到
    `.../content/medrxiv/early/<date>/<doi>.source.xml`，必须 `-L` 跟随
  - bioRxiv 同格式链接 **403**（整站 IP 封禁，与内容页一致）→ 本脚本只处理 medRxiv

限速纪律（源自 9.8.2 实测：medRxiv 是 Cloudflare 速率限制 429，会恢复但别招惹）：
  - 串行，条间 sleep 默认 20s（--sleep 可调，别低于 15）
  - 遇 429/403 不做重试狂欢：记录状态、跳过，末尾汇总人工决定

用法：
  python3 scripts/fetch_medrxiv_fulltext.py <hits.json> [--limit N] [--sleep S] [--outdir DIR]
"""
import json
import re
import subprocess
import sys
import time
from pathlib import Path

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
OUTDIR = Path("/workspace/data/fulltext/medrxiv")


def safe_name(doi: str) -> str:
    return re.sub(r"[^0-9A-Za-z._-]+", "_", doi)


def fetch_jats(url: str, timeout: int = 90):
    """返回 (http_code, bytes, final_url)。用 curl -L 跟随 301。"""
    try:
        p = subprocess.run(
            ["curl", "-sL", "-o", "/dev/null" if False else "-", "-w",
             "\n%{http_code}\n%{url_effective}", "-A", UA, "--max-time", str(timeout), url],
            capture_output=True, timeout=timeout + 15)
        out = p.stdout
        # 结构：body...\n<code>\n<url>
        m = re.search(rb"\n(\d{3})\n(\S+)\s*$", out)
        if not m:
            return 0, b"", url
        code = int(m.group(1))
        final = m.group(2).decode("utf-8", "replace")
        body = out[: m.start()]
        return code, body, final
    except Exception:
        return 0, b"", url


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit("用法：fetch_medrxiv_fulltext.py <hits.json> [--limit N] [--sleep S]")
    src = args[0]
    limit, sleep_s = 0, 20.0
    if "--limit" in args:
        limit = int(args[args.index("--limit") + 1])
    if "--sleep" in args:
        sleep_s = float(args[args.index("--sleep") + 1])
    skip_existing = "--force" not in args  # 默认跳过已有 .xml，避免每日重跑重复下载惹 429

    hits = json.load(open(src, encoding="utf-8"))
    med = [h for h in hits if h.get("_server") == "medRxiv"]
    # 与 preprint_daily 相同排序：核心优先、定量多优先
    med.sort(key=lambda x: (not x["_core"], -x["_nq"]))
    if limit:
        med = med[:limit]

    OUTDIR.mkdir(parents=True, exist_ok=True)
    if skip_existing:
        before = len(med)
        med = [h for h in med if not (OUTDIR / f"{safe_name(h['doi'])}.xml").exists()]
        skipped = before - len(med)
        if skipped:
            print(f"跳过已抓 {skipped} 条（--force 可强制重下）")
    print(f"medRxiv 待抓 {len(med)} 条，条间 sleep {sleep_s}s，输出 {OUTDIR}")

    results = []
    for i, h in enumerate(med, 1):
        doi = h["doi"]
        url = h.get("jatsxml") or ""
        name = safe_name(doi)
        if not url:
            results.append({"doi": doi, "status": "no_jatsxml", "bytes": 0})
            print(f"{i:3d}. [无jatsxml链接] {doi}")
            continue
        code, body, final = fetch_jats(url)
        ok = code == 200 and body.lstrip().startswith(b"<") and b"<article" in body[:2000]
        rec = {"doi": doi, "title": h.get("title", ""), "http": code,
               "bytes": len(body), "final_url": final,
               "status": "ok" if ok else f"fail_http_{code}"}
        if ok:
            (OUTDIR / f"{name}.xml").write_bytes(body)
            (OUTDIR / f"{name}.meta.json").write_text(json.dumps({
                "doi": doi, "title": h.get("title", ""), "date": h.get("date"),
                "category": h.get("category"), "server": "medRxiv",
                "abstract": h.get("abstract", ""),
                "author_corresponding": h.get("author_corresponding"),
                "author_corresponding_institution": h.get("author_corresponding_institution"),
                "source_url": final, "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "n_quant": h.get("_nq"), "core": h.get("_core"),
            }, ensure_ascii=False, indent=1), encoding="utf-8")
        results.append(rec)
        mark = "OK " if ok else f"失败({code})"
        print(f"{i:3d}. [{mark}] {len(body):>8d}B {doi}")
        if i < len(med):
            time.sleep(sleep_s)

    summary_path = OUTDIR / "_fetch_summary.json"
    summary_path.write_text(json.dumps({
        "source": src, "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "total": len(med), "ok": sum(1 for r in results if r["status"] == "ok"),
        "results": results,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    ok_n = sum(1 for r in results if r["status"] == "ok")
    print(f"\n完成：{ok_n}/{len(med)} 成功，汇总 {summary_path}")


if __name__ == "__main__":
    main()
