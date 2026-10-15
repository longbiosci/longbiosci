#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_articles_preprint_2026-09.py —— 消化「预印本速递」系列 11 期积压（57 篇）

来源：文献层 dsuxMCSCwEVB 下的 11 个「预印本速递_*.md」产出，
已由上游去重汇总为《预印本速递·统一总表》（本仓库副本：
data/preprint-master-2026-09.json，共 57 条，按 DOI 去重）。

对账结论（本轮已核验）：
  57 条 DOI 在本站 421 条 DOI（data/doi-index.json + news/*.html 全文扫描）
  中命中 0 条 —— 全部为真漏收，无一条已在站内。
  层级：主榜 33 / 观察哨 16 / 补遗 8。

证据等级：全部为预印本（bioRxiv 54 + arXiv q-bio 3），未经同行评审，
按 SOP §4.2 统一标 **C（预印本·观点·机构披露）**。

写作纪律：
  * 只依据总表给出的字段（中文标题 / 一句话贡献 / 核心要点 / 保留意见 / 价值）
    与公开摘要改写，**定量一律沿用卡片原文，不臆测、不外推**；
  * 卡片未给出样本量、效应量处标「待补全文」；
  * 内部链接 slug 全部由 pick_related() 从 data/articles.json（即 news/ 实际
    存在的文件）运行时读取，**不硬编码、不凭记忆**。
"""
import json
import os
import re
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
sys.path.insert(0, os.path.join(ROOT, "scripts"))
# gen_articles 在 import 期就会读 sys.argv[1..3]，这里补满，避免 IndexError
while len(sys.argv) < 2:
    sys.argv.append(ROOT)
while len(sys.argv) < 3:
    sys.argv.append(os.path.join(ROOT, "data/preprint-master-2026-09.json"))
while len(sys.argv) < 4:
    sys.argv.append("2026-10-15")
import gen_articles as ga  # noqa: E402

MASTER = os.path.join(ROOT, "data/preprint-master-2026-09.json")
M = json.load(open(MASTER, encoding="utf-8"))

# ── ITEMS：总表序号 → (slug, 站内 topic, tag, 导语) ────────────────────────
# 序号与 data/preprint-master-2026-09.json 的「序号」字段一一对应（1..57）。
# topic 取值限定为站内 9 个主题页之一；tag 沿用站内已有口径。
ITEMS = [
    (1, "Tau-Astrocyte-Senescence-Neurovascular-Alzheimer-2026.html", "神经退行", "基础研究",
     "tau 研究里，「神经元自己坏掉」一直是默认叙事。这份预印本把镜头挪到了旁边的星形胶质细胞：tau 传进去之后，先衰老、再放 SASP，然后才是神经元受损。"),
    (2, "APOE4-Drosophila-Cognitive-Decline-2026.html", "神经退行", "基础研究",
     "APOE4 是散发性 AD 最强的遗传风险因子，但缺少便宜、快、可规模化的在体模型。这份工作把人源 APOE4 装进果蝇，让「认知随龄衰退」这件事可以在几周内被测量。"),
    (3, "Germline-Removal-Somatic-DNA-Repair-Zebrafish-2026.html", "生命历程", "基础研究",
     "生殖系与体细胞的资源分配，是衰老演化理论的老问题。这份预印本的结论有点反直觉：拿掉生殖系，体细胞不是「躺平」，而是把基因组维护换成了一套更快、更省、更高保真的方案。"),
    (4, "Single-Cell-Isoform-Splicing-Aging-Atlas-2026.html", "方法与工具", "方法学",
     "我们通常把「细胞身份」和「细胞衰老」当成两件事来测。这份 26 组织长读长图谱给出的一条线索是：可变剪接异构体的使用，可能同时编码了这两条轴。"),
    (5, "Heterogeneous-Epigenetic-Mammalian-Mortality-Clock-2026.html", "表观遗传", "计算生物学",
     "表观遗传时钟大多靠回归拟合年龄。这份工作换了个目标：直接拟合死亡率曲线，并把 CpG 的 U 型甲基化轨迹当作跨物种的共同语言。"),
    (6, "Hypothalamus-Aging-X-Linked-Sex-Difference-2026.html", "神经退行", "基础研究",
     "下丘脑是全身衰老的调控枢纽之一，但「雌雄老化路径不同」长期停留在观察层面。这份单核多组学把差异落到了 X 染色体失活中心的重塑上。"),
    (7, "AP1-Lung-Fibrosis-ECM-Program-2026.html", "器官衰老", "基础研究",
     "纤维化常被描述为「修复失控」。这份预印本把它拆成了一个更具体的问题：同一群成纤维细胞里，发育态与纤维化态的细胞外基质程序由 AP-1 借不同元件切换——而且可以往回拨。"),
    (8, "MEG-Resting-State-Network-Aging-2026.html", "神经退行", "研究进展",
     "「老了脑网络就变差」是一个过于粗糙的说法。这份 MEG 工作把分辨率提到了频率维度：老化不是全面衰退，而是网络在不同频段上的重新分配。"),
    (9, "Hippocampus-Memory-Update-Tent5a-Aging-2026.html", "神经退行", "基础研究",
     "老年记忆的麻烦往往不在「记不住」，而在「更新不了」。这份工作把老龄鼠海马在记忆更新时的转录程序和单纯提取作了对比，并锁定了 Tent5a。"),
    (10, "Amyloid-Trajectory-Bifurcation-Normal-Aging-AD-2026.html", "神经退行", "研究进展",
     "淀粉样蛋白阳性并不等于会得 AD——这是领域里最尴尬的事实之一。这份自监督轨迹模型给出的答案是：两条路径在很早期就分岔了。"),
    (11, "Transcranial-Aperiodic-Stimulation-Working-Memory-2026.html", "神经退行", "临床研究",
     "非侵入性脑刺激的争议一直在于「参数凭什么这么设」。这份工作用随机非周期刺激去直接推脑电的非周期活动，把刺激参数和一个可测量的电生理量挂上了钩。"),
    (12, "SenSASP-Senescence-SASP-Gene-Database-2026.html", "方法与工具", "工具方法",
     "衰老与 SASP 基因名单散在四套资源里，ID 体系互不兼容，是做富集分析时最现实的摩擦。这份工作把它们统一到了 Ensembl ID，并补了三层注释。"),
    (13, "Life-History-Fast-Slow-Evolution-Mortality-2026.html", "生命历程", "计算生物学",
     "快慢生活史策略是演化生物学的经典框架，把它和衰老演化理论放到同一个模型里检验，是这份预印本想做的事。"),
    (14, "REDD1-Dexamethasone-Muscle-Atrophy-Mitochondria-ER-2026.html", "器官衰老", "基础研究",
     "糖皮质激素性肌萎缩是临床上最常见的医源性肌肉流失之一。这份工作把 REDD1 摆到了 mTOR 下游、线粒体-内质网接触与神经肌肉接头之间的位置。"),
    (15, "Canine-Immune-Aging-Geroprotector-Early-Life-2026.html", "免疫与炎症", "基础研究",
     "犬类是目前最接近人类的自然衰老大动物模型。这份全生命周期免疫轨迹的价值在于：它测的不只是「老了以后怎样」，而是早年干预留下的印记有多持久。"),
    (16, "In-Vivo-Multiparametric-Mitochondria-Aging-Trajectory-2026.html", "代谢与营养", "方法学",
     "线粒体衰老几乎全部证据来自离体或固定样本。这份工作给出的是活体、多参数、可重复的成像框架——并且发现「线粒体衰老」在不同组织里根本不是同一条轨迹。"),
    (17, "Choroid-Plexus-Calcification-Aging-QSM-2026.html", "神经退行", "研究进展",
     "脉络丛在脑老化里的角色最近被反复提起，但缺少大样本量化。这份三万人 QSM 影像把钙化这件事从「偶尔看到」变成了「可以统计」。"),
    (18, "GIA-AlphaGenome-Germline-Regulated-CpG-Clock-2026.html", "表观遗传", "计算生物学",
     "表观时钟选出来的 CpG，有多少其实是被种系遗传变异定死的？这份工作用 AlphaGenome 去回答这个问题，直接指向时钟的可解释性。"),
    (19, "Microtubule-Lifetime-Stability-Decoupling-Senescence-2026.html", "细胞衰老", "基础研究",
     "细胞骨架在衰老细胞里会发生什么，长期靠免疫荧光定性。这份工作的结论是一个提醒：微管乙酰化不能当作「微管年龄」的读数。"),
    (20, "mTOR-Alzheimer-Cerebrovascular-RNA-Network-2026.html", "神经退行", "基础研究",
     "AD 的血管侧病变常被当成神经病变的背景板。这份预印本把 mTOR 放到了脑血管 RNA 调控网络的破坏者位置上。"),
    (21, "MALDI-TOF-Brain-Energy-Metabolism-AD-Sex-Age-2026.html", "神经退行", "基础研究",
     "脑能量代谢在 AD 里怎么变，取决于你在哪个脑区、什么性别、多大年纪取样。这份成像质谱给的是一张带空间坐标的图，而不是一个平均值。"),
    (22, "Serum-Metabolomics-Physical-Resilience-Trajectory-2026.html", "代谢与营养", "研究进展",
     "「韧性」（resilience）比「衰弱」更难测，因为它描述的是动态能力。这份 28 年随访血清代谢组把中年到老年的韧性轨迹拆成了代谢物特征。"),
    (23, "CD55-CD319-CX3CR1-GZMK-CD8-T-Cell-Gating-2026.html", "免疫与炎症", "方法学",
     "单细胞定义了 GZMK⁺ CD8 T 细胞这个免疫衰老里的关键亚群，但做功能实验时你得先把它分出来。这份工作给的是一套能直接上机的流式门控。"),
    (24, "Deep-Learning-Explainability-Neurocognitive-Aging-2026.html", "神经退行", "研究进展",
     "深度学习预测脑龄已经不稀奇，稀奇的是解释它到底看了什么。这份 615 人工作的结论是：脑龄归因不止默认模式-额顶网络这一条轴。"),
    (25, "Older-Adults-Costly-Information-Search-2026.html", "神经退行", "研究进展",
     "「老年人决策更保守」这个说法，可能把两件事混在了一起。这份工作观察到的是：老年人愿意付出实际代价去换取更多信息。"),
    (26, "Multimodal-Neuroimaging-Coupling-Confound-Test-2026.html", "神经退行", "方法学",
     "多模态影像耦合分析里，年龄既是科学变量也是最强混杂。这份工作给出一个基于 U 统计量的检验，用来判断耦合到底是信号还是协变量的影子。"),
    (27, "Splice-Donor-Disruption-Progerin-Rescue-2026.html", "器官衰老", "基础研究",
     "早衰症的基因编辑路线通常瞄准 LMNA 突变本身。这份工作换了个更巧的切入口：破坏突变型才有的那个隐蔽剪接供体，让 progerin 根本不被生产出来。"),
    (28, "Mitochondria-Cristae-Alpha-KG-KDM-SASP-Model-2026.html", "细胞衰老", "计算生物学",
     "代谢与表观遗传在衰老细胞里怎么互相推动，缺少可检验的机制模型。这份工作建了一个：线粒体嵴重塑 → α-KG 耗竭 → KDM4/6 抑制 → SASP 放大。"),
    (29, "Elexacaftor-Triple-Therapy-Epigenetic-Age-CF-2026.html", "表观遗传", "临床研究",
     "把表观遗传时钟用作药物疗效读数，是领域里诱人但危险的一步。这份 n=8 的先导研究给了个正面信号，也给了个样本量上的清醒剂。"),
    (30, "DNA-Co-methylation-Module-Aging-Dynamics-2026.html", "表观遗传", "研究进展",
     "单个 CpG 随龄漂移大家都熟，CpG 之间的协同关系随龄怎么变则少有人系统刻画。这份 7500 余人全血工作把共甲基化模块分成了随龄稳定与随龄重塑两类。"),
    (31, "Autism-Adult-System-Specific-Epigenetic-Aging-2026.html", "表观遗传", "研究进展",
     "生物年龄是否在某些疾病群体里被系统性改写，是时钟应用里最容易过读的一类问题。这份 n=37 的唾液甲基化工作给出的是「系统特异性差异」，而不是一个总体的加速量。"),
    (32, "Drosophila-DGRP-Organ-System-Decline-Genetics-2026.html", "生命历程", "基础研究",
     "不同器官以不同速率衰退，这已是共识；但衰退速率是否受遗传背景调控、是否与寿命同轨，一直缺少系统数据。这份 DGRP 工作给了一个明确答案。"),
    (33, "Lifespan-Single-Cell-Immune-Metabolic-Transition-2026.html", "免疫与炎症", "基础研究",
     "免疫衰老的分界线画在哪里？这份 0–100 岁、2008 人 PBMC 图谱把转折点定位到了幼儿期，而不是通常以为的中年以后。"),
    (34, "Engineered-Nanosponge-Neuroinflammation-Cognition-2026.html", "免疫与炎症", "基础研究",
     "外周炎症驱动神经炎症、进而损伤认知，这条链条缺一个能打断它的工具。这份工作用的不是抑制剂，而是一个「吸附循环因子」的纳米海绵。"),
    (35, "Single-Cell-Multiomics-QTL-Senescence-HUVEC-2026.html", "细胞衰老", "基础研究",
     "非编码变异在衰老里怎么起作用，通常只能靠 bulk eQTL 间接推断。这份单细胞多组学 QTL 图谱的价值在于：它能看到调控效应随细胞状态而变。"),
    (36, "S1P-USS-High-Muscle-Stem-Cell-Regeneration-2026.html", "器官衰老", "基础研究",
     "肌肉干细胞随龄减少再生能力，通常被归因为细胞自主性衰退。这份工作把一部分原因放回了微环境：一群「衰老样」干细胞分泌的 S1P 竟然是再生所必需的。"),
    (37, "Caloric-Restriction-Brain-RNA-Lipid-Remodeling-2026.html", "代谢与营养", "基础研究",
     "热量限制如何延寿，主流解释集中在营养感应通路。这份工作给出的是另一条：脑内 RNA 加工与皮层脂质组成的年龄依赖性整合重塑。"),
    (38, "YAP-Skin-Wound-Healing-Aging-ICE-Mice-2026.html", "器官衰老", "基础研究",
     "老年人伤口愈合差，通常被讲成「细胞增殖慢」。这份工作把机械信号转导（YAP）拉了进来，并用表观遗传衰老鼠做了复现。"),
    (39, "Sonic-Hedgehog-Intervertebral-Disc-Rejuvenation-2026.html", "器官衰老", "基础研究",
     "椎间盘退变是老年失能的主要原因之一，且几乎无有效干预。这份工作把髓核里的 Shh 信号随龄下降定位为驱动因素，并证明药理激活可部分逆转。"),
    (40, "Lower-Limb-Muscle-Atrophy-Heterogeneity-MRI-2026.html", "器官衰老", "研究进展",
     "肌少症研究和临床评估常用单一肌群代表全身。这份 17 块下肢肌的 MRI 量化说明：肌肉萎缩的异质性大到足以让「代表肌」的选择改变结论。"),
    (41, "IPF-Distal-Lung-Epigenome-Nanopore-2026.html", "器官衰老", "基础研究",
     "IPF 的表观遗传研究多聚焦于成纤维细胞。这份纳米孔全基因组测序把镜头对准了远端肺上皮，并发现甲基化重塑以低甲基化为主。"),
    (42, "Chromatin-Structure-Epigenetic-Memory-Model-2026.html", "表观遗传", "计算生物学",
     "表观遗传漂移为什么会发生，缺少机制性的理论模型。这份工作提出染色质区室逐代融合的预测，并给出了一个可被检验的代数上限。"),
    (43, "Composable-Simulation-Framework-Aging-AI-Agent-2026.html", "方法与工具", "工具方法",
     "衰老研究里各子领域的动力学模型互不兼容，无法拼装检验。Buck 研究所这份框架要解决的就是这件事，并且明确面向 AI 智能体的在硅干预测试。"),
    (44, "Nucleus-Morphology-Computational-Phenomics-Skin-Aging-2026.html", "方法与工具", "工具方法",
     "最便宜的老化读数可能就藏在日常 H&E 切片里。这份工作把核形态做成了 129 维可解释特征，并据此给出了皮肤老化的终生速率轨迹。"),
    (45, "Hair-Follicle-Aging-Mesenchymal-Epithelial-PTN-2026.html", "器官衰老", "基础研究",
     "毛囊衰老和脱发是两回事，临床上却常被混为一谈。这份时空图谱的价值在于它同时给出了两者的机制分野，并锁定了 PTN。"),
    (46, "Oxaliplatin-5FU-LGSOC-Senescence-Like-Arrest-2026.html", "细胞衰老", "基础研究",
     "化疗诱导衰老在肿瘤学里通常被当作治疗获益机制。这份患者来源细胞的研究给了一个不那么乐观的版本：阻滞是可逆的，撤药后增殖能力会回来。"),
    (47, "Brain-Metabolic-Connectivity-Method-Comparison-2026.html", "神经退行", "研究进展",
     "脑代谢连接度有多种算法，但没人系统比较过它们在年龄效应上的分歧。这份工作做了这件事，结论是：方法选择会改变你看到的年龄效应。"),
    (48, "Novelty-Seeking-Exploration-Social-Network-Aging-2026.html", "神经退行", "研究进展",
     "老年探索行为下降常被当作单一的动机衰退。这份 fMRI 工作把它拆成了新奇寻求与目标导向探索两条策略，各自对应不同脑网络与社会结局。"),
    (49, "Heart-Transplant-Donor-Biological-Age-Assimilation-2026.html", "器官衰老", "基础研究",
     "异时移植（heterochronic）实验是衰老领域最有说服力的范式之一，但在人体上极难获得证据。心脏移植提供了一个罕见的自然实验。"),
    (50, "Osteoblast-Senescence-Mitochondrial-Dysfunction-2026.html", "器官衰老", "基础研究",
     "成骨细胞衰老与骨质疏松的关联早有假说，缺一个能稳定维持并可复现的模型。这份工作补上了这一点，并在人原代细胞里做了验证。"),
    (51, "Mitochondrial-Retrograde-Signaling-Metformin-C-elegans-2026.html", "代谢与营养", "基础研究",
     "二甲双胍的抗衰效应被广泛讨论，但它与线粒体损伤位点的关系很少被拆开看。这份线虫工作的结论是：损伤部位不同，长寿通路不同，药物效应甚至可以反转。"),
    (52, "miR-155-210-Lung-Fibrosis-Alveolar-Regeneration-2026.html", "器官衰老", "基础研究",
     "肺纤维化之所以难逆转，一个原因是肺泡上皮失去了可塑性。这份工作把「锁死」可塑性的责任归给了两个随增龄升高的缺氧响应 miRNA。"),
    (53, "Mnemonic-Discrimination-Aging-Alzheimer-Blood-Biomarker-2026.html", "神经退行", "研究进展",
     "行为学测试能不能接上血液标志物，是 AD 早筛链条里最关键也最薄弱的一环。这份工作把情景辨别能力与海马体积、血浆 pTau217 放在了同一个模型里。"),
    (54, "MMAD-Risk-Plasma-Proteomics-Age-Dependent-Disease-2026.html", "方法与工具", "计算生物学",
     "用血浆蛋白组预测远期疾病风险，主流工具是 Cox 模型。这份工作在英国生物银行 3000 蛋白数据上给出了一个替代方案，并检验了精简面板的代价。"),
    (55, "Periodontitis-Microbiome-SASP-Threshold-Model-2026.html", "免疫与炎症", "计算生物学",
     "牙周炎反复发作、难以根治，微生物组解释了一部分，宿主侧的解释长期缺位。这份阈值模型把 SASP 监视程序摆到了「宿主闸门」的位置。"),
    (56, "Candida-Chronological-Lifespan-Virulence-2026.html", "生命历程", "基础研究",
     "时序寿命（chronological lifespan）是比较老年学的经典读数，但在致病真菌里很少被系统测量。这份念珠菌属比较工作补上了这块拼图。"),
    (57, "Physical-Activity-Power-Training-Adaptation-Older-Men-2026.html", "器官衰老", "研究进展",
     "同样 12 周功率训练，老年人适应度差异很大——通常被归因于训练本身。这份工作指出：训练日之外的日常活动波动，可能是被忽略的补偿因素。"),
]

# ── HINTS：每篇的「站内关联提示词」 ────────────────────────────────────────
# pick_related() 用它在 data/articles.json 里检索真实存在的 slug。
# 只用总表自带的关键词标签时，57 篇里 23 篇最佳匹配分为 0（会退化成随便挑两篇），
# 所以这里为每篇补一组站内文章更可能用到的词。
HINTS = {
    1: ["tau", "星形胶质细胞", "阿尔茨海默", "神经退行"],
    2: ["APOE", "阿尔茨海默", "认知", "果蝇"],
    3: ["生殖系", "DNA修复", "突变", "体细胞"],
    4: ["单细胞", "剪接", "转录组", "多组学"],
    5: ["表观遗传时钟", "甲基化", "生物年龄", "死亡率"],
    6: ["下丘脑", "性别", "脑", "炎症"],
    7: ["纤维化", "细胞外基质", "肺", "成纤维"],
    8: ["脑网络", "静息态", "认知", "影像"],
    9: ["海马", "记忆", "认知", "学习"],
    10: ["淀粉样", "阿尔茨海默", "Aβ", "tau"],
    11: ["经颅", "工作记忆", "脑刺激", "认知"],
    12: ["SASP", "衰老细胞", "数据库", "工具"],
    13: ["演化", "生活史", "死亡率", "比较"],
    14: ["肌肉", "肌少症", "萎缩", "mTOR"],
    15: ["犬", "免疫", "雷帕霉素", "geroprotector"],
    16: ["线粒体", "成像", "代谢", "活体"],
    17: ["脉络丛", "钙化", "影像", "脑"],
    18: ["表观遗传时钟", "甲基化", "CpG", "遗传"],
    19: ["微管", "细胞骨架", "衰老细胞", "细胞周期"],
    20: ["mTOR", "阿尔茨海默", "脑血管", "RNA"],
    21: ["能量代谢", "阿尔茨海默", "代谢组", "脑"],
    22: ["代谢组", "衰弱", "韧性", "队列"],
    23: ["T细胞", "免疫", "CD8", "流式"],
    24: ["脑龄", "深度学习", "认知", "影像"],
    25: ["探索", "决策", "认知", "学习"],
    26: ["影像", "混杂", "方法", "脑"],
    27: ["早衰症", "progerin", "LMNA", "剪接"],
    28: ["SASP", "α-酮戊二酸", "代谢", "表观"],
    29: ["表观遗传时钟", "囊性纤维化", "甲基化", "药物"],
    30: ["甲基化", "表观遗传时钟", "CpG", "队列"],
    31: ["表观遗传时钟", "甲基化", "生物年龄", "疾病"],
    32: ["果蝇", "器官", "遗传", "衰退"],
    33: ["免疫", "单细胞", "代谢", "T细胞"],
    34: ["神经炎症", "认知", "炎症", "小胶质"],
    35: ["单细胞", "QTL", "多组学", "内皮"],
    36: ["肌肉", "干细胞", "再生", "肌少症"],
    37: ["热量限制", "RNA", "脂质", "脑"],
    38: ["伤口", "皮肤", "YAP", "再生"],
    39: ["椎间盘", "Shh", "软骨", "再生"],
    40: ["肌肉", "肌少症", "MRI", "萎缩"],
    41: ["纤维化", "肺", "甲基化", "上皮"],
    42: ["染色质", "表观", "甲基化", "模型"],
    43: ["模型", "仿真", "AI", "工具"],
    44: ["形态", "工具", "皮肤", "影像"],
    45: ["毛囊", "干细胞", "皮肤", "再生"],
    46: ["衰老细胞", "化疗", "p53", "细胞周期"],
    47: ["代谢", "脑", "影像", "连接"],
    48: ["探索", "认知", "社会", "脑"],
    49: ["异时", "移植", "表观遗传时钟", "心脏"],
    50: ["骨", "成骨", "骨质疏松", "线粒体"],
    51: ["二甲双胍", "线粒体", "线虫", "药物"],
    52: ["纤维化", "肺", "miRNA", "再生"],
    53: ["阿尔茨海默", "pTau", "记忆", "血检"],
    54: ["蛋白组", "风险", "预测", "队列"],
    55: ["微生物组", "牙周", "炎症", "SASP"],
    56: ["酵母", "时序寿命", "热量限制", "真菌"],
    57: ["运动", "训练", "肌肉", "老年"],
}

BY_NO = {str(x.get("序号", "")).strip(): x for x in M}


def norm_date(s):
    """从「上线日期」混乱字段里取出 YYYY-MM-DD（总表字段格式不统一）。"""
    m = re.search(r"(\d{4}-\d{2}-\d{2})", str(s or ""))
    return m.group(1) if m else ""


def split_points(s):
    """把「核心要点」按分号切成要点；单句则整段返回。"""
    parts = [p.strip("；; ").strip() for p in str(s or "").split("；")]
    parts = [p for p in parts if p]
    return parts


def doi_of(x):
    """从「DOI / arXiv ID」字段取出可解析的 DOI 主体。"""
    raw = str(x.get("DOI / arXiv ID", "") or "")
    m = re.search(r"10\.\d{4,9}/[^\s（）()]+", raw)
    if m:
        return m.group(0).rstrip(".,;：:")
    m = re.search(r"arXiv[:\.]?([\d.]+)", raw)
    if m:
        return "10.48550/arXiv." + m.group(1)
    return ""


INDUS = {"行业动态", "产业动态", "公司动态", "监管政策", "政策解读", "行业观察", "产业观察"}


def pick_related(topic, keywords, pool, used, k=2):
    """从 data/articles.json（= news/ 实际存在的文件）里按 topic + 关键词
    重叠挑真实 slug。绝不凭记忆硬编码。

    两级回退：先用同 topic 命中；若同 topic 全部 0 分，再放宽到全站检索，
    避免退化成「随手取该 topic 前两篇」。行业类条目降权但不排除。
    """
    def score(a):
        t = (a.get("title", "") + " " + a.get("desc", "") + " " + a.get("tag", ""))
        s = sum(1 for w in keywords if w and w.lower() in t.lower())
        if a.get("tag") in INDUS:
            s -= 0.5
        return s

    def take(cand):
        out = []
        for a in sorted(cand, key=score, reverse=True)[:k]:
            out.append((a["slug"], a["title"]))
            used.add(a["slug"])
        return out

    intopic = [a for a in pool if a.get("topic") == topic and a.get("slug") not in used]
    if intopic and max(score(a) for a in intopic) > 0:
        return take(intopic)
    allsite = [a for a in pool if a.get("slug") not in used]
    return take(allsite)


def body_of(x, lead):
    title_cn = x.get("标题（中文）", "")
    points = split_points(x.get("核心要点", ""))
    contrib = x.get("一句话贡献", "")
    value = x.get("对我的价值", "")
    limit = x.get("保留意见 / 局限", "")
    plat = x.get("来源平台", "")
    rtype = x.get("研究类型", "")
    online = x.get("上线日期", "")
    issue = x.get("速递期次", "")
    kw = x.get("关键词标签", "")
    authors = x.get("作者", "")
    doi = doi_of(x)

    b = []
    b.append(f"<p>{lead}</p>")
    b.append("<h2>卡片事实</h2>")
    rows = [
        ("来源平台", f"{plat}（预印本，未同行评审）"),
        ("速递期次", issue),
        ("上线日期", online),
        ("研究类型", rtype),
    ]
    if authors and authors != "未列":
        rows.append(("作者", authors))
    else:
        rows.append(("作者 / 通讯单位", "原始速递未列（<strong>待补全文</strong>）"))
    if doi:
        rows.append(("DOI", f'<a href="https://doi.org/{doi}" target="_blank" rel="noopener">{doi}</a>'))
    if kw:
        rows.append(("关键词", " / ".join(w.strip() for w in kw.replace(";", "/").split("/") if w.strip())))
    b.append("<table><thead><tr><th>要素</th><th>内容</th></tr></thead><tbody>")
    b += [f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in rows]
    b.append("</tbody></table>")

    b.append("<h2>这项研究说了什么</h2>")
    if points:
        b.append("<ul>" + "".join(f"<li>{p}</li>" for p in points) + "</ul>")
    elif contrib:
        b.append(f"<p>{contrib}</p>")
    if contrib:
        b.append(f"<blockquote><p>{contrib}</p></blockquote>")

    if value:
        b.append("<h2>为什么值得看</h2>")
        b.append(f"<p>{value}</p>")

    b.append("<h2>需要保留的意见</h2>")
    b.append("<ul>")
    b.append("<li><strong>预印本，未经同行评审</strong>——结论可能在正式发表时被修改或推翻；本站按<strong>等级 C</strong>记录，不作为实践依据；</li>")
    if limit:
        b.append(f"<li>{limit}</li>")
    b.append("<li>卡片未给出样本量、效应量与统计细节处均标<strong>待补全文</strong>，本文不补充任何总表之外的定量；</li>")
    b.append("</ul>")

    # 全站 C 级提示框沿用统一模板，其中「非原始研究」的表述针对的是观点评论类
    # 文献；本批次全部为预印本（原始研究报告，只是未经同行评审），必须澄清，
    # 否则等于把原始研究错标成观点文章。
    b.append("<h2>关于本文的 C 级标注</h2>")
    b.append(
        f"<p>本站 C 级覆盖三类内容：「预印本 / 观点评论 / 机构披露」。本文属于<strong>第一类——预印本</strong>："
        f"它是发表在 {plat} 上的一份<strong>原始研究报告</strong>（{rtype}），只是<strong>尚未通过同行评审</strong>，"
        f"并非观点或评论文章。文末提示框沿用全站统一模板，其中「非原始研究」一句<strong>不适用于本文</strong>，特此说明。</p>")
    b.append(
        "<p>本文内容依据「预印本速递」统一总表与预印本平台公开摘要撰写；"
        "付费墙与未获取全文之处一律标注<strong>待补全文</strong>，<strong>未做任何数值推算补全</strong>。</p>")
    return "\n\n".join(b)


def main():
    arts = json.load(open(os.path.join(ROOT, "data/articles.json"), encoding="utf-8"))
    pool = list(arts)
    used = set()

    groups = {}
    for no, slug, topic, tag, lead in ITEMS:
        x = BY_NO[str(no)]
        if not x:
            print(f"!! 总表缺序号 {no}")
            continue
        kws = [w for w in str(x.get("关键词标签", "")).replace(";", " ").split()] + HINTS.get(no, [])
        rel = pick_related(topic, kws, pool, used)
        doi = doi_of(x)
        src_bits = [f'{x.get("来源平台", "")} 预印本（未同行评审）']
        if doi:
            src_bits.append(
                f'DOI <a href="https://doi.org/{doi}" target="_blank" rel="noopener">{doi}</a>')
        src_bits.append("来源=文献层「预印本速递」统一总表")
        src_bits.append("交叉判定=C（预印本·观点·机构披露）· <strong>待补全文</strong>")
        groups.setdefault(x.get("速递期次", ""), {})[slug] = dict(
            topic=topic, ev="C", tag=tag,
            title=x.get("标题（中文）", ""),
            crumb=f'{x.get("来源平台", "")} · {x.get("研究类型", "")} · {x.get("速递期次", "")} 期速递',
            desc=(f'{x.get("一句话贡献", "")}。来自 {x.get("来源平台", "")} 预印本'
                  f'（{norm_date(x.get("上线日期", "")) or x.get("上线日期", "")}），'
                  f'证据等级 C——未同行评审，本站按线索记录，不下结论。'),
            source=" · ".join(src_bits),
            body=body_of(x, lead),
            related=rel,
        )

    total = 0
    for issue in sorted(groups):
        ga.A.clear()
        ga.A.update(groups[issue])
        ga.DATE = issue if re.match(r"^\d{4}-\d{2}-\d{2}$", issue) else "2026-10-15"
        print(f"── 期次 {issue} → date={ga.DATE}，{len(groups[issue])} 篇")
        ga.main()
        total += len(groups[issue])
        # 重新加载，让下一组的 related 能感知刚写入的文章
        arts[:] = json.load(open(os.path.join(ROOT, "data/articles.json"), encoding="utf-8"))
        pool[:] = arts
    print(f"合计提交 {total} 篇（证据等级全部为 C）")


if __name__ == "__main__":
    main()
