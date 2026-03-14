#!/usr/bin/env python3
"""
用《中国历史大事年表》交叉验证130章事件索引的年份标注。

策略：
1. 从年表提取"人物→活跃年份"和"关键事件→年份"的对照表
2. 从事件索引提取每个事件的标注年份和涉及人物
3. 交叉验证，找出明显偏差

输出：偏差报告 + 建议修正的JSON文件
"""

import os
import re
import json
import glob
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
CHRONOLOGY = os.path.join(BASE_DIR, "kg", "chronology", "data", "中国历史大事年表.md")
EVENTS_DIR = os.path.join(BASE_DIR, "kg", "events", "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "kg", "events", "data")

# ============================================================
# 第一步：从年表提取人物活跃年份
# ============================================================

def parse_chronology(path):
    """解析年表，返回：
    - person_years: {人名: [年份列表]}  人物在年表中出现的年份
    - event_keywords: {关键词: 年份}  特征事件对应的年份
    """
    person_years = defaultdict(list)
    event_keywords = {}

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 匹配 ### 前XXX年 格式的年份标题
    year_pattern = re.compile(r"^### 前(\d+)年", re.MULTILINE)
    matches = list(year_pattern.finditer(content))

    for i, m in enumerate(matches):
        year_bce = int(m.group(1))
        # 获取该年份下的正文（到下一个年份或文件末尾）
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        text = content[start:end].strip()

        # 提取人名（简单启发式：2-4字中文词，出现在特定上下文中）
        # 主要关注"XXX死"、"XXX卒"、"XXX自杀"等死亡记录
        death_patterns = [
            (r"(\w{2,4})(?:死|卒|自杀|被杀|病死|崩)(?:（前(\d+)[—一]）)?", "death"),
            (r"丞相(\w{2,4})", "active"),
            (r"以(\w{2,4})为丞相", "active"),
            (r"(\w{2,4})为丞相", "active"),
        ]

        for pat, ptype in death_patterns:
            for pm in re.finditer(pat, text):
                name = pm.group(1)
                # 过滤太短或明显非人名的
                if len(name) < 2 or name in ("是年", "此后", "从此", "因此", "匈奴", "南越", "东越", "西域"):
                    continue
                if ptype == "death":
                    person_years[name].append((-year_bce, "death"))
                else:
                    person_years[name].append((-year_bce, "active"))

        # 提取关键事件（战争、重大政治事件等）
        key_events = {
            "阪泉之战": None,  # 传说
            "涿鹿之战": None,
            "牧野之战": 1046,
            "共和行政": 841,
            "犬戎灭周": 771,
            "三家灭智": 453,
            "三家分晋": 403,
            "长平之战": 260,
            "焚书": 213,
            "坑儒": 212,
            "大泽乡起义": 209,
            "巨鹿之战": 207,
            "鸿门宴": 206,
            "垓下之战": 202,
            "白登之围": 200,
            "七国之乱": 154,
            "封禅泰山": 110,
            "巫蛊之祸": 91,
            "太初改历": 104,
        }

        for kw, expected in key_events.items():
            if kw in text:
                event_keywords[kw] = year_bce

    return person_years, event_keywords


# ============================================================
# 第二步：从年表提取人物死亡年份（更精确）
# ============================================================

def extract_death_years(path):
    """专门提取年表中记载的人物死亡年份"""
    deaths = {}

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    year_pattern = re.compile(r"^### 前(\d+)年", re.MULTILINE)
    matches = list(year_pattern.finditer(content))

    for i, m in enumerate(matches):
        year_bce = int(m.group(1))
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        text = content[start:end]

        # 匹配 "XXX死（前NNN—）" 或 "XXX死" 或 "XXX卒" 等
        for pm in re.finditer(r"(\w{2,4})(?:死|卒|自杀|被杀|病死|崩)", text):
            name = pm.group(1)
            if len(name) >= 2 and name not in ("是年", "此后", "从此", "因此", "不久"):
                deaths[name] = year_bce

    return deaths


# ============================================================
# 第三步：从事件索引提取事件和年份
# ============================================================

def parse_event_index(path):
    """解析事件索引文件，返回事件列表：
    [{id, name, year_bce, year_type, persons, is_death_event}, ...]
    """
    events = []

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 解析概览表
    table_pattern = re.compile(
        r"\|\s*([\d-]+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|"
    )

    for m in table_pattern.finditer(content):
        event_id = m.group(1).strip()
        event_name = m.group(2).strip()
        event_type = m.group(3).strip()
        time_str = m.group(4).strip()

        if event_id == "事件ID" or not re.match(r"\d{3}-\d{3}", event_id):
            continue

        # 提取年份
        year_bce = None
        year_type = None

        # 精确纪年
        precise = re.search(r"（公元前(\d+)年）", time_str)
        if precise:
            year_bce = int(precise.group(1))
            year_type = "precise"

        # 推断纪年
        inferred = re.search(r"\[约公元前(\d+)年\]", time_str)
        if inferred:
            if year_bce is None:
                year_bce = int(inferred.group(1))
                year_type = "inferred"

        # 提取人物（v2.1格式：〖@人名〗）
        persons = re.findall(r"〖@([^〖〗\n]+)〗", m.group(0))

        # 判断是否为死亡事件
        is_death = bool(re.search(r"崩|卒|死|薨|自杀|被杀", event_name))

        events.append({
            "id": event_id,
            "name": event_name,
            "year_bce": year_bce,
            "year_type": year_type,
            "persons": persons,
            "is_death": is_death,
        })

    return events


# ============================================================
# 第四步：交叉验证
# ============================================================

def cross_validate(events, death_years, event_keywords, chapter_id):
    """交叉验证事件年份，返回偏差列表"""
    issues = []

    # 检查同一章内是否有所有推断事件指向同一年份（单锚点塌缩）
    inferred_years = [e["year_bce"] for e in events if e["year_type"] == "inferred" and e["year_bce"]]
    if inferred_years:
        from collections import Counter
        year_counts = Counter(inferred_years)
        most_common_year, count = year_counts.most_common(1)[0]
        total_inferred = len(inferred_years)
        if total_inferred >= 5 and count / total_inferred > 0.7:
            issues.append({
                "type": "anchor_collapse",
                "chapter": chapter_id,
                "detail": f"{count}/{total_inferred}个推断事件指向同一年份（前{most_common_year}年），疑似单锚点塌缩",
                "severity": "high",
            })

    # 检查死亡事件的年份
    for e in events:
        if not e["year_bce"]:
            continue

        # 死亡事件 vs 年表中的死亡记录
        if e["is_death"]:
            for person in e["persons"]:
                if person in death_years:
                    ref_year = death_years[person]
                    diff = abs(e["year_bce"] - ref_year)
                    if diff > 5:
                        issues.append({
                            "type": "death_year_mismatch",
                            "chapter": chapter_id,
                            "event_id": e["id"],
                            "event_name": e["name"],
                            "current_year": e["year_bce"],
                            "reference_year": ref_year,
                            "person": person,
                            "diff": diff,
                            "detail": f"{e['id']} {e['name']}：标注前{e['year_bce']}年，年表记载{person}死于前{ref_year}年，偏差{diff}年",
                            "severity": "high" if diff > 20 else "medium",
                        })

        # 事件名中包含关键事件
        for kw, ref_year in event_keywords.items():
            if kw in e["name"]:
                diff = abs(e["year_bce"] - ref_year)
                if diff > 3:
                    issues.append({
                        "type": "known_event_mismatch",
                        "chapter": chapter_id,
                        "event_id": e["id"],
                        "event_name": e["name"],
                        "current_year": e["year_bce"],
                        "reference_year": ref_year,
                        "keyword": kw,
                        "diff": diff,
                        "detail": f"{e['id']} {e['name']}：标注前{e['year_bce']}年，年表记载{kw}在前{ref_year}年，偏差{diff}年",
                        "severity": "high" if diff > 20 else "medium",
                    })

    return issues


# ============================================================
# 主函数
# ============================================================

def main():
    print("解析年表...")
    person_years, event_keywords = parse_chronology(CHRONOLOGY)
    death_years = extract_death_years(CHRONOLOGY)
    print(f"  年表人物死亡记录：{len(death_years)}条")
    print(f"  关键事件：{len(event_keywords)}条")

    # 扫描所有事件索引
    all_issues = []
    chapter_stats = []

    paths = sorted(glob.glob(os.path.join(EVENTS_DIR, "*_事件索引.md")))
    print(f"\n扫描 {len(paths)} 章事件索引...")

    for path in paths:
        fname = os.path.basename(path).replace("_事件索引.md", "")
        chapter_id = fname.split("_")[0]

        events = parse_event_index(path)
        if not events:
            continue

        issues = cross_validate(events, death_years, event_keywords, chapter_id)

        total = len(events)
        dated = sum(1 for e in events if e["year_bce"])
        high = sum(1 for i in issues if i.get("severity") == "high")
        medium = sum(1 for i in issues if i.get("severity") == "medium")

        chapter_stats.append({
            "chapter": chapter_id,
            "name": fname,
            "total_events": total,
            "dated_events": dated,
            "high_issues": high,
            "medium_issues": medium,
        })

        all_issues.extend(issues)

        if issues:
            print(f"  {fname}: {len(issues)}个问题（高{high}/中{medium}）")

    # 输出报告
    print(f"\n{'='*60}")
    print(f"总计：{len(all_issues)}个问题")
    print(f"  高优先级：{sum(1 for i in all_issues if i.get('severity')=='high')}")
    print(f"  中优先级：{sum(1 for i in all_issues if i.get('severity')=='medium')}")

    # 按严重程度排序输出
    high_issues = [i for i in all_issues if i.get("severity") == "high"]
    if high_issues:
        print(f"\n{'='*60}")
        print("高优先级问题详情：")
        print(f"{'='*60}")
        for i in sorted(high_issues, key=lambda x: x.get("diff", 0), reverse=True):
            print(f"  [{i['chapter']}] {i['detail']}")

    # 保存完整报告为JSON
    report = {
        "summary": {
            "total_issues": len(all_issues),
            "high": sum(1 for i in all_issues if i.get("severity") == "high"),
            "medium": sum(1 for i in all_issues if i.get("severity") == "medium"),
            "chapters_scanned": len(chapter_stats),
        },
        "issues": all_issues,
        "chapter_stats": chapter_stats,
    }

    report_path = os.path.join(OUTPUT_DIR, "date_validation_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n完整报告已保存到：{report_path}")

    # 找出需要优先审查的章节
    priority_chapters = sorted(
        [c for c in chapter_stats if c["high_issues"] > 0],
        key=lambda x: x["high_issues"],
        reverse=True,
    )
    if priority_chapters:
        print(f"\n建议优先审查的章节（按问题数排序）：")
        for c in priority_chapters[:20]:
            print(f"  {c['name']}: 高{c['high_issues']} 中{c['medium_issues']} （共{c['total_events']}事件）")


if __name__ == "__main__":
    main()
