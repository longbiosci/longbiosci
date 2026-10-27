#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_articles_intake_2026-10-28a.py —— 05:30 班第 16 轮 · 批次 a

消化对象
────────
《预印本全文级解读_2026-10-28》（任务 12819187，元层 dQpzABLkRxLu
子目录 dmRvnNuSIkpC）—— _items 索引 26 条（主窗口 T-1=2026-10-27：
主榜 01–05 + 观察哨 01–09；补遗窗口 T-2=2026-10-26：补遗主榜 A1–A4
+ 补遗观察哨 B1–B8）。

判空（硬规则）：26 个解读文件 + _items 全部实际下载，实测字节数均 > 0，
无空产出（实测表：.intake/sizes-1028.json）。

查重（规则④）：逐条 grep news/*.html 正文全文命中 DOI ——
26 条中 **25 条 NEW / 1 条已上站跳过**（10.64898/2026.10.11.758291
「小鼠肠道与肝脏再生过程中的转录组年轻化」，补遗主榜 A1）。

成篇口径（沿用 2026-10-26a 批）
──────────────────────────────
· 正文采用上游解读页的分节结构，**照抄原文**，不改写、不压缩；
· A 档（8 篇，medRxiv PDF 全文已逐节核验）与 C 档（17 篇，bioRxiv
  Cloudflare 403 仅官方摘要）一视同仁上站——档位只影响「是否核验全文」
  的显式标注，不影响是否发表；
· slug 由 DOI 派生，`Preprint-<doi-slug>-2026.html`，唯一可反查；
· 证据分级：预印本一律 C（无论数据规模与档位），依 SOP §4.2；
· 时间标签（规则③）：正文首段 `数据日期 YYYY-MM-DD · 生成时间 YYYY-MM-DD HH:MM`。
"""
import html
import importlib.util
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATE = "2026-10-28"
RAW = os.path.join(ROOT, ".intake", "raw", "1028")
ITEMS = json.load(open(os.path.join(RAW, "dfPCBwYantrz___items"), encoding="utf-8"))


def bind_local():
    """_items 的 file 名 → 本轮实际下载落盘路径（file_id__name 形式）。

    下载时按「file_id + basename」落盘，与 _items 里的 file 名不是同一串，
    故此处按 basename 去扩展名后的最长前缀匹配，匹配不到即视为缺失。
    """
    files = os.listdir(RAW)
    for it in ITEMS:
        stem = it['file'][:-3] if it['file'].endswith('.md') else it['file']
        hit = [f for f in files if stem in f]
        it['_local'] = os.path.join(RAW, hit[0]) if hit else None


bind_local()

TOPIC_RULES = [
    ("神经退行", ["阿尔茨海默", "AD ", "tau", "Tau", "认知", "脑", "神经", "帕金森",
                  "突触核蛋白", "海马", "痴呆", "癫痫", "朊", "路易体", "ALS", "亨廷顿",
                  "亨廷顿病", "精神病", "脑龄", "脑网络", "MEG", "fMRI", "侧脑室"]),
    ("表观遗传", ["表观", "甲基化", "时钟", "m6A", "染色质", "miR-", "核纤层", "核膜",
                  "LAD", "转录组"]),
    ("细胞衰老", ["衰老细胞", "senescence", "senolytic", "SASP", "细胞衰老", "部分重编程",
                  "端粒", "p16", "p21", "克隆性造血", "脂滴", "再生"]),
    ("免疫与炎症", ["免疫", "炎症", "T 细胞", "巨噬", "小胶质", "细胞因子", "干扰素", "感染"]),
    ("代谢与营养", ["代谢", "线粒体", "NAD", "营养", "饮食", "胰岛素", "脂", "糖", "葡萄糖",
                    "糖尿病", "生物能", "囊泡"]),
    ("方法与工具", ["方法", "管线", "pipeline", "模型", "算法", "测序", "标志物", "队列",
                    "图谱", "分割", "转录组", "敏感性", "逻辑回归", "scRNA", "规范建模",
                    "基础模型", "大语言模型", "LLM"]),
    ("器官衰老", ["骨", "肝", "肾", "心", "血管", "肺", "肠", "肌肉", "皮肤", "卵巢", "睾丸",
                  "皮层", "肿瘤", "肉瘤", "听力", "助听器", "睡眠", "运动", "步态"]),
]


def topic_of(title, category):
    for topic, kws in TOPIC_RULES:
        for k in kws:
            if k in title:
                return topic
    if category:
        return "生命历程"
    return "生命历程"


def md2html(s):
    """上游 markdown → 文章正文 HTML（表格行跳过，题录已进 source 串）。"""
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
        if re.match(r'^\s*\|', line):
            if buf:
                out.append('<p>' + ' '.join(buf) + '</p>')
                buf = []
            continue
        if line.strip().startswith('---'):
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
    t = re.sub(r'<[^>]+>', '', t)
    t = re.sub(r'\s+', ' ', t).strip(' -·|>')
    return t[:n]


def parse_doc(path):
    txt = open(path, encoding='utf-8').read()
    meta = dict(
        doi=(re.search(r'\*\*DOI\*\*：`(10\.\d{4,9}/[^`]+)`', txt) or [None, None])[1],
        rank=((re.search(r'\*\*档位\*\*：([^　｜|\n]+)', txt) or [None, ''])[1]).strip(),
        data_date=(re.search(r'\*\*数据日期\*\*：([\d-]{10})', txt) or [None, ''])[1],
        gen_at=(re.search(r'\*\*生成时间\*\*：([\d-]{10} [\d:]{5})', txt) or [None, ''])[1],
        server=((re.search(r'\*\*来源\*\*：([^　｜|\n]+)', txt) or [None, ''])[1]).strip(),
        version=((re.search(r'\*\*版本\*\*：([^　｜|\n]+)', txt) or [None, ''])[1]).strip(),
        category=((re.search(r'\*\*category\*\*：([^　｜|\n]+)', txt) or [None, ''])[1]).strip(),
        level=((re.search(r'\*\*层级\*\*：\*?\*?([^*｜|\n]+)', txt) or [None, ''])[1]).strip(),
        authors=((re.search(r'\*\*作者署名\*\*：([^\n]+)', txt)
                  or re.search(r'\*\*作者\*\*：([^\n]+)', txt) or [None, ''])[1]).strip(),
        corr=((re.search(r'\*\*通讯\*\*：([^\n]+)', txt) or [None, ''])[1]).strip(),
    )
    title = txt.split('\n')[0].lstrip('# ').strip()
    secs, cur, buf = {}, None, []
    for line in txt.split('\n')[1:]:
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
    return dict(title=title, meta=meta, sections=secs)


def slug_of(doi):
    s = re.sub(r'[^0-9A-Za-z]+', '-', doi).strip('-')
    return f"Preprint-{s}-2026.html"


def already_on_site(dois):
    """规则④查重：DOI 在 news/*.html 正文中出现即判已上站。

    ⚠️ 只比对 slug 是不够的——本轮实测：10.64898/2026.10.11.758291 已于
    10-26 批以「Regeneration-Transient-Transcriptomic-Rejuvenation-Gut-Liver-2026.html」
    上站，而本批按 DOI 派生的 slug 是另一串，只查 slug 存在性会**重复建页**。
    故判重一律以 DOI 全文命中为准，slug 存在性只作二次兜底。
    """
    import subprocess
    pat = os.path.join(ROOT, ".intake", "doi-grep-1028.txt")
    open(pat, "w", encoding="utf-8").write("\n".join(dois))
    r = subprocess.run(["grep", "-rlF", "-f", pat] +
                       sorted(os.path.join("news", f) for f in os.listdir(
                           os.path.join(ROOT, "news")) if f.endswith(".html")),
                       cwd=ROOT, capture_output=True, text=True)
    hits = {}
    for line in r.stdout.splitlines():
        try:
            t = open(os.path.join(ROOT, line), encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        for d in dois:
            if d in t:
                hits.setdefault(d, []).append(os.path.basename(line))
    os.path.exists(pat) and os.remove(pat)
    return hits


def main():
    arts = json.load(open(os.path.join(ROOT, 'data/articles.json'), encoding='utf-8'))
    existing = {a['slug'] for a in arts}
    onsite = already_on_site([it['doi'] for it in ITEMS])
    A, dup = {}, []

    for it in ITEMS:
        doi = it['doi']
        slug = slug_of(doi)
        # 规则④：上站前对照站内已发布内容查重（DOI 全文命中 news/*.html）
        if onsite.get(doi):
            dup.append((doi, f"已上站（规则④跳过）：{onsite[doi][0]}"))
            continue
        if slug in existing or os.path.exists(os.path.join(ROOT, 'news', slug)):
            dup.append((doi, 'slug 已存在（规则④跳过）'))
            continue
        path = it.get('_local')
        if not path or not os.path.exists(path):
            dup.append((doi, '源文件缺失'))
            continue
        if slug in A:
            dup.append((doi, '本批内重名'))
            continue
        d = parse_doc(path)
        secs = d['sections']
        order = [k for k in secs if re.match(r'^[一二三四五六七八九十]、', k)]
        dd = d['meta']['data_date'] or it['data_date']
        ga = d['meta']['gen_at'] or '2026-10-28 02:05'
        ver = d['meta']['version'] or 'v1'
        cat = d['meta']['category'] or ''
        body_parts = [f'<p><em>数据日期 {dd} · 生成时间 {ga}　｜　'
                      f'预印本 · {html.escape(it["server"])} · {html.escape(ver)} '
                      f'· {html.escape(cat)}</em></p>']
        for k in order:
            if '原文题录' in k:
                continue
            body_parts.append(f'<h2>{html.escape(k)}</h2>' + md2html(secs[k]))
        one = next((secs[k] for k in order if '一句话结论' in k or '一句话' in k), '')
        if not one:
            one = d['title']
        ft = it.get('fulltext_status', 'C')
        ft_note = ('全文已获取并逐节核验（档位 A）' if ft == 'A'
                   else '摘要级 · 未取全文（源站封锁，档位 C）')
        src = (f'<em>{html.escape(it["server"])}</em> · 档位 {html.escape(d["meta"]["rank"])}'
               f' · 版本 {html.escape(ver)}'
               f' · DOI <a href="https://doi.org/{doi}" target="_blank" '
               f'rel="noopener noreferrer">{doi}</a>'
               f' · 来源：IMA 知识库《预印本全文级解读_2026-10-28》（任务 12819187）'
               f' · <strong>{ft_note}</strong>')
        A[slug] = dict(
            topic=topic_of(d['title'], cat), ev="C", tag="预印本",
            title=d['title'], crumb=d['title'][:28],
            desc=esc_plain(one, 190),
            source=src,
            body='\n\n'.join(body_parts),
            related=[],
        )

    print(f"本批成篇 {len(A)} 篇 · 跳过 {len(dup)} 条")
    for x in dup:
        print('  跳过:', x)

    sys.argv = ["gen_articles.py", ROOT, "/dev/null", DATE]
    _spec = importlib.util.spec_from_file_location(
        "ga", os.path.join(ROOT, "scripts", "gen_articles.py"))
    ga = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(ga)
    ga.A = A
    ga.main()


if __name__ == "__main__":
    main()
