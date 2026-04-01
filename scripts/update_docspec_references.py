#!/usr/bin/env python3
"""
更新所有文件中对 doc/spec 下文件的引用
"""

import os
import re
from pathlib import Path

# 文件重命名映射表
RENAME_MAP = {
    # SPEC_ 类
    "标注格式规范": "SPEC_标注格式",
    "动词标注规范": "SPEC_动词标注",
    "段落编号规范": "SPEC_段落编号",
    "拼音标注质量规范v3.0": "SPEC_拼音标注质量v3.0",
    "拼音注释功能规范": "SPEC_拼音注释功能",
    "紫色编号设计": "SPEC_紫色编号设计",
    "配置面板扩展指南": "SPEC_配置面板扩展",

    # RENDER_ 类
    "动词渲染规则": "RENDER_动词规则",
    "实体渲染规划": "RENDER_实体规划",
    "实体渲染规划_v6_增强版": "RENDER_实体规划v6",
    "CSS版本历史_v5.4": "RENDER_CSS历史v5.4",

    # PLAN_ 类
    "实体标注方案": "PLAN_实体标注",
    "人物生卒年反思流程": "PLAN_人物生卒年反思",
    "官职词表构建计划": "PLAN_官职词表构建",
    "通用词表构建计划": "PLAN_通用词表构建",
    "史记辞典规划": "PLAN_史记辞典",
    "姓氏制度": "PLAN_姓氏制度",
    "谥号索引需求说明": "PLAN_谥号索引需求",

    # ANALYSIS_ 类
    "多音字处理方案总结": "ANALYSIS_多音字处理",
    "繁简词库对比分析": "ANALYSIS_繁简词库对比",
    "繁简体词库构造方案": "ANALYSIS_繁简体词库构造",
    "繁简映射87字完整词频表": "ANALYSIS_繁简映射87字词频",
    "繁简映射分析总结": "ANALYSIS_繁简映射总结",
    "繁简映射统计报告": "ANALYSIS_繁简映射统计",
    "OpenCC错误率分析": "ANALYSIS_OpenCC错误率",
    "骑字多音规则说明": "ANALYSIS_骑字多音规则",

    # DATA_ 类
    "单字扩展为词组规则": "DATA_单字扩展词组规则",
    "低频字符词库规则建议": "DATA_低频字符词库规则",
    "繁简映射数据": "DATA_繁简映射",
    "新增词库规则v3.0": "DATA_新增词库规则v3.0",
    "真实错误分析": "DATA_真实错误分析",

    # GUIDE_ 类
    "校验工具使用指南": "GUIDE_校验工具",
    "校验覆盖范围": "GUIDE_校验覆盖范围",

    # CHANGELOG_ 类
    "更新说明v3.0.1": "CHANGELOG_v3.0.1",
    "更新说明v3.0.2": "CHANGELOG_v3.0.2",
    "更新说明v3.1": "CHANGELOG_v3.1",
    "custom-variants更新日志": "CHANGELOG_custom-variants",
}

def update_file(filepath):
    """更新单个文件中的引用"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # 替换所有引用
    for old_name, new_name in RENAME_MAP.items():
        # 匹配 .md 和 .json 文件
        for ext in ['.md', '.json']:
            old_full = old_name + ext
            new_full = new_name + ext

            # 替换各种可能的引用格式
            # 1. 直接文件名引用（带路径）
            content = content.replace(f"doc/spec/{old_full}", f"doc/spec/{new_full}")
            content = content.replace(f"../doc/spec/{old_full}", f"../doc/spec/{new_full}")
            content = content.replace(f"../../doc/spec/{old_full}", f"../../doc/spec/{new_full}")

            # 2. Markdown 链接中的引用（只替换链接部分，不替换显示文本）
            # 格式: [显示文本](path/to/file.md)
            content = re.sub(
                rf'\[([^\]]+)\]\(((?:\.\./)*doc/spec/{re.escape(old_full)})\)',
                rf'[\1](\2)',
                content
            )
            content = re.sub(
                rf'\(((?:\.\./)*doc/spec/){re.escape(old_full)}\)',
                rf'(\1{new_full})',
                content
            )

            # 3. 反引号包裹的路径
            content = re.sub(
                rf'`((?:\.\./)*doc/spec/){re.escape(old_full)}`',
                rf'`\1{new_full}`',
                content
            )

    # 如果有变化，写回文件
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    """主函数：遍历所有需要更新的文件"""
    repo_root = Path(__file__).parent.parent

    # 需要检查的目录和文件扩展名
    check_dirs = [
        'skills',
        'doc',
        'docs',
        'scripts',
        'kg',
        'resources',
        'logs',
        'data'
    ]
    check_extensions = ['.md', '.py', '.json', '.html']

    # 也检查根目录的特定文件
    root_files = ['README.md', 'TODO.md', 'CHANGELOG.md']

    updated_files = []

    # 更新根目录文件
    for filename in root_files:
        filepath = repo_root / filename
        if filepath.exists():
            if update_file(filepath):
                updated_files.append(str(filepath.relative_to(repo_root)))

    # 更新各目录中的文件
    for dir_name in check_dirs:
        dir_path = repo_root / dir_name
        if not dir_path.exists():
            continue

        for ext in check_extensions:
            for filepath in dir_path.rglob(f'*{ext}'):
                # 跳过某些目录
                skip_dirs = {'.git', 'node_modules', '__pycache__', 'archive'}
                if any(skip in filepath.parts for skip in skip_dirs):
                    continue

                if update_file(filepath):
                    updated_files.append(str(filepath.relative_to(repo_root)))

    # 输出结果
    if updated_files:
        print(f"✅ 已更新 {len(updated_files)} 个文件:")
        for f in sorted(updated_files):
            print(f"  - {f}")
    else:
        print("⚠️ 没有找到需要更新的文件")

if __name__ == '__main__':
    main()
