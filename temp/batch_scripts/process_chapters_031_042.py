#!/usr/bin/env python3
"""
批量处理《史记》031-042章节（世家部分）
"""

import anthropic
import os
import sys
import json
from pathlib import Path
from datetime import datetime


# 章节列表
CHAPTERS = [
    "031_吴太伯世家",
    "032_齐太公世家",
    "033_鲁周公世家",
    "034_燕召公世家",
    "035_管蔡世家",
    "036_陈杞世家",
    "037_卫康叔世家",
    "038_宋微子世家",
    "039_晋世家",
    "040_楚世家",
    "041_越王句践世家",
    "042_郑世家",
]


SYSTEM_PROMPT = """你是《史记》专家，擅长对古文进行结构化标注和实体识别。

你的任务是将《史记》世家原文处理成结构化的Markdown格式，并进行实体标注。

## 输出格式要求

### 1. 文档结构
- **一级标题**：# [0] [世家名]
- **二级标题**：按历史时期、重要人物和重大事件划分
  - 对于吴太伯世家：太伯世系、季札德行、阖闾时期、夫差灭国等
  - 对于齐太公世家：太公封齐、桓公霸业、田氏代齐等
  - 对于鲁周公世家：周公辅政、鲁国历史等
  - 对于晋世家：晋献公、文公霸业、三家分晋等
  - 对于楚世家：楚国崛起、问鼎中原、吴楚争霸等
- **三级标题**：细分重要事件
- **段落编号**：使用圣经式编号 [章.节]（如 [1.1]、[1.2]等）

### 2. 实体标注规则
- 人名: @人名@（如：@太伯@、@季札@、@齐桓公@、@管仲@、@晋文公@、@重耳@）
- 地名: =地名=（如：=吴=、=齐=、=鲁=、=晋=、=楚=、=郑=）
- 官职: $官职$（如：$太宰$、$相国$、$将军$、$大夫$）
- 时间/纪年: %时间%（如：%元年%、%二年%、%春秋%）
- 朝代/氏族/国号: &朝代&（如：&周&、&春秋&、&战国&）
- 制度/典章: ^制度^（如：^分封^、^礼制^、^会盟^）
- 族群/部落: ~族群~（如：~荆蛮~、~戎狄~、~蛮夷~）
- 器物/礼器: *器物*（如：*鼎*、*剑*、*印绶*、*兵车*）
- 天文/历法: !天文!
- 传说/神话: ?神话?
- 动植物: 🌿动植物🌿

### 3. 特殊注意事项

#### 对于世家：
1. **历史脉络**：按时间顺序梳理国家或家族的历史发展
2. **重要人物**：突出每个时期的关键人物及其事迹
3. **对话处理**：对话使用引用块（> 符号），保持对话的独立性
4. **长对话标注**：长对话前可添加 NOTE 说明
5. **太史公曰**：置于最后，独立成节

#### 重点关注：
1. **季札聘鲁**（吴太伯世家）：季札观周乐的长段评论需要完整保留
2. **管仲相齐**（齐太公世家）：齐桓公霸业和管仲的治国理念
3. **周公辅政**（鲁周公世家）：周公摄政和制礼作乐
4. **重耳流亡**（晋世家）：晋文公流亡和称霸的过程
5. **楚庄问鼎**（楚世家）：楚庄王问鼎中原的历史
6. **卧薪尝胆**（越王句践世家）：句践复国的故事

### 4. 段落分段
- 合理分段，保持可读性
- 长对话、长篇评论可适当分段
- 每段有独立的段落编号
- 世系传承部分可以相对密集

### 5. 输出要求
- 直接输出处理好的Markdown文本
- 不要添加任何解释性文字
- 不要使用代码块包裹输出
- 确保所有实体都被正确标注
- 保持原文的完整性

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

    user_prompt = f"""请处理以下《史记》世家章节：{chapter_name}

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
        offices_count = output_text.count('$') // 2  # 官职

        print(f"✅ 处理完成")
        print(f"   - 行数: {lines}")
        print(f"   - 人名标注: {entities_count}")
        print(f"   - 地名标注: {places_count}")
        print(f"   - 官职标注: {offices_count}")
        print(f"   - Token使用: {response.usage.input_tokens} in / {response.usage.output_tokens} out")

        return output_text, True, None

    except Exception as e:
        error_msg = str(e)
        print(f"❌ 处理失败: {error_msg}")
        return None, False, error_msg


def main():
    """主函数"""

    # 设置路径
    BASE_DIR = Path("/home/baojie/work/shiji-kb")
    INPUT_DIR = BASE_DIR / "docs" / "original_text"
    OUTPUT_DIR = BASE_DIR / "chapter_md"
    PROGRESS_FILE = BASE_DIR / "progress_031_042.json"

    # 确保输出目录存在
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 初始化 API 客户端
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ 错误: 未设置 ANTHROPIC_API_KEY 环境变量")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    # 加载进度
    progress = load_progress(PROGRESS_FILE)

    print(f"\n{'='*80}")
    print(f"《史记》031-042 章节批量处理")
    print(f"{'='*80}")
    print(f"输入目录: {INPUT_DIR}")
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"已完成: {len(progress['completed'])} 章节")
    print(f"失败: {len(progress['failed'])} 章节")
    print(f"{'='*80}\n")

    # 处理每个章节
    for chapter_full_name in CHAPTERS:
        chapter_num = chapter_full_name[:3]
        chapter_name = chapter_full_name[4:]

        # 检查是否已完成
        if chapter_full_name in progress['completed']:
            print(f"✓ 跳过已完成: {chapter_full_name}")
            continue

        # 检查输入文件
        input_file = INPUT_DIR / f"{chapter_full_name}.txt"
        if not input_file.exists():
            print(f"❌ 输入文件不存在: {input_file}")
            progress['failed'][chapter_full_name] = "输入文件不存在"
            save_progress(PROGRESS_FILE, progress)
            continue

        # 检查输出文件是否已存在
        output_file = OUTPUT_DIR / f"{chapter_full_name}.tagged.md"
        if output_file.exists():
            print(f"✓ 输出文件已存在，跳过: {chapter_full_name}")
            progress['completed'].append(chapter_full_name)
            save_progress(PROGRESS_FILE, progress)
            continue

        # 读取输入文件
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                input_text = f.read()
        except Exception as e:
            print(f"❌ 读取文件失败: {e}")
            progress['failed'][chapter_full_name] = f"读取失败: {str(e)}"
            save_progress(PROGRESS_FILE, progress)
            continue

        # 处理章节
        output_text, success, error_msg = process_chapter(
            client, chapter_num, chapter_name, input_text
        )

        if success:
            # 保存输出
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(output_text)
                print(f"✅ 已保存: {output_file}")
                progress['completed'].append(chapter_full_name)
            except Exception as e:
                print(f"❌ 保存文件失败: {e}")
                progress['failed'][chapter_full_name] = f"保存失败: {str(e)}"
        else:
            progress['failed'][chapter_full_name] = error_msg

        # 保存进度
        save_progress(PROGRESS_FILE, progress)

        # 添加延迟避免API限流
        import time
        time.sleep(2)

    # 最终报告
    print(f"\n{'='*80}")
    print("处理完成!")
    print(f"{'='*80}")
    print(f"✅ 成功: {len(progress['completed'])} 章节")
    print(f"❌ 失败: {len(progress['failed'])} 章节")

    if progress['failed']:
        print("\n失败章节:")
        for chapter, error in progress['failed'].items():
            print(f"  - {chapter}: {error}")

    print(f"\n进度文件: {PROGRESS_FILE}")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()
