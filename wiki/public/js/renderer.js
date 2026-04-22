/* 页面 / 首页 / 404 / infobox 的 DOM 挂载。
 *
 * 解析逻辑 (frontmatter + MD + wikilink + hook) 全在 parser.js。
 * 本模块只把解析结果填到 DOM, 并管元数据/导航/状态栏。
 */

import { escapeHtml, TYPE_LABELS } from './util.js';
import { parseMarkdown } from './parser.js';

export async function renderPage(core, pid, meta, mdText) {
  document.body.classList.remove('is-home');
  const { front, html, broken } = await parseMarkdown(core, mdText, { pid, meta });

  const tagsFooter = renderTagsFooter(front, meta);
  document.getElementById('article').innerHTML = html + tagsFooter;
  const infoboxHtml = await renderInfobox(core, front, meta);
  document.getElementById('infobox').outerHTML = infoboxHtml;

  const label = front.label || meta.label;
  document.getElementById('crumb').textContent =
    (TYPE_LABELS[meta.type] || meta.type) + ' / ' + label;
  document.title = label + ' · 史记 Wiki';
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

export async function renderInfobox(core, front, meta) {
  let rows = [];
  const push = (k, v) => {
    if (v != null && v !== '') {
      rows.push(`<tr><th>${escapeHtml(k)}</th><td>${v}</td></tr>`);
    }
  };

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

  // Plugin hook: 允许改写 infobox 行
  rows = await core.hooks.onInfobox.run(rows, front, meta);

  if (!rows.length) {
    return '<aside class="infobox" id="infobox" hidden></aside>';
  }
  return `<aside class="infobox" id="infobox">
    <h2>${escapeHtml(front.label || meta.label)}</h2>
    <table>${rows.join('')}</table>
  </aside>`;
}

export function renderHome(core) {
  const pages = core.registry.pages;
  const ids = Object.keys(pages);

  // 代表人物: 按 total_refs 降序取 top 6, 缺此字段则按 id 序
  const hasRefs = ids.some((id) => pages[id].total_refs != null);
  const featured = ids
    .map((id) => ({ id, ...pages[id] }))
    .sort((a, b) => {
      if (hasRefs) return (b.total_refs || 0) - (a.total_refs || 0);
      return a.id.localeCompare(b.id, 'zh');
    })
    .slice(0, 6);

  const featuredHtml = featured.map(renderFeaturedCard).join('');

  const allItems = ids.slice().sort((a, b) => a.localeCompare(b, 'zh'))
    .map((id) => {
      const p = pages[id];
      const t = TYPE_LABELS[p.type] || p.type || '';
      const meta = p.total_refs != null
        ? ` <span class="list-meta">${p.total_refs} 次 / ${p.total_chapters} 篇</span>`
        : '';
      return `<li><span class="type-tag">${escapeHtml(t)}</span>` +
        `<a href="#${encodeURIComponent(id)}">${escapeHtml(p.label)}</a>${meta}</li>`;
    }).join('');

  document.getElementById('article').innerHTML =
    `<div class="wiki-home">
      <h1>史记 Wiki</h1>
      <p class="tagline">从 130 篇《史记》提取的 ${ids.length} 个实体页面, 可按姓名或别名搜索</p>

      <div class="search-box">
        <input id="wiki-search" type="search"
          placeholder="搜索人名或别名 (如 '刘邦', '高祖', '沛公')"
          autocomplete="off" autofocus>
        <ul id="search-results" hidden></ul>
      </div>

      <h2>代表人物</h2>
      <div class="featured-grid">${featuredHtml}</div>

      <details class="all-pages">
        <summary>全部 ${ids.length} 页</summary>
        <ul class="page-list">${allItems}</ul>
      </details>
    </div>`;

  document.body.classList.add('is-home');
  const ib = document.getElementById('infobox');
  ib.hidden = true;
  ib.innerHTML = '';
  document.getElementById('crumb').textContent = '首页';
  document.title = '史记 Wiki';
  document.getElementById('src-info').textContent = 'pages.json';
  document.getElementById('broken-info').textContent = '';

  // 搜索交互
  const input = document.getElementById('wiki-search');
  const resultsEl = document.getElementById('search-results');
  input.addEventListener('input', () => {
    const q = input.value.trim();
    if (!q) {
      resultsEl.hidden = true; resultsEl.innerHTML = ''; return;
    }
    const matches = searchPages(q, core.registry);
    resultsEl.hidden = false;
    if (matches.length === 0) {
      resultsEl.innerHTML =
        `<li class="search-empty">没有匹配: "${escapeHtml(q)}"</li>`;
      return;
    }
    resultsEl.innerHTML = matches.map((m) => {
      const labelHtml = escapeHtml(m.entry.label);
      const altHtml = m.matched !== m.entry.label
        ? `<span class="match-alt">[${escapeHtml(m.matched)}]</span>` : '';
      const meta = m.entry.total_refs != null
        ? `<span class="match-meta">${m.entry.total_refs} 次 / ${m.entry.total_chapters} 篇</span>`
        : '';
      return `<li class="search-result-item">
        <a href="#${encodeURIComponent(m.pid)}">
          <span class="match-label">${labelHtml}</span>${altHtml}${meta}
        </a>
      </li>`;
    }).join('');
  });
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      const first = resultsEl.querySelector('a');
      if (first) location.hash = first.getAttribute('href').slice(1);
    } else if (e.key === 'Escape') {
      input.value = ''; resultsEl.hidden = true; resultsEl.innerHTML = '';
    }
  });
}

/**
 * 每页底部分类标签 (语义化):
 *   <footer class="entity-tags" role="contentinfo">
 *     <a class="tag tag-type" rel="tag">人名</a>
 *     <a class="tag" rel="tag">汉朝</a>...
 *   </footer>
 *
 * 来源:
 *   - type (frontmatter.type 或 meta.type): 主分类, 显示为突出样式
 *   - tags[]: 自由标签
 *
 * rel="tag" 是 HTML5 microformats 的标签链接关系, 搜索引擎和
 * 阅读器可识别. href 指向 "#?tag=<name>"; 未来可加 tag 路由.
 */
function renderTagsFooter(front, meta) {
  const type = front.type || meta.type || '';
  const typeLabel = TYPE_LABELS[type] || type;
  const tags = front.tags || [];
  if (!typeLabel && tags.length === 0) return '';

  const parts = [];
  if (typeLabel) {
    parts.push(
      `<a class="tag tag-type" rel="tag" data-kind="type"` +
      ` href="#?type=${encodeURIComponent(type)}">${escapeHtml(typeLabel)}</a>`
    );
  }
  for (const tag of tags) {
    parts.push(
      `<a class="tag" rel="tag" data-kind="tag"` +
      ` href="#?tag=${encodeURIComponent(tag)}">${escapeHtml(tag)}</a>`
    );
  }
  return `<footer class="entity-tags" role="contentinfo" aria-label="分类">
    <span class="tag-label">分类</span>
    ${parts.join(' ')}
  </footer>`;
}

function renderFeaturedCard(p) {
  const life = p.lifespan || null;
  let lifeS = '';
  if (life && life.birth != null && life.death != null) {
    const b = life.birth < 0 ? `前 ${-life.birth}` : String(life.birth);
    const d = life.death < 0 ? `前 ${-life.death}` : String(life.death);
    lifeS = `<div class="card-life">${b} — ${d}</div>`;
  }
  const meta = p.total_refs != null
    ? `<div class="card-meta">
         <strong>${p.total_refs}</strong> 次出现 ·
         <strong>${p.total_chapters}</strong> 篇
       </div>` : '';
  const aliasPreview = (p.aliases || []).slice(0, 3).join(' · ');
  const aliasHtml = aliasPreview
    ? `<div class="card-aliases">${escapeHtml(aliasPreview)}</div>` : '';
  return `<a class="featured-card" href="#${encodeURIComponent(p.id)}">
    <h3>${escapeHtml(p.label)}</h3>
    ${lifeS}${meta}${aliasHtml}
  </a>`;
}

function searchPages(q, registry) {
  const lower = q.toLowerCase();
  const matched = new Map(); // pid → 命中的 surface
  for (const [pid, entry] of Object.entries(registry.pages)) {
    if (pid.toLowerCase().includes(lower)) matched.set(pid, pid);
    else if (entry.label && entry.label.toLowerCase().includes(lower)) {
      matched.set(pid, entry.label);
    }
  }
  for (const [alias, pid] of Object.entries(registry.alias_index || {})) {
    if (matched.has(pid)) continue;
    if (alias.toLowerCase().includes(lower)) matched.set(pid, alias);
  }
  return [...matched.entries()]
    .slice(0, 15)
    .map(([pid, matched]) => ({ pid, entry: registry.pages[pid], matched }));
}

/**
 * 分类页 (类 MediaWiki Category): 列出某 type/tag 下的所有页面.
 *   URL: #?type=<type>  或  #?tag=<tag>
 */
export function renderCategory(core, kind, value) {
  const pages = core.registry.pages;
  const matches = [];
  for (const [pid, entry] of Object.entries(pages)) {
    if (kind === 'type' && entry.type === value) {
      matches.push({ pid, ...entry });
    } else if (kind === 'tag' && (entry.tags || []).includes(value)) {
      matches.push({ pid, ...entry });
    }
  }
  // refs 降序, 无 refs 按 id
  matches.sort((a, b) => {
    const ra = a.total_refs || 0, rb = b.total_refs || 0;
    if (ra !== rb) return rb - ra;
    return a.pid.localeCompare(b.pid, 'zh');
  });

  const titleKind = kind === 'type' ? '类型' : '标签';
  const displayValue = kind === 'type'
    ? (TYPE_LABELS[value] || value) : value;

  const itemsHtml = matches.map((p) => {
    const life = p.lifespan;
    let lifeS = '';
    if (life && life.birth != null && life.death != null) {
      const b = life.birth < 0 ? `前 ${-life.birth}` : String(life.birth);
      const d = life.death < 0 ? `前 ${-life.death}` : String(life.death);
      lifeS = `<span class="cat-life">${b}—${d}</span>`;
    }
    const meta = p.total_refs != null
      ? `<span class="cat-meta">${p.total_refs} 次 / ${p.total_chapters} 篇</span>` : '';
    return `<li>
      <a href="#${encodeURIComponent(p.pid)}" class="cat-link">${escapeHtml(p.label)}</a>
      ${lifeS}${meta}
    </li>`;
  }).join('');

  const body = matches.length > 0
    ? `<ol class="category-list">${itemsHtml}</ol>`
    : '<p class="category-empty">此分类下暂无页面。</p>';

  document.getElementById('article').innerHTML =
    `<nav class="category-crumb"><a href="#">← 首页</a></nav>
     <h1>${escapeHtml(titleKind)}：${escapeHtml(displayValue)}</h1>
     <p class="category-summary">共 <strong>${matches.length}</strong> 个页面</p>
     ${body}`;

  document.body.classList.add('is-home');
  const ib = document.getElementById('infobox');
  ib.hidden = true;
  ib.innerHTML = '';
  document.getElementById('crumb').textContent = `${titleKind}：${displayValue}`;
  document.title = `${titleKind} ${displayValue} · 史记 Wiki`;
  document.getElementById('src-info').textContent =
    `pages.json (筛选: ${kind}=${value})`;
  document.getElementById('broken-info').textContent = '';
  window.scrollTo(0, 0);
}

export function renderNotFound(core, target) {
  document.getElementById('article').innerHTML =
    `<h1>页面不存在</h1>
     <p>未找到页面 <code>${escapeHtml(target)}</code>。</p>
     <p><a href="#">回到首页</a></p>`;
  const ib = document.getElementById('infobox');
  ib.hidden = true;
  ib.innerHTML = '';
  document.getElementById('crumb').textContent = '未找到';
  document.title = '未找到 · 史记 Wiki';
  document.getElementById('src-info').textContent = '';
  document.getElementById('broken-info').textContent = '';
}
