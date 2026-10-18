# 真实未消化 backlog（2026-10-17 建，2026-10-18 分拣结案）

## 结案摘要（2026-10-18）

| 处置 | 条数 | 说明 |
|---|---:|---|
| **已成篇** | **2** | `acel.70697`（GHR 拮抗延寿）、`s11357-026-02489-0`（HIIT 老年雌鼠） |
| **留档观察**（不做单篇） | 9 | 摘要含 1–7 个定量，但主题重叠 / 体例不适配 / 宜并入专题 |
| **明确不做** | 19 | 摘要零定量（机制一句话 / Review / News & Views / 无摘要） |
| **无法核验** | 1 | 预印本 DOI，PubMed 无记录 |
| 合计 | **31** | 原 31 条，无遗漏、无新增 |

> backlog 到此**关闭**。状态从「31 条悬着」变为「2 条已消化 + 28 条有明确书面结论」。

## 分拣规则（本轮确立，写入纪律）

只有一条硬规则：

> **摘要里没有可引用定量的，不成篇。**

依据是 `/about/` 的溯源承诺：本站每条数字都必须能回到官方摘要原文。
凭标题加一句结论拼出来的稿子，读者无法验收，也不该占用「最新」栏位。
所以本轮**没有**把 31 条做成 31 篇——这正是 2026-10-17 建这份清单时
标注的「只有 DOI 和标题，不足以成文」。

执行方式（可复现）：

1. 31 个 DOI 逐个走 PubMed `"<doi>"[DOI]` 解析 → **30/31 命中**
   （唯一未命中：`10.64898/2026.09.08.750089`，Aging 预印本，PubMed 不收录）；
2. 30 篇摘要用 `efetch` 批量取回；
3. 按定量密度排序（n=、百分数、p 值、mmHg、时长单位、指数记法）；
4. **再按「站内是否缺这一块」二次筛选**——密度高不等于该写。
   最终成篇 2 条，两条都因站内存在**结构性缺口**，而不只是数字多。

---

## 一、已成篇（2 条）

| DOI | PMID | 标题 | 成篇理由 |
|---|---|---|---|
| `10.1111/acel.70697` | 42701998 | Growth Hormone Receptor Antagonism Extends Lifespan | 与站内既有 `acel.70741`（肝特异性 GHR 敲除**加速**衰老）构成同一通路的**相反方向**证据。站内此前只有「敲除变差」一侧，缺「拮抗变好」一侧 |
| `10.1007/s11357-026-02489-0` | 42720846 | HIIT in aged female mice preserves physical, cognitive, cardiovascular function | 站内运动条目多为人群观察，缺一条**终点齐全的严格动物对照**；且补上作者既往只做雄鼠的性别缺口 |

产出：

- `news/GHR-Antagonist-Pegvisomant-Lineage-Extends-Lifespan-AgingCell-2026.html`
- `news/HIIT-Aged-Female-Mice-Multi-Endpoint-GeroScience-2026.html`

生成脚本：`scripts/gen_articles_backlog_2026-10-18.py`（可复跑，已存在则跳过）。
两篇全部定量已逐字对照 PubMed 官方摘要复核（含窄空格 U+2009 与 HTML 实体的原始写法），
摘要未给出的数字一律标注「待补全文」。

---

## 二、留档观察（9 条，不做单篇）

判定标准：摘要**有** 1–7 个定量，但（a）主题与站内已有文章高度重叠，或
（b）属于队列概况 / 试验方案（protocol），本身不是研究结论，或
（c）单篇分量不足以撑起一篇「最新」，更适合将来并入专题/速览。

| DOI | PMID | 定量数 | 标题 | 不做的具体理由 |
|---|---|---:|---|---|
| `10.1007/s11357-026-02523-1` | 42717162 | 7 | Apo(a)-rich electronegative HDL accelerates vascular aging | 数据最完整的未做条目。H5 亚组分 4.0±3.5% vs 2.7±1.0%（p=0.024）、n=131/118，**质量足够成篇**，本轮因批次容量留档。**下一轮优先消化** |
| `10.1111/acel.70700` | 42689491 | 6 | In Vivo Base Editing Rescues Bone Dysplasia in HGPS Mice | 定量充足（体外 ~40%、体内 ~14/22/10/<1%），但与站内早衰症/碱基编辑主题重叠度待核，下一轮先查重再定 |
| `10.1111/acel.70675` | 42625375 | 5 | Thymic Microenvironment Shapes Age-Related TCR Repertoire | 与站内胸腺/免疫衰老条目（`Thymic-Health-Immune-Senescence-Nature-2026-Bernatz.html`）主题相邻，宜并入而非单列 |
| `10.1007/s11357-026-02362-0` | 42373885 | 5 | FAXAge 随机对照试验方案 | **试验方案（protocol）**，无结果数据。按纪律不写成「研究发现」 |
| `10.1007/s11357-025-02028-3` | 41396412 | 5 | Plasma metabolomic/proteomic discrimination of slow-aging mice | 方法学工具类，单篇新闻价值弱；宜并入「方法与工具」专题 |
| `10.1007/s11357-026-02498-z` | 42663798 | 4 | Arlington Study of Healthy Aging (ASHA) cohort profile | **队列概况**，非干预结论 |
| `10.1007/s11357-025-02035-4` | 41372565 | 4 | Fasting-mimicking diet on autophagy and metabolic health | 与站内 FMD / 热量限制主题重叠，需先查重 |
| `10.1007/s11357-025-02043-4` | 41389162 | 3 | Western Hunter-Gatherer ancestry and human longevity | 群体遗传学，与站点「衰老干预」主线偏离，留档备查 |
| `10.1111/acel.70734` | 42802483 | 2 | Autophagy Flux Remodeled Sex- and Cell Type-Specifically in Human Aging | 人体图谱类，2 个定量偏少，宜入专题 |

## 三、明确不做（19 条）

判定标准：**摘要无任何可引用定量**。按本轮硬规则不成篇。

| DOI | PMID | 标题 | 类型 |
|---|---|---|---|
| `10.1111/acel.70701` | 42723546 | hUC-MSC Secretome Improves Skin Photoaging | 机制研究，摘要纯定性 |
| `10.1111/acel.70716` | 42733962 | Synaptic Mitochondrial Oxidative Stress / Individual Variability | 机制研究，纯定性 |
| `10.1111/acel.70664` | 42663406 | Oxygenaging: A Physiological Framework | **Review（框架综述）** |
| `10.1111/acel.70683` | 42631664 | Network Model to Predict Transcriptional Reprogramming | 计算模型，纯定性 |
| `10.1007/s11357-026-02464-9` | 42625099 | Hyaluronan Deficiency Disrupts Endothelial Glycocalyx | 机制研究，纯定性 |
| `10.1038/s43587-026-01230-y` | 42768112 | The Chemical Fingerprint of Cellular Senescence | **摘要为空**（PubMed 未提供） |
| `10.1038/s43587-026-01189-w` | 42624918 | Turning CDK4/6 Inhibitors Against the Dark Side of Senescence | **News & Views（评述）** |
| `10.1111/acel.70733` | 42811797 | From Regenerative to Degenerative Niche | 综述/观点 |
| `10.1111/acel.70693` | 42649478 | Timing-Dependent Clearance of p16⁺ Cells | 机制研究，纯定性 |
| `10.1111/acel.70735` | 42811500 | Single-Cell Mapping of Neutrophil Remodeling | 图谱类，纯定性 |
| `10.1016/j.cell.2026.06.035` | 42480526 | CSF Clearance Through Arachnoid Fenestrations | 解剖/机制，纯定性 |
| `10.1007/s11357-025-02019-4` | 41388182 | Ovarian Somatic Tissue Rejuvenates Apolipoproteins | 纯定性 |
| `10.1016/j.cmet.2026.09.003` | 42810351 | Microbial ADH Degrades Metformin | 机制研究，纯定性 |
| `10.1038/s43587-026-01224-w` | 42693292 | GLP-1 Receptor Agonism Extends Median Lifespan | **研究亮点（Research Highlight）** |
| `10.1007/s11357-026-02546-8` | 42776386 | Ketone Ester in Aged Mice: Sex-Specific Cognitive/Metabolic | 仅 1 个定量 |
| `10.1007/s11357-026-02532-0` | 42749976 | The TyrRS Cascade: Circadian Gating of Neuronal DNA Repair | 仅 1 个定量 |
| `10.1007/s11357-026-02554-8` | 42809069 | Autologous Cytokine-Induced NK Cells as Senolytics | 仅 1 个定量 + 综述性 |
| `10.1007/s11357-026-02429-y` | 42503570 | LINE-1 CpG Methylation in Canine Blood/Cortical DNA | 仅 1 个定量 |
| `10.1007/s11357-025-02017-6` | 41299013 | Longevity-Driven Hepatic Transcriptional Programs | 仅 1 个定量 |

## 四、无法核验（1 条）

| DOI | 标题 | 状态 |
|---|---|---|
| `10.64898/2026.09.08.750089` | Ion modulation restores local synaptic function in APOE4 neuronal networks | **Aging 预印本，PubMed 不收录**。摘要无法从 PubMed 独立取回，按纪律不成篇；如需消化，须直接访问预印本页面并明确标注非同行评议 |

---

## 附：清单的最初来源与方法缺陷（保留原文）

`ledger.py audit` 长期报「漏收 170 条」，此前各轮按「中文摘要条目无法与英文原标题匹配」
把它整体归为查重假象。2026-10-17 做了**分层复核**，结论是：假象居多，但**不是全部**。

复核方法（三层）：

1. 先筛出**带 DOI** 的漏收条目 —— 有稳定主键，可精确判定（共 63 条）；
2. 再用**标题特征词**（去停用词后的前 3 个英文实词，不足则退化为前 2 个）
   在 `news/*.html` 全文中检索；命中即判定「站内已有、属台账匹配假象」；
3. 剔除上游已明确标注「假阳性 / 口径核对」的条目（这类本就不该成文）。

结果：带 DOI 的 63 条中 **25 条站内已有（假象）**、**31 条站内确实查无**。

> **已知方法缺陷（重要）**：中文标题条目取不到英文特征词，会被自动判为缺失。
> 本清单中的中文条目已用中文关键词人工复核（站内仅有泛泛提及、无对应专题文章），
> 但该方法仍可能残留少量误报 —— **动手消化前请逐条再核一次 DOI**。

**2026-10-18 对原「建议处理顺序」的工艺修正**：清单原本写「先取回批次卡片原文，
否则不足以成文，需重新从网盘文献层下载 `cards_2026-09-25.md` / `cards_2026-10-02.md`」。
本轮验证——**不必依赖卡片原文**：PubMed 官方摘要本身就是足以成文的第一手事实源，
且比卡片更可核验（有 DOI、PMID、可逐字复核的摘要原文）。
今后积压分拣直接走 PubMed，不再等卡片，也不再因「卡片不在本地」而把 backlog 拖着。
