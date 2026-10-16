#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify-pipeline.py —— LongBiosci 本地管线（10 环节）整体验收脚本 v1.0

做法：把仓库整体复制到临时目录（cp -a 保留 mtime）→ 在副本上按
run-pipeline.sh 的顺序跑完 10 个脚本 → 与仓库线上基线逐件比对。

验收口径：
  · data/articles.json / index.html / topics/*.html / news/*.html /
    news-N.html / rss.xml      —— 逐字节一致
  · sitemap.xml               —— 集合 + 逐条属性（lastmod/changefreq/priority）
                                 等价（顺序为确定性顺序，与线上历史区块序
                                 不同属已知偏差，不影响 SEO 语义）
  · 文件集合                  —— 不多不少

仓库（golden）文件全程只读，不会被改动。
"""
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile

PIPE = os.path.dirname(os.path.abspath(__file__))


def _repo_root(pipe):
    """定位仓库根：开发态在 <pipe>/../repo_push，入库后（scripts/）在 <pipe>/.."""
    cand = os.path.abspath(os.path.join(pipe, "..", "repo_push"))
    if os.path.isdir(os.path.join(cand, "data")):
        return cand
    return os.path.abspath(os.path.join(pipe, ".."))


REPO = _repo_root(PIPE)
SKIP_DIRS = {".git", "__pycache__"}
URL_RE = re.compile(
    r"<url>\s*<loc>https://longbiosci\.com/([^<]*)</loc>\s*"
    r"<lastmod>([^<]*)</lastmod>\s*<changefreq>([^<]*)</changefreq>\s*"
    r"<priority>([^<]*)</priority>")


# 「易变时间戳白名单」：这些字段写的是「本次运行时刻」，不是内容。
# 逐字节比对时若不归一化，[B] 每轮必 FAIL 一次，而人工甄别两轮之后
# 都证明是虚警——真出问题时，虚警会把它淹掉。故在此显式剔除，
# 并在命中时打印说明，保留可追溯性。
VOLATILE = {
    "rss.xml": [(re.compile(rb"<lastBuildDate>[^<]*</lastBuildDate>"),
                 b"<lastBuildDate>@VOLATILE@")],
}
_volatile_hit = set()


def sha(path, rel=""):
    with open(path, "rb") as f:
        data = f.read()
    for pat, rep in VOLATILE.get(rel, ()):
        new = pat.sub(rep, data)
        if new != data:
            _volatile_hit.add(rel)
        data = new
    return hashlib.sha256(data).hexdigest()


def snapshot(root):
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root)
            out[rel] = sha(full, rel)
    return out


def parse_sitemap(path):
    x = open(path, encoding="utf-8").read()
    return x.split("\n", 1)[0], URL_RE.findall(x)


def first_diff(a, b, label, limit=3):
    """打印首个差异位置，返回是否一致。"""
    if a == b:
        return True
    print(f"  [FAIL] {label}: {len(a)} B vs {len(b)} B")
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            lo = max(0, i - 90)
            print(f"    首个差异 @ {i}")
            print("    got :", repr(a[lo:i + 90]))
            print("    want:", repr(b[lo:i + 90]))
            return False
    print(f"    前缀一致但长度不同（差 {abs(len(a) - len(b))} B）")
    print("    got  tail:", repr(a[-140:]))
    print("    want tail:", repr(b[-140:]))
    return False


def main():
    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        case = os.path.join(tmp, "site")
        print(f"[0] 复制仓库基线 → {case}")
        shutil.copytree(REPO, case, ignore=shutil.ignore_patterns(*SKIP_DIRS))

        # sitemap 的非文章页 lastmod 取自文件 mtime：先从 golden 还原再跑管线
        _, gold_urls = parse_sitemap(os.path.join(case, "sitemap.xml"))
        import time
        restored = 0
        for path, lastmod, _cf, _pr in gold_urls:
            full = os.path.join(case, path)
            if os.path.isfile(full):
                ts = time.mktime(time.strptime(lastmod, "%Y-%m-%d")) + 12 * 3600
                os.utime(full, (ts, ts))
                restored += 1
        print(f"    还原 mtime: {restored}/{len(gold_urls)} 个页面")

        gold = snapshot(case)

        print("[1] 执行 run-pipeline.sh（10 环节）")
        r = subprocess.run(["bash", os.path.join(PIPE, "run-pipeline.sh"), case],
                           capture_output=True, text=True)
        print(r.stdout.rstrip())
        if r.returncode != 0:
            print(r.stderr)
            raise SystemExit("❌ 管线执行失败")

        new = snapshot(case)

        # ---- A) 文件集合 ----
        only_new = sorted(set(new) - set(gold))
        only_gold = sorted(set(gold) - set(new))
        if only_new or only_gold:
            ok = False
            print(f"[A] 文件集合: FAIL  多出 {only_new[:8]}  缺失 {only_gold[:8]}")
        else:
            print(f"[A] 文件集合一致（{len(new)} 个文件）: PASS")

        # ---- B) 逐字节比对（排除 sitemap.xml，单独等价验收）----
        changed = [p for p in gold if gold[p] != new[p] and p != "sitemap.xml"]
        shown = 0
        for p in sorted(changed):
            if shown < limit_len():
                first_diff(open(os.path.join(case, p), "rb").read(),
                           open(os.path.join(REPO, p), "rb").read(), p)
                shown += 1
        if changed:
            ok = False
        print(f"[B] 产物逐字节一致: {'PASS' if not changed else 'FAIL ' + str(sorted(changed)[:8])}")
        if _volatile_hit:
            print(f"    （已归一化易变时间戳字段：{sorted(_volatile_hit)}——"
                  f"这些字段写的是运行时刻，不是内容）")

        # ---- C) sitemap 等价 ----
        # 整跑会把被重写的页面（topics/ news-N 等）mtime 推进到运行当天，
        # lastmod 随之推进到今天——这与线上「最后一次运行日」的行为一致，
        # 属预期。要验证 lastmod 取值规则本身，需先把 mtime 还原到 golden
        # 记录的日期，再单独重跑环节 5。
        _, gold_urls = parse_sitemap(os.path.join(REPO, "sitemap.xml"))
        for path, lastmod, _cf, _pr in gold_urls:
            full = os.path.join(case, path)
            if os.path.isfile(full):
                ts = time.mktime(time.strptime(lastmod, "%Y-%m-%d")) + 12 * 3600
                os.utime(full, (ts, ts))
        r5 = subprocess.run([sys.executable, os.path.join(PIPE, "rebuild-sitemap.py"), case],
                            capture_output=True, text=True)
        if r5.returncode != 0:
            print(r5.stderr)
            raise SystemExit("❌ rebuild-sitemap.py 单独重跑失败")
        print("    环节 5 单独重跑:", r5.stdout.strip())

        decl_g, urls_g = parse_sitemap(os.path.join(REPO, "sitemap.xml"))
        decl_n, urls_n = parse_sitemap(os.path.join(case, "sitemap.xml"))
        gp = {p: (lm, cf, pr) for p, lm, cf, pr in urls_g}
        np_ = {p: (lm, cf, pr) for p, lm, cf, pr in urls_n}
        missing = sorted(set(gp) - set(np_))
        added = sorted(set(np_) - set(gp))
        attr_diff = {p: (gp[p], np_[p]) for p in set(gp) & set(np_) if gp[p] != np_[p]}
        sitemap_ok = not missing and not added and not attr_diff and decl_g == decl_n
        print(f"[C] sitemap.xml: {len(urls_g)} → {len(urls_n)} 条  "
              f"{'PASS（集合+属性等价）' if sitemap_ok else 'FAIL（%d 条属性不符）' % len(attr_diff)}")
        if missing:
            print("    缺失:", missing[:8])
        if added:
            print("    多出:", added[:8])
        for p, (g, n) in list(attr_diff.items())[:5]:
            print(f"    {p}: golden={g} new={n}")
        order_same = [p for p, *_ in urls_g] == [p for p, *_ in urls_n]
        if not order_same:
            print("    ⚠️ 顺序与线上历史序不同（确定性顺序，已知偏差，不影响语义）")
        ok &= sitemap_ok

        # ---- D) 关键产物存在性 ----
        must = ["data/articles.json", "index.html", "rss.xml", "sitemap.xml",
                "news/index.html", "topics/index.html"]
        lack = [m for m in must if not os.path.isfile(os.path.join(case, m))]
        print(f"[D] 关键产物齐备: {'PASS' if not lack else 'FAIL ' + str(lack)}")
        ok &= not lack

    print("\n总结:", "✅ 全管线验收通过" if ok else "❌ 存在失败项")
    return 0 if ok else 1


def limit_len():
    return 3


if __name__ == "__main__":
    sys.exit(main())
