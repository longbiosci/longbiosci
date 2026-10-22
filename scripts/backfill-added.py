#!/usr/bin/env python3
"""为 data/articles.json 补「收录日」字段 added（幂等）。

added 优先级：
1. data/intake-cursor.json 中该 slug 所属批次的 done_at（巡检消化日，最准）
2. git 首次添加日期（仅当晚于仓库基线提交，即基线之后新收录的文章）
3. 兜底 = 基线提交日期（baseline 批量导入，无法再细分）

用法：python3 scripts/backfill-added.py [repo_root]
"""
import json
import os
import subprocess
import sys

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")


def _git(*args):
    try:
        return subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=60,
        ).stdout.strip()
    except (subprocess.SubprocessError, OSError):
        return ""


def load_cursor_slugs():
    """slug -> done_at 日期（仅 status=done 的批次）。"""
    path = os.path.join(ROOT, "data", "intake-cursor.json")
    m = {}
    try:
        cur = json.load(open(path, encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return m
    for e in cur.get("entries", {}).values():
        if e.get("status") != "done":
            continue
        d = (e.get("done_at") or "")[:10]
        if not d:
            continue
        for s in e.get("slugs") or []:
            m.setdefault(s, d)
    return m


def main():
    path = os.path.join(ROOT, "data", "articles.json")
    with open(path, encoding="utf-8") as f:
        articles = json.load(f)

    # 基线提交（最早把 news/ 批量入库的那个 commit）的日期
    first = _git("log", "--reverse", "--format=%ad", "--date=short", "--", "news/")
    baseline = first.splitlines()[0] if first else ""
    cursor_slugs = load_cursor_slugs()

    filled = from_cursor = from_git = fallback = 0
    for a in articles:
        if a.get("added"):
            continue
        slug = a["slug"]
        d = cursor_slugs.get(slug)
        if d:
            from_cursor += 1
        else:
            gd = _git("log", "--diff-filter=A", "--format=%ad", "--date=short",
                      "--", "news/" + slug).splitlines()
            gd = gd[-1] if gd else ""
            if gd and gd != baseline:
                d = gd
                from_git += 1
            else:
                d = baseline or a.get("date", "")
                fallback += 1
        a["added"] = d
        filled += 1
    with open(path, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"[added] 补写 {filled} 条 / 共 {len(articles)} 条"
          f"（游标 {from_cursor} · git 新增 {from_git} · 基线兜底 {fallback}，"
          f"基线日 {baseline or '未知'}）")


if __name__ == "__main__":
    main()
