# -*- coding: utf-8 -*-
"""
extract_chars.py —— 字库汉字提取脚本
========================================
从指定目录的所有文件中提取所有汉字（每个字仅保留 1 个），
包括中文标点符号，输出为单行 txt（供 XWC_Static.exe 编译字库使用）。

用法:
    python extract_chars.py <目录1> [目录2 ...] [-o 输出文件]

示例:
    python extract_chars.py "G:/Projects/Enclave/registry" "G:/Projects/Enclave/Dialogues"

输出格式（与 charset_def.txt 一致）:
    - UTF-8 编码，无 BOM
    - 单行，字符间无空格/分隔符
    - 每个字符只出现一次，按 Unicode 码点排序
"""

import os
import re
import sys
import argparse


# ============ 字符范围定义 ============

# 汉字范围：CJK 统一表意文字（基本区）
CJK_START = 0x4E00
CJK_END = 0x9FFF

# 汉字扩展区 A（若需要可打开，多数游戏字库不含）
CJK_EXT_A_START = 0x3400
CJK_EXT_A_END = 0x4DBF

# 中文标点符号（全角标点 + 中文专用符号）
CHINESE_PUNCTUATION = set(
    '，。、；：？！""''（）《》〈〉【】〔〕—…·～‘’“”「」『』'
    '！＃％＆（）＊，－．／：；？＠［＼］＾＿｀｛｜｝～'
)

# 常用中文标点全集：即使当前文本未出现也强制纳入字库，
# 防止游戏系统动态拼接消息（如 "（新）"、"第 3 章"）时缺字。
MANDATORY_PUNCTUATION = set(
    '，。、；：？！""''（）《》〈〉【】〔〕—…·～‘’“”「」『』！'
    '　　'  # 全角空格
)

# 拉丁字符全集：数字 + 大小写字母 + 欧洲拉丁扩展字符（重音字母等）。
# 游戏内可能显示英文菜单、关卡名、数字统计等，强制纳入避免缺字。
LATIN_CHARS = set(
    '0123456789'
    'abcdefghijklmnopqrstuvwxyz'
    'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    '×àáâãäåæçèéêëìíîïðñòóôõöøùúûüýÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝß'
)

# ASCII 符号全集：半角标点/运算符等。
# 字符串表与对话文件中的格式标记（如 § 占位符、| 段落分隔、* 键前缀、
# _ 键名下划线、{ } 宏、! ? 语气、- . / : 等）可能原样显示或进入文本流，
# 强制纳入避免游戏内缺字。
ASCII_SYMBOLS = set(
    ' !"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'
    '§´―'  # 文件里实际出现的扩展符号
)

# 完整的可打印 ASCII（含字母数字），供 --include-ascii-all 使用
PRINTABLE_ASCII = set(''.join(chr(i) for i in range(32, 127)))


def is_hanzi(ch):
    """判断是否为汉字（基本区 CJK）"""
    code = ord(ch)
    return CJK_START <= code <= CJK_END


def is_hanzi_ext_a(ch):
    """判断是否为汉字（扩展区 A）"""
    code = ord(ch)
    return CJK_EXT_A_START <= code <= CJK_EXT_A_END


def is_chinese_punct(ch):
    """判断是否为中文标点符号"""
    return ch in CHINESE_PUNCTUATION


def decode_file(path):
    """自动检测并解码文件内容（UTF-16 LE / UTF-8 / GBK）。

    注意：UTF-16 解码几乎不会失败（任意字节对都能组成 code unit），
    若把 UTF-8 文件误按 UTF-16 解码会产生大量假字符。
    因此按顺序：BOM 优先 -> UTF-8 严格校验 -> UTF-16（校验质量）-> GBK。
    """
    with open(path, 'rb') as f:
        data = f.read()

    # 1. BOM 优先判断
    if data[:2] in (b'\xff\xfe', b'\xfe\xff'):
        return data.decode('utf-16')
    if data[:3] == b'\xef\xbb\xbf':
        return data.decode('utf-8-sig')

    # 2. UTF-8 严格解码（唯一不会产生假字符的方式）
    try:
        return data.decode('utf-8')
    except (UnicodeDecodeError, ValueError):
        pass

    # 3. UTF-16 尝试（校验：无替换符/代理区残留才算有效）
    try:
        t = data.decode('utf-16')
        bad = sum(1 for c in t if 0xDC00 <= ord(c) <= 0xDFFF or c == '\ufffd')
        if bad == 0:
            return t
    except (UnicodeDecodeError, ValueError):
        pass

    # 4. GBK（老工具常见）
    try:
        return data.decode('gbk')
    except (UnicodeDecodeError, ValueError):
        return None


def walk_files(dirs):
    """递归遍历目录，返回所有文件路径"""
    files = []
    for d in dirs:
        if os.path.isfile(d):
            files.append(d)
        elif os.path.isdir(d):
            for root, _, fnames in os.walk(d):
                for fn in fnames:
                    # 跳过 .lnk 快捷方式等无意义文件
                    if fn.lower().endswith('.lnk'):
                        continue
                    files.append(os.path.join(root, fn))
    return files


def extract_chars(files, include_ext_a=False, mandatory_punct=True, include_latin=True,
                  include_ascii_sym=True, include_ascii_all=False):
    """
    从文件中提取所有汉字与中文标点（去重）。
    返回 (chars_set, total_files, decoded_files, total_chars_read)
    """
    chars = set()
    total_chars_read = 0
    decoded = 0
    failed = []

    for fp in files:
        text = decode_file(fp)
        if text is None:
            failed.append(fp)
            continue
        decoded += 1

        # 逐字符统计（只计汉字与中文标点）
        for ch in text:
            if is_hanzi(ch) or is_chinese_punct(ch):
                chars.add(ch)
                total_chars_read += 1
            elif include_ext_a and is_hanzi_ext_a(ch):
                chars.add(ch)
                total_chars_read += 1

    # 强制纳入常用标点全集（保证字库完整）
    if mandatory_punct:
        for ch in MANDATORY_PUNCTUATION:
            chars.add(ch)

    # 强制纳入拉丁字符（数字/字母/重音字符）
    if include_latin:
        for ch in LATIN_CHARS:
            chars.add(ch)

    # 强制纳入 ASCII 符号（格式标记/半角标点）
    if include_ascii_sym:
        for ch in ASCII_SYMBOLS:
            chars.add(ch)

    # 完整可打印 ASCII（空格+标点+字母数字全覆盖）
    if include_ascii_all:
        for ch in PRINTABLE_ASCII:
            chars.add(ch)

    return chars, decoded, failed, total_chars_read


def main():
    parser = argparse.ArgumentParser(
        description='提取汉字与中文标点生成字库 txt（每个字 1 个，按 Unicode 排序）'
    )
    parser.add_argument('dirs', nargs='+', help='要扫描的目录或文件路径')
    parser.add_argument('-o', '--output', default='charset_new.txt',
                        help='输出文件路径（默认 charset_new.txt）')
    parser.add_argument('--include-ext-a', action='store_true',
                        help='是否包含 CJK 扩展区 A 汉字（默认不包含）')
    parser.add_argument('--merge', default=None, metavar='FILE',
                        help='合并现有字库文件（如 charset_def.txt），保留其全部字符，'
                             '防止漏掉旧文本用到的字')
    parser.add_argument('--no-latin', action='store_true',
                        help='不强制纳入拉丁字符（数字/字母/重音字符），默认包含')
    parser.add_argument('--no-ascii-sym', action='store_true',
                        help='不强制纳入 ASCII 符号（§ * _ | { } 等格式标记），默认包含')
    parser.add_argument('--ascii-all', action='store_true',
                        help='纳入全部可打印 ASCII（含空格和所有半角标点）')
    args = parser.parse_args()

    files = walk_files(args.dirs)
    print(f'扫描到文件: {len(files)} 个')

    chars, decoded, failed, total_read = extract_chars(
        files, args.include_ext_a, include_latin=not args.no_latin,
        include_ascii_sym=not args.no_ascii_sym, include_ascii_all=args.ascii_all)

    # 合并旧字库
    if args.merge and os.path.isfile(args.merge):
        with open(args.merge, 'r', encoding='utf-8') as f:
            old_text = f.read()
        for ch in old_text:
            chars.add(ch)
        print(f'已合并旧字库 {args.merge}: +{len(set(old_text))} 字符')

    # 按 Unicode 码点排序
    sorted_chars = sorted(chars, key=ord)
    result = ''.join(sorted_chars)

    # 写文件（UTF-8，无 BOM，单行，不追加换行，与 charset_def.txt 格式一致）
    with open(args.output, 'w', encoding='utf-8', newline='') as f:
        f.write(result)

    # 输出统计
    print(f'成功解码文件: {decoded}/{len(files)}')
    if failed:
        print('无法解码的文件:')
        for fp in failed:
            print(f'  {fp}')
    print(f'提取到的字符总数(含重复): {total_read}')
    print(f'去重后字符数: {len(chars)}')
    print(f'输出文件: {args.output} ({os.path.getsize(args.output)} bytes)')

    # 显示部分内容预览
    print(f'预览: {result[:80]}...')


if __name__ == '__main__':
    main()
