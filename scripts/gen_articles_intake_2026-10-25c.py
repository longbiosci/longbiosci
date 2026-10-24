#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_articles_intake_2026-10-25c.py —— 内容摄入第 23 批（2026-10-25 05:30 巡检）

消化对象
────────
《文献监控_2026-10-25_卡片》（file_id dnqNDVpqTrjt，实测 212,025 B）
第三节 —— **69 条摘要级卡片**（编号 46–114，卡片自带「未核验全文」标记）。

a 脚本消化的是第一节 45 条全文级卡片（已下载全文并逐节核验）；本脚本消化
剩下的 69 条摘要级。按排班改造第 ② 条「产能不设上限」，检出的增量有多少
消化多少，故这 69 条全部成篇，不做取舍。

摘要级与全文级的区别（必须在页面上说清楚）
──────────────────────────────────────────
摘要级卡片**只依据期刊公开摘要与 PubMed 元数据**撰写，付费墙全文未获取、
未逐节核验，卡片中不确定的效应量一律保留原文的「被截断 / 不可见」表述，
本站未做任何数值推算补全。正文首段与来源串均显式标注「摘要级 · 未核验全文」。

查重（规则④，硬规则）
──────────────────────
扫描 news/*.html **正文全文**提取 DOI（624 个）+ PMID（127 个）后逐条比对，
不只看 data/doi-index.json（落后于页面）：
  · 69 条摘要级卡片 DOI / PMID **站内 0 命中** → 全部净新增；
  · 另有 slug 级查重（articles.json 696 条 + 本批内部）。

时间标签（规则③）
────────────────
每篇正文首段输出「数据日期 2026-10-25 · 生成时间 YYYY-MM-DD HH:MM」。
数据日期取卡片期号 2026-10-25（检索窗口 2026-10-22~2026-10-25）。

证据分级
────────
· A 人体原始数据研究（队列 / RCT / 横断面 / 人体生信 / 汇总人体研究的 Meta）；
· B 动物模型或体外细胞的原始研究；
· C 非原始研究（叙述性综述、观点评论、理论框架、文献计量、概念框架）。
"""
import html
import importlib.util
import json
import os
import re
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATE = "2026-10-25"
GEN_AT = datetime.now().strftime("%Y-%m-%d %H:%M")
DATA_DATE = "2026-10-25"
SRC_CARD = ("IMA 知识库《文献层·文献监控卡片》2026-10-25 期 · 摘要级"
            "（file_id dnqNDVpqTrjt，实测 212,025 B）")

cards = json.load(open('/tmp/cards_1025.json', encoding='utf-8'))
AB = [c for c in cards if c.get('verify')]          # 摘要级，69 条，按出现顺序
assert len(AB) == 69, len(AB)

# 摘要级卡片编号在原文里有重号（108–114 出现两轮），故按 **索引** 定位，不用 num。
# idx → (slug, 中文标题, 面包屑短句, topic, ev, tag)
M = {
 0: ("Home-Use-LED-Mask-Cream-Anti-Aging-2026.html",
     "家用红光面罩配抗衰面霜：弹性蛋白 +29.6%，鱼尾纹深度 −24.2%",
     "家用 LED 光生物调节的人体证据", "器官衰老", "A", "临床研究"),
 1: ("Frailty-Screening-Preventive-Care-LTC-Certification-2026.html",
     "把衰弱筛查写进预防保健后，长期照护认定率的斜率变了",
     "衰弱筛查与照护认定率趋势", "生命历程", "A", "流行病学"),
 2: ("Wild-Type-ATTR-CM-Ageing-Myocardium-2026.html",
     "野生型 ATTR 心肌病：把视角从四聚体稳定挪到「衰老心肌」",
     "ATTR-CM 的衰老心肌框架", "器官衰老", "C", "观点评论"),
 3: ("Ferro-Aging-Alzheimer-Iron-Framework-2026.html",
     "ferro-aging：用铁死亡重写阿尔茨海默的衰老叙事",
     "铁死亡与 ferro-aging 假说", "神经退行", "C", "观点评论"),
 4: ("Endothelial-Cell-Aging-Single-Cell-Atlas-2026.html",
     "人内皮细胞衰老的单细胞图谱：血管新生退潮，与一个 p21 程序",
     "内皮细胞衰老转录图谱", "器官衰老", "A", "单细胞研究"),
 5: ("Type-2-Immunity-Counter-Regulatory-Aging-2026.html",
     "2 型免疫：衰老里那条被忽略的反调节轴",
     "2 型免疫的反调节角色", "免疫与炎症", "C", "观点评论"),
 6: ("Lowering-Insulin-Signalling-Development-Longevity-2026.html",
     "发育期降胰岛素信号：长得更快、生得更多、活得更久，但子代付出代价",
     "发育期胰岛素信号与生活史权衡", "代谢与营养", "B", "基础研究"),
 7: ("Aged-Female-APOE4-KI-Rat-Neuroimaging-2026.html",
     "老年雌性 APOE4 大鼠：脑区变大而非萎缩，Barnes 迷宫已经受损",
     "APOE4 大鼠的多模态影像表型", "神经退行", "B", "基础研究"),
 8: ("Accelerated-Brain-Aging-Executive-Deficits-2026.html",
     "脑龄差与执行功能：精神病高危与精神分裂症各伤一处",
     "脑龄差与执行功能缺损", "神经退行", "A", "脑衰老与认知"),
 9: ("Biological-Age-CVD-Hospitalization-Risk-2026.html",
     "用住院风险定义生物学年龄：一个 AUROC 0.87 的新算法",
     "以住院风险估计生物学年龄", "方法与工具", "A", "方法学"),
 10: ("Nutrition-Inflammation-Index-Vascular-Aging-Mortality-2026.html",
      "营养-炎症指数与血管老化：糖尿病及前期人群的死亡风险分层",
      "营养炎症指数与血管老化", "代谢与营养", "A", "流行病学"),
 11: ("Postpartum-Recovery-Window-Maternal-Aging-2026.html",
      "产后是一个恢复窗口：妊娠间隔可能是母体衰老的缺失变量",
      "产后恢复窗口与母体衰老", "生命历程", "C", "观点评论"),
 12: ("Drosophila-Adipaging-Carotenoid-Review-2026.html",
      "Adipaging：把果蝇脂肪体当作衰老-代谢的研究平台",
      "果蝇 adipaging 模型与类胡萝卜素", "代谢与营养", "C", "综述"),
 13: ("Zinc-HDAC6-Autophagy-Cerebral-Ischemia-2026.html",
      "脑缺血再灌注后的锌：经 HDAC6 把自噬推向神经元损伤的一侧",
      "锌-HDAC6-自噬轴与脑缺血", "神经退行", "B", "基础研究"),
 14: ("Pythagorean-Self-Awareness-Telomere-RCT-2026.html",
      "心理行为干预降低了总氧化状态，但端粒长度没动",
      "心理干预 RCT 的端粒终点", "生命历程", "A", "临床试验"),
 15: ("Cellular-Senescence-Vascular-Aging-Pulmonary-Hypertension-2026.html",
      "肺动脉高压里的血管衰老：从内皮修复失败到 ECM 硬化",
      "肺动脉高压的血管衰老框架", "细胞衰老", "C", "综述"),
 16: ("WEE1-Inhibition-Senescence-Epigenetic-GBM-2026.html",
      "抢在衰老之前：早期 WEE1 抑制阻断胶质母细胞瘤的衰老样重编程",
      "治疗诱导衰老的表观重编程", "细胞衰老", "B", "基础研究"),
 17: ("Neurodegeneration-Sub-Saharan-Africa-Exposome-2026.html",
      "撒哈拉以南非洲：被低估的「生物衰老→神经退行」天然实验场",
      "非洲场景下的衰老与神经退行", "神经退行", "C", "观点评论"),
 18: ("Cellular-Senescence-Neurodegeneration-Review-2026.html",
      "细胞衰老与神经退行：机制说得清，生物标志物仍缺位",
      "衰老细胞与神经退行综述", "细胞衰老", "C", "综述"),
 19: ("Spinach-RIP-mTOR-Colorectal-Cancer-2026.html",
      "菠菜核糖体失活蛋白：下调 AKT/mTOR，把 HT29 推向凋亡",
      "SoRIP 与 mTOR 通路", "代谢与营养", "B", "基础研究"),
 20: ("MOTS-c-LARS1-Lipophagy-Diabetic-Nephropathy-2026.html",
      "MOTS-c 下调 LARS1：用脂噬疏通糖尿病肾病的小管衰老",
      "MOTS-c 与脂噬抗肾小管衰老", "器官衰老", "B", "基础研究"),
 21: ("Selenium-Macrophage-Senescence-Ovarian-Fibrosis-2026.html",
      "硒如何挡住镉的卵巢毒性：先压住巨噬细胞的铁死亡与衰老",
      "巨噬细胞衰老与卵巢纤维化", "免疫与炎症", "B", "基础研究"),
 22: ("Fermented-Pomegranate-Brain-Aging-Microbiome-2026.html",
      "发酵石榴汁：经菌群-代谢物轴压住神经炎症与脑衰老通路",
      "发酵石榴汁与脑衰老", "神经退行", "B", "肠道菌群"),
 23: ("Autophagy-Activation-SMA-Lifespan-2026.html",
      "在 SMA 线虫里，激活自噬比抑制它更能改善神经肌肉功能",
      "自噬激活与 SMA 模型", "神经退行", "B", "基础研究"),
 24: ("Bone-Force-Sensing-Delays-Aging-2026.html",
      "骨细胞的力学感知：给老年小鼠加负荷，健康期与寿命一起延长",
      "骨机械感知与全身衰老", "器官衰老", "B", "基础研究"),
 25: ("Taurine-Inflammaging-NLRP3-Macrophage-2026.html",
      "牛磺酸随龄升高不是坏事：它是对炎症衰老的对映稳态反应",
      "牛磺酸与 NLRP3 炎症小体", "免疫与炎症", "B", "基础研究"),
 26: ("Neural-Representation-Geometry-Aging-MCI-2026.html",
      "健康老化的神经表征在扩张，MCI 与 AD 的却在坍缩",
      "神经表征几何与认知老化", "神经退行", "A", "脑衰老与认知"),
 27: ("Lipid-Composite-Indices-Vascular-Aging-2026.html",
      "12 个血脂复合指数：TyG 每增 1 单位，血管老化 OR 翻倍",
      "血脂复合指数与血管老化", "器官衰老", "A", "流行病学"),
 28: ("Aperiodic-EEG-Attentional-Aging-Marker-2026.html",
      "非周期性脑电的纵向下降，追的是加工速度而不是执行功能",
      "非周期性脑电与注意老化", "神经退行", "A", "脑衰老与认知"),
 29: ("Human-Milk-Oligosaccharides-Intestinal-Decline-2026.html",
      "3′-SL 与 LNnT：两种母乳寡糖如何减缓自然衰老的肠道退化",
      "母乳寡糖与肠道衰老", "器官衰老", "B", "肠道菌群"),
 30: ("Bibliometric-Cellular-Senescence-Heart-Failure-2026.html",
      "心衰中的细胞衰老：一张 2020 年后加速膨胀的文献地图",
      "心衰细胞衰老的文献计量", "细胞衰老", "C", "方法学"),
 31: ("Epigenetic-VSMC-Plasticity-Vascular-Aging-2026.html",
      "血管平滑肌细胞的表观可塑性：急性损伤与慢性衰老要两套打法",
      "VSMC 表观调控与血管衰老", "表观遗传", "C", "综述"),
 32: ("Equisetum-Polysaccharide-Obesity-Aged-Mice-2026.html",
      "木贼多糖：在被高脂饮食打乱的老年肠道里恢复多样性",
      "多糖干预与老年肥胖", "代谢与营养", "B", "肠道菌群"),
 33: ("NAD-Metabolic-Restoration-Lung-GVHD-2026.html",
      "恢复 NAD⁺ 代谢：把肺 GVHD 的抗炎与抗感染能力解耦",
      "NAD⁺ 代谢修复与肺 GVHD", "NAD+与sirtuin", "B", "基础研究"),
 34: ("Death-Receptors-IAP-Antagonist-Senolytics-2026.html",
      "衰老细胞对 IAP 成瘾：一条从死亡受体出发的 senolytic 路线",
      "死亡受体-IAP 轴与 senolytics", "细胞衰老", "B", "基础研究"),
 35: ("HAP40-Proteostasis-Huntingtin-2026.html",
      "HAP40 不只是亨廷顿蛋白的搭档，它是一个蛋白质稳态调控因子",
      "HAP40 与蛋白质稳态", "神经退行", "B", "蛋白质稳态"),
 36: ("Cellular-Senescence-CKD-Cardiac-Fibrosis-2026.html",
      "细胞衰老：慢性肾病与心脏纤维化之间那条共同机制",
      "衰老细胞与心肾纤维化", "细胞衰老", "C", "综述"),
 37: ("Resveratroloside-Mitochondria-Chromatin-Senescence-2026.html",
      "白藜芦醇糖苷：毒性更低，却同时改线粒体与染色质两头",
      "白藜芦醇糖苷的线粒体-染色质轴", "器官衰老", "B", "基础研究"),
 38: ("CCL11-Microglial-Reparative-ICH-Aged-Brain-2026.html",
      "循环 CCL11 是老年脑出血后修复失败的那个可靶向介质",
      "CCL11 与老年脑出血修复", "神经退行", "B", "基础研究"),
 39: ("SEPTIN6-HSC-Senescence-Congenital-Neutropenia-2026.html",
      "胚系 SEPTIN6 突变：让造血干细胞提前衰老，mTOR 抑制可挽救",
      "SEPTIN6 与造血干细胞衰老", "干细胞", "B", "基础研究"),
 40: ("Senescence-Signature-Breast-Cancer-Immunotherapy-2026.html",
      "衰老特征签名：给乳腺癌分层，并预测免疫治疗应答",
      "衰老签名与乳腺癌免疫治疗", "细胞衰老", "A", "计算生物学"),
 41: ("Anxiety-Trajectory-Hip-Fracture-Risk-2026.html",
      "焦虑症状的上升轨迹，把髋部骨折风险一起带上去了",
      "焦虑轨迹与髋部骨折", "生命历程", "A", "流行病学"),
 42: ("Burn-Survivors-80-Plus-Functional-Recovery-2026.html",
      "80 岁以上烧伤幸存者的功能悖论：身体很差，社会角色却在均值",
      "高龄烧伤幸存者的功能恢复", "生命历程", "A", "临床研究"),
 43: ("NCCRP1-Ovarian-Cancer-PI3K-AKT-mTOR-2026.html",
      "NCCRP1 拉高卵巢癌的线粒体呼吸，也拉高了转移与不良预后",
      "NCCRP1 与卵巢癌 mTOR 轴", "代谢与营养", "B", "基础研究"),
 44: ("HMMR-Colorectal-Carcinoma-mTOR-2026.html",
      "HMMR 经 PI3K/AKT/mTOR 推动结直肠癌的增殖与侵袭",
      "HMMR 与结直肠癌", "代谢与营养", "B", "基础研究"),
 45: ("Warm-Needling-Chondrocyte-Senescence-KOA-2026.html",
      "温针灸对膝骨关节炎大鼠软骨细胞衰老的调控效应",
      "温针灸与软骨细胞衰老", "器官衰老", "B", "基础研究"),
 46: ("Cardiometabolic-Pregnancy-Offspring-Biological-Ageing-2026.html",
      "妊娠期心脏代谢并发症：子代端粒没变，甲基化变了",
      "妊娠并发症与子代生物学老化", "生命历程", "A", "系统评价"),
 47: ("Nicotinamide-Riboside-Flap-Survival-Autophagy-2026.html",
      "NR 经 NAD⁺/SIRT1–FOXO1 增强自噬，提高皮瓣存活",
      "NR 与皮瓣存活的自噬通路", "NAD+与sirtuin", "B", "基础研究"),
 48: ("Cold-BH2-Metabolic-Network-Longevity-2026.html",
      "寒冷激活一条 BH2 代谢网络：只在肌肉里提速就够延寿",
      "寒冷-BH2 轴与长寿（Nature）", "代谢与营养", "B", "基础研究"),
 49: ("Proteostasis-Stress-SOD2-Localization-Senescence-2026.html",
      "蛋白质稳态应激让 SOD2 离开线粒体，而不是让它变少",
      "蛋白质稳态应激与 SOD2 错位", "线粒体", "B", "基础研究"),
 50: ("Frailty-Assessment-Ovarian-Cancer-Review-2026.html",
      "卵巢癌的衰弱评估：61 篇文献里只有一半真正在测衰弱",
      "卵巢癌衰弱评估的系统综述", "生命历程", "C", "系统评价"),
 51: ("Longevity-Thalassemia-Which-Clock-2026.html",
      "地中海贫血的长寿之问：我们要减速的究竟是哪个时钟",
      "地中海贫血与「该慢哪个钟」", "生命历程", "C", "观点评论"),
 52: ("Hyperfunction-Systemic-Amplification-Rejuvenation-2026.html",
      "从超功能到系统性放大：重写晚年加速的逻辑",
      "超功能理论与系统性放大", "细胞衰老", "C", "衰老理论"),
 53: ("Sarcopenia-Protein-Mediterranean-Diet-Review-2026.html",
      "肌少症的营养策略：蛋白策略与地中海式膳食的证据最一致",
      "肌少症营养策略的系统综述", "代谢与营养", "A", "系统评价"),
 54: ("Lithocholic-Acid-Microbial-Biotransformation-Anti-Aging-2026.html",
      "用米曲霉改造石胆酸：羟基化、甲酯化、乙酰化各改一次活性",
      "石胆酸的微生物转化与抗衰活性", "代谢与营养", "B", "基础研究"),
 55: ("Chalcone-Derivative-AMPK-Autophagy-Alzheimer-2026.html",
      "一个三氟甲基查尔酮：同时推自噬流与溶酶体，改善 Aβ/Tau 病理",
      "查尔酮衍生物与 AD 蛋白毒性", "神经退行", "B", "基础研究"),
 56: ("Platelet-Inflammation-Biological-Aging-Diabetes-2026.html",
      "血小板站到炎症衰老与表观遗传时钟之间：糖尿病队列的横断面证据",
      "血小板、炎症与生物学老化", "免疫与炎症", "A", "流行病学"),
 57: ("Intermittent-Fasting-Mediterranean-Inflammation-RCT-2026.html",
      "8 周膳食质量没降 CRP，是禁食带来的体重下降降了它",
      "禁食、体重与炎症的 RCT", "代谢与营养", "A", "临床试验"),
 58: ("Macrophage-Depletion-Aged-Kidney-Senescence-2026.html",
      "清除巨噬细胞能减老年肾的炎症与衰老，但高剂量伤肾",
      "巨噬细胞清除与肾脏衰老", "器官衰老", "B", "基础研究"),
 59: ("Interlimb-Coupling-Aging-Parkinson-Force-Control-2026.html",
      "老化与帕金森在力控任务上留下不同的肢体间耦合指纹",
      "肢体间耦合与老化/帕金森", "神经退行", "A", "临床研究"),
 60: ("Biological-Aging-Dietary-Biomarkers-Comment-2026.html",
      "是生物学老化还是膳食生物标志物？——膳食-衰老关联的解读之困",
      "膳食模式与生物学年龄的因果解读", "代谢与营养", "C", "观点评论"),
 61: ("Cellular-Senescence-Skeletal-Muscle-Review-2026.html",
      "骨骼肌里的衰老细胞：它们通过 SASP 重塑整个肌组织微环境",
      "骨骼肌细胞衰老综述", "器官衰老", "C", "综述"),
 62: ("Plant-Based-Diet-Frailty-Multicohort-2026.html",
      "植物性膳食与衰弱：健康指数 OR 0.71–0.80，不健康的反过来",
      "植物性膳食指数与衰弱", "代谢与营养", "A", "流行病学"),
 63: ("Multimorbidity-Economic-Burden-Aging-2026.html",
      "多重共病的双重负担：2000–2023 年的 YLD 与经济代价",
      "多重共病的经济负担", "生命历程", "A", "流行病学"),
 64: ("Particulate-Matter-Cardiovascular-Aging-Framework-2026.html",
      "颗粒物暴露是「加速老化」还是可逆毒性：用时间维度分辨",
      "颗粒物暴露与心血管老化框架", "器官衰老", "C", "观点评论"),
 65: ("Neuroinflammatory-Resolution-Failure-Brain-Aging-2026.html",
      "脑老化里的炎症不消退：一个以「恢复」为导向的小胶质细胞框架",
      "神经炎症消退失败与脑老化", "免疫与炎症", "C", "综述"),
 66: ("Accelerated-Epigenetic-Aging-Frontotemporal-Dementia-2026.html",
      "额颞叶痴呆的表观年龄加速 +1.17 年，指向吸烟、炎症与糖代谢",
      "FTD 的表观遗传年龄加速", "表观遗传时钟", "A", "生物标志物"),
 67: ("Interpretable-Deep-Learning-Brain-Age-Review-2026.html",
      "可解释深度学习做脑龄预测：从局部归因走向解剖学意义表征",
      "可解释深度学习与脑龄预测", "方法与工具", "C", "方法学"),
 68: ("Intrinsic-Capacity-Decline-Frailty-Fall-Risk-2026.html",
      "内在能力下降：89% 的社区老人有，运动域最先掉",
      "内在能力下降与跌倒风险", "生命历程", "A", "临床研究"),
}


def md2html(s):
    """卡片字段是 markdown 片段：加粗 + 列表项 + 段落。"""
    if not s:
        return ""
    s = s.replace('\r', '')
    out, buf = [], []
    for line in s.split('\n'):
        line = line.strip()
        if not line:
            continue
        item = re.match(r'^[-*]\s+(.*)$', line)
        if item:
            if buf:
                out.append('<p>' + ' '.join(buf) + '</p>')
                buf = []
            out.append('<li>' + item.group(1) + '</li>')
        else:
            buf.append(line)
    if buf:
        out.append('<p>' + ' '.join(buf) + '</p>')
    txt = '\n'.join(out)
    txt = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', txt)

    def wrap_ul(m):
        return '<ul>\n' + m.group(0) + '\n</ul>'
    txt = re.sub(r'(?:<li>.*?</li>\n?)+', wrap_ul, txt)
    return txt


def esc_plain(s, n=200):
    """desc：去 markdown 标记后截断。"""
    t = re.sub(r'\*\*(.+?)\*\*', r'\1', s or '')
    t = re.sub(r'\s+', ' ', t).strip(' -·')
    return t[:n]


def lit_src(c):
    j = re.sub(r'\*\*', '', c['journal'] or '')
    bits = ['<em>' + html.escape(j) + '</em>']
    if c['pmid']:
        bits.append('PMID ' + c['pmid'])
    if c['doi']:
        bits.append('DOI <a href="https://doi.org/' + c['doi'] + '" target="_blank" '
                    'rel="noopener noreferrer">' + c['doi'] + '</a>')
    bits.append('来源：' + SRC_CARD + ' · <strong>摘要级，未核验全文</strong>')
    return ' · '.join(bits)


def body_of(c):
    parts = ['<p><em>数据日期 ' + DATA_DATE + ' · 生成时间 ' + GEN_AT + '</em></p>']
    parts.append('<p><strong>档位说明：</strong>本文为<strong>摘要级</strong>卡片，'
                 '仅依据期刊公开摘要与 PubMed 元数据撰写，'
                 '<strong>付费墙全文未获取、未逐节核验</strong>；'
                 '摘要中被截断或不可见的效应量，本站不做任何推算补全。</p>')
    if c['question']:
        parts.append('<h2>研究问题</h2>' + md2html(c['question']))
    if c['method']:
        parts.append('<h2>方法</h2>' + md2html(c['method']))
    if c['conclusion']:
        parts.append('<h2>核心结论</h2>' + md2html(c['conclusion']))
    if c['limit']:
        parts.append('<h2>局限</h2>' + md2html(c['limit']))
    if c['value']:
        parts.append('<h2>对本项目的价值</h2>' + md2html(c['value']))
    en_title = html.escape(c['title'])
    jn = html.escape(re.sub(r'\*\*', '', c['journal'] or ''))
    parts.append('<h2>原文题录</h2><ul>'
                 '<li>英文标题：' + en_title + '</li>'
                 '<li>期刊与标识：' + jn + '</li>'
                 '</ul>')
    return '\n\n'.join(parts)


def main():
    arts = json.load(open(os.path.join(ROOT, 'data/articles.json'), encoding='utf-8'))
    existing = {a['slug'] for a in arts}
    A = {}
    dup_here = []
    for idx, (slug, title, crumb, topic, ev, tag) in sorted(M.items()):
        if slug in existing or slug in A or os.path.exists(os.path.join(ROOT, 'news', slug)):
            dup_here.append(slug)
            continue
        c = AB[idx]
        A[slug] = dict(
            topic=topic, ev=ev, tag=tag,
            title=title, crumb=crumb,
            desc=esc_plain(c['conclusion'] or c['question'], 190),
            source=lit_src(c),
            body=body_of(c),
            related=[],
        )
    print("本批成篇 %d 篇 · 站内/本批已存在跳过 %d" % (len(A), len(dup_here)))
    if dup_here:
        print('  跳过：', dup_here)

    sys.argv = ["gen_articles.py", ROOT, "/dev/null", DATE]
    _spec = importlib.util.spec_from_file_location(
        "ga", os.path.join(ROOT, "scripts", "gen_articles.py"))
    ga = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(ga)
    ga.A = A
    ga.main()


if __name__ == "__main__":
    main()
