#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_articles_intake_2026-10-20.py —— 内容摄入第 17 批（2026-10-20 巡检）

事实源（全部经 file_download + stat -c%s 实测，非 dir_list 缓存）
────────────────────────────────────────────────────────────────
| file_id | 产出 | 实测字节 |
|---|---|---|
| dNEaHVTmNPMT | 文献层《预印本速递_2026-10-20》 | 50,017 B |
| dfVynsAFVVFd | 文献层《预印本流水线_升级与运行纪要_2026-10-18_B方案》 | 5,313 B |
| dXzxgtkeYPXT | 元层《月度研究热点综述_2026-10》v2 修订版 | 41,249 B |

⚠️ dXzxgtkeYPXT 的 dir_list 缓存 size=20322 B 是**陈旧值**（10-15 版）。
   10-20 04:34 任务 7762988 重跑并覆盖为 v2 修订版，实测 41,249 B，
   近乎翻倍。故本轮对它**重新硬核验**（游标虽已 done，但内容已实质更新）。

查重结论（四路查重 + 高特异词硬核验）
──────────────────────────────────
harvest.py 对 3 份产出抽 39 条候选，**37 条 confidence=none**。
按硬规则 3（confidence=none ≠ 漏收），逐条用 **DOI 尾号 + 高特异词**在 news/ 原文硬核验：

| 条目 | DOI 尾号 | 站内命中 | 结论 |
|---|---|---|---|
| 主榜#1 PhenoAge×癌症 | 26365671 | **0** | 真漏收 → 成篇 |
| 主榜#2 ML 预测延寿化合物 | 759743 | **0** | 真漏收 → 成篇 |
| 观察哨#1 STING 缺失延寿 | 759663 | **0** | 真漏收 → 成篇（C 级线索） |
| 月度TOP3 LOY→AMD | PMID 42894102 / acel.70775 | **0** | 真漏收 → 成篇 |
| 月度TOP3 CR 降体细胞突变 | cell.2026.08.013 | **1 篇** | **已收**（2026-10-15 消化）→ 不重复 |
| 月度TOP4.2 雷帕霉素 HFpEF | mayocp.2026.09.006 | **1 篇** | **已收**（Rapamycin-HFpEF-Frailty-…）→ 不重复 |
|月度TOP4.1 NOPARK| jama.2026.18828 | **1 篇** | **已收**（10-18 交叉周报）→ 不重复 |

泛词陷阱已排除：`PhenoAge` 站内 24 篇、`STING` 61 篇、`rapamycin` 18 篇、`HFpEF` 5 篇 —— 这些只能证明「同主题文章多」，不能证明同一研究已收录；真正的判据是 DOI 尾号与 PMID，均为 0。

一手核验（本轮新增动作）
──────────────────────
对月度综述 v2 引用的关键条目，用 NCBI E-utilities 拉取 **PubMed 官方摘要原文**逐项核验：
PMID 42894102（LOY→AMD，*Aging Cell*）摘要定量齐全；
PMID 42856689（CHIP→衰弱，medRxiv）摘要可取；
PMID 42880230（SMaHT，*Cell* Preview）摘要极短；
PMID 42716011（CR 降突变，*Cell*）已收，仅作背景链接。
PMID 42759606（雷帕霉素 HFpEF）PubMed 与 Europe PMC **均无摘要**（online ahead of print）→ 该试验定量无法一手核验，因站内已有专稿，本轮不重复写。

纪律
────
· 预印本篇一律「只依据官方摘要」+ 上游已下载 PDF 摘录的全文要点，摘要未给处标「待补全文」。
· 定量不臆测；付费墙/未获取内容标「待补全文」。
· 内部链接 slug 全部经 news/ 目录实际存在性校验（脚本启动即校验，不存在直接退出）。
"""
import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATE = "2026-10-20"

# ── 内部链接（2026-10-20 实查 news/ 目录后复制，脚本会二次校验）──
REL_PHENOAGE = [
    ("Vegan-Diet-PhenoAge-Inflammatory-Pathways-RCT-2026.html",
     "纯素饮食 1 个月：PhenoAge 逆转 1.7 岁"),
    ("To-Trust-Epigenetic-Clocks-Avoiding-AgingCell-2026.html",
     "要相信表观遗传时钟，先避开这些坑"),
    ("LivAge-An-Online-Aging-Clock-AgingCell-2026.html",
     "LivAge：给小鼠做一个开箱即用的转录组时钟"),
    ("Cell-Type-Senescence-Signatures-Blood-Aging-Clocks-2026.html",
     "血液中的细胞类型衰老特征"),
]
REL_ML = [
    ("DeepStrataAge-Interpretable-Aging-Clock.html",
     "DeepStrataAge：可解释的衰老时钟"),
    ("Composable-Simulation-Framework-Aging-AI-Agent-2026.html",
     "衰老研究的 AI Agent 组合式模拟框架"),
    ("Deep-Learning-Explainability-Neurocognitive-Aging-2026.html",
     "深度学习可解释性在神经认知衰老中的应用"),
]
REL_STING = [
    ("CCND1-CDK6-cGAS-STING-SASP-Palbociclib-NatureAging-2026.html",
     "衰老细胞里反常上调的 CDK6：palbociclib 重定位"),
    ("cGAS-Deficient-Premature-Aging-LINE1-Inflammation-2026.html",
     "cGAS 缺陷的早老表型与 LINE1 炎症"),
    ("CK2alpha-LMNA-STING-Systemic-Aging-Nat-Comms-2026.html",
     "CK2α–LMNA–STING 轴与系统性衰老"),
    ("Lung-Fibroblasts-Drive-Inflammaging.html",
     "肺成纤维细胞驱动炎症衰老"),
]
REL_LOY = [
    ("Caloric-Restriction-Somatic-Mutation-Genome-Integrity-Cell-2026.html",
     "热量限制降低小鼠全基因组体细胞突变"),
    ("DREAM-Complex-Somatic-Mutation-Lifespan-NatureAging-2026.html",
     "DREAM 复合体：连接体细胞突变与寿命"),
    ("Germline-Removal-Somatic-DNA-Repair-Zebrafish-2026.html",
     "去除生殖系重编程体细胞 DNA 修复"),
]


def notice(ev):
    """本批统一的证据分级框。

    ⚠️ 分级口径更正（2026-10-20，同一批次的自我更正）
    ----------------------------------------------
    本批初稿一度按「数据类型」分级（有人体数据就 A、非人体就 B），把 PhenoAge 那篇
    medRxiv 预印本标成了 A、把 ML 那篇 bioRxiv 预印本标成了 B。这与 about/ 公开的
    站点约定不符 —— 那里白纸黑字写着：
        A = 同行评议人体研究 / B = 同行评议临床前研究 / C = 预印本（未经同行评议）
    公开承诺优先于内部口径：凡是预印本，一律 C。两篇已在 HTML 内就地更正并保留
    更正说明条款（见 about/ 的「发现错误就公开更正」承诺），这里同步改 C 以保证
    重新生成时不会回退。教训：产证据分级前应先用 lg('about/') 核对站点公开图例。

    来源口径的差异（预印本摘要 vs PubMed 官方摘要）写在**每篇 body 自己的 notice-box** 里，
    因为 gen_articles.py 只以 notice(ev) 单参数调用，无法按篇区分。
    """
    t = {"A": "A 级（同行评议人体研究）",
         "B": "B 级（同行评议临床前研究）",
         "C": "C 级（预印本：未经同行评议，结论可能随审稿改变）"}[ev]
    return (f'<div class="notice-box">\n'
            f'    <p><span class="tier tier-{ev.lower()}">{ev} 级</span>'
            f'<strong>证据分级：{t}</strong></p>\n'
            f'    <p><strong>关于转载与本证据分级的说明：</strong>本篇由 LongBiosci 编辑部依据'
            f'<strong>可核验的一手来源</strong>（预印本官方摘要 / PubMed 官方摘要）整理，'
            f'定量一律照抄原文，<strong>未做任何数值推算补全</strong>；'
            f'凡本站未获取的内容一律标注「待补全文」。</p>\n'
            f'</div>')


def main():
    arts = json.load(open(os.path.join(ROOT, "data/articles.json"), encoding="utf-8"))
    used = {a["slug"] for a in arts}
    all_rel = sum([REL_PHENOAGE, REL_ML, REL_STING, REL_LOY], [])
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
    ga.notice = notice          # 换成「预印本口径 / PubMed 摘要口径」，理由见文件头

    DOI1 = "10.64898/2026.10.15.26365671"
    DOI2 = "10.64898/2026.10.16.759743"
    DOI3 = "10.64898/2026.10.16.759663"
    DOI4 = "10.1111/acel.70775"

    src1 = (f'<em>medRxiv</em>（oncology）· 预印本：Blood-based PhenoAge may reflect disease '
            f'burden rather than biological aging in cancer'
            f' · DOI <a href="https://doi.org/{DOI1}" target="_blank" '
            f'rel="noopener noreferrer">{DOI1}</a>'
            f' · 第一作者 Anish K. Simhal；共同通讯 Guillermo Sapiro（普林斯顿大学）与 '
            f'Joshua S. Mincer（威尔康奈尔医学院）；合作单位含 MSKCC'
            f' · 来源：IMA 知识库《预印本速递》2026-10-20 期（<b>全文 PDF 已获取</b>，793,288 B / 12 页）')

    src2 = (f'<em>bioRxiv</em>（bioinformatics）· 预印本：Predicting Lifespan-Extending Compounds '
            f'Using Supervised Machine Learning'
            f' · DOI <a href="https://doi.org/{DOI2}" target="_blank" '
            f'rel="noopener noreferrer">{DOI2}</a>'
            f' · 第一作者 Divyam D. Acharya；通讯 A. Freitas（帝国理工学院）'
            f' · 来源：IMA 知识库《预印本速递》2026-10-20 期（摘要级，源站 403，全文未获取）')

    src3 = (f'<em>bioRxiv</em>（genetics）· 预印本：STING deficiency extends median lifespan and '
            f'mitigates age-related liver pathology in mice'
            f' · DOI <a href="https://doi.org/{DOI3}" target="_blank" '
            f'rel="noopener noreferrer">{DOI3}</a>'
            f' · 通讯 Vera Gorbunova（罗切斯特大学医学中心）；作者含 A. Seluanov、J. M. Sedivy'
            f' · 来源：IMA 知识库《预印本速递》2026-10-20 期（摘要级，源站 403，全文未获取）')

    src4 = (f'<em>Aging Cell</em> 2026 Oct;25(10):e70775：Systemic Loss of Chromosome Y Associates '
            f'With Age-Related Ophthalmic Diseases in Middle-Aged Men: A Longitudinal Multi-Omic Study'
            f' · DOI <a href="https://doi.org/{DOI4}" target="_blank" '
            f'rel="noopener noreferrer">{DOI4}</a>'
            f' · PMID <a href="https://pubmed.ncbi.nlm.nih.gov/42894102/" target="_blank" '
            f'rel="noopener noreferrer">42894102</a>'
            f' · 通讯 Jian Zhou 等（复旦大学附属眼耳鼻喉科医院）'
            f' · 来源：IMA 知识库《月度研究热点综述》2026 年 10 月 v2 版 + <b>PubMed 官方摘要原文核验</b>')

    A = {
        "PhenoAge-Cancer-Disease-Burden-Not-Biological-Aging-medRxiv-2026.html": dict(
            topic="表观遗传", ev="C", tag="预印本",
            title="PhenoAge 在癌症患者身上读到的可能不是「衰老」，而是肿瘤负荷",
            crumb="3,067 例术前患者的时钟拆解",
            desc="MSKCC 四个癌种 3,067 例根治性切除患者的分析显示，PhenoAge 加速随肿瘤分期升高、其全部预后信号可被 1–2 项常规化验指标复现、换成等权重后信号不减弱——三条证据指向同一个替代解释：它测的是恶性肿瘤的系统性后果。",
            source=src1,
            body="""<p><strong>一句话结论：</strong>在 3,067 例初治手术患者中，血液 PhenoAge 的预后信号<strong>可被 1–2 项常规化验指标复现</strong>、<strong>随病理分期升高</strong>、<strong>换成等权重后不减弱</strong>——这三条同时成立，指向的结论是：在癌症场景下，PhenoAge 更像是<strong>在测量疾病负荷（disease burden），而不是独立的生物学衰老</strong>。</p>

<p class="notice-box"><strong>⚠️ 本文为预印本，未经同行评审，结论可能在正式发表时变更。</strong>本篇标 ①–③ 出自官方摘要，④–⑧ 出自上游已获取的全文 PDF（12 页）摘录；本站未直接持有该 PDF，全文要点按上游摘录转述。</p>

<h2>这项研究想回答什么</h2>
<p>PhenoAge 是近年最常被搬进肿瘤流行病学的「生物年龄」指标之一，常见叙事是：<strong>生物学年龄加速 → 癌症预后变差 / 早发癌症上升</strong>。但这类叙事有一个从未被认真处理的问题——PhenoAge 的九个组分（白蛋白、肌酐、血糖、CRP、淋巴细胞百分比、MCV、RDW、ALP、白细胞计数）几乎全是<strong>急性期蛋白与血常规项目</strong>，而肿瘤本身就会把这些指标搅动起来。</p>
<p>于是有了一个可检验的替代假说：<strong>如果 PhenoAge 在癌症患者身上主要反映的是「恶性肿瘤的系统性后果」，那么它的预后信息应该可以被一两项常规化验复现</strong>，而不是携带某种独立的衰老维度。本文就是把这个假说拆成三个判据来打。</p>

<h2>他们怎么做的</h2>
<ul>
<li><strong>人群</strong>：接受原发肿瘤根治性切除、<strong>术前未接受全身治疗</strong>的患者，共 <strong>3,067 例</strong>。</li>
<li><strong>四个队列</strong>（全文）：<strong>COAD 结肠腺癌 n=577</strong>、<strong>RCC 肾细胞癌 n=1,724</strong>、<strong>LUAD 肺腺癌 n=241</strong>、<strong>TNBC 三阴性乳腺癌 n=525</strong>。</li>
<li><strong>取样时点</strong>（全文）：血液采集于术前<strong>中位 7 / 10 / 14 / 7 天</strong>（依次对应四个队列）。</li>
<li><strong>读出</strong>：PhenoAge 加速（按 SD 计）对<strong>总生存</strong>与<strong>复发特异生存</strong>的 HR；与病理 T 分期的相关；单组分 / 双组分的判别力对照；在临床病理模型上的 C-index 增量。</li>
<li><strong>方法细节</strong>（全文）：CRP 因术前极少检测被省略，改用<strong>八组分版 PhenoAge</strong>（权重在 NHANES III 重估），与九组分版排序 <strong>ρ &gt; 0.96</strong>、C-index 差 <strong>&lt; 0.02</strong>。</li>
</ul>

<h2>核心发现：三条替代解释同时成立</h2>
<h3>① 预后信号可被一两个组分复现</h3>
<p>八个组分中的<strong>一个或两个</strong>（因癌种而异）即可承载全部预后信号。逐癌种看 C-index（全文）：</p>
<table>
<tr><th>队列</th><th>最佳单组分</th><th>其值</th><th>PhenoAge 加速值</th></tr>
<tr><td>COAD</td><td>白蛋白</td><td><strong>0.69</strong></td><td>0.68</td></tr>
<tr><td>RCC</td><td>淋巴细胞百分比</td><td><strong>0.69</strong></td><td>0.71</td></tr>
<tr><td>LUAD</td><td>RDW</td><td><strong>0.70</strong></td><td>—（肌酐 0.67）</td></tr>
<tr><td>TNBC</td><td>无组分达到</td><td>&lt; 0.58</td><td>—</td></tr>
</table>
<p>更关键的是<strong>两两组合</strong>：在每种癌症中，双组分组合与加速值的差距<strong>不超过 0.01</strong>；COAD 的 28 个可能配对中，有 <strong>8 个超过了加速值本身</strong>。</p>

<h3>② 加速值随肿瘤分期走</h3>
<p>PhenoAge 加速<strong>随病理分期升高</strong>。与 T 分期的 Spearman 相关（全文）：</p>
<table>
<tr><th>队列</th><th>ρ</th><th>P</th></tr>
<tr><td>COAD</td><td><strong>0.20</strong></td><td>&lt; 0.001</td></tr>
<tr><td>RCC</td><td><strong>0.14</strong></td><td>&lt; 0.001</td></tr>
<tr><td>LUAD</td><td><strong>0.15</strong></td><td>0.023</td></tr>
<tr><td>TNBC</td><td>0.06</td><td>0.14（不显著）</td></tr>
</table>
<p>而且，<strong>仅仅用 T 分期做校正，就能让 HR 的 log 值下降 10–17%</strong>——换句话说，时钟的一部分预测力是分期信息的代理。</p>

<h3>③ 换成等权重，信号不减弱</h3>
<p>把 PhenoAge 的<strong>一般人群权重替换成等权重</strong>后，预后信号<strong>并未减弱</strong>。如果时钟捕捉的是某种有内在结构的衰老生物学，那么这种权重应该是有意义的；权重可以随便换而信号不倒，说明支撑信号的是<strong>「哪些化验值异常」这件事本身</strong>，而不是特定的加权组合。</p>

<h2>定量结果与证据边界</h2>
<table>
<tr><th>指标（全文）</th><th>COAD</th><th>RCC</th><th>LUAD</th><th>TNBC</th></tr>
<tr><td>总生存 HR（每 +1 SD 加速）</td><td><strong>1.66</strong></td><td><strong>1.57</strong></td><td>1.28</td><td>1.17</td></tr>
<tr><td>复发特异生存 HR</td><td>1.39</td><td>1.39</td><td>1.24</td><td>1.13</td></tr>
<tr><td>加入临床模型后 C-index 增量</td><td colspan="4">0.013–0.023（复发特异生存 0.000–0.017，bootstrap 区间多含 0）</td></tr>
</table>
<p><strong>局限，五条必须一起读：</strong></p>
<ol>
<li><strong>没有独立的生物学衰老参照物。</strong>作者自己在局限里写明：本研究缺乏可与 PhenoAge 对照的独立衰老度量，因此只能说明「大部分预后信息可被癌症相关化验异常复现」，<strong>不能证明 PhenoAge 在癌症中不含任何衰老信号</strong>。</li>
<li><strong>单中心、回顾性、仅限手术患者。</strong>MSKCC 一家机构，且要求术前有完整八项化验面板——LUAD 从 293 例筛到 241 例、TNBC 从 755 例筛到 525 例，<strong>能走到根治性手术的患者本身就是预后较好的一群</strong>，选择偏倚不可避免。</li>
<li><strong>TNBC 是最弱的一环。</strong>加速值与 T 分期无关联（<strong>P=0.14</strong>）、无单组分达 0.58、525 例中 519 例为 T1/T2（分期变异不足）。把结论外推到 TNBC 要格外小心。</li>
<li><strong>省略了 CRP。</strong>八组分版虽经敏感性分析（ρ&gt;0.96、C-index 差&lt;0.02），但 CRP 是<strong>炎症核心项</strong>，在癌症场景下省略它可能恰恰削弱了「衰老」一侧的解释力。</li>
<li><strong>只测了 PhenoAge 一种时钟。</strong>结论不能外推到 GrimAge、DunedinPACE 或甲基化时钟——「不同时钟测的是不同东西」是本文自己反复强调的前提。</li>
</ol>

<h2>为什么值得关注</h2>
<p>这是一篇<strong>拆工具的论文，不是拆生物学的论文</strong>，价值恰恰在这里。三条反证据（可单组分复现、随分期走、等权重不减弱）指向同一个替代解释，给出三个可操作的用途：</p>
<ol>
<li><strong>文献解读层面</strong>：今后看到「PhenoAge 加速预测癌症预后」的论文，可以直接引用本文作为「需排除疾病负荷混淆」的方法学依据。</li>
<li><strong>选题层面</strong>：作者明确呼吁该领域需要「<strong>其信号可与癌症及其治疗的炎症/营养/血液学/器官特异性后果区分开来</strong>」的衰老度量——这本身就是一条选题线索，例如比较不同时钟在同一癌症队列中的判别贡献。</li>
<li><strong>数据层面</strong>：MSKCC 四癌种 3,067 例的术前常规化验 + 长期随访，若要做时钟验证或生物标志物比较，是一个可对照的外部数据集。</li>
</ol>""",
            related=REL_PHENOAGE,
        ),

        "ML-Lifespan-Extending-Compounds-Prediction-bioRxiv-2026.html": dict(
            topic="方法与工具", ev="C", tag="预印本",
            title="用 XGBoost 筛延寿化合物：准确率 80.36% 好看，但 AUPRC 只有 0.52",
            crumb="特征表示同时改变性能与解释",
            desc="帝国理工团队用 STITCH 化合物-蛋白互作特征在 C. elegans 上做延寿化合物分类，XGBoost 最高准确率 80.36%、AUROC 0.7605；但真正该盯的数字是 AUPRC 仅 0.52–0.53，且解释方法会随特征表示而变。",
            source=src2,
            body="""<p><strong>一句话结论：</strong>同一份 STITCH 化合物-蛋白互作数据，换成三种表示方式（连续互作概率 / 固定阈值二元 / 交叉验证内优化阈值二元），<strong>模型的预测性能与「怎么解释模型」会同时改变</strong>——XGBoost 最高准确率 <strong>80.36%</strong>、AUROC <strong>0.7605</strong>，而 AUPRC 只有 <strong>0.52–0.53</strong>。</p>

<p class="notice-box"><strong>⚠️ 本文为预印本，未经同行评审；本次仅依据官方摘要撰写，全文未获取（bioRxiv 源站对本环境返回 HTTP 403），摘要未给出之处标「待补全文」。</strong></p>

<h2>这项研究想回答什么</h2>
<p>延寿化合物的实验筛选成本极高（寿命实验动辄数月），因此「用计算模型先排序、再上湿实验」是长期存在的思路。但这类任务有一个结构性问题：<strong>化合物-蛋白互作数据本身是稀疏且不确定的</strong>——STITCH 给出的是「互作概率」这种预测值。</p>
<p>于是问题被拆成两层：<strong>把互作概率当连续值用、还是卡阈值变成二元？</strong>以及——这个选择会不会连带影响「模型认为哪些蛋白重要」？后者才是真正有用的部分，因为很多人拿这类模型来<strong>反向提名机制靶点</strong>。</p>

<h2>他们怎么做的</h2>
<ul>
<li><strong>特征来源</strong>：<strong>STITCH 数据库</strong>的化合物-蛋白互作。</li>
<li><strong>标签</strong>：*C. elegans* 中的延寿化合物分类；<strong>标签来源库与纳入标准摘要未说明 → 待补全文</strong>。</li>
<li><strong>三种特征表示</strong>：① 连续互作概率；② <strong>固定阈值 0.5</strong> 的二元特征；③ 在<strong>交叉验证内部</strong>选出的优化阈值二元特征。</li>
<li><strong>模型</strong>：Random Forest 与 XGBoost，<strong>分层 10 折交叉验证</strong>。</li>
<li><strong>可解释性</strong>：MDI、SHAP、TreeSHAP、LIME 四种方法，用 <strong>Jaccard 相似度</strong>比较 Top 特征排序。</li>
</ul>

<h2>核心发现</h2>
<table>
<tr><th>模型 / 表示</th><th>准确率</th><th>AUROC</th><th>AUPRC</th></tr>
<tr><td>Random Forest · 固定阈值二元</td><td><strong>78.84%</strong></td><td>0.7391</td><td>0.5202</td></tr>
<tr><td>XGBoost · 优化阈值二元</td><td><strong>80.36%</strong></td><td>—</td><td>—</td></tr>
<tr><td>XGBoost · 连续特征</td><td>—</td><td><strong>0.7605</strong></td><td><strong>0.5332</strong></td></tr>
</table>
<ul>
<li><strong>解释的一致性</strong>：<strong>SHAP 与 TreeSHAP 一致性最强</strong>，在三种 XGBoost 表示下给出<strong>完全相同的前 10 蛋白特征集</strong>；MDI 与 LIME 则未必如此。</li>
<li><strong>作者的落点</strong>：应当<strong>把分类指标与可解释性放在一起评估</strong>，而不是只看准确率。</li>
</ul>

<h2>证据边界与必须保留的怀疑</h2>
<ol>
<li><strong>AUPRC 0.52–0.53 才是本报告最关键的数字。</strong>准确率 80% 好看，但<strong>正负样本若不平衡，准确率会被多数类撑起来</strong>；AUPRC 接近随机线的水平说明「Top-N 候选里真阳性的比例有限」。摘要<strong>未给正负样本数量与比例 → 待补全文</strong>。</li>
<li><strong>只在 *C. elegans* 上训练与验证</strong>，无酵母 / 果蝇 / 小鼠的独立外推测试 → 迁移到哺乳动物延寿筛选的能力未知。</li>
<li><strong>STITCH 偏向被研究充分的化合物</strong>，对全新骨架泛化能力存疑；且互作概率本身是<strong>预测值而非实测</strong>，误差会传导进模型。</li>
<li><strong>无湿实验验证</strong>：摘要未报告任何新预测的化合物被实验证实延长寿命。</li>
</ol>

<h2>为什么值得关注</h2>
<p>这篇的定位是「<strong>方法与基线的校准器</strong>」，不是「新靶点发现者」。三点价值：</p>
<ol>
<li><strong>给出了可对照的基线数字</strong>（RF 78.84% / AUROC 0.7391；XGBoost 80.36% / AUROC 0.7605 / AUPRC 0.5332）。自建模型时可以直接比照这道线，判断特征工程是不是真有增益。</li>
<li><strong>「特征表示改变解释」这个发现比性能数字更有用</strong>。SHAP/TreeSHAP 在三种表示下给出相同的 Top-10，而 MDI/LIME 未必——提示在延寿化合物这类小样本任务里，<strong>解释方法本身的稳定性需要单独验证</strong>，否则「模型挑出的候选蛋白」可能只是表示方式的产物。</li>
<li><strong>可接手的改进方向</strong>：把「化合物-蛋白互作」特征换成「<strong>化合物-衰老通路</strong>」特征，性能上限会不会更高？这是一个能直接上手的对照实验。</li>
</ol>""",
            related=REL_ML,
        ),

        "STING-Deficiency-Extends-Median-Lifespan-Mice-bioRxiv-2026.html": dict(
            topic="免疫与炎症", ev="C", tag="预印本",
            title="STING 缺失延长小鼠中位寿命并缓解肝脏老化，但定量全部待补",
            crumb="Gorbunova / Seluanov 组的炎症-寿命因果链",
            desc="cGAS-STING 先天免疫通路的核心接头蛋白被遗传敲除后，小鼠中位寿命延长、对年龄相关肝脏衰退显著抵抗。这条把「慢性炎症驱动衰老」从相关性推向因果的证据，目前只能按线索记录——摘要未给任何可引用定量，且源站封锁导致全文不可得。",
            source=src3,
            body="""<p><strong>一句话结论：</strong>遗传性敲除 <strong>STING</strong>（cGAS-STING 先天免疫通路的核心接头蛋白）<strong>延长小鼠中位寿命</strong>，并伴随对<strong>年龄相关肝脏衰退的显著抵抗</strong>——作者据此认为 STING 是延长健康寿命的有前景靶点。</p>

<p class="notice-box"><strong>⚠️ 这是 C 级线索，不是证据。</strong>官方摘要<strong>仅 478 字符，未给出任何可引用定量</strong>：无样本量、无寿命延长百分比或月数、无 p 值、无肝脏指标数值；同时 <strong>bioRxiv 源站对本环境返回 HTTP 403，全文 PDF 不可得</strong>。以下每条结论都需等全文才能转成证据。</p>

<h2>为什么这条必须在看不清的时候也记一笔</h2>
<p>「慢性炎症驱动衰老」这句话被引用到几乎失去信息量，但真正能落地的因果检验其实很少：多数证据是<strong>相关性</strong>（老年人炎症因子高）或<strong>间接干预</strong>（抗炎药改善某器官指标）。而本文做的是最直接的一种：<strong>把通路核心节点从基因层面拿掉，看动物活多久</strong>。</p>
<p>机制链条也恰好串起了衰老标志的上下游——<strong>基因组不稳定 → 胞质 DNA（线粒体损伤、核膜破裂、转座子激活）→ cGAS-STING 感知 → 慢性炎症</strong>。STING 落在这条链的<strong>可药理干预位置</strong>上，而且已有 STING 抑制剂在自身免疫适应症中推进到临床。</p>

<h2>目前能确认的只有三点</h2>
<ol>
<li>cGAS-STING 通路是<strong>慢性炎症的主要驱动因素</strong>；此前已知急性 STING 抑制可减轻神经炎症与组织损伤，但<strong>对长寿的长期影响此前未知</strong>。</li>
<li><strong>STING 的遗传性缺失延长小鼠的中位寿命。</strong></li>
<li>生存获益伴随<strong>对年龄相关肝脏衰退的显著抵抗</strong>。</li>
</ol>

<h2>读之前必须带上的五条限定</h2>
<ol>
<li><strong>用词是「中位寿命」而非「最大寿命」。</strong>两者在衰老研究里含义不同：中位寿命延长可能反映的是<strong>疾病负担下降，而非衰老速率本身变慢</strong>——这需要全文里的<strong>生存曲线形态</strong>来判断，现在没有。</li>
<li><strong>只报告了肝脏</strong>，未报告其他组织；也<strong>未报告健康寿命（healthspan）指标</strong>——尽管结论里用了「healthy lifespan」的说法，措辞与证据之间存在跳跃。</li>
<li><strong>未说明敲除方式</strong>（全身性 vs 条件性）、性别、遗传背景，摘要一概未提。</li>
<li><strong>转化上的硬问题没有被触及</strong>：STING 是<strong>抗病毒免疫的核心</strong>，长期缺失的感染风险是绕不开的安全性议题。</li>
<li><strong>团队背景是加分项也是滤镜</strong>：Gorbunova / Seluanov 组是长寿领域的顶级团队（裸鼹鼠、长寿分子机制），这让结论更值得追，但不替代数据。</li>
</ol>

<h2>与本站其他证据怎么对接</h2>
<p>若本文数据扎实，它会把「抗炎 = 延寿」从流行病学关联提升为<strong>小鼠水平的因果证据</strong>，并直接指向一条 geroprotector 药物开发路径。它同时接入三条既有主线：<strong>senolytics</strong>（清除衰老细胞以降 SASP）、<strong>SASP 抑制</strong>（含本站已记录的 CDK6/cGAS-STING 与 LMNA–CK2α–STING 两条机制）、以及<strong>inflammaging</strong>。反过来，若最终数据只体现中位寿命而非最大寿命延长，那么它更像「降低疾病负荷」，而不是「延缓衰老」——这两种解读对应的干预预期完全不同。</p>
<p><strong>下步动作</strong>：优先补全文。本站将在拿到定量（样本量、寿命延长时间、生存曲线、肝脏组织学与肝功能指标）后，把本页由 C 级线索升级为 B 级证据，并重写 quantitative 部分。</p>""",
            related=REL_STING,
        ),

        "LOSS-of-Chromosome-Y-AMD-UKBiobank-MultiOmic-2026.html": dict(
            topic="生命历程", ev="A", tag="研究进展",
            title="Y 染色体丢失提前 12 年发出信号：22.3 万男性追踪出的「克隆嵌合—免疫—视网膜轴」",
            crumb="223,051 名男性的纵向多组学",
            desc="UK Biobank 223,051 名男性分析显示，造血系统 Y 染色体嵌合缺失独立预测年龄相关性黄斑变性风险，41 个血浆蛋白呈非线性动力学，其中 MMP-12 在诊断前 12 年即显著偏离，CD16+ 单核细胞 LOY 频率最高并经单核计数中介分析支持因果。",
            source=src4,
            body="""<p><strong>一句话结论：</strong>在 UK Biobank 的 <strong>223,051 名男性</strong>中，造血系统的 <strong>Y 染色体嵌合缺失（LOY）</strong>独立预测 <strong>年龄相关性黄斑变性（AMD）</strong>发生风险（<strong>HR = 0.611，95% CI 0.397–0.942</strong>）；风险陡升阈值出现在 <strong>mL RR = −0.17</strong>；<strong>41 个</strong>优先蛋白呈非线性轨迹，其中弹性蛋白降解酶 <strong>MMP-12 在诊断前 12 年即显著偏离</strong>。</p>

<p class="notice-box"><strong>关于本文的文献来源：</strong>本站依据 <strong>PubMed 官方摘要原文（PMID 42894102）</strong>逐项撰写，并经 DOI / 期刊卷期独立核验；分析框架参考 IMA 知识库《月度研究热点综述》2026 年 10 月 v2 版。<strong>论文正式版全文为付费内容，本站未获取</strong>，超出官方摘要的信息一律标注「待补全文」。</p>

<h2>这项研究想回答什么</h2>
<p>LOY 是老年男性造血系统最常见的体细胞突变之一，长期被视为「生物学衰老的一个标记」。但标记 ≠ 原因：它到底是在<strong>伴随</strong>衰老，还是在<strong>驱动</strong>某个具体器官的退化？本文把问题收得非常具体——<strong>LOY 能不能预测一种明确的、与年龄相关的感觉器官疾病（AMD），如果能，中间那条链是什么？</strong></p>

<h2>他们怎么做的</h2>
<ul>
<li><strong>人群</strong>：UK Biobank <strong>223,051 名男性</strong>，纵向设计。</li>
<li><strong>三条组学层</strong>：<strong>Olink 血浆蛋白组</strong>（15 年临床前窗口内的动力学）、<strong>外周血 + 脉络膜组织单细胞 RNA 测序</strong>、LOY 定量（median log R ratio, mLRR）。</li>
<li><strong>统计</strong>：多变量校正的生存模型、限制性立方样条（找风险阈值）、<strong>因果中介分析</strong>、LightGBM 机器学习预测 5 年发病。</li>
</ul>

<h2>核心发现</h2>
<table>
<tr><th>层次</th><th>结果</th></tr>
<tr><td>流行病学</td><td>LOY 独立预测 AMD 发生风险 <strong>HR = 0.611（95% CI 0.397–0.942）</strong></td></tr>
<tr><td>阈值效应</td><td>限制性立方样条识别风险陡升阈值 <strong>mL RR = −0.17</strong></td></tr>
<tr><td>蛋白动力学</td><td>15 年临床前窗口内 <strong>41 个</strong>优先蛋白呈发散的非线性轨迹</td></tr>
<tr><td>最早信号</td><td><strong>MMP-12</strong>（弹性蛋白降解酶）在诊断前 <strong>12 年</strong>即显著偏离</td></tr>
<tr><td>细胞定位</td><td><strong>CD16⁺ 循环单核细胞</strong>与<strong>驻留巨噬细胞</strong>的 LOY 频率最高</td></tr>
<tr><td>转录表型</td><td>Y 缺失髓系细胞呈促炎表型，<strong>IFI30</strong> 与 <strong>CKB</strong> 细胞类型特异性上调</td></tr>
<tr><td>因果链</td><td>中介分析确认<strong>外周单核细胞计数显著中介</strong> LOY 相关退行风险</td></tr>
<tr><td>预测</td><td>LightGBM 用优先蛋白特征预测 5 年发病 <strong>AUC = 0.734</strong></td></tr>
</table>

<h2>为什么这条证据的分量不同于「又一个生物标志物」</h2>
<ol>
<li><strong>规模 + 器官特异性。</strong>22.3 万人量级，且终点是单一器官的明确疾病（AMD），而不是笼统的「全因死亡」——器官特异性因果链比泛化关联更难伪造。</li>
<li><strong>有时间顺序。</strong>蛋白轨迹在临床诊断前 15 年的窗口内展开，MMP-12 提前 12 年偏离，这让「LOY → 免疫细胞改变 → 视网膜退行」在时间上说得通。</li>
<li><strong>有中介分析。</strong>单核细胞计数被确认是显著中介项，把「外周血克隆」和「眼底病变」之间的黑箱撬开了一道口子，而不是停在相关性上。</li>
</ol>

<h2>证据边界</h2>
<ol>
<li><strong>HR = 0.611 的方向表述需以原文为准。</strong>摘要原文即如此表述（保护方向的 HR &lt; 1），本站按原文记录，不做方向性推断；此处的读法差异必须在引用时核对全文。</li>
<li><strong>这是观察性队列（UKB）</strong>，即便有中介分析也仍是统计意义上的因果推断，不等于干预证据。</li>
<li><strong>人群结构限制</strong>：UKB 参与者以英国白人为主，外推到其他族裔需谨慎；<strong>女性无法直接外推</strong>（对象本是 Y 染色体）。</li>
<li><strong>AUC = 0.734 的预测模型未做外部验证</strong>，且 UKB 的健康志愿者偏倚会同时影响 LOY 检出与疾病基线风险 → <strong>待补全文</strong>。</li>
<li><strong>功能推断的层次不同</strong>：蛋白组学是实测，但「髓系细胞促炎表型 → 视网膜损伤」的分子链条是<strong>推断性</strong>的，需要组织层面的直接证据。</li>
</ol>

<h2>放进更大的图景里</h2>
<p>本文是「<strong>体细胞突变从衰老标志物升格为可干预驱动轴</strong>」这条新兴主线的一部分。同期还有三条独立证据在同一方向收敛：SMaHT Network 首次给出<strong>人体全身躯体嵌合基线图谱</strong>（*Cell*，2026-10-15，PMID 42880230），让「正常」第一次可被测量；本站已记录的<strong>热量限制降低小鼠全基因组体细胞突变负荷</strong>（*Cell*，2026-09-09）证明这条轴<strong>可以被干预</strong>；以及一项覆盖 <strong>730,088 人</strong>的 medRxiv 研究（PMID 42856689）显示<strong>克隆性造血（CHIP）与常染色体嵌合改变</strong>与新发衰弱及更快的功能衰退强相关，而 X/Y 嵌合缺失则不然——注意这条对本文中 LOY 的角色给出了重要的<strong>限定</strong>：在<strong>衰弱</strong>这一终点上，LOY 未见同等关联。</p>
<p>把四条放在一起，图景是：<strong>测量基线已经建立、可被干预已经被证明、人群层面的器官特异链条正在陆续出现</strong>，但每条链的终点器官（视网膜、衰弱、血液肿瘤）各不相同，说明克隆嵌合不是一条统一的「衰老开关」，而是一组<strong>组织特异造血–免疫–靶器官轴</strong>。这个判断直接影响后续的跟踪策略：不该期望一种干预在所有终点上都成立。</p>""",
            related=REL_LOY,
        ),
    }

    for slug in A:
        if slug in used:
            sys.exit(f"✗ slug 已存在，拒绝覆盖：{slug}")
    print(f"本批新写 {len(A)} 篇（其中 3 篇来自《预印本速递_2026-10-20》，"
          f"1 篇来自《月度研究热点综述_2026-10》v2 修订版）")
    ga.A = A
    ga.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
