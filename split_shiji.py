import os
import re

def split_shiji(input_file, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Define chapter headers based on observation
    # Chapters usually followed by "本纪", "表", "书", "世家", "列传"
    # And there are section headers like "十二本纪", "十表", etc.
    
    sections = {
        "本纪": 12,
        "表": 10,
        "书": 8,
        "世家": 30,
        "列传": 70
    }
    
    # Titles we found in the file:
    # 12: 五帝本纪, 夏本纪, 殷本纪, 周本纪, 秦本纪, 秦始皇本纪, 项羽本纪, 高祖本纪, 吕太后本纪, 孝文本纪, 孝景本纪, 孝武本纪
    # 10: 十二诸侯年表, 六国年表, 秦楚之际月表, 汉兴以来诸侯王年表, 高祖功臣侯者年表, 惠景间侯者年表, 建元以来侯者年表, 王子侯者年表, 汉兴以来将相名臣年表, 三代世表
    # 8: 礼书, 乐书, 律书, 历书, 天官书, 封禅书, 河渠书, 平准书
    # 30: 吴太伯世家, 齐太公世家, ... (many others)
    # 70: 伯夷列传, 管晏列传, ... (many others)
    # Plus "太史公自序" at the end.

    # Pattern to match chapter titles
    # They usually end with 本纪, 表, 书, 世家, 列传
    # Note: Some titles like "太史公自序" or "太史公曰" need careful handling.
    # The actual chapter titles in the file are mostly alone on a line.
    
    chapters = []
    current_chapter_title = None
    current_chapter_content = []
    
    # We start after "========正文========"
    start_found = False
    
    # Chapter markers
    re_chapter = re.compile(r'^(.+(本纪|表|书|世家|列传))$')
    re_skip = re.compile(r'^(十二本纪|十表|八书|三十世家|七十列传|========.*========)$')

    for line in lines:
        line_strip = line.strip()
        
        if "========正文========" in line_strip:
            start_found = True
            continue
            
        if not start_found:
            continue
            
        # Check for chapter title
        match = re_chapter.match(line_strip)
        if match and not re_skip.match(line_strip):
            # If we were already in a chapter, save it
            if current_chapter_title:
                chapters.append((current_chapter_title, current_chapter_content))
            
            current_chapter_title = line_strip
            current_chapter_content = []
        elif line_strip == "太史公自序":
            if current_chapter_title:
                chapters.append((current_chapter_title, current_chapter_content))
            current_chapter_title = line_strip
            current_chapter_content = []
        elif current_chapter_title:
            current_chapter_content.append(line)

    # Add the last chapter
    if current_chapter_title:
        chapters.append((current_chapter_title, current_chapter_content))

    # Write files
    for i, (title, content) in enumerate(chapters, 1):
        filename = f"{i:03d}_{title}.txt"
        # Sanitize filename (remove characters like / though unlikely here)
        filename = filename.replace('/', '_').replace('\\', '_')
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(title + "\n")
            f.writelines(content)
            
    print(f"Successfully split into {len(chapters)} files in '{output_dir}'.")

if __name__ == "__main__":
    split_shiji("/home/baojie/work/shiji-kb/史记.txt", "/home/baojie/work/shiji-kb/史记_章节")
