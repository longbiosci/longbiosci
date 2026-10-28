#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量下载核验（1029 轮）——硬规则：判空必须实际下载核验字节数。

下载对象 = cursor next 的三类注意力对象：
  1) pending：游标无记录的 4 个（文献监控卡片/总览×2、午刊留档 tar）
  2) updated：已 done 但 mtime/size 变化的 9 个（运营日志/待办清单/人工待下载清单等）
  3) samename：新 file_id 同名（即第 2 份总览，已含在 pending）

落盘：(file_id, name, layer, 缓存size, 实测bytes, md5, 是否为空, file_id→下载证据)
→ .intake/sizes-1029.json，并回填 data/verified-sizes.json（供 build_manifest 覆盖缓存值）
"""
import csv
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta

REPO = "/workspace/longbiosci"
TZ = timezone(timedelta(hours=8))
RAW = os.path.join(REPO, ".intake", "raw", "1029")
os.makedirs(RAW, exist_ok=True)
NOW = datetime.now(TZ).strftime("%Y-%m-%dT%H:%M:%S+08:00")

rows = []
with open(os.path.join(REPO, "data", "intake-manifest.tsv"), encoding="utf-8") as f:
    rows = list(csv.DictReader(f, delimiter="\t"))
by_id = {r["file_id"]: r for r in rows}

cur = json.load(open(os.path.join(REPO, "data", "intake-cursor.json"),
                     encoding="utf-8"))["entries"]

todo, why = [], {}
# 1) pending：游标无记录
for r in rows:
    if r["file_id"] not in cur:
        todo.append(r)
        why[r["file_id"]] = "pending（游标无记录）"
# 2) updated：已 done 但 size/mtime 与游标记录不一致
for r in rows:
    rec = cur.get(r["file_id"])
    if not rec or rec.get("status") != "done":
        continue
    if str(rec.get("size", "")) != r["size"] or str(rec.get("mtime", "")) != r["modify_time"]:
        if r["file_id"] not in why:
            todo.append(r)
            why[r["file_id"]] = "updated（清单 size/mtime 与游标记录不一致）"

seen = set()
uniq = []
for r in todo:
    if r["file_id"] in seen:
        continue
    seen.add(r["file_id"])
    uniq.append(r)


def safe(n):
    return "".join(c if c not in "/\\:*?\"<>|" else "_" for c in n)[:90]


out = {}
for i, r in enumerate(uniq, 1):
    fid, base = r["file_id"], os.path.basename(r["name"])
    dest = os.path.join(RAW, f"{fid}__{safe(base)}")
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        note = "已存在非空副本，跳过重复下载"
    else:
        p = subprocess.run([sys.executable, "scripts/ndfetch.py", fid, dest],
                           cwd=REPO, capture_output=True, text=True)
        tail = (p.stdout or "").strip().splitlines()
        note = tail[-1] if tail else (p.stderr or "").strip()[:160]
    got = os.path.getsize(dest) if os.path.exists(dest) else 0
    md5 = hashlib.md5(open(dest, "rb").read()).hexdigest() if got else ""
    out[fid] = {"name": r["name"], "layer": r["layer"], "ext": r["ext"],
                "cached_size": r["size"], "bytes": got, "md5": md5,
                "empty": got == 0, "raw": dest, "note": note,
                "why": why.get(fid, "?"), "modify_time": r["modify_time"]}
    flag = "⛔实测为空" if got == 0 else "✓"
    print(f"[{i}/{len(uniq)}] {r['layer']} {base[:42]:44s} "
          f"缓存{r['size']:>9} 实测{got:>9} {flag} {md5[:8]}  {why.get(fid,'')[:14]}",
          flush=True)

json.dump(out, open(os.path.join(REPO, ".intake", "sizes-1029.json"), "w",
                    encoding="utf-8"), ensure_ascii=False, indent=1)

# 回填实测字节表：这份表是 build_manifest 覆盖 dir_list 陈旧缓存的唯一依据
vs_path = os.path.join(REPO, "data", "verified-sizes.json")
vs = json.load(open(vs_path, encoding="utf-8"))
for fid, v in out.items():
    if v["empty"]:
        continue                      # 空文件不登记为正值，避免掩盖空产
    vs[fid] = {"bytes": v["bytes"], "verified_at": NOW,
               "by": "摄入巡检 12409847（05:30 班 1029 轮）",
               "note": f"{os.path.basename(v['name'])}：实测下载核验"
                       + (f"（dir_list 缓存 {v['cached_size']} B）"
                          if str(v["cached_size"]) != str(v["bytes"]) else "（与缓存一致）")}
json.dump(vs, open(vs_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

empt = [k for k, v in out.items() if v["empty"]]
print(f"\n完成 {len(out)} 个 · 实测为空 {len(empt)} 个 · verified-sizes 累计 {len([k for k in vs if not k.startswith('_')])} 条")
for k in empt:
    print(f"  ⛔ {k}  {out[k]['name']}")
