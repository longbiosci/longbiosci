#!/usr/bin/env python3
"""flash_validate.py —— 快讯栏目（lb-flash-v1）校验器（管线末位守卫）

背景：2026-10-27 起，午刊班 13508579 的直发权限收窄到「快讯」单一栏目
（data/flash.json + /flash.html），与主内容管线（articles.json/news/）完全隔离。
本脚本负责守住这条边界：
  1. flash.json 结构合法（schema / items / 每条必备字段）；
  2. 每条快讯带时间标签：date=YYYY-MM-DD 且 generated_at=YYYY-MM-DD HH:MM；
  3. 每条有可核验来源（source_url / doi / pmid / nct 至少其一）；
  4. 条目上限 30，超出报错（应由午刊班滚动淘汰最旧）；
  5. **隔离断言**：flash 条目不得混入 articles.json（slug/标题互查），
     防止快讯被误当成主内容入正式管线。

用法：python3 scripts/flash_validate.py [--fix-trim]
exit 0 = 通过；exit 1 = 校验失败（管线即失败）。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FLASH = ROOT / "data" / "flash.json"
ARTICLES = ROOT / "data" / "articles.json"
MAX_ITEMS = 30
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DT_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")


def fail(msg: str) -> None:
    print(f"❌ [flash] {msg}")
    sys.exit(1)


def main() -> None:
    if not FLASH.exists():
        fail(f"缺少 {FLASH}（快讯栏目数据源必须存在，可为空列表）")
    try:
        d = json.loads(FLASH.read_text(encoding="utf-8"))
    except Exception as e:
        fail(f"flash.json 不是合法 JSON：{e}")
    if d.get("schema") != "lb-flash-v1":
        fail(f"schema 应为 lb-flash-v1，实际 {d.get('schema')!r}")
    items = d.get("items")
    if not isinstance(items, list):
        fail("items 必须是数组")
    if len(items) > MAX_ITEMS:
        fail(f"快讯 {len(items)} 条超过上限 {MAX_ITEMS}（应由午刊班淘汰最旧条目）")

    ids, titles = set(), []
    for i, it in enumerate(items, 1):
        where = f"第 {i} 条（id={it.get('id', '?')!r}）"
        for key in ("id", "title", "date", "generated_at", "source"):
            if not str(it.get(key, "")).strip():
                fail(f"{where} 缺少必备字段 {key}")
        if not DATE_RE.match(it["date"]):
            fail(f"{where} date 不是 YYYY-MM-DD：{it['date']!r}")
        if not DT_RE.match(it["generated_at"]):
            fail(f"{where} generated_at 不是 YYYY-MM-DD HH:MM：{it['generated_at']!r}")
        if not any(str(it.get(k, "")).strip() for k in ("source_url", "doi", "pmid", "nct")):
            fail(f"{where} 无可核验来源（source_url/doi/pmid/nct 至少其一）")
        if it["id"] in ids:
            fail(f"{where} id 重复")
        ids.add(it["id"])
        titles.append(it["title"])

    # 隔离断言：快讯不得进入主内容库
    if ARTICLES.exists():
        arts = json.loads(ARTICLES.read_text(encoding="utf-8"))
        art_titles = {a.get("title", "") for a in arts}
        art_slugs = {a.get("slug", "") for a in arts}
        clash = [t for t in titles if t in art_titles]
        if clash:
            fail(f"快讯标题与 articles.json 撞车（违反栏目隔离）：{clash[:2]}")
        slug_clash = [i for i in ids if i in art_slugs]
        if slug_clash:
            fail(f"快讯 id 与 articles.json slug 撞车：{slug_clash[:2]}")

    print(f"✅ [flash] 快讯校验通过：{len(items)} 条 · 时间标签齐全 · 来源可核验 · 与主内容库隔离无撞车")


if __name__ == "__main__":
    main()
