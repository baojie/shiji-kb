/**
 * pn-citation — PN 引文链接插件
 *
 * 将以下两种引文形式渲染为指向章节原文段落锚的链接：
 *
 *   （[[040_楚世家|040-082]]）          ← 标准写法（wikilink 已展开为 <a>）
 *   （040-082）                          ← 纯文本写法
 *   （040-082意旨）                      ← 带意旨标注
 *
 * 目标 URL:
 *   https://baojie.github.io/shiji-kb/chapters/040_楚世家.html#pn-82
 *
 * Hook: onAfterRender（HTML 后处理，wikilink 已展开）
 */

const PLUGIN_NAME = 'pn-citation';
const CHAPTERS_BASE = 'https://baojie.github.io/shiji-kb/chapters/';

// 匹配 wikilink 展开后的形式：（<a ...>040-082</a>）
// 支持 class="wikilink resolved/broken/self"
// pn 格式：普通段落号（数字，可带小数）或表格行号（r + 数字）
const RE_PN = '(r?\\d+(?:\\.\\d+)?)';
const RE_WIKILINK = new RegExp(`（<a\\s[^>]*class="wikilink[^"]*"[^>]*>(\\d{3})-${RE_PN}<\\/a>(?:意旨)?）`, 'g');

// 匹配纯文本形式：（040-12）（040-082）（022-r7）（040-082意旨）
const RE_PLAIN = new RegExp(`（(\\d{3})-${RE_PN}(?:意旨)?）`, 'g');

function pnToInt(pnStr) {
  if (pnStr.startsWith('r')) return pnStr;          // 表格行：r7 → #pn-r7
  return pnStr.includes('.') ? pnStr : String(parseInt(pnStr, 10));
}

function buildUrl(chNum, pnStr, chapterMap) {
  const chFile = chapterMap[chNum];
  if (!chFile) return null;
  const pn = pnToInt(pnStr);
  return `${CHAPTERS_BASE}${encodeURIComponent(chFile)}.html#pn-${pn}`;
}

function expandCitations(html, chapterMap) {
  // 1. 替换 wikilink 展开形式
  html = html.replace(RE_WIKILINK, (_match, chNum, pnStr) => {
    const url = buildUrl(chNum, pnStr, chapterMap);
    if (!url) return _match;
    return `（<a class="pn-citation" href="${url}" target="_blank" title="${chNum}-${pnStr} 原文">${chNum}-${pnStr}</a>）`;
  });

  // 2. 替换纯文本形式（排除已在 <a> 标签内的）
  // 用占位符标记 <a>...</a> 内部，避免误处理
  const anchors = [];
  const protected_ = html.replace(/<a[\s\S]*?<\/a>/g, (m) => {
    anchors.push(m);
    return `\x00anchor${anchors.length - 1}\x00`;
  });

  const expanded = protected_.replace(RE_PLAIN, (_match, chNum, pnStr) => {
    const url = buildUrl(chNum, pnStr, chapterMap);
    if (!url) return _match;
    return `（<a class="pn-citation" href="${url}" target="_blank" title="${chNum}-${pnStr} 原文">${chNum}-${pnStr}</a>）`;
  });

  // 还原 anchor 占位符
  return expanded.replace(/\x00anchor(\d+)\x00/g, (_, i) => anchors[+i]);
}

export default {
  name: PLUGIN_NAME,
  version: '1.0.0',

  async init(core) {
    let chapterMap = null;

    // 启动时加载章节映射表
    core.hooks.onBoot.add(async () => {
      try {
        const r = await fetch('data/chapter_map.json');
        chapterMap = await r.json();
        console.log(`[${PLUGIN_NAME}] 加载 ${Object.keys(chapterMap).length} 个章节映射`);
      } catch (e) {
        console.warn(`[${PLUGIN_NAME}] 无法加载 chapter_map.json:`, e);
      }
    });

    // HTML 后处理：展开引文链接
    core.hooks.onAfterRender.add((html) => {
      if (!chapterMap) return html;
      return expandCitations(html, chapterMap);
    });

    // 暴露给其他插件（如 semantic-block）用于 DOM 注入后的补充展开
    core.pnCitation = {
      expand: (html) => chapterMap ? expandCitations(html, chapterMap) : html,
    };
  },
};
