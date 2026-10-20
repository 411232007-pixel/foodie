# Foodie

一支在本機執行的 Discord 機器人:`#food-log` 頻道裡有人傳食物照片,它用 `claude -p` 判斷、估熱量,記進 Excel、存下照片,並回覆那則訊息。

## 開始任何工作前

先讀 `docs/architecture.md`(設計、欄位、檔名規則、回覆格式、驗證清單、已知缺口)和 `README.md`。需求原文在 `docs/foodie requirements.md`。文件與你的想法衝突時,先問,不要自己改設計;**也不可以只改文件來掩蓋程式沒做到的事**。

## 常用指令

```powershell
uv run python -m foodie     # 啟動 bot(Ctrl+C 停止)
uv run pytest               # 自動測試(不連網路、不花額度)
$env:FOODIE_LIVE="1"; uv run pytest tests/test_live_isolation.py -s; Remove-Item Env:FOODIE_LIVE   # 真的呼叫 claude -p,花一點額度
```

## 四段防護

架構文件第 12 節定義了四段防護。程式裡每一段都用這種固定格式的註解包起來,有開始、有結束(注意開始那行「開始」前面是全形空格):

```python
# ==== 防護 1：claude -p 的檔案範圍隔離　開始 ====
...
# ==== 防護 1 結束 ====
```

| 防護 | 檔案 | 函式 |
|---|---|---|
| 1:`claude -p` 的檔案範圍隔離 | `src/foodie/analyzer.py` | `build_command` |
| 2:上傳者的字只當資料,不接進指令 | `src/foodie/analyzer.py` | `build_task` |
| 3:食物名稱變檔名前先清洗 | `src/foodie/photo_store.py` | `candidate_path` |
| 4:寫進 Excel 的文字不被當公式 | `src/foodie/ledger.py` | `_put_text` |

規則:

- **一開始四段全部開啟,不要停用任何一段。** 要做「關閉防護」的對照實驗,一律在**隔離副本**(複製到暫存資料夾)裡做,用虛構的機密資料,不要在這個專案裡直接註解掉,也不要留下任何停用防護的設定或開關。
- 每一段都要能整段拿掉而程式仍可運作(區塊前面有「沒有防護時」的預設寫法),之後教學會逐段關掉對照。
- 不要把防護邏輯散落在標記範圍之外,也不要把一般的格式與數字檢查(`result_check.py`)混進防護標記裡。
- 改動這四個檔案後,README 的防護位置表要同步(`tests/test_readme.py` 會檢查)。

## 不可以 commit 的東西

- 不可以把 `.env` commit 進 git。裡面有 `DISCORD_TOKEN`。要 commit 的是只有假值的 `.env.example`。
- `DATA_DIR` 裡的照片和 Excel 紀錄也不要 commit,那是大家的飲食隱私。`.gitignore` 已擋住 `.env`、`data/`、`photos/`、`food_log.xlsx`;`DATA_DIR` 若指到專案外面更保險。
- 不要在輸出、日誌、文件、對話裡顯示 token 或任何秘密值。測試只用虛構資料。
- commit 前跑 `uv run pytest`:`tests/test_repo_hygiene.py` 會檢查實際會被提交的檔案(已追蹤 + 未被忽略的新檔),不含 `.env`、照片、`.xlsx`,也不含真實 token 或長得像 token 的字串。再看一次 `git status`。
