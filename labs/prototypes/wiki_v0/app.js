/* 史记 Wiki v0 · 浏览器端渲染器
 *
 * 运行时流程:
 *   1. fetch pages.json  → 注册表 (id→meta, alias→id)
 *   2. 监听 hashchange   → 路由
 *   3. 路由: fetch 当前页的 .md → 解析 frontmatter → MD→HTML → wikilink 替换 → 挂载
 *
 * 依赖 (全局): markdownit, jsyaml
 */

'use strict';

const TYPE_LABELS = {
  person: '人名', place: '地名', state: '邦国', official: '官职',
  identity: '身份', dynasty: '朝代', event: '事件', chapter: '章节',
  topic: '主题', meta: '元页',
};

// Unicode 私用区占位符, 用来在 MD 渲染前保护 [[...]] 避免表格 | 冲突
const PH_OPEN = '\uE010';
const PH_CLOSE = '\uE011';
const WIKILINK_RE = /\[\[([^\[\]|]+?)(?:\|([^\[\]]+?))?\]\]/g;
const PH_RE = /\uE010(\d+)\uE011/g;
const FRONTMATTER_RE = /^---\s*\n([\s\S]*?)\n---\s*\n/;

const state = {
  registry: null,
  md: null,
};

// ---------- 启动 ----------
async function boot() {
  state.md = window.markdownit({
    html: false, linkify: true, typographer: true, breaks: false,
  });

  try {
    const r = await fetch('pages.json');
    state.registry = await r.json();
  } catch (e) {
    showFatal('无法加载 pages.json：' + e.message);
    return;
  }

  window.addEventListener('hashchange', route);
  route();
}

// ---------- 路由 ----------
async function route() {
  const raw = decodeURIComponent(location.hash.slice(1) || '');
  setStatus('载入…');
  if (!raw) {
    renderHome();
    setStatus('');
    return;
  }
  const pageEntry = resolvePageId(raw);
  if (!pageEntry) {
    renderNotFound(raw);
    setStatus('');
    return;
  }
  const [pid, meta] = pageEntry;
  try {
    const mdText = await fetch(meta.path).then((r) => {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.text();
    });
    renderPage(pid, meta, mdText);
    setStatus('');
  } catch (e) {
    showFatal(`加载 ${meta.path} 失败：${e.message}`);
  }
}

function resolvePageId(raw) {
  if (raw in state.registry.pages) return [raw, state.registry.pages[raw]];
  if (raw in state.registry.alias_index) {
    const pid = state.registry.alias_index[raw];
    return [pid, state.registry.pages[pid]];
  }
  if (raw.includes('/')) {
    const tail = raw.split('/', 2)[1];
    if (tail in state.registry.alias_index) {
      const pid = state.registry.alias_index[tail];
      return [pid, state.registry.pages[pid]];
    }
  }
  return null;
}

// ---------- 渲染 ----------
function renderPage(pid, meta, mdText) {
  const {front, body} = splitFrontmatter(mdText);

  // 1. 保护 wikilink
  const {protectedText, tokens} = protectWikilinks(body);

  // 2. MD → HTML
  let html = state.md.render(protectedText);

  // 3. 展开 wikilink
  const broken = [];
  html = expandWikilinks(html, tokens, pid, broken);

  // 4. 挂载
  document.getElementById('article').innerHTML = html;
  document.getElementById('infobox').outerHTML = renderInfobox(front, meta);
  document.getElementById('crumb').textContent =
    (TYPE_LABELS[meta.type] || meta.type) + ' / ' + (front.label || meta.label);
  document.title = (front.label || meta.label) + ' · 史记 Wiki';
  document.getElementById('src-info').textContent = '源: ' + meta.path;

  const brokenInfo = document.getElementById('broken-info');
  if (broken.length) {
    const uniq = [...new Set(broken)].sort();
    brokenInfo.innerHTML = ` · 断链 ${uniq.length}：` +
      uniq.map((b) => `<code>${escapeHtml(b)}</code>`).join(' ');
  } else {
    brokenInfo.textContent = '';
  }

  window.scrollTo(0, 0);
}

function renderHome() {
  const pages = state.registry.pages;
  const ids = Object.keys(pages).sort();
  const items = ids.map((id) => {
    const p = pages[id];
    const t = TYPE_LABELS[p.type] || p.type;
    return `<li><span class="type-tag">${escapeHtml(t)}</span>
      <a href="#${encodeURIComponent(id)}">${escapeHtml(p.label)}</a></li>`;
  }).join('');
  document.getElementById('article').innerHTML =
    `<h1>史记 Wiki <small>(v0 原型)</small></h1>
     <p>共 ${ids.length} 页。</p>
     <ul class="page-list">${items}</ul>`;
  document.getElementById('infobox').hidden = true;
  document.getElementById('crumb').textContent = '首页';
  document.title = '史记 Wiki';
  document.getElementById('src-info').textContent = 'pages.json';
  document.getElementById('broken-info').textContent = '';
}

function renderNotFound(target) {
  document.getElementById('article').innerHTML =
    `<h1>页面不存在</h1>
     <p>未找到页面 <code>${escapeHtml(target)}</code>。</p>
     <p><a href="#">回到首页</a></p>`;
  document.getElementById('infobox').hidden = true;
  document.getElementById('crumb').textContent = '未找到';
  document.title = '未找到 · 史记 Wiki';
}

// ---------- Infobox ----------
function renderInfobox(front, meta) {
  const rows = [];
  const push = (k, v) => v != null && v !== '' && rows.push(
    `<tr><th>${escapeHtml(k)}</th><td>${v}</td></tr>`);

  if (front.canonical_name && front.canonical_name !== (front.label || meta.label)) {
    push('规范名', escapeHtml(front.canonical_name));
  }
  if (front.aliases && front.aliases.length) {
    push('别名', front.aliases.map(escapeHtml).join(' · '));
  }
  push('类型', TYPE_LABELS[front.type || meta.type] || front.type || meta.type);
  if (front.birth_ce != null) {
    push('生', front.birth_ce < 0 ? `前 ${-front.birth_ce}` : String(front.birth_ce));
  }
  if (front.death_ce != null) {
    push('卒', front.death_ce < 0 ? `前 ${-front.death_ce}` : String(front.death_ce));
  }
  if (front.tags && front.tags.length) {
    push('标签', front.tags.map(escapeHtml).join(' · '));
  }

  if (!rows.length) {
    return '<aside class="infobox" id="infobox" hidden></aside>';
  }
  return `<aside class="infobox" id="infobox">
    <h2>${escapeHtml(front.label || meta.label)}</h2>
    <table>${rows.join('')}</table>
  </aside>`;
}

// ---------- Frontmatter ----------
function splitFrontmatter(text) {
  const m = FRONTMATTER_RE.exec(text);
  if (!m) return {front: {}, body: text};
  try {
    const front = window.jsyaml.load(m[1]) || {};
    return {front, body: text.slice(m[0].length)};
  } catch (e) {
    console.warn('frontmatter 解析失败:', e);
    return {front: {}, body: text};
  }
}

// ---------- Wikilink ----------
function protectWikilinks(body) {
  const tokens = [];
  const protectedText = body.replace(WIKILINK_RE, (_, target, text) => {
    tokens.push({target: target.trim(), text: text ? text.trim() : null});
    return PH_OPEN + (tokens.length - 1) + PH_CLOSE;
  });
  return {protectedText, tokens};
}

function expandWikilinks(html, tokens, selfId, brokenOut) {
  return html.replace(PH_RE, (_, idxStr) => {
    const {target, text} = tokens[+idxStr];
    let display = text != null ? text : target;
    if (text == null && display.includes('/')) {
      display = display.split('/', 2)[1];
    }
    const resolved = resolvePageId(target);
    if (!resolved) {
      brokenOut.push(target);
      return `<a class="wikilink broken" data-target="${escapeAttr(target)}"
        title="未解析: ${escapeAttr(target)}">${escapeHtml(display)}</a>`;
    }
    const [pid] = resolved;
    const cls = pid === selfId ? 'wikilink self' : 'wikilink resolved';
    return `<a class="${cls}" href="#${encodeURIComponent(pid)}">${escapeHtml(display)}</a>`;
  });
}

// ---------- 工具 ----------
function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) =>
    ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
}
function escapeAttr(s) { return escapeHtml(s); }

function setStatus(msg) {
  document.getElementById('status').textContent = msg;
}
function showFatal(msg) {
  document.getElementById('article').innerHTML =
    `<h1>错误</h1><p class="error">${escapeHtml(msg)}</p>`;
  setStatus('');
}

// ---------- 启动 ----------
boot();
