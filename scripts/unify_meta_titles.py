#!/usr/bin/env python3
"""
统一元技能文档的标题格式为：META: 标题 — 副标题
"""

from pathlib import Path


# 标题映射表：文件名 -> 新标题
TITLE_MAP = {
    '00-META-04_柳叶刀方法.md': 'META: 柳叶刀方法 — 精细分解与混合解决方案',
    '00-META-05_知识作为上下文压缩.md': 'META: 知识作为上下文压缩 — KG的价值论证',
    '00-META-06_SKILL优化与演化.md': 'META: SKILL优化与演化 — 方法论文档的持续改进',
    '00-META-07_可读性.md': 'META: 可读性 — 人类优先的数据格式设计',
    '00-META-11_数据体感培养.md': 'META: 数据体感培养 — 直接观察数据的十层体系',
    '00-META-12_数据融合.md': 'META: 数据融合 — 多源数据对齐与消歧',
    '00-META-13_技能迁移.md': 'META: 技能迁移 — SKILL跨项目复用方法论',
    '00-META-14_好东西都是总结出来的.md': 'META: 好东西都是总结出来的 — 元技能的元技能',
}


def unify_title(file_path: Path) -> bool:
    """统一文档标题"""
    if file_path.name not in TITLE_MAP:
        print(f"⊙ {file_path.name}: 标题格式已正确，跳过")
        return False

    new_title = TITLE_MAP[file_path.name]
    content = file_path.read_text(encoding='utf-8')

    # 替换第一行
    lines = content.split('\n')
    old_title = lines[0]
    lines[0] = f'# {new_title}'

    new_content = '\n'.join(lines)
    file_path.write_text(new_content, encoding='utf-8')

    print(f"✓ {file_path.name}")
    print(f"  旧: {old_title}")
    print(f"  新: # {new_title}")
    return True


def main():
    skills_dir = Path('skills')
    meta_files = sorted(skills_dir.glob('00-META-*.md'))

    processed_count = 0
    for file_path in meta_files:
        if unify_title(file_path):
            processed_count += 1

    print(f"\n总计修改: {processed_count} 个文档")


if __name__ == '__main__':
    main()
