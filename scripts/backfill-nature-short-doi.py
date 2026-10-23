#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
backfill-nature-short-doi.py —— 一次性回填 Nature 简写式 DOI（2026-10-23）

背景
────
backfill-doi.py 的正则只认 `10.xxxx/` 全式 DOI。站内有 16 篇 July–September
文章正文只写了 Nature 简写式（`s43587-026-01176-1`，无 `10.1038/` 前缀），
正则取不到，articles.json 的 doi 字段为空，DOI 精确查重对这 16 篇失效。

安全处置
────────
简写式不能无脑回填——多主题轮播文也会引用他人的简写式 DOI
（如 Longevity-Pipeline-Commercialization 引用了一篇 2023 年 Nature 论文）。
本轮对 16 个候选逐个走 Crossref API 核验标题，14 个标题与站内文章主题
吻合才回填；2 个排除：
  - Longevity-Pipeline-Commercialization-Sep-Oct-2026.html
    Crossref 返回「 Modelling post-implantation human development to yolk sac 」
    （2023，背景引用，非本文主题）→ 不回填
  - Oral-Microbiome-Neisseria-flavescens-Geroprotective-NatureAging-2026.html
    Crossref 404（DOI 无法核验）→ 不回填

核验证据：crossref_nature_short.json（与本脚本同轮次留档）。
今后新文章由 harvest 从卡片带入全式 DOI，不依赖此补丁；
遗留缺口（无法自动区分单主题/多主题）记入运营待办清单。
"""
import json
import os
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "/workspace/repo"

# Crossref 2026-10-23 核验通过：标题与站内文章主题一致
VERIFIED = {
    "Contractile-Myografts-Systemic-AntiAging-Nature-Aging-2026.html": "10.1038/s43587-026-01190-3",
    "Exercise-Slows-Ovarian-Aging-Nature-Aging-2026.html": "10.1038/s43587-026-01176-1",
    "Spatial-Microglia-Senescence-Aging-Brain-Nature-Aging-2026.html": "10.1038/s43587-026-01167-2",
    "IL-11-Matrix-Stiffness-Ovarian-Aging-Nature-Aging-2026.html": "10.1038/s43587-026-01159-2",
    "Telomere-Damage-Signaling-Hematopoiesis-Immune-Restore-2026.html": "10.1038/s43587-026-01146-7",
    "Geromedicine-Trial-Hierarchical-Endpoints-Win-Statistics-2026.html": "10.1038/s43587-026-01158-3",
    "GLP1-Obesity-Sarcopenia-Nature-Review-2026.html": "10.1038/s41574-026-01254-9",
    "Lung-Fibroblasts-Drive-Inflammaging.html": "10.1038/s41577-026-01302-5",
    "Spaceflight-Accelerated-Aging-Model.html": "10.1038/s43587-026-01105-2",
    "Spatial-Atlas-Aging-Human-Breast.html": "10.1038/s43587-026-01104-3",
    "Epigenetic-Dysregulation-Aging-Therapeutic-Target.html": "10.1038/s41580-026-00958-0",
    "p38-MAPK-Potassium-Homeostasis-Lifespan.html": "10.1038/s41467-026-70641-7",
    "Killifish-Immune-Aging-Model.html": "10.1038/s43587-026-01086-2",
    "Btaf1-Hematopoietic-Stem-Cell-Aging.html": "10.1038/s41467-026-70787-4",
}


def main():
    path = os.path.join(ROOT, "data/articles.json")
    arts = json.load(open(path, encoding="utf-8"))
    by_slug = {a["slug"]: a for a in arts}
    n = 0
    for slug, doi in VERIFIED.items():
        a = by_slug.get(slug)
        if a is None:
            print(f"⚠️ slug 不存在: {slug}")
            continue
        if a.get("doi"):
            print(f"⚠️ 已有 DOI，跳过: {slug} -> {a['doi']}")
            continue
        a["doi"] = doi
        n += 1
    json.dump(arts, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"回填 {n} 篇 / 验证 {len(VERIFIED)} 篇")


if __name__ == "__main__":
    main()
