#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_articles_foundations_2026-10.py
—— 「衰老十四大标志 · 奠基文献」系列（批次 2026-10）

来源：IMA 知识库「衰老文献库_总索引」（EuropePMC DOI 精确命中），
      经 scripts/harvest.py 四路查重判定为「漏收」，并逐条在 news/*.html 全文
      中做过 DOI 与高特异关键词硬核验，确认为真漏收。
      总索引 89 条漏收里，仅这 14 条同时具备「一句话贡献 / 核心要点 /
      保留意见 / 对我的价值」四段实质笔记，且恰好一一对应 H01–H14 全部
      十四个衰老标志；其余 75 条四段笔记全空，本轮不写（见收尾报告）。

纪律（继承 SOP §4.2）：
  - 只依据总索引笔记 + 期刊公开元数据撰写，**定量一律照抄笔记，不推算补全**
  - 13 篇「仅元数据（全文未获）」已在正文明确标注「待补全文」；
    仅 H09（Dyer 1993）在共享库有归档全文
  - 证据分级 A/B/C 口径与全站一致；内链 slug 全部取自 ls news/ 实抄
"""
import html
import importlib.util
import json
import os
import re
import sys
from datetime import datetime

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
DATE = sys.argv[2] if len(sys.argv) > 2 else "2026-10-16"

# 复用 gen_articles.py 的 HEAD / ld / date_cn，确保与全站模板逐字节一致
_HERE = os.path.dirname(os.path.abspath(__file__))
_argv = sys.argv
sys.argv = [_argv[0], ROOT, "_unused", DATE]
_spec = importlib.util.spec_from_file_location("_ga", os.path.join(_HERE, "gen_articles.py"))
ga = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ga)
sys.argv = _argv

HEAD, ld, date_cn = ga.HEAD, ga.ld, ga.date_cn


def notice(ev, fulltext):
    """与全站 A/B/C 口径一致，仅替换「文献来源」段为奠基文献专用措辞。"""
    t = {"A": "A 级（同行评议人体研究）",
         "B": "B 级（同行评议临床前研究，主要为动物模型）",
         "C": "C 级（预印本 / 观点评论，非原始研究）"}[ev]
    body = {
        "A": "<p><strong>本文属人体研究证据，但需注意：</strong>观察性或小样本干预的结论不等于已证实临床获益；效应量与长期安全性仍需更大规模、更长随访的试验验证。</p>",
        "B": "<p><strong>本文核心结论来自动物模型或体外细胞学，属临床前证据，不能外推至人体。</strong>「延长健康寿命」「改善功能」等表述在小鼠中的意义，与人类临床结局之间仍有距离。</p>",
        "C": "<p><strong>本文属观点/评论类文献，不是原始研究。</strong>其论点依赖于作者对既有证据的梳理与判断，<strong>不构成新的实验证据</strong>。本站标注 C 级即为此意——阅读时请把它当作「领域内的思考框架」，而非「研究发现」。</p>",
    }[ev]
    src = ("<p><strong>关于本文的文献来源：</strong>本文是「衰老十四大标志 · 奠基文献」系列之一，"
           "条目来自 IMA 知识库「衰老文献库_总索引」（EuropePMC DOI 精确命中），"
           "正文依据<strong>库内结构化笔记与期刊公开元数据</strong>撰写。")
    if fulltext:
        src += "该文在共享库有<strong>归档全文</strong>，笔记中的定量数据均出自原文。"
    else:
        src += ("该文目前<strong>仅获元数据，全文未获取</strong>——"
                "笔记中的定量数据均照抄库内已有记录，"
                "<strong>原文页码、完整统计量与实验细节均为「待补全文」"
                "，未做任何数值推算补全</strong>。")
    src += "</p>"
    return (f'<div class="notice-box">\n'
            f'    <p><span class="tier tier-{ev.lower()}">{ev} 级</span>'
            f'<strong>证据分级：{t}</strong></p>\n'
            f'    {body}\n'
            f'    {src}\n'
            f'</div>')


def build(slug, m, related_html):
    ld_news, ld_crumb = ld(m["title"], html.escape(m["desc"], quote=True), slug, DATE, m["crumb"])
    body = m["body"].rstrip() + "\n\n" + notice(m["ev"], m.get("ft", False)) + "\n"
    return HEAD.format(
        title=html.escape(m["title"]), desc=html.escape(m["desc"], quote=True),
        slug=slug, date=DATE, date_cn=date_cn(DATE), crumb=html.escape(m["crumb"]),
        tag=html.escape(m["tag"]), topic=html.escape(m["topic"]),
        ev=m["ev"].lower(), source=m["source"], body=body,
        ld_news=ld_news, ld_crumb=ld_crumb, related=related_html,
    )


def src(journal, year, vol, authors, inst, en_title, doi, journal_url=None):
    """统一的 source 行：期刊链接 + 年份卷期 + 第一作者 + 英文原题 + DOI 链接。"""
    j = (f'<a href="{journal_url}" target="_blank" rel="noopener noreferrer">{journal}</a>'
         if journal_url else journal)
    return (f'{j}（{year}{("，" + vol) if vol else ""}）· {authors}'
            f'{("（" + inst + "）") if inst else ""} · 论文：<em>{en_title}</em> · DOI '
            f'<a href="https://doi.org/{doi}">{doi}</a>')


# ---------------- 十四篇 ----------------
A = {}

A["Mitochondrial-Decay-Oxidative-Damage-Aging-PNAS-1994.html"] = dict(
    topic="生命历程", ev="C", tag="经典回顾", ft=False,
    title="线粒体既是活性氧的来源也是它的靶子：1994 年那篇把「氧化损伤—线粒体衰减」焊在一起的奠基论述",
    crumb="H01 基因组不稳定性 · 奠基文献",
    desc="Shigenaga 与 Ames 1994 年发表于 PNAS 的论证性论述：线粒体自身产生的活性氧是随龄氧化损伤累积的主要来源，并把质子漏、膜流动性下降、心磷脂减少列为线粒体功能衰退的促成因素。这是自由基衰老学说在分子层面的集大成表述。",
    source=src("Proceedings of the National Academy of Sciences", "1994", "91(23): 10771–10778",
               "Shigenaga MK、Hagen TM、Ames BN", "加州大学伯克利分校",
               "Oxidative damage and mitochondrial decay in aging",
               "10.1073/pnas.91.23.10771"),
    body="""<p>「衰老就是氧化的累积」这句话今天听来近乎常识，但在 1994 年它仍是一个需要被系统性论证的假说。Shigenaga、Hagen 与 Ames 这篇发表于 <em>PNAS</em> 的文章，是这个假说迄今最完整的一次分子级陈述——<strong>它要回答的不是「氧化损伤是否存在」，而是「它从哪里来、为什么会随龄加速」</strong>。</p>

<h2>核心论证：线粒体是内源氧化损伤的主源</h2>

<p>需氧代谢不可避免地持续产生活性氧（ROS）。作者论证的关键一步在于指出：<strong>线粒体既是 ROS 的最大产地，又是离它最近、最易被击中的目标</strong>。于是产生一个正反馈结构——线粒体产生 ROS → ROS 损伤线粒体自身的膜、蛋白与 DNA → 受损线粒体产 ROS 效率更低但漏得更多 → 损伤进一步累积。这个结构解释了为什么氧化损伤会「随龄加速」而非线性累积。</p>

<h2>三个被点名的促成因素</h2>

<ul>
<li><strong>内膜质子漏速率</strong>——与 ROS 生成速率直接相关，是耦合效率下降的标志；</li>
<li><strong>膜流动性下降</strong>——影响电子传递链复合体的构象与功能；</li>
<li><strong>心磷脂（cardiolipin）含量与功能降低</strong>——心磷脂是线粒体内膜的特征性磷脂，它的丢失会直接动摇电子传递链的组装基础。</li>
</ul>

<blockquote><p>值得留意的是：这三条每一条都在 2026 年的研究里重新活了过来。心磷脂尤其典型——它当年只是一个生化 footnote，如今已成为可成药的内膜稳态靶点（见延伸阅读）。</p></blockquote>

<h2>今天该怎么读它</h2>

<p>这篇最直接的遗产是它把「线粒体靶向抗衰」从一句口号变成了可操作的技术路线：如果损伤主要发生在线粒体内膜，那么<strong>把抗氧化剂送进线粒体基质</strong>就是合理的工程目标——SS-31、MitoQ、SkQ1 这一类线粒体靶向化合物的设计逻辑，都可以追溯到这个论证。</p>

<p>同时它也埋下了后来几十年的争议种子：既然 ROS 是主因，那么<strong>补充抗氧化剂应当延寿</strong>。这个推论在后来的大规模人体试验中<strong>并未成立</strong>。读这篇时必须把「氧化损伤随龄累积」这个<strong>现象</strong>，与「抗氧化剂能延寿」这个<strong>推论</strong>分开——后者是被证据否定的。</p>

<h2>局限（务必连同局限一起读）</h2>

<ul>
<li>这是一篇<strong>论证性论述（Perspective/Review）而非单一实验</strong>，其力量来自对分散证据的整合，而非来自一个可复核的因果实验。</li>
<li>因果证据主要来自<strong>物种间比较</strong>（寿命与过氧化物产生量、氧化损伤程度的负相关）与转基因果蝇，<strong>哺乳动物体内的完整因果链在当时并不完整</strong>。</li>
<li>文中提到「乙酰-L-肉碱似可逆转多项随龄细胞缺损」，这在当时只是<strong>初步观察</strong>，不能作为干预有效的证据。</li>
<li>原文页码区间、各实验的具体样本量与统计量，因<strong>全文未获取</strong>，均为<strong>待补全文</strong>。</li>
</ul>
""",
    related=[("Mitochondrial-Supercomplexes-Longevity-Review-2026.html",
              "线粒体超复合体与长寿：电子传递链组装如何决定寿命"),
             ("Cardiolipin-ERRgamma-Muscle-Fiber-Switch-Nature-Aging-2026.html",
              "心磷脂-ERRγ 轴调控肌纤维类型切换：Nature Aging 揭示内膜脂质如何决定肌肉衰老"),
             ("Mitochondria-Master-Regulator-Aging-Inflammaging-2026.html",
              "线粒体：衰老的主调控器，连接能量代谢与慢性炎症")],
)

A["Telomere-Length-Predicts-Replicative-Capacity-PNAS-1992.html"] = dict(
    topic="细胞衰老", ev="B", tag="经典回顾", ft=False,
    title="端粒长度比供体年龄更能预测细胞还能分裂多少次：1992 年 PNAS 把端粒从「现象」推到了「预测模型」",
    crumb="H02 端粒磨损 · 奠基文献",
    desc="Allsopp 等 1992 年发表于 PNAS：31 名 0–93 岁供体的成纤维细胞显示，初始端粒长度是比供体年龄更强的复制寿命预测因子，解释了此前无法解释的个体间巨大差异。这是端粒作为「可测量生物标志物」的起点。",
    source=src("Proceedings of the National Academy of Sciences", "1992", "89(21): 10114–10118",
               "Allsopp RC 等 8 位作者", "加州大学旧金山分校 / McMaster 大学",
               "Telomere length predicts replicative capacity of human fibroblasts",
               "10.1073/pnas.89.21.10114"),
    body="""<p>到 1990 年代初，学界已经知道两件事：<strong>人成纤维细胞在体外只能分裂有限次数</strong>（Hayflick 极限），以及<strong>端粒会随细胞分裂而缩短</strong>。但两者之间是否真的存在定量关系，一直缺一把钥匙。Allsopp 等人 1992 年这篇 <em>PNAS</em> 论文提供的正是这把钥匙。</p>

<h2>设计：用 31 名跨 93 岁年龄跨度的供体做横断面</h2>

<p>研究收集了 <strong>31 名 0–93 岁供体</strong>的成纤维细胞株，同时测量两件事：供体的<strong>实际年龄</strong>，与细胞株的<strong>初始端粒长度</strong>；然后追踪这些细胞在体外<strong>还能分裂多少次</strong>（复制能力）。</p>

<h2>关键结果：端粒长度赢了年龄</h2>

<ul>
<li>细胞的<strong>增殖能力与供体年龄只有弱相关</strong>（r = −0.42，P = 0.02）——年龄只能解释很小一部分变异；</li>
<li><strong>端粒 DNA 长度与供体年龄相关</strong>，符合「端粒随龄磨损」的预期；</li>
<li>决定性的一步：<strong>初始端粒长度解释了此前无法解释的复制能力个体差异</strong>——同样是 60 岁供体，端粒长的细胞还能分裂更多次。</li>
</ul>

<blockquote><p>这一步的意义在于：它把端粒从「一个随龄变化的现象」变成了「一个<strong>可测量的、携带预测信息的生物标志物</strong>」。没有这个转换，后面几十年的端粒流行病学、端粒长度检测商业化、以及白细胞端粒长度作为心血管风险标志物的整条研究线都无从谈起。</p></blockquote>

<h2>它和 Harley 1990 构成的「对子」</h2>

<p>库内笔记把本文与 <strong>Harley 1990</strong> 那篇并列为「现象 → 预测模型」的奠基对子：前者确立「端粒随龄缩短」这个现象，后者证明这个现象<strong>携带可提取的预测力</strong>。两篇合起来才构成了端粒磨损作为衰老标志的完整论证。</p>

<h2>局限</h2>

<ul>
<li><strong>体外培养模型</strong>。成纤维细胞在培养皿里的复制寿命，与人体的组织再生能力、与个体的健康寿命之间，隔着好几层推论。这篇文章证明的是「端粒长度预测体外复制能力」，<strong>不是</strong>「端粒长度预测人的寿命」。</li>
<li><strong>横断面设计</strong>：供体年龄与端粒长度是同一时点测的，无纵向随访，「随龄缩短」在此是推断而非直接观测。</li>
<li><strong>相关系数 r = −0.42 属中等偏弱</strong>。年龄与复制能力之间的关联并不强，这是本文常被误读为「端粒决定一切」时需要回看的一点。</li>
<li>样本量、各亚组构成、置信区间等细节因<strong>全文未获取</strong>，为<strong>待补全文</strong>。</li>
</ul>
""",
    related=[("Telomere-Damage-Signaling-Hematopoiesis-Immune-Restore-2026.html",
              "靶向端粒损伤信号通路恢复造血与免疫功能"),
             ("Positioning-TERT-Apex-Aging-Nature-Aging-2026.html",
              "TERT：置于衰老之巅——Nature Aging 重新定义端粒酶在衰老中的核心地位"),
             ("tDDR-Inhibition-Hematopoietic-Aging-Nature-Aging-2026.html",
              "靶向端粒 DNA 损伤反应恢复造血功能：新型反义寡核苷酸策略离临床更近一步")],
)

A["ER-CpG-Island-Methylation-Aging-Colon-NatureGenetics-1994.html"] = dict(
    topic="表观遗传", ev="A", tag="经典回顾", ft=False,
    title="1994 年就有人把「随龄甲基化」和「癌症」接上了：雌激素受体 CpG 岛与表观遗传时钟的思想源头",
    crumb="H03 表观遗传改变 · 奠基文献",
    desc="Issa 等 1994 年发表于 Nature Genetics：结肠黏膜中雌激素受体基因 CpG 岛甲基化的细胞亚群比例随年龄递增，且 45 例结直肠肿瘤几乎全部携带同一改变。这是「随龄表观遗传漂移」与肿瘤易感性被首次接通的研究，也是后来表观遗传时钟思想的分子基础。",
    source=src("Nature Genetics", "1994", "8(1): 536",
               "Issa JP 等 6 位作者", "约翰斯·霍普金斯大学肿瘤中心",
               "Methylation of the oestrogen receptor CpG island links ageing and neoplasia in human colon",
               "10.1038/ng0894-536"),
    body="""<p>今天说起表观遗传衰老，第一反应通常是「甲基化时钟」——用几十个 CpG 位点的甲基化水平估算生物学年龄。但这个思路的源头，是 1994 年一篇只盯住<strong>一个基因、一个 CpG 岛</strong>的 <em>Nature Genetics</em> 论文。</p>

<h2>发现一：甲基化随年龄以「细胞亚群比例」的方式递增</h2>

<p>Issa 等人检测人结肠黏膜组织中<strong>雌激素受体（ER）基因 CpG 岛</strong>的甲基化状态。关键观察是：甲基化并不是在所有人身上均匀出现，而是<strong>携带甲基化的细胞亚群比例随年龄递增</strong>。</p>

<p>这个「亚群比例递增」的表述很重要。它暗示的机制不是「所有细胞同步改变」，而是<strong>携带异常甲基化的克隆随年龄逐步扩张、占据更大份额</strong>——这正是后来被反复验证的「表观遗传漂移 + 克隆选择」模型。</p>

<h2>发现二：同一改变几乎出现在全部结直肠肿瘤中</h2>

<ul>
<li><strong>45 例结直肠肿瘤几乎全部存在该 ER CpG 岛甲基化改变</strong>，<strong>包括最早的病变阶段</strong>——说明它发生在肿瘤发生的早期，而非进展的后果；</li>
<li>肿瘤组织中 <strong>ER 表达下降</strong>；</li>
<li>功能性验证：在结肠癌细胞中<strong>外源导入 ER 可抑制细胞生长</strong>——把甲基化、表达沉默与增殖表型串成了一条链。</li>
</ul>

<blockquote><p>把这两组发现合起来看，本文提出的模型是：<strong>年龄 → 某基因 CpG 岛甲基化的细胞亚群扩张 → 抑癌/分化相关基因表达沉默 → 肿瘤易感性上升</strong>。这条链把「衰老」和「癌症」这两个长期被分开研究的现象，第一次放在了同一个分子机制上。</p></blockquote>

<h2>它为什么是表观遗传时钟的思想源头</h2>

<p>核心贡献在于提出了「<strong>随龄表观遗传漂移可被定量</strong>」这件事。本文只看一个 CpG 岛，当然成不了时钟；但它确立了一个可推广的逻辑——如果甲基化随年龄单调变化，那么<strong>测量一批位点的甲基化水平就能反推年龄</strong>。2010 年代 Horvath 时钟、PhenoAge、GrimAge 等一系列工作，是这个逻辑在全基因组尺度上的实现。</p>

<h2>局限</h2>

<ul>
<li><strong>单基因、单 CpG 岛</strong>，不是全基因组图谱。本文能证明的是「这个位点的甲基化随龄变化」，<strong>不能据此推断全基因组甲基化景观的变化规律</strong>。</li>
<li><strong>样本限于结肠黏膜</strong>。不同组织的甲基化漂移速率与方向差异很大，本文结论不能直接外推到其他组织。</li>
<li>「外源导入 ER 抑制生长」是<strong>体外细胞系实验</strong>，属机制提示而非体内因果证明。</li>
<li>全基因组随龄甲基化图谱要等到 2010 年代才出现——本文的价值是<strong>提出问题</strong>，而非给出全景。</li>
<li>45 例肿瘤的分期构成、正常黏膜对照数、甲基化比例的统计检验，因<strong>全文未获取</strong>，为<strong>待补全文</strong>。</li>
</ul>
""",
    related=[("Longitudinal-Epigenetic-Clock-InCHIANTI-Mortality-2026.html",
              "表观遗传时钟纵向变化预测死亡风险：InCHIANTI 队列 24 年追踪研究"),
             ("DNA-Methylation-Clock-Epigenetic-Progeria-2026.html",
              "DNA 甲基化时钟：被拆解的早衰密码"),
             ("DNA-Methylation-Clock-Socioeconomic-Mortality-2026.html",
              "DNA 甲基化时钟揭示社会健康不平等的生物学机制")],
)

A["Protein-Oxidation-Aging-JBC-1997.html"] = dict(
    topic="细胞衰老", ev="C", tag="经典回顾", ft=False,
    title="细胞处理氧化蛋白的能力为什么会随龄下降：1997 年 JBC 把「氧化损伤」接上了「蛋白稳态」",
    crumb="H04 蛋白稳态丧失 · 奠基文献",
    desc="Berlett 与 Stadtman 1997 年发表于 JBC 的综述：蛋白质氧化修饰（尤其是羰基化）随龄累积，而降解系统对氧化蛋白的清除效率随龄下降，二者共同构成蛋白稳态丧失的分子基础。这是把氧化应激与蛋白稳态两条研究线焊在一起的关键论述。",
    source=src("The Journal of Biological Chemistry", "1997", "272(33): 20313–20316",
               "Berlett BS、Stadtman ER", "美国国立心肺血液研究所（NHLBI）",
               "Protein oxidation in aging, disease, and oxidative stress",
               "10.1074/jbc.272.33.20313"),
    body="""<p>「氧化应激」和「蛋白稳态丧失」在今天的衰老标志框架里是两个相邻的条目，但它们最初来自两条几乎不相干的研究传统：前者源自自由基化学，后者源自蛋白质降解与折叠生物学。Berlett 与 Stadtman 这篇 1997 年的 <em>JBC</em> 综述，是把这两条线接起来的关键一环。</p>

<h2>两个必须同时成立的条件</h2>

<p>本文的论证结构其实很简单，但正因为简单才有力量——蛋白稳态的崩溃需要<strong>两个方向同时失衡</strong>：</p>

<ul>
<li><strong>生成端</strong>：蛋白质的氧化修饰（尤其是<strong>羰基化</strong>）随龄累积。羰基化是不可逆修饰，被打上这个标记的蛋白质通常已经失活；</li>
<li><strong>清除端</strong>：降解系统对<strong>氧化蛋白的清除效率随龄下降</strong>。</li>
</ul>

<p>注意这两个条件的乘积关系：如果生成增加但清除同步跟上，损伤不会累积；如果清除下降但没有损伤生成，也不会有底物堆积。<strong>衰老的问题在于两者同时发生</strong>——这正是本文最核心的洞察。</p>

<blockquote><p>顺带说一句，这个「生成 × 清除」的框架，与 2026 年本站反复报道的自噬衰退、蛋白酶体活性下降、分子伴侣介导自噬（CMA）失效等一系列工作是同一套逻辑。1997 年这篇提出的不是某个具体分子，而是<strong>一个至今通用的分析框架</strong>。</p></blockquote>

<h2>氧化应激作为「上游共同因素」的定位</h2>

<p>本文把氧化应激放在上游：它既是蛋白氧化修饰的直接来源，也被认为参与了其他随龄损伤过程。库内笔记特别指出，这一论证与同期两篇工作构成互相支撑的证据链——<strong>「Proteasome inactivation upon aging」</strong>与<strong>「Aging and proteolysis of oxidized proteins」</strong>。三篇合起来才把「氧化 → 蛋白损伤 → 降解失效」这条链钉住。</p>

<h2>为什么它值得在 2026 年重读</h2>

<p>因为当前许多抗衰策略的靶点，都落在这条链上：激活蛋白酶体、增强自噬、提升分子伴侣能力、直接清除氧化蛋白。<strong>这些策略共享的前提，正是本文论证的「清除端失效是衰老的可干预环节」。</strong>理解了这个前提，才能理解为什么「提升降解能力」而不是「减少氧化」成为了主流工程路线——后者在人体试验中的失败已经太多了。</p>

<h2>局限</h2>

<ul>
<li>这是一篇 <strong>Mini-review</strong>，篇幅短、以整合为主，<strong>不是原始研究报告</strong>。</li>
<li>论据<strong>以作者自身系列工作为主</strong>。Stadtman 实验室是蛋白质羰基化研究的奠基者，本文的文献覆盖不可避免地带有该实验室的视角权重。</li>
<li>本文发表时 <strong>Europe PMC 未收录其摘要</strong>，因此本条目可用的公开元数据极为有限。</li>
<li>清除效率随龄下降的定量幅度、所引用的具体实验体系与统计量，因<strong>全文未获取</strong>，为<strong>待补全文</strong>。</li>
</ul>
""",
    related=[("Blm10-PA200-20S-Proteasome-Alpha-Synuclein-2026.html",
              "Blm10/PA200 蛋白酶体激活剂：绕过蛋白酶体抑制的新策略——Aging Cell 研究"),
             ("DUB-Oxidative-Stress-Brain-Aging-NACET-2026.html",
              "去泛素化酶活性丧失：脑衰老中「可逆」的早期驱动因素"),
             ("CMA-Decline-Macrophage-Senescent-Clearance-NatureAging-2026.html",
              "CMA 衰退让「僵尸细胞」逃过免疫清除：Nature Aging 揭示衰老细胞堆积的双重失效")],
)

A["Autophagy-Yeast-Proteinase-Deficient-JCB-1992.html"] = dict(
    topic="细胞衰老", ev="B", tag="经典回顾", ft=False,
    title="大隅良典的起点：1992 年那篇用蛋白酶缺陷酵母「看见」自噬的论文",
    crumb="H05 巨自噬失能 · 奠基文献",
    desc="Takeshige 等 1992 年发表于 JCB：用蛋白酶缺陷酵母突变株在营养缺乏条件下观察到液泡内自噬体累积，首次把自噬确立为可遗传学操作的细胞过程。这是大隅良典自噬研究系列的起点，也是 2016 年诺贝尔奖工作的源头。",
    source=src("The Journal of Cell Biology", "1992", "119(2): 301–311",
               "Takeshige K、Baba M、Tsuboi S、Noda T、Ohsumi Y", "东京大学理学部植物学教室",
               "Autophagy in yeast demonstrated with proteinase-deficient mutants and conditions for its induction",
               "10.1083/jcb.119.2.301"),
    body="""<p>自噬这个概念在 1960 年代就由 Christian de Duve 提出并命名，但此后的三十年裡，它基本停留在<strong>形态学描述</strong>的层面——看得见，但没法操作。1992 年这篇 <em>JCB</em> 论文改变了这一点，方法是<strong>把一个「看得见但抓不住」的过程，变成了一个可以遗传学操作的系统</strong>。</p>

<h2>巧妙的实验设计：让自噬体「堆积」起来</h2>

<p>关键技法是<strong>蛋白酶缺陷酵母突变株</strong>。原理是这样的：正常情况下，自噬体与液泡融合后，其内容物会被液泡内的蛋白酶（蛋白酶 A、蛋白酶 B、羧肽酶 Y）<strong>迅速降解</strong>——所以你只能看到「空泡」，看不到正在被降解的中间态。</p>

<p>作者把这些蛋白酶<strong>敲掉</strong>。于是降解这一步被卡住，自噬体融进液泡之后不再消失，而是<strong>在液泡腔内不断堆积</strong>。一个瞬态过程因此被「冻结」成了可观察、可计量的形态。</p>

<h2>观察到的现象</h2>

<ul>
<li>蛋白酶缺陷株转入<strong>营养缺乏培养基</strong>后 <strong>1 小时</strong>即出现球形小体；</li>
<li><strong>3 小时</strong>后这些小体几乎<strong>充满液泡腔</strong>；</li>
<li>电镜确认这些小体是<strong>双层膜自噬体</strong>；</li>
<li>液泡腔<strong>体积同步增大</strong>；</li>
<li>由此确立：<strong>自噬是液泡内蛋白降解的形态学基础</strong>——即营养缺乏时，细胞大量降解自身蛋白以维持生存。</li>
</ul>

<blockquote><p>这篇论文的贡献常被概括为「证明了自噬存在」。更准确的说法是：它<strong>提供了第一个可用的自噬实验系统</strong>。有了这个系统，才可能有后来的 <em>APG/ATG</em> 基因筛选——大隅良典团队正是用同一策略筛选出自噬缺陷突变体，从而克隆出第一批自噬必需基因。没有 1992 年的这套系统，就没有 2016 年的诺贝尔化学奖。</p></blockquote>

<h2>与衰老的连接是后来的事</h2>

<p>必须诚实地说：<strong>这篇论文与衰老没有直接关系</strong>。它的全部实验都在酵母里完成，目的是证明自噬作为细胞过程的存在与可诱导性。哺乳动物自噬与衰老之间的直接联系，要等到 2000 年代才逐步建立——包括自噬随龄下降、自噬基因的多态性与长寿关联、以及清除损伤线粒体（线粒体自噬）在衰老中的作用。</p>

<p>把它放在「奠基文献」位置上的理由是：<strong>它提供了此后全部自噬-衰老研究的概念工具与遗传学工具</strong>。今天所有讨论「恢复自噬能否抗衰」的工作，术语与机制框架都来自这条线。</p>

<h2>局限</h2>

<ul>
<li><strong>酵母单细胞模型</strong>。酵母液泡与哺乳动物溶酶体虽有同源性，但调控网络差异巨大，<strong>酵母中的自噬诱导条件不能直接映射到哺乳动物</strong>。</li>
<li>本文<strong>未涉及任何衰老表型或寿命数据</strong>——把它归入「衰老标志 H05 奠基文献」，是追溯研究传统的结果，不是本文自身的结论。</li>
<li>不同突变株的具体遗传背景、各时间点的定量统计，因<strong>全文未获取</strong>，为<strong>待补全文</strong>。</li>
</ul>
""",
    related=[("Autophagy-Restore-Glaucoma-Retinal-Ganglion-2026.html",
              "恢复自噬可保护青光眼视网膜神经节细胞：mTOR 抑制剂新机制研究"),
             ("CMA-Decline-Macrophage-Senescent-Clearance-NatureAging-2026.html",
              "CMA 衰退让「僵尸细胞」逃过免疫清除：Nature Aging 揭示衰老细胞堆积的双重失效"),
             ("FGF21-SIRT1-Disc-Degeneration.html",
              "FGF21 与 SIRT1 延缓椎间盘退变：生长因子抗衰老新机制")],
)

A["daf-2-Insulin-Receptor-Longevity-Science-1997.html"] = dict(
    topic="代谢与营养", ev="B", tag="经典回顾", ft=False,
    title="一条基因把寿命翻一倍：1997 年 daf-2 论文如何开启「营养感应调控衰老」的整个领域",
    crumb="H06 营养感应失调 · 奠基文献",
    desc="Kimura、Tissenbaum、Liu 与 Ruvkun 1997 年发表于 Science：克隆 daf-2 并证明它编码胰岛素受体家族成员，降低 DAF-2 信号同时延长线虫寿命并诱导 dauer 形成。这是第一次把胰岛素样代谢控制与寿命调控在分子层面直接连接。",
    source=src("Science", "1997", "277(5328): 942–946",
               "Kimura KD、Tissenbaum HA、Liu Y、Ruvkun G", "哈佛医学院 / 麻省总医院分子生物学系",
               "daf-2, an insulin receptor-like gene that regulates longevity and diapause in Caenorhabditis elegans",
               "10.1126/science.277.5328.942"),
    body="""<p>在 1997 年之前，「营养/代谢与寿命有关」更多是一条<strong>生理学观察</strong>——1930 年代起就知道限制热量能延长啮齿动物寿命，但没人知道这背后的分子开关是什么。Ruvkun 团队这篇 <em>Science</em> 论文第一次给出了一个具体的基因，而且它是一个<strong>胰岛素受体</strong>。</p>

<h2>发现：daf-2 是一个胰岛素受体家族成员</h2>

<p>研究克隆了线虫的 <strong>daf-2</strong> 基因。这个基因此前因调控 <strong>dauer</strong>（一种在恶劣环境下进入的休眠幼虫态）而被熟知。测序结果出人意料又合乎逻辑：<strong>daf-2 编码的蛋白属于胰岛素受体家族</strong>。</p>

<h2>一个信号，两种表型</h2>

<ul>
<li><strong>降低 DAF-2 信号</strong>会同时引发两件事：<strong>代谢与发育改变</strong>（诱导 dauer 形成），以及<strong>寿命延长</strong>；</li>
<li>这两件事被同一个受体调控，说明它们<strong>共享同一套分子机制</strong>——这不是巧合，而是「在食物不足时进入节能、延寿模式」这一适应性程序的两个侧面。</li>
</ul>

<blockquote><p>这才是本文真正的洞察：<strong>寿命不是被某个「寿命基因」单独设定的，而是被一套评估环境营养状况的信号系统所调节的可塑性状</strong>。daf-2 是这套系统的入口。</p></blockquote>

<h2>与哺乳动物热量限制的机制同构</h2>

<p>本文直接指出：<strong>线虫中 DAF-2 通路的作用，与哺乳动物热量限制延长寿命的机制是同构的</strong>。这个判断把 1930 年代以来的热量限制研究，与新兴的分子遗传学接了起来，并提出了「代谢—休眠—寿命的普遍联系」这一跨物种框架。</p>

<h2>它开启了什么</h2>

<p>今天被统称为「营养感应网络」的全部靶点——<strong>mTOR、AMPK、sirtuins、IGF-1/胰岛素通路</strong>——在概念上都从属于本文打开的这扇门。可以说，<strong>过去三十年抗衰药理学的主干线，就是从 daf-2 出发的</strong>：二甲双胍、雷帕霉素、GLP-1 受体激动剂作为「热量限制模拟物」的整套叙事，其合法性都建立在「营养感应通路可调控寿命」这一命题上。</p>

<h2>局限</h2>

<ul>
<li><strong>线虫模型</strong>。从线虫到小鼠再到人，这条通路每一级的保守性都不完全，效应量逐级衰减——这是解读全部后续转化研究时必须记住的折扣系数。</li>
<li>本文<strong>只证明 daf-2 本身</strong>。下游转录因子 <strong>DAF-16</strong>（FoxO 同源物）的作用，是由同年其他实验室独立证明的，本文未涵盖。</li>
<li>「延长寿命」的<strong>具体幅度</strong>、各突变等位基因的表型强弱排序，因<strong>全文未获取</strong>，为<strong>待补全文</strong>。</li>
</ul>
""",
    related=[("Lsp2-mTORC1-TOP-mRNA-Drosophila-Lifespan-Nature-2026.html",
              "不必少吃也能延寿：果蝇「营养传感器」Lsp2 找到延寿开关，绕开雷帕霉素"),
             ("IGF1R-Inhibitors-Extend-Healthspan-Mouse-2026.html",
              "小分子 IGF-1R 抑制剂可延长小鼠健康寿命"),
             ("Semaglutide-Lifespan-Extension-Nature-2026.html",
              "Nature 封面研究：晚年司美格鲁肽治疗显著延长小鼠寿命——或为热量限制模拟物")],
)

A["Oxidative-Stress-Caloric-Restriction-Aging-Science-1996.html"] = dict(
    topic="代谢与营养", ev="C", tag="经典回顾", ft=False,
    title="热量限制为什么延寿？1996 年 Science 给出的答案是「降低氧化损伤」——以及这个答案后来遇到的问题",
    crumb="H07 线粒体功能障碍 · 奠基文献",
    desc="Sohal 与 Weindruch 1996 年发表于 Science 的综述：系统论证氧化应激是衰老的主要成因，并梳理热量限制通过降低氧化损伤延缓衰老的证据。这是「热量限制—氧化应激—寿命」框架的经典表述，也是理解此后所有饮食干预抗衰工作的参照系。",
    source=src("Science", "1996", "273(5271): 59–63",
               "Sohal RS、Weindruch R", "南卫理公会大学 / 威斯康星大学",
               "Oxidative stress, caloric restriction, and aging",
               "10.1126/science.273.5271.59"),
    body="""<p>热量限制（CR）是衰老研究中最古老的确定性现象：从 1930 年代起就知道，在营养不缺乏的前提下减少热量摄入能延长啮齿动物寿命。但「<strong>为什么</strong>」这个问题一直悬着。Sohal 与 Weindruch 1996 年这篇 <em>Science</em> 综述给出了当时最系统的一个答案：<strong>CR 通过降低氧化损伤起作用</strong>。</p>

<h2>论证的两条腿</h2>

<p>文章的结构是「先立机制，再解释干预」：</p>

<ul>
<li><strong>腿一：氧化应激是衰老的成因。</strong>需氧代谢持续产生活性氧，促氧化与抗氧化之间的失衡构成慢性氧化应激，进而驱动随龄损伤累积。支持证据包括：过表达抗氧化酶可延缓果蝇随龄氧化损伤累积并<strong>延长最长寿命</strong>；物种间比较显示，寿命与过氧化物产生量、氧化损伤程度呈负相关。</li>
<li><strong>腿二：CR 的作用是降低氧化损伤。</strong>文章综述了 CR 降低氧化损伤的证据，从而把「CR 延寿」这个现象装进了「氧化应激致衰」这个机制框架。</li>
</ul>

<blockquote><p>这个框架的力量在于简洁：它把「少吃」和「活得久」用一条因果链连起来，且这条链上每一步都可测量。这正是它此后三十年成为领域默认参照系的原因——<strong>今天几乎每一篇饮食干预抗衰的论文，都在显性或隐性地与这个框架对话。</strong></p></blockquote>

<h2>必须补上的后半段故事</h2>

<p>读这篇时不能只读前半段。这个框架推出后被广泛接受，并直接催生了「补充抗氧化剂应当延寿」的推论——而<strong>这个推论在大规模人体试验中被否定了</strong>：维生素 E、维生素 C、β-胡萝卜素等的随机对照试验未能显示延寿获益，部分亚组甚至显示风险信号。</p>

<p>后续研究的修正大致有两个方向：一是<strong>ROS 并非单纯的损伤因子，低水平 ROS 是必要的信号分子</strong>（线粒体毒物兴奋效应，mitohormesis），一味清除反而有害；二是<strong>CR 的机制远不止降低氧化损伤</strong>——它还涉及营养感应通路（mTOR、AMPK、sirtuins）、自噬、蛋白稳态、炎症等多个层面。</p>

<h2>今天该怎么用它</h2>

<p>把它当作<strong>一个历史坐标</strong>而非操作指南。它的价值在于提供了「饮食干预—氧化损伤—寿命」这条最清晰的因果链假设，让后来的研究有东西可以证伪。<strong>科学史上被推翻的框架同样重要，尤其是当它被推翻得如此彻底、如此有教育意义的时候。</strong></p>

<h2>局限</h2>

<ul>
<li>这是一篇<strong>综述性论证</strong>，不是原始研究报告。</li>
<li>因果证据主要来自<strong>果蝇转基因实验与物种间比较</strong>。作者自己也指出：<strong>哺乳动物中的完整因果链在当时尚不完整</strong>——这一点在三十年后依然只被部分填补。</li>
<li>「延长最长寿命」这一表述在当时的测量标准下存在争议，与今天的寿命曲线统计口径不完全一致。</li>
<li>所引用的具体实验体系、样本量与统计量，因<strong>全文未获取</strong>，为<strong>待补全文</strong>。</li>
</ul>
""",
    related=[("Phosphatidylcholine-Synthesis-Mitochondrial-Aging-2026.html",
              "磷脂酰胆碱合成下降：驱动天然线粒体衰老的关键机制"),
             ("Exercise-Mitochondrial-Quality-Control-Brain-Aging-2026.html",
              "运动通过线粒体质量控制机制对抗大脑衰老"),
             ("Caloric-Restriction-Somatic-Mutation-Genome-Integrity-Cell-2026.html",
              "热量限制能降低小鼠全基因组体细胞突变：基因组完整性是可改造的衰老轴")],
)


A["SA-beta-gal-Senescence-Biomarker-PNAS-1995.html"] = dict(
    topic="细胞衰老", ev="A", tag="经典回顾", ft=False,
    title="把「衰老细胞」染成蓝色的那篇论文：1995 年 SA-β-gal 标志物的建立与其三十年后仍在使用的理由",
    crumb="H08 细胞衰老 · 奠基文献",
    desc="Dimri 等 1995 年发表于 PNAS：发现在 pH 6 条件下的衰老相关 β-半乳糖苷酶活性，可在培养细胞与在体老年皮肤活检中识别衰老细胞，首次为「细胞衰老确实发生在体内」提供了可视化证据。SA-β-gal 至今仍是衰老细胞检测的默认手段。",
    source=src("Proceedings of the National Academy of Sciences", "1995", "92(20): 9363–9367",
               "Dimri GP 等 10 位作者", "北卡罗来纳大学 Lineberger 综合癌症中心",
               "A biomarker that identifies senescent human cells in culture and in aging skin in vivo",
               "10.1073/pnas.92.20.9363"),
    body="""<p>细胞衰老（cellular senescence）作为<strong>体外现象</strong>在 1960 年代就被 Hayflick 描述了。但此后三十年裡有一个悬而未决的问题：<strong>体内真的有衰老细胞吗？</strong>培养皿里的细胞停止分裂是一回事，活体组织里是否也存在同样状态的细胞，完全是另一回事——因为没有办法把它们标出来。</p>

<p>Dimri 等人 1995 年这篇 <em>PNAS</em> 论文提供的正是这个标记方法，而且简单到近乎粗暴：<strong>在 pH 6 条件下检测 β-半乳糖苷酶活性</strong>。</p>

<h2>方法为什么是 pH 6</h2>

<p>溶酶体 β-半乳糖苷酶的最适 pH 约为 4。作者发现，衰老细胞的<strong>溶酶体含量大幅增加</strong>，使得即使在 pH 6（远高于最适 pH、正常细胞基本不显色）的条件下，衰老细胞仍能被检出明显的酶活性。染色后衰老细胞呈蓝色，这就是 <strong>SA-β-gal</strong>（senescence-associated β-galactosidase）名称的由来。</p>

<h2>两个层面的验证</h2>

<ul>
<li><strong>培养细胞</strong>：复制衰老的成纤维细胞与经诱导早衰的细胞均呈阳性；</li>
<li><strong>在体组织</strong>——这是决定性的一步：在<strong>老年个体皮肤活检</strong>中检出了 SA-β-gal 阳性细胞，而年轻个体皮肤中显著更少。</li>
</ul>

<blockquote><p>这一步的意义怎么强调都不过分：它<strong>首次为「细胞衰老是发生在体内的真实现象」提供了可视化证据</strong>。在此之前，细胞衰老只是一种体外培养观察到的细胞行为；在此之后，它是一个可以在组织切片上被指认出来的实体。整个 senolytics（衰老细胞清除）领域的合法性，都建立在这个「体内确实有可靶向的衰老细胞」的前提上。</p></blockquote>

<h2>三十年后仍在使用的理由，以及它的代价</h2>

<p>SA-β-gal 至今仍是衰老细胞检测的<strong>默认手段</strong>。理由很实际：便宜、无需特殊设备、在组织切片上可直接观察。本站报道的 2026 年多项研究，从肾脏多组学到椎间盘退变，仍在使用它作为衰老细胞负荷的读数。</p>

<p>但代价也必须说清楚：<strong>该酶活性来源于溶酶体，并非衰老特异</strong>。任何导致溶酶体含量增加的状态——包括某些巨噬细胞活化、融合、以及单纯的汇合过度——都可能产生假阳性。这一点在本文发表后不久就引发争议，并延续至今。</p>

<h2>局限</h2>

<ul>
<li><strong>非衰老特异性</strong>。这是最主要的技术局限，也是此后三十年方法学改进的主要靶点——p16^INK4a、p21、SASP 因子谱、以及深度学习评分等替代手段，都是为补这个洞而出现的。</li>
<li><strong>无单细胞分辨率</strong>（以当时的标准）。染色是组织层面的，难以与细胞类型身份、转录状态精细对应。</li>
<li><strong>皮肤活检样本</strong>：本文的在体证据限于皮肤，能否代表其他组织当时的衰老细胞负荷，本文未回答。</li>
<li>年轻与老年组的样本数、阳性细胞比例的统计检验、以及各诱导衰老模型的处置细节，因<strong>全文未获取</strong>，为<strong>待补全文</strong>。</li>
</ul>
""",
    related=[("Cell-Senescence-Biological-Complexity-Nature-Reviews-2026.html",
              "Nature Reviews 综述：重新审视细胞衰老"),
             ("Mitochondrial-Metabolism-Epigenetic-SASP-Nature-2026.html",
              "Nature 重磅：线粒体代谢驱动衰老细胞 SASP——全新药物靶点浮现"),
             ("SASP-Paracrine-Spreading-Senescence-Human-Brain-Cell-Types-2026.html",
              "衰老如何在大脑细胞间传播：SASP 旁分泌机制研究")],
)

A["Maillard-Products-Skin-Collagen-JCI-1993.html"] = dict(
    topic="细胞衰老", ev="A", tag="经典回顾", ft=True,
    title="糖化只涨 33%，糖氧化涨了 5 倍：1993 年 JCI 如何把「糖氧化」确立为胶原老化的主驱动",
    crumb="H09 细胞外基质变化 · 奠基文献",
    desc="Dyer 等 1993 年发表于 JCI：测定 39 例 1 型糖尿病与 52 例对照的皮肤胶原，发现初始糖化产物随龄仅升 33%，而糖氧化产物（CML、pentosidine）升约 5 倍。这确立了「糖氧化」而非单纯糖化是胶原老化的主驱动，是 AGEs 研究的定量起点。",
    source=src("The Journal of Clinical Investigation", "1993", "91(6): 2463–2469",
               "Dyer DG 等 7 位作者", "Case Western Reserve 大学医学院",
               "Accumulation of Maillard reaction products in skin collagen in diabetes and aging",
               "10.1172/jci116481"),
    body="""<p>Maillard 反应（非酶糖化）早在 1912 年就被描述，它让食物在加热时变褐、变香。但它在<strong>人体组织里随龄发生什么</strong>，在 1990 年代初仍缺少可靠的定量数据。Dyer 等人这篇 <em>JCI</em> 论文填补了这个空白，而且给出了一个反直觉的结果。</p>

<h2>设计：糖尿病是一把「加速器」</h2>

<p>研究测定了 <strong>39 例 1 型糖尿病患者</strong>与 <strong>52 例对照</strong>的皮肤胶原活检样本。纳入糖尿病组的逻辑很聪明：<strong>如果 Maillard 产物确实由葡萄糖驱动，那么长期高血糖应当显著加速它的累积</strong>——糖尿病组因此成了一个天然的加速模型。</p>

<h2>核心结果：糖化与糖氧化不是一回事</h2>

<p>这是本文最重要的一张对照表：</p>

<ul>
<li><strong>初始糖化产物</strong>（果糖赖氨酸）：从 20 岁到 85 岁<strong>仅上升 33%</strong>；</li>
<li><strong>糖氧化产物</strong>——<strong>CML</strong>（羧甲基赖氨酸）、<strong>pentosidine</strong>（戊糖素）与胶原荧光——同期<strong>上升约 5 倍</strong>，且与年龄<strong>强相关</strong>；</li>
<li>糖尿病使<strong>糖氧化产物进一步升高</strong>。</li>
</ul>

<blockquote><p>这个 33% vs 500% 的对比是全文的枢纽。它说明：真正随龄驱动胶原变性的<strong>不是葡萄糖与蛋白的初始结合</strong>，而是<strong>后续被氧化修饰的那一批产物</strong>。换句话说，<strong>氧化步骤才是瓶颈</strong>。这个结论直接改变了此后 AGEs 研究的重心——从「降低血糖」转向「阻断氧化环节与清除已形成的交联」。</p></blockquote>

<h2>为什么它至今仍是实证基础</h2>

<p>本文的三条结论今天都被反复引用：</p>

<ul>
<li><strong>AGEs/ALEs 随龄累积</strong>的定量证据——这是「细胞外基质变化」作为衰老标志的直接实测支撑；</li>
<li><strong>胶原交联与组织僵硬</strong>的关联——这条线今天延伸到动脉硬化、皮肤老化、椎间盘退变与肺纤维化；</li>
<li><strong>糖尿病 = 加速老化模型</strong>的定量证明——这条线今天延伸到「糖尿病患者的生物学年龄高于实足年龄」这一整套研究。</li>
</ul>

<p>本站 2026 年报道的 CMLase 工程酶研究，其立论前提正是本文建立的「CML 是随龄累积且功能有害的主要 AGE」这一结论。</p>

<h2>局限</h2>

<ul>
<li><strong>皮肤胶原</strong>。皮肤是长半衰期蛋白富集的方便取材部位，但<strong>外推到血管、软骨、肺等其他组织需谨慎</strong>——各组织的胶原周转率与糖化程度差异很大。</li>
<li><strong>横断面设计</strong>。20→85 岁的差异来自不同个体间的比较，<strong>不是同一批人随时间变化的纵向观测</strong>；出生年份队列效应无法排除。</li>
<li>糖尿病组与对照组的年龄匹配、性别构成、以及各产物的具体统计检验，<strong>需回看归档全文复核</strong>（该文在共享库有归档 PDF）。</li>
</ul>
""",
    related=[("ECM-Aging-Senescence-Circuit-Nature-Aging-2026.html",
              "Nature Aging：细胞外基质老化——衰老细胞积累的「自强化回路」"),
             ("AGEs-Glycation-Tissue-Stiffness-2026.html",
              "AGEs 糖化终产物：组织僵硬与衰老的分子驱动因素"),
             ("CMLase-Enzyme-Breaks-Down-CML-AGEs-Nature-Communications-2026.html",
              "CMLase：工程酶可逆转 CML-AGE 蛋白质损伤")],
)

A["Aging-Hematopoietic-Stem-Cells-NatureMedicine-1996.html"] = dict(
    topic="细胞衰老", ev="B", tag="经典回顾", ft=False,
    title="数量多 5 倍，功能只剩 1/4：1996 年那篇确立「干细胞老化 = 数量与功能解耦」的论文",
    crumb="H10 干细胞耗竭 · 奠基文献",
    desc="Morrison 等 1996 年发表于 Nature Medicine：纯化老年小鼠造血干细胞与年轻对照做单细胞比较，发现老年 HSC 数量多 5 倍但归巢与重建效率仅 1/4，且更多处于细胞周期。这确立了干细胞衰老「数量与功能解耦」的范式。",
    source=src("Nature Medicine", "1996", "2(9): 1011–1016",
               "Morrison SJ、Wandycz AM、Akashi K、Globerson A、Weissman IL", "斯坦福大学医学院",
               "The aging of hematopoietic stem cells",
               "10.1038/nm0996-1011"),
    body="""<p>直觉上，「干细胞耗竭」应该是干细胞变少了。1996 年这篇 <em>Nature Medicine</em> 论文给出的结果恰好相反，而且这个反直觉的发现此后成为了整个领域的标准图景。</p>

<h2>方法：纯化 + 有限稀释单细胞重建</h2>

<p>研究用表面标志物<strong>纯化</strong>出老年小鼠与年轻小鼠的造血干细胞（HSC），做<strong>有限稀释单细胞重建实验</strong>——即把单个 HSC 移植进受致死辐照的受体鼠，观察它能否重建整个造血系统。这是当时能给出的最严格的功能性读数。</p>

<h2>核心结果：一个悖论</h2>

<ul>
<li><strong>单细胞层面</strong>：老年与年轻 HSC 的<strong>体内祖细胞活性没有差别</strong>——单拎出来看，单个老年干细胞并不比年轻的差；</li>
<li><strong>群体频率</strong>：老年骨髓中 HSC 的<strong>频率高 5 倍</strong>；</li>
<li><strong>归巢与植入效率</strong>：老年 HSC 的归巢与植入效率<strong>降至 1/4</strong>；</li>
<li><strong>细胞周期</strong>：老年 HSC <strong>频繁进入 S/G2/M 期</strong>，年轻 HSC 罕见。</li>
</ul>

<blockquote><p>把这四条合起来，浮现的图景是：<strong>老年骨髓里干细胞更多，但每一个都不太能干活</strong>。数量上升很可能是<strong>对功能下降的代偿</strong>——系统试图用更多的干细胞来弥补每个干细胞的效率损失。这就是「<strong>数量与功能解耦</strong>」这个范式的由来。</p></blockquote>

<h2>为什么它定义了后来的研究议程</h2>

<p>这个范式直接决定了后续三十年造血衰老研究的提问方式。人们不再问「干细胞还剩多少」，而是问「<strong>为什么剩下的这些不好用了</strong>」——答案逐步指向 DNA 损伤累积、表观遗传漂移、极性丧失、自噬下降、以及骨髓微环境（niche）的炎症化。</p>

<p>本文确立的现象也是今天<strong>老年克隆性造血（CHIP）</strong>研究的直接上游：如果老年 HSC 池由大量低功能、高周转的细胞构成，那么携带优势突变的克隆在其中扩张，几乎是必然的结果。CHIP 与心血管风险、血液肿瘤风险的关联研究，都建立在这个池子动力学的基础之上。</p>

<h2>局限</h2>

<ul>
<li><strong>小鼠模型</strong>。小鼠与人的造血系统在寿命尺度、HSC 周转速率、以及克隆动力学上差异显著，<strong>定量关系（5 倍、1/4）不能直接外推至人类</strong>。</li>
<li>对「数量↑功能↓」悖论的<strong>机制解释，在本文中是作者自称的推测</strong>，不是实验证明的部分。这一点常被后来的综述误引为本文结论。</li>
<li>1996 年的 HSC 纯化方案（表面标志物组合）与今天的标准不完全一致，<strong>当时定义的「HSC 群体」纯度低于现今水平</strong>——频率数据应在此前提下理解。</li>
<li>移植受体数、稀释梯度设计、各组的统计检验，因<strong>全文未获取</strong>，为<strong>待补全文</strong>。</li>
</ul>
""",
    related=[("Chromatin-Closure-Stem-Cell-Exhaustion-RIKEN-2026.html",
              "RIKEN 揭示：衰老过程中染色质闭合驱动干细胞耗竭新机制"),
             ("Stem-Cell-Rejuvenation-Age-Related-Degeneration-2026.html",
              "干细胞疗法抗衰老最新进展：预适应与衰老清除的协同路径"),
             ("Senolytic-Regenerative-Synergy-Healthspan-2026.html",
              "衰老细胞清除与干细胞联合疗法显著延长健康寿命——突破性协同效应验证")],
)

A["Postnatal-Handling-Neuroendocrine-Aging-Rats-1991.html"] = dict(
    topic="神经退行", ev="B", tag="经典回顾", ft=False,
    title="出生后前几周的抚摸，改变了大鼠二十年后的衰老轨迹：1991 年那篇 HPA 轴发育编程研究",
    crumb="H11 细胞间通讯改变 · 奠基文献",
    desc="Meaney 等 1991 年发表于 Neurobiology of Aging：雌性大鼠出生后早期处理可永久提高海马糖皮质激素受体结合，并减轻老年期 HPA 轴活动过高，证明发育期环境信号经神经内分泌通路「编程」了衰老轨迹。",
    source=src("Neurobiology of Aging", "1991", "12(1): 31–38",
               "Meaney MJ 等 4 位作者", "麦吉尔大学 / Douglas 医院研究中心",
               "Postnatal handling attenuates certain neuroendocrine, anatomical, and cognitive dysfunctions "
               "associated with aging in female rats",
               "10.1016/0197-4580(91)90036-j"),
    body="""<p>「细胞间通讯改变」这个衰老标志，今天的主要内容是 SASP、炎症因子、以及异时共生研究揭示的体液因子。但它的<strong>发育端</strong>——即早期生活经历如何通过神经内分泌系统设定一生的衰老轨迹——来自一条更老的线索。Meaney 团队 1991 年这篇论文是这条线索上的关键节点。</p>

<h2>实验：出生后早期处理</h2>

<p>所谓「出生后处理（postnatal handling）」，是把新生大鼠每天短时间从母鼠身边取出、人工把玩后放回，全程只持续出生后最初几周。这个轻微的早期环境扰动，此前的雄性大鼠研究已显示会改变成年后的应激反应性。本文要问的是：<strong>这个效应是否会一路延续到老年期</strong>。</p>

<h2>结果：一个跨越一生的效应</h2>

<ul>
<li><strong>海马 II 型糖皮质激素受体结合在处理组永久性升高</strong>——这是关键的分子锚点。糖皮质激素受体是 HPA 轴负反馈的「刹车」，海马中它的密度越高，应激反应的终止越有效；</li>
<li><strong>未处理雌鼠老年期基础皮质酮升高、应激反应过强</strong>，而处理组这一随龄恶化被显著减轻；</li>
<li><strong>海马退化与 HPA 活动升高相伴</strong>——二者构成一个相互强化的回路。</li>
</ul>

<blockquote><p>本文的核心命题是：<strong>发育期的环境信号，通过永久改变神经内分泌的设定点，编程了此后的衰老轨迹。</strong>这不是「早期创伤导致疾病」这种笼统说法，而是给出了一个可测量的中间变量——海马糖皮质激素受体密度。</p></blockquote>

<h2>它在这条研究链上的位置</h2>

<p>把本文放在坐标系里看，它是<strong>发育端</strong>的起点：</p>

<ul>
<li>发育端（本文）：早期社会经历 → HPA 轴设定点 → 一生的应激反应性；</li>
<li>成年端：社会隔离、慢性压力 → 持续的神经内分泌与免疫激活；</li>
<li>机制端：异时共生与 SASP 研究揭示的体液因子——晚年循环中的促炎因子本身就是一套「细胞间通讯」的紊乱。</li>
</ul>

<p>三端合起来，才构成「细胞间通讯改变」这个标志的完整叙事：<strong>通讯系统既在发育期被设定，又在成年期被社会与环境持续调制，最终在衰老中失调。</strong></p>

<h2>局限</h2>

<ul>
<li><strong>雌鼠数据</strong>。此前该实验室的工作多为雄鼠，本文专做雌鼠——这既是补充，也意味着<strong>本条目结论的性别特异性需谨慎对待</strong>，不能默认两性一致。</li>
<li><strong>大鼠模型</strong>。从啮齿动物的 HPA 轴发育编程到人类早期依恋与社会经济地位对健康的影响，中间隔着大量需要独立验证的推论。</li>
<li><strong>受体表达上调的机制本文未展开</strong>——它证明了「早期处理 → 受体结合升高」这个现象，但「为什么」要等到后来的表观遗传研究（<em>Nr3c1</em> 启动子甲基化）才给出分子解释。</li>
<li>各组动物数、皮质酮测定的时间点与统计量，因<strong>全文未获取</strong>，为<strong>待补全文</strong>。</li>
</ul>
""",
    related=[("SASP-Paracrine-Spreading-Senescence-Human-Brain-Cell-Types-2026.html",
              "衰老如何在大脑细胞间传播：SASP 旁分泌机制研究"),
             ("Senomorphic-Agents-Multi-Target-SASP-Healthy-Aging-2026.html",
              "衰老形态调节剂：靶向 SASP 多通路策略实现健康衰老"),
             ("Novelty-Seeking-Exploration-Social-Network-Aging-2026.html",
              "老年人的新奇寻求与目标导向探索分别对应可分离的社会网络结局与脑系统")],
)

A["Clonal-T-Cell-Expansion-Elderly-JEM-1994.html"] = dict(
    topic="免疫与炎症", ev="A", tag="经典回顾", ft=False,
    title="健康老年人血液里，某些 T 细胞克隆能占到全部 CD8 的三分之一以上：1994 年免疫衰老的细胞学起点",
    crumb="H12 慢性炎症 · 奠基文献",
    desc="Posnett 等 1994 年发表于 JEM：比较 65 岁以上供体与脐带血的 TCR Vβ 库，发现老年人出现大规模 CD8 T 细胞克隆性扩增（最高可占全部 CD8 的 37.5%），确立了人类免疫衰老中 T 细胞克隆扩张这一现象。",
    source=src("The Journal of Experimental Medicine", "1994", "179(2): 609–618",
               "Posnett DN 等 4 位作者", "康奈尔大学医学院",
               "Clonal populations of T cells in normal elderly humans: the T cell equivalent to "
               "&quot;benign monoclonal gammapathy&quot;",
               "10.1084/jem.179.2.609"),
    body="""<p>免疫衰老（immunosenescence）在 1990 年代初已是一个常用词，但它主要描述的是<strong>功能性下降</strong>——疫苗应答变差、感染易感性上升、胸腺退化。Posnett 等人这篇 <em>JEM</em> 论文从一个不同的角度切入，问的是：<strong>老年人的 T 细胞库在结构上变成了什么样子？</strong></p>

<h2>标题里的那个类比</h2>

<p>论文的副标题是「T 细胞版的良性单克隆丙种球蛋白病」。这个类比很精准：<strong>良性单克隆丙种球蛋白病（MGUS）</strong>指的是无症状老年人血液中出现单克隆浆细胞增殖产物——一种<strong>与年龄相关、通常无害、但反映免疫系统稳态改变的克隆性现象</strong>。作者要说的是：T 细胞区室里存在同类现象。</p>

<h2>发现：CD8 区室的大规模克隆扩张</h2>

<p>研究比较<strong>65 岁以上供体</strong>与<strong>脐带血</strong>的 TCR Vβ 库（T 细胞受体 β 链可变区的使用谱）：</p>

<ul>
<li>老年人出现<strong>超出均值 +3 SD 的 Vβ 扩增亚群</strong>——即某些 Vβ 家族的使用频率异常高，提示其背后是寡克隆扩张；</li>
<li>这些扩增<strong>主要发生在 CD8 而非 CD4</strong> 区室；</li>
<li>单个克隆的规模可<strong>占全部 CD8 T 细胞的 37.5%</strong>——这是一个在正常免疫学中相当惊人的数字；</li>
<li>部分克隆呈<strong>异常表型与功能</strong>。</li>
</ul>

<blockquote><p>用脐带血作对照是关键。脐带血代表「未经抗原暴露的初始库」——分布均匀、无克隆偏斜。与它对比，老年库的偏斜程度才有了可量化的参照。</p></blockquote>

<h2>它为什么是慢性炎症的细胞学基础</h2>

<p>本文的直接贡献是确立了「<strong>T 细胞克隆扩张是免疫衰老的结构性特征</strong>」这一现象。它与慢性炎症（inflammaging）的连接是后来建立的，逻辑大致是：少数克隆占据大量空间 → 初始 T 细胞库被挤压、TCR 多样性下降 → 对新抗原（新病原体、新疫苗）的应答能力下降 → 同时这些终末分化、常呈衰老样表型的克隆本身分泌促炎因子 → 形成低度慢性炎症。</p>

<p>这条链今天延伸到<strong>CMV 潜伏感染与免疫衰老</strong>的研究——本文发表时，这些克隆扩张的驱动因素尚未明确，而巨细胞病毒此后被确定为最主要的驱动者之一。</p>

<h2>局限</h2>

<ul>
<li><strong>横断面设计</strong>。老年与脐带血是两组不同个体，<strong>克隆扩张的时间进程是推断的，未被纵向观测</strong>。</li>
<li><strong>驱动因素当时未明</strong>。本文描述了现象，但「为什么扩张」——CMV、其他潜伏疱疹病毒、还是胸腺输出减少导致的稳态增殖——本文未回答。</li>
<li>「异常表型与功能」的描述受限于<strong>1994 年可用标志物</strong>的分辨率，与今天的高维流式/单细胞标准不可直接比较。</li>
<li>老年与脐带血供体的具体样本数、Vβ 家族的检测方法与统计阈值，因<strong>全文未获取</strong>，为<strong>待补全文</strong>。</li>
</ul>
""",
    related=[("Trained-Immunity-Vaccines-Inflammaging-2026.html",
              "训练免疫：疫苗或可成为降低衰老慢性炎症的新策略"),
             ("Lung-Fibroblasts-Drive-Inflammaging.html",
              "衰老肺成纤维细胞驱动肺部炎症衰老"),
             ("Mitochondria-Master-Regulator-Aging-Inflammaging-2026.html",
              "线粒体：衰老的主调控器，连接能量代谢与慢性炎症")],
)

A["Inulin-Lactose-Elderly-Constipation-AJCN-1997.html"] = dict(
    topic="代谢与营养", ev="A", tag="经典回顾", ft=False,
    title="1997 年就有人在老年便秘者身上试过益生元：菊粉、双歧杆菌与「菌群干预可改善老年功能」的早期人群证据",
    crumb="H13 菌群失调 · 奠基文献",
    desc="Kleessen 等 1997 年发表于 AJCN：15 例乳糖、10 例菊粉的老年便秘人群干预显示，菊粉显著增加粪便双歧杆菌、改善通便并提高短链脂肪酸。这是较早把益生元、肠道菌群与老年健康连接起来的前瞻性人群干预研究。",
    source=src("The American Journal of Clinical Nutrition", "1997", "65(5): 1397–1402",
               "Kleessen B 等 4 位作者", "德国柏林自由大学 / 联邦健康消费者保护与兽医学研究所",
               "Effects of inulin and lactose on fecal microflora, microbial activity, and bowel habit "
               "in elderly constipated persons",
               "10.1093/ajcn/65.5.1397"),
    body="""<p>肠道菌群与衰老的关系，在 2026 年已经是一个有大量机制研究支撑的领域。但回到 1997 年，把「益生元」「肠道菌群」和「老年人的具体健康结局」放在同一个干预试验里的研究还相当少。Kleessen 等人这篇 <em>AJCN</em> 论文是其中较早的一项，而且它选的终点非常具体：<strong>老年便秘者的通便情况</strong>。</p>

<h2>设计：菊粉 vs 乳糖，19 天</h2>

<p>研究纳入<strong>老年便秘者</strong>，分为两组：<strong>乳糖组 15 例、菊粉组 10 例</strong>。干预方式为剂量<strong>从 20 g/d 递增至 40 g/d，共 19 天</strong>。这里乳糖实际上扮演了对照的角色——它是另一种可发酵底物，用于区分「任何可发酵碳水的作用」与「菊粉的特异性作用」。</p>

<h2>结果：菊粉有效，乳糖个体差异大</h2>

<ul>
<li><strong>菊粉组</strong>：粪便<strong>双歧杆菌数增加</strong>，<strong>乳酸盐与短链脂肪酸升高</strong>，粪便 <strong>pH 下降</strong>，<strong>通便情况改善</strong>；</li>
<li><strong>乳糖组</strong>：<strong>个体差异大</strong>，未呈现一致的组水平效应。</li>
</ul>

<blockquote><p>把这条结果链连起来看，机制是清楚的：<strong>菊粉（一种可发酵的果聚糖）→ 被双歧杆菌等选择性利用 → 发酵产短链脂肪酸与乳酸 → 肠腔 pH 下降、渗透压改变、蠕动增强 → 通便改善。</strong>这套「底物—菌群—代谢产物—生理结局」的链条，此后成为益生元研究的模板。</p></blockquote>

<h2>它在整条研究链上的位置</h2>

<p>本文的价值主要在于<strong>它是「益生元—双歧杆菌—老年功能改善」这条链上较早的前瞻性人群证据</strong>。它证明了菌群干预不只是改变菌群构成，还能连接到一个可被老年人自己感知的临床终点。这个证明在今天依然重要——当前大量菌群研究停留在「改变菌群组成」层面，缺少功能结局。</p>

<p>同时它也提出了一个此后被反复验证的教训：<strong>不同可发酵底物的效应差异很大</strong>。乳糖组的高个体差异提示「任何益生元都有效」的想法不成立，底物结构、个体的初始菌群构成、以及基线饮食习惯都会调节效应。</p>

<h2>局限（读这篇时请特别留意）</h2>

<ul>
<li><strong>样本极小</strong>：乳糖组 n=15、菊粉组 n=10。以今天的临床试验标准看，这属于<strong>探索性规模</strong>，效应估计极不稳定。</li>
<li><strong>无安慰剂对照</strong>。两组都接受了可发酵底物，<strong>缺少真正的惰性对照</strong>——因此「通便改善」在多大程度上来自干预本身，而非来自参与试验带来的饮食与关注度变化，无法排除。</li>
<li><strong>菌群用培养法测定</strong>。1997 年尚无高通量 16S rRNA 测序，培养法<strong>严重低估菌群多样性</strong>，且只能检测可培养的菌属。本文「双歧杆菌增加」的结论方向可信，但<strong>菌群构成的整体图景与今天的数据不可直接比较</strong>。</li>
<li><strong>干预仅 19 天</strong>，无随访。长期有效性与安全性本文未涉及。</li>
<li>各组的具体测量值、变异范围与统计检验，因<strong>全文未获取</strong>，为<strong>待补全文</strong>。</li>
</ul>
""",
    related=[("INDY-Gut-Microbiome-Longevity-Drosophila-2026.html",
              "长寿基因 INDY 延寿新机制：调控肠道菌群与肠道稳态"),
             ("Naked-Mole-Rat-Microbiome-Healthy-Aging-2026.html",
              "裸鼢鼠肠道微生物组终身稳定：健康长寿的新证据"),
             ("Gut-Microbiota-Glutamic-Acid-Oocyte-Rejuvenation-2026.html",
              "肠道菌群调控谷氨酸恢复老龄卵母细胞质量：Nature Aging 新研究")],
)

A["Social-Capital-Income-Inequality-Mortality-AJPH-1997.html"] = dict(
    topic="神经退行", ev="A", tag="经典回顾", ft=False,
    title="信任与社团密度能预测一个州的死亡率：1997 年那篇把「社会资本」变成可量化健康决定因素的研究",
    crumb="H14 心理-社会隔离 · 奠基文献",
    desc="Kawachi 等 1997 年发表于 AJPH：美国 39 州的生态学分析显示，社会资本（志愿组织密度、社会信任）与年龄标化死亡率显著负相关，且收入不平等部分经由削弱社会凝聚而起作用。这是孤独感与社会关系影响健康这一研究传统的上游文献。",
    source=src("American Journal of Public Health", "1997", "87(9): 1491–1498",
               "Kawachi I、Kennedy BP、Lochner K、Prothrow-Stith D", "哈佛大学公共卫生学院",
               "Social capital, income inequality, and mortality",
               "10.2105/ajph.87.9.1491"),
    body="""<p>「社会关系影响健康」这句话长期处于流行病学的边缘——它听起来更像常识或道德劝诫，而不是一个可操作的科学命题。Kawachi 等人 1997 年这篇 <em>AJPH</em> 论文的关键贡献，是<strong>把它变成了一个有数据、有通路、有可测量指标的研究对象</strong>。</p>

<h2>把「社会资本」操作化为两个指标</h2>

<p>研究用两个可量化的代理变量来测量社会资本：</p>

<ul>
<li><strong>志愿组织成员密度</strong>（人均参与的志愿社团数量）；</li>
<li><strong>社会信任比例</strong>（调查中同意「多数人可以信任」的人口比例）。</li>
</ul>

<p>这两个指标覆盖了社会资本的两个面向：<strong>结构性的</strong>（你参加了多少组织）与<strong>认知性的</strong>（你是否信任他人）。</p>

<h2>结果：三个层次的关联</h2>

<ul>
<li><strong>社会资本的两个指标</strong>与<strong>总死亡率</strong>及<strong>多数死因别死亡率</strong>均呈<strong>负相关</strong>；</li>
<li><strong>收入不平等</strong>与死亡率相关，且<strong>与低社会资本相关</strong>；</li>
<li>由此提示：<strong>社会资本是「收入不平等 → 死亡率」这条通路上的中介</strong>——即收入差距通过削弱社会凝聚力，进而损害群体健康。</li>
</ul>

<blockquote><p>第三点才是本文真正的野心所在。它试图回答的不是「社会资本好不好」，而是「<strong>宏观经济结构如何渗透进人群的健康</strong>」。这个提问方式此后成为了社会流行病学的标准范式。</p></blockquote>

<h2>它为什么是 H14 的上游</h2>

<p>「心理-社会隔离」作为衰老标志，其主要证据来自个体层面的孤独感与死亡率研究。本文是这条研究传统的<strong>群体层面源头</strong>：它证明了社会关系的质量可以在<strong>群体尺度</strong>上预测死亡率，从而使「社会关系是可测量的健康决定因素」这一命题获得了流行病学意义上的合法性。</p>

<p>今天这条线已经延伸到多个层次：个体层面的孤独感与全因死亡风险、神经层面的社会隔离与认知衰退、以及生物学层面的<strong>DNA 甲基化时钟如何编码社会经济地位</strong>——本站报道过的研究显示，社会健康不平等确实可以被写入表观遗传组。本文是这条链条的起点。</p>

<h2>局限（生态学设计的固有问题）</h2>

<ul>
<li><strong>生态学设计</strong>：分析单位是<strong>美国 39 个州</strong>，暴露（社会资本）与结局（死亡率）都在群体层面测量。<strong>这带来了生态学谬误的实质风险</strong>——州层面「社会资本高 → 死亡率低」，<strong>不能</strong>推断为个体层面「参加社团多的人死亡率低」。这是本文最常被误引之处。</li>
<li><strong>社会资本仅用两题测量</strong>。社会资本是一个多维构念（包含连结型、桥接型、连结型等多个维度），两个代理变量只能捕捉其中一小部分。</li>
<li><strong>横断面生态学关联</strong>，无时间维度，<strong>因果方向无法确立</strong>——也可能是「健康人群更倾向于参与社团」的反向因果，或两者共同受第三方因素驱动。</li>
<li>各州混杂因素（种族构成、城市化率、医疗资源）的调整方式与调整后效应量，因<strong>全文未获取</strong>，为<strong>待补全文</strong>。</li>
</ul>
""",
    related=[("DNA-Methylation-Clock-Socioeconomic-Mortality-2026.html",
              "DNA 甲基化时钟揭示社会健康不平等的生物学机制"),
             ("Novelty-Seeking-Exploration-Social-Network-Aging-2026.html",
              "老年人的新奇寻求与目标导向探索分别对应可分离的社会网络结局与脑系统"),
             ("Trained-Immunity-Vaccines-Inflammaging-2026.html",
              "训练免疫：疫苗或可成为降低衰老慢性炎症的新策略")],
)


# ---------------- 主流程 ----------------
def main():
    arts = json.load(open(os.path.join(ROOT, "data/articles.json"), encoding="utf-8"))
    existing = {a["slug"] for a in arts}
    byslug = {a["slug"]: a for a in arts}
    newsdir = set(os.listdir(os.path.join(ROOT, "news")))

    # 硬校验：所有内链 slug 必须真实存在于 news/，或在本批次内
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
