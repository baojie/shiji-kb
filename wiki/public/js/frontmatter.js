/* YAML frontmatter 解析。 依赖 window.jsyaml (CDN)。 */

// 标准格式: 文件以 --- 开头
const FRONTMATTER_RE = /^---\s*\n([\s\S]*?)\n---\s*\n/;
// 扩展格式: 文件以裸 YAML 字段开头（无 ---），后接 ---...--- 主块
// 例: event 页面将 paragraph_refs / event_type / location 放在主块之前
const EXTENDED_RE = /^([\s\S]*?)---\s*\n([\s\S]*?)\n---\s*\n/;

export function splitFrontmatter(text) {
  const m = FRONTMATTER_RE.exec(text);
  if (m) {
    try {
      const front = window.jsyaml.load(m[1]) || {};
      return { front, body: text.slice(m[0].length) };
    } catch (e) {
      console.warn('[frontmatter] 解析失败:', e);
      return { front: {}, body: text.slice(m[0].length) };
    }
  }
  // 扩展格式: preamble 字段 + ---...--- 主块，合并后主块优先
  const m2 = EXTENDED_RE.exec(text);
  if (m2) {
    try {
      const preamble = window.jsyaml.load(m2[1]) || {};
      const main = window.jsyaml.load(m2[2]) || {};
      return { front: { ...preamble, ...main }, body: text.slice(m2[0].length) };
    } catch (e) {
      console.warn('[frontmatter] 解析失败 (extended):', e);
      return { front: {}, body: text.slice(m2[0].length) };
    }
  }
  return { front: {}, body: text };
}
