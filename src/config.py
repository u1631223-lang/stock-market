"""
松井証券ランキング自動取得システム - 設定モジュール

このモジュールはプロジェクト全体で使用する定数・設定値を管理します。
"""

# ===========================
# URL設定
# ===========================

URLS = {
    "morning": "https://finance.matsui.co.jp/ranking-day-trading-morning/index?condition=0&market=0",
    "afternoon": "https://finance.matsui.co.jp/ranking-day-trading-afternoon/index?condition=0&market=0"
}

# ===========================
# スケジュール設定
# ===========================

# 取得時刻（JST）: HH:MM形式
# キー: 時刻、値: 取得対象（morning or afternoon）
TIME_SLOTS = {
    "09:15": "morning",
    "09:30": "morning",
    "12:00": "morning",
    "12:45": "afternoon",
    "14:30": "afternoon"
}

# ===========================
# HTTP設定
# ===========================

# User-Agent（403エラー回避のため）
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# タイムアウト設定（秒）
REQUEST_TIMEOUT = 30

# ===========================
# リトライ設定
# ===========================

# 最大リトライ回数
RETRY_COUNT = 3

# リトライ間隔（秒）: 指数バックオフ
RETRY_DELAYS = [5, 10, 20]

# ===========================
# データ保存設定
# ===========================

# データ保存ディレクトリ（プロジェクトルートからの相対パス）
DATA_DIR = "data"

# ===========================
# LINE 通知設定
# ===========================

# LINE Messaging API エンドポイント (push message)
# 注意: LINE Notifyは2025年3月31日にサービス終了
LINE_MESSAGING_API_PUSH = "https://api.line.me/v2/bot/message/push"

# 廃止予定: LINE Notify API (2025年3月31日終了)
# LINE_NOTIFY_API = "https://notify-api.line.me/api/notify"
