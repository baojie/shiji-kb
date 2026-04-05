#!/usr/bin/env python3
"""
使用a2o-lite方法批量处理《史记》章节，提取事实性知识和程序性知识。

用法:
    python scripts/generate_a2o_chapters.py 091 120
"""

import os
import sys
import json
import re
from pathlib import Path
from anthropic import Anthropic

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
CHAPTER_MD_DIR = PROJECT_ROOT / "chapter_md"
OUTPUT_BASE_DIR = PROJECT_ROOT / "kg" / "ontology" / "ontology-v2" / "chapters"

# Anthropic API客户端
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def read_chapter(chapter_num):
    """读取章节文件"""
    pattern = f"{chapter_num:03d}_*.tagged.md"
    files = list(CHAPTER_MD_DIR.glob(pattern))
    if not files:
        raise FileNotFoundError(f"未找到章节文件: {pattern}")

    with open(files[0], 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取章节名称
    title = files[0].stem.replace('.tagged', '').replace(f'{chapter_num:03d}_', '')
    return title, content

def create_chapter_directory(chapter_num):
    """创建章节目录结构"""
    chapter_dir = OUTPUT_BASE_DIR / f"chapter_{chapter_num:03d}"
    facts_dir = chapter_dir / "skus" / "facts"
    skills_dir = chapter_dir / "skus" / "skills"

    facts_dir.mkdir(parents=True, exist_ok=True)
    skills_dir.mkdir(parents=True, exist_ok=True)

    return chapter_dir

def extract_knowledge_with_ai(title, content, chapter_num):
    """使用Claude API提取知识单元"""

    prompt = f"""你是《史记》知识提取专家。请使用a2o-lite方法从以下章节中提取结构化知识。

章节：{chapter_num:03d}_{title}

这是一篇列传，请重点提取：
1. **事实性知识（Facts）**：人物生平、核心事迹、思想主张、历史评价、重要事件、人物关系等
2. **程序性知识（Skills）**：可复用的方法论、策略、决策过程等

**提取原则**：
- MECE原则（相互独立，完全穷尽）
- 结构化数据作为单个单元保留（不拆分表格/列表）
- 事实与技能分离
- 质量重于数量
- 每个SKU应当独立、完整、可复用

**输出格式**：
请以JSON格式返回，包含以下字段：
```json
{{
  "facts": [
    {{
      "id": "fact_001",
      "name": "简短名称",
      "description": "详细描述",
      "type": "json|markdown",
      "content": "实际内容（JSON对象或Markdown文本）"
    }}
  ],
  "skills": [
    {{
      "id": "skill_001",
      "name": "简短名称",
      "description": "详细描述",
      "content": "Markdown格式的详细步骤和决策点"
    }}
  ],
  "eureka": [
    {{
      "title": "洞察标题",
      "content": "跨领域洞察内容"
    }}
  ]
}}
```

章节内容：
{content[:20000]}  # 限制长度避免超出token限制

请开始提取："""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=16000,
        temperature=0.7,
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )

    # 提取JSON响应
    response_text = response.content[0].text

    # 尝试提取JSON块
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # 如果没有代码块，尝试直接解析
        json_str = response_text

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"JSON解析失败: {e}")
        print(f"响应内容: {response_text[:500]}")
        raise

def save_knowledge_units(chapter_dir, knowledge):
    """保存知识单元到文件"""
    facts_dir = chapter_dir / "skus" / "facts"
    skills_dir = chapter_dir / "skus" / "skills"

    fact_count = 0
    skill_count = 0

    # 保存Facts
    for fact in knowledge.get('facts', []):
        fact_id = fact['id']
        fact_type = fact.get('type', 'markdown')

        if fact_type == 'json':
            filepath = facts_dir / f"{fact_id}.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    "name": fact['name'],
                    "description": fact['description'],
                    "data": fact['content']
                }, f, ensure_ascii=False, indent=2)
        else:
            filepath = facts_dir / f"{fact_id}.md"
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"---\n")
                f.write(f"name: {fact['name']}\n")
                f.write(f"description: {fact['description']}\n")
                f.write(f"---\n\n")
                f.write(fact['content'])

        fact_count += 1

    # 保存Skills
    for skill in knowledge.get('skills', []):
        skill_id = skill['id']
        filepath = skills_dir / f"{skill_id}.md"

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"---\n")
            f.write(f"name: {skill['name']}\n")
            f.write(f"description: {skill['description']}\n")
            f.write(f"---\n\n")
            f.write(skill['content'])

        skill_count += 1

    return fact_count, skill_count

def generate_mapping(chapter_dir, title, knowledge):
    """生成mapping.md"""
    filepath = chapter_dir / "mapping.md"

    content = f"# SKU 映射 — {title}\n\n"
    content += f"本文件将《史记·{title}》的所有标准知识单元（SKU）映射到其使用场景。\n\n"
    content += "---\n\n"

    # 按主题分组Facts
    content += "## 事实性知识单元\n\n"
    for fact in knowledge.get('facts', []):
        content += f"- **[factual] skus/facts/{fact['id']}.{'json' if fact.get('type')=='json' else 'md'}**\n"
        content += f"  - **描述**：{fact['description']}\n"
        content += f"  - **使用场景**：{fact.get('use_cases', '待补充')}\n\n"

    # Skills
    content += "## 程序性知识单元\n\n"
    for skill in knowledge.get('skills', []):
        content += f"- **[procedural] skus/skills/{skill['id']}.md**\n"
        content += f"  - **描述**：{skill['description']}\n"
        content += f"  - **使用场景**：{skill.get('use_cases', '待补充')}\n\n"

    content += "---\n\n"
    content += f"**本章SKU统计**：\n"
    content += f"- 事实性知识单元（facts）：{len(knowledge.get('facts', []))}个\n"
    content += f"- 程序性知识单元（skills）：{len(knowledge.get('skills', []))}个\n"
    content += f"- 总计：{len(knowledge.get('facts', [])) + len(knowledge.get('skills', []))}个SKU\n\n"

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def generate_eureka(chapter_dir, title, knowledge):
    """生成eureka.md"""
    filepath = chapter_dir / "eureka.md"

    content = f"# 灵感笔记 — {title}\n\n"
    content += "知识提取过程中发现的跨领域洞察和创意。\n\n"
    content += "---\n\n"

    for item in knowledge.get('eureka', []):
        content += f"## {item['title']}\n\n"
        content += f"{item['content']}\n\n"

    content += "---\n\n"
    content += f"**洞察统计**：{len(knowledge.get('eureka', []))}条\n"
    content += f"**来源章节**：{title}\n\n"

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def generate_readme(chapter_dir, chapter_num, title, knowledge):
    """生成README.md"""
    filepath = chapter_dir / "README.md"

    fact_count = len(knowledge.get('facts', []))
    skill_count = len(knowledge.get('skills', []))
    eureka_count = len(knowledge.get('eureka', []))

    content = f"# {title} — 知识图谱\n\n"
    content += f"本目录包含《史记·{title}》章节的结构化知识提取。\n\n"
    content += "---\n\n"

    content += "## 目录结构\n\n"
    content += "```\n"
    content += f"chapter_{chapter_num:03d}/\n"
    content += "├── skus/\n"
    content += f"│   ├── facts/          # 事实性知识单元（{fact_count}个）\n"
    for i, fact in enumerate(knowledge.get('facts', [])[:5], 1):
        ext = 'json' if fact.get('type') == 'json' else 'md'
        content += f"│   │   ├── {fact['id']}.{ext}    # {fact['description'][:30]}...\n"
    if fact_count > 5:
        content += f"│   │   └── ...                 # 更多facts\n"
    content += f"│   └── skills/         # 程序性知识单元（{skill_count}个）\n"
    for i, skill in enumerate(knowledge.get('skills', [])[:3], 1):
        content += f"│   │   ├── {skill['id']}.md     # {skill['description'][:30]}...\n"
    if skill_count > 3:
        content += f"│   │   └── ...                 # 更多skills\n"
    content += "├── mapping.md          # SKU使用场景映射\n"
    content += f"├── eureka.md           # 跨领域洞察（{eureka_count}条）\n"
    content += "└── README.md           # 本文件\n"
    content += "```\n\n"
    content += "---\n\n"

    content += "## 知识单元概览\n\n"

    content += "### 事实性知识（Facts）\n\n"
    content += "| 编号 | 名称 | 格式 | 核心内容 |\n"
    content += "|------|------|------|----------|\n"
    for fact in knowledge.get('facts', []):
        fact_type = 'JSON' if fact.get('type') == 'json' else 'Markdown'
        content += f"| {fact['id']} | {fact['name']} | {fact_type} | {fact['description']} |\n"
    content += "\n"

    content += "### 程序性知识（Skills）\n\n"
    content += "| 编号 | 名称 | 应用场景 |\n"
    content += "|------|------|----------|\n"
    for skill in knowledge.get('skills', []):
        content += f"| {skill['id']} | {skill['name']} | {skill['description']} |\n"
    content += "\n"

    content += "---\n\n"
    content += "## 跨领域洞察（Eureka）\n\n"
    content += f"本章提取出{eureka_count}条跨领域洞察。\n\n"
    for i, item in enumerate(knowledge.get('eureka', []), 1):
        content += f"{i}. **{item['title']}**\n"
    content += "\n---\n\n"

    content += "**版本**：v1.0\n"
    content += "**创建日期**：2026-04-05\n"
    content += f"**SKU总数**：{fact_count + skill_count}个（{fact_count} facts + {skill_count} skills）\n"
    content += f"**跨域洞察**：{eureka_count}条\n"

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def process_chapter(chapter_num):
    """处理单个章节"""
    print(f"\n{'='*60}")
    print(f"处理章节 {chapter_num:03d}")
    print(f"{'='*60}")

    try:
        # 读取章节
        title, content = read_chapter(chapter_num)
        print(f"章节标题: {title}")
        print(f"章节长度: {len(content)} 字符")

        # 创建目录
        chapter_dir = create_chapter_directory(chapter_num)
        print(f"创建目录: {chapter_dir}")

        # 使用AI提取知识
        print("正在调用Claude API提取知识...")
        knowledge = extract_knowledge_with_ai(title, content, chapter_num)

        # 保存知识单元
        fact_count, skill_count = save_knowledge_units(chapter_dir, knowledge)
        print(f"保存了 {fact_count} 个facts, {skill_count} 个skills")

        # 生成辅助文件
        generate_mapping(chapter_dir, title, knowledge)
        print("生成 mapping.md")

        generate_eureka(chapter_dir, title, knowledge)
        print(f"生成 eureka.md ({len(knowledge.get('eureka', []))} 条洞察)")

        generate_readme(chapter_dir, chapter_num, title, knowledge)
        print("生成 README.md")

        return {
            'chapter_num': chapter_num,
            'title': title,
            'fact_count': fact_count,
            'skill_count': skill_count,
            'eureka_count': len(knowledge.get('eureka', [])),
            'success': True
        }

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return {
            'chapter_num': chapter_num,
            'success': False,
            'error': str(e)
        }

def main():
    if len(sys.argv) != 3:
        print("用法: python scripts/generate_a2o_chapters.py <起始章节> <结束章节>")
        print("示例: python scripts/generate_a2o_chapters.py 091 120")
        sys.exit(1)

    start_chapter = int(sys.argv[1])
    end_chapter = int(sys.argv[2])

    print(f"开始处理章节 {start_chapter:03d} 到 {end_chapter:03d}")
    print(f"总共 {end_chapter - start_chapter + 1} 个章节")

    results = []

    for chapter_num in range(start_chapter, end_chapter + 1):
        result = process_chapter(chapter_num)
        results.append(result)

    # 输出统计报告
    print("\n" + "="*60)
    print("处理完成！统计报告：")
    print("="*60)

    success_count = sum(1 for r in results if r['success'])
    total_facts = sum(r.get('fact_count', 0) for r in results if r['success'])
    total_skills = sum(r.get('skill_count', 0) for r in results if r['success'])
    total_eureka = sum(r.get('eureka_count', 0) for r in results if r['success'])

    print(f"\n成功处理: {success_count}/{len(results)} 章节")
    print(f"总计提取:")
    print(f"  - Facts: {total_facts} 个")
    print(f"  - Skills: {total_skills} 个")
    print(f"  - Eureka洞察: {total_eureka} 条")
    print(f"  - SKU总数: {total_facts + total_skills} 个")

    print("\n各章节详情:")
    print(f"{'章节':<10} {'标题':<20} {'Facts':<8} {'Skills':<8} {'Eureka':<8} {'状态':<10}")
    print("-" * 70)
    for r in results:
        if r['success']:
            print(f"{r['chapter_num']:03d}      {r['title']:<20} {r['fact_count']:<8} {r['skill_count']:<8} {r['eureka_count']:<8} ✓")
        else:
            print(f"{r['chapter_num']:03d}      {'N/A':<20} {'N/A':<8} {'N/A':<8} {'N/A':<8} ✗ {r.get('error', '')[:20]}")

    print("\n" + "="*60)

if __name__ == "__main__":
    main()
