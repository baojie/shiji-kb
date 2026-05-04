# Wiki 图片资源

本目录存放 featured 精品页使用的图像。**所有图片必须**：

1. **公共领域** (PD) — 过版权年限的老画作、石刻拓片等
2. 或 **用户自己生成** (AI / 绘制) — 权属用户
3. **不允许**热链第三方版权图片

## 推荐来源

- **维基共享资源 (Wikimedia Commons)** 的 PD 图片, 下载后本地存储
- 南薰殿旧藏《历代帝王图》系列 (清代，已 PD)
- 吴道子《孔子行教像》(唐代石刻拓片)
- 《三才图会》(明万历,已 PD) 的历史人物图

## 命名约定

- 人物肖像: `<canonical>.jpg` 或 `<canonical>.png`
- 事件场景: `<event-slug>.jpg`
- 地图 / 示意图: `<topic>-map.svg`

## 元数据

每张图建议附 `images/<name>.json` 写明:
```json
{
  "source": "https://commons.wikimedia.org/wiki/...",
  "license": "PD (or CC0 / CC-BY-SA)",
  "author": "匿名 / 作者",
  "date": "约 1700 年",
  "description": "刘邦画像, 出自..."
}
```
