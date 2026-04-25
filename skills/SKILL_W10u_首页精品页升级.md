---
name: SKILL_W10u_首页精品页升级
title: Wiki 内务整理 H21：首页精品页全面检查与升级
description: 扫描当前会出现在首页的页面，逐一执行质量检查清单：结构完整性、内容质量、配图、infobox 字段、PN 引注。不合格项写入修复队列，合格页面通过 featured=true 加盖认证。
---

# SKILL W10u: 首页精品页升级（H21）

> "首页是知识库的门面，每个出现在首页的页面都代表整个项目的水准。"

---

## 一、何时执行

| 触发场景 | 说明 |
|---|---|
| 每 50 轮执行一次全面扫描 | 定期巡检 |
| 用户发现某首页页面质量不达标 | 立即触发 |
| 新增 `featured: true` 页面后 | 验收检查 |
| 首页策略变更后 | 全量重审 |

---

## 二、首页页面识别方法

首页显示哪些页面由两个因素决定：

### 评分规则
```
scoreOf = (featured ? 1000 : 0) + quality_score
quality_score = refs//20 + tag_bonus + rev_bonus + size_bonus + manual_bonus + narrative_bonus
```

### 分桶上限
| type | 上限 |
|------|------|
| person | 6 |
| story | 4 |
| sanwen | 3 |
| overview | 2 |
| concept | 2 |
| chapter | 2 |

### 识别脚本
```python
# 找出当前会上首页的页面
import json

data = json.load(open('wiki/public/pages.json'))
pages = data['pages']

CAPS = {'person': 6, 'story': 4, 'sanwen': 3, 'overview': 2, 'concept': 2, 'chapter': 2}
SKIP = {'redirect', 'disambiguation', 'year', 'place', 'event', 'special', 'list', '侯国', 'skill'}

def score(p):
    return (1000 if p.get('featured') else 0) + (p.get('quality_score') or 0)

all_pages = [{'id': k, **v} for k, v in pages.items()]
all_pages.sort(key=score, reverse=True)

counts = {}
featured = []
for p in all_pages:
    if len(featured) >= 18: break
    t = p.get('type', '')
    if t in SKIP or t not in CAPS: continue
    n = counts.get(t, 0)
    if n >= CAPS[t]: continue
    counts[t] = n + 1
    featured.append(p)

for p in featured:
    print(f"{'★' if p.get('featured') else ' '} [{p.get('type'):10}] q={p.get('quality_score',0):3d} {p['id']}")
```

```bash
cd /home/baojie/work/knowledge/shiji-kb
python3 -c "$(cat scripts/list_homepage_pages.py 2>/dev/null || echo 'print(\"需要创建 scripts/list_homepage_pages.py\")')"
```

---

## 三、每页检查清单

对每个首页页面，逐项核查：

### 3.1 结构字段
- [ ] `type` 正确（person/overview/sanwen/story/concept/chapter）
- [ ] `label` 与页面标题一致
- [ ] `pn` 字段存在且格式正确（`(NNN-M)` 或 `(NNN-M)(NNN-M)`）
- [ ] `sources` 字段列出了来源章节
- [ ] `tags` 至少 2 个，分类合理
- [ ] `aliases` 包含常见称呼（对 person 尤其重要）

### 3.2 内容质量
- [ ] 无 `<!-- stub:` 块
- [ ] 首段（lead paragraph）清晰概括页面主题，≥50字
- [ ] 有实质性散文分析（不只是引文/列表堆砌）
- [ ] 无重复内容（同一段落/原文出现两次）
- [ ] 引文段落有 PN 标注（如 `（072-6）`）
- [ ] 断链已修复或已标注
- [ ] 有相关人物/相关章节链接

### 3.3 配图
- [ ] frontmatter 有 `image` 字段（`image: images/xxx.jpg`）
- [ ] 图片文件存在于 `wiki/public/images/`
- [ ] 有 `image_caption` 说明图片内容
- [ ] （可选）有 `image_credit` 图片来源

**配图优先来源**：
- 维基共享资源（Wikimedia Commons）中的古地图、古画、出土文物
- 命名规范：`images/{类型}_{页面id}.jpg`（如 `images/person_穰侯.jpg`）

### 3.4 精品认证
- [ ] 以上所有项通过后，确认或设置 `featured: true`
- [ ] 如有重大问题未修复，移除 `featured: true`（防止劣质页面占首页位）
- [ ] 在 frontmatter `tags` 中追加 `首页精品`（若不存在）——此 tag 是入过首页的永久标志

**追加 `首页精品` tag 的操作**（每个 H21 任务完成后执行）：
```python
# 读取页面，在 tags 列表追加「首页精品」
import re
from pathlib import Path

slug = 'PAGE_SLUG'  # 替换为实际 slug
path = Path(f'wiki/public/pages/{slug}.md')
text = path.read_text(encoding='utf-8')

# 内联 tags: [a, b] 格式
def add_tag(text, tag):
    def replace_tags(m):
        fm = m.group(1)
        inline = re.search(r'^(tags:\s*\[)([^\]]*)\]', fm, re.MULTILINE)
        if inline:
            current = [x.strip().strip('"\'') for x in inline.group(2).split(',') if x.strip()]
            if tag not in current:
                current.append(tag)
            new_fm = fm[:inline.start()] + f'tags: [{", ".join(current)}]' + fm[inline.end():]
            return f'---\n{new_fm}\n---'
        return m.group(0)
    return re.sub(r'^---\n(.*?)\n---', replace_tags, text, flags=re.DOTALL)

path.write_text(add_tag(text, '首页精品'), encoding='utf-8')
print(f'✓ {slug}: 已追加「首页精品」tag')
```

---

## 四、各类型页面的优化方法

### 4.1 所有类型共用

**修复 frontmatter 字段**：
```yaml
# 必须有的字段
label: 页面名称          # 与 id 一致
type: person/overview/sanwen/story/...
pn: (NNN-M)              # 主要原典段落号，多个用 (NNN-M)(NNN-M) 连写
sources: [章节名]         # 来源章节列表
tags: [tag1, tag2, ...]  # 至少 2 个

# 精品页还需要
featured: true
image: images/文件名.jpg
image_caption: 图片说明
image_credit: "Wikimedia Commons / ..."
```

**补充 PN 方法**：在页面正文或引文中找 `（NNN-M）` 格式的引注，取主要段落号填入 pn 字段。参见 `SKILL_W10e_原文溯源增补.md`。

**补充配图方法**：
1. 在 Wikimedia Commons 搜索相关词（英文：历史人物名 + "China ancient"，地名 + "map"）
2. 下载图片到 `wiki/public/images/`，命名为 `{类型}_{页面id缩写}.jpg`
3. 在 frontmatter 加 `image`/`image_caption`/`image_credit`

---

### 4.2 overview（综述页）优化步骤

overview 是最容易出现结构混乱的类型，常见问题：多个 h1、内容段重复、原文太长。

**标准结构**：
```markdown
---
frontmatter（含 label/type/pn/sources/tags/featured）
---

# 页面标题

一句话导言（50-100字，概括人物/事件核心）。

---

## 背景 / 崛起        ← 时间线起点
## 主要事件1          ← 核心事件（可多个）
## 主要事件2
## 结局 / 落幕        ← 时间线终点
## 历史意义           ← 分析评价

## 相关人物
## 相关章节
```

**具体操作**：

1. **去重**：检查是否有多个 `# 一级标题`——只保留一个。第二个 h1 以下的内容若与前面重复，整节删除；若有独特内容，合并到合适的 h2 节。
   ```bash
   grep -n "^# " wiki/public/pages/PAGE.md
   ```

2. **合并冗余节**：如"崛起"和"权力巅峰"开头重复了同一段话，删除其中一份；保留更详细的那个节，把另一节的独特内容移入。

3. **处理原文节**：长篇原文（>500字）移至 `## 原文摘录` 并只保留最关键段落（1-3段），其余用 pn 引注指向章节页。
   ```markdown
   ## 原文摘录
   > **穰侯出关，辎车千乘有余。**（072-14）
   
   完整原文见 [[072_穰侯列传]]（072-1 至 072-14）。
   ```

4. **加导言**：h1 标题下紧接 50-100 字导言，概括核心人物/事件，不用 h2。

---

### 4.3 sanwen（散文/策论页）优化步骤

sanwen 页面已有标准结构（背景/全文/解读），主要问题是缺字段和配图。

**标准结构**：
```markdown
---
frontmatter（含 pn/sources/chapter_no/essay_type/author）
---

# 散文标题

一句话导言（出处 + 核心主张）。

---

## 背景          ← 历史语境（≤300字）
## 全文          ← 原文引文块 + pn 标注
## 解读          ← 论证结构分析（核心价值所在）
## 历史评析      ← 跨文本比较 / 思想史意义

## 相关人物
## 相关章节
```

**具体操作**：

1. **pn 字段**：从 `## 全文` 引文的 `（NNN-M）` 标注中取段落号，填入 frontmatter `pn: (NNN-M)`。

2. **sources 字段**：与 chapter_no 对应，填章节名（如 `chapter_no: "072"` → `sources: [穰侯列传]`）。

3. **导言质量**：首段要直接说明"这是什么、出自哪里、核心论点是什么"，避免只写背景。

4. **解读结构**：按论证层次（一、二、三…）拆分，每层给出原文证据 + 分析，不要只是转述原文。

---

### 4.4 person（人物页）优化步骤

**标准结构**：
```markdown
---
frontmatter（含 birth_ce/death_ce/aliases/pn/sources）
---

# 人名

导言（身份 + 时代 + 核心贡献/命运，50-80字）。

## 生平
## 主要事迹    ← 或按时间分节
## 相关人物
## 史记引文
## 相关章节
```

**具体操作**：
1. infobox 字段：检查 `birth_ce`/`death_ce`/`aliases`/`office`/`title` 是否填写
2. pn：从页面内引文标注中提取，填入 frontmatter
3. 导言不等于 infobox 的文字化——要有人物评价，不只是"XX，战国时期赵国人"

---

### 4.5 重复内容检测
```bash
python3 -c "
content = open('wiki/public/pages/PAGE.md').read()
paras = [p.strip() for p in content.split('\n\n') if len(p.strip()) > 50]
seen = {}
for i, p in enumerate(paras):
    key = p[:100]
    if key in seen:
        print(f'段落 {i} 与段落 {seen[key]} 重复: {key[:60]}...')
    else:
        seen[key] = i
"
```

---

## 五、队列记录格式

```markdown
<!-- 在 housekeeping_queue.md 追加 H21 条目 -->
- [ ] H21 | P1 | [[PAGE]] | 首页精品页升级
  - 类型: overview / sanwen / person ...
  - 问题: [重复内容/缺pn/缺配图/缺分析/有断链]
  - 具体: 描述具体问题
```

---

## 六、优先级策略

处理顺序：
1. **P0（立即）**：有 `featured: true` 但内容有重复/错误的页面
2. **P1（本轮）**：无图但质量不差的页面（补图效果明显）
3. **P2（下轮）**：内容完整但 pn/tags 不全的页面

---

## 七、首页策略说明

### 当前策略（2026-04）
- `featured: true` 加 1000 分，手动设置，代表认证精品
- `quality_score` 自动计算，字数长/引注多/多次编辑得高分
- 分桶保证类型多样性

### 已知问题
- 长页面自动得高分，草稿性综述页（如过长的 overview）可能挤入首页
- 缺图的首页卡片视觉效果差
- `featured` 标记没有对应的质量门槛，可以不经检查就设置

### 改进方向（TODO）
- [ ] 为 `featured: true` 制定最低质量门槛（有图+有pn+无重复内容）
- [ ] 为 overview 类型提高 size_bonus 的上限或降低权重，避免"篇幅即质量"
- [ ] 首页卡片无图时显示类型 icon 作为视觉占位

---

## 八、工具与脚本

| 工具 | 用途 |
|------|------|
| `python3 wiki/scripts/butler/discover_homepage_new.py` | **扫描首页新晋页面**（缺「首页精品」tag → 输出 H21 队列条目） |
| `python3 scripts/list_homepage_pages.py` | 列出当前首页会出现的页面 |
| `wiki/public/pages.json` | 读取 quality_score、featured、type 等字段 |
| `wiki/public/images/` | 配图存放目录 |
| `wiki/logs/butler/housekeeping_queue.md` | 写入 H21 任务队列 |

---

## 九、成功标准

每轮 H21 执行完成后：
- [ ] 已扫描当前首页页面列表（不超过18个）
- [ ] 每个页面完成三级核查（结构/内容/配图）
- [ ] 发现的问题写入队列（不强制当轮修复所有问题）
- [ ] 至少处理 1 个具体问题（修复重复内容 / 补图 / 补 pn）
- [ ] 质量明显不达标的页面移除 `featured: true`

---

## 相关路径

- `wiki/logs/butler/housekeeping_queue.md` — H21 任务队列
- `wiki/public/images/` — 配图目录
- `skills/SKILL_W10h_精品页增补.md` — H7：识别新精品页候选（互补任务）
- `skills/SKILL_W8_精品页建设方法论.md` — 执行精品页建设的完整方法论
- `skills/SKILL_W10e_原文溯源增补.md` — 补充 pn 字段
