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
            labelHTML: '拼音注释 <a href="../pronunciation-debates.html" target="_blank" style="font-size: 0.85em; color: #3498db; text-decoration: none; margin-left: 4px;" title="查看读音争议说明">[?]</a>',
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
        }
    ];

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

        // 添加标题
        const title = document.createElement('h3');
        title.textContent = '显示设置';
        panel.appendChild(title);

        // 创建设置组
        const settingGroup = document.createElement('div');
        settingGroup.className = 'setting-group';

        // 为每个配置项创建checkbox
        SETTINGS_CONFIG.forEach(config => {
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
                elem.style.display = '';
                elem.removeAttribute('data-hidden-by-merge');
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

        if (settingsToggle && settingsPanel) {
            // 切换面板显示/隐藏
            settingsToggle.addEventListener('click', function(e) {
                e.stopPropagation();
                settingsPanel.classList.toggle('active');
            });

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
