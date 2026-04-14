import sys
import os
import glob

# 判断是否是"开引号"
def is_open_quote(prev_char):
    if prev_char is None:
        return True

    # 中文常见"引出内容"的前置字符
    opening_chars = set([
        ' ', '\n', '\t',
        '，', '。', '！', '？', '：', '；',
        '（', '【', '《'
    ])

    return prev_char in opening_chars


def convert_quotes(text):
    result = []
    stats = {
        'halfwidth_double': 0,  # 半角双引号 "
        'halfwidth_single': 0,  # 半角单引号 '
    }

    for i, ch in enumerate(text):
        prev_char = text[i - 1] if i > 0 else None

        if ch == '"':
            stats['halfwidth_double'] += 1
            if is_open_quote(prev_char):
                result.append('\u201c')  # 全角左双引号
            else:
                result.append('\u201d')  # 全角右双引号

        elif ch == "'":
            stats['halfwidth_single'] += 1
            if is_open_quote(prev_char):
                result.append('\u2018')  # 全角左单引号
            else:
                result.append('\u2019')  # 全角右单引号

        else:
            result.append(ch)

    return ''.join(result), stats


def find_chapter_file(chapter_input):
    """
    根据输入查找对应的章节文件
    支持：
    - 简写章节号（如 001, 096）
    - 完整文件名（如 096_张丞相列传.tagged.md）
    - 完整路径
    """
    # 如果是完整路径，直接返回
    if os.path.exists(chapter_input):
        return chapter_input

    # 如果输入是3位数字（如 001, 096）
    if chapter_input.isdigit() and len(chapter_input) == 3:
        pattern = f"chapter_md/{chapter_input}_*.tagged.md"
        matches = glob.glob(pattern)
        if matches:
            return matches[0]
        else:
            print(f"错误：未找到章节 {chapter_input} 对应的文件")
            return None

    # 如果输入是文件名（不含路径）
    if not '/' in chapter_input:
        # 尝试在 chapter_md/ 目录查找
        file_path = f"chapter_md/{chapter_input}"
        if os.path.exists(file_path):
            return file_path

    # 其他情况直接返回输入
    if os.path.exists(chapter_input):
        return chapter_input

    print(f"错误：未找到文件 {chapter_input}")
    return None


def main():
    if len(sys.argv) != 2:
        print("用法: python fix_quotes.py <章节号|文件名|文件路径>")
        print("")
        print("示例:")
        print("  python fix_quotes.py 001")
        print("  python fix_quotes.py 096")
        print("  python fix_quotes.py 096_张丞相列传.tagged.md")
        print("  python fix_quotes.py chapter_md/096_张丞相列传.tagged.md")
        return

    chapter_input = sys.argv[1]

    # 查找对应的文件
    file_path = find_chapter_file(chapter_input)
    if not file_path:
        return

    # 读取文件
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # 转换引号
    converted, stats = convert_quotes(text)

    # 显示统计信息
    total = stats['halfwidth_double'] + stats['halfwidth_single']
    if total == 0:
        print(f"✓ 文件 {file_path} 中没有需要转换的半角引号")
        return

    print(f"发现 {total} 个半角引号：")
    if stats['halfwidth_double'] > 0:
        print(f"  - 半角双引号 \": {stats['halfwidth_double']} 个")
    if stats['halfwidth_single'] > 0:
        print(f"  - 半角单引号 ': {stats['halfwidth_single']} 个")

    # 写回同一文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(converted)

    print(f"✓ 转换完成：{file_path}")


if __name__ == "__main__":
    main()