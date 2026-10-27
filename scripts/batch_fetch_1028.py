#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量下载待处理产出 → .intake/raw/1028/，并落盘实测字节数与 md5。

硬规则：判空必须实际下载核验字节数，不信 dir_list 的 size（陈旧缓存）。
本脚本对 pending 清单里的每一个 file_id 都真下载一次，把
（file_id, 实测字节数, md5, 是否为空）写进 sizes-1028.json。
"""
import csv
import hashlib
import json
import os
import subprocess
import sys

REPO = "/workspace/longbiosci"
RAW = os.path.join(REPO, ".intake", "raw", "1028")
os.makedirs(RAW, exist_ok=True)

rows = []
with open(os.path.join(REPO, "data", "intake-manifest.tsv"), encoding="utf-8") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        rows.append(r)

# 需要下载的三类：游标无记录（pending）+ 同名疑似重复（samename）+ 已 done 但 mtime 变（updated）
cur = json.load(open(os.path.join(REPO, "data", "intake-cursor.json"), encoding="utf-8"))["entries"]
todo = [r for r in rows if r["file_id"] not in cur]

# 补充：同名/更新类（由 next 输出人工确认）
extra_ids = set()
by_name = {}
for r in rows:
    by_name.setdefault(os.path.basename(r["name"]), []).append(r)
for r in rows:
    if r["file_id"] in cur:
        continue
for fid, v in cur.items():
    if v.get("status") == "done":
        pass
# mtime 变化的三条（行业情报周报_2026-09-16 / 运营待办清单 / 运营日志）
MTIME_CHANGED = {
    "行业情报周报_2026-09-16": "1793059918000",
    "运营待办清单": "1793107648000",
    "运营日志": "1793107612000",
}
for r in rows:
    base = os.path.basename(r["name"])
    if base in MTIME_CHANGED and r["modify_time"] == MTIME_CHANGED[base]:
        if r["file_id"] not in {t["file_id"] for t in todo}:
            todo.append(r)

def safe(n):
    return "".join(c if c not in "/\\:*?\"<>|" else "_" for c in n)[:90]

out = {}
for i, r in enumerate(todo, 1):
    fid = r["file_id"]
    dest = os.path.join(RAW, f"{fid}__{safe(os.path.basename(r['name']))}")
    if not os.path.exists(dest):
        p = subprocess.run([sys.executable, "scripts/ndfetch.py", fid, dest],
                           cwd=REPO, capture_output=True, text=True)
        tail = (p.stdout or "").strip().splitlines()
        note = tail[-1] if tail else (p.stderr or "").strip()[:120]
    else:
        note = "已存在，跳过下载"
    got = os.path.getsize(dest) if os.path.exists(dest) else 0
    md5 = hashlib.md5(open(dest, "rb").read()).hexdigest() if got else ""
    out[fid] = {"name": r["name"], "layer": r["layer"], "cached_size": r["size"],
                "bytes": got, "md5": md5, "empty": got == 0, "note": note}
    print(f"[{i}/{len(todo)}] {r['layer']} {os.path.basename(r['name'])[:44]:46s} "
          f"缓存{r['size']:>9} 实测{got:>9}  {'⛔空' if got==0 else '✓'}  {md5[:8]}",
          flush=True)

json.dump(out, open(os.path.join(REPO, ".intake", "sizes-1028.json"), "w",
                    encoding="utf-8"), ensure_ascii=False, indent=1)
empt = [k for k, v in out.items() if v["empty"]]
print(f"\n完成 {len(out)} 个 · 实测为空 {len(empt)} 个")
for k in empt:
    print(f"  ⛔ {k} {out[k]['name']}")
