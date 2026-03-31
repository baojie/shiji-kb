# 参考文献

本目录收集与史记知识库项目相关的参考文献、类似项目和技术资源。

**在线网站资源**：参见 [websites.md](websites.md)（简化列表）

---

## 学术研究

- 蒙克，"公元前546年：春秋战国历史分期的机器学习新证"，《开放时代》2026年第1期。
  - 微信原文：https://mp.weixin.qq.com/s/7UUtwzkCanzKX1MuX3cMWQ
  - 核心论点：春秋与战国的分野是国家建构底层游戏规则的范式转型，从以规范性权威（normative authority）为主导转向以强制性权力（coercive power）为核心。临界点为公元前546年（第二次弭兵会盟），而非传统的前481/475/403年。
  - 方法：基于原创数据集《祀与戎》，将《左传》等史料量化为军事、外交、内政、话语模式指标，采用归纳式随机森林（random forest）机器学习方法，让历史模式自行浮现。
  - 关键发现：
    - 构建"规范秩序指数"（NOI）追踪时代精神气候，发现前546年出现断崖式崩坏
    - 规范性权威与强制性权力的重要性曲线在前546年后发生"死亡交叉"
    - 前546年弭兵会盟后，强制性权力的重要性不可逆转地超越规范性权威
    - 旧规则（权威）并未消失，而是被降级收编为服务于新规则（权力）的工具
  - 与本项目关联：本项目事件索引覆盖《史记》全130篇，其中大量春秋战国事件的年代标注、事件分期可与该研究的定量分析形成互证。该研究的"规范性权威→强制性权力"范式转型框架，可为本项目后续高级分析（如事件聚类、时代特征提取）提供理论视角。

## 阅读价值与知识提取

- 周江岭，"图形化阅读价值系统"，演示文稿（PDF，33页）。
  - 本地文件：[图形化阅读价值系统.pdf](图形化阅读价值系统.pdf)
  - 核心理念：从"卖书"转向"卖阅读价值"。传统出版行业只管售前（把书卖掉），缺乏售中（阅读过程）和售后（知识沉淀）的价值服务。提出图形化阅读价值系统，将阅读从被动消费转化为主动的知识生产。
  - WHY（为什么做）：
    - 出版业从卖书→卖百货→需要卖阅读价值的趋势演变
    - 亚马逊、当当、京东等已覆盖售前售中，但"阅读价值"维度尚无玩家
    - 商业价值估算：图书+报纸+杂志发行抽成模式，年营收潜力约8000万
  - HOW（如何做）：7个模块构成阅读价值链
    1. **扫读**：获得速度（类比音乐/电影的进度记录，为阅读引入时间管理）
    2. **内容**：获得案例（从书中提取有案例价值的片段，如图表、数据）
    3. **估值**：标注价值（按兴趣/工作/研究/分享等维度标注内容价值）
    4. **备注**：随手记（短期记忆→记下了；长期记忆→形成知识摘要）
    5. **反馈**：获得交流对象（连接作者、出版社、Fans等）
    6. **强项**：挖掘出卖点（产生自己的特色，建立品牌）
    7. **捕捉**：获得高度关联知识（行业消息、图书、名人、机构、软件、Skill等）
  - WHAT（什么是阅读价值）：
    - 以布鲁姆分类法（知识→理解→应用→分析→综合→评估）为理论框架
    - 强调从"记忆"走向"分析、综合、评估"的高阶认知
    - 阅读数据是"数据黄金"——亚马逊Kindle已积累阅读行为数据但未开放
  - 与本项目关联：本项目的事件索引+知识图谱+可视化（地铁图、事件页面）本质上就是对《史记》的"图形化阅读价值系统"实践——将古籍阅读从线性文本消费转化为结构化知识探索。该框架的7模块思路（扫读→内容→估值→备注→反馈→强项→捕捉）可为本项目的用户交互设计和价值呈现提供参考。



## 技术工具与框架

### NLP工具

- LTP (Language Technology Platform)
  - GitHub: https://github.com/HIT-SCIR/ltp
  - 开发方：哈工大社会计算与信息检索研究中心
  - 定位：中文自然语言处理工具包
  - 功能：分词、词性标注、命名实体识别、依存句法分析、语义角色标注等
  - 与本项目关联：本项目曾尝试使用LTP进行古文分析，遇到Python 3.13兼容性问题。详见 [labs/hybrid-semantic-analysis/LTP_COMPATIBILITY_ISSUE.md](../../labs/hybrid-semantic-analysis/LTP_COMPATIBILITY_ISSUE.md)

### 大语言模型

- Qwen2.5 (通义千问2.5)
  - Hugging Face: https://huggingface.co/Qwen/Qwen2.5-7B-Instruct
  - 开发方：阿里巴巴达摩院
  - 模型规格：0.5B / 1.5B / 3B / 7B / 14B / 32B / 72B 多个版本
  - 特点：中文理解能力强，支持长文本（最高128K上下文）
  - 与本项目关联：本项目曾尝试使用Qwen2.5-7B进行史记文本分析，遇到8GB显存限制。详见 [labs/hybrid-semantic-analysis/QWEN_MEMORY_ISSUE.md](../../labs/hybrid-semantic-analysis/QWEN_MEMORY_ISSUE.md)

- bitsandbytes — 大模型量化工具
  - GitHub: https://github.com/TimDettmers/bitsandbytes
  - 定位：PyTorch的8位和4位量化库
  - 功能：将模型权重压缩到INT8/INT4，显著降低显存占用
  - 与本项目关联：可用于在有限显存环境（如8GB）下运行大语言模型

- Transformers 量化指南
  - 文档: https://huggingface.co/docs/transformers/quantization
  - 内容：使用Transformers库进行模型量化的官方指南
  - 涵盖：bitsandbytes量化、GPTQ量化、AWQ量化等多种方法

### AI辅助开发工具

- Claude Code
  - 官网: https://claude.com/claude-code
  - 文档: https://docs.claude.com/en/docs/claude-code
  - 开发方：Anthropic
  - 定位：AI驱动的代码编辑器和开发助手
  - 核心功能：
    - 自然语言编程：用自然语言描述需求，AI直接生成代码并执行
    - 文件操作：Read/Write/Edit文件，支持批量操作和正则替换
    - Shell集成：执行bash命令、git操作、包管理等
    - Agent系统：支持创建专门化的子任务Agent（Explore/Task）
    - SKILL系统：通过结构化自然语言文档（SKILL）定义可复用工作流
  - 与本项目关联：本项目全程使用Claude Code进行开发，包括：
    - 130篇标注文件的批量处理和质量检查
    - 41个SKILL文档的编写和管理
    - 事件索引、实体索引、知识图谱的构建
    - 自动化脚本开发（Python/Bash）
    - Git工作流和版本管理
    - CHANGELOG和TODO的维护
  - 实践文档：[CLAUDE.md](../../CLAUDE.md) — 项目级Claude Code使用规范

### API与数据交换

- HuggingFace Hub
  - GitHub Releases: https://github.com/huggingface/huggingface_hub/releases
  - 定位：与Hugging Face模型中心交互的Python库
  - 功能：模型/数据集下载、上传、版本管理
  - 注意事项：v0.25.0+版本将`use_auth_token`参数改为`token`，影响旧版LTP等工具

## 项目相关问题记录

### Issue追踪

- 史记知识库 Issue #1 — 时间与数量标注混淆
  - GitHub: https://github.com/baojie/shiji-kb/issues/1
  - 问题描述：部分数量词（如"千石"、"八篇"、"十五郡"）被错误标注为时间类型
  - 修复记录：
    - [logs/issue_1_时间数量混淆修复报告.md](../../logs/issue_1_时间数量混淆修复报告.md)
    - [logs/issue_1_完整修复报告.md](../../logs/issue_1_完整修复报告.md)
  - 修复成果：共修复46处错误标注，涉及22个章节，29种表达

---

更多在线网站资源请参见 [websites.md](websites.md)