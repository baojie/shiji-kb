#!/usr/bin/env python3
"""渲染散文集 HTML 页面（结构仿 render_yunwen_html.py）。"""

import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from semantic_tags import render_tags_to_html  # noqa: E402


TYPE_ORDER = ["诏令", "奏疏", "书信", "檄文", "策论", "议论"]


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


def generate_html(json_path: Path, output_path: Path) -> None:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    by_type: dict[str, list] = {}
    for item in data:
        by_type.setdefault(item["type"], []).append(item)

    for idx, item in enumerate(data):
        item["_uid"] = f"sanwen-{idx}"

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
    .toc {{ background:#f9f9f9; padding:20px 30px; margin-bottom:40px; border-radius:5px; border-left:4px solid #8b4513; }}
    .toc h2 {{ font-size:1.5em; color:#8b4513; margin-bottom:15px; }}
    .toc ul {{ list-style:none; padding-left:0; }}
    .toc > ul > li {{ margin-bottom:10px; padding-left:20px; position:relative; }}
    .toc > ul > li:before {{ content:"📜"; position:absolute; left:0; margin-right:8px; }}
    .toc a {{ color:#333; text-decoration:none; font-size:1.1em; }}
    .toc a:hover {{ color:#8b4513; text-decoration:underline; }}
    .toc-sub {{ list-style:none; padding-left:22px; margin-top:6px; }}
    .toc-sub li {{ margin-bottom:4px; padding-left:14px; font-size:.95em; position:relative; }}
    .toc-sub li:before {{ content:"•"; color:#999; position:absolute; left:0; }}
    .toc-sub a {{ font-size:.95em; color:#666; }}
    .type-section {{ margin-bottom:60px; }}
    .type-header {{ font-size:2em; color:#8b4513; margin-bottom:10px; border-left:5px solid #8b4513; padding-left:15px; }}
    .type-desc {{ color:#666; margin-bottom:30px; padding-left:20px; font-style:italic; }}
    .sanwen-item {{ margin-bottom:50px; border-left:3px solid #d4a373; padding-left:20px; }}
    .item-title {{ font-size:1.5em; color:#8b4513; margin-bottom:10px; font-weight:bold; }}
    .item-subtitle {{ font-size:.9em; color:#999; margin-bottom:14px; font-style:italic; }}
    .item-subtitle a {{ color:#999; text-decoration:none; }}
    .item-subtitle a:hover {{ color:#8b4513; text-decoration:underline; }}
    .item-intro {{ color:#666; font-size:.95em; margin-bottom:16px; padding:10px 14px; background:#fbf6ee; border-left:3px solid #c9a96e; border-radius:3px; }}
    .item-content {{ line-height:2.2; color:#333; text-align:justify; }}
    .item-content p {{ margin:0 0 1em; }}
    .footer {{ text-align:center; margin-top:50px; padding-top:20px; border-top:1px solid #ddd; color:#999; font-size:.9em; }}
    @media (max-width:768px) {{ .container {{ padding:20px; }} h1 {{ font-size:1.8em; }} }}
  </style>
</head>
<body>
  <div class="container">
    <h1>史记散文集</h1>
    <div class="subtitle">共收录 {len(data)} 篇散文（诏令、奏疏、书信、檄文、策论、议论）</div>
    <div class="nav">
      <a href="../index.html">← 返回首页</a>
      <a href="special_index.html">专项索引</a>
      <a href="sanwen.pdf" class="pdf">📥 下载PDF</a>
    </div>
"""

    toc = ['    <div class="toc"><h2>目录</h2><ul>']
    for t in TYPE_ORDER:
        items = by_type.get(t, [])
        if not items:
            continue
        toc.append(f'      <li><a href="#type-{t}">{t}（{len(items)}篇）</a>')
        toc.append('        <ul class="toc-sub">')
        for it in items:
            toc.append(
                f'          <li><a href="#{it["_uid"]}">{it["title"]} '
                f'<span style="color:#999">· {it["chapter_num"]} {it["chapter_title"]}</span></a></li>'
            )
        toc.append("        </ul>")
        toc.append("      </li>")
    toc.append("    </ul></div>")
    toc_html = "\n".join(toc) + "\n"

    body_parts = []
    for t in TYPE_ORDER:
        items = by_type.get(t, [])
        if not items:
            continue
        body_parts.append(f'    <div class="type-section" id="type-{t}">')
        body_parts.append(f'      <div class="type-header">{t}（{len(items)}篇）</div>')
        body_parts.append(f'      <div class="type-desc">{items[0]["type_desc"]}</div>')
        for it in items:
            content_html = format_prose(it["content"])
            intro_html = f'<div class="item-intro">{render_entity_tags(it["intro"])}</div>' if it.get("intro") else ""
            body_parts.append(f'''      <div class="sanwen-item" id="{it["_uid"]}">
        <div class="item-title">{it["title"]}</div>
        <div class="item-subtitle">
          <a href="../chapters/{it["chapter_num"]}_{it["chapter_title"]}.html">{it["chapter_num"]} {it["chapter_title"]}</a>
          · [{it["start_para"]}-{it["end_para"]}]
        </div>
        {intro_html}
        <div class="item-content">{content_html}</div>
      </div>''')
        body_parts.append("    </div>")
    body = "\n".join(body_parts)

    tail = """
    <div class="footer">
      <p>史记知识库 | 散文专项索引</p>
      <p>数据提取自《史记》标注版本</p>
    </div>
  </div>
</body>
</html>
"""
    output_path.write_text(head + toc_html + body + tail, encoding="utf-8")
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

    shutil.copy2(json_file, special_dir / "sanwen.json")
    md_file = data_dir / "sanwen.md"
    if md_file.exists():
        shutil.copy2(md_file, special_dir / "sanwen.md")
    print(f"✓ JSON/MD → {special_dir}")

    # PDF
    try:
        from weasyprint import HTML, CSS
        pdf_path = special_dir / "sanwen.pdf"
        pdf_css = CSS(string="""
            @page { size: A4; margin: 2.5cm 2cm;
                @top-center { content: "史记·散文集"; font-size: 10pt; color: #666; }
                @bottom-center { content: counter(page); font-size: 10pt; color: #666; } }
            body { font-family: "Noto Serif SC","Source Han Serif SC",serif; font-size: 12pt; line-height: 1.8; }
            h1 { font-size: 24pt; page-break-after: avoid; }
            .type-section { page-break-inside: avoid; margin-bottom: 30pt; }
            .type-header { font-size: 18pt; page-break-after: avoid; }
            .sanwen-item { page-break-inside: avoid; margin-bottom: 20pt; }
            .item-title { font-size: 14pt; page-break-after: avoid; }
            .nav, .toc { display: none; }
            a { color: #8b4513; text-decoration: none; }
        """)
        HTML(filename=str(html_file)).write_pdf(str(pdf_path), stylesheets=[pdf_css])
        print(f"✓ PDF: {pdf_path} ({pdf_path.stat().st_size/1024/1024:.2f} MB)")
    except ImportError:
        print("⚠️  WeasyPrint 未安装，跳过 PDF")
    except Exception as e:
        print(f"⚠️  PDF 失败: {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
