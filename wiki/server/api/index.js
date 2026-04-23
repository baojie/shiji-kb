/* API 路由注册中心. serve.js 只 require 本文件, 拿到 dispatch. */

'use strict';

const router = require('./router.js');
const health = require('./handlers/health.js');
const query = require('./handlers/query.js');
const want  = require('./handlers/want.js');

router.register('GET',  '/api/health', health.handle, { auth: health.auth });
router.register('GET',  '/api/query',  query.handle,  { auth: query.auth  });
router.register('GET',  '/api/want',   want.handle,   { auth: want.auth   });

module.exports = router;
