/**
 * 实体索引页面搜索过滤
 * 监听输入框，按名称和别名过滤实体条目
 * 同时控制字母分节和拼音导航栏的显隐
 */
document.addEventListener('DOMContentLoaded', function() {
    var input = document.getElementById('filter-input');
    if (!input) return;

    var entries = document.querySelectorAll('.entity-entry');
    var sections = document.querySelectorAll('.letter-section');
    var pinyinNav = document.querySelector('.pinyin-nav');

    input.addEventListener('input', function() {
        var query = this.value.trim().toLowerCase();

        if (!query) {
            // 清空搜索时显示全部
            for (var i = 0; i < entries.length; i++) {
                entries[i].style.display = '';
            }
            for (var i = 0; i < sections.length; i++) {
                sections[i].style.display = '';
            }
            if (pinyinNav) pinyinNav.style.display = '';
            return;
        }

        // 搜索时隐藏拼音导航
        if (pinyinNav) pinyinNav.style.display = 'none';

        for (var i = 0; i < entries.length; i++) {
            var entry = entries[i];
            var name = entry.querySelector('.canonical-name');
            var aliases = entry.querySelector('.alias-list');

            var nameText = name ? name.textContent.toLowerCase() : '';
            var aliasText = aliases ? aliases.textContent.toLowerCase() : '';

            if (nameText.indexOf(query) !== -1 || aliasText.indexOf(query) !== -1) {
                entry.style.display = '';
            } else {
                entry.style.display = 'none';
            }
        }

        // 隐藏没有可见条目的字母分节
        for (var i = 0; i < sections.length; i++) {
            var section = sections[i];
            var visibleEntries = section.querySelectorAll('.entity-entry:not([style*="display: none"])');
            section.style.display = visibleEntries.length > 0 ? '' : 'none';
        }
    });
});
