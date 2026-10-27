#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merge_podcast_1028.py —— 05:30 班第 16 轮 · 播客 ep027–ep035 接入

消化对象
────────
《LongBiosci_播客_ep027-ep035_增量_待推送_2026-10-28》（元层 file_id
`daOaqmbrDKDw`，实测 **23,603,200 B**，POSIX tar）。

判空（硬规则）：实际下载核验，实测字节数 == 缓存值，非空产出。

为什么只取三类文件，不全量解包覆盖
──────────────────────────────────
包内除音频与文稿外还含 `index.html` / `sitemap.xml` / `docs/运营日志.md` /
`podcast.xml` / `podcast/index.html`。这些是**生成物或协作文档**：
  · 直接覆盖 index.html / sitemap.xml 会把本站本轮新增的 40 篇文章挤出去
    （包是按「基线 0fb834a」打的，不含本轮内容）；
  · podcast.xml / podcast/index.html 由管线环节 8（gen-podcast.py）重建，
    交给生成器比交给包更可靠；
  · docs/运营日志.md 是协作文档，本轮另有元层同名著者，不覆盖。
故只取 **audio/*.mp3（9 个）+ podcast/transcripts/*.md（9 份）
+ data/podcast.json（35 期全量，经验证含 ep001–ep026 全部）**。

四路去重（沿用包内红线）：slug / title / article_slugs / DOI 对 ep001–ep035
全量比对，重复即拒绝。

时间标签（规则③）：data_datetime=2026-10-22 18:32，generated_at=2026-10-28 03:39，
取自包内推送说明，**不用本轮巡检时刻冒替上游生成时点**。
"""
import hashlib
import json
import os
import shutil
import sys

ROOT = "/workspace/longbiosci"
SRC = "/tmp/pod28"


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    # ── ① 校验包完整性（SHA256SUMS.txt） ──
    sums = {}
    for line in open(os.path.join(SRC, "SHA256SUMS.txt"), encoding="utf-8"):
        c = line.split()
        if len(c) >= 2:
            sums[c[-1].lstrip("*")] = c[0]
    bad = [k for k, v in sums.items()
           if not os.path.exists(os.path.join(SRC, k))
           or sha(os.path.join(SRC, k)) != v]
    print(f"① 包内 SHA256 校验：{len(sums)} 条，不符 {len(bad)} 条")
    if bad:
        sys.exit(f"✗ 校验失败：{bad}")

    # ── ② 载入包内与本地 podcast.json，确认 ep001–ep026 无损失 ──
    new = json.load(open(os.path.join(SRC, "data", "podcast.json"), encoding="utf-8"))
    old = json.load(open(os.path.join(ROOT, "data", "podcast.json"), encoding="utf-8"))
    n_eps, o_eps = new["episodes"], old["episodes"]
    old_ids = {e["id"] for e in o_eps}
    new_ids = {e["id"] for e in n_eps}
    lost = old_ids - new_ids
    print(f"② 期数 本地 {len(o_eps)} → 包内 {len(n_eps)}；本地期号被包内丢失 {len(lost)} 期")
    if lost:
        sys.exit(f"✗ 包会抹掉已有期号：{sorted(lost)}")
    # 前 26 期内容是否被动过（slug + title 比对）
    drift = []
    om = {e["id"]: e for e in o_eps}
    for e in n_eps:
        if e["id"] in om and (om[e["id"]]["slug"] != e["slug"]
                              or om[e["id"]]["title"] != e["title"]):
            drift.append(e["id"])
    print(f"   前 26 期 slug/title 漂移：{len(drift)} 期")
    if drift:
        sys.exit(f"✗ 历史期号被改写：{drift}")

    # ── ③ 四路去重 ──
    def key(e):
        return (e["slug"], e["title"].strip(),
                tuple(sorted(e.get("article_slugs") or [])),
                tuple(sorted((s.get("doi") or "") for s in e.get("sources") or [])))
    seen, dup = set(), []
    for e in n_eps:
        k = key(e)
        if k in seen:
            dup.append(e["id"])
        seen.add(k)
    print(f"③ 四路去重（slug/title/article_slugs/DOI）：重复 {len(dup)} 期")
    if dup:
        sys.exit(f"✗ 重复期号：{dup}")

    # ── ④ 音频与文稿：只拷贝新增的 9 期 ──
    added = [e for e in n_eps if e["id"] not in old_ids]
    na = nt = 0
    for e in added:
        ap = os.path.join(SRC, "audio", os.path.basename(e["audio"]))
        tp = os.path.join(SRC, "podcast", "transcripts", e["slug"] + ".md")
        if os.path.exists(ap):
            dst = os.path.join(ROOT, "audio", os.path.basename(e["audio"]))
            if not os.path.exists(dst):
                shutil.copy2(ap, dst)
            na += 1
        else:
            print(f"   ⚠ 缺音频：{e['id']} {e['audio']}")
        if os.path.exists(tp):
            dst = os.path.join(ROOT, "podcast", "transcripts", e["slug"] + ".md")
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if not os.path.exists(dst):
                shutil.copy2(tp, dst)
            nt += 1
        else:
            print(f"   ⚠ 缺文稿：{e['id']}")
    print(f"④ 新增 {len(added)} 期：音频落地 {na}、文稿落地 {nt}")

    # ── ⑤ article_slugs / 音频存在性硬校验 ──
    miss_art, miss_aud = [], []
    for e in added:
        for s in e.get("article_slugs") or []:
            p = os.path.join(ROOT, s if s.startswith("news/") else "news/" + s)
            if not os.path.exists(p):
                miss_art.append((e["id"], s))
        if not os.path.exists(os.path.join(ROOT, "audio", os.path.basename(e["audio"]))):
            miss_aud.append(e["id"])
    print(f"⑤ 站内文章缺失 {len(miss_art)} 条 · 音频缺失 {len(miss_aud)} 条")
    for x in miss_art:
        print(f"   ⚠ {x}")
    if miss_aud:
        sys.exit(f"✗ 音频缺失：{miss_aud}")

    # ── ⑥ 落库 ──
    json.dump(new, open(os.path.join(ROOT, "data", "podcast.json"), "w",
                        encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"⑥ data/podcast.json 写入完成：{len(n_eps)} 期"
          f"（新增 {len(added)}：{' '.join(e['id'] for e in added)}）")
    for e in added:
        print(f"   + {e['id']} {e['slug']}  {e['series']}  "
              f"{e.get('duration_sec')}s  数据日期 {e.get('data_datetime')}")


if __name__ == "__main__":
    main()
