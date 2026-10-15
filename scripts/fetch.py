#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch.py —— 从 JSON 读 download_url 并原样下载（不经手抄、不做任何拼接）

为什么必须有这个脚本
────────────────────
网盘 file_download 返回的 URL 长达 1000+ 字符，且是签名 URL。
手抄到 shell 里几乎必错 —— 实测 2026-10-15 一天内错3 次：
  1 次 InvalidAccessKeyId（字符抄错，签名不匹配）
  1 次 403（签名超过 1 小时窗口）
  1 次 InvalidAccessKeyId（`WwrxbwQQ` vs `WwrxbqQQ`）
「把返回写成 JSON 再读」这个中转环节同样容易出错，
所以正确做法是：**让 agent 用程序把 URL 交给下载器，不经过字符搬运**。

用法：python3 scripts/fetch.py <meta.json> <输出路径>
其中 meta.json 就是 file_download 的原始返回。
⚠️ 禁止对 download_url 做任何拆分、解析、追加参数或二次编码。
"""
import json
import os
import subprocess
import sys

payload = json.load(open(sys.argv[1], encoding="utf-8"))
url = payload["download_url"]
out = sys.argv[2]

# 落盘前先验长度 —— 签名 URL 被截断是最常见的事故
if len(url) < 500:
    print(f"⚠️ URL 仅 {len(url)} 字符，疑似被截断（正常应 >800）。仍尝试下载…")

r = subprocess.run(["curl", "-sSL", "--fail-with-body", "-o", out, url],
                   capture_output=True, text=True)
if r.returncode != 0:
    print(f"✗ 下载失败 exit={r.returncode}\n{r.stderr[:400]}")
    blob = r.stdout + r.stderr
    if "InvalidAccessKeyId" in blob:
        print("  → 签名无效，几乎必然是 URL 被手动改动过。请让 agent 用程序传递，不要手抄。")
    if "403" in blob:
        print("  → 可能是签名过期（窗口约 1 小时），重新调 file_download。")
    sys.exit(1)

data = open(out, "rb").read()
head = data[:200].decode("utf-8", "ignore")
if head.lstrip().startswith("<?xml") and "<Error>" in head:
    print(f"✗ 返回的是错误 XML 而非文件：{head[:200]}")
    sys.exit(1)

print(f"{len(data)} bytes -> {out}  ({os.path.getsize(out)} on disk)")
print("前 80 字:", head[:80].replace("\n", " "))