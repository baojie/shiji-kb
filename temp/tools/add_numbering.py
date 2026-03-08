import os

def add_numbering_to_txt(input_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    files = sorted([f for f in os.listdir(input_dir) if f.endswith('.txt')])
    
    for filename in files:
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)
        
        with open(input_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        numbered_lines = []
        p_count = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if i == 0: # Title
                numbered_lines.append(f"[{p_count}] {stripped}\n")
                p_count += 1
            elif not stripped:
                numbered_lines.append(line)
            else:
                numbered_lines.append(f"[{p_count}] {stripped}\n")
                p_count += 1
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(numbered_lines)
    
    print(f"Numbered files saved to {output_dir}")

if __name__ == "__main__":
    add_numbering_to_txt("/home/baojie/work/shiji-kb/archive/chapter_improved", "/home/baojie/work/shiji-kb/chapter_numbered")
