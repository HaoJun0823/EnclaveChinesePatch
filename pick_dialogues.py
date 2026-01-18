import os
import csv

def extract_dialogues(root_dir, output_csv):
    extracted_data = []
    dialogues_path = os.path.join(root_dir, 'Dialogues')
    
    if not os.path.exists(dialogues_path):
        print(f"错误: 找不到目录 {dialogues_path}")
        return

    for root, dirs, files in os.walk(dialogues_path):
        for file in files:
            if file.endswith('.xrg'):
                file_path = os.path.join(root, file)
                
                try:
                    # 使用 utf-16 逐行读取
                    with open(file_path, 'r', encoding='utf-16') as f:
                        for line_num, line in enumerate(f, 1):
                            clean_line = line.strip()
                            
                            # 识别以 *TEXT 开头的行
                            if clean_line.startswith('*TEXT'):
                                # 寻找第一个引号和最后一个引号的位置
                                start_idx = clean_line.find('"')
                                end_idx = clean_line.rfind('"')
                                
                                if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
                                    # 提取两个引号之间的内容
                                    text_content = clean_line[start_idx + 1 : end_idx]
                                    
                                    relative_path = os.path.relpath(file_path, root_dir)
                                    extracted_data.append({
                                        'file': relative_path,
                                        'line': line_num,
                                        'original_text': text_content
                                    })
                                else:
                                    # 如果没有成对引号，记录整行（去除 *TEXT 标记）
                                    text_content = clean_line.replace('*TEXT', '').strip()
                                    relative_path = os.path.relpath(file_path, root_dir)
                                    extracted_data.append({
                                        'file': relative_path,
                                        'line': line_num,
                                        'original_text': text_content
                                    })
                except Exception as e:
                    print(f"处理文件 {file} 时出错: {e}")

    # 写入 CSV
    headers = ['file', 'line', 'original_text']
    try:
        # 使用 QUOTE_ALL 确保所有内容都被引号包裹，防止 CSV 解析歧义
        with open(output_csv, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=headers, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            writer.writerows(extracted_data)
        print(f"提取完成！输出至: {output_csv}")
    except Exception as e:
        print(f"写入 CSV 时出错: {e}")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(current_dir, "dialogue_extraction_fixed.csv")
    extract_dialogues(current_dir, output_path)