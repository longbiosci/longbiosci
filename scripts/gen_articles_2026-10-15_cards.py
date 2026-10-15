#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_articles_2026-10-15_cards.py —— 内容摄入第 12 批（文献卡片真漏收）

来源与判定
──────────
事实源：data/intake-manifest.tsv（网盘四层全量清单）
游标：  data/intake-cursor.json
本批候选来自两个此前从未被查重覆盖过的产出：

  ① 网站层 网站喂料_2026-10-13/IMA_文献著录_2026-10-13.md（dCbmTQRxOmJF）
     —— 该著录包注明「来源：重点期刊监控·每周五（第 2026-10-09 期）」，
        而文献层 dNTCoBPwiOnt（2026-10-09 深度卡片）size=0。
        即：这份著录包就是那期缺失产出的实质内容，本轮据此补收。
  ② 行业层 行业情报周报_2026-09-16（dOnhQdjKdwmw / dVKsSOJcCMjU）

查重：scripts/harvest.py 四路判定 → 248 条候选中 59 条判「漏收」，
      其中 152 条 confidence=none。按硬规则逐条用高特异关键词回搜
      news/*.html 原文复核，结论：

  · C04（CMA 巨噬细胞清除）与 C18（ChromAgeNet）**站内已有文章，
    但 HTML 与 articles.json 均未记录 DOI** → 假漏收，属 DOI 索引缺口，
    本轮以补 DOI 处理，不重写。
  · 下列 6 条 DOI 与关键词在站内均为 0 命中 → 确认真漏收，本批补写。

纪律（SOP §4.2）：只依据期刊公开摘要与 PubMed 元数据撰写；
定量一律沿用产出原文给出的数字，摘要未给的一律标「待补全文」，不推算、不臆测。
"""
import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATE = "2026-10-15"

sys.argv = ["gen_articles.py", ROOT, "/dev/null", DATE]
_spec = importlib.util.spec_from_file_location(
    "ga", os.path.join(ROOT, "scripts", "gen_articles.py"))
ga = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ga)

A = {}

# ── C02 · Nature Aging · cyclin D1–CDK6 → cGAS–STING → SASP ───────────────
A["CCND1-CDK6-cGAS-STING-SASP-Palbociclib-NatureAging-2026.html"] = dict(
    topic="细胞衰老", ev="B", tag="研究进展",
    title="衰老细胞里「反常上调」的 CDK6：palbociclib 把一条老药重定位成抗衰候选",
    crumb="CCND1/CDK6 与 SASP",
    desc="Sanford Burnham Prebys 团队发现，已停止增殖的衰老细胞中 CCND1/CDK6 反而上调，通过加剧 DNA 损伤、形成胞质染色质片段激活 cGAS–STING 驱动 SASP；临床级 CDK4/6 抑制剂 palbociclib 可降低老年鼠衰弱并改善体能。",
    source=('<a href="https://www.nature.com/nataging/" target="_blank" rel="noopener noreferrer">Nature Aging</a>'
            '（2026，6(9): 1829–1848）· Sanford Burnham Prebys Medical Discovery Institute '
            'Rajesh A 等，通讯 Adams PD · 论文：<em>Inhibiting cyclin D1-CDK6 suppresses '
            'senescence-associated inflammatory gene expression and age-related functional decline</em>'
            ' · DOI <a href="https://doi.org/10.1038/s43587-026-01196-x">10.1038/s43587-026-01196-x</a>'),
    body="""<p>细胞周期蛋白依赖性激酶（CDK）教科书上的角色是「推动细胞增殖」。因此一个长期存在的直觉是：<strong>细胞一旦退出细胞周期，CDK 就该随之沉寂</strong>。这篇 <em>Nature Aging</em> 论文的核心，就是去检验这个直觉——结果是反的。</p>

<h2>发现一：不增殖的衰老细胞里，CCND1/CDK6 反而升高</h2>

<p>衰老细胞的标志是<strong>永久性退出细胞周期</strong>，但作者观察到老年小鼠肝脏的衰老肝细胞中 <strong>Ccnd1（编码 cyclin D1）表达升高</strong>。也就是说，这些细胞虽然不再分裂，驱动分裂的那个分子开关却仍然开着。</p>

<h2>发现二：这条轴怎么接到炎症上</h2>

<p>机制链条被梳理为一条完整的因果链：</p>

<ul>
<li><strong>CCND1/CDK6 上调</strong> → 加剧 <strong>DNA 损伤</strong>累积；</li>
<li>DNA 损伤 → 形成<strong>胞质染色质片段</strong>（chromatin fragments 泄漏到细胞质）；</li>
<li>胞质 DNA → 激活 <strong>cGAS–STING</strong> 通路；</li>
<li>cGAS–STING → 驱动 <strong>SASP</strong>（衰老相关分泌表型）与<strong>干扰素刺激基因（ISG）</strong>表达。</li>
</ul>

<p>这条链把「细胞周期 machinery」与「炎症性衰老」这两块此前相对独立的研究领域接在了一起：<strong>衰老细胞之所以持续放毒（SASP），部分原因是它的细胞周期程序没有真正关干净。</strong></p>

<h2>发现三：已在临床使用多年的 palbociclib 有效</h2>

<p>最具转化含义的一点，是干预手段<strong>不需要新药</strong>。作者用<strong>临床级 CDK4/6 抑制剂 palbociclib</strong>（乳腺癌已上市药物）处理老年小鼠：</p>

<ul>
<li>降低 DNA 损伤与 ISG 表达；</li>
<li><strong>抑制衰弱</strong>并<strong>改善体能表现</strong>。</li>
</ul>

<blockquote><p>这属于典型的<strong>药物重定位（drug repurposing）</strong>：一个已有完整人体安全性数据、已上市多年的药物，被指向一个全新的适应症方向。相比从零开始的新分子，这条路的时间与成本优势非常可观。</p></blockquote>

<h2>与本站已记录研究的对照</h2>

<p>本站此前记录过「打断 CDK4/6–RARα–NF-κB 轴减轻衰老相关炎症」的工作（见延伸阅读），两者都指向 <strong>CDK4/6 是衰老炎症的枢纽</strong>，但落点是不同的下游通路（本条为 DNA 损伤–cGAS–STING，那一条为 RARα–NF-κB）。两条独立证据互相印证，比任何一条单独看都更可靠。</p>

<p>另需注意本站记录的「cGAS 敲除小鼠反而早衰」这一反直觉结果：它说明 <strong>cGAS 不能「全敲」或「全抑制」</strong>，而本条提出的路线是上游<strong>降低进入胞质的 DNA 片段</strong>，而非直接抑制 cGAS 本身——方向上更符合那条风险边界。</p>

<h2>局限：定量与安全性都还是空白</h2>

<ul>
<li>摘要层面<strong>未提供任何可引用定量</strong>——效应量、样本量、性别构成、给药方案与疗程<strong>全部待补全文</strong>。本文因此不给出任何具体数字。</li>
<li><strong>靶点选择性问题未解决</strong>：核心主张是 CDK6–CCND1，而 palbociclib 同时抑制 CDK4 与 CDK6。观察到的获益究竟来自 CDK6 抑制、CDK4 抑制，还是两者，摘要<strong>没有区分</strong>。</li>
<li><strong>长期安全性完全未评估</strong>：CDK4/6 抑制剂的已知剂量限制毒性是<strong>造血抑制</strong>（中性粒细胞减少）。在老年个体中长期给药的风险-收益比，是这条路线绕不过去的问题，而老年人群恰恰最可能已有造血储备下降。</li>
<li>终点是<strong>衰弱与体能</strong>，<strong>不是寿命</strong>——「改善体能」不等于「延长健康寿命」，更不等于延寿。</li>
</ul>
""",
    related=[("Disruption-CDK4-6-RAR--NF--B-axis-attenuates-senescence-associated-inflammation-improves-function.html",
              "打断 CDK4/6–RARα–NF-κB 轴减轻衰老相关炎症并改善功能"),
             ("cGAS-Deficient-Premature-Aging-LINE1-Inflammation-2026.html",
              "反直觉：敲除 cGAS 的小鼠提前衰老——「抑制 cGAS 抗衰」这条主流假设需要重新评估"),
             ("SenSASP-Senescence-SASP-Gene-Database-2026.html",
              "SenSASP：统一的衰老与 SASP 基因多层数据库")],
)

# ── C08 · Cell Metabolism · PD-L2 免疫检查点 ───────────────────────────────
A["PD-L2-Immune-Checkpoint-Senescent-Cells-CellMetab-2026.html"] = dict(
    topic="免疫与炎症", ev="B", tag="研究进展",
    title="衰老细胞也有自己的「PD-L1」：PD-L2 被证实是躲避免疫清除的检查点",
    crumb="PD-L2 与衰老细胞免疫逃逸",
    desc="Cedars-Sinai 先进老年治疗中心（Kirkland 团队）发现 PD-L2 在衰老细胞与衰老过程中上调，是衰老细胞逃避免疫清除的检查点；PD-L2 敲除老年鼠衰老细胞累积更少、胰岛素敏感性与握力更好，抗 PD-L2 治疗可恢复老年野生鼠的胰岛素敏感性。",
    source=('<a href="https://www.cell.com/cell-metabolism/" target="_blank" rel="noopener noreferrer">Cell Metabolism</a>'
            '（在线优先 2026-09-10）· Cedars-Sinai 先进老年治疗中心 Chaib S 等，通讯 Kirkland JL · '
            '论文：<em>Blocking PD-L2 prevents senescent cell accumulation and age-related dysfunction</em>'
            ' · DOI <a href="https://doi.org/10.1016/j.cmet.2026.08.014">10.1016/j.cmet.2026.08.014</a>'),
    body="""<p>肿瘤细胞用 <strong>PD-L1/PD-L2 踩下免疫系统的刹车</strong>，这是过去十年肿瘤免疫学最重要的发现之一。这篇 <em>Cell Metabolism</em> 论文问了一个简单但此前没人系统回答的问题：<strong>衰老细胞会不会用同一招？</strong>答案是会。</p>

<h2>核心发现：PD-L2 是衰老细胞的免疫检查点</h2>

<ul>
<li><strong>PD-L2 表达随衰老上调</strong>，在衰老细胞上尤其明显；</li>
<li>与野生型对照相比，<strong>老年 PD-L2 敲除鼠</strong>的衰老细胞累积更少，<strong>胰岛素敏感性与握力更高</strong>；</li>
<li>更具转化含义的是治疗性验证：<strong>抗 PD-L2 抗体治疗可恢复老年野生鼠的胰岛素敏感性</strong>——即不需要基因敲除，给药也能起效。</li>
</ul>

<blockquote><p>作者把<strong>免疫检查点阻断（ICB）</strong>的逻辑从肿瘤整体搬到了衰老：衰老细胞之所以能在组织里长期赖着不走，部分原因是它借 PD-L2 主动抑制了本该清除它的免疫细胞。</p></blockquote>

<h2>三种清除路线的分工，本条站在哪一端</h2>

<p>本站已记录的衰老细胞干预路线，按机制可以分成三族，本条属于第二族：</p>

<table>
<thead><tr><th>路线</th><th>机制</th><th>本条位置</th></tr></thead>
<tbody>
<tr><td>外源杀伤</td><td>直接用 senolytics 药物诱导衰老细胞凋亡（D+Q、fisetin 等）</td><td>—</td></tr>
<tr><td><strong>增强内源性清除</strong></td><td>修复免疫系统「看不见 / 清不掉」衰老细胞的缺陷</td><td><strong>本条（PD-L2 阻断）</strong></td></tr>
<tr><td>代谢/自噬路线</td><td>改善巨噬细胞等清除细胞的自身功能状态（如 CMA）</td><td>—</td></tr>
</tbody>
</table>

<h2>为什么这条路线值得单独关注</h2>

<p>外源杀伤路线的固有难题是<strong>治疗窗</strong>：衰老细胞并非全然有害，它们在伤口愈合、组织修复中也有生理功能，反复「杀」存在代价。而<strong>解除免疫抑制是恢复一种本来就存在的生理机制</strong>——理论上更接近「让身体自己打扫」，而不是外部投毒。</p>

<p>此外，抗 PD-L2 抗体在肿瘤领域已有大量人体安全性数据与成熟的生产工艺，这一点与本站记录的 palbociclib 重定位逻辑类似：<strong>不需要从零开发分子</strong>。</p>

<h2>局限：风险恰恰也来自「借用肿瘤免疫」</h2>

<ul>
<li><strong>长期免疫相关不良事件（irAE）未评估</strong>。肿瘤 ICB 最棘手的问题就是自身免疫毒性；在老年群体中长期给药的风险-收益比，本文<strong>完全没有数据</strong>——而老年人正是自身免疫与慢性炎症背景最复杂的人群。</li>
<li><strong>与肿瘤风险的双向关系未知</strong>。ICB 在抗衰语境下是「解除抑制」，但解除免疫抑制对<strong>潜在肿瘤克隆</strong>意味着什么，是一个必须回答、目前无人回答的问题。</li>
<li>终点是<strong>功能指标</strong>（胰岛素敏感性、握力）与<strong>衰老细胞负荷</strong>，<strong>未报告寿命或健康期</strong>——功能改善不等于延寿。</li>
<li>摘要层面<strong>未提供可引用定量</strong>：PD-L2 上调幅度、衰老细胞负荷下降幅度、抗体剂量与疗程<strong>均待补全文</strong>。本文不给出任何具体数字。</li>
</ul>
""",
    related=[("CMA-Decline-Macrophage-Senescent-Clearance-NatureAging-2026.html",
              "CMA 衰退让「僵尸细胞」逃过免疫清除：Nature Aging 揭示衰老细胞堆积的双重失效"),
             ("EP2-Antagonism-Senescent-Neutrophil-Clearance-Organ-Aging-2026.html",
              "Science 重磅：EP2 受体拮抗恢复巨噬细胞清除衰老细胞能力，多器官衰老大幅逆转"),
             ("Immorta-SenoMune-AI-Designed-Senolytic-Immune-Therapy-2026.html",
              "AI 设计的多肽 senolytic 免疫疗法：让免疫系统重新学会「认人」")],
)

# ── C15 · Aging Cell · 肝 GHR 敲除加速衰老 ─────────────────────────────────
A["Hepatocyte-GHR-Ablation-Accelerated-Aging-PDK4-AgingCell-2026.html"] = dict(
    topic="代谢与营养", ev="B", tag="研究进展",
    title="反直觉：只在肝脏敲除生长激素受体，小鼠反而衰老得更快",
    crumb="肝脏 GHR 缺失与加速衰老",
    desc="辽宁省基因工程动物模型重点实验室团队发现，肝细胞特异性 GHR 敲除小鼠寿命缩短、认知下降、骨矿化受损、炎症衰老加重；机制是循环 GH 升高介导脂肪–肝串扰，经 STAT5b/PPARγ→Pdk4、Cd36 造成线粒体损伤，而 PDK4 抑制可改善病理。",
    source=('<a href="https://onlinelibrary.wiley.com/journal/14749728" target="_blank" rel="noopener noreferrer">Aging Cell</a>'
            '（2026，25(10): e70741）· 辽宁省基因工程动物模型重点实验室 Yang K 等，通讯 Wu Y · '
            '论文：<em>Hepatocyte Growth Hormone Receptor Ablation Is Associated With Aging Phenotypes '
            'and Hepatic Mitochondrial Dysfunction</em> · DOI '
            '<a href="https://doi.org/10.1111/acel.70741">10.1111/acel.70741</a>'),
    body="""<p>生长激素（GH）轴是衰老研究里最经典的「减一点更长寿」案例之一：<strong>全身性 GH 受体缺失的动物往往更长寿</strong>。于是很自然的外推是——<strong>在肝脏里再减一点，应该也更好</strong>。这篇 <em>Aging Cell</em> 论文的结果是完全相反的。</p>

<h2>结果：肝特异性 GHR 敲除 = 加速衰老</h2>

<p>肝细胞特异性 GHR 敲除小鼠表现出一整套衰老加重表型：</p>

<ul>
<li><strong>寿命缩短</strong>；</li>
<li>衰老标志增强、<strong>代谢应激韧性下降</strong>；</li>
<li><strong>认知下降</strong>、<strong>骨矿化受损</strong>；</li>
<li><strong>炎症衰老加重</strong>；</li>
<li>在高脂饮食背景下，<strong>肝老化与年龄相关肝病进一步加重</strong>。</li>
</ul>

<h2>机制：一条组织间的「串扰」链</h2>

<p>作者把机制梳理成一条跨越脂肪与肝脏的因果链：</p>

<p><strong>肝 GHR 缺失 → 循环 GH 升高 → 脂肪–肝串扰 → 脂肪分解增强 + CD36 依赖的肝脂肪变性 → STAT5b 磷酸化受损 / PPARγ 上调 → Pdk4 与 Cd36 转录升高 → 线粒体损伤 + 异位脂质累积 → 自我放大的恶性循环。</strong></p>

<p>链条末端给出了一个可干预节点：<strong>PDK4 的药理抑制可改善上述病理</strong>。</p>

<blockquote><p>关键含义是<strong>组织特异性方向性</strong>：在这个模型里，<strong>肝脏的 GHR 信号是保护性的</strong>。这与「全身 GH 信号越低越好」的常识判断正好相反。</p></blockquote>

<h2>为什么这个「反直觉」很重要</h2>

<p>它是对一类简化叙事的直接反例。把「GH/IGF-1 轴越低越好」直接翻译成「任何组织里降低 GH 信号都抗衰」，在逻辑上跳过了<strong>组织特异性与代偿</strong>这一步。本条提示：肝脏的 GH 信号缺口会通过循环 GH 升高，<strong>把压力转嫁到脂肪组织，再反弹回肝脏</strong>。</p>

<p>对正在评估各种「降低 GH/IGF-1」策略的人来说，这是一条必须知道的风险边界：<strong>方向对了，不等于靶组织对了。</strong></p>

<h2>局限</h2>

<ul>
<li><strong>全身缺失 vs 肝特异性缺失的表型分裂机制未澄清</strong>——两者结果相反，但为什么，摘要<strong>没有解释</strong>。其他组织是否发生代偿（例如脂肪或肌肉的 GHR 信号上调），是解读这个悖论的关键，目前未知。</li>
<li>摘要<strong>未报告性别与样本量</strong>；GH 轴的性别差异非常显著，缺这一信息会明显限制结论的可解读性。</li>
<li><strong>PDK4 抑制剂的特异性与长期安全性未评估</strong>，「改善病理」的幅度与持续性未知。</li>
<li>摘要层面<strong>未提供可引用定量</strong>：寿命缩短幅度、认知与骨指标变化、PDK4 抑制的效应量<strong>全部待补全文</strong>。本文不给出任何具体数字。</li>
</ul>
""",
    related=[("Methionine-Supplemented-Longevity-Diet-FGF21-Long-2026.html",
              "低蛋白+蛋氨酸补充饮食：揭示延寿且不减肌力的新机制"),
             ("Mitochondria-Cristae-Alpha-KG-KDM-SASP-Model-2026.html",
              "细胞衰老中的代谢-表观耦合：线粒体嵴重塑驱动 SASP"),
             ("Metabolomics-5-Longevity-Interventions-UMHET3-Mice-2026.html",
              "五大延寿干预手段共享代谢特征：代谢组学揭示统一机制")],
)

# ── C16 · Aging Cell · SIRT1 沉默 L1 ───────────────────────────────────────
A["SIRT1-L1-Retrotransposon-Heterochromatin-AgingCell-2026.html"] = dict(
    topic="表观遗传", ev="B", tag="研究进展",
    title="SIRT1 的另一份工作：把 L1 跳跃基因按在异染色质里，按不住就触发衰老",
    crumb="SIRT1 与 L1 逆转座子沉默",
    desc="上海市第一妇婴保健院/同济大学团队发现 SIRT1 富集于 L1 的 5′-UTR，增强 Lamin B1、KAP1 互作并提升 H3K9me3 以沉默 L1 转录；SIRT1 缺失则 L1 去抑制、激活 cGAS–STING 触发细胞衰老，该效应可被已获批抗逆转录药物 3TC 挽救。",
    source=('<a href="https://onlinelibrary.wiley.com/journal/14749728" target="_blank" rel="noopener noreferrer">Aging Cell</a>'
            '（2026，25(9): e70689）· 上海市第一妇婴保健院 / 同济大学 Wang X 等，通讯 Geng A · '
            '论文：<em>SIRT1 Silences L1 Retrotransposons by Stabilizing Heterochromatin-Modifying '
            'Complexes</em> · DOI '
            '<a href="https://doi.org/10.1111/acel.70689">10.1111/acel.70689</a>'),
    body="""<p>SIRT1 是长寿研究领域出镜率最高的分子之一，但它的<strong>具体工作内容</strong>一直有点含糊：「去乙酰化酶」「代谢感受器」「延寿因子」——这些标签都对，却都没说清它在基因组层面到底做了什么。这篇 <em>Aging Cell</em> 论文给了一个相当具体的答案：<strong>它负责按住 L1 逆转座子。</strong></p>

<h2>L1 为什么必须被按住</h2>

<p><strong>LINE1（L1）</strong>是人类基因组里唯一还活跃的自主型逆转座子，约占基因组的 17%。它在年轻细胞里被异染色质牢牢封住；随着年龄增长，这层封印逐渐松动，L1 开始转录、逆转录，产生胞质 DNA——而胞质 DNA 正是 <strong>cGAS–STING</strong> 的激活信号，最终通向<strong>炎症与细胞衰老</strong>。</p>

<h2>发现：SIRT1 是这套封印的维护者</h2>

<ul>
<li><strong>SIRT1 富集于 L1 的 5′-UTR</strong>，且在静息态细胞中富集增加；</li>
<li>它增强 <strong>Lamin B1 与 KAP1</strong> 之间的互作，提高抑制性标记 <strong>H3K9me3</strong>，从而沉默 L1 转录；</li>
<li><strong>SIRT1 缺失</strong>时，Lamin B1–KAP1 互作明显降低、二者在 L1 5′-UTR 的定位减少，L1 转录升高；</li>
<li>L1 去抑制 → 激活 <strong>cGAS–STING</strong> → <strong>触发细胞衰老</strong>。</li>
</ul>

<p>机制链可以概括为：<strong>SIRT1 → 招募 Lamin B1/KAP1 → H3K9me3 升高 → L1 沉默 → 基因组稳定 → 延缓衰老</strong>；缺失时则走 <strong>L1 → cDNA → cGAS–STING → I 型干扰素 → 衰老</strong>。</p>

<h2>最有转化含义的一点：3TC 能救</h2>

<p>作者进一步验证，SIRT1 缺失引发的衰老<strong>可被逆转录酶抑制剂 3TC 挽救</strong>。3TC（拉米夫定）是<strong>已获批多年的抗 HIV 药物</strong>，安全性数据充分。</p>

<blockquote><p>这意味着 L1 抑制不是一个「等待新药」的方向——<strong>现成的、已获批的分子就是可用的工具</strong>。本站此前记录过抗逆转录病毒药物降低健康人生物学年龄的概念验证研究（见延伸阅读），两者在机制上正好互相衔接。</p></blockquote>

<h2>与「cGAS 敲除反而早衰」的关系</h2>

<p>本站记录过一项反直觉结果：<strong>cGAS 敲除小鼠呈现早衰</strong>，机制同样是 LINE1 去抑制。两条研究放在一起看，指向同一个更上层的结论：<strong>真正决定衰老走向的是「L1 有没有被按住」，而不是 cGAS 活性的高低。</strong>cGAS 只是 L1 泄漏的下游读出口；把读出口堵掉，泄漏本身还在，反而失去了核内的看家功能。</p>

<h2>局限</h2>

<ul>
<li><strong>3TC 的挽救仅在细胞层面验证</strong>，<strong>体内效果未报告</strong>——这是本条从「机制好看」到「可能有用」之间最大的缺口。</li>
<li>主要证据来自<strong>细胞系</strong>，缺少在体衰老模型与<strong>寿命数据</strong>。终点是衰老标志，不是寿命。</li>
<li>SIRT1 激活剂（白藜芦醇类等）的<strong>转化争议未被涉及</strong>——「提升 SIRT1 活性」与「SIRT1 正常表达」不是一回事，不能从本条直接推出补充 SIRT1 激活剂有效。</li>
<li>摘要层面<strong>未提供可引用定量</strong>：L1 转录变化幅度、H3K9me3 变化、3TC 挽救的效应量<strong>均待补全文</strong>。本文不给出任何具体数字。</li>
</ul>
""",
    related=[("cGAS-Deficient-Premature-Aging-LINE1-Inflammation-2026.html",
              "反直觉：敲除 cGAS 的小鼠提前衰老——「抑制 cGAS 抗衰」这条主流假设需要重新评估"),
             ("Dog-Epigenetic-Clock-LINE1-Science-2026.html",
              "大狗的表观遗传时钟走得更快：Science 报告 894 只犬 LINE1 跳跃基因去甲基化"),
             ("Antiretroviral-Reduce-Biological-Age-Preprint-2026.html",
              "人类首个概念验证：抗逆转录病毒药物治疗显著降低健康人生物年龄")],
)

# ── C17 · Aging Cell · uPAR GFD-CD3 BiTE ───────────────────────────────────
A["uPAR-GFD-CD3-BiTE-Senolytic-Nonhuman-Primate-AgingCell-2026.html"] = dict(
    topic="细胞衰老", ev="B", tag="研究进展",
    title="给 senolytic 装上「剂量旋钮」：uPAR 靶向 BiTE 在小鼠与食蟹猴类灵长类中清除衰老细胞",
    crumb="uPAR 靶向 BiTE 与 senolytic 剂量可调性",
    desc="为绕开 uPAR CAR-T 的剂量依赖毒性，研究者改用 uPA 生长因子样结构域为靶向头的双特异性 T 细胞衔接器 GFD-CD3 BiTE：高剂量引起肝毒性，而在转氨酶监测下的低剂量可有效清除衰老细胞、缓解小鼠与非人灵长类的年龄相关病理且未见不良反应。",
    source=('<a href="https://onlinelibrary.wiley.com/journal/14749728" target="_blank" rel="noopener noreferrer">Aging Cell</a>'
            '（2026，25(10): e70742）· Deng J 等，通讯 Zhao X · 论文：<em>uPAR-Targeting T Cell Engager '
            'Exerts Senolytic Effects in Mice and Non-Human Primates With Serum Aminotransferase Activity '
            'as a Safety Monitor</em> · DOI '
            '<a href="https://doi.org/10.1111/acel.70742">10.1111/acel.70742</a>'),
    body="""<p>用免疫系统清除衰老细胞（senolytic 免疫疗法）是近几年最活跃的方向之一，其中 <strong>uPAR CAR-T</strong> 曾给出漂亮的临床前结果。但它有一个工程学上的硬伤：<strong>CAR-T 是活细胞制品，打进去之后很难「往回调」</strong>。这篇 <em>Aging Cell</em> 论文针对的正是这一点。</p>

<h2>改了什么：从 CAR-T 换成 BiTE</h2>

<p>作者把靶向头换成 <strong>uPA 的生长因子样结构域（GFD）</strong>，构建<strong>双特异性 T 细胞衔接器 GFD-CD3 BiTE</strong>——一端抓住表达 uPAR 的衰老细胞，另一端抓住 T 细胞的 CD3，把两者拉到一起让 T 细胞执行杀伤。</p>

<p>相比 CAR-T，BiTE 是<strong>一个可滴定的分子药物</strong>，而不是一次性的细胞输注。</p>

<h2>结果：剂量决定毒性，也决定疗效</h2>

<ul>
<li><strong>高剂量</strong>：主要毒性是<strong>肝毒性</strong>，机制是 T 细胞攻击<strong>肝内皮</strong>；</li>
<li><strong>低剂量（在血清转氨酶监测引导下）</strong>：有效清除衰老细胞，缓解<strong>老年小鼠与非人灵长类</strong>的年龄相关病理，且<strong>未见不良反应</strong>。</li>
</ul>

<p>值得注意的是，结论在<strong>小鼠与非人灵长类两个物种</strong>中都成立——这在 senolytic 领域是相当少见的数据密度。</p>

<blockquote><p>论文标题里那句「以血清转氨酶活性作为安全监测」是本条最实质的贡献：<strong>它把一个开放的安全问题，变成了一个可以用常规血检随时读出的门控变量。</strong>这让 senolytic 免疫疗法从「一次性细胞制品」变成了「可滴定、可监测的药物」。</p></blockquote>

<h2>为什么「剂量可调性」是个真问题</h2>

<p>衰老细胞并非全然有害——它们参与伤口愈合、组织修复与某些生理性重塑。一个<strong>无法撤出、无法减量</strong>的干预手段，在长期安全性上先天吃亏。BiTE 的半衰期短、可停药、可减量，这一点在慢性给药场景（抗衰天然是长期用药）中尤其关键。</p>

<h2>局限</h2>

<ul>
<li><strong>治疗窗有多宽未量化</strong>。摘要只说「低剂量有效且未见不良反应」，但<strong>有效剂量与毒性剂量之间隔多远</strong>——这个决定成败的数字<strong>没有给出</strong>。</li>
<li><strong>非人灵长类数据细节缺失</strong>：物种、年龄、样本量、随访时长<strong>全部未报告</strong>。而 NHP 数据恰恰是本条最有力的部分，缺这些信息会显著削弱其说服力。</li>
<li><strong>长期免疫风险未评估</strong>：反复激活 T 细胞带来的免疫记忆、自身免疫风险、以及对正常表达 uPAR 组织的影响，均未在摘要中涉及。</li>
<li><strong>转氨酶作为唯一安全监测指标是否够用存疑</strong>——它主要反映肝细胞损伤，而本条的主要毒性机制是<strong>肝内皮</strong>受攻击。用转氨酶去门控一种内皮损伤，灵敏度是否足够，是个合理的疑问。</li>
<li>摘要层面<strong>未提供可引用定量</strong>，本文不给出任何具体数字。</li>
</ul>
""",
    related=[("Immorta-SenoMune-AI-Designed-Senolytic-Immune-Therapy-2026.html",
              "AI 设计的多肽 senolytic 免疫疗法：让免疫系统重新学会「认人」"),
             ("Senotherapeutics-Fisetin-Derivatives-Phenotypic-Screening-AgingCell-2026.html",
              "表型药物筛选找到新型黄酮类 senotherapeutics：fisetin 衍生物活性更强"),
             ("Targeting-cellular-senescence-dermatology-senolytic-senomorphic-strategies.html",
              "皮肤科中的衰老细胞靶向：senolytic 与 senomorphic 策略（综述）")],
)

# ── 行业层 · Insilico Rentosertib 蛋白质组时钟 ──────────────────────────────
A["Rentosertib-Proteomic-Aging-Clocks-IPF-Nature-Biotech-2026.html"] = dict(
    topic="临床与转化", ev="A", tag="临床进展",
    title="AI 设计的 IPF 新药让 6 个蛋白质组时钟同时变年轻——但最强信号不在最有效的剂量上",
    crumb="Rentosertib 与蛋白质组年龄时钟",
    desc="Insilico Medicine 对 Rentosertib IIa 期做蛋白质组学时钟二次分析：42 例 IPF 患者、2841 种血清蛋白、6 个独立时钟一致显示治疗组预测生物学年龄更年轻；但时钟信号最强的剂量与肺功能改善最大的剂量并不重合，作者明确指出蛋白质组时钟无法单独区分「衰老变慢」与「疾病被治疗」。",
    source=('<a href="https://www.nature.com/natbiotech/" target="_blank" rel="noopener noreferrer">Nature Biotechnology</a>'
            '（2026-09-07）· Insilico Medicine · Rentosertib（ISM001-055 / INS018_055，TNIK 抑制剂）'
            'IIa 期蛋白质组学时钟二次分析 · DOI '
            '<a href="https://doi.org/10.1038/s41587-026-03286-y">10.1038/s41587-026-03286-y</a>'),
    body="""<p>「AI 设计的药物让人变年轻了」——这类标题在长寿领域每隔几个月就会出现一次。这篇 <em>Nature Biotechnology</em> 论文值得认真读的原因，恰恰是<strong>它没有停在那个标题上，而是主动给出了最不利于自己的那组对照</strong>。</p>

<h2>研究做了什么</h2>

<p>这是对 <strong>Rentosertib（ISM001-055 / INS018_055）</strong>——英矽智能用生成式 AI 设计的 TNIK 抑制剂——<strong>IIa 期试验的蛋白质组学二次分析</strong>。规模与做法：</p>

<ul>
<li><strong>42 例 IPF（特发性肺纤维化）患者</strong>，平均年龄 <strong>67.1 岁</strong>；</li>
<li>检测 <strong>2,841 种血清蛋白</strong>；</li>
<li>用 <strong>6 个相互独立的蛋白质组年龄时钟</strong>评估：ProtAge、OrganAge（时序/死亡率两个版本）、PAC、ipfP3GPT、PAOPAC。</li>
</ul>

<h2>结果一：六个时钟方向一致</h2>

<p>六个独立时钟<strong>一致显示治疗组的预测生物学年龄更年轻</strong>。其中：</p>

<ul>
<li><strong>30 mg BID 组</strong>在第 4 周达到峰值，预测生物学年龄<strong>约降低 3–4 年</strong>（单一时钟最高约 6 年）；</li>
<li><strong>60 mg QD 组</strong>的肺功能改善最明显：<strong>FVC +98.4 mL，而安慰剂组为 −20.3 mL</strong>。</li>
</ul>

<p>六个时钟<strong>互相独立却方向一致</strong>，这一点比任何单一时钟的读数都更有分量——它基本排除了「恰好挑到一个喜欢的时钟」这种选择性报告。</p>

<h2>结果二：也是最关键的一点——两个「最优」不重合</h2>

<blockquote><p><strong>时钟信号最强的剂量（30 mg BID）≠ 肺功能改善最大的剂量（60 mg QD）。</strong>作者明确指出：蛋白质组时钟<strong>无法单独区分「衰老变慢」与「疾病被治疗」</strong>。</p></blockquote>

<p>这句话是整个领域最需要被反复引用的一句话。它把生物学年龄时钟的定位说清楚了：</p>

<ul>
<li>时钟读数变年轻，可能是<strong>系统性衰老真的慢了</strong>；</li>
<li>也可能只是<strong>这个器官的病理被压住了</strong>，于是血浆蛋白谱回摆到更像健康人的样子。</li>
</ul>

<p>在 IPF 这种有明确器官病理的疾病里，第二种解释的分量一点也不比第一种轻。</p>

<h2>对监管语境的直接含义</h2>

<p>本站此前记录过 FDA 层面的表态（经二手转述，<strong>一手来源待核实</strong>）：<strong>暂无任何药物获批衰老适应证，且不认可「逆转生物年龄」作为药效评价标准</strong>。本条正好给这个立场提供了实证支撑——<strong>连作者自己都不认为时钟读数可以单独作为疗效证据。</strong></p>

<p>同一期行业情报还记录了 Rentosertib 的 III 期 <strong>GENESIS-IPF-3（NCT07687459）</strong>完成首例受试者给药：52 周、随机双盲安慰剂对照、中国 47 中心 320 例，主要终点是 <strong>52 周 FVC 年下降率</strong>——即<strong>一个传统的器官功能终点，而不是生物学年龄</strong>。这个终点选择本身就说明了时钟在监管路径中的真实位置。</p>

<h2>局限</h2>

<ul>
<li><strong>这是探索性二次分析，不是预设终点</strong>。样本量 42 例，且分组后每组更小。</li>
<li><strong>未报告效应量与统计量</strong>（除本文引用的两组数字外），置信区间与多重比较校正情况<strong>待补全文</strong>。</li>
<li>六个时钟<strong>并非完全独立构建</strong>——它们可能共享训练数据与蛋白特征，一致性存在被高估的可能。</li>
<li>随访窗口偏短（峰值出现在第 4 周），<strong>无法判断时钟读数的持久性</strong>。</li>
<li>本条同时属于<strong>企业主导的研究</strong>（Insilico 为药物开发者），利益关系需在解读时计入。</li>
</ul>
""",
    related=[("Lung-Stem-Cell-Senescence-IPF-Transitional-Cells-2026.html",
              "肺干细胞衰老驱动特发性肺纤维化——过渡细胞状态的致命角色"),
             ("GLP1-Aging-Clocks-ARDD-2026-Interpretation.html",
              "GLP-1 药物能让「衰老时钟」变慢吗？ARDD 2026 上诺和与礼来的数据解读"),
             ("StackAge-Multi-Omics-Aging-Clock-UK-Biobank-2026.html",
              "StackAge：整合 30K 样本的多组学生物年龄时钟")],
)

ga.A = A
if __name__ == "__main__":
    ga.main()
