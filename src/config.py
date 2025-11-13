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

# SBI証券 業種別株価平均ランキング（前日比）
SECTOR_URL = "https://www.sbisec.co.jp/ETGate/?OutSide=on&getFlg=on&_ControlID=WPLETmgR001Control&_PageID=WPLETmgR001Mdtl20&_ActionID=DefaultAID&_DataStoreID=DSWPLETmgR001Control&burl=iris_ranking&cat1=market&cat2=ranking&dir=tl1-rnk%7Ctl2-stock%7Ctl3-industry%7Ctl4-idx%7Ctl5-uprate&file=index.html"

# ===========================
# スケジュール設定
# ===========================

# 松井証券ランキング取得時刻（JST）: HH:MM形式
# キー: 時刻、値: 取得対象（morning or afternoon）
TIME_SLOTS = {
    "09:20": "morning",
    "13:00": "afternoon"
}

# セクター別騰落ランキング取得時刻（JST）: HH:MM形式
SECTOR_TIME_SLOTS = {
    "11:45": "midday",
    "16:00": "close"
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
# 注意: RETRY_COUNTを変更する場合は、RETRY_DELAYSの要素数も合わせて調整してください
#       要素数が足りない場合は最後の値が使われますが、意図した遅延時間にならない可能性があります
RETRY_DELAYS = [5, 10, 20]

# ===========================
# データ保存設定
# ===========================

# データ保存ディレクトリ（プロジェクトルートからの相対パス）
DATA_DIR = "data"

# セクター別ランキングデータ保存ディレクトリ
SECTOR_DATA_DIR = "data/sector"

# ===========================
# LINE 通知設定
# ===========================

# LINE Messaging API エンドポイント (push message)
# 注意: LINE Notifyは2025年3月31日にサービス終了
LINE_MESSAGING_API_PUSH = "https://api.line.me/v2/bot/message/push"

# 廃止予定: LINE Notify API (2025年3月31日終了)
# LINE_NOTIFY_API = "https://notify-api.line.me/api/notify"
