#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从标注的史记章节中提取分类词表
"""

import os
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple

# 定义11类实体的标记模式
ENTITY_PATTERNS = {
    '人名': (r'@([^@]+)@', '@'),
    '地名': (r'=([^=]+)=', '='),
    '官职': (r'\$([^\$]+)\$', '$'),
    '时间': (r'%([^%]+)%', '%'),
    '朝代': (r'&([^&]+)&', '&'),
    '制度': (r'\^([^\^]+)\^', '^'),
    '族群': (r'~([^~]+)~', '~'),
    '器物': (r'\*([^\*]+)\*', '*'),
    '天文': (r'!([^!]+)!', '!'),
    '神话': (r'\?([^\?]+)\?', '?'),
    '动植物': (r'🌿([^🌿]+)🌿', '🌿'),
}

class VocabularyBuilder:
    def __init__(self, chapter_dir: str):
        self.chapter_dir = Path(chapter_dir)
        # 存储: {类别: {词条: [(章节名, 上下文)]}}
        self.vocabularies: Dict[str, Dict[str, List[Tuple[str, str]]]] = {
            category: defaultdict(list) for category in ENTITY_PATTERNS.keys()
        }

    def extract_entities_from_file(self, file_path: Path):
        """从单个文件中提取实体"""
        chapter_name = file_path.stem.replace('.tagged', '')

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')

        for category, (pattern, marker) in ENTITY_PATTERNS.items():
            matches = re.finditer(pattern, content)

            for match in matches:
                entity = match.group(1).strip()
                if not entity:
                    continue

                # 获取上下文（包含该实体的段落）
                start_pos = match.start()

                # 找到所在行
                context_line = None
                pos = 0
                for line in lines:
                    if pos <= start_pos < pos + len(line) + 1:
                        context_line = line.strip()
                        break
                    pos += len(line) + 1

                # 清理上下文，移除段落编号和其他标记
                if context_line:
                    # 移除段落编号 [x.x.x]
                    context = re.sub(r'^\[[\d\.]+\]\s*', '', context_line)
                    # 限制长度
                    if len(context) > 100:
                        context = context[:100] + '...'
                else:
                    context = match.group(0)

                self.vocabularies[category][entity].append((chapter_name, context))

    def process_all_files(self):
        """处理所有tagged.md文件"""
        tagged_files = list(self.chapter_dir.glob('*.tagged.md'))
        print(f"发现 {len(tagged_files)} 个标注文件")

        for i, file_path in enumerate(tagged_files, 1):
            print(f"  [{i}/{len(tagged_files)}] 处理: {file_path.name}")
            self.extract_entities_from_file(file_path)

        print("\n提取完成！")

    def generate_vocabulary_file(self, category: str, output_dir: Path):
        """生成单个类别的词表文件"""
        vocab_data = self.vocabularies[category]

        if not vocab_data:
            print(f"  {category}: 0 个词条（跳过）")
            return

        # 按词条出现次数排序
        sorted_entries = sorted(vocab_data.items(),
                               key=lambda x: len(x[1]),
                               reverse=True)

        # 生成文件名
        filename_map = {
            '人名': '01_人名词表.md',
            '地名': '02_地名词表.md',
            '官职': '03_官职词表.md',
            '时间': '04_时间词表.md',
            '朝代': '05_朝代词表.md',
            '制度': '06_制度词表.md',
            '族群': '07_族群词表.md',
            '器物': '08_器物词表.md',
            '天文': '09_天文词表.md',
            '神话': '10_神话词表.md',
            '动植物': '11_动植物词表.md',
        }

        output_file = output_dir / filename_map[category]

        with open(output_file, 'w', encoding='utf-8') as f:
            # 写入标题和说明
            marker = ENTITY_PATTERNS[category][1]
            f.write(f"# 史记{category}词表\n\n")
            f.write(f"> 标记符号：`{marker}词条{marker}`  \n")
            f.write(f"> 词条总数：**{len(sorted_entries)}**  \n")
            f.write(f"> 总出现次数：**{sum(len(contexts) for _, contexts in sorted_entries)}**  \n")
            f.write(f"> 数据来源：{len(list(self.chapter_dir.glob('*.tagged.md')))} 个已标注章节\n\n")
            f.write("---\n\n")

            # 写入词条
            for i, (entity, contexts) in enumerate(sorted_entries, 1):
                f.write(f"## {i}. {entity}\n\n")
                f.write(f"**出现次数**：{len(contexts)} 次\n\n")

                # 按章节分组
                chapters_dict = defaultdict(list)
                for chapter, context in contexts:
                    chapters_dict[chapter].append(context)

                f.write(f"**出现章节**：{', '.join(sorted(set(c for c, _ in contexts)))}\n\n")

                # 列出典型用例（最多5个）
                f.write("**典型用例**：\n\n")
                unique_contexts = []
                seen = set()
                for chapter, context in contexts:
                    if context not in seen:
                        unique_contexts.append((chapter, context))
                        seen.add(context)
                    if len(unique_contexts) >= 5:
                        break

                for chapter, context in unique_contexts:
                    # 高亮当前词条
                    highlighted = context.replace(f'{marker}{entity}{marker}',
                                                 f'**{marker}{entity}{marker}**')
                    f.write(f"- 【{chapter}】{highlighted}\n")

                f.write("\n")

        print(f"  {category}: {len(sorted_entries)} 个词条 → {output_file.name}")

    def generate_all_vocabularies(self, output_dir: Path):
        """生成所有类别的词表"""
        output_dir.mkdir(parents=True, exist_ok=True)

        print("\n" + "="*60)
        print("生成词表文件")
        print("="*60 + "\n")

        for category in ENTITY_PATTERNS.keys():
            self.generate_vocabulary_file(category, output_dir)

        # 生成总索引
        self.generate_index(output_dir)

    def generate_index(self, output_dir: Path):
        """生成词表总索引"""
        index_file = output_dir / 'README.md'

        with open(index_file, 'w', encoding='utf-8') as f:
            f.write("# 史记分类词表索引\n\n")
            f.write("> 本词表从《史记》已标注章节中自动提取，包含11类实体词汇。\n\n")

            # 统计信息
            total_entries = sum(len(vocab) for vocab in self.vocabularies.values())
            total_occurrences = sum(
                sum(len(contexts) for contexts in vocab.values())
                for vocab in self.vocabularies.values()
            )

            f.write("## 统计信息\n\n")
            f.write(f"- 标注章节数：{len(list(self.chapter_dir.glob('*.tagged.md')))} 篇\n")
            f.write(f"- 词条总数：{total_entries} 个\n")
            f.write(f"- 标注总数：{total_occurrences} 次\n\n")

            f.write("## 词表列表\n\n")
            f.write("| 序号 | 类别 | 标记 | 词条数 | 文件 |\n")
            f.write("|------|------|------|--------|------|\n")

            filename_map = {
                '人名': '01_人名词表.md',
                '地名': '02_地名词表.md',
                '官职': '03_官职词表.md',
                '时间': '04_时间词表.md',
                '朝代': '05_朝代词表.md',
                '制度': '06_制度词表.md',
                '族群': '07_族群词表.md',
                '器物': '08_器物词表.md',
                '天文': '09_天文词表.md',
                '神话': '10_神话词表.md',
                '动植物': '11_动植物词表.md',
            }

            for i, (category, (_, marker)) in enumerate(ENTITY_PATTERNS.items(), 1):
                count = len(self.vocabularies[category])
                filename = filename_map[category]
                f.write(f"| {i} | {category} | `{marker}` | {count} | [{filename}](./{filename}) |\n")

            f.write("\n## 使用说明\n\n")
            f.write("每个词表文件包含以下信息：\n\n")
            f.write("- **词条名称**：提取的实体词汇\n")
            f.write("- **出现次数**：该词条在所有章节中出现的总次数\n")
            f.write("- **出现章节**：包含该词条的章节列表\n")
            f.write("- **典型用例**：该词条的实际使用示例（带上下文）\n\n")

            f.write("## 标注规则\n\n")
            f.write("实体标注使用特定符号标记：\n\n")
            for category, (_, marker) in ENTITY_PATTERNS.items():
                f.write(f"- **{category}**：`{marker}词条{marker}`\n")

        print(f"\n  索引文件: README.md")

def main():
    """主函数"""
    print("\n" + "="*60)
    print("史记分类词表构建工具")
    print("="*60 + "\n")

    chapter_dir = "chapter_md"
    output_dir = Path("kg/vocabularies")

    # 创建构建器
    builder = VocabularyBuilder(chapter_dir)

    # 提取实体
    print("第一步：从标注文件中提取实体\n")
    builder.process_all_files()

    # 生成词表
    print("\n第二步：生成词表文件\n")
    builder.generate_all_vocabularies(output_dir)

    print("\n" + "="*60)
    print("词表构建完成！")
    print(f"输出目录：{output_dir}")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
