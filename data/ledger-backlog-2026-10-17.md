# 真实未消化 backlog（2026-10-17 台账复核）

## 这份清单怎么来的

`ledger.py audit` 长期报「漏收 170 条」，此前各轮按「中文摘要条目无法与英文原标题匹配」
把它整体归为查重假象。本轮做了**分层复核**，结论是：假象居多，但**不是全部**。

复核方法（三层）：

1. 先筛出**带 DOI** 的漏收条目 —— 有稳定主键，可精确判定（共 63 条）；
2. 再用**标题特征词**（去停用词后的前 3 个英文实词，不足则退化为前 2 个）
   在 `news/*.html` 全文中检索；命中即判定「站内已有、属台账匹配假象」；
3. 剔除上游已明确标注「假阳性 / 口径核对」的条目（这类本就不该成文）。

结果：带 DOI 的 63 条中 **25 条站内已有（假象）**、**31 条站内确实查无**。

> **已知方法缺陷（重要）**：中文标题条目取不到英文特征词，会被自动判为缺失。
> 本清单中的中文条目已用中文关键词人工复核（站内仅有泛泛提及、无对应专题文章），
> 但该方法仍可能残留少量误报 —— **动手消化前请逐条再核一次 DOI**。

## 未消化条目（按产出批次）

### 产出来源：`cards_2026-09-25.md`（13 条）

| 代号 | DOI | 标题 / 要点 |
|---|---|---|
| A11 | `10.1111/acel.70701` | hUC-MSC Secretome Improves Skin Photoaging by Enhancing Mitophagy to Inhibit the |
| A13 | `10.1111/acel.70675` | The Thymic Microenvironment Shapes Age-Related Qualitative Changes in the TCR Re |
| A2 | `10.1111/acel.70716` | Synaptic Mitochondrial Oxidative Stress Contributes to Individual Variability in |
| A8 | `10.1111/acel.70664` | Oxygenaging: A Physiological Framework for Geroscience（Review） |
| A9 | `10.1111/acel.70683` | Network Model to Predict Age-Related Transcriptional Reprogramming |
| G1 | `10.1007/s11357-026-02489-0` | High-intensity interval training in aged female mice preserves physical, cogniti |
| G12 | `10.1007/s11357-026-02464-9` | Hyaluronan deficiency disrupts endothelial glycocalyx integrity and contributes  |
| G14 | `10.1007/s11357-026-02498-z` | The Arlington study of healthy aging（ASHA）cohort profile |
| G2 | `10.1007/s11357-026-02546-8` | Ketone ester supplementation in aged mice produces sex-specific cognitive and me |
| G4 | `10.1007/s11357-026-02523-1` | Apolipoprotein-rich electronegative HDL accelerates vascular aging and atheroscl |
| G5 | `10.1007/s11357-026-02532-0` | The TyrRS cascade: circadian gating of neuronal DNA repair and its collapse in a |
| N11 | `10.1038/s43587-026-01230-y` | The chemical fingerprint of cellular senescence |
| N13 | `10.1038/s43587-026-01189-w` | Turning CDK4/6 inhibitors against the dark side of senescence（News & Views，评述 N3 |

### 产出来源：`cards_2026-10-02.md`（17 条）

| 代号 | DOI | 标题 / 要点 |
|---|---|---|
| A10 | `10.1111/acel.70733` | From Regenerative to Degenerative Niche: Multicellular Crosstalk and Population  |
| A13 | `10.1111/acel.70697` | GHA 转基因鼠首次证明 GH 拮抗延长寿命：雌雄中位与最大寿命均显著延长（最大寿命分别 +186 天 / +265 天），2 岁鼠更不易衰弱、握力更强（尽管肥 |
| A15 | `10.1111/acel.70700` | AAV9 递送腺嘌呤碱基编辑器体内修正 LMNA c.1824C>T：体外近 40% 校正，体内 P3/P14/1 月/4 月给药 6 月龄骨组织校正率约 14 |
| A16 | `10.1111/acel.70693` | 放化疗后清除 p16⁺ 细胞的时机决定疗效：照射后 1 月清除无效，4 月清除显著减轻衰弱、改善神经肌肉/认知、恢复血脑屏障与肝代谢、提高中位生存（雌鼠获益最大 |
| A4 | `10.1111/acel.70734` | Autophagy Flux Is Remodeled Sex- and Cell Type-Specifically During Human Aging… |
| A9 | `10.1111/acel.70735` | Single-Cell Mapping Identifies Aging-Associated Neutrophil Remodeling Across Mul |
| C4 | `10.1016/j.cell.2026.06.035` | CSF clearance through arachnoid fenestrations to olfactory meningeal lymphatics |
| G1 | `10.1007/s11357-026-02362-0` | Study protocol for FAXAge: a randomized, controlled clinical trial of fasting an |
| G13 | `10.1007/s11357-025-02035-4` | Effect of fasting-mimicking diet on markers of autophagy and metabolic health in |
| G2 | `10.1007/s11357-026-02554-8` | Autologous cytokine-induced NK cells as candidate cellular senolytics: evidence, |
| G5 | `10.1007/s11357-026-02429-y` | LINE-1 CpG methylation in canine blood and cortical DNA tracks epigenetic change |
| G6 | `10.1007/s11357-025-02028-3` | Discrimination of normal from slow-aging mice by plasma metabolomic and proteomi |
| G7 | `10.1007/s11357-025-02043-4` | Western Hunter-Gatherer genetic ancestry contributes to human longevity in the I |
| G8 | `10.1007/s11357-025-02019-4` | Ovarian somatic tissue rejuvenates circulating apolipoproteins and promotes cogn |
| G9 | `10.1007/s11357-025-02017-6` | Longevity-driven hepatic transcriptional programs mediate resilience to diet-ind |
| M5 | `10.1016/j.cmet.2026.09.003` | Microbial aldehyde-alcohol dehydrogenase degrades metformin to limit therapeutic |
| N5 | `10.1038/s43587-026-01224-w` | GLP-1 receptor agonism extends median lifespan in mice（研究亮点） |

### 产出来源：`preprint-2026-09-15_recheck.md`（1 条）

| 代号 | DOI | 标题 / 要点 |
|---|---|---|
| S4 | `10.64898/2026.09.08.750089` | Ion modulation restores local synaptic function in APOE4 neuronal networks despi |

## 建议处理顺序

1. 先取回对应批次的卡片原文 —— `.intake/raw/` 当前**没有** `cards_2026-09-25.md` 与
   `cards_2026-10-02.md`，需重新从网盘文献层下载。否则只有 DOI 和标题，
   **不足以成文**：按「禁止编造定量」纪律，不得凭标题杜撰数据与结论。
2. 按 `scripts/README-intake.md` 的正常消化流程逐条成文
   （取摘要 → 证据分级 → 四路查重 → backfill-doi → 管线 → 推送）。
3. 每消化一批后重跑 `ledger.py audit`，观察「已收录 / 漏收」是否同步移动。
