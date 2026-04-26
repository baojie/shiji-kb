/**
 * semantic-block — ::: infobox / ::: meta / ::: seealso 渲染插件
 *
 * 职责：
 *   onBeforeRender  解析页面中所有 ::: 块，替换为占位符（所有类型，含 query）
 *   onAfterRender   展开 infobox / meta / seealso 占位符；query 占位符原样保留给 semantic-query
 *   onInfobox       将第一个 ::: infobox 的字段注入 sidebar
 *
 * 通过 core.semanticBlock 暴露缓存，供 semantic-query 等插件读取。
 */

import { resolvePageId } from '../../js/registry.js';

const PLUGIN_NAME = 'semantic-block';

// 占位符字符（Unicode 私用区）——semantic-query 使用相同值
export const PH_OPEN  = '';
export const PH_CLOSE = '';

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

// 简单 YAML 解析：flat key: value / key: [a,b,c] / key: {k:v,...}
export function parseYaml(text) {
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
    } else if (val.startsWith('{') && val.endsWith('}')) {
      const inner = val.slice(1, -1);
      const sub = {};
      for (const pair of inner.split(',')) {
        const ci2 = pair.indexOf(':');
        if (ci2 > 0) sub[pair.slice(0, ci2).trim()] = pair.slice(ci2 + 1).trim();
      }
      obj[key] = sub;
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

// ::: type [attrs]\ncontent\n::: → 占位符（提取所有类型，含 query）
export function extractBlocks(body) {
  const blocks = [];
  const re = /^:::[ \t]+(\w+)([^\n]*)\n([\s\S]*?)^:::[ \t]*$/gm;
  const newBody = body.replace(re, (_, blockType, inlineStr, content) => {
    const meta = { ...parseYaml(content), ...parseInlineAttrs(inlineStr || '') };
    const idx = blocks.length;
    blocks.push({ idx, blockType: blockType.toLowerCase(), meta, rawContent: content });
    return `${PH_OPEN}${idx}${PH_CLOSE}`;
  });
  return { newBody, blocks };
}

// seealso：展开 rawContent 里的 [[...]] wikilink（在 onAfterRender 阶段手动展开）
function renderSeeAlso(rawContent, resolve) {
  const WIKILINK_RE = /\[\[([^\[\]|]+?)(?:\|([^\[\]]+?))?\]\]/g;
  const lines = (rawContent || '').trim().split('\n').filter(l => l.trim());

  function expandLine(line) {
    let result = '';
    let lastIndex = 0;
    let m;
    WIKILINK_RE.lastIndex = 0;
    while ((m = WIKILINK_RE.exec(line)) !== null) {
      result += esc(line.slice(lastIndex, m.index));
      const target = m[1].trim();
      const display = m[2] ? m[2].trim() : target;
      const resolved = resolve(target);
      if (!resolved) {
        result += `<a class="wikilink broken" href="#${encodeURIComponent(target)}">${esc(display)}</a>`;
      } else {
        const [pid2] = resolved;
        result += `<a class="wikilink resolved" href="#${encodeURIComponent(pid2)}">${esc(display)}</a>`;
      }
      lastIndex = m.index + m[0].length;
    }
    result += esc(line.slice(lastIndex));
    return result;
  }

  if (lines.length === 1) {
    return `<p class="seealso-block"><span class="seealso-label">📖 详细参见</span>${expandLine(lines[0])}</p>`;
  }
  const items = lines.map(l => `<li>${expandLine(l.trim())}</li>`).join('');
  return `<div class="seealso-block"><p class="seealso-label">📖 详细参见</p><ul>${items}</ul></div>`;
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

// ---------- 样式（infobox + meta，不含 query） ----------

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
    const s = String(v).trim().replace(/\(/g, '（').replace(/\)/g, '）');
    return s;
  }
  if (Array.isArray(v)) return esc(v.join(' · '));
  return esc(String(v));
}

function injectMetaBlock(blocks, core) {
  const metaBlocks = blocks.filter(b => b.blockType === 'meta');
  if (!metaBlocks.length) return;

  const infobox = document.getElementById('infobox');
  if (!infobox) return;

  infobox.querySelectorAll('.sb-meta-section').forEach(el => el.remove());

  for (const mb of metaBlocks) {
    const rows = [];
    for (const [k, v] of Object.entries(mb.meta)) {
      const label = META_FIELD_LABELS[k] || k;
      const fv = fmtMetaValue(k, v);
      if (fv) rows.push(`<tr><th>${esc(label)}</th><td>${fv}</td></tr>`);
    }
    if (!rows.length) continue;
    const section = document.createElement('div');
    section.className = 'sb-meta-section';
    let tableHtml = `<table>${rows.join('')}</table>`;
    if (core?.pnCitation) tableHtml = core.pnCitation.expand(tableHtml);
    section.innerHTML = tableHtml;
    infobox.appendChild(section);
  }

  infobox.removeAttribute('hidden');
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
  version: '1.1.0',
  description: '语义块：::: infobox 和 ::: meta 解析渲染；暴露 core.semanticBlock 供其他插件读取',

  async init(core) {
    injectStyles();

    // 1. onBeforeRender：提取所有 ::: 块（含 query），替换为占位符
    core.hooks.onBeforeRender.add(async (body, ctx) => {
      const pid = ctx?.pid ?? '__last__';
      const { newBody, blocks } = extractBlocks(body);
      _cache.set(pid, blocks);
      _cache.set('__last__', blocks);
      return newBody;
    });

    // 2. onAfterRender：展开 infobox/meta 占位符；query 占位符原样保留
    core.hooks.onAfterRender.add(async (html, ctx) => {
      const pid = ctx?.pid ?? '__last__';
      const blocks = _cache.get(pid) || _cache.get('__last__') || [];
      if (!blocks.length) return html;

      let infoboxCount = 0;
      const PH_PARA_RE = new RegExp(
        `<p>\\s*${PH_OPEN}(\\d+)${PH_CLOSE}\\s*<\\/p>`, 'g'
      );

      const result = html.replace(PH_PARA_RE, (match, idxStr) => {
        const block = blocks[parseInt(idxStr, 10)];
        if (!block) return '';
        const { blockType, meta } = block;

        if (blockType === 'infobox') {
          infoboxCount++;
          if (infoboxCount === 1) return '';
          return renderInlineInfoboxHtml(meta);
        }
        if (blockType === 'meta') {
          return '';
        }
        if (blockType === 'query') {
          return match; // 保留占位符，交给 semantic-query 处理
        }
        if (blockType === 'seealso') {
          const resolve = (target) => resolvePageId(target, core.registry);
          return renderSeeAlso(block.rawContent, resolve);
        }
        const safe = JSON.stringify({ type: blockType, ...meta }).replace(/'/g, '&#39;');
        return `<div class="semantic-block" data-block-type="${esc(blockType)}" data-meta='${safe}' hidden></div>`;
      });

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

    // 4. 暴露 API：getBlocks 供 semantic-query 等插件读取
    core.semanticBlock = {
      getBlocks: (pid) => _cache.get(pid) || _cache.get('__last__') || [],
      PH_OPEN,
      PH_CLOSE,
    };
  },
};
