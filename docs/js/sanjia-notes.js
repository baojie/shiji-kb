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
     * 章节文本保留部分传统字形（如 "於" "然後" "蟲"），notes 经 opencc t2s 成简体后为
     * "于" "然后" "虫"，两侧不一致导致匹配失败。这里做 1:1 字符映射把双方归一到同一规范形，
     * 由于是字符级 1:1 映射，字符偏移量不变，indexOf 位置可直接套用回原文。
     *
     * 映射原则：归并到简体常用字（多数情况）。
     */
    const VARIANT_MAP = {
        // 虚词/常用字：章节保留传统，notes t2s 成简体
        '於': '于',
        '後': '后',
        '蟲': '虫',
        '衛': '卫', '衞': '卫',
        '擒': '禽',  // 章节 "擒杀" vs notes "禽杀"
        '䇲': '策',
        '䝙': '貙',
        // 其他常见异体
        '徧': '遍',
        '悳': '德',
        '辠': '罪',
        '愬': '诉',
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
        if (note.anchor_text) {
            html += `<span class="sanjia-note-anchor">${escapeHtml(note.anchor_text)}</span>`;
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
            if (matchPos === -1) {
                results.push({ note, idx, chapterLevel: true });
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
        return results;
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
        if (note.anchor_text) {
            html += `<span class="sanjia-note-anchor">${escapeHtml(note.anchor_text)}</span>`;
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
