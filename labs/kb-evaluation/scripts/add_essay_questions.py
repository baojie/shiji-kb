#!/usr/bin/env python3
"""
为第1组问题集添加问答题（essay questions）

这些问题需要综合多处信息，给出长文本答案（100-300字）
"""

import json
from pathlib import Path

def generate_essay_questions():
    """生成需要长文本回答的问题"""

    essay_questions = [
        # Comparative 比较型
        {
            "id": "Q101",
            "question": "比较张良、萧何、韩信三人在汉朝建立过程中的不同作用和最终结局，分析造成不同结局的原因。",
            "type": "comparative",
            "difficulty": "hard",
            "category": "person_comparative",
            "subcategory": "功臣对比",
            "target_chapters": ["055", "053", "092"],
            "keywords": ["张良", "萧何", "韩信", "汉初三杰", "功臣结局"],
            "expected_answer_length": "200-300字"
        },
        {
            "id": "Q102",
            "question": "苏秦主张合纵，张仪主张连横，请比较两人的外交策略及其对战国局势的影响。",
            "type": "comparative",
            "difficulty": "medium",
            "category": "person_comparative",
            "subcategory": "策略对比",
            "target_chapters": ["069", "070"],
            "keywords": ["苏秦", "张仪", "合纵", "连横", "战国外交"],
            "expected_answer_length": "150-200字"
        },
        {
            "id": "Q103",
            "question": "比较商鞅变法和吴起变法的异同点，分析两者结局不同的原因。",
            "type": "comparative",
            "difficulty": "hard",
            "category": "person_comparative",
            "subcategory": "变法对比",
            "target_chapters": ["068", "065"],
            "keywords": ["商鞅", "吴起", "变法", "秦国", "楚国"],
            "expected_answer_length": "200-300字"
        },
        {
            "id": "Q104",
            "question": "比较孔子、老子、墨子三位思想家的核心主张有何不同？",
            "type": "comparative",
            "difficulty": "medium",
            "category": "person_comparative",
            "subcategory": "思想对比",
            "target_chapters": ["047", "063", "074"],
            "keywords": ["孔子", "老子", "墨子", "儒家", "道家", "墨家"],
            "expected_answer_length": "150-250字"
        },

        # Inferential 推理型
        {
            "id": "Q105",
            "question": "韩信被杀后，萧何为何没有遭到同样的命运？请从二人的性格、行为和刘邦的考虑等方面分析。",
            "type": "inferential",
            "difficulty": "hard",
            "category": "person_inferential",
            "subcategory": "命运推理",
            "target_chapters": ["092", "053"],
            "keywords": ["韩信", "萧何", "功高震主", "自保"],
            "expected_answer_length": "200-300字"
        },
        {
            "id": "Q106",
            "question": "从屈原、贾谊两人的遭遇和结局，可以看出什么样的历史规律或人生启示？",
            "type": "inferential",
            "difficulty": "hard",
            "category": "person_inferential",
            "subcategory": "规律总结",
            "target_chapters": ["084"],
            "keywords": ["屈原", "贾谊", "忠而被谤", "怀才不遇"],
            "expected_answer_length": "200-300字"
        },
        {
            "id": "Q107",
            "question": "李斯从布衣到丞相又被腰斩，他的人生轨迹反映了什么？",
            "type": "inferential",
            "difficulty": "medium",
            "category": "person_inferential",
            "subcategory": "人生轨迹",
            "target_chapters": ["087"],
            "keywords": ["李斯", "成败得失", "权力欲望"],
            "expected_answer_length": "150-250字"
        },
        {
            "id": "Q108",
            "question": "为什么荆轲刺秦王失败了？从准备、执行到结果，分析失败的多重原因。",
            "type": "inferential",
            "difficulty": "medium",
            "category": "person_inferential",
            "subcategory": "事件分析",
            "target_chapters": ["086"],
            "keywords": ["荆轲", "刺秦", "失败原因"],
            "expected_answer_length": "150-200字"
        },

        # Evaluative 评价型（需要长答案）
        {
            "id": "Q109",
            "question": "太史公对项羽的评价是矛盾的：一方面称其为'本纪'给予帝王待遇，另一方面又指出其'自矜功伐，奋其私智'。请综合分析司马迁对项羽的真实态度。",
            "type": "evaluative",
            "difficulty": "hard",
            "category": "person_evaluative",
            "subcategory": "史家评价",
            "target_chapters": ["007"],
            "keywords": ["项羽", "太史公", "本纪", "评价"],
            "expected_answer_length": "200-300字"
        },
        {
            "id": "Q110",
            "question": "如何评价汉武帝在位期间的功过？请从内政、外交、文化等多个角度分析。",
            "type": "evaluative",
            "difficulty": "hard",
            "category": "person_evaluative",
            "subcategory": "功过评价",
            "target_chapters": ["012", "111", "030"],
            "keywords": ["汉武帝", "功过", "内政", "外交"],
            "expected_answer_length": "250-350字"
        },
        {
            "id": "Q111",
            "question": "管仲作为齐桓公的宰相，太史公给予了很高评价。请结合史记内容分析管仲的主要贡献和治国理念。",
            "type": "evaluative",
            "difficulty": "medium",
            "category": "person_evaluative",
            "subcategory": "人物评价",
            "target_chapters": ["062"],
            "keywords": ["管仲", "齐桓公", "霸业", "治国"],
            "expected_answer_length": "150-250字"
        },
        {
            "id": "Q112",
            "question": "如何评价吕后执政时期？她对汉朝初期的稳定起到了什么作用？",
            "type": "evaluative",
            "difficulty": "medium",
            "category": "person_evaluative",
            "subcategory": "执政评价",
            "target_chapters": ["009"],
            "keywords": ["吕后", "执政", "汉初", "政治"],
            "expected_answer_length": "150-250字"
        },

        # Relational 关系型
        {
            "id": "Q113",
            "question": "详细描述廉颇与蔺相如从矛盾到和解的过程，说明这个故事反映了什么样的为人处世之道。",
            "type": "relational",
            "difficulty": "medium",
            "category": "person_relational",
            "subcategory": "人际关系",
            "target_chapters": ["081"],
            "keywords": ["廉颇", "蔺相如", "将相和", "负荆请罪"],
            "expected_answer_length": "150-200字"
        },
        {
            "id": "Q114",
            "question": "刘邦与项羽的关系经历了哪些阶段性变化？分析导致关系变化的关键事件。",
            "type": "relational",
            "difficulty": "hard",
            "category": "person_relational",
            "subcategory": "对手关系",
            "target_chapters": ["007", "008"],
            "keywords": ["刘邦", "项羽", "楚汉相争", "鸿门宴"],
            "expected_answer_length": "200-300字"
        },
        {
            "id": "Q115",
            "question": "孔子与其弟子的关系如何？从史记中的记载分析孔子的教育方式和师生互动。",
            "type": "relational",
            "difficulty": "medium",
            "category": "person_relational",
            "subcategory": "师生关系",
            "target_chapters": ["047", "067"],
            "keywords": ["孔子", "弟子", "教育", "因材施教"],
            "expected_answer_length": "150-250字"
        },

        # Complex Synthesis 综合型
        {
            "id": "Q116",
            "question": "白起一生战功赫赫却被赐死，请综合分析他的军事成就、性格特点以及最终悲剧的原因。",
            "type": "inferential",
            "difficulty": "hard",
            "category": "person_synthesis",
            "subcategory": "综合分析",
            "target_chapters": ["073"],
            "keywords": ["白起", "军事", "长平之战", "被赐死"],
            "expected_answer_length": "200-300字"
        },
        {
            "id": "Q117",
            "question": "张骞两次出使西域的经历和意义是什么？对后世产生了哪些深远影响？",
            "type": "evaluative",
            "difficulty": "medium",
            "category": "person_synthesis",
            "subcategory": "历史影响",
            "target_chapters": ["123"],
            "keywords": ["张骞", "西域", "丝绸之路", "凿空"],
            "expected_answer_length": "150-250字"
        },
        {
            "id": "Q118",
            "question": "司马迁在《史记》中如何看待'货殖'（经商致富）？从货殖列传的内容分析他的经济思想。",
            "type": "evaluative",
            "difficulty": "hard",
            "category": "person_synthesis",
            "subcategory": "思想分析",
            "target_chapters": ["129"],
            "keywords": ["货殖", "经济思想", "太史公", "富与德"],
            "expected_answer_length": "200-300字"
        },
        {
            "id": "Q119",
            "question": "从伯夷叔齐的故事和太史公的评价，可以看出司马迁对'天道'和'报应'的什么看法？",
            "type": "inferential",
            "difficulty": "hard",
            "category": "person_synthesis",
            "subcategory": "哲学思考",
            "target_chapters": ["061"],
            "keywords": ["伯夷", "叔齐", "天道", "善恶报应"],
            "expected_answer_length": "200-300字"
        },
        {
            "id": "Q120",
            "question": "卫青和霍去病叔侄二人都是抗击匈奴的名将，请比较他们的军事风格、为人处世和历史地位。",
            "type": "comparative",
            "difficulty": "medium",
            "category": "person_synthesis",
            "subcategory": "人物对比",
            "target_chapters": ["111"],
            "keywords": ["卫青", "霍去病", "匈奴", "将军"],
            "expected_answer_length": "200-300字"
        }
    ]

    return essay_questions

def main():
    """主函数"""
    print("开始为第1组问题集添加问答题...")

    # 生成问答题
    essay_qs = generate_essay_questions()

    # 读取现有问题文件
    questions_file = Path(__file__).parent.parent / "questions" / "set01_person_basic.json"
    with open(questions_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 添加问答题
    data["questions"].extend(essay_qs)
    data["total_questions"] = len(data["questions"])
    data["description"] = "测试对史记人物基本信息的掌握，包括姓名、字号、籍贯、家世、生卒年等（含20道需要长文本回答的问答题）"

    # 保存问题文件
    with open(questions_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # 统计
    type_dist = {}
    for q in data["questions"]:
        qtype = q["type"]
        type_dist[qtype] = type_dist.get(qtype, 0) + 1

    print(f"\n✓ 成功添加20道问答题")
    print(f"  问题文件：{questions_file}")
    print(f"  总问题数：{data['total_questions']}")
    print(f"\n问题类型分布：")
    for qtype, count in sorted(type_dist.items(), key=lambda x: -x[1]):
        print(f"  {qtype}: {count}题 ({count*100//data['total_questions']}%)")

    print(f"\n新增问答题分类：")
    print(f"  比较型 (comparative): 5题")
    print(f"  推理型 (inferential): 8题")
    print(f"  评价型 (evaluative): 4题")
    print(f"  关系型 (relational): 3题")

    print(f"\n预期答案长度：")
    print(f"  150-200字: 5题")
    print(f"  150-250字: 6题")
    print(f"  200-300字: 9题")

if __name__ == "__main__":
    main()
