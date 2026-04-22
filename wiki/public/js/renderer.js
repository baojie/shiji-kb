/* 页面 / 首页 / 404 / infobox 的 DOM 挂载。
 *
 * 解析逻辑 (frontmatter + MD + wikilink + hook) 全在 parser.js。
 * 本模块只把解析结果填到 DOM, 并管元数据/导航/状态栏。
 */

import { escapeHtml, TYPE_LABELS } from './util.js';
import { parseMarkdown } from './parser.js';

function buildPager(current, total) {
  const mk = (n, label, cls = '') =>
    n === current
      ? `<span class="pager-current">${label}</span>`
      : `<a class="pager-link${cls ? ' ' + cls : ''}" href="#?recent&page=${n}">${label}</a>`;
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

/* 从 recent-archive 取 [offset, offset+count) 的 entries.
 * 月份文件按 index.json 排好最新在前, 每个文件 entries[] 内部也按时间倒序. */
async function fetchFromArchive(months, offset, count) {
  const out = [];
  let skip = offset;
  for (const m of months) {
    if (m.count <= skip) { skip -= m.count; continue; }
    const r = await fetch(`recent-archive/${encodeURIComponent(m.name)}.json`);
    if (!r.ok) continue;
    const data = await r.json();
    // 归档文件按插入顺序, 较老的在后面. 但插入时每次 overflow 用 .append, 旧的在前,
    // 所以我们要反转 (最新在前) 再 slice.
    const entries = (data.entries || []).slice().reverse();
    const take = entries.slice(skip, skip + (count - out.length));
    out.push(...take);
    skip = 0;
    if (out.length >= count) break;
  }
  return out;
}

/* Hero image 渲染. frontmatter 可指定:
 *   image: images/xxx.jpg
 *   image_caption: "刘邦画像, 清南薰殿旧藏"
 *   image_credit: "Public Domain · 南薰殿"
 * 图片放 wiki/public/images/. 加载失败时隐藏. */
function renderHeroImage(front) {
  const src = front.image;
  if (!src) return '';
  const caption = front.image_caption || '';
  const credit = front.image_credit || '';
  return `<figure class="hero-image">
    <img src="${escapeHtml(src)}"
         alt="${escapeHtml(caption)}"
         onerror="this.closest('figure').style.display='none'">
    ${caption ? `<figcaption>${escapeHtml(caption)}${credit ? ` <span class="credit">· ${escapeHtml(credit)}</span>` : ''}</figcaption>` : ''}
  </figure>`;
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

export async function renderPage(core, pid, meta, mdText) {
  document.body.classList.remove('is-home');
  const { front, html, broken } = await parseMarkdown(core, mdText, { pid, meta });

  const tagsFooter = renderTagsFooter(front, meta);
  const historyLink = `<p class="page-history-link"><a href="#?history=${encodeURIComponent(pid)}">查看修订历史 →</a></p>`;
  // Hero image (featured 页可选)
  const heroImg = renderHeroImage(front);
  document.getElementById('article').innerHTML = heroImg + html + historyLink + tagsFooter;
  const infoboxHtml = await renderInfobox(core, front, meta);
  document.getElementById('infobox').outerHTML = infoboxHtml;

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
  document.getElementById('infobox').outerHTML = '<aside class="infobox" id="infobox" hidden></aside>';
  document.getElementById('src-info').textContent = '';
  document.getElementById('broken-info').textContent = '';
  window.scrollTo(0, 0);
}

export async function renderInfobox(core, front, meta) {
  let rows = [];
  const push = (k, v) => {
    if (v != null && v !== '') {
      rows.push(`<tr><th>${escapeHtml(k)}</th><td>${v}</td></tr>`);
    }
  };

  if (front.canonical_name && front.canonical_name !== (front.label || meta.label)) {
    push('规范名', escapeHtml(front.canonical_name));
  }
  if (front.aliases && front.aliases.length) {
    push('别名', front.aliases.map(escapeHtml).join(' · '));
  }
  push('类型', TYPE_LABELS[front.type || meta.type] || front.type || meta.type);
  if (front.birth_ce != null) {
    push('生', front.birth_ce < 0 ? `前 ${-front.birth_ce}` : String(front.birth_ce));
  }
  if (front.death_ce != null) {
    push('卒', front.death_ce < 0 ? `前 ${-front.death_ce}` : String(front.death_ce));
  }
  if (front.tags && front.tags.length) {
    push('标签', front.tags.map(escapeHtml).join(' · '));
  }

  // Plugin hook: 允许改写 infobox 行
  rows = await core.hooks.onInfobox.run(rows, front, meta);

  if (!rows.length) {
    return '<aside class="infobox" id="infobox" hidden></aside>';
  }
  return `<aside class="infobox" id="infobox">
    <h2>${escapeHtml(front.label || meta.label)}</h2>
    <table>${rows.join('')}</table>
  </aside>`;
}

export function renderHome(core) {
  const pages = core.registry.pages;
  const ids = Object.keys(pages);

  // 代表页面: featured=true 优先, 再按 quality_score, 然后 total_refs, 然后 id
  const hasQuality = ids.some((id) => pages[id].quality_score != null);
  const hasRefs = ids.some((id) => pages[id].total_refs != null);
  const featured = ids
    .map((id) => ({ id, ...pages[id] }))
    .sort((a, b) => {
      // featured 优先
      const fa = a.featured ? 1 : 0, fb = b.featured ? 1 : 0;
      if (fa !== fb) return fb - fa;
      if (hasQuality) {
        const d = (b.quality_score || 0) - (a.quality_score || 0);
        if (d !== 0) return d;
      }
      if (hasRefs) return (b.total_refs || 0) - (a.total_refs || 0);
      return a.id.localeCompare(b.id, 'zh');
    })
    .slice(0, 8);  // user-req: 主页 8 个精品位

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

      <h2>代表人物 <small class="muted">(按质量排)</small></h2>
      <div class="featured-grid">${featuredHtml}</div>

      <nav class="home-links">
        <a href="#?all" class="home-link">全部 ${ids.length} 页 →</a>
        <a href="#?recent" class="home-link">最近修订 →</a>
        <a href="#${encodeURIComponent('Special:Random')}" class="home-link">随机页 →</a>
      </nav>

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
      <h3>📊 <a href="#${encodeURIComponent('Special:知识量')}" class="k-title-link">知识量</a> <span class="k-value">${k.K.toLocaleString()}</span>
        ${sparkSvg}
      </h3>
      <div class="k-row">
        <span>${k.page_count} 页</span>
        <span>${k.featured_count} 精品</span>
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
  const ib = document.getElementById('infobox');
  ib.hidden = true;
  ib.innerHTML = '';
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
  return `<a class="featured-card" href="#${encodeURIComponent(p.id)}">
    <h3>${escapeHtml(p.label)}</h3>
    ${lifeS}${meta}${aliasHtml}
  </a>`;
}

function searchPages(q, registry) {
  const lower = q.toLowerCase();
  const matched = new Map(); // pid → 命中的 surface
  for (const [pid, entry] of Object.entries(registry.pages)) {
    if (pid.toLowerCase().includes(lower)) matched.set(pid, pid);
    else if (entry.label && entry.label.toLowerCase().includes(lower)) {
      matched.set(pid, entry.label);
    }
  }
  for (const [alias, pid] of Object.entries(registry.alias_index || {})) {
    if (matched.has(pid)) continue;
    if (alias.toLowerCase().includes(lower)) matched.set(pid, alias);
  }
  return [...matched.entries()]
    .slice(0, 15)
    .map(([pid, matched]) => ({ pid, entry: registry.pages[pid], matched }));
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
    const life = p.lifespan;
    let lifeS = '';
    if (life && life.birth != null && life.death != null) {
      const b = life.birth < 0 ? `前 ${-life.birth}` : String(life.birth);
      const d = life.death < 0 ? `前 ${-life.death}` : String(life.death);
      lifeS = `<span class="cat-life">${b}—${d}</span>`;
    }
    const meta = p.total_refs != null
      ? `<span class="cat-meta">${p.total_refs} 次 / ${p.total_chapters} 篇</span>` : '';
    return `<li>
      <a href="#${encodeURIComponent(p.pid)}" class="cat-link">${escapeHtml(p.label)}</a>
      ${lifeS}${meta}
    </li>`;
  }).join('');

  const body = matches.length > 0
    ? `<ol class="category-list">${itemsHtml}</ol>`
    : '<p class="category-empty">此分类下暂无页面。</p>';

  document.getElementById('article').innerHTML =
    `<nav class="category-crumb"><a href="#">← 首页</a></nav>
     <h1>${escapeHtml(titleKind)}：${escapeHtml(displayValue)}</h1>
     <p class="category-summary">共 <strong>${matches.length}</strong> 个页面</p>
     ${body}`;

  document.body.classList.add('is-home');
  const ib = document.getElementById('infobox');
  ib.hidden = true;
  ib.innerHTML = '';
  document.getElementById('crumb').textContent = `${titleKind}：${displayValue}`;
  document.title = `${titleKind} ${displayValue} · 史记 Wiki`;
  document.getElementById('src-info').textContent =
    `pages.json (筛选: ${kind}=${value})`;
  document.getElementById('broken-info').textContent = '';
  window.scrollTo(0, 0);
}

/**
 * 最近修订页 (#?recent[&page=N]): 读 recent.json (活跃 500 条), 超出则拉归档.
 * user-req-7: 归档的历史也可翻页看到.
 */
export async function renderRecent(core, pageNum = 1) {
  const r = await fetch('recent.json');
  if (!r.ok) throw new Error('HTTP ' + r.status);
  const data = await r.json();
  const activeEntries = data.entries || [];

  // 尝试读 archive-index.json
  let archivedCount = 0;
  let archiveMonths = [];  // [{name, count}, ...] 最新月在前
  try {
    const ai = await fetch('recent-archive/index.json');
    if (ai.ok) {
      const idx = await ai.json();
      archiveMonths = idx.months || [];
      archivedCount = idx.total_archived || 0;
    }
  } catch { /* no archive */ }

  const PAGE_SIZE = 50;
  const totalEntries = activeEntries.length + archivedCount;
  const totalPages = Math.max(1, Math.ceil(totalEntries / PAGE_SIZE));
  pageNum = Math.min(Math.max(1, pageNum), totalPages);

  const start = (pageNum - 1) * PAGE_SIZE;
  const end = start + PAGE_SIZE;

  let entries;
  if (end <= activeEntries.length) {
    // 整页在活跃区
    entries = activeEntries.slice(start, end);
  } else if (start >= activeEntries.length) {
    // 整页在归档区 — 按月累加定位
    const offsetInArchive = start - activeEntries.length;
    entries = await fetchFromArchive(archiveMonths, offsetInArchive, PAGE_SIZE);
  } else {
    // 跨界: 活跃尾 + 归档头
    const activeTail = activeEntries.slice(start);
    const fromArch = await fetchFromArchive(archiveMonths, 0, PAGE_SIZE - activeTail.length);
    entries = activeTail.concat(fromArch);
  }

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

  // 翻页条
  const pagerHtml = totalPages > 1 ? buildPager(pageNum, totalPages) : '';

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
     <p class="category-summary">共 <strong>${totalEntries}</strong> 条修订 · <strong>${data.total_pages}</strong> 个页面</p>
     ${body}`;

  document.body.classList.add('is-home');
  const ib = document.getElementById('infobox');
  ib.hidden = true; ib.innerHTML = '';
  document.getElementById('crumb').textContent = '最近修订';
  document.title = '最近修订 · 史记 Wiki';
  document.getElementById('src-info').textContent = 'recent.json';
  document.getElementById('broken-info').textContent = '';
  window.scrollTo(0, 0);
}

/**
 * 单页修订历史 (#?history=<page>): 读 docs/wiki/history/<page>.json.
 */
export async function renderHistory(core, page) {
  const r = await fetch(`history/${encodeURIComponent(page)}.json`);
  if (!r.ok) throw new Error('HTTP ' + r.status);
  const data = await r.json();
  const revs = data.revisions || [];

  const rows = revs.map((rev, idx) => {
    const isLatest = rev.rev_id === data.latest_rev_id;
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
     <p class="category-summary">共 <strong>${data.revision_count}</strong> 条修订</p>
     <table class="recent-changes">
       <thead><tr><th>时间</th><th>作者</th><th>摘要</th><th>大小</th><th>修订</th></tr></thead>
       <tbody>${rows}</tbody>
     </table>`;

  document.body.classList.add('is-home');
  const ib = document.getElementById('infobox');
  ib.hidden = true; ib.innerHTML = '';
  document.getElementById('crumb').textContent = `修订历史 / ${page}`;
  document.title = `${page} 修订历史 · 史记 Wiki`;
  document.getElementById('src-info').textContent = `history/${page}.json`;
  document.getElementById('broken-info').textContent = '';
  window.scrollTo(0, 0);
}

/**
 * 单条历史版本 (#?revision=<page>&rev=<id>): 从 history/<page>.json 的
 * revisions[].content 中提取内容 (user-req-6 内联存储后). 历史数据在单文件里.
 */
export async function renderRevision(core, page, revId) {
  const r = await fetch(`history/${encodeURIComponent(page)}.json`);
  if (!r.ok) throw new Error('HTTP ' + r.status);
  const data = await r.json();
  const rev = (data.revisions || []).find((x) => x.rev_id === revId);
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
  const ib = document.getElementById('infobox');
  ib.hidden = true; ib.innerHTML = '';
  document.getElementById('crumb').textContent = `${page} @ ${revId}`;
  document.title = `${page} @ ${revId} · 史记 Wiki`;
  document.getElementById('src-info').textContent = `history/${page}/${revId}.md`;
  document.getElementById('broken-info').textContent = '';
  window.scrollTo(0, 0);
}

/**
 * All 页 (#?all): 全部页面的完整列表, 分组可切换 (type / era / alpha).
 * 取代主页原来的 "全部 N 页" 折叠区.
 */
export function renderAll(core) {
  const pages = core.registry.pages;
  const ids = Object.keys(pages);

  // 分组: 按 type
  const byType = {};
  for (const id of ids) {
    const p = pages[id];
    const t = p.type || 'unknown';
    if (!byType[t]) byType[t] = [];
    byType[t].push({ id, ...p });
  }

  // 每组内按 quality_score 降序
  for (const t of Object.keys(byType)) {
    byType[t].sort((a, b) =>
      (b.quality_score || 0) - (a.quality_score || 0) ||
      a.id.localeCompare(b.id, 'zh')
    );
  }

  const typeOrder = ['person', 'topic', 'place', 'state', 'event',
                     'chapter', 'official', 'identity'];
  const orderedTypes = Object.keys(byType).sort((a, b) => {
    const ia = typeOrder.indexOf(a), ib = typeOrder.indexOf(b);
    if (ia === -1 && ib === -1) return a.localeCompare(b);
    if (ia === -1) return 1;
    if (ib === -1) return -1;
    return ia - ib;
  });

  const groupsHtml = orderedTypes.map((t) => {
    const label = TYPE_LABELS[t] || t;
    const items = byType[t].map((p) => {
      const qs = p.quality_score != null
        ? ` <span class="list-score">q=${p.quality_score}</span>` : '';
      const meta = p.total_refs != null
        ? ` <span class="list-meta">${p.total_refs} 次 / ${p.total_chapters} 篇</span>` : '';
      const tags = (p.tags || []).slice(0, 3).map(escapeHtml).join(' · ');
      const tagsHtml = tags ? ` <span class="list-tags">${tags}</span>` : '';
      return `<li>
        <a href="#${encodeURIComponent(p.id)}">${escapeHtml(p.label)}</a>
        ${qs}${meta}${tagsHtml}
      </li>`;
    }).join('');
    return `<section class="all-group">
      <h2>${escapeHtml(label)} <small>(${byType[t].length})</small></h2>
      <ul class="all-list">${items}</ul>
    </section>`;
  }).join('');

  document.getElementById('article').innerHTML =
    `<nav class="category-crumb"><a href="#">← 首页</a></nav>
     <h1>全部页面</h1>
     <p class="category-summary">共 <strong>${ids.length}</strong> 页, 按类型分组, 组内按质量分降序</p>
     ${groupsHtml}`;

  document.body.classList.add('is-home');
  const ib = document.getElementById('infobox');
  ib.hidden = true;
  ib.innerHTML = '';
  document.getElementById('crumb').textContent = '全部页面';
  document.title = '全部 · 史记 Wiki';
  document.getElementById('src-info').textContent = 'pages.json';
  document.getElementById('broken-info').textContent = '';
  window.scrollTo(0, 0);
}

/**
 * 版本 diff 页 (#?diff=<page>&rev=<rev_id>): 显示该版 vs parent_rev 的行级 diff.
 * user-req-8: 每个版本应可看上一个版本的 diff.
 */
export async function renderDiff(core, page, revId) {
  const r = await fetch(`history/${encodeURIComponent(page)}.json`);
  if (!r.ok) throw new Error('HTTP ' + r.status);
  const data = await r.json();
  const revs = data.revisions || [];
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

  const ib = document.getElementById('infobox');
  ib.hidden = true; ib.innerHTML = '';
  document.getElementById('crumb').textContent = `${page} diff ${revId}`;
  document.title = `${page} diff · 史记 Wiki`;
  document.getElementById('src-info').textContent = `history/${page}.json (diff ${revId} vs ${cur.parent_rev || 'null'})`;
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
  const ib = document.getElementById('infobox');
  ib.hidden = true;
  ib.innerHTML = '';
  document.getElementById('crumb').textContent = '未找到';
  document.title = '未找到 · 史记 Wiki';
  document.getElementById('src-info').textContent = '';
  document.getElementById('broken-info').textContent = '';
}
