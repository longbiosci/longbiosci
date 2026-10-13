#!/usr/bin/env python3
"""从 data/articles.json 重建 rss.xml 与 sitemap.xml。
由 .github/workflows/regen-index.yml 在 articles.json 变更时自动调用；
也可本地运行：python3 scripts/gen_index.py
"""
import json
import re
from datetime import datetime, timezone
from email.utils import formatdate
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://longbiosci.com"

def rfc822(date_str: str) -> str:
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return formatdate(dt.timestamp(), usegmt=True)

def build(articles: list) -> None:
    arts = sorted(articles, key=lambda a: a.get("date", ""), reverse=True)
    rss_arts = arts[:50]  # rss 只保留最近 50 条，避免订阅文件过大
    last_build = formatdate(usegmt=True)

    items = []
    for a in rss_arts:
        url = f"{BASE}/news/{a['slug']}"
        title = escape(f"{a['title']} - LongBiosci")
        desc = escape(a.get("desc", ""))
        items.append(
            f"<item><title>{title}</title><link>{url}</link>"
            f'<guid isPermaLink="true">{url}</guid>'
            f"<pubDate>{rfc822(a['date'])}</pubDate>"
            f"<description>{desc}</description></item>"
        )
    rss = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
        "  <channel>\n"
        "    <title>LongBiosci - 长寿科技资讯</title>\n"
        f"    <link>{BASE}</link>\n"
        "    <description>最新生物医药与长寿科技研究资讯</description>\n"
        "    <language>zh-cn</language>\n"
        f"    <lastBuildDate>{last_build}</lastBuildDate>\n"
        f'    <atom:link href="{BASE}/rss.xml" rel="self" type="application/rss+xml"/>\n'
        + "".join(items) +
        "\n  </channel>\n</rss>\n"
    )
    (ROOT / "rss.xml").write_text(rss, encoding="utf-8")

    urls = [
        f"{BASE}/", f"{BASE}/news.html", f"{BASE}/about.html",
        f"{BASE}/archive.html", f"{BASE}/rss.xml",
    ]
    for a in arts:
        urls.append(f"{BASE}/news/{a['slug']}")
    mods = sorted({a.get("date", "") for a in arts}, reverse=True)
    lastmod = mods[0] if mods else datetime.now().strftime("%Y-%m-%d")
    blocks = []
    for u in urls:
        p = "1.0" if u.rstrip("/") == BASE else "0.7"
        blocks.append(
            f"  <url>\n    <loc>{u}</loc>\n    <lastmod>{lastmod}</lastmod>\n"
            f"    <changefreq>weekly</changefreq>\n    <priority>{p}</priority>\n  </url>"
        )
    sm = (
        "<?xml version='1.0' encoding='UTF-8'?>\n"
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">\n'
        + "\n".join(blocks) + "\n</urlset>\n"
    )
    (ROOT / "sitemap.xml").write_text(sm, encoding="utf-8")
    print(f"rss.xml: {len(rss_arts)} items; sitemap: {len(urls)} urls; lastmod={lastmod}")

if __name__ == "__main__":
    arts = json.loads((ROOT / "data" / "articles.json").read_text(encoding="utf-8"))
    build(arts)
