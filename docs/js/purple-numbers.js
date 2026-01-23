// Purple Numbers (PN) 点击复制功能
document.addEventListener('DOMContentLoaded', function() {
    // 为所有 PN 添加点击事件
    document.querySelectorAll('.para-num').forEach(function(pn) {
        pn.addEventListener('click', function(e) {
            e.preventDefault();

            // 获取完整的 URL（包含锚点）
            const url = window.location.href.split('#')[0] + this.getAttribute('href');

            // 复制到剪贴板
            navigator.clipboard.writeText(url).then(function() {
                // 显示复制成功提示
                const originalText = pn.textContent;
                pn.textContent = '✓';
                pn.style.color = '#4CAF50';

                setTimeout(function() {
                    pn.textContent = originalText;
                    pn.style.color = '';
                }, 1000);
            }).catch(function(err) {
                console.error('复制失败:', err);
                alert('复制失败，请手动复制链接');
            });
        });
    });
});
