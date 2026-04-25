/**
 * semantic-query — ::: query 块渲染插件
 *
 * 职责：
 *   onAfterRender  从 core.semanticBlock 取缓存，展开 query 占位符为 HTML 表格/列表
 *
 * 依赖 semantic-block 插件（需先注册，以确保 _cache 在 onBeforeRender 时填充）。
 *
 * query 块支持的参数：
 *   过滤：type / tags / featured / total_refs_min 等（精确相等 + _min/_max 范围）
 *   布尔：tags_any:[a,b]  tags_not:[a,b]  type_any:[a,b]
 *   计算：computed:{key: expr}  （表达式变量为 registry 字段名）
 *   显示：sort / order / limit / display / fields / field_labels / title
 */

const PLUGIN_NAME = 'semantic-query';

function esc(s) {
  return String(s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ---------- 表达式求值器 ----------

function tokenizeExpr(expr) {
  const tokens = [];
  let i = 0;
  while (i < expr.length) {
    if (/\s/.test(expr[i])) { i++; continue; }
    if ('+-*/()'.includes(expr[i])) { tokens.push(expr[i++]); continue; }
    let j = i;
    while (j < expr.length && /[\w.]/.test(expr[j])) j++;
    if (j > i) { tokens.push(expr.slice(i, j)); i = j; continue; }
    i++;
  }
  return tokens;
}

export function evalExpr(expr, vars) {
  const tokens = tokenizeExpr(String(expr));
  let pos = 0;
  const peek = () => tokens[pos];
  const consume = () => tokens[pos++];

  function parsePrimary() {
    const t = consume();
    if (t === '(') { const v = parseAddSub(); consume(); return v; }
    const n = Number(t);
    if (!isNaN(n) && t !== undefined) return n;
    const v = vars[t];
    return (v == null) ? null : typeof v === 'number' ? v : Number(v);
  }
  function parseUnary() {
    if (peek() === '-') { consume(); const v = parsePrimary(); return v == null ? null : -v; }
    return parsePrimary();
  }
  function parseMulDiv() {
    let l = parseUnary();
    while (peek() === '*' || peek() === '/') {
      const op = consume(); const r = parseUnary();
      if (l == null || r == null) { l = null; continue; }
      l = op === '*' ? l * r : r !== 0 ? l / r : null;
    }
    return l;
  }
  function parseAddSub() {
    let l = parseMulDiv();
    while (peek() === '+' || peek() === '-') {
      const op = consume(); const r = parseMulDiv();
      if (l == null || r == null) { l = null; continue; }
      l = op === '+' ? l + r : l - r;
    }
    return l;
  }
  try { return parseAddSub(); } catch (_) { return null; }
}

// ---------- 查询引擎 ----------

const QUERY_SYSTEM_KEYS = new Set([
  'sort', 'order', 'limit', 'display', 'fields', 'title', 'field_labels', 'computed',
]);

const QUERY_BOOL_KEYS = new Set([
  'tags_any', 'tags_not', 'type_any',
]);

const QUERY_FIELD_LABELS = {
  label: '名称', type: '类型', tags: '标签',
  total_refs: '引用', total_chapters: '章节数',
  quality_score: '质量', featured: '精品',
  lifespan: '活跃期', birth_ce: '生', death_ce: '卒',
};

const QUERY_TYPE_LABELS = {
  person: '人物', place: '地名', state: '邦国', official: '官职',
  identity: '身份', dynasty: '朝代', event: '事件', chapter: '章节',
  topic: '主题', list: '列表', sanwen: '散文', story: '故事',
};

function executeQuery(meta, registry) {
  const allPages = Object.entries(registry.pages);

  const filtered = allPages.filter(([, page]) => {
    if (meta.tags_any) {
      const any = Array.isArray(meta.tags_any) ? meta.tags_any : [meta.tags_any];
      if (!any.some(t => (page.tags || []).includes(t))) return false;
    }
    if (meta.tags_not) {
      const not = Array.isArray(meta.tags_not) ? meta.tags_not : [meta.tags_not];
      if (not.some(t => (page.tags || []).includes(t))) return false;
    }
    if (meta.type_any) {
      const anyT = Array.isArray(meta.type_any) ? meta.type_any : [meta.type_any];
      if (!anyT.includes(page.type)) return false;
    }

    for (const [key, val] of Object.entries(meta)) {
      if (QUERY_SYSTEM_KEYS.has(key) || QUERY_BOOL_KEYS.has(key)) continue;
      if (key.endsWith('_min')) {
        const field = key.slice(0, -4);
        const n = page[field];
        if (typeof n !== 'number' || n < val) return false;
        continue;
      }
      if (key.endsWith('_max')) {
        const field = key.slice(0, -4);
        const n = page[field];
        if (typeof n !== 'number' || n > val) return false;
        continue;
      }
      const pageVal = page[key];
      if (Array.isArray(pageVal) && typeof val === 'string') {
        if (!pageVal.includes(val)) return false;
        continue;
      }
      if (pageVal !== val) return false;
    }
    return true;
  });

  const sortField = meta.sort || 'label';
  const order = meta.order === 'desc' ? -1 : 1;
  filtered.sort(([, a], [, b]) => {
    const av = a[sortField] ?? '';
    const bv = b[sortField] ?? '';
    if (typeof av === 'number' && typeof bv === 'number') return (av - bv) * order;
    return String(av).localeCompare(String(bv), 'zh') * order;
  });

  const limit = typeof meta.limit === 'number' ? meta.limit : 200;
  return filtered.slice(0, limit).map(([pid, page]) => ({ pid, ...page }));
}

function fmtQueryValue(key, v) {
  if (v == null || v === '') return '';
  if (key === 'type') return QUERY_TYPE_LABELS[v] || String(v);
  if (key === 'birth_ce' || key === 'death_ce') {
    if (typeof v !== 'number') return String(v);
    return v < 0 ? `前${-v}` : String(v);
  }
  if (Array.isArray(v)) return v.join(' · ');
  if (typeof v === 'boolean') return v ? '是' : '';
  if (typeof v === 'number') return String(v);
  return String(v);
}

function renderQueryBlock(meta, registry) {
  if (!registry) return '<p class="query-error">数据未加载</p>';

  const results = executeQuery(meta, registry);
  const display = meta.display || 'list';
  const titleHtml = meta.title ? `<div class="query-title">${esc(meta.title)}</div>` : '';
  const countHtml = `<div class="query-count">${results.length} 条结果</div>`;

  if (results.length === 0) {
    return `${titleHtml}<p class="query-empty">无匹配结果</p>`;
  }

  if (display === 'table') {
    const rawFields = meta.fields;
    const fields = Array.isArray(rawFields) ? rawFields
      : typeof rawFields === 'string' ? [rawFields]
      : ['label', 'type', 'tags', 'total_refs'];
    const customLabels = (meta.field_labels && typeof meta.field_labels === 'object')
      ? meta.field_labels : {};
    const computed = (meta.computed && typeof meta.computed === 'object')
      ? meta.computed : {};

    const thead = '<tr>' + fields.map(f =>
      `<th>${esc(customLabels[f] || QUERY_FIELD_LABELS[f] || f)}</th>`
    ).join('') + '</tr>';

    const tbody = results.map(item => {
      const cells = fields.map(f => {
        if (f === 'label') {
          return `<td><a class="wikilink resolved" href="#${encodeURIComponent(item.pid)}">${esc(item.label || item.pid)}</a></td>`;
        }
        const val = (f in computed) ? evalExpr(computed[f], item) : item[f];
        return `<td>${esc(fmtQueryValue(f, val))}</td>`;
      }).join('');
      return `<tr>${cells}</tr>`;
    }).join('');

    return `${titleHtml}${countHtml}
<table class="query-table">
<thead>${thead}</thead>
<tbody>${tbody}</tbody>
</table>`;
  }

  // list mode
  const items = results.map(item =>
    `<li><a class="wikilink resolved" href="#${encodeURIComponent(item.pid)}">${esc(item.label || item.pid)}</a></li>`
  ).join('');
  return `${titleHtml}${countHtml}<ul class="query-results">${items}</ul>`;
}

// ---------- 样式 ----------

const STYLES = `
.query-title {
  font-weight: 600;
  font-size: 1em;
  margin: .8em 0 .3em;
  color: var(--accent, #7a1f1f);
}
.query-count {
  font-size: .85em;
  color: var(--fg-muted, #888);
  margin-bottom: .4em;
}
.query-empty { color: var(--fg-muted, #888); font-style: italic; }
.query-results {
  list-style: disc;
  padding-left: 1.5em;
  margin: .4em 0 .8em;
  columns: 2;
  column-gap: 2em;
}
.query-results li { break-inside: avoid; padding: .1em 0; }
table.query-table {
  width: 100%;
  border-collapse: collapse;
  font-size: .93em;
  margin: .4em 0 .8em;
}
table.query-table th {
  background: var(--bg-box, #f0ece0);
  border: 1px solid var(--border, #d8d2bf);
  padding: .3em .5em;
  text-align: left;
  font-weight: 600;
}
table.query-table td {
  border: 1px solid var(--border, #d8d2bf);
  padding: .25em .5em;
  vertical-align: top;
}
table.query-table tr:nth-child(even) td { background: var(--bg-stripe, #f8f5ed); }
`;

function injectStyles() {
  if (document.getElementById('semantic-query-style')) return;
  const el = document.createElement('style');
  el.id = 'semantic-query-style';
  el.textContent = STYLES;
  document.head.appendChild(el);
}

// ---------- 插件入口 ----------

export default {
  name: PLUGIN_NAME,
  version: '1.0.0',
  description: '::: query 块渲染：语义查询、布尔过滤、计算字段、自定义列标签',

  async init(core) {
    injectStyles();

    // onAfterRender：展开 query 占位符（semantic-block 已跳过这些占位符）
    core.hooks.onAfterRender.add(async (html, ctx) => {
      const sb = core.semanticBlock;
      if (!sb) return html; // semantic-block 未加载

      const pid = ctx?.pid ?? '__last__';
      const blocks = sb.getBlocks(pid);
      if (!blocks.some(b => b.blockType === 'query')) return html;

      const { PH_OPEN, PH_CLOSE } = sb;
      const PH_PARA_RE = new RegExp(
        `<p>\\s*${PH_OPEN}(\\d+)${PH_CLOSE}\\s*<\\/p>`, 'g'
      );

      return html.replace(PH_PARA_RE, (match, idxStr) => {
        const block = blocks[parseInt(idxStr, 10)];
        if (!block || block.blockType !== 'query') return match;
        return renderQueryBlock(block.meta, core.registry);
      });
    });
  },
};
