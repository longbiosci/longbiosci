#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_add_rss.py —— add-rss-today-run.py 验收脚本（v1.0）

用例（全部在临时副本上进行，仓库文件只在最后做一次幂等确认）：
  A) 幂等：默认日期（UTC 今天，无今日新文章）重跑 → 与基线逐字节一致
  B) 复刻 10-14 真实运行：前置状态 = 现行 50 篇 + 3 个假 item 垫尾（=53 篇，
     模拟真实运行前的容量），--date 2026-10-14 --now "2026-10-14 00:30:00"
     → 必须与线上 rss.xml 逐字节一致。一招同时验证：
        insert(0) 次序（JSON 逆序）、title/desc 转义、pubDate 格式（+0000）、
        53 上限从队尾丢弃（3 个假 item 被挤掉）、lastBuildDate 刷新
  C) 新文章冒烟：合成一篇含 & < > " ' 的 10-15 文章追加到 articles.json 末尾
     → 置顶、总数仍 53（队尾丢 1 篇）、lastBuildDate 刷新、
     item XML 与手写期望字面量一致（独立验证转义，不依赖脚本自身函数）
  D) 边缘：目录中没有 rss.xml → 生成默认骨架；再补跑 10-14 → 3 篇正确置顶
  收尾：对真实仓库跑一次默认日期，确认逐字节不变（git diff 为空）。
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

PIPE = os.path.dirname(os.path.abspath(__file__))
_CAND = os.path.abspath(os.path.join(PIPE, "..", "repo_push"))  # 开发态
REPO = _CAND if os.path.isdir(os.path.join(_CAND, "data")) else os.path.abspath(os.path.join(PIPE, ".."))
SCRIPT = os.path.join(PIPE, "add-rss-today-run.py")
RSS = os.path.join(REPO, "rss.xml")
ARTICLES = os.path.join(REPO, "data", "articles.json")

ITEM_RE = re.compile(r"<item>.*?</item>", re.S)
LINK_RE = re.compile(r"<link>https://longbiosci\.com/news/([^<]+)</link>")


def run_script(root, *extra):
    r = subprocess.run([sys.executable, SCRIPT, root] + list(extra),
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout)
        print(r.stderr)
        raise SystemExit(f"脚本执行失败: {extra}")
    return r.stdout


def make_case(tmp, name, rss_text=None, records=None):
    d = os.path.join(tmp, name)
    os.makedirs(os.path.join(d, "data"), exist_ok=True)
    if records is None:
        shutil.copy(ARTICLES, os.path.join(d, "data", "articles.json"))
    else:
        with open(os.path.join(d, "data", "articles.json"), "w",
                  encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=1)
    if rss_text is not None:
        with open(os.path.join(d, "rss.xml"), "w", encoding="utf-8",
                  newline="") as f:
            f.write(rss_text)
    return d


def split_raw(raw):
    items = ITEM_RE.findall(raw)
    head = raw[:raw.find("<item>")] if items else raw
    tail = raw[raw.rfind("</item>") + 7:] if items else ""
    return head, items, tail


def main():
    golden_raw = open(RSS, encoding="utf-8").read()
    g_head, g_items, g_tail = split_raw(golden_raw)
    records = json.load(open(ARTICLES, encoding="utf-8"))
    d14_slugs = [r["slug"] for r in records if r["date"] == "2026-10-14"]
    assert len(d14_slugs) == 3, f"10-14 文章应为 3 篇，实际 {len(d14_slugs)}"
    ok = True

    with tempfile.TemporaryDirectory() as tmp:
        # ---------- A) 幂等 ----------
        d = make_case(tmp, "case_a", rss_text=golden_raw)
        out = run_script(d)
        got = open(os.path.join(d, "rss.xml"), encoding="utf-8").read()
        same = got == golden_raw
        ok &= same
        print(f"[A] 幂等重跑逐字节一致: {'PASS' if same else 'FAIL'}")
        if not same:
            print("   ", out.strip().replace("\n", "\n    "))

        # ---------- B) 复刻 10-14 真实运行 ----------
        kept = [it for it in g_items
                if LINK_RE.search(it).group(1) not in set(d14_slugs)]
        assert len(kept) == 50, f"移除 10-14 后应剩 50 篇，实际 {len(kept)}"
        fakes = []
        for n in range(3):
            src = g_items[-1]
            old = LINK_RE.search(src).group(1)
            fakes.append(src.replace(old, f"ZZZ-Truncation-Probe-{n}.html"))
        pre_raw = g_head + "".join(kept + fakes) + g_tail
        d = make_case(tmp, "case_b", rss_text=pre_raw)
        out = run_script(d, "--date", "2026-10-14", "--now",
                         "2026-10-14 00:30:00")
        got = open(os.path.join(d, "rss.xml"), encoding="utf-8").read()
        same = got == golden_raw
        ok &= same
        print(f"[B] 复刻 10-14 运行逐字节一致: {'PASS' if same else 'FAIL'}")
        if not same:
            print("   ", out.strip().replace("\n", "\n    "))
            for i, (a, b) in enumerate(zip(got, golden_raw)):
                if a != b:
                    print(f"    首个差异 @ {i}:")
                    print("    got :", repr(got[max(0, i - 60):i + 60]))
                    print("    want:", repr(golden_raw[max(0, i - 60):i + 60]))
                    break
            else:
                print(f"    长度不同: got {len(got)} vs want {len(golden_raw)}")

        # ---------- C) 新文章冒烟（含全量转义字符） ----------
        probe = {
            "slug": "ZZZ-Escaping-Probe.html",
            "title": "转义探针 & < > \" ' 齐活",
            "desc": "desc: & < > \" ' 与中文混排",
            "date": "2026-10-15",
        }
        d = make_case(tmp, "case_c", rss_text=golden_raw, records=records + [probe])
        out = run_script(d, "--date", "2026-10-15", "--now",
                         "2026-10-15 00:45:00")
        got = open(os.path.join(d, "rss.xml"), encoding="utf-8").read()
        c_head, c_items, c_tail = split_raw(got)
        expected_item = (
            '<item><title>转义探针 &amp; &lt; &gt; &quot; &#x27; 齐活 - LongBiosci</title>'
            '<link>https://longbiosci.com/news/ZZZ-Escaping-Probe.html</link>'
            '<guid isPermaLink="true">https://longbiosci.com/news/ZZZ-Escaping-Probe.html</guid>'
            '<pubDate>Thu, 15 Oct 2026 00:00:00 +0000</pubDate>'
            '<description>desc: &amp; &lt; &gt; &quot; &#x27; 与中文混排</description></item>'
        )
        want_head = g_head.replace(
            "Wed, 14 Oct 2026 00:30:00 GMT", "Thu, 15 Oct 2026 00:45:00 GMT")
        expected = want_head + expected_item + "".join(g_items[:52]) + g_tail
        same = got == expected
        checks = {
            "逐字节等于手算期望": same,
            "item 总数 = 53": len(c_items) == 53,
            "探针置顶": c_items and c_items[0] == expected_item,
            "队尾丢弃最旧 1 篇": c_items[1:] == g_items[:52],
            "lastBuildDate 已刷新":
                "Thu, 15 Oct 2026 00:45:00 GMT" in got,
            "探针 pubDate 为 UTC 零点 +0000":
                "<pubDate>Thu, 15 Oct 2026 00:00:00 +0000</pubDate>" in got,
        }
        ok &= all(checks.values())
        print(f"[C] 新文章冒烟: {'PASS' if all(checks.values()) else 'FAIL'}")
        for k, v in checks.items():
            print(f"     {'✓' if v else '✗'} {k}")
        if not same:
            for i, (a, b) in enumerate(zip(got, expected)):
                if a != b:
                    print(f"    首个差异 @ {i}:")
                    print("    got :", repr(got[max(0, i - 60):i + 60]))
                    print("    want:", repr(expected[max(0, i - 60):i + 60]))
                    break
            else:
                print(f"    长度不同: got {len(got)} vs want {len(expected)}")

        # ---------- D) 边缘：无 rss.xml ----------
        d = make_case(tmp, "case_d")  # 只有 data/articles.json
        run_script(d, "--date", "2026-10-15")
        fresh = open(os.path.join(d, "rss.xml"), encoding="utf-8").read()
        run_script(d, "--date", "2026-10-14")
        grown = open(os.path.join(d, "rss.xml"), encoding="utf-8").read()
        g2_items = ITEM_RE.findall(grown)
        checks = {
            "空骨架无 item": "<item>" not in fresh,
            "骨架含 channel 元数据":
                "<language>zh-cn</language>" in fresh
                and "<atom:link" in fresh,
            "骨架以 </rss> 换行结尾": fresh.endswith("</rss>\n"),
            "补跑 10-14 后 3 篇": len(g2_items) == 3,
            "首篇为 Menopause（JSON 逆序）":
                g2_items and LINK_RE.search(g2_items[0]).group(1).startswith(
                    "Menopause-"),
            "末篇为 COSMOS":
                g2_items and LINK_RE.search(g2_items[-1]).group(1).startswith(
                    "COSMOS-"),
            "lastBuildDate 已刷新":
                "<lastBuildDate>Wed, 14 Oct 2026" in grown,
        }
        ok &= all(checks.values())
        print(f"[D] 空文件边缘: {'PASS' if all(checks.values()) else 'FAIL'}")
        for k, v in checks.items():
            print(f"     {'✓' if v else '✗'} {k}")

    # ---------- 收尾：真实仓库幂等确认 ----------
    saved = open(RSS, "rb").read()
    out = run_script(REPO)
    now_bytes = open(RSS, "rb").read()
    same = now_bytes == saved
    if not same:
        with open(RSS, "wb") as f:
            f.write(saved)
    ok &= same
    print(f"[E] 真实仓库默认日期逐字节不变: {'PASS' if same else 'FAIL'}")
    print("   ", out.strip().replace("\n", "\n    "))
    r = subprocess.run(["git", "diff", "--stat", "rss.xml"], cwd=REPO,
                       capture_output=True, text=True)
    clean = r.stdout.strip() == ""
    ok &= clean
    print(f"[E] git diff rss.xml 为空: {'PASS' if clean else 'FAIL'}")

    print("\n总结:", "全部通过 ✅" if ok else "存在失败项 ❌")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
