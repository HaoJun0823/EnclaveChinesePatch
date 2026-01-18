import os
import csv
from pypinyin import pinyin, Style

def text_to_pinyin(text):
    """
    将中文转换为带音调和空格的拼音。
    例如: "你好" -> "Nǐ Hǎo"
    """
    if not text:
        return ""
    
    # Style.TONE: 声调风格，拼音声调在韵母上
    # heteronym=False: 不启用多音字模式
    pinyin_list = pinyin(text, style=Style.NORMAL, heteronym=False)
    
    # 将每个拼音首字母大写，并用空格连接
    # item[0] 是单个汉字的拼音字符串
    formatted_pinyin = [item[0].capitalize() for item in pinyin_list]
    
    return " ".join(formatted_pinyin)

def read_file_with_fallback(full_path):
    """
    尝试多种编码读取文件，解决 BOM 和 ANSI 冲突问题
    """
    encodings = ['utf-16', 'utf-16-le', 'cp936', 'utf-8']
    for enc in encodings:
        try:
            with open(full_path, 'r', encoding=enc) as f:
                content = f.readlines()
                # 如果成功读取且内容不为空，返回内容和当前使用的编码
                if content:
                    return content, enc
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise Exception("无法识别的编码格式")

def inject_translations_as_pinyin(root_dir, input_csv):
    mod_map = {}
    
    # 1. 读取 CSV
    try:
        with open(input_csv, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                file_rel_path = row['file']
                line_num = int(row['line'])
                pinyin_text = text_to_pinyin(row['original_text'])
                
                if file_rel_path not in mod_map:
                    mod_map[file_rel_path] = []
                mod_map[file_rel_path].append((line_num, pinyin_text))
    except Exception as e:
        print(f"读取 CSV 出错: {e}")
        return

    # 2. 遍历并写回
    for rel_path, changes in mod_map.items():
        full_path = os.path.join(root_dir, rel_path)
        if not os.path.exists(full_path):
            continue
            
        try:
            # 使用自动识别编码读取
            lines, detected_enc = read_file_with_fallback(full_path)
            
            # 执行替换
            modified = False
            for line_idx, pinyin_content in changes:
                actual_idx = line_idx - 1
                if 0 <= actual_idx < len(lines):
                    original_line = lines[actual_idx]
                    start_quote_idx = original_line.find('"')
                    end_quote_idx = original_line.rfind('"')
                    
                    if start_quote_idx != -1 and end_quote_idx != -1:
                        new_line = (
                            original_line[:start_quote_idx + 1] + 
                            pinyin_content + 
                            original_line[end_quote_idx:]
                        )
                        lines[actual_idx] = new_line
                        modified = True
            
            if modified:
                # 统一写回为 CP936 (ANSI)，因为拼音在 ANSI 下最安全
                # 针对 Randerion.CSharp.Definition 项目，ANSI 格式通常是其要求的
                with open(full_path, 'w', encoding='cp936', errors='replace') as f:
                    f.writelines(lines)
                print(f"成功处理 ({detected_enc} -> ANSI): {rel_path}")

        except Exception as e:
            print(f"处理文件 {rel_path} 时最终出错: {e}")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file = os.path.join(current_dir, "dialogue_extraction_chs.csv")
    inject_translations_as_pinyin(current_dir, csv_file)