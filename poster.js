/* ==========================================================================
   LongBiosci 海报生成器
   在文章页挂载「生成海报」按钮，运行时读取页面 DOM 元数据，
   用 Canvas 绘制分享长图并提供 PNG 下载。

   设计要点：
   1. 不注入任何 HTML 结构，自身在运行时挂载 → 对存量 377 篇零侵入
   2. 数据来自页面已有的 h1 / description / time / data-tier，避免重复维护
   3. 纯前端 Canvas 绘制，无第三方依赖（与全站零追踪方针一致）
   4. 幂等：重复执行只会覆盖同一挂载点，不会产生第二个按钮
   ========================================================================== */
(function () {
  'use strict';

  if (window.__lbPosterMounted) return;
  window.__lbPosterMounted = true;

  var W = 1080;                            // 导出宽度（2倍图=2160px）；高度按内容自适应
  var C = {
    ink: '#0f2b46', body: '#3d4a57', muted: '#6b7885', faint: '#94a1ad',
    primary: '#0d4f8b', green: '#1a7f4b',
    line: '#e2e8ed', bg: '#ffffff', sunken: '#f5f7f9',
    tier: {
      a: { fg: '#1a7f4b', bg: '#e6f4ec', label: 'A 级 · 同行评议人体' },
      b: { fg: '#9a6800', bg: '#fdf3e0', label: 'B 级 · 同行评议临床前' },
      c: { fg: '#5a6570', bg: '#eef1f4', label: 'C 级 · 预印本未经同行评议' }
    }
  };
  var FONT = '"PingFang SC","Hiragino Sans GB","Microsoft YaHei","Source Han Sans SC",sans-serif';

  /* ---------- 读取页面元数据 ---------- */
  function meta() {
    var cur = document.currentScript || (function () {
      var s = document.querySelectorAll('script[src*="poster.js"]');
      return s.length ? s[0] : null;
    })();

    var h1 = document.querySelector('.article-header h1, h1');
    var title = h1 ? h1.textContent.trim() : document.title.replace(/ — LongBiosci$/, '').trim();

    var d = document.querySelector('meta[name="description"]');
    var desc = d ? d.getAttribute('content') : '';

    var t = document.querySelector('time[datetime]');
    var date = t ? t.getAttribute('datetime') : '';

    var badge = document.querySelector('.notice-box .tier');
    var tier = cur && cur.getAttribute('data-tier');
    if (!tier && badge) {
      var m = badge.className.match(/tier-([abc])/);
      tier = m ? m[1] : '';
    }
    tier = (tier || '').toLowerCase();
    if (C.tier[tier] === undefined) tier = '';

    var topic = cur ? cur.getAttribute('data-topic') : '';

    // 抓取正文摘要（去标签、截断）
    var body = document.querySelector('.article-content');
    if (!desc && body) desc = body.textContent.replace(/\s+/g, ' ').trim();
    desc = desc.replace(/\s+/g, ' ').trim();

    // 提取「核心发现」要点：取正文里第一个 <ul> 的前 3 条 li，
    // 用于填充海报中段，避免出现大片空白
    var points = [];
    if (body) {
      var ul = body.querySelector('ul');
      if (ul) {
        var lis = ul.querySelectorAll('li');
        for (var i = 0; i < lis.length && points.length < 3; i++) {
          var s = lis[i].textContent.replace(/\s+/g, ' ').trim();
          if (s.length > 8) points.push(s);
        }
      }
    }

    return {
      title: title,
      desc: desc,
      date: date,
      tier: tier,
      topic: topic || '衰老与长寿',
      points: points
    };
  }

  /* ---------- Canvas 绘制工具 ---------- */
  function rr(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  // 中英混排换行。
  // 关键：ASCII 词元（数字/英文/百分比/型号）视为**不可切分原子**，
  // 否则 "847 人" 会被断成 "8" + "47 人"，中英混排时尤其难看。
  // 同时做避头尾处理，避免标点出现在行首/行尾。
  var NO_START = '，。、；：！？）》」』%…';
  var NO_END = '（《「『';

  function tokenize(text) {
    var out = [], buf = '';
    var chars = Array.from(text);
    for (var i = 0; i < chars.length; i++) {
      var ch = chars[i];
      // ASCII 词元：字母数字与常见连接符
      if (/[A-Za-z0-9]/.test(ch)) {
        buf += ch;
      } else {
        if (buf) { out.push(buf); buf = ''; }
        // 紧跟 ASCII 的连接符并入前一个词元（如 GSTP1-ROS、28%）
        if (ch === '-' || ch === '.' || ch === '%' || ch === '+') {
          if (out.length && /[A-Za-z0-9]$/.test(out[out.length - 1])) {
            out[out.length - 1] += ch;
            continue;
          }
        }
        out.push(ch);
      }
    }
    if (buf) out.push(buf);
    return out;
  }

  function wrap(ctx, text, maxW) {
    var lines = [], line = '';
    var toks = tokenize(text);
    for (var i = 0; i < toks.length; i++) {
      var t = toks[i];
      var test = line + t;
      if (ctx.measureText(test).width > maxW && line) {
        // 避头尾：行首禁则字跟随上一行
        if (NO_START.indexOf(t) >= 0) { lines.push(line + t); line = ''; continue; }
        // 避尾：上一行末是左括号类，则把它挪到下一行
        var last = line[line.length - 1];
        if (NO_END.indexOf(last) >= 0) {
          lines.push(line.slice(0, -1));
          line = last + t;
          continue;
        }
        lines.push(line);
        line = t;
      } else {
        line = test;
      }
    }
    if (line) lines.push(line);
    return lines;
  }

  function drawMark(ctx, cx, cy, r, color) {
    // 品牌标识：圆环 + 右上缺口 + 实心点
    ctx.save();
    ctx.strokeStyle = color;
    ctx.lineWidth = r * 0.26;
    ctx.lineCap = 'round';
    ctx.beginPath();
    var start = -Math.PI * 0.36, end = Math.PI * 1.42;
    ctx.arc(cx, cy, r * 0.72, start, end);
    ctx.stroke();
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(cx + r * 0.52, cy - r * 0.52, r * 0.3, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  var END_PUNCT = '。！？；';

  // 取可完整落下的句子：若首行放不下整句，回退到最近的句读并补省略号，
  // 避免海报出现「半句话」被硬切断
  function clipSentence(ctx, text, maxW, maxLines) {
    var full = wrap(ctx, text, maxW);
    if (full.length <= maxLines) return full;

    var cut = full.slice(0, maxLines);
    var joined = cut.join('');
    var last = -1;
    for (var i = joined.length - 1; i >= 0; i--) {
      if (END_PUNCT.indexOf(joined[i]) >= 0) { last = i; break; }
    }
    if (last > 8) {
      // 截到最后一个句读，重新按可用宽度排版
      var keep = joined.slice(0, last + 1);
      return wrap(ctx, keep, maxW);
    }
    // 找不到合适句读：末行补省略号
    var lastLine = cut[cut.length - 1];
    if (lastLine.length > 1) lastLine = lastLine.replace(/[，、]$/, '') + '…';
    cut[cut.length - 1] = lastLine;
    return cut;
  }

  function fitTitle(ctx, text, maxW) {
    // 标题过大时自动缩字号，保证最多 5 行放得下
    var sizes = [62, 56, 50, 45, 40, 36];
    for (var i = 0; i < sizes.length; i++) {
      ctx.font = '700 ' + sizes[i] + 'px ' + FONT;
      var lines = wrap(ctx, text, maxW);
      if (lines.length <= 5 || i === sizes.length - 1) {
        return { size: sizes[i], lines: lines };
      }
    }
    return { size: 36, lines: [] };
  }

  /* ---------- 主绘制 ---------- */
  function draw(canvas, m) {
    var dpr = 2;                                   // 2倍图，导出更清晰
    var PAD = 72;
    var maxW = W - PAD * 2;
    var FOOT_H = 132;

    /* ---- 第一遍：量出内容总高（离屏测量，不影响可见画布）---- */
    var probe = document.createElement('canvas').getContext('2d');

    var probeY = 300;
    probeY += 42;                          // topic
    if (m.date) probeY += 40;              // date
    probeY += 18;

    var fit = fitTitle(probe, m.title, maxW);
    probeY += fit.lines.length * fit.size * 1.42;
    probeY += 26 + 40;                     // 分隔线 + 间距

    probe.font = '400 27px ' + FONT;
    var dlines = clipSentence(probe, m.desc, maxW, 5);
    probeY += dlines.length * 44;

    // 要点区（与摘要之间留 44，标题 34）
    var bullets = [];
    if (m.points && m.points.length) {
      probeY += 44 + 34;
      probe.font = '400 23px ' + FONT;
      for (var i = 0; i < m.points.length; i++) {
        var bl = clipSentence(probe, m.points[i], maxW - 34, 2);
        bullets.push(bl);
        probeY += bl.length * 36 + 20;
      }
    }

    /* ---- 画布高度按内容自适应，避免底部大片空白 ---- */
    var HH = Math.round(Math.max(1080, Math.min(1600, probeY + 80 + FOOT_H)));

    canvas.width = W * dpr;
    canvas.height = HH * dpr;
    canvas.style.width = '100%';
    canvas.style.height = 'auto';
    var ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);

    // 背景
    ctx.fillStyle = C.bg;
    ctx.fillRect(0, 0, W, HH);

    // 顶部品牌带
    var grad = ctx.createLinearGradient(0, 0, W, 220);
    grad.addColorStop(0, '#0d4f8b');
    grad.addColorStop(1, '#1668b5');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, W, 220);

    drawMark(ctx, 84, 96, 30, 'rgba(255,255,255,.96)');
    ctx.fillStyle = '#fff';
    ctx.font = '700 40px ' + FONT;
    ctx.textBaseline = 'middle';
    ctx.fillText('LongBiosci', 136, 88);
    ctx.fillStyle = 'rgba(255,255,255,.8)';
    ctx.font = '400 22px ' + FONT;
    ctx.fillText('衰老生物学与长寿科技', 136, 128);

    // 证据分级徽章（右上）
    if (m.tier && C.tier[m.tier]) {
      var T = C.tier[m.tier];
      ctx.font = '600 22px ' + FONT;
      var bw = ctx.measureText(T.label).width + 36;
      rr(ctx, W - bw - 56, 62, bw, 48, 24);
      ctx.fillStyle = 'rgba(255,255,255,.17)';
      ctx.fill();
      ctx.strokeStyle = 'rgba(255,255,255,.55)';
      ctx.lineWidth = 1.5;
      ctx.stroke();
      ctx.fillStyle = '#fff';
      ctx.fillText(T.label, W - bw - 38, 87);
    }

    /* ---- 第二遍：正式绘制 ---- */
    var y = 300;
    ctx.textBaseline = 'top';

    // 主题 + 日期
    ctx.font = '600 24px ' + FONT;
    ctx.fillStyle = C.primary;
    ctx.fillText(m.topic, PAD, y);
    y += 42;
    if (m.date) {
      ctx.font = '400 22px ' + FONT;
      ctx.fillStyle = C.faint;
      ctx.fillText(m.date.replace(/-/g, '.'), PAD, y);
      y += 40;
    }

    // 标题
    y += 18;
    ctx.font = '700 ' + fit.size + 'px ' + FONT;
    ctx.fillStyle = C.ink;
    for (i = 0; i < fit.lines.length; i++) {
      ctx.fillText(fit.lines[i], PAD, y);
      y += fit.size * 1.42;
    }

    // 分隔线
    y += 26;
    ctx.strokeStyle = C.line;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(PAD, y);
    ctx.lineTo(W - PAD, y);
    ctx.stroke();
    y += 40;

    // 摘要
    ctx.font = '400 27px ' + FONT;
    ctx.fillStyle = C.body;
    for (i = 0; i < dlines.length; i++) {
      ctx.fillText(dlines[i], PAD, y);
      y += 44;
    }

    // 核心发现要点
    if (bullets.length) {
      y += 44;
      ctx.font = '600 23px ' + FONT;
      ctx.fillStyle = C.ink;
      ctx.fillText('核心发现', PAD, y);
      y += 34;
      ctx.font = '400 23px ' + FONT;
      for (i = 0; i < bullets.length; i++) {
        ctx.fillStyle = C.green;
        ctx.beginPath();
        ctx.arc(PAD + 7, y + 13, 5, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = C.body;
        for (var j = 0; j < bullets[i].length; j++) {
          ctx.fillText(bullets[i][j], PAD + 26, y);
          y += 36;
        }
        y += 20;
      }
    }

    // 底部证据条
    ctx.fillStyle = C.sunken;
    ctx.fillRect(0, HH - FOOT_H, W, FOOT_H);
    ctx.strokeStyle = C.line;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, HH - FOOT_H);
    ctx.lineTo(W, HH - FOOT_H);
    ctx.stroke();

    drawMark(ctx, PAD + 22, HH - FOOT_H / 2, 19, C.primary);
    ctx.textBaseline = 'middle';
    ctx.fillStyle = C.muted;
    ctx.font = '400 23px ' + FONT;
    ctx.fillText('longbiosci.com · 每篇标注证据分级', PAD + 62, HH - FOOT_H / 2);

    return canvas;
  }

  /* ---------- 下载 ---------- */
  function download(canvas, m) {
    var name = 'longbiosci-' + (document.title || 'poster')
      .replace(/[\\/:*?"<>|\s]+/g, '-')
      .slice(0, 60) + '.png';
    // 优先 toBlob，回退 toDataURL
    if (canvas.toBlob) {
      canvas.toBlob(function (blob) {
        var url = URL.createObjectURL(blob);
        save(url, name);
        setTimeout(function () { URL.revokeObjectURL(url); }, 2000);
      }, 'image/png');
    } else {
      save(canvas.toDataURL('image/png'), name);
    }

    function save(href, fname) {
      var a = document.createElement('a');
      a.href = href;
      a.download = fname;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }
  }

  /* ---------- UI ---------- */
  function buildUI(m) {
    var wrap = document.createElement('div');
    wrap.className = 'lb-poster';
    wrap.innerHTML =
      '<button class="lb-poster-btn" type="button" aria-label="生成文章海报">' +
      '<svg viewBox="0 0 24 24" width="17" height="17" aria-hidden="true" fill="none" ' +
      'stroke="currentColor" stroke-width="1.9" stroke-linejoin="round">' +
      '<rect x="3" y="3" width="18" height="18" rx="2"/>' +
      '<path d="M3 15l5-5 4 4 3-3 6 6"/>' +
      '<circle cx="8.5" cy="8.5" r="1.4" fill="currentColor" stroke="none"/>' +
      '</svg><span>生成海报</span></button>';

    var overlay = document.createElement('div');
    overlay.className = 'lb-poster-modal';
    overlay.setAttribute('aria-hidden', 'true');
    overlay.innerHTML =
      '<div class="lb-poster-panel" role="dialog" aria-modal="true" aria-label="文章海报">' +
      '<div class="lb-poster-head">' +
      '<strong>文章海报</strong>' +
      '<button class="lb-poster-x" type="button" aria-label="关闭">×</button>' +
      '</div>' +
      '<div class="lb-poster-canvas-box"><canvas id="lbPosterCanvas"></canvas></div>' +
      '<div class="lb-poster-actions">' +
      '<button class="lb-poster-dl" type="button">下载 PNG</button>' +
      '<p class="lb-poster-tip">长按图片也可保存到相册</p>' +
      '</div></div>';
    document.body.appendChild(overlay);

    var canvas = overlay.querySelector('#lbPosterCanvas');

    function open() {
      draw(canvas, m);
      overlay.classList.add('on');
      overlay.setAttribute('aria-hidden', 'false');
      document.body.style.overflow = 'hidden';
    }
    function close() {
      overlay.classList.remove('on');
      overlay.setAttribute('aria-hidden', 'true');
      document.body.style.overflow = '';
    }

    wrap.querySelector('.lb-poster-btn').addEventListener('click', open);
    overlay.querySelector('.lb-poster-x').addEventListener('click', close);
    overlay.querySelector('.lb-poster-dl').addEventListener('click', function () {
      download(canvas, m);
    });
    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) close();
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && overlay.classList.contains('on')) close();
    });

    // 挂载点：优先文章头部的元信息行，其次正文前
    var head = document.querySelector('.article-header');
    if (head) head.appendChild(wrap);
    else {
      var h1 = document.querySelector('h1');
      if (h1 && h1.parentNode) h1.parentNode.insertBefore(wrap, h1.nextSibling);
      else document.body.insertBefore(wrap, document.body.firstChild);
    }
  }

  function init() {
    if (!document.querySelector('h1')) return;      // 跳转页等无正文页不挂载
    buildUI(meta());
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
