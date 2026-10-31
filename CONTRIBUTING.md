# 參與開發

請先執行 README 的開發依賴安裝指令及 `./tools/test.sh`。

回報輸入問題時，請提供：

- Linux 發行版、桌面環境、X11／Wayland 及 Rime 版本。
- 完整按鍵順序，例如 `R B Space 1`。
- 實際輸出的字／候選排序，以及預期結果。

修改字庫請改 `data/` 的來源或覆寫資料，再執行 `python3 tools/build_data.py`，不要只改產生的字典。引入新資料時，請同時提供來源、版本及授權。

新增或修改輸入操作時，請更新 `tests/test_engine.cpp` 的實際按鍵測試。安裝流程的修改請涵蓋舊設定保留、重複安裝及移除還原。

提交前執行：

```bash
./tools/test.sh
python3 tools/package.py
```
