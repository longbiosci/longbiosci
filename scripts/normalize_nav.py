#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全站主导航归一化（2026-10-15 P0#3 + P3#17）

背景
----
全站 465 个含 `class="main-nav"` 的文件里散落着 18 种互不一致的写法：
入口集合有 8/9/10 三种、栏目顺序不同、`aria-current` 归属错位、
有的三项挤一行有的全挤一行。既没法一次性维护，也会让读者在不同页面
看到不同的导航。

本脚本把导航统一为一份标准结构：
  首页 / 最新 / 主题专辑 / 热词专题 / 概念与工具 / 周刊 /
  证据分级 / 临床试验 / 产业 / 关于 + 搜索（独立 button 位）

三处一并修好：
  1. `/guide/` 9 个页面此前 aria-current 错标在「主题专辑」上；
  2. 根级 8 个概念页（senolytic / rapamycin / nmn …）此前错标在「主题专辑」，
     实际由 /research/ 收录，改为高亮「概念与工具」；
  3. 381 篇 news/*.html 此前完全没有高亮，读者在文章页看不出自己在哪个栏目，
     统一按路径归属补上。

标签长短优化（移动端实测 3 行 → 2 行，header 151px → 113px）
----------------------------------------------------------
`.nav-mq` 包裹的部分在 max-width:768px 下隐藏，桌面完整、移动端简短。
被测过：不缩短则 320/375/390px 均要 3 行；缩短后三档均为 2 行，
且比改造前（9 项 2 行 115px）还矮 2px——加了两个入口反而更紧凑。
每个用了 `.nav-mq` 的链接都带 `aria-label` 写明完整栏目名，
屏幕阅读器不受视觉缩写影响。

用法
----
  python3 normalize_nav.py <仓库根目录> [--apply]   # 不加 --apply 只报告

幂等：重复运行不产生变化，可以直接当巡检用。
author: LongBiosci 网站运营自动化
"""
import os
import re
import sys

# ---------------------------------------------------------------- 标准导航结构

SEARCH_SVG = (
    '<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true" focusable="false">'
    '<circle cx="6.8" cy="6.8" r="4.6" fill="none" stroke="currentColor" stroke-width="1.6"/>'
    '<line x1="10.3" y1="10.3" x2="14" y2="14" stroke="currentColor" stroke-width="1.6" '
    'stroke-linecap="round"/></svg>'
)

# (href, 桌面显示文本, 移动端显示文本, 是否需要 aria-label)
# 移动端文本为 None 表示不缩写。
ITEMS = [
    ("/", "首页", None),
    ("/news/", "最新", None),
    ("/topics/", "主题专辑", "专辑"),
    ("/guide/", "热词专题", "热词"),
    ("/research/", "概念与工具", "概念"),
    ("/daily/", "周刊", None),
    ("/evidence/", "证据分级", "证据"),
    ("/trials.html", "临床试验", "临床"),
    ("/companies/", "产业", None),
    ("/about/", "关于", None),
]

SEARCH_TMPL = (
    '<a href="/search.html"{cur} class="nav-search" aria-label="站内搜索">{svg}'
    '<span class="nav-search-text">搜索</span></a>'
)


def build_nav(current, indent="      ", nl="\n"):
    """生成导航块的 inner HTML。current 为要高亮的 href（可为 None）。"""
    lines = []
    for href, full, short in ITEMS:
        cur = ' aria-current="page"' if current == href else ""
        # aria-label 只在标签被缩写时才需要：读屏器此时读到的可见文本是短的，
        # 需要它补回完整栏目名。文本未被改写时加 label 纯属冗余。
        label = ""
        if short is None:
            body = full
        else:
            # short 是 full 的前缀 → 隐藏尾部；否则隐藏头部
            if full.startswith(short):
                body = '%s<span class="nav-mq">%s</span>' % (short, full[len(short):])
            else:
                assert full.endswith(short), (full, short)
                body = '<span class="nav-mq">%s</span>%s' % (full[: len(full) - len(short)], short)
            label = ' aria-label="%s"' % full
        lines.append('{i}<a href="{h}"{c}{l}>{b}</a>'.format(
            i=indent, h=href, c=cur, l=label, b=body))
    # 搜索不在 ITEMS 里（它单独占一个 button 位），高亮要在这里补。
    search_cur = ' aria-current="page"' if current == "/search.html" else ""
    lines.append(indent + SEARCH_TMPL.format(cur=search_cur, svg=SEARCH_SVG))
    return nl + nl.join(lines) + nl + indent[:-2]


# ---------------------------------------------------------------- 归属判定规则

# 根级由 /research/ 收录的 8 个概念词条页（见 research/index.html 的链接）
ROOT_CONCEPT_PAGES = {
    "senolytic.html", "metformin.html", "rapamycin.html", "nmn.html",
    "telomere.html", "stemcell.html", "spermidine.html", "melatonin.html",
}


def current_for(rel):
    """按文件路径判定该页所属的导航栏目。rel 为相对仓库根的路径。"""
    rel = rel.replace("\\", "/").lstrip("./")
    parts = rel.split("/")

    if parts[-1] in ("gen-home.py",):
        return "/"
    if parts[-1] in ("gen-news-index.py",):
        return "/news/"
    if parts[-1] in ("gen-topic-pages.py",):
        return "/topics/"

    top = parts[0]
    if rel == "index.html":
        return "/"
    if top == "scripts":
        return None  # 其余脚本按各自角色另行判定，或不动
    if rel == "search.html":
        return "/search.html"
    if rel == "trials.html":
        return "/trials.html"
    if top in ("about", "privacy", "contact", "editorial-policy"):
        return "/about/"
    if top == "news" or re.fullmatch(r"news-\d+\.html", rel):
        return "/news/"
    if top == "topics":
        return "/topics/"
    if top == "guide":
        return "/guide/"
    if top == "research":
        return "/research/"
    if top == "daily":
        return "/daily/"
    if top == "evidence":
        return "/evidence/"
    if top in ("companies", "events", "investors"):
        return "/companies/"
    if top == "papers":
        return "/research/"   # /research/ 把它列在「研究工具」区
    if top == "deep-dive":
        return "/news/"
    if top == "glossary.html" or rel == "glossary.html":
        return "/research/"
    if len(parts) == 1 and rel in ROOT_CONCEPT_PAGES:
        return "/research/"
    return None


# ---------------------------------------------------------------- 替换逻辑

# 匹配外层的 <nav class="...main-nav..."> 或 <div class="...main-nav...">，
# 开标签原样保留（news/*.html 的父 <nav> 已带 aria-label="主导航"，不能动）。
NAV_RE = re.compile(
    r'(<(?:nav|div)[^>]*\bclass="[^"]*\bmain-nav\b[^"]*"[^>]*>)(.*?)(</(?:nav|div)>)',
    re.S,
)


def _looks_escaped(inner):
    """判断 inner 里的换行是字面 \\n 两字符（Python 源里的模板）还是真换行。"""
    return "\\n" in inner and "\n" not in inner


def process(path, rel, apply=False):
    src = open(path, encoding="utf-8", errors="ignore").read()
    m = NAV_RE.search(src)
    if not m:
        return ("skip", "无 main-nav")
    if "{nav_html}" in m.group(2):
        return ("skip", "动态模板 {nav_html}（已废弃的旧生成器，不动）")
    if "<a href=" not in m.group(2):
        return ("skip", "无 <a> 子项")

    cur = current_for(rel)
    nl = "\\n" if _looks_escaped(m.group(2)) else "\n"
    new_inner = build_nav(cur, nl=nl)
    if m.group(2) == new_inner:
        return ("same", "")
    if apply:
        open(path, "w", encoding="utf-8").write(
            src[: m.start(2)] + new_inner + src[m.end(2):]
        )
    return ("change", "高亮→%s" % (cur or "无"))


def main():
    root = sys.argv[1]
    apply_ = "--apply" in sys.argv
    stats = {"change": 0, "same": 0, "skip": 0}
    skips = []
    changed_files = []
    for dirpath, dirnames, filenames in os.walk(root):
        if ".git" in dirpath.split(os.sep):
            continue
        for f in filenames:
            if not f.endswith((".html", ".py")):
                continue
            p = os.path.join(dirpath, f)
            rel = os.path.relpath(p, root)
            try:
                st, msg = process(p, rel, apply_)
            except Exception as e:  # noqa: BLE001
                st, msg = "skip", "异常 %s" % e
            stats[st] += 1
            if st == "change":
                changed_files.append("%-60s %s" % (rel, msg))
            elif st == "skip":
                skips.append("%-60s %s" % (rel, msg))

    print("修改 %d / 已一致 %d / 跳过 %d" % (stats["change"], stats["same"], stats["skip"]))
    if changed_files:
        print("\n--- 将修改 ---")
        for c in changed_files[:60]:
            print("   ", c)
        if len(changed_files) > 60:
            print("    ...(%d more)" % (len(changed_files) - 60))
    if skips:
        print("\n--- 跳过 ---")
        for s in skips:
            print("   ", s)
    if not apply_:
        print("\n（预告模式，未写入。加 --apply 执行）")


if __name__ == "__main__":
    main()
