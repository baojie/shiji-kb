/**
 * place-map — 地名/邦国页面的地图 sidebar 插件
 *
 * 当页面 type 为 place 或 state 且 frontmatter 有 coords: [lon, lat] 时，
 * 在 infobox 底部注入 Leaflet 地图，标注地点位置。
 *
 * 数据来源：CHGIS V6（scripts/add_place_coords.py 写入）
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

// 当前 Leaflet map 实例（每次导航重建）
let _currentMap = null;

export default {
  async init(core) {
    core.hooks.onInfobox.add(async (rows, front, meta) => {
      const type = front.type || meta.type;
      if (type !== 'place' && type !== 'state') return rows;

      const coords = front.coords;
      if (!Array.isArray(coords) || coords.length < 2) return rows;

      const [lon, lat] = coords.map(Number);
      if (!isFinite(lon) || !isFinite(lat)) return rows;

      const label    = front.label || meta.label || '';
      const srcNote  = front.coords_source ? `<span class="map-source">${front.coords_source}</span>` : '';

      // 地图容器行（colspan=2，固定高度）
      const mapRow = `<tr><td colspan="2" class="map-cell">
        <div id="sidebar-map-container" style="height:200px;width:100%;"></div>
        ${srcNote}
      </td></tr>`;

      rows = [...rows, mapRow];

      // 等 DOM 更新后再初始化 Leaflet
      setTimeout(async () => {
        try {
          await loadLeaflet();
          const el = document.getElementById('sidebar-map-container');
          if (!el) return;

          // 销毁上一页残留的地图实例
          if (_currentMap) {
            _currentMap.remove();
            _currentMap = null;
          }

          const map = window.L.map(el, {
            center: [lat, lon],
            zoom: 6,
            scrollWheelZoom: false,
          });

          window.L.tileLayer(
            'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
            { attribution: '© <a href="https://www.openstreetmap.org/">OpenStreetMap</a>', maxZoom: 18 }
          ).addTo(map);

          window.L.marker([lat, lon])
            .addTo(map)
            .bindPopup(label || '');

          _currentMap = map;
        } catch (e) {
          console.error('[place-map] Leaflet 初始化失败:', e);
        }
      }, 0);

      return rows;
    });
  },
};
