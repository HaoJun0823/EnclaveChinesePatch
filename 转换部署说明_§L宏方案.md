# Dialogues §L 宏转换部署说明（v1, 2026-08-10）

## 转换内容

把 `Dialogues_中文润色_UTF-16`（48 个文件，1158 条 *TEXT）转换为「§L 宏引用 + StringTable 表」方案，
对齐他人补丁（零 DLL 依赖、引擎原生宽管线）。

| 产物 | 路径 | 说明 |
|---|---|---|
| 转换后对话文件 | `G:\Projects\Enclave\Dialogues_§L宏_UTF-16\`（48 个） | `*TEXT "中文"` → `*TEXT "§LDLG_XXX"`，其余逐字节保留 |
| 更新后汉化表 | `G:\Projects\Enclave\StringTable_Chs_Revised.txt` | 追加 1148 条 `DLG_*` key（原 1319 + 新 1148 = 2467） |
| 原表备份 | `StringTable_Chs_Revised.txt.bak_20260810` | 回滚用 |
| 转换脚本 | `G:\Projects\Enclave\_convert_dialogues_to_macro.py` | 补翻 32 个缺失文件后重跑 |

## 校验结果（全 PASS）

1. 结构一致性：48 个新 .xrg 与原文件非 TEXT 行逐字节相同，BOM/CRLF 同风格
2. key 对应：§L 引用 1148 个 ↔ 表中 1148 条 DLG_*，无缺失、无孤儿、无重复
3. 值完整性：抽查 Dlg_Marcus/DM01/LM01 全部正确；LM01 含 `§LTUTORIAL_*` 混合宏原样保留（引擎二次展开）
4. 字库覆盖：表内 1148 条对话值共用 984 个汉字，1931 字集 0 缺失
5. 跳过 10 条：Checkpoint 3 条纯宏（§LCHECKPOINT_MSG/2/3，表内已有对应 key）+ 7 条空 TEXT

## 部署步骤（建议顺序）

1. **备份游戏现状**（游戏目录当前为 Steam 纯净版）：
   ```
   cp -r "I:/SteamLibrary/steamapps/common/Enclave/Sbz1" "I:/SteamLibrary/steamapps/common/Enclave/Sbz1.bak_20260810"
   ```
2. **对话文件**：`Dialogues_§L宏_UTF-16\*.xrg`（48 个）→ 覆盖 `游戏\Sbz1\Dialogues\`
   ⚠️ 游戏内另有 32 个未翻译文件（Cut_* 过场、DM05/07/13、Dialogue_Adam、Dlg_Archer/Durzu/Golem 等）
   **保持英文原版不动**（不覆盖），游戏内会显示英文
3. **汉化表**：`StringTable_Chs_Revised.txt` → 复制为 `游戏\Sbz1\registry\StringTable_Eng.txt`（沿用 8-09 命名，UTF-16LE + BOM 格式一致）
4. **字库**：`G:\Projects\Enclave\Fonts\Clairvaux.xfc`（5.66MB，1931 字集）→ 覆盖 `游戏\Sbz1\Fonts\Clairvaux.xfc`
5. **P3.xrg**：无需修改（游戏已指向 `Registry\\StringTable_Eng.txt`，第 3 步即覆盖该名）
6. **DLL 可退役**：删除/移走 `binkw32.dll` proxy 链与 `EnclaveCJK.dll`（若在），游戏以纯文本方案运行

## 32 个未翻译文件清单（后续补翻）

Cut_Csl01_Assassin / Cut_Csl01_Guard / Cut_Csl01_OrcBoss / Cut_Csl01_Player /
Cut_Csl02_Archer / Cut_Csl03_Archer / Cut_Csl03_AssemblyMember / Cut_Csl03_Princess /
Cut_Csl03_Queen / Cut_Csl04_Archer / Cut_Csl04_Marcus / Cut_Csl05_Lorus /
Cut_Stl02_Narrator / DM05 / DM07 / DM13 / Dialogue_Adam / Dlg_Archer /
Dlg_Durzu / Dlg_Golem（其余 12 个见 `_conversion_report.json` 之外的游戏目录）

补翻流程：把英文原版 .xrg 翻译后存为 UTF-16LE（同格式），放入 `Dialogues_中文润色_UTF-16\`，
重跑 `python _convert_dialogues_to_macro.py`（会自动追加新 key，已有 key 不重复）。

## 回滚

```
cp "G:/Projects/Enclave/StringTable_Chs_Revised.txt.bak_20260810" "G:/Projects/Enclave/StringTable_Chs_Revised.txt"
# 游戏目录：用 Sbz1.bak_20260810 整体还原
```

## 验证要点（进游戏后）

- 过场/对话字幕中文正常、句尾无 @（走了 StringTable 宽管线，不经过 TFStr Assign 裸 strlen）
- 菜单全中文（原有 1319 条 key 不受影响）
- 教程按键名正常（LM01 的 §LTUTORIAL_* 二次展开，宏名后均为半角空格边界，已验 0 问题）
- 未翻译 32 文件显示英文（预期）
