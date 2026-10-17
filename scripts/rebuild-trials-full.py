#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rebuild-trials-full.py —— 用上游新版《衰老与长寿相关临床试验登记清单》重建宽口径检索库

存在理由
────────
本站 /trials-full.html 的数据源 data/trials-full.json 长期停在 **558 项**（2026-10-01 口径）。
2026-10-18 上游产出方法论重建版，**462 项**（新增 27 / 退出 123）。若不同步，
「全量检索库」会持续对外宣称一个已经不成立的口径。

为什么不能直接拿新版的 _snapshot.json
────────────────────────────────────
新版 snapshot 每条只有 {nct, status, brief, categories, last_update} 五项，
而 /trials-full.html 的渲染 JS 需要 title / phase / intervention / conditions /
sponsor / country / tags 共 10 个字段。直接替换会让页面上出现大片 undefined。
另外：旧版 snapshot file_id（dXnPTXlfISVq）已被上游删除（file_download 返回
「文件不存在」），拿不回来做字段补全。

因此本脚本从新版 **Markdown 清单**解析——它的方向清单表格恰好带全这 10 列，
是唯一同时具备「新口径 + 完整字段」的数据源。

保守策略（重要）
────────────────
旧库里存在、新版没抓到的条目，暂**不物理删除**：落盘为 462 项新主库的同时，
把差额输出到 data/trials-full-retired.json 备查，并在页面加口径变更说明。
这样使用者遇到「某试验搜不到了」时，能判断它是「已完成」还是「被口径剔除」。

用法
────
  python3 scripts/rebuild-trials-full.py [新版清单.md]
"""
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IN = sys.argv[1] if len(sys.argv) > 1 else ".intake/raw/trials-list-2026-10-18.md"
OLD = os.path.join(ROOT, "data", "trials-full.json")
OUT = os.path.join(ROOT, "data", "trials-full.json")
RET = os.path.join(ROOT, "data", "trials-full-retired.json")
TZ = timezone(timedelta(hours=8))

HEADER_NCT = {"nct id", "nct编号", "nct"}


def _g(cells, idx):
    """按列索引安全取值：表格里偶有缺列/多列的行，index 直取会 IndexError。"""
    return cells[idx] if isinstance(idx, int) and 0 <= idx < len(cells) else ""


def strip_cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse(md_path):
    """解析 §二 各方向清单表格，返回 {nct: row}"""
    rows, cur_dir = {}, None
    with open(md_path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    i = 0
    in_section = False          # 只认「§二 各方向试验清单」，避免把 §三 对比章节算进去
    while i < len(lines):
        ln = lines[i].strip()

        # 章节边界：§二 进入，遇到下一个二级标题退出。
        # 不做这个限制的话，§3.1「新增 27 项」与 §3.3「退出 123 项」两个对比表
        # 会被二次计入——实测首版因此解析出 585 项（462 + 123），比真值多 27%。
        if ln.startswith("## "):
            in_section = ln.startswith("## 二")

        m = re.match(r"^###\s*2\.(\d+)\s+([^（(]+)", ln)
        if m and in_section:
            cur_dir = m.group(2).strip()
        if in_section and ln.startswith("|") and "NCT ID" in ln:
            head = strip_cells(ln)
            # 定位列：兼容列序变动
            col = {h.lower(): k for k, h in enumerate(head)}
            i += 2                                   # 跳过分隔行
            while i < len(lines) and lines[i].strip().startswith("|"):
                c = strip_cells(lines[i])
                if len(c) >= len(head) - 1:
                    nct = _g(c, col.get("nct id", 0)).strip()
                    if re.fullmatch(r"NCT\d{8}", nct):
                        tags = _g(c, col.get("方向标签", 9)).strip()
                        rows[nct] = {
                            "nct": nct,
                            "title": _g(c, col.get("试验标题", 1)).strip(),
                            "status": _status(_g(c, col.get("状态", 2)).strip()),
                            "phase": _g(c, col.get("阶段", 3)).strip() or "—",
                            "intervention": _g(c, col.get("干预（类型）", 4)).strip(),
                            "conditions": _g(c, col.get("主要适应症/条件", 5)).strip(),
                            "sponsor": _g(c, col.get("申办方", 6)).strip(),
                            "country": _g(c, col.get("国家/地区", 7)).strip(),
                            "last_update": _g(c, col.get("最近更新", 8)).strip(),
                            "tags": tags or cur_dir,
                            "link": "https://clinicaltrials.gov/study/" + nct,
                        }
                i += 1
            continue
        i += 1
    return rows


SMAP = {"招募中": "招募中", "尚未招募": "尚未招募", "邀请入组中": "邀请入组中",
        "RECRUITING": "招募中", "NOT_YET_RECRUITING": "尚未招募",
        "ENROLLING_BY_INVITATION": "邀请入组中"}


def _status(s):
    return SMAP.get(s, s)


def main():
    new = parse(IN)
    if not new:
        sys.exit(f"✗ 未从 {IN} 解析到任何试验行——表格格式可能变了")

    old = json.load(open(OLD, encoding="utf-8"))
    old_map = {t["nct"]: t for t in old["trials"]}

    # 幂等护栏：本脚本会覆写 OLD，重跑一次就变成拿自己的输出当基线，
    # 于是「新增 X 项」恒等于 0、「退出」恒等于 0 —— 差集静默失真，
    # 而这两个数字正是判断「这次刷新到底动了什么」的唯一依据。
    # 实测 2026-10-18 首跑后再次运行即触发（27 项新增被读成 0）。
    stamp = datetime.now(TZ).strftime("%Y%m%d%H%M%S")
    with open(OLD, encoding="utf-8") as _f:
        pass
    bak = OLD + ".prev"
    if os.path.exists(bak) and len(old_map) == len(new):
        sys.exit(f"✗ {OLD} 的大小与本次输出相同（{len(new)}），疑似已跑过一轮。"
                 f"请先把上一次的备份 {bak} 还原为 {OLD} 再运行。")
    with open(OLD, encoding="utf-8") as _f, open(bak, "w", encoding="utf-8") as _o:
        _o.write(_f.read())

    # 新版抓到、但缺完整字段的（理论上不应发生）：用旧版字段补
    filled = 0
    for nct, t in new.items():
        o = old_map.get(nct)
        if o and not t.get("sponsor"):
            t.update({k: o[k] for k in o if k not in t or not t[k]})
            filled += 1

    trials = sorted(new.values(), key=lambda x: (x["last_update"], x["nct"]), reverse=True)

    doc = {
        "generated_at": datetime.strptime(
            re.search(r"生成时间\*\*：(\S+)", open(IN, encoding="utf-8").read()).group(1),
            "%Y-%m-%d").strftime("%Y-%m-%d"),
        "source": ("ClinicalTrials.gov API v2（自动化任务产出，经网盘元层回收）"
                   " · 2026-10-18 起采用收紧后的相关性口径（原 558 → 现 %d 项）" % len(trials)),
        "total_unique": len(trials),
        "trials": trials,
    }
    json.dump(doc, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    retired = [old_map[n] for n in old_map if n not in new]
    json.dump({"generated_at": doc["generated_at"], "total": len(retired),
               "note": "上一期（558 项）存在、本期（%d 项）不再计入的条目，"
                       "含「真实状态转出」与「被口径收紧剔除」两类，上游未做归因拆分"
                       % len(new),
               "trials": retired},
              open(RET, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print(f"✔ {OUT}：{len(trials)} 项（旧库 558 → 新库 {len(trials)}，"
          f"净变动 {len(trials) - len(old['trials'])}）")
    print(f"  其中沿用旧字段补全 {filled} 项")
    print(f"✔ {RET}：{len(retired)} 项差额备查（未做归因拆分，见上游反馈）")
    print(f"  新库独有（真新增）：{sum(1 for n in new if n not in old_map)} 项")
    return 0


if __name__ == "__main__":
    sys.exit(main())
