import re
import os
# Randerion(HaoJun0823)
def generate_randerion_charset(text_dir, output_file):
    # 正则表达式：提取汉字、中文标点、全角符号
    chinese_pattern = re.compile(r'[\u4e00-\u9fa5\u3000-\u303f\uff00-\uffef\u2000-\u206f]')
    
    all_content = []
    file_count = 0

    if not os.path.exists(text_dir):
        print(f"错误：文件夹 '{text_dir}' 不存在。")
        return

    print(f"正在以 UTF-16 LE 模式扫描目录: {text_dir} ...")
    
    # 遍历文件夹
    for root, dirs, files in os.walk(text_dir):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                # 显式使用 utf-16-le 读取
                with open(file_path, 'r', encoding='utf-16-le', errors='ignore') as f:
                    all_content.append(f.read())
                file_count += 1
                print(f"已索引: {file}")
            except Exception as e:
                print(f"无法读取文件 {file}: {e}")

    if not all_content:
        print("未提取到任何内容，请确保 text 文件夹内的文件保存为 UTF-16 LE 编码。")
        return

    # 汇总并处理字符
    combined_text = "".join(all_content)
    matches = chinese_pattern.findall(combined_text)
    
    # 去重并排序 (保证字库定义的稳定性)
    unique_chars = sorted(list(set(matches)))
    result_text = "".join(unique_chars)

    # 写入 output 文件 (同样使用 UTF-16 LE)
    try:
        # 使用 utf-16 写入时，Python 会自动处理 LE 和 BOM
        with open(output_file, 'w', encoding='utf-16-le') as f:
            f.write(result_text)
        
        print("\n" + "="*40)
        print(f"【Randerion.CSharp.Definition 提取报告】")
        print(f"扫描文件夹: {text_dir}")
        print(f"处理文件数: {file_count}")
        print(f"提取中文字符总数: {len(matches)}")
        print(f"去重后唯一字符数: {len(unique_chars)}")
        print(f"最终字库已存至: {output_file} (UTF-16 LE)")
        print("="*40)

    except Exception as e:
        print(f"写入失败: {e}")

if __name__ == "__main__":
    # 配置
    TEXT_FOLDER = "text"           # 存放原始文本文档的文件夹
    OUTPUT_FILE = "input.txt"      # 最终生成的去重字库文件
    
    generate_randerion_charset(TEXT_FOLDER, OUTPUT_FILE)