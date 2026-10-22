#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_articles_preprint_2026-10-22.py —— 内容摄入第 19 批（文献层《预印本速递_2026-10-22》）

来源与判定
────────
事实源：文献层《预印本速递_2026-10-22.md》（file_id dhKUzsPPYJNA，实测 31,347 B，
本地落 .intake/raw/预印本速递_2026-10-22.md）。该期产出侧自述：
bioRxiv 172/171、medRxiv 72/72 翻页覆盖完；主榜 4 · 观察哨 2 · 补遗 3，误报率 81.6%。

本批为**补消化**：2026-10-22 07:30 的摄入巡检未把该期入游标，导致 10-22 当日
站内无新增文章（用户反馈「10-22 的更新在网站上看不到」），由运营侧补跑本批。

成篇范围（沿用 10-19/10-20 批惯例）
────────
· 主榜 4 条全部成篇。
· 观察哨 2 条不成篇：观察哨 1（脑老化 5-mC/5-hmC 框架）摘要无任何定量；
  观察哨 2（MCFT 蛋白周转筛选平台）属资源类，蛋白稳态仅为背景动机。
· 补遗 3 条不成篇：相关性弱（代谢物理理论 / CKD 微量元素 / 肾脏 3D 形态学），
  均无衰老主轴定量。
· 游标 note 记录处置。

纪律
────
· 主榜 1 全文已由上游获取（PDF 48 页已校验），但本站**仍只依据官方摘要**撰写，
  与全站「摘要级」口径一致；主榜 2–4 仅摘要（bioRxiv 403 源站封锁）。
· 证据分级沿用 10-19 批口径：预印本原始研究定 **B**（临床前/人体原始研究），
  预印本属性由 tag 与正文 notice 明示，不用 C 掩盖「这是原始研究」。
· 所有定量仅出自摘要；缺处一律「待补全文」。
· related slug 全部经 news/ 实际存在性校验。
"""
import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATE = "2026-10-22"

REL_CLOCK = [
    ("DunedinPACE-Lifestyle-Intervention-RCT-2026.html",
     "DunedinPACE 能被干预改变吗：生活方式 RCT 的时钟读数"),
    ("Dog-Epigenetic-Clock-LINE1-Science-2026.html",
     "狗的表观遗传时钟与 LINE-1：跨物种的老化测量"),
    ("Longitudinal-Epigenetic-Clock-InCHIANTI-Mortality-2026.html",
     "InCHIANTI 纵向队列：表观遗传时钟与死亡风险"),
]
REL_GRID = [
    ("Implicit-Associative-Memory-Aging-Hippocampus-Perirhinal-2026.html",
     "老年海马–周皮层内隐联想记忆：表征可分，绑定变脆"),
    ("Hippocampus-Memory-Update-Tent5a-Aging-2026.html",
     "Tent5a 与海马记忆更新：老化突触的翻译调控"),
]
REL_MICROGLIA = [
    ("Microglia-Replaced-Peripheral-Blood-Cells-Human-Brain-Aging-2026.html",
     "人老化脑中的小胶质细胞：外周血细胞在替换它们"),
    ("Microglia-Cancer-Mutations-Drive-Alzheimer-Cell-2026.html",
     "小胶质细胞的「癌症式」突变与阿尔茨海默病"),
]
REL_PERFUSION = [
    ("Implicit-Associative-Memory-Aging-Hippocampus-Perirhinal-2026.html",
     "老年海马–周皮层内隐联想记忆：表征可分，绑定变脆"),
    ("MCI-Neuropsychiatric-Symptoms-MRI-Structure-Perfusion-medRxiv-2026.html",
     "MCI 的神经精神症状与脑结构–灌注：MRI 证据"),
]


def notice(ev):
    t = {"A": "A 级（同行评议人体研究）",
         "B": "B 级（原始研究，动物模型或人体观察，未经同行评审的预印本）",
         "C": "C 级（预印本 / 观点评论，非原始研究）"}[ev]
    return (f'<div class="notice-box">\n'
            f'    <p><span class="tier tier-{ev.lower()}">{ev} 级</span>'
            f'<strong>证据分级：{t}</strong></p>\n'
            f'    <p><strong>关于本文的文献来源：</strong>本站依据 <strong>预印本官方摘要原文</strong>'
            f'撰写（来源：《预印本速递》2026-10-22 期，第 19 批摄入）。'
            f'这是一篇<strong>未经同行评审的预印本</strong>，结论可能在正式发表时变更；'
            f'摘要未给出之处已标注「待补全文」，<strong>未做任何数值推算补全</strong>。</p>\n'
            f'</div>')


def main():
    arts = json.load(open(os.path.join(ROOT, "data/articles.json"), encoding="utf-8"))
    used = {a["slug"] for a in arts}
    rel = REL_CLOCK + REL_GRID + REL_MICROGLIA + REL_PERFUSION
    missing = [s for s, _ in rel if not os.path.exists(os.path.join(ROOT, "news", s))]
    if missing:
        sys.exit(f"✗ related slug 在 news/ 下不存在：{missing}")

    sys.argv = ["gen_articles.py", ROOT, "/dev/null", DATE]
    _spec = importlib.util.spec_from_file_location(
        "ga", os.path.join(ROOT, "scripts", "gen_articles.py"))
    ga = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(ga)
    ga.notice = notice

    DOI1 = "10.64898/2026.10.21.26365867"
    DOI2 = "10.64898/2026.10.15.759328"
    DOI3 = "10.64898/2026.10.15.759429"
    DOI4 = "10.64898/2026.10.15.759438"

    def src(doi, journal, en, corr, fullnote="摘要级，全文未获取"):
        return (f'<em>{journal}</em> · 预印本：{en}'
                f' · DOI <a href="https://doi.org/{doi}" target="_blank" '
                f'rel="noopener noreferrer">{doi}</a>'
                f' · {corr}'
                f' · 来源：《预印本速递》2026-10-22 期（{fullnote}）')

    src1 = src(DOI1, "medRxiv（neurology）",
               "Biological age measured by DNA methylation clocks and neurodegenerative "
               "diseases: a systematic review and meta-analysis",
               "通讯 Andrea B. Maier（新加坡国立大学 Yong Loo Lin 医学院）",
               "摘要级；上游已获取全文 PDF（48 页）但本站口径仍以摘要为准")
    src2 = src(DOI2, "bioRxiv（neuroscience）",
               "Temporal instability weakens entorhinal grid-like coding in older adults",
               "通讯 Vladislava Segen（德国神经退行性疾病中心 DZNE）")
    src3 = src(DOI3, "bioRxiv（immunology）",
               "Young bone marrow-derived microglia-like cells improve cognitive function "
               "in the aged brain through BDNF-TrkB signalling",
               "通讯 Ren-Ke Li（多伦多总医院研究所）")
    src4 = src(DOI4, "bioRxiv（neuroscience）",
               "Distinct spatial organization of human hippocampal perfusion and "
               "microvascular pulsatility across age",
               "通讯 Danny JJ Wang（南加州大学）")

    A = {
        "DNAm-Clock-EAA-Dementia-Meta-Analysis-37-Studies-2026.html": dict(
            topic="表观遗传", ev="B", tag="预印本",
            title="37 项研究 4.6 万人的证伪性检验：五种表观遗传时钟里只有 GrimAge 预测痴呆",
            crumb="DNAm 时钟与神经退行病的 meta 分析",
            desc="n=46,365 的 meta 分析显示，GrimAge 年龄加速每 +1 SD，痴呆风险 HR 1.11；"
                 "Horvath1 / Hannum / PhenoAge / DunedinPACE 均不显著——「时钟即生物标志物」"
                 "的默认假设需要重新审视。",
            source=src1,
            body="""<p><strong>一句话结论：</strong>37 项观察性研究（<strong>n=46,365</strong>）的 meta 分析发现，五种主流 DNA 甲基化时钟中，<strong>只有 GrimAge 的表观年龄加速（EAA）能稳定预测全因痴呆风险</strong>——EAA 每升高 1 个 SD，HR = <strong>1.11（95% CI 1.02–1.20；I²=0%；p=0.018）</strong>；Horvath1、Hannum、PhenoAge、DunedinPACE <strong>均无显著关联</strong>。</p>

<p class="notice-box"><strong>⚠️ 本文为预印本，未经同行评审；本站依据官方摘要撰写，结论可能在正式发表时变更。</strong></p>

<h2>这项研究想回答什么</h2>
<p>「表观遗传时钟能不能当疾病生物标志物」是当前抗衰领域绕不开的根基问题：大量干预试验把 DNAm 年龄当终点，也有大量观察研究把 EAA 当风险指标。如果时钟读数与临床结局根本不挂钩，这条链路就悬空了。本文用<strong>证伪性设计</strong>正面检验：六库检索（2011-01-01 至 2026-04-15），从 42,023 条记录筛出 37 项观察研究 + 7 项孟德尔随机化研究，按时钟逐个做纵向 meta 分析（层级效应模型 + Knapp-Hartung 校正）。</p>

<h2>核心发现</h2>
<ul>
<li><strong>GrimAge EAA +1 SD → 痴呆 HR 1.11（1.02–1.20）</strong>，异质性 I²=0%，是全表最稳的一条。</li>
<li><strong>Horvath1 / Hannum / PhenoAge / DunedinPACE 与痴呆均不显著</strong>——包括被广泛使用的 DunedinPACE。</li>
<li>PD / MS / ALS 的证据在「时钟代际 × 研究设计」间高度异质，只能定性引用；孟德尔随机化仅提供有限因果性证据。</li>
</ul>

<h2>怎么读这份阴性结果</h2>
<ol>
<li><strong>GrimAge 为什么独存？</strong>最合理的解释是它<strong>整合了吸烟与血浆蛋白等临床表型</strong>——预测力可能来自这些成分而非甲基化年龄信号本身。这对「时钟测的是老化速度还是风险因素暴露」之争是重要旁证。</li>
<li><strong>对干预试验的含义：</strong>若试验终点用 Horvath1 / PhenoAge，即使读数改善，其对痴呆风险的临床解释力也要打问号。</li>
<li><strong>局限（摘要明示 + 本站补充）：</strong>发表偏倚与时钟版本混杂风险；偏倚检验（Egger / funnel）结果待补全文；阴性结果是效应量小还是把握度不足，摘要未给把握度分析。</li>
</ol>

<h2>为什么值得关注</h2>
<p>这是目前对该问题<strong>最系统的一次证伪性评估</strong>，且通讯单位是专门的健康长寿研究机构。它不否定表观遗传时钟的研究价值，但把「读数改善 = 抗衰有效」的推理链明确敲了一记：先回答「你用的时钟与哪个临床结局有稳定关联」，再谈终点替换。</p>""",
            related=REL_CLOCK,
        ),
        "Entorhinal-Grid-Coding-Temporal-Instability-Aging-bioRxiv-2026.html": dict(
            topic="神经退行", ev="B", tag="预印本",
            title="老年人内嗅皮层的「网格信号」变弱，是表征不稳了，不是没了",
            crumb="老化内嗅网格编码的稳定性解释",
            desc="85 名老年人的 VR+fMRI 显示：内嗅六向信号变弱对应网格表征的跨 run 不稳定，"
                 "而非表征缺失；左 pmEC 稳定性还能预测物体位置记忆——年龄本身反而解释力不足。",
            source=src2,
            body="""<p><strong>一句话结论：</strong>在 <strong>85 名老年人</strong>的虚拟现实导航 + fMRI 实验中，内嗅皮层「六向信号」随老化变弱，反映的是<strong>网格表征在时间上不稳定</strong>（跨 run 的方向模式不可复现），而<strong>不是表征缺失</strong>；左侧后内侧内嗅皮层（pmEC）的稳定性越高，物体-位置记忆越好。</p>

<p class="notice-box"><strong>⚠️ 本文为预印本，未经同行评审；本站依据官方摘要撰写（源站封锁，全文未获取），结论可能在正式发表时变更。</strong></p>

<h2>这项研究想回答什么</h2>
<p>网格细胞负责空间导航的「坐标系」，人类 fMRI 里对应内嗅皮层的六向（60° 周期）信号。既往发现老年人该信号变弱，但「变弱」有两种截然不同的含义：<strong>表征退场</strong>（没法救）或<strong>表征不稳</strong>(可以练)。本文在老年人内部直接检验哪种解释成立。</p>

<h2>核心发现</h2>
<ul>
<li><strong>六向朝向稳定性</strong>（方向特异性活动模式的跨 run 可复现性）与 pmEC 六向信号强度相关。</li>
<li><strong>左侧 pmEC：稳定性越高，物体-位置记忆越好</strong>。</li>
<li><strong>年龄本身与局部结构指标均不能解释</strong>这些个体差异——「表征稳定性」比「实际年龄」更有解释力。</li>
<li>压后皮层的绝对朝向稳定性与左 pmEC 相关，中介分析支持其经 pmEC 稳定性间接影响六向信号。</li>
</ul>

<h2>证据边界</h2>
<ol>
<li><strong>纯老年人队列（N=85）</strong>，无青年对照，摘要未给年龄范围与方差；「老年人内部差异」推到「老化效应」需谨慎。</li>
<li>记忆关联为<strong>相关/中介设计</strong>，无因果干预；六向信号作为网格细胞的 fMRI 替代指标本身仍有争议。</li>
<li>具体效应量（相关系数、中介效应值、p 值）摘要未给，<strong>待补全文</strong>。</li>
</ol>

<h2>为什么值得关注</h2>
<p>它把「老化导致神经表征退化」精细化成「<strong>稳定性下降，而非信号消失</strong>」——如果瓶颈是不稳定而非缺失，稳定性就是潜在可训练的靶点（导航训练、睡眠、神经调控都有入手处）。对「老化认知衰退是否可逆」这条叙事，这是一个方向性的证据点。</p>""",
            related=REL_GRID,
        ),
        "Young-BM-Microglia-BDNF-TrkB-Aged-Cognition-bioRxiv-2026.html": dict(
            topic="免疫与炎症", ev="B", tag="预印本",
            title="年轻骨髓小胶质细胞改善老年脑认知，靠的是早期归巢期的 BDNF-TrkB，不需要永久嵌合",
            crumb="异体年轻细胞的「rejuvenation」机制定位",
            desc="可诱导清除体系显示：年轻供体骨髓来源小胶质样细胞的认知获益在移植后 1 个月"
                 "起效、依赖 BDNF-TrkB 通路，且清除后仍维持——不必永久嵌合，TrkB 激动剂或可模拟。",
            source=src3,
            body="""<p><strong>一句话结论：</strong>用可诱导清除体系证明：年轻供体骨髓来源的小胶质样细胞改善老年脑认知，<strong>不需要永久嵌合</strong>——获益在早期脑内归巢期经 <strong>BDNF-TrkB</strong> 通路起效，之后即使把细胞清掉，改善仍然维持。</p>

<p class="notice-box"><strong>⚠️ 本文为预印本，未经同行评审；本站依据官方摘要撰写（源站封锁，全文未获取），结论可能在正式发表时变更。</strong></p>

<h2>这项研究想回答什么</h2>
<p>「年轻细胞让老年组织回春」的证据在增多，但始终悬着一个问题：<strong>获益需要异体细胞永久驻留吗？</strong>若需要，细胞移植的免疫相容性与安全性就是绕不开的坎；若不需要，机制干预（药物模拟）就有了入口。本文用「可清除」设计直接切这个口。</p>

<h2>他们怎么做的</h2>
<ul>
<li>构建 <strong>CX3CR1⁺ 巨噬细胞可被白喉毒素选择性清除</strong>的小鼠体系；年轻供体骨髓移植入老年野生型受体后，在 <strong>1 个月或 3 个月</strong>两个时点做可控清除。</li>
<li><strong>移植后 3 个月清除</strong>：脑内小胶质生态位已无法被外周或中枢巨噬细胞补充；全身单核细胞招募减少、中性粒细胞涌入脑内；海马行为未受影响（该时点海马内本就无这些细胞）。</li>
<li><strong>移植后 1 个月清除</strong>：BM 来源小胶质样细胞在海马内丰富存在，此时清除会<strong>严重损害认知改善</strong>，并<strong>抑制海马神经元树突棘分支形成</strong>。</li>
<li>药理学阻断 BDNF 受体 <strong>TrkB</strong>，产生与清除细胞相同的损害效应。</li>
</ul>

<h2>核心发现与定位</h2>
<p>因果链指向：<strong>早期归巢期的 BDNF-TrkB 信号是获益的充要窗口，之后细胞在不在都无所谓</strong>。这与异体共生、部分重编程两条主线在「获益是否需要持久嵌合」上给出了同一方向的答案。</p>

<h2>证据边界</h2>
<ol>
<li>摘要<strong>未给各组动物数、行为学效应量与统计值</strong>，1 个月 vs 3 个月的改善幅度无法量化，<strong>待补全文</strong>。</li>
<li>BDNF-TrkB 的因果链靠「阻断剂表型复制」单侧支撑，缺 TrkB 条件敲除或 BDNF 补充的双向验证。</li>
<li>骨髓移植是强干预；向人的转化涉及安全性与免疫相容性，摘要未涉及。</li>
</ol>

<h2>为什么值得关注</h2>
<p>这是「年轻细胞 rejuvenation」从现象走向机制的一步，而且把靶点落到了<strong>可药理操作的节点</strong>：既然获益经 TrkB 且不需持久嵌合，<strong>TrkB 激动剂或小分子模拟可能复现部分获益</strong>——这条路线的成本与风险都比细胞移植低一个量级。</p>""",
            related=REL_MICROGLIA,
        ),
        "Hippocampal-Perfusion-mvPI-Spatial-Aging-bioRxiv-2026.html": dict(
            topic="神经退行", ev="B", tag="预印本",
            title="海马的「供水」与「搏动」是两条独立的老化轴线：7T MRI 的空间图谱",
            crumb="灌注与微血管搏动性的二分框架",
            desc="35 名青年与老年人的 7T MRI 显示，海马灌注与微血管搏动指数（mvPI）空间组织"
                 "不同、各有年龄差异；青年组中前者对应 PV 中间神经元密度，后者对应 theta 频段。",
            source=src4,
            body="""<p><strong>一句话结论：</strong><strong>35 名青年与老年成人</strong>的 7T MRI 显示，海马<strong>灌注</strong>（代谢供给）与<strong>微血管容积搏动指数 mvPI</strong>（机械应力）是<strong>两个维度不同、各自有年龄差异</strong>的空间组织——不能当一回事读。</p>

<p class="notice-box"><strong>⚠️ 本文为预印本，未经同行评审；本站依据官方摘要撰写（源站封锁，全文未获取），结论可能在正式发表时变更。</strong></p>

<h2>这项研究想回答什么</h2>
<p>老化脑的血管侧变化常被笼统称为「脑血流下降」。但血管系统给神经组织的影响至少有两条路：<strong>供给</strong>（灌注）与<strong>机械</strong>（心跳驱动的微血管搏动，其对周围组织的应力近年才可测量）。二者在老化中是否同一回事？本文在海马皮层展开图上把两者分开画。</p>

<h2>核心发现</h2>
<ul>
<li>灌注与 mvPI 呈<strong>不同的空间组织</strong>，且<strong>均存在年龄相关差异</strong>。</li>
<li>青年组：灌注优先对应 <strong>PV（parvalbumin）中间神经元密度与 beta/gamma 频段</strong>分布；mvPI 对应 <strong>theta 频段</strong>分布。</li>
<li><strong>青年组检出的部分关联在老年组图谱中未检出</strong>（阴性结果，把握度未报告）。</li>
<li>频谱模拟提示 mvPI–theta 关系的一个可能解释是<strong>心跳相关相位重置</strong>；空间转录组显示 <strong>PIEZO2</strong> 在血管周围富集，是「血管搏动→神经元活动」机械转导的候选介导因子（转录组层面，未做功能验证）。</li>
</ul>

<h2>证据边界</h2>
<ol>
<li><strong>N=35 且青年+老年混合分组</strong>，摘要未给各组人数与年龄均值；横断面无法区分老化与队列效应。</li>
<li>「老年组未检出」是阴性结果，无把握度分析，可能只是样本量不足。</li>
<li>PIEZO2 仅为候选，无功能验证；影像效应量与 p 值未给，<strong>待补全文</strong>。</li>
</ol>

<h2>为什么值得关注</h2>
<p>它给出了一个可操作的二分框架：<strong>灌注与搏动性是老化脑血管的两条独立轴线</strong>——干预与测量的对象从此应该分开。PIEZO2 的发现把「机械转导参与老化脑神经血管耦合」的假说首次推到人类数据上，是影像–机制结合里相对稀缺的一块。</p>""",
            related=REL_PERFUSION,
        ),
    }

    for slug in A:
        if slug in used:
            sys.exit(f"✗ slug 已存在，拒绝覆盖：{slug}")
    print(f"本批新写 {len(A)} 篇（观察哨 2 + 补遗 3 不成篇，理由见文件头）")
    ga.A = A
    ga.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
