/* special.js — Special: 系统页动态渲染 */

import { escapeHtml } from './util.js';

// 所有硬编码的 Special 页。新增 Special 页时只需在此添加一行。
// renderSpecialAll 自动用这个列表生成 Special:All 索引。
const SPECIAL_PAGES = [
  { id: 'Special:Recent',    label: '最近修订',     desc: '最近修订记录（滚动窗口，最新 500 条）' },
  { id: 'Special:AllPages',  label: '所有页面',     desc: '所有 wiki 页面的完整列表，支持分组切换' },
  { id: 'Special:Statistics', label: '统计 (Statistics)', desc: '知识库统计：K 值增长曲线、质量分布、页面计数' },
  { id: 'Special:Settings',  label: '设置',         desc: '用户设置' },
  { id: 'Special:Plugins',   label: '插件列表',     desc: '已安装插件列表' },
  { id: 'Special:All',       label: '所有特殊页面', desc: '所有特殊系统页面索引' },
  { id: 'Special:Random',    label: '随机页',       desc: '随机跳转到一个非章节页面' },
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
// 注意：此缓存在同一页面会话中保持，切换路由不会重新 fetch。
// 若需强制刷新，使用 getPluginDefs(true)。
let _pluginDefs = null;
async function getPluginDefs(force = false) {
  if (_pluginDefs && !force) return _pluginDefs;
  try {
    const r = await fetch('plugins.json?t=' + Date.now());
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

export async function renderSpecialSettings(core) {
  setPage('Settings', `
    <h1>Special:Settings</h1>
    <p class="muted">所有插件默认启用，无需手动配置。</p>
    <h2>特殊页面</h2>
    <p>→ <a href="#${encodeURIComponent('Special:Plugins')}">Special:Plugins</a> &nbsp;
       → <a href="#${encodeURIComponent('Special:All')}">Special:All</a></p>
  `);
}

/* ── Special:Plugins ── */
export async function renderSpecialPlugins(core) {
  const PLUGIN_DEFS = await getPluginDefs(true);
  const allDefs = PLUGIN_DEFS.map(p => {
    return `<tr>
      <td><strong>${escapeHtml(p.name)}</strong></td>
      <td>✅ 已启用</td>
      <td><small class="muted">${escapeHtml(p.desc)}</small></td>
    </tr>`;
  }).join('');

  setPage('Plugins', `
    <h1>Special:Plugins</h1>

    <table>
      <thead><tr><th>插件</th><th>状态</th><th>说明</th></tr></thead>
      <tbody>${allDefs}</tbody>
    </table>
  `);
}

/* ── Special:All ── */
export function renderSpecialAll(core) {
  // 从 registry 中找所有 special 页
  const registered = Object.entries(core.registry.pages)
    .filter(([pid]) => pid.startsWith('Special:'))
    .map(([pid, e]) => ({ pid, label: e.label || pid }));

  // 硬编码 + 插件动态注册的 Special 页合并
  const hardcoded = [
    ...SPECIAL_PAGES,
    ...core.specialPages,
  ].map(p => ({ pid: p.id, label: p.label }));

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

/* ── Special:Statistics — 统计页（K 值增长 + 质量分布）── */
export async function renderSpecialStatistics(core) {
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
  const hitRate = latest ? (latest.link_hit_rate * 100).toFixed(1) + '%' : '—';
  const qc = latest && latest.quality_counts ? latest.quality_counts : {};
  const premium = qc.premium ?? (latest ? latest.featured_count : '—');

  // SVG 折线图
  const chartHtml = buildKChart(timeline);
  const premiumChartHtml = buildPremiumChart(timeline);
  const qualityStackHtml = buildQualityStackChart(timeline);

  // 质量分布表格
  const QUALITY_LABELS = [
    ['premium', '旗舰', '#9f7aea'],
    ['featured', '精品', '#4f9cf9'],
    ['standard', '标准', '#68d391'],
    ['basic',    '基础', '#fbd38d'],
    ['stub',     '存根', '#fc8181'],
  ];
  const total = Object.values(qc).reduce((a, b) => a + b, 0) || 1;
  const qualityRows = QUALITY_LABELS.map(([key, label, color]) => {
    const n = qc[key] || 0;
    const pct = (n / total * 100).toFixed(1);
    const barW = Math.round(n / total * 200);
    return `<tr>
      <td><span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:${color};margin-right:6px"></span>${label} (${key})</td>
      <td style="text-align:right;font-variant-numeric:tabular-nums">${n.toLocaleString()}</td>
      <td style="text-align:right;color:var(--fg-muted)">${pct}%</td>
      <td><div style="display:inline-block;height:8px;width:${barW}px;background:${color};border-radius:2px;vertical-align:middle"></div></td>
    </tr>`;
  }).join('');

  // K 公式
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

  setPage('统计 (Statistics)', `
    <h1>Special:Statistics — 知识库统计</h1>

    <div class="k-stat-bar">
      <div class="k-stat"><span class="k-stat-val">${K}</span><span class="k-stat-label">当前 K 值</span></div>
      <div class="k-stat"><span class="k-stat-val">${pages}</span><span class="k-stat-label">总页数</span></div>
      <div class="k-stat"><span class="k-stat-val">${premium}</span><span class="k-stat-label">旗舰页 (premium)</span></div>
      <div class="k-stat"><span class="k-stat-val">${hitRate}</span><span class="k-stat-label">链接命中率</span></div>
    </div>

    <h2>K 值增长曲线</h2>
    ${chartHtml}

    <h2>旗舰页增长</h2>
    ${premiumChartHtml}

    <h2>质量分布随时间变化</h2>
    ${qualityStackHtml}

    <h2>当前质量分布</h2>
    <p class="chart-desc">五级质量体系由 <code>compute_quality.py</code> 自动评定。只有 <b>premium</b> 旗舰页可出现在首页。</p>
    <table>
      <thead><tr><th>级别</th><th>数量</th><th>占比</th><th>分布</th></tr></thead>
      <tbody>${qualityRows}</tbody>
    </table>

    <h2>K 值公式定义</h2>
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

function _buildSvgBase(timeline, vals, color, yLabel, maxTickCount = 8) {
  const W = 900, H = 320, PAD = { top: 28, right: 24, bottom: 48, left: 68 };
  const cw = W - PAD.left - PAD.right;
  const ch = H - PAD.top - PAD.bottom;

  const minV = Math.min(...vals) * 0.97;
  const maxV = Math.max(...vals) * 1.01;
  const xScale = (i) => PAD.left + (i / (timeline.length - 1 || 1)) * cw;
  const yScale = (v) => PAD.top + ch - ((v - minV) / (maxV - minV || 1)) * ch;

  const points = timeline.map((d, i) => `${xScale(i).toFixed(1)},${yScale(vals[i]).toFixed(1)}`).join(' ');

  // area fill under line
  const areaClose = `${xScale(timeline.length - 1).toFixed(1)},${PAD.top + ch} ${xScale(0).toFixed(1)},${PAD.top + ch}`;

  const yTicks = 6;
  const yTickHtml = Array.from({ length: yTicks + 1 }, (_, i) => {
    const v = minV + (maxV - minV) * (i / yTicks);
    const y = yScale(v).toFixed(1);
    const label = v >= 1000 ? Math.round(v).toLocaleString() : Math.round(v);
    return `<line x1="${PAD.left}" y1="${y}" x2="${PAD.left + cw}" y2="${y}" stroke="var(--border)" stroke-dasharray="4,4"/>
      <text x="${PAD.left - 8}" y="${y}" text-anchor="end" dominant-baseline="middle" font-size="12" fill="var(--fg-muted)">${label}</text>`;
  }).join('');

  const step = Math.ceil(timeline.length / maxTickCount);
  const xTickHtml = timeline.map((d, i) => {
    if (i % step !== 0 && i !== timeline.length - 1) return '';
    const x = xScale(i).toFixed(1);
    const label = d.generated ? d.generated.slice(0, 10) : '';
    return `<text x="${x}" y="${H - PAD.bottom + 16}" text-anchor="middle" font-size="11" fill="var(--fg-muted)">${label}</text>`;
  }).join('');

  return { W, H, PAD, cw, ch, xScale, yScale, points, areaClose, yTickHtml, xTickHtml, color };
}

function buildKChart(timeline) {
  if (!timeline.length) return '<p class="muted">（暂无历史数据）</p>';

  const vals = timeline.map(d => d.K);
  const { W, H, PAD, cw, ch, xScale, yScale, points, areaClose, yTickHtml, xTickHtml } = _buildSvgBase(timeline, vals, 'var(--accent)');

  return `
  <p class="chart-desc">每次提交后计算的知识量总分。<b>K 值越高</b>，代表知识库的信息密度与覆盖深度越大。
  单次跳跃通常对应批量新增页面；平缓上升对应现有页面的深化扩写。</p>
  <div class="k-chart-wrap">
  <svg viewBox="0 0 ${W} ${H}" style="width:100%;height:auto;display:block">
    ${yTickHtml}
    <polygon points="${points} ${areaClose}" fill="rgba(var(--accent-rgb,220,38,38),0.08)" stroke="none"/>
    <polyline points="${points}" fill="none" stroke="var(--accent)" stroke-width="2.5" stroke-linejoin="round"/>
    ${timeline.map((d, i) => `<circle cx="${xScale(i).toFixed(1)}" cy="${yScale(vals[i]).toFixed(1)}" r="3.5" fill="var(--accent)"/>`).join('')}
    ${xTickHtml}
    <text x="${PAD.left - 8}" y="${PAD.top - 10}" font-size="12" fill="var(--accent)" text-anchor="end">K 值</text>
    <text x="${PAD.left + cw / 2}" y="${H - 6}" font-size="12" fill="var(--fg-muted)" text-anchor="middle">提交日期</text>
  </svg>
  </div>`;
}

function buildPremiumChart(timeline) {
  if (!timeline.length) return '';

  // 兼容旧快照（featured_count）和新快照（quality_counts.premium）
  const vals = timeline.map(d =>
    d.quality_counts ? (d.quality_counts.premium || 0) : (d.featured_count || 0)
  );
  if (Math.max(...vals) === 0) return '<p class="muted">（暂无旗舰页历史数据）</p>';

  const color = 'rgba(159,122,234,1)';
  const { W, H, PAD, cw, ch, xScale, yScale, points, areaClose, yTickHtml, xTickHtml } = _buildSvgBase(timeline, vals, color);

  const dotHtml = timeline.map((d, i) => {
    const cx = xScale(i).toFixed(1), cy = yScale(vals[i]).toFixed(1);
    return `<circle cx="${cx}" cy="${cy}" r="3.5" fill="${color}"/>`;
  }).join('');

  return `
  <p class="chart-desc"><b>旗舰页</b>（premium）是通过 <code>compute_quality.py</code> 自动评定的最高质量词条，
  满足：有图 + ≥5节 + 散文≥1000字 + (PN≥10 或引文≥10 或散文≥2500)。
  旗舰页数量增长反映了知识库的深化进度。</p>
  <div class="k-chart-wrap">
  <svg viewBox="0 0 ${W} ${H}" style="width:100%;height:auto;display:block">
    ${yTickHtml}
    <polygon points="${points} ${areaClose}" fill="rgba(159,122,234,0.18)" stroke="none"/>
    <polyline points="${points}" fill="none" stroke="${color}" stroke-width="2.5" stroke-linejoin="round"/>
    ${dotHtml}
    ${xTickHtml}
    <text x="${PAD.left - 8}" y="${PAD.top - 10}" font-size="12" fill="${color}" text-anchor="end">旗舰页数</text>
    <text x="${PAD.left + cw / 2}" y="${H - 6}" font-size="12" fill="var(--fg-muted)" text-anchor="middle">提交日期</text>
  </svg>
  </div>
  <p class="chart-desc" style="color:var(--fg-muted)">⚠️ 曲线中的下降并不代表内容缩水，而是因为 <b>评定标准提高</b>（如门槛字数或 PN 要求上调），导致部分页面从旗舰降为精品，待持续扩写后将重新升级。</p>`;
}

/* 质量分布堆叠面积图 */
function buildQualityStackChart(timeline) {
  // 只用有 quality_counts 的快照
  const data = timeline.filter(d => d.quality_counts);
  if (data.length < 2) {
    return `<p class="muted">（质量分布历史数据积累中，目前 ${data.length} 条，至少需要 2 条）</p>`;
  }

  const TIERS = [
    { key: 'stub',     color: 'rgba(252,129,129,0.85)',  label: '存根' },
    { key: 'basic',    color: 'rgba(251,211,141,0.85)',  label: '基础' },
    { key: 'standard', color: 'rgba(104,211,145,0.85)', label: '标准' },
    { key: 'featured', color: 'rgba(79,156,249,0.85)',  label: '精品' },
    { key: 'premium',  color: 'rgba(159,122,234,1)',     label: '旗舰' },
  ];

  const W = 900, H = 320, PAD = { top: 28, right: 120, bottom: 48, left: 68 };
  const cw = W - PAD.left - PAD.right;
  const ch = H - PAD.top - PAD.bottom;
  const n = data.length;

  const xScale = i => PAD.left + (i / (n - 1)) * cw;

  // 每个时间点各层累积高度
  const stacks = data.map(d => {
    const qc = d.quality_counts;
    let acc = 0;
    return TIERS.map(t => {
      const v = qc[t.key] || 0;
      const bot = acc;
      acc += v;
      return { v, bot, top: acc };
    });
  });

  const maxTotal = Math.max(...stacks.map(s => s[TIERS.length - 1].top));
  const yScale = v => PAD.top + ch - (v / (maxTotal || 1)) * ch;

  // 绘制每层堆叠多边形
  const layersSvg = TIERS.map((tier, ti) => {
    // 上边缘从左到右，下边缘从右到左
    const topPts = data.map((_, i) => `${xScale(i).toFixed(1)},${yScale(stacks[i][ti].top).toFixed(1)}`).join(' ');
    const botPts = data.map((_, i) => `${xScale(i).toFixed(1)},${yScale(stacks[i][ti].bot).toFixed(1)}`).reverse().join(' ');
    return `<polygon points="${topPts} ${botPts}" fill="${tier.color}" stroke="none"/>`;
  }).join('');

  // Y 轴刻度
  const yTicks = 5;
  const yTickHtml = Array.from({ length: yTicks + 1 }, (_, i) => {
    const v = maxTotal * i / yTicks;
    const y = yScale(v).toFixed(1);
    const label = Math.round(v).toLocaleString();
    return `<line x1="${PAD.left}" y1="${y}" x2="${PAD.left + cw}" y2="${y}" stroke="var(--border)" stroke-dasharray="3,3"/>
      <text x="${PAD.left - 8}" y="${y}" text-anchor="end" dominant-baseline="middle" font-size="11" fill="var(--fg-muted)">${label}</text>`;
  }).join('');

  // X 轴日期
  const step = Math.ceil(n / 8);
  const xTickHtml = data.map((d, i) => {
    if (i % step !== 0 && i !== n - 1) return '';
    return `<text x="${xScale(i).toFixed(1)}" y="${H - PAD.bottom + 16}" text-anchor="middle" font-size="11" fill="var(--fg-muted)">${(d.generated || '').slice(0, 10)}</text>`;
  }).join('');

  // 图例（右侧）
  const legendHtml = TIERS.slice().reverse().map((t, i) => {
    const y = PAD.top + i * 22;
    return `<rect x="${W - PAD.right + 8}" y="${y}" width="12" height="12" fill="${t.color}" rx="2"/>
      <text x="${W - PAD.right + 26}" y="${y + 10}" font-size="12" fill="var(--fg)">${t.label}</text>`;
  }).join('');

  return `
  <p class="chart-desc">各质量级别页面数量随时间的堆叠变化。数据从引入五级质量体系（2026-04-26）起积累。</p>
  <div class="k-chart-wrap">
  <svg viewBox="0 0 ${W} ${H}" style="width:100%;height:auto;display:block">
    ${yTickHtml}
    ${layersSvg}
    <line x1="${PAD.left}" y1="${PAD.top}" x2="${PAD.left}" y2="${PAD.top + ch}" stroke="var(--border)"/>
    ${xTickHtml}
    ${legendHtml}
  </svg>
  </div>`;
}
