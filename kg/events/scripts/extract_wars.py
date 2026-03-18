#!/usr/bin/env python3
"""
战争事件提取与融合脚本

功能：
1. 从130章事件索引中提取所有战争类型事件
2. 基于规则和LLM辅助归并同一战争的多个来源
3. 融合多源信息，处理矛盾记载
4. 生成战争事件索引和JSON数据

用法：
    # 完整流程
    python extract_wars.py --all

    # 分阶段执行
    python extract_wars.py --stage=identify     # 初步识别
    python extract_wars.py --stage=merge_auto   # 自动归并
    python extract_wars.py --stage=merge_llm    # LLM辅助归并
    python extract_wars.py --stage=consolidate  # 信息融合
    python extract_wars.py --stage=enrich       # 细节补充
    python extract_wars.py --stage=export       # 导出文件
"""

import os
import re
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
EVENTS_DIR = PROJECT_ROOT / "kg" / "events" / "data"
OUTPUT_DIR = PROJECT_ROOT / "kg" / "events" / "data"
CHAPTER_MD_DIR = PROJECT_ROOT / "chapter_md"

# 临时文件目录
TMP_DIR = PROJECT_ROOT / "kg" / "events" / "tmp"
TMP_DIR.mkdir(exist_ok=True)


class WarEvent:
    """战争事件数据结构"""

    def __init__(self, event_id: str, name: str, event_type: str = "战争"):
        self.event_id = event_id
        self.name = name
        self.event_type = event_type
        self.sources = [event_id]  # 来源事件ID列表

        # 基本信息
        self.time_start: Optional[str] = None
        self.time_end: Optional[str] = None
        self.time_certainty: str = "unknown"  # precise/approximate/legendary
        self.time_original: List[str] = []  # 原始时间表达

        self.locations: List[str] = []
        self.duration: Optional[str] = None

        # 交战方
        self.attacker_state: List[str] = []
        self.attacker_commanders: List[str] = []
        self.attacker_advisors: List[str] = []

        self.defender_state: List[str] = []
        self.defender_commanders: List[str] = []
        self.defender_ruler: List[str] = []

        # 战争信息
        self.trigger: List[str] = []  # 战争起因
        self.process: List[str] = []  # 战争经过
        self.outcome: List[str] = []  # 战争结果
        self.casualties: List[Dict[str, str]] = []  # 伤亡（多源）
        self.scale: List[str] = []  # 规模
        self.strategy: List[str] = []  # 战术

        # 元数据
        self.chapters: List[str] = []  # 来源章节（如"001_五帝本纪"）
        self.descriptions: List[Dict[str, str]] = []  # 各来源的描述
        self.conflicts: List[Dict[str, Any]] = []  # 矛盾记录

        # 关联引用（待实现）
        self.related_events: List[str] = []  # 关联的其他事件ID（如"005-034"）
        self.related_facts: List[str] = []  # 关联的事实ID（如"FACT-015-234"，待SKILL_05d实现）
        self.supporting_evidence: List[Dict[str, str]] = []  # 支持证据
        # 格式: [{"type": "event"|"fact", "id": "005-135", "field": "casualties", "text": "..."}]

    def add_source(self, event_id: str, chapter: str, description: str):
        """添加来源"""
        if event_id not in self.sources:
            self.sources.append(event_id)
        if chapter not in self.chapters:
            self.chapters.append(chapter)
        self.descriptions.append({
            "source": event_id,
            "chapter": chapter,
            "text": description
        })

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "war_id": self.get_war_id(),
            "war_name": self.name,
            "war_type": self.event_type,
            "time": {
                "start": self.time_start,
                "end": self.time_end,
                "certainty": self.time_certainty,
                "original": self.time_original
            },
            "location": self.locations,
            "duration": self.duration,
            "belligerents": {
                "attacker": {
                    "state": self.attacker_state,
                    "commanders": self.attacker_commanders,
                    "advisors": self.attacker_advisors
                },
                "defender": {
                    "state": self.defender_state,
                    "commanders": self.defender_commanders,
                    "ruler": self.defender_ruler
                }
            },
            "trigger": self.trigger,
            "process": self.process,
            "outcome": self.outcome,
            "casualties": self.casualties,
            "scale": self.scale,
            "strategy": self.strategy,
            "sources": self.sources,
            "chapters": self.chapters,
            "descriptions": self.descriptions,
            "conflicts": self.conflicts,
            "related_events": self.related_events,
            "related_facts": self.related_facts,
            "supporting_evidence": self.supporting_evidence
        }

    def get_war_id(self) -> str:
        """生成战争ID（基于第一个来源事件ID）"""
        first_event = self.sources[0]
        chapter_num = first_event.split("-")[0]
        return f"WAR-{chapter_num}-{first_event.split('-')[1]}"


class WarExtractor:
    """战争事件提取器"""

    def __init__(self):
        self.raw_wars: List[Dict[str, Any]] = []  # 原始战争事件
        self.merged_wars: List[WarEvent] = []  # 归并后的战争

    def stage_identify(self):
        """阶段1：初步识别所有战争事件"""
        print("=" * 60)
        print("阶段1：初步识别战争事件")
        print("=" * 60)

        war_count = 0

        # 遍历所有事件索引文件
        for event_file in sorted(EVENTS_DIR.glob("*_事件索引.md")):
            print(f"\n处理文件: {event_file.name}")

            with open(event_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 提取概览表格中的战争事件
            wars = self._extract_wars_from_overview(content, event_file.stem)
            war_count += len(wars)
            self.raw_wars.extend(wars)

            print(f"  发现 {len(wars)} 个战争事件")

        # 保存原始数据
        output_file = TMP_DIR / "wars_raw.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.raw_wars, f, ensure_ascii=False, indent=2)

        print(f"\n总计识别 {war_count} 个战争事件")
        print(f"原始数据已保存至: {output_file}")

    def _extract_wars_from_overview(self, content: str, file_stem: str) -> List[Dict[str, Any]]:
        """从事件索引文件的概览表格中提取战争事件"""
        wars = []

        # 查找概览表格部分
        overview_match = re.search(
            r'## 事件列表概览\s*\n\s*\|[^\n]+\|\s*\n\s*\|[-:| ]+\|\s*\n((?:\|[^\n]+\|\s*\n)+)',
            content
        )

        if not overview_match:
            return wars

        table_content = overview_match.group(1)

        # 解析表格行
        for line in table_content.strip().split('\n'):
            if not line.startswith('|'):
                continue

            cells = [cell.strip() for cell in line.split('|')[1:-1]]

            if len(cells) < 7:
                continue

            event_id, name, event_type, time, location, persons, dynasty = cells[:7]

            # 只提取战争类型
            if event_type == "战争":
                wars.append({
                    "event_id": event_id,
                    "name": name,
                    "time": time,
                    "location": location,
                    "persons": persons,
                    "dynasty": dynasty,
                    "chapter": file_stem,
                    "description": ""  # 稍后从详细记录中提取
                })

        # 补充详细描述和原文
        for war in wars:
            description = self._extract_event_description(content, war["event_id"])
            war["description"] = description

            # 同时提取带标注的原文引用
            fields = self._extract_detailed_fields(content, war["event_id"])
            war["original_text"] = fields.get("original_text", "")

        return wars

    def _extract_event_description(self, content: str, event_id: str) -> str:
        """提取事件的详细描述"""
        # 查找详细事件记录部分
        pattern = rf'### {re.escape(event_id)} [^\n]+\n(.*?)(?=\n### |\n## |\Z)'
        match = re.search(pattern, content, re.DOTALL)

        if match:
            detail_section = match.group(1)
            # 提取事件描述字段
            desc_match = re.search(r'- \*\*事件描述\*\*:\s*(.+?)(?=\n- \*\*|\Z)', detail_section, re.DOTALL)
            if desc_match:
                return desc_match.group(1).strip()

        return ""

    def _extract_detailed_fields(self, content: str, event_id: str) -> Dict[str, Any]:
        """提取事件的详细字段（原文引用等）"""
        pattern = rf'### {re.escape(event_id)} [^\n]+\n(.*?)(?=\n### |\n## |\Z)'
        match = re.search(pattern, content, re.DOTALL)

        fields = {}
        if match:
            detail_section = match.group(1)

            # 提取各个字段
            field_patterns = {
                'description': r'- \*\*事件描述\*\*:\s*(.+?)(?=\n- \*\*|\Z)',
                'original_text': r'- \*\*原文引用\*\*:\s*["""](.+?)["""](?=\n- \*\*|\Z)',
                'location_detail': r'- \*\*地点\*\*:\s*(.+?)(?=\n|\Z)',
                'persons_detail': r'- \*\*主要人物\*\*:\s*(.+?)(?=\n|\Z)',
            }

            for field_name, pattern in field_patterns.items():
                field_match = re.search(pattern, detail_section, re.DOTALL)
                if field_match:
                    fields[field_name] = field_match.group(1).strip()

        return fields

    def stage_merge_auto(self):
        """阶段2：基于规则的自动归并"""
        print("\n" + "=" * 60)
        print("阶段2：自动归并（基于规则）")
        print("=" * 60)

        # 加载原始数据
        if not self.raw_wars:
            input_file = TMP_DIR / "wars_raw.json"
            with open(input_file, 'r', encoding='utf-8') as f:
                self.raw_wars = json.load(f)

        # 按名称分组
        name_groups = defaultdict(list)
        for war in self.raw_wars:
            # 清理战争名称（去除标注符号）
            clean_name = self._clean_war_name(war["name"])
            name_groups[clean_name].append(war)

        # 归并同名战争
        for name, wars in name_groups.items():
            if len(wars) == 1:
                # 单一来源，直接创建WarEvent
                w = wars[0]
                war_event = WarEvent(w["event_id"], name)
                war_event.add_source(w["event_id"], w["chapter"], w["description"])
                self._populate_war_fields(war_event, w)
                self.merged_wars.append(war_event)
            else:
                # 多来源，归并
                print(f"\n归并战争: {name} (共{len(wars)}个来源)")
                war_event = WarEvent(wars[0]["event_id"], name)
                for w in wars:
                    print(f"  - {w['chapter']}: {w['event_id']}")
                    war_event.add_source(w["event_id"], w["chapter"], w["description"])
                    self._populate_war_fields(war_event, w)

                self.merged_wars.append(war_event)

        print(f"\n归并完成: {len(self.raw_wars)} 个原始事件 → {len(self.merged_wars)} 个战争")

        # 保存归并结果
        output_file = TMP_DIR / "wars_merged_auto.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump([w.to_dict() for w in self.merged_wars], f, ensure_ascii=False, indent=2)

        print(f"归并数据已保存至: {output_file}")

    def _clean_war_name(self, name: str) -> str:
        """清理战争名称，去除标注符号"""
        # 去除实体标注符号
        name = re.sub(r'[〖〗@=&;%+~]', '', name)
        return name.strip()

    def _populate_war_fields(self, war_event: WarEvent, war_data: Dict[str, Any]):
        """从原始数据填充战争事件字段"""
        # 时间
        time_str = war_data.get("time", "").strip()
        if time_str and time_str != "-":
            war_event.time_original.append(time_str)
            # TODO: 解析具体年份

        # 地点
        location = war_data.get("location", "").strip()
        if location and location != "-":
            clean_loc = self._clean_war_name(location)
            if clean_loc not in war_event.locations:
                war_event.locations.append(clean_loc)

        # 人物（简单分割，实际需要更复杂的解析）
        persons = war_data.get("persons", "").strip()
        if persons and persons != "-":
            # TODO: 区分进攻方/防守方
            pass

    def stage_merge_llm(self):
        """阶段3：LLM辅助归并模糊情况"""
        print("\n" + "=" * 60)
        print("阶段3：LLM辅助归并（模糊情况）")
        print("=" * 60)
        print("此功能待实现：需要调用LLM API判断相似但不同名的战争是否为同一战争")
        # TODO: 实现LLM辅助归并

    def stage_consolidate(self):
        """阶段4：信息融合 - 解析战争关键信息"""
        print("\n" + "=" * 60)
        print("阶段4：信息融合 - 解析战争关键信息")
        print("=" * 60)

        # 加载归并数据（如果未加载）
        if not self.merged_wars:
            input_file = TMP_DIR / "wars_merged_auto.json"
            with open(input_file, 'r', encoding='utf-8') as f:
                wars_data = json.load(f)
                self.merged_wars = [self._dict_to_war_event(w) for w in wars_data]

        # 为每个战争解析关键信息
        for war in self.merged_wars:
            print(f"\n解析: {war.name}")
            for desc in war.descriptions:
                self._parse_war_info(war, desc['text'], desc['source'])

        # 保存增强后的数据
        output_file = TMP_DIR / "wars_enriched.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump([w.to_dict() for w in self.merged_wars], f, ensure_ascii=False, indent=2)

        print(f"\n信息融合完成，增强数据已保存至: {output_file}")

    def _parse_war_info(self, war: WarEvent, description: str, source: str):
        """从描述中解析战争信息

        Args:
            war: 战争事件对象
            description: 事件描述（不带标注）
            source: 来源事件ID（如"005-135"）

        Note:
            当前使用规则提取，未来可以：
            1. 从原文引用（带标注）中提取，精度更高
            2. 关联到事实ID（FACT-XXX-XXX），待SKILL_05d完成后实现
        """

        # 尝试从war的descriptions中找到原文
        original_text = ""
        for desc in war.descriptions:
            if desc['source'] == source:
                # 需要重新读取原文获取带标注版本
                # 这里暂时使用description
                original_text = description
                break

        # 1. 提取交战双方（国家/势力）
        # 匹配模式：X攻Y、X伐Y、X vs Y、X灭Y等
        belligerents_patterns = [
            r'〖?&([^&〗]+)&〗?(?:攻|伐|击|围|灭|败)〖?&([^&〗]+)&〗?',  # 秦攻赵
            r'〖?&([^&〗]+)&〗?(?:与|和)〖?&([^&〗]+)&〗?(?:战|交战)',  # 秦与赵战
            r'〖?@([^@〗]+)@〗?(?:攻|伐|击|围|灭|败)〖?&([^&〗]+)&〗?',  # 项羽攻秦
            # 非标注版本的模式（因为description中标注已被清除）
            r'(秦|赵|齐|楚|燕|魏|韩|吴|越|晋|周|汉|匈奴)(?:攻|伐|击|围|灭|败)(秦|赵|齐|楚|燕|魏|韩|吴|越|晋|周|汉|匈奴)',
        ]

        for pattern in belligerents_patterns:
            matches = re.findall(pattern, description)
            for match in matches:
                attacker, defender = match
                if attacker not in war.attacker_state:
                    war.attacker_state.append(attacker)
                if defender not in war.defender_state:
                    war.defender_state.append(defender)

        # 2. 提取人物
        # 先尝试从标注中提取
        persons_with_mark = re.findall(r'〖?@([^@〗]+)@〗?', description)
        # 也尝试从常见名字提取（如"白起"、"赵括"等）
        common_names = re.findall(r'([白赵廉王李陈项张刘韩魏][\u4e00-\u9fff]{1,2})(?:率|将|攻|伐|击|守|降|死|败|胜)', description)

        all_persons = list(set(persons_with_mark + common_names))
        for person in all_persons:
            if person not in war.attacker_commanders:
                war.attacker_commanders.append(person)

        # 3. 提取伤亡信息
        casualty_patterns = [
            r'(?:坑杀|斩首|杀|死|亡|降)(?:.*?)([十百千万亿兆\d]+(?:余)?[人万])',  # 坑杀四十万
            r'([十百千万亿兆\d]+(?:余)?[人万])(?:被)?(?:坑杀|斩|死|降)',  # 四十万被坑杀
        ]

        for pattern in casualty_patterns:
            matches = re.findall(pattern, description)
            for match in matches:
                casualty_text = match if isinstance(match, str) else match[0]
                # 记录伤亡（带来源）
                casualty_entry = {
                    "source": source,
                    "text": casualty_text,
                    "context": description[:100] + "..."
                }
                # 检查是否已存在相同记录
                if not any(c['text'] == casualty_text for c in war.casualties):
                    war.casualties.append(casualty_entry)

        # 4. 提取战果/结果
        outcome_patterns = [
            r'(〖?@?[^@〗]+@?〗?)(?:胜|大胜|败|惨败|降|逃|走|死)',  # X胜、Y败
            r'(?:破|拔|取|克|围|灭)(?:〖?=?[^=〗]+\=?〗?)',  # 破赵、灭楚
        ]

        for pattern in outcome_patterns:
            matches = re.findall(pattern, description)
            for match in matches:
                outcome_text = match if isinstance(match, str) else match[0]
                if outcome_text not in war.outcome:
                    war.outcome.append(outcome_text)

        # 5. 提取地点（已在war.locations中，这里可以补充）
        locations = re.findall(r'〖?=([^=〗]+)=〗?', description)
        for loc in locations:
            if loc not in war.locations:
                war.locations.append(loc)

    def stage_enrich(self):
        """阶段5：细节补充"""
        print("\n" + "=" * 60)
        print("阶段5：细节补充")
        print("=" * 60)
        print("此功能待实现：从原文中补充战术、转折点等细节")
        # TODO: 实现细节补充

    def stage_export(self):
        """阶段6：导出文件"""
        print("\n" + "=" * 60)
        print("阶段6：导出文件")
        print("=" * 60)

        # 加载增强数据（优先）或归并数据
        if not self.merged_wars:
            # 尝试加载增强数据
            enriched_file = TMP_DIR / "wars_enriched.json"
            if enriched_file.exists():
                input_file = enriched_file
                print("使用增强数据（含解析的战争信息）")
            else:
                input_file = TMP_DIR / "wars_merged_auto.json"
                print("使用归并数据（不含详细解析）")

            with open(input_file, 'r', encoding='utf-8') as f:
                wars_data = json.load(f)
                self.merged_wars = [self._dict_to_war_event(w) for w in wars_data]

        # 导出JSON
        json_file = OUTPUT_DIR / "wars.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump([w.to_dict() for w in self.merged_wars], f, ensure_ascii=False, indent=2)
        print(f"JSON数据已导出至: {json_file}")

        # 导出Markdown索引
        md_file = OUTPUT_DIR / "战争事件索引.md"
        self._export_markdown_index(md_file)
        print(f"Markdown索引已导出至: {md_file}")

    def _dict_to_war_event(self, data: Dict[str, Any]) -> WarEvent:
        """从字典重建WarEvent对象"""
        war = WarEvent(data["sources"][0], data["war_name"])
        war.sources = data["sources"]
        war.chapters = data["chapters"]
        war.descriptions = data["descriptions"]
        war.time_start = data["time"]["start"]
        war.time_end = data["time"]["end"]
        war.time_certainty = data["time"]["certainty"]
        war.time_original = data["time"]["original"]
        war.locations = data["location"]
        war.duration = data["duration"]

        # 交战双方
        war.attacker_state = data["belligerents"]["attacker"]["state"]
        war.attacker_commanders = data["belligerents"]["attacker"]["commanders"]
        war.attacker_advisors = data["belligerents"]["attacker"]["advisors"]
        war.defender_state = data["belligerents"]["defender"]["state"]
        war.defender_commanders = data["belligerents"]["defender"]["commanders"]
        war.defender_ruler = data["belligerents"]["defender"]["ruler"]

        # 战争信息
        war.trigger = data.get("trigger", [])
        war.process = data.get("process", [])
        war.outcome = data.get("outcome", [])
        war.casualties = data.get("casualties", [])
        war.scale = data.get("scale", [])
        war.strategy = data.get("strategy", [])
        war.conflicts = data.get("conflicts", [])

        # 关联引用
        war.related_events = data.get("related_events", [])
        war.related_facts = data.get("related_facts", [])
        war.supporting_evidence = data.get("supporting_evidence", [])

        return war

    def _export_markdown_index(self, output_file: Path):
        """导出Markdown格式的战争索引"""
        lines = [
            "# 史记战争事件索引",
            "",
            "## 统计概览",
            "",
            f"- **总战争数**: {len(self.merged_wars)}",
            f"- **多源战争**: {sum(1 for w in self.merged_wars if len(w.sources) > 1)}",
            f"- **单源战争**: {sum(1 for w in self.merged_wars if len(w.sources) == 1)}",
            "",
            "---",
            "",
            "## 战争列表",
            "",
            "| 战争ID | 战争名称 | 时间 | 地点 | 来源数 | 来源章节 |",
            "|--------|---------|------|------|--------|---------|",
        ]

        for war in self.merged_wars:
            war_id = war.get_war_id()
            time_display = war.time_original[0] if war.time_original else "-"
            location_display = ", ".join(war.locations) if war.locations else "-"
            source_count = len(war.sources)
            chapters_display = ", ".join(war.chapters[:3])  # 最多显示3个
            if len(war.chapters) > 3:
                chapters_display += "..."

            lines.append(
                f"| {war_id} | {war.name} | {time_display} | {location_display} | "
                f"{source_count} | {chapters_display} |"
            )

        lines.extend([
            "",
            "---",
            "",
            "## 详细战争记录",
            "",
        ])

        for war in self.merged_wars:
            lines.extend(self._format_war_detail(war))

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

    def _format_war_detail(self, war: WarEvent) -> List[str]:
        """格式化战争详细信息"""
        lines = [
            f"### {war.get_war_id()} {war.name}",
            "",
            "#### 基本信息",
            f"- **战争ID**: {war.get_war_id()}",
            f"- **战争名称**: {war.name}",
            f"- **来源数**: {len(war.sources)}",
            "",
        ]

        if war.time_original:
            lines.append(f"- **时间**: {', '.join(war.time_original)}")

        if war.locations:
            lines.append(f"- **地点**: {', '.join(war.locations)}")

        lines.append("")

        # 交战双方
        if war.attacker_state or war.defender_state:
            lines.extend([
                "#### 交战双方",
                "",
            ])

            if war.attacker_state:
                lines.append(f"- **进攻方**: {', '.join(war.attacker_state)}")
                if war.attacker_commanders:
                    lines.append(f"  - **将领**: {', '.join(war.attacker_commanders[:5])}")  # 最多显示5个

            if war.defender_state:
                lines.append(f"- **防守方**: {', '.join(war.defender_state)}")
                if war.defender_commanders:
                    lines.append(f"  - **将领**: {', '.join(war.defender_commanders[:5])}")

            lines.append("")

        # 伤亡情况
        if war.casualties:
            lines.extend([
                "#### 伤亡情况",
                "",
            ])
            for casualty in war.casualties:
                lines.append(f"- **{casualty['source']}**: {casualty['text']}")
            lines.append("")

        # 战争结果
        if war.outcome:
            lines.extend([
                "#### 战争结果",
                "",
            ])
            for outcome in war.outcome[:10]:  # 最多显示10个
                lines.append(f"- {outcome}")
            lines.append("")

        # 来源章节
        lines.extend([
            "#### 来源章节",
            "",
        ])

        for desc in war.descriptions:
            lines.append(f"- **{desc['chapter']}** ({desc['source']}): {desc['text'][:100]}...")

        lines.extend([
            "",
            "---",
            "",
        ])

        return lines


def main():
    parser = argparse.ArgumentParser(description="战争事件提取与融合")
    parser.add_argument(
        '--stage',
        choices=['identify', 'merge_auto', 'merge_llm', 'consolidate', 'enrich', 'export'],
        help='执行特定阶段'
    )
    parser.add_argument('--all', action='store_true', help='执行完整流程')

    args = parser.parse_args()

    extractor = WarExtractor()

    if args.all:
        # 执行完整流程
        extractor.stage_identify()
        extractor.stage_merge_auto()
        extractor.stage_merge_llm()
        extractor.stage_consolidate()
        extractor.stage_enrich()
        extractor.stage_export()
    elif args.stage:
        # 执行特定阶段
        stage_method = getattr(extractor, f'stage_{args.stage}')
        stage_method()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
