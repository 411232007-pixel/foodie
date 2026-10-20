# Discord Bot 設定步驟

這份文件帶你做:

1. 在 Discord Developer Portal 建立 application 與 bot
2. 打開 **Message Content Intent**(一定要)
3. 取得 bot token
4. 選好權限,把 bot 邀進**你自己的 Server**
5. 把 token 和 CHANNEL_ID 放進 `.env`

**開始前**:請先完成 [docs/discord-server-setup.md](discord-server-setup.md),你需要已經有自己的 Server,以及手上有 `CHANNEL_ID`。

> **關於畫面**:Discord Developer Portal 偶爾會改版,按鈕位置或名稱若和下面略有不同,找意思最接近的即可。Developer Portal 只有英文介面。

## 名詞先講清楚

- **Developer Portal(開發者後台)**:Discord 專門給開發者建立機器人的網站。
- **Application(應用程式)**:Developer Portal 裡的一個專案,你的機器人屬於它。
- **Bot(機器人)**:Discord 上由程式控制的帳號。agent 就是透過它收發訊息。
- **Token(權杖)**:機器人的「密碼」。程式拿著它,Discord 才相信「這支程式就是你的機器人」。
- **Intent**:機器人事先向 Discord 聲明「我需要收哪一類資料」的開關。

---

## 🔴 先讀這一段:bot token 的規則

> ### bot token 絕對不能:
> - ❌ **貼給任何人**(同學、朋友、老師、客服都不行)
> - ❌ **貼進這個對話**(包含和 Claude 的任何對話視窗)
> - ❌ **commit 進 git**(也就是不能出現在 GitHub 上)
> - ❌ 截圖時露出來
> - ❌ 寫在程式碼、README、筆記軟體的公開頁面裡
>
> **為什麼這麼嚴格**:誰拿到 token,誰就能完全操控你的機器人 —— 用它在你的 Server(以及它加入的任何地方)發訊息、讀頻道訊息。而且 Discord 只會讓你看到 token **一次**。
>
> **token 只應該存在一個地方**:你電腦上專案資料夾裡的 `.env` 檔(這個檔案已經被 `.gitignore` 擋住,不會被 git 收進去)。
>
> **萬一不小心貼出去了**:馬上回到 Developer Portal,按 **Reset Token**(步驟見下面「三、取得 token」),舊的 token 立刻失效。不用慌,但要立刻做。

---

## 一、建立 application 與 bot

1. 用瀏覽器打開 <https://discord.com/developers/applications>。
2. 如果要你登入,用你平常的 Discord 帳號登入。
3. 點畫面右上角藍紫色的 **「New Application」**。
4. 在「**Name**」欄位輸入名稱,例如 `Foodie`。
5. 勾選「I have read and agree to the Discord Developer Terms of Service and Developer Policy」(同意條款)。
6. 點 **「Create」**。
7. 你會進入這個 application 的頁面(「General Information」)。左邊有一排選單。

> 在新版 Developer Portal,建立 application 的同時就已經替你建好一個 bot 帳號了,不需要另外再按「Add Bot」。

### 讓只有你能邀請這個 bot

1. 左邊選單點 **「Bot」**。
2. 往下找到「**Public Bot**」,把開關**關掉**(變成灰色)。
   - 意思:只有你(application 的主人)能把這個 bot 邀進 Server,別人拿到連結也不能自己邀。
3. 找到「**Requires OAuth2 Code Grant**」,確認它是**關閉**的(預設就是關)。
4. 如果頁面底部跳出「**Save Changes**」的黑色條,點它存檔。

---

## 二、打開 Message Content Intent(一定要)

### 為什麼一定要

Discord 預設不讓機器人看「訊息的內容」,也就是**看不到訊息附帶的圖片**,只會收到空白的訊息。這個 agent 的工作就是看別人傳的照片,所以必須明確打開 **Message Content Intent**,Discord 才會把圖片附件交給它。

**如果沒打開**,最常見的症狀是:bot 登入成功、顯示在線,但傳照片它完全沒反應(或程式啟動時直接報錯,說缺少 privileged intent)。

### 步驟

1. 左邊選單點 **「Bot」**。
2. 往下捲,找到「**Privileged Gateway Intents**」這一區(有三個開關)。
3. 把「**MESSAGE CONTENT INTENT**」的開關**打開**(變成藍色)。
4. 另外兩個(**Presence Intent**、**Server Members Intent**)**保持關閉**,這個 agent 用不到,少開比較安全。
5. 按下頁面底部出現的 **「Save Changes」**。**沒按存檔等於沒開。**

**確認**:重新整理頁面,Message Content Intent 仍然是打開的。

> 這個機器人只在你自己的 Server 運作,而且加入的 Server 少於 100 個,所以可以直接打開這個開關,不需要送審。

---

## 三、取得 bot token

> 🔴 做這一步之前,請再看一次上面「bot token 的規則」。身邊沒人看你的螢幕、不要正在分享畫面、不要正在錄影。

1. 左邊選單點 **「Bot」**。
2. 找到「**Token**」這一區,點 **「Reset Token」**。
3. 跳出確認視窗,點 **「Yes, do it!」**。
4. Discord 可能會要你輸入密碼或兩步驟驗證碼,照做。
5. 畫面上會出現一長串字,這就是 **token**(通常有 70 個字以上,中間有兩個小數點)。
6. 點旁邊的 **「Copy」**,複製到剪貼簿。

**Token 只會顯示這一次。** 離開頁面或重新整理後就看不到了,忘了只能再按一次 Reset Token 產生新的(舊的會失效)。

**先不要貼到任何地方**,繼續做完下面的步驟,最後直接貼進 `.env`(見第五節)。

---

## 四、選權限,並把 bot 邀進你的 Server

### 這個 agent 需要的權限(只要四個)

| 權限(英文) | 中文意思 | 數值 | 為什麼需要 |
|---|---|---|---|
| **View Channels** | 檢視頻道 | 1024 | 看得到 `#food-log`,才讀得到裡面的照片 |
| **Send Messages** | 傳送訊息 | 2048 | 回覆分析結果 |
| **Add Reactions** | 新增反應 | 64 | 收到照片時,在那則訊息上加 ⏳ 表示「收到了,排隊中」;處理完會把 ⏳ 拿掉 |
| **Read Message History** | 讀取訊息歷史 | 65536 | 回覆某一則訊息、對舊訊息加反應時,Discord 要求要有這個權限 |

四個加起來是 **68672**。

**不要**勾 Administrator(管理員)或其他權限。權限越少,萬一出事損害越小。

**沒有 Add Reactions 會怎樣**:程式不會當掉,照樣分析、記錄、回覆,只是看不到 ⏳,終端機會印一次警告。所以它是「體驗用」的權限,但需求要求有 ⏳,所以請授權。

> 機器人「把自己加的 ⏳ 拿掉」「回覆訊息」不需要額外的管理權限,不要勾 Manage Messages。

### 產生邀請連結

1. 在 Developer Portal 左邊選單點 **「OAuth2」**。
2. 往下捲到「**OAuth2 URL Generator**」這一區。
3. 在「**Scopes**」(範圍)裡,只勾 **`bot`**。
   - 勾了之後,下面會多出一個「**Bot Permissions**」(機器人權限)區塊。
   - **不要**勾 `applications.commands`,這個 agent 不用斜線指令。
4. 在「**Bot Permissions**」裡,只勾這四個:
   - ☑ **View Channels**(在 General Permissions 底下)
   - ☑ **Send Messages**(在 Text Permissions 底下)
   - ☑ **Add Reactions**(在 Text Permissions 底下)
   - ☑ **Read Message History**(在 Text Permissions 底下)
5. 如果頁面有「**Integration Type**」,選 **Guild Install**。
6. 往最下面捲,看到「**Generated URL**」,點旁邊的 **「Copy」**。

> 做個核對:這四個權限加起來的「權限數字」是 `68672`。生成的網址裡會有 `permissions=68672`。如果不是,回去檢查勾了哪些。

### 也可以自己組連結(已經建好 application 時比較快)

把下面網址裡的 `<APPLICATION_ID>` 換成你的 Application ID(Developer Portal → 你的 application → **General Information** → **Application ID**,是一串 18~19 位的數字,不是機密):

```
https://discord.com/oauth2/authorize?client_id=<APPLICATION_ID>&scope=bot&permissions=68672
```

### 之前已經邀請過 bot,現在要補權限(重新授權)

不用把 bot 踢掉再加。用上面的連結(`permissions=68672`)再走一次「邀進你的 Server」的步驟,選同一個 Server,Discord 會把權限更新成這四個。做完後到 Server 設定 → 身分組 → 找到 Foodie 的身分組,確認四個權限都有打勾。

如果 `#food-log` 頻道自己有設定權限覆蓋(頻道設定 → 權限),要確認沒有把 Foodie 的 **Add Reactions** 設成禁止(❌)。

### 邀進你的 Server

這個邀請網址**不是機密**(它不含 token),可以安全複製使用。

1. 把剛剛複製的網址貼到瀏覽器網址列,按 Enter。
2. 如果要登入,用你的 Discord 帳號登入。
3. 畫面會問「**Add to server**」。點下拉選單,選**你自己的 Server**(例如「Foodie 測試」)。
   - 如果下拉選單裡沒有你的 Server,表示你登入的帳號不是這個 Server 的擁有者或沒有「管理伺服器」權限,換回建立 Server 的那個帳號。
4. 點 **「繼續」(Continue)**。
5. 看一遍它列出的權限,應該只有那四個,點 **「授權」(Authorize)**。
6. 若出現「我不是機器人」驗證,照著做。
7. 看到「**已授權**」(Authorized)就完成了。

### 確認 bot 在你的 Server 裡

1. 回到 Discord,進入你的 Server。
2. 看畫面**最右邊的成員清單**(沒看到的話,點右上角的人像圖示)。
3. 你應該看到「Foodie」(你取的名字),旁邊有一個 **BOT** 標籤。
   - 它現在是**離線**(灰色)的,這是正常的 —— 因為程式還沒啟動。程式跑起來之後才會變成在線。

---

## 五、把 token 和 CHANNEL_ID 放進 `.env`

> 🔴 token 只放在這個檔案裡,其他地方都不要貼。

`.env` 是放在專案資料夾的純文字設定檔。專案資料夾是 `C:\Users\a0939\foodie`。

### 用 VS Code 建立(建議,最不容易出錯)

你的電腦有 VS Code,用它最簡單:

1. 打開 VS Code,選 **「檔案」→「開啟資料夾」**,選 `C:\Users\a0939\foodie`。
2. 在左邊檔案清單的空白處按右鍵,選 **「新增檔案」**。
3. 檔名輸入 **`.env`**(**前面有一個點,後面沒有任何副檔名**),按 Enter。
4. 貼上下面四行,把值換成你自己的:

```
DISCORD_TOKEN=貼上你剛剛複製的 token
CHANNEL_ID=貼上第一份文件拿到的頻道 ID
CLAUDE_MODEL=claude-sonnet-5-5
DATA_DIR=D:\foodie-data
```

5. 注意:
   - `=` 前後**不要有空白**。
   - 值**不要加引號**。
   - `DISCORD_TOKEN` 和 `CHANNEL_ID` 一定要換成你自己的。
   - `DATA_DIR` 是紀錄與照片存放位置。建議放在**專案資料夾的外面**(這裡舉例 `D:\foodie-data`,你可以改成任何你喜歡、不在 `foodie` 資料夾裡面的位置)。資料夾不存在也沒關係,程式之後會自己建。
6. 按 **Ctrl + S** 存檔。

### 如果用「記事本」建立

記事本很容易偷偷把檔名存成 `.env.txt`,那樣程式讀不到。如果一定要用:

1. 儲存時,「**存檔類型**」選 **「所有檔案 (*.*)」**。
2. 「**檔案名稱**」輸入 **`.env`**(要含引號也可以:`".env"`)。
3. 「**編碼**」選 **UTF-8**。
4. 存到 `C:\Users\a0939\foodie`。
5. 到檔案總管檢查:選單 **「檢視」→「顯示」→ 勾選「檔案副檔名」**,確認檔名是 `.env`,不是 `.env.txt`。

### 確認它不會被 commit

1. 打開 PowerShell,進入專案資料夾(`cd C:\Users\a0939\foodie`)。
2. 輸入 `git status` 按 Enter。
3. **在列出的檔案裡,不應該看到 `.env`。** 看不到才是對的(它被 `.gitignore` 擋住了)。
4. 如果你看到 `.env` 出現在清單裡,**不要 commit**,先告訴我,我們一起查原因。

---

## 完成檢查

- [ ] Developer Portal 有一個 application(例如 `Foodie`)
- [ ] **Public Bot** 已關閉
- [ ] **Message Content Intent** 已打開,且已按 Save Changes
- [ ] 邀請網址只勾了 `bot` 與 View Channels / Send Messages / Add Reactions / Read Message History,網址含 `permissions=68672`
- [ ] 你的 Server 成員清單看得到 Foodie(離線,有 BOT 標籤)
- [ ] 專案資料夾有 `.env`,裡面有四個項目,檔名不是 `.env.txt`
- [ ] `git status` 看不到 `.env`
- [ ] token 沒有貼給任何人、沒有貼進任何對話

## 常見問題

| 狀況 | 可能原因與做法 |
|---|---|
| 邀請網址打開後,下拉選單沒有我的 Server | 你登入的 Discord 帳號不是 Server 擁有者,換成建立 Server 的帳號 |
| 之後程式啟動,bot 在線但傳照片沒反應 | 99% 是 Message Content Intent 沒打開、或沒按 Save Changes。回到第二節檢查 |
| 之後程式啟動,出現「Message Content Intent 沒打開」 | 同上。程式會直接退出並告訴你這句話,不是壞掉 |
| 傳照片後沒有 ⏳,但有分析結果 | 少了 Add Reactions 權限(或頻道把它禁止了)。用 `permissions=68672` 的連結重新授權 |
| ⏳ 一直不消失 | 正常情況下處理完或失敗都會拿掉。如果是程式被強制關閉(例如斷電、直接關視窗)時還在排隊的訊息,⏳ 會留著,手動點掉即可 |
| 之後程式啟動,出現 `Improper token` 或登入失敗 | token 複製不完整、前後多了空白、或已經被 Reset 過。重新 Reset Token 取一個新的,貼進 `.env` |
| bot 在線,但不在 `#food-log` 回覆 | 檢查 `CHANNEL_ID` 是不是 `#food-log` 的 ID(不是 Server 的 ID);bot 的權限被頻道設定擋住也會這樣 |
| 不小心把 token 貼出去了 | 馬上到 Developer Portal → Bot → **Reset Token**,舊的立刻失效,再把新的貼進 `.env` |
