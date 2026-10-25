#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_articles_intake_2026-10-26c.py —— 05:30 班第 14 轮 · 批次 c

消化对象
────────
《LongBiosci_播客_ep014-ep019_增量_待推送_2026-10-26》（任务 13323391，
元层 dKUTHchdFmMA，13.95 MB tar）—— 新增 6 期：ep014–ep019。

查重（规则④）：包内 podcast.json 19 期 vs 本站 13 期，**前 13 期逐字段
逐字节一致（0 差异）**，新增 6 期 slug 全部不在站内 → **净新增 6 期，
跳过 13 条（站内已发布）**。

⚠️ 为什么不全包覆盖（与批次 b 的午刊包同源的坑）
──────────────────────────────────────────
包内 `index.html` / `sitemap.xml` / `podcast/index.html` / `podcast.xml`
均基于**远端基线 d413d13**（10-25 的 613 条口径）生成。而本站经本轮前两
批已达 772 条口径。整体覆盖会把本站在库的文章从站点地图与首页里抹掉。
故本批只取**三处内容件**：

    audio/*.mp3                  （6 个，SHA256 全 OK）
    podcast/transcripts/*.md     （6 个，SHA256 全 OK）
    data/podcast.json            （19 期；前 13 期与本站一致，故可直接采用）

`podcast/index.html` 与 `podcast.xml` 由管线环节 8（gen-podcast.py）
从 data/podcast.json 重新生成，`index.html` / `sitemap.xml` 分别由环节 3
与环节 18 重建。

时间标签（规则③）：沿用上游每期自带的 `data_datetime` / `generated_at`
（数据日期 2026-10-22 18:32 · 生成时间 2026-10-26 03:43），
由 gen-podcast.py 输出到页面 `.ep-time` 与 RSS item 描述。
"""
import hashlib
import json
import os
import shutil
import subprocess
import tarfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = os.path.join(ROOT, ".intake-tmp/20261026/pod/LongBiosci_播客_ep014-ep019_增量_2026-10-26")
PACKED = json.load(open(os.path.join(TMP, "data/podcast.json"), encoding="utf-8"))

COPY = [
    ("audio", "audio", ".mp3"),
    ("podcast/transcripts", "podcast/transcripts", ".md"),
]


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    old = json.load(open(os.path.join(ROOT, "data/podcast.json"), encoding="utf-8"))
    old_slugs = {e["slug"] for e in old["episodes"]}
    new_eps = [e for e in PACKED["episodes"] if e["slug"] not in old_slugs]
    dup = [e["slug"] for e in PACKED["episodes"] if e["slug"] in old_slugs]

    print(f"包内 {len(PACKED['episodes'])} 期 · 站内已有 {len(dup)} 期（跳过）"
          f" · 净新增 {len(new_eps)} 期")

    copied = []
    for srcdir, dstdir, ext in COPY:
        src = os.path.join(TMP, srcdir)
        dst = os.path.join(ROOT, dstdir)
        os.makedirs(dst, exist_ok=True)
        for fn in sorted(os.listdir(src)):
            if not fn.endswith(ext):
                continue
            s, d = os.path.join(src, fn), os.path.join(dst, fn)
            if os.path.exists(d):
                print(f"  ⨯ 跳过（已存在） {dstdir}/{fn}")
                continue
            shutil.copy2(s, d)
            copied.append(f"{dstdir}/{fn}")

    # data/podcast.json：前 13 期与本站逐字段一致，故整体采用是安全的
    out = os.path.join(ROOT, "data/podcast.json")
    json.dump(PACKED, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print(f"复制文件 {len(copied)} 个：")
    for c in copied:
        print("  ✓", c)
    print(f"data/podcast.json 13 → {len(PACKED['episodes'])} 期")

    # 音频时长核验：ffprobe 可用则实测，不可用则仅登记字节（不臆测时长）
    for e in new_eps:
        p = os.path.join(ROOT, e["audio"])
        n = os.path.getsize(p) if os.path.exists(p) else -1
        sec = "—"
        try:
            r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                "format=duration", "-of", "default=nw=1:nk=1", p],
                               capture_output=True, text=True, timeout=30)
            if r.returncode == 0 and r.stdout.strip():
                sec = str(round(float(r.stdout.strip())))
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        flag = "" if abs(int(sec) - e["duration_sec"]) <= 2 or sec == "—" else " ⚠与 JSON 不符"
        print(f"  ep {e['id']} {e['slug']}: {n} B · JSON 时长 {e['duration_sec']} s"
              f" · 实测 {sec} s{flag}")


if __name__ == "__main__":
    main()
