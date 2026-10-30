#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cursor_done_1031.py —— 第 20 轮（2026-10-31 05:30 班）轮末游标落库

硬规则遵循
────────
1. 每个 file_id 都有明确状态（done / empty），不依赖对话记忆。
2. 判空一律以**实际下载字节 + 内容解析**为准，不信 dir_list 的 size。
3. 每个 done 记录带内容 md5，下一轮 seen 才有判重基准。

本轮处置
────────
· 元层《预印本全文级解读_2026-10-31》73 个解读页 → done
  （72 篇上站；主榜 19 查重跳过——DOI 精确命中站内且正文含该 DOI）
· 批次配套 6 件（总索引 / 运行摘要 / 日志副本 / _items / 全集.tar + 根目录留痕 2 件）→ done
· 文献层《预印本速递_2026-10-31》及其总表 → done（上游源，已由元层批次消化）
· 文献层《文献监控_2026-10-29_总览》×2 → ⛔ empty（重跑后**仍为空壳**，需再重跑 7762989）
· 文献层《文献监控_2026-10-29_卡片》→ done（seen 判 UNCHANGED，仅哈希刷新）
· 行业层《行业情报周报_2026-09-16》滚动更新 → done（三表 17 个主体全部站内已覆盖）
"""
import csv
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CURSOR = os.path.join(ROOT, "data/intake-cursor.json")
MANIFEST = os.path.join(ROOT, "data/intake-manifest.tsv")
BD = os.path.join(ROOT, ".intake/raw/tar1031/预印本全文级解读_2026-10-31")
SKIP_DOI = "10.64898/2026.05.01.26352140"


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def main():
    man = {r["file_id"]: r for r in csv.DictReader(
        open(MANIFEST, encoding="utf-8"), delimiter="\t")}
    cur = json.load(open(CURSOR, encoding="utf-8"))
    ent = cur["entries"]

    # ── 复算本轮 slug（与成稿脚本同一套规则） ──
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "g", os.path.join(ROOT, "scripts/gen_articles_intake_2026-10-31a.py"))
    g = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g)

    arts = json.load(open(os.path.join(ROOT, "data/articles.json"), encoding="utf-8"))
    new_slugs = {a["slug"] for a in arts if a.get("date") == "2026-10-31"}

    items = json.load(open(os.path.join(BD, "_items.json"), encoding="utf-8"))
    slug_of, used = {}, set()
    for it in items:
        if it["doi"] == SKIP_DOI:
            continue
        p = os.path.join(BD, it["file"])
        _, tc, secs = g.parse_md(p)
        meta = g.meta_table(secs.get(0, ""))
        te = g.strip_md(meta.get("标题（原文）", "")) or it.get("title_orig", "")
        base = g.slugify(te)
        s, n = base, 1
        while s in used:
            n += 1
            s = base.replace(".html", f"-{n}.html")
        used.add(s)
        slug_of[it["file"]] = s

    # 只认真正落到 news/ 的 slug
    slug_of = {k: v for k, v in slug_of.items() if v in new_slugs}

    now = "2026-10-31T05:30:00+08:00"
    n_done = n_empty = 0

    def put(fid, status, slugs=None, note="", h=""):
        nonlocal n_done, n_empty
        m = man.get(fid)
        if not m:
            print(f"  ⚠ {fid} 不在清单，跳过")
            return
        ent[fid] = {
            "name": m["name"], "layer": m["layer"],
            "size": int(m["size"] or 0), "mtime": m["modify_time"],
            "status": status, "done_at": now,
            "slugs": slugs or [], "note": note, "hash": h,
        }
        if status == "done":
            n_done += 1
        else:
            n_empty += 1

    # ── 1) 73 个解读页 ──
    for it in items:
        fn = it["file"]
        fid = None
        for k, m in man.items():
            if m["name"].endswith("/" + fn[:-3]) or m["name"] == fn[:-3]:
                fid = k
                break
        if not fid:
            print(f"  ⚠ 找不到 file_id：{fn}")
            continue
        p = os.path.join(BD, fn)
        h = md5(p) if os.path.exists(p) else ""
        if it["doi"] == SKIP_DOI:
            put(fid, "done", [], "查重跳过：DOI 精确命中站内 "
                "Peripheral-Epigenetic-Aging-Centenarians-2026.html 且该页正文含本 DOI，"
                "不重复成篇（本轮跳过计数 +1）", h)
        else:
            s = slug_of.get(fn)
            put(fid, "done", [s] if s else [],
                f"已上站：{s}（数据日期 {it['data_date']}，时间标签 生成时间 2026-10-31 05:30）"
                if s else "成稿但未落 slug", h)

    # ── 2) 批次配套 ──
    for fid, note, local in (
        ("dOPAHGhHVZOl", "总索引：本批 73 篇的机读目录，不单独成篇", ".intake/raw/dOPAHGhHVZOl"),
        ("dptYMNcBrauv", "运行摘要（目录内）：留痕件，不单独成篇；载明本批 74→73、全文通道全线 403",
         ".intake/raw/dptYMNcBrauv"),
        ("dKxOKqqdZpcV", "日志副本（目录内）：留痕件，278 B，不单独成篇", ".intake/raw/dKxOKqqdZpcV"),
        ("dcMpxitvxhSW", "全集打包 tar：与 73 个单页同源、字节逐条一致，不重复消化",
         ".intake/raw/dcMpxitvxhSW"),
        ("dzkmRnWewTGc", "_items 机读清单：73 条元数据，已用于本轮成稿与查重，不单独成篇", ""),
        ("dLcQEtksReSf", "运行摘要（元层根目录留痕）：与目录内 dptYMNcBrauv 同名同内容，DUPLICATE", ""),
        ("dHDZombEBAEE", "日志副本（元层根目录留痕）：与目录内 dKxOKqqdZpcV 同名同内容，DUPLICATE", ""),
    ):
        h = md5(os.path.join(ROOT, local)) if local and os.path.exists(os.path.join(ROOT, local)) else ""
        put(fid, "done", [], note, h)

    # ── 3) 文献层 ──
    put("dENskhRbTohZ", "done", [],
        "上游源《预印本速递_2026-10-31》（232,160 B，交付主榜 21 + 观察哨 53 = 74 条）；"
        "已由元层《预印本全文级解读_2026-10-31》73 篇成稿消化，本件不重复成篇",
        md5(os.path.join(ROOT, ".intake/raw/preprint-express-1031")))
    put("dzHcjRDLvvGu", "done", [],
        "《预印本速递_总表_2026-10-31增量》xlsx：与速递 md 同源不同载体，不重复成篇",
        md5(os.path.join(ROOT, ".intake/raw/preprint-table-1031")))
    put("dGBunAeRiRlm", "done", [],
        "seen 判 UNCHANGED（内容哈希一致，mtime 未变、仅 size 缓存修正）；10-29 已消化",
        md5(os.path.join(ROOT, ".intake/raw/u_dGBunAeRiRlm")))
    # ── 判空告警：重跑后仍为空壳 ──
    ALERT = ("⛔ 空壳（第二道闸判出）：实测 5,676 B 但 xl/worksheets/sheet1.xml 的 "
             "<sheetData/> 为空节点、<row> 数 0，零数据行；名为 .csv 的那份实体也是 xlsx。"
             "10-30 轮已判空并告警，本轮 mtime 变化后**再次实际下载核验，仍为空壳** —— "
             "任务已被重跑但产出依旧失败，需再重跑 **7762989（重点期刊监控·每周五）**。"
             "同批《文献监控_2026-10-29_卡片》692,872 B 完好且已消化，故不影响已上站内容。")
    put("dZRISkLBlBMk", "empty", [], ALERT,
        md5(os.path.join(ROOT, ".intake/raw/verify_dZRISkLBlBMk")))
    put("dmaqQuEoiQgX", "empty", [], ALERT,
        md5(os.path.join(ROOT, ".intake/raw/verify_dmaqQuEoiQgX")))

    # ── 4) 行业层 ──
    put("dVKsSOJcCMjU", "done", [],
        "滚动更新（17,543 B，mtime 2026-10-29 08:07）：2026-W38 行业周报 xlsx 三表版。"
        "与已消化的 md 版同源；本轮逐条核验三表 17 个主体（公司/监管机构）**站内全部已覆盖**，"
        "无新增条目，不重复成篇。哈希基准已刷新",
        md5(os.path.join(ROOT, ".intake/raw/u_dVKsSOJcCMjU")))

    cur["updated_at"] = now
    json.dump(cur, open(CURSOR, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"✔ 落库完成：done {n_done} 条 / empty {n_empty} 条；游标共 {len(ent)} 条")


if __name__ == "__main__":
    main()
