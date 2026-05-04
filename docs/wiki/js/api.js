/* 前端 API 客户端 (ES Module).
 *
 * 用法:
 *   import api from './api.js';
 *   const r = await api.query('entity_facts', { id: '刘邦' });
 *
 * Token (可选):
 *   api.setToken('xxx');   // 存入 sessionStorage, 后续请求自动带
 *   api.setToken(null);    // 清除
 */

const API_BASE = '/api';
const TOKEN_KEY = 'wiki.apiToken';

function getToken() {
  try {
    return sessionStorage.getItem(TOKEN_KEY) || '';
  } catch {
    return '';
  }
}

export function setToken(token) {
  try {
    if (token) sessionStorage.setItem(TOKEN_KEY, token);
    else sessionStorage.removeItem(TOKEN_KEY);
  } catch (e) {
    console.warn('[api] token 存取失败:', e);
  }
}

async function request(pathname, { method = 'GET', params, body } = {}) {
  let url = API_BASE + pathname;
  if (params) {
    const qs = new URLSearchParams(params).toString();
    if (qs) url += '?' + qs;
  }
  const headers = { 'Accept': 'application/json' };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  if (body !== undefined) headers['Content-Type'] = 'application/json';

  const r = await fetch(url, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  const text = await r.text();
  let parsed;
  try { parsed = text ? JSON.parse(text) : null; }
  catch { parsed = { error: 'parse_error', raw: text }; }

  if (!r.ok) {
    const err = new Error(
      (parsed && parsed.error) || `HTTP ${r.status}`);
    err.code = r.status;
    err.body = parsed;
    throw err;
  }
  return parsed;
}

export async function query(kind, params = {}) {
  return request('/query', { params: { kind, ...params } });
}

export async function health() {
  return request('/health');
}

export default { query, health, setToken };
