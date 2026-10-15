#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_missing_meta_2026-10.py —— 补写元层 TOP 榜核定漏收的1 篇

来源：`月度研究热点综述_2026-10.md`（元层，file_id dXzxgtkeYPXT，parent_id dQpzABLkRxLu）
原榜单 TOP1–TOP5 中，ER-100、D+Q MASH RCT、TranslAGE、Lsp2/Nature mTOR、
心磷脂-ERRγ、犬类时钟、AMPK 991 均已在站内；真漏收仅此1 篇。

证据等级 A（人体 RCT）。但样本量、具体数值未在卡片中给出，
按 SOP §4.2 只写卡片给出的事实，定量不臆测，付费墙处标「待补全文」。
"""
import os
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import gen_articles as ga  # noqa: E402

A = {}

A["Vegan-Diet-PhenoAge-Inflammatory-Pathways-RCT-2026.html"] = dict(
    topic="临床与转化", ev="A", tag="临床试验",
    title="纯素饮食 1 个月：PhenoAge 逆转 1.7 岁，且机制落在炎症通路表观遗传调控上",
    crumb="MedComm 2026 · 等热量纯素 vs 高肉饮食 RCT",
    desc="一项等热量对照 RCT 比较 1 个月纯素饮食与高肉饮食，报告表观遗传时钟指标 PhenoAge 逆转约 1.7 岁，机制指向炎症通路的表观遗传调控——这是本站记录的第一个把纯素干预与生物年龄读数直接挂钩的对照试验结果。",
    source=('MedComm（2026）· DOI '
            '<a href="https://doi.org/10.1002/mco2.70899" target="_blank" rel="noopener">10.1002/mco2.70899</a> · '
            '来源=元层「月度研究热点综述」2026-10 榜单 · 交叉判定=A（人体对照试验）· <strong>待补全文</strong>'),
    body="""<p>素食与健康的研究里，最不缺的是<strong>观察性数据</strong>——爱斯基摩人、芬兰人、教会健康人群 cohorts都指向同一个方向。真正稀缺的是<strong>对照试验</strong>：把饮食换掉，然后看生物年龄读数往哪个方向动。这项研究问的就是这个问题。</p>

<h2>设计要点：等热量是关键</h2>

<p>这项试验的干预是<strong>1 个月纯素饮食</strong>，对照是<strong>高肉饮食</strong>。两者<strong>等热量</strong>——这一点比「素食 vs 杂食」重要得多：它把<strong>食物构成</strong>从<strong>总热量</strong>里剥离出来了。如果不等热量，任何差异都可以用「吃得少了」来解释。</p>

<table>
<thead><tr><th>要素</th><th>设置</th></tr></thead>
<tbody>
<tr><td>时长</td><td>1 个月</td></tr>
<tr><td>对照</td><td><strong>等热量</strong>高肉饮食</td></tr>
<tr><td>主要终点</td><td><strong>PhenoAge</strong>（表观遗传时钟）</td></tr>
<tr><td>机制线索</td><td>炎症通路的<strong>表观遗传调控</strong></td></tr>
</tbody>
</table>

<h2>结果：PhenoAge 逆转约 1.7 岁</h2>

<p>结果是 <strong>PhenoAge 逆转约 1.7 岁</strong>。PhenoAge 是 DNA甲基化领域的经典指标（与实际年龄、健康状态、死亡风险相关），比早期的 Horvath 时钟更贴近临床结局。因此 1.7 岁的读数位移不是一个可以忽略的量级。</p>

<blockquote><p>更重要的是机制落点：不是「吃得素感觉好」，而是<strong>炎症通路本身被表观遗传地调控了</strong>。这与本站长期跟踪的「炎症衰老 / inflammaging」主线直接接上。</p></blockquote>

<h2>1.7 岁这个数字该怎么读</h2>

<p>三点必须一起看：</p>

<ul>
<li><strong>时长只有 1 个月</strong>。时钟读数的移动能在这么短时间内出现，说明它反映的是<strong>代谢状态的快速可塑性</strong>，而非累积损伤的逆转；</li>
<li><strong>PhenoAge 是标志物，不是结局</strong>。它与死亡风险相关，但<strong>降低 PhenoAge 不等于寿命延长</strong>——这与本站对NAD⁺ 前体的判定口径一致（标志物 ≠ 获益）；</li>
<li><strong>绝对值小、相对变化大</strong>。1.7 岁的逆转在时间轴上不到两个月，会不会在停用饮食后回弹，需要更长的随访。</li>
</ul>

<h2>与既有证据的关系</h2>

<p>本站已在跟踪的饮食干预证据里，这项研究的定位是<strong>首次把纯素干预与生物年龄读数直接挂钩</strong>：</p>

<ul>
<li><strong>限热量/ 类限制</strong>（CR、蛋白质限制、蛋氨酸-FGF21 轴）——动物证据强，人体读数证据较弱；</li>
<li><strong>植物性饮食的观察性证据</strong>——方向一致但无法排除混杂；</li>
<li><strong>这项 RCT</strong>——直接把「换成纯素」这个变量放进等热量框架里测量时钟。</li>
</ul>

<blockquote><p>它把一条靠观察性数据支撑的假设，往<strong>可干预、可测量</strong>的方向推了一步——但离「照着吃就能年轻 1.7 岁」还差得远。</p></blockquote>

<h2>需要注意的地方</h2>

<p>证据等级 <strong>A</strong>（人体对照试验），但有三条限制：</p>

<ul>
<li><strong>样本量与具体分布未获取</strong>（卡片未提供，<strong>待补全文</strong>）；1 个月 RCT 的样本量通常不大，效应量稳定性需看全文；</li>
<li><strong>1 个月不足以评价长期依从性与健康结局</strong>，纯素饮食的长期可行性是独立问题；</li>
<li>纯素饮食的<strong>营养充分性</strong>（B12、铁、锌、Omega-3）需要各自单独评估，本文不构成饮食推荐。</li>
</ul>

<p>本站会跟踪这项研究的后续随访与是否有更大规模复制。相关机制背景可参考
<a href="/news/Protein-Diet-Longevity-Lamming-Cell-Review-2026.html">蛋白质饮食与长寿的 Cell 综述</a>
与<a href="/news/Methionine-Supplemented-Longevity-Diet-FGF21-Long-2026.html">蛋氨酸-FGF21 轴研究</a>。</p>""",
    related=[
        ("Protein-Diet-Longevity-Lamming-Cell-Review-2026.html",
         "蛋白质摄入与长寿：Cell 综述里的争议与共识"),
        ("Methionine-Supplemented-Longevity-Diet-FGF21-Long-2026.html",
         "蛋氨酸-FGF21 轴：饮食长寿效应里最热的通路之一"),
    ],
)

ga.A.update(A)
ga.main()
