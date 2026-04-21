# labs/sanjia — 三家注抽取分析脚本

本目录存放抽取质量分析、统计、跨源对比相关的一次性脚本（非生产路径）。

生产路径：
- 抽取：`scripts/parse_sanjia_notes_v4.py`
- 缓存：`scripts/build_sanjia_cache.py`
- 渲染：`docs/js/sanjia-notes.js`

## 脚本

| 脚本 | 用途 |
|---|---|
| [sanjia_stats.py](sanjia_stats.py) | 生成 `reports/三家注数据统计.md`：条目数、体裁分布、题材、引证典籍 |
| [compare_full.py](compare_full.py) | 全库 130 章对 wikisource_sanjia 源 HTML 1:1 比对 |
| [compare_three_sources.py](compare_three_sources.py) | 抽 10 章三源对比（wiki HTML / 点校本 TXT / 我们 JSON） |
| [compare_dianjiao.py](compare_dianjiao.py) | 抽取点校本 `史记集解三家注索隐正义.txt` 逐章条目数 |
| [analyze_unmatched.py](analyze_unmatched.py) | 分析前端匹配算法未命中的 note，统计变体字差异频次 |

## 用法

```bash
# 生成统计报告
python labs/sanjia/sanjia_stats.py

# 全库对源 HTML 的完整性
python labs/sanjia/compare_full.py

# 三源抽样对比
python labs/sanjia/compare_three_sources.py
```
