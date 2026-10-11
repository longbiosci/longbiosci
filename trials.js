/* 临床试验数据库 —— tab 切换
   原页面的 showTab() 依赖隐式全局 event.target（脆弱、无法键盘操作、
   刷新后丢失状态）。这里改为事件绑定 + URL hash 同步 + 键盘方向键。
*/
(function () {
  'use strict';

  var tabs = Array.prototype.slice.call(
    document.querySelectorAll('.tr-tab'));
  if (!tabs.length) return;

  function select(id, focus) {
    var hit = false;
    tabs.forEach(function (t) {
      var on = t.getAttribute('data-tab') === id;
      if (on) hit = true;
      t.setAttribute('aria-selected', on ? 'true' : 'false');
      var panel = document.getElementById('panel-' + t.getAttribute('data-tab'));
      if (panel) panel.classList.toggle('active', on);
      if (on && focus) t.focus();
    });
    return hit;
  }

  tabs.forEach(function (t) {
    t.addEventListener('click', function () {
      var id = t.getAttribute('data-tab');
      select(id);
      // 同步到 hash：便于分享具体分类，也支持浏览器前进/后退
      if (history.replaceState) history.replaceState(null, '', '#' + id);
    });
  });

  // 键盘可达：左右方向键在 tab 间移动（符合 WAI-ARIA tab 模式）
  tabs.forEach(function (t, i) {
    t.addEventListener('keydown', function (e) {
      var d = e.key === 'ArrowRight' ? 1 : (e.key === 'ArrowLeft' ? -1 : 0);
      if (!d) return;
      e.preventDefault();
      var next = tabs[(i + d + tabs.length) % tabs.length];
      select(next.getAttribute('data-tab'), true);
    });
  });

  // 支持 trials.html#nmn 直达
  var h = (location.hash || '').replace('#', '');
  if (h) select(h);
})();