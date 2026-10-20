# foodie

一支在你自己電腦上執行的 Discord 機器人:指定頻道(`#food-log`)裡有人傳食物照片,它用 `claude -p` 判斷是不是食物、估重量和熱量,把結果記進 Excel、存下照片,並**回覆那則訊息**,最後附上「今日已攝取熱量」。程式關掉就不處理。

設計與原因在 [docs/architecture.md](docs/architecture.md),原始需求在 [docs/foodie requirements.md](docs/foodie%20requirements.md)。

## 目前驗證到哪裡

| 項目 | 狀態 |
|---|---|
| 自動測試(`uv run pytest`) | ✅ 通過(含 Discord 層的模擬測試、Excel、檔名、防護) |
| 真的呼叫 `claude -p` 的端對端與防護對照 | ✅ 已做過(結果見 architecture.md 第 12、16 節) |
| 程式能啟動、讀設定、連上 Discord 登入 | ✅ 能啟動並登入;**目前被擋在 Message Content Intent 沒打開**(見下方「第一次使用」第 3 步) |
| **在真的 Discord 頻道傳照片、看到 ⏳ 與回覆** | ⬜ **尚未實測**,需要你操作 |

## 第一次使用

1. 照 [docs/discord-server-setup.md](docs/discord-server-setup.md) 建 Server、`#food-log` 頻道、取得 `CHANNEL_ID`。
2. 照 [docs/discord-bot-setup.md](docs/discord-bot-setup.md) 建 bot、取得 token、邀進 Server。邀請連結的權限數字要是 **`101440`**(含 Add Reactions 用來顯示 ⏳,以及 Attach Files 用來讓 `!export` 傳檔案)。
3. 到 Developer Portal → 你的 application → **Bot** → 打開 **MESSAGE CONTENT INTENT** → 按 **Save Changes**。沒開的話程式會直接退出並告訴你這件事。
4. 在專案資料夾建 `.env`(範本是 `.env.example`),填四個項目:

   ```
   DISCORD_TOKEN=你的 bot token
   CHANNEL_ID=#food-log 的頻道 ID
   CLAUDE_MODEL=haiku
   DATA_DIR=./data
   ```

   `DATA_DIR` 的相對路徑是以**專案資料夾**為基準,跟你在哪裡啟動無關。`.env` 和 `data/` 都已被 `.gitignore` 擋住。

## 啟動

在專案資料夾(`C:\Users\a0939\foodie`)打開 PowerShell:

```powershell
uv run python -m foodie
```

(`uv run foodie` 也可以,效果相同。)看到 `已上線:Foodie(bot id=…),正在聽頻道 #food-log` 就是成功了。要停止按 **Ctrl + C**;如果當下正在分析照片,最多會多等約 90 秒才完全結束。

啟動需要:`uv` 已安裝、Claude Code(`claude` 指令)已安裝並登入。分析照片會用掉你自己的 Claude 額度。

## 在 #food-log 傳什麼、會看到什麼

傳一張食物照片(手機相簿的 JPG 就可以;PNG、WebP、GIF 也行,單檔 8 MB 內)。預期:

1. 照片底下很快出現 **⏳**(收到,排隊中)。
2. 幾秒到十幾秒後,⏳ 消失,bot **回覆那則訊息**,類似:

   ```
   是食物:牛肉麵
   成份:牛肉、麵條、青菜、湯
   重量:約 500 公克
   熱量:約 650 大卡
   你今天已攝取熱量:約 650 大卡
   ```
3. `DATA_DIR` 裡多了:
   - `food_log.xlsx` 新增一列(你要求的 8 個欄位,最後多一欄「上傳者ID」)
   - `photos\2026-10-20 15-17-03 牛肉麵.jpg`

其他測試:

| 傳什麼 | 預期 |
|---|---|
| 一個馬克杯(不是食物) | 回覆「你傳的不是食物,是馬克杯。」並列出重量 0、熱量 0;Excel「食物敘述」寫「不是食物」、「成份」寫「馬克杯」;照片照樣存;當日總熱量不變 |
| 一則訊息附 2~3 張照片 | 一張一張處理,最後一則合併回覆 |
| 很模糊/全黑的照片 | 「照片看不清楚，請重拍一張」,不記錄、不存照片 |
| 輸入 `!export` | 回覆你自己的紀錄 Excel(見下一節);還沒有紀錄時回「你還沒有任何紀錄」 |
| 其他純文字、PDF、影片 | 完全沒反應 |
| 別的頻道傳照片 | 完全沒反應 |
| 同一秒傳兩張同名食物 | 檔名第二張尾巴加 `-2` |

## 匯出自己的紀錄:`!export`

任何人在 `#food-log` 輸入 **`!export`**(只輸入這一個詞),bot 會回覆那則訊息,附上一份 `foodie-日期.xlsx`,裡面是**你自己**的全部歷史紀錄:

- 只有你的資料(用 Discord 使用者 ID 比對,別人的列不會出現),沒有照片,也沒有你電腦上的檔案路徑。
- 欄位:日期時間、上傳者、食物敘述、成份、重量、熱量、當日已攝取熱量。
- 這是一份新檔案,不會動到原本的 `food_log.xlsx`;不花 Claude 額度;同一個人 60 秒內只能匯出一次。
- 需要 bot 有 **Attach Files** 權限(用 `permissions=101440` 的連結授權)。
- **注意**:檔案是回覆在頻道裡,能看到 `#food-log` 的人都能下載。
- 這個版本以前建立的舊紀錄(沒有「上傳者ID」)**不會被匯出給任何人**,因為只有顯示名稱,任何人都能改名冒充。要納入,請在 Excel 的第 9 欄手動填上對方的 Discord ID。

**當日已攝取熱量是「每個人各算各的」**:用 Discord 使用者 ID 分人(改暱稱、或兩個人暱稱一樣都不會算混),所以小明的回覆只加總小明今天吃的。每天午夜 00:00(你電腦的時間)歸零重算。這個版本以前的舊紀錄沒有 ID,會暫時用「上傳者」欄的名稱比對。

## 測試

```powershell
uv run pytest                      # 自動測試,不連網路、不花額度

# 需要真的呼叫 claude -p(花一點額度,使用虛構的機密檔):
$env:FOODIE_LIVE="1"; uv run pytest tests/test_live_isolation.py -s; Remove-Item Env:FOODIE_LIVE
```

## 四段防護在哪裡

每一段都用這種註解包起來,**一開始全部開啟**,之後教學可以單獨把某一段整段註解掉:

```python
# ==== 防護 1：claude -p 的檔案範圍隔離　開始 ====
...
# ==== 防護 1 結束 ====
```

| 防護 | 做什麼 | 檔案 | 函式 | 標記大約行號 |
|---|---|---|---|---|
| 防護 1 | `claude -p` 在只放這一張照片的暫存資料夾裡執行,只給讀檔工具 | `src/foodie/analyzer.py` | `build_command` | 83–91 |
| 防護 2 | 上傳者打的字放進有隨機分隔線的「資料區」,不接進指令 | `src/foodie/analyzer.py` | `build_task` | 106–117 |
| 防護 3 | 食物名稱變檔名前清掉路徑字元,並確認最後路徑仍在 `photos` 裡 | `src/foodie/photo_store.py` | `candidate_path` | 43–54 |
| 防護 4 | 寫進 Excel 的文字一律存成純文字,不當公式 | `src/foodie/ledger.py` | `_put_text` | 202–208 |

行號會隨程式修改而位移,用函式名稱或這個指令找最準:

```powershell
Select-String -Path src\foodie\*.py -Pattern "==== 防護"
```

`tests/test_guard_markers.py` 會檢查四段都存在、成對、沒被註解掉;`tests/test_readme.py` 會檢查上表的函式名稱還對得上,行號沒有偏離超過 12 行。

### 防護的能力與限制(如實)

- **防護 1** 實際擋住讀檔的是 Claude Code 自己的權限系統:在 `--permission-prompts none` 下,工作資料夾以外的讀取會被拒絕(實測有被拒絕的紀錄)。**它不是作業系統層級的沙盒**:如果 Claude Code 的權限判斷有漏洞,就沒有第二道牆。程式另外只開放 `Read` 工具、`dontAsk` 模式、`--restricted`,但在這台電腦上**沒能證明這三個設定帶來額外的保護**(拆開測試時,只靠「暫存資料夾 + 不彈詢問」就已經擋住),它們目前只是備用的多一層。要更強,需要用另一個低權限的 Windows 帳號執行 `claude`,尚未做。
- **防護 2** 是「結構分離 + 明確告知」,對模型是機率性的,不是數學保證;實測關掉它會被騙(名稱被改成指定字串、熱量被改成 0),開著則沒有。它被其他層補強:防護 1(限制能讀什麼)、結果檢查(數字範圍、型別)。
- **防護 3** 有雙重保險:清洗字元,並在寫檔前確認解析後的路徑仍在 `photos` 資料夾內;另外用「不覆蓋已存在檔案」的方式建立檔案。
- **防護 4** 套用到**所有**寫進 Excel 的文字欄位,包含上傳者名稱、食物敘述、成份、照片路徑。

## 已知限制

- 副檔名跟著**真實格式**:JPEG 存 `.jpg`,PNG 存 `.png`,不會把 PNG 偷偷改名成 `.jpg`,也沒有轉檔(沒有裝圖片處理套件)。判斷格式只看檔案開頭幾個位元組,不是完整解碼。
- 程式被強制結束(斷電、直接關視窗)時,還在排隊的訊息上的 ⏳ 會留著;正常用 Ctrl + C 關閉會清掉。
- 開著 Excel 時 Windows 會鎖檔:程式會在終端機警告並重試 3 次,仍失敗就回覆「紀錄檔暫時寫不進去」,**不留照片、不寫半筆資料**。建議 bot 運作時用另存新檔或複製一份來看。
- 照片會送到 Anthropic 的服務分析。

## 專案結構

```
src/foodie/
  __main__.py      啟動入口(讀設定、登入)
  config.py        讀 .env;額度與安全上限
  bot.py           Discord:過濾訊息、⏳、排隊、一次處理一則、回覆
  processor.py     一張照片的完整流程(分析 → 存照片 → 寫 Excel)
  analyzer.py      呼叫 claude -p                  ← 防護 1、2
  result_check.py  檢查 claude 的 JSON(型別、數字、範圍)
  photo_store.py   存照片、檔名、撞名               ← 防護 3
  ledger.py        Excel 紀錄、當日總熱量            ← 防護 4
  replies.py       回覆文字
tests/             自動測試
docs/              需求、架構、Discord 設定步驟
```
