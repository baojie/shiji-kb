// 游戏数据
const SKILLS = [
    {
        id: 'burn-boats',
        name: '破釜沉舟',
        category: 'military',
        rarity: 4,
        description: '切断所有退路，极大提升军队士气。背水一战，置之死地而后生。',
        cost: { military: 30, wealth: 20 },
        effect: '本次战斗军队战斗力+150%，胜利后威望+50',
        cooldown: 5,
        shijiQuote: '项羽乃悉引兵渡河，皆沉船，破釜甑，烧庐舍，持三日粮，以示士卒必死，无一还心。',
        shijiSource: '《史记·项羽本纪》'
    },
    {
        id: 'hongmen-escape',
        name: '鸿门脱险',
        category: 'military',
        rarity: 4,
        description: '在危险场合中安全脱身的策略。大行不顾细谨，大礼不辞小让。',
        cost: { prestige: 10 },
        effect: '避免一次致命危机，民心+20',
        cooldown: 3,
        shijiQuote: '沛公至军，立诛杀曹无伤。',
        shijiSource: '《史记·项羽本纪》'
    },
    {
        id: 'three-laws',
        name: '约法三章',
        category: 'politics',
        rarity: 3,
        description: '废除苛政，建立简化法律体系，迅速获得民心。',
        cost: { prestige: 15 },
        effect: '民心+40，威望+20',
        cooldown: 0,
        shijiQuote: '与父老约，法三章耳：杀人者死，伤人及盗抵罪。',
        shijiSource: '《史记·高祖本纪》'
    },
    {
        id: 'knowing-talent',
        name: '知人善任',
        category: 'leadership',
        rarity: 3,
        description: '识别和任用贤才，建立强大的核心团队。',
        cost: { wealth: 20, prestige: 10 },
        effect: '所有资源获取+30%，持续3回合',
        cooldown: 5,
        shijiQuote: '夫运筹策帷帐之中，决胜于千里之外，吾不如子房。镇国家，抚百姓，给馈饷，不绝粮道，吾不如萧何。连百万之军，战必胜，攻必取，吾不如韩信。',
        shijiSource: '《史记·高祖本纪》'
    },
    {
        id: 'muye-battle',
        name: '牧野之战',
        category: 'military',
        rarity: 5,
        description: '以少胜多的经典战役，集结诸侯，一举推翻暴政。',
        cost: { military: 40, prestige: 30 },
        effect: '对暴君势力战斗力+200%，胜利后威望+100',
        cooldown: 10,
        shijiQuote: '甲子昧爽，受率其旅若林，会于牧野。罔有敌于我师，前徒倒戈，攻于后以北，血流漂杵。',
        shijiSource: '《史记·周本纪》'
    },
    {
        id: 'jun-xian',
        name: '废分封行郡县',
        category: 'politics',
        rarity: 5,
        description: '废除分封制，建立中央集权的郡县制行政体系。',
        cost: { prestige: 50, popularity: 30 },
        effect: '威望+80，但民心-20（触及贵族利益）',
        cooldown: 0,
        shijiQuote: '置三十六郡，郡置守、尉、监。',
        shijiSource: '《史记·秦始皇本纪》'
    },
    {
        id: 'emperor-title',
        name: '皇帝尊号制',
        category: 'politics',
        rarity: 5,
        description: '建立皇帝称号制度，确立至高无上的君主地位。',
        cost: { prestige: 40 },
        effect: '威望+100，解锁"帝国"模式',
        cooldown: 0,
        shijiQuote: '古有天皇，有地皇，有泰皇，泰皇最贵。臣等昧死上尊号，王为"泰皇"。命为"制"，令为"诏"，天子自称曰"朕"。',
        shijiSource: '《史记·秦始皇本纪》'
    },
    {
        id: 'city-surrender',
        name: '城池劝降',
        category: 'military',
        rarity: 3,
        description: '通过谈判和封赏促使敌方守军投降。',
        cost: { wealth: 30, prestige: 20 },
        effect: '避免战斗损失，获得敌方城池，军力+20',
        cooldown: 2,
        shijiQuote: '汉王遣使谓雍王曰："急下，吾以汝为上将，封三万户。"',
        shijiSource: '《史记·高祖本纪》'
    },
    {
        id: 'water-virtue',
        name: '水德运数制',
        category: 'politics',
        rarity: 4,
        description: '基于五德终始说建立政权合法性，推行统一标准。',
        cost: { prestige: 35, wealth: 25 },
        effect: '威望+60，解锁"标准化"政策',
        cooldown: 0,
        shijiQuote: '方今水德之始，改年始，朝贺皆自十月朔。衣服旄旌节旗皆上黑。数以六为纪。',
        shijiSource: '《史记·秦始皇本纪》'
    },
    {
        id: 'burn-books',
        name: '焚书坑儒',
        category: 'culture',
        rarity: 4,
        description: '统一思想，禁止私学，严惩议政者。',
        cost: { prestige: 30, popularity: 40 },
        effect: '威望+50，但民心-60（知识分子不满）',
        cooldown: 0,
        shijiQuote: '非博士官所职，天下敢有藏诗、书、百家语者，悉诣守、尉杂烧之。有敢偶语诗书者弃市。以古非今者族。',
        shijiSource: '《史记·秦始皇本纪》'
    },
    {
        id: 'xihe-calendar',
        name: '羲和历法',
        category: 'culture',
        rarity: 3,
        description: '通过观测星象确定四时节气，指导农业生产。',
        cost: { wealth: 15, prestige: 10 },
        effect: '民心+30，财富+20（农业丰收）',
        cooldown: 4,
        shijiQuote: '乃命羲、和，敬顺昊天，数法日月星辰，敬授民时。',
        shijiSource: '《史记·五帝本纪》'
    },
    {
        id: 'shang-succession',
        name: '殷商继承制',
        category: 'history',
        rarity: 3,
        description: '分析王位继承制度变更引发的动乱。',
        cost: { prestige: 20 },
        effect: '了解历史教训，避免继承危机',
        cooldown: 0,
        shijiQuote: '自中丁以来，废適而更立诸弟子，弟子或争相代立，比九世乱，於是诸侯莫朝。',
        shijiSource: '《史记·殷本纪》'
    },
    {
        id: 'wujiang-choice',
        name: '乌江抉择',
        category: 'history',
        rarity: 4,
        description: '项羽在乌江的生死抉择，宁死不渡。',
        cost: { prestige: 50 },
        effect: '保全名节，威望+80，但失去翻盘机会',
        cooldown: 0,
        shijiQuote: '纵江东父兄怜而王我，我何面目见之？纵彼不言，籍独不愧于心乎？',
        shijiSource: '《史记·项羽本纪》'
    },
    {
        id: 'zhou-trial',
        name: '西周刑审制',
        category: 'politics',
        rarity: 3,
        description: '西周时期完善的刑事审判制度。',
        cost: { prestige: 15, popularity: 10 },
        effect: '民心+25，威望+15（法治昌明）',
        cooldown: 3,
        shijiQuote: '象以典刑，流宥五刑，鞭作官刑，扑作教刑，金作赎刑。',
        shijiSource: '《史记·五帝本纪》'
    },
    {
        id: 'shiji-author',
        name: '史记作者识别',
        category: 'meta',
        rarity: 5,
        description: '特殊技能：了解《史记》的作者和创作背景。',
        cost: {},
        effect: '解锁隐藏剧情和彩蛋',
        cooldown: 0,
        shijiQuote: '太史公曰：余读谍记，黄帝以来皆有年数。稽其历谱谍终始五德之传，古文咸不同，乖异。',
        shijiSource: '《史记·太史公自序》'
    }
];

// 游戏状态
let gameState = {
    turn: 1,
    resources: {
        wealth: 100,
        popularity: 100,
        military: 100,
        prestige: 100
    },
    hand: [],
    usedSkills: new Set(),
    currentChapter: 1,
    currentScene: 0
};

// 剧情数据
const STORY_CHAPTERS = [
    {
        title: '第一章：商周之变',
        scenes: [
            {
                title: '起兵伐纣',
                text: '公元前1046年，商纣王暴虐无道，酒池肉林，宠信妲己，诛杀忠臣。周武王姬发在姜子牙等贤臣辅佐下，决定起兵伐纣，为天下除害。',
                choices: [
                    {
                        text: '立即起兵，直取朝歌',
                        effect: () => {
                            updateResources({ military: -20, prestige: +10 });
                            nextScene();
                        }
                    },
                    {
                        text: '先联络诸侯，积蓄力量',
                        effect: () => {
                            updateResources({ prestige: +20, wealth: -10 });
                            nextScene();
                        }
                    }
                ]
            },
            {
                title: '牧野决战',
                text: '周军与商军在牧野相遇。商军虽众，但士气低落。此时，你需要选择战术...',
                choices: [
                    {
                        text: '使用"牧野之战"技能（需要：军力40，威望30）',
                        requireSkill: 'muye-battle',
                        effect: () => {
                            if (canUseSkill('muye-battle')) {
                                useSkill('muye-battle');
                                showMessage('大获全胜！商军前徒倒戈，纣王自焚于鹿台。周朝建立！');
                                updateResources({ prestige: +100, military: +50 });
                                nextScene();
                            } else {
                                showMessage('资源不足，无法使用此技能！');
                            }
                        }
                    },
                    {
                        text: '常规作战',
                        effect: () => {
                            updateResources({ military: -30, prestige: +30 });
                            showMessage('经过苦战，终于击败商军。');
                            nextScene();
                        }
                    }
                ]
            },
            {
                title: '章节完成',
                text: '恭喜！你成功帮助周武王推翻商纣，建立周朝。历史的车轮继续向前...',
                choices: [
                    {
                        text: '返回主菜单',
                        effect: () => {
                            showMainMenu();
                        }
                    }
                ],
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
    }

            }
        ]
    }
];

// 初始化游戏
function initGame() {
    // 初始化手牌
    gameState.hand = ['three-laws', 'knowing-talent', 'hongmen-escape'];
    updateUI();
}

// 显示主菜单
function showMainMenu() {
    hideAllScreens();
    document.getElementById('main-menu').classList.add('active');
}

// 开始故事模式
function startStoryMode() {
    hideAllScreens();
    document.getElementById('game-screen').classList.add('active');
    gameState.currentChapter = 0;
    gameState.currentScene = 0;
    initGame();
    loadScene();
}

// 加载场景
function loadScene() {
    const chapter = STORY_CHAPTERS[gameState.currentChapter];
    const scene = chapter.scenes[gameState.currentScene];
    
    document.getElementById('story-title').textContent = scene.title;
    document.getElementById('story-text').textContent = scene.text;
    
    // 显示选择
    const choicesContainer = document.getElementById('story-choices');
    choicesContainer.innerHTML = '';
    
    scene.choices.forEach(choice => {
        const btn = document.createElement('button');
        btn.className = 'choice-btn';
        btn.textContent = choice.text;
        btn.onclick = choice.effect;
        choicesContainer.appendChild(btn);
    });
    
    updateUI();
}

// 下一场景
function nextScene() {
    gameState.currentScene++;
    const chapter = STORY_CHAPTERS[gameState.currentChapter];
    
    if (gameState.currentScene >= chapter.scenes.length) {
        // 章节结束
        gameState.currentChapter++;
        gameState.currentScene = 0;
    }
    
    loadScene();
}

// 显示技能图鉴
function showSkillLibrary() {
    hideAllScreens();
    document.getElementById('skill-library').classList.add('active');
    renderSkillCards();
}

// 渲染技能卡牌
function renderSkillCards(filter = 'all') {
    const container = document.getElementById('skill-cards-container');
    container.innerHTML = '';
    
    const filteredSkills = filter === 'all' 
        ? SKILLS 
        : SKILLS.filter(s => s.category === filter);
    
    filteredSkills.forEach(skill => {
        const card = createSkillCard(skill);
        container.appendChild(card);
    });
}

// 创建技能卡牌元素
function createSkillCard(skill) {
    const card = document.createElement('div');
    card.className = `skill-card ${skill.category}`;
    
    const rarity = '★'.repeat(skill.rarity);
    
    card.innerHTML = `
        <div class="skill-header">
            <span class="skill-name">${skill.name}</span>
            <span class="skill-rarity">${rarity}</span>
        </div>
        <div class="skill-category">${getCategoryName(skill.category)}</div>
        <div class="skill-description">${skill.description}</div>
        <div class="skill-cost">
            ${Object.entries(skill.cost).map(([key, value]) => 
                `<span class="cost-item">${getResourceIcon(key)} -${value}</span>`
            ).join('')}
        </div>
        <div class="skill-effect">✨ ${skill.effect}</div>
    `;
    
    card.onclick = () => showSkillDetail(skill);
    
    return card;
}

// 显示技能详情
function showSkillDetail(skill) {
    const modal = document.getElementById('skill-modal');
    const detailContainer = document.getElementById('skill-detail');
    
    const rarity = '★'.repeat(skill.rarity);
    const canUse = canUseSkill(skill.id);
    
    detailContainer.innerHTML = `
        <h2>${skill.name} ${rarity}</h2>
        <div class="skill-detail-section">
            <h3>类型</h3>
            <p>${getCategoryName(skill.category)}</p>
        </div>
        <div class="skill-detail-section">
            <h3>描述</h3>
            <p>${skill.description}</p>
        </div>
        <div class="skill-detail-section">
            <h3>消耗</h3>
            <div class="skill-cost">
                ${Object.entries(skill.cost).map(([key, value]) => 
                    `<span class="cost-item">${getResourceIcon(key)} ${getResourceName(key)}: -${value}</span>`
                ).join('')}
            </div>
        </div>
        <div class="skill-detail-section">
            <h3>效果</h3>
            <p class="skill-effect">${skill.effect}</p>
        </div>
        <div class="skill-detail-section">
            <h3>冷却时间</h3>
            <p>${skill.cooldown} 回合</p>
        </div>
        <div class="shiji-quote">
            <p>${skill.shijiQuote}</p>
            <p style="text-align: right; margin-top: 10px;">—— ${skill.shijiSource}</p>
        </div>
        <button class="use-skill-btn" ${!canUse ? 'disabled' : ''} onclick="useSkillFromModal('${skill.id}')">
            ${canUse ? '使用技能' : '资源不足'}
        </button>
    `;
    
    modal.classList.add('active');
}

// 关闭技能详情
function closeSkillModal() {
    document.getElementById('skill-modal').classList.remove('active');
}

// 显示教程
function showTutorial() {
    document.getElementById('tutorial-modal').classList.add('active');
}

// 关闭教程
function closeTutorial() {
    document.getElementById('tutorial-modal').classList.remove('active');
}

// 过滤技能
function filterSkills(category) {
    // 更新按钮状态
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    renderSkillCards(category);
}

// 检查是否可以使用技能
function canUseSkill(skillId) {
    const skill = SKILLS.find(s => s.id === skillId);
    if (!skill) return false;
    
    // 检查资源
    for (const [resource, cost] of Object.entries(skill.cost)) {
        if (gameState.resources[resource] < cost) {
            return false;
        }
    }
    
    // 检查冷却
    if (gameState.usedSkills.has(skillId)) {
        return false;
    }
    
    return true;
}

// 使用技能
function useSkill(skillId) {
    const skill = SKILLS.find(s => s.id === skillId);
    if (!skill || !canUseSkill(skillId)) return false;
    
    // 扣除资源
    for (const [resource, cost] of Object.entries(skill.cost)) {
        gameState.resources[resource] -= cost;
    }
    
    // 标记已使用
    gameState.usedSkills.add(skillId);
    
    updateUI();
    showMessage(`使用了技能：${skill.name}`);
    
    return true;
}

// 从弹窗使用技能
function useSkillFromModal(skillId) {
    if (useSkill(skillId)) {
        closeSkillModal();
    }
}

// 更新资源
function updateResources(changes) {
    for (const [resource, change] of Object.entries(changes)) {
        gameState.resources[resource] = Math.max(0, Math.min(200, gameState.resources[resource] + change));
    }
    updateUI();
}

// 结束回合
function endTurn() {
    gameState.turn++;
    gameState.usedSkills.clear();
    
    // 每回合恢复少量资源
    updateResources({
        wealth: 10,
        popularity: 5,
        military: 5,
        prestige: 5
    });
    
    showMessage(`回合 ${gameState.turn} 开始`);
}

// 更新UI
function updateUI() {
    // 更新资源显示
    document.getElementById('wealth').textContent = gameState.resources.wealth;
    document.getElementById('popularity').textContent = gameState.resources.popularity;
    document.getElementById('military').textContent = gameState.resources.military;
    document.getElementById('prestige').textContent = gameState.resources.prestige;
    document.getElementById('current-turn').textContent = gameState.turn;
    
    // 更新手牌
    renderHandCards();
}

// 渲染手牌
function renderHandCards() {
    const container = document.getElementById('hand-cards');
    container.innerHTML = '';
    
    gameState.hand.forEach(skillId => {
        const skill = SKILLS.find(s => s.id === skillId);
        if (skill) {
            const card = createSkillCard(skill);
            card.classList.add('hand-card');
            container.appendChild(card);
        }
    });
}

// 显示消息
function showMessage(message) {
    // 简单的alert，可以后续改进为更好的UI
    alert(message);
}

// 隐藏所有屏幕
function hideAllScreens() {
    document.querySelectorAll('.screen').forEach(screen => {
        screen.classList.remove('active');
    });
}

// 辅助函数
function getCategoryName(category) {
    const names = {
        military: '军事策略',
        politics: '政治制度',
        culture: '文化思想',
        leadership: '领导管理',
        history: '历史事件'
    };
    return names[category] || category;
}

function getResourceIcon(resource) {
    const icons = {
        wealth: '💰',
        popularity: '👥',
        military: '⚔️',
        prestige: '📜'
    };
    return icons[resource] || '';
}

function getResourceName(resource) {
    const names = {
        wealth: '财富',
        popularity: '民心',
        military: '军力',
        prestige: '威望'
    };
    return names[resource] || resource;
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    showMainMenu();
});
