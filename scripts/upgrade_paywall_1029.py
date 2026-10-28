#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""upgrade_paywall_1029.py —— 2026-10-29 轮：付费墙积压回捞的 11 张升级卡片原地升级。

背景：
  10-25 轮有 11 条文献因付费墙只拿到摘要，按「摘要级」上站（正文里明确声明
  未获全文、未做数值推算）。本轮上游从积压里回捞到全文，产出「升级卡片」。
  按规则 ④（上站前查重，重复条目跳过计数），这 11 条 PMID 已站内存在，
  **不新建页面**，改为原地替换正文：保留原 slug / 原始发布日期 / 原中文标题，
  把正文升级为全文级，并在首屏写明本次升级的时间。

口径：
  - 日期不动：页码 publish date 仍是首次上线日，避免日期倒挂
  - 正文首行是 `<em>数据日期 / 生成时间</em>` 时间标签（规则 ③）
  - desc 用全文级结论替换原摘要级结论
  - evidence / tag 按全文内容重新分级
"""
import html
import importlib.util
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DATE = "2026-10-29"
GEN_AT = "2026-10-29 05:50"

SRC_FT = ("Upstream 卡片 `文献监控_2026-10-29_卡片`（file_id dGBunAeRiRlm，"
          "实测 692,872 B；付费墙积压回捞全文批次）")

# 11 张升级卡片是中文撰写的（其余 274 张是英文原文摘抄），
# 分级正则（HUMAN_KW / ANIMAL_KW）在中文正文上基本失效：
# U10 明明是 C. elegans 却被判成 A、U11 明明是前瞻性临床志愿者却被判成 B。
# 这里逐条人工裁定，比继续堆正则可靠。
UP_EV = {
    "U01": ("B", "核心模型为秀丽隐杆线虫，哺乳动物在体因果验证缺失"),
    "U02": ("A", "12 个人体组织、37.5 万个人内皮细胞的单细胞图谱"),
    "U03": ("B", "肿瘤治疗诱导衰老模型，体外＋小鼠在体"),
    "U04": ("A", "allo-HSCT 后慢性肺 GVHD 患者 BAL 液单细胞测序，人源样本"),
    "U05": ("A", "GBD 2023 聚合数据的卫生经济学建模，产出新估计值（与 169 同口径）"),
    "U06": ("B", "18 月龄 C57BL/6 雄性小鼠脑出血模型"),
    "U07": ("A", "5.3 万人营养-炎症指数与血管老化、死亡率的队列关联"),
    "U08": ("A", "39 万余人健康体检队列外部验证的生物学年龄算法"),
    "U09": ("A", "脑老化与执行功能缺损的青少年／成人实证队列"),
    "U10": ("B", "C. elegans 模型 + 药理自噬激活，无线虫以外人体数据"),
    "U11": ("A", "56 天家用 LED 面膜＋面霜的前瞻性人体临床研究"),
}
UP_TOPIC = {}


def load_intake_helpers():
    """复用 10-29 批的分级 / 渲染函数，避免两处口径漂移。"""
    src = open(os.path.join(ROOT, 'scripts',
                            'gen_articles_intake_2026-10-29a.py'),
               encoding='utf-8').read()
    ns = {'__name__': 'intake1029', '__file__': 'x'}
    exec(compile(src.rsplit('def main()', 1)[0], 'intake', 'exec'), ns)
    return ns


def load_ga():
    # gen_articles.py 在模块层读 sys.argv（ROOT/SRC/DATE），先占位再加载
    old = sys.argv
    sys.argv = ["gen_articles.py", ROOT, "/dev/null", DATA_DATE]
    try:
        p = os.path.join(ROOT, "scripts", "gen_articles.py")
        spec = importlib.util.spec_from_file_location("ga_up", p)
        ga = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ga)
        return ga
    finally:
        sys.argv = old


CRUMB_RE = re.compile(r'<nav class="breadcrumb"[^>]*>.*?'
                      r'<span aria-current="page">(.*?)</span>', re.S)
REL_RE = re.compile(r'<div class="related-block">.*?<ul class="related-list">(.*?)'
                    r'</ul>', re.S)
DATE_RE = re.compile(r'<span class="date"><time datetime="(\d{4}-\d{2}-\d{2})">')


def _md2html(s):
    if not s:
        return ""
    s = s.replace('\r', '')
    out, buf = [], []
    for line in s.split('\n'):
        line = line.strip()
        if not line:
            continue
        item = re.match(r'^[-*]\s+(.*)$', line)
        if item:
            if buf:
                out.append('<p>' + ' '.join(buf) + '</p>')
                buf = []
            out.append('<li>' + item.group(1) + '</li>')
        else:
            buf.append(line)
    if buf:
        out.append('<p>' + ' '.join(buf) + '</p>')
    txt = '\n'.join(out)
    txt = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', txt)
    txt = re.sub(r'(?:<li>.*?</li>\n?)+', lambda m: '<ul>\n' + m.group(0) + '\n</ul>', txt)
    return txt


def esc_plain(s, n=190):
    t = re.sub(r'\*\*(.+?)\*\*', r'\1', s or '')
    t = re.sub(r'\s+', ' ', t).strip(' -·')
    return t[:n]


def body_of(c, ns, prev_note):
    head = f'<p><em>数据日期 {DATA_DATE} · 生成时间 {GEN_AT}</em></p>'
    head += ('<p><strong>本次为付费墙积压回捞的原地升级</strong>：本条首次上线时为'
             '「摘要级」（仅有 PubMed 结构化摘要），现已获取全文并逐节核验，'
             '正文与结论改为全文级撰写；slug、首次发布日期与标题保持不变。</p>')
    if prev_note:
        head += '<p>' + prev_note + '</p>'
    parts = [head]
    for h, key in [("研究问题", "question"), ("方法", "method"),
                   ("核心结论", "conclusion"), ("局限", "limit"),
                   ("对本项目的价值", "value")]:
        if c[key]:
            parts.append(f'<h2>{h}</h2>' + _md2html(c[key]))
    if c["ftsrc"]:
        parts.append('<h2>全文来源</h2>' + _md2html(c["ftsrc"]))
    parts.append('<h2>原文题录</h2><ul>'
                 '<li>英文标题：' + html.escape(c["title"]) + '</li>'
                 '<li>期刊与标识：' + html.escape(c["journal"]) +
                 (f' · PMID {c["pmid"]}' if c["pmid"] else "") +
                 (f' · DOI {html.escape(c["doi"])}' if c["doi"] else "") +
                 '</li></ul>')
    return '\n\n'.join(parts)


def lit_src(c):
    bits = [f'<em>{html.escape(c["journal"])}</em>']
    if c["pmid"]:
        bits.append(f'PMID {c["pmid"]}')
    if c["doi"]:
        bits.append(f'DOI <a href="https://doi.org/{c["doi"]}" target="_blank" '
                    f'rel="noopener noreferrer">{c["doi"]}</a>')
    bits.append('来源：' + SRC_FT + ' · 全文已获取并通过归属校验')
    return ' · '.join(bits)


def main():
    cards = json.load(open('/tmp/cards_1029.json', encoding='utf-8'))
    up = [c for c in cards if c["num"].startswith("U")]
    if not up:
        print("没有升级卡片，退出")
        return
    ns = load_intake_helpers()
    ga = load_ga()

    arts_p = os.path.join(ROOT, "data", "articles.json")
    arts = json.load(open(arts_p, encoding='utf-8'))
    byslug = {a["slug"]: a for a in arts}

    # PMID → 站内页面（只看 news/*.html 正文）
    pm_re = re.compile(r'PMID\s*:?\s*(\d{6,8})')
    hit = {}
    for p in __import__('glob').glob(os.path.join(ROOT, 'news', '*.html')):
        t = open(p, encoding='utf-8', errors='ignore').read()
        for m in set(pm_re.findall(t)):
            hit.setdefault(m, os.path.basename(p))

    done, miss = [], []
    for c in up:
        slug = hit.get(c["pmid"])
        if not slug or slug not in byslug:
            miss.append((c["num"], c["pmid"]))
            continue
        page = open(os.path.join(ROOT, 'news', slug), encoding='utf-8').read()
        crumb = (CRUMB_RE.search(page).group(1)
                 if CRUMB_RE.search(page) else byslug[slug]["title"][:12])
        relm = REL_RE.search(page)
        rel = relm.group(1) if relm else ""
        dm = DATE_RE.search(page)
        pub_date = dm.group(1) if dm else byslug[slug].get("date", DATA_DATE)

        ev, why = UP_EV.get(c["num"], (ns['grade'](c), "自动分级"))
        topic = UP_TOPIC.get(c["num"]) or ns['TOPIC_MAP'].get(
            c["topic"], byslug[slug].get("topic", "生命历程"))
        ga.DATE = pub_date
        m = dict(topic=topic, ev=ev, tag=ns['tag_of'](c, ev),
                 title=byslug[slug]["title"], crumb=crumb,
                 desc=esc_plain(c["conclusion"] or c["question"]),
                 source=lit_src(c),
                 body=body_of(c, ns, None), related=[],
                 notice_src="fulltext")
        out = os.path.join(ROOT, 'news', slug)
        open(out, 'w', encoding='utf-8', newline='').write(ga.build(slug, m, rel))
        e = byslug[slug]
        e["desc"] = m["desc"]
        e["evidence"] = ev
        e["tag"] = m["tag"]
        e["type"] = m["tag"]
        e["topic"] = topic
        done.append((c["num"], slug, ev))

    with open(arts_p, 'w', encoding='utf-8') as f:
        json.dump(arts, f, ensure_ascii=False, indent=2)
    print(f"原地升级 {len(done)} 篇（升级卡片 {len(up)} 张）")
    for n, s, ev in sorted(done):
        print(f"   ↑ {n} → {s} [{ev}]")
    if miss:
        print("未命中站内页面：", miss)


if __name__ == "__main__":
    main()
