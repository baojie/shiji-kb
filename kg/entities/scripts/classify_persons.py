#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为 person 实体生成分类标签（身份类）。

完全对照 classify_places.py / classify_officials.py 的工作流，按 L1-L5 打分：
  L1   显式白名单（帝王/诸侯/将相/学者/外邦/上古/…）
       + person.ttl 本体分类（1825 人）
       + rulers.json 自动归入 帝王/诸侯君主/外邦
  L2   章节上下文
       - 专题列传直接映射（086/105/110/113-116/119/121/122/124-129）
       - 本纪/世家 主人公 → 帝王/诸侯君主
  L2.5 shihao_index 批量归类
  L3   共现模式（chapter_md 扫描 + 三家注）
  L4   后缀启发式（单于/夫人/公子/侯等）
  L5   并列/亲属传播

输出: kg/entities/data/person_categories.json
结构: { canonical_name: [cat, cat, ...] }  # 按优先级升序，主标在前
"""

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
INDEX_JSON = _ROOT / 'kg' / 'entities' / 'data' / 'entity_index.json'
OUT_JSON = _ROOT / 'kg' / 'entities' / 'data' / 'person_categories.json'
OUT_CONF_JSON = _ROOT / 'kg' / 'entities' / 'data' / 'person_confidence.json'
RULERS_JSON = _ROOT / 'kg' / 'relations' / 'rulers.json'
SHIHAO_JSON = _ROOT / 'kg' / 'entities' / 'data' / 'shihao_index.json'
ALIAS_JSON = _ROOT / 'kg' / 'entities' / 'data' / 'entity_aliases.json'
PERSON_TTL = _ROOT / 'kg' / 'taxonomy' / 'person.ttl'
SANJIA_FILE = _ROOT / 'corpus' / 'shiji' / '史记集解三家注索隐正义.txt'
CHAPTER_DIR = _ROOT / 'chapter_md'


# ─── 类别常量（优先级数字越小越高）───
CAT_EMPEROR    = ('帝王', 1)
CAT_RULER      = ('诸侯君主', 2)
CAT_CONSORT    = ('后妃', 3)
CAT_PRINCE     = ('宗室', 4)
CAT_CHANCELLOR = ('将相', 5)
CAT_STRATEGIST = ('谋臣策士', 6)
CAT_SCHOLAR    = ('学者文士', 7)
CAT_LOCAL      = ('地方官', 8)
CAT_SWORDSMAN  = ('刺客游侠', 9)
CAT_COURTIER   = ('近臣奇人', 10)
CAT_MERCHANT   = ('货殖', 11)
CAT_FOREIGN    = ('外邦', 12)
CAT_MYTHICAL   = ('上古神话', 13)
CAT_RETAINER   = ('家臣门客', 14)
CAT_COMMONER   = ('平民刑徒', 15)
CAT_MIS        = ('误标', 90)
CAT_SPLIT      = ('待拆分', 91)
CAT_FICTIONAL  = ('虚构寓言', 92)

ALL_CATS = [
    CAT_EMPEROR, CAT_RULER, CAT_CONSORT, CAT_PRINCE, CAT_CHANCELLOR,
    CAT_STRATEGIST, CAT_SCHOLAR, CAT_LOCAL, CAT_SWORDSMAN, CAT_COURTIER,
    CAT_MERCHANT, CAT_FOREIGN, CAT_MYTHICAL, CAT_RETAINER, CAT_COMMONER,
    CAT_MIS, CAT_SPLIT, CAT_FICTIONAL,
]
CAT_PRIORITY = {name: prio for name, prio in ALL_CATS}


# ─── 显式白名单 ───

# 帝王（三皇五帝+历代天子+秦汉皇帝）
EXPLICIT_EMPEROR = {
    # 上古
    '黄帝', '颛顼', '帝颛顼高阳', '帝喾高辛', '尧', '舜', '帝挚',
    # 夏
    '禹', '启', '夏后帝启', '桀',
    '帝太康', '帝中康', '后帝相', '帝孔甲', '帝不降',
    # 商
    '汤', '帝太甲', '帝盘庚', '帝武丁', '纣', '帝辛',
    # 周
    '周文王', '周武王', '周成王', '周康王', '周昭王', '周穆王',
    '周共王', '周懿王', '周孝王', '周夷王', '周厉王', '周宣王', '周幽王',
    '周平王', '周桓王', '周庄王', '周釐王', '周惠王', '周襄王',
    '周顷王', '周匡王', '周定王', '周简王', '周灵王', '周景王',
    '周悼王', '周敬王', '周元王', '周贞定王', '周哀王', '周思王', '周考王',
    '周威烈王', '周安王', '周烈王', '周显王', '周慎靓王', '周赧王',
    # 秦
    '秦始皇', '秦始皇帝', '始皇', '二世', '秦二世', '子婴',
    # 汉（史记范围）
    '汉高祖', '高帝', '孝惠帝', '汉惠帝', '高后', '吕太后',
    '汉文帝', '孝文帝', '汉景帝', '孝景帝', '汉武帝', '孝武帝',
    '汉昭帝',
    # 异体字/别名
    '商汤', '秦皇帝', '今上', '当今', '今天子',
    # 上古先王（可归帝王，也可兼上古神话）
    '王季历', '公刘', '古公亶父', '太王', '王亥', '季历',
    '蟜极', '穷蝉', '敬康', '句望', '桥牛',
    # 殷商先公先王系谱（003 殷本纪）
    '相土', '昌若', '曹圉', '冥', '振', '微', '报丁', '报乙', '报丙',
    '主壬', '主癸', '示壬', '示癸',
    # 周先祖系谱（004 周本纪）
    '鞠', '皇仆', '高圉', '亚圉', '公非', '辟方', '毁隃',
    '差弗', '庆节',
    # 补录（第三轮）
    '帝俈', '帝喾', '帝俊',       # 上古帝王
    '汉宣帝', '孝宣帝', '孝昭帝', '汉昭帝',  # 汉帝
    '周缪王', '周穆王',            # 已有穆王，缪王为异体
    '殷契',                        # 商始祖
    '大骆',                        # 秦先祖
    '非子',                        # 秦非子（秦始封君）
    '秦仲',                        # 秦国君
    '秦庄公', '秦襄公后',          # 秦早期君主（补）
    '隐王',                        # 陈胜谥隐王（或刘如意王号）→ 帝王类
}

# 诸侯君主（rulers.json 会批量补）
EXPLICIT_RULER = {
    # 春秋五霸
    '齐桓公', '晋文公', '秦穆公', '宋襄公', '楚庄王',
    # 战国七雄代表
    '秦孝公', '秦惠文王', '秦武王', '秦昭王', '秦庄襄王',
    '秦惠王', '秦献公', '秦文公', '秦襄公', '秦孝文王',
    '秦悼公', '秦惠公',
    '魏文侯', '魏惠王', '魏武侯', '魏襄王', '魏哀王',
    '赵武灵王', '赵惠文王', '赵孝成王',
    '韩昭侯', '韩宣惠王',
    '燕昭王', '燕惠王',
    '楚怀王', '楚顷襄王',
    '齐威王', '齐宣王', '齐湣王', '齐王建', '齐襄王',
    '梁惠王',
    # 吴越
    '吴王阖闾', '吴王夫差', '吴王光', '越王句践', '越王勾践',
    '允常', '鼫与', '无彊',
    # 先秦诸侯
    '郑庄公', '郑桓公', '郑厉公', '郑文公', '郑昭公',
    '郑成公', '郑简公', '郑缪公', '郑釐公', '郑灵公',
    '陈厉公', '陈桓公', '陈哀公',
    '卫惠公', '卫灵公', '卫献公', '卫出公', '卫宣公',
    '卫庄公', '卫成公', '卫桓公', '卫庄公蒯聩', '卫共伯馀', '卫黔牟',
    '宋昭公', '宋景公', '宋公', '宋襄公',
    # 上古三代诸侯
    '白公胜', '公叔座',
    # 被rulers遗漏的其他
    '王季历', '公刘', '古公亶父', '太王',
    # 杞/虢等小国诸侯
    '杞湣公', '杞哀公', '杞武公', '杞文公', '杞简公',
    '楚蚡冒', '楚鬻熊', '楚庄敖', '楚子晳', '郑子婴',
    '田齐桓公',  # 战国田齐
    '宣公力',  # 鲁宣公别名
    # 补录（第三轮）
    # 杞国君主系列（036_陈杞世家）
    '杞谋娶公', '杞隐公', '杞釐公', '杞出公', '杞桓公', '杞僖公',
    # 宋国君主
    '釐公举',          # 宋釐公
    # 小国诸侯/诸侯王
    '吴臣',          # 长沙王（吴芮子）
    '毋知',          # 齐君无知（弑君自立）
    '齐晏孺子',      # 被弑之齐君
    '共尉',          # 临江王
    '吴叔',          # 被立为假王
    '缗',            # 晋侯缗
    '康叔封',        # 周武王弟，封卫始祖
    '釐公举',        # 宋国君
    '楚王延寿',      # 楚王
    '姜齐桓公',      # 姜齐桓公（区别于田齐桓公）
    '齐君无知',      # 齐国君主
    '密康公',        # 周共王时诸侯
    '威公',          # 东周小国君
    '东周惠公',      # 东周君
    '王弟带',        # 周王室宗亲（弑周王）→ 宗室更准确，但历史上争王位
    '公孙纠',        # 宋昭公父→宗室，此处归诸侯系
    '帝太康', '太康',  # 夏代诸侯/帝王（后代）
    '吴王刘濞',      # 吴王（刘姓诸侯）
    '楚元王',        # 刘交，汉楚元王
}

# 后妃
EXPLICIT_CONSORT = {
    '褒姒', '妲己', '妹喜', '骊姬', '虞姬',
    '戚夫人', '薄太后', '窦太后', '王太后', '王皇后',
    '陈皇后', '卫皇后', '卫夫人', '李夫人', '钩弋夫人',
    '武帝母', '孝文太后', '孝景太后',
    '平阳公主', '平阳主',
    '吕后', '吕太后', '高后',
    '宣太后', '华阳夫人', '华阳太后',
    '赵太后', '夏太后', '帝太后', '王太后',
    # 补录（第三轮）
    '嫘祖',          # 黄帝正妃
    '郑袖', '楚怀王郑袖',  # 楚怀王宠姬
    '燕后',          # 赵太后女，嫁燕
    '大任',          # 周文王母
    '魏媪',          # 薄太后母
    '卫媪',          # 卫青母，平阳侯妾
    '惠文后',        # 秦惠文王后
    '窦太主',        # 窦太后女，馆陶公主
    '娥',            # 脩成君女
    '太史敫女',      # 太史敫女，嫁田法章
    '大骆妻',        # 秦先祖妻（申侯女）
    '简狄',          # 殷契母
    '姜原',          # 后稷母
}

# 宗室（公子/王子/太子/外戚）
EXPLICIT_PRINCE = {
    '周公旦', '召公奭', '召公', '太公望', '太公望吕尚', '吕尚',
    '信陵君', '孟尝君', '平原君', '春申君', '魏无忌', '田文',
    '赵胜', '黄歇', '公子光',
    '太子丹', '太子申生', '公子纠', '公子小白',
    '燕太子丹', '卫太子伋', '共叔段', '周王子穨',
    '楚太子建', '季札',  # 季子札=吴国公子札
    '厓季载',  # 周文王子冉季载？
    '窦婴', '田蚡', '窦长君', '窦少君', '田胜', '臧兒',
    # 汉代刘氏宗室（大量）
    '刘长', '刘安', '刘武', '刘肥', '刘交', '刘郢', '刘戊',
    '刘濞', '刘非', '刘启', '刘揖', '刘荣', '刘德',
    '刘孝', '刘勃', '刘志', '刘迁', '刘舍', '刘棁', '刘赐',
    '刘彭祖', '刘将闾', '刘寿', '刘定国', '刘登', '刘阏于',
    '刘喜', '刘昌', '刘昆侈', '刘胜', '刘参', '刘义', '刘庆',
    '刘去', '刘建', '刘端', '刘寄', '刘乘', '刘舜', '刘嘉',
    '刘恢', '刘恒',  # 恒=文帝，但未称帝前为代王
    '齐悼惠王', '淮南厉王', '淮南王', '梁孝王', '梁共王',
    '赵敬肃王', '菑川懿王', '河闲献王', '济北贞王',
    '定国',  # 楚定王
    '淮阴侯', '东牟侯', '长沙王', '吴王',  # 刘濞
}

# 将相（含丞相/三公/将军/大臣）
EXPLICIT_CHANCELLOR = {
    # 先秦相
    '管仲', '晏婴', '晏子', '百里奚', '蹇叔', '甘茂', '穰侯', '魏冉',
    '乐毅', '廉颇', '蔺相如', '李牧', '赵奢', '田单', '乐乘',
    '王翦', '王贲', '蒙恬', '蒙武', '蒙毅', '白起', '司马错',
    '范雎', '蔡泽', '吕不韦', '李斯', '赵高',
    '田忌', '孙膑', '孙武',
    '吴起', '乐羊', '李悝',
    '商鞅', '申不害', '韩非', '慎到',
    # 春秋卿大夫
    '崔杼', '鲍叔牙', '鲍叔', '文种', '庆封', '晋鄙',
    '吕礼', '驺忌子', '驺忌', '智伯瑶', '荀瑶', '费无忌',
    '公孙奭', '隰朋', '南宫万', '囊瓦', '开方', '赵良',
    '周緤', '周仁', '张卿', '王信', '盖公', '张负',
    '楚子西', '楚伍奢', '楚伍举', '伍奢', '伍举',
    '赵括', '魏勃', '周亚夫', '赵盾', '赵衰',
    '狐偃', '咎犯', '子犯', '百里傒', '先轸', '随会',
    '郤克', '赵鞅', '栾书', '韩康子', '魏桓子',
    '田不礼', '邯郸午', '陈招', '卫伉', '曹窋', '曹襄',
    # 秦张仪等"国名+人名"格式
    '秦张仪', '魏相田文', '纵横家陈轸',
    '秦樗里疾',
    # 异体字
    '硃家', '硃亥', '蒉聩',
    # 春秋战国大夫（补录第二轮发现）
    '师涓', '周兰', '中行文子', '贾季', '孔文子', '浑良夫',
    '成得臣', '楚靳尚', '楚申亥', '雍纠', '台骀', '甫假',
    '张仲', '类犴反', '弥子', '胡衍', '孟贲', '卞庄子',
    '楚昭阳', '楚若敖', '楚郏敖',
    '齐庆封', '微仲', '仇牧', '庸职', '竖刀', '田豹', '厓季载',
    '缯贺', '宋偃', '卫君起',
    # 汉代中层臣
    '赵周', '宋邑', '甘公', '霍嬗', '吕泽', '陈留', '徐甲',
    '许昌', '田广明', '范明友', '上官安', '李沮', '韩曾',
    '周兰', '富', '最', '指',
    '公孙光', '公孙奭', '乐臣公', '韩婴',
    '胜之', '魏子',
    # 秦末汉初
    '萧何', '张良', '韩信', '陈平', '周勃', '灌婴', '樊哙',
    '曹参', '王陵', '审食其', '审食其', '张苍', '任敖',
    '夏侯婴', '郦商', '傅宽', '靳歙', '叔孙通', '刘敬', '娄敬',
    '贯高', '赵王敖', '张耳', '陈馀', '英布', '彭越',
    '周亚夫', '周昌', '卢绾', '陆贾', '郦食其',
    # 文景武朝
    '袁盎', '晁错', '张释之', '冯唐', '石奋', '卫绾', '直不疑',
    '田叔', '窦婴', '田蚡', '韩安国', '公孙弘', '公孙贺',
    '李广', '程不识', '李蔡', '李广利',
    '卫青', '霍去病', '霍光', '公孙敖', '公孙贺', '赵信', '苏建',
    '主父偃', '朱买臣', '严助', '终军',
    '张汤', '赵禹', '郅都', '宁成', '义纵', '王温舒', '杜周',  # 酷吏归将相（他们是中央大员）
    # 补录（第三轮）
    # 战国大夫/使者
    '祝午',          # 齐郎中令
    '赵郝',          # 赵国使者
    '郑硃',          # 赵国使者入秦
    '田盼子',        # 齐将
    '王子城父',      # 齐将
    '郈昭伯',        # 鲁大夫
    '司马翦',        # 楚国策士（兼谋臣）
    '公仲侈',        # 韩相
    '廖',            # 秦内史廖
    '亲弗',          # 齐相
    '章子',          # 齐将
    '甘龙',          # 秦大夫
    '杜挚',          # 秦大夫
    '乐池',          # 相秦
    '斯离',          # 秦尉
    '司马梗',        # 秦将
    '公孙痤',        # 魏将
    '费昌',          # 秦先祖臣
    '智开',          # 智伯后人
    # 汉代臣
    '冯敬',          # 御史大夫
    '王恬开',        # 廷尉/梁相
    '张春',          # 陈豨将
    '张侈',          # 列侯
    '曹时',          # 平阳侯
    '曹宗',          # 平阳侯后代
    '柴武',          # 棘蒲侯/将军
    '吕齮',          # 南阳守
    '赵充',          # 太常
    '蒙嘉',          # 秦中庶子
    '袁种',          # 常侍骑
    '冯遂',          # 冯唐子
    '公孙度',        # 平津侯/郡守
    '庄参',          # 南越使者
    '尼谿参',        # 朝鲜相
    '宋襄',          # 宋义子，相齐
    '吕青',          # 令尹（陈涉军）
    '李当户',        # 李广子，郎
    '蕑忌',          # 中尉
    '乐叔',          # 华成君，乐毅孙
    '乐瑕公',        # 乐氏族人
    '司马靳',        # 武安君部将
    '司马昌',        # 秦主铁官
    '司马无泽',      # 汉市长
    '陶硃',          # 范蠡别名（货殖，此处作将相多标签）
    '田逆',          # 田氏族人
    '李宗',          # 老子子，魏将
    '李假',          # 李宗玄孙
    '张子房',        # 张良别名
    '郑忠',          # 劝止汉王渡河的郎中
    '周勣',          # 游说纵横士
    '周最',          # 六国策士
    '庄舄',          # 越人仕楚
    '宦者平',        # 仓公医案中宦者（归近臣，此处为将相兜底）
    # 司马家族祖先链
    '大廉',          # 嬴姓先祖
    '王廖',          # 兵家
    '翟景',          # 六国谋臣
    '齐明',          # 六国谋臣
    '杜赫',          # 六国谋臣
    '徐尚',          # 六国谋臣
    '乘', '周绾',    # 汉初臣
    '蒯通',          # 策士（已在 STRATEGIST）
}

# 谋臣策士
EXPLICIT_STRATEGIST = {
    '苏秦', '张仪', '公孙衍', '犀首',
    '苏代', '苏厉', '毛遂',
    '范雎', '蔡泽', '鲁仲连', '邹阳', '虞卿',
    '陈平', '陆贾', '郦食其', '蒯通', '随何',
    '侯生', '侯嬴', '朱亥',
    '娄敬', '刘敬',
    # 补录（第三轮）
    '司马翦',        # 谓楚王之策士
    '郑忠',          # 劝说汉王之郎中（策士兼臣）
    '茅焦',          # 劝说秦始皇之齐人策士
    '驺奭',          # 稷下先生（兼学者）
}

# 学者文士（诸子百家 + 博士 + 儒林 + 汉代文士）
EXPLICIT_SCHOLAR = {
    # 上古贤人
    '伯夷', '叔齐',
    # 儒家
    '孔子', '仲尼', '孔丘', '孟子', '孟轲', '荀子', '荀卿',
    '颜回', '子路', '子贡', '子夏', '子游', '曾子', '子张', '子思',
    '宰我', '冉有', '冉求', '公冶长', '子羔', '有若', '闵子骞',
    '漆雕开', '樊须', '公西华', '原宪', '澹台灭明',
    '商瞿', '端木赐', '高柴', '仲由', '卜商', '言偃',
    '颛孙师', '孔伋', '曾参', '冉雍', '冉伯牛',
    '仲弓', '公伯缭', '季子札',  # 季札=吴宗室
    # 其他先秦
    '老子', '李耳', '老聃', '墨子', '墨翟', '庄子', '庄周',
    '韩非', '韩非子', '慎到', '申不害', '公孙龙',
    '邹衍', '邹奭', '淳于髡',  # 稷下
    # 汉代儒林
    '申公', '辕固生', '伏生', '浮丘伯', '董仲舒', '胡毋生',
    '公孙弘',  # 既是儒也是丞相（多标签）
    # 汉代文学
    '贾谊', '贾生', '司马相如', '枚乘', '邹阳', '严助',
    '东方朔',  # 兼近臣奇人
    '司马谈', '司马迁',
    # 兵家
    '孙武', '孙子', '孙膑', '吴起', '司马穰苴',
    # 补录（第三轮）
    '驺奭',          # 稷下先生（与淳于髡等并列）
    '石申',          # 天文/星象学家（027_天官书）
    '鲋',            # 孔子后代，陈涉博士
    '颜路',          # 颜回父，仲尼弟子列传
    '樊迟', '樊须',  # 孔子弟子（仲尼弟子列传）
    '徐延',          # 儒林—礼官大夫之孙
    '徐襄',          # 儒林—礼官大夫之孙
    '越石父',        # 贤士（晏婴赎之）
    '接子',          # 稷下先生
    '环渊',          # 稷下先生
    '田骈',          # 稷下先生
    '唐举',          # 相者（近臣类，但多以方术学者身份出现）
    '石申夫',        # 魏国天文学家
    '养由基',        # 楚善射者（兵家/武士）
    '巫贤', '巫咸',  # 商代贤臣（近臣/学者）
    '费中',          # 纣之佞臣→近臣奇人，此处兼学者（方士）
}

# 地方官（循吏+酷吏+郡守县令）
EXPLICIT_LOCAL = {
    # 循吏
    '孙叔敖', '子产', '公仪休', '石奢', '李离',
    # 酷吏也标地方官（他们多出自郡守县令）
    '郅都', '宁成', '周阳由', '赵禹', '义纵', '王温舒',
    '尹齐', '杨仆', '减宣', '杜周',
    # 贤良地方官
    '汲黯', '郑当时', '黯',
}

# 刺客游侠
EXPLICIT_SWORDSMAN = {
    '曹沫', '专诸', '要离', '豫让', '聂政', '聂荣',
    '荆轲', '高渐离', '秦舞阳', '田光',
    '朱家', '田仲', '王孟', '剧孟', '郭解', '郭翁伯', '洛阳剧孟',
}

# 近臣奇人（佞幸+滑稽+方士+医者+日者+龟策）
EXPLICIT_COURTIER = {
    # 佞幸
    '籍孺', '闳孺', '邓通', '赵谈', '北宫伯子', '韩嫣', '韩说', '李延年',
    # 滑稽
    '淳于髡', '优孟', '优旃', '东方朔', '郭舍人', '西门豹',
    # 方士
    '宋毋忌', '正伯侨', '充尚', '羡门子高',
    '卢生', '韩众', '侯公', '徐福', '徐巿',
    '李少君', '少翁', '文成', '栾大', '公孙卿', '公孙', '五利', '五利将军',
    '宽舒', '丁夫人',
    # 医者
    '扁鹊', '秦越人', '仓公', '淳于意', '臣意',
    # 日者/龟策
    '司马季主', '宋忠', '贾谊日者', '卫平',
    # 补录（第三轮）
    '宦者平',        # 宦者，学淳于意医术
    '桑距',          # 诸侯幸臣
    '江充',          # 汉武帝近臣，告发太子
    '齐侍医遂',      # 齐王侍医
    '齐郎中令循',    # 仓公医案患者（近臣）
    '费中',          # 纣之佞臣
    '恶来',          # 纣之佞臣
    '唐举',          # 相者
    '阳庆子殷',      # 阳庆之子（扁鹊仓公传）
}

# 货殖商人
EXPLICIT_MERCHANT = {
    '陶朱公', '鸱夷子皮',
    '子贡',  # 也在学者（多标签）
    '白圭', '猗顿', '乌氏倮', '巴寡妇清',
    '范蠡',
    '程郑', '卓氏', '卓王孙', '任氏', '橋姚', '师史',
    '宛孔氏', '曹邴氏', '刁间', '周人', '秦扬',
    '吕不韦',  # 虽后入政，起家商贾（多标签）
    # 补录（第三轮）
    '陶硃',          # 范蠡别名（硃＝朱，variant未能自动匹配"陶朱公"）
    '刀间',          # 货殖列传中齐国商人（129章）
}

# 外邦（匈奴/南越/朝鲜/大宛/西南夷/东越）
EXPLICIT_FOREIGN = {
    # 匈奴单于
    '头曼', '冒顿', '冒顿单于', '老上', '老上单于', '军臣', '军臣单于',
    '伊稚斜', '伊稚斜单于', '乌维', '乌维单于', '兒单于',
    '句黎湖', '且鞮侯', '且鞮侯单于',
    # 匈奴贵族/贤王
    '昆邪王', '浑邪王', '休屠王', '赵信', '中行说', '卢侯王',
    '右贤王', '左贤王', '谷蠡王', '屠耆王',
    '于单', '乌师庐',
    # 南越
    '赵佗', '赵胡', '赵婴齐', '赵兴', '赵建德', '吕嘉',
    # 朝鲜
    '卫满', '右渠', '朝鲜王',
    # 东越
    '无诸', '摇', '驺力',
    # 西南夷
    '夜郎王', '滇王', '邛君', '笮侯',
    # 大宛
    '昆莫', '军须靡', '蝉封', '毋寡',
}

# 上古神话
EXPLICIT_MYTHICAL = {
    '女娲', '共工', '祝融', '句芒', '蓐收', '玄冥',
    '后土', '风后', '力牧', '大鸿',
    '重黎', '吴回', '陆终', '昆吾',
    '太昊', '神农', '炎帝', '蚩尤',
    '简狄', '姜原', '有娀氏', '有邰氏',
    # 上古贤人辅佐
    '皋陶', '大禹', '伯益', '益', '伯夷', '后稷', '弃',
    '契', '伯禹', '共工', '驩兜', '三苗', '鲧',
    # 补录（第三轮）：001_五帝本纪相关上古人物
    '八恺', '八元',  # 高阳氏/高辛氏八才子（泛称）
    '硃虎', '熊罴',  # 舜帝臣
    '青阳',          # 黄帝子（与上古神话相关，归此）
    '嫘祖',          # 黄帝妃（与后妃重叠，此处上古语境）
    '羿',            # 古弓箭英雄（夏代）
    '简狄',          # 殷契母
    '奄息', '仲行', '针虎',  # 秦穆公殉葬三人（子舆氏）
    '臣扈', '伊陟', '巫咸', '巫贤',  # 商代贤臣
}

# 家臣门客
EXPLICIT_RETAINER = {
    '冯驩', '毛遂', '朱亥', '侯嬴', '夷门监',
    '唐雎', '宾孟', '安陵君',
    '魏武子', '程婴', '公孙杵臼', '赵朔', '赵武',  # 赵氏孤儿
    '豫让',  # 兼刺客
    # 补录（第三轮）
    '毛公',          # 信陵君门下处士
    '薛公',          # 卖浆家隐士（信陵君门下）
    '越石父',        # 贤士（晏婴所赎）→ 兼 学者文士
}

# 平民刑徒
EXPLICIT_COMMONER = {
    '陈涉', '陈胜', '吴广', '葛婴',
    '武臣', '韩广', '田儋', '田横',
    '英布',  # 骊山刑徒出身，起义后封王（多标签）
    '彭越',  # 大泽起义
    '项梁', '项羽', '项伯', '项庄',  # 楚国遗民起义
    # 补录（第三轮）
    '王仲',          # 王太后之夫（普通人）
    '金王孙',        # 王太后前夫家
    '陈伯',          # 陈平兄（农夫）
}

# 虚构寓言
EXPLICIT_FICTIONAL = {
    '子虚', '乌有先生', '亡是公',
    '无是公', '罔两', '河伯',  # 河伯偶指人物名
}

# 待拆分（官职+人名 或 国名+官职+人名 复合）
EXPLICIT_SPLIT = {
    '秦樗里疾',       # 秦 + 樗里疾
    '秦张仪', '魏相田文', '纵横家陈轸',
    '齐中御府长信',   # 齐 + 中御府 + 长信
    '路中大夫',       # 路 + 中大夫
    '太公望吕尚',     # 太公望 + 吕尚（兼宗室）
    '卫庄公蒯聩',     # 卫庄公 + 蒯聩
    '卫共伯馀',       # 卫共伯 + 馀
}

# 误标（单字常见动词/副词被误标）
EXPLICIT_MIS = {
    '则', '它', '始', '执', '苏', '最', '指', '买', '应',
    '富', '胜', '立', '成', '得', '使', '见', '可',
    '上', '下', '子',  # '子' 很常见但多数是人名后缀
    '五帝',  # 是泛称，非具体人
}


# ─── 后缀启发式 ───
SUFFIX_RULES = [
    # (后缀长度, 后缀, 类别)
    (2, '单于', CAT_FOREIGN),
    (2, '贤王', CAT_FOREIGN),
    (3, '昆邪王', CAT_FOREIGN),
    (3, '休屠王', CAT_FOREIGN),
    (3, '浑邪王', CAT_FOREIGN),
    (2, '右王', CAT_FOREIGN),
    (2, '左王', CAT_FOREIGN),
    (3, '谷蠡王', CAT_FOREIGN),
    (3, '屠耆王', CAT_FOREIGN),
    (2, '夫人', CAT_CONSORT),
    (2, '太后', CAT_CONSORT),
    (2, '王后', CAT_CONSORT),
    (2, '皇后', CAT_CONSORT),
    (1, '姬', CAT_CONSORT),
    (2, '公子', CAT_PRINCE),
    (2, '太子', CAT_PRINCE),
    (2, '王子', CAT_PRINCE),
    # 爵号后缀（弱）—— 只有当其他规则未匹配时才用
    # X侯/X君 的默认归类在 L4 末尾处理
]


# ─── 侯者年表章节（L2 → 将相/宗室）───
# 018 高祖功臣 / 019 惠景间 / 020 建元以来 — 汉代列侯，多是将相
# 021 建元已来王子 — 汉诸侯王子，归宗室
HOUZHE_HAN_FUNCTIONARY = {'018_高祖功臣侯者年表', '019_惠景间侯者年表', '020_建元以来侯者年表'}
HOUZHE_HAN_PRINCE = {'021_建元已来王子侯者年表'}


# ─── L2 章节上下文规则 ───
# 专题列传 → 默认类别（仅适用于 ref 在该章节出现频次占比 ≥ 50% 的情况）
THEMATIC_CHAPTERS = {
    '086_刺客列传': CAT_SWORDSMAN,
    '105_扁鹊仓公列传': CAT_COURTIER,
    '110_匈奴列传': CAT_FOREIGN,
    '113_南越列传': CAT_FOREIGN,
    '114_东越列传': CAT_FOREIGN,
    '115_朝鲜列传': CAT_FOREIGN,
    '116_西南夷列传': CAT_FOREIGN,
    '119_循吏列传': CAT_LOCAL,
    '121_儒林列传': CAT_SCHOLAR,
    '122_酷吏列传': CAT_LOCAL,
    '123_大宛列传': CAT_FOREIGN,
    '124_游侠列传': CAT_SWORDSMAN,
    '125_佞幸列传': CAT_COURTIER,
    '126_滑稽列传': CAT_COURTIER,
    '127_日者列传': CAT_COURTIER,
    '128_龟策列传': CAT_COURTIER,
    '129_货殖列传': CAT_MERCHANT,
    # 补录（第三轮）：孔子弟子列传 → 学者文士
    '067_仲尼弟子列传': CAT_SCHOLAR,
    # 本纪 → 帝王（主人公）
    '001_五帝本纪': CAT_EMPEROR,
    '002_夏本纪': CAT_EMPEROR,
    '003_殷本纪': CAT_EMPEROR,
    '004_周本纪': CAT_EMPEROR,
    '005_秦本纪': CAT_RULER,  # 秦早期为诸侯
    '006_秦始皇本纪': CAT_EMPEROR,
    '007_项羽本纪': CAT_COMMONER,  # 项羽自称西楚霸王，起家是起义者
    '008_高祖本纪': CAT_EMPEROR,
    '009_吕太后本纪': CAT_CONSORT,
    '010_孝文本纪': CAT_EMPEROR,
    '011_孝景本纪': CAT_EMPEROR,
    '012_孝武本纪': CAT_EMPEROR,
}

# 世家章（031-060 默认诸侯君主主人公）
WORLDFAMILY_CHAPTERS = [f'{i:03d}' for i in range(31, 61)]


# ─── person.ttl 本体类 → 16 类映射 ───
# owl:Class → (category, priority)
TTL_CLASS_MAP = {
    # 王室
    '帝王': CAT_EMPEROR,
    '诸侯': CAT_RULER,
    '后妃': CAT_CONSORT,
    '宗室': CAT_PRINCE,
    '先秦后妃': CAT_CONSORT,
    '汉后妃': CAT_CONSORT,
    '吴楚七国': CAT_PRINCE,  # 吴楚七国诸侯王属宗室（刘氏）
    '淮南衡山': CAT_PRINCE,
    # 臣的时代子类 → 默认将相
    '战国': CAT_CHANCELLOR,
    '春秋': CAT_CHANCELLOR,
    '楚汉': CAT_CHANCELLOR,
    '汉中后': CAT_CHANCELLOR,
    '汉初': CAT_CHANCELLOR,
    '秦': CAT_CHANCELLOR,
    '先秦早期': CAT_CHANCELLOR,
    '越国臣子': CAT_CHANCELLOR,
    # 三代/五帝时代
    '三代': CAT_EMPEROR,  # 三代往往是帝王或贤臣；主归帝王
    '五帝时代': CAT_EMPEROR,
    '商代': CAT_CHANCELLOR,
    '夏代': CAT_CHANCELLOR,
    '商代名臣': CAT_CHANCELLOR,
    '西周': CAT_CHANCELLOR,
    # 刘邦阵营
    '刘邦阵营': CAT_CHANCELLOR,
    '刘邦文臣': CAT_CHANCELLOR,
    '刘邦武将': CAT_CHANCELLOR,
    '项羽阵营': CAT_CHANCELLOR,
    # 吕氏集团、汉初诸将
    '吕氏集团': CAT_PRINCE,
    '汉初诸将': CAT_CHANCELLOR,
    # 朝臣
    '文帝朝臣': CAT_CHANCELLOR,
    '文景朝臣': CAT_CHANCELLOR,
    '文景武朝臣': CAT_CHANCELLOR,
    '景帝朝臣': CAT_CHANCELLOR,
    '武帝朝臣': CAT_CHANCELLOR,
    '武帝将领': CAT_CHANCELLOR,
    '武帝文臣': CAT_CHANCELLOR,
    '汉其他': CAT_CHANCELLOR,
    # 秦国
    '秦朝将领': CAT_CHANCELLOR,
    '秦朝权臣': CAT_CHANCELLOR,
    '秦朝重臣': CAT_CHANCELLOR,
    '秦末起义': CAT_COMMONER,
    '秦国先祖': CAT_RULER,
    '秦国将领': CAT_CHANCELLOR,
    '秦国相臣': CAT_CHANCELLOR,
    '秦国臣子': CAT_CHANCELLOR,
    # 战国各国
    '晋国臣子': CAT_CHANCELLOR,
    '晋国世族': CAT_CHANCELLOR,
    '晋国六卿': CAT_CHANCELLOR,
    '晋国卿大夫': CAT_CHANCELLOR,
    '晋国宗室': CAT_PRINCE,
    '晋国将领': CAT_CHANCELLOR,
    '晋国谋臣': CAT_STRATEGIST,
    '楚国臣子': CAT_CHANCELLOR,
    '楚国权贵': CAT_CHANCELLOR,
    '燕国臣子': CAT_CHANCELLOR,
    '赵国臣子': CAT_CHANCELLOR,
    '韩国臣子': CAT_CHANCELLOR,
    '魏国臣子': CAT_CHANCELLOR,
    '齐国田氏臣子': CAT_CHANCELLOR,
    '齐国臣子': CAT_CHANCELLOR,
    # 春秋诸国臣子
    '卫国臣子': CAT_CHANCELLOR,
    '吴国臣子': CAT_CHANCELLOR,
    '吴楚臣子': CAT_CHANCELLOR,
    '宋国臣子': CAT_CHANCELLOR,
    '管蔡臣子': CAT_CHANCELLOR,
    '郑国臣子': CAT_CHANCELLOR,
    '陈国臣子': CAT_CHANCELLOR,
    '鲁国臣子': CAT_CHANCELLOR,
    # 策士
    '策士': CAT_STRATEGIST,
    # 诸子百家
    '儒生': CAT_SCHOLAR,
    '孔门弟子': CAT_SCHOLAR,
    '汉儒': CAT_SCHOLAR,
    '法家': CAT_SCHOLAR,
    '兵家': CAT_SCHOLAR,
    '思想家': CAT_SCHOLAR,
    '文学家': CAT_SCHOLAR,
    '隐士': CAT_SCHOLAR,
    '史家': CAT_SCHOLAR,
    # 社会人物
    '刺客': CAT_SWORDSMAN,
    '游侠': CAT_SWORDSMAN,
    '滑稽': CAT_COURTIER,
    '佞幸': CAT_COURTIER,
    '商贾': CAT_MERCHANT,
    # 方术
    '方士': CAT_COURTIER,
    '医者': CAT_COURTIER,
    '日者龟策': CAT_COURTIER,
    # 外邦
    '匈奴': CAT_FOREIGN,
    '大宛西域': CAT_FOREIGN,
    '南越': CAT_FOREIGN,
    '朝鲜': CAT_FOREIGN,
    '东越': CAT_FOREIGN,
    '西南夷': CAT_FOREIGN,
    # 虚构
    '虚构人物': CAT_FICTIONAL,
    # 疑似误标
    '疑似误标': CAT_MIS,
    '无国名谥号': CAT_MIS,
    '后妃相关': CAT_MIS,
    '吴国': CAT_MIS,
    '燕国': CAT_MIS,
    '赵国': CAT_MIS,
    '鲁国': CAT_MIS,
    '齐国': CAT_MIS,
    # 上古
    '上古': CAT_EMPEROR,
    '周': CAT_EMPEROR,
    '商': CAT_EMPEROR,
    '夏': CAT_EMPEROR,
    '晋国': CAT_RULER,   # 晋国诸侯君主
    '楚国': CAT_RULER,
    '汉': CAT_EMPEROR,
    '秦朝': CAT_EMPEROR,
}


# ─── 数据加载 ───

# 异体字归一化表（成对映射）
VARIANT_NORMALIZE = {
    '朱': '硃', '硃': '朱',
    '勾': '句', '句': '勾',
    '釐': '僖', '僖': '釐',
    '閭': '闾', '闾': '閭',
    '谿': '溪', '溪': '谿',
}


def variant_forms(name):
    """生成名字的异体字变形集合（包括原名）。"""
    forms = {name}
    for i, ch in enumerate(name):
        if ch in VARIANT_NORMALIZE:
            alt = name[:i] + VARIANT_NORMALIZE[ch] + name[i+1:]
            forms.add(alt)
    return forms


def load_rulers_map():
    """rulers.json → {canonical: cat}。对每条 ruler 注册多种形式：
    - 谥号（如 '襄公'）
    - 所属国+谥号（如 '秦襄公'）
    - 名（如 '句践'）
    - 别名（如 '越王句践'）
    """
    mapping = defaultdict(list)
    if not RULERS_JSON.exists():
        return mapping
    with open(RULERS_JSON, encoding='utf-8') as f:
        data = json.load(f)
    for r in data.get('rulers', []):
        t = r.get('类型', '')
        sh = (r.get('谥号') or '').strip()
        nm = (r.get('名') or '').strip()
        state = (r.get('所属国') or '').strip()
        al = r.get('别名')
        if isinstance(al, str):
            al = [al]
        elif not isinstance(al, list):
            al = []

        if t == '天子/皇帝':
            cat = CAT_EMPEROR
        elif t in ('诸侯王', '诸侯侯君'):
            cat = CAT_RULER
        elif t == '汉诸侯王':
            cat = CAT_PRINCE
        elif t == '单于':
            cat = CAT_FOREIGN
        elif t in ('晋卿大夫', '齐卿大夫'):
            cat = CAT_CHANCELLOR
        elif t == '先祖':
            cat = CAT_EMPEROR
        else:
            continue

        # 去掉国名注释（如 '齐（田齐）' → '齐'）
        state_clean = re.sub(r'[（(][^）)]*[）)]', '', state).strip()

        forms = set()
        if sh:
            # 原 谥号 + 剥 paren + paren 内部
            forms.add(sh)
            sh_stripped = re.sub(r'[（(][^）)]*[）)]', '', sh).strip()
            if sh_stripped and sh_stripped != sh:
                forms.add(sh_stripped)
            # paren 内的内容（如 "赵王（赵敬肃王）" → "赵敬肃王"）
            for inner in re.findall(r'[（(]([^）)]+)[）)]', sh):
                inner = inner.strip()
                if inner:
                    forms.add(inner)
            # 加 state 前缀
            if state_clean:
                forms.add(state_clean + sh_stripped)
        if nm:
            forms.add(nm)
            if state_clean and sh and sh != nm:
                forms.add(state_clean + nm)
        for a in al:
            a = (a or '').strip()
            if a:
                forms.add(a)

        # 扩展异体字变形
        expanded_forms = set()
        for f in forms:
            expanded_forms.update(variant_forms(f))
        for f in expanded_forms:
            if f and cat not in mapping[f]:
                mapping[f].append(cat)
    return mapping


def load_ttl_map():
    """person.ttl → {canonical: cat}（吃本体分类）"""
    mapping = {}
    if not PERSON_TTL.exists():
        return mapping
    content = PERSON_TTL.read_text(encoding='utf-8')
    # 匹配 per:X a per:Y ; ...
    for m in re.finditer(r'^per:(\S+)\s+a\s+per:(\S+)\s*;', content, re.MULTILINE):
        name = m.group(1)
        cls = m.group(2)
        if cls in TTL_CLASS_MAP:
            # 为每个名字生成异体字变形
            for form in variant_forms(name):
                mapping.setdefault(form, []).append(TTL_CLASS_MAP[cls])
    return mapping


def load_alias_map():
    """entity_aliases.json (新 4 列结构) → {surface: [canonical, ...]}。
    用于 L2.5 alias 继承：未分类 surface 继承其 canonical 的类别。
    """
    mapping = defaultdict(list)
    if not ALIAS_JSON.exists():
        return mapping
    with open(ALIAS_JSON, encoding='utf-8') as f:
        data = json.load(f)
    rows = data.get('person', [])
    if not isinstance(rows, list):
        return mapping
    for r in rows:
        surface = r.get('surface', '').strip()
        canonical = r.get('canonical', '').strip()
        if surface and canonical and surface != canonical:
            if canonical not in mapping[surface]:
                mapping[surface].append(canonical)
    return mapping


def load_shihao_map():
    """shihao_index.json → 归入 诸侯君主"""
    mapping = {}
    if not SHIHAO_JSON.exists():
        return mapping
    with open(SHIHAO_JSON, encoding='utf-8') as f:
        data = json.load(f)
    # 结构可能是 {"shihao": [...]} 或 {name: {...}}；先扫所有 key
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, dict) and '类型' in v:
                # skip — 不直接映射
                pass
    return mapping


def load_chapters_content():
    """加载 chapter_md 全文，用于 L3 共现匹配。"""
    content_by_chap = {}
    for f in sorted(CHAPTER_DIR.glob('*.tagged.md')):
        chap = f.stem.replace('.tagged', '')
        content_by_chap[chap] = f.read_text(encoding='utf-8')
    return content_by_chap


# ─── L3 共现模式 ───
# 每个模式：(regex_pattern, cat, 说明)。{NAME} 会被替换为 re.escape(canonical)。
L3_CONTEXT_PATTERNS = [
    # 君主相关
    (r'〖@{NAME}〗⟦○立⟧', CAT_RULER),
    (r'⟦○立⟧〖@{NAME}〗', CAT_RULER),
    (r'〖@{NAME}〗⟦○即位⟧', CAT_RULER),
    (r'〖@{NAME}〗⟦○崩⟧', CAT_EMPEROR),  # 崩 专用天子
    (r'〖@{NAME}〗⟦○薨⟧', CAT_RULER),   # 薨 诸侯
    (r'⟦◉弑⟧〖@{NAME}〗', CAT_RULER),   # 被弑多为君主
    (r'〖@{NAME}〗元年', CAT_RULER),     # "X元年" X是纪元君主
    (r'〖@{NAME}〗〖%.+?〗年', CAT_RULER),  # 〖@X〗〖%N〗年
    # 将相相关
    (r'〖@{NAME}〗为〖;丞相〗', CAT_CHANCELLOR),
    (r'〖@{NAME}〗为〖;相国〗', CAT_CHANCELLOR),
    (r'〖@{NAME}〗为〖;御史大夫〗', CAT_CHANCELLOR),
    (r'〖@{NAME}〗为〖;太尉〗', CAT_CHANCELLOR),
    (r'拜〖@{NAME}〗为〖;丞相〗', CAT_CHANCELLOR),
    (r'〖;丞相〗〖@{NAME}〗', CAT_CHANCELLOR),
    (r'〖;相〗〖@{NAME}〗', CAT_CHANCELLOR),
    # 将军
    (r'拜〖@{NAME}〗为〖;.*?将军〗', CAT_CHANCELLOR),
    (r'〖@{NAME}〗为〖;.*?将军〗', CAT_CHANCELLOR),
    (r'〖;.*?将军〗〖@{NAME}〗', CAT_CHANCELLOR),
    (r'〖@{NAME}〗将兵', CAT_CHANCELLOR),
    (r'〖@{NAME}〗将〖\$.+?〗', CAT_CHANCELLOR),  # X 将 N 万
    # 学者
    (r'〖;博士〗〖@{NAME}〗', CAT_SCHOLAR),
    (r'〖@{NAME}〗为〖;博士〗', CAT_SCHOLAR),
    (r'〖@{NAME}〗治〖\{.+?〗', CAT_SCHOLAR),  # X治《春秋》等
    # 后妃
    (r'〖@{NAME}〗生', CAT_CONSORT),  # X生子
    # 近臣奇人
    (r'〖;幸臣〗〖@{NAME}〗', CAT_COURTIER),    # 幸臣X
    (r'〖#宦者〗〖@{NAME}〗', CAT_COURTIER),    # 宦者X
    (r'〖;侍医〗〖@{NAME}〗', CAT_COURTIER),    # 侍医X
    # 郡守/地方官
    (r'〖@{NAME}〗为〖;.*?太守〗', CAT_LOCAL),
    (r'〖;.*?太守〗〖@{NAME}〗', CAT_LOCAL),
    (r'〖@{NAME}〗为〖;.*?令〗', CAT_LOCAL),
]


def apply_l3(canonical, chapters_content, refs):
    """L3：共现模式扫描。返回 [(cat, score)] 列表。"""
    votes = Counter()
    chaps_to_check = set(r[0] for r in refs[:30])  # 限制扫描范围
    for chap in chaps_to_check:
        content = chapters_content.get(chap, '')
        if not content:
            continue
        name_esc = re.escape(canonical)
        for pat_tpl, cat in L3_CONTEXT_PATTERNS:
            pat = pat_tpl.replace('{NAME}', name_esc)
            n = len(re.findall(pat, content))
            if n > 0:
                votes[cat] += n
    return votes


# ─── 分类逻辑 ───

def apply_l1(canonical, explicit_maps):
    """L1：显式白名单命中"""
    cats = []
    for white_set, cat in explicit_maps:
        if canonical in white_set:
            if cat not in cats:
                cats.append(cat)
    return cats


def apply_l2(canonical, refs, thematic_chapters):
    """L2：章节上下文——某章占比 ≥ 50% 且 ≥ 2 次 → 归入该章默认类"""
    if not refs:
        return []
    chap_count = Counter(r[0] for r in refs)
    total = len(refs)
    for chap, n in chap_count.items():
        if chap in thematic_chapters and n >= 2 and n / total >= 0.5:
            return [thematic_chapters[chap]]
    return []


def apply_l2_houzhe(canonical, refs):
    """L2 侯者年表启发式：refs 在 018-020（汉代功臣侯者年表）占比 ≥ 50% → 将相；
    refs 在 021（建元已来王子）占比 ≥ 50% → 宗室。
    阈值参数：HOUZHE_MIN_REFS = 1（大量冷僻侯国只在年表出现一次）。
    """
    if not refs:
        return []
    chap_count = Counter(r[0] for r in refs)
    total = len(refs)
    func_hits = sum(n for c, n in chap_count.items() if c in HOUZHE_HAN_FUNCTIONARY)
    prince_hits = sum(n for c, n in chap_count.items() if c in HOUZHE_HAN_PRINCE)
    if prince_hits >= 1 and prince_hits / total >= 0.5:
        return [CAT_PRINCE]
    if func_hits >= 1 and func_hits / total >= 0.5:
        return [CAT_CHANCELLOR]
    return []


def apply_l4(canonical):
    """L4：后缀启发式"""
    for length, suffix, cat in SUFFIX_RULES:
        if len(canonical) > length and canonical.endswith(suffix):
            return [cat]
        if canonical == suffix:  # 纯后缀词（单独出现）
            return [cat]
    # 爵号后缀弱规则
    if canonical.endswith('侯') and len(canonical) >= 2 and len(canonical) <= 4:
        # 非"列侯/彻侯"等泛称（那些是 official）
        if canonical not in ('侯',):
            return [CAT_CHANCELLOR]  # 汉代列侯多是功臣
    if canonical.endswith('君') and len(canonical) >= 2 and len(canonical) <= 4:
        if canonical not in ('君',):
            return [CAT_CHANCELLOR]
    # 〖@公子X〗或 〖@X公子〗
    if '公子' in canonical:
        return [CAT_PRINCE]
    # 刘X（2-3字）→ 汉代皇族，归宗室
    if canonical.startswith('刘') and 2 <= len(canonical) <= 3:
        return [CAT_PRINCE]
    # X王（2-3字）先秦诸侯弱规则：X 是邦国单字时归诸侯君主
    if canonical.endswith('王') and 2 <= len(canonical) <= 3:
        first = canonical[0]
        if first in '齐楚燕赵韩魏秦吴越晋郑宋卫鲁陈蔡曹滕许邾莒徐虢':
            return [CAT_RULER]
    # X公（2-3字）春秋诸侯
    if canonical.endswith('公') and 2 <= len(canonical) <= 3:
        first = canonical[0]
        if first in '齐楚燕赵韩魏秦吴越晋郑宋卫鲁陈蔡曹滕许邾莒徐虢':
            return [CAT_RULER]
    # 国名+人名 复合（如 "楚昭阳"="楚"+"昭阳"）
    # X 为邦国单字，Y 非君主后缀 → 将相
    if len(canonical) == 3:
        first = canonical[0]
        last = canonical[-1]
        if first in '齐楚燕赵韩魏秦吴越晋郑宋卫鲁陈蔡' and last not in '王公侯君姬父':
            return [CAT_CHANCELLOR]
    return []


def merge_cats(*cat_lists):
    """合并多来源类别，去重，按优先级升序排列。"""
    seen = set()
    merged = []
    for lst in cat_lists:
        for cat in lst:
            name = cat[0]
            if name not in seen:
                seen.add(name)
                merged.append(cat)
    merged.sort(key=lambda c: c[1])
    return merged


def classify_person(canonical, entity_info, ttl_map, rulers_map, chapters_content=None):
    """对单个 person 实体分类，返回类别列表（按优先级升序）。"""
    refs = entity_info.get('refs', [])

    # L1: 白名单 + ttl + rulers
    l1_cats = []
    explicit_whitelists = [
        (EXPLICIT_EMPEROR, CAT_EMPEROR),
        (EXPLICIT_RULER, CAT_RULER),
        (EXPLICIT_CONSORT, CAT_CONSORT),
        (EXPLICIT_PRINCE, CAT_PRINCE),
        (EXPLICIT_CHANCELLOR, CAT_CHANCELLOR),
        (EXPLICIT_STRATEGIST, CAT_STRATEGIST),
        (EXPLICIT_SCHOLAR, CAT_SCHOLAR),
        (EXPLICIT_LOCAL, CAT_LOCAL),
        (EXPLICIT_SWORDSMAN, CAT_SWORDSMAN),
        (EXPLICIT_COURTIER, CAT_COURTIER),
        (EXPLICIT_MERCHANT, CAT_MERCHANT),
        (EXPLICIT_FOREIGN, CAT_FOREIGN),
        (EXPLICIT_MYTHICAL, CAT_MYTHICAL),
        (EXPLICIT_RETAINER, CAT_RETAINER),
        (EXPLICIT_COMMONER, CAT_COMMONER),
        (EXPLICIT_FICTIONAL, CAT_FICTIONAL),
        (EXPLICIT_SPLIT, CAT_SPLIT),
        (EXPLICIT_MIS, CAT_MIS),
    ]
    l1_cats = apply_l1(canonical, explicit_whitelists)

    # TTL/rulers 追加
    if canonical in ttl_map:
        for cat in ttl_map[canonical]:
            if cat not in l1_cats:
                l1_cats.append(cat)
    if canonical in rulers_map:
        for cat in rulers_map[canonical]:
            if cat not in l1_cats:
                l1_cats.append(cat)

    # L2: 章节上下文（仅当 L1 为空时兜底）
    l2_cats = []
    if not l1_cats:
        l2_cats = apply_l2(canonical, refs, THEMATIC_CHAPTERS)
        if not l2_cats:
            l2_cats = apply_l2_houzhe(canonical, refs)

    # L3: 共现模式（仅当 L1/L2 均为空时用 L3 作主要线索）
    l3_cats = []
    if not l1_cats and not l2_cats and chapters_content:
        votes = apply_l3(canonical, chapters_content, refs)
        if votes:
            # 投票数 ≥ 2 的类别才采纳
            for cat, n in votes.most_common():
                if n >= 2:
                    l3_cats.append(cat)
                    break  # 只取最高票
            if not l3_cats and len(refs) <= 3:
                # refs 少时，1 票也可
                for cat, n in votes.most_common(1):
                    l3_cats.append(cat)

    # L4: 后缀
    l4_cats = apply_l4(canonical)

    # 合并
    merged = merge_cats(l1_cats, l2_cats, l3_cats, l4_cats)

    return merged


def main():
    print('[1/4] 加载 entity_index.json ...', file=sys.stderr)
    with open(INDEX_JSON, encoding='utf-8') as f:
        index = json.load(f)
    persons = index.get('person', {})
    print(f'      → {len(persons)} 人', file=sys.stderr)

    print('[2/4] 加载 person.ttl 本体分类 ...', file=sys.stderr)
    ttl_map = load_ttl_map()
    print(f'      → {len(ttl_map)} 条 TTL 分类', file=sys.stderr)

    print('[3/5] 加载 rulers.json ...', file=sys.stderr)
    rulers_map = load_rulers_map()
    print(f'      → {len(rulers_map)} 条君主', file=sys.stderr)

    print('[4/5] 加载 entity_aliases.json (L2.5 alias 继承) ...', file=sys.stderr)
    alias_map = load_alias_map()
    print(f'      → {len(alias_map)} 条 surface→canonical', file=sys.stderr)

    print('[5/6] 加载 chapter_md 内容（用于 L3 共现）...', file=sys.stderr)
    chapters_content = load_chapters_content()
    print(f'      → {len(chapters_content)} 个章节', file=sys.stderr)

    print('[6/6] 逐个分类 ...', file=sys.stderr)
    categories = {}
    confidence = {}
    cat_counter = Counter()
    unclassified = []

    # 第一遍：L1 + L2 + L3 + L4
    for canonical, info in persons.items():
        cats = classify_person(canonical, info, ttl_map, rulers_map, chapters_content)
        if cats:
            categories[canonical] = [c[0] for c in cats]
            # 置信度：L1 来源高、L2 来源中、L4 来源低
            if canonical in ttl_map or any(canonical in w[0] for w in [
                (EXPLICIT_EMPEROR, 0), (EXPLICIT_RULER, 0), (EXPLICIT_CONSORT, 0),
                (EXPLICIT_PRINCE, 0), (EXPLICIT_CHANCELLOR, 0), (EXPLICIT_STRATEGIST, 0),
                (EXPLICIT_SCHOLAR, 0), (EXPLICIT_LOCAL, 0), (EXPLICIT_SWORDSMAN, 0),
                (EXPLICIT_COURTIER, 0), (EXPLICIT_MERCHANT, 0), (EXPLICIT_FOREIGN, 0),
                (EXPLICIT_MYTHICAL, 0), (EXPLICIT_RETAINER, 0), (EXPLICIT_COMMONER, 0),
                (EXPLICIT_FICTIONAL, 0),
            ]):
                conf = 0.95
            else:
                conf = 0.6
            confidence[canonical] = {cats[0][0]: conf}
            cat_counter[cats[0][0]] += 1
        else:
            unclassified.append(canonical)

    # 第二遍：L2.5 alias 继承（多轮，直到收敛）
    alias_inherit_count = 0
    for _ in range(3):  # 最多 3 轮传播
        changed = False
        for name in list(unclassified):
            if name in categories:
                continue
            if name in alias_map:
                # 继承第一个已分类 canonical 的类别
                for target in alias_map[name]:
                    if target in categories:
                        categories[name] = list(categories[target])
                        confidence[name] = {categories[name][0]: 0.7}  # 继承置信度稍低
                        alias_inherit_count += 1
                        changed = True
                        break
        if not changed:
            break

    # 重算 unclassified 与 cat_counter
    unclassified = [n for n in persons if n not in categories]
    cat_counter = Counter()
    for name in persons:
        if name in categories:
            cat_counter[categories[name][0]] += 1
        else:
            cat_counter['(未分类)'] += 1

    print(f'\nL2.5 alias 继承补充: {alias_inherit_count} 条', file=sys.stderr)

    # 输出
    with open(OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(categories, f, ensure_ascii=False, indent=2)
    with open(OUT_CONF_JSON, 'w', encoding='utf-8') as f:
        json.dump(confidence, f, ensure_ascii=False, indent=2)

    print('\n== 分类分布 ==', file=sys.stderr)
    for cat_name, n in sorted(cat_counter.items(), key=lambda x: -x[1]):
        pct = n / len(persons) * 100
        print(f'  {cat_name}: {n} ({pct:.1f}%)', file=sys.stderr)
    print(f'\n写入 {OUT_JSON.relative_to(_ROOT)}', file=sys.stderr)
    print(f'写入 {OUT_CONF_JSON.relative_to(_ROOT)}', file=sys.stderr)


if __name__ == '__main__':
    main()
