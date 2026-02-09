/**
 * 实体索引页面搜索过滤
 * 监听输入框，按名称和别名过滤实体条目
 */
document.addEventListener('DOMContentLoaded', function() {
    var input = document.getElementById('filter-input');
    if (!input) return;

    var entries = document.querySelectorAll('.entity-entry');

    input.addEventListener('input', function() {
        var query = this.value.trim().toLowerCase();

        if (!query) {
            // 清空搜索时显示全部
            for (var i = 0; i < entries.length; i++) {
                entries[i].style.display = '';
            }
            return;
        }

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
    });
});
