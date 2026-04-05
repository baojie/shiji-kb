#!/usr/bin/env python3
"""
批量提取《史记》031-060章节的知识单元（使用a2o-lite方法）

使用方法:
    python scripts/extract_chapters_031_060.py

输出目录:
    kg/ontology/ontology-v2/chapters/chapter_NNN/
"""

import os
import sys
import json
import anthropic
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
CHAPTER_MD_DIR = PROJECT_ROOT / "chapter_md"
OUTPUT_DIR = PROJECT_ROOT / "kg" / "ontology" / "ontology-v2" / "chapters"
REFERENCE_CHAPTER = OUTPUT_DIR / "chapter_001"

# API配置
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    print("错误: 未设置ANTHROPIC_API_KEY环境变量")
    sys.exit(1)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def read_file(file_path):
    """读取文件内容"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def write_file(file_path, content):
    """写入文件"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def get_chapter_info(chapter_num):
    """获取章节信息"""
    chapter_files = list(CHAPTER_MD_DIR.glob(f"{chapter_num:03d}_*.tagged.md"))
    if not chapter_files:
        return None, None

    chapter_file = chapter_files[0]
    chapter_name = chapter_file.stem.replace(".tagged", "").split("_", 1)[1]
    return chapter_file, chapter_name


def read_reference_examples():
    """读取参考示例（chapter_001）"""
    examples = {
        "fact_json": read_file(REFERENCE_CHAPTER / "skus" / "facts" / "fact_001.json"),
        "fact_md": read_file(REFERENCE_CHAPTER / "skus" / "facts" / "fact_002.md"),
        "skill_md": read_file(REFERENCE_CHAPTER / "skus" / "skills" / "skill_001.md"),
        "mapping": read_file(REFERENCE_CHAPTER / "mapping.md"),
        "eureka": read_file(REFERENCE_CHAPTER / "eureka.md"),
        "readme": read_file(REFERENCE_CHAPTER / "README.md"),
    }
    return examples


def create_extraction_prompt(chapter_content, chapter_name, chapter_num, examples):
    """创建知识提取的prompt"""

    is_shijiaseries = chapter_num >= 31 and chapter_num <= 60

    focus_areas = ""
    if is_shijiaseries:
        focus_areas = """
**本章为世家类章节，重点提取**：
1. 世系传承：建国始祖、历代君主、世系关系
2. 重大事件：政治变革、战争征伐、外交活动
3. 治国策略：制度创新、人才任用、危机应对
4. 权力斗争：继承纷争、篡位叛乱、权臣专政
5. 文化成就：礼乐制度、学术贡献、道德典范
"""

    prompt = f"""# 任务：提取《史记·{chapter_name}》的知识单元（a2o-lite方法）

## 输入文本

```markdown
{chapter_content}
```

{focus_areas}

## 提取要求

### 1. MECE原则
- 事实单元之间相互独立、完全穷尽
- 程序单元之间相互独立、完全穷尽
- 避免重复、避免遗漏

### 2. 事实性知识（Facts）
- **结构化数据**（世系、官职、年表等）→ JSON格式
- **叙事性内容**（事件、功绩、策略等）→ Markdown格式
- 每个fact聚焦一个主题，完整保留原文信息
- 命名规范：`fact_001.json` 或 `fact_001.md`

### 3. 程序性知识（Skills）
- 提取**可复用的方法论**（如何选拔人才、如何应对危机等）
- 必须包含：概述、步骤、决策点、预期结果
- Markdown格式，命名规范：`skill_001.md`

### 4. 跨领域洞察（Eureka）
- **仅包含真正跨领域的洞察**（可应用于现代组织、管理、决策等场景）
- 每条洞察：核心观点 + 古代案例 + 现代启示
- 质量重于数量（5-15条即可）

## 参考示例（chapter_001）

### fact_001.json（结构化数据示例）
```json
{examples['fact_json']}
```

### fact_002.md（叙事性内容示例）
```markdown
{examples['fact_md']}
```

### skill_001.md（程序性知识示例）
```markdown
{examples['skill_md']}
```

### eureka.md（跨领域洞察示例）
```markdown
{examples['eureka'][:1500]}
...
```

## 输出格式

请按以下JSON格式输出所有知识单元：

```json
{{
  "chapter_num": "{chapter_num:03d}",
  "chapter_name": "{chapter_name}",
  "facts": [
    {{
      "filename": "fact_001.json",
      "content": "{{...JSON对象...}}"
    }},
    {{
      "filename": "fact_002.md",
      "content": "...Markdown文本..."
    }}
  ],
  "skills": [
    {{
      "filename": "skill_001.md",
      "content": "...Markdown文本..."
    }}
  ],
  "eureka_content": "# 灵感笔记 — {chapter_name}\\n\\n...",
  "mapping_content": "# SKU 映射 — {chapter_name}\\n\\n...",
  "readme_content": "# {chapter_name} — 知识图谱\\n\\n..."
}}
```

**重要提示**：
1. JSON格式的fact，content字段应为JSON对象（字符串形式）
2. Markdown格式的fact/skill，content字段为纯文本
3. 所有文件内容完整、格式正确、可直接保存

开始提取！
"""
    return prompt


def extract_chapter_knowledge(chapter_num):
    """提取单个章节的知识"""
    print(f"\n{'='*60}")
    print(f"处理章节 {chapter_num:03d}")
    print(f"{'='*60}")

    # 获取章节信息
    chapter_file, chapter_name = get_chapter_info(chapter_num)
    if not chapter_file:
        print(f"  [跳过] 未找到章节文件")
        return None

    print(f"  章节: {chapter_name}")
    print(f"  文件: {chapter_file.name}")

    # 检查输出目录是否已存在
    output_chapter_dir = OUTPUT_DIR / f"chapter_{chapter_num:03d}"
    if output_chapter_dir.exists():
        print(f"  [警告] 输出目录已存在，将覆盖: {output_chapter_dir}")

    # 读取章节内容
    chapter_content = read_file(chapter_file)
    print(f"  字数: {len(chapter_content)}")

    # 读取参考示例
    examples = read_reference_examples()

    # 创建提取prompt
    prompt = create_extraction_prompt(chapter_content, chapter_name, chapter_num, examples)

    # 调用Claude API
    print(f"  [API] 调用Claude Sonnet 4.5进行知识提取...")
    try:
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=16000,
            temperature=0.3,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response_text = message.content[0].text
        print(f"  [API] 响应长度: {len(response_text)} 字符")

        # 解析JSON响应
        # 提取JSON代码块
        import re
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 尝试直接解析整个响应
            json_str = response_text

        result = json.loads(json_str)

        # 保存文件
        save_chapter_files(output_chapter_dir, result)

        # 统计
        stats = {
            "chapter_num": chapter_num,
            "chapter_name": chapter_name,
            "facts_count": len(result.get("facts", [])),
            "skills_count": len(result.get("skills", [])),
            "eureka_count": count_eureka_items(result.get("eureka_content", "")),
        }

        print(f"  [完成] Facts: {stats['facts_count']}, Skills: {stats['skills_count']}, Eureka: {stats['eureka_count']}")
        return stats

    except Exception as e:
        print(f"  [错误] {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def save_chapter_files(output_dir, result):
    """保存章节文件"""
    # 创建目录结构
    facts_dir = output_dir / "skus" / "facts"
    skills_dir = output_dir / "skus" / "skills"
    facts_dir.mkdir(parents=True, exist_ok=True)
    skills_dir.mkdir(parents=True, exist_ok=True)

    # 保存facts
    for fact in result.get("facts", []):
        filename = fact["filename"]
        content = fact["content"]

        # 如果是JSON格式，需要格式化
        if filename.endswith(".json"):
            if isinstance(content, str):
                content = json.loads(content)
            content = json.dumps(content, ensure_ascii=False, indent=2)

        write_file(facts_dir / filename, content)

    # 保存skills
    for skill in result.get("skills", []):
        filename = skill["filename"]
        content = skill["content"]
        write_file(skills_dir / filename, content)

    # 保存其他文件
    write_file(output_dir / "eureka.md", result.get("eureka_content", ""))
    write_file(output_dir / "mapping.md", result.get("mapping_content", ""))
    write_file(output_dir / "README.md", result.get("readme_content", ""))


def count_eureka_items(eureka_content):
    """统计eureka条数（通过##标题计数）"""
    import re
    matches = re.findall(r'^## ', eureka_content, re.MULTILINE)
    return len(matches)


def main():
    """主函数"""
    print("="*60)
    print("批量提取《史记》031-060章节的知识单元")
    print("="*60)

    # 要处理的章节范围
    chapters_to_process = range(31, 61)  # 031-060

    all_stats = []

    for chapter_num in chapters_to_process:
        stats = extract_chapter_knowledge(chapter_num)
        if stats:
            all_stats.append(stats)

        # 为了避免API限流，每章之间暂停
        import time
        time.sleep(2)

    # 打印统计报告
    print("\n" + "="*60)
    print("统计报告")
    print("="*60)
    print(f"{'章节':<6} {'章节名':<20} {'Facts':<8} {'Skills':<8} {'Eureka':<8}")
    print("-"*60)

    total_facts = 0
    total_skills = 0
    total_eureka = 0

    for stats in all_stats:
        print(f"{stats['chapter_num']:03d}    {stats['chapter_name']:<20} {stats['facts_count']:<8} {stats['skills_count']:<8} {stats['eureka_count']:<8}")
        total_facts += stats['facts_count']
        total_skills += stats['skills_count']
        total_eureka += stats['eureka_count']

    print("-"*60)
    print(f"{'合计':<26} {total_facts:<8} {total_skills:<8} {total_eureka:<8}")
    print("="*60)

    # 保存统计报告
    report_path = OUTPUT_DIR / "extraction_report_031_060.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("《史记》031-060章节知识提取统计报告\n")
        f.write("="*60 + "\n\n")
        f.write(f"{'章节':<6} {'章节名':<20} {'Facts':<8} {'Skills':<8} {'Eureka':<8}\n")
        f.write("-"*60 + "\n")
        for stats in all_stats:
            f.write(f"{stats['chapter_num']:03d}    {stats['chapter_name']:<20} {stats['facts_count']:<8} {stats['skills_count']:<8} {stats['eureka_count']:<8}\n")
        f.write("-"*60 + "\n")
        f.write(f"{'合计':<26} {total_facts:<8} {total_skills:<8} {total_eureka:<8}\n")

    print(f"\n报告已保存到: {report_path}")


if __name__ == "__main__":
    main()
