/**
 * backlinks — 反向引用插件
 *
 * onBoot:         一次性 fetch backlinks.json，挂到 core.backlinks
 * onAfterRender:  在文章末尾注入"被以下页面引用"区块
 *
 * backlinks.json 结构（由 scripts/build_backlinks.py 生成）：
 *   { "pageId": [{"id":"...", "label":"...", "type":"..."}, ...] }
 */

const TYPE_LABELS = {
  person:   '人名',
  place:    '地名',
  state:    '邦国',
  official: '官职',
  identity: '身份',
  event:    '事件',
  concept:  '概念',
  chapter:  '章节',
  topic:    '主题',
};

function renderBacklinks(backlinks, pid) {
  const entries = backlinks[pid];
  if (!entries || entries.length === 0) return '';

  // 按 type 分组
  const groups = {};
  for (const e of entries) {
    const g = TYPE_LABELS[e.type] || e.type || '其他';
    (groups[g] || (groups[g] = [])).push(e);
  }

  const groupHtml = Object.entries(groups)
    .sort(([a], [b]) => a.localeCompare(b, 'zh'))
    .map(([groupName, items]) => {
      const links = items
        .map(e => `<a class="wikilink resolved bl-link" href="#${encodeURIComponent(e.id)}">${e.label}</a>`)
        .join('');
      return `<span class="bl-group"><span class="bl-group-label">${groupName}</span>${links}</span>`;
    })
    .join('');

  return `
<section class="backlinks" id="backlinks">
  <h2 class="bl-heading">被以下页面引用</h2>
  <div class="bl-body">${groupHtml}</div>
</section>`;
}

export default {
  async init(core) {
    // ── onBoot: 加载 backlinks.json ──
    core.hooks.onBoot.add(async (c) => {
      try {
        const r = await fetch('backlinks.json');
        if (r.ok) {
          c.backlinks = await r.json();
        } else {
          c.backlinks = {};
        }
      } catch {
        c.backlinks = {};
      }
    });

    // ── onAfterRender: 注入反向引用区块 ──
    core.hooks.onAfterRender.add((html, { pid }) => {
      if (!core.backlinks) return html;
      const section = renderBacklinks(core.backlinks, pid);
      if (!section) return html;
      // 插入到文章末尾（historyLink 之前，如有的话）
      const historyMarker = '<p class="page-history-link">';
      const idx = html.lastIndexOf(historyMarker);
      if (idx !== -1) {
        return html.slice(0, idx) + section + html.slice(idx);
      }
      return html + section;
    });
  },
};
