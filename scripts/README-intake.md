# 内容通道（Content Intake）· 使用说明

## 三层状态：不再依赖 agent 记忆

原始问题是：整条链的唯一状态是「我记得上次捞到哪」。上下文一压缩就丢，
于是要么重复捞、要么漏捞——**这与「网站内容有遗漏」是同一个病根**。

现在状态分三层，各管一件 durable 的事：

| 层 | 文件 | 作用 |
|---|---|---|
| **事实源** | `data/intake-manifest.tsv` | 网盘四个目录的**全量**清单，每次重建。含 size 与 mtime |
| **游标** | `data/intake-cursor.json` | 每个产出文件的处理状态（pending/done/empty），**幂等**。机器可判定 |
| **触发** | automation `12409847` | 每 4 小时跑一次：读游标 → 扫目录 → 有新就消化 → 推游标 |

```bash
python3 scripts/cursor.py verify --repo .   # 清单与游标是否对齐（不一致 = 有新产出）
python3 scripts/cursor.py next   --repo .   # 待处理清单（含「why」：空文件 / 游标无记录）
python3 scripts/cursor.py stat   --repo .   # 各层消化进度 + 空文件告警
python3 scripts/cursor.py done   --repo . --file-id <id> --slugs a.html b.html --note "..."
python3 scripts/cursor.py empty  --repo . --file-id <id> --note "size=0，需重跑任务 <id>"
```

**游标让「处理过没有」变成机器可判定的事实**，而不是 agent 的印象。
即使一次运行中途挂掉，下次接手从游标继续即可。

## 这个通道解决什么问题

项目里有 **6 个自动化任务**在持续产出内容，产出全部落在网盘 IMA 知识库：

| 任务 | 频率 | 产出层 | 文件形态 |
|---|---|---|---|
| 重点期刊监控·每周五（`7762989`） | 每周五 | 文献层 | `深度文献卡片_YYYY-MM-DD.md`（SOP §4.2，50+ 张卡，**`\| N1 \|` 编号表格**） |
| 行业情报周报·每周三（`7762986`） | 每周三 | 行业层 | `行业情报周报_YYYY-MM-DD.md` + `.xlsx`（三表结构） |
| 临床×科学文献交叉追踪·周更（`7660605`） | 每周一 | 文献层 + 元层 | 喂料池条目 + `临床×文献交叉周报_*.md` |
| 衰老与长寿临床试验清单·月度刷新（`7660599`） | 每月1日 | 清单 | `临床试验清单.md` / `.json` |
| 月度研究热点综述·每月15日（`7762988`） | 每月15日 | **元层** | 综述 md。⚠️ 元层**无独立目录**，写在 `dQpzABLkRxLu`（网站层父目录） |
| 网站运营与优化（每日两次，`12179175`） | 每天 | 网站层 | 运营日志 / 待办清单 |

###⚠️ 产出格式不止一种，这是实测踩出来的坑

`harvest.py` 的表格解析器最初只认 `\| N1 \|` 编号表格，
结果**文献层「预印本速递」系列 11 期全部被静默丢弃**——那些是
`### 标题 + 字段表` 结构。现已补`parse_section_items()`。
**每接入一种新产出格式，都要验证一次抽取结果不为 0 条。**

目前已知的三种格式：

| 格式 | 示例产出 | 解析方式 |
|---|---|---|
| 编号表格 | 深度文献卡片 `\| N1 \| 期刊 \| 标题 \| ... \|` | `parse_md_tables()` |
| 编号表格（`#` 号 + 反引号 DOI） | 预印本速递 09-24 `\| 1 \| 标题 \| \`doi\` \|` | `parse_md_tables()` |
| `### 标题 + 字段表` | 预印本速递 09-13 | `parse_section_items()` |

**2026-10-15 之前的现状**：这些产出与网站之间**没有通道**。喂料池 631 条全部标记
`publish_status=待成稿` / `fed_to_daily=false`，即**一次都没被网站消化过**。
本通道就是为了补上这个断点。

## 全链路流程（七段）

```
网盘产出（6 个自动化任务）
   │ ① intake.sh 发现 ──── 空文件告警 + 时间窗筛选
   ▼
.intake/raw/
   │ ② harvest.py 四路查重 ── 每条结论带 confidence
   ▼
漏收清单
   │ ③ 人工复核（硬核验：直接搜站内关键词）★不可自动化
   ▼
待写清单
   │ ④ gen_articles*.py 写稿 ── 证据分级 A/B/C、SOP §4.2
   ▼
news/*.html + articles.json
   │ ⑤ backfill-doi.py 补DOI 索引   ← 必须在写稿后跑，否则新文查不到
   ▼
   │ ⑥ run-pipeline.sh（10 阶段，末位为死链+计数硬校验）
   ▼
线上
   │ ⑦ ledger.py audit 对账 ── 产出 vs 上站双向核对
   ▼
「已收录 N · 漏收 M」→ M 回到第③ 步
```

**为什么第③段刻意不自动化**：证据分级（A/B/C）与定量口径必须逐条按 SOP §4.2 处理，
付费墙未获取处标「待补全文」，定量一律不臆测。这件事交给脚本必然出错。

**为什么第⑤步是必经环节**：新写的文章如果不补 DOI 索引，下一轮 harvest 就查不到它，
会把自己刚写的文章重新报成「漏收」。2026-10-15 实测：补索引前 164 条假漏收，
补索引 + 修DOI 正则后降到 150 条，且新写 3 篇被正确识别为已收录。

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
站内：414 篇文章 / 420 个 DOI / 414 个标题可比对
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

`harvest.py` 用**四路**匹配，**每条结论带 confidence**：

| 路| 依据 | confidence | 可信度 |
|---|---|---|---|
| 1 | DOI 精确命中 `data/doi-index.json` | `high` | 可直接采信 |
| 2 | slug 机制词命中 | `medium` | **需抽查正文** |
| 3 | 标题 3-gram 相似 ≥ 0.34 | `low` | 谨慎 |
| 4 | **英文原标题 vs 站内英文 slug 词元重叠**（≥3 词且 ≥0.5） | `medium` | **可采信** |
| — | 四路均未命中 | `none` | **不等于漏收**，见盲区 |

**第 4 路是解决盲区 1 的关键设计。** 站内 `<title>` 是中文译名，但**站内 slug 是英文
kebab-case**（如 `Contractile-Myografts-Systemic-AntiAging-Nature-Aging-2026.html`），
与英文原标题天然可比，且**不需要维护中文对照表**。停用词表已剔除 `aging` /
`longevity` / `cell` / `human` / `html` 这类无区分度词。

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

**盲区 3：`articles.json` 原本不存 DOI（已修复）。**
早期查重直接读 `data/articles.json` 的 DOI 字段，得出「14 篇全是新文献」的错误结论——
因为该字段根本不存在。现在 `backfill-doi.py` 会从正文回填DOI 并生成
`data/doi-index.json`（DOI → slug 权威索引）。
**当前状态：414 篇中 277 篇（67%）有 DOI，仍有 137 篇（33%）无 DOI**——
这些多为交叉追踪与行业周报产出（本就无 DOI），只能靠机制词与人工核对。

###两个已修复但值得记住的坑

**坑1：DOI 正则太贪婪。** 原来用 `10\.\d{4,9}/[^\s"'<>&]+`，会把
`10.1016/j.ymthe.2026.05.025）·研究：MIT` 整段当成 DOI 写进索引——
**站内自己建的索引就是脏的，DOI 精确匹配对站内自己都失效**。现在改为
Crossref 合法字符集 `[-._;()/:a-z0-9<>\[\]+]+`。

**坑 2：Markdown 链接污染。** 产出里DOI 常写成
`[10.1038/xxx](https://doi.org/10.1038/xxx)`，正则会把后半段 URL 一起吞进来。
现在先剥 `](...)` 再匹配。这个bug 单独造成约 10 条假漏收。

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
| `scripts/intake.sh` | ① 发现：网盘产出 → 本地暂存 → 调 harvest（含空文件告警）|
| `scripts/harvest.py` | ② 判定：四路查重，输出带 confidence 的报告 |
| `scripts/ledger.py` | ⑦ 对账：产出 vs 上站双向台账（漏收 + 孤站） |
| `scripts/backfill-doi.py` | ⑤补 DOI 索引（写稿后必跑，幂等） |
| `scripts/gen_articles.py` | ④ 写稿模板（文献类，含证据分级 notice） |
| `scripts/gen_industry_2026-10-15.py` | ④ 写稿范例（产业/监管类） |
| `scripts/gen_missing_2026-09-25.py` | ④ 写稿范例（台账核定漏收的处置记录） |
| `scripts/fetch.py` | 从 JSON 读 download_url 原样下载（防手抄 URL 出错） |
| `scripts/check-links.py` | ⑥末位：死链 + 计数一致性硬校验（不通过则管线失败） |
| `scripts/refresh_counts.py` | ⑥倒数第二：各处「N 篇」计数回写事实源（幂等自愈） |
| `scripts/run-pipeline.sh` | ⑥ 上线：10 阶段管线 |

## 每日自检清单（跑一遍才算完成一轮）

```bash
python3 scripts/backfill-doi.py .        # 索引与文章库一致
python3 scripts/ledger.py audit .        # 读 data/ledger-outputs.json 对账，漏收数与上轮对比
bash scripts/run-pipeline.sh             # 10/10，末位必须打印「检查通过」
python3 -c "import json;print(len(json.load(open('data/articles.json'))))"  # 与首页/sitemap/search-index 一致
```

`ledger.py audit` 的「漏收数」应**逐期收敛**。若突然从 20 涨到 150，
几乎一定是 DOI 索引失效或正则被污染——先查这两个，不要先怀疑产出。

## 排障

| 现象 | 原因 | 处理 |
|---|---|---|
| 新写的文章被重新报成「漏收」 | 没跑 `backfill-doi.py`，DOI 索引缺新条目 | 写稿后、管线前跑一次 `backfill-doi.py .` |
| 站内某文的 DOI 在索引里带中文尾巴 | 旧版贪婪正则写的脏索引 | 重跑 `backfill-doi.py .`（幂等，只增字段） |
| 产出条目 DOI 带 `](https://doi.org/...)` | Markdown 链接未剥离 | 已修`normalize_doi()`；若仍有请贴样本 |
| `ledger.py audit` 漏收数远大于预期 | 中文摘要条目 + 一篇研究对应多条卡片 | 逐条硬核验，别直接写稿 |
| `intake.sh` 报「未提供 NETDRIVE_MANIFEST」 | 未生成网盘清单 | 先用 `tdrive.dir_list` 生成 TSV |
| `intake.sh` 报「跳过空文件 size=0」 | 上传失败（如文献层 2026-10-09 深度卡片） | 重跑该产出任务并回读校验 SHA256 |
| `候选条目：0 条` | 文件格式不含表格 / 表头识别失败 | 检查 `parse_md_tables` 的 `TITLE_HINTS` |
| 管线第9 步报「死链」 | 手写正文里的 `/news/xxx.html` 拼错 | 按脚本打印的路径核对；`slug` 用 `ls news/` 复制，别手敲 |
| 管线第 9 步报「计数不一致」 | articles.json 与磁盘文件不同步 | 跑 `backfill-doi.py` 后重跑管线；若是新文章，确认已写入 articles.json |
| `audit` 报「产出条目 0」 | `data/ledger-outputs.json` 缺失 | 跑 `ledger.py build <repo> <产出文件...>` 重建持久化清单 |
| 漏收数量远超预期 | 机制词表失效（编号前缀不匹配） | 补 `FALLBACK_TERMS` |
| 漏收数量明显偏少 | 机制词过于通用 | 检查 `confidence=medium` 的条目，剔除通用词 |