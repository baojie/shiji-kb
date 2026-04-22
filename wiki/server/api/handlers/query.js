/* GET /api/query?kind=<name>&... — 语义查询入口.
 *
 * v0 kind 白名单:
 *   - entity_facts(id)      返回实体的基本属性 + 章节分布 + 总引用数
 *
 * 将来:
 *   - related_entities(id, relation)
 *   - mentions_in_chapters(id, limit?)
 *   - events_of(id)
 */

'use strict';

const { db } = require('../db.js');
const { ApiError } = require('../router.js');

const QUERY_KINDS = {
  entity_facts(params) {
    if (!params.id) throw new ApiError(400, 'missing id');
    const entity = db.getEntity(params.id);
    if (!entity) {
      return { kind: 'entity_facts', id: params.id, found: false, facts: null };
    }
    return { kind: 'entity_facts', id: params.id, found: true, facts: entity };
  },
};

async function handle({ query }) {
  const { kind, ...params } = query;
  if (!kind) throw new ApiError(400, 'missing kind');
  const fn = QUERY_KINDS[kind];
  if (!fn) throw new ApiError(400, `unknown kind: ${kind}`);
  return fn(params);
}

module.exports = { handle, QUERY_KINDS };
