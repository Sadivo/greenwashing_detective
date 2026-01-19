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

## 五、程式架構

greenwashing_detective_project/
├── app.py                      # [主程式] Flask 網頁伺服器入口
├── app_llm_rich_test.py        # [測試] LLM 功能測試入口
├── config.py                   # [設定] 專案配置與環境變數載入
├── requirements.txt            # [依賴] Python 套件清單
├── SQL_table.txt               # [資料庫] Table Schema 定義文件
├── .env.example                # [環境] 環境變數範例檔 (API Key 設定)
├── pyproject.toml              # [配置] 專案工具配置
├── README.md                   # [文件] 專案說明文件
│
├── src/                        # [核心邏輯] 後端功能模組
│   ├── crawler_esgReport.py    # ESG 永續報告書爬蟲
│   ├── crawler_news.py         # 相關新聞爬蟲
│   ├── gemini_api.py           # Google Gemini LLM API 串接
│   ├── pplx_api.py             # Perplexity API 串接
│   ├── calculate_esg.py        # ESG 分數計算邏輯
│   ├── db_service.py           # 資料庫連線與 CRUD 操作
│   ├── word_cloud.py           # 文字雲圖片生成工具
│   └── run_prompt2_gemini.py   # 特定 Prompt 執行腳本
│
├── static/                     # [靜態資源] 前端資源檔案
│   ├── css/                    # 樣式表 (style.css)
│   ├── js/                     # 前端腳本 (script.js)
│   ├── images/                 # 圖片資源 (生成的文字雲、風險圖示)
│   └── data/                   # 靜態資料檔
│       ├── dict/               # 分析用字典 (esg_dict, fuzzy_dict, stopword)
│       ├── SASB_weightMap.json # SASB 權重映射表
│       ├── msci_flag.json      # MSCI 評級對照
│       └── tw_listed_companies.json # 台灣上市公司清單
│
├── templates/                  # [前端模板] HTML 檔案
│   └── index.html              # 首頁介面
│
├── change/                     # [開發文件] 變更紀錄與規劃書
│   ├── 整合規劃書.md            # 系統整合架構說明
│   └── t1/ ~ t6/               # 各階段任務變更詳情
│
└── temp_data/                  # [暫存] 運行時產生的暫存檔 (通常不納入版控)
    ├── esgReport/              # 下載的 PDF 報告
    └── prompt*_json/           # LLM 分析結果緩存

# process flowchart

```mermaid
flowchart TD
    %% --- 樣式定義 ---
    linkStyle default stroke:#000,stroke-width:1px;
    classDef start_end fill:#f2d08a,stroke:#333,stroke-width:1px,color:#000;
    classDef process fill:#eee,stroke:#999,stroke-width:1px,color:#333;
    classDef decision fill:#fff4dd,stroke:#d4a017,stroke-width:2px,color:#000;
    classDef program fill:#034f4f,stroke:#333,stroke-width:1px,color:#fff;
    classDef db fill:#e1f5fe,stroke:#01579b,stroke-width:2px,color:#000;
    classDef outputData fill:#fff3e0,stroke:#ff9800,stroke-dasharray: 5 5,color:#000;

    %% --- 泳道 1: Frontend ---
    subgraph UI [使用者互動層]
        Start(["index.html<br/>Dashboard"]):::start_end
        Input["User Input<br/>搜尋關鍵字"]:::process
        End(["index.html<br/>結果展示"]):::start_end
    end

    %% --- 泳道 2: Processing ---
    subgraph App [後端邏輯處理]
        JS{"script.js<br/>發送請求"}:::decision
        CheckDB("app.py<br/>檢查資料狀態"):::program
        Crawler("crawler_esgReport.py<br/>PDF 爬蟲"):::program
        Gemini("gemini_api<br/>P1:內文比對"):::program
        prompt2("run_prompt2_gemini.py<br/>P2:外部驗證"):::program
        news("crawler_news.py<br/>新聞爬蟲"):::program
        Pplx("pplx_api.py<br/>URL 外部驗證"):::program
        Calc("calculate_esg.py<br/>風險分數計算"):::program
        Word_cloud("word_cloud.py<br/>生成詞雲"):::program
        pymysql_insert("db_service.py<br/>寫入資料庫"):::program
        Flask("app.py<br/>Flask API Server"):::program
    end

    %% --- 泳道 3: Data ---
    subgraph Data [數據管理層]
        PDF[["永續報告書<br/>PDF 檔案"]]:::outputData
        news["新聞<br/>JSON"]:::outputData
        JSON1["內文比對結果<br/>JSON"]:::outputData
        JSON2["外部驗證結果<br/>JSON"]:::outputData
        JSON3["網頁確認結果<br/>JSON"]:::outputData
        DB_Node[("MySQL<br/>資料庫")]:::db
        wc_json["詞雲<br/>JSON"]:::outputData
    end

    %% --- 連線邏輯 ---
    Start --> Input --> JS
    JS --> CheckDB
    
    %% 資料檢查路徑
    DB_Node -.->|讀取狀態| CheckDB
    CheckDB -- 無資料 --> Crawler
    CheckDB -- 有資料 --> End

    %% 爬蟲與 AI 處理流
    Crawler --> PDF --> Gemini
    Gemini --> JSON1
    prompt2 --> JSON2
    Pplx --> JSON3

    %% 詞雲生成流
    PDF --> Word_cloud --> wc_json
    wc_json --> Flask

    %% JSON 數據分流
    JSON2 --> Pplx
    JSON3 --> Calc --> Flask
    JSON3 --> pymysql_insert -.->|寫入| DB_Node
    DB_Node -.->|讀取| Flask
    JSON1 --> news --> prompt2

    %% 最終回傳展示
    Flask --> End

    %% 調整視覺間距
    style UI fill:#f9f9f9,stroke:#ddd
    style App fill:#f5f5f5,stroke:#ddd
    style Data fill:#f9f9f9,stroke:#ddd