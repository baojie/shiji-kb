# 个人录音知识图谱

用 SKILL 驱动的 AI 流水线，将日常录音/文本自动转化为结构化知识图谱。

## 架构

```
录音文件(.wav/.mp3) ──→ FunASR paraformer-zh ──→ 文本
文本(.txt) ─────────────────────────────────────→ 文本
                                                    │
                    ┌───────────────────────────────┘
                    ▼
            SKILL-清洗（去语气词/重复）
                    │
            SKILL-分割（按话题切段）
                    │
            SKILL-实体提取（6类：person/activity/location/emotion/decision/question）
                    │
            SKILL-人物追踪（合并同一人物）
                    │
            关系构建（共同出现/参与）
                    │
            SKILL-反思（3轮检查+纠错+SKILL自动打补丁）
                    │
                    ▼
              SQLite 知识图谱
```

## 快速开始

```bash
# 配置 harness/config.yaml 中的服务地址

# 测试服务连通性
python -m harness.cli test-asr
python -m harness.cli test-model

# 处理录音
python -m harness.cli process recording.wav

# 处理文本
python -m harness.cli process data/notes.txt

# 查询知识图谱
python -m harness.cli query "SELECT name, type, mention_count FROM entities ORDER BY mention_count DESC LIMIT 20"

# 查看统计
python -m harness.cli status
```

## 依赖

- Python 3.10+
- PyYAML (`pip install pyyaml`)
- FunASR 服务（语音转录，可选）
- 本地 LLM 服务（OpenAI 兼容接口，如 vLLM/Ollama 部署的 Qwen3.5-2B）

## SKILL 文档

| SKILL | 功能 |
|-------|------|
| SKILL-清洗 | 口语转录→书面句子 |
| SKILL-分割 | 连续叙述→话题片段 |
| SKILL-实体提取 | 提取6类实体 |
| SKILL-人物追踪 | 跨段人物合并 |
| SKILL-反思 | 检查提取质量 |

SKILL 文档在反思循环中会自动进化：发现的错误模式被追加到"禁止规则区"，下次运行自动应用。
