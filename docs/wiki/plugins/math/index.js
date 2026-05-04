/**
 * math.js — KaTeX 数学公式渲染插件
 *
 * 支持:
 *   - 行内: $...$ 或 \(...\)
 *   - 块级: $$...$$ 或 \[...\]
 */

const PLUGIN_NAME = 'math';
const KATEX_CSS = 'https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css';
const KATEX_JS  = 'https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js';
const AUTO_RENDER_JS = 'https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js';

async function loadKaTeX() {
  if (window.katex) return;
  // CSS
  if (!document.querySelector(`link[href="${KATEX_CSS}"]`)) {
    const link = document.createElement('link');
    link.rel = 'stylesheet'; link.href = KATEX_CSS;
    document.head.appendChild(link);
  }
  // JS
  await new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = KATEX_JS; s.onload = resolve; s.onerror = reject;
    document.head.appendChild(s);
  });
  await new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = AUTO_RENDER_JS; s.onload = resolve; s.onerror = reject;
    document.head.appendChild(s);
  });
}

function renderMath() {
  if (!window.renderMathInElement) return;
  const article = document.getElementById('article');
  if (!article) return;
  window.renderMathInElement(article, {
    delimiters: [
      { left: '$$', right: '$$', display: true },
      { left: '$',  right: '$',  display: false },
      { left: '\\[', right: '\\]', display: true },
      { left: '\\(', right: '\\)', display: false },
    ],
    throwOnError: false,
  });
}

export default {
  name: PLUGIN_NAME,
  version: '1.0.0',
  description: 'KaTeX 数学公式渲染（$...$ 行内，$$...$$ 块级）',

  async init(core) {
    await loadKaTeX();

    // 每次页面渲染后运行 KaTeX
    core.hooks.onAfterRender.add(async (html) => {
      // 稍延迟等 DOM 更新
      setTimeout(renderMath, 50);
      return html;
    });
  },
};
