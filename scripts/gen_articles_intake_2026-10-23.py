#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_articles_intake_2026-10-23.py —— 内容摄入第 19 批（2026-10-23 巡检）

消化对象
────────
1. 《文献层_五刊监控_深度文献卡片_2026-10-23》(dasrAsiBHRgt, 实测 245,022 B)
   —— 增量轮，61 张卡全部带 DOI + PMID，与上期零重叠。
2. 《预印本速递_2026-10-23》(dDCLlIreKqJS, 实测 42,130 B)
   —— 主榜 5 / 观察哨 4 / 补遗 6，共 15 条。

查重与硬核验（本批最重要的教训）
──────────────────────────────
harvest.py 四路查重报告称「漏收 48 条」，但**用 DOI 逐条 grep news/*.html 原文**后：
  · 76 条候选中 **15 条站内已存在**（harvest 只识别出 5 条）；
  · 原因是 data/doi-index.json 仅 436 条，而 news/ 有 613 个页面 ——
    **DOI 索引落后于页面实际内容**，harvest 的「漏收」判定因此系统性偏高。
  · 这与 SOP 收尾自检条「若漏收数突然暴涨，先查 DOI 索引是否失效」完全吻合：
    先怀疑索引，不要先怀疑产出。
  · 结论：本批所有成篇条目均以 news/*.html 原文硬核验为准，不信 harvest 的 confidence=none。

成篇范围
────────
本批成篇 13 篇：五刊 9 篇（B 级）+ 预印本 4 篇（C 级）。
未成篇的 46 条真漏收（补遗 6 条 + 其余五刊条目）判定与理由写进游标备注：
  · 补遗 6 条 —— 主题与衰老仅边际相关（鸦科端粒生态学、白血病前克隆竞争等），
    且摘要无衰老相关定量，按本站口径不成篇；
  · 其余五刊条目 —— 综述类（A16/A28/G01/G05/G09/G13/G23/G07）、
    纯方法学/资源类（A06 已在站、G22）、或人体相关性证据单薄者，
    本轮按「先上机制原创研究」的优先级暂缓，登记不入站。

证据分级（严格按 about/ 公开图例）
────────────────────────────────
A = 同行评议人体研究 / B = 同行评议临床前研究 / C = 预印本。
五刊条目即使发表在 Cell / Nature Aging，只要核心结论来自动物或体外模型，一律 B；
预印本一律 C，无论数据来自 2,711 例人群尸检还是 10,757 只小鼠——
这一点在 ITP 那篇里尤其需要说清，因为它的数据规模远超多数已发表论文。

纪律
────
· 定量一律照抄卡片/官方摘要原文，未做任何推算；
· 摘要未给的（样本量、效应量、统计量）一律标「待补全文」；
· 内部链接 slug 启动时校验存在性，不存在直接退出。
"""
import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATE = "2026-10-23"

SRC_LIT = "IMA 知识库《文献层·五刊监控·深度文献卡片》2026-10-23 期（file_id dasrAsiBHRgt）"
SRC_PP = "IMA 知识库《预印本速递》2026-10-23 期（file_id dDCLlIreKqJS）"

# ── 预印本 4 篇 ────────────────────────────────────────────────
REL_ITP = [
    ("NIA-ITP-11-Compounds-No-Lifespan-Extension-2026.html",
     "NIA 干预测试项目 11 种化合物：多数没能延长小鼠寿命"),
    ("Rapamycin-HFpEF-Frailty-Functional-Endpoint-Failure-2026.html",
     "雷帕霉素在 HFpEF 与衰弱中的功能终点失败"),
    ("Metabolomics-5-Longevity-Interventions-UMHET3-Mice-2026.html",
     "五种延寿干预的代谢组学：UM-HET3 小鼠里的共同与分歧"),
]
REL_AUTOP = [
    ("Amyloid-Trajectory-Bifurcation-Normal-Aging-AD-2026.html",
     "淀粉样蛋白轨迹在正常衰老与 AD 之间的分叉"),
    ("Plasma-PTau217-ATN-Axis-Performance-Boundaries-ADNI-medRxiv-2026.html",
     "血浆 p-tau217 与 ATN 轴的性能边界"),
    ("PathStAR-Structural-Aging-Human-Tissues-Nature-Aging-2026.html",
     "PathStAR：用人类组织切片量化结构性衰老"),
]
REL_MDM4 = [
    ("Insights-Interplay-Senescent-Cells-Immune-AgingCell-2026.html",
     "衰老细胞与免疫系统互作的 insights 综述"),
    ("CCND1-CDK6-cGAS-STING-SASP-Palbociclib-NatureAging-2026.html",
     "CCND1-CDK6 经 cGAS-STING 驱动 SASP：Palbociclib 的 senomorphic 证据"),
    ("Mitochondrial-Metabolism-Epigenetic-SASP-Nature-2026.html",
     "线粒体代谢经表观重塑驱动 SASP"),
]
REL_ISP = [
    ("Partial-Reprogramming-OSK-Human-Neurons-Glia-Epigenetic-Rejuvenation-2026.html",
     "OSK 部分重编程在人神经元与胶质细胞中的表观回春"),
    ("Life-Biosciences-ER-100-First-Human-Data-AAO-2026.html",
     "Life Biosciences ER-100 的首批人体数据"),
    ("NewLimit-435M-Epigenetic-Reprogramming-2026.html",
     "NewLimit 4.35 亿美元：表观重编程赛道的资本化"),
]
# ── 五刊 9 篇 ──────────────────────────────────────────────────
REL_DUSP5 = [
    ("MEK-T-Cell-Exhaustion-Immunotherapy-MS-KCC-2026.html",
     "MEK 抑制与 T 细胞耗竭：免疫治疗中的可回拉节点"),
    ("Granzyme-K-Aged-CD8-T-cells-Cognitive-Decline-2026.html",
     "颗粒酶 K⁺ 老年 CD8⁺ T 细胞与认知下降"),
    ("Clonal-T-Cell-Expansion-Elderly-JEM-1994.html",
     "健康老年人血液里，某些 T 细胞克隆能占到全部 CD8 的三分之一以上"),
]
REL_3HB = [
    ("MEK-T-Cell-Exhaustion-Immunotherapy-MS-KCC-2026.html",
     "MEK 抑制与 T 细胞耗竭：免疫治疗中的可回拉节点"),
    ("Cytotoxic-CD4-CTL-Senescence-Aging-2026.html",
     "细胞毒性 CD4⁺ CTL：被忽略的衰老免疫细胞群"),
    ("Sentcell-Immune-Rejuvenation-Senescent-T-Cells-Phase1-2026.html",
     "Sentcell 的衰老 T 细胞免疫回春：1 期临床"),
]
REL_MITOTX = [
    ("BNIP3L-NIX-Mitophagy-Alzheimer-Tau-Amyloid-bioRxiv-2026.html",
     "BNIP3L/NIX 介导的线粒体自噬限制 AD 病理"),
    ("PPTC7-Import-Arrest-Mitophagy-Pathway-Switch-bioRxiv-2026.html",
     "PPTC7 输入阻滞：线粒体自噬的通路开关"),
    ("Chronic-Senolytic-Treatment-or-Aerobic-Exercise-Reduce-Senescence-Improve-Myocardial-Function.html",
     "慢性 senolytics 与有氧运动：9 个月对照下的衰老心脏"),
]
REL_RAPA = [
    ("Immune-Signatures-Atherosclerosis-Plaque-Immunity-Aging-2026.html",
     "动脉粥样硬化斑块内的免疫特征与衰老"),
    ("LATS1-2-CD38-Endothelial-Senescence-Atherothrombosis-2026.html",
     "LATS1/2-CD38 轴与内皮衰老驱动的动脉血栓"),
    ("Rapamycin-HFpEF-Frailty-Functional-Endpoint-Failure-2026.html",
     "雷帕霉素在 HFpEF 与衰弱中的功能终点失败"),
]
REL_SIRT6 = [
    ("SIRT6-AAV-Chromatin-Rejuvenation-Liver-2026.html",
     "SIRT6 经 AAV 递送实现的肝脏染色质回春"),
    ("SIRT6-Centenarian-Variants-Senolytic-2026.html",
     "百岁老人 SIRT6 变体与 senolytic 敏感性"),
    ("NAD-Precursor-Systematic-Review-Meta-Analysis-2026.html",
     "NAD⁺ 前体的系统综述与 meta 分析"),
]
REL_NR = [
    ("NOPARK-NR-Early-Parkinson-Phase3-JAMA-2026.html",
     "NOPARK：NR 在早期帕金森病中的 3 期结果"),
    ("Senolytics-Restore-Microglia-White-Matter-Nature-Aging-2026.html",
     "senolytics 恢复小胶质细胞与白质：Nature Aging 证据"),
    ("Association-between-whole-blood-NAD-concentration-frailty-community-dwelling-older-adults-Itabashi-Longitudinal.html",
     "全血 NAD⁺ 浓度与社区老人衰弱：板桥队列"),
]
REL_INSC = [
    ("Partial-Reprogramming-OSK-Human-Neurons-Glia-Epigenetic-Rejuvenation-2026.html",
     "OSK 部分重编程在人神经元与胶质细胞中的表观回春"),
    ("Transcriptomic-Reprogramming-Screen-Identifies-SRSF1-NatureAging-2026.html",
     "转录组重编程筛选锁定 SRSF1"),
    ("Systemic-Recalibration-Epigenetic-Reprogramming-Combination-2026.html",
     "表观重编程的系统性重校准与联合策略"),
]
REL_MTR4 = [
    ("LATS1-2-CD38-Endothelial-Senescence-Atherothrombosis-2026.html",
     "LATS1/2-CD38 轴与内皮衰老驱动的动脉血栓"),
    ("AAV-FGF21-Gene-Therapy-Healthspan-Lifespan-2026.html",
     "AAV-FGF21 基因治疗与健康期、寿命"),
    ("GHR-Antagonist-Pegvisomant-Lineage-Extends-Lifespan-AgingCell-2026.html",
     "GHR 拮抗剂 Pegvisomant 谱系延长寿命"),
]
REL_PROT = [
    ("DNAm-Clock-EAA-Dementia-Meta-Analysis-37-Studies-2026.html",
     "DNAm 时钟的表观年龄加速与痴呆：37 项研究 meta 分析"),
    ("LivAge-An-Online-Aging-Clock-AgingCell-2026.html",
     "LivAge：一个在线的衰老时钟"),
    ("SASP-Score-Deep-Learning-Senescent-Cell-2026.html",
     "深度学习把 SASP 压成一个分数"),
]


def notice(ev):
    t = {"A": "A 级（同行评议人体研究）",
         "B": "B 级（同行评议临床前研究，主要为动物或体外模型）",
         "C": "C 级（预印本：未经同行评议，结论可能随审稿改变）"}[ev]
    src_note = {
        "B": "本站依据 <strong>IMA 知识库「五刊监控·深度文献卡片」（SOP §4.2 摘要级）</strong>撰写，"
             "依据<strong>期刊公开摘要与 PubMed 元数据</strong>；付费墙全文未获取之处已标注「待补全文」，"
             "<strong>未做任何数值推算补全</strong>。",
        "C": "本篇依据<strong>预印本官方摘要</strong>（本轮经 IMA 知识库《预印本速递》卡片与官方摘要核对）"
             "整理，定量一律照抄原文，<strong>未做任何数值推算补全</strong>；"
             "凡摘要未给出的信息一律标注「待补全文」。",
    }[ev]
    return (f'<div class="notice-box">\n'
            f'    <p><span class="tier tier-{ev.lower()}">{ev} 级</span>'
            f'<strong>证据分级：{t}</strong></p>\n'
            f'    <p><strong>本文核心结论来自动物模型或体外细胞学，属临床前证据，不能外推至人体。</strong>'
            f'「延长健康寿命」「改善功能」等表述在小鼠中的意义，与人类临床结局之间仍有距离。</p>\n'
            f'    <p><strong>关于本文的文献来源：</strong>{src_note}</p>\n'
            f'</div>')


def lit_src(journal, vol, title, doi, pmid, authors, avail):
    return (f'<em>{journal}</em>（{vol}）· {title}'
            f' · DOI <a href="https://doi.org/{doi}" target="_blank" '
            f'rel="noopener noreferrer">{doi}</a> · PMID <a href="https://pubmed.ncbi.nlm.nih.gov/'
            f'{pmid}/" target="_blank" rel="noopener noreferrer">{pmid}</a>'
            f' · {authors} · 来源：{SRC_LIT} · 全文：{avail}')


def pp_src(server, cat, title, doi, authors, avail):
    return (f'<em>{server}</em>（{cat}）· 预印本：{title}'
            f' · DOI <a href="https://doi.org/{doi}" target="_blank" '
            f'rel="noopener noreferrer">{doi}</a> · {authors}'
            f' · 来源：{SRC_PP} + 官方摘要核对 · 全文：{avail}')


def main():
    all_rel = (REL_ITP + REL_AUTOP + REL_MDM4 + REL_ISP + REL_DUSP5 + REL_3HB
               + REL_MITOTX + REL_RAPA + REL_SIRT6 + REL_NR + REL_INSC
               + REL_MTR4 + REL_PROT)
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

    A = {}

    # ══════════ P1 · ITP 异常对照队列 ══════════
    A["ITP-Outlier-Control-Cohort-Prediction-Interval-Lifespan-2026.html"] = dict(
        topic="研究方法", ev="C", tag="预印本",
        title="10,757 只对照小鼠的警告：换掉一个「异常」队列，两种雷帕霉素方案的显著性就变了",
        crumb="寿命实验的对照组本身在漂移",
        desc="NIA 干预测试项目（ITP）核心统计力量（Churchill 与 Nelson，JAX）用 18 年、10,757 只对照小鼠建立预测区间框架，发现年际变异（尤其雄性）远大于随机抽样能解释的部分；剔除一个新识别出的雄性异常队列后，两种雷帕霉素方案的统计学显著性发生了变化。",
        source=pp_src("bioRxiv", "bioinformatics",
                      "A prediction-interval framework for identifying outlier control cohorts in lifespan studies",
                      "10.64898/2026.10.21.760720",
                      "通讯 Gary A. Churchill（The Jackson Laboratory）；合著者含 J. F. Nelson",
                      "C 仅摘要 · 源站封锁（Cloudflare 403）"),
        body="""<p>小鼠寿命实验里最容易被当成背景噪声的东西是<strong>对照组的自然变异</strong>。
这篇预印本用 NIA 干预测试项目（ITP）18 年、<strong>10,757 只对照小鼠</strong>的数据说明：
这个「噪声」大到足以改变结论——<strong>从原始寿命分析中排除一个新识别出的雄性异常队列后，
两种 rapamycin 方案的统计学显著性发生了变化</strong>。</p>

<p>作者阵容值得先说：通讯 Gary Churchill 与合著者 J. F. Nelson 都在 The Jackson Laboratory，
正是 ITP 的统计核心。<strong>这不是外部挑刺，是内部体检。</strong></p>

<h2>框架做了什么</h2>
<p>ITP 在<strong>三个独立站点</strong>用标准化方案测试干预，这个设计本意就是抵消单站点的偶然性。
作者在此之上建立<strong>预测区间（prediction interval）</strong>框架：
先由历史对照数据估计每个「站点 × 年份 × 性别 × 品系」单元格应当落在什么区间，
再把实际队列与之比对，超出即标记为异常。</p>

<p>核心统计量上的发现是：<strong>年际变异（尤其雄性）对队列均值变异的贡献，
远大于单纯随机抽样所能解释的部分</strong>。</p>

<h2>三个判定结果</h2>
<table>
<thead><tr><th>队列</th><th>框架判定</th><th>备注</th></tr></thead>
<tbody>
<tr><td>2022 年 JAX 雌性</td><td><strong>异常</strong></td><td>复现了历史已有疑点</td></tr>
<tr><td>2017 年 UT 雄性</td><td><strong>未判异常</strong></td><td>与部分历史质疑相反</td></tr>
<tr><td>某一个雄性队列</td><td><strong>异常（新识别）</strong></td><td>此前未被识别；剔除后两种 rapamycin 方案的显著性改变</td></tr>
</tbody>
</table>

<p>第三行是本条的实质内容。它的含义不是「雷帕霉素无效」，
而是<strong>「该方案有效」这一结论的稳健性依赖于某一个对照队列是否计入</strong>——
这在统计上是完全不同的两件事，但在文献传播中经常被合并成前者。</p>

<h2>为什么对做寿命实验的人是必读</h2>
<p>传统做法是「处理组 vs 同期对照」。这个框架指出同期对照本身就在漂移，
于是<strong>站点 × 年份的隐蔽结构会直接进入处理效应的估计</strong>。
如果对照队列恰好偏低，干预就显得更有效；反之则被埋掉。</p>

<p>作者的诉求很清楚：需要<strong>标准化的离群值检测框架</strong>，
并在衰老研究中<strong>显式计入自然变异</strong>，而不是假定对照是稳定的地板。</p>

<h2>数字：给了规模，没给效应</h2>
<p>摘要给出的可引用定量是<strong>10,757 只对照小鼠、18 年、三个站点</strong>。
但以下关键字段一律<strong>待补全文</strong>，本站未做任何推算：</p>
<ul>
<li>究竟是<strong>哪两种 rapamycin 方案</strong>（剂量、给药途径、起始月龄）—— 待补全文</li>
<li>排除异常队列后显著性<strong>向哪个方向变化</strong>（变显著 / 变不显著 / 效应量增减）—— 待补全文</li>
<li>新识别的雄性异常队列<strong>是哪一年、哪个站点</strong> —— 待补全文</li>
<li>预测区间的覆盖水平与判定阈值 —— 待补全文</li>
</ul>

<h2>局限</h2>
<ul>
<li>本条性质上是<strong>方法学/资源类</strong>论文，不产生新的生物学发现。
它评判的是<strong>已有结论的稳健性</strong>，不是提出新机制。</li>
<li>「显著性改变」是<strong>方向未明的表述</strong>——在拿到全文前，
既不能读成「雷帕霉素被证伪」，也不能读成「雷帕霉素更可信」。</li>
<li>框架目前建立在 ITP 的标准化方案之上；<strong>单实验室的小规模寿命实验</strong>
能否直接套用同一区间估计，摘要未讨论。</li>
</ul>

<blockquote><p>对所有做小鼠寿命实验的人，这是一条<strong>方法学警报</strong>：
对照组本身就在漂移。它同时意味着，部分已发表的寿命延长结论可能需要重新体检一次。</p></blockquote>

<h2>为什么仍是 C 级</h2>
<p>它的样本规模（10,757 只）远超多数已发表的同行评议寿命研究，
数据来源是公认最严格的 ITP。但它是<strong>未经同行评议的预印本</strong>，
按本站分级约定只能标 C。<strong>数据规模与机构权威都不会抬高预印本的证据等级</strong>——
这一点刻意写在这里，提醒自己也提醒读者。</p>

<p class="small">本文为预印本，未经同行评审，结论可能在正式发表时变更。</p>""",
        related=REL_ITP)

    # ══════════ P2 · 圣保罗尸检队列 ══════════
    A["Amyloid-Tau-Neuropathology-Autopsy-Cohort-SaoPaulo-2026.html"] = dict(
        topic="神经退行", ev="C", tag="预印本",
        title="2,711 例尸检的冷水：70 岁前 Aβ/tau 病理并不常见，而生物标志物看不见的共存病变同样能解释认知损害",
        crumb="用金标准组织学校准生物标志物",
        desc="巴西圣保罗大学 2004–2025 年人群尸检队列 2,711 例（平均 73.4 岁）显示，同时达到 Thal 3–5 且 Braak IV–VI 者仅 19.6%；61–70 岁为 5.5%，81–90 岁才升至 36.5%。更关键的是，仅共存脑病变者的 CDR>0 比例为 58.5%，与仅 Aβ+tau 联合病理者的 63.7% 接近。",
        source=pp_src("medRxiv", "neurology",
                      "Amyloid and Tau Neuropathologic Stage, Coexisting Brain Disease, and Cognitive Status "
                      "in a Population-Based Autopsy Cohort",
                      "10.64898/2026.10.20.26365945",
                      "通讯 Lea T. Grinberg（Mayo Clinic Jacksonville + 圣保罗大学医学院 LIM-22）",
                      "B 全文 PDF 已下载（1,412,554 B / 34 页），本站按摘要级撰写"),
        body="""<p>近年阿尔茨海默病（AD）研究的一大转向是<strong>从临床诊断走向生物标志物定义</strong>：
血浆 p-tau217、淀粉样蛋白 PET 正在取代「临床综合征」成为入组与研究终点。
这篇 medRxiv 预印本用<strong>2,711 例人群尸检的组织学「金标准」</strong>，
给这套新语言做了一次校准。</p>

<h2>队列：2,711 例，来自全市尸检服务</h2>
<p>样本来自圣保罗大学衰老研究生物样本库 2004–2025 年，
经市属集中尸检服务抽样（年约 15,000 例尸检，覆盖全市约 <strong>16% 死亡</strong>）。</p>
<ul>
<li>例数 <strong>2,711</strong>；平均年龄 <strong>73.4（SD 14.4）岁</strong>，范围 <strong>23–111 岁</strong></li>
<li>女性 <strong>1,340 例（49.4%）</strong></li>
<li>关键设计优势：<strong>不按认知诊断或记忆门诊入组</strong>，而是从全市死亡中抽样</li>
</ul>

<h2>核心结果一：生物标志物可检测范围的病理，70 岁前并不常见</h2>
<p>按预设「生物标志物可检测范围」（Thal phase 3–5 <strong>且</strong> Braak stage IV–VI）分层：</p>
<table>
<thead><tr><th>分层</th><th>例数</th><th>占比</th></tr></thead>
<tbody>
<tr><td>两项阈值均达</td><td>531</td><td><strong>19.6%</strong></td></tr>
<tr><td>仅达淀粉样阈值</td><td>270</td><td><strong>10.0%</strong></td></tr>
<tr><td>仅达 tau 阈值</td><td>207</td><td><strong>7.6%</strong></td></tr>
<tr><td>两项均未达</td><td>1,703</td><td><strong>62.8%</strong></td></tr>
</tbody>
</table>

<p>这个分布随年龄陡升，但起点很低：</p>
<table>
<thead><tr><th>年龄组</th><th>联合病理状态比例</th></tr></thead>
<tbody>
<tr><td>23–50 岁</td><td><strong>0%</strong></td></tr>
<tr><td>61–70 岁</td><td><strong>5.5%</strong></td></tr>
<tr><td>71–80 岁</td><td><strong>14.5%</strong></td></tr>
<tr><td>81–90 岁</td><td><strong>36.5%</strong></td></tr>
<tr><td>91–111 岁</td><td><strong>45.9%</strong></td></tr>
</tbody>
</table>

<p>换句话说，<strong>在 70 岁前，处于现行生物标志物可检测范围内的 Aβ/tau 病理是少数现象</strong>。
这直接关系到一个非常实际的问题：在这个年龄段测出阳性，意味着什么。</p>

<h2>核心结果二：生物标志物看不见的病变，解释力不输晚期 AD 病理</h2>
<p>CDR>0（有认知损害）的比例随 Braak 分期单调递增：stage 0 为 88/541（<strong>16.3%</strong>），
stage VI 为 155/179（<strong>86.6%</strong>）。这条符合预期。</p>

<p>但把「共存脑病变」（coexisting brain disease，即非 Aβ/tau 的病变）也纳入交叉分类后，
出现了一个不好解释的结果：</p>
<table>
<thead><tr><th>交叉分类</th><th>CDR>0 比例</th></tr></thead>
<tbody>
<tr><td>两者皆无</td><td>225/1,467（<strong>15.3%</strong>）</td></tr>
<tr><td>仅共存病变</td><td>204/349（<strong>58.5%</strong>）</td></tr>
<tr><td>仅 Aβ+tau 联合病理</td><td>216/339（<strong>63.7%</strong>）</td></tr>
<tr><td>两者皆有</td><td>165/192（<strong>85.9%</strong>）</td></tr>
</tbody>
</table>

<p><strong>「仅有共存病变」的 58.5% 与「仅有 Aβ+tau 联合病理」的 63.7% 相距不远</strong>。
在 CDR-SB 多变量模型中，共存脑病变的<strong>独有解释贡献最大</strong>
（partial R² = <strong>0.088，95% CI 0.064–0.114</strong>），
而 Braak 分期占总解释方差份额最大（LMG 贡献 <strong>0.115</strong>）。</p>

<blockquote><p>翻译成人话：<strong>现有 Aβ/tau 生物标志物检测不到的那些病变，
解释认知损害的能力并不输给晚期 AD 病理。</strong>
对「以淀粉样蛋白为中心」的干预叙事，这是一记警钟。</p></blockquote>

<h2>还有一个细节：17.6% 的不一致</h2>
<p>作者报告 <strong>17.6% 的逝者中 Aβ 与 tau 两项分期不一致</strong>。
这意味着把两者合并成单一「AD 病理连续体」的做法，在接近五分之一的个体上不成立。</p>

<h2>局限</h2>
<ul>
<li><strong>横断面尸检设计，无法推断因果</strong>——病理与认知损害的时序关系不能由此确定。</li>
<li>单一地理人群（<strong>巴西圣保罗混合祖源人群</strong>），外推性需在其他队列验证；
这一点对病理频率尤其重要，因为 APOE 等遗传背景分布不同。</li>
<li>CDR 由逝者<strong>生前最后一次评估</strong>得出，<strong>时间间隔不一致</strong>可能引入错分。</li>
<li>PDF 已下载但未通读全文，<strong>上述数字全部来自摘要</strong>；
各年龄组的分子分母、共存病变的具体分类与判定标准——<strong>待补全文</strong>。</li>
</ul>

<h2>为什么是 C 级</h2>
<p>样本量 2,711、人群尺度、金标准组织学——每一项都足够硬。
但它是<strong>未经同行评议的 medRxiv 预印本</strong>，按本站约定标 C。
<strong>样本规模不抬高证据等级</strong>。</p>

<p class="small">本文为预印本，未经同行评审，结论可能在正式发表时变更。</p>""",
        related=REL_AUTOP)

    # ══════════ P3 · 细胞大小 → MDM4-S ══════════
    A["Cell-Size-Chromatin-Rewiring-MDM4-Splicing-Senescence-2026.html"] = dict(
        topic="细胞衰老", ev="C", tag="预印本",
        title="细胞变大不只是衰老的结果：它让染色质重排、MDM4 剪错，反过来把细胞焊死在衰老里",
        crumb="从形态学标志到因果环节",
        desc="苏黎世大学团队证明细胞增大时染色质在核斑点与核纤层间全局重分布，导致 p53 负调控因子 MDM4 被错误剪接为无功能变体 MDM4-S，维持 p53 依赖的永久性细胞周期退出与 SASP；重新导入正确剪接的 MDM4 转录本可恢复 G1 进程、逆转衰老表型。",
        source=pp_src("bioRxiv", "cell biology",
                      "Rewired mRNA homeostasis enforces cell-size associated senescence",
                      "10.64898/2026.10.21.760624",
                      "通讯 Sandhya Manohar（University of Zurich, Department for Molecular Mechanisms of Disease）",
                      "D 仅摘要 · 未尝试下载（bioRxiv 403）"),
        body="""<p>衰老细胞<strong>变大</strong>这件事，从 Hayflick 时代就在显微镜下被看到过无数次。
但它一直被当作<strong>结果的读数</strong>——细胞停下来了所以摊开变大，而不是原因。
这篇预印本把它翻了过来：<strong>细胞增大本身就是衰老的驱动环节</strong>。</p>

<h2>机制链条</h2>
<p>摘要给出的因果链相当完整，这在预印本里不多见：</p>
<ol>
<li><strong>细胞增大</strong>（excess cell size）不只是衰老的被动结果，
而可通过 <strong>p53-p21 通路主动促进衰老</strong>；</li>
<li>全基因组邻近作图显示：细胞增大使<strong>染色质在核斑点（nuclear speckles）
与核纤层（nuclear lamina）之间全局重分布</strong>；</li>
<li>伴随<strong>核纤层相关基因的去抑制</strong>，其中部分基因参与 <strong>SASP</strong>；</li>
<li>细胞增大<strong>扰乱正常的剪接异构体使用</strong>——关键一击是
<strong>MDM4 被差异剪接为无功能变体 MDM4-S</strong>。MDM4 本是 p53 信号的负调控因子；</li>
<li>重新导入<strong>正确剪接的 MDM4 转录本</strong>可<strong>恢复 G1 细胞周期进程</strong>，
从而在增大细胞中逆转衰老表型。</li>
</ol>

<blockquote><p>值得单独拎出来的逻辑：<strong>MDM4 是 p53 的刹车。</strong>
细胞变大 → 刹车蛋白被剪成废品 → p53 持续激活 → 细胞周期永久退出 + SASP 维持。
这是一个<strong>自我维持的环路</strong>，而剪接错误是其中可干预的一环。</p></blockquote>

<h2>为什么这条有意思</h2>
<p>本站已记录的衰老细胞干预路线，绝大多数落在两端：
<strong>用 senolytics 直接杀死衰老细胞</strong>，或<strong>用 senomorphics 压制 SASP</strong>。
这篇给出的是第三条——<strong>剪接校正</strong>：
不杀细胞、不压 SASP，而是把被剪错的 MDM4 修回来，让细胞自己退出衰老程序。</p>

<p>如果这个机制在体内成立，它的吸引力在于<strong>不依赖清除</strong>：
senolytics 的最大顾虑之一是某些组织里的衰老细胞<strong>有生理功能</strong>（伤口愈合、胎盘、肿瘤抑制），
一刀切清除的代价未知。剪接校正在理论上只影响「因增大而错误进入衰老」的那部分。</p>

<h2>数字：这篇没有数字</h2>
<p>需要如实说明：<strong>该摘要未提供任何可引用定量</strong>——
没有样本量、染色质重排的定量幅度、MDM4-S / MDM4 比例、也没有 P 值。
以下字段一律<strong>待补全文</strong>，本站未推算、未从同类文献套用：</p>
<table>
<thead><tr><th>字段</th><th>状态</th></tr></thead>
<tbody>
<tr><td>所用细胞类型与衰老诱导方式</td><td>待补全文（通讯单位背景提示可能为 HeLa / RPE1 增殖模型）</td></tr>
<tr><td>MDM4-S 与 MDM4 的比例变化</td><td>待补全文</td></tr>
<tr><td>染色质区室重分布的定量幅度</td><td>待补全文</td></tr>
<tr><td>去抑制的核纤层相关基因数量与清单</td><td>待补全文</td></tr>
<tr><td>回补 MDM4 后 G1 恢复的比例</td><td>待补全文</td></tr>
<tr><td>是否有体内 / 原代组织验证</td><td>待补全文（摘要未提及动物实验）</td></tr>
</tbody>
</table>

<h2>保留意见</h2>
<ul>
<li>「<strong>可以逆转衰老表型</strong>」是一个很强的断言。
在拿到全文之前，它究竟意味着「恢复增殖」还是「SASP 消退」还是「衰老标志全面回落」，
本站不下判断。</li>
<li>若为<strong>体外增殖细胞系模型</strong>，能否推广至体内衰老组织（尤其 post-mitotic 组织）
完全未知——而组织里的衰老细胞恰恰是 senolytics 的主要目标。</li>
<li>摘要未说明<strong>增大的触发因素</strong>是什么。如果增大本身由上游损伤驱动，
那剪接校正可能只处理了链条的后半段。</li>
</ul>

<p class="small">本文为预印本，未经同行评审，结论可能在正式发表时变更。</p>""",
        related=REL_MDM4)

    # ══════════ P4 · ISP 平台 / 山中因子顺序 ══════════
    A["In-Silico-Perturbation-Yamanaka-Order-Partial-Reprogramming-2026.html"] = dict(
        topic="部分重编程", ev="C", tag="预印本",
        title="山中因子的 24 种导入顺序，第一次被系统地筛了一遍：POU5F1 或 SOX2 打头，效应最大",
        crumb="虚拟扰动给出的可验证假设",
        desc="筑波大学 TARA 中心发布免代码的 ISP Platform，在 Geneformer 上做跨物种、状态反馈与多基因虚拟扰动；状态反馈 ISP 模拟了山中因子全部 24 种导入顺序，发现 POU5F1 或 SOX2 排在最前时因子特异性效应急剧增大，另有 7 个多能性基因的虚拟过表达使体细胞向 iPSC 偏移程度超过山中四因子。",
        source=pp_src("bioRxiv", "bioinformatics",
                      "ISP Platform powered by Geneformer: Framework for Cross-Species, State-feedback, "
                      "and Multi-Gene In Silico Perturbation Screens with Application to iPS Cell State Transitions",
                      "10.64898/2026.09.17.752497",
                      "通讯 Yuya Sanaki（University of Tsukuba, Life Science Center for Survival Dynamics, TARA）",
                      "D 仅摘要 · 未尝试（version 2，2026-10-22 上线；代码已开源）"),
        body="""<p>部分重编程（partial reprogramming / OSK）是长寿领域资金与关注最集中的方向之一，
但有一个<strong>少有人系统问的实验变量</strong>：<strong>山中因子的导入顺序会不会影响效果？</strong>
标准做法是把 OCT4 / SOX2 / KLF4 / MYC 一起上，顺序通常不被当作变量。
这篇预印本用<strong>虚拟筛选</strong>把这个问题问了一遍。</p>

<h2>平台：免代码 + 状态反馈</h2>
<p>ISP Platform 建立在 <strong>Geneformer</strong> 之上，几个特点：</p>
<ul>
<li><strong>免代码图形界面</strong>——不需要写 Python 就能跑虚拟扰动；</li>
<li>支持<strong>双向跨物种分析</strong>：输入物种与人 / 鼠 Geneformer 模型可独立选择；</li>
<li>支持<strong>多基因 ISP</strong> 与<strong>状态反馈 ISP</strong>——
后者指<strong>每次扰动后重新预测表达排序，再喂入下一次扰动</strong>。
这一点是它能模拟「顺序」的关键：普通单步扰动没有先后概念。</li>
</ul>

<h2>结果与衰老研究的接口</h2>
<p>摘要给出的三项结果里，有两项与重编程直接相关：</p>
<ol>
<li>状态反馈 ISP 模拟了<strong>山中因子的全部 24 种导入顺序</strong>（4! = 24），
在每种顺序中分离出<strong>因子特异性效应</strong>；
结果显示<strong>当 POU5F1 或 SOX2 排在最前时，效应急剧增大</strong>。</li>
<li>在人 / 鼠 iPSC 单细胞转录组上做全基因组敲低筛选，
物种匹配与互换模型<strong>均能优先命中核心多能性调控因子</strong>——这是对平台可信度的一个自检。</li>
<li><strong>7 个多能性基因的虚拟过表达，使体细胞向 iPSC 偏移的程度超过山中四因子</strong>
（Yamanaka factors: OCT4/SOX2/KLF4/MYC）。</li>
</ol>

<p>此外，成对虚拟过表达筛选还指出了 <strong>NANOG / KLF2 基准之外的 prime-to-naive 转换候选调控因子</strong>。</p>

<blockquote><p>对计划做 OSK 诱导实验的人，这是<strong>可直接转为 hypothesis 的资源</strong>：
先上 POU5F1 或 SOX2、以及那 7 基因组合，都是低成本可试的优先级假设。
工具本身免代码，试错成本极低。</p></blockquote>

<h2>必须说清的边界：这是 in silico</h2>
<p>这一点本站要写得比摘要更重：<strong>所有结果都是计算机模拟</strong>，无湿实验验证。</p>
<ul>
<li>「<strong>7 基因优于山中 4 因子</strong>」是 <strong>Geneformer 嵌入空间里的排序位移</strong>，
<strong>不等于实际重编程效率提升</strong>。这两件事之间隔着一整个实验验证的距离。</li>
<li>「顺序效应」同理——模型学到的顺序依赖，未必对应真实细胞里的动力学。</li>
<li>本条<strong>不产出任何生物学结论</strong>，它产出的是<strong>待验证的优先级</strong>。</li>
</ul>

<h2>数字与字段</h2>
<p>摘要给出的可引用信息是 <strong>24 种顺序</strong>、<strong>7 个基因</strong>、
<strong>Geneformer</strong>、<strong>version 2</strong>。以下一律<strong>待补全文</strong>：</p>
<ul>
<li>7 个多能性基因的<strong>具体名单</strong> —— 待补全文</li>
<li>「效应急剧增大」的<strong>定量口径</strong>（嵌入位移量？命中率？）—— 待补全文</li>
<li>prime-to-naive 候选因子的名单 —— 待补全文</li>
<li>所用 iPSC 单细胞数据集的来源与规模 —— 待补全文</li>
</ul>

<h2>为什么本站还是收了它</h2>
<p>部分重编程是长寿领域的 top-tier 方向，而<strong>「导入顺序」这个变量几乎无人系统研究</strong>。
一个免代码工具把假设生成成本压到接近于零，对实验组是有用的。
本站把它标为 <strong>C 级（预印本）+ 方法学/资源类</strong>，
读者应把它当作<strong>待验证假设的来源</strong>，而不是证据。</p>

<p class="small">本文为预印本，未经同行评审，结论可能在正式发表时变更。</p>""",
        related=REL_ISP)

    # ══════════ F1 · CRISPR Dusp5 / Zfp219（Cell） ══════════
    A["CRISPR-Screen-Dusp5-Zfp219-Aged-T-Cell-Cell-2026.html"] = dict(
        topic="免疫与炎症", ev="B", tag="研究进展",
        title="单细胞 CRISPR 筛出两个靶点：敲掉它们，老年 T 细胞的抗肿瘤能力被拉回来",
        crumb="Dusp5 与 Zfp219 是衰老 T 细胞功能失调的驱动",
        desc="Cell 发表的这项研究在衰老肿瘤模型中做单细胞 CRISPR 筛选，锁定 Dusp5 与 Zfp219：敲除 Dusp5 提高 ERK 磷酸化并全局增强 T 细胞增殖，敲除 Zfp219 引发表观重编程、提高细胞毒分子表达，特异地在衰老环境中增强抗肿瘤免疫。人源 ZNF219 在老年癌症患者瘤内 CD8⁺ T 细胞中水平更高，且与免疫治疗后更差生存相关。",
        source=lit_src("Cell", "2026, 189(21): 6738-6751.e7",
                       "CRISPR screens identify targets to rescue age-related T cell dysfunction in cancer",
                       "10.1016/j.cell.2026.07.016", "42526438",
                       "第一作者 Chen Alex C Y（共 22 位作者）",
                       "摘要级 · 待补全文（订阅墙，PubMed 无 PMCID）"),
        body="""<p>老年癌症患者对免疫检查点抑制剂（ICB）的响应普遍更差，这是一个临床事实。
机制层面通常被归因于「免疫衰老」这个筐——但筐里究竟<strong>哪几个基因是真正的驱动</strong>，
一直缺少系统性的筛选。这篇 <em>Cell</em> 论文用<strong>单细胞 CRISPR 筛选</strong>直接回答了这个问题。</p>

<h2>命中：Dusp5 与 Zfp219</h2>
<table>
<thead><tr><th>靶点</th><th>敲除后的效应</th><th>性质</th></tr></thead>
<tbody>
<tr><td><strong>Dusp5</strong></td><td>提高 <strong>ERK 磷酸化</strong>，<strong>全局增强</strong> T 细胞增殖</td>
<td>磷酸酶，成药性相对较好</td></tr>
<tr><td><strong>Zfp219</strong></td><td>引发<strong>表观重编程</strong>，提高<strong>细胞毒分子</strong>表达，
<strong>特异地在衰老环境中</strong>增强抗肿瘤免疫</td>
<td>转录因子，直接成药性低</td></tr>
</tbody>
</table>

<p>两个靶点的差别值得注意：<strong>Dusp5 的效应是「全局」的</strong>（年轻和年老都增强增殖），
而<strong>Zfp219 的效应是「衰老特异」的</strong>——
只在衰老环境中才显著增强抗肿瘤免疫。对转化而言后者的吸引力更大，
因为它意味着<strong>治疗窗可能只落在老年患者身上</strong>，对年轻患者的正常免疫功能扰动更小。</p>

<h2>从鼠到人：ZNF219</h2>
<p>这是本条最有分量的一段：作者检测了<strong>人源同源物 ZNF219</strong> 在老年癌症患者瘤内
CD8⁺ T 细胞中的水平，发现<strong>更高</strong>，且<strong>与免疫治疗后更差的生存相关</strong>。</p>

<blockquote><p>这是一个<strong>人-鼠一致性</strong>证据。它在小鼠里被筛出来，在人体样本里与临床结局相关——
这条链比单纯的动物机制研究要硬。</p></blockquote>

<h2>与 ICB 的联用</h2>
<p>作者进一步做了 <strong>Zfp219 敲除 + 免疫检查点抑制剂</strong> 的联合，
结果是<strong>协同</strong>：扩增效应样 CD8⁺ T 细胞，并在老年鼠中实现<strong>肿瘤清除</strong>。
这对临床叙事很关键——如果单用只是「改善」，联用才是「清除」。</p>

<h2>定量：摘要未给</h2>
<p>以下字段一律<strong>待补全文</strong>，本站未做任何推算：</p>
<ul>
<li>CRISPR 文库规模与命中阈值</li>
<li>各组 n、生存 HR 与置信区间</li>
<li>肿瘤生长曲线的效应量</li>
<li>ZNF219 高 / 低表达组的分层方式与 cutoff</li>
<li>ERK 磷酸化与细胞毒分子的变化幅度</li>
</ul>

<h2>局限</h2>
<ul>
<li>筛选<strong>在肿瘤模型内完成</strong>。「衰老 T 细胞功能障碍」的结论能否外推到
<strong>非肿瘤的免疫衰老</strong>（感染、疫苗应答）——这是本站最关心的一点——<strong>未验证</strong>。
老年人流感疫苗应答差是免疫衰老最经典的临床表现，本篇不覆盖它。</li>
<li>ZNF219 的人体证据是<strong>相关性</strong>，不是干预性证据。</li>
<li><strong>Zfp219 作为转录因子，体内可成药性较低</strong>，转化需依赖其下游通路。
Dusp5 是磷酸酶，这条路更现实。</li>
<li>未见<strong>雌雄分列</strong>分析。</li>
</ul>

<h2>证据等级：为什么是 B 不是 A</h2>
<p>它有人体样本的相关性证据，但<strong>没有人体干预</strong>；
所有功能性结论（敲除、联用、肿瘤清除）<strong>全部来自小鼠</strong>。
按本站约定，核心结论来自动物模型即标 B。</p>""",
        related=REL_DUSP5)

    # ══════════ F2 · 肝脏 BDH1 / 3HB → CD8 耗竭 ══════════
    A["Hepatic-BDH1-3HB-CD8-T-Cell-Exhaustion-CellMetab-2026.html"] = dict(
        topic="免疫与炎症", ev="B", tag="研究进展",
        title="衰老让肝脏少产一种酮体，远程把 T 细胞「耗竭」掉：BDH1–3HB–PRKAR1B–CREM 轴",
        crumb="器官代谢远程操控免疫衰老",
        desc="Cell Metabolism 研究显示，衰老抑制肝脏 BDH1 依赖的 β-羟基丁酸（3HB）合成并限制 SLC16A1 介导的摄取，使循环 3HB 生物利用度下降；肝 BDH1 敲除即可复现衰老相关的 CD8⁺ T 细胞功能障碍，而补充 3HB 经蛋白 β-羟基丁酰化逆转缺陷，并大幅恢复衰老微环境下 CAR-T 的抗肿瘤活性。",
        source=lit_src("Cell Metabolism", "2026, 38(10): 2054-2071.e9",
                       "Aging microenvironment induces CD8+ T cell exhaustion by suppressing hepatic "
                       "β-hydroxybutyrylate synthesis",
                       "10.1016/j.cmet.2026.08.009", "42692017",
                       "第一作者 Xiao Yifeng（共 10 位作者）",
                       "摘要级 · 待补全文（订阅墙，PubMed 无 PMCID）"),
        body="""<p>酮体 β-羟基丁酸（3HB）在衰老研究里通常有两个身份：
<strong>能量底物</strong>与<strong>信号分子</strong>。这篇 <em>Cell Metabolism</em> 论文给它加了第三个——
<strong>免疫细胞功能的远程调控者</strong>，并且把「衰老 → 肝脏 → 血液 → T 细胞」这条轴完整走了一遍。</p>

<h2>链条：从肝脏到 T 细胞</h2>
<ol>
<li>衰老<strong>抑制肝脏 BDH1 依赖的 3HB 合成</strong>，并<strong>限制 SLC16A1 介导的 3HB 摄取</strong>，
使循环 3HB 的<strong>生物利用度下降</strong>；</li>
<li><strong>肝 BDH1 敲除即可复现</strong>衰老相关的 CD8⁺ T 细胞功能障碍
（<strong>抗病毒与抗肿瘤免疫双双受损</strong>）——这是因果性的关键一步，
说明不需要「衰老」这个整体状态，缺一个肝酶就够了；</li>
<li><strong>补充 3HB</strong> 可经<strong>蛋白 β-羟基丁酰化</strong>逆转这些缺陷；</li>
<li>用 3HB 衍生化学探针 <strong>3Halk</strong> 联合功能筛选，鉴定出
<strong>PRKAR1B 是 3HB 信号的主要效应器</strong>；</li>
<li>机制终点：<strong>PRKAR1B 的 β-羟基丁酰化抑制转录因子 CREM</strong>，
而 CREM 驱动耗竭相关基因表达。于是 3HB 缺乏 → 抑制被解除 → <strong>耗竭程序被维持</strong>。</li>
</ol>

<blockquote><p>这套逻辑的漂亮之处在于<strong>双向可操作</strong>：
敲掉肝里的 BDH1 就能制造耗竭，补回 3HB 就能解除耗竭。
不是相关，是<strong>可逆的因果</strong>。</p></blockquote>

<h2>最贴近临床的一段：CAR-T</h2>
<p>作者报告<strong>衰老微环境对 CAR-T 抗肿瘤活性的削弱，亦可被 3HB 大幅恢复</strong>。</p>

<p>CAR-T 在老年患者中效果较差是已知问题，通常归因于 T 细胞本身的质量。
这条结果提示：<strong>问题可能部分在 T 细胞之外</strong>——在肝脏的代谢输出上。
如果成立，那么改善 CAR-T 在老年患者中效果的手段，可能不是把细胞改造得更强，
而是把<strong>宿主的代谢环境</strong>调回去。</p>

<h2>定量：摘要未给</h2>
<p>以下一律<strong>待补全文</strong>，本站未推算：</p>
<ul>
<li>循环 3HB 浓度的具体变化幅度（衰老组 vs 年轻组）</li>
<li>肝 BDH1 敲除的效率与各组 n</li>
<li>3HB 补充的剂量、途径与疗程</li>
<li>CAR-T 杀伤效应的恢复幅度与肿瘤生长曲线</li>
<li>PRKAR1B β-羟基丁酰化位点的鉴定方法</li>
</ul>

<h2>局限</h2>
<ul>
<li>核心证据链<strong>全部在小鼠中完成</strong>。人类衰老 T 细胞是否存在同一
<strong>3HB–PRKAR1B–CREM 轴</strong>，未验证。</li>
<li>「3HB 补充」的<strong>人体可及性</strong>未讨论。口服酮体酯或 NR 能否达到等效暴露，
是这条路线能否成立的前提，而摘要没有回答。</li>
<li>CAR-T 部分用的是哪种模型（同系 / 异种、靶点、细胞来源）<strong>摘要未述</strong>。</li>
<li><strong>长期补充 3HB 的安全性</strong>未评估。对老年人而言，
长期酮体干预对骨、肾、血脂的影响是现成的顾虑。</li>
</ul>

<h2>在本站证据群里的位置</h2>
<p>本条与同批的 <strong>CRISPR 筛选 Dusp5/Zfp219</strong> 构成「老年患者免疫治疗响应差」的双解法：
<strong>一个补代谢物（3HB），一个改 T 细胞内在程序</strong>。
前者的转化门槛明显更低——3HB 是可口服的现成分子。</p>""",
        related=REL_3HB)

    # ══════════ F3 · 线粒体移植 HIF-3α-BNIP3 ══════════
    A["Mitochondrial-Transplantation-HIF3A-BNIP3-Mitophagy-Aging-Heart-2026.html"] = dict(
        topic="线粒体", ev="B", tag="研究进展",
        title="衰老心脏的线粒体自噬不是太少，是「堵住了」：HIF-3α 异常上调把 BNIP3 顶过了头",
        crumb="把 mitophagy 缺陷重新定义为流通拥堵",
        desc="Aging Cell 研究提出衰老心脏的线粒体质量控制缺陷是线粒体自噬（mitophagy）流通拥堵而非单纯不足，上游驱动是 HIF-3α–BNIP3 轴：HIF-3α 在衰老心肌细胞中异常上调、直接驱动 BNIP3 过度表达从而触发拥堵；线粒体移植经改善 ATP 稳态抑制该轴，重建 mitophagy 流通并逆转心脏衰老。",
        source=lit_src("Aging Cell", "2026, 25(10): e70720",
                       "Mitochondrial Transplantation Rejuvenates Aging Heart by Restoring Mitophagy Flux "
                       "via the HIF-3α-BNIP3 Axis",
                       "10.1111/acel.70720", "42775695",
                       "第一作者 Jin Ning（共 14 位作者）",
                       "摘要级 · <strong>PMC13599351 免费全文可核验</strong>"),
        body="""<p>「线粒体自噬随年龄下降」几乎是衰老领域的教科书条目。
这篇 <em>Aging Cell</em> 论文提出了一个不同的诊断：<strong>问题不是能力不足，是流通拥堵</strong>。
这个区分不是文字游戏——它直接决定干预方向该是<strong>激活</strong>还是<strong>疏通</strong>。</p>

<h2>重新定义：不是太少，是堵住了</h2>
<p>作者的出发点是：衰老心脏中线粒体质量控制严重受损，通常归因于 mitophagy 稳态被破坏，
但<strong>关键分子驱动因子不明</strong>。他们找到的是 <strong>HIF-3α</strong>。</p>

<p>这里有一个反直觉的点：<strong>HIF-3α 传统上被视为转录抑制因子</strong>，
却在衰老心肌细胞中<strong>异常上调</strong>，并<strong>直接调控 BNIP3 过度表达</strong>，
从而触发 mitophagy 拥堵。</p>

<blockquote><p>BNIP3 是经典的 mitophagy 受体——通常认为「多」是好事，意味着清除更积极。
本文的论点是<strong>过量反而造成流通堵塞</strong>：
受体过表达让自噬流在中间环节堆积，如同高速入口全开但出口只有一个。</p></blockquote>

<h2>干预：线粒体移植</h2>
<p><strong>线粒体移植</strong>（mitochondrial transplantation）通过<strong>改善细胞内 ATP 稳态</strong>
来抑制 HIF-3α–BNIP3 轴的病理过度激活，从而<strong>重建正常的 mitophagy 流通</strong>并逆转心脏衰老。</p>

<p>因果链是：ATP 稳态改善 → HIF-3α 不再异常上调 → BNIP3 回落 → 拥堵解除 → mitophagy 流通恢复。
注意这里的干预<strong>不是直接抑制 BNIP3</strong>，而是从更上游的能量状态入手。</p>

<h2>定量：摘要未给</h2>
<p>以下一律<strong>待补全文</strong>（本文 PMC13599351 免费全文可获取，建议精读补全）：</p>
<ul>
<li>mitophagy 流通量的具体测定方法与数值（年轻 vs 老年）</li>
<li>HIF-3α / BNIP3 的表达变化幅度</li>
<li>心功能指标（EF、舒张功能等）的改善幅度</li>
<li>各组 n 与 P 值</li>
<li><strong>线粒体移植的具体方案</strong>——见下方局限</li>
</ul>

<h2>局限：本站最关心的一条</h2>
<p>「<strong>线粒体移植</strong>」的<strong>细胞来源、制备与递送方案，摘要完全未述</strong>。
这是可复现性与转化的核心问题——没有它，这条结果无法被独立验证，
也无法判断它距离临床应用有多远。</p>

<p>本站倾向把它记作<strong>机制性证据而非治疗路线</strong>：
「mitophagy 是流通拥堵」这个重新定义有价值，
但「移植线粒体」作为一种疗法，其可行性、免疫原性与规模化难度都远未解决。</p>

<p>其他局限：</p>
<ul>
<li>HIF-3α 作为「直接调控 BNIP3」的<strong>证据强度</strong>待全文核实；</li>
<li><strong>拥堵模型与经典「mitophagy 随龄下降」模型的关系与边界未厘清</strong>——
两者在多大程度上是同一现象的不同切面，摘要没有讨论；</li>
<li>长期安全性未评估。</li>
</ul>

<h2>可与本站哪几条对照读</h2>
<p>本条与同批的 <strong>A02（人类自噬流通量是性别与细胞类型特异的）</strong> 可以对照：
两条都指向<strong>「自噬随龄下降」这个概括过于粗糙</strong>——
一条说它在人身上不成立，一条说它的性质根本不是「下降」。</p>""",
        related=REL_MITOTX)

    # ══════════ F4 · 雷帕霉素 / 动脉粥样硬化 ══════════
    A["Rapamycin-Immune-Reprogramming-Aged-Atherosclerosis-AgingCell-2026.html"] = dict(
        topic="代谢与营养", ev="B", tag="研究进展",
        title="在已经长好斑块的老年小鼠身上，雷帕霉素 8 周把斑块巨噬细胞压下来，也压住了淋巴免疫",
        crumb="从延寿扩展到已病状态下的血管免疫重编程",
        desc="Aging Cell 研究在 80–90 周龄雄性 Ldlr⁻/⁻ 小鼠中腹腔给药雷帕霉素 8 周，斑块巨噬细胞含量从对照 0.95±0.09×10⁵ μm² 降至 0.75±0.07×10⁵ μm²（p<0.05）；血管与淋巴组织 T 细胞总数下降并向中枢记忆表型偏移，主动脉 Treg 的 Foxp3、Tgfb1 表达升高，脾与淋巴结中年龄相关 B 细胞减少。",
        source=lit_src("Aging Cell", "2026, 25(10): e70730",
                       "Therapeutic Immune Reprogramming by Rapamycin Attenuates Plaque Inflammation and "
                       "Lymphoid Immune Responses in Aged Atherosclerotic Mice",
                       "10.1111/acel.70730", "42775680",
                       "第一作者 de Mol Jill（共 10 位作者）",
                       "摘要级 · <strong>PMC13599350 免费全文可核验</strong>"),
        body="""<p>雷帕霉素在衰老领域的证据，绝大多数来自<strong>预防性给药</strong>——
在动物还没病的时候开始给，看它延不延寿。
这篇 <em>Aging Cell</em> 论文问的是一个更难、也更接近临床的问题：
<strong>在已经长出斑块的老年动物身上给药，还有没有用？</strong></p>

<h2>设计：80–90 周龄，病变已形成</h2>
<ul>
<li>模型：<strong>80–90 周龄雄性 Ldlr⁻/⁻ 小鼠</strong>——这个月龄的小鼠已有明确动脉粥样硬化病变；</li>
<li>给药：<strong>腹腔注射雷帕霉素，每三周一次，共 8 周</strong>；</li>
<li>评估：<strong>流式细胞术 + 单细胞 RNA 测序</strong>评估全身与斑块免疫，加组织学评估斑块形态；</li>
<li>还做了<strong>主动脉 Treg 的单细胞转录组</strong>，以及体液免疫指标（Tfh、IL-21、生发中心 B、浆细胞、Ig）。</li>
</ul>

<h2>核心定量</h2>
<p>本条最有价值的是一个<strong>带误差棒的数字</strong>：</p>
<blockquote><p>斑块<strong>巨噬细胞含量</strong>从对照 <strong>0.95 ± 0.09 × 10⁵ μm²</strong>
降至 <strong>0.75 ± 0.07 × 10⁵ μm²</strong>（<strong>p < 0.05</strong>）。</p></blockquote>

<p>这是本站记录的雷帕霉素血管证据里，少有的<strong>直接组织学定量终点</strong>，
而不是替代性的免疫指标。</p>

<h2>免疫层面的五条变化</h2>
<ol>
<li>斑块<strong>巨噬细胞含量显著下降</strong>（数值见上）；</li>
<li>血管与淋巴组织 <strong>T 细胞总数减少</strong>，并<strong>向中枢记忆表型偏移</strong>，
以 <strong>CD8⁺ 区室尤为明显</strong>；</li>
<li><strong>调节性 CD4⁺ T 细胞（Treg）相对富集</strong>；
主动脉 Treg 单细胞转录组显示抑制性基因 <strong>Foxp3、Tgfb1 表达升高</strong>；</li>
<li>体液免疫全面回落：<strong>滤泡辅助 T 细胞、IL-21、生发中心 B 细胞、浆细胞</strong>，
以及<strong>总 / 氧化特异性表位特异性免疫球蛋白水平</strong>均下降；</li>
<li>脾与淋巴结中<strong>年龄相关 B 细胞（ABC）减少</strong>。</li>
</ol>

<p>第 5 条值得单独注意：ABC 是近年免疫衰老研究里的热点群体，
在自身免疫与老年炎症中都扮演角色。雷帕霉素能减少它，
与本站已记录的「雷帕霉素作为免疫调节剂」证据方向一致。</p>

<h2>定量：只有巨噬细胞那一项</h2>
<p>除斑块巨噬细胞含量与其 P 值外，以下一律<strong>待补全文</strong>
（本文 PMC13599350 免费全文可获取）：</p>
<ul>
<li>其余免疫群体的<strong>具体变化幅度</strong>（百分比或绝对计数）</li>
<li>各组 <strong>n</strong> 与<strong>给药剂量</strong>（mg/kg）</li>
<li>斑块<strong>大小与稳定性</strong>是否真正改善——见局限</li>
</ul>

<h2>局限</h2>
<ul>
<li><strong>仅用雄性小鼠</strong>，性别外推受限。这一点对动脉粥样硬化尤其重要，
因为该病的性别差异本身就显著。</li>
<li>8 周给药后，<strong>斑块稳定性 / 大小是否真正改善</strong>（而非仅仅是免疫组成改变），
<strong>摘要未给出硬终点</strong>。免疫组成改善是好事，但读者关心的是斑块本身。</li>
<li>雷帕霉素的<strong>免疫抑制副作用</strong>在老年适应症中的风险-获益<strong>未讨论</strong>。
本文观察到的 Tfh / 生发中心 B / Ig 全面下降，
既是「抗动脉粥样硬化」的机制，也<strong>正是免疫抑制的表现</strong>——
这两面在本文中是同一件事，作者未做权衡。</li>
<li>剂量换算到人需谨慎。</li>
</ul>

<h2>在本站证据群里的位置</h2>
<p>与同批的 <strong>PD-L2 免疫检查点</strong>、<strong>Dusp5/Zfp219 CRISPR 筛选</strong>
同属「免疫通路抗衰」证据群。本条的独特价值在于它<strong>从延寿扩展到了已病状态</strong>，
并给了带误差棒的组织学终点。</p>""",
        related=REL_RAPA)

    # ══════════ F5 · SIRT6 / MDL-800 椎间盘 ══════════
    A["SIRT6-Activator-MDL-800-Intervertebral-Disc-AgingCell-2026.html"] = dict(
        topic="NAD+与sirtuin", ev="B", tag="研究进展",
        title="24 月龄小鼠长期吃 SIRT6 激动剂：椎间盘退变评分降了，H3K9ac 降了，自噬升了",
        crumb="SIRT6 药理激活的体内证据",
        desc="Aging Cell 研究在 24 月龄小鼠中长期全身给予 SIRT6 小分子激动剂 MDL-800，椎间盘形态健康、细胞活力提高、退变评分降低；H3K9ac、H3K36me3、H3K79me2 下降，p21、IL-6、TGF-β、CCL2 降低，自噬提高而不影响生物能量学；系统耐受性良好，仅见椎体结构参数轻微下降与轻度痛觉过敏。",
        source=lit_src("Aging Cell", "2026, 25(10): e70709",
                       "SIRT6 Activation Improves Intervertebral Disc Health in the Aging Spine",
                       "10.1111/acel.70709", "42895774",
                       "第一作者 Ramteke Pranay（共 12 位作者）",
                       "摘要级 · <strong>PMC13679769 免费全文可核验</strong>"),
        body="""<p>SIRT6 是 NAD⁺ 依赖的去乙酰化酶，在衰老研究里的位置一直有点尴尬：
<strong>功能缺失的证据很硬</strong>（敲掉它衰老加速），
但<strong>「激活它」的证据长期停留在概念层面</strong>。
这篇 <em>Aging Cell</em> 论文补上了这个缺口——而且是在<strong>老年动物</strong>身上，
用<strong>长期全身给药</strong>做的。</p>

<h2>干预：MDL-800，24 月龄，长期</h2>
<ul>
<li>药物：<strong>SIRT6 小分子激动剂 MDL-800</strong>（该分子在抗衰老领域已被多个实验室采用）；</li>
<li>对象：<strong>24 月龄小鼠</strong>——相当于人类的老年期，椎间盘已有自然退变；</li>
<li>方式：<strong>长期全身给予</strong>；</li>
<li>评估维度覆盖组织形态、表观修饰、多组学、代谢、免疫系统与行为安全性。</li>
</ul>

<h2>核心结果</h2>
<ol>
<li><strong>椎间盘本身</strong>：形态健康、细胞活力提高、<strong>退变评分降低</strong>；</li>
<li><strong>衰老标志</strong>：<strong>p21、IL-6、TGF-β、CCL2 水平下降</strong>；</li>
<li><strong>表观修饰</strong>：SIRT6 激活降低 <strong>H3K9ac</strong>（这是 SIRT6 最直接的酶学读出），
并改善细胞外基质质量；</li>
<li><strong>多组学</strong>：组织 RNA-Seq、组蛋白 H3 修饰测定与 ATAC-seq 显示
<strong>H3K9ac、H3K36me3、H3K79me2 均下降</strong>，表观-转录景观被重塑；</li>
<li><strong>自噬</strong>：<strong>MDL-800 提高自噬而不影响椎间盘细胞的生物能量学</strong>；
这一点很重要——多数自噬诱导剂会连带压掉线粒体功能，这里没有；</li>
<li><strong>系统耐受性</strong>：血浆代谢组、骨髓与脾的 scRNA-seq 与细胞因子谱
显示<strong>系统耐受性良好</strong>。</li>
</ol>

<blockquote><p>「<strong>提高自噬但不影响生物能量学</strong>」值得注意：
它意味着自噬提升不是以牺牲能量代谢为代价的。
这与本站同批的 <strong>A02（自噬流通量在人身上是性别与细胞类型特异的）</strong> 可以对照阅读——
两条都提醒「自噬随龄下降」这个概括过于粗糙。</p></blockquote>

<h2>安全性：不是没有代价</h2>
<p>摘要报告<strong>无椎体骨折，运动功能与行为未受影响</strong>，这是好消息。
但同一段里也出现了两处需要标记的信号：</p>
<ul>
<li><strong>椎体结构参数轻微下降</strong>；</li>
<li><strong>轻度痛觉过敏</strong>。</li>
</ul>
<p>两者都不算严重，但都不是零。对一个<strong>拟长期口服</strong>的抗衰老分子而言，
这两条正是后续转化中必须盯住的指标。<strong>本站如实记录，不做淡化。</strong></p>

<h2>定量：摘要未给</h2>
<p>以下一律<strong>待补全文</strong>（本文 PMC13679769 免费全文可获取，建议精读补全）：</p>
<ul>
<li>退变评分的变化幅度与评分体系</li>
<li>各组 <strong>n</strong>、MDL-800 的<strong>剂量与疗程</strong></li>
<li>H3K9ac / H3K36me3 / H3K79me2 的变化幅度</li>
<li>p21 / IL-6 / TGF-β / CCL2 的变化幅度</li>
<li>自噬指标的具体读数</li>
</ul>

<h2>局限</h2>
<ul>
<li><strong>仅老年鼠单一模型</strong>，未见<strong>年轻对照</strong>，也未见<strong>雌雄分列</strong>。</li>
<li>MDL-800 的长期全身安全性虽称良好，但已有上述两处信号，<strong>风险-收益需在转化时权衡</strong>。</li>
<li><strong>椎间盘局部药物暴露量与全身暴露的关系未述</strong>——长期全身给药是否必要，无法判断。</li>
<li><strong>人椎间盘细胞与小鼠差异很大</strong>（人椎间盘细胞更大、营养来源不同、髓核特性不同），
种属外推的限制比其他组织更严格。</li>
</ul>

<h2>为什么这条在 NAD⁺ 主线里重要</h2>
<p>本站已记录的 NAD⁺ 干预绝大多数落在<strong>上游补充</strong>：
补充 NR / NMN，看能不能把 NAD⁺ 池抬起来。
本条的位置更<strong>下游、更特异</strong>——直接激活 NAD⁺ 的<strong>效应器</strong> SIRT6，
绕开了「补了前体但组织内 NAD⁺ 未必提升」这个长期存在的分歧。</p>

<p>而且它给的是<strong>从表观修饰 → 组织形态 → 系统安全性</strong>的完整链条，
而不是单点读数。</p>""",
        related=REL_SIRT6)

    # ══════════ F6 · NR 与老年小鼠小胶质细胞 ══════════
    A["Nicotinamide-Riboside-Microglia-Cognition-Aged-Mice-GeroScience-2026.html"] = dict(
        topic="NAD+与sirtuin", ev="B", tag="研究进展",
        title="NR 补 8 周：老年鼠的小胶质细胞回到年轻态，筑巢、Y 迷宫、新物体识别都回来了",
        crumb="NAD⁺ 与认知衰退之间的胶质细胞环节",
        desc="GeroScience 研究显示 22 月龄雄性小鼠补充烟酰胺核糖（NR）400 mg/kg × 8 周，改善筑巢、Y 迷宫自发交替与新物体识别；IBA1 与 GFAP 活化降低接近年轻表型，小胶质细胞活化、炎症通路与趋化因子产生降低，年龄依赖（ADEM）与疾病相关（DAM）小胶质细胞转录签名降低、稳态态增强。",
        source=lit_src("GeroScience", "2026, 48(5): 6629-6646",
                       "Nicotinamide riboside supplementation restores microglial health and improves "
                       "cognition in aged male mice",
                       "10.1007/s11357-025-01959-1", "41273482",
                       "第一作者 Thiyagarajan Ramkumar（共 12 位作者）",
                       "摘要级 · <strong>PMC13601472 免费全文可核验</strong>"),
        body="""<p>60 岁以上人群中约 <strong>1/6</strong> 存在认知损害，预计 2030 年超过 <strong>7,500 万人</strong>。
NAD⁺ 水平下降与小胶质细胞功能随龄改变，都被认为是促成因素。
但「补 NR → 改善认知」这个链条里，<strong>中间那一环究竟是什么</strong>，
证据一直不够具体。这篇 <em>GeroScience</em> 论文把这一环指向了<strong>小胶质细胞</strong>。</p>

<h2>设计：三组，正常衰老而非疾病模型</h2>
<ul>
<li><strong>6 月龄</strong>（年轻）</li>
<li><strong>22 月龄</strong>（老年）</li>
<li><strong>22 月龄 + NR</strong>（<strong>400 mg/kg 体重 × 8 周</strong>）</li>
<li>均为<strong>雄性小鼠</strong></li>
</ul>

<p>这里有一个关键设计选择值得先说：作者用的是<strong>正常衰老</strong>小鼠，
<strong>不是 AD 模型、不是神经退行疾病模型</strong>。
这意味着 NR 的获益<strong>不限于病理状态</strong>——这一点决定了这条证据的适用范围。</p>

<h2>行为学：三项都动了</h2>
<table>
<thead><tr><th>测试</th><th>反映的能力</th></tr></thead>
<tbody>
<tr><td><strong>筑巢能力</strong></td><td>工具性日常活动</td></tr>
<tr><td><strong>Y 迷宫自发交替</strong></td><td>空间工作记忆</td></tr>
<tr><td><strong>新物体识别</strong></td><td>识别记忆</td></tr>
</tbody>
</table>

<p>NR <strong>改善或预防</strong>了这三项的衰退。其中<strong>筑巢</strong>尤其值得一提：
它是啮齿类里少有的、与人类「工具性日常活动」直接对应的范式，
在认知衰退研究中的生态效度高于多数迷宫任务。</p>

<h2>机制：小胶质细胞的表型回退</h2>
<ul>
<li>NR <strong>降低小胶质细胞（IBA1）与星形胶质细胞（GFAP）活化</strong>，<strong>使之接近年轻表型</strong>；</li>
<li>基因表达谱：<strong>Aged+NR 组小胶质细胞活化、炎症通路与趋化因子产生均降低</strong>；</li>
<li>同时<strong>学习与记忆、胶质生成相关基因上调</strong>；</li>
<li>NR 还<strong>降低了年龄依赖（ADEM）与疾病相关（DAM）小胶质细胞的转录签名，增强稳态态</strong>。</li>
</ul>

<blockquote><p><strong>ADEM 与 DAM 是同一群小胶质细胞的两种「坏状态」</strong>——
ADEM 与正常衰老相关，DAM 与神经退行病理相关。
NR 把两个签名同时压低、把稳态态抬高，
比单纯说「抗炎」要精确得多。</p></blockquote>

<h2>与本站已有人体证据的配对</h2>
<p>同批还收录了 <strong>板桥队列（Itabashi Longitudinal Study on Aging）</strong> 的人体结果：
全血 NAD⁺ 中位浓度在衰弱者中低于非衰弱者（24.00 vs 25.00 μmol/L）。
两条构成「<strong>动物机制 + 人体关联</strong>」的配对——
本站不把这种配对读成因果，但它是 NAD⁺ 主线里目前能拿到的最完整证据组合。</p>

<h2>定量：摘要未给</h2>
<p>可引用的定量是 <strong>22 月龄、NR 400 mg/kg × 8 周、雄性</strong>。
以下一律<strong>待补全文</strong>：</p>
<ul>
<li>各行为学测试的具体数值、n 与 P 值</li>
<li>IBA1 / GFAP 活化降低的幅度</li>
<li>差异表达基因数量</li>
<li>ADEM / DAM 签分的判定阈值</li>
<li>组织 / 血液 NAD⁺ 是否真的提升（**这是最关键的一项**）</li>
</ul>

<h2>局限</h2>
<ul>
<li><strong>仅雄性小鼠</strong>——性别外推受限，而认知衰退的性别差异本身显著。</li>
<li><strong>400 mg/kg 换算到人体偏高</strong>，人体等效剂量的可及性存疑。
这是 NAD⁺ 前体研究里的通病，本站反复标记。</li>
<li>观察 <strong>8 周</strong>，<strong>长期效果与停药后是否回弹未知</strong>。</li>
<li>认知测试种类有限，未包括更复杂的执行功能范式。</li>
<li>ADEM / DAM 签名的判定<strong>依赖特定小鼠数据集</strong>，跨研究可比性有限。</li>
</ul>

<h2>在 NAD⁺ 证据谱里的位置</h2>
<p>本站已记录的 NAD⁺ 证据大致分三层：<strong>人体 NAD⁺ 浓度与表型的关联</strong>（板桥）、
<strong>临床前给药的功能改善</strong>（本条）、<strong>临床试验的结果</strong>（NOPARK 3 期阴性）。
本条处在中间层，且给出了<strong>行为学 + 胶质细胞表型</strong>的双层读数——
比「补了 NAD⁺、某个标志物动了」要更接近机制。</p>""",
        related=REL_NR)

    # ══════════ F7 · iNSC 表观去衰老动力学 ══════════
    A["Epigenetic-DeAging-Kinetics-iNSC-Blood-Cells-AgingCell-2026.html"] = dict(
        topic="表观遗传时钟", ev="B", tag="研究进展",
        title="101 岁供体的血细胞转成神经干细胞后，表观年龄只剩 5%：但去衰老要好几周才完成",
        crumb="表观去衰老的动力学与增殖依赖性问题",
        desc="Aging Cell 研究用 SOX2 与 cMYC 把 0–101 岁供者的红系祖细胞直接转化为诱导神经干细胞（iNSC），表观遗传时钟显示低代次与高代次分别仅保留供者原始年龄的约 13% 与 5%；去衰老持续数周、甚至在增殖抑制条件下仍进行，不依赖细胞分裂。",
        source=lit_src("Aging Cell", "2026, 25(10): e70751",
                       "Protracted Fate Acquisition and Epigenetic De-Aging During Induced Neural Stem Cell "
                       "Conversion of Human Blood Cells",
                       "10.1111/acel.70751", "42829448",
                       "第一作者 Berg Lea Jessica（共 9 位作者）",
                       "摘要级 · <strong>PMC13634082 免费全文可核验</strong>"),
        body="""<p>「重编程能把表观年龄抹掉」这件事已经不算新闻。
真正悬而未决的是一个方法论问题：<strong>表观去衰老需不需要细胞增殖？</strong>
这个问题的答案直接决定了重编程机制的模型——是分裂驱动甲基化稀释，
还是存在某种不依赖 DNA 复制的主动去甲基化过程。</p>

<p>这篇 <em>Aging Cell</em> 论文给出了明确答案：<strong>不需要。</strong></p>

<h2>设计：SOX2 + cMYC，红系祖细胞 → iNSC</h2>
<ul>
<li>方法：用 <strong>SOX2 与 cMYC</strong> 两个重编程因子，
把供者的<strong>红系祖细胞</strong>直接转化为<strong>诱导神经干细胞（iNSC）</strong>；</li>
<li>这是<strong>直接转分化</strong>——<strong>不经过多能态</strong>；</li>
<li>供者年龄跨度 <strong>0–101 岁</strong>——这是本条最大的亮点。</li>
</ul>

<p>「不经过 iPSC 多能态」这个设计选择很重要：
多能态本身就会把表观年龄抹掉，所以走 iPSC 路线<strong>无法回答去衰老的动力学</strong>。
直接转分化保留了「从成年细胞出发」这个前提。</p>

<h2>核心定量：13% 与 5%</h2>
<blockquote><p>表观遗传时钟显示：<strong>低代次与高代次 iNSC
分别仅保留供者原始年龄的约 13% 与 5%</strong>。</p></blockquote>

<p>换句话说，一个 <strong>101 岁供体</strong>的细胞转成 iNSC 后，
表观时钟读数大约相当于<strong>5 岁</strong>。这不是「变年轻一点」，是<strong>几乎归零</strong>。</p>

<h2>关键发现：去衰老是旷日持久的</h2>
<ol>
<li>去衰老<strong>持续数周</strong>，不是几小时内的切换；</li>
<li><strong>在增殖抑制条件下仍在进行</strong>——这是本条的机制核心；</li>
<li>年轻与年老供者来源 iNSC 的转录组差异<strong>随转化时间延长而消散</strong>；</li>
<li>已建立的 iNSC 系<strong>缺乏年龄相关的细胞标志</strong>，与 iPSC 及其衍生物类似。</li>
</ol>

<blockquote><p>第 2 条值得单独说明：如果去衰老<strong>不依赖细胞分裂</strong>，
那它<strong>不能</strong>被解释为「分裂稀释了旧甲基化标记」——
必须存在某种<strong>主动的表观重塑过程</strong>。
这为重编程研究提供了一个可检验的机制方向。</p></blockquote>

<h2>定量：给了幅度，没给规模</h2>
<p>可引用定量是<strong>供者年龄跨度 0–101 岁</strong>与<strong>13% / 5%</strong>。
以下一律<strong>待补全文</strong>：</p>
<ul>
<li>供者<strong>样本数</strong>（跨年龄是否均匀？老年端有几个？）</li>
<li>使用的是<strong>哪一类表观时钟</strong>（Horvath？GrimAge？组织特异？）</li>
<li>时间序列的<strong>采样点</strong>与「数周」的具体时长</li>
<li>「增殖抑制」的具体手段与检测到的去衰老幅度</li>
<li>转录组差异消散的基因数</li>
</ul>

<h2>局限</h2>
<ul>
<li><strong>重编程因子含 cMYC</strong>——致癌风险。转化路径的安全性需评估。</li>
<li><strong>去衰老的持久性未验证</strong>：去掉因子后是否回弹？iNSC 在体外长期培养后表观年龄是否稳定？</li>
<li><strong>表观时钟在转分化细胞中的适用性本身存在争议</strong>——
这些时钟多是在血 / 组织来源上训练的，用在神经谱系细胞上读数是否可靠，学界没有共识。
这一点必须提醒：<strong>5% 这个数字的可信度，取决于时钟在该细胞类型上的效度</strong>。</li>
<li><strong>功能层面的「年轻化」证据不足</strong>——
甲基化年龄归零不等于功能恢复年轻态。</li>
</ul>

<h2>在部分重编程证据谱里的位置</h2>
<p>本站已记录的部分重编程证据大致分三类：
<strong>临床管线</strong>（Life Biosciences ER-100 首批人体数据、NewLimit 融资）、
<strong>体内基因治疗</strong>（OSK 在人神经元与胶质细胞、OSKTF 卒中康复）、
<strong>体外机制</strong>（本条）。</p>

<p>本条处在最远的一环——<strong>转化距离最远</strong>，但它回答的是一个基础问题：
<strong>表观去衰老到底怎么发生的</strong>。
对判断「部分重编程能不能安全地用于人体」，这个问题的答案最终会影响剂量与时程设计。</p>""",
        related=REL_INSC)

    # ══════════ F8 · MTR4 血管内皮年轻因子 ══════════
    A["MTR4-Youth-Factor-Vascular-Endothelium-AgingCell-2026.html"] = dict(
        topic="血管衰老", ev="B", tag="研究进展",
        title="一个跨三物种的血管「年轻因子」：MTR4 被 SYVN1 泛素化降解，线虫里过表达延寿可比经典长寿模型",
        crumb="SYVN1–MTR4–BUB3/BUBR1 是一条全新通路",
        desc="Aging Cell 研究鉴定 RNA 解旋酶 MTR4 为血管内皮保守年轻因子：MTR4 在衰老 HUVEC 与老年小鼠主动脉中显著下降且不依赖细胞周期退出；衰老诱导 E3 泛素连接酶 SYVN1 上调，使 MTR4 发生 K638 连接的多聚泛素化并经蛋白酶体降解。小鼠内皮特异敲低促进血管功能障碍与多器官衰老，线虫 mtr-4 过表达显著延长寿命。",
        source=lit_src("Aging Cell", "2026, 25(10): e70774",
                       "MTR4: A Conserved Youth Factor for Vascular Endothelium",
                       "10.1111/acel.70774", "42885357",
                       "第一作者 Guo Zhenyuan（共 8 位作者）",
                       "摘要级 · <strong>PMC13673228 免费全文可核验</strong>"),
        body="""<p>「血管衰老驱动全身衰老」是衰老领域的主线假说之一，
但<strong>维持内皮年轻态的内源性因子</strong>长期基本未知。
这篇 <em>Aging Cell</em> 论文给出了一个候选：<strong>MTR4</strong>。
更难得的是它在<strong>人细胞—小鼠—线虫</strong>三个层次上给出了<strong>方向一致且双向</strong>的证据。</p>

<h2>双向证据</h2>
<table>
<thead><tr><th>层次</th><th>干预</th><th>结果</th></tr></thead>
<tbody>
<tr><td>人 HUVEC（体外）</td><td>敲低 MTR4</td><td>驱动增殖中的 HUVEC <strong>进入早衰</strong></td></tr>
<tr><td>人 HUVEC（体外）</td><td>过表达 MTR4</td><td>经<strong>稳定 BUB3、维持 BUBR1</strong> 恢复衰老细胞的年轻表型</td></tr>
<tr><td>小鼠（内皮特异）</td><td>敲低 Mtr4</td><td><strong>促进血管功能障碍与多器官衰老</strong></td></tr>
<tr><td>小鼠（内皮特异）</td><td>过表达 Mtr4</td><td><strong>缓解</strong></td></tr>
<tr><td>线虫</td><td>过表达 mtr-4</td><td><strong>显著延长寿命</strong>，幅度「可比经典长寿模型」</td></tr>
<tr><td>线虫</td><td>敲低 mtr-4</td><td><strong>加速衰老</strong></td></tr>
</tbody>
</table>

<p>六个格子、三个物种、双向操作、方向完全一致——这种一致性在衰老因子里不常见。</p>

<h2>机制：SYVN1 把它泛素化掉了</h2>
<p>下降的机制也被找到了：</p>
<ol>
<li>MTR4 蛋白在衰老 HUVEC 与老年小鼠主动脉中<strong>显著下降</strong>，
且<strong>不依赖一般性细胞周期退出</strong>（这一点排除了「细胞不分裂了所以蛋白少了」的平凡解释）；</li>
<li>衰老<strong>诱导 E3 泛素连接酶 SYVN1 上调</strong>；</li>
<li>SYVN1 促使 MTR4 发生 <strong>K638 连接的多聚泛素化</strong>并经<strong>蛋白酶体降解</strong>；</li>
<li>下游：MTR4 缺失驱动早衰；过表达则通过<strong>结合并稳定 BUB3</strong>、
<strong>维持 BUBR1 表达</strong>来恢复年轻表型。</li>
</ol>

<blockquote><p>MTR4 是 RNA 解旋酶 / 核 RNA 外切体辅因子，
通常被放在 RNA 代谢的筐里。这里它接到了 <strong>BUB3/BUBR1</strong>——
纺锤体组装检查点的组分，通常与有丝分裂保真度相关。
「RNA 外切体辅因子 → 检查点蛋白 → 内皮衰老」这条链条是全新的。</p></blockquote>

<h2>定量：几乎全是定性</h2>
<p>以下一律<strong>待补全文</strong>，本站未做任何推算：</p>
<ul>
<li><strong>线虫延寿幅度</strong>——摘要说「可比经典长寿模型、超过多数单基因干预」，
但<strong>这是定性表述，没有百分比</strong>。这是本条规定要核的第一件事；</li>
<li>小鼠 n 与血管功能指标变化；</li>
<li>MTR4 蛋白下降幅度；</li>
<li>SYVN1 上调幅度与 K638 位点的鉴定方法。</li>
</ul>

<h2>局限</h2>
<ul>
<li><strong>三层次的证据强度严重不均</strong>：
人体证据<strong>仅 HUVEC 体外</strong>；小鼠只有内皮特异的敲低 / 过表达；
只有线虫给了<strong>寿命</strong>这个硬终点。
从「人 HUVEC 体外」到「人内皮在体」，距离不小。</li>
<li>「超过多数单基因干预」是<strong>定性表述</strong>，缺具体百分比，需全文核实。</li>
<li><strong>MTR4 作为 RNA 外切体辅因子，其过表达的治疗可行性完全未讨论</strong>——
递送、剂量、过表达 RNA 代谢蛋白的系统性后果，都是问题。</li>
<li><strong>内皮特异过表达的长期后果未评估</strong>——
尤其是<strong>血管增生风险</strong>。让内皮「回春」会不会顺带促进病理性血管生成，摘要没有回答。</li>
</ul>

<h2>可追踪的转化切口</h2>
<p>如果 MTR4 是被 SYVN1 降解的，那么<strong>抑制 SYVN1</strong> 是一个理论上的干预点
——E3 连接酶是相对可成药的靶点类别，比过表达 RNA 解旋酶现实得多。
本站建议列为高优先级补全文，并追踪是否有靶向 SYVN1 的小分子。</p>

<h2>在本站证据群里的位置</h2>
<p>与同批的 <strong>LATS1/2–CD38 内皮衰老</strong>、<strong>雷帕霉素的血管免疫重编程</strong>
同属血管衰老板块。本条的独特之处在于给出了<strong>一个内源性「年轻因子」</strong>——
而不是又一个「敲掉什么会更老」的功能缺失证据。</p>""",
        related=REL_MTR4)

    # ══════════ F9 · 蛋白组器官时钟 vs 死亡 ══════════
    A["Plasma-Proteomic-Organ-Clocks-Mortality-LBC1936-AgingCell-2026.html"] = dict(
        topic="表观遗传时钟", ev="B", tag="研究进展",
        title="蛋白组器官时钟确实能预测死亡——但没赢过便宜得多的 GrimAge2、脑体积、握力和认知",
        crumb="对血浆蛋白器官时钟的冷静基准测试",
        desc="在 Lothian Birth Cohort 1936（861 人、444 例死亡、16 年随访）中，蛋白组器官时钟里肝脏（HR/SD 1.43）、免疫（1.42）与心脏（1.38）的年龄加速与全因死亡关联最强，但仍弱于表观时钟 GrimAge2、脑总体积、灰质体积、呼吸功能与认知（HR/SD 1.44–1.62）。9,703 个血浆蛋白中 368 个与死亡相关。",
        source=lit_src("Aging Cell", "2026, 25(10): e70747",
                       "Multimodal Ageing Biomarkers and Plasma Proteomic Signatures Associated With "
                       "All-Cause Mortality",
                       "10.1111/acel.70747", "42823846",
                       "第一作者 Pyrgioti Maira（共 15 位作者）",
                       "摘要级 · <strong>PMC13631562 免费全文可核验</strong>"),
        body="""<p>血浆蛋白组估算器官年龄是近两年的热点方向，
商业上也已经有人把它包装成「器官衰老检测」。
但一个一直缺的问题是：<strong>它到底比现有标志物好多少？</strong>
这篇 <em>Aging Cell</em> 论文做的就是<strong>一次基准测试</strong>——
而结论是<strong>还没有更好</strong>。</p>

<h2>队列：LBC1936</h2>
<ul>
<li><strong>Lothian Birth Cohort 1936</strong>：全部出生于 1936 年的苏格兰裔队列，是衰老研究里少数几个
有<strong>极长随访</strong>的出生队列；</li>
<li>n = <strong>861</strong>；全因死亡 <strong>444 例</strong>；随访 <strong>16 年</strong>；</li>
<li>同时具备<strong>表观时钟、端粒长度、体能、神经影像、认知</strong>等多模态数据——
这正是能做基准比较的前提。</li>
</ul>

<h2>核心结果：蛋白组器官时钟有效，但不是最强的</h2>
<p>蛋白组器官时钟里，三个器官的年龄加速与死亡关联最强：</p>
<table>
<thead><tr><th>器官时钟</th><th>HR / SD（95% CI）</th></tr></thead>
<tbody>
<tr><td><strong>肝脏</strong></td><td><strong>1.43</strong>（1.30–1.58）</td></tr>
<tr><td><strong>免疫</strong></td><td><strong>1.42</strong>（1.29–1.57）</td></tr>
<tr><td><strong>心脏</strong></td><td><strong>1.38</strong>（1.25–1.53）</td></tr>
</tbody>
</table>

<p>但对照标志物<strong>全线更高</strong>：</p>
<blockquote><p><strong>表观时钟 GrimAge2、脑总体积、灰质体积、呼吸功能与认知</strong>——
HR/SD <strong>1.44–1.62</strong>。</p></blockquote>

<p>差距不算悬殊，但<strong>方向是明确的</strong>：
<strong>便宜得多的指标目前仍胜过更贵的蛋白组器官时钟</strong>。</p>

<h2>第二个发现：368 个死亡相关蛋白</h2>
<p>作者对 <strong>9,703 个血浆蛋白靶点</strong>做了生存分析，识别出 <strong>368 个</strong>与死亡相关的候选蛋白。
功能上的分化很有意思：</p>
<ul>
<li><strong>高风险蛋白</strong>富集于<strong>免疫功能</strong>；</li>
<li><strong>低风险蛋白</strong>富集于<strong>基因组稳定性与细胞功能</strong>相关通路。</li>
</ul>

<p>这个方向和本站记录的多个免疫衰老证据群一致——免疫指标在死亡风险里反复出现。</p>

<h2>为什么这条值得收录</h2>
<p>因为它是一个<strong>否证性的方法学结果</strong>。
热点方向通常会吸引大量投入，而这条结果给出的信息是：
<strong>现阶段，多模态组合优于单一蛋白组器官时钟。</strong></p>

<p>对做衰老标志物选择的人，这个结论直接影响实验设计：
如果你的目标是预测死亡 / 疾病风险，
<strong>GrimAge2 + 体能 + 认知 + 呼吸功能</strong>的性价比高于上一套昂贵的蛋白组 panel。</p>

<h2>定量：给了 HR，没给蛋白清单</h2>
<p>可引用定量是 <strong>n=861、死亡 444 例、随访 16 年、HR/SD 与 95% CI、368 个蛋白</strong>。
以下一律<strong>待补全文</strong>：</p>
<ul>
<li>蛋白筛选的 <strong>FDR 阈值</strong></li>
<li><strong>368 个蛋白的完整清单</strong></li>
<li>蛋白组平台的交叉验证（SomaLogic / Olink 的特异性效应）</li>
<li>多变量模型中各标志物的独立贡献</li>
</ul>

<h2>局限</h2>
<ul>
<li><strong>单一起源队列</strong>（1936 年出生、苏格兰裔）——
队列效应强，且出生年份本身就是混杂因素。外推性受限。</li>
<li><strong>观察性设计</strong>，无法区分因果。</li>
<li>蛋白组平台（SomaLogic / Olink）的<strong>特异性效应未交叉验证</strong>。</li>
<li><strong>反向因果的可能</strong>：器官时钟与死亡的关联可能受基线疾病影响——
器官年龄「加速」也许正是疾病的结果，而不是它的前兆。这一点摘要没有讨论。</li>
</ul>

<h2>在本站证据群里的位置</h2>
<p>与同批的 <strong>LivAge 在线衰老时钟</strong>、<strong>DNAm 时钟 meta 分析</strong>、
以及<strong>深度学习 SASP Score</strong>同属「衰老标志物基准比较」板块。
本条的定位最清晰：<strong>它是一个冷静的对照，不是一个新发现。</strong></p>""",
        related=REL_PROT)

    ga.A = A
    ga.main()


if __name__ == "__main__":
    main()
