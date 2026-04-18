/**
 * 实体索引页面搜索过滤
 * - 文本搜索：按名称和别名过滤
 * - 地段分类筛选（仅地名页）：多选开关按钮
 *     · "全部" 独立键：按下后清空其他所有选中，恢复显示全部
 *     · 其他键：可多选，点击一次按下加入过滤集合，再点一次弹起移除
 *     · 无任何分类键按下时，视同"全部"（显示所有条目），"全部"键保持按下态
 * 两者组合生效；同时控制字母分节和拼音导航栏的显隐
 */
document.addEventListener('DOMContentLoaded', function() {
    var input = document.getElementById('filter-input');
    var entries = document.querySelectorAll('.entity-entry');
    var sections = document.querySelectorAll('.letter-section');
    var pinyinNav = document.querySelector('.pinyin-nav');
    var catChips = document.querySelectorAll('.cat-chip');

    // state.cats: 已选中分类的集合（用普通对象模拟 Set，兼容旧浏览器）
    // 空对象 = 显示全部
    var state = { text: '', cats: {} };

    function catsEmpty() {
        for (var k in state.cats) {
            if (Object.prototype.hasOwnProperty.call(state.cats, k)) return false;
        }
        return true;
    }

    function applyFilter() {
        var query = state.text;
        var anyCat = !catsEmpty();

        for (var i = 0; i < entries.length; i++) {
            var entry = entries[i];
            var name = entry.querySelector('.canonical-name');
            var aliases = entry.querySelector('.alias-list');
            var nameText = name ? name.textContent.toLowerCase() : '';
            var aliasText = aliases ? aliases.textContent.toLowerCase() : '';

            var textMatch = !query || nameText.indexOf(query) !== -1 || aliasText.indexOf(query) !== -1;

            var catMatch = true;
            if (anyCat) {
                var entryCat = entry.getAttribute('data-category') || '';
                // 多标签：data-category 用 | 分隔，如 "县|城邑"
                //   - 条目分类为空 → 匹配 __blank__
                //   - 否则：任一分类在 state.cats 中被选中即命中
                if (entryCat === '') {
                    catMatch = !!state.cats['__blank__'];
                } else {
                    var entryCats = entryCat.split('|');
                    catMatch = false;
                    for (var k = 0; k < entryCats.length; k++) {
                        if (state.cats[entryCats[k]]) {
                            catMatch = true;
                            break;
                        }
                    }
                }
            }

            entry.style.display = (textMatch && catMatch) ? '' : 'none';
        }

        // 隐藏没有可见条目的字母分节
        for (var i = 0; i < sections.length; i++) {
            var section = sections[i];
            var visibleEntries = section.querySelectorAll('.entity-entry:not([style*="display: none"])');
            section.style.display = visibleEntries.length > 0 ? '' : 'none';
        }

        // 启用文本搜索或分类筛选（非全部）时隐藏拼音导航
        if (pinyinNav) {
            pinyinNav.style.display = (query || anyCat) ? 'none' : '';
        }
    }

    function refreshChipStates() {
        var empty = catsEmpty();
        for (var j = 0; j < catChips.length; j++) {
            var chip = catChips[j];
            var key = chip.getAttribute('data-cat-filter') || '';
            if (key === '') {
                // "全部" 按钮：当无任何分类选中时按下
                chip.classList.toggle('active', empty);
            } else {
                chip.classList.toggle('active', !!state.cats[key]);
            }
        }
    }

    if (input) {
        input.addEventListener('input', function() {
            state.text = this.value.trim().toLowerCase();
            applyFilter();
        });
    }

    if (catChips && catChips.length) {
        for (var i = 0; i < catChips.length; i++) {
            catChips[i].addEventListener('click', function(e) {
                e.preventDefault();
                var key = this.getAttribute('data-cat-filter') || '';

                if (key === '') {
                    // "全部"：清空所有分类选择
                    state.cats = {};
                } else {
                    // 其他分类：切换开关
                    if (state.cats[key]) {
                        delete state.cats[key];
                    } else {
                        state.cats[key] = true;
                    }
                }
                refreshChipStates();
                applyFilter();
            });
        }
        // 初始化：默认"全部"按下
        refreshChipStates();
    }
});
