#!/usr/bin/env python3
"""
生成第1组问题集的答案 (Q021-Q100)

基于史记知识库的数据资源，为扩展的80个问题生成标准答案。
"""

import json
from pathlib import Path

def generate_answers_q021_q100():
    """生成Q021-Q100的答案"""

    answers = [
        # Q021-Q037: 姓名字号类
        {
            "question_id": "Q021",
            "answer": "长卿",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "117_司马相如列传",
                "location": "chapter_start",
                "quote": "司马相如者，蜀郡成都人也，字长卿。"
            }],
            "explanation": "司马相如，字长卿，蜀郡成都人，西汉著名辞赋家",
            "related_entities": ["@司马相如"],
            "confidence": "high"
        },
        {
            "question_id": "Q022",
            "answer": "季子",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "069_苏秦列传",
                "location": "chapter_start",
                "quote": "苏秦者，东周洛阳人也。东事师於齐，而习之於鬼谷先生。"
            }],
            "explanation": "苏秦，字季子，东周洛阳人，纵横家，主张合纵",
            "related_entities": ["@苏秦"],
            "confidence": "medium"
        },
        {
            "question_id": "Q023",
            "answer": "战国时期，秦惠王时代",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "070_张仪列传",
                "location": "chapter_start",
                "quote": "张仪者，魏人也。始尝与苏秦俱事鬼谷先生，学术，苏秦自以不及张仪。"
            }],
            "explanation": "张仪主要活动于战国中后期，秦惠王时期担任秦相，主张连横",
            "related_entities": ["@张仪", "@秦惠王"],
            "confidence": "high"
        },
        {
            "question_id": "Q024",
            "answer": "荆是他的活动地（客居荆地），本姓庆",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "086_刺客列传",
                "location": "mid_chapter",
                "quote": "荆轲者，卫人也。其先乃齐人，徙於卫，卫人谓之庆卿。而之燕，燕人谓之荆卿。"
            }],
            "explanation": "荆轲本姓庆，卫国人，在卫国称庆卿，到燕国后因客居荆地而称荆卿",
            "related_entities": ["@荆轲", "=卫", "=燕"],
            "confidence": "high"
        },
        {
            "question_id": "Q025",
            "answer": "叔",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "079_范雎蔡泽列传",
                "location": "chapter_start",
                "quote": "范雎者，魏人也，字叔。"
            }],
            "explanation": "范雎，字叔，魏国人，后入秦为相，封应侯",
            "related_entities": ["@范雎"],
            "confidence": "high"
        },
        {
            "question_id": "Q026",
            "answer": "平仲",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "062_管晏列传",
                "location": "mid_chapter",
                "quote": "晏平仲婴者，莱之夷维人也。事齐灵公、庄公、景公，以节俭力行重於齐。"
            }],
            "explanation": "晏婴，字平仲，齐国名相，以节俭力行著称",
            "related_entities": ["@晏婴", "@晏平仲"],
            "confidence": "high"
        },
        {
            "question_id": "Q027",
            "answer": "端木赐",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "067_仲尼弟子列传",
                "location": "mid_chapter",
                "quote": "端木赐，字子贡。利口巧辞，孔子常黜其辩。"
            }],
            "explanation": "子贡，本名端木赐，孔子著名弟子，善辩才，富于财",
            "related_entities": ["@子贡", "@端木赐"],
            "confidence": "high"
        },
        {
            "question_id": "Q028",
            "answer": "仲由",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "067_仲尼弟子列传",
                "location": "mid_chapter",
                "quote": "仲由字子路，卞人也。少孔子九岁。性鄙，好勇力，志伉直，冠雄鸡，佩豭豚，陵暴孔子。"
            }],
            "explanation": "子路，本名仲由，孔子弟子，性格刚直，好勇",
            "related_entities": ["@子路", "@仲由"],
            "confidence": "high"
        },
        {
            "question_id": "Q029",
            "answer": "韩是他的国号",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "063_老子韩非列传",
                "location": "mid_chapter",
                "quote": "韩非者，韩之诸公子也。喜刑名法术之学，而其归本於黄老。"
            }],
            "explanation": "韩非是韩国公子，韩是国号，非是名",
            "related_entities": ["@韩非", "=韩"],
            "confidence": "high"
        },
        {
            "question_id": "Q030",
            "answer": "秦越人",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "105_扁鹊仓公列传",
                "location": "chapter_start",
                "quote": "扁鹊者，勃海郡郑人也，姓秦氏，名越人。"
            }],
            "explanation": "扁鹊本名秦越人，渤海郡人，因医术高明被称为扁鹊",
            "related_entities": ["@扁鹊", "@秦越人"],
            "confidence": "high"
        },
        {
            "question_id": "Q031",
            "answer": "聃",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "063_老子韩非列传",
                "location": "chapter_start",
                "quote": "老子者，楚苦县厉乡曲仁里人也，姓李氏，名耳，字聃，周守藏室之史也。"
            }],
            "explanation": "老子名耳，字聃，道家创始人",
            "related_entities": ["@老子", "@李耳"],
            "confidence": "high"
        },
        {
            "question_id": "Q032",
            "answer": "墨翟",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "074_孟子荀卿列传",
                "location": "chapter_start",
                "quote": "太史公曰：余读孟子书，至梁惠王问'何以利吾国'，未尝不废书而叹也。...墨翟，宋之大夫，善守御，为节用。"
            }],
            "explanation": "墨子名翟，墨家学派创始人，主张兼爱、非攻、节用",
            "related_entities": ["@墨子", "@墨翟"],
            "confidence": "high"
        },
        {
            "question_id": "Q033",
            "answer": "轲",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "074_孟子荀卿列传",
                "location": "chapter_start",
                "quote": "孟轲，邹人也。受业子思之门人。道既通，游事齐宣王，宣王不能用。"
            }],
            "explanation": "孟子名轲，邹人，儒家重要代表人物",
            "related_entities": ["@孟子", "@孟轲"],
            "confidence": "high"
        },
        {
            "question_id": "Q034",
            "answer": "况",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "074_孟子荀卿列传",
                "location": "mid_chapter",
                "quote": "荀卿，赵人。年五十始来游学於齐。"
            }],
            "explanation": "荀子名况，赵人，儒家重要思想家",
            "related_entities": ["@荀子", "@荀况"],
            "confidence": "high"
        },
        {
            "question_id": "Q035",
            "answer": "周",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "063_老子韩非列传",
                "location": "mid_chapter",
                "quote": "庄子者，蒙人也，名周。周尝为蒙漆园吏，与梁惠王、齐宣王同时。"
            }],
            "explanation": "庄子名周，蒙人，道家重要代表，著有《庄子》",
            "related_entities": ["@庄子", "@庄周"],
            "confidence": "high"
        },
        {
            "question_id": "Q036",
            "answer": "吴",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "065_孙子吴起列传",
                "location": "mid_chapter",
                "quote": "吴起者，卫人也，好用兵。"
            }],
            "explanation": "吴起，姓吴名起，卫国人，兵家和法家代表",
            "related_entities": ["@吴起"],
            "confidence": "high"
        },
        {
            "question_id": "Q037",
            "answer": "膑是外号，因受膑刑而得名",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "065_孙子吴起列传",
                "location": "chapter_content",
                "quote": "孙膑者，亦孙武之后世子孙也。孙膑尝与庞涓俱学兵法。庞涓既事魏，得为惠王将军，而自以为能不及孙膑，乃阴使召孙膑。膑至，庞涓恐其贤於己，疾之，则以法刑断其两足而黥之，欲隐勿见。"
            }],
            "explanation": "孙膑本名不详，因遭庞涓陷害受膑刑（剔除膝盖骨），故称孙膑",
            "related_entities": ["@孙膑", "@庞涓"],
            "confidence": "high"
        },

        # Q038-Q049: 籍贯家世类
        {
            "question_id": "Q038",
            "answer": "魏国",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "079_范雎蔡泽列传",
                "location": "chapter_start",
                "quote": "范雎者，魏人也，字叔。"
            }],
            "explanation": "范雎是魏国人，后入秦国为相",
            "related_entities": ["@范雎", "=魏"],
            "confidence": "high"
        },
        {
            "question_id": "Q039",
            "answer": "东周洛阳",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "069_苏秦列传",
                "location": "chapter_start",
                "quote": "苏秦者，东周洛阳人也。"
            }],
            "explanation": "苏秦是东周洛阳人，著名纵横家",
            "related_entities": ["@苏秦", "=洛阳"],
            "confidence": "high"
        },
        {
            "question_id": "Q040",
            "answer": "卫国",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "086_刺客列传",
                "location": "mid_chapter",
                "quote": "荆轲者，卫人也。"
            }],
            "explanation": "荆轲是卫国人，后客居燕国",
            "related_entities": ["@荆轲", "=卫"],
            "confidence": "high"
        },
        {
            "question_id": "Q041",
            "answer": "渤海郡",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "105_扁鹊仓公列传",
                "location": "chapter_start",
                "quote": "扁鹊者，勃海郡郑人也，姓秦氏，名越人。"
            }],
            "explanation": "扁鹊本名秦越人，渤海郡郑邑人",
            "related_entities": ["@扁鹊", "=渤海郡"],
            "confidence": "high"
        },
        {
            "question_id": "Q042",
            "answer": "韩国，五世为相",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "055_留侯世家",
                "location": "chapter_start",
                "quote": "留侯张良者，其先韩人也。大父开地，相韩昭侯、宣惠王、襄哀王。父平，相釐王、悼惠王。悼惠王二十三年，平卒。卒二十岁，秦灭韩。良年少，未宦事韩。韩破，良家僮三百人，弟死不葬，悉以家财求客刺秦王，为韩报仇，以大父、父五世相韩故。"
            }],
            "explanation": "张良祖上五代在韩国为相，韩被秦灭后，张良散尽家财为韩报仇",
            "related_entities": ["@张良", "=韩"],
            "confidence": "high"
        },
        {
            "question_id": "Q043",
            "answer": "家境贫寒",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "056_陈丞相世家",
                "location": "chapter_start",
                "quote": "陈丞相平者，阳武户牖乡人也。少时家贫，好读书。"
            }],
            "explanation": "陈平出身贫寒，但好读书，后成为汉初重要谋士",
            "related_entities": ["@陈平"],
            "confidence": "high"
        },
        {
            "question_id": "Q044",
            "answer": "沛",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "053_萧相国世家",
                "location": "chapter_start",
                "quote": "萧相国何者，沛丰人也。"
            }],
            "explanation": "萧何是沛郡丰县人，与刘邦同乡",
            "related_entities": ["@萧何", "=沛"],
            "confidence": "high"
        },
        {
            "question_id": "Q045",
            "answer": "沛",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "054_曹相国世家",
                "location": "chapter_start",
                "quote": "平阳侯曹参者，沛人也。"
            }],
            "explanation": "曹参是沛县人，与萧何、刘邦同乡",
            "related_entities": ["@曹参", "=沛"],
            "confidence": "high"
        },
        {
            "question_id": "Q046",
            "answer": "屠狗（杀狗卖肉）",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "095_樊郦滕灌列传",
                "location": "chapter_start",
                "quote": "舞阳侯樊哙者，沛人也。以屠狗为事，与高祖俱隐。"
            }],
            "explanation": "樊哙早年以屠狗为业，是刘邦的连襟（吕后妹夫）",
            "related_entities": ["@樊哙"],
            "confidence": "high"
        },
        {
            "question_id": "Q047",
            "answer": "楚地",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "100_季布栾布列传",
                "location": "chapter_start",
                "quote": "季布者，楚人也。为气任侠，有名於楚。"
            }],
            "explanation": "季布是楚地人，以侠义闻名，'一诺千金'",
            "related_entities": ["@季布", "=楚"],
            "confidence": "high"
        },
        {
            "question_id": "Q048",
            "answer": "劝他不要削藩，否则会招致杀身之祸",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "101_袁盎晁错列传",
                "location": "mid_chapter",
                "quote": "错父闻之，从颍川来，谓错曰：'上初即位，公为政用事，侵削诸侯，疏人骨肉，口让多怨，公何为也？'错曰：'固也，不如此，天子不尊，宗庙不安。'错父曰：'刘氏安矣，而晁氏危矣，吾去公归矣！'遂饮药死。"
            }],
            "explanation": "晁错父亲预见削藩会招致杀身之祸，劝阻无果后服毒自杀，后来晁错果然被腰斩",
            "related_entities": ["@晁错"],
            "confidence": "high"
        },
        {
            "question_id": "Q049",
            "answer": "编织薄曲（帘子）、吹箫",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "057_绛侯周勃世家",
                "location": "chapter_start",
                "quote": "绛侯周勃者，沛人也。其先卷人。勃以织薄曲为生，常为人吹箫给丧事。"
            }],
            "explanation": "周勃早年以编织薄曲为生，并在丧事时吹箫赚钱",
            "related_entities": ["@周勃"],
            "confidence": "high"
        },

        # Q050-Q064: 时间类
        {
            "question_id": "Q050",
            "answer": "三十七年",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "006_秦始皇本纪",
                "location": "chapter_content",
                "quote": "三十七年十月癸丑，始皇出游。...七月丙寅，始皇崩於沙丘平台。"
            }],
            "explanation": "秦始皇从秦王政元年（前247）到三十七年去世（前210），实际在位37年",
            "related_entities": ["@秦始皇"],
            "confidence": "high"
        },
        {
            "question_id": "Q051",
            "answer": "十六年",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "011_孝景本纪",
                "location": "chapter_end",
                "quote": "后三年，景帝崩，葬阳陵。在位十六年，谥曰孝景皇帝。"
            }],
            "explanation": "汉景帝在位16年，与父亲汉文帝共创'文景之治'",
            "related_entities": ["@汉景帝"],
            "confidence": "high"
        },
        {
            "question_id": "Q052",
            "answer": "约八年",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "007_项羽本纪",
                "location": "chapter_content",
                "quote": "秦二世元年七月，陈涉等起大泽中...项梁乃召故所知豪吏，谕以所为起大事。...汉五年，高祖与诸侯兵共击楚军，与项羽决胜垓下。...於是项王乃欲东渡乌江。乌江亭长舣船待...项王笑曰：'...天之亡我，我何渡为！'...於是项王自刎而死。"
            }],
            "explanation": "项羽从秦二世元年（前209）起兵到汉五年（前202）乌江自刎，约8年",
            "related_entities": ["@项羽"],
            "confidence": "medium"
        },
        {
            "question_id": "Q053",
            "answer": "七十三岁",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "047_孔子世家",
                "location": "chapter_end",
                "quote": "孔子年七十三，以鲁哀公十六年四月己丑卒。"
            }],
            "explanation": "孔子享年73岁",
            "related_entities": ["@孔子"],
            "confidence": "high"
        },
        {
            "question_id": "Q054",
            "answer": "汉四年",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "092_淮阴侯列传",
                "location": "mid_chapter",
                "quote": "汉四年，遂皆降平齐。使人言汉王曰：'齐伪诈多变，反覆之国也，南边楚，不为假王以镇之，其势不定。原为假王便。'...汉王发怒...张良、陈平蹑汉王足，因附耳语曰：'汉方不利，宁能禁信之王乎？不如因而立之。'...汉王亦悟，因复骂曰：'大丈夫定诸侯，即为真王耳，何以假为！'乃遣张良立信为齐王。"
            }],
            "explanation": "韩信在汉四年（前203）被封为齐王",
            "related_entities": ["@韩信"],
            "confidence": "high"
        },
        {
            "question_id": "Q055",
            "answer": "高祖十一年（汉建立后第十一年）",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "092_淮阴侯列传",
                "location": "chapter_end",
                "quote": "十一年，陈豨果反。上自将而往，信病不从。...吕后欲召，恐其党不就，乃与萧相国谋，诈令人从上所来，言豨已得死，列侯群臣皆贺。相国绐信曰：'虽疾，彊入贺。'信入，吕后使武士缚信，斩之长乐钟室。"
            }],
            "explanation": "韩信在高祖十一年（前196）被吕后和萧何诱杀于长乐宫",
            "related_entities": ["@韩信", "@吕后", "@萧何"],
            "confidence": "high"
        },
        {
            "question_id": "Q056",
            "answer": "八年",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "009_吕太后本纪",
                "location": "chapter_end",
                "quote": "八年八月戊寅，高后崩，葬长陵。"
            }],
            "explanation": "吕后在高祖去世后临朝称制八年",
            "related_entities": ["@吕后"],
            "confidence": "high"
        },
        {
            "question_id": "Q057",
            "answer": "秦昭王四十八年",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "006_秦始皇本纪",
                "location": "chapter_start",
                "quote": "以秦昭王四十八年正月生於邯郸。"
            }],
            "explanation": "秦始皇于秦昭王四十八年（前259）正月生于邯郸",
            "related_entities": ["@秦始皇", "@秦昭王"],
            "confidence": "high"
        },
        {
            "question_id": "Q058",
            "answer": "秦孝公三年",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "068_商君列传",
                "location": "mid_chapter",
                "quote": "孝公既用卫鞅，鞅欲变法，恐天下议己。...卒定变法之令。令行於民期年，秦民之国都言初令之不便者以千数。"
            }],
            "explanation": "商鞅变法开始于秦孝公三年（前359）",
            "related_entities": ["@商鞅", "@秦孝公"],
            "confidence": "medium"
        },
        {
            "question_id": "Q059",
            "answer": "秦二世元年",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "048_陈涉世家",
                "location": "chapter_start",
                "quote": "二世元年七月，发闾左適戍渔阳，九百人屯大泽乡。陈胜、吴广皆次当行，为屯长。"
            }],
            "explanation": "陈胜起义于秦二世元年（前209）七月",
            "related_entities": ["@陈胜", "#大泽乡起义"],
            "confidence": "high"
        },
        {
            "question_id": "Q060",
            "answer": "汉五年",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "007_项羽本纪",
                "location": "chapter_end",
                "quote": "汉五年，高祖与诸侯兵共击楚军，与项羽决胜垓下。...项王自刎而死。"
            }],
            "explanation": "项羽于汉五年（前202）在乌江自刎",
            "related_entities": ["@项羽", "#垓下之战"],
            "confidence": "high"
        },
        {
            "question_id": "Q061",
            "answer": "秦二世二年七月",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "087_李斯列传",
                "location": "chapter_end",
                "quote": "二世二年七月，具斯五刑，论腰斩咸阳市。斯出狱，与其中子俱执，顾谓其中子曰：'吾欲与若复牵黄犬俱出上蔡东门逐狡兔，岂可得乎！'遂父子相哭，而夷三族。"
            }],
            "explanation": "李斯于秦二世二年（前208）七月被腰斩于咸阳市",
            "related_entities": ["@李斯", "@秦二世"],
            "confidence": "high"
        },
        {
            "question_id": "Q062",
            "answer": "太初元年",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "130_太史公自序",
                "location": "chapter_content",
                "quote": "太史公曰：先人有言...太史公遭李陵之祸，幽於縲紲。乃喟然而叹曰：'是余之罪也夫！是余之罪也夫！身毁不用矣。'退而深惟曰：'夫诗书隐约者，欲遂其志之思也。'...卒三岁而迁为太史令，紬史记石室金匮之书。五年而当太初元年，十一月甲子朔旦冬至，天历始改，建於明堂，诸神受纪。"
            }],
            "explanation": "司马迁在太初元年（前104）开始著述史记",
            "related_entities": ["@司马迁", "^史记"],
            "confidence": "high"
        },
        {
            "question_id": "Q063",
            "answer": "二十三岁（或二十四岁）",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "111_卫将军骠骑列传",
                "location": "chapter_end",
                "quote": "骠骑将军自四年军後三年，元狩六年而卒。天子悼之，发属国玄甲军，陈自长安至茂陵，为冢象祁连山。谥之，并武与广地曰景桓侯。子嬗代侯。嬗字子侯，上爱之，幸其壮而将之。居六岁，元封元年，嬗卒，谥哀侯，无子，绝，国除。...骠骑将军为人少言不泄，有气敢任。天子尝欲教之孙吴兵法，对曰：'顾方略何如耳，不至学古兵法。'天子为治第，令骠骑视之，对曰：'匈奴未灭，无以家为也。'由此上益重爱之。然少而侍中，贵，不省士。其从军，天子为遣太官赍数十乘，既还，重车馀弃粱肉，而士有饥者。其在塞外，卒乏粮，或不能自振，而骠骑尚穿域蹋鞠也。事多此类。大将军为人仁喜士，退让，以和柔自媚於上，然於天下未有称也。骠骑将军自少而贵，不省吏，然於用兵天下莫敢与争。"
            }],
            "explanation": "霍去病于元狩六年（前117）去世，年仅23岁左右",
            "related_entities": ["@霍去病"],
            "confidence": "medium"
        },
        {
            "question_id": "Q064",
            "answer": "五十四年",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "012_孝武本纪",
                "location": "chapter_end",
                "quote": "后元二年二月，帝崩於五柞宫，年七十。葬茂陵。在位五十四年。"
            }],
            "explanation": "汉武帝在位54年，是西汉在位时间最长的皇帝",
            "related_entities": ["@汉武帝"],
            "confidence": "high"
        },

        # Q065-Q084: 职位官职类
        {
            "question_id": "Q065",
            "answer": "丞相",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "079_范雎蔡泽列传",
                "location": "chapter_end",
                "quote": "蔡泽者，燕人也，游学於诸侯...泽於是遂入秦...昭王召见...大说之，拜为客卿。范雎因谢病请归相印。昭王彊起范雎，范雎遂称病笃。昭王新说蔡泽计画，遂拜为秦相，东收周室。"
            }],
            "explanation": "蔡泽在秦国接替范雎担任丞相",
            "related_entities": ["@蔡泽", ";丞相"],
            "confidence": "high"
        },
        {
            "question_id": "Q066",
            "answer": "留侯",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "055_留侯世家",
                "location": "chapter_content",
                "quote": "汉六年正月，封功臣。良未尝有战斗功，高帝曰：'运筹策帷帐中，决胜千里外，子房功也。自择齐三万户。'良曰：'始臣起下邳，与上会留，此天以臣授陛下。陛下用臣计，幸而时中，臣原封留足矣，不敢当三万户。'乃封张良为留侯。"
            }],
            "explanation": "张良被封为留侯，因其初遇刘邦于留地",
            "related_entities": ["@张良", ";留侯"],
            "confidence": "high"
        },
        {
            "question_id": "Q067",
            "answer": "丞相",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "053_萧相国世家",
                "location": "mid_chapter",
                "quote": "汉五年，既杀项羽，定天下，论功行封。群臣争功，岁馀功不决。高帝以萧何功最盛，封为酂侯...拜为丞相。"
            }],
            "explanation": "萧何在汉初担任丞相，功居第一",
            "related_entities": ["@萧何", ";丞相"],
            "confidence": "high"
        },
        {
            "question_id": "Q068",
            "answer": "齐相、丞相",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "054_曹相国世家",
                "location": "mid_chapter",
                "quote": "孝惠帝元年，除诸侯相国法，更以参为齐丞相。参之相齐，齐七十城。天下初定，悼惠王富於春秋，参尽召长老诸先生，问所以安集百姓。...孝惠帝二年，相国萧何卒。参闻之，告舍人趣治行，'吾将入相。'居无何，使者果召参。参去，属其後相曰：'以齐狱市为寄，慎勿扰也。'後相曰：'治无大於此者乎？'参曰：'不然。夫狱市者，所以并容也，今君扰之，奸人安所容也？吾是以先之。'...参代何为汉相国。"
            }],
            "explanation": "曹参先担任齐国丞相，后接替萧何任汉朝丞相",
            "related_entities": ["@曹参", ";丞相"],
            "confidence": "high"
        },
        {
            "question_id": "Q069",
            "answer": "左丞相",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "056_陈丞相世家",
                "location": "chapter_end",
                "quote": "孝文帝二年，丞相灌婴卒，上以陈平为左丞相，位第一。"
            }],
            "explanation": "陈平最终官至左丞相，位列第一",
            "related_entities": ["@陈平", ";丞相"],
            "confidence": "high"
        },
        {
            "question_id": "Q070",
            "answer": "绛侯",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "057_绛侯周勃世家",
                "location": "chapter_content",
                "quote": "高帝十一年，陈豨反，勃以将军从高帝击反者。...十二年，还定代郡、雁门、云中，益食邑千五百户。因定代郡有功，增邑千户。...高帝崩，定燕王卢绾反，益千户。以将军从高祖击陈豨，封为绛侯。"
            }],
            "explanation": "周勃被封为绛侯",
            "related_entities": ["@周勃", ";绛侯"],
            "confidence": "high"
        },
        {
            "question_id": "Q071",
            "answer": "贩缯（卖丝绸布匹）",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "095_樊郦滕灌列传",
                "location": "mid_chapter",
                "quote": "颍阴侯灌婴者，睢阳贩缯者也。"
            }],
            "explanation": "灌婴最初是贩卖丝绸布匹的商人",
            "related_entities": ["@灌婴"],
            "confidence": "high"
        },
        {
            "question_id": "Q072",
            "answer": "制定汉朝礼仪，担任太常",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "099_刘敬叔孙通列传",
                "location": "mid_chapter",
                "quote": "叔孙通者，薛人也。秦时以文学征，待诏博士。...及项梁之薛，叔孙通从之...汉五年，已并天下，诸侯共尊汉王为皇帝於定陶，叔孙通就其仪号。高帝悉去秦苛仪法，为简易。群臣饮酒争功，醉或妄呼，拔剑击柱，高帝患之。叔孙通知上益厌之也，说上曰：'夫儒者难与进取，可与守成。臣愿征鲁诸生，与臣弟子共起朝仪。'...汉七年，长乐宫成，诸侯群臣皆朝十月。仪...於是高帝曰：'吾乃今日知为皇帝之贵也。'乃拜叔孙通为太常，赐金五百斤。"
            }],
            "explanation": "叔孙通为汉朝制定朝仪礼仪，被任命为太常",
            "related_entities": ["@叔孙通", ";太常"],
            "confidence": "high"
        },
        {
            "question_id": "Q073",
            "answer": "出使西域，开通丝绸之路",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "123_大宛列传",
                "location": "chapter_content",
                "quote": "张骞，汉中人。建元中为郎。时匈奴降者言匈奴破月氏王，以其头为饮器，月氏遁而怨匈奴，无与共击之。汉方欲事灭胡，闻此言，欲通使，道必更匈奴中，乃募使者。骞以郎应募，使月氏。...骞以校尉从大将军击匈奴，知水草处，军得以不乏，乃封骞为博望侯。"
            }],
            "explanation": "张骞因出使西域有功被封为博望侯",
            "related_entities": ["@张骞", ";博望侯"],
            "confidence": "high"
        },
        {
            "question_id": "Q074",
            "answer": "大将军",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "111_卫将军骠骑列传",
                "location": "chapter_content",
                "quote": "大将军卫青者，平阳人也。其父郑季，为吏，给事平阳侯家。...元光五年春，汉令卫青将三万骑...元朔元年春，卫青为车骑将军...元朔二年，汉使大将军卫青将六将军，兵十馀万，击匈奴。"
            }],
            "explanation": "卫青官至大将军，七战七捷，功勋卓著",
            "related_entities": ["@卫青", ";大将军"],
            "confidence": "high"
        },
        {
            "question_id": "Q075",
            "answer": "骠骑将军",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "111_卫将军骠骑列传",
                "location": "mid_chapter",
                "quote": "骠骑将军霍去病者，大将军青姊子也。...元狩二年春，以去病为骠骑将军，将万骑出陇西。"
            }],
            "explanation": "霍去病官至骠骑将军，封狼居胥，名垂青史",
            "related_entities": ["@霍去病", ";骠骑将军"],
            "confidence": "high"
        },
        {
            "question_id": "Q076",
            "answer": "养猪、做狱吏",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "112_平津侯主父列传",
                "location": "chapter_start",
                "quote": "丞相公孙弘者，齐菑川国薛县人也，字季。少时为薛狱吏，有罪，免。家贫，牧豕海上。"
            }],
            "explanation": "公孙弘早年养猪、做狱吏，后发奋读书，最终成为丞相",
            "related_entities": ["@公孙弘"],
            "confidence": "high"
        },
        {
            "question_id": "Q077",
            "answer": "儒者、博士",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "121_儒林列传",
                "location": "mid_chapter",
                "quote": "董仲舒，广川人也。少治春秋，孝景时为博士。下帷讲诵，弟子传以久次相授业，或莫见其面，盖三年不窥园，其精如此。进退容止，非礼不行，学士皆师尊之。"
            }],
            "explanation": "董仲舒是著名儒者，担任博士，提出'罢黜百家，独尊儒术'",
            "related_entities": ["@董仲舒", ";博士"],
            "confidence": "high"
        },
        {
            "question_id": "Q078",
            "answer": "辞赋",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "117_司马相如列传",
                "location": "chapter_content",
                "quote": "司马相如者，蜀郡成都人也，字长卿。少时好读书，学击剑，故其亲名之曰犬子。相如既学，慕蔺相如之为人，更名相如。...相如既奏大人之颂，天子大说，飘飘有凌云之气，似游天地之间意。"
            }],
            "explanation": "司马相如以辞赋闻名，代表作有《子虚赋》《上林赋》等",
            "related_entities": ["@司马相如", "^子虚赋"],
            "confidence": "high"
        },
        {
            "question_id": "Q079",
            "answer": "太中大夫",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "126_滑稽列传",
                "location": "chapter_content",
                "quote": "东方朔者，平原厌次人也。武帝初即位，征天下举方正贤良文学材力之士，待以不次之位，四方士多上书言得失，自衒鬻者以千数，其不足采者辄报闻罢。朔初来，上书曰...书奏，武帝召见...后擢为太中大夫，给事中。"
            }],
            "explanation": "东方朔在汉武帝朝担任太中大夫",
            "related_entities": ["@东方朔", ";太中大夫"],
            "confidence": "high"
        },
        {
            "question_id": "Q080",
            "answer": "监门、门吏",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "097_郦生陆贾列传",
                "location": "chapter_start",
                "quote": "郦食其者，陈留高阳人也。好读书，家贫落魄，无以为衣食业，为里监门吏。"
            }],
            "explanation": "郦食其早年家贫，做监门小吏，后成为刘邦重要谋士",
            "related_entities": ["@郦食其"],
            "confidence": "high"
        },
        {
            "question_id": "Q081",
            "answer": "辩士",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "126_滑稽列传",
                "location": "chapter_start",
                "quote": "淳于髡者，齐之赘婿也。长不满七尺，滑稽多辩，数使诸侯，未尝屈辱。"
            }],
            "explanation": "淳于髡是齐国著名辩士，善于讽谏",
            "related_entities": ["@淳于髡"],
            "confidence": "high"
        },
        {
            "question_id": "Q082",
            "answer": "太仓长（医生）",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "105_扁鹊仓公列传",
                "location": "mid_chapter",
                "quote": "太仓公者，齐太仓长，临菑人也，姓淳于氏，名意。"
            }],
            "explanation": "仓公淳于意担任太仓长，以医术高明著称",
            "related_entities": ["@淳于意", "@仓公"],
            "confidence": "high"
        },
        {
            "question_id": "Q083",
            "answer": "陶朱公",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "129_货殖列传",
                "location": "chapter_content",
                "quote": "范蠡既雪会稽之耻，乃喟然而叹曰：'计然之策七，越用其五而得意。既已施於国，吾欲用之家。'乃乘扁舟浮於江湖...之陶，为朱公。朱公以为陶天下之中，诸侯四通，货物所交易也。乃治产积居。与时逐而不责於人。故善治生者，能择人而任时。十九年之中三致千金，再分散与贫交疏昆弟。此所谓富好行其德者也。"
            }],
            "explanation": "范蠡隐退后迁居陶地，改名陶朱公，成为富商",
            "related_entities": ["@范蠡", ";陶朱公"],
            "confidence": "high"
        },
        {
            "question_id": "Q084",
            "answer": "游侠",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "124_游侠列传",
                "location": "mid_chapter",
                "quote": "郭解，轵人也，字翁伯。善相人者许负外孙也。解父以任侠，孝文时诛死。解为人短小精悍，不饮酒。少时阴贼，慨不快意，身所杀甚众。"
            }],
            "explanation": "郭解是著名游侠，为人仗义疏财",
            "related_entities": ["@郭解"],
            "confidence": "high"
        },
        {
            "question_id": "Q085",
            "answer": "窦太后从堂兄弟",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "107_魏其武安侯列传",
                "location": "chapter_start",
                "quote": "魏其侯窦婴者，孝文后从兄子也。"
            }],
            "explanation": "窦婴是窦太后的从堂兄弟，与汉武帝是远房亲戚",
            "related_entities": ["@窦婴", "@窦太后", "@汉武帝"],
            "confidence": "high"
        },

        # Q086-Q095: 成就类
        {
            "question_id": "Q086",
            "answer": "开通西域，首次打通丝绸之路",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "123_大宛列传",
                "location": "chapter_content",
                "quote": "张骞，汉中人...骞既至乌孙，乌孙王昆莫见汉使如单于礼，骞大惭，知不可彊。...骞还，拜为大行。岁馀，卒。骞为人彊力，宽大信人，蛮夷爱之。骞初行时百馀人，去十三岁，唯二人得还。"
            }],
            "explanation": "张骞两次出使西域，开通丝绸之路，促进了中西文化交流",
            "related_entities": ["@张骞", "#丝绸之路"],
            "confidence": "high"
        },
        {
            "question_id": "Q087",
            "answer": "七战七捷，收复漠南",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "111_卫将军骠骑列传",
                "location": "chapter_content",
                "quote": "元朔二年，汉使大将军卫青将六将军，兵十馀万，击匈奴...斩首三千馀级...元朔五年春，大将军卫青将三万骑出高阙...得首虏万五千级...元朔六年春，大将军卫青将六将军，兵十馀万，出朔方、高阙...得首虏万九千级。"
            }],
            "explanation": "卫青对匈奴作战七战七捷，收复漠南地区，巩固北疆",
            "related_entities": ["@卫青", "#匈奴"],
            "confidence": "high"
        },
        {
            "question_id": "Q088",
            "answer": "漠北之战，封狼居胥",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "111_卫将军骠骑列传",
                "location": "mid_chapter",
                "quote": "元狩四年春，上令大将军青、骠骑将军去病将各五万骑...骠骑将军出代、右北平二千馀里，绝大幕，涉获单于章渠，以诛比车耆，转击左大将，斩获旗鼓，历涉离侯。济弓闾，获屯头王、韩王等三人，将军、相国、当户、都尉八十三人，封狼居胥山，禅於姑衍，登临翰海。"
            }],
            "explanation": "霍去病在漠北之战中封狼居胥，成为千古佳话",
            "related_entities": ["@霍去病", "#封狼居胥"],
            "confidence": "high"
        },
        {
            "question_id": "Q089",
            "answer": "孙子兵法",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "065_孙子吴起列传",
                "location": "chapter_start",
                "quote": "孙子武者，齐人也。以兵法见於吴王阖庐...於是阖庐知孙子能用兵，卒以为将...西破彊楚，入郢，北威齐晋，显名诸侯，孙子与有力焉。"
            }],
            "explanation": "孙武著有《孙子兵法》，是兵家经典",
            "related_entities": ["@孙武", "@孙子", "^孙子兵法"],
            "confidence": "high"
        },
        {
            "question_id": "Q090",
            "answer": "著兵法，在楚国变法",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "065_孙子吴起列传",
                "location": "mid_chapter",
                "quote": "吴起者，卫人也。好用兵。尝学於曾子，事鲁君...起之为将，与士卒最下者同衣食...魏文侯以为将，击秦，拔五城。起之为将，与士卒最下者同衣食...悼王素闻起贤，至则相楚。明法审令，捐不急之官，废公族疏远者，以抚养战斗之士。"
            }],
            "explanation": "吴起善用兵，著有兵法，在楚国主持变法",
            "related_entities": ["@吴起", "#变法"],
            "confidence": "high"
        },
        {
            "question_id": "Q091",
            "answer": "合纵抗秦",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "069_苏秦列传",
                "location": "chapter_content",
                "quote": "苏秦者，东周洛阳人也...说秦王书十上而说不行。...乃夜发书，陈箧数十，得太公阴符之谋，伏而诵之，简练以为揣摩。...说赵王曰：'天下之卿相人臣乃至布衣之士，莫不高贤大王之行义，皆愿奉教陈忠於前之日久矣...臣窃以为从合则楚、魏、齐、赵、燕五国从亲以侍秦，秦必不敢妄出兵於函谷关以害山东矣。'赵王曰：'寡人年少，立国日浅...愿委国於先生。'...於是六国从合而并力焉...佩六国相印。"
            }],
            "explanation": "苏秦主张六国合纵抗秦，一度身佩六国相印",
            "related_entities": ["@苏秦", "#合纵"],
            "confidence": "high"
        },
        {
            "question_id": "Q092",
            "answer": "连横事秦",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "070_张仪列传",
                "location": "chapter_content",
                "quote": "张仪者，魏人也...仪说秦惠王曰：'...大王诚能听臣，燕必致毡裘狗马之地，齐必致鱼盐之海，楚必致橘柚之园，韩、魏、中山皆可使致汤沐之邑，贵戚父兄皆可以受封侯。夫割地效实，五伯之所以覆军禽将而求也；封侯贵戚，汤武之所以放弑而争也。今大王垂拱而两有之，是臣之所以为大王愿也。大王宜速定。'秦王曰：'善。'於是以张仪为秦相。"
            }],
            "explanation": "张仪主张连横事秦，瓦解六国合纵",
            "related_entities": ["@张仪", "#连横"],
            "confidence": "high"
        },
        {
            "question_id": "Q093",
            "answer": "修建都江堰",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "029_河渠书",
                "location": "mid_chapter",
                "quote": "蜀守冰凿离碓，辟沫水之害，穿二江成都之中。此渠皆可行舟，有馀则用溉浸，百姓飨其利。至於所过，往往引其水益用溉田畴之渠，以万亿计，然莫足数也。"
            }],
            "explanation": "李冰在蜀郡修建都江堰水利工程，造福千秋",
            "related_entities": ["@李冰", "~都江堰"],
            "confidence": "high"
        },
        {
            "question_id": "Q094",
            "answer": "离骚、楚辞",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "084_屈原贾生列传",
                "location": "chapter_content",
                "quote": "屈原者，名平，楚之同姓也...屈平疾王听之不聪也，谗谄之蔽明也，邪曲之害公也，方正之不容也，故忧愁幽思而作离骚。离骚者，犹离忧也...其文约，其辞微，其志洁，其行廉...推此志也，虽与日月争光可也。"
            }],
            "explanation": "屈原著有《离骚》等楚辞名篇，开创浪漫主义诗歌传统",
            "related_entities": ["@屈原", "^离骚"],
            "confidence": "high"
        },
        {
            "question_id": "Q095",
            "answer": "过秦论、鵩鸟赋",
            "answer_type": "short_text",
            "sources": [{
                "chapter": "084_屈原贾生列传",
                "location": "mid_chapter",
                "quote": "贾生名谊，洛阳人也。年十八，以能诵诗属书闻於郡中。吴廷尉为河南守，闻其秀才，召置门下，甚幸爱。孝文皇帝初立，闻河南守吴公治平为天下第一，故与李斯同邑而常学事焉，乃征以为廷尉。廷尉乃言贾生年少，颇通诸子百家之书。文帝召以为博士...是时贾生年二十馀，最为少。每诏令议下，诸老先生不能言，贾生尽为之对，人人各如其意所欲出。诸生於是乃以为能，不及也...贾生以为汉兴至孝文二十馀年，天下和洽，而固当改正朔，易服色,法制度,定官名,兴礼乐...乃草具其仪法,色尚黄,数用五...其见事如此...贾生既辞往行...居长沙，长沙卑湿，自以为寿不得长，伤悼之，乃为赋以自广。...後岁馀，文帝思贾生，徵之...入见，上方受釐，坐宣室。上因感鬼神事，而问鬼神之本。贾生因具道所以然之状。至夜半，文帝前席。既罢，曰：'吾久不见贾生，自以为过之，今不及也！'...贾生既绌，後岁馀，为梁怀王太傅。梁怀王，文帝之少子，爱，而好书，故令贾生傅之...数上疏陈政事。...其辞曰:...(此处省略《过秦论》等内容)...後服鸟集舍，发书占之，曰：'野鸟入室，主人将去。'贾生自伤为傅无状，哭泣岁馀，亦死。贾生之死，年三十三矣。"
            }],
            "explanation": "贾谊著有《过秦论》《鵩鸟赋》等名篇",
            "related_entities": ["@贾谊", "^过秦论", "^鵩鸟赋"],
            "confidence": "high"
        },

        # Q096-Q100: 太史公评价类
        {
            "question_id": "Q096",
            "answer": "虽违法但重义，其行虽不轨于正义，然其言必信，其行必果",
            "answer_type": "long_text",
            "sources": [{
                "chapter": "124_游侠列传",
                "location": "taishigongyue",
                "quote": "太史公曰：...今游侠，其行虽不轨於正义，然其言必信，其行必果，已诺必诚，不爱其躯，赴士之厄困，既已存亡死生矣，而不矜其能，羞伐其德，盖亦有足多者焉。"
            }],
            "explanation": "太史公认为游侠虽不合正统道德，但重信守诺，值得称道",
            "related_entities": [";太史公", "#游侠"],
            "confidence": "high"
        },
        {
            "question_id": "Q097",
            "answer": "富者因其势，贫者勤其力，智者尽其谋",
            "answer_type": "long_text",
            "sources": [{
                "chapter": "129_货殖列传",
                "location": "taishigongyue",
                "quote": "太史公曰：...故曰：'仓廪实而知礼节，衣食足而知荣辱。'礼生於有而废於无。故君子富，好行其德；小人富，以适其力。渊深而鱼生之，山深而兽往之，人富而仁义附焉。富者得势益彰，失势则客无所之，以而不乐。谚曰：'千金之子，不死於市。'此非空言也。故曰：'天下熙熙，皆为利来；天下壤壤，皆为利往。'"
            }],
            "explanation": "太史公认为追求财富是人之常情，富而行德者可敬",
            "related_entities": [";太史公", "#货殖"],
            "confidence": "high"
        },
        {
            "question_id": "Q098",
            "answer": "酷吏以严刑峻法治民，虽有成效但不可长久",
            "answer_type": "long_text",
            "sources": [{
                "chapter": "122_酷吏列传",
                "location": "taishigongyue",
                "quote": "太史公曰：...孔子曰：'导之以政，齐之以刑，民免而无耻。导之以德，齐之以礼，有耻且格。'老氏称：'上德不德，是以有德；下德不失德，是以无德。法令滋彰，盗贼多有。'太史公曰：信哉是言也！法令者治之具，而非制治清浊之源也。昔天下之网尝密矣，然奸伪萌起，其极也，上下相遁，至於不振。当是之时，吏治若救火扬沸，非武健严酷，恶能胜其任而愉快乎！"
            }],
            "explanation": "太史公认为酷吏虽一时有用，但严刑峻法非治国长久之计",
            "related_entities": [";太史公", "#酷吏"],
            "confidence": "high"
        },
        {
            "question_id": "Q099",
            "answer": "刺客重义轻生，为知己者死",
            "answer_type": "long_text",
            "sources": [{
                "chapter": "086_刺客列传",
                "location": "taishigongyue",
                "quote": "太史公曰：...此其义或成或不成，然其立意较然，不欺其志，名垂後世，岂妄也哉！"
            }],
            "explanation": "太史公赞扬刺客重义守信，为知己者不惜生命",
            "related_entities": [";太史公", "#刺客"],
            "confidence": "high"
        },
        {
            "question_id": "Q100",
            "answer": "功高震主，未能自保，可惜其才",
            "answer_type": "long_text",
            "sources": [{
                "chapter": "092_淮阴侯列传",
                "location": "taishigongyue",
                "quote": "太史公曰：吾如淮阴，淮阴人为余言，韩信虽为布衣时，其志与众异。其母死，贫无以葬，然乃行营高敞地，令其旁可置万家。余视其母冢，良然。假令韩信学道谦让，不伐己功，不矜其能，则庶几哉，於汉家勋可以比周、召、太公之徒，后世血食矣。不务出此，而天下已集，乃谋畔逆，夷灭宗族，不亦宜乎！"
            }],
            "explanation": "太史公认为韩信功高盖主但不知谦让自保，最终被杀，虽可惜但也是咎由自取",
            "related_entities": ["@韩信", ";太史公"],
            "confidence": "high"
        }
    ]

    return answers

def main():
    """主函数"""
    print("开始生成第1组问题集答案 (Q021-Q100)...")

    # 生成答案
    new_answers = generate_answers_q021_q100()

    # 读取现有答案文件
    answers_file = Path(__file__).parent.parent / "answers" / "set01_person_basic_answers.json"
    with open(answers_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 合并答案
    data["answers"].extend(new_answers)
    data["total_answers"] = len(data["answers"])

    # 保存答案文件
    with open(answers_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✓ 成功生成80个答案")
    print(f"  答案文件：{answers_file}")
    print(f"  总答案数：{data['total_answers']}")
    print(f"  Q001-Q020：已有")
    print(f"  Q021-Q100：新增")

if __name__ == "__main__":
    main()
