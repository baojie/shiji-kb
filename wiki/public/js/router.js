/* 哈希路由。 */

import { resolvePageId } from './registry.js';
import {
  renderPage, renderHome, renderNotFound, renderCategory,
  renderRecent, renderHistory, renderRevision, renderAll, renderDiff,
  renderSource,
} from './renderer.js';
import { renderSpecialSettings, renderSpecialPlugins, renderSpecialAll, renderSpecialKnowledge } from './special.js';
import { setStatus, showFatal } from './util.js';

export function setupRouter(core) {
  window.addEventListener('hashchange', () => route(core));
  route(core);
}

async function route(core) {
  // 先取原始 hash (未解码), 便于区分 '?query' 和普通 slug
  const rawHash = location.hash.slice(1) || '';
  setStatus('载入…');

  // 特殊页: #?type=<type> · #?tag=<tag> · #?recent · #?history=<page> · #?revision=<page>&rev=<id>
  if (rawHash.startsWith('?')) {
    const params = new URLSearchParams(rawHash.slice(1));
    const type = params.get('type');
    const tag = params.get('tag');
    if (type) { renderCategory(core, 'type', type); setStatus(''); return; }
    if (tag) { renderCategory(core, 'tag', tag); setStatus(''); return; }
    if (params.has('all')) {
      renderAll(core);
      setStatus(''); return;
    }
    if (params.has('recent')) {
      const pageNum = parseInt(params.get('page') || '1', 10);
      try { await renderRecent(core, pageNum); } catch (e) { showFatal(`recent.json 加载失败：${e.message}`); }
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
  if (raw === 'Special:Settings') {
    renderSpecialSettings(core);
    setStatus(''); return;
  }
  if (raw === 'Special:Plugins') {
    renderSpecialPlugins(core);
    setStatus(''); return;
  }
  if (raw === 'Special:All') {
    renderSpecialAll(core);
    setStatus(''); return;
  }
  if (raw === 'Special:知识量') {
    renderSpecialKnowledge(core);
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

    // Redirect syntax: first non-empty line is "#REDIRECT [[目标]]"
    const firstLine = mdText.split('\n').find(l => l.trim());
    const redirectMatch = firstLine && firstLine.match(/^#REDIRECT\s+\[\[([^\]|]+)(?:\|[^\]]+)?\]\]/);
    if (redirectMatch) {
      const target = redirectMatch[1].trim();
      const targetResolved = resolvePageId(target, core.registry);
      if (targetResolved) {
        location.hash = encodeURIComponent(targetResolved[0]);
        setStatus('');
        return;
      }
    }

    await renderPage(core, pid, meta, mdText);
    setStatus('');
  } catch (e) {
    showFatal(`加载 ${meta.path} 失败：${e.message}`);
  }
}
