/* footnote plugin — 渲染 [^id] 引用与 [^id]: 定义
 *
 * 依赖 markdown-it-footnote（UMD，运行时从 jsDelivr 加载）。
 * 失败时静默降级（页面仍可正常显示，只是脚注不渲染）。
 */

const CDN = 'https://cdn.jsdelivr.net/npm/markdown-it-footnote@4.0.0/dist/markdown-it-footnote.js';

const CSS = `
.footnotes-sep { border: none; border-top: 1px solid #ccc; margin: 2em 0 0.5em; }
.footnotes { font-size: 0.88em; color: #555; }
.footnotes ol { padding-left: 1.5em; }
.footnotes li { margin: 0.25em 0; }
.footnote-ref { font-size: 0.8em; vertical-align: super; line-height: 0; }
.footnote-ref a,
.footnote-backref { color: #888; text-decoration: none; }
.footnote-ref a:hover,
.footnote-backref:hover { color: #333; text-decoration: underline; }
`;

function injectCSS() {
  const el = document.createElement('style');
  el.textContent = CSS;
  document.head.appendChild(el);
}

async function loadPlugin() {
  if (window.markdownItFootnote) return window.markdownItFootnote;
  await new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = CDN;
    s.onload = resolve;
    s.onerror = reject;
    document.head.appendChild(s);
  });
  return window.markdownItFootnote;
}

export default {
  name: 'footnote',
  version: '1.0.0',
  async init(core) {
    try {
      const plugin = await loadPlugin();
      core.md.use(plugin);
      injectCSS();
    } catch (e) {
      console.warn('[footnote] 插件加载失败，脚注将不渲染:', e);
    }
  },
};
