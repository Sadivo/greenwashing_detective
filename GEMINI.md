# GEMINI.md - 專案指令與上下文指南

本檔案為 AI 助手提供專案 `greenwashing-detective` 的核心架構、開發規範與運作指令。

## 1. 專案概覽 (Project Overview)
**ESG 抓耙子 (Greenwashing Detective)** 是一款自動化審閱 ESG 報告書並量化「漂綠 (Greenwashing)」風險的工具。它結合了國際永續準則 (SASB) 與多階段 AI 驗證流程。

### 核心技術棧
- **後端框架**: Python Flask
- **AI 引擎**: 
  - **Gemini 1.5 Pro**: 用於 PDF 文本解析、SASB 議題識別及新聞矛盾分析。
  - **Perplexity AI**: 用於實時聯網驗證證據來源的真實性。
- **爬蟲技術**: 
  - **PDF 爬蟲**: 從公開資訊觀測站 (MOPS) 自動下載報告。
  - **新聞爬蟲**: 整合 GNews API 獲取企業負面新聞。
- **數據處理**: 
  - **SASB 框架**: 基於 `static/data/SASB_weightMap.json` 進行產業權重計算。
  - **NLP**: Jieba 斷詞、WordCloud 生成。
- **資料庫**: MySQL (支援本地 TCP 與 GCP Cloud SQL Unix Socket)。
- **雲端部署**: Google Cloud Platform (Cloud Run, Cloud SQL, GCS)。

## 2. 運行與開發指令 (Building and Running)

### 環境管理 (使用 uv)
根據專案規範，一律使用 `uv` 進行環境管理：
```bash
# 安裝依賴
uv pip install -r requirements.txt

# 啟動 Web 應用
uv run app.py

# 啟動 Line Bot (於 Line 目錄)
cd Line
uv run app_line.py
```

### 資料庫初始化
1. 確保 MySQL 已啟動並建立 `greenwash` 資料庫。
2. 執行 `SQL_table.txt` 腳本建置表結構。

### 環境變數 (.env)
需配置以下關鍵變數：
- `GOOGLE_API_KEY`: Gemini API 密鑰。
- `PPLX_API_KEY`: Perplexity API 密鑰。
- `DB_USER`, `DB_PASSWORD`, `DB_NAME`: 資料庫設定。
- `INSTANCE_CONNECTION_NAME`: (選填) 用於 GCP Cloud SQL 連線。
- `LINE_CHANNEL_ACCESS_TOKEN`, `LINE_CHANNEL_SECRET`: Line Bot 設定。

## 3. 核心分析流程 (Pipeline)
系統採用六階段自動化流程，支援**斷點續傳**：
1. **Stage 1 (PDF 下載)**: `crawler_esgReport.py`。
2. **Stage 2 (AI 掃描 & 文字雲)**: `gemini_api.py` (分析 SASB 聲稱) 與 `word_cloud.py`。
3. **Stage 3 (新聞比對)**: `crawler_news.py` 抓取與議題相關的新聞。
4. **Stage 4 (AI 矛盾分析)**: `run_prompt2_gemini.py` 比對報告聲稱與新聞證據。
5. **Stage 5 (來源驗證)**: `pplx_api.py` 驗證證據 URL 的有效性。
6. **Stage 6 (入庫與計算)**: `db_service.py` 儲存結果，`calculate_esg.py` 計算最終風險分數。

## 4. 開發規範 (Development Conventions)

### 模組化與路徑
- 所有目錄路徑應透過 `config.py` 中的 `PATHS` 獲取，避免硬編碼字串。
- 暫存資料存放在 `temp_data/` 下的對應子目錄，流程完成後應調用 `app.py` 中的 `cleanup_temp_files` 清理。

### 斷點續傳機制
- 系統透過 `company` 表中的 `analysis_status` 紀錄進度（stage1~stage6）。
- 開發新功能時需確保狀態轉換的正確性，並參考 `src/recovery_utils.py` 進行狀態判定。

### 錯誤處理
- 在 `app.py` 中使用 `mark_processing_start` 與 `mark_processing_end` 標記活躍任務，避免重複執行。
- AI 分析失敗時應將狀態更新為 `failed`。

### 前端互動
- 前端使用 `static/js/script.js` 與 `/api/query_company` 以及 `/api/check_progress/<esg_id>` 進行非同步互動。

---
*註：本文件由 Gemini CLI 自動生成，作為未來互動的指令上下文。*
