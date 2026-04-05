import sys

# 判断是否是“开引号”
def is_open_quote(prev_char):
    if prev_char is None:
        return True

    # 中文常见“引出内容”的前置字符
    opening_chars = set([
        ' ', '\n', '\t',
        '，', '。', '！', '？', '：', '；',
        '（', '【', '《'
    ])

    return prev_char in opening_chars


def convert_quotes(text):
    result = []

    for i, ch in enumerate(text):
        prev_char = text[i - 1] if i > 0 else None

        if ch == '"':
            if is_open_quote(prev_char):
                result.append('“')
            else:
                result.append('”')

        elif ch == "'":
            if is_open_quote(prev_char):
                result.append('‘')
            else:
                result.append('’')

        else:
            result.append(ch)

    return ''.join(result)


def main():
    if len(sys.argv) != 3:
        print("用法: python script.py 输入文件 输出文件")
        return

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()

    converted = convert_quotes(text)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(converted)

    print("转换完成！")


if __name__ == "__main__":
    main()