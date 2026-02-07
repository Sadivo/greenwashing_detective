# 別讓永續變成口號！ESG抓耙子：ESG綠色洗白風險儀表板

**ESG 抓耙子** 是一款結合 LLM 與 國際永續準則，自動化審閱 ESG 報告書並量化企業漂綠風險的工具。

---

### 為什麼要做這個專案？

國際企業(Apple、Google、Microsoft等)皆積極推行 ESG 永續發展，並嚴格限制供應鏈碳排放；台灣金管會規定 2025 年起，全體上市櫃公司均應申報永續報告書；2026 年起正式開徵碳費。企業永續發展不再是選擇題，而是必答題。

但一份報告書內容動輒數百頁，對投資人或監管機構來說，要找出「說一套做一套」的 **漂綠（Greenwashing)** 行為就像大海撈針。

我們的目標是透過 AI 的力量，自動化地審閱這些報告，並抓取外部新聞進行「實話對決」，讓企業的永續主張無所遁形。

---

## 成果展示 (介面截圖)
* **專案網頁：**[ESG綠色洗白風險儀表板](https://esg-app-546777032880.asia-northeast1.run.app/)

* **視覺化儀表板：** 一眼看出這家公司的 ESG 風險等級。
> ![Dashboard 風險標籤示意圖](static/images/dashboard.png)

* **自適應版面 (RWD)：** 無論是用電腦深入研究，還是用手機隨手查詢，版面都會自動調整，提供最舒適的閱讀體驗。
> <img src="static/images/RWD.png" width="600" alt="RWD">

* **分析清單：** 列出「企業主張」vs「外部證據」的對比，給每個項目出風險分數。
> ![風險分數清單](static/images/anly_list.png)

* **SASB 產業權重分布：** 快速看出該產業的重點在哪裡。
> ![SASB 產業權重分布](static/images/SASB_MAP.png)

* **關鍵字雲：** 快速掌握報告書的重點是什麼。
> ![文字雲](static/images/cloud_word.png)

* **Line Bot 隨身查：** 透過 Line Bot 查詢公司 ESG 風險分數。
> <img src="static/images/line_bot.png" width="600" alt="Line bot">

---

## 核心功能：多端互動，資訊不漏接

-  與其只叫 AI 總結摘要，我們設計了一套嚴謹的**三階段驗證流程**：

    - **AI 深入掃描 (P1)：** 依據國際權威的 **SASB 框架**與學術界公認的 **Clarkson 2008 評分邏輯**，對 PDF 進行逐頁分析，找出潛在的誇大疑點。
    - **即時新聞交叉比對 (P2)：** 串接 **GNews API** 抓取與該議題相關的新聞。如果報告說環境保護做得很好，但新聞卻有汙染裁罰紀錄，系統會自動標記矛盾。
    - **證據真實性檢驗 (P3)：** 擔心 AI 產生幻覺（Hallucination）或網址失效？我們整合了 **Perplexity AI** 自動修復並驗證所有證據來源的真實性。

- Line Bot 隨身查：

    - 我們特別開發了專屬的 Line Bot，使用者只要輸入公司代碼，就能秒查資料庫中的 ESG 總分。
    - 機器人會提供外連網址，直接引導使用者回到主網站查看更精確的分析報告。
    - 技術亮點：這是一個不依賴官方 SDK，完全由 Flask 從底層實作的 Line Bot，展現對 Webhook 與 API 協議的掌握度。

- 全裝置自適應 (RWD)：網站具備自適應功能，無論是用電腦大螢幕進行深度研究，還是用手機隨手查詢，都能享有流暢的閱讀體驗。

---

## 技術架構

- **前端開發：** HTML5, CSS3 (RWD 響應式設計), JavaScript (控制頁面互動與圖表呈現)。
- **自動化資料獲取：**
    - **報告書爬蟲：** 自動從 ESG 平台抓取指定年度與公司的 PDF 報告。
    - **外部新聞蒐集：** 整合 GNews 等工具，並行爬取相關企業之 ESG 負面或爭議新聞。
- **後端框架：** Python Flask 負責處理 API 請求、任務調度與流程控制。
- **AI 深度解析 (LLM 串接)：**
    - **內文比對 (Prompt 1)：** 提取 SASB 相關議題、具體聲稱及其對應頁碼，並針對前後文做比對，識別是否存在不一致。
    - **外部查證 (Prompt 2)：** 將公司聲稱與外部證據比對，識別是否存在不一致。
    - **可靠性驗證 (Prompt 3)：** 利用 Perplexity API 進行實時聯網，若原始連結失效，自動搜尋第三方可靠來源（排除官網），確保證據力。
- **自然語言處理：** NLP 工具 使用 Jieba 斷詞處理、自定義 ESG/Fuzzy/stopwords 字典、PDFPlumber 文本提取。
- **雲端與資料庫 (GCP)：**
    - **Cloud Run：** 容器化部署 Web 服務與 LINE Bot。
    - **Cloud SQL (MySQL)：** 結構化儲存企業資料 及 分析結果
    - **Cloud Storage：** 儲存 PDF 報告、圖片、SASB 權重地圖、AI 產生的 JSON 檔。
    - **Artifact Registry：** 管理 Docker image。

---

## 系統架構圖

我們將複雜的流程拆解為清晰的模組化結構：

```mermaid
graph TB
    %% 使用者介面
    User[使用者] --> WebUI[Web 介面 RWD]
    User --> LineBot[LINE Bot]
    
    %% Flask 核心
    WebUI & LineBot --> Flask[Flask Web Server]
    
    %% 路由分流
    Flask --> Query{路由判斷}
    
    %% 查詢路徑
    Query -->|查詢請求| DB[(MySQL Database)]
    DB --> Result[回傳分析報告]
    
    %% 分析路徑 - 六階段流程
    Query -->|分析請求| Stage1[Stage 1: PDF 下載<br/>crawler_esgReport]
    
    Stage1 --> Parallel{平行處理}
    Parallel --> Stage2A[Stage 2A: AI 深入掃描<br/>Gemini + SASB 框架]
    Parallel --> Stage2B[Stage 2B: 文字雲生成<br/>word_cloud]
    
    Stage2A --> Stage3[Stage 3: 新聞交叉比對<br/>GNews API 多執行緒]
    
    Stage3 --> Stage4[Stage 4: AI 驗證與評分<br/>Gemini 二次分析]
    
    Stage4 --> Stage5[Stage 5: 來源驗證<br/>Perplexity AI]
    
    Stage5 --> Stage6[Stage 6: 存入資料庫]
    Stage2B --> Stage6
    
    Stage6 --> DB
    
    %% 樣式
    classDef blueNode fill:#4A90E2,stroke:#2E5C8A,stroke-width:2px,color:#fff
    classDef greenNode fill:#50C878,stroke:#2D7A4A,stroke-width:2px,color:#fff
    classDef redNode fill:#FF6B6B,stroke:#C44444,stroke-width:2px,color:#fff
    classDef orangeNode fill:#FFB347,stroke:#CC8936,stroke-width:2px,color:#fff
    
    class User,WebUI,LineBot blueNode
    class Flask,Query greenNode
    class Stage1,Stage2A,Stage2B,Stage3,Stage4,Stage5,Parallel redNode
    class DB,Stage6,Result orangeNode
```

---

## 技術實作：我們如何解決遇到的問題？

在開發過程中，我們遇到不少挑戰，來看我們如何「讓系統更耐操」：
* **模組化大亂鬥：** 專案初期各項功能各跑各的，我們學會了「模組化」，將爬蟲、AI、資料庫操作整合進統一的 Pipeline，確保自動化流程一氣呵成。
* **自動化爬蟲 pipeline：** 公開資訊觀測站的 PDF 多為外連到企業官方網站，格式雜亂讓我們一度在初期就卡住，我們發現多家網站背後都連向了『ESG 數位平台』，透過分析背後邏輯成功設計了自動化爬蟲功能。
* **新聞搜尋開天窗：** GNews 搜尋常因為關鍵字問題而抓不到東西，我們實作了三層 Fallback 機制，讓系統能自動從「特定詞」切換到「產業關鍵字」再到「基本組合」，確保分析不中斷。
* **多執行緒搜尋：** 新聞搜尋受限於GNews API的限制，實際上是最耗時的階段，我們改用多執行緒同時抓取多個議題的資料，不再讓系統傻傻排隊。
* **平行處理：** 我們把「文字雲生成」跟「AI 分析」拆開同步執行，省下部分等待時間。
* **斷點續傳機制：** 面對 API 斷線或系統意外中斷，我們實作了狀態紀錄功能。系統能自動識別資料庫中的 stageN 狀態，當使用者重新整理或重啟時，可以選擇 **從斷點繼續** 而不需要浪費額外的 API 額度重頭來過。

---

## 如何在本地執行 (Local Development)

想在自己的電腦上跑跑看？請按照以下步驟操作：

1.  **環境準備**
    *   確保已安裝 Python 3.9+ 與 MySQL。
    *   複製 `.env.example` 並重新命名為 `.env`，填入您的 API Keys。
    *   **注意：** 本地執行時，請確保 `.env` 中的 `INSTANCE_CONNECTION_NAME` 為空值，系統才會自動切換至 Local TCP 連線模式。

2.  **安裝套件**
    ```bash
    pip install -r requirements.txt
    ```

3.  **初始化資料庫**
    *   建立 MySQL 資料庫 (預設名稱: `greenwash`)。
    *   執行專案目錄下的 `SQL_table.txt` 腳本，完成資料表建置與測試資料匯入。

4.  **啟動專案**
    ```bash
    python app.py
    ```
    打開瀏覽器前往 `http://localhost:5000`

---

## 雲端部署 (GCP)

本專案已完整遷移至 Google Cloud Platform (GCP)，採用容器化架構，確保環境一致性：

1.  **專案準備**：
    *   在 GCP Console 建立專案，並啟用 Cloud Run, Cloud SQL, Artifact Registry API。
    *   準備好 `.env.example` 中的環境變數 (資料庫連線、API Keys)。

2.  **核心元件與部署建議**：
    *   **資料庫 (Cloud SQL)**：建立 MySQL 8.0 實例，建議開啟 Public IP 但限制存取來源，或使用 Cloud SQL Auth Proxy。
    *   **儲存 (Cloud Storage)**：建立 Bucket 用於存放 PDF 報告與暫存 JSON。
    *   **建置 (Cloud Build)**：可直接連結 GitHub 觸發自動建置，或使用 Cloud Shell 執行 `gcloud builds submit` 產出 Docker Image。
    *   **部署 (Cloud Run)**：選擇剛建置的 Image，**注意需配置至少 2GiB 記憶體** (處理 PDF 需求)，並在「變數」頁面填入環境變數。

---

## 未來優化方向 (Roadmap)
雖然系統已經跑得很穩，但身為開發者，我們還有更多想玩的：

- 更多元的資料來源： 整合「環保署處分紀錄」與「勞基法違規」等政府 Open Data，讓 AI 不只看新聞，還能查企業的違規「黑歷史」。

- 專屬「ESG 顧問」： 透過檢索增強生成 (RAG)，讓使用者不只能看數據，還能跟網頁內嵌的聊天助手提問或瞎聊，讓系統變得「有生命」。

- 機器學習模型：導入定量數據分析，利用過往漂綠案例訓練模型，實現對企業數據造假的「異常偵測」與預警標籤。