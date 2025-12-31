# Greenwashing Detective Project

## 一、 下載 GitHub Desktop
請先至官網下載並安裝 [GitHub Desktop](https://desktop.github.com/)。

## 二、 把專案領回家 (Clone)
1. 打開 **GitHub Desktop** 並登入你的帳號。
2. 點擊 `File` > `Clone Repository`。
3. 選取 `greenwashing_detective_project`，並選擇本地端的存放路徑。
4. **注意：** 資料夾路徑盡量**不要包含中文**，以避免程式執行時報錯。

## 三、 檔案對應說明
以下為專案主要檔案與功能對照：

* **資料庫服務：** `db_service.py` (pymysql)
* **主程式入口：** `app.py` (flask)
* **AI 介面：**
    * `gemini_api.py` (Gemini)
    * `pplx_api.py` (Perplexity)
* **爬蟲程式：** `crawler_esgReport`
* **前端網頁：**
    * **HTML:** `/templates/index.html`
    * **CSS:** `/static/css/style.css`
    * **JS:** `/static/js/script.js`

---

## 四、 工作步驟 (避免衝突)
為了確保多人協作順暢，請嚴格遵守以下流程：

1.  **同步進度：** 開工前先點擊 **Fetch origin / Pull**，確保本地端是最新版本。
2.  **建立分支：** 點擊 `Current Branch` > `New Branch`。
    * *命名格式建議：* `功能名稱_版本` (例如：`gemini_api_v2`)
3.  **提交變更：** 程式完成後，在 GitHub Desktop 進行 **Commit** 並點擊 **Publish branch**。
4.  **發起合併：** 回到 GitHub 網頁版點擊 **Compare & pull request**，並簡述修改內容。
5.  **完成：** 待管理員確認無誤後，即可進行合併（Merge）。