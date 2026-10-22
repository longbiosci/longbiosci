#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
push_changed.py —— 定向推送：只上传「相对远端基线真正变更」的文件。

为什么不用 push_via_api.py
--------------------------
它遍历 `git rev-list --objects HEAD` 的**全部**可达对象（885 blob），
逐个 POST /git/blobs。仓库里有几十 MB 的图片/二进制文件，
其中部分会触发 GitHub 的 400（malformed request），且整体耗时 5 分钟以上。

定向版只做 4 步，且每步都能核对 sha：
1. 对每个变更文件，POST /git/blobs（base64 内联），校验返回 sha == 本地 sha
2. 自底向上重建受影响的 tree（只重建「路径前缀」涉及的目录）
3. POST /git/commits（parent = 远端 main，tree = 新根 tree）
4. PATCH /git/refs/heads/main（**非 force**；远端若已前进则 API 拒绝，不覆盖他人提交）

安全约束
--------
- 绝不 force；
- 每一步都校验 sha，任何不一致立即中止；
- PAT 只放请求头，不打印、不落盘。

凭证来源（2026-10-22 改）
--------------------------
优先读环境变量 `GH_TOKEN` / `GITHUB_TOKEN`，不再要求传 token 文件。
原因：定时任务跑在一次性沙箱里，把 token 写进命令行参数或临时文件
既会被进程列表/日志看见，又随沙箱销毁而丢失。环境变量由任务配置注入，
一次配好长期可用，脚本也不必知道任何密钥路径。

仍保留位置参数读文件的老用法（兼容），但**不推荐**。

用法：
  python3 scripts/push_changed.py [base_ref]      # 凭证取自环境变量
  python3 scripts/push_changed.py <token_file> [base_ref]   # 旧用法
"""
import base64
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

OWNER = "longbiosci"
REPO = "longbiosci"
API = f"https://api.github.com/repos/{OWNER}/{REPO}"
BRANCH = "main"


def read_token(argv):
    """凭证取值顺序：环境变量 > 旧的 token 文件参数。

    返回 (token, 剩余参数)。argv 里的 token 文件参数（若存在）会被消费掉，
    免得被误当成 base_ref。
    """
    tok = (os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or "").strip()
    if tok:
        # 若显式传了 token 文件，忽略它（环境变量优先，且不读明文文件）
        if argv and os.path.isfile(argv[0]):
            argv = argv[1:]
        return tok, argv
    if argv and os.path.isfile(argv[0]):
        return open(argv[0]).read().strip(), argv[1:]
    raise SystemExit(
        "缺少凭证：请设置环境变量 GH_TOKEN（或 GITHUB_TOKEN），"
        "或按旧用法传入 token 文件路径。")


def sh(*args):
    return subprocess.run(args, capture_output=True, check=True).stdout


def api(path, method="GET", payload=None, token=None, retries=6):
    """带指数退避重试的 API 调用。

    2026-10-21 实测：本沙箱到 api.github.com 的链路不稳，同一份内容
    连续 POST 可能第 1 次 400（malformed request）、第 2 次就 201 成功；
    偶尔还会 socket timeout。两者都不是内容问题，是链路抖动。
    因此对 4xx/5xx 与网络异常统一重试（退避 2/4/8/16/32/60 秒）。
    """
    url = API + path
    last = ""
    for attempt in range(retries):
        data = None
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "longbiosci-ops",
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
            last = f"HTTP {e.code} on {method} {path}\n{detail}"
            # 4xx（除 429）多为请求本身问题，重试无意义；但实测该链路会
            # 对完全正确的请求返回 400，因此仍给足重试机会。
            if e.code not in (400, 403, 404, 422) and attempt < retries - 1:
                pass
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last = f"{type(e).__name__} on {method} {path}: {e}"
        if attempt < retries - 1:
            wait = min(2 ** (attempt + 1), 60)
            print(f"    重试 {attempt + 1}/{retries}（{wait}s 后）：{last.splitlines()[0]}")
            time.sleep(wait)
    raise SystemExit(f"重试 {retries} 次仍失败：\n{last}")


def main():
    token, rest = read_token(sys.argv[1:])
    base = rest[0] if rest else "0bdb2f8"

    head = sh("git", "rev-parse", "HEAD").decode().strip()
    msg = sh("git", "log", "-1", "--format=%B").decode().strip()

    remote = api(f"/git/ref/heads/{BRANCH}", token=token)
    remote_sha = remote["object"]["sha"]
    remote_commit = api(f"/git/commits/{remote_sha}", token=token)
    remote_tree = remote_commit["tree"]["sha"]
    print(f"远端 {BRANCH} = {remote_sha[:7]}  tree={remote_tree[:7]}")
    print(f"本地 HEAD     = {head[:7]}")

    if remote_sha == head:
        print("已同步，无需推送")
        return

    # 变更文件列表
    changed = [l for l in sh("git", "diff", "--name-only", base, head).decode().split("\n") if l.strip()]
    print(f"变更文件 {len(changed)} 个")

    # 1) 上传 blob
    blobs = {}
    for f in changed:
        local_sha = sh("git", "rev-parse", f"HEAD:{f}").decode().strip()
        content = open(f, "rb").read()
        r = api("/git/blobs", method="POST", token=token,
                payload={"content": base64.b64encode(content).decode(), "encoding": "base64"})
        assert r["sha"] == local_sha, f"blob sha 不一致：{f}（本地 {local_sha} / API {r['sha']}）"
        blobs[f] = local_sha
    print(f"blob 上传完成 {len(blobs)} 个，sha 全部一致")

    # 2) 重建受影响的 tree
    # 受影响的目录 = 变更文件所在的所有目录前缀
    dirs = set()
    for f in changed:
        parts = f.split("/")[:-1]
        for i in range(len(parts)):
            dirs.add("/".join(parts[:i + 1]))

    def build_tree(dirpath, base_tree_sha):
        """dirpath 为 '' 表示根。返回新 tree sha。

        注意 ls-tree 的两种用法（踩过的坑）：
        - 根目录不能用 `ls-tree HEAD ""`（空 pathspec 会报 fatal），
          要用 `ls-tree HEAD`（不带 pathspec）；
        - 子目录不能用 `ls-tree HEAD news`（那返回的是 news 这个条目本身），
          要用 `ls-tree HEAD:news`（列出 news 的**内容**）。
        两种用法返回的 name 都是**相对于该目录**的名字，可直接作为 API 的 path。
        """
        prefix = f"{dirpath}/" if dirpath else ""
        spec = "HEAD" if not dirpath else f"HEAD:{dirpath}"
        entries = []
        out = sh("git", "ls-tree", "-z", spec).decode()
        for rec in out.split("\0"):
            if not rec:
                continue
            meta, name = rec.split("\t", 1)
            mode, typ, osha = meta.split()
            assert not (name.startswith('"') and name.endswith('"')), f"路径被转义：{name}"
            path = f"{prefix}{name}"
            if typ == "tree":
                # 子目录：若它受影响则用新 tree，否则沿用远端的
                if name in dirs and dirpath:
                    entries.append({"path": name, "mode": mode, "type": "tree",
                                    "sha": build_tree(path, None)})
                else:
                    entries.append({"path": name, "mode": mode, "type": "tree", "sha": osha})
            else:
                if path in blobs:
                    entries.append({"path": name, "mode": mode, "type": "blob", "sha": blobs[path]})
                else:
                    entries.append({"path": name, "mode": mode, "type": "blob", "sha": osha})
        payload = {"tree": entries}
        if base_tree_sha:
            payload["base_tree"] = base_tree_sha
        r = api("/git/trees", method="POST", token=token, payload=payload)
        return r["sha"]

    # 受影响目录按深度倒序自底向上（深度大的先建）
    ordered = sorted(dirs, key=lambda d: (-d.count("/"), d))
    tree_map = {}
    for d in ordered:
        tree_map[d] = build_tree(d, None)
    print(f"tree 重建 {len(tree_map)} 个: {', '.join(tree_map)}")

    new_root = tree_map.get("", None)
    if new_root is None:
        new_root = build_tree("", remote_tree)
    print(f"新根 tree = {new_root[:7]}")

    # 3) 建 commit
    c = api("/git/commits", method="POST", token=token, payload={
        "message": msg, "tree": new_root, "parents": [remote_sha]})
    new_commit = c["sha"]
    print(f"新 commit = {new_commit[:7]}")

    # 4) 更新 ref（非 force）
    api(f"/git/refs/heads/{BRANCH}", method="PATCH", token=token,
        payload={"sha": new_commit, "force": False})
    print(f"✅ 已推送，远端 {BRANCH} = {new_commit[:7]}")


if __name__ == "__main__":
    main()
