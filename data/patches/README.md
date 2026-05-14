# data/patches/ - 标注补丁数据

存放由各推断脚本生成的标注建议 TSV 文件，用于 `scripts/apply_annotation_patches.py` 批量应用。

**文件命名**：`NNN_篇名_类型.tsv`（类型如：别名补标、新实体、省称建议）

**用途**：结构化的标注修订建议，经人工确认后由脚本应用到 .tagged.md 文件。

**迁移说明**：原路径为 `doc/analysis/patch/`，2026-05-14 迁移至此。
