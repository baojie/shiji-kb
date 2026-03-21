#!/usr/bin/env python3
"""
通用分类树生成器 — 从 RDF/OWL Turtle 文件生成 Markdown 分类树

输入：*.ttl（OWL/RDF 本体文件）
输出：*_taxonomy.md（可读的层级分类树）

用法：
  python kg/taxonomy/scripts/build_taxonomy.py kg/taxonomy/person.ttl
  python kg/taxonomy/scripts/build_taxonomy.py kg/taxonomy/biology.ttl
  python kg/taxonomy/scripts/build_taxonomy.py kg/taxonomy/person.ttl -o kg/taxonomy/person_taxonomy.md
  python kg/taxonomy/scripts/build_taxonomy.py kg/taxonomy/person.ttl --unit 人
  python kg/taxonomy/scripts/build_taxonomy.py kg/taxonomy/person.ttl --max-show 30

TTL 本身是权威数据源，本脚本从中解析：
  - 类层次（owl:Class + rdfs:subClassOf）
  - 实例归类（a <class>）
  - 中文标签（rdfs:label "X"@zh）
  - 出现次数（:count N）

设计原则：
  - 不需要额外的 JSON 配置或分类数据
  - 与实体类型无关：人物/生物/地名/官职均可使用
  - 自动推断根类（没有 rdfs:subClassOf 的 owl:Class）
"""

import argparse
import sys
from collections import defaultdict
from pathlib import Path

try:
    from rdflib import Graph, URIRef, Literal, Namespace
    from rdflib.namespace import RDF, RDFS, OWL, XSD
except ImportError:
    print('错误: 需要 rdflib。请运行: pip install rdflib')
    sys.exit(1)

SHIJI = Namespace('http://memect.cn/baojie/ontologies/2025/1/shiji/')
MAX_SHOW = 20


# ════════════════════════════════════════════
# TTL 解析
# ════════════════════════════════════════════

def parse_ttl(ttl_path: Path) -> dict:
    """解析 TTL 文件，提取类层次和实例信息。

    返回:
        {
            'classes': {uri: {'label': str, 'parent': uri_or_None}},
            'instances': {uri: {'label': str, 'count': int, 'types': [uri]}},
            'root_class': uri,
        }
    """
    g = Graph()
    g.parse(str(ttl_path), format='turtle')

    COUNT = SHIJI['count']

    # 收集所有 owl:Class
    classes = {}
    for cls_uri in g.subjects(RDF.type, OWL.Class):
        label = _get_zh_label(g, cls_uri)
        parent = None
        for p in g.objects(cls_uri, RDFS.subClassOf):
            parent = p
            break
        classes[cls_uri] = {'label': label, 'parent': parent}

    # 找根类（没有 parent 或 parent 不在 classes 中的）
    roots = [u for u, info in classes.items()
             if info['parent'] is None or info['parent'] not in classes]

    # 如果有多个根，取实例最多的那个（通常就一个）
    root_class = roots[0] if roots else None

    # 收集实例（有 :count 属性的非 Class 实体）
    instances = {}
    for inst_uri in g.subjects(COUNT, None):
        if inst_uri in classes:
            continue  # 跳过类本身
        label = _get_zh_label(g, inst_uri)
        count = 0
        for c in g.objects(inst_uri, COUNT):
            count = int(c)
            break
        types = [t for t in g.objects(inst_uri, RDF.type) if t in classes]
        instances[inst_uri] = {'label': label, 'count': count, 'types': types}

    return {
        'classes': classes,
        'instances': instances,
        'root_class': root_class,
    }


def _get_zh_label(g, uri):
    """获取中文标签，fallback 到任意标签或 URI 末段。"""
    for label in g.objects(uri, RDFS.label):
        if hasattr(label, 'language') and label.language == 'zh':
            return str(label)
    # fallback: 任意标签
    for label in g.objects(uri, RDFS.label):
        return str(label)
    # fallback: URI 末段
    s = str(uri)
    return s.rsplit('/', 1)[-1].rsplit('#', 1)[-1]


# ════════════════════════════════════════════
# 树结构构建
# ════════════════════════════════════════════

class TreeNode:
    """分类树节点。"""
    __slots__ = ('uri', 'label', 'children', 'instances', 'total_instances')

    def __init__(self, uri, label: str):
        self.uri = uri
        self.label = label
        self.children: list['TreeNode'] = []
        self.instances: list[tuple[str, int]] = []  # [(label, count), ...]
        self.total_instances = 0


def build_class_tree(parsed: dict, order: list[str] = None) -> TreeNode:
    """从解析结果构建完整的类树。

    Args:
        parsed: parse_ttl() 的返回值
        order: 根类直接子类的显示顺序（中文标签列表），未列出的排到最后
    """
    classes = parsed['classes']
    instances = parsed['instances']
    root_uri = parsed['root_class']

    # 创建所有节点
    nodes = {}
    for uri, info in classes.items():
        nodes[uri] = TreeNode(uri, info['label'])

    # 建立父子关系
    for uri, info in classes.items():
        parent = info['parent']
        if parent and parent in nodes and parent != uri:
            nodes[parent].children.append(nodes[uri])

    # 将实例挂到最具体的类上
    for inst_uri, info in instances.items():
        types = info['types']
        if not types:
            continue
        # 选最具体的类型（在类树中层级最深的）
        best_type = _most_specific_class(types, classes)
        if best_type in nodes:
            nodes[best_type].instances.append((info['label'], info['count']))

    root = nodes.get(root_uri)
    if root is None:
        # 创建虚拟根
        root = TreeNode(None, '根')
        for uri, info in classes.items():
            if info['parent'] is None or info['parent'] not in classes:
                root.children.append(nodes[uri])

    # 排序
    _sort_tree(root)
    # 计数
    _count_tree(root)

    # 应用自定义顺序到根的直接子节点
    if order:
        label_to_rank = {label: i for i, label in enumerate(order)}
        fallback = len(order)
        root.children.sort(key=lambda c: label_to_rank.get(c.label, fallback))

    return root


def _most_specific_class(type_uris: list, classes: dict):
    """在多个类型中选最具体的（树中最深的）。"""
    if len(type_uris) == 1:
        return type_uris[0]

    # 计算每个类的深度
    def depth(uri):
        d = 0
        cur = uri
        seen = set()
        while cur in classes and cur not in seen:
            seen.add(cur)
            parent = classes[cur]['parent']
            if parent and parent in classes:
                d += 1
                cur = parent
            else:
                break
        return d

    return max(type_uris, key=depth)


def _sort_tree(node: TreeNode):
    """递归排序：子节点按总实例数降序，实例按 count 降序。"""
    node.instances.sort(key=lambda x: -x[1])
    for child in node.children:
        _sort_tree(child)


def _count_tree(node: TreeNode) -> int:
    """递归计算每个节点的总实例数（含子节点）。"""
    total = len(node.instances)
    for child in node.children:
        total += _count_tree(child)
    node.total_instances = total
    # 排序子节点（需要在计数后排序）
    node.children.sort(key=lambda c: -c.total_instances)
    return total


# ════════════════════════════════════════════
# Markdown 分类树渲染
# ════════════════════════════════════════════

def render_tree(root: TreeNode, unit: str, max_show: int) -> str:
    """渲染完整的 Markdown 分类树。"""
    lines = [
        f'# 史记{root.label}分类树',
        '',
        f'> {root.total_instances} {unit}{root.label}，'
        f'来源：RDF 本体',
        '',
        '## 详细分类树',
        '',
        '```',
        f'{root.label}  [{root.total_instances}{unit}]',
    ]

    # 渲染子节点
    for ci, child in enumerate(root.children):
        is_last = (ci == len(root.children) - 1)
        _render_node(child, '', is_last, unit, max_show, lines)

    # 渲染根的直接实例
    if root.instances:
        _render_instances(root.instances, '', unit, max_show, lines,
                          has_siblings=False)

    lines.append('```')
    return '\n'.join(lines)


def _render_node(node: TreeNode, prefix: str, is_last: bool,
                 unit: str, max_show: int, lines: list[str]):
    """递归渲染一个节点及其子树。"""
    conn = '└── ' if is_last else '├── '
    lines.append(f'{prefix}{conn}{node.label}  [{node.total_instances}{unit}]')
    child_prefix = prefix + ('    ' if is_last else '│   ')

    # 子类节点
    direct = node.instances
    has_direct = len(direct) > 0

    for ci, child in enumerate(node.children):
        child_is_last = (ci == len(node.children) - 1) and not has_direct
        _render_node(child, child_prefix, child_is_last, unit, max_show, lines)

    # 本级实例
    if has_direct:
        if node.children:
            # 有子类时，本级实例标记为"(本级)"
            lines.append(f'{child_prefix}└── (本级)  [{len(direct)}{unit}]')
            inst_prefix = child_prefix + '    '
        else:
            inst_prefix = child_prefix

        _render_instances(direct, inst_prefix, unit, max_show, lines,
                          has_siblings=False)


def _render_instances(instances: list[tuple[str, int]], prefix: str,
                      unit: str, max_show: int, lines: list[str],
                      has_siblings: bool):
    """渲染实例列表。"""
    show = min(len(instances), max_show)
    for i, (name, count) in enumerate(instances[:show]):
        is_last_inst = (i == show - 1) and len(instances) <= show
        conn = '└── ' if is_last_inst else '├── '
        lines.append(f'{prefix}{conn}{name} ({count})')
    if len(instances) > show:
        lines.append(f'{prefix}└── ……其余{len(instances) - show}{unit}')


# ════════════════════════════════════════════
# 主流程
# ════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description='从 RDF/OWL Turtle 文件生成 Markdown 分类树')
    parser.add_argument('ttl', help='输入 TTL 文件路径')
    parser.add_argument('-o', '--output', help='输出 MD 文件路径（默认：同名_taxonomy.md）')
    parser.add_argument('--unit', default=None,
                        help='计数单位（人/种/条），默认自动推断')
    parser.add_argument('--max-show', type=int, default=MAX_SHOW,
                        help=f'每个叶子类最多显示的实例数（默认 {MAX_SHOW}）')
    parser.add_argument('--order',
                        help='根子类显示顺序（逗号分隔的中文标签），'
                             '如 "王室,臣,策士,诸子百家,社会人物,方术,外邦,虚构人物,疑似误标"')

    args = parser.parse_args()

    ttl_path = Path(args.ttl)
    if not ttl_path.exists():
        print(f'错误: 文件不存在: {ttl_path}')
        sys.exit(1)

    # 默认输出路径
    if args.output:
        out_path = Path(args.output)
    else:
        out_path = ttl_path.with_name(ttl_path.stem + '_taxonomy.md')

    # 解析 TTL
    print(f'解析: {ttl_path}')
    parsed = parse_ttl(ttl_path)

    n_classes = len(parsed['classes'])
    n_instances = len(parsed['instances'])
    print(f'  {n_classes} 类, {n_instances} 实例')

    # 自动推断单位
    unit = args.unit
    if unit is None:
        root_label = parsed['classes'].get(parsed['root_class'], {}).get('label', '')
        unit_map = {'人物': '人', '生物': '种'}
        unit = unit_map.get(root_label, '个')

    # 解析排序
    order = args.order.split(',') if args.order else None

    # 构建树
    root = build_class_tree(parsed, order=order)

    # 渲染
    md_content = render_tree(root, unit, args.max_show)
    out_path.write_text(md_content, encoding='utf-8')
    print(f'输出: {out_path} ({md_content.count(chr(10)) + 1} 行)')


if __name__ == '__main__':
    main()
