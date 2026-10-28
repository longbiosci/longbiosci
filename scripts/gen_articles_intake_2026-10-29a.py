#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_articles_intake_2026-10-29a.py —— 内容摄入第 26 批（2026-10-29 05:30 巡检）

消化对象
────────
《文献监控_2026-10-29_卡片》（file_id dGBunAeRiRlm，file_download 实测 692,872 B）
—— 285 张卡片：全文级 199（编号 001–199）、升级卡片 11（U01–U11）、
摘要级 75（编号 200–274）。是本任务历史上单批次最大的一次文献交付。

产出决策（按排班改造第 ② 条「产能不设上限」）
──────────────────────────────────────────
  全文级 199 → **全部成篇**（每篇正文含研究问题/方法/核心结论/局限/项目价值五段）
  摘要级  75 → **全部成篇**（正文与来源串显式标注「摘要级 · 未核验全文」）
  升级卡  11 → 其 PMID 已在本站成篇（10-25 批以摘要级上线），按规则④**不重复建页**，
              改由 upgrade_paywall_1029.py 就地升级为全文级正文（父 cred 保留）

查重（规则④，硬规则）
────────────────────
扫描 news/*.html + papers/ + evidence/ + zh/** **正文全文**提取 DOI（882 个）
与 PMID（210 个）后逐条比对，不只看 data/doi-index.json（落后于页面）：
  · 274 条候选 DOI 站内 **0 命中**；PMID 命中的 11 条恰为升级卡片（已跳过）；
  · 另做 slug 级与批内查重。

时间标签（规则③）
────────────────
每篇正文首段输出「数据日期 2026-10-29 · 生成时间 YYYY-MM-DD HH:MM」。
数据日期取卡片期号 2026-10-29（PubMed edat 检索窗口 2026-10-27 ~ 2026-10-29）。

证据分级（沿用 10-25c 批口径）
────────────────────────────
A 人体原始数据研究（队列 / RCT / 横断面 / 多组学人体 / 汇总人体的 Meta 归 C）；
B 动物模型或体外细胞原始研究；C 非原始研究（综述、观点、理论框架、指南）。
"""
import html
import importlib.util
import json
import os
import re
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATE = "2026-10-29"
GEN_AT = datetime.now().strftime("%Y-%m-%d %H:%M")
DATA_DATE = "2026-10-29"
SRC_FT = ("IMA 知识库《文献层·文献监控卡片》2026-10-29 期 · 全文级"
          "（file_id dGBunAeRiRlm，下载实测 692,872 B）")
SRC_AB = ("IMA 知识库《文献层·文献监控卡片》2026-10-29 期 · 摘要级"
          "（file_id dGBunAeRiRlm，下载实测 692,872 B）")

MAP_FILES = ['/tmp/map_1029_1.json', '/tmp/map_1029_2.json',
             '/tmp/map_1029_3.json', '/tmp/map_1029_4.json',
             '/tmp/map_1029_5.json']

# 卡片主题 → 站内 8 个专题（首页 topic-grid 硬编码顺序，非这 8 个不入屋）
TOPIC_MAP = {
    "脑老化 / 神经退行 / 认知": "神经退行",
    "肌肉骨骼 / 衰弱 / 肌少症": "器官衰老",
    "方法学 / 生物标志物 / AI 建模": "方法与工具",
    "细胞衰老 / senolytics / SASP": "细胞衰老",
    "mTOR / 自噬 / 蛋白质稳态": "代谢与营养",
    "代谢 / 内分泌 / 肝肾老化的界面": "代谢与营养",
    "线粒体功能与氧化应激": "代谢与营养",
    "干预策略与临床试验": "生命历程",
    "血管 / 心血管老化": "器官衰老",
    "免疫衰老 / 炎症衰老": "免疫与炎症",
    "表观遗传时钟 / 生物学年龄": "表观遗传",
    "其他衰老相关": "生命历程",
    "生殖与发育起源": "生命历程",
    "皮肤 / 感官 / 口腔老化": "器官衰老",
    "微生物组及其代谢物": "代谢与营养",
    "NAD+ 代谢与补充策略": "代谢与营养",
    "干细胞 / 再生 / 重编程": "表观遗传",
}
# 个别条目按内容归到更贴切的专题
TOPIC_OVERRIDE = {
    "018": "代谢与营养", "092": "代谢与营养", "149": "代谢与营养",
    "002": "神经退行", "008": "神经退行", "016": "神经退行",
    "019": "免疫与炎症", "054": "免疫与炎症", "065": "器官衰老",
    "109": "表观遗传", "201": "表观遗传", "234": "细胞衰老",
    "226": "方法与工具", "266": "方法与工具", "213": "器官衰老",
    "182": "方法与工具",
    "122": "神经退行", "227": "神经退行",
}

REVIEW_TITLE_KW = [r'\breview\b', r'meta-analysis', r'meta analysis', r'\bscoping\b',
                   r'perspective', r'commentary', r'\bframework\b', r'hypothesis',
                   r'guidelines?', r'\broadmap\b', r'bibliometric', r'\bsurvey\b',
                   r'prospects', r'current concepts', r'theory of',
                   r'new insights', r'research advances', r'new developments',
                   r'updated guide', r'insight[s]? from', r'evidence gaps',
                   r' advances ', r'advances in', r'a synthesis', r'primer',
                   r'leçon', r'\bprotocol\b']
# 正文里「这是二次研究」的显式自陈（比关键词更稳）
REVIEW_BODY_KW = [r'this review', r'in this review', r'we review', r'we discuss how',
                  r'this article reviews', r'this commentary', r'this perspective',
                  r'narrative review', r'this scoping review', r'this systematic review',
                  r'this bibliometric', r'in this monograph', r'we surveyed']
OPINION_KW = [r'commentary', r'perspective', r'opinion', r'hypothesis',
              r'seven ways', r'integrating cure and care', r'-ocean']
ANIMAL_KW = [r'\bmice\b', r'\bmouse\b', r'\brats?\b', r'c\. elegans',
             r'drosophila', r'zebrafish', r'\bquail', r'in vitro',
             r'cell line', r'\bhela\b', r'organoid', r'\bxenograft',
             r'app/ps1', r'\b5xfad\b', r'\b3xtg\b', r'c57bl', r'\bsod1\b',
             r'but\b.*\-.*\bmice\b']
# 人工裁定：机器判不了的少数条，放在所有启发式之前，可强制任意级别
EV_OVERRIDE = {
    # 169 标题带 framework，但正文是 GBD 生态数据的概率模型再分析（有协变量、结局建模），属原始研究
    "169": "A",
}

HUMAN_KW = [r'\bparticipants\b', r'\bpatients\b', r'\bcohort\b',
            r'\brandomi[sz]ed\b', r'\brct\b', r'cross-sectional',
            r'longitudinal', r'uk biobank', r'\bnhanes\b', r'\bcharls\b',
            r'\bmedicare\b', r'\bshare\b', r'\belderly\b', r'older adults',
            r'\bhuman\b', r'case-cohort', r'nested case', r'health records',
            r'\bbeneficiaries\b', r'retrospective', r'\boutpatients?\b',
            r'older persons', r'master athletes', r'prospective cohort']


def grade(c):
    """与 10-25c 批同口径：A 人体原始 / B 临床前 / C 非原始研究。

    二手研究的判定只认两类硬信号：标题中的 review/meta-analysis 类词，或正文里
    「This review / We review」式的显式自陈。此前把 body 关键词（protocol、
    reviewed、framework）当作二次研究信号，实测把仑卡奈单抗真实世界队列
    （正文出现 "study protocol was reviewed"）误判成 C 级 —— looked-at-the-word
    而非 looked-at-the-work 的典型。A/B 侧同理：以「有没有人体数据」为准，
    混合证据（小鼠 + 人样本）按有人体数据的 A 处理。
    """
    low_t = c["title"].lower()
    if c["num"] in EV_OVERRIDE:      # 人工裁定优先于一切启发式
        return EV_OVERRIDE[c["num"]]
    blob = " ".join([c["method"], c["conclusion"], c["question"],
                     c["limit"]]).lower()
    # 最好用的信号是上游自己的标注：卡片「局限」字段写着
    # 「全文未设独立 limitations 节；结构上为综述/二次研究」的，直接按 C。
    if "二次研究" in (c["limit"] or "") or "综述" in (c["limit"] or ""):
        return "C"
    if any(re.search(k, low_t) for k in REVIEW_TITLE_KW):
        return "C"
    # 正文自陈（「we argue in this review」式）——比任何关键词都可靠
    body = " ".join([c["method"], c["conclusion"], c["question"]]).lower()
    if any(re.search(k, body) for k in REVIEW_BODY_KW):
        return "C"
    human = any(re.search(k, blob) for k in HUMAN_KW)
    animal = any(re.search(k, blob) for k in ANIMAL_KW)
    if human and not animal:
        return "A"
    if human and animal:          # 混合证据：以是否有人体数据为准
        return "A"
    return "B"


def tag_of(c, ev):
    t = c["title"].lower()
    if ev == "C":
        if any(re.search(k, t) for k in OPINION_KW):
            return "观点评论"
        if re.search(r'bibliometric|methods|assessment|guideline|survey|panel', t):
            return "方法学"
        return "综述解读"
    if ev == "B":
        return "基础研究"
    if re.search(r'randomi[sz]ed|\brct\b|trial', t):
        return "临床试验"
    if re.search(r'cross-sectional|case-control|Incidence|prevalence|burden|'
                 r'national|cohort|survey', t):
        return "流行病学"
    return "研究进展"


def already_on_site(doi, pmid, cache):
    return doi in cache["doi"] or (pmid and pmid in cache["pmid"])


def md2html(s):
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

    def wrap_ul(m):
        return '<ul>\n' + m.group(0) + '\n</ul>'
    txt = re.sub(r'(?:<li>.*?</li>\n?)+', wrap_ul, txt)
    return txt


def esc_plain(s, n=190):
    t = re.sub(r'\*\*(.+?)\*\*', r'\1', s or '')
    t = re.sub(r'\s+', ' ', t).strip(' -·')
    return t[:n]


def lit_src(c, abstract_only):
    bits = [f'<em>{html.escape(c["journal"])}</em>']
    if c["pmid"]:
        bits.append(f'PMID {c["pmid"]}')
    if c["doi"]:
        bits.append(f'DOI <a href="https://doi.org/{c["doi"]}" target="_blank" '
                    f'rel="noopener noreferrer">{c["doi"]}</a>')
    bits.append(('来源：' + SRC_AB + ' · 摘要级，未获取付费墙全文'
                 if abstract_only else
                 '来源：' + SRC_FT + ' · 全文已获取并通过归属校验'))
    return ' · '.join(bits)


def body_of(c, abstract_only):
    head = (f'<p><em>数据日期 {DATA_DATE} · 生成时间 {GEN_AT}</em></p>')
    if abstract_only:
        head += ('<p><strong>证据级别：摘要级</strong>。本条依据 PubMed 结构化摘要'
                 '与元数据撰写，付费墙全文未获取、未逐节核验，本站未做任何数值推算补全。</p>')
    parts = [head]
    for h, key in [("研究问题", "question"), ("方法", "method"),
                   ("核心结论", "conclusion"), ("局限", "limit"),
                   ("对本项目的价值", "value")]:
        if c[key]:
            parts.append(f'<h2>{h}</h2>' + md2html(c[key]))
    if c["ftsrc"]:
        parts.append('<h2>全文来源</h2>' + md2html(c["ftsrc"]))
    parts.append('<h2>原文题录</h2><ul>'
                 '<li>英文标题：' + html.escape(c["title"]) + '</li>'
                 '<li>期刊与标识：' + html.escape(c["journal"]) +
                 (f' · PMID {c["pmid"]}' if c["pmid"] else "") +
                 (f' · DOI {html.escape(c["doi"])}' if c["doi"] else "") +
                 '</li></ul>')
    return '\n\n'.join(parts)


# 规则④跨班次撞车撤回：03:30 播客班已于本轮之前把同一批文献（同 PMID）上线，
# 对方先发在前，我方不重复成篇（2026-10-29 推送前 DOI/PMID 全站扫库发现）。
# 编号 → 对方已在站的 slug
PUBLISHED_ELSEWHERE = {
    "057": "Aging-As-Failed-Resolution-Framework-Geroscience-IJMS-2026.html",
    "191": "FG1-Aromatic-Vinegar-Lifespan-Celegans-SKN1-IJMS-2026.html",
    "048": "Geroscience-Trial-Biomarker-Roadmap-Lifestyle-Aging-Biomolecules-2026.html",
    "186": "Myricitrin-Delays-Celegans-Aging-DAF16-SIR21-Antioxidants-2026.html",
    "092": "NMN-Does-Not-Prevent-Cardiac-Hypertrophy-Hypoxia-Mice-Nutrients-2026.html",
    "054": "NMN-Microglia-OGDR-NLRP3-Lipid-Droplet-Biomedicines-2026.html",
    "065": "P2X7-Antagonist-A740003-Cardiac-Senescence-Inflammaging-Pharmaceuticals-2026.html",
    "072": "Senescence-Malignancy-Axis-Inflammaging-Perspective-Antioxidants-2026.html",
    "185": "Skeletal-Muscle-Aging-Systemic-Aging-Contributor-Biomolecules-2026.html",
    "234": "Updated-Guide-Assessment-Mammalian-Cellular-Senescence-MolCells-2026.html",
}

def main():
    cards = {c["num"]: c for c in json.load(open('/tmp/cards_1029.json',
                                                 encoding='utf-8'))}
    M = {}
    for p in MAP_FILES:
        for num, slug, title, crumb in json.load(open(p, encoding='utf-8')):
            M[num] = (slug, title, crumb)
    print(f"映射条目 {len(M)} 条 · 卡片 {len(cards)} 张")

    # 站内已收录 DOI / PMID：扫正文全文（articles.json 的字段落后于页面）
    doi_re = re.compile(r'10\.\d{4,9}/[^\s"\'<>()\[\]]+')
    pm_re = re.compile(r'PMID\s*:?\s*(\d{6,8})')
    cache = {"doi": set(), "pmid": set()}
    import glob
    paths = (glob.glob(os.path.join(ROOT, 'news', '*.html'))
             + glob.glob(os.path.join(ROOT, 'papers', '*.html'))
             + glob.glob(os.path.join(ROOT, 'evidence', '*.html'))
             + glob.glob(os.path.join(ROOT, 'zh', '**', '*.html'), recursive=True))
    for p in paths:
        t = open(p, encoding='utf-8', errors='ignore').read()
        for d in doi_re.findall(t):
            cache["doi"].add(d.rstrip('.,;）)'))
        for m in pm_re.findall(t):
            cache["pmid"].add(m)

    arts = json.load(open(os.path.join(ROOT, 'data/articles.json'),
                          encoding='utf-8'))
    exist_slug = {a['slug'] for a in arts}

    A, dups, slugs_seen = {}, [], set(exist_slug)
    stat = {}
    for num, (slug, title, crumb) in M.items():
        c = cards[num]
        if num in PUBLISHED_ELSEWHERE:      # 规则④：已由 03:30 班先发，不重复成篇
            dups.append((num, M[num][0], f'03:30 播客班已先发 {PUBLISHED_ELSEWHERE[num]}'))
            continue
        # RERENDER=1 时跳过查重：页面本来就是本脚本上一轮写的，
        # 此时 DOI/slug 全部命中属于预期结果
        if not os.environ.get('RERENDER'):
            if slug in slugs_seen:
                dups.append((num, slug, 'slug 已存在'))
                continue
            if already_on_site(c["doi"], c["pmid"], cache):
                dups.append((num, slug, f'站内已收录 DOI {c["doi"]}'))
                continue
        ev = grade(c)
        topic = TOPIC_OVERRIDE.get(num) or TOPIC_MAP.get(c["topic"], "生命历程")
        A[slug] = dict(
            topic=topic, ev=ev, tag=tag_of(c, ev),
            title=title, crumb=crumb,
            desc=esc_plain(c["conclusion"] or c["question"]),
            source=lit_src(c, c["abstract_only"]),
            body=body_of(c, c["abstract_only"]),
            related=[],
            # 提示框里的来源声明要随「是否拿到全文」走，不能一刀切写「摘要级」
            notice_src=("abstract" if c["abstract_only"] else "fulltext"),
        )
        slugs_seen.add(slug)
        cache["doi"].add(c["doi"])
        if c["pmid"]:
            cache["pmid"].add(c["pmid"])
        stat[ev] = stat.get(ev, 0) + 1
    print(f"本批成篇 {len(A)} 篇 · 跳过重复 {len(dups)}")
    for n, s, w in dups:
        print(f"   ⏭ {n} {s} —— {w}")
    print("证据分级分布：", stat)
    # 覆盖率自检：274 条候选里任何一条没成篇都要逐条写明原因
    undone = [n for n in M if M[n][0] not in A]
    print(f"映射 {len(M)} 条 → 成篇 {len(A)} 条，未成篇 {len(undone)} 条：{undone}")

    sys.argv = ["gen_articles.py", ROOT, "/dev/null", DATE]
    _spec = importlib.util.spec_from_file_location(
        "ga", os.path.join(ROOT, "scripts", "gen_articles.py"))
    ga = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(ga)
    if os.environ.get('DRY'):
        print('DRY=1 —— 未写盘')
        return

    # 已存在的 slug（重渲染场景）：只就地重写页面，保留发布日期/面包屑/延伸阅读
    arts_p = os.path.join(ROOT, 'data/articles.json')
    arts = json.load(open(arts_p, encoding='utf-8'))
    byslug = {a['slug']: a for a in arts}
    for slug, m in list(A.items()):
        if slug not in byslug:
            continue
        page_p = os.path.join(ROOT, 'news', slug)
        old = open(page_p, encoding='utf-8', errors='ignore').read()
        crumb = byslug[slug].get('crumb') or byslug[slug]['title'][:12]
        cm = re.search(r'<span aria-current="page">(.*?)</span>', old)
        if cm:
            crumb = cm.group(1)
        rm = re.search(r'<ul class="related-list">(.*?)</ul>', old, re.S)
        rel = rm.group(1) if rm else ''
        ga.DATE = byslug[slug].get('date', DATE)
        open(page_p, 'w', encoding='utf-8', newline='').write(
            ga.build(slug, dict(m, crumb=crumb), rel))
        e = byslug[slug]
        e.update(desc=m['desc'], evidence=m['ev'], tag=m['tag'],
                 type=m['tag'], topic=m['topic'])
        A.pop(slug)
    json.dump(arts, open(arts_p, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=2)
    print(f"就地重渲染 {len(set(M[n][0] for n in M) & set(byslug))} 篇已存在页面")

    ga.A = A
    ga.main()


if __name__ == "__main__":
    main()
