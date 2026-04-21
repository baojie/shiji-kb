#!/usr/bin/env python3
"""
渲染成语典故HTML页面
将成语JSON数据渲染为带实体高亮的HTML页面
"""

import json
import re
from pathlib import Path
import sys

# 导入统一的语义标签处理模块
sys.path.insert(0, str(Path(__file__).parent))
from semantic_tags import render_tags_to_html, get_entity_css_styles


def render_entity_tags(text):
    """将实体标注转换为HTML span标签（使用统一标准）"""
    return render_tags_to_html(text, normalize_legacy=True)

def highlight_chengyu_in_original(original_text, chengyu_name, shiji_form=None):
    """
    在纯净文本中高亮（加粗）锚句关键字。
    假定输入已是去标注 + 去段号的纯文本，不再包含〖〗等标记。

    优先级（长者先匹配）：
    1. shiji_form 完整形（如消歧情形下的原文形式）
    2. 成语本身完整形
    3. 成语 2+2 拆分（例如"网开三面" → "网开"、"三面"）
    4. 对复合成语（含"/"）逐项匹配
    """
    import html
    text = html.escape(original_text)

    keywords = []
    if shiji_form:
        keywords.append(shiji_form)
        # shiji_form 也按内部分句拆
        for part in re.split(r'[，、；。]', shiji_form):
            part = part.strip()
            if len(part) >= 2:
                keywords.append(part)

    if '/' in chengyu_name:
        keywords.extend(chengyu_name.split('/'))
    else:
        clean = chengyu_name.strip()
        keywords.append(clean)
        # 按内部标点分句
        if re.search(r'[，、；。]', clean):
            for part in re.split(r'[，、；。]', clean):
                part = part.strip()
                if len(part) >= 2:
                    keywords.append(part)
        elif len(clean) >= 4:
            keywords.append(clean[:2])
            keywords.append(clean[2:4])

    # 去重，按长度排序（长的先匹配）
    seen = set()
    unique = []
    for k in keywords:
        k = (k or '').strip()
        if len(k) >= 2 and k not in seen:
            seen.add(k)
            unique.append(k)
    unique.sort(key=len, reverse=True)

    for k in unique:
        pattern = re.compile(f'(?<!<strong>)({re.escape(html.escape(k))})(?![^<]*</strong>)')
        text = pattern.sub(r'<strong>\1</strong>', text, count=0)

    return text

def generate_html(json_path, output_path):
    """生成HTML页面"""

    # 读取JSON数据（标注过的成语）
    with open(json_path, 'r', encoding='utf-8') as f:
        chengyu_data = json.load(f)

    # 每条加标记
    for item in chengyu_data:
        item['is_summarized'] = False

    # 合并"总结性"条目（未标注但与原文相关的）
    summarized_path = Path(json_path).parent / 'chengyu_summarized.json'
    if summarized_path.exists():
        with open(summarized_path, 'r', encoding='utf-8') as f:
            summ_doc = json.load(f)
        for e in summ_doc.get('entries', []):
            chengyu_data.append({
                'chapter_num': e['chapter_num'],
                'chapter_title': e['chapter_title'],
                'chengyu': e['chengyu'],
                'shiji_form': '',
                'original': e.get('original', ''),
                'meaning': e.get('meaning', ''),
                'context': e.get('context', ''),
                'paragraph': e.get('paragraph') or '',
                'annotated': False,
                'is_summarized': True,
                'verified': e.get('verified', ''),
                'anchor': e.get('anchor') or '',
            })

    # 再次排序（按章节 + 成语名）
    chengyu_data.sort(key=lambda x: (x['chapter_num'], 0 if not x.get('is_summarized') else 1, x['chengyu']))

    # 按章节分组
    by_chapter = {}
    for item in chengyu_data:
        chapter_key = f"{item['chapter_num']}_{item['chapter_title']}"
        if chapter_key not in by_chapter:
            by_chapter[chapter_key] = []
        by_chapter[chapter_key].append(item)

    # 统计定位成功数
    located_count = sum(1 for item in chengyu_data if item.get('context'))

    # 生成成语索引（按拼音首字母分组）
    chengyu_index = []
    for item in chengyu_data:
        chengyu_index.append({
            'name': item['chengyu'],
            'meaning': item.get('meaning', ''),
            'chapter': f"{item['chapter_num']} {item['chapter_title']}",
            'id': f"cy_{item['chapter_num']}_{chengyu_data.index(item)}"
        })

    # 生成HTML
    html = '''<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>史记成语典故集</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: "Source Han Serif SC", "Noto Serif SC", serif;
            line-height: 2;
            color: #333;
            background-color: #fdfaf6;
            padding: 20px;
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        h1 {
            text-align: center;
            color: #8b4513;
            font-size: 2.5em;
            margin-bottom: 10px;
            border-bottom: 3px double #8b4513;
            padding-bottom: 20px;
        }

        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 40px;
            font-size: 1.1em;
        }

        .nav {
            background: #f5f5f5;
            padding: 15px;
            margin-bottom: 30px;
            border-radius: 5px;
        }

        .nav a {
            color: #8b4513;
            text-decoration: none;
            margin-right: 20px;
        }

        .nav a:hover {
            text-decoration: underline;
        }

        .nav a.pdf {
            color: #c00;
            font-weight: bold;
        }

        .chapter-section {
            margin-bottom: 60px;
        }

        .chapter-header {
            font-size: 1.8em;
            color: #8b4513;
            margin-bottom: 20px;
            border-left: 5px solid #8b4513;
            padding-left: 15px;
        }

        .chengyu-item {
            margin-bottom: 40px;
            border-left: 3px solid #d4a373;
            padding-left: 20px;
        }

        .item-title {
            font-size: 1.6em;
            color: #8b4513;
            margin-bottom: 10px;
            font-weight: bold;
        }

        .item-meaning {
            font-size: 1em;
            color: #666;
            margin-bottom: 15px;
            font-style: italic;
        }

        .item-original {
            font-size: 1.1em;
            color: #444;
            margin-bottom: 15px;
            padding: 10px;
            background: #f9f6f2;
            border-left: 3px solid #c9a56c;
        }

        .item-original strong {
            color: #8b4513;
            font-weight: 700;
            text-decoration: underline;
            text-decoration-color: #d4a373;
            text-decoration-thickness: 2px;
            text-underline-offset: 2px;
        }

        .item-meta {
            font-size: 0.9em;
            color: #999;
            margin-bottom: 10px;
        }

        .pn-link {
            color: #8b4513;
            text-decoration: none;
            border-bottom: 1px dotted #c9a56c;
        }

        .pn-link:hover {
            color: #c00;
            border-bottom-color: #c00;
        }

        .item-context {
            line-height: 2.2;
            color: #555;
            padding: 15px;
            background: #fefdfb;
            border: 1px solid #e9e3d9;
            border-radius: 3px;
        }

        .no-context {
            color: #999;
            font-style: italic;
        }

        /* 使用统一的实体标注样式 */
        .entity {
            font-weight: 500;
            border-bottom: 1px dotted;
            cursor: help;
        }

        .entity.person { color: #c00; border-bottom-color: #c00; }
        .entity.time { color: #06c; border-bottom-color: #06c; }
        .entity.place { color: #080; border-bottom-color: #080; }
        .entity.office { color: #660; border-bottom-color: #660; }
        .entity.war { color: #690; border-bottom-color: #690; }
        .entity.ref { color: #999; border-bottom-color: #999; }
        .entity.other { color: #999; border-bottom-color: #999; }

        /* 搜索框样式 */
        .search-box {
            margin-bottom: 30px;
        }

        .search-box input {
            width: 100%;
            padding: 12px;
            font-size: 1.1em;
            border: 1px solid #ccc;
            border-radius: 3px;
            font-family: inherit;
        }

        .search-box input:focus {
            outline: none;
            border-color: #8b4513;
            box-shadow: 0 0 5px rgba(139, 69, 19, 0.3);
        }

        .search-stats {
            margin-top: 10px;
            color: #666;
            font-size: 0.9em;
        }

        /* 索引样式 */
        .index-section {
            background: #fafafa;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 5px;
            border: 1px solid #ddd;
        }

        .index-header {
            font-size: 1.3em;
            color: #8b4513;
            margin-bottom: 15px;
            font-weight: bold;
            cursor: pointer;
            user-select: none;
        }

        .index-header:hover {
            color: #a0522d;
        }

        .index-content {
            display: none;
            columns: 3;
            column-gap: 20px;
        }

        .index-content.show {
            display: block;
        }

        .index-item {
            break-inside: avoid;
            margin-bottom: 8px;
            padding: 5px 0;
        }

        .index-item a {
            color: #8b4513;
            text-decoration: none;
            display: block;
        }

        .index-item a:hover {
            color: #c00;
            text-decoration: underline;
        }

        .index-item .chapter-label {
            color: #999;
            font-size: 0.85em;
            margin-left: 5px;
        }

        .hidden {
            display: none !important;
        }

        .highlight-match {
            background: yellow;
            font-weight: bold;
        }

        .chengyu-item.summarized {
            border-left-color: #999;
            background: #fcfbf9;
        }

        .summ-badge {
            display: inline-block;
            font-size: 0.6em;
            padding: 2px 8px;
            margin-left: 10px;
            border-radius: 10px;
            vertical-align: middle;
            font-weight: normal;
        }

        .summ-verbatim {
            background: #e8f4ea;
            color: #4a7a4f;
            border: 1px solid #a8c7ad;
        }

        .summ-partial {
            background: #f4eee8;
            color: #7a674a;
            border: 1px solid #c7b4a8;
        }

        .summ-narrative {
            background: #ede8f4;
            color: #4f4a7a;
            border: 1px solid #a8a8c7;
        }

        .footer {
            text-align: center;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #999;
            font-size: 0.9em;
        }

        @media (max-width: 768px) {
            .container {
                padding: 20px;
            }
            h1 {
                font-size: 1.8em;
            }
            .index-content {
                columns: 1;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>史记成语典故集</h1>
        <div class="subtitle">史记中共有 ''' + str(len(chengyu_data)) + ''' 条成语典故 | 定位 ''' + str(located_count) + ''' 条原文</div>

        <div class="nav">
            <a href="../index.html">← 返回首页</a>
            <a href="special_index.html">专项索引</a>
            <a href="chengyu.pdf" class="pdf">📥 下载PDF</a>
        </div>

        <!-- 搜索框 -->
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="搜索成语、释义或出处...（如：破釜沉舟、项羽、决心）" />
            <div class="search-stats" id="searchStats"></div>
        </div>

        <!-- 成语索引 -->
        <div class="index-section">
            <div class="index-header" onclick="toggleIndex()">📑 成语索引（点击展开/收起）</div>
            <div class="index-content" id="indexContent">
'''

    # 生成索引列表
    for item in chengyu_index:
        html += f'''                <div class="index-item">
                    <a href="#{item['id']}">{item['name']}<span class="chapter-label">{item['chapter']}</span></a>
                </div>
'''

    html += '''            </div>
        </div>

'''

    # 按章节顺序输出
    item_index = 0
    for chapter_key in sorted(by_chapter.keys()):
        items = by_chapter[chapter_key]
        chapter_num, chapter_title = chapter_key.split('_', 1)

        html += f'''
        <div class="chapter-section" id="chapter-{chapter_num}">
            <div class="chapter-header">{chapter_num} {chapter_title}（{len(items)}条）</div>

'''

        for item in items:
            chengyu = item['chengyu']
            meaning = item['meaning']
            context = item.get('context', '')
            paragraph = item.get('paragraph', '')
            item_id = f"cy_{chapter_num}_{item_index}"
            item_index += 1

            summ_label = ''
            if item.get('is_summarized'):
                verified = item.get('verified', '')
                badges = {
                    'verbatim': '原文可证',
                    'partial': '原文部分可证',
                    'narrative': '叙事性总结',
                }
                summ_label = f' <span class="summ-badge summ-{verified}">总结 · {badges.get(verified, verified)}</span>'

            html += f'''
            <div class="chengyu-item{' summarized' if item.get('is_summarized') else ''}" id="{item_id}" data-chengyu="{chengyu}" data-meaning="{meaning}" data-chapter="{chapter_title}">
                <div class="item-title">{chengyu}{summ_label}</div>
                <div class="item-meaning">{meaning}</div>
'''

            if paragraph:
                chap_filename = f"{chapter_num}_{chapter_title}.html"
                link = f"../chapters/{chap_filename}#pn-{paragraph}"
                html += f'                <div class="item-meta">位置：<a href="{link}" class="pn-link">{chapter_num} {chapter_title} · 第 {paragraph} 段</a></div>\n'

            shiji_form = item.get('shiji_form') or item.get('anchor') or ''
            if context:
                context_html = highlight_chengyu_in_original(context, chengyu, shiji_form)
                html += f'''                <div class="item-context">{context_html}</div>
'''
            else:
                original = highlight_chengyu_in_original(item.get('original', ''), chengyu, shiji_form)
                html += f'                <div class="item-original">{original}</div>\n'
                if not item.get('is_summarized'):
                    html += '                <div class="no-context">（原文位置未定位）</div>\n'

            html += '            </div>\n\n'

        html += '        </div>\n\n'

    html += '''
        <div class="footer">
            <p>史记知识库 | 成语典故专项索引</p>
            <p>数据提取自《史记》标注版本</p>
        </div>
    </div>

    <script>
        // 搜索功能
        const searchInput = document.getElementById('searchInput');
        const searchStats = document.getElementById('searchStats');
        const chengyuItems = document.querySelectorAll('.chengyu-item');
        const chapterSections = document.querySelectorAll('.chapter-section');

        searchInput.addEventListener('input', function() {
            const query = this.value.trim().toLowerCase();

            if (!query) {
                // 清空搜索，显示所有
                chengyuItems.forEach(item => item.classList.remove('hidden'));
                chapterSections.forEach(section => section.classList.remove('hidden'));
                searchStats.textContent = '';
                return;
            }

            let matchCount = 0;
            const visibleChapters = new Set();

            // 搜索每个成语项
            chengyuItems.forEach(item => {
                const chengyu = item.dataset.chengyu.toLowerCase();
                const meaning = item.dataset.meaning.toLowerCase();
                const chapter = item.dataset.chapter.toLowerCase();
                const text = item.textContent.toLowerCase();

                if (chengyu.includes(query) ||
                    meaning.includes(query) ||
                    chapter.includes(query) ||
                    text.includes(query)) {
                    item.classList.remove('hidden');
                    matchCount++;
                    // 记录该成语所在章节应该显示
                    const chapterSection = item.closest('.chapter-section');
                    if (chapterSection) {
                        visibleChapters.add(chapterSection.id);
                    }
                } else {
                    item.classList.add('hidden');
                }
            });

            // 隐藏没有匹配项的章节
            chapterSections.forEach(section => {
                if (visibleChapters.has(section.id)) {
                    section.classList.remove('hidden');
                } else {
                    section.classList.add('hidden');
                }
            });

            // 更新统计信息
            if (matchCount === 0) {
                searchStats.textContent = '未找到匹配结果';
                searchStats.style.color = '#c00';
            } else {
                searchStats.textContent = `找到 ${matchCount} 条匹配结果`;
                searchStats.style.color = '#060';
            }
        });

        // 索引展开/收起
        function toggleIndex() {
            const indexContent = document.getElementById('indexContent');
            indexContent.classList.toggle('show');
        }

        // 点击索引链接后滚动到对应位置
        document.querySelectorAll('.index-item a').forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const targetId = this.getAttribute('href').substring(1);
                const targetElement = document.getElementById(targetId);
                if (targetElement) {
                    targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    // 高亮效果
                    targetElement.style.backgroundColor = '#fff8dc';
                    setTimeout(() => {
                        targetElement.style.backgroundColor = '';
                    }, 2000);
                }
            });
        });

        // 快捷键支持：Ctrl+F 或 Command+F 聚焦搜索框
        document.addEventListener('keydown', function(e) {
            if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
                e.preventDefault();
                searchInput.focus();
                searchInput.select();
            }
        });
    </script>
</body>
</html>
'''

    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✓ HTML 已生成: {output_path}")

def main():
    project_root = Path(__file__).parent.parent
    # 从data/目录读取JSON
    json_path = project_root / "data/chengyu.json"
    # 保存HTML到docs/special/
    output_path = project_root / "docs/special/chengyu.html"

    if not json_path.exists():
        print(f"错误: JSON文件不存在: {json_path}")
        print("请先运行 extract_chengyu.py")
        return 1

    generate_html(json_path, output_path)
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
