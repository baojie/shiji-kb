# labs/translation/ - 翻译实验

存放《史记》白话翻译实验数据。

**子目录**：
- `*.md` - 各章节白话翻译（`NNN_篇名_白话.md`）
- `quality/` - 翻译质量评估数据
- `v2/` - v2 版本翻译实验

**迁移说明**：原路径为 `doc/translation*/`，2026-05-14 迁移至 `labs/translation/`。

**相关脚本**：
- `scripts/generate_translation_json.py` - 将 .md 转为 JSON
- `scripts/evaluate_v2.py` - v1/v2 质量对比评估
- `scripts/sync_translation_disambig.py` - 同步实体消歧
