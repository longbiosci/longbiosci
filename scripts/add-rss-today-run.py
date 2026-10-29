#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
add-rss-today-run.py —— RSS 订阅源更新器（逆向重写版 v1.0）

复刻来源：线上 rss.xml（2026-10-14 基线，53 个 item）+ data/articles.json。
规则（自基线逆向得出）：
  - 数据源：data/articles.json，取 date == 运行日期（**本地 UTC+8**，与文章
    date 字段同口径）且尚未进 RSS 的文章。
    ⚠️ 这里曾经按 UTC 取「今天」：站点文章的 date 是本地日期，而管线
    在北京时间 08:00–24:00 之间跑时 UTC 仍是前一天 → 当天新写的文章
    永远判不进「今日」，只能靠手工 `--date` 补跑；更糟的是下一轮 UTC
    翻页后又把前一天的文章当新的加进来，53 条上限从队尾挤掉 5 条，
    feed 窗口每跑一次滑一格（2026-10-16 收尾自检 [B] 项因此报 FAIL）。
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
  --date 指定「今日」日期（默认本地 UTC+8 今天），用于补跑/验收
  --now  指定 lastBuildDate 时刻（默认当前 UTC 时间），用于确定性复现
"""
import html
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

# 站点文章的 date 字段写的是本地日期（UTC+8）。「今天」必须与之同口径，
# 否则每天大半时间里的产出都进不了 feed（详见文件头说明）。
LOCAL_TZ = timezone(timedelta(hours=8))

MAX_ITEMS = 53  # feed 容量上限（自基线实测）
SITE = "https://longbiosci.com"
# P2 #12（2026-10-29 晨间班）：RSS 补 dc:creator。
# 站点所有条目均由本站编辑部撰写，无外部作者元数据可回填，
# 故用统一署名，让订阅阅读器不再显示空白作者。
DC_CREATOR = "LongBiosci 编辑部"
DC_NS = 'xmlns:dc="http://purl.org/dc/elements/1.1/"'

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

ITEM_RE = re.compile(r"<item>.*?</item>", re.S)
LINK_RE = re.compile(r"<link>" + re.escape(SITE) + r"/news/([^<]+)</link>")
LASTBUILD_RE = re.compile(r"(<lastBuildDate>)[^<]*(</lastBuildDate>)")

# rss.xml 缺失时的默认骨架（channel 元数据与线上一致）
DEFAULT_HEAD = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" ' + DC_NS + '>\n'
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
            f"<dc:creator>{esc(DC_CREATOR)}</dc:creator>"
            f"<description>{esc(rec['desc'])}</description></item>")


def ensure_dc_ns(head):
    """给既有 rss.xml 的 <rss> 根元素补 dc 命名空间（幂等）。

    线上 rss.xml 是 2026-10-29 之前生成的，根元素只有 xmlns:atom；
    DEFAULT_HEAD 只在文件缺失时才生效，跑一万次管线也补不上存量文件的
    命名空间。没有 xmlns:dc 却写 <dc:creator> 属于未声明前缀，
    严格校验器会直接判 feed 非法 —— 所以补齐必须落在 head 上，且幂等。
    """
    if DC_NS.split("=")[0] in head:
        return head
    return re.sub(r"<rss\s", lambda m: m.group(0), head, count=1).replace(
        "<rss ", "<rss " + DC_NS + " ", 1)


def ensure_dc_creator(item):
    """给单个 item 补 <dc:creator>（幂等，已有则原样返回）。

    插在 <pubDate> 之后、<description> 之前，与 item_xml() 的字段序一致，
    保证「存量 item 迁移后」与「新建 item」的字节结构完全对齐，
    下次跑管线不会产生只因字段顺序不同而产生的 diff。
    """
    if "<dc:creator>" in item:
        return item
    return re.sub(r"(</pubDate>)", r"\1<dc:creator>" + DC_CREATOR + "</dc:creator>",
                  item, count=1)


def item_slug(item):
    m = LINK_RE.search(item)
    return m.group(1) if m else None


def new_item_sep(items):
    """从既有 item 的尾部推断「item 之间的间隔符」（如 "\\r\\n"），
    供新建 item 复用，避免新条目与后一条粘在同一行。
    推断不出时回退到 "\\n"——至少不会粘连。"""
    for it in items:
        m = re.search(r"</item>(\s*)\Z", it)
        if m and m.group(1):
            return m.group(1)
    return "\n"


def split_rss(raw):
    """拆成 (head, items, tail)；items 为原始字符串列表，原样保留。

    2026-10-17 修复：items 必须**连同其后的间隔符**一起切出。
    原实现用 findall 只取 `<item>…</item>` 本身，item 之间的换行/缩进
    （本仓库 75 个 item 共 21 处）会被静默丢弃；main() 里
    `head + "".join(items) + tail` 再拼回去时，整个文件就被压成少数几行——
    即便当日一篇新文章都没有，跑一次管线也会产生一次覆盖全文件的 diff，
    把真正的「新增/挤出 item」淹没在上百行 churn 里。
    故改为按 span 切分，每个元素 = item 原文 + 其后到下一个 item 前的原文，
    保证 join 结果与输入逐字节相等。
    """
    spans = [(m.start(), m.end()) for m in ITEM_RE.finditer(raw)]
    if not spans:
        # 无 item：按 </channel> 拆分，保持文件其余部分原样
        idx = raw.find("  </channel>")
        if idx != -1:
            return raw[:idx], [], raw[idx:]
        return raw, [], DEFAULT_TAIL
    items = []
    for i, (start, _end) in enumerate(spans):
        # 到下一 item 起点为止（末个 item 取到它自己的结尾）
        stop = spans[i + 1][0] if i + 1 < len(spans) else spans[i][1]
        items.append(raw[start:stop])
    last_end = spans[-1][1]
    return raw[:spans[0][0]], items, raw[last_end:]


def main():
    args = sys.argv[1:]
    root = "."
    # 「今日」按本地（UTC+8）判定 —— 与 articles.json 的 date 字段同口径。
    # lastBuildDate 仍用 UTC（RFC822 惯例，后缀 GMT），两者不要混。
    run_date = datetime.now(LOCAL_TZ).date()
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
    # 新建的 item 是单行，须补上与其它 item 相同的间隔符，否则拼回去时会
    # 与后一个 item 粘在同一行（split_rss 现在保留间隔符，新建的也得跟上）。
    sep = new_item_sep(items)
    for rec in new_recs:
        items.insert(0, item_xml(rec) + sep)

    if new_recs:
        evicted = items[MAX_ITEMS:]          # 上限之外的被静默丢弃，必须点名
        items = items[:MAX_ITEMS]
        head = LASTBUILD_RE.sub(
            lambda m: m.group(1) + rfc822(now, "GMT") + m.group(2), head)
        names = "、".join(r["slug"][:40] for r in new_recs)
        print(f"  rss.xml: 新增 {len(new_recs)} 篇（{names}），共 {len(items)} 篇")
        if evicted:
            print(f"  ⚠️ feed 已达上限 {MAX_ITEMS}，挤出 {len(evicted)} 条：")
            for it in evicted:
                m = re.search(r"<title>(.*?)</title>", it)
                print(f"     - {(m.group(1) if m else it[:60])[:70]}")
    else:
        print(f"  rss.xml: {date_str} 无新文章，未变动")

    # P2 #12：无论本次有没有新条目，写出前都把 dc 命名空间与 dc:creator 补齐，
    # 使存量文件的一次性迁移与普通增量走同一条代码路径。
    head = ensure_dc_ns(head)
    items = [ensure_dc_creator(it) for it in items]
    out = head + "".join(items) + tail

    # 换行符风格保真：仓库 rss.xml 是 CRLF，而本脚本的模板常量是 LF。
    # 若不做此转换，即便当日没有新文章，每次跑管线也会把整个文件从 CRLF 刷成 LF，
    # 产生一次覆盖全文件的无意义 diff —— 它既污染 git 历史，也会把真正的
    # 内容变更（新增/挤出 item）淹没在上百行 churn 里，让验收看不到重点。
    #
    # 坑（2026-10-17 实测踩到）：检测必须用二进制读。上面的 raw 是用文本模式
    # 读的，Python 的 universal newlines 早把 CRLF 规整成了 LF，拿 raw 判断
    # 永远得到 LF，转换形同虚设。故此处单独二进制读一次。
    try:
        with open(rss_path, "rb") as f:
            newline = "\r\n" if b"\r\n" in f.read() else "\n"
    except OSError:
        newline = "\n"
    out = re.sub(r"\r?\n", newline, out)

    with open(rss_path, "w", encoding="utf-8", newline="") as f:
        f.write(out)
    print(f"RSS 更新完成: {len(items)} 个 item（上限 {MAX_ITEMS}）")


if __name__ == "__main__":
    main()
