# 内容通道（Content Intake）· 使用说明

## 这个通道解决什么问题

项目里有 **6 个自动化任务**在持续产出内容，产出全部落在网盘 IMA 知识库：

| 任务 | 频率 | 产出层 | 文件形态 |
|---|---|---|---|
| 重点期刊监控·每周五 | 每周五 | 文献层 | `深度文献卡片_YYYY-MM-DD.md`（SOP §4.2，50+ 张卡） |
| 行业情报周报·每周三 | 每周三 | 行业层 | `行业情报周报_YYYY-MM-DD.md` + `.xlsx`（三表结构） |
| 临床×科学文献交叉追踪·周更 | 每周一 | 文献层 | 喂料池条目（交叉判定 A/B/C） |
| 衰老与长寿临床试验清单·月度刷新 | 每月1日 | 清单 | `临床试验清单.md` / `.json` |
| 月度研究热点综述·每月15日 | 每月15日 | 元层 | 综述 md |
| 网站运营与优化（每日两次） | 每天 | — | 运营日志 / 待办清单 |

**2026-10-15 之前的现状**：这些产出与网站之间**没有通道**。喂料池 631 条全部标记
`publish_status=待成稿` / `fed_to_daily=false`，即**一次都没被网站消化过**。
本通道就是为了补上这个断点。

## 三段式流程

```
网盘产出 ──① intake.sh 发现──► .intake/raw/ ──② harvest.py 查重──► 漏收清单
                                                                    │
                                        ③ 人工复核 + 写稿（不可自动化）│
                                                                    ▼
                                    gen_articles.py ──► run-pipeline.sh ──► 线上
```

**为什么第③段刻意不自动化**：证据分级（A/B/C）与定量口径必须逐条按 SOP §4.2 处理，
付费墙未获取处标「待补全文」，定量一律不臆测。这件事交给脚本必然出错。

## 用法

### 第①步：列举网盘产出

用网盘工具（`tdrive.dir_list`）遍历这三个目录，生成 TSV 清单：

| 层 | dir_id |
|---|---|
| 文献层 | `dsuxMCSCwEVB` |
| 行业层 | `dVEYJcsAbUdK` |
| 网站层 | `drGisxAlABJK` |

TSV 格式（tab 分隔）：
```
file_id	layer	name	ext	size	modify_time	modify_date
dkwSBCCuiNrB	文献层	深度文献卡片_2026-10-02	md	215865	1791551600000	2026-10-02
```

### 第②步：跑 intake

```bash
# 只处理最近 14 天的产出
NETDRIVE_MANIFEST=/tmp/nd.tsv ./scripts/intake.sh /path/to/repo --since '14 days ago'

# 输出
仓库根目录: /path/to/repo
筛选时间窗: 自 14 天前
→ 选中 3 个新增/更新产出文件
站内：414 篇文章 / 319 个 DOI / 414 个标题可比对
候选条目：75 条（来自 2 个产出文件）
判定结果：{'漏收': 46, '已收录': 15, '需人工核对': 30}
置信度分布：{'none': 54, 'high': 11, 'medium': 1}
```

产出文件落在 `<repo>/.intake/harvest-report.json`。

### 第③步：人工复核 + 写稿

```bash
# 看漏收清单
python3 -c "
import json; r=json.load(open('.intake/harvest-report.json'))
for i in r['items']:
    if i['status']=='漏收': print(i['title'][:70], '|', i['basis'][:60])
"
```

确认后写入 `scripts/gen_articles_<批次>.py`（参考 `gen_articles.py` 与
`gen_industry_2026-10-15.py` 两个现成范例），再执行：

```bash
python3 scripts/gen_articles.py . <待写清单.json> 2026-10-15
bash scripts/run-pipeline.sh
```

## 判定口径（务必理解，否则会误信结论）

`harvest.py` 用三路匹配，**每条结论都带 confidence**：

| confidence | 依据 | 可信度 |
|---|---|---|
| `high` | DOI 精确命中站内全文 | 可直接采信 |
| `medium` | slug 机制词命中 | **需抽查正文** |
| `low` | 标题 3-gram 相似 ≥ 0.34 | 谨慎 |
| `none` | 三路均未命中 | **不等于漏收**，见盲区 |

### 三个已知盲区（都是实测踩出来的）

**盲区 1：标题相似度对英文文献天然失效。**
站内文章标题是**中文译名**，产出给的往往是**英文原标题**。实测站内414 篇中文标题
vs 英文原标题，相似度普遍 `0.00`——这一路对英文文献条目**没有判别力**。
所以 `confidence=none` 的条目**不能直接当漏收写稿**，必须人工核对。

**盲区 2：通用机制词制造「假已收录」。**
词表里如果放`aging` / `senolytic` / `cGAS` / `autophagy` 这类通用词，会命中站内
任意一篇同领域文章。实测一度把 **27 条真漏收误判成「已收录」**。
因此机制词表收录标准是**必须高特异**：`pseudocatenulatum`、`5-AVAB`、`RLS-1496`、
`PrecivityAD` 这种能唯一定位的词；`LINE1`、`CD38` 这种边界词要慎用。

**盲区 3：`articles.json` 不存 DOI。**
早期查重直接读 `data/articles.json` 的 DOI 字段，得出「14 篇全是新文献」的错误结论——
因为该字段根本不存在。正确做法是**扫 `news/*.html` 全文**提取 DOI。

### 硬校验的教训

给查重加「关键词出现在库内文本中就判已收录」这条**看似合理**的规则，结果
`SIRT1` / `猕猴` / `p21` / `体细胞突变` 这类短词命中了完全不同的文章
（例如「DREAM 复合体」含「体细胞突变」，但与「热量限制降低突变负荷」是两篇）。

**结论：`confidence=medium` 的「已收录」必须抽查正文**，不能只看命中就放过。

## 扩展机制词表

发现新的高特异词时，编辑 `scripts/harvest.py` 的两个位置：

```python
DEFAULT_MECH = {              # 按条目编号（优先路径）
    "C01": ["pseudocatenulatum", "5-AVAB", "MicroAge"],
    ...
}

FALLBACK_TERMS = [            # 编号对不上时的全局兜底
    "pseudocatenulatum", "RLS-1496", "ER-100", "PrecivityAD", ...
]
```

收录标准：能在 slug 里唯一定位这篇研究。做不到就别放。

也可以外置 JSON 覆盖（不改代码）：

```bash
python3 scripts/harvest.py <repo> <files...> --mech /path/to/mech.json
```

## 相关文件

| 文件 | 作用 |
|---|---|
| `scripts/intake.sh` | ① 发现：网盘产出 → 本地暂存 → 调 harvest |
| `scripts/harvest.py` | ② 判定：三路查重，输出带 confidence 的报告 |
| `scripts/gen_articles.py` | ③ 写稿模板（文献类，含证据分级 notice） |
| `scripts/gen_industry_2026-10-15.py` | ③ 写稿范例（产业/监管类） |
| `scripts/run-pipeline.sh` | ④ 上线：8 阶段管线 |

## 排障

| 现象 | 原因 | 处理 |
|---|---|---|
| `intake.sh` 报「未提供 NETDRIVE_MANIFEST」 | 未生成网盘清单 | 先用 `tdrive.dir_list` 生成 TSV |
| `intake.sh` 报「跳过空文件 size=0」 | 上传失败（如文献层 2026-10-09 深度卡片） | 重跑该产出任务并回读校验 SHA256 |
| `候选条目：0 条` | 文件格式不含表格 / 表头识别失败 | 检查 `parse_md_tables` 的 `TITLE_HINTS` |
| 漏收数量远超预期 | 机制词表失效（编号前缀不匹配） | 补 `FALLBACK_TERMS` |
| 漏收数量明显偏少 | 机制词过于通用 | 检查 `confidence=medium` 的条目，剔除通用词 |