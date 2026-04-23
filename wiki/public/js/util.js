/* 纯工具函数, 无模块依赖。 */

export const TYPE_LABELS = {
  person: '人名',
  place: '地名',
  state: '邦国',
  official: '官职',
  identity: '身份',
  dynasty: '朝代',
  event: '事件',
  concept: '概念',
  chapter: '章节',
  topic: '主题',
  overview: '综述',
  meta: '元页',
  sanwen: '散文',
  story: '故事',
};

export function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) =>
    ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
}

export function escapeAttr(s) { return escapeHtml(s); }

export function setStatus(msg) {
  const el = document.getElementById('status');
  if (el) el.textContent = msg;
}

export function showFatal(msg) {
  const article = document.getElementById('article');
  if (article) {
    article.innerHTML = `<h1>错误</h1><p class="error">${escapeHtml(msg)}</p>`;
  }
  setStatus('');
}
