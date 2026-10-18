#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_medrxiv_retry.py —— medRxiv 全文补抓（带退避重试）

背景（2026-10-19 凌晨实测三批）：
  - 20s 间隔：12/21 成功；30s 间隔：6/15 成功。429 是 Cloudflare 突发限流，
    呈「连续成功 3-4 条 → 429 2-3 条 → 恢复」的锯齿模式，等一等就能过。
  - 所以对失败条目不要放弃：冷却后重试，大概率成功。

策略：
  - 每条最多 3 次尝试，退避 30s / 60s / 120s（§9.8.3 纪律）
  - 跳过已有 .xml 的 DOI（以磁盘为准，不信汇总——汇总会被逐批覆盖）
  - 串行，条间 sleep 30s
  - 汇总写 _retry_summary.json，不碰 _fetch_summary.json

用法：python3 scripts/fetch_medrxiv_retry.py <hits.json> [--limit N]
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
BACKOFF = [30, 60, 120]


def safe_name(doi: str) -> str:
    return re.sub(r"[^0-9A-Za-z._-]+", "_", doi)


def fetch_jats(url: str, timeout: int = 90):
    try:
        p = subprocess.run(
            ["curl", "-sL", "-o", "-", "-w",
             "\n%{http_code}\n%{url_effective}", "-A", UA, "--max-time", str(timeout), url],
            capture_output=True, timeout=timeout + 15)
        out = p.stdout
        m = re.search(rb"\n(\d{3})\n(\S+)\s*$", out)
        if not m:
            return 0, b"", url
        return int(m.group(1)), out[: m.start()], m.group(2).decode("utf-8", "replace")
    except Exception:
        return 0, b"", url


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit("用法：fetch_medrxiv_retry.py <hits.json> [--limit N]")
    limit = int(args[args.index("--limit") + 1]) if "--limit" in args else 0

    hits = json.load(open(args[0], encoding="utf-8"))
    med = [h for h in hits if h.get("_server") == "medRxiv"]
    med.sort(key=lambda x: (not x["_core"], -x["_nq"]))

    todo = []
    for h in med:
        name = safe_name(h["doi"])
        if (OUTDIR / f"{name}.xml").exists():
            continue  # 已有，跳过
        if not h.get("jatsxml"):
            continue
        todo.append(h)
    if limit:  # limit 必须在跳过已有之后再截断，否则只看排序后前 N 条
        todo = todo[:limit]

    print(f"待补抓 {len(todo)} 条（已自动跳过有 .xml 的）")
    results = []
    for i, h in enumerate(todo, 1):
        doi, url = h["doi"], h["jatsxml"]
        code, body, final = 0, b"", url
        for attempt, wait in enumerate([0] + BACKOFF, 1):
            if wait:
                print(f"     {doi} 第{attempt}次退避 {wait}s …")
                time.sleep(wait)
            code, body, final = fetch_jats(url)
            if code == 200 and body.lstrip().startswith(b"<") and b"<article" in body[:2000]:
                break
        ok = code == 200 and body.lstrip().startswith(b"<") and b"<article" in body[:2000]
        if ok:
            name = safe_name(doi)
            (OUTDIR / f"{name}.xml").write_bytes(body)
            (OUTDIR / f"{name}.meta.json").write_text(json.dumps({
                "doi": doi, "title": h.get("title", ""), "date": h.get("date"),
                "category": h.get("category"), "server": "medRxiv",
                "abstract": h.get("abstract", ""),
                "author_corresponding": h.get("author_corresponding"),
                "author_corresponding_institution": h.get("author_corresponding_institution"),
                "source_url": final, "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "n_quant": h.get("_nq"), "core": h.get("_core"), "retry": True,
            }, ensure_ascii=False, indent=1), encoding="utf-8")
        results.append({"doi": doi, "http": code, "bytes": len(body),
                        "status": "ok" if ok else f"fail_http_{code}"})
        print(f"{i:3d}. [{'OK ' if ok else f'失败({code})'}] {len(body):>8d}B {doi}")
        if i < len(todo):
            time.sleep(30)

    out = OUTDIR / "_retry_summary.json"
    out.write_text(json.dumps({
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "attempted": len(todo), "ok": sum(1 for r in results if r["status"] == "ok"),
        "results": results,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    ok_n = sum(1 for r in results if r["status"] == "ok")
    print(f"\n补抓完成：{ok_n}/{len(todo)} 成功，汇总 {out}")


if __name__ == "__main__":
    main()
