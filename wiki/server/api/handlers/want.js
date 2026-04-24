/* GET /api/want?page=<page_id> — 用户点击"想要"按钮, 把页面插入 butler 队列首位 (P0).
 *
 * 成功: { ok: true,  page, added: true,  message }
 * 重复: { ok: true,  page, added: false, message }
 * 错误: 500 { ok: false, error }
 */

'use strict';

const fs = require('fs');
const path = require('path');

const QUEUE_PATH = path.resolve(__dirname, '../../../../wiki/logs/butler/queue.md');
const SECTION_HEADER = '## ⭐ 用户想要 (P0)';

function today() {
  return new Date().toISOString().slice(0, 10);
}

function buildEntry(page) {
  return `- [ ] **[想要]** ${page}: \`create-stub\` [P0] [${today()}] [用户请求]\n`;
}

function insertIntoQueue(page) {
  if (!fs.existsSync(QUEUE_PATH)) {
    throw new Error('queue.md 不存在: ' + QUEUE_PATH);
  }
  const raw = fs.readFileSync(QUEUE_PATH, 'utf8');

  if (raw.includes(`**[想要]** ${page}:`)) {
    return { added: false, message: `"${page}" 已在队列中` };
  }

  const entry = buildEntry(page);
  let updated;

  const sectionIdx = raw.indexOf(SECTION_HEADER);
  if (sectionIdx !== -1) {
    const afterHeader = raw.indexOf('\n', sectionIdx) + 1;
    updated = raw.slice(0, afterHeader) + entry + raw.slice(afterHeader);
  } else {
    const firstSection = raw.indexOf('\n## ');
    const insertAt = firstSection === -1 ? raw.length : firstSection + 1;
    const block = SECTION_HEADER + '\n' + entry + '\n';
    updated = raw.slice(0, insertAt) + block + raw.slice(insertAt);
  }

  fs.writeFileSync(QUEUE_PATH, updated, 'utf8');
  return { added: true, message: `"${page}" 已加入队列首位` };
}

async function handle({ query }) {
  const page = (query.page || '').trim();
  if (!page) {
    const { ApiError } = require('../router.js');
    throw new ApiError(400, 'missing page');
  }

  try {
    const result = insertIntoQueue(page);
    return { ok: true, page, ...result };
  } catch (e) {
    const { ApiError } = require('../router.js');
    throw new ApiError(500, e.message);
  }
}

module.exports = { handle, auth: 'public' };
