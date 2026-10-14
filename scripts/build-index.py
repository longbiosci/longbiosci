#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build-index.py —— data/articles.json 构建器（逆向重写版 v1.0）

复刻来源：线上 data/articles.json（2026-10-14 基线，380 条记录，9 字段）
实证方式：380 篇文章页逐字段全量比对，规则命中率除 desc 57 篇旧稿件源
遗留值外全部 100%。

核心模型：增量更新（与原管线行为一致，已由多项证据锁定）
  1. 读取现有 data/articles.json 为权威登记——已登记 slug 的原记录整体保留，
     不因 HTML 侧后续编辑（meta description 改写、来源块增删）而变动。
     （实证：57 篇 desc 仅存于 JSON；3 篇 source 为 umami.is/doi.org 但 HTML
     无来源块；旧模板文章无 tag/time 而 JSON 有值——均为登记态遗留。）
  2. 扫描 news/*.html，对未登记文件提取 9 字段追加。
     登记门槛：能提取到 h1 标题 且 article-header 内有 time 日期
     （实证：3 个孤儿旧稿无 h1 无 time，天然排除）。
  3. 排序：slug 字母正序 stable sort，再按 date 倒序（与原产物一致）。
  4. 序列化：json.dumps(ensure_ascii=False, indent=1) + CRLF 行尾，无尾随换行
     （与原文件 217147 字节逐字节一致，Windows 工具风格产出）。

新文章字段提取规则（对新模板文章全量实证）：
  slug      文件名
  title     <h1> 文本（剔除 <br>）
  desc      meta description → og:description → ''
  tag       article-header 区块 <span class="tag"> → 无则 ''
  date      article-header 区块 <time datetime="YYYY-MM-DD">
  topic     poster.js 的 data-topic → topics/ 专题页引用反推 → ''
  type      TAG2TYPE[tag]（87 项映射表，未登录 tag 缺省 研究进展）
  evidence  poster.js 的 data-tier → notice-box <span class="tier tier-x"> → ''
  source    <p class="source">来源: <a href="https://HOST/..."> 的 HOST → 无则 ''
"""
import json
import os
import re
import sys

# ---- tag → type 映射表（自 380 条产物全量提取，87 项无冲突）----
TAG2TYPE = {
    '': '研究进展',
    'GLP-1药物': '研究进展',
    'HMGB1': '研究进展',
    'Nature Aging': '研究进展',
    'Nature研究': '研究进展',
    'Senolytic': '研究进展',
    '临床研究': '临床进展',
    '临床试验': '临床进展',
    '临床进展': '临床进展',
    '产业动态': '行业动态',
    '产业洞察': '行业动态',
    '产业观察': '行业动态',
    '代谢': '研究进展',
    '代谢与衰老': '研究进展',
    '代谢组学': '研究进展',
    '免疫衰老': '研究进展',
    '公司动态': '行业动态',
    '再生医学': '研究进展',
    '分子机制': '机制研究',
    '动脉粥样硬化': '研究进展',
    '单细胞研究': '研究进展',
    '基因疗法': '研究进展',
    '基因研究': '研究进展',
    '基因表达': '研究进展',
    '基础研究': '机制研究',
    '大型队列研究': '研究进展',
    '大脑衰老': '研究进展',
    '工具方法': '研究进展',
    '干细胞衰老': '研究进展',
    '心肌再生': '研究进展',
    '技术方法': '研究进展',
    '技术突破': '研究进展',
    '抗衰老研究': '研究进展',
    '政策解读': '行业动态',
    '新方法论': '研究进展',
    '新研究': '研究进展',
    '方法学': '综述解读',
    '早衰症': '研究进展',
    '最新研究': '研究进展',
    '机制研究': '机制研究',
    '流行病学': '研究进展',
    '深度解读': '综述解读',
    '炎症': '研究进展',
    '理论综述': '综述解读',
    '生物学': '研究进展',
    '生物标志物': '研究进展',
    '研究': '研究进展',
    '研究发现': '研究进展',
    '研究突破': '研究进展',
    '研究简报': '研究进展',
    '研究进展': '研究进展',
    '神经免疫': '研究进展',
    '神经科学': '研究进展',
    '神经科学 · 免疫衰老': '研究进展',
    '科学研究': '研究进展',
    '科研突破': '研究进展',
    '科研进展': '研究进展',
    '突破': '研究进展',
    '系统综述': '综述解读',
    '系统评价': '综述解读',
    '综述': '综述解读',
    '综述解读': '综述解读',
    '综述进展': '综述解读',
    '肌肉衰老': '研究进展',
    '肠道菌群': '研究进展',
    '脑类淋巴系统': '研究进展',
    '自身免疫': '研究进展',
    '营养与衰老': '研究进展',
    '蛋白稳态': '研究进展',
    '蛋白质稳态': '研究进展',
    '行业动态': '行业动态',
    '表观遗传': '研究进展',
    '衰老理论': '研究进展',
    '衰老细胞': '研究进展',
    '衰老钟': '研究进展',
    '观点分析': '观点评论',
    '观点文章': '观点评论',
    '观点视角': '观点评论',
    '观点评论': '观点评论',
    '观点评述': '观点评论',
    '计算生物学': '研究进展',
    '运动': '研究进展',
    '运动医学': '研究进展',
    '重磅研究': '研究进展',
    '重磅预印本': '研究进展',
    '阿尔茨海默': '研究进展',
    '领域评述': '综述解读',
}

# topics/ 专题页文件名 → topic 中文名（分页 -2/-3 自动归一）
TOPIC_FILE2CN = {
    "cellular-senescence": "细胞衰老",
    "epigenetics": "表观遗传",
    "immunology-inflammation": "免疫与炎症",
    "life-course": "生命历程",
    "metabolism-nutrition": "代谢与营养",
    "methods-tools": "方法与工具",
    "neurodegeneration": "神经退行",
    "organ-aging": "器官衰老",
}

RE_H1 = re.compile(r"<h1>(.*?)</h1>", re.S)
RE_META_DESC = re.compile(r'<meta name="description" content="([^"]*)">')
RE_OG_DESC = re.compile(r'<meta property="og:description" content="([^"]*)">')
RE_ART_HEADER = re.compile(r'<header class="article-header">(.*?)</header>', re.S)
RE_TAG = re.compile(r'<span class="tag">([^<]*)</span>')
RE_TIME = re.compile(r'<time datetime="(\d{4}-\d{2}-\d{2})"')
RE_DATA_TOPIC = re.compile(r'data-topic="([^"]+)"')
RE_DATA_TIER = re.compile(r'data-tier="([A-D])"')
RE_TIER_SPAN = re.compile(r'<span class="tier tier-([a-d])">')
RE_SOURCE = re.compile(r'<p class="source">来源: <a href="https?://([^/"]+)')
RE_NEWS_HREF = re.compile(r'href="/news/([^"]+)"')


def clean_text(s):
    """去 HTML 标签与首尾空白（h1 内的 <br> 等）。"""
    s = re.sub(r"<br\s*/?>", "", s)
    s = re.sub(r"<[^>]+>", "", s)
    return s.strip()


def build_topic_index(root):
    """topics/ 专题页引用反推：slug -> topic 中文名。一篇归属多个专题时取首个。"""
    idx = {}
    tdir = os.path.join(root, "topics")
    if not os.path.isdir(tdir):
        return idx
    for fn in sorted(os.listdir(tdir)):
        if not fn.endswith(".html") or fn == "index.html":
            continue
        base = re.sub(r"-\d+\.html$", ".html", fn)
        cn = TOPIC_FILE2CN.get(base[:-5])
        if not cn:
            continue
        with open(os.path.join(tdir, fn), encoding="utf-8") as f:
            for slug in RE_NEWS_HREF.findall(f.read()):
                idx.setdefault(slug, cn)
    return idx


def extract_article(root, slug, topic_idx):
    """从单篇文章页提取字段；结构不合格（无 h1 或无日期）返回 None。"""
    path = os.path.join(root, "news", slug)
    with open(path, encoding="utf-8") as f:
        html = f.read()

    m = RE_H1.search(html)
    if not m:
        return None
    title = clean_text(m.group(1))

    header = RE_ART_HEADER.search(html)
    header_html = header.group(1) if header else ""

    mt = RE_TIME.search(header_html) or RE_TIME.search(html)
    if not mt:
        return None  # 登记门槛：无日期视为非文章页（孤儿旧稿）

    md = RE_META_DESC.search(html)
    if md:
        desc = md.group(1)
    else:
        mo = RE_OG_DESC.search(html)
        desc = mo.group(1) if mo else ""

    mg = RE_TAG.search(header_html) or RE_TAG.search(html)
    tag = mg.group(1).strip() if mg else ""

    mtopic = RE_DATA_TOPIC.search(html)
    topic = mtopic.group(1) if mtopic else topic_idx.get(slug, "")

    mtier = RE_DATA_TIER.search(html)
    if not mtier:
        ms = RE_TIER_SPAN.search(html)
        mtier = ms
    evidence = mtier.group(1).upper() if mtier else ""

    msrc = RE_SOURCE.search(html)
    source = msrc.group(1) if msrc else ""

    return {
        "slug": slug,
        "title": title,
        "desc": desc,
        "tag": tag,
        "date": mt.group(1),
        "topic": topic,
        "type": TAG2TYPE.get(tag, "研究进展"),
        "evidence": evidence,
        "source": source,
    }


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    index_path = os.path.join(root, "data", "articles.json")

    # 1) 现有登记（权威基线）
    registered = {}
    if os.path.isfile(index_path):
        with open(index_path, encoding="utf-8") as f:
            for rec in json.load(f):
                registered[rec["slug"]] = rec

    # 2) 扫描 news/ 找新文章
    topic_idx = build_topic_index(root)
    news_dir = os.path.join(root, "news")
    added, skipped = [], []
    if os.path.isdir(news_dir):
        for fn in sorted(os.listdir(news_dir)):
            if not fn.endswith(".html") or fn == "index.html":
                continue
            if fn in registered:
                continue
            rec = extract_article(root, fn, topic_idx)
            if rec is None:
                skipped.append(fn)
                continue
            registered[fn] = rec
            added.append(fn)

    # 3) 排序：slug 正序 stable → date 倒序
    records = sorted(registered.values(), key=lambda r: r["slug"])
    records.sort(key=lambda r: r.get("date", ""), reverse=True)

    # 4) 序列化（CRLF + indent=1，与原格式逐字节一致）
    text = json.dumps(records, ensure_ascii=False, indent=1).replace("\n", "\r\n")
    os.makedirs(os.path.dirname(index_path), exist_ok=True)
    with open(index_path, "w", encoding="utf-8", newline="") as f:
        f.write(text)

    print(f"articles.json 构建完成: {len(records)} 条（新增 {len(added)}，跳过非文章页 {len(skipped)}）")
    for fn in skipped:
        print(f"  [skip] {fn}")


if __name__ == "__main__":
    main()
