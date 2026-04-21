/**
 * 史记知识库 - 配置面板配置定义
 * 集中定义所有显示选项，自动生成配置面板HTML
 */

(function() {
    'use strict';

    // 配置项定义
    const SETTINGS_CONFIG = [
        {
            id: 'syntax-highlight',
            label: '语法高亮',
            storageKey: 'shiji-syntax-highlight',
            defaultValue: true,  // 默认开启
            onChange: function(enabled) {
                updateSyntaxHighlight(enabled);
            }
        },
        {
            id: 'pinyin-display',
            label: '拼音注释',
            labelHTML: '拼音注释 <a href="../github-discussions/pronunciation-debates.html" target="_blank" style="font-size: 0.85em; color: #3498db; text-decoration: none; margin-left: 4px;" title="查看读音争议说明">[?]</a>',
            storageKey: 'shiji-pinyin-display',
            defaultValue: false,  // 默认关闭
            onChange: function(enabled) {
                updatePinyinDisplay(enabled);
            }
        },
        {
            id: 'traditional-chinese',
            label: '繁体显示',
            storageKey: 'shiji-traditional-chinese',
            defaultValue: false,  // 默认关闭（简体）
            onChange: function(enabled) {
                updateTraditionalChinese(enabled);
            }
        },
        {
            id: 'smart-paragraph',
            label: '智能分段',
            storageKey: 'shiji-smart-paragraph',
            defaultValue: true,  // 默认开启
            onChange: function(enabled) {
                updateSmartParagraph(enabled);
            }
        },
        {
            id: 'modern-translation',
            label: '白话翻译',
            labelHTML: '白话翻译 <span style="font-size:0.8em;color:#999;font-weight:normal;">（实验，仅001章）</span>',
            storageKey: 'shiji-modern-translation',
            defaultValue: false,  // 默认关闭
            onChange: function(enabled) {
                updateModernTranslation(enabled);
            }
        },
        {
            id: 'sanjia-notes',
            label: '三家注',
            labelHTML: '三家注 <span style="font-size:0.8em;color:#999;font-weight:normal;">（集解·索隐·正义）</span>',
            storageKey: 'shiji-sanjia-notes',
            defaultValue: false,  // 默认关闭
            onChange: function(enabled) {
                updateSanjiaNotes(enabled);
            }
        },
        {
            type: 'slider',
            id: 'font-size',
            label: '字体大小',
            storageKey: 'shiji-font-size',
            defaultValue: 16,
            min: 12,
            max: 28,
            step: 1,
            unit: 'px',
            onChange: function(value) {
                updateFontSize(value);
            }
        }
    ];

    /**
     * 更新字体大小（作用于 body，其他元素多用 em 相对单位）
     */
    function updateFontSize(value) {
        document.body.style.fontSize = value + 'px';
    }

    /**
     * 自动生成配置面板HTML
     */
    function generateSettingsPanel() {
        const panel = document.getElementById('settings-panel');
        if (!panel) {
            console.warn('[settings-panel] 未找到 settings-panel 元素');
            return;
        }

        // 清空现有内容
        panel.innerHTML = '';

        // 添加关闭按钮
        const closeButton = document.createElement('button');
        closeButton.id = 'settings-panel-close';
        closeButton.innerHTML = '✕';
        closeButton.setAttribute('aria-label', '关闭设置面板');
        panel.appendChild(closeButton);

        // 添加标题
        const title = document.createElement('h3');
        title.textContent = '显示设置';
        panel.appendChild(title);

        // 创建设置组
        const settingGroup = document.createElement('div');
        settingGroup.className = 'setting-group';

        // 为每个配置项创建控件
        SETTINGS_CONFIG.forEach(config => {
            if (config.type === 'slider') {
                const item = document.createElement('div');
                item.className = 'setting-item setting-slider';

                const savedRaw = localStorage.getItem(config.storageKey);
                const value = savedRaw === null ? config.defaultValue : Number(savedRaw);

                const labelRow = document.createElement('div');
                labelRow.className = 'setting-slider-label';
                const span = document.createElement('span');
                span.textContent = config.label;
                const valueSpan = document.createElement('span');
                valueSpan.className = 'setting-slider-value';
                valueSpan.textContent = value + (config.unit || '');
                labelRow.appendChild(span);
                labelRow.appendChild(valueSpan);

                const slider = document.createElement('input');
                slider.type = 'range';
                slider.id = config.id;
                slider.min = config.min;
                slider.max = config.max;
                slider.step = config.step || 1;
                slider.value = value;

                slider.addEventListener('input', function() {
                    const v = Number(this.value);
                    valueSpan.textContent = v + (config.unit || '');
                    localStorage.setItem(config.storageKey, String(v));
                    config.onChange(v);
                });

                item.appendChild(labelRow);
                item.appendChild(slider);
                settingGroup.appendChild(item);

                config.onChange(value);
                return;
            }

            const label = document.createElement('label');
            label.className = 'setting-item';

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = config.id;

            // 从 localStorage 读取保存的配置
            const savedValue = localStorage.getItem(config.storageKey);
            const isEnabled = savedValue === null ? config.defaultValue : savedValue === 'true';
            checkbox.checked = isEnabled;

            const span = document.createElement('span');
            // 如果有 labelHTML 字段，使用 innerHTML；否则使用 textContent
            if (config.labelHTML) {
                span.innerHTML = config.labelHTML;
            } else {
                span.textContent = config.label;
            }

            label.appendChild(checkbox);
            label.appendChild(span);
            settingGroup.appendChild(label);

            // 绑定事件处理器
            checkbox.addEventListener('change', function() {
                const enabled = this.checked;
                localStorage.setItem(config.storageKey, enabled.toString());
                config.onChange(enabled);
            });

            // 立即应用初始状态
            config.onChange(isEnabled);
        });

        panel.appendChild(settingGroup);
    }

    /**
     * 更新语法高亮
     */
    function updateSyntaxHighlight(enabled) {
        if (enabled) {
            document.body.classList.remove('syntax-highlight-off');
        } else {
            document.body.classList.add('syntax-highlight-off');
        }
    }

    /**
     * 更新拼音显示
     */
    function updatePinyinDisplay(enabled) {
        if (enabled) {
            document.body.classList.remove('pinyin-off');
        } else {
            document.body.classList.add('pinyin-off');
        }
    }

    /**
     * 更新繁简体显示
     */
    function updateTraditionalChinese(enabled) {
        // 繁简转换功能由 simp-trad-converter.js 实现
        // 这里只是触发事件，让转换器知道需要切换
        if (window.ShijiConverter) {
            if (enabled) {
                window.ShijiConverter.convertToTraditional();
            } else {
                window.ShijiConverter.convertToSimplified();
            }
        } else {
            console.warn('[settings-panel] ShijiConverter 未加载');
        }
    }

    /**
     * 更新智能分段
     * 当关闭时，按pn合并段落，所有共享顶级编号的段落合并成一个段落显示
     *
     * 新逻辑：从每个顶级段落开始，收集后面所有非顶级段落的内容，
     * 将它们的文本内容追加到顶级段落中，然后隐藏这些子段落元素
     *
     * 例如：11, 11.1, 11.2, 11.3, 11.4, 11.5 都合并到段落11中
     */
    function updateSmartParagraph(enabled) {
        if (enabled) {
            // 恢复：显示所有被隐藏的元素，清除标记
            document.querySelectorAll('[data-merged-content]').forEach(elem => {
                const originalContent = elem.getAttribute('data-original-content');
                if (originalContent) {
                    elem.innerHTML = originalContent;
                    elem.removeAttribute('data-original-content');
                    elem.removeAttribute('data-merged-content');
                }
            });

            document.querySelectorAll('[data-hidden-by-merge]').forEach(elem => {
                // 对于白话翻译，需要根据开关状态决定是否显示
                if (elem.classList.contains('modern-translation')) {
                    elem.style.display = document.body.classList.contains('show-translation') ? 'block' : 'none';
                } else {
                    elem.style.display = '';
                }
                elem.removeAttribute('data-hidden-by-merge');
            });

            // 恢复合并过的顶级翻译框内容
            document.querySelectorAll('.modern-translation[data-original-translation]').forEach(elem => {
                const contentEl = elem.querySelector('.translation-content');
                if (contentEl) {
                    contentEl.innerHTML = elem.getAttribute('data-original-translation');
                }
                elem.removeAttribute('data-original-translation');
            });

            // 恢复合并过的顶级三家注容器
            document.querySelectorAll('.sanjia-notes-container[data-original-sanjia]').forEach(elem => {
                elem.innerHTML = elem.getAttribute('data-original-sanjia');
                elem.removeAttribute('data-original-sanjia');
            });
            // 移除动态创建的三家注合并容器（当顶级段落原本无三家注时创建）
            document.querySelectorAll('.sanjia-notes-container[data-dynamically-merged]').forEach(elem => {
                elem.remove();
            });

            // 恢复对话和引用元素的样式
            document.querySelectorAll('.quoted, .dialogue').forEach(elem => {
                elem.style.display = '';
                elem.style.margin = '';
                elem.style.padding = '';
                elem.style.textIndent = '';
                elem.style.paddingLeft = '';
            });

            // 恢复孤立子段落的<br>标签
            document.querySelectorAll('[data-br-removed]').forEach(elem => {
                const originalContent = elem.getAttribute('data-original-br-content');
                if (originalContent) {
                    elem.innerHTML = originalContent;
                    elem.removeAttribute('data-original-br-content');
                    elem.removeAttribute('data-br-removed');
                }
            });

            document.body.classList.remove('merge-paragraphs');
        } else {
            document.body.classList.add('merge-paragraphs');

            // 获取所有段落、列表项和引用块，按DOM顺序
            const allElements = Array.from(document.querySelectorAll('p, li, ul, blockquote'));

            // 识别顶级段落
            const topLevelElements = [];
            allElements.forEach(elem => {
                const paraNum = elem.querySelector('a.para-num');
                if (paraNum && paraNum.id && paraNum.id.startsWith('pn-')) {
                    const numPart = paraNum.id.substring(3);
                    if (!numPart.includes('.')) {
                        // 这是顶级段落
                        topLevelElements.push({
                            element: elem,
                            topLevelNum: numPart
                        });
                    }
                }
            });

            // 对每个顶级段落，收集并合并其后的所有子段落
            topLevelElements.forEach((topLevel, index) => {
                const topElem = topLevel.element;
                const topNum = topLevel.topLevelNum;

                // 保存原始内容
                topElem.setAttribute('data-original-content', topElem.innerHTML);
                topElem.setAttribute('data-merged-content', 'true');

                // 查找下一个顶级段落的位置
                const nextTopElem = index < topLevelElements.length - 1
                    ? topLevelElements[index + 1].element
                    : null;

                // 收集当前顶级段落和下一个顶级段落之间的所有内容
                let currentElem = topElem.nextElementSibling;
                const contentParts = []; // 存储要合并的内容

                while (currentElem && currentElem !== nextTopElem) {
                    // 跳过h2, h3等标题，以及hr分隔线
                    if (currentElem.tagName.match(/^H[1-6]$/) || currentElem.tagName === 'HR') {
                        break; // 遇到标题或分隔线，停止收集
                    }

                    let shouldCollect = false;
                    let hasParaNum = false;

                    // 如果是UL，检查其中的li是否有段落编号
                    if (currentElem.tagName === 'UL') {
                        const lis = currentElem.querySelectorAll('li');
                        let hasMatchingLi = false;

                        lis.forEach(li => {
                            const liParaNum = li.querySelector('a.para-num');
                            if (liParaNum && liParaNum.id && liParaNum.id.startsWith('pn-')) {
                                hasParaNum = true;
                                const liNumPart = liParaNum.id.substring(3);
                                const liTopNum = liNumPart.split('.')[0];

                                if (liTopNum === topNum) {
                                    hasMatchingLi = true;
                                    // 隐藏编号，收集文本，同时移除br标签
                                    let content = li.innerHTML.replace(/<a[^>]*class="para-num"[^>]*>.*?<\/a>\s*/g, '');
                                    content = content.replace(/<br\s*\/?>/gi, '');
                                    contentParts.push(content);
                                }
                            } else {
                                // li没有段落编号，收集其内容
                                let content = li.innerHTML.replace(/<br\s*\/?>/gi, '');
                                contentParts.push(content);
                            }
                        });

                        // 如果ul有匹配的li，或者ul的li都没有编号（说明是列表内容），则隐藏
                        if (hasMatchingLi || !hasParaNum) {
                            shouldCollect = true;
                            currentElem.style.display = 'none';
                            currentElem.setAttribute('data-hidden-by-merge', 'true');
                        }
                    } else if (currentElem.tagName === 'P' || currentElem.tagName === 'LI' || currentElem.tagName === 'BLOCKQUOTE') {
                        // 检查P、LI或BLOCKQUOTE是否有段落编号
                        const paraNum = currentElem.querySelector('a.para-num');
                        if (paraNum && paraNum.id && paraNum.id.startsWith('pn-')) {
                            hasParaNum = true;
                            const numPart = paraNum.id.substring(3);
                            const elemTopNum = numPart.split('.')[0];

                            // 如果属于当前顶级编号
                            if (elemTopNum === topNum) {
                                shouldCollect = true;
                                // 隐藏编号，收集文本，同时移除br标签和换行符
                                let content = currentElem.innerHTML.replace(/<a[^>]*class="para-num"[^>]*>.*?<\/a>\s*/g, '');
                                content = content.replace(/<br\s*\/?>\s*/gi, ' ');
                                contentParts.push(content);
                                // 隐藏元素
                                currentElem.style.display = 'none';
                                currentElem.setAttribute('data-hidden-by-merge', 'true');

                                // 同时隐藏对应的白话翻译
                                const nextElem = currentElem.nextElementSibling;
                                if (nextElem && nextElem.classList.contains('modern-translation')) {
                                    nextElem.style.display = 'none';
                                    nextElem.setAttribute('data-hidden-by-merge', 'true');
                                }
                            } else {
                                // 属于不同的顶级编号，停止收集
                                break;
                            }
                        } else {
                            // 没有段落编号的P或BLOCKQUOTE，收集其内容
                            shouldCollect = true;
                            let content = currentElem.innerHTML.replace(/<br\s*\/?>\s*/gi, ' ');
                            contentParts.push(content);
                            currentElem.style.display = 'none';
                            currentElem.setAttribute('data-hidden-by-merge', 'true');
                        }
                    }

                    currentElem = currentElem.nextElementSibling;
                }

                // 将收集的内容追加到顶级段落
                if (contentParts.length > 0) {
                    topElem.innerHTML += contentParts.join('');
                }

                // 移除顶级段落内部的所有<br>标签和紧随其后的换行符，使内容连续显示
                topElem.innerHTML = topElem.innerHTML.replace(/<br\s*\/?>\s*/gi, ' ');

                // 将顶级段落内的所有块级元素改为行内元素
                topElem.querySelectorAll('ul, ol, li, div, p, blockquote').forEach(blockElem => {
                    blockElem.style.display = 'inline';
                    blockElem.style.margin = '0';
                    blockElem.style.padding = '0';
                });

                // 移除对话和引用的特殊样式（缩进、换行等）
                topElem.querySelectorAll('.quoted, .dialogue').forEach(elem => {
                    elem.style.display = 'inline';
                    elem.style.margin = '0';
                    elem.style.padding = '0';
                    elem.style.textIndent = '0';
                    elem.style.paddingLeft = '0';
                });

                // 将子段落的白话翻译合并到顶级翻译框中
                // topElem.nextElementSibling 是顶级段落的翻译框（若翻译已加载）
                const topTransDiv = topElem.nextElementSibling;
                if (topTransDiv && topTransDiv.classList.contains('modern-translation') &&
                    !topTransDiv.hasAttribute('data-hidden-by-merge')) {
                    const subTransParts = [];
                    document.querySelectorAll('.modern-translation[data-pn]').forEach(subTrans => {
                        const pn = subTrans.getAttribute('data-pn');
                        // 匹配属于本顶级编号的子翻译，如 topNum="1" 匹配 "1.1", "1.2" ...
                        if (pn && pn.startsWith(topNum + '.') && subTrans.hasAttribute('data-hidden-by-merge')) {
                            const contentEl = subTrans.querySelector('.translation-content');
                            if (contentEl) subTransParts.push(contentEl.innerHTML);
                        }
                    });
                    if (subTransParts.length > 0) {
                        const contentEl = topTransDiv.querySelector('.translation-content');
                        if (contentEl) {
                            // 保存原始内容以便恢复
                            topTransDiv.setAttribute('data-original-translation', contentEl.innerHTML);
                            // 追加子翻译内容
                            contentEl.innerHTML += subTransParts.join('');
                        }
                    }
                }

                // 合并子段落的三家注到顶级三家注容器（类比白话翻译合并）
                // 顶级容器用 data-pn=topNum 查找；子容器 data-pn 形如 "N.M" "N.M.K"
                const subSanjiaNotes = [];
                document.querySelectorAll(
                    `.sanjia-notes-container[data-sub][data-pn^="${topNum}."]`
                ).forEach(sub => {
                    const pn = sub.getAttribute('data-pn') || '';
                    // 仅匹配 topNum 为根的编号（避免 "10.1" 误匹配 topNum="1"）
                    if (pn.split('.')[0] !== topNum) return;
                    Array.from(sub.querySelectorAll('.sanjia-note')).forEach(note => {
                        subSanjiaNotes.push(note.outerHTML);
                    });
                });
                if (subSanjiaNotes.length > 0) {
                    const topSanjia = document.querySelector(
                        `.sanjia-notes-container[data-pn="${topNum}"]:not([data-sub])`
                    );
                    if (topSanjia) {
                        // 顶级段落本身有三家注：把子注追加进去
                        topSanjia.setAttribute('data-original-sanjia', topSanjia.innerHTML);
                        topSanjia.innerHTML += subSanjiaNotes.join('');
                    } else {
                        // 顶级段落原无三家注：动态创建一个容器承载子注
                        const newContainer = document.createElement('div');
                        newContainer.className = 'sanjia-notes-container';
                        newContainer.setAttribute('data-pn', topNum);
                        newContainer.setAttribute('data-dynamically-merged', 'true');
                        newContainer.innerHTML = subSanjiaNotes.join('');
                        // 插入到 topElem 之后，跳过紧跟的 <ul>/<ol> 与 modern-translation
                        let anchor = topElem;
                        while (anchor.nextElementSibling && (
                            anchor.nextElementSibling.tagName === 'UL' ||
                            anchor.nextElementSibling.tagName === 'OL'
                        )) {
                            anchor = anchor.nextElementSibling;
                        }
                        while (anchor.nextElementSibling &&
                               anchor.nextElementSibling.classList &&
                               anchor.nextElementSibling.classList.contains('modern-translation')) {
                            anchor = anchor.nextElementSibling;
                        }
                        if (anchor.parentNode) {
                            anchor.parentNode.insertBefore(newContainer, anchor.nextSibling);
                        }
                    }
                }
            });

            // 兜底处理：对于所有未被合并的子段落（孤立子段落，没有对应的顶级段落）
            // 也要移除其中的<br>标签，使其显示为连续文本
            document.querySelectorAll('p[id^="pn-"], blockquote[id^="pn-"]').forEach(elem => {
                // 跳过已经被合并处理的元素
                if (!elem.hasAttribute('data-merged-content') && !elem.hasAttribute('data-hidden-by-merge')) {
                    if (elem.innerHTML.includes('<br')) {
                        // 保存原始内容以便恢复
                        elem.setAttribute('data-original-br-content', elem.innerHTML);
                        // 移除<br>标签和换行符
                        elem.innerHTML = elem.innerHTML.replace(/<br\s*\/?>\s*/gi, ' ');
                        // 标记为已处理
                        elem.setAttribute('data-br-removed', 'true');
                    }
                }
            });
        }
    }

    /**
     * 更新白话翻译显示
     * 当启用时，加载并显示白话翻译内容；关闭时隐藏
     * 注意：白话翻译不受拼音和繁简转换影响
     */
    async function updateModernTranslation(enabled) {
        if (enabled) {
            document.body.classList.add('show-translation');

            // 从页面URL获取章节编号
            const pathMatch = window.location.pathname.match(/\/(\d{3})_/);
            if (!pathMatch) {
                console.warn('[settings-panel] 无法从URL提取章节编号');
                return;
            }

            const chapterNum = pathMatch[1];
            const translationUrl = `../translations/${chapterNum}.json`;

            try {
                // 加载翻译数据
                const response = await fetch(translationUrl);
                if (!response.ok) {
                    console.log(`[settings-panel] 章节${chapterNum}暂无白话翻译`);
                    return;
                }

                const translationData = await response.json();
                console.log(`[settings-panel] 已加载章节${chapterNum}的白话翻译`);

                // 为每个PN段落插入翻译
                // 支持范围键（如 '12.1-12.3'）：取起始pn作为定位锚点
                Object.keys(translationData.translations).forEach(pnKey => {
                    const translation = translationData.translations[pnKey];

                    // 解析范围键：'12.1-12.3' → startPn='12.1'，普通键直接使用
                    const dashIdx = pnKey.indexOf('-');
                    const startPn = (dashIdx > 0) ? pnKey.slice(0, dashIdx) : pnKey;

                    const pnElement = document.getElementById(`pn-${startPn}`);

                    if (pnElement) {
                        // 找到PN段落容器：
                        // - 若pnElement是<a>标签（id在内联锚点上），取其父元素（<p>/<li>等）
                        // - 若pnElement已是块级元素（如empty-para <div>，id直接在块上），直接使用
                        let paraElement = (pnElement.tagName === 'A')
                            ? pnElement.parentElement
                            : pnElement;

                        // 检查是否已经插入过翻译（用 data-pn 精确匹配，避免位置判断偏差）
                        let translationDiv = document.querySelector(`.modern-translation[data-pn="${pnKey}"]`);
                        if (translationDiv) {
                            // 已存在，只需显示
                            translationDiv.style.display = 'block';
                        } else {
                            // 创建翻译容器
                            translationDiv = document.createElement('div');
                            translationDiv.className = 'modern-translation pinyin-off';  // pinyin-off确保不受拼音影响
                            translationDiv.setAttribute('data-pn', pnKey);

                            // translation.text 已是预渲染的HTML（含<span class="person">等语义标注）
                            translationDiv.innerHTML = `<div class="translation-content">${translation.text}</div>`;

                            // 插入到原文段落后
                            // 若 paraElement 在 <ul>/<ol> 中（如 <li> 子段落），
                            // 块级 <div> 不能插入列表内部，需先跳出到列表层级
                            let insertAnchor = paraElement;
                            while (insertAnchor.parentNode &&
                                   (insertAnchor.parentNode.tagName === 'UL' ||
                                    insertAnchor.parentNode.tagName === 'OL')) {
                                insertAnchor = insertAnchor.parentNode;
                            }
                            // 再跳过后续紧跟的 <ul>/<ol>（如 empty-para 后的延续列表）
                            let nextSib = insertAnchor.nextElementSibling;
                            while (nextSib && (nextSib.tagName === 'UL' || nextSib.tagName === 'OL')) {
                                insertAnchor = nextSib;
                                nextSib = insertAnchor.nextElementSibling;
                            }
                            // 跳过已插入的翻译框，保持文档顺序（避免多个范围翻译倒序插入）
                            while (nextSib && nextSib.classList &&
                                   nextSib.classList.contains('modern-translation')) {
                                insertAnchor = nextSib;
                                nextSib = insertAnchor.nextElementSibling;
                            }
                            insertAnchor.parentNode.insertBefore(translationDiv, insertAnchor.nextSibling);
                        }
                    }
                });

            } catch (error) {
                console.error('[settings-panel] 加载白话翻译失败:', error);
            }

        } else {
            document.body.classList.remove('show-translation');

            // 隐藏所有翻译
            document.querySelectorAll('.modern-translation').forEach(elem => {
                elem.style.display = 'none';
            });

            console.log('[settings-panel] 白话翻译已关闭');
        }
    }

    /**
     * 更新三家注显示（由 sanjia-notes.js 实现加载与渲染）
     */
    async function updateSanjiaNotes(enabled) {
        // 模块可能晚于此处初始化，等待就绪后再调用
        const invoke = () => window.ShijiSanjia.setEnabled(enabled);
        if (window.ShijiSanjia) {
            invoke();
        } else {
            let attempts = 0;
            const timer = setInterval(() => {
                attempts++;
                if (window.ShijiSanjia) {
                    clearInterval(timer);
                    invoke();
                } else if (attempts > 50) {
                    clearInterval(timer);
                    console.warn('[settings-panel] ShijiSanjia 未加载');
                }
            }, 100);
        }
    }

    /**
     * 清理所有<br>标签后面的换行符
     * 防止在启用white-space: pre-line的元素中出现双重换行
     */
    function cleanupBrTags() {
        // 查找所有可能包含<br>标签的元素
        document.querySelectorAll('p, blockquote, div').forEach(elem => {
            // 只处理包含<br>标签的元素
            if (elem.innerHTML.includes('<br')) {
                // 移除<br>标签后的换行符和空白字符，但保留<br>标签本身
                elem.innerHTML = elem.innerHTML.replace(/(<br\s*\/?>)\s+/gi, '$1');
            }
        });
    }

    /**
     * 初始化配置面板
     */
    function init() {
        // 清理<br>标签后的换行符
        cleanupBrTags();

        // 生成配置面板HTML
        generateSettingsPanel();

        // 设置面板切换逻辑
        const settingsToggle = document.getElementById('settings-toggle');
        const settingsPanel = document.getElementById('settings-panel');
        const closeButton = document.getElementById('settings-panel-close');

        if (settingsToggle && settingsPanel) {
            // 切换面板显示/隐藏
            settingsToggle.addEventListener('click', function(e) {
                e.stopPropagation();
                settingsPanel.classList.toggle('active');
            });

            // 关闭按钮点击事件
            if (closeButton) {
                closeButton.addEventListener('click', function(e) {
                    e.stopPropagation();
                    settingsPanel.classList.remove('active');
                });
            }

            // 点击面板外关闭
            document.addEventListener('click', function(e) {
                if (!settingsPanel.contains(e.target) && e.target !== settingsToggle) {
                    settingsPanel.classList.remove('active');
                }
            });

            // 阻止在面板内点击时关闭
            settingsPanel.addEventListener('click', function(e) {
                e.stopPropagation();
            });
        }
    }

    // 等待 DOM 加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // 暴露配置项供外部使用（如果需要）
    window.ShijiSettings = {
        config: SETTINGS_CONFIG,
        addSetting: function(newConfig) {
            SETTINGS_CONFIG.push(newConfig);
            generateSettingsPanel(); // 重新生成面板
        }
    };

})();
