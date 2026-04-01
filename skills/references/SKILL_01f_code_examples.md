# SKILL 01f - 代码示例参考

本文档包含 SKILL_01f（句读和标点校勘）中提到的详细代码示例。

## 目录

- [gj.cool API 调用](#gjcool-api-调用)
- [本地模型断句](#本地模型断句)
- [质量检查脚本](#质量检查脚本)
- [标点规范化映射](#标点规范化映射)
- [反思提示词](#反思提示词)

---

## gj.cool API 调用

### Python调用示例

```python
import requests

def auto_punctuate_gj(text: str) -> str:
    """
    调用 gj.cool API 自动断句。

    Args:
        text: 无标点的原文

    Returns:
        带标点的文本
    """
    url = "https://gj.cool/api/punctuate"
    payload = {
        "text": text,
        "model": "default"  # 或 "poetry" (诗歌专用)
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()["result"]
    else:
        raise Exception(f"API调用失败: {response.text}")

# 使用示例
raw_text = "太史公曰余读史记至于孔子世家观其言为人君难为人臣不易"
punctuated = auto_punctuate_gj(raw_text)
print(punctuated)
# 输出：太史公曰：余读《史记》至于《孔子世家》，观其言：为人君难，为人臣不易。
```

**注意事项**：
- API有调用频率限制（约100次/小时）
- 超过10,000字的文本需要分段调用
- 韵文需使用 `"model": "poetry"` 参数

---

## 本地模型断句

### 使用 Qwen-2.5 模型

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

def auto_punctuate_local(text: str) -> str:
    """使用本地模型自动断句（需8GB+ GPU）"""
    model_name = "Qwen/Qwen2.5-7B-Instruct"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        device_map="auto",
        torch_dtype="auto"
    )

    prompt = f"""你是古籍断句专家。请为以下无标点的文言文添加标点符号。

要求：
1. 使用全角标点（，。；：？！）
2. 引文用「」标记
3. 书名用《》标记
4. 保持原文不变，只添加标点

原文：
{text}

带标点的文本："""

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=len(text) * 2)
    result = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # 提取模型输出中的带标点文本
    return result.split("带标点的文本：")[-1].strip()
```

---

## 质量检查脚本

### 基础标点检查

```python
import re

def lint_punctuation_basic(text: str) -> list[dict]:
    """基础标点检查"""
    issues = []

    # 检查1：引号是否成对
    if text.count('"') != text.count('"'):
        issues.append({'type': 'unmatched_quote', 'msg': '引号不成对'})

    # 检查2：句子是否过长（>100字无句号）
    sentences = re.split(r'[。！？]', text)
    for i, sent in enumerate(sentences):
        if len(sent) > 100:
            issues.append({'type': 'long_sentence', 'line': i, 'length': len(sent)})

    # 检查3：逗号是否过密（连续5个逗号无句号）
    if re.search(r'，[^。]{1,20}，[^。]{1,20}，[^。]{1,20}，[^。]{1,20}，[^。]{1,20}，', text):
        issues.append({'type': 'comma_overflow', 'msg': '逗号过密，可能需要分号'})

    # 检查4：是否使用了半角标点（禁止）
    if re.search(r'[,.:;?!"\'<>]', text):
        issues.append({'type': 'halfwidth_punct', 'msg': '存在半角标点，必须改为全角'})

    return issues
```

---

## 标点规范化映射

### 全角/半角标点映射表

```python
PUNCTUATION_NORMALIZATION = {
    # 全角 → 规范形式
    '。': '。',
    '，': '，',
    '；': '；',
    '：': '：',
    '？': '？',
    '！': '！',

    # 半角 → 全角（用于规范化）
    '.': '。',
    ',': '，',
    ';': '；',
    ':': '：',
    '?': '？',
    '!': '！',

    # 引号统一映射（不同形式的引号视为等价）
    '"': '"',   # 半角左双引号
    '"': '"',   # 半角右双引号
    '「': '"',   # 日文左引号
    '」': '"',   # 日文右引号
    '『': ''',   # 日文左单引号
    '』': ''',   # 日文右单引号

    # 书名号
    '<': '《',
    '>': '》',
}

def normalize_punctuation(text: str) -> str:
    """规范化标点符号（用于比对）"""
    for old, new in PUNCTUATION_NORMALIZATION.items():
        text = text.replace(old, new)
    return text
```

---

## 反思提示词

### 标点反思提示词模板

```python
PUNCTUATION_REFLECTION_PROMPT = """你是《史记》标点校勘专家。请检查以下文本的标点符号使用是否合理。

**检查重点**：
1. 句子长度是否合理（一般不超过50字）
2. 逗号、分号、句号层次是否清晰
3. 引号使用是否正确（对话、引文）
4. 韵文是否保持韵律（每句结尾断句）
5. 并列结构是否使用顿号

**文本**：
{text}

**对照版本**（维基文库）：
{wiki_version}

**对照版本**（中华书局）：
{zhonghua_version}

请指出以下问题：
1. 明显的标点错误（位置 + 原因）
2. 可疑的断句（位置 + 建议）
3. 与参考版本的重要差异（位置 + 说明）

**输出格式**：
```json
{{
  "errors": [
    {{"line": 行号, "type": "错误类型", "position": "上下文", "reason": "原因", "suggestion": "建议"}}
  ],
  "warnings": [
    {{"line": 行号, "type": "可疑类型", "context": "上下文", "note": "说明"}}
  ],
  "differences": [
    {{"line": 行号, "our_version": "我们的版本", "reference": "参考版本", "comment": "评论"}}
  ]
}}
```
"""
```

### 使用示例

```python
def reflect_punctuation(text: str, wiki_version: str = "", zhonghua_version: str = "") -> dict:
    """使用LLM反思标点"""
    from openai import OpenAI

    client = OpenAI()
    prompt = PUNCTUATION_REFLECTION_PROMPT.format(
        text=text,
        wiki_version=wiki_version or "（未提供）",
        zhonghua_version=zhonghua_version or "（未提供）"
    )

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    import json
    return json.loads(response.choices[0].message.content)
```

---

## 相关文档

- [SKILL_01f_句读和标点校勘.md](../SKILL_01f_句读和标点校勘.md) - 主文档
- [SKILL_01f_background.md](./SKILL_01f_background.md) - 背景信息与FAQ
