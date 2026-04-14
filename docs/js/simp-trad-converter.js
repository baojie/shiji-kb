/**
 * 史记知识库 - 繁简转换器
 *
 * 功能：
 * 1. 使用 OpenCC (opencc-js) 进行基础繁简转换
 * 2. 使用特殊词汇对照表进行二次校正
 * 3. 保留原始HTML结构和标注符号
 *
 * 依赖：
 * - OpenCC.js (通过CDN引入)
 * - 简繁转换自定义词表 (s2t-custom-variants.json)
 */

(function() {
    'use strict';

    // OpenCC 转换器实例
    let converter = null;

    // 特殊词汇对照表（简体→繁体）
    let customVariants = null;

    // 当前显示模式（'simplified' | 'traditional'）
    let currentMode = 'simplified';

    // 原始文本缓存（用于恢复简体）
    const originalTextCache = new Map();

    /**
     * 初始化 OpenCC 转换器
     */
    async function initOpenCC() {
        try {
            // 使用 OpenCC.js 的 s2t (Simplified to Traditional) 转换
            converter = OpenCC.Converter({ from: 'cn', to: 'tw' });
            console.log('[converter] OpenCC 初始化成功');
            return true;
        } catch (error) {
            console.error('[converter] OpenCC 初始化失败:', error);
            return false;
        }
    }

    /**
     * 加载特殊词汇对照表
     */
    async function loadCustomVariants() {
        try {
            const response = await fetch('../data/s2t-custom-variants.json');
            if (response.ok) {
                customVariants = await response.json();
                console.log('[converter] 简繁转换自定义词表加载成功，共', Object.keys(customVariants).length, '条');
                return true;
            } else {
                console.warn('[converter] 简繁转换自定义词表未找到，将只使用 OpenCC 标准转换');
                customVariants = {};
                return false;
            }
        } catch (error) {
            console.warn('[converter] 简繁转换自定义词表加载失败:', error);
            customVariants = {};
            return false;
        }
    }

    /**
     * 转换文本（简体→繁体）
     * @param {string} text - 要转换的文本
     * @returns {string} - 转换后的文本
     */
    function convertText(text) {
        if (!text || !converter) return text;

        // 步骤1: 使用 OpenCC 进行基础转换
        let result = converter(text);

        // 步骤2: 应用特殊词汇对照表进行校正
        if (customVariants && Object.keys(customVariants).length > 0) {
            // 按词汇长度降序排序，优先匹配长词
            const entries = Object.entries(customVariants).sort((a, b) => b[0].length - a[0].length);

            for (const [simp, trad] of entries) {
                // 使用全局替换
                const regex = new RegExp(escapeRegExp(simp), 'g');
                result = result.replace(regex, trad);
            }
        }

        return result;
    }

    /**
     * 转换DOM节点（递归处理）
     * @param {Node} node - 要转换的DOM节点
     * @param {boolean} toTraditional - true=转繁体, false=恢复简体
     */
    function convertNode(node, toTraditional) {
        // 跳过不需要转换的节点
        if (shouldSkipNode(node)) {
            return;
        }

        // 处理文本节点
        if (node.nodeType === Node.TEXT_NODE) {
            const text = node.textContent;
            if (!text.trim()) return; // 跳过空白文本

            if (toTraditional) {
                // 转换为繁体
                if (!originalTextCache.has(node)) {
                    originalTextCache.set(node, text); // 缓存原始文本
                }
                node.textContent = convertText(text);
            } else {
                // 恢复简体
                if (originalTextCache.has(node)) {
                    node.textContent = originalTextCache.get(node);
                }
            }
            return;
        }

        // 递归处理子节点
        if (node.childNodes && node.childNodes.length > 0) {
            Array.from(node.childNodes).forEach(child => {
                convertNode(child, toTraditional);
            });
        }
    }

    /**
     * 判断是否应该跳过该节点
     */
    function shouldSkipNode(node) {
        if (!node) return true;

        // 跳过 script, style, code 等标签
        const skipTags = ['SCRIPT', 'STYLE', 'CODE', 'PRE'];
        if (node.nodeType === Node.ELEMENT_NODE && skipTags.includes(node.tagName)) {
            return true;
        }

        // 跳过特定 class（如果需要）
        if (node.nodeType === Node.ELEMENT_NODE && node.classList) {
            // 保留 Purple Numbers（段落编号）不转换
            if (node.classList.contains('para-num')) {
                return true;
            }
            // 白话翻译保持简体（现代白话文无需繁化）
            if (node.classList.contains('modern-translation')) {
                return true;
            }
        }

        return false;
    }

    /**
     * 转换整个页面到繁体
     */
    function convertToTraditional() {
        if (currentMode === 'traditional') {
            console.log('[converter] 已经是繁体模式');
            return;
        }

        if (!converter) {
            console.error('[converter] OpenCC 未初始化');
            return;
        }

        console.log('[converter] 开始转换为繁体...');
        const startTime = performance.now();

        // 白话翻译保持简体：转换前保存内容，转换后恢复
        const transElems = document.querySelectorAll('.modern-translation');
        const savedHTML = new Map();
        transElems.forEach(el => savedHTML.set(el, el.innerHTML));

        // 转换主内容区域
        convertNode(document.body, true);

        // 恢复白话翻译为简体
        savedHTML.forEach((html, el) => { el.innerHTML = html; });

        currentMode = 'traditional';
        document.body.classList.add('traditional-mode');

        const elapsed = (performance.now() - startTime).toFixed(2);
        console.log(`[converter] 繁体转换完成，耗时 ${elapsed}ms`);
    }

    /**
     * 恢复简体
     */
    function convertToSimplified() {
        if (currentMode === 'simplified') {
            console.log('[converter] 已经是简体模式');
            return;
        }

        console.log('[converter] 恢复简体...');
        const startTime = performance.now();

        // 白话翻译保持简体：转换前保存内容，转换后恢复
        const transElems = document.querySelectorAll('.modern-translation');
        const savedHTML = new Map();
        transElems.forEach(el => savedHTML.set(el, el.innerHTML));

        // 恢复主内容区域
        convertNode(document.body, false);

        // 恢复白话翻译（防止 convertNode 误清缓存导致内容丢失）
        savedHTML.forEach((html, el) => { el.innerHTML = html; });

        currentMode = 'simplified';
        document.body.classList.remove('traditional-mode');

        const elapsed = (performance.now() - startTime).toFixed(2);
        console.log(`[converter] 简体恢复完成，耗时 ${elapsed}ms`);
    }

    /**
     * 转义正则表达式特殊字符
     */
    function escapeRegExp(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    /**
     * 初始化转换器
     */
    async function init() {
        console.log('[converter] 初始化繁简转换器...');

        // 等待 OpenCC.js 加载
        if (typeof OpenCC === 'undefined') {
            console.error('[converter] OpenCC.js 未加载，请检查 CDN 引用');
            return;
        }

        // 初始化 OpenCC
        const openccReady = await initOpenCC();
        if (!openccReady) {
            console.error('[converter] 转换器初始化失败');
            return;
        }

        // 加载特殊词汇对照表
        await loadCustomVariants();

        // 暴露全局接口
        window.ShijiConverter = {
            convertToTraditional,
            convertToSimplified,
            getCurrentMode: () => currentMode
        };

        console.log('[converter] 转换器初始化完成');
    }

    // 等待 DOM 和 OpenCC.js 都加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            // 延迟一点，确保 OpenCC.js 已加载
            setTimeout(init, 100);
        });
    } else {
        setTimeout(init, 100);
    }

})();
