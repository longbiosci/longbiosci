#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_articles_backlog_2026-10-18.py —— 内容摄入第 16 批（31 条积压分拣后的成篇部分）

背景与分拣规则
──────────────
`data/ledger-backlog-2026-10-17.md` 记 31 条「站内确实查无」的漏收条目。
本批先做**可核验性分拣**，规则只有一条：

    摘要里没有可引用定量的，不成篇。

理由：本站每条定量都必须能追到官方摘要原文（见 /about/ 的编辑方针）。
凭标题与一句话结论拼出的稿子，读者无法验收，等于用「看起来像新闻」的东西
稀释事实源。宁可 backlog 挂着写「明确不做」，也不产出无法验收的文章。

分拣结果（DOI→PubMed 逐个解析，30/31 命中，仅预印本 10.64898/... 未收录）：

  A. 摘要含 4 个以上可引用定量、且主题成体系 → 成篇（本批 2 条）
  B. 摘要含 1~3 个定量、主题分散 → 不成篇，进 backlog 的「留档观察」区
  C. 摘要为 0 定量（多为机制一句话 / Review / News & Views） → 明确不做

本批两条的选取不只看数字密度，还看**站内是否需要一条反向锚点**：

  1. GHR 拮抗剂延寿（Aging Cell 25(9):e70697，PMID 42701998）
     与站内既有《反直觉：只在肝脏敲除 GHR 的小鼠衰老更快》（acel.70741）构成
     同一通路的**相反方向**证据。两篇主题都关乎「GH 信号该不该降、降到哪」，
     站内此前只有「敲除加速衰老」一侧，缺「拮抗延寿」一侧，属结构性缺口。

  2. HIIT 在老年雌鼠中的多终点保护（GeroScience，PMID 42720846）
     站内运动干预条目多为人群观察，缺一条**控制严格、终点齐全的动物实验**
     作为机制侧参照；且该文补上了作者既往只做雄鼠的性别缺口。

数字来源：PubMed E-utilities 官方摘要（esummary + efetch），撰写时逐字复核。
         摘要中未出现的数字，本文一律不写；未给出的（如 GHA 队列样本量、
         HIIT 组的绝对摄氧量）标注「待补全文」。
"""
import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATE = "2026-10-18"

sys.argv = ["gen_articles.py", ROOT, "/dev/null", DATE]
_spec = importlib.util.spec_from_file_location(
    "ga", os.path.join(ROOT, "scripts", "gen_articles.py"))
ga = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ga)

A = {}

# ─────────────────────────────────────────────────────────────
# 1. GHR 拮抗剂延寿
# ─────────────────────────────────────────────────────────────
A["GHR-Antagonist-Pegvisomant-Lineage-Extends-Lifespan-AgingCell-2026.html"] = dict(
    title="同一个靶点，两种做法：GHR 拮抗让小鼠活得更久，而在肝脏里敲掉它却加速衰老",
    desc=("俄亥俄团队在 GHA 转基因小鼠中报告中位与最长寿命均显著延长，雄鼠最长寿命延长 186 天、雌鼠 265 天，"
          "2 岁龄队列握力更强、衰弱更轻但脂肪更多。这与站内此前报道的「肝细胞特异性 GHR 敲除加速衰老」方向相反，"
          "两篇合起来说明 GH 信号的「组织特异性」比「高或低」更关键。"),
    tag="研究进展",
    topic="代谢与营养",
    ev="B",
    crumb="GHR 拮抗与寿命",
    source=('<a href="https://onlinelibrary.wiley.com/journal/14749728" target="_blank" rel="noopener noreferrer">Aging Cell</a>'
            '（2026，25(9): e70697）· Ohio University / Edison Biotechnology Institute，List EO、Berryman DE 等'
            ' · 论文：<em>Growth Hormone Receptor Antagonism Extends Lifespan</em>'
            ' · DOI <a href="https://doi.org/10.1111/acel.70697">10.1111/acel.70697</a>'
            ' · PubMed <a href="https://pubmed.ncbi.nlm.nih.gov/42701998/">42701998</a>'),
    body="""<p>生长激素（GH）通路是长寿研究里被验证得最彻底的方向之一：<strong>削弱 GH 作用的模型，在多个物种里都活得比对照久</strong>。但「削弱」这两个字太粗——<strong>在哪儿削弱、削弱多少、用药物还是用基因</strong>，结果可以完全相反。</p>

<p>这篇 <em>Aging Cell</em> 论文补上了长期缺失的一块：<strong>药物层面的 GH 受体拮抗（GHA），到底能不能延长寿命</strong>。而它给出的答案，正好和本站此前报道的另一篇论文形成对照。</p>

<h2>先理解这个模型的来历</h2>

<p>作者团队的特殊之处在于时间跨度。论文明确写到：</p>

<ul>
<li>1990 年代初，这个实验室发现把牛 GH 第 119 位（人 GH 第 120 位）保守甘氨酸的密码子突变成包括赖氨酸在内的多种氨基酸，<strong>能把 GH 从激动剂变成拮抗剂</strong>；</li>
<li>这条发现最终长成了 <strong>Somavert（Pegvisomant，培维索孟）</strong>——目前<strong>唯一获 FDA 批准的 GHR 拮抗剂</strong>，用于肢端肥大症；</li>
<li>而用于发现并开发 Pegvisomant 的那株 <strong>GHA 转基因小鼠</strong>，自 <strong>1991 年</strong>起一直养在这个实验室里。</li>
</ul>

<p>所以这不是「新做一个模型」，而是<strong>把一株 30 多年的老模型重新拿出来做存活分析</strong>——这解释了为什么一项 2026 年的寿命研究，能建立在 1990 年代的分子生物学上。</p>

<h2>为什么此前一直没做成</h2>

<p>作者点出的障碍很具体：<strong>Pegvisomant 对啮齿类 GHR 的亲和力很差</strong>，所以它从来没能在小鼠身上做过寿命测试。这是一个典型的「人体有效、动物模型用不了」的错位——药物已经上市，却无法在标准的长寿模型里验证。GHA 转基因小鼠因此成了<strong>唯一可行的替身</strong>。</p>

<p>而此前并非没人试过。论文直白地写：<strong>早先一项存在若干局限的研究，未能在 GHA 小鼠中检出寿命延长</strong>。本次研究是针对那些局限做的改进版本。这意味着结论不是「首次发现」，而是<strong>「在纠正方法学缺陷后，先前被读成阴性的结果翻了过来」</strong>。</p>

<h2>结果：中位与最长寿命同时延长</h2>

<p>论文报告，GHA 小鼠的<strong>中位寿命与最长寿命均显著延长</strong>，四个 p 值分别对应雄鼠与雌鼠的中位、最长寿命：</p>

<table>
<thead><tr><th>性别</th><th>中位寿命</th><th>最长寿命</th><th>最长寿命延长</th></tr></thead>
<tbody>
<tr><td>雄鼠</td><td>p = 0.044</td><td>p = 0.0037</td><td><strong>186 天</strong></td></tr>
<tr><td>雌鼠</td><td>p = 2 × 10⁻⁸</td><td>p = 9 × 10⁻⁶</td><td><strong>265 天</strong></td></tr>
</tbody>
</table>

<p>两性都显著，这在 GH 轴研究里值得单独说一句——GH 的分泌模式本身有强烈性别差异（雄性呈脉冲式、雌性更持续），所以一个干预在<strong>两性都成立</strong>，比只在一种性别里成立要硬得多。</p>

<blockquote><p><strong>雌鼠的效应显著更强</strong>：p 值差了三到四个数量级，最长寿命多延长 <strong>79 天</strong>。这是一个值得后续专门研究的信号，但摘要<strong>未给出两组的中位寿命绝对值</strong>，所以无法换算成百分比——<strong>具体延寿幅度待补全文</strong>。</p></blockquote>

<h2>健康寿命：更结实，但更胖</h2>

<p>第二项结果来自<strong>一个独立的 2 岁龄队列</strong>。在相当于小鼠晚年的这个时间点上，GHA 雄鼠与雌鼠都表现出：</p>

<ul>
<li><strong>衰弱程度更轻</strong>；</li>
<li><strong>握力更强</strong>；</li>
<li>但<strong>脂肪量增加</strong>。</li>
</ul>

<p>「更结实但同时更胖」这个组合，恰好是 GH 通路研究里的老问题。GH 信号降低会改变体成分——这在 GH 缺乏症患者身上也是已知现象。所以这里的关键不是「有没有副作用」，而是<strong>「在体成分变差的同时，功能与寿命更好」</strong>：它说明<strong>体成分不是衡量衰老干预的充分终点</strong>。</p>

<h2>和站内另一篇放在一起看，才是完整结论</h2>

<p>本站此前报道过另一篇 <em>Aging Cell</em> 论文（<a href="/news/Hepatocyte-GHR-Ablation-Accelerated-Aging-PDK4-AgingCell-2026.html">acel.70741</a>）：<strong>只在肝细胞里敲除 GHR，小鼠反而衰老更快、寿命更短</strong>，机制是循环 GH 升高经脂肪–肝串扰造成线粒体损伤。</p>

<p>两篇并排，得到的是一个比「GH 越低越好」精确得多的判断：</p>

<table>
<thead><tr><th>干预</th><th>作用范围</th><th>寿命结果</th></tr></thead>
<tbody>
<tr><td>GHR 拮抗（本篇，转基因模型）</td><td>全身性削弱 GHR 信号</td><td><strong>中位与最长寿命均延长</strong></td></tr>
<tr><td>肝细胞特异性 GHR 敲除（acel.70741）</td><td>仅肝脏移除 GHR</td><td><strong>寿命缩短</strong></td></tr>
</tbody>
</table>

<p>同一受体，一个削全身、一个只削肝，方向相反。这不能用「剂量差异」解释，只能落到<strong>组织特异性与代偿</strong>上：肝脏失去 GHR 后循环 GH 反而升高，压力被转移给脂肪组织再反弹回肝脏。而全身性拮抗没有留下这样一个「局部缺口」。</p>

<blockquote><p>对读者的实际含义：<strong>「降 GH/IGF-1」不是一个可以整块讨论的干预</strong>。决定结果是「在哪个组织降、其他组织是否代偿」，而不是「降了多少」。任何以组织特异性方式干预该通路的方案（包括某些基因治疗思路），都必须单独验证。</p></blockquote>

<h2>局限与未解答的问题</h2>

<ul>
<li><strong>是转基因模型，不是药物。</strong>GHA 小鼠从发育期起就全身性表达拮抗，与成年后给药（Pegvisomant 的实际用法）不是一回事。论文的结论是「GH 拮抗这一机制可延寿」，<strong>不能直接读成「Pegvisomant 可用于抗衰」</strong>。</li>
<li><strong>样本量未报告。</strong>存活分析的可信度高度依赖每组动物数，摘要未给，<strong>待补全文</strong>。</li>
<li><strong>中位寿命绝对值未给</strong>，因此无法计算延寿百分比或与热量限制、雷帕霉素等经典干预横向比较。</li>
<li>「改进的局限」具体改了什么（饲养条件？对照？寿命统计方法？），摘要<strong>未展开</strong>。这恰恰是本次结论能推翻前作的关键，需要读全文才能判断改进是否足够。</li>
<li><strong>雌鼠效应远强于雄鼠</strong>，机制未解释。</li>
</ul>""",
    related=[
        ("Hepatocyte-GHR-Ablation-Accelerated-Aging-PDK4-AgingCell-2026.html",
         "反直觉：只在肝脏敲除生长激素受体，小鼠反而衰老得更快"),
        ("daf-2-Insulin-Receptor-Longevity-Science-1997.html",
         "一条基因把寿命翻一倍：1997 年 daf-2 论文如何开启「营养感应调控衰老」的整个领域"),
    ],
)


# ─────────────────────────────────────────────────────────────
# 2. HIIT 老年雌鼠
# ─────────────────────────────────────────────────────────────
A["HIIT-Aged-Female-Mice-Multi-Endpoint-GeroScience-2026.html"] = dict(
    title="14 周 HIIT 让 24 月龄雌鼠的有氧能力涨 71%，而对照组掉了 67% 的四股力量",
    desc=("C57BL/6J 小鼠（每组 9 只、期末 24 月龄）经 14 周渐进 HIIT 后，有氧能力 +71%、执行功能 +73%、"
          "总运动功能 +39%，收缩压降 17 mmHg；心肌纤维化与海马 IL-1β 下降，衰弱推迟。"
          "四项功能指标在训练组几乎不动、在对照组大幅下滑，提示 HIIT 的作用更像「守住不塌」而不是「变得更强」。"),
    tag="研究进展",
    topic="器官衰老",
    ev="B",
    crumb="HIIT 与老年雌鼠功能",
    source=('<a href="https://link.springer.com/journal/11357" target="_blank" rel="noopener noreferrer">GeroScience</a>'
            '（2026 年 9 月 10 日在线）· Theobald D、Williamson P、Johnston A、Tripp L 等'
            ' · 论文：<em>High-intensity interval training in aged female mice preserves physical, cognitive, and cardiovascular function</em>'
            ' · DOI <a href="https://doi.org/10.1007/s11357-026-02489-0">10.1007/s11357-026-02489-0</a>'
            ' · PubMed <a href="https://pubmed.ncbi.nlm.nih.gov/42720846/">42720846</a>'),
    body="""<p>运动是少数在人群研究里反复成立的衰老干预。但人群研究有个绕不过去的困难：<strong>很难分清「运动让人变好」和「能运动的人本来就更好」</strong>。动物实验能把这个混淆关掉——代价是要接受物种距离。</p>

<p>这篇 <em>GeroScience</em> 论文值得注意的地方不在结论新鲜（运动有益，这点不新），而在<strong>终点铺得非常全</strong>：体能、认知、心血管、体成分、能量代谢、组织学标志一起测，并且<strong>把作者自己此前只做雄鼠的缺口补上了</strong>。</p>

<h2>设计：14 周，两组各 9 只，期末 24 月龄</h2>

<ul>
<li><strong>动物</strong>：C57BL/6J 小鼠，随机分为 HIIT 组与久坐对照（SED）组，<strong>各组 n = 9</strong>，<strong>实验结束时 24 月龄</strong>；</li>
<li><strong>干预</strong>：HIIT 组进行 <strong>14 周</strong>训练，<strong>训练量与强度渐进增加</strong>；</li>
<li><strong>测量</strong>：干预前后各测一轮，涵盖体能、认知、心血管功能、体成分、全身测热法；干预后另做免疫组化等组织学标志。</li>
</ul>

<p>作者此前已在雄鼠中证明 HIIT 能在一生跨度内保住体能，本研究把对象换成雌鼠，并新增了大量此前未测的评估项。摘要<strong>未说明运动从第几周龄开始</strong>，按「期末 24 月龄 + 14 周干预」推算应在 21 月龄左右启动——但这是推算，<strong>起始月龄以全文为准</strong>。</p>

<h2>结果：最值得看的不是涨幅，是「谁在掉」</h2>

<table>
<thead><tr><th>终点</th><th>HIIT 组</th><th>久坐对照组</th></tr></thead>
<tbody>
<tr><td>有氧能力</td><td><strong>+71%</strong></td><td>无变化</td></tr>
<tr><td>四股力量 / 耐力</td><td><strong>−28%</strong></td><td><strong>−67%</strong></td></tr>
<tr><td>前肢握力</td><td>无变化</td><td><strong>−16%</strong></td></tr>
<tr><td>总运动功能</td><td><strong>+39%</strong></td><td>无变化</td></tr>
<tr><td>执行功能</td><td><strong>+73%</strong></td><td>无变化</td></tr>
<tr><td>探索行为</td><td colspan="2">多项测试中改善</td></tr>
<tr><td>收缩压</td><td><strong>−17 mmHg（−12%）</strong></td><td>—</td></tr>
<tr><td>平均动脉压</td><td><strong>−16 mmHg</strong></td><td>—</td></tr>
</tbody>
</table>

<p>所有功能差异均达<strong>p &lt; 0.05</strong>。此外，HIIT 还<strong>减少心肌纤维化</strong>、<strong>降低海马 IL-1β 表达</strong>、<strong>推迟衰弱发生</strong>。</p>

<blockquote><p><strong>把这张表竖着读</strong>：四项指标（有氧能力、总运动功能、执行功能、前肢握力）在 HIIT 组是「无变化」，在对照组是「下滑」。只有有氧能力、总运动功能、执行功能三项出现了<strong>绝对提升</strong>。也就是说，HIIT 在多数终点上的作用是<strong>「守住不塌」</strong>——把年龄相关的下降<b>按住</b>，而不是把老年动物练回年轻水平。</p></blockquote>

<p>这个区别对人有直接含义。人群里常见「老年人练了之后体能提升 X%」的叙述，但在严格对照的动物实验里，<strong>缺省状态是衰退</strong>；所谓「改善」，很多时候只是<strong>衰退没有发生</strong>。这不是贬低运动，而是提醒别把「防止下滑」误读成「逆转变老」。</p>

<h2>两个值得单独说的数字</h2>

<p><strong>四股力量/耐力的 −28% vs −67%</strong>：这是全表差距最大的一项。训练组自己也在掉，但掉得不到对照组的一半。这是典型的「延缓」而非「阻止」形状。</p>

<p><strong>收缩压 −17 mmHg（−12%）</strong>：在人类临床里，收缩压降低 10 mmHg 量级已被视为有临床意义的幅度，因此这个数字引人注目。但要注意两点：<strong>这是小鼠的血压</strong>，且摘要<strong>未给出对照组的血压变化</strong>，无法排除组间基线差异。绝对血压值也<strong>未报告，待补全文</strong>。</p>

<h2>局限</h2>

<ul>
<li><strong>样本量小且每组仅 9 只</strong>。功能学与组织学终点尚可，但<strong>本研究未报告寿命终点</strong>——「保住功能」与「延长寿命」在这个领域并不总是同向。</li>
<li><strong>没有中间剂量或中等强度对照</strong>。因此无法回答一个实际很重要的问题：<strong>这些获益是 HIIT 特有的，还是有氧运动普遍具有的</strong>？对老年人而言，HIIT 的可执行性和受伤风险与中等强度训练差别很大，缺这一组，结论不能直接转化为运动处方。</li>
<li><strong>仅雌鼠</strong>。补上了作者自己的性别缺口，但也意味着不能与既往雄鼠数据直接合并成「两性一致」的结论。</li>
<li>摘要<strong>未报告</strong>训练依从性、是否有个体退出、以及有氧能力的绝对值（仅给百分比）。<strong>待补全文。</strong></li>
<li>海马 IL-1β、心肌纤维化的<strong>定量幅度未给</strong>，仅有方向性表述。</li>
</ul>

<h2>该怎么用这条信息</h2>

<p>它是<strong>机制侧的支持证据</strong>，不是运动处方。它说明在控制最严格的条件下，晚年开始的渐进 HIIT 能同时改善心肺、运动功能、执行功能与心脏/脑的炎症与纤维化标志——这让「运动作为衰老干预」的生物学基础更实了一层。但把它换算成「老年人应该做 HIIT」，跳过了剂量、安全性与人群异质性三件事。</p>""",
    related=[
        ("Exercise-Mitochondrial-Quality-Control-Brain-Aging-2026.html",
         "运动为什么能护脑：线粒体质量控制是被反复指认的那条通路"),
        ("Oxidative-Stress-Caloric-Restriction-Aging-Science-1996.html",
         "热量限制为什么延寿？1996 年 Science 给出的答案是「降低氧化损伤」——以及这个答案后来遇到的问题"),
    ],
)

ga.A = A
if __name__ == "__main__":
    ga.main()
