#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ndupload.py —— 网盘上传一站式：申请上传 → PUT → 确认落库

为什么要有这一层
────────────────
file_upload 返回的是一组 COS 上传头，其中 Authorization / x-cos-security-token
都是几百字符的签名串。只要它们经过「人眼→手指→终端」，就必然出错——
与 ndfetch.py 要防的是同一类事故（2026-10-15 一天手抄错 3 次的教训）。

有下载器没有上传器，等于把雷留在一半的流程里：下载全程不经人手，
上传却要手抄几百字符的签名头，风险反而集中在更关键的那一步。

做法：直接调网盘 MCP 的 HTTP 端点拿上传凭证，用程序原样拼进 curl 参数，
PUT 完成后再调 file_upload_complete 落库。**全程签名不经人手、不经上下文。**

用法
────
  python3 scripts/ndupload.py <本地文件> <dir_id> [--name 另存为的名字]
  python3 scripts/ndupload.py .intake/raw/site-ops-log.md drGisxAlABJK

同名文件默认覆盖（conflict_strategy=overwrite）——运营日志/待办清单这类
需要反复追加的文档，不该每次都产生一个「运营日志(1).md」。
"""
import json
import mimetypes
import os
import subprocess
import sys
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ndfetch import _rpc, PROTOCOL  # noqa: E402


def _call(sid, name, arguments, rid):
    _, resp = _rpc(sid, "tools/call", {"name": name, "arguments": arguments}, rid=rid)
    if "error" in resp:
        raise RuntimeError(f"MCP 错误（{name}）：{resp['error']}")
    texts = [c.get("text", "") for c in resp["result"].get("content", [])]
    return json.loads(texts[0]) if texts else {}


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    local, dir_id = sys.argv[1], sys.argv[2]
    name = None
    if "--name" in sys.argv:
        name = sys.argv[sys.argv.index("--name") + 1]
    if not os.path.isfile(local):
        print(f"✗ 本地文件不存在：{local}")
        return 1
    name = name or os.path.basename(local)
    size = os.path.getsize(local)

    sid, _ = _rpc(None, "initialize", {
        "protocolVersion": PROTOCOL, "capabilities": {},
        "clientInfo": {"name": "ndupload", "version": "1.0"}}, rid=1)
    try:
        _rpc(sid, "notifications/initialized", rid=2)
    except urllib.error.HTTPError:
        pass

    up = _call(sid, "tdrive.file_upload", {
        "dir_id": dir_id, "file_name": name, "file_size": size,
        "conflict_strategy": "overwrite"}, rid=3)
    if not up.get("path"):
        print(f"✗ 未拿到上传路径：{up}")
        return 1
    url = "https://" + up["domain"] + up["path"]
    print(f"上传 {name}（{size} B）→ dir {dir_id}")

    cmd = ["curl", "-sSL", "-X", "PUT"]
    for k, v in up.get("headers", {}).items():
        cmd += ["-H", f"{k}: {v}"]
    cmd += ["-T", os.path.abspath(local), url]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or r.stderr.strip():
        print(f"✗ PUT 失败 exit={r.returncode}\n{r.stderr[:400]}")
        return 1
    # 关键：COS 出错时返回的是 exit=0 + 空 stderr + XML <Error> 正文。
    # 只看 returncode/stderr 会把「签名错 → 内容根本没传上去」判成成功，
    # 于是后面照常落库，网盘里存的还是旧内容——比直接报错更危险。
    body = (r.stdout or "").lstrip()
    if body.startswith("<?xml") or "<Error>" in body[:200]:
        print(f"✗ PUT 被服务端拒绝（exit=0 但返回 XML 错误体）：\n{body[:400]}")
        return 1
    print("✓ PUT 完成（响应体无错误）")

    done = _call(sid, "tdrive.file_upload_complete", {
        "dir_id": dir_id, "file_name": name, "file_size": size,
        "confirm_key": up["confirm_key"], "task_id": up["task_id"]}, rid=4)
    print(f"✓ 落库完成 → file_id={done.get('file_id', '(未返回)')}")
    print(json.dumps(done, ensure_ascii=False)[:300])
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
