#!/usr/bin/env python3
"""为缺少「延伸阅读」块的文章页补块。

背景
----
站点有 12 篇文章用的是**旧模板**（`class="footer"`，无 `</main>`），
在后续 rebuild 中未被重新生成，因此没有「延伸阅读」块。
其余 368 篇都有，块内 3 条同主题最新文章链接。

策略
----
1. 只处理 data/articles.json 中的条目（跳过孤儿页与 index.html）
2. 锚点：`<div class="footer">` 首次出现处，在其前插入
3. 候选：同主题（topic 字段）最新 3 篇，排除自身；同主题不足则不限主题补齐到 3 条
4. 只使用 articles.json 已有条目 → 零编造

幂等：已有 related-block 的页面跳过；二次运行输出「改动 0」。
"""
import json
import re
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = 3

ANCHOR_RE = re.compile(r'([ \t]*)<div class="footer">')


def main():
    arts = json.load(open(ROOT / "data/articles.json", encoding="utf-8"))
    by_slug = {a["slug"]: a for a in arts}

    # 按主题分组，组内按日期倒序
    by_topic = {}
    for a in sorted(arts, key=lambda x: x.get("date", ""), reverse=True):
        by_topic.setdefault(a.get("topic", ""), []).append(a)

    news_dir = ROOT / "news"
    changed = 0
    filled = []
    skipped = []

    for f in sorted(news_dir.glob("*.html")):
        if f.name == "index.html":
            continue
        art = by_slug.get(f.name)
        if art is None:
            skipped.append(f.name)
            continue
        h = f.read_text(encoding="utf-8")
        if "related-block" in h:
            continue

        # 选候选：同主题最新 3 篇（排除自身）
        topic = art.get("topic", "")
        cands = [a for a in by_topic.get(topic, []) if a["slug"] != f.name]
        if len(cands) < TARGET:
            seen = {a["slug"] for a in cands} | {f.name}
            for a in sorted(arts, key=lambda x: x.get("date", ""), reverse=True):
                if a["slug"] not in seen:
                    cands.append(a)
                    seen.add(a["slug"])
                if len(cands) >= TARGET:
                    break
        cands = cands[:TARGET]

        items = "".join(
            f'<li><a href="/news/{escape(a["slug"])}">{escape(a["title"])}</a> '
            f'<span class="tag-date">{escape(a.get("date", ""))}</span></li>'
            for a in cands
        )
        block = (
            f'{ANCHOR_RE.search(h).group(1)}'
            f'<div class="related-block"><h3>延伸阅读</h3>'
            f'<ul class="related-list">{items}</ul></div>\n\n'
        )

        m = ANCHOR_RE.search(h)
        assert m, f"锚点未找到: {f.name}"
        h2 = h[: m.start()] + block + h[m.start():]
        f.write_text(h2, encoding="utf-8")
        changed += 1
        filled.append((f.name, topic, [a["slug"] for a in cands]))

    print(f"补块页面: {changed}")
    for name, topic, cands in filled:
        print(f"  {name[:58]:<58} [{topic}]")
        for c in cands:
            print(f"      → {c[:70]}")
    if skipped:
        print(f"跳过（孤儿页，不在 articles.json）: {len(skipped)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
