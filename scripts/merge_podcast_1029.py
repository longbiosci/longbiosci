#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merge_podcast_1029.py —— 03:30 播客班 · ep036–ep047 接入（12 期）

消化对象
────────
本轮自制产出：podcast/transcripts/*.md（12 份六段式口播稿）
              + audio/*.mp3（12 个 edge-tts 合成音频，ffprobe 实测时长）

判空（硬规则）：音频与文稿均在本班现场产出，落库前逐项 os.path.exists 实测，
                字节数非空（mp3 均 > 1 MB）。非从网盘接收，无缓存值可比对。

时间标签（规则③）
────────────────
data_datetime = 2026-10-28 05:51（取自 data/intake-cursor.json 的 updated_at，
                即站内内容数据的截止时刻；不用本轮运行时刻冒替上游数据日期）
generated_at  = 本轮运行的真实时刻（HH:MM），落库瞬间取一次，12 期与页面共用

四路去重（沿用既有红线）：slug / title / article_slugs / DOI 对 ep001–ep035
全量历史比对，重复即拒绝。另加一层：新期目之间的两两比对。

红线：每期至少一条 sources 且带 DOI 或 PMID；article_slugs 指向的站内文章
必须真实存在；音频文件必须存在。任一条不满足即 exit 1，不静默降级。
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DATETIME = "2026-10-28 05:51"
CN_TZ = timezone(timedelta(hours=8))

# ── 12 期事实源（每条数字均来自站内已发布文章，逐条可回查）────────────────
NEW = [
    dict(
        id="ep036", slug="dog-aging-project-41047-survival-2026", series="论文精读",
        title="四万一千只狗的寿命方程：体型、血统，还有你住在哪里",
        desc="41,047 只伴侣犬的生存分析：中位寿命从小型犬 14 年到巨型犬不足 10 年；校正人口学后城乡差异不再显著而地区差异仍显著，且与人类死亡率模式正相关（r=0.43）。",
        article="Dog-Aging-Project-Longevity-Factors-41047-Dogs-Geroscience-2026.html",
        sources=[dict(
            label="GeroScience（2026）：Dog Aging Project 首批生存分析，41,047 只伴侣犬的寿命决定因素",
            doi="10.1007/s11357-026-02448-9", pmid="42945030",
            note="观察性队列，死亡日期由主人报告；七十二个关联为相关而非因果；站内 B 级证据，核心结论来自动物模型，不能外推至人体")],
    ),
    dict(
        id="ep037", slug="hiv-epigenetic-age-acceleration-meta-2026", series="论文精读",
        title="表观遗传时钟快了 3.41 年：一份 55 项研究的荟萃，和一个没人填的空白",
        desc="14 项 HorvathAge 表观年龄加速的随机效应荟萃给出平均差 3.41 年（95%CI 2.22–4.60）；同时暴露出「无一项研究聚焦 65 岁以上」的证据空白。",
        article="HIV-Epigenetic-Aging-Metaanalysis-JGerontolA-2026.html",
        sources=[dict(
            label="The Journals of Gerontology: Series A（2026）：HIV 感染与表观遗传年龄加速的系统综述与荟萃分析",
            doi="10.1093/gerona/glag252", pmid="42921758",
            note="55 项纳入研究，异质性大（人群、样本、芯片平台、所用时钟均不统一）；仅 6 项纳入 18 岁以下、无一项聚焦 65 岁以上；站内 A 级证据指证据层级，非个体外推许可")],
    ),
    dict(
        id="ep038", slug="mitochondrial-biomarkers-neurology-2026", series="机制十分钟",
        title="线粒体进神经科要过四道关：一份清单，和一句「还不能横向比」",
        desc="综述把线粒体标志物分为体液、遗传、多组学、影像四类，跨病种指向生物能量学、氧化还原稳态、线粒体基因组维持与炎症信号四条共同紊乱。",
        article="Mitochondrial-Biomarkers-Neurology-Clinical-Implications-NatRevNeurol-2026.html",
        sources=[dict(
            label="Nature Reviews Neurology（2026）：线粒体生物标志物在神经科的临床意义综述",
            doi="10.1038/s41582-026-01274-z", pmid="",
            note="综述，站内 A 级证据，依据英文摘要整理未取全文；作者明示临床落地仍受方法学异质性、生物变异性与疾病特异性不足限制；目前无任何单一指标可跨研究横向比较")],
    ),
    dict(
        id="ep039", slug="mitoq-human-preantral-follicle-2026", series="打假与证伪",
        title="线粒体抗氧化剂在人类卵泡上翻车：成熟期有益，不等于早期也有益",
        desc="人类卵巢皮质与窦前卵泡体外模型中，Mito-Q 未改善卵泡存活率与密度，浓度升高反伴随颗粒细胞凋亡增加与窦前卵泡生长受限。",
        article="MitoQ-Mitochondria-Targeted-Antioxidant-Human-Preantral-Follicle-MolHumReprod-2026.html",
        sources=[dict(
            label="Molecular Human Reproduction（2026）：线粒体靶向抗氧化剂对人类卵巢组织与窦前卵泡的影响",
            doi="10.1093/molehr/gaag062", pmid="",
            note="体外研究，浓度与体内暴露不可直接换算；组织来源为特定临床人群且样本量有限；结论限于早期卵泡发生与生育力保存场景，不应读成「Mito-Q 对人体有害」的泛化判断")],
    ),
    dict(
        id="ep040", slug="nmn-cardiac-hypertrophy-hypoxia-2026", series="打假与证伪",
        title="NMN 的一次未达主要终点：应激标志物压住了，心脏肥厚没挡住",
        desc="间歇常压低氧小鼠中，NMN 显著减弱右心室 BNP 与 Myh7 表达，却未在器官层面阻止心脏肥厚，血清 LDH 活性反而进一步升高。",
        article="NMN-Does-Not-Prevent-Cardiac-Hypertrophy-Hypoxia-Mice-Nutrients-2026.html",
        sources=[dict(
            label="Nutrients（2026）：间歇常压低氧小鼠中 NMN 对心脏肥厚与应激标志物的作用",
            doi="10.3390/nu18203334", pmid="42942905",
            note="作者自称探索性结果；低氧模型与人类心脏衰老不同；未见剂量-反应与长期随访；站内 B 级证据，来自动物模型，不能外推至人体")],
    ),
    dict(
        id="ep041", slug="cellular-senescence-assessment-guide-2026", series="机制十分钟",
        title="一个染色阳性就说「细胞衰老了」：一份更新版指南要纠正的正是这件事",
        desc="更新版指南把细胞衰老检测扩展到细胞周期与形态、转录组特征、基于荧光的活细胞工具三类，并强调单一标志物判定衰老在方法学上不充分。",
        article="Updated-Guide-Assessment-Mammalian-Cellular-Senescence-MolCells-2026.html",
        sources=[dict(
            label="Molecules and Cells（2026）：哺乳动物细胞衰老评估的更新版方法指南",
            doi="10.1016/j.mocell.2026.100408", pmid="42946057",
            note="MiniResource 体裁，是操作指南而非新数据；摘要未给出具体判读阈值，实操细节需看全文")],
    ),
    dict(
        id="ep042", slug="bcg-tau-ps19-mice-2026", series="论文精读",
        title="卡介苗在 tau 病小鼠里做了什么：病理退了、转录组回摆，边界也还在",
        desc="PS19 小鼠给药后海马磷酸化 tau 减少、脑萎缩减缓，疾病相关基因表达特征几乎回归健康对照；人群证据仍是回顾性，效应量跨度 12%~78%。",
        article="BCG-Vaccination-Tau-Pathology-PS19-Mice-SciAdv-2026.html",
        sources=[dict(
            label="Science Advances（2026）：卡介苗接种对 PS19 tau 病小鼠病理、影像与髓系细胞重编程的影响",
            doi="10.1126/sciadv.aej4603", pmid="",
            note="小鼠单一模型、单一品系；人群证据为回顾性且效应量跨度极大；从接种卡介苗到可用于神经退行病之间仍有很长的路")],
    ),
    dict(
        id="ep043", slug="oskm-partial-reprogramming-stroke-2026", series="论文精读",
        title="部分重编程扛不扛得住一次卒中：老年小鼠四十八小时的实测",
        desc="老年小鼠诱导 OSKM 后接受永久性大脑中动脉闭塞，48 小时损伤面积更小、髓鞘完整性保留、Olig2⁺ 与 PDGFRα⁺ 细胞增加。",
        article="OSKM-Partial-Reprogramming-Ischemic-Brain-Damage-Aging-AgingCell-2026.html",
        sources=[dict(
            label="Aging Cell（2026）：部分重编程（OSKM）对老年小鼠缺血性脑损伤的作用",
            doi="10.1111/acel.70776", pmid="",
            note="观察窗仅 48 小时，属急性期读数；缺失长期生存、长期功能与剂量安全性数据；重编程是否直接作用于少突胶质细胞谱系尚未被因果证明")],
    ),
    dict(
        id="ep044", slug="glial-lipid-reprogramming-brain-aging-2026", series="机制十分钟",
        title="脑衰老里的脂质问题不是「变多了」，而是「换了身份」",
        desc="综述主张衰老脑胶质细胞的氧化还原脆弱性不取决于脂质有多少，而取决于酰基链饱和度、头基结构、氧化脂质种类与缩醛磷脂缓冲等化学性质。",
        article="Glial-Lipid-Reprogramming-Brain-Aging-Redox-Biology-2026.html",
        sources=[dict(
            label="Redox Biology（2026）：胶质细胞脂质重编程与衰老脑氧化还原脆弱性综述",
            doi="10.1016/j.redox.2026.104453", pmid="42927732",
            note="综述框架主张，非干预有效性的证据；站内 B 级证据，来自临床前证据或二次文献，不能外推至人体")],
    ),
    dict(
        id="ep045", slug="tcell-exhaustion-proteostasis-atlas-2026", series="论文精读",
        title="T 细胞耗竭的底层可能是蛋白稳态崩了：一份多组学图谱给出的落点",
        desc="四层多组学图谱把蛋白稳态崩溃定义为 T 细胞耗竭的中心特征；过表达 E3 连接酶 RNF166 在体外与体内均增强 T 细胞持久性。",
        article="Proteomic-Atlas-T-Cell-Exhaustion-Proteostatic-Collapse-Cell-2026.html",
        sources=[dict(
            label="Cell（2026）：T 细胞耗竭的多组学图谱，蛋白稳态崩溃作为中心特征",
            doi="10.1016/j.cell.2026.09.051", pmid="42906538",
            note="具体蛋白数、周转速率变化倍数与 RNF166 过表达的体内疗效幅度摘要未给出，站内标注待补全文；E3 连接酶与免疫治疗结局的关联仍属相关性证据")],
    ),
    dict(
        id="ep046", slug="ifn1-autoantibodies-centenarians-2026", series="论文精读",
        title="百岁老人的一个免疫悖论：抗病毒自身抗体不再随年龄上升了",
        desc="四个队列 938 名百岁老人中 5.4% 携带中和性 I 型干扰素自身抗体，相对「80 岁以上超过 6%」出现平台期（日本 3.3%~哥伦比亚 9.1%）。",
        article="Type-I-Interferon-Autoantibodies-Plateau-Centernarians-JHumImmun-2026.html",
        sources=[dict(
            label="Journal of Human Immunity（2026）：四个队列 938 名百岁老人中和性 I 型干扰素自身抗体患病率",
            doi="10.70962/jhi.20260143", pmid="42944855",
            note="横断面设计，无随访死亡率数据；5.4% 与「80 岁以上 >6%」为跨研究比较而非同一队列内部对照；四队列检测方法与入组标准一致性需看全文")],
    ),
    dict(
        id="ep047", slug="epigenetic-clocks-life-insurance-2026", series="产业脉搏",
        title="保险公司为什么还不买表观遗传时钟的账：四条理由，两个例外",
        desc="《Insurance Science》列出四条障碍：个体层面不准、不等同于生物年龄、训练数据偏差、预测死亡率不优于年龄性别吸烟史血压 BMI 与病史。",
        article="Biological-Clocks-Life-Insurance-Underwriting-2026.html",
        sources=[dict(
            label="Insurance Science（2026）：生物衰老时钟用于人寿保险核保的可行性分析",
            doi="10.17849/insm-53-2-1-5.1B", pmid="",
            note="分析性文章，非原始研究；本期只转述其结论，不推荐任何检测产品、公司与检测服务，亦不作任何投资相关推断")],
    ),
]

DATE = "2026-10-29"


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1", path],
        capture_output=True, text=True, check=True).stdout
    return round(float(out.strip().split("=")[1]))


def main():
    gen_at = datetime.now(CN_TZ).strftime("%Y-%m-%d %H:%M")
    data = json.load(open(os.path.join(ROOT, "data", "podcast.json"), encoding="utf-8"))
    old = data["episodes"]
    print("① 历史期数 %d（%s ~ %s）" % (len(old), old[0]["id"], old[-1]["id"]))

    # ── ② 硬校验：音频 / 文稿 / 站内文章 / 来源标识 ──
    errs = []
    for e in NEW:
        aud = os.path.join(ROOT, "audio", e["slug"] + ".mp3")
        if not os.path.exists(aud) or os.path.getsize(aud) < 1024:
            errs.append("%s 音频缺失或过小" % e["id"])
        tr = os.path.join(ROOT, "podcast", "transcripts", e["slug"] + ".md")
        if not os.path.exists(tr):
            errs.append("%s 文稿缺失" % e["id"])
        if not os.path.exists(os.path.join(ROOT, "news", e["article"])):
            errs.append("%s 站内文章不存在：%s" % (e["id"], e["article"]))
        if not e["sources"]:
            errs.append("%s 无来源" % e["id"])
        for s in e["sources"]:
            if not (s.get("doi") or s.get("pmid")):
                errs.append("%s 来源缺 DOI/PMID" % e["id"])
    print("② 音频/文稿/站内文章/来源标识校验：%d 项不符" % len(errs))
    for x in errs:
        print("   ✗ " + x)
    if errs:
        sys.exit(1)

    # ── ③ 四路去重（对历史 + 本轮内部）──
    def key(e):
        return (e["slug"], e["title"].strip(),
                tuple(sorted(e.get("article_slugs") or [])),
                tuple(sorted((s.get("doi") or "").lower() for s in e.get("sources") or [])))
    hist = {key(e) for e in old}
    hist_slugs = {e["slug"] for e in old}
    hist_titles = {e["title"].strip() for e in old}
    hist_arts = {s for e in old for s in (e.get("article_slugs") or [])}
    hist_dois = {(s.get("doi") or "").lower() for e in old for s in (e.get("sources") or []) if s.get("doi")}
    dup = []
    for e in NEW:
        if e["slug"] in hist_slugs:
            dup.append((e["id"], "slug"))
        if e["title"].strip() in hist_titles:
            dup.append((e["id"], "title"))
        for s in e["sources"]:
            if (s.get("doi") or "").lower() in hist_dois:
                dup.append((e["id"], "DOI " + s["doi"]))
        if ("news/" + e["article"]) in hist_arts or e["article"] in hist_arts:
            dup.append((e["id"], "article_slug"))
    seen = set()
    for e in NEW:
        k = (e["slug"], e["title"].strip())
        if k in seen:
            dup.append((e["id"], "本轮内部重复"))
        seen.add(k)
    print("③ 四路去重（slug/title/article_slugs/DOI）：重复 %d 项" % len(dup))
    for x in dup:
        print("   ✗ " + str(x))
    if dup:
        sys.exit(1)

    # ── ④ 组装新期目（duration_sec 由 ffprobe 实测回填，不手填）──
    built = []
    for e in NEW:
        aud = os.path.join(ROOT, "audio", e["slug"] + ".mp3")
        built.append({
            "id": e["id"], "slug": e["slug"], "series": e["series"],
            "title": e["title"], "desc": e["desc"],
            "article_slugs": ["news/" + e["article"]],
            "sources": [dict(label=s["label"], doi=s["doi"], pmid=s["pmid"],
                             url=("https://doi.org/" + s["doi"]) if s["doi"] else "",
                             note=s["note"]) for s in e["sources"]],
            "date": DATE, "data_datetime": DATA_DATETIME, "generated_at": gen_at,
            "duration_sec": probe(aud),
            "audio": "audio/" + e["slug"] + ".mp3",
            "voice": "zh-CN-XiaoxiaoNeural",
        })
    print("④ ffprobe 实测时长回填完成：%d 期" % len(built))

    # ── ⑤ 回写播客页时间标签并落库 ──
    data["show"]["data_datetime"] = DATA_DATETIME
    data["show"]["generated_at"] = gen_at
    data["episodes"] = old + built
    json.dump(data, open(os.path.join(ROOT, "data", "podcast.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("⑤ data/podcast.json 写入完成：%d → %d 期（新增 %d）"
          % (len(old), len(data["episodes"]), len(built)))
    for b in built:
        print("   + %s %s  %s  %ss  %s" % (b["id"], b["slug"], b["series"],
                                           b["duration_sec"], b["generated_at"]))

    # ── ⑥ 同步文稿 frontmatter 的 generated_at 占位符 ──
    n = 0
    for b in built:
        p = os.path.join(ROOT, "podcast", "transcripts", b["slug"] + ".md")
        t = open(p, encoding="utf-8").read()
        if "__GEN_AT__" in t:
            open(p, "w", encoding="utf-8").write(t.replace("__GEN_AT__", gen_at))
            n += 1
    print("⑥ 文稿 generated_at 占位符回填：%d 份 → %s" % (n, gen_at))


if __name__ == "__main__":
    main()
