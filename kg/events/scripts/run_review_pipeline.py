#!/usr/bin/env python3
"""
史记130章事件索引年代审查总管线

功能：
1. 逐章用 Claude 反思年代标注（基于 review 提示词 + SKILL 规则）
2. 辅以自动检测（格式/一致性/范围/锚点塌缩等）
3. 累积发现的新错误模式，用新发现更新 SKILL_04c_事件年代推断.md
4. 用累积知识更新下一章的 review 提示词
5. 生成每章审查报告 + 总汇报告

用法：
    python run_review_pipeline.py                  # 全部 001-130（自动检查）
    python run_review_pipeline.py --reflect        # 全部 001-130（Claude反思）
    python run_review_pipeline.py --reflect 001    # Claude反思单章
    python run_review_pipeline.py 001-012          # 自动检查范围
    python run_review_pipeline.py --reflect 001-005  # Claude反思范围
    python run_review_pipeline.py --resume         # 从上次中断处继续
    python run_review_pipeline.py --report         # 只看已有报告汇总
    python run_review_pipeline.py --reflect --dry  # 只生成提示词不调API
    python run_review_pipeline.py --prompt 109     # 输出单章Agent反思提示词
    python run_review_pipeline.py --ingest 109 result.json  # 导入Agent反思结果

模式：
    默认模式：只跑自动检查（快速，无API调用）
    --reflect：调用 Claude API 逐章反思（慢，消耗token，但能发现语义错误）
    --prompt：输出单章反思提示词到stdout，供Claude Code Agent调用
    --ingest：导入Agent输出的JSON结果，更新SKILL和下章提示词

输出：
    kg/events/reports/review_{chapter_id}.json     每章检测结果
    kg/events/reports/reflect_{chapter_id}.md      每章Claude反思报告
    kg/events/reports/pipeline_state.json          管线状态（已审/累积发现）
    kg/events/reports/summary.md                   汇总报告
"""

import os
import re
import json
import sys
import glob as glob_mod
import time
from collections import defaultdict, Counter
from datetime import datetime

# ============================================================
# 路径
# ============================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
EVENTS_DIR = os.path.join(BASE_DIR, "kg", "events", "data")
REPORTS_DIR = os.path.join(BASE_DIR, "kg", "events", "reports")
PROMPTS_DIR = os.path.join(BASE_DIR, "kg", "events", "prompts")
SKILL_PATH = os.path.join(BASE_DIR, "skills", "SKILL_04c_事件年代推断.md")
LIFESPANS_PATH = os.path.join(BASE_DIR, "kg", "entities", "data", "person_lifespans.json")
REIGN_PATH = os.path.join(BASE_DIR, "kg", "chronology", "data", "reign_periods.json")
STATE_PATH = os.path.join(REPORTS_DIR, "pipeline_state.json")

# ============================================================
# 加载参考数据
# ============================================================

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_person_lifespans():
    """返回 {名字: {"birth": int, "death": int}} （公元前为负数）"""
    data = load_json(LIFESPANS_PATH)
    return data.get("persons", {})


def load_reign_periods():
    """返回 {名字: {"state": str, "start_bce": int, "end_bce": int}}"""
    data = load_json(REIGN_PATH)
    return data.get("rulers", {})


def load_reign_years():
    """返回 {年号名: {"start_bce": int, ...}}  用于汉代年号换算"""
    data = load_json(REIGN_PATH)
    return data.get("reign_years", {})


# ============================================================
# 解析事件索引
# ============================================================

def parse_event_index(filepath):
    """解析事件索引文件，返回概览表 + 详情列表"""
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    result = {
        "filepath": filepath,
        "chapter_id": os.path.basename(filepath).split("_")[0],
        "chapter_name": os.path.basename(filepath).replace("_事件索引.md", "").split("_", 1)[1] if "_" in os.path.basename(filepath) else "",
        "overview_events": [],
        "detail_events": [],
        "raw_text": text,
    }

    # --- 解析概览表 ---
    table_pattern = re.compile(
        r"^\| (\d{3}-\d{3}) \| (.+?) \| (.+?) \| (.+?) \| (.+?) \| (.+?) \| (.+?) \|",
        re.MULTILINE
    )
    for m in table_pattern.finditer(text):
        result["overview_events"].append({
            "id": m.group(1),
            "name": m.group(2).strip(),
            "type": m.group(3).strip(),
            "time": m.group(4).strip(),
            "location": m.group(5).strip(),
            "persons": m.group(6).strip(),
            "dynasty": m.group(7).strip(),
        })

    # --- 解析详情 ---
    detail_pattern = re.compile(r"^### (\d{3}-\d{3}) (.+?)$", re.MULTILINE)
    detail_matches = list(detail_pattern.finditer(text))

    for i, m in enumerate(detail_matches):
        event_id = m.group(1)
        event_name = m.group(2).strip()
        # 提取该块的文本（到下一个 ### 或文件末尾）
        start = m.end()
        end = detail_matches[i + 1].start() if i + 1 < len(detail_matches) else len(text)
        block = text[start:end].strip()

        detail = {
            "id": event_id,
            "name": event_name,
            "block": block,
        }

        # 提取字段（兼容半角: 和全角：）
        for field_name in ["事件类型", "时间", "地点", "主要人物", "涉及朝代",
                           "事件描述", "原文引用", "段落位置", "年代推断"]:
            pat = re.compile(rf"- \*\*{field_name}\*\*[：:]\s*(.+?)$", re.MULTILINE)
            fm = pat.search(block)
            detail[field_name] = fm.group(1).strip() if fm else None

        result["detail_events"].append(detail)

    return result


# ============================================================
# 年份解析工具
# ============================================================

def extract_year_bce(time_str):
    """从时间字符串提取公元前年份（负数），返回 (year_bce, precision)
    precision: 'exact' | 'inferred' | 'approx' | None
    """
    if not time_str or time_str == "-":
        return None, None

    # 精确：（公元前XXX年）
    m = re.search(r"（公元前(\d+)年）", time_str)
    if m:
        return -int(m.group(1)), "exact"

    # 近似推算：[约公元前XXX年]
    m = re.search(r"\[约公元前(\d+)年\]", time_str)
    if m:
        return -int(m.group(1)), "approx"

    # 确定推算：[公元前XXX年]
    m = re.search(r"\[公元前(\d+)年\]", time_str)
    if m:
        return -int(m.group(1)), "inferred"

    # 只有原文纪年如 %建元三年%，无公元年
    return None, None


def year_to_str(year_bce):
    """负数转'前XXX年'"""
    if year_bce is None:
        return "?"
    return f"前{abs(year_bce)}年"


# ============================================================
# 检查函数（每个返回 issues 列表）
# ============================================================

def check_overview_detail_consistency(parsed):
    """检查1：概览表与详情的年份是否一致"""
    issues = []
    overview_map = {e["id"]: e for e in parsed["overview_events"]}
    detail_map = {e["id"]: e for e in parsed["detail_events"]}

    for eid, ov in overview_map.items():
        dt = detail_map.get(eid)
        if not dt:
            issues.append({
                "event_id": eid,
                "check": "概览详情一致性",
                "severity": "error",
                "message": f"概览表有 {eid}，但详情中无对应记录",
            })
            continue

        ov_year, ov_prec = extract_year_bce(ov["time"])
        dt_year, dt_prec = extract_year_bce(dt.get("时间", ""))

        if ov_year is not None and dt_year is not None and ov_year != dt_year:
            issues.append({
                "event_id": eid,
                "check": "概览详情年份不一致",
                "severity": "error",
                "message": f"概览={year_to_str(ov_year)}，详情={year_to_str(dt_year)}",
                "overview_time": ov["time"],
                "detail_time": dt.get("时间", ""),
            })

        if ov_prec is not None and dt_prec is not None and ov_prec != dt_prec:
            issues.append({
                "event_id": eid,
                "check": "概览详情精度不一致",
                "severity": "warning",
                "message": f"概览精度={ov_prec}，详情精度={dt_prec}",
            })

    # 反向检查
    for eid in detail_map:
        if eid not in overview_map:
            issues.append({
                "event_id": eid,
                "check": "概览详情一致性",
                "severity": "error",
                "message": f"详情有 {eid}，但概览表中无对应行",
            })

    return issues


def check_missing_fields(parsed):
    """检查2：详情中是否缺少年代推断行或时间行"""
    issues = []
    for evt in parsed["detail_events"]:
        if not evt.get("时间"):
            issues.append({
                "event_id": evt["id"],
                "check": "缺少时间字段",
                "severity": "error",
                "message": "详情缺少 **时间** 字段",
            })
        if not evt.get("年代推断"):
            issues.append({
                "event_id": evt["id"],
                "check": "缺少年代推断",
                "severity": "warning",
                "message": "详情缺少 **年代推断** 字段",
            })
        # 时间字段有原文纪年但无公元年
        time_str = evt.get("时间", "")
        if time_str and "〖%" in time_str:
            year, _ = extract_year_bce(time_str)
            if year is None:
                issues.append({
                    "event_id": evt["id"],
                    "check": "有纪年无公元年",
                    "severity": "warning",
                    "message": f"时间字段含原文纪年但无公元年转换: {time_str}",
                })
    return issues


def check_dual_date_format(parsed):
    """检查3：是否存在双日期冗余（同时有精确和推断标记）"""
    issues = []
    for evt in parsed["detail_events"]:
        time_str = evt.get("时间", "") or ""
        has_exact = bool(re.search(r"（公元前\d+年）", time_str))
        has_inferred = bool(re.search(r"\[(?:约)?公元前\d+年\]", time_str))
        if has_exact and has_inferred:
            issues.append({
                "event_id": evt["id"],
                "check": "双日期冗余",
                "severity": "warning",
                "message": f"同时有精确和推断标记: {time_str}",
            })
    return issues


def check_single_anchor_collapse(parsed):
    """检查4：单锚点塌缩 - 大量推断事件指向同一年份"""
    issues = []
    year_counts = defaultdict(list)
    for evt in parsed["detail_events"]:
        time_str = evt.get("时间", "") or ""
        year, prec = extract_year_bce(time_str)
        if year is not None and prec in ("inferred", "approx"):
            year_counts[year].append(evt["id"])

    total_events = len(parsed["detail_events"])
    for year, eids in year_counts.items():
        # 超过40%的推断事件指向同一年份 → 疑似塌缩
        if len(eids) >= 5 and len(eids) >= total_events * 0.3:
            issues.append({
                "event_id": "ALL",
                "check": "单锚点塌缩疑似",
                "severity": "warning",
                "message": f"{len(eids)}/{total_events}个事件指向{year_to_str(year)}，"
                           f"疑似被单一锚点拉偏。涉及: {', '.join(eids[:5])}...",
                "year": year,
                "count": len(eids),
                "event_ids": eids,
            })

    return issues


def check_death_event_dates(parsed, persons):
    """检查5：崩逝事件的年份是否与 person_lifespans 一致"""
    issues = []
    death_keywords = ["崩", "卒", "薨", "死", "殁", "殉", "被杀", "自杀", "崩逝"]

    for evt in parsed["detail_events"]:
        name = evt["name"]
        is_death = any(kw in name for kw in death_keywords)
        if not is_death:
            continue

        time_str = evt.get("时间", "") or ""
        year, prec = extract_year_bce(time_str)
        if year is None:
            continue

        # 查找涉及人物（v2.1格式：〖@人名〗）
        persons_str = evt.get("主要人物", "") or ""
        person_names = re.findall(r"〖@([^〖〗\n]+)〗", persons_str)

        for pname in person_names:
            if pname in persons:
                death_year = persons[pname].get("death")
                if death_year is not None and abs(year - death_year) > 50:
                    issues.append({
                        "event_id": evt["id"],
                        "check": "崩逝年份偏差",
                        "severity": "error",
                        "message": f"'{name}'标注{year_to_str(year)}，"
                                   f"但{pname}卒年为{year_to_str(death_year)}，偏差{abs(year - death_year)}年",
                        "person": pname,
                        "annotated_year": year,
                        "expected_year": death_year,
                    })

    return issues


def check_succession_dates(parsed, rulers):
    """检查6：即位/册封事件与 reign_periods 的一致性"""
    issues = []
    succession_keywords = ["即位", "践位", "称王", "称帝", "立为", "登基"]

    for evt in parsed["detail_events"]:
        name = evt["name"]
        is_succession = any(kw in name for kw in succession_keywords)
        if not is_succession:
            continue

        time_str = evt.get("时间", "") or ""
        year, prec = extract_year_bce(time_str)
        if year is None:
            continue

        # 查找涉及人物（v2.1格式：〖@人名〗）
        persons_str = evt.get("主要人物", "") or ""
        person_names = re.findall(r"〖@([^〖〗\n]+)〗", persons_str)

        for pname in person_names:
            if pname in rulers:
                start_bce = rulers[pname].get("start_bce")
                if start_bce is not None:
                    expected = -start_bce
                    if abs(year - expected) > 20:
                        issues.append({
                            "event_id": evt["id"],
                            "check": "即位年份偏差",
                            "severity": "warning",
                            "message": f"'{name}'标注{year_to_str(year)}，"
                                       f"但{pname}即位年为前{start_bce}年，偏差{abs(year - expected)}年",
                            "person": pname,
                            "annotated_year": year,
                            "expected_year": expected,
                        })

    return issues


def check_era_range(parsed):
    """检查7：事件年份是否在合理时代范围内
    策略：从概览表所有年份中推导本章实际时间范围（最早-最晚），
    只标记远超该范围的极端离群值。
    """
    issues = []

    # 收集本章所有已标注年份
    all_years = []
    for evt in parsed["detail_events"]:
        time_str = evt.get("时间", "") or ""
        year, _ = extract_year_bce(time_str)
        if year is not None:
            all_years.append(year)

    if len(all_years) < 3:
        return issues

    # 用 p10/p90 作为核心范围，容差 200 年（章节可能有前序/尾声）
    all_years_sorted = sorted(all_years)
    n = len(all_years_sorted)
    p10 = all_years_sorted[max(0, n // 10)]
    p90 = all_years_sorted[min(n - 1, n * 9 // 10)]
    tolerance = max(200, (p90 - p10) * 0.3)

    range_min = p10 - tolerance
    range_max = p90 + tolerance

    for evt in parsed["detail_events"]:
        time_str = evt.get("时间", "") or ""
        year, prec = extract_year_bce(time_str)
        if year is None:
            continue

        if year < range_min or year > range_max:
            issues.append({
                "event_id": evt["id"],
                "check": "年份超出时代范围",
                "severity": "warning",
                "message": f"'{evt['name']}'标注{year_to_str(year)}，"
                           f"离群于本章核心范围{year_to_str(int(p10))}~{year_to_str(int(p90))}",
            })

    return issues


def check_chronological_order(parsed):
    """检查8：事件年份是否大致按时间顺序排列"""
    issues = []
    years = []
    for evt in parsed["detail_events"]:
        time_str = evt.get("时间", "") or ""
        year, _ = extract_year_bce(time_str)
        years.append((evt["id"], evt["name"], year))

    # 检查严重乱序（跳跃超过100年的逆序）
    prev_year = None
    prev_id = None
    for eid, ename, year in years:
        if year is None:
            continue
        if prev_year is not None and year < prev_year - 100:
            issues.append({
                "event_id": eid,
                "check": "时间顺序异常",
                "severity": "info",
                "message": f"'{ename}'({year_to_str(year)})在'{prev_id}'({year_to_str(prev_year)})之后，"
                           f"时间回跳{abs(year - prev_year)}年",
            })
        if year is not None:
            prev_year = year
            prev_id = eid

    return issues


# ============================================================
# 审查单章
# ============================================================

def review_chapter(filepath, persons, rulers):
    """对单章执行全部自动检查，返回结果字典"""
    parsed = parse_event_index(filepath)
    chapter_id = parsed["chapter_id"]

    all_issues = []

    # 导入 CHAPTER_ERA 需要在 sys.path 中
    try:
        all_issues.extend(check_overview_detail_consistency(parsed))
        all_issues.extend(check_missing_fields(parsed))
        all_issues.extend(check_dual_date_format(parsed))
        all_issues.extend(check_single_anchor_collapse(parsed))
        all_issues.extend(check_death_event_dates(parsed, persons))
        all_issues.extend(check_succession_dates(parsed, rulers))
        all_issues.extend(check_chronological_order(parsed))
    except Exception as e:
        all_issues.append({
            "event_id": "SYSTEM",
            "check": "检查异常",
            "severity": "error",
            "message": str(e),
        })

    # 尝试 era range 检查（需要 import）
    try:
        all_issues.extend(check_era_range(parsed))
    except Exception:
        pass  # generate_review_prompts 可能不在 path 中

    # 统计
    severity_counts = Counter(i["severity"] for i in all_issues)
    check_counts = Counter(i["check"] for i in all_issues)

    report = {
        "chapter_id": chapter_id,
        "chapter_name": parsed["chapter_name"],
        "total_events": len(parsed["detail_events"]),
        "overview_events": len(parsed["overview_events"]),
        "issues": all_issues,
        "severity_counts": dict(severity_counts),
        "check_counts": dict(check_counts),
        "reviewed_at": datetime.now().isoformat(),
    }

    return report


# ============================================================
# Claude API 反思
# ============================================================

def build_reflect_prompt(chapter_id, chapter_name, event_index_text,
                         auto_issues, skill_text, accumulated_findings):
    """构建发送给 Claude 的反思提示词"""

    # 读取该章的 review 提示词（如果有）
    prompt_path = os.path.join(PROMPTS_DIR, f"review_{chapter_id}.md")
    review_prompt = ""
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            review_prompt = f.read()

    # 自动检查发现的问题摘要
    auto_summary = ""
    if auto_issues:
        auto_summary = "\n## 自动检查已发现的问题\n\n"
        auto_summary += "以下问题由自动检查脚本发现，请在反思中优先确认或修正：\n\n"
        for issue in auto_issues:
            if issue["severity"] in ("error", "warning"):
                auto_summary += f"- [{issue['severity']}] {issue['event_id']}: {issue['message']}\n"

    # 累积发现摘要
    accum_summary = ""
    if accumulated_findings:
        pattern_counts = defaultdict(int)
        for f in accumulated_findings:
            pattern_counts[f["pattern"]] += f["count"]
        accum_summary = "\n## 前序章节累积发现的高频模式\n\n"
        for pattern, count in sorted(pattern_counts.items(), key=lambda x: -x[1]):
            accum_summary += f"- **{pattern}** (累计{count}次)\n"

    system_prompt = f"""你是一位精通中国古代史的学者，正在审查《史记》事件索引中的年代标注。

你的任务：
1. 逐事件审查年代标注是否正确
2. 发现错误并给出修正建议（含推断理由）
3. 识别新的错误模式（不在SKILL已有8类中的）

## SKILL规则（必须遵守）

{skill_text}
"""

    user_prompt = f"""请审查 {chapter_id}_{chapter_name} 的事件索引年代标注。

{review_prompt}
{auto_summary}
{accum_summary}

## 待审查的事件索引

{event_index_text}

## 输出要求

请严格按以下JSON格式输出（用```json包裹），不要输出其他内容：

```json
{{
  "chapter_id": "{chapter_id}",
  "total_events": <事件总数>,
  "corrections": [
    {{
      "event_id": "NNN-NNN",
      "event_name": "事件名",
      "current_year": "当前标注年份",
      "suggested_year": "建议年份",
      "reason": "修正理由（简明扼要）",
      "confidence": "high/medium/low"
    }}
  ],
  "new_patterns": [
    {{
      "pattern_name": "模式名",
      "description": "问题描述",
      "example": "本章中的典型案例",
      "detection": "如何识别"
    }}
  ],
  "confirmed_ok": <确认无误的事件数>,
  "notes": "审查总结备注（一句话）"
}}
```

注意：
- 只列出需要修正的事件，确认无误的不需要逐个列出
- corrections 中只包含有明确依据的修正，不要猜测
- new_patterns 只包含不在SKILL已有8类错误模式中的新发现，如无则为空列表
- confidence: high=年表有载或可精确换算; medium=有较强间接证据; low=推测"""

    return system_prompt, user_prompt


def get_api_key():
    """获取 Anthropic API key，按优先级尝试：
    1. ANTHROPIC_API_KEY 环境变量
    2. ~/.anthropic/api_key 文件
    3. 项目 .env 文件
    """
    # 环境变量
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if key:
        return key

    # ~/.anthropic/api_key
    key_file = os.path.expanduser("~/.anthropic/api_key")
    if os.path.exists(key_file):
        with open(key_file, "r") as f:
            key = f.read().strip()
        if key:
            return key

    # 项目 .env
    env_file = os.path.join(BASE_DIR, ".env")
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("ANTHROPIC_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if key:
                        return key

    return ""


def call_claude_api(system_prompt, user_prompt, model="claude-sonnet-4-6"):
    """调用 Claude API 进行反思"""
    import anthropic

    api_key = get_api_key()
    if not api_key:
        raise RuntimeError(
            "未找到 API key。请设置以下任一：\n"
            "  1. export ANTHROPIC_API_KEY=sk-ant-...\n"
            "  2. 写入 ~/.anthropic/api_key\n"
            "  3. 写入项目 .env 文件: ANTHROPIC_API_KEY=sk-ant-..."
        )

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=model,
        max_tokens=8192,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    for block in message.content:
        if hasattr(block, "text"):
            return block.text
    raise ValueError("Claude API 返回中无文本内容")


def parse_reflect_response(response_text):
    """解析 Claude 返回的 JSON 反思结果"""
    # 提取 ```json ... ``` 块
    m = re.search(r"```json\s*\n(.*?)\n```", response_text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    # 尝试直接解析整个文本
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        return {"error": "无法解析返回结果", "raw": response_text[:2000]}


def reflect_chapter(chapter_id, chapter_name, filepath,
                    auto_report, skill_text, accumulated_findings,
                    dry_run=False):
    """用 Claude API 对单章进行反思审查"""
    with open(filepath, "r", encoding="utf-8") as f:
        event_index_text = f.read()

    auto_issues = auto_report.get("issues", []) if auto_report else []

    system_prompt, user_prompt = build_reflect_prompt(
        chapter_id, chapter_name, event_index_text,
        auto_issues, skill_text, accumulated_findings
    )

    if dry_run:
        # 只保存提示词，不调 API
        dry_path = os.path.join(REPORTS_DIR, f"reflect_prompt_{chapter_id}.md")
        with open(dry_path, "w", encoding="utf-8") as f:
            f.write(f"# System Prompt\n\n{system_prompt}\n\n# User Prompt\n\n{user_prompt}")
        return {"chapter_id": chapter_id, "dry_run": True, "prompt_saved": dry_path}

    print(f"  调用 Claude API 反思中...")
    try:
        response_text = call_claude_api(system_prompt, user_prompt)
    except Exception as e:
        print(f"  [API ERROR] {e}")
        return {"chapter_id": chapter_id, "error": str(e)}

    # 保存原始回复
    raw_path = os.path.join(REPORTS_DIR, f"reflect_{chapter_id}.md")
    with open(raw_path, "w", encoding="utf-8") as f:
        f.write(response_text)

    # 解析结构化结果
    result = parse_reflect_response(response_text)
    result["chapter_id"] = chapter_id
    result["chapter_name"] = chapter_name

    # 保存结构化结果
    json_path = os.path.join(REPORTS_DIR, f"reflect_{chapter_id}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result


# ============================================================
# 管线状态管理
# ============================================================

def load_state():
    """加载管线状态"""
    if os.path.exists(STATE_PATH):
        return load_json(STATE_PATH)
    return {
        "reviewed_chapters": [],
        "accumulated_findings": [],
        "new_error_patterns": [],
        "last_chapter": None,
        "started_at": datetime.now().isoformat(),
    }


def save_state(state):
    os.makedirs(REPORTS_DIR, exist_ok=True)
    state["updated_at"] = datetime.now().isoformat()
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def save_report(report):
    os.makedirs(REPORTS_DIR, exist_ok=True)
    path = os.path.join(REPORTS_DIR, f"review_{report['chapter_id']}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


# ============================================================
# 发现模式提取
# ============================================================

def extract_findings(report):
    """从审查报告中提取值得累积的发现"""
    findings = []

    # 高频检查类型 → 可能是新模式
    for check_name, count in report["check_counts"].items():
        if count >= 3:
            findings.append({
                "chapter_id": report["chapter_id"],
                "pattern": check_name,
                "count": count,
                "severity": "aggregate",
                "examples": [
                    i["event_id"] for i in report["issues"]
                    if i["check"] == check_name
                ][:5],
            })

    return findings


# ============================================================
# SKILL 更新
# ============================================================

def get_existing_skill_patterns():
    """读取 SKILL 中已有的错误模式名称"""
    if not os.path.exists(SKILL_PATH):
        return set()
    with open(SKILL_PATH, "r", encoding="utf-8") as f:
        text = f.read()
    # 提取 ### N. 模式名
    return set(re.findall(r"### \d+\.\s*(.+?)$", text, re.MULTILINE))


def append_skill_pattern(pattern_name, description, example, detection):
    """向 SKILL 文件追加新错误模式"""
    with open(SKILL_PATH, "r", encoding="utf-8") as f:
        text = f.read()

    # 找到最后一个错误模式编号
    nums = [int(x) for x in re.findall(r"### (\d+)\.", text)]
    next_num = max(nums) + 1 if nums else 1

    new_section = f"""

### {next_num}. {pattern_name}

**问题**: {description}

**典型案例**: {example}

**识别方法**: {detection}
"""

    # 插入到常见错误模式部分的末尾
    # 找 "## 审查检查清单" 或文件末尾
    insertion_point = text.find("## 审查检查清单")
    if insertion_point == -1:
        text += new_section
    else:
        text = text[:insertion_point] + new_section + "\n" + text[insertion_point:]

    with open(SKILL_PATH, "w", encoding="utf-8") as f:
        f.write(text)

    return next_num


# ============================================================
# 提示词更新
# ============================================================

def update_prompt_with_findings(chapter_id, findings):
    """在下一章的 review 提示词中追加累积发现"""
    prompt_path = os.path.join(PROMPTS_DIR, f"review_{chapter_id}.md")
    if not os.path.exists(prompt_path):
        return

    with open(prompt_path, "r", encoding="utf-8") as f:
        text = f.read()

    # 如果已经有累积发现节，先移除
    marker_start = "<!-- PIPELINE_FINDINGS_START -->"
    marker_end = "<!-- PIPELINE_FINDINGS_END -->"
    if marker_start in text:
        pre = text[:text.index(marker_start)]
        post = text[text.index(marker_end) + len(marker_end):]
        text = pre + post

    if not findings:
        return

    # 构建累积发现节
    findings_text = f"\n{marker_start}\n"
    findings_text += "## 前序章节累积发现\n\n"
    findings_text += "以下是审查前序章节时发现的高频问题，请重点关注：\n\n"

    # 按模式汇总
    pattern_summary = defaultdict(list)
    for f in findings:
        pattern_summary[f["pattern"]].append(f["chapter_id"])

    for pattern, chapters in sorted(pattern_summary.items(), key=lambda x: -len(x[1])):
        findings_text += f"- **{pattern}**：在 {', '.join(chapters)} 中出现\n"

    findings_text += f"\n{marker_end}\n"

    # 追加到注意事项之前
    insertion = text.find("## 注意事项")
    if insertion == -1:
        text += findings_text
    else:
        text = text[:insertion] + findings_text + "\n" + text[insertion:]

    with open(prompt_path, "w", encoding="utf-8") as f:
        f.write(text)


# ============================================================
# 汇总报告
# ============================================================

def generate_summary(state):
    """生成全局汇总报告"""
    lines = [
        "# 事件索引年代审查汇总报告",
        "",
        f"生成时间：{datetime.now().isoformat()}",
        f"已审查章节：{len(state['reviewed_chapters'])}/130",
        "",
        "## 各章问题统计",
        "",
        "| 章节 | 事件数 | error | warning | info |",
        "|------|--------|-------|---------|------|",
    ]

    total_events = 0
    total_errors = 0
    total_warnings = 0
    chapter_details = []

    for cid in sorted(state["reviewed_chapters"]):
        rpath = os.path.join(REPORTS_DIR, f"review_{cid}.json")
        if not os.path.exists(rpath):
            continue
        report = load_json(rpath)
        n_events = report.get("total_events", 0)
        sc = report.get("severity_counts", {})
        n_err = sc.get("error", 0)
        n_warn = sc.get("warning", 0)
        n_info = sc.get("info", 0)
        total_events += n_events
        total_errors += n_err
        total_warnings += n_warn

        name = report.get("chapter_name", "")
        lines.append(f"| {cid}_{name} | {n_events} | {n_err} | {n_warn} | {n_info} |")

        if n_err > 0 or n_warn >= 3:
            chapter_details.append((cid, name, report))

    lines.extend([
        "",
        f"**总计**: {total_events}个事件，{total_errors}个错误，{total_warnings}个警告",
        "",
    ])

    # 高频问题模式
    all_checks = Counter()
    for cid in state["reviewed_chapters"]:
        rpath = os.path.join(REPORTS_DIR, f"review_{cid}.json")
        if not os.path.exists(rpath):
            continue
        report = load_json(rpath)
        for check, count in report.get("check_counts", {}).items():
            all_checks[check] += count

    if all_checks:
        lines.extend([
            "## 全局高频问题",
            "",
            "| 问题类型 | 出现次数 |",
            "|----------|----------|",
        ])
        for check, count in all_checks.most_common(20):
            lines.append(f"| {check} | {count} |")
        lines.append("")

    # 需要人工审查的章节
    if chapter_details:
        lines.extend([
            "## 需要人工深入审查的章节",
            "",
        ])
        for cid, name, report in chapter_details:
            n_err = report.get("severity_counts", {}).get("error", 0)
            n_warn = report.get("severity_counts", {}).get("warning", 0)
            lines.append(f"### {cid}_{name} ({n_err}错误/{n_warn}警告)")
            lines.append("")
            for issue in report.get("issues", []):
                if issue["severity"] in ("error", "warning"):
                    lines.append(f"- [{issue['severity']}] {issue['event_id']}: {issue['message']}")
            lines.append("")

    # 累积发现
    if state.get("accumulated_findings"):
        lines.extend([
            "## 累积发现的模式",
            "",
        ])
        pattern_agg = defaultdict(lambda: {"count": 0, "chapters": []})
        for f in state["accumulated_findings"]:
            key = f["pattern"]
            pattern_agg[key]["count"] += f["count"]
            pattern_agg[key]["chapters"].append(f["chapter_id"])

        for pattern, info in sorted(pattern_agg.items(), key=lambda x: -x[1]["count"]):
            lines.append(f"- **{pattern}** (累计{info['count']}次，出现于 {', '.join(info['chapters'])})")
        lines.append("")

    summary_path = os.path.join(REPORTS_DIR, "summary.md")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return summary_path


# ============================================================
# 主管线
# ============================================================

def get_all_chapters():
    """扫描 data 目录获取所有章节"""
    chapters = []
    for path in sorted(glob_mod.glob(os.path.join(EVENTS_DIR, "*_事件索引.md"))):
        fname = os.path.basename(path).replace("_事件索引.md", "")
        parts = fname.split("_", 1)
        if len(parts) == 2:
            chapters.append((parts[0], parts[1], path))
    return chapters


def generate_agent_prompt(chapter_id):
    """生成单章的 Agent 反思提示词，输出到 stdout。
    用于 Claude Code Agent 调用：
        prompt=$(python run_review_pipeline.py --prompt 109)
    """
    chapters = get_all_chapters()
    chapter_map = {cid: (cname, fpath) for cid, cname, fpath in chapters}

    if chapter_id not in chapter_map:
        print(f"章节 {chapter_id} 不存在", file=sys.stderr)
        return

    chapter_name, filepath = chapter_map[chapter_id]

    with open(filepath, "r", encoding="utf-8") as f:
        event_index_text = f.read()

    # 加载 SKILL
    skill_text = ""
    if os.path.exists(SKILL_PATH):
        with open(SKILL_PATH, "r", encoding="utf-8") as f:
            skill_text = f.read()

    # 加载自动检查结果（如果有）
    auto_issues = []
    auto_report_path = os.path.join(REPORTS_DIR, f"review_{chapter_id}.json")
    if os.path.exists(auto_report_path):
        auto_report = load_json(auto_report_path)
        auto_issues = auto_report.get("issues", [])

    # 加载累积发现
    state = load_state()
    accumulated = state.get("accumulated_findings", [])

    system_prompt, user_prompt = build_reflect_prompt(
        chapter_id, chapter_name, event_index_text,
        auto_issues, skill_text, accumulated
    )

    # 合并为一个完整提示
    full_prompt = f"{system_prompt}\n\n---\n\n{user_prompt}"

    # 保存到 prompts/review_NNN.md
    os.makedirs(PROMPTS_DIR, exist_ok=True)
    prompt_path = os.path.join(PROMPTS_DIR, f"review_{chapter_id}.md")
    with open(prompt_path, "w", encoding="utf-8") as f:
        f.write(full_prompt)
    print(f"提示词已保存: {prompt_path}", file=sys.stderr)

    print(full_prompt)


def ingest_reflect_result(chapter_id, json_path):
    """导入 Agent 的反思结果 JSON，更新状态、SKILL、提示词。

    用法：python run_review_pipeline.py --ingest 109 path/to/result.json
    """
    with open(json_path, "r", encoding="utf-8") as f:
        result = json.load(f)

    state = load_state()

    corrections = result.get("corrections", [])
    new_patterns = result.get("new_patterns", [])
    n_ok = result.get("confirmed_ok", 0)

    print(f"导入 {chapter_id} 反思结果:")
    print(f"  修正建议: {len(corrections)}处")
    print(f"  确认无误: {n_ok}处")
    print(f"  新模式: {len(new_patterns)}个")

    # 新模式 → 追加到 SKILL
    existing_patterns = get_existing_skill_patterns()
    for np in new_patterns:
        pname = np.get("pattern_name", "")
        if pname and pname not in existing_patterns:
            num = append_skill_pattern(
                pname,
                np.get("description", ""),
                np.get("example", ""),
                np.get("detection", ""),
            )
            print(f"  [SKILL更新] 新增错误模式#{num}: {pname}")
            state["new_error_patterns"].append({
                "chapter_id": chapter_id,
                "pattern": pname,
            })

    # 累积 corrections
    if corrections:
        state["accumulated_findings"].append({
            "chapter_id": chapter_id,
            "pattern": "Claude反思修正",
            "count": len(corrections),
            "examples": [c["event_id"] for c in corrections[:5]],
        })

    # 标记已反思
    if chapter_id not in state.get("reflected_chapters", []):
        if "reflected_chapters" not in state:
            state["reflected_chapters"] = []
        state["reflected_chapters"].append(chapter_id)

    save_state(state)

    # 保存结构化结果
    os.makedirs(REPORTS_DIR, exist_ok=True)
    out_path = os.path.join(REPORTS_DIR, f"reflect_{chapter_id}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 更新下一章提示词
    chapters = get_all_chapters()
    for i, (cid, _, _) in enumerate(chapters):
        if cid == chapter_id and i + 1 < len(chapters):
            next_cid = chapters[i + 1][0]
            update_prompt_with_findings(next_cid, state["accumulated_findings"])
            print(f"  已更新 {next_cid} 的提示词")
            break

    print(f"  结果已保存: {out_path}")


def parse_args(args):
    """解析命令行参数"""
    flags = {a for a in args if a.startswith("--")}
    positional = [a for a in args if not a.startswith("--")]

    reflect = "--reflect" in flags
    resume = "--resume" in flags
    report_only = "--report" in flags
    dry_run = "--dry" in flags
    prompt_mode = "--prompt" in flags
    ingest_mode = "--ingest" in flags

    target_ids = None
    if positional:
        target_ids = set()
        for arg in positional:
            if "-" in arg and arg[0].isdigit():
                start, end = arg.split("-", 1)
                for i in range(int(start), int(end) + 1):
                    target_ids.add(f"{i:03d}")
            elif arg[0].isdigit():
                target_ids.add(arg.zfill(3))
            # else: could be a file path for --ingest

    # For --ingest, also capture file path
    ingest_file = None
    if ingest_mode:
        for arg in positional:
            if not arg[0].isdigit():
                ingest_file = arg
                break

    return target_ids, reflect, resume, report_only, dry_run, prompt_mode, ingest_mode, ingest_file


def run_pipeline(target_ids=None, reflect=False, resume=False, dry_run=False):
    """运行审查管线

    reflect=False: 只跑自动检查（快速，无API调用）
    reflect=True:  自动检查 + Claude API 反思（慢，每章一次API调用）
    dry_run=True:  生成反思提示词但不调API（用于检查提示词质量）
    """
    # 加载状态
    state = load_state() if resume else {
        "reviewed_chapters": [],
        "reflected_chapters": [],
        "accumulated_findings": [],
        "new_error_patterns": [],
        "last_chapter": None,
        "started_at": datetime.now().isoformat(),
    }
    if "reflected_chapters" not in state:
        state["reflected_chapters"] = []

    # 加载参考数据
    persons = load_person_lifespans()
    rulers = load_reign_periods()

    # 加载 SKILL（供反思使用）
    skill_text = ""
    if reflect and os.path.exists(SKILL_PATH):
        with open(SKILL_PATH, "r", encoding="utf-8") as f:
            skill_text = f.read()

    # 确保 generate_review_prompts 可以被 import
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)

    # 获取所有章节
    chapters = get_all_chapters()
    reviewed_set = set(state["reviewed_chapters"]) if resume else set()
    reflected_set = set(state["reflected_chapters"]) if resume else set()

    os.makedirs(REPORTS_DIR, exist_ok=True)
    count = 0
    total_corrections = 0
    total_new_patterns = 0

    for chapter_id, chapter_name, filepath in chapters:
        if target_ids is not None and chapter_id not in target_ids:
            continue
        if resume and not reflect and chapter_id in reviewed_set:
            continue
        if resume and reflect and chapter_id in reflected_set:
            continue

        print(f"\n{'='*60}")
        print(f"审查 {chapter_id}_{chapter_name}" + (" [反思模式]" if reflect else ""))
        print(f"{'='*60}")

        # 第一步：自动检查
        report = review_chapter(filepath, persons, rulers)
        save_report(report)

        sc = report["severity_counts"]
        print(f"  事件数: {report['total_events']}")
        print(f"  自动检查: {sc.get('error', 0)}错误, {sc.get('warning', 0)}警告, {sc.get('info', 0)}提示")

        for issue in report["issues"]:
            if issue["severity"] == "error":
                print(f"  [ERROR] {issue['event_id']}: {issue['message']}")

        # 第二步：Claude 反思（如果开启）
        if reflect:
            reflect_result = reflect_chapter(
                chapter_id, chapter_name, filepath,
                report, skill_text, state["accumulated_findings"],
                dry_run=dry_run,
            )

            if not dry_run and "error" not in reflect_result:
                corrections = reflect_result.get("corrections", [])
                new_patterns = reflect_result.get("new_patterns", [])
                n_ok = reflect_result.get("confirmed_ok", 0)

                print(f"  Claude反思: {len(corrections)}处修正建议, "
                      f"{n_ok}处确认无误, {len(new_patterns)}个新模式")
                total_corrections += len(corrections)
                total_new_patterns += len(new_patterns)

                # 高置信度修正摘要
                for c in corrections:
                    conf = c.get("confidence", "?")
                    print(f"    [{conf}] {c.get('event_id')}: "
                          f"{c.get('current_year')} → {c.get('suggested_year')} "
                          f"({c.get('reason', '')[:50]})")

                # 新模式 → 考虑追加到 SKILL
                existing_patterns = get_existing_skill_patterns()
                for np in new_patterns:
                    pname = np.get("pattern_name", "")
                    if pname and pname not in existing_patterns:
                        print(f"    [新模式] {pname}: {np.get('description', '')[:60]}")
                        append_skill_pattern(
                            pname,
                            np.get("description", ""),
                            np.get("example", ""),
                            np.get("detection", ""),
                        )
                        state["new_error_patterns"].append({
                            "chapter_id": chapter_id,
                            "pattern": pname,
                        })
                        # 重新加载更新后的 SKILL
                        with open(SKILL_PATH, "r", encoding="utf-8") as f:
                            skill_text = f.read()

                # 将 corrections 也作为 findings 累积
                if corrections:
                    state["accumulated_findings"].append({
                        "chapter_id": chapter_id,
                        "pattern": "Claude反思修正",
                        "count": len(corrections),
                        "examples": [c["event_id"] for c in corrections[:5]],
                    })

                if chapter_id not in state["reflected_chapters"]:
                    state["reflected_chapters"].append(chapter_id)

            elif dry_run:
                print(f"  [dry-run] 提示词已保存")

            # API 调用间隔，避免速率限制
            if not dry_run:
                time.sleep(2)

        # 提取自动检查发现
        findings = extract_findings(report)
        state["accumulated_findings"].extend(findings)

        # 更新下一章的提示词
        next_idx = None
        for i, (cid, _, _) in enumerate(chapters):
            if cid == chapter_id and i + 1 < len(chapters):
                next_idx = i + 1
                break
        if next_idx is not None:
            next_cid = chapters[next_idx][0]
            update_prompt_with_findings(next_cid, state["accumulated_findings"])

        # 更新状态
        if chapter_id not in state["reviewed_chapters"]:
            state["reviewed_chapters"].append(chapter_id)
        state["last_chapter"] = chapter_id
        save_state(state)
        count += 1

    # 生成汇总
    summary_path = generate_summary(state)
    print(f"\n{'='*60}")
    print(f"审查完成: {count}章")
    if reflect:
        print(f"  修正建议: {total_corrections}处")
        print(f"  新错误模式: {total_new_patterns}个")
    print(f"汇总报告: {summary_path}")
    print(f"管线状态: {STATE_PATH}")

    return state


def main():
    target_ids, reflect, resume, report_only, dry_run, prompt_mode, ingest_mode, ingest_file = parse_args(sys.argv[1:])

    if report_only:
        state = load_state()
        summary_path = generate_summary(state)
        print(f"汇总报告已生成: {summary_path}")
        return

    if prompt_mode:
        # --prompt 109 → 输出单章反思提示词到 stdout
        if not target_ids or len(target_ids) != 1:
            print("--prompt 需要指定一个章节编号，如: --prompt 109", file=sys.stderr)
            sys.exit(1)
        chapter_id = list(target_ids)[0]
        generate_agent_prompt(chapter_id)
        return

    if ingest_mode:
        # --ingest 109 path/to/result.json → 导入反思结果
        if not target_ids or len(target_ids) != 1:
            print("--ingest 需要指定一个章节编号，如: --ingest 109 result.json", file=sys.stderr)
            sys.exit(1)
        if not ingest_file:
            print("--ingest 需要指定结果文件路径", file=sys.stderr)
            sys.exit(1)
        chapter_id = list(target_ids)[0]
        ingest_reflect_result(chapter_id, ingest_file)
        return

    run_pipeline(target_ids=target_ids, reflect=reflect,
                 resume=resume, dry_run=dry_run)


if __name__ == "__main__":
    main()
