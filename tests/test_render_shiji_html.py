#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render_shiji_html.py 的回归测试
确保重构不破坏现有功能
"""

import sys
import re
from pathlib import Path

# 添加父目录到路径以导入被测模块
sys.path.insert(0, str(Path(__file__).parent.parent))

import render_shiji_html as rsh


def test_entity_conversion():
    """测试实体标注转换为HTML"""
    test_cases = [
        # 人名
        ('〖@秦始皇〗', 'class="person"', '秦始皇</span>'),
        # 人名消歧
        ('〖@台|吕台〗', 'class="person"', 'data-canonical="吕台"', '>台</span>'),
        # 地名
        ('〖=咸阳〗', 'class="place"', '咸阳</span>'),
        # 官职
        ('〖;丞相〗', 'class="official"', '丞相</span>'),
        # 时间
        ('〖%元年〗', 'class="time"', '元年</span>'),
        # 氏族
        ('〖&嬴氏〗', 'class="dynasty"', '嬴氏</span>'),
        # 邦国
        ('〖◆秦〗', 'class="feudal-state"', '秦</span>'),
        # 军事动词
        ('⟦◈攻⟧', 'class="verb-military"', '攻</span>'),
        # 刑罚动词
        ('⟦◉斩⟧', 'class="verb-penalty"', '斩</span>'),
    ]

    for test_case in test_cases:
        input_text = test_case[0]
        expected_patterns = test_case[1:]
        result = rsh.convert_entities(input_text)
        # 移除链接包装，只检查span部分
        result_without_links = re.sub(r'<a [^>]+>|</a>', '', result)

        for pattern in expected_patterns:
            if pattern not in result_without_links:
                print(f"❌ 失败: {input_text}")
                print(f"   期望包含: {pattern}")
                print(f"   实际结果: {result_without_links}")
                return False

    print("✓ 实体转换测试通过")
    return True


def test_quote_patterns():
    """测试引号转换"""
    test_cases = [
        ('"你好"', '<span class="quoted">"你好"</span>'),
        ('"hello"', '<span class="quoted">"hello"</span>'),
        ('「注释」', '<span class="quoted">「注释」</span>'),
    ]

    for input_text, expected_pattern in test_cases:
        result = rsh.convert_entities(input_text)
        if expected_pattern not in result:
            print(f"❌ 失败: {input_text}")
            print(f"   期望: {expected_pattern}")
            print(f"   实际: {result}")
            return False

    print("✓ 引号转换测试通过")
    return True


def test_paragraph_numbers():
    """测试段落编号转换"""
    test_cases = [
        ('[1]', 'id="pn-1"'),
        ('[2.3]', 'id="pn-2.3"'),
        ('[10.5.2]', 'id="pn-10.5.2"'),
    ]

    for input_text, expected_pattern in test_cases:
        result = rsh.convert_entities(input_text)
        if expected_pattern not in result:
            print(f"❌ 失败: {input_text}")
            print(f"   期望包含: {expected_pattern}")
            print(f"   实际: {result}")
            return False

    print("✓ 段落编号测试通过")
    return True


def test_heading_id_generation():
    """测试标题ID生成"""
    import urllib.parse

    test_cases = [
        ('〖@秦始皇〗本纪', '秦始皇本纪'),  # 应去除标注符号
        ('第一章', '第一章'),
        # 消歧格式保留规范名（管道符后面的）
        ('〖=咸阳|咸阳城〗之战', '咸阳城之战'),
    ]

    for input_text, expected_clean in test_cases:
        result = rsh.generate_heading_id(input_text)
        # URL解码以便比较
        decoded = urllib.parse.unquote(result)
        if decoded != expected_clean:
            print(f"❌ 失败: {input_text}")
            print(f"   期望: {expected_clean}")
            print(f"   实际: {decoded}")
            return False

    print("✓ 标题ID生成测试通过")
    return True


def test_complex_text():
    """测试复杂文本（混合多种标注）"""
    input_text = '〖@秦始皇〗在〖=咸阳〗即位，〖;丞相〗⟦◈攻⟧〖◆楚〗。"大喜"'
    result = rsh.convert_entities(input_text)

    # 检查关键元素是否都存在
    checks = [
        'class="person"',
        'class="place"',
        'class="official"',
        'class="verb-military"',
        'class="feudal-state"',
        'class="quoted"',
    ]

    for check in checks:
        if check not in result:
            print(f"❌ 复杂文本测试失败，缺少: {check}")
            print(f"   结果: {result}")
            return False

    print("✓ 复杂文本测试通过")
    return True


def test_actual_file_rendering():
    """测试实际文件渲染（如果存在测试文件）"""
    test_file = Path('chapter_md/004_周本纪.tagged.md')
    if not test_file.exists():
        print("⊘ 跳过文件渲染测试（测试文件不存在）")
        return True

    output_file = Path('/tmp/test_render_output.html')
    try:
        result = rsh.markdown_to_html(
            str(test_file),
            str(output_file),
            css_file='docs/css/shiji-styles.css'
        )

        if not output_file.exists():
            print("❌ 文件渲染测试失败：输出文件未生成")
            return False

        # 检查输出文件基本结构
        content = output_file.read_text(encoding='utf-8')
        checks = [
            '<!DOCTYPE html>',
            '<html lang="zh-CN">',
            '<body>',
            '</body>',
            '</html>',
        ]

        for check in checks:
            if check not in content:
                print(f"❌ 文件渲染测试失败，缺少: {check}")
                return False

        print("✓ 文件渲染测试通过")
        return True

    except Exception as e:
        print(f"❌ 文件渲染测试异常: {e}")
        return False
    finally:
        # 清理测试文件
        if output_file.exists():
            output_file.unlink()


def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("运行 render_shiji_html.py 回归测试")
    print("=" * 50)

    tests = [
        test_entity_conversion,
        test_quote_patterns,
        test_paragraph_numbers,
        test_heading_id_generation,
        test_complex_text,
        test_actual_file_rendering,
    ]

    results = []
    for test in tests:
        print(f"\n运行: {test.__name__}")
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"测试结果: {passed}/{total} 通过")
    print("=" * 50)

    return all(results)


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
