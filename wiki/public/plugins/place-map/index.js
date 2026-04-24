/**
 * place-map — 地名/邦国页面的地图插件
 *
 * 当页面 type 为 place 或 state 且 frontmatter 有 coords: [lon, lat] 时，
 * 在 sidebar 的独立 #sidebar-map 区块中渲染 Leaflet 地图，标注地点位置。
 * infobox 中的 coords 文本字段保持原样显示。
 */

const LEAFLET_CSS = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
const LEAFLET_JS  = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';

let _leafletPromise = null;

function loadLeaflet() {
  if (window.L) return Promise.resolve();
  if (_leafletPromise) return _leafletPromise;

  _leafletPromise = new Promise((resolve, reject) => {
    if (!document.querySelector('link[href*="leaflet"]')) {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = LEAFLET_CSS;
      document.head.appendChild(link);
    }
    const script = document.createElement('script');
    script.src = LEAFLET_JS;
    script.onload  = resolve;
    script.onerror = reject;
    document.head.appendChild(script);
  });

  return _leafletPromise;
}

let _currentMap = null;

export default {
  async init(core) {
    core.hooks.onInfobox.add(async (rows, front, meta) => {
      const mapEl = document.getElementById('sidebar-map');
      if (!mapEl) return rows;

      const type = front.type || meta.type;
      if (type !== 'place' && type !== 'state') {
        // 非地名页：隐藏地图区块
        mapEl.hidden = true;
        mapEl.innerHTML = '';
        if (_currentMap) { _currentMap.remove(); _currentMap = null; }
        return rows;
      }

      const coords = front.coords;
      if (!Array.isArray(coords) || coords.length < 2) {
        mapEl.hidden = true;
        mapEl.innerHTML = '';
        if (_currentMap) { _currentMap.remove(); _currentMap = null; }
        return rows;
      }

      const [lon, lat] = coords.map(Number);
      if (!isFinite(lon) || !isFinite(lat)) return rows;

      const label = front.label || meta.label || '';

      // 准备容器，先显示骨架
      mapEl.hidden = false;
      mapEl.innerHTML = '<div id="sidebar-map-leaflet" style="height:200px;width:100%;"></div>';

      // 等 DOM 更新后初始化 Leaflet
      setTimeout(async () => {
        try {
          await loadLeaflet();
          const el = document.getElementById('sidebar-map-leaflet');
          if (!el) return;

          if (_currentMap) { _currentMap.remove(); _currentMap = null; }

          const map = window.L.map(el, {
            center: [lat, lon],
            zoom: 6,
            scrollWheelZoom: false,
          });

          window.L.tileLayer(
            'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
            { attribution: '© <a href="https://www.openstreetmap.org/">OpenStreetMap</a>', maxZoom: 18 }
          ).addTo(map);

          window.L.marker([lat, lon]).addTo(map).bindPopup(label);

          _currentMap = map;

          // 确保 sidebar 可见（地图已就位）
          const sidebarEl = document.getElementById('sidebar');
          if (sidebarEl) sidebarEl.hidden = false;
        } catch (e) {
          console.error('[place-map] Leaflet 初始化失败:', e);
        }
      }, 0);

      return rows;
    });
  },
};
