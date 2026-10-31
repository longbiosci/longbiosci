#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_trials_milestones.py —— /trials/milestones/ 关键试验里程碑页（管线第 7c 环节）

用法：python3 scripts/gen_trials_milestones.py <仓库根目录>

为什么要有这一页
────────────────
站上此前只有一个静态的 /trials.html（临床试验清单入口），而真正带**状态变更**的
资产级事实（谁推进了、谁回撤了、什么时候变的、出处在哪）只存在于行业情报班 7762986
交付到网盘行业层的《管线状态基线.json》里——读者在站上完全看不到，运营侧也只能靠
下载 md 才能核对。本页把这份基线搬进站内：

  · **数据源 = data/trials-baseline.json**（由行业层《管线状态基线.json》v1.1
    原样导入，保留 file_id / 生成方 / 覆盖窗口等溯源字段，见文件内 source 段）；
  · **按状态变更日期倒序**，每条同时给出「变更日期」与「基线生成时间」两个时间戳
    —— 与文章页「情报发生日期 / 发布日期」同源口径，避免把基线快照日当成事件日；
  · 变更徽标沿用基线自身定义：⬆ 推进 / ⬇ 回撤 / 🔄 维持但关键信息更新 / — 基线建立；
  · 有 NCT 号的直链 ClinicalTrials.gov，无 NCT 的**如实留空**并给出公司官方出处，
    **不猜号、不补号**；每条必带 source 出处链接（基线 28/28 齐全）；
  · 幂等：产物由 data/trials-baseline.json 唯一决定，可反复运行。

产物：
  /trials/milestones/index.html   关键试验里程碑（按变更日期倒序 + 按变更类型分组）
  并向 /trials.html 注入一个带 lb-milestones-entry 标记的入口链接（幂等，
  必须在 gen-industry.py / normalize_nav.py 之后不被覆盖的位置运行，见 run-pipeline.sh）。

不做什么：不改写基线内容（导入即事实源，改了就不是可溯源基线）；
不动全站导航（新增导航项会挤压移动端两行预算，入口放在 /trials.html 内部即可）。
"""
import html
import json
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import importlib.util as _ilu


def _load(name, path):
    spec = _ilu.spec_from_file_location(name, path)
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_gi = _load("gen_industry", os.path.join(HERE, "gen-industry.py"))

# 变更类型：显示名 / 说明 / 分组顺序
CHANGE_ORDER = [
    ("⬆", "推进", "阶段推进 / 新增试验 / 首次人体 / 新增资格"),
    ("🔄", "更新", "阶段维持但关键信息更新"),
    ("⬇", "回撤", "主要终点未达 / 终止 / 资产出售 / 停止运营"),
    ("—", "基线", "基线建立，本期无变更"),
]
CHANGE_NAME = {k: v for k, v, _ in CHANGE_ORDER}
CHANGE_DESC = {k: d for k, _, d in CHANGE_ORDER}

STYLE = """
<style>
.tl-chips{display:flex;flex-wrap:wrap;gap:.4rem;margin:.8rem 0 1.2rem}
.tl-chip{display:inline-block;padding:.28rem .7rem;border:1px solid var(--line,#d8dee6);
border-radius:999px;font-size:.85rem;text-decoration:none;color:inherit}
.tl-chip:hover{border-color:var(--accent,#2f6feb)}
.ms{list-style:none;margin:0;padding:0}
.ms-item{position:relative;padding:0 0 1.15rem 1.55rem;border-left:2px solid var(--line,#d8dee6)}
.ms-item:last-child{border-left-color:transparent}
.ms-item::before{content:"";position:absolute;left:-7px;top:.45rem;width:12px;height:12px;
border-radius:50%;background:var(--accent,#2f6feb);border:2px solid #fff}
.ms-date{font-size:.8rem;color:var(--muted,#667);letter-spacing:.02em}
.ms-badge{display:inline-block;font-size:.75rem;padding:.1rem .45rem;border-radius:4px;
background:#eef2f7;margin-left:.4rem;vertical-align:1px}
.ms-title{font-weight:600;margin:.15rem 0 .2rem;font-size:1.02rem}
.ms-meta{font-size:.88rem;color:var(--muted,#556);margin:.1rem 0}
.ms-detail{font-size:.92rem;line-height:1.65;margin:.25rem 0 0}
.ms-src{font-size:.82rem;margin-top:.25rem}
.ms-src a{color:var(--accent,#2f6feb)}
.ms-note{font-size:.85rem;color:var(--muted,#667);margin-top:.15rem}
.tl-anchor{margin:1.6rem 0 .6rem;font-size:1.15rem}
.tl-n{font-size:.8rem;font-weight:400;color:var(--muted,#667);margin-left:.5rem}
table.ms-tbl{width:100%;border-collapse:collapse;font-size:.9rem;margin:.4rem 0 1rem}
table.ms-tbl th,table.ms-tbl td{border-bottom:1px solid var(--line,#e3e8ef);
padding:.4rem .5rem;text-align:left;vertical-align:top}
</style>
"""


def esc(s):
    return html.escape(str(s or ""), quote=True)


def nct_link(nct):
    nct = (nct or "").strip()
    if not nct:
        return ""
    return (f' · <a href="https://clinicaltrials.gov/study/{esc(nct)}" '
            f'rel="nofollow noopener" target="_blank">{esc(nct)}</a>')


def build(root):
    path = os.path.join(root, "data", "trials-baseline.json")
    if not os.path.exists(path):
        print("[milestones] 缺少 data/trials-baseline.json —— 跳过（不空产）",
              file=sys.stderr)
        return 0
    d = json.load(open(path, encoding="utf-8"))
    src = d.get("source") or {}
    items = list(d.get("pipelines") or [])

    # 硬断言：缺出处即构建失败——本页的全部价值就是「每条可回查」
    missing = [x for x in items if not (x.get("source") or "").strip()]
    if missing:
        print(f"[milestones] 断言失败：{len(missing)} 条基线缺少 source 出处链接",
              file=sys.stderr)
        return 1
    # 日期精度：接受 YYYY-MM-DD 与 YYYY-MM 两种。
    # 上游基线里确实存在月份精度的条目（如 Loyal LOY-003 = "2026-09"，官方稿只给到月），
    # 这不是错误而是来源精度——硬拒会让整条管线卡在一个合法上游格式上，
    # 故改为「接受两种精度 + 在页面上标注精度」，排序一律补齐到当月 1 日。
    bad_date = [x for x in items
                if not re.fullmatch(r"\d{4}-\d{2}(-\d{2})?", str(x.get("status_date") or ""))]
    if bad_date:
        print(f"[milestones] 断言失败：{len(bad_date)} 条基线 status_date "
              f"既非 YYYY-MM-DD 也非 YYYY-MM", file=sys.stderr)
        return 1
    month_only = [x for x in items
                  if re.fullmatch(r"\d{4}-\d{2}", str(x.get("status_date") or ""))]
    if month_only:
        print(f"[milestones] 注意：{len(month_only)} 条基线日期为月份精度"
              f"（{[x['status_date'] for x in month_only]}），页面标注「月份精度」并补齐排序")

    def sort_key(x):
        sd = str(x.get("status_date") or "")
        return (sd + "-01" if re.fullmatch(r"\d{4}-\d{2}", sd) else sd,
                x.get("company") or "")

    items.sort(key=sort_key, reverse=True)
    counts = Counter(x.get("change") or "—" for x in items)
    companies = len({x.get("company") for x in items if x.get("company")})
    with_nct = sum(1 for x in items if (x.get("nct") or "").strip())
    dates = sorted(x.get("status_date") for x in items if x.get("status_date"))

    # ── 变更类型锚点 ──
    chips = "".join(
        f'<a href="#c-{i}" class="tl-chip">{b} {esc(CHANGE_NAME[b])}'
        f' <span>{counts.get(b,0)}</span></a>'
        for i, (b, _, _) in enumerate(CHANGE_ORDER) if counts.get(b, 0))
    chips = f'<div class="tl-chips">{chips}</div>' if chips else ""

    # ── 里程碑时间线（按变更日期倒序）──
    body = []
    for i, (badge, name, desc) in enumerate(CHANGE_ORDER):
        n = counts.get(badge, 0)
        if not n:
            continue
        body.append(f'<h2 id="c-{i}" class="tl-anchor">{badge} {esc(name)}'
                    f'<span class="tl-n">{n} 条 · {esc(desc)}</span></h2>')
        body.append('<ul class="ms">')
        for x in items:
            if (x.get("change") or "—") != badge:
                continue
            meta = " · ".join(
                p for p in (x.get("company"), x.get("drug"), x.get("phase"),
                            x.get("indication")) if p)
            trial = x.get("trial_name")
            sd = str(x.get("status_date") or "")
            # 月份精度的日期显式标注，不让读者把它当成确切发生日
            date_txt = (sd + '<span class="ms-badge">月份精度</span>'
                        if re.fullmatch(r"\d{4}-\d{2}", sd) else sd)
            bits = [f'<div class="ms-date">{date_txt}'
                    f'<span class="ms-badge">{badge} {esc(name)}</span></div>']
            bits.append(f'<div class="ms-title">{esc(meta)}</div>')
            if trial:
                bits.append(f'<div class="ms-meta">试验：{esc(trial)}'
                            f'{nct_link(x.get("nct"))}</div>')
            elif x.get("nct"):
                bits.append(f'<div class="ms-meta">登记号：{nct_link(x.get("nct"))}</div>')
            if x.get("mechanism"):
                bits.append(f'<div class="ms-meta">机制：{esc(x.get("mechanism"))}</div>')
            bits.append(f'<p class="ms-detail">{esc(x.get("status_detail"))}</p>')
            if x.get("change_note"):
                bits.append(f'<div class="ms-note">变更说明：{esc(x.get("change_note"))}</div>')
            bits.append('<div class="ms-src">出处：<a href="'
                        f'{esc(x.get("source"))}" rel="nofollow noopener" '
                        f'target="_blank">官方来源</a></div>')
            body.append('<li class="ms-item">' + "".join(bits) + "</li>")
        body.append("</ul>")

    # ── 口径与溯源（放在最后，读者先看到里程碑本身）──
    prov = [
        '<h2 id="prov" class="tl-anchor">口径与溯源</h2>',
        '<table class="ms-tbl"><tbody>',
        f'<tr><th>数据源</th><td>{esc(src.get("file"))}（schema {esc(src.get("schema_version"))}，'
        f'基线日 {esc(src.get("baseline_date"))}）· 行业层 <code>{esc(src.get("layer"))}</code>'
        f' · file_id <code>{esc(src.get("file_id"))}</code></td></tr>',
        f'<tr><th>产出方</th><td>{esc(src.get("generated_by"))}'
        f' · 生成于 {esc(src.get("generated_at"))}</td></tr>',
        f'<tr><th>覆盖窗口</th><td>{esc(src.get("coverage_window"))}'
        f' · 上一期 {esc(src.get("previous_delivery"))}</td></tr>',
        f'<tr><th>变更标记</th><td>' +
        "；".join(f'{b} = {esc(dd)}' for b, _, dd in CHANGE_ORDER) + '</td></tr>',
        f'<tr><th>缺失项（如实）</th><td>{len(items) - with_nct} / {len(items)} 条未在基线中'
        f'登记 NCT 号（多为公司管线页口径或临床前资产），本页不补号、不猜号，'
        f'仅给出公司官方出处</td></tr>',
        '</tbody></table>',
        f'<p class="ms-note">{esc(src.get("note"))}</p>',
    ]
    body.extend(prov)

    hero_html = _gi.hero(
        "关键试验里程碑",
        f"衰老与长寿领域 {len(items)} 个在研资产的状态变更时间线，"
        f"来自行业情报班的《管线状态基线》，每条带变更日期、阶段、机制与官方出处。",
        stats=[(len(items), "在研资产"), (companies, "家公司"),
               (counts.get("⬆", 0), "推进 ⬆"), (counts.get("⬇", 0), "回撤 ⬇"),
               (f"{dates[0]}", "最早变更"), (f"{dates[-1]}", "最近变更")] if dates else None,
    )

    page = _gi.page(
        "关键试验里程碑 · LongBiosci",
        f"衰老与长寿在研管线 {len(items)} 个资产的关键里程碑：推进 / 回撤 / 更新，"
        f"按变更日期倒序，每条带出处。",
        "/trials/milestones/",
        "",
        hero_html,
        STYLE + chips + "\n".join(body))

    out_dir = os.path.join(root, "trials", "milestones")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)

    # ── 向 /trials.html 注入入口（幂等）──
    ipath = os.path.join(root, "trials.html")
    if os.path.exists(ipath):
        s = open(ipath, encoding="utf-8").read()
        link = (f'<p class="lb-milestones-entry" style="margin-top:.6rem">'
                f'<a href="/trials/milestones/">→ 查看关键试验里程碑'
                f'（{len(items)} 个资产 · {counts.get("⬆",0)} 推进 / '
                f'{counts.get("⬇",0)} 回撤 · 按变更日期倒序）</a></p>')
        if "lb-milestones-entry" in s:
            s = re.sub(r'<p class="lb-milestones-entry".*?</p>', link, s,
                       count=1, flags=re.S)
        else:
            s = re.sub(r'(<h1[^>]*>[^<]*</h1>)', r'\1\n' + link, s, count=1)
        open(ipath, "w", encoding="utf-8").write(s)

    print(f"[milestones] 资产 {len(items)} 条 · 公司 {companies} 家 · 带 NCT {with_nct} 条 · "
          f"变更分布 " + " ".join(f"{b}{counts.get(b,0)}" for b, _, _ in CHANGE_ORDER))
    print(f"[milestones] 日期跨度 {dates[0]} ~ {dates[-1]}")
    print("[milestones] 产出 trials/milestones/index.html；入口已注入 trials.html")
    return 0


if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    sys.exit(build(root))
