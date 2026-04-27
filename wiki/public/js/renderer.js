/* 页面 / 首页 / 404 / infobox 的 DOM 挂载。
 *
 * 解析逻辑 (frontmatter + MD + wikilink + hook) 全在 parser.js。
 * 本模块只把解析结果填到 DOM, 并管元数据/导航/状态栏。
 */

import { escapeHtml, TYPE_LABELS } from './util.js';
import { parseMarkdown } from './parser.js';
import { resolvePageId } from './registry.js';

/* 只在本地开发服务器上启用"想要"按钮 */
function isLocalhost() {
  return location.hostname === 'localhost' || location.hostname === '127.0.0.1';
}

/* 渲染"想要此页面"按钮 HTML + 绑定点击事件（异步注入）。
 * 仅在 localhost 下注入；远程部署时返回空字符串。 */
function injectWantButton(pid) {
  if (!isLocalhost()) return;
  const btn = document.createElement('button');
  btn.className = 'want-btn';
  btn.textContent = '⭐ 想要此页面';
  btn.title = '把这个页面加入 Butler 优先处理队列';
  btn.addEventListener('click', async () => {
    btn.disabled = true;
    btn.textContent = '提交中…';
    try {
      const res = await fetch('/api/want?page=' + encodeURIComponent(pid));
      const data = await res.json();
      if (data.added) {
        btn.textContent = '✅ 已加入队列';
        btn.classList.add('want-btn--done');
      } else {
        btn.textContent = '已在队列中';
        btn.classList.add('want-btn--exists');
      }
    } catch (e) {
      btn.textContent = '❌ 提交失败';
      btn.disabled = false;
    }
  });
  const article = document.getElementById('article');
  if (article) article.appendChild(btn);
}

function buildPager(current, total) {
  const mk = (n, label, cls = '') =>
    n === current
      ? `<span class="pager-current">${label}</span>`
      : `<a class="pager-link${cls ? ' ' + cls : ''}" href="#${encodeURIComponent('Special:Recent')}?page=${n}">${label}</a>`;
  const parts = [];
  if (current > 1) parts.push(mk(current - 1, '← 上一页', 'prev'));
  // 页码数字 (window of 5)
  const lo = Math.max(1, current - 2);
  const hi = Math.min(total, current + 2);
  if (lo > 1) parts.push(mk(1, '1'));
  if (lo > 2) parts.push('<span class="pager-gap">…</span>');
  for (let i = lo; i <= hi; i++) parts.push(mk(i, String(i)));
  if (hi < total - 1) parts.push('<span class="pager-gap">…</span>');
  if (hi < total) parts.push(mk(total, String(total)));
  if (current < total) parts.push(mk(current + 1, '下一页 →', 'next'));
  return `<nav class="pager">${parts.join(' ')}</nav>`;
}


/* 右侧栏图像区. 支持两种格式：
   单图: frontmatter image / image_caption / image_credit
   多图: frontmatter images: [{file, caption, credit}, ...] */
function renderSidebarPortrait(front) {
  const el = document.getElementById('sidebar-portrait');
  if (!el) return;

  // 统一成图片条目数组
  let items = [];
  if (Array.isArray(front.images) && front.images.length) {
    items = front.images.map(img => ({
      src:     img.file    || img.src || '',
      caption: img.caption || '',
      credit:  img.credit  || '',
    }));
  } else if (front.image) {
    items = [{
      src:     front.image,
      caption: front.image_caption || '',
      credit:  front.image_credit  || '',
    }];
  }

  if (!items.length) { el.hidden = true; el.innerHTML = ''; return; }

  el.hidden = false;
  el.innerHTML = items.map((img, i) => `
    <div class="portrait-item${i > 0 ? ' portrait-item--sep' : ''}">
      <a href="${escapeHtml(img.src)}" target="_blank" rel="noopener" class="portrait-zoom" title="点击放大">
        <img src="${escapeHtml(img.src)}"
             alt="${escapeHtml(img.caption || front.label || '')}"
             loading="lazy"
             onerror="this.closest('.portrait-item').style.display='none'">
      </a>
      ${img.caption ? `<figcaption>${escapeHtml(img.caption)}${img.credit ? `<br><span class="credit">${escapeHtml(img.credit)}</span>` : ''}</figcaption>` : ''}
    </div>`).join('');
}

function renderSidebarMap(front) {
  const el = document.getElementById('sidebar-map');
  if (!el) return;

  const coords = front.coords;
  if (!Array.isArray(coords) || coords.length < 2) {
    el.hidden = true; el.innerHTML = '';
    return;
  }

  const [lon, lat] = coords;
  const name = front.coords_name || front.label || '';
  const source = front.coords_source ? `<span class="map-source">${escapeHtml(front.coords_source)}</span>` : '';
  const delta = 0.4;
  const bbox = `${lon - delta},${lat - delta},${lon + delta},${lat + delta}`;
  const osmEmbed = `https://www.openstreetmap.org/export/embed.html?bbox=${bbox}&layer=mapnik&marker=${lat},${lon}`;

  el.hidden = false;
  el.innerHTML = `
    <iframe
      src="${osmEmbed}"
      style="width:100%;height:180px;border:none;display:block;"
      loading="lazy"
      title="${escapeHtml(name)}地图"
      referrerpolicy="no-referrer">
    </iframe>
    <div class="map-caption">${escapeHtml(name)}${source}</div>`;
}

function hideSidebar() {
  const sidebar = document.getElementById('sidebar');
  if (sidebar) sidebar.hidden = true;
  const ib = document.getElementById('infobox');
  if (ib) { ib.hidden = true; ib.innerHTML = ''; }
  const portrait = document.getElementById('sidebar-portrait');
  if (portrait) { portrait.hidden = true; portrait.innerHTML = ''; }
  const mapEl = document.getElementById('sidebar-map');
  if (mapEl) { mapEl.hidden = true; mapEl.innerHTML = ''; }
}

function fmtTimestamp(iso) {
  // ISO → "2026-04-22 16:10" (本地时区)
  try {
    const d = new Date(iso);
    const pad = (n) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ` +
      `${pad(d.getHours())}:${pad(d.getMinutes())}`;
  } catch { return iso; }
}

// 将事件页中 **主要人物**：XXX、YYY 和 **地点**：ZZZ 的纯文本转为 wikilink
const LINKIFY_FIELDS = new Set(['主要人物', '地点']);

function linkifyEventFields(articleEl, registry) {
  articleEl.querySelectorAll('strong').forEach(strong => {
    const label = strong.textContent.trim();
    if (!LINKIFY_FIELDS.has(label)) return;
    // 紧跟在 <strong> 后面的文本节点，形如 "：name1、name2"
    const textNode = strong.nextSibling;
    if (!textNode || textNode.nodeType !== Node.TEXT_NODE) return;
    const text = textNode.textContent;
    const sep = text[0];
    if (sep !== '：' && sep !== ':') return;
    const rest = text.slice(1).trim();
    if (!rest) return;

    // 分割：以 、或 ，分隔，保留分隔符样式
    const parts = rest.split(/([、，])/);
    const fragment = document.createDocumentFragment();
    fragment.appendChild(document.createTextNode(sep));
    for (const part of parts) {
      if (part === '、' || part === '，') {
        fragment.appendChild(document.createTextNode(part));
        continue;
      }
      const name = part.trim();
      if (!name) continue;
      const resolved = resolvePageId(name, registry);
      const a = document.createElement('a');
      a.href = `#${encodeURIComponent(resolved ? resolved[0] : name)}`;
      a.className = resolved ? 'wikilink resolved' : 'wikilink broken';
      if (!resolved) a.title = `未解析: ${name}`;
      a.textContent = name;
      fragment.appendChild(a);
    }
    textNode.replaceWith(fragment);
  });
}

export async function renderPage(core, pid, meta, mdText) {
  document.body.classList.remove('is-home');
  const { front, html, broken } = await parseMarkdown(core, mdText, { pid, meta });

  const tagsFooter = renderTagsFooter(front, meta);
  document.getElementById('article').innerHTML = html + tagsFooter;
  linkifyEventFields(document.getElementById('article'), core.registry);
  const infoboxContent = await renderInfobox(core, front, meta, pid);
  const ibEl = document.getElementById('infobox');
  const sidebarEl = document.getElementById('sidebar');
  if (infoboxContent) {
    const expandedInfobox = core.pnCitation ? core.pnCitation.expand(infoboxContent) : infoboxContent;
    ibEl.innerHTML = expandedInfobox;
    ibEl.hidden = false;
  } else {
    ibEl.innerHTML = '';
    ibEl.hidden = true;
  }
  renderSidebarPortrait(front);
  renderSidebarMap(front);
  const portraitEl = document.getElementById('sidebar-portrait');
  const mapEl = document.getElementById('sidebar-map');
  sidebarEl.hidden = ibEl.hidden && (!portraitEl || portraitEl.hidden) && (!mapEl || mapEl.hidden);

  const label = front.label || meta.label;
  document.getElementById('crumb').textContent =
    (TYPE_LABELS[meta.type] || meta.type) + ' / ' + label;
  document.title = label + ' · 史记 Wiki';

  // 源码查看链接 —— 在标题右侧注入，点击进入专用源码页
  const srcHref = `#?source=${encodeURIComponent(pid)}`;
  const h1 = document.getElementById('article').querySelector('h1');
  if (h1) {
    const existing = h1.querySelector('.src-tab');
    if (existing) existing.remove();
    const existingOrig = h1.querySelector('.orig-tab');
    if (existingOrig) existingOrig.remove();
    const tab = document.createElement('a');
    tab.href = srcHref;
    tab.className = 'src-tab';
    tab.textContent = '查看源码';
    h1.appendChild(tab);
    const histTab = document.createElement('a');
    histTab.href = `#?history=${encodeURIComponent(pid)}`;
    histTab.className = 'src-tab hist-tab';
    histTab.textContent = '修订历史';
    h1.appendChild(histTab);
    // 章节页额外注入"查看原文"链接，指向 GitHub Pages 渲染版
    if (meta.type === 'chapter') {
      const origTab = document.createElement('a');
      origTab.href = `https://baojie.github.io/shiji-kb/chapters/${encodeURIComponent(pid)}.html`;
      origTab.className = 'orig-tab';
      origTab.textContent = '查看原文';
      origTab.target = '_blank';
      origTab.rel = 'noopener';
      h1.appendChild(origTab);
    }
  }
  // footer 保留原始文件链接（开发用）
  const srcSpan = document.getElementById('src-info');
  srcSpan.innerHTML = `<a href="${escapeHtml(meta.path)}" class="src-link" target="_blank">源文件: ${escapeHtml(meta.path)}</a>`;
  // 清除残留 panel
  const srcPanel = document.getElementById('src-panel');
  if (srcPanel) srcPanel.remove();

  const brokenInfo = document.getElementById('broken-info');
  if (broken.length) {
    const uniq = [...new Set(broken)].sort();
    brokenInfo.innerHTML = ` · 断链 ${uniq.length}：` +
      uniq.map((b) => `<code>${escapeHtml(b)}</code>`).join(' ');
  } else {
    brokenInfo.textContent = '';
  }


  window.scrollTo(0, 0);
}

export async function renderSource(core, pid, meta) {
  document.body.classList.remove('is-home');
  const r = await fetch(meta.path);
  if (!r.ok) throw new Error('HTTP ' + r.status);
  const mdText = await r.text();

  const label = meta.label || pid;
  document.getElementById('crumb').textContent = '源码 / ' + label;
  document.title = label + ' 源码 · 史记 Wiki';

  document.getElementById('article').innerHTML = `
    <h1 class="src-view-title">${escapeHtml(label)} <span class="src-view-badge">源码</span></h1>
    <p class="muted"><a href="#${encodeURIComponent(pid)}">← 返回阅读页</a></p>
    <pre class="src-pre">${escapeHtml(mdText)}</pre>
  `;
  hideSidebar();
  document.getElementById('src-info').textContent = '';
  document.getElementById('broken-info').textContent = '';
  window.scrollTo(0, 0);
}

// 字段名 → 中文标签（仅用于改善显示，未收录的字段直接用 key 显示）
const FIELD_LABELS = {
  event_type: '事件类型', date: '日期', location: '地点', description: '描述',
  sources: '来源', event_ids: '事件编号', essay_type: '散文类型',
  author: '作者', chapter_no: '章节', canonical_name: '规范名',
  aliases: '别名', birth_ce: '生', death_ce: '卒', tags: '标签',
  pn: '原文位置',
};

// 纯内部字段，不对用户展示
const INFOBOX_SKIP = new Set([
  'id', 'label', 'title', 'type', 'featured', 'auto_generated',
  'quality_score', 'path', 'paragraph_refs',
  // 图片由 sidebar-portrait 渲染，无需在 infobox 表格里重复显示
  'image', 'image_caption', 'image_credit', 'image_prompt', 'images',
]);

export async function renderInfobox(core, front, meta, pid) {
  let rows = [];
  const handled = new Set();
  const push = (k, v) => {
    if (v != null && v !== '') {
      rows.push(`<tr><th>${escapeHtml(k)}</th><td>${v}</td></tr>`);
    }
  };

  // 特殊格式字段（需定制渲染，先处理）
  if (front.canonical_name && front.canonical_name !== (front.label || meta.label)) {
    push('规范名', escapeHtml(front.canonical_name));
  }
  handled.add('canonical_name');

  if (front.aliases && front.aliases.length) {
    push('别名', front.aliases.map(a => {
      const escaped = escapeHtml(a);
      if (a !== pid && core.registry.pages[a]) {
        return `<a href="#${encodeURIComponent(a)}">${escaped}</a>`;
      }
      return escaped;
    }).join(' · '));
  }
  handled.add('aliases');

  push('类型', TYPE_LABELS[front.type || meta.type] || front.type || meta.type);
  handled.add('type');

  if (front.birth_ce != null) {
    push('生', front.birth_ce < 0 ? `前 ${-front.birth_ce}` : String(front.birth_ce));
  }
  handled.add('birth_ce');

  if (front.death_ce != null) {
    push('卒', front.death_ce < 0 ? `前 ${-front.death_ce}` : String(front.death_ce));
  }
  handled.add('death_ce');

  if (front.tags && front.tags.length) {
    push('标签', front.tags.map(escapeHtml).join(' · '));
  }
  handled.add('tags');

  // 遍历所有剩余字段，通用渲染
  for (const [key, val] of Object.entries(front)) {
    if (handled.has(key) || INFOBOX_SKIP.has(key)) continue;
    if (val == null || val === '') continue;
    const label = FIELD_LABELS[key] || key;
    if (key === 'pn') {
      // 半角括号转全角，供 pn-citation 插件展开为链接；不 escape
      const s = String(val).trim().replace(/\(/g, '（').replace(/\)/g, '）');
      push(label, s);
    } else if (Array.isArray(val)) {
      if (val.length) push(label, val.map(v => escapeHtml(String(v))).join(' · '));
    } else if (typeof val === 'object') {
      // 嵌套对象（如 paragraph_refs）跳过
    } else {
      push(label, escapeHtml(String(val)));
    }
  }

  // Plugin hook: 允许改写 infobox 行
  rows = await core.hooks.onInfobox.run(rows, front, meta);

  if (!rows.length) return null;
  return `<h2>${escapeHtml(front.label || meta.label)}</h2>
    <table>${rows.join('')}</table>`;
}

export function renderHome(core) {
  const pages = core.registry.pages;
  const ids = Object.keys(pages);

  // 精品页面: 按类型分桶保证多样性，featured=true 优先，再按 quality_score
  const allPages = ids.map((id) => ({ id, ...pages[id] }));
  const scoreOf = (p) => (p.featured ? 1000 : 0) + (p.quality_score || 0);
  const byScore = (a, b) => scoreOf(b) - scoreOf(a);

  // 各类型上限：person≤6，story≤4，sanwen≤3，overview/concept/chapter 各≤2
  const caps = { person: 6, story: 4, sanwen: 3, overview: 2, concept: 2, chapter: 2 };
  const SKIP_TYPES = new Set(['redirect', 'disambiguation', 'year', 'place', 'event', 'special', 'list', '侯国', 'skill']);
  const counts = {};
  const featured = [];
  const candidates = [...allPages].sort(byScore);
  // 第一轮：按上限从各桶各取
  for (const p of candidates) {
    if (featured.length >= 18) break;
    const t = p.type || '';
    if (SKIP_TYPES.has(t) || !(t in caps)) continue;
    const n = counts[t] || 0;
    if (n >= caps[t]) continue;
    counts[t] = n + 1;
    featured.push(p);
  }
  // 第二轮：剩余位用高分补足
  if (featured.length < 18) {
    const used = new Set(featured.map((p) => p.id));
    for (const p of candidates) {
      if (featured.length >= 18) break;
      if (used.has(p.id)) continue;
      if (SKIP_TYPES.has(p.type || '')) continue;
      featured.push(p);
    }
  }

  const featuredHtml = featured.map(renderFeaturedCard).join('');

  document.getElementById('article').innerHTML =
    `<div class="wiki-home">
      <h1>史记 Wiki</h1>
      <p class="tagline">从 130 篇《史记》提取的 ${ids.length} 个实体页面, 可按姓名或别名搜索</p>

      <div class="search-box">
        <input id="wiki-search" type="search"
          placeholder="搜索人名或别名 (如 '刘邦', '高祖', '沛公')"
          autocomplete="off" autofocus>
        <ul id="search-results" hidden></ul>
      </div>

      <h2>精品页面 <small class="muted">(按质量排)</small></h2>
      <div class="featured-grid">${featuredHtml}</div>

      <nav class="home-links">
        <a href="#${encodeURIComponent('About')}" class="home-link home-link--about">关于本 Wiki</a>
        <a href="#${encodeURIComponent('Special:AllPages')}" class="home-link">全部 ${ids.length} 页 →</a>
        <a href="#${encodeURIComponent('Special:Recent')}" class="home-link">最近修订 →</a>
        <a href="#${encodeURIComponent('Special:Random')}" class="home-link">随机页 →</a>
      </nav>

      <p class="home-disclaimer">⚠️ 本 Wiki 所有内容由 AI 机器人自动生成，难免有错误和疏漏。后台机器人 Butler 在持续巡逻纠错，但请勿用于学术引用。如发现问题欢迎<a href="https://github.com/baojie/shiji-kb/issues/new" target="_blank" rel="noopener">提交 Issue</a>。</p>

      <div id="k-panel" class="k-panel"><span class="muted">正在加载知识量...</span></div>
    </div>`;

  // 知识量仪表板：latest + timeline sparkline
  Promise.all([
    fetch('data/knowledge_latest.json').then(r => r.ok ? r.json() : null).catch(() => null),
    fetch('data/knowledge_timeline.jsonl').then(r => r.ok ? r.text() : '').catch(() => ''),
  ]).then(([k, tlText]) => {
    if (!k) { document.getElementById('k-panel').innerHTML = ''; return; }
    const panel = document.getElementById('k-panel');
    if (!panel) return;
    const pct = (k.link_hit_rate * 100).toFixed(1);
    const kb  = (k.total_bytes / 1024).toFixed(0);

    // sparkline from timeline
    const pts = tlText.trim().split('\n')
      .map(l => { try { return JSON.parse(l); } catch { return null; } })
      .filter(d => d && d.K > 100)        // filter bad K=0 entries
      .slice(-30);                         // last 30 snapshots
    let sparkSvg = '';
    if (pts.length >= 2) {
      const W = 120, H = 28, pad = 2;
      const ks = pts.map(p => p.K);
      const mn = Math.min(...ks), mx = Math.max(...ks);
      const range = mx - mn || 1;
      const coords = pts.map((p, i) => {
        const x = pad + (i / (pts.length - 1)) * (W - pad * 2);
        const y = H - pad - ((p.K - mn) / range) * (H - pad * 2);
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      }).join(' ');
      sparkSvg = `<svg class="k-spark" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}"
        aria-label="知识量增长曲线">
        <polyline points="${coords}" fill="none" stroke="var(--accent)" stroke-width="1.5"
          stroke-linejoin="round" stroke-linecap="round"/>
        <circle cx="${+coords.split(' ').at(-1).split(',')[0]}"
                cy="${+coords.split(' ').at(-1).split(',')[1]}"
                r="2.5" fill="var(--accent)"/>
      </svg>`;
    }

    panel.innerHTML = `
      <h3>📊 <a href="#${encodeURIComponent('Special:Statistics')}" class="k-title-link">知识量</a> <span class="k-value">${k.K.toLocaleString()}</span>
        ${sparkSvg}
      </h3>
      <div class="k-row">
        <span>${k.page_count} 页</span>
        <span>${(k.quality_counts?.premium ?? k.featured_count ?? 0)} 旗舰</span>
        <span>链接命中 ${pct}%</span>
        <span>${kb} KB</span>
        <span>${k.total_revisions} 修订</span>
      </div>
      <div class="k-row k-top">
        TOP: ${k.top10_pages.slice(0, 5).map(t =>
          `<a href="#${encodeURIComponent(t.pid)}">${t.pid}</a>(${t.k})`
        ).join(' · ')}
      </div>
      <div class="k-row muted">快照: ${k.generated}</div>
    `;
  }).catch(() => { const p = document.getElementById('k-panel'); if (p) p.innerHTML = ''; });

  document.body.classList.add('is-home');
  hideSidebar();
  document.getElementById('crumb').textContent = '首页';
  document.title = '史记 Wiki';
  document.getElementById('src-info').textContent = 'pages.json';
  document.getElementById('broken-info').textContent = '';

  // 搜索交互
  const input = document.getElementById('wiki-search');
  const resultsEl = document.getElementById('search-results');
  input.addEventListener('input', () => {
    const q = input.value.trim();
    if (!q) {
      resultsEl.hidden = true; resultsEl.innerHTML = ''; return;
    }
    const matches = searchPages(q, core.registry);
    resultsEl.hidden = false;
    if (matches.length === 0) {
      resultsEl.innerHTML =
        `<li class="search-empty">没有匹配: "${escapeHtml(q)}"</li>`;
      return;
    }
    resultsEl.innerHTML = matches.map((m) => {
      const labelHtml = escapeHtml(m.entry.label);
      const altHtml = m.matched !== m.entry.label
        ? `<span class="match-alt">[${escapeHtml(m.matched)}]</span>` : '';
      const meta = m.entry.total_refs != null
        ? `<span class="match-meta">${m.entry.total_refs} 次 / ${m.entry.total_chapters} 篇</span>`
        : '';
      return `<li class="search-result-item">
        <a href="#${encodeURIComponent(m.pid)}">
          <span class="match-label">${labelHtml}</span>${altHtml}${meta}
        </a>
      </li>`;
    }).join('');
  });
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      const first = resultsEl.querySelector('a');
      if (first) location.hash = first.getAttribute('href').slice(1);
    } else if (e.key === 'Escape') {
      input.value = ''; resultsEl.hidden = true; resultsEl.innerHTML = '';
    }
  });
}

/**
 * 每页底部分类标签 (语义化):
 *   <footer class="entity-tags" role="contentinfo">
 *     <a class="tag tag-type" rel="tag">人名</a>
 *     <a class="tag" rel="tag">汉朝</a>...
 *   </footer>
 *
 * 来源:
 *   - type (frontmatter.type 或 meta.type): 主分类, 显示为突出样式
 *   - tags[]: 自由标签
 *
 * rel="tag" 是 HTML5 microformats 的标签链接关系, 搜索引擎和
 * 阅读器可识别. href 指向 "#?tag=<name>"; 未来可加 tag 路由.
 */
function renderTagsFooter(front, meta) {
  const type = front.type || meta.type || '';
  const typeLabel = TYPE_LABELS[type] || type;
  const tags = front.tags || [];
  if (!typeLabel && tags.length === 0) return '';

  const parts = [];
  if (typeLabel) {
    parts.push(
      `<a class="tag tag-type" rel="tag" data-kind="type"` +
      ` href="#?type=${encodeURIComponent(type)}">${escapeHtml(typeLabel)}</a>`
    );
  }
  for (const tag of tags) {
    parts.push(
      `<a class="tag" rel="tag" data-kind="tag"` +
      ` href="#?tag=${encodeURIComponent(tag)}">${escapeHtml(tag)}</a>`
    );
  }
  return `<footer class="entity-tags" role="contentinfo" aria-label="分类">
    <span class="tag-label">分类</span>
    ${parts.join(' ')}
  </footer>`;
}

function renderFeaturedCard(p) {
  const life = p.lifespan || null;
  let lifeS = '';
  if (life && life.birth != null && life.death != null) {
    const b = life.birth < 0 ? `前 ${-life.birth}` : String(life.birth);
    const d = life.death < 0 ? `前 ${-life.death}` : String(life.death);
    lifeS = `<div class="card-life">${b} — ${d}</div>`;
  }
  const meta = p.total_refs != null
    ? `<div class="card-meta">
         <strong>${p.total_refs}</strong> 次出现 ·
         <strong>${p.total_chapters}</strong> 篇
       </div>` : '';
  const aliasPreview = (p.aliases || []).slice(0, 3).join(' · ');
  const aliasHtml = aliasPreview
    ? `<div class="card-aliases">${escapeHtml(aliasPreview)}</div>` : '';
  const imgHtml = p.image
    ? `<div class="card-thumb"><img src="${escapeHtml(p.image)}" alt="${escapeHtml(p.label)}" loading="lazy"></div>` : '';
  return `<a class="featured-card${p.image ? ' has-thumb' : ''}" href="#${encodeURIComponent(p.id)}">
    ${imgHtml}<div class="card-body">
      <h3>${escapeHtml(p.label)}</h3>
      ${lifeS}${meta}${aliasHtml}
    </div>
  </a>`;
}

function searchPages(q, registry) {
  const lower = q.toLowerCase();
  // type priority: core entities first, long-form content last
  const TYPE_PRIO = { person: 40, state: 35, dynasty: 35, official: 30,
    place: 30, institution: 25, identity: 25, xing: 25, shihao: 20,
    concept: 15, artifact: 15, biology: 15, tribe: 15,
    event: 5, story: 5, sanwen: 5, chapter: 5, taishigongyue: 5,
    redirect: -20 };

  function matchScore(surface) {
    const s = surface.toLowerCase();
    if (s === lower)            return 100;
    if (s.startsWith(lower))   return 70;
    if (s.includes(lower))     return 30;
    return 0;
  }

  // pid → { surface, score }
  const best = new Map();
  function tryMatch(pid, surface) {
    const sc = matchScore(surface);
    if (!sc) return;
    const prev = best.get(pid);
    if (!prev || sc > prev.score) best.set(pid, { surface, score: sc });
  }

  for (const [pid, entry] of Object.entries(registry.pages)) {
    tryMatch(pid, pid);
    if (entry.label) tryMatch(pid, entry.label);
  }
  for (const [alias, pid] of Object.entries(registry.alias_index || {})) {
    tryMatch(pid, alias);
  }

  return [...best.entries()]
    .map(([pid, { surface, score }]) => {
      const entry = registry.pages[pid];
      const typePrio = TYPE_PRIO[entry?.type] ?? 10;
      const refs = entry?.total_refs ?? 0;
      return { pid, entry, matched: surface, _sort: score * 100 + typePrio * 10 + Math.min(refs, 9) };
    })
    .sort((a, b) => b._sort - a._sort)
    .slice(0, 15)
    .map(({ pid, entry, matched }) => ({ pid, entry, matched }));
}

/**
 * 分类页 (类 MediaWiki Category): 列出某 type/tag 下的所有页面.
 *   URL: #?type=<type>  或  #?tag=<tag>
 */
export function renderCategory(core, kind, value) {
  const pages = core.registry.pages;
  const matches = [];
  for (const [pid, entry] of Object.entries(pages)) {
    if (kind === 'type' && entry.type === value) {
      matches.push({ pid, ...entry });
    } else if (kind === 'tag' && (entry.tags || []).includes(value)) {
      matches.push({ pid, ...entry });
    }
  }
  // refs 降序, 无 refs 按 id
  matches.sort((a, b) => {
    const ra = a.total_refs || 0, rb = b.total_refs || 0;
    if (ra !== rb) return rb - ra;
    return a.pid.localeCompare(b.pid, 'zh');
  });

  const titleKind = kind === 'type' ? '类型' : '标签';
  const displayValue = kind === 'type'
    ? (TYPE_LABELS[value] || value) : value;

  const itemsHtml = matches.map((p) => {
    const firstChar = p.label ? p.label[0] : '';
    const life = p.lifespan;
    let lifeS = '';
    if (life && life.birth != null && life.death != null) {
      const b = life.birth < 0 ? `前 ${-life.birth}` : String(life.birth);
      const d = life.death < 0 ? `前 ${-life.death}` : String(life.death);
      lifeS = `<span class="cat-life">${b}—${d}</span>`;
    }
    const meta = p.total_refs != null
      ? `<span class="cat-meta">${p.total_refs} 次 / ${p.total_chapters} 篇</span>` : '';
    return `<li data-alpha="${getPinyinInitial(p.label)}">
      <a href="#${encodeURIComponent(p.pid)}" class="cat-link">${escapeHtml(p.label)}</a>
      ${lifeS}${meta}
    </li>`;
  }).join('');

  // 超过 100 项时附加 A-Z 过滤栏
  const filterBar = matches.length > 100
    ? buildFirstCharBarHtml(matches.map(p => p.label || p.pid))
    : '';

  const body = matches.length > 0
    ? `<div class="category-filterable">${filterBar}<ol class="category-list">${itemsHtml}</ol></div>`
    : '<p class="category-empty">此分类下暂无页面。</p>';

  document.getElementById('article').innerHTML =
    `<nav class="category-crumb"><a href="#">← 首页</a></nav>
     <h1>${escapeHtml(titleKind)}：${escapeHtml(displayValue)}</h1>
     <p class="category-summary">共 <strong>${matches.length}</strong> 个页面</p>
     ${body}`;

  // A: 绑定首字过滤
  const filterable = document.querySelector('.category-filterable');
  if (filterable) setupFirstCharFilter(filterable);

  document.body.classList.add('is-home');
  hideSidebar();
  document.getElementById('crumb').textContent = `${titleKind}：${displayValue}`;
  document.title = `${titleKind} ${displayValue} · 史记 Wiki`;
  document.getElementById('src-info').textContent =
    `pages.json (筛选: ${kind}=${value})`;
  document.getElementById('broken-info').textContent = '';
  window.scrollTo(0, 0);
}

/**
 * 最近修订页 (#?recent[&page=N]): recent.jsonl 是滚动窗口（最新 1000 条），单次 fetch 即可.
 */
export async function renderRecent(core, pageNum = 1) {
  const DISPLAY_LIMIT = 500;
  const PAGE_SIZE = 50;

  const bust = `?v=${Math.floor(Date.now() / 60000)}`;
  const r = await fetch('recent.jsonl' + bust);
  if (!r.ok) throw new Error('HTTP ' + r.status);
  const text = await r.text();
  const allEntries = text.split('\n').filter(l => l.trim()).map(l => JSON.parse(l));

  // recent.jsonl 保留最近 1000 条（滚动窗口），取最新 DISPLAY_LIMIT 条逆序显示
  const recent500 = allEntries.slice(-DISPLAY_LIMIT).reverse();

  const totalEntries = recent500.length;
  const totalPages = Math.max(1, Math.ceil(totalEntries / PAGE_SIZE));
  pageNum = Math.min(Math.max(1, pageNum), totalPages);

  const start = (pageNum - 1) * PAGE_SIZE;
  const entries = recent500.slice(start, start + PAGE_SIZE);

  const rows = entries.map((e) => {
    const pageLink = `<a href="#${encodeURIComponent(e.page)}">${escapeHtml(e.page)}</a>`;
    const histLink = `<a href="#?history=${encodeURIComponent(e.page)}">历史</a>`;
    const revLink = `<a href="#?revision=${encodeURIComponent(e.page)}&rev=${encodeURIComponent(e.rev_id)}">${escapeHtml(e.rev_id)}</a>`;
    const diffLink = `<a href="#?diff=${encodeURIComponent(e.page)}&rev=${encodeURIComponent(e.rev_id)}">diff</a>`;
    return `<tr>
      <td class="rc-time">${escapeHtml(fmtTimestamp(e.timestamp))}</td>
      <td class="rc-page">${pageLink}</td>
      <td class="rc-author">${escapeHtml(e.author)}</td>
      <td class="rc-summary">${escapeHtml(e.summary || '')}</td>
      <td class="rc-rev">${revLink} · ${diffLink} · ${histLink}</td>
    </tr>`;
  }).join('');

  const pagerHtml = totalPages > 1 ? buildPager(pageNum, totalPages) : '';

  const uniquePages = new Set(recent500.map(e => e.page)).size;
  const logNote = allEntries.length > DISPLAY_LIMIT ? `（窗口共 ${allEntries.length} 条，显示最新 ${DISPLAY_LIMIT} 条）` : '';

  const body = entries.length === 0
    ? '<p class="category-empty">暂无修订记录。</p>'
    : `<table class="recent-changes">
        <thead><tr><th>时间</th><th>页面</th><th>作者</th><th>摘要</th><th>修订</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
      ${pagerHtml}`;

  document.getElementById('article').innerHTML =
    `<nav class="category-crumb"><a href="#">← 首页</a></nav>
     <h1>最近修订 <small class="muted">第 ${pageNum}/${totalPages} 页</small></h1>
     <p class="category-summary">显示 <strong>${totalEntries}</strong> 条修订 · <strong>${uniquePages}</strong> 个页面 ${escapeHtml(logNote)}</p>
     ${body}`;

  document.body.classList.add('is-home');
  hideSidebar();
  document.getElementById('crumb').textContent = '最近修订';
  document.title = '最近修订 · 史记 Wiki';
  document.getElementById('src-info').textContent = 'recent.jsonl';
  document.getElementById('broken-info').textContent = '';
  window.scrollTo(0, 0);
}

/**
 * 单页修订历史 (#?history=<page>): 读 history/<page>.jsonl（JSONL 正序，末行最新）.
 */
export async function renderHistory(core, page) {
  const r = await fetch(`history/${encodeURIComponent(page)}.jsonl`);
  if (!r.ok) throw new Error('HTTP ' + r.status);
  const text = await r.text();
  const revs = text.split('\n').filter(l => l.trim()).map(l => JSON.parse(l));
  // JSONL 正序（最旧在前），逆序显示（最新在前）
  const revsDesc = revs.slice().reverse();
  const latestRevId = revs.length ? revs[revs.length - 1].rev_id : null;

  const rows = revsDesc.map((rev) => {
    const isLatest = rev.rev_id === latestRevId;
    const tag = isLatest ? ' <span class="rev-badge">最新</span>' : '';
    const revLink = `<a href="#?revision=${encodeURIComponent(page)}&rev=${encodeURIComponent(rev.rev_id)}">${escapeHtml(rev.rev_id)}</a>`;
    const diffLink = rev.parent_rev
      ? `<a href="#?diff=${encodeURIComponent(page)}&rev=${encodeURIComponent(rev.rev_id)}">diff</a>`
      : '<span class="muted">diff</span>';
    return `<tr>
      <td class="rc-time">${escapeHtml(fmtTimestamp(rev.timestamp))}${tag}</td>
      <td class="rc-author">${escapeHtml(rev.author)}</td>
      <td class="rc-summary">${escapeHtml(rev.summary || '')}</td>
      <td class="rc-size">${rev.size} B</td>
      <td class="rc-diff">${diffLink}</td>
      <td class="rc-rev">${revLink}${tag}</td>
    </tr>`;
  }).join('');

  document.getElementById('article').innerHTML =
    `<nav class="category-crumb">
       <a href="#">← 首页</a> ·
       <a href="#${encodeURIComponent(page)}">← ${escapeHtml(page)}</a>
     </nav>
     <h1>${escapeHtml(page)} · 修订历史</h1>
     <p class="category-summary">共 <strong>${revs.length}</strong> 条修订</p>
     <table class="recent-changes">
       <thead><tr><th>时间</th><th>作者</th><th>摘要</th><th>大小</th><th>修订</th></tr></thead>
       <tbody>${rows}</tbody>
     </table>`;

  document.body.classList.add('is-home');
  hideSidebar();
  document.getElementById('crumb').textContent = `修订历史 / ${page}`;
  document.title = `${page} 修订历史 · 史记 Wiki`;
  document.getElementById('src-info').textContent = `history/${page}.jsonl`;
  document.getElementById('broken-info').textContent = '';
  window.scrollTo(0, 0);
}

/**
 * 单条历史版本 (#?revision=<page>&rev=<id>): 从 history/<page>.jsonl 中查找对应行.
 */
export async function renderRevision(core, page, revId) {
  const r = await fetch(`history/${encodeURIComponent(page)}.jsonl`);
  if (!r.ok) throw new Error('HTTP ' + r.status);
  const text = await r.text();
  const revs = text.split('\n').filter(l => l.trim()).map(l => JSON.parse(l));
  const rev = revs.find((x) => x.rev_id === revId);
  if (!rev) throw new Error(`rev not found: ${revId}`);
  if (rev.content == null) throw new Error(`rev missing content: ${revId}`);
  const mdText = rev.content;

  const meta = (core.registry.pages[page]) || { type: 'meta', label: page, path: '' };
  const { html } = await parseMarkdown(core, mdText, { pid: page, meta });

  const banner = `<div class="rev-banner">
    <strong>历史版本</strong> · 修订 <code>${escapeHtml(revId)}</code> ·
    <a href="#${encodeURIComponent(page)}">→ 当前版本</a> ·
    <a href="#?history=${encodeURIComponent(page)}">→ 全部修订</a> ·
    <a href="#?diff=${encodeURIComponent(page)}&rev=${encodeURIComponent(revId)}">→ vs 上版 diff</a>
  </div>`;

  document.getElementById('article').innerHTML = banner + html;
  hideSidebar();
  document.getElementById('crumb').textContent = `${page} @ ${revId}`;
  document.title = `${page} @ ${revId} · 史记 Wiki`;
  document.getElementById('src-info').textContent = `history/${page}.jsonl @ ${revId}`;
  document.getElementById('broken-info').textContent = '';
  window.scrollTo(0, 0);
}

/**
/* 从 label 列表提取唯一首字，返回过滤栏 HTML（首字 ≤ 3 个时不生成）。*/
/* 拼音首字母映射表（覆盖史记人名常用首字） */
const PINYIN_INITIAL = {
  B: '伯卜扁比白百薄褒鲍',
  C: '城崔春晁曹曾楚樗淳程蔡触鉏陈',
  D: '丁东帝杜段澹窦翟董邓',
  E: '二',
  F: '冯夫扶樊肥范',
  G: '公勾灌甘盖管葛虢郭高',
  H: '侯后壶扈桓汉浑淮狐胡衡闳霍韩黄',
  J: '介剧姬季晋景汲箕荆贾蹇鞠',
  K: '孔括蒯',
  L: '乐刘卢吕娄嫪廉李栗栾梁老落蔺路郦酈里陆骊鲁龙',
  M: '冒孟枚毛缪蒙闵',
  N: '南宁聂',
  P: '平庞彭辟',
  Q: '屈戚秦骑齐',
  R: '任穰',
  S: '叔司商姒孙宋审慎桑申石示苏随',
  T: '唐太屠田缇',
  W: '伍卫吴文王魏',
  X: '侠信先夏宣弦徐新荀萧西许郤项须',
  Y: '严义伊优原夷尧晏杨燕由羊英虞袁豫颜',
  Z: '专中主仲召周子宰州庄张智朱章臧赵邹郅郑钟长',
};

function getPinyinInitial(label) {
  const ch = label && label[0];
  if (!ch) return '#';
  for (const [letter, chars] of Object.entries(PINYIN_INITIAL)) {
    if (chars.includes(ch)) return letter;
  }
  return '#';
}

function buildFirstCharBarHtml(labels) {
  const used = new Set(labels.map(l => getPinyinInitial(l)).filter(c => c !== '#'));
  const ordered = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('').filter(l => used.has(l));
  if (ordered.length <= 2) return '';
  const btns = ['全', ...ordered].map((c, i) =>
    `<button class="firstchar-btn${i === 0 ? ' active' : ''}" data-char="${c}">${c}</button>`
  ).join('');
  return `<div class="firstchar-bar" role="group" aria-label="按拼音首字母过滤">${btns}</div>`;
}

function setupFirstCharFilter(container) {
  const bar = container.querySelector('.firstchar-bar');
  if (!bar) return;
  bar.addEventListener('click', e => {
    const btn = e.target.closest('.firstchar-btn');
    if (!btn) return;
    const ch = btn.dataset.char;
    bar.querySelectorAll('.firstchar-btn').forEach(b => b.classList.toggle('active', b === btn));
    container.querySelectorAll('li[data-alpha]').forEach(li => {
      li.hidden = ch !== '全' && li.dataset.alpha !== ch;
    });
  });
}

/**
 * Special:AllPages — 分面浏览器
 * 左侧分面（类型 / 标签），右侧分页结果列表，顶部文字搜索。
 */
export function renderAll(core) {
  const pages = core.registry.pages;

  // ── 构建全局分面数据 ─────────────────────────────────────────────
  const allEntries = Object.entries(pages)
    .filter(([id]) => !id.startsWith('Special:'))
    .map(([id, p]) => ({ id, ...p }));

  const typeCounts      = {};
  const tagCounts       = {};
  const essayTypeCounts = {};
  const eventTypeCounts = {};
  const qualityCounts   = {};
  const sourceCounts    = {};
  for (const p of allEntries) {
    const t = p.type || 'unknown';
    typeCounts[t] = (typeCounts[t] || 0) + 1;
    // jun_title: true 的页面也计入 jun 分面（无论其本身 type 是 person/official 等）
    if (p.jun_title && t !== 'jun') {
      typeCounts['jun'] = (typeCounts['jun'] || 0) + 1;
    }
    for (const tag of (p.tags || [])) tagCounts[tag] = (tagCounts[tag] || 0) + 1;
    if (p.essay_type)  essayTypeCounts[p.essay_type]  = (essayTypeCounts[p.essay_type]  || 0) + 1;
    if (p.event_type)  eventTypeCounts[p.event_type]  = (eventTypeCounts[p.event_type]  || 0) + 1;
    const q = p.quality || 'stub';
    qualityCounts[q] = (qualityCounts[q] || 0) + 1;
    for (const src of (p.sources || [])) sourceCounts[src] = (sourceCounts[src] || 0) + 1;
  }
  const orderedEssayTypes = Object.keys(essayTypeCounts).sort(
    (a, b) => essayTypeCounts[b] - essayTypeCounts[a]
  );
  const orderedEventTypes = Object.keys(eventTypeCounts).sort(
    (a, b) => eventTypeCounts[b] - eventTypeCounts[a]
  );
  // 章节来源分面：按页面数降序，只显示出现 ≥ 3 次的
  const orderedSources = Object.entries(sourceCounts)
    .filter(([, c]) => c >= 3)
    .sort((a, b) => b[1] - a[1])
    .map(([s]) => s);

  // 只显示出现 ≥ 5 次的 tag
  const topTags = Object.entries(tagCounts)
    .filter(([, c]) => c >= 5)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 30)
    .map(([t]) => t);

  const typeOrder = [
    // 核心人事
    'person', 'event', 'story',
    // 地理政治
    'place', 'state', '侯国', 'dynasty',
    // 文献
    'chapter', 'overview', 'sanwen', 'taishigongyue', 'chengyu', 'book',
    // 社会制度
    'official', 'identity', 'institution', 'tribe', 'ritual', 'legal',
    // 物质文化
    'artifact', 'biology', 'astronomy', 'quantity',
    // 时间
    'time', 'year',
    // 思想概念
    'concept', 'mythical', 'verb',
    // 专项索引
    'shihao', 'bihui', 'xing', 'jun',
    // 页面管理
    'disambiguation', 'redirect', 'list', 'topic', 'skill', 'overview',
    'meta', 'special', 'unknown',
  ];
  // 类型分面：按条数降序排列
  const orderedTypes = Object.keys(typeCounts).sort(
    (a, b) => typeCounts[b] - typeCounts[a]
  );

  // ── URL 状态 ──────────────────────────────────────────────────────
  function getState() {
    const hash = decodeURIComponent(location.hash.slice(1));
    const qi   = hash.indexOf('?');
    const p    = new URLSearchParams(qi >= 0 ? hash.slice(qi + 1) : '');
    return {
      types:   p.getAll('type'),
      essays:  p.getAll('essay'),
      events:  p.getAll('event'),
      tags:    p.getAll('tag'),
      sources: p.getAll('source'),
      qlevel:  p.get('q') || '',
      search:  p.get('s') || '',
      page:    Math.max(1, parseInt(p.get('page') || '1', 10)),
    };
  }

  function buildHash(s) {
    const p = new URLSearchParams();
    s.types.forEach(t   => p.append('type',   t));
    s.essays.forEach(e  => p.append('essay',  e));
    s.events.forEach(e  => p.append('event',  e));
    s.tags.forEach(t    => p.append('tag',    t));
    s.sources.forEach(s => p.append('source', s));
    if (s.qlevel) p.set('q', s.qlevel);
    if (s.search) p.set('s',    s.search);
    if (s.page > 1) p.set('page', String(s.page));
    const qs = p.toString();
    return '#' + encodeURIComponent('Special:AllPages') + (qs ? '?' + qs : '');
  }

  // ── 过滤 ──────────────────────────────────────────────────────────
  const PAGE_SIZE = 50;

  function applyFilters(s) {
    let r = allEntries;
    if (s.types.length)   r = r.filter(p =>
      s.types.includes(p.type || 'unknown') ||
      (s.types.includes('jun') && p.jun_title)
    );
    if (s.essays.length)  r = r.filter(p => s.essays.includes(p.essay_type || ''));
    if (s.events.length)  r = r.filter(p => s.events.includes(p.event_type || ''));
    if (s.tags.length)    r = r.filter(p => s.tags.every(t => (p.tags || []).includes(t)));
    if (s.sources.length) r = r.filter(p => s.sources.every(src => (p.sources || []).includes(src)));
    if (s.qlevel) r = r.filter(p => (p.quality || 'stub') === s.qlevel);
    if (s.search) {
      const kw = s.search.toLowerCase();
      r = r.filter(p =>
        p.id.toLowerCase().includes(kw) ||
        (p.label || '').toLowerCase().includes(kw) ||
        (p.aliases || []).some(a => a.toLowerCase().includes(kw))
      );
    }
    return r.slice().sort((a, b) =>
      (b.k_score || 0) - (a.k_score || 0) ||
      (a.label || a.id).localeCompare(b.label || b.id, 'zh')
    );
  }

  // ── 分面栏 ────────────────────────────────────────────────────────
  function renderFacets(s) {
    const typeItems = orderedTypes.map(t => {
      const active = s.types.includes(t);
      return `<label class="facet-item${active ? ' active' : ''}">
        <input type="checkbox" data-facet="type" data-val="${escapeHtml(t)}"${active ? ' checked' : ''}>
        <span class="facet-label">${escapeHtml(TYPE_LABELS[t] || t)}</span>
        <span class="facet-count">${typeCounts[t]}</span>
      </label>`;
    }).join('');

    const essayItems = orderedEssayTypes.map(et => {
      const active = s.essays.includes(et);
      return `<label class="facet-item${active ? ' active' : ''}">
        <input type="checkbox" data-facet="essay" data-val="${escapeHtml(et)}"${active ? ' checked' : ''}>
        <span class="facet-label">${escapeHtml(et)}</span>
        <span class="facet-count">${essayTypeCounts[et]}</span>
      </label>`;
    }).join('');

    const tagItems = topTags.map(tag => {
      const active = s.tags.includes(tag);
      return `<label class="facet-item${active ? ' active' : ''}">
        <input type="checkbox" data-facet="tag" data-val="${escapeHtml(tag)}"${active ? ' checked' : ''}>
        <span class="facet-label">${escapeHtml(tag)}</span>
        <span class="facet-count">${tagCounts[tag]}</span>
      </label>`;
    }).join('');

    const eventItems = orderedEventTypes.map(et => {
      const active = s.events.includes(et);
      return `<label class="facet-item${active ? ' active' : ''}">
        <input type="checkbox" data-facet="event" data-val="${escapeHtml(et)}"${active ? ' checked' : ''}>
        <span class="facet-label">${escapeHtml(et)}</span>
        <span class="facet-count">${eventTypeCounts[et]}</span>
      </label>`;
    }).join('');

    const QUALITY_LEVELS = [
      ['premium',  '旗舰'],
      ['featured', '精品'],
      ['standard', '标准'],
      ['basic',    '基础'],
      ['stub',     '存根'],
    ];
    const qItems = QUALITY_LEVELS.map(([val, lbl]) =>
      `<label class="facet-item${s.qlevel === val ? ' active' : ''}">
        <input type="radio" name="qlevel" data-facet="q" data-val="${val}"${s.qlevel === val ? ' checked' : ''}>
        <span class="facet-label">${lbl}</span>
        <span class="facet-count">${qualityCounts[val] || 0}</span>
      </label>`
    ).join('');

    const sourceItems = orderedSources.map(src => {
      const active = s.sources.includes(src);
      return `<label class="facet-item${active ? ' active' : ''}">
        <input type="checkbox" data-facet="source" data-val="${escapeHtml(src)}"${active ? ' checked' : ''}>
        <span class="facet-label">${escapeHtml(src)}</span>
        <span class="facet-count">${sourceCounts[src]}</span>
      </label>`;
    }).join('');

    const essaySection = orderedEssayTypes.length ? `
      <details class="facet-group" open>
        <summary class="facet-group-title">散文类型</summary>
        <div class="facet-items">${essayItems}</div>
      </details>` : '';

    const eventSection = orderedEventTypes.length ? `
      <details class="facet-group" open>
        <summary class="facet-group-title">事件类型</summary>
        <div class="facet-items">${eventItems}</div>
      </details>` : '';

    const sourceSection = orderedSources.length ? `
      <details class="facet-group" open>
        <summary class="facet-group-title">所在章节</summary>
        <div class="facet-items facet-tags">${sourceItems}</div>
      </details>` : '';

    return `<aside class="facet-panel">
      <div class="facet-reset-row">
        <strong>筛选</strong>
        <button class="facet-reset-btn" id="facet-reset">清除</button>
      </div>
      <details class="facet-group" open>
        <summary class="facet-group-title">类型</summary>
        <div class="facet-items">${typeItems}</div>
      </details>${essaySection}${eventSection}${sourceSection}
      <details class="facet-group" open>
        <summary class="facet-group-title">标签</summary>
        <div class="facet-items facet-tags">${tagItems}</div>
      </details>
      <details class="facet-group">
        <summary class="facet-group-title">内容质量</summary>
        <div class="facet-items">${qItems}</div>
      </details>
    </aside>`;
  }

  // ── 结果列表 ──────────────────────────────────────────────────────
  function renderResults(results, s) {
    const total      = results.length;
    const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
    const page       = Math.min(s.page, totalPages);
    const slice      = results.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

    const QUALITY_BADGE = { premium: '旗舰', featured: '精品' };
    const items = slice.map(p => {
      const badge = QUALITY_BADGE[p.quality] ? `<span class="res-quality res-quality-${p.quality}">${QUALITY_BADGE[p.quality]}</span>` : '';
      const qs    = p.k_score != null ? `<span class="res-score">K=${p.k_score}</span>` : '';
      const tags  = (p.tags || []).slice(0, 4).map(t => `<span class="res-tag">${escapeHtml(t)}</span>`).join('');
      return `<li class="res-item">
        <a class="res-title" href="#${encodeURIComponent(p.id)}">${escapeHtml(p.label || p.id)}</a>
        <div class="res-meta"><span class="res-type">${escapeHtml(TYPE_LABELS[p.type] || p.type || '')}</span>${badge}${qs}${tags}</div>
      </li>`;
    }).join('');

    let pagerHtml = '';
    if (totalPages > 1) {
      const mkLink = (pg, label) =>
        `<a class="pager-btn${pg === page ? ' active' : ''}" href="${buildHash({ ...s, page: pg })}">${label}</a>`;
      const prev  = page > 1 ? mkLink(page - 1, '←') : '';
      const next  = page < totalPages ? mkLink(page + 1, '→') : '';
      const nums  = Array.from({ length: totalPages }, (_, i) => i + 1)
        .filter(n => n <= 2 || n >= totalPages - 1 || Math.abs(n - page) <= 2)
        .reduce((acc, n, i, arr) => {
          if (i > 0 && n - arr[i - 1] > 1) acc.push('…');
          acc.push(n); return acc;
        }, [])
        .map(n => typeof n === 'string' ? `<span class="pager-ellipsis">…</span>` : mkLink(n, n))
        .join('');
      pagerHtml = `<div class="pager">${prev}${nums}${next}</div>`;
    }

    const badge = [...s.types.map(t => TYPE_LABELS[t] || t), ...s.essays, ...s.events, ...s.tags,
                   ...s.sources, ...(s.qlevel ? [s.qlevel] : []), ...(s.search ? [`"${s.search}"`] : [])].join(' · ');
    return `<div class="res-header">
        <span class="res-count">共 <strong>${total}</strong> 个页面${badge ? ' · ' + badge : ''}</span>
      </div>
      <ul class="res-list">${items || '<li class="res-empty">无匹配结果</li>'}</ul>
      ${pagerHtml}`;
  }

  // ── 移动端过滤栏 ─────────────────────────────────────────────────
  function renderMobileFilters(s) {
    const typeOptions = [`<option value="">全部类型</option>`]
      .concat(orderedTypes.map(t =>
        `<option value="${escapeHtml(t)}"${s.types[0] === t ? ' selected' : ''}>${escapeHtml(TYPE_LABELS[t] || t)} (${typeCounts[t]})</option>`
      )).join('');
    return `
      <div class="ap-mobile-filters">
        <input id="ap-search" class="allpages-search" type="search"
          placeholder="搜索页面名称或别名…" value="${escapeHtml(s.search)}">
        <select id="ap-type-select" class="ap-type-select">
          ${typeOptions}
        </select>
      </div>`;
  }

  // ── 主渲染 ────────────────────────────────────────────────────────
  function render() {
    const s       = getState();
    const results = applyFilters(s);
    const article = document.getElementById('article');
    const isMobile = window.innerWidth < 700;

    if (isMobile) {
      article.innerHTML = `
        <nav class="category-crumb"><a href="#">← 首页</a></nav>
        <h1>Special:AllPages</h1>
        <div class="allpages-mobile">
          ${renderMobileFilters(s)}
          <div id="ap-results">${renderResults(results, s)}</div>
        </div>`;
    } else {
      article.innerHTML = `
        <nav class="category-crumb"><a href="#">← 首页</a></nav>
        <h1>Special:AllPages</h1>
        <div class="allpages-layout">
          ${renderFacets(s)}
          <div class="allpages-main">
            <div class="allpages-search-row">
              <input id="ap-search" class="allpages-search" type="search"
                placeholder="搜索页面名称或别名…" value="${escapeHtml(s.search)}">
            </div>
            <div id="ap-results">${renderResults(results, s)}</div>
          </div>
        </div>`;
    }

    document.body.classList.add('is-home');
    hideSidebar();
    document.getElementById('crumb').textContent = 'Special:AllPages';
    document.title = '全部页面 · 史记 Wiki';
    document.getElementById('src-info').textContent = `共 ${allEntries.length} 页`;
    document.getElementById('broken-info').textContent = '';
    window.scrollTo(0, 0);

    // 搜索框（防抖 200ms，桌面/移动共用）
    let timer;
    article.querySelector('#ap-search').addEventListener('input', e => {
      clearTimeout(timer);
      timer = setTimeout(() => {
        const ns = getState();
        ns.search = e.target.value.trim();
        ns.page = 1;
        history.replaceState(null, '', buildHash(ns));
        document.getElementById('ap-results').innerHTML = renderResults(applyFilters(ns), ns);
      }, 200);
    });

    if (isMobile) {
      // 移动端：类型下拉框
      article.querySelector('#ap-type-select').addEventListener('change', e => {
        const ns = getState();
        ns.types = e.target.value ? [e.target.value] : [];
        ns.page = 1;
        history.replaceState(null, '', buildHash(ns));
        document.getElementById('ap-results').innerHTML = renderResults(applyFilters(ns), ns);
      });
    } else {
      // 桌面端：分面 checkbox / radio
      article.querySelectorAll('input[data-facet]').forEach(cb => {
        cb.addEventListener('change', () => {
          const ns = getState();
          const { facet, val } = cb.dataset;
          if (facet === 'type') {
            ns.types  = cb.checked ? [...new Set([...ns.types,  val])] : ns.types.filter(t => t !== val);
          } else if (facet === 'essay') {
            ns.essays = cb.checked ? [...new Set([...ns.essays, val])] : ns.essays.filter(t => t !== val);
          } else if (facet === 'event') {
            ns.events = cb.checked ? [...new Set([...ns.events, val])] : ns.events.filter(t => t !== val);
          } else if (facet === 'tag') {
            ns.tags    = cb.checked ? [...new Set([...ns.tags,    val])] : ns.tags.filter(t => t !== val);
          } else if (facet === 'source') {
            ns.sources = cb.checked ? [...new Set([...ns.sources, val])] : ns.sources.filter(t => t !== val);
          } else if (facet === 'q') {
            ns.qlevel = cb.checked ? val : '';
          }
          ns.page = 1;
          history.replaceState(null, '', buildHash(ns));
          document.getElementById('ap-results').innerHTML = renderResults(applyFilters(ns), ns);
          article.querySelectorAll('.facet-item').forEach(lbl => {
            const inp = lbl.querySelector('input');
            lbl.classList.toggle('active', !!(inp && inp.checked));
          });
        });
      });

      // 清除按钮
      article.querySelector('#facet-reset')?.addEventListener('click', () => {
        history.replaceState(null, '', buildHash({ types: [], essays: [], events: [], tags: [], sources: [], qlevel: '', search: '', page: 1 }));
        render();
      });
    }
  }

  render();
}


/**
 * 版本 diff 页 (#?diff=<page>&rev=<rev_id>): 显示该版 vs parent_rev 的行级 diff.
 * user-req-8: 每个版本应可看上一个版本的 diff.
 */
export async function renderDiff(core, page, revId) {
  const r = await fetch(`history/${encodeURIComponent(page)}.jsonl`);
  if (!r.ok) throw new Error('HTTP ' + r.status);
  const text = await r.text();
  const revs = text.split('\n').filter(l => l.trim()).map(l => JSON.parse(l));
  const cur = revs.find((x) => x.rev_id === revId);
  if (!cur) throw new Error(`rev not found: ${revId}`);

  let prevContent = '';
  let prevRev = null;
  if (cur.parent_rev) {
    prevRev = revs.find((x) => x.rev_id === cur.parent_rev);
    if (prevRev) prevContent = prevRev.content || '';
  }
  const curContent = cur.content || '';

  const chunks = computeLineDiff(prevContent, curContent);
  const diffHtml = renderDiffChunks(chunks);

  const header = `<nav class="category-crumb">
    <a href="#${encodeURIComponent(page)}">← ${escapeHtml(page)}</a>
    <span class="sep">·</span>
    <a href="#?history=${encodeURIComponent(page)}">所有修订</a>
    <span class="sep">·</span>
    <a href="#?revision=${encodeURIComponent(page)}&rev=${encodeURIComponent(revId)}">查看该版</a>
  </nav>`;

  const meta = `<div class="diff-meta">
    <div><strong>本版:</strong> <code>${escapeHtml(revId)}</code> · ${escapeHtml(fmtTimestamp(cur.timestamp))} · ${escapeHtml(cur.author)}</div>
    ${prevRev
      ? `<div><strong>上版:</strong> <code>${escapeHtml(prevRev.rev_id)}</code> · ${escapeHtml(fmtTimestamp(prevRev.timestamp))} · ${escapeHtml(prevRev.author)}</div>`
      : '<div><em>首个版本 (无上版), 全部显示为新增</em></div>'}
    <div class="diff-summary">
      <span class="diff-added">+${chunks.filter((c) => c.type === 'add').length}</span>
      ·
      <span class="diff-removed">-${chunks.filter((c) => c.type === 'del').length}</span>
      行 · 摘要: <em>${escapeHtml(cur.summary || '(无)')}</em>
    </div>
  </div>`;

  document.getElementById('article').innerHTML = header +
    `<h1>版本差异 <small class="muted">${escapeHtml(page)}</small></h1>` +
    meta + `<div class="diff-body">${diffHtml}</div>`;

  hideSidebar();
  document.getElementById('crumb').textContent = `${page} diff ${revId}`;
  document.title = `${page} diff · 史记 Wiki`;
  document.getElementById('src-info').textContent = `history/${page}.jsonl (diff ${revId} vs ${cur.parent_rev || 'null'})`;
  document.getElementById('broken-info').textContent = '';
  window.scrollTo(0, 0);
}

// 行级 LCS-based diff. 返回 [{type: 'same'|'add'|'del', line}, ...] 按新序.
function computeLineDiff(oldText, newText) {
  const o = oldText.split('\n');
  const n = newText.split('\n');
  const m = o.length, nn = n.length;
  // DP
  const dp = Array(m + 1).fill(null).map(() => new Int32Array(nn + 1));
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= nn; j++) {
      dp[i][j] = o[i - 1] === n[j - 1]
        ? dp[i - 1][j - 1] + 1
        : Math.max(dp[i - 1][j], dp[i][j - 1]);
    }
  }
  const res = [];
  let i = m, j = nn;
  while (i > 0 && j > 0) {
    if (o[i - 1] === n[j - 1]) { res.push({ type: 'same', line: o[i - 1] }); i--; j--; }
    else if (dp[i - 1][j] >= dp[i][j - 1]) { res.push({ type: 'del', line: o[i - 1] }); i--; }
    else { res.push({ type: 'add', line: n[j - 1] }); j--; }
  }
  while (i > 0) { res.push({ type: 'del', line: o[i - 1] }); i--; }
  while (j > 0) { res.push({ type: 'add', line: n[j - 1] }); j--; }
  return res.reverse();
}

function renderDiffChunks(chunks) {
  return chunks.map((c) => {
    const cls = 'diff-line diff-' + c.type;
    const sign = { same: ' ', add: '+', del: '-' }[c.type];
    return `<div class="${cls}"><span class="diff-sign">${sign}</span><span class="diff-text">${escapeHtml(c.line)}</span></div>`;
  }).join('');
}

export function renderNotFound(core, target) {
  document.getElementById('article').innerHTML =
    `<h1>页面不存在</h1>
     <p>未找到页面 <code>${escapeHtml(target)}</code>。</p>
     <p><a href="#">回到首页</a></p>`;
  hideSidebar();
  document.getElementById('crumb').textContent = '未找到';
  document.title = '未找到 · 史记 Wiki';
  document.getElementById('src-info').textContent = '';
  document.getElementById('broken-info').textContent = '';
  injectWantButton(target);
}
