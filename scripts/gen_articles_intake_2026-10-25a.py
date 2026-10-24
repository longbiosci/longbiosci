#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_articles_intake_2026-10-25a.py —— 内容摄入第 21 批（2026-10-25 05:30 巡检）

消化对象
────────
《文献监控_2026-10-25_卡片》（file_id dnqNDVpqTrjt，实测 212,025 B）
—— 114 张卡片（47 全文级 + 69 摘要级）。本批先成篇 **全文级 45 篇**
（另 2 篇全文级经 DOI 硬核验站内已收录，判重复跳过；摘要级 69 条见
同批 b 脚本或入档，视时间窗而定）。

为什么先做全文级
────────────────
全文级卡片是「已下载全文并逐节核验」的档位，含样本量、效应量与区间，
可以照抄原文定量；摘要级只能转述摘要，两者在可引用性上不是一档。
05:30 班要求 09:00 前上线，故按档位排序投入产能，不是控量。

查重（规则④，硬规则）
──────────────────────
不是只看 data/doi-index.json（456 条，落后于页面），而是**扫描 news/*.html
全文**提取 DOI（915 个）+ PMID（82 个）后逐条比对：
  · 47 篇全文级中 **2 篇站内已有**（DOI 命中）→ 跳过并计数；
  · 45 篇净新增 → 成篇。
这与 2026-10-24 记档的坑一致：查重必须扫正文全文，不能只扫 articles.json 字段。

时间标签（规则③）
────────────────
每篇正文首段输出「数据日期 YYYY-MM-DD · 生成时间 YYYY-MM-DD HH:MM」。
数据日期取卡片期号 2026-10-25（检索窗口 2026-10-22~2026-10-25）。

纪律
────
· 研究问题 / 方法 / 结论 / 局限 / 价值 五段全部**照抄卡片原文**，未做推断与润色；
· 卡片未给的定量一律不补；
· 证据分级：人体研究 A、临床前（动物/体外）B；综述与政策研究按其证据性质归 B。
"""
import html
import importlib.util
import json
import os
import re
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATE = "2026-10-25"
GEN_AT = datetime.now().strftime("%Y-%m-%d %H:%M")
DATA_DATE = "2026-10-25"
SRC_CARD = ("IMA 知识库《文献层·文献监控卡片》2026-10-25 期"
            "（file_id dnqNDVpqTrjt，实测 212,025 B）")

cards = json.load(open('/tmp/cards_1025.json', encoding='utf-8'))
BY_NUM = {c['num']: c for c in cards}

# 编号 → (slug, 中文标题, 面包屑短句, topic, ev, tag)
M = {
 "01": ("Heart-Failure-Circulating-Vascular-NAD-CD38-2026.html",
        "心衰小鼠的 NAD⁺：循环在降，血管在烧，CD38 随病程一路升高",
        "心衰中的 NAD⁺ 双室重塑", "NAD+与sirtuin", "B", "基础研究"),
 "02": ("Giant-Panda-Gut-Microbiome-Longevity-2026.html",
        "大熊猫的长寿菌群：年龄相关的肠型转换与功能轨迹",
        "大熊猫肠道菌群与年龄", "代谢与营养", "B", "基础研究"),
 "03": ("Hair-Graying-Melanocyte-Stem-Cell-2026.html",
        "头发为什么变白：毛囊黑色素细胞储库的不可逆，与那道窄门",
        "白发与黑色素细胞干细胞", "干细胞", "B", "综述解读"),
 "04": ("Exercise-Grip-Strength-Meta-Older-Adults-2026.html",
        "运动能把手握力提多少：一份 meta 给出的合并效应 SMD 0.47",
        "运动干预与老年人握力", "生命历程", "A", "研究进展"),
 "05": ("Young-Plasma-Exosome-YOD1-M2-Bone-2026.html",
        "年轻血浆外泌体递送 YOD1：经 M2 极化与 mTOR 改写骨稳态",
        "年轻血浆外泌体与骨", "器官衰老", "B", "基础研究"),
 "06": ("Exosome-Skin-Aging-Therapy-Review-2026.html",
        "外泌体抗皮肤衰老：机制说得通，临床证据还很薄",
        "外泌体疗法与皮肤老化", "器官衰老", "B", "综述解读"),
 "07": ("Maternal-ACE-Epigenetic-Aging-Children-2026.html",
        "母亲的童年逆境，会不会写进孩子的表观遗传时钟",
        "代际表观遗传嵌入", "表观遗传", "A", "研究进展"),
 "08": ("Antisense-Oligo-Glycosylation-Keratinocyte-Senescence-2026.html",
        "敲低糖基化基因，能否改写角质形成细胞的衰老表型",
        "糖基化与细胞衰老", "细胞衰老", "B", "基础研究"),
 "09": ("ARG2-Osteoblast-Senescence-Mitophagy-2026.html",
        "ARG2 踩下线粒体自噬的刹车：成骨细胞衰老与骨丢失的新轴",
        "ARG2 与成骨细胞衰老", "细胞衰老", "B", "基础研究"),
 "10": ("Frailty-Hepatocellular-Carcinoma-Outcomes-2026.html",
        "肝癌里的衰弱：一个被低估的结局预测因子",
        "肝细胞癌与衰弱", "临床与转化", "A", "临床进展"),
 "11": ("Cellular-Senescence-Multiple-Sclerosis-2026.html",
        "多发性硬化为什么会走向进展期：细胞衰老作为缺失的一环",
        "细胞衰老与多发性硬化", "细胞衰老", "B", "综述解读"),
 "12": ("GZMK-CD8-T-Acinar-Senescence-Salivary-2026.html",
        "GZMK⁺CD8⁺ T 细胞让腺泡细胞衰老：口干的一条免疫路径",
        "GZMK⁺CD8⁺ T 细胞与唾液腺", "免疫与炎症", "B", "基础研究"),
 "13": ("Regional-BBB-Dysfunction-Cognition-2026.html",
        "血脑屏障漏在哪里，认知就掉在哪里",
        "区域血脑屏障功能障碍与认知", "神经退行", "A", "研究进展"),
 "14": ("Inducible-NAD-Deficiency-Multi-Systemic-Mice-2026.html",
        "把 NAD 耗竭做成开关：ANDY 小鼠的多系统衰老与寿命缩短",
        "诱导性 NAD 缺乏小鼠", "NAD+与sirtuin", "B", "基础研究"),
 "15": ("Brain-Age-Gap-Cognitive-Decline-2026.html",
        "脑龄提前多少，记忆就掉多快：BAG 与纵向认知下降",
        "脑龄差与认知轨迹", "神经退行", "A", "研究进展"),
 "16": ("DCTN2-HCC-Senescence-TRIM21-MST2-2026.html",
        "DCTN2：一个被 TP53 突变抬高的肝癌衰老相关基因",
        "DCTN2 与肝癌细胞衰老", "细胞衰老", "B", "基础研究"),
 "17": ("Dog-Lifespan-Therapeutics-Regulatory-2026.html",
        "先给狗用的延寿药：犬用寿命治疗正在给人类 gerotherapeutics 铺路",
        "犬寿命治疗药物的监管启示", "临床与转化", "B", "综述解读"),
 "18": ("Sirtuin-Family-Network-Review-2026.html",
        "sirtuin 不是单一长寿开关，而是一张区室化网络",
        "sirtuin 家族的机制与治疗", "NAD+与sirtuin", "B", "综述解读"),
 "19": ("NIR-Probe-Beta-Gal-Inhibitor-Senolytics-2026.html",
        "用近红外探针筛衰老细胞：从天然 β-gal 抑制剂到动脉粥样硬化",
        "近红外探针筛选衰老细胞", "方法与工具", "B", "方法学"),
 "20": ("WGS-Senescence-Variants-Mice-2026.html",
        "全基因组测序找衰老相关变异：Cic、Gsta6 与 Bfsp1 三个候选",
        "全基因组测序与衰老变异", "方法与工具", "B", "基础研究"),
 "21": ("Global-Cancer-Burden-Middle-Aged-Elderly-2026.html",
        "中老年癌症负担三十年：老龄化是发病增长的主要驱动",
        "全球中老年癌症负担趋势", "生命历程", "A", "研究进展"),
 "22": ("Aging-Kidney-Senescence-Bibliometric-2026.html",
        "肾脏衰老与纤维化的文献计量图谱：谁在做、做到哪一步",
        "肾脏衰老文献计量", "器官衰老", "B", "方法学"),
 "23": ("EPA-DHA-NRF2-Beta-Cell-Resilience-2026.html",
        "EPA 与 DHA 给 β 细胞装上一条 NRF2 韧性回路",
        "EPA/DHA 与 β 细胞保护", "代谢与营养", "B", "基础研究"),
 "24": ("Plantar-Flexor-Torque-Gait-Complexity-Aging-2026.html",
        "老年人的步态与扭矩复杂度绑在了一起：运动控制的降维",
        "步态与扭矩复杂度随龄变化", "生命历程", "A", "研究进展"),
 "25": ("Cervical-Spinal-Cord-Morphometry-Lifespan-2026.html",
        "颈髓也有生长曲线：首张覆盖全生命周期的形态学图表",
        "颈髓形态学的生命周期图谱", "神经退行", "A", "研究进展"),
 "26": ("Ferro-Aging-Bone-Joint-Degeneration-2026.html",
        "ferro-aging：把铁代谢与骨关节退变连起来的统一框架",
        "铁老化与骨关节退变", "器官衰老", "B", "综述解读"),
 "27": ("Plasma-Immune-Senescence-Biomarkers-Cohort-2026.html",
        "六种血浆标志物先于事件升高：免疫调节与衰老的提前信号",
        "血浆免疫衰老标志物", "免疫与炎症", "A", "研究进展"),
 "28": ("circRNA-Partial-Reprogramming-MSC-2026.html",
        "环状 RNA 做部分重编程：MSC 变年轻，但不会变成 iPSC",
        "circRNA 部分重编程 MSC", "部分重编程", "B", "基础研究"),
 "29": ("Apelin13-GATA4-Neuronal-Senescence-Autophagy-2026.html",
        "Apelin-13 不清除 ROS，而是恢复自噬：阻断 GATA4 神经元衰老的另一条路",
        "Apelin-13 与神经元衰老", "神经退行", "B", "基础研究"),
 "30": ("Hearing-Threshold-Sarcopenia-Sex-Specific-2026.html",
        "高频听力越差，男性肌少症 odds 越高：1,032 人的性别差异",
        "听力阈值与肌少症", "生命历程", "A", "研究进展"),
 "31": ("Motor-Neuron-Vulnerability-Aging-2026.html",
        "老年运动神经元为什么选择性易感：MMP-9 与 Chodl 的随龄轨迹",
        "运动神经元的选择性易感性", "神经退行", "B", "基础研究"),
 "32": ("Cladribine-Older-MS-Real-World-2026.html",
        "50 岁以上 MS 患者用克拉屈滨：115 例真实世界的两年 ARR",
        "克拉屈滨在 older MS 的真实世界数据", "临床与转化", "A", "临床进展"),
 "33": ("National-Healthy-Longevity-Strategies-2026.html",
        "同一份联合国决议，四条实施路径：各国健康长寿战略比较",
        "国家健康长寿战略比较", "生命历程", "B", "综述解读"),
 "34": ("Hematopoietic-Loss-of-X-Chromosome-Women-2026.html",
        "女性造血系统的 X 染色体丢失：55 岁以上超过 10% 可检出",
        "女性造血 X 染色体丢失", "表观遗传", "A", "研究进展"),
 "35": ("PTSD-Metabolic-Syndrome-Epigenetic-Age-2026.html",
        "腰围越大表观年龄越高，PTSD 越重反而越低：一个负向交互",
        "PTSD、代谢综合征与表观年龄", "表观遗传", "A", "研究进展"),
 "36": ("Vitamin-A-E-Gut-Microbiota-Children-2026.html",
        "维生素 A/E 与学龄儿童肠道菌群：缺乏普遍，菌群差异有限",
        "维生素状态与儿童肠道菌群", "代谢与营养", "A", "研究进展"),
 "37": ("Aging-Tumor-Microenvironment-Oral-Cancer-2026.html",
        "衰老如何为口腔癌搭建促肿瘤生态位",
        "衰老与口腔癌肿瘤微环境", "免疫与炎症", "B", "综述解读"),
 "38": ("NAD-Supplementation-Wound-Healing-Case-2026.html",
        "常规处理无效的伤口，口服 NAD⁺ 补充后快速愈合",
        "NAD⁺ 补充与伤口愈合", "NAD+与sirtuin", "B", "临床进展"),
 "39": ("Out-of-Home-Activities-Healthy-Ageing-2026.html",
        "出门做什么、去哪儿：老年人日常活动的「内容 × 场景」框架",
        "外出活动与健康老龄化", "生命历程", "A", "研究进展"),
 "40": ("Meat-Consumption-Frailty-Community-2026.html",
        "吃够推荐量肉类的人，衰弱可能性低三成：社区人群的 OR 0.70",
        "肉类摄入与衰弱", "代谢与营养", "A", "研究进展"),
 "41": ("Adropin-Endothelin-Vascular-Aging-T2DM-2026.html",
        "adropin 与内皮素的失衡：ENHO–EDN1 变异与早期血管老化",
        "adropin–内皮素轴与血管老化", "血管衰老", "A", "研究进展"),
 "42": ("Lactiplantibacillus-HY7715-AGEs-BBB-Aging-2026.html",
        "热灭活的益生菌也有效：HY7715 降低 AGEs 与血脑屏障渗漏",
        "植物乳杆菌 HY7715 与衰老", "代谢与营养", "B", "基础研究"),
 "43": ("Senescence-Antiviral-Interferon-IPF-2026.html",
        "衰老让 IPF 成纤维细胞的抗病毒应答变了形",
        "衰老与抗病毒干扰素应答", "免疫与炎症", "B", "基础研究"),
 "44": ("Pentahydroxyflavone-Metformin-Hepatic-AMPK-2026.html",
        "五羟基黄酮联合二甲双胍：AMPK/SREBP-1c/SCD1 上的肝保护",
        "PHF 与二甲双胍的肝脏保护", "代谢与营养", "B", "基础研究"),
 "45": ("Cilia-Centered-NAD-Signaling-Lysosome-2026.html",
        "纤毛是 NAD⁺ 信号的中枢：耗竭先伤纤毛，再伤溶酶体",
        "纤毛中心的 NAD⁺ 信号网络", "NAD+与sirtuin", "B", "基础研究"),
}


def md2html(s):
    """卡片字段是 markdown 片段：加粗 + 列表项 + 段落。"""
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
    # 列表项补外层 <ul>
    txt = re.sub(r'(<li>.*?</li>)(\n<li>)', r'\1\2', txt)

    def wrap_ul(m):
        return '<ul>\n' + m.group(0) + '\n</ul>'
    txt = re.sub(r'(?:<li>.*?</li>\n?)+', wrap_ul, txt)
    return txt


def esc_plain(s, n=200):
    """desc：去 markdown 标记后截断。"""
    t = re.sub(r'\*\*(.+?)\*\*', r'\1', s or '')
    t = re.sub(r'\s+', ' ', t).strip(' -·')
    return t[:n]


def lit_src(c):
    j = re.sub(r'\*\*', '', c['journal'] or '')
    bits = [f'<em>{html.escape(j)}</em>']
    if c['pmid']:
        bits.append(f'PMID {c["pmid"]}')
    if c['doi']:
        bits.append(f'DOI <a href="https://doi.org/{c["doi"]}" target="_blank" '
                    f'rel="noopener noreferrer">{c["doi"]}</a>')
    bits.append(f'来源：{SRC_CARD} · 全文已获取并核验')
    return ' · '.join(bits)


def body_of(c):
    parts = [f'<p><em>数据日期 {DATA_DATE} · 生成时间 {GEN_AT}</em></p>']
    if c['question']:
        parts.append('<h2>研究问题</h2>' + md2html(c['question']))
    if c['method']:
        parts.append('<h2>方法</h2>' + md2html(c['method']))
    if c['conclusion']:
        parts.append('<h2>核心结论</h2>' + md2html(c['conclusion']))
    if c['limit']:
        parts.append('<h2>局限</h2>' + md2html(c['limit']))
    if c['value']:
        parts.append('<h2>对本项目的价值</h2>' + md2html(c['value']))
    en_title = html.escape(c['title'])
    jn = html.escape(re.sub(r'\*\*', '', c['journal'] or ''))
    parts.append('<h2>原文题录</h2><ul>'
                 '<li>英文标题：' + en_title + '</li>'
                 '<li>期刊与标识：' + jn + '</li>'
                 '</ul>')
    return '\n\n'.join(parts)


def main():
    arts = json.load(open(os.path.join(ROOT, 'data/articles.json'), encoding='utf-8'))
    existing = {a['slug'] for a in arts}
    A = {}
    dup_here = []
    for num, (slug, title, crumb, topic, ev, tag) in M.items():
        if slug in existing or os.path.exists(os.path.join(ROOT, 'news', slug)):
            dup_here.append(slug)
            continue
        c = BY_NUM[num]
        A[slug] = dict(
            topic=topic, ev=ev, tag=tag,
            title=title, crumb=crumb,
            desc=esc_plain(c['conclusion'] or c['question'], 190),
            source=lit_src(c),
            body=body_of(c),
            related=[],
        )
    print(f"本批成篇 {len(A)} 篇 · 站内/本批已存在跳过 {len(dup_here)}")
    if dup_here:
        print('  跳过：', dup_here)

    sys.argv = ["gen_articles.py", ROOT, "/dev/null", DATE]
    _spec = importlib.util.spec_from_file_location(
        "ga", os.path.join(ROOT, "scripts", "gen_articles.py"))
    ga = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(ga)
    ga.A = A
    ga.main()


if __name__ == "__main__":
    main()
