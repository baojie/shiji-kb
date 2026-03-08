#!/usr/bin/env python3
"""
批量处理《史记》084-095章节（列传）
使用Claude API进行实体标注和结构化处理
"""

import anthropic
import os
import sys
from pathlib import Path


# 章节列表 084-095
CHAPTERS = [
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
]


SYSTEM_PROMPT = """你是《史记》专家，擅长对古文进行结构化标注和实体识别。

你的任务是将《史记》列传原文处理成结构化的Markdown格式，并进行实体标注。

## 输出格式要求

### 1. 文档结构
- **一级标题**：# [0] [列传名]
- **二级标题**：按人物和事件划分
  - 对于合传（如"韩信卢绾列传"），为每个主要人物设立二级标题
  - 包括：家世、早年、主要事迹、太史公曰等
- **三级标题**：细分重要事件
- **段落编号**：使用圣经式编号 [章.节]（如 [1.1]、[1.2]等）

### 2. 实体标注规则（11类实体）
- **人名**: @人名@（如：@屈原@、@贾谊@、@李斯@、@韩信@）
- **地名**: =地名=（如：=楚国=、=咸阳=、=关中=）
- **官职**: $官职$（如：$丞相$、$太尉$、$大将军$）
- **时间/纪年**: %时间%（如：%秦始皇二十六年%、%汉高祖五年%）
- **朝代/氏族/国号**: &朝代&（如：&秦&、&楚&、&汉&）
- **制度/典章**: ^制度^（如：^郡县制^、^三公九卿^）
- **族群/部落**: ~族群~（如：~匈奴~、~楚人~）
- **器物/礼器**: *器物*（如：*剑*、*玉玺*）
- **天文/历法**: !天文!（如：!彗星!、!日食!）
- **传说/神话**: ?神话?（如：?凤凰?、?龙?）
- **动植物**: 🌿动植物🌿（如：🌿马🌿、🌿兰草🌿）

### 3. 列传特殊注意事项
1. **人物关系**：注意标注师徒、朋友、政治关系（如：@张耳@与@陈馀@）
2. **对话处理**：对话使用引用块（> 符号），保持对话的独立性
3. **长对话标注**：长对话前可添加 NOTE 说明（如：> NOTE: 李斯谏逐客书）
4. **历史事件**：重要事件设三级标题（如：### 荆轲刺秦王）
5. **合传处理**：一个列传包含多人时，需要清晰划分每个人物的部分
6. **段落分段**：合理分段，保持可读性
7. **保持原文**：不改变原文内容，只添加结构和标注

### 4. 输出要求
- 直接输出处理好的Markdown文本
- 不要添加任何解释性文字
- 不要使用代码块包裹输出
- 确保所有实体都被正确标注
- 保持原文的完整性

## 示例格式

```markdown
# [0] 屈原贾生列传

## 屈原

### 早年与得志

[1.1] @屈原@名@平@，&楚&之$同姓$也。为&楚怀王$左徒$。

[1.2] 博闻强志，明於治乱，娴於辞令。入则与$王$图议$国事$，以出$号令$；出则接遇$宾客$，应对诸侯。$王$甚任之。

### 被谗去职

[2.1] %上官大夫%与之同列，争宠而心害其能。

[2.2] @怀王@使@屈原@造为$宪令$，@屈原@属草稿未定。

> NOTE: 上官大夫的谗言

[2.3] @上官大夫@见而欲夺之，@屈原@不与。因谗之曰："$王$使@屈原@为$令$，众莫不知。每一令出，@平@伐其功，以为'非我莫能为'也。"

[2.4] $王$怒而疏@屈原@。
```

请按照以上格式要求处理给定的列传文本。
"""


def process_chapter(client, chapter_num, chapter_name, input_text):
    """处理单个章节"""

    user_prompt = f"""请处理以下《史记》列传章节：{chapter_name}

原文如下：

{input_text}

请按照系统提示中的格式要求，输出结构化的Markdown文本。注意：
1. 这是列传，记录历史人物传记
2. 注意标注人物间的关系（师徒、朋友、政治关系等）
3. 注意标注对话内容中的人名、地名、官职等实体
4. 合理划分段落和章节
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
        officials_count = output_text.count('$') // 2  # 官职
        dynasties_count = output_text.count('&') // 2  # 朝代

        print(f"✅ 处理完成")
        print(f"   - 行数: {lines}")
        print(f"   - 人名标注: {entities_count}")
        print(f"   - 地名标注: {places_count}")
        print(f"   - 官职标注: {officials_count}")
        print(f"   - 朝代标注: {dynasties_count}")
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

    base_dir = Path(".")
    input_dir = base_dir / "docs" / "original_text"
    output_dir = base_dir / "chapter_md"

    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)

    print("="*80)
    print("《史记》批量处理工具 - 章节 084-095（列传）")
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

        # 检查输出文件是否已存在（不询问，直接处理）
        if output_file.exists():
            print(f"⚠️  文件已存在，将覆盖: {output_file.name}")

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
