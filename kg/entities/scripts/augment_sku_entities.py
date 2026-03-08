#!/usr/bin/env python3
"""
用现有实体识别数据对 Factual SKU 进行实体增补。

读取 entity_index.json 中的实体库，匹配每个 factual SKU 的内容文本，
为每个 SKU 生成 entities.json，并更新 skus_index.json。
"""

import json
import os
import re
from collections import defaultdict

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ENTITY_INDEX = os.path.join(_PROJECT_ROOT, "kg", "entities", "data", "entity_index.json")
ALIAS_FILE = os.path.join(_PROJECT_ROOT, "kg", "entities", "data", "entity_aliases.json")
SKUS_INDEX = os.path.join(_PROJECT_ROOT, "ontology", "skus", "skus_index.json")
FACTUAL_DIR = os.path.join(_PROJECT_ROOT, "ontology", "skus", "factual")

# 实体类型的中文名，用于输出
ENTITY_TYPE_NAMES = {
    "person": "人名",
    "place": "地名",
    "official": "官职",
    "time": "时间",
    "dynasty": "朝代",
    "institution": "制度",
    "tribe": "族群",
    "artifact": "器物",
    "astronomy": "天文",
    "mythical": "神话",
    "flora-fauna": "动植物",
}


def build_entity_lookup(entity_index):
    """
    构建实体查找表：{实体名/别名: [(类型, 规范名), ...]}
    过滤掉单字实体以避免误匹配。
    """
    lookup = defaultdict(list)

    for etype, entities in entity_index.items():
        for canonical, info in entities.items():
            # 添加规范名
            if len(canonical) >= 2:
                lookup[canonical].append((etype, canonical))
            # 添加别名
            for alias in info.get("aliases", []):
                if len(alias) >= 2 and alias != canonical:
                    lookup[alias].append((etype, canonical))

    return dict(lookup)


def extract_text(sku_dir):
    """从 SKU 目录读取内容文本。优先 content.md，其次 content.json。"""
    md_path = os.path.join(sku_dir, "content.md")
    json_path = os.path.join(sku_dir, "content.json")

    if os.path.exists(md_path):
        with open(md_path, "r", encoding="utf-8") as f:
            return f.read()
    elif os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 将 JSON 序列化为文本用于匹配
            return json.dumps(data, ensure_ascii=False, indent=2)
    return ""


def match_entities(text, lookup):
    """
    在文本中匹配实体名称。
    优先匹配长名称，返回 {类型: {规范名: 出现次数}}。
    """
    if not text:
        return {}

    # 按长度降序排列实体名，优先匹配长的
    names_by_length = sorted(lookup.keys(), key=len, reverse=True)

    # 记录匹配结果
    results = defaultdict(lambda: defaultdict(int))
    # 记录已匹配的文本位置，避免子串重复计数
    matched_positions = set()

    for name in names_by_length:
        # 查找所有出现位置
        start = 0
        while True:
            pos = text.find(name, start)
            if pos == -1:
                break

            # 检查该位置是否已被更长的匹配覆盖
            name_positions = set(range(pos, pos + len(name)))
            if not name_positions & matched_positions:
                # 记录匹配
                for etype, canonical in lookup[name]:
                    results[etype][canonical] += 1
                matched_positions |= name_positions

            start = pos + 1

    return dict(results)


def get_top_entities(results, top_n=5):
    """从匹配结果中提取出现频次最高的实体（去重）。"""
    # 合并同一规范名在不同类型下的出现次数
    merged = defaultdict(int)
    for etype, entities in results.items():
        for canonical, count in entities.items():
            merged[canonical] += count

    # 按出现次数降序排列，去重
    sorted_entities = sorted(merged.items(), key=lambda x: x[1], reverse=True)

    return [name for name, count in sorted_entities[:top_n]]


def process_sku(sku_dir, sku_id, source_chunk, lookup):
    """处理单个 SKU，返回实体数据。"""
    text = extract_text(sku_dir)
    if not text:
        return None

    results = match_entities(text, lookup)
    if not results:
        return None

    # 构建输出
    entities = {}
    total_count = 0
    for etype in sorted(results.keys()):
        names = sorted(results[etype].keys())
        entities[etype] = names
        total_count += len(names)

    top = get_top_entities(results)

    return {
        "sku_id": sku_id,
        "source_chunk": source_chunk,
        "entities": entities,
        "entity_count": total_count,
        "top_entities": top,
    }


def main():
    # 加载实体库
    print("加载实体库...")
    with open(ENTITY_INDEX, "r", encoding="utf-8") as f:
        entity_index = json.load(f)

    lookup = build_entity_lookup(entity_index)
    print(f"  实体查找表：{len(lookup)} 个名称（含别名，≥2字）")

    # 加载 SKU 索引
    with open(SKUS_INDEX, "r", encoding="utf-8") as f:
        skus_data = json.load(f)

    factual_skus = [s for s in skus_data["skus"] if s["classification"] == "factual"]
    print(f"  Factual SKU：{len(factual_skus)} 个")

    # 处理每个 SKU
    processed = 0
    skipped = 0
    total_entities = 0

    # 建立 sku_id → index 的映射，用于更新 skus_index
    sku_id_to_idx = {s["sku_id"]: i for i, s in enumerate(skus_data["skus"])}

    for sku_info in factual_skus:
        sku_id = sku_info["sku_id"]
        source_chunk = sku_info.get("source_chunk", "")
        sku_dir = os.path.join(FACTUAL_DIR, sku_id)

        if not os.path.isdir(sku_dir):
            skipped += 1
            continue

        result = process_sku(sku_dir, sku_id, source_chunk, lookup)

        if result:
            # 写入 entities.json
            out_path = os.path.join(sku_dir, "entities.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            # 更新 skus_index
            idx = sku_id_to_idx.get(sku_id)
            if idx is not None:
                skus_data["skus"][idx]["entity_count"] = result["entity_count"]
                skus_data["skus"][idx]["top_entities"] = result["top_entities"]

            processed += 1
            total_entities += result["entity_count"]
        else:
            skipped += 1

    # 保存更新后的 skus_index
    with open(SKUS_INDEX, "w", encoding="utf-8") as f:
        json.dump(skus_data, f, ensure_ascii=False, indent=2)

    # 输出统计
    print(f"\n完成！")
    print(f"  已处理：{processed} 个 SKU")
    print(f"  跳过（无内容/无匹配）：{skipped} 个")
    print(f"  总实体标注数：{total_entities}")
    if processed > 0:
        print(f"  平均每个 SKU：{total_entities / processed:.1f} 个实体")


if __name__ == "__main__":
    main()
