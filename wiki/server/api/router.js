/* 极简 API 路由器 (CommonJS).
 *
 * 用法:
 *   const router = require('./router.js');
 *   router.register('GET', '/api/health', handler, { auth: 'public' });
 *   router.dispatch(req, res);
 *
 * 设计:
 *   - v0: 精确 method+path 匹配, 无路径参数 (用 query string 传参数)
 *   - 所有 handler 返回 Promise<any>, 抛 ApiError 触发 4xx
 *   - 默认 auth='user', 设 'public' 跳过鉴权
 */

'use strict';

const { checkAuth } = require('./auth.js');

class ApiError extends Error {
  constructor(code, message) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
  }
}

const routes = new Map();

function register(method, path, handler, opts = {}) {
  const key = `${method.toUpperCase()} ${path}`;
  routes.set(key, { handler, auth: opts.auth || 'user' });
}

function sendJson(res, status, body) {
  res.writeHead(status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-store',
  });
  res.end(JSON.stringify(body));
}

async function dispatch(req, res) {
  let u;
  try {
    u = new URL(req.url, 'http://localhost');
  } catch {
    return sendJson(res, 400, { error: 'bad_url' });
  }

  const route = routes.get(`${req.method.toUpperCase()} ${u.pathname}`);
  if (!route) {
    return sendJson(res, 404, { error: 'not_found', path: u.pathname });
  }

  if (route.auth !== 'public') {
    const result = checkAuth(req);
    if (!result.ok) {
      return sendJson(res, result.code || 401, { error: result.error });
    }
  }

  try {
    const query = Object.fromEntries(u.searchParams);
    const body = await route.handler({ req, query });
    sendJson(res, 200, body);
  } catch (e) {
    if (e instanceof ApiError) {
      sendJson(res, e.code, { error: e.message });
    } else {
      console.error('[api] handler error:', e);
      sendJson(res, 500, { error: 'internal_error' });
    }
  }
}

module.exports = { register, dispatch, sendJson, ApiError };
