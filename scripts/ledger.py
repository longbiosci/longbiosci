# -*- coding: utf-8 -*-
"""
ledger.py —— 内容台账与对账（Content Ledger & Reconciliation）

为什么需要它
────────────
上一轮暴露的真问题不是「不会写文章」，而是**没人能回答「该有的都有吗」**：
  - 产出文件的卡片数 ≠ 上站数（09-25 期 51 条里 48 条已在站，差异无记录）
  - 同一个 DOI 可能同时出现在多期卡片里（跨期增量），重复上报
  - size=0 的产出文件此前一直没人发现，直到写脚本时才撞见
  - 网盘文件的存在性 ≠ 内容有效（空文件、签名过期下载失败）

本脚本建立**双向可对账**的台账：
  产出侧：产出文件里声称收录的全部条目（按 DOI / 标题指纹归一）
  上站侧：news/*.html 实际存在的全部文章（同样归一）
  对账：① 产出有、上站无 → 漏收（必须逐条处置）② 上站有、产出无 → 孤站（可接受但要计数）

用法
────
  # 1) 扫描产出并写入台账
  python3 scripts/ledger.py build <repo> <产出文件...>

  # 2) 对账并报告
  python3 scripts/ledger.py audit <repo> [--out data/ledger.json]

台账落data/ledger.json（入库），作为「上一轮处理到哪」的锚点。
"""
import glob
import hashlib
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harvest import (parse_md_tables, pick_title_col, extract_doi,  # noqa: E402
                     load_slugs_and_dois, ngrams, jaccard,
                     normalize_doi, slug_tokens, token_overlap)


def norm_doi(d):
    return normalize_doi(d)


def fingerprint(title, doi=""):
    """条目的稳定指纹：优先 DOI，无DOI 时用标题词集合的哈希"""
    if doi:
        return "doi:" + norm_doi(doi)
    n = sorted(ngrams(title, n=3))[:12]
    return "t:" + hashlib.sha1("|".join(n).encode()).hexdigest()[:16]


def scan_outputs(paths):
    """从产出文件抽出全部条目，按指纹去重（跨期重复会合并）"""
    seen = {}
    per_file = {}
    for p in paths:
        if not os.path.exists(p):
            continue
        text = open(p, encoding="utf-8", errors="ignore").read()
        n = 0
        for tb in parse_md_tables(text):
            if not tb["rows"]:
                continue
            ti = pick_title_col(tb["header"])
            for cells in tb["rows"]:
                if len(cells) <= ti:
                    continue
                title = re.sub(r"\*\*|\*|\[|\]|\(.*?\)", "", cells[ti]).strip()
                if len(title) < 12:
                    continue
                doi = extract_doi(cells)
                code = cells[0].strip()
                fp = fingerprint(title, doi)
                if fp not in seen:
                    seen[fp] = {
                        "fingerprint": fp, "title": title[:300], "doi": doi,
                        "code": code if re.match(r"^[A-Za-z]{0,4}\d{1,3}$", code) else "",
                        "seen_in": [],
                    }
                seen[fp]["seen_in"].append(os.path.basename(p))
                n += 1
        per_file[os.path.basename(p)] = {
            "rows": n,
            "bytes": os.path.getsize(p),
            "suspicious_empty": os.path.getsize(p) == 0,
        }
    return seen, per_file


def scan_site(root):
    """扫描站内实际文章，返回 {指纹: slug} 与 DOI 集合"""
    slugs, titles, dois = load_slugs_and_dois(root)
    out = {}
    for slug, t in titles.items():
        fp = fingerprint(t)
        out.setdefault(fp, slug)
    return slugs, titles, dois, out


def audit(root, outputs, entries=None, per_file=None):
    """双向对账

    entries / per_file 传入 build 阶段的持久化清单；
    不传则现场扫 outputs 文件。两者都不为空时合并。
    """
    slugs, titles, dois, site_fp = scan_site(root)
    items, scanned = scan_outputs(outputs) if outputs else ({}, {})
    if entries:
        for e in entries:                # 持久化清单优先，保留其 seen_in
            fp = e["fingerprint"]
            if fp not in items:
                items[fp] = e
            else:
                items[fp]["seen_in"] = sorted(set(
                    items[fp]["seen_in"]) | set(e.get("seen_in", [])))
    merged_files = dict(per_file or {})
    merged_files.update(scanned)
    per_file = merged_files

    missing, covered = [], 0
    for fp, it in items.items():
        if it["doi"] and norm_doi(it["doi"]) in dois:
            covered += 1
            it["status"] = "已收录"
            it["basis"] = f"DOI 命中 {norm_doi(it['doi'])}"
            continue
        # 站内指纹可能因中文译名而对不上，退化为标题相似度
        best, bs = 0.0, ""
        tn = ngrams(it["title"])
        for slug, t in titles.items():
            j = jaccard(tn, ngrams(t))
            if j > best:
                best, bs = j, slug
        if best >= 0.34:
            it["status"] = "已收录"
            it["basis"] = f"标题相似 {best:.2f} → {bs}"
            covered += 1
            continue
        # 第 4 路：英文原标题 vs 站内英文 slug 的词元重叠（绕开中文译名盲区）
        tt = slug_tokens(it["title"])
        # r 必须在 if 之外初始化：标题词元 <2 个时第 4 路整段跳过，
        # 但下面的「漏收」basis 仍要打印 `词元重叠 {r:.2f}` —— 未初始化会让
        # 整份 audit 报告崩掉（与 harvest.py 的 tob 属同一类缺陷）。
        r = 0.0
        if len(tt) >= 2:
            r, inter = 0.0, []
            bslug = ""
            # 必须 sorted()：slugs 是 set，直接迭代其顺序受 PYTHONHASHSEED 影响。
            # 多个 slug 得分并列时（r > tob 只留第一个赢家），赢家不同则 inter 不同，
            # 而下面的判据含 len(inter) >= 3 —— 于是同一份数据两次 audit 会给出
            # 不同的「已收录/漏收」计数（实测 173/177 ↔ 171/179）。
            # 审计工具自己不确定，就没资格当收尾自检。
            for slug in sorted(slugs):
                rr, ii = token_overlap(tt, slug_tokens(slug))
                if rr > r:
                    r, inter, bslug = rr, ii, slug
            if len(inter) >= 3 and r >= 0.5:
                it["status"] = "已收录"
                it["basis"] = f"slug 词元重叠 {r:.2f}（{len(inter)} 词）→ {bslug}"
                covered += 1
                continue
        it["status"] = "漏收"
        it["basis"] = (f"四路均未命中（DOI={it['doi'] or '无'}，标题相似 {best:.2f}，"
                       f"词元重叠 {r:.2f}）"
                       + ("；★中文摘要条目，必须人工核对站内中文关键词"
                          if re.search(r"[一-鿿]", it["title"]) else ""))
        missing.append(it)

    # 孤站：站内有、任何产出都没有（允许存在，但要计数）
    orphan = sorted(set(slugs) - {
        s for fp, s in site_fp.items()
        if any(m["fingerprint"] == fp for m in items.values())})

    report = {
        "site": {"articles": len(slugs), "dois": len(dois)},
        "outputs": per_file,
        "output_entries": len(items),
        "covered": covered,
        "missing_count": len(missing),
        "missing": missing,
        "orphan_count": len(orphan),
        "orphan_sample": orphan[:20],
        "note": ("missing 必须逐条人工核对后再写稿。判定为「漏收」只代表三路均未命中，"
                 "不是结论——中文摘要条目尤其需要用中文关键词直接搜站内。"),
    }
    return report


def main():
    # 兼容两种写法：audit . / audit --repo .
    # SOP 文档里写的是 `--repo .`，而本脚本原本只认位置参数，
    # 照文档跑会得到一串莫名其妙的 "--repo/data/ledger.json 不存在"。
    # 与其让每轮都踩一次，不如两种都收下。
    argv = [a for a in sys.argv[1:] if a not in ("--repo", "-r")]
    if len(argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd, root = argv[0], argv[1]
    sys.argv = [sys.argv[0]] + argv

    if cmd == "build":
        files = [f for f in sys.argv[3:] if f != "--merge"]
        merge = "--merge" in sys.argv
        items, per_file = scan_outputs(files)
        out = os.path.join(root, "data/ledger-outputs.json")
        # --merge：与既有台账合并，而不是整体覆盖。
        # 为什么必须有：.intake/raw/ 是 gitignore 的暂存目录，换一个沙箱就空了，
        # 历史产出文件的原件再也拿不回来；而 build 原本是整文件覆写，
        # 拿当前目录下的文件 build 一次，就把前几轮 build 进去的历史记录静默抹掉了
        # （实测：已入库 5 个历史产出文件，原件均不在本沙箱）。
        # 产出台账是累积账，不是快照 —— 覆盖式写入等于让历史凭空消失。
        if merge and os.path.exists(out):
            saved = json.load(open(out, encoding="utf-8"))
            for e in saved.get("entries", []):
                fp = e["fingerprint"]
                if fp not in items:
                    items[fp] = e
                else:
                    items[fp]["seen_in"] = sorted(
                        set(items[fp]["seen_in"]) | set(e.get("seen_in", [])))
            for fn, meta in saved.get("files", {}).items():
                per_file.setdefault(fn, meta)
            print(f"--merge：已并入既有台账（原 {len(saved.get('files', {}))} 个文件）")
        json.dump({"entries": list(items.values()), "files": per_file},
                  open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"产出条目 {len(items)} 条（跨期去重后）→ {out}")
        for fn, meta in per_file.items():
            flag = "⚠️ 空文件" if meta["suspicious_empty"] else ""
            print(f"  {fn}: {meta['rows']} 行 / {meta['bytes']} B {flag}")

    elif cmd == "audit":
        # 产出侧清单优先读 data/ledger-outputs.json（build 阶段的持久化结果）。
        # 为什么不能只扫 .intake/raw：.intake/ 已gitignore（网盘产出副本不入库），
        # 清空暂存后 audit 会误报「产出条目 0」——那是对账能力的静默失效，
        # 比报错更危险。找不到持久化清单时明确告警而不是返回空结果。
        outfile = os.path.join(root, "data/ledger-outputs.json")
        files = sorted(glob.glob(os.path.join(root, ".intake/raw/*.md")))
        entries, per_file = [], {}
        if os.path.exists(outfile):
            saved = json.load(open(outfile, encoding="utf-8"))
            entries = saved.get("entries", [])
            per_file = saved.get("files", {})
            print(f"产出清单读自 {outfile}（{len(entries)} 条，"
                  f"{len(per_file)} 个文件）")
        else:
            print(f"⚠️ 未找到 {outfile} —— 产出侧清单缺失，对账结果不可信。\n"
                  f"   请先跑：python3 scripts/ledger.py build <repo> <产出文件...>\n")
        # 未 build 的文件默认「只告警、不入账」。
        # 为什么改：.intake/raw/ 里不只是产出副本——运营日志、待办清单（132 KB，
        # 满是 markdown 表格）、README、站点评估都在里面。它们一旦被 scan_outputs
        # 当成产出入口解析，对账数字就取决于「这个沙箱里恰好躺着什么文件」，
        # 而 .intake/ 是 gitignore 的、不进版本库——等于对账结果不可复现
        # （与 set 迭代顺序是同一类病：工具自己不确定，就不能当收尾自检）。
        # 安全网的价值在「提醒有文件没 build」，不在「替你把它算进去」。
        # 只提醒「真的没 build」的文件。2026-10-23 修：原逻辑只要
        # .intake/raw/ 里有 md 就报数，经 ledger-merge-outputs.py 并入
        # 台账的 6 个文件每次都被误报——收尾自检里的假警报比没有警报更坏。
        files = [f for f in files if os.path.basename(f) not in per_file]
        if files:
            print(f"另发现 {len(files)} 个 .intake/raw/*.md（未 build 进台账）")
            if "--include-unbuilt" in sys.argv:
                print("  --include-unbuilt 已指定 → 纳入本次对账")
            else:
                print("  默认不纳入：该目录混有运营日志/待办清单/README 等非产出文档，"
                      "静默并入会让对账随暂存目录漂移。")
                print("  确认它们均为产出文件时，追加 --include-unbuilt。")
                files = []
        rep = audit(root, files, entries=entries, per_file=per_file)
        out = os.path.join(root, "data/ledger.json")
        json.dump(rep, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"站内 {rep['site']['articles']} 篇 / DOI {rep['site']['dois']} 个")
        print(f"产出条目 {rep['output_entries']}（跨期去重后）· "
              f"已收录 {rep['covered']} · 漏收 {rep['missing_count']}")
        print(f"孤站 {rep['orphan_count']}（产出未提及，允许）")
        print(f"→ {out}\n")
        if rep["missing"]:
            print("漏收明细（必须逐条人工核对）：")
            for m in rep["missing"]:
                print(f"  [{m.get('code', ''):>4}] {m['title'][:62]}")
                print(f"         {m['basis'][:88]}")
        for fn, meta in rep["outputs"].items():
            if meta["suspicious_empty"]:
                print(f"\n⚠️ 产出文件为空: {fn} —— 该期内容实际缺失，需重跑对应任务")
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()