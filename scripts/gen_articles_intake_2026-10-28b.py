#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_articles_intake_2026-10-28b.py —— 05:30 班第 16 轮 · 批次 b

消化对象
────────
《行业情报周报_2026-10-28》（2026-W44，周三班，行业层 file_id
`dfCLxqSPNKoU`，实测 **55,044 B**）。

⚠️ 同名两份交付，本批只取 md 版
──────────────────────────────
行业层本轮同名两份《行业情报周报_2026-10-28》：
  · `dfCLxqSPNKoU`（55,044 B）—— **真 md 报告**，四表结构完整，本批消化此份；
  · `dauTkaOpIygl`（50,911 B）—— 实测为 **xlsx（PK zip 头）**，表格版交付，
    正文内容与 md 版同源，不重复成篇（按规则④计入跳过）。
两份均**实际下载核验，字节数均 > 0，非空产出**。

成篇范围（15 篇）
────────────────
§2 投融资 2 条（#1 Ferring×Gameto、#6 XPRIZE Healthspan；#5 Beacon×Snap
并入 §14 监测类）；§3 管线 9 条（#1 Longeveron ⬇、#2 Arrowhead ⬆、
#3 Calico ⬆、#4 Insilico ⬆、#5 NRG ⬆、#6 Immorta ⬆、#7 Carnyx ⬆、
#11 Rubedo 补档、#12 Life Biosciences 补档、#14 Biograph×Caristo）；
行业结构回撤 1 条（Unity 停运 / Turn Bio 资产流失，§3.1 基线 ⬇）；
§5 人才 1 条（NewLimit 临床班底）。
§3 #10 Eos SENOLYTIX 周报自述「午刊已上站，本期引用站内，不重复成稿」——
经 grep 核实站内确有 `Eos-SENOLYTIX-PTC-2105-Late-Life-Survival-SEC-2026.html`，
按规则④跳过并计数。

纪律
────
· 全部定量**照抄周报原文**（周报已逐条给出一手来源 URL），不推算、不补全；
· 周报 §6「待核实/降级」区的条目（瑞初医药 A 轮、Attilio、Estrella）**不成篇**；
· 每篇带规则③时间标签：`数据日期 YYYY-MM-DD · 生成时间 2026-10-28`；
· 证据分级：产业动态一律 **B**（一手官方公告 / 监管机构原文可核验），
  非同行评议研究，正文 notice 明示。
"""
import html
import importlib.util
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATE = "2026-10-28"
GEN_AT = "2026-10-28 03:00"      # 行业情报班（周三 03:00）交付时刻

TAG = "产业动态"
EV = "B"


def lab(dd):
    """规则③时间标签"""
    return (f'<p><em>数据日期 {dd} · 生成时间 {GEN_AT}　｜　'
            f'行业情报周报 2026-W44（任务 7762986，周三 03:00 班）</em></p>')


def src(dd, name, url, extra=""):
    return (f'<em>来源：{html.escape(name)}</em> · <a href="{url}" target="_blank" '
            f'rel="noopener noreferrer">{url[:110]}</a>'
            + (f' · {extra}' if extra else ''))


A = {}


def add(slug, title, topic, dd, desc, body, source):
    A[slug] = dict(topic=topic, ev=EV, tag=TAG, title=title, crumb=title[:28],
                   desc=desc, source=source,
                   body=lab(dd) + "\n" + body, related=[])


# ── §2 #1 · Ferring × Gameto ─────────────────────────────────────────
add("Ferring-Acquires-Gameto-1-38B-Ovarian-Aging-2026.html",
    "Ferring 至多 13.825 亿美元收购 Gameto：卵巢衰老第一次被大药厂定价",
    "器官衰老", "2026-10-27",
    "瑞士 Ferring 于 10-27 签署协议收购 Gameto，交易价值至多 13.825 亿美元；"
    "Gameto 2022 年以 2300 万美元起步、主打「卵巢衰老」，四年后被生殖医学集团收购。",
    """<h2>交易要点</h2>
<ul>
<li><strong>买方 / 卖方</strong>：Ferring Pharmaceuticals（瑞士，私营）× Gameto（美国纽约）</li>
<li><strong>交易价值</strong>：至多 <strong>$1.3825B</strong>（含开发、监管、商业里程碑）；<strong>首付款未披露</strong></li>
<li><strong>标的管线</strong>：Fertilo——<strong>iPSC 来源卵巢支持细胞</strong>，替代颗粒细胞使未成熟卵子在体外成熟（IVM）；管线延伸至卵巢疾病与绝经</li>
<li><strong>科学出身</strong>：技术源自 <strong>George Church 实验室</strong></li>
<li><strong>临床状态</strong>：Fertilo 在美国<strong>仍处研究阶段、未获 FDA 批准</strong>；3 期进行中、计划入组 500 例，对照常规 IVM 培养液，主要终点为 12 周持续妊娠；已在澳洲、阿根廷、秘鲁、墨西哥可及</li>
<li><strong>人物</strong>：Gameto CEO 兼联合创始人 Dina Turner；Ferring 董事会主席兼 CEO Jean-Frédéric Paulsen</li>
</ul>
<h2>为什么这条值得单独记</h2>
<p>资本买的是<strong>近期可变现的适应症</strong>，不是「延缓卵巢时钟」本身。Fertilo 先落在 IVF，
而不是卵巢衰老适应症——这条边界必须在引用时说清楚，否则很容易被读成
「卵巢衰老已被药厂认可为适应症」。</p>
<h2>局限与待核实</h2>
<ul>
<li>官方稿明确「至多 $1.3825B（含里程碑）」，<strong>未披露首付款金额或交割日期</strong>；周报已将其列入 §6 待核实区</li>
<li>Fertilo 的关键注册性 3 期尚未读出，交易价值中的绝大部分为里程碑对价</li>
</ul>""",
    src("2026-10-27", "Ferring 官方新闻稿",
        "https://www.ferring.com/ferring-pharmaceuticals-and-gameto-sign-agreement-for-proposed-acquisition",
        "LT 报道：https://longevity.technology/news/ferring-moves-to-acquire-gameto-in-1-38b-deal/"))

# ── §2 #6 · XPRIZE Healthspan ────────────────────────────────────────
add("XPRIZE-Healthspan-101M-Finalist-Teams-2026.html",
    "XPRIZE Healthspan 1.01 亿美元：10 支终选团队与「1 年能否外推数十年」的硬问题",
    "方法与工具", "2026-10-26",
    "XPRIZE Healthspan 总奖金 1.01 亿美元，10 支终选团队各获 100 万美元无限制资金并保留 IP；"
    "评审主席 Steven Cummings，健康领域执行副总裁 Jamie Justice。",
    """<h2>机制与规模</h2>
<ul>
<li><strong>总奖金</strong>：$101M；10 支终选团队各获 <strong>$100 万无限制资金</strong>并保留 IP</li>
<li><strong>共享基础设施</strong>：中心实验室、生物标志物检测、认知评估，每队另值约 $200~250 万</li>
<li><strong>测量域</strong>：以<strong>肌肉、认知、免疫</strong>三大系统为测量域的 <strong>1 年期</strong>干预试验</li>
<li><strong>评审</strong>：评审主席 Steven Cummings（UCSF 荣誉教授）；健康领域执行副总裁 Jamie Justice</li>
</ul>
<h2>最值得记的一句原话</h2>
<blockquote><p>「我们现在是否有足够证据基于功能指标开展监管对话？<strong>没有。</strong>」——Jamie Justice</p></blockquote>
<p>奖项提供的是<strong>十年典型衰退的参照数据</strong>，不是批准路径。</p>
<h2>局限</h2>
<p><strong>1 年期试验能否外推至数十年衰老，是本领域最硬的未解问题</strong>。三大测量域（肌肉/认知/免疫）
在 12 个月内的变化幅度、与长期健康寿命的映射关系，均尚未被验证。</p>""",
    src("2026-10-26", "XPRIZE Healthspan（LT 报道）",
        "https://longevity.technology/news/the-101-million-question-isnt-who-wins/"))

# ── §3 #1 · Longeveron ELPIS II（负面） ──────────────────────────────
add("Longeveron-ELPIS-II-Phase-2b-Miss-HLHS-2026.html",
    "Longeveron ELPIS II 2b 期主要终点未达：间充质干细胞疗法在 HLHS 上失败",
    "临床与转化", "2026-10-26",
    "Longeveron 公布 ELPIS II 2b 期更新结果，未达 12 个月右室射血分数变化的主要疗效终点；"
    "预设次要终点 MACE 达显著（8 例 vs 1 例，P=0.043）。",
    """<h2>结果</h2>
<ul>
<li><strong>设计</strong>：40 例婴儿，随机；Laromestrocel（年轻健康供者骨髓来源间充质干细胞）作为左心发育不良综合征（HLHS）II 期姑息手术的辅助治疗</li>
<li><strong>主要终点</strong>：12 个月右室射血分数变化——<strong>未达到</strong></li>
<li><strong>预设次要终点</strong>：主要不良心脏事件（MACE）<strong>达统计学显著：标准治疗组 8 例 vs Laromestrocel 组 1 例（P=0.043）</strong></li>
<li><strong>安全性</strong>：耐受性良好，12 个月内未发现治疗相关严重不良事件</li>
<li><strong>合作与资助</strong>：与 NHLBI 合作、获 NIH 资助</li>
<li><strong>下一步</strong>：公司拟请求与 FDA 开会审议结果并讨论 HLHS 开发项目下一步；该 2 期数据已入选 <strong>2026-11-08 AHA 科学年会 late-breaking 口头报告</strong></li>
</ul>
<h2>为什么这是本期最需要如实记录的一条</h2>
<p>间充质干细胞疗法在罕见病上<strong>主要终点失败</strong>，会外溢到整个「细胞疗法抗衰」叙事的证据预期。
次要终点显著但主要终点未达，是典型的「不能反推为成功」的情形——引用时若只提 MACE 的 P=0.043，
是对结果的实质性误读。</p>
<h2>局限</h2>
<ul>
<li>周报注明：<strong>ELPIS II 的 NCT 号未获</strong>（ClinicalTrials.gov API 以「ELPIS / laromestrocel」检索无返回，可能为 EudraCT 或后期登记），来源为公司 GlobeNewswire 一手稿</li>
<li>样本量 40 例；次要终点事件数极小（8 vs 1），P 值对单个事件的重新分类高度敏感</li>
</ul>""",
    src("2026-10-26", "Longeveron / GlobeNewswire 原稿",
        "https://www.globenewswire.com/news-release/2026/10/26/3388178/0/en/longeveron-announces-updated-results-from-elpis-ii-phase-2b-clinical-trial-evaluating-laromestrocel-as-a-potential-treatment-for-hypoplastic-left-heart-syndrome-hlhs.html",
        "LT：https://longevity.technology/news/updated-phase-2b-data-show-fewer-major-cardiac-events-in-hlhs/"))

# ── §3 #2 · Arrowhead ARO-MAPT ───────────────────────────────────────
add("Arrowhead-ARO-MAPT-Subcutaneous-siRNA-Crosses-BBB-2026.html",
    "Arrowhead ARO-MAPT：皮下 siRNA 首次临床验证可跨越血脑屏障，CSF tau 降 73%",
    "神经退行", "2026-10-14",
    "ARO-MAPT 1/2a 期中期数据：健康志愿者 12.8 mg/kg 组 CSF 总 tau 平均降 73%（个体最高 85%），"
    "末次给药后 90 天仍维持。",
    """<h2>数据</h2>
<ul>
<li><strong>药物</strong>：ARO-MAPT——靶向 MAPT 的 RNAi，沉默全部 6 种 tau 亚型，<strong>皮下给药</strong></li>
<li><strong>降幅</strong>：2.1 mg/kg（D1/8/15）与 6.4 mg/kg 在 D105 的 CSF 总 tau 平均降幅 <strong>40% / 69%</strong>；12.8 mg/kg（D1/15）<strong>平均降 73%、个体最高 85%</strong></li>
<li><strong>持续性</strong>：D105 = <strong>末次给药后 90 天</strong>，支持每三个月或更低频给药</li>
<li><strong>安全性</strong>：多数 TEAE 为 1 级/轻度，无严重 TEAE、无死亡、无导致停药事件</li>
<li><strong>规模</strong>：计划入组约 64 名健康志愿者 + 至多 48 名早期 AD 患者（第 2 部分），<strong>2027 年更新数据</strong></li>
<li><strong>试验</strong>：Phase 1/2a｜<strong>NCT07221344</strong>（RECRUITING，末次更新 2026-09-16）</li>
<li><strong>公司定性</strong>：CEO Christopher Anzalone 称这是 TRiM 平台<strong>首次临床验证可皮下递送 siRNA 跨越血脑屏障</strong></li>
</ul>
<h2>对衰老领域的意义在递送，不在 tau</h2>
<p>CNS 递送一直是神经退行病与脑衰老干预的共同瓶颈。这条的价值是<strong>平台级</strong>的：
皮下注射—跨 BBB—长效，这套组合一旦成立，适配的靶点远不止 MAPT。</p>
<h2>局限</h2>
<ul>
<li>中期数据，健康志愿者为主；AD 患者部分尚未读出</li>
<li>tau 降低与临床获益的关联未在本试验中建立</li>
</ul>""",
    src("2026-10-14", "Arrowhead 官方新闻稿",
        "https://arrowheadpharma.com/en-us/newsroom/arrowhead-pharmaceuticals-announces-aro-mapt-interim-phase-12a",
        "LT：https://longevity.technology/news/arrowheads-shot-under-the-skin-cut-spinal-fluid-tau-by-73/"))

# ── §3 #3 / §4 #1 · Calico Fosigotifator EMA PRIME ───────────────────
add("Calico-Fosigotifator-EMA-PRIME-VWM-2026.html",
    "Calico 的 fosigotifator 获 EMA PRIME：eIF2B 激活剂攒成 FDA+EMA 双认定",
    "临床与转化", "2026-10-22",
    "Calico Life Sciences 的 eIF2B 激活剂 fosigotifator 获 EMA PRIME 资格，用于白质消融性脑病（VWM）；"
    "此前已获 FDA 突破性疗法认定并入选 FDA START 试点。",
    """<h2>事实</h2>
<ul>
<li><strong>药物 / 机制</strong>：Fosigotifator——<strong>eIF2B 激活剂</strong></li>
<li><strong>适应症</strong>：白质消融性脑病（VWM）——超罕见进展性脑白质病，由 eIF2B 五个亚基变异引起慢性整合应激反应（ISR）激活，<strong>目前无任何获批疗法</strong></li>
<li><strong>依据</strong>：基于正在进行的 <strong>1b/2 期</strong>（2023-505704-30-00）初步临床数据授予</li>
<li><strong>既往资格</strong>：已获 FDA 突破性疗法认定（2026 年）并入选 FDA START 试点项目</li>
<li><strong>临床前</strong>：fosigotifator 降低脑与脊髓 ISR、改善运动缺陷<strong>并延长寿命</strong></li>
<li><strong>试验</strong>：Phase 1b/2｜<strong>NCT05757141</strong>（RECRUITING，n=50，主要完成 2027-11，末次更新 2026-10-16）</li>
<li><strong>Levinson 表态</strong>：PRIME 反映 VWM 的重大未满足需求</li>
</ul>
<h2>对本领域的意义</h2>
<p>一家明确以「衰老与年龄相关疾病」定位的公司，<strong>第一次把监管资格攒成 FDA + EMA 双认定</strong>。
对以 ISR / eIF2B 为代表的衰老核心通路而言，这意味着监管愿意为「机制明确 + 无药可医」的罕见切口开快速通道——
<strong>走罕见病、再外推至常见年龄相关病，仍是最现实的落地路径</strong>。</p>
<h2>局限</h2>
<p>「延长寿命」为<strong>临床前</strong>结果，未在人体中检验；PRIME 依据的是初步临床数据，
不构成疗效结论。</p>""",
    src("2026-10-22", "Calico 官方新闻稿 / EMA PRIME 官方页",
        "https://www.calicolabs.com/press/calico-life-sciences-announces-european-medicines-agency-grants-prime-designation-to-investigational-fosigotifator-for-vanishing-white-matter",
        "EMA：https://www.ema.europa.eu/en/human-regulatory-overview/research-and-development/prime-priority-medicines"))

# ── §3 #4 · Insilico ISM6331 ─────────────────────────────────────────
add("Insilico-ISM6331-Pan-TEAD-Inhibitor-ESMO-2026.html",
    "Insilico ISM6331：生成式 AI 设计的泛 TEAD 抑制剂，130 mg 组 ORR 40%",
    "方法与工具", "2026-10-25",
    "英矽智能在 ESMO 2026 报告 ISM6331（Chemistry42 生成式 AI 设计的口服泛 TEAD 抑制剂）"
    "1 期首次人体数据：间皮瘤 130 mg QD 组 ORR 40.0%（2/5）。",
    """<h2>数据（数据截止 2026-08-14，N=36，中位既往 2 线）</h2>
<ul>
<li><strong>130 mg QD 组</strong>：ORR <strong>40.0%（2/5）</strong>；靶病灶缩小 58% 与 36%</li>
<li><strong>30–130 mg 总体</strong>：ORR <strong>18.2%（4/22）</strong>、首次评估 DCR <strong>68.2%</strong></li>
<li><strong>缓解持续性</strong>：4 例 PR 中 3 例在数据截止时仍持续（1 例接近 1 年）</li>
<li><strong>安全性</strong>：15–130 mg <strong>无 DLT</strong>、无导致停药的 TRAE；3 级 TRAE 8.3%；治疗相关蛋白尿 11.1%（低级别可逆）</li>
<li><strong>靶点结合证据</strong>：循环 CCN2 持续下降；半衰期 18~32 小时支持 QD</li>
<li><strong>报告人</strong>：Melina E. Marmarelis（宾大 Abramson）｜试验：Phase 1/2｜<strong>NCT06566079</strong>（RECRUITING，n=160）</li>
</ul>
<h2>与本领域的关联在方法学</h2>
<p>ISM6331 由 <strong>Chemistry42 生成式 AI</strong> 设计——生成式 AI 设计分子是长寿药物发现的主流新工具，
本条是该方法在实体瘤 1 期读出的一条实证。适应症（间皮瘤）本身与衰老无关。</p>
<h2>局限</h2>
<p>130 mg 组仅 5 例、2 例缓解，<strong>ORR 40% 的分母极小</strong>，置信区间必然很宽，
不宜作为该药疗效水平的稳定估计。</p>""",
    src("2026-10-25", "Insilico / PR Newswire（含港交所公告）",
        "https://www.prnewswire.com/news-releases/insilico-medicine-reports-40-orr-at-130-mg-for-pan-tead-inhibitor-ism6331-designed-using-generative-ai-in-heavily-pretreated-mesothelioma-at-esmo-2026-302919241.html",
        "港交所公告：https://www1.hkexnews.hk/listedco/listconews/sehk/2026/1027/2026102700061_c.pdf"))

# ── §3 #5 · NRG Therapeutics NRG5051 ─────────────────────────────────
add("NRG-Therapeutics-NRG5051-PET-Biodistribution-Trial-2026.html",
    "NRG5051 启动 PET 生物分布试验：为线粒体 mPTP 抑制剂的脑穿透取证",
    "线粒体", "2026-10-21",
    "NRG Therapeutics 完成 NRG5051 放射性标记并在伦敦健康志愿者启动 PET 扫描（NRG5051-102），"
    "用于证明 CNS 穿透；计划 2027 年在 ALS 患者中开展 2 期概念验证。",
    """<h2>进展</h2>
<ul>
<li><strong>药物</strong>：NRG5051——<strong>NLRX1 介导的线粒体通透性转换孔（mPTP）抑制剂</strong>，恢复神经退行病中的线粒体功能</li>
<li><strong>本条动作</strong>：新试验启动——PET 生物分布试验 <strong>NRG5051-102</strong>；已完成放射性标记并在伦敦健康志愿者启动 PET 扫描</li>
<li><strong>目的</strong>：证明 <strong>CNS 穿透</strong>，为未来患者试验的剂量选择提供依据；测定血浆动力学与分布系数以估测脑实质内药物水平</li>
<li><strong>并行</strong>：NRG5051-101（1 期随机双盲，健康志愿者安全性/耐受性/PK）正在收尾</li>
<li><strong>计划</strong>：<strong>2027 年在 ALS 患者中开展 2 期概念验证</strong></li>
</ul>
<h2>意义</h2>
<p>线粒体功能衰退是衰老的核心标志之一，而 mPTP 是线粒体途径细胞死亡的共同通道。
本条的分量在于它不是疗效数据，而是<strong>把「脑内是否够药」这个前置问题做实</strong>——
神经退行领域大量临床失败的归因之一就是中枢暴露不足。</p>
<h2>局限</h2>
<p>尚无人体疗效数据；PET 生物分布试验只回答药代与暴露，不回答靶点结合或临床获益。</p>""",
    src("2026-10-21", "NRG Therapeutics / GlobeNewswire 原稿",
        "https://www.globenewswire.com/news-release/2026/10/21/3385145/0/en/nrg-therapeutics-announces-a-pet-biodistribution-trial-of-lead-clinical-asset-nrg5051.html",
        "LT：https://longevity.technology/news/nrg-therapeutics-launches-brain-tracking-study-for-new-neurodegenerative-drug/"))

# ── §3 #6 · Immorta Bio SenoMune-0257 ────────────────────────────────
add("Immorta-Bio-SenoMune-0257-AI-Senolytic-Peptide-2026.html",
    "Immorta Bio 的 SenoMune-0257：9 氨基酸 AI 设计 senolytic 免疫疗法拟年底进人体",
    "细胞衰老", "2026-10-12",
    "Immorta Bio 公布 SenoMune-0257——9 氨基酸合成肽、AI 设计的 senolytic 免疫疗法，"
    "临床前完成，拟 2026 年底首次人体。",
    """<h2>公告内容</h2>
<ul>
<li><strong>分子</strong>：SenoMune-0257——<strong>9 氨基酸合成肽</strong>，AI 设计的 senolytic 免疫疗法</li>
<li><strong>机制</strong>：激活细胞毒性 T 细胞选择性清除衰老细胞（公司称「在测试条件下」不伤及健康细胞），并提供<strong>持久免疫记忆</strong>；公司称比个体化细胞免疫疗法生产成本更低</li>
<li><strong>前代</strong>：SenoVax 在癌症与加速衰老模型中显示抑瘤与生存期延长</li>
<li><strong>阶段</strong>：临床前完成 → <strong>拟 2026 年底首次人体</strong></li>
<li><strong>人物</strong>：CSO Thomas Ichim 称用 AI 从数十个候选肽逐级收敛至 SenoMune-0257；董事长兼 CEO Boris Reznik 称之为「治疗衰老疾病方式的根本性突破」</li>
</ul>
<h2>⚠ 必须标注的缺口</h2>
<p>公告<strong>未说明是否已提交监管申请、试验地点与规模</strong>。「拟年底进入人体」是公司表述，
不是已登记的临床试验。</p>""",
    src("2026-10-12", "Immorta Bio / PR Newswire 原稿",
        "https://www.prnewswire.com/news-releases/immorta-bio-pioneers-ai-designed-senolytic-immunotherapy-targeting-diseases-of-aging-302905700.html",
        "LT：https://longevity.technology/news/immorta-bios-nine-amino-acid-peptide-aims-at-zombie-cells/"))

# ── §3 #7 · Carnyx CNYX-005 ──────────────────────────────────────────
add("Carnyx-CNYX-005-Sleep-Aged-Rats-IND-Enabling-2026.html",
    "Carnyx 的 CNYX-005：老年大鼠总睡眠增加 1.5~2 小时，进入 IND-enabling",
    "生命历程", "2026-10-23",
    "Carnyx Therapeutics 公布 CNYX-005 临床前数据：老年大鼠总睡眠时间较对照增加约 1.5~2 小时，"
    "主要来自 NREM 睡眠；10-27 宣布进入 IND-enabling 开发。",
    """<h2>数据与动作</h2>
<ul>
<li><strong>分子</strong>：CNYX-005——口服小分子，源自<strong>睡眠调节与健康衰老相关肽生物学</strong>（含 Epitalon 研究）</li>
<li><strong>临床前结果</strong>：老年大鼠总睡眠时间较对照<strong>增加约 1.5~2 小时</strong>，主要来自 <strong>NREM 睡眠</strong>（连续 EEG 监测）</li>
<li><strong>推进</strong>：10-27 宣布进入 <strong>IND-enabling 开发</strong>（安全性、毒理、PK、暴露与剂量选择），目标支持 IND 与首次人体</li>
<li><strong>同日人事</strong>：Chris Brearley 医学博士出任 CMO（转化医学、临床药理学与早期开发 30+ 年，曾任 Pfizer、Amgen、Serono 高级职位）</li>
<li><strong>其他管线</strong>：CNYX-001（视网膜色素变性）｜CEO Patrick Gunning</li>
</ul>
<h2>周报点明的边界</h2>
<p>公司<strong>明确区分「不同于消费者圈层炒作的 Epitalon 本身」</strong>，强调走正式药物开发路径。
这条边界值得记：同一物质家族在「复方药房/远程医疗消费化供给」与「正式 IND」两条路上，
监管态度截然不同（参见本期 §4 #2 关于 503A 肽类的状态）。</p>
<h2>局限</h2>
<p>仅大鼠数据；睡眠时长的增加是否转化为健康结局获益，未有任何证据。</p>""",
    src("2026-10-23", "Carnyx（PRNewswire 转载）",
        "https://www.biospace.com/press-releases/carnyx-therapeutics-advances-lead-oral-sleep-candidate-cnyx-005-into-ind-enabling-development",
        "LT：https://longevity.technology/news/carnyxs-sleep-candidate-adds-1-5-2-hours-in-rats/"))

# ── §3 #11 · Rubedo RLS-1496（补档） ─────────────────────────────────
add("Rubedo-RLS-1496-Skin-Epigenetic-Age-Phase-1b-2026.html",
    "Rubedo RLS-1496 1b 期：外用 4 周后皮肤表观遗传年龄平均降低 2.1 年",
    "细胞衰老", "2026-10-12",
    "Rubedo Life Sciences 公布 RLS-1496 1b 期数据：特应性皮炎患者 11 对配对活检，"
    "外用 4 周后皮肤表观遗传年龄平均降低 2.1 年（p=0.032）。",
    """<h2>数据</h2>
<ul>
<li><strong>药物</strong>：RLS-1496——靶向衰老细胞的候选药</li>
<li><strong>设计</strong>：特应性皮炎患者 <strong>11 对配对活检</strong>，外用 4 周</li>
<li><strong>主要结果</strong>：皮肤<strong>表观遗传年龄平均降低 2.1 年（p=0.032）</strong>；最佳应答者第 63 天降低 <strong>11.7 年</strong></li>
<li><strong>其他</strong>：III 型胶原纤维 +10%，血浆炎症标志物下降；光化性角化病 22 例病灶平均减少 <strong>49%</strong></li>
<li><strong>阶段</strong>：Phase 1b</li>
</ul>
<h2>为什么这条重要</h2>
<p>「表观遗传年龄」第一次在<strong>人体局部组织</strong>上被一款 senolytic 候选药<strong>以配对活检的方式</strong>
测出下降。虽然样本极小、且是皮肤局部读数，但它把「时钟可干预」从血液整体读数推进到了组织层面。</p>
<h2>局限</h2>
<ul>
<li>n=11 配对活检，样本极小；p=0.032 属边界显著</li>
<li>「最佳应答者 -11.7 年」是极值，不是集中趋势，不可当作典型效应</li>
<li>本条为<strong>窗口外补档</strong>（事件日期 2026-10-12，上期周报未收录）</li>
</ul>""",
    src("2026-10-12", "Rubedo / Business Wire",
        "https://www.businesswire.com/news/home/20261012590263/en/"))

# ── §3 #12 · Life Biosciences ER-100（补档） ─────────────────────────
add("Life-Biosciences-ER-100-First-In-Human-Phase-1-2026.html",
    "Life Biosciences 的 ER-100：OSK 部分重编程首批 3 例人体数据",
    "表观遗传", "2026-10-08",
    "Life Biosciences 公布 ER-100（AAV2 玻璃体腔注射 + 多西环素诱导的 OSK 部分表观重编程）"
    "1 期首批 3 例开角型青光眼患者 Day 56 数据。",
    """<h2>数据</h2>
<ul>
<li><strong>疗法</strong>：ER-100——<strong>OSK 部分表观重编程</strong>（AAV2 玻璃体腔注射 + 多西环素诱导）</li>
<li><strong>人群 / 时点</strong>：首批 <strong>3 例</strong>开角型青光眼患者，Day 56</li>
<li><strong>安全性</strong>：全部耐受良好，<strong>无 DLT / AESI / SAE</strong>；DSMB 建议升至剂量水平 2（6×10¹¹ vg）</li>
<li><strong>信号</strong>：<strong>2/3 例视野（Humphrey）改善，≥28% 检测点提升 >4 dB</strong></li>
<li><strong>试验</strong>：Phase 1｜<strong>NCT07290244</strong></li>
</ul>
<h2>意义与克制</h2>
<p>这是部分重编程在人体上的<strong>首批安全性数据</strong>——赛道里程碑意义明确。
但 3 例、Day 56、视野改善为早期信号，<strong>既不能据此判断疗效，也不能据此判断长期安全性</strong>；
剂量已升至水平 2，试验仍在进行中。</p>
<h2>局限</h2>
<ul>
<li>n=3，无对照；视野改善的临床意义需更长时间与更大样本确认</li>
<li>本条为<strong>窗口外补档</strong>（事件日期 2026-10-08，上期周报未收录）</li>
</ul>""",
    src("2026-10-08", "Life Biosciences 官方稿",
        "https://www.lifebiosciences.com/life-biosciences-announces-first-in-human-data-from-ongoing-phase-1-trial-evaluating-er-100-in-optic-neuropathies/"))

# ── §3 #14 / §4 #3 · Biograph × Caristo ──────────────────────────────
add("Biograph-Caristo-Coronary-Inflammation-Asymptomatic-2026.html",
    "42.9% 无症状低危成人存在冠脉炎症：常规风险工具一个都没识别出来",
    "免疫与炎症", "2026-10-22",
    "Biograph 完成首个美国研究：无症状、常规风险分层为低危的成人中 42.9% 存在冠脉炎症升高，"
    "而 ApoB、hs-CRP、AHA PREVENT-ASCVD 等常规工具均未与之相关。",
    """<h2>数据</h2>
<ul>
<li><strong>技术</strong>：CaRi-Heart——AI 分析冠脉 CT 血管造影的<strong>冠状动脉周围炎症</strong></li>
<li><strong>结果</strong>：无症状、常规风险分层为低危的成人中 <strong>42.9% 存在冠脉炎症升高</strong>、17.9% 为极高</li>
<li><strong>关键发现</strong>：<strong>约 47% 无可检出斑块者亦有周围炎症升高</strong></li>
<li><strong>阴性对照</strong>：常规血检与临床风险工具（<strong>ApoB、non-HDL-C、HbA1c、hs-CRP、AHA PREVENT-ASCVD</strong>）<strong>均未与冠脉炎症相关</strong>，未能识别受影响个体</li>
<li><strong>监管状态</strong>：CaRi-Heart 已获 FDA De Novo 上市授权，CaRi-Plaque 已获 FDA 510(k) 许可</li>
</ul>
<h2>与炎症衰老（inflammaging）的同构</h2>
<p>慢性低度炎症被做成<strong>可检测、可编码、可支付</strong>的产品，干预窗口才真正存在。
这是「上游疾病相位」第一次有了可报销的影像学生物标志物。</p>
<h2>局限</h2>
<p>公司<strong>承认需更多研究验证其预后价值</strong>——即「测得出」尚未证明「能预测事件」。
在无症状低危人群中提高检出率，也必然伴随过度诊断的风险。</p>""",
    src("2026-10-22", "Biograph × Caristo / Business Wire",
        "https://www.businesswire.com/news/home/20261022460203/en/Biograph-Completes-First-U.S.-Study-with-Caristo-Diagnostics-AI-Powered-Coronary-Inflammation-Detection-Finding-Risk-in-Over-42-of-Asymptomatic-Patients",
        "LT：https://longevity.technology/news/biograph-finds-coronary-inflammation-in-43-of-asymptomatic-adults/"))

# ── §5 #1 · NewLimit 临床班底 ────────────────────────────────────────
add("NewLimit-Clinical-Development-Hire-2027-FIH-2026.html",
    "NewLimit 补齐临床班底：前 89bio 首席医学官出任临床开发负责人，重申 2027 首次人体",
    "表观遗传", "2026-10-21",
    "NewLimit 宣布 Hank Mansbach（前 89bio 首席医学官）出任临床开发负责人、"
    "Amelia Adams（前 Denali）任技术运营高级总监，并重申 2027 年进入首次人体试验。",
    """<h2>任命</h2>
<ul>
<li><strong>Hank Mansbach</strong> 出任<strong>临床开发负责人</strong>：此前任 <strong>89bio 首席医学官</strong>，主导 pegozafermin 从 1 期推进至全球 3 期（89bio 后被罗氏/基因泰克收购）</li>
<li><strong>Amelia Adams</strong> 出任<strong>技术运营高级总监</strong>：此前在 <strong>Denali Therapeutics</strong> 负责生产与质控</li>
</ul>
<h2>同日披露的技术进展（公司博客口径）</h2>
<ul>
<li>老年肝细胞再生救援效力<strong>提升 &gt;2 倍</strong></li>
<li>治疗级生产放大 <strong>314 倍</strong>且质量提升 13 倍</li>
<li>累计测试 <strong>&gt;5000 个 payload</strong></li>
<li>重申 <strong>2027 年进入首次人体试验</strong></li>
</ul>
<h2>为什么组织信号比数据更说明问题</h2>
<p>部分重编程赛道<strong>从「科学验证」切换到「临床可执行」</strong>：招一个把药推到全球 3 期的
CMO 出身的人做临床开发负责人，是在为 2027 年那一步铺路。这个动作本身
比任何一条临床前数据都更能说明这条赛道到了哪个阶段。</p>
<h2>局限</h2>
<p>技术进展数字均为<strong>公司自述</strong>，无同行评议出版物支撑。</p>""",
    src("2026-10-21", "NewLimit 官方博客", "https://blog.newlimit.com/p/2026-summer"))

# ── §3.1 · 行业结构回撤（Unity / Turn Bio） ──────────────────────────
add("Longevity-Industry-Retrenchment-Unity-Turn-Bio-2026.html",
    "两条 ⬇：Unity Biotechnology 已停止运营，Turn Bio 核心资产被竞拍收购",
    "生命历程", "2026-10-28",
    "本期《管线状态基线》v1.0 记录两条重大回撤：Unity Biotechnology 官网明示公司已停止运营；"
    "Turn Biotechnologies 官网域名过期，核心 ERA 平台资产已于 2026-05 被韩国大熊制药竞拍收购。",
    """<h2>Unity Biotechnology</h2>
<ul>
<li><strong>基线状态（2026-10-28）</strong>：<strong>公司已停止运营</strong>（官网明示）</li>
<li><strong>历史状态</strong>：临床阶段 senolytic（曾是该赛道最有代表性的公司之一）</li>
<li><strong>佐证</strong>：最近 SEC 备案 2026-08-19</li>
</ul>
<h2>Turn Biotechnologies</h2>
<ul>
<li><strong>基线状态</strong>：<strong>官网域名过期</strong>（turn.bio 与 /news、/newsroom 均返回 Squarespace「Website Expired」）</li>
<li><strong>资产去向</strong>：核心 <strong>ERA 平台</strong>资产已于 <strong>2026-05-21</strong> 被<strong>韩国大熊制药竞拍收购</strong></li>
<li><strong>变更</strong>：⬇ 资产流失</li>
</ul>
<h2>本期另两条「官网消失」的留痕（无法从官方渠道确认）</h2>
<ul>
<li><strong>Retro Biosciences</strong>：retrobio.com 现为<strong>域名出售停放页</strong>（标价 $100,000）</li>
<li><strong>Juvenescence</strong>：juvenescence.com 为中文「该网站正在出售」停放页，疑似迁至 juvlabs.com（该站对 curl 返回 403 Cloudflare 挑战）</li>
</ul>
<p>周报对这两家的判定是<strong>「无更新」</strong>——注意其措辞：不是「确认无新闻」，
而是<strong>「无法从官方渠道确认」</strong>。这是诚实记录与猜测之间的分界线。</p>
<h2>为什么这条要单独成篇</h2>
<p>在一个以融资额与管线推进为主要叙事的领域里，<strong>失败与退场长期少被记录</strong>。
senolytic 赛道最早的代表公司之一停止运营、部分重编程早期平台资产被竞拍，
这两条构成了与本期各条 ⬆ 同等重要的信息。只报 ⬆ 不报 ⬇ 的行业记录是失真的。</p>""",
    src("2026-10-28", "行业情报周报 2026-W44 · 管线状态基线 v1.0（行业层 file_id dmsATtPgKteT）",
        "https://longevity.technology/news/",
        "基线快照见网盘行业层《管线状态基线》（19,435 B，实测非空）"))

# ── §2 #5 · Beacon × Snap（脑衰老表型可规模化采集） ──────────────────
add("Beacon-Biosignals-Acquires-Snap-Home-EEG-2026.html",
    "Beacon 收购 Snap Diagnostics：家用 EEG 睡眠检测进入基层医疗，脑衰老表型走向临床级数据",
    "神经退行", "2026-10-22",
    "Beacon Biosignals 收购 Snap Diagnostics（金额未披露），其 FDA 510(k) cleared Waveband 头带"
    "配合 AI 分析，自 2027 年进入基层医疗、远程医疗与精神科场景。",
    """<h2>交易与产品</h2>
<ul>
<li><strong>买方 / 卖方</strong>：Beacon Biosignals × Snap Diagnostics（全美 50 州运营、Medicare 注册的独立诊断检测机构、JCAHO 认证）</li>
<li><strong>金额</strong>：<strong>未披露</strong>（周报 §6 已列为待核实）</li>
<li><strong>产品</strong>：Beacon 的 <strong>FDA 510(k) cleared Waveband 头带</strong> + AI 分析，用于阻塞性睡眠呼吸暂停与夜间睡眠紊乱评估</li>
<li><strong>场景</strong>：2027 年起进入基层医疗、远程医疗、精神科等；患者覆盖翻倍以上</li>
<li><strong>平台</strong>：含基于<strong>数百万小时 EEG</strong> 训练的基础模型，用于生成<strong>脑健康生物标志物</strong>；同时支持生物制药伙伴的临床试验</li>
</ul>
<h2>与衰老的关联</h2>
<p>睡眠结构改变（深 NREM 减少、碎片化）是<strong>公认的脑衰老表型</strong>。家用 EEG 把这一表型
变成可规模化采集的数据；家庭场景 + Medicare 计费意味着这类数据将从<strong>「研究级」变成「临床级」</strong>。</p>
<h2>局限</h2>
<p>交易金额未披露；「脑健康生物标志物」目前是平台能力表述，未给出已验证的临床效用证据。</p>""",
    src("2026-10-22", "Beacon Biosignals / GlobeNewswire 原稿",
        "https://www.globenewswire.com/news-release/2026/10/22/3386463/0/en/beacon-biosignals-acquires-snap-diagnostics-paving-the-way-for-eeg-enabled-home-sleep-testing-in-every-care-setting.html",
        "LT：https://longevity.technology/news/beacon-biosignals-acquires-snap-diagnostics-for-home-eeg-sleep-testing/"))


def main():
    arts = json.load(open(os.path.join(ROOT, "data/articles.json"), encoding="utf-8"))
    used = {a["slug"] for a in arts}
    dup = [s for s in A if s in used or os.path.exists(os.path.join(ROOT, "news", s))]
    for s in dup:
        print(f"  ⨯ 跳过（规则④，站内已有）：{s}")
        A.pop(s)
    print(f"本批成篇 {len(A)} 篇 · 跳过 {len(dup)} 条")

    sys.argv = ["gen_articles.py", ROOT, "/dev/null", DATE]
    _spec = importlib.util.spec_from_file_location(
        "ga", os.path.join(ROOT, "scripts", "gen_articles.py"))
    ga = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(ga)
    ga.A = A
    ga.main()


if __name__ == "__main__":
    main()
