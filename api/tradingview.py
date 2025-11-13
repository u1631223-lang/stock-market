"""
TradingView Webhook エンドポイント (Vercel Serverless Function)

TradingViewからのWebhookを受信し、LINE Messaging APIで通知を送信します。
"""

import json
import os
from http.server import BaseHTTPRequestHandler
from datetime import datetime

import requests


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """TradingViewからのPOSTリクエストを処理"""

        # セキュリティ: シークレットトークン検証
        secret = self.headers.get("X-TradingView-Secret")
        expected_secret = os.environ.get("TRADINGVIEW_SECRET")

        if not expected_secret:
            self.send_error(500, "Server configuration error")
            return

        if secret != expected_secret:
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b"Forbidden: Invalid secret")
            return

        # リクエストボディを取得
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode("utf-8"))
        except (ValueError, json.JSONDecodeError) as e:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(f"Bad Request: {str(e)}".encode())
            return

        # LINE通知メッセージを作成
        message = format_trading_alert(data)

        # LINE Messaging APIで通知
        success = send_line_message(message)

        if success:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"Failed to send LINE notification")

    def do_GET(self):
        """ヘルスチェック用"""
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"TradingView Webhook is running")


def format_trading_alert(data: dict) -> str:
    """
    TradingViewアラートをLINEメッセージにフォーマット

    Args:
        data: TradingViewから送信されたJSONデータ

    Returns:
        str: フォーマット済みメッセージ
    """
    # TradingViewから送信される一般的なフィールド
    ticker = data.get("ticker", data.get("symbol", "不明"))
    action = data.get("action", data.get("order_action", ""))
    strategy = data.get("strategy", "")
    price = data.get("close", data.get("price", ""))
    time = data.get("time", data.get("timenow", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    # カスタムメッセージ（TradingViewから直接送信された場合）
    custom_message = data.get("message", "")

    # アクションに応じたアイコン
    icon = "📈"
    if action:
        action_lower = action.lower()
        if "buy" in action_lower or "long" in action_lower:
            icon = "🟢"
        elif "sell" in action_lower or "short" in action_lower:
            icon = "🔴"
        elif "close" in action_lower:
            icon = "⚪"

    lines = [f"{icon} TradingView Alert"]

    if custom_message:
        # カスタムメッセージがある場合はそれを優先
        lines.append("")
        lines.append(custom_message)
    else:
        # 構造化データから自動生成
        if ticker:
            lines.append(f"銘柄: {ticker}")
        if strategy:
            lines.append(f"戦略: {strategy}")
        if action:
            lines.append(f"アクション: {action}")
        if price:
            lines.append(f"価格: {price}")
        lines.append(f"時刻: {time}")

    # 追加情報があれば表示
    for key, value in data.items():
        if key not in ["ticker", "symbol", "action", "order_action", "strategy", "close", "price", "time", "timenow", "message"]:
            lines.append(f"{key}: {value}")

    return "\n".join(lines)


def send_line_message(message: str) -> bool:
    """
    LINE Messaging APIでメッセージを送信

    Args:
        message: 送信するメッセージ

    Returns:
        bool: 送信成功時True
    """
    access_token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    user_id = os.environ.get("LINE_TARGET_USER_ID")

    if not access_token or not user_id:
        print("ERROR: LINE credentials not configured")
        return False

    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    payload = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": message,
            }
        ],
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        print(f"LINE notification sent successfully: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Failed to send LINE notification: {e}")
        return False
