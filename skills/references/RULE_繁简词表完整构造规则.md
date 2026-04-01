---
name: rule-s2t-complete-variants
title: 繁简词表完整构造规则
description: 使用LLM逐章分析，穷尽所有OpenCC未正确转换的词组，构造完整的自定义词表，并总结规律作为OpenCC补丁。
status: 规划中（未执行）
priority: 中期目标
---

# 繁简词表完整构造规则

> **目标**：通过LLM辅助的系统化分析，构造一个**完整**的繁简自定义词表，覆盖《史记》中所有OpenCC未正确转换的词组。

---

## 一、背景与动机

### 1.1 当前状态（v3.0）

**已完成**：
- 36条精准规则
- 修复183个已知错误
- 覆盖率：100%（针对已识别的错误）

**局限性**：
- 只覆盖4个高频字符的上下文问题（后、于、发、历）
- 其余83个一对多字符未系统分析
- 可能存在未被统计方法识别的低频错误

### 1.2 目标

通过**LLM逐章反思**，构造一个**完整**的词表：

1. **穷尽性**：覆盖所有130章，不遗漏任何OpenCC错误
2. **系统性**：不依赖统计阈值（≥3次），包括低频错误
3. **规律性**：从完整词表中总结规律，优化规则结构

---

## 二、方法论：LLM辅助的完整分析

### 2.1 总体流程

```
【阶段1：逐章分析】
  对每一章（1-130）：
    1. 加载简体原文
    2. OpenCC转换为繁体
    3. LLM分析转换结果
       - 识别所有可疑转换
       - 检查上下文语义
       - 判断是否错误
    4. 输出错误词组列表

【阶段2：词表构造】
  1. 合并130章的错误词组
  2. 去重和频率统计
  3. 人工审核高频词组（≥5次）
  4. 构造完整词表v4.0

【阶段3：规律提取】
  1. 按字符分组（如"后"字、"于"字）
  2. 按语义分组（人名、地名、官职、时间）
  3. 识别规律模式
  4. 优化规则结构（如正则规则）

【阶段4：验证与迭代】
  1. 全文应用v4.0词表
  2. LLM重新检查转换结果
  3. 识别剩余错误
  4. 迭代优化词表
```

### 2.2 核心创新：LLM上下文分析

**为什么需要LLM**：

传统统计方法的局限：
- ❌ 无法理解语义（"后"是爵位还是时间？）
- ❌ 依赖频率阈值（低频错误会被忽略）
- ❌ 无法验证正确性（统计≠语义正确）

LLM的优势：
- ✅ **理解上下文**：根据前后文判断"后"的含义
- ✅ **识别低频错误**：不依赖统计，逐字分析
- ✅ **专家级判断**：具备古汉语知识，理解古籍用法

---

## 三、详细执行流程

### 3.1 阶段1：逐章分析（130次迭代）

#### 输入
```python
{
  "chapter_id": "001",
  "title": "五帝本纪",
  "simplified_text": "...",  # 简体原文
  "opencc_result": "..."     # OpenCC转换结果
}
```

#### LLM Prompt 模板

```
你是一位古汉语专家，精通繁简体转换。

【任务】
分析以下《史记》章节的OpenCC繁体转换结果，识别所有不符合古籍用法的错误转换。

【简体原文】
{simplified_text}

【OpenCC转换结果】
{opencc_result}

【分析要求】
1. 逐词检查OpenCC转换结果
2. 重点关注以下87个一对多字符：
   {one_to_many_chars}
3. 判断标准：
   - 根据上下文语义判断繁体形式是否正确
   - 参考古籍用法（如"后"作爵位应保持"后"）
   - 人名、地名的特定繁体写法

【输出格式】
请以JSON格式输出所有错误转换：

```json
{
  "errors": [
    {
      "simplified": "于定国",
      "opencc_converted": "於定國",
      "correct": "于定国",
      "reason": "姓氏应保持'于'，不应转为'於'",
      "context": "...于定国为廷尉...",
      "category": "人名-姓氏"
    },
    ...
  ],
  "summary": {
    "total_errors": 12,
    "categories": {"人名-姓氏": 3, "时间词": 5, ...}
  }
}
```

【重要提示】
- 只报告**真实错误**，不包括异体字选择差异
- 如OpenCC转为"擊"，维基用"撃"，这是异体字差异，不是错误
- 关注上下文相关的转换错误（如"后"字在不同语境的不同形式）
```

#### 输出
```json
{
  "chapter_id": "001",
  "errors": [
    {
      "simplified": "历山",
      "opencc_converted": "歷山",
      "correct": "曆山",
      "reason": "地名，历法之山，应转'曆'",
      "occurrences": 3
    },
    ...
  ],
  "total_errors": 8
}
```

### 3.2 阶段2：词表构造

#### 步骤1：合并130章结果

```python
def merge_chapter_errors(chapter_results):
    """合并130章的错误词组"""
    all_errors = defaultdict(lambda: {
        'opencc': None,
        'correct': None,
        'reason': None,
        'occurrences': 0,
        'chapters': []
    })

    for result in chapter_results:
        for error in result['errors']:
            key = error['simplified']
            all_errors[key]['opencc'] = error['opencc_converted']
            all_errors[key]['correct'] = error['correct']
            all_errors[key]['reason'] = error['reason']
            all_errors[key]['occurrences'] += error['occurrences']
            all_errors[key]['chapters'].append(result['chapter_id'])

    return all_errors
```

#### 步骤2：频率统计与分类

```python
def categorize_errors(all_errors):
    """按频率和类型分类"""
    categories = {
        'high_freq': [],      # ≥10次
        'medium_freq': [],    # 3-9次
        'low_freq': [],       # 1-2次
    }

    for simp, data in all_errors.items():
        freq = data['occurrences']
        if freq >= 10:
            categories['high_freq'].append((simp, data))
        elif freq >= 3:
            categories['medium_freq'].append((simp, data))
        else:
            categories['low_freq'].append((simp, data))

    return categories
```

#### 步骤3：人工审核策略

| 频率分类 | 数量（估计） | 审核策略 |
|---------|------------|---------|
| 高频（≥10次） | ~50条 | **必须人工审核**，确保100%正确 |
| 中频（3-9次） | ~150条 | **抽样审核**，LLM结果置信度高则直接采用 |
| 低频（1-2次） | ~300条 | **LLM直接采用**，后续使用中发现问题再修正 |

#### 步骤4：生成v4.0词表

```python
def generate_v4_variants(reviewed_errors):
    """生成v4.0自定义词表"""
    v4_variants = {}

    for simp, data in reviewed_errors.items():
        # 规则：只用词组，禁止单字
        if len(simp) >= 2:
            v4_variants[simp] = data['correct']

    return v4_variants
```

**预期规模**：v3.0 (36条) → v4.0 (150-250条)

### 3.3 阶段3：规律提取

#### 3.3.1 按字符分组

```python
def group_by_character(v4_variants):
    """按包含的一对多字符分组"""
    groups = defaultdict(list)

    one_to_many_chars = ['后', '于', '发', '历', '复', '里', ...]  # 87个

    for simp, trad in v4_variants.items():
        for char in one_to_many_chars:
            if char in simp:
                groups[char].append((simp, trad))

    return groups
```

**示例输出**：
```
"后"字规则（23条）:
  - 吕后 → 呂后
  - 太后 → 太后
  - 后世 → 後世
  ...

"于"字规则（6条）:
  - 于定国 → 于定国
  - 于单 → 于单
  - 于是 → 於是
  ...
```

#### 3.3.2 按语义分组

```python
def group_by_semantics(v4_variants):
    """按语义类别分组（使用LLM）"""
    # LLM Prompt: 对每个词组分类
    categories = {
        '人名-姓氏': [],
        '人名-名': [],
        '地名': [],
        '官职': [],
        '时间词': [],
        '历法术语': [],
        '其他': []
    }

    for simp, trad in v4_variants.items():
        category = llm_classify(simp, context)
        categories[category].append((simp, trad))

    return categories
```

**示例输出**：
```
人名-姓氏（4条）:
  - 于定国 → 于定国
  - 于单 → 于单

历法术语（5条）:
  - 历日 → 曆日
  - 历数 → 曆數
  - 颛顼历 → 颛顼曆
```

#### 3.3.3 识别规律模式

**目标**：从词组规则中提取通用规律

```python
def extract_patterns(grouped_variants):
    """提取规律模式"""
    patterns = []

    # 示例：姓氏"于"的规律
    # 规则: 于 + 单字名 → 保持"于"
    if '于' in grouped_variants:
        yu_rules = grouped_variants['于']
        # 检查是否所有"于X"（X为单字）都保持"于"
        if all(rule[0][0] == '于' and len(rule[0]) == 2
               for rule in yu_rules if len(rule[0]) == 2):
            patterns.append({
                'type': 'regex',
                'pattern': '于[人名]',  # 伪代码
                'replacement': '于$1',
                'description': '姓氏"于"保持不变'
            })

    return patterns
```

**可能的规律**：
1. **姓氏模式**：`于 + 单字名` → 保持"于"
2. **历法模式**：`历 + [日|数|度]` → 转"曆"
3. **爵位模式**：`[X]后` → 保持"后"（吕后、太后、皇后）
4. **时间模式**：`[其|之|然|前|先]后` → 转"後"

### 3.4 阶段4：验证与迭代

#### 步骤1：全文应用v4.0

```python
def apply_v4_and_verify(chapter_text, v4_variants):
    """应用v4.0词表并验证"""
    # 1. OpenCC基础转换
    opencc_result = opencc.convert(chapter_text)

    # 2. 应用v4.0词表
    final_result = apply_custom_variants(opencc_result, v4_variants)

    # 3. LLM验证
    verification_prompt = f"""
    检查以下繁体转换结果是否还有错误：

    【繁体文本】
    {final_result}

    【要求】
    识别任何剩余的繁简转换错误。
    """

    remaining_errors = llm.analyze(verification_prompt)

    return remaining_errors
```

#### 步骤2：迭代优化

```
第1轮：v4.0（初版，150-250条规则）
  ↓
LLM验证 → 发现30个剩余错误
  ↓
第2轮：v4.1（新增30条规则）
  ↓
LLM验证 → 发现5个剩余错误
  ↓
第3轮：v4.2（新增5条规则）
  ↓
LLM验证 → 无剩余错误
  ↓
最终版本：v4.2（~285条规则）
```

---

## 四、质量控制

### 4.1 自动化检查

```python
def quality_checks(v4_variants):
    """质量检查清单"""

    # 1. 禁止单字规则
    single_chars = [k for k in v4_variants if len(k) == 1]
    assert len(single_chars) == 0, f"发现单字规则: {single_chars}"

    # 2. 简繁一致性检查
    for simp, trad in v4_variants.items():
        # 检查简体部分是否真的需要转换
        opencc_result = opencc.convert(simp)
        assert opencc_result != trad, f"规则冗余: {simp}"

    # 3. 频率验证
    for simp, trad in v4_variants.items():
        freq = count_in_shiji(simp)
        if freq == 0:
            print(f"⚠️ 警告: {simp} 在《史记》中未出现")

    # 4. 冲突检测
    detect_rule_conflicts(v4_variants)
```

### 4.2 人工审核要点

**高频规则（≥10次）审核清单**：

1. **语义正确性**
   - ✅ 转换后的繁体形式符合古籍用法
   - ✅ 上下文语义一致

2. **覆盖完整性**
   - ✅ 同类词是否都已覆盖（如"吕后"有了，"薄后"呢？）

3. **规则冲突**
   - ✅ 是否与其他规则冲突（长词优先匹配）

4. **异体字差异**
   - ✅ 确认不是异体字选择差异

### 4.3 回归测试

```python
def regression_test():
    """回归测试：确保v4.0不破坏v3.0已修复的错误"""

    # 加载v3.0的183个已知错误
    known_errors = load_known_errors()

    # 应用v4.0转换
    for error in known_errors:
        result = convert_with_v4(error['simplified'])
        assert result == error['correct'], \
            f"v4.0破坏了v3.0的修复: {error['simplified']}"

    print("✅ 回归测试通过：v4.0保持v3.0的所有修复")
```

---

## 五、预期成果

### 5.1 v4.0词表特点

| 特性 | v3.0 | v4.0（预期） |
|-----|------|------------|
| 规则数量 | 36条 | 150-250条 |
| 覆盖字符 | 4个（后、于、发、历） | 87个（所有一对多字符） |
| 覆盖方法 | 统计驱动（≥3次） | LLM穷尽分析 |
| 低频错误 | 未覆盖 | 完全覆盖 |
| 规律提取 | 人工总结 | LLM辅助总结 |

### 5.2 规律文档

**输出**：[`doc/spec/ANALYSIS_繁简映射总结.md`](../../doc/spec/ANALYSIS_繁简映射总结.md)

内容包括：
1. **字符级规律**（87个一对多字符的转换规律）
2. **语义级规律**（人名、地名、官职等的转换规则）
3. **可能的正则规则**（如`于[人名]` → 保持"于"）
4. **OpenCC补丁建议**（可提交给OpenCC官方）

### 5.3 覆盖率报告

**输出**：见 `CHANGELOG_custom-variants.md` 或相关分析文档

```markdown
# v4.0 覆盖率报告

## 统计数据

- 总分析字符：577,186
- 一对多字符出现：19,493次
- v3.0覆盖：183个错误（基于统计分析）
- v4.0覆盖：XXX个错误（基于LLM穷尽分析）
- 覆盖率提升：XXX%

## 分字符覆盖情况

| 字符 | v3.0规则数 | v4.0规则数 | 新增规则 |
|-----|-----------|-----------|---------|
| 后 | 23 | 25 | +2 |
| 于 | 6 | 12 | +6 |
| 发 | 3 | 8 | +5 |
| 历 | 4 | 6 | +2 |
| 复 | 0 | 5 | +5 |
| ... | ... | ... | ... |
```

---

## 六、实施计划

### 6.1 时间估算

| 阶段 | 工作量 | 时间估算 |
|-----|-------|---------|
| 阶段1：逐章分析（130章） | 130次LLM调用 | 2-3天 |
| 阶段2：词表构造 | 合并+审核 | 1天 |
| 阶段3：规律提取 | LLM分析+人工总结 | 1天 |
| 阶段4：验证与迭代 | 2-3轮迭代 | 1-2天 |
| **总计** | | **5-7天** |

### 6.2 资源需求

1. **LLM API**
   - 估计调用次数：130章分析 + 50次审核 + 130章验证 = ~310次
   - 推荐模型：Claude Sonnet/GPT-4（需要古汉语理解能力）

2. **人工审核**
   - 高频规则审核：~50条 × 5分钟 = 4小时
   - 中频规则抽查：~150条 × 1分钟 = 2.5小时
   - **总计**：~1个工作日

3. **计算资源**
   - Python环境
   - OpenCC库
   - 足够存储（中间结果~100MB）

### 6.3 风险与缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|-----|------|------|---------|
| LLM误判古汉语用法 | 中 | 高 | 高频规则人工审核，低频规则迭代修正 |
| 规则数量过多（>500条） | 低 | 中 | 提取规律，合并相似规则 |
| 规则冲突 | 低 | 高 | 自动冲突检测，长词优先匹配 |
| API成本过高 | 低 | 低 | 批量处理，缓存结果 |

---

## 七、成功标准

### 7.1 定量指标

- ✅ **覆盖率**：v4.0覆盖所有87个一对多字符的错误
- ✅ **规模**：词表规模150-250条（相比v3.0的36条）
- ✅ **准确率**：人工抽查准确率≥95%
- ✅ **回归测试**：v3.0的183个错误全部保持修复

### 7.2 定性指标

- ✅ **规律清晰**：能总结出字符级和语义级的转换规律
- ✅ **可维护**：规则有明确的理由和上下文
- ✅ **可扩展**：规律可应用于其他古籍（如《汉书》《三国志》）
- ✅ **文档完整**：规律总结、覆盖率报告、使用说明

---

## 八、后续应用

### 8.1 扩展到其他古籍

v4.0的规律可直接应用于：

| 古籍 | 字符数 | 预期直接可用率 | 需新增规则 |
|-----|-------|--------------|----------|
| 《汉书》 | ~800K | 80-90% | 20-50条 |
| 《三国志》 | ~360K | 85-95% | 10-30条 |
| 《资治通鉴》 | ~3000K | 70-80% | 50-100条 |

### 8.2 贡献给OpenCC

将总结的规律提交给OpenCC官方：

1. **字符级规则**：补充到OpenCC的上下文词典
2. **语义级规则**：建议新增"古籍模式"转换配置
3. **人名地名规则**：补充专有名词词典

---

## 九、参考文档

### 9.1 相关SKILL

- [SKILL_01e 繁简体处理](../SKILL_01e_繁简体处理.md) - 当前v3.0实现
- [SKILL_00-M02 迭代工作流](../00-META-02_迭代工作流.md) - MVP→完整版方法论

### 9.2 技术文档

- [OpenCC 文档](https://github.com/BYVoid/OpenCC)
- [繁简映射统计报告](../../doc/spec/ANALYSIS_繁简映射统计.md)
- [OpenCC错误率分析](../../doc/spec/ANALYSIS_OpenCC错误率.md)

---

## 十、附录

### 10.1 LLM Prompt 完整模板

详见 [LLM_Prompts.md](./LLM_Prompts.md)（待创建）

### 10.2 数据格式规范

#### 章节错误输出格式
```json
{
  "chapter_id": "001",
  "chapter_title": "五帝本纪",
  "analysis_timestamp": "2026-03-31T16:30:00Z",
  "errors": [
    {
      "simplified": "于定国",
      "opencc_converted": "於定國",
      "correct": "于定国",
      "reason": "姓氏应保持'于'",
      "category": "人名-姓氏",
      "context": "...于定国为廷尉...",
      "confidence": 0.95,
      "occurrences": 3,
      "positions": [1234, 5678, 9012]
    }
  ],
  "summary": {
    "total_errors": 8,
    "by_category": {
      "人名-姓氏": 3,
      "时间词": 2,
      "历法术语": 3
    }
  }
}
```

---

**创建日期**：2026-03-31
**状态**：规划中（未执行）
**优先级**：中期目标（v3.0稳定后执行）
**预期完成时间**：5-7天
**作者**：Claude Code
**审核**：待用户确认