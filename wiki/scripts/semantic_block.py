"""
语义块插件（Python 端）

解析 Markdown body 中的 ::: <type> ... ::: 语法，支持两种块类型：

  ::: infobox
  label: 垓下之战
  date: -202
  location: 安徽灵璧
  participants: [刘邦, 项羽, 韩信]
  result: 汉胜楚败
  :::

  ::: meta
  birth_ce: -247
  death_ce: -210
  :::

块类型语义：
  - infobox  可见信息卡片，渲染为 <aside class="infobox ...">
             第一个 infobox 块的字段会合并到 sidebar（块优先于 frontmatter）
             后续 infobox 块渲染为行内浮动卡片
  - meta     不可见元数据注释，渲染为 <div data-meta='...' hidden>
             供 JS 插件读取，不影响页面显示

inline attrs 写法（开头行末尾）：
  ::: meta type=event date=-202

字段优先级：inline attrs > YAML content > frontmatter
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Optional

import yaml


# ---------------------------------------------------------------------------
# 正则
# ---------------------------------------------------------------------------

# 匹配整个 ::: 块；使用非贪婪匹配保证多块互不干扰
FENCED_BLOCK_RE = re.compile(
    r'^:::[ \t]+(\w+)([^\n]*)\n(.*?)^:::[ \t]*$',
    re.MULTILINE | re.DOTALL,
)

# 开头行末尾的 key=value 或 key="value" 属性
INLINE_ATTR_RE = re.compile(r'(\w+)=("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'|\S+)')

# 占位符（Unicode 私用区，MD 不会转义）
_PH_OPEN  = ""
_PH_CLOSE = ""
BLOCK_PH_RE = re.compile(rf"{_PH_OPEN}(\d+){_PH_CLOSE}")


# ---------------------------------------------------------------------------
# 字段显示名映射（有序，决定 infobox 行顺序）
# ---------------------------------------------------------------------------

INFOBOX_FIELD_MAP: list[tuple[str, str]] = [
    ("label",          "名称"),
    ("canonical_name", "规范名"),
    ("type",           "类型"),
    ("birth_ce",       "生"),
    ("death_ce",       "卒"),
    ("native",         "籍贯"),
    ("title",          "封号"),
    ("office",         "官职"),
    ("date",           "时间"),
    ("end_date",       "终止"),
    ("location",       "地点"),
    ("participants",   "参与方"),
    ("result",         "结果"),
    ("modern_name",    "今地名"),
    ("region",         "所属"),
    ("tags",           "标签"),
    ("aliases",        "别名"),
    ("note",           "备注"),
    ("pn",             "段落号"),
]

_FIELD_MAP_KEYS: set[str] = {k for k, _ in INFOBOX_FIELD_MAP}
_DATE_KEYS: frozenset[str] = frozenset({"birth_ce", "death_ce", "date", "end_date"})

# frontmatter 系统/注册表字段，不应出现在 infobox 展示中
SYSTEM_EXCLUDE_KEYS: frozenset[str] = frozenset({
    "id", "featured", "auto_generated", "path",
    "total_refs", "total_chapters", "quality_score",
    "lifespan", "revision_count",
})

# type 字段值的中文翻译
TYPE_VALUE_MAP: dict[str, str] = {
    "person":   "人物",
    "place":    "地名",
    "state":    "邦国",
    "official": "官职",
    "identity": "身份",
    "dynasty":  "朝代",
    "event":    "事件",
    "chapter":  "章节",
    "topic":    "主题",
    "meta":     "元页",
}


# ---------------------------------------------------------------------------
# 数据类
# ---------------------------------------------------------------------------

@dataclass
class SemanticBlock:
    idx: int         # 页面内序号（0-based），用于占位符
    block_type: str  # "infobox" | "meta" | 其他自定义类型
    meta: dict       # 已合并 inline attrs 的元数据


# ---------------------------------------------------------------------------
# 解析
# ---------------------------------------------------------------------------

def _parse_inline_attrs(s: str) -> dict:
    """解析 '::: type key=val key2="val val"' 中的属性部分。"""
    result: dict = {}
    for key, val in INLINE_ATTR_RE.findall(s):
        if len(val) >= 2 and val[0] in ('"', "'") and val[-1] == val[0]:
            val = val[1:-1]
        result[key] = val
    return result


def parse_semantic_blocks(body: str) -> tuple[str, list[SemanticBlock]]:
    """
    扫描 body，将所有 ::: 块替换为占位符（\\ue020N\\ue021）。

    返回 (modified_body, blocks)：
      - modified_body：占位符已替换的正文，可直接传给 MD 渲染
      - blocks：按出现顺序排列的 SemanticBlock 列表
    """
    blocks: list[SemanticBlock] = []

    def _replace(m: re.Match) -> str:
        block_type   = m.group(1).lower()
        inline_str   = m.group(2) or ""
        yaml_content = m.group(3)

        inline_attrs = _parse_inline_attrs(inline_str)
        try:
            meta = yaml.safe_load(yaml_content) or {}
        except yaml.YAMLError:
            meta = {}
        if not isinstance(meta, dict):
            meta = {}

        # inline attrs 优先级最高，覆盖 YAML 同名字段
        meta.update(inline_attrs)

        idx = len(blocks)
        blocks.append(SemanticBlock(idx=idx, block_type=block_type, meta=meta))
        return f"{_PH_OPEN}{idx}{_PH_CLOSE}"

    modified = FENCED_BLOCK_RE.sub(_replace, body)
    return modified, blocks


# ---------------------------------------------------------------------------
# 渲染工具
# ---------------------------------------------------------------------------

def _fmt_value(key: str, v) -> str:
    """将字段值格式化为显示字符串。"""
    if v is None:
        return ""
    if isinstance(v, list):
        return " · ".join(str(x) for x in v)
    if isinstance(v, bool):
        return "是" if v else "否"
    if isinstance(v, int) and key in _DATE_KEYS:
        return f"前 {-v}" if v < 0 else str(v)
    if key == "type":
        return TYPE_VALUE_MAP.get(str(v), str(v))
    return str(v)


def render_infobox_html(meta: dict,
                        title: Optional[str] = None,
                        css_class: str = "infobox") -> str:
    """
    将 meta dict 渲染为 infobox HTML。

    - 先按 INFOBOX_FIELD_MAP 顺序输出已知字段
    - 再输出 meta 中额外的未知字段（原样显示 key 名）
    - label 字段用作卡片标题，不再出现在行内
    """
    label = meta.get("label") or title or ""
    rows: list[str] = []

    # 已知字段（按定义顺序）
    for key, display_name in INFOBOX_FIELD_MAP:
        if key == "label" or key not in meta:
            continue
        # canonical_name 与 label 相同时冗余，跳过
        if key == "canonical_name" and meta.get("canonical_name") == label:
            continue
        fv = _fmt_value(key, meta[key])
        if fv:
            rows.append(f"<tr><th>{display_name}</th><td>{fv}</td></tr>")

    # meta 中额外字段（不在映射表里的，且不是系统字段）
    for key, val in meta.items():
        if key in _FIELD_MAP_KEYS or key in SYSTEM_EXCLUDE_KEYS:
            continue
        fv = _fmt_value(key, val)
        if fv:
            rows.append(f"<tr><th>{key}</th><td>{fv}</td></tr>")

    if not rows and not label:
        return ""

    header = f"<h2>{label}</h2>" if label else ""
    return (
        f'<aside class="{css_class}">'
        f"{header}"
        f'<table>{"".join(rows)}</table>'
        f"</aside>"
    )


def expand_blocks_in_html(html: str,
                          blocks: list[SemanticBlock],
                          first_infobox_in_sidebar: bool = True) -> str:
    """
    将 MD 渲染后 HTML 中的占位符替换为最终 HTML。

    first_infobox_in_sidebar=True：
      第一个 infobox 块已由 sidebar slot 渲染，body 内跳过（不重复输出）。
    """
    infobox_seen = [0]

    def _replace(m: re.Match) -> str:
        idx   = int(m.group(1))
        block = blocks[idx]
        bt    = block.block_type

        if bt == "infobox":
            infobox_seen[0] += 1
            if infobox_seen[0] == 1 and first_infobox_in_sidebar:
                return ""   # sidebar 已渲染，body 内省略
            return render_infobox_html(block.meta, css_class="infobox inline")

        if bt == "meta":
            safe = json.dumps(block.meta, ensure_ascii=False).replace("'", "&#39;")
            return f"<div class=\"semantic-meta\" data-meta='{safe}' hidden></div>"

        # 未知类型：通用隐藏块（保留数据供 JS 扩展）
        payload = {"type": bt, **block.meta}
        safe = json.dumps(payload, ensure_ascii=False).replace("'", "&#39;")
        return (
            f'<div class="semantic-block" data-block-type="{bt}" '
            f"data-meta='{safe}' hidden></div>"
        )

    return BLOCK_PH_RE.sub(_replace, html)


def get_display_meta(page_meta: dict, blocks: list[SemanticBlock]) -> dict:
    """
    合并 frontmatter 与第一个 infobox 块的 meta，用于 sidebar 渲染。
    块字段优先级高于 frontmatter 同名字段。
    """
    merged = dict(page_meta)
    for block in blocks:
        if block.block_type == "infobox":
            merged.update(block.meta)
            break
    return merged
