#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
nd_dirlist.py —— 抓取网盘四层目录清单，产出 build_manifest.py 需要的 nd_raw.json

为什么要有这一层
────────────────
事实源 `data/intake-manifest.tsv` 由 nd_raw.json 生成。此前 nd_raw.json 是
把 dir_list 的返回**手抄**成 JSON 的 —— 43 个产出的 file_id、毫秒时间戳、
字节数，抄错任何一个都会让游标对不上号，而这恰恰是「该有的都有吗」的
唯一依据。事实源本身不能建立在一个会抄错的步骤上。

本脚本直调网盘 MCP 端点枚举四层目录（自动翻页），原样落盘。
配合 build_manifest.py 使用，全程不经人手。

用法
────
  python3 scripts/nd_dirlist.py [输出路径]
  默认输出到 <artifact>/nd_raw.json（build_manifest.py 的默认读取位置）
"""
import itertools
import json
import os
import sys
import time
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ndfetch import _rpc, PROTOCOL  # noqa: E402

LAYERS = [
    ("文献层", "dsuxMCSCwEVB"),
    ("行业层", "dVEYJcsAbUdK"),
    ("元层",   "dQpzABLkRxLu"),
    ("网站层", "drGisxAlABJK"),
]


def _call(sid, name, arguments, rid):
    """调一次工具，并对「静默失效」零容忍。

    网盘工具的业务级错误不走 JSON-RPC 的 error 通道，而是塞进正常响应体里的
    `error_code` / `error_msg`。若只看 JSON-RPC error，这类响应会被当成
    「成功但没有条目」——目录凭空变空，事实源静默缺项，而这恰恰是清单
    唯一要防的事故。实测连续快速调用时会触发限流，返回的就是这种体。
    """
    for attempt in range(4):
        _, resp = _rpc(sid, "tools/call",
                       {"name": name, "arguments": arguments}, rid=rid)
        if "error" in resp:
            raise RuntimeError(f"MCP 错误（{name}）：{resp['error']}")
        texts = [c.get("text", "") for c in resp["result"].get("content", [])]
        d = json.loads(texts[0]) if texts else {}
        if not d.get("error_code"):
            return d
        if attempt == 3:
            raise RuntimeError(
                f"网盘返回业务错误（{name}）：{d.get('error_code')} "
                f"{d.get('error_msg')} / {d.get('suggested_action')}")
        time.sleep(2 ** attempt)          # 限流退避：1s / 2s / 4s
    return {}


_rid = itertools.count(1000)      # 全局单调递增；JSON-RPC 的 id 复用会让服务端
                                  # 返回缓存响应，导致目录「凭空变空」


def list_all(sid, dir_id, rid=None, prefix=""):
    """dir_list 每页最多 20 条且**不递归**，两者都会让事实源静默缺项。

    实测：网站层根目录下只有 2 个文件，另外 17 个产出全在子目录
    `网站喂料_2026-10-13/` 里。若用 entry_kind=2（只返回文件）或只取直接子项，
    这 17 个产出会从清单里凭空消失——而清单的作用恰恰是「该有的都有吗」。

    故：entry_kind=0 全取，遇到 kind=2（目录）下钻一层，名字加目录前缀。
    """
    items, cursor, page = [], None, 0
    while True:
        args = {"dir_id": dir_id, "limit": 20, "entry_kind": 0}
        if cursor:
            args["cursor"] = cursor
        r = _call(sid, "tdrive.dir_list", args, rid=next(_rid))
        time.sleep(0.6)          # 与网盘限流窗口保持距离
        page += 1
        entries = r.get("entries") or []
        for e in entries:
            if e.get("kind") == 2:                      # 目录 → 下钻一层
                items += list_all(sid, e["file_id"],
                                  prefix=prefix + e["name"] + "/")
            else:
                items.append(dict(e, name=prefix + e["name"]))
        cursor = r.get("next_cursor")
        if not cursor or page > 20:
            break
    return items


DEFAULT_OUT = os.path.join(
    "/root/.codebuddy/artifact/2f8a7d30-9c21-4f0b-1d4a-ef836f1a8000",
    "nd_raw.json")


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUT
    out = os.path.abspath(out)

    sid, _ = _rpc(None, "initialize", {
        "protocolVersion": PROTOCOL, "capabilities": {},
        "clientInfo": {"name": "nd_dirlist", "version": "1.0"}}, rid=1)
    try:
        _rpc(sid, "notifications/initialized", rid=2)
    except urllib.error.HTTPError:
        pass

    raw = {}
    for layer, dir_id in LAYERS:
        items = list_all(sid, dir_id)
        keep = [{"file_id": i.get("file_id") or i.get("id"),
                 "name": i.get("name"), "ext": (i.get("ext") or "").lstrip("."),
                 "size": str(i.get("size") or 0),
                 "modify_time": str(i.get("modify_time") or 0)}
                for i in items]
        raw[layer] = {"dir_id": dir_id, "items": keep}
        empty = sum(1 for k in keep if k["size"] == "0")
        print(f"  {layer}: {len(keep)} 个产出"
              + (f"（size=0: {empty}）" if empty else ""))

    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(raw, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"→ {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
