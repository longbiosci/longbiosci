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
    {file_id, name, layer, size, mtime, status, done_at, slugs, hash}
  status ∈ pending / done / empty / skipped

配合 data/intake-manifest.tsv（网盘全量清单，事实源）使用：
    cursor next   列出待处理的产出（pending + size>0）
    cursor done   把条目标记为已处理，可带本次产出的 slug 与内容哈希
    cursor seen   按（文件名, 内容哈希）判重：这份内容以前消化过吗
    cursor stat   看消化进度（哪几期还没动、哪几期是空的）
    cursor verify 与 manifest 交叉核对：清单里有但游标里没有的 = 新产出

幂等：同一个 file_id 重复 done 只更新记录，不会重复处理。

滚动文件判重（2026-10-24 新增，实测教训）
────────────────────────────────────
网盘对同名文件有两种行为且都会发生：原地更新（file_id 不变、mtime 变，
实测 10-23 待办清单 dDgSRfxdSmVQ）与同名新建（file_id 变，vlog 记载的
overwrite 不生效案例；实测 10-24 运行摘要 dsGXxdlopHqF/dGSADrtEEHrK
同名同大小两份）。只按 file_id 判新，这两种都发现不了——要么整篇日志
被反复重消化，要么更新被永久跳过。故规则改为：

  1) next  —— 提示层：列出「已 done 但 size/mtime 变了」（原地更新）与
             「新 file_id 但 basename 与已 done 记录相同」（同名新副本）。
             只提示不判定，因为 size 可能是陈旧缓存，mtime 也可能被
             非内容性操作（如 IMA 同步）触及。
  2) seen —— 终裁层：下载后算内容 md5，由本命令按（basename, hash）
             对已 done 记录判重。UNCHANGED / DUPLICATE / NEW 三态，
             哈希相同才是重复；同名不同哈希 = 滚动更新，只消化增量。
  3) done —— 留痕层：--hash 把内容哈希写进游标，下一轮 seen 才有基准。
             2026-10-24 之前 done 的历史记录没有哈希，这些条目 seen
             只能判 NEW（安全侧：宁可重消化，不可漏消化）。

用法
────
  python3 scripts/cursor.py next  --repo .
  python3 scripts/cursor.py done  --repo . --file-id dXzxgtkeYPXT --slugs a.html b.html --hash <md5>
  python3 scripts/cursor.py seen  --repo . --file-id dGSADrtEEHrK --hash <md5>
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
    """列出待处理的产出。

    三类注意力对象：
    1) 待处理：游标无记录 / 状态非 done / 空文件（原有逻辑）
    2) 滚动更新：已 done，但清单里的 size/mtime 与游标记录不一致——
       同名文件被覆盖更新而 file_id 未变（原地更新），按 file_id 判新
       完全看不见。mtime 是可靠信号；size 可能是陈旧缓存，只作辅助。
    3) 同名新副本：新 file_id，但 basename 与已 done 记录或本轮已排队记录
       相同——疑似同一文档的重复交付（实测 10-24 运行摘要在元层根目录与
       子目录各一份，同名同哈希）。是否重复由 seen 按内容哈希终裁。
    """
    cur, man = load(repo), load_manifest(repo)
    ent = cur["entries"]
    out, updated, samename = [], [], []
    # 已 done 记录的 basename 索引（判「同名」用：含历史已消化 + 本轮已排队）
    done_names, pending_names = {}, {}
    for fid, v in ent.items():
        if v.get("status") == "done":
            done_names.setdefault(os.path.basename(v.get("name", "")), []).append(fid)

    for m in man:
        if layer and m["layer"] != layer:
            continue
        size = int(m["size"] or 0)
        rec = ent.get(m["file_id"])
        if rec and rec.get("status") == "done":
            # ── 第 2 类：已消化但清单显示它变了 ──
            size_changed = str(rec.get("size", "")) != m["size"]
            mtime_changed = str(rec.get("mtime", "")) != m["mtime"]
            if size_changed or mtime_changed:
                # mtime 变 = 网盘侧真写过（可靠信号）；仅 size 变而 mtime 不变
                # 多是陈旧缓存被实测值修正（build_manifest 的 override），
                # 不一定是内容更新——分开标注，避免狼来了。
                signal = ("mtime 变化（可能真更新）" if mtime_changed
                          else "仅 size 缓存修正（mtime 未变，大概率非内容更新）")
                updated.append({
                    "file_id": m["file_id"], "name": m["name"],
                    "layer": m["layer"], "size": size,
                    "was": (rec.get("size"), rec.get("mtime")),
                    "now": (m["size"], m["mtime"]),
                    "hash": rec.get("hash", ""), "signal": signal,
                })
            continue
        if size == 0 and not include_empty:
            continue
        # ── 第 3 类：新 file_id，但 basename 与已消化/本轮已排队的记录同名 ──
        base = os.path.basename(m["name"])
        known = done_names.get(base, []) + pending_names.get(base, [])
        if rec is None and known:
            samename.append({
                "file_id": m["file_id"], "name": m["name"],
                "layer": m["layer"], "size": size,
                "seen_as": known,
            })
            continue
        out.append({
            "file_id": m["file_id"], "name": m["name"], "layer": m["layer"],
            "size": size,
            "why": ("空文件（产出缺失，需重跑对应任务）" if size == 0
                    else "游标无记录" if not rec
                    else f"上次状态={rec.get('status')}"),
        })
        pending_names.setdefault(base, []).append(m["file_id"])
    if not out:
        print("✅ 没有待处理的产出（游标与清单一致）")
    else:
        print(f"待处理 {len(out)} 个产出：")
        for o in out:
            print(f"  [{o['layer']}] {o['name'][:52]}  ({o['size']} B) — {o['why']}")
    if updated:
        print(f"\n🔄 已消化但清单显示有更新（{len(updated)} 个）—— 下载后用 seen 判重：")
        for u in updated:
            hint = "有哈希基准" if u["hash"] else "⚠️ 历史无哈希，只能按内容人工比对"
            print(f"  [{u['layer']}] {u['name'][:46]}  ({u['size']} B) — {u['signal']} · {hint}")
            print(f"      size/mtime {u['was']} → {u['now']}")
    if samename:
        print(f"\n👥 新 file_id 但与已消化/本轮已排队记录同名（{len(samename)} 个）—— "
              f"疑似重复交付，下载后 seen 终裁：")
        for s in samename:
            print(f"  [{s['layer']}] {s['name'][:46]}  ({s['size']} B) — "
                  f"同名已知：{' '.join(s['seen_as'])}")
    return 0


def _mark(repo, file_id, status, slugs=None, note="", content_hash=""):
    cur = load(repo)
    man = {m["file_id"]: m for m in load_manifest(repo)}
    m = man.get(file_id, {})
    cur["entries"][file_id] = {
        "name": m.get("name", ""), "layer": m.get("layer", ""),
        "size": int(m.get("size") or 0), "mtime": m.get("mtime", ""),
        "status": status, "done_at": now(),
        "slugs": slugs or [],
        "note": note,
        "hash": content_hash,
    }
    save(repo, cur)
    print(f"✔ {m.get('name', file_id)} → {status}"
          + (f"（{len(slugs)} 篇）" if slugs else "") + (f"  {note}" if note else "")
          + (f"  hash={content_hash[:12]}…" if content_hash else ""))
    return 0


def cmd_done(repo, file_id, slugs, note="", content_hash=""):
    return _mark(repo, file_id, "done", slugs, note, content_hash)


def cmd_seen(repo, file_id, content_hash):
    """按（文件名, 内容哈希）判重：这份内容以前消化过吗？

    下载文件后先算 md5 再调本命令。三种结论：
      UNCHANGED  本 file_id 已 done 且哈希一致 —— mtime 变了但内容没变
      DUPLICATE  另一条已 done 记录（同名）哈希一致 —— 重复交付，勿再消化
      NEW        无任何匹配 —— 新内容（同名不同哈希 = 滚动更新，消化增量）
    退出码：0 = 无需再消化（UNCHANGED/DUPLICATE）；1 = 需要消化（NEW）；
            2 = 参数缺失。
    """
    if not file_id or not content_hash:
        print("用法：cursor.py seen --repo . --file-id <id> --hash <md5>")
        return 2
    cur = load(repo)
    ent = cur["entries"]
    rec = ent.get(file_id)
    if rec and rec.get("status") == "done" and rec.get("hash") == content_hash:
        print(f"UNCHANGED {file_id}：本文件已消化且内容一致"
              f"（消化于 {rec.get('done_at', '?')}）—— mtime 变化非内容性，"
              f"重新 done 一次刷新记录即可")
        return 0
    base = os.path.basename(rec.get("name", "")) if rec else ""
    if not base:
        man = {m["file_id"]: m for m in load_manifest(repo)}
        base = os.path.basename(man.get(file_id, {}).get("name", ""))
    dups = [(fid, v) for fid, v in ent.items()
            if v.get("status") == "done" and v.get("hash") == content_hash
            and os.path.basename(v.get("name", "")) == base and fid != file_id]
    if dups:
        fid, v = dups[0]
        print(f"DUPLICATE {file_id}：与已消化的 {fid} 内容完全相同"
              f"（同名「{base}」，消化于 {v.get('done_at', '?')}）—— 跳过消化，"
              f"done 时带 --note 注明重复来源")
        return 0
    same_name = [fid for fid, v in ent.items()
                 if v.get("status") == "done" and fid != file_id
                 and os.path.basename(v.get("name", "")) == base]
    if same_name:
        print(f"NEW {file_id}：同名「{base}」已有消化记录"
              f"（{' '.join(same_name)}）但哈希不匹配 —— 这是滚动更新，只消化增量部分")
    elif rec and rec.get("status") == "done" and not rec.get("hash"):
        print(f"NEW {file_id}：本文件已消化但历史无哈希基准 —— 若确认内容已消化过，"
              f"用 done --hash 补记基准；若有实质更新，只消化增量")
    else:
        print(f"NEW {file_id}：无同名已消化记录 —— 全新内容，正常消化")
    return 1


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
    ap.add_argument("cmd", choices=["next", "done", "empty", "stat", "verify", "seen"])
    ap.add_argument("--repo", default=".")
    ap.add_argument("--file-id", default="")
    ap.add_argument("--layer", default=None)
    ap.add_argument("--slugs", nargs="*", default=[])
    ap.add_argument("--note", default="")
    ap.add_argument("--hash", default="", help="内容 md5（done 记录 / seen 判重用）")
    ap.add_argument("--include-empty", action="store_true")
    a = ap.parse_args()
    if a.cmd == "next":
        return cmd_next(a.repo, a.layer, a.include_empty)
    if a.cmd in ("stat", "verify"):
        return {"stat": cmd_stat, "verify": cmd_verify}[a.cmd](a.repo)
    if a.cmd == "seen":
        return cmd_seen(a.repo, a.file_id, a.hash)
    return {"done": lambda r: cmd_done(r, a.file_id, a.slugs, a.note, a.hash),
            "empty": lambda r: cmd_empty(r, a.file_id, a.note)}[a.cmd](a.repo)


if __name__ == "__main__":
    sys.exit(main() or 0)