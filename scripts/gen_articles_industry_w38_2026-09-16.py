#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_articles_industry_w38_2026-09-16.py —— 内容摄入第 25 批（行业情报周报 W38 补遗）

来源与判定
────────
事实源：行业层《行业情报周报_2026-09-16》（期号 2026-W38，file_id dVKsSOJcCMjU，
        实测 17,552 B，xlsx 三表：投融资表 / 管线进展表 / 监管动态表 + 编制说明）。
        覆盖窗口 2026-09-09 ~ 2026-09-16。

为什么是「补遗」
──────────────
本文件在游标里是**滚动更新**（file_id 不变、内容哈希变，seen 终裁 = NEW），
本轮重新下载核验后按增量处理。查重发现：
  · **监管动态表 7 条已由往期成篇收录** —— industry.json 事件 ev-2026-022
    （article_slug `Longevity-Regulatory-Payment-Boundaries-2026.html`，2026-10-16）
    的 source 明写「IMA 行业情报周报（2026-09-16）」，四道边界与中国「衰老非疾病」、
    FDA 终点收紧、加拿大 lecanemab 报销、长寿肽灰色地带全部命中 → **不重复上站**；
  · **投融资表 + 管线进展表 20 条站内 0 命中** → 真漏收，本批补齐。

产出口径
────────
· 1 篇总览文章（三表全文转 HTML 呈现，未做取舍，含编制说明的「待核实清单」）；
· data/industry.json 追加 20 条事件（8 融资 + 12 管线），
  每条带 source（来源域名）与 source_url（周报登记的一手链接），
  article_slug 指向本批总览文章（与站内既有 40 条事件同一口径：事件必须可溯源到页面）。

时间标签（规则③）
────────────────
正文首段输出「数据日期 2026-09-09 → 2026-09-16（周报覆盖窗口）
· 上站生成时间 YYYY-MM-DD HH:MM」。

纪律
────
· 金额、轮次、投资方、阶段均**照抄周报原文**，未做换算与加总；
· 周报自己标「待核实」的字段原样保留「待核实」字样，不补全；
· 投融资表末尾两条『—』行（邻近赛道 Inspiren、日期待核实的 Magnitude）
  按周报口径**不入库为事件**，仅在文章附录中列出。
"""
import html
import importlib.util
import json
import os
import re
import sys
from datetime import datetime
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATE = "2026-10-25"
GEN_AT = datetime.now().strftime("%Y-%m-%d %H:%M")
SLUG = "Industry-Weekly-W38-2026-09-16-Backfill.html"
SRC_NOTE = ("IMA 知识库《行业层·行业情报周报》2026-W38（2026-09-16）"
            " · file_id dVKsSOJcCMjU · 实测 17,552 B")

SHEETS = json.load(open('/tmp/ind_0916.json', encoding='utf-8'))


def esc(s):
    return html.escape('' if s is None else str(s))


def table_of(name, cols):
    rows = [r for r in SHEETS[name][1:] if any(x.strip() for x in r)]
    head = SHEETS[name][0]
    th = ''.join(f'<th>{esc(head[i])}</th>' for i in cols)
    tb = ''
    for r in rows:
        tds = ''
        for i in cols:
            v = r[i] if i < len(r) else ''
            if v.startswith('http'):
                tds += (f'<td><a href="{esc(v)}" target="_blank" '
                        f'rel="noopener noreferrer">原文</a></td>')
            else:
                tds += f'<td>{esc(v)}</td>'
        tb += '<tr>' + tds + '</tr>'
    return ('<div class="table-wrap"><table><thead><tr>' + th +
            '</tr></thead><tbody>' + tb + '</tbody></table></div>')


FIN = [r for r in SHEETS['投融资表'][1:] if any(x.strip() for x in r)]
PIPE = [r for r in SHEETS['管线进展表'][1:] if any(x.strip() for x in r)]
# 末尾两条「—」行不入库（邻近赛道 / 日期待核实），只在文章附录列出
FIN_CORE = [r for r in FIN if r[0].strip().isdigit()]
FIN_APPENDIX = [r for r in FIN if not r[0].strip().isdigit()]


def dom(url):
    try:
        return urlparse(url).netloc.replace('www.', '')
    except Exception:
        return '—'


def mk_events():
    evs = []
    n = 41  # 现有编号已排至 ev-2026-040，本批从 041 起排，避免撞号
    for r in FIN_CORE:
        (_, company, date, round_, amount, _val, focus, investor, note, url) = r[:10]
        typ = '收购' if '收购' in round_ or '收购' in company else '融资'
        date = re.sub(r'（.*?）', '', date).strip()
        evs.append(dict(
            id=f"ev-2026-{n:03d}", date=date, type=typ,
            entity=company.split('（')[0].strip(),
            headline=f"{company.split('（')[0].strip()}：{round_} {amount}".strip('： '),
            amount=amount if amount and amount != '未披露' else None,
            round=round_, counterparty=investor or None,
            evidence='C', source=dom(url), source_url=url,
            article_slug=SLUG))
        n += 1
    for r in PIPE:
        (_, company, date, proj, nature, key, stage, url) = r[:8]
        date = re.sub(r'（.*?）', '', date).strip()
        if '待核实' in date or len(date) != 10:
            continue              # 周报自标「日期待核实」的条目不入库，只在正文表格中列出
        ev = 'A' if url.startswith('https://doi.org') else 'C'
        evs.append(dict(
            id=f"ev-2026-{n:03d}", date=date, type='管线',
            entity=company.split('（')[0].strip(),
            headline=f"{company.split('（')[0].strip()}｜{proj}：{nature}",
            amount=None, round=None, counterparty=None,
            evidence=ev, source=dom(url), source_url=url,
            article_slug=SLUG))
        n += 1
    return evs


def main():
    # ── 1) 成篇 ────────────────────────────────────────────────
    appendix = ''
    for r in FIN_APPENDIX:
        appendix += (f'<li>{esc(r[1])} · {esc(r[2])} · {esc(r[3])} {esc(r[4])}'
                     f' · {esc(r[5]) if len(r) > 5 else ""}'
                     f' · <a href="{esc(r[9])}" target="_blank" '
                     f'rel="noopener noreferrer">原文</a></li>')

    body = (
        '<p><em>数据日期 2026-09-09 → 2026-09-16（周报覆盖窗口；周报运行日期 2026-09-16）'
        ' · 上站生成时间 ' + GEN_AT + '</em></p>\n\n'
        '<p><strong>为什么叫补遗。</strong>这份 W38 周报在网盘行业层是<strong>滚动更新文件</strong>'
        '（file_id 不变、内容哈希变），本轮按增量重新核验。它的<strong>监管动态表 7 条'
        '已由往期成篇收录</strong>——站内事件 <code>ev-2026-022</code>《四道边界：中国明确'
        '「衰老非疾病」、FDA 收紧终点标准、加拿大卡在支付、长寿肽仍在灰色地带》'
        '的溯源字段写的就是本期周报，四节内容全部命中，按查重规则④<strong>不重复上站</strong>。'
        '本文补齐的是剩下两张表：<strong>投融资表 8 条 + 管线进展表 12 条，共 20 条，'
        '站内 0 命中</strong>。</p>\n\n'
        '<h2>一、投融资表（8 条入库 + 2 条附录）</h2>\n\n'
        + table_of('投融资表', [0, 1, 2, 3, 4, 6, 7, 9]) + '\n\n'
        '<h3>附录：本期不入库的两条（周报口径）</h3>\n\n'
        '<ul>' + appendix + '</ul>\n\n'
        '<p>前者属<strong>老年照护科技外围</strong>（AI 跌倒监测，非衰老生物学），'
        '后者<strong>公告日期未能确认落在本窗口内</strong>。按周报编制说明「未获一手证据的字段'
        '一律标注待核实」，两者均不写入产业事件库。</p>\n\n'
        '<h2>二、管线进展表（12 条全部入库）</h2>\n\n'
        + table_of('管线进展表', [0, 1, 2, 3, 4, 5, 6, 7]) + '\n\n'
        '<h2>三、本期编制说明与已知局限（照录周报原文）</h2>\n\n'
        '<ul>\n'
        '<li>期号 <strong>2026-W38</strong>，运行日期 2026-09-16（GMT+8），'
        '覆盖窗口近 7 天 2026-09-09 ~ 09-16。</li>\n'
        '<li>检索源：公司新闻稿 / IR、SEC EDGAR、Business Wire / PR Newswire / GlobeNewswire。</li>\n'
        '<li>标注规则：<strong>未获一手证据的字段一律标注「待核实」，不做数值推算补全</strong>。</li>\n'
        '<li>待核实清单：① HexemBio 本轮新增金额（仅披露累计 $15.5M）；'
        '② Temple 收购 Longevous 实际公告时点（引用原文日期 2026-08-27）；'
        '③ Magnitude Biosciences 公告日期。</li>\n'
        '<li>已知局限：本周为<strong>不完整周</strong>（3 个交易日），主表采用近 7 天口径；'
        '私人市场融资有 1–2 周披露滞后；未覆盖日韩以等区域性未披露融资。</li>\n'
        '<li>缺口说明（周报自陈）：知识库内未检索到 SOP §4.4 模板文件，按项目既定三表结构执行。</li>\n'
        '</ul>\n\n'
        '<h2>读法提示</h2>\n\n'
        '<p>金额栏为公开披露原文，<strong>未做换算或加总</strong>；'
        '「累计总融资」不等于本轮金额。管线进展表的「阶段」以周报原文为准，'
        '其中伴侣动物临床（Genflow）、I 期（Retro）与商业化服务（Elysium、GlycanAge）'
        '不属于同一证据层级，不应并列解读。</p>')

    sys.argv = ["gen_articles.py", ROOT, "/dev/null", DATE]
    _spec = importlib.util.spec_from_file_location(
        "ga", os.path.join(ROOT, "scripts", "gen_articles.py"))
    ga = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(ga)

    ga.A = {SLUG: dict(
        topic="产业", ev="C", tag="产业动态",
        title="行业情报补遗 W38（2026-09-16）：8 笔融资与 12 条管线，钱往递送平台和保肌两处走",
        crumb="行业情报周报 W38 补遗",
        desc=("行业层 W38 周报（2026-09-09~09-16）滚动更新后的增量部分："
              "投融资 8 笔（Moonwalk $70M B 轮领跑，脂肪靶向 siRNA）、管线进展 12 条"
              "（Insilico Rentosertib III 期首例给药、Genflow 犬试验达主要终点、"
              "BioViva 双基因疗法获美国专利）。监管动态一节已由往期成篇，此处不重复。"),
        source=('<em>' + SRC_NOTE + '</em> · 覆盖窗口 2026-09-09 → 2026-09-16'
                ' · <strong>本文为二次汇编，金额与阶段均照录周报原文，未作换算与加总</strong>'),
        body=body, related=[])}
    ga.main()

    # ── 2) 行业事件库追加 ──────────────────────────────────────
    p = os.path.join(ROOT, 'data', 'industry.json')
    data = json.load(open(p, encoding='utf-8'))
    have = {(e.get('entity'), e.get('date'), e.get('headline')) for e in data['events']}
    added = []
    for e in mk_events():
        k = (e.get('entity'), e.get('date'), e.get('headline'))
        if k in have:
            continue
        data['events'].append(e)
        added.append(e['id'])
    data['events'].sort(key=lambda e: e.get('date', ''))
    json.dump(data, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f"industry.json 事件 {len(data['events'])} 条（本批新增 {len(added)}："
          + (added[0] + '–' + added[-1] if added else '无') + '）')


if __name__ == "__main__":
    main()
