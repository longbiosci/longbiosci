#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_articles_intake_2026-10-25b.py —— 内容摄入第 22 批（2026-10-25 05:30 巡检）

消化对象
────────
《预印本全文级解读_2026-10-25》（任务 12819187，元层 dQpzABLkRxLu
子目录 dXINeJTzybpG）—— 54 条（数据日期 2026-10-23 的 20 条欠账清偿
＋ 2026-10-24 的 34 条当日），档位分布 A 8 / C 16 / D 30。

查重（规则④）：扫 news/*.html 全文 DOI（915 个）逐条比对，
54 条中 **4 条站内已有** → 跳过计数；**50 条净新增 → 本批全部成篇**。

成篇口径
────────
· 正文采用上游解读页的「一句话结论 / 研究问题与设计 / 核心结果 /
  局限与保留意见 / 对研究者的价值 / 全文核验状态」六节，**照抄原文**；
· 不因档位（A/C/D）筛掉任何一条——档位只影响「是否核验全文」的标注，
  不影响是否上站；D 级（源站封锁、未取全文）在正文末尾已由上游标注。
· slug 由 DOI 直接派生，保证唯一且可反查。

证据分级：预印本一律 C（无论数据规模与档位）。
时间标签（规则③）：沿用上游每页自带的「数据日期 + 生成时间」，
并在正文首段以 `数据日期 YYYY-MM-DD · 生成时间 YYYY-MM-DD HH:MM` 输出。
"""
import html
import importlib.util
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATE = "2026-10-25"
TMP = os.path.join(ROOT, ".intake-tmp/1025")
BOOKS = [
    os.path.join(TMP, "dlCcedbEOyBO__预印本解读_合订本_2026-10-23_20条.md"),
    os.path.join(TMP, "dpJYzScWqsdR__预印本解读_合订本_2026-10-24_34条.md"),
]
ITEMS = json.load(open(os.path.join(TMP, "dsZSULgnRTBP__预印本解读_2026-10-25_items.json"),
                       encoding="utf-8"))
BY_DOI = {it['doi']: it for it in ITEMS}

# 本轮查重（扫 news/*.html 全文提取 915 个 DOI 后逐条比对）命中的 4 条：
# 站内已有成稿（午刊 10-24 批次已发布），按规则④跳过并计数，不重复上站。
SKIP_DOI = {
    "10.64898/2026.10.21.760791",   # 主榜02 衰老成纤维细胞因果网络 → 午刊已发
    "10.64898/2026.10.18.759616",   # 主榜03 miR-29 → 午刊已发
    "10.64898/2026.10.19.760092",   # 补遗01 NAD 性别特异性保护 → 午刊已发
    "10.64898/2026.10.21.760773",   # 观察哨02 高龄母体蜕膜血管 → 午刊已发
}

TOPIC_RULES = [
    ("神经退行", ["阿尔茨海默", "AD ", "tau", "Tau", "认知", "脑", "神经", "帕金森",
                  "突触核蛋白", "海马", "痴呆", "朊", "路易体", "ALS", "亨廷顿"]),
    ("表观遗传", ["表观", "甲基化", "时钟", "m6A", "染色质", "miR-"]),
    ("细胞衰老", ["衰老细胞", "senescence", "senolytic", "SASP", "细胞衰老", "部分重编程",
                  "端粒", "p16", "p21"]),
    ("免疫与炎症", ["免疫", "炎症", "T 细胞", "巨噬", "小胶质", "细胞因子", "干扰素"]),
    ("代谢与营养", ["代谢", "线粒体", "NAD", "营养", "饮食", "胰岛素", "脂", "糖"]),
    ("方法与工具", ["方法", "管线", "pipeline", "模型", "算法", "测序", "标志物", "队列",
                    "图谱", "分割", "转录组"]),
    ("器官衰老", ["骨", "肝", "肾", "心", "血管", "肺", "肠", "肌肉", "皮肤", "卵巢", "睾丸"]),
]


def topic_of(title, rank):
    for topic, kws in TOPIC_RULES:
        for k in kws:
            if k in title:
                return topic
    return "生命历程"


def md2html(s):
    if not s:
        return ""
    out, buf = [], []
    for line in s.split('\n'):
        line = line.rstrip()
        if not line.strip():
            if buf:
                out.append('<p>' + ' '.join(buf) + '</p>')
                buf = []
            continue
        if re.match(r'^\s*\|', line):          # 表格行：跳过（题录表已进 source）
            if buf:
                out.append('<p>' + ' '.join(buf) + '</p>')
                buf = []
            continue
        item = re.match(r'^\s*(?:\d+\.\s+|[-*]\s+)(.*)$', line)
        if item:
            if buf:
                out.append('<p>' + ' '.join(buf) + '</p>')
                buf = []
            out.append('<li>' + item.group(1) + '</li>')
        else:
            buf.append(line.strip())
    if buf:
        out.append('<p>' + ' '.join(buf) + '</p>')
    txt = '\n'.join(out)
    txt = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', txt)
    txt = re.sub(r'`([^`]+)`', r'<code>\1</code>', txt)
    txt = re.sub(r'(?:<li>.*?</li>\n?)+',
                 lambda m: '<ul>\n' + m.group(0) + '\n</ul>', txt)
    return txt


def esc_plain(s, n=190):
    t = re.sub(r'\*\*(.+?)\*\*', r'\1', s or '')
    t = re.sub(r'`', '', t)
    t = re.sub(r'\s+', ' ', t).strip(' -·|')
    return t[:n]


def parse_book(path):
    """合订本 → [{doi, rank, title, meta, sections:{名:正文}}]"""
    txt = open(path, encoding='utf-8').read()
    parts = re.split(r'\n(?=# )', txt)
    out = []
    for p in parts[1:]:
        m_doi = re.search(r'\*\*DOI\*\*：`(10\.\d{4,9}/[^`]+)`', p)
        m_rank = re.search(r'\*\*档位\*\*：([^　｜|]+)', p)
        m_dd = re.search(r'\*\*数据日期\*\*：([\d-]{10})', p)
        m_gt = re.search(r'\*\*生成时间\*\*：([\d-]{10} [\d:]{5})', p)
        m_srv = re.search(r'\*\*来源\*\*：([^　｜|]+)', p)
        m_lvl = re.search(r'\*\*解读层级\*\*：\*?\*?([^*｜|\n]+)', p)
        title = p.split('\n')[0].lstrip('# ').strip()
        if not m_doi:
            continue
        secs = {}
        cur = None
        buf = []
        for line in p.split('\n'):
            h = re.match(r'^## +(.+)$', line)
            if h:
                if cur:
                    secs[cur] = '\n'.join(buf).strip()
                cur = h.group(1).strip()
                buf = []
            elif cur:
                buf.append(line)
        if cur:
            secs[cur] = '\n'.join(buf).strip()
        out.append(dict(doi=m_doi.group(1), rank=(m_rank.group(1).strip() if m_rank else ''),
                        title=title, data_date=(m_dd.group(1) if m_dd else ''),
                        gen_at=(m_gt.group(1) if m_gt else ''),
                        server=(m_srv.group(1).strip() if m_srv else ''),
                        level=(m_lvl.group(1).strip() if m_lvl else ''),
                        sections=secs))
    return out


def slug_of(doi):
    s = re.sub(r'[^0-9A-Za-z]+', '-', doi).strip('-')
    return f"Preprint-{s}-2026.html"


def main():
    entries = []
    for b in BOOKS:
        entries += parse_book(b)
    print(f"合订本解析出 {len(entries)} 条")

    arts = json.load(open(os.path.join(ROOT, 'data/articles.json'), encoding='utf-8'))
    existing = {a['slug'] for a in arts}
    A, dup = {}, []
    for e in entries:
        it = BY_DOI.get(e['doi'], {})
        if it.get('dup') or e['doi'] in SKIP_DOI:
            dup.append((e['doi'], '站内已收录（规则④跳过）'))
            continue
        slug = slug_of(e['doi'])
        if slug in A:
            dup.append((e['doi'], '本批内重名'))
            continue
        if slug in existing or os.path.exists(os.path.join(ROOT, 'news', slug)):
            dup.append((e['doi'], 'slug 已存在'))
            continue
        secs = e['sections']
        order = [k for k in secs if re.match(r'^[一二三四五六七]、', k)]
        body_parts = [f'<p><em>数据日期 {e["data_date"] or "2026-10-24"} · '
                      f'生成时间 {e["gen_at"] or "2026-10-25 02:25"}</em></p>']
        for k in order:
            if '原文题录' in k:
                continue
            body_parts.append(f'<h2>{html.escape(k)}</h2>' + md2html(secs[k]))
        one = next((secs[k] for k in order if '一句话结论' in k), '')
        level = re.sub(r'\*', '', e['level'])
        src = (f'<em>{html.escape(e["server"] or "预印本")}</em> · 档位 {html.escape(e["rank"])}'
               f' · 解读层级 {html.escape(level)}'
               f' · DOI <a href="https://doi.org/{e["doi"]}" target="_blank" '
               f'rel="noopener noreferrer">{e["doi"]}</a>'
               f' · 来源：IMA 知识库《预印本全文级解读_2026-10-25》（任务 12819187）')
        A[slug] = dict(
            topic=topic_of(e['title'], e['rank']), ev="C", tag="预印本",
            title=e['title'], crumb=e['title'][:28],
            desc=esc_plain(one, 190),
            source=src,
            body='\n\n'.join(body_parts),
            related=[],
        )
    print(f"本批成篇 {len(A)} 篇 · 跳过 {len(dup)} 条")
    for d in dup:
        print('  跳过:', d)

    sys.argv = ["gen_articles.py", ROOT, "/dev/null", DATE]
    _spec = importlib.util.spec_from_file_location(
        "ga", os.path.join(ROOT, "scripts", "gen_articles.py"))
    ga = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(ga)
    ga.A = A
    ga.main()


if __name__ == "__main__":
    main()
