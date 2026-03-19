# Skill 005 Sub-Skills

本目录包含 skill_005 (Personnel Appointment Consultation) 的子技能。

## 子技能列表

### 1. 动词标注 (Verb Annotation)

**文件**: [verb_annotation.md](verb_annotation.md)

**SKU**: skill_005_verb_annotation

**用途**: 为《史记》文本进行动词语义标注，识别和分类军事、刑罚等核心动词，构建结构化知识图谱。

**核心能力**:
- 识别军事动词（伐/攻/击/战等28个核心词）
- 识别刑罚动词（杀/诛/斩/弑等23个核心词）
- 识别政治动词（封/立等2个核心词）
- 区分动词与名词（⟦◉杀⟧ vs 〖[斩首〗）
- 判断消歧需求并添加说明

**相关文档**:
- [动词标注规范](../../../../doc/spec/动词标注规范.md)
- [动词渲染规则](../../../../doc/spec/动词渲染规则.md)
- [动词分类体系](../../../../kg/entities/data/verb_taxonomy.md)

**核心脚本**:
- `kg/entities/scripts/query_verbs_by_type.py` - 查询统计
- `kg/entities/scripts/validate_verb_tagging.py` - 验证质量
- `kg/entities/scripts/migrate_verb_tags.py` - 批量迁移

**当前状态**: v3.1，已完成全部130章标注，共6,178处动词标注

---

**维护**: Claude AI Agent
**更新**: 2026-03-19
