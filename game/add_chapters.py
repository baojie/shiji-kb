#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为史记争霸游戏添加第三、四章
"""

import re
from pathlib import Path

# 获取脚本所在目录
SCRIPT_DIR = Path(__file__).parent
GAME_JS = SCRIPT_DIR / 'game.js'

# 读取原文件
with open(GAME_JS, 'r', encoding='utf-8') as f:
    content = f.read()

# 第三章和第四章的JavaScript代码
new_chapters = ''',
    {
        title: '第三章：楚汉相争',
        scenes: [
            {
                title: '秦朝灭亡',
                text: '公元前206年，秦朝暴政终于引发天下大乱。刘邦率军先入关中，项羽随后而至。在鸿门，项羽设宴款待刘邦，范增暗示要除掉刘邦，但项羽犹豫不决...',
                choices: [
                    {
                        text: '使用"鸿门脱险"逃离危机',
                        requireSkill: 'hongmen-escape',
                        effect: () => {
                            if (canUseSkill('hongmen-escape')) {
                                useSkill('hongmen-escape');
                                showMessage('刘邦借口如厕，从小路逃回霸上，保全性命！');
                                updateResources({ popularity: +20, prestige: -10 });
                                nextScene();
                            } else {
                                showMessage('资源不足，无法使用此技能！');
                            }
                        }
                    },
                    {
                        text: '正面应对，据理力争',
                        effect: () => {
                            updateResources({ prestige: +10, military: -20 });
                            showMessage('虽然保全颜面，但处境危险。');
                            nextScene();
                        }
                    }
                ]
            },
            {
                title: '分封天下',
                text: '项羽自封西楚霸王，分封诸侯。刘邦被封为汉王，领地偏远的巴蜀汉中。刘邦心有不甘，但韬光养晦，暗中积蓄力量...',
                choices: [
                    {
                        text: '使用"知人善任"招揽人才',
                        requireSkill: 'knowing-talent',
                        effect: () => {
                            if (canUseSkill('knowing-talent')) {
                                useSkill('knowing-talent');
                                showMessage('得到张良、萧何、韩信等贤才辅佐！');
                                updateResources({ wealth: +30, military: +30, prestige: +20 });
                                nextScene();
                            } else {
                                showMessage('资源不足，无法使用此技能！');
                            }
                        }
                    },
                    {
                        text: '暗渡陈仓，出兵关中',
                        effect: () => {
                            updateResources({ military: -15, prestige: +15 });
                            showMessage('出其不意，占据关中要地。');
                            nextScene();
                        }
                    }
                ]
            },
            {
                title: '巨鹿之战',
                text: '项羽与秦军主力在巨鹿决战。韩信建议："此时正是破釜沉舟之机，以示必死之心！"',
                choices: [
                    {
                        text: '使用"破釜沉舟"战术',
                        requireSkill: 'burn-boats',
                        effect: () => {
                            if (canUseSkill('burn-boats')) {
                                useSkill('burn-boats');
                                showMessage('汉军士气爆发，以一当十，大破楚军！');
                                updateResources({ military: +50, prestige: +60 });
                                nextScene();
                            } else {
                                showMessage('资源不足，无法使用此技能！');
                            }
                        }
                    },
                    {
                        text: '稳扎稳打，步步为营',
                        effect: () => {
                            updateResources({ military: -20, wealth: +10 });
                            showMessage('虽然稳妥，但错失良机。');
                            nextScene();
                        }
                    }
                ]
            },
            {
                title: '垓下之围',
                text: '汉军将项羽围困于垓下。夜晚，四面楚歌响起，项羽知大势已去。乌江亭长劝项羽渡江，东山再起，但项羽羞愧难当...',
                choices: [
                    {
                        text: '劝说项羽渡江（历史假设）',
                        effect: () => {
                            updateResources({ military: -30, prestige: -20 });
                            showMessage('项羽拒绝渡江，自刎于乌江。楚汉之争结束。');
                            nextScene();
                        }
                    },
                    {
                        text: '见证项羽的选择',
                        requireSkill: 'wujiang-choice',
                        effect: () => {
                            if (canUseSkill('wujiang-choice')) {
                                useSkill('wujiang-choice');
                                showMessage('项羽宁死不渡，保全名节。一代霸王，壮烈收场。');
                                updateResources({ prestige: +80 });
                                nextScene();
                            } else {
                                showMessage('资源不足，无法使用此技能！');
                            }
                        }
                    }
                ]
            },
            {
                title: '章节完成',
                text: '楚汉之争落幕，项羽自刎乌江，刘邦统一天下。然而，如何治理这个饱经战乱的国家，成为新的挑战...',
                choices: [
                    {
                        text: '继续第四章：汉朝建立',
                        effect: () => {
                            gameState.currentChapter = 3;
                            gameState.currentScene = 0;
                            loadScene();
                        }
                    },
                    {
                        text: '返回主菜单',
                        effect: () => {
                            showMainMenu();
                        }
                    }
                ]
            }
        ]
    },
    {
        title: '第四章：汉朝建立',
        scenes: [
            {
                title: '入主咸阳',
                text: '公元前202年，刘邦在定陶称帝，建立汉朝，定都长安。百姓饱受战乱之苦，渴望休养生息。萧何建议："当施仁政，与民休息。"',
                choices: [
                    {
                        text: '使用"约法三章"安抚民心',
                        requireSkill: 'three-laws',
                        effect: () => {
                            if (canUseSkill('three-laws')) {
                                useSkill('three-laws');
                                showMessage('废除秦朝苛法，约法三章，百姓欢欣鼓舞！');
                                updateResources({ popularity: +40, prestige: +20 });
                                nextScene();
                            } else {
                                showMessage('资源不足，无法使用此技能！');
                            }
                        }
                    },
                    {
                        text: '沿用秦朝法律',
                        effect: () => {
                            updateResources({ prestige: +10, popularity: -30 });
                            showMessage('法律严苛，民心不稳。');
                            nextScene();
                        }
                    }
                ]
            },
            {
                title: '论功行赏',
                text: '天下初定，群臣争功。刘邦深知，成功离不开张良的谋略、萧何的后勤、韩信的军事才能。如何论功行赏，考验着刘邦的智慧...',
                choices: [
                    {
                        text: '使用"知人善任"公正论功',
                        requireSkill: 'knowing-talent',
                        effect: () => {
                            if (canUseSkill('knowing-talent')) {
                                useSkill('knowing-talent');
                                showMessage('运筹帷幄者张良，镇国安民者萧何，百战百胜者韩信，各得其所！');
                                updateResources({ prestige: +30, popularity: +20 });
                                nextScene();
                            } else {
                                showMessage('资源不足，无法使用此技能！');
                            }
                        }
                    },
                    {
                        text: '按军功大小封赏',
                        effect: () => {
                            updateResources({ military: +20, popularity: -10 });
                            showMessage('武将满意，但文臣不满。');
                            nextScene();
                        }
                    }
                ]
            },
            {
                title: '异姓王问题',
                text: '韩信、彭越、英布等异姓诸侯王拥兵自重，威胁中央。有大臣建议削藩，但也有人担心引发叛乱...',
                choices: [
                    {
                        text: '使用"城池劝降"和平解决',
                        requireSkill: 'city-surrender',
                        effect: () => {
                            if (canUseSkill('city-surrender')) {
                                useSkill('city-surrender');
                                showMessage('通过谈判和封赏，和平收回兵权。');
                                updateResources({ wealth: -30, prestige: +20, military: +20 });
                                nextScene();
                            } else {
                                showMessage('资源不足，无法使用此技能！');
                            }
                        }
                    },
                    {
                        text: '强行削藩',
                        effect: () => {
                            updateResources({ military: -40, prestige: +30 });
                            showMessage('引发叛乱，但最终平定。');
                            nextScene();
                        }
                    },
                    {
                        text: '维持现状',
                        effect: () => {
                            updateResources({ popularity: +10, prestige: -20 });
                            showMessage('暂时稳定，但隐患依旧。');
                            nextScene();
                        }
                    }
                ]
            },
            {
                title: '制度建设',
                text: '汉朝初建，需要建立完善的制度。是沿用秦朝的郡县制，还是恢复周朝的分封制？这关系到国家的长治久安...',
                choices: [
                    {
                        text: '郡县制与分封制并行',
                        effect: () => {
                            updateResources({ prestige: +20, popularity: +15 });
                            showMessage('郡国并行，兼顾中央集权与宗室利益。');
                            nextScene();
                        }
                    },
                    {
                        text: '完全采用郡县制',
                        requireSkill: 'jun-xian',
                        effect: () => {
                            if (canUseSkill('jun-xian')) {
                                useSkill('jun-xian');
                                showMessage('中央集权得以加强，但宗室不满。');
                                updateResources({ prestige: +80, popularity: -20 });
                                nextScene();
                            } else {
                                showMessage('资源不足，无法使用此技能！');
                            }
                        }
                    }
                ]
            },
            {
                title: '章节完成',
                text: '恭喜！你成功辅佐刘邦建立汉朝，开创了中国历史上最辉煌的王朝之一。汉朝延续四百余年，影响深远。你的智慧和决策，改变了历史的进程！',
                choices: [
                    {
                        text: '查看成就',
                        effect: () => {
                            showAchievements();
                        }
                    },
                    {
                        text: '返回主菜单',
                        effect: () => {
                            showMainMenu();
                        }
                    },
                    {
                        text: '重新开始',
                        effect: () => {
                            gameState.currentChapter = 0;
                            gameState.currentScene = 0;
                            gameState.resources = {
                                wealth: 100,
                                popularity: 100,
                                military: 100,
                                prestige: 100
                            };
                            gameState.usedSkills.clear();
                            loadScene();
                        }
                    }
                ]
            }
        ]
    }'''

# 找到STORY_CHAPTERS数组的结束位置并插入新章节
# 查找最后一个 }]; 之前的位置
pattern = r'(\s*}\s*\]\s*}\s*\];)\s*\n\s*//\s*初始化游戏'

if re.search(pattern, content):
    # 在数组结束前插入新章节
    new_content = re.sub(
        pattern,
        new_chapters + r'\n\1\n\n// 初始化游戏',
        content
    )
    
    # 写入新文件
    with open(GAME_JS, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ 成功添加第三、四章！")
    print(f"📊 新文件大小：{len(new_content)} 字节")
else:
    print("❌ 未找到插入位置，请检查文件结构")
