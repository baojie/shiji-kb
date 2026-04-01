---
name: skill-01f
title: 句读和标点校勘
description: 古籍断句与标点符号使用规范。包括无标点古籍的AI自动断句与质量控制、已标点版本的标点反思、标点符号规范约定、以及文本完整性检查中的标点处理规则。
version: 1.0
last_updated: 2026-04-01
---

# SKILL 01f: 句读和标点校勘

> **核心理念**：标点是文本理解的第一道工序。准确的句读是一切语义分析的基础。

---

## 一、快速开始

### 何时使用此Skill

- **场景1**：接收到无标点的古籍原文，需要进行自动断句和标点
- **场景2**：已有标点的版本存在明显句读错误，需要系统性反思
- **场景3**：多版本对照时发现标点差异，需要确定最佳方案
- **场景4**：验证标注完整性时，需要理解标点符号的处理规则

### 核心步骤（句读工序位置）

```
【校勘管线】
① 句读与标点 (SKILL_01f)        ← 最前置工序，建立文本骨架
   ↓
② 多版本互校 (SKILL_01b)        ← 确定定本
   ↓
③ 表格校勘 (SKILL_01c)          ← 特殊结构校勘
   ↓
④ 正音与拼音 (SKILL_01d)        ← 标注读音
   ↓
⑤ 繁简体处理 (SKILL_01e)        ← 繁简转换
   ↓
⑥ 结构化标注 (SKILL_02*)        ← 章节切分、区块、三家注等
   ↓
⑦ 实体标注 (SKILL_03*)          ← 人名、地名、官职、书名等
   ↓
⑧ 标注完整性维护 (SKILL_01a)    ← 验证所有标注未篡改原文
```

**为何句读在最前面**：
- 句读错误会导致语义切分错误，影响所有后续工序
- 标点是文本的"骨架"，骨架不对，血肉无从依附
- 句读完成后，才能进行多版本对照（不同版本的句读可能不同）

**为何标注完整性在最后**：
- 标注完整性是验证步骤，检查所有标注工作是否遵守"标注铁律"
- 只有在实体标注等所有标注工作完成后，才需要进行完整性验证
- 完整性检查需要理解哪些标点是原文固有的，哪些是标注时添加的

### 工作流程（3种场景）

#### 场景A：无标点古籍自动断句

```bash
# 步骤1：准备无标点原文
# 输入：archive/raw/无标点原文.txt

# 步骤2：AI自动断句（使用gj.cool API或本地模型）
python scripts/punctuation/auto_punctuate.py archive/raw/无标点原文.txt

# 步骤3：生成初稿（带标点）
# 输出：curation_base/初稿_已标点.txt

# 步骤4：人工校对（修正明显错误）
# 工具：VSCode + 对照参考版本

# 步骤5：质量验证
python scripts/punctuation/validate_punctuation.py curation_base/初稿_已标点.txt

# 步骤6：生成校对报告
python scripts/punctuation/generate_punctuation_report.py curation_base/初稿_已标点.txt
```

#### 场景B：已标点版本的反思

```bash
# 步骤1：提取现有标点模式
python scripts/punctuation/extract_pattern.py chapter_md/001_*.tagged.md

# 步骤2：对照多版本（维基/四库/中华书局）
python scripts/punctuation/compare_punctuation.py 001 --sources wiki,siku,zhonghua

# 步骤3：标记可疑句读（如句子过长、引号不匹配）
python scripts/punctuation/lint_punctuation.py chapter_md/001_*.tagged.md

# 步骤4：AI反思建议
python scripts/punctuation/reflect_punctuation.py chapter_md/001_*.tagged.md

# 步骤5：人工决策与修正
```

#### 场景C：文本完整性检查中的标点处理

```bash
# 在 lint_text_integrity.py 中，标点去除规则：
# 1. 原文无标点 → 标注文件的标点全部视为"结构性添加"
# 2. 标注文件去除标注符号后，标点保留
# 3. 比对时，规范化映射消除全角/半角差异
# 4. 引号差异（"" vs 「」 vs 『』）通过规范化映射忽略
```

### 成功标准

- [ ] **断句准确率**：AI断句后人工校对，错误率 <5%（每千字<50处错误）
- [ ] **标点规范性**：全部使用全角标点，引号嵌套正确（" " → ' '）
- [ ] **换行符规范**：使用LF（Unix格式），无CRLF
- [ ] **韵文格式规范**：句号后必须换行
- [ ] **语义完整性**：句子边界与语义边界一致，无误断、误连
- [ ] **多版本一致性**：关键句读与权威版本（中华书局等）一致
- [ ] **完整性验证通过**：`lint_text_integrity.py` 检查通过

---

## 二、标点符号规范

### 2.1 基本原则

**古籍标点三原则**（参考《标点符号用法》GB/T 15834-2011）：

1. **全角优先**：古籍整理中，所有标点符号必须使用全角字符
2. **语义优先**：标点服从语义，不拘泥于现代语法
3. **从俗从简**：常用标点优先，避免过度使用冷僻符号

### 2.1a 换行符规范

**本项目统一使用 LF（Line Feed，Unix风格）换行符**：

| 规范 | 说明 | 字符编码 |
|-----|------|---------|
| **使用** | LF（`\n`） | `0x0a` |
| **禁止** | CRLF（`\r\n`） | `0x0d 0x0a` |
| **禁止** | CR（`\r`） | `0x0d` |

**原因**：
1. **Git默认行为**：Git在Linux/macOS上默认使用LF
2. **跨平台兼容**：现代编辑器（VSCode/Vim/Sublime等）均支持LF
3. **Python脚本兼容**：Python在文本模式下自动处理换行符，使用LF可避免意外的`\r`字符
4. **已有文件现状**：项目中现有的`.tagged.md`文件均使用LF

**VSCode配置**（推荐）：
```json
{
  "files.eol": "\n"
}
```

**Git配置**（推荐）：
```bash
# 提交时自动转换为LF，检出时保持LF
git config --global core.autocrlf input

# Windows用户若需要本地使用CRLF，检出时可转换（不推荐）
# git config --global core.autocrlf true
```

**验证换行符**：
```bash
# 方法1：使用file命令
file chapter_md/001_*.tagged.md
# 输出：UTF-8 text（LF换行符）

# 方法2：使用od查看十六进制
head -5 chapter_md/001_*.tagged.md | od -An -tx1 | grep "0a"
# 应看到 0a（LF），不应看到 0d 0a（CRLF）

# 方法3：使用dos2unix检测（若安装）
dos2unix -ic chapter_md/*.tagged.md
# 无输出表示已是Unix格式
```

### 2.2 标点符号对照表

| 类型 | 符号 | Unicode | 用法 | 禁止使用 |
|-----|------|---------|------|---------|
| **句号** | 。 | U+3002 | 陈述句结尾 | ❌ 半角`.` |
| **逗号** | ，| U+FF0C | 句内停顿 | ❌ 半角`,` |
| **顿号** | 、 | U+3001 | 并列词语间 | ❌ 半角`,` |
| **分号** | ；| U+FF1B | 复句内并列分句间 | ❌ 半角`;` |
| **冒号** | ：| U+FF1A | 提示下文、总结上文 | ❌ 半角`:` |
| **问号** | ？| U+FF1F | 疑问句结尾 | ❌ 半角`?` |
| **叹号** | ！| U+FF01 | 感叹句结尾 | ❌ 半角`!` |
| **左双引号** | " | U+201C | 第一层引用 | ❌ 半角`"` 直角「 |
| **右双引号** | " | U+201D | 第一层引用结束 | ❌ 半角`"` 直角」 |
| **左单引号** | ' | U+2018 | 第二层引用（引用内引用） | ❌ 半角`'` 直角『 |
| **右单引号** | ' | U+2019 | 第二层引用结束 | ❌ 半角`'` 直角』 |
| **左书名号** | 《 | U+300A | 书名、篇名 | ❌ `<` |
| **右书名号** | 》 | U+300B | 书名、篇名结束 | ❌ `>` |
| **破折号** | —— | U+2014×2 | 注释、转折、延长 | ❌ `--` `-` |
| **省略号** | …… | U+2026×2 | 文字省略 | ❌ `...` `。。。` |

### 2.3 引号嵌套规则

**嵌套顺序**（从外到内）：

```
第一层：" "  （弯双引号）
第二层：' '  （弯单引号）
第三层：" "  （重复第一层）
```

**示例**：

```
太史公曰："孔子称'《尚书》言"夏礼吾能言之"，而不能徵'，信矣。"
         └─第1层────┘└第2层─┘└──第3层────────┘
```

**常见错误**：
- ❌ 使用半角引号 `"` `'`
- ❌ 使用直角引号 `「」` `『』`（日文用法）
- ❌ 第一层用单引号 `''`
- ❌ 忘记嵌套层次，全部用同一种引号

### 2.4 特殊情况处理

#### 2.4.1 对话与引文

**直接引语**（说话内容）：
```
高祖曰："大风起兮云飞扬，威加海内兮归故乡，安得猛士兮守四方！"
```

**间接引语**（转述）：
```
太史公言孔子修《春秋》，笔则笔，削则削。
（无引号，因为是转述而非原话）
```

**引用文献**：
```
《索隐》曰："音禅。"
└─书名号┘  └引文─┘
```

**长段对话分段引号规范**（依据GB/T 15834-2011）：

根据《标点符号用法》国家标准（GB/T 15834-2011）的规定：

> **"独立成段的引文如果只有一段，段首和段尾都用引号；不止一段时，每段开头仅用前引号，只在最后一段末尾用后引号。"**

**正确示例**（多段对话）：
```
太史公曰："余读《史记》至于《孔子世家》，观其言。
"为人君难，为人臣不易。
"信乎，其言之难也！"
```

**格式说明**：
- **第一段**：开头用前引号 `"`，末尾**不用**后引号
- **中间段**：开头用前引号 `"`，末尾**不用**后引号
- **最后段**：开头用前引号 `"`，末尾**必须用**后引号 `"`

**单段对话**（作为对比）：
```
孔子曰："三人行，必有我师焉。"
（单段时，段首和段尾都用引号）
```

**错误示例**：
```
❌ 太史公曰："余读《史记》至于《孔子世家》，观其言。"
"为人君难，为人臣不易。"
"信乎，其言之难也！"
（每段都用成对引号，违反国家标准）
```

**为什么这样规定**：
- 保持多段引用的连续性
- 让读者明确这些段落属于同一个完整的引述
- 避免被误认为是不同的独立对话

#### 2.4.2 韵文与诗歌

**韵文格式规范**：

1. **每个句号后换行**（强制规则）：
```
大风起兮云飞扬，威加海内兮归故乡，安得猛士兮守四方！
```
应改为：
```
大风起兮云飞扬，威加海内兮归故乡。
安得猛士兮守四方！
```

2. **韵脚处理**：
   - 韵脚之间用逗号，不换行
   - 段落结束用句号，必须换行
   - 全文结束可用感叹号或句号

3. **诗歌格式**（四言、五言、七言等）：
```
东门之枌，宛丘之栩。
子仲之子，婆娑其下。
（每两句为一段，句号后换行）
```

4. **辞赋格式**（楚辞体等）：
```
帝高阳之苗裔兮，朕皇考曰伯庸。
摄提贞于孟陬兮，惟庚寅吾以降。
（每两句为一联，句号后换行）
```

#### 2.4.3 并列结构

**并列词语**（用顿号）：
```
秦、晋、齐、楚皆霸。
```

**并列短语**（用逗号）：
```
北击匈奴，南伐百越，西定巴蜀，东至海滨。
```

**并列分句**（用分号）：
```
商君治秦，法令至行；秦人富强，天下畏之。
```

#### 2.4.4 表格中的标点

**年表纪事**：
```
| 年份 | 秦 | 楚 |
|------|----|----|
| 元年 | 孝公即位。商鞅入秦。 | 悼王立。|
```

**原则**：
- 每个单元格内是独立句子时，使用句号
- 若单元格内容是词组，无标点
- 表格符号 `|` 不影响文本内容（在完整性检查时去除）

### 2.5 标点与标注的关系

**标注符号不改变标点**：

✅ **正确**：
```
〖#项羽〗曰："吾闻〖#汉王〗已得〖'关中〗。"
（标点在标注符号外）
```

❌ **错误**：
```
〖#项羽〗曰：〖引"吾闻〖#汉王〗已得〖'关中〗"〗。
（标点被包入标注符号内，会导致显示异常）
```

**引号与标注的共存**：
```
〖#太史公〗曰："〖#孔子〗之徒无道〖!桓〗〖!文〗之事者，是以无传焉。"
                └────────────引文内可以标注────────────────┘
```

---

## 三、AI自动断句工作流

### 3.1 技术方案选型

| 方案 | 工具 | 准确率 | 速度 | 成本 | 推荐场景 |
|-----|------|-------|------|------|---------|
| **在线API** | gj.cool（龙泉寺团队） | 92-99% | 快 | 免费 | 小规模文本（<1万字） |
| **本地模型** | Qwen/GLM-4等 | 90-95% | 中 | 一次性 | 大规模文本（>10万字） |
| **规则+模型** | 基于CRF+Transformer混合 | 95%+ | 慢 | 高 | 高质量要求（学术出版） |

**本项目推荐方案**：
- **第一轮**：使用 gj.cool API（https://gj.cool）进行自动断句
- **第二轮**：人工校对（重点检查长句、引文、韵文）
- **第三轮**：使用本地模型（Qwen-2.5-72B-Instruct）进行反思

### 3.2 gj.cool API 使用方法

**接口文档**：https://gj.cool/help/api

**Python调用示例**：

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

### 3.3 本地模型方案（高级）

**使用 Qwen-2.5 模型**：

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

### 3.4 质量控制流程

**三级检查机制**：

#### 第一级：自动规则检查

```python
def lint_punctuation_basic(text: str) -> list[dict]:
    """基础标点检查"""
    issues = []

    # 检查1：引号是否成对
    if text.count('「') != text.count('」'):
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

#### 第二级：人工校对重点

**重点检查位置**：
1. **长句子**（>50字无标点）：可能是误连，需要加句号或分号
2. **对话部分**：引号是否正确，「」是否成对
3. **韵文**：是否保持韵律（每个韵脚后断句）
4. **引用文献**：书名号《》是否正确，引文「」是否正确
5. **并列结构**：顿号、逗号、分号层次是否正确

**校对辅助工具**：

```bash
# 生成人工校对报告（高亮可疑位置）
python scripts/punctuation/highlight_suspicious.py curation_base/初稿.txt

# 输出示例：
# [行52] 长句警告（98字无句号）：太史公曰余读史记至于孔子世家观其言...
# [行103] 引号不成对：「孔子称《尚书》...（缺少右引号）
# [行200] 韵文可能误断：大风起兮云飞扬。威加海内兮归故乡。（建议合并）
```

#### 第三级：AI反思验证

**使用LLM进行反思**（检查人工校对后的版本）：

```python
def reflect_punctuation(text: str) -> dict:
    """AI反思：检查标点是否合理"""
    prompt = f"""你是《史记》专家。请检查以下文本的标点是否合理。

检查要点：
1. 句子边界是否与语义边界一致
2. 引号、书名号是否正确
3. 并列结构的顿号、逗号、分号是否层次分明
4. 韵文是否保持韵律

文本：
{text}

请指出可疑的标点位置（如果有），并说明原因。如无问题，回答"标点合理"。
"""
    # 调用LLM API（Qwen/Claude/GPT-4等）
    response = call_llm_api(prompt)
    return parse_reflection(response)
```

---

## 四、标点反思工作流

### 4.1 多版本对照

**参考版本优先级**：

1. **中华书局点校本**（最权威，作为标准参考）
2. **维基文库版本**（开放获取，需人工验证）
3. **四库全书版本**（古本，标点可能不符合现代规范）
4. **其他数字化版本**（如国学大师、汉典等）

**对照方法**：

```bash
# 提取多版本的标点模式
python scripts/punctuation/extract_all_versions.py 001

# 输出：versions_punctuation/001_comparison.json
# {
#   "zhonghua": "太史公曰：余读《史记》...",
#   "wiki": "太史公曰，余读《史记》...",
#   "siku": "太史公曰余读史记...",
#   "diff": [
#     {"pos": 5, "zhonghua": "：", "wiki": "，", "reason": "冒号vs逗号"}
#   ]
# }
```

### 4.2 反思提示词模板

**Prompt模板**：

```
你是古籍整理专家，精通《史记》。请检查以下文本的标点是否合理。

【文本】
{text}

【检查要点】
1. 句子边界：是否与语义单元一致？
2. 引文标记：对话、引用是否正确使用「」？
3. 并列结构：顿号、逗号、分号层次是否清晰？
4. 韵文处理：是否保持韵律完整？
5. 书名标记：《》是否正确？

【参考版本对比】
- 中华书局版：{zhonghua_version}
- 维基文库版：{wiki_version}

【输出格式】
若有问题，按以下格式输出：
```json
{
  "issues": [
    {
      "position": "行52，第18字",
      "original": "，",
      "suggested": "。",
      "reason": "此处应为句子结束，不应用逗号",
      "severity": "high"  // high/medium/low
    }
  ]
}
```

若无问题，输出：
```json
{"status": "ok", "message": "标点合理，无需修改"}
```
```

### 4.3 常见标点错误模式

| 错误类型 | 示例 | 正确做法 | 检测规则 |
|---------|------|---------|---------|
| **误用逗号代替句号** | 太史公曰，余读史记，观其言 | 太史公曰：余读《史记》，观其言。 | 句子过长（>50字） |
| **误用冒号代替逗号** | 孔子称：夏礼吾能言之 | 孔子称，夏礼吾能言之 | "称""言""曰"后非引文时用逗号 |
| **引号缺失** | 太史公曰余读史记 | 太史公曰：「余读《史记》」 | "曰"后若为原话应加引号 |
| **引号嵌套错误** | 「孔子称「夏礼」」 | 「孔子称『夏礼』」 | 内层应用『』 |
| **韵文误断** | 大风起兮云飞扬。威加海内兮归故乡。 | 大风起兮云飞扬，威加海内兮归故乡。 | 韵脚间用逗号 |
| **并列顿号误用** | 秦，晋，齐，楚 | 秦、晋、齐、楚 | 单字并列用顿号 |

---

## 五、工具与脚本

**⚠️ 重要说明**：以下脚本**尚未开发**，本章节为规划文档。实际使用前需要先开发这些工具。

### 关联脚本（待开发）

#### 自动断句工具 ⚠️ 待开发
- `scripts/punctuation/auto_punctuate.py` - 调用gj.cool API自动断句
  - 输入：无标点txt文件
  - 输出：带标点txt文件
  - 用法：`python scripts/punctuation/auto_punctuate.py archive/raw/input.txt`
  - **状态**：❌ 未开发

- `scripts/punctuation/auto_punctuate_local.py` - 使用本地模型断句
  - 输入：无标点txt文件
  - 输出：带标点txt文件
  - 用法：`python scripts/punctuation/auto_punctuate_local.py archive/raw/input.txt`
  - **状态**：❌ 未开发

#### 验证工具
- `scripts/lint_symbol_conflicts.py` - 符号冲突检测（标点、标注、Markdown）
  - 检查：半角标点、直角引号、标点在标注内、Markdown在标注内、嵌套标注、标注跨标点
  - 输出：检查报告（按文件和严重程度分组）
  - 用法：`python scripts/lint_symbol_conflicts.py chapter_md/*.md --report logs/symbol_conflicts.txt`
  - **状态**：✅ 已实现（基于 SKILL_01g）

- `scripts/punctuation/lint_punctuation.py` - 标点规则检查 ⚠️ 待开发
  - 检查：引号成对、句子长度、换行符类型
  - 输出：检查报告（JSON格式）
  - 用法：`python scripts/punctuation/lint_punctuation.py chapter_md/001*.md`
  - **状态**：❌ 未开发（部分功能已被 lint_symbol_conflicts.py 覆盖）

- `scripts/punctuation/validate_punctuation.py` - 标点语义验证 ⚠️ 待开发
  - 检查：语义边界、引文标记、并列结构、韵文换行
  - 输出：可疑位置列表
  - 用法：`python scripts/punctuation/validate_punctuation.py curation_base/初稿.txt`
  - **状态**：❌ 未开发

#### 对照工具 ⚠️ 待开发
- `scripts/punctuation/compare_punctuation.py` - 多版本标点对比
  - 输入：章节编号 + 版本列表
  - 输出：差异对照表（HTML）
  - 用法：`python scripts/punctuation/compare_punctuation.py 001 --sources wiki,siku,zhonghua`
  - **状态**：❌ 未开发

- `scripts/punctuation/extract_pattern.py` - 提取标点模式
  - 输入：标注文件
  - 输出：标点统计（每种标点的使用频率）
  - 用法：`python scripts/punctuation/extract_pattern.py chapter_md/*.md`
  - **状态**：❌ 未开发

#### 反思工具 ⚠️ 待开发
- `scripts/punctuation/reflect_punctuation.py` - AI标点反思
  - 输入：带标点文本
  - 输出：反思报告（可疑位置 + 修改建议）
  - 用法：`python scripts/punctuation/reflect_punctuation.py chapter_md/001*.md`
  - **状态**：❌ 未开发

- `scripts/punctuation/highlight_suspicious.py` - 高亮可疑位置
  - 输入：带标点文本
  - 输出：HTML报告（可疑位置高亮显示）
  - 用法：`python scripts/punctuation/highlight_suspicious.py curation_base/初稿.txt`
  - **状态**：❌ 未开发

#### 批量处理 ⚠️ 待开发
- `scripts/punctuation/batch_process.sh` - 批量断句处理
  - 输入：目录（包含多个无标点txt文件）
  - 输出：对应的带标点txt文件 + 统一质量报告
  - 用法：`bash scripts/punctuation/batch_process.sh archive/raw/`
  - **状态**：❌ 未开发

### 开发优先级

根据实际需求，建议按以下顺序开发：

1. **P0（高优先级）**：
   - `lint_punctuation.py` - 基础规则检查（引号成对、半角标点、换行符）
   - `validate_punctuation.py` - 语义验证（长句、韵文换行）

2. **P1（中优先级）**：
   - `compare_punctuation.py` - 多版本对照（辅助人工校对）
   - `extract_pattern.py` - 标点统计（质量监控）

3. **P2（低优先级）**：
   - `auto_punctuate.py` - 自动断句（仅在有无标点古籍时需要）
   - `reflect_punctuation.py` - AI反思（可用LLM临时替代）
   - `highlight_suspicious.py` - 可疑位置高亮（可用人工代替）
   - `batch_process.sh` - 批量处理（最后集成）

### 使用示例

#### 示例1：无标点古籍自动断句（完整流程）

```bash
# 第一步：准备原文
cp 古籍原文_无标点.txt archive/raw/001_test.txt

# 第二步：自动断句（调用gj.cool API）
python scripts/punctuation/auto_punctuate.py archive/raw/001_test.txt

# 输出：curation_base/001_test_punctuated.txt

# 第三步：基础规则检查
python scripts/punctuation/lint_punctuation.py curation_base/001_test_punctuated.txt

# 输出示例：
# [警告] 行52: 长句子（98字无句号）
# [错误] 行103: 引号不成对（「3个，」2个）
# [警告] 行200: 连续5个逗号，建议使用分号

# 第四步：人工校对（使用VSCode，重点修正上述警告位置）
code curation_base/001_test_punctuated.txt

# 第五步：AI反思（修正后再验证）
python scripts/punctuation/reflect_punctuation.py curation_base/001_test_punctuated.txt

# 输出：反思报告（若无问题，显示"标点合理"）

# 第六步：生成最终报告
python scripts/punctuation/generate_punctuation_report.py curation_base/001_test_punctuated.txt

# 输出：logs/punctuation/001_test_report.md
```

#### 示例2：已标点版本的反思

```bash
# 第一步：提取现有标点模式
python scripts/punctuation/extract_pattern.py chapter_md/001_*.tagged.md

# 输出示例：
# 标点统计：
#   句号（。）：523次
#   逗号（，）：1,203次
#   顿号（、）：89次
#   分号（；）：12次
#   问号（？）：5次
#   叹号（！）：3次
#   引号（「」）：87对
#   书名号（《》）：23对

# 第二步：多版本对照
python scripts/punctuation/compare_punctuation.py 001 --sources wiki,siku

# 输出：versions_punctuation/001_comparison.html（可在浏览器中查看）

# 第三步：标记可疑位置
python scripts/punctuation/highlight_suspicious.py chapter_md/001_*.tagged.md

# 输出：logs/punctuation/001_suspicious.html（高亮显示可疑位置）

# 第四步：AI反思
python scripts/punctuation/reflect_punctuation.py chapter_md/001_*.tagged.md

# 输出：反思报告（若有问题，列出位置 + 建议）

# 第五步：人工决策（根据AI建议修正）
```

#### 示例3：批量处理（多章节）

```bash
# 批量断句（全部130章）
bash scripts/punctuation/batch_process.sh archive/raw/

# 该脚本会：
# 1. 遍历 archive/raw/*.txt
# 2. 对每个文件调用 auto_punctuate.py
# 3. 对每个输出调用 lint_punctuation.py
# 4. 生成统一的质量报告 logs/punctuation/batch_report.md
```

---

## 六、完整性检查中的标点处理

### 6.1 标点去除规则（在lint_text_integrity.py中）

**核心原则**：标点符号是"结构性添加"，不影响文本完整性验证。

```python
def strip_markup(text: str) -> str:
    """去除全部语义标注符号和结构性标点，保留实体内容本身。"""

    # 1. 去除标注符号（〖TYPE〗 ⟦TYPE⟧）
    text = re.sub(r'〖[^〗]*〗', '', text)
    text = re.sub(r'⟦[^⟧]*⟧', '', text)

    # 2. 保留标点符号（标点不影响文本完整性）
    # （不去除标点，因为原文可能有标点）

    # 3. 去除Markdown结构（标题、引用、列表等）
    text = re.sub(r'^#{1,6}.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^>\s?', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*-\s', '', text, flags=re.MULTILINE)

    return text
```

### 6.2 标点规范化映射（消除全角/半角差异）

**在 `_norm()` 函数中**：

```python
_NORM_TABLE = str.maketrans({
    # 各式引号 → 统一删除（标注规范：原文无引号，标注文件用全角引号，忽略此差异）
    '\u201c': '',   # " (左双引号)
    '\u201d': '',   # " (右双引号)
    '\u300c': '',   # 「
    '\u300d': '',   # 」
    '\u300e': '',   # 『
    '\u300f': '',   # 』
    '\u2018': '',   # ' (左单引号)
    '\u2019': '',   # ' (右单引号)
    '"': '',        # 半角双引号（历史遗留）
    "'": '',        # 半角单引号（历史遗留）
})

def _norm(text: str) -> str:
    """规范化字形变体，消除等价异体字差异。"""
    text = text.translate(_NORM_TABLE)
    return text
```

**规范化策略**：
- **引号**：原文无引号时，标注文件添加的引号通过规范化映射删除，不计入差异
- **其他标点**：保留在规范化文本中，因为标点可能是原文固有的（如句号、逗号）
- **全角/半角**：禁止使用半角标点，若发现则报错（`lint_punctuation.py`检测）

### 6.3 原文有标点 vs 原文无标点

**判断依据**：

| 原文类型 | 特征 | 完整性检查策略 |
|---------|------|--------------|
| **有标点原文** | archive/chapter/*.txt 中含有句号、逗号等 | 标注文件必须保留这些标点，不得删改 |
| **无标点原文** | archive/chapter/*.txt 中全部汉字，无标点 | 标注文件添加的标点视为"结构性添加"，通过规范化映射忽略 |

**本项目情况**：
- 《史记》简体底本（archive/chapter/*.txt）**已经包含标点**
- 因此，标注文件（chapter_md/*.tagged.md）中的标点应与原文一致
- 若需修改标点，必须先修改原文txt，再同步到标注文件

**工作流程**：
```bash
# 发现标点错误时
# 1. 先修改原文（archive/chapter/001_xxx.txt）
vim archive/chapter/001_五帝本纪.txt

# 2. 再同步到标注文件（使用脚本或手工）
python scripts/sync_punctuation_to_tagged.py 001

# 3. 验证完整性
python scripts/lint_text_integrity.py 001
```

---

## 七、检查清单

### 执行前检查（断句前）

- [ ] 确认原文来源（是否权威版本）
- [ ] 确认原文是否已有标点（有标点→反思流程；无标点→断句流程）
- [ ] 准备参考版本（中华书局版、维基版等）
- [ ] 确认文体类型（散文/韵文/表格，决定断句策略）

### 执行中验证（断句后/反思中）

- [ ] **基础规则检查**：引号成对、无半角标点、句子长度合理
- [ ] **换行符检查**：使用LF（`\n`），无CRLF（`\r\n`）
- [ ] **语义边界检查**：句子边界与语义单元一致
- [ ] **引文标记检查**：对话、引用正确使用" "和' '
- [ ] **长对话引号检查**：多段对话仅最后一段用后引号（GB/T 15834-2011）
- [ ] **并列结构检查**：顿号、逗号、分号层次清晰
- [ ] **韵文检查**：韵律完整，韵脚处断句，句号后换行
- [ ] **书名标记检查**：《》正确标记书名、篇名

### 执行后验证（最终确认）

- [ ] **人工校对完成**：高风险位置（长句、引文、韵文）已人工审查
- [ ] **AI反思通过**：使用LLM验证，无可疑位置或已处理
- [ ] **多版本对照**：与权威版本（中华书局）的关键句读一致
- [ ] **完整性验证**：`lint_text_integrity.py` 检查通过
- [ ] **校对报告生成**：logs/punctuation/ 中有完整报告
- [ ] **原文同步**：若修改标点，archive/chapter/*.txt 已同步更新

---

## 八、FAQ

### Q1: 为什么句读工序在最前面？

**A**: 句读是文本结构的"骨架"，错误的句读会导致：
1. **语义切分错误**：如"孔子曰。为政以德。"误断为"孔子曰为。政以德。"
2. **实体边界错误**：如"〖#齐桓公〗曰"误断为"〖#齐桓〗公曰"
3. **引文识别错误**：如「」范围错误，导致引文与正文混淆

因此，必须在所有标注工序之前完成句读，确保"骨架"正确。

### Q2: 原文有标点时，是否还需要反思？

**A**: 需要。原因：
1. **底本可能有错**：网络来源的文本，标点不一定可靠
2. **标点规范不统一**：如引号样式（"" vs 「」）、全角/半角混用
3. **多版本差异**：不同版本的句读可能不同，需要选择最佳方案

**反思重点**：
- 与权威版本（中华书局）对照
- 检查标点规范性（全角、引号嵌套）
- 修正明显的句读错误（如长句、引号不成对）

### Q3: gj.cool API 断句准确率如何？

**A**: 根据龙泉寺团队的测试数据：
- **诗歌**：99%准确率
- **词曲**：95%准确率
- **散文**：92%准确率

**本项目经验**（《史记》散文为主）：
- 自动断句后，**平均每千字约30-50处需要人工修正**
- 修正主要集中在：长句（>50字）、引文边界、韵文、对话

**因此**：
- 不能完全依赖API，必须有人工校对
- 人工校对重点：长句、引文、韵文
- AI反思可以辅助发现遗漏的错误

### Q4: 如何处理标点与标注符号的冲突？

**A**: 标点在标注符号**外部**，不被包入标注内。

✅ **正确示例**：
```
〖#项羽〗曰：「吾闻〖#汉王〗已得〖'关中〗。」
└标注─┘└标点┘└引号┘└标注─┘     └标注─┘└标点┘└引号┘
```

❌ **错误示例**：
```
〖#项羽曰：「吾闻〖#汉王〗已得〖'关中〗。」〗
└───标注符号内包含标点和引号，错误─────────┘
```

**原因**：
- 标注符号会在显示时被去除，如果标点在标注内，会导致标点丢失
- 引号是原文的一部分，不应被标注符号包裹

### Q5: 韵文应该如何断句和换行？

**A**: 韵文（诗歌、辞赋）有特殊规则：

**核心规则**：**每个句号后必须换行**

**诗歌**（如五言、七言诗）：
```
东门之枌，宛丘之栩。
子仲之子，婆娑其下。
（每两句一联，句号后换行）
```

**辞赋**（如《大风歌》）：
```
大风起兮云飞扬，威加海内兮归故乡。
安得猛士兮守四方！
（每个自然段用句号结束，句号后换行）
```

**楚辞体**（如《离骚》）：
```
帝高阳之苗裔兮，朕皇考曰伯庸。
摄提贞于孟陬兮，惟庚寅吾以降。
（每两句一联，句号后换行）
```

**原则**：
- **句号后必须换行**（强制规则，便于阅读和版式控制）
- 韵脚之间用逗号，不换行
- 段落结束用句号，必须换行
- 保持韵律完整，不在韵脚中间断句

**错误示例**：
```
❌ 大风起兮云飞扬，威加海内兮归故乡，安得猛士兮守四方！
（全文一行，不符合规范）

❌ 东门之枌，宛丘之栩。子仲之子，婆娑其下。
（句号后未换行）
```

### Q6: 长对话分段时，引号应该如何使用？

**A**: 根据《标点符号用法》国家标准（GB/T 15834-2011）：

**核心规则**：
- **单段对话**：段首和段尾都用引号 `"..."`
- **多段对话**：每段开头用前引号 `"`，**只在最后一段末尾**用后引号 `"`

**正确示例**（多段对话）：
```
太史公曰："余读《史记》至于《孔子世家》，观其言。
"为人君难，为人臣不易。
"信乎，其言之难也！"
```

**格式解析**：
- 第1段：`"余读《史记》...` ← 有前引号，**无**后引号
- 第2段：`"为人君难...` ← 有前引号，**无**后引号
- 第3段：`"信乎，其言之难也！"` ← 有前引号，**有**后引号

**错误做法**：
```
❌ 太史公曰："余读《史记》至于《孔子世家》，观其言。"
"为人君难，为人臣不易。"
"信乎，其言之难也！"
（每段都用成对引号，违反国家标准）
```

**为什么这样规定**：
1. 保持多段引用的连续性
2. 让读者明确这些段落属于同一个完整的引述
3. 避免被误认为是多个独立的对话

**何时分段**：
- 对话内容较长（>100字）
- 语义有明显的层次或转折
- 便于阅读和理解

### Q7: Windows用户如何处理换行符问题？

**A**: Windows默认使用CRLF（`\r\n`），但本项目要求LF（`\n`）。

**推荐方案**：

1. **VSCode配置**（最简单）：
   ```json
   // .vscode/settings.json
   {
     "files.eol": "\n"
   }
   ```
   新建文件自动使用LF，打开CRLF文件时会提示转换。

2. **Git配置**（推荐）：
   ```bash
   # 提交时自动转换为LF，检出时保持LF
   git config --global core.autocrlf input
   ```

3. **手动转换**（批量处理现有文件）：
   ```bash
   # 使用dos2unix（需安装）
   dos2unix chapter_md/*.tagged.md

   # 或使用sed（Linux/macOS）
   sed -i 's/\r$//' chapter_md/*.tagged.md

   # 或使用Python
   python -c "import sys; data=open(sys.argv[1],'rb').read(); open(sys.argv[1],'wb').write(data.replace(b'\r\n',b'\n'))" file.md
   ```

4. **验证转换结果**：
   ```bash
   # 查看文件换行符类型
   file chapter_md/001_*.tagged.md
   # 应显示：UTF-8 text（无"with CRLF"字样）

   # 或使用Git检查
   git diff --check
   # 无输出表示无混合换行符问题
   ```

**注意事项**：
- **不要在Windows记事本中编辑**：记事本会自动转换为CRLF
- **推荐编辑器**：VSCode、Notepad++、Sublime Text（均支持配置LF）
- **Git提交前检查**：运行`git diff --check`确保无混合换行符

---

## 九、相关文档

### 关联Skill
- [SKILL_01](SKILL_01_古籍校勘.md) - 古籍小学总览
- [SKILL_01a](SKILL_01a_标注完整性维护.md) - 标注完整性维护
- [SKILL_01b](SKILL_01b_多版本互校底本.md) - 多版本互校
- [SKILL_01g](SKILL_01g_标注符号集合原则.md) - 标注符号集合原则（标点、标注、Markdown符号完全分离）
- [SKILL_10f](SKILL_10f_Skill的提炼与转化.md) - Skill编写规范

### 参考标准
- 《标点符号用法》国家标准（GB/T 15834-2011）
- 《学术出版规范——一般要求》行业标准
- 中华书局《古籍整理出版情况简报》中的标点规范

### 学术资源
- 龙泉寺AI项目：https://gj.cool（古籍自动断句服务）
- 北京师范大学古籍智能研究中心：https://ai.bnu.edu.cn/gj
- 《基于深度学习的古籍文本自动断句与标点一体化研究》（ResearchGate论文）

---

**维护者**: Claude + 用户
**创建日期**: 2026-04-01
**最后更新**: 2026-04-01
**版本**: v1.0
