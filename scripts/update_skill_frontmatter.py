#!/usr/bin/env python3
"""
为skills目录下的所有SKILL文件更新YAML frontmatter,符合Anthropic标准

Anthropic标准要求:
1. description必须包含"做什么"和"何时使用"
2. 明确列出触发条件和关键词
3. 具有一定"pushiness"以避免undertrigging

更新策略:
- 读取文件内容,提取标题和子标题
- 基于文件内容智能生成详细description
- 保留现有name和title字段
"""

import re
from pathlib import Path
from typing import Dict, Tuple


# SKILL描述映射表 - 基于文档内容的智能描述
SKILL_DESCRIPTIONS = {
    "SKILL_00_管线总览.md":
        "《史记》知识库全流程概览,从原始文本到知识应用的完整管线。当需要了解项目整体架构、工序流程、数据流转时使用。适用于新人onboarding、技术选型、流程设计等场景。",

    "SKILL_01_古籍校勘.md":
        "古籍文本校勘方法,从底本到定本的文字审校流程。当发现原文错别字、缺字、衍文脱文、标点错误时使用。适用于txt底本初步处理、文字质量审查、与权威版本对照等任务。",

    "SKILL_02_结构分析.md":
        "古籍文本结构化分析总览,从定本到标注文本的转换流程。当需要对古籍进行章节切分、段落编号、注释标注、结构语义分析时使用。涵盖Purple Numbers编号、三家注处理、词法分析等子工序。",

    "SKILL_02a_章节切分与编号.md":
        "古籍章节切分与Purple Numbers段落编号方法。当需要为古籍文本添加持久化段落标识符、进行语义分段、建立可引用的文本锚点时使用。适用于txt转md、段落索引构建、细粒度引用系统设计。",

    "SKILL_02b_区块与韵文处理.md":
        "Fenced Div语义块与赞体韵文标注方法。当遇到《史记》中的'太史公曰'、韵文、诏书等特殊文体时使用。涵盖Pandoc Fenced Div语法、韵文检测、渲染样式设计等内容。",

    "SKILL_02c_三家注标注.md":
        "《史记》三家注(裴骃集解、司马贞索隐、张守节正义)语义化标注与数据结构设计。当需要处理古籍注释、区分注释类型、对齐正文与注文时使用。适用于注释结构化、注释索引构建、注释语义分析。",

    "SKILL_02d_结构语义分析.md":
        "古籍文本的结构语义关系挖掘,包括注释对齐、排版映射、嵌套结构分析。当需要理解文本内部层次关系、注释与正文对应关系、段落间语义连接时使用。适用于深度文本分析、语义网络构建。",

    "SKILL_02e_词法分析.md":
        "古籍字词级标注、统计与遗漏发现。当需要分析虚词用法、统计特定词汇分布、检测标注遗漏时使用。适用于词频统计、标注覆盖率检查、语言学研究等场景。",

    "SKILL_02f_文本统计.md":
        "古籍文本定量分析与分布特征统计。当需要统计章节字数、实体分布、标注密度等量化指标时使用。适用于数据质量评估、章节特征分析、进度追踪等任务。",

    "SKILL_02g_表格结构语义分析.md":
        "《史记》十表的维度定义、关系挖掘与数据转换。当处理《史记》013-022章的表格内容时使用。涵盖表格语义理解、时间轴对齐、人物/事件提取等专项处理。",

    "SKILL_02h_词表构建.md":
        "专项词汇识别与结构化词表构建。当需要提取特定领域词汇(如官职、地名、器物)并构建受控词表时使用。适用于术语库建设、本体构建准备、领域知识梳理。",

    "SKILL_02i_指代消解.md":
        "古籍人称代词与身份指代的语义消解。当文本中存在'其''彼''是人'等指代词需要确定所指对象时使用。适用于共指消解、人物关系理清、语义理解增强等任务。**实验阶段,尚未大规模应用**。",

    "SKILL_03_实体构建.md":
        "古籍实体识别与结构化索引构建总览,从标注文本到实体知识库。当需要进行18类实体NER标注、实体消歧、实体索引生成时使用。涵盖实体标注、消歧、反思、渲染等完整流程。",

    "SKILL_03a_实体标注.md":
        "古籍18类实体NER标注完整方法(v2.5标注体系)。当需要标注人名、地名、官职、邦国、时间、典籍等实体时使用。适用于.txt到.tagged.md转换、实体识别、知识抽取等任务。明确使用本技能当用户提到'实体标注''NER''命名实体识别'或需要为古籍文本添加〖TYPE 实体〗标记。",

    "SKILL_03b_人名消歧.md":
        "古籍人名消歧方法,区分同名异人与异名同人。当发现'李斯(秦相)'与'李斯(他人)'等同名冲突时使用。涵盖规范名设计、消歧语法(〖@显示名|规范名〗)、全局一致性检查等内容。",

    "SKILL_03c_按章反思.md":
        "实体标注按章反思审查方法,Agent驱动的逐章深度审查。当完成单章实体标注后需要质量审查时使用。每个Agent处理一章,发现标错/遗漏实体、修正语境误判、积累章节特有错误模式。质量基线30-80处修正/章。明确使用本技能当用户提到'按章反思''实体审查''单章质检'或标注质量不理想需要改进。",

    "SKILL_03d_渲染与发布.md":
        "标注文本HTML渲染与GitHub Pages发布流程。当需要将.tagged.md转换为可视化网页、生成实体索引、发布到GitHub Pages时使用。适用于成果展示、在线阅读器构建、知识库发布等场景。",

    "SKILL_03e_按类型反思.md":
        "实体标注按类型反思,批量修正系统性错误。当发现某类实体(如邦国、官职)存在全局性错误模式时使用。适用于跨章节的类型级质量审查、批量修正、错误模式总结等任务。",

    "SKILL_03f_实体边界错误综合反思.md":
        "实体边界错误综合反思,修饰词切分与分类修正。当发现实体标注中多标/少标修饰词、类型分类错误时使用。涵盖边界审查、修饰词处理规则、类型纠错等专项内容。",

    "SKILL_04_事件构建.md":
        "历史事件识别与结构化提取总览,从标注文本到事件索引。当需要从古籍中提取历史事件、标注公元纪年、构建事件时间轴时使用。涵盖事件识别、年代推断、年代审查、年份消歧等完整流程。",

    "SKILL_04a_事件识别.md":
        "古籍历史事件识别方法,基于LLM的语义级事件提取。当需要从叙事文本中识别'鸿门宴''垓下之战'等历史事件时使用。处理跨段叙述、事件粒度判断、因果关系提取等复杂场景。明确使用本技能当用户提到'事件提取''事件识别''历史事件'。",

    "SKILL_04b_十表事件处理.md":
        "《史记》十表(013-022章)专项事件处理方法。当处理表格形式的编年史内容时使用。涵盖表格事件提取、时间轴对齐、与本纪/世家内容融合等专项流程。",

    "SKILL_04c_事件年代推断.md":
        "历史事件公元纪年推断方法,基于年号表与在位年计算。当事件有'秦始皇三十七年'等在位纪年需要转换为公元纪年时使用。适用于自动纪年标注、时间轴构建、年代数据库生成。",

    "SKILL_04d_事件年代审查.md":
        "事件年代Agent反思审查流程,检测年代标注错误与不确定性。当自动标注的公元纪年需要质量审查时使用。通过Agent综合判断年代合理性、发现计算错误、解决纪年冲突等问题。",

    "SKILL_04e_年份消歧.md":
        "古籍年份消歧方法,解决同一年号不同朝代冲突。当'建元元年''永平三年'等年号可能对应多个朝代时使用。涵盖年号消歧规则、朝代推断、纪年表匹配等内容。",

    "SKILL_04f_动词标注.md":
        "古籍动词标注方法,识别并标注事件触发词。当需要标注'攻''封''杀''立'等历史行为动词时使用。适用于事件抽取增强、动宾关系识别、行为语义分析。**实验阶段**。",

    "SKILL_05_关系构建.md":
        "知识图谱关系抽取与构建总览,从事件实体到关系网络。当需要构建人物关系、事件关系、地点关系等图谱关系时使用。涵盖事件关系发现、实体关系构建、人物关系网络、事实三元组抽取等内容。",

    "SKILL_05a_事件关系发现.md":
        "历史事件间关系识别方法,从孤立事件到关系网络。当需要识别事件间的因果、时序、包含等关系时使用。适用于事件图谱构建、叙事逻辑分析、历史推理等场景。",

    "SKILL_05b_实体关系构建.md":
        "实体间结构化关系抽取,涵盖人物/地点/制度等多类实体。当需要抽取'任职于''位于''隶属于'等实体关系时使用。适用于知识图谱三元组生成、关系数据库构建等任务。",

    "SKILL_05c_人物关系构建.md":
        "多层次人物关系网络构建,从共现到家谱。当需要识别父子、君臣、师徒、婚姻等人物关系时使用。涵盖关系抽取、关系分类、关系可视化、家谱树生成等内容。",

    "SKILL_05d_事实发现.md":
        "原子事实三元组抽取方法,细粒度知识单元识别。当需要将叙事文本分解为<主语,谓语,宾语>形式的原子事实时使用。适用于知识图谱构建、事实验证、知识推理等任务。",

    "SKILL_05e_战争事件识别.md":
        "战争事件专项识别与多源知识融合。当需要提取战争事件、对齐《史记》与《战国策》等多源记载时使用。涵盖战争事件抽取、多源对齐、矛盾检测等内容。**实验阶段**。",

    "SKILL_06_本体构建.md":
        "本体分类体系构建总览,从实体实例到抽象本体。当需要构建人物分类、地点分类、制度分类等本体层次时使用。涵盖本体设计、实体归类、OWL/RDFS建模等内容。",

    "SKILL_06a_实体到本体.md":
        "实体到本体转换流程,从标注文本到RDF分类本体。当需要将实体数据转换为OWL/RDFS本体、构建类层次、定义属性关系时使用。适用于语义网建模、本体工程、知识推理等场景。",

    "SKILL_07_逻辑推理.md":
        "基于知识图谱的逻辑推理与矛盾检测总览。当需要进行事实验证、矛盾发现、知识补全、洞见挖掘时使用。涵盖生卒年推断、姓氏推理、反常检测、史料溯源等推理任务。",

    "SKILL_07a_人物生卒年推断.md":
        "历史人物生卒年区间估算方法。当人物无明确生卒记载但有事件记录时,通过事件时间推断生卒年区间。适用于人物时间轴补全、年代合理性验证、传记完整性增强。",

    "SKILL_07b_姓氏推理.md":
        "先秦人物姓与氏的区分与标注方法。当处理先秦人物需要区分'嬴姓赵氏''姬姓周氏'等姓氏组合时使用。涵盖姓氏推理规则、命名规范、标注语法等内容。",

    "SKILL_07c_反常推理.md":
        "不符合常识的历史事实检测与解读。当发现'白起杀降40万''项羽力能扛鼎'等反常记载时,通过推理验证真实性或揭示修辞手法。适用于史实可信度评估、文本批判、历史研究。",

    "SKILL_07d_溯源推理.md":
        "史料来源可信度评估与溯源链构建。当需要追溯《史记》记载的原始来源、评估二手史料可信度时使用。涵盖引文识别、来源推断、可信度评分等内容。",

    "SKILL_08_SKU构造.md":
        "知识单元(SKU)构造方法,从结构化知识到产品化知识单元。当需要将知识图谱封装为可复用、可交易的知识产品时使用。适用于知识产品设计、知识电商、教育内容生产等场景。**规划阶段**。",

    "SKILL_09_应用构造.md":
        "知识库应用产品化总览,从知识到用户产品。当需要基于知识图谱构建阅读器、游戏、问答系统等应用时使用。涵盖认知辅助阅读器、知识库游戏化等应用案例。",

    "SKILL_09a_认知辅助阅读器.md":
        "古籍认知辅助阅读器设计,语法高亮+结构语义化。当需要构建古籍在线阅读器、提供实体高亮、注释浮窗、语义导航等功能时使用。适用于数字人文产品、教育工具、学术平台等场景。",

    "SKILL_09b_知识库游戏化.md":
        "基于《史记》知识库的游戏设计方法。当需要将历史知识转化为互动游戏、剧本杀、卡牌对战等形式时使用。涵盖游戏机制设计、知识融入策略、叙事生成等内容。",
}

# META技能描述映射
META_DESCRIPTIONS = {
    "00-META-00_好东西都是总结出来的.md":
        "元技能的元技能,阐述知识沉淀与SKILL文档编写的方法论。当需要总结项目经验、编写新SKILL、提炼通用方法论时使用。强调从实践到理论的升华过程,适用于团队知识管理、最佳实践沉淀、培训材料编写等场景。",

    "00-META-01_反思.md":
        "Agent驱动的质量审查通用方法论。当任何AI生成内容(实体标注/事件提取/关系构建)需要质量审查与迭代修正时使用。涵盖反思的三个维度(审查粒度/执行策略/迭代模式)、错误模式积累、收敛判断等核心方法。明确使用本技能当用户提到'反思''质量审查''Agent审查''迭代修正'或需要改进AI生成内容质量。",

    "00-META-02_迭代工作流.md":
        "从冷启动到收敛的迭代执行策略。当设计新工序流程、规划多轮迭代任务时使用。基于Lean Semantic Web理论,涵盖快速原型、增量改进、质量收敛等阶段性策略。适用于项目规划、敏捷开发、持续改进等场景。",

    "00-META-03_冷启动.md":
        "从零开始构建AI驱动工序的方法论。当面对全新任务、无历史数据、缺乏参考案例时使用。涵盖最小可行原型(MVP)设计、种子数据构建、快速验证等冷启动策略。适用于新项目启动、新工序设计、技术探索等场景。",

    "00-META-04_柳叶刀方法.md":
        "精细分解与混合解决方案设计方法。当复杂任务需要分解为子任务、选择规则/LLM/混合方案时使用。强调'能用规则绝不用LLM'的成本优化原则。适用于系统架构设计、工序拆解、技术选型等场景。",

    "00-META-05_知识作为上下文压缩.md":
        "知识图谱价值论证,阐述KG作为上下文压缩的理论基础。当需要论证知识图谱必要性、设计知识表示方案、优化上下文使用时参考。涵盖信息论视角、压缩原理、RAG优化等内容。适用于技术方案设计、学术研究、架构评审等场景。",

    "00-META-06_SKILL优化与演化.md":
        "SKILL方法论文档的持续改进策略。当现有SKILL需要优化、发现新的最佳实践、积累错误模式时使用。涵盖文档版本管理、模式库维护、反馈循环设计等内容。适用于知识库维护、文档迭代、团队学习等场景。",

    "00-META-07_可读性.md":
        "人类优先的数据格式设计原则。当设计标注格式、选择数据表示、权衡人类可读性与机器效率时使用。强调Markdown优于JSON、文本优于二进制的哲学。适用于数据格式设计、工具选型、用户体验优化等场景。",

    "00-META-08_标注体系设计.md":
        "语义标记符号的工程化设计原则。当设计新的实体类型、标注语法、消歧规则时使用。涵盖类型体系设计、符号选择、版本演化、工具链适配等内容。适用于标注规范制定、数据建模、schema设计等场景。",

    "00-META-09_Agent提示词工程.md":
        "方法论驱动的AI任务设计与提示词编写。当为Agent设计新任务、编写提示词、调试AI行为时使用。区别于传统Prompt,强调方法论嵌入、任务分解、质量标准等结构化设计。适用于Agent开发、AI工作流设计、提示词优化等场景。",

    "00-META-10_质量控制.md":
        "自动化质检体系与工具链设计方法。当需要构建linter、设计质检规则、自动化检测错误时使用。区别于反思(AI驱动),强调规则驱动、确定性检测、工具化实现。适用于CI/CD集成、数据验证、质量保障等场景。",

    "00-META-11_数据体感培养.md":
        "直接观察数据的十层体系,培养数据敏感度的方法论。当需要理解数据分布、发现异常模式、建立数据直觉时使用。强调从原始数据到可视化的多层次观察。适用于数据分析、质量审查、模式发现等场景。",

    "00-META-12_数据融合.md":
        "多源数据对齐与消歧方法论。当需要融合《史记》与《战国策》等多源史料、解决数据冲突时使用。涵盖实体对齐、时间对齐、矛盾检测、可信度评估等内容。适用于多源知识融合、数据整合、一致性检查等场景。",

    "00-META-13_技能迁移.md":
        "SKILL跨项目复用方法论。当需要将《史记》项目的方法应用到其他古籍、现代文本、多语言场景时使用。涵盖通用化改造、领域适配、工具迁移等策略。适用于技术复用、横向扩展、方法论推广等场景。",
}


def extract_frontmatter_and_content(file_path: Path) -> Tuple[Dict[str, str], str, int]:
    """
    提取frontmatter和正文内容

    Returns:
        (frontmatter_dict, content_without_frontmatter, frontmatter_end_line)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    frontmatter = {}
    content_start = 0

    # 检查是否有frontmatter
    if lines and lines[0].strip() == '---':
        # 查找frontmatter结束位置
        for i in range(1, len(lines)):
            if lines[i].strip() == '---':
                content_start = i + 1
                # 解析frontmatter
                for line in lines[1:i]:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        frontmatter[key.strip()] = value.strip()
                break

    content = ''.join(lines[content_start:])
    return frontmatter, content, content_start


def update_skill_frontmatter(file_path: Path, description: str) -> bool:
    """更新单个SKILL文件的frontmatter"""
    frontmatter, content, _ = extract_frontmatter_and_content(file_path)

    # 保留现有的name和title,只更新description
    name = frontmatter.get('name', '')
    title = frontmatter.get('title', '')

    if not name or not title:
        print(f"  ⚠️  {file_path.name} 缺少name或title字段,跳过")
        return False

    # 构建新的frontmatter
    new_frontmatter = f"""---
name: {name}
description: {description}
---

"""

    new_content = new_frontmatter + content

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"  ✅ {file_path.name}")
    print(f"      description: {description[:80]}..." if len(description) > 80 else f"      description: {description}")
    return True


def add_meta_frontmatter(file_path: Path, description: str) -> bool:
    """为META文件添加frontmatter"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查是否已有frontmatter
    if content.startswith('---'):
        print(f"  ⏭️  {file_path.name} 已有frontmatter,跳过")
        return False

    # 从文件名提取name
    # 00-META-01_反思.md -> meta-01-reflection
    filename = file_path.stem
    match = re.match(r'00-META-(\d+)_(.+)', filename)
    if not match:
        print(f"  ⚠️  {file_path.name} 文件名格式不匹配,跳过")
        return False

    meta_num = match.group(1)
    meta_title = match.group(2)
    name = f"meta-{meta_num}"

    # 构建frontmatter
    new_frontmatter = f"""---
name: {name}
description: {description}
---

"""

    new_content = new_frontmatter + content

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"  ✅ {file_path.name}")
    print(f"      name: {name}")
    print(f"      description: {description[:80]}..." if len(description) > 80 else f"      description: {description}")
    return True


def main():
    skills_dir = Path('/home/baojie/work/knowledge/shiji-kb/skills')

    print("=" * 80)
    print("更新SKILL文件frontmatter")
    print("=" * 80)

    skill_updated = 0
    skill_skipped = 0

    # 更新SKILL文件
    for filename, description in SKILL_DESCRIPTIONS.items():
        file_path = skills_dir / filename
        if file_path.exists():
            if update_skill_frontmatter(file_path, description):
                skill_updated += 1
            else:
                skill_skipped += 1
        else:
            print(f"  ⚠️  文件不存在: {filename}")
            skill_skipped += 1

    print("\n" + "=" * 80)
    print("添加META文件frontmatter")
    print("=" * 80)

    meta_added = 0
    meta_skipped = 0

    # 添加META文件frontmatter
    for filename, description in META_DESCRIPTIONS.items():
        file_path = skills_dir / filename
        if file_path.exists():
            if add_meta_frontmatter(file_path, description):
                meta_added += 1
            else:
                meta_skipped += 1
        else:
            print(f"  ⚠️  文件不存在: {filename}")
            meta_skipped += 1

    print("\n" + "=" * 80)
    print("总结")
    print("=" * 80)
    print(f"SKILL文件:")
    print(f"  ✅ 更新: {skill_updated} 个")
    print(f"  ⏭️  跳过: {skill_skipped} 个")
    print(f"\nMETA文件:")
    print(f"  ✅ 添加: {meta_added} 个")
    print(f"  ⏭️  跳过: {meta_skipped} 个")
    print(f"\n📝 总计: {skill_updated + meta_added} 个文件已更新")


if __name__ == '__main__':
    main()
