#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""导航改造后的多视口 × 多页面实测（本机 Django-free：用 http.server 起静态服务）

检查项：
  1. 11 个导航入口全部可见且完全落在视口内（不被裁切）
  2. 页面无横向溢出
  3. aria-current 高亮指向正确栏目
  4. 桌面端仍是单行 + sticky；移动端行数与 header 高度
  5. 无 JS 控制台错误、无嵌套/空锚点
"""
import subprocess
import sys
import time

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:%s" % (sys.argv[2] if len(sys.argv) > 2 else "8801")
ROOT = sys.argv[1]

# 页面 -> 期望高亮的 href
PAGES = [
    ("/index.html", "/"),
    ("/news/index.html", "/news/"),
    ("/news/7-Ketocholesterol-Derivatives-Pathophysiology.html", "/news/"),
    ("/topics/index.html", "/topics/"),
    ("/guide/index.html", "/guide/"),
    ("/guide/mitochondria-autophagy.html", "/guide/"),
    ("/research/index.html", "/research/"),
    ("/senolytic.html", "/research/"),
    ("/evidence/index.html", "/evidence/"),
    ("/trials.html", "/trials.html"),
    ("/companies/index.html", "/companies/"),
    ("/search.html", "/search.html"),
    ("/daily/index.html", "/daily/"),
    ("/about/index.html", "/about/"),
]
VIEWPORTS = [(320, 640), (375, 667), (390, 844), (768, 1024), (1024, 768), (1440, 900)]

JS = """() => {
  const nav = document.querySelector('.main-nav');
  const hdr = document.querySelector('.site-header');
  const as  = [...document.querySelectorAll('.main-nav a')];
  const rows = [];
  as.forEach(a => {
    const b = a.getBoundingClientRect();
    let row = rows.find(r => Math.abs(r.top - b.top) <= 6);
    if (!row) { row = {top: b.top, items: []}; rows.push(row); }
    row.items.push((a.getAttribute('aria-label') || a.textContent).trim());
  });
  const off = as.filter(a => {
    const b = a.getBoundingClientRect();
    return b.left < -0.5 || b.right > window.innerWidth + 0.5 || b.width < 1 || b.height < 1;
  }).map(a => a.getAttribute('aria-label') || a.textContent);
  const cur = [...document.querySelectorAll('.main-nav a[aria-current="page"]')]
              .map(a => a.getAttribute('href'));
  return {
    count: as.length,
    nRows: rows.length,
    rows: rows.sort((a,b)=>a.top-b.top).map(r => r.items.join(' | ')),
    off,
    cur,
    headerH: Math.round(hdr.getBoundingClientRect().height),
    headerPos: getComputedStyle(hdr).position,
    hScroll: document.documentElement.scrollWidth - window.innerWidth,
    nestedA: document.querySelectorAll('a a').length,
    emptyA: [...document.querySelectorAll('a')].filter(a => !a.textContent.trim() && !a.querySelector('img,svg')).length,
  };
}"""

srv = subprocess.Popen([sys.executable, "-m", "http.server", sys.argv[2] if len(sys.argv) > 2 else "8801"],
                       cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1.2)
fail = 0
total = 0
try:
    with sync_playwright() as pw:
        br = pw.chromium.launch(args=["--no-sandbox"])
        for w, h in VIEWPORTS:
            pg = br.new_page(viewport={"width": w, "height": h})
            errs = []
            pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
            pg.on("pageerror", lambda e: errs.append(str(e)))
            print("=" * 92)
            print("视口 %dx%d" % (w, h))
            print("=" * 92)
            for url, want_cur in PAGES:
                total += 1
                pg.goto(BASE + url, wait_until="domcontentloaded")
                r = pg.evaluate(JS)
                bad = []
                if r["count"] != 11:
                    bad.append("入口数 %d≠11" % r["count"])
                if r["off"]:
                    bad.append("被裁切:%s" % ",".join(r["off"]))
                if r["hScroll"] > 0:
                    bad.append("横向溢出 %dpx" % r["hScroll"])
                if r["cur"] != [want_cur]:
                    bad.append("高亮 %s 应为 %s" % (r["cur"], want_cur))
                if r["nestedA"]:
                    bad.append("嵌套锚点 %d" % r["nestedA"])
                if r["emptyA"]:
                    bad.append("空锚点 %d" % r["emptyA"])
                if errs:
                    bad.append("JS错误 %s" % errs[:1])
                # 布局约束
                if w >= 1024 and r["nRows"] != 1:
                    bad.append("桌面 %d 行(应1)" % r["nRows"])
                if w >= 1024 and r["headerPos"] != "sticky":
                    bad.append("桌面未吸顶")
                errs.clear()
                status = "OK " if not bad else "FAIL"
                if bad:
                    fail += 1
                print("  [%s] %-58s nav=%2d 行=%d header=%3dpx %s"
                      % (status, url, r["count"], r["nRows"], r["headerH"], r["headerPos"]))
                if bad:
                    for b in bad:
                        print("         !! " + b)
            pg.close()
        br.close()
finally:
    srv.terminate()

print("\n" + "=" * 92)
print("总用例 %d，失败 %d" % (total, fail))
sys.exit(1 if fail else 0)
