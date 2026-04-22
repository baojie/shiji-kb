/* 哈希路由。 */

import { resolvePageId } from './registry.js';
import { renderPage, renderHome, renderNotFound, renderCategory } from './renderer.js';
import { setStatus, showFatal } from './util.js';

export function setupRouter(core) {
  window.addEventListener('hashchange', () => route(core));
  route(core);
}

async function route(core) {
  // 先取原始 hash (未解码), 便于区分 '?query' 和普通 slug
  const rawHash = location.hash.slice(1) || '';
  setStatus('载入…');

  // 分类页: #?type=<type> 或 #?tag=<tag>
  if (rawHash.startsWith('?')) {
    const params = new URLSearchParams(rawHash.slice(1));
    const type = params.get('type');
    const tag = params.get('tag');
    if (type) { renderCategory(core, 'type', type); setStatus(''); return; }
    if (tag) { renderCategory(core, 'tag', tag); setStatus(''); return; }
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
    await renderPage(core, pid, meta, mdText);
    setStatus('');
  } catch (e) {
    showFatal(`加载 ${meta.path} 失败：${e.message}`);
  }
}
