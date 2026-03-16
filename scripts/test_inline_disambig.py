#!/usr/bin/env python3
"""测试内联消歧语法 〖TYPE 显示|规范名〗 的正确处理。

测试覆盖：
1. lint_text_integrity.py::strip_markup() — 脱标完整性
2. validate_tagging.py::remove_all_tags() — 脱标完整性
3. render_shiji_html.py::convert_entities() — HTML渲染（data-canonical）
"""

import sys
import os
import re

# 路径设置
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, 'kg', 'entities', 'scripts'))

# ─────────────────────────────────────────────
# 测试用例：每种类型各一条带 | 的标注
# ─────────────────────────────────────────────
TEST_INPUT = (
    '〖@台|吕台〗见〖=沛|沛县〗，〖;守|郡守〗位，〖\'汉|大汉〗兴，'
    '〖&芈|芈姓〗族，〖^郡县|郡县制〗，〖~胡|匈奴〗犯，〖#外戚|外戚家族〗，'
    '〖%元|元年〗始，〖•鼎|九鼎〗铸，〖!彗|彗星〗现，〖+龙|蟠龙〗纹，〖$千|千金〗赏。'
)

EXPECTED_STRIPPED = '台见沛，守位，汉兴，芈族，郡县，胡犯，外戚，元始，鼎铸，彗现，龙纹，千赏。'

# 不带 | 的标注（回归：原有行为不变）
TEST_INPUT_NO_DISAMBIG = (
    '〖@项羽〗战〖=垓下〗，〖;楚王〗败，〖\'楚〗亡。'
)
EXPECTED_NO_DISAMBIG = '项羽战垓下，楚王败，楚亡。'


# ─────────────────────────────────────────────
# 测试 1：lint_text_integrity.py::strip_markup
# ─────────────────────────────────────────────
def test_strip_markup():
    from lint_text_integrity import strip_markup

    result = strip_markup(TEST_INPUT)
    assert result == EXPECTED_STRIPPED, (
        f'[FAIL] strip_markup 带| 期望:\n  {EXPECTED_STRIPPED!r}\n实际:\n  {result!r}'
    )
    print('[PASS] strip_markup: 带|消歧正确')

    result2 = strip_markup(TEST_INPUT_NO_DISAMBIG)
    assert result2 == EXPECTED_NO_DISAMBIG, (
        f'[FAIL] strip_markup 无| 期望:\n  {EXPECTED_NO_DISAMBIG!r}\n实际:\n  {result2!r}'
    )
    print('[PASS] strip_markup: 无|回归正确')


# ─────────────────────────────────────────────
# 测试 2：validate_tagging.py::remove_all_tags
# ─────────────────────────────────────────────
def test_remove_all_tags():
    from validate_tagging import remove_all_tags

    result = remove_all_tags(TEST_INPUT)
    assert result == EXPECTED_STRIPPED, (
        f'[FAIL] remove_all_tags 带| 期望:\n  {EXPECTED_STRIPPED!r}\n实际:\n  {result!r}'
    )
    print('[PASS] remove_all_tags: 带|消歧正确')

    result2 = remove_all_tags(TEST_INPUT_NO_DISAMBIG)
    assert result2 == EXPECTED_NO_DISAMBIG, (
        f'[FAIL] remove_all_tags 无| 期望:\n  {EXPECTED_NO_DISAMBIG!r}\n实际:\n  {result2!r}'
    )
    print('[PASS] remove_all_tags: 无|回归正确')


# ─────────────────────────────────────────────
# 测试 3：render_shiji_html.py::convert_entities
# ─────────────────────────────────────────────
def test_convert_entities():
    from render_shiji_html import convert_entities

    # 每种类型各一个消歧标注
    cases = [
        ('〖@台|吕台〗',     'person',       '吕台'),
        ('〖=沛|沛县〗',     'place',        '沛县'),
        ('〖;守|郡守〗',     'official',     '郡守'),
        ("〖'汉|大汉〗",     'feudal-state', '大汉'),
        ('〖&芈|芈姓〗',     'dynasty',      '芈姓'),
        ('〖^郡县|郡县制〗', 'institution',  '郡县制'),
        ('〖~胡|匈奴〗',     'tribe',        '匈奴'),
        ('〖#外戚|外戚家族〗','identity',    '外戚家族'),
        ('〖%元|元年〗',     'time',         '元年'),
        ('〖•鼎|九鼎〗',     'artifact',     '九鼎'),
        ('〖!彗|彗星〗',     'astronomy',    '彗星'),
        ('〖+龙|蟠龙〗',     'biology',      '蟠龙'),
        ('〖$千|千金〗',     'quantity',     '千金'),
    ]

    for markup, css_class, canonical in cases:
        html = convert_entities(markup)
        assert f'class="{css_class}"' in html, (
            f'[FAIL] {markup} 期望 class="{css_class}", 实际: {html}'
        )
        assert f'data-canonical="{canonical}"' in html, (
            f'[FAIL] {markup} 期望 data-canonical="{canonical}", 实际: {html}'
        )
        print(f'[PASS] convert_entities: {markup} → class={css_class}, canonical={canonical}')

    # 无|的标注回归
    html_plain = convert_entities('〖@项羽〗')
    assert 'class="person"' in html_plain, f'[FAIL] 无|人名未渲染: {html_plain}'
    assert 'data-canonical' not in html_plain, f'[FAIL] 无|人名不应含data-canonical: {html_plain}'
    print('[PASS] convert_entities: 无|人名回归正确')


# ─────────────────────────────────────────────
# 主入口
# ─────────────────────────────────────────────
if __name__ == '__main__':
    errors = []

    for fn in [test_strip_markup, test_remove_all_tags, test_convert_entities]:
        try:
            fn()
        except AssertionError as e:
            errors.append(str(e))
            print(str(e))
        except Exception as e:
            errors.append(f'[ERROR] {fn.__name__}: {e}')
            print(f'[ERROR] {fn.__name__}: {e}')

    print()
    if errors:
        print(f'FAILED: {len(errors)} 项测试未通过')
        sys.exit(1)
    else:
        print('ALL PASSED')
