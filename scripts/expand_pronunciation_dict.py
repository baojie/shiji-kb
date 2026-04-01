#!/usr/bin/env python3
"""
根据多音字分析报告扩展特殊读音词表

基于《史记》多音字读音分布分析，补充高频但尚未覆盖的词条
每个词条都会在史记原文中验证实际出现次数
"""

import json
import re
from pathlib import Path
from collections import Counter

# 文件路径
SHIJI_TEXT = Path("archive/史记.简体.txt")
DICT_FILE = Path("docs/data/special-pronunciation.json")

# 新增词条（基于分析报告的建议）
NEW_ENTRIES = [
    # ===== 1. "间"相关（离间、反间、间谍） =====
    {
        "text": "离间",
        "pinyin": ["lí", "jiàn"],
        "context": "动词",
        "note": "挑拨离间，'间'读jiàn（去声）"
    },
    {
        "text": "反间",
        "pinyin": ["fǎn", "jiàn"],
        "context": "名词",
        "note": "反间计，用敌方间谍反为我用，'间'读jiàn（去声）"
    },
    {
        "text": "间谍",
        "pinyin": ["jiàn", "dié"],
        "context": "名词",
        "note": "从事秘密侦察的人，'间'读jiàn（去声）"
    },

    # ===== 2. "朝"相关（朝廷、朝见、朝聘） =====
    {
        "text": "朝廷",
        "pinyin": ["cháo", "tíng"],
        "context": "名词",
        "note": "君主接见群臣议政之处，'朝'读cháo（阳平）"
    },
    {
        "text": "朝见",
        "pinyin": ["cháo", "jiàn"],
        "context": "动词",
        "note": "诸侯朝见天子，'朝'读cháo（阳平）"
    },
    {
        "text": "朝聘",
        "pinyin": ["cháo", "pìn"],
        "context": "动词",
        "note": "诸侯朝聘天子，'朝'读cháo（阳平）"
    },

    # ===== 3. "更"相关（更名、更始、更定） =====
    {
        "text": "更名",
        "pinyin": ["gēng", "míng"],
        "context": "动词",
        "note": "改换名字，'更'读gēng（平声）"
    },
    {
        "text": "更始",
        "pinyin": ["gēng", "shǐ"],
        "context": "动词",
        "note": "重新开始，'更'读gēng（平声）"
    },
    {
        "text": "更定",
        "pinyin": ["gēng", "dìng"],
        "context": "动词",
        "note": "改定、重新制定，'更'读gēng（平声）"
    },

    # ===== 4. "好"相关（好学、好色、好战） =====
    {
        "text": "好学",
        "pinyin": ["hào", "xué"],
        "context": "动词",
        "note": "喜爱学习，'好'读hào（去声）"
    },
    {
        "text": "好色",
        "pinyin": ["hào", "sè"],
        "context": "动词",
        "note": "喜爱美色，'好'读hào（去声）"
    },
    {
        "text": "好战",
        "pinyin": ["hào", "zhàn"],
        "context": "动词",
        "note": "喜爱战争，'好'读hào（去声）"
    },

    # ===== 5. "率"相关（率众、统率、率领） =====
    {
        "text": "率众",
        "pinyin": ["shuài", "zhòng"],
        "context": "动词",
        "note": "率领众人，'率'读shuài（去声）"
    },
    {
        "text": "统率",
        "pinyin": ["tǒng", "shuài"],
        "context": "动词",
        "note": "统领率领，'率'读shuài（去声）"
    },
    {
        "text": "率领",
        "pinyin": ["shuài", "lǐng"],
        "context": "动词",
        "note": "带领、引领，'率'读shuài（去声）"
    },

    # ===== 6. "中"相关（射中、中计、中伏） =====
    {
        "text": "射中",
        "pinyin": ["shè", "zhòng"],
        "context": "动词",
        "note": "射中目标，动词，'中'读zhòng（去声）"
    },
    {
        "text": "中计",
        "pinyin": ["zhòng", "jì"],
        "context": "动词",
        "note": "中了计策，动词，'中'读zhòng（去声）"
    },
    {
        "text": "中伏",
        "pinyin": ["zhòng", "fú"],
        "context": "动词",
        "note": "中了埋伏，动词，'中'读zhòng（去声）"
    },

    # ===== 7. "都"相关（都城、都尉） =====
    {
        "text": "都城",
        "pinyin": ["dū", "chéng"],
        "context": "名词",
        "note": "国都、首都，'都'读dū（阴平）"
    },
    {
        "text": "都尉",
        "pinyin": ["dū", "wèi"],
        "context": "官职",
        "note": "汉代武官名，掌管军事，'都'读dū（阴平）"
    },

    # ===== 8. "降"相关（投降、降伏） =====
    {
        "text": "投降",
        "pinyin": ["tóu", "xiáng"],
        "context": "动词",
        "note": "归降、降服，'降'读xiáng（阳平）"
    },
    {
        "text": "降伏",
        "pinyin": ["xiáng", "fú"],
        "context": "动词",
        "note": "归顺、降服，'降'读xiáng（阳平）"
    },

    # ===== 9. "殷"相关（殷商、殷墟） =====
    {
        "text": "殷商",
        "pinyin": ["yīn", "shāng"],
        "context": "朝代名",
        "note": "商朝，因盘庚迁殷后又称殷商，'殷'读yīn（阴平）"
    },
    {
        "text": "殷墟",
        "pinyin": ["yīn", "xū"],
        "context": "地名",
        "note": "商朝都城遗址，在今河南安阳，'殷'读yīn（阴平）"
    },

    # ===== 10. "应"相关 =====
    {
        "text": "应当",
        "pinyin": ["yīng", "dāng"],
        "context": "助动词",
        "note": "应该、应当，'应'读yīng（阴平）"
    },

    # ===== 11. "当"相关 =====
    {
        "text": "适当",
        "pinyin": ["shì", "dàng"],
        "context": "形容词",
        "note": "恰当、合适，'当'读dàng（去声）"
    },

    # ===== 12. "使"相关 =====
    {
        "text": "使者",
        "pinyin": ["shǐ", "zhě"],
        "context": "名词",
        "note": "奉命出使的人，'使'读shǐ（上声）"
    },

    # ===== 13. "过"相关 =====
    {
        "text": "过国",
        "pinyin": ["guò", "guó"],
        "context": "动词",
        "note": "经过某国，'过'读guò（去声）"
    },

    # ===== 14. "与"相关 =====
    {
        "text": "参与",
        "pinyin": ["cān", "yù"],
        "context": "动词",
        "note": "参加、参与，'与'读yù（去声）"
    },

    # ===== 15. "为"相关 =====
    {
        "text": "以为",
        "pinyin": ["yǐ", "wéi"],
        "context": "动词",
        "note": "认为、以为，'为'读wéi（阳平）"
    },
    {
        "text": "因为",
        "pinyin": ["yīn", "wèi"],
        "context": "连词",
        "note": "因为、由于，'为'读wèi（去声）"
    },

    # ===== 16. "复"相关 =====
    {
        "text": "重复",
        "pinyin": ["chóng", "fù"],
        "context": "动词",
        "note": "再次重复，'复'读fù（去声）"
    },

    # ===== 17. 其他高频动词用法 =====
    {
        "text": "大说",
        "pinyin": ["dà", "yuè"],
        "context": "动词",
        "note": "大为高兴，'说'通'悦'读yuè（去声）"
    },
]


def load_shiji_text():
    """加载史记文本"""
    with open(SHIJI_TEXT, 'r', encoding='utf-8') as f:
        return f.read()


def verify_entry(text, shiji_content):
    """验证词条在史记中的出现次数"""
    count = shiji_content.count(text)
    return count


def load_existing_dict():
    """加载现有词表"""
    with open(DICT_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    print("=" * 80)
    print("扩展特殊读音词表")
    print("=" * 80)

    # 加载数据
    print("\n📖 加载数据...")
    shiji_content = load_shiji_text()
    existing_dict = load_existing_dict()
    existing_texts = {entry['text'] for entry in existing_dict['entries']}

    print(f"  史记文本：{len(shiji_content)} 字符")
    print(f"  现有词表：{len(existing_texts)} 条")

    # 验证新词条
    print("\n🔍 验证新词条在史记中的使用情况...")
    verified_entries = []
    skipped_entries = []

    for entry in NEW_ENTRIES:
        text = entry['text']

        # 检查是否已存在
        if text in existing_texts:
            print(f"  ⚠️  跳过（已存在）：{text}")
            skipped_entries.append(entry)
            continue

        # 验证出现次数
        count = verify_entry(text, shiji_content)

        if count > 0:
            print(f"  ✅ {text:12s} | 出现 {count:3d} 次 | {entry['note'][:40]}...")
            verified_entries.append(entry)
        else:
            print(f"  ❌ {text:12s} | 未出现 | {entry['note'][:40]}...")

    # 统计
    print(f"\n📊 验证结果统计")
    print(f"  新词条总数：{len(NEW_ENTRIES)}")
    print(f"  已存在：{len(skipped_entries)}")
    print(f"  验证通过：{len(verified_entries)}")
    print(f"  未通过：{len(NEW_ENTRIES) - len(skipped_entries) - len(verified_entries)}")

    if not verified_entries:
        print("\n⚠️  没有需要添加的新词条")
        return

    # 添加到词表
    print(f"\n✏️  添加 {len(verified_entries)} 个新词条到词表...")

    # 更新版本信息
    version_parts = existing_dict['version'].split('.')
    major, minor = int(version_parts[0]), int(version_parts[1])
    new_version = f"{major}.{minor + 1}"

    existing_dict['version'] = new_version
    existing_dict['lastUpdated'] = "2026-04-01"
    existing_dict['description'] = f"史记特殊读音词汇（人工整理 + 史记正义提取）- v{new_version} 新增{len(verified_entries)}条多音字常用词组"

    # 添加新词条
    existing_dict['entries'].extend(verified_entries)

    # 保存
    with open(DICT_FILE, 'w', encoding='utf-8') as f:
        json.dump(existing_dict, f, ensure_ascii=False, indent=2)

    print(f"  ✅ 已保存到：{DICT_FILE}")
    print(f"  📌 新版本：v{new_version}")
    print(f"  📊 词条总数：{len(existing_dict['entries'])}")

    # 按类别统计
    print(f"\n📋 新增词条分类统计")
    category_count = Counter(e['context'] for e in verified_entries)
    for category, count in sorted(category_count.items(), key=lambda x: x[1], reverse=True):
        print(f"  {category:10s}: {count:2d} 条")

    # 显示新增词条列表
    print(f"\n📝 新增词条列表")
    for i, entry in enumerate(verified_entries, 1):
        pinyin_str = ' '.join(entry['pinyin'])
        print(f"  {i:2d}. {entry['text']:12s} ({pinyin_str:30s}) | {entry['context']}")

    print(f"\n✅ 扩展完成！")
    print(f"\n💡 使用建议：")
    print(f"  1. 运行拼音标注工具测试新词条效果")
    print(f"  2. 检查是否还有遗漏的高频词组")
    print(f"  3. 更新相关文档说明")


if __name__ == "__main__":
    main()
