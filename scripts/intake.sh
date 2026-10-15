#!/usr/bin/env bash
# =============================================================================
# intake.sh —— LongBiosci 内容通道前半段（发现 + 判定）
#
# 用途：把网盘 IMA 知识库里的各任务产出自动接入网站内容生产，替代
#       「每天人工翻网盘找有没有新东西」。
#
# 用法：
#   ./intake.sh [仓库根目录] [--since YYYY-MM-DD]
#
# 流程：
#   1 列举网盘知识库目录下的产出文件（文献层 / 行业层 / 网站层 + 元层父目录）
#   2 按 mtime 过滤出 --since 之后新增或更新的文件（默认：只取最近 14 天）
#   3 调用 harvest.py 做三路查重，产出 data/harvest-report.json
#   4 打印漏收清单，供下一步写稿（gen_articles.py）
#
# 边界说明：本脚本**不做写作**，只负责「有什么新产出、哪些还没上站」。
#         写作环节刻意保持人工/AI 判断，因为证据分级与定量口径
#         必须逐条按SOP §4.2 处理，不能自动化。
#
# ⚠️ 网盘 download_url 签名窗口仅约 1 小时，过期即 403 / InvalidAccessKeyId。
#    手抄 URL 到 shell 里极易出错（本项目已踩两次）。
#    标准做法：把 file_download 的返回原样存成 JSON，再用fetch.py 下载：
#      python3 - <<'EOF'
#      import json,sys; json.dump({"download_url": sys.argv[1]}, open("/tmp/u.json","w"))
#      EOF
#      python3 scripts/fetch.py /tmp/u.json <输出路径>
#
# ⚠️ 依赖网盘 MCP 工具（tdrive.dir_list / file_download），
#    MCP 不可用时本脚本会跳过下载、仅做本地判定，不阻塞管线。
# =============================================================================
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${1:-$(pwd)}"
if [[ $# -gt 0 ]]; then shift; fi

SINCE=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --since) SINCE="$2"; shift 2 ;;
    *) echo "未知参数: $1" >&2; exit 1 ;;
  esac
done

WORK="${ROOT}/.intake"
mkdir -p "${WORK}/raw"

# ---- 配置：网盘知识库三层目录 ID（见《运营日志》知识库结构一节）----
KNOWLEDGE_LAYERS=(
  "dsuxMCSCwEVB:文献层"      # 五刊监控深度卡片 / 预印本速递 / 总索引
  "dVEYJcsAbUdK:行业层"      # 行业情报周报 md + xlsx
  "drGisxAlABJK:网站层"      # 网站喂料池 xlsx / 喂料池总表 / 查重报告
)

# ⚠️ 元层（任务 7762988 月度研究热点综述）**没有独立目录**——
# 实测 2026-10-15：产出 `月度研究热点综述_2026-10.md` 的 parent_id 是 dQpzABLkRxLu
# （即网站层的父目录），而 dntPxtImVdXC 下只有三个子目录。
# 漏掉这一行会导致每月 15 日的产出永远发现不了。
EXTRA_DIRS=(
  "dQpzABLkRxLu:元层"
)

echo "仓库根目录: ${ROOT}"
echo "产出暂存:   ${WORK}/raw"
echo

# ---- 1. 列出网盘产出 ----
cat > "${WORK}/manifest.tsv" <<'TSV'
# file_id<TAB>layer<TAB>name<TAB>ext<TAB>size<TAB>modify_time<TAB>modify_date
TSV

if [[ -n "${NETDRIVE_MANIFEST:-}" ]]; then
  # 由 MCP 调用方预先生成清单（file_id \t layer \t name \t ext \t size \t modify_time）
  cp "${NETDRIVE_MANIFEST}" "${WORK}/manifest.tsv"
  echo "✅ 使用外部网盘清单: ${NETDRIVE_MANIFEST}"
else
  echo "ℹ️  未提供 NETDRIVE_MANIFEST（网盘 MCP 清单），跳过网盘列举。"
  echo "    调用方应先用 tdrive.dir_list 列出各层文件，生成 TSV 后："
  echo "    NETDRIVE_MANIFEST=/path/to/list.tsv ./scripts/intake.sh"
  echo
fi

# ---- 2. 筛选新增/更新 ----
SINCE_EPOCH=$(date -u -d "${SINCE:-14 days ago}" +%s 2>/dev/null || echo 0)
echo "筛选时间窗: 自 ${SINCE:-14 天前}"
python3 - "${WORK}/manifest.tsv" "${SINCE_EPOCH}" "${WORK}/selected.tsv" <<'PY'
import sys, datetime
src, since_epoch, dst = sys.argv[1], int(sys.argv[2]), sys.argv[3]
n = 0
with open(dst, "w", encoding="utf-8") as out:
    for line in open(src, encoding="utf-8"):
        if line.startswith("#") or not line.strip():
            continue
        p = line.rstrip("\n").split("\t")
        if len(p) < 7:
            continue
        fid, layer, name, ext, size, mtime, mdate = p[:7]
        # 时间戳优先用 mdate（YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS）
        t = mdate.strip().split(" ")[0]
        try:
            epoch = int(datetime.datetime.strptime(t, "%Y-%m-%d").replace(
                tzinfo=datetime.timezone.utc).timestamp())
        except Exception:
            try:
                epoch = int(mtime) // 1000
            except Exception:
                continue
        if epoch < since_epoch:
            continue
        # 空文件是上传失败信号，跳过（曾遇到 size=0 的深度卡片）
        if size.strip() in ("0", ""):
            print(f"  ⚠️跳过空文件: {layer}/{name}（size={size}，疑似上传失败）")
            continue
        if ext.lower() not in ("md", "json", "xlsx", "csv"):
            continue
        out.write(f"{fid}\t{layer}\t{name}.{ext}\n")
        n += 1
print(f"→ 选中 {n} 个新增/更新产出文件")
PY
echo

if [[ ! -s "${WORK}/selected.tsv" ]]; then
  echo "✅ 时间窗内无新增产出，无需处理。"
  exit 0
fi

# ---- 3. 三路查重 ----
FILES=()
while IFS=$'\t' read -r fid layer name; do
  local_file="${WORK}/raw/${layer}_${name}"
  if [[ ! -f "${local_file}" ]]; then
    # 需要调用方预先下载（file_download + curl），缺失则跳过
    continue
  fi
  FILES+=("${local_file}")
done < "${WORK}/selected.tsv"

if [[ ${#FILES[@]} -eq 0 ]]; then
  echo "ℹ️  选中文件尚未下载到 ${WORK}/raw/，无法判定。"
  echo "    请先用 file_download + curl 拉取，再重跑本脚本。"
  exit 0
fi

echo "待判定产出 ${#FILES[@]} 个："
printf '  - %s\n' "${FILES[@]}"
echo

python3 "${HERE}/harvest.py" "${ROOT}" "${FILES[@]}" --out "${WORK}/harvest-report.json"

# ---- 4. 输出结论 ----
python3 - "${WORK}/harvest-report.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1], encoding="utf-8"))
print("=" * 60)
print(f"总候选 {r['total']} 条 | " +
      " ".join(f"{k} {v}" for k, v in r["summary"].items()))
miss = [i for i in r["items"] if i["status"] == "漏收"]
if not miss:
    print("✅ 无漏收：产出内容均已在站内")
else:
    print(f"\n待处理 {len(miss)} 条：")
    for i, it in enumerate(miss, 1):
        print(f"  {i:>2}. [{it['title'][:52]}]")
        print(f"      {it['basis'][:70]}")
    print("\n下一步：逐条人工复核 basis → 写稿 → gen_articles.py 上线")
    print("⚠️  不要跳过人工复核：三路判定对短关键词易误判为「已收录」")
PY