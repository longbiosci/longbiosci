#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
openrxiv_fetch.py —— 从 openRxiv 官方 S3 全文仓库取预印本全文（MECA）

## 为什么需要这个脚本

`www.biorxiv.org` 对本环境**全站 Cloudflare 403**（主页 / `.full` / `.full.pdf` / `jatsxml
全封），经 4 条独立路径验证属 **IP 级封禁**，等也不会恢复（2026-10-18 20:09 与
2026-10-19 02:31 两次测试相隔 6 小时，均为 403）。

但 openRxiv 另有一套**完全不经过 Cloudflare 的官方全文仓库**（供文本与数据挖掘 TDM 用）：

    s3://biorxiv-src-monthly/Current_Content/<Month_Year>/<uuid>.meca
    s3://medrxiv-src-monthly/Current_Content/<Month_Year>/<uuid>.meca

MECA 就是个 zip，里面 `content/*.xml` 是**完整正文的 JATS XML**（比 PDF 更适合做解读，
因为结构化、可直接抽段落/图表说明/方法）。

## 计费（重要）

这些桶是 **requester pays**：$0.09/GB，请求方账号付费。
实测单篇 MECA 约 6 MB → **每篇约 ¥0.004**；每天下 10 篇，**一个月不到 ¥2**。
匿名访问返回 403，错误信息为 "Anonymous users cannot invoke requests against
Requester Pays buckets" —— **这是"要认证付费"，不是"被封锁"**，与上面的封禁性质不同，
别看到 403 就以为这条路也走不通。

## 凭证

按顺序查找：
  1. 环境变量  AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY（可加 AWS_SESSION_TOKEN）
  2. ~/.aws/credentials（profile 默认 default，可用 --profile 指定）

**凭证绝不写入仓库**，也绝不打印到日志。

## 用法

    python3 scripts/openrxiv_fetch.py <DOI> [--out DIR] [--server biorxiv|medrxiv] [--profile NAME]

成功时在 --out（默认 ./meca_out）下产出：
    <slug>.meca          原始 MECA 包
    <slug>.full.xml      正文 JATS XML
    <slug>.full.txt      纯文本正文（供解读使用）
    <slug>.meta.json     本次取文元信息（DOI / s3Key / 字节数 / 时间）

退出码：0 成功；2 缺凭证；3 未定位到 s3Key；4 下载失败；5 包内无正文 XML。
"""

import argparse
import datetime as dt
import json
import os
import re
import sys
import zipfile

BUCKETS = {
    "biorxiv": "biorxiv-src-monthly",
    "medrxiv": "medrxiv-src-monthly",
}

# 第三方 DOI → S3 位置查询（公开，无需 AWS 凭证）
API_TPL = "https://openrxiv.csf.now/v1/works/{doi}"


def log(msg):
    print(msg, file=sys.stderr, flush=True)


def load_credentials(profile="default"):
    """返回 (key_id, secret, token) 或 None。"""
    kid = os.environ.get("AWS_ACCESS_KEY_ID")
    sec = os.environ.get("AWS_SECRET_ACCESS_KEY")
    tok = os.environ.get("AWS_SESSION_TOKEN")
    if kid and sec:
        return kid, sec, tok

    path = os.path.expanduser("~/.aws/credentials")
    if not os.path.exists(path):
        return None
    try:
        import configparser

        cp = configparser.ConfigParser()
        cp.read(path)
        if profile not in cp:
            return None
        s = cp[profile]
        kid = s.get("aws_access_key_id")
        sec = s.get("aws_secret_access_key")
        tok = s.get("aws_session_token")
        if kid and sec:
            return kid, sec, tok
    except Exception as e:
        log(f"读取 ~/.aws/credentials 失败：{e}")
    return None


def lookup_s3_key_via_api(doi):
    """用公开 API 查 s3Bucket/s3Key。返回 (bucket, key, filesize) 或 None。"""
    import urllib.request

    url = API_TPL.format(doi=doi)
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "longbiosci-openrxiv-fetch/1.0"}
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.load(r)
    except Exception:
        return None
    vers = d.get("versions") or []
    if not vers:
        return None
    v = vers[-1]
    return v.get("s3Bucket"), v.get("s3Key"), v.get("fileSize")


def slugify(doi):
    s = doi.split("/")[-1]
    s = re.sub(r"[^A-Za-z0-9._-]", "_", s)
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("doi")
    ap.add_argument("--out", default="./meca_out")
    ap.add_argument("--server", default=None, choices=["biorxiv", "medrxiv"])
    ap.add_argument("--profile", default="default")
    a = ap.parse_args()

    doi = a.doi.strip()
    outdir = a.out
    os.makedirs(outdir, exist_ok=True)

    # 1) 先查公开的 DOI→S3 映射
    hit = lookup_s3_key_via_api(doi)
    if hit and hit[0] and hit[1]:
        bucket, key, size = hit
        log(f"API 命中：s3://{bucket}/{key}（{size} B）")
    else:
        server = a.server or ("medrxiv" if doi.startswith("10.1101/2020") else "biorxiv")
        log(f"API 无索引，需按目录列举定位（server={server}）。凭证到位后实现列举匹配。")
        print(f"UNMAPPED\t{doi}\t{server}")
        sys.exit(3)

    # 2) 下载（requester pays）
    creds = load_credentials(a.profile)
    if not creds:
        log("缺少 AWS 凭证：请设置 AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY，或写入 ~/.aws/credentials")
        sys.exit(2)
    try:
        import boto3
        from botocore.config import Config

        cfg = Config(connect_timeout=30, read_timeout=180, retries={"max_attempts": 3})
        s3 = boto3.client(
            "s3",
            aws_access_key_id=creds[0],
            aws_secret_access_key=creds[1],
            aws_session_token=creds[2],
            config=cfg,
        )
        slug = slugify(doi)
        mpath = os.path.join(outdir, slug + ".meca")
        s3.download_file(bucket, key, mpath, ExtraArgs={"RequestPayer": "requester"})
    except SystemExit:
        raise
    except Exception as e:
        log(f"下载失败：{e}")
        sys.exit(4)

    # 3) 解包抽正文
    try:
        with zipfile.ZipFile(mpath) as z:
            names = z.namelist()
            xmls = [n for n in names if n.startswith("content/") and n.endswith(".xml")]
            pdfs = [n for n in names if n.lower().endswith(".pdf")]
            if not xmls:
                log(f"包内无正文 XML，仅有：{names[:10]}")
                sys.exit(5)
            # 正文通常是 content/ 下最大的那个 xml
            def xsize(n):
                return z.getinfo(n).file_size
            main = max(xmls, key=xsize)
            raw = z.read(main)
        txt = raw.decode("utf-8", errors="replace")
    except SystemExit:
        raise
    except Exception as e:
        log(f"解包失败：{e}")
        sys.exit(5)

    slug = slugify(doi)
    xpath = os.path.join(outdir, slug + ".full.xml")
    tpath = os.path.join(outdir, slug + ".full.txt")
    open(xpath, "wb").write(raw)

    # 抽纯文本：去掉标签，保留段落
    body = txt
    m = re.search(r"<body\b.*?</body>", body, re.S)
    if m:
        body = m.group(0)
    body = re.sub(r"<(table-wrap|inline-formula|disp-formula)\b.*?</\1>", " [公式/表格] ", body, flags=re.S)
    body = re.sub(r"<title>", "\n## ", body)
    body = re.sub(r"<p\b[^>]*>", "\n", body)
    body = re.sub(r"<[^>]+>", "", body)
    import html as _h

    body = _h.unescape(body)
    body = re.sub(r"\n\s*\n+", "\n\n", body).strip()
    open(tpath, "w", encoding="utf-8").write(body)

    meta = {
        "doi": doi,
        "server": "bioRxiv" if "bio" in (bucket or "") else "medRxiv",
        "s3_bucket": bucket,
        "s3_key": key,
        "meca_bytes": os.path.getsize(mpath),
        "xml_entry": main,
        "txt_chars": len(body),
        "has_pdf_in_meca": bool(pdfs),
        "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    open(os.path.join(outdir, slug + ".meta.json"), "w", encoding="utf-8").write(
        json.dumps(meta, ensure_ascii=False, indent=2)
    )
    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
