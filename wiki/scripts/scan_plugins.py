#!/usr/bin/env python3
"""
scan_plugins.py — 扫描 wiki/public/plugins/ 目录，生成 plugins.json.

每个子目录若包含 plugin.json + index.js，则视为合法插件。
输出格式:
  {
    "plugins": [
      {
        "id": "math",
        "entry": "plugins/math/index.js",
        "name": "...",
        "version": "...",
        "description": "...",
        "settings_key": "..."   (可选)
      },
      ...
    ]
  }

用法:
  python wiki/scripts/scan_plugins.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # wiki/
PLUGINS_DIR = ROOT / "public" / "plugins"
OUTPUT = ROOT / "public" / "plugins.json"


def scan() -> list[dict]:
    plugins = []
    if not PLUGINS_DIR.exists():
        return plugins
    dirs = sorted(PLUGINS_DIR.iterdir(), key=lambda d: (
        json.loads((d / "plugin.json").read_text(encoding="utf-8")).get("load_order", 50)
        if (d / "plugin.json").exists() else 50, d.name
    ))
    for sub in dirs:
        if not sub.is_dir():
            continue
        meta_file = sub / "plugin.json"
        entry_file = sub / "index.js"
        if not meta_file.exists() or not entry_file.exists():
            continue
        try:
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[warn] {sub.name}/plugin.json parse error: {e}", file=sys.stderr)
            continue
        plugin = {
            "id": sub.name,
            "entry": f"plugins/{sub.name}/index.js",
            "name": meta.get("name", sub.name),
            "version": meta.get("version", "?"),
            "description": meta.get("description", ""),
        }
        if "settings_key" in meta:
            plugin["settings_key"] = meta["settings_key"]
        plugins.append(plugin)
        print(f"[plugin] {plugin['id']} v{plugin['version']} → {plugin['entry']}")
    return plugins


def main() -> int:
    plugins = scan()
    out = {"plugins": plugins}
    OUTPUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[ok] {len(plugins)} plugin(s) → {OUTPUT.relative_to(ROOT.parent)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
