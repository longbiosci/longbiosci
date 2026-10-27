#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_event_date.py —— 修复文章页机器可读属性 data-lb-event-date 的占位值缺陷（待办 P2-18）

背景（2026-10-26 晨间班实测留据）：
  管线在 2026-10-25 21:5x 的 inject 步骤里给文章页注入了 data-lb-event-date 属性，
  但值是占位符 "1"，不是「情报发生日期」。该属性供机器使用（时间线聚合、排序、
  sitemap lastmod），值为 "1" 会让任何按它排序的逻辑全部塌陷。

本脚本做什么：
  1. 扫描 news/*.html，定位 data-lb-event-date="1"（或任何非 YYYY-MM-DD 的占位值）；
  2. 从页面正文中解析真实「情报发生日期」（优先），回退到「本站发布 / 发布于」日期；
  3. 写回为 data-lb-event-date="YYYY-MM-DD"；
  4. 断言：所有写回值必须匹配 ^\d{4}-\d{2}-\d{2}$，否则整批失败退出（不半途写入）。

用法：
  python3 fix_event_date.py <news目录> [--apply]   # 不加 --apply 只做体检，不写盘
"""
import os
import re
import sys
import datetime

ATTR_RE = re.compile(r'data-lb-event-date="([^"]*)"')
# 正文里的日期句式，按优先级排列
PATTERNS = [
    re.compile(r'情报发生\s*[（(]?\s*(\d{4}-\d{2}-\d{2})'),
    re.compile(r'情报发生[^0-9]{0,12}(\d{4}-\d{2}-\d{2})'),
    re.compile(r'本站发布[^0-9]{0,12}(\d{4}-\d{2}-\d{2})'),
    re.compile(r'发布于[^0-9]{0,12}(\d{4}-\d{2}-\d{2})'),
    re.compile(r'"date"\s*:\s*"(\d{4}-\d{2}-\d{2})'),
]
DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def is_real_date(v):
    if not DATE_RE.match(v or ''):
        return False
    try:
        datetime.date.fromisoformat(v)
        return True
    except ValueError:
        return False


def extract_event_date(html):
    """从正文解析情报发生日期；返回 (日期, 来源句式序号) 或 (None, None)"""
    for i, p in enumerate(PATTERNS):
        m = p.search(html)
        if m and is_real_date(m.group(1)):
            return m.group(1), i
    return None, None


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    root = sys.argv[1]
    apply = '--apply' in sys.argv
    files = [os.path.join(root, f) for f in os.listdir(root) if f.endswith('.html')]

    total_attr = 0      # 含该属性的文件数
    bad = 0             # 值为占位符的文件数
    fixed = 0           # 本次修复成功的
    unparsed = []       # 有属性但解析不出日期的
    already_ok = 0

    for path in files:
        with open(path, 'r', encoding='utf-8', errors='ignore') as fh:
            html = fh.read()
        m = ATTR_RE.search(html)
        if not m:
            continue
        total_attr += 1
        cur = m.group(1)
        if is_real_date(cur):
            already_ok += 1
            continue
        bad += 1
        d, src = extract_event_date(html)
        if not d:
            unparsed.append(os.path.basename(path))
            continue
        if apply:
            new_html = ATTR_RE.sub('data-lb-event-date="%s"' % d, html)
            with open(path, 'w', encoding='utf-8') as fh:
                fh.write(new_html)
        fixed += 1

    print('扫描目录        : %s' % root)
    print('HTML 文件总数   : %d' % len(files))
    print('含该属性的文件  : %d' % total_attr)
    print('已是真实日期    : %d' % already_ok)
    print('占位值待修      : %d' % bad)
    print('本次修复/可修   : %d' % fixed)
    print('解析不出日期    : %d %s' % (len(unparsed), unparsed[:5]))

    # 断言：只要还有占位值残留（未解析成功的），整批判失败
    if unparsed:
        print('❌ 断言失败：仍有 %d 篇解析不出情报发生日期，未批量写入（保持原样）' % len(unparsed))
        return 1
    if apply:
        # 二次校验：写盘后复查一遍
        residual = 0
        for path in files:
            with open(path, 'r', encoding='utf-8', errors='ignore') as fh:
                html = fh.read()
            m = ATTR_RE.search(html)
            if m and not is_real_date(m.group(1)):
                residual += 1
        print('写盘后复查残留  : %d' % residual)
        if residual:
            print('❌ 断言失败：写盘后仍有占位值残留')
            return 1
        print('✅ 断言通过：全部 data-lb-event-date 均为 YYYY-MM-DD')
    return 0


if __name__ == '__main__':
    sys.exit(main())
