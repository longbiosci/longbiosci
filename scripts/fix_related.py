#!/usr/bin/env python3
"""站内死链修复器：把指向已删除文章的 /news/<slug> 链接改指到保留版本。

背景
----
本站对同一研究的重复报道做过两轮清理（398→377），删除文章的页面已 404，
但文章页底部的「延伸阅读」块与概念页（senolytic/stemcell/melatonin 等）
是静态 HTML，链接不会自动跟着删——会留下大量死链。

修复策略（按优先级）
--------------------
1. 查 data/redirects.json：已删 slug -> 保留 slug（人工确认过的映射，最可信）
2. 若映射结果已在当前列表中出现 -> 去重后从同主题最新文章里补位
3. 若无映射 -> 移除该条目，并在输出里报告

设计原则：**不改写正文、不发明内容**，只做链接层面的重定向与补位。
补位只使用 data/articles.json 中已存在的条目，保证零编造。

用法：python3 scripts/fix_related.py [--dry-run]
退出码：0 = 无残留死链；1 = 仍有残留（需补 data/redirects.json）
"""
import json
import re
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DRY = "--dry-run" in sys.argv
TARGET_RELATED = 3  # 延伸阅读保留条数

REL_BLOCK_RE = re.compile(
    r'<div class="related-block">\s*<h3>延伸阅读</h3>\s*'
    r'<ul class="related-list">(.*?)</ul>\s*</div>', re.S)
REL_ITEM_RE = re.compile(
    r'<li><a href="/news/([^"]+)">(.*?)</a>\s*<span class="tag-date">([^<]*)</span></li>')
ABS_LINK_RE = re.compile(r'href="https://longbiosci\.com/news/([^"]+)"')
# 注意：必须同时覆盖「相对 /news/x.html」与「绝对 https://longbiosci.com/news/x.html」
# 两种写法。2026-10-15 巡检发现：正文「与已有研究的关系」「相关阅读」小节用的是绝对
# 写法，而本脚本原先只认相对写法，导致 2 条正文死链躲过了「死链复扫 0」的自检。
NEWS_LINK_RE = re.compile(r'href="(?:https://longbiosci\.com)?/news/([^"]+)"')


def load():
    arts = json.loads((ROOT / "data" / "articles.json").read_text(encoding="utf-8"))
    arts.sort(key=lambda a: a.get("date", ""), reverse=True)
    redir_path = ROOT / "data" / "redirects.json"
    raw = json.loads(redir_path.read_text(encoding="utf-8")) if redir_path.exists() else {}
    redirects = {k: v for k, v in raw.items() if not k.startswith("_")}
    valid = {a["slug"] for a in arts}
    by_slug = {a["slug"]: a for a in arts}
    by_topic = {}
    for a in arts:
        by_topic.setdefault(a.get("topic", ""), []).append(a)
    return arts, redirects, valid, by_slug, by_topic


def split_feed_items(html: str):
    """按 div 嵌套深度切出每个 <div class="feed-item">…</div> 区块。

    feed-item 内部含多层 div，正则无法安全匹配，这里做深度计数。
    """
    out, i = [], 0
    tag = '<div class="feed-item">'
    while True:
        s = html.find(tag, i)
        if s < 0:
            break
        depth, j = 1, s + len(tag)
        while depth and j < len(html):
            nd = html.find("<div", j)
            cd = html.find("</div>", j)
            if cd < 0:
                break
            if 0 <= nd < cd:
                depth += 1
                j = nd + 4
            else:
                depth -= 1
                j = cd + 6
        out.append((s, j, html[s:j]))
        i = j
    return out


def drop_dead_feed_items(html, valid, redirects, stats, unmapped, rel):
    """概念页/列表页里，指向已删文章且无重定向映射的条目整块剔除。"""
    pieces, last, changed = [], 0, False
    for s, e, block in split_feed_items(html):
        dead = [slug for slug in set(NEWS_LINK_RE.findall(block))
                if slug not in valid and redirects.get(slug) not in valid]
        if dead:
            changed = True
            stats["dropped"] += len(dead)
            for slug in dead:
                unmapped.setdefault(slug, []).append(rel)
            pieces.append(html[last:s])
            last = e
    if not changed:
        return html
    pieces.append(html[last:])
    return "".join(pieces)


def dedupe_feed_items(html):
    """概念页：多个已删 slug 重定向到同一保留篇时，只保留第一条。"""
    pieces, last, seen, changed = [], 0, set(), False
    for s, e, block in split_feed_items(html):
        slugs = NEWS_LINK_RE.findall(block)
        if slugs and all(sl in seen for sl in slugs):
            changed = True
            pieces.append(html[last:s])
            last = e
        else:
            seen.update(slugs)
    if not changed:
        return html
    pieces.append(html[last:])
    return "".join(pieces)


def fill_candidates(by_topic, topic, exclude, limit):
    """同主题优先，按时间倒序取补位文章。"""
    seen, out = set(), []
    for a in by_topic.get(topic, []):
        if a["slug"] in exclude or a["slug"] in seen:
            continue
        seen.add(a["slug"])
        out.append(a)
        if len(out) >= limit:
            break
    return out


def render_items(items):
    lis = "".join(
        f'<li><a href="/news/{a["slug"]}">{escape(str(a["title"]))}</a> '
        f'<span class="tag-date">{a.get("date", "")}</span></li>'
        for a in items)
    return (f'<div class="related-block"><h3>延伸阅读</h3>'
            f'<ul class="related-list">{lis}</ul></div>')


def main():
    arts, redirects, valid, by_slug, by_topic = load()
    stats = {"redirected": 0, "dropped": 0, "filled": 0, "pages": 0}
    unmapped = {}

    for path in sorted(ROOT.rglob("*.html")):
        try:
            html = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        orig = html

        # ---------- 0. 概念页/列表页：整块剔除无法映射的 feed-item ----------
        if 'class="feed-item"' in html:
            html = drop_dead_feed_items(html, valid, redirects, stats, unmapped, rel)

        # ---------- 1. 文章页「延伸阅读」块 ----------
        self_slug = path.name if rel.startswith("news/") else None
        self_art = by_slug.get(self_slug) if self_slug else None

        def repl_block(m):
            items = []
            used = {self_slug} if self_slug else set()
            for slug, _title, _date in REL_ITEM_RE.findall(m.group(1)):
                if slug in valid:
                    if slug in used:
                        stats["dropped"] += 1
                        continue
                    used.add(slug)
                    items.append(by_slug[slug])
                    continue
                tgt = redirects.get(slug)
                if tgt and tgt in valid:
                    stats["redirected"] += 1
                    if tgt in used:
                        stats["dropped"] += 1
                        continue
                    used.add(tgt)
                    items.append(by_slug[tgt])
                else:
                    stats["dropped"] += 1
                    unmapped.setdefault(slug, []).append(rel)
            if len(items) < TARGET_RELATED and self_art:
                for a in fill_candidates(by_topic, self_art.get("topic", ""),
                                         used, TARGET_RELATED - len(items)):
                    used.add(a["slug"])
                    items.append(a)
                    stats["filled"] += 1
            return render_items(items) if items else ""

        if REL_BLOCK_RE.search(html):
            html = REL_BLOCK_RE.sub(repl_block, html)

        # ---------- 2. 其他位置（列表页 / 概念页）的裸链接重定向 ----------
        def repl_link(m):
            slug = m.group(1)
            if slug in valid:
                return m.group(0)
            tgt = redirects.get(slug)
            if tgt and tgt in valid:
                stats["redirected"] += 1
                return f'href="/news/{tgt}"'
            unmapped.setdefault(slug, []).append(rel)
            return m.group(0)

        parts, last = [], 0
        for m in REL_BLOCK_RE.finditer(html):
            parts.append(NEWS_LINK_RE.sub(repl_link, html[last:m.start()]))
            parts.append(m.group(0))
            last = m.end()
        parts.append(NEWS_LINK_RE.sub(repl_link, html[last:]))
        html = "".join(parts)

        # ---------- 3. 重定向后去重（多个已删 slug 指向同一保留篇）----------
        if 'class="feed-item"' in html:
            html = dedupe_feed_items(html)

        if html != orig:
            stats["pages"] += 1
            if not DRY:
                path.write_text(html, encoding="utf-8")
            print("fixed:", rel)

    # ---------- 3. 自检 ----------
    remaining = []
    for path in sorted(ROOT.rglob("*.html")):
        try:
            html = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for s in set(NEWS_LINK_RE.findall(html)):
            if s not in valid:
                remaining.append((str(path.relative_to(ROOT)), s))

    print("\n--- fix_related 汇总 ---")
    print(f"重定向修复 {stats['redirected']} 处 · 去重/移除 {stats['dropped']} 处 · "
          f"补位 {stats['filled']} 处 · 改动页面 {stats['pages']}")
    if unmapped:
        print(f"\n无映射的失效 slug（{len(unmapped)} 个，已剔除）：")
        for s, files in sorted(unmapped.items()):
            print(f"  - {s}（{len(set(files))} 个页面）")
    print(f"\n剩余死链: {len(remaining)} 处")
    for f, s in remaining[:20]:
        print(f"  {f} -> {s}")
    return 1 if remaining else 0


if __name__ == "__main__":
    sys.exit(main())
