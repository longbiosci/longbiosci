#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test-poster-ui.py —— poster.js 弹层交互回归测试（无头 Chromium）

覆盖：按钮挂载 → canvas 绘制 → 复制链接（含剪贴板内容与 tip 还原）
→ 下载 PNG（文件头/体积）→ 分享三条路径（文件分享 / 降级分享链接 /
AbortError 静默）→ Esc 关闭与重开幂等。

用法：
    cd <仓库根>  && python3 -m http.server 8931 &        # 本地静态服务
    python3 scripts/test-poster-ui.py                    # 默认测示例文章
    python3 scripts/test-poster-ui.py <URL>              # 指定文章页 URL

依赖：playwright（pip install playwright && playwright install chromium）。
不依赖仓库内任何模块，也不写入任何文件——纯只读验证。
注意：无头 Chromium 默认无 navigator.share，「分享」按钮不渲染属预期；
分享路径由调用方以 add_init_script 打桩验证（见 main 内 page2/page3 模式，
    2026-10-17 首次落地时已用桩验证过文件分享/降级/取消三条路径）。
"""
import os
import sys

from playwright.sync_api import sync_playwright
URL = sys.argv[1] if len(sys.argv) > 1 else \
    "http://127.0.0.1:8931/news/Centenarian-Gut-Microbiome-Secondary-Bile-Acids-NatureAging-2026.html"
fails = []

def check(name, cond, detail=""):
    print(("  ✅ " if cond else "  ❌ ") + name + (f"  [{detail}]" if detail else ""))
    if not cond:
        fails.append(name)

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1280, "height": 900},
                        permissions=["clipboard-read", "clipboard-write"])
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.goto(URL, wait_until="networkidle")

    print("== 1. 挂载 ==")
    check("生成海报按钮已挂载", page.locator(".lb-poster-btn").count() == 1)
    check("无 JS 报错", not errors, "; ".join(errors[:2]))

    print("== 2. 打开弹层 ==")
    page.locator(".lb-poster-btn").click()
    page.wait_for_timeout(600)
    check("弹层可见", page.locator(".lb-poster-modal.on").count() == 1)
    check("canvas 存在", page.locator("#lbPosterCanvas").count() == 1)

    dims = page.evaluate("""() => {
        var c = document.querySelector('#lbPosterCanvas');
        var ctx = c.getContext('2d');
        var d = ctx.getImageData(0, 0, c.width, c.height).data;
        var nonWhite = 0;
        for (var i = 0; i < d.length; i += 4000) { if (d[i] < 245 || d[i+1] < 245 || d[i+2] < 245) nonWhite++; }
        return {w: c.width, h: c.height, nonWhite: nonWhite};
    }""")
    check("canvas 已绘制（2倍图宽 2160）", dims["w"] == 2160, f"w={dims['w']}")
    check("canvas 高度在 1080–2200 区间", 2160 <= dims["h"] <= 4400, f"h={dims['h']}")
    check("canvas 非空白（有内容像素）", dims["nonWhite"] > 500, f"nonWhite={dims['nonWhite']}")

    print("== 3. 按钮组 ==")
    check("下载 PNG 按钮", page.locator(".lb-poster-dl").count() == 1)
    check("复制链接按钮", page.locator(".lb-poster-copy").count() == 1)
    has_share_js = page.evaluate("typeof navigator.share !== 'undefined'")
    share_btn = page.locator(".lb-poster-share").count()
    check("分享按钮按 navigator.share 支持度渐进渲染",
          share_btn == (1 if has_share_js else 0),
          f"navigator.share={has_share_js}, 按钮数={share_btn}")

    print("== 4. 复制链接 ==")
    page.locator(".lb-poster-copy").click()
    page.wait_for_timeout(400)
    tip = page.locator(".lb-poster-tip").inner_text()
    clip = page.evaluate("navigator.clipboard.readText()")
    check("tip 反馈「链接已复制」", "已复制" in tip, tip)
    check("剪贴板内容为 canonical URL",
          clip == "https://longbiosci.com/news/Centenarian-Gut-Microbiome-Secondary-Bile-Acids-NatureAging-2026.html",
          clip)
    page.wait_for_timeout(2200)
    check("tip 2.4s 后还原", "长按图片" in page.locator(".lb-poster-tip").inner_text())

    print("== 5. 下载 PNG ==")
    with page.expect_download() as dl_info:
        page.locator(".lb-poster-dl").click()
    dl = dl_info.value
    path = dl.path()
    import os
    size = os.path.getsize(path)
    check("下载文件为 .png", dl.suggested_filename.endswith(".png"), dl.suggested_filename)
    check("PNG 体积合理（>50KB）", size > 50_000, f"{size/1024:.0f} KB")
    with open(path, "rb") as f:
        magic = f.read(8)
    check("PNG 文件头正确", magic == b"\x89PNG\r\n\x1a\n", str(magic))

    print("== 6. 分享按钮存在时的行为（桩验证） ==")
    if share_btn == 1:
        page.evaluate("""() => {
            window.__shareCalls = [];
            navigator.share = (d) => { window.__shareCalls.push(d); return Promise.resolve(); };
            navigator.canShare = (d) => !!(d && d.files);
        }""")
        page.locator(".lb-poster-share").click()
        page.wait_for_timeout(500)
        calls = page.evaluate("window.__shareCalls")
        check("点击分享调用了 navigator.share", len(calls) == 1)
        if calls:
            d = calls[0]
            check("分享内容含 PNG 文件", "files" in d and d["files"], str(list(d.keys())))
            check("分享文件类型为 image/png",
                  d.get("files") and d["files"][0].get("type") == "image/png")
            check("分享标题为文章标题", "LongBiosci" == d.get("title"), str(d.get("title")))

    print("== 7. 关闭与重开（幂等） ==")
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)
    check("Esc 关闭弹层", page.locator(".lb-poster-modal.on").count() == 0)
    page.locator(".lb-poster-btn").click()
    page.wait_for_timeout(500)
    check("重开只画一次（无第二个按钮）", page.locator(".lb-poster-btn").count() == 1
          and page.locator(".lb-poster-modal").count() == 1)
    check("重开无 JS 报错", not errors, "; ".join(errors[:2]))

    b.close()

print()
if fails:
    print(f"❌ {len(fails)} 项未通过: {fails}")
    sys.exit(1)
print("✅ 全部通过")
