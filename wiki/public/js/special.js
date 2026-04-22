/* special.js — Special: 系统页动态渲染 */

import { escapeHtml } from './util.js';

const SPECIAL_PAGES = [
  { id: 'Special:知识量',  desc: '知识量（K）度量的定义与公式' },
  { id: 'Special:Settings', desc: '插件开关与用户设置' },
  { id: 'Special:Plugins',  desc: '已安装插件列表' },
  { id: 'Special:All',      desc: '所有特殊系统页面索引' },
  { id: 'Special:Random',   desc: '随机跳转到一个非章节页面' },
];

function setPage(title, html) {
  document.body.classList.remove('is-home');
  document.getElementById('article').innerHTML = html;
  const ib = document.getElementById('infobox');
  if (ib) ib.outerHTML = '<aside class="infobox" id="infobox" hidden></aside>';
  document.getElementById('crumb').textContent = 'Special / ' + title;
  document.title = title + ' · 史记 Wiki';
  document.getElementById('src-info').innerHTML = '';
  document.getElementById('broken-info').textContent = '';
  window.scrollTo(0, 0);
}

// 从 plugins.json 加载插件定义（供 Settings 和 Plugins 页使用）
let _pluginDefs = null;
async function getPluginDefs() {
  if (_pluginDefs) return _pluginDefs;
  try {
    const r = await fetch('plugins.json');
    if (!r.ok) return [];
    const m = await r.json();
    _pluginDefs = (m.plugins || []).map(p =>
      typeof p === 'string'
        ? { key: p, name: p, desc: '', corePlugin: false }
        : {
            key:        p.settings_key || p.id,
            name:       p.name || p.id,
            desc:       p.description || '',
            id:         p.id,
            corePlugin: !p.settings_key,   // 无 settings_key = 核心插件，始终运行
          }
    );
    return _pluginDefs;
  } catch { return []; }
}

function loadSettings() {
  try { return JSON.parse(localStorage.getItem('wiki_settings') || '{}'); }
  catch { return {}; }
}

function saveSettings(s) {
  localStorage.setItem('wiki_settings', JSON.stringify(s));
}

export async function renderSpecialSettings(core) {
  const s = loadSettings();
  const PLUGIN_DEFS = await getPluginDefs();

  const rows = PLUGIN_DEFS.map(p => {
    const enabled = s?.plugins?.[p.key] === true;
    return `<tr>
      <td><strong>${escapeHtml(p.name)}</strong><br><small class="muted">${escapeHtml(p.desc)}</small></td>
      <td style="text-align:center">
        <label class="toggle-label">
          <input type="checkbox" data-plugin="${escapeHtml(p.key)}" ${enabled ? 'checked' : ''}>
          ${enabled ? '已启用' : '已关闭'}
        </label>
      </td>
    </tr>`;
  }).join('');

  setPage('Settings', `
    <h1>Special:Settings</h1>
    <p class="muted">设置保存在浏览器 localStorage，不同设备独立。</p>
    <h2>插件</h2>
    <table class="settings-table">
      <thead><tr><th>插件</th><th>状态</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
    <p><small>更改后刷新页面生效。</small></p>
    <hr>
    <h2>特殊页面</h2>
    <p>→ <a href="#${encodeURIComponent('Special:Plugins')}">Special:Plugins</a> &nbsp;
       → <a href="#${encodeURIComponent('Special:All')}">Special:All</a></p>
  `);

  // 绑定 checkbox 事件
  document.querySelectorAll('input[data-plugin]').forEach(cb => {
    cb.addEventListener('change', () => {
      const settings = loadSettings();
      if (!settings.plugins) settings.plugins = {};
      settings.plugins[cb.dataset.plugin] = cb.checked;
      saveSettings(settings);
      cb.nextSibling.textContent = cb.checked ? '已启用' : '已关闭';
    });
  });
}

/* ── Special:Plugins ── */
export async function renderSpecialPlugins(core) {
  const PLUGIN_DEFS = await getPluginDefs();
  const s = loadSettings();
  const activatedDefs = PLUGIN_DEFS.filter(p => p.corePlugin || s?.plugins?.[p.key] === true);
  const pluginRows = activatedDefs.length
    ? activatedDefs.map(p =>
        `<tr><td><strong>${escapeHtml(p.name)}</strong></td><td>${escapeHtml(p.version || '—')}</td></tr>`
      ).join('')
    : '<tr><td colspan="2" class="muted">（无已激活插件）</td></tr>';
  const allDefs = PLUGIN_DEFS.map(p => {
    const status = p.corePlugin
      ? '🔵 核心插件，始终运行'
      : (s?.plugins?.[p.key] === true ? '✅ 已启用' : '⭕ 已安装，未启用');
    return `<tr>
      <td><strong>${escapeHtml(p.name)}</strong></td>
      <td>${status}</td>
      <td><small class="muted">${escapeHtml(p.desc)}</small></td>
    </tr>`;
  }).join('');

  setPage('Plugins', `
    <h1>Special:Plugins</h1>

    <h2>已激活插件</h2>
    <table>
      <thead><tr><th>名称</th><th>版本</th></tr></thead>
      <tbody>${pluginRows}</tbody>
    </table>

    <h2>所有已安装插件</h2>
    <table>
      <thead><tr><th>插件</th><th>状态</th><th>说明</th></tr></thead>
      <tbody>${allDefs}</tbody>
    </table>

    <p>→ <a href="#${encodeURIComponent('Special:Settings')}">Special:Settings</a> 管理插件开关</p>
  `);
}

/* ── Special:All ── */
export function renderSpecialAll(core) {
  // 从 registry 中找所有 special 页
  const registered = Object.entries(core.registry.pages)
    .filter(([pid]) => pid.startsWith('Special:'))
    .map(([pid, e]) => ({ pid, label: e.label || pid }));

  // 合并硬编码路由（不在 registry 里的）
  const hardcoded = [
    { pid: 'Special:Random',   label: '随机页' },
    { pid: 'Special:Settings', label: '设置' },
    { pid: 'Special:Plugins',  label: '插件列表' },
    { pid: 'Special:All',      label: '所有特殊页面' },
  ];

  const seen = new Set(registered.map(r => r.pid));
  const all = [
    ...registered,
    ...hardcoded.filter(h => !seen.has(h.pid)),
  ].sort((a, b) => a.pid.localeCompare(b.pid));

  const rows = all.map(({ pid, label }) => {
    const def = SPECIAL_PAGES.find(p => p.id === pid);
    return `<tr>
      <td><a href="#${encodeURIComponent(pid)}">${escapeHtml(pid)}</a></td>
      <td>${escapeHtml(label)}</td>
      <td class="muted">${def ? escapeHtml(def.desc) : ''}</td>
    </tr>`;
  }).join('');

  setPage('All Special Pages', `
    <h1>Special:All — 所有特殊系统页面</h1>
    <table>
      <thead><tr><th>页面 ID</th><th>标题</th><th>说明</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
  `);
}

/* ── Special:知识量 — 动态 K 值页（含增长图表）── */
export async function renderSpecialKnowledge(core) {
  // 加载时间线数据
  let timeline = [];
  try {
    const r = await fetch('data/knowledge_timeline.jsonl');
    if (r.ok) {
      const text = await r.text();
      timeline = text.trim().split('\n').filter(Boolean).map(l => JSON.parse(l));
    }
  } catch (e) { /* 无数据则不画图 */ }

  // 加载最新快照
  let latest = null;
  try {
    const r = await fetch('data/knowledge_latest.json');
    if (r.ok) latest = await r.json();
  } catch (e) { /* ignore */ }

  const K = latest ? latest.K.toLocaleString() : '—';
  const pages = latest ? latest.page_count : '—';
  const featured = latest ? latest.featured_count : '—';
  const hitRate = latest ? (latest.link_hit_rate * 100).toFixed(1) + '%' : '—';

  // SVG 折线图
  const chartHtml = buildKChart(timeline);

  // K 公式（仅文字，不依赖 KaTeX）
  const formula = `
    <blockquote>
      <code>K = Σ_page  log₂(1+B) × (1 + min(D,5)) × W × clamp(q/30, 1, 3)</code>
    </blockquote>
    <table>
      <thead><tr><th>变量</th><th>含义</th><th>说明</th></tr></thead>
      <tbody>
        <tr><td><b>B</b></td><td>页面字节数</td><td>去除 frontmatter 后 UTF-8 字节数</td></tr>
        <tr><td><b>D</b></td><td>链接密度（封顶 5.0）</td><td>wikilink 数 / (B/1000)</td></tr>
        <tr><td><b>W</b></td><td>类型权重</td><td>person/event/place=1.0 · topic=0.8 · chapter=0.4</td></tr>
        <tr><td><b>q</b></td><td>质量分（0–90）</td><td>归一化为 Q∈[1, 3]</td></tr>
      </tbody>
    </table>`;

  const top10 = latest && latest.top10_pages ? latest.top10_pages.map((p, i) =>
    `<tr><td>${i + 1}</td><td><a href="#${encodeURIComponent(p.pid)}">${escapeHtml(p.pid)}</a></td><td>${p.k}</td></tr>`
  ).join('') : '';

  setPage('知识量 (K)', `
    <h1>Special:知识量 — 知识量度量</h1>

    <div class="k-stat-bar">
      <div class="k-stat"><span class="k-stat-val">${K}</span><span class="k-stat-label">当前 K 值</span></div>
      <div class="k-stat"><span class="k-stat-val">${pages}</span><span class="k-stat-label">总页数</span></div>
      <div class="k-stat"><span class="k-stat-val">${featured}</span><span class="k-stat-label">精品页</span></div>
      <div class="k-stat"><span class="k-stat-val">${hitRate}</span><span class="k-stat-label">链接命中率</span></div>
    </div>

    <h2>增长曲线</h2>
    ${chartHtml}

    <h2>公式定义</h2>
    ${formula}

    <h2>K 值 Top 10 页面</h2>
    <table>
      <thead><tr><th>#</th><th>页面</th><th>K</th></tr></thead>
      <tbody>${top10}</tbody>
    </table>

    <h2>设计目标</h2>
    <ul>
      <li>反映<b>知识深度</b>，而非单纯字数——链接密度奖励内联结构</li>
      <li>防止刷字数——log₂ 压缩使扩张收益递减</li>
      <li>区分内容质量——Q 乘子激励高质量页面</li>
      <li>章节存根不淹没实体页——章节权重 0.4 刻意压缩</li>
    </ul>

    <p class="muted">Special: 系统页本身不计入 K。
    →&nbsp;<a href="#${encodeURIComponent('Special:Settings')}">设置</a>
    &nbsp;·&nbsp;<a href="#${encodeURIComponent('Special:All')}">所有特殊页面</a></p>
  `);
}

function buildKChart(timeline) {
  if (!timeline.length) return '<p class="muted">（暂无历史数据）</p>';

  const W = 680, H = 260, PAD = { top: 20, right: 20, bottom: 40, left: 60 };
  const cw = W - PAD.left - PAD.right;
  const ch = H - PAD.top - PAD.bottom;

  const vals = timeline.map(d => d.K);
  const minK = Math.min(...vals) * 0.97;
  const maxK = Math.max(...vals) * 1.01;

  const xScale = (i) => PAD.left + (i / (timeline.length - 1 || 1)) * cw;
  const yScale = (v) => PAD.top + ch - ((v - minK) / (maxK - minK)) * ch;

  const points = timeline.map((d, i) => `${xScale(i).toFixed(1)},${yScale(d.K).toFixed(1)}`).join(' ');

  // Y axis ticks
  const yTicks = 5;
  const yTickHtml = Array.from({ length: yTicks + 1 }, (_, i) => {
    const v = minK + (maxK - minK) * (i / yTicks);
    const y = yScale(v).toFixed(1);
    return `<line x1="${PAD.left}" y1="${y}" x2="${PAD.left + cw}" y2="${y}" stroke="var(--border)" stroke-dasharray="3,3"/>
      <text x="${PAD.left - 6}" y="${y}" text-anchor="end" dominant-baseline="middle" font-size="11" fill="var(--fg-muted)">${Math.round(v).toLocaleString()}</text>`;
  }).join('');

  // X axis labels (evenly spaced, max 6)
  const step = Math.ceil(timeline.length / 6);
  const xTickHtml = timeline.map((d, i) => {
    if (i % step !== 0 && i !== timeline.length - 1) return '';
    const x = xScale(i).toFixed(1);
    const label = d.generated ? d.generated.slice(0, 10) : '';
    return `<text x="${x}" y="${H - PAD.bottom + 14}" text-anchor="middle" font-size="10" fill="var(--fg-muted)">${label}</text>`;
  }).join('');

  // Featured count as area fill (secondary)
  const featVals = timeline.map(d => d.featured_count || 0);
  const maxFeat = Math.max(...featVals) || 1;
  const featPoints = timeline.map((d, i) => {
    const fy = PAD.top + ch - ((d.featured_count || 0) / maxFeat) * ch;
    return `${xScale(i).toFixed(1)},${fy.toFixed(1)}`;
  }).join(' ');
  const featClose = `${xScale(timeline.length - 1).toFixed(1)},${PAD.top + ch} ${xScale(0).toFixed(1)},${PAD.top + ch}`;

  return `<div class="k-chart-wrap">
  <svg viewBox="0 0 ${W} ${H}" style="width:100%;max-width:${W}px;height:auto;display:block">
    <!-- grid + y ticks -->
    ${yTickHtml}
    <!-- featured fill (secondary axis, scaled independently) -->
    <polygon points="${featPoints} ${featClose}" fill="rgba(99,179,237,0.15)" stroke="none"/>
    <!-- K line -->
    <polyline points="${points}" fill="none" stroke="var(--accent)" stroke-width="2.5" stroke-linejoin="round"/>
    <!-- dots -->
    ${timeline.map((d, i) => `<circle cx="${xScale(i).toFixed(1)}" cy="${yScale(d.K).toFixed(1)}" r="3" fill="var(--accent)"/>`).join('')}
    <!-- x labels -->
    ${xTickHtml}
    <!-- axis labels -->
    <text x="${PAD.left}" y="${H - 4}" font-size="11" fill="var(--fg-muted)">日期</text>
    <text x="${PAD.left - 40}" y="${PAD.top}" font-size="11" fill="var(--accent)" text-anchor="middle">K 值</text>
    <text x="${PAD.left + cw}" y="${PAD.top + 12}" font-size="10" fill="rgba(99,179,237,0.8)" text-anchor="end">精品页（淡蓝）</text>
  </svg>
  </div>`;
}
