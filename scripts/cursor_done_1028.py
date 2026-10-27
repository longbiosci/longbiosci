#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cursor_done_1028.py —— 第 16 轮（2026-10-28 05:30 班）游标批量收尾

硬规则：游标记录每个 file_id 的处理状态，不依赖对话记忆。
本脚本把本轮 43 个实际下载核验过的产出一次性落游标（status + hash + slugs + note），
幂等：重复运行只更新记录。
"""
import csv
import json
import os
import re
import subprocess
import sys

ROOT = "/workspace/longbiosci"
RAW = os.path.join(ROOT, ".intake", "raw", "1028")
SIZES = json.load(open(os.path.join(ROOT, ".intake", "sizes-1028.json"), encoding="utf-8"))
ITEMS = json.load(open(os.path.join(RAW, "dfPCBwYantrz___items"), encoding="utf-8"))

rows = {r["file_id"]: r for r in csv.DictReader(
    open(os.path.join(ROOT, "data", "intake-manifest.tsv"), encoding="utf-8"), delimiter="\t")}


def slug_of(doi):
    return "Preprint-" + re.sub(r"[^0-9A-Za-z]+", "-", doi).strip("-") + "-2026.html"


# 批次 a：26 条中 25 篇上站（10.64898/2026.10.11.758291 站内已有，规则④跳过）
SKIP_A = "10.64898/2026.10.11.758291"
slugs_a = [slug_of(it["doi"]) for it in ITEMS if it["doi"] != SKIP_A]

# 批次 b：15 篇产业文章（与 gen_articles_intake_2026-10-28b.py 的 A 键一致）
import importlib.util
_spec = importlib.util.spec_from_file_location(
    "b28", os.path.join(ROOT, "scripts", "gen_articles_intake_2026-10-28b.py"))
b28 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(b28)
slugs_b = list(b28.A.keys())

POD = [f"podcast/ep{i:03d}" for i in range(27, 36)]

NOTE = {
    # 文献层
    "dtRtWuzsKAUz": "速递母文件；26 条真实 DOI 已由《预印本全文级解读_2026-10-28》全覆盖（25 篇上站，1 条规则④已上站跳过）；速递正文「今日观察」为条目评论，不单独成篇",
    "dpnLrBCASvgV": "xlsx 汇总表（Microsoft Excel 2007+，实测 30,105 B）；26 条条目已由解读批次全覆盖",
    # 行业层
    "dmsATtPgKteT": "管线状态基线 v1.0（JSON，19,435 B）；行业结构回撤（Unity 停运 / Turn Bio 资产流失）已由批次 b 成篇 1 篇，基线快照本身不单独上站",
    "dauTkaOpIygl": "同名两份交付之一，实测为 xlsx 表格版（50,911 B）；与 dfCLxqSPNKoU（md 版）同源，按规则④不重复成篇",
    "dfCLxqSPNKoU": "同名两份交付之一，实测为真 md 报告（55,044 B，四表结构）；批次 b 成篇 15 篇；§3 #10 Eos 周报自述已上站、§6 待核实区 3 条不成篇",
    # 元层 · 交付包 / 非产出
    "dbZAxUiJXMff": "历史交付包（10-27 已推送完成，提交 60ad7ce928），无待消化内容",
    "daOaqmbrDKDw": "播客 ep027–ep035 增量包（tar，23,603,200 B）；音频 9 个 + 文稿 9 份 + podcast.json 35 期已接入，页面/RSS 由管线环节 8 重建；包内 index.html/sitemap.xml 为旧基线未采用",
    "dfLQXQxzlQEV": "GitHub 凭证文件（93 B），非内容产出",
    "dlyTXAelaRdq": "历史交付包（午刊 10-27，已上线），无待消化内容",
    "dfPCBwYantrz": "解读批次索引（_items，26 条），已全部消化",
    "dEqVnNUzEkuZ": "26 篇解读的 tar 打包副本，内容已由单篇逐一消化，不重复处理",
    "dTCUavEKmZaS": "流水线运行日志副本，无上站内容",
    "dUBjzmhPtlOB": "与 dVdAvVgUAvkp 内容完全相同（md5 8fb6b22b…），同名重复交付，按规则④不重复处理",
    "dVdAvVgUAvkp": "运行总结；本轮 26 篇 / A 档 8 / C 档 18 / 欠账清偿 0，已核对",
    # 滚动更新
    "dVKsSOJcCMjU": "同名滚动更新（mtime 变、哈希不同）；实测为 xlsx 载体，内容与已消化的 09-16 周报同源，不重复成篇",
    "duLHFqzcdVBY": "元层运营待办清单滚动更新（mtime 10-27 21:27）；协作文档，本轮已读取吸收，不覆盖网站层同名文件",
    "dcRhMjctGcjp": "元层运营日志滚动更新（mtime 10-27 21:26，含第 15 轮 21:45 留痕与 P2-29/P3-10）；协作文档，本轮已读取吸收",
}

SLUGS = {}
for it in ITEMS:
    fid = None
    stem = it["file"][:-3] if it["file"].endswith(".md") else it["file"]
    for f in os.listdir(RAW):
        if stem in f:
            fid = f.split("__")[0]
            break
    if fid and it["doi"] != SKIP_A:
        SLUGS[fid] = [slug_of(it["doi"])]
SLUGS["dfCLxqSPNKoU"] = slugs_b
SLUGS["daOaqmbrDKDw"] = POD
SLUGS["dmsATtPgKteT"] = ["Longevity-Industry-Retrenchment-Unity-Turn-Bio-2026.html"]
SLUGS["dtRtWuzsKAUz"] = slugs_a
SLUGS["dpnLrBCASvgV"] = []
SLUGS["dfPCBwYantrz"] = slugs_a


def run(fid, slugs, note):
    h = SIZES.get(fid, {}).get("md5", "")
    cmd = ["python3", "scripts/cursor.py", "done", "--repo", ".",
           "--file-id", fid, "--note", note, "--hash", h]
    if slugs:
        cmd += ["--slugs"] + slugs
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    print((r.stdout or r.stderr).strip()[:150])


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
