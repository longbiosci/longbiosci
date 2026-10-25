#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_articles_intake_2026-10-26b.py —— 05:30 班第 14 轮 · 批次 b

消化对象
────────
《午刊补丁包_2026-10-25_待推送.tar.gz》（任务 13508579 午刊生产班，
元层 dutntPjmuBOP）—— 12 篇成品文章页。

查重（规则④）：12 篇 slug 全部不在站内；但对 12 条的 DOI 逐条
`grep news/*.html` 正文全文比对后，**3 条同一 DOI 已有本站成稿**：

    10.1111/acel.70783      → Lowering-Insulin-Signalling-Development-Longevity-2026.html
    10.1126/sciadv.aef3338  → NAD-Metabolic-Restoration-Lung-GVHD-2026.html
    10.1126/sciadv.aed4541  → Death-Receptors-IAP-Antagonist-Senolytics-2026.html

按规则④「重复条目跳过并计数」，这 3 篇不上站、**净新增 9 篇**。

⚠️ 为什么不用包内的 articles.json 覆盖
─────────────────────────────────
包内 `articles.json` 是 **601 + 12 = 613** 条口径，而本站经本轮之前的
消化已达 772 条。若直接覆盖，会把本站在库的多于cule 文章**整批抹掉**。
故：只取 `news/*.html`，`data/articles.json` 由管线环节 1
（build-index.py）从 HTML 重建，不用包内的。

本批修复的两处上游缺陷（周报 2026-W43 风险 #7 已点名其一）
──────────────────────────────────────────────────
1. `data-lb-event-date="1"` **占位值**：12 篇的机器可读发生日期属性全为
   字面量 "1"，任何按它排序/算 lastmod 的逻辑都会塌陷。改为真实
   发生日期 `YYYY-MM-DD`（取 `article:published_time` 之外的明确标注来源：
   页脚 notice-box 的「情报发生」）。
2. **缺规则③时间标签**：原页只在页脚写了「情报发生 X · 本站发布 Y」，
   首段没有 `数据日期 YYYY-MM-DD · 生成时间 YYYY-MM-DD HH:MM`。
   在正文 `<div class="article-content">` 首行注入该标签。
   生成时间取网盘交付时间戳（2026-10-25 13:59，可溯源），
   **不用当前巡检时间冒替上游生成时点**。
"""
import json
import os
import re
import shutil
import tarfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = os.path.join(ROOT, ".intake-tmp/20261026")
SRC = os.path.join(TMP, "midday/午刊_2026-10-25/news")

# 规则④：同一 DOI 站内已有成稿 → 跳过并计数，不重复上站
SKIP_DOI = {
    "10.1111/acel.70783": "Lowering-Insulin-Signalling-Development-Longevity-2026.html",
    "10.1126/sciadv.aef3338": "NAD-Metabolic-Restoration-Lung-GVHD-2026.html",
    "10.1126/sciadv.aef4541": "Death-Receptors-IAP-Antagonist-Senolytics-2026.html",
    "10.1126/sciadv.aed4541": "Death-Receptors-IAP-Antagonist-Senolytics-2026.html",
}

INJECT = ("<p><strong>数据日期 {dd}</strong>（情报发生） · "
          "<strong>生成时间 {gt}</strong>　｜　本篇由午刊生产班（任务 13508579）"
          "于 2026-10-25 交付，05:30 巡检（任务 12409847）于 2026-10-26 收录上站。</p>\n")


def find_doi(html):
    dois = set(re.findall(r'doi\.org/(10\.\d{4,9}/[^"\'<>\s]+)', html))
    return dois


def main():
    if not os.path.isdir(SRC):
        tar = os.path.join(TMP, "midday_patch_2026-10-25.tar.gz")
        with tarfile.open(tar) as t:
            t.extractall(os.path.join(TMP, "midday"))

    newsdir = os.path.join(ROOT, "news")
    copied, skipped, fixed_event = [], [], 0

    for fn in sorted(os.listdir(SRC)):
        if not fn.endswith(".html"):
            continue
        raw = open(os.path.join(SRC, fn), encoding="utf-8").read()
        doi_hit = [d for d in find_doi(raw) if d in SKIP_DOI]
        if doi_hit:
            skipped.append((fn, doi_hit[0], SKIP_DOI[doi_hit[0]]))
            continue
        dst = os.path.join(newsdir, fn)
        if os.path.exists(dst):
            skipped.append((fn, "-", "slug 已存在"))
            continue

        # ① 取真实发生日期（页脚 notice-box 的「情报发生 YYYY-MM-DD」）
        m = re.search(r'情报发生\s*([\d]{4}-[\d]{2}-[\d]{2})', raw)
        dd = m.group(1) if m else re.search(
            r'article:published_time"\s+content="([\d]{4}-[\d]{2}-[\d]{2})', raw).group(1)
        gt = "2026-10-25 13:59"      # 网盘交付时间戳 1792907950 → 2026-10-25 13:59:10

        # ② 修 data-lb-event-date="1" 占位值
        new = raw.replace('data-lb-event-date="1"', f'data-lb-event-date="{dd}"')
        if new != raw:
            fixed_event += 1

        # ③ 首段注入规则③时间标签
        marker = '<div class="article-content">'
        if marker in new:
            new = new.replace(marker, marker + "\n" + INJECT.format(dd=dd, gt=gt), 1)

        open(dst, "w", encoding="utf-8").write(new)
        copied.append((fn, dd))

    print(f"本批上站 {len(copied)} 篇 · 跳过 {len(skipped)} 条 · 修 event-date 占位值 {fixed_event} 处")
    for f, d in copied:
        print(f"  ✓ {f}  情报发生 {d}")
    for f, d, why in skipped:
        print(f"  ⨯ 跳过 {f}：{d} → 站内已有 {why}")


if __name__ == "__main__":
    main()
