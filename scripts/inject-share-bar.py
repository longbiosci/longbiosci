#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量给存量 news/*.html 注入转发分享条（复制链接 + 二维码）。

多锚点回退：article-footer → </article> → <footer site-footer> → </main> → </body>
样式兜底：未引用 /style.css 的页，分享条自带内联 <style>。
幂等：已含 share-bar 的页面跳过。

只处理**文章页**，三类文件必须排除（2026-10-23 修）
-----------------------------------------------
glob 的是 news/*.html，可这目录里还住着两种非文章页：
  · news/index.html      文章列表页。「分享给好友」分享一份列表、二维码指向列表，
                         语义就不对；更麻烦的是 gen-news-index 每轮重写它，
                         本脚本每轮再注入一次 —— 两个生成器对同一个文件来回拉锯，
                         该页内容每轮都变，sitemap 的 lastmod 永远停在当天。
                         （这正是在 rebuild-sitemap 改内容指纹后暴露出来的：
                          每轮都有一条「内容有变」，追下去才发现是自家脚本互踩。）
  · news/<slug>.html 的迁移守卫页（带 lb-redirect-stub）
                         页面本身在说「这篇文章已迁移」，底下一个按钮让人
                         分享这个已失效的地址 —— 帮读者把死链传播出去。
故：basename == index.html 跳过；含 STUB_MARK 跳过。

用法：python3 inject-share-bar.py [repo_root]
"""
import glob
import os
import sys

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")

SHARE_BODY = """<section class="share-bar" aria-label="分享给好友">
            <span class="share-bar-title">分享给好友</span>
            <div class="share-bar-actions">
                <button type="button" class="share-copy-btn">复制链接</button>
                <span class="share-tip" hidden>已复制 &#10003;</span>
            </div>
            <div class="share-qr">
                <div class="share-qr-code" aria-hidden="true"></div>
                <span class="share-qr-note">微信扫码，手机直接打开</span>
            </div>
        </section>
"""

INLINE_CSS = (
    "<style>.share-bar{display:flex;flex-wrap:wrap;align-items:center;gap:16px;"
    "margin:28px 0 0;padding:14px 18px;background:#f8f9fc;border:1px solid #e6e8ef;"
    "border-radius:12px}.share-bar-title{font-weight:600;color:#111;font-size:15px}"
    ".share-bar-actions{display:flex;align-items:center;gap:12px}"
    ".share-copy-btn{border:0;cursor:pointer;background:#0f3460;color:#fff;font-size:14px;"
    "padding:9px 18px;border-radius:8px;min-height:40px;font-family:inherit}"
    ".share-tip{color:#00A86B;font-size:13px;font-weight:600}"
    ".share-qr{display:flex;align-items:center;gap:12px;margin-left:auto}"
    ".share-qr-code img{display:block;width:92px;height:92px;border-radius:8px;background:#fff;"
    "padding:4px;border:1px solid #e6e8ef}.share-qr-note{font-size:12px;color:#666;"
    "max-width:9em;line-height:1.6}"
    "@media(max-width:600px){.share-bar{flex-direction:column;align-items:flex-start;gap:12px}"
    ".share-qr{margin-left:0}}</style>"
)

SCRIPTS = (
    '<script src="/qrcode.min.js"></script>\n'
    '<script src="/share.js" defer></script>'
)

# 迁移守卫页的自证标记（与 gen-redirects.py / check-links.py 同名同义）
STUB_MARK = "lb-redirect-stub"

ANCHORS = [
    '<footer class="article-footer">',
    "</article>",
    '<footer class="site-footer">',
    "</main>",
    "</body>",
]


def inject(html):
    if "share-bar" in html:
        return None  # 已注入，跳过
    share = INLINE_CSS + SHARE_BODY if "style.css" not in html else SHARE_BODY
    for a in ANCHORS:
        if a in html:
            html = html.replace(a, share + "\n" + a, 1)
            if SCRIPTS.splitlines()[0] not in html:
                html = html.replace("</body>", SCRIPTS + "\n</body>", 1)
            return html
    return None  # 完全无锚点


def main():
    paths = sorted(glob.glob(os.path.join(ROOT, "news", "*.html")))
    done = skipped = noanchor = notarticle = 0
    for p in paths:
        if os.path.basename(p) == "index.html":
            notarticle += 1
            continue
        html = open(p, encoding="utf-8").read()
        if STUB_MARK in html:
            notarticle += 1
            continue
        if "share-bar" in html:
            skipped += 1
            continue
        out = inject(html)
        if out is None:
            noanchor += 1
            print("WARN 无锚点跳过:", os.path.basename(p))
            continue
        open(p, "w", encoding="utf-8").write(out)
        done += 1
    print(
        f"[share-bar] 本轮注入 {done} 篇，已存在跳过 {skipped} 篇，无锚点 {noanchor} 篇，"
        f"非文章页跳过 {notarticle} 个（列表页 / 迁移守卫页），共 {len(paths)} 个文件"
    )


if __name__ == "__main__":
    main()
