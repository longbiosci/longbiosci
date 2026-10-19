#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
synth_podcast_audio.py —— 播客文稿 → mp3 合成器（手动运行，不进管线）

为什么不在管线里跑
------------------
TTS 走微软 Edge 在线语音端点（edge-tts），无 SLA：网络波动会直接阻断整条
站点管线，且同一文稿重复合成会产出不同音频。本站的取舍是——**音频是发布物，
不是构建物**：文稿定稿 → 本脚本合成一次 → mp3 入 git → 管线里的
gen-podcast.py 只生成页面与 RSS，并校验音频文件存在。

环境要求
--------
edge-tts 装在系统 Python 3.12（PEP 668 阻止了 pyenv 3.11 环境内的安装）。
必须用系统解释器显式运行：

    /usr/bin/python3.12 scripts/synth_podcast_audio.py <transcript.md> [--force]

用法
----
  /usr/bin/python3.12 scripts/synth_podcast_audio.py podcast/transcripts/<slug>.md

产物：audio/<slug>.mp3（frontmatter 里的 slug 决定文件名）
      合成后打印 ffprobe 实测时长——把它回填进 data/podcast.json 的
      duration_sec 字段（不手填，见策划文档 §5.2）。

幂等：已存在同名 mp3 时默认跳过；--force 重新合成。

文稿格式约定（transcripts/*.md）
-------------------------------
  frontmatter：slug / series / title / date / voice / rate（YAML 简易键值）
  正文：`#` 开头的行是标题不口播；其余全部口播；空行分段。
author: LongBiosci 网站运营自动化
"""
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"
DEFAULT_RATE = "+5%"


def parse_transcript(path):
    """拆出 frontmatter 键值 + 口播正文（去标题行）。"""
    s = open(path, encoding="utf-8").read()
    meta, body = {}, s
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", s, flags=re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip().strip('"').strip("'")
        body = s[m.end():]
    spoken_lines = [l for l in body.splitlines() if not l.lstrip().startswith("#")]
    text = "\n".join(spoken_lines).strip()
    return meta, text


def synth(text, voice, rate, out_path):
    """edge-tts 合成。长文本按段落分块合成后 concat，规避单请求长度限制。"""
    import asyncio
    import edge_tts

    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    tmp_dir = os.path.join(os.path.dirname(out_path), ".synth_tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    parts = []

    async def one(i, chunk):
        p = os.path.join(tmp_dir, "part_%03d.mp3" % i)
        tts = edge_tts.Communicate(chunk, voice=voice, rate=rate)
        await tts.save(p)
        parts.append(p)

    async def main():
        for i, chunk in enumerate(paras):
            await one(i, chunk)

    asyncio.run(main())

    # concat（mp3 直接 concat 再重封装，段间保留 edge-tts 自然句读）
    list_file = os.path.join(tmp_dir, "list.txt")
    with open(list_file, "w", encoding="utf-8") as f:
        for p in parts:
            f.write("file '%s'\n" % os.path.basename(p))
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", list_file, "-c", "copy", out_path],
        check=True,
    )
    for p in parts:
        os.remove(p)
    os.remove(list_file)
    os.rmdir(tmp_dir)


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration,bit_rate,size",
         "-of", "default=noprint_wrappers=1", path],
        capture_output=True, text=True, check=True,
    ).stdout
    d = dict(l.split("=") for l in out.strip().splitlines())
    return float(d["duration"]), int(d.get("bit_rate", 0) or 0), int(d.get("size", 0) or 0)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    path = sys.argv[1]
    force = "--force" in sys.argv[2:]
    meta, text = parse_transcript(path)
    slug = meta.get("slug") or os.path.splitext(os.path.basename(path))[0]
    voice = meta.get("voice") or DEFAULT_VOICE
    rate = meta.get("rate") or DEFAULT_RATE
    out = os.path.join(REPO, "audio", slug + ".mp3")
    os.makedirs(os.path.dirname(out), exist_ok=True)

    if os.path.exists(out) and not force:
        dur, br, size = probe(out)
        print("已存在，跳过（--force 可重合成）: %s" % out)
    else:
        print("合成中：%d 段 · %d 字 · 音色 %s · 语速 %s" % (
            len([p for p in re.split(r"\n\s*\n", text) if p.strip()]),
            len(re.sub(r"\s", "", text)), voice, rate))
        synth(text, voice, rate, out)
        dur, br, size = probe(out)
        print("完成: %s" % out)

    print("duration_sec = %d（%.1f 分钟） · bit_rate = %d · size = %.2f MB"
          % (round(dur), dur / 60, br, size / 1048576))
    print("→ 把 duration_sec=%d 回填进 data/podcast.json 对应期目" % round(dur))


if __name__ == "__main__":
    main()
