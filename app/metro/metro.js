const DOCS_BASE_URL = 'https://baojie.github.io/shiji-kb/docs/';

let data = null;
let visibleLines = new Set();
let highlightedLine = null;
let stationIndex = {};
let chainIndex = {};
let viewBox = { x: 0, y: 0, w: 2000, h: 1000 };
let isPanning = false;
let panStart = { x: 0, y: 0 };

const LAYOUT = {
  xScale: 1.6,
  lineSpacing: 28,
  padding: { left: 120, right: 40, top: 40 },
  stationR: 3.5,
};

// ─── Load ───

async function init() {
  const resp = await fetch('data/metro_map_data.json');
  data = await resp.json();

  // Index
  for (const line of data.lines) {
    for (const s of line.stations) {
      stationIndex[s.id] = { ...s, lineId: line.id, lineColor: line.color, lineName: line.name };
    }
  }
  for (const c of data.chains || []) {
    if (!chainIndex[c.source]) chainIndex[c.source] = [];
    if (!chainIndex[c.target]) chainIndex[c.target] = [];
    chainIndex[c.source].push({ ...c, dir: 'out' });
    chainIndex[c.target].push({ ...c, dir: 'in' });
  }

  // Default: show first 3 chapters
  for (const line of data.lines.slice(0, 3)) {
    visibleLines.add(line.id);
  }

  buildSidebar();
  render();
  initPanZoom();
}

// ─── Sidebar ───

function buildSidebar() {
  const body = document.getElementById('sidebarBody');
  body.innerHTML = '';

  for (const grp of data.meta.groups) {
    const grpLines = data.lines.filter(l => l.group === grp);
    const grpStations = grpLines.reduce((sum, l) => sum + l.stations.length, 0);

    const header = document.createElement('div');
    header.className = 'group-header';
    header.innerHTML = `${grp} <span style="font-weight:400;font-size:10px">${grpLines.length}篇/${grpStations}事件</span>
      <span class="group-toggle" data-group="${grp}">全选</span>`;
    header.querySelector('.group-toggle').addEventListener('click', (e) => {
      e.stopPropagation();
      const allVisible = grpLines.every(l => visibleLines.has(l.id));
      grpLines.forEach(l => {
        if (allVisible) visibleLines.delete(l.id);
        else visibleLines.add(l.id);
      });
      e.target.textContent = allVisible ? '全选' : '取消';
      updateSidebarState();
      render();
    });
    body.appendChild(header);

    for (const line of grpLines) {
      const item = document.createElement('div');
      item.className = 'line-item' + (visibleLines.has(line.id) ? ' active' : ' hidden');
      item.dataset.lineId = line.id;
      item.innerHTML = `<span class="line-dot" style="background:${line.color}"></span>
        <span>${line.name}</span>
        <span class="line-count">${line.stations.length}</span>`;
      item.addEventListener('click', () => {
        if (visibleLines.has(line.id)) visibleLines.delete(line.id);
        else visibleLines.add(line.id);
        updateSidebarState();
        render();
      });
      body.appendChild(item);
    }
  }
}

function updateSidebarState() {
  document.querySelectorAll('.line-item').forEach(el => {
    const on = visibleLines.has(el.dataset.lineId);
    el.classList.toggle('active', on);
    el.classList.toggle('hidden', !on);
  });
}

// ─── Search ───

document.getElementById('searchInput').addEventListener('input', (e) => {
  const q = e.target.value.trim().toLowerCase();
  if (!q) { resetHighlight(); return; }

  const matches = new Set();
  for (const [eid, s] of Object.entries(stationIndex)) {
    if (s.name.includes(q) || s.people.some(p => p.includes(q))
        || s.locations.some(l => l.includes(q))) {
      matches.add(eid);
      visibleLines.add(s.lineId);
    }
  }

  updateSidebarState();
  render();

  // Highlight matched stations
  document.querySelectorAll('.station').forEach(el => {
    const isMatch = matches.has(el.dataset.event);
    el.classList.toggle('dimmed', !isMatch && matches.size > 0);
  });
});

// ─── Render ───

function xPos(val) {
  const [xMin] = data.meta.x_range;
  return LAYOUT.padding.left + (val - xMin) * LAYOUT.xScale;
}

function render() {
  const svg = document.getElementById('metroSvg');
  const lines = data.lines.filter(l => visibleLines.has(l.id));

  // Calculate total dimensions
  const [xMin, xMax] = data.meta.x_range;
  const totalW = LAYOUT.padding.left + LAYOUT.padding.right + (xMax - xMin) * LAYOUT.xScale;
  const totalH = LAYOUT.padding.top + lines.length * LAYOUT.lineSpacing + 60;

  svg.setAttribute('width', totalW);
  svg.setAttribute('height', totalH);
  svg.innerHTML = '';

  // Year ticks
  const tickG = svgEl('g');
  const startYear = Math.ceil(xMin / 50) * 50;
  for (let yr = startYear; yr <= xMax; yr += 50) {
    const x = xPos(yr);
    const tick = svgEl('g', { class: 'year-tick' });
    tick.appendChild(svgEl('line', { x1: x, y1: 20, x2: x, y2: totalH - 10 }));
    const label = yr < 0 ? `前${-yr}` : `${yr}`;
    const t = svgEl('text', { x, y: 14, 'text-anchor': 'middle' });
    t.textContent = label;
    tick.appendChild(t);
    tickG.appendChild(tick);
  }
  svg.appendChild(tickG);

  // Render each visible line
  lines.forEach((line, idx) => {
    const y = LAYOUT.padding.top + idx * LAYOUT.lineSpacing;
    renderOneLine(svg, line, y, idx);
  });

  // Transfers
  renderTransfers(svg, lines);

  // Stats
  const visStations = lines.reduce((s, l) => s + l.stations.length, 0);
  document.getElementById('stats').textContent = `${lines.length} 线路 / ${visStations} 事件`;

  applyViewBox();
}

function renderOneLine(svg, line, y, idx) {
  if (!line.stations.length) return;

  // Sort stations chronologically so back-references in text don't appear displaced
  const stations = [...line.stations].sort((a, b) => {
    if (a.x_pos === null && b.x_pos === null) return 0;
    if (a.x_pos === null) return 1;
    if (b.x_pos === null) return -1;
    return a.x_pos - b.x_pos;
  });

  // Compute pixel positions
  const positions = stations.map(s => ({
    x: xPos(s.x_pos),
    y,
    s,
  }));

  // Ensure minimum gap
  for (let i = 1; i < positions.length; i++) {
    if (positions[i].x - positions[i - 1].x < 8) {
      positions[i].x = positions[i - 1].x + 8;
    }
  }

  // Draw path
  if (positions.length > 1) {
    let d = `M ${positions[0].x} ${y}`;
    for (let i = 1; i < positions.length; i++) d += ` L ${positions[i].x} ${y}`;
    svg.appendChild(svgEl('path', {
      d, class: 'line-path', stroke: line.color, 'data-line': line.id,
    }));
  }

  // Line label — wrapped in a group so updateLabelVisibility can scale it
  const lx = positions[0].x - 8;
  const labelW = line.label.length * 12 + 8;
  const badgeG = svgEl('g', {
    class: 'line-badge',
    'data-ax': (lx - labelW / 2).toFixed(1),
    'data-ay': y.toFixed(1),
  });
  badgeG.appendChild(svgEl('rect', {
    x: lx - labelW, y: y - 8, width: labelW, height: 16,
    fill: line.color, class: 'line-label-bg',
  }));
  const lt = svgEl('text', {
    x: lx - labelW / 2, y: y + 4, 'text-anchor': 'middle', class: 'line-label-text',
  });
  lt.textContent = line.label;
  badgeG.appendChild(lt);
  svg.appendChild(badgeG);

  // Cluster precomputation: group stations within DENSE_GAP SVG px of each other
  const DENSE_GAP = 20;
  const clusterSize = new Array(positions.length).fill(0);
  const memberOfCluster = new Array(positions.length).fill(-1); // -1 = standalone or rep
  let ci = 0;
  while (ci < positions.length) {
    let cj = ci + 1;
    while (cj < positions.length && positions[cj].x - positions[ci].x < DENSE_GAP) cj++;
    if (cj - ci > 1) {
      clusterSize[ci] = cj - ci;
      for (let k = ci + 1; k < cj; k++) memberOfCluster[k] = ci;
    }
    ci = cj;
  }

  // Stations — all labels created, visibility/mode controlled by updateLabelVisibility
  positions.forEach((p, i) => {
    const isMember = memberOfCluster[i] >= 0;
    const g = svgEl('g', {
      class: 'station', 'data-line': line.id, 'data-event': p.s.id,
      'data-svgx': p.x.toFixed(1),
      transform: `translate(${p.x},${p.y})`,
    });
    if (isMember) {
      g.setAttribute('data-rep-x', positions[memberOfCluster[i]].x.toFixed(1));
    }

    const hasCE = p.s.year !== null;
    g.appendChild(svgEl('circle', {
      cx: 0, cy: 0, r: LAYOUT.stationR,
      fill: hasCE ? '#fff' : line.color,
      stroke: line.color,
      'stroke-width': hasCE ? 1.5 : 0,
      class: 'station-dot',
      opacity: hasCE ? 1 : 0.5,
    }));

    // Priority based on actual pixel gap to previous station
    const prevX = i > 0 ? positions[i - 1].x : -Infinity;
    const gap = p.x - prevX;
    const priority = gap < 20 ? 4 : gap < 45 ? 3 : gap < 90 ? 2 : gap < 180 ? 1 : 0;
    const isTop = idx % 2 === 0;
    const lbl = svgEl('text', {
      x: 0, y: isTop ? -10 : 14,
      'text-anchor': 'middle',
      class: 'station-label',
      'data-line': line.id,
      'data-priority': priority,
      'data-gap': gap.toFixed(1),
      'data-name': p.s.name,
      'data-istop': isTop ? '1' : '0',
      'data-cluster': clusterSize[i] > 0 ? clusterSize[i] : '',
    });
    lbl.textContent = p.s.name.slice(0, 5);
    g.appendChild(lbl);

    // Cluster badge on representative: shown when members are merged
    if (clusterSize[i] > 1) {
      const lastMemberX = positions[i + clusterSize[i] - 1].x;
      const span = (lastMemberX - p.x).toFixed(1);
      const bx = 0, by = isTop ? -(LAYOUT.stationR + 6) : (LAYOUT.stationR + 6);
      g.appendChild(svgEl('circle', { cx: bx + 5, cy: by, r: 5.5,
        class: 'cluster-badge-bg', 'data-span': span }));
      const bt = svgEl('text', { x: bx + 5, y: by,
        class: 'cluster-badge-text', 'data-span': span });
      bt.textContent = clusterSize[i];
      g.appendChild(bt);
    }

    g.addEventListener('mouseenter', (e) => showTooltip(e, p.s, line));
    g.addEventListener('mouseleave', hideTooltip);
    g.addEventListener('click', () => showDetail(p.s, line));
    svg.appendChild(g);

    // Store position for transfers
    p.s._x = p.x;
    p.s._y = y;
  });
}

function renderTransfers(svg, visLines) {
  const visLineIds = new Set(visLines.map(l => l.id));
  const transferG = svgEl('g', { class: 'transfers-layer' });

  const typeStyle = {
    cross_ref:  { stroke: '#555', width: 1.5, dash: '3 2', opacity: 0.5 },
    co_person:  { stroke: '#457b9d', width: 0.8, dash: '2 3', opacity: 0.25 },
    co_location:{ stroke: '#2a9d8f', width: 0.8, dash: '2 3', opacity: 0.2 },
    concurrent: { stroke: '#e76f51', width: 0.8, dash: '2 3', opacity: 0.25 },
  };

  for (const tr of data.transfers) {
    const evts = tr.events.map(eid => stationIndex[eid]).filter(s => s && s._x !== undefined && visLineIds.has(s.lineId));
    if (evts.length < 2) continue;

    const [a, b] = evts;
    const style = typeStyle[tr.type] || typeStyle.co_person;

    transferG.appendChild(svgEl('line', {
      x1: a._x, y1: a._y, x2: b._x, y2: b._y,
      stroke: style.stroke, 'stroke-width': style.width,
      'stroke-dasharray': style.dash, opacity: style.opacity,
      class: 'transfer-line', 'data-type': tr.type || 'cross_ref',
    }));

    // Transfer markers only for cross_ref (same event, different chapters)
    if (tr.type === 'cross_ref') {
      for (const s of evts) {
        const c = svgEl('circle', {
          cx: s._x, cy: s._y, r: 6, fill: '#fff', stroke: '#555', 'stroke-width': 2,
          class: 'transfer-marker',
        });
        c.addEventListener('click', () => showDetail(s, { color: s.lineColor, name: s.lineName }));
        transferG.appendChild(c);
      }
    }
  }

  svg.appendChild(transferG);
}

// ─── Detail Panel ───

function showDetail(station, line) {
  const panel = document.getElementById('detailPanel');
  const yearStr = station.year != null ? (station.year < 0 ? `公元前${-station.year}年` : `公元${station.year}年`) : '年份不详';

  document.getElementById('panelTitle').textContent = station.name;
  document.getElementById('panelMeta').innerHTML = `
    <span class="meta-tag" style="background:${line.color}15;color:${line.color}">${station.type}</span>
    <span class="meta-tag">${yearStr}</span>
    <span class="meta-tag">${station.id}</span>
    <span class="meta-tag">${station.chapter_name || ''}</span>
  `;

  let html = '';

  // Description
  if (station.description) {
    html += `<div class="panel-section">
      <div class="panel-section-title">事件描述</div>
      <div class="description-text">${station.description}</div>
    </div>`;
  }

  // Original quote
  if (station.quote) {
    html += `<div class="panel-section">
      <div class="panel-section-title">原文引用</div>
      <div class="quote-box">${station.quote}</div>
    </div>`;
  }

  // Paragraph link
  if (station.para_pos && station.chapter) {
    const chNum = station.chapter;
    const paraIds = station.para_pos.match(/\[(\d+)\]/g);
    if (paraIds) {
      const links = paraIds.map(p => {
        const num = p.replace(/[\[\]]/g, '');
        const url = `${DOCS_BASE_URL}${chNum}.html#p${num}`;
        return `<a class="para-link" href="${url}" target="_blank">${station.chapter_name} ${p}</a>`;
      }).join(' ');
      html += `<div class="panel-section">
        <div class="panel-section-title">原文段落</div>
        ${links}
      </div>`;
    }
  }

  // People with entity links
  if (station.people && station.people.length) {
    html += `<div class="panel-section">
      <div class="panel-section-title">人物</div>
      <div class="entity-list">${station.people.map(p =>
        `<a class="entity-tag person" href="${DOCS_BASE_URL}entities.html#${encodeURIComponent(p)}" target="_blank">${p}</a>`
      ).join('')}</div>
    </div>`;
  }

  // Locations with entity links
  if (station.locations && station.locations.length) {
    html += `<div class="panel-section">
      <div class="panel-section-title">地点</div>
      <div class="entity-list">${station.locations.map(l =>
        `<a class="entity-tag location" href="${DOCS_BASE_URL}places.html#${encodeURIComponent(l)}" target="_blank">${l}</a>`
      ).join('')}</div>
    </div>`;
  }

  // Dynasties
  if (station.dynasties && station.dynasties.length) {
    html += `<div class="panel-section">
      <div class="panel-section-title">朝代</div>
      <div class="entity-list">${station.dynasties.map(d =>
        `<span class="entity-tag dynasty">${d}</span>`
      ).join('')}</div>
    </div>`;
  }

  // Related events from chains
  const rels = chainIndex[station.id] || [];
  // Also find transfer connections for this station
  const transferRels = (data.transfers || []).filter(tr =>
    tr.events.includes(station.id)
  ).map(tr => {
    const oid = tr.events.find(e => e !== station.id);
    return { type: tr.type || 'cross_ref', target: oid, shared_people: tr.shared_people };
  });

  const allRels = [...rels, ...transferRels.map(t => ({ ...t, dir: 'link' }))];

  if (allRels.length) {
    const labels = { sequel: '延续', causal: '因果', part_of: '包含', opposition: '对立',
                     cross_ref: '互见', co_person: '共人', co_location: '共地', concurrent: '同期' };
    html += `<div class="panel-section">
      <div class="panel-section-title">关联事件</div>
      <ul class="related-list">${allRels.map(r => {
        const oid = r.dir === 'out' ? r.target : r.dir === 'in' ? r.source : r.target;
        const o = stationIndex[oid];
        const nm = o ? o.name : oid;
        const arrow = r.dir === 'out' ? '&rarr;' : r.dir === 'in' ? '&larr;' : '&harr;';
        const chInfo = o && o.chapter_name ? `<small style="color:var(--text-muted)"> [${o.chapter_name}]</small>` : '';
        return `<li data-event="${oid}">
          <span class="rel-badge ${r.type}">${labels[r.type] || r.type}</span>
          ${arrow} ${nm}${chInfo}
          ${r.reason ? `<br><small style="color:var(--text-muted)">${r.reason}</small>` : ''}
          ${r.shared_people && r.shared_people.length ? `<br><small style="color:var(--text-muted)">共同人物: ${r.shared_people.join('、')}</small>` : ''}
        </li>`;
      }).join('')}</ul>
    </div>`;
  }

  document.getElementById('panelBody').innerHTML = html;

  // Click related events
  document.getElementById('panelBody').querySelectorAll('[data-event]').forEach(el => {
    el.addEventListener('click', () => {
      const s = stationIndex[el.dataset.event];
      if (s) showDetail(s, { color: s.lineColor || '#666', name: s.lineName || '' });
    });
  });

  panel.classList.add('open');
}

document.getElementById('panelClose').addEventListener('click', () => {
  document.getElementById('detailPanel').classList.remove('open');
});

// ─── Tooltip ───

function showTooltip(e, s, line) {
  const tt = document.getElementById('tooltip');
  const yr = s.year != null ? (s.year < 0 ? `前${-s.year}年` : `${s.year}年`) : '';
  tt.innerHTML = `<b>${s.name}</b><div class="tt-sub">${yr ? yr + ' | ' : ''}${s.type} | ${s.people.slice(0,2).join('、')}</div>`;
  tt.classList.add('visible');
  tt.style.left = (e.clientX + 14) + 'px';
  tt.style.top = (e.clientY - 8) + 'px';
}

function hideTooltip() {
  document.getElementById('tooltip').classList.remove('visible');
}

// ─── Pan & Zoom ───

function initPanZoom() {
  const svg = document.getElementById('metroSvg');
  const main = document.getElementById('mainArea');

  // Fit view
  fitView();

  svg.addEventListener('mousedown', (e) => {
    if (e.target.closest('.station, .transfer-marker')) return;
    isPanning = true;
    panStart = { x: e.clientX, y: e.clientY };
    e.preventDefault();
  });

  window.addEventListener('mousemove', (e) => {
    if (!isPanning) return;
    const rect = main.getBoundingClientRect();
    const dx = (e.clientX - panStart.x) * (viewBox.w / rect.width);
    const dy = (e.clientY - panStart.y) * (viewBox.h / rect.height);
    viewBox.x -= dx;
    viewBox.y -= dy;
    panStart = { x: e.clientX, y: e.clientY };
    applyViewBox();
    updateBottomBar();
  });

  window.addEventListener('mouseup', () => { isPanning = false; });

  main.addEventListener('wheel', (e) => {
    e.preventDefault();
    const s = e.deltaY > 0 ? 1.1 : 0.9;
    const rect = svg.getBoundingClientRect();
    const mx = (e.clientX - rect.left) / rect.width;
    const my = (e.clientY - rect.top) / rect.height;
    const nw = viewBox.w * s, nh = viewBox.h * s;
    viewBox.x += (viewBox.w - nw) * mx;
    viewBox.y += (viewBox.h - nh) * my;
    viewBox.w = nw;
    viewBox.h = nh;
    applyViewBox();
    updateBottomBar();
  }, { passive: false });

  // Touch
  let lastDist = 0;
  svg.addEventListener('touchstart', (e) => {
    if (e.touches.length === 1) {
      isPanning = true;
      panStart = { x: e.touches[0].clientX, y: e.touches[0].clientY };
    } else if (e.touches.length === 2) {
      const dx = e.touches[0].clientX - e.touches[1].clientX;
      const dy = e.touches[0].clientY - e.touches[1].clientY;
      lastDist = Math.sqrt(dx*dx + dy*dy);
    }
    e.preventDefault();
  }, { passive: false });

  svg.addEventListener('touchmove', (e) => {
    const rect = main.getBoundingClientRect();
    if (e.touches.length === 1 && isPanning) {
      const dx = (e.touches[0].clientX - panStart.x) * (viewBox.w / rect.width);
      const dy = (e.touches[0].clientY - panStart.y) * (viewBox.h / rect.height);
      viewBox.x -= dx; viewBox.y -= dy;
      panStart = { x: e.touches[0].clientX, y: e.touches[0].clientY };
      applyViewBox();
    } else if (e.touches.length === 2 && lastDist > 0) {
      const dx = e.touches[0].clientX - e.touches[1].clientX;
      const dy = e.touches[0].clientY - e.touches[1].clientY;
      const dist = Math.sqrt(dx*dx + dy*dy);
      const s = lastDist / dist;
      viewBox.w *= s; viewBox.h *= s;
      lastDist = dist;
      applyViewBox();
    }
    e.preventDefault();
  }, { passive: false });

  svg.addEventListener('touchend', () => { isPanning = false; lastDist = 0; });
}

function fitView() {
  const svg = document.getElementById('metroSvg');
  const main = document.getElementById('mainArea');
  const w = parseFloat(svg.getAttribute('width')) || 2000;
  const h = parseFloat(svg.getAttribute('height')) || 1000;
  const rw = main.clientWidth;
  const rh = main.clientHeight;
  const scale = Math.min(rw / w, rh / h) * 0.92;
  viewBox.w = rw / scale;
  viewBox.h = rh / scale;
  viewBox.x = (w - viewBox.w) / 2;
  viewBox.y = (h - viewBox.h) / 2;
  applyViewBox();
}

function applyViewBox() {
  document.getElementById('metroSvg').setAttribute('viewBox',
    `${viewBox.x} ${viewBox.y} ${viewBox.w} ${viewBox.h}`);
  updateLabelVisibility();
}

// ─── Label Visibility ───

function updateLabelVisibility() {
  const svgElem = document.getElementById('metroSvg');
  const svgDisplayW = svgElem.getBoundingClientRect().width;
  const scale = svgDisplayW > 0 ? svgDisplayW / viewBox.w : 0; // screen px per SVG unit

  // ── Clamped physical sizes: scale with zoom but bounded ──
  // In inline SVG, CSS px values ARE scaled by viewBox. We compensate by setting
  // sizes in SVG user units = clampedPhysicalPx / scale, so physical size is clamped.
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
  const physFont   = clamp(9  * scale, 9,  18); // physical px: grow with zoom, cap 9–18
  const physR      = clamp(3.5 * scale, 3,  7);  // physical px: cap 3–7
  const physStroke = clamp(1.5 * scale, 1.0, 2.5);
  const svgFont    = scale > 0 ? (physFont   / scale).toFixed(2) : '9';
  const svgR       = scale > 0 ? (physR      / scale).toFixed(2) : '3.5';
  const svgStroke  = scale > 0 ? (physStroke / scale).toFixed(2) : '1.5';

  // Update all station circles
  document.querySelectorAll('.station-dot').forEach(dot => {
    dot.setAttribute('r', svgR);
    if (dot.getAttribute('stroke-width')) dot.setAttribute('stroke-width', svgStroke);
  });

  // Hover circle: clamped to 4–8px physical
  const physHover = clamp(7 * scale, 4, 8);
  svgElem.style.setProperty('--hover-r', (physHover / scale).toFixed(2));

  // Clamp line width: 2.5 SVG units base, max 6px physical
  const physLine = clamp(2.5 * scale, 1.5, 6);
  const svgLine  = (physLine / scale).toFixed(2);
  document.querySelectorAll('.line-path').forEach(p => {
    p.style.strokeWidth = svgLine + 'px';
  });

  // Year tick font: clamped 9–18px physical
  const physYearFont = clamp(11 * scale, 9, 18);
  const svgYearFont  = scale > 0 ? (physYearFont / scale).toFixed(2) : '11';
  document.querySelectorAll('.year-tick text').forEach(t => {
    t.style.fontSize = svgYearFont + 'px';
  });


  document.querySelectorAll('.station-label').forEach(lbl => {
    const gap      = parseFloat(lbl.dataset.gap  || '9999');
    const cluster  = parseInt(lbl.dataset.cluster || '0');
    const name     = lbl.dataset.name || '';
    const isTop    = lbl.dataset.istop === '1';
    const screenGap = gap * scale;

    // Reset state
    lbl.classList.remove('zoom-hidden', 'lbl-v', 'lbl-count');
    lbl.removeAttribute('transform');
    lbl.removeAttribute('dominant-baseline');
    lbl.setAttribute('text-anchor', 'middle');
    lbl.setAttribute('x', '0');
    lbl.setAttribute('y', isTop ? '-10' : '14');
    lbl.style.fontSize = svgFont + 'px';

    if (screenGap < 12) {
      lbl.classList.add('zoom-hidden');

    } else if (screenGap < 28) {
      if (cluster > 1) {
        lbl.textContent = `+${cluster}`;
        lbl.classList.add('lbl-count');
      } else {
        lbl.classList.add('zoom-hidden');
      }

    } else {
      // Vertical text: for writing-mode:vertical-rl, text-anchor controls vertical anchoring.
      // 'end'   → y anchors to BOTTOM of text (label grows upward from y)
      // 'start' → y anchors to TOP   of text (label grows downward from y)
      // Place y at circle edge + 3 physical px so label always hugs the line.
      const svgEdge = parseFloat(svgR) + 3 / scale;
      lbl.removeAttribute('dominant-baseline');
      if (isTop) {
        lbl.setAttribute('text-anchor', 'end');
        lbl.setAttribute('y', (-svgEdge).toFixed(2));
      } else {
        lbl.setAttribute('text-anchor', 'start');
        lbl.setAttribute('y', svgEdge.toFixed(2));
      }
      lbl.setAttribute('x', '0');
      lbl.textContent = name;
      lbl.classList.add('lbl-v');
    }
  });

  // Cluster merge/split
  const MERGE_PX = 16;
  document.querySelectorAll('.station[data-rep-x]').forEach(g => {
    const repX = parseFloat(g.dataset.repX);
    const myX  = parseFloat(g.dataset.svgx);
    g.classList.toggle('cluster-hidden', Math.abs(myX - repX) * scale < MERGE_PX);
  });
  document.querySelectorAll('.cluster-badge-bg, .cluster-badge-text').forEach(el => {
    const merged = parseFloat(el.dataset.span) * scale < MERGE_PX;
    el.style.display = merged ? '' : 'none';
    if (merged) {
      el.style.fontSize = svgFont + 'px';
      if (el.tagName === 'circle' || el.classList.contains('cluster-badge-bg')) {
        el.setAttribute('r', (5.5 / scale).toFixed(2));
      }
    }
  });

  // Transfer visibility: cross_ref always shown, others only when zoomed in
  const showCoRelations = viewBox.w < 1500;
  document.querySelectorAll('.transfer-line').forEach(el => {
    const t = el.getAttribute('data-type');
    if (t && t !== 'cross_ref') {
      el.style.display = showCoRelations ? '' : 'none';
    }
  });

  // Line badge: cap physical size at 20px so it doesn't grow infinitely when zoomed in
  const MAX_BADGE_PHYS = 20; // natural is 11px physical at scale=1
  document.querySelectorAll('.line-badge').forEach(g => {
    const ax = parseFloat(g.dataset.ax);
    const ay = parseFloat(g.dataset.ay);
    const naturalPhys = 11 * scale;
    if (naturalPhys > MAX_BADGE_PHYS) {
      const s = MAX_BADGE_PHYS / naturalPhys;
      g.setAttribute('transform', `translate(${ax},${ay}) scale(${s}) translate(${-ax},${-ay})`);
    } else {
      g.removeAttribute('transform');
    }
  });
}

// ─── Highlight & Bottom Bar ───

function resetHighlight() {
  document.querySelectorAll('.station, .line-path, .station-label').forEach(el => {
    el.classList.remove('dimmed', 'highlighted');
  });
}

function updateBottomBar() {
  if (!data) return;
  const cx = viewBox.x + viewBox.w / 2;
  const [xMin] = data.meta.x_range;
  const yr = Math.round(xMin + (cx - LAYOUT.padding.left) / LAYOUT.xScale);
  document.getElementById('yearLabel').textContent = yr < 0 ? `公元前 ${-yr} 年` : `公元 ${yr} 年`;
  let era = '';
  if      (yr < -2100) era = '上古（五帝时代）';
  else if (yr < -1600) era = '夏';
  else if (yr < -1046) era = '商';
  else if (yr < -771)  era = '西周';
  else if (yr < -476)  era = '春秋';
  else if (yr < -221)  era = '战国';
  else if (yr < -206)  era = '秦';
  else if (yr < 9)     era = '西汉';
  else if (yr < 23)    era = '新莽';
  else if (yr < 220)   era = '东汉';
  document.getElementById('eraLabel').textContent = era;
}

// Zoom buttons
document.getElementById('zoomIn').addEventListener('click', () => {
  const cx = viewBox.x + viewBox.w/2, cy = viewBox.y + viewBox.h/2;
  viewBox.w *= 0.7; viewBox.h *= 0.7;
  viewBox.x = cx - viewBox.w/2; viewBox.y = cy - viewBox.h/2;
  applyViewBox(); updateBottomBar();
});
document.getElementById('zoomOut').addEventListener('click', () => {
  const cx = viewBox.x + viewBox.w/2, cy = viewBox.y + viewBox.h/2;
  viewBox.w *= 1.4; viewBox.h *= 1.4;
  viewBox.x = cx - viewBox.w/2; viewBox.y = cy - viewBox.h/2;
  applyViewBox(); updateBottomBar();
});
document.getElementById('zoomFit').addEventListener('click', () => { fitView(); updateBottomBar(); });

// ─── Util ───

function svgEl(tag, attrs = {}) {
  const el = document.createElementNS('http://www.w3.org/2000/svg', tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
  return el;
}

init();
