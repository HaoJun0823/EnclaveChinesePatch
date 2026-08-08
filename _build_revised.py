# -*- coding: utf-8 -*-
"""
以英文文件为骨架，生成修订后的完整中文翻译文件。
- 所有英文键全部保留（1286 条），补齐缺失键
- 无重复键
- 占位符/分隔符与英文一致
- 故事书部分使用信雅达重译，其余保留现有翻译（个别修正）
"""
import re
import sys

sys.path.insert(0, 'G:/Projects/Enclave')
from _revision_dict import REVISED

ENG_PATH = 'G:/Projects/Enclave/_eng_utf8.tmp'
CHS_PATH = 'G:/Projects/Enclave/StringTable_Chs_Full.txt'
OUT_PATH = 'G:/Projects/Enclave/StringTable_Chs_Revised.txt'

# 读取英文文件（UTF-8 临时转码版）
with open(ENG_PATH, 'r', encoding='utf-8') as f:
    eng_lines = f.readlines()

# 读取现有中文文件
with open(CHS_PATH, 'r', encoding='utf-8') as f:
    chs_text = f.read()

# 解析中文：key -> value（首次出现优先）
chs_map = {}
for line in chs_text.splitlines():
    m = re.match(r'^\s*\*(.+?)\s+\"(.*)\"\s*$', line)
    if m:
        key, val = m.group(1), m.group(2)
        if key not in chs_map:
            chs_map[key] = val

# 解析英文：key -> value（用于校验）
eng_keys = []
for line in eng_lines:
    m = re.match(r'^\s*\*(.+?)\s+\"(.*)\"\s*$', line)
    if m:
        eng_keys.append((m.group(1), m.group(2)))

eng_map = dict(eng_keys)

# 生成新文件内容
out_lines = []
# 保留英文文件开头注释（翻译为中文）
out_lines.append('// 所有新增/添加的键可以在以下行中找到\n')
out_lines.append('// PC PORT: Translate: (New keys)\n')
out_lines.append('// PC PORT: END: Translate\n\n')
out_lines.append('// 所有修改/变更的键可以在以下行中找到\n')
out_lines.append('// PC PORT: Translate: (Old key, new value)\n')
out_lines.append('// PC PORT: END: Translate\n\n')
out_lines.append('*game_english\n{\n')

# 键顺序按英文文件（保留原顺序，包括重复键——但用 set 去重保留第一次）
seen = set()
count = 0
for key, _ev in eng_keys:
    if key in seen:
        continue
    seen.add(key)
    # 取值：优先修订字典，其次现有中文，最后英文
    if key in REVISED:
        val = REVISED[key]
    elif key in chs_map:
        val = chs_map[key]
    else:
        val = _ev  # 兜底用英文
    out_lines.append(f'\t*{key}\t\t"{val}"\n')
    count += 1

out_lines.append('}\n')

with open(OUT_PATH, 'w', encoding='utf-8', newline='\n') as f:
    f.writelines(out_lines)

print(f'生成完成：{OUT_PATH}')
print(f'条目总数: {count}')

# ========== 验证 ==========
# 1. 重新解析生成的文件
def parse(path):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    entries = []
    for line in text.splitlines():
        m = re.match(r'^\s*\*(.+?)\s+\"(.*)\"\s*$', line)
        if m:
            entries.append((m.group(1), m.group(2)))
    return entries

rev = parse(OUT_PATH)
rev_keys = [k for k, _ in rev]
print(f'重新解析条目数: {len(rev)}')

# 2. 键完整性检查
eng_key_set = set(eng_map.keys())
rev_key_set = set(rev_keys)
missing = eng_key_set - rev_key_set
extra = rev_key_set - eng_key_set
print(f'英文缺失键: {len(missing)} {sorted(missing)[:10]}')
print(f'多余键: {len(extra)} {sorted(extra)[:10]}')

# 3. 重复键检查
from collections import Counter
dup = {k: c for k, c in Counter(rev_keys).items() if c > 1}
print(f'重复键: {len(dup)} {dup}')

# 4. 占位符检查
bad_ph = 0
rev_map = dict(rev)
for k, ev in eng_map.items():
    if k not in rev_map:
        continue
    e_ph = sorted(re.findall(r'§\w+', ev))
    c_ph = sorted(re.findall(r'§\w+', rev_map[k]))
    if e_ph != c_ph:
        bad_ph += 1
        if bad_ph <= 10:
            print(f'占位符不一致 {k}: EN={ev} CN={rev_map[k]}')
print(f'占位符不一致总数: {bad_ph}')

# 5. 分隔符检查
bad_sep = 0
for k, ev in eng_map.items():
    if k not in rev_map:
        continue
    if '|' in ev and ev.count('|') != rev_map[k].count('|'):
        bad_sep += 1
        if bad_sep <= 10:
            print(f'分隔符不一致 {k}: EN={ev} CN={rev_map[k]}')
print(f'分隔符不一致总数: {bad_sep}')
