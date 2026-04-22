/* YAML frontmatter 解析。 依赖 window.jsyaml (CDN)。 */

const FRONTMATTER_RE = /^---\s*\n([\s\S]*?)\n---\s*\n/;

export function splitFrontmatter(text) {
  const m = FRONTMATTER_RE.exec(text);
  if (!m) return { front: {}, body: text };
  try {
    const front = window.jsyaml.load(m[1]) || {};
    return { front, body: text.slice(m[0].length) };
  } catch (e) {
    console.warn('[frontmatter] 解析失败:', e);
    return { front: {}, body: text };
  }
}
