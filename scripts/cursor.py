#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cursor.py —— 摄入游标：让「处理过没有」变成机器可判定的事实

问题
────
整条内容通道的唯一状态曾经是「我记得上次捞到哪」。
后果：上下文一压缩就丢，于是要么重复捞，要么漏捞——
      这与「网站内容有遗漏」是同一个病根（状态无处存放）。

做法
────
维护 data/intake-cursor.json，每个产出文件一条记录：
    {file_id, name, layer, size, mtime, status, done_at, slugs}
  status ∈ pending / done / empty / skipped

配合 data/intake-manifest.tsv（网盘全量清单，事实源）使用：
    cursor next   列出待处理的产出（pending + size>0）
    cursor done   把条目标记为已处理，可带本次产出的 slug
    cursor stat   看消化进度（哪几期还没动、哪几期是空的）
    cursor verify 与 manifest 交叉核对：清单里有但游标里没有的 = 新产出

幂等：同一个 file_id 重复 done 只更新记录，不会重复处理。

用法
────
  python3 scripts/cursor.py next  --repo .
  python3 scripts/cursor.py done  --repo . --file-id dXzxgtkeYPXT --slugs a.html b.html
  python3 scripts/cursor.py empty --repo . --file-id dNTCoBPwiOnt
  python3 scripts/cursor.py stat  --repo .
  python3 scripts/cursor.py verify --repo .
"""
import argparse
import json
import os
import sys
from datetime import datetime

CURSOR = "data/intake-cursor.json"
MANIFEST = "data/intake-manifest.tsv"


def now():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00")


def load(repo):
    p = os.path.join(repo, CURSOR)
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8"))
    return {"version": 1, "updated_at": "", "entries": {}}


def save(repo, cur):
    cur["updated_at"] = now()
    p = os.path.join(repo, CURSOR)
    json.dump(cur, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return p


def load_manifest(repo):
    p = os.path.join(repo, MANIFEST)
    if not os.path.exists(p):
        return []
    rows = []
    with open(p, encoding="utf-8") as f:
        head = f.readline()
        for line in f:
            c = line.rstrip("\n").split("\t")
            if len(c) >= 6:
                rows.append(dict(zip(["file_id", "layer", "name", "ext",
                                      "size", "mtime"], c[:6])))
    return rows


# ────────────────────────────── 命令 ──────────────────────────────

def cmd_next(repo, layer=None, include_empty=False):
    """列出待处理产出：游标里没有该 file_id，或状态仍是 pending"""
    cur, man = load(repo), load_manifest(repo)
    ent = cur["entries"]
    out = []
    for m in man:
        if layer and m["layer"] != layer:
            continue
        size = int(m["size"] or 0)
        rec = ent.get(m["file_id"])
        if size == 0 and not include_empty:
            continue
        if rec and rec.get("status") == "done":
            continue
        out.append({
            "file_id": m["file_id"], "name": m["name"], "layer": m["layer"],
            "size": size,
            "why": ("空文件（产出缺失，需重跑对应任务）" if size == 0
                    else "游标无记录" if not rec
                    else f"上次状态={rec.get('status')}"),
        })
    if not out:
        print("✅ 没有待处理的产出（游标与清单一致）")
    else:
        print(f"待处理 {len(out)} 个产出：")
        for o in out:
            print(f"  [{o['layer']}] {o['name'][:52]}  ({o['size']} B) — {o['why']}")
    return 0


def _mark(repo, file_id, status, slugs=None, note=""):
    cur = load(repo)
    man = {m["file_id"]: m for m in load_manifest(repo)}
    m = man.get(file_id, {})
    cur["entries"][file_id] = {
        "name": m.get("name", ""), "layer": m.get("layer", ""),
        "size": int(m.get("size") or 0), "mtime": m.get("mtime", ""),
        "status": status, "done_at": now(),
        "slugs": slugs or [],
        "note": note,
    }
    save(repo, cur)
    print(f"✔ {m.get('name', file_id)} → {status}"
          + (f"（{len(slugs)} 篇）" if slugs else "") + (f"  {note}" if note else ""))
    return 0


def cmd_done(repo, file_id, slugs, note=""):
    return _mark(repo, file_id, "done", slugs, note)


def cmd_empty(repo, file_id, note=""):
    return _mark(repo, file_id, "empty", [], note or "产出为空")


def cmd_stat(repo):
    cur, man = load(repo), load_manifest(repo)
    ent = cur["entries"]
    print(f"游标更新于 {cur.get('updated_at') or '从未'} · "
          f"记录 {len(ent)} 条 / 清单 {len(man)} 个产出")
    by = {}
    for m in man:
        layer = m["layer"]
        by.setdefault(layer, []).append(m)
    print()
    for layer, ms in sorted(by.items()):
        done = [m for m in ms if ent.get(m["file_id"], {}).get("status") == "done"]
        pend = [m for m in ms if m not in done]
        empt = [m for m in pend if int(m["size"] or 0) == 0]
        unproc = [m for m in pend if m not in empt]
        print(f"【{layer}】已消化 {len(done)}/{len(ms)}"
              + (f" · 待处理 {len(unproc)}" if unproc else "")
              + (f" · 空文件 {len(empt)}" if empt else ""))
        for m in unproc:
            print(f"    ⬜ {m['name'][:50]}  ({m['size']} B)")
        for m in empt:
            print(f"    ⛔ {m['name'][:50]}  size=0 —— 需重跑任务")
    return 0


def cmd_verify(repo):
    """交叉核对：清单里有但游标里没有的 = 新产出（agent 捞漏的兜底）"""
    cur, man = load(repo), load_manifest(repo)
    ent = cur["entries"]
    new = [m for m in man if m["file_id"] not in ent]
    stale = [f for f in ent if f not in {m["file_id"] for m in man}]
    print(f"清单 {len(man)} 个 / 游标 {len(ent)} 条")
    if not new and not stale:
        print("✅ 一致：清单与游标完全对齐")
        return 0
    if new:
        print(f"\n⚠️ 清单有、游标无（{len(new)} 个）—— 这些是尚未处理的新产出：")
        for m in new:
            print(f"    {m['layer']} · {m['name'][:50]}")
    if stale:
        print(f"\n⚠️ 游标有、清单无（{len(stale)} 个）—— 清单可能过期，需重建：")
        for f in stale:
            print(f"    {f}  {ent[f].get('name', '')}")
    return 1


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("cmd", choices=["next", "done", "empty", "stat", "verify"])
    ap.add_argument("--repo", default=".")
    ap.add_argument("--file-id", default="")
    ap.add_argument("--layer", default=None)
    ap.add_argument("--slugs", nargs="*", default=[])
    ap.add_argument("--note", default="")
    ap.add_argument("--include-empty", action="store_true")
    a = ap.parse_args()
    return {"next": cmd_next, "done": cmd_done, "empty": cmd_empty,
            "stat": cmd_stat, "verify": cmd_verify}[a.cmd](
        a.repo, a.layer, a.include_empty) if a.cmd == "next" else \
        {"next": cmd_next, "done": cmd_done, "empty": cmd_empty,
         "stat": cmd_stat, "verify": cmd_verify}[a.cmd](a.repo) if a.cmd in ("stat", "verify") else \
        {"done": lambda r: cmd_done(r, a.file_id, a.slugs, a.note),
         "empty": lambda r: cmd_empty(r, a.file_id, a.note)}[a.cmd](a.repo)


if __name__ == "__main__":
    sys.exit(main() or 0)