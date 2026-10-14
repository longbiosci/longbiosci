#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
add-rss-today-run.py —— RSS 订阅源更新器（逆向重写版 v1.0）

复刻来源：线上 rss.xml（2026-10-14 基线，53 个 item）+ data/articles.json。
规则（自基线逆向得出）：
  - 数据源：data/articles.json，取 date == 运行日期（UTC）且尚未进 RSS 的文章
  - 新文章按 articles.json 顺序逐個 insert(0)（队首插入），因此当日批次在
    feed 顶部呈 JSON 逆序。实证：10-14 批次 JSON 序为
    COSMOS → King-Penguin → Menopause，线上 RSS 序为
    Menopause → King-Penguin → COSMOS，与「按 JSON 序逐個 insert(0)」完全吻合
  - item 结构（单行、无缩进、item 之间无分隔符，与基线一致）：
    <item><title>{title} - LongBiosci</title><link>{url}</link>
    <guid isPermaLink="true">{url}</guid><pubDate>{RFC822}</pubDate>
    <description>{desc}</description></item>
    其中 url = https://longbiosci.com/news/{slug}（slug 含 .html）
  - title/desc 走 html.escape(quote=True)（实证基线中 " 渲染为 &quot;）
  - pubDate = 文章 date 的 UTC 零点，后缀 +0000（Wed, 14 Oct 2026 00:00:00 +0000）；
    老 item 的 GMT 后缀为历史痕迹，原样保留、一律不重写
  - 容量上限 53 个 item，超出部分从队尾丢弃。实证：10-14 运行
    前置 53 篇 + 新增 3 篇 = 56 篇 → 截断回 53 篇
  - lastBuildDate 仅在真有新增 item 时更新为运行时刻（GMT 后缀）；
    无新增时输出与输入逐字节一致（幂等，避免每日空跑产生噪声 diff）
  - desc 不做截断（实证 53 个 item 的 desc 与 articles.json 逐条 100% 相等，
    截断只发生在 news 列表页，RSS 保留全文）
  - 已知偏差：原管线当日多批次时的内部次序疑似按文章文件落地次序
    （mtime/到达序）而非 articles.json 次序——10-13 单日 18 篇呈 6 组×3 篇、
    组内既非字母序也非逆序，任何基于 JSON 次序的规则均无法复现。该信息
    （落地次序）已随原机器不可恢复。本实现按 JSON 次序，在标准运维模型
    （每日单次运行）下与线上表现一致；多批次同日只会影响同一 pubDate
    块内的次序，不影响内容与正确性
用法：add-rss-today-run.py [root] [--date YYYY-MM-DD] [--now "YYYY-MM-DD HH:MM:SS"]
  root   仓库根目录（默认当前目录）
  --date 指定「今日」日期（默认 UTC 今天），用于补跑/验收
  --now  指定 lastBuildDate 时刻（默认当前 UTC 时间），用于确定性复现
"""
import html
import json
import os
import re
import sys
from datetime import datetime, timezone

MAX_ITEMS = 53  # feed 容量上限（自基线实测）
SITE = "https://longbiosci.com"

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

ITEM_RE = re.compile(r"<item>.*?</item>", re.S)
LINK_RE = re.compile(r"<link>" + re.escape(SITE) + r"/news/([^<]+)</link>")
LASTBUILD_RE = re.compile(r"(<lastBuildDate>)[^<]*(</lastBuildDate>)")

# rss.xml 缺失时的默认骨架（channel 元数据与线上一致）
DEFAULT_HEAD = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
    '  <channel>\n'
    '    <title>LongBiosci - 长寿科技资讯</title>\n'
    '    <link>https://longbiosci.com</link>\n'
    '    <description>最新生物医药与长寿科技研究资讯</description>\n'
    '    <language>zh-cn</language>\n'
    '    <lastBuildDate>{lastbuild}</lastBuildDate>\n'
    '    <atom:link href="https://longbiosci.com/rss.xml" rel="self" type="application/rss+xml"/>\n'
)
DEFAULT_TAIL = '\n  </channel>\n</rss>\n'


def rfc822(dt, suffix):
    """格式化 RFC 822 日期（英文周几/月份写死，避免 locale 干扰）。"""
    return (f"{WEEKDAYS[dt.weekday()]}, {dt.day:02d} {MONTHS[dt.month - 1]} "
            f"{dt.year} {dt.hour:02d}:{dt.minute:02d}:{dt.second:02d} {suffix}")


def esc(s):
    return html.escape(s or "", quote=True)


def item_xml(rec):
    """由 articles.json 记录生成 RSS item（单行）。"""
    url = f"{SITE}/news/{rec['slug']}"
    pub = datetime.strptime(rec["date"], "%Y-%m-%d")
    return (f"<item><title>{esc(rec['title'])} - LongBiosci</title>"
            f"<link>{url}</link>"
            f'<guid isPermaLink="true">{url}</guid>'
            f"<pubDate>{rfc822(pub, '+0000')}</pubDate>"
            f"<description>{esc(rec['desc'])}</description></item>")


def item_slug(item):
    m = LINK_RE.search(item)
    return m.group(1) if m else None


def split_rss(raw):
    """拆成 (head, items, tail)；items 为原始字符串列表，原样保留。"""
    m = ITEM_RE.search(raw)
    if not m:
        # 无 item：按 </channel> 拆分，保持文件其余部分原样
        idx = raw.find("  </channel>")
        if idx != -1:
            return raw[:idx], [], raw[idx:]
        return raw, [], DEFAULT_TAIL
    items = ITEM_RE.findall(raw)
    last_end = raw.rfind("</item>") + len("</item>")
    return raw[:m.start()], items, raw[last_end:]


def main():
    args = sys.argv[1:]
    root = "."
    run_date = datetime.now(timezone.utc).date()
    now = datetime.now(timezone.utc).replace(microsecond=0)
    i = 0
    while i < len(args):
        if args[i] == "--date":
            run_date = datetime.strptime(args[i + 1], "%Y-%m-%d").date()
            i += 2
        elif args[i] == "--now":
            now = datetime.strptime(args[i + 1], "%Y-%m-%d %H:%M:%S").replace(
                tzinfo=timezone.utc)
            i += 2
        else:
            root = args[i]
            i += 1

    rss_path = os.path.join(root, "rss.xml")
    if os.path.exists(rss_path):
        with open(rss_path, encoding="utf-8") as f:
            raw = f.read()
    else:
        raw = DEFAULT_HEAD.replace("{lastbuild}", rfc822(now, "GMT")) + DEFAULT_TAIL

    head, items, tail = split_rss(raw)

    with open(os.path.join(root, "data/articles.json"), encoding="utf-8") as f:
        records = json.load(f)

    existing = {item_slug(it) for it in items}
    date_str = run_date.isoformat()
    new_recs = [r for r in records
                if r.get("date") == date_str and r["slug"] not in existing]

    # 按 articles.json 顺序逐個 insert(0) → 当日块呈 JSON 逆序（与 10-14 实证一致）
    for rec in new_recs:
        items.insert(0, item_xml(rec))

    if new_recs:
        items = items[:MAX_ITEMS]
        head = LASTBUILD_RE.sub(
            lambda m: m.group(1) + rfc822(now, "GMT") + m.group(2), head)
        names = "、".join(r["slug"][:40] for r in new_recs)
        print(f"  rss.xml: 新增 {len(new_recs)} 篇（{names}），共 {len(items)} 篇")
    else:
        print(f"  rss.xml: {date_str} 无新文章，未变动")

    out = head + "".join(items) + tail
    with open(rss_path, "w", encoding="utf-8", newline="") as f:
        f.write(out)
    print(f"RSS 更新完成: {len(items)} 个 item（上限 {MAX_ITEMS}）")


if __name__ == "__main__":
    main()
