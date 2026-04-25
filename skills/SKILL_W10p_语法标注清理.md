---
name: SKILL_W10p_语法标注清理
title: Wiki 内务整理 H15：语法标注符号清理
description: 清理 wiki 页面正文中残留的标注符号（〖◆〗〖;〗⟦⟧〘〙等），将其还原为干净文本，每次处理一页一节，diff ≤ 20 行。
---

# SKILL W10p: 语法标注清理（H15）

> "标注文件里的标记是精华，wiki 页面里的标记是污染。两者不能混淆。"

---

## 一、何时执行

| 触发场景 | 优先级 |
|---|---|
| `grep -rl '〖\|⟦\|〘' wiki/public/pages/` 有结果 | P1 |
| 新导入页面时，发现标注符号未清理 | P1 |
| H10 分诊发现"标注符号泄漏" | P1 |

---

## 二、发现候选（扫描方法）

```bash
# 全库扫描残留标注符号
grep -rl '〖\|⟦\|〘\|〗\|⟧\|〙' wiki/public/pages/ | head -20

# 查看某页的具体位置
grep -n '〖\|⟦\|〘' wiki/public/pages/问题页.md
```

**常见残留符号**：

| 符号 | 来源 | 在 wiki 页中应清理为 |
|---|---|---|
| `〖◆实体〗` | 实体标注 | `实体`（可顺手转 wikilink `[[实体]]`）|
| `〖◆显示\|规范〗` | 消歧实体标注 | `显示`（注意：只保留显示名）|
| `〖;职位〗` | 职位标注 | `职位` |
| `⟦○动词〗` 或 `⟦动词⟧` | 动词标注 | `动词` |
| `〖%地名〗` | 地名标注 | `地名` |
| `〘※成语〙` | 成语标注 | `成语` |
| `〖~X〗` | 异体字标注 | `X`（保留规范字）|

---

## 三、执行步骤

### Step 1：扫描并确认问题位置

```bash
grep -n '〖\|⟦\|〘' wiki/public/pages/问题页.md
```

### Step 2：逐符号确认清理规则

对每处标注，判断应清理为哪个文本：

- `〖◆张仪〗` → `[[张仪]]`（有 wiki 页面时顺手链接）
- `〖◆张仪\|张仪（魏人）〗` → `张仪`（只保留显示名，不加链接）
- `〖;丞相〗` → `丞相`
- `⟦破⟧` → `破`
- `〘围魏救赵〙` → `围魏救赵`

### Step 3：处理全角引号（关键！）

清理标注符号时，**绝对不得改变正文中的全角引号**：
- 正确：`""` （全角，U+201C/U+201D）
- 错误：`""` （半角，U+0022）

如果使用脚本处理，处理后必须验证：

```bash
# 检查是否意外引入半角引号
grep -n '"' wiki/public/pages/问题页.md
```

### Step 4：编写替换脚本（推荐用脚本而非手动 Edit）

```python
#!/usr/bin/env python3
# clean_annotations.py
import re, sys

def clean(text):
    # 〖◆显示|规范〗 → 显示
    text = re.sub(r'〖[◆%@#]\s*([^|〗]+)\|[^〗]+〗', r'\1', text)
    # 〖◆实体〗 → [[实体]]（可选：加 wikilink）
    text = re.sub(r'〖◆\s*([^〗]+)〗', r'[[\1]]', text)
    # 〖;职位〗 → 职位
    text = re.sub(r'〖[;]\s*([^〗]+)〗', r'\1', text)
    # ⟦动词⟧ → 动词
    text = re.sub(r'⟦[^⟧]*?([^○◈⟧]+)⟧', r'\1', text)
    # 〘※成语〙 → 成语
    text = re.sub(r'〘[※]?\s*([^〙]+)〙', r'\1', text)
    # 〖~X〗 → X
    text = re.sub(r'〖[~]\s*([^〗]+)〗', r'\1', text)
    return text

if __name__ == '__main__':
    with open(sys.argv[1], encoding='utf-8') as f:
        content = f.read()
    cleaned = clean(content)
    print(cleaned)
```

```bash
python3 clean_annotations.py wiki/public/pages/问题页.md > /tmp/cleaned.md
# 验证后写入
python3 wiki/scripts/butler/edit_page.py "问题页" /tmp/cleaned.md \
    --summary "w10p: H15 清理残留标注符号" \
    --author "butler"
```

### Step 5：限制范围

**每次最多清理一页的一个节**（如只清理 `## 史记引文` 节），diff ≤ 20 行。

---

## 四、成功标准 / 完成条件

- [ ] 处理后页面中无 `〖` `⟦` `〘` 等标注符号
- [ ] 全角引号 `""` 未被替换为半角引号 `""`
- [ ] 原文文字（去除标注符号后）未被修改
- [ ] diff ≤ 20 行
- [ ] 完成后运行 `grep -n '"' 问题页.md` 验证无半角引号

---

## 五、工具与脚本

| 工具 | 用途 |
|---|---|
| `grep -rl '〖\|⟦'` | 批量发现有残留符号的页面 |
| 上方 `clean_annotations.py` 脚本 | 安全清理标注符号 |
| `wiki/scripts/butler/edit_page.py` | 写入清理后的页面 |

---

## 六、常见误判

| 误判 | 说明 |
|---|---|
| `## 史记引文` 节中的 `〖〗` | 若是正文引文中的标注，也应清理（引文节内容已是"渲染后"格式）|
| `>` 引用块中的引号变成半角 | Edit 工具有时会转换，务必验证 |
| `〖◆X\|Y〗` 中保留规范名 Y | ❌ 只保留显示名 X |

---

## 相关路径

- `wiki/logs/butler/housekeeping_queue.md` — H15 任务队列
- `skills/SKILL_W10k_页面错误反思.md` — H10，发现标注泄漏后写入 H15 队列
