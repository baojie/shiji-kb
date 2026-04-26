#!/usr/bin/env python3
"""
扫描 wiki/public/plugins/*/plugin.json，生成 wiki/public/plugins.json。

用法:
    python3 wiki/scripts/build_plugins.py [--site-root wiki/public]

约定：此脚本由 .git/hooks/pre-commit 在每次 git commit 前自动调用，
无需手动执行。添加新插件时只需创建 plugins/<name>/plugin.json。
"""

from __future__ import annotations
import argparse, json, sys
from pathlib import Path


def build(site_root: Path) -> list[dict]:
    entries = []
    for plugin_json in sorted((site_root / 'plugins').glob('*/plugin.json')):
        plugin_dir = plugin_json.parent
        try:
            meta = json.loads(plugin_json.read_text(encoding='utf-8'))
        except Exception as e:
            print(f'[warn] {plugin_dir.name}/plugin.json 解析失败: {e}', file=sys.stderr)
            continue
        plugin_id = meta.get('id') or plugin_dir.name
        entry_file = meta.get('entry', 'index.js')
        if not (plugin_dir / entry_file).exists():
            print(f'[warn] entry 不存在，跳过: {plugin_id}/{entry_file}', file=sys.stderr)
            continue
        entries.append({
            'id':          plugin_id,
            'entry':       f'plugins/{plugin_dir.name}/{entry_file}',
            'name':        meta.get('name', plugin_id),
            'version':     meta.get('version', '0.0.0'),
            'description': meta.get('description', ''),
            '_order':      meta.get('load_order', 50),
        })
    entries.sort(key=lambda e: (e['_order'], e['id']))
    return [{k: v for k, v in e.items() if k != '_order'} for e in entries]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--site-root', default='wiki/public')
    args = ap.parse_args()

    site_root = Path(args.site_root).resolve()
    plugins = build(site_root)
    out = site_root / 'plugins.json'
    out.write_text(json.dumps({'plugins': plugins}, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')
    print(f'[plugins] {len(plugins)} 个插件 → {out.relative_to(Path.cwd())}')
    for p in plugins:
        print(f'  {p["id"]}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
