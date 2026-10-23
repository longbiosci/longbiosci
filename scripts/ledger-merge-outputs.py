#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ledger-merge-outputs.py —— 把新产出文件合并进台账（2026-10-23 第 11 轮）

为什么需要它
────────────
ledger.py build 是全量重建（不合并），而旧产出的本地副本已随暂存目录清理，
只剩 data/ledger-outputs.json 这一份持久记录。本轮及此前几轮消化的产出
（10-19 流水线摘要、10-21/10-22 速递、10-23 速递与五刊卡片）尚未入账，
audit 只能看到 21 个旧文件——本轮消化的 13 篇因此不在对账范围内。

做法
────
复用 ledger.scan_outputs 解析新文件，按 fingerprint 合并进现有台账：
  - 新指纹 → 新增条目
  - 已存在 → seen_in 追加文件名（跨期重复自动合并，与 build 的行为一致）
只合并明确列出的产出文件；.intake/ops/ 下的运营文档绝不纳入。
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import ledger  # noqa: E402

ROOT = sys.argv[1] if len(sys.argv) > 1 else "/workspace/repo"
NEW_FILES = [
    ".intake/raw/preprint-summary-2026-10-19.md",
    ".intake/raw/preprint-2026-10-21.md",
    ".intake/raw/preprint-2026-10-22.md",
    ".intake/raw/industry-2026-10-21.md",
    ".intake/raw/预印本速递_2026-10-23.md",
    ".intake/raw/文献层_五刊监控_深度文献卡片_2026-10-23.md",
]


def main():
    outfile = os.path.join(ROOT, "data/ledger-outputs.json")
    saved = json.load(open(outfile, encoding="utf-8"))
    entries = saved["entries"]
    per_file = saved.get("files", {})
    by_fp = {e["fingerprint"]: e for e in entries}
    before = len(entries)

    paths = [os.path.join(ROOT, f) for f in NEW_FILES]
    paths = [p for p in paths if os.path.exists(p)]
    seen, files_meta = ledger.scan_outputs(paths)
    added = 0
    for fp, e in seen.items():
        if fp in by_fp:
            by_fp[fp]["seen_in"] = sorted(set(by_fp[fp]["seen_in"]) | set(e["seen_in"]))
        else:
            by_fp[fp] = e
            added += 1
    for fn, meta in files_meta.items():
        per_file[fn] = meta
    merged = sorted(by_fp.values(), key=lambda e: e["fingerprint"])
    json.dump({"entries": merged, "files": per_file},
              open(outfile, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"台账条目 {before} → {len(merged)}（新增 {added}）")
    print(f"覆盖文件 {len(per_file)} 个（本次合并 {len(files_meta)} 个）")


if __name__ == "__main__":
    main()
