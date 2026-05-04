/**
 * route-map — ::: route 块渲染为带箭头的 Leaflet 路线地图
 *
 * 语法:
 *   ::: route title=前209年征战路线
 *   胡陵 → 方与 → 薛
 *   :::
 *
 * 或 YAML 格式:
 *   ::: route
 *   title: 前209年征战路线
 *   places: 胡陵 → 方与 → 薛
 *   :::
 *
 * 功能:
 *   - 从 core.registry 查询各地点坐标（frontmatter coords: [lon, lat]）
 *   - 渲染内联 Leaflet 地图，含编号标记、折线连接、方向箭头
 *   - 无坐标的地点在图例中列出但不绘制
 */

const PLUGIN_NAME = 'route-map';
const LEAFLET_CSS = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
const LEAFLET_JS  = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
const COORDS_URL  = 'data/place_coords.json';

let _leafletPromise = null;
let _mapCounter = 0;
let _placeCoords = null;  // { "地名": [lon, lat], ... }

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

// 解析 block content 中的地点名列表（支持 → / , / 换行分隔）
function parsePlaces(meta, content) {
  const raw = meta.places || content || '';
  return raw
    .split(/[→,\n]+/)
    .map(s => s.trim())
    .filter(Boolean);
}

// 计算两点之间的方位角（度）
function bearing(lat1, lon1, lat2, lon2) {
  const toRad = d => d * Math.PI / 180;
  const dLon = toRad(lon2 - lon1);
  const y = Math.sin(dLon) * Math.cos(toRad(lat2));
  const x = Math.cos(toRad(lat1)) * Math.sin(toRad(lat2))
           - Math.sin(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.cos(dLon);
  return (Math.atan2(y, x) * 180 / Math.PI + 360) % 360;
}

// 两点中间点（经纬度简单平均，近距离足够精确）
function midpoint(lat1, lon1, lat2, lon2) {
  return [(lat1 + lat2) / 2, (lon1 + lon2) / 2];
}

// 编号圆形标记 icon（label 可含逗号如 "1,4"）
function numIcon(label, color) {
  const s = String(label);
  const fontSize = s.length > 3 ? '9px' : s.length > 2 ? '10px' : '11px';
  const w = s.length > 3 ? 30 : s.length > 2 ? 26 : 22;
  return window.L.divIcon({
    html: `<div style="
      width:${w}px;height:22px;border-radius:11px;
      background:${color};border:2px solid #fff;
      color:#fff;font-size:${fontSize};font-weight:bold;
      display:flex;align-items:center;justify-content:center;
      box-shadow:0 1px 3px rgba(0,0,0,.4);padding:0 2px;
    ">${s}</div>`,
    className: '',
    iconSize: [w, 22],
    iconAnchor: [w / 2, 11],
  });
}

// 箭头图标（三角形，旋转到方向）
function arrowIcon(deg) {
  return window.L.divIcon({
    html: `<div style="
      width:0;height:0;
      border-left:6px solid transparent;
      border-right:6px solid transparent;
      border-bottom:12px solid #c0392b;
      transform:rotate(${deg}deg);
      transform-origin:center 8px;
      opacity:0.85;
    "></div>`,
    className: '',
    iconSize: [12, 12],
    iconAnchor: [6, 6],
  });
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

function renderRouteMap(containerId, places, title) {
  loadLeaflet().then(() => {
    const L = window.L;
    const el = document.getElementById(containerId);
    if (!el) return;

    // 查坐标
    const resolved = places.map((name, i) => {
      const c = lookupCoords(name);
      if (c) return { name, lat: c.lat, lon: c.lon, idx: i + 1 };
      return { name, lat: null, lon: null, idx: i + 1 };
    });

    const withCoords = resolved.filter(p => p.lat !== null);
    const missing    = resolved.filter(p => p.lat === null);

    // 更新图例
    if (missing.length) {
      const legendEl = document.getElementById(containerId + '-missing');
      if (legendEl) {
        legendEl.textContent = '坐标缺失：' + missing.map(p => `${p.idx}.${p.name}`).join('、');
      }
    }

    if (withCoords.length < 1) {
      el.innerHTML = '<p style="color:#999;padding:8px">无可用坐标数据</p>';
      return;
    }

    // 初始化地图
    const map = L.map(el, { scrollWheelZoom: false });
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap',
      maxZoom: 12,
    }).addTo(map);

    // 路线折线
    const latLngs = withCoords.map(p => [p.lat, p.lon]);
    L.polyline(latLngs, { color: '#c0392b', weight: 2.5, opacity: 0.8 }).addTo(map);

    // 方向箭头（每段中点，跳过同坐标段）
    for (let i = 0; i < withCoords.length - 1; i++) {
      const a = withCoords[i], b = withCoords[i + 1];
      if (a.lat === b.lat && a.lon === b.lon) continue;
      const deg = bearing(a.lat, a.lon, b.lat, b.lon);
      const [mlat, mlon] = midpoint(a.lat, a.lon, b.lat, b.lon);
      L.marker([mlat, mlon], { icon: arrowIcon(deg), interactive: false }).addTo(map);
    }

    // 合并同坐标点，避免标记相互遮盖
    // key = "lat,lon" → { name, indices[], isFirst, isLast }
    const firstIdx = withCoords[0].idx;
    const lastIdx  = withCoords[withCoords.length - 1].idx;
    const merged = new Map();
    withCoords.forEach(p => {
      const key = `${p.lat},${p.lon}`;
      if (!merged.has(key)) {
        merged.set(key, { lat: p.lat, lon: p.lon, name: p.name, indices: [] });
      }
      merged.get(key).indices.push(p.idx);
    });

    merged.forEach(({ lat, lon, name, indices }) => {
      const isFirst = indices.includes(firstIdx);
      const isLast  = indices.includes(lastIdx);
      const color   = isFirst ? '#27ae60' : isLast ? '#8e44ad' : '#2980b9';
      const label   = indices.join(',');
      const marker  = L.marker([lat, lon], { icon: numIcon(label, color) }).addTo(map);
      const stops   = indices.map(n => `${n}.`).join(' ');
      marker.bindPopup(`<b>${stops} <a href="#${encodeURIComponent(name)}">${name}</a></b>`);
    });

    // 自动缩放到所有点
    map.fitBounds(L.latLngBounds(latLngs), { padding: [24, 24] });
  }).catch(e => console.error('[route-map] Leaflet 加载失败:', e));
}

export default {
  name: PLUGIN_NAME,
  version: '1.0.0',
  description: '::: route 块渲染为带箭头的 Leaflet 路线地图',

  async init(core) {
    // 预加载坐标数据
    fetch(COORDS_URL)
      .then(r => r.json())
      .then(data => { _placeCoords = data; })
      .catch(e => console.warn('[route-map] 坐标数据加载失败:', e));

    core.hooks.onAfterRender.add(async (html, ctx) => {
      // semantic-block 将未知块类型转为:
      //   <div class="semantic-block" data-block-type="route" data-meta='...' hidden></div>
      // 其中 data-meta 是 JSON，单引号转义为 &#39;
      const RE = /<div class="semantic-block" data-block-type="route" data-meta='([^']*)' hidden><\/div>/g;
      if (!RE.test(html)) return html;
      RE.lastIndex = 0;

      const pending = [];

      html = html.replace(RE, (match, metaStr) => {
        let meta = {};
        try { meta = JSON.parse(metaStr.replace(/&#39;/g, "'")); } catch (e) { return match; }

        const places = parsePlaces(meta, '');
        const title  = meta.title || '';
        const mapId  = `route-map-${++_mapCounter}`;

        // 宽高：默认 width=100% height=260px；指定 height 时用 height，指定 square 时用 aspect-ratio
        const w = meta.width  || '100%';
        const h = meta.height || '260px';
        const sizeStyle = h === 'square'
          ? `width:${w};aspect-ratio:1/1;`
          : `width:${w};height:${h};`;

        pending.push({ mapId, places, title });

        return `
          <div class="route-map-wrap">
            ${title ? `<div class="route-map-title">${title}</div>` : ''}
            <div id="${mapId}" style="${sizeStyle}border-radius:4px;overflow:hidden;"></div>
            <div id="${mapId}-missing" style="font-size:11px;color:#999;margin-top:3px;"></div>
          </div>`;
      });

      if (pending.length) {
        setTimeout(() => {
          for (const { mapId, places, title } of pending) {
            renderRouteMap(mapId, places, title);
          }
        }, 0);
      }

      return html;
    });

    // 注入样式
    const style = document.createElement('style');
    style.textContent = `
      .route-map-wrap { margin: 12px 0; }
      .route-map-title {
        font-size: 13px; font-weight: bold;
        color: #555; margin-bottom: 4px;
      }
    `;
    document.head.appendChild(style);
  },
};
