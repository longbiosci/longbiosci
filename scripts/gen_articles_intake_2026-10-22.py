#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_articles_intake_2026-10-22.py —— 内容摄入第 10 轮（2026-10-22 双产出）

事实源（均经 tdrive.file_download + stat -c%s 实测字节数，非 dir_list 缓存值）
────────────────────────────────────────────────────────────────────────
· 文献层《预印本速递_2026-10-22》   file_id dhKUzsPPYJNA  实测 31,347 B
  → .intake/raw/preprint-2026-10-22.md
  自检：入榜 9 条，带 DOI 9 条（100%）；主榜 4 条中 PDF 下载成功 1 条、
  bioRxiv 源站 403（Cloudflare IP 级封锁）3 条。
· 元层《LongBiosci_待写补丁_2026-10-21.tar》file_id dbhxURufXOPt 实测 215,304 B
  → .intake/raw/LongBiosci_待写补丁_2026-10-21.tar.gz（3 个 git patch，**非内容产出**，
    属工程/SEO 修复补丁，按应用层处置，不进入本批写稿）

查重与硬核验（四路查重 + 高特异关键词站内原文硬核验）
────────────────────────────────────────────────────
harvest.py 从速递抽出 9 条候选，判定 **9 条 confidence=none**。
按硬规则 3（confidence=none ≠ 漏收），改用 DOI 尾号 + 英文专名在 news/ 原文逐条硬核验：

| 条目 | 硬核验词 | news/ 命中 | 结论 |
|---|---|---|---|
| 主榜1 DNAm 时钟 meta | `26365867` / `DNA methylation clocks` | 0 / 1 篇（该 1 篇 DOI 10.18632/aging.206377，社会健康不平等，非同一研究） | 真漏收 → 成篇 |
| 主榜2 内嗅网格编码 | `759328` / `entorhinal` / `grid-like coding` | 0 / 0 / 0 | 真漏收 → 成篇（与主榜4 合并） |
| 主榜3 年轻骨髓小胶质样细胞 | `759429` / `BDNF-TrkB` / `microglia-like` | 0 / 0 / 0 | 真漏收 → 成篇 |
| 主榜4 海马灌注与 mvPI | `759438` / `hippocampal perfusion` / `microvascular pulsatility` | 0 / 0 / 0 | 真漏收 → 成篇（与主榜2 合并） |
| 观察哨1 脑老化 5mC/5hmC | `757659` / `hydroxymethylation` | 0 / 0 | 真漏收，但**摘要零定量** → 不成篇（入档） |
| 观察哨2 蛋白周转筛选 | `723176` / `protein turnover` | 0 / 0 | 真漏收，属方法学平台 → 按上游建议不成篇（入档） |
| 补遗1 代谢物理理论 | `749078` / `Metabolic Holon` | 0 / 0 | 真漏收，主题非衰老 → 不成篇（入档） |
| 补遗2 微量元素 CKD | `26365915` / `Trace element supplementation` | 0 / 0 | 真漏收，主题非衰老 → 不成篇（入档） |
| 补遗3 肾脏 3D 图谱 | `26365903` / `Medullary Thickness` | 0 / 0 | 真漏收，年龄仅作协变量 → 不成篇（入档） |

⚠️ 泛词提醒：`DNA methylation clocks` 命中 1 篇只能证明「同主题文章多」，
**不能证明本条已收录**；真正判据是 DOI 尾号，9 条全部 0 命中。

纪律
────
· 只写产出给出的事实；预印本侧**摘要未给出的定量一律标「待补全文」**，数值不臆测、不从同类文献套用。
· 主榜1 上游已在本机下载 PDF（2,173,707 B / 48 页），但**本站未获取该全文**，
  本稿定量仍全部取自 medRxiv 官方摘要，不因「上游有 PDF」而补写任何摘要外的数字。
· 证据分级沿用全站 notice-box 口径：A 同行评议人体研究 / B 临床前·未评审人体证据 /
  C 预印本观点·行业披露。本批 3 篇**均为预印本且全文未获取**（bioRxiv 源站 403），
  故一律定 **B**，并在 notice 正文中写明「未评 A 级」的具体理由（未经同行评审 + 仅摘要）。
· 内部链接 slug 全部取自 data/articles.json，且经 news/ 目录实际存在性校验（脚本内硬校验）。
"""
import html
import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATE = "2026-10-22"

# ── 内部链接：均经 news/ 目录实际存在性校验（2026-10-22 实查）──
REL_CLOCK = [
    ("DunedinPACE-Mortality-Biomarker.html",
     "DunedinPACE：14种衰老生物标志物中预测死亡最强"),
    ("DunedinPACE-Lifestyle-Intervention-RCT-2026.html",
     "随机对照试验证实：生活方式干预显著延缓DunedinPACE表观遗传衰老速度"),
    ("DNA-Methylation-Clock-Socioeconomic-Mortality-2026.html",
     "DNA甲基化时钟揭示社会健康不平等的生物学机制"),
    ("COSMOS-Multivitamin-Epigenetic-Aging-Clocks-Nature-Medicine-2026.html",
     "每日一粒复合维生素，让表观遗传年龄走得慢一点：COSMOS 试验 958 人两年结果"),
]
REL_BRAIN = [
    ("Brain-Metabolic-Connectivity-Method-Comparison-2026.html",
     "脑代谢连接度方法比较：拓扑、认知、年龄、结构与遗传"),
    ("AQP4-TGN073-Glymphatic-Tau-Pathology-MolNeurodegener-2026.html",
     "小分子化合物 TGN-073 激活 AQP4 增强脑类淋巴功能，减轻 tau 病理与神经退行性变"),
    ("Blood-Metabolome-Brain-Health-Midlife-Nature-Aging-2026.html",
     "血液代谢组学揭示中年大脑健康代谢轨迹：生活方式与药物如何影响阿尔茨海默病风险"),
    ("Deep-Learning-Explainability-Neurocognitive-Aging-2026.html",
     "用深度学习可解释性方法探索健康神经认知老化"),
]
REL_MG = [
    ("Young-Plasma-Exchange-Cognitive-Impairment-Pilot-2026.html",
     "年轻供体血浆置换：认知障碍患者的间质液回春 pilot 研究"),
    ("Microglia-Replaced-Peripheral-Blood-Cells-Human-Brain-Aging-2026.html",
     "颠覆认知：外周血细胞可替代大脑免疫细胞"),
    ("TIMP2-Microglia-Aging-Brain-Nature-Communications-2026.html",
     "TIMP2 蛋白疗法调节老化大脑中小胶质细胞功能"),
    ("Stem-Cell-Rejuvenation-Age-Related-Degeneration-2026.html",
     "干细胞疗法抗衰老最新进展：预适应与衰老清除的协同路径"),
]

PREAMBLE_PREPRINT = (
    '<p class="notice-box"><strong>⚠️ 本文为预印本，未经同行评审；'
    '本次仅依据预印本平台官方 API 返回的摘要原文撰写，全文未获取'
    '（bioRxiv 源站对本环境返回 HTTP 403，Cloudflare IP 级封锁），'
    '结论可能在正式发表时变更。摘要未给出的定量一律标注「待补全文」，'
    '未做任何数值推算补全。</strong></p>')


def notice(ev):
    t = {"A": "A 级（同行评议人体研究）",
         "B": "B 级（未评审 / 临床前证据：预印本原始研究或未获取全文）",
         "C": "C 级（预印本观点 / 行业披露，非原始研究）"}[ev]
    b = ("<p><strong>本文为预印本，未经同行评审，且本站未获取全文（源站封锁），"
         "仅依据官方摘要撰写，故未评为 A 级。</strong>"
         "摘要中未给出的样本量、效应量与统计值，本站<strong>一律标注「待补全文」，"
         "不做推算、不从同类文献套用</strong>。"
         "预印本结论可能在正式发表时变更，引用前请以正式版为准。</p>")
    src = ("<p><strong>关于本文的文献来源：</strong>本站依据预印本平台官方 API 返回的"
           "<strong>摘要原文</strong>撰写（来源：IMA 知识库《预印本速递》2026-10-22 期，"
           "摘要级，全文未获取）。</p>")
    return (f'<div class="notice-box">\n'
            f'    <p><span class="tier tier-{ev.lower()}">{ev} 级</span>'
            f'<strong>证据分级：{t}</strong></p>\n'
            f'    {b}\n'
            f'    {src}\n'
            f'</div>')


def main():
    arts = json.load(open(os.path.join(ROOT, "data/articles.json"), encoding="utf-8"))
    used = {a["slug"] for a in arts}
    all_rel = REL_CLOCK + REL_BRAIN + REL_MG
    missing = [s for s, _ in all_rel if not os.path.exists(os.path.join(ROOT, "news", s))]
    if missing:
        sys.exit(f"✗ related slug 在 news/ 下不存在：{missing}\n"
                 f"  内部链接必须 ls news/ 实际复制，不能凭记忆写。")

    sys.argv = ["gen_articles.py", ROOT, "/dev/null", DATE]
    _spec = importlib.util.spec_from_file_location(
        "ga", os.path.join(ROOT, "scripts", "gen_articles.py"))
    ga = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(ga)
    ga.notice = notice

    DOI_META = "10.64898/2026.10.21.26365867"
    DOI_GRID = "10.64898/2026.10.15.759328"
    DOI_PERF = "10.64898/2026.10.15.759438"
    DOI_MG = "10.64898/2026.10.15.759429"

    src_meta = (
        f'<em>medRxiv</em>（neurology）· 预印本 · 2026-10-21：'
        f'Biological age measured by DNA methylation clocks and neurodegenerative diseases: '
        f'A systematic review and meta-analysis'
        f' · DOI <a href="https://doi.org/{DOI_META}" target="_blank" '
        f'rel="noopener noreferrer">{DOI_META}</a>'
        f' · 第一作者 Z. Kua；通讯 Andrea B. Maier'
        f'（新加坡国立大学 Yong Loo Lin 医学院 · NUS 健康长寿研究院）'
        f' · 来源：IMA 知识库《预印本速递》2026-10-22 期（摘要级，全文未获取）')

    src_brain = (
        f'<em>bioRxiv</em>（neuroscience）· 预印本 · 2026-10-21：'
        f'Temporal instability weakens entorhinal grid-like coding in older adults'
        f' · DOI <a href="https://doi.org/{DOI_GRID}" target="_blank" '
        f'rel="noopener noreferrer">{DOI_GRID}</a>'
        f'（通讯 Vladislava Segen，德国神经退行性疾病中心 DZNE）'
        f' ＋ <em>bioRxiv</em>（neuroscience）· 2026-10-21：'
        f'Distinct spatial organization of human hippocampal perfusion and microvascular '
        f'pulsatility across age'
        f' · DOI <a href="https://doi.org/{DOI_PERF}" target="_blank" '
        f'rel="noopener noreferrer">{DOI_PERF}</a>'
        f'（通讯 Danny JJ Wang，南加州大学）'
        f' · 来源：IMA 知识库《预印本速递》2026-10-22 期（摘要级，全文未获取）')

    src_mg = (
        f'<em>bioRxiv</em>（immunology）· 预印本 · 2026-10-21：'
        f'Young bone marrow-derived microglia-like cells improve cognitive function in the '
        f'aged brain through BDNF-TrkB signalling'
        f' · DOI <a href="https://doi.org/{DOI_MG}" target="_blank" '
        f'rel="noopener noreferrer">{DOI_MG}</a>'
        f' · 作者 L. Wlodarek, R-K. Li；通讯 Ren-Ke Li'
        f'（多伦多总医院研究所 Toronto General Research Institute）'
        f' · 来源：IMA 知识库《预印本速递》2026-10-22 期（摘要级，全文未获取）')

    A = {
        "DNAm-Clocks-Dementia-Risk-Meta-Analysis-2026.html": dict(
            topic="表观遗传", ev="B", tag="预印本",
            title="46,365 人的系统性证伪：五种主流甲基化时钟里，只有 GrimAge 能预测痴呆",
            crumb="只有 GrimAge 预测痴呆：46,365 人的 meta 分析",
            desc="37 项观察性研究（n=46,365）的 meta 分析：GrimAge 年龄加速每升 1 个 SD，"
                 "全因痴呆风险 HR=1.11（95% CI 1.02–1.20，p=0.018）；Horvath1、Hannum、PhenoAge、"
                 "DunedinPACE 与痴呆风险均无显著关联。",
            source=src_meta,
            body=f"""<p><strong>一句话结论：</strong>检索 6 个数据库（2011-01-01 至 2026-04-15）、从 <strong>42,023 条记录</strong>中筛出 <strong>37 项观察性研究（n=46,365）</strong>与 <strong>7 项孟德尔随机化研究</strong>的系统综述与 meta 分析显示：在五种主流 DNA 甲基化（DNAm）时钟中，<strong>只有 GrimAge 的表观年龄加速（EAA）能稳定预测全因痴呆风险</strong>——每升高 1 个 SD，风险 <strong>HR = 1.11（95% CI 1.02–1.20；I² = 0.0%；p = 0.018）</strong>；<strong>Horvath1、Hannum、PhenoAge、DunedinPACE 的 EAA 与痴呆风险均无显著关联</strong>。作者据此认为，现有时钟<strong>不足以作为神经退行病的生物标志物</strong>。</p>

{PREAMBLE_PREPRINT}

<h2>这项研究想回答什么</h2>
<p>「表观遗传时钟测出的生物学年龄」在过去十年被大量用作衰老干预试验的终点与观察性队列的暴露变量。但它到底<strong>能不能预测神经退行性疾病</strong>，此前一直是靠单项研究的零散结论拼接——不同时钟、不同疾病、不同研究设计混在一起，谁也说不清。本文做的就是把这块证据<strong>系统地合并并分代际拆解</strong>：五种主流时钟 × 痴呆（含 AD）及其他神经退行病（PD / MS / ALS），纵向 meta 分析 + 孟德尔随机化证据并列评估。</p>
<p>通讯单位值得单独一提：<strong>新加坡国立大学 Yong Loo Lin 医学院下属的 NUS 健康长寿研究院</strong>，通讯作者 Andrea B. Maier 是衰老流行病学领域的资深研究者——这不是一个外围团队对主流工具的外行批评。</p>

<h2>核心发现</h2>
<ol>
<li><strong>唯一站得住的关联是 GrimAge。</strong>纵向 meta 分析：GrimAge EAA 每升高 1 个 SD，全因痴呆风险 <strong>HR = 1.11（95% CI 1.02–1.20）</strong>，异质性 <strong>I² = 0.0%</strong>，<strong>p = 0.018</strong>。I² 为 0 意味着纳入研究之间高度一致——这在观察性 meta 分析里并不常见。</li>
<li><strong>四个阴性结果才是本篇的重心。</strong><strong>Horvath1 EAA、Hannum EAA、PhenoAge EAA、DunedinPACE 与痴呆风险均无显著关联</strong>。换句话说，目前被最广泛使用、也最常被写进试验方案的几代时钟，在这份合并证据里<strong>没有显示出对痴呆的预测力</strong>。</li>
<li><strong>其他神经退行病高度异质。</strong>PD / MS / ALS 的证据在「时钟代际 × 研究设计」之间分散，摘要<strong>未给出合并效应量</strong>。</li>
<li><strong>孟德尔随机化只提供有限的因果性证据。</strong>即现有遗传学证据<strong>不足以支撑「表观年龄加速导致神经退行」的因果解读</strong>。</li>
<li><strong>方法学规格不低</strong>：相关与层级效应 meta 分析（correlated and hierarchical effects model），限制性最大似然估计 + Knapp-Hartung 校正。</li>
</ol>

<h2>定量结果与证据边界</h2>
<table>
<tr><th>项目</th><th>数值</th><th>备注</th></tr>
<tr><td>检索记录数</td><td>42,023 条</td><td>6 个数据库，2011-01-01 至 2026-04-15</td></tr>
<tr><td>纳入观察性研究</td><td>37 项（n = 46,365）</td><td>女性 60.5%；平均年龄中位数 69.4 岁（IQR 62.5–73.3）</td></tr>
<tr><td>孟德尔随机化研究</td><td>7 项</td><td>因果性证据「有限」</td></tr>
<tr><td>GrimAge EAA → 全因痴呆</td><td><strong>HR = 1.11（95% CI 1.02–1.20）</strong></td><td>I² = 0.0%，p = 0.018；每 1 个 SD</td></tr>
<tr><td>Horvath1 / Hannum / PhenoAge / DunedinPACE</td><td>与痴呆风险<strong>无显著关联</strong></td><td>具体效应量与 CI <strong>待补全文</strong></td></tr>
<tr><td>PD / MS / ALS 合并效应量</td><td>未给</td><td><strong>待补全文</strong></td></tr>
<tr><td>发表偏倚检验（Egger / funnel plot）</td><td>未给</td><td><strong>待补全文</strong></td></tr>
</table>
<p><strong>定量缺口（本站未做任何补全）：</strong>除痴呆外的各时钟 I² 与异质性来源分解未给；
PD/MS/ALS 未给合并效应量；<strong>偏倚检验结果（Egger / funnel plot）待补全文</strong>；
「阴性结论究竟是效应量真的小，还是样本量不足」<strong>摘要未给出把握度分析</strong>。</p>

<h2>四条必须保留的意见</h2>
<ol>
<li><strong>这是预印本，未经同行评审。</strong>meta 分析的结论高度依赖纳入标准与时钟版本处理，而这两项恰恰需要全文才能核查。</li>
<li><strong>时钟版本混杂是真实风险。</strong>第一代（Horvath1 / Hannum）、第二代（PhenoAge / GrimAge）与第三代（DunedinPACE）在本文被并列比较，若纳入研究各自使用的版本与算法实现不一致，跨研究的效应量可比性会下降。</li>
<li><strong>纳入限于「已报告 DNAm 年龄与疾病关联」的发表文献</strong>，存在<strong>发表偏倚</strong>——报告了阴性关联的研究更可能根本没被写进论文，也就进不了这个 meta。</li>
<li><strong>「不足以作为生物标志物」≠「时钟无用」。</strong>本文检验的是<strong>对神经退行病发病的预测力</strong>，不等于否定时钟对全因死亡、心血管风险或干预响应的价值。</li>
</ol>

<h2>为什么值得关注</h2>
<p>这是目前对「表观遗传时钟能否作为神经退行病外周生物标志物」<strong>最系统的一次证伪性评估</strong>。它的价值不在于又多了一个阳性关联，而在于给整个领域划了一条线：<strong>把「DNAm 年龄」当默认终点之前，得先说清楚用的是哪个时钟。</strong></p>
<p>最值得单独成段的一点：<strong>GrimAge 之所以突出，很可能不是因为它更「准」地测到了甲基化年龄，而是因为它整合了吸烟史与血浆蛋白等临床表型</strong>——也就是说，它更像一个复合临床风险评分，而不是纯粹的甲基化年龄信号。这个解释若成立，会直接改变人们对「第二代时钟为什么有效」的理解。</p>
<p>对正在设计试验的研究者还有一条实操提示：ClinicalTrials.gov 上有一批以 DNAm 年龄为主要或次要终点的干预试验。<strong>如果这些试验选的终点是 Horvath1 或 PhenoAge，那么按本文的合并证据，其结果的临床解释力需要重新评估</strong>——终点测到了变化，不等于痴呆风险会跟着变。</p>""",
            related=REL_CLOCK,
        ),

        "Aged-Brain-Vascular-Neural-Coupling-Entorhinal-Perfusion-2026.html": dict(
            topic="神经退行", ev="B", tag="预印本",
            title="老化脑的两条独立轴线：内嗅「网格编码」只是不稳了，海马灌注与血管搏动各走各的",
            crumb="老化脑：表征「不稳定」而非消失，灌注与搏动是两个维度",
            desc="两项同日 bioRxiv 研究合并读：85 名老年人中，内嗅六向信号变弱反映的是网格表征"
                 "跨 run 不可复现（不稳定）而非缺失；35 人 7T MRI 显示海马灌注与微血管容积搏动指数"
                 "是两套空间组织，各自有年龄差异。",
            source=src_brain,
            body=f"""<p><strong>一句话结论（两篇合并读）：</strong>同日上线 bioRxiv 的两项老化脑研究给出了一个共同的叙事修正——<strong>老化损伤的是「稳定性」与「组织方式」，不是「有没有」</strong>。第一篇（N=85 老年人，VR 导航 + fMRI）证明<strong>老年人内嗅皮层「六向信号」变弱，反映的是网格表征不稳定（跨 run 方向模式不可复现）而非表征缺失</strong>；第二篇（N=35 青年＋老年，7T MRI）证明<strong>海马灌注与微血管容积搏动指数（mvPI）是两套彼此独立的空间组织</strong>，各自都有年龄相关差异，且<strong>青年组中检测到的一部分关联在老年组图谱中消失了</strong>。</p>

{PREAMBLE_PREPRINT}

<h2>一、内嗅皮层：是「不稳定」，不是「没有了」</h2>
<p>网格细胞（grid cell）的内嗅表征在人类通常用 fMRI 的<strong>六向（six-fold）朝向信号</strong>作为替代指标。既往观察到老年人这个信号变弱，常见的解释是<strong>表征退化/缺失</strong>。本文用可复现性把这两种解释区分开了。</p>
<h3>他们怎么做的</h3>
<ul>
<li><strong>85 名老年人</strong>，虚拟现实导航任务 + fMRI。</li>
<li>关键指标：<strong>六向朝向稳定性</strong>——方向特异性活动模式在<strong>不同 run 之间能否复现</strong>。</li>
<li>对照变量：<strong>实足年龄</strong>与<strong>局部结构指标</strong>（灰质等）。</li>
</ul>
<h3>核心发现</h3>
<ol>
<li><strong>朝向稳定性与后内侧内嗅皮层（pmEC）的六向信号强度相关</strong>——即「稳不稳」直接决定了fMRI 上「看不看得见」。</li>
<li><strong>左侧 pmEC 中，朝向稳定性越高，物体-位置记忆越好。</strong>把影像学指标接到了行为学上。</li>
<li><strong>年龄本身与局部结构指标都不能解释这两个指标的个体差异。</strong>换句话说，在这个老年队列内部，<strong>「表征稳定性」比「实足年龄」更有解释力</strong>。</li>
<li><strong>压后皮层（retrosplenial cortex）</strong>的绝对朝向稳定性与左 pmEC 稳定性相关，中介分析支持其经由 pmEC 稳定性对六向信号产生间接关联。</li>
</ol>
<h3>保留意见</h3>
<ul>
<li><strong>纯老年人队列（N=85），无青年对照组</strong>——摘要未报告年龄范围与方差。所以严格讲，这是<strong>「老年人内部的个体差异」</strong>，能否推到「老化效应」需要谨慎。</li>
<li>记忆关联是<strong>相关 / 中介设计，无因果干预</strong>。六向信号作为网格细胞的 fMRI 替代指标本身<strong>仍有方法学争议</strong>。</li>
<li><strong>效应量全部待补全文</strong>：相关系数、中介效应值、p 值，摘要均未给出。</li>
</ul>

<h2>二、海马：灌注与搏动性是两个维度，不是一个</h2>
<h3>他们怎么做的</h3>
<ul>
<li><strong>7T MRI，35 名青年与老年成人</strong>；在<strong>展开后的海马皮层</strong>上绘制灌注图与<strong>微血管容积搏动指数（mvPI）</strong>图。</li>
<li>与空间转录组、频谱模拟做交叉验证。</li>
</ul>
<h3>核心发现</h3>
<ol>
<li><strong>灌注与 mvPI 呈现不同的空间组织</strong>，且<strong>两者均存在年龄相关差异</strong>。</li>
<li>青年组中：<strong>灌注</strong>优先对应 <strong>PV（parvalbumin）中间神经元密度</strong>与 <strong>beta/gamma 频段</strong>分布；<strong>mvPI</strong> 则与 <strong>theta 频段</strong>分布相关。</li>
<li><strong>在青年组检测到的一部分关联，在老年组图谱中未被检测到</strong>——这是本篇的阴性结果，也是老化信号的所在。</li>
<li>机制线索：频谱模拟提示 mvPI–theta 关系的一个可能解释是<strong>心跳相关的相位重置</strong>；空间转录组显示 <strong>PIEZO2</strong> 在血管周围富集，是<strong>血管机械转导</strong>的候选介导因子。</li>
</ol>
<h3>保留意见</h3>
<ul>
<li><strong>N=35 且为青年+老年混合分组</strong>，摘要未给各组人数与年龄均值；横断面设计<strong>无法区分老化与队列效应</strong>。</li>
<li>「老年组未检测到」属<strong>阴性结果，未报告统计把握度</strong>，样本量不足的可能性无法排除。</li>
<li><strong>PIEZO2 是转录组层面的候选，未做功能验证</strong>；具体影像学效应量与 p 值<strong>待补全文</strong>。</li>
</ul>

<h2>三、合并起来读：一个可操作的二分框架</h2>
<table>
<tr><th>维度</th><th>研究</th><th>老化改变的是什么</th><th>样本</th></tr>
<tr><td>神经表征</td><td>内嗅网格编码</td><td><strong>稳定性下降</strong>（跨 run 不可复现），不是信号消失</td><td>85 名老年人</td></tr>
<tr><td>代谢供给</td><td>海马灌注</td><td>空间组织随年龄改变，青年期的神经关联在老年组检测不到</td><td>35 人（青年＋老年）</td></tr>
<tr><td>机械应力</td><td>微血管容积搏动（mvPI）</td><td>与灌注<strong>不同轴</strong>的组织方式，theta 关联；PIEZO2 为候选介导因子</td><td>同上</td></tr>
</table>
<p>第二篇给出的二分框架——<strong>灌注（代谢供给）与搏动性（机械应力）是老化脑血管的两条独立轴线</strong>——之所以有价值，是因为它把一个笼统的「脑血流变差」拆成了两个可以分开测量、也可能分开干预的变量。<strong>PIEZO2 则把「血管搏动 → 神经元活动」的机械转导假说推到了人类身上</strong>，这在老化脑研究里是相对稀缺的机制-影像结合证据。</p>
<p>两篇合起来还有一条更一般的提示：<strong>老化研究里大量「信号变弱了」的观察，可能有一部分是「稳定性变差了」被误读成了「功能消失了」。</strong>这个区分对干预设计影响很大——<strong>稳定性是潜在可训练、可药理操作的状态变量，而「缺失」听起来就不可逆</strong>。</p>

<h2>四、定量边界</h2>
<ol>
<li>两篇<strong>摘要均未给出相关系数、中介效应量、影像学效应量与 p 值</strong>，本站一律标<strong>待补全文</strong>，未做任何推算。</li>
<li>两篇均为<strong>横断面设计</strong>，<strong>不能区分老化与队列效应</strong>；其中第一篇<strong>无青年对照</strong>。</li>
<li><strong>bioRxiv 源站对本环境返回 403</strong>，<strong>两篇全文均未获取</strong>，方法细节与统计量无从核验。</li>
<li>样本量偏小（N=85 / N=35），阴性结果的把握度无法评估。</li>
</ol>""",
            related=REL_BRAIN,
        ),

        "Young-BM-Microglia-Like-Cells-BDNF-TrkB-Aged-Brain-2026.html": dict(
            topic="神经退行", ev="B", tag="预印本",
            title="异体年轻细胞的认知获益不必「永久嵌合」：早期归巢期的一个 BDNF-TrkB 窗口",
            crumb="年轻骨髓细胞的认知获益：早期归巢 + BDNF-TrkB，不需永久嵌合",
            desc="可诱导清除小鼠体系证明：移植后 1 个月清除年轻骨髓来源小胶质样细胞会取消认知改善"
                 "并抑制树突棘分支，3 个月清除则无影响；药理阻断 TrkB 复制同样的损害。"
                 "提示获益发生在早期归巢窗口，且可药理操作。",
            source=src_mg,
            body=f"""<p><strong>一句话结论：</strong>用可诱导清除体系证明，<strong>年轻供体骨髓来源小胶质样细胞改善老年脑认知，不需要细胞永久嵌合</strong>——移植后 <strong>1 个月</strong>清除这些细胞会<strong>严重损害认知功能的改善</strong>并<strong>抑制海马神经元树突棘分支形成</strong>，而移植后 <strong>3 个月</strong>清除则<strong>不影响已获得的海马依赖行为改善</strong>；药理学<strong>阻断 BDNF 受体 TrkB</strong> 产生与清除细胞<strong>相同的损害效应</strong>。结论指向：获益发生在<strong>早期脑内归巢期</strong>，通过 <strong>BDNF-TrkB</strong> 起效，且<strong>不必依赖细胞永久整合即可长期维持</strong>。</p>

{PREAMBLE_PREPRINT}

<h2>这项研究想回答什么</h2>
<p>异体共生（heterochronic parabiosis）、年轻血浆置换、年轻细胞移植这一类实验反复显示：<strong>来自年轻个体的因素能让老年组织「回春」</strong>。但一个始终没解决的关键问题是——<strong>这些获益是否要求供体细胞长期、永久地嵌合在受体组织里？</strong>如果答案是「必须永久嵌合」，那么细胞移植就是唯一路径，转化门槛极高；如果答案是「不需要」，那么<strong>存在被药理模拟的时间窗口</strong>。本文用可逆清除体系直接做了这个判别。</p>

<h2>他们怎么做的</h2>
<ul>
<li><strong>工具</strong>：构建 <strong>CX3CR1⁺ 巨噬细胞可被白喉毒素选择性清除</strong>的小鼠体系（CX3CR1 是中枢与外周髓系细胞的常用标记）。</li>
<li><strong>流程</strong>：年轻供体骨髓移植入老年野生型受体 → 在移植后 <strong>1 个月</strong>或 <strong>3 个月</strong>两个时点进行<strong>可控清除</strong>。</li>
<li><strong>读出</strong>：脑内小胶质细胞生态位的补充情况、外周免疫细胞招募、海马依赖行为、海马神经元树突棘分支。</li>
<li><strong>药理验证</strong>：阻断 BDNF 受体 <strong>TrkB</strong>，看是否复制清除表型。</li>
<li><strong>通讯</strong>：Ren-Ke Li（<strong>多伦多总医院研究所</strong>），长期做细胞治疗与心肌/组织修复方向。</li>
</ul>

<h2>核心发现</h2>
<ol>
<li><strong>移植后 3 个月清除：生态位空了，但行为不受影响。</strong>清除后脑内小胶质细胞生态位<strong>无法再被外周或中枢来源的巨噬细胞补充</strong>；伴随<strong>全身单核细胞招募显著减少、中性粒细胞大量涌入脑内</strong>；而<strong>海马依赖行为未受影响</strong>——作者推测是因为该时点海马内本来就没有这些细胞了。</li>
<li><strong>移植后 1 个月清除：获益被取消（最关键的一条）。</strong>此时 BM 来源小胶质样细胞<strong>在海马内丰富存在</strong>，清除会<strong>严重损害认知功能的改善</strong>，并<strong>抑制海马神经元树突棘分支形成</strong>。</li>
<li><strong>TrkB 阻断复制了清除的表型。</strong>药理学阻断 BDNF 受体 TrkB 产生<strong>与清除细胞相同的损害效应</strong>——把效应分子定位到了 BDNF-TrkB 轴。</li>
<li><strong>结论句</strong>：早期脑内归巢期通过 <strong>BDNF-TrkB</strong> 起效，且<strong>获益不需要细胞永久整合即可长期维持</strong>。</li>
</ol>

<h2>定量结果与证据边界</h2>
<table>
<tr><th>读出</th><th>移植后 1 个月清除</th><th>移植后 3 个月清除</th><th>定量</th></tr>
<tr><td>海马依赖行为改善</td><td><strong>严重损害</strong></td><td>未受影响</td><td><strong>待补全文</strong></td></tr>
<tr><td>海马神经元树突棘分支</td><td><strong>受抑制</strong></td><td>未报告</td><td><strong>待补全文</strong></td></tr>
<tr><td>小胶质细胞生态位</td><td>细胞丰富存在</td><td><strong>无法被补充</strong></td><td><strong>待补全文</strong></td></tr>
<tr><td>全身单核细胞招募</td><td>未报告</td><td>显著减少</td><td><strong>待补全文</strong></td></tr>
<tr><td>脑内中性粒细胞</td><td>未报告</td><td>大量涌入</td><td><strong>待补全文</strong></td></tr>
<tr><td>TrkB 阻断效应量</td><td colspan="2">复制清除表型（定性）</td><td><strong>待补全文</strong></td></tr>
<tr><td>各组动物数 / 行为学统计值</td><td colspan="2">未给</td><td><strong>待补全文</strong></td></tr>
</table>
<p><strong>定量缺口：</strong>摘要<strong>未给出各组动物数量、行为学效应量与统计值</strong>，
1 个月与 3 个月两个时点的<strong>认知改善幅度无法量化</strong>，也无法比较「改善了多少」与「损失了多少」。</p>

<h2>四条必须保留的意见</h2>
<ol>
<li><strong>因果链靠「阻断剂表型复制」单一证据支撑。</strong>缺少 <strong>TrkB 条件性敲除</strong>或 <strong>BDNF 中和 / 补充</strong>的双向验证——药理阻断剂的脱靶可能性无法排除。</li>
<li><strong>无定量</strong>：所有行为学结论均为定性描述，改善幅度与统计显著性不可评估。</li>
<li><strong>干预强度极高。</strong>这是<strong>骨髓移植级别</strong>的强干预（涉及清髓/免疫重建级别的预处理），向人类转化的<strong>安全性与免疫相容性问题摘要完全未涉及</strong>。</li>
<li><strong>小鼠模型 + 预印本 + 全文未获取。</strong>bioRxiv 源站对本环境返回 403，方法细节与统计量无从核验。</li>
</ol>

<h2>为什么值得关注</h2>
<p>它把「年轻细胞/年轻微环境 rejuvenation」从<strong>现象层推进到了机制层</strong>：把异体年轻骨髓细胞的认知获益定位到 <strong>BDNF-TrkB + 早期归巢</strong> 这一个<strong>可药理操作的节点</strong>。这意味着一条重要的转化含义——<strong>不必做细胞移植，用 TrkB 激动剂或小分子模拟，可能就能复现部分获益</strong>。</p>
<p>更值得注意的是它对领域内那个长期争论给出的答案倾向：在<strong>「获益是否需要持久嵌合」</strong>这个关键问题上，本文与异体共生、部分重编程这两条主线的证据倾向是<strong>一致的——不需要</strong>。三条独立路径指向同一结论，比任何单篇都更有分量。</p>
<p>同时它给出了一个<strong>时间窗口</strong>的设计提示：1 个月有效、3 个月无效，说明<strong>干预存在关键的早期窗口期</strong>。任何试图在人体上复现这类效应的方案，投递时机很可能比剂量更重要。</p>""",
            related=REL_MG,
        ),
    }

    for slug in A:
        if slug in used:
            sys.exit(f"✗ slug 已存在，拒绝覆盖：{slug}")
    print(f"本批新写 {len(A)} 篇（观察哨 1–2、补遗 1–3 按上游建议入档不成篇，理由见文件头）")
    ga.A = A
    ga.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
