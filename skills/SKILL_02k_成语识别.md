---
name: skill-02k
title: 成语识别
description: 在《史记》原文中识别固化语言单元（成语/熟语/引用）并决定是否作 〘※〙 标注的工作流。涵盖识别源、反思迭代、双轨架构（已标注 vs 总结性）、验证与排除清单。本 Skill 只讲识别，标注符号规范见 02j，词表通用原则见 02h。
version: 1.0
last_updated: 2026-04-21
---

# SKILL 02k: 成语识别

> 识别 = 决定"哪一段原文算成语"。与标注（02j 讲怎么写）、词表（02h 讲通用原则）正交。
> 成语识别的核心难点：史记中的"成语"常与现代标准形式字序/字形不同，且常与人名/地名/动词实体重叠。

---

## 一、何时使用

- 对新章节首次铺成语标注
- 对已有标注进行反思：发现"本该是成语但标了实体"、"标了太短非成语"等错误
- 审视《史记成语典故.md》词表的条目与原文的对应关系
- 用户通过 `/btw` 点出某处应/不应为成语，需同步更新词表与章节

## 二、识别源（由硬到软）

| 源类型 | 说明 | 文件 |
|------|------|------|
| **权威词表** | 人工整理的《史记》成语典故集 | `kg/vocabularies/data/史记成语典故.md` |
| **原文验证** | 词表条目的"原文"栏必须在对应章节（去标注纯文本）中找到锚句 | `scripts/verify_summarized_chengyu.py` |
| **跨领域知识** | 现代汉语成语词典、汉语大词典；AI 判断固化度 | — |
| **用户点校** | 通过 `/btw 片段 → 规范形式` 直接校正 | 手动 |

**边界约束**：原文字符必须存在；成语标注**不修改原文**，只加括号。如果现代成语 A 源自史记句段 B（字序/字形不同），则用消歧形式 `〘※B|A〙`（见 02j §消歧原则）。

## 三、识别决策规则

### 3.1 什么算成语

✅ **标**
- 四字固化熟语（`移风易俗`、`名山大川`）
- 非四字但固化的熟语（`桃李不言，下自成蹊`）
- 后世演变为成语、在史记中为首见或早期用例的表达

❌ **不标**
- 普通多字短语，可逐字理解（`遣使求和`、`斩将夺旗`）
- 2-3 字的名词或短语，非固化成语（`人彘`、`智囊`、`凿空`、`真将军`）
- 36 计名（`反间计`）、三字典故名（`批逆鳞`）
- 非史记来源的成语（源自《左传》《战国策》《论语》等）

### 3.2 三问法

1. 后世汉语中是否有此固化成语？
2. 意义是否不能完全从字面推导？
3. 在史记中是否为"引用前代"或"首见"用法？

任意两问为"是"即倾向标注。

### 3.3 与实体/动词冲突时的优先级

规则：**成语优先于实体与动词**（语言层整体 > 局部指称）。

例外：若内部实体在本段承担**实质性指称功能**（如"泰山封禅"中"泰山"是具体地点），则标实体不标成语。

判断标准：内部专名能否替换为另一具体专名而语义自然？
- `名山大川` → 不能（泛指）→ 成语
- `泰山` → 能（换成其他山）→ 地名

冲突示例：
```
✓ 〘※完璧归赵〙            （原文 完〖•璧〗归〖◆赵〗，赵特指国名，仍整体标成语）
✓ 〘※楚虽三户，亡秦必楚〙  （原文夹有 〖◆楚〗〖◆秦〗，仍整体标成语）
✓ 〖=泰山〗封禅           （泰山是具体地点，标地名不标成语）
```

详细符号规范与消歧写法见 [SKILL_02j 修辞标注](SKILL_02j_修辞标注.md)。

---

## 四、工作流：四轮反思

### 轮 1：批量初标（基于词表直查）

**输入**：`kg/vocabularies/data/史记成语典故.md`
**脚本**：`scripts/annotate_chengyu.py`
**策略**：
- A. 直接搜 `chengyu_name` → 若在干净文本中找到且未被占用 → 标注
- B. `chengyu_name` 不在原文，但词表"原文"栏短语（≤10字）在原文 → `〘※shiji_form|chengyu_name〙`
- C. 被整个实体括住且实体文字 == 成语 → 删实体，改成语

**覆盖**：约 150–180 条一次到位。

### 轮 2：反思与清理

**诊断脚本**：`scripts/reflect_chengyu_round2c.py`（基于"去标注纯文本 + 位置映射"查找被实体标注分割的成语）

**修复脚本**：`scripts/fix_chengyu_round2.py`
- 去除轮 1 产生的**短标**（`INVALID_SHORT_TAGS`：不食言/画一/智囊/凿空/真将军/人彘/反间计/批逆鳞）
- **实体/动词 → 成语 转换**：当成语跨越 `〖〗`/`⟦⟧` 边界且整体匹配时，吸收边界括号并整体重写为 `〘※〙`

**安全机制**：
- 扩展边界使括号对平衡
- 扩展后 `strip_all_markup(region) == chengyu_name` 才执行
- 右→左扫描避免位置错乱
- 写入前 `lint_text_integrity.py` 前后比较纯文本一致

典型案例：
```
完〖•璧〗归〖◆赵〗           → 〘※完璧归赵〙
〖+鸿鹄〗之志               → 〘※鸿鹄之志〙
土⟦○崩⟧瓦解                → 〘※土崩瓦解〙
〖%鸡鸣|时辰〗狗盗          → 〘※鸡鸣狗盗〙
```

### 轮 3：用户点校（增量）

用户以 `/btw <原文片段> -> <规范形式>` 指示修正。典型动作：
- 添加消歧：`养虎自遗患 -> 养虎遗患` → `〘※养虎自遗患|养虎遗患〙`
- 新增标注：`扬扬甚自得 -> 扬扬自得` → `〘※扬扬甚自得|扬扬自得〙`
- 修复实体误标：`不食〖◆周〗〖•粟〗 -> 耻食周粟` → `〘※不食周粟|耻食周粟〙`

每次点校后必须：
1. 修改对应 `chapter_md/*.tagged.md`
2. 同步更新 `kg/vocabularies/data/史记成语典故.md`
3. 重新运行 `extract_chengyu_tagged.py` + `build_chengyu_summarized.py`

### 轮 4：总结性补充（不标注但保留）

有些成语**无法逐字标注**：
- 史记描述事件但从未出现成语名（`助纣为虐`、`赵氏孤儿`、`窃符救赵`）
- 字序颠倒且无连续原文锚句（括号叙述性总结）

这些条目通过 `build_chengyu_summarized.py` 从源 MD 生成 `data/chengyu_summarized.json`，**不影响章节标注**。

---

## 五、双轨数据架构

| 文件 | 内容 | 生成方式 | 覆盖来源 |
|------|------|---------|---------|
| `kg/vocabularies/data/史记成语典故.md` | 权威源表（约 350 条） | **人工维护** | — |
| `data/chengyu.json` / `chengyu.md` | 已标注成语（约 210 条） | `extract_chengyu_tagged.py` | `chapter_md/*.tagged.md` 中的 `〘※〙` |
| `data/chengyu_summarized.json` / `chengyu_summarized.md` | 总结性成语（约 155 条） | `build_chengyu_summarized.py` | 源 MD 中未被标注的条目 |
| `docs/special/chengyu.html` | 合并展示 | `render_chengyu_html.py` | 上两个 JSON 合并 |

**互不冲掉**：
- `extract_chengyu_tagged.py` 只读 tagged.md，只写 `chengyu.json`
- `build_chengyu_summarized.py` 只读源 MD，只写 `chengyu_summarized.json`
- 用户对源 MD 的修改不会被脚本重写；脚本对数据文件的覆盖不会污染源 MD

---

## 六、验证四分类

`verify_summarized_chengyu.py` 对每条词表条目分类：

| 状态 | 含义 | 处理 |
|------|------|------|
| **tagged** | 章节中已有 `〘※name〙` 或 `〘※shiji_form|name〙` | 进入 `chengyu.json`，从总结表排除 |
| **verbatim** | 原文栏字串（规范化后）直接在纯文本中 | 可选补标，或留作总结 |
| **partial** | 省略号分段，至少一段锚句可证 | 留作总结 |
| **narrative** | 原文栏是括号叙述（如 `（萧何定法，曹参守而勿失）`）| 留作总结，HTML 打"叙事性总结"徽章 |
| **unverified** | 原文栏在纯文本中完全找不到 | **必须处理**：要么删除条目（非史记），要么订正章节/引文 |

**规范化**覆盖：全半角标点统一去除；异体字合并（`脣→唇`、`甕→瓮`、`於→于`、`穀→谷`、`説→说`、`飜→翻`）。

**每次修改源 MD 后必跑此脚本**。目标：`unverified = 0`。

---

## 七、排除清单（不属于史记的常见误入）

**非史记来源**（从源 MD 剔除）：
| 成语 | 真实出处 |
|------|---------|
| 唇亡齿寒 | 左传（史记 039 虽有"脣亡则齿寒"，已归入 039 而非 043） |
| 过犹不及 | 论语 |
| 悬梁刺股 | 战国策（刺股）+ 汉书-era（悬梁）|
| 狡兔三窟 | 战国策 |

**短名词/伪成语**（2-3 字，不标注）：
- `人彘`、`智囊`、`凿空`、`画一`、`不食言`、`真将军`、`反间计`、`批逆鳞`

**章节误标**（从源 MD 迁移）：
- `当断不断，反受其乱`：046 → 052 齐悼惠王世家（召平语）
- `以貌取人`：047 → 067 仲尼弟子列传
- `重足而立，侧目而视`：122 → 120 汲郑列传

---

## 八、脚本索引

| 脚本 | 作用 |
|------|------|
| `scripts/annotate_chengyu.py` | 轮 1：批量初标 |
| `scripts/reflect_chengyu_round2c.py` | 轮 2 诊断：找出实体覆盖的成语 |
| `scripts/fix_chengyu_round2.py` | 轮 2 修复：去短标 + 实体→成语转换 |
| `scripts/verify_summarized_chengyu.py` | 验证词表条目 vs 原文 |
| `scripts/build_chengyu_summarized.py` | 构建总结性数据文件 |
| `scripts/extract_chengyu_tagged.py` | 从 tagged.md 提取已标注成语 → `chengyu.json` |
| `scripts/render_chengyu_html.py` | 合并两份 JSON 渲染 HTML |
| `scripts/lint_text_integrity.py` | 标注文本完整性校验（必跑） |

**标准流程**：
```bash
# 初始或反思后
python scripts/annotate_chengyu.py              # 仅新章节
python scripts/fix_chengyu_round2.py            # 反思
python scripts/lint_text_integrity.py           # 完整性校验（必跑）
python scripts/extract_chengyu_tagged.py        # → chengyu.json
python scripts/build_chengyu_summarized.py      # → chengyu_summarized.json
python scripts/render_chengyu_html.py           # → docs/special/chengyu.html
python generate_all_chapters.py                 # 章节 HTML
```

---

## 九、检查清单

**识别前**
- [ ] 确认词表条目的"原文"栏在对应章节纯文本中有锚句
- [ ] 确认不是非史记来源（左传/战国策/论语/汉书）
- [ ] 确认长度 ≥ 4 字，或是固化六字/多字熟语

**识别中**
- [ ] 跨实体/动词边界的成语：选择整体成语还是保留实体？（参考 §3.3）
- [ ] 字序或字形与现代不同：需要消歧 `〘※shiji|modern〙`
- [ ] Markdown 标题行不标注

**识别后**
- [ ] 跑 `lint_text_integrity.py` 前后纯文本一致
- [ ] 跑 `verify_summarized_chengyu.py` 确认 `unverified = 0`
- [ ] 重建 `chengyu.json` / `chengyu_summarized.json` / HTML

---

## 十、关联文档

- [SKILL_02j 修辞标注](SKILL_02j_修辞标注.md) — 标注符号规范、消歧写法、HTML 渲染
- [SKILL_02h 词表构建](SKILL_02h_词表构建.md) — 词表（glossary）通用原则
- [SKILL_01g 标注符号集合原则](SKILL_01g_标注符号集合原则.md) — 三层括号框架
- [SKILL_03a 实体标注](SKILL_03a_实体标注.md) — 实体层优先级
