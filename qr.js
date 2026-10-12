/* ==========================================================================
   qr.js —— 零依赖 QR Code 编码器（字节模式，EC level M）

   为什么自己写：
   全站方针是零第三方依赖、零追踪，任何 CDN 上的 qrcode 库都是一个
   「把读者 IP 交给第三方的请求」。二维码只编码一个纯文本 URL，
   自己实现完全可控，且没有维护负担以外的隐性成本。

   实现范围：字节模式 + EC level M + 版本 1..20自动选择 + mask 0..7 全量评估。
   足够覆盖 https://longbiosci.com/news/<slug>.html 这类长度的 URL。
   参考 ISO/IEC 18004。
   ========================================================================== */
(function (global) {
  'use strict';

  /* ---------- GF(256)伽罗华域运算 ---------- */
  // QR 用本原多项式 x^8 + x^4 + x^3 + x^2 + 1 (0x11D)
  var EXP = new Uint8Array(512);
  var LOG = new Uint8Array(256);
  (function () {
    var x = 1;
    for (var i = 0; i < 255; i++) {
      EXP[i] = x;
      LOG[x] = i;
      x <<= 1;
      if (x & 0x100) x ^= 0x11D;
    }
    for (var j = 255; j < 512; j++) EXP[j] = EXP[j - 255];
  })();

  function gmul(a, b) {
    if (a === 0 || b === 0) return 0;
    return EXP[LOG[a] + LOG[b]];
  }

  /* ---------- 版本参数表（EC level M）----------
     每项：[每块纠错码字数, 组1块数, 组1数据码字, 组2块数, 组2数据码字]
     注意：rawDataModules 返回的是「模块（bit）数」，而版本表是「码字（byte）数」，
     两者单位不同，必须先整除 8 再减去纠错码字。 */
  var VER_M = {
    1:  [10, 1, 16, 0, 0],
    2:  [16, 1, 28, 0, 0],
    3:  [26, 1, 44, 0, 0],
    4:  [18, 2, 32, 0, 0],
    5:  [24, 2, 43, 0, 0],
    6:  [16, 4, 27, 0, 0],
    7:  [18, 4, 31, 0, 0],
    8:  [22, 2, 38, 2, 39],
    9:  [22, 3, 36, 2, 37],
    10: [26, 4, 43, 1, 44],
    11: [30, 1, 50, 4, 51],
    12: [22, 6, 36, 2, 37],
    13: [22, 8, 37, 1, 38],
    14: [24, 4, 40, 5, 41],
    15: [24, 5, 41, 5, 42],
    16: [28, 7, 45, 3, 46],
    17: [28, 10, 46, 1, 47],
    18: [26, 9, 43, 4, 44],
    19: [26, 3, 44, 11, 45],
    20: [26, 3, 41, 13, 42]
  };

  // 每版本的功能模块总数（用于算容量），公式来自 ISO/IEC 18004 表9
  function rawDataModules(ver) {
    var r = (16 * ver + 128) * ver + 64;
    if (ver >= 2) {
      var n = Math.floor(ver / 7) + 2;
      r -= (25 * n - 10) * n - 55;
      if (ver >= 7) r -= 36;
    }
    return r;
  }

  function dataCodewords(ver) {
    var p = VER_M[ver];
    // rawDataModules 是 bit 数 -> 整除 8 得总码字数 -> 减去纠错码字
    return Math.floor(rawDataModules(ver) / 8) - p[0] * (p[1] + p[3]);
  }

  /* ---------- 对齐图形中心坐标 ---------- */
  function alignPositions(ver) {
    if (ver === 1) return [];
    var n = Math.floor(ver / 7) + 2;
    var size = ver * 4 + 17;
    var step = (ver === 32) ? 26 : Math.ceil((ver * 4 + 4) / (n * 2 - 2)) * 2;
    var pos = [6];
    for (var p = size - 7; pos.length < n; p -= step) pos.splice(1, 0, p);
    return pos;
  }

  /* ---------- 生成纠错码字（Reed-Solomon） ----------
     直接用 ISO/IEC 18004:2015 附录 A 表 A.1 的生成多项式系数，
     而不是运行时推导 —— 推导容易因系数次序/首项约定出错，
     而这张表是标准原文，18 个长度全覆盖，不存在约定歧义。 */
  var GEN_POLY = {
    2: [25, 1],
    5: [113, 164, 166, 119, 10],
    6: [166, 0, 134, 5, 176, 15],
    7: [87, 229, 146, 149, 238, 102, 21],
    8: [175, 238, 208, 249, 215, 252, 196, 28],
    10: [251, 67, 46, 61, 118, 70, 64, 94, 32, 45],
    13: [74, 152, 176, 100, 86, 100, 106, 104, 130, 218, 206, 140, 78],
    14: [199, 249, 155, 48, 190, 124, 218, 137, 216, 87, 207, 59, 22, 91],
    15: [8, 183, 61, 91, 202, 37, 51, 58, 58, 237, 140, 124, 5, 99, 105],
    16: [120, 104, 107, 109, 102, 161, 76, 3, 91, 191, 147, 169, 182, 194, 225, 120],
    17: [43, 139, 206, 78, 43, 239, 123, 206, 214, 147, 24, 99, 150, 39, 243, 163, 136],
    18: [215, 234, 158, 94, 184, 97, 118, 170, 79, 187, 152, 148, 252, 179, 5, 98, 96, 153],
    20: [17, 60, 79, 50, 61, 163, 26, 187, 202, 180, 221, 225, 83, 239, 156, 164, 212, 212, 188, 190],
    22: [210, 171, 247, 242, 93, 230, 14, 109, 221, 53, 200, 74, 8, 172, 98, 80, 219, 134, 160, 105, 165, 231],
    24: [229, 121, 135, 48, 211, 117, 251, 126, 159, 180, 169, 152, 192, 226, 228, 218, 111, 0, 117, 232, 87, 96, 227, 21],
    26: [173, 125, 158, 2, 103, 182, 118, 17, 145, 201, 111, 28, 165, 53, 161, 21, 245, 142, 13, 102, 48, 227, 153, 145, 218, 70],
    28: [168, 223, 200, 104, 224, 234, 108, 180, 110, 190, 195, 147, 205, 27, 232, 201, 21, 43, 245, 87, 42, 195, 212, 119, 242, 37, 9, 123],
    30: [41, 173, 145, 152, 216, 31, 179, 182, 50, 48, 110, 86, 239, 96, 222, 125, 42, 173, 226, 193, 224, 130, 156, 37, 251, 216, 238, 40, 192, 180]
  };

  function eccBytes(data, n) {
    var gen = GEN_POLY[n];
    if (!gen) throw new Error('QR: 不支持的纠错码长度 ' + n);
    // 合成除法：把 data 后补 n 个 0 作为移位寄存器，
    // 逐字节用生成多项式系数消去最高项，最后 n 字节即纠错码。
    // ⚠️ 必须写成「写回 buf[k+j+1]」的形式。若改成 res[j] ^= ... 的
    // 紧凑写法会差一个移位，ECC 全错但不会报错——极其隐蔽。
    var buf = data.slice().concat(new Array(n).fill(0));
    for (var k = 0; k < data.length; k++) {
      var coef = buf[k];
      if (coef !== 0) {
        var lc = LOG[coef];
        for (var j = 0; j < n; j++) buf[k + j + 1] ^= EXP[lc + gen[j]];
      }
    }
    return buf.slice(data.length);
  }

  /* ---------- 8种掩码 ---------- */
  function maskBit(mask, r, c) {
    switch (mask) {
      case 0: return (r + c) % 2 === 0;
      case 1: return r % 2 === 0;
      case 2: return c % 3 === 0;
      case 3: return (r + c) % 3 === 0;
      case 4: return (Math.floor(r / 2) + Math.floor(c / 3)) % 2 === 0;
      case 5: return (r * c) % 2 + (r * c) % 3 === 0;
      case 6: return ((r * c) % 2 + (r * c) % 3) % 2 === 0;
      default: return ((r + c) % 2 + (r * c) % 3) % 2 === 0;
    }
  }

  /* ---------- 主流程 ---------- */
  function encode(text) {
    var utf8 = unescape(encodeURIComponent(text));   // 转字节
    var len = utf8.length;

    // 选版本
    var ver = 0;
    for (var v = 1; v <= 20; v++) {
      var cap = dataCodewords(v);
      var needBits = 4 + (v < 10 ? 8 : 16) + len * 8;
      if (needBits <= cap * 8) { ver = v; break; }
    }
    if (!ver) throw new Error('QR: 内容过长（需 >版本20）');

    // ---- 位流：模式指示符 + 字符计数 + 数据 + 终止符 ----
    var bits = [];
    function push(val, n) { for (var i = n - 1; i >= 0; i--) bits.push((val >> i) & 1); }
    push(4, 4);                                    // 字节模式
    push(len, ver < 10 ? 8 : 16);
    for (var b = 0; b < len; b++) push(utf8.charCodeAt(b), 8);

    var capBits = dataCodewords(ver) * 8;
    push(0, Math.min(4, capBits - bits.length));     // 终止符
    while (bits.length % 8 !== 0) bits.push(0);      // 补齐字节
    // 填充字节 0xEC / 0x11
    var padByte = 0xEC;
    while (bits.length < capBits) {
      push(padByte, 8);
      padByte ^= 0xEC ^ 0x11;
    }

    var dataCw = [];
    for (var i2 = 0; i2 < bits.length; i2 += 8) {
      var byteV = 0;
      for (var t = 0; t < 8; t++) byteV = (byteV << 1) | bits[i2 + t];
      dataCw.push(byteV);
    }

    // ---- 分块 + 纠错 ----
    var p = VER_M[ver];
    var blocks = [];
    var eccLen = p[0], n1 = p[1], d1 = p[2], n2 = p[3], d2 = p[4];
    var off = 0, k;
    for (k = 0; k < n1; k++) { blocks.push(dataCw.slice(off, off + d1)); off += d1; }
    for (k = 0; k < n2; k++) { blocks.push(dataCw.slice(off, off + d2)); off += d2; }
    var eccs = blocks.map(function (blk) { return eccBytes(blk, eccLen); });

    // 交织
    var finalCw = [];
    var maxD = Math.max(d1, d2);
    for (var c = 0; c < maxD; c++) {
      for (k = 0; k < blocks.length; k++) if (c < blocks[k].length) finalCw.push(blocks[k][c]);
    }
    for (var e = 0; e < eccLen; e++) {
      for (k = 0; k < eccs.length; k++) finalCw.push(eccs[k][e]);
    }

    // ---- 铺矩阵 ----
    var size = ver * 4 + 17;
    var mod = [], isFn = [];
    for (var r0 = 0; r0 < size; r0++) {
      mod.push(new Array(size).fill(0));
      isFn.push(new Array(size).fill(false));
    }

    function finder(r, c) {
      for (var dr = -1; dr <= 7; dr++) {
        for (var dc = -1; dc <= 7; dc++) {
          var rr = r + dr, cc = c + dc;
          if (rr < 0 || rr >= size || cc < 0 || cc >= size) continue;
          var inRing = (dr >= 0 && dr <= 6 && (dc === 0 || dc === 6)) ||
                       (dc >= 0 && dc <= 6 && (dr === 0 || dr === 6));
          var inCore = dr >= 2 && dr <= 4 && dc >= 2 && dc <= 4;
          mod[rr][cc] = (inRing || inCore) ? 1 : 0;
          isFn[rr][cc] = true;
        }
      }
    }
    finder(0, 0); finder(0, size - 7); finder(size - 7, 0);

    // 定时图形
    for (var i3 = 8; i3 < size - 8; i3++) {
      var v = i3 % 2 === 0 ? 1 : 0;
      mod[6][i3] = v; isFn[6][i3] = true;
      mod[i3][6] = v; isFn[i3][6] = true;
    }

    // 对齐图形
    var ap = alignPositions(ver);
    for (var ai = 0; ai < ap.length; ai++) {
      for (var aj = 0; aj < ap.length; aj++) {
        var ar = ap[ai], ac = ap[aj];
        // 跳过与 finder 重叠的三个角
        if ((ar <= 8 && ac <= 8) || (ar <= 8 && ac >= size - 9) || (ar >= size - 9 && ac <= 8)) continue;
        for (var dr2 = -2; dr2 <= 2; dr2++) {
          for (var dc2 = -2; dc2 <= 2; dc2++) {
            var m2 = (Math.max(Math.abs(dr2), Math.abs(dc2)) !== 1) ? 1 : 0;
            mod[ar + dr2][ac + dc2] = m2;
            isFn[ar + dr2][ac + dc2] = true;
          }
        }
      }
    }

    // 保留格式信息区（先占位，掩码后再写）
    function reserveFormat() {
      for (var i4 = 0; i4 <= 8; i4++) {
        if (i4 !== 6) { isFn[8][i4] = true; isFn[i4][8] = true; }
      }
      for (var i5 = 0; i5 < 8; i5++) {
        isFn[8][size - 1 - i5] = true;
        isFn[size - 1 - i5][8] = true;
      }
      isFn[size - 8][8] = true;   // 固定黑模块
    }
    reserveFormat();

    // 数据铺设（ISO/IEC 18004:2015 §7.7.3 符号字符放置）
    //
    // 从右下角起，两列宽为一组，自右向左交替上下扫。
    // ⚠️ 两个容易写错的点：
    //   1) right <= 6 时整组左移 1（跳过第 6 列定时图形），
    //      不能只判 right == 6，否则会漏掉左侧第 5 列那一组。
    //   2) 上下方向由 right 决定（(right&2)==0 为向上），
    //      且跨过第 6 列时要反转，不能靠一个 dir 变量一直翻转。
    var bitIdx = 0;
    var totalBits = finalCw.length * 8;
    for (var right = size - 1; right > 0; right -= 2) {
      var rr2 = right;
      if (rr2 <= 6) rr2 -= 1;
      for (var vert = 0; vert < size; vert++) {
        for (var z = 0; z < 2; z++) {
          var j = rr2 - z;
          var upwards = ((rr2 & 2) === 0);
          if (j < 6) upwards = !upwards;
          var i2 = upwards ? (size - 1 - vert) : vert;
          if (!isFn[i2][j]) {
            var bit = 0;
            if (bitIdx < totalBits) {
              bit = (finalCw[bitIdx >> 3] >> (7 - (bitIdx & 7))) & 1;
            }
            bitIdx++;
            mod[i2][j] = bit;
          }
        }
      }
    }

    // ---- 选最佳掩码：8种全试，按 ISO 惩罚分取最低 ----
    var best = null, bestScore = Infinity;
    for (var mask = 0; mask < 8; mask++) {
      var cand = mod.map(function (rowArr) { return rowArr.slice(); });
      for (var rr2 = 0; rr2 < size; rr2++) {
        for (var cc3 = 0; cc3 < size; cc3++) {
          if (!isFn[rr2][cc3] && maskBit(mask, rr2, cc3)) cand[rr2][cc3] ^= 1;
        }
      }
      writeFormat(cand, size, mask);
      var sc = penalty(cand, size);
      if (sc < bestScore) { bestScore = sc; best = cand; }
    }

    return { size: size, modules: best };
  }

  /* ---------- 格式信息（EC=M, 掩码 3bit） ----------
     关键：垂直方向与水平方向的位序**相反**（ISO/IEC 18004:2015 §7.9.1 图25）：
       垂直列（第8列）  LSB-first：bit0 在最上（行0）
       水平行（第8行）  MSB-first：bit14 在最左（列0）
     跳过定时图形（第6行/列），故第6位之后坐标整体偏移1。
     参考实现 segno.encoder.add_format_info 的权威逻辑。 */
  var FMT_M = 0;   // EC level M → 索引偏移 0x00
  var FMT_MASK = 0x5412;

  function fmtBits(ec, mask) {
    var data = (ec << 3) | mask;
    var rem = data;
    for (var i4 = 0; i4 < 10; i4++) rem = (rem << 1) ^ (((rem >> 9) & 1) * 0x537);
    return ((data << 10) | rem) ^ FMT_MASK;
  }

  function writeFormat(m, size, mask) {
    var bits = fmtBits(FMT_M, mask);
    var voff = 0, hoff = 0;
    var row8 = m[8];
    for (var i = 0; i < 8; i++) {
      var vbit = (bits >> i) & 1;            // 垂直用 LSB
      var hbit = (bits >> (14 - i)) & 1;      // 水平用 MSB
      if (i === 6) { voff += 1; hoff = 1; }  // 越过定时图形
      m[i + voff][8] = vbit;                 // 垂直列
      row8[i + hoff] = hbit;                 // 水平行
      row8[size - 1 - i] = vbit;             // 水平行右上副本
      m[size - 1 - i][8] = hbit;             // 垂直列左下副本
    }
    m[size - 8][8] = 1;                      // 固定黑模块
  }

  /* ---------- 掩码惩罚分（ISO 18004 第8节） ---------- */
  function penalty(m, size) {
    var score = 0, r, c, i;

    // 规则1：同色连续 >=7
    for (r = 0; r < size; r++) {
      var runV = 1;
      for (c = 1; c < size; c++) {
        if (m[r][c] === m[r][c - 1]) { runV++; if (runV === 5) score += 3; else if (runV > 5) score += 1; }
        else runV = 1;
      }
    }
    for (c = 0; c < size; c++) {
      var runH = 1;
      for (r = 1; r < size; r++) {
        if (m[r][c] === m[r - 1][c]) { runH++; if (runH === 5) score += 3; else if (runH > 5) score += 1; }
        else runH = 1;
      }
    }

    // 规则2：2x2 同色块
    for (r = 0; r < size - 1; r++) {
      for (c = 0; c < size - 1; c++) {
        var v2 = m[r][c];
        if (v2 === m[r][c + 1] && v2 === m[r + 1][c] && v2 === m[r + 1][c + 1]) score += 3;
      }
    }

    // 规则3：类似 finder 的 1:1:3:1:1 图案
    var pat1 = [1,0,1,1,1,0,1,0,0,0,0];
    var pat2 = [0,0,0,0,1,0,1,1,1,0,1];
    function matchAt(get, n) {
      var a = true, b = true;
      for (i = 0; i < 11; i++) {
        if (get(i) !== pat1[i]) a = false;
        if (get(i) !== pat2[i]) b = false;
      }
      return (a ? 1 : 0) + (b ? 1 : 0);
    }
    for (r = 0; r < size; r++) {
      for (c = 0; c <= size - 11; c++) {
        score += 40 * matchAt(function (i) { return m[r][c + i]; }, size);
      }
    }
    for (c = 0; c < size; c++) {
      for (r = 0; r <= size - 11; r++) {
        score += 40 * matchAt(function (i) { return m[r + i][c]; }, size);
      }
    }

    // 规则4：黑白比例偏离 50%
    var dark = 0;
    for (r = 0; r < size; r++) for (c = 0; c < size; c++) dark += m[r][c];
    var ratio = dark * 100 / (size * size);
    score += Math.floor(Math.abs(ratio - 50) / 5) * 10;

    return score;
  }

  /* ---------- 对外：返回可布尔矩阵 ---------- */
  function matrix(text) {
    var q = encode(text);
    var out = [];
    for (var r = 0; r < q.size; r++) {
      out.push(q.modules[r].slice());
    }
    return out;
  }

  global.LBQR = { encode: encode, matrix: matrix };
})(typeof window !== 'undefined' ? window : this);