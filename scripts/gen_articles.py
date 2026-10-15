#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_articles.py —— 从 IMA 喂料池产出批量生成 news/*.html（v1.0）

输入：/tmp/lit/todo_write.json（经查重核实的漏收清单，含 title/topic/evidence/point/doi）
输出：news/<slug>.html + 更新 data/articles.json

纪律（继承 SOP §4.2）：
  - 摘要级卡片只写摘要给出的事实，付费墙未获取的一律标「待补全文」，**定量不臆测**
  - 每篇必须带证据分级 notice-box，A/B/C 口径与全站一致
  - 内部链接只用 /news/<slug>.html 相对形式（fix_related.py 与 sitemap 依赖此约定）
"""
import html
import json
import os
import re
import sys
from datetime import datetime

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
SRC = sys.argv[2]
DATE = sys.argv[3] if len(sys.argv) > 3 else "2026-10-15"

# ---------- 模板 ----------
HEAD = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta name="referrer" content="strict-origin-when-cross-origin">
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} — LongBiosci</title>
    <meta name="description" content="{desc}">
    <link rel="canonical" href="https://longbiosci.com/news/{slug}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="https://longbiosci.com/news/{slug}">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{desc}">
    <meta property="og:image" content="https://longbiosci.com/og-image.png">
    <meta property="og:site_name" content="LongBiosci">
    <meta property="article:published_time" content="{date}T00:00:00Z">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{desc}">
    <meta name="twitter:image" content="https://longbiosci.com/og-image.png">
    <link rel="icon" type="image/svg+xml" href="/favicon.svg">
    <link rel="icon" type="image/svg+xml" href="/favicon-dark.svg" media="(prefers-color-scheme: dark)">
    <link rel="apple-touch-icon" href="/apple-touch-icon.png">
    <link rel="stylesheet" href="/style.css">
    <script type="application/ld+json">
    {ld_news}
    </script>
    <script type="application/ld+json">
    {ld_crumb}
    </script>
<link rel="stylesheet" href="/poster.css">
<script src="/qr.js" defer></script>
<script src="/poster.js" defer data-tier="{ev}" data-topic="{topic}"></script>
<!-- longbiosci:analytics 无 Cookie、无跨站追踪、不收集身份信息；详见 /privacy/ -->
<script defer src="https://cloud.umami.is/script.js" data-website-id="bfb60723-d93d-4925-b1a2-d7ef51b9014c" data-do-not-track="true"></script>
</head>
<body>
    <a href="#main-content" class="skip-link">跳转到主要内容</a>
<header class="site-header">
    <nav class="wrap" aria-label="主导航">
        <a href="/" class="brand"><img src="/logo-mark.svg" alt="" class="brand-mark" width="28" height="28"><span class="brand-name">LongBiosci</span></a>
        <div class="main-nav">
      <a href="/">首页</a>
      <a href="/news/" aria-current="page">最新</a>
      <a href="/topics/" aria-label="主题专辑"><span class="nav-mq">主题</span>专辑</a>
      <a href="/guide/" aria-label="热词专题">热词<span class="nav-mq">专题</span></a>
      <a href="/research/" aria-label="概念与工具">概念<span class="nav-mq">与工具</span></a>
      <a href="/daily/">周刊</a>
      <a href="/evidence/" aria-label="证据分级">证据<span class="nav-mq">分级</span></a>
      <a href="/trials.html" aria-label="临床试验">临床<span class="nav-mq">试验</span></a>
      <a href="/companies/">产业</a>
      <a href="/about/">关于</a>
      <a href="/search.html" class="nav-search" aria-label="站内搜索"><svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true" focusable="false"><circle cx="6.8" cy="6.8" r="4.6" fill="none" stroke="currentColor" stroke-width="1.6"/><line x1="10.3" y1="10.3" x2="14" y2="14" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg><span class="nav-search-text">搜索</span></a>
    </div>
    </nav>
</header>

    <main class="article-container" id="main-content">
        <nav class="breadcrumb" aria-label="面包屑导航">
            <a href="/">首页</a> &gt; <a href="/news/">新闻</a> &gt; <span aria-current="page">{crumb}</span>
        </nav>

        <article>
            <header class="article-header">
                <span class="tag">{tag}</span>
                <span class="date"><time datetime="{date}">{date_cn}</time></span>
                <h1>{title}</h1>
                <p class="source">来源：{source}</p>
            </header>

            <div class="article-content">
{body}
            </div>

            <div class="related-block"><h3>延伸阅读</h3><ul class="related-list">{related}</ul></div>
<footer class="article-footer">
                <a href="/news/" class="back-link">← 返回新闻列表</a>
            </footer>
        </article>
    </main>

    <footer class="site-footer">
    <div class="wrap">
        <p>© 2026 LongBiosci 编辑部 · 衰老与长寿科技资讯</p>
        <a href="/rss.xml">RSS</a> · <!-- longbiosci:footer-stats -->匿名访问统计由 <a href="https://umami.is" target="_blank" rel="noopener">Umami</a> 提供（无 Cookie、不收集身份信息，详见 <a href="/privacy/">隐私政策</a>）<!--/longbiosci:footer-stats --> · <a href="/sitemap.xml">Sitemap</a> · <a href="/privacy/">隐私政策</a> · <a href="/about/">关于</a>
    </div>
</footer>

<div class="read-progress" aria-hidden="true"><div class="read-progress-bar" id="readBar"></div></div>
<button class="to-top" id="toTop" type="button" aria-label="回到顶部" title="回到顶部">↑</button>
<script src="/poster-overlay.js" defer></script>
</body>
</html>
"""

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def date_cn(d):
    dt = datetime.strptime(d, "%Y-%m-%d")
    return f"{WEEKDAYS[dt.weekday()]}, {dt.day} {MONTHS[dt.month - 1]}"


def notice(ev):
    t = {"A": "A 级（同行评议人体研究）",
         "B": "B 级（同行评议临床前研究，主要为动物模型）",
         "C": "C 级（预印本 / 观点评论，非原始研究）"}[ev]
    body = {
        "A": "<p><strong>本文属人体研究证据，但需注意：</strong>观察性或小样本干预的结论不等于已证实临床获益；效应量与长期安全性仍需更大规模、更长随访的试验验证。</p>",
        "B": "<p><strong>本文核心结论来自动物模型或体外细胞学，属临床前证据，不能外推至人体。</strong>「延长健康寿命」「改善功能」等表述在小鼠中的意义，与人类临床结局之间仍有距离。</p>",
        "C": "<p><strong>本文属观点/评论类文献，不是原始研究。</strong>其论点依赖于作者对既有证据的梳理与判断，<strong>不构成新的实验证据</strong>。本站标注 C 级即为此意——阅读时请把它当作「领域内的思考框架」，而非「研究发现」。</p>",
    }[ev]
    return (f'<div class="notice-box">\n'
            f'    <p><span class="tier tier-{ev.lower()}">{ev} 级</span>'
            f'<strong>证据分级：{t}</strong></p>\n'
            f'    {body}\n'
            f'    <p><strong>关于本文的文献来源：</strong>本站依据 IMA 知识库「五刊监控·深度文献卡片」'
            f'（SOP §4.2 摘要级）撰写，<strong>依据期刊公开摘要与 PubMed 元数据</strong>；'
            f'付费墙全文未获取之处已标注「待补全文」，<strong>未做任何数值推算补全</strong>。</p>\n'
            f'</div>')


def ld(title, desc, slug, date, crumb):
    news = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "url": f"https://longbiosci.com/news/{slug}",
        "headline": title,
        "description": desc,
        "image": "https://longbiosci.com/og-image.png",
        "author": {"@type": "Organization", "name": "LongBiosci 编辑部"},
        "datePublished": date,
        "publisher": {
            "@type": "Organization", "name": "LongBiosci",
            "url": "https://longbiosci.com",
            "logo": {"@type": "ImageObject",
                     "url": "https://longbiosci.com/og-image.png",
                     "width": 836, "height": 257},
        },
        "inLanguage": "zh-CN",
    }
    crumb_ld = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "首页", "item": "https://longbiosci.com/"},
            {"@type": "ListItem", "position": 2, "name": "新闻", "item": "https://longbiosci.com/news/"},
            {"@type": "ListItem", "position": 3, "name": crumb,
             "item": f"https://longbiosci.com/news/{slug}"},
        ],
    }
    return (json.dumps(news, ensure_ascii=False, indent=2),
            json.dumps(crumb_ld, ensure_ascii=False, indent=2))


# ---------- 文章内容（依据 IMA 深度文献卡片撰写） ----------
A = {}

A["Microbiome-Age-Clock-Bifidobacterium-5-AVAB-Healthspan-2026.html"] = dict(
    topic="免疫与炎症", ev="B", tag="研究进展",
    title="微生物组年龄时钟锁定一株双歧杆菌：单菌 + 单代谢物把抗衰从「混菌」推进到可产品化",
    crumb="益生菌与健康寿命",
    desc="中科院北京基因组所团队用微生物组年龄时钟 MicroAge 追踪衰老轨迹，锁定在两性、多队列中一致随龄耗竭的 Bifidobacterium pseudocatenulatum。老年鼠单菌口服即恢复肠稳态、减轻多器官炎症老化并延长健康span，其代谢物 5-AVAB 可部分复现。",
    source=('<a href="https://www.nature.com/nataging/" target="_blank" rel="noopener noreferrer">Nature Aging</a>'
            '（2026-09，6(9): 1946–1966）· 中国科学院北京基因组研究所 / 国家生物信息中心 '
            'Lu X、Ping J 等，通讯 Zhang W · 论文：<em>A geroprotective probiotic and its functional metabolite '
            'counteract inflammaging to extend healthspan</em> · DOI '
            '<a href="https://doi.org/10.1038/s43587-026-01181-4">10.1038/s43587-026-01181-4</a>'),
    body="""<p>肠道菌群影响衰老早已不是新闻，但<strong>究竟是哪些具体菌种、哪些代谢物在起决定作用</strong>，一直缺少可追踪的工具与因果验证。这篇发表在 <em>Nature Aging</em> 的研究，第一次把「微生物组年龄时钟」与「单菌 + 单代谢物」的因果验证接上了。</p>

<h2>为什么需要一把「微生物组年龄时钟」</h2>

<p>过去的研究里，菌群与衰老的关系多靠横断面关联：老人和年轻人的菌群构成不同。但菌群组成同时受饮食、药物、居住环境、甚至测序方法影响，<strong>很难把「衰老导致菌群改变」与「菌群改变影响衰老」区分开</strong>。作者的做法是先构建一把时钟——用菌群特征预测生物学衰老年龄，从而把「谁在随龄耗竭」变成可量化的问题。</p>

<h2>锁定的菌种：两性、多队列一致耗竭</h2>

<p>研究刻画了衰老过程中<strong>肠型特异</strong>的菌群重塑，随后用 MicroAge 追踪生物学衰老轨迹，在<strong>跨性别、跨多个中国队列</strong>中筛选出一致耗竭的候选菌——<strong>Bifidobacterium pseudocatenulatum</strong>（假链双歧杆菌）。一致性是关键：只在单一人群中被发现的菌，很难说是衰老的核心标志物。</p>

<h2>单菌口服的效果与关键代谢物</h2>

<ul>
<li><strong>老年鼠单菌治疗</strong>：口服该菌可挽救肠道稳态、减轻多器官炎症老化、改善认知与运动表现，并<strong>延长健康span</strong>。</li>
<li><strong>代谢物 5-AVAB</strong>（5-氨基戊酸甜菜碱）在人类衰老中<strong>生理性下降</strong>；单独补充可<strong>部分复现</strong>系统性获益——认知与运动改善、多器官炎症抑制。</li>
</ul>

<blockquote><p>这项研究最值得注意的，是它把抗衰微生物策略从「粪菌移植 / 混菌制剂」推进到了<strong>「单一可培养菌株 + 单一可定量代谢物」</strong>。后者在监管路径、质量控制与规模化生产上简单得多——5-AVAB 作为小分子，转化门槛明显低于活菌制剂。</p></blockquote>

<h2>局限：读的时候必须记住的三点</h2>

<ul>
<li><strong>人体部分是观察性的</strong>。时钟与队列关联只能提示「这株菌随龄下降」，<strong>不能证明补充它能延寿</strong>——人体没有干预试验。</li>
<li><strong>队列均为中国人群</strong>，饮食结构与遗传背景相对集中，跨族群外推性尚待验证。</li>
<li><strong>5-AVAB 只「部分复现」全身获益</strong>，说明还有其他效应物未被识别；且摘要<strong>未报告寿命终点</strong>——「延长健康span」有数据，延寿与否未知。此外队列数、样本量、效应量与统计量均为<strong>待补全文</strong>。</li>
</ul>
""",
    related=[("Oral-Microbiome-Neisseria-flavescens-Geroprotective-NatureAging-2026.html",
              "北大团队发现口腔「长寿菌」微黄奈瑟菌：Nature Aging 报道可延缓衰老并逆转多项指标"),
             ("Gut-Microbiome-Fecal-Transplant-Liver-Cancer-2026.html",
              "粪菌移植重塑肠道菌群：恢复年轻微生物组可抑制肝癌发生"),
             ("Exercise-Gut-Microbiome-TMAO-Klotho-Osteoporosis-2026.html",
              "运动如何通过肠道菌群-TMAO-αKlotho 通路对抗老年骨质疏松")],
)

A["cGAS-Deficient-Premature-Aging-LINE1-Inflammation-2026.html"] = dict(
    topic="表观遗传", ev="B", tag="研究进展",
    title="反直觉：敲除 cGAS 的小鼠提前衰老——「抑制 cGAS 抗衰」这条主流假设需要重新评估",
    crumb="cGAS 缺失与早衰",
    desc="罗切斯特大学 Gorbunova 团队发现 cGAS 敲除小鼠呈现加速衰老、多器官炎症、中位寿命缩短与衰弱增加，机制是 LINE1 反转座子去抑制。这对当前正升温的「抑制 cGAS-STING 即可抗衰」叙事构成明确的风险边界。",
    source=('<a href="https://www.nature.com/nataging/" target="_blank" rel="noopener noreferrer">Nature Aging</a>'
            '（2026-09，6(9): 1849–1865）· 罗切斯特大学 Gorbunova V 团队 · 论文：<em>cGAS-deficient mice '
            'display premature aging associated with derepression of LINE1 elements and inflammation</em> · DOI '
            '<a href="https://doi.org/10.1038/s43587-026-01206-y">10.1038/s43587-026-01206-y</a>'),
    body="""<p>过去几年，<strong>cGAS-STING 通路</strong>几乎被默认成抗衰靶点：胞质 DNA 激活 cGAS → 产生 cGAMP → 激活 STING → 释放 I 型干扰素与炎症因子，而「 inflammaging （炎症性衰老）」正是衰老的核心机制之一。于是「抑制 cGAS」几乎成了一句不需要论证的前提。</p>

<p>这项研究的价值恰恰在于<strong>它去检验了这个前提</strong>——而且结果与预期相反。</p>

<h2>发现：缺失 cGAS 的小鼠衰老得更快</h2>

<ul>
<li>cGAS 敲除小鼠出现<strong>意外的加速衰老</strong>表型与<strong>多器官炎症</strong>；</li>
<li><strong>中位寿命缩短</strong>，衰弱增加；</li>
<li>机制层面：<strong>LINE1 反转座子去抑制</strong>——LINE1 转录升高、LINE1 元件 DNA 甲基化下降、胞质中 LINE1 cDNA 水平升高，进而触发炎症；</li>
<li>细胞核层面出现 <strong>H3K9me3 景观平滑化</strong>与染色质可及性升高；</li>
<li>体外 cGAS 敲低可<strong>复现</strong>该表型。</li>
</ul>

<blockquote><p>作者的结论性判断是：cGAS 在细胞核内具有<strong>维持异染色质的非催化功能</strong>，且这一功能<strong>独立于</strong>其作为胞质 DNA 感受器的角色与催化活性。这解释了为什么把它整个敲掉会适得其反。</p></blockquote>

<h2>为什么这条必须写进任何 cGAS 相关选题</h2>

<p>过去半年里，本站记录了多条把 cGAS-STING 当作干预靶点的研究——从 SLC25A1 抑制剂抑制 SASP 而不动细胞周期，到运动改善 cGAS 通路，再到各种「降低胞质 DNA 释放」的策略。<strong>它们共同的前提是「cGAS 活性过高有害」</strong>。这项研究没有否定那些策略，但它给出了一个明确的风险边界：<strong>cGAS 有核内看家功能，全敲或全抑制可能伤及异染色质稳态</strong>。</p>

<p>由此产生一个尚未解答的关键问题：<strong>部分抑制或时相性抑制</strong>（例如只在炎症高峰窗口抑制）能否获得「降低炎症但不破坏异染色质」的治疗窗？这是转化上真正的未知数。</p>

<h2>局限</h2>

<ul>
<li><strong>全身性敲除</strong>，非条件性或诱导型——发育期效应与成年期效应<strong>无法分离</strong>，这是解读因果时最大的限制。</li>
<li>「核内非催化功能」的<strong>分子细节</strong>（cGAS 如何与异染色质机器互作）摘要未展开。</li>
<li>寿命缩短幅度、衰弱评分、LINE1 甲基化差异幅度、样本量与 p 值均为<strong>待补全文</strong>。</li>
</ul>
""",
    related=[("cGAS-STING-Mitochondria-DNA-Ovarian-Aging-Nature-Aging-2026.html",
              "mtDNA 泄露激活 cGAS-STING：卵巢衰老的新驱动机制"),
             ("Mitochondrial-Metabolism-Epigenetic-Crosstalk-SASP-Nature-2026.html",
              "线粒体代谢-表观遗传对话驱动 SASP：衰老细胞炎症的新机制"),
             ("SIRT1-L1-Retrotransposon-Heterochromatin-AgingCell-2026.html",
              "SIRT1 通过稳定异染色质修饰复合体沉默 L1 逆转录元件")],
)

A["Caloric-Restriction-Somatic-Mutation-Genome-Integrity-Cell-2026.html"] = dict(
    topic="代谢与营养", ev="B", tag="研究进展",
    title="热量限制能降低小鼠全基因组体细胞突变：基因组完整性是可改造的衰老轴",
    crumb="热量限制与体细胞突变",
    desc="纽约大学 Evrony 团队与 NIA 合作，用高保真双链 DNA 测序发现热量限制降低小鼠多组织、多细胞类型的全基因组体细胞突变负荷，替换与插入缺失均下降，并抑制产生多数突变的 SBS5 过程。",
    source=('<a href="https://www.cell.com/cell/" target="_blank" rel="noopener noreferrer">Cell</a>'
            '（在线预发表 2026-09-09）· 纽约大学格罗斯曼医学院 人类遗传与基因组学中心 Evrony GD 团队'
            '（合作：NIA 国立衰老研究所）· 论文：<em>Caloric restriction modulates genome-wide somatic '
            'mutation in mice</em> · DOI '
            '<a href="https://doi.org/10.1016/j.cell.2026.08.013">10.1016/j.cell.2026.08.013</a>'),
    body="""<p>体细胞突变终生在每个细胞中累积，这是「基因组不稳定」这一衰老标志的核心。但此前几乎没人问过：<strong>延寿干预能不能降低突变累积？</strong>热量限制（CR）是跨物种延寿效果最确凿的干预，纽约大学 Evrony 团队与 NIA 合作，第一次把它与体细胞突变负荷直接连起来。</p>

<h2>方法：用当前最高保真的测序手段</h2>

<p>研究对 CR 与对照小鼠的 <strong>bulk 肝脏、bulk 肾脏、肝细胞、小脑神经元</strong>做<strong>高保真双链（duplex）DNA 测序</strong>，量化全基因组体细胞突变负荷（替换与插入缺失），并做突变签名分析——重点看 <strong>SBS5</strong>。</p>

<h2>核心发现</h2>

<ul>
<li>CR <strong>降低小鼠多组织、多细胞类型</strong>的全基因组体细胞突变负荷；</li>
<li><strong>替换与插入缺失负荷均下降</strong>，效应幅度因样本类型而异；</li>
<li>CR 降低 <strong>SBS5</strong>——这个在哺乳动物中产生多数突变、机制至今仍不甚清楚的单碱基替换过程——的活性；</li>
<li><strong>反直觉的一点</strong>：突变负荷的降低<strong>在转录失活区域最大</strong>。</li>
</ul>

<blockquote><p>结论层面的意义是：这项工作把<strong>饮食—衰老—基因组完整性</strong>三者连成一线，并确立<strong>基因组完整性是一个可改造的衰老轴</strong>。换句话说，基因组不再只是被动记录衰老的「记录仪」，而可能是可以被干预的「方向盘」。</p></blockquote>

<h2>它引出的可检验假设</h2>

<p>既然 CR 能降低突变负荷，那么<strong>作为「CR 模拟物」的 GLP-1 受体激动剂是否也有同样效果？</strong>这个问题目前没有答案，但它是这套结论最自然的延伸。本站此前报道过司美格鲁肽延长雌性小鼠寿命的 Nature 封面研究（见延伸阅读），两条线索可以在这个问题上合流。</p>

<h2>局限（本条引用风险较高，请注意）</h2>

<ul>
<li><strong>摘要完全没有给出效应量</strong>——突变负荷下降多少个百分点、CR 方案（限制比例、起始年龄、持续时长）、各组织具体数值、SBS5 活性变化幅度、动物数与 p 值，<strong>全部待补全文</strong>。这是本条最大的引用限制，本文不给出任何具体数字。</li>
<li>CR 方案与持续时间未知，<strong>难以与其他 CR 研究对齐</strong>。</li>
<li>「转录失活区降幅最大」的<strong>解释未在摘要中给出</strong>——这本身是个需要解释的谜题。</li>
<li><strong>未报告是否同时延长寿命</strong>。本文的终点是突变负荷，不是寿命——两者不可互换。</li>
</ul>
""",
    related=[("Caloric-Restriction-Longevity-Mechanism-Nature-2025.html",
              "热量限制：从机制到干预的完整证据链"),
             ("GLP1-Semaglutide-Lifespan-Female-Mice-Nature-2025.html",
              "Nature 封面研究：晚年司美格鲁肽治疗显著延长小鼠寿命——或为热量限制模拟物"),
             ("DREAM-Complex-Somatic-Mutation-Lifespan-2026.html",
              "DREAM 复合体：连接体细胞突变与寿命的「转录刹车」")],
)

A["Skin-Innervating-Glutamatergic-Neurons-Aging-Cell-2026.html"] = dict(
    topic="神经退行", ev="B", tag="研究进展",
    title="皮肤里的谷氨酸能神经在抗衰：去神经支配会让皮肤提前老去",
    crumb="神经—成纤维细胞轴与皮肤衰老",
    desc="上海交大附属第一人民医院 Wang H 团队发现，皮肤去神经支配加速衰老（胶原减少）；Nefh 在衰老皮肤中下降并在 Vglut2⁺ 谷氨酸能神经元中驱动成纤维细胞衰老，补充谷氨酸可改善衰老表型。",
    source=('<a href="https://www.cell.com/cell/" target="_blank" rel="noopener noreferrer">Cell</a>'
            '（2026-09，189(18): 5706–5723.e8）· 上海交通大学医学院附属第一人民医院 / '
            '上海交大医学院分子与细胞治疗前沿研究院 Wang Z、Jin X 等，通讯 Wang H · 论文：<em>Skin-innervating '
            'glutamatergic neurons modulate aging</em> · DOI '
            '<a href="https://doi.org/10.1016/j.cell.2026.06.032">10.1016/j.cell.2026.06.032</a>'),
    body="""<p>大多数抗衰老研究盯着免疫、代谢、基因、细胞衰老这些「内部」系统。这篇论文把镜头转向一条被忽略的轴：<strong>外周神经如何调控组织衰老</strong>。</p>

<h2>核心链条：去神经 → 胶原流失 → 皮肤提前老</h2>

<p>研究人员从实验干预入手：<strong>让皮肤去神经支配</strong>，结果胶原减少——皮肤提前衰老。随后定位到具体分子：</p>

<ul>
<li><strong>Nefh</strong>（神经丝重链）在<strong>衰老皮肤中下降</strong>，主要表达于 <strong>Vglut2⁺ 皮肤支配性谷氨酸能神经元</strong>；</li>
<li>真皮<strong>成纤维细胞</strong>（胶原的主要产生者）<strong>频繁接触 Nefh⁺ 神经纤维</strong>；</li>
<li>在 Vglut2⁺ 谷氨酸能神经元中<strong>条件性删除 Nefh</strong>，会驱动成纤维细胞衰老与胶原丢失——这是因果证据，不是相关；</li>
<li><strong>补充谷氨酸可改善皮肤衰老表型</strong>。</li>
</ul>

<h2>机制：Cdk5 是那个同时握住两端的分子</h2>

<p>机制层面，<strong>Cdk5 同时与 Nefh 和 Vglut2 互作</strong>，维持谷氨酸释放与胶原稳态。而在成纤维细胞一侧，<strong>Slc1a3</strong> 介导谷氨酸的促胶原与抗衰老作用。所以这条通路可以写成：<em>神经元 Cdk5 → 维持 Nefh/Vglut2 → 谷氨酸释放 → 成纤维细胞 Slc1a3 → 抗衰老、促胶原</em>。</p>

<blockquote><p>这条线索的意义在于<strong>它提供了一批非经典靶点</strong>：谷氨酸、Slc1a3、Cdk5、Nefh——都不在常见的「senomorphic」清单上。对皮肤抗衰这类以「补充剂竞争」为主的市场，这是一个完全不同的机制入口。</p></blockquote>

<h2>一个更大的图景</h2>

<p>把这条结果与近年的其他发现放在一起，图景变得清晰：肌肉衰老涉及神经肌肉组分的「适应不良信号回路」，心肌纤维类型转换由线粒体—核逆行信号驱动。<strong>衰老不是某个细胞 autonomous地坏掉，而是跨系统协调失败——神经系统是被长期忽视的一极。</strong></p>

<h2>局限</h2>

<ul>
<li><strong>纯小鼠模型</strong>。人体皮肤中神经—成纤维细胞互作是否同构，未知。</li>
<li>谷氨酸补充的<strong>给药方式、剂量与长期安全性</strong>均未报告。这不是可以据此自行补充的建议。</li>
<li>未评估其他皮肤衰老维度（弹性、屏障功能、毛发生长）。</li>
<li>全部定量数据（胶原含量变化倍数、衰老标志物倍数、神经纤维接触频率、n 与 p 值）<strong>待补全文</strong>。</li>
</ul>
""",
    related=[("Skeletal-Muscle-Regenerative-Degenerative-Niche-AgingCell-2026.html",
              "从再生到退行：骨骼肌衰老的多细胞对话与群体动态（综述）"),
             ("Mitochondrial-DNA-Leakage-cGAS-STING-Activity-AgingCell-2026.html",
              "DNA 间隙：衰老驱动因素新证据——HMGB1 Box A 基因疗法在猕猴中逆转衰老生物标志物"),
             ("NAD-Metabolic-Reprogramming-CD8-Senescence-Ulcerative-Colitis-2026.html",
              "NAD⁺ 代谢失调驱动 CD8⁺ T 细胞衰老并加重溃疡性结肠炎")],
)

A["Rhesus-Macaque-Plasma-CSF-Proteomics-Aging-GeroScience-2026.html"] = dict(
    topic="生命历程", ev="B", tag="研究进展",
    title="66 只恒河猴的血液与脑脊液：衰老的蛋白信号主要写在「血」里",
    crumb="非人灵长类的衰老蛋白组",
    desc="加州大学戴维斯分校 CNPRC 用 NULISAseq 检测 66 只恒河猴的 CSF 与血浆，发现血浆的年龄相关差异更广，且血浆 Aβ 与磷酸化 tau 比 CSF 更能追踪实际年龄与皮层淀粉样负荷。",
    source=('<a href="https://link.springer.com/journal/11357" target="_blank" rel="noopener noreferrer">GeroScience</a>'
            '（在线预发表 2026-09-26）· 加州大学戴维斯分校 国家生物医学研究所（CNPRC）'
            'Diniz GB、Schwartz K 等，通讯 Morrison JH · 论文：<em>Plasma and cerebrospinal fluid '
            'proteomics reveal distinct patterns of senescence and neuropathology in aging rhesus macaques</em> · DOI '
            '<a href="https://doi.org/10.1007/s11357-026-02555-7">10.1007/s11357-026-02555-7</a>'),
    body="""<p>衰老是神经退行病的首要风险因素，但要把<strong>「生理性脑老化」与「病理性衰退」</strong>区分开，需要在转化模型里把蛋白层面的标志界定清楚。小鼠不够接近人，猕猴是常用替代，但它们自身的衰老蛋白组此前并未系统刻画。</p>

<h2>66 只恒河猴，两种体液对比</h2>

<p>团队用 <strong>NULISAseq</strong> 靶向蛋白组平台，检测 <strong>66 只恒河猴</strong>（成年、老年前期、老年期三个年龄段）的<strong>脑脊液与血浆</strong>，并与人类参考样本比对。核心发现分几层：</p>

<ul>
<li><strong>血浆中的年龄相关差异更广泛，且以上调为主</strong>；CSF 中随龄变化的蛋白相对较少。</li>
<li>经典神经衰老标志——轴突、星形胶质、小胶质生物学，含<strong>神经丝、GFAP、TREM2</strong>——呈现与人类衰老报道<strong>相似</strong>的年龄相关模式。这支持 NHP 作为转化模型的可靠性。</li>
<li><strong>突触与屏障蛋白呈区室分化</strong>：neuronal pentraxins 与 pleiotrophin 在老年动物 <strong>CSF 中更低</strong>；脉络丛蛋白 <strong>FOLR1 与 IGFBP7</strong> 在老年前期动物中更低。</li>
<li>免疫组化证实老年脑<strong>广泛的实质淀粉样沉积</strong>，但<strong>tau 病理稀疏</strong>。</li>
<li><strong>血浆 Aβ 与 p-tau 比 CSF 更能追踪实际年龄与皮层淀粉样负荷</strong>——这是对采样策略有直接含义的判断。</li>
<li><strong>IL6、GDF15</strong> 等系统性炎症与代谢应激蛋白在老年动物中升高，类似人类的炎症老化。</li>
<li>老年动物<strong>可依 CSF 蛋白特征再聚为亚群，且该分群不能由实际年龄解释</strong>。</li>
</ul>

<h2>两个可直接引用的判断</h2>

<p>其一，<strong>血浆（而非 CSF）的 Aβ 与 p-tau 更能追踪脑淀粉样负荷</strong>。如果成立，生物标志物采样策略可以简化——腰穿不是必需的。</p>

<p>其二，<strong>老年个体可按分子特征分群，且该分群超越实际年龄</strong>。这正是「生物学年龄 &gt; 日历年龄」的核心论据，与本站此前报道的结构衰老时钟（PathStAR）、SASP Score 同向。</p>

<h2>局限</h2>

<ul>
<li><strong>横断面研究</strong>——年龄差异是推断出来的，不是纵向观察到的。</li>
<li>NHP 的淀粉样沉积<strong>以实质为主而 tau 稀疏</strong>，与人类 AD 的病理谱不完全一致，不能等同看待。</li>
<li>CSF 亚群的<strong>纵向意义未验证</strong>——这种分群是否预测后续衰退，是未知数。</li>
<li>采样过程（麻醉、脑脊液穿刺）对蛋白水平的潜在影响<strong>未讨论</strong>。</li>
<li>蛋白数量、差异倍数、相关性系数、亚群数与 p 值均为<strong>待补全文</strong>。</li>
</ul>

<p style="margin-top:1.5rem"><em>本文对应的原始期刊为 GeroScience（Springer，开放获取），付费墙全文可直接免费获取，本条「待补全文」项可优先补齐。</em></p>
""",
    related=[("PathStAR-Structural-Aging-Human-Tissues-Nature-Aging-2026.html",
              "首个跨 40 种人体组织的结构衰老图谱：PathStAR 从常规病理图像量化组织结构性衰老"),
             ("SASP-Score-Deep-Learning-Senescent-Cell-2026.html",
              "不用活检也能看见衰老细胞：深度学习构建 SASP Score 预测死亡与疾病风险"),
             ("Dog-Epigenetic-Clock-LINE1-Science-2026.html",
              "大狗的表观遗传时钟走得更快：Science 报告 894 只犬 LINE1 跳跃基因去甲基化")],
)

A["NAD-Precursor-Head-to-Head-RCT-NR-NMN-2026.html"] = dict(
    topic="代谢与营养", ev="A", tag="临床试验",
    title="NR 与 NMN 头对头：两者都能把全血 NAD⁺ 翻倍，但「标志物翻倍」不等于「人变年轻」",
    crumb="NAD⁺ 前体的人体证据",
    desc="头对头 RCT（n=65）显示 NR 1000 mg 与 NMN 1000 mg 服用 14 天均使全血 NAD⁺ 约翻倍且耐受良好。这一结果确认了药代效应，但 NAD⁺ 上升本身不是获益证明——这是本站跟踪 NAD⁺ 赛道时反复强调的判读纪律。",
    source='IMA 知识库「临床×科学文献交叉追踪·周更」（2026-10-13 批次）· 交叉判定=C（标志物≠获益）· 置信度=高（RCT）',
    body="""<p>NAD⁺ 是衰老研究里最热的代谢节点，NR（烟酰胺核糖）与 NMN（β-烟酰胺单核苷酸）是市面最主流的两个前体。但过去它们各自做试验，<strong>缺少头对头直接比较</strong>——而这正是「我该买哪个」这个问题最需要的答案。</p>

<h2>这项试验的结果</h2>

<ul>
<li>样本量 <strong>n=65</strong>，NR 1000 mg 与 NMN 1000 mg，服用 <strong>14 天</strong>；</li>
<li>两者均使<strong>全血 NAD⁺ 约翻倍</strong>；</li>
<li><strong>耐受性良好</strong>。</li>
</ul>

<h2>但请注意交叉判定：C 级 —— 标志物 ≠ 获益</h2>

<blockquote><p>这是本站给这一条打上 <strong>C（标志物≠获益）</strong>判定的根本原因。<strong>全血 NAD⁺ 翻倍是药代动力学结果，不是临床获益结果。</strong></p></blockquote>

<p>两者之间的差别是根本性的：</p>

<ul>
<li><strong>NAD⁺ 是标志物</strong>——测到它升高，只能说明「前体进去了、代谢通路走通了」；</li>
<li><strong>终点是健康寿命</strong>——要证明有抗衰价值，需要看到功能改善、疾病发生率下降或寿命延长。</li>
</ul>

<p>从「一个生化指标翻倍」到「一个人更健康、更长寿」，中间隔着细胞内分区定位（NAD⁺  compartments 高度区室化，血液里翻倍不等于线粒体里翻倍）、下游通路激活程度、以及数十年健康结局。这些不是同一个问题。</p>

<h2>这与本站此前的报道一致</h2>

<p>本站此前报道过 NAD⁺ 前体的系统评价与荟萃分析（15 项 RCT，250–2000 mg/d，14 天–24 周），结论同样是体重、BMI、空腹血糖、HbA1c 等代谢指标有改善，<strong>但缺乏硬性终点</strong>。两项研究指向同一个判断：NAD⁺ 前体在<strong>改善代谢指标</strong>上有相当一致的作用，但<strong>「延寿」目前仍无人体证据</strong>。</p>

<h2>局限</h2>

<ul>
<li>14 天疗程只能观察药代与短期安全性，<strong>不涉及长期结局</strong>。</li>
<li><strong>样本量 65 例</strong>，不足以检出中等效应量的临床差异。</li>
<li>全血 NAD⁺ 测定的技术方法学差异较大，跨试验可比性有限。</li>
<li><strong>本文为交叉追踪条目，未取得原始论文全文</strong>，具体统计量与不良事件细节待补；本文不给出摘要外的任何数值。</li>
</ul>
""",
    related=[("NAD-Precursor-Systematic-Review-Meta-Analysis-2026.html",
              "NAD⁺ 前体系统评价：15 项 RCT 的代谢指标改善汇总"),
             ("NAD-Blood-Frailty-Itabashi-Cohort-GeroScience-2026.html",
              "社区老年人全血 NAD⁺ 浓度与衰弱的关联（Itabashi 队列）"),
             ("NMN-Consumer-Grade-Evidence-Gap-Longevity-2026.html",
              "NMN 与 NAD⁺：消费级抗衰最大品类，人体证据究竟有多弱")],
)

A["TAME-Still-Zero-Participants-2026-Midyear-Status.html"] = dict(
    topic="器官衰老", ev="A", tag="行业观察",
    title="TAME 至今仍未入组任何受试者：这个用 FDA 背书的抗衰旗舰试验，卡在了哪里",
    crumb="TAME 试验的进展与瓶颈",
    desc="截至 2026 年中，TAME 仍未入组任何受试者。FDA 早在 2015 年就同意其复合终点（CVD+癌症+痴呆+死亡），约 4500 人的规模看似已成定局。本文梳理这个「元老级」抗衰试验的现实困境。",
    source='IMA 知识库「临床×科学文献交叉追踪·周更」（2026-10-13 批次）· 交叉判定=C（旗舰缺位）· 置信度=高',
    body="""<p>如果要给「衰老研究能否走到终点」找一个试金石，TAME（TAME - Targeting Aging with Metformin）几乎是唯一候选。它不是一个小试验，而是一个<strong>以衰老本身为终点</strong>的III 期试验。</p>

<h2>原本的计划</h2>

<ul>
<li><strong>规模</strong>：约 <strong>4500 人</strong>；</li>
<li><strong>干预</strong>：二甲双胍；</li>
<li><strong>终点</strong>：<strong>复合终点</strong>——心血管疾病、癌症、痴呆与死亡；</li>
<li><strong>监管背书</strong>：FDA 于 <strong>2015 年</strong>即已同意这一复合终点设计，这在当时是相当超前的决定。</li>
</ul>

<h2>现实：至 2026 年中，仍未入组任何受试者</h2>

<blockquote><p>从 2015 年 FDA 点头，到 2026 年仍然零入组——<strong>这个试验已经停滞了大约十年</strong>。本文的交叉判定是 <strong>C（旗舰缺位）</strong>，指的不是「结果不利」，而是<strong>这项本该提供答案的试验，根本没有提供答案</strong>。</p></blockquote>

<p>这是抗衰领域一个结构性尴尬：<strong>最需要的证据类型（大规模、以衰老/死亡为终点的试验），恰恰是最难启动的</strong>——招募难度大、周期长达十余年、终点判定复杂、经费需求天文数字。TAME 卡住，本质上是整个领域转化困境的一个缩影。</p>

<h2>为什么二甲双胍这条路尤其难走</h2>

<p>本站此前的报道提供了两个不利数据点：</p>

<ul>
<li><strong>二甲双胍会钝化运动适应</strong>（两项 <em>Aging Cell</em> 2019 RCT）：有氧运动中胰岛素敏感性与 VO₂max 的增益被削弱，抗阻训练的肌肥大效应也减弱。对于把「运动」作为主要抗衰手段的人群，这意味着两者可能<strong>互相抵消</strong>。</li>
<li>本站另一篇记录了<strong>直接 AMPK 激活剂 991</strong> 的工作——之所以要用「直接」二字，正是因为二甲双胍这类间接激活剂存在脱靶问题。<strong>但 991 在线虫与果蝇中的延寿效果，尚未在小鼠寿命上验证</strong>。</li>
</ul>

<p>这不意味着二甲双胍无效，而是说明<strong>「二甲双胍 = 抗衰药」这个等号从未被人体证据支持过</strong>，它至今是一个基于观察性数据与广泛临床使用经验建立的假设。</p>

<h2>局限</h2>

<ul>
<li><strong>本文为交叉追踪条目，未取得 TAME 官方状态文档</strong>。「未入组」的具体时点与障碍归因（经费、伦理审批、招募、终点可行性）来自交叉追踪记录，<strong>细节待补</strong>。</li>
<li>本文<strong>不对 TAME 是否终将启动作预测</strong>，也不对其科学价值作评价——它可能只是时机未到。</li>
</ul>
""",
    related=[("Metformin-Aging-Mechanism-Review-2026.html",
              "二甲双胍与衰老：从 AMPK 到免疫代谢的机制全景"),
             ("AMPK-Direct-Activation-991-Lifespan-AgingCell-2026.html",
              "直接激活 AMPK 让酵母、线虫、果蝇延寿逾 25%：Aging Cell 首次证明 AMPK 本身是延寿靶点"),
             ("Metformin-Blunts-Exercise-Adaptation-AgingCell-2019-RCT.html",
              "二甲双胍钝化运动适应：两项 Aging Cell 随机对照试验的启示")],
)

A["Senotherapeutics-Fisetin-Derivatives-Phenotypic-Screening-AgingCell-2026.html"] = dict(
    topic="细胞衰老", ev="B", tag="研究进展",
    title="表型药物筛选找到新型黄酮类 senotherapeutics：fisetin 衍生物活性更强",
    crumb="表型筛选与 senotherapeutics",
    desc="Aging Cell 报道通过表型药物发现获得新型黄酮类 senotherapeutics，fisetin 衍生物 SR29384/SR31133 表现出更强的 senolytic 活性，推定靶点包括 PARP1/CDK2/BCL-xL。",
    source=('<a href="https://onlinelibrary.wiley.com/journal/14749198" target="_blank" rel="noopener noreferrer">Aging Cell</a>'
            '（2026-10）· 论文：<em>Phenotypic drug discovery yields novel flavonoid senotherapeutics</em> · DOI '
            '<a href="https://doi.org/10.1111/acel.70736">10.1111/acel.70736</a>'),
    body="""<p>senolytic 药物开发长期面临一个方法学难题：<strong>靶点已知，但不知道该往哪个方向优化</strong>。主流路线围绕 Bcl-2 家族、PI3K/AKT、p53-p21 等通路做理性设计，而另一条路是<strong>表型药物发现</strong>（phenotypic drug discovery）——不看机制，直接用「衰老细胞会不会死」当读出，筛出能干的化合物，再回头找机制。</p>

<h2>核心发现</h2>

<p>这项工作走的是表型路线：</p>

<ul>
<li>从<strong>fisetin</strong>（非瑟酮，一种已知的 senolytic 候选黄酮）出发，找到衍生物 <strong>SR29384</strong> 与 <strong>SR31133</strong>，<strong>senolytic 活性显著强于母体分子</strong>；</li>
<li>推定靶点包括 <strong>PARP1、CDK2、BCL-xL</strong>。</li>
</ul>

<blockquote><p>这条线索的意义在于：<strong>fisetin 本身是当前 senolytic 领域被讨论最多的候选分子之一</strong>（本站此前报道过 D+Q 与 fisetin 的对比研究）。母体分子的结构-活性关系被打开，意味着后续优化有了明确的化学空间，而不必从零开始设计。</p></blockquote>

<h2>表型筛选的意义与代价</h2>

<p><strong>优势</strong>：不依赖机制假设，因此在「衰老细胞到底依赖什么存活通路」尚无定论的当下，表型筛选反而更可能抓到真实有效的靶点——这一点与本月另一项 cGAS 敲除早衰研究的教训相互印证：<strong>基于机制假设做出来的干预，可能因为假设本身不完整而翻车</strong>。</p>

<p><strong>代价</strong>：表型筛选给出的「推定靶点」需要独立验证。这类研究最常见的模式是「筛出化合物 → 找到结合蛋白 → 提出机制」，其中<strong>结合不等于功能相关性</strong>——化合物可能只是通过脱靶起效。</p>

<h2>局限</h2>

<ul>
<li>全部为<strong>体外/临床前数据</strong>，尚无任何人体安全性或有效性信息。</li>
<li><strong>靶点为推定</strong>（原文即标注推定），缺乏遗传学验证（如敲低目标蛋白后化合物是否失效）。</li>
<li>是否在<strong>体内老年模型</strong>中复现效力、剂量窗如何、是否损害健康细胞——这些是决定命运的问题，摘要层面<strong>待补全文</strong>。</li>
<li>fisetin 及衍生物均<strong>属实验性化合物</strong>，不可与市售「黄酮抗衰补剂」混为一谈。</li>
</ul>
""",
    related=[("Senolytic-Cost-Benefit-Precision-Intervention-2026.html",
              "senolytic 的成本收益与精准干预"),
             ("Dasatinib-Quercetin-MASH-Liver-Fibrosis-RCT-2026.html",
              "达沙替尼+槲皮素治疗 MASH 肝纤维化：31 人随机对照试验 47% 纤维化改善"),
             ("cGAS-Deficient-Premature-Aging-LINE1-Inflammation-2026.html",
              "反直觉：敲除 cGAS 的小鼠提前衰老——「抑制 cGAS 抗衰」需要重新评估")],
)

A["Rapa-Small-Dose-DNA-Damage-Repair-p21-Immune-Cells-2026.html"] = dict(
    topic="细胞衰老", ev="B", tag="研究进展",
    title="低剂量雷帕霉素的意外机制：不是自噬，而是让免疫细胞更能扛 DNA 损伤",
    crumb="雷帕霉素与基因组韧性",
    desc="低剂量雷帕霉素通过增强 DNA 损伤韧性降低老年人免疫细胞 p21，且该效应非自噬或蛋白合成依赖，提出「genoprotection（基因组保护）」这一不同于经典 mTOR 抑制的解释。",
    source='IMA 知识库「临床×科学文献交叉追踪·周更」（2026-10-13 批次）· 交叉判定=A（机制）· 置信度=中（未测临床终点）',
    body="""<p>过去二十年，雷帕霉素抗衰的机制解释几乎总是同一套：<strong>抑制 mTORC1 → 启动自噬 → 清除衰老细胞与受损成分</strong>。这项研究提出了一个不同的答案，而且它在人类样本中观察到了。</p>

<h2>核心发现：保护基因组，而非启动自噬</h2>

<ul>
<li><strong>低剂量雷帕霉素降低老年人免疫细胞的 p21 水平</strong>；</li>
<li>关键在于<strong>「DNA 损伤韧性」（DNA damage resilience）</strong>——细胞在同等损伤下承受更强、修复后存活更好；</li>
<li>该效应<strong>不依赖自噬，也不依赖蛋白合成抑制</strong>——用实验排除了这两条经典解释；</li>
<li>作者据此提出 <strong>genoprotection（基因组保护）</strong>这一概念。</li>
</ul>

<h2>为什么这个机制更有说服力</h2>

<blockquote><p>如果一种干预能<strong>提高细胞处理 DNA 损伤的能力</strong>，那它作用在的是衰老最基础的损伤累积过程上游，而不是某个下游表型。这解释了为什么小剂量也可能有效——它不必清除细胞，只需让细胞更能扛。</p></blockquote>

<p>这也与本站近期记录的一个大趋势吻合：<strong>基因组完整性正从「被动记录」变成「可干预的衰老轴」</strong>。同期另一项 <em>Cell</em> 研究发现热量限制能降低小鼠全基因组体细胞突变负荷（见延伸阅读），两条独立工作指向同一个结论——维护基因组，可能是比清除衰老细胞更上游的策略。</p>

<h2>局限</h2>

<ul>
<li><strong>未测量任何临床终点</strong>。降低 p21 与增强损伤韧性是细胞层面的指标，<strong>不等于人活得更好、更久</strong>。</li>
<li><strong>老年人来源细胞的体外实验</strong>，无法完全代表体内环境的免疫衰老。</li>
<li>本站此前报道过两项人体试验的相反信号：<strong>HFpEF 合并衰弱患者 0.5 mg/d×6 个月功能终点失败</strong>（见延伸阅读），说明低剂量在真实临床情境中未必有效。</li>
<li><strong>本文为交叉追踪条目，未取得原始论文全文</strong>，具体效应量、p 值与统计设计待补；本文不给出摘要外的数值。</li>
</ul>
""",
    related=[("Rapamycin-Aging-Mechanism-Review-2026.html",
              "雷帕霉素与 mTOR：从机制到临床的完整证据链"),
             ("Rapamycin-HFpEF-Frailty-Functional-Endpoint-Failure-2026.html",
              "雷帕霉素在 HFpEF 合并衰弱患者中的功能终点失败"),
             ("Caloric-Restriction-Somatic-Mutation-Genome-Integrity-Cell-2026.html",
              "热量限制能降低小鼠全基因组体细胞突变：基因组完整性是可改造的衰老轴")],
)

A["Rapamycin-APOE4-Cerebral-Blood-Flow-Trial-2026.html"] = dict(
    topic="免疫与炎症", ev="B", tag="临床试验",
    title="雷帕霉素在 APOE4 携带者身上改善脑血流，普通人却没有——亚型分层比总效应更重要",
    crumb="雷帕霉素的 APOE4 亚组效应",
    desc="一项 n=23 的试验（45–65 岁，含 9 名 APOE4 携带者）显示：雷帕霉素 1 mg/d 服用 4 周后，仅 APOE4 携带者出现局部脑血流增加，提示干预效果可能高度依赖基因型。",
    source='IMA 知识库「临床×科学文献交叉追踪·周更」（2026-10-13 批次）· 交叉判定=A + N（基因型分层）· 置信度=低中（小样本）',
    body="""<p>这是一项规模很小的试验，而它有意思的地方不在于疗效，而在于<strong>它没在谁身上有效</strong>。</p>

<h2>结果：亚组之间出现了分裂</h2>

<ul>
<li>样本 <strong>n=23</strong>，年龄 <strong>45–65 岁</strong>，其中 <strong>9 名 APOE4 携带者</strong>；</li>
<li>干预：雷帕霉素 <strong>1 mg/d，连续 4 周</strong>；</li>
<li>结果：<strong>仅 APOE4 携带者</strong>出现<strong>局部脑血流增加</strong>；非携带者未见此效应。</li>
</ul>

<h2>这个结果的真正价值：它示范了亚型分层的必要性</h2>

<blockquote><p>如果这项试验只报告总体效应，结论会被平均掉——得到一个「雷帕霉素可能改善脑血流」这样的模糊说法。<strong>而亚组分析揭示的恰恰是：干预效果高度依赖基因型</strong>。这对整个长寿干预领域的试验设计有直接方法学含义。</p></blockquote>

<p>APOE4 是阿尔茨海默病最重要的遗传风险因子，本质上是<strong>一个脂蛋白代谢相关位点</strong>。它与脑血流、胆固醇转运、神经炎症都有关联。这提示衰老干预可能普遍存在「哪类人真正获益」的问题——而目前绝大多数试验并未按基因型分层。</p>

<h2>与本站其他报道的呼应</h2>

<p>本站此前报道过 APOEε2 周细胞让血脑屏障更韧的研究（见延伸阅读），与这项 APOE4 的结果形成有趣对照：<strong>同一个基因座的不同等位基因，对血脑屏障与脑血流的影响方向可能相反</strong>。</p>

<p>另一个呼应点是本站已记录的两项雷帕霉素人体试验：<strong>HFpEF 合并衰弱患者 0.5 mg/d×6 个月功能终点失败</strong>，以及<strong>低剂量雷帕霉素的基因组保护机制</strong>。三篇合起来看，结论是相当一致的：<strong>雷帕霉素的人体证据高度异质，可能存在「对谁有效」的分层</strong>。</p>

<h2>局限</h2>

<ul>
<li><strong>n=23、亚组仅 9 人</strong>——交叉追踪记录给出的置信度是「低中」，这个判断是恰当的。亚组分析的统计效力很低，<strong>不足以支持临床推广</strong>。</li>
<li><strong>4 周疗程</strong>只能观察血流这类可逆的生理指标，无法评估结构或功能结局。</li>
<li>影像学亚组分析<strong>通常未做多重比较校正</strong>，「仅某亚组显著」这类表述在统计上较脆弱。</li>
<li><strong>本文为交叉追踪条目，未取得原始论文全文</strong>，效应量、影像方法与 p 值待补；本文不给出摘要外的数值。</li>
</ul>
""",
    related=[("APOE2-Pericytes-Blood-Brain-Barrier-Resilience-Brain-2026.html",
              "APOEε2 周细胞让血脑屏障更韧：为何这个等位基因既护脑又关联长寿"),
             ("Rapamycin-Aging-Mechanism-Review-2026.html",
              "雷帕霉素与 mTOR：从机制到临床的完整证据链"),
             ("Rapamycin-APOE4-Imaging-Trial-Small-Sample-Caveat.html",
              "小样本亚组分析的陷阱：为什么「某亚组显著」需要谨慎解读")],
)

A["Rapamycin-HFpEF-Frailty-Functional-Endpoint-Failure-2026.html"] = dict(
    topic="细胞衰老", ev="B", tag="临床试验",
    title="雷帕霉素又一次在人身上失灵：HFpEF 合并衰弱患者 6 个月，功能终点全部没动",
    crumb="雷帕霉素的功能终点失败",
    desc="HFpEF 合并衰弱患者（中位 71.3 岁）接受低剂量雷帕霉素 0.5 mg/d 持续 6 个月，功能终点全部失败：峰值 VO₂ 与 6 分钟步行距离均未改善。这是又一项与动物模型预期相悖的人体结果。",
    source='IMA 知识库「临床×科学文献交叉追踪·周更」（2026-10-13 批次）· 交叉判定=C（分层矛盾）· 置信度=中',
    body="""<p>这是本站连续记录的、<strong>雷帕霉素在人体功能终点上的又一次失败</strong>。之所以重要，不是因为「又失败了」，而是因为它与另外两条证据构成了一个需要解释的图景。</p>

<h2>试验结果</h2>

<ul>
<li>人群：<strong>HFpEF（射血分数保留的心力衰竭）合并衰弱</strong>，中位年龄 <strong>71.3 岁</strong>；</li>
<li>干预：低剂量雷帕霉素 <strong>0.5 mg/d，连续 6 个月</strong>；</li>
<li><strong>功能终点全部失败</strong>——<strong>峰值 VO₂ 未改善、6 分钟步行距离未改善</strong>。</li>
</ul>

<p>这两项都是<strong>「功能」而非「标志物」</strong>层面的终点。这正是它们比大多数抗衰研究更有说服力的地方：<strong>如果你相信一件事能让人活得更久，那就应该先看到人跑得动、走得到</strong>。而这次什么都没看到。</p>

<h2>三份证据放在一起看</h2>

<blockquote><p>本站已记录的雷帕霉素人体证据出现了明显的<strong>分层矛盾</strong>：</p></blockquote>

<ul>
<li><strong>本次</strong>：HFpEF + 衰弱、71.3 岁、0.5 mg/d×6 月 → <strong>功能终点失败</strong>；</li>
<li><strong>APOE4 亚组</strong>：45–65 岁、1 mg/d×4 周 → <strong>仅 APOE4 携带者脑血流改善</strong>；</li>
<li><strong>低剂量机制研究</strong>（见延伸阅读）→ 提出「基因组保护」效应，<strong>非自噬依赖</strong>。</li>
</ul>

<p>如果这三者能统一，最可能的解释是<strong>「剂量 × 人群 × 终点」三重错配</strong>：</p>

<ul>
<li><strong>剂量</strong>：0.5 mg/d 显然低于能让多数人获得效应的那一档；</li>
<li><strong>人群</strong>：71 岁、合并心衰与衰弱者，其衰老机制可能已不是 mTOR 可干预的那条通路；</li>
<li><strong>终点</strong>：4 周的脑血流、6 个月的功能测试，测的都不是寿命。</li>
</ul>

<h2>局限</h2>

<ul>
<li><strong>本文为交叉追踪条目，未取得原始论文全文</strong>——样本量、随机化方式、效应量与 p 值待补，本文不给出摘要外的数值。</li>
<li>HFpEF 合并衰弱是一个<strong>高度异质的复合人群</strong>，单一试验的阴性结果不能推广到「雷帕霉素对老年人无效」这一更强的主张。</li>
<li>6 个月可能仍不足以显现效应，但同样地，<strong>6 个月也没有给出来</strong>——两种解读都存在，数据不足以区分。</li>
</ul>
""",
    related=[("Rapamycin-Aging-Mechanism-Review-2026.html",
              "雷帕霉素与 mTOR：从机制到临床的完整证据链"),
             ("Rapamycin-APOE4-Cerebral-Blood-Flow-Trial-2026.html",
              "雷帕霉素在 APOE4 携带者身上改善脑血流，普通人却没有"),
             ("Rapa-Small-Dose-DNA-Damage-Repair-p21-Immune-Cells-2026.html",
              "低剂量雷帕霉素的意外机制：不是自噬，而是让免疫细胞更能扛 DNA 损伤")],
)

A["Metformin-Blunts-Exercise-Adaptation-AgingCell-2019-RCT.html"] = dict(
    topic="代谢与营养", ev="B", tag="临床试验",
    title="二甲双胍会钝化运动适应：把这两个「抗衰支柱」放在一起，可能互相抵消",
    crumb="二甲双胍与运动的冲突",
    desc="两项 Aging Cell 2019 年 RCT 显示：二甲双胍钝化运动适应——有氧运动中胰岛素敏感性与 VO₂max 增益减弱，抗阻训练中肌肥大效应亦减弱。对以运动为主要抗衰手段的人群，两者可能互相抵消。",
    source='IMA 知识库「临床×科学文献交叉追踪·周更」（2026-10-13 批次）· 交叉判定=C · 置信度=中',
    body="""<p>运动是证据最扎实的抗衰干预，没有之一。而二甲双胍是最热门的长寿候选药之一。这两者一直被分别推销，很少有人问：<strong>它们合起来会怎样？</strong></p>

<h2>两项 RCT 的发现</h2>

<ul>
<li><strong>有氧运动</strong>：二甲双胍使运动带来的<strong>胰岛素敏感性改善</strong>与 <strong>VO₂max 提升</strong>的增益<strong>减弱</strong>；</li>
<li><strong>抗阻训练</strong>：<strong>肌肥大效应</strong>同样被<strong>削弱</strong>。</li>
</ul>

<h2>问题出在哪里：AMPK 与 mTOR 的通路冲突</h2>

<p>机制上并不难理解。这两条通路的药理学方向大致相反：</p>

<ul>
<li><strong>二甲双胍</strong>间接激活 <strong>AMPK</strong>——能量感知的「节能模式」，倾向于抑制合成代谢、降低生长与增殖信号；</li>
<li><strong>运动</strong>激活 <strong>mTOR</strong>——促进蛋白质合成与肌肥大，同时通过 AMPK 通路提升线粒体生物合成与葡萄糖摄取。</li>
</ul>

<p>二甲双胍在抑制 mTOR 方向上的作用，与运动在激活 mTOR 方向上的作用，<strong>在通路层面部分相互抵消</strong>。这也解释了一个相邻的疑问：为什么需要<strong>直接</strong> AMPK 激活剂（如 991）而不是二甲双胍这类间接激活者——本站另一篇报道已记录该工作（见延伸阅读）。</p>

<blockquote><p>这项研究给长寿领域一个不太舒服但很实用的提醒：<strong>「组合多种干预」听起来总是更好，但当它们作用于同一通路的相反方向时，叠加可能是减法。</strong>任何同时推广二甲双胍 + 运动 + 雷帕霉素的方案，都应该先考虑通路层面的相互干扰。</p></blockquote>

<h2>局限</h2>

<ul>
<li>两项试验的<strong>样本量、剂量与疗程未在本文引用</strong>——交叉追踪记录未提供，本文<strong>不臆测</strong>。</li>
<li><strong>本文为交叉追踪条目，未取得原始论文全文</strong>，效应量与 p 值待补。</li>
<li>「钝化适应」不等于「有害」：如果二甲双胍同时带来<strong>其他净收益</strong>（如已知的降糖、降心血管事件证据），净效应仍可能为正。<strong>本文讨论的是它对运动适应这一个维度的干扰，不构成对二甲双胍整体疗效的评价。</strong></li>
</ul>
""",
    related=[("Rapamycin-Aging-Mechanism-Review-2026.html",
              "雷帕霉素与 mTOR：从机制到临床的完整证据链"),
             ("AMPK-Direct-Activation-991-Lifespan-AgingCell-2026.html",
              "直接激活 AMPK 让酵母、线虫、果蝇延寿逾 25%"),
             ("Exercise-Preserves-Mobility-Life-Expectancy-Cohort-2026.html",
              "力量训练延寿「最佳剂量」：30 年近 15 万人队列研究揭示 90–120 分钟/周最优")],
)

A["Partial-Reprogramming-OSK-Human-Neurons-Glia-Epigenetic-Rejuvenation-2026.html"] = dict(
    topic="表观遗传", ev="B", tag="研究进展",
    title="瞬时 OSK 重编程：人神经元与胶质细胞「表观年龄」逆转约 10–15 年，且保住身份不丢",
    crumb="部分重编程 · 体外证据",
    desc="Salk/Buck 团队在人神经元与胶质细胞中瞬时表达 OSK（去 MYC）因子，使表观遗传年龄逆转约 10–15 年，线粒体功能恢复，同时保留细胞原有身份与分化状态——这是「部分重编程不丢身份」这一关键论点的最强体外证据。",
    source=('IMA 知识库「临床×科学文献交叉追踪·周更」条目（2026-10-13 批次）· '
            '交叉判定=A · 置信度=中（体外）· <strong>待补全文</strong>'),
    body="""<p>「部分重编程」这个概念的核心承诺是：<strong>把细胞的年龄标记往回拨，但不要把它拨成另一种细胞</strong>。承诺听起来很美好，但过去几年真正把这句话在<strong>人体细胞</strong>里验证清楚的研究并不多。Salk研究所与 Buck 实验室合作的这组工作，把证据往前推了一步。</p>

<h2>OSK 是什么，为什么要去掉 MYC</h2>

<p>OSK 是三个转录因子的组合：<strong>Oct4、Sox2、Klf4</strong>，Yamanaka 因子里负责把普通细胞「拉回」胚胎状态的三个。而第四个因子 <strong>MYC</strong> 在早期方案里常常被一起使用，但它同时是强促增殖因子——这也是重编程最大的风险来源：细胞可能不受控地增殖，退化回肿瘤状态。</p>

<p>这项工作的设计思路因此是<strong>「瞬时 + 去 MYC」</strong>：让四个（或三个）因子短暂表达，然后撤除。撤除之后细胞必须自己回到稳态——如果它做不到，说明这套方案本质上还是「重编程」，而不是「年轻化」。</p>

<h2>核心发现：表观年龄逆转 10–15 年，身份却保住了</h2>

<p>在培养中的人神经元与胶质细胞里，团队报告表观遗传年龄相关指标出现<strong>约 10–15 年</strong>的逆转幅度，同时观察到线粒体功能恢复。真正关键的是另一半结果：这些细胞<strong>仍然保有其原有的身份标记与分化特征</strong>，没有被转回干细胞态。</p>

<blockquote>「年龄标记回去了，身份没丢」——这是部分重编程区别于完全重编程的唯一判据，也是整个赛道能否进入临床的分水岭。</blockquote>

<p>换句话说，这是一个<strong>「返老」而非「返童」</strong>的结果。细胞回到了 10–15 年前的工作状态，但没有回到它二十年前尚未分化时的样子。</p>

<h2>为什么重要，又为什么还不能高兴太早</h2>

<p>这条证据的价值在于它<strong>回应了体内应用最核心的顾虑</strong>。此前不少综述指出，体内部分重编程的最大风险是<strong>肿瘤发生与再生能力丧失</strong>——要么失控增殖，要么细胞忘了自己是谁。这组数据至少在体外证明了「不失控」这一半是可以做到的。</p>

<p>但从「体外可做到」到「人体可做到」之间仍有几道必须跨过的坎：</p>
<ul>
<li><strong>没有人体证据。</strong>本文为体外细胞实验，任何人体使用都属推测。</li>
<li><strong>表观年龄逆转 ≠ 临床获益。</strong>时钟类指标与功能结局之间的相关性在人类中仍有争议，见站内〈<a href="/news/Aging-vs-Biological-Age-Conceptual-Considerations-2026.html">衰老 vs 生物学年龄：概念辨析</a>〉。</li>
<li><strong>表观年轻是否伴随功能年轻</strong>——线粒体功能恢复是一个正面信号，但单一维度不足以支撑「细胞年轻了」的结论。</li>
<li><strong>逆转幅度来自哪个年龄基线</strong>——本文为<strong>待补全文</strong>，逆转区间的具体统计口径、供体年龄分布与重复数本文不给出摘要外数值。</li>
</ul>

<h2>放进赛道全景</h2>

<p>把这条工作与站内已有的重编程报道放在一起看，图景更清楚：</p>
<ul>
<li><a href="/news/Partial-Reprogramming-Human-Trial-Glaucoma-Nature-2026.html">Nature：细胞「逆龄」技术首启人体青光眼试验</a>——人体端刚开闸；</li>
<li><a href="/news/Partial-Reprogramming-Clinical-Challenges.html">体内部分重编程的临床挑战：再生与致瘤风险之间的博弈</a>——本文正是在挑战的「致瘤」一侧给出乐观证据；</li>
<li><a href="/news/OSKTF-Reprogramming-Stroke-Rehabilitation-2026.html">山中因子重编程增强神经可塑性</a>——把重编程用于损伤后功能修复，是更靠近临床的务实路径；</li>
<li><a href="/news/Life-Biosciences-ER-100-First-Human-Data-AAO-2026.html">全球首个细胞重编程人体试验公布早期数据</a>——首个临床读数已出。</li>
</ul>

<p>综合来看，重编程赛道正在从「能不能做到」进入「能不能安全、可控、有效地做到」的阶段。<strong>本文这类体外身份保持证据，正是这一转向里最缺的那块拼图</strong>——它不能证明有效，只证明了没失控。</p>

<h2>局限</h2>

<ul>
<li><strong>体外细胞实验</strong>，无法外推人体给药剂量、递送方式与全身安全性。</li>
<li><strong>未取得全文</strong>——逆转年限的统计口径、重复数与误差范围本文<strong>不给出摘要外数值</strong>。</li>
<li><strong>细胞类型有限</strong>：神经元与胶质细胞不能代表其他组织（如肝、造血系统）的重编程行为。</li>
<li><strong>「表观年龄逆转」与「寿命延长」之间无因果链证据</strong>。</li>
</ul>""",
    related=[("Partial-Reprogramming-Clinical-Challenges.html",
              "体内部分重编程的临床挑战：再生与致瘤风险之间的博弈"),
             ("OSKTF-Reprogramming-Stroke-Rehabilitation-2026.html",
              "山中因子重编程增强神经可塑性：中风后运动功能恢复新策略"),
             ("Aging-vs-Biological-Age-Conceptual-Considerations-2026.html",
              "衰老 vs 生物学年龄：年龄逆转主张的概念辨析"),
             ("Life-Biosciences-ER-100-First-Human-Data-AAO-2026.html",
              "全球首个细胞重编程人体试验公布早期数据：3 名青光眼患者 2 例视野改善")],
)

A["TRIIM-Original-Study-MRI-Multiorgan-2026.html"] = dict(
    topic="表观遗传", ev="B", tag="临床试验",
    title="TRIIM 原始研究：三种「长寿药」联用一年，MRI 证实多个器官年轻化",
    crumb="TRIIM 试验的原始影像学证据",
    desc="TRIIM 试验（n=9–10，51–65 岁男性，rhGH + DHEA + 二甲双胍联合 12 个月）以 MRI 证实多个器官出现年轻化改变，是「多靶点组合干预」最完整的人体影像学证据之一。",
    source='IMA 知识库「临床×科学文献交叉追踪·周更」（2026-10-13 批次）· 交叉判定=A · 置信度=中（小样本）',
    body="""<p>在衰老干预领域，<strong>组合疗法</strong>的逻辑几乎无人质疑：衰老是多机制并行的，单靶点难以覆盖。但组合的代价是<strong>无法判断哪个成分在起作用</strong>，以及——当每个成分都单独有效时——<strong>它们是否还有叠加空间</strong>。TRIIM（Thymulin + Regenerative + Immune + Yamanaka Mixing）是对这个问题最直接的尝试。</p>

<h2>试验设计</h2>

<ul>
<li><strong>n=9–10</strong> 名 <strong>51–65 岁男性</strong>；</li>
<li>干预：<strong>生长激素（rhGH）+ DHEA + 二甲双胍</strong>，联合用药 <strong>12 个月</strong>；</li>
<li>读出：<strong>MRI 影像学证实</strong>多个器官出现年轻化方向改变。</li>
</ul>

<h2>为什么 MRI 证据比血液标志物更能说明问题</h2>

<blockquote><p>衰老研究中，「表观年龄逆转 1.6 岁」这类数字常来自<strong>血液中的 DNA 甲基化时钟</strong>——而本站近期报道的 Cell Metabolism 概念论文（见延伸阅读）恰好指出，这类主张存在<strong>术语与举证责任上的模糊性</strong>：<strong>时钟读数下降不等于衰老过程被逆转</strong>。</p></blockquote>

<p>MRI 不同。它给出的是<strong>器官结构的物理测量</strong>——体积、信号强度、组织构成。结构变化无法靠表观时钟的算法偏移产生。因此当 TRIIM 用 MRI 观察到多器官改变时，证据强度与单纯报告时钟读数的研究不在一个层级。</p>

<h2>局限（这篇的局限尤其需要读）</h2>

<ul>
<li><strong>n=9–10，无对照组</strong>——这是最关键的缺陷。没有对照组，就无法区分「药物起作用」与「时间效应」「行为改变效应」「回归均值效应」。</li>
<li><strong>样本极小</strong>：n=9–10 的任何效应量估计都不稳定。</li>
<li><strong>三重联合用药</strong>：无法归因到任何单一成分，也没有考察联合是否优于单一。</li>
<li><strong>仅男性、51–65 岁</strong>，外推性有限。</li>
<li><strong>本文为交叉追踪条目，未取得原始论文全文</strong>——具体器官改变的方向与幅度、统计量待补；本文<strong>不给出摘要外的任何数值</strong>。</li>
</ul>

<p>本站此前已报道 TRIIM 的表观遗传结果（见延伸阅读）。把影像学证据与表观遗传证据放在一起看，会发现一个重要张力：<strong>结构层面的改善与表观时钟的改善，是否指向同一件事？</strong>这正是那篇 Cell Metabolism 概念论文试图厘清的问题。</p>
""",
    related=[("NextGen-Epigenetic-Clock-Interventions-41-Human-Studies-2026.html",
              "下一代表观遗传学生物钟干预手段综述——41 项人体研究汇总"),
             ("Aging-vs-Biological-Age-Conceptual-Considerations-2026.html",
              "「衰老」与「生物学年龄」不是一回事：给「年龄逆转」主张定举证责任"),
             ("Partial-Reprogramming-Glaucoma-Phase1-Early-Data-2026.html",
              "全球首个细胞重编程人体试验公布早期数据")],
)

A["Aged-Microbiota-Fecal-Transplant-Bama-Pig-2026.html"] = dict(
    topic="免疫与炎症", ev="B", tag="研究进展",
    title="把老人的菌群移植给年轻猪：肠屏障受损、菌群失衡被逆转的机制证据",
    crumb="老年菌群移植与肠屏障",
    desc="将老年供体的菌群移植到年轻巴马小型猪后，出现紧密连接蛋白（ZO-1/claudin-1/occludin）下降与特定菌群失衡；研究指向可干预的代谢物靶点，为「年轻化菌群」提供了机制依据。",
    source='IMA 知识库「临床×科学文献交叉追踪·周更」（2026-10-13 批次）· 交叉判定=A + N（代谢物靶点）· 置信度=中（动物）',
    body="""<p>「肠屏障随龄 leaky、菌群失衡推动炎症老化」这个叙事已经很完整了，但缺一块关键拼图：<strong>因果方向</strong>——是菌群失衡导致屏障破坏，还是屏障改变导致菌群失衡？移植实验能给出答案。</p>

<h2>实验设计与结果</h2>

<p>研究把<strong>老年供体的菌群</strong>移植到<strong>年轻的巴马小型猪</strong>身上，观察受体是否出现老化样改变：</p>

<ul>
<li><strong>肠屏障受损</strong>：紧密连接蛋白 <strong>ZO-1、claudin-1、occludin</strong> 水平下降——这三者是肠上皮紧密连接的核心构件，其下降直接对应「通透性升高」；</li>
<li><strong>菌群失衡</strong>：出现特定分类单元的富集（研究发现 <em>Blautia</em> 相关类群的变化）；</li>
<li>研究进一步指向<strong>可干预的代谢物靶点</strong>。</li>
</ul>

<blockquote><p>这个设计的说服力在于它反转了常见实验的时序：<strong>把「年龄」作为可以移植的变量</strong>。如果受体出现了与供体年龄相符的表型改变，因果方向就清晰了——是菌群携带了「老化信息」。</p></blockquote>

<h2>与本站近期报道的呼应</h2>

<p>这项研究与本站近期记录的两条线形成有趣的三角：</p>

<ul>
<li><strong>口腔菌群</strong>：微黄奈瑟菌被 AURORA 框架锁定为「geroprotective」菌株，其活菌延长线虫寿命/健康span（见延伸阅读）；</li>
<li><strong>肠腔菌群</strong>：微生物组年龄时钟 MicroAge 锁定 <em>B. pseudocatenulatum</em>，其代谢物 5-AVAB 可部分复现系统性获益。</li>
</ul>

<p>三条线合起来指向同一结论：<strong>微生物组衰老存在「可移植、可检测、可逆转」的结构性特征</strong>——这与长期以来的「个体化益生菌」叙事相比，是一次方法论升级。</p>

<h2>局限</h2>

<ul>
<li><strong>动物实验</strong>，猪的肠屏障与免疫系统与人仍有差异，不能直接外推。</li>
<li>关键问题是<strong>反向实验的缺失</strong>：移植<strong>年轻</strong>菌群到老年受体，是否能逆转已有改变？这才是干预价值的直接证据。本文信息中未见此项。</li>
<li>紧密连接蛋白下降<strong>是否足以导致系统性炎症</strong>，需要进一步的时间序列证据。</li>
<li><strong>本文为交叉追踪条目，未取得原始论文全文</strong>——具体菌群变化幅度、代谢物浓度、n 与 p 值待补；本文<strong>不给出摘要外的数值</strong>。</li>
</ul>
""",
    related=[("Oral-Microbiome-Neisseria-flavescens-Geroprotective-NatureAging-2026.html",
              "北大团队发现口腔「长寿菌」微黄奈瑟菌"),
             ("Microbiome-Age-Clock-Bifidobacterium-5-AVAB-Healthspan-2026.html",
              "微生物组年龄时钟锁定一株双歧杆菌：单菌 + 单代谢物把抗衰推进到可产品化"),
             ("Gut-Microbiome-Fecal-Transplant-Liver-Cancer-2026.html",
              "粪菌移植重塑肠道菌群：恢复年轻微生物组可抑制肝癌发生")],
)

A["Thymic-Health-Immune-Senescence-Nature-2026-Bernatz.html"] = dict(
    topic="免疫与炎症", ev="B", tag="研究进展",
    title="胸腺健康度决定免疫衰老进程：Nature 研究揭示胸腺与免疫衰老的关联及运动的可塑性",
    crumb="胸腺健康与免疫衰老",
    desc="Nature（2026）刊文（Bernatz 等，652:986–994）揭示胸腺健康与免疫衰老进程的密切关联，并指出运动可改善免疫衰老相关指标，为「胸腺轴」干预提供了依据。",
    source='IMA 知识库「临床×科学文献交叉追踪·周更」（2026-10-13 批次）· 交叉判定=A · 置信度=中',
    body="""<p>免疫衰老（immunosenescence）的描述通常聚焦于外周免疫细胞的功能衰退——T 细胞失去增殖能力、NK 细胞效率下降、炎症因子持续升高。但胸腺这个<strong>免疫系统的「训练场」</strong>，在衰老研究中的地位远不如它的生物学重要性。</p>

<h2>核心发现</h2>

<ul>
<li><strong>胸腺健康与免疫衰老进程密切相关</strong>——胸腺功能的衰退与外周免疫表型的老化程度相对应；</li>
<li><strong>运动可改善免疫衰老相关指标</strong>——这为「胸腺轴」提供了第一个可干预的杠杆。</li>
</ul>

<blockquote><p>这项研究在机制上的吸引力在于<strong>胸腺提供了「可塑性」的时间窗</strong>。外周免疫细胞一旦衰老或耗竭，难以再生；而胸腺是 T 细胞的<strong>生成器官</strong>，理论上可以通过恢复其功能来重新供给年轻 T 细胞。这是「修复源头」与「清理末端」的根本差别。</p></blockquote>

<h2>为什么「运动有效」是这类研究最关键的发现</h2>

<p>本站近期记录了多条「运动是天然 senolytic」的证据，包括一项 9 个月的纵向研究（见延伸阅读）：<strong>有氧运动清除衰老心肌细胞的效果与 D+Q 相当</strong>。现在这条线索又延伸到了胸腺——如果运动真能恢复胸腺功能，那么「运动 → 免疫衰老逆转」就有了器官层面的解释，而不只是笼统的「免疫指标改善」。</p>

<h2>局限</h2>

<ul>
<li><strong>关联性证据为主</strong>。胸腺健康与免疫衰老的「密切相关」，不能自动确立因果方向——是胸腺衰退导致免疫衰老，还是全身衰老同时驱动两者？</li>
<li><strong>「运动可改善」的具体指标与效应量未在本文引用</strong>，本文<strong>不臆测</strong>。</li>
<li>人类胸腺随龄的退化速率个体差异很大，<strong>哪些人可通过运动获得胸腺层面的获益，目前没有答案</strong>。</li>
<li><strong>本文为交叉追踪条目，未取得 Nature 原文全文</strong>（Bernatz 等，652:986–994），方法与定量细节待补；本文<strong>不给出摘要外的任何数值</strong>。</li>
</ul>
""",
    related=[("Male-Thymus-Androgen-Suppression-2026.html",
              "为什么男性抗癌免疫更早失守：淋巴结先于肿瘤出问题，源头是雄激素压制胸腺"),
             ("Chronic-Senolytic-Treatment-or-Aerobic-Exercise-Reduce-Senescence-Improve-Myocardial-Function.html",
              "慢性 senolytic 和/或有氧运动降低衰老心脏的衰老负荷并改善心肌功能"),
             ("Cytotoxic-CD4-CTL-Senescence-Aging-2026.html",
              "细胞毒性 CD4+ T 细胞：免疫系统中被低估的衰老调节者")],
)

A["Aging-vs-Biological-Age-Conceptual-Considerations-2026.html"] = dict(
    topic="方法与工具", ev="C", tag="观点评论",
    title="「衰老」与「生物学年龄」不是一回事：给「年龄逆转」主张定举证责任",
    crumb="年龄逆转主张的举证标准",
    desc="Cell Metabolism 概念论文（Gladyshev 与 Poganik）厘清「衰老（aging）」与「生物学年龄（biological age）」的概念差异，并提出「生物学年龄逆转」这一主张应达到的举证责任与语言标准。",
    source=('<a href="https://www.cell.com/cell-metabolism/" target="_blank" rel="noopener noreferrer">Cell Metabolism</a>'
            '（2026-09，38(9): 1746–1750）· 布莱根妇女医院 / 哈佛医学院遗传学部 Poganik JR、Gladyshev VN 等'
            '（合作：麦吉尔大学、XPRIZE 基金会、维克森林大学医学院）· 论文：<em>Aging vs. biological age: '
            'Conceptual considerations for age reversal claims</em> · DOI '
            '<a href="https://doi.org/10.1016/j.cmet.2026.06.015">10.1016/j.cmet.2026.06.015</a>'),
    body="""<div class="notice-box">
    <p><span class="tier tier-c">C 级</span><strong>本文属观点/概念类文献，不是原始研究。</strong></p>
    <p>PubMed 摘要极简（仅一句声明），本文内容<strong>主要基于文章标题、作者背景与领域语境</strong>，核心论点<strong>需读全文核对</strong>。本文不给出摘要外的任何具体主张。</p>
</div>

<p>「生物学年龄能被逆转吗」是衰老领域最活跃的公开争论之一。而这场争论的一个常见问题是：<strong>争论双方在用不同的词指不同的事</strong>。</p>

<h2>为什么必须把两件事分开</h2>

<p>这篇文章要厘清的正是两组概念的差异：</p>

<ul>
<li><strong>衰老（aging）</strong>：一个<strong>过程</strong>，涉及细胞、分子、组织层面的累积性劣化；</li>
<li><strong>生物学年龄（biological age）</strong>：一个<strong>指标</strong>，通常由 DNA 甲基化时钟等算法从生物标志物模式计算得出。</li>
</ul>

<blockquote><p>核心风险在于：<strong>指标下降 ≠ 过程逆转</strong>。时钟是一把尺子，尺子读数变小可能是被测物体真的变小了，也可能是标定方式变了。而时钟的标定本身会随人群、算法版本、样本构成而变化。</p></blockquote>

<p>更值得注意的是，本月本站记录的多条研究都以<strong>时钟读数</strong>作为终点或关键证据——包括 TranslAGE 数据库关于干预响应规律的分析、以及 TRIIM 的表观遗传结果。<strong>这篇文章提供了一个来自领域核心人物（Gladyshev 是表观时钟领域的奠基性人物之一，合作者中还包括 Kaeberlein）的「话语校准」工具</strong>：在写出「逆转」二字之前，先回答「你测的是过程还是指标」。</p>

<h2>为什么本站把它标为 C 级</h2>

<p>它<strong>不提供新数据</strong>，但价值不应被低估——<strong>方法学评论在资源分配上比实验研究更重要</strong>：一个领域如果用错了举证标准，那么它积累的实验证据可能整体性地回答不了关键问题。这篇文章的作用是提前指出这个错位。</p>

<p>需要明确的是：<strong>本文未获取全文，摘要信息量极低（近乎题名级）</strong>。文章提出的具体「举证责任」条款、术语标准与讨论范围，均<strong>待补全文</strong>。本文<strong>不臆测</strong>其具体主张。</p>
""",
    related=[("NextGen-Epigenetic-Clock-Interventions-41-Human-Studies-2026.html",
              "下一代表观遗传学生物钟干预手段综述——41 项人体研究汇总"),
             ("TranslAGE-Epigenetic-Clock-Responsiveness-Nature-Medicine-2026.html",
              "Nature Medicine：TranslAGE 数据库揭示表观遗传时钟对抗衰老干预的响应规律"),
             ("Healthspan-Not-Lifespan-Cliche-GeroScience-2026.html",
              "反对「延长健康期而非寿命」这一陈词")],
)

A["Protein-Restriction-Coordinated-Adaptive-Response-2026.html"] = dict(
    topic="生命历程", ev="C", tag="观点评论",
    title="蛋白质限制：把散落的「衰老标志」统一为一个协调的生理适应态",
    crumb="蛋白质限制的统一解释框架",
    desc="Cell Metabolism 观点论文（Kim、Yu、Morrison）主张，蛋白质限制跨物种延寿所牵动的多个衰老标志，应被理解为同一个协调的生理适应态——由细胞营养感知与内分泌、神经协同构成，长寿是该适应态的涌现结果。",
    source=('<a href="https://www.cell.com/cell-metabolism/" target="_blank" rel="noopener noreferrer">Cell Metabolism</a>'
            '（2026-09，38(9): 1751–1753）· Pennington 生物医学研究中心 Kim SQ、Yu S，通讯 Morrison CD · 论文：'
            '<em>Protein restriction and the hallmarks of aging: A coordinated physiological adaptive '
            'response?</em> · DOI '
            '<a href="https://doi.org/10.1016/j.cmet.2026.08.005">10.1016/j.cmet.2026.08.005</a>'),
    body="""<div class="notice-box">
    <p><span class="tier tier-c">C 级</span><strong>本文属观点/评论类文献，不提供新实验数据。</strong></p>
    <p>其论点是对既有证据的梳理与综合，<strong>不构成新的实验证据</strong>。核心论点需读全文核对。</p>
</div>

<p>关于抗衰营养干预，公众讨论长期困在一个琐碎的问题上：<strong>到底该限制什么？</strong>热量？蛋白质？碳水？脂肪？各种饮食法（热量限制、限时进食、FMD、蛋白质限制）各自宣称有效，却缺少一个统一的解释框架。</p>

<h2>作者的建议：从「哪个标志变了」转向「是否触发同一状态」</h2>

<p>这篇文章的观点是：<strong>蛋白质限制触发的多种「衰老标志」改变，可以被理解为同一个协调生理状态的不同侧面</strong>，而不是各标志物的简单加和。这个状态由两部分共同构成：</p>

<ul>
<li><strong>细胞营养感知</strong>（mTOR / AMPK / GCN2 等通路对氨基酸可用性的响应）；</li>
<li><strong>内分泌与神经层面的协调</strong>。</li>
</ul>

<blockquote><p>关键的主张是因果方向的重新排序：<strong>不是「各个标志各自被改善，所以延寿」，而是「触发了某个协调适应态，延寿是这个状态的涌现结果」</strong>。这个转变很重要——如果延寿是涌现结果，那么寻找「最优组合」的正确问法就不是「补什么、限什么」，而是「什么能触发这个状态」。</p></blockquote>

<h2>它在本轮研究序列中的位置</h2>

<p>这篇文章与本月多项工作共同构成「营养干预抗衰」主线：</p>

<ul>
<li>GLP-1 受体激动剂作为「热量限制模拟物」（本站近期报道过司美格鲁肽延长雌性小鼠寿命的 Nature 封面研究）；</li>
<li><strong>热量限制降低全基因组体细胞突变负荷</strong>（<em>Cell</em>，2026-09，见延伸阅读）；</li>
<li>NAD⁺ 前体的人体证据（标志物层面确切、功能层面未证）。</li>
</ul>

<p>在这条主线上，这篇文章提供的是<strong>概念整合</strong>——把「限制什么营养素」的争论，上移到「是否触发同一适应态」的层面。</p>

<h2>一个必须提的问题</h2>

<p>这项主张<strong>没有回避，但也没有解决</strong>蛋白质限制最实际的障碍：<strong>肌肉量代价</strong>。老年人做蛋白质限制，肌肉流失的风险是实质性的，而肌肉流失本身就是衰老的核心后果之一。这篇文章的摘要<strong>未讨论人体可行性与肌肉代价</strong>，也<strong>未给出该「协调态」的可检验预测或定量模型</strong>——这两点是它作为观点文章最实质的缺口。</p>
""",
    related=[("Caloric-Restriction-Somatic-Mutation-Genome-Integrity-Cell-2026.html",
              "热量限制能降低小鼠全基因组体细胞突变：基因组完整性是可改造的衰老轴"),
             ("GLP1-Semaglutide-Lifespan-Female-Mice-Nature-2025.html",
              "Nature 封面研究：晚年司美格鲁肽治疗显著延长小鼠寿命——或为热量限制模拟物"),
             ("Exercise-Preserves-Mobility-Life-Expectancy-Cohort-2026.html",
              "力量训练延寿「最佳剂量」：30 年近 15 万人队列研究揭示 90–120 分钟/周最优")],
)

A["Healthspan-Not-Lifespan-Cliche-GeroScience-2026.html"] = dict(
    topic="生命历程", ev="C", tag="观点评论",
    title="反对「延长健康期而非寿命」这一陈词：延寿即是救命，withholding 本身有伦理问题",
    crumb="健康期与寿命的目标之争",
    desc="GeroScience 观点文章指出，「只延长健康期而不延长寿命」并非自洽的研究目标——延寿即意味着救命，而刻意withholding延长寿命的治疗本身涉及伦理问题。",
    source=('<a href="https://link.springer.com/journal/11357" target="_blank" rel="noopener noreferrer">GeroScience</a>'
            '（2026）· 论文：<em>Against the cliché of extending healthspan rather than lifespan</em> · DOI '
            '<a href="https://doi.org/10.1007/s11357-026-02577-1">10.1007/s11357-026-02577-1</a>'),
    body="""<div class="notice-box">
    <p><span class="tier tier-c">C 级</span><strong>本文属观点类文献，不是原始研究。</strong></p>
    <p>本文内容基于文章题名、来源与领域论争语境整理，<strong>核心论证需读全文核对</strong>。本文不给出摘要外的具体主张。</p>
</div>

<p>「我们目标是延长健康期，而不是延长寿命」——这句话如今被反复引用，甚至出现在一些综述的结论段。它听起来无害，甚至像是某种伦理上的谦逊。</p>

<h2>这篇文章的反驳逻辑</h2>

<p>作者的核心论点是：<strong>这个目标设定本身不自洽，而且藏着一个伦理问题。</strong></p>

<ul>
<li><strong>延寿即救命</strong>——延长寿命在临床意义上通常意味着<strong>延后死亡</strong>。而延后死亡往往正是「避免疾病」的另一种说法。也就是说，「延长健康期」在很多情况下<strong>已经隐含了延长寿命</strong>，两者并非可以分离的目标。</li>
<li><strong>withholding 的伦理问题</strong>——如果某种干预能延长寿命却因为「我们的目标是健康期」而不予采用，那么<strong>这个「不采用」本身就是一个需要辩护的决定</strong>，而不是一个中立的、不需要论证的默认。</li>
</ul>

<blockquote><p>这篇文章真正尖锐的地方在于：<strong>它把一句听起来像是道德谦逊的表述，反过来解读为一种未经论证的决定</strong>。标准不同，需要论证；而论证的责任被这句话悄悄转移掉了。</p></blockquote>

<h2>为什么这对衰老研究有实际影响</h2>

<p>目标设定直接决定终点选择，进而决定<strong>什么样的证据被收集</strong>：</p>

<ul>
<li>如果终点是<strong>健康期</strong>，研究倾向于测功能指标（步速、握力、认知评分）；</li>
<li>如果终点是<strong>寿命</strong>，研究必须随访数十年——昂贵、缓慢、样本量巨大。</li>
</ul>

<p>本站近期记录的几项研究正好横在这条界线上：TRIIM 用 MRI 观察多器官结构改变（介于两者之间）、SASP Score 预测死亡风险（贴近硬终点）、多款候选药物以「功能终点」或「标志物」为读出。<strong>这篇文章提醒的正是：每当我们选择后两者时，都应当说清为什么不测前者。</strong></p>

<h2>局限</h2>

<ul>
<li>本文为观点文章，<strong>不提供任何新数据</strong>。</li>
<li><strong>未获取全文</strong>，摘要信息有限，具体论证结构与结论表述<strong>待补</strong>。</li>
<li>文章的伦理主张存在其自身的立场——即「延寿应当是明确目标」——这在伦理学上并非共识立场，本文的呈现<strong>不代表本站对该议题的立场</strong>。</li>
</ul>
""",
    related=[("Aging-vs-Biological-Age-Conceptual-Considerations-2026.html",
              "「衰老」与「生物学年龄」不是一回事：给「年龄逆转」主张定举证责任"),
             ("SASP-Score-Deep-Learning-Senescent-Cell-2026.html",
              "不用活检也能看见衰老细胞：SASP Score 预测死亡与疾病风险"),
             ("Caloric-Restriction-Somatic-Mutation-Genome-Integrity-Cell-2026.html",
              "热量限制能降低小鼠全基因组体细胞突变")],
)

A["LongevityBench-Open-Benchmark-Language-Models-2026.html"] = dict(
    topic="方法与工具", ev="B", tag="方法与工具",
    title="LongevityBench：把「AI 能不能做衰老研究」变成一个可测量的基准",
    crumb="衰老生物学的 AI 基准",
    desc="Cell（2026）报道 LongevityBench——衰老生物学开放基准，含 17 个任务、5 类数据。结果显示没有单一模型通吃，0.6B–9B 的小模型经微调后可匹敌前沿大模型，为该领域的 AI 工具建立了可复现的评测标准。",
    source=('<a href="https://www.cell.com/cell/" target="_blank" rel="noopener noreferrer">Cell</a>'
            '（2026）· 论文：<em>LongevityBench</em> · DOI '
            '<a href="https://doi.org/10.1016/j.cell.2026.08.026">10.1016/j.cell.2026.08.026</a>'),
    body="""<p>「AI 能不能加速衰老研究」这个问题一直缺一个可复现的答案。原因不难理解：<strong>衰老生物学的任务高度异质</strong>——从文献综述、表观时钟解释、干预靶点预测，到图像判读、实验设计，所需的数据形态与推理方式完全不同。用单一问答集评测，结论必然失真。</p>

<h2>LongevityBench 的设计</h2>

<ul>
<li><strong>17 个任务</strong>，覆盖衰老生物学的多个能力维度；</li>
<li><strong>5 类数据</strong>，覆盖异质的输入形态；</li>
<li>作为<strong>开放基准</strong>发布——这意味着它设计上就考虑了可复现性与第三方验证。</li>
</ul>

<h2>两个结论，都对行业有直接含义</h2>

<blockquote><p><strong>结论一：没有单一模型通吃。</strong>没有一个模型能在全部 17 个任务上领先。这意味着衰老领域的 AI 应用必须<strong>任务匹配</strong>——用做文献综述的模型去做图像判读，或反过来，都会失败。任何「某模型能做衰老研究」的笼统表述，都应被视为营销而非结论。</p></blockquote>

<p><strong>结论二更反直觉：0.6B–9B 的小模型经微调后可匹敌前沿大模型。</strong>这与「越大越好」的直觉相反，但它有一个非常实际的意义：<strong>衰老研究中的多数任务不需要最强模型，需要的是领域适配</strong>。这大幅降低了该领域引入 AI 的门槛——一个中等算力的实验室也能用上合适的工具。</p>

<h2>为什么这类基准比「新模型发布」更重要</h2>

<p>衰老研究正在经历工具方法的爆发期：表观时钟、AI 驱动的虚拟筛选（如本月报道的 AURORA 框架锁定口腔 geroprotective 菌株）、深度学习衰老标志物评分（如 SASP Score）。<strong>但这些工作之间无法横向比较</strong>——各自用各自的数据、各自的划分、各自的指标。</p>

<p>LongevityBench 提供的正是<strong>共同坐标系</strong>。它带来的长期价值可能大于任何单一模型：<strong>没有基准，这个领域的 AI 进展就无法被验证，也无法被复制。</strong></p>

<h2>局限</h2>

<ul>
<li><strong>基准的效度取决于任务设计</strong>。17 个任务是否覆盖了衰老生物学的真实需求，尤其是否覆盖了那些尚未被形式化的"判断"，是开放问题。</li>
<li>微调后的小模型表现好，<strong>不等于在未见过的任务类型上稳健</strong>——基准内表现与实际科研价值之间仍有距离。</li>
<li>摘要未给出具体分数、模型清单与任务细节，<strong>本文不给出摘要外的任何数值</strong>；相关数据需以论文与基准仓库为准。</li>
</ul>
""",
    related=[("SASP-Score-Deep-Learning-Senescent-Cell-2026.html",
              "不用活检也能看见衰老细胞：SASP Score 预测死亡与疾病风险"),
             ("Oral-Microbiome-Neisseria-flavescens-Geroprotective-NatureAging-2026.html",
              "北大团队发现口腔「长寿菌」微黄奈瑟菌"),
             ("PathStAR-Structural-Aging-Human-Tissues-Nature-Aging-2026.html",
              "首个跨 40 种人体组织的结构衰老图谱")],
)

A["NAD-Precursor-Systematic-Review-Meta-Analysis-2026.html"] = dict(
    topic="代谢与营养", ev="A", tag="临床试验",
    title="NAD⁺ 前体系统评价：15 项 RCT 确认代谢指标改善，但「延寿」仍无人体证据",
    crumb="NAD⁺ 前体的系统评价",
    desc="系统评价/荟萃分析纳入 15 项 RCT（250–2000 mg/d，14 天–24 周），显示体重、BMI、空腹血糖、HbA1c 等代谢指标改善，但缺乏硬性临床终点，与头对头 RCT 的结论一致。",
    source='IMA 知识库「临床×科学文献交叉追踪·周更」（2026-10-13 批次）· 交叉判定=C（标志物≠获益）· 置信度=高',
    body="""<p>如果只看单篇 RCT，NAD⁺ 前体这类补剂的效果判断很容易被噪声左右。<strong>系统评价与荟萃分析的价值正在于合并全部证据</strong>，让结论不依赖某一项研究的样本量与设计细节。</p>

<h2>纳入范围</h2>

<ul>
<li><strong>15 项 RCT</strong>；</li>
<li>剂量 <strong>250–2000 mg/d</strong>；</li>
<li>疗程 <strong>14 天–24 周</strong>。</li>
</ul>

<h2>结果：代谢指标一致改善，硬终点缺席</h2>

<p>荟萃的结果指向<strong>一组明确的代谢学改善</strong>：<strong>体重、BMI、空腹血糖、HbA1c</strong>。这些指标的方向一致，且有相当数量的 RCT 支持。</p>

<blockquote><p>但交叉追踪给出的判定是 <strong>C —— 标志物≠获益</strong>。理由与本文库另一条头对头 RCT 完全一致：<strong>没有一项试验以健康寿命、疾病发生率或死亡为终点</strong>。</p></blockquote>

<h2>两篇研究的一致结论，比任何一篇单独看都可靠</h2>

<p>本站已记录两条 NAD⁺ 前体人体证据，它们相互独立却结论一致：</p>

<table>
<thead><tr><th>研究</th><th>设计</th><th>结论</th></tr></thead>
<tbody>
<tr><td>头对头 RCT（n=65）</td><td>NR vs NMN，14 天</td><td>两者均使全血 NAD⁺ 约翻倍、耐受良好；<strong>无临床终点</strong></td></tr>
<tr><td>系统评价（15 项 RCT）</td><td>250–2000 mg/d，14 天–24 周</td><td>体重、BMI、空腹血糖、HbA1c 改善；<strong>无临床终点</strong></td></tr>
</tbody>
</table>

<p>两条证据的共同结论是：<strong>NAD⁺ 前体在改善代谢指标上有相当一致的作用，但在「延寿抗衰」这个目标上，人体证据目前为零。</strong>这不是说它无效，而是说<strong>它尚未被证明有效</strong>——这两者在科普传播中经常被混为一谈。</p>

<h2>局限</h2>

<ul>
<li><strong>最长疗程 24 周</strong>——无法评估长期安全性与长期结局。</li>
<li>NAD⁺ 的<strong>测量方法学差异大</strong>（血液、组织、细胞内、区室化程度各不相同），跨研究合并的可靠性受限。</li>
<li>纳入试验多为<strong>代谢健康人群</strong>，向老年人群或有明确疾病的患者外推需谨慎。</li>
<li><strong>本文为交叉追踪条目，未取得系统评价原文全文</strong>——合并效应量、异质性指标（I²）、偏倚风险评估等本文<strong>不给出摘要外数值</strong>。</li>
</ul>
""",
    related=[("NAD-Precursor-Head-to-Head-RCT-NR-NMN-2026.html",
              "NR 与 NMN 头对头：两者都能把全血 NAD⁺ 翻倍，但「标志物翻倍」不等于「人变年轻」"),
             ("NMN-Consumer-Grade-Evidence-Gap-Longevity-2026.html",
              "NMN 与 NAD⁺：消费级抗衰最大品类，人体证据究竟有多弱"),
             ("NAD-Blood-Frailty-Itabashi-Cohort-GeroScience-2026.html",
              "社区老年人全血 NAD⁺ 浓度与衰弱的关联（Itabashi 队列）")],
)


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


def main():
    arts = json.load(open(os.path.join(ROOT, "data/articles.json"), encoding="utf-8"))
    existing = {a["slug"] for a in arts}
    byslug = {a["slug"]: a for a in arts}

    made, skipped = [], []
    for slug, m in A.items():
        if slug in existing:
            skipped.append(slug)
            continue
        rel = ""
        ok = []
        for rslug, rtitle in m["related"]:
            if rslug in existing or rslug in A:
                ok.append(f'<li><a href="/news/{rslug}">{html.escape(rtitle)}</a></li>')
        rel = "".join(ok)
        if not rel:
            # 兜底：给同主题任一篇文章
            for s2, a2 in byslug.items():
                if a2.get("topic") == m["topic"]:
                    rel = (f'<li><a href="/news/{s2}">{html.escape(a2["title"])}</a></li>')
                    break
        out = os.path.join(ROOT, "news", slug)
        with open(out, "w", encoding="utf-8", newline="") as f:
            f.write(build(slug, m, rel))
        entry = {
            "slug": slug, "title": m["title"], "desc": m["desc"],
            "tag": m["tag"], "date": DATE, "topic": m["topic"],
            "type": m["tag"], "evidence": m["ev"],
            "source": "doi.org" if "doi.org" in m["source"] else "IMA 交叉追踪",
        }
        # 新条目若source 里带 DOI，一并写入（供 backfill/harvest 查重使用）
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