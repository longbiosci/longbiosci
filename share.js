/* LongBiosci 文章页分享条：复制链接 + 二维码（本地同源库，无外部依赖）
 * 依赖 /qrcode.min.js（qrcode-generator）。本文件只做初始化，幂等。
 */
(function () {
  "use strict";
  function showTip(bar) {
    var tip = bar.querySelector(".share-tip");
    if (!tip) return;
    tip.hidden = false;
    setTimeout(function () {
      tip.hidden = true;
    }, 1500);
  }
  function fallbackCopy(text, bar) {
    var ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.top = "-9999px";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    try {
      document.execCommand("copy");
      showTip(bar);
    } catch (e) {
      /* 复制失败静默 */
    }
    document.body.removeChild(ta);
  }
  function initBar(bar) {
    if (bar.dataset.init === "1") return;
    bar.dataset.init = "1";
    // 每期播客卡片可带 data-share-url 指向锚点链接（如 /podcast/#ep002），
    // 无则回退整页 URL —— 文章页兼容不变。
    var url = bar.dataset.shareUrl || window.location.href;
    var qrBox = bar.querySelector(".share-qr-code");
    if (qrBox && typeof qrcode === "function") {
      try {
        var qr = qrcode(0, "M");
        qr.addData(url);
        qr.make();
        qrBox.innerHTML = qr.createImgTag(4, 8);
      } catch (e) {
        qrBox.innerHTML = "";
      }
    }
    var btn = bar.querySelector(".share-copy-btn");
    if (btn) {
      btn.addEventListener("click", function () {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard
            .writeText(url)
            .then(function () {
              showTip(bar);
            })
            .catch(function () {
              fallbackCopy(url, bar);
            });
        } else {
          fallbackCopy(url, bar);
        }
      });
    }
  }
  function initAll() {
    var bars = document.querySelectorAll(".share-bar");
    for (var i = 0; i < bars.length; i++) initBar(bars[i]);
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAll);
  } else {
    initAll();
  }
})();
