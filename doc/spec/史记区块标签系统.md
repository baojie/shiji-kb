# 史记区块标签系统

## 概述

史记知识库使用 `::: tag` 语法标记特殊文本区块，这是一个通用的区块标签系统，用于标识和提取特定类型的内容。

## 区块标签语法

```markdown
::: 标签名称
区块内容
区块内容
:::
```

## 主要区块类型

### 1. 评论类区块

#### 太史公曰
- **标签**: `太史公曰`
- **描述**: 司马迁的史论评述
- **数量**: 125篇（96.2%章节）
- **格式**:
  ```markdown
  ## 太史公曰

  ::: 太史公曰
  [27] 〖@太史公〗曰：...
  :::
  ```

#### 赞
- **标签**: `赞`
- **描述**: 诗歌形式的评价
- **格式**:
  ```markdown
  ### 赞

  ::: 赞
  [28] 〖@尧〗遭鸿水，黎人阻饥。
  :::
  ```

### 2. 文献类区块

#### 诏书
- **标签**: `*诏` (如：击匈奴诏、不急立太子诏、和亲匈奴诏)
- **描述**: 皇帝诏令
- **例子**:
  ```markdown
  ::: 击匈奴诏
  ...诏书内容...
  :::
  ```

#### 传说
- **标签**: `传说`、`传曰`
- **描述**: 引用传闻或经传评论

### 3. 论述类区块

#### 评论
- **标签**: `君子曰`、`太史公评*`
- **描述**: 各类评论性文字

### 4. 其他特殊区块

- **制度**: 制度说明
- **功成身退**: 特定主题论述
- **不羁之士**: 人物类型论述
- **反间之言**: 计谋类内容
- **嫉妒之害**: 主题论述

## 区块查询框架

### 1. 提取脚本模板

```python
def extract_blocks_by_tag(chapter_file, tag_name):
    """提取指定标签的区块"""
    content = chapter_file.read_text(encoding='utf-8')

    # 方法1：标准格式 ::: tag ... :::
    pattern1 = rf'##\s*(?:\[\d+\])?\s*{tag_name}.*?\n.*?::: {tag_name}\s*\n(.*?)\n:::'
    matches = re.findall(pattern1, content, re.DOTALL)

    if matches:
        return matches[0].strip()

    # 方法2：段落格式（无::: 标记）
    pattern2 = rf'\[(\d+(?:\.\d+)?)\] 〖@{tag_name}〗：([^\n]+(?:\n(?!\[|\n|##)[^\n]+)*)'
    matches = re.findall(pattern2, content, re.MULTILINE)

    if matches:
        return '\n\n'.join([f"[{m[0]}] 〖@{tag_name}〗：{m[1]}" for m in matches])

    return None
```

### 2. 通用查询接口

```python
def query_blocks(tag_pattern=None, chapter_range=None):
    """
    通用区块查询接口

    参数:
        tag_pattern: 标签名称或正则表达式（如 "太史公曰" 或 ".*诏"）
        chapter_range: 章节范围（如 [1, 12] 表示本纪）

    返回:
        List[Dict]: 匹配的区块列表
    """
    pass
```

### 3. 专项索引生成

每个区块类型可以生成独立的专项索引：

```
docs/special/
├── taishigongyue.html     # 太史公曰专项
├── zan.html               # 赞专项（待实现）
├── zhaoshu.html           # 诏书专项（待实现）
└── ...
```

## 区块标签统计

### 按章节类型分布

- **本纪** (12篇): 太史公曰覆盖率 100%
- **表** (10篇): 太史公曰覆盖率 60%
- **书** (8篇): 太史公曰覆盖率 75%
- **世家** (30篇): 太史公曰覆盖率 93%
- **列传** (70篇): 太史公曰覆盖率 100%

### 特殊格式说明

1. **多段落标签**: 同一章节可能有多个同类区块
2. **嵌套标签**: 区块内可能包含实体标注
3. **编号格式**: 支持 `[27]` 和 `[27.1]` 两种段落编号

## 使用示例

### 提取所有太史公曰

```bash
python scripts/extract_taishigongyue.py
```

### 提取所有赞

```bash
python scripts/extract_blocks.py --tag="赞" --output="docs/special/zan.html"
```

### 提取所有诏书

```bash
python scripts/extract_blocks.py --tag-pattern=".*诏" --output="docs/special/zhaoshu.html"
```

## 扩展计划

1. **赞**: 提取所有诗歌形式的评价
2. **诏书**: 提取所有皇帝诏令
3. **书信**: 提取历史书信文献
4. **对话**: 提取重要历史对话
5. **论述**: 提取各类专题论述

## 技术实现

- **标注格式**: Markdown fenced div syntax (`::: tag`)
- **提取工具**: Python + 正则表达式
- **渲染引擎**: 自定义HTML生成器
- **索引系统**: JSON + HTML

## 参考

- 区块标签系统基于CommonMark扩展语法
- 实体标注使用 `〖TYPE content〗` 格式
- Purple Numbers用于段落编号和引用
