#!/usr/bin/env python3
"""
《史记》096-110列传批量标注工具

使用说明:
1. 确保已安装 anthropic 库: pip install anthropic
2. 设置环境变量: export ANTHROPIC_API_KEY="your_api_key_here"
3. 运行脚本: python3 process_096_110_manual.py

本脚本将处理以下15个列传章节:
- 096_张丞相列传
- 097_郦生陆贾列传
- 098_傅靳蒯成列传
- 099_刘敬叔孙通列传
- 100_季布栾布列传
- 101_袁盎晁错列传
- 102_张释之冯唐列传
- 103_万石张叔列传
- 104_田叔列传
- 105_扁鹊仓公列传
- 106_吴王濞列传
- 107_魏其武安侯列传
- 108_韩长孺列传
- 109_李将军列传
- 110_匈奴列传
"""

import anthropic
import os
import sys
import json
from pathlib import Path
from datetime import datetime


# 章节列表
CHAPTERS = [
    "096_张丞相列传",
    "097_郦生陆贾列传",
    "098_傅靳蒯成列传",
    "099_刘敬叔孙通列传",
    "100_季布栾布列传",
    "101_袁盎晁错列传",
    "102_张释之冯唐列传",
    "103_万石张叔列传",
    "104_田叔列传",
    "105_扁鹊仓公列传",
    "106_吴王濞列传",
    "107_魏其武安侯列传",
    "108_韩长孺列传",
    "109_李将军列传",
    "110_匈奴列传",
]


SYSTEM_PROMPT = """你是《史记》专家，擅长对古文进行结构化标注和实体识别。

你的任务是将《史记》列传原文处理成结构化的Markdown格式，并进行实体标注。

## 输出格式要求

### 1. 文档结构
- **一级标题**：# [0] [列传名]
- **二级标题**：按人物和事件划分
  - 对于合传（如"张丞相列传"包含多位丞相），为每个主要人物设立二级标题
  - 对于民族列传（如"匈奴列传"），按历史沿革和重大事件划分
  - 包括：家世、早年、主要事迹、太史公曰等
- **三级标题**：细分重要事件
- **段落编号**：使用圣经式编号 [章.节]（如 [1.1]、[1.2]等）

### 2. 实体标注规则（11类实体）
- 人名: @人名@（如：@张苍@、@周昌@、@郦食其@、@陆贾@、@李广@）
- 地名: =地名=（如：=阳武=、=咸阳=、=长安=）
- 官职: $官职$（如：$丞相$、$御史大夫$、$太守$）
- 时间/纪年: %时间%（如：%秦时%、%汉王四年%、%孝文帝元年%）
- 朝代/氏族/国号: &朝代&（如：&秦&、&汉&、&楚&）
- 制度/典章: ^制度^（如：^律历^、^五德^、^封建制^）
- 族群/部落: ~族群~（如：~匈奴~、~乌孙~、~月氏~、~东胡~）
- 器物/礼器: *器物*（如：*印绶*、*剑*、*鼎*）
- 天文/历法: !天文!（如：!黄龙!、!五星聚!）
- 传说/神话: ?神话?
- 动植物: 🌿动植物🌿

### 3. 特殊注意事项

#### 对于人物列传：
1. **合传处理**：一个列传包含多人时（如096张丞相列传包含张苍、周昌、任敖、申屠嘉等多位丞相），需要清晰划分每个人物的部分
2. **对话处理**：对话使用引用块（> 符号），保持对话的独立性
3. **长对话标注**：长对话前可添加 NOTE 说明（如：> NOTE: @郦食其@说辞）
4. **官职标注**：丞相、御史大夫等官职必须标注为 $官职$

#### 对于匈奴列传（110）- 重要！
1. **族群标注**：大量使用~族群~标注（如：~匈奴~、~乌孙~、~月氏~、~东胡~、~楼烦~）
2. **历史沿革**：按时间顺序组织内容（从夏商周到汉武帝时期）
3. **风俗记载**：单独设立小节描述匈奴风俗习惯
4. **重大战役**：清晰标注战争名称、时间和参战将领
5. **单于世系**：清晰标注历代单于（如：@冒顿单于@、@老上单于@、@军臣单于@等）

#### 对于医学列传（105_扁鹊仓公列传）：
1. **医案记载**：每个医案独立标注
2. **病名标注**：疾病名称需要准确标注
3. **医理论述**：保持完整性
4. **诊断过程**：完整保留脉诊、望诊等内容

### 4. 段落分段
- 合理分段，保持可读性
- 长对话可适当分段
- 每段有独立的段落编号
- 段落编号按二级标题重新计数

### 5. 输出要求
- 直接输出处理好的Markdown文本
- 不要添加任何解释性文字
- 不要使用代码块包裹输出
- 确保所有实体都被正确标注
- 保持原文的完整性，不要删改原文

### 6. 示例格式

# [0] 张丞相列传

## 张丞相苍

### 家世与早年

[1.1] $丞相$@张苍@者，=阳武=人也。好书^律历^。

[1.2] &秦&时为$御史$，主柱下方书。有罪，亡归。

### 从汉立功

[2.1] 及@沛公@略地过=阳武=，@苍@以客从攻=南阳=。

请按照以上格式要求处理给定的列传文本。
"""


def load_progress(progress_file):
    """加载处理进度"""
    if progress_file.exists():
        with open(progress_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"completed": [], "failed": {}, "timestamp": ""}


def save_progress(progress_file, progress):
    """保存处理进度"""
    progress["timestamp"] = datetime.now().isoformat()
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


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
        positions_count = output_text.count('$') // 2  # 官职
        tribes_count = output_text.count('~') // 2   # 族群

        print(f"✅ 处理完成")
        print(f"   - 行数: {lines}")
        print(f"   - 人名标注: {entities_count}")
        print(f"   - 地名标注: {places_count}")
        print(f"   - 官职标注: {positions_count}")
        print(f"   - 族群标注: {tribes_count}")
        print(f"   - Token使用: {response.usage.input_tokens} in / {response.usage.output_tokens} out")

        return output_text, True, None

    except Exception as e:
        error_msg = str(e)
        print(f"❌ 处理失败: {error_msg}")
        return None, False, error_msg


def main():
    print("\n" + "="*80)
    print("《史记》批量处理工具 - 章节 096-110 列传")
    print("="*80 + "\n")

    # 检查API密钥
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ 错误: 未设置 ANTHROPIC_API_KEY 环境变量\n")
        print("请运行:")
        print('  export ANTHROPIC_API_KEY="your_api_key_here"')
        print("\n或者在代码中直接设置:")
        print('  client = anthropic.Anthropic(api_key="your_api_key_here")\n')
        return 1

    # 初始化客户端
    try:
        client = anthropic.Anthropic(api_key=api_key)
        print("✅ API客户端初始化成功\n")
    except Exception as e:
        print(f"❌ 无法初始化Anthropic客户端: {e}\n")
        return 1

    base_dir = Path("/home/baojie/work/shiji-kb")
    input_dir = base_dir / "docs" / "original_text"
    output_dir = base_dir / "chapter_md"
    progress_file = base_dir / "progress_096_110.json"

    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)

    # 加载进度
    progress = load_progress(progress_file)

    print("="*80)
    print(f"输入目录: {input_dir}")
    print(f"输出目录: {output_dir}")
    print(f"章节数量: {len(CHAPTERS)}")
    print(f"已完成: {len(progress['completed'])}")
    print(f"已失败: {len(progress['failed'])}")
    if progress.get('timestamp'):
        print(f"上次运行: {progress['timestamp']}")
    print("="*80 + "\n")

    # 自动跳过已完成的章节
    skip_completed = True
    if progress['completed']:
        print(f"已完成的章节: {', '.join(progress['completed'])}")
        print("将自动跳过已完成的章节\n")

    success_count = len(progress['completed']) if skip_completed else 0
    failed_chapters = dict(progress['failed']) if skip_completed else {}

    for i, chapter in enumerate(CHAPTERS, 1):
        chapter_num = chapter.split('_')[0]
        chapter_name = chapter.split('_')[1]

        print(f"\n[{i}/{len(CHAPTERS)}] 处理章节: {chapter}")

        # 跳过已完成的章节
        if skip_completed and chapter in progress['completed']:
            print(f"⏭️  跳过（已完成）: {chapter}")
            continue

        input_file = input_dir / f"{chapter}.txt"
        output_file = output_dir / f"{chapter}.tagged.md"

        # 检查输入文件是否存在
        if not input_file.exists():
            print(f"⚠️  跳过: {chapter} (文件不存在)")
            failed_chapters[chapter] = "文件不存在"
            continue

        # 检查输出文件是否已存在
        if output_file.exists():
            print(f"⚠️  文件已存在: {output_file.name}")
            print(f"   将自动覆盖已存在的文件")

        # 读取原文
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                input_text = f.read()
            print(f"📖 已读取原文，共 {len(input_text)} 字符")
        except Exception as e:
            print(f"❌ 读取文件失败: {chapter} - {str(e)}")
            failed_chapters[chapter] = f"读取失败: {str(e)}"
            continue

        # 处理章节
        output_text, success, error = process_chapter(client, chapter_num, chapter_name, input_text)

        if success and output_text:
            # 保存结果
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(output_text)
                print(f"💾 已保存: {output_file.name}\n")
                success_count += 1

                # 更新进度
                if chapter not in progress['completed']:
                    progress['completed'].append(chapter)
                if chapter in progress['failed']:
                    del progress['failed'][chapter]
                save_progress(progress_file, progress)

            except Exception as e:
                print(f"❌ 保存文件失败: {chapter} - {str(e)}")
                failed_chapters[chapter] = f"保存失败: {str(e)}"
        else:
            failed_chapters[chapter] = error or "处理失败"
            progress['failed'][chapter] = error or "处理失败"
            save_progress(progress_file, progress)

    # 输出统计
    print("\n" + "="*80)
    print("处理完成统计")
    print("="*80)
    print(f"✅ 成功: {success_count}/{len(CHAPTERS)}")

    if failed_chapters:
        print(f"❌ 失败: {len(failed_chapters)}")
        for chapter, reason in failed_chapters.items():
            print(f"   - {chapter}: {reason}")
    else:
        print("🎉 所有章节处理成功！")

    print(f"\n进度文件: {progress_file}")
    print(f"可以随时重新运行脚本继续处理")
    print("="*80 + "\n")

    return 0 if len(failed_chapters) == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
