#!/usr/bin/env python3
"""
深度分析《五帝本纪》段落之间的语义关系

不仅限于时序关系，还包括：
- 因果关系 (causal): A导致B
- 并列关系 (parallel): A和B并列描述
- 总分关系 (hierarchy): A总结B，或B详述A
- 引用关系 (reference): A引用B的内容
- 对比关系 (contrast): A和B形成对比
- 补充关系 (elaboration): B补充说明A
- 转折关系 (transition): 从A转向B
"""

import json
from pathlib import Path
from typing import List, Dict, Any

def analyze_relations(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    深度分析段落之间的多维关系
    """
    paragraphs = data['paragraphs']
    relations = []

    # 建立段落索引
    para_dict = {p['anchor']: p for p in paragraphs}

    # 遍历所有段落对
    for i in range(len(paragraphs)):
        current = paragraphs[i]
        current_anchor = current['anchor']
        current_section = current['section']
        current_subsection = current.get('subsection', '')
        current_text = current['full_text']
        current_summary = current['summary']

        # 检查与后续段落的关系
        # 扩大检查范围以捕获更多关系
        max_check = min(i + 10, len(paragraphs))
        for j in range(i + 1, max_check):
            next_para = paragraphs[j]
            next_anchor = next_para['anchor']
            next_section = next_para['section']
            next_subsection = next_para.get('subsection', '')
            next_text = next_para['full_text']
            next_summary = next_para['summary']

            # 1. 时序-承接关系（同小节内相邻段落）
            if (current_section == next_section and
                current_subsection == next_subsection and
                current_subsection and  # 确保有subsection
                j == i + 1):
                relations.append({
                    'source': current_anchor,
                    'target': next_anchor,
                    'type': 'temporal',
                    'subtype': 'succession',
                    'description': '同一小节内的紧密承接'
                })

            # 2. 时序-顺序关系（同章节内跨小节或相邻无小节段落）
            elif (current_section == next_section and
                  current_section):  # 确保在同一章节内
                # 如果是相邻段落，关系更紧密
                if j == i + 1:
                    relations.append({
                        'source': current_anchor,
                        'target': next_anchor,
                        'type': 'temporal',
                        'subtype': 'succession',
                        'description': '同一章节内的紧密承接'
                    })
                elif j <= i + 3:  # 检查接下来3个段落
                    relations.append({
                        'source': current_anchor,
                        'target': next_anchor,
                        'type': 'temporal',
                        'subtype': 'sequential',
                        'description': '同一大节内的时间顺序'
                    })

            # 3. 因果关系（关键词识别）
            causal_keywords = ['於是', '故', '因', '以', '遂', '乃']
            if any(kw in next_summary[:20] for kw in causal_keywords):
                # 检查是否与前一段有因果联系
                if any(word in current_summary[-50:] for word in ['作乱', '衰', '欲', '不善', '无功']):
                    relations.append({
                        'source': current_anchor,
                        'target': next_anchor,
                        'type': 'causal',
                        'subtype': 'consequence',
                        'description': '前因后果关系'
                    })

            # 4. 世系继承关系
            if ('崩' in current_summary and ('立' in next_summary or '代' in next_summary)):
                relations.append({
                    'source': current_anchor,
                    'target': next_anchor,
                    'type': 'genealogy',
                    'subtype': 'succession',
                    'description': '帝王世系继承'
                })

            # 5. 总分关系（列举式段落）
            if ('-' in next_text or '其一' in next_text or '其二' in next_text):
                # 下一段是列举，当前段是总起
                relations.append({
                    'source': current_anchor,
                    'target': next_anchor,
                    'type': 'hierarchy',
                    'subtype': 'general_to_specific',
                    'description': '总述到分述'
                })

    # 特殊关系：最后两章与前文的关系
    # [26] 五帝世系总结 - 对全篇的总结
    if '26' in para_dict:
        relations.append({
            'source': '1',
            'target': '26',
            'type': 'hierarchy',
            'subtype': 'summary',
            'description': '世系总结对应黄帝章节开始'
        })
        relations.append({
            'source': '5',
            'target': '26',
            'type': 'hierarchy',
            'subtype': 'summary',
            'description': '世系总结包含颛顼'
        })
        relations.append({
            'source': '7',
            'target': '26',
            'type': 'hierarchy',
            'subtype': 'summary',
            'description': '世系总结包含帝喾'
        })
        relations.append({
            'source': '10',
            'target': '26',
            'type': 'hierarchy',
            'subtype': 'summary',
            'description': '世系总结包含帝尧'
        })
        relations.append({
            'source': '14',
            'target': '26',
            'type': 'hierarchy',
            'subtype': 'summary',
            'description': '世系总结包含帝舜'
        })

    # [27] 太史公曰 - 对全篇的评论
    if '27' in para_dict:
        relations.append({
            'source': '1',
            'target': '27',
            'type': 'meta',
            'subtype': 'commentary',
            'description': '史家评论全篇（黄帝）'
        })
        relations.append({
            'source': '10',
            'target': '27',
            'type': 'meta',
            'subtype': 'commentary',
            'description': '史家评论全篇（尧）'
        })
        relations.append({
            'source': '14',
            'target': '27',
            'type': 'meta',
            'subtype': 'commentary',
            'description': '史家评论全篇（舜）'
        })

    # 特殊：[21-22] 举贤任能章节的对比关系
    # [21] 八恺八元（贤） vs [22] 四凶（不才）
    relations.append({
        'source': '21',
        'target': '22.6',
        'type': 'contrast',
        'subtype': 'good_vs_evil',
        'description': '贤才与不才的对比'
    })

    # [20] 舜的孝行与德行 vs [18-19] 家人的迫害
    relations.append({
        'source': '18',
        'target': '20',
        'type': 'contrast',
        'subtype': 'adversity_vs_virtue',
        'description': '逆境与美德的对比'
    })

    # 特殊：[4.2] -> [5] 世系传承关系
    relations.append({
        'source': '4.2',
        'target': '5',
        'type': 'genealogy',
        'subtype': 'succession',
        'description': '黄帝传位给颛顼'
    })

    # [6] -> [7] 世系传承
    relations.append({
        'source': '6',
        'target': '7',
        'type': 'genealogy',
        'subtype': 'succession',
        'description': '颛顼传位给帝喾'
    })

    # [9] -> [10] 世系传承
    relations.append({
        'source': '9',
        'target': '10',
        'type': 'genealogy',
        'subtype': 'succession',
        'description': '帝喾传位给帝尧'
    })

    # [13.8] -> [14] 尧传位给舜
    relations.append({
        'source': '13.8',
        'target': '14',
        'type': 'genealogy',
        'subtype': 'abdication',
        'description': '禅让：尧传位给舜'
    })

    # 引用关系：[11] 历法描述引用《尚书》
    relations.append({
        'source': '11',
        'target': '11.5',
        'type': 'elaboration',
        'subtype': 'detail',
        'description': '历法总述与详细说明'
    })

    # 并列关系：五帝各自的描述
    relations.append({
        'source': '1',
        'target': '5',
        'type': 'parallel',
        'subtype': 'emperors',
        'description': '五帝并列：黄帝与颛顼'
    })
    relations.append({
        'source': '5',
        'target': '7',
        'type': 'parallel',
        'subtype': 'emperors',
        'description': '五帝并列：颛顼与帝喾'
    })
    relations.append({
        'source': '7',
        'target': '10',
        'type': 'parallel',
        'subtype': 'emperors',
        'description': '五帝并列：帝喾与帝尧'
    })
    relations.append({
        'source': '10',
        'target': '14',
        'type': 'parallel',
        'subtype': 'emperors',
        'description': '五帝并列：帝尧与帝舜'
    })

    return relations

def main():
    # 读取原始数据
    root = Path(__file__).resolve().parent.parent
    data_file = root / 'kg/structure/data/paragraph_relations_001.json'
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 分析关系
    para_count = len(data['paragraphs'])
    print(f'正在深度分析{para_count}个段落之间的关系...')
    new_relations = analyze_relations(data)

    # 去重
    seen = set()
    unique_relations = []
    for rel in new_relations:
        key = (rel['source'], rel['target'], rel['type'])
        if key not in seen:
            seen.add(key)
            unique_relations.append(rel)

    # 统计
    relation_types = {}
    for rel in unique_relations:
        rel_type = rel['type']
        if rel_type not in relation_types:
            relation_types[rel_type] = []
        relation_types[rel_type].append(rel)

    print(f'\n✅ 识别出 {len(unique_relations)} 个关系')
    print('\n关系类型统计:')
    for rel_type, rels in sorted(relation_types.items()):
        print(f'  {rel_type}: {len(rels)}个')
        # 显示该类型的前3个示例
        for rel in rels[:3]:
            print(f'    [{rel["source"]}] -> [{rel["target"]}]: {rel.get("description", "")}')

    # 保存增强版数据
    data['relations'] = unique_relations

    output_file = root / 'kg/structure/data/paragraph_relations_001_enhanced.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f'\n✅ 增强版数据已保存到: {output_file}')
    print(f'\n关系总数: {len(unique_relations)}')
    print(f'原版关系数: 40 (仅时序)')
    print(f'新增关系数: {len(unique_relations) - 40}')

if __name__ == '__main__':
    main()
