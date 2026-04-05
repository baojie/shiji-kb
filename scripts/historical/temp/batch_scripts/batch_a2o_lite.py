#!/usr/bin/env python3
"""
批量应用a2o-lite方法处理所有史记章节
为每一章生成SKU（facts和skills）
"""

import os
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple
import anthropic

# 配置
CHAPTER_MD_DIR = Path("/home/baojie/work/knowledge/shiji-kb/chapter_md")
OUTPUT_BASE_DIR = Path("/home/baojie/work/knowledge/shiji-kb/kg/ontology/ontology-v2/chapters")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# Claude模型
MODEL = "claude-sonnet-4-5-20250929"
MAX_TOKENS = 16000

def get_chapter_files(start: int = 2, end: int = 130) -> List[Path]:
    """获取指定范围的章节文件"""
    files = sorted(CHAPTER_MD_DIR.glob("*.tagged.md"))
    return [f for f in files if f.name.startswith(tuple(f"{i:03d}_" for i in range(start, end + 1)))]

def parse_chapter_number(filename: str) -> int:
    """从文件名提取章节号"""
    match = re.match(r"(\d{3})_", filename)
    return int(match.group(1)) if match else 0

def read_chapter(filepath: Path) -> str:
    """读取章节内容"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def create_chapter_dirs(chapter_num: int) -> Dict[str, Path]:
    """创建章节目录结构"""
    chapter_dir = OUTPUT_BASE_DIR / f"chapter_{chapter_num:03d}"
    facts_dir = chapter_dir / "skus" / "facts"
    skills_dir = chapter_dir / "skus" / "skills"

    facts_dir.mkdir(parents=True, exist_ok=True)
    skills_dir.mkdir(parents=True, exist_ok=True)

    return {
        "chapter": chapter_dir,
        "facts": facts_dir,
        "skills": skills_dir
    }

def extract_knowledge_with_claude(chapter_text: str, chapter_name: str) -> Dict:
    """使用Claude提取知识"""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""请对以下《史记》章节应用a2o-lite方法，提取事实性知识（facts）和程序性知识（skills）。

章节名称：{chapter_name}

章节内容：
{chapter_text[:50000]}  # 限制长度避免超限

请按以下格式返回JSON：
{{
  "facts": [
    {{
      "filename": "fact_001.md" 或 "fact_001.json",
      "name": "知识单元标识名",
      "description": "一句话描述",
      "content": "内容（markdown格式）",
      "is_json": false,
      "json_data": {{}} // 如果is_json为true，这里是结构化数据
    }}
  ],
  "skills": [
    {{
      "filename": "skill_001.md",
      "name": "技能标识名",
      "description": "何时使用此技能",
      "content": "完整的markdown内容（包含frontmatter）"
    }}
  ],
  "eureka_insights": [
    "洞察1",
    "洞察2"
  ]
}}

要求：
1. 遵循MECE原则（相互独立，完全穷尽）
2. 结构化数据（表格、列表）保持为单个单元
3. facts包含事实性知识（人物、事件、数据等）
4. skills包含程序性知识（方法、流程、技巧等）
5. eureka_insights仅包含真正跨领域的洞察（质量重于数量）
6. 每个fact和skill必须有清晰的使用场景

请直接返回JSON，不要额外解释。"""

    try:
        message = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        # 提取JSON内容
        response_text = message.content[0].text
        # 尝试解析JSON
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        else:
            return {"facts": [], "skills": [], "eureka_insights": []}

    except Exception as e:
        print(f"❌ Claude提取失败: {e}")
        return {"facts": [], "skills": [], "eureka_insights": []}

def save_facts(facts: List[Dict], facts_dir: Path) -> int:
    """保存facts到文件"""
    count = 0
    for fact in facts:
        filepath = facts_dir / fact["filename"]

        if fact.get("is_json", False):
            # JSON格式
            data = {
                "name": fact["name"],
                "description": fact["description"],
                "data": fact.get("json_data", {})
            }
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        else:
            # Markdown格式
            content = f"""---
name: {fact["name"]}
description: {fact["description"]}
---

{fact.get("content", "")}
"""
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

        count += 1

    return count

def save_skills(skills: List[Dict], skills_dir: Path) -> int:
    """保存skills到文件"""
    count = 0
    for skill in skills:
        filepath = skills_dir / skill["filename"]
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(skill["content"])
        count += 1

    return count

def generate_mapping(facts: List[Dict], skills: List[Dict], chapter_name: str) -> str:
    """生成mapping.md内容"""
    content = f"""# SKU 映射 — {chapter_name}

本文件将《史记·{chapter_name}》的所有标准知识单元（SKU）映射到其使用场景。

---

## 事实性知识（Facts）

"""

    for fact in facts:
        filename = fact["filename"]
        name = fact["name"]
        desc = fact["description"]
        content += f"""- **[factual] skus/facts/{filename}**
  - **描述**：{desc}
  - **使用场景**：（待补充）

"""

    content += """
## 程序性知识（Skills）

"""

    for skill in skills:
        filename = skill["filename"]
        name = skill["name"]
        desc = skill["description"]
        content += f"""- **[procedural] skus/skills/{filename}**
  - **描述**：{desc}
  - **使用场景**：（待补充）

"""

    return content

def generate_eureka(insights: List[str], chapter_name: str) -> str:
    """生成eureka.md内容"""
    content = f"""# 灵感笔记 — {chapter_name}

知识提取过程中发现的跨领域洞察和创意。

---

"""

    if not insights:
        content += "*暂无洞察。*\n"
    else:
        for i, insight in enumerate(insights, 1):
            content += f"{i}. {insight} [{chapter_name}]\n\n"

    content += f"""
---

**洞察统计**：{len(insights)}条
**来源章节**：{chapter_name}
"""

    return content

def generate_readme(chapter_num: int, chapter_name: str, facts: List[Dict], skills: List[Dict], eureka_count: int) -> str:
    """生成README.md内容"""
    content = f"""# {chapter_name} — 知识图谱

本目录包含《史记·{chapter_name}》章节的结构化知识提取。

---

## 目录结构

```
chapter_{chapter_num:03d}/
├── skus/
│   ├── facts/          # 事实性知识单元（{len(facts)}个）
│   └── skills/         # 程序性知识单元（{len(skills)}个）
├── mapping.md          # SKU使用场景映射
├── eureka.md           # 跨领域洞察（{eureka_count}条）
└── README.md           # 本文件
```

---

## 知识单元概览

### 事实性知识（Facts）

| 编号 | 名称 | 格式 | 核心内容 |
|------|------|------|----------|
"""

    for fact in facts:
        fact_id = fact["filename"].replace(".md", "").replace(".json", "")
        fmt = "JSON" if fact.get("is_json", False) else "Markdown"
        content += f"| {fact_id} | {fact['name']} | {fmt} | {fact['description']} |\n"

    content += """
### 程序性知识（Skills）

| 编号 | 名称 | 应用场景 |
|------|------|----------|
"""

    for skill in skills:
        skill_id = skill["filename"].replace(".md", "")
        content += f"| {skill_id} | {skill['name']} | {skill['description'][:50]}... |\n"

    content += f"""
---

## 跨领域洞察（Eureka）

本章提取出{eureka_count}条跨领域洞察。

---

**版本**：v1.0
**创建日期**：2026-04-05
**SKU总数**：{len(facts) + len(skills)}个（{len(facts)} facts + {len(skills)} skills）
**跨域洞察**：{eureka_count}条
"""

    return content

def process_chapter(chapter_file: Path) -> Dict:
    """处理单个章节，返回统计信息"""
    chapter_num = parse_chapter_number(chapter_file.name)
    chapter_name = chapter_file.stem.replace(".tagged", "").split("_", 1)[1]

    print(f"📖 处理章节 {chapter_num:03d}：{chapter_name}")

    # 读取章节内容
    chapter_text = read_chapter(chapter_file)

    # 创建目录
    dirs = create_chapter_dirs(chapter_num)

    # 使用Claude提取知识
    print(f"  🤖 使用Claude提取知识...")
    knowledge = extract_knowledge_with_claude(chapter_text, chapter_name)

    facts = knowledge.get("facts", [])
    skills = knowledge.get("skills", [])
    eureka_insights = knowledge.get("eureka_insights", [])

    # 保存facts
    facts_count = save_facts(facts, dirs["facts"])
    print(f"  ✓ 保存了 {facts_count} 个facts")

    # 保存skills
    skills_count = save_skills(skills, dirs["skills"])
    print(f"  ✓ 保存了 {skills_count} 个skills")

    # 生成mapping.md
    mapping_content = generate_mapping(facts, skills, chapter_name)
    with open(dirs["chapter"] / "mapping.md", 'w', encoding='utf-8') as f:
        f.write(mapping_content)
    print(f"  ✓ 生成了 mapping.md")

    # 生成eureka.md
    eureka_content = generate_eureka(eureka_insights, chapter_name)
    with open(dirs["chapter"] / "eureka.md", 'w', encoding='utf-8') as f:
        f.write(eureka_content)
    print(f"  ✓ 生成了 eureka.md（{len(eureka_insights)}条洞察）")

    # 生成README.md
    readme_content = generate_readme(chapter_num, chapter_name, facts, skills, len(eureka_insights))
    with open(dirs["chapter"] / "README.md", 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print(f"  ✓ 生成了 README.md")

    print(f"✅ 章节 {chapter_num:03d} 处理完成\n")

    return {
        "chapter_num": chapter_num,
        "chapter_name": chapter_name,
        "facts": facts_count,
        "skills": skills_count,
        "eureka": len(eureka_insights)
    }

def main(start: int = 2, end: int = 10):
    """主函数"""
    print("=" * 70)
    print(f"批量应用a2o-lite方法处理史记章节（{start:03d}-{end:03d}）")
    print("=" * 70)
    print()

    # 检查API Key
    if not ANTHROPIC_API_KEY:
        print("❌ 错误：未找到ANTHROPIC_API_KEY环境变量")
        return

    # 获取指定范围的章节文件
    chapter_files = get_chapter_files(start, end)
    total = len(chapter_files)
    print(f"📚 找到 {total} 个待处理章节（{start:03d}-{end:03d}）\n")

    # 处理每个章节
    stats = []
    for i, chapter_file in enumerate(chapter_files, 1):
        print(f"[{i}/{total}] ", end="")
        stat = process_chapter(chapter_file)
        stats.append(stat)

    # 输出统计报告
    print()
    print("=" * 70)
    print("统计报告")
    print("=" * 70)
    print(f"{'章节':<25} {'Facts':<10} {'Skills':<10} {'Eureka':<10}")
    print("-" * 70)

    total_facts = 0
    total_skills = 0
    total_eureka = 0

    for stat in stats:
        chapter_label = f"{stat['chapter_num']:03d}_{stat['chapter_name']}"
        print(f"{chapter_label:<25} {stat['facts']:<10} {stat['skills']:<10} {stat['eureka']:<10}")
        total_facts += stat['facts']
        total_skills += stat['skills']
        total_eureka += stat['eureka']

    print("-" * 70)
    print(f"{'总计':<25} {total_facts:<10} {total_skills:<10} {total_eureka:<10}")
    print("=" * 70)
    print(f"\n✅ 完成！成功处理 {len(stats)}/{total} 个章节")

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3:
        start = int(sys.argv[1])
        end = int(sys.argv[2])
        main(start, end)
    else:
        # 默认处理002-010
        main(2, 10)
