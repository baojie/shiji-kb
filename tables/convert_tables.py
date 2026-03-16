#!/usr/bin/env python3
"""
将史记十表 HTML 文件转换为 JSON 和 CSV 格式
输出目录: tables/data/
支持多段结构（如013_三代世表含三张子表）
"""
import json
import csv
import os
from html.parser import HTMLParser


class MultiTableParser(HTMLParser):
    """解析 HTML 中可能包含多张 <table> 的页面，并追踪 <h2> 分段标题。"""

    def __init__(self):
        super().__init__()
        self.title = ""
        # sections: list of {"section_title": str, "headers": [...], "rows": [[...]]}
        self.sections = []
        self._in_h1 = False
        self._in_h2 = False
        self._in_thead = False
        self._in_tbody = False
        self._in_th = False
        self._in_td = False
        self._current_row = []
        self._current_cell = ""
        self._pending_section_title = ""  # h2 seen before current table
        self._cur_section = None          # currently open section

    def _open_section(self):
        self._cur_section = {
            "section_title": self._pending_section_title,
            "headers": [],
            "rows": []
        }
        self._pending_section_title = ""
        self.sections.append(self._cur_section)

    def handle_starttag(self, tag, attrs):
        if tag == "h1":
            self._in_h1 = True
        elif tag == "h2":
            self._in_h2 = True
        elif tag == "table":
            self._open_section()
        elif tag == "thead":
            self._in_thead = True
        elif tag == "tbody":
            self._in_tbody = True
        elif tag == "tr":
            self._current_row = []
        elif tag == "th":
            self._in_th = True
            self._current_cell = ""
        elif tag == "td":
            self._in_td = True
            self._current_cell = ""

    def handle_endtag(self, tag):
        if tag == "h1":
            self._in_h1 = False
        elif tag == "h2":
            self._in_h2 = False
        elif tag == "thead":
            self._in_thead = False
        elif tag == "tbody":
            self._in_tbody = False
        elif tag == "tr":
            if self._cur_section is None:
                return
            if self._in_thead and self._current_row:
                self._cur_section["headers"] = self._current_row[:]
            elif self._current_row:
                if not self._cur_section["headers"]:
                    # First row in table without explicit thead → use as header
                    self._cur_section["headers"] = self._current_row[:]
                else:
                    self._cur_section["rows"].append(self._current_row[:])
            self._current_row = []
        elif tag == "th":
            self._in_th = False
            self._current_row.append(self._current_cell.strip())
        elif tag == "td":
            self._in_td = False
            self._current_row.append(self._current_cell.strip())

    def handle_data(self, data):
        if self._in_h1:
            self.title += data
        elif self._in_h2:
            self._pending_section_title += data
        elif self._in_th:
            self._current_cell += data
        elif self._in_td:
            self._current_cell += data


def parse_html(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    parser = MultiTableParser()
    parser.feed(content)
    return parser.title.strip(), parser.sections


def make_row_dict(headers, row):
    d = {}
    for i, h in enumerate(headers):
        key = h if h else f"col_{i}"
        d[key] = row[i] if i < len(row) else ""
    return d


def build_json(table_id, title, sections):
    """单段 → 保持扁平结构；多段 → 嵌套 sections。"""
    if len(sections) == 1:
        s = sections[0]
        return {
            "table_info": {
                "id": table_id,
                "title": title,
                "columns": s["headers"],
                "row_count": len(s["rows"])
            },
            "rows": [make_row_dict(s["headers"], r) for r in s["rows"]]
        }
    else:
        return {
            "table_info": {
                "id": table_id,
                "title": title,
                "section_count": len(sections),
                "total_rows": sum(len(s["rows"]) for s in sections)
            },
            "sections": [
                {
                    "section_title": s["section_title"],
                    "columns": s["headers"],
                    "row_count": len(s["rows"]),
                    "rows": [make_row_dict(s["headers"], r) for r in s["rows"]]
                }
                for s in sections
            ]
        }


def write_csv(filepath, sections):
    """多段时加 section 列；单段时直接输出。"""
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        if len(sections) == 1:
            s = sections[0]
            clean_h = [h if h else f"col_{i}" for i, h in enumerate(s["headers"])]
            writer.writerow(clean_h)
            for row in s["rows"]:
                padded = list(row) + [""] * max(0, len(s["headers"]) - len(row))
                writer.writerow(padded[:len(s["headers"])])
        else:
            # Collect all unique columns across sections, add "分段" prefix column
            writer.writerow(["分段"] + ["内容"])  # simplified: one text column per row
            # Actually: use section-aware flat output
            # Re-open with proper multi-section layout
            pass

    # For multi-section: write a simpler section-aware CSV
    if len(sections) > 1:
        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            for s in sections:
                sec_title = s["section_title"] or "（无标题）"
                headers = s["headers"]
                clean_h = [h if h else f"col_{i}" for i, h in enumerate(headers)]
                # Section header row
                writer.writerow([f"## {sec_title}"])
                writer.writerow(clean_h)
                for row in s["rows"]:
                    padded = list(row) + [""] * max(0, len(headers) - len(row))
                    writer.writerow(padded[:len(headers)])
                writer.writerow([])  # blank separator


TABLE_FILES = [
    ("013", "013_三代世表_table.html"),
    ("014", "014_十二诸侯年表_table.html"),
    ("015", "015_六国年表_table.html"),
    ("016", "016_秦楚之际月表_table.html"),
    ("017", "017_汉兴以来诸侯王年表_table.html"),
    ("018", "018_高祖功臣侯者年表_table.html"),
    ("019", "019_惠景间侯者年表_table.html"),
    ("020", "020_建元以来侯者年表_table.html"),
    ("021", "021_建元已来王子侯者年表_table.html"),
    ("022", "022_汉兴以来将相名臣年表_table.html"),
]

HTML_DIR = os.path.join(os.path.dirname(__file__), "..", "resources", "table_html")
OUT_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(OUT_DIR, exist_ok=True)

for table_id, filename in TABLE_FILES:
    html_path = os.path.join(HTML_DIR, filename)
    base = filename.replace("_table.html", "")

    title, sections = parse_html(html_path)

    # JSON
    data = build_json(table_id, title, sections)
    json_path = os.path.join(OUT_DIR, f"{base}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # CSV
    csv_path = os.path.join(OUT_DIR, f"{base}.csv")
    write_csv(csv_path, sections)

    total_rows = sum(len(s["rows"]) for s in sections)
    if len(sections) > 1:
        sec_info = " | ".join(
            f"{s['section_title']}({len(s['rows'])}行×{len(s['headers'])}列)"
            for s in sections
        )
        print(f"✓ {base}: {len(sections)}段 共{total_rows}行 — {sec_info}")
    else:
        s = sections[0]
        print(f"✓ {base}: {total_rows} 行, {len(s['headers'])} 列")

print(f"\n完成！输出目录: {OUT_DIR}")
