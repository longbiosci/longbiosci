#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_manifest.py —— 把网盘四层清单转成 data/intake-manifest.tsv（事实源）并与旧清单 diff

用法：python3 scripts/build_manifest.py [nd_raw.json]
默认读取 ../artifact/.../nd_raw.json（由 nd_dirlist.py 生成）。

两个必须处理的坑
────────────────
1) **元层目录其实是 IMA 知识库树的根**。
   `dQpzABLkRxLu`（元层）下除了 5 个真正的元层产出外，还有一个
   `IMA知识库_0019eb4e65002c9f/` 子树，里面镜像了文献层/行业层/网站层的
   全部 36 个文件（file_id 完全相同），另有 2 份
   《衰老与长寿相关临床试验登记清单》。
   不按 file_id 去重的话，清单会从 43 行膨胀到 83 行，
   cursor verify 也会因为同一 file_id 出现多次而失去意义。
   去重优先级：文献层 > 行业层 > 网站层 > 元层（元层的镜像条目让位）。

2) **网盘 dir_list 的 size 是陈旧缓存值**，不能用来判「空产出」。
   实测：运营日志刚上传 85842 B，dir_list 仍报 64212 B。
   判定 size=0 必须以实际下载字节数为准（ndfetch.py 已带大小校验）。
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_RAW = "/root/.codebuddy/artifact/2f8a7d30-9c21-4f0b-1d4a-ef836f1a8000/nd_raw.json"
REPO = os.path.dirname(HERE)
OUT = os.path.join(REPO, "data", "intake-manifest.tsv")
VERIFIED = os.path.join(REPO, "data", "verified-sizes.json")
TZ = timezone(timedelta(hours=8))
ORDER = ["文献层", "行业层", "网站层", "元层"]      # 元层垫底：其镜像条目让位
PRIORITY = {layer: i for i, layer in enumerate(ORDER)}


def mdate(ms):
    return datetime.fromtimestamp(int(ms) / 1000, TZ).strftime("%Y-%m-%d")


def main():
    raw = json.load(open(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_RAW,
                         encoding="utf-8"))
    old = {}
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            f.readline()
            for line in f:
                c = line.rstrip("\n").split("\t")
                if len(c) >= 6:
                    old[c[0]] = (c[4], c[5])       # size, mtime

    # 按 file_id 归并：同一个文件被多个层引用时，取优先级最高的层
    best, mirrors = {}, 0
    for layer in ORDER:
        for it in raw.get(layer, {}).get("items", []):
            fid = it["file_id"]
            if fid in best:
                mirrors += 1
                if PRIORITY[layer] >= PRIORITY[best[fid][1]]:
                    continue
            best[fid] = (it, layer)

    # 实测字节数覆盖缓存值：dir_list 的 size 是陈旧缓存，判空必须以实测为准。
    # 已实测两次假象：dsMQHIJKCTLS（缓存 0 / 实际 33644）、dNTCoBPwiOnt（缓存 0 / 实际 89241）。
    # 缓存 0 若直接进清单，cursor 会把一条完整产出当空文件跳过 —— 内容凭空丢失。
    vsize, overriden = {}, []
    if os.path.exists(VERIFIED):
        for k, v in json.load(open(VERIFIED, encoding="utf-8")).items():
            if k.startswith("_"):
                continue
            vsize[k] = int(v["bytes"] if isinstance(v, dict) else v)
    if vsize:
        for fid, (it, layer) in best.items():
            got = vsize.get(fid)
            if got is None:
                continue
            if str(it["size"]) != str(got):
                overriden.append((it["name"], it["size"], got))
            it["size"] = str(got)
        # 缓存里根本没有的条目（极少见）也要补进清单
        for fid, got in vsize.items():
            if fid not in best:
                best[fid] = ({"file_id": fid, "name": fid, "ext": "",
                              "size": str(got), "modify_time": "0"}, "元层")

    rows = []
    for fid, (it, layer) in best.items():
        if layer != "元层" and "/IMA知识库" in it["name"]:
            continue          # 镜像条目的名字带 IMA 前缀，不进清单
        rows.append((fid, layer, it["name"], it["ext"],
                     it["size"], it["modify_time"], mdate(it["modify_time"])))
    rows.sort(key=lambda r: (PRIORITY[r[1]], r[2]))

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("file_id\tlayer\tname\text\tsize\tmodify_time\tmodify_date\n")
        for r in rows:
            f.write("\t".join(str(x) for x in r) + "\n")

    print(f"写入 {OUT}：{len(rows)} 个产出（去重掉 {mirrors} 条跨层镜像）")
    for nm, cached, got in overriden:
        print(f"  ⚠️ 缓存 size 被实测值覆盖：{nm[:40]}  {cached} → {got} B")
    if overriden:
        print(f"  共 {len(overriden)} 条（dir_list 缓存不可信，实测为准）")
    for layer in ORDER:
        n = sum(1 for r in rows if r[1] == layer)
        e = sum(1 for r in rows if r[1] == layer and str(r[4]) == "0")
        print(f"  {layer}: {n} 个" + (f"（其中 size=0: {e}）" if e else ""))

    new_ids = {r[0] for r in rows}
    gone = [k for k in old if k not in new_ids]
    added = [r for r in rows if r[0] not in old]
    changed = []
    for r in rows:
        if r[0] in old and old[r[0]] != (r[4], r[5]):
            changed.append((r[2], old[r[0]], (r[4], r[5])))
    print(f"\n与旧清单对比：新增 {len(added)} · 消失 {len(gone)} · 变更(size/mtime) {len(changed)}")
    for r in added:
        print(f"  [新增] {r[1]} · {r[2]}  {r[4]}B  {r[6]}")
    for g in gone:
        print(f"  [消失] {g}")
    for c in changed:
        print(f"  [变更] {c[0]}  size/mtime {c[1]} → {c[2]}")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
