#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
push_via_api.py —— 当 github.com:443 的 git 协议被网络阻断、而 api.github.com 可用时，
用 GitHub Git Data API 把本地提交推送上去。

背景（2026-10-18 实测）
----------------------
`git push` 连续三次失败：
  - `Failed to connect to github.com port 443 after 132734 ms`
  - `GnuTLS recv error (-110): The TLS connection was non-properly terminated.`
而同一时刻 `curl https://api.github.com/repos/...` 返回 200、耗时 1.1 s。
用 `/dev/tcp/github.com/443` 探测：**TCP 直接不通**。
=> 不是凭据问题，是 github.com:443 这条链路被阻断；api.github.com 是另一条可达链路。

做法
----
1. 取远端当前 main 的 tree（作为 base）；
2. 用 `git rev-list --objects <local head>` 列出本地全部可达对象，按类型分组；
   只上传远端**尚不存在**的对象（先批量 `POST /git/blobs`（内容内联）与 `POST /git/trees`（带 base_tree））；
3. `POST /git/commits`（parent = 远端 main）；
4. `PATCH /git/refs/heads/main`（**非 force**：显式传 `force: false`）。

安全约束
--------
- **绝不 force**：`force: false`，若远端在此期间又前进了，API 会拒绝，脚本报错退出，不覆盖他人提交；
- PAT 只从文件读取、只放在请求头，**不打印、不写进任何配置文件**；
- 只新增对象，不删除远端对象。

用法：python3 scripts/push_via_api.py <token_file>
"""
import base64
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

OWNER = "longbiosci"
REPO = "longbiosci"
API = f"https://api.github.com/repos/{OWNER}/{REPO}"
BRANCH = "main"


def sh(*args):
    return subprocess.run(args, capture_output=True, check=True).stdout


def api(path, method="GET", payload=None, token=None, raw=False):
    url = API + path
    data = None
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "longbiosci-intake-pusher",
    }
    if payload is not None:
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            body = r.read()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:800]
        raise SystemExit(f"HTTP {e.code} on {method} {path}\n{detail}")


def main():
    token = open(sys.argv[1]).read().strip()
    head = sh("git", "rev-parse", "HEAD").decode().strip()
    msg_file = sh("git", "log", "-1", "--format=%B").decode()

    remote = api(f"/git/ref/heads/{BRANCH}", token=token)
    remote_sha = remote["object"]["sha"]
    remote_commit = api(f"/git/commits/{remote_sha}", token=token)
    remote_tree = remote_commit["tree"]["sha"]
    print(f"远端 {BRANCH} = {remote_sha[:7]}")
    print(f"本地 HEAD     = {head[:7]}")

    if remote_sha == head:
        print("已同步，无需推送")
        return

    # 远端已有对象集合（避免重复上传）
    print("拉取远端现有对象清单…")
    have = set()
    missing_fetch = 0
    stack = [remote_tree]
    while stack:
        t = stack.pop()
        if t in have:
            continue
        have.add(t)
        try:
            tree = api(f"/git/trees/{t}", token=token)
        except SystemExit:
            # 不能静默跳过：have 不完整会让脚本误判「哪些 tree 远端已有」，
            # 把原本一致的 tree 也拿去重建 —— 一旦重建出错就会触发下面的 sha 断言。
            # 2026-10-18 正是这样把 docs/（中文文件名）误判为需重建而卡住推送的。
            missing_fetch += 1
            continue
        if tree.get("truncated"):
            raise SystemExit(
                f"远端 tree {t[:7]} 返回 truncated=true，对象清单不完整，已中止（不会推送）")
        for e in tree.get("tree", []):
            if e["type"] == "tree":
                stack.append(e["sha"])
            else:
                have.add(e["sha"])
    print(f"远端已有对象 {len(have)} 个")
    if missing_fetch:
        raise SystemExit(
            f"有 {missing_fetch} 个远端 tree 拉取失败，have 清单不完整，已中止（不会推送）")

    # 本地可达对象
    listing = sh("git", "rev-list", "--objects", head).decode().strip().split("\n")
    pairs = []
    for line in listing:
        parts = line.split(" ", 1)
        if len(parts) == 2:
            pairs.append((parts[0], parts[1]))
    shas = [p[0] for p in pairs]
    batch = subprocess.run(["git", "cat-file", "--batch-check"],
                           input="\n".join(shas).encode(),
                           capture_output=True, check=True).stdout.decode()
    types = {}
    for line in batch.strip().split("\n"):
        s, t, _ = line.split(" ", 2)
        types[s] = t

    blobs = [(s, p) for s, p in pairs if types.get(s) == "blob"]
    trees = [s for s, p in pairs if types.get(s) == "tree"]
    print(f"本地可达：blob {len(blobs)} 个 / tree {len(trees)} 个")

    # 上传缺失的 blob（内容内联，base64）
    new_blobs = 0
    uploaded = set()
    for s, path in blobs:
        if s in have:
            continue
        content = sh("git", "cat-file", "blob", s)
        payload = {
            "content": base64.b64encode(content).decode(),
            "encoding": "base64",
        }
        r = api("/git/blobs", method="POST", payload=payload, token=token)
        assert r["sha"] == s, f"blob sha 不一致：{path}"
        uploaded.add(s)
        new_blobs += 1
        if new_blobs % 50 == 0:
            print(f"  已上传 blob {new_blobs}")
    print(f"新增 blob {new_blobs} 个")

    # 上传缺失的 tree：自底向上（按 path 深度倒序，深的先建）
    #   Git Data API 建 tree 需要子项 sha，子树必须先存在。
    #   这里用「按本地 tree 内容递归重建」的方式：先算每个 tree 的直接子项，
    #   子 tree 先建；子项若为 blob 且已在远端，直接复用 sha。
    def tree_entries(sha):
        # 必须用 -z（NUL 分隔，且不做任何转义）。
        # 踩过的坑：默认 `ls-tree` 对非 ASCII 路径会按 core.quotepath 转义成
        #   "\350\277\220\350\220\245\345\276\205\346\227\245\345\277\227.md"
        # 这种八进制加引号的形式。把转义串当真实路径传给 Git Data API，
        # 建出来的 tree sha 与本地不一致 —— 于是中文文件名目录下的 tree 永远重建失败，
        # 触发下面的 assert 并中止推送（docs/ 就是这么卡住的）。
        out = sh("git", "ls-tree", "-z", sha).decode()
        res = []
        for rec in out.split("\0"):
            if not rec:
                continue
            meta, name = rec.split("\t", 1)
            mode, typ, osha = meta.split()
            # 双保险：绝不接受被引号包裹（即被转义）的路径
            assert not (name.startswith('"') and name.endswith('"')), \
                f"路径被转义，拒绝推送：{name}"
            res.append({"path": name, "mode": mode, "type": typ, "sha": osha})
        return res

    # 只重建「本地与远端不同」的 tree。判断方式：本地 tree 的 sha 若已在远端 have 中，无需重建。
    to_build = [t for t in trees if t not in have]
    print(f"需重建 tree {len(to_build)} 个")

    built = {}
    progress = True
    while to_build and progress:
        progress = False
        for t in list(to_build):
            entries = tree_entries(t)
            ok = True
            payload_entries = []
            for e in entries:
                if e["type"] == "tree":
                    if e["sha"] in have or e["sha"] in built:
                        payload_entries.append({"path": e["path"], "mode": e["mode"],
                                                "type": "tree", "sha": e["sha"]})
                    else:
                        ok = False
                        break
                else:
                    if e["sha"] not in have and e["sha"] not in uploaded:
                        ok = False
                        break
                    payload_entries.append({"path": e["path"], "mode": e["mode"],
                                            "type": "blob", "sha": e["sha"]})
            if not ok:
                continue
            r = api("/git/trees", method="POST",
                    payload={"tree": payload_entries}, token=token)
            assert r["sha"] == t, "tree sha 不一致（说明本地 tree 无法用 API 精确复现）"
            built[t] = True
            to_build.remove(t)
            progress = True
    if to_build:
        raise SystemExit(f"仍有 {len(to_build)} 个 tree 无法重建，已中止（不会推送）")
    print(f"重建 tree {len(built)} 个，全部 sha 一致")

    # 建提交
    local_commit = sh("git", "cat-file", "commit", head).decode()
    # 作者/提交者时间取本地提交里的值，保证与本地 history 一致
    import re
    author_name = re.search(r"^author (.*) <(.*)> (\d+) ([+-]\d+)$", local_commit, re.M)
    committer = re.search(r"^committer (.*) <(.*)> (\d+) ([+-]\d+)$", local_commit, re.M)
    body = local_commit.split("\n\n", 1)[1] if "\n\n" in local_commit else msg_file
    payload = {
        "message": msg_file,
        "tree": sh("git", "rev-parse", "HEAD^{tree}").decode().strip(),
        "parents": [remote_sha],
        "author": {"name": author_name.group(1), "email": author_name.group(2)},
        "committer": {"name": committer.group(1), "email": committer.group(2)},
    }
    c = api("/git/commits", method="POST", payload=payload, token=token)
    print(f"新提交 {c['sha'][:7]}")

    ref = api(f"/git/refs/heads/{BRANCH}", method="PATCH",
              payload={"sha": c["sha"], "force": False}, token=token)
    print(f"已更新 refs/heads/{BRANCH} → {ref['object']['sha'][:7]}（force=false）")


if __name__ == "__main__":
    main()
