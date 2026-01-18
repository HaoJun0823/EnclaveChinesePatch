import os
import csv

def inject_translations_ansi(root_dir, input_csv):
    mod_map = {}
    
    # 1. 读取 CSV 翻译文件
    try:
        # CSV 通常建议用 utf-8-sig 读取以保证兼容性
        with open(input_csv, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                file_rel_path = row['file']
                line_num = int(row['line'])
                new_text = row['original_text']
                
                if file_rel_path not in mod_map:
                    mod_map[file_rel_path] = []
                mod_map[file_rel_path].append((line_num, new_text))
    except Exception as e:
        print(f"读取 CSV 出错: {e}")
        return

    # 2. 遍历并写回文件 (以 ANSI 格式)
    for rel_path, changes in mod_map.items():
        full_path = os.path.join(root_dir, rel_path)
        
        if not os.path.exists(full_path):
            print(f"警告: 找不到文件 {full_path}")
            continue
            
        try:
            # 原始文件是 UTF-16 LE，先读进来
            with open(full_path, 'r', encoding='utf-16') as f:
                lines = f.readlines()
            
            # 执行替换
            for line_idx, translated_content in changes:
                actual_idx = line_idx - 1
                if 0 <= actual_idx < len(lines):
                    original_line = lines[actual_idx]
                    
                    start_quote_idx = original_line.find('"')
                    end_quote_idx = original_line.rfind('"')
                    
                    if start_quote_idx != -1 and end_quote_idx != -1:
                        # 拼接新行，保留原始的引号外结构
                        new_line = (
                            original_line[:start_quote_idx + 1] + 
                            translated_content + 
                            original_line[end_quote_idx:]
                        )
                        lines[actual_idx] = new_line
            
            # --- 关键修改点：写回为 ANSI ---
            # 在简体中文系统下，encoding='ansi' 等同于 'gbk'
            with open(full_path, 'w', encoding='cp936', errors='replace') as f:
                f.writelines(lines)
            
            print(f"已成功转换为 ANSI 并还原: {rel_path}")

        except Exception as e:
            print(f"处理文件 {rel_path} 时出错: {e}")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file = os.path.join(current_dir, "dialogue_extraction_chs.csv")
    
    inject_translations_ansi(current_dir, csv_file)
    print("\n所有文件已完成 ANSI 编码还原。")