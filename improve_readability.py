#!/usr/bin/env python3
"""
改进史记章节文件的可读性
1. 在段落之间插入空行
2. 检测并修复可能的误分段
"""

import os
import re

def is_sentence_ending(line):
    """
    检测行末是否有句子结束符号
    
    参数:
        line: 要检测的文本行
    
    返回:
        bool: 如果行末有句子结束符号返回True,否则返回False
    
    逻辑说明:
        - 空行被视为已结束(返回True)
        - 检测常见的中文句子结束符号:
          。(句号) ！(感叹号) ？(问号) 
          」(右引号) 』(右书名号) 
          ：(冒号) ；(分号) …(省略号)
    """
    line = line.rstrip('\r\n ')
    if not line:
        return True
    
    # 中文句子结束符号列表
    ending_marks = ['。', '！', '？', '」', '』', '：', '；', '…']
    return any(line.endswith(mark) for mark in ending_marks)

def should_merge_with_next(line, next_line):
    """
    判断当前行是否应该与下一行合并
    
    参数:
        line: 当前行
        next_line: 下一行
    
    返回:
        bool: 如果应该合并返回True,否则返回False
    
    合并逻辑说明:
        误分段的典型特征是行末没有句子结束符号,这通常意味着
        句子在下一行继续。本函数通过以下规则判断是否合并:
        
        1. 如果当前行以句子结束符号结尾 → 不合并
           (说明这是一个完整的句子,不应该与下一行合并)
        
        2. 如果当前行或下一行为空 → 不合并
           (空行应该保留,用于段落分隔)
        
        3. 如果当前行很短(少于10个字符) → 不合并
           (可能是标题、小节标记等特殊格式,应该独立成行)
        
        4. 其他情况 → 合并
           (当前行末没有结束符号,且不属于特殊情况,
            很可能是误分段,应该与下一行合并成完整段落)
    
    示例:
        原文:
          於是九州攸同，四奥既居，九山
          旅，九川涤原，九泽既陂...
        
        检测: 第一行末尾没有句子结束符号 → 应该合并
        
        合并后:
          於是九州攸同，四奥既居，九山旅，九川涤原，九泽既陂...
    """
    if not line or not next_line:
        return False
    
    line = line.rstrip('\r\n ')
    next_line = next_line.strip('\r\n ')
    
    # 规则1: 如果当前行以句子结束符号结尾,不合并
    if is_sentence_ending(line):
        return False
    
    # 规则2: 如果当前行为空,不合并
    if not line:
        return False
    
    # 规则2: 如果下一行为空,不合并
    if not next_line:
        return False
    
    # 规则3: 如果当前行很短(可能是标题或特殊格式),不合并
    if len(line) < 10:
        return False
    
    # 规则4: 其他情况,判定为误分段,应该合并
    return True

def improve_file(input_path, output_path):
    """改进单个文件的可读性"""
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    if not lines:
        return
    
    improved_lines = []
    i = 0
    
    while i < len(lines):
        current_line = lines[i].rstrip('\r\n')
        
        # 跳过空行
        if not current_line:
            i += 1
            continue
        
        # 第一行是标题,单独处理
        if i == 0:
            improved_lines.append(current_line + '\n')
            improved_lines.append('\n')  # 标题后加空行
            i += 1
            continue
        
        # 检查是否需要与下一行合并
        merged_line = current_line
        j = i + 1
        
        while j < len(lines):
            next_line = lines[j].rstrip('\r\n')
            
            # 跳过空行
            if not next_line:
                j += 1
                continue
            
            # 判断是否应该合并
            if should_merge_with_next(merged_line, next_line):
                merged_line += next_line
                j += 1
            else:
                break
        
        # 添加合并后的行
        improved_lines.append(merged_line + '\n')
        improved_lines.append('\n')  # 段落后加空行
        
        i = j
    
    # 移除末尾多余的空行
    while improved_lines and improved_lines[-1].strip() == '':
        improved_lines.pop()
    
    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(improved_lines)

def process_directory(input_dir, output_dir):
    """处理整个目录"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    files = sorted([f for f in os.listdir(input_dir) if f.endswith('.txt')])
    
    print(f"开始处理 {len(files)} 个文件...")
    
    for filename in files:
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)
        
        try:
            improve_file(input_path, output_path)
            print(f"✓ 已处理: {filename}")
        except Exception as e:
            print(f"✗ 处理失败 {filename}: {e}")
    
    print(f"\n完成! 改进后的文件保存在: {output_dir}")

if __name__ == "__main__":
    input_directory = "/home/baojie/work/shiji-kb/chapter"
    output_directory = "/home/baojie/work/shiji-kb/chapter_improved"
    
    process_directory(input_directory, output_directory)
