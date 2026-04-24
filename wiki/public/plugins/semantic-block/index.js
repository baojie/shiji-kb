/**
 * semantic-block.js — 语义块插件（客户端）
 *
 * 处理 Markdown 中的 ::: block ... ::: 语法，走三个 hook：
 *
 *   onBeforeRender  解析 ::: 块，替换为占位符，防止 markdown-it 误处理
 *   onAfterRender   将占位符展开为 HTML（inline infobox / 隐藏 meta 块）
 *   onInfobox       将第一个 ::: infobox 块的字段注入 sidebar
 *
 * 支持两种块类型：
 *   ::: infobox     可见信息卡片（第一个→sidebar，后续→行内 float-right）
 *   ::: meta        隐藏元数据（<div data-meta> hidden）
 */

const PLUGIN_NAME = 'semantic-block';

// 占位符字符（Unicode 私用区，不同于 wikilink 的 /）
const PH_OPEN  = '';
const PH_CLOSE = '';

// 页面状态缓存：pid → blocks[]
const _cache = new Map();

// ---------- 字段表 ----------

const INFOBOX_FIELD_MAP = [
  ['canonical_name', '规范名'],
  ['type',           '类型'],
  ['birth_ce',       '生'],
  ['death_ce',       '卒'],
  ['native',         '籍贯'],
  ['title',          '封号'],
  ['office',         '官职'],
  ['date',           '时间'],
  ['end_date',       '终止'],
  ['location',       '地点'],
  ['participants',   '参与方'],
  ['result',         '结果'],
  ['modern_name',    '今地名'],
  ['region',         '所属'],
  ['tags',           '标签'],
  ['aliases',        '别名'],
  ['note',           '备注'],
];

const FIELD_MAP_KEYS = new Set([...INFOBOX_FIELD_MAP.map(([k]) => k), 'label']);

const SYSTEM_EXCLUDE_KEYS = new Set([
  'id', 'featured', 'auto_generated', 'path',
  'total_refs', 'total_chapters', 'quality_score',
  'lifespan', 'revision_count',
]);

const DATE_KEYS = new Set(['birth_ce', 'death_ce', 'date', 'end_date']);

const TYPE_VALUE_MAP = {
  person: '人物', place: '地名', state: '邦国', official: '官职',
  identity: '身份', dynasty: '朝代', event: '事件',
  chapter: '章节', topic: '主题', meta: '元页',
};

// ---------- 工具 ----------

function esc(s) {
  return String(s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function fmtValue(key, v) {
  if (v == null) return '';
  if (Array.isArray(v)) return v.map(String).join(' · ');
  if (typeof v === 'boolean') return v ? '是' : '否';
  if (key === 'type') return TYPE_VALUE_MAP[v] || String(v);
  if (DATE_KEYS.has(key) && typeof v === 'number')
    return v < 0 ? `前 ${-v}` : String(v);
  return String(v);
}

// 简单 YAML 解析：flat key: value / key: [a,b,c]
function parseYaml(text) {
  const obj = {};
  for (const line of text.split('\n')) {
    const ci = line.indexOf(':');
    if (ci < 1) continue;
    const key = line.slice(0, ci).trim();
    if (!key || key.startsWith('#')) continue;
    let val = line.slice(ci + 1).trim();
    if (!val) continue;
    if (val.startsWith('[') && val.endsWith(']')) {
      obj[key] = val.slice(1, -1).split(',').map(s => s.trim()).filter(Boolean);
    } else if ((val[0] === '"' && val.endsWith('"')) || (val[0] === "'" && val.endsWith("'"))) {
      obj[key] = val.slice(1, -1);
    } else if (val === 'true') {
      obj[key] = true;
    } else if (val === 'false') {
      obj[key] = false;
    } else {
      const n = Number(val);
      obj[key] = isNaN(n) ? val : n;
    }
  }
  return obj;
}

function parseInlineAttrs(s) {
  const obj = {};
  const re = /(\w+)=("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|\S+)/g;
  let m;
  while ((m = re.exec(s)) !== null) {
    let v = m[2];
    if (v.length >= 2 && (v[0] === '"' || v[0] === "'") && v[v.length - 1] === v[0])
      v = v.slice(1, -1);
    obj[m[1]] = v;
  }
  return obj;
}

// ::: type [attrs]\ncontent\n::: → 占位符
function extractBlocks(body) {
  const blocks = [];
  const re = /^:::[ \t]+(\w+)([^\n]*)\n([\s\S]*?)^:::[ \t]*$/gm;
  const newBody = body.replace(re, (_, blockType, inlineStr, content) => {
    const meta = { ...parseYaml(content), ...parseInlineAttrs(inlineStr || '') };
    const idx = blocks.length;
    blocks.push({ idx, blockType: blockType.toLowerCase(), meta });
    return `${PH_OPEN}${idx}${PH_CLOSE}`;
  });
  return { newBody, blocks };
}

// ---------- 渲染 ----------

function renderInlineInfoboxHtml(meta) {
  const label = meta.label || '';
  const rows = [];
  for (const [key, dispName] of INFOBOX_FIELD_MAP) {
    if (key === 'label' || !(key in meta)) continue;
    if (key === 'canonical_name' && meta.canonical_name === label) continue;
    const fv = fmtValue(key, meta[key]);
    if (fv) rows.push(`<tr><th>${esc(dispName)}</th><td>${esc(fv)}</td></tr>`);
  }
  for (const [key, val] of Object.entries(meta)) {
    if (FIELD_MAP_KEYS.has(key) || SYSTEM_EXCLUDE_KEYS.has(key)) continue;
    const fv = fmtValue(key, val);
    if (fv) rows.push(`<tr><th>${esc(key)}</th><td>${esc(fv)}</td></tr>`);
  }
  if (!rows.length && !label) return '';
  const h = label ? `<h2>${esc(label)}</h2>` : '';
  return `<aside class="infobox inline">${h}<table>${rows.join('')}</table></aside>`;
}

// sidebar 需要注入的额外字段（已由 renderInfobox 处理的跳过）
const SIDEBAR_HANDLED = new Set([
  'canonical_name', 'aliases', 'type', 'birth_ce', 'death_ce', 'tags', 'label',
]);

function buildExtraInfoboxRows(blockMeta) {
  const rows = [];
  for (const [key, dispName] of INFOBOX_FIELD_MAP) {
    if (SIDEBAR_HANDLED.has(key) || !(key in blockMeta)) continue;
    const fv = fmtValue(key, blockMeta[key]);
    if (fv) rows.push(`<tr><th>${esc(dispName)}</th><td>${esc(fv)}</td></tr>`);
  }
  for (const [key, val] of Object.entries(blockMeta)) {
    if (FIELD_MAP_KEYS.has(key) || SYSTEM_EXCLUDE_KEYS.has(key)) continue;
    const fv = fmtValue(key, val);
    if (fv) rows.push(`<tr><th>${esc(key)}</th><td>${esc(fv)}</td></tr>`);
  }
  return rows;
}

// ---------- 样式 ----------

const STYLES = `
aside.infobox.inline {
  float: right;
  clear: right;
  margin: 0 0 1.2em 1.5em;
  width: 240px;
  font-size: .88em;
  background: var(--bg-box, #f0ece0);
  border: 1px solid var(--border, #d8d2bf);
  border-radius: 4px;
  padding: 1em;
  align-self: start;
}
aside.infobox.inline h2 {
  font-size: 1em;
  margin: 0 0 .5em;
  padding-bottom: .25em;
  border-bottom: 1px solid var(--border, #d8d2bf);
  color: var(--accent, #7a1f1f);
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}
aside.infobox.inline table { width: 100%; border: none; margin: 0; }
aside.infobox.inline th, aside.infobox.inline td {
  border: none;
  padding: .2em .3em;
  vertical-align: top;
  background: transparent;
  font-size: .95em;
}
aside.infobox.inline th { color: var(--fg-muted, #666); font-weight: 500; width: 4em; }
aside.infobox.inline.collapsed table { display: none; }
.infobox-toggle {
  background: none; border: none; cursor: pointer;
  font-size: .75em; color: var(--fg-muted, #666);
  padding: 0; line-height: 1;
}
.infobox-toggle:hover { color: var(--accent, #7a1f1f); }
.sb-meta-section {
  margin-top: .6em;
  padding-top: .5em;
  border-top: 1px solid var(--border, #d8d2bf);
}
.sb-meta-section table { width: 100%; border: none; margin: 0; }
.sb-meta-section th, .sb-meta-section td {
  border: none;
  padding: .15em .25em;
  vertical-align: top;
  background: transparent;
  font-size: .93em;
}
.sb-meta-section th { color: var(--fg-muted, #888); font-weight: 400; width: 5em; white-space: nowrap; }
.sb-meta-section td { word-break: break-all; }
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
  if (document.getElementById('semantic-block-style')) return;
  const el = document.createElement('style');
  el.id = 'semantic-block-style';
  el.textContent = STYLES;
  document.head.appendChild(el);
}

// ---------- meta 字段显示名 ----------

const META_FIELD_LABELS = {
  pn:             '原文位置',
  event_type:     '事件类型',
  location:       '地点',
  chapter:        '来源章节',
  paragraph_refs: '段落引用',
};

function fmtMetaValue(key, v) {
  if (key === 'chapter') {
    const names = Array.isArray(v) ? v : String(v).split(/[\s,，]+/).filter(Boolean);
    return names.map(n => `<a href="#${encodeURIComponent(n)}">${esc(n)}</a>`).join(' · ');
  }
  if (key === 'pn') {
    // 全局替换所有半角括号为全角，供 pn-citation 插件展开为链接
    // 多段格式：(094-10) | (097-3.1) → （094-10） | （097-3.1）
    const s = String(v).trim().replace(/\(/g, '（').replace(/\)/g, '）');
    return s;  // 不 escape，让 pn-citation 处理
  }
  if (Array.isArray(v)) return esc(v.join(' · '));
  return esc(String(v));
}

function injectMetaBlock(blocks, core) {
  const metaBlocks = blocks.filter(b => b.blockType === 'meta');
  console.debug('[sb] injectMetaBlock: metaBlocks=', metaBlocks.length, 'blocks total=', blocks.length);
  if (!metaBlocks.length) return;

  const infobox = document.getElementById('infobox');
  console.debug('[sb] infobox found:', !!infobox, infobox?.id);
  if (!infobox) return;

  infobox.querySelectorAll('.sb-meta-section').forEach(el => el.remove());

  for (const mb of metaBlocks) {
    const rows = [];
    for (const [k, v] of Object.entries(mb.meta)) {
      const label = META_FIELD_LABELS[k] || k;
      const fv = fmtMetaValue(k, v);
      console.debug('[sb] meta field:', k, '→', fv ? fv.slice(0, 60) : '(empty)');
      if (fv) rows.push(`<tr><th>${esc(label)}</th><td>${fv}</td></tr>`);
    }
    if (!rows.length) continue;
    const section = document.createElement('div');
    section.className = 'sb-meta-section';
    let tableHtml = `<table>${rows.join('')}</table>`;
    // pn-citation 插件负责将 （NNN-MMM） 展开为链接
    if (core?.pnCitation) tableHtml = core.pnCitation.expand(tableHtml);
    section.innerHTML = tableHtml;
    infobox.appendChild(section);
    console.debug('[sb] meta section appended, pnCitation available:', !!core?.pnCitation);
  }

  infobox.removeAttribute('hidden');
}

// ---------- 查询引擎 ----------

const QUERY_SYSTEM_KEYS = new Set([
  'sort', 'order', 'limit', 'display', 'fields', 'title',
]);

const QUERY_FIELD_LABELS = {
  label: '名称', type: '类型', tags: '标签',
  total_refs: '引用', total_chapters: '章节数',
  quality_score: '质量', featured: '精品',
  lifespan: '活跃期',
};

const QUERY_TYPE_LABELS = {
  person: '人物', place: '地名', state: '邦国', official: '官职',
  identity: '身份', dynasty: '朝代', event: '事件', chapter: '章节',
  topic: '主题', list: '列表', sanwen: '散文', story: '故事',
};

function executeQuery(meta, registry) {
  const allPages = Object.entries(registry.pages);

  const filtered = allPages.filter(([pid, page]) => {
    for (const [key, val] of Object.entries(meta)) {
      if (QUERY_SYSTEM_KEYS.has(key)) continue;
      // _min / _max 范围过滤
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
      // 数组包含：页面字段是数组，查询值是字符串
      if (Array.isArray(pageVal) && typeof val === 'string') {
        if (!pageVal.includes(val)) return false;
        continue;
      }
      // 布尔/字符串/数字相等
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
  if (Array.isArray(v)) return v.join(' · ');
  if (typeof v === 'boolean') return v ? '是' : '';
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

    const thead = '<tr>' + fields.map(f =>
      `<th>${esc(QUERY_FIELD_LABELS[f] || f)}</th>`
    ).join('') + '</tr>';

    const tbody = results.map(item => {
      const cells = fields.map(f => {
        if (f === 'label') {
          return `<td><a class="wikilink resolved" href="#${encodeURIComponent(item.pid)}">${esc(item.label || item.pid)}</a></td>`;
        }
        return `<td>${esc(fmtQueryValue(f, item[f]))}</td>`;
      }).join('');
      return `<tr>${cells}</tr>`;
    }).join('');

    return `${titleHtml}${countHtml}
<table class="query-table">
<thead>${thead}</thead>
<tbody>${tbody}</tbody>
</table>`;
  }

  // list mode (default)
  const items = results.map(item =>
    `<li><a class="wikilink resolved" href="#${encodeURIComponent(item.pid)}">${esc(item.label || item.pid)}</a></li>`
  ).join('');
  return `${titleHtml}${countHtml}<ul class="query-results">${items}</ul>`;
}

// ---------- 折叠按钮 ----------

function initCollapseButtons() {
  document.querySelectorAll('aside.infobox.inline:not([data-sb-init])').forEach(aside => {
    aside.setAttribute('data-sb-init', '1');
    let h2 = aside.querySelector('h2');
    if (!h2) {
      h2 = document.createElement('h2');
      aside.prepend(h2);
    }
    const btn = document.createElement('button');
    btn.className = 'infobox-toggle';
    btn.textContent = '▲';
    btn.setAttribute('aria-label', '折叠');
    h2.appendChild(btn);
    btn.addEventListener('click', () => {
      const c = aside.classList.toggle('collapsed');
      btn.textContent = c ? '▼' : '▲';
      btn.setAttribute('aria-label', c ? '展开' : '折叠');
    });
  });
}

// ---------- 插件入口 ----------

export default {
  name: PLUGIN_NAME,
  version: '1.0.0',
  description: '语义块：::: infobox 和 ::: meta 解析渲染',

  async init(core) {
    injectStyles();

    // 1. onBeforeRender：提取 ::: 块，替换为占位符
    core.hooks.onBeforeRender.add(async (body, ctx) => {
      const pid = ctx?.pid ?? '__last__';
      const { newBody, blocks } = extractBlocks(body);
      _cache.set(pid, blocks);
      _cache.set('__last__', blocks);   // 供 onInfobox 回退使用
      return newBody;
    });

    // 2. onAfterRender：展开占位符 → HTML
    core.hooks.onAfterRender.add(async (html, ctx) => {
      const pid = ctx?.pid ?? '__last__';
      const blocks = _cache.get(pid) || _cache.get('__last__') || [];
      if (!blocks.length) return html;

      let infoboxCount = 0;
      const PH_PARA_RE = new RegExp(
        `<p>\\s*${PH_OPEN}(\\d+)${PH_CLOSE}\\s*<\\/p>`, 'g'
      );

      const result = html.replace(PH_PARA_RE, (_, idxStr) => {
        const block = blocks[parseInt(idxStr, 10)];
        if (!block) return '';
        const { blockType, meta } = block;

        if (blockType === 'infobox') {
          infoboxCount++;
          if (infoboxCount === 1) return '';   // 第一个由 sidebar 处理
          return renderInlineInfoboxHtml(meta);
        }
        if (blockType === 'meta') {
          // 不在 article 体内渲染，数据已缓存在 _cache，由 infobox 下方注入
          return '';
        }
        if (blockType === 'query') {
          return renderQueryBlock(meta, core.registry);
        }
        const safe = JSON.stringify({ type: blockType, ...meta }).replace(/'/g, '&#39;');
        return `<div class="semantic-block" data-block-type="${esc(blockType)}" data-meta='${safe}' hidden></div>`;
      });

      // 折叠按钮 + meta块 在 DOM 更新后初始化
      setTimeout(() => {
        initCollapseButtons();
        injectMetaBlock(blocks, core);
      }, 0);

      return result;
    });

    // 3. onInfobox：将第一个 ::: infobox 块的字段注入 sidebar
    core.hooks.onInfobox.add(async (rows, front) => {
      const pid = front?.id ?? '__last__';
      const blocks = _cache.get(pid) || _cache.get('__last__') || [];
      const first = blocks.find(b => b.blockType === 'infobox');
      if (first) {
        const extra = buildExtraInfoboxRows(first.meta);
        if (extra.length) {
          let insertAt = -1;
          for (let i = 0; i < rows.length; i++) {
            if (rows[i].includes('>卒<')) { insertAt = i + 1; break; }
          }
          if (insertAt >= 0) rows.splice(insertAt, 0, ...extra);
          else rows.push(...extra);
        }
      }

      return rows;
    });

    // 4. 暴露 API
    core.semanticBlock = {
      getBlocks: (pid) => _cache.get(pid) || [],
      getPageMeta: () => {
        const metas = [];
        document.querySelectorAll('.semantic-meta[data-meta]').forEach(el => {
          try { metas.push(JSON.parse(el.getAttribute('data-meta').replace(/&#39;/g, "'"))); }
          catch (_) {}
        });
        return metas;
      },
    };
  },
};
