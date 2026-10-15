#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_articles_cross_weekly_2026-10-12.py —— 内容摄入第 13 批（临床×文献交叉周报·创刊号回填）

来源与判定
──────────
事实源：元层《临床×文献交叉周报_2026-10-12》（dsMQHIJKCTLS，实测 33,644 B，人工代跑交付）。
该周报的核心研究经四路查重 + 关键词硬核验**均已在站**（D+Q MASH RCT / ER-100 /
CA77.1 / SENESCENCE2030 / HFpEF / TAME / AMPK 991 等），无单篇真漏收。
本批回填的是周报独有的**交叉分析视角**：三态判定（进展/争议/新靶点）与登记捕获缺口，
作为「交叉周报」栏目创刊号。上游自动化链路 2026-10-19 首跑后，本栏目每周一篇。

纪律：数字与 DOI 全部沿用周报原文（其引用均为公开摘要级信息），不臆测；
登记清单口径沿用本站 /trials.html（82 项机制口径）与 /trials-full.html（558 项宽口径）。
"""
import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATE = "2026-10-16"

sys.argv = ["gen_articles.py", ROOT, "/dev/null", DATE]
_spec = importlib.util.spec_from_file_location(
    "ga", os.path.join(ROOT, "scripts", "gen_articles.py"))
ga = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ga)

A = {}

A["Cross-Weekly-Clinical-Literature-2026-10-12.html"] = dict(
    topic="临床与转化", ev="A", tag="交叉周报",
    title="交叉周报创刊号：senolytics 首次逆转人体器官纤维化，而登记库里「部分重编程」仍是 0 项",
    crumb="临床×文献交叉周报 2026-10-12",
    desc="以 ClinicalTrials.gov 登记库为骨架、近 6 周文献为血肉的首期交叉周报：D+Q 实现 RCT 级纤维化逆转、ER-100 已给人体药但登记检索抓不到、CMA 是清除衰老细胞的第二条通路、NAD+ 与雷帕霉素双双进入「对谁有效」阶段。",
    source=('<a href="https://clinicaltrials.gov/" target="_blank" rel="noopener noreferrer">ClinicalTrials.gov</a> 登记库'
            '（v2026-10-01 快照，7 方向 558 项）× 近 6 周文献（Nature Metabolism / Nature Aging / Aging Cell 等）'
            ' · 本文为《临床×文献交叉追踪周报 2026-10-12》的站点版，原始报告见项目知识库'),
    body="""<p>这是「临床×文献交叉周报」的第一期。方法很简单也很硬：以临床试验登记库的 7 个方向为骨架，逐方向对照最近几周的实验室发现与临床读出，给每一对「临床在验证的机制 ↔ 实验室最新证据」打三类标签——<strong>【进展】</strong>同向推进、<strong>【争议】</strong>证据打架、<strong>【新靶点】</strong>实验室有、临床还没有。以下是本期六个头条。</p>

<h2>头条一：senolytics 拿到了十余年来最硬的人体结构性终点证据</h2>

<p>D+Q（达沙替尼+槲皮素）治疗纤维化型 MASH 的 2 期随机对照试验（<strong>NCT05506488</strong>）发表于 <em>Nature Metabolism</em>（2026-10-01）：<strong>肝纤维化改善 47% vs 安慰剂 7%（P=0.02）</strong>。站内此前已有专文报道（见延伸阅读），本期交叉判定的增量在于定位：这是「清除衰老细胞」假说自提出以来<strong>首次在随机对照设计中逆转人类器官结构性病变</strong>。两个限定必须说清：样本仅 31 人；且该试验不在当前活跃登记清单内（状态差异）——「登记 ≠ 全景」正是本栏目要盯的第一类缺口。</p>

<h2>头条二：登记库里「部分重编程 = 0 项」，而全球首个部分重编程人体试验已经读出数据</h2>

<p>登记清单按关键词检索，「部分重编程/表观遗传重编程」方向计 <strong>0 项</strong>。但 Life Biosciences 的 <strong>ER-100（NCT07290244）</strong>已于 2026-10-08 公布首批 3 例人体数据：<strong>无剂量限制毒性，2/3 例视野改善，DSMB 建议升剂量</strong>。差异的根源是<strong>关键词捕获缺口</strong>——该试验以眼科适应症注册、干预字段写 AAV2-OSK，标题不含 aging 字样。这不是「没有试验」，是「检索式抓不到」。<strong>教训已固化：</strong>检索式必须补 OSK / Yamanaka / partial reprogramming / AAV2，并按申办方白名单二次召回。</p>

<h2>头条三：CMA——清除衰老细胞的第二条通路</h2>

<p><em>Nature Aging</em>（2026-10-05）显示：<strong>伴侣介导自噬（CMA）随龄衰退</strong>导致巨噬细胞无法清除衰老细胞；CMA 激活剂 <strong>CA77.1</strong> 在老年鼠降低多组织衰老负荷（站内已有专文）。交叉判定的意义：senolytics「直接杀死衰老细胞」之外，存在<strong>第二条路线——恢复清除能力（CMA/LAMP2A）</strong>。目前 CMA 方向尚无对应在研临床试验，属典型【新靶点】。</p>

<h2>头条四与五：NAD+ 与雷帕霉素，双双进入「对谁有效」阶段</h2>

<p>两条主线在同一周给出了结构相似的答案：</p>

<ul>
<li><strong>NAD+ 前体</strong>：头对头 RCT 确认 NR/NMN 均使全血 NAD+ 约翻倍，但同期 15 项 RCT 的系统评价显示对体重、血糖、血脂、血压<strong>全部无显著影响</strong>——「参与了机制」不等于「改变了临床终点」。</li>
<li><strong>雷帕霉素</strong>：三项结果彼此矛盾——低剂量降低老年人免疫细胞 p21 且机制为「增强 DNA 损伤韧性（genoprotection）」而非经典自噬抑制（<em>Aging Cell</em>，DOI 10.1111/acel.70364）；APOE4 携带者脑血流改善；但 Mayo 的 HFpEF+衰弱老人<strong>功能终点失败</strong>。<strong>「对谁有效」已取代「是否有生物学效应」成为核心问题。</strong></li>
</ul>

<h2>头条六：TAME 仍未入组首例，机制侧已在绕行</h2>

<p>FDA 早在 2015 年即认可 TAME 的复合终点设计，但至本期因仿制药无利润、约 4500–7500 万美元资金缺口<strong>仍未入组首例受试者</strong>——整个 geroscience 领域缺一个「FDA 认可的衰老适应症」锚点。同期 <em>Aging Cell</em>（2026-09-29）报道直接 AMPK 激活剂 <strong>991</strong> 在裂殖酵母、线虫（中位寿命 ≈18–20%）、果蝇（≈9%）延长寿命，AMPK 缺失则效应消失（DOI 10.1111/acel.70721）——为绕过 TAME 僵局提供了机制替代路径（注意：无小鼠寿命数据，高剂量反而缩短寿命）。</p>

<h2>方法学附言：本栏目要长期盯的四类失真</h2>

<ol>
<li><strong>登记捕获缺口</strong>：以疾病适应症注册的衰老机制试验会被关键词漏掉（ER-100 案例）；</li>
<li><strong>状态覆盖缺口</strong>：只盯活跃登记会漏掉「已完成且已读出」的试验（NCT05506488 正是如此）；</li>
<li><strong>替代终点双向失真</strong>：既有「标志物改善但终点未达」（NAD+），也有「无创指标全阴但活检真实逆转」（D+Q 肝纤维化的 FIB-4/ELF 均阴性）；</li>
<li><strong>剂量曲线被低估</strong>：AMPK 991 高剂量反而缩短寿命，是本周最便宜的提醒。</li>
</ol>

<p>方法论共识方面，SENESCENCE2030 路线图（<em>Nature Aging</em>，DOI 10.1038/s43587-026-01222-y）要求建立衰老细胞「内型」分类与可临床操作的标准化生物标志物——目前<strong>全球尚无获批的 senolytic 药物</strong>，这个基本盘没有变。</p>""",
    related=[("Dasatinib-Quercetin-Senolytic-MASH-Liver-Fibrosis-RCT-2026.html",
              "达沙替尼+槲皮素治疗 MASH 肝纤维化：31 人随机对照试验 47% 纤维化改善"),
             ("Life-Biosciences-ER-100-First-Human-Data-AAO-2026.html",
              "全球首个细胞重编程人体试验公布早期数据：3 名青光眼患者 2 例视野改善"),
             ("CMA-Decline-Macrophage-Senescent-Clearance-NatureAging-2026.html",
              "CMA 衰退让「僵尸细胞」逃过免疫清除：Nature Aging 揭示衰老细胞堆积新机制")]
)

ga.A = A
if __name__ == "__main__":
    ga.main()
