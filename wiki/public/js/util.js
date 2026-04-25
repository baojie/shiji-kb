/* 纯工具函数, 无模块依赖。 */

export const TYPE_LABELS = {
  // 人物
  person: '人名',
  // 地理
  place: '地名',
  // 政治实体
  state: '邦国',
  dynasty: '朝代',
  'feudal-state': '邦国',
  // 职官制度
  official: '官职',
  institution: '制度',
  identity: '身份',
  // 事件时间
  event: '事件',
  time: '时间',
  year: '年份',
  // 物质文化
  artifact: '器物',
  biology: '生物',
  astronomy: '天文',
  quantity: '数量',
  // 文献
  book: '典籍',
  sanwen: '散文',
  taishigongyue: '太史公曰',
  chengyu: '成语',
  // 社会
  tribe: '族群',
  ritual: '礼仪',
  legal: '法律',
  // 思想
  concept: '概念',
  mythical: '神话',
  // 动词
  verb: '动词',
  'verb-military': '军事动词',
  'verb-penalty': '刑法动词',
  'verb-political': '政治动词',
  'verb-economic': '经济动词',
  // 专项
  shihao: '谥号',
  bihui: '避讳',
  xing: '姓氏',
  jun: '君号',
  // 页面类型
  chapter: '章节',
  topic: '主题',
  overview: '综述',
  story: '故事',
  list: '列表',
  disambiguation: '消歧义',
  redirect: '重定向',
  侯国: '侯国',
  skill: '技能',
  meta: '元页',
  unknown: '未知',
  special: '特殊页面',
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
