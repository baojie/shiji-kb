/* 入口。 加载依赖 / 注册表 / 插件, 启动路由器。 */

import { createHooks } from './hooks.js';
import { loadRegistry } from './registry.js';
import { setupRouter } from './router.js';
import { createMarkdownIt } from './parser.js';
import { showFatal } from './util.js';

const HOOK_NAMES = [
  'onBoot',          // (core)                              启动完成, 插件已加载
  'onRoute',         // (raw, core) → string | null | undef 自定义路由
  'onBeforeRender',  // (body, {pid,meta,front}) → body     MD 源预处理
  'onAfterRender',   // (html, {pid,meta,front}) → html     HTML 后处理
  'onInfobox',       // (rows, front, meta) → rows          Infobox 行定制
];

async function boot() {
  const core = {
    hooks: createHooks(HOOK_NAMES),
    registry: null,
    md: null,
    plugins: [],
  };
  // 调试: 允许控制台访问 core
  window.__wiki = core;

  if (!window.markdownit || !window.jsyaml) {
    showFatal('依赖未加载 (markdown-it / js-yaml)');
    return;
  }
  core.md = createMarkdownIt();

  try {
    core.registry = await loadRegistry();
  } catch (e) {
    showFatal('无法加载 pages.json：' + e.message);
    return;
  }

  await loadPlugins(core);
  await core.hooks.onBoot.run(core);
  setupRouter(core);
}

async function loadPlugins(core) {
  let manifest;
  try {
    const r = await fetch('plugins.json');
    if (!r.ok) return;
    manifest = await r.json();
  } catch (e) {
    return; // 无 manifest = 无插件
  }
  for (const entry of (manifest.plugins || [])) {
    // 支持旧格式（字符串路径）和新格式（对象 {id, entry, ...}）
    const pluginPath = typeof entry === 'string' ? entry : entry.entry;
    const pluginId   = typeof entry === 'string' ? entry : entry.id;
    try {
      const mod = await import('../' + pluginPath);
      const p = mod.default;
      if (!p || typeof p.init !== 'function') {
        console.warn(`[plugin] ${pluginId} 缺少 default.init`);
        continue;
      }
      await p.init(core);
      core.plugins.push({
        name: p.name || pluginId,
        version: p.version || entry.version || '?',
        description: entry.description || '',
      });
      console.log(`[plugin] ${p.name || pluginId} v${p.version || '?'} loaded`);
    } catch (e) {
      console.error(`[plugin] ${pluginId} 加载失败:`, e);
    }
  }
}

boot();
