/* 哈希路由。 */

import { resolvePageId } from './registry.js';
import {
  renderPage, renderHome, renderNotFound, renderCategory,
  renderRecent, renderHistory, renderRevision, renderAll, renderDiff,
  renderSource,
} from './renderer.js';
import { renderSpecialSettings, renderSpecialPlugins, renderSpecialAll, renderSpecialStatistics } from './special.js';
import { setStatus, showFatal, escapeHtml } from './util.js';

export function setupRouter(core) {
  window.addEventListener('hashchange', () => route(core));
  route(core);
}

async function route(core) {
  // 先取原始 hash (未解码), 便于区分 '?query' 和普通 slug
  const rawHash = location.hash.slice(1) || '';

  // 页内锚点（如脚注 #fn1 / #fnref1）：目标元素已在 DOM 中，直接滚动，不做页面路由
  if (rawHash && !rawHash.startsWith('?')) {
    const el = document.getElementById(decodeURIComponent(rawHash));
    if (el) {
      const id = decodeURIComponent(rawHash);
      const isBackref = id.startsWith('fnref');
      const navH = document.querySelector('.topnav')?.offsetHeight ?? 0;
      if (isBackref) {
        // 回跳到行内引用：找最近块级祖先，顶部对齐并留出 nav 高度
        const BLOCK = new Set(['P','LI','TD','TH','H1','H2','H3','H4','H5','H6','BLOCKQUOTE','DIV','SECTION']);
        let block = el.parentElement;
        while (block && !BLOCK.has(block.tagName)) block = block.parentElement;
        const target = block || el;
        const top = target.getBoundingClientRect().top + window.scrollY - navH - 8;
        window.scrollTo({ top, behavior: 'smooth' });
      } else {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
      setStatus('');
      return;
    }
  }

  setStatus('载入…');

  // 特殊页: #?type=<type> · #?tag=<tag> · #?recent · #?history=<page> · #?revision=<page>&rev=<id>
  if (rawHash.startsWith('?')) {
    const params = new URLSearchParams(rawHash.slice(1));
    const type = params.get('type');
    const tag = params.get('tag');
    if (type) { renderCategory(core, 'type', type); setStatus(''); return; }
    if (tag) { renderCategory(core, 'tag', tag); setStatus(''); return; }
    if (params.has('all')) {
      location.hash = encodeURIComponent('Special:AllPages');
      setStatus(''); return;
    }
    if (params.has('recent')) {
      // 旧 URL 兼容：直接渲染，不做 redirect（避免 hashchange 不触发的问题）
      const pageNum = parseInt(params.get('page') || '1', 10);
      try { await renderRecent(core, pageNum); } catch (e) { showFatal(`recent.jsonl 加载失败：${e.message}`); }
      setStatus(''); return;
    }
    if (params.has('history')) {
      const page = params.get('history');
      try { await renderHistory(core, page); }
      catch (e) { showFatal(`history/${page}.json 加载失败：${e.message}`); }
      setStatus(''); return;
    }
    if (params.has('diff')) {
      const page = params.get('diff');
      const rev = params.get('rev');
      try { await renderDiff(core, page, rev); }
      catch (e) { showFatal(`diff ${page} @ ${rev} 失败：${e.message}`); }
      setStatus(''); return;
    }
    if (params.has('revision')) {
      const page = params.get('revision');
      const rev = params.get('rev');
      try { await renderRevision(core, page, rev); }
      catch (e) { showFatal(`history/${page}.json#${rev} 加载失败：${e.message}`); }
      setStatus(''); return;
    }
    if (params.has('source')) {
      const page = params.get('source');
      const resolved = resolvePageId(page, core.registry);
      if (!resolved) { renderNotFound(core, page); setStatus(''); return; }
      const [pid, meta] = resolved;
      try { await renderSource(core, pid, meta); }
      catch (e) { showFatal(`源码加载失败：${e.message}`); }
      setStatus(''); return;
    }
  }

  let raw = decodeURIComponent(rawHash);

  // Plugin hook: 自定义路由
  //   handler 返回 null  → 表示"已自行处理", 跳过默认路由
  //   handler 返回 string → 改写 raw
  //   handler 返回 undefined → 保持原值
  const mutated = await core.hooks.onRoute.run(raw, core);
  if (mutated === null) {
    setStatus('');
    return;
  }
  if (typeof mutated === 'string') raw = mutated;

  if (!raw) {
    renderHome(core);
    setStatus('');
    return;
  }

  // Special: 系统页路由
  if (raw === 'Special:Random') {
    const pids = Object.keys(core.registry.pages).filter(
      p => !p.startsWith('Special:') && core.registry.pages[p].type !== 'chapter'
    );
    const randomPid = pids[Math.floor(Math.random() * pids.length)];
    location.hash = encodeURIComponent(randomPid);
    setStatus('');
    return;
  }
  if (raw === 'Special:Recent' || raw.startsWith('Special:Recent?')) {
    const qm = raw.indexOf('?');
    const pageNum = qm >= 0 ? parseInt(new URLSearchParams(raw.slice(qm + 1)).get('page') || '1', 10) : 1;
    try { await renderRecent(core, pageNum); } catch (e) { showFatal(`recent.jsonl 加载失败：${e.message}`); }
    setStatus(''); return;
  }
  if (raw === 'Special:Settings') {
    renderSpecialSettings(core);
    setStatus(''); return;
  }
  if (raw === 'Special:Plugins') {
    renderSpecialPlugins(core);
    setStatus(''); return;
  }
  if (raw === 'Special:AllPages' || raw.startsWith('Special:AllPages?')) {
    renderAll(core);
    setStatus(''); return;
  }
  if (raw === 'Special:All') {
    renderSpecialAll(core);
    setStatus(''); return;
  }
  if (raw === 'Special:Statistics' || raw === 'Special:知识量') {
    renderSpecialStatistics(core);
    setStatus(''); return;
  }

  // 动态 Special 页：由插件通过 core.registerSpecialPage() 注册
  const dynPage = core.specialPages.find(
    p => raw === p.id || raw.startsWith(p.id + '?')
  );
  if (dynPage?.render) {
    const params = raw.includes('?') ? new URLSearchParams(raw.slice(raw.indexOf('?') + 1)) : new URLSearchParams();
    try { await dynPage.render(core, params); } catch (e) { showFatal(`${dynPage.id} 渲染失败：${e.message}`); }
    setStatus(''); return;
  }

  const resolved = resolvePageId(raw, core.registry);
  if (!resolved) {
    renderNotFound(core, raw);
    setStatus('');
    return;
  }

  const [pid, meta] = resolved;
  try {
    const r = await fetch(meta.path);
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const mdText = await r.text();

    // Redirect syntax: "#REDIRECT [[目标]]" or "REDIRECT [[目标]]" in body (skip frontmatter)
    const bodyText = mdText.replace(/^---\n[\s\S]*?\n---\n?/, '');
    const firstBodyLine = bodyText.split('\n').find(l => l.trim());
    const redirectMatch = firstBodyLine && firstBodyLine.match(/^#?REDIRECT\s+\[\[([^\]|]+)(?:\|[^\]]+)?\]\]/);
    if (redirectMatch) {
      const target = redirectMatch[1].trim();
      const targetResolved = resolvePageId(target, core.registry);
      // 渲染重定向页（含修订历史），不自动跳转
      const label = meta.label || pid;
      const strippedMd = mdText.replace(/^#?REDIRECT\s+\[\[[^\]]+\]\]\s*/m, `# ${label}\n`);
      await renderPage(core, pid, meta, strippedMd);
      const targetLink = targetResolved
        ? `<a href="#${encodeURIComponent(targetResolved[0])}">${escapeHtml(target)}</a>`
        : `<span class="broken-link">${escapeHtml(target)}</span>`;
      const notice = document.createElement('div');
      notice.className = 'redirect-notice';
      notice.innerHTML = `<span class="redirect-arrow">⇒</span> 重定向至 ${targetLink}`;
      const article = document.getElementById('article');
      const h1 = article.querySelector('h1');
      if (h1) h1.after(notice); else article.prepend(notice);
      setStatus('');
      return;
    }

    await renderPage(core, pid, meta, mdText);
    setStatus('');
  } catch (e) {
    showFatal(`加载 ${meta.path} 失败：${e.message}`);
  }
}
