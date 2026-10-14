#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_inject_poster.py —— inject-poster.py 验收脚本（v1.0）

  A) 全量无操作：对完整副本（news/ 384 文件 + articles.json）运行 →
     所有文件 sha256 逐一不变（380 篇已有标签全部跳过，孤儿与
     index.html 不碰）——证明「有即跳过」幂等
  B) 黄金复刻·布局 A：摘除 COSMOS 的 poster 行 → 注入 → 必须逐字节
     还原原文件（锚点 = analytics 注释前）
  C) 黄金复刻·布局 B：摘除 Cardiolipin 的 poster 行 → 注入 → 必须逐字节
     还原原文件（该页 qr.js 在 analytics 之后，专验锚点不是 qr.js）
  D) 旧模板分支：摘除 Chronic 的裸 poster 行 → 注入 → 带属性标签落在
     </head> 之前（旧模板无 analytics 注释），属性值取自 JSON
  E) 孤儿安全：副本中 3 个孤儿 + news/index.html 在 A) 中已覆盖不变
全部用例在临时副本上进行，仓库文件不被改动。
"""
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile

PIPE = os.path.dirname(os.path.abspath(__file__))
_CAND = os.path.abspath(os.path.join(PIPE, "..", "repo_push"))  # 开发态
REPO = _CAND if os.path.isdir(os.path.join(_CAND, "data")) else os.path.abspath(os.path.join(PIPE, ".."))
SCRIPT = os.path.join(PIPE, "inject-poster.py")


def run(root):
    r = subprocess.run([sys.executable, SCRIPT, root],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout)
        print(r.stderr)
        raise SystemExit("inject-poster.py 执行失败")
    return r.stdout


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def snapshot(d):
    out = {}
    for f in sorted(os.listdir(d)):
        p = os.path.join(d, f)
        if os.path.isfile(p):
            out[f] = sha(p)
    return out


def strip_poster_line(text):
    """摘除 poster.js  script 行（含行尾换行），模拟注入前状态。"""
    m = re.search(r'<script src="/poster\.js"[^>]*></script>\n', text)
    assert m, "未找到 poster 行"
    return text[:m.start()] + text[m.end():]


def main():
    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        # ---------- A) 全量无操作 ----------
        site = os.path.join(tmp, "site")
        os.makedirs(os.path.join(site, "data"))
        shutil.copy(os.path.join(REPO, "data/articles.json"),
                    os.path.join(site, "data/articles.json"))
        shutil.copytree(os.path.join(REPO, "news"),
                        os.path.join(site, "news"))
        before = snapshot(os.path.join(site, "news"))
        out = run(site)
        after = snapshot(os.path.join(site, "news"))
        same = before == after
        ok &= same
        print(f"[A] 全量无操作（{len(before)} 个文件 sha256 全不变）: "
              f"{'PASS' if same else 'FAIL'}")
        print("   ", out.strip().splitlines()[-1])
        if not same:
            for k in before:
                if before[k] != after.get(k):
                    print("    变化:", k)

        # ---------- B) 布局 A 黄金复刻 ----------
        for label, slug in [("B", "COSMOS-Multivitamin-Epigenetic-Aging-"
                                  "Clocks-Nature-Medicine-2026.html"),
                            ("C", "Cardiolipin-ERRgamma-Muscle-Fiber-Switch-"
                                  "Nature-Aging-2026.html")]:
            p = os.path.join(site, "news", slug)
            original = open(p, "rb").read()
            text = original.decode("utf-8")
            with open(p, "w", encoding="utf-8", newline="") as f:
                f.write(strip_poster_line(text))
            run(site)
            rebuilt = open(p, "rb").read()
            same = rebuilt == original
            ok &= same
            print(f"[{label}] 摘除后注入逐字节还原 {slug[:40]}: "
                  f"{'PASS' if same else 'FAIL'}")
            if not same:
                for i, (x, y) in enumerate(zip(rebuilt, original)):
                    if x != y:
                        lo = max(0, i - 60)
                        print(f"    差异 @ {i}:")
                        print("    got :", repr(rebuilt[lo:i + 60]))
                        print("    want:", repr(original[lo:i + 60]))
                        break
                else:
                    print(f"    长度不同: {len(rebuilt)} vs {len(original)}")

        # ---------- D) 旧模板（无 analytics）分支 ----------
        slug = ("Chronic-Senolytic-Treatment-or-Aerobic-Exercise-Reduce-"
                "Senescence-Improve-Myocardial-Function.html")
        p = os.path.join(site, "news", slug)
        original = open(p, "rb").read()
        text = original.decode("utf-8")
        with open(p, "w", encoding="utf-8", newline="") as f:
            f.write(strip_poster_line(text))
        run(site)
        rebuilt = open(p, encoding="utf-8").read()
        m = re.search(r'(<script src="/poster\.js"[^>]*></script>)\n(</head>)',
                      rebuilt)
        checks = {
            "带属性标签落在 </head> 之前": bool(m),
            "属性值取自 JSON（B/细胞衰老）":
                m and m.group(1) == ('<script src="/poster.js" defer '
                                     'data-tier="B" data-topic="细胞衰老">'
                                     '</script>'),
            "qr.js 仍在标签之前":
                rebuilt.find("<script src=\"/qr.js\"") < rebuilt.find(
                    "<script src=\"/poster.js\""),
        }
        ok &= all(checks.values())
        print(f"[D] 旧模板无 analytics 分支: "
              f"{'PASS' if all(checks.values()) else 'FAIL'}")
        for k, v in checks.items():
            print(f"     {'✓' if v else '✗'} {k}")
        # 恢复原文件供 E 使用
        with open(p, "wb") as f:
            f.write(original)

        # ---------- E) 再跑一次全量无操作（B/C/D 改动已还原）----------
        before2 = snapshot(os.path.join(site, "news"))
        run(site)
        after2 = snapshot(os.path.join(site, "news"))
        same = before2 == after2 and before2 == before
        ok &= same
        print(f"[E] 收尾复跑仍全量不变: {'PASS' if same else 'FAIL'}")

    print("\n总结:", "全部通过 ✅" if ok else "存在失败项 ❌")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
