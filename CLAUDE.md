# Foodie

一支在本機執行的 Discord 機器人:頻道裡有人傳食物照片,它用 `claude -p` 判斷、估熱量,記進 Excel、存下照片,並回覆上傳者。

## 開始任何工作前

先讀 `docs/architecture.md`。設計、欄位、檔名規則、回覆格式、驗證清單都在裡面;需求原文在 `docs/foodie requirements.md`。文件與你的想法衝突時,先問,不要自己改設計。

## 四段防護

架構文件第 12 節定義了四段防護。程式裡每一段都要用固定格式的註解包起來,有開始、有結束:

```python
# >>> 防護 3 開始:清洗檔名
...
# <<< 防護 3 結束
```

- 防護 1:`claude -p` 的工作範圍隔離(`analyzer.py`)
- 防護 2:上傳者的文字只當資料(`analyzer.py`)
- 防護 3:食物名稱變檔名前先清洗(`photo_store.py`)
- 防護 4:寫進 Excel 的文字不被當公式(`ledger.py`)

**一開始四段全部開啟。** 每一段都要能整段拿掉而程式仍可運作,之後教學會逐段關掉對照。不要把防護邏輯散落在標記範圍之外,也不要把一般的格式與數字檢查混進防護標記裡。

## 不可以 commit 的東西

- 不可以把 `.env` commit 進 git。裡面有 `DISCORD_TOKEN`。要 commit 的是只有假值的 `.env.example`。
- `DATA_DIR` 裡的照片和 Excel 紀錄也不要 commit,那是大家的飲食隱私。`DATA_DIR` 建議放在專案資料夾外面。
- commit 前看一下 `git status`,確認沒有 `.env`、照片、`.xlsx`。
