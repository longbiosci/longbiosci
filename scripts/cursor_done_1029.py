#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cursor_done_1029.py —— 第 17 轮（2026-10-29 05:30 班）游标批量收尾

硬规则：游标记录每个 file_id 的处理状态，不依赖对话记忆。
本脚本把本轮 13 个实际下载核验过的产出一次性落游标（status + hash + slugs + note），
幂等：重复运行只更新记录。
"""
import csv
import json
import os
import subprocess

ROOT = "/workspace/longbiosci"
SIZES = json.load(open(os.path.join(ROOT, ".intake", "sizes-1029.json"),
                       encoding="utf-8"))

rows = {r["file_id"]: r for r in csv.DictReader(
    open(os.path.join(ROOT, "data", "intake-manifest.tsv"),
         encoding="utf-8"), delimiter="\t")}


def slugs_from_map():
    """274 篇新稿的 slug（与 gen_articles_intake_2026-10-29a.py 的映射一致）"""
    src = open(os.path.join(ROOT, "scripts",
                            "gen_articles_intake_2026-10-29a.py"),
               encoding="utf-8").read()
    ns = {"__name__": "x", "__file__": "y"}
    exec(compile(src.rsplit("def main()", 1)[0], "i", "exec"), ns)
    out = []
    for p in ns["MAP_FILES"]:
        for num, slug, title, crumb in json.load(open(p, encoding="utf-8")):
            out.append(slug)
    return out


UP_SLUGS = [
    "Cold-BH2-Metabolic-Network-Longevity-2026.html",
    "Endothelial-Cell-Aging-Single-Cell-Atlas-2026.html",
    "Death-Receptors-IAP-Antagonist-Senolytics-2026.html",
    "NAD-Metabolic-Restoration-Lung-GVHD-2026.html",
    "Multimorbidity-Economic-Burden-Aging-2026.html",
    "CCL11-Microglial-Reparative-ICH-Aged-Brain-2026.html",
    "Nutrition-Inflammation-Index-Vascular-Aging-Mortality-2026.html",
    "Biological-Age-CVD-Hospitalization-Risk-2026.html",
    "Accelerated-Brain-Aging-Executive-Deficits-2026.html",
    "Autophagy-Activation-SMA-Lifespan-2026.html",
    "Home-Use-LED-Mask-Cream-Anti-Aging-2026.html",
]

NOTE = {
    # 文献层 —— 本轮唯一的内容产出
    "dGBunAeRiRlm":
        "285 张卡片全量消化：274 篇新稿上站（199 全文级 / 75 摘要级，A111/B69/C94）+ "
        "U01–U11 付费墙回捞 11 篇原地升级（不占新页）；规则④查重 DOI 命中 0、PMID 命中 11 "
        "（全部为升级条目，故不新建页面）；每张新页带数据日期/生成时间标签",
    "dZRISkLBlBMk":
        "总览 xlsx 版（file_id dZRISkLBlBMk）：经在线文档再导出通道，实测 5,677 B，"
        "与 dmaqQuEoiQgX 字节数完全相同，**非可从字节核验是否完整**；"
        "内容已被 dGBunAeRiRlm 卡片全覆盖，不重复成篇",
    "dmaqQuEoiQgX":
        "总览 csv 版：同 dZRISkLBlBMk，实测 5,677 B 同规格空壳；"
        "内容已被卡片全覆盖，不重复成篇",
    # 元层
    "dPChwCcGPgui":
        "午刊 2026-10-28 已上站留档 tar（257,599 B）；上游自述已上线，本班不重复消化",
    "dMNQhEqhmyEO":
        "人工待下载清单（滚动更新，实测 48,647 B）；清单职责是登记缺口，本轮无可成篇内容",
    "duLHFqzcdVBY":
        "元层运营待办清单（滚动更新，实测 205,205 B）；协作文档，本轮已读取吸收并回写回传，"
        "不覆盖网站层同名文件",
    "dcRhMjctGcjp":
        "元层运营日志（滚动更新，实测 242,502 B）；协作文档，本轮留痕已并入并回传两层",
    "dTCUavEKmZaS":
        "预印本解读日志副本（12,270 B）；cursor seen 判 UNCHANGED（与 10-28 已消化件同哈希），"
        "无上站内容",
    "dUBjzmhPtlOB":
        "预印本解读运行总结（18,005 B）；cursor seen 判 UNCHANGED，无上站内容",
    # 行业层
    "dfCLxqSPNKoU":
        "行业情报周报 2026-10-28（md 版，55,044 B）；第 16 轮已消化成篇 15 篇，"
        "cursor seen 判 UNCHANGED",
    "dVKsSOJcCMjU":
        "行业情报周报 2026-09-16（滚动更新，17,543 B）；内容与已消化版本同源，"
        "cursor seen 判 UNCHANGED，不重复成篇",
    # 网站层 —— 与元层互为内容重复
    "dVisoPwrcwVm":
        "网站层运营待办清单（188,866 B）；与元层 duLHFqzcdVBY 内容哈希相同，"
        "cursor seen 判 DUPLICATE，按规则④不重复处理",
    "dRlRAPWevRku":
        "网站层运营日志（237,337 B）；与元层 dcRhMjctGcjp 内容哈希相同，"
        "cursor seen 判 DUPLICATE，按规则④不重复处理",
}

SLUGS = {
    "dGBunAeRiRlm": slugs_from_map() + UP_SLUGS,
    "dZRISkLBlBMk": [],
    "dmaqQuEoiQgX": [],
    "dPChwCcGPgui": [],
    "dMNQhEqhmyEO": [],
    "duLHFqzcdVBY": [],
    "dcRhMjctGcjp": [],
    "dTCUavEKmZaS": [],
    "dUBjzmhPtlOB": [],
    "dfCLxqSPNKoU": [],
    "dVKsSOJcCMjU": [],
    "dVisoPwrcwVm": [],
    "dRlRAPWevRku": [],
}


def run(fid, slugs, note):
    h = SIZES.get(fid, {}).get("md5", "")
    cmd = ["python3", "scripts/cursor.py", "done", "--repo", ".",
           "--file-id", fid, "--note", note, "--hash", h]
    if slugs:
        cmd += ["--slugs"] + slugs
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    print((r.stdout or r.stderr).strip()[:200])


def main():
    n = 0
    for fid in SIZES:
        if fid not in rows:
            print(f"  ⚠ {fid} 不在清单里，跳过")
            continue
        run(fid, SLUGS.get(fid, []), NOTE.get(fid, "本轮已消化"))
        n += 1
    print(f"\n游标落库 {n} 条")


if __name__ == "__main__":
    main()
