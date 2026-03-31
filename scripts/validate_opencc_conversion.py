#!/usr/bin/env python3
"""
验证OpenCC转换效果
对已提取的10,028个繁简词对,用OpenCC验证转换是否正确
筛选出OpenCC转换失败或不正确的词条

这些词条就是需要补充到自定义词表的
"""

import json
from pathlib import Path
import subprocess

# 配置路径
PROJECT_ROOT = Path("/home/baojie/work/knowledge/shiji-kb")
INPUT_FILE = PROJECT_ROOT / "doc" / "analysis" / "word" / "04_s2t_variants_final.json"
OUTPUT_DIR = PROJECT_ROOT / "doc" / "analysis" / "word"

def opencc_convert_s2t(text: str) -> str:
    """使用系统OpenCC转换简体到繁体

    由于opencc命令不可用,使用Python的OpenCC库
    如果库不可用,使用基础字符映射
    """
    # 尝试导入OpenCC库
    try:
        import opencc
        converter = opencc.OpenCC('s2t')
        return converter.convert(text)
    except Exception as e:
        # 如果opencc库不可用或出错,返回None(表示无法验证)
        return None

def validate_conversion(simplified: str, expected_traditional: str) -> dict:
    """验证OpenCC转换是否正确

    返回:
        {
            "simplified": "汉王",
            "expected": "漢王",
            "opencc_result": "漢王",
            "match": True/False,
            "status": "correct"|"incorrect"|"opencc_unavailable"
        }
    """
    opencc_result = opencc_convert_s2t(simplified)

    if opencc_result is None:
        return {
            "simplified": simplified,
            "expected": expected_traditional,
            "opencc_result": None,
            "match": None,
            "status": "opencc_unavailable"
        }

    match = (opencc_result == expected_traditional)
    status = "correct" if match else "incorrect"

    return {
        "simplified": simplified,
        "expected": expected_traditional,
        "opencc_result": opencc_result,
        "match": match,
        "status": status
    }

def main():
    """主流程"""
    print("\n" + "=" * 60)
    print("OpenCC转换效果验证")
    print("=" * 60)

    # 加载词表
    print(f"\n加载词表: {INPUT_FILE.name}")
    if not INPUT_FILE.exists():
        print(f"❌ 文件不存在: {INPUT_FILE}")
        return

    variants = json.loads(INPUT_FILE.read_text(encoding='utf-8'))
    total_words = len(variants)
    print(f"✓ 已加载 {total_words:,} 个词条")

    # 检查OpenCC是否可用
    print("\n检查OpenCC...")
    test_result = opencc_convert_s2t("测试")
    if test_result is None:
        print("❌ OpenCC不可用,尝试安装opencc库:")
        print("   pip install opencc-python-reimplemented")

        # 尝试使用命令行OpenCC
        print("\n尝试使用命令行OpenCC...")
        try:
            result = subprocess.run(
                ['opencc', '-c', 's2t'],
                input='测试',
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=5
            )
            if result.returncode == 0:
                print(f"✓ 命令行OpenCC可用: '测试' → '{result.stdout.strip()}'")
                # 使用命令行版本
                use_cli = True
            else:
                print("❌ 命令行OpenCC也不可用")
                return
        except Exception as e:
            print(f"❌ 无法使用OpenCC: {e}")
            return
    else:
        print(f"✓ OpenCC库可用: '测试' → '{test_result}'")
        use_cli = False

    # 验证所有词条
    print(f"\n开始验证 {total_words:,} 个词条...")
    print("(这可能需要几分钟...)")

    results = []
    correct_count = 0
    incorrect_count = 0

    for idx, (simp, trad) in enumerate(variants.items(), 1):
        result = validate_conversion(simp, trad)
        results.append(result)

        if result['status'] == 'correct':
            correct_count += 1
        elif result['status'] == 'incorrect':
            incorrect_count += 1

        if idx % 2000 == 0:
            print(f"  已验证 {idx}/{total_words} ({idx*100//total_words}%)")

    print(f"\n验证完成!")
    print(f"  - 转换正确: {correct_count:,} 词 ({correct_count*100//total_words}%)")
    print(f"  - 转换错误: {incorrect_count:,} 词 ({incorrect_count*100//total_words}%) ⚠️")

    # 筛选出转换错误的词条
    incorrect_words = [r for r in results if r['status'] == 'incorrect']

    if incorrect_words:
        print(f"\n发现 {len(incorrect_words):,} 个OpenCC转换错误的词条!")
        print("这些词需要添加到自定义词表中\n")

        # 按频率排序(需要从原始数据中获取频率)
        print("前20个转换错误的词条:")
        for i, item in enumerate(incorrect_words[:20], 1):
            simp = item['simplified']
            exp = item['expected']
            got = item['opencc_result']
            print(f"  {i:2d}. {simp:12s} → 期望:{exp:12s} OpenCC:{got:12s} ❌")

    # 保存结果
    output_file = OUTPUT_DIR / "05_opencc_validation.json"
    output_data = {
        "total": total_words,
        "correct": correct_count,
        "incorrect": incorrect_count,
        "results": results
    }
    output_file.write_text(json.dumps(output_data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"\n✓ 完整结果已保存: {output_file}")

    # 保存需要补充的词条(仅错误的)
    if incorrect_words:
        output_incorrect = OUTPUT_DIR / "06_need_custom_variants.json"
        # 转换为OpenCC需要的格式
        custom_variants = {item['simplified']: item['expected'] for item in incorrect_words}
        output_incorrect.write_text(json.dumps(custom_variants, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"✓ 需补充词条已保存: {output_incorrect}")

        # 保存可读版本
        output_md = OUTPUT_DIR / "06_need_custom_variants.md"
        lines = ["# 需要补充到自定义词表的词条\n\n"]
        lines.append(f"**总数**: {len(incorrect_words):,}\n\n")
        lines.append("这些词条是OpenCC无法正确转换的,需要添加到自定义词表中。\n\n")
        lines.append("| 简体 | 期望繁体 | OpenCC结果 |\n")
        lines.append("|-----|---------|----------|\n")

        for item in incorrect_words:
            lines.append(f"| {item['simplified']} | {item['expected']} | {item['opencc_result']} |\n")

        output_md.write_text(''.join(lines), encoding='utf-8')
        print(f"✓ 需补充词条(可读版)已保存: {output_md}")
    else:
        print("\n✅ 所有词条的OpenCC转换都是正确的!")

    print("\n" + "=" * 60)
    print("✅ 验证完成!")
    print("=" * 60)

if __name__ == "__main__":
    main()
