#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check-links.py —— 全站死链与计数一致性检查（管线第 9 步）

为什么必须有这一步
────────────────
2026-10-15 补写文章时，手写正文里的一个 `/news/xxx.html` 链接少写了作者名
（`Protein-Diet-Longevity-Cell-Review` 漏了 `-Lamming-`），生成时无感、
管线无感、推送无感，直到手工扫全站才发现。

**只要检查不自动化，遗漏就会重演。** 这一步把「死链」和「计数不一致」
变成管线级别的硬失败，而不是靠人眼。

检查项
──────
1. 内部链接：所有 href="/xxx.html" 指向的文件必须存在
2. 内部资源：/style.css /poster.js /logo-mark.svg 等必须存在
3. 计数一致：articles.json / search-index.json / sitemap.xml / 首页 / 搜索页
4. 产出纪律：news/ 下 HTML 文件数与 articles.json 条目数必须相等
5. 证据分级：evidence/index.html 三个分级计数 == articles.json 分级分布，
   且磁盘上的分级分页数量与数据量推导的一致（不多不少）
6. 绝对 URL 与 canonical（2026-10-21 新增）：
   - 所有指向本站的绝对 URL（https://longbiosci.com/...）必须对应存在的文件
   - 每个页面必须有 canonical，且必须**自指**（指向本页自身）
   - canonical 指向的目标必须真实存在

为什么加这一项
──────────────
原检查项 1 只匹配 `href|src="(/[^"#?]+)"`，即**只查以 / 开头的相对路径**。
于是两类缺陷长期无人发现：
- canonical / og:url 写错（404.html → /404/、mobile.html → /mobile/、
  news/Multiverse-Brain-Age-Pipeline-Sensitivity-2026.html → 一个不存在的
  -Prediction- 变体，共3 处，线上全部 404）
- 3 个 daily 周刊页完全没有 canonical（其中 2 个在 sitemap 内）
它们都「不影响页面渲染」，所以管线一路绿灯。SEO 上这是硬伤：
canonical 指向 404 等于主动告诉搜索引擎「这个页面已废弃」。

扫描范围（2026-10-17 扩）
────────────────────
此前只扫根目录 / news/ / topics/，evidence/ guide/ 等栏目页**从未被扫过**。

后果是真实且昂贵的：evidence/index.html 长期写着「A 94 / B 269 / C 17」，
而事实是「A 131 / B 311 / C 109」——整整 425 篇的差异在站内躺了数日无人发现，
原因是「死链扫描」与「计数校验」都绕开了这个目录。
扫描范围自此覆盖全部栏目目录，栏目页漂移与栏目页死链一并纳入。

自检（--self-test）
────────────────
跑这个脚本的检查项会变绿，只说明「没有问题被报告」，不说明「检查被执行了」。
本仓库已经三次栽在这件事上：

  ┌───┬────────────────────┬──────────────────────────────────────────┐
  │ # │ 检查项             │ 失效方式与后果                           │
  ├───┼────────────────────┼──────────────────────────────────────────┤
  │ 1 │ 首页计数           │ 只认「共 N 篇」，而首页写的是「全站 N 篇」│
  │   │                    │ → 正则失配静默跳过，计数校验从未执行     │
  │ 2 │ canonical 自指     │ 把绝对 URL 传给只接受 / 开头的 url_to_disk│
  │   │                    │ → 恒返回 None，自指判定整段被跳过       │
  │ 3 │ 迁移页约束         │ 同上，且分支内还有个未定义变量 tpath     │
  └───┴────────────────────┴──────────────────────────────────────────┘

三次都是同一个模式：**输出里没有红色，就被当成了通过。**
所以本脚本自带反例站点：--self-test 会造 8 个已知好坏的页面，
逐个断言「该报错的必须报错、不该报错的必须不报错」，
任一条不符就 exit 1。检查器自己也要被检查，否则它只是一段绿色的装饰。

覆盖边界（诚实标注）：自检目前只覆盖 canonical 判定与首页/搜索页计数口径，
死链、证据分级、sitemap 三项仍只有正向执行、没有反向探针。

退出码：0 = 全通过；1 = 有问题（清单打印到stdout）
"""
import contextlib
import glob
import io
import json
import math
import os
import re
import shutil
import sys
import tempfile
from collections import Counter

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."


# 全站栏目目录。改这里等于改「哪些页面会被扫到」——
# 新增栏目目录务必登记，否则该目录的死链与计数漂移会再次隐身。
SCAN_DIRS = ["", "news", "topics", "evidence", "guide", "research",
             "companies", "events", "daily", "about", "privacy",
             "investors", "industry", "podcast", "papers", "search"]


def iter_pages():
    for d in SCAN_DIRS:
        for p in sorted(glob.glob(os.path.join(ROOT, d, "*.html"))):
            yield p, open(p, encoding="utf-8", errors="ignore").read()


def url_to_disk(url):
    """站内 URL(/x/y.html) → 磁盘路径；None 表示不是本站路径。"""
    u = url.split("#")[0].split("?")[0]
    if not u.startswith("/"):
        return None
    disk = os.path.join(ROOT, u.lstrip("/"))
    if u.endswith("/") or u == "":
        disk = os.path.join(disk, "index.html")
    return disk


def page_self_url(rel):
    """页面自身的规范 URL（/x/y.html）。入参是**仓库内相对路径**，不是磁盘路径。

    2026-10-22 修正（本仓库第四处「写了检查但检查没生效」）：
    此前这里还会再做一次 os.path.relpath(rel, ROOT)，而入参 rel 本身已经是
    相对路径了 —— 重复 relpath 会把它当成「相对于 cwd」重新解析，
    于是 cwd == ROOT 时凑巧正确（管线正好是在站点根跑的），
    而 cwd != ROOT 时（例：`cd /tmp && check-links.py /workspace/work`）
    算出来是 ../../xxx 这种垃圾，自指判定整体失真却依然报绿。

    同时删掉了一个 `rel.startswith("index.html")` 分支：rel 由 glob 产出、
    形如 topics/index.html，永远不可能以 index.html 开头，那是没用的残留，
    留着只会让人误以为它处理过某种情况。
    """
    if rel == "index.html":
        return "/"
    return "/" + rel


ABS_URL_RE = re.compile(r'https?://longbiosci\.com(/[^\s"\'<>]*)')
CANON_RE = re.compile(r'<link[^>]*rel="canonical"[^>]*href="([^"]+)"', re.I)
# 「页面已迁移」守卫页的自证标记。由 scripts/gen-redirects.py 写入，
# 没有它就无法把「故意指向别处的 canonical」和「写错的 canonical」区分开。
STUB_MARK = "lb-redirect-stub"
REFRESH_RE = re.compile(
    r'<meta[^>]*http-equiv=["\']refresh["\'][^>]*content=["\'][^"\']*?url=([^"\'>]+)',
    re.I)


def canon_path(url):
    """绝对 URL → 站内路径（/news/x.html 或 /about/）；非本站返回 None。

    历史教训（2026-10-22）：此前直接把绝对 URL 传给 url_to_disk，
    而它只对以 / 开头的串返回路径 —— 结果是**返回 None，自指判定整段被跳过**。
    「写了检查但检查没生效」在本仓库已是第三次复现（另见下面 total-count 注释）。
    判定能不能跑到，必须自己验一遍，不能因为输出里没有红色就当通过。
    """
    u = url.split("#")[0].split("?")[0]
    for p in ("https://longbiosci.com", "http://longbiosci.com"):
        if u.startswith(p):
            return u[len(p):] or "/"
    return None


def canon_norm(u):
    """把 /x/index.html 与 /x/ 归一，避免目录形式造成的假性不自指。"""
    if u.endswith("/index.html"):
        return u[:-len("index.html")]
    if u == "/index.html":
        return "/"
    return u


# ⚠️ 首页计数字样有两个口径：本站实际写的是「全站 N 篇」。
# 历史上这里只认「共 N 篇」—— 正则失配时代码静默跳过、不报错，
# 于是这个校验**从来没真正执行过**。两个口径都要认，缺一即退化。
# 提到模块级是为了让 --self-test 能直接拿样本验证它们各自都能命中。
HOME_COUNT_PATTERNS = (
    re.compile(r"全站\s*([\d,]+)\s*篇"),
    re.compile(r"共\s*([\d,]+)\s*篇"),
)
TOTAL_COUNT_RE = re.compile(r'id="total-count"[^>]*>([\d,]+)')


def check_canonical_and_abs(problems, details):
    """检查 6：canonical 存在性、自指性、目标存在性 + 站内绝对 URL 有效性"""
    n_pages = n_canon = 0
    seen_abs = set()
    for path, h in iter_pages():
        rel = os.path.relpath(path, ROOT).replace("\\", "/")
        n_pages += 1
        is_stub = STUB_MARK in h

        # canonical 存在性
        m = CANON_RE.search(h)
        if not m:
            problems["缺 canonical"] += 1
            details.append(f"缺 canonical  {rel}")
        else:
            n_canon += 1
            target = m.group(1).strip()
            cpath = canon_path(target)
            if cpath is None:
                # 指向站外：只要求是合法绝对 URL
                if not target.startswith(("http://", "https://")):
                    problems["canonical 非绝对 URL"] += 1
                    details.append(f"canonical 非绝对URL  {rel} -> {target}")
            else:
                disk = url_to_disk(cpath)
                if disk is None or not os.path.exists(disk):
                    problems["canonical 指向失效"] += 1
                    details.append(f"canonical 指向失效  {rel} -> {target}")
                elif is_stub:
                    # 迁移守卫页：canonical **必须**指向保留版本（自指就是配置漏了）
                    if canon_norm(cpath) == canon_norm(page_self_url(rel)):
                        problems["迁移页 canonical 自指"] += 1
                        details.append(f"迁移页canonical自指  {rel} -> {target}")
                    rm = REFRESH_RE.search(h)
                    if not rm:
                        problems["迁移页缺 meta refresh"] += 1
                        details.append(f"迁移页缺meta refresh  {rel}")
                    elif canon_norm(canon_path(rm.group(1).strip()) or "") \
                            != canon_norm(cpath):
                        problems["迁移页 refresh 目标不一致"] += 1
                        details.append(f"迁移页refresh不一致  {rel} -> {rm.group(1)}")
                else:
                    # 普通页：自指判定（真正生效前这里是一段永不执行的死代码）
                    if canon_norm(cpath) != canon_norm(page_self_url(rel)):
                        problems["canonical 非自指"] += 1
                        details.append(f"canonical 非自指  {rel} -> {target}")

        # 站内绝对 URL 一律校验（含 og:url、JSON-LD、正文绝对链接）
        for u in ABS_URL_RE.findall(h):
            if (u, rel) in seen_abs:
                continue
            seen_abs.add((u, rel))
            disk = url_to_disk(u)
            if disk and not os.path.exists(disk):
                problems["绝对 URL 失效"] += 1
                details.append(f"绝对URL 失效  {rel} -> {u}")

    print(f"[SEO] {n_pages} 个页面 / {n_canon} 个有 canonical"
          f" / 站内绝对 URL 去重后 {len({u for u, _ in seen_abs})} 个")


def rel_targets():
    """站内绝对路径（/xxx.html）→ 对应磁盘文件"""
    t = set()
    paths = []
    for d in SCAN_DIRS:
        paths += glob.glob(os.path.join(ROOT, d, "*.html"))
    for p in paths:
        h = open(p, encoding="utf-8", errors="ignore").read()
        for m in re.findall(r'(?:href|src)="(/[^"#?]+)"', h):
            t.add(m)
    return t


def _render_probe(canon, refresh=None, stub=False, with_canon=True):
    """构造一个自检用页面。canon / refresh 均为站内路径（/x.html）。"""
    parts = ['<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><title>p</title>']
    if stub:
        parts.append(f"<!-- {STUB_MARK} -->")
    if with_canon:
        parts.append(f'<link rel="canonical" href="https://longbiosci.com{canon}">')
    if refresh is not None:
        parts.append(f'<meta http-equiv="refresh"'
                     f' content="0; url=https://longbiosci.com{refresh}">')
    parts.append("</head><body>probe</body></html>")
    return "\n".join(parts) + "\n"


def _probe_files(canon, refresh=None, stub=False, with_canon=True,
                 target_exists=True):
    """一个探针小站：被指的目标页（可选）+ 受检的 case.html。"""
    files = {}
    if target_exists:
        files["target.html"] = _render_probe("/target.html")
    files["case.html"] = _render_probe(canon, refresh, stub, with_canon)
    return files


# 探针表：(名字, 页面构造参数, 期望触发的问题类型集合)
# 期望为空集合 = 这个页面是健康的，**任何**报错都算误伤。
# 每个探针都是一条独立的断言：改了判定逻辑却没改这里，自检就会红。
SELF_TEST_PROBES = (
    ("健康普通页", dict(canon="/case.html", target_exists=False), set()),
    ("普通页 canonical 非自指", dict(canon="/target.html"),
     {"canonical 非自指"}),
    ("canonical 指向失效", dict(canon="/gone.html", target_exists=False),
     {"canonical 指向失效", "绝对 URL 失效"}),
    ("缺 canonical", dict(canon="/case.html", with_canon=False,
                          target_exists=False), {"缺 canonical"}),
    ("迁移页 canonical 自指",
     dict(canon="/case.html", refresh="/case.html", stub=True,
          target_exists=False), {"迁移页 canonical 自指"}),
    ("迁移页缺 meta refresh",
     dict(canon="/target.html", stub=True), {"迁移页缺 meta refresh"}),
    ("迁移页 refresh 目标不一致",
     dict(canon="/target.html", refresh="/case.html", stub=True),
     {"迁移页 refresh 目标不一致"}),
    ("健康迁移页", dict(canon="/target.html", refresh="/target.html",
                        stub=True), set()),
)


def _run_probe(files):
    """在隔离的临时目录里跑一次 canonical 判定，返回问题类型集合。

    必须隔离：探针页绝不能落进真实站点目录（会被管线当成真页面扫进去）。
    也必须临时改 ROOT —— 判定函数是直接读模块级全局的。
    """
    global ROOT
    tmp = tempfile.mkdtemp(prefix="lb-selftest-")
    saved_root = ROOT
    ROOT = tmp
    try:
        for name, html in files.items():
            with open(os.path.join(tmp, name), "w", encoding="utf-8") as f:
                f.write(html)
        problems, buf = Counter(), io.StringIO()
        with contextlib.redirect_stdout(buf):   # 吞掉判定函数的例行 [SEO] 打印
            check_canonical_and_abs(problems, [])
        return set(problems)
    finally:
        ROOT = saved_root
        shutil.rmtree(tmp, ignore_errors=True)


def self_test():
    """反例驱动的自检：证明这些判定真的会跑、真的会报错。"""
    print("[自检] canonical 判定探针")
    failed = 0
    for name, kwargs, expect in SELF_TEST_PROBES:
        got = _run_probe(_probe_files(**kwargs))
        if got == expect:
            label = "无问题（正确）" if not expect else "、".join(sorted(got))
            print(f"   ✅ {name} → {label}")
        else:
            failed += 1
            miss = sorted(expect - got)
            extra = sorted(got - expect)
            print(f"   ❌ {name}：期望 {'、'.join(sorted(expect)) or '无问题'}"
                  f"｜实际 {'、'.join(sorted(got)) or '无问题'}")
            if miss:
                print(f"      未报出（判定没生效）: {'、'.join(miss)}")
            if extra:
                print(f"      多报（可能是误伤）: {'、'.join(extra)}")

    # 计数口径：只认一个口径就是历史上第二次假阳性的根因，两个都要验
    n_expected = 570
    for sample, pat in zip(("全站 570 篇", "共 570 篇"), HOME_COUNT_PATTERNS):
        m = pat.search(sample)
        ok = m is not None and int(m.group(1).replace(",", "")) == n_expected
        print(f"   {'✅' if ok else '❌'} 首页计数口径「{sample}」→ "
              f"{'命中 ' + m.group(1) if m else '未命中'}")
        if not ok:
            failed += 1
    m = TOTAL_COUNT_RE.search('<span id="total-count">570</span>')
    ok = m is not None and int(m.group(1).replace(",", "")) == n_expected
    print(f"   {'✅' if ok else '❌'} 搜索页计数标记 → {'命中 ' + m.group(1) if m else '未命中'}")
    if not ok:
        failed += 1

    total = len(SELF_TEST_PROBES) + 3
    print()
    if failed:
        print(f"❌ 自检失败：{failed}/{total} 项未按预期触发"
              f" —— 检查器自身已失准，它的输出不可信")
        return 1
    print(f"✅ 自检通过：{total}/{total} 项按预期触发"
          f"（含 {len(SELF_TEST_PROBES)} 个反例探针）")
    print("   覆盖边界：仅 canonical 判定与计数口径，"
          "死链/证据分级/sitemap 三项仍无反向探针")
    return 0


def main():
    problems = Counter()
    details = []

    # ---- 1) 内部链接与资源 ----
    checked = 0
    for t in sorted(rel_targets()):
        if t.startswith("//"):
            continue
        checked += 1
        disk = os.path.join(ROOT, t.lstrip("/"))
        if t.endswith("/"):                      # 目录链接：看有没有 index.html
            disk = os.path.join(disk, "index.html")
        if not os.path.exists(disk):
            problems["死链"] += 1
            details.append(f"死链  {t}")
    print(f"[链接] 检查 {checked} 个站内绝对路径引用")

    # ---- 1b) canonical 与站内绝对 URL ----
    check_canonical_and_abs(problems, details)

    # ---- 2) articles.json 与 news/ 文件数一致 ----
    # news/ 下有一批刻意的「页面已迁移」占位页（旧 URL 保留以防外链失效），
    # 它们不是文章，不参与计数。
    MIGRATED = "页面已迁移"
    arts = json.load(open(os.path.join(ROOT, "data/articles.json"), encoding="utf-8"))
    files, migrated = [], 0
    for p in glob.glob(os.path.join(ROOT, "news", "*.html")):
        base = os.path.basename(p)
        if base.startswith("news-") or base == "index.html":
            continue
        head = open(p, encoding="utf-8", errors="ignore").read(2000)
        if MIGRATED in head:
            migrated += 1
            continue
        files.append(p)
    print(f"[计数] articles.json {len(arts)} 条 / news/ 文章文件 {len(files)} 个"
          f"（另有 {migrated} 个迁移占位页，不计入）")
    if len(arts) != len(files):
        problems["计数不一致"] += 1
        only_a = {a["slug"] for a in arts} - {os.path.basename(p) for p in files}
        only_f = {os.path.basename(p) for p in files} - {a["slug"] for a in arts}
        details.append(f"计数不一致 articles={len(arts)} files={len(files)}"
                       + (f" 仅在 articles: {sorted(only_a)[:3]}" if only_a else "")
                       + (f" 仅在磁盘: {sorted(only_f)[:3]}" if only_f else ""))

    # ---- 3) 搜索索引 / sitemap / 首页 / 搜索页计数 ----
    si_path = os.path.join(ROOT, "data/search-index.json")
    n_index = 0
    if os.path.exists(si_path):
        si = json.load(open(si_path, encoding="utf-8"))
        n_index = sum(1 for r in si if isinstance(r, list) and len(r) > 1
                      and str(r[1]).startswith("/news/"))
        print(f"[计数] search-index {n_index} 条 news")
        if n_index != len(arts):
            problems["搜索索引不一致"] += 1
            details.append(f"search-index {n_index} != articles {len(arts)}")

        # ---- 3b) 搜索索引的「栏目页」条目必须真的有页面 ----
        # 2026-10-23 新增。此前的盲区：本脚本只校验 HTML 里的链接，
        # 而 search-index.json 的 15 条栏目页条目是**旧基线继承下来、无人校验**的。
        # 其中 "/papers/" 一直指向一个不存在的目录 —— 读者在站内搜索里点
        # 「论文索引」，落地就是 404。这条死链由我们自己的搜索结果产出，
        # 却因为「不是 HTML 里的 href」整整一周没被发现。
        # 判据：非 /news/ 的条目（栏目页 / 工具页）必须能在磁盘上找到对应文件。
        dead_entries = []
        for r in si:
            if not (isinstance(r, list) and len(r) > 1 and isinstance(r[1], str)):
                continue
            u = r[1]
            if u.startswith("/news/"):
                continue
            disk = url_to_disk(u)
            if disk is None or not os.path.exists(disk):
                dead_entries.append(u)
        if dead_entries:
            problems["搜索索引死条目"] += 1
            details.append("搜索索引死条目（点进去 404）: "
                           + ", ".join(sorted(set(dead_entries))[:8]))

    sm = os.path.join(ROOT, "sitemap.xml")
    if os.path.exists(sm):
        n_url = open(sm, encoding="utf-8").read().count("<loc>")
        print(f"[计数] sitemap {n_url} 条 URL")
        # sitemap 含栏目页等非文章 URL，只要求不少于文章数
        if n_url < len(arts):
            problems["sitemap 偏少"] += 1
            details.append(f"sitemap {n_url} < articles {len(arts)}")

    home = os.path.join(ROOT, "index.html")
    if os.path.exists(home):
        h = open(home, encoding="utf-8").read()
        # 两个口径都要认（理由见 HOME_COUNT_PATTERNS 处的注释：
        # 只认一个时，正则失配会静默跳过，这个校验等于没跑）。
        m = None
        for pat in HOME_COUNT_PATTERNS:
            m = pat.search(h)
            if m:
                break
        if m:
            n_home = int(m.group(1).replace(",", ""))
            print(f"[计数] 首页声明 {n_home} 篇")
            if n_home != len(arts):
                problems["首页计数不一致"] += 1
                details.append(f"首页 {n_home} != articles {len(arts)}")
        else:
            problems["首页无计数标记"] += 1
            details.append("首页未找到「共 N 篇」或「全站 N 篇」计数标记")

    search = os.path.join(ROOT, "search.html")
    if os.path.exists(search):
        h = open(search, encoding="utf-8").read()
        m = TOTAL_COUNT_RE.search(h)
        if m:
            n = int(m.group(1).replace(",", ""))
            print(f"[计数] 搜索页声明 {n} 篇")
            if n != len(arts):
                problems["搜索页计数不一致"] += 1
                details.append(f"搜索页 {n} != articles {len(arts)}")

    # ---- 4) 证据分级页与事实源一致 ----
    # 三件事一起查，缺一件都会让 /evidence/ 与 articles.json 分叉：
    #   ① 索引页三个分级的计数
    #   ② 磁盘上各分级的分页数量（多 = 孤儿页会被搜录；少 = 读者看不到后半部分）
    #   ③ 分级页里列出的文章数 == 该分级的文章总数
    ev_index = os.path.join(ROOT, "evidence", "index.html")
    if os.path.exists(ev_index):
        h = open(ev_index, encoding="utf-8").read()
        tier_counts = Counter((a.get("evidence") or "").upper() for a in arts)
        # 卡片在页面上的顺序由 gen-evidence-pages.py 的 TIER_CONFIG 固定为 A/B/C，
        # 故按文档顺序取到的计数序列可与 ["A","B","C"] 一一对应。
        # 注意：单捕获组的 findall 返回字符串列表，不是二元组 —— 别再写成 for code, n in ...
        ev_counts = [int(n.replace(",", "")) for n in
                     re.findall(r'class="ev-n">([\d,]+)\s*篇</span>', h)]
        shown = dict(zip(("A", "B", "C"), ev_counts))
        print(f"[证据] articles 分布 {dict(sorted(tier_counts.items()))}"
              f" / 索引页显示 {sorted(shown.items())}")
        if not shown:
            problems["证据索引无计数"] += 1
            details.append("evidence/index.html 未找到分级计数标记")
        else:
            for code in sorted(tier_counts):
                if code not in ("A", "B", "C"):
                    continue
                if shown.get(code) != tier_counts[code]:
                    problems["证据索引计数不一致"] += 1
                    details.append(f"evidence 索引 {code} 级 {shown.get(code)}"
                                    f" != articles {tier_counts[code]}")
        # 分页数量：按 PER_PAGE 推导，与 gen-evidence-pages.py 保持同一常量
        ev_per_page = 24
        for code in ("A", "B", "C"):
            n = tier_counts.get(code, 0)
            want = max(1, math.ceil(n / ev_per_page))
            have = sorted(
                int(x) for x in re.findall(
                    rf"^{code}-(\d+)\.html$",
                    "\n".join(os.listdir(os.path.join(ROOT, "evidence"))),
                    re.M)
            )
            # 真实存在的分页号集合应为 {2..want}
            want_set = set(range(2, want + 1))
            extra = sorted(set(have) - want_set)
            missing = sorted(want_set - set(have))
            page1 = os.path.join(ROOT, "evidence", f"{code}.html")
            if n > 0 and not os.path.exists(page1):
                problems["证据分级页缺失"] += 1
                details.append(f"evidence/{code}.html 不存在（该级 {n} 篇）")
            if extra:
                problems["证据孤儿分页"] += 1
                details.append(f"evidence/{code} 多余分页 {extra}（应到 {want}）")
            if missing:
                problems["证据分页缺失"] += 1
                details.append(f"evidence/{code} 缺失分页 {missing}（应到 {want}）")

    # ---- 汇总 ----
    print()
    if not problems:
        print("✅ 检查通过：死链 0 · 计数全一致")
        return 0
    print(f"❌ 发现 {sum(problems.values())} 类问题：{dict(problems)}")
    for d in details[:30]:
        print("   " + d)
    return 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    sys.exit(main())
