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
import hashlib
import importlib.util
import json
import math
import os
import re
import sys
from datetime import datetime

# 与各生成器共用 PER_PAGE，杜绝「两处各写一个 30、日后漂移」的隐患。
# 文件名含连字符，不能直接 import，用 importlib 按路径加载。
_spec = importlib.util.spec_from_file_location(
    "gen_news_index", os.path.join(os.path.dirname(os.path.abspath(__file__)), "gen-news-index.py"))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
NEWS_PER_PAGE = _mod.PER_PAGE

_ev_spec = importlib.util.spec_from_file_location(
    "gen_evidence_pages", os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                       "gen-evidence-pages.py"))
_ev_mod = importlib.util.module_from_spec(_ev_spec)
_ev_spec.loader.exec_module(_ev_mod)
EV_PER_PAGE = _ev_mod.PER_PAGE
EV_TIERS = [c for c, _t, _d, _n in _ev_mod.TIER_CONFIG]

BASE = "https://longbiosci.com"

# ---- 单页配置表（顺序照抄原 sitemap 输出顺序）----
# (相对路径, changefreq, priority)
PAGES = [
    ("zh/index.html",         "weekly",  "0.8"),
    ("flash.html",            "hourly",  "0.6"),  # 快讯栏目（lb-flash-v1 · 午刊班专用）
    ("trials.html",           "daily",   "0.8"),
    ("trials-full.html",      "daily",   "0.6"),
    ("telomere.html",         "monthly", "0.7"),
    ("stemcell.html",         "monthly", "0.7"),
    ("spermidine.html",       "monthly", "0.6"),
    ("senolytic.html",        "monthly", "0.8"),
    ("search.html",           "weekly",  "0.8"),
    ("research/index.html",   "weekly",  "0.8"),
    # /papers/ 论文索引：2026-10-23 新建（此前 search-index 里挂着一句承诺，
    # 但页面从不存在，搜到了点进去是 404）。归入「概念与工具」下，日更 0.7。
    ("papers/index.html",     "daily",   "0.7"),
    ("rapamycin.html",        "monthly", "0.7"),
    ("privacy/index.html",    "monthly", "0.5"),
    ("industry/index.html",   "daily",   "0.8"),
    ("podcast/index.html",    "weekly",  "0.8"),
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
    # about.html 已于 2026-10-23 剔除：它是 gen-redirects.py 按 redirects.json
    # 生成的**迁移守卫页**（canonical → /about/），不是内容页。
    # 守卫页进 sitemap 等于告诉搜索引擎「这个地址有一份独立内容」，
    # 与它自己 canonical 指向别处直接矛盾——canonical 的效力会被自相矛盾的收录削弱。
    # 同一份 redirects.json 里另外 38 条是 news/ 下的文章守卫页，因 sitemap 只收
    # articles.json 登记项而天然不入 sitemap；根级的这一条是唯一漏网的。
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

# 每日简报页：改为**扫描目录、数据驱动**，不再用冻结清单。
#
# 为什么必须改（2026-10-17 实锤）
# --------------------------------
# 原先这里是一份抄自旧基线的受控清单 DAILY_PAGES = ["index.html", "2026-03-28.html"]。
# 那时 daily/ 下确实只有 2 个简报页，清单不算错；此后《预印本速递》每天出一期，
# 目录已长到 20+ 期，清单却从不更新。
#
# 后果是**静默的**：本脚本重建 sitemap 时只吐清单里的 2 条，
# 于是 19 个真实存在、线上本已收录的简报页被一次性踢出 sitemap。
# 可怕之处在于——脚本输出「664 条 URL，重建完成」看着一切正常，
# 只有拿新旧 sitemap 做一次集合差集才会暴露。故改为扫描，并留此注。
DAILY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}.*\.html$")
# 明确排除：与正式索引页重复的历史遗留页，以及同一期的移动版镜像（避免重复内容入 sitemap）
DAILY_EXCLUDE = {"index-2026-03-11.html", "2026-10-10-mobile.html"}

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


# ---- lastmod 状态：内容指纹 ----
# 为什么不能对非文章页直接用 mtime（2026-10-23 修）
# ------------------------------------------------
# 本脚本此前对非文章页取文件 mtime。本地看着没问题（文件是逐日重写的），
# 但在 CI 里 actions/checkout 会把**整棵树的 mtime 刷成 checkout 时刻**，
# 于是每次部署 sitemap 里几十个非文章页的 lastmod 全变成当天——
# 哪怕内容一个字都没动。后果有两层：
#   1) 搜索引擎读到的信号是「这些页面天天更新」，lastmod 的信噪比被自己的
#      构建流程毁掉（Google 明确说过 lastmod 不可信时会直接忽略）；
#   2) 每次提交都夹带几十行纯日期 diff，真正的变更被噪音淹没，
#      也让人不敢用 diff 判断「这次到底改了什么」。
# 改为内容指纹判定：data/page-lastmod.json 记 path → [日期, sha1 前 12 位]，
# 指纹没变就沿用上次日期，变了才写今天。
# 首次运行时以**现有 sitemap.xml 的 lastmod** 作基线（配当前指纹），
# 因此这次改造本身不会造成一次全站日期跳变。
STATE_FILE = "data/page-lastmod.json"


def file_hash(path):
    """文件内容 sha1 前 12 位；读不到返回空串（当作「已变化」处理）。"""
    h = hashlib.sha1()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
    except OSError:
        return ""
    return h.hexdigest()[:12]


def load_state(root):
    try:
        with open(os.path.join(root, STATE_FILE), encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, ValueError):
        return {}
    return {k: (v[0], v[1]) for k, v in raw.items()
            if isinstance(v, list) and len(v) == 2}


def seed_from_sitemap(root):
    """旧 sitemap.xml 的 path → lastmod，用于首次建立指纹基线。"""
    try:
        with open(os.path.join(root, "sitemap.xml"), encoding="utf-8") as f:
            txt = f.read()
    except OSError:
        return {}
    seed = {}
    for block in txt.split("<url>")[1:]:
        m_loc = re.search(r"<loc>([^<]+)</loc>", block)
        m_lm = re.search(r"<lastmod>([^<]+)</lastmod>", block)
        if m_loc and m_lm and m_loc.group(1).strip().startswith(BASE + "/"):
            seed[m_loc.group(1).strip()[len(BASE) + 1:]] = m_lm.group(1).strip()
    return seed


def resolve_lastmod(root, entries):
    """给非文章页补 lastmod。返回 (entries, 新状态, 沿用数, 变更数, 是否首次建基线)。"""
    today = datetime.now().strftime("%Y-%m-%d")
    old = load_state(root)
    seeded = False
    if not old:
        old = {p: (d, "") for p, d in seed_from_sitemap(root).items()}
        seeded = True
    new_state, out, moved = {}, [], []
    kept = changed = 0
    for path, own, cf, pr in entries:
        if own:                      # 文章页：lastmod 就是发布日，不参与指纹判定
            out.append((path, own, cf, pr))
            continue
        h = file_hash(os.path.join(root, path))
        prev_date, prev_hash = old.get(path, ("", ""))
        if prev_date and (prev_hash == h or seeded):
            date, kept = prev_date, kept + 1
        else:
            date, changed = today, changed + 1
            moved.append(path)
        new_state[path] = (date, h)
        out.append((path, date, cf, pr))
    return out, new_state, kept, changed, seeded, moved


def save_state(root, state):
    """逐行写，便于 git diff 直读；内容无变化则不落盘（保持幂等）。"""
    txt = "{\n" + ",\n".join(
        '  %s: ["%s", "%s"]' % (json.dumps(k, ensure_ascii=False), v[0], v[1])
        for k, v in sorted(state.items())) + "\n}\n"
    path = os.path.join(root, STATE_FILE)
    try:
        with open(path, encoding="utf-8") as f:
            if f.read() == txt:
                return False
    except OSError:
        pass
    with open(path, "w", encoding="utf-8") as f:
        f.write(txt)
    return True


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
    #    由 articles.json 推导真实分页数量，而不是 glob 目录。
    #    理由同 news-N：glob 会把任何残留的 A-9.html 都当合法分页提交给搜索引擎，
    #    哪怕该级文章已经减少到只有 4 页。sitemap 是对搜索引擎的契约，
    #    只收录当前真实存在的分页；孤儿分页由 gen-evidence-pages.py 负责清理。
    entries.append(("evidence/index.html", None, *INDEX_PAGES[2][1:]))
    with open(os.path.join(root, "data/articles.json"), encoding="utf-8") as f:
        _arts = json.load(f)
    for code in EV_TIERS:
        n = sum(1 for a in _arts if (a.get("evidence") or "").upper() == code)
        if n == 0:
            continue
        entries.append((f"evidence/{code}.html", None, "weekly", "0.7"))
        for page in range(2, math.ceil(n / EV_PER_PAGE) + 1):
            entries.append((f"evidence/{code}-{page}.html", None, "weekly", "0.6"))

    # 6) daily 组（扫描目录，按文件名排序，确定性顺序）
    entries.append(("daily/index.html", None, *INDEX_PAGES[3][1:]))
    daily_dir = os.path.join(root, "daily")
    if os.path.isdir(daily_dir):
        for name in sorted(n for n in os.listdir(daily_dir)
                           if DAILY_RE.match(n) and n not in DAILY_EXCLUDE):
            entries.append((f"daily/{name}", None, "monthly", "0.6"))

    # 7) 单页配置表（保持原顺序）
    for path, cf, pr in PAGES:
        entries.append((path, None, cf, pr))

    # lastmod 在此只定文章页（articles.json 的 date）；
    # 非文章页留 None，交由 resolve_lastmod() 按内容指纹判定（见上方长注释）。
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
        out.append((path, own, cf, pr))
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
    entries, state, kept, changed, seeded, moved = resolve_lastmod(root, entries)
    xml = render(entries)
    out = os.path.join(root, "sitemap.xml")
    with open(out, "w", encoding="utf-8") as f:
        f.write(xml)
    wrote_state = save_state(root, state)
    print(f"sitemap.xml 重建完成: {len(entries)} 条 URL · "
          f"lastmod 沿用 {kept} 条 / 内容有变 {changed} 条"
          + ("（" + "、".join(moved[:8]) + ("…" if len(moved) > 8 else "") + "）" if moved else "")
          + ("（首次建立指纹基线）" if seeded else "")
          + ("" if wrote_state else " · 指纹状态无变化"))


if __name__ == "__main__":
    main()
