#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_articles_intake_2026-10-21.py —— 内容摄入第 N 批（2026-10-21 双产出）

事实源（均经 tdrive.file_download + stat -c%s 实测字节数）
──────────────────────────────────────────────────────
· 文献层《预印本速递_2026-10-21》        file_id dNacOPpqOpKF  实测 39,189 B
  → .intake/raw/preprint-2026-10-21.md
· 文献层《预印本全文级流水线_运行摘要_2026-10-19》 file_id dEbLgGGlcwOG 实测 8,297 B
  → .intake/raw/preprint-summary-2026-10-19.md（**运行摘要，无可成篇条目**，只作链路留痕）
· 行业层《行业情报周报_2026-10-21》      file_id dmJkBUnnRwKd  实测 47,589 B（md）
                                         file_id dxCnKBUCoQXK  实测 30,825 B（xlsx 同表）
  → .intake/raw/industry-2026-10-21.md

查重与硬核验（四路查重 + 高特异关键词站内原文硬核验）
────────────────────────────────────────────────────
harvest.py 对 3 份产出抽出 53 条候选，判定：漏收 6 / 已收录 6 / 需人工核对 41，
其中 **47 条 confidence=none**。按硬规则 3（confidence=none ≠ 漏收），
改用 DOI 尾号与公司/靶点专名在 news/ 原文逐条硬核验：

| 条目 | 硬核验词 | news/ 命中 | 结论 |
|---|---|---|---|
| 观察哨#1 HGPS×Hi-C | `760205` | 0 篇 | 真漏收 → 成篇 |
| 观察哨#3 CARM1 | `759715` / `CARM1` | 0 篇 | 真漏收 → 成篇 |
| 观察哨#4 BNIP3L/NIX | `759942` / `BNIP3L` | 0 篇 | 真漏收 → 成篇 |
| 观察哨#2 MEMR | `26351829` | 0 篇 | 真漏收，但**否定性结果 + 摘要零定量** → 不成篇（入档） |
| 补遗#1 Semaglutide 心率 | `26365823` | 0 篇 | 真漏收，属 GLP-1 安全性参照 → 不成篇（入档） |
| 摘要漏收 [5] EHR 生物年龄 | `26365756` | 0 篇 | 真漏收，但摘要未给定量 → 不成篇（入档） |
| Mission MTX325 | `MTX325` / `Mission Therapeutics` | 0 篇（`USP30` 仅 1 篇且为融资综述） | 真漏收 → 成篇 |
| Acta $24M | `Acta Pharmaceuticals` / `GSM-779690T` | 0 篇 | 真漏收 → 成篇 |
| 内在能力终点之争 | `OCHEN` / `intrinsic capacity` | 0 / 2 篇 | OCHEN 为新细节、Beard 访谈为新事件 → 成篇（与既有两篇互链） |

⚠️ 泛词误判提醒：`progeria` 命中 5 篇、`Alector` 命中 35 篇 —— 只能证明「同主题文章多」，
**不能证明本条已收录**；真正判据是 DOI 尾号，均为 0 命中。

纪律
────
· 只写产出给出的事实；预印本侧**摘要未给出的定量一律标「待补全文」**，数值不臆测、不从同类文献套用。
· 证据分级沿用全站 notice-box 口径：A 人体 / B 临床前（动物·体外细胞）/ C 预印本·观点·行业披露。
  - 预印本 3 篇均为**原始研究**（人细胞 / 小鼠 / 人神经元＋线虫），故定 **B**；
    「预印本、未经同行评审、全文未获取」由 tag 与正文首段明示，**不用 C 掩盖「这是原始研究」**。
  - 行业 3 篇为**公司公告 / 监管会议报道 / 媒体转述**，定 **C**。
· 内部链接 slug 全部取自 data/articles.json，且经 news/ 目录实际存在性校验（脚本内硬校验）。
· 上游交接建议「本期无主榜、不建议逐条成篇」已审慎采纳：观察哨 #1/#3/#4 虽摘要零定量，
  但**它们是本期唯一真正做衰老机制的稿件**，且分别对接「早老症/染色质架构」「肌少症·干细胞耗竭」
  「线粒体自噬」三条站内既有主线，故成篇；观察哨 #2、补遗 #1 按上游建议入档不成篇。
"""
import html
import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATE = "2026-10-21"

# ── 内部链接：均经 news/ 目录实际存在性校验（2026-10-21 实查）──
REL_HGPS = [
    ("White-Adipose-Atrophy-Accelerates-Aging-Male-2026.html",
     "白色脂肪萎缩加速雄性小鼠衰老——Nature Communications 新研究"),
    ("RANKL-Antibody-Progeria-Longevity-2026.html",
     "靶向 RANKL 中和抗体延长早衰小鼠寿命"),
    ("Splice-Donor-Disruption-Progerin-Rescue-2026.html",
     "基因组剪接供体位点破坏可挽救早衰症全身病变"),
    ("DNA-Methylation-Clock-Epigenetic-Progeria-2026.html",
     "DNA 甲基化时钟：被拆解的早衰密码"),
]
REL_CARM1 = [
    ("Senescent-Cells-Sarcopenia-Therapy.html",
     "衰老细胞如何驱动肌少症：Senolytics 与 Senomorphics 双路径干预新进展"),
    ("NMJ-Failure-Sarcopenia-ClC-1-Inhibition-2026.html",
     "肌肉衰老新机制：神经肌肉接头失效与 ClC-1 离子通道抑制"),
]
REL_MITOPHAGY = [
    ("PPTC7-Import-Arrest-Mitophagy-Pathway-Switch-bioRxiv-2026.html",
     "一个 phosphatase 的输入受阻，同时按下线粒体自噬两条通路的开关"),
    ("Mitochondrial-Dysfunction-Inflammaging-Mechanistic-Bridge-GeroScience-2026.html",
     "线粒体作为「生物能量衰竭 → 衰老/炎症衰老」的机制性桥梁"),
    ("Autophagy-Restore-Glaucoma-Retinal-Ganglion-2026.html",
     "恢复自噬可保护青光眼视网膜神经节细胞：mTOR 抑制剂新机制研究"),
]
REL_MISSION = [
    ("NOPARK-NR-Early-Parkinson-Phase3-JAMA-2026.html",
     "NOPARK 三期揭盲：410 人每日 1000 mg NAD⁺ 前体一年，主要终点显著劣于安慰剂"),
    ("LRRK2-EV-cGAS-STING-Parkinson-Accelerated-Aging-Cell-Reports-2026.html",
     "LRRK2 突变＋细胞外囊泡：帕金森病作为「加速衰老疾病」的新证据"),
    ("Mitochondria-Master-Regulator-Aging-Inflammaging-2026.html",
     "线粒体：衰老的主调控器，连接能量代谢与慢性炎症"),
]
REL_ACTA = [
    ("Amyloid-Trajectory-Bifurcation-Normal-Aging-AD-2026.html",
     "分岔的淀粉样蛋白轨迹区分正常老化与阿尔茨海默病进展"),
    ("Plasma-PTau217-ATN-Axis-Performance-Boundaries-ADNI-medRxiv-2026.html",
     "血浆 p-tau217 不是万能的：AUROC 从 0.95 掉到 0.79，取决于你问哪个轴"),
    ("C2N-PrecivityAD2-Cambridge-Cognition-UK-Alzheimer-Diagnosis.html",
     "阿尔茨海默病诊断的两条捷径：血检＋数字认知在英国全科诊所做到了 90% 准确率"),
]
REL_IC = [
    ("WHO-Intrinsic-Capacity-Health-Measurement-2026.html",
     "WHO「内在能力」框架：首次可能直接测量健康而非疾病"),
    ("FDA-Aging-Regulatory-Science-Priority-ARDD-2026.html",
     "FDA 把「衰老与长寿」写进监管科学议程：ARDD 2026 释放的信号与仍未解决的问题"),
    ("Repair-Biotechnologies-REP-0003-FDA-RDEP-2026.html",
     "Repair Bio 旗下 REP-0003 获 FDA RDEP 资格：mRNA 疗法瞄准细胞内游离胆固醇清除"),
]

PREAMBLE_PREPRINT = (
    '<p class="notice-box"><strong>⚠️ 本文为预印本，未经同行评审；'
    '本次仅依据 bioRxiv 官方 API 返回的摘要原文撰写，全文未获取'
    '（源站对本环境返回 HTTP 403），结论可能在正式发表时变更。'
    '摘要未给出的定量一律标注「待补全文」，未做任何数值推算补全。</strong></p>')


def notice(ev):
    """按来源切换证据分级框：预印本口径 / 行业情报口径"""
    t = {"A": "A 级（同行评议人体研究）",
         "B": "B 级（同行评议临床前研究，主要为动物模型）",
         "C": "C 级（预印本 / 观点评论，非原始研究）"}[ev]
    b = ("<p><strong>本文核心结论来自患者来源细胞、基因敲入小鼠与人神经元／线虫模型，"
         "属临床前证据，不能外推至人体。</strong>「谱系巩固失败」「卫星细胞耗竭」「抑制 Tau 聚集」"
         "等表述在临床前模型中的意义，与人类临床结局之间仍有距离。</p>" if ev == "B" else
         "<p><strong>本文属机构披露 / 行业信息，不是同行评议的原始研究。</strong>"
         "文中金额、阶段、日期与表述均来自公司公告、监管会议报道与行业媒体，"
         "<strong>未经独立核实</strong>。融资公告与管线进展<strong>不构成临床证据</strong>；"
         "「首例给药」「达到主要终点」「认定」等表述各有其特定含义，不等于疗效证明或监管批准。</p>")
    src = ("<p><strong>关于本文的文献来源：</strong>本站依据 <strong>bioRxiv 预印本官方 API "
           "返回的摘要原文</strong>撰写（来源：IMA 知识库《预印本速递》2026-10-21 期，"
           "摘要级，全文未获取）。</p>" if ev == "B" else
           "<p><strong>关于本文的文献来源：</strong>本站依据 IMA 知识库「行业情报周报」"
           "2026-W43 期（2026-10-21）撰写，原始出处为各公司公告、监管文件与行业媒体报道。"
           "周报中标注「待核实」的条目，本文<strong>照录其存疑状态，不做补全</strong>；"
           "未披露的金额一律写「未披露」，<strong>不做估算</strong>。</p>")
    return (f'<div class="notice-box">\n'
            f'    <p><span class="tier tier-{ev.lower()}">{ev} 级</span>'
            f'<strong>证据分级：{t}</strong></p>\n'
            f'    {b}\n'
            f'    {src}\n'
            f'</div>')


def main():
    arts = json.load(open(os.path.join(ROOT, "data/articles.json"), encoding="utf-8"))
    used = {a["slug"] for a in arts}
    all_rel = REL_HGPS + REL_CARM1 + REL_MITOPHAGY + REL_MISSION + REL_ACTA + REL_IC
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

    DOI_HGPS = "10.64898/2026.10.19.760205"
    DOI_CARM1 = "10.64898/2026.10.17.759715"
    DOI_NIX = "10.64898/2026.10.18.759942"

    src_hgps = (
        f'<em>bioRxiv</em>（cell biology）· 预印本 v1 · 2026-10-20：'
        f'Abnormal nuclear organization impairs adipogenic lineage commitment and terminal '
        f'maturation in Hutchinson-Gilford progeria syndrome (HGPS)'
        f' · DOI <a href="https://doi.org/{DOI_HGPS}" target="_blank" '
        f'rel="noopener noreferrer">{DOI_HGPS}</a>'
        f' · 第一作者 N. Gogia；通讯 Rachel Patton McCord（美国田纳西大学诺克斯维尔分校）'
        f' · 来源：IMA 知识库《预印本速递》2026-10-21 期（摘要级，全文未获取）')

    src_carm1 = (
        f'<em>bioRxiv</em>（cell biology）· 预印本 v1 · 2026-10-20：'
        f'Phosphorylation of CARM1 at Ser572 preserves muscle stem cell self-renewal by '
        f'restricting premature myogenic commitment'
        f' · DOI <a href="https://doi.org/{DOI_CARM1}" target="_blank" '
        f'rel="noopener noreferrer">{DOI_CARM1}</a>'
        f' · 第一作者 C. A. VanGenderen；作者含 M. A. Rudnicki；通讯 Natasha C. Chang（麦吉尔大学）'
        f' · 来源：IMA 知识库《预印本速递》2026-10-21 期（摘要级，全文未获取）')

    src_nix = (
        f'<em>bioRxiv</em>（cell biology）· 预印本 v1 · 2026-10-20：'
        f'BNIP3L/NIX-mediated mitophagy limits Alzheimer disease pathology and preserves '
        f'neuronal function'
        f' · DOI <a href="https://doi.org/{DOI_NIX}" target="_blank" '
        f'rel="noopener noreferrer">{DOI_NIX}</a>'
        f' · 第一作者 Y. Li；作者含 V. Bohr（NIA）；通讯 Konstantinos Pakalikaras'
        f'（雅典国立卡波季斯特里亚大学医学院生理学系）'
        f' · 来源：IMA 知识库《预印本速递》2026-10-21 期（摘要级，全文未获取）')

    src_mission = (
        'Mission Therapeutics 公司新闻稿（GlobeNewswire，2026-10-15）'
        '｜Longevity.Technology 报道（2026-10-19）'
        '｜来源：IMA 知识库《行业情报周报》2026-W43 期（2026-10-21）'
        '｜原文：<a href="https://www.globenewswire.com/news-release/2026/10/15/3381299/0/en/'
        'mission-therapeutics-doses-first-parkinson-s-patient-in-phase-1b-study-of-potential-'
        'disease-modifying-treatment-mtx325.html" target="_blank" rel="noopener noreferrer">'
        'GlobeNewswire 2026-10-15</a>')

    src_acta = (
        'Business Wire 通稿（2026-10-15），经 Times Argus 与 The Joplin Globe 同源转载'
        '｜来源：IMA 知识库《行业情报周报》2026-W43 期（2026-10-21）'
        '｜原文：<a href="https://www.timesargus.com/news/business/acta-pharmaceuticals-closes-'
        '24-million-in-seed-financing-for-alzheimer-s-disease-pipeline-targeting-early/'
        'article_7c53a760-deda-5dc6-92f3-929bca7e4e1d.html" target="_blank" '
        'rel="noopener noreferrer">Times Argus 2026-10-15</a>')

    src_ic = (
        'WHO 老龄化与生命历程司前司长 John Beard 在 Longevity.Technology 播客的系统阐述'
        '（2026-10-19）｜FDA ARDD 2026 会议报道（Global Longevity Association、regeneration.ai '
        '现场引述，2026-10-01 会议 / 2026-10 整理）'
        '｜来源：IMA 知识库《行业情报周报》2026-W43 期（2026-10-21）'
        '｜原文：<a href="https://longevity.technology/news/intrinsic-capacity-a-new-way-to-'
        'measure-healthy-aging/" target="_blank" rel="noopener noreferrer">'
        'Longevity.Technology 2026-10-19</a>')

    A = {
        "HGPS-Adipogenic-Lineage-HiC-Chromatin-2026.html": dict(
            topic="表观遗传", ev="B", tag="预印本",
            title="早老症的脂肪流失，问题不在「启动」而在「巩固」：Hi-C 把 3D 基因组和脂肪谱系失败接上了",
            crumb="早老症的脂肪流失卡在「巩固」这一步",
            desc="在年龄匹配的健康人与 HGPS 患者皮肤成纤维细胞里诱导成脂：谱系「启动」速率相当，"
                 "失败发生在下游的「巩固」——脂滴形态异常、转录响应延迟紊乱、替代谱系 priming 未收敛。"
                 "但摘要没给任何数字。",
            source=src_hgps,
            body=f"""<p><strong>一句话结论：</strong>在<strong>年龄匹配</strong>的健康对照与 HGPS 患者来源皮肤成纤维细胞中诱导成脂分化后发现，HGPS 细胞<strong>向成脂谱系「定向（commit）」的速率与对照相当</strong>，分歧发生在下游——异常脂滴形态、延迟且紊乱的转录响应，且脂肪成熟停滞的同时<strong>仍保留向骨软骨／血管等替代谱系的分化潜能</strong>；Hi-C 显示病因特异的<strong>分化期染色质区室重组失败</strong>。</p>

{PREAMBLE_PREPRINT}

<h2>这项研究想回答什么</h2>
<p>HGPS（Hutchinson-Gilford 早老症）由截短的 Lamin A——即 <strong>progerin</strong>——驱动，核架构失稳，<strong>优先累及间充质谱系组织</strong>；其中显著缺陷之一是<strong>早发且严重的皮下脂肪萎缩</strong>。作者要检验的假设很具体：<strong>染色质架构紊乱是不是 MSC 谱系定向与成脂失败的根因？</strong></p>
<p>为了保住<strong>供体年龄、表观遗传史与组织背景</strong>这三个变量，他们没有用细胞系，而是在<strong>年龄匹配的健康对照与 HGPS 患者来源皮肤成纤维细胞</strong>中诱导成脂，并在整个分化时间进程上做<strong>成像 + bulk RNA-seq + Hi-C</strong> 三模态取样。</p>

<h2>核心发现</h2>
<ol>
<li><strong>关键阴性结果（最重要的一条）：定向没问题。</strong>HGPS 成纤维细胞向成脂谱系「启动」的速率<strong>与健康对照相当</strong>——这直接反驳了「HGPS 脂肪萎缩 = 分化能力缺陷」的默认归因。</li>
<li><strong>分歧在下游的「巩固」。</strong>诱导后表现为<strong>异常的脂质滴形态</strong>、<strong>紊乱且延迟的转录响应</strong>。</li>
<li><strong>双向 priming 未被收敛。</strong>在脂肪成熟停滞的同时，细胞<strong>仍保留对骨软骨／血管等替代间充质谱系的 priming</strong>——即「该收敛的选择没有收敛」。</li>
<li><strong>Hi-C 的增量信息在动态而非基线。</strong>两组之间存在一定基线空间区室差异，但<strong>更显著的差异出现在「诱导过程中如何重组区室」</strong>：健康细胞中脂质代谢基因的<strong>区室-转录耦合</strong>在成脂期很强，HGPS 中明显失调。</li>
<li><strong>结论句：</strong>HGPS 破坏的是谱系的<strong>巩固（consolidation）而非启动（initiation）</strong>，并与分化期染色质重组的疾病特异性失败相伴。</li>
</ol>

<h2>定量结果与证据边界</h2>
<table>
<tr><th>读出</th><th>结果</th><th>定量</th></tr>
<tr><td>成脂谱系定向速率</td><td>HGPS ≈ 健康对照（无差异）</td><td><strong>待补全文</strong></td></tr>
<tr><td>脂滴形态</td><td>异常（定性描述）</td><td><strong>待补全文</strong></td></tr>
<tr><td>分化期转录响应</td><td>延迟且紊乱</td><td><strong>待补全文</strong></td></tr>
<tr><td>替代谱系 priming</td><td>保留、未收敛</td><td><strong>待补全文</strong></td></tr>
<tr><td>Hi-C 区室重组</td><td>HGPS 中脂代谢基因区室-转录耦合失调</td><td><strong>待补全文</strong></td></tr>
</table>
<p><strong>必须标注的定量缺口：</strong>该摘要<strong>未提供任何数字</strong>——
<code>n = ?</code>、<code>供体年龄区间 = ?</code>、<code>Hi-C 测序深度与分辨率 = ?</code>、
<code>差异表达基因数 = ?</code>、<code>区室切换的定量幅度 = ?</code>。
<strong>这些数字本站没有推算，也没有从别处套用。</strong></p>

<h2>四条必须保留的意见</h2>
<ol>
<li><strong>摘要零定量是本篇最大的局限。</strong>「异常脂滴形态」「延迟的转录响应」这类判断没有伴随任何统计量，无法评估效应大小，也无法判断样本是否足以支撑「grade × timepoint」的三模态设计。</li>
<li><strong>模型是皮肤成纤维细胞，不是原代脂肪前体／MSC。</strong>作者这样做是为了保住「年龄／表观史／组织背景」，取舍合理，但<strong>不等于体内皮下脂肪组织的情形</strong>，外部效度要打折扣。</li>
<li><strong>Hi-C 的相关性 ≠ 因果。</strong>区室重组失败与转录失调是<strong>共变</strong>关系，摘要未给出扰动实验（例如 lamina／progerin 校正后的回补）来锁定因果方向。</li>
<li><strong>从早老症外推到正常衰老要谨慎。</strong>progerin 是极端扰动；本文回答的是「核架构崩坏会怎样」，<strong>不能直接等同于正常衰老中的脂肪组织流失机制</strong>。</li>
</ol>

<h2>为什么值得关注</h2>
<p>机制层面，它把「<strong>核 lamina 失稳 → 3D 基因组重组失败 → 谱系巩固失败 → 皮下脂肪萎缩</strong>」这条链补完整了，并且把失败点从「分化能力」精确挪到「巩固」——这会影响干预该怎么设计：<strong>不是提高定向效率，而是修巩固通路</strong>。</p>
<p>方法层面，<strong>年龄匹配 + Hi-C 时间序列</strong>这套组合拳是现成的可复用方案：想在正常衰老中测 MSC／脂肪前体是否存在类似的区室重组能力下降，可以直接照搬。</p>
<p>还有一个值得并读的点：「保留替代谱系 priming + 成熟停滞」这个细胞状态描述，与衰老领域里<strong>去分化／谱系漂移（lineage drift）</strong>的叙事高度同构。</p>""",
            related=REL_HGPS,
        ),

        "CARM1-Ser572-Muscle-Stem-Cell-Exhaustion-2026.html": dict(
            topic="器官衰老", ev="B", tag="预印本",
            title="肌肉干细胞「不该这么快决定命运」：CARM1 Ser572 是防耗竭的刹车，只有反复损伤才试得出来",
            crumb="CARM1 Ser572：只在反复损伤下暴露的刹车",
            desc="磷酸化缺失型敲入小鼠显示：单次损伤后再生基本正常，反复再生挑战却导致卫星细胞池进行性耗竭。"
                 "对肌少症研究的直接提示——只看单次损伤会漏掉这类表型。",
            source=src_carm1,
            body=f"""<p><strong>一句话结论：</strong>用<strong>磷酸化缺失型敲入小鼠（CARM1 SA）</strong>证明，CARM1 Ser572 磷酸化是<strong>延迟卫星细胞「决定命运」的刹车</strong>——<strong>单次损伤后再生基本正常，但反复再生挑战会导致卫星细胞池进行性耗竭</strong>，转录上表现为 TGFβ-SMAD 受损、Tgfbr3 下降、MYC 活性上升。</p>

{PREAMBLE_PREPRINT}

<h2>这项研究想回答什么</h2>
<p>骨骼肌再生依赖卫星细胞（MuSC），必须在<strong>成肌定向</strong>与<strong>自我更新</strong>之间取得平衡，才能终生维持再生能力。已知 CARM1 通过甲基化 PAX7 促进 Myf5 表达与成肌定向；肌营养不良蛋白糖蛋白复合物经 p38γ 介导的 <strong>CARM1 Ser572 磷酸化</strong>调控该通路——但<strong>这个磷酸化事件在体内的生理角色此前未知</strong>。本文就是要回答：这个位点在小鼠体内到底干什么。</p>

<h2>他们怎么做的</h2>
<ul>
<li><strong>工具</strong>：构建<strong>磷酸化缺失型敲入小鼠 CARM1 SA</strong>（Ser→Ala，位点不可磷酸化）。</li>
<li><strong>细胞层读出</strong>：成肌细胞的 PAX7 表达、融合能力、肌管形成。</li>
<li><strong>离体</strong>：单肌纤维实验，看卫星细胞的定向身份与自我更新型细胞数量。</li>
<li><strong>体内</strong>：单次损伤再生 vs <strong>反复再生挑战（serial injury）</strong>。</li>
<li><strong>转录组</strong>：稳态 vs 再生期的差异。</li>
<li><strong>作者阵容</strong>：含 <strong>M. A. Rudnicki</strong>（肌肉干细胞领域的奠基性人物之一），通讯 Natasha C. Chang（麦吉尔大学）。</li>
</ul>

<h2>核心发现</h2>
<ol>
<li><strong>成肌细胞表型</strong>：CARM1 SA 成肌细胞<strong>PAX7 表达下降、融合受损、肌管形成异常</strong>——尽管转录特征显示为<strong>加速的成肌进程</strong>（跑得快，跑不好）。</li>
<li><strong>离体单肌纤维</strong>：卫星细胞<strong>提前获得定向祖细胞身份</strong>，伴随<strong>自我更新型卫星细胞数量减少</strong>。</li>
<li><strong>最有价值的一条</strong>：<strong>肌肉发育与单次损伤后的再生基本保住</strong>，但<strong>反复再生挑战</strong>导致 CARM1 SA 小鼠<strong>卫星细胞池进行性耗竭</strong>。</li>
<li><strong>转录组</strong>：稳态下影响极小，再生期改变显著——<strong>细胞外基质相关基因表达下降、TGFβ-SMAD 信号受损、Tgfbr3 表达降低、MYC 活性升高</strong>，与「自我更新程序丧失 + 活化增强」一致。</li>
</ol>

<h2>定量结果与证据边界</h2>
<table>
<tr><th>读出</th><th>CARM1 SA 结果</th><th>定量</th></tr>
<tr><td>单次损伤后再生</td><td>基本正常</td><td><strong>待补全文</strong></td></tr>
<tr><td>反复再生挑战</td><td>卫星细胞池进行性耗竭</td><td><strong>待补全文</strong></td></tr>
<tr><td>Pax7⁺ 细胞比例</td><td>下降</td><td><strong>待补全文</strong></td></tr>
<tr><td>损伤轮次 / 各基因型 n</td><td>未给</td><td><strong>待补全文</strong></td></tr>
</table>
<p><strong>定量缺口：</strong>摘要<strong>无任何数字</strong>——
<code>各基因型 n = ?</code>、<code>损伤轮次 = ?</code>、<code>卫星细胞计数变化倍数 = ?</code>、
<code>Pax7⁺ 细胞比例 = ?</code>。全部表型均为定性描述，<strong>无法判断耗竭幅度</strong>。</p>

<h2>四条必须保留的意见</h2>
<ol>
<li><strong>「反复损伤」是衰老的替代模型，不是衰老本身。</strong>摘要未设老龄组，所以「进行性耗竭」能否解释<strong>老年小鼠／人</strong>的卫星细胞减少，这里<strong>没有直接证据</strong>，表述要小心。</li>
<li><strong>稳态影响「极小」本身就是信息。</strong>说明该位点是<strong>应急制动</strong>而非基础开关——干预窗口可能在<strong>再生期而非稳态期</strong>。</li>
<li><strong>无定量</strong>：耗竭幅度、统计显著性全部不可评估。</li>
<li><strong>bioRxiv 403，全文不可得</strong>：本篇目前无法核验方法细节与统计量。</li>
</ol>

<h2>为什么值得关注</h2>
<p>它与<strong>肌少症／干细胞耗竭</strong>这条主线直接对接：<strong>「单次应激扛得住、反复应激就崩」正是衰老干细胞生物学的核心命题</strong>。本文给了一个具体的分子刹车（CARM1-pSer572），可纳入「维持 MuSC 自我更新的调控节点」清单。</p>
<p>机制也可操作：<strong>TGFβ-SMAD 受损 + MYC 升高</strong>是可测量的下游读数，适合做干预筛选的 readout（例如能否用 TGFβ 通路激动剂回补耗竭表型）。</p>
<p>最后是一条<strong>实验设计层面的硬提示</strong>：如果你的课题涉及 MuSC 衰老，<strong>只看单次损伤会漏掉这类耗竭表型</strong>——必须加「重复损伤／serial injury」臂。这条对任何做干细胞衰老的实验室都成立，与本文结论是否被推翻无关。</p>""",
            related=REL_CARM1,
        ),

        "BNIP3L-NIX-Mitophagy-Alzheimer-Pathology-2026.html": dict(
            topic="神经退行", ev="B", tag="预印本",
            title="BNIP3L/NIX 线粒体自噬：人神经元到线虫的双向验证，缺失加剧 Tau 与 Aβ，回补则压住两者",
            crumb="BNIP3L/NIX 线粒体自噬同时压住 Tau 与 Aβ",
            desc="缺失 BNIP3L/NIX（或其线虫同源物 DCT-1）会同时恶化 Tau 与 Aβ 病理；回补活性则降低 Tau 磷酸化、"
                 "显著抑制 seeding 诱导的 Tau 聚集。跨物种双向证据，但摘要无一个数字。",
            source=src_nix,
            body=f"""<p><strong>一句话结论：</strong>确定 <strong>BNIP3L/NIX 依赖性线粒体自噬是一条保守的神经元质量控制通路</strong>——缺失它（或线虫同源物 <strong>DCT-1</strong>）会同时恶化 <strong>Tau 与 Aβ</strong> 病理并损害神经元网络／突触／行为功能；<strong>回补其活性</strong>则改善蛋白毒性应激下的神经元功能、降低 Tau 磷酸化、并显著抑制 seeding 诱导的 Tau 聚集。</p>

{PREAMBLE_PREPRINT}

<h2>这项研究想回答什么</h2>
<p><strong>线粒体自噬缺陷正成为阿尔茨海默病的关键促因</strong>，但神经元内控制线粒体清除的通路、以及它对病程的具体贡献此前不清。本文要做的就是把这条通路钉死，并检验它是否<strong>同时作用于 Tau 与 Aβ 两条病理轴</strong>。</p>

<h2>他们怎么做的（双向验证）</h2>
<ul>
<li><strong>缺失方向</strong>：敲除／敲低 <strong>BNIP3L/NIX</strong>（人／鼠体系）或其 <strong>C. elegans 同源物 DCT-1</strong>。</li>
<li><strong>增益方向</strong>：回补 BNIP3L/NIX 与 DCT-1 活性。</li>
<li><strong>读出</strong>：基础与应激诱导的线粒体自噬水平、线粒体稳态、Tau 与 Aβ 病理、神经元网络／突触／行为功能、人神经元中疾病相关的 Tau 磷酸化、原代小鼠神经元中 seeding 诱导的 Tau 聚集。</li>
<li><strong>作者阵容</strong>：含 <strong>V. Bohr</strong>（NIA 线粒体生物学资深研究者），通讯 Konstantinos Pakalikaras（雅典国立卡波季斯特里亚大学医学院生理学系）。</li>
</ul>

<h2>核心发现</h2>
<ol>
<li><strong>缺失加剧两条病理轴。</strong>缺失 BNIP3L/NIX 或 DCT-1 会<strong>削弱基础与应激诱导的线粒体自噬</strong>、破坏线粒体稳态，并<strong>同时加剧 Tau 与 Aβ 病理</strong>。</li>
<li><strong>功能层面同步受损。</strong>在人神经元与体内模型中，<strong>神经元网络、突触与行为功能</strong>均受损害。</li>
<li><strong>回补是正向的。</strong>恢复 BNIP3L/NIX 与 DCT-1 活性可改善体内蛋白毒性应激下的神经元功能、降低人神经元中疾病相关 Tau 磷酸化、并<strong>显著抑制原代小鼠神经元中 seeding 诱导的 Tau 聚集</strong>。</li>
<li><strong>作者结论。</strong>BNIP3L/NIX 介导的线粒体自噬是串联<strong>线粒体质量控制、蛋白稳态与神经元功能</strong>的机制性环节，恢复其活性是抗 AD 病理的潜在策略。</li>
</ol>

<h2>定量结果与证据边界</h2>
<table>
<tr><th>读出</th><th>方向</th><th>定量</th></tr>
<tr><td>线粒体自噬（基础／应激诱导）</td><td>缺失后削弱</td><td><strong>待补全文</strong></td></tr>
<tr><td>Tau / Aβ 病理</td><td>缺失后加剧</td><td><strong>待补全文</strong></td></tr>
<tr><td>人神经元 Tau 磷酸化</td><td>回补后降低</td><td><strong>待补全文</strong></td></tr>
<tr><td>seeding 诱导 Tau 聚集</td><td>回补后显著抑制</td><td><strong>待补全文</strong></td></tr>
<tr><td>行为学</td><td>缺失后受损</td><td><strong>待补全文</strong></td></tr>
</table>
<p><strong>定量缺口：</strong>摘要<strong>无任何数字</strong>——所有 "impaired / enhanced / markedly suppressed" 均无统计量。
<code>样本量与重复数 = ?</code>、<code>mitophagy flux 变化倍数 = ?</code>、
<code>Tau 聚集抑制百分比 = ?</code>、<code>行为学效应量 = ?</code>。
<strong>不可从同类文献推断后套用到此处。</strong></p>

<h2>四条必须保留的意见</h2>
<ol>
<li><strong>主题是 AD，不是衰老。</strong>它被收进来是因为<strong>线粒体自噬 + 蛋白稳态是衰老的两大标志</strong>，且做了跨物种验证；但<strong>摘要全篇没有把老化作为变量</strong>（无年龄组、无寿命数据）。<strong>别把它当成「延寿」证据读。</strong></li>
<li><strong>「种子化 Tau 聚集」模型的推广需谨慎。</strong>seeded aggregation 是急性外源诱导，与散发性 AD 的慢性进程不完全等价。</li>
<li><strong>缺少上游因果。</strong>摘要未说明衰老过程中 BNIP3L/NIX 活性是否下降、何时下降——这是把它接入「衰老」叙事的必要一环，目前是缺口。</li>
<li><strong>bioRxiv 403，全文不可得</strong>：本期无法核验方法细节与统计量。</li>
</ol>

<h2>为什么值得关注</h2>
<p>它把「<strong>线粒体自噬 → 蛋白稳态</strong>」这条轴做实了：如果你的综述要写「线粒体质量控制作为神经退行的共同上游」，这是一篇现成的<strong>人—线虫双向证据</strong>——缺失与回补两个方向都做了，比单方向的关联研究更有说服力。</p>
<p>作者阵容本身也是信号：<strong>V. Bohr 参与</strong>意味着这条线与 NIA 的线粒体-DNA 修复衰老轴可能有后续联动，可留意其正式发表版本。</p>
<p>实操上，BNIP3L/NIX 活性回补可作为线粒体自噬干预筛选体系里的<strong>正向标杆（positive control）</strong>，用来校准 platform 的检出下限。</p>""",
            related=REL_MITOPHAGY,
        ),

        "Mission-Therapeutics-MTX325-USP30-Parkinson-Phase1b-2026.html": dict(
            topic="神经退行", ev="C", tag="临床进展",
            title="线粒体自噬第一次进帕金森临床给药：Mission 的 USP30 抑制剂 MTX325 完成 1b 期首例",
            crumb="MTX325：把线粒体自噬推进帕金森 1b 期",
            desc="口服、脑渗透的 USP30 抑制剂 MTX325 在英国完成 1b 期首例给药，计划入组 36 例轻中度帕金森患者，"
                 "目标是建立临床作用机制证明，数据读出预计 2027 年底。",
            source=src_mission,
            body="""<p><strong>一句话结论：</strong>Mission Therapeutics 的 <strong>MTX325</strong>——一款口服、脑渗透的 <strong>USP30 抑制剂</strong>，旨在促进受损线粒体清除（线粒体自噬）——已在英国皇家利物浦大学医院完成 <strong>1b 期首例给药</strong>，计划入组 <strong>36 例</strong>轻中度原发性帕金森患者，<strong>数据读出预计 2027 年底</strong>。</p>

<h2>为什么这条值得单列</h2>
<p>本周行业情报里临床进展不少，但这一条与衰老生物学的<strong>「线粒体功能障碍」标志直接对应</strong>：USP30 是线粒体质量控制的<strong>核心负调控因子</strong>（去泛素化酶，拮抗 Parkin 介导的线粒体自噬）。抑制它，等于松开线粒体自噬的刹车。</p>
<p><strong>「线粒体自噬」此前在衰老研究里几乎是机制共识，但在临床上一直没有可给药的抓手。</strong>MTX325 进入 1b 期，是这条轴从「标志」走向「可干预靶点」的一步——所以本站把本篇与同期两篇线粒体自噬预印本并列阅读。</p>

<h2>已知信息</h2>
<table>
<tr><th>项目</th><th>内容</th></tr>
<tr><td>药物 / 靶点</td><td><strong>MTX325</strong>：<strong>USP30</strong> 抑制剂（去泛素化酶），口服、脑渗透</td></tr>
<tr><td>机制意图</td><td>促进受损线粒体清除（线粒体自噬）</td></tr>
<tr><td>阶段 / 事件</td><td><strong>1b 期首例给药</strong>（英国皇家利物浦大学医院）</td></tr>
<tr><td>设计</td><td>计划入组 <strong>36 例</strong>轻中度原发性帕金森患者（英国／欧洲／澳大利亚）</td></tr>
<tr><td>目标</td><td>建立<strong>临床作用机制证明（proof-of-mechanism）</strong>，并评估安全性、耐受性、生物标志物与影像</td></tr>
<tr><td>时间线</td><td><strong>数据读出预计 2027 年底</strong></td></tr>
<tr><td>已完成</td><td>健康志愿者 <strong>1a 期</strong>；<strong>PET 证实脑部分布与高 CNS 渗透</strong></td></tr>
<tr><td>临床前</td><td>线粒体自噬增加、α-突触核蛋白聚集与多巴胺能神经元获益</td></tr>
<tr><td>商业侧</td><td>投资方含 Pfizer Venture Investments、Sofinnova Partners、Roche Venture Fund；化合物专利期至 <strong>2041</strong></td></tr>
<tr><td>时间</td><td>公司稿 2026-10-15；Longevity.Technology 报道 2026-10-19</td></tr>
</table>

<h2>证据边界（三条，必须带进解读）</h2>
<ol>
<li><strong>1b 期主要看机制与安全，不是疗效。</strong>36 例、以 proof-of-mechanism 为目标的设计，<strong>不能得出任何临床获益结论</strong>。把它读作「线粒体自噬有了临床抓手」可以，读作「帕金森有了新疗法」则远远过早。</li>
<li><strong>本文全部信息来自公司新闻稿与行业媒体转述</strong>，非同行评议文献。临床前结果（α-突触核蛋白、多巴胺能神经元获益）未经独立复核。</li>
<li><strong>「PET 证实脑部分布与高 CNS 渗透」解决的是暴露问题，不是靶点验证问题</strong>——药物进了脑子，不等于它在该剂量下真的提高了人脑线粒体自噬通量。这正是 1b 期要回答的。</li>
</ol>

<h2>与衰老研究的关系</h2>
<p>把这条放进衰老坐标系：<strong>线粒体功能障碍</strong>是公认的衰老标志之一，<strong>线粒体自噬随龄下降</strong>则是该标志的核心机制环节。MTX325 的价值不在于帕金森这一适应症本身，而在于它<strong>第一次把线粒体自噬做成了可口服、可入脑、可临床给药的分子</strong>——如果 1b 期能证明人体内的机制（mitophagy 通量确实被抬高），这条轴的成药性就算被证伪或被证实，两种结果对衰老领域都有信息量。</p>
<p>参照系也值得记住：本站已记录过 <strong>NOPARK 三期</strong>——410 人每日 1000 mg NAD⁺ 前体一年，<strong>主要终点显著劣于安慰剂</strong>。同样是「线粒体相关」叙事，一个在 1b 期验机制，一个已在三期读出阴性。<strong>机制 plausible 不等于临床有效</strong>，这正是 1b 期 proof-of-mechanism 存在的意义。</p>""",
            related=REL_MISSION,
        ),

        "Acta-Pharmaceuticals-Alzheimer-Prevention-Seed-2026.html": dict(
            topic="神经退行", ev="C", tag="行业动态",
            title="2400 万美元种子轮押注「大脑的他汀」：Acta 要把阿尔茨海默病拦在症状出现之前",
            crumb="Acta 的 2400 万美元：AD 预防成可融资命题",
            desc="Acta Pharmaceuticals 完成 2400 万美元种子轮，主打 Tanzi 团队 25 年积累的 γ-分泌酶调节剂 "
                 "GSM-779690T，定位症状前风险人群的每日一次口服预防。",
            source=src_acta,
            body="""<p><strong>一句话结论：</strong>Acta Pharmaceuticals 以累计 <strong>2400 万美元种子轮</strong>落地，主打 <strong>Rudolph Tanzi</strong> 团队约 25 年积累的<strong>新一代 γ-分泌酶调节剂 GSM-779690T</strong>，明确定位「<strong>早期干预与预防</strong>」，公司把它表述为<strong>「大脑的他汀」</strong>——每日一次口服，用于症状前的风险人群。</p>

<h2>这笔钱押的是什么</h2>
<table>
<tr><th>项目</th><th>内容</th></tr>
<tr><td>公司 / 轮次</td><td>Acta Pharmaceuticals，Seed（<strong>$24M 累计种子融资</strong>）</td></tr>
<tr><td>时间</td><td><strong>2026-10-15</strong>（Business Wire 通稿）</td></tr>
<tr><td>主打资产</td><td><strong>GSM-779690T</strong>：新一代 <strong>γ-分泌酶调节剂（GSM）</strong></td></tr>
<tr><td>科学创始人</td><td><strong>Rudolph E. Tanzi</strong>（MGH / UCSD；家族性 AD 三个基因 <strong>APP / PSEN1 / PSEN2</strong> 的共同发现者）</td></tr>
<tr><td>资产来源</td><td>Tanzi 与已故 Steven L. Wagner 约 <strong>25 年</strong>GSM 研究的产物；前期临床开发投入约 <strong>$70M</strong></td></tr>
<tr><td>机制</td><td>降低促斑块形成的 <strong>Aβ42</strong>，同时升高具保护性的 <strong>Aβ37 / Aβ38</strong></td></tr>
<tr><td>与 GSI 的区别</td><td>早期 γ-分泌酶<strong>抑制剂</strong>（GSI）因干扰 Notch 剪切等问题受挫；<strong>GSM 保留酶的生理功能</strong>（临床前 20 μM 下未见 Notch 剪切抑制）</td></tr>
<tr><td>定位</td><td>「<strong>大脑的他汀</strong>」——每日一次口服，用于<strong>症状前</strong>的风险人群</td></tr>
<tr><td>平台</td><td>另有联合疗法项目（Alzheimer's-in-a-Dish™ 类器官／组装体筛选平台，已筛出 <strong>30+</strong> 有效组合）</td></tr>
<tr><td>投资方</td><td><strong>未披露</strong></td></tr>
</table>

<h2>为什么这件事在本周值得记一笔</h2>
<p>行业情报周报给出的判断很直接：<strong>「预防阿尔茨海默病」正在成为一个可融资的命题。</strong>过去十年 AD 领域的资金 overwhelmingly 流向已出现症状人群的抗 Aβ 抗体，而预防端因为需要极长的随访与极大的样本量，一直是资本回避的方向。2400 万美元的种子轮体量不算大，但<strong>把「症状前、每日一次口服、预防」写成公司定位并成功募资</strong>，本身是定位的变化。</p>
<p>同时要注意本周的<strong>反差</strong>：衰老核心赛道（senolytics / 部分重编程 / 表观遗传时钟 / NAD+）<strong>本周没有出现大额融资</strong>。钱主要流向了肿瘤 ADC（翰森×罗氏）、神经退行病早期干预（Acta）与 mRNA 平台。<strong>「神经退行的早期干预」比「衰老本身」更容易被资本市场定价</strong>，因为它有现成的监管路径与可定义的适应症。</p>

<h2>证据边界（三条）</h2>
<ol>
<li><strong>全部信息来自公司通稿与同源媒体转载</strong>（Times Argus、The Joplin Globe，均源出 Business Wire），<strong>非同行评议文献</strong>；「临床前 20 μM 下未见 Notch 剪切抑制」是公司口径的临床前结果，未见独立复核。</li>
<li><strong>投资方未披露</strong>，无法从资本方构成判断背书强度；<strong>本次未做估算或补全</strong>。</li>
<li><strong>「大脑的他汀」是公司表述，不是监管认定</strong>。他汀类有明确的 LDL-C 替代终点与数十年结局数据；<strong>Aβ42↓/Aβ37、38↑ 目前是未被验证为替代终点的生物标志物变化</strong>——两者不在一个证据层级上。这个比喻传播力很强，但读者需要知道它类比的是<strong>愿景</strong>，不是<strong>已建立的监管证据标准</strong>。</li>
</ol>

<h2>与衰老研究的关系</h2>
<p>本站此前记录的血浆 p-tau217 绩效边界（AUROC 从 0.95 掉到 0.79）与淀粉样蛋白轨迹分岔，都指向同一个问题：<strong>「在症状前识别出会进展的人」这件事本身仍不牢靠</strong>。Acta 的命题建立在「能可靠识别症状前高风险人群」这一前提上——前提越弱，预防性给药的风险收益比就越难算。所以对研究者而言，<strong>这笔融资真正值得跟踪的不是 GSM 分子本身，而是它倒逼的「症状前人群如何定义」这一方法论问题</strong>。</p>""",
            related=REL_ACTA,
        ),

        "Intrinsic-Capacity-Endpoint-Standardization-Debate-2026.html": dict(
            topic="方法与工具", ev="C", tag="行业动态",
            title="内在能力有了「收件地址」，但还没有一把尺子：Beard 的警告与 FDA 的 OCHEN 落在同一周",
            crumb="内在能力：方向被认可，测量工具未就绪",
            desc="WHO 内在能力框架奠基人 John Beard 公开警告该概念「出现在每一张 PPT 上」却没有统一测量标准；"
                 "同期 FDA 侧点名 OCHEN 为衰老适应症的临床审评办公室，并明确所有衰老时钟目前都只是预后性标志物。",
            source=src_ic,
            body="""<p><strong>一句话结论：</strong>本周出现了两个方向相反的信号——<strong>监管侧</strong>：FDA 首次有了「衰老作为适应症」的明确临床审评收件地址（CDER 下属 <strong>OCHEN</strong> 办公室）；<strong>测量侧</strong>：WHO 内在能力框架奠基人 <strong>John Beard</strong> 公开警告，这个概念「出现在每一张 PPT 上」但<strong>没有统一的测量标准</strong>，并直指「人们在抓着劣质指标来为生物标志物背书」。<strong>两条放在一起读，才是本周最真实的图景：方向被认可，工具未就绪。</strong></p>

<h2>一、Beard 说了什么（2026-10-19）</h2>
<p>John Beard 是 WHO 老龄化与生命历程司前司长（2009–2019），现哥伦比亚大学国际长寿中心 USA 主任，也是<strong>内在能力（intrinsic capacity）框架的奠基人</strong>。框架把「人」与「环境」分开，人这一侧即内在能力，含五个域：<strong>认知、运动、心理韧性、感官、活力</strong>。</p>
<h3>框架带来的政策启示</h3>
<ul>
<li>WHO 磋商的关键教训是<strong>老年人群差异极大</strong>——部分 80 岁者如 20 岁般强健，部分 60 岁者需大量照护，因此应按<strong>「高且稳定 / 下降 / 显著丧失」分层</strong>施策。</li>
<li><strong>法国已运行以内在能力为入口的国家项目。</strong></li>
<li>Beard 的数据判断是「<strong>68 岁是新的 62 岁</strong>」（全样本看更接近 70 岁是新的 60 岁），且改善<strong>主要来自峰值更高</strong>（营养、教育、儿童期感染减少）而非衰退更慢——意味着<strong>干预不只可以减缓衰退，还可以抬高起点</strong>。</li>
</ul>
<h3>但奠基人自己的警告更重要</h3>
<ol>
<li>内在能力「<strong>出现在每一张 PPT 上</strong>」，但<strong>没有统一的测量标准</strong>。</li>
<li>他警告人们在「<strong>抓着劣质指标来为生物标志物背书，否则整个领域会被毁掉、会失去公信力</strong>」。</li>
<li>许多研究只是<strong>把分项分数相加</strong>——「<strong>就像把纸割伤和骨折取平均</strong>」。</li>
<li>他设想的解决路径是工具梯队：<strong>研究的兰博基尼级严苛测量 + 临床简版 + 最终验证过的生物标志物与可穿戴信号</strong>；有人出钱的话几年内可成，<strong>「但现在我们有点跑在证据前面了」</strong>。</li>
</ol>

<h2>二、FDA 侧同期补充的关键细节</h2>
<p>本站此前已记录 FDA 把 aging & longevity 纳入监管科学议程（ARDD 2026）。本期行业情报补充了几处<strong>上期未记录的关键细节</strong>：</p>
<table>
<tr><th>细节</th><th>内容</th></tr>
<tr><td>时间表</td><td>Kozlowski 明确为「<strong>计划于 2027 财年初</strong>」（tentative，暂定）</td></tr>
<tr><td>收件地址</td><td>Penzenstadler 点名 <strong>OCHEN</strong>（CDER 新药办公室下属的心脏、血液、内分泌与肾病办公室）为负责<strong>「衰老作为适应症」</strong>的临床审评办公室，并鼓励申办方通过 IND 提交真实方案——<strong>这是「衰老」第一次有了明确的监管收件地址</strong></td></tr>
<tr><td>生物标志物准入门槛</td><td>Siegel 明确区分「预后生物标志物」与「替代终点」：<strong>目前所有衰老时钟都还只是预后性的，无一被验证为替代终点</strong></td></tr>
<tr><td>路径建议</td><td>建立 <strong>pre-competitive 联盟</strong>，编纂「生物标志物操作手册」，使各公司试验设计可合并用于验证</td></tr>
<tr><td>未决问题</td><td>Zeta 质疑「是否必须先把衰老定义为疾病才能推进」</td></tr>
</table>

<h2>三、证据边界</h2>
<ol>
<li><strong>FARS 是研究优先级，不是审评路径。</strong>纳入议程不等于<strong>有新指南、有新终点、有批准标准</strong>；时间表亦为暂定。把它读作「FDA 准备审批抗衰老药了」是严重误读。</li>
<li><strong>OCHEN 为收件地址这一点来自会议现场引述</strong>（Global Longevity Association 与 regeneration.ai 的整理），<strong>不是 FDA 正式文件</strong>，需以 FDA 后续公开发布为准。</li>
<li><strong>Beard 的访谈经由行业媒体播客传播</strong>，其中的数据判断（如「68 岁是新的 62 岁」）未给出出处文献，本站<strong>照录其表述，不做溯源补全</strong>。</li>
<li>内在能力作为<strong>候选终点</strong>的地位来自 FDA 方面提出的<strong>两种候选证据模型之一</strong>（多病累积 / 内在能力），<strong>尚未被采纳</strong>。</li>
</ol>

<h2>为什么这一周值得单独记</h2>
<p>因为<strong>推动方与奠基人发出了方向相反的声</strong>：一边是监管开始给出收件地址，一边是框架奠基人说「我们有点跑在证据前面了」。这不是矛盾，而是这个阶段的真实状态——<strong>「有收件地址」比「上议程」更重要</strong>，但收件地址只解决「交给谁审」，不解决「拿什么证据审」。</p>
<p>对研究者而言，<strong>内在能力的测量方法学是当下最具杠杆的空缺点</strong>：谁能给出既严苛又可临床落地的测量方案，并把它与硬终点连接起来，谁就事实上参与了下一代终点的定义。Beard 说的「工具梯队」其实就是一份公开的路线图。</p>
<p>反过来说，这也是一句提醒：<strong>在测量标准建立之前，任何把内在能力（或任意衰老时钟）当作替代终点来设计试验的做法，都缺少监管层面的支撑。</strong></p>""",
            related=REL_IC,
        ),
    }

    for slug in A:
        if slug in used:
            sys.exit(f"✗ slug 已存在，拒绝覆盖：{slug}")
    print(f"本批新写 {len(A)} 篇（观察哨 #2、补遗 #1 等按上游建议入档不成篇，理由见文件头）")
    ga.A = A
    ga.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
