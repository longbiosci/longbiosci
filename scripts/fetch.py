#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 JSON 读取 file_download 返回的 download_url 并下载（原样使用，不做任何拼接）"""
import json
import subprocess
import sys
import urllib.request

payload = json.load(open(sys.argv[1], encoding="utf-8"))
url = payload["download_url"]
out = sys.argv[2]

req = urllib.request.Request(url, method="GET")
with urllib.request.urlopen(req, timeout=180) as r:
    data = r.read()
open(out, "wb").write(data)
print(f"{len(data)} bytes -> {out}")
print("前80 字:", data[:80].decode("utf-8", "ignore").replace("\n", " "))