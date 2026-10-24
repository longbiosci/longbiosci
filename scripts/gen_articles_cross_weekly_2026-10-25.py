#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_articles_cross_weekly_2026-10-25.py —— 内容摄入第 24 批（交叉周报 2026-10-25）

来源与判定
────────
事实源：元层《临床×文献交叉周报_2026-10-25》（file_id djjxCTwChAkQ，实测 39,871 B，
        生成时间 2026-10-25 01:20，由上游自动化任务产出）。
数据窗口：临床试验 ClinicalTrials.gov API v2（LastUpdatePostDate 2026-10-17→2026-10-25，
        HTTP 200，拉取时刻 01:05）· 科学文献 PubMed E-utilities（EDAT 近 10 日，
        HTTP 200，拉取时刻 01:03）。
本期检出：203 条唯一 NCT（核心 geroscience 49 条）· 355 篇唯一 PMID（核心 153 篇）
        · 31 组交叉条目。

体裁与产出口径
──────────────
交叉周报每周一期，**每期成一篇**，与 10-12 创刊号、10-18 期同一口径
（tag=交叉周报 / type=交叉周报 / evidence=A / source=IMA 交叉追踪）。
周报的文献侧已由同批 a/c 脚本按卡片逐条成篇（114 张卡片），故本周报文章
**只承担周报独有的那部分**：临床侧登记数据、临床↔文献的交叉判定、争议与风险信号。

查重（规则④，硬规则）
──────────────────────
扫描 news/*.html **正文全文**提取 DOI + PMID 后逐条比对（不只看 doi-index.json）：
  · 周报正文 45 个 DOI / 41 个 PMID 中，文献侧多数已被同批 a/c 脚本成篇收录
    （ARG2 42909967、骨力感应 42914985、寒冷 BH2 42907506、IAP senolytic 42912996、
     血小板指数 42906648、CDPBA 42919166、HMO 42914466 等 20 条命中）；
  · 周报自身声明的 2 条跨期重复（SRSF1 10.1038/s43587-026-01234-8、
    Serpina3n 10.1016/j.cmet.2026.09.016）已在产出侧跳过，不入本文；
  · **本文为周报体裁的综述性文章，不是上述任何单篇文献的重复上站**，
    slug 级查重：Cross-Weekly-Clinical-Literature-2026-10-25.html 站内不存在。

时间标签（规则③）
────────────────
正文首段输出「数据日期 2026-10-17 → 2026-10-25（临床）/ 2026-10-15 → 2026-10-25（文献）
· 生成时间 2026-10-25 HH:MM」。

纪律
────
· 本文所有 NCT 号、分期、样本量、状态、终点均**照抄周报原文**，未做推断；
· 周报未给定量的地方一律写「周报未给」或「待读出」，不补数；
· 争议与风险信号按周报原文四节照录，不作缓和。
"""
import importlib.util
import os
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATE = "2026-10-25"
GEN_AT = datetime.now().strftime("%Y-%m-%d %H:%M")

sys.argv = ["gen_articles.py", ROOT, "/dev/null", DATE]
_spec = importlib.util.spec_from_file_location(
    "ga", os.path.join(ROOT, "scripts", "gen_articles.py"))
ga = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ga)

A = {}

A["Cross-Weekly-Clinical-Literature-2026-10-25.html"] = dict(
    topic="临床与转化", ev="A", tag="交叉周报",
    title=("交叉周报 2026-10-25：D+Q+NR 三联完成读出的同一周，"
           "小鼠模型反问「清除衰老细胞并不恢复 NAD」"),
    crumb="交叉周报 2026-10-25 · 临床×文献",
    desc=("本周 203 条登记更新里最硬的一条：SENIOR（NCT06018467，n=120，II 期）"
          "把骨质疏松定义成「骨骼加速衰老」，用 Dasatinib + Quercetin + 烟酰胺核糖苷三联"
          "去打骨吸收标志物 CTX，状态已COMPLETED。同一周 Nat Commun 的慢性 NAD 缺乏小鼠"
          "给出反方向读数：senolytic 只部分改善功能、且不能恢复 NAD。另有 5 条试验把表观遗传"
          "时钟写成注册终点，而 10 时钟头对头比较显示选型可能直接决定成败。"),
    source=('<em>IMA 知识库《元层·临床×文献交叉周报》2026-10-25 期</em>'
            '（file_id djjxCTwChAkQ，实测 39,871 B · 生成时间 2026-10-25 01:20）'
            ' · 临床侧 ClinicalTrials.gov API v2（HTTP 200）'
            ' · 文献侧 PubMed E-utilities（HTTP 200）'
            ' · <strong>本文为二次综述，定量均照录周报原文，未作推断补全</strong>'),
    body=(
        '<p><em>数据日期 · 临床试验 2026-10-17 → 2026-10-25（ClinicalTrials.gov API v2，'
        'HTTP 200，拉取 01:05）｜数据日期 · 科学文献 2026-10-15 → 2026-10-25'
        '（PubMed E-utilities，HTTP 200，拉取 01:03）｜生成时间 ' + GEN_AT + '</em></p>\n\n'
        '<p>本期基线：检出 <strong>203 条唯一 NCT</strong>（其中核心 geroscience '
        '<strong>49</strong> 条）、<strong>355 篇唯一 PMID</strong>（核心衰老机制/干预 '
        '<strong>153</strong> 篇），配出 <strong>31 组</strong>交叉条目，覆盖全部 49 条核心试验。'
        '与基线（往期周报 + 月度综述 + 两张总表，共 44 个 NCT、39 个 DOI、24 个 PMID）比对，'
        'NCT 侧 <strong>0</strong> 冲突，文献侧 2 条重复已在产出端跳过。'
        '下面只讲周报独有的那部分——临床登记这一侧发生了什么。</p>\n\n'
        '<h2>① SENIOR 完成：第一个把 senolytic 与 NAD⁺ 前体捆绑进骨质疏松的 II 期 RCT</h2>\n\n'
        '<p><strong>NCT06018467</strong>（Odense University Hospital，PHASE2，n=120，'
        '<strong>COMPLETED</strong>；主要完成 2026-04-24，登记更新 2026-10-23）。'
        '方案把骨质疏松明确定义为「骨骼加速衰老、衰老细胞在骨内蓄积」的疾病，'
        '干预为 <strong>Dasatinib 100 mg + Quercetin 1250 mg + 烟酰胺核糖苷 1 g</strong>，'
        '主终点是骨吸收标志物 <strong>CTX</strong>（基线 / W5 / W13 / W21）。</p>\n\n'
        '<p>交叉价值：本周 <em>Theranostics</em> 给出正交机制支撑——<strong>ARG2</strong> '
        '在衰老成骨细胞中显著升高，经 <strong>IκBα/NF-κB/HDAC9 → 抑制 TXN2</strong> '
        '造成线粒体氧化应激与 PINK1/Parkin/LC3 线粒体自噬受阻；成骨细胞特异性 ARG2 敲除'
        '或药物抑制（<strong>BEC</strong>）可逆转骨丢失（PMID 42909967，'
        'DOI 10.7150/thno.129818，2026-10-02）。<strong>D+Q 清除衰老细胞 + NR 修复线粒体</strong>'
        '的组合，恰好对应该轴的上下游两端——这是本期机制闭环最完整的一条。</p>\n\n'
        '<h2>② 争议：慢性 NAD 缺乏模型直接挑战这个组合逻辑</h2>\n\n'
        '<p><em>Nat Commun</em> 的 ANDY 小鼠（PMID 42918808，'
        'DOI 10.1038/s41467-026-77996-x）给出一条不好看的结论：'
        '<strong>senolytic 处理仅部分改善功能衰退，且不能恢复 NAD 水平</strong>；'
        '只有膳食烟酸补充才能逆转表型、生化、衰老相关与转录异常。'
        '这与 SENIOR 的三联设计形成直接张力——<strong>如果清除衰老细胞不能恢复 NAD，'
        '三联中的 NR 可能才是真正起效的那个，而 D+Q 的贡献被稀释</strong>。</p>\n\n'
        '<p>读这条时要盯住两点：SENIOR 样本量仅 120、主终点是 CTX（骨吸收标志物，'
        '不是骨折这类硬终点），替代终点的解释空间很大。周报原文也是这么写的。</p>\n\n'
        '<h2>③ NIA 亲自下场：Urolithin A 进入 NIH 资助的代谢终点试验</h2>\n\n'
        '<p><strong>NCT06274749</strong>（申办方 <strong>National Institute on Aging</strong>，'
        'n=180，≥55 岁、BMI≥27，<strong>RECRUITING</strong>，启动 2026-10-28）。'
        '主终点是口服葡萄糖后<strong>胰岛素分泌</strong>，次级终点包括 ³¹P MRS 测线粒体呼吸、'
        '脑 MRS 测脑氧化代谢、以及肠道菌群组成。同期 <strong>NCT07517913</strong>'
        '（Amazentis SA，n=40，COMPLETED 2026-10-04）专门测 Mitopure 的 '
        '<strong>CSF:plasma 比值</strong>——血脑屏障这一侧第一次有了专门的试验。</p>\n\n'
        '<p>交叉价值：<em>Adv Sci</em> 综述（PMID 42875857）把 UA 类干预定位在'
        '「递送瓶颈 + 证据分级」框架内——SS-31 仅获 Barth 综合征加速批准、'
        'NAD⁺ 前体处于早期临床、其余多为临床前。NIA 的设计（外周代谢 + 中枢代谢 + 菌群'
        '同时测）正是为填这个缺口。</p>\n\n'
        '<h2>④ 4 周读一次生物年龄：迄今最激进的终点设定</h2>\n\n'
        '<p><strong>NCT07888595</strong>（Frontiers in Bioscience Research Institute and Aging，'
        'EARLY_PHASE1，n=48，ENROLLING_BY_INVITATION，启动 2026-10-21，主完成 2028-10-14）。'
        '主终点为 <strong>START/REST 生物年龄（转录组 tAge 与蛋白组 pAge，单位：年），4 周</strong>；'
        '次级终点含 9 基因衰老 qPCR 面板、IL-6/IL-8、胞内 α-KG/ATP/NAD⁺、NAD⁺/NADH 比值、'
        'NF-κB p65 活性。设计上用<strong>同侧/对侧未处理皮肤作自身对照</strong>。</p>\n\n'
        '<p>意义与风险并存：4 周即读生物年龄变化，是本方向迄今最激进的终点设定；'
        '而本周 <em>Diabetes</em> 的 10 时钟头对头比较（PMID 42900742，'
        'DOI 10.2337/db26-0089）显示——在 1 型糖尿病肾病中，'
        '<strong>仅 PhenoAge 的表观年龄加速与表观预测端粒长度显著关联疾病，其余时钟不一致</strong>。'
        '换句话说，<strong>时钟选型可能直接决定试验成败</strong>。</p>\n\n'
        '<h2>⑤ 骨机械力感应：给无法运动的老年人留了一个可药化靶点</h2>\n\n'
        '<p><em>Cell Metabolism</em>（PMID 42914985，DOI 10.1016/j.cmet.2026.09.020，'
        '2026-10-23）：删除骨细胞机械敏感通道 <strong>Piezo1</strong> 使小鼠<strong>全身衰老加速</strong>；'
        '对 20–24 月龄小鼠施加动态胫骨轴向负荷（DTAL），<strong>健康期与寿命均延长'
        '（中位寿命 +9.4%，79.5 天）</strong>，并逆转骨髓免疫衰老、下调促炎因子。'
        '新鉴定的力学响应因子 <strong>PEDF</strong> 与人类健康衰老高度相关。</p>\n\n'
        '<p>价值在于临床未满足需求：为卧床、行动受限、无法完成运动处方的老年人'
        '提供了<strong>可药化的替代靶点</strong>。与本期 CHALF 队列（NCT07881094，n=8960）、'
        'Vivifrail 多成分运动试验（NCT07732478，n=300）构成「人群—机制—干预」三角。</p>\n\n'
        '<h2>⑥ 表观遗传时钟正从研究工具变成注册临床终点</h2>\n\n'
        '<p>本期检出 <strong>5 条以生物年龄/表观时钟为终点</strong>的试验：'
        'NCT07888595（START/REST）、NCT07879742（<strong>DunedinPACE</strong> 主终点，'
        'n=262，7 中心，1 年；干预是鸡精 BEC 每日摄入）、NCT07890753'
        '（唾液 DNAm 年龄加速）、NCT07871552（HIV 人群经验证表观时钟 + LINE-1 反转录转座子活性）、'
        'NCT07887334（含衰弱评估）。其中 NCT07879742 属于<strong>消费健康品牌首次用硬终点'
        '做随机对照</strong>的规模。</p>\n\n'
        '<p>但测量学基础还没稳：<em>Clin Nutr</em> 直接质疑「膳食模式 ↔ 生物年龄加速」'
        '关联的因果可解释性（PMID 42906317）；<em>Geroscience</em> 的 INSPIRE-t（n=890，'
        '20–102 岁，PMID 42891778）显示体力活动、久坐、睡眠质量与多种时钟存在独立与交互关联，'
        '生活方式是必须控制的混杂。在这些试验读出之前，<strong>「生物年龄下降」这个终点本身'
        '仍要经过一致性检验</strong>。</p>\n\n'
        '<h2>其余三条争议与一条风险信号</h2>\n\n'
        '<ul>\n'
        '<li><strong>二甲双胍的阴性分子读数。</strong><em>Geroscience</em> 报告非糖尿病老年 AMD '
        '随机试验（NCT02684578，1000 mg bid × 18 个月，采样 n=15：8 用药 / 7 对照）的'
        '<strong>全血转录组：多重校正后无任何单个基因达显著差异</strong>'
        '（PMID 42900294，DOI 10.1007/s11357-026-02593-1，2026-10-20）。'
        '样本极小是首要局限，但「二甲双胍作为 gerotherapeutic 仍缺可重复的分子层面人体证据」'
        '这句话本周成立。</li>\n'
        '<li><strong>NAD⁺ 的临床声称与证据等级不匹配。</strong><em>Aesthetic Surgery Journal</em> '
        '的证据评述（PMID 42891627，DOI 10.1093/asj/sjag232，2026-10-17）指出，'
        'NAD⁺ 的抗衰、代谢、神经认知益处「支持证据主要是轶事性的，来源于临床前、'
        '非手术数据与患者证言，而非临床研究」。与此同时 dsm-firmenich 的 trigonelline I 期'
        '（NCT07880925）以<strong>全血 NAD⁺ 为主终点</strong>——行业尚未证明 NAD⁺ 升高本身'
        '能转化为临床获益。</li>\n'
        '<li><strong>风险信号：NCT06876142 在启动前被挂起。</strong>NCI 申办的 '
        '<strong>Mirdametinib + Sirolimus</strong>（MEK + mTOR 双抑制）治疗 RAS 突变难治复发性'
        '多发性骨髓瘤，PHASE1/2，n=54，计划启动 2026-10-28，登记状态于 '
        '<strong>2026-10-23 更新为 SUSPENDED</strong>。MEK/mTOR 双阻断是衰老领域反复出现的'
        '组合策略，其安全性边界值得持续跟踪。</li>\n'
        '</ul>\n\n'
        '<h2>本期新增靶点（周报口径，均带 DOI + PMID）</h2>\n\n'
        '<ul>\n'
        '<li><strong>PEDF</strong>——骨细胞 Piezo1 下游的力学响应性抗衰因子（Cell Metab，42914985）</li>\n'
        '<li><strong>ARG2 → IκBα/NF-κB/HDAC9/TXN2</strong>——成骨细胞衰老轴，抑制剂 BEC 有效（Theranostics，42909967）</li>\n'
        '<li><strong>IAP 拮抗剂 senolytic</strong>——衰老细胞对 cIAP-2 成瘾，FADDosome 是入口开关（Sci Adv，42912996）</li>\n'
        '<li><strong>CAT-4/GCH1 → BH2 → DHFR-1/BH4 → PAH-1</strong>——冷暴露经肌肉来源 BH2 跨组织延寿（Nature，42907506）</li>\n'
        '<li><strong>初级纤毛—NAD⁺—CHMP4B—溶酶体轴</strong>——下丘脑代谢衰老，热量限制可恢复（Aging Cell，42902820）</li>\n'
        '<li><strong>线粒体柠檬酸代谢 → SASP</strong>——独立于 mtDNA-cGAS-STING 的第二条 SASP 驱动通路（Dev Cell，42874574）</li>\n'
        '<li><strong>血小板炎症指数 NPR/MPR/MNPR</strong>——与 6 种甲基化时钟及 KDM BioAge 加速显著相关（Exp Gerontol，42906648）</li>\n'
        '<li><strong>CDPBA</strong>——基于 1170 万人 Cox 模型的生物年龄算法，AUROC 0.849/0.871（BMC Cardiovasc Disord，42919166）</li>\n'
        '</ul>\n\n'
        '<h2>局限（照录周报 §6.3）</h2>\n\n'
        '<ul>\n'
        '<li>临床试验侧只用 <code>LastUpdatePostDate</code> 区间检索，'
        '<strong>不覆盖未更新登记的在研试验</strong>；</li>\n'
        '<li>文献侧仅取 <code>EDAT</code> 近 10 日，长周期研究可能落在窗口外；</li>\n'
        '<li>「核心 geroscience」判定为规则化标签匹配，存在人工判读边界；</li>\n'
        '<li>交叉配对基于机制标签↔主题标签，<strong>不等于因果验证</strong>。</li>\n'
        '</ul>'),
    related=[],
)

ga.A = A
ga.main()
