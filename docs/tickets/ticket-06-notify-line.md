# Ticket #6: notify_line.py 実装

## 📋 基本情報

- **優先度:** 🟡 中
- **ステータス:** ✅ 完了（Messaging API移行済み: 2025-10-21）
- **推定工数:** 45分
- **依存関係:** #1
- **担当者:** Claude
- **作成日:** 2025-10-21
- **最終更新:** 2025-10-21 08:22

---

## 📝 概要

LINE Notify APIを使用して、スクレイピング結果の通知を送信するモジュールを実装する。成功・失敗の通知とメッセージフォーマット機能を提供。

> **重要:** LINE Notify は 2025年3月31日に提供終了予定のため、Messaging API への移行計画立案と実装が追加タスクとして必要です。

---

## ✅ Messaging API 移行完了（2025-10-21）

- [x] LINE Developers で公式アカウントと Messaging API チャネルを作成
  - プロバイダ: `stock-market`
  - Channel ID: `2008327755`
- [x] チャネルアクセストークン・User IDの取得完了
- [x] `notify_line.py` を Messaging API の push メッセージ送信に対応
  - エンドポイント: `https://api.line.me/v2/bot/message/push`
  - JSON形式でのメッセージ送信
- [x] GitHub Secrets の更新
  - `LINE_CHANNEL_ACCESS_TOKEN`: チャネルアクセストークン
  - `LINE_TARGET_USER_ID`: 送信先User ID
- [x] ワークフロー・ドキュメントの更新完了

---

## 🎯 タスク一覧

- [x] `src/notify_line.py` ファイル作成
- [x] `send_line_notify(message: str, token: str) -> bool` 関数実装
  - [x] 環境変数から LINE_NOTIFY_TOKEN 取得
  - [x] LINE Notify API呼び出し
  - [x] ステータスコード確認
  - [x] エラーハンドリング
- [x] `format_success_message(datetime_str: str, target: str, rankings: List[Dict]) -> str` 関数実装
  - [x] 成功メッセージの生成
  - [x] ベスト3の銘柄表示
  - [x] 見やすいフォーマット
- [x] `format_error_message(datetime_str: str, target: str, error: str) -> str` 関数実装
  - [x] エラーメッセージの生成
  - [x] エラー内容の簡潔な表示
- [x] コマンドライン実行対応（テスト用）
- [x] docstring 追加
- [x] メッセージフォーマットテスト（4件すべて成功）
- [x] トークンハンドリングテスト（2件すべて成功）

---

## 📦 成果物

### ファイル: `src/notify_line.py`

**主要関数のシグネチャ:**

```python
import os
from typing import List, Dict

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
    """
    pass

def format_success_message(datetime_str: str, target: str, rankings: List[Dict]) -> str:
    """
    成功時のメッセージをフォーマットする

    Args:
        datetime_str: 日時文字列（例: "2025-10-20 09:15"）
        target: "morning" or "afternoon"
        rankings: ランキングデータのリスト

    Returns:
        str: フォーマット済みメッセージ
    """
    pass

def format_error_message(datetime_str: str, target: str, error: str) -> str:
    """
    エラー時のメッセージをフォーマットする

    Args:
        datetime_str: 日時文字列
        target: "morning" or "afternoon"
        error: エラー内容

    Returns:
        str: フォーマット済みメッセージ
    """
    pass
```

---

## ✅ 完了条件

- [x] `src/notify_line.py` ファイルが存在する
- [x] すべての関数が実装されている
- [x] 環境変数 `LINE_NOTIFY_TOKEN` からトークンを取得できる
- [x] LINE Notify API呼び出しが実装されている
- [x] 成功メッセージが適切にフォーマットされる
- [x] エラーメッセージが適切にフォーマットされる
- [x] コマンドライン実行でテスト送信できる
- [x] docstring が適切に記載されている
- [x] PEP 8 スタイルガイドに準拠している
- [x] メッセージフォーマットテスト成功（4件）
- [x] トークンハンドリングテスト成功（2件）

---

## 🧪 テスト方法

### 環境変数設定

```bash
# LINE Notify トークンを取得（https://notify-bot.line.me/ja/）
export LINE_NOTIFY_TOKEN="your_token_here"
```

### テスト実行

```bash
# 仮想環境をアクティブ化
source venv/bin/activate

# テストメッセージ送信
cd src
python notify_line.py
```

### 関数個別テスト

```python
from notify_line import send_line_notify, format_success_message, format_error_message
import os

# トークン確認
token = os.getenv("LINE_NOTIFY_TOKEN")
print(f"Token: {'設定済み' if token else '未設定'}")

# 成功メッセージのテスト
rankings = [
    {"rank": "1", "code": "1234", "name": "サンプル株式"},
    {"rank": "2", "code": "5678", "name": "テスト銘柄"},
    {"rank": "3", "code": "9012", "name": "デモ会社"},
]
success_msg = format_success_message("2025-10-21 09:15", "morning", rankings)
print(success_msg)

# エラーメッセージのテスト
error_msg = format_error_message("2025-10-21 09:15", "morning", "HTTP 403 Forbidden")
print(error_msg)

# 実際に送信テスト
send_line_notify("テストメッセージ", token)
```

---

## 📌 注意事項

- **トークンの管理**: 環境変数から取得、コードにハードコードしない
- **GitHub Secrets**: GitHub Actions では Secrets として設定
- **API制限**: LINE Notifyには時間当たりの送信上限がある（通常は問題なし）
- **メッセージ長**: 最大1,000文字まで
- **改行**: `\n` で改行可能

---

## 🔍 実装例

### メッセージフォーマット例

**成功時:**
```
✅ [成功] 2025-10-21 09:15
朝ランキング取得完了

📊 ベスト3:
1位: サンプル株式 (1234)
2位: テスト銘柄 (5678)
3位: デモ会社 (9012)
```

**エラー時:**
```
❌ [エラー] 2025-10-21 09:15
朝ランキング取得失敗

エラー内容:
HTTP 403 Forbidden
```

### LINE Notify API 呼び出し例

```python
import requests
from config import LINE_NOTIFY_API

def send_line_notify(message: str, token: str = None) -> bool:
    if token is None:
        token = os.getenv("LINE_NOTIFY_TOKEN")

    if not token:
        raise ValueError("LINE_NOTIFY_TOKEN が設定されていません")

    headers = {"Authorization": f"Bearer {token}"}
    data = {"message": message}

    try:
        response = requests.post(LINE_NOTIFY_API, headers=headers, data=data, timeout=10)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"LINE通知送信エラー: {e}")
        return False
```

---

## 🔗 関連チケット

- **依存元:** #1 (プロジェクト環境構築)
- **関連:** #4 (scrape_rankings.py) - メイン処理から呼び出される

---

## 📚 参考資料

- [LINE Notify API Document](https://notify-bot.line.me/doc/ja/)
- [LINE Notify トークン発行](https://notify-bot.line.me/my/)

---

## 📝 作業ログ

| 日時 | 作業内容 | 備考 |
|------|---------|------|
| 2025-10-21 08:00 | チケット作成 | - |
| 2025-10-21 08:20 | notify_line.py 作成 | 3つの主要関数実装 |
| 2025-10-21 08:20 | main()関数追加 | テスト用の直接実行機能 |
| 2025-10-21 08:21 | メッセージフォーマットテスト | 4件のテストすべて成功 |
| 2025-10-21 08:22 | トークンハンドリングテスト | 2件のテストすべて成功 |
| 2025-10-21 08:22 | ✅ チケット完了 | すべてのタスク完了 |
