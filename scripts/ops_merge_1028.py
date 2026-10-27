#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ops_merge_1028.py —— 第 16 轮运营文档合并 + 留痕

背景（连着两轮的挂账）
──────────────────────
网站层与元层各有一份《运营日志》《运营待办清单》，长期双份漂移。
SOP 写「元层是 10-15 旧版、以网站层为准」，但**连续两轮实测元层更新**：
本轮元层运营日志 mtime 2026-10-27 21:26（含 13:30 / 21:00 两节），
网站层仍停在 10-22 15:13；本地 docs/ 只有 10-27 14:30 那一节。

本轮不再各写各的：**以元层新版为底，把本地独有的一节插回原位，
再追加第 16 轮留痕**，产出唯一一份，回传两层，消除分叉。
差异精确到节，不做全文覆盖（否则必然丢内容）。
"""
import os
import re

ROOT = "/workspace/longbiosci"
RAW = os.path.join(ROOT, ".intake", "raw", "1028")
SRC_LOG = os.path.join(RAW, "dcRhMjctGcjp__运营日志")
SRC_TODO = os.path.join(RAW, "duLHFqzcdVBY__运营待办清单")
DST_LOG = os.path.join(ROOT, "docs", "运营日志.md")
DST_TODO = os.path.join(ROOT, "docs", "运营待办清单.md")


def sections(text):
    """按 '## ' 切块，返回 [(标题行, 块正文), ...]；文件头单独返回"""
    lines = text.split("\n")
    idx = [i for i, l in enumerate(lines) if l.startswith("## ")]
    head = "\n".join(lines[:idx[0]]) if idx else text
    blocks = []
    for n, i in enumerate(idx):
        j = idx[n + 1] if n + 1 < len(idx) else len(lines)
        blocks.append((lines[i], "\n".join(lines[i + 1:j]).rstrip()))
    return head, blocks


def merge(base_path, local_path, insert_after=None):
    """以 base（元层新版）为底，把 local 独有的 ## 节插回原位。"""
    b_head, b_blocks = sections(open(base_path, encoding="utf-8").read())
    _, l_blocks = sections(open(local_path, encoding="utf-8").read())
    b_titles = {t for t, _ in b_blocks}
    out = list(b_blocks)
    inserted = []
    for t, body in l_blocks:
        if t in b_titles:
            continue
        pos = len(out)
        if insert_after:
            for n, (bt, _) in enumerate(out):
                if insert_after in bt:
                    pos = n + 1
        out.insert(pos, (t, body))
        inserted.append(t)
    return b_head, out, inserted


LOG_ADD = """

## 2026-10-28 05:30 · 内容摄入巡检（任务 12409847）· 第 16 轮

> 数据日期 2026-10-28 · 生成时间 2026-10-28 05:30（本班沙箱时钟实测）。
> 本轮交付：**40 条增量全量消化，站内文章 790 → 830（+40），播客 26 → 35 期**，
> 推送与线上核验在本班闭环（制度变更后的第一次）。

### 一、本轮接了什么（清单 183 个产出 · 增量 40 个）

| 层 | 产出 | 实测字节 | 处置 |
|---|---|---|---|
| 文献层 | 预印本速递_2026-10-28 | 149,427 | 26 条 DOI 已由解读批次全覆盖，母文件不重复成篇 |
| 文献层 | 预印本速递_总表_2026-10-28增量 | 30,105 | xlsx 汇总表，同上 |
| 行业层 | 行业情报周报_2026-10-28（md 版） | **55,044** | **批次 b 成篇 15 篇** |
| 行业层 | 行业情报周报_2026-10-28（xlsx 版） | 50,911 | 同名另一份，表格版，不重复成篇 |
| 行业层 | 管线状态基线 v1.0 | 19,435 | 行业结构回撤已成一文，快照不单独上站 |
| 元层 | 预印本全文级解读_2026-10-28（26 篇 + _items） | 5,800~14,921 | **批次 a 成篇 25 篇** |
| 元层 | 播客 ep027–ep035 增量包 | 23,603,200 | **9 期接入（26 → 35）** |
| 元层 | 3 个历史交付包 + 凭证 + 日志副本 + 运行总结 ×2 | — | 已上线 / 非产出 / 重复件，不重复处理 |

### 二、判空（硬规则：实际下载核验，不信 dir_list 的 size）

43 个文件**逐个实际下载**核验字节数：**实测为空 0 个**，无需告警重跑。
其中 **6 条缓存 size 与实测不符**，最大的两条是运营文档：

| 文件 | 缓存 size | 实测 |
|---|---|---|
| 运营待办清单（元层） | 142,584 | **185,024** |
| 运营日志（元层） | 312,581 | **229,228** |
| 预印本全文级解读_运行总结_2026-10-28 | 14,681 | 18,005 |
| 行业情报周报_2026-10-28（md 版） | 53,827 | 55,044 |

dir_list 的 size 又一次说谎（第 4 次实测证据）。**判空只认下载后的字节数。**

### 三、消化（40 条增量全量消化 · 无截断、无抽样）

| 批次 | 来源 | 条目 | 上站 | 规则④跳过 |
|---|---|---|---|---|
| a | 预印本全文级解读_2026-10-28 | 26 | **25 篇** | **1** |
| b | 行业情报周报 2026-W44 | 15 | **15 篇** | 0（§6 待核实区 3 条本就不成篇） |
| 播客 | ep027–ep035 增量包 | 9 | **9 期** | 0 |
| — | 其余（交付包/凭证/副本/重复件） | — | 0 | — |

- 站内文章 **790 → 830（+40）**；DOI 索引 **649 → 674**；播客 **26 → 35 期**
- 批次 a 跳过的 1 条：`10.64898/2026.10.11.758291`「小鼠肠道与肝脏再生过程中的转录组年轻化」
  已于 10-26 批以 `Regeneration-Transient-Transcriptomic-Rejuvenation-Gut-Liver-2026.html` 上站
- 批次 b 的 15 篇覆盖：Ferring×Gameto / XPRIZE Healthspan / Longeveron ELPIS II **（主要终点未达，负面必记）**
  / Arrowhead ARO-MAPT / Calico EMA PRIME / Insilico ISM6331 / NRG5051 / Immorta SenoMune-0257 /
  Carnyx CNYX-005 / Rubedo RLS-1496 / Life Biosciences ER-100 / NewLimit 临床班底 /
  **Unity 停运 + Turn Bio 资产流失（行业回撤）** / Biograph×Caristo / Beacon×Snap

### 四、本轮抓到的四个坑（挂账，不掩盖）

1. **查重只比 slug 会漏判重复——本轮真踩到并回滚了一次。**
   `10.64898/2026.10.11.758291` 早在 10-26 批以**另一个 slug** 上站，而本批按 DOI 派生的
   slug 与之不同，只查 slug 存在性 → **建出了重复页**（articles.json 一度 816）。
   已删除该页并把判重改为 **DOI 全文命中 `news/*.html`**（`already_on_site()`，
   写进 `gen_articles_intake_2026-10-28a.py`）。**slug 只是兜底，DOI 才是判据。**
2. **同日同名两份行业周报，载体不同**：一份真 md（55,044 B）、一份 xlsx（50,911 B），
   两者都**没有扩展名**。判空三道闸的第三闸（交付载体正确）连续第 2 轮抓到人。
3. **运行总结重复交付**：子目录内与元层根目录各一份，**md5 完全相同**（`8fb6b22b…`），
   按规则④只处理一份。
4. **元层运营文档比网站层新——SOP 描述已过期（连续第 2 轮确认）**：
   本轮把两层的运营日志 / 待办清单**合并为唯一一份**并回传两层，消除分叉（见本节末尾）。

### 五、收尾自检（五项全绿）

| 检查 | 结果 |
|---|---|
| `cursor.py verify` | 清单 183 / 游标 187，「清单有、游标无」**0**；游标落库 43 条（带 hash + slugs + note） |
| `backfill-doi.py` | `doi-index.json` **674 条**（649 → 674，本轮 25 篇预印本全部入索引） |
| `ledger.py audit` | 产出条目 426 · 已收录 195 · 漏收 231 · 孤站 868（与上一轮持平：台账基数未变） |
| `run-pipeline.sh` | **20/20 全绿**，死链 0，自检 11/11 探针按预期触发，计数全一致（830/830/830） |
| 推送 | Git Data API 快通道，187 项，tree sha 与本地 HEAD 一致，**新提交 `6259da7f94`，force=false** |

### 六、上线核验（独立于管线，全部实测）

| 核验项 | 结果 |
|---|---|
| 线上 `data/articles.json` | HTTP 200 · **830 条** |
| 线上 `podcast.xml` | HTTP 200 · **35 items** · lastBuildDate `Wed, 28 Oct 2026 03:39:00 +0800` |
| `/podcast/` | HTTP 200 · 含 ep027 与 ep035 · 70 个 mp3 链接（35 期） |
| 首页计数 | **全站 830 篇** |
| 抽查 `Preprint-10-64898-…-761546-2026.html` | HTTP 200 · `data-lb-event-date="2026-10-25"`（真日期） |
| 抽查 `Ferring-Acquires-Gameto-…-2026.html` | HTTP 200 |
| 抽查 `Longeveron-ELPIS-II-…-2026.html` | HTTP 200 |

**这是制度变更后的第一次闭环**：05:30 班自己检出 → 消化 → 推送 → 线上核验，
**未产出任何「待推送包」**，连续 5 轮的「待推送」就此收口。

### 七、本轮不做 / 未做

- **未覆盖包内 `index.html` / `sitemap.xml`**：播客增量包是按旧基线（0fb834a）打的，
  采用它会把本轮 40 篇新文挤出首页与 sitemap。只取音频、文稿、`podcast.json`，
  页面与 RSS 交给管线环节 8 重建。
- **未把周报 §6「待核实区」3 条成篇**（瑞初医药 A 轮 / Attilio / Estrella）：
  上游自己判定无一手官方出处，本班不升格。
- **未修改任何排班**，未代产任何采集岗的空产。
- **未改动 `data/flash.json`**（快讯为空列表，属合法状态）。

**本班留痕**：本次耗时约 **62 分钟**（起 05:29 → 止 06:31，沙箱时钟实测，
含网盘 43 个文件下载核验、两批写稿、管线 20 环节、推送与线上核验）。
"""

TODO_ADD = """

## 2026-10-28 05:30 · 内容摄入巡检（任务 12409847 第 16 轮）留痕

### ✅ 已完成

- [x] 重建全量清单：**183 个产出**（去重 62 条跨层镜像），游标 147 → 187
- [x] 判空：43 个文件**实际下载核验**，实测为空 **0 个**；6 条缓存 size 被实测值覆盖
- [x] 批次 a：预印本解读 26 条 → **25 篇上站** + 1 条规则④跳过
- [x] 批次 b：行业周报 W44 → **15 篇上站**（含 1 篇负面结果与 1 篇行业回撤）
- [x] 播客 ep027–ep035 → **9 期接入**（26 → 35），音频 9 个 + 文稿 9 份落地
- [x] 收尾：backfill-doi（674 条）· ledger audit · 管线 20/20 全绿
- [x] 推送上线：提交 `6259da7f94`（187 项，force=false）+ 线上核验 7 项全绿
- [x] 运营日志 / 待办清单**两层合并为唯一一份**并回传（消除双份漂移）

### ⬜ 新增挂账

1. **🆕 P2-30 · 查重必须走 DOI 全文命中，不能只比 slug**（本轮真踩到的坑）
   - 事实：`10.64898/2026.10.11.758291` 已于 10-26 批以另一 slug 上站，本批
     按 DOI 派生的 slug 不同 → **建出重复页**，articles.json 一度到 816 才发现。
   - 已在 `gen_articles_intake_2026-10-28a.py` 实现 `already_on_site()`（DOI → grep
     `news/*.html` 全文），**但该实现只在本批脚本里**，其余 `gen_articles_*.py`
     仍是「只查 slug」老逻辑。
   - 建议：把 `already_on_site()` 提到公共位置（如 `scripts/harvest.py` 或新建
     `scripts/dedupe.py`），**所有批次脚本统一调用**，否则下一批照样踩。
2. **🆕 P2-31 · 元层 / 网站层运营文档双份漂移（SOP 描述已过期）**
   - 事实：SOP 写「元层是 10-15 旧版、以网站层为准」，但连续两轮实测**元层更新**
     （本轮元层 mtime 10-27 21:26，网站层仍 10-22 15:13，本地 docs/ 只有 14:30 那一节）。
   - 本轮处置：以元层为底 + 本地独有节插回原位 + 本轮留痕，合并为唯一一份回传两层。
   - 建议：**修订 SOP**，明确「运营日志 / 待办清单的唯一权威是仓库 `docs/`，
     网盘两层均为只读镜像，由推送班次单向回写」，避免第三次各写各的。
3. **🆕 P2-32 · 同名无扩展名交付的载体识别**
   - 本轮行业层两份《行业情报周报_2026-10-28》都**没有扩展名**，实测一份 md 一份 xlsx。
   - 判空三道闸的第三闸（载体正确）连续第 2 轮抓到人，但**目前靠人眼看二进制头**。
   - 建议：把 `file`/魔数识别写进 `build_manifest.py` 的输出（增加一列 `kind`），
     让「扩展名与内容不符」在清单层就可见。
4. **沿用 P2（未收敛）**：`cursor.py` 无 `skipped` 态（第 2 轮挂账）；
   `verify` 的 4 条「游标有、清单无」历史遗留（`dbsioFAWDjqi` / `dntPxtImVdXC` /
   `dcohzvNdxzhl` / `dAyJLyFnKcvo`）**每轮照报**，台账需要「已判定」豁免态。

### 本轮留给下轮的提醒

- **台账数字本轮未变（195 / 231）不是没干活**：`ledger-outputs.json` 是持久化清单，
  不重建就不会变。本轮未跑 `ledger.py build`，故「漏收 231」仍是上一轮的存量噪音
  （大批中文摘要型条目，四路匹配天生无判别力）。**可比口径是「新增英文文献条目是否漏收」，
  本轮为 0**——25 篇全部进入 `articles.json` 且 DOI 入索引，无一条被重新报成漏收。
  若下轮想让台账反映本轮，需显式跑 `ledger.py build <repo> <本轮产出文件...>`。
- **播客包这类「整包交付」越来越多**：本轮靠「只取音频/文稿/JSON、页面交给管线」
  躲过一次覆盖事故（包内 index.html 是旧基线）。下轮遇到同类包，**先解包看清单再决定取哪几项**，
  不要 `tar -xf` 直接铺进仓库。
"""


def main():
    # ── 运营日志：元层为底 + 本地独有节插回 13:30 之后 ──
    head, blocks, ins = merge(SRC_LOG, DST_LOG, insert_after="2026-10-27 13:30")
    print(f"运营日志：以元层新版为底，插回本地独有 {len(ins)} 节：")
    for t in ins:
        print(f"   + {t}")
    body = "\n".join("\n".join((t, b)) for t, b in blocks).rstrip() + "\n" + LOG_ADD
    open(DST_LOG, "w", encoding="utf-8").write(head.rstrip() + "\n\n" + body.lstrip("\n"))
    print(f"→ {DST_LOG}  {os.path.getsize(DST_LOG)} B")

    # ── 待办清单：元层为底（## 节一致，元层内容更新）──
    h2, blocks2, ins2 = merge(SRC_TODO, DST_TODO)
    print(f"待办清单：以元层新版为底，插回本地独有 {len(ins2)} 节")
    body2 = "\n".join("\n".join((t, b)) for t, b in blocks2).rstrip() + "\n" + TODO_ADD
    open(DST_TODO, "w", encoding="utf-8").write(h2.rstrip() + "\n\n" + body2.lstrip("\n"))
    print(f"→ {DST_TODO}  {os.path.getsize(DST_TODO)} B")


if __name__ == "__main__":
    main()
