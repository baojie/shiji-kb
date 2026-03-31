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
            span.textContent = config.label;

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
     * 初始化配置面板
     */
    function init() {
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
