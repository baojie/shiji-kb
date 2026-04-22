#!/usr/bin/env node
/* 从 kg/ 构建 wiki/data/semantic.json 种子数据.
 *
 * 用法:
 *   node wiki/server/api/seed.js
 *
 * v0 聚合策略（三层，叠加以消歧并避免虚胖）:
 *
 *   [L1] canonical 合并表
 *     `entity_aliases.json` 同一人常用多个 canonical (汉高祖 / 刘邦,
 *     西楚霸王 / 项羽, 秦始皇帝 / 秦始皇, 刘恒 / 汉文帝 ...). 经 CANONICAL_MERGE
 *     静态合并后, 每个人只有一个 wiki 规范名.
 *
 *   [L2] 每个 surface 选单一 refs 来源 (防止双重计数)
 *     - 无歧义 surface (aliases 里只指向一个 canonical, 或 surface===canonical
 *       且 aliases 无该行): 取 entity_index[surface].refs (子句级粒度, 最准)
 *     - 歧义 surface (aliases 里多个 canonical): 取 aliases 行自带的 refs
 *       (已消歧, 段落级粒度)
 *     绝不可两个来源都取——粒度不同 (段落 "13" vs 子句 "13.3") 去重会失败,
 *     造成同一段落被当作多条 ref (袁盎虚胖到 118 次就是此 bug).
 *
 *   [L3] (chapter, paragraph) 去重
 *     不同 surface 可能在同一子句各出现一次, 按子句 id 去重, 统计 mention 次数.
 *
 * 产出字段:
 *   id, type, aliases, lifespan, total_refs, total_chapters, chapters[]
 */

'use strict';

const fs = require('fs');
const path = require('path');

const REPO_ROOT = path.resolve(__dirname, '../../..');
const OUT = path.resolve(__dirname, '../../data/semantic.json');

const TOP_CHAPTERS_LIMIT = 30;

// entity_aliases.json 中同一人用了多个 canonical (如 "刘邦" 和 "汉高祖" 并存).
// 这里列出已知的合并: 左侧并入右侧. 右侧是 wiki 的规范名.
// 按需扩展 (尤其是 top-N 人物).
const CANONICAL_MERGE = {
  '汉高祖': '刘邦',
  '高祖': '刘邦',
  '西楚霸王': '项羽',
  '秦始皇帝': '秦始皇',
  '刘恒': '汉文帝',
  '孝文帝': '汉文帝',
  '刘启': '汉景帝',
  '孝景帝': '汉景帝',
  '卫鞅': '商鞅',
  '黥布': '英布',
  '范睢': '范雎',
  '秦昭王': '秦昭襄王',
};

function canonicalize(name) {
  return CANONICAL_MERGE[name] || name;
}

function loadJson(relPath) {
  const abs = path.join(REPO_ROOT, relPath);
  return JSON.parse(fs.readFileSync(abs, 'utf8'));
}

function buildSurfaceMap(aliasRows) {
  // surface → Set(canonicalize(canonical))
  // 用于判断 surface 是否无歧义 (单一目标 canonical).
  const m = {};
  for (const row of aliasRows || []) {
    if (!row.canonical) continue;
    if (!m[row.surface]) m[row.surface] = new Set();
    m[row.surface].add(canonicalize(row.canonical));
  }
  return m;
}

function isUnambiguous(surface, expectedCanonical, surfaceMap) {
  const targets = surfaceMap[surface];
  if (!targets) {
    // 无 aliases 记录: 仅当 surface 与 canonical 相同 (标准写法) 才视为无歧义
    return surface === expectedCanonical;
  }
  return targets.size === 1 && targets.has(expectedCanonical);
}

function filterChapterRefs(refs) {
  return (refs || []).filter(
    (r) => Array.isArray(r) && r[0] && /^\d{3}_/.test(r[0])
  );
}

function dedupeRefs(refs) {
  const seen = new Set();
  return refs.filter((r) => {
    const k = r[0] + '|' + r[1];
    if (seen.has(k)) return false;
    seen.add(k);
    return true;
  });
}

function collectSurfacesByCanonical(aliasRows) {
  // canonical (合并后) → Set(surface)
  // 也记录原 canonical 作为 "alias" 供前端路由.
  const byCanonical = {};
  for (const row of aliasRows || []) {
    if (!row.canonical) continue;
    const c = canonicalize(row.canonical);
    if (!byCanonical[c]) byCanonical[c] = new Set();
    byCanonical[c].add(row.surface);
    if (row.canonical !== c) byCanonical[c].add(row.canonical);
  }
  return byCanonical;
}

function buildEntities(aliasRows, personIndex, surfaceMap, lifespans) {
  const surfacesByCanonical = collectSurfacesByCanonical(aliasRows);

  // 预索引 aliases 行: (surface, canonical-after-merge) → 累积 refs
  // 用于歧义 surface 的 refs 取值.
  const aliasRefsIndex = {};
  for (const row of aliasRows || []) {
    if (!row.canonical) continue;
    const c = canonicalize(row.canonical);
    const key = row.surface + '|' + c;
    if (!aliasRefsIndex[key]) aliasRefsIndex[key] = [];
    aliasRefsIndex[key].push(...filterChapterRefs(row.refs));
  }

  const result = {};
  let unambigAdd = 0, ambigAdd = 0;

  for (const [canonical, surfacesSet] of Object.entries(surfacesByCanonical)) {
    // 候选 surface: aliases 映射进来的 + canonical 自己 (标准写法)
    const surfaces = new Set([...surfacesSet, canonical]);

    const refs = [];
    for (const s of surfaces) {
      if (isUnambiguous(s, canonical, surfaceMap)) {
        // [L2 unambiguous path] 取 entity_index (mention 级)
        if (personIndex[s]) {
          const add = filterChapterRefs(personIndex[s].refs);
          refs.push(...add);
          unambigAdd += add.length;
        }
      } else {
        // [L2 ambiguous path] 取 aliases 行 (paragraph 级)
        const add = aliasRefsIndex[s + '|' + canonical] || [];
        refs.push(...add);
        ambigAdd += add.length;
      }
    }

    const deduped = dedupeRefs(refs);
    if (deduped.length === 0) continue;

    const chapterCounts = {};
    for (const [ch] of deduped) {
      chapterCounts[ch] = (chapterCounts[ch] || 0) + 1;
    }
    const chapters = Object.entries(chapterCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, TOP_CHAPTERS_LIMIT)
      .map(([chapter, count]) => ({ chapter, count }));

    const aliases = [...surfaces]
      .filter((s) => s !== canonical)
      .sort();

    result[canonical] = {
      id: canonical,
      type: 'person',
      aliases,
      lifespan: lifespans[canonical] || null,
      total_refs: deduped.length,
      total_chapters: Object.keys(chapterCounts).length,
      chapters,
    };
  }

  console.log(`[seed] 无歧义路径取 ${unambigAdd} refs (entity_index), `
    + `歧义路径取 ${ambigAdd} refs (aliases 行)`);
  return result;
}

function main() {
  console.log('[seed] 加载 kg/ 数据...');
  const aliases = loadJson('kg/entities/data/entity_aliases.json');
  // 用 kg/entities/data/entity_index.json (新, 与 tagged.md 对齐).
  // 根目录 kg/entity_index.json 是旧快照, PN 可能过期.
  const idx = loadJson('kg/entities/data/entity_index.json');
  const lifespans = loadJson('kg/entities/data/person_lifespans.json').persons || {};
  const personIndex = idx.person || {};
  const surfaceMap = buildSurfaceMap(aliases.person);

  const entities = buildEntities(aliases.person, personIndex, surfaceMap, lifespans);
  const entityCount = Object.keys(entities).length;
  console.log(`[seed] 聚合完成, ${entityCount} 规范名`);

  const data = {
    entities,
    generated: new Date().toISOString(),
    stats: {
      entity_count: entityCount,
      source: 'kg/entities/data/entity_aliases.json (disambig refs) + person_lifespans.json',
    },
  };

  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(data, null, 2));
  const sizeMB = (fs.statSync(OUT).size / (1024 * 1024)).toFixed(2);
  console.log(`[seed] ${entityCount} 实体 / ${sizeMB} MB → ${OUT}`);

  // W5 提案 5 (2026-04-22-v2): 重复 canonical 诊断. 共享强别名 → 合并候选.
  findLikelyDuplicates(entities);
}

function findLikelyDuplicates(entities) {
  // 过滤掉过于通用的别名 (王/帝/公/侯/君 等单字和常用组合)
  const WEAK = new Set(['王', '帝', '公', '侯', '君', '上', '子', '父',
    '太子', '太后', '皇帝', '天子', '孝', '文', '武', '大夫']);
  const strongAlias = (s) => s.length >= 2 && !WEAK.has(s);

  const byAlias = {};  // alias → [canonical, ...]
  for (const [c, e] of Object.entries(entities)) {
    for (const a of (e.aliases || [])) {
      if (!strongAlias(a)) continue;
      if (!byAlias[a]) byAlias[a] = [];
      byAlias[a].push(c);
    }
  }

  const dupes = [];
  for (const [a, cs] of Object.entries(byAlias)) {
    if (cs.length < 2) continue;
    // 避免重复 pair
    for (let i = 0; i < cs.length; i++) {
      for (let j = i + 1; j < cs.length; j++) {
        dupes.push({
          alias: a,
          canonicals: [cs[i], cs[j]],
          hint: 'both share strong alias',
        });
      }
    }
  }

  if (dupes.length === 0) {
    console.log('[seed] 无重复 canonical 候选');
    return;
  }

  const out = path.resolve(__dirname, '../../data/duplicate_candidates.json');
  fs.writeFileSync(out, JSON.stringify({
    generated: new Date().toISOString(),
    count: dupes.length,
    note: '共享强别名的 canonical 对. 人工审核后加进 seed.js 的 CANONICAL_MERGE.',
    candidates: dupes.slice(0, 50),
  }, null, 2));
  console.log(`[seed] 发现 ${dupes.length} 对重复候选 → ${out}`);
}

main();
