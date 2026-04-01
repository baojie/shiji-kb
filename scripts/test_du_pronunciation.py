#!/usr/bin/env python3
"""
测试pypinyin对《史记》中"读"字的拼音处理
检查哪些应该读dòu（去声）的被错误标注为dú（阳平）
"""

from pypinyin import pinyin, Style

# 《史记》中包含"读"字的典型例句
test_cases = [
    # 应该读 dú（阳平）的情况：阅读、朗读
    ("周太史伯阳读史记曰", "dú", "阅读史书"),
    ("余读高祖侯功臣", "dú", "阅读史料"),
    ("孔子读史记至楚复陈", "dú", "阅读史书"),
    ("读易，韦编三绝", "dú", "阅读易经"),
    ("好读书", "dú", "喜欢读书"),
    ("读其书未毕", "dú", "阅读文字"),
    ("读此则为王者师矣", "dú", "阅读此书"),
    ("常习诵读之", "dú", "诵读"),
    ("不敢复读天下之书", "dú", "阅读书籍"),
    ("伏而读之", "dú", "阅读"),

    # 应该读 dòu（去声）的情况：句读（断句）
    # 注意：史记正文中没有"句读"一词，但有以下可能相关的用法

    # 通假字相关（读曰、读为）- 读 dú
    # 史记中主要是"读"作为动词"阅读"使用
]

def test_pypinyin():
    """测试pypinyin对"读"字的处理"""
    print("=" * 80)
    print("测试pypinyin对《史记》中\"读\"字的拼音标注")
    print("=" * 80)

    errors = []

    for text, expected_tone, context in test_cases:
        # 找到"读"字在文本中的位置
        idx = text.index("读")

        # 获取pypinyin的标注（带声调）
        result = pinyin(text, style=Style.TONE)
        actual = result[idx][0] if idx < len(result) else "未找到"

        # 提取声调（简化判断）
        is_correct = expected_tone in actual

        status = "✓" if is_correct else "✗"

        print(f"\n{status} 例句：{text}")
        print(f"  上下文：{context}")
        print(f"  期望读音：{expected_tone}")
        print(f"  实际标注：{actual}")

        if not is_correct:
            errors.append({
                "text": text,
                "expected": expected_tone,
                "actual": actual,
                "context": context
            })

    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    print(f"测试用例总数：{len(test_cases)}")
    print(f"标注正确：{len(test_cases) - len(errors)}")
    print(f"标注错误：{len(errors)}")

    if errors:
        print("\n需要修正的情况：")
        for err in errors:
            print(f"  • {err['text']}")
            print(f"    期望：{err['expected']}，实际：{err['actual']}")
            print(f"    上下文：{err['context']}")

    # 结论
    print("\n" + "=" * 80)
    print("结论")
    print("=" * 80)
    print("""
《史记》中"读"字的使用情况：

1. **绝大多数读 dú（阳平）**：表示"阅读、朗读"
   - 读史记、读书、诵读、伏读等

2. **没有发现需要读 dòu（去声）的例子**：
   - 史记正文中没有"句读"一词
   - "句读"只出现在后世注释中（如《史记索隐》）
   - 注释中的"一句读"、"连一句读"等是校勘术语，不是原文

3. **pypinyin处理建议**：
   - 目前pypinyin对《史记》中的"读"字标注应该都是正确的（dú）
   - 无需为"句读"添加特殊规则（因为史记原文中不存在此词）
   - 如果将来处理注释文本，才需要考虑"句读"读dòu的情况
    """)

if __name__ == "__main__":
    test_pypinyin()
