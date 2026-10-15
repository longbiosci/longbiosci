#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_missing_2026-09-25.py —— 补写 09-25 期台账核定的3 篇真漏收

这 3 条的判定过程（不是「脚本说漏收就写」，而是三道人工核验）：
  1. ledger.py audit 判为漏收（DOI、标题相似、slug 词元重叠四路均未命中）
  2. 用高特异关键词直接搜站内 HTML：SELENOP / ApoER2 / 软骨硒 → 0 命中
     Kpaa /苯乙酰化 / PAA / K481paa → 0 命中；菌群 + 暴露组 + 脑老化 → 0 命中
  3. 排除「命中的是完全不同的另一篇」——例如同期的 N10 BMAL1-YAP 命中的是
     BMAL1-Macrophage-Inflammation-Carcinogenesis-2026.html，与产出条目无关

纪律（SOP §4.2）：只依据公开摘要 + PubMed 元数据；付费墙未获取处标「待补全文」；
定量一律不臆测。三条均为临床前/机制层面，证据分级 B（骨关节炎人体样本为 B 偏上，
综述类为 C）。
"""
import os
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import gen_articles as ga  # noqa: E402

A = {}

A["Selenium-Axis-Liver-Cartilage-Osteoarthritis-Metabolic-2026.html"] = dict(
    topic="代谢与营养", ev="B", tag="研究进展",
    title="肝-软骨硒轴：肝功能不全如何把骨关节炎里的软骨细胞推进衰老",
    crumb="Cell Metabolism · 肝-软骨硒轴 · 骨关节炎",
    desc="研究揭示肝脏-软骨之间的硒转运轴：肝功能不全时 SELENOP-ApoER2 轴受损，软骨硒供应不足、软骨细胞衰老；而无机硒补充可绕过该转运障碍直接改善骨关节炎——提示「肝功能」可能是骨关节炎的一个可干预上游变量。",
    source=('Cell Metabolism（2026-09-22 在线）· DOI <a href="https://doi.org/10.1016/j.cmet.2026.08.023" '
            'target="_blank" rel="noopener">10.1016/j.cmet.2026.08.023</a> · '
            '交叉判定=B（临床前，含人体关节样本）· <strong>待补全文</strong>'),
    body="""<p>骨关节炎（OA）的主流叙事一直是「软骨磨损 + 炎症」。这项工作把视线往上游移了一层：<strong>决定软骨状态的，可能不是软骨自己，而是肝脏给它送了什么</strong>。</p>

<h2>一条此前没被放进 OA 叙事的轴：硒</h2>

<p>硒是人体必需的微量元素，也是谷胱甘肽过氧化物酶（GPx）这类抗氧化酶的核心组分。而<strong>SELENOP（硒蛋白 P）</strong>是血浆中运输硒的主要载体，由肝脏合成；<strong>ApoER2</strong>则是细胞表面接受硒的受体。</p>

<p>这条链的逻辑是：<strong>肝功能不全 → SELENOP 产生或转运异常 → 软骨细胞拿不到足量硒 → 抗氧化能力下降 → 软骨细胞进入衰老状态 → 骨关节炎进展</strong>。</p>

<blockquote><p>换句话说，OA 的部分损伤信号可能来自肝，而软骨只是「下游受害者」。这也是为什么单关节局部用药难以打断病程。</p></blockquote>

<h2>最有意思的一点：无机硒可以绕过这道障碍</h2>

<p>研究的关键干预结果不是「补硒有效」这么笼统，而是<strong>补硒的位置很讲究</strong>：无机硒补充能够<strong>绕过 SELENOP-ApoER2 这条受损的转运轴</strong>，直接改善软骨状态。</p>

<p>这意味着两条不同的治疗逻辑：</p>

<table>
<thead><tr><th>干预位置</th><th>逻辑</th><th>适用情形</th></tr></thead>
<tbody>
<tr><td>恢复 SELENOP-ApoER2 转运</td><td>从上游修复硒的投递系统</td><td>肝功能不全导致的转运障碍</td></tr>
<tr><td><strong>无机硒补充</strong></td><td><strong>绕过故障段，直接补足底物</strong></td><td>转运能力无法快速恢复时</td></tr>
</tbody>
</table>

<p>「绕过故障段」这个思路在营养学里并不新鲜，但在 OA 这个领域是新的——它把 OA 的干预靶点从关节内部移到了<strong>全身硒状态与肝功能</strong>。</p>

<h2>该怎么看待这个结论</h2>

<p>需要注意的边界：</p>

<ul>
<li>证据等级为 <strong>B</strong>——主要证据来自分子机制与动物模型，虽含人体关节样本，但距离「补硒能治 OA」的临床结论仍有距离；</li>
<li><strong>补硒过量本身有毒性</strong>（硒的窗口窄），任何「吃硒治骨关节炎」的说法都应先问剂量与人群；</li>
<li>真正有价值的下游问题是：<strong>能不能用常规肝功能指标把「硒转运障碍型OA」筛出来</strong>，从而做到分层干预。</li>
</ul>

<blockquote><p>这项研究真正的价值不在于「硒」，而在于它给出了一个可检验的假设：<strong>部分骨关节炎可能是全身代谢与器官间信号失衡的末端表现，而非纯粹的关节局部疾病。</strong></p></blockquote>

<p>本站已将此项归入 <strong>「器官间信号」主线</strong>跟踪——与肝-骨、肠-脑、肾-心这类跨器官轴系列一并观察，等待是否有临床队列数据跟进。</p>""",
    related=[
        ("Gut-Exosome-Aging-Microbiome-2026.html", "衰老外泌体与肠道菌群：跨器官信号的一具体实例"),
    ],
)

A["Microbiota-Phenylacetylation-Kpaa-Mitochondrial-SIRT3-2026.html"] = dict(
    topic="代谢与营养", ev="B", tag="研究进展",
    title="菌群造出的新型赖氨酸修饰 Kpaa：一条被忽视的线粒体衰老通路及其逆转开关",
    crumb="Cell Metabolism · 菌群赖氨酸苯乙酰化 · SIRT3",
    desc="研究发现肠道菌群经苯丙氨酸-PAA 通路生成新型赖氨酸苯乙酰化修饰（Kpaa），修饰 HSP60 后触发线粒体未折叠蛋白应答（UPR）并损害线粒体功能；而去乙酰化酶 SIRT3 可逆转——这是「菌群-宿主修饰组-线粒体衰老」链条上第一个被明确串起来的环节。",
    source=('Cell Metabolism 2026;38(9):1864–1880.e8 · DOI '
            '<a href="https://doi.org/10.1016/j.cmet.2026.05.016" target="_blank" rel="noopener">10.1016/j.cmet.2026.05.016</a> · '
            '交叉判定=B（细胞与动物模型）· <strong>待补全文</strong>'),
    body="""<p>过去十年关于「菌群影响衰老」的说法汗牛充栋，但绝大多数停在<strong>相关性</strong>层面——哪个菌多、哪个代谢物高、然后推测炎症。这项工作的分量在于：它把链条的<strong>每一步都指出了具体分子</strong>。</p>

<h2>新修饰类型：苯乙酰化（Kpaa）</h2>

<p>赖氨酸乙酰化大家已经很熟，这次发现的是另一种修饰——<strong>苯乙酰化（phenylacetylation，简称 Kpaa）</strong>。它的来源出乎意料地朴素：<strong>肠道菌群代谢膳食苯丙氨酸，产生苯丙氨酸代谢物 PAA，再进一步衍生出苯乙酰化</strong>。</p>

<p>换句话说，你吃的<strong>含苯丙氨酸的蛋白质</strong>（几乎所有荤食都富含）在肠道菌群手里被加工成了一种<strong>能直接修饰宿主蛋白的化学基团</strong>。</p>

<h2>被修饰的靶点：HSP60 与线粒体 UPR</h2>

<p>被 Kpaa 修饰的蛋白是 <strong>HSP60</strong>（热休克蛋白 60），定位在线粒体基质，是<strong>线粒体未折叠蛋白应答（UPR）</strong>的核心成员。线粒体 UPR 的含义与细胞质 UPR 类似：线粒体内出现折叠错误的蛋白时，会启动一套清理与修复机制。</p>

<p>而 Kpaa 修饰 HSP60 的后果是触发线粒体 UPR，并<strong>损害线粒体功能</strong>。这条因果链相当长，但每一环都有实验支撑：</p>

<blockquote><p><strong>菌群 → PAA → Kpaa → HSP60 修饰 → 线粒体 UPR → 线粒体功能损害</strong></p></blockquote>

<h2>可逆的那一环：SIRT3</h2>

<p>研究的实用价值落在<strong>去乙酰化酶 SIRT3</strong>身上——它能够<strong>逆转</strong>上述表型。SIRT3 属于 sirtuin 家族，定位于线粒体，是 NAD⁺ 的主要细胞内消费者之一。</p>

<p>这就把两项本站长期跟踪的主题连在了一起：<strong>菌群代谢物</strong>与 <strong>NAD⁺ / sirtuin 轴</strong>。而 NAD⁺ 前体补充的争议在这里获得了一个新角度——若衰老的部分机制确实是「修饰酶活性下降导致的表观去修饰失衡」，那么补充 NAD⁺ 是否有意义，取决于<strong>去修饰酶那一侧是否真的在衰减</strong>。</p>

<table>
<thead><tr><th>环节</th><th>方向</th><th>可否干预</th></tr></thead>
<tbody>
<tr><td>膳食苯丙氨酸摄入</td><td>上游</td><td>可调（饮食结构）</td></tr>
<tr><td>菌群 PAA 生成</td><td>中间</td><td>理论可调（益生菌/饮食）</td></tr>
<tr><td>Kpaa 修饰 HSP60</td><td>损伤点</td><td>尚无直接手段</td></tr>
<tr><td><strong>SIRT3 去修饰</strong></td><td><strong>保护点</strong></td><td>NAD⁺ 相关通路、基因治疗</td></tr>
</tbody>
</table>

<h2>需要克制的地方</h2>

<p>证据等级 <strong>B</strong>，主要来自细胞与动物模型。三处不应过度解读：</p>

<ul>
<li><strong>不要立刻推「少吃苯丙氨酸」</strong>——苯丙氨酸是<strong>必需氨基酸</strong>，人体不能自行合成，摄入不足的后果比可能的修饰负担更严重；</li>
<li>菌株差异巨大，同一饮食在不同人身上的菌群构成完全不同，<strong>个体差异未被解决</strong>；</li>
<li>SIRT3 在人类中的可成药性远高于其在模型中的表现，这一步距离临床还有多轮验证。</li>
</ul>

<blockquote><p>真正值得跟踪的是：这条链能不能从<strong>修饰组学</strong>的角度，给衰老研究提供一个与「炎症」「端粒」「表观遗传时钟」都正交的<strong>第四个可干预维度</strong>。</p></blockquote>""",
    related=[
        ("NAD-Precursor-Systematic-Review-Meta-Analysis-2026.html",
         "NAD⁺ 前体系统评价：15 项 RCT 确认代谢指标改善，但「延寿」仍无人体证据"),
        ("Centenarian-Gut-Microbiome-Secondary-Bile-Acids-NatureAging-2026.html",
         "百岁老人肠道菌群与次级胆汁酸：菌群代谢物能推动年龄读数"),
        ("Engineered-Gut-Bacteria-LBP-FMT-Clinical-Trial-2026.html",
         "工程菌与菌群移植（LBP-FMT）临床试验：干预菌群的人体证据到哪一步了"),
    ],
)

A["Gut-Microbiome-Exposome-Brain-Aging-Framework-2026.html"] = dict(
    topic="神经退行", ev="C", tag="综述",
    title="菌群 × 暴露组 × 脑老化：把「环境毒物」正式接入脑衰老研究框架",
    crumb="Cell Metabolism 综述 · 菌群-暴露组-脑轴",
    desc="综述系统论证肠道菌群是环境神经毒物暴露的首道代谢与屏障界面，决定宿主对毒物的反应与解毒能力，主张把「暴露组」（exposome）概念与脑衰老研究整合——为环境神经科学提供一个以菌群为中介的可干预层。",
    source=('Cell Metabolism 综述（2026-08-26 在线）· DOI '
            '<a href="https://doi.org/10.1016/j.cmet.2026.08.002" target="_blank" rel="noopener">10.1016/j.cmet.2026.08.002</a> · '
            '交叉判定=C（观点/综述，无独立实验数据）· <strong>待补全文</strong>'),
    body="""<p>脑衰老研究有一个长期的结构性缺口：<strong>它主要研究「人老了之后脑子发生了什么」，很少系统回答「环境里有什么在损伤脑子，以及为什么同样暴露、不同人受损程度差这么多」</strong>。这篇综述试图补的就是这一块。</p>

<h2>核心论点：菌群是暴露的第一道关口</h2>

<p>把环境神经毒物从入口到脑子的路径画出来，会经过三道关：</p>

<ol>
<li><strong>代谢</strong>——菌群直接参与有毒化合物的代谢与转化，可能<strong>解毒</strong>，也可能<strong>活化</strong>；</li>
<li><strong>屏障</strong>——肠道屏障与血脑屏障的实际通透性由菌群状态决定，是「进不进得来」的决定环节；</li>
<li><strong>宿主反应</strong>——菌群代谢产物作为信号分子，调节宿主的炎症与神经免疫应答。</li>
</ol>

<blockquote><p>因此，<strong>同样剂量的暴露，在不同个体身上造成的脑损伤可以差出一个数量级</strong>——差异不主要来自遗传，而可能大量来自菌群构成。</p></blockquote>

<h2>为什么「暴露组」这个词很关键</h2>

<p><strong>暴露组（exposome）</strong>指的是一个人一生中接触到的全部环境因素的集合，概念上是「基因组」的镜像——前者是外来的、动态的、可变的。把它与脑老化整合，意味着脑衰老研究要开始考虑：</p>

<table>
<thead><tr><th>传统脑衰老研究</th><th>纳入暴露组后</th></tr></thead>
<tbody>
<tr><td>关注遗传风险（如 APOE4）</td><td>同时关注环境风险及其累积剂量</td></tr>
<tr><td>结局视为个体属性</td><td>结局视为「暴露 ×菌群响应」的乘积</td></tr>
<tr><td>干预以药物/生活方式为主</td><td>增加「调节菌群响应」这一层干预</td></tr>
</tbody>
</table>

<p>这不是纯理论推演——肠道菌群参与环境毒物代谢这一点，在药物代谢、农药残留、重金属等领域都已有实证支持。把它系统接到脑老化上，是把分散的证据重新组织成一个可研究的对象。</p>

<h2>这个框架的实用价值</h2>

<p>如果这个视角成立，它给出的可操作方向有几条：</p>

<ul>
<li><strong>暴露史纳入队列研究</strong>：神经系统退行性疾病队列若只记录生活方式而不记录职业与环境污染暴露，会丢掉大量解释力；</li>
<li><strong>菌群作为修饰因子而非病因</strong>：这解释了为什么同样暴露的人群损伤差异巨大，也意味着<strong>干预靶点可能是「菌群响应能力」而非「清除毒物」</strong>；</li>
<li><strong>为「环境神经科学」提供锚点</strong>：该领域长期缺乏统一的因果框架。</li>
</ul>

<h2>必须说清楚的是：这是综述，不是新数据</h2>

<p>证据分级 <strong>C</strong>——这是一篇<strong>观点与框架型综述</strong>，没有提供独立实验数据。它的价值在于<strong>组织与提出问题</strong>，而不是证明结论。</p>

<p>要警惕的落差：综述提出的整合框架通常<strong>领先于验证数据若干年</strong>。「菌群决定毒性反应」在单个毒物上成立，不等于在整体暴露组上成立——真实暴露是混合物、多途径、多时段，交互效应几乎没有数据支撑。</p>

<blockquote><p>我的判断：这个框架值得跟踪，但它的正确用法是<strong>当作研究议程来读</strong>——看它提出了哪些可检验的具体假设，而不是把它当作已经确立的结论去理解人群风险。</p></blockquote>""",
    related=[
        ("Gut-Brain-Axis-Neurodegenerative-Diseases.html", "肠-脑轴与神经退行性疾病：机制综述"),
        ("Clostridium-Scindens-Centos-Gut-IAA-2026.html",
         "Clostridium scindens 与中心性吲哚乙酸（IAA）：菌群代谢物跨越血脑屏障的实例"),
    ],
)

ga.A.update(A)
ga.main()
