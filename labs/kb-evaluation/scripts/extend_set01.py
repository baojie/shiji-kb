#!/usr/bin/env python3
"""
扩展第1组问题集到100题

基于人名词表和设计规范，自动生成剩余的80个问题
确保：
1. 子类型均衡分布（姓名字号20、籍贯家世20、生卒15、官职25、成就20）
2. 难度分布（简单40%、中等40%、困难20%）
3. 章节覆盖>100个
"""

import json
from pathlib import Path

# 当前已有20题
# 需要补充80题，分配如下：
# - 姓名字号：17题（当前3题）
# - 籍贯家世：12题（当前8题，5籍贯+3家世）
# - 生卒年份：15题（当前0题）
# - 官职身份：21题（当前4题）
# - 重要成就：15题（当前5题）

# 新增问题列表
new_questions = [
    # === 姓名字号类（17题）===
    {
        "id": "Q021",
        "question": "司马相如的字是什么？",
        "type": "factual",
        "difficulty": "medium",
        "category": "person_basic_name",
        "subcategory": "字号",
        "target_chapters": ["117"],
        "keywords": ["司马相如", "字", "长卿"]
    },
    {
        "id": "Q022",
        "question": "苏秦的字是什么？",
        "type": "factual",
        "difficulty": "medium",
        "category": "person_basic_name",
        "subcategory": "字号",
        "target_chapters": ["069"],
        "keywords": ["苏秦", "字", "季子"]
    },
    {
        "id": "Q023",
        "question": "张仪的主要活动在哪个时期？",
        "type": "factual",
        "difficulty": "medium",
        "category": "person_basic_name",
        "subcategory": "名号",
        "target_chapters": ["070"],
        "keywords": ["张仪", "战国", "秦惠王"]
    },
    {
        "id": "Q024",
        "question": "荆轲的名字中，'荆'是他的姓还是他的活动地？",
        "type": "factual",
        "difficulty": "medium",
        "category": "person_basic_name",
        "subcategory": "名号辨析",
        "target_chapters": ["086"],
        "keywords": ["荆轲", "卫", "荆"]
    },
    {
        "id": "Q025",
        "question": "范雎的字是什么？",
        "type": "factual",
        "difficulty": "easy",
        "category": "person_basic_name",
        "subcategory": "字号",
        "target_chapters": ["079"],
        "keywords": ["范雎", "字", "叔"]
    },
    {
        "id": "Q026",
        "question": "晏婴的字是什么？",
        "type": "factual",
        "difficulty": "easy",
        "category": "person_basic_name",
        "subcategory": "字号",
        "target_chapters": ["062"],
        "keywords": ["晏婴", "字", "平仲"]
    },
    {
        "id": "Q027",
        "question": "子贡的本名是什么？",
        "type": "factual",
        "difficulty": "medium",
        "category": "person_basic_name",
        "subcategory": "名号",
        "target_chapters": ["067"],
        "keywords": ["子贡", "端木赐"]
    },
    {
        "id": "Q028",
        "question": "子路的本名是什么？",
        "type": "factual",
        "difficulty": "medium",
        "category": "person_basic_name",
        "subcategory": "名号",
        "target_chapters": ["067"],
        "keywords": ["子路", "仲由"]
    },
    {
        "id": "Q029",
        "question": "韩非子的姓名中，哪个是他的国号？",
        "type": "factual",
        "difficulty": "easy",
        "category": "person_basic_name",
        "subcategory": "名号",
        "target_chapters": ["063"],
        "keywords": ["韩非", "韩", "非"]
    },
    {
        "id": "Q030",
        "question": "扁鹊的本名是什么？",
        "type": "factual",
        "difficulty": "medium",
        "category": "person_basic_name",
        "subcategory": "名号",
        "target_chapters": ["105"],
        "keywords": ["扁鹊", "秦越人"]
    },
    {
        "id": "Q031",
        "question": "李耳的字是什么？",
        "type": "factual",
        "difficulty": "easy",
        "category": "person_basic_name",
        "subcategory": "字号",
        "target_chapters": ["063"],
        "keywords": ["老子", "李耳", "字", "聃"]
    },
    {
        "id": "Q032",
        "question": "墨子的姓名是什么？",
        "type": "factual",
        "difficulty": "medium",
        "category": "person_basic_name",
        "subcategory": "名号",
        "target_chapters": ["074"],
        "keywords": ["墨子", "墨翟"]
    },
    {
        "id": "Q033",
        "question": "孟子的名字是什么？",
        "type": "factual",
        "difficulty": "easy",
        "category": "person_basic_name",
        "subcategory": "名",
        "target_chapters": ["074"],
        "keywords": ["孟子", "孟轲"]
    },
    {
        "id": "Q034",
        "question": "荀子的名字是什么？",
        "type": "factual",
        "difficulty": "easy",
        "category": "person_basic_name",
        "subcategory": "名",
        "target_chapters": ["074"],
        "keywords": ["荀子", "荀况"]
    },
    {
        "id": "Q035",
        "question": "庄子的姓名是什么？",
        "type": "factual",
        "difficulty": "easy",
        "category": "person_basic_name",
        "subcategory": "名",
        "target_chapters": ["063"],
        "keywords": ["庄子", "庄周"]
    },
    {
        "id": "Q036",
        "question": "吴起的名字中，哪个是姓？",
        "type": "factual",
        "difficulty": "easy",
        "category": "person_basic_name",
        "subcategory": "姓名",
        "target_chapters": ["065"],
        "keywords": ["吴起", "吴", "起"]
    },
    {
        "id": "Q037",
        "question": "孙膑的名字是'膑'还是外号？",
        "type": "factual",
        "difficulty": "hard",
        "category": "person_basic_name",
        "subcategory": "名号辨析",
        "target_chapters": ["065"],
        "keywords": ["孙膑", "膑刑", "本名"]
    },

    # === 籍贯家世类（12题）===
    {
        "id": "Q038",
        "question": "范雎是哪国人？",
        "type": "factual",
        "difficulty": "easy",
        "category": "person_basic_origin",
        "subcategory": "籍贯",
        "target_chapters": ["079"],
        "keywords": ["范雎", "魏"]
    },
    {
        "id": "Q039",
        "question": "苏秦是哪里人？",
        "type": "factual",
        "difficulty": "easy",
        "category": "person_basic_origin",
        "subcategory": "籍贯",
        "target_chapters": ["069"],
        "keywords": ["苏秦", "东周", "洛阳"]
    },
    {
        "id": "Q040",
        "question": "荆轲的籍贯是哪里？",
        "type": "factual",
        "difficulty": "easy",
        "category": "person_basic_origin",
        "subcategory": "籍贯",
        "target_chapters": ["086"],
        "keywords": ["荆轲", "卫"]
    },
    {
        "id": "Q041",
        "question": "扁鹊的籍贯是哪里？",
        "type": "factual",
        "difficulty": "easy",
        "category": "person_basic_origin",
        "subcategory": "籍贯",
        "target_chapters": ["105"],
        "keywords": ["扁鹊", "秦越人", "渤海郡"]
    },
    {
        "id": "Q042",
        "question": "张良的祖上是哪国的相国？",
        "type": "factual",
        "difficulty": "medium",
        "category": "person_basic_family",
        "subcategory": "家世",
        "target_chapters": ["055"],
        "keywords": ["张良", "韩", "五世相"]
    },
    {
        "id": "Q043",
        "question": "陈平的家境如何？",
        "type": "factual",
        "difficulty": "medium",
        "category": "person_basic_family",
        "subcategory": "家世",
        "target_chapters": ["056"],
        "keywords": ["陈平", "贫寒"]
    },
    {
        "id": "Q044",
        "question": "萧何是哪里人？",
        "type": "factual",
        "difficulty": "easy",
        "category": "person_basic_origin",
        "subcategory": "籍贯",
        "target_chapters": ["053"],
        "keywords": ["萧何", "沛"]
    },
    {
        "id": "Q045",
        "question": "曹参是哪里人？",
        "type": "factual",
        "difficulty": "easy",
        "category": "person_basic_origin",
        "subcategory": "籍贯",
        "target_chapters": ["054"],
        "keywords": ["曹参", "沛"]
    },
    {
        "id": "Q046",
        "question": "樊哙的职业背景是什么？",
        "type": "factual",
        "difficulty": "easy",
        "category": "person_basic_family",
        "subcategory": "出身",
        "target_chapters": ["095"],
        "keywords": ["樊哙", "屠狗"]
    },
    {
        "id": "Q047",
        "question": "季布是哪里人？",
        "type": "factual",
        "difficulty": "medium",
        "category": "person_basic_origin",
        "subcategory": "籍贯",
        "target_chapters": ["100"],
        "keywords": ["季布", "楚"]
    },
    {
        "id": "Q048",
        "question": "晁错的父亲对他有何建议？",
        "type": "factual",
        "difficulty": "hard",
        "category": "person_basic_family",
        "subcategory": "父子关系",
        "target_chapters": ["101"],
        "keywords": ["晁错", "父亲", "劝谏"]
    },
    {
        "id": "Q049",
        "question": "周勃的出身职业是什么？",
        "type": "factual",
        "difficulty": "medium",
        "category": "person_basic_family",
        "subcategory": "出身",
        "target_chapters": ["057"],
        "keywords": ["周勃", "织薄曲"]
    },

    # === 生卒年份类（15题）===
    {
        "id": "Q050",
        "question": "秦始皇在位多少年？",
        "type": "factual",
        "difficulty": "medium",
        "category": "person_basic_time",
        "subcategory": "在位年数",
        "target_chapters": ["006"],
        "keywords": ["秦始皇", "在位", "三十七年"]
    },
    {
        "id": "Q051",
        "question": "汉景帝在位多少年？",
        "type": "factual",
        "difficulty": "medium",
        "category": "person_basic_time",
        "subcategory": "在位年数",
        "target_chapters": ["011"],
        "keywords": ["汉景帝", "在位", "十六年"]
    },
    {
        "id": "Q052",
        "question": "项羽从起兵到乌江自刎经历了多少年？",
        "type": "factual",
        "difficulty": "hard",
        "category": "person_basic_time",
        "subcategory": "生涯时长",
        "target_chapters": ["007"],
        "keywords": ["项羽", "起兵", "自刎", "八年"]
    },
    {
        "id": "Q053",
        "question": "孔子享年多少岁？",
        "type": "factual",
        "difficulty": "medium",
        "category": "person_basic_time",
        "subcategory": "寿命",
        "target_chapters": ["047"],
        "keywords": ["孔子", "年", "七十三"]
    },
    {
        "id": "Q054",
        "question": "韩信是何时被封为齐王的？",
        "type": "factual",
        "difficulty": "hard",
        "category": "person_basic_time",
        "subcategory": "重要时刻",
        "target_chapters": ["092"],
        "keywords": ["韩信", "齐王", "汉四年"]
    },
    {
        "id": "Q055",
        "question": "韩信被杀是在汉朝建立后的第几年？",
        "type": "factual",
        "difficulty": "hard",
        "category": "person_basic_time",
        "subcategory": "重要时刻",
        "target_chapters": ["092"],
        "keywords": ["韩信", "被杀", "高祖十一年"]
    },
    {
        "id": "Q056",
        "question": "吕后执政多少年？",
        "type": "factual",
        "difficulty": "medium",
        "category": "person_basic_time",
        "subcategory": "执政年数",
        "target_chapters": ["009"],
        "keywords": ["吕后", "执政", "八年"]
    },
    {
        "id": "Q057",
        "question": "秦始皇是何时出生的（以秦昭王年号计）？",
        "type": "factual",
        "difficulty": "hard",
        "category": "person_basic_time",
        "subcategory": "生年",
        "target_chapters": ["006"],
        "keywords": ["秦始皇", "昭王四十八年", "邯郸"]
    },
    {
        "id": "Q058",
        "question": "商鞅变法开始于哪一年（秦孝公纪年）？",
        "type": "factual",
        "difficulty": "hard",
        "category": "person_basic_time",
        "subcategory": "重要时刻",
        "target_chapters": ["068"],
        "keywords": ["商鞅", "变法", "孝公三年"]
    },
    {
        "id": "Q059",
        "question": "陈胜起义是在秦二世哪一年？",
        "type": "factual",
        "difficulty": "medium",
        "category": "person_basic_time",
        "subcategory": "重要时刻",
        "target_chapters": ["048"],
        "keywords": ["陈胜", "起义", "秦二世元年"]
    },
    {
        "id": "Q060",
        "question": "项羽是何时自刎的（以汉纪年）？",
        "type": "factual",
        "difficulty": "medium",
        "category": "person_basic_time",
        "subcategory": "去世时间",
        "target_chapters": ["007"],
        "keywords": ["项羽", "自刎", "汉五年"]
    },
    {
        "id": "Q061",
        "question": "李斯是何时被杀的（秦纪年）？",
        "type": "factual",
        "difficulty": "hard",
        "category": "person_basic_time",
        "subcategory": "去世时间",
        "target_chapters": ["087"],
        "keywords": ["李斯", "被杀", "秦二世二年"]
    },
    {
        "id": "Q062",
        "question": "司马迁是何时开始著史记的？",
        "type": "factual",
        "difficulty": "hard",
        "category": "person_basic_time",
        "subcategory": "重要时刻",
        "target_chapters": ["130"],
        "keywords": ["司马迁", "史记", "太初元年"]
    },
    {
        "id": "Q063",
        "question": "霍去病去世时年仅多少岁？",
        "type": "factual",
        "difficulty": "medium",
        "category": "person_basic_time",
        "subcategory": "寿命",
        "target_chapters": ["111"],
        "keywords": ["霍去病", "年", "二十三"]
    },
    {
        "id": "Q064",
        "question": "汉武帝在位多少年？",
        "type": "factual",
        "difficulty": "medium",
        "category": "person_basic_time",
        "subcategory": "在位年数",
        "target_chapters": ["012"],
        "keywords": ["汉武帝", "在位", "五十四年"]
    },

    # === 官职身份类（21题）===
    {
        "id": "Q065",
        "question": "蔡泽在秦国担任过什么官职？",
        "type": "factual",
        "difficulty": "medium",
        "category": "person_basic_position",
        "subcategory": "官职",
        "target_chapters": ["079"],
        "keywords": ["蔡泽", "丞相", "秦"]
    },
    {
        "id": "Q066",
        "question": "张良被刘邦封为什么侯？",
        "type": "factual",
        "difficulty": "easy",
        "category": "person_basic_position",
        "subcategory": "爵位",
        "target_chapters": ["055"],
        "keywords": ["张良", "留侯"]
    },
    {
        "id": "Q067",
        "question": "萧何在汉初担任什么职务？",
        "type": "factual",
        "difficulty": "easy",
        "category": "person_basic_position",
        "subcategory": "官职",
        "target_chapters": ["053"],
        "keywords": ["萧何", "丞相"]
    },
    {
        "id": "Q068",
        "question": "曹参在汉初先后担任过哪些重要职务？",
        "type": "factual",
        "difficulty": "medium",
        "category": "person_basic_position",
        "subcategory": "官职",
        "target_chapters": ["054"],
        "keywords": ["曹参", "齐相", "丞相"]
    },
    {
        "id": "Q069",
        "question": "陈平最终官至什么职位？",
        "type": "factual",
        "difficulty": "easy",
        "category": "person_basic_position",
        "subcategory": "官职",
        "target_chapters": ["056"],
        "keywords": ["陈平", "左丞相"]
    },
    {
        "id": "Q070",
        "question": "周勃最终被封为什么侯？",
        "type": "factual",
        "difficulty": "easy",
        "category": "person_basic_position",
        "subcategory": "爵位",
        "target_chapters": ["057"],
        "keywords": ["周勃", "绛侯"]
    },
    {
        "id": "Q071",
        "question": "灌婴最初以什么身份跟随刘邦？",
        "type": "factual",
        "difficulty": "medium",
        "category": "person_basic_position",
        "subcategory": "职业",
        "target_chapters": ["095"],
        "keywords": ["灌婴", "贩缯"]
    },
    {
        "id": "Q072",
        "question": "叔孙通的主要职责是什么？",
        "type": "factual",
        "difficulty": "medium",
        "category": "person_basic_position",
        "subcategory": "职责",
        "target_chapters": ["099"],
        "keywords": ["叔孙通", "制定礼仪", "太常"]
    },
    {
        "id": "Q073",
        "question": "张骞因何功被封为博望侯？",
        "type": "factual",
        "difficulty": "medium",
        "category": "person_basic_position",
        "subcategory": "封侯原因",
        "target_chapters": ["123"],
        "keywords": ["张骞", "博望侯", "出使西域"]
    },
    {
        "id": "Q074",
        "question": "卫青官至何职？",
        "type": "factual",
        "difficulty": "easy",
        "category": "person_basic_position",
        "subcategory": "官职",
        "target_chapters": ["111"],
        "keywords": ["卫青", "大将军"]
    },
    {
        "id": "Q075",
        "question": "霍去病的官职是什么？",
        "type": "factual",
        "difficulty": "easy",
        "category": "person_basic_position",
        "subcategory": "官职",
        "target_chapters": ["111"],
        "keywords": ["霍去病", "骠骑将军"]
    },
    {
        "id": "Q076",
        "question": "公孙弘以什么身份起家？",
        "type": "factual",
        "difficulty": "hard",
        "category": "person_basic_position",
        "subcategory": "出身",
        "target_chapters": ["112"],
        "keywords": ["公孙弘", "养猪", "狱吏"]
    },
    {
        "id": "Q077",
        "question": "董仲舒的主要身份是什么？",
        "type": "factual",
        "difficulty": "easy",
        "category": "person_basic_position",
        "subcategory": "职业",
        "target_chapters": ["121"],
        "keywords": ["董仲舒", "儒者", "博士"]
    },
    {
        "id": "Q078",
        "question": "司马相如最初以什么文体闻名？",
        "type": "factual",
        "difficulty": "medium",
        "category": "person_basic_position",
        "subcategory": "专长",
        "target_chapters": ["117"],
        "keywords": ["司马相如", "辞赋", "子虚赋"]
    },
    {
        "id": "Q079",
        "question": "东方朔在汉武帝朝担任什么职务？",
        "type": "factual",
        "difficulty": "medium",
        "category": "person_basic_position",
        "subcategory": "官职",
        "target_chapters": ["126"],
        "keywords": ["东方朔", "太中大夫"]
    },
    {
        "id": "Q080",
        "question": "郦食其最初的身份是什么？",
        "type": "factual",
        "difficulty": "medium",
        "category": "person_basic_position",
        "subcategory": "出身",
        "target_chapters": ["097"],
        "keywords": ["郦食其", "监门", "门吏"]
    },
    {
        "id": "Q081",
        "question": "淳于髡的主要身份是什么？",
        "type": "factual",
        "difficulty": "medium",
        "category": "person_basic_position",
        "subcategory": "职业",
        "target_chapters": ["126"],
        "keywords": ["淳于髡", "齐", "辩士"]
    },
    {
        "id": "Q082",
        "question": "仓公的本职是什么？",
        "type": "factual",
        "difficulty": "easy",
        "category": "person_basic_position",
        "subcategory": "官职",
        "target_chapters": ["105"],
        "keywords": ["淳于意", "太仓长", "医"]
    },
    {
        "id": "Q083",
        "question": "货殖列传中，范蠡改名换姓后自称什么？",
        "type": "factual",
        "difficulty": "hard",
        "category": "person_basic_position",
        "subcategory": "化名",
        "target_chapters": ["129"],
        "keywords": ["范蠡", "陶朱公"]
    },
    {
        "id": "Q084",
        "question": "郭解的主要身份是什么？",
        "type": "factual",
        "difficulty": "easy",
        "category": "person_basic_position",
        "subcategory": "职业",
        "target_chapters": ["124"],
        "keywords": ["郭解", "游侠"]
    },
    {
        "id": "Q085",
        "question": "魏其侯窦婴与汉武帝是什么亲属关系？",
        "type": "factual",
        "difficulty": "hard",
        "category": "person_basic_family",
        "subcategory": "亲属关系",
        "target_chapters": ["107"],
        "keywords": ["窦婴", "汉武帝", "窦太后", "堂兄弟"]
    },

    # === 重要成就类（15题）===
    {
        "id": "Q086",
        "question": "张骞出使西域的主要成就是什么？",
        "type": "factual",
        "difficulty": "medium",
        "category": "person_basic_achievement",
        "subcategory": "主要成就",
        "target_chapters": ["123"],
        "keywords": ["张骞", "西域", "丝绸之路"]
    },
    {
        "id": "Q087",
        "question": "卫青对匈奴战争的主要贡献是什么？",
        "type": "factual",
        "difficulty": "medium",
        "category": "person_basic_achievement",
        "subcategory": "主要成就",
        "target_chapters": ["111"],
        "keywords": ["卫青", "匈奴", "漠南", "七战七捷"]
    },
    {
        "id": "Q088",
        "question": "霍去病最著名的战役是什么？",
        "type": "factual",
        "difficulty": "medium",
        "category": "person_basic_achievement",
        "subcategory": "主要成就",
        "target_chapters": ["111"],
        "keywords": ["霍去病", "漠北", "封狼居胥"]
    },
    {
        "id": "Q089",
        "question": "孙武的主要著作是什么？",
        "type": "factual",
        "difficulty": "easy",
        "category": "person_basic_achievement",
        "subcategory": "主要成就",
        "target_chapters": ["065"],
        "keywords": ["孙武", "孙子兵法"]
    },
    {
        "id": "Q090",
        "question": "吴起在军事和政治上有何成就？",
        "type": "factual",
        "difficulty": "medium",
        "category": "person_basic_achievement",
        "subcategory": "主要成就",
        "target_chapters": ["065"],
        "keywords": ["吴起", "兵法", "变法"]
    },
    {
        "id": "Q091",
        "question": "苏秦最著名的外交成就是什么？",
        "type": "factual",
        "difficulty": "easy",
        "category": "person_basic_achievement",
        "subcategory": "主要成就",
        "target_chapters": ["069"],
        "keywords": ["苏秦", "合纵"]
    },
    {
        "id": "Q092",
        "question": "张仪最著名的外交策略是什么？",
        "type": "factual",
        "difficulty": "easy",
        "category": "person_basic_achievement",
        "subcategory": "主要成就",
        "target_chapters": ["070"],
        "keywords": ["张仪", "连横"]
    },
    {
        "id": "Q093",
        "question": "李冰在蜀郡的主要功绩是什么？",
        "type": "factual",
        "difficulty": "medium",
        "category": "person_basic_achievement",
        "subcategory": "主要成就",
        "target_chapters": ["029"],
        "keywords": ["李冰", "都江堰"]
    },
    {
        "id": "Q094",
        "question": "屈原的主要文学成就是什么？",
        "type": "factual",
        "difficulty": "easy",
        "category": "person_basic_achievement",
        "subcategory": "主要成就",
        "target_chapters": ["084"],
        "keywords": ["屈原", "离骚", "楚辞"]
    },
    {
        "id": "Q095",
        "question": "贾谊著有哪些重要文章？",
        "type": "factual",
        "difficulty": "medium",
        "category": "person_basic_achievement",
        "subcategory": "主要成就",
        "target_chapters": ["084"],
        "keywords": ["贾谊", "过秦论", "鵩鸟赋"]
    },
    {
        "id": "Q096",
        "question": "太史公如何评价游侠？",
        "type": "evaluative",
        "difficulty": "medium",
        "category": "person_basic_evaluation",
        "subcategory": "太史公评价",
        "target_chapters": ["124"],
        "keywords": ["游侠", "太史公曰", "义"]
    },
    {
        "id": "Q097",
        "question": "太史公如何评价货殖之人？",
        "type": "evaluative",
        "difficulty": "medium",
        "category": "person_basic_evaluation",
        "subcategory": "太史公评价",
        "target_chapters": ["129"],
        "keywords": ["货殖", "太史公曰", "富"]
    },
    {
        "id": "Q098",
        "question": "太史公如何评价酷吏？",
        "type": "evaluative",
        "difficulty": "medium",
        "category": "person_basic_evaluation",
        "subcategory": "太史公评价",
        "target_chapters": ["122"],
        "keywords": ["酷吏", "太史公曰", "法"]
    },
    {
        "id": "Q099",
        "question": "太史公如何评价刺客？",
        "type": "evaluative",
        "difficulty": "medium",
        "category": "person_basic_evaluation",
        "subcategory": "太史公评价",
        "target_chapters": ["086"],
        "keywords": ["刺客", "太史公曰", "义士"]
    },
    {
        "id": "Q100",
        "question": "太史公在《淮阴侯列传》中如何评价韩信？",
        "type": "evaluative",
        "difficulty": "hard",
        "category": "person_basic_evaluation",
        "subcategory": "太史公评价",
        "target_chapters": ["092"],
        "keywords": ["韩信", "太史公曰", "功高", "谋反"]
    }
]

print(f"新增问题数: {len(new_questions)}")
print("\n子类型分布:")
subcategory_count = {}
for q in new_questions:
    subcat = q['subcategory']
    subcategory_count[subcat] = subcategory_count.get(subcat, 0) + 1

for subcat, count in sorted(subcategory_count.items()):
    print(f"  {subcat}: {count}题")

print("\n难度分布:")
difficulty_count = {"easy": 0, "medium": 0, "hard": 0}
for q in new_questions:
    difficulty_count[q['difficulty']] += 1

print(f"  简单: {difficulty_count['easy']}题")
print(f"  中等: {difficulty_count['medium']}题")
print(f"  困难: {difficulty_count['hard']}题")

print("\n章节覆盖:")
chapters = set()
for q in new_questions:
    chapters.update(q['target_chapters'])

print(f"  新增章节数: {len(chapters)}")
print(f"  章节列表: {sorted(chapters)}")
