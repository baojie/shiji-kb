/* Wikilink 保护 / 展开。
 *
 * 为何两步走:
 *   MD 表格 '|' 会和 [[target|text]] 里的 '|' 冲突。
 *   渲染前用私用区占位符替换 [[...]], MD 跑完再换回真实 <a> 标签。
 */

const PH_OPEN = '\uE010';
const PH_CLOSE = '\uE011';
const WIKILINK_RE = /\[\[([^\[\]|]+?)(?:\|([^\[\]]+?))?\]\]/g;
const PH_RE = /\uE010(\d+)\uE011/g;

export function protectWikilinks(body) {
  const tokens = [];
  const protectedText = body.replace(WIKILINK_RE, (_, target, text) => {
    tokens.push({ target: target.trim(), text: text ? text.trim() : null });
    return PH_OPEN + (tokens.length - 1) + PH_CLOSE;
  });
  return { protectedText, tokens };
}

/**
 * @param {string} html   MD 渲染后的 HTML (含占位符)
 * @param {Array}  tokens protectWikilinks 返回的 token 数组
 * @param {object} opts
 *   @param {string}   opts.selfId   当前页 id, 用于 self 样式
 *   @param {function} opts.resolve  (target) => [pid, entry] | null
 *   @param {function} opts.onBroken (target) => void  断链记录回调
 *   @param {function} opts.escape   HTML 转义函数
 */
export function expandWikilinks(html, tokens, opts) {
  const { selfId, resolve, onBroken, escape } = opts;
  return html.replace(PH_RE, (_, idxStr) => {
    const { target, text } = tokens[+idxStr];
    let display = text != null ? text : target;
    if (text == null && display.includes('/')) {
      display = display.split('/', 2)[1];
    }
    const resolved = resolve(target);
    if (!resolved) {
      onBroken(target);
      // 断链仍可点击（导航到目标，页面会显示 404），仅样式不同
      return `<a class="wikilink broken" href="#${encodeURIComponent(target)}" data-target="${escape(target)}"` +
        ` title="未解析: ${escape(target)}">${escape(display)}</a>`;
    }
    const [pid] = resolved;
    const cls = pid === selfId ? 'wikilink self' : 'wikilink resolved';
    return `<a class="${cls}" href="#${encodeURIComponent(pid)}">${escape(display)}</a>`;
  });
}
