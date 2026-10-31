# linux-xp-quick

**讓 Linux 速成輸入接近 Windows XP 傳統速成的使用習慣。**

[![測試](https://github.com/billysyt/linux-xp-quick/actions/workflows/test.yml/badge.svg)](https://github.com/billysyt/linux-xp-quick/actions/workflows/test.yml)
[![版本](https://img.shields.io/github/v/release/billysyt/linux-xp-quick)](https://github.com/billysyt/linux-xp-quick/releases)

以 Rime／IBus 為基礎，提供固定字序、每頁 9 個候選字、繁體中文聯想，以及 `Shift＋數字` 續接選字。

目前版本：**0.0.1**。已在 **Ubuntu 24.04、GNOME、X11、IBus Rime 1.5、librime 1.10** 驗證。

## 操作方式

| 操作 | 結果 |
| --- | --- |
| `O F 2`（人火 2） | 輸入「你」，字序不會因使用次數而改變 |
| `R Space`（口＋空白鍵） | 一碼直接輸入「口」 |
| `R B Space`（口月＋空白鍵） | 兩碼翻到下一頁候選字，不直接出字 |
| `1`–`9` | 選擇目前頁面的候選字 |
| `O J 1`（人十 1） | 輸入「什」，立即顯示聯想字 |
| 接著按 `Shift＋2` | 續接「麼」，組成「什麼」 |
| `Shift＋1`–`Shift＋9` | 選擇目前頁面的聯想字 |
| `=`／`Page Down` | 下一頁 |
| `-`／`Page Up` | 上一頁 |
| `Esc` | 取消候選／聯想清單 |
| 聯想清單出現時繼續輸入字根 | 直接開始下一個字 |

聯想清單只顯示將要輸入的字，例如「須、然、要」，沒有重複的完整詞組註解。亦可用滑鼠選字。聯想階段的空白鍵採用 Rime 預設行為：選取目前候選；`Shift＋數字` 可直接指定位置。

選用 GNOME 設定後，`Ctrl＋Space` 及 `Ctrl＋Shift` 可切換輸入來源。如果桌面只有英文與 Rime 兩個來源，就是切換中／英文；有其他來源時則會循環切換。

## 安裝

### Ubuntu／Debian：下載版本包

需要 Python 3.10 以上。Ubuntu 24.04 已內建 Python 3。

```bash
curl -fLO https://github.com/billysyt/linux-xp-quick/releases/download/v0.0.1/linux-xp-quick-0.0.1.tar.gz
tar -xzf linux-xp-quick-0.0.1.tar.gz
cd linux-xp-quick-0.0.1
./install.sh --install-deps --configure-gnome
```

`--install-deps` 透過 apt 安裝 IBus Rime、Lua 插件、Rime 編譯工具與 Python 依賴；只有這一步會使用 sudo。**請勿使用 `sudo ./install.sh`**，輸入法設定應屬於目前使用者。

`--configure-gnome` 會加入 Rime 輸入來源，將切換鍵設定為 `Ctrl＋Space`／`Ctrl＋Shift`，並備份被修改的桌面設定。這個選項需要在 GNOME 桌面的終端機內執行。原有其他輸入來源會保留。

如果已經安裝好 Rime，只需：

```bash
./install.sh
```

預設安裝至 `$XDG_CONFIG_HOME/ibus/rime`，未設定 XDG_CONFIG_HOME 時使用 `~/.config/ibus/rime`。

安裝後：

1. 第一次安裝 IBus Rime，請登出再登入，讓桌面辨識新輸入法。
2. 在「設定 → 鍵盤 → 輸入來源」加入 **中文 → Rime**。使用過 `--configure-gnome` 可略過此步。
3. 切換到 Rime，從右上角輸入法選單執行「部署」。
4. 在文字輸入欄按 `F4`，選擇 **XP 速成**。

原有 Rime 方案會保留。如果已經使用其他方案，安裝程式不會替你切換到 XP 速成，請完成第 4 步。

### 從 Git 安裝

```bash
git clone https://github.com/billysyt/linux-xp-quick.git
cd linux-xp-quick
git checkout v0.0.1
./install.sh --install-deps --configure-gnome
```

### 其他 Linux 桌面

安裝 IBus Rime、librime Lua 插件、`rime_deployer`、Rime prelude 及 PyYAML 後執行 `./install.sh`。切換鍵與輸入來源請在桌面設定中調整。

0.0.1 的自動安裝流程以 Ubuntu／Debian IBus 為支援範圍。Fcitx5、Wayland 及其他發行版尚未完整驗證；核心方案採用 Rime 格式，但這一版不提供 Fcitx5 自動設定。

## 更新、備份與移除

更新時下載新版本，再執行 `./install.sh`。重複安裝不會重複加入方案。

安裝程式會保留原有設定值，並把被覆寫檔案的原始內容保存在 `~/.local/state/linux-xp-quick/`（或 `$XDG_STATE_HOME/linux-xp-quick/`）。合併 YAML 時可能重新排版及移除註解；備份保留原始檔案的完整內容。

```bash
# 預覽安裝內容
./install.sh --dry-run

# 檢查依賴
python3 tools/install.py doctor

# 移除方案並還原設定
./uninstall.sh
```

移除後請重新部署 Rime。Rime 本身及其他輸入方案仍會保留。如果安裝後改過共用方案清單，移除程式只移除 XP 速成的項目；如果改過本專案的 Lua／字典檔案，程式會暫停，讓你先另存修改。自行更改過的桌面快捷鍵亦會保留。

自訂路徑可使用 `--rime-dir /path/to/rime`；移除時須提供相同路徑。

## 字序與聯想的來源

- **字表**：ibus-table-chinese 1.8.12 的 Quick Classic，包含 17,578 條一碼／兩碼字碼；保留固定排序，關閉使用頻率學習。
- **聯想詞庫**：衍生自 [慈心速成](https://github.com/arliong/rime-cixin-quick) 的繁體詞組索引，其詞頻資料源自 Rime「八股文」。另補充少量常用廣東話詞組。
- **「什 → Shift＋2 → 麼」**：本專案固定的相容設定，第一個聯想為「物」，第二個為「麼」。

這是開源 Rime 方案，並非微軟官方輸入法，也沒有使用 Windows 二進位檔案。目標是重現熟悉的操作方式；**所有字與聯想的排位並不保證與每個 Windows 版本完全相同**。

字庫、建置來源與原始授權一併附在版本包內，詳見 [THIRD_PARTY.md](THIRD_PARTY.md)。執行時不會連線查字、不記錄輸入文字，也不會依輸入歷史調整字序。

## 常見問題

**只有英文，沒有中文字候選欄？**

先確認已選擇 Rime 的「XP 速成」方案，而不是英文鍵盤。再執行 `python3 tools/install.py doctor`，確認 Lua 插件已安裝，然後重新部署。按住 Shift 選聯想字不會切成英文。

**按兩個字根後，空白鍵沒有出字？**

這是傳統速成的翻頁操作。請用 `1`–`9` 選字。一個字根加空白鍵才會直接選字。

**Ctrl＋Shift 與其他快捷鍵互相影響？**

這個組合由 GNOME／XKB 處理，某些應用程式也會使用 Ctrl＋Shift 組合。可在桌面設定保留 Ctrl＋Space，改用其他輸入來源切換鍵；速成方案本身不會攔截 Ctrl／Alt／Super 快捷鍵來選聯想字。

**想修改聯想排序？**

開發者可修改 `data/prediction-overrides.json`，執行 `python3 tools/build_data.py` 重建，再安裝及部署。一般使用者可在 [Issues](https://github.com/billysyt/linux-xp-quick/issues) 提供字根、目前排序與期望排序。

## 開發與測試

```bash
sudo apt-get install --no-install-recommends \
  ibus-rime librime-plugin-lua librime-bin rime-prelude \
  python3-yaml python3-gi lua5.4 librime-dev g++
./tools/test.sh
```

測試使用暫存 Rime 目錄，涵蓋固定字序、空白鍵規則、聯想翻頁、Shift 選字、滑鼠選字、工作階段隔離，以及安裝／還原流程。測試不會改動你的桌面輸入法。

```bash
python3 tools/build_data.py          # 從已鎖定的本地來源重建字庫
python3 tools/build_data.py --check  # 驗證產生結果與來源一致
python3 tools/package.py            # 產生版本包及 SHA256SUMS
```

專案結構：

```text
rime/          可安裝的 Rime 方案與 Lua 模組
data/          上游來源、校驗值及本地詞組調整
tools/         安裝、移除、測試、資料建置及打包工具
tests/         真實 librime 整合測試及安裝流程測試
licenses/      第三方授權原文
```

## 授權

本專案原創程式碼及文件採用 [MIT](LICENSE)。Quick Classic 字表按其原始「Freely redistributable without restriction」條款提供；聯想詞庫保留 LGPL-3.0 及上游所要求的授權聲明。請參閱 [THIRD_PARTY.md](THIRD_PARTY.md)。
