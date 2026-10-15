"""漏收判定器 —— 三路匹配，宁可误判为「已收录」也不重复上线。

判定依据（按优先级）：
  1. DOI 精确匹配：文章 HTML 里出现该 DOI
  2. slug 机制词命中：slug 含该研究的核心分子/基因/方法名
  3. 标题高相似：中文标题去除标点后 3-gram 重合度 ≥ 阈值
只有三路全部判否，才算「漏收」。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
arts = json.load(open(ROOT / "data/articles.json", encoding="utf-8"))

# --- 建立全库索引 ---
html_dois = set()
for p in (ROOT / "news").glob("*.html"):
    t = p.read_text(encoding="utf-8", errors="ignore")
    for m in re.findall(r"10\.\d{4,9}/[^\s\"'<>,;)\]]+", t):
        html_dois.add(m.rstrip(".").lower())

slugs = [a.get("slug", "") for a in arts]
titles = [a.get("title", "") for a in arts]


def ngram(s, n=3):
    s = re.sub(r"[^\w一-鿿]+", "", s)
    return {s[i:i + n] for i in range(len(s) - n + 1)}


title_ng = [ngram(t) for t in titles]


def title_sim(t, i):
    a = ngram(t)
    if not a:
        return 0.0
    b = title_ng[i]
    return len(a & b) / len(a | b)


# 每篇参考条目的机制关键词（人工从标题/要点抽取，用于 slug 匹配）
MECH = {
    "C01": ["pseudocatenulatum", "5-AVAB", "Microbiome-Bifidobacterium"],
    "C02": ["Cyclin-D1-CDK6", "Palbociclib-CCND1", "CDK6-SASP"],
    "C03": ["Plb1", "Lipid-Aging", "Elongation-Lipid"],
    "C04": ["CMA", "Chaperone-Mediated-Autophagy", "LAMP2A"],
    "C05": ["Abemaciclib", "CDK4-6-RAR", "Senomorphic-CDK"],
    "C06": ["cGAS-Deficient", "LINE1", "cGAS-LINE1"],
    "C07": ["Glucocorticoid", "ACBP", "Glucocorticoid-Aging"],
    "C08": ["PD-L2"],
    "C09": ["Stiffness-ECM", "Fibrosis-ECM", "Aging-Sclerosis"],
    "C10": ["Aging-vs-Biological-Age", "Biological-Age-Concept"],
    "C11": ["Protein-Restriction"],
    "C12": ["Fisetin", "Senotherapeutics", "SR29384"],
    "C13": ["Chronic-Senolytic", "Myocardial", "Aerobic-Exercise-Heart"],
    "C14": ["Antiaging-Strategy", "Mechanistic-Framework", "Senotherapy-Framework"],
    "C15": ["GHR", "Growth-Hormone-Receptor", "Hepatocyte-GHR"],
    "C16": ["SIRT1-L1", "L1-Retrotransposon", "SIRT1-Heterochromatin"],
    "C17": ["uPAR", "T-Cell-Engager", "GFD-CD3"],
    "C18": ["ChromAgeNet", "Chromatin-HSC", "Deep-Learning-HSC"],
    "C19": ["Dermatology-Senolytic", "Skin-Senolytic"],
    "C20": ["NHP-Plasma-CSF", "Macaque-Proteomic", "NHP-Proteomic"],
    "C21": ["NAD-Frailty", "Itabashi", "Blood-NAD-Frailty"],
    "C22": ["Chemotherapy-Bone-Loss", "Bone-Loss-Senolytic"],
    "C23": ["Healthspan-Not-Lifespan", "Healthspan-Cliché"],
    "C24": ["LongevityBench"],
    "C25": ["Caloric-Restriction-Mutation", "Somatic-Mutation-CR"],
    "C26": ["Nefh", "Glutamatergic", "Skin-Innervation"],
}


def judge(rec):
    doi = (rec.get("doi") or "").lower()
    code = None
    m = re.match(r"C(\d+)", rec["title"])
    if m:
        code = f"C{int(m.group(1)):02d}"
    # 1) DOI
    if doi and doi in html_dois:
        return "已收录", f"DOI 命中 {doi}"
    # 2) slug 机制词
    hits = [k for k in MECH.get(code, []) if any(k.lower() in s.lower() for s in slugs)]
    if hits:
        return "已收录", f"slug 命中 {hits}"
    # 3) 标题相似
    best, bi = 0.0, -1
    for i, t in enumerate(titles):
        s = title_sim(rec["title"], i)
        if s > best:
            best, bi = s, i
    if best >= 0.34:
        return "已收录", f"标题相似 {best:.2f} → {titles[bi][:34]}"
    return "漏收", f"三路均未命中（标题最高相似 {best:.2f}）"


if __name__ == "__main__":
    recs = json.load(open(sys.argv[2], encoding="utf-8"))
    out = []
    for r in recs:
        st, why = judge(r)
        r["status"], r["reason"] = st, why
        out.append(r)
    json.dump(out, open(sys.argv[3], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    miss = [r for r in out if r["status"] == "漏收"]
    hit = [r for r in out if r["status"] == "已收录"]
    print(f"总 {len(out)}｜漏收 {len(miss)}｜已收录 {len(hit)}")
    print("\n--- 已收录（不重复上线）---")
    for r in hit:
        print(f"  {r['title'][:44]:46s} {r['reason']}")
    print("\n--- 漏收（待补）---")
    for r in miss:
        print(f"  {r['no']:>2} {r['topic']:6s} {r['ev']}  {r['title'][:52]}")