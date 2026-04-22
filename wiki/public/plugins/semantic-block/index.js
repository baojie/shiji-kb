/**
 * semantic-block.js — 语义块插件（客户端）
 *
 * 功能：
 *   1. inline infobox（aside.infobox.inline）添加折叠/展开按钮
 *   2. 读取 .semantic-meta[data-meta] 将元数据暴露到 window.__pageMeta[]
 *   3. 提供 core.semanticBlock API 供其他插件查询当前页元数据
 *
 * 默认启用（不依赖 settings_key 开关），始终运行。
 */

const PLUGIN_NAME = 'semantic-block';

// ---------- inline infobox 折叠 ----------

function initInlineInfoboxes() {
  document.querySelectorAll('aside.infobox.inline').forEach((aside) => {
    const title = aside.querySelector('h2');
    if (!title) return;

    // 折叠按钮
    const btn = document.createElement('button');
    btn.className = 'infobox-toggle';
    btn.setAttribute('aria-label', '折叠');
    btn.textContent = '▲';
    title.appendChild(btn);

    const table = aside.querySelector('table');
    let collapsed = false;

    btn.addEventListener('click', () => {
      collapsed = !collapsed;
      if (table) table.style.display = collapsed ? 'none' : '';
      btn.textContent = collapsed ? '▼' : '▲';
      btn.setAttribute('aria-label', collapsed ? '展开' : '折叠');
      aside.classList.toggle('collapsed', collapsed);
    });
  });
}

// ---------- meta 块读取 ----------

function collectPageMeta() {
  const results = [];
  document.querySelectorAll('.semantic-meta[data-meta]').forEach((el) => {
    try {
      const data = JSON.parse(el.getAttribute('data-meta').replace(/&#39;/g, "'"));
      results.push(data);
    } catch (_) { /* 忽略解析失败 */ }
  });
  window.__pageMeta = results;
  return results;
}

// ---------- 注入样式 ----------

const INLINE_STYLE = `
aside.infobox.inline .infobox-toggle {
  float: right;
  background: none;
  border: none;
  cursor: pointer;
  font-size: .75em;
  color: var(--fg-muted, #666);
  padding: 0 0 0 .4em;
  line-height: 1;
}
aside.infobox.inline .infobox-toggle:hover { color: var(--accent, #7a1f1f); }
aside.infobox.inline.collapsed { opacity: .85; }
`;

function injectStyle() {
  if (document.getElementById('semantic-block-style')) return;
  const style = document.createElement('style');
  style.id = 'semantic-block-style';
  style.textContent = INLINE_STYLE;
  document.head.appendChild(style);
}

// ---------- 插件入口 ----------

export default {
  name: PLUGIN_NAME,
  version: '1.0.0',
  description: '语义块：inline infobox 折叠 + meta 元数据读取',

  async init(core) {
    injectStyle();

    const run = () => {
      initInlineInfoboxes();
      const meta = collectPageMeta();
      // 将 API 挂到 core，供其他插件使用
      if (core) {
        core.semanticBlock = {
          getPageMeta: () => window.__pageMeta || [],
        };
      }
      if (meta.length) {
        console.debug(`[semantic-block] 读取到 ${meta.length} 个 meta 块`);
      }
    };

    if (core?.hooks?.onAfterRender) {
      core.hooks.onAfterRender.tap(async (html) => {
        setTimeout(run, 0);
        return html;
      });
    } else {
      // 无 core 时（直接加载静态页）直接执行
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', run);
      } else {
        run();
      }
    }
  },
};
