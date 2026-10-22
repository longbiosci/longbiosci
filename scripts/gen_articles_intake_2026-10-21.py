#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_articles_intake_2026-10-21.py —— 内容摄入第 18 批（2026-10-21 巡检）

消化对象
────────
1. 《预印本速递_2026-10-21》(dNacOPpqOpKF, 39,189 B) —— 主榜 0、观察哨 4、补遗 5。
   上游口径：主榜需「衰老为核心主题 **且** 摘要含可引用定量」；本期两条以衰老为
   核心主题的稿件摘要零定量，故落观察哨。**故观察哨 #1–#4 全部按本批口径成篇**
   （不是「主榜 0 就什么都写不了」）。
2. 《行业情报周报_2026-10-21》(dmJkBUnnRwKd, 47,589 B) —— W43 期，投融资 9 /
   管线 15 / 监管 6。本批只提取**与衰老机制直接相关**的一条临床进展成篇
   （Mission Therapeutics MTX325，USP30 抑制剂 = 线粒体质量控制），
   其余条目在游标备注中登记，不在本站逐条铺开（避免以行业流水账稀释文献站定位）。

不写的与为什么
──────────────
· 补遗 5 条（Semaglutide 睡眠心率、肾性高血压脑白质、SIRT1–METTL3 计算筛选、
  ORIGIN-PD 分层、MagLOV2 pH 传感器）—— 相关性弱于观察哨，且本站已有同主题
  覆盖（见 harvest 四路比对）。判定与理由写进游标备注，**不入站必须留痕**。
· 《预印本全文级流水线_运行摘要_2026-10-19》(dEbLgGGlcwOG) —— 文件名 2026-10-19，
  正文自述「检索日期 2026-10-19」但执行时间 2026-10-20 07:00–07:56，
  属**摘要型过程文档**（full 32 / partial 1 / none 0，bioRxiv 70 条 403 缺席），
  不含可成篇的研究条目 → 判为 empty（过程文档），并记录错位问题。

证据分级（严格按 about/ 公开图例）
────────────────────────────────
A = 同行评议人体研究 / B = 同行评议临床前研究 / C = 预印本。
前 3 篇全部 bioRxiv/medRxiv 预印本 → **一律 C**，无论数据来自人体还是小鼠。
第 4 篇是行业情报（公司公告 + 媒体），非研究论文，按站点惯例标 B 并注明
「非同行评议研究、来源为公司新闻稿」——这一点在页内写清楚，不冒充研究证据。

纪律
────
· 定量一律照抄速递卡片/官方摘要原文，未做任何推算；
· 摘要未给的（样本量、效应量、统计量）一律标「待补全文」；
· 内部链接 slug 启动时校验存在性，不存在直接退出。
"""
import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATE = "2026-10-21"

REL_HGPS = [
    ("RANKL-Antibody-Progeria-Longevity-2026.html",
     "早老症的另一条路：阻断 RANKL 能否改善 progeria 的骨与代谢表型"),
    ("DNA-Methylation-Clock-Epigenetic-Progeria-2026.html",
     "表观遗传时钟在早老症里跑得更快——但快多少取决于测哪个组织"),
    ("Chromatin-Closure-Stem-Cell-Exhaustion-RIKEN-2026.html",
     "染色质闭锁与干细胞耗竭：核架构如何决定谱系走向"),
]
REL_CARM1 = [
    ("Chromatin-Closure-Stem-Cell-Exhaustion-RIKEN-2026.html",
     "染色质闭锁与干细胞耗竭：核架构如何决定谱系走向"),
    ("ATF5-Muscle-Mass-Quality-Aging-2026.html",
     "ATF5 与老年肌肉的质量下降"),
    ("Cardiolipin-ERRgamma-Muscle-Fiber-Switch-Nature-Aging-2026.html",
     "心磷脂–ERRγ 轴与肌纤维类型转换"),
]
REL_NIX = [
    ("In-Vivo-Multiparametric-Mitochondria-Aging-Trajectory-2026.html",
     "多参数活体成像揭示组织特异的线粒体衰老轨迹"),
    ("Aged-Mitochondrial-DNA-Is-Associated-AgingCell-2026.html",
     "老年肌肉的线粒体：崩掉的是 mtDNA 与 redox 应答"),
    ("FAM162A-Mitochondrial-Longevity-2026.html",
     "FAM162A：线粒体应激反应与长寿的接口"),
]
REL_USP30 = [
    ("In-Vivo-Multiparametric-Mitochondria-Aging-Trajectory-2026.html",
     "多参数活体成像揭示组织特异的线粒体衰老轨迹"),
    ("FAM162A-Mitochondrial-Longevity-2026.html",
     "FAM162A：线粒体应激反应与长寿的接口"),
    ("Exercise-Mitochondrial-Quality-Control-Brain-Aging-2026.html",
     "运动如何通过线粒体质量控制影响脑老化"),
]


def notice(ev):
    t = {"A": "A 级（同行评议人体研究）",
         "B": "B 级（同行评议临床前研究）",
         "C": "C 级（预印本：未经同行评议，结论可能随审稿改变）"}[ev]
    return (f'<div class="notice-box">\n'
            f'    <p><span class="tier tier-{ev.lower()}">{ev} 级</span>'
            f'<strong>证据分级：{t}</strong></p>\n'
            f'    <p><strong>关于转载与本证据分级的说明：</strong>本篇依据'
            f'<strong>预印本官方摘要</strong>（本轮经 IMA 知识库《预印本速递》卡片与官方摘要核对）整理，'
            f'定量一律照抄原文，<strong>未做任何数值推算补全</strong>；'
            f'凡摘要未给出的信息一律标注「待补全文」。</p>\n'
            f'    <p><strong>为什么是 C 级：</strong>它来自<strong>未经同行评议的预印本</strong>，'
            f'按 <a href="/about/" target="_blank" rel="noopener noreferrer">本站公开的分级约定</a>'
            f'只能标 C——数据来自人体或来自顶级机构，都不会抬高预印本的证据等级。</p>\n'
            f'</div>')


def notice_industry(ev):
    t = "B 级（同行评议临床前研究）"
    return ('<div class="notice-box">\n'
            '    <p><span class="tier tier-b">B 级</span>'
            '<strong>证据分级：B 级 · 但请注意这一篇不是研究论文</strong></p>\n'
            '    <p>本篇是<strong>行业情报</strong>，依据公司新闻稿与监管/媒体公开信息整理，'
            '<strong>不是同行评议研究</strong>。按本站分级表它落在 B（临床前/临床早期证据层级），'
            '但请把它读作「某个候选药进入了哪一步」，而不是「某个机制被证实了」。</p>\n'
            '    <p>凡涉及疗效的表述，本文一律只写公司公告原话并标注为<strong>公司自述</strong>；'
            '1b 期的主要目的是<strong>机制证明与安全性</strong>，不产出疗效结论。</p>\n'
            '    </div>')


def main():
    arts = json.load(open(os.path.join(ROOT, "data/articles.json"), encoding="utf-8"))
    all_rel = REL_HGPS + REL_CARM1 + REL_NIX + REL_USP30
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
    ga.notice = notice

    def src(server, cat, title, doi, authors, extra):
        return (f'<em>{server}</em>（{cat}）· 预印本：{title}'
                f' · DOI <a href="https://doi.org/{doi}" target="_blank" '
                f'rel="noopener noreferrer">{doi}</a>'
                f' · {authors}'
                f' · 来源：IMA 知识库《预印本速递》2026-10-21 期（file_id dNacOPpqOpKF）'
                f' + 官方摘要核对（{extra}）')

    src1 = src("bioRxiv", "cell biology",
               "Abnormal nuclear organization impairs adipogenic lineage commitment and "
               "terminal maturation in Hutchinson-Gilford progeria syndrome (HGPS)",
               "10.64898/2026.10.19.760205",
               "第一作者 N. Gogia；通讯 Rachel Patton McCord（田纳西大学诺克斯维尔分校）",
               "version 1，2026-10-20 上线；摘要零定量")
    src2 = src("bioRxiv", "cell biology",
               "Phosphorylation of CARM1 at Ser572 preserves muscle stem cell self-renewal "
               "by restricting premature myogenic commitment",
               "10.64898/2026.10.17.759715",
               "第一作者 C. A. VanGenderen；含 M. A. Rudnicki；通讯 Natasha C. Chang（麦吉尔大学）",
               "version 1，2026-10-20 上线；摘要零定量")
    src3 = src("bioRxiv", "cell biology",
               "BNIP3L/NIX-mediated mitophagy limits Alzheimer disease pathology and "
               "preserves neuronal function",
               "10.64898/2026.10.18.759942",
               "第一作者 Y. Li；含 V. Bohr；通讯 Konstantinos Pakalikaras（雅典大学医学院生理学系）",
               "version 1，2026-10-20 上线；摘要零定量")

    A = {
        "HGPS-Adipogenic-Lineage-Consolidation-Failure-HiC-bioRxiv-2026.html": dict(
            topic="细胞衰老", ev="C", tag="预印本",
            title="早老症的脂肪流失，坏在「巩固」不在「启动」：Hi-C 第一次把 3D 基因组接上脂肪谱系失败",
            crumb="HGPS 细胞能开始分化，但收敛不住",
            desc="在年龄匹配的健康人与早老症（HGPS）患者来源的成纤维细胞里诱导成脂分化，田纳西大学团队发现 HGPS 细胞的谱系「定向」速率与健康人相当，分歧发生在其后：脂滴形态异常、转录响应延迟紊乱，并且始终没有关掉向骨软骨与血管分支的分化潜能。",
            source=src1,
            body="""<p>Hutchinson-Gilford 早老症（HGPS）由截短的 Lamin A（progerin）驱动，核架构失稳，
<strong>优先累及间充质来源组织</strong>。其中最显著、也最容易被忽视的一条是皮下脂肪的早发萎缩。
一个自然的假设是「核架构乱了，干细胞就找不到自己的谱系了」。这篇预印本把这句直觉拆开检验，
结论比直觉更精确：<strong>它们开得了头，但收不了尾。</strong></p>

<h2>设计：为什么用患者成纤维细胞</h2>
<p>要在体外研究「年龄」，最难的是把<strong>供体年龄</strong>和<strong>疾病状态</strong>分开。
作者的做法是在<strong>年龄匹配</strong>的健康对照与 HGPS 患者来源的<strong>皮肤成纤维细胞</strong>
中同时诱导成脂分化——这样供体的年龄背景、表观遗传史、组织来源都被控住了，
差异只能来自 progerin 本身。三模态取样：活细胞成像 + bulk RNA-seq + Hi-C。</p>

<h2>最关键的一个阴性结果</h2>
<p><strong>HGPS 细胞向成脂谱系「定向（commit）」的速率与健康对照相当。</strong>
这句话值得单独拎出来，因为它直接否掉了一半的假设：问题不在「认不出脂肪这条路」。
分歧全部发生在定向之后：</p>
<ul>
<li><strong>脂滴形态异常</strong>，而不是简单的数量减少；</li>
<li>转录响应<strong>延迟且紊乱</strong>；</li>
<li>脂肪成熟停滞的同时，细胞<strong>仍然保留着向骨软骨、血管等替代间充质谱系分化的潜能</strong>
——即两条路的 priming 没有被收敛掉，最后哪条都没走完。</li>
</ul>

<h2>Hi-C 给出的增量</h2>
<p>如果只看基线，HGPS 与健康的确有<strong>一些</strong>三维基因组区室差异；但作者强调，
<strong>更显著的差异出现在「诱导过程中如何重新组织区室」</strong>：
健康细胞在成脂期会建立很强的「脂质代谢基因 ↔ 染色质区室」耦合，HGPS 里这个耦合明显失调。
换句话说，<strong>不是一个静态的坏结构，而是一次失败的动态重组</strong>。</p>

<h2>数字：这篇没有数字</h2>
<p>需要如实说明：<strong>该摘要未提供任何定量</strong>——没有样本量、供体年龄区间、差异基因数、
Hi-C 分辨率，也没有 P 值。以下字段一律为<strong>待补全文</strong>，我没有推算，也没有从同类文献套用：</p>
<table>
<tr><th>字段</th><th>状态</th></tr>
<tr><td>供体数 / 每组 n</td><td>待补全文</td></tr>
<tr><td>供体年龄区间（是否真正匹配）</td><td>待补全文</td></tr>
<tr><td>Hi-C 测序深度与分辨率</td><td>待补全文</td></tr>
<tr><td>区室切换的定量幅度</td><td>待补全文</td></tr>
<tr><td>差异表达基因数</td><td>待补全文</td></tr>
</table>

<h2>该怎么读它</h2>
<p>这是「<strong>早老症 = 加速衰老</strong>」这个类比最容易被误用的地方。本文讲的是
<strong>一个特定谱系的分化失败</strong>，不是「细胞老得更快」。它能告诉我们的是：
核架构对分化的作用可能集中在<strong>谱系巩固（consolidation）</strong>这个常被忽略的阶段，
而这一阶段恰恰是多数体外分化方案不细看的地方——大家都在测「分化效率」，
很少测「有没有关掉别的路」。</p>
<p>对干细胞与部分重编程方向的一个间接提示：如果 <strong>priming 的收敛</strong>需要持续的
染色质重组，那么任何以「提高重编程效率」为目标的干预，都值得加一个反向指标——
<strong>它有没有把细胞变得更容易被别的谱系带走</strong>。</p>

<p class="small">本文为预印本，未经同行评审。bioRxiv 内容域对本环境返回 403，未获取全文。</p>""",
            related=REL_HGPS),

        "CARM1-Ser572-Muscle-Stem-Cell-Exhaustion-bioRxiv-2026.html": dict(
            topic="干细胞", ev="C", tag="预印本",
            title="肌肉干细胞里的一个「刹车」：单次损伤扛得住，反复损伤就崩",
            crumb="CARM1 Ser572 磷酸化维持自我更新",
            desc="麦吉尔大学团队做出磷酸化缺失型 CARM1 SA 敲入小鼠，发现肌肉发育与单次损伤后的再生基本正常，但反复再生挑战会让卫星细胞池进行性耗竭——转录上是 TGFβ-SMAD 受损、Tgfbr3 下降、MYC 活性上升。",
            source=src2,
            body="""<p>骨骼肌再生的秘密在于卫星细胞必须在<strong>「分化成肌纤维」</strong>与
<strong>「复制自己留一份」</strong>之间来回取舍。这个取舍一旦偏向分化，短期看再生很漂亮，
长期看池子会空。这篇预印本找到了这个取舍上的一个分子刹车。</p>

<h2>背景链条</h2>
<p>CARM1 通过甲基化 PAX7 促进 Myf5 表达，把卫星细胞推向成肌定向；而肌营养不良蛋白糖蛋白复合物
可以经 <strong>p38γ</strong> 介导的 <strong>CARM1 Ser572 磷酸化</strong>调控这条通路。
通路图早就有了，缺的是<strong>体内生理证据</strong>——这篇补的就是这一块。</p>

<h2>工具与核心表型</h2>
<table>
<tr><th>环节</th><th>观察（官方摘要）</th></tr>
<tr><td>工具</td><td><strong>磷酸化缺失型敲入小鼠 CARM1 SA</strong>（Ser572 不可磷酸化）</td></tr>
<tr><td>成肌细胞</td><td>PAX7 表达下降、融合受损、肌管形成异常；但转录特征显示<strong>成肌进程加速</strong></td></tr>
<tr><td>单肌纤维离体</td><td>卫星细胞<strong>提前获得定向祖细胞身份</strong>，自我更新型卫星细胞减少</td></tr>
<tr><td><strong>肌肉发育</strong></td><td>基本正常</td></tr>
<tr><td><strong>单次损伤后再生</strong></td><td><strong>基本正常</strong></td></tr>
<tr><td><strong>反复再生挑战</strong></td><td><strong>卫星细胞池进行性耗竭</strong></td></tr>
</table>
<p>这四行放在一起是本篇最值得记住的结构：<strong>稳态正常 → 单次应激正常 → 反复应激崩塌</strong>。
如果你的实验只做「一次损伤、两周取材」，这个表型<strong>完全看不见</strong>。</p>

<h2>转录组：稳态几乎不动，再生期才暴露</h2>
<p>稳态下转录组影响极小，再生期则出现：<strong>细胞外基质相关基因下降、TGFβ-SMAD 信号受损、
Tgfbr3 表达降低、MYC 活性升高</strong>。这与「自我更新程序丧失 + 活化增强」的画像一致——
细胞不是不会修，是修完不给自己留种子。</p>

<h2>定量：摘要没有给</h2>
<p>摘要通篇无数字。以下均为<strong>待补全文</strong>：各基因型 n、损伤轮次、
卫星细胞计数变化倍数、Pax7⁺ 细胞比例、耗竭的动力学曲线。我没有从同类文献推断补全。</p>

<h2>保留意见（重要）</h2>
<ul>
<li><strong>「反复损伤」是衰老的替代模型，不是衰老本身。</strong>摘要没有设老龄组，
所以不能直接说「这解释了老年肌肉卫星细胞减少」。</li>
<li><strong>稳态影响极小</strong>这个信息很有用：说明该位点是<strong>应急制动</strong>而非基础开关，
干预窗口大概在再生期而不是稳态期。</li>
<li>bioRxiv 403，全文未取；所有表型都是定性描述。</li>
</ul>

<p>对做肌肉衰老或 MuSC（muscle stem cell）课题的人，本文最实用的一条建议是方法学上的：
<strong>加一个 serial injury 臂</strong>。否则「一次性损伤后再生正常」会被误读为「表型阴性」。</p>

<p class="small">本文为预印本，未经同行评审。</p>""",
            related=REL_CARM1),

        "BNIP3L-NIX-Mitophagy-Alzheimer-Tau-Amyloid-bioRxiv-2026.html": dict(
            topic="线粒体", ev="C", tag="预印本",
            title="BNIP3L/NIX 线粒体自噬：从人到线虫双双验证，能压住 Tau 与 Aβ 病理",
            crumb="人神经元 ↔ 线虫 DCT-1 双向验证",
            desc="缺失 BNIP3L/NIX（或线虫同源物 DCT-1）会同时恶化 Tau 与 Aβ 病理、损害神经元网络与行为；回补其活性则降低 Tau 磷酸化并显著抑制 seeding 诱导的 Tau 聚集。摘要无任何定量。",
            source=src3,
            body="""<p>阿尔茨海默病（AD）里的线粒体自噬缺陷，这两年从「相关性」走向「因果候选」。
这篇预印本的价值不在于发现了新通路，而在于把 <strong>BNIP3L/NIX 依赖性线粒体自噬</strong>
在一个<strong>跨物种、双向（缺失 + 回补）</strong>的设计里钉住了。</p>

<h2>双向验证的结构</h2>
<table>
<tr><th>方向</th><th>做了什么</th><th>结果</th></tr>
<tr><td><strong>功能缺失</strong></td><td>敲除人/鼠 BNIP3L/NIX，或线虫同源物 <strong>DCT-1</strong></td><td>基础与应激诱导的线粒体自噬均削弱、线粒体稳态破坏、<strong>Tau 与 Aβ 病理加剧</strong>；人神经元与体内模型的<strong>网络、突触、行为功能受损</strong></td></tr>
<tr><td><strong>功能回补</strong></td><td>回补 BNIP3L/NIX 与 DCT-1 活性</td><td>蛋白毒性应激下神经元功能改善、人神经元中疾病相关 <strong>Tau 磷酸化降低</strong>、原代小鼠神经元中 <strong>seeding 诱导的 Tau 聚集被显著抑制</strong></td></tr>
</table>
<p>线虫同源物的存在让这条通路有了「进化保守」的分量；而「回补有效」比单纯敲除更有转化意义——
它说明这是一个<strong>可上调的节点</strong>，而不只是一个保护性背景因素。</p>

<h2>定量：又一个零数字摘要</h2>
<p>摘要中出现的 impaired / enhanced / markedly suppressed <strong>全都没有统计量</strong>。
以下均为<strong>待补全文</strong>：样本量与重复数、mitophagy flux 变化倍数、
Tau 聚集抑制百分比、行为学效应量。不做任何推算。</p>

<h2>三条必须写明的保留意见</h2>
<ol>
<li><strong>主题是 AD，不是衰老。</strong>它被收进来是因为线粒体自噬与蛋白稳态是衰老的两大标志，
且做了跨物种验证；但<strong>摘要全篇没有把年龄当作变量</strong>——没有年龄组、没有寿命数据。
不要把它当延寿证据读。</li>
<li><strong>seeding 模型不等于散发性 AD。</strong>外源种子诱导的急性聚集，与人类散发性 AD 里
绵延十几年的慢性进程不是一回事。</li>
<li><strong>缺上游因果。</strong>摘要没说衰老过程中 BNIP3L/NIX 活性是否下降、何时下降。
这是把它接入衰老叙事的必要一环，目前空着。</li>
</ol>

<h2>对综述写作的用处</h2>
<p>如果你的综述要写「线粒体质量控制作为神经退行的共同上游」，这是一份现成的
<strong>人细胞 ↔ 线虫双向证据</strong>，比单物种敲除数据更耐审稿人追问。
另外，回补实验天然提供了一个<strong>筛选体系的正向对照</strong>（positive control），
可以用来校准平台对 mitophagy 变化的检出下限。</p>

<p class="small">本文为预印本，未经同行评审。</p>""",
            related=REL_NIX),

        "Mission-Therapeutics-MTX325-USP30-Parkinson-Phase1b-2026.html": dict(
            topic="产业", ev="B", tag="临床进展",
            title="线粒体自噬第一次走进帕金森患者：USP30 抑制剂 MTX325 完成 1b 期首例给药",
            crumb="36 例，数据读出预计 2027 年底",
            desc="Mission Therapeutics 的 USP30 抑制剂 MTX325 在英国皇家利物浦大学医院完成 1b 期首例给药，计划入组 36 例轻中度帕金森患者。USP30 是线粒体自噬的负调控去泛素化酶——这是衰老标志「线粒体功能障碍」少有的直接成药尝试。",
            source=('<em>Longevity.Technology</em>（行业媒体，2026-10-19 报道）'
                    ' · 公司原始新闻稿 <a href="https://www.globenewswire.com/news-release/2026/10/15/3381299/0/en/mission-therapeutics-doses-first-parkinson-s-patient-in-phase-1b-study-of-potential-disease-modifying-treatment-mtx325.html" target="_blank" rel="noopener noreferrer">GlobeNewswire 2026-10-15</a>'
                    ' · 公司稿首发 2026-10-15'
                    ' · 来源：IMA 知识库《行业情报周报》2026-W43（file_id dmJkBUnnRwKd）'),
            body="""<p>衰老研究里最常被引用、也最难以成药的一条标志是<strong>线粒体功能障碍</strong>。
原因很实际：线粒体太多、太分散、太基础，全局干预几乎必然带来毒性。
<strong>USP30</strong> 提供了一条绕开这个困局的路径——它不直接「修线粒体」，而是
<strong>松开线粒体自噬的刹车</strong>，让细胞自己去清理受损的那一批。</p>

<h2>这次发生了什么</h2>
<table>
<tr><th>项目</th><th>内容</th></tr>
<tr><td>药物</td><td><strong>MTX325</strong>，口服、脑渗透的 <strong>USP30 抑制剂</strong>（去泛素化酶）</td></tr>
<tr><td>机制</td><td>USP30 去除线粒体外膜上的泛素链，是线粒体自噬的<strong>负调控因子</strong>；抑制它等于放大清除信号</td></tr>
<tr><td>进展</td><td><strong>1b 期首例给药</strong>，地点为英国皇家利物浦大学医院</td></tr>
<tr><td>规模</td><td>计划入组 <strong>36 例</strong>轻中度原发性帕金森患者（英国 / 欧洲 / 澳大利亚）</td></tr>
<tr><td>主要目标</td><td><strong>临床作用机制证明（proof-of-mechanism）</strong>+ 安全性、耐受性、生物标志物与影像</td></tr>
<tr><td>数据读出</td><td>预计 <strong>2027 年底</strong></td></tr>
<tr><td>此前数据</td><td>健康志愿者 1a 期已完成；<strong>PET 证实脑部分布与较高 CNS 渗透</strong></td></tr>
<tr><td>投资方</td><td>Pfizer Venture Investments、Sofinnova Partners、Roche Venture Fund</td></tr>
<tr><td>专利</td><td>化合物专利期至 2041 年</td></tr>
</table>

<h2>为什么这条值得单独写</h2>
<p>线粒体自噬在衰老文献里被讨论了十几年，但<strong>真正以「提升线粒体自噬」为机制进入
患者给药的候选药非常少</strong>。过去几年这个方向更多停留在工具化合物与遗传学模型。
MTX325 是目前离「机制在人体里是否成立」最近的一个读数。</p>
<p>需要立刻降温的是：<strong>1b 期主要看机制与安全，不看疗效。</strong>36 例、开放标签、
主要终点不是 UPDRS——任何「改善帕金森症状」的解读，在这一期都不成立。
公司公告里提到的临床前结果（线粒体自噬增加、α-突触核蛋白聚集减少、多巴胺能神经元获益）
<strong>是动物数据</strong>，且为公司自述。</p>

<h2>与衰老研究的接口</h2>
<p>线粒体自噬是「线粒体功能障碍」这条衰老标志里<strong>最可药化的一环</strong>——
因为它是一个<strong>清除</strong>过程，而不是一个<strong>重建</strong>过程，干预点明确、可逆、有剂量窗口。
如果 2027 年底的机制数据（例如血细胞或肌肉活检中的 mitophagy 标志、PET/影像）
能在人体里给出方向一致的信号，那么这条通路的可信度会从「模型假说」升到「人体可操作」。
反过来，如果机制信号阴性，那么「提升线粒体自噬可延缓神经退行」这个叙事需要重新审视——
这对整个衰老干预领域都是一个真实的检验点。</p>

<h2>跟踪清单</h2>
<ul>
<li><strong>2027 年底</strong>：1b 期机制与安全性数据读出（关键节点）</li>
<li>中期是否有生物标志物子研究的单独披露</li>
<li>同期其他 USP30 项目的进展（该靶点并非 Mission 独家）</li>
<li>是否扩展到其他以线粒体质量控制为核心的适应症（心衰、肌少症等）</li>
</ul>

<p class="small">本文为行业情报，依据公司新闻稿与行业媒体报道整理，<strong>非同行评议研究</strong>。
涉及疗效的表述均为公司自述，本站未做独立验证。</p>""",
            related=REL_USP30),
    }

    ga.A = A
    ga.main()


if __name__ == "__main__":
    main()
