#!/usr/bin/env python3
"""
批量处理《史记》043-050世家章节
- 043_赵世家 ⭐⭐ 重点章节
- 044_魏世家
- 045_韩世家
- 046_田敬仲完世家
- 047_孔子世家 ⭐⭐⭐ 重点章节
- 048_陈涉世家
- 049_外戚世家
- 050_楚元王世家
"""

import anthropic
import os
import sys
import json
from pathlib import Path
from datetime import datetime


# 章节列表
CHAPTERS = [
    "043_赵世家",        # ⭐⭐ 战国七雄之一，内容丰富
    "044_魏世家",        # 战国七雄之一
    "045_韩世家",        # 战国七雄之一
    "046_田敬仲完世家",  # 田氏代齐
    "047_孔子世家",      # ⭐⭐⭐ 最重要！孔子及其弟子
    "048_陈涉世家",      # 秦末农民起义
    "049_外戚世家",      # 汉代外戚
    "050_楚元王世家",    # 刘邦兄长之后
]


SYSTEM_PROMPT = """你是《史记》专家，擅长对古文进行结构化标注和实体识别。

你的任务是将《史记》世家原文处理成结构化的Markdown格式，并进行实体标注。

## 输出格式要求

### 1. 文档结构
- **一级标题**：# [0] [世家名]
- **二级标题**：按历史时期和重大事件划分
  - 对于诸侯世家（赵、魏、韩、田敬仲完）：按世系和重大事件划分
    - 世系源流（早期历史）
    - 建国立业
    - 历代君主（每位君主可设立二级或三级标题）
    - 重大战役和政治事件
    - 灭亡与结局
  - 对于孔子世家（047）⭐⭐⭐：
    - 孔子世系
    - 孔子生平（详细分期）
    - 周游列国（按国家和事件）
    - 著述立说
    - 弟子列传（重要弟子需标注）
    - 后世影响
  - 对于陈涉世家（048）：
    - 起义背景
    - 大泽乡起义
    - 建立张楚政权
    - 败亡
  - 对于外戚世家、楚元王世家：按人物和世系划分
- **三级标题**：细分具体事件
- **段落编号**：使用圣经式编号 [章.节]（如 [1.1]、[1.2]等）

### 2. 实体标注规则（11类）
- 人名: @人名@（如：@赵襄子@、@魏文侯@、@韩非@、@孔子@、@子路@、@颜回@、@陈胜@、@吴广@）
- 地名: =地名=（如：=邯郸=、=大梁=、=新郑=、=曲阜=、=陈=）
- 官职: $官职$（如：$相国$、$将军$、$大夫$、$宰相$）
- 时间/纪年: %时间%（如：%公元前403年%、%周安王二十六年%）
- 朝代/氏族/国号: &朝代&（如：&赵国&、&魏国&、&韩国&、&齐国&、&晋国&、&春秋&、&战国&）
- 制度/典章: ^制度^（如：^分封制^、^变法^、^礼制^、^井田制^）
- 族群/部落: ~族群~（主要用于少数民族，世家章节较少使用）
- 器物/礼器: *器物*（如：*钟*、*鼎*、*剑*、*车*）
- 天文/历法: !天文!
- 传说/神话: ?神话?
- 动植物: 🌿动植物🌿

### 3. 世家特殊注意事项

#### 诸侯世家（043-046 赵魏韩田）：
1. **世系清晰**：各代君主要标注清楚，使用@君主名@
2. **家族关系**：父子、兄弟关系要清晰
3. **战国七雄互动**：
   - 大量的战争：标注清楚交战双方、时间、地点
   - 联盟与背叛：合纵连横
   - 人才流动：各国间的游说、任用
4. **地名密集**：战国时期地名众多，需要细致标注
5. **官职变化**：战国官制复杂，如$上卿$、$相国$、$将军$等

#### 孔子世家（047）⭐⭐⭐ 最重要：
1. **孔子言行**：
   - 对话：使用引用块（> 符号）
   - 评论：《论语》式的简短对话
   - 长篇言论：保持完整性
2. **弟子标注**：
   - 重要弟子：@颜回@、@子路@、@子贡@、@冉求@、@宰我@等
   - 七十二贤人：尽可能标注
3. **周游列国**：
   - 按国家组织：&鲁国&、&卫国&、&陈国&、&楚国&等
   - 在各国的遭遇和言行
4. **儒家经典**：
   - 《诗》、《书》、《礼》、《乐》、《易》、《春秋》
   - 标注为典籍或制度
5. **历史评价**：太史公曰部分

#### 陈涉世家（048）：
1. **起义过程**：
   - 大泽乡起义：时间、地点、原因
   - 号召口号："王侯将相宁有种乎"
   - 建立张楚政权
2. **人物关系**：@陈胜@与@吴广@的关系
3. **历史意义**：第一次农民起义

#### 外戚世家（049）、楚元王世家（050）：
1. **汉初政治**：刘邦建国后的政治格局
2. **外戚关系**：皇室姻亲关系复杂，需细致标注
3. **世系传承**：各代传承关系

### 4. 对话和引文处理
- 短对话：直接标注实体
- 长对话：使用引用块（> 符号）
- 对话前可添加 NOTE 说明
  ```
  > NOTE: 孔子答子路问
  >
  > 子路问："听到就去做吗？"孔子说："有父兄在，怎能听到就去做？"
  ```

### 5. 段落分段
- 合理分段，保持可读性
- 长篇叙述适当分段
- 每段有独立的段落编号

### 6. 输出要求
- 直接输出处理好的Markdown文本
- 不要添加任何解释性文字
- 不要使用代码块包裹输出
- 确保所有实体都被正确标注
- 保持原文的完整性
- 特别注意043赵世家和047孔子世家的细致程度

请按照以上格式要求处理给定的世家文本。
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

    # 针对不同章节的特殊提示
    special_notes = {
        "043": "⭐⭐ 赵世家是战国七雄之一，内容丰富，注意标注赵氏家族的世系和重大战役（如长平之战）。",
        "047": "⭐⭐⭐ 孔子世家是最重要的章节！需要非常细致地标注孔子的言行、弟子、周游列国的经历。",
    }

    special_note = special_notes.get(chapter_num, "")

    user_prompt = f"""请处理以下《史记》世家章节：{chapter_name}

{special_note}

原文如下：

{input_text}

请按照系统提示中的格式要求，输出结构化的Markdown文本。
"""

    print(f"\n{'='*80}")
    print(f"正在处理: {chapter_num}_{chapter_name}")
    if special_note:
        print(f"{special_note}")
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
        persons_count = output_text.count('@') // 2  # 人名
        places_count = output_text.count('=') // 2   # 地名
        offices_count = output_text.count('$') // 2   # 官职
        states_count = output_text.count('&') // 2   # 朝代/国号

        print(f"✅ 处理完成")
        print(f"   - 行数: {lines}")
        print(f"   - 人名标注: {persons_count}")
        print(f"   - 地名标注: {places_count}")
        print(f"   - 官职标注: {offices_count}")
        print(f"   - 朝代/国号标注: {states_count}")
        print(f"   - Token使用: {response.usage.input_tokens} in / {response.usage.output_tokens} out")

        return output_text, True, None

    except Exception as e:
        error_msg = str(e)
        print(f"❌ 处理失败: {error_msg}")
        return None, False, error_msg


def main():
    # 检查API密钥 - 尝试从环境变量或使用默认配置
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        # 尝试使用 anthropic 库的默认配置
        try:
            client = anthropic.Anthropic()  # 会自动查找 ~/.anthropic/api_key 等
            print("✅ 使用默认 Anthropic 配置")
        except Exception as e:
            print("❌ 错误: 未找到 ANTHROPIC_API_KEY")
            print(f"   {str(e)}")
            print("\n请运行:")
            print('export ANTHROPIC_API_KEY="your_api_key_here"')
            return 1
    else:
        client = anthropic.Anthropic(api_key=api_key)
        print("✅ 使用环境变量 ANTHROPIC_API_KEY")

    base_dir = Path(".")
    input_dir = base_dir / "docs" / "original_text"
    output_dir = base_dir / "chapter_md"
    progress_file = base_dir / "progress_043_050.json"

    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)

    # 加载进度
    progress = load_progress(progress_file)

    print("="*80)
    print("《史记》批量处理工具 - 世家 043-050")
    print("="*80)
    print(f"输入目录: {input_dir}")
    print(f"输出目录: {output_dir}")
    print(f"章节数量: {len(CHAPTERS)}")
    print(f"已完成: {len(progress['completed'])}")
    print(f"已失败: {len(progress['failed'])}")
    print("\n重点章节:")
    print("  ⭐⭐ 043_赵世家 - 战国七雄，内容丰富")
    print("  ⭐⭐⭐ 047_孔子世家 - 最重要章节")
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
    failed_chapters = progress['failed'].copy() if skip_completed else {}

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
