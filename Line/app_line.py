import os
import re
from urllib.parse import urlencode
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from flask import Flask, request, abort, render_template

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    QuickReply,
    QuickReplyItem,
    PostbackAction,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent, PostbackEvent

# =========================
#  設定 / Env
# =========================
load_dotenv()

LINE_CHANNEL_ACCESS_TOKEN = (os.getenv("LINE_CHANNEL_ACCESS_TOKEN") or "").strip()
LINE_CHANNEL_SECRET = (os.getenv("LINE_CHANNEL_SECRET") or "").strip()

DB_HOST = (os.getenv("DB_HOST") or "127.0.0.1").strip()
DB_PORT = int((os.getenv("DB_PORT") or "3306").strip())
DB_USER = (os.getenv("DB_USER") or "root").strip()
DB_PASSWORD = (os.getenv("DB_PASSWORD") or "").strip()
DB_NAME = (os.getenv("DB_NAME") or "").strip()

DB_TABLE_COMPANY = (os.getenv("DB_TABLE_COMPANY") or "company").strip()

# company 表欄位（可用 env 覆寫）
DB_COL_COMPANY_CODE = (os.getenv("DB_COL_COMPANY_CODE") or "company_code").strip()
DB_COL_COMPANY_NAME = (os.getenv("DB_COL_COMPANY_NAME") or "company_name").strip()
DB_COL_REPORT_YEAR = (os.getenv("DB_COL_REPORT_YEAR") or "Report_year").strip()
DB_COL_TOTAL_SCORE = (os.getenv("DB_COL_TOTAL_SCORE") or "total_score").strip()

INSTANCE_CONNECTION_NAME = (os.getenv("INSTANCE_CONNECTION_NAME") or "").strip()
PORT = int((os.getenv("PORT") or "8080").strip())  # Cloud Run 預設給 8080

# alias map（可自行擴充）
ALIAS_MAP = {
    "亞泥": "亞洲水泥",
    "台積": "台積電",
    "中鋼": "中國鋼鐵",
    "聯發": "聯發科",
}

def require_line_env() -> None:
    missing = []
    if not LINE_CHANNEL_ACCESS_TOKEN:
        missing.append("LINE_CHANNEL_ACCESS_TOKEN")
    if not LINE_CHANNEL_SECRET:
        missing.append("LINE_CHANNEL_SECRET")
    if missing:
        raise RuntimeError("❌ 缺少 LINE 必要設定：" + ", ".join(missing))

def check_db_env() -> Tuple[bool, str]:
    # 不用在啟動就炸掉，改成用到 DB 才檢查
    if not DB_NAME:
        return False, "DB_NAME 尚未設定"
    if INSTANCE_CONNECTION_NAME:
        # Cloud SQL Socket 模式：DB_USER/DB_PASSWORD/DB_NAME 必須有
        if not DB_USER:
            return False, "DB_USER 尚未設定"
        # DB_PASSWORD 可能允許空（看你 DB），所以不強制
        return True, "OK"
    # TCP 模式：至少要 host/name/user
    if not DB_HOST:
        return False, "DB_HOST 尚未設定"
    if not DB_USER:
        return False, "DB_USER 尚未設定"
    return True, "OK"

require_line_env()

# =========================
#  Flask / LINE init
# =========================
app = Flask(__name__)
configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
api_client = ApiClient(configuration)
line_bot_api = MessagingApi(api_client)

# =========================
#  Session（記憶鎖定公司）
# =========================
user_sessions: Dict[str, Dict[str, Any]] = {}

def normalize(text: str) -> str:
    return (text or "").strip().replace(" ", "")

def is_trigger_a(norm: str) -> bool:
    return ("企業ESG查詢" in norm) or ("鎖定查詢" in norm) or (norm.upper() == "A")

def looks_like_company_input(norm: str) -> bool:
    return bool(re.fullmatch(r"\d{4}", norm)) or (len(norm) >= 2)

# =========================
#  DB helpers
# =========================
def _get_db_conn():
    unix_socket = f"/cloudsql/{INSTANCE_CONNECTION_NAME}" if INSTANCE_CONNECTION_NAME else None

    # 先檢查設定
    ok, msg = check_db_env()
    if not ok:
        raise RuntimeError(f"DB 設定不完整：{msg}")

    try:
        import pymysql  # type: ignore
        kwargs = dict(
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
        )
        if unix_socket:
            kwargs["unix_socket"] = unix_socket
        else:
            kwargs["host"] = DB_HOST
            kwargs["port"] = DB_PORT
        return pymysql.connect(**kwargs)

    except Exception:
        import mysql.connector  # type: ignore
        kwargs = dict(
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
        )
        if unix_socket:
            kwargs["unix_socket"] = unix_socket
        else:
            kwargs["host"] = DB_HOST
            kwargs["port"] = DB_PORT
        return mysql.connector.connect(**kwargs)

def _fetchone(conn, sql: str, params: tuple):
    try:
        cur = conn.cursor(dictionary=True)  # mysql-connector
    except TypeError:
        cur = conn.cursor()  # pymysql DictCursor
    cur.execute(sql, params)
    return cur.fetchone()

def _fetchall(conn, sql: str, params: tuple):
    try:
        cur = conn.cursor(dictionary=True)
    except TypeError:
        cur = conn.cursor()
    cur.execute(sql, params)
    return cur.fetchall() or []

def db_find_company_by_code(code4: str) -> Optional[Dict[str, Any]]:
    sql = (
        f"SELECT {DB_COL_COMPANY_CODE} AS company_code, "
        f"MIN({DB_COL_COMPANY_NAME}) AS company_name "
        f"FROM {DB_TABLE_COMPANY} "
        f"WHERE {DB_COL_COMPANY_CODE}=%s "
        f"GROUP BY {DB_COL_COMPANY_CODE} "
        f"LIMIT 1"
    )
    conn = _get_db_conn()
    try:
        row = _fetchone(conn, sql, (code4,))
        if not row:
            return None
        return {
            "company_code": str(row.get("company_code") or ""),
            "company_name": str(row.get("company_name") or ""),
        }
    finally:
        conn.close()

def db_search_companies_by_name(name_kw: str, limit: int = 5) -> List[Dict[str, str]]:
    sql = (
        f"SELECT {DB_COL_COMPANY_CODE} AS company_code, "
        f"MIN({DB_COL_COMPANY_NAME}) AS company_name "
        f"FROM {DB_TABLE_COMPANY} "
        f"WHERE {DB_COL_COMPANY_NAME} LIKE %s "
        f"GROUP BY {DB_COL_COMPANY_CODE} "
        f"ORDER BY {DB_COL_COMPANY_CODE} ASC "
        f"LIMIT {int(limit)}"
    )
    conn = _get_db_conn()
    try:
        rows = _fetchall(conn, sql, (f"%{name_kw}%",))
        return [{"company_code": str(r.get("company_code") or ""), "company_name": str(r.get("company_name") or "")} for r in rows]
    finally:
        conn.close()

def db_list_years(company_code: str) -> List[int]:
    sql = (
        f"SELECT DISTINCT {DB_COL_REPORT_YEAR} AS y "
        f"FROM {DB_TABLE_COMPANY} "
        f"WHERE {DB_COL_COMPANY_CODE}=%s "
        f"ORDER BY {DB_COL_REPORT_YEAR} DESC"
    )
    conn = _get_db_conn()
    try:
        rows = _fetchall(conn, sql, (company_code,))
        years: List[int] = []
        for r in rows:
            y = r.get("y")
            if y is None:
                continue
            try:
                years.append(int(y))
            except Exception:
                pass
        return years
    finally:
        conn.close()

def db_get_total_score(company_code: str, year: int) -> Optional[float]:
    sql = (
        f"SELECT {DB_COL_TOTAL_SCORE} AS total "
        f"FROM {DB_TABLE_COMPANY} "
        f"WHERE {DB_COL_COMPANY_CODE}=%s AND {DB_COL_REPORT_YEAR}=%s "
        f"LIMIT 1"
    )
    conn = _get_db_conn()
    try:
        row = _fetchone(conn, sql, (company_code, year))
        if not row:
            return None
        val = row.get("total")
        if val is None:
            return None
        return float(val)
    finally:
        conn.close()

# =========================
#  基本路由（讓 Cloud Run 好測）
# =========================
@app.get("/")
def root():
    return "OK - line-bot-cloud is running", 200

@app.get("/healthz")
def healthz():
    return {"ok": True}, 200

# =========================
#  LINE Callback
# =========================
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK", 200

@app.route("/dashboard", methods=["GET"])
def dashboard():
    company = (request.args.get("company") or "").strip()
    return render_template("dashboard.html", company=company)

# =========================
#  Reply helpers
# =========================
def send_reply(event, text: str, quick_reply: Optional[QuickReply] = None) -> None:
    msg = TextMessage(text=text, quick_reply=quick_reply)
    line_bot_api.reply_message(
        ReplyMessageRequest(reply_token=event.reply_token, messages=[msg])
    )

def build_main_quick_reply() -> QuickReply:
    items = [
        QuickReplyItem(action=PostbackAction(label="年份", data="ACTION=SHOW_YEARS")),
        QuickReplyItem(action=PostbackAction(label="Dashboard", data="ACTION=DASHBOARD")),
    ]
    return QuickReply(items=items)

def build_year_quick_reply(years: List[int]) -> QuickReply:
    items: List[QuickReplyItem] = []
    for y in years[:13]:
        items.append(QuickReplyItem(action=PostbackAction(label=str(y), data=f"YEAR={y}")))
    return QuickReply(items=items)

def risk_level_from_score(score: float) -> Dict[str, str]:
    if score >= 70:
        return {"level": "低風險", "emoji": "🟢"}
    if score >= 40:
        return {"level": "中風險", "emoji": "🟡"}
    return {"level": "高風險", "emoji": "🔴"}

def bar_10(score: float) -> str:
    s = max(0.0, min(100.0, score))
    filled = int(round(s / 10.0))
    filled = max(0, min(10, filled))
    return "■" * filled + "□" * (10 - filled)

def reply_db_error(event, e: Exception):
    # DB 爆了要講人話，別再假裝查無此公司
    send_reply(
        event,
        "⚠️ 目前資料庫連線/設定有問題，暫時無法查詢。\n"
        f"（提示：{type(e).__name__}，請到 Cloud Run logs 看詳細錯誤）"
    )

# =========================
#  Message handler（鎖定公司）
# =========================
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text or ""
    norm = normalize(text)

    if text == "專題目的(ESG分析)":
        send_reply(
            event,
            (
                "【專題目的說明】\n\n"
                "本專題以 LINE Bot 作為互動入口，結合資料庫與視覺化儀表板，\n"
                "提供使用者快速查詢企業 ESG 相關風險資訊。\n\n"
                "• 鎖定特定公司\n"
                "• 查看 ESG 風險評分摘要\n"
                "• 連結至 Dashboard 取得更完整的分析結果\n\n"
                "重點：可 Demo、流程穩定。"
            )
        )
        return

    if text == "操作流程":
        send_reply(
            event,
            (
                "【操作流程說明】\n\n"
                "1️⃣ Rich Menu 選「公司查詢」→ 輸入公司代碼/名稱\n"
                "2️⃣ 回傳 ESG 分數摘要 + Quick Reply\n"
                "3️⃣ 點「年份」選年度\n"
                "4️⃣ 點「Dashboard」開啟詳細頁\n"
            )
        )
        return

    sess = user_sessions.get(user_id, {"state": "IDLE"})
    state = sess.get("state", "IDLE")

    if is_trigger_a(norm):
        user_sessions[user_id] = {"state": "WAITING_COMPANY", **sess}
        send_reply(event, "請輸入公司代碼（4 碼）或公司名稱（例如：1102 / 亞泥）")
        return

    if looks_like_company_input(norm):
        search_key = ALIAS_MAP.get(norm, norm)

        # code
        if re.fullmatch(r"\d{4}", norm):
            try:
                row = db_find_company_by_code(norm)
            except Exception as e:
                print(f"DB 查詢失敗（company by code）：{e}")
                reply_db_error(event, e)
                return

            if not row or not row.get("company_name"):
                send_reply(event, "查無此公司，請輸入正確的公司代碼或公司名稱。")
                return

            user_sessions[user_id] = {
                "state": "LOCKED",
                "company_code": row["company_code"],
                "company_name": row["company_name"],
            }
            send_reply(
                event,
                f"✅ 已鎖定：{row['company_code']}（{row['company_name']}）",
                quick_reply=build_main_quick_reply(),
            )
            return

        # name
        try:
            hits = db_search_companies_by_name(search_key, limit=5)
        except Exception as e:
            print(f"DB 查詢失敗（company by name）：{e}")
            reply_db_error(event, e)
            return

        if len(hits) == 1 and hits[0]["company_code"]:
            user_sessions[user_id] = {
                "state": "LOCKED",
                "company_code": hits[0]["company_code"],
                "company_name": hits[0]["company_name"],
            }
            send_reply(
                event,
                f"✅ 已鎖定：{hits[0]['company_code']}（{hits[0]['company_name']}）",
                quick_reply=build_main_quick_reply(),
            )
            return

        if len(hits) > 1:
            lines = ["找到多筆公司，請改輸入 4 碼代碼："]
            for i, c in enumerate(hits, start=1):
                cc = c.get("company_code", "")
                cn = c.get("company_name", "")
                if cc and cn:
                    lines.append(f"{i}. {cc}（{cn}）")
            send_reply(event, "\n".join(lines))
            return

        send_reply(event, "查無此公司，請輸入正確的公司代碼或公司名稱。")
        return

    if state == "IDLE":
        send_reply(event, "請輸入公司代碼（4 碼）或公司名稱，或輸入 A 進入鎖定流程。")

# =========================
#  Postback handler（年份 / 分數 / Dashboard）
# =========================
@handler.add(PostbackEvent)
def handle_postback(event):
    user_id = event.source.user_id
    sess = user_sessions.get(user_id, {"state": "IDLE"})
    state = sess.get("state", "IDLE")
    data = (event.postback.data or "").strip()

    if state != "LOCKED":
        send_reply(event, "尚未鎖定公司，請先輸入公司代碼（4 碼）或公司名稱。")
        return

    company_code = str(sess.get("company_code") or "")
    company_name = str(sess.get("company_name") or "")

    if data == "ACTION=SHOW_YEARS":
        try:
            years = db_list_years(company_code)
        except Exception as e:
            print(f"DB 查詢失敗（years）：{e}")
            reply_db_error(event, e)
            return

        if not years:
            send_reply(event, f"目前查不到年份資料。")
            return

        send_reply(event, "請選擇年份：", quick_reply=build_year_quick_reply(years))
        return

    if data == "ACTION=DASHBOARD":
        dashboard_base_url = (os.getenv("DASHBOARD_BASE_URL") or "https://YOUR-DASHBOARD-SITE").strip().rstrip("/")

        # 需要年份才能讓 Dashboard 自動帶出資料
        selected_year = sess.get("selected_year")
        if not selected_year:
            send_reply(event, "請先點「年份」選年度後，再開啟 Dashboard。", quick_reply=build_main_quick_reply())
            return

        params = {"year": int(selected_year), "code": company_code}
        url = f"{dashboard_base_url}?{urlencode(params)}"

        send_reply(event, f"📊【{company_name} Dashboard】點擊下方連結查看：{url}")
        return

    if data.startswith("YEAR="):
        try:
            year = int(data.split("=", 1)[1])
        except Exception:
            send_reply(event, "年份格式錯誤，請重新選擇年份。")
            return

        # 記住使用者最後一次選的年份，供 Dashboard 連結帶參數
        sess["selected_year"] = year
        user_sessions[user_id] = sess

        try:
            score = db_get_total_score(company_code, year)
        except Exception as e:
            print(f"DB 查詢失敗（score）：{e}")
            reply_db_error(event, e)
            return

        if score is None:
            send_reply(event, f"{year} 年查不到分數資料。")
            return

        risk = risk_level_from_score(float(score))
        bar = bar_10(float(score))

        send_reply(
            event,
            f"⚖️【{company_name} ESG 風險評分】\n"
            f"年度：{year}\n"
            f"{risk['emoji']} 風險等級：{risk['level']}\n"
            f"總分：[{bar}]",
            quick_reply=build_main_quick_reply(),
        )
        return

    send_reply(event, "收到，但目前這個操作尚未支援。")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=False)
