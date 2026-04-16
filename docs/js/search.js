// 史记知识库 — 静态全文检索（客户端）
// 同时为首页下拉搜索与 search.html 全部结果页提供底层能力。
// 首次使用时懒加载 data/search-index.json，按 AND 子串匹配段落。

(function () {
  const DROPDOWN_MAX = 30;
  const SNIPPET_RADIUS = 24;

  // ── 通用工具 ─────────────────────────────────────────
  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function escapeRegex(s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  function tokenize(q) {
    return q.trim().split(/\s+/).filter(Boolean);
  }

  // ── 索引加载（懒加载 + 缓存）─────────────────────────
  let indexPromise = null;
  let data = null;

  function indexUrl() {
    // 支持从子目录页面加载（例如 search.html 在 docs/ 根目录）
    const base = (typeof window !== 'undefined' && window.ShijiSearchBase) || '';
    return (base ? base.replace(/\/$/, '') + '/' : '') + 'data/search-index.json';
  }

  function loadIndex() {
    if (!indexPromise) {
      indexPromise = fetch(indexUrl())
        .then(function (r) {
          if (!r.ok) throw new Error('HTTP ' + r.status);
          return r.json();
        })
        .then(function (j) {
          data = j;
          data.chapterMap = {};
          for (let i = 0; i < data.chapters.length; i++) {
            data.chapterMap[data.chapters[i].n] = data.chapters[i];
          }
          return data;
        });
    }
    return indexPromise;
  }

  // ── 搜索（返回全部命中，不截断）──────────────────────
  function searchAll(query) {
    const tokens = tokenize(query);
    if (!tokens.length || !data) return { hits: [], tokens: [] };
    const lowered = tokens.map(function (t) { return t.toLowerCase(); });
    const entries = data.entries;
    const hits = [];
    for (let i = 0; i < entries.length; i++) {
      const e = entries[i];
      const hay = e.x.toLowerCase();
      let ok = true;
      for (let j = 0; j < lowered.length; j++) {
        if (hay.indexOf(lowered[j]) === -1) { ok = false; break; }
      }
      if (ok) hits.push(e);
    }
    return { hits: hits, tokens: tokens };
  }

  // ── 片段生成 + 高亮 ──────────────────────────────────
  function makeSnippet(text, tokens, radius) {
    radius = radius || SNIPPET_RADIUS;
    let pos = -1, matched = '';
    const lower = text.toLowerCase();
    for (let i = 0; i < tokens.length; i++) {
      const t = tokens[i].toLowerCase();
      const p = lower.indexOf(t);
      if (p !== -1 && (pos === -1 || p < pos)) { pos = p; matched = t; }
    }
    if (pos === -1) return escapeHtml(text.slice(0, 80));

    const start = Math.max(0, pos - radius);
    const end = Math.min(text.length, pos + matched.length + radius * 2);
    let snip = text.slice(start, end);
    if (start > 0) snip = '…' + snip;
    if (end < text.length) snip = snip + '…';

    let html = escapeHtml(snip);
    for (let i = 0; i < tokens.length; i++) {
      const t = tokens[i];
      if (!t) continue;
      const re = new RegExp(escapeRegex(t), 'gi');
      html = html.replace(re, function (m) { return '<mark>' + escapeHtml(m) + '</mark>'; });
    }
    return html;
  }

  // ── URL 构造 ────────────────────────────────────────
  function chapterUrl(ch, pid, basePrefix) {
    basePrefix = basePrefix || '';
    return basePrefix + 'chapters/' + encodeURIComponent(ch.f) + '.html#pn-' + encodeURIComponent(pid);
  }

  function searchPageUrl(query, basePrefix) {
    basePrefix = basePrefix || '';
    return basePrefix + 'search.html?q=' + encodeURIComponent(query);
  }

  // ── 导出 API ────────────────────────────────────────
  window.ShijiSearch = {
    loadIndex: loadIndex,
    searchAll: searchAll,
    makeSnippet: makeSnippet,
    chapterUrl: chapterUrl,
    searchPageUrl: searchPageUrl,
    escapeHtml: escapeHtml,
    getData: function () { return data; },
  };

  // ── 首页下拉行为（仅当相关 DOM 存在时激活）──────────
  const input = document.getElementById('shiji-search-input');
  const results = document.getElementById('shiji-search-results');
  if (!input || !results) return;

  let debounceTimer = null;

  function triggerLoad() {
    if (!indexPromise) {
      results.innerHTML = '<div class="ss-hint">正在加载索引…</div>';
      results.style.display = 'block';
    }
    return loadIndex().catch(function (err) {
      results.innerHTML = '<div class="ss-hint">索引加载失败：' +
        escapeHtml(String(err && err.message || err)) + '</div>';
      indexPromise = null;
    });
  }

  function render(query) {
    if (!data) return;
    const q = query.trim();
    if (!q) {
      results.style.display = 'none';
      results.innerHTML = '';
      return;
    }
    const r = searchAll(q);
    if (!r.hits.length) {
      results.innerHTML = '<div class="ss-hint">未找到「' + escapeHtml(q) + '」</div>';
      results.style.display = 'block';
      return;
    }

    const total = r.hits.length;
    const shown = Math.min(total, DROPDOWN_MAX);
    const parts = [];
    parts.push('<div class="ss-summary">找到 ' + total +
      ' 个段落' + (total > shown ? '（显示前 ' + shown + '）' : '') + '</div>');

    for (let i = 0; i < shown; i++) {
      const h = r.hits[i];
      const ch = data.chapterMap[h.c];
      if (!ch) continue;
      const num = String(ch.n).padStart(3, '0');
      const url = chapterUrl(ch, h.p);
      parts.push(
        '<a class="ss-hit" href="' + url + '">' +
          '<span class="ss-ch">' + num + '·' + escapeHtml(ch.t) + ' · ' + escapeHtml(h.p) + '</span>' +
          '<span class="ss-snip">' + makeSnippet(h.x, r.tokens) + '</span>' +
        '</a>'
      );
    }

    if (total > shown) {
      parts.push(
        '<a class="ss-more" href="' + searchPageUrl(q) + '">' +
          '查看全部 ' + total + ' 个结果 →' +
        '</a>'
      );
    }

    results.innerHTML = parts.join('');
    results.style.display = 'block';
  }

  input.addEventListener('focus', triggerLoad);

  input.addEventListener('input', function () {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(function () {
      if (data) render(input.value);
      else triggerLoad().then(function () { if (data) render(input.value); });
    }, 120);
  });

  input.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') {
      const q = input.value.trim();
      if (q) {
        e.preventDefault();
        window.location.href = searchPageUrl(q);
      }
    } else if (e.key === 'Escape') {
      input.value = '';
      results.style.display = 'none';
      results.innerHTML = '';
      input.blur();
    }
  });

  document.addEventListener('click', function (e) {
    if (!results.contains(e.target) && e.target !== input) {
      results.style.display = 'none';
    }
  });

  input.addEventListener('focus', function () {
    if (data && input.value.trim()) results.style.display = 'block';
  });
})();
