#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""解析《文献监控_2026-10-29_卡片》→ /tmp/cards_1029.json

三节结构：
  一、全文级解读卡片 199 篇（编号 001–199，含「全文来源」字段）
  二、升级卡片 11 篇（编号「升级卡片 01」–「升级卡片 11」，含「来源」字段）
  三、摘要级卡片 75 篇（编号 200–274，含「核验级别：未核验全文」字段）
字段 heading 上有的缩进续行（- **方法**：…\n  1）…），必须一并归入该字段。
"""
import json
import re
import sys

SRC = sys.argv[1] if len(sys.argv) > 1 else (
    "/workspace/longbiosci/.intake/raw/1029/dGBunAeRiRlm__文献监控_2026-10-29_卡片")

FIELD_MAP = {
    "标题": "title", "期刊": "journal", "全文来源": "ftsrc", "来源": "ftsrc",
    "核验级别": "verify", "研究问题": "question",
    "方法（摘自摘要）": "method", "方法": "method",
    "核心结论（摘自摘要）": "conclusion", "核心结论": "conclusion",
    "局限": "limit", "对项目价值": "value",
}
FIELD_RE = re.compile(r'^-\s+\*\*(.+?)\*\*[：:]\s*(.*)$')

cards, cur, field, sec = [], None, None, None
sec_re = re.compile(r'^##\s+([一二三])、(.+?)$')
head_re = re.compile(r'^###\s+(?:卡片\s+(\d{3})|升级卡片\s+(\d{2}))\s*[｜|]\s*(.*)$')
head2_re = re.compile(r'^###\s+升级卡片\s+(\d{2})（(.*?)）$')

with open(SRC, encoding="utf-8") as f:
    for line in f:
        line = line.rstrip("\n")
        m = sec_re.match(line)
        if m:
            sec = m.group(1)
            if cur:
                cards.append(cur)
                cur = None
            continue
        h2 = head2_re.match(line)
        h = h2 or head_re.match(line)
        if h:
            if cur:
                cards.append(cur)
            if h2:
                num = "U" + h2.group(1)
                tail = h2.group(2) or ""
            else:
                num = h.group(1)
                tail = h.group(3) or ""
            topics = re.split(r'（交叉：', tail)[0].strip()
            cross = ""
            cm = re.search(r'（交叉：(.*?)）\s*$', tail)
            if cm:
                cross = cm.group(1)
            cur = {"num": num, "sec": sec, "topic": topics, "cross": cross,
                   "title": "", "journal": "", "ftsrc": "", "verify": "",
                   "question": "", "method": "", "conclusion": "",
                   "limit": "", "value": ""}
            field = None
            continue
        if cur is None:
            continue
        fm = FIELD_RE.match(line)
        if fm:
            key = FIELD_MAP.get(fm.group(1).strip())
            if key:
                field = key
                cur[key] = fm.group(2).strip()
            else:
                field = None
        elif line.strip() and (line.startswith("  ") or line.startswith("\t")):
            if field and cur[field]:
                cur[field] += "\n" + line.strip()
            elif field:
                cur[field] = line.strip()
        elif not line.strip():
            field = None

if cur:
    cards.append(cur)


def grab(pat, s, group=1, default=""):
    m = re.search(pat, s or "")
    return (m.group(group).strip() if m else default)


for c in cards:
    j = c["journal"]
    c["pmid"] = grab(r'PMID\s*(\d+)', j)
    c["doi"] = grab(r'DOI\s*(\S+?)(?:（|｜|\||$)', j).rstrip('.,')
    c["doi"] = c["doi"].replace("`", "")
    jn = re.split(r'[｜|]', j)[0]
    c["journal"] = jn.replace("**", "").strip()
    c["pmc"] = grab(r'PMC(\d+)', j)
    c["abstract_only"] = "未核验全文" in (c["verify"] or "")
    c["upgraded"] = c["num"].startswith("U")
    c["stars"] = grab(r'(★+☆*)', c["value"])

json.dump(cards, open("/tmp/cards_1029.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

print(f"解析 {len(cards)} 张卡片")
sec_cnt = {}
for c in cards:
    sec_cnt[c["sec"]] = sec_cnt.get(c["sec"], 0) + 1
print("分节：", {k: v for k, v in sorted(sec_cnt.items())})
print("摘要级（未核验全文）：", sum(1 for c in cards if c["abstract_only"]))
print("升级卡：", sum(1 for c in cards if c["upgraded"]))
print("有 DOI：", sum(1 for c in cards if c["doi"]),
      " 有 PMID：", sum(1 for c in cards if c["pmid"]))
missing = [c["num"] for c in cards if not c["title"] or not c["doi"]]
print("缺标题/DOI：", missing[:20], "共", len(missing))
# 内部 DOI 重复
seen, dup = {}, []
for c in cards:
    if c["doi"] and c["doi"] in seen:
        dup.append((c["num"], seen[c["doi"]], c["doi"]))
    seen.setdefault(c["doi"], c["num"])
print("内部 DOI 重复：", dup)
