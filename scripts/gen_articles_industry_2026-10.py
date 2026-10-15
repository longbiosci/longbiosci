#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_articles_industry_2026-10.py
—— 行业层漏收增量消化（批次 2026-10）

来源：IMA 知识库「行业情报周报_2026-09-16」与「行业情报周报_2026-10-14」
      （经 scripts/harvest.py 四路查重 → confidence=none → 逐条在 news/*.html
      全文做高特异关键词硬核验后确认的真漏收）

硬核验结论（本轮）：
  - 文献类 4 条（NAD 头对头 RCT / 雷帕霉素 APOE4 / 雷帕霉素 HFpEF / 犬表观时钟）
    全部已收录，标题逐字对应，不重复写。
  - 行业周报 09-16 与喂料池 [投融资]/[管线]/[监管] 条目系同一批事件，去重后计一次。
  - Variant Bio × BI、FDA ARDD 监管科学议程、《The regulatory door is ajar》
    三条款目，站内已有对应文章，不重复写。
  - 真漏收 14 条，按「融资 / 管线与商业化 / 监管与支付」三条主线合并为 3 篇深度盘点。
  - 另有 6 条（Healthleap、NMPA 化妆品规范、FibroBiologics、Magnitude、Inspiren、
    Temple×Longevous）因材料过薄或与长寿弱相关，本轮不独立成篇，详见收尾报告。

纪律（继承 SOP §4.2）：
  - 行业/监管条目按「机构披露」口径定为 C 级
  - 金额、样本量、统计量一律照抄周报记录，不推算、不合并口径
  - 内链 slug 全部取自 ls news/ 实抄，main() 启动前做存在性硬校验
"""
import html
import importlib.util
import json
import os
import re
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
DATE = sys.argv[2] if len(sys.argv) > 2 else "2026-10-16"

_HERE = os.path.dirname(os.path.abspath(__file__))
_argv = sys.argv
sys.argv = [_argv[0], ROOT, "_unused", DATE]
_spec = importlib.util.spec_from_file_location("_ga", os.path.join(_HERE, "gen_articles.py"))
ga = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ga)
sys.argv = _argv

HEAD, ld, date_cn = ga.HEAD, ga.ld, ga.date_cn


def notice(ev):
    t = {"A": "A 级（同行评议人体研究）",
         "B": "B 级（同行评议临床前研究，主要为动物模型）",
         "C": "C 级（预印本 / 观点评论，非原始研究）"}[ev]
    body = {
        "A": "<p><strong>本文属人体研究证据，但需注意：</strong>观察性或小样本干预的结论不等于已证实临床获益；效应量与长期安全性仍需更大规模、更长随访的试验验证。</p>",
        "B": "<p><strong>本文核心结论来自动物模型或体外细胞学，属临床前证据，不能外推至人体。</strong>「延长健康寿命」「改善功能」等表述在小鼠中的意义，与人类临床结局之间仍有距离。</p>",
        "C": "<p><strong>本文属机构披露 / 行业信息，不是同行评议的原始研究。</strong>"
            "文中金额、阶段、日期与表述均来自公司公告、监管文件与行业媒体报道，"
            "<strong>未经独立核实</strong>。融资公告与管线进展<strong>不构成临床证据</strong>；"
            "「达到主要终点」「授权」「认定」等表述各有其特定含义，不等于疗效证明或监管批准。</p>",
    }[ev]
    src = ("<p><strong>关于本文的文献来源：</strong>本站依据 IMA 知识库「行业情报周报」"
           "（2026-09-16 / 2026-10-14 两期）撰写，原始出处为各公司公告、监管文件与行业媒体。"
           "周报中标注「待核实」的条目，本文<strong>照录其存疑状态，不做补全</strong>；"
           "未披露的金额一律写「未披露」，<strong>不做估算</strong>。</p>")
    return (f'<div class="notice-box">\n'
            f'    <p><span class="tier tier-{ev.lower()}">{ev} 级</span>'
            f'<strong>证据分级：{t}</strong></p>\n'
            f'    {body}\n'
            f'    {src}\n'
            f'</div>')


def build(slug, m, related_html):
    ld_news, ld_crumb = ld(m["title"], html.escape(m["desc"], quote=True), slug, DATE, m["crumb"])
    body = m["body"].rstrip() + "\n\n" + notice(m["ev"]) + "\n"
    return HEAD.format(
        title=html.escape(m["title"]), desc=html.escape(m["desc"], quote=True),
        slug=slug, date=DATE, date_cn=date_cn(DATE), crumb=html.escape(m["crumb"]),
        tag=html.escape(m["tag"]), topic=html.escape(m["topic"]),
        ev=m["ev"].lower(), source=m["source"], body=body,
        ld_news=ld_news, ld_crumb=ld_crumb, related=related_html,
    )


A = {}

A["Longevity-Funding-Roundup-Sep-Oct-2026.html"] = dict(
    topic="生命历程", ev="C", tag="行业动态",
    title="六笔钱流向了哪里：2026 年 9–10 月长寿产业融资盘点，以及「 therapeutics 之外」的钱在变多",
    crumb="长寿产业融资盘点",
    desc="HexemBio 1550 万美元、Moonwalk 7000 万美元 B 轮、Biophytis 5300 万欧元增资、Axo Longevity 500 万美元种子轮、Clene 400 万美元、Vincere 270 万美元 NIH 资助——六笔交易勾勒出 2026 年秋长寿资本的三条去向：真正的 therapeutics、预防性消费健康、以及被迫切开业的检测与监测。",
    source=("IMA 知识库「行业情报周报」（2026-09-16 / 2026-10-14 两期）· 原始出处："
            "Longevity Technology、Businesswire、PR Newswire、Finanzwire、SEC EDGAR、"
            "各公司投资者关系公告 · 详见正文各条来源链接"),
    body="""<p>看单一的融资新闻意义不大——每家公司都会说自己「解决衰老的根本原因」。但如果把一段时间里的交易放在一起看，<strong>钱的流向会暴露这个行业当下真正相信什么</strong>。以下是 2026 年 9 月中旬至 10 月中旬，经查重确认尚未被本站收录的六笔交易。</p>

<h2>一、真正在做 therapeutics 的</h2>

<h3>HexemBio：1550 万美元累计，造血干细胞年轻化</h3>
<ul>
<li><strong>时间与轮次</strong>：新一轮（本轮金额未单独披露），<strong>累计总融资 1550 万美元</strong>，日期 2026-09-15；</li>
<li><strong>投资方</strong>：Draper Associates 领投，Happiness Capital 新进，Boost VC 等老股东跟投；</li>
<li><strong>方向</strong>：<strong>Synthetic Human Yolk Sac 平台</strong>——用工程化手段重建卵黄囊样的造血发育微环境，实现造血干细胞年轻化；</li>
<li><strong>三条产品线</strong>：一代为骨髓移植细胞治疗、二代为无需体外采细胞处理的注射剂、三代为皮肤增强与保护；</li>
<li><strong>来源</strong>：<a href="https://longevity.technology/news/hexembio-raises-15-5m-to-rejuvenate-aging-stem-cells/" target="_blank" rel="noopener noreferrer">Longevity Technology</a>。</li>
</ul>

<h3>Moonwalk Biosciences：7000 万美元 B 轮（超额认购）</h3>
<ul>
<li><strong>时间与轮次</strong>：Series B（超额认购）<strong>7000 万美元</strong>，日期 2026-09-09；</li>
<li><strong>方向</strong>：<strong>MW101，脂肪靶向 siRNA</strong>。临床前显示体重与脂肪量下降且不减少摄食、保留瘦体重；NHP 单次给药后脂肪靶点结合持久。目标 2027 年底首次人体；</li>
<li><strong>来源</strong>：<a href="https://longevity.technology/news/moonwalk-raises-70m-for-adipose-targeted-rnai/" target="_blank" rel="noopener noreferrer">Longevity Technology</a>。</li>
</ul>

<h3>Biophytis：5300 万欧元增资，肌少症 III 期在跑</h3>
<ul>
<li><strong>时间与方式</strong>：配股 + 认股权证，面向机构投资者（剔除原有股东），日期 2026-09-11；</li>
<li><strong>投资者构成</strong>：美国机构 62% / 欧洲机构 38%；</li>
<li><strong>方向</strong>：<strong>BIO101</strong>。肥胖方向为 II 期 OBA——作为 GLP-1 辅助用药，目标是保留肌肉力量与活动能力、抑制停药反弹；肌少症方向为 <strong>III 期 SARA-31</strong>（已进入注册性阶段，是本批六笔里临床进度最靠前的）；</li>
<li><strong>来源</strong>：<a href="https://www.finanzwire.com/press-release/biophytis-epa-albps-biophytis-announces-completion-of-53-million-capital-increase-to-fund-its-phase-2-trial-in-obesity-HhDjcQ4jYof" target="_blank" rel="noopener noreferrer">Finanzwire</a>。</li>
</ul>

<blockquote><p>把 BIO101 的适应症选择单独拎出来说：它瞄准的是「<strong>GLP-1 停药反弹</strong>」与「<strong>减重伴随的肌肉流失</strong>」——这两个问题不是衰老生物学的产物，而是<strong>当前最热门药物的临床副作用</strong>。药厂愿意为此付钱，是因为它有明确的支付方与明确的终点。这是本批六笔里商业逻辑最清楚的一笔。</p></blockquote>

<h3>Vincere Biosciences：270 万美元 NIH SBIR Phase II</h3>
<ul>
<li><strong>性质</strong>：<strong>非股权资助</strong>，NIDDK / NIH，2 年期，日期 2026-09-14；</li>
<li><strong>方向</strong>：<strong>USP30 抑制剂</strong>，靶向线粒体功能障碍与线粒体自噬（mitophagy）受损；</li>
<li><strong>适应症扩展</strong>：由帕金森（CNS 项目）<strong>扩展至急性肾损伤</strong>；</li>
<li><strong>来源</strong>：<a href="https://longevity.technology/news/vincere-biosciences-wins-2-7m-nih-grant-to-advance-acute-kidney-injury-drug/" target="_blank" rel="noopener noreferrer">Longevity Technology</a>。</li>
</ul>

<h3>Clene Inc.：400 万美元 Registered Direct Offering</h3>
<ul>
<li><strong>时间与方式</strong>：按 Nasdaq 市价规则，日期 2026-09-15；</li>
<li><strong>投资方</strong>：董事长 David Matlin 领投，创始投资方 Kensington Capital Holdings、CEO 及其他老股东参与；</li>
<li><strong>方向</strong>：<strong>CNM-Au8</strong>，靶向线粒体功能与 NAD 通路并降低氧化应激，覆盖 ALS / 帕金森 / 多发性硬化；</li>
<li><strong>来源</strong>：<a href="https://invest.clene.com/news-releases/news-release-details/clene-announces-4-million-registered-direct-offering" target="_blank" rel="noopener noreferrer">Clene 投资者关系</a>。</li>
</ul>

<h2>二、卖的不是药，是「预防性健康会员制」</h2>

<h3>Axo Longevity：500 万美元种子轮（超额认购）</h3>
<ul>
<li><strong>时间与轮次</strong>：Seed（超额认购）<strong>500 万美元</strong>，日期 2026-09-10；</li>
<li><strong>投资方</strong>：MS&amp;AD Ventures、Izou Partners、LifeX Ventures、Everywhere Ventures、UNQ、51 Ventures、Cistern Capital、NIAN Sports Entertainment；天使投资人含 Clinica Planas Barcelona 的 Jorge Planas、前 H&amp;M 总裁 Daniel Kulle；</li>
<li><strong>方向</strong>：<strong>预防性健康会员制</strong>——100+ 生物标志物血检 + Axo Health Score + 生物年龄；覆盖英/爱/西/德/荷 + 秘鲁；</li>
<li><strong>来源</strong>：<a href="https://www.businesswire.com/news/home/20260910642125/en/" target="_blank" rel="noopener noreferrer">Businesswire</a>。</li>
</ul>

<h2>三条观察</h2>

<ol>
<li><strong>只有一半的钱在押「衰老机制」。</strong>HexemBio（干细胞年轻化）、Moonwalk（脂肪靶向 siRNA）、Vincere（线粒体自噬）是直接押机制；Biophytis 押的是 GLP-1 的副作用市场；Axo 押的是消费级检测；Clene 是老牌神经退行管线。<strong>严格意义上的「抗衰 therapeutics」只占本批交易的一半左右。</strong></li>
<li><strong>「保留瘦体重」成为新的共同终点。</strong>Biophytis 的 OBA 试验与 Moonwalk 的 MW101，一个做药一个做 siRNA，但都把「减脂不减肌」作为核心卖点。这个终点好测、好讲、且支付方认得。</li>
<li><strong>非股权资助在补位。</strong>Vincere 的 270 万美元来自 NIH SBIR 而非 VC。在长寿一级市场估值仍高的背景下，政府资助正在成为早期线粒体/自噬类项目的重要资金来源——这类机制短期难有商业回报，VC 出手的意愿低于两年前。</li>
</ol>

<h2>本文没有覆盖的部分</h2>

<ul>
<li>另有<strong>三笔交易因材料过薄或不属长寿赛道，本轮未独立成篇</strong>：FibroBiologics 约 50 万美元私募配售（独家认购方为公司首席科学官本人）、Magnitude Biosciences 130 万英镑种子轮（<strong>日期待核实</strong>）、Inspiren 7000 万美元 C 轮（养老机构 AI 监测，属<strong>邻近赛道·非 therapeutics</strong>）。</li>
<li>Temple 收购 Longevous（2026-09-14 报道）金额未披露，本文未计入统计。</li>
<li>本期周报窗口内还有 Undecimal Bio、Sava Technologies、Sensible Biotechnologies 等交易，<strong>本站此前已收录</strong>，见延伸阅读。</li>
<li><strong>所有金额均为公司公告口径，未经独立核实</strong>；欧元与美元未做汇率换算，<strong>不给出合计总额</strong>。</li>
</ul>
""",
    related=[("Undecimal-Bio-siRNA-Non-Hepatic-Delivery-Seed-18M.html",
              "把 siRNA 送到肝脏以外：Undecimal Bio 1800 万美元种子轮押注非肝递送"),
             ("Sava-Technologies-Sensor-SeriesB-36M-Continuous-Monitoring.html",
              "测糖这件事终于拿到产业级押注：Sava Technologies B 轮 3600 万美元，Ascensia 拿到欧洲分销权"),
             ("Sensible-Biotechnologies-VECTOR-mRNA-47M-In-Cell-Production.html",
              "把 mRNA 工厂搬进活细胞：Sensible Biotechnologies 4700 万美元推进 VECTOR 平台"),
             ("NewLimit-435M-Epigenetic-Reprogramming-2026.html",
              "长寿公司 NewLimit 融资 4.35 亿美元：表观遗传重编程迈入临床时代"),
             ("Retro-Biosciences-1.8B-Valuation-2026.html",
              "Retro Biosciences 估值达 18 亿美元：3 年从实验室到临床候选药物"),
             ("Alector-Genentech-AL050-Parkinson-Brain-Carrier-1.17B.html",
              "Genentech 豪掷 11.7 亿美元里程碑接手 Alector 的帕金森项目：为什么是 GCase 而不是抗体")],
)

A["Longevity-Pipeline-Commercialization-Sep-Oct-2026.html"] = dict(
    topic="生命历程", ev="C", tag="行业动态",
    title="从比格犬的甲基化时钟到纽约的长寿诊所：2026 年 9–10 月管线与商业化八则",
    crumb="管线与商业化进展",
    desc="Genflow 的 SIRT6 基因疗法在 24 只老龄比格犬上达到主要终点；Retro Biosciences 因早期安全性数据「过于干净」而扩大 I 期入组；BioViva 拿到端粒/肌肉/血糖相关专利但明确声明不构成监管批准。同期四则商业化动作勾勒出「检测—诊所—产能」这条提前于疗法落地的链条。",
    source=("IMA 知识库「行业情报周报」（2026-09-16 / 2026-10-14 两期）· 原始出处："
            "Longevity Technology、Businesswire、PR Newswire、Morningstar、SEC EDGAR、"
            "各公司投资者关系公告与会议报道 · 详见正文各条来源链接"),
    body="""<p>这一批八则进展里，真正有临床数据读出的只有两条，其余是专利、产能、合作与服务落地。<strong>这个比例本身就是信息</strong>：在一个还没有任何衰老适应证获批的领域里，行业正在先把「怎么造、怎么测、怎么卖」这件事搞定，而把「有没有效」往后推。</p>

<h2>一、两条有数据读出的</h2>

<h3>Genflow Biosciences：GF-1002 在老龄比格犬上达到主要终点</h3>

<ul>
<li><strong>项目</strong>：<strong>GF-1002</strong>——SIRT6 百岁老人变异体的裸 DNA 基因疗法；阶段为<strong>伴侣动物临床 / 人体前</strong>；</li>
<li><strong>试验设计</strong>：SLAB 试验，<strong>24 只 10 岁以上比格犬</strong>，随机盲法分四组——裸 DNA 两个剂量组、AAV8 单剂组、生理盐水对照组；</li>
<li><strong>主要终点</strong>：<strong>GRIM DNA 甲基化时钟测得的生物学年龄</strong>，治疗组较对照显著下降；次要功能学指标亦改善，<strong>细节留待公布</strong>；</li>
<li><strong>后续</strong>：完整数据（含甲基化时钟与肌肉组织学）于 <strong>2026-10-01~02 多伦多 Animal Longevity Summit（ALOS）</strong>发布；公司正与全球动物健康企业洽谈授权；</li>
<li><strong>日期与来源</strong>：2026-09-11，<a href="https://longevity.technology/news/genflows-gene-therapy-turns-back-aging-in-dogs/" target="_blank" rel="noopener noreferrer">Longevity Technology</a>。</li>
</ul>

<blockquote><p>读这条要抓住两点。第一，<strong>主要终点是一个甲基化时钟</strong>，不是寿命、不是功能、不是任何临床结局——这正是当前整个领域最核心的方法论困境（本站已多次讨论，见延伸阅读）。第二，<strong>犬是唯一一种「表观遗传时钟 → 寿命」可以在合理时间内被同时验证的哺乳动物</strong>；本站此前报道过 894 只犬的 LINE1 甲基化时钟研究，两条线索在这里可以合流。但请注意：<strong>「显著下降」的具体幅度、各剂量组的分别结果、以及统计检验细节，本文均未获得</strong>。</p></blockquote>

<h3>Retro Biosciences：RTR-242 的 I 期「太干净了」</h3>

<ul>
<li><strong>项目</strong>：<strong>RTR-242</strong>——恢复溶酶体酸性、增强自噬，针对阿尔茨海默/帕金森；阶段 I 期；</li>
<li><strong>调整内容</strong>：早期安全性数据「<strong>过于干净</strong>」、<strong>无剂量限制信号</strong>，公司因此新增两个队列，入组由 76 扩至 108（<strong>+42%</strong>），以求找到有效剂量；目前仅在 18–65 岁健康志愿者中测试；</li>
<li><strong>同赛道对照</strong>：Lysoway Therapeutics（2026-05 首次人体）、Vanqua Bio（2026-05 早期安全性积极）；</li>
<li><strong>日期</strong>：<strong>具体公告日期待核实</strong>；来源为 Longevity Technology。</li>
</ul>

<blockquote><p>「安全性数据太干净」是一个罕见且值得玩味的理由。通常 I 期扩大入组是因为看到了毒性需要更多数据，而这里反过来——<strong>因为找不到剂量限制毒性，所以不知道该用多大剂量</strong>。这暴露了自噬类增强剂的一个固有难题：<strong>这类药物的治疗窗上限不由毒性定义，而由「自噬增强到什么程度算过度」定义，而后者的测量手段目前不存在。</strong></p></blockquote>

<h2>二、四则商业化与产能动作</h2>

<h3>BioViva：专利授权 ≠ 监管批准</h3>
<ul>
<li><strong>内容</strong>：美国专利 <strong>No. 12,653,907</strong>《Methods of Treating or Preventing Age-Related Disorders》，权利要求覆盖<strong>端粒长度、肌肉量、血糖水平</strong>，并涵盖 AAV 等病毒载体递送；</li>
<li><strong>项目</strong>：hTERT + Follistatin-344（FST-344）双基因疗法，阶段为<strong>研究阶段</strong>；</li>
<li><strong>公司声明</strong>：专利授权<strong>不构成监管批准</strong>，相关技术仍处研究阶段；</li>
<li><strong>日期</strong>：报道 2026-09-14／专利授权日 2026-06-16。</li>
</ul>

<h3>Celularity × MuseCell Innovations：最高 3 亿美元的生产合作</h3>
<ul>
<li><strong>内容</strong>：Celularity 在新泽西 Florham Park 基地（<strong>147,215 平方英尺</strong>，9 个 Grade C/ISO 7 + 6 个 Grade D/ISO 8 洁净套件）按授权的「<strong>Dezawa Method</strong>」生产 DMC，及 Dezawa MuseExosomes、MuseSecretome；</li>
<li><strong>金额</strong>：基于当前市场与 MCI 预测，扩大合作后 5 年内可能为 Celularity 带来<strong>超 3 亿美元采购额与 200+ 高技能岗位</strong>——<strong>属预测性表述，非已确认订单</strong>；</li>
<li><strong>技术要点</strong>：DMC 身份由「<strong>生产方法 + 规格符合性</strong>」定义，而非仅由组织来源定义；</li>
<li><strong>日期</strong>：2026-09-07。</li>
</ul>

<h3>GlycanAge × ExoEarth Corporation：MOU 签署</h3>
<ul>
<li><strong>内容</strong>：在日本推进 GlycanAge 生物年龄检测商业化；并开展纵向联合研究，用 GlycanAge 追踪接受 <strong>EXOCURE</strong> 者的生物年龄与免疫相关变化；</li>
<li><strong>状态</strong>：研究方案<strong>尚未定稿</strong>（待科学、医学、伦理与监管审查），<strong>样本量、测量频率、具体方案均未公布</strong>；</li>
<li><strong>项目</strong>：糖基化炎症衰老检测 × EXOCURE 外泌体平台（源自脱落乳牙干细胞）；阶段为商业化 + 研究者发起/企业合作研究；</li>
<li><strong>日期</strong>：2026-09-10。</li>
</ul>

<h3>Elysium Health：纽约长寿诊所开业</h3>
<ul>
<li><strong>内容</strong>：The Elysium Longevity Institute（TELI）纽约开业，医师主导的个性化长寿医疗；上线 <strong>18 项长寿方案</strong>（含处方药、肽类、补充剂，口服/鼻内/注射）；Omar Baker 任 CMO，联合创始人兼首席科学家 <strong>Leonard Guarente</strong> 为合作者；</li>
<li><strong>性质</strong>：<strong>属消费医疗服务，非获批疗法</strong>；</li>
<li><strong>日期</strong>：2026-09-09。</li>
</ul>

<h2>三、两则平台与管线推进</h2>

<h3>HexemBio：Synthetic Human Yolk Sac 平台</h3>
<ul>
<li>一代（骨髓移植细胞治疗）：<strong>2025-07 获 FDA 孤儿药资格、2026-01 完成 pre-IND 会议、目标 2027 首次人体</strong>；二代（注射剂，无需体外采细胞处理）晚期临床前；三代（皮肤增强与保护）开发末期；</li>
<li><strong>平台发表于 Nature</strong>（s41586-023-06914-8），全球 <strong>17 项专利申请、2 项已授权</strong>；</li>
<li><strong>日期</strong>：2026-09-15。</li>
</ul>

<h3>Moonwalk Biosciences：MW101</h3>
<ul>
<li>临床前显示<strong>体重与脂肪量下降且不减少摄食、保留瘦体重</strong>；NHP 单次给药后脂肪靶点结合持久；目标 <strong>2027 年底首次人体</strong>；同步搭建更广泛的心血管代谢组织靶向 siRNA 管线；</li>
<li><strong>日期</strong>：2026-09-09。</li>
</ul>

<h2>本文的口径说明</h2>

<ul>
<li>以上八则<strong>均为机构披露 / 行业媒体报道</strong>，非同行评议文献。<strong>「达到主要终点」「授权」「MOU」各有其特定含义，均不等于疗效证明或监管批准。</strong></li>
<li>Genflow 试验的<strong>效应量、各剂量组分别结果、统计检验细节</strong>，以及 ALOS 会议公布后的完整数据，<strong>本文均未获取</strong>。</li>
<li>Retro 的公告<strong>日期待核实</strong>；Celularity 的 3 亿美元为<strong>预测性表述</strong>；GlycanAge 的研究<strong>方案未定稿</strong>。</li>
<li>Insilico Medicine 的 Rentosertib 项目（III 期首例给药、Longevity Vaccines 计划）<strong>本站此前已收录</strong>，本条不重复。</li>
</ul>
""",
    related=[("Life-Biosciences-ER-100-First-Human-Data-AAO-2026.html",
              "全球首个细胞重编程人体试验公布早期数据：3 名青光眼患者 2 例视野改善，剂量将升至 3 倍"),
             ("Rubedo-RLS-1496-GPX4-Phase1.html",
              "Rubedo RLS-1496 I 期临床结果：GPX4 调节剂首个人体数据"),
             ("Immorta-SenoMune-AI-Designed-Senolytic-Immune-Therapy-2026.html",
              "AI 设计的多肽 senolytic 免疫疗法：让免疫系统重新学会「认人」"),
             ("Dog-Epigenetic-Clock-LINE1-Science-2026.html",
              "大狗的表观遗传时钟走得更快：Science 报告 894 只犬 LINE1 跳跃基因去甲基化"),
             ("Function-Health-Google-Health-Integration-Lab-Data.html",
              "160 项实验室检测接入 Google Health：功能医学数据从「单独看」变成「和可穿戴数据一起看」"),
             ("KHL-Foundation-Rejuvenation-Cocktail-2026.html",
              "KHL Foundation：创始人年过八旬 Launch 基因疗法「回春鸡尾酒」医疗旅游")],
)

A["Longevity-Regulatory-Payment-Boundaries-2026.html"] = dict(
    topic="生命历程", ev="C", tag="监管政策",
    title="四道边界：中国明确「衰老非疾病」、FDA 收紧终点标准、加拿大卡在支付、长寿肽仍在灰色地带",
    crumb="监管与支付的四道边界",
    desc="2026 年 9 月，四则互不相关的监管决定从四个方向划出了抗衰产业的边界：中国药监与卫健委明确衰老非疾病范畴且从未批准任何抗衰老适应证；FDA 的 RDEA 试点允许讨论新型终点但要求证明临床获益；加拿大 CDA-AMC 对 lecanemab 的报销决定显示瓶颈正从审批端转向支付端；FDA 503A/503B 清单则解释了「长寿肽」为何长期处于灰色地带。",
    source=("IMA 知识库「行业情报周报_2026-09-16」· 原始出处：人民日报健康客户端（央视采访佐证）、"
            "Endpoints News（经二手转述）、Longevity Technology、Canada's Drug Agency（CDA-AMC）、"
            "FDA 官方 bulks list 页面 · 详见正文各条来源链接"),
    body="""<p>关于「抗衰产业到底走到哪一步了」，最常见的说法是「监管还没跟上」。但如果把 2026 年 9 月这四则互不相关的决定放在一起看，会得到一个更准确的判断：<strong>监管不是没跟上，而是已经在四个不同方向上把边界划出来了</strong>——只是这些边界划的地方，和行业希望的不一样。</p>

<h2>边界一（适应证定义）：中国明确「衰老非疾病范畴」</h2>

<p>这是本批四则中信息价值最高、也最容易被忽略的一条。2026-09-11，人民日报健康客户端报道（央视采访佐证）梳理了中国监管的逻辑，要点如下：</p>

<ol>
<li><strong>衰老属自然生理退变，非法定疾病。</strong>WHO《国际疾病分类》未将衰老纳入疾病范畴——<strong>没有疾病定义，就无法设定临床评价标准</strong>；</li>
<li>北大三院毕洪森指出：<strong>国内乃至全球均无一款针对抗衰的药品获批</strong>；</li>
<li><strong>全球无任何干细胞、外泌体产品获药监机构批准用于抗衰老、美容修复</strong>；</li>
<li>NAD⁺（辅酶Ⅰ）注射剂国内 2002 年获批，但<strong>仅限辅助治疗白细胞减少症/冠心病/心肌炎</strong>，肌注、单次 5 mg；<strong>部分机构改为静滴且超剂量 30–50 倍属违规</strong>；</li>
<li>国家卫健委<strong>多次警示</strong>：医美/养生机构开展干细胞输注、外泌体抗衰<strong>属违规诊疗</strong>。</li>
</ol>

<blockquote><p>第 4 点值得单独说。它给出了一个极其具体的对照：<strong>同一个分子，合法用法是肌注 5 mg 辅助治疗特定疾病，违规用法是静滴 150–250 mg 用于「抗衰」。</strong>市面上大量「NAD⁺ 点滴」的商业宣传，其剂量就落在这个违规区间里。这是本批信息中<strong>最接近消费者实际决策</strong>的一条。</p></blockquote>

<p><strong>意义</strong>：对国内「抗衰产业化」是明确的降温信号。做综述或转化研究时，须严格区分「基础研究发现」与「临床疗效」，避免被断章取义引用。</p>

<h2>边界二（终点标准）：FDA 罕见病终点政策——一扇半开的门</h2>

<p>2026-09-14，Endpoints News 报道（经二手转述）了 FDA 在罕见病试验标准与终点选择上的方向调整：</p>

<ul>
<li>总体方向：在<strong>小人群研究中给予更大灵活性</strong>，同时要求仍须证明<strong>「患者感受、功能或生存」</strong>方面的临床获益；</li>
<li><strong>RDEA</strong>（Rare Disease Endpoint Advancement）试点：允许申办方就<strong>新型疗效终点</strong>（含此前从未支持过批准的终点）与 FDA 早期沟通；</li>
<li>核心工具：<strong>自然史研究、患者/照护者视角、疾病相关生物标志物与替代终点验证</strong>；</li>
<li><strong>官方警示（关键）</strong>：生物标志物本身通常<strong>只支持机制或靶点结合证据</strong>，<strong>除非经适当验证为替代终点，否则不构成临床获益证明</strong>；并对外部对照试验在终点主观时的偏倚风险提出警告。</li>
</ul>

<blockquote><p>对以生物标志物为主要卖点的长寿项目，这是<strong>「半开半掩」</strong>：终点创新被允许讨论，但「生物年龄下降」这类终点要升级为<strong>可批准终点</strong>，仍须走完整的替代终点验证流程。这不是一条捷径，而是一张需要多年才能兑现的期票。</p></blockquote>

<h2>边界三（支付端）：加拿大 lecanemab 报销决定</h2>

<p>2026-08-31，加拿大药物管理局（CDA-AMC）经行政复议后发布<strong>最终正面报销推荐</strong>，支持对轻度认知障碍或轻度阿尔茨海默痴呆 eligible 患者给予 public reimbursement。</p>

<ul>
<li><strong>后续流程</strong>：须经 <strong>pCPA</strong>（泛加拿大药物联盟）价格谈判，再由各省分别作出覆盖决定——<strong>推荐不等于可及</strong>；</li>
<li><strong>规模</strong>：加拿大 2025 年约 <strong>77 万痴呆患者，预计 2050 年达 170 万</strong>；</li>
<li><strong>产品背景</strong>：lecanemab 已在 <strong>53 个国家/地区获批</strong>；2025 年获美国批准皮下维持注射，2026-07 再获皮下起始剂量批准。</li>
</ul>

<blockquote><p>这条的意义不在阿尔茨海默本身，而在它示范了<strong>瓶颈的转移</strong>：一个已经在 53 个国家获批的药物，在加拿大的可及性还要再走「行政复议 → 推荐 → 价格谈判 → 各省分别决定」四步。<strong>对后续阿尔茨海默乃至广义衰老相关疗法，这套流程树立了报销与价格基准的模板。</strong>支付端，而不是审批端，正在成为神经退行疗法的真正瓶颈。</p></blockquote>

<h2>边界四（灰色市场）：FDA 503A/503B 清单与「长寿肽」</h2>

<p>2026-09-11 查证状态：</p>

<ul>
<li><strong>Ipamorelin acetate</strong>：列于 <strong>503B 临时政策 Category 2</strong>（2023-09 加入，FDA 认定「<strong>可能具有显著安全风险</strong>」）；</li>
<li><strong>CJC-1295</strong>：提名于 2024-09 撤回，不再在活跃 Category 2 表中，但 <strong>FDA 仍保留安全性风险表述</strong>；</li>
<li><strong>两者均未通过 503A 准入审评</strong>——顾问委员会分别于 2024-10、2024-12 投票反对纳入；</li>
<li>FDA 对 ipamorelin 的关注点为<strong>免疫原性、肽类杂质及严重不良事件报告</strong>。</li>
</ul>

<p><strong>意义</strong>：这一条解释了<strong>为何大量「长寿/抗衰肽」远程医疗项目处于监管灰色地带</strong>——它们既未被批准，也不在被明确禁止的清单上，而是通过「未被列入准入清单」这一状态在事实上流通。<strong>建议以 FDA 官方 bulks list 页面为准复核</strong>，本条依据为二手来源。</p>

<h2>合起来看</h2>

<p>这四道边界指向同一个结构性问题：<strong>「衰老」目前在任何主要司法辖区都不是可批准的适应证，而「生物年龄」在任何地方都不是可接受的注册终点。</strong>在此前提下，行业的可行路径只有两条——要么把衰老拆成具体的年龄相关疾病逐个做（中国、FDA 的现行路径），要么先建立可验证的替代终点（FDA RDEA 试点的目标）。两条都需要多年。</p>

<p>而在这个等待期里，<strong>商业化跑得比证据快</strong>：NAD⁺ 静滴、长寿肽远程医疗、各类生物年龄检测，都在边界之外或边界的模糊处运营。中国监管的表述最直白——<strong>「无疾病定义即无法设定临床评价标准」</strong>。这句话值得所有从业者抄下来。</p>

<h2>本文未覆盖与口径说明</h2>

<ul>
<li>同期的 <strong>FDA ARDD 2026 监管科学议程</strong>、《The regulatory door is ajar》综合评述、以及 Variant Bio × Boehringer Ingelheim 的合作扩展，<strong>本站此前已收录</strong>，见延伸阅读。</li>
<li>CDE 对 Rentosertib 的<strong>突破性治疗品种认定</strong>，本轮核查后<strong>未找到可靠的官方公告链接</strong>（当前仅见百科条目），按纪律<strong>不写入正文</strong>。另需提醒：<strong>孤儿药资格 ≠ 批准</strong>，Rentosertib 目前仍为在研药物。</li>
<li>NMPA 2026 年第 99 号公告（《化妆品安全技术规范》修订实施）与长寿<strong>仅间接相关</strong>，本轮未独立成篇。</li>
<li>本批四则<strong>均为机构表态或行业媒体报道转述</strong>，非同行评议研究。FDA 罕见病终点政策一条的<strong>原始报道来源待核实</strong>。</li>
</ul>
""",
    related=[("FDA-Aging-Regulatory-Science-Priority-ARDD-2026.html",
              "FDA 把「衰老与长寿」写进监管科学议程：ARDD 2026 释放的信号与仍未解决的问题"),
             ("Aging-vs-Biological-Age-Conceptual-Considerations-2026.html",
              "「衰老」与「生物学年龄」不是一回事：给「年龄逆转」主张定举证责任"),
             ("Rentosertib-Proteomic-Aging-Clocks-IPF-Nature-Biotech-2026.html",
              "AI 设计的 IPF 新药让 6 个蛋白质组时钟同时变年轻——但最强信号不在最有效的剂量上"),
             ("Calico-Fosigotifator-FDA-BTD-VWM-2026.html",
              "Calico 旗下 eIF2B 激活剂 Fosigotifator 获 FDA 突破性疗法认定——剑指白质消融病"),
             ("Repair-Biotechnologies-REP-0003-FDA-RDEP-2026.html",
              "Repair Bio 旗下 REP-0003 获 FDA RDEP 资格：mRNA 疗法瞄准细胞内游离胆固醇清除"),
             ("Noom-Buys-Pharmacy-Healthy-Aging.html",
              "Noom 收购连锁药房大举进军健康老龄化市场")],
)


# ---------------- 主流程 ----------------
def main():
    arts = json.load(open(os.path.join(ROOT, "data/articles.json"), encoding="utf-8"))
    existing = {a["slug"] for a in arts}
    newsdir = set(os.listdir(os.path.join(ROOT, "news")))

    bad = []
    for slug, m in A.items():
        for rslug, _ in m["related"]:
            if rslug not in newsdir and rslug not in A:
                bad.append((slug, rslug))
    if bad:
        for s, r in bad:
            print(f"[内链不存在] {s} -> {r}")
        sys.exit(1)
    print(f"内链校验通过（{sum(len(m['related']) for m in A.values())} 条）")

    made, skipped = [], []
    for slug, m in A.items():
        if slug in existing:
            skipped.append(slug)
            continue
        rel = "".join(f'<li><a href="/news/{rslug}">{html.escape(rtitle)}</a></li>'
                      for rslug, rtitle in m["related"])
        with open(os.path.join(ROOT, "news", slug), "w", encoding="utf-8", newline="") as f:
            f.write(build(slug, m, rel))
        entry = {
            "slug": slug, "title": m["title"], "desc": m["desc"],
            "tag": m["tag"], "date": DATE, "topic": m["topic"],
            "type": m["tag"], "evidence": m["ev"],
            "source": "doi.org" if "doi.org" in m["source"] else "IMA 交叉追踪",
        }
        md = re.search(r"10\.\d{4,9}/[-._;()/:a-z0-9]+", m["source"], re.I)
        if md:
            entry["doi"] = md.group(0).rstrip(".,;:</a>")
        arts.append(entry)
        made.append(slug)

    arts.sort(key=lambda a: (a.get("date", ""), a.get("slug", "")), reverse=True)
    with open(os.path.join(ROOT, "data/articles.json"), "w", encoding="utf-8") as f:
        json.dump(arts, f, ensure_ascii=False, indent=2)
    print(f"新生成 {len(made)} 篇，跳过（已存在）{len(skipped)} 篇，articles.json 现 {len(arts)} 篇")


if __name__ == "__main__":
    main()
