# 第三方內容與資料來源

## Quick Classic 字表

- 來源：[ibus-table-chinese 1.8.12](https://github.com/mike-fabian/ibus-table-chinese/blob/1.8.12/tables/quick/quick-classic.txt)
- 原作者／轉換者：Roy Hiu-yeung Chan（Roy Chan）。上游註明來源為 xcin module。
- 原始條款：`LICENSE = Freely redistributable without restriction`。
- 未修改的原始檔案：`data/upstream/quick-classic.txt`，保留完整檔頭。
- 衍生檔案：`rime/linux_xp_quick.dict.yaml`。
- 修改方式：只收錄一至兩個英文字母的字碼，按頻率、Big5 編碼及 Unicode 排序，輸出 Rime 固定排序字典。特殊符號鍵碼未納入；標點由 Rime prelude 提供。

## 繁體聯想詞組

- 來源：[arliong/rime-cixin-quick](https://github.com/arliong/rime-cixin-quick/tree/e6d0377c45858187d254ec4a719ee601625f90a4)，鎖定 commit `e6d0377c45858187d254ec4a719ee601625f90a4`。
- 未修改的索引：`data/upstream/cixin_quick_index.lua`。
- 上游專案版權：2026 慈心速成（Cixin Quick）專案貢獻者。
- 詞頻資料衍生自 [rime/rime-essay](https://github.com/rime/rime-essay)，LGPL-3.0。Rime essay 版權持有人包括 GONG Chen、Kunki Chiu。
- 上游原創部分採 MIT；其授權同時指出生成的詞組索引受 LGPL-3.0 約束。完整聲明保留於 `licenses/Cixin-Quick-MIT.txt` 及 `licenses/Cixin-Quick-NOTICE.md`。
- 衍生索引：`rime/lua/linux_xp_quick/data.lua`，保留 LGPL-3.0。
- 修改方式：去除重複詞組、穩定排序索引鍵，合併 `data/prediction-overrides.json` 的「什」字位置及廣東話詞組調整。
- 可修改來源、覆寫資料及建置工具全部包含於倉庫及發佈包；執行 `python3 tools/build_data.py` 可離線重建。
- LGPL-3.0 與其引用的 GPL-3.0 全文分別保存在 `licenses/LGPL-3.0.txt` 及 `licenses/GPL-3.0.txt`。

上游 NOTICE 亦提到 rime-ms-quick 單字字表；本專案使用的單字字表來自 Quick Classic。為保留上游 NOTICE 所引用的授權檔案，本專案一併附上 `licenses/rime-ms-quick-MIT.txt`，並未使用其整份單字碼表或 Windows 程式。

## 執行環境

Rime、IBus Rime、librime-lua 及 Rime prelude 由系統套件管理員提供，依各自授權發佈。版本包不包含上述程式的二進位檔案。測試使用系統安裝的 librime 標頭與函式庫。

所有鎖定來源的下載位置、版本及 SHA-256 記錄於 `data/sources.json`。
