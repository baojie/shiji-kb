/* 页面 / 首页 / 404 / infobox 的 DOM 挂载。
 *
 * 解析逻辑 (frontmatter + MD + wikilink + hook) 全在 parser.js。
 * 本模块只把解析结果填到 DOM, 并管元数据/导航/状态栏。
 */

import { escapeHtml, TYPE_LABELS } from './util.js';
import { parseMarkdown } from './parser.js';

export async function renderPage(core, pid, meta, mdText) {
  const { front, html, broken } = await parseMarkdown(core, mdText, { pid, meta });

  document.getElementById('article').innerHTML = html;
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
  const ids = Object.keys(pages).sort();
  const items = ids.map((id) => {
    const p = pages[id];
    const t = TYPE_LABELS[p.type] || p.type || '';
    return `<li><span class="type-tag">${escapeHtml(t)}</span>` +
      `<a href="#${encodeURIComponent(id)}">${escapeHtml(p.label)}</a></li>`;
  }).join('');

  document.getElementById('article').innerHTML =
    `<h1>史记 Wiki <small>(v0 原型)</small></h1>
     <p>共 ${ids.length} 页。</p>
     <ul class="page-list">${items}</ul>`;
  const ib = document.getElementById('infobox');
  ib.hidden = true;
  ib.innerHTML = '';
  document.getElementById('crumb').textContent = '首页';
  document.title = '史记 Wiki';
  document.getElementById('src-info').textContent = 'pages.json';
  document.getElementById('broken-info').textContent = '';
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
