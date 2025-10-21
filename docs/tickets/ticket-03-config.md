# Ticket #3: config.py 実装

## 📋 基本情報

- **優先度:** 🔴 高
- **ステータス:** ✅ 完了
- **推定工数:** 15分
- **依存関係:** #1
- **担当者:** Claude
- **作成日:** 2025-10-21
- **最終更新:** 2025-10-21 08:15

---

## 📝 概要

プロジェクト全体で使用する設定値を一元管理する設定モジュールを作成する。URL、スケジュール、リトライ設定などを定数として定義。

---

## 🎯 タスク一覧

- [x] `src/config.py` ファイル作成
- [x] URL定数定義（朝・午後のランキングページ）
- [x] TIME_SLOTS 定義（5つの実行時刻）
- [x] USER_AGENT 定義（ブラウザ識別文字列）
- [x] リトライ設定定義（RETRY_COUNT, RETRY_DELAYS）
- [x] タイムアウト設定定義
- [x] DATA_DIR 定義（データ保存先）
- [x] モジュールdocstring 追加
- [x] 各定数にコメント追加

---

## 📦 成果物

### ファイル: `src/config.py`

**期待される内容:**

```python
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
# LINE Notify設定（将来的に Messaging API へ置き換え）
# ===========================

# LINE Notify API エンドポイント（Messaging API 移行後に更新予定）
LINE_NOTIFY_API = "https://notify-api.line.me/api/notify"
```

---

## ✅ 完了条件

- [x] `src/config.py` ファイルが存在する
- [x] すべての必須設定値が定義されている
  - [x] URLS (朝・午後)
  - [x] TIME_SLOTS (5つの時刻)
  - [x] USER_AGENT
  - [x] REQUEST_TIMEOUT
  - [x] RETRY_COUNT, RETRY_DELAYS
  - [x] DATA_DIR
  - [x] LINE_NOTIFY_API
- [x] docstring が適切に記載されている
- [x] 各セクションにコメントがある
- [x] PEP 8 スタイルガイドに準拠している

---

## 🧪 テスト方法

### インポートテスト

```bash
cd src
python -c "from config import *; print('URLs:', URLS); print('TIME_SLOTS:', TIME_SLOTS)"
```

### 設定値検証

```python
import config

# URL検証
assert "morning" in config.URLS
assert "afternoon" in config.URLS
assert config.URLS["morning"].startswith("https://")

# TIME_SLOTS検証
assert len(config.TIME_SLOTS) == 5
assert "09:15" in config.TIME_SLOTS
assert config.TIME_SLOTS["09:15"] == "morning"

# リトライ設定検証
assert config.RETRY_COUNT == 3
assert len(config.RETRY_DELAYS) == 3

# USER_AGENT検証
assert "Mozilla" in config.USER_AGENT

print("✅ すべての設定値が正しく定義されています")
```

---

## 📌 注意事項

- **環境変数は使用しない**: すべて定数として定義（LINE_NOTIFY_TOKENは例外）
- **絶対パスは使用しない**: DATA_DIRは相対パスで定義
- **マジックナンバー禁止**: すべての数値に意味のある定数名を付ける
- **変更容易性**: URL変更時はこのファイルのみ修正すればよい設計

---

## 🔗 関連チケット

- **依存元:** #1 (プロジェクト環境構築)
- **ブロック対象:** #4 (scrape_rankings.py), #6 (notify_line.py)

---

## 📚 参考資料

- [PEP 8 -- Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [Python Naming Conventions](https://peps.python.org/pep-0008/#naming-conventions)

---

## 📝 作業ログ

| 日時 | 作業内容 | 備考 |
|------|---------|------|
| 2025-10-21 08:00 | チケット作成 | - |
| 2025-10-21 08:14 | config.py 作成 | すべての設定値を定義 |
| 2025-10-21 08:15 | インポートテスト実施 | すべての設定値が正常に読み込まれることを確認 |
| 2025-10-21 08:15 | ✅ チケット完了 | すべてのタスク完了 |
