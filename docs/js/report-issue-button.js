/**
 * 史记知识库 - 浮动报错按钮
 * 提供用户截屏报错到 GitHub Issues 的快捷入口
 */

(function() {
    'use strict';

    /**
     * 创建报错按钮
     */
    function createReportButton() {
        const button = document.createElement('button');
        button.id = 'report-issue-button';
        button.title = '发现错误？点击报告';
        button.innerHTML = '⚠️'; // 警告标志
        button.setAttribute('aria-label', '报告问题');

        // 点击事件
        button.addEventListener('click', function() {
            openReportIssue();
        });

        document.body.appendChild(button);
    }

    /**
     * 打开 GitHub Issues 页面
     */
    function openReportIssue() {
        // 获取当前页面信息
        const currentUrl = window.location.href;
        const pageTitle = document.title;

        // 构建 Issue body 模板
        const issueBody = `
### 问题描述
[请描述您发现的问题]

### 页面位置
- 页面: ${pageTitle}
- URL: ${currentUrl}

### 截图
[请在此处粘贴截图]

### 其他信息
[如有其他补充信息请在此处说明]
`.trim();

        // 构建 GitHub Issues URL
        const githubIssuesUrl = 'https://github.com/baojie/shiji-kb/issues/new';
        const params = new URLSearchParams({
            title: `[报错] ${pageTitle}`,
            body: issueBody,
            labels: 'bug,用户报告'
        });

        // 打开新窗口
        window.open(`${githubIssuesUrl}?${params.toString()}`, '_blank');
    }

    /**
     * 初始化
     */
    function init() {
        // 等待 DOM 加载完成
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', createReportButton);
        } else {
            createReportButton();
        }
    }

    // 启动
    init();

    // 暴露接口供外部调用
    window.ShijiReportIssue = {
        open: openReportIssue
    };

})();
