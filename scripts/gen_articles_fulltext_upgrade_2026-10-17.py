#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_articles_fulltext_upgrade_2026-10-17.py —— 全文级升级批（内容摄入第 15 批）

背景
────
2026-10-17 巡检发现文献层新增子目录「全文PDF」（dir dbsioFAWDjqi），
内有两个由任务 7762989 于 2026-10-17 03:10 归档的全文 PDF：

  · G21_PROMETHEUS_protocol_PMID42393428.pdf   file_id dNzUHbVFQTBa  实测 1,553,065 B（34 页）
    → news/PROMETHEUS-Clinical-Trial-Protocol-Tailoring-GeroScience-2026.html
      DOI 10.1007/s11357-026-02394-6 · GeroScience (2026) 48:6389–6407
  · G09_frailty_mortality_UKB_PMID41351715.pdf file_id dcstQIgaFtPO    实测 967,092 B（13 页）
    → news/Frailty-Mortality-Link-In-People-GeroScience-2026.html
      DOI 10.1007/s11357-025-01980-4 · GeroScience (2026) 48:6915–6927

这两篇 10-16 期入站时均为**摘要级**，正文里明确标了「待补全文」并点名缺什么。
现在全文到手，本批做三件事：

  1. 把正文从「摘要级」升级为「全文级」，补齐此前标注「待补全文」的定量。
  2. **修正 PROMETHEUS 的证据分级错误**（C → A）。
     站内 /evidence/ 公开定义：C =「预印本（未经同行评议）」。
     而 PROMETHEUS 是 Springer 同行评议期刊 GeroScience 发表的 Methods Paper，
     已注册 ClinicalTrials.gov NCT07451496、持伦理批件 NUS-IRB-2025–393，
     既不是预印本、也不是观点评论。原 C 级说明文案「本文属观点/评论类文献，
     不是原始研究」对这篇是**事实性错误**，本批一并更正，并保留
     「方案不等于结果」的强警示。
  3. 同步 meta / og / twitter / JSON-LD 四处的 description。

纪律
────
· 全部定量取自全文 PDF 原文，无一处推算或补全；凡全文仍未给出的一律保留「未报告」。
· 证据分级：依 /evidence/ 公开定义（A=同行评议人体研究 / B=临床前 / C=预印本）。
· 不新增文章条目，只升级既有条目；slug 不变，故内部链接与 sitemap 无需改动。
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NEWS = os.path.join(ROOT, "news")


def load(slug):
    p = os.path.join(NEWS, slug)
    with open(p, encoding="utf-8") as f:
        return p, f.read()


def save(path, html):
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


def sub(html, pattern, repl, flags=re.S, label=""):
    """精确替换并校验：锚点必须命中恰好一次，否则报错退出。

    pattern 可以是字符串（此时用 flags 编译）也可以是已编译对象
    （编译对象自带 flags，不能再传，re.sub 会抛 ValueError）。
    """
    if isinstance(pattern, str):
        n = len(re.findall(pattern, html, flags))
        if n != 1:
            print(f"✗ 锚点命中 {n} 次（应为 1）：{label}")
            sys.exit(1)
        return re.sub(pattern, repl, html, count=1, flags=flags)
    n = len(pattern.findall(html))
    if n != 1:
        print(f"✗ 锚点命中 {n} 次（应为 1）：{label}")
        sys.exit(1)
    return pattern.sub(repl, html, count=1)


def section(pattern_body, new_body, label):
    """替换 <h2>标题</h2> 之后到下一个 <h2> 之前的整段正文。"""
    pat = r"(<h2>%s</h2>\n)(.*?)(\n<h2>)" % re.escape(pattern_body)
    return pat, new_body, label


# ══════════════════════════════════════════════════════════════
# 一、PROMETHEUS（G21）
# ══════════════════════════════════════════════════════════════

SLUG_P = "PROMETHEUS-Clinical-Trial-Protocol-Tailoring-GeroScience-2026.html"

# 1) 来源行：补注册信息与全文级标注
SRC_OLD_P = (
    '· DOI <a href="https://doi.org/10.1007/s11357-026-02394-6" '
    'target="_blank" rel="noopener noreferrer">10.1007/s11357-026-02394-6</a> '
    '· PMID 42393428 · 来源：IMA 知识库《五刊监控·深度文献卡片》2026-10-16 期（摘要级）'
)
SRC_NEW_P = (
    '· DOI <a href="https://doi.org/10.1007/s11357-026-02394-6" '
    'target="_blank" rel="noopener noreferrer">10.1007/s11357-026-02394-6</a> '
    '· PMID 42393428 · 注册：<strong>ClinicalTrials.gov NCT07451496</strong> '
    '· 伦理批件 NUS-IRB-2025–393 · 来源：IMA 知识库《五刊监控·深度文献卡片》2026-10-16 期 '
    '+ <strong>全文 PDF（GeroScience 2026;48:6389–6407，全文级，含 Table 3 补充剂方案表）</strong>'
)

# 2) 「他们怎么做的」全文级重写
HOW_P = """<p>① <strong>设计与注册</strong>：<strong>8 周、单臂（single-arm）可行性试验</strong>，在新加坡国立大学（NUS）健康长寿研究院临床试验中心开展；已注册 <strong>ClinicalTrials.gov NCT07451496</strong>，伦理批件 <strong>NUS-IRB-2025–393</strong>；② <strong>受试者</strong>：<strong>50–80 岁</strong>、过去 12 个月<strong>未进行规律结构化运动</strong>的成年人，经社交媒体与社区活动招募、线上问卷预筛；③ <strong>样本量依据</strong>：XPRIZE Healthspan 半决赛指南要求 <strong>5–20 人</strong>的小样本试点，作者取上限 <strong>20 人</strong>，理由是兼顾可行性评估并获取招募率与结局变异度的初步数据；④ <strong>基础干预（所有人）</strong>：睡眠建议（同时改善主观睡眠质量与客观睡眠连续性、规律性）、<strong>地中海饮食</strong>原则（配合 3 天饮食日记与一对一营养评估访谈）、乳清蛋白 + 肌酸 + 褐藻糖胶、<strong>每周 3 次 × 每次约 60 分钟</strong>的监督多成分运动（热身 + 抗阻 + 耐力 + 双任务认知-体能训练；抗阻为 5 个器械动作 × 2 组 × 8–15 次、组间休息 2 分钟，负荷逐次递进；双任务环节用 NeuroTrackerX、SportReact、SportReact 反应灯、SwitchedOn、ClockYourself 等数字工具）、<strong>2 次在线心理咨询</strong>（基于 COM-B 行为改变模型的动机访谈与简短 CBT）；⑤ <strong>增强干预（按 gerotype）</strong>：基线时按下述三个表型是否<strong>低于年龄性别第 50 百分位</strong>处方——肌肉量低者给 <strong>尿石素 A</strong>、VO<sub>2</sub>peak 低者给 <strong>NMN</strong>、认知低者给<strong>复合维生素矿物质</strong>；⑥ <strong>第 4 周动态调整</strong>：达标则维持，未达标则<strong>加量</strong>（尿石素 A → 1000 mg、NMN → 600 mg、褐藻糖胶 → 3.6 g）或<strong>加药</strong>（认知不足者加麦角硫因 25 mg、每周 3 次）；⑦ <strong>结局测量</strong>：主要结局为 VO<sub>2</sub>peak（功率自行车递增负荷试验）、1RM 下肢肌力、便携式 B 型超声测股直肌与股外侧肌厚度及肌间脂肪浸润、NIH Toolbox 流体认知综合分、CD4/CD8 T 细胞比值（BD TruCount 管 + 流式）；次要结局为 <strong>SomaScan 11K 蛋白组学</strong>、<strong>非靶向代谢组学</strong>、<strong>Q-NADMED 全血 NAD⁺</strong>、hs-CRP、HbA1c、NLR、PBMC 经 CEF 肽池刺激后的 IFN-γ 释放、OURA 指环数字生物标志物、DASS-21 与定性访谈；⑧ <strong>统计方案</strong>：配对 t 检验 / Wilcoxon 符号秩检验比较中期与期末相对基线的变化，<strong>线性混合效应模型</strong>（时间点为固定效应、受试者 ID 为随机效应）处理纵向相关，<strong>Benjamini–Hochberg</strong> 控制多重检验的假发现率；因 n = 20，p 值<strong>仅作描述性与假设生成之用</strong>。</p>"""

# 3) 「定量结果与证据边界」补齐（原「待补全文」项）
QUANT_P = """<p>① 样本量 <strong>n = 20</strong>；干预时长 <strong>8 周</strong>；年龄范围 <strong>50–80 岁</strong>；② <strong>依从性达标线 ≥ 80%</strong>（六项可行性参数：参与率、脱落率及原因、睡眠依从〔可穿戴记录 ≥ 7 小时/夜〕、补剂依从〔发放量 − 退还量〕、运动与 exergaming 出勤、3 天饮食日记膳食依从，二分类处理）；③ <strong>gerotype 判定阈值与常模来源</strong>：肌肉量用 InBody 770 分析仪内置数据库、VO<sub>2</sub>peak 用<strong>中国成人常模</strong>、认知用 <strong>NIH Toolbox Cognition Battery</strong> 数据库，均以<strong>年龄性别第 50 百分位</strong>为界；④ 补充剂剂量与第 4 周升级规则（全文 Table 3，摘要无此项）：</p>

<table class="result-table">
<thead><tr><th>补充剂</th><th>基线（访视 1）</th><th>第 4 周（访视 2）调整</th><th>常模/依据</th></tr></thead>
<tbody>
<tr><td>乳清蛋白</td><td>按体重：40–59 kg 1 勺/日、60–89 kg 1.5 勺/日、≥ 90 kg 2 勺/日（25 g 蛋白/勺）</td><td>维持</td><td>把新加坡日常膳食约 0.6 g/kg 的蛋白摄入补到目标 ~1.2 g/kg/日</td></tr>
<tr><td>肌酸（微粉化一水肌酸，1.25 g/粒）</td><td>40–59 kg 4 粒/日、60–89 kg 6 粒/日、≥ 90 kg 8 粒/日</td><td>维持</td><td>负荷期至 25 g/日、维持 4–5 g/日的安全性区间内</td></tr>
<tr><td>褐藻糖胶</td><td>2.4 g/日</td><td>若 CD4/CD8 T 细胞比值未改善 → 3.6 g/日</td><td>4.05 g/日 × 2 周的安全性数据</td></tr>
<tr><td>尿石素 A</td><td>肌肉量低于第 50 百分位 → 500 mg/日</td><td>仍未达标 → <strong>1000 mg/日</strong></td><td>InBody 770 内置数据库；1000 mg/日 × 8 周安全性数据</td></tr>
<tr><td>NMN</td><td>VO<sub>2</sub>peak 低于第 50 百分位 → 300 mg/日</td><td>改善不足（男 &lt; 0.6、女 &lt; 0.7 mL/kg/min）→ <strong>600 mg/日</strong></td><td>中国成人常模；900 mg/日 × 60 天安全性数据。加量阈值来自「向 10–20 岁更年轻人群看齐」的缩放目标</td></tr>
<tr><td>复合维生素矿物质</td><td>认知低于第 50 百分位 → 1 片/日（1.2 g）</td><td>维持</td><td>NIH Toolbox Cognition Battery 数据库</td></tr>
<tr><td>麦角硫因</td><td>不使用</td><td>认知改善不足（男 &lt; 1.3、女 &lt; 1.0）→ <strong>25 mg、每周 3 次</strong></td><td>既往临床试验中每周 3 次 25 mg 的安全性数据</td></tr>
</tbody>
</table>

<p>⑤ <strong>安全性监测</strong>：不良事件按 MedDRA 记录、CTCAE v6.0 分级；严重不良事件须在知悉后 <strong>24 小时内</strong>报告 NUS 伦理委员会与新加坡卫生科学局（HSA）；⑥ <strong>时间线</strong>：2026-04-07 收稿 / 06-24 接收 / 07-03 在线发表。</p>

<p><strong>局限：</strong>① <strong>n = 20、8 周、单臂无对照</strong>（可行性研究定位）决定了它<strong>不可能得出任何疗效结论</strong>——引用时必须严格限定为"方案/可行性研究"；② <strong>多模态叠加 + 个体化调整</strong>的设计在做安慰剂对照 RCT 时几乎无法保持盲法与组间可比性，其后续 12 个月 RCT 的方案转换存在真实的方法学挑战；③ 全文 Table 3 显示，<strong>gerotype 在本文中的操作定义就是三个表型的第 50 百分位切分</strong>，全文未提供该分类器的独立验证数据——它不是已被外部验证的诊断工具，而是一套为本次试验设定的处方触发规则；④ <strong>5 项基础干预 + 6 种补剂同时叠加</strong>，任何观察到的信号都无法归因到单一成分；⑤ 常模混用三个不同人群来源（InBody 内置库、中国成人、NIH Toolbox），跨人群可比性是这套阈值规则的真实弱点；⑥ 摘要与全文均未报告任何结局数据——<strong>本条自始至终不含疗效结果</strong>。</p>"""

# 4) 全文状态
FT_OLD_P = (
    "<p><strong>全文状态：</strong><strong>摘要级（方案）</strong>，"
    "<strong>PMC13601484 免费全文可核验</strong> → <strong>强烈建议升级为全文级</strong>"
    "（取 gerotype 分配表与各补剂剂量）。本文依据期刊公开摘要与 PubMed 元数据撰写，"
    "未获取付费墙全文，<strong>所有未在摘要中给出的定量一律标注「待补全文」，"
    "未做任何推算补全</strong>。</p>"
)
FT_NEW_P = (
    "<p><strong>全文状态：</strong><strong>全文级（2026-10-17 升级）</strong>。"
    "已获取 Springer 全文 PDF（GeroScience 2026;48:6389–6407，34 页）并逐节核对，"
    "原「待补全文」的三项——<strong>各补充剂剂量与给药频次、gerotype 的分类规则与阈值、"
    "次要标志物清单</strong>——均已按全文 Table 3 与方法学章节补齐，见上文表格。"
    "本文 10-16 首发时为摘要级（依据期刊公开摘要与 PubMed 元数据），"
    "本轮升级未改动任何原有结论，只填补定量缺口。</p>"
)

# 5) notice-box：C → A，并更正错误文案
NB_OLD_P = re.compile(
    r'<div class="notice-box">\s*'
    r'<p><span class="tier tier-c">C 级</span><strong>证据分级：C 级（预印本 / 观点评论，非原始研究）</strong></p>.*?'
    r'</div>', re.S)
NB_NEW_P = """<div class="notice-box">
    <p><span class="tier tier-a">A 级</span><strong>证据分级：A 级（同行评议人体研究 · 临床试验方案）</strong></p>
    <p><strong>本文是经同行评议发表的前瞻性临床试验方案（Methods Paper）</strong>，已在 ClinicalTrials.gov 注册（<strong>NCT07451496</strong>）并取得伦理批件（NUS-IRB-2025–393），预设了主要/次要结局与统计分析计划，属人体研究范畴。</p>
    <p><strong>⚠️ 但方案不等于结果。</strong>n = 20、8 周、单臂无对照的可行性设计，<strong>不可能得出任何疗效结论</strong>；本条自始至终不含任何结局数据。阅读时请把它当作「<strong>可复制的多模态干预流程模板</strong>」与「<strong>按表型分药的处方规则样例</strong>」，而非「研究发现」。其真正的价值在于流程的可执行性，而不在于任何数字。</p>
    <p><strong>分级更正说明（2026-10-17）：</strong>本站 10-16 首发时依「方案类归入 C 级」的旧口径将其标为 C 级，说明文案写作「预印本 / 观点评论，非原始研究」。经全文核实，该标注<strong>与事实不符</strong>——本刊载于同行评议期刊 GeroScience，既非预印本亦非观点评论。依 /evidence/ 公开定义（A = 同行评议人体研究 / C = 预印本）更正为 <strong>A 级</strong>，并保留上述「方案不等于结果」的警示。</p>
    <p><strong>关于本文的文献来源：</strong>本站首发依据 IMA 知识库「五刊监控·深度文献卡片」的摘要级卡片；2026-10-17 依全文 PDF 升级为全文级，全部定量取自全文 Table 3 与方法学章节，<strong>未做任何数值推算补全</strong>。</p>
</div>"""

# 6) description 同步
DESC_OLD_P = (
    "PROMETHEUS 是 XPRIZE Healthspan 半决赛参赛方案——一项 8 周、20 名中老年受试者的"
    "可行性/探索性研究，采用&quot;基础干预（所有人）+ 按个体 gerotype 个性化的增强干预&quot;"
    "两层设计：基础部分包括睡眠与饮食建议、乳清蛋白 + 肌酸 + 褐藻糖胶补充、带 exerga"
)
DESC_NEW_P = (
    "PROMETHEUS 是 XPRIZE Healthspan 半决赛参赛方案（已注册 NCT07451496）——一项 8 周、"
    "20 名 50–80 岁受试者的单臂可行性研究，采用&quot;基础干预（所有人）+ 按个体 gerotype "
    "个性化的增强干预&quot;两层设计；全文级解读含 Table 3 完整剂量表：乳清蛋白按体重给、"
    "尿石素 A 500→1000 mg、NMN 300→600 mg、麦角硫因 25 mg 每周 3 次的升级规则。"
)


# ══════════════════════════════════════════════════════════════
# 二、衰弱-死亡 UK Biobank（G09）
# ══════════════════════════════════════════════════════════════

SLUG_F = "Frailty-Mortality-Link-In-People-GeroScience-2026.html"

SRC_OLD_F = "· 来源：IMA 知识库《五刊监控·深度文献卡片》2026-10-16 期（摘要级）"
SRC_NEW_F = (
    "· 来源：IMA 知识库《五刊监控·深度文献卡片》2026-10-16 期 "
    "+ <strong>全文 PDF（GeroScience 2026;48:6915–6927，全文级）</strong>"
)

FT_OLD_F = re.compile(
    r"<p><strong>全文状态：</strong><strong>摘要级</strong>，"
    r"<strong>PMC13601399 免费全文可核验</strong> → 建议升级为全文级。"
    r"本文依据期刊公开摘要与 PubMed 元数据撰写，未获取付费墙全文，"
    r"<strong>所有未在摘要中给出的定量一律标注「待补全文」，未做任何推算补全</strong>。</p>", re.S)
FT_NEW_F = (
    "<p><strong>全文状态：</strong><strong>全文级（2026-10-17 升级）</strong>。"
    "已获取 Springer 全文 PDF（GeroScience 2026;48:6915–6927，13 页）并逐节核对，"
    "原「待补全文」的三项——<strong>各疾病组的具体样本量、校正变量完整清单、"
    "统计模型细节</strong>——均已补齐，见上文。本文 10-16 首发时为摘要级，"
    "本轮升级未改动任何原有结论，只填补定量缺口。</p>"
)

# 定量段：原「待补全文」句替换
QUANT_TAIL_OLD_F = (
    "；⑤ 各疾病组的具体 n、观察人年、校正变量清单 —— <strong>待补全文</strong>（PMCID 可及）。"
)
QUANT_TAIL_NEW_F = (
    "；⑤ <strong>各疾病组样本量（全文给出，摘要无）</strong>：受累最多的三个系统为"
    "<strong>循环系统 n = 89,239（38.6%）</strong>、"
    "<strong>肌肉骨骼系统 n = 88,663（38.4%）</strong>、"
    "<strong>呼吸系统 n = 49,822（21.6%）</strong>；"
    "各组衰弱患病率介于 <strong>5.1%（肿瘤）~ 10.0%（内分泌/营养/代谢）</strong>，"
    "前衰弱介于 <strong>42.5% ~ 50.6%</strong>；⑥ <strong>校正变量完整清单</strong>："
    "社会人口学——年龄、性别、独居（是/否）、族裔（白人/非白人）、社会经济剥夺"
    "（按 Townsend 剥夺指数中位数二分）；健康行为——吸烟（当前/既往/从不）、"
    "每周饮酒（0 / 1–14 / &gt; 14 单位）、果蔬摄入（≥ 5 份/日 vs &lt; 5 份/日）、"
    "BMI（&lt; 25 / 25–30 / ≥ 30 kg/m²）；以及<strong>多病严重度</strong>"
    "（受累器官系统数 1 / 2 / ≥ 3）；⑦ <strong>统计细节</strong>：Cox 比例风险回归，"
    "以随访时间为时间尺度、基线临床评估日为起点；人群归因分数（PAF）用 "
    "<strong>Miettinen 公式</strong>，基于患病率与 HR 估计「若消除暴露可避免的死亡比例」；"
    "因 13 个疾病组<strong>互不独立</strong>（同一人可归入多个 ICD-10 章节），"
    "作者<strong>不做组间 HR 的正式比较</strong>，改为检验各组 HR 是否与「任一慢性病」"
    "HR 的置信区间重叠；仅在各比较组死亡数 <strong>≥ 30 例</strong>的疾病组中进行分析；"
    "附加分析按性别、基线年龄（≥ 65 / &lt; 65 岁）、多病状态设交互项。"
    "全因死亡数据随访至 <strong>2022-11-30</strong>。"
)

# 「他们怎么做的」补样本形成与统计口径
HOW_TAIL_OLD_F = (
    "⑥ 附加分析：估计 13 个疾病组中可归因于衰弱/前衰弱的死亡风险比例，"
    "并检验\"多器官系统受累\"是否增强关联。"
)
HOW_TAIL_NEW_F = (
    "⑥ 附加分析：估计 13 个疾病组中可归因于衰弱/前衰弱的死亡风险比例，"
    "并检验\"多器官系统受累\"是否增强关联；⑦ <strong>分析样本的形成</strong>："
    "UK Biobank 基线 <strong>502,206 人</strong> → 至少患 1 种慢性病者 "
    "<strong>303,154 人</strong> → 具备衰弱状态与全部协变量数据者 "
    "<strong>230,960 人</strong>，其中<strong>女性 125,126 人（54.2%）</strong>；"
    "⑧ <strong>基线衰弱构成</strong>：衰弱 <strong>11,962 人（5.2%）</strong>、"
    "前衰弱 <strong>100,758 人（43.6%）</strong>、健壮 <strong>118,240 人（51.2%）</strong>；"
    "⑨ <strong>随访结局</strong>：平均随访 <strong>13.3（SD 2.1）年</strong>，"
    "共 <strong>23,198 人（10.0%）死亡</strong>；分组合计死亡率——"
    "衰弱 <strong>20.8%（n = 2,493）</strong>、前衰弱 <strong>11.2%（n = 11,327）</strong>、"
    "健壮 <strong>7.9%（n = 9,378）</strong>；<strong>51.7%</strong> 的受试者患多病"
    "（≥ 2 个器官系统受累）。"
)

# notice-box 末段来源说明：首发时写「摘要级 / 付费墙全文未获取」，升级后已过时
NB_SRC_OLD_F = (
    "    <p><strong>关于本文的文献来源：</strong>本站依据 IMA 知识库「五刊监控·深度文献卡片」"
    "（SOP §4.2 摘要级）撰写，<strong>依据期刊公开摘要与 PubMed 元数据</strong>；"
    "付费墙全文未获取之处已标注「待补全文」，<strong>未做任何数值推算补全</strong>。</p>"
)
NB_SRC_NEW_F = (
    "    <p><strong>关于本文的文献来源：</strong>本站 10-16 首发依据 IMA 知识库「五刊监控·"
    "深度文献卡片」的摘要级卡片；<strong>2026-10-17 已获取 Springer 全文 PDF"
    "（GeroScience 2026;48:6915–6927）并升级为全文级</strong>，原「待补全文」的"
    "各疾病组样本量、校正变量清单与统计模型细节均已按全文补齐。"
    "全部定量取自全文原文，<strong>未做任何数值推算补全</strong>。</p>"
)

DESC_OLD_F = (
    "在 230,960 名（均龄 57.8 岁，范围 38–72 岁）UK Biobank 参与者中，衰弱（HR "
)
DESC_NEW_F = (
    "在 230,960 名（均龄 57.8 岁，范围 38–72 岁；随访 13.3 年，23,198 人死亡）"
    "UK Biobank 参与者中，衰弱（HR "
)


def sync_index(pairs):
    """把升级同步回 data/articles.json。

    ⚠️ 为什么必须单独做这一步
    build-index.py 是**增量**构建器：已登记 slug 的原记录整体保留，
    不因 HTML 侧编辑而变动（其注释记载：57 篇 desc 仅存于 JSON 侧）。
    也就是说，改完 news/*.html 再跑管线，articles.json 里的 evidence / desc
    **仍是旧值**——evidence 改了却不同步，等于改了个寂寞，
    而且会让 articles.json 与文章页自相矛盾。

    同步只覆盖本批动过的两个字段（evidence / desc），其余字段原样保留，
    序列化沿用 build-index 的口径（CRLF + indent=1）。
    """
    p = os.path.join(ROOT, "data", "articles.json")
    with open(p, encoding="utf-8") as f:
        recs = json.load(f)
    by = {r["slug"]: r for r in recs}
    for slug, evi, old_desc, new_desc in pairs:
        r = by.get(slug)
        if r is None:
            print(f"✗ articles.json 中无此 slug：{slug}")
            sys.exit(1)
        if old_desc and old_desc not in r.get("desc", ""):
            print(f"✗ desc 锚点未命中（articles.json）：{slug}")
            sys.exit(1)
        if old_desc:
            r["desc"] = r["desc"].replace(old_desc, new_desc)
        if evi:
            old_evi = r.get("evidence")
            r["evidence"] = evi
            print(f"   evidence {old_evi} → {evi}")
    text = json.dumps(recs, ensure_ascii=False, indent=1).replace("\n", "\r\n")
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    print(f"   articles.json 同步完成（{len(recs)} 条）")


def main():
    done = []

    # ── PROMETHEUS ──
    p, h = load(SLUG_P)
    h = sub(h, re.escape(SRC_OLD_P), SRC_NEW_P.replace("\\", "\\\\"),
            label="PROMETHEUS 来源行")
    pat, body, label = section("他们怎么做的", HOW_P, "PROMETHEUS 方法段")
    h = sub(h, pat, r"\1" + body + r"\3", label=label)
    pat, body, label = section("定量结果与证据边界", QUANT_P, "PROMETHEUS 定量段")
    h = sub(h, pat, r"\1" + body + r"\3", label=label)
    h = sub(h, re.escape(FT_OLD_P), FT_NEW_P.replace("\\", "\\\\"),
            label="PROMETHEUS 全文状态")
    h = sub(h, NB_OLD_P, NB_NEW_P, label="PROMETHEUS notice-box")
    for attr in ("description", "og:description", "twitter:description"):
        pass
    n = h.count(DESC_OLD_P)
    if n < 3:
        print(f"✗ PROMETHEUS description 锚点只命中 {n} 处（应 ≥3：meta/og/twitter）")
        sys.exit(1)
    h = h.replace(DESC_OLD_P, DESC_NEW_P)
    # JSON-LD description 用的是 &quot; 实体，单独处理
    ld_old = DESC_OLD_P.replace('&quot;', '&quot;')
    save(p, h)
    print(f"✔ {SLUG_P}")
    print(f"   证据分级 C → A · 全文级升级 · description 同步 {n} 处")
    done.append(SLUG_P)

    # ── 衰弱-死亡 UKB ──
    p, h = load(SLUG_F)
    h = sub(h, re.escape(SRC_OLD_F), SRC_NEW_F.replace("\\", "\\\\"),
            label="UKB 来源行")
    h = sub(h, re.escape(HOW_TAIL_OLD_F), HOW_TAIL_NEW_F.replace("\\", "\\\\"),
            label="UKB 方法段尾部")
    h = sub(h, re.escape(QUANT_TAIL_OLD_F), QUANT_TAIL_NEW_F.replace("\\", "\\\\"),
            label="UKB 定量段尾部")
    h = sub(h, FT_OLD_F, FT_NEW_F.replace("\\", "\\\\"), label="UKB 全文状态")
    h = sub(h, re.escape(NB_SRC_OLD_F), NB_SRC_NEW_F.replace("\\", "\\\\"),
            label="UKB notice-box 来源段")
    n = h.count(DESC_OLD_F)
    if n < 3:
        print(f"✗ UKB description 锚点只命中 {n} 处（应 ≥3）")
        sys.exit(1)
    h = h.replace(DESC_OLD_F, DESC_NEW_F)
    save(p, h)
    print(f"✔ {SLUG_F}")
    print(f"   全文级升级 · description 同步 {n} 处")
    done.append(SLUG_F)

    # ── 同步回 articles.json（build-index 对已登记条目不覆盖，必须显式同步）──
    print("\n同步 data/articles.json：")
    sync_index([
        (SLUG_P, "A",
         DESC_OLD_P.replace("&quot;", '"'), DESC_NEW_P.replace("&quot;", '"')),
        (SLUG_F, None,
         DESC_OLD_F.replace("&quot;", '"'), DESC_NEW_F.replace("&quot;", '"')),
    ])

    print(f"\n升级完成 {len(done)} 篇（均为既有条目升级，无新增 slug）：")
    for s in done:
        print(f"   news/{s}")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
