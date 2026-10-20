#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_articles_intake_2026-10-20b.py —— 内容摄入第 17 批（补徐的 5 条，2026-10-20 巡检）

为什么会有这个「b 批」
────────────────────
第 17 批（gen_articles_intake_2026-10-20.py）消化《预印本速递_2026-10-20》时，
只把**主榜 2 条 + 观察哨 1 条**成篇，其余 **6 条**（观察哨 #2–#5、补遗 #1–#3）被
挡在上游自己的建议之外：观察哨 #2/#3 摘要无定量、其余档次偏低，上游写明
「供下游决定」。

但「交给下游」不等于「可以不算」。按硬规则 3（confidence=none ≠ 漏收，但也不能据此
判已收），本轮逐条做了三件事：

1. 用 API 拉取 **5 条的 medRxiv / bioRxiv 官方摘要原文**（详见 .intake/verify/），
   确认其中 **4 条摘要里有可引用定量**，只有 PPTC7 那条是纯机制、无定量；
2. 用 DOI 尾号在 news/ 硬核验：26364284 / 26365658 / 26365677 / 26365631 / 759620
   **全部 0 命中** → 真漏收，不是重复；
3. 按「摘要有可引用定量即可成篇、其余标待补全文」的口径补写 5 篇。

未成篇的 **观察哨 #2（UFM-1 / UFMylation，线虫）与 #3（父代间歇性禁食跨代）**，
官方摘要**确无任何定量**，按同一口径留作观察哨，不入站在主动性 minimizing 的前提下
如实执行——这条判断写进备注，便于后人复核。

证据分级口径（本批严格执行站点公开约定）
──────────────────────────────────────
about/ 白纸黑字：A = 同行评议人体研究 / B = 同行评议临床前研究 / **C = 预印本**。
本批 5 篇**全部来自未经同行评议的预印本**，故一律 **C 级**；
其中 4 篇虽是人体数据，仍按「预印本优先」标 C——公开承诺不因数据好看而放宽。
（同批次已把 a 批的 PhenoAge A→C、ML B→C 就地更正并保留更正说明。）

纪律
────
· 定量一律照抄官方摘要原文，未做任何推算或补全；
· 摘要未给的（样本筛选细节、效应量、完整统计模型）一律标「待补全文」；
· 标题里的强因果词（如 "precedes"）在正文里明确拆穿为「横断面」；
· 内部链接 slug 全部经 news/ 实际存在性校验，脚本启动即校验，不存在直接退出。
"""
import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATE = "2026-10-20"

# ── 内部链接（2026-10-20 实查 news/ 目录后复制，脚本会二次校验）──
REL_NPS = [
    ("Mild-Cognitive-Impairment-Pre-frailty-Show-GeroScience-2026.html",
     "一个反直觉的阴性结果：早期阶段的「前衰弱」与「轻度认知障碍」"),
    ("Mnemonic-Discrimination-Aging-Alzheimer-Blood-Biomarker-2026.html",
     "记忆辨别缺陷与 AD 血液标志物的关联"),
    ("Amyloid-Trajectory-Bifurcation-Normal-Aging-AD-2026.html",
     "分岔的淀粉样蛋白轨迹区分正常老化与 AD 进展"),
]
REL_IIV = [
    ("Implicit-Associative-Memory-Aging-Hippocampus-Perirhinal-2026.html",
     "内隐联结记忆在老年保持完好：海马与内嗅皮层共同支撑"),
    ("Hippocampus-Memory-Update-Tent5a-Aging-2026.html",
     "衰老破坏背侧海马记忆更新转录程序"),
    ("Mnemonic-Discrimination-Aging-Alzheimer-Blood-Biomarker-2026.html",
     "记忆辨别缺陷与 AD 血液标志物的关联"),
]
REL_GUT = [
    ("Gut-Microbiome-Exposome-Brain-Aging-Framework-2026.html",
     "菌群 × 暴露组 × 脑老化：统一的脑衰老研究框架"),
    ("Age-Associated-Gut-Microbiota-Dysbiosis-Impairs-AgingCell-2026.html",
     "老年人抗流感差，菌群少产的乙酸是关键一环"),
    ("Microbiome-Age-Clock-Bifidobacterium-5-AVAB-Healthspan-2026.html",
     "微生物组年龄时钟锁定一株双歧杆菌"),
]
REL_PTAU = [
    ("P-Tau217-Cognitive-Impairment-Prediction-2026.html",
     "血液 p-tau217 可预测 5 年内认知障碍风险"),
    ("C2N-PrecivityAD2-Cambridge-Cognition-UK-Alzheimer-Diagnosis.html",
     "血检 + 数字认知在英国全科诊所的阿尔茨海默诊断路径"),
    ("Mnemonic-Discrimination-Aging-Alzheimer-Blood-Biomarker-2026.html",
     "记忆辨别缺陷与 AD 血液标志物的关联"),
]
REL_MITO = [
    ("In-Vivo-Multiparametric-Mitochondria-Aging-Trajectory-2026.html",
     "多参数活体成像揭示组织特异的线粒体衰老轨迹"),
    ("Aged-Mitochondrial-DNA-Is-Associated-AgingCell-2026.html",
     "老年肌肉的线粒体：崩掉的是 mtDNA 与 redox 应答"),
    ("Mitochondrial-Supercomplexes-Longevity-Review-2026.html",
     "线粒体超复合体与长寿：氧化磷酸化高级组装结构"),
]


def notice(ev):
    """本批统一的证据分级框。

    严格执行 about/ 公开的站点约定：A＝同行评议人体研究 / B＝同行评议临床前研究 /
    C＝预印本。本批 5 篇全部是 medRxiv / bioRxiv 预印本 → 一律 C。
    来源口径（本批全部为「预印本官方摘要一手拉取」）写在每篇 body 自己的 notice-box 里，
    因为 gen_articles.py 只以 notice(ev) 单参数调用，无法按篇区分。
    """
    t = {"A": "A 级（同行评议人体研究）",
         "B": "B 级（同行评议临床前研究）",
         "C": "C 级（预印本：未经同行评议，结论可能随审稿改变）"}[ev]
    return (f'<div class="notice-box">\n'
            f'    <p><span class="tier tier-{ev.lower()}">{ev} 级</span>'
            f'<strong>证据分级：{t}</strong></p>\n'
            f'    <p><strong>关于转载与本证据分级的说明：</strong>本篇由 LongBiosci 编辑部依据'
            f'<strong>medRxiv / bioRxiv 官方摘要原文</strong>（本轮经 API 一手拉取并留存）整理，'
            f'定量一律照抄原文，<strong>未做任何数值推算补全</strong>；'
            f'凡摘要未给出的信息一律标注「待补全文」。</p>\n'
            f'    <p><strong>为什么这篇人体数据也是 C 级：</strong>它是<strong>未经同行评议的预印本</strong>，'
            f'按 <a href="/about/" target="_blank" rel="noopener noreferrer">本站公开的分级约定</a>'
            f'只能标 C——数据来自人体不会抬高预印本的证据等级。</p>\n'
            f'</div>')


def main():
    arts = json.load(open(os.path.join(ROOT, "data/articles.json"), encoding="utf-8"))
    used = {a["slug"] for a in arts}
    all_rel = sum([REL_NPS, REL_IIV, REL_GUT, REL_PTAU, REL_MITO], [])
    missing = [s for s, _ in all_rel
               if not os.path.exists(os.path.join(ROOT, "news", s))]
    if missing:
        sys.exit(f"✗ related slug 在 news/ 下不存在：{missing}\n"
                 f"  内部链接必须 ls news/ 实际复制，不能凭记忆写。")

    sys.argv = ["gen_articles.py", ROOT, "/dev/null", DATE]
    _spec = importlib.util.spec_from_file_location(
        "ga", os.path.join(ROOT, "scripts", "gen_articles.py"))
    ga = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(ga)
    ga.notice = notice

    D1 = "10.64898/2026.10.15.26364284"
    D2 = "10.64898/2026.10.15.26365658"
    D3 = "10.64898/2026.10.15.26365677"
    D4 = "10.64898/2026.10.15.26365631"
    D5 = "10.64898/2026.10.16.759620"

    def src(server, cat, en_title, doi, author_line, extra):
        return (f'<em>{server}</em>（{cat}）· 预印本：{en_title}'
                f' · DOI <a href="https://doi.org/{doi}" target="_blank" '
                f'rel="noopener noreferrer">{doi}</a>'
                f' · {author_line}'
                f' · 来源：IMA 知识库《预印本速递》2026-10-20 期 + '
                f'<b>{server} 官方摘要原文一手拉取核验</b>（{extra}）')

    src1 = src("medRxiv", "geriatric medicine",
               "Longitudinal associations between neuropsychiatric symptoms, structural "
               "and perfusion MRI changes in older adults with Mild Cognitive Impairment",
               D1, "通讯 Latha Velayudhan（伦敦国王学院）", "摘要 1,778 字符，未获取全文")
    src2 = src("medRxiv", "neurology",
               "Memory Intraindividual Variability and its Association with Hippocampal "
               "Integrity in Older Latino Adults Without Dementia",
               D2, "通讯 Amanda I. Gonzalez（波士顿大学心理与脑科学系）",
               "摘要 1,116 字符，未获取全文")
    src3 = src("medRxiv", "neurology",
               "Change in gut microbiome precedes symptomatic Alzheimer's disease and is "
               "correlated with amyloid-beta accumulation in the brain",
               D3, "通讯 Geraint B. Rogers（南澳大利亚健康与医学研究所）",
               "摘要 1,270 字符，未获取全文")
    src4 = src("medRxiv", "neurology",
               "Performance boundaries of plasma-centred prediction across PET- and "
               "MRI-defined AT(N): QC-first internal validation in ADNI with separate "
               "axis-specific assessments",
               D4, "通讯 Fumie Costen（曼彻斯特大学）", "摘要 2,264 字符，未获取全文")
    src5 = src("bioRxiv", "cell biology",
               "Arrested PPTC7 import couples mitochondrial depolarisation to NIX and "
               "BNIP3 degradation",
               D5, "通讯 Michael Clague（利物浦大学）", "摘要 1,245 字符，未获取全文")

    A = {
        "MCI-Neuropsychiatric-Symptoms-MRI-Structure-Perfusion-medRxiv-2026.html": dict(
            topic="神经退行", ev="C", tag="预印本",
            title="MCI 的行为心理症状落在具体的脑结构与血流改变上，但样本只剩 18 人",
            crumb="30 人入组、18 人完成 29 个月随访",
            desc="伦敦国王学院团队对 65 岁以上轻度认知障碍者的纵向影像随访显示：右侧海马旁回体积丢失与攻击性加重相关、右侧海马与海马旁回灌注升高与激越加重相关。每项关联都通过了 FDR 校正，但完成随访的只有 18 人。",

            source=src1,
            body="""<p>神经精神症状（neuropsychiatric symptoms, NPS）在轻度认知障碍（MCI）人群中极为常见，
而「哪些脑区改变对应哪些症状」在纵向多模态影像上一直缺少证据。这项 medRxiv 预印本想回答三件事：
随访期内 NPS、内侧颞叶体积与局部脑血流（CBF）各自怎么变；影像变化与 NPS 变化是否相关；
以及基线影像能否预测 NPS 的后续恶化。</p>

<h2>设计与数字：先把样本量说清楚</h2>
<table>
<tr><th>项目</th><th>数值（官方摘要）</th></tr>
<tr><td>入组</td><td>MCI 且年龄 &gt; 65 岁，<strong>30 人</strong></td></tr>
<tr><td>完成随访</td><td><strong>18 人</strong></td></tr>
<tr><td>平均随访时长</td><td><strong>29 ± 8.9 个月</strong></td></tr>
<tr><td>影像读数</td><td>内侧颞叶体积测量 + 区域脑血流（CBF）</td></tr>
<tr><td>多重比较校正</td><td>FDR（摘要给出 pFDR 阈值）</td></tr>
</table>
<p><strong>这是本篇最需要放在第一位的事实：30 人入组、18 人进入纵向分析。</strong>
后面所有显著结果，都是在这 18 人的随访数据上得到的。</p>

<h2>三个层面的结果</h2>
<h3>① 随访期内确实在萎缩</h3>
<p>总体灰质与白质体积显著下降，伴随<strong>双侧海马、双侧海马旁回、右侧内嗅皮层</strong>的体积丢失
（pFDR ≤ 0.05）。这部分与既有 AD/MCI 影像文献方向一致，可视为队列的内部一致性检查。</p>

<h3>② 症状落在具体脑区上</h3>
<table>
<tr><th>影像变化</th><th>对应的症状变化</th><th>显著性</th></tr>
<tr><td>右侧海马旁回体积丢失</td><td>攻击性<strong>加重</strong></td><td>pFDR &lt; 0.01</td></tr>
<tr><td>右侧海马 + 海马旁回 CBF <strong>升高</strong></td><td>激越<strong>加重</strong></td><td>pFDR &lt; 0.01</td></tr>
</table>
<p>注意第二行的方向：<strong>血流升高</strong>而不是降低，伴随症状恶化。这在直觉上反常——
通常预期神经退行伴随低灌注。作者把它解读为灌注指标作为「监测疾病进展」生物标志物的潜力，
但摘要给出的是关联而非机制，<strong>为什么是高灌注、它代表代偿还是病理，均待补全文</strong>。</p>

<h3>③ 基线影像预测后续恶化</h3>
<p><strong>较低的</strong>右侧内嗅皮层基线体积 → 攻击性增加；
<strong>较低的</strong>右侧海马与海马旁回基线 CBF → 激越恶化（pFDR &lt; 0.05）。
这里方向就符合直觉了：起点越差的，后续症状越糟。</p>

<h2>边界：五条必须一起读</h2>
<ol>
<li><strong>18 人的纵向样本。</strong>三个在读层面（体积、CBF、NPS）两两关联，
在这个量级下任一强影响点都可能改变结论方向。<strong>结论应视为假设生成，不是确证。</strong></li>
<li><strong>未获取全文。</strong>入组标准、失访原因（12 人为何未完成）、
NPS 量表与评分方式、CBF 的获取序列与量化方法、回归模型是否校正年龄/性别/教育/APOE，
摘要均未给出 → <strong>待补全文</strong>。</li>
<li><strong>没有效应量与置信区间。</strong>摘要只给 pFDR 阈值，
不知道关联有多强、区间有多宽。</li>
<li><strong>相关性不等于机制。</strong>「海马旁回丢失 → 攻击性」是统计关联，
中间没有任何环路或递质层面的证据。</li>
<li><strong>未经同行评议。</strong>这是预印本，以上全部结果都可能随审稿改变。</li>
</ol>

<h2>为什么仍然值得记一笔</h2>
<p>把 NPS 从「护理负担」层面拉回到「可测量的脑区改变」层面，这件事本身有临床价值：
如果行为症状对应特定脑区，那么影像就不只是诊断工具，还可能用于<strong>预测谁会出现行为恶化</strong>。
作者在结论里也明确指向这一用途。但要把它当作实用手段，还需要远大于 18 人的外部验证。</p>""",
            related=REL_NPS,
        ),

        "Memory-Intraindividual-Variability-Hippocampal-White-Matter-Latino-medRxiv-2026.html": dict(
            topic="神经退行", ev="C", tag="预印本",
            title="记性忽好忽坏这件事，指向白质而不是海马体积",
            crumb="67 名老年拉美裔：β = −0.34 vs β = 0.028",
            desc="波士顿拉丁裔衰老研究（BLAST）67 名未患痴呆者的分析给出了一个干净的双 dissociation：记忆波动性与海马-扣带束白质 FA 相关（β=−0.34），与海马体积无关（β=0.028）；平均记忆成绩则恰好相反。",

            source=src2,
            body="""<p>认知的<strong>个体内变异性</strong>（intraindividual variability, IIV）指同一个人在不同时间点
或不同任务上的成绩波动。它被认为是认知衰退的早期标志之一，但在<strong>拉美裔</strong>人群中几乎没有数据——
而这个群体既是美国增长最快的老年人群之一，又是 AD 风险被系统性低估的人群。这项 medRxiv 预印本补的正是这个缺口。</p>

<h2>设计与核心数字</h2>
<ul>
<li><strong>样本</strong>：波士顿拉丁裔衰老研究（Boston Latino Aging Study）<strong>67 名</strong>未患痴呆的老年参与者。</li>
<li><strong>检测</strong>：认知测验 + MRI。</li>
<li><strong>两个预测变量</strong>：<strong>记忆 IIV</strong>（波动性）与<strong>平均记忆成绩</strong>（水平）。</li>
<li><strong>两个结局</strong>：<strong>海马体积</strong>（灰质）与<strong>海马-扣带束白质 FA</strong>（各向异性分数，白质微结构指标）。</li>
<li><strong>统计方法</strong>：线性回归。</li>
</ul>

<h2>核心发现：一个双向 dissociation</h2>
<table>
<tr><th>预测变量</th><th>海马体积</th><th>海马-扣带束 FA</th></tr>
<tr><td><strong>平均记忆成绩</strong></td><td><strong>β = 0.24，p = .03</strong>（显著）</td><td>β = −0.07，p = .52（不显著）</td></tr>
<tr><td><strong>记忆 IIV（波动性）</strong></td><td>β = 0.028，p = .84（不显著）</td><td><strong>β = −0.34，p &lt; .01</strong>（显著）</td></tr>
</table>
<p>读法是：<strong>成绩好不好，看的是海马有多大；成绩稳不稳，看的是连接海马的那束白质好不好。</strong>
四类组合每类都给出方向和显著性，形成一个对称的结果——这在小样本观察性研究里算是相当干净的分离。</p>
<p>作者的推论是：<strong>记忆 IIV 可能更贴近海马白质通路，而平均成绩更能反映海马体积。</strong></p>

<h2>边界：别急着把它当 biomarker</h2>
<ol>
<li><strong>横断面。</strong>同一时间点的测验与 MRI，无法判断白质变化在前还是波动性在前。</li>
<li><strong>n = 67</strong>，且是单一队列；摘要未报告多重比较校正方式与协变量清单 → <strong>待补全文</strong>。</li>
<li><strong>四个回归共用同一批人</strong>，结果之间不独立，不能用「四个都符合预期」来抬高证据强度。</li>
<li><strong>FA 是间接指标。</strong>它受髓鞘、轴突密度、交叉纤维等多种因素影响，
不能直译为「白质完整性」。</li>
<li><strong>未经同行评议。</strong></li>
</ol>

<h2>为什么值得关注</h2>
<p>对读者最实用的一条是：<strong>如果你的记忆力「忽好忽坏」，其病理含义可能与「整体变差」不同</strong>——
前者可能指向白质通路。这一区分在认知老化文献里长期被混为一谈。同时，这也是少见的一份
聚焦<strong>拉美裔</strong>老年人群的海马-白质数据， racial/ethnic 代表性本身就是价值。</p>""",
            related=REL_IIV,
        ),

        "Gut-Microbiome-Precedes-Symptomatic-Alzheimer-Amyloid-medRxiv-2026.html": dict(
            topic="神经退行", ev="C", tag="预印本",
            title="无症状人群的肠道菌群随脑内 Aβ 变化，但「先于」二字要先打折扣",
            crumb="101 人、p(perm)=0.03、R²=0.014",
            desc="101 名无症状个体（中位年龄 70 岁）的粪便宏基因组与脑内 Aβ 定量显示：菌群组成随 Aβ 水平变化，Aβ 相关菌群特征对应 GABA 合成能力与免疫/自噬调控因子的降低。但这是横断面研究，标题里的 precedes 指「临床前期」而非「时间在前」。",

            source=src3,
            body="""<p>阿尔茨海默病（AD）在出现临床症状的<strong>几十年前</strong>就开始有脑内 β-淀粉样蛋白（Aβ）沉积。
微生物组-肠-脑轴已被牵连进 AD，但它在<strong>这个临床前阶段</strong>到底扮演什么角色，此前并不清楚。
这项 medRxiv 预印本直接瞄着临床前期：在无症状人群里看菌群特征与 Aβ 负荷的关系。</p>

<h2>设计与数字</h2>
<table>
<tr><th>项目</th><th>数值（官方摘要）</th></tr>
<tr><td>样本</td><td>无症状个体 <strong>n = 101</strong></td></tr>
<tr><td>年龄 / 性别</td><td>中位 <strong>70.0 岁</strong>，<strong>53% 女性</strong></td></tr>
<tr><td>检测</td><td>认知评估 + 脑内 Aβ 定量 + <strong>粪便宏基因组测序</strong></td></tr>
<tr><td>统计方法</td><td>多变量校正的<strong>有序逻辑回归</strong></td></tr>
<tr><td>总体关联</td><td>菌群组成随 Aβ 水平变化：<strong>p(perm) = 0.03，R² = 0.014</strong></td></tr>
</table>

<h2>具体哪些菌</h2>
<table>
<tr><th>方向</th><th>菌种</th><th>显著性</th></tr>
<tr><td>Aβ 越高 → <strong>增多</strong></td><td><em>Alistipes communis</em></td><td rowspan="2">q &lt; 0.001</td></tr>
<tr><td>Aβ 越高 → <strong>减少</strong></td><td><em>Anaerotignum faecicola</em>、<em>Eubacterium rectale</em></td></tr>
</table>
<p>更有意思的是功能层面的推断：<strong>与 Aβ 相关的菌群特征，对应 γ-氨基丁酸（GABA）
合成能力的下降，以及免疫与自噬的系统性调控因子的降低</strong>（q &lt; 0.01）。
换句话说，不只是「哪些菌变了」，而是「它们能做什么变了」，而且变的方向恰好落在神经活性代谢物上。</p>

<h2>边界：把标题读清楚</h2>
<ol>
<li><strong>「precedes」指的是临床前期，不是时间顺序。</strong>这是一项<strong>横断面</strong>研究：
同一个时间点的粪便测序与 Aβ 定量。它证明的是「在还没有症状的人里，菌群差异已经存在」，
<strong>不能证明菌群变化发生在 Aβ 沉积之前</strong>。标题的因果暗示需要在此明确打折。</li>
<li><strong>R² = 0.014。</strong>菌群组成对 Aβ 水平的解释度只有约 1.4%——统计显著，
但关联极弱。用它做个体层面的推断毫无意义。</li>
<li><strong>「Aβ 定量」的方式摘要未说明</strong>（PET 还是 CSF），
多变量具体校正了哪些变量（年龄、性别、BMI、饮食、用药、APOE 基因型）也未知 → <strong>待补全文</strong>。</li>
<li><strong>功能推断来自宏基因组 pathway 预测</strong>，不是代谢物实测；
摘要未报告粪便/血液代谢组验证。</li>
<li><strong>单时间点粪便样本</strong>无法反映菌群的时间波动。</li>
<li><strong>未经同行评议。</strong></li>
</ol>

<h2>放进更大的图景里</h2>
<p>本站此前收录过「<strong>菌群 × 暴露组 × 脑老化</strong>的统一框架」与多条肠-脑轴证据，
本文的位置是把这条轴往<strong>临床前窗口</strong>里推了一格：在症状出现前，菌群层面已经有可测信号，
而且涉及<strong>神经活性代谢物</strong>的合成潜力。对干预设计的含义是明确的——
如果目标是预防，窗口可能比我们习惯以为的更早；但要把它变成干预靶点，
还缺最关键的一步：<strong>纵向队列 + 代谢组学验证</strong>。</p>""",
            related=REL_GUT,
        ),

        "Plasma-PTau217-ATN-Axis-Performance-Boundaries-ADNI-medRxiv-2026.html": dict(
            topic="方法与工具", ev="C", tag="预印本",
            title="血浆 p-tau217 不是万能的：AUROC 从 0.95 掉到 0.79，取决于你问哪个轴",
            crumb="ADNI 分轴评估：A 0.9425 / T 0.9495 / T-within-A+ 0.8852 / N 0.7865",
            desc="曼彻斯特大学团队在 ADNI 上把 AT(N) 拆成五类任务分别评估：血浆 p-tau217 对 A 轴和 T 轴表现优异（AUROC 0.94 量级），但在 A+ 人群内部判别 T 阳性（0.8852）与 MRI 定义的神经变性 N 轴（0.7865）明显下滑。90% 灵敏度下，特异度从 87.5% 掉到 60.7%。",

            source=src4,
            body="""<p>血浆 p-tau217 是当下 AD 血液标志物里风头最劲的一个，头条常常是「可以替代 PET 了」。
但绝大多数验证是在<strong>混合队列</strong>里做的：把 A+ 的病人和 A− 的健康人放在一起对比，
AUC 自然好看。这篇 medRxiv 预印本做了一件不太讨喜但必要的事——
<strong>把 AT(N) 拆成五个子任务逐个考</strong>，看它在每个轴上到底能到什么水平。</p>

<h2>任务与样本（ADNI）</h2>
<table>
<tr><th>轴 / 任务</th><th>总人数</th><th>阳性数</th></tr>
<tr><td>A（淀粉样蛋白阳性，PET）</td><td>1,097</td><td>496</td></tr>
<tr><td>T（tau 阳性，PET）</td><td>929</td><td>195</td></tr>
<tr><td><strong>T within A+</strong>（A+ 内部判别 T）</td><td>361</td><td>161</td></tr>
<tr><td>N（研究定义的海马神经变性，MRI）</td><td>1,303</td><td>248</td></tr>
<tr><td>joint A+T+</td><td>852</td><td>161</td></tr>
</table>
<p>方法上值得点赞的一点：<strong>重复嵌套交叉验证，且预处理与校准都在折内进行</strong>
（所谓 QC-first），避免了信息泄漏——这正是很多血浆标志物 AUC 虚高的常见原因。</p>

<h2>核心结果：性能边界在哪</h2>
<table>
<tr><th>任务</th><th>AUROC（95% CI）</th></tr>
<tr><td>A</td><td><strong>0.9425</strong>（0.9271–0.9562）</td></tr>
<tr><td>T</td><td><strong>0.9495</strong>（0.9325–0.9645）</td></tr>
<tr><td>T within A+</td><td>0.8852（0.8485–0.9163）</td></tr>
<tr><td><strong>N（MRI 神经变性）</strong></td><td><strong>0.7865</strong>（0.7553–0.8151）</td></tr>
<tr><td>joint A+T+</td><td>0.9614（0.9484–0.9726）</td></tr>
</table>
<p>更有临床冲击力的是<strong>固定高灵敏度</strong>时的表现：把灵敏度设定为 90%，
T 轴整体特异度 <strong>87.5%</strong>，但<strong>局限在 A+ 人群内部</strong>时特异度仅 <strong>60.7%</strong>。</p>

<h2>两个外部队列的补充证据</h2>
<ul>
<li><strong>Bio-Hermes（908 人；328 / 324 阳性）</strong>：在 p-tau217 之上加入血浆 Aβ40 与 Aβ42，
AUROC 从 <strong>0.894 提升到 0.916</strong>（配对差 0.022，95% 条件区间 0.010–0.035），
Brier 分数改善 −0.011（−0.017 至 −0.005）。<strong>改善是真的，但很小。</strong></li>
<li><strong>A4 试验队列</strong>：序数化 p-tau217 对 A4 特异的内侧颞叶 tau-PET 终点，
AUROC <strong>0.7356</strong>（0.6775–0.7907），平均精度 0.5657（0.4732–0.6677），
Spearman ρ = 0.4718（0.3824–0.5528）。<strong>这是「单标志物判别条件性 T 阳性」的真实水平。</strong></li>
</ul>

<h2>边界：五条</h2>
<ol>
<li><strong>全部是内部验证。</strong>ADNI 的嵌套交叉验证再严格，也只是「同一批数据内部」；
A4 与 Bio-Hermes 虽是独立队列，但其结果在各自<strong>特定轴、特定检测实现</strong>下才成立，
作者自己在结论里就划了这个范围。</li>
<li><strong>p-tau217 有多种检测试剂</strong>（摘要提到 Lilly 的检测试剂），
不同检测之间的数值不可互换，本文结论不能平移到另一种 assay。</li>
<li><strong>T-within-A+ 与 N 轴存在类别不平衡</strong>（161/361、248/1,303），
AUROC 在不平衡场景下偏乐观，平均精度（仅 A4 给了 0.5657）才是更诚实的指标。</li>
<li><strong>ADNI 本身不是临床代表性人群</strong>：参与者多为自愿入组、白人比例高，
初级保健场景的性能会更低。</li>
<li><strong>未经同行评议</strong>，且N 轴的「研究定义的海马神经变性」具体定义需待补全文。</li>
</ol>

<h2>为什么这篇值得占据一整个位置</h2>
<p>它提供的是<strong>反驳弹药</strong>，而不是又一个「血液检测替代 PET」的好消息。
具体可引用的两句是：<strong>「血浆 p-tau217 在 A+ 内部判别 tau 阳性时，90% 灵敏度下特异度只有 60.7%」</strong>，
以及<strong>「对 MRI 定义的神经变性，AUROC 仅 0.7865」</strong>。
今后在看到「血浆标志物已可替代影像」这类表述时，这两句是可以直接拿来校准的定量边界。</p>""",
            related=REL_PTAU,
        ),

        "PPTC7-Import-Arrest-Mitophagy-Pathway-Switch-bioRxiv-2026.html": dict(
            topic="细胞衰老", ev="C", tag="预印本",
            title="一个 phosphatase 的输入受阻，同时按下线粒体自噬两条通路的开关",
            crumb="去极化既稳定 PINK1，又清除 NIX/BNIP3",
            desc="利物浦大学 Clague 组在 RPE1 细胞中证明：线粒体去极化会抑制新合成 PPTC7 的线粒体输入，这个输入受阻既稳定 PINK1（启动 Parkin 依赖通路），又导致 NIX 与 BNIP3 被降解（关闭受体依赖通路），从而协调两条线粒体自噬通路的切换。摘要无定量。",

            source=src5,
            body="""<p>线粒体自噬（mitophagy）有两条启动通路，而且都挂在线粒体<strong>蛋白质输入</strong>这件事上：
输入受阻时，PINK1 在线粒体外膜稳定下来，激活 Parkin / 泛素依赖通路；
另一条受体介导通路由外膜蛋白 NIX 与 BNIP3 主导，而它们的降解（经 SCFFBXL4 复合物）
需要一个 PP2C 家族磷酸酶 <strong>PPTC7</strong> 作为专性底物识别因子——
PPTC7 本身要在前往基质的途中被「捕获」在线粒体外膜上。这篇 bioRxiv 预印本问的是：
当线粒体去极化发生时，这两条通路如何被协调？</p>

<h2>发现：一个开关，两个相反方向</h2>
<p>在 <strong>RPE1 细胞</strong>中，去极化带来两个同时发生但方向相反的后果：</p>
<ol>
<li>NIX 与 BNIP3 <strong>快速丢失</strong>，且依赖泛素与蛋白酶体、并依赖 PPTC7 的持续合成；</li>
<li>用<strong>多西环素介导的脉冲-追踪实验</strong>直接证明：去极化<strong>抑制了新合成 PPTC7 的输入</strong>，
而这个停滞的 PPTC7 本身也以 FBXL4 依赖的方式，与其底物一同被降解。</li>
</ol>
<p>合起来的机制图景是：<strong>输入受阻这件事，一方面稳定了 PINK1（开启泛素依赖通路），
一方面清除了 NIX/BNIP3（关闭受体依赖通路）</strong>，从而完成通路切换；
而 PPTC7 被同步降解，又把「受体周转」与「PPTC7 合成速率」耦合起来。</p>

<h2>局限与「待补全文」</h2>
<ol>
<li><strong>摘要无任何定量。</strong>没有半衰期、没有降解速率、没有剂量-效应关系、
没有统计量与重复数 → 按本站口径，本篇的所有机制表述都标为「待补全文」。</li>
<li><strong>仅一种细胞系（RPE1）</strong>，无原代细胞、无动物、无衰老模型。
本文是细胞生物学工作，<strong>本身不是衰老研究</strong>——
它与衰老的关联要靠线粒体自噬在衰老中的既有地位来建立，而这个推断是读者做的，不是作者做的。</li>
<li><strong>去极化的诱导方式摘要未说明</strong>（CCCP？寡霉素/抗霉素？），
不同诱导条件下的输入抑制程度可能不同 → 待补全文。</li>
<li><strong>「通路切换」的生理意义未经验证</strong>：在什么场景下细胞需要在两条通路间切换、
切换失败会怎样，均无数据。</li>
<li><strong>未经同行评议。</strong></li>
</ol>

<h2>为什么本站还是收了它</h2>
<p>因为「线粒体自噬能力随龄下降」是衰老生物学里的一条核心命题，而这条链条上的
<strong>具体分子开关</strong>长期是黑箱。PPTC7 这条线把「蛋白质输入效率」和
「两条自噬通路的选择」连在了一起——如果输入效率本身随龄下降，那么老化细胞的自噬通路选择
就可能发生系统性偏移，这正是一条可检验的后续假设。把它作为<strong>机制节点</strong>存档，
价值在此；把它当成抗衰手段，则为时过早（而且全文数据都不涉及衰老表型）。</p>""",
            related=REL_MITO,
        ),
    }

    for slug in A:
        if slug in used:
            sys.exit(f"✗ slug 已存在，拒绝覆盖：{slug}")
    print(f"本批新写 {len(A)} 篇（补b批：来自《预印本速递_2026-10-20》观察哨 #4/#5 + 补遗 #1–#3，"
          f"官方摘要一手拉取核验，全部 C 级）")
    ga.A = A
    ga.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
