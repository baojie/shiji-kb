---
name: SKILL_W10s_正文断言核验
title: Wiki 内务整理 H19：正文断言 PN 核验与追加
description: 检测正文中有叙述句但缺乏 PN 引注（句子数/PN引注数比 > 5）的页面，为关键断言句找到原文段落并追加行内 PN 引注，每轮 ≤3 句。
---

# SKILL W10s: 正文断言核验（H19）

> "每个断言都应该有原文背书。PN 引注不是装饰，是可验证性的承诺。"

---

## 一、何时执行

| 触发场景 | 优先级 |
|---|---|
| 正文叙述句多但 PN 引注少（比值 > 5:1） | P1 |
| 精品页建设（W8）前的前置质量检查 | P1 |
| 用户要求某页面增加引注 | P1 |

**与 H4 的区分**：
- H4（W10e）：frontmatter 完全无 pn 字段，属于首次溯源
- H19（本文）：已有部分 PN，但正文中仍有大量无引注断言句

---

## 二、发现候选（扫描方法）

```bash
# 统计各页面的句子数与 PN 引注数，找比值 > 5 的
python3 -c "
import glob, re
for f in glob.glob('wiki/public/pages/*.md'):
    content = open(f).read()
    # 统计叙述句（以。结尾）
    sents = len(re.findall(r'[^。]*。', content))
    # 统计 PN 引注（(NNN-NN) 格式）
    pns = len(re.findall(r'\(\d{3}-\d+', content))
    if sents > 5 and pns > 0 and sents / max(pns, 1) > 5:
        print(f'{sents}/{pns}={sents//max(pns,1)}\t{f.split(\"/\")[-1]}')
" | sort -rn | head -20
```

---

## 三、执行步骤

### Step 1：读页面，识别断言句

```bash
cat wiki/public/pages/目标页.md
```

找出**关键断言句**：包含具体事实（年代、事件、人物关系、地名）的叙述句。

**优先候选断言**：
- 含年代数字的句子（如"公元前XXX年，X出任Y"）
- 含人物关系的句子（如"X是Y的臣子"）
- 含事件结果的句子（如"X战败，Y胜利"）

### Step 2：用 find_pn 脚本查找原文段落

```bash
# 若脚本存在
python3 wiki/scripts/butler/find_pn_for_quote.py "断言关键词" --context "人物名"

# 手动查找：在原文标注文件中搜索
grep -n "关键词" data/chapters/NNN_*.md | head -10
```

### Step 3：确认匹配正确（相似度 ≥ 0.8）

对照原文段落，确认：
1. 该段落确实支持页面中的断言
2. PN 编号格式：`(NNN-NN)` 中 NNN 是章节号，NN 是段落号

### Step 4：追加行内 PN 引注

**简洁格式**（推荐）：

```markdown
张仪于前328年出任秦相（069-15）。
```

**详细格式**（精品页用）：

```markdown
张仪于前328年出任秦相（见 [[069_张仪列传]] §15）。
```

### Step 5：写入并验证

```bash
python3 wiki/scripts/butler/edit_page.py "目标页" /tmp/annotated.md \
    --summary "w10s: H19 为N个断言追加PN引注（NNN-NN等）" \
    --author "butler"
```

**验证**：diff ≤ 10 行（每轮 ≤3 句引注）。

### Step 6：记录无法匹配的断言

```bash
echo '{"page": "目标页", "sent": "无法匹配的断言文本", "tried": "搜索关键词", "date": "2026-04-25"}' \
    >> wiki/logs/butler/failures.jsonl
```

**找不到原文段落 → 不附注，记录 failures.jsonl，不删除断言句**。

---

## 四、成功标准 / 完成条件

- [ ] 每轮处理 ≤ 3 个断言句
- [ ] 每个新增 PN 均经人工核实指向正确段落
- [ ] diff ≤ 10 行
- [ ] 无法匹配的断言记入 failures.jsonl，未强行附注
- [ ] 处理后该页 PN 密度有所提升

---

## 五、工具与脚本

| 工具 | 用途 |
|---|---|
| 上方 Python 脚本 | 批量发现 PN 密度低的页面 |
| `find_pn_for_quote.py` | 搜索断言对应的 PN |
| `wiki/scripts/butler/edit_page.py` | 写入修改 |
| `wiki/logs/butler/failures.jsonl` | 记录无法匹配的断言 |

---

## 六、PN 格式规范

| 情形 | 格式 | 示例 |
|---|---|---|
| 行内简洁 | `（NNN-NN）` | `（069-15）` |
| 行内详细 | `（见 [[NNN_X]] §NN）` | `（见 [[069_张仪列传]] §15）` |
| frontmatter pn | `(NNN-NN)` | `(069-15)` |

**不得使用**：`(069-15-16)` 连字符连接多段（参考 W10a §2.2）。

---

## 相关路径

- `wiki/logs/butler/housekeeping_queue.md` — H19 任务队列
- `wiki/logs/butler/failures.jsonl` — 无法匹配的断言记录
- `skills/SKILL_W10e_原文溯源增补.md` — H4，首次溯源走此流程
