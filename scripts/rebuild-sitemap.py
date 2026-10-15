#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rebuild-sitemap.py —— sitemap.xml 重建器（逆向重写版 v1.0）

复刻来源：线上 sitemap.xml（2026-10-14 基线，460 条 loc，零重复）
逆向依据：workflow 注释 + 产物结构三侧交叉确认

规则（自 460 条产物逐组统计得出）：
  文章页 news/*.html：URL 与 lastmod 来自 data/articles.json 登记
    （380 条 date 字段与产物 lastmod 100% 对应验证），而非 glob 文件系统——
    文件系统中存在 3 个未登记孤儿页（截断名旧稿）+ qr.png 等非页面，
    glob 会误收。这是与原管线的关键一致点。
  lastmod（其余页面）= 页面文件的 mtime 日期（YYYY-MM-DD）。
                 管线每天重跑会自然刷新被重写页面（index/news-N/topics/evidence/
                 daily/news 索引），文章页与静态概念页不被重写，保持发布日。
  changefreq/priority 按组规则 + 单页配置表（见 PAGES）。

  分组规则：
    index.html            daily   1.0
    news/index.html       daily   0.8
    news-N.html (N>=2)    daily   0.6    新闻归档分页
    news/*.html           monthly 0.7    文章页
    topics/index.html     weekly  0.8
    topics/*.html         weekly  0.7
    evidence/index.html   weekly  0.8
    evidence/*.html       weekly  0.7
    daily/index.html      daily   0.8
    daily/*.html          monthly 0.6    每日简报历史页
    PAGES 表内单页        逐页配置

  明确排除：404.html（错误页不入 sitemap）、deep-dive/（孤儿目录）、
    assets/ data/ scripts/（非页面）。guide/ 暂不纳入——待接入站内入口后
    由增强版统一纳入（见运营待办 #3）。

与原始管线的差异（预期差异，验收按等价性判定）：
  原版 URL 顺序为 glob 目录序（ext4 readdir 序，跨机器不可复现）；
  本版采用确定性顺序：组间固定、组内有序。URL 集合与逐条属性保持一致。
"""
import importlib.util
import json
import math
import os
import re
import sys
from datetime import datetime

# 与生成器共用 PER_PAGE，杜绝「两处各写一个 30、日后漂移」的隐患。
# 文件名含连字符，不能直接 import，用 importlib 按路径加载。
_spec = importlib.util.spec_from_file_location(
    "gen_news_index", os.path.join(os.path.dirname(os.path.abspath(__file__)), "gen-news-index.py"))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
NEWS_PER_PAGE = _mod.PER_PAGE

BASE = "https://longbiosci.com"

# ---- 单页配置表（顺序照抄原 sitemap 输出顺序）----
# (相对路径, changefreq, priority)
PAGES = [
    ("zh/index.html",         "weekly",  "0.8"),
    ("trials.html",           "daily",   "0.8"),
    ("trials-full.html",      "daily",   "0.6"),
    ("telomere.html",         "monthly", "0.7"),
    ("stemcell.html",         "monthly", "0.7"),
    ("spermidine.html",       "monthly", "0.6"),
    ("senolytic.html",        "monthly", "0.8"),
    ("search.html",           "weekly",  "0.8"),
    ("research/index.html",   "weekly",  "0.8"),
    ("rapamycin.html",        "monthly", "0.7"),
    ("privacy/index.html",    "monthly", "0.5"),
    ("papers/index.html",     "weekly",  "0.7"),
    ("nmn.html",              "monthly", "0.7"),
    ("mobile.html",           "yearly",  "0.4"),
    ("metformin.html",        "monthly", "0.7"),
    ("melatonin.html",        "monthly", "0.6"),
    ("investors/index.html",  "weekly",  "0.7"),
    ("glossary.html",         "monthly", "0.6"),
    ("events/index.html",     "weekly",  "0.6"),
    ("en/index.html",         "weekly",  "0.7"),
    ("cover-generator.html",  "yearly",  "0.4"),
    ("contact/index.html",    "yearly",  "0.5"),
    ("companies/index.html",  "weekly",  "0.7"),
    ("article.html",          "monthly", "0.5"),
    ("about/index.html",      "monthly", "0.6"),
    ("about.html",            "monthly", "0.5"),
]

# 组规则：(glob 模式, changefreq, priority)；索引页单独优先输出
GROUPS = [
    ("topics/*.html",         "weekly",  "0.7"),
    ("evidence/*.html",       "weekly",  "0.7"),
]

# 热词专题组（2026-10-15 P0#3 补收录）
# /guide/ 的 9 个页面自 2026-10-14 就已上线，但从未进过 sitemap——
# 当时只补了页面没接入口也没登记。索引页给 0.8（等同 topics/evidence 索引），
# 专题页 0.7（同组页一视同仁）。
GUIDE_INDEX = ("guide/index.html", "weekly", "0.8")
GUIDE_GROUP = ("guide/*.html", "weekly", "0.7")

# 每日简报页受控清单（golden 基线收录范围）。
# 注意：daily/2026-10-09/10 两篇 AI 简报页与 index-2026-03-11.html 未被收录，
# 属原管线遗留疏漏（文件存在但无登记入口），已在运营待办跟踪，复刻版保持现状。
DAILY_PAGES = ["index.html", "2026-03-28.html"]

# 目录索引页（各组第一个输出）
INDEX_PAGES = [
    ("topics/index.html",     "weekly",  "0.8"),
    ("news/index.html",       "daily",   "0.8"),
    ("evidence/index.html",   "weekly",  "0.8"),
    ("daily/index.html",      "daily",   "0.8"),
]

ARCHIVE_RE = re.compile(r"^news-(\d+)\.html$")  # 带捕获组，便于取页号


def mtime_date(path):
    """文件 mtime 的日期部分；缺失回退今天。"""
    try:
        return datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d")
    except OSError:
        return datetime.now().strftime("%Y-%m-%d")


def collect(root="."):
    """返回 [(relpath, lastmod, changefreq, priority), ...]，确定性顺序。"""
    entries = []

    # 1) topics 组
    entries.append(("topics/index.html", None, *INDEX_PAGES[0][1:]))
    for p in sorted(glob_group(root, "topics/*.html")):
        entries.append((p, None, *GROUPS[0][1:]))

    # 1b) guide 热词专题组：索引页优先，随后 8 个专题页按文件名排序
    entries.append(("guide/index.html", None, *GUIDE_INDEX[1:]))
    for p in sorted(glob_group(root, "guide/*.html")):
        entries.append((p, None, *GUIDE_GROUP[1:]))

    # 2) news 组：索引页 mtime + 文章页全部来自 articles.json 登记
    entries.append(("news/index.html", None, *INDEX_PAGES[1][1:]))
    try:
        with open(os.path.join(root, "data/articles.json"), encoding="utf-8") as f:
            articles = json.load(f)
    except (OSError, ValueError) as e:
        print(f"[error] 读取 data/articles.json 失败: {e}", file=sys.stderr)
        articles = []
    for a in sorted(articles, key=lambda a: a.get("slug", "")):
        entries.append((f"news/{a['slug']}", a.get("date", ""), "monthly", "0.7"))

    # 3) 新闻归档分页 news-N.html
    #    双重防护：既按 ARCHIVE_RE 过滤，也按 articles.json 算出的真实总页数截断。
    #    理由：os.listdir 会把任何残留的 news-N.html 都当成合法分页收进 sitemap。
    #    实测 news-14.html（391 篇时代的孤儿页）曾因此长期被提交给搜索引擎，
    #    与首页「全站 380 篇」直接矛盾。sitemap 是给搜索引擎看的契约，
    #    只允许收录当前真实存在的分页。
    with open(os.path.join(root, "data/articles.json"), encoding="utf-8") as f:
        max_archive_page = max(1, math.ceil(len(json.load(f)) / NEWS_PER_PAGE))
    for name in sorted(
        (n for n in os.listdir(root)
         if ARCHIVE_RE.match(n) and int(ARCHIVE_RE.match(n).group(1)) <= max_archive_page),
        key=lambda n: int(ARCHIVE_RE.match(n).group(1)),
    ):
        entries.append((name, None, "daily", "0.6"))

    # 4) 首页
    entries.append(("index.html", None, "daily", "1.0"))

    # 5) evidence 组
    entries.append(("evidence/index.html", None, *INDEX_PAGES[2][1:]))
    for p in sorted(glob_group(root, "evidence/*.html")):
        entries.append((p, None, *GROUPS[1][1:]))

    # 6) daily 组（受控清单）
    entries.append(("daily/index.html", None, *INDEX_PAGES[3][1:]))
    for name in DAILY_PAGES:
        if name != "index.html":
            entries.append((f"daily/{name}", None, "monthly", "0.6"))

    # 7) 单页配置表（保持原顺序）
    for path, cf, pr in PAGES:
        entries.append((path, None, cf, pr))

    # 附上 lastmod：条目已带日期（articles.json date）则用之，否则取文件 mtime
    out = []
    seen = set()
    for path, own, cf, pr in entries:
        full = os.path.join(root, path)
        if not os.path.isfile(full):
            print(f"[warn] 跳过不存在的页面: {path}", file=sys.stderr)
            continue
        if path in seen:
            continue
        seen.add(path)
        lastmod = own if own else mtime_date(full)
        out.append((path, lastmod, cf, pr))
    return out


def glob_group(root, pattern):
    import glob as _g
    d, pat = pattern.split("/", 1)
    base = os.path.join(root, d)
    if not os.path.isdir(base):
        return []
    return [
        f"{d}/{n}"
        for n in os.listdir(base)
        if n.endswith(".html") and n != "index.html" and _g.fnmatch.fnmatch(n, pat)
    ]


def render(entries):
    lines = [
        "<?xml version='1.0' encoding='UTF-8'?>",
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">',
    ]
    for path, lastmod, cf, pr in entries:
        lines.append("  <url>")
        lines.append(f"    <loc>{BASE}/{path}</loc>")
        lines.append(f"    <lastmod>{lastmod}</lastmod>")
        lines.append(f"    <changefreq>{cf}</changefreq>")
        lines.append(f"    <priority>{pr}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    entries = collect(root)
    xml = render(entries)
    out = os.path.join(root, "sitemap.xml")
    with open(out, "w", encoding="utf-8") as f:
        f.write(xml)
    print(f"sitemap.xml 重建完成: {len(entries)} 条 URL")


if __name__ == "__main__":
    main()
