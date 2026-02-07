#!/usr/bin/env python3
"""
批量处理《史记》101-130章节（最后30个列传）- 增强版
- 支持断点续传
- 更好的错误处理
- 进度保存
"""

import anthropic
import os
import sys
import json
from pathlib import Path
from datetime import datetime


# 章节列表
CHAPTERS = [
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
    "111_卫将军骠骑列传",
    "112_平津侯主父列传",
    "113_南越列传",
    "114_东越列传",
    "115_朝鲜列传",
    "116_西南夷列传",
    "117_司马相如列传",
    "118_淮南衡山列传",
    "119_循吏列传",
    "120_汲郑列传",
    "121_儒林列传",
    "122_酷吏列传",
    "123_大宛列传",
    "124_游侠列传",
    "125_佞幸列传",
    "126_滑稽列传",
    "127_日者列传",
    "128_龟策列传",
    "129_货殖列传",
    "130_太史公自序",  # ⭐⭐⭐ 最重要！
]


SYSTEM_PROMPT = """你是《史记》专家，擅长对古文进行结构化标注和实体识别。

你的任务是将《史记》列传原文处理成结构化的Markdown格式，并进行实体标注。

## 输出格式要求

### 1. 文档结构
- **一级标题**：# [0] [列传名]
- **二级标题**：按人物和事件划分
  - 对于合传（如"袁盎晁错列传"），为每个主要人物设立二级标题
  - 对于民族列传（如"匈奴列传"、"南越列传"），按历史沿革和重大事件划分
  - 对于类传（如"循吏列传"、"酷吏列传"），按人物分类
  - 对于"太史公自序"，按司马氏家世、司马迁生平、著述说明划分
  - 包括：家世、早年、主要事迹、太史公曰等
- **三级标题**：细分重要事件
- **段落编号**：使用圣经式编号 [章.节]（如 [1.1]、[1.2]等）

### 2. 实体标注规则
- 人名: @人名@（如：@袁盎@、@晁错@、@李广@、@卫青@、@霍去病@、@司马迁@）
- 地名: =地名=
- 官职: $官职$
- 时间/纪年: %时间%
- 朝代/氏族/国号: &朝代&
- 制度/典章: ^制度^
- 族群/部落: ~族群~（如：~匈奴~、~南越~、~东越~、~乌孙~、~月氏~等）
- 器物/礼器: *器物*
- 天文/历法: !天文!
- 传说/神话: ?神话?
- 动植物: 🌿动植物🌿

### 3. 特殊注意事项

#### 对于人物列传：
1. **合传处理**：一个列传包含多人时，需要清晰划分每个人物的部分
2. **对话处理**：对话使用引用块（> 符号），保持对话的独立性
3. **长对话标注**：长对话前可添加 NOTE 说明（如：> NOTE: 袁盎说辞）

#### 对于民族列传（匈奴、南越、东越、朝鲜、西南夷、大宛）：
1. **族群标注**：大量使用~族群~标注（如：~匈奴~、~乌孙~、~月氏~、~大宛~）
2. **历史沿革**：按时间顺序组织内容
3. **风俗记载**：单独设立小节
4. **重大战役**：清晰标注战争名称和时间

#### 对于类传（循吏、酷吏、游侠、佞幸、滑稽、日者、货殖）：
1. **人物归类**：每个人物设立独立的二级或三级标题
2. **总论在前**：如有总论部分，置于最前
3. **太史公曰**：置于最后

#### 对于太史公自序（130）⭐⭐⭐：
1. **司马氏家世**：详细标注历代祖先（@司马错@、@司马昌@、@司马靳@、@司马谈@等）
2. **司马迁生平**：
   - 早年游历
   - 继承父职
   - 李陵之祸（非常重要！）
   - 发愤著书
3. **著述说明**：
   - 《史记》体例（本纪、表、书、世家、列传）
   - 130篇目录总序
   - 著述宗旨
4. **特别细致**：这是司马迁的自述，需要非常细致地处理

#### 对于司马相如列传（117）：
1. **文学作品**：《子虚赋》、《上林赋》等文学作品需要保持完整性
2. **赋体标注**：长赋可适当分段，但保持文学性

### 4. 段落分段
- 合理分段，保持可读性
- 长对话、长赋可适当分段
- 每段有独立的段落编号

### 5. 输出要求
- 直接输出处理好的Markdown文本
- 不要添加任何解释性文字
- 不要使用代码块包裹输出
- 确保所有实体都被正确标注
- 保持原文的完整性

请按照以上格式要求处理给定的列传文本。
"""


def load_progress(progress_file):
    """加载处理进度"""
    if progress_file.exists():
        with open(progress_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"completed": [], "failed": {}}


def save_progress(progress_file, progress):
    """保存处理进度"""
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
        tribes_count = output_text.count('~') // 2   # 族群

        print(f"✅ 处理完成")
        print(f"   - 行数: {lines}")
        print(f"   - 人名标注: {entities_count}")
        print(f"   - 地名标注: {places_count}")
        print(f"   - 族群标注: {tribes_count}")
        print(f"   - Token使用: {response.usage.input_tokens} in / {response.usage.output_tokens} out")

        return output_text, True, None

    except Exception as e:
        error_msg = str(e)
        print(f"❌ 处理失败: {error_msg}")
        return None, False, error_msg


def main():
    # 检查API密钥
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ 错误: 未设置 ANTHROPIC_API_KEY 环境变量")
        print("\n请运行:")
        print('export ANTHROPIC_API_KEY="your_api_key_here"')
        return 1

    client = anthropic.Anthropic(api_key=api_key)

    base_dir = Path("/home/baojie/work/shiji-kb")
    input_dir = base_dir / "docs" / "original_text"
    output_dir = base_dir / "chapter_md"
    progress_file = base_dir / "progress_101_130.json"

    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)

    # 加载进度
    progress = load_progress(progress_file)

    print("="*80)
    print("《史记》批量处理工具 - 章节 101-130（最后30个列传）- 增强版")
    print("="*80)
    print(f"输入目录: {input_dir}")
    print(f"输出目录: {output_dir}")
    print(f"章节数量: {len(CHAPTERS)}")
    print(f"已完成: {len(progress['completed'])}")
    print(f"已失败: {len(progress['failed'])}")
    print("="*80)

    # 询问是否跳过已完成的章节
    if progress['completed']:
        print(f"\n已完成的章节: {', '.join(progress['completed'])}")
        skip_completed = input("是否跳过已完成的章节? (y/n, 默认y): ").strip().lower()
        if skip_completed == '' or skip_completed == 'y':
            skip_completed = True
        else:
            skip_completed = False
    else:
        skip_completed = False

    success_count = len(progress['completed']) if skip_completed else 0
    failed_chapters = progress['failed'] if skip_completed else {}

    for chapter in CHAPTERS:
        chapter_num = chapter.split('_')[0]
        chapter_name = chapter.split('_')[1]

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
        if output_file.exists() and not skip_completed:
            response = input(f"⚠️  文件已存在: {output_file.name}\n   是否覆盖? (y/n, 默认n): ").strip().lower()
            if response != 'y':
                print(f"⏭️  跳过: {chapter}")
                continue

        # 读取原文
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                input_text = f.read()
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

    print(f"\n进度文件: {progress_file}")
    print(f"可以随时重新运行脚本继续处理")

    return 0 if len(failed_chapters) == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
