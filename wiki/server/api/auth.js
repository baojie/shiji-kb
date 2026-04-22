/* Bearer token 鉴权.
 *
 * - 环境变量 WIKI_TOKEN 未设: 放行 (单用户本地默认)
 * - 设了: 请求必须带 `Authorization: Bearer <token>` 且匹配
 */

'use strict';

function checkAuth(req) {
  const required = process.env.WIKI_TOKEN;
  if (!required) {
    return { ok: true, mode: 'open' };
  }
  const header = req.headers.authorization || '';
  const match = header.match(/^Bearer\s+(.+)$/i);
  if (!match || match[1].trim() !== required) {
    return { ok: false, code: 401, error: 'unauthorized' };
  }
  return { ok: true, mode: 'token' };
}

module.exports = { checkAuth };
