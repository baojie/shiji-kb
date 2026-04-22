/* Markdown 解析主流水线。
 *
 * parseMarkdown(core, mdText, ctx) 做完整链路:
 *   1. splitFrontmatter  → {front, body}
 *   2. hook onBeforeRender(body)
 *   3. protectWikilinks  (避开 MD 表格 '|' 冲突)
 *   4. markdown-it 渲染
 *   5. expandWikilinks   (占位符 → <a>)
 *   6. hook onAfterRender(html)
 *
 * 返回: {front, html, broken[]}
 */

import { splitFrontmatter } from './frontmatter.js';
import { protectWikilinks, expandWikilinks } from './wikilink.js';
import { resolvePageId } from './registry.js';
import { escapeHtml } from './util.js';

export function createMarkdownIt() {
  if (!window.markdownit) {
    throw new Error('markdown-it 未加载');
  }
  return window.markdownit({
    html: false,
    linkify: true,
    typographer: true,
    breaks: false,
  });
}

export async function parseMarkdown(core, mdText, ctx = {}) {
  const { pid, meta } = ctx;
  const { front, body: rawBody } = splitFrontmatter(mdText);

  // Hook: MD 源预处理 (e.g. semantic 插件展开 :::query)
  const body = await core.hooks.onBeforeRender.run(rawBody, { pid, meta, front });

  // 占位符保护 wikilink
  const { protectedText, tokens } = protectWikilinks(body);

  // MD → HTML
  let html = core.md.render(protectedText);

  // 展开 wikilink 占位符为 <a>
  const broken = [];
  html = expandWikilinks(html, tokens, {
    selfId: pid,
    resolve: (target) => resolvePageId(target, core.registry),
    onBroken: (t) => broken.push(t),
    escape: escapeHtml,
  });

  // Hook: HTML 后处理
  html = await core.hooks.onAfterRender.run(html, { pid, meta, front });

  return { front, html, broken };
}
