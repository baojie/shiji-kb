#!/usr/bin/env python3
"""为缺失的高频断链页面创建 redirect 文件。

筛选规则：
1. 目标页面在 top 100 最频繁引用的缺失页面中
2. 有明确的 redirect 目标（同一个人物/地点的标准页面）
3. 目标页面文件存在

用法：
  python3 scripts/create_missing_redirects.py
"""
import os, re

PAGES_DIR = 'docs/wiki/pages'

# Manual mapping: broken link target -> existing page to redirect to
# Based on analysis of top 100 missing pages
REDIRECT_MAP = {
    # === 人物 —— 有标准页面 ===
    '汉武帝': '刘彻',
    '吕太后': '吕后',
    '梁孝王刘武': '梁孝王',
    '白公胜': '白公胜作乱',
    '越王勾践': '041_越王勾践世家',
    '纣王': '商纣王',
    '周庄王': '东周庄王',
    '周景王': '东周景王',
    '周顷王': '东周顷王',
    '周慎靓王': '周慎靓王',
    '慎靓王': '周慎靓王',
    '曲沃武公': '曲沃武公并晋',
    '子比': '叔向论子比不能立（五难论）',
    '齐王建': '齐王建坐视五国覆亡',
    '白圭': '白圭经商法',
    '秦嘉': '秦嘉叛陈',
    '恶来': '恶来事纣与蜚廉之死',
    '景驹': '击败秦嘉景驹',
    '开方': '成开方',
    '楚威王': '说楚威王合从',
    '河间献王': '河间献王好儒',
    '夏桀': '夏桀殷纣穷武而亡',
    '月氏': '张骞至大月氏大夏',

    # === 国家/朝代 ===
    '西汉': '西汉侯国分布图',
    '韩国': '韩国灭亡',
}

def create_redirect(source_name, target_name):
    """Create a redirect page: source.md -> [[target]]"""
    fp = os.path.join(PAGES_DIR, f'{source_name}.md')
    if os.path.exists(fp):
        return f'SKIP: {source_name}.md already exists'

    # Check target exists
    target_fp = os.path.join(PAGES_DIR, f'{target_name}.md')
    if not os.path.exists(target_fp):
        return f'SKIP: target {target_name}.md does not exist'

    # Get target's label for frontmatter
    content = open(target_fp, encoding='utf-8').read()
    label_m = re.search(r'^label:\s*(.+)', content, re.MULTILINE)
    label = label_m.group(1).strip().strip('"\'') if label_m else source_name
    id_m = re.search(r'^id:\s*(.+)', content, re.MULTILINE)
    pid = id_m.group(1).strip().strip('"\'') if id_m else source_name

    redirect_content = f"""---
id: {source_name}
type: redirect
label: {source_name}
redirect: {target_name}
quality: redirect
---

#REDIRECT [[{target_name}]]
"""
    with open(fp, 'w', encoding='utf-8') as f:
        f.write(redirect_content)
    return f'CREATE: {source_name}.md → [[{target_name}]]'

def main():
    created = 0
    skipped = 0
    for source, target in REDIRECT_MAP.items():
        result = create_redirect(source, target)
        if result.startswith('CREATE'):
            print(result)
            created += 1
        else:
            print(result)
            skipped += 1

    print(f'\n创建 {created} 个 redirect, 跳过 {skipped} 个')

if __name__ == '__main__':
    main()
