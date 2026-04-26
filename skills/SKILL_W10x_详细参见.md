---
name: SKILL_W10x_详细参见
title: H25 详细参见——章节页引用深度页
description: 识别章节页中有更详细专题页（时间线、综合分析、列表）覆盖的内容，在章节页相关段落末尾添加"详细参见"引用，引导读者跳转。
---

# SKILL W10x: H25 详细参见

> "章节页是入口，专题页是深度。章节页应当指向更详细的描述，而不是让读者在目录里猜。"

---

## 一、定位

**触发场景**：某专题页（时间线、综合分析、征战汇总等）已存在，但覆盖该主题的章节页没有链回这个专题页。

典型例子：
- 曹参各征战章节页（曹参定三秦击楚、曹参定齐七十县……）→ 应引用 [[曹参征战时间线]]
- 某人物的多个传记章节页 → 应引用该人物的综合分析页或事件汇总页

---

## 二、判断标准

**满足以下全部条件才处理**：

1. 存在一个专题页（type: timeline / list / analysis / insight），明确以某人物/主题为核心
2. 有一个或多个章节页（type: event / chapter），内容是该专题页所涵盖主题的子集
3. 章节页中**尚无**对该专题页的 wikilink

**不处理的情况**：
- 章节页本身已是高质量页（quality: premium），结构完整，添加引用会破坏行文
- 专题页质量为 stub，引用意义不大
- 两个页面关联牵强，需要强行解释才能说明关联

---

## 三、添加格式

在章节页**正文最后**（`## 相关章节` 或 `---` 分隔线之前），插入 `:::seealso` 块：

```markdown
::: seealso
[[专题页名称]] — 一句话说明该专题页涵盖的范围
:::
```

多个专题页时每行一条：

```markdown
::: seealso
[[曹参征战时间线]] — 从龙起兵到击平陈豨的完整征战时序
[[曹参起事——从沛狱掾到攻城野战之冠]] — 深度分析
:::
```

**示例**（曹参定三秦击楚.md）：

```markdown
## 事件经过

……（原有内容不变）……

::: seealso
[[曹参征战时间线]] — 曹参从从龙起兵到击平陈豨的完整征战时序（054-001 ~ 054-008）
:::

## 相关章节
```

若章节页**无** `## 相关章节` 或尾部分隔，则追加到正文末尾。

> **渲染说明**：`:::seealso` 由 `semantic-block` 插件处理，渲染为绿色左边框的 📖 详细参见 卡片，与引文（红色左边框）视觉明确区分。禁止使用旧格式 `> **详细参见**：`（blockquote 样式与引文相同）。

---

## 四、操作流程

### 步骤 1：识别候选专题页

```bash
# 找出所有 timeline/list/analysis/insight 类型页面
python3 - <<'EOF'
import json
from pathlib import Path

pages = json.load(open("wiki/public/pages.json"))["pages"]
candidates = [
    (pid, p) for pid, p in pages.items()
    if p.get("type") in ("timeline", "list", "analysis", "insight")
    and p.get("quality") not in ("stub",)
]
for pid, p in candidates:
    print(f"[{p['type']}] {pid} — {p.get('description','')[:60]}")
EOF
```

### 步骤 2：匹配相关章节页

对每个专题页，提取其 `subject` 或标题中的人名/主题词，
在章节页（type: event/chapter）中找 `sources` 或 `description` 包含该词的页面。

```bash
SUBJECT="曹参"
DETAIL_PAGE="曹参征战时间线"

python3 - <<'EOF'
import json, re
from pathlib import Path

subject = "曹参"
detail_page = "曹参征战时间线"
pages_dir = Path("wiki/public/pages")

for f in sorted(pages_dir.glob("*.md")):
    text = f.read_text(encoding="utf-8")
    # 章节页包含主题词，但未引用专题页
    if subject in text and detail_page not in text:
        # 粗筛：type: event 或 chapter
        if "type: event" in text or "type: chapter" in text:
            print(f.name)
EOF
```

### 步骤 3：审查并插入

对每个候选章节页：

1. 阅读全文，确认关联成立
2. 找到合适插入点（`## 相关章节` 前，或正文末）
3. 插入 `:::seealso` 块（见§三格式规范）
4. 直接写入文件（Python `Path.write_text`）

```python
SEEALSO = (
    "::: seealso\n"
    "[[曹参征战时间线]] — 曹参从从龙起兵到击平陈豨的完整征战时序（054-001 ~ 054-008）\n"
    ":::"
)
text = f.read_text(encoding="utf-8")
f.write_text(text.replace("\n\n---\n\n## 相关章节", f"\n\n{SEEALSO}\n\n---\n\n## 相关章节"), encoding="utf-8")
```

### 步骤 4：记录（必须，不可省略）

**每次编辑后立即调用**，不可事后批量补录：

```bash
python3 wiki/scripts/butler/record_revision.py \
    --page "曹参定三秦击楚" \
    --summary "H25: 添加详细参见：[[曹参征战时间线]]" \
    --author butler
```

---

## 五、队列格式

```markdown
- [ ] H25 | [[曹参定三秦击楚]] → [[曹参征战时间线]] | 征战章节缺少时间线引用
  发现: 2026-04-26 用户报告
- [ ] H25 | [[曹参定齐七十县]] → [[曹参征战时间线]] | 同上
```

---

## 六、批量处理节奏

- 每次 H25 处理一个**专题页对应的全批**章节页（通常 3–8 个）
- 每轮最多插入 **10 条**详细参见，避免内容同质化
- 同一专题页不重复入队

---

## 七、常见专题页类型与匹配规则

| 专题页类型 | 典型标题模式 | 匹配章节页条件 |
|---|---|---|
| timeline | `{人物}征战时间线`、`{人物}生平时间线` | sources 包含同一世家，且含该人物名 |
| list | `{人物}功绩总计`、`历次{事件}列表` | description 覆盖同类事件 |
| analysis | `{人物}起事——……`、`{主题}的…规律` | 主题词出现在章节页正文 |
| insight | 洞察/规律类页面 | 章节页是洞察的一个实例事件 |
