#!/usr/bin/env python3
"""渲染散文集 HTML 页面 — 按章节时间排序，类型作标签。"""

import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from semantic_tags import render_tags_to_html  # noqa: E402


TYPE_ORDER = ["诏令", "奏疏", "书信", "檄文", "谏言", "策论", "议论"]

TYPE_COLORS = {
    "诏令": "#c0392b",
    "奏疏": "#2980b9",
    "书信": "#27ae60",
    "檄文": "#e67e22",
    "谏言": "#8e44ad",
    "策论": "#d35400",
    "议论": "#2c3e50",
}


def render_entity_tags(text: str) -> str:
    return render_tags_to_html(text, normalize_legacy=True)


def format_prose(content: str) -> str:
    """处理散文：保留段号、每段一行、转换实体。"""
    paragraphs = []
    cur: list[str] = []
    for raw in content.split("\n"):
        line = raw.strip()
        if not line:
            if cur:
                paragraphs.append(" ".join(cur))
                cur = []
            continue
        # 段号提示保留在开头
        m = re.match(r"^\[(\d+(?:\.\d+)*)\]\s*(.*)$", line)
        if m:
            if cur:
                paragraphs.append(" ".join(cur))
                cur = []
            rest = m.group(2)
            if rest:
                cur = [render_entity_tags(rest)]
        else:
            cur.append(render_entity_tags(line))
    if cur:
        paragraphs.append(" ".join(cur))
    return "".join(f"<p>{p}</p>" for p in paragraphs)


def _plain_chars(content: str) -> int:
    """去标注后的纯文本字数（只计汉字和标点）。"""
    text = re.sub(r"[〖⟦][^〗⟧]*[〗⟧]", "", content)
    text = re.sub(r"\[[\d.]+\]\s*", "", text)
    text = re.sub(r"\s+", "", text)
    return len(text)


def generate_html(json_path: Path, output_path: Path) -> None:
    data = json.loads(json_path.read_text(encoding="utf-8"))

    # 按章节号排序（已在 manifest 中排好）
    for idx, item in enumerate(data):
        item["_uid"] = f"sanwen-{idx}"
        item["_chars"] = _plain_chars(item.get("content", ""))

    # 统计各类型数量
    by_type: dict[str, int] = {}
    for item in data:
        by_type[item["type"]] = by_type.get(item["type"], 0) + 1

    type_badge_css = "\n".join(
        f'    .badge-{t} {{ background:{c}; color:#fff; padding:2px 8px; border-radius:3px; font-size:.75em; margin-left:8px; vertical-align:middle; }}'
        for t, c in TYPE_COLORS.items()
    )

    head = f"""<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>史记散文集</title>
  <link rel="stylesheet" href="../css/shiji-styles-v6.css">
  <style>
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    body {{ font-family:"Source Han Serif SC","Noto Serif SC",serif; line-height:2; color:#333; background:#fdfaf6; padding:20px; }}
    .container {{ max-width:900px; margin:0 auto; background:#fff; padding:40px; box-shadow:0 2px 10px rgba(0,0,0,.1); }}
    h1 {{ text-align:center; color:#8b4513; font-size:2.5em; margin-bottom:10px; border-bottom:3px double #8b4513; padding-bottom:20px; }}
    .subtitle {{ text-align:center; color:#666; margin-bottom:40px; font-size:1.1em; }}
    .nav {{ background:#f5f5f5; padding:15px; margin-bottom:30px; border-radius:5px; }}
    .nav a {{ color:#8b4513; text-decoration:none; margin-right:20px; }}
    .nav a:hover {{ text-decoration:underline; }}
    .nav a.pdf {{ color:#c00; font-weight:bold; }}
    .type-summary {{ background:#f9f9f9; padding:15px 20px; margin-bottom:30px; border-radius:5px; border-left:4px solid #8b4513; }}
    .type-summary span {{ margin-right:12px; }}
    .toc {{ background:#f9f9f9; padding:20px 30px; margin-bottom:40px; border-radius:5px; border-left:4px solid #8b4513; }}
    .toc h2 {{ font-size:1.5em; color:#8b4513; margin-bottom:15px; }}
    .toc ul {{ list-style:none; padding-left:0; }}
    .toc > ul > li {{ margin-bottom:6px; padding-left:20px; position:relative; }}
    .toc > ul > li:before {{ content:"📜"; position:absolute; left:0; }}
    .toc a {{ color:#333; text-decoration:none; font-size:1.05em; }}
    .toc a:hover {{ color:#8b4513; text-decoration:underline; }}
    .toc .ch-num {{ color:#999; font-size:.9em; }}
    .sanwen-item {{ margin-bottom:50px; border-left:3px solid #d4a373; padding-left:20px; }}
    .item-title {{ font-size:1.5em; color:#8b4513; margin-bottom:10px; font-weight:bold; }}
    .item-subtitle {{ font-size:.9em; color:#999; margin-bottom:14px; font-style:italic; }}
    .item-subtitle a {{ color:#999; text-decoration:none; }}
    .item-subtitle a:hover {{ color:#8b4513; text-decoration:underline; }}
    .item-intro {{ color:#666; font-size:.95em; margin-bottom:16px; padding:10px 14px; background:#fbf6ee; border-left:3px solid #c9a96e; border-radius:3px; }}
    .item-content {{ line-height:2.2; color:#333; text-align:justify; }}
    .item-content p {{ margin:0 0 1em; }}
    .footer {{ text-align:center; margin-top:50px; padding-top:20px; border-top:1px solid #ddd; color:#999; font-size:.9em; }}
{type_badge_css}
    @media (max-width:768px) {{ .container {{ padding:20px; }} h1 {{ font-size:1.8em; }} }}
  </style>
</head>
<body>
  <div class="container">
    <h1>史记散文集</h1>
    <div class="subtitle">共收录 {len(data)} 篇散文 · 按章节顺序排列</div>
    <div class="nav">
      <a href="../index.html">&larr; 返回首页</a>
      <a href="special_index.html">专项索引</a>
      <a href="sanwen.pdf" class="pdf">📥 下载PDF</a>
    </div>
"""

    # 类型统计条
    type_summary = '    <div class="type-summary">'
    for t in TYPE_ORDER:
        cnt = by_type.get(t, 0)
        if cnt:
            color = TYPE_COLORS.get(t, "#666")
            type_summary += f'<span class="badge-{t}">{t} {cnt}</span> '
    type_summary += "</div>\n"

    # 目录 — 按章节顺序
    toc = ['    <div class="toc"><h2>目录</h2><ul>']
    for it in data:
        badge = f'<span class="badge-{it["type"]}">{it["type"]}</span>'
        toc.append(
            f'      <li><a href="#{it["_uid"]}">{it["title"]}</a>{badge} '
            f'<span class="ch-num">{it["chapter_num"]} {it["chapter_title"]} · {it["_chars"]}字</span></li>'
        )
    toc.append("    </ul></div>")
    toc_html = "\n".join(toc) + "\n"

    # 正文 — 按章节顺序，不分类
    body_parts = []
    for it in data:
        content_html = format_prose(it["content"])
        intro_html = (
            f'<div class="item-intro">{render_entity_tags(it["intro"])}</div>'
            if it.get("intro")
            else ""
        )
        badge = f'<span class="badge-{it["type"]}">{it["type"]}</span>'
        body_parts.append(
            f'''    <div class="sanwen-item" id="{it["_uid"]}">
        <div class="item-title">{it["title"]}{badge}</div>
        <div class="item-subtitle">
          <a href="../chapters/{it["chapter_num"]}_{it["chapter_title"]}.html">{it["chapter_num"]} {it["chapter_title"]}</a>
          &middot; [{it["start_para"]}-{it["end_para"]}] &middot; {it["_chars"]}字
        </div>
        {intro_html}
        <div class="item-content">{content_html}</div>
      </div>'''
        )
    body = "\n".join(body_parts)

    total_chars = sum(it["_chars"] for it in data)
    tail = f"""
    <div class="footer">
      <p>史记知识库 | 散文专项索引</p>
      <p>共 {len(data)} 篇 · {total_chars:,} 字</p>
    </div>
  </div>
</body>
</html>
"""
    output_path.write_text(head + type_summary + toc_html + body + tail, encoding="utf-8")
    print(f"✓ HTML: {output_path}")


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    data_dir = root / "data"
    json_file = data_dir / "sanwen.json"
    if not json_file.exists():
        print(f"错误: {json_file} 不存在，先运行 extract_sanwen.py")
        return 1
    special_dir = root / "docs" / "special"
    special_dir.mkdir(parents=True, exist_ok=True)

    html_file = special_dir / "sanwen.html"
    generate_html(json_file, html_file)

    # 复制 JSON/MD 到 docs
    for ext in ("json", "md"):
        src = data_dir / f"sanwen.{ext}"
        dst = special_dir / f"sanwen.{ext}"
        if src.exists():
            shutil.copy2(src, dst)
    print(f"✓ JSON/MD → {special_dir}")

    # PDF
    try:
        from weasyprint import HTML

        pdf_file = special_dir / "sanwen.pdf"
        HTML(filename=str(html_file)).write_pdf(str(pdf_file))
        mb = pdf_file.stat().st_size / 1024 / 1024
        print(f"✓ PDF: {pdf_file} ({mb:.2f} MB)")
    except ImportError:
        print("⚠ weasyprint 未安装，跳过 PDF 生成")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
