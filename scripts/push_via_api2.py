#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
push_via_api2.py —— 面向 GitHub Git Data API 的**快路径**推送（继 push_via_api.py 之后）

为什么要有第二个版本
──────────────────
第一版（push_via_api.py）的做法是「枚举远端全部对象 → 逐个补传缺失 blob →
自底向上重建所有缺失 tree」。逻辑正确，但在本仓库规模上**实测卡死**：
2026-10-20 跑了 17 分钟、只发出 31 次请求就停住不动了 —— tree 枚举是串行的，
任一请求慢或一个抖动，整条链就卡在那里，且没有任何进度输出。

快路径的关键认知：**Git Data API 创建 tree 支持 `base_tree` 参数。**
传生长发育远端 tree 作为基座，再只列出**发生变化的路径**即可：
  - 修改/新增：{path, mode, type:"blob", sha}
  - 删除：{path, sha: null}
嵌套路径（含 '/'）由 GitHub 自行展开成子树，**无需自底向上重建**。
于是请求数从「几百 tree + 几百 blob」降到「几十 blob + 4 次」。

请求清单
────────
1. GET  /git/ref/heads/{branch}          （取远端 HEAD）
2. GET  /git/commits/{remote_sha}        （取远端 tree）
3. POST /git/blobs           ×变更文件数 （仅上传猿端没有的 blob，并发）
4. POST /git/trees           ×1          （base_tree = 远端 tree + 变更项）
5. POST /git/commits         ×1          （parents = [远端 HEAD]）
6. PATCH /git/refs/heads/{branch} ×1     （**force: false**）

安全约束
────────
- **绝不 force**：显式 `force: false`；若远端在此期间又前进了，API 会拒绝，脚本报错退出。
- **树 sha 强校验**：新 tree 的 sha 必须与本地 `HEAD^{tree}` 完全一致，
  不一致就中止，**绝不创建一个内容不确定的远端 tree**（比失败更危险）。
- PAT 只从文件读取、只放请求头，不打印、不写入任何配置文件。

用法
────
  python3 scripts/push_via_api2.py <token_file> [--dry-run]

变更多少 сердцу depends on 与哪个基准比：`--base <tree-ish>` 可指定基准
（默认是工作方式与合成快照提交 840ec3f 的差异，见下方 SNAPSHOT_COMMIT）。
"""
import base64
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

OWNER = "longbiosci"
REPO = "longbiosci"
API = f"https://api.github.com/repos/{OWNER}/{REPO}"
BRANCH = "main"

# 远端 main（3b59970d）的 trees 在本地被重建成的提交对象。
# 它**不是**远端那个提交的 sha（对象 sha 无法离线复现），但**内容与远端 tree 一致**，
# 因此可当作「远端此刻长什么样」的本地代理，用来算差异。
# ⚠️ 该提交会随沙箱重建丢失（2026-10-24 实测：丢失后 rev-parse 直接崩）。
# 已由 resolve_base() 自愈：缺失/过期时自动在本地历史找 tree 等价的提交。
SNAPSHOT_COMMIT = "840ec3ff24320f51334871c8c750d6355e0d0f8d"


def _local_tree(rev):
    """本地提交的 tree sha；rev 不存在返回 None（不抛异常）。"""
    r = subprocess.run(["git", "rev-parse", rev + "^{tree}"],
                       capture_output=True)
    return r.stdout.decode().strip() if r.returncode == 0 else None


def resolve_base(base, remote_tree):
    """基准自愈：硬编码快照提交丢失或远端前进后，在本地历史里找一个
    tree 与远端一致的提交——内容等价即可用于算差异，commit sha 无需相同。
    找不到才按 SOP 报错（下载 tarball 重建快照），严禁带着过期基准上路。
    """
    if _local_tree(base) == remote_tree:
        return base
    for c in sh("git", "rev-list", "HEAD", "-n", "100").decode().split():
        if _local_tree(c) == remote_tree:
            print(f"⚠️ 基准 {base[:10]} 本地缺失或已过期 → 自动改用等价提交 "
                  f"{c[:10]}（tree 与远端一致 {remote_tree[:10]}）")
            return c
    raise SystemExit(
        f"✗ 基准 {base[:10]} 不可用，且本地历史中找不到 tree == 远端 "
        f"{remote_tree[:10]} 的提交。\n"
        f"  按 SOP：下载远端 tarball → 重建为本地提交 → 重试；不要带着过期基准上路。")


def sh(*args, check=True):
    return subprocess.run(args, capture_output=True, check=check).stdout


def api(path, method="GET", payload=None, token=None, timeout=60):
    url = API + path
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "longbiosci-push-fastpath",
    }
    data = None
    if payload is not None:
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:800]
        raise SystemExit(f"HTTP {e.code} on {method} {path}\n{detail}")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    # 凭证优先取环境变量（定时任务一次配置长期可用），其次才读文件
    token = (os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or "").strip()
    if not token:
        if not args:
            raise SystemExit("缺少凭证：请设置 GH_TOKEN 环境变量，或传入 token 文件路径。")
        token = open(args[0]).read().strip()
        args = args[1:]

    # --base <tree-ish>：差异的一端。默认用重建的远端快照提交；
    # 连续推送时可传 --base <远端 tree sha>，省去重新下载快照。
    base = SNAPSHOT_COMMIT
    if "--base" in sys.argv:
        base = sys.argv[sys.argv.index("--base") + 1]
    # 用环境变量取凭证时不能再要求位置参数，否则等于没改成「免传文件」
    if len(args) < 1 and not token:
        raise SystemExit("用法：push_via_api2.py [token文件] [--base <tree-ish>] [--dry-run]")

    head = sh("git", "rev-parse", "HEAD").decode().strip()
    head_tree = sh("git", "rev-parse", "HEAD^{tree}").decode().strip()

    remote = api(f"/git/ref/heads/{BRANCH}", token=token)
    remote_sha = remote["object"]["sha"]
    remote_commit = api(f"/git/commits/{remote_sha}", token=token)
    remote_tree = remote_commit["tree"]["sha"]
    print(f"远端 {BRANCH:6s}= {remote_sha[:10]}")
    print(f"本地 HEAD     = {head[:10]}")
    base = resolve_base(base, remote_tree)

    # 1) 快照 fidelity 校验：本地重建的远端 tree 必须与 API 返回的 tree sha 一致。
    #    不一致说明快照不是远端此刻的样子，此时算出的差异不可用。
    snap_tree = sh("git", "rev-parse", base + "^{tree}").decode().strip()
    if snap_tree != remote_tree:
        raise SystemExit(
            f"✗ 基准校验失败：本地快照 tree {snap_tree[:10]} ≠ 远端 tree {remote_tree[:10]}。\n"
            f"  远端可能在此期间又前进了——请重新下载远端快照后再推，不要带着过期基准上路。")
    print(f"✓ 基准一致：本地快照 tree == 远端 tree（{remote_tree[:10]}）")

    # 2) 算差异
    diff = sh("git", "diff", "--name-status", "-z", "--find-renames",
              base, head).decode()
    recs = [r for r in diff.split("\0") if r]
    adds, mods, dels = [], [], []
    i = 0
    while i < len(recs):
        st = recs[i]
        if st.startswith("R") or st.startswith("C"):       # R100 / C75 后跟两个路径
            oldp, newp = recs[i + 1], recs[i + 2]
            dels.append(oldp)
            adds.append(newp)
            i += 3
            continue
        path = recs[i + 1]
        if st == "A":
            adds.append(path)
        elif st == "D":
            dels.append(path)
        else:                                               # M / T
            mods.append(path)
        i += 2
    changed_paths = adds + mods
    print(f"变更：新增 {len(adds)} / 修改 {len(mods)} / 删除 {len(dels)}"
          f"（共 {len(changed_paths) + len(dels)} 项）")
    if dels:
        print("  删除项：" + ", ".join(dels[:6]) + ("…" if len(dels) > 6 else ""))

    # 3) 取 blob sha + 模式
    entries = []
    blobs = []
    for p in changed_paths:
        # -z 下 git 不转义非 ASCII 路径；同时显式关掉 quotepath 双保险
        meta = sh("git", "-c", "core.quotepath=false", "ls-tree", "-z",
                  "HEAD", "--", p).decode().strip("\0")
        if not meta:
            raise SystemExit(f"✗ HEAD 里找不到 {p}")
        info, name = meta.split("\t", 1)
        mode, typ, sha = info.split()
        assert name == p, f"路径解析不一致：读到 {name!r}，期望 {p!r}"
        blobs.append((p, sha))
        entries.append({"path": p, "mode": mode, "type": "blob", "sha": sha})
    for p in dels:
        entries.append({"path": p, "sha": None})

    # 4) 上传远端没有的 blob（并发）
    #    判断「远端有没有」不用枚举远端全部对象：直接 GET /git/blobs/{sha}，
    #    存在就是 200（本地 reproduce 出来的 sha 远端有同内容文件即命中）。
    def need_upload(item):
        path, sha = item
        try:
            api(f"/git/blobs/{sha}", token=token, timeout=30)
            return None
        except SystemExit:
            return item

    todo = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        for r in ex.map(need_upload, blobs):
            if r:
                todo.append(r)
    print(f"需上传 blob：{len(todo)} / {len(blobs)}")

    def put_blob(item):
        path, sha = item
        content = sh("git", "cat-file", "blob", sha)
        r = api("/git/blobs", method="POST", payload={
            "content": base64.b64encode(content).decode(),
            "encoding": "base64"}, token=token, timeout=120)
        assert r["sha"] == sha, f"blob sha 不一致：{path}（{r['sha']} vs {sha}）"
        return path

    if todo and not dry:
        with ThreadPoolExecutor(max_workers=8) as ex:
            done = sum(1 for _ in ex.map(put_blob, todo))
        print(f"✓ 已上传 {done} 个 blob")
    elif todo:
        print("  （dry-run：跳过上传）")

    # 5) 建 tree（一次请求）
    print(f"建 tree：base_tree={remote_tree[:10]} + {len(entries)} 项")
    if dry:
        print("  （dry-run：不创建 tree/commit/更新 ref）")
        return
    new_tree = api("/git/trees", method="POST",
                   payload={"base_tree": remote_tree, "tree": entries},
                   token=token, timeout=180)
    if new_tree["sha"] != head_tree:
        raise SystemExit(
            f"✗ tree sha 不一致：API 建出 {new_tree['sha'][:10]}，本地 HEAD^{{tree}} 是 {head_tree[:10]}。\n"
            f"  已中止，未创建提交——宁可推不上去，也不推一个内容不确定的远端。")
    print(f"✓ tree sha 与本地 HEAD 完全一致（{head_tree[:10]}）")

    # 6) 建提交 + 更新 ref（非 force）
    commit = sh("git", "log", "-1", "--format=%B").decode()
    c = api("/git/commits", method="POST", payload={
        "message": commit, "tree": new_tree["sha"], "parents": [remote_sha]},
        token=token)
    print(f"✓ 新提交 {c['sha'][:10]}（parents=[{remote_sha[:10]}]）")

    ref = api(f"/git/refs/heads/{BRANCH}", method="PATCH",
              payload={"sha": c["sha"], "force": False}, token=token)
    print(f"✓ 已更新 refs/heads/{BRANCH} → {ref['object']['sha'][:10]}（force=false）")


if __name__ == "__main__":
    main()
