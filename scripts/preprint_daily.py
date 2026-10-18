#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
preprint_daily.py —— 《预印本速递》生成器（每日）

数据源：bioRxiv / medRxiv details API v2
  https://api.biorxiv.org/details/biorxiv/<start>/<end>/<cursor>
  https://api.medrxiv.org/details/medrxiv/<start>/<end>/<cursor>

两条已实测的硬前提（写在这里是为了不被后人重复踩）：

A. **必须翻页**。API 每页固定 30 条，`messages[0].total` 才是真实总量。
   只看第一页会得到恒定 30 条，进而得出「几乎无衰老相关」的错误结论——
   本脚本作者 2026-10-18 就踩过，差点据此否掉整个每日速递。

B. **全文拿不到，别试**。每条带 `jatsxml`，但直连一律 Cloudflare 403
   （带浏览器 UA 同样 403），Europe PMC 对预印本（src=PPR）无 fullTextXML（500）。
   所以只把链接原样记录供读者打开，结构化数据只用 `abstract`。

用法：
  python3 scripts/preprint_daily.py <YYYY-MM-DD>          # 抓该日
  python3 scripts/preprint_daily.py <start> <end>          # 抓区间
输出：/tmp/预印本速递_<date>.md（+ 结构化 JSON 便于下游查重）
"""
import json
import re
import sys
import time
import urllib.request

API = {
    "bioRxiv": "https://api.biorxiv.org/details/biorxiv",
    "medRxiv": "https://api.medrxiv.org/details/medrxiv",
}

# 宽召回（宁可多召回，靠人工/模型判读收紧）
KW = re.compile(
    r"\b(aging|ageing|senescen|longevity|lifespan|healthspan|geroscience|progeria|"
    r"senolytic|epigenetic clock|inflammaging|frailty|sarcopenia|heterochronic|"
    r"geroprotector|NAD\+|rapamycin|mTOR|telomere|partial reprogramming|Yamanaka|"
    r"OSK|SASP|p16INK4a|p21|sirtuin|caloric restriction|dietary restriction|"
    r"autophagy|mitochondri|stem cell|Alzheimer|Parkinson|dementia)\b", re.I)

# 核心衰老词（用于分档：标题或摘要命中的优先判为主榜候选）
CORE = re.compile(
    r"\b(aging|ageing|senescen|longevity|lifespan|healthspan|geroscience|progeria|"
    r"senolytic|epigenetic clock|inflammaging|frailty|sarcopenia|heterochronic|"
    r"geroprotector)\b", re.I)

# 定量信号（用于判断「摘要里有没有可引用的数字」——下游成篇的分拣依据）
NUM = re.compile(
    r"(?<![\w.])(\d+(?:\.\d+)?\s*(?:%|fold|-fold|mmHg|mg/kg|nM|µM|μM|days|weeks|months|years))"
    r"|(?:[nN]\s*=\s*\d+)|(?:p\s*[<=]\s*0?\.\d+)|(?:[×x]\s*10\^?-?\d+)|(?:\b\d{2,}\b)")


def get(url, tries=3):
    last = None
    for _ in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "longbiosci-intake/1.0"})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read())
        except Exception as e:
            last = e
            time.sleep(2)
    raise last


def fetch_all(server, start, end):
    """翻完所有页，按 DOI 去重。"""
    base = API[server]
    seen = {}
    cursor = 0
    total = None
    while True:
        j = get(f"{base}/{start}/{end}/{cursor}")
        coll = j.get("collection", [])
        if total is None:
            total = (j.get("messages") or [{}])[0].get("total")
        if not coll:
            break
        for x in coll:
            seen[x["doi"]] = x
        if len(coll) < 30:
            break
        cursor += 30
        if cursor > 3000:
            break
        time.sleep(0.3)
    return seen, total


def quantify(x):
    ab = x.get("abstract", "") or ""
    return len(NUM.findall(ab))


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit("用法：preprint_daily.py <YYYY-MM-DD> 或 <start> <end>")
    start = args[0]
    end = args[1] if len(args) > 1 else args[0]

    all_hits = []
    stats = {}
    for server in ("bioRxiv", "medRxiv"):
        items, total = fetch_all(server, start, end)
        hits = [x for x in items.values() if KW.search((x.get("title", "") + " " + (x.get("abstract") or "")))]
        for h in hits:
            h["_server"] = server
            h["_nq"] = quantify(h)
            h["_core"] = bool(CORE.search(h.get("title", "") + " " + (h.get("abstract") or "")))
        stats[server] = {"total": total, "fetched": len(items), "hits": len(hits)}
        all_hits.extend(hits)

    # 排序：核心词命中优先，其次定量多
    all_hits.sort(key=lambda x: (not x["_core"], -x["_nq"]))

    print(f"时间窗 {start} ~ {end}")
    for s, v in stats.items():
        print(f"  {s}: total={v['total']} 实际取到={v['fetched']} 宽口径命中={v['hits']}")
    print(f"合计命中 {len(all_hits)} 条（以下按 核心词优先 / 定量多优先 排序）\n")

    for i, x in enumerate(all_hits, 1):
        flag = "核心" if x["_core"] else "  宽"
        print(f"{i:3d}. [{flag}] n={x['_nq']:3d} {x.get('title','')[:88]}")
        print(f"     {x['_server']} | {x.get('category')} | {x.get('date')} | {x.get('doi')}")
        print(f"     corr: {x.get('author_corresponding','未列')} @ {x.get('author_corresponding_institution','未列')}")
        print(f"     jatsxml: {x.get('jatsxml')}")
        ab = (x.get("abstract") or "").replace("\n", " ")
        print(f"     abs: {ab[:220]}…")
        print()

    out = f"/tmp/preprint_hits_{start}_{end}.json"
    json.dump(all_hits, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"结构化结果已写 {out}")


if __name__ == "__main__":
    main()
