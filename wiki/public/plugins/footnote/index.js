/* footnote plugin — 渲染 [^id] 引用与 [^id]: 定义
 *
 * 依赖 markdown-it-footnote（本地 UMD 文件，无 CDN 依赖）。
 */

const LOCAL = new URL('./markdown-it-footnote.js', import.meta.url).href;

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

async function loadPlugin() {
  if (window.markdownitFootnote) return window.markdownitFootnote;
  await new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = LOCAL;
    s.onload = resolve;
    s.onerror = reject;
    document.head.appendChild(s);
  });
  return window.markdownitFootnote;
}

// 覆盖回跳锚点：将 ↩︎ (↩︎) 替换为 ↑
function patchAnchorRule(md) {
  md.renderer.rules.footnote_anchor = function (tokens, idx, options, env, slf) {
    let id = slf.rules.footnote_anchor_name(tokens, idx, options, env, slf);
    if (tokens[idx].meta.subId > 0) id += ':' + tokens[idx].meta.subId;
    return ' <a href="#fnref' + id + '" class="footnote-backref">↑</a>';
  };
}

export default {
  name: 'footnote',
  version: '1.0.0',
  async init(core) {
    try {
      const plugin = await loadPlugin();
      core.md.use(plugin);
      patchAnchorRule(core.md);
      const style = document.createElement('style');
      style.textContent = CSS;
      document.head.appendChild(style);
    } catch (e) {
      console.warn('[footnote] 插件加载失败，脚注将不渲染:', e);
    }
  },
};
