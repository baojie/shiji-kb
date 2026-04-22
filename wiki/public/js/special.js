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
        ? { key: p, name: p, desc: '' }
        : { key: p.settings_key || p.id, name: p.name || p.id, desc: p.description || '', id: p.id }
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
  const pluginRows = core.plugins.length
    ? core.plugins.map(p =>
        `<tr><td><code>${escapeHtml(p.name)}</code></td><td>${escapeHtml(p.version || '?')}</td><td class="muted">${escapeHtml(p.description || '')}</td></tr>`
      ).join('')
    : '<tr><td colspan="3" class="muted">（无已激活插件）</td></tr>';

  const s = loadSettings();
  const allDefs = PLUGIN_DEFS.map(p => {
    const enabled = s?.plugins?.[p.key] === true;
    return `<tr>
      <td><strong>${escapeHtml(p.name)}</strong></td>
      <td>${enabled ? '✅ 已启用' : '⭕ 已安装，未启用'}</td>
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
