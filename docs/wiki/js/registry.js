/* 页面注册表加载与 id 解析。 */

export async function loadRegistry(url = 'pages.json') {
  const bust = `?v=${Math.floor(Date.now() / 60000)}`;
  const r = await fetch(url + bust);
  if (!r.ok) throw new Error(`pages.json HTTP ${r.status}`);
  return r.json();
}

/**
 * 路由/wikilink 的 id 解析:
 *   1. 精确匹配 pages[raw]
 *   2. 别名 alias_index[raw]
 *   3. 若 raw 带 "type/slug" 前缀, 取 slug 再按别名查 (兼容旧 slug 式)
 * @returns {[string, object] | null}  [pid, pageEntry] 或 null
 */
export function resolvePageId(raw, registry) {
  if (!raw) return null;
  if (raw in registry.pages) return [raw, registry.pages[raw]];
  if (raw in registry.alias_index) {
    const pid = registry.alias_index[raw];
    return [pid, registry.pages[pid]];
  }
  if (raw.includes('/')) {
    const tail = raw.split('/', 2)[1];
    if (tail in registry.pages) return [tail, registry.pages[tail]];
    if (tail in registry.alias_index) {
      const pid = registry.alias_index[tail];
      return [pid, registry.pages[pid]];
    }
  }
  return null;
}
