/**
 * 史记知识库 - 统一JS导入模块
 *
 * 集中管理所有外部JavaScript库和CDN依赖
 * 所有章节HTML只需引入此文件即可
 *
 * 使用方法：
 * 在HTML <head> 中添加：
 * <script src="../js/shiji-imports.js"></script>
 */

(function() {
    'use strict';

    /**
     * 动态加载外部脚本
     * @param {string} src - 脚本URL
     * @param {object} options - 加载选项
     * @returns {Promise} - 加载完成的Promise
     */
    function loadScript(src, options = {}) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = src;

            // 设置脚本属性
            if (options.defer) script.defer = true;
            if (options.async) script.async = true;
            if (options.integrity) script.integrity = options.integrity;
            if (options.crossOrigin) script.crossOrigin = options.crossOrigin;

            script.onload = () => {
                console.log(`[imports] ✓ 加载成功: ${src}`);
                resolve();
            };
            script.onerror = () => {
                console.error(`[imports] ✗ 加载失败: ${src}`);
                reject(new Error(`Failed to load script: ${src}`));
            };

            document.head.appendChild(script);
        });
    }

    /**
     * 依赖项配置
     */
    const DEPENDENCIES = {
        // 第三方库（优先使用本地，CDN作为后备）
        libs: [
            {
                name: 'OpenCC.js',
                local: '../libs/opencc.min.js',  // 本地路径
                cdn: 'https://cdn.jsdelivr.net/npm/opencc-js@1.0.5/dist/umd/full.min.js',  // CDN后备
                options: {},
                required: true  // 是否必需（失败时是否阻塞）
            }
            // 未来可以添加更多库
            // {
            //     name: 'Chart.js',
            //     local: '../libs/chart.min.js',
            //     cdn: 'https://cdn.jsdelivr.net/npm/chart.js@4.0.0/dist/chart.umd.min.js',
            //     options: {},
            //     required: false
            // }
        ],

        // 本地脚本（按依赖顺序加载）
        local: [
            // 基础功能（无依赖）
            '../js/purple-numbers.js',
            '../js/heading-pinyin.js',

            // 繁简转换（依赖OpenCC.js）
            '../js/simp-trad-converter.js',

            // 配置面板（最后加载，依赖转换器）
            '../js/settings-panel-config.js',

            // 报错按钮（独立功能，无依赖）
            '../js/report-issue-button.js'

            // 未来添加的脚本在这里追加
        ]
    };

    /**
     * 加载第三方库（优先本地，失败时降级到CDN）
     * @param {object} lib - 库配置
     */
    async function loadLibrary(lib) {
        // 优先尝试本地版本
        try {
            await loadScript(lib.local, lib.options);
            console.log(`[imports] ✓ ${lib.name} 使用本地版本`);
            return;
        } catch (error) {
            console.warn(`[imports] 本地版本加载失败: ${lib.name}，尝试CDN...`);
        }

        // 降级到CDN
        if (lib.cdn) {
            try {
                await loadScript(lib.cdn, lib.options);
                console.log(`[imports] ✓ ${lib.name} 使用CDN版本`);
                return;
            } catch (error) {
                if (lib.required) {
                    throw new Error(`${lib.name} 加载失败（本地和CDN均失败）`);
                } else {
                    console.warn(`[imports] 可选库加载失败: ${lib.name}`);
                }
            }
        } else if (lib.required) {
            throw new Error(`${lib.name} 本地版本加载失败且无CDN后备`);
        }
    }

    /**
     * 异步加载所有依赖
     */
    async function loadAllDependencies() {
        console.log('[imports] 开始加载依赖...');
        const startTime = performance.now();

        try {
            // 第一步：加载第三方库（优先本地，降级CDN）
            console.log('[imports] 加载第三方库...');
            const libPromises = DEPENDENCIES.libs.map(lib => loadLibrary(lib));
            await Promise.all(libPromises);

            // 第二步：按顺序加载本地脚本
            console.log('[imports] 加载本地脚本...');
            for (const scriptPath of DEPENDENCIES.local) {
                await loadScript(scriptPath, {});
            }

            const elapsed = (performance.now() - startTime).toFixed(2);
            console.log(`[imports] ✓ 所有依赖加载完成，耗时 ${elapsed}ms`);

        } catch (error) {
            console.error('[imports] ✗ 依赖加载失败:', error);
            // 可以在这里添加用户友好的错误提示
        }
    }

    /**
     * 初始化
     */
    function init() {
        // 检查是否在浏览器环境
        if (typeof window === 'undefined' || typeof document === 'undefined') {
            console.error('[imports] 不在浏览器环境中运行');
            return;
        }

        // 等待DOM加载完成
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', loadAllDependencies);
        } else {
            // DOM已加载，立即执行
            loadAllDependencies();
        }
    }

    // 启动
    init();

    // 暴露接口（如果需要手动重新加载）
    window.ShijiImports = {
        reload: loadAllDependencies,
        dependencies: DEPENDENCIES
    };

})();
