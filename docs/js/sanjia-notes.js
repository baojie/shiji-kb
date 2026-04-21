/**
 * 史记知识库 - 三家注（集解·索隐·正义）行下展示
 *
 * 功能：
 * 1. 从 docs/notes_cache/NNN-notes.json 加载简体缓存
 * 2. 在每个段落末尾插入三家注条目
 * 3. 在原文中插入上标编号 [N]，与注释条目双向联动
 * 4. 支持开关（body.show-sanjia 控制显示）
 *
 * 数据源：
 * - 原始繁体：data/notes/NNN-notes.json（维基文库三家注抽取）
 * - 简体缓存：docs/notes_cache/NNN-notes.json（由 scripts/build_sanjia_cache.py 生成）
 */
(function() {
    'use strict';

    let notesData = null;   // [{id, anchor_text, before_context, after_context, items:[{source,label,text}]}]
    let loadPromise = null;
    let rendered = false;

    function chapterNumFromUrl() {
        // 兼容编码路径：/chapters/001_xxx.html
        const decoded = decodeURIComponent(window.location.pathname);
        const m = decoded.match(/\/(\d{3})_/);
        return m ? m[1] : null;
    }

    async function loadNotes() {
        if (loadPromise) return loadPromise;
        loadPromise = (async () => {
            const num = chapterNumFromUrl();
            if (!num) {
                console.warn('[sanjia] 无法从URL提取章节编号');
                return;
            }
            const url = `../notes_cache/${num}-notes.json`;
            try {
                const resp = await fetch(url);
                if (!resp.ok) {
                    console.log(`[sanjia] 章节 ${num} 暂无三家注数据 (${resp.status})`);
                    return;
                }
                const data = await resp.json();
                notesData = Array.isArray(data.notes) ? data.notes : [];
                console.log(`[sanjia] 已加载 ${notesData.length} 条三家注`);
            } catch (err) {
                console.error('[sanjia] 加载失败:', err);
            }
        })();
        return loadPromise;
    }

    function stripLeadingEllipsis(s) {
        if (!s) return '';
        return s.replace(/^(\.{3}|…)/, '');
    }

    /**
     * 变体字符归一（用于匹配，不影响显示）：
     * 章节文本保留部分传统字形，notes 经 opencc t2s 成简体后字形不同，
     * 两侧不一致导致匹配失败。这里做 1:1 字符映射把双方归一到同一规范形，
     * 由于是字符级 1:1 映射，字符偏移量不变，indexOf 位置可直接套用回原文。
     *
     * 映射来自 scripts/analyze_unmatched.py 对全库未匹配样本的统计：
     * "某字符 → 某字符" 若出现 ≥ 3 次且两字确为异体/常见讹变，则加入此表。
     */
    const VARIANT_MAP = {
        // 虚词/常用字：章节保留传统，notes t2s 成简体
        '於': '于', '后': '后',
        '後': '后', '蟲': '虫',
        '衛': '卫', '衞': '卫',
        '擒': '禽',
        '䇲': '策', '䝙': '貙',
        '徧': '遍', '悳': '德', '辠': '罪', '愬': '诉',

        // 高频异体字对（analyze_unmatched.py 发现）
        '馀': '余',        // 115 次
        '閒': '间', '閑': '间', '闲': '间',  // 57 次
        '硃': '朱',        // 19
        '適': '适',        // 18
        '迺': '乃',        // 16
        '穀': '谷',        // 15（仅地名/人名外）
        '徵': '征',        // 13
        '脩': '修',        // 13
        '卻': '却',        // 10
        '兒': '儿',        // 10
        '愿': '原', '願': '原',  // 10（愿/原 两用）
        '鴈': '雁',        // 9
        '鍾': '锺', '錘': '锺', '钟': '锺',  // 9
        '釐': '厘',        // 6
        '氾': '泛',        // 5
        '甯': '宁',        // 5
        '旂': '旗',        // 5
        '犂': '犁',        // 5
        '鬬': '斗', '鬭': '斗', '鬥': '斗',  // 5
        '鉅': '巨', '钜': '巨',               // 4
        '蓺': '艺', '藝': '艺',               // 4
        '靁': '雷',        // 4
        '孼': '孽',        // 4
        '襃': '褒',        // 4
        '璿': '璇',        // 3
        '麤': '粗',        // 3
        '籓': '藩',        // 3
        '袵': '衽',        // 3
        '汙': '污',        // 3
        '巂': '嶲',        // 3
        '猨': '猿',        // 3
        '犇': '奔',        // 7
        '鄴': '邺',        // 2
        '婿': '壻',        // 2
        '祕': '秘',        // 2
        '濰': '潍',        // 2
        '砲': '炮',        // 2
    };
    function normalize(s) {
        if (!s) return '';
        let out = '';
        for (const ch of s) {
            out += VARIANT_MAP[ch] || ch;
        }
        return out;
    }

    /**
     * 统计 needle 在 haystack 中出现次数（用于唯一性判断）。
     */
    function countOccurrences(haystack, needle) {
        if (!needle) return 0;
        let count = 0, idx = 0;
        while ((idx = haystack.indexOf(needle, idx)) !== -1) {
            count++;
            idx += needle.length;
        }
        return count;
    }

    /**
     * 在段落的文本流中定位 targetOffset 处的 {node, offset}
     *
     * @param {Element} paragraph - 段落根元素
     * @param {number} targetOffset - 纯文本中的字符偏移（从段落起始，基于 trim 后的文本）
     *
     * 说明：paragraphPlainText 会剥离段落首尾空白，targetOffset 基于剥离后文本；
     * 此处 walk DOM 时需要跳过首部空白节点与首节点的前导空白，保持一致。
     */
    function locateAtOffset(paragraph, targetOffset) {
        const walker = document.createTreeWalker(
            paragraph,
            NodeFilter.SHOW_TEXT,
            {
                acceptNode: function(node) {
                    const pe = node.parentElement;
                    if (!pe) return NodeFilter.FILTER_REJECT;
                    if (pe.closest('rt, a.para-num, .sanjia-anchor-marker, .sanjia-notes-container')) {
                        return NodeFilter.FILTER_REJECT;
                    }
                    return NodeFilter.FILTER_ACCEPT;
                }
            }
        );
        const nodes = [];
        let n;
        while ((n = walker.nextNode())) nodes.push(n);
        if (nodes.length === 0) return null;

        // 跳过首部纯空白的文本节点
        let startIdx = 0;
        while (startIdx < nodes.length && !/\S/.test(nodes[startIdx].textContent)) startIdx++;
        if (startIdx >= nodes.length) return null;

        // 首个非空白节点内部可能仍有前导空白，也要跳过
        const firstLead = nodes[startIdx].textContent.match(/^\s*/)[0].length;

        let accumulated = 0;
        for (let i = startIdx; i < nodes.length; i++) {
            const node = nodes[i];
            const skip = (i === startIdx) ? firstLead : 0;
            const effectiveLen = node.textContent.length - skip;
            if (accumulated + effectiveLen >= targetOffset) {
                return { node, offset: skip + (targetOffset - accumulated) };
            }
            accumulated += effectiveLen;
        }
        // 超出末尾：落到最后一个文本节点末端
        const last = nodes[nodes.length - 1];
        return { node: last, offset: last.textContent.length };
    }

    /**
     * 返回段落的纯文本（忽略已插入的三家注元素）
     */
    function paragraphPlainText(paragraph) {
        let text = '';
        const walker = document.createTreeWalker(
            paragraph,
            NodeFilter.SHOW_TEXT,
            {
                acceptNode: function(node) {
                    const pe = node.parentElement;
                    if (!pe) return NodeFilter.FILTER_REJECT;
                    // 跳过拼音标注（<rt> 内容）和段落编号（<a class="para-num">）
                    if (pe.closest('rt, a.para-num, .sanjia-anchor-marker, .sanjia-notes-container')) {
                        return NodeFilter.FILTER_REJECT;
                    }
                    return NodeFilter.FILTER_ACCEPT;
                }
            }
        );
        let n;
        while ((n = walker.nextNode())) {
            text += n.textContent;
        }
        // 文言原文无意义空白：剥离两端空白，让相邻段落拼接时字符紧邻
        // 否则 "<a>1.2</a> 项籍..." 的前导空格会破坏跨段 before_context 匹配
        return text.replace(/^\s+/, '').replace(/\s+$/, '');
    }

    /**
     * 清理显示用 anchor_text：原始数据里 anchor 常为 before_context 的末尾截断，
     * 有时起始字符是前一句的残尾（如 "夷，死人如乱麻..." — "夷" 是 "外攘四夷" 的末字）。
     * 此处把起始 1–3 字符 + 子句标点 (，。；、) 的前缀剥掉，让 anchor 从子句边界起。
     * 若剥掉后为空（说明 anchor 本身就是单个短词如 "者，"），保持原样。
     */
    function cleanAnchorForDisplay(s) {
        if (!s) return s;
        // 先去掉纯粹前导标点
        s = s.replace(/^[，。；、、]+/, '');
        // 再剥 "1–3 字 + 子句标点" 前缀（若仍有实质内容）
        const m = s.match(/^[^，。；、]{1,3}[，。；、]/);
        if (m && m[0].length < s.length) {
            return s.substring(m[0].length);
        }
        return s;
    }

    function escapeHtml(s) {
        if (s == null) return '';
        return String(s)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function insertMarkerAt(paragraph, offset, num) {
        const loc = locateAtOffset(paragraph, offset);
        if (!loc) return false;
        const { node, offset: off } = loc;

        const marker = document.createElement('sup');
        marker.className = 'sanjia-anchor-marker';
        marker.setAttribute('data-note-num', String(num));
        marker.textContent = `[${num}]`;

        // 若文本节点在 <ruby> 内（拼音标注），将 marker 插入到 ruby 之外
        // 否则 marker 会嵌入 ruby 内部，视觉错位
        const ruby = node.parentElement && node.parentElement.closest('ruby');
        if (ruby) {
            if (off <= 0) {
                ruby.parentNode.insertBefore(marker, ruby);
            } else {
                ruby.parentNode.insertBefore(marker, ruby.nextSibling);
            }
            return true;
        }

        if (off <= 0) {
            node.parentNode.insertBefore(marker, node);
        } else if (off >= node.textContent.length) {
            if (node.nextSibling) {
                node.parentNode.insertBefore(marker, node.nextSibling);
            } else {
                node.parentNode.appendChild(marker);
            }
        } else {
            const rest = node.splitText(off);
            node.parentNode.insertBefore(marker, rest);
        }
        return true;
    }

    function buildNoteEntryHtml(num, note) {
        let html = '';
        html += `<div class="sanjia-note" data-note-num="${num}">`;
        html += `<span class="sanjia-note-num">[${num}]</span>`;
        const displayAnchor = cleanAnchorForDisplay(note.anchor_text);
        if (displayAnchor) {
            html += `<span class="sanjia-note-anchor">${escapeHtml(displayAnchor)}</span>`;
        }
        html += `<div class="sanjia-note-items">`;
        (note.items || []).forEach(it => {
            html += `<div class="sanjia-note-item" data-source="${it.source}">`;
            html += `<span class="sanjia-source sanjia-source-${it.source}">${escapeHtml(it.label)}</span>`;
            html += `<span class="sanjia-text">${escapeHtml(it.text)}</span>`;
            html += `</div>`;
        });
        html += `</div></div>`;
        return html;
    }

    /**
     * 构建章节全文（按段落 DOM 顺序拼接），并记录每段在全文中的起止位置。
     *
     * 返回 { text, paraRanges: [{para, start, end, textLen}] }。
     */
    function buildChapterText(paragraphs) {
        let text = '';
        const ranges = [];
        paragraphs.forEach(para => {
            const pt = paragraphPlainText(para);
            if (!pt) return;
            ranges.push({ para, start: text.length, end: text.length + pt.length, textLen: pt.length });
            text += pt;
        });
        // 归一化版本用于匹配；索引位置与 text 一一对应
        return { text, textNorm: normalize(text), paraRanges: ranges };
    }

    /**
     * 在章节全文中匹配每条注的位置。
     *
     * 返回 [{note, matchPos, insertPos, paraInfo, localInsert}]，
     * paraInfo 指向 insertPos 所在的段落。
     *
     * 三层匹配 + 顺序约束回退：
     *   1. 完整 before+after
     *   2. 仅 before（≥4 字符）
     *   3. 唯一后缀（6-20 字符，多义时用 after 消歧）
     *   4. 顺序约束回退：note 在章内为序列号，其位置应介于前/后已匹配 note 之间。
     *      在此区间内再尝试 anchor_text / 短后缀匹配；仍未命中则取区间中点（兜底）。
     */
    function matchNotesInChapter(chapter, notes) {
        const results = [];
        notes.forEach((note, idx) => {
            if (!note.before_context && !note.after_context && !note.anchor_text) {
                // 纯章首注（如 n001）单独放入 chapter 容器
                results.push({ note, idx, chapterLevel: true });
                return;
            }
            const before = stripLeadingEllipsis(note.before_context);
            const after = note.after_context || '';

            let matchPos = -1;
            let insertPos = -1;

            // 匹配用归一化文本（字符级 1:1，位置与原文一致）
            const beforeN = normalize(before);
            const afterN = normalize(after);

            // 策略1：before + after 精确匹配
            if (beforeN && afterN) {
                const full = beforeN + afterN;
                const pos = chapter.textNorm.indexOf(full);
                if (pos !== -1) {
                    matchPos = pos;
                    insertPos = pos + beforeN.length;
                }
            }
            // 策略2：仅 before_context（length ≥ 4 避免短串误匹配）
            if (matchPos === -1 && beforeN && beforeN.length >= 4) {
                const pos = chapter.textNorm.indexOf(beforeN);
                if (pos !== -1) {
                    matchPos = pos;
                    insertPos = pos + beforeN.length;
                }
            }
            // 策略3：后缀回退 —— 章节个别字与 notes 有差异（错字/异体/版本分歧）时，
            // 完整 before 不匹配，但末尾若干字符往往能命中。
            // 要求命中次数严格唯一；若多次出现则用 after_context 首若干字辅助去重。
            if (matchPos === -1 && beforeN && beforeN.length >= 6) {
                const SUFFIX_LENS = [20, 16, 12, 10, 8, 6];
                for (const sl of SUFFIX_LENS) {
                    if (sl > beforeN.length) continue;
                    const suf = beforeN.substring(beforeN.length - sl);
                    const occ = countOccurrences(chapter.textNorm, suf);
                    if (occ === 1) {
                        const pos = chapter.textNorm.indexOf(suf);
                        matchPos = pos;
                        insertPos = pos + sl;
                        break;
                    }
                    if (occ > 1 && afterN) {
                        // 用 after 首若干字符消歧
                        for (const al of [6, 4, 2, 1]) {
                            if (al > afterN.length) continue;
                            const combined = suf + afterN.substring(0, al);
                            if (countOccurrences(chapter.textNorm, combined) === 1) {
                                const pos = chapter.textNorm.indexOf(combined);
                                matchPos = pos;
                                insertPos = pos + sl;
                                break;
                            }
                        }
                        if (matchPos !== -1) break;
                    }
                }
            }
            if (matchPos === -1) {
                // 先搁置，稍后用顺序约束回退批量处理
                results.push({ note, idx, pending: true });
                return;
            }

            // 根据 insertPos 定位到所在段落
            const paraInfo = findParaForOffset(chapter.paraRanges, insertPos);
            if (!paraInfo) {
                results.push({ note, idx, chapterLevel: true });
                return;
            }
            const localInsert = insertPos - paraInfo.start;
            results.push({ note, idx, matchPos, insertPos, paraInfo, localInsert });
        });

        // 顺序约束回退：对 pending 项，用前后已定位 note 限定搜索窗口
        fillPendingByOrder(results, chapter);

        return results;
    }

    /**
     * 顺序约束回退。
     *
     * 假设：notes 数组中 note 的先后顺序与其在章内位置的先后顺序一致（原始维基文库抽取时按文序）。
     * 对未匹配 note：
     *   - 找到序列中前/后最近的 matched note 的 insertPos，得到搜索窗口 [prev, next]
     *   - 在窗口内搜索 anchor_text（归一后）或短后缀（唯一匹配）
     *   - 都失败则取窗口中点作为 insertPos（保底落在相邻段，至少出现在正文附近）
     */
    function fillPendingByOrder(results, chapter) {
        // 先记录已匹配项的 idx→insertPos 映射
        const matchedPos = new Map();
        results.forEach(r => {
            if (r.insertPos !== undefined && r.insertPos >= 0) {
                matchedPos.set(r.idx, r.insertPos);
            }
        });

        // 对每个 pending，按序查找前/后最近的 matched
        results.forEach(r => {
            if (!r.pending) return;
            // 前向扫描
            let prev = null;
            for (let j = r.idx - 1; j >= 0; j--) {
                if (matchedPos.has(j)) { prev = matchedPos.get(j); break; }
            }
            // 后向扫描
            let next = null;
            for (let j = r.idx + 1; j < results.length; j++) {
                if (matchedPos.has(j)) { next = matchedPos.get(j); break; }
            }
            const lo = prev !== null ? prev : 0;
            const hi = next !== null ? next : chapter.text.length;
            if (hi <= lo) {
                // 退化：直接用 lo 作为 insertPos
                attachToPara(r, lo, chapter);
                return;
            }

            const window = chapter.textNorm.substring(lo, hi);
            const anchor = r.note.anchor_text || '';
            const aN = normalize(anchor);
            let localFound = -1;

            // 3a. 在窗口内搜 anchor_text
            if (aN && aN.length >= 2) {
                const p = window.indexOf(aN);
                if (p !== -1) localFound = p + aN.length;
            }
            // 3b. 在窗口内搜短后缀（非唯一也接受，因为已有窗口约束）
            if (localFound === -1) {
                const before = stripLeadingEllipsis(r.note.before_context);
                const bN = normalize(before);
                if (bN) {
                    for (const sl of [12, 8, 6, 4, 3]) {
                        if (sl > bN.length) continue;
                        const suf = bN.substring(bN.length - sl);
                        const p = window.indexOf(suf);
                        if (p !== -1) { localFound = p + sl; break; }
                    }
                }
            }

            // 3c. 兜底：窗口中点
            const insertPos = localFound !== -1 ? (lo + localFound) : Math.floor((lo + hi) / 2);
            attachToPara(r, insertPos, chapter);
            // 记录此次回退位置，供后续 pending 参考
            matchedPos.set(r.idx, insertPos);
        });
    }

    function attachToPara(r, insertPos, chapter) {
        const paraInfo = findParaForOffset(chapter.paraRanges, insertPos);
        if (!paraInfo) {
            r.chapterLevel = true;
            delete r.pending;
            return;
        }
        r.matchPos = insertPos;
        r.insertPos = insertPos;
        r.paraInfo = paraInfo;
        r.localInsert = insertPos - paraInfo.start;
        r.fallback = true;
        delete r.pending;
    }

    /**
     * 二分查找：定位 insertPos 落入哪个段落范围。
     * 边界情况：insertPos 正好等于某段落的 end 时，归入该段落（末端）。
     */
    function findParaForOffset(ranges, pos) {
        if (ranges.length === 0) return null;
        for (const r of ranges) {
            if (pos >= r.start && pos <= r.end) return r;
        }
        return null;
    }

    /**
     * 为整页插入三家注。只执行一次。
     *
     * 策略：先按 DOM 顺序收集所有段落，拼成章节全文；再在全文中一次性匹配每条注，
     * 最后根据 insertPos 定位回所在段落。这样 before_context 跨越 <li> 边界
     * （如"四至"列表）也能正确匹配。
     */
    function renderSanjia() {
        if (rendered || !notesData || notesData.length === 0) return;

        const EXCLUDE = 'nav, #settings-panel, #settings-toggle, header, footer, .chapter-nav, .sanjia-notes-container';
        const candidates = Array.from(document.querySelectorAll('p, blockquote, li'));
        const paragraphs = candidates.filter(el => {
            if (el.closest(EXCLUDE)) return false;
            if (!/[\u4e00-\u9fff]/.test(el.textContent)) return false;
            return true;
        });

        const chapter = buildChapterText(paragraphs);
        const matches = matchNotesInChapter(chapter, notesData);

        // 段落 → 该段匹配到的 matches 列表
        const byPara = new Map();
        const chapterOnly = [];
        matches.forEach(m => {
            if (m.chapterLevel || !m.paraInfo) {
                chapterOnly.push(m);
            } else {
                const para = m.paraInfo.para;
                if (!byPara.has(para)) byPara.set(para, []);
                byPara.get(para).push(m);
            }
        });

        // 按段落顺序（DOM 顺序）编号与渲染
        let counter = 1;
        paragraphs.forEach(p => {
            const arr = byPara.get(p);
            if (!arr || arr.length === 0) return;

            // 段内按 insertPos 升序编号，稳定
            arr.sort((a, b) => a.localInsert - b.localInsert);
            arr.forEach(m => { m.num = counter++; });

            // 插入编号标记：从后往前，避免位置偏移
            const byInsertDesc = arr.slice().sort((a, b) => b.localInsert - a.localInsert);
            byInsertDesc.forEach(m => {
                insertMarkerAt(p, m.localInsert, m.num);
            });

            // 生成注释容器
            let pnId = p.id ? p.id.replace(/^pn-/, '') : '';
            if (!pnId) {
                const paraNumEl = p.querySelector('a.para-num[id^="pn-"]');
                if (paraNumEl) pnId = paraNumEl.id.replace(/^pn-/, '');
            }
            const isSubPara = pnId.includes('.');
            const container = document.createElement('div');
            container.className = 'sanjia-notes-container';
            if (pnId) container.setAttribute('data-pn', pnId);
            if (isSubPara) container.setAttribute('data-sub', 'true');

            container.innerHTML = arr.map(m => buildNoteEntryHtml(m.num, m.note)).join('');

            // 若 p 在 <li> 内，容器插入到包围的 <ul>/<ol> 之后，避免块级元素进入列表
            let anchor = p;
            while (anchor.parentNode && (anchor.parentNode.tagName === 'UL' || anchor.parentNode.tagName === 'OL')) {
                anchor = anchor.parentNode;
            }
            anchor.parentNode.insertBefore(container, anchor.nextSibling);
        });

        // 拆分：真·章首注（无任何锚点，如 n001）vs 未能定位的孤儿注
        const chapterHead = [];
        const orphans = [];
        chapterOnly.forEach(m => {
            if (!m.note.items || m.note.items.length === 0) return;
            const hasAnyCtx = m.note.anchor_text || m.note.before_context || m.note.after_context;
            if (!hasAnyCtx) chapterHead.push(m);
            else orphans.push(m);
        });

        // 真·章首注：紧跟 h1，默认展开
        if (chapterHead.length > 0) {
            const container = document.createElement('div');
            container.className = 'sanjia-notes-container sanjia-notes-chapter';
            container.setAttribute('data-pn', 'chapter-head');
            let html = '<div class="sanjia-notes-heading">章首总注</div>';
            chapterHead.forEach(m => {
                html += renderNoteEntryPlain(m.note);
            });
            container.innerHTML = html;
            const h1 = document.querySelector('h1');
            if (h1 && h1.parentNode) h1.parentNode.insertBefore(container, h1.nextSibling);
        }

        // 未定位的孤儿注：放在章末，折叠展示（避免压没正文）
        if (orphans.length > 0) {
            const details = document.createElement('details');
            details.className = 'sanjia-notes-container sanjia-notes-orphans';
            details.setAttribute('data-pn', 'orphans');
            let html = `<summary class="sanjia-notes-heading">未能定位的注 (${orphans.length} 条) · 展开</summary>`;
            orphans.forEach(m => {
                html += renderNoteEntryPlain(m.note);
            });
            details.innerHTML = html;
            // 插入到 body 末尾前（排在章节末尾）
            document.body.appendChild(details);
        }

        bindInteractions();
        rendered = true;

        const matchedCount = matches.filter(m => !m.chapterLevel && m.paraInfo).length;
        console.log(`[sanjia] 渲染完成: 段落内 ${matchedCount}，章首 ${chapterHead.length}，未定位 ${orphans.length}`);
    }

    function renderNoteEntryPlain(note) {
        let html = '<div class="sanjia-note">';
        const displayAnchor = cleanAnchorForDisplay(note.anchor_text);
        if (displayAnchor) {
            html += `<span class="sanjia-note-anchor">${escapeHtml(displayAnchor)}</span>`;
        }
        html += '<div class="sanjia-note-items">';
        note.items.forEach(it => {
            html += `<div class="sanjia-note-item" data-source="${it.source}">`;
            html += `<span class="sanjia-source sanjia-source-${it.source}">${escapeHtml(it.label)}</span>`;
            html += `<span class="sanjia-text">${escapeHtml(it.text)}</span>`;
            html += `</div>`;
        });
        html += '</div></div>';
        return html;
    }

    /**
     * 使用文档级事件委托，使点击交互在 DOM 被重建后仍然生效
     * （如"智能分段"合并/恢复会 innerHTML+= 重建段落内容，丢失直接绑定的 listener）。
     */
    let delegationBound = false;
    function bindInteractions() {
        if (delegationBound) return;
        delegationBound = true;
        document.addEventListener('click', function(e) {
            const marker = e.target.closest && e.target.closest('.sanjia-anchor-marker');
            if (marker) {
                e.preventDefault();
                const num = marker.getAttribute('data-note-num');
                highlightPair(num);
                const note = document.querySelector(`.sanjia-note[data-note-num="${num}"]`);
                if (note) note.scrollIntoView({ behavior: 'smooth', block: 'center' });
                return;
            }
            const noteNum = e.target.closest && e.target.closest('.sanjia-note .sanjia-note-num');
            if (noteNum) {
                e.preventDefault();
                const noteEl = noteNum.closest('.sanjia-note');
                if (!noteEl) return;
                const num = noteEl.getAttribute('data-note-num');
                highlightPair(num);
                const mk = document.querySelector(`.sanjia-anchor-marker[data-note-num="${num}"]`);
                if (mk) mk.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        });
    }

    function highlightPair(num) {
        document.querySelectorAll('.sanjia-anchor-marker.highlighted, .sanjia-note.highlighted')
            .forEach(el => el.classList.remove('highlighted'));
        const marker = document.querySelector(`.sanjia-anchor-marker[data-note-num="${num}"]`);
        const note = document.querySelector(`.sanjia-note[data-note-num="${num}"]`);
        if (marker) marker.classList.add('highlighted');
        if (note) note.classList.add('highlighted');
    }

    async function setEnabled(enabled) {
        if (enabled) {
            document.body.classList.add('show-sanjia');
            await loadNotes();
            if (notesData) renderSanjia();
        } else {
            document.body.classList.remove('show-sanjia');
        }
    }

    window.ShijiSanjia = {
        setEnabled,
        isRendered: () => rendered
    };
})();
