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
    specialPages: [],  // 插件动态注册的 Special 页
  };
  core.registerSpecialPage = (def) => core.specialPages.push(def);
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

// plugins.json 由 wiki/scripts/build_plugins.py 自动生成，勿手动编辑。
// 添加新插件：在 plugins/<name>/plugin.json 中声明元数据，然后运行 build_plugins.py。
async function loadPlugins(core) {
  let manifest;
  try {
    const r = await fetch('plugins.json');
    if (!r.ok) return;
    manifest = await r.json();
  } catch (e) {
    return;
  }

  // 串行加载，保证 load_order 顺序（manifest 已由 build_plugins.py 排序）
  for (const entry of (manifest.plugins || [])) {
    const pluginPath = entry.entry;
    const pluginId   = entry.id;
    try {
      // 元数据优先读 plugin.json（entry 字段），JS 模块中不再需要重复声明
      const [mod, meta] = await Promise.all([
        import('../' + pluginPath),
        fetch(pluginPath.replace(/\/[^/]+$/, '/plugin.json'))
          .then(r => r.ok ? r.json() : {}).catch(() => ({})),
      ]);
      const p = mod.default;
      if (!p || typeof p.init !== 'function') {
        console.warn(`[plugin] ${pluginId} 缺少 default.init`);
        continue;
      }
      await p.init(core);
      core.plugins.push({
        id:          pluginId,
        name:        meta.name        || entry.name        || pluginId,
        version:     meta.version     || entry.version     || '?',
        description: meta.description || entry.description || '',
      });
      console.log(`[plugin] ${pluginId} v${meta.version || entry.version || '?'} loaded`);
    } catch (e) {
      console.error(`[plugin] ${pluginId} 加载失败:`, e);
    }
  }
}

boot();
