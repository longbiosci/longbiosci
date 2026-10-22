#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen-redirects.py —— 由 data/redirects.json 批量生成「页面已迁移」占位页

要解决什么
────────
被删除/更名的文章 URL 目前直接 404。外链（他人的引用、社交传播、RSS 历史、
读者的书签）点进来就是死路，且这些 URL 上累积的外链权重全部作废。

GitHub Pages 是纯静态托管，**发不出真正的 301**。行业通行替代品是
「meta refresh(0) + JS 跳转 + canonical 指向目标」三件套：
  - 访客：0 秒跳转，几乎无感
  - 爬虫：canonical 把本页的信号合并到目标页，权重随之外链传导
  - 禁用 JS 的访客：正文留有可点击链接，仍能到达

为什么**不加** noindex
────────────────
本仓库此前手工写的迁移页（news/ARDD-*.html）用的是
「canonical 自指 + noindex」——那样是**安全的，但权重不传导**：
noindex 会让搜索引擎丢弃该页全部信号，外链等于白攒。
本工具改用 canonical 指向保留版本 + 不写 noindex，
目的就是清单 P1 #6 写的那句「把外链权重导到保留版本」。

资料来源与纪律
────────────
- 映射**只**来自 data/redirects.json（人工确认过的事实源），绝不自动推断。
- 目标页面不存在时**拒绝生成**并计入失败：宁可不生成，也不能造出指向
  404 的跳转页——那比留着 404 更糟（还多一层跳转）。
- 遇到磁盘上已存在、且不是本工具产出的页面：**不覆盖**。
  人工页面可能有本工具不知道的内容；只在此页面正文极短（<200 字，
  已是简单迁移标语）时才「收养」它，把它升级成规范格式。
  更大的页面必须显式 `--adopt=xxx.html` 才接管——**先人工比对确认它是
  目标页的内容子集，再授权**，否则一律跳过并列入未处理清单。

幂等
────
重复运行改动数为 0（内容一致则不写盘）。

用法
────
    python3 scripts/gen-redirects.py [仓库根目录] [--adopt=a.html,b.html]

映射值写法
────────
    "旧文件名.html": "新文件名.html"      → news/ 下的文章迁移（默认）
    "about.html":    "/about/"            → 根级页面迁移，值以 / 开头
"""
import json
import os
import re
import sys

SITE = "https://longbiosci.com"
# 工具自证标记：check-links.py 据此对该页豁免「canonical 必须自指」，
# 改为要求「canonical 必须指向真实目标」。没有这个标记，迁移页每次都会被误判。
STUB_MARK = "lb-redirect-stub"
# 正文短于此字数（纯标签去干净后）且含迁移字样 → 判定为简单迁移标语，可安全收养
ADOPT_MAX_LEN = 200
ADOPT_HINT = ("页面已迁移", "正在跳转到", "已更名", "moved", "redirect")

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>页面已迁移 - LongBiosci</title>
<link rel="canonical" href="{canon}">
<meta http-equiv="refresh" content="0; url={canon}">
<meta property="og:url" content="{canon}">
<meta property="og:title" content="页面已迁移 - LongBiosci">
<meta name="robots" content="index, follow">
<!-- {mark} 由 scripts/gen-redirects.py 依据 data/redirects.json 生成，勿手工编辑。
     旧 URL 的守卫页：canonical 指向保留版本以传导外链权重，故**不能**加 noindex。
     刻意不挂 analytics——访客 0 秒即离开，统计无意义且污染数据。 -->
</head>
<body>
<p>本页已迁移，正在跳转……</p>
<p>若未自动跳转，请访问：<a href="{canon}">{canon}</a></p>
<script>window.location.replace("{canon}");</script>
</body>
</html>
"""


def render(target_url):
    return TEMPLATE.format(canon=target_url, mark=STUB_MARK)


def plain_len(html):
    """去掉 script/style/标签后的正文长度，用于判断页面是否只是个迁移标语。"""
    b = re.sub(r"<script.*?</script>", "", html, flags=re.S | re.I)
    b = re.sub(r"<style.*?</style>", "", b, flags=re.S | re.I)
    b = re.sub(r"<head.*?</head>", "", b, flags=re.S | re.I)
    t = re.sub(r"<[^>]+>", " ", b)
    return len(re.sub(r"\s+", "", t))


def is_adoptable(html):
    """仅当页面短到「不含任何实质内容」时才允许接管，避免静默毁掉人工页面。"""
    if STUB_MARK in html:
        return True
    if plain_len(html) > ADOPT_MAX_LEN:
        return False
    low = html.lower()
    return any(k.lower() in low for k in ADOPT_HINT)


def url_to_disk(root, url):
    """站内 URL（/x/y.html 或 /x/）→ 磁盘路径；None 表示非本站路径。"""
    u = url.split("#")[0].split("?")[0]
    if not u.startswith("/"):
        return None
    disk = os.path.join(root, u.lstrip("/"))
    if u.endswith("/") or u == "":
        disk = os.path.join(disk, "index.html")
    return disk


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    root = args[0] if args else "."
    # 显式授权收养的页面（先比对确认它是目标页的内容子集，再授权）
    authorized = set()
    for a in sys.argv[1:]:
        if a.startswith("--adopt="):
            authorized.update(x.strip() for x in a.split("=", 1)[1].split(",") if x.strip())

    rd_path = os.path.join(root, "data", "redirects.json")
    if not os.path.exists(rd_path):
        print(f"❌ 找不到 {rd_path}"); return 1

    rd = json.load(open(rd_path, encoding="utf-8"))
    pairs = [(k, v) for k, v in rd.items()
             if not k.startswith("_") and isinstance(v, str)]
    pairs.sort()

    news = os.path.join(root, "news")
    os.makedirs(news, exist_ok=True)

    created = updated = adopted = skipped = 0
    failed = []

    for src, dst in pairs:
        if dst.startswith("/"):
            # 根级页面迁移：值写成站内绝对路径（如 /about/）
            src_path = os.path.join(root, src)
            target_url = SITE + dst
            dst_path = url_to_disk(root, dst)
            label = src
        else:
            # 默认：news/ 下的文章迁移（兼容写成 news/xxx.html 的历史条目）
            src_rel = src[len("news/"):] if src.startswith("news/") else src
            dst_rel = dst[len("news/"):] if dst.startswith("news/") else dst
            src_path = os.path.join(news, src_rel)
            dst_path = os.path.join(news, dst_rel)
            target_url = f"{SITE}/news/{dst_rel}"
            label = f"news/{src_rel}"

        if dst_path is None or not os.path.exists(dst_path):
            failed.append(f"目标缺失  {label} -> {dst}")
            continue

        # canonical 用站点绝对 URL 形式：check-links 只认绝对 URL
        content = render(target_url)

        if os.path.exists(src_path):
            old = open(src_path, encoding="utf-8", errors="ignore").read()
            if old == content:
                skipped += 1
                continue
            rel = os.path.relpath(src_path, root).replace("\\", "/")
            if not is_adoptable(old) and rel not in authorized:
                skipped += 1
                failed.append(f"已有人工页面，未覆盖  {label} "
                              f"（正文 {plain_len(old)} 字；"
                              f"确认是目标页子集后可 --adopt={rel}）")
                continue
            if STUB_MARK in old:
                updated += 1
            else:
                adopted += 1
        else:
            created += 1
        with open(src_path, "w", encoding="utf-8") as f:
            f.write(content)

    print(f"[迁移页] 映射 {len(pairs)} 条：新建 {created} · 更新 {updated} · "
          f"收养 {adopted} · 无变化 {skipped}")
    if failed:
        print(f"⚠️  {len(failed)} 条未生成：")
        for s in failed:
            print(f"   {s}")
        return 1
    print("✅ 全部迁移页已就位（目标均已存在，无指向 404 的跳转）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
