#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_home_topics.py —— gen-home.py + gen-topic-pages.py 验收脚本（v1.0）

在临时副本上生成，与仓库线上基线逐字节比对：
  A) gen-home.py    → index.html
  B) gen-topic-pages.py → topics/ 全部 20 个文件（8 专题页 + 12 分页页 + 索引页）
任一不一致即打印首个差异位置与上下文。仓库文件不被改动。
"""
import filecmp
import os
import shutil
import subprocess
import sys
import tempfile

PIPE = os.path.dirname(os.path.abspath(__file__))
_CAND = os.path.abspath(os.path.join(PIPE, "..", "repo_push"))  # 开发态
REPO = _CAND if os.path.isdir(os.path.join(_CAND, "data")) else os.path.abspath(os.path.join(PIPE, ".."))


def run(script, root):
    r = subprocess.run([sys.executable, os.path.join(PIPE, script), root],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout)
        print(r.stderr)
        raise SystemExit(f"{script} 执行失败")
    return r.stdout


def diff_report(path_a, path_b, label):
    """逐字节比对，打印首个差异。"""
    a = open(path_a, "rb").read()
    b = open(path_b, "rb").read()
    if a == b:
        return True
    print(f"  [FAIL] {label}: {len(a)} B vs {len(b)} B")
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            lo = max(0, i - 80)
            print(f"    首个差异 @ {i}:")
            print("    got :", repr(a[lo:i + 80]))
            print("    want:", repr(b[lo:i + 80]))
            return False
    print(f"    前缀一致，长度不同（got 多/少 {abs(len(a) - len(b))} B）")
    print("    got  tail:", repr(a[-120:]))
    print("    want tail:", repr(b[-120:]))
    return False


def main():
    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        case = os.path.join(tmp, "site")
        os.makedirs(os.path.join(case, "data"))
        shutil.copy(os.path.join(REPO, "data/articles.json"),
                    os.path.join(case, "data/articles.json"))

        # ---- A) 首页 ----
        out = run("gen-home.py", case)
        print(out.strip())
        ok &= diff_report(os.path.join(case, "index.html"),
                          os.path.join(REPO, "index.html"), "index.html")
        print(f"[A] gen-home.py 首页逐字节一致: {'PASS' if ok else 'FAIL'}")

        # ---- B) 专题页 + 索引页 ----
        out = run("gen-topic-pages.py", case)
        print(out.strip())
        names = sorted(os.listdir(os.path.join(REPO, "topics")))
        names = [n for n in names if n.endswith(".html")]
        got_names = sorted(os.listdir(os.path.join(case, "topics")))
        if got_names != names:
            ok = False
            print(f"  [FAIL] 文件集合不同: 多 {set(got_names) - set(names)} "
                  f"少 {set(names) - set(got_names)}")
        bad = []
        for n in names:
            a = os.path.join(case, "topics", n)
            b = os.path.join(REPO, "topics", n)
            if not os.path.exists(a) or not diff_report(a, b, f"topics/{n}"):
                bad.append(n)
        ok &= not bad
        print(f"[B] gen-topic-pages.py {len(names)} 个文件逐字节一致: "
              f"{'PASS' if not bad else 'FAIL ' + str(bad)}")

    print("\n总结:", "全部通过 ✅" if ok else "存在失败项 ❌")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
