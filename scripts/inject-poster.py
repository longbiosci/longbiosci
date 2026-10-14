#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
inject-poster.py —— 文章页海报脚本注入器（逆向重写版 v1.0）

复刻来源：线上 news/ 全部 380 篇文章页（2026-10-14 基线）。
规则（自基线逆向得出）：
  - 数据驱动：遍历 data/articles.json 的每条记录，处理 news/{slug}；
    news/ 下不在 JSON 里的文件（3 个孤儿旧稿 + index.html）一律不碰
    （实证：它们没有任何 poster/qr/poster.css 痕迹）
  - 幂等：文件中已含 <script src="/poster.js" 即跳过，绝不重写已有标签
    （实证：10 篇 10-13 旧模板文章的裸标签、1 篇属性与 JSON 不一致的
    Centenarian 均原样保留——原注入器显然也是「有即跳过」）
  - 注入标签：<script src="/poster.js" defer data-tier="{evidence}"
    data-topic="{topic}"></script>，evidence/topic 取自 JSON 记录
  - 插入锚点：analytics 注释（<!-- longbiosci:analytics）之前；
    无该注释则 </head> 之前；两者都没有则追加到文末（防御分支）
    实证三种 head 布局全部吻合：
      布局 A（367 篇）: poster.css → qr.js → [poster] → analytics → umami
      布局 B（3 篇）  : poster.css → [poster] → analytics → qr.js（无 umami）
      布局 C（10 篇） : poster.css → qr.js → [poster] → </head>（旧模板）
  - qr.js / poster.css 是文章模板的静态部分（位置随模板版本漂移），
    不由本脚本注入；全站仅 news/ 文章页有此体系
  - 已知偏差：10 篇旧模板文章的裸标签是旧版注入器的历史遗留，
    按「有即跳过」原则原样保留；如需统一为带属性格式需单独评估
    （会改动线上页面，记入运营待办）
"""
import json
import os
import sys

POSTER_RE = "<script src=\"/poster.js\""
ANALYTICS_ANCHOR = "<!-- longbiosci:analytics"


def inject(root, verbose=True):
    with open(os.path.join(root, "data/articles.json"), encoding="utf-8") as f:
        records = json.load(f)

    injected, skipped, missing = 0, 0, []
    for rec in records:
        path = os.path.join(root, "news", rec["slug"])
        if not os.path.exists(path):
            missing.append(rec["slug"])
            continue
        with open(path, encoding="utf-8") as f:
            html_text = f.read()
        if POSTER_RE in html_text:
            skipped += 1
            continue
        tag = (f'<script src="/poster.js" defer '
               f'data-tier="{rec["evidence"]}" '
               f'data-topic="{rec["topic"]}"></script>')
        idx = html_text.find(ANALYTICS_ANCHOR)
        if idx != -1:
            new_text = html_text[:idx] + tag + "\n" + html_text[idx:]
        else:
            idx = html_text.find("</head>")
            if idx != -1:
                new_text = html_text[:idx] + tag + "\n" + html_text[idx:]
            else:
                new_text = html_text + tag + "\n"
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(new_text)
        injected += 1
        if verbose:
            print(f"  + news/{rec['slug']}")

    if verbose:
        print(f"海报注入完成: 新增 {injected} 篇，已存在跳过 {skipped} 篇"
              + (f"，缺失文件 {len(missing)} 个: {missing}" if missing else ""))
    return injected, skipped, missing


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    inject(root)


if __name__ == "__main__":
    main()
