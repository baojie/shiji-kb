# 邦国反思（feudal-state）

对应 [SKILL_03k 邦国分类](../../../skills/SKILL_03k_邦国分类.md)。

## 分类体系（11 类）

- `cat-ancient-state` 上古方国
- `cat-dynasty` 朝代
- `cat-zhou-vassal` 周代诸侯（含原战国七雄）
- `cat-qin-end` 秦末列国
- `cat-han-vassal` 汉诸侯王国
- `cat-han-marquis` 汉侯国
- `cat-foreign` 外邦（含原外夷/西域）
- `cat-collective` 合称
- `cat-generic` 泛称
- `cat-tribe-mis` 部族误标（真·误标）
- `cat-place-mis` 地名误标（真·误标）
- `cat-split` 待拆分（真·误标）

## 工作流

- `kg/entities/scripts/classify_feudal_states.py` — 主分类脚本
- `kg/entities/scripts/rebuild_feudal_state_html.py` — 重建 HTML
- `kg/entities/scripts/dump_blank_feudal_states.py` — 导出未分类条目上下文

## 首轮（2026-04-22）

- 204 条全部分类（100% 覆盖，0 未分类）
- 12 条真·误标候选（tribe-mis 2 / split 10）→ 反向触发 03e1
- 9 条多标签（跨时代双重身份，全部合理）
- 用户反馈"侯国也算邦国"→ 新增 `cat-han-marquis` 类（8 条），地名误标归 0

详见 [第一轮_反思报告.md](第一轮_反思报告.md)。
