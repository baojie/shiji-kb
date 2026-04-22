/* GET /api/health — 健康检查, 无鉴权. */

'use strict';

const { db } = require('../db.js');

async function handle() {
  return {
    ok: true,
    time: new Date().toISOString(),
    db: db.meta(),
  };
}

module.exports = { handle, auth: 'public' };
