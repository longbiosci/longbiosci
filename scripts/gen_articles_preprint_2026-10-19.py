#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_articles_preprint_2026-10-19.py —— 内容摄入第 16 批（文献层《预印本速递_2026-10-19》）

来源与判定
────────
事实源：文献层《预印本速递_2026-10-19.md》
（file_id dMaxwACLTlaq，实测 **19,505 B**，本地落 .intake/raw/preprint-2026-10-19.md）。
同批另一份《预印本全文级流水线_运行摘要_2026-10-18》（dQpERrkBggNI，6,918 B）
是同一条流水线的运行摘要，**本身不含可成篇条目**，只作链路留痕。

产出侧自述：生物预印本源站（bioRxiv）对本环境返回 **HTTP 403**（Cloudflare IP 级封锁），
**两篇主榜卡片均无 PDF 可得**，Europe PMC 对两条 DOI 亦 0 命中。
→ 本批两篇一律 **只依据预印本官方摘要**撰写，任何摘要未给出的定量一律标「待补全文」。

查重结论（四路查重 + 高特异关键词硬核验）
────────────────────────────────────────
harvest.py 对 2 份产出抽出 16 条候选，**全部 confidence=none**。
按硬规则 3（confidence=none 不等于漏收），改用高特异词在 news/ 原文逐条硬核验：

| 条目 | 硬核验词 | 站内命中 | 结论 |
|---|---|---|---|
| 主榜#1 皮肤 senomorphic | `758751` / `H. lupulus` / `G. biloba` | **0 篇** | 真漏收 → 成篇 |
| 主榜#2 α-Klotho 大鼠 | `759802` / `multigenerational` / `phosphorus restriction` / `Wistar-Imamichi` | **0 篇**（站内 7 篇提 Klotho，无一涉及大鼠繁育/磷限制） | 真漏收 → 成篇 |
| 观察哨#1 中年小鼠脑血流 | `758495` / `oxygen extraction` / `capillary flows` | **0 篇** | 漏收但摘要无可引用定量 → **不成篇**（按上游建议并入主题合并稿） |
| 观察哨#2 CD1 自发性 OA | `758449` / `CD1 mice` | **0 篇** | 漏收但属资源/模型类、无定量 → **不成篇**（入档） |

⚠️ 注意 `senomorphic` 一词在站内命中 19 篇 —— 这正是脚本头部警告的「泛词误判」：
它只能证明「同主题文章多」，**不能证明本条已收录**；真正判据是 DOI 尾号与
「H. lupulus / G. biloba」这对具体干预词，两者均 0 命中。

纪律
────
· 只写预印本官方摘要给出的事实，摘要未给出处一律「待补全文」，定量不臆测。
· 证据分级沿用全站 notice-box 口径：A 人体 / B 临床前（动物·体外细胞）/ C 预印本·观点。
  两篇均为**人体原代细胞 / 大鼠模型**的**原始研究**，故定 **B**，
  其「预印本、未经同行评审、全文未获取」的属性由 tag 与正文首段明示，
  不用 C 掩盖「这是原始研究」这一事实。
· 内部链接 slug 全部取自 data/articles.json 且经 news/ 目录实际存在性校验。

为什么必须覆盖 gen_articles.notice
──────────────────────────────────
gen_articles.notice 的最后一段硬编码：
「本站依据 IMA 知识库『五刊监控·深度文献卡片』（SOP §4.2 摘要级）撰写…」
本批来源是 **bioRxiv 预印本官方 API**，与五刊监控无关；照抄会让读者误信
「已过同行评议的期刊卡片」。故 monkey-patch 为预印本口径，来源链条如实写明。
"""
import html
import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATE = "2026-10-19"

# ── 内部链接：均经 news/ 目录实际存在性校验（2026-10-19 实查）──
REL_SKIN = [
    ("SA-beta-gal-Senescence-Biomarker-PNAS-1995.html",
     "把「衰老细胞」染成蓝色的那篇论文：1995 年 SA-β-gal 标志物的建立与沿用"),
    ("Nutritional-Interventions-Cellular-Senescence-Human-Studies-2026.html",
     "营养干预与细胞衰老：人体研究给出了什么"),
    ("CCND1-CDK6-cGAS-STING-SASP-Palbociclib-NatureAging-2026.html",
     "衰老细胞里「反常上调」的 CDK6：palbociclib 把一条老药重定位成抗衰老工具"),
]
REL_KLOTHO = [
    ("Frailty-Assessment-In-Naturally-Aged-GeroScience-2026.html",
     "小鼠衰弱该怎么测：五大工具的系统比较"),
    ("LivAge-An-Online-Aging-Clock-AgingCell-2026.html",
     "LivAge：给小鼠做一个开箱即用的转录组时钟"),
    ("DQ-Senolytic-Multi-Omics-Kidney-Rejuvenation-2026.html",
     "D+Q senolytic 的多组学肾脏「 rejuvenation」图谱"),
]


def notice(ev):
    """预印本口径的证据分级框（覆盖 gen_articles.notice 的五刊监控措辞）"""
    t = {"A": "A 级（同行评议人体研究）",
         "B": "B 级（同行评议临床前研究，主要为动物模型）",
         "C": "C 级（预印本 / 观点评论，非原始研究）"}[ev]
    b = ("<p><strong>本文核心结论来自人体原代细胞与离体皮肤外植体实验，属临床前证据，"
         "不能外推至人体。</strong>「降低衰老负荷」「恢复胶原排列」等表述在离体模型中的意义，"
         "与人体临床结局之间仍有距离。</p>" if ev == "B" else "")
    return (f'<div class="notice-box">\n'
            f'    <p><span class="tier tier-{ev.lower()}">{ev} 级</span>'
            f'<strong>证据分级：{t}</strong></p>\n'
            f'    {b}\n'
            f'    <p><strong>关于本文的文献来源：</strong>本站依据 <strong>bioRxiv 预印本官方 API '
            f'返回的摘要原文</strong>撰写（来源：IMA 知识库《预印本速递》2026-10-19 期）。'
            f'这是一篇<strong>未经同行评审的预印本</strong>，结论可能在正式发表时变更；'
            f'本次<b>未获取全文</b>（源站对本环境返回 HTTP 403，PDF 不可得），'
            f'摘要未给出之处已标注「待补全文」，<strong>未做任何数值推算补全</strong>。</p>\n'
            f'</div>')


def main():
    arts = json.load(open(os.path.join(ROOT, "data/articles.json"), encoding="utf-8"))
    used = {a["slug"] for a in arts}
    # related slug 硬校验：不存在的内部链接一律丢掉，宁缺勿假
    missing = [s for s, _ in REL_SKIN + REL_KLOTHO
               if not os.path.exists(os.path.join(ROOT, "news", s))]
    if missing:
        sys.exit(f"✗ related slug 在 news/ 下不存在：{missing}\n"
                 f"  内部链接必须 ls news/ 实际复制，不能凭记忆写。")

    sys.argv = ["gen_articles.py", ROOT, "/dev/null", DATE]
    _spec = importlib.util.spec_from_file_location(
        "ga", os.path.join(ROOT, "scripts", "gen_articles.py"))
    ga = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(ga)
    ga.notice = notice                      # 换成预印本口径，理由见文件头

    DOI1 = "10.64898/2026.10.13.758751"
    DOI2 = "10.64898/2026.10.17.759802"

    src1 = (f'<em>bioRxiv</em>（cell biology）· 预印本：Targeting skin ageing at the source: '
            f'a novel cellular reprogramming approach using natural extract combinations'
            f' · DOI <a href="https://doi.org/{DOI1}" target="_blank" '
            f'rel="noopener noreferrer">{DOI1}</a>'
            f' · 通讯作者 Lorna W. Harries（英国埃克塞特大学）'
            f' · 来源：IMA 知识库《预印本速递》2026-10-19 期（摘要级，全文未获取）')

    src2 = (f'<em>bioRxiv</em>（physiology）· 预印本：Dietary phosphorus restriction enables '
            f'multigenerational breeding of α-Klotho-deficient rats'
            f' · DOI <a href="https://doi.org/{DOI2}" target="_blank" '
            f'rel="noopener noreferrer">{DOI2}</a>'
            f' · 通讯作者 Yasumitsu Nagao（日本自治医科大学）；作者含 Kuro-o Makoto'
            f' · 来源：IMA 知识库《预印本速递》2026-10-19 期（摘要级，全文未获取）')

    A = {
        "Skin-Ageing-Senomorphic-Natural-Extracts-bioRxiv-2026.html": dict(
            topic="细胞衰老", ev="B", tag="预印本",
            title="啤酒花＋银杏提取物组合让老化皮肤细胞衰老负荷下降 45%，且不诱导增殖",
            crumb="啤酒花＋银杏组合的 senomorphic 效应",
            desc="用 H. lupulus 与 G. biloba 提取物组合处理自然老化的人真皮成纤维细胞，"
                 "衰老表型负荷最高下降 45%，同时不诱导细胞增殖——但只看摘要，读全文前别急着归类。",
            source=src1,
            body="""<p><strong>一句话结论：</strong>把啤酒花（<em>H. lupulus</em>）与银杏（<em>G. biloba</em>）提取物组合起来，经 ERK/AKT–RNA 剪接轴去「调节」而非「清除」衰老细胞，在<strong>自然老化的人原代皮肤细胞</strong>中取得最高 <strong>45%</strong> 的衰老表型改善，且<strong>不诱导细胞增殖</strong>。</p>

<p class="notice-box"><strong>⚠️ 本文为预印本，未经同行评审；本次仅依据官方摘要撰写，全文未获取（源站封锁），结论可能在正式发表时变更。</strong></p>

<h2>这项研究想回答什么</h2>
<p>主流 senolytic 路线是「<strong>清除</strong>衰老细胞」，代价是需要承担清除带来的组织稳态风险。本文换了一条路——<strong>senomorphic（衰老表型调节）</strong>：不杀细胞，而是把衰老细胞的分泌表型与损伤负荷压下去。问题因此变成：<strong>能不能找到一种可外用、可产品化的天然提取物组合，在人体老化皮肤细胞上同时降低衰老负荷与炎症，还不刺激增殖？</strong></p>

<h2>他们怎么做的</h2>
<ul>
<li><strong>细胞层</strong>：自然老化（复制性衰老）的<strong>人原代真皮成纤维细胞</strong>与<strong>人原代角质形成细胞</strong>。</li>
<li><strong>干预</strong>：<em>H. lupulus</em> ＋ <em>G. biloba</em> 提取物组合，摘要称其为「nature-identical synthetic molecules + 对应提取物」的双轨设计，<strong>具体成分与浓度未给 → 待补全文</strong>。</li>
<li><strong>读出维度</strong>：细胞毒性、衰老细胞负荷、增殖、DNA 损伤负荷、SASP 标志物。</li>
<li><strong>组织层</strong>：3D <strong>人离体全层皮肤外植体</strong>，经 <strong>1.5 J/cm² UVC</strong> 照射后给简易外用配方，观察表皮增生、胶原纤维排列与衰老/炎症标志物（<strong>仅定性描述，无定量 → 待补全文</strong>）。</li>
</ul>

<h2>核心发现</h2>
<ul>
<li>老化<strong>人真皮成纤维细胞</strong>：剂量依赖的 senomorphic 效应，<strong>最高 45%（p ≤ 0.0001）</strong>。</li>
<li>老化<strong>人原代角质形成细胞</strong>：<strong>10%（p ≤ 0.001）</strong>——同一组合在两类皮肤细胞上的效应量差了四倍多，这个落差本身值得追问。</li>
<li><strong>DNA 损伤负荷下降 50%（p ≤ 0.0001）</strong>。</li>
<li><strong>不诱导细胞增殖</strong>：对 senomorphic 路线而言这是关键的安全性叙事——既压下了衰老负荷，又没有给出促增殖信号（senolytic 之外的一条路，最怕的就是「顺手刺激了增殖」）。</li>
<li>机制定位：<strong>天然小分子协同 → 上游 ERK/AKT 信号 → RNA 剪接调控 → 衰老表型重编程</strong>。</li>
</ul>

<h2>定量结果与证据边界</h2>
<table>
<tr><th>读出</th><th>结果</th><th>统计</th></tr>
<tr><td>真皮成纤维细胞衰老负荷</td><td>最高 −45%</td><td>p ≤ 0.0001</td></tr>
<tr><td>角质形成细胞衰老负荷</td><td>−10%</td><td>p ≤ 0.001</td></tr>
<tr><td>DNA 损伤负荷</td><td>−50%</td><td>p ≤ 0.0001</td></tr>
<tr><td>细胞增殖</td><td>未诱导</td><td>摘要未给统计量</td></tr>
<tr><td>3D 外植体（UVC 1.5 J/cm²）</td><td>表皮增生减轻、胶原排列恢复、衰老与炎症标志物下降</td><td><strong>定性，无定量 → 待补全文</strong></td></tr>
</table>
<p><strong>局限（四条，全部必须带进解读）：</strong></p>
<ol>
<li><strong>「reprogramming」是宽泛用法，不是 OSK/Yamanaka 部分重编程。</strong>摘要里的机制是 ERK/AKT 与 RNA 剪接调控，与表观遗传重编程不在同一层级；标题措辞偏产品化，<strong>读全文前不宜把它归类为「部分重编程」进展</strong>。</li>
<li><strong>3D 外植体结果是定性的</strong>，未给样本量、评分方法与统计量，<strong>不能当效应量引用</strong>。</li>
<li><strong>用的是 UVC 而非 UVB/UVA。</strong>UVC 在自然日光中不到达地表，作为「光老化」模型的外部效度有限 —— 需看全文是否另做 UVB。</li>
<li><strong>潜在产业关联未在摘要披露</strong>：作者团队含多位非学术机构署名（机构在 API 中未列明），属需全文核验的利益相关事项。</li>
</ol>

<h2>为什么值得关注</h2>
<p>Harries 组的长期主线是<strong>剪接因子调控与细胞衰老</strong>，本文是该主线向「可外用、可产品化」的延伸。价值在两点：一是把衰老干预靶点从「清除衰老细胞」<strong>前移到「剪接调控」</strong>，与 senolytic/senomorphic 主流叙事形成对照；二是给出<strong>人原代老化细胞＋3D 全层皮肤</strong>的层级证据链，比纯细胞系更接近皮肤衰老的真实组织环境。如果你关注「皮肤作为衰老研究的可见窗口」，或美容–长寿交叉赛道（senomorphic 护肤），这篇值得优先读全文—— <strong>而全文恰恰是本文目前最缺的东西</strong>。</p>""",
            related=REL_SKIN,
        ),

        "Alpha-Klotho-Deficient-Rats-Phosphorus-Restriction-Breeding-2026.html": dict(
            topic="方法与工具", ev="B", tag="预印本",
            title="α-Klotho 缺陷大鼠终于能养到第五代了：靠的是母体低磷饮食，不是基因改造",
            crumb="α-Klotho 缺陷大鼠的多代繁育突破",
            desc="用母体低磷饮食这一「非基因」手段，绕过 α-Klotho 缺陷大鼠的早期死亡与繁殖障碍，"
                 "把断奶存活率从 85.8% 提到 92.6%，并把该经典早老模型维持到至少第五代。",
            source=src2,
            body="""<p><strong>一句话结论：</strong>从交配持续到哺乳期给母体喂<strong>低磷（LP）饲料</strong>，把 α-Klotho 缺陷大鼠的断奶前存活率从 <strong>85.8% 提到 92.6%</strong>；断奶后继续低磷，可支持生长、性腺发育与 KO×KO 自然交配，群体<strong>至少维持到第 5 代</strong>。</p>

<p class="notice-box"><strong>⚠️ 本文为预印本，未经同行评审；本次仅依据官方摘要撰写，全文未获取（源站封锁）。</strong></p>

<h2>这项研究想回答什么</h2>
<p>α-Klotho 是衰老研究的标志性基因（Kuro-o 1997 年发现，缺陷小鼠呈早老表型、寿命缩短），但这条线长期卡在一个工程问题上：<strong>KO 动物活不久，也生不出</strong>。没有足够的动物数量和稳定的繁育体系，任何需要长期随访或足够样本量的研究都无从谈起。本文的问题因此非常具体——<strong>能不能不动基因，只靠营养手段，把这个模型变成可长期维持、可多代繁育的常规模型？</strong></p>

<h2>他们怎么做的</h2>
<ul>
<li><strong>模型</strong>：CRISPR/Cas9 介导的 <strong>α-Klotho 外显子 1–5 缺失</strong>大鼠，主要在 <strong>Wistar-Imamichi</strong> 背景上评估。</li>
<li><strong>干预</strong>：母体低磷（LP）饲喂，从交配持续到哺乳期；部分动物断奶后继续 LP。</li>
<li><strong>读出</strong>：断奶前存活率、KO 幼崽占比、血浆磷、生长与性腺发育、KO×KO 自然交配成功率、24 小时代谢节律（间接测热法）。</li>
<li><strong>作者阵容</strong>：通讯 Yasumitsu Nagao（日本自治医科大学），作者列表含 <strong>Kuro-o Makoto</strong>——α-Klotho 的发现者本人。</li>
</ul>

<h2>核心发现</h2>
<table>
<tr><th>指标</th><th>低磷（LP）</th><th>正常磷</th></tr>
<tr><td>断奶前总体存活率</td><td><strong>92.6%</strong></td><td>85.8%</td></tr>
<tr><td>断奶存活个体中 KO 占比</td><td><strong>34/113</strong></td><td>23/145</td></tr>
<tr><td>KO×KO 自然交配后代</td><td colspan="2">15 窝中 <strong>74/85</strong> 存活至断奶</td></tr>
<tr><td>KO 群体维持代数</td><td colspan="2"><strong>至少第 5 代</strong></td></tr>
<tr><td>24h 代谢节律</td><td colspan="2">明暗周期下<strong>仍呈异质性</strong>（无具体参数 → 待补全文）</td></tr>
</table>
<p>此外，母体 LP 同时<strong>降低了 KO 幼崽的血浆磷</strong>——这与 α-Klotho 在 FGF23–磷轴中的位置是一致的。</p>

<h2>证据边界与四条必须保留的意见</h2>
<ol>
<li><strong>这是模型建立/维持的方法学突破，不是衰老机制的新发现。</strong>摘要未报告任何寿命、肾功能、血管钙化或磷代谢下游表型的新数据，<strong>别当成「Klotho 延寿」的新证据读</strong>。</li>
<li><strong>92.6% vs 85.8% 的存活差异，摘要未给统计检验，也未给窝数分母的方差结构。</strong>是否显著、是否受窝间效应驱动，<strong>待补全文</strong>。</li>
<li><strong>低磷饮食本身是强干预，而且恰好打在这套系统的核心上。</strong>FGF23–Klotho–磷轴正是该模型的主轴，用它来维持 KO 动物，很可能<strong>同时改变了你本来想观察的表型</strong>——后续任何用该模型做的磷/矿物质/肾脏表型研究，都必须把 LP 当作混杂因素处理。</li>
<li><strong>代谢节律的「异质性」结论模糊</strong>，无量化指标，<strong>待补全文</strong>。</li>
</ol>

<h2>为什么值得关注</h2>
<p>本文属于<strong>基础设施级贡献</strong>：一旦落地，α-Klotho 大鼠就能进入需要长期随访与足够样本量的研究——肾–血管–骨轴、FGF23/磷代谢、代谢节律与衰老的交互，这些方向此前受限于模型本身「难维持」，现在有了可操作的入口。如果你的研究线涉及<strong>营养感应与矿物质代谢</strong>，或需要用大鼠（而非小鼠）做生理操作，这篇是必读的方法学前置。反过来说，若你只关心「Klotho 能不能延寿」，这一篇给不出新答案。</p>""",
            related=REL_KLOTHO,
        ),
    }

    for slug in A:
        if slug in used:
            sys.exit(f"✗ slug 已存在，拒绝覆盖：{slug}")
    print(f"本批新写 {len(A)} 篇（观察哨 2 条按上游建议不成篇，理由见文件头）")
    ga.A = A
    ga.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
