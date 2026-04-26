/**
 * geomap — ::: geomap 块：多地点图钉地图（无路线连线）
 *
 * 语法（YAML格式）:
 *   ::: geomap
 *   title: 项羽分封十八诸侯（前206年）
 *   places: 废丘:雍·章邯, 栎阳:塞·司马欣, 汉中:汉·刘邦
 *   :::
 *
 * places 格式: 地名:标签, 地名:标签, ...
 * 地名用于查询坐标，标签显示在图钉弹窗里
 * 无标签时直接写地名
 *
 * 功能:
 *   - 从 place_coords.json 查询各地点坐标
 *   - 渲染 Leaflet 地图，每个地点显示带标签的图钉
 *   - 无坐标的地点在图例中列出
 *   - 点击图钉显示地名+标签弹窗
 */

const PLUGIN_NAME = 'geomap';
const LEAFLET_CSS = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
const LEAFLET_JS  = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
const COORDS_URL  = 'data/place_coords.json';

let _leafletPromise = null;
let _mapCounter = 0;
let _placeCoords = null;

function loadLeaflet() {
  if (window.L) return Promise.resolve();
  if (_leafletPromise) return _leafletPromise;
  _leafletPromise = new Promise((resolve, reject) => {
    if (!document.querySelector('link[href*="leaflet"]')) {
      const link = document.createElement('link');
      link.rel = 'stylesheet'; link.href = LEAFLET_CSS;
      document.head.appendChild(link);
    }
    const script = document.createElement('script');
    script.src = LEAFLET_JS;
    script.onload = resolve; script.onerror = reject;
    document.head.appendChild(script);
  });
  return _leafletPromise;
}

// 解析 "地名:标签, 地名:标签" 格式
function parsePins(raw) {
  return (raw || '').split(',').map(s => {
    const idx = s.indexOf(':');
    if (idx === -1) return { place: s.trim(), label: '' };
    return { place: s.slice(0, idx).trim(), label: s.slice(idx + 1).trim() };
  }).filter(p => p.place);
}

function lookupCoords(name) {
  if (!_placeCoords) return null;
  const c = _placeCoords[name];
  if (Array.isArray(c) && c.length >= 2) {
    const [lon, lat] = [Number(c[0]), Number(c[1])];
    if (isFinite(lon) && isFinite(lat)) return { lon, lat };
  }
  return null;
}

// 图钉颜色调色板（循环使用）
const PIN_COLORS = [
  '#c0392b','#27ae60','#2980b9','#8e44ad','#d35400',
  '#16a085','#2c3e50','#f39c12','#1abc9c','#e74c3c',
];

function pinIcon(label, color) {
  const L = window.L;
  const short = label ? label.slice(0, 4) : '●';
  return L.divIcon({
    html: `<div style="
      background:${color};border:2px solid #fff;border-radius:4px;
      color:#fff;font-size:10px;font-weight:bold;padding:2px 4px;
      white-space:nowrap;box-shadow:0 1px 3px rgba(0,0,0,.4);
      max-width:80px;overflow:hidden;text-overflow:ellipsis;
    ">${short}</div>`,
    className: '',
    iconSize: null,
    iconAnchor: [0, 0],
  });
}

function renderGeomap(containerId, pins, title) {
  loadLeaflet().then(() => {
    const L = window.L;
    const el = document.getElementById(containerId);
    if (!el) return;

    const resolved = pins.map((p, i) => {
      const c = lookupCoords(p.place);
      return c
        ? { ...p, lat: c.lat, lon: c.lon, color: PIN_COLORS[i % PIN_COLORS.length] }
        : { ...p, lat: null, lon: null };
    });

    const withCoords = resolved.filter(p => p.lat !== null);
    const missing    = resolved.filter(p => p.lat === null);

    if (missing.length) {
      const legendEl = document.getElementById(containerId + '-missing');
      if (legendEl)
        legendEl.textContent = '坐标缺失：' + missing.map(p => p.label ? `${p.label}(${p.place})` : p.place).join('、');
    }

    if (!withCoords.length) {
      el.innerHTML = '<p style="color:#999;padding:8px">无可用坐标数据</p>';
      return;
    }

    const map = L.map(el, { scrollWheelZoom: false });
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap', maxZoom: 12,
    }).addTo(map);

    const latLngs = withCoords.map(p => [p.lat, p.lon]);

    withCoords.forEach(p => {
      const marker = L.marker([p.lat, p.lon], { icon: pinIcon(p.label, p.color) }).addTo(map);
      const linkPlace = `<a href="#${encodeURIComponent(p.place)}">${p.place}</a>`;
      const popup = p.label ? `<b>${p.label}</b><br>${linkPlace}` : `<b>${linkPlace}</b>`;
      marker.bindPopup(popup);
    });

    map.fitBounds(L.latLngBounds(latLngs), { padding: [32, 32] });
  }).catch(e => console.error('[geomap] Leaflet 加载失败:', e));
}

export default {
  name: PLUGIN_NAME,
  version: '1.0.0',
  description: '::: geomap 块：多地点图钉地图，无路线连线，适合分封/郡国/战场分布等地理概览',

  async init(core) {
    fetch(COORDS_URL)
      .then(r => r.json())
      .then(data => { _placeCoords = data; })
      .catch(e => console.warn('[geomap] 坐标数据加载失败:', e));

    core.hooks.onAfterRender.add(async (html, ctx) => {
      const RE = /<div class="semantic-block" data-block-type="geomap" data-meta='([^']*)' hidden><\/div>/g;
      if (!RE.test(html)) return html;
      RE.lastIndex = 0;

      const pending = [];
      html = html.replace(RE, (match, metaStr) => {
        let meta = {};
        try { meta = JSON.parse(metaStr.replace(/&#39;/g, "'")); } catch { return match; }

        const pins  = parsePins(meta.places || '');
        const title = meta.title || '';
        const mapId = `geomap-${++_mapCounter}`;

        // 宽高：默认 width=100%，height 由 aspect-ratio:1/1 撑开（正方形）
        const w = meta.width  || '100%';
        const h = meta.height || null;
        const sizeStyle = h
          ? `width:${w};height:${h};`
          : `width:${w};aspect-ratio:1/1;`;

        pending.push({ mapId, pins, title });

        return `
          <div class="geomap-wrap">
            ${title ? `<div class="geomap-title">${title}</div>` : ''}
            <div id="${mapId}" style="${sizeStyle}border-radius:4px;overflow:hidden;"></div>
            <div id="${mapId}-missing" style="font-size:11px;color:#999;margin-top:3px;"></div>
          </div>`;
      });

      if (pending.length) {
        setTimeout(() => {
          for (const { mapId, pins, title } of pending)
            renderGeomap(mapId, pins, title);
        }, 0);
      }
      return html;
    });

    const style = document.createElement('style');
    style.textContent = `
      .geomap-wrap { margin: 12px 0; }
      .geomap-title { font-size: 13px; font-weight: bold; color: #555; margin-bottom: 4px; }
    `;
    document.head.appendChild(style);
  },
};
