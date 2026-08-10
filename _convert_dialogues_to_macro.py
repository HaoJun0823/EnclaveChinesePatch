# -*- coding: utf-8 -*-
"""
_convert_dialogues_to_macro.py
把 Dialogues_中文润色_UTF-16 的对话文本转换为「§L 宏引用 + StringTable 表」方案
（对齐 Enclavec简繁汉化补丁v3 的纯文本路线，零 DLL 依赖）。

规则：
  1. 每个非空、非纯§宏引用的 *TEXT 值生成唯一 key: DLG_<文件名大写>_<NNN>
  2. .xrg 里 *TEXT "值" 替换为 *TEXT "§LDLG_XXX"（保留 BOM/CRLF/缩进/其余行）
  3. 值按引擎原生格式 `\t*KEY\t\t"value"` 追加进 StringTable 的 *game_english 块内
  4. 空 TEXT、纯§宏引用（如 §LCHECKPOINT_MSG）保持原样不转换
  5. 含§混合文本（教程 §LTUTORIAL_* + 中文）正常转换，值保留原样（引擎二次展开）

用法:
  python _convert_dialogues_to_macro.py [输入目录] [输出目录] [StringTable路径]
默认:
  输入  G:/Projects/Enclave/Dialogues_中文润色_UTF-16
  输出  G:/Projects/Enclave/Dialogues_§L宏_UTF-16
  表    G:/Projects/Enclave/StringTable_Chs_Revised.txt
"""
import os, re, sys, glob, json

DLG_DIR   = r'G:/Projects/Enclave/Dialogues_中文润色_UTF-16'
OUT_DIR   = r'G:/Projects/Enclave/Dialogues_§L宏_UTF-16'
ST_PATH   = r'G:/Projects/Enclave/StringTable_Chs_Revised.txt'

TEXT_RE = re.compile(r'(\*TEXT\s+)"([^"]*)"')

def classify(v):
    """返回 'skip'（保持原样）或 'conv'（需转换）"""
    s = v.strip()
    if not s:
        return 'skip'          # 空 TEXT
    if '§' in s and not any('\u4e00' <= c <= '\u9fff' for c in s):
        return 'skip'          # 纯§宏引用（已是查表入口）
    return 'conv'

def conv_one_file(src_path, out_path, key_prefix, entries):
    """转换单个 .xrg，返回 (行数, text数, 转换数, 跳过数)"""
    raw = open(src_path, 'rb').read()
    # 保留原始 BOM：仅当文件头是 UTF-16LE BOM 时按 utf-16-le 解码，写回时补 BOM
    has_bom = raw[:2] == b'\xff\xfe'
    body = raw[2:] if has_bom else raw
    try:
        text = body.decode('utf-16-le')
    except UnicodeDecodeError:
        # 非 UTF-16（理论上不会发生），原样复制
        open(out_path, 'wb').write(raw)
        return None
    lines = text.split('\n')
    n_text = n_conv = n_skip = 0
    idx = 0
    for i, line in enumerate(lines):
        m = TEXT_RE.search(line)
        if not m:
            continue
        n_text += 1
        val = m.group(2)
        if classify(val) == 'skip':
            n_skip += 1
            continue
        key = f'{key_prefix}_{idx:03d}'
        idx += 1
        n_conv += 1
        entries.append((key, val))
        newline = line[:m.start(2)] + f'§L{key}' + line[m.end(2):]
        lines[i] = newline
    out = '\n'.join(lines)
    data = ('\ufeff' + out if has_bom else out).encode('utf-16-le')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    open(out_path, 'wb').write(data)
    return (len(lines), n_text, n_conv, n_skip)

def update_stringtable(st_path, entries, report):
    """把 entries 追加进 StringTable 的 *game_english 块（最后一个 } 前）"""
    raw = open(st_path, 'rb').read()
    has_bom = raw[:2] == b'\xff\xfe'
    text = raw[2:].decode('utf-16-le') if has_bom else raw.decode('utf-16-le')
    if text.startswith('\ufeff'):
        text = text[1:]
        has_bom = True
    # 找 game_english 块内最后一个独立行 } 作为插入点
    lines = text.split('\n')
    insert_idx = None
    # 从末尾找属于 *game_english 的闭合 }：最后一个非空行
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip() == '}':
            insert_idx = i
            break
    if insert_idx is None:
        raise RuntimeError('StringTable 未找到闭合 }')
    new_entries = [f'\t*{k}\t\t"{v}"' for k, v in entries]
    lines[insert_idx:insert_idx] = new_entries
    out = '\n'.join(lines)
    data = ('\ufeff' + out if has_bom else out).encode('utf-16-le')
    open(st_path, 'wb').write(data)
    report['inserted_after_line'] = insert_idx
    report['table_total_entries'] = len(new_entries)

def main():
    dlg_dir = sys.argv[1] if len(sys.argv) > 1 else DLG_DIR
    out_dir = sys.argv[2] if len(sys.argv) > 2 else OUT_DIR
    st_path = sys.argv[3] if len(sys.argv) > 3 else ST_PATH

    entries = []          # (key, value) 有序
    file_report = {}
    total = {'files': 0, 'texts': 0, 'conv': 0, 'skip': 0}

    for fp in sorted(glob.glob(os.path.join(dlg_dir, '*.xrg'))):
        fn = os.path.basename(fp)
        base = os.path.splitext(fn)[0].upper()
        key_prefix = f'DLG_{base}'
        out_path = os.path.join(out_dir, fn)
        r = conv_one_file(fp, out_path, key_prefix, entries)
        if r is None:
            file_report[fn] = 'NON-UTF16-SKIPPED'
            continue
        nl, nt, nc, ns = r
        total['files'] += 1
        total['texts'] += nt
        total['conv'] += nc
        total['skip'] += ns
        file_report[fn] = {'lines': nl, 'texts': nt, 'conv': nc, 'skip': ns}

    report = {'total': total, 'entries': len(entries), 'files': file_report}

    # 先校验 key 唯一，再写表
    keys = [k for k, _ in entries]
    dup = {k for k in keys if keys.count(k) > 1}
    if dup:
        raise RuntimeError(f'key 重复: {dup}')

    update_stringtable(st_path, entries, report)
    report['table_path'] = st_path
    report['out_dir'] = out_dir

    # 输出机器可读报告
    rep_path = os.path.join(out_dir, '_conversion_report.json')
    os.makedirs(out_dir, exist_ok=True)
    with open(rep_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print(json.dumps(report['total'], ensure_ascii=False))
    print(f"转换条目: {len(entries)}, 报告: {rep_path}")

if __name__ == '__main__':
    main()
