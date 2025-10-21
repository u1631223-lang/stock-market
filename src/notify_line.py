"""
LINE通知モジュール

LINE Notify APIを使用して、スクレイピング結果の通知を送信します。
"""

import os
import requests
from typing import List, Dict
from config import LINE_NOTIFY_API


def send_line_notify(message: str, token: str = None) -> bool:
    """
    LINE Notify APIにメッセージを送信する

    Args:
        message: 送信するメッセージ
        token: LINE Notify トークン（省略時は環境変数から取得）

    Returns:
        bool: 送信成功時 True、失敗時 False

    Raises:
        ValueError: トークンが設定されていない場合

    Examples:
        >>> send_line_notify("テストメッセージ")
        True
        >>> send_line_notify("テストメッセージ", token="your_token")
        True
    """
    # トークンが指定されていない場合は環境変数から取得
    if token is None:
        token = os.getenv("LINE_NOTIFY_TOKEN")

    if not token:
        raise ValueError("LINE_NOTIFY_TOKEN が設定されていません")

    # LINE Notify API にリクエスト
    headers = {"Authorization": f"Bearer {token}"}
    data = {"message": message}

    try:
        response = requests.post(LINE_NOTIFY_API, headers=headers, data=data, timeout=10)
        response.raise_for_status()
        print(f"✅ LINE通知送信成功")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ LINE通知送信エラー: {e}")
        return False


def format_success_message(datetime_str: str, target: str, rankings: List[Dict]) -> str:
    """
    成功時のメッセージをフォーマットする

    Args:
        datetime_str: 日時文字列（例: "2025-10-20 09:15"）
        target: "morning" or "afternoon"
        rankings: ランキングデータのリスト

    Returns:
        str: フォーマット済みメッセージ

    Examples:
        >>> rankings = [
        ...     {"rank": "1", "code": "1234", "name": "サンプル株式"},
        ...     {"rank": "2", "code": "5678", "name": "テスト銘柄"},
        ... ]
        >>> msg = format_success_message("2025-10-21 09:15", "morning", rankings)
        >>> print(msg)
        ✅ [成功] 2025-10-21 09:15
        朝ランキング取得完了
        ...
    """
    # 日本語の時間帯名
    target_name = "朝" if target == "morning" else "午後"

    # 基本メッセージ
    message = f"✅ [成功] {datetime_str}\n"
    message += f"{target_name}ランキング取得完了\n"

    # ベスト3を表示
    if rankings and len(rankings) >= 3:
        message += "\n📊 ベスト3:\n"
        for i in range(3):
            rank = rankings[i].get("rank", str(i + 1))
            code = rankings[i].get("code", "----")
            name = rankings[i].get("name", "不明")
            message += f"{rank}位: {name} ({code})\n"
    elif rankings:
        # 3件未満の場合は全て表示
        message += "\n📊 取得データ:\n"
        for item in rankings:
            rank = item.get("rank", "-")
            code = item.get("code", "----")
            name = item.get("name", "不明")
            message += f"{rank}位: {name} ({code})\n"

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
    print("=== LINE通知テスト ===\n")

    # 環境変数の確認
    token = os.getenv("LINE_NOTIFY_TOKEN")
    if not token:
        print("❌ LINE_NOTIFY_TOKEN が設定されていません")
        print("\n設定方法:")
        print('export LINE_NOTIFY_TOKEN="your_token_here"')
        return

    print(f"✅ LINE_NOTIFY_TOKEN: 設定済み (長さ: {len(token)}文字)\n")

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
