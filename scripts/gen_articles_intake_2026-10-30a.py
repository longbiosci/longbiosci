#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_articles_intake_2026-10-30a.py —— 05:30 班第 18 轮 · 批次 a

消化对象
────────
《行业情报周报_2026-10-30》（2026-W44 第三次运行，周五班，行业层
file_id `djpYEKiEfRcs`，实测 **36,454 B**；表格版 `dETldVedMwAc`
39,022 B，同源不同载体，**不重复成篇**，按规则④计入跳过）。
配套交付《管线状态基线.json》v1.1（`dmsATtPgKteT`，实测 26,020 B，
schema_version=1.1、条目 28）——基线文件本身不成篇。

⚠️ 判空三道闸结果
────────────────
本轮 6 个增量产出**全部实际下载核验**（ndfetch.py，见 .intake/raw/1030/）：
  · 行业周报 md 36,454 B / xlsx 39,022 B / 基线 json 26,020 B —— 非空、内容完整；
  · 人工待下载清单 48,647 B —— 非空，seen 判 UNCHANGED（仅 size 缓存修正）；
  · **文献监控_2026-10-29_总览 xlsx/csv（dZRISkLBlBMk / dmaqQuEoiQgX）
    实测 5,676 B，字节正常但 `xl/worksheets/sheet1.xml` 的 `<sheetData/>`
    为空节点、零数据行** —— 第二道闸不通过，属**空壳交付**，已告警并指明重跑任务（见留痕）。

成篇范围（15 篇）
────────────────
§2 投融资 3 条 · §3 管线临床 6 条 · §4 监管 3 条 · §5 人才 1 条
· §8 watchlist 留痕 1 条 · §4.1 未来 30 天日历 1 条 · 周报速览 1 条。

按规则④**跳过 2 条**（周报 §9 交接协议自述站内已刊，grep 核实属实）：
  · §3 #1 Mission MTX325 → `Mission-Therapeutics-MTX325-USP30-Parkinson-Phase1b-2026.html`
  · §3 #5 Klothonova    → `Klotho-Sustained-Delivery-Cell-in-a-Box-Encapsulation-FrontAging-2026.html`
另：§4 #1/#2（两笔 FDA IND）与 §3 #6/#7 为同一事件，合并进对应管线篇，不单列；
§5 #1 Voyager 治理变动合并进 Voyager 管线篇；§5 #3 Vesalius 高管合并进 Celularity 篇。

纪律
────
· 全部定量**照抄周报原文**（周报已逐条给出一手来源 URL），不推算、不补全；
· 周报 §6「待核实/降级」5 条（NCT07202403、Rapalogix RLX-201、
  消费级检测 4 项、Fathom CSO、Longevica）**一律不成篇**；
· 每篇带规则③时间标签：`数据日期 YYYY-MM-DD · 生成时间 2026-10-30 05:30`；
· 证据分级：产业动态一律 **B**（一手官方公告 / 监管机构原文可核验，非同行评议）。
"""
import html
import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATE = "2026-10-30"
GEN_AT = "2026-10-30 05:30"      # 05:30 内容摄入班消化时刻

TAG = "产业动态"
EV = "B"


def lab(dd):
    """规则③时间标签"""
    return (f'<p><em>数据日期 {dd} · 生成时间 {GEN_AT}　｜　'
            f'行业情报周报 2026-W44 第三次运行（任务 7762986，周一/三/五 01:30 班）</em></p>')


def src(dd, name, url, extra=""):
    return (f'<em>来源：{html.escape(name)}</em> · <a href="{url}" target="_blank" '
            f'rel="noopener noreferrer">{url[:110]}</a>'
            + (f' · {extra}' if extra else ''))


A = {}


def add(slug, title, topic, dd, desc, body, source):
    A[slug] = dict(topic=topic, ev=EV, tag=TAG, title=title, crumb=title[:28],
                   desc=desc, source=source,
                   body=lab(dd) + "\n" + body, related=[])


# ── §2 #1 · seragy holding ───────────────────────────────────────────
add("Seragy-12M-SerAS-Protein-Aggregation-Biomarker-Neurodegeneration-2026.html",
    "seragy 以约 1200 万欧元起步：把「蛋白聚集体」从定性做成可定量的法医式报告",
    "神经退行", "2026-10-28",
    "德国汉诺威 seragy holding（原 Prosperodes GmbH）以约 €12M / ~$13.4M 的混合融资启动，"
    "主攻 SeRAS 蛋白聚集定量生物标志物平台；资金来自 Commerzbank、MBG 与下萨克森州政府。",
    """<h2>交易要点</h2>
<ul>
<li><strong>公司</strong>：seragy holding GmbH（原 Prosperodes GmbH，德国汉诺威）</li>
<li><strong>金额与结构</strong>：约 <strong>€12M / ~$13.4M</strong>，为<strong>债权 + 股权 + 公共资金</strong>的混合包，不是纯股权融资</li>
<li><strong>投资方</strong>：<strong>Commerzbank</strong>、<strong>Mittelständische Beteiligungsgesellschaft（MBG）</strong>、<strong>下萨克森州政府</strong></li>
<li><strong>时间</strong>：公司公告 <strong>2026-10-14</strong>；Longevity.Technology 报道 <strong>2026-10-28</strong></li>
<li><strong>资金投向</strong>：扩建实验室与分析能力、扩充团队，面向<strong>阿尔茨海默病、帕金森病、ALS</strong>等蛋白构象病（proteopathies）</li>
</ul>
<h2>技术主张：从「有无」到「分型 + 定量」</h2>
<p>现行<strong>种子扩增检测（SAA）</strong>只能给出聚集体「有 / 无」的<strong>定性</strong>信号。
seragy 的 SeRAS 平台主张做到<strong>聚集体分型 + 定量</strong>的「法医式」报告，
服务场景是药物开发者的<strong>入组分层与疗效读数</strong>——也就是把生物标志物
从诊断工具前移到试验工具。</p>
<h2>为什么这条属于衰老情报</h2>
<p>蛋白稳态（proteostasis）崩塌是衰老的核心标志之一，而「能量化聚集负荷」长期是
该领域的测量瓶颈。平台若能稳定给出定量读数，直接影响的是<strong>干预试验有没有可用的中期终点</strong>。</p>
<h2>局限与待核实</h2>
<ul>
<li>混合融资中股权部分占比<strong>未披露</strong>；公告未给出 valuation 与分期安排</li>
<li>SeRAS 的定量性能目前仅见<strong>公司自述</strong>，尚无独立复现或同行评议数据</li>
<li>周报明确本期<strong>窗口内没有衰老方向的股权融资</strong>，本条属「债权 + 公共资金 + 股权」混合，不应被读成 VC 回归</li>
</ul>""",
    src("2026-10-28", "公司稿（BioSpace 新闻发布页）",
        "https://www.biospace.com/press-releases/seragy-launches-with-12-million-financing-to-advance-quantitative-biomarkers-for-neurodegenerative-diseases",
        "LT：https://longevity.technology/news/seragy-raises-13-4m-for-protein-clumps/"))

# ── §2 #2 · VeriSIM Life / ARPA-H ────────────────────────────────────
add("VeriSIM-Life-ARPA-H-6-5M-Cell-Preservation-Biostabilization-2026.html",
    "VeriSIM Life 拿到至多 650 万美元政府资助：把「活细胞保存」从冷链依赖里解出来",
    "方法与工具", "2026-10-28",
    "ARPA-H 项目参与方联合体（DesiCorp 牵头）获至多 $6.5M 政府资助，VeriSIM 提供机制性 AI 与 "
    "BIOiSIM 平台做预测性生物建模，目标是摆脱超低温冷链依赖的活细胞保存/储存/运输。",
    """<h2>要点</h2>
<ul>
<li><strong>类型</strong>：<strong>政府资助计划</strong>（ARPA-H 项目参与方），非股权融资</li>
<li><strong>金额</strong>：<strong>至多 $6.5M</strong></li>
<li><strong>联合体</strong>：由 <strong>DesiCorp</strong> 牵头，含 <strong>Ossium Health、Via Therapeutics、
University of Louisville、University of Texas at Austin</strong>；<strong>VeriSIM Life</strong> 提供机制性 AI 与 <strong>BIOiSIM</strong> 平台</li>
<li><strong>方向</strong>：<strong>活细胞保存 / 储存 / 运输</strong>（生物稳定化与生物制造），目标是摆脱超低温冷链依赖</li>
<li><strong>时间</strong>：BusinessWire <strong>2026-10-26</strong>；LT 报道 <strong>2026-10-28</strong></li>
</ul>
<h2>与衰老的关联</h2>
<p>细胞与组织保存是<strong>细胞治疗、生物样本库与再生医学的底层瓶颈</strong>。
衰老领域的多数工程化路线（干细胞、部分重编程、CAR 类 senolytic）最终都要落地到
「细胞能不能在不掉活性的前提下被运到患者手里」。冷链是这个链条上最贵也最脆的一环。</p>
<h2>值得记的一点</h2>
<p>这是 VeriSIM <strong>从药物发现外溢到 biostabilization / biomanufacturing</strong> 的第一步——
一家做 AI 药物建模的公司被拉进保存问题，说明<strong>瓶颈已经从「发现分子」移到了「把活体产物送到床边」</strong>。</p>
<h2>局限</h2>
<ul>
<li>资助为「至多」额度，未披露到款节奏与里程碑条件</li>
<li>技术目标（摆脱超低温冷链）为<strong>计划目标</strong>，未见已发表的性能数据</li>
</ul>""",
    src("2026-10-28", "BusinessWire 原稿",
        "https://www.businesswire.com/news/home/20261026451468/en/VeriSIM-Life-Powers-the-AI-Behind-Next-Generation-Cell-Preservation",
        "LT：https://longevity.technology/news/verisim-life-powers-ai-for-next-generation-cell-preservation/"))

# ── §2 #3 + §4 #3 + §5 #3 · Celularity × Vesalius（8-K 同一份） ──────
add("Celularity-Vesalius-Peptide-API-US-cGMP-PCAC-503A-2026.html",
    "Celularity × Vesalius 建美国本土多肽 API 终段产能：一份把监管假设写进条款的商业合同",
    "产业", "2026-10-29",
    "SEC 8-K（2026-10-29）披露 Celularity 与 Vesalius Longevity Labs 签署独家生产与供应协议，"
    "在新泽西 Florham Park 建美国本土首个 Peptual® 多肽 API 终段生产平台，"
    "供货前提明确写为 FDA 依 PCAC 建议将多肽纳入 503A 可 compounding 散装物质名单；明确排除 GLP-1。",
    """<h2>协议要点</h2>
<ul>
<li><strong>双方</strong>：Celularity Inc.（NASDAQ: CELU）× <strong>Vesalius Longevity Labs Inc.</strong></li>
<li><strong>类型</strong>：独家<strong>生产与供应协议</strong>（BD / 产能型，<strong>非股权融资</strong>），对价未披露</li>
<li><strong>内容</strong>：在新泽西 <strong>Florham Park</strong> 工厂承担多肽原料的<strong>下游纯化、加工、分析与放行</strong>，建立美国本土首个 <strong>Peptual® 多肽 API 终段生产与供应平台</strong>，批次级可追溯</li>
<li><strong>关键条款</strong>：<em>若</em> FDA 依 <strong>PCAC</strong> 建议把多肽加入 <strong>503A 可 compounding 散装物质名单</strong>，双方<em>即</em>向持牌美国 compounding 药房供货</li>
<li><strong>明确排除</strong>：<strong>GLP-1 受体激动剂及其他减重多肽</strong></li>
<li><strong>背景动因</strong>：FDA 已公开提示<strong>未经核实的境外来源多肽 API</strong>的质量与溯源风险</li>
<li><strong>时间</strong>：SEC 8-K 附件 99.1，<strong>2026-10-29</strong></li>
</ul>
<h2>三方角色：一条「科学信誉 + 供应链合规」的双轨</h2>
<p>同一份 8-K 还披露了 Vesalius 的人事配置：<strong>Micheal Roizen, M.D.</strong>（此前任
<strong>克利夫兰诊所健康中心 Wellness 主任</strong>）出任<strong>首席科学顾问</strong>，
<strong>Pradeep Albert</strong> 任 CEO。一家多肽长寿品牌把「前克利夫兰诊所健康中心主任」
放在首席科学顾问位，同时配本土 cGMP 产能——<strong>科学信誉与供应链合规被打包出售</strong>，这是本期最典型的商业设计。</p>
<h2>为什么这条要单列</h2>
<p>一家纳斯达克挂牌的「再生长寿」公司<strong>把营收预期挂在一份尚未发生的监管决定上</strong>。
这不是隐喻：合同文本里写的是条件句。对研究者而言，它的情报价值在于——
<strong>PCAC 对多肽散装物质的处置，已经有人用真金白银的产能押注了</strong>。</p>
<h2>局限与待核实</h2>
<ul>
<li><strong>对价、供货量、期限均未披露</strong>，仅知为收入型合作</li>
<li>触发条件<strong>尚未发生</strong>：FDA 是否采纳 PCAC 建议、何时采纳，无公开日期</li>
<li>多肽类干预的<strong>临床证据基础未在 8-K 中讨论</strong>，本协议只解决供应链与合规，不构成疗效主张</li>
</ul>""",
    src("2026-10-29", "SEC 8-K 附件 99.1",
        "https://www.sec.gov/Archives/edgar/data/1752828/000149315226049203/ex99-1.htm",
        "法规原文 21 CFR 216.23：https://www.ecfr.gov/current/title-21/chapter-I/subchapter-C/part-216/section-216.23"))

# ── §3 #2 · XellSmart XS411 ──────────────────────────────────────────
add("XellSmart-XS411-iPSC-Dopaminergic-Phase1-MDS-2026.html",
    "XellSmart XS411：I 期 9 例「良好 ON 时间」平均增加 5 小时以上，II 期 30 例盲态入组完成",
    "神经退行", "2026-10-27",
    "现货型 iPSC 来源多巴胺能前体细胞移植治疗帕金森病：I 期 9 例单次移植后 6 个月平均每日"
    "「良好 ON 时间」增加 >5 小时；II 期 30 例盲态入组已完成，结果于 MDS 年会披露。",
    """<h2>数据</h2>
<ul>
<li><strong>资产</strong>：<strong>XS411</strong>——<strong>现货型（off-the-shelf）iPSC 来源多巴胺能前体细胞</strong>移植</li>
<li><strong>I 期</strong>：<strong>9 例</strong>，病程约 <strong>10 年</strong>、Hoehn–Yahr 关期 <strong>3–4 级</strong>；单次移植后 <strong>6 个月</strong>，平均每日「良好 ON 时间」<strong>增加 &gt;5 小时</strong></li>
<li><strong>II 期</strong>：<strong>30 例</strong>，<strong>盲态入组已完成</strong>，结果于 <strong>MDS 年会</strong>披露</li>
<li><strong>变更标记</strong>：<strong>⬆</strong>（Phase I 数据读出 + Phase II 入组完成）</li>
<li><strong>时间</strong>：PRNewswire <strong>2026-10-18</strong>；LT 报道 <strong>2026-10-27</strong></li>
</ul>
<h2>怎么读这个数字</h2>
<p>「每日良好 ON 时间 +5 小时」是<strong>患者可感知的功能终点</strong>，而不是替代指标。
但必须同时读分母：<strong>n=9、单臂、无对照、随访 6 个月</strong>。
在帕金森病这种症状波动大、安慰剂效应显著的疾病里，单臂小样本的功能改善
<strong>只能算概念验证，不能算疗效确立</strong>。</p>
<h2>真正的看点</h2>
<p>「现货型 iPSC」意味着<strong>细胞治疗从个体化制备走向标准化产品</strong>——
这与自体或基因编辑路线是两条不同的产业化路径。若能成立，成本与可及性的量级会完全不同。</p>
<h2>局限与待核实</h2>
<ul>
<li>I 期<strong>未设对照</strong>，未见统计值与置信区间披露</li>
<li>II 期结果<strong>仅在会议披露</strong>（MDS 年会），未见同行评议全文</li>
<li>周报未给出试验登记号（无 NCT），来源为公司新闻稿</li>
</ul>""",
    src("2026-10-27", "PRNewswire 原稿",
        "https://www.prnewswire.com/news-releases/new-progress--xellsmart-unveiled-phase-i-results-of-off-the-shelf-parkinsons-disease-cell-therapy-at-mds--completed-blinded-phase-ii-enrollment-302911915.html",
        "LT：https://longevity.technology/news/xellsmarts-parkinsons-cell-shot-adds-5-good-hours-a-day/"))

# ── §3 #3 · Sironax SIR4156 ──────────────────────────────────────────
add("Sironax-SIR4156-NAMPT-Activator-Phase2-Obesity-Enrollment-2026.html",
    "Sironax SIR4156 二期入组约 50%：NAMPT 激活剂与司美格鲁肽联用，目标是「减脂不减肌」",
    "NAD+与sirtuin", "2026-10-27",
    "首创口服变构 NAMPT 激活剂 SIR4156（NAD+ 补救合成通路限速酶）Phase 2 入组进度约 50%，"
    "与司美格鲁肽联用、目标为减脂同时保瘦体重；试验登记号 ACTRN12626001033336。",
    """<h2>要点</h2>
<ul>
<li><strong>资产</strong>：<strong>SIR4156</strong>——首创、口服<strong>变构 NAMPT 激活剂</strong>（<strong>NAD+ 补救合成通路限速酶</strong>）</li>
<li><strong>适应症与设计</strong>：<strong>肥胖</strong>，与<strong>司美格鲁肽联用</strong>；全球双盲随机安慰剂对照平行组试验</li>
<li><strong>阶段与进度</strong>：<strong>Phase 2</strong>（阶段维持），<strong>入组进度约 50%</strong></li>
<li><strong>登记号</strong>：<strong>ACTRN12626001033336</strong>（澳新注册库，<strong>非 ClinicalTrials.gov</strong>）</li>
<li><strong>主要目的</strong>：评估对<strong>身体脂肪量与身体成分</strong>的影响</li>
<li><strong>时间</strong>：公司稿 <strong>2026-10-13</strong>；LT 报道 <strong>2026-10-27</strong></li>
</ul>
<h2>为什么值得盯</h2>
<p>NAD+ 领域过去十几年主要在<strong>前体</strong>（NR / NMN / NMNH）上做文章，
而 <strong>NAMPT 是补救合成通路的限速酶</strong>——直接激活限速酶是<strong>通路层面的另一条路</strong>，
理论上绕开了前体补充的剂量与转化瓶颈。</p>
<p>适应症选在<strong>肥胖 / 身体成分</strong>而不是「衰老」，与本期周报的整体判断一致：
<strong>资本与开发都在找可获批的近期适应症</strong>，机制是衰老相关，标签不是。</p>
<h2>局限与待核实</h2>
<ul>
<li>登记在 <strong>ANZCTR</strong> 而非 ClinicalTrials.gov，跨库检索时容易漏掉</li>
<li>入组约 50%，<strong>无中期数据</strong>；主要终点为身体成分，非衰老终点</li>
<li>NAMPT 激活的<strong>长期安全性</strong>（NAD+ 通路的促增殖顾虑）未见公开讨论</li>
</ul>""",
    src("2026-10-27", "Sironax 公司官网稿",
        "https://www.sironax.com/sironax-advances-enrollment-in-phase-2-forge-lm-obesity-trial-of-nampt-activator-sir4156/",
        "试验登记：ACTRN12626001033336"))

# ── §3 #4 + §5 #1 · Voyager ──────────────────────────────────────────
add("Voyager-VY1706-VY7523-CTAD-2026-CEO-Succession-2026.html",
    "Voyager 把 CEO 交接绑在 VY1706 的数据读出上：tau 双资产进 CTAD 海报，治理安排同步披露",
    "神经退行", "2026-10-27",
    "VY1706（tau 靶向基因治疗）与 VY7523（抗 tau 抗体）入选 CTAD 2026（11-16~19，波士顿）两项海报；"
    "8-K 明确 Robin Swartz 将在 2027 Q1 取得 VY1706 早期 AD 初始急性安全性数据后接任 CEO。",
    """<h2>资产与会议</h2>
<ul>
<li><strong>VY1706</strong>：tau 靶向<strong>基因治疗</strong>，降低 tau 生成；早期 AD 临床中</li>
<li><strong>VY7523</strong>：<strong>抗 tau 抗体</strong></li>
<li><strong>会议</strong>：两项 <strong>CTAD 2026 海报</strong>（第 19 届临床试验大会，<strong>2026-11-16 ~ 11-19，波士顿</strong>）</li>
<li><strong>变更标记</strong>：<strong>🔄</strong> 阶段维持，仅披露更新；<strong>无阶段变化</strong></li>
<li><strong>时间</strong>：GlobeNewswire <strong>2026-10-27</strong>；LT 报道 <strong>2026-10-29</strong></li>
</ul>
<h2>治理安排：把 succession 写成一个具体终点</h2>
<ul>
<li><strong>Robin Swartz</strong>（56 岁）出任<strong>总裁</strong>（即刻生效），预计接替 <strong>Alfred W. Sandrock, Jr., M.D., Ph.D.</strong> 出任 CEO；Sandrock 预计留任董事</li>
<li>Swartz 现任<strong>首席商务官兼首席运营官</strong>（2024-11 起），2026-05 起兼任 <strong>Principal Financial Officer 兼 Treasurer</strong>；此前在 Genzyme / Sanofi Genzyme 任职逾 20 年</li>
<li><strong>董事会决议 2026-10-20，8-K 申报 2026-10-21</strong>（items 5.02 / 9.01）</li>
<li><strong>触发条件</strong>：在 <strong>2027 Q1</strong> 取得 <strong>VY1706 早期 AD 初始急性安全性数据</strong>后完成交接</li>
</ul>
<h2>为什么这条不只是一则人事新闻</h2>
<p>把<strong>管理层交接的触发条件写成单一试验的具体终点</strong>，是相当少见的治理设计：
它等于公司<strong>对外押注了 VY1706 的时间表</strong>。对外部观察者来说，
这提供了两个可读的信号——一是公司对 2027 Q1 读出有内部把握，
二是<strong>该数据被视为公司级分水岭</strong>。</p>
<h2>局限与待核实</h2>
<ul>
<li>CTAD 海报为<strong>会议披露</strong>，未见完整数据；海报标题与结果未在周报中给出</li>
<li>「2027 Q1」为公司<strong>预期时间</strong>，临床读出延期是常态</li>
<li>无阶段推进（🔄），本条不构成疗效证据</li>
</ul>""",
    src("2026-10-27", "GlobeNewswire 原稿（CTAD）+ SEC 8-K（治理）",
        "https://www.globenewswire.com/news-release/2026/10/27/3388959/36461/en/voyager-s-tau-targeted-gene-therapy-vy1706-and-anti-tau-antibody-vy7523-for-alzheimer-s-disease-to-be-featured-in-poster-presentations-at-ctad-2026.html",
        "SEC 8-K：https://www.sec.gov/Archives/edgar/data/1640266/000119312526427224/d157795d8k.htm"))

# ── §3 #6 + §4 #1 · United Therapeutics SUMMIT ───────────────────────
add("United-Therapeutics-Treprostinil-SMI-SUMMIT-PH-COPD-IND-2026.html",
    "United Therapeutics 吸入型 Treprostinil 获 FDA IND 放行：一个长期被漏诊的 40 万~80 万人群",
    "器官衰老", "2026-10-29",
    "FDA 放行 United Therapeutics 的 IND，允许开展 SUMMIT 试验：手持软雾吸入器给药的吸入型"
    "前列环素类似物治疗 COPD 相关肺动脉高压（PH-COPD），Phase 2，约 40 例，每日 4 次、每次 1 吸。",
    """<h2>要点</h2>
<ul>
<li><strong>资产</strong>：<strong>Treprostinil SMI</strong>——手持<strong>软雾吸入器</strong>给药的吸入型前列环素类似物（肺血管扩张）</li>
<li><strong>适应症</strong>：<strong>COPD 相关肺动脉高压（PH-COPD）</strong></li>
<li><strong>阶段</strong>：<strong>Phase 2</strong>（FDA IND 已放行），约 <strong>40 例</strong></li>
<li><strong>试验名 / 方案</strong>：<strong>SUMMIT</strong>；<strong>每日 4 次、每次 1 吸</strong></li>
<li><strong>人群估计</strong>：公司估计美国 PH-COPD 人群 <strong>40 万 ~ 80 万人</strong></li>
<li><strong>时间</strong>：公司 IR 稿 <strong>2026-10-19</strong>；LT 报道 <strong>2026-10-29</strong></li>
</ul>
<h2>为什么 PH-COPD 长期被漏诊</h2>
<p>两个结构性原因：一是 <strong>PH-COPD 症状与 COPD 高度重叠</strong>；
二是<strong>稳定期 COPD 不推荐做右心导管检查</strong>（确诊金标准）。
结果是一个<strong>公司估计达数十万量级的人群长期没有专门的 IND 路径</strong>。</p>
<h2>剂型的意义</h2>
<p>软雾吸入把前列环素类的使用门槛<strong>从静脉 / 皮下推进到 handheld</strong>。
剂型变化不改机制，但直接改变「谁能用、在哪用、能不能长期用」。</p>
<h2>与衰老的关联</h2>
<p>COPD 与肺血管重塑是<strong>典型的器官衰老表型</strong>，人群基数大、年龄梯度陡。
本条的定位是<strong>器官衰老适应症边界的扩张</strong>，而非系统性抗衰老干预。</p>
<h2>局限与待核实</h2>
<ul>
<li>周报未给出 <strong>NCT 登记号</strong>（公司 IR 稿未提供），来源为公司 IR</li>
<li>「40 万~80 万」为<strong>公司估计</strong>，非流行病学调查实测值</li>
<li>Phase 2、约 40 例，<strong>尚无疗效数据</strong></li>
</ul>""",
    src("2026-10-29", "United Therapeutics 公司 IR 稿",
        "https://ir.unither.com/press-releases/2026/10-19-2026-120012353",
        "LT：https://longevity.technology/news/fda-clears-soft-mist-inhaler-trial-for-lung-disease/"))

# ── §3 #7 + §4 #2 + §5 #2 · Opus Genetics ────────────────────────────
add("Opus-Genetics-OPGx-RDH12-IND-Clearance-CSO-Appointment-2026.html",
    "Opus Genetics：RDH12 基因治疗 IND 放行（上期漏项补录），同期任命 CSO",
    "临床与转化", "2026-10-29",
    "FDA 放行 OPGx-RDH12（AAV 基因增补，RDH12 相关 Leber 先天性黑蒙）IND，计划本季度启动 "
    "Phase 1/2；公司同期任命 Andrew Murphy 为 CSO、Jamie Lynne Hart 为 Executive Director。",
    """<h2>IND 放行（公告日 2026-10-21，上期漏项补录）</h2>
<ul>
<li><strong>资产</strong>：<strong>OPGx-RDH12</strong>——<strong>AAV 基因增补治疗</strong></li>
<li><strong>适应症</strong>：<strong>RDH12 相关 Leber 先天性黑蒙（RDH12-LCA）</strong>，儿童期起病的进行性视力丧失</li>
<li><strong>进展</strong>：<strong>FDA IND 放行 → 本季度启动 Phase 1/2</strong>（CEO George Magrath 口径）</li>
<li><strong>合作方</strong>：<strong>Global RDH12 Alliance</strong>（美国 RDH12 Fund for Sight + 英国 Eyes on the Future，2025-07 建立）</li>
<li><strong>管线位置</strong>：公司<strong>第 3 个进入临床开发</strong>的基因治疗项目</li>
</ul>
<h2>人事（2026-10-29）</h2>
<ul>
<li><strong>Andrew Murphy, Ph.D.</strong> 任<strong>首席科学官</strong>：18 年以上生物技术经验，此前任 <strong>Kriya Therapeutics</strong> 研究与早期开发 SVP（负责 AAV 载体设计、研究、基因组学与数据科学），职业生涯中支持 <strong>7 个项目完成 I 期 IND/CTA 递交</strong>（其中 5 个在 Kriya）</li>
<li><strong>Jamie Lynne Hart, M.S., M.P.H.</strong> 任 <strong>Executive Director, Executive Operations</strong>：15 年以上经验，此前任 <strong>Apellis Pharmaceuticals（现 Biogen）CEO 幕僚长</strong></li>
<li><strong>公司现状</strong>：管理 <strong>7 条 AAV 管线</strong></li>
</ul>
<h2>模式意义</h2>
<p><strong>「患者组织筹资 + 联盟化开发」正在成为超罕见儿科适应症的标准打法</strong>——
Global RDH12 Alliance 由两地患者组织联合构成，2025-07 建立，不到一年半推进到 IND 放行。</p>
<h2>局限与待核实</h2>
<ul>
<li>周报<strong>未提供 NCT 登记号</strong>（IND 阶段）；「本季度启动」为公司口径，无精确日期</li>
<li>本条为<strong>上期漏项补录</strong>（公告日 10-21 落在上期窗口内未收录），已在本期标注</li>
<li>RDH12-LCA 属<strong>罕见儿科单基因病</strong>，与系统性衰老机制无关，列入管线表是因 AAV 平台能力相通</li>
</ul>""",
    src("2026-10-29", "Opus Genetics 公司 IR 原稿（IND）／公司 IR（人事）",
        "https://ir.opusgtx.com/press-releases/detail/547/opus-genetics-announces-fda-clearance-of-ind-application-for-opgx-rdh12",
        "人事：https://ir.opusgtx.com/press-releases/detail/548/opus-genetics-appoints-dr-andrew-murphy-as-chief-scientific-officer-and-jamie-lynne-hart-as-executive-director-executive-operations"))

# ── §3 #8 · NCT06889740 ──────────────────────────────────────────────
add("NMNH-Ca-NCT06889740-Completed-Healthy-Adults-2026.html",
    "NMNH-Ca 健康成人试验状态更新为已完成：NAD+ 前体类补充剂少有的一次登记库闭环",
    "NAD+与sirtuin", "2026-10-27",
    "EffePharm（UthPeak）的 NMNH-Ca（还原型 β-烟酰胺单核苷酸钙盐）试验 NCT06889740 "
    "在 ClinicalTrials.gov 状态更新为 COMPLETED（记录最后更新 2026-10-27），n≈80，健康成人。",
    """<h2>要点</h2>
<ul>
<li><strong>干预</strong>：<strong>NMNH-Ca</strong>——<strong>还原型 β-烟酰胺单核苷酸钙盐</strong>，NAD+ 前体类补充剂</li>
<li><strong>适应症 / 人群</strong>：<strong>健康衰老</strong>（健康成人），<strong>n≈80</strong></li>
<li><strong>类型</strong>：<strong>补充剂类干预性研究</strong>（非药物注册路径）</li>
<li><strong>登记号</strong>：<strong>NCT06889740</strong></li>
<li><strong>状态变更</strong>：<strong>COMPLETED</strong>（记录最后更新 <strong>2026-10-27</strong>）</li>
<li><strong>研究目的</strong>：评估 NMNH-Ca 在健康成人中的<strong>安全性、耐受性与有效性</strong></li>
<li><strong>变更标记</strong>：<strong>⬆</strong>（状态推进至完成）</li>
</ul>
<h2>怎么读「COMPLETED」</h2>
<p>状态更新为已完成<strong>不等于结果公布</strong>：ClinicalTrials.gov 的 COMPLETED 只表示
<strong>研究活动结束</strong>，结果条目可能尚未提交。NAD+ 前体这一大类里，
<strong>登记并完成</strong>的干预性研究数量本就不多，因此这条记录本身有索引价值。</p>
<h2>与衰老情报的关系</h2>
<p>NMNH 是 NMN 的还原型衍生物，属<strong>消费补充剂与临床研究交界</strong>地带。
对研究者而言，它的价值在于：<strong>这是少数能进登记库、有明确 n 与安全终点的前体类试验</strong>，
而不是另一份「据称有效」的营销材料。</p>
<h2>局限与待核实</h2>
<ul>
<li>记录更新至 2026-10-27，<strong>未见结果发布</strong>（results 未 posted）</li>
<li>n≈80、健康成人、补充剂类，<strong>证据强度远低于药物试验</strong></li>
<li>「健康衰老」为登记条件表述，<strong>非可获批适应症</strong></li>
</ul>""",
    src("2026-10-27", "ClinicalTrials.gov 记录 NCT06889740",
        "https://clinicaltrials.gov/study/NCT06889740",
        "状态：COMPLETED（最后更新 2026-10-27）"))

# ── §4 #3 · FDA / PCAC 503A（监管角度单列） ──────────────────────────
add("FDA-PCAC-503A-Peptide-Bulk-Substances-Compounding-2026.html",
    "FDA 的 503A 散装物质名单为何牵动多肽产业：21 CFR 216.23 与一条尚未发生的监管决定",
    "产业", "2026-10-29",
    "Celularity×Vesalius 的 8-K 把供货前提写为 FDA 依 PCAC 建议将多肽纳入 503A 可 compounding "
    "散装物质名单；法规依据为 21 CFR 216.23。日期未公开，是本期最需持续跟踪的监管变量。",
    """<h2>法规框架</h2>
<ul>
<li><strong>法规原文</strong>：<strong>21 CFR 216.23</strong>——依 503A 可用于 compounding 的散装药物物质名单</li>
<li><strong>现行状态</strong>：FDA 已公开提示<strong>未经核实的境外来源多肽 API</strong>的质量与溯源风险，并要求 compounding 药房核验供应商</li>
<li><strong>待决事项</strong>：<strong>PCAC</strong>（Pharmacy Compounding Advisory Committee）建议的多肽纳入名单，<strong>FDA 是否采纳、何时采纳均无公开日期</strong></li>
</ul>
<h2>商业侧已经先行</h2>
<p>本期最反常的一条不是监管文件本身，而是<strong>商业合同把它写成了条件句</strong>：
Celularity 与 Vesalius 约定，<em>若</em> FDA 依 PCAC 建议把多肽加入 503A 名单，
双方<em>即</em>向持牌美国 compounding 药房供货，并明确<strong>排除 GLP-1 及减重多肽</strong>。
换言之，<strong>产能已经建起来了，等的是一个尚未发生的决定</strong>。</p>
<h2>对研究者的意义</h2>
<p>多肽类「长寿」干预在美国的主要可及渠道，很大程度取决于<strong>compounding 药房能不能合法配制</strong>。
这条名单的走向，会直接决定一批多肽干预是<strong>合规可及</strong>还是<strong>转入灰市</strong>。
在证据层面它不改变任何疗效结论，但在<strong>暴露人群规模与质量可控性</strong>上是决定性的。</p>
<h2>局限与待核实</h2>
<ul>
<li><strong>日期未公开</strong>，本期无法给出预期时间表，仅能标注「持续跟踪」</li>
<li>周报注明 <strong>fda.gov 在本运行环境下大面积不可达</strong>（PCAC 会议页等返回 404 / 401），本条以 <strong>eCFR 法规原文 + SEC 8-K</strong> 交叉确认，未直接引 FDA 页面</li>
</ul>""",
    src("2026-10-29", "eCFR 法规原文 21 CFR 216.23",
        "https://www.ecfr.gov/current/title-21/chapter-I/subchapter-C/part-216/section-216.23",
        "商业背景（SEC 8-K）：https://www.sec.gov/Archives/edgar/data/1752828/000149315226049203/ex99-1.htm"))

# ── §4 #4 + #5 · 两条联邦公报 ────────────────────────────────────────
add("FDA-Advisory-Committee-Nominations-CTGTAC-Renewal-2026.html",
    "FDA 咨询委员会两则制度性动态：提名截止 11-16，CTGT 委员会续期至 2028-10-28",
    "产业", "2026-10-29",
    "联邦公报 FR 2026-20065：咨询委员会成员与消费者组织提名材料截止 2026-11-16；"
    "FR 2026-20989：细胞、组织与基因治疗咨询委员会（CTGT AC）章程续期至 2028-10-28。",
    """<h2>一、提名征集（FR 2026-20065）</h2>
<ul>
<li><strong>文件</strong>：<em>Request for Nominations for Individuals and Consumer Organizations for Advisory Committees</em></li>
<li><strong>发布</strong>：联邦公报 <strong>2026-10-01</strong></li>
<li><strong>截止</strong>：<strong>2026-11-16</strong>；受理本届及 <strong>2026-12-31</strong> 前可能出现或已经出现的空缺</li>
<li><strong>涵盖委员会</strong>：FDA Science Board、Pediatrics AC、Blood Products AC、<strong>Cellular, Tissue and Gene Therapies AC</strong>、Vaccines and Related Biological Products AC 等</li>
</ul>
<h2>二、CTGT AC 续期（FR 2026-20989）</h2>
<ul>
<li><strong>发布</strong>：联邦公报 <strong>2026-10-14</strong></li>
<li><strong>内容</strong>：<strong>Cellular, Tissue and Gene Therapies Advisory Committee</strong> 章程有效期延续至 <strong>2028-10-28</strong></li>
</ul>
<h2>为什么值得记</h2>
<p>咨询委员会的<strong>人事结构会直接影响未来 1~2 年基因/细胞治疗类衰老资产的评审口径</strong>。
部分重编程、AAV 递送、细胞治疗这几条路线，最终都要过 <strong>CTGT AC</strong> 这一关。
续期意味着<strong>未来两年该通道的制度连续性是可预期的</strong>；提名窗口则是一个
<strong>可从监管原文确认的具体日期型事件</strong>——在本期 FDA 官网大面积不可达的情况下，
这是少数能给出确切日期的监管信息。</p>
<h2>局限</h2>
<ul>
<li>提名征集为<strong>程序性事件</strong>，不涉及任何具体产品的审评结论</li>
<li>周报注明 <strong>FDA 官网咨询委员会日历页、PCAC 会议页均返回 404 / 401</strong>，
「未来 30 天 FDA 咨询委员会会议日程」<strong>无法从监管原文确认</strong>，本期改用联邦公报交叉补位</li>
</ul>""",
    src("2026-10-29", "联邦公报原文 FR 2026-20065 / FR 2026-20989",
        "https://www.federalregister.gov/documents/2026/10/01/2026-20065/request-for-nominations-for-individuals-and-consumer-organizations-for-advisory-committees",
        "CTGT AC 续期：https://www.federalregister.gov/documents/2026/10/14/2026-20989/advisory-committee-cellular-tissue-and-gene-therapies-advisory-committee-renewal"))

# ── §4.1 · 未来 30 天日历 ────────────────────────────────────────────
add("Longevity-Regulatory-Data-Calendar-2026-11-01-to-11-30.html",
    "未来 30 天要看什么：CTAD 双海报、AHA late-breaking 与 11 月 PDUFA 窗口（2026-10-30 ~ 11-29）",
    "产业", "2026-10-30",
    "本期周报 §4.1 列出 7 项未来 30 天预期事件：Longeveron AHA 2026（11-08）、FDA 提名截止（11-16）、"
    "CTAD 2026 波士顿（11-16~19）、11 月 PDUFA 窗口、Opus Phase 1/2 启动（Q4）、Voyager VY1706 读出（2027 Q1）。",
    """<h2>日程（按预计日期）</h2>
<ul>
<li><strong>2026-11-08</strong>：<strong>Longeveron</strong> 在 <strong>AHA 2026 年会</strong>做 late-breaking 报告，公布 <strong>Laromestrocel ELPIS II（HLHS）</strong>更新结果。上期已记 ⬇（主要终点未达、MACE 次要终点显著）</li>
<li><strong>2026-11-16</strong>：<strong>FDA 咨询委员会成员与消费者组织提名截止</strong>（FR 2026-20065，联邦公报原文）</li>
<li><strong>2026-11-16 ~ 11-19</strong>：<strong>CTAD 2026</strong>（第 19 届阿尔茨海默病临床试验大会，波士顿）——<strong>Voyager</strong> 的 <strong>VY1706</strong> 与 <strong>VY7523</strong> 两项海报</li>
<li><strong>2026-11 月内</strong>：<strong>PDUFA 目标日期窗口</strong>——Agios mitapivat（11-01）；Cytokinetics aficamten、BioAtla、Summit（11-14）；Capricor Deramiocel（HOPE-3，自 8-22 推迟）与 Sera Prognostics MOLBREEVI（11-22）；BridgeBio BBP-418（11-27）；Cogent、Roche giredestrant、Vertex povetacicept（11-30）。<strong>多为非衰老适应症</strong>，作为监管节奏参照</li>
<li><strong>2026 Q4 内</strong>：<strong>Opus Genetics</strong> 计划启动 <strong>OPGx-RDH12 Phase 1/2</strong>（公司口径，无精确日期）</li>
<li><strong>2027 Q1</strong>（超出 30 天，列为后续关键触发点）：<strong>Voyager VY1706</strong> 早期 AD 初始急性安全性数据——8-K 明确此为 <strong>Robin Swartz 接任 CEO 的触发条件</strong></li>
<li><strong>待定</strong>：<strong>FDA / PCAC 对多肽散装物质（503A）名单的后续处置</strong>，即 Celularity×Vesalius 合同的生效前提</li>
</ul>
<h2>这份日历的可靠性边界</h2>
<p>必须区分三类来源性质：<strong>①</strong> 联邦公报原文（提名截止 11-16）——可直接采信；
<strong>②</strong> 公司公告/预告（Longeveron、CTAD、Opus、Voyager）——公司口径，可能延期；
<strong>③</strong> <strong>pdufa.bio 聚合日历</strong>——<strong>非监管原文，需以公司公告或 FDA 原文复核</strong>。</p>
<h2>局限</h2>
<p>周报明确：<strong>FDA 官网在本运行环境下大面积不可达</strong>（咨询委员会日历页、PCAC 会议页、
新闻公告页均返回 404 / 401；fda.gov IND 申请页返回 401）。
因此「未来 30 天 FDA 咨询委员会会议日程」<strong>无法从监管原文确认</strong>，
本表是联邦公报 + eCFR + 聚合日历交叉补位的结果。</p>""",
    src("2026-10-30", "行业情报周报 2026-10-30 §4.1（联邦公报原文 / 公司公告 / pdufa.bio 聚合日历）",
        "https://www.federalregister.gov/documents/2026/10/01/2026-20065/request-for-nominations-for-individuals-and-consumer-organizations-for-advisory-committees",
        "CTAD：https://www.globenewswire.com/news-release/2026/10/27/3388959/36461/en/voyager-s-tau-targeted-gene-therapy-vy1706-and-anti-tau-antibody-vy7523-for-alzheimer-s-disease-to-be-featured-in-poster-presentations-at-ctad-2026.html ｜ PDUFA 聚合：https://pdufa.bio/"))

# ── §5 #4 · DEPH Labs ────────────────────────────────────────────────
add("DEPH-Labs-Lisa-Loud-CEO-Epigenetic-Biological-Age-Privacy-2026.html",
    "DEPH Labs 任命科技与隐私背景的 CEO：表观遗传年龄检测的重心移向「数据」而非「生物学」",
    "表观遗传时钟", "2026-10-23",
    "DEPH Holdings（伦敦 / 德州）任命 Lisa Loud 为 CEO（GlobeNewswire 2026-10-23，上期漏项补录）。"
    "公司主营单性别表观遗传生物年龄检测（UMMU 女性 / ENGNE 男性，居家唾液采样）。",
    """<h2>要点</h2>
<ul>
<li><strong>公司</strong>：<strong>DEPH Labs</strong>（母公司 DEPH Holdings, Inc.，英国伦敦 / 美国德州）</li>
<li><strong>变动</strong>：<strong>Lisa Loud</strong> 出任<strong>首席执行官</strong></li>
<li><strong>履历背景</strong>：此前在 <strong>Apple、PayPal、BitMEX、ShapeShift、Secret Network</strong> 任高级管理职位——<strong>科技 + 金融 + 区块链 + 数字隐私</strong>背景，<strong>非生命科学背景</strong></li>
<li><strong>业务</strong>：<strong>表观遗传生物年龄检测</strong>；自称建成全球首个<strong>完全基于单性别数据</strong>的表观遗传生物年龄平台，通过 <strong>UMMU</strong>（女性）与 <strong>ENGNE</strong>（男性）两个平台以<strong>居家唾液采样</strong>提供生物学年龄洞察</li>
<li><strong>时间</strong>：GlobeNewswire <strong>2026-10-23</strong>（<strong>上期漏项，本期补录</strong>）</li>
</ul>
<h2>值得记的不是任命本身，而是任命的方向</h2>
<p>一家做表观遗传年龄检测的公司，把 CEO 交给一位<strong>科技与数字隐私背景</strong>的管理者，
说明公司战略重心明确落在<strong>「数据隐私 + 消费者可及」</strong>，而不是生物学机制的深化。
这与本领域另一条路线（把时钟做成<strong>监管可接受的替代终点</strong>）形成对照——
<strong>同样是甲基化时钟，一边在做临床试验终点，一边在做消费产品</strong>。</p>
<h2>局限与待核实</h2>
<ul>
<li>周报未能取得 <strong>GlobeNewswire 原站链接</strong>（本次抓取返回 403），改用可点击的完整转载（ceo.ca 与 Yahoo Finance 均含全文），并在表中注明原站不可达</li>
<li>「全球首个完全基于单性别数据」为<strong>公司自述</strong>，无可核验的第三方验证</li>
<li>居家唾液采样的<strong>组织来源与时钟适用性</strong>（唾液 vs 血液甲基化时钟的一致性）未提供验证数据</li>
</ul>""",
    src("2026-10-23", "GlobeNewswire 原稿（完整转载，原站本次抓取返回 403）",
        "https://ceo.ca/@GlobeNewswire/deph-labs-appoints-lisa-loud-as-ceo-to-accelerate-privacy-centric",
        "同步转载：https://finance.yahoo.com/healthcare/articles/deph-labs-appoints-lisa-loud-as-ceo-193600730.html"))

# ── §7 + §8 · watchlist 留痕 ─────────────────────────────────────────
add("Longevity-Watchlist-25-Companies-Oct30-2026-No-Updates.html",
    "watchlist 25 家逐一核查：窗口内零更新，但其中 5 家官网已无法访问",
    "产业", "2026-10-30",
    "本期对 25 家重点公司逐一访问官方站点/新闻室/管线页：25/25 完成核查，2026-10-28~10-30 "
    "窗口内均无新增官方动态；其中 5 家官网异常（Retro、Juvenescence、Turn.bio、Unity、Rubedo）。",
    """<h2>核查结论</h2>
<p><strong>25 家全部完成核查；窗口内均无新增官方动态。其中 5 家官网异常，
构成证据缺口——「无更新」不等于「确认无进展」。</strong></p>
<h2>5 家官网异常（必须单列）</h2>
<ul>
<li><strong>Retro Biosciences</strong>：<code>retrobio.com</code> 为<strong>域名出售停放页</strong></li>
<li><strong>Juvenescence</strong>：<code>juvenescence.com</code> 为<strong>中文「该网站正在出售」停放页</strong></li>
<li><strong>Turn Biotechnologies</strong>：<code>turn.bio</code> 显示 <strong>Squarespace「Website Expired」</strong>（域名过期）</li>
<li><strong>Unity Biotechnology</strong>：官网 200，但明示<strong>已停止运营</strong>（结构性退出）</li>
<li><strong>Rubedo Life Sciences</strong>：<code>rubedolifesciences.com</code> <strong>DNS 解析失败</strong>，<code>rubedo.life</code> 超时</li>
</ul>
<h2>其余 20 家的可达性现状（部分节选）</h2>
<ul>
<li><strong>Altos Labs</strong>：<code>/news</code> 与 <code>/newsroom</code> 均 404，仅首页可读</li>
<li><strong>Life Biosciences</strong>：Cloudflare 拦截（403），改用新闻列表页；最新为 <strong>2026-10-08</strong> ER-100 首次人体数据</li>
<li><strong>NewLimit</strong>：Substack 可达；最新为 <strong>2026-10-21</strong>「2026 Summer」</li>
<li><strong>Calico（Alphabet）</strong>：press 页 200 但为 JS 渲染，<strong>无法解析发布日期</strong></li>
<li><strong>BioAge Labs</strong>：<code>/news</code> 404，根域 200；EDGAR（CIK 0001709941）<strong>无 ≥2026-10-20 的新申报</strong></li>
<li><strong>Loyal</strong>：<code>/posts</code> 404，根域 200，<strong>LOY-003 FDA 里程碑横幅仍在</strong></li>
<li><strong>Rejuvenate Bio</strong>：最新为 <strong>2026-06-08</strong>（$6M 融资 + Merck Animal Health）</li>
<li><strong>Intervene Immune</strong>：200，<strong>TRIIM-X（NCT04375657）</strong>在列</li>
<li><strong>Insilico Medicine</strong>：新闻页 200（JS 渲染），2026 年条目日期无法解析</li>
</ul>
<h2>本期数据缺口（周报 §7，如实转述）</h2>
<ul>
<li><strong>窗口内没有任何衰老/长寿方向的股权融资公告</strong>——本期投融资表 3 条分别是混合融资、政府资助、BD 与产能协议</li>
<li><strong>FDA 官网大面积不可达</strong>（404 / 401），改用联邦公报 + eCFR + 聚合日历交叉补位</li>
<li><strong>管线表中 4 条无 NCT 号</strong>（MTX325、Klothonova、OPGx-RDH12、Treprostinil SMI），来源为公司官方管线页/新闻稿</li>
<li><strong>DEPH Labs 未能取得 GlobeNewswire 原站链接</strong>（403），改用完整转载</li>
</ul>
<h2>为什么「无更新」也要成篇</h2>
<p>行业情报的价值不只在 ⬆。25 家的沉默、5 家官网的消失，
与本期各条进展<strong>同等重要</strong>——只报进展不报退场的行业记录是失真的。
同时必须保留周报的措辞边界：<strong>「无法从官方渠道确认」不等于「确认无新闻」</strong>。</p>""",
    src("2026-10-30", "行业情报周报 2026-10-30 §7 数据缺口 / §8 watchlist 主动盯梢留痕（25 家逐一访问）",
        "https://longevity.technology/news/",
        "基线快照见网盘行业层《管线状态基线》v1.1（26,020 B，实测非空）"))

# ── 周报速览 ─────────────────────────────────────────────────────────
add("Longevity-Industry-Weekly-W44-2026-10-30-Overview.html",
    "行业周报速览（2026-10-30）：两天窗口零股权融资，行业先把基础设施建起来",
    "产业", "2026-10-30",
    "2026-W44 第三次运行（窗口 10-28~10-30）：四表共 20 条，其中投融资 3、管线临床 8、监管 5、"
    "人才 4；本期最大结构性缺口是窗口内没有任何衰老方向的股权融资公告。",
    """<h2>本期速览五条</h2>
<ol>
<li><strong>两天窗口里，股权融资为零——但产能先动了。</strong>投融资表 3 条没有一条是衰老方向的股权融资：
一笔债权+股权+州政府补贴的混合包（seragy，€12M）、一笔 ARPA-H 牵头的政府资助（VeriSIM/DesiCorp，至多 $6.5M）、
一笔产能型 BD（Celularity×Vesalius）。<strong>在「衰老」还不是可获批适应症之前，行业先把基础设施建起来</strong>。</li>
<li><strong>最反常的一条：Celularity 把监管假设直接写进商业合同。</strong>8-K 原文明确写：
<em>若</em> FDA 依 PCAC 建议把多肽加入 503A 可 compounding 散装物质名单，双方<em>即</em>向持牌美国 compounding 药房供货，
同时明确排除 GLP-1。<strong>一家纳斯达克挂牌的「再生长寿」公司，把营收预期挂在一份尚未发生的监管决定上</strong>。</li>
<li><strong>线粒体质量控制（USP30 / mitophagy）首次进人。</strong>Mission Therapeutics MTX325 完成帕金森 1b 期首例给药
（英国皇家利物浦，36 例）。与 senolytics、部分重编程并列，衰老生物学的第三条工程化路径从「机制」走到「给人打针」。
<strong>注：内部站已于 10-21 刊出该快讯，本期按交接协议引用内部链接，不重新起草。</strong></li>
<li><strong>Klotho 第一次拿到「持续递送」的工程答案。</strong>Avaí Bio × Austrianova 的 Klothonova 用
Cell-in-a-Box 封装细胞，在体外实现可溶性 Klotho 的长期生成与分泌（<em>Frontiers in Aging</em>，10-28）。
Klotho 过去最大的拦路虎从来不是「有没有效」，而是<strong>半衰期和递送方式</strong>。
<strong>注：内部站 10-28 已刊综述，本期不重复起草。</strong></li>
<li><strong>Voyager 把 CEO 交接绑在数据读出上。</strong>8-K（10-21）写明：Robin Swartz 出任总裁，
将在 <strong>2027 Q1</strong> 取得 VY1706 早期 AD 初始急性安全性数据后接任 CEO。
<strong>把 succession 触发条件写成一个具体试验的具体终点，是不常见的治理设计</strong>。</li>
</ol>
<h2>四表统计</h2>
<ul>
<li>§2 投融资 <strong>3 条</strong>；§3 管线与临床 <strong>8 条</strong>（6 条 ⬆、2 条 🔄、<strong>无 ⬇</strong>）；§4 监管 <strong>5 条</strong>；§5 人才 <strong>4 条</strong></li>
<li>§4.1 未来 30 天预期事件 <strong>7 项</strong>；§6 待核实/降级 <strong>5 条</strong>（本期不成篇）</li>
<li><strong>来源自检</strong>：四表共 20 条，<strong>带链接 20 条，无链接 0 条</strong>；全文 34 条唯一 URL 定稿前逐条校验</li>
<li><strong>基线变更</strong>：《管线状态基线.json》v1.0（20 条）→ <strong>v1.1（28 条）</strong>，新增 8 条，既有 20 条窗口内无状态变更</li>
</ul>
<h2>本期最诚实的一句判断</h2>
<blockquote><p>窗口内<strong>没有出现任何衰老/长寿方向的股权融资公告</strong>。上期的判断
（资本为衰老机制买单、不为「衰老」适应症买单）在本期进一步推进——
<strong>连股权都不掏了，只掏政府补贴、债权和产能</strong>。</p></blockquote>
<h2>方法与口径（便于复用检索）</h2>
<ul>
<li><strong>采集源</strong>：Longevity.Technology（经 sitemap 8,860 条 URL 取 lastmod 定位窗口）+ watchlist 25 家官网
+ <strong>SEC EDGAR</strong>（submissions / 全文检索）+ <strong>ClinicalTrials.gov API v2</strong>
（<code>AREA[LastUpdatePostDate]RANGE[2026-10-27,2026-10-30]</code>）+ <strong>联邦公报 API</strong> + <strong>eCFR</strong>
+ BusinessWire / GlobeNewswire / PRNewswire 原稿 + pdufa.bio 聚合日历</li>
<li><strong>去重口径</strong>：公司名、药物名、NCT/注册号三维度比对上期周报、行业层历史交付清单与内部站 articles.json（1,127 篇）</li>
<li><strong>硬规则</strong>：无<strong>可点击原始来源</strong>的条目一律删除，不做「据知情人士」类补全</li>
</ul>""",
    src("2026-10-30", "《行业情报周报_2026-10-30》（行业层 file_id djpYEKiEfRcs，实测 36,454 B）",
        "https://longevity.technology/news/",
        "表格版：行业情报周报_2026-10-30.xlsx（`dETldVedMwAc`，39,022 B）｜基线：管线状态基线.json v1.1（`dmsATtPgKteT`，26,020 B）"))


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
