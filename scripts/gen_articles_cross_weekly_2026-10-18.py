#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_articles_cross_weekly_2026-10-18.py —— 内容摄入第 15 批（交叉周报 2026-10-18）

来源与判定
──────────
事实源：元层《临床×文献交叉周报_2026-10-18》（dwyAwojtLOeF，实测 29,189 B，
        7660605 根因修复后**首次全程自动化自产出**，非人工代跑）。

四路查重结果（harvest-cross-1018.json）只抽出 3 条候选且 2 条 confidence=none，
这是周报体裁（散文式标题）与查重器（卡片编号/DOI 抽取）不匹配所致。
按硬规则「站内搜不到 ≠ 漏收」，对 13 个主表 DOI 逐个 grep news/*.html 原文硬核验：

  已收录（DOI 精确命中站内原文）：
    10.1038/s43587-026-01234-8 → Transcriptomic-Reprogramming-Screen-Identifies-SRSF1-NatureAging-2026.html
    10.1038/s43587-026-01238-4 → Lymph-Node-Contraction-Links-Sex-biased-NatureAging-2026.html
    ER-100 / OSK               → Life-Biosciences-ER-100-First-Human-Data-AAO-2026.html
    D+Q MASH RCT（同研究）      → Dasatinib-Quercetin-Senolytic-MASH-Liver-Fibrosis-RCT-2026.html
  未收录（0 篇命中）→ 真漏收：
    10.1001/jama.2026.18828（NOPARK，JAMA 三期）
    10.1038/s44318-026-00922-w / 10.1007/s11357-025-01990-2（时钟可靠性）
    10.1016/j.celrep.2026.117849（NR 组织双刃剑）
    10.1177/0271678X261490342（APOE4 雷帕霉素）

本批只写最硬的一条漏收：NOPARK。理由——它是 NAD⁺ 方向迄今规模最大、级别最高
（JAMA 三期 RCT）的人体终点读出，且为**阴性**，而站内 NAD⁺ 主题下已有 4 篇多为
正面/中性叙述，缺这条反向锚点会构成系统性偏向。
其余未收录项多为动物/综述/相邻主题，留待下轮，不凑数。

数字来源：PubMed E-utilities 官方摘要（PMID 42848371 / DOI 10.1001/jama.2026.18828），
        本脚本撰写时已独立复核，全部定量与官方摘要逐字一致。
        周报原文未记录的 NCT03568968、PMID、及「PI 持 NR 治 PD 专利」背景系本轮补充。
"""
import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATE = "2026-10-18"

sys.argv = ["gen_articles.py", ROOT, "/dev/null", DATE]
_spec = importlib.util.spec_from_file_location(
    "ga", os.path.join(ROOT, "scripts", "gen_articles.py"))
ga = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ga)

A = {}

A["NOPARK-NR-Early-Parkinson-Phase3-JAMA-2026.html"] = dict(
    topic="神经退行", ev="A", tag="临床试验",
    title="NOPARK 三期揭盲：410 人每日 1000 mg NAD⁺ 前体一年，主要终点显著劣于安慰剂",
    crumb="NOPARK 三期 · JAMA 2026-10-08",
    desc="挪威 11 中心、393 人纳入主要分析的随机双盲安慰剂对照三期：早期帕金森病患者口服烟酰胺核糖苷 500 mg 每日两次共 52 周，MDS-UPDRS 总分较安慰剂组差 2.72 点（P=.02），非运动症状负担亦更重。这是 NAD⁺ 前体在神经退行领域迄今级别最高、规模最大的人体终点读出，且由持有 NR 治疗帕金森病专利的团队自己做出。",
    source=('<a href="https://doi.org/10.1001/jama.2026.18828" target="_blank" rel="noopener noreferrer">'
            'Brakedal B, et al. Nicotinamide Riboside for Patients With Early-Stage Parkinson Disease: '
            'The NOPARK Randomized Clinical Trial. <em>JAMA</em>. 2026 Oct 8. '
            'DOI: 10.1001/jama.2026.18828</a>（PMID 42848371 · ClinicalTrials.gov NCT03568968 · '
            '全文为在线预发表，本文仅依据官方摘要撰写，定量数据未作推断）'),
    body="""<p>NAD⁺ 前体是过去十年最受热捧的「抗衰老分子」之一：它能可靠地把人体血液中的 NAD⁺ 水平翻倍，动物模型里改善线粒体功能的证据成堆。但把这两个事实连成「因此能治神经退行病」的那一步，一直缺一块硬证据。2026 年 10 月 8 日 <em>JAMA</em> 在线发表的挪威 <strong>NOPARK 三期试验</strong>，把这块石头填了进去——结果是往反方向落的。</p>

<h2>试验做了什么</h2>

<p>这是一项随机、双盲、安慰剂对照的 <strong>三期</strong>临床试验，在挪威 <strong>11 家中心</strong>开展。入组条件相当严格，瞄准的是被普遍认为最可能获益的人群：年龄 ≥35 岁、确诊不足 2 年的<strong>早期</strong>帕金森病患者、Hoehn-Yahr 分期 &lt;3、多巴胺转运体（DAT）显像确认存在黑质纹状体多巴胺能神经末梢缺失、且入组前多巴胺能治疗方案已稳定。</p>

<ul>
<li><strong>筛选与入组</strong>：537 人筛查 → <strong>410 人随机</strong>（2020-05-06 至 2024-06-20）→ <strong>393 人纳入主要分析</strong>；末次随访完成于 2025-06-19。</li>
<li><strong>基线</strong>：平均年龄 <strong>65.6（SD 9.4）</strong>岁，133 人（<strong>34%</strong>）为女性。</li>
<li><strong>干预</strong>：口服烟酰胺核糖苷（NR）<strong>500 mg、每日两次</strong>（n=206）vs 外观相同的安慰剂（n=204），持续 <strong>52 周</strong>。这一剂量足以把全血 NAD⁺ 显著提升——此前独立的头对头 RCT 已确认这一生物学效应。</li>
<li><strong>主要终点</strong>：第 52 周 MDS-UPDRS 第 I–III 部分总分相对基线的变化（量表范围 0–236，分数越高病情越重），采用重复测量混合模型分析。</li>
<li><strong>5 项预设关键次要终点</strong>：MDS-UPDRS 的第 I、II、III 部分各自变化、DAT SPECT 脑影像、以及非运动症状量表（NMSS，范围 0–360）。</li>
</ul>

<h2>结果：主要终点倒向安慰剂一侧</h2>

<p>第 52 周时，MDS-UPDRS 总分在 NR 组<strong>上升 2.45 点</strong>（95% CI 0.80–4.10），而在安慰剂组<strong>下降 0.27 点</strong>（95% CI −1.95–1.40）；校正后的组间均差为 <strong>2.72 点（95% CI 0.47–4.98；P = .02）</strong>——<strong>有利于安慰剂</strong>。</p>

<p>5 项关键次要终点中，4 项无显著差异，唯一有差异的那一项同样是负向：<strong>非运动症状负担在 NR 组加重更多</strong>（NMSS 校正均差 <strong>4.22 点</strong>，95% CI 1.07–7.37；P = .009）。这意味着 NR 组在两条独立的临床评分维度上都留下了比安慰剂更差的读数。</p>

<p>安全性倒是 NR 组更好：严重不良事件发生率 <strong>NR 组 17/205（8.3%）vs 安慰剂组 29/205（14.1%）</strong>。所以这不是一个「副作用迫使停药」的故事，而是<strong>在安全耐受的前提下，它没有疗效，且读数比安慰剂更差</strong>。</p>

<h2>怎么正确地读这个「恶化」</h2>

<p>论文里预设的「临床重要恶化」阈值是 <strong>5.2 点</strong>（对应的改善阈值为 6.7 点）。NR 组高出的 2.72 点<strong>低于这个门槛</strong>。因此严格的表述是：<strong>NR 没有改善病情，且方向明确不利于 NR；但不能断言它在临床上造成了「显著恶化」。</strong></p>

<p>作者的结论同样克制而明确：<em>「在早期帕金森病患者中，烟酰胺核糖苷治疗 52 周未改善临床结局，且与比安慰剂更差的临床结局相关。这些发现不支持将烟酰胺核糖苷作为帕金森病的疾病修饰治疗。」</em></p>

<h2>一个值得特意指出的背景：这项阴性试验出自谁手</h2>

<p>这一点在讨论该研究时经常被略过，但它决定了这条证据的分量。通讯作者 <strong>Charalampos Tzoulis</strong> 与共同作者 <strong>Christian Dölle</strong> 在利益冲突声明中披露：他们持有「烟酰胺核糖苷用于治疗帕金森病」的<strong>多项国际专利（欧洲 EP4284387A1 已授权）</strong>，且这些专利<strong>均已授权给 Niagen Bioscience</strong>——这是一家以 NR 为核心产品的公司。同一团队此前正是 NR 治疗帕金森病最有说服力的早期证据（NADPARK 一期）的产出方。</p>

<p>做出这个试验的人，有充分的动机希望它成功。在这种结构下仍然读出阴性结果，反而使这条证据比一个中立团队做出来的阴性结果<strong>更难反驳</strong>。</p>

<h2>放进本站已有的 NAD⁺ 证据链里看</h2>

<p>把这条结果和站内已报道的另外两条放在一起，NAD⁺ 前体的图景其实已经相当清楚：</p>

<ul>
<li><strong>生物学效应是真实的</strong>：NR 与 NMN 的头对头 RCT 确认两者都能使全血 NAD⁺ 水平约翻倍（见延伸阅读）。NOPARK 没有推翻这一点，它用的是足以产生该生物学效应的剂量。</li>
<li><strong>但生物学效应不等于临床获益</strong>：这正是本站此前反复强调的边界。NOPARK 把它从一句提醒变成了一个 393 人规模的实测答案。</li>
<li><strong>「NAD⁺ 翻倍」这个终点本身的价值被削弱</strong>：当一个标志物变化明确发生、而同一批人的两条临床评分都朝坏的方向走时，把该标志物作为替代终点的合理性就需要重新论证。</li>
</ul>

<h2>局限与开放问题</h2>

<ul>
<li><strong>人群外推有限</strong>：仅早期 PD、DAT 显像确认多巴胺能缺失、且以挪威人群为主（NHANES 式多样性不足）。不能外推到中晚期 PD，也不能外推到健康老年人的「保健性」使用。</li>
<li><strong>52 周是否足够</strong>：疾病修饰试验的时长永远是争议点；52 周对 PD 而言已属长程，但支持者仍可争辩需要更久。</li>
<li><strong>剂量与组织穿透</strong>：口服 NR 在中枢神经系统的实际暴露量未经本研究直接测定。</li>
<li><strong>一个方向性的张力</strong>：同期 <em>Cell Reports</em>（2026-09-22）报道 mutator 早衰小鼠长期 NR 补充在心脏有益、却损伤造血与红细胞成熟。NAD⁺ 通路可能存在<strong>组织特异的双向效应</strong>，这使「全身性提升 NAD⁺」这一策略本身的合理性成为一个开放问题，而非既定前提。</li>
</ul>

<p>本站立场一贯是「负面结果的情报价值高于正面结果」。NOPARK 是截至目前为止，把 NAD⁺ 前体从「机制上说得通」推到「在人类疾病终点上被检验过并失败」的那一步。这不意味着 NAD⁺ 生物学不重要，而是意味着它的<strong>临床主张必须回到新的起点，重新设计终点与人群</strong>。</p>

<p class="note">本文依据 <em>JAMA</em> 在线预发表版本的官方摘要撰写；若后续正式刊出版本存在数据修订，以正式版为准。</p>""",
    related=[("NAD-Precursor-Head-to-Head-RCT-NR-NMN-2026.html",
              "NR 与 NMN 头对头：两者都能把全血 NAD⁺ 翻倍，但「标志物翻倍」不等于「人变年轻」"),
             ("NAD-Precursor-Systematic-Review-Meta-Analysis-2026.html",
              "NAD⁺ 前体系统评价：15 项 RCT 的代谢指标改善，与「延寿」证据之间的距离"),
             ("LRRK2-EV-cGAS-STING-Parkinson-Accelerated-Aging-Cell-Reports-2026.html",
              "LRRK2 与细胞外囊泡：帕金森病中 cGAS-STING 通路与加速衰老的机制")]
)

A["Cross-Weekly-Clinical-Literature-2026-10-18.html"] = dict(
    topic="神经退行", ev="A", tag="交叉周报",
    title="交叉周报 2026-10-18：NAD⁺ 三期倒向安慰剂，而登记表减 96 项里混着「口径」与「真相」",
    crumb="临床×文献交叉周报 2026-10-18",
    desc="本期以 NAD⁺ 方向迄今最大的三期为轴，串起四条在同一周出现的反向证据：NOPARK 主要终点劣于安慰剂、表观遗传时钟作为试验终点的可靠性被三条独立证据质疑、NR 在增殖组织中伤害性为先、以及 ER-100 首批人体数据读的是功能终点而非标志物。登记侧同时发生口径重建：活跃试验从 558 降至 462 项。",
    source=('<a href="https://clinicaltrials.gov/" target="_blank" rel="noopener noreferrer">ClinicalTrials.gov</a>'
            '（活跃招募快照 2026-10-01，7 方向 462 / 558 项双口径）× 近 6 周同行评议文献'
            '（JAMA / Nature Metabolism / Nature Aging / EMBO Journal / Cell Reports / GeroScience）'
            ' · 本文为《临床×文献交叉追踪周报 2026-10-18》的站点版，原始报告见项目知识库'),
    body="""<p>这是「临床×文献交叉周报」的第二期。方法仍是那一条硬规矩：以 ClinicalTrials.gov 登记库的 7 个方向为骨架，逐方向对照最近几周的实验室发现与临床读出，给每一对「临床在验证的机制 ↔ 实验室最新证据」打三类标签——<strong>【进展】</strong>同向推进、<strong>【争议】</strong>证据打架、<strong>【新靶点】</strong>实验室有、临床还没有。</p>

<p>本期与创刊号的气质不同：创刊号的主色调是「突破」，这一期的主色调是<strong>「证伪」</strong>。四条重要读数，三条是负向的，而它们指向同一个方法的自我拷问：我们长期用来判断「有没有效果」的那些替代终点，到底还站得住吗。</p>

<h2>头条一：NOPARK 把「NAD⁺ 提升 → 临床获益」这条链当场拆开</h2>

<p>挪威 11 中心、410 人随机、393 人纳入主要分析的三期 RCT 发表于 <em>JAMA</em>（2026-10-08）：早期帕金森病患者口服 NR 500 mg 每日两次、共 52 周，MDS-UPDRS 总分校正均差 <strong>2.72 点（95% CI 0.47–4.98；P = .02），有利于安慰剂</strong>；非运动症状负担同样在 NR 组更重（NMSS 差 4.22 点，P = .009）。站内已就此文单独立传（见延伸阅读），本栏目要强调的是它在<b>方法层</b>的含义。</p>

<p>NR 组全血 NAD⁺ 被提升这件事，从未被质疑——同期文献正是用它来说明生物学目标「明确达成」。而恰恰是这批人，在两条独立的临床评分上读数更差。当一个替代终点达成、而临床终点背离时，被证伪的不是这个分子，<strong>是这个替代终点本身</strong>。</p>

<p>更值得注意的是执行者：该研究的通讯团队持有多项「NR 治疗帕金森病」国际专利并已授权给 NR 生产商 Niagen Bioscience。做这个试验的人有充分动机希望它成功，结果仍然是阴性的。</p>

<h2>头条二：表观遗传时钟的可靠性，本周被三条独立证据同时质疑</h2>

<p>把「甲基化时钟下降」当作返老还童的证据，本周变得更难辩护：</p>

<ul>
<li><strong>GeroScience（2026-08）</strong>：COSMOS-Blood 队列 899 人（平均 70 岁）随访 2 年。主成分版时钟高度稳定，年增幅极小（PC Horvath +0.14 年/年、PC GrimAge +0.16 年/年）；<strong>DunedinPACE 无显著纵向变化</strong>；基线值解释了随访值 <strong>71–88%</strong> 的变异。第一年的上升常在次年回落——典型的<strong>回归均值</strong>现象。作者建议试验改用 ANCOVA 分析。</li>
<li><strong>MACRO 试验</strong>：144 例肥胖成人 12 个月饮食干预。基线时 DunedinPACE 与 7 项心血管代谢标志物相关（FDR &lt; 0.05），<strong>干预后关联大部分消失</strong>；变化-变化分析全阴；正式中介分析显示三个时钟<strong>均未中介</strong>减重带来的代谢获益。</li>
<li><strong>衰老富集时钟（<em>EMBO Journal</em>，2026-10-02）</strong>：从 396,333 个甲基化位点中，仅 <strong>9,363 个（2.4%）</strong>与衰老、增龄、死亡风险同向变化。据此训练的 3 个衰老富集成时钟，在 senolytic 处理的培养细胞、老年小鼠肌肉、以及 19 名服药者血液（6 个月）中<strong>均无下降</strong>，其中培养细胞训练的评分在 3 个月时反而<strong>显著上升</strong>。</li>
</ul>

<p>限定要说清：这些数据集多无安慰剂对照，也未证实衰老细胞真被清除。但三条独立证据同时指向「时钟对干预不敏感、且存在回归均值」，已经足以要求任何以时钟为主要终点的试验做出说明。</p>

<h2>头条三：同一周的正面读数，读的是「功能」而不是「标志物」</h2>

<p>唯一的重要正向进展恰好提供了一个对照样本。Life Biosciences 在 AAO 2026 Eyecelerator 公布了 <strong>ER-100（NCT07290244）</strong>的首批人体数据：3 例开角型青光眼，单次玻璃体腔注射 2×10¹¹ vg（AAV2 载体、OSK 三因子、剔除 c-Myc），至 Day 56 无 SAE / DLT / AESI，<strong>2/3 例视野检查显示早期改善</strong>，DSMB 已建议递增至 6×10¹¹ vg。</p>

<p>必须限定：3 例、开放标签、56 天，这是信号不是结论。但它的意义在于<strong>读出的是功能终点（视野）而非分子标志物</strong>——在一个标志物可靠性普遍被质疑的周里，这个选择本身就值得记录。</p>

<h2>登记侧：活跃试验从 558 降到 462，但减的 96 项里混着两件不同的事</h2>

<p>本周期登记的活跃招募试验从 558 项变更为 <strong>462 项</strong>：新增 27、退出 123、状态变更记录 0。清单自己说明了原因——这是<strong>方法学重建版</strong>：长寿方向的相关性判定收紧，仅保留明确长寿/健康衰老/老年衰弱强信号，剔除儿科、牙科、纯美容及泛健康噪声。退出明细里确实能看到这类条目（如牙科树脂修复体 NCT04630587）。</p>

<p>但这里有一个需要指出的<b>分析缺口</b>：123 项退出的备注栏<strong>全部是同一句套话</strong>——「已不在三种活跃状态之内（完成/终止/撤回等）」。于是「真实状态转为已完成」的重要试验（如巴尔的摩纵向衰老研究 BLSA、NCT00233272 这类）与「被清洗规则剔除」的噪声条目，在表里被混成一类，读者无法分辨某个特定试验到底是<strong>完成了</strong>还是<strong>被删了</strong>。这对依赖该清单做尽调核查的使用者来说是一个实质可读性缺陷，已作为质量问题反馈给登记清单刷新任务。</p>

<h2>方法学附言：本栏目长期盯的四类失真，本期复核结果</h2>

<ol>
<li><strong>登记捕获缺口</strong>——<b>仍未修复</b>。本期以 <code>AAV2-OSK</code> 精确检索直接命中 NCT07290244（招募中），而清单的「部分重编程」方向<strong>仍记为 0 项</strong>。这不是「没有试验」，是「检索式抓不到」。修复方案早已写进上游任务的 prompt（OSK / Yamanaka / AAV2 + 申办方白名单），本轮产出未执行。</li>
<li><strong>状态覆盖缺口</strong>——本期已临时补回 8 项 COMPLETED 且有近期更新的试验，含 Fisetin 治轻度 AD（NCT07279714）等。</li>
<li><strong>替代终点失真</strong>——本期出现教科书级的双向案例，且方向相反：D+Q 治 MASH 肝纤维化中，FIB-4 / ELF / ProC3 / 弹性成像<strong>全部阴性</strong>，活检却显示纤维化改善；而 NOPARK 则相反，生物学目标达成而临床终点背离。<strong>两个方向都不可简化为「有效/无效」。</strong></li>
<li><strong>产业活动不在公开登记中</strong>——新发现。按申办方白名单检索，Retro Biosciences / Altos Labs / NewLimit / YouthBio / Turn Bio / Rejuvenate Bio / Shift Bioscience / Clock.bio 在 ClinicalTrials.gov 上<strong>均为 0 项登记</strong>，仅 Life Biosciences 有 9 项。公开登记数会<strong>系统性低估</strong>产业活跃度。</li>
</ol>

<h2>两条本期未能核实、明确标注为「待核实」的信息</h2>

<ul>
<li><strong>PEARL 试验</strong>（雷帕霉素，&gt;200 名健康成人）：多个聚合站报道 DunedinPACE 在 5 mg 组降低约 0.04 单位（p = 0.003）、GrimAge2 约 −1.1 年（p = 0.041）、流感疫苗抗体应答增强 28%。<strong>本轮 PubMed 检索未定位到主要结果论文</strong>，上述数字未获独立来源确认，不作为本站结论。</li>
<li><strong>化学重编程 VC6TF</strong>：仅有媒体转述，原始期刊与 DOI 待核实。</li>
</ul>

<p>最后一句给本期的整体基调：这是罕见的一周，最重要的三条新证据都在说「我们之前判读的那套办法有问题」，而不是「我们找到了新东西」。对一个仍在寻找临床锚点的领域，这未必是坏消息。</p>""",
    related=[("NOPARK-NR-Early-Parkinson-Phase3-JAMA-2026.html",
              "NOPARK 三期揭盲：410 人每日 1000 mg NAD⁺ 前体一年，主要终点显著劣于安慰剂"),
             ("Cross-Weekly-Clinical-Literature-2026-10-12.html",
              "交叉周报创刊号：senolytics 首次逆转人体器官纤维化，而登记库里「部分重编程」仍是 0 项"),
             ("Dasatinib-Quercetin-Senolytic-MASH-Liver-Fibrosis-RCT-2026.html",
              "达沙替尼+槲皮素治疗 MASH 肝纤维化：31 人随机对照试验 47% 纤维化改善")]
)

ga.A = A
if __name__ == "__main__":
    ga.main()
