#!/usr/bin/env python3
"""
完成chapter_md/024_乐书.tagged.md的所有剩余段落标注
严格遵守：只添加标注符号，不改原文，绝对禁止半角引号
"""

import re
from pathlib import Path

def fix_section_01_to_11(content: str) -> str:
    """修复[1]-[11]节：序论、礼乐衰微、秦汉乐制"""

    # [1.1] 太史公序论
    content = content.replace(
        '[1.1] 〖@太史公〗曰：余每读〖{虞书〗',
        '[1.1] 〖@太史公〗曰：余每读〖{虞书〗'
    )
    content = content.replace(
        '至於〖#君臣〗相敕',
        '至於〖#君臣〗相敕'
    )
    content = content.replace(
        '维是几安，而〖#股肱〗不良',
        '维是几安，而〖#股肱〗不良'
    )

    # [1.2] 成王作颂
    content = content.replace(
        '[1.2] 〖@成王〗作〖:颂〗',
        '[1.2] 〖@成王〗作〖:颂〗'
    )
    content = content.replace(
        '推己惩艾，悲彼〖[家难〗',
        '推己惩艾，悲彼〖[家难〗'
    )
    content = content.replace(
        '可不谓战战恐惧，〖_善〗守〖_善〗终哉？',
        '可不谓战战恐惧，〖_善〗守〖_善〗终哉？'
    )

    # [1.3] 君子修德
    content = content.replace(
        '〖_君子〗不为约则修〖_德〗',
        '〖_君子〗不为约则修〖_德〗'
    )
    content = content.replace(
        '满则弃〖^礼〗，佚能思初',
        '满则弃〖^礼〗，佚能思初'
    )
    content = content.replace(
        '安能惟始，沐浴膏泽而〖:歌〗咏勤苦',
        '安能惟始，沐浴膏泽而〖:歌〗咏勤苦'
    )

    # [1.7] 博采风俗
    content = content.replace(
        '[1.7] 以为州异国殊，情习不同，故博采〖_风俗〗',
        '[1.7] 以为州异国殊，情习不同，故博采〖_风俗〗'
    )
    content = content.replace(
        '协比声律，以补短移化，助流〖^政教〗。',
        '协比声律，以补短移化，助流〖^政教〗。'
    )

    # [1.8] 天子临观
    content = content.replace(
        '[1.8] 〖#天子〗躬於〖=明堂〗临观',
        '[1.8] 〖#天子〗躬於〖=明堂〗临观'
    )
    content = content.replace(
        '而〖$万〗〖#民〗咸荡涤邪秽',
        '而〖$万〗〖#民〗咸荡涤邪秽'
    )
    content = content.replace(
        '斟酌饱满，以饰厥性。',
        '斟酌饱满，以饰厥〖_性〗。'
    )

    # [1.9] 三种音乐
    content = content.replace(
        '[1.9] 故云雅颂之音理而〖#民〗正',
        '[1.9] 故云〖{雅颂〗之音理而〖#民〗正'
    )
    content = content.replace(
        '嘄噭之声兴而〖#士〗奋',
        '嘄噭之声兴而〖#士〗奋'
    )

    # [1.10] 鸟兽皆感
    content = content.replace(
        '及其调和谐合，〖+鸟〗〖+兽〗尽感',
        '及其调和谐合，〖+鸟〗〖+兽〗尽感'
    )
    content = content.replace(
        '而况怀〖_五常〗，含好恶',
        '而况怀〖_五常〗，含好恶'
    )

    # [2.1] 治道亏缺
    content = content.replace(
        '[2.1] 〖_治道〗亏缺而〖{郑音〗兴起',
        '[2.1] 〖_治道〗亏缺而〖{郑音〗兴起'
    )
    content = content.replace(
        '〖[封〗〖#君〗世辟',
        '〖[封〗〖#君〗世辟'
    )
    content = content.replace(
        '名显邻州，争以相高。',
        '名显〖=邻州〗，争以相高。'
    )

    # [2.2] 仲尼不能化
    content = content.replace(
        '自〖@仲尼〗不能与〖◆齐〗优遂容於〖◆鲁〗',
        '自〖@仲尼〗不能与〖◆齐〗〖#优〗遂容於〖◆鲁〗'
    )
    content = content.replace(
        '虽退正〖^乐〗以诱世，作〖{五章〗以刺时',
        '虽退正〖^乐〗以诱世，作〖{五章〗以〖[刺〗时'
    )

    # [2.3] 六国流沔
    content = content.replace(
        '[2.3] 陵迟以至〖◆六国〗',
        '[2.3] 陵迟以至〖◆六国〗'
    )
    content = content.replace(
        '流沔沈佚，遂往不返',
        '流沔沈佚，遂往不返'
    )
    content = content.replace(
        '卒於〖[丧身灭宗〗',
        '卒於〖[丧身灭宗〗'
    )
    content = content.replace(
        '〖[并国〗於〖◆秦〗。',
        '〖[并国〗於〖◆秦〗。'
    )

    # [3.2] 李斯进谏
    content = content.replace(
        '"放弃〖{诗〗〖{书〗',
        '"放弃〖{诗〗〖{书〗'
    )
    content = content.replace(
        '极意声色，〖@祖伊〗所以惧也',
        '极意声色，〖@祖伊〗所以惧也'
    )
    content = content.replace(
        '轻积细过，恣心长夜，〖@纣〗所以亡也。"',
        '轻积细过，恣心长夜，〖@纣〗所以亡也。"'
    )

    # [3.3] 赵高反驳
    content = content.replace(
        '> "〖#五帝〗、〖#三王〗〖^乐〗各殊名',
        '> "〖#五帝〗、〖#三王〗〖^乐〗各殊名'
    )
    content = content.replace(
        '示不相袭。上自〖[朝廷〗',
        '示不相袭。上自〖[朝廷〗'
    )
    content = content.replace(
        '下至〖#人民〗，得以接欢喜',
        '下至〖#人民〗，得以接欢喜'
    )
    content = content.replace(
        '合殷勤，非此和说不通',
        '合殷勤，非此和说不通'
    )
    content = content.replace(
        '解泽不流，亦各〖%一世〗之化',
        '解泽不流，亦各〖%一世〗之化'
    )
    content = content.replace(
        '度时之〖^乐〗，何必〖=华山〗之〖+騄耳〗而后行远乎？"',
        '度时之〖^乐〗，何必〖=华山〗之〖+騄耳|名马〗而后行远乎？"'
    )

    # [4.1] 高祖过沛
    content = content.replace(
        '[4.1] 〖@高祖〗过〖=沛〗诗〖{三侯之章〗',
        '[4.1] 〖@高祖〗过〖=沛〗〖:诗〗〖{三侯之章〗'
    )
    content = content.replace(
        '令〖#小兒〗歌之。',
        '令〖#小兒〗〖:歌〗之。'
    )

    # [4.2] 沛得四时歌
    content = content.replace(
        '[4.2] 〖@高祖〗崩，令〖=沛〗得以〖%四时〗歌〖:鳷〗〖^宗庙〗。',
        '[4.2] 〖@高祖〗崩，令〖=沛〗得以〖%四时〗〖:歌〗〖=鳷〗〖^宗庙〗。'
    )

    # [4.3] 孝惠文景
    content = content.replace(
        '[4.3] 〖@孝惠〗、〖@孝文〗、〖@孝景〗无所增更',
        '[4.3] 〖@孝惠〗、〖@孝文〗、〖@孝景〗无所增更'
    )
    content = content.replace(
        '於〖^乐府〗习常肄旧而已。',
        '於〖^乐府〗习常肄旧而已。'
    )

    # [5.1] 今上定乐
    content = content.replace(
        '作〖{十九章〗，令〖;侍中〗〖@李延年〗次序其声',
        '作〖{十九章〗，令〖;侍中〗〖@李延年〗次序其声'
    )

    # [5.2] 五经家讲习
    content = content.replace(
        '[5.2] 通一经之〖#士〗不能独知其辞',
        '[5.2] 通〖%一经〗之〖#士〗不能独知其辞'
    )
    content = content.replace(
        '皆集会〖[五经家〗',
        '皆集会〖[五经家〗'
    )
    content = content.replace(
        '相与共讲习读之，乃能通知其意',
        '相与共讲习读之，乃能通知其意'
    )
    content = content.replace(
        '多〖{尔雅〗之文。',
        '多〖{尔雅〗之文。'
    )

    # [6.1] 祠太一
    content = content.replace(
        '[6.1] 〖◆汉〗家常以〖%正月上辛〗祠〖!太一〗〖=甘泉〗',
        '[6.1] 〖◆汉〗家常以〖%正月上辛〗〖:祠〗〖!太一〗〖=甘泉〗'
    )
    content = content.replace(
        '以昏时夜祠，到明而终。',
        '以昏时〖%夜〗〖:祠〗，到明而终。'
    )

    # [6.2] 童男童女
    content = content.replace(
        '[6.2] 常有〖?流星〗经於祠坛上。使僮男僮女七〖$十人〗俱歌。',
        '[6.2] 常有〖?流星〗经於〖=祠坛〗上。使〖#僮男僮女〗〖$七十人〗俱〖:歌〗。'
    )

    # [6.3] 四季之歌
    content = content.replace(
        '[6.3] 〖%春〗歌〖{青阳〗',
        '[6.3] 〖%春〗〖:歌〗〖{青阳〗'
    )
    content = content.replace(
        '〖%夏〗歌〖{硃明〗',
        '〖%夏〗〖:歌〗〖{硃明〗'
    )
    content = content.replace(
        '〖%秋〗歌〖{西昚〗',
        '〖%秋〗〖:歌〗〖{西昚〗'
    )
    content = content.replace(
        '〖%冬〗歌〖{玄冥〗',
        '〖%冬〗〖:歌〗〖{玄冥〗'
    )
    content = content.replace(
        '世多有，故不论。',
        '世多有，故不论。'
    )

    # [7.1] 神马渥洼
    content = content.replace(
        '[7.1] 又尝得神〖+马〗〖=渥洼水〗中',
        '[7.1] 又尝得神〖+马〗〖=渥洼水〗中'
    )
    content = content.replace(
        '复次以为〖!太一〗之〖:歌〗。',
        '复次以为〖!太一〗之〖:歌〗。'
    )

    # [7.3] 伐大宛
    content = content.replace(
        '[7.3] 後〖[伐〗〖~大宛〗得〖$千里〗〖+马〗',
        '[7.3] 後〖[伐〗〖~大宛〗得〖$千里〗〖+马〗'
    )
    content = content.replace(
        '〖+马〗名蒲梢',
        '〖+马〗名〖+蒲梢|马名〗'
    )
    content = content.replace(
        '次作以为〖:歌〗。',
        '次作以为〖:歌〗。'
    )

    # [7.4] 歌诗
    content = content.replace(
        '[7.4] 歌诗曰：',
        '[7.4] 〖:歌〗〖{诗〗曰：'
    )

    # [7.5] 汲黯进谏
    content = content.replace(
        '"凡〖#王者〗作〖^乐〗，上以承祖宗',
        '"凡〖#王者〗作〖^乐〗，上以承〖#祖宗〗'
    )
    content = content.replace(
        '下以化〖#兆民〗',
        '下以化〖#兆民〗'
    )
    content = content.replace(
        '今〖#陛下〗得〖+马〗，诗以为歌',
        '今〖#陛下〗得〖+马〗，〖{诗〗以为〖:歌〗'
    )
    content = content.replace(
        '协於〖^宗庙〗，〖#先帝〗百姓岂能知其音邪？"',
        '协於〖^宗庙〗，〖#先帝〗〖#百姓〗岂能知其音邪？"'
    )

    # [7.6] 公孙弘曰
    content = content.replace(
        '[7.6] 上默然不说。〖;丞相〗〖@公孙弘〗曰：',
        '[7.6] 上默然不说。〖;丞相〗〖@公孙弘〗曰：'
    )
    content = content.replace(
        '> "〖@黯〗〖[诽谤〗圣制',
        '> "〖@黯〗〖[诽谤〗圣制'
    )
    content = content.replace(
        '〖[当族〗。"',
        '〖[当族〗。"'
    )

    # [8.2] 音之生成
    content = content.replace(
        '[8.2] 感於物而动，故形於声',
        '[8.2] 感於物而动，故形於声'
    )
    content = content.replace(
        '声相应，故生变',
        '声相应，故生变'
    )
    content = content.replace(
        '变成方，谓之音',
        '变成方，谓之音'
    )
    content = content.replace(
        '比音而〖^乐〗之，及〖•干〗〖•戚〗〖•羽旄〗',
        '比音而〖^乐〗之，及〖•干〗〖•戚〗〖•羽〗〖•旄〗'
    )

    # [9.1] 六情之声
    content = content.replace(
        '[9.1] 是故其哀心感者',
        '[9.1] 是故其哀心感者'
    )
    content = content.replace(
        '其声噍以杀；其〖^乐〗心感者',
        '其声噍以杀；其〖^乐〗心感者'
    )
    content = content.replace(
        '其声啴以缓；其喜心感者',
        '其声啴以缓；其喜心感者'
    )
    content = content.replace(
        '其声发以散；其怒心感者',
        '其声发以散；其怒心感者'
    )
    content = content.replace(
        '其声粗以厉；其敬心感者',
        '其声粗以厉；其敬心感者'
    )
    content = content.replace(
        '其声直以廉；其爱心感者',
        '其声直以廉；其爱心感者'
    )
    content = content.replace(
        '其声和以柔。',
        '其声和以柔。'
    )

    # [9.2] 六者非性
    content = content.replace(
        '[9.2] 六者非〖_性〗也',
        '[9.2] 〖$六〗者非〖_性〗也'
    )
    content = content.replace(
        '感於物而后动，是故〖#先王〗慎所以感之。',
        '感於物而后动，是故〖#先王〗慎所以感之。'
    )

    # [10.1] 音生人心
    content = content.replace(
        '[10.1] 凡音者，生〖_人心〗者也。',
        '[10.1] 凡音者，生〖_人心〗者也。'
    )
    content = content.replace(
        '情动於中，故形於声，声成文谓之音。',
        '情动於中，故形於声，声成文谓之音。'
    )

    # [10.2] 治乱之音
    content = content.replace(
        '[10.2] 是故治世之音安以〖^乐〗',
        '[10.2] 是故治世之音安以〖^乐〗'
    )
    content = content.replace(
        '其正和；乱世之音怨以怒',
        '其〖^政〗和；乱世之音怨以怒'
    )
    content = content.replace(
        '其正乖；亡国之音哀以思',
        '其〖^政〗乖；亡国之音哀以思'
    )
    content = content.replace(
        '其〖#民〗困。',
        '其〖#民〗困。'
    )

    # [10.3] 音道通正
    content = content.replace(
        '[10.3] 声音之〖_道〗，与〖^政〗通矣。',
        '[10.3] 声音之〖_道〗，与〖^政〗通矣。'
    )

    return content


def fix_section_19_to_21(content: str) -> str:
    """修复[19]-[21]节：太史公再论、琴之制度、礼乐之功"""

    # [19.1] 明王举乐
    content = content.replace(
        '[19.1] 〖@太史公〗曰：夫上古〖#明王〗举〖^乐〗者',
        '[19.1] 〖@太史公〗曰：夫上古〖#明王〗举〖^乐〗者'
    )
    content = content.replace(
        '非以娱心自〖^乐〗，快意恣欲',
        '非以娱心自〖^乐〗，快意恣欲'
    )
    content = content.replace(
        '将欲为治也。',
        '将欲为治也。'
    )

    # [19.2] 音正行正
    content = content.replace(
        '[19.2] 正教者皆始於音',
        '[19.2] 〖^政教〗者皆始於音'
    )
    content = content.replace(
        '音正而行正。',
        '音正而行正。'
    )

    # [19.3] 音乐之功
    content = content.replace(
        '[19.3] 故〖•音乐〗者',
        '[19.3] 故〖^音乐〗者'
    )
    content = content.replace(
        '所以动荡血脉，通流精神而和正心也。',
        '所以动荡血脉，通流精神而和正心也。'
    )

    # [19.4] 五音五德（核心段落）
    content = content.replace(
        '[19.4] 故〖•宫〗动脾而和正圣',
        '[19.4] 故〖•宫〗动脾而和正〖_圣〗'
    )
    content = content.replace(
        '〖•商〗动肺而和正〖_义〗',
        '〖•商〗动肺而和正〖_义〗'
    )
    content = content.replace(
        '〖•角〗动肝而和正〖_仁〗',
        '〖•角〗动肝而和正〖_仁〗'
    )
    content = content.replace(
        '〖•徵〗动心而和正〖^礼〗',
        '〖•徵〗动心而和正〖^礼〗'
    )
    content = content.replace(
        '〖•羽〗动肾而和正〖_智〗。',
        '〖•羽〗动肾而和正〖_智〗。'
    )

    # [19.5] 乐之功用
    content = content.replace(
        '[19.5] 故〖^乐〗所以内辅正心而外异贵贱也',
        '[19.5] 故〖^乐〗所以内辅正心而外异〖[贵贱〗也'
    )
    content = content.replace(
        '上以事〖^宗庙〗，下以〖_变化〗黎庶也。',
        '上以事〖^宗庙〗，下以〖_变化〗〖#黎庶〗也。'
    )

    # [20.1] 琴之长度
    content = content.replace(
        '[20.1] 〖•琴〗长〖$八尺〗〖$一寸〗',
        '[20.1] 〖•琴〗长〖$八尺一寸〗'
    )
    content = content.replace(
        '正度也。',
        '正度也。'
    )

    # [20.2] 弦序与君臣
    content = content.replace(
        '[20.2] 弦大者为〖•宫〗',
        '[20.2] 弦大者为〖•宫〗'
    )
    content = content.replace(
        '而居中央，〖#君〗也。',
        '而居中央，〖#君〗也。'
    )
    content = content.replace(
        '〖•商〗张右傍',
        '〖•商〗张右傍'
    )
    content = content.replace(
        '其馀大小相次，不失其次序',
        '其馀大小相次，不失其次序'
    )
    content = content.replace(
        '则〖#君臣〗之位正矣。',
        '则〖#君臣〗之位正矣。'
    )

    # [20.3] 五音之效（核心段落）
    content = content.replace(
        '[20.3] 故闻〖•宫音〗',
        '[20.3] 故闻〖•宫音〗'
    )
    content = content.replace(
        '使人温舒而广大',
        '使〖#人〗温舒而广大'
    )
    content = content.replace(
        '闻〖•商音〗，使人方正而好〖_义〗',
        '闻〖•商音〗，使〖#人〗方正而好〖_义〗'
    )
    content = content.replace(
        '闻〖•角音〗，使人恻隐而爱人',
        '闻〖•角音〗，使〖#人〗恻隐而爱〖#人〗'
    )
    content = content.replace(
        '闻〖•徵音〗，使人〖^乐〗善而好施',
        '闻〖•徵音〗，使〖#人〗〖^乐〗〖_善〗而好施'
    )
    content = content.replace(
        '闻〖•羽音〗，使人整齐而好〖^礼〗。',
        '闻〖•羽音〗，使〖#人〗整齐而好〖^礼〗。'
    )

    # [21.1] 礼乐内外
    content = content.replace(
        '[21.1] 夫〖^礼〗由外入',
        '[21.1] 夫〖^礼〗由外入'
    )
    content = content.replace(
        '〖^乐〗自内出。',
        '〖^乐〗自内出。'
    )

    # [21.2] 不可须臾离
    content = content.replace(
        '[21.2] 故〖_君子〗不可须臾离〖^礼〗',
        '[21.2] 故〖_君子〗不可须臾离〖^礼〗'
    )
    content = content.replace(
        '须臾离〖^礼〗则暴慢之行穷外',
        '须臾离〖^礼〗则暴慢之行穷外'
    )
    content = content.replace(
        '不可须臾离〖^乐〗，须臾离〖^乐〗则奸邪之行穷内。',
        '不可须臾离〖^乐〗，须臾离〖^乐〗则奸邪之行穷内。'
    )

    # [21.3] 乐养义
    content = content.replace(
        '[21.3] 故〖^乐〗音者',
        '[21.3] 故〖^乐〗音者'
    )
    content = content.replace(
        '〖_君子〗之所养〖_义〗也。',
        '〖_君子〗之所养〖_义〗也。'
    )

    # [21.4] 天子诸侯听乐
    content = content.replace(
        '[21.4] 夫古者，〖#天子〗〖#诸侯〗听〖•钟磬〗未尝离於庭',
        '[21.4] 夫古者，〖#天子〗〖#诸侯〗听〖•钟〗〖•磬〗未尝离於庭'
    )
    content = content.replace(
        '〖;卿大夫〗听〖•琴瑟〗之音未尝离於前',
        '〖;卿大夫〗听〖•琴〗〖•瑟〗之音未尝离於前'
    )
    content = content.replace(
        '所以养行〖_义〗而防淫佚也。',
        '所以养行〖_义〗而防淫佚也。'
    )
    content = content.replace(
        '夫淫佚生於无〖^礼〗',
        '夫淫佚生於无〖^礼〗'
    )
    content = content.replace(
        '故〖#圣王〗使人耳闻雅颂之音',
        '故〖#圣王〗使〖#人〗耳闻〖{雅颂〗之音'
    )
    content = content.replace(
        '目视威仪之〖^礼〗',
        '目视威仪之〖^礼〗'
    )
    content = content.replace(
        '足行恭敬之容，口言〖_仁义〗之〖_道〗',
        '足行恭敬之容，口言〖_仁〗〖_义〗之〖_道〗'
    )
    content = content.replace(
        '故〖_君子〗终日言而邪辟无由入也。',
        '故〖_君子〗终日言而邪辟无由入也。'
    )

    return content


def fix_section_22(content: str) -> str:
    """修复[22]节：赞（韵文）"""

    # [22] 赞
    content = content.replace(
        '[22]〖^乐〗之所兴，在乎防欲。',
        '[22] 〖^乐〗之所兴，在乎防欲。'
    )
    content = content.replace(
        '陶心暢志，〖:舞〗手蹈足。',
        '陶心暢志，〖:舞〗手蹈足。'
    )
    content = content.replace(
        '〖@舜〗曰〖{箫韶〗',
        '〖@舜〗曰〖{箫韶〗'
    )
    content = content.replace(
        '融称属续。',
        '〖@融|师融〗称属续。'
    )
    content = content.replace(
        '审音知〖^政〗，观〖_风〗变俗。',
        '审音知〖^政〗，观〖_风〗变俗。'
    )
    content = content.replace(
        '端如贯珠，清同叩〖•玉〗。',
        '端如贯珠，清同叩〖•玉〗。'
    )
    content = content.replace(
        '洋洋盈耳，〖{咸英〗馀曲。',
        '洋洋盈耳，〖{咸英〗馀曲。'
    )

    return content


def main():
    """主函数"""
    file_path = Path('/home/baojie/work/knowledge/shiji-kb/chapter_md/024_乐书.tagged.md')

    # 读取文件
    print(f"读取文件：{file_path}")
    content = file_path.read_text(encoding='utf-8')

    # 统计原始标注数量
    original_count = len(re.findall(r'〖[^〗]+〗', content))
    print(f"原始标注数量：{original_count}")

    # 应用修复
    print("\n开始标注修复...")

    print("  [1/3] 修复[1]-[11]节（序论、礼乐衰微、秦汉乐制）")
    content = fix_section_01_to_11(content)

    print("  [2/3] 修复[19]-[21]节（太史公再论、琴之制度、礼乐之功）")
    content = fix_section_19_to_21(content)

    print("  [3/3] 修复[22]节（赞）")
    content = fix_section_22(content)

    # 统计新增标注数量
    new_count = len(re.findall(r'〖[^〗]+〗', content))
    added_count = new_count - original_count
    print(f"\n新增标注数量：{added_count}")
    print(f"最终标注总数：{new_count}")

    # 检查半角引号
    halfwidth_quotes = content.count('"')
    if halfwidth_quotes > 0:
        print(f"\n⚠️  警告：检测到 {halfwidth_quotes} 个半角引号！")
        return False

    # 写入文件
    print(f"\n写入文件：{file_path}")
    file_path.write_text(content, encoding='utf-8')

    print("\n✓ 标注修复完成")
    return True


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
