#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ndfetch.py —— 网盘下载一站式：拿签名 URL → 交给 fetch.py 下载 → 校验文件

为什么要有这一层
────────────────
file_download 返回的是 1000+ 字符的签名 URL。只要这个 URL 经过「人眼→手指→终端」
这条链路，就一定会错（实测 2026-10-15 一天 3 次：InvalidAccessKeyId ×2、403 ×1）。

fetch.py 解决了「下半段」（URL 已在 JSON 里 → 下载），但上半段——
怎么把 URL 弄进那个 JSON——此前仍然靠手抄，等于把雷留在了最关键的一步。

本脚本补齐上半段：直接调网盘 MCP 的 HTTP 端点拿返回，
用程序把 download_url 原样写进 meta.json，再调用 fetch.py。
**全程 URL 不经人手，也不经 agent 的上下文**。

用法
────
  python3 scripts/ndfetch.py <file_id> <输出路径>
  python3 scripts/ndfetch.py dBBZqfrAlUWW .intake/raw/preprint-2026-09-13.md

依赖：curl、python3 标准库。MCP 端点来自 ~/.codebuddy/.mcp.json（netdrive）。
"""
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

MCP_URL = "http://netdrive.agent-gateway.auth-proxy.local/mcp"
PROTOCOL = "2025-06-18"


def _rpc(session, method, params=None, rid=1):
    """MCP streamable-HTTP：一次 POST 一个 JSON-RPC 消息，响应体是 JSON 或 SSE"""
    body = json.dumps({"jsonrpc": "2.0", "id": rid, "method": method,
                       "params": params or {}}).encode()
    headers = {"Content-Type": "application/json",
               "Accept": "application/json, text/event-stream"}
    if session:
        headers["Mcp-Session-Id"] = session
    req = urllib.request.Request(MCP_URL, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        new_sid = r.headers.get("Mcp-Session-Id") or session
        raw = r.read().decode("utf-8", "ignore")
    # SSE 包装：取最后一个 data: 行
    if raw.lstrip().startswith("event:") or "\ndata:" in raw:
        lines = [l[5:] for l in raw.splitlines() if l.startswith("data:")]
        raw = lines[-1] if lines else raw
    return new_sid, json.loads(raw)


def file_download(file_id):
    sid, _ = _rpc(None, "initialize", {
        "protocolVersion": PROTOCOL, "capabilities": {},
        "clientInfo": {"name": "ndfetch", "version": "1.0"}}, rid=1)
    try:
        _rpc(sid, "notifications/initialized", rid=2)
    except urllib.error.HTTPError:
        pass                                   # 通知无响应是正常的
    _, resp = _rpc(sid, "tools/call", {
        "name": "tdrive.file_download", "arguments": {"file_id": file_id}}, rid=3)
    if "error" in resp:
        raise RuntimeError(f"MCP 错误：{resp['error']}")
    texts = [c.get("text", "") for c in resp["result"].get("content", [])]
    return json.loads(texts[0]) if texts else {}


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    file_id, out = sys.argv[1], sys.argv[2]
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)

    meta = file_download(file_id)
    if not meta.get("download_url"):
        print(f"✗ 未拿到 download_url：{meta}")
        return 1

    tmp = out + ".__meta.json"
    # 原样落盘——不做任何拆分、拼接、二次编码
    json.dump(meta, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"URL {len(meta['download_url'])} 字符 · {meta.get('name', '')}")

    r = subprocess.run([sys.executable, "scripts/fetch.py", tmp, out])
    os.unlink(tmp)
    if r.returncode != 0:
        return r.returncode

    # 大小校验：网盘 size 与实际字节数不一致 = 半载或错文件
    size = int(meta.get("size") or 0)
    got = os.path.getsize(out)
    if size and abs(got - size) > max(64, size * 0.02):
        print(f"⚠️ 大小不符：网盘 {size} B，实得 {got} B（差 {got - size}）")
    else:
        print(f"✓ 大小校验通过（{got} B）")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
