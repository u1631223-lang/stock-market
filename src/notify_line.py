"""
LINE通知モジュール

LINE Messaging APIを使用して、スクレイピング結果の通知を送信します。

注意: LINE Notifyは2025年3月31日にサービス終了したため、
      LINE Messaging API (push message) に移行しました。
"""

import os
import time
import requests
from typing import List, Dict
from config import LINE_MESSAGING_API_PUSH, RETRY_COUNT, RETRY_DELAYS


def send_line_notify(message: str, token: str = None, user_id: str = None) -> bool:
    """
    LINE Messaging API (push message) でメッセージを送信する

    Args:
        message: 送信するメッセージ
        token: LINE Channel Access Token（省略時は環境変数 LINE_CHANNEL_ACCESS_TOKEN から取得）
        user_id: 送信先のLINE User ID（省略時は環境変数 LINE_TARGET_USER_ID から取得）

    Returns:
        bool: 送信成功時 True、失敗時 False

    Raises:
        ValueError: トークンまたはユーザーIDが設定されていない場合

    Examples:
        >>> send_line_notify("テストメッセージ")
        True
        >>> send_line_notify("テストメッセージ", token="your_token", user_id="U1234...")
        True
    """
    # トークンが指定されていない場合は環境変数から取得
    if token is None:
        token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

    if not token:
        raise ValueError("LINE_CHANNEL_ACCESS_TOKEN が設定されていません")

    # ユーザーIDが指定されていない場合は環境変数から取得
    if user_id is None:
        user_id = os.getenv("LINE_TARGET_USER_ID")

    if not user_id:
        raise ValueError("LINE_TARGET_USER_ID が設定されていません")

    # LINE Messaging API (push) にリクエスト
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Messaging API のメッセージフォーマット
    data = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }

    # リトライロジック
    for attempt in range(1, RETRY_COUNT + 1):
        try:
            response = requests.post(LINE_MESSAGING_API_PUSH, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            print(f"✅ LINE通知送信成功 (宛先: {user_id[:10]}...)")
            return True
        except requests.exceptions.RequestException as e:
            is_last_attempt = (attempt == RETRY_COUNT)
            
            # ステータスコードによってリトライ可否を判断
            should_retry = False
            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
                # 4xx系エラー（401, 403など）はリトライしない
                if 400 <= status_code < 500:
                    print(f"❌ LINE通知送信エラー (試行 {attempt}/{RETRY_COUNT}): {e}")
                    print(f"   ステータスコード: {status_code} - リトライ不可（認証/権限エラー）")
                    if hasattr(e.response, 'text'):
                        print(f"   レスポンス: {e.response.text}")
                    return False
                # 5xx系エラーやその他はリトライする
                else:
                    should_retry = not is_last_attempt
            else:
                # ネットワークエラーなどはリトライする
                should_retry = not is_last_attempt
            
            if should_retry:
                delay = RETRY_DELAYS[attempt - 1]
                print(f"⚠️ LINE通知送信エラー (試行 {attempt}/{RETRY_COUNT}): {e}")
                if hasattr(e, 'response') and hasattr(e.response, 'text'):
                    print(f"   レスポンス: {e.response.text}")
                print(f"   {delay}秒後にリトライします...")
                time.sleep(delay)
            else:
                print(f"❌ LINE通知送信エラー (試行 {attempt}/{RETRY_COUNT}): {e}")
                if hasattr(e, 'response') and hasattr(e.response, 'text'):
                    print(f"   レスポンス: {e.response.text}")
                return False
    
    return False


def format_success_message(datetime_str: str, target: str, rankings: List[Dict], previous_rankings: List[Dict] = None) -> str:
    """
    成功時のメッセージをフォーマートする

    Args:
        datetime_str: 日時文字列（例: "2025-10-20 09:15"）
        target: "morning" or "afternoon"
        rankings: ランキングデータのリスト
        previous_rankings: 前回のランキングデータ（オプション）

    Returns:
        str: フォーマット済みメッセージ

    Examples:
        >>> rankings = [
        ...     {"rank": "1", "code": "1234", "name": "サンプル株式", "change_percent": "株価変動率：+5.00%"},
        ...     {"rank": "2", "code": "5678", "name": "テスト銘柄", "change_percent": "株価変動率：+3.00%"},
        ... ]
        >>> msg = format_success_message("2025-10-21 09:15", "morning", rankings)
        >>> print(msg)
        📊 2025-10-21 09:15
        午前中資金流入ランキング
        ...
    """
    # 日本語の時間帯名
    target_name = "午前中資金流入" if target == "morning" else "午後資金流入"

    # 基本メッセージ
    message = f"📊 {datetime_str}\n"
    message += f"{target_name}ランキング\n"

    # 前回ランキングから銘柄コード→順位のマップを作成
    prev_rank_map = {}
    if previous_rankings:
        for item in previous_rankings:
            code = item.get("code", "")
            rank_str = item.get("rank", "")
            if code and rank_str:
                try:
                    prev_rank_map[code] = int(rank_str)
                except (ValueError, TypeError):
                    pass

    # ベスト10全件を表示（株価変動率、ランキング変動も含む）
    if rankings:
        message += "\n"
        for i, item in enumerate(rankings[:10]):  # 最大10件
            rank = item.get("rank", str(i + 1))
            code = item.get("code", "----")
            name = item.get("name", "不明")
            
            # 株価変動率を取得（"株価変動率：+5.00%" → "+5.00%"）
            change_percent_raw = item.get("change_percent", "")
            if change_percent_raw:
                # "株価変動率：" プレフィックスを削除
                change_percent = change_percent_raw.replace("株価変動率：", "").strip()
            else:
                change_percent = "-"
            
            # ランキング変動を計算（前回データがある場合のみ）
            rank_change_icon = ""
            if previous_rankings:  # 前回データがある場合のみ変動を表示
                if code in prev_rank_map:
                    try:
                        current_rank = int(rank)
                        prev_rank = prev_rank_map[code]

                        if current_rank < prev_rank:
                            # 順位が上がった（数字が小さくなった）
                            diff = prev_rank - current_rank
                            rank_change_icon = f" 🔺↑{diff}"
                        elif current_rank > prev_rank:
                            # 順位が下がった（数字が大きくなった）
                            diff = current_rank - prev_rank
                            rank_change_icon = f" 🔻↓{diff}"
                        else:
                            # 変動なし
                            rank_change_icon = " -"
                    except (ValueError, TypeError):
                        pass
                elif code != "----":
                    # 前回のランキングに存在しない（新規ランクイン）
                    rank_change_icon = " 🆕NEW"
            
            message += f"{rank}位: [{code}] {name} {change_percent}{rank_change_icon}\n"

    return message


def format_error_message(datetime_str: str, target: str, error: str) -> str:
    """
    エラー時のメッセージをフォーマットする

    Args:
        datetime_str: 日時文字列
        target: "morning" or "afternoon"
        error: エラー内容

    Returns:
        str: フォーマット済みメッセージ

    Examples:
        >>> msg = format_error_message("2025-10-21 09:15", "morning", "HTTP 403 Forbidden")
        >>> print(msg)
        ❌ [エラー] 2025-10-21 09:15
        朝ランキング取得失敗
        ...
    """
    # 日本語の時間帯名
    target_name = "朝" if target == "morning" else "午後"

    # エラーメッセージ
    message = f"❌ [エラー] {datetime_str}\n"
    message += f"{target_name}ランキング取得失敗\n"
    message += f"\nエラー内容:\n{error}"

    return message


def main():
    """
    モジュール直接実行時の動作

    テストメッセージを送信します。
    """
    print("=== LINE通知テスト (Messaging API) ===\n")

    # 環境変数の確認
    token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    user_id = os.getenv("LINE_TARGET_USER_ID")

    if not token:
        print("❌ LINE_CHANNEL_ACCESS_TOKEN が設定されていません")
        print("\n設定方法:")
        print('export LINE_CHANNEL_ACCESS_TOKEN="your_channel_access_token"')
        return

    if not user_id:
        print("❌ LINE_TARGET_USER_ID が設定されていません")
        print("\n設定方法:")
        print('export LINE_TARGET_USER_ID="your_user_id"')
        return

    print(f"✅ LINE_CHANNEL_ACCESS_TOKEN: 設定済み (長さ: {len(token)}文字)")
    print(f"✅ LINE_TARGET_USER_ID: 設定済み ({user_id[:10]}...)\n")

    # テストメッセージ1: シンプルなメッセージ
    print("【テスト1】シンプルなメッセージ送信")
    test_message = "🧪 [テスト] LINE通知モジュールのテスト実行"
    result1 = send_line_notify(test_message)
    print()

    # テストメッセージ2: 成功メッセージのフォーマット
    print("【テスト2】成功メッセージのフォーマット")
    sample_rankings = [
        {"rank": "1", "code": "1234", "name": "サンプル株式会社"},
        {"rank": "2", "code": "5678", "name": "テスト銘柄"},
        {"rank": "3", "code": "9012", "name": "デモ会社"},
    ]
    success_msg = format_success_message("2025-10-21 09:15", "morning", sample_rankings)
    print("--- フォーマット結果 ---")
    print(success_msg)
    print("--- 送信中 ---")
    result2 = send_line_notify(success_msg)
    print()

    # テストメッセージ3: エラーメッセージのフォーマット
    print("【テスト3】エラーメッセージのフォーマット")
    error_msg = format_error_message("2025-10-21 09:15", "afternoon", "HTTP 403 Forbidden")
    print("--- フォーマット結果 ---")
    print(error_msg)
    print("--- 送信中 ---")
    result3 = send_line_notify(error_msg)
    print()

    # 結果サマリー
    print("="*50)
    print("【テスト結果サマリー】")
    print(f"テスト1 (シンプル): {'✅ 成功' if result1 else '❌ 失敗'}")
    print(f"テスト2 (成功メッセージ): {'✅ 成功' if result2 else '❌ 失敗'}")
    print(f"テスト3 (エラーメッセージ): {'✅ 成功' if result3 else '❌ 失敗'}")

    if result1 and result2 and result3:
        print("\n✅ すべてのテストが成功しました")
    else:
        print("\n❌ 一部のテストが失敗しました")


if __name__ == "__main__":
    main()
