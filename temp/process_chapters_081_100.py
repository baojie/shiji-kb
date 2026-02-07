#!/usr/bin/env python3
"""
批量处理《史记》081-100章节（列传）
使用Claude API进行实体标注和结构化处理
"""

import anthropic
import os
import sys
from pathlib import Path


# 章节列表
CHAPTERS = [
    "081_廉颇蔺相如列传",
    "082_田单列传",
    "083_鲁仲连邹阳列传",
    "084_屈原贾生列传",
    "085_吕不韦列传",
    "086_刺客列传",
    "087_李斯列传",
    "088_蒙恬列传",
    "089_张耳陈馀列传",
    "090_魏豹彭越列传",
    "091_黥布列传",
    "092_淮阴侯列传",
    "093_韩信卢绾列传",
    "094_田儋列传",
    "095_樊郦滕灌列传",
    "096_张丞相列传",
    "097_郦生陆贾列传",
    "098_傅靳蒯成列传",
    "099_刘敬叔孙通列传",
    "100_季布栾布列传",
]


SYSTEM_PROMPT = """你是《史记》专家，擅长对古文进行结构化标注和实体识别。

你的任务是将《史记》列传原文处理成结构化的Markdown格式，并进行实体标注。

## 输出格式要求

### 1. 文档结构
- **一级标题**：# [0] [列传名]
- **二级标题**：按人物和事件划分
  - 对于合传（如"廉颇蔺相如列传"），为每个主要人物设立二级标题
  - 包括：家世、早年、主要事迹、太史公曰等
- **三级标题**：细分重要事件（如"完璧归赵"、"渑池之会"等）
- **段落编号**：使用圣经式编号 [章.节]（如 [1.1]、[1.2]等）

### 2. 实体标注规则
- 人名: @人名@（如：@廉颇@、@蔺相如@、@韩信@）
- 地名: =地名=
- 官职: $官职$
- 时间/纪年: %时间%
- 朝代/氏族/国号: &朝代&
- 制度/典章: ^制度^
- 族群/部落: ~族群~
- 器物/礼器: *器物*
- 天文/历法: !天文!
- 传说/神话: ?神话?
- 动植物: 🌿动植物🌿

### 3. 特殊注意事项
1. **合传处理**：一个列传包含多人时，需要清晰划分每个人物的部分
2. **对话处理**：对话使用引用块（> 符号），保持对话的独立性
3. **长对话标注**：长对话前可添加 NOTE 说明（如：> NOTE: 蔺相如说辞）
4. **段落分段**：合理分段，保持可读性
5. **保持原文**：不改变原文内容，只添加结构和标注

### 4. 输出要求
- 直接输出处理好的Markdown文本
- 不要添加任何解释性文字
- 不要使用代码块包裹输出
- 确保所有实体都被正确标注
- 保持原文的完整性

## 示例格式

```markdown
# [0] 廉颇蔺相如列传

## 廉颇

### 早年与成名

[1.1] @廉颇@者，&赵&之良将也。

[1.2] %赵惠文王十六年%，@廉颇@为&赵&将伐&齐&，大破之，取=阳晋=，拜为$上卿$，以勇气闻於诸侯。

## 蔺相如

### 出身

[2.1] @蔺相如@者，&赵&人也，为&赵&$宦者令$@缪贤@舍人。

### 完璧归赵

[3.1] %赵惠文王时%，得&楚&*和氏璧*。

[3.2] &秦&$昭王$闻之，使人遗&赵王&书，原以十五城请易*璧*。

[3.3] &赵王&与$大将军$@廉颇@诸大臣谋：欲予&秦&，&秦&城恐不可得，徒见欺；欲勿予，即患&秦&兵之来。
```

请按照以上格式要求处理给定的列传文本。
"""


def process_chapter(client, chapter_num, chapter_name, input_text):
    """处理单个章节"""

    user_prompt = f"""请处理以下《史记》列传章节：{chapter_name}

原文如下：

{input_text}

请按照系统提示中的格式要求，输出结构化的Markdown文本。
"""

    print(f"\n{'='*80}")
    print(f"正在处理: {chapter_num}_{chapter_name}")
    print(f"{'='*80}\n")

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=16000,
            temperature=0,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )

        output_text = response.content[0].text

        # 统计信息
        lines = output_text.count('\n')
        entities_count = output_text.count('@') // 2  # 人名
        places_count = output_text.count('=') // 2   # 地名

        print(f"✅ 处理完成")
        print(f"   - 行数: {lines}")
        print(f"   - 人名标注: {entities_count}")
        print(f"   - 地名标注: {places_count}")
        print(f"   - Token使用: {response.usage.input_tokens} in / {response.usage.output_tokens} out")

        return output_text, True

    except Exception as e:
        print(f"❌ 处理失败: {str(e)}")
        return None, False


def main():
    # 检查API密钥
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ 错误: 未设置 ANTHROPIC_API_KEY 环境变量")
        return 1

    client = anthropic.Anthropic(api_key=api_key)

    base_dir = Path("/home/baojie/work/shiji-kb")
    input_dir = base_dir / "docs" / "original_text"
    output_dir = base_dir / "chapter_md"

    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)

    print("="*80)
    print("《史记》批量处理工具 - 章节 081-100（列传）")
    print("="*80)
    print(f"输入目录: {input_dir}")
    print(f"输出目录: {output_dir}")
    print(f"章节数量: {len(CHAPTERS)}")
    print("="*80)

    success_count = 0
    failed_chapters = []

    for chapter in CHAPTERS:
        chapter_num = chapter.split('_')[0]
        chapter_name = chapter.split('_')[1]

        input_file = input_dir / f"{chapter}.txt"
        output_file = output_dir / f"{chapter}.tagged.md"

        # 检查输入文件是否存在
        if not input_file.exists():
            print(f"⚠️  跳过: {chapter} (文件不存在)")
            failed_chapters.append((chapter, "文件不存在"))
            continue

        # 检查输出文件是否已存在
        if output_file.exists():
            response = input(f"⚠️  文件已存在: {output_file.name}\n   是否覆盖? (y/n): ")
            if response.lower() != 'y':
                print(f"⏭️  跳过: {chapter}")
                continue

        # 读取原文
        with open(input_file, 'r', encoding='utf-8') as f:
            input_text = f.read()

        # 处理章节
        output_text, success = process_chapter(client, chapter_num, chapter_name, input_text)

        if success and output_text:
            # 保存结果
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output_text)
            print(f"💾 已保存: {output_file.name}\n")
            success_count += 1
        else:
            failed_chapters.append((chapter, "处理失败"))

    # 输出统计
    print("\n" + "="*80)
    print("处理完成统计")
    print("="*80)
    print(f"✅ 成功: {success_count}/{len(CHAPTERS)}")

    if failed_chapters:
        print(f"❌ 失败: {len(failed_chapters)}")
        for chapter, reason in failed_chapters:
            print(f"   - {chapter}: {reason}")

    return 0 if len(failed_chapters) == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
