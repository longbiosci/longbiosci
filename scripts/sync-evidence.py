#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sync-evidence.py —— 把 news/*.html 的证据分级回写 data/articles.json

用法：python3 scripts/sync-evidence.py .            # 预览差异（不写盘）
      python3 scripts/sync-evidence.py . --write    # 实际写回

为什么需要这一层
────────────────
build-index.py 的 main() 里写着「1) 现有登记（权威基线）」：已登记 slug 的原记录
被**整体保留**，HTML 侧的任何后续编辑都不会回写 articles.json。

这造成一个反复复现的坑：在文章页上更正证据分级后，页面显示是对的，
articles.json 仍是旧值；而 articles.json 恰恰是首页、话题页、搜索索引的数据源，
于是站内出现「同一篇文章两个分级」。

实例（本脚本的直接动因）：
  - 2026-10-17 把 PROMETHEUS 方案从 C 更正为 A（同行评议人体研究方案，已注册
    NCT07451496），HTML 与 articles.json 当时都已改对；
  - 同日合并远端两个新稿提交后，远端带回来的 articles.json 快照仍是 C，
    增量构建「保留原记录」→ 分级回退到 C，而 HTML 是 A，站内自相矛盾。
  也就是说：**只要远端再带回一个旧快照，这个矛盾就会复发**，靠一次性补丁挡不住。

为什么只同步 evidence、不同步 desc
────────────────────────────────
已知站内约 57 篇文章的 desc 只存在于 articles.json 侧（HTML 里没有对应的
meta description，或两者早已分叉）。若一并从 HTML 覆盖 desc，会**静默丢数据**。
而 evidence 的判据是页面上的 notice-box 分级标记，HTML 侧必有，可以安全回写。

幂等：可反复运行；无差异时不写盘。
"""

import json
import os
import re
import sys

# 与 scripts/build-index.py 保持完全一致的判据与优先级，避免两处口径分叉。
RE_DATA_TIER = re.compile(r'data-tier="([A-D])"')
RE_TIER_SPAN = re.compile(r'<span class="tier tier-([a-d])">')


def tier_of(html):
    """按 build-index.py 相同顺序取分级：data-tier 优先，其次 notice-box 的 tier span。"""
    m = RE_DATA_TIER.search(html)
    if not m:
        m = RE_TIER_SPAN.search(html)
    return m.group(1).upper() if m else ""


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    write = "--write" in sys.argv

    index_path = os.path.join(root, "data", "articles.json")
    with open(index_path, encoding="utf-8") as f:
        records = json.load(f)

    news_dir = os.path.join(root, "news")
    changed, missing, no_tier = [], [], []

    for rec in records:
        slug = rec.get("slug", "")
        path = os.path.join(news_dir, slug)
        if not os.path.isfile(path):
            missing.append(slug)
            continue
        with open(path, encoding="utf-8") as f:
            html = f.read()
        tier = tier_of(html)
        if not tier:
            no_tier.append(slug)
            continue
        if rec.get("evidence") != tier:
            changed.append((slug, rec.get("evidence", ""), tier))
            if write:
                rec["evidence"] = tier

    print(f"articles.json：{len(records)} 条")
    print(f"页面缺失：{len(missing)} 条 · 页面无分级标记：{len(no_tier)} 条")
    print(f"分级不一致：{len(changed)} 条")
    for slug, old, new in changed:
        print(f"  {old or '(空)'} → {new}   {slug}")

    if not changed:
        print("\n✅ 无差异，无需同步")
        return 0

    if not write:
        print("\n（预览模式。加 --write 才会写回 articles.json）")
        return 0

    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"\n✅ 已同步 {len(changed)} 条 evidence → {index_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
