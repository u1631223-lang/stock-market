# 松井証券ランキング自動取得システム

## 概要

松井証券のデイトレードランキングページから、指定された時刻に自動的にランキングデータを取得し、JSON形式で保存するシステムです。GitHub Actions で定時実行し、結果を LINE で通知します。

## 機能

- 📊 **自動データ取得**: 平日の5回（09:15, 09:30, 12:00, 12:45, 14:30）に自動実行
- 💾 **データ保存**: ランキングデータをJSON形式でGitHubリポジトリに保存
- 📲 **LINE通知**: 取得成功・失敗を LINE Notify で通知
- 🗓️ **営業日判定**: 土日祝日は自動的にスキップ
- 🔄 **リトライ機能**: ネットワークエラー時は自動リトライ

## 取得対象

- **朝のランキング**: https://finance.matsui.co.jp/ranking-day-trading-morning/index?condition=0&market=0
- **午後のランキング**: https://finance.matsui.co.jp/ranking-day-trading-afternoon/index?condition=0&market=0
- **取得データ**: ベスト10の銘柄情報（順位、コード、銘柄名、株価など）

## セットアップ

### 1. リポジトリのクローン

```bash
git clone https://github.com/username/market.git
cd market
```

### 2. 依存関係のインストール

```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. LINE Notify トークンの取得

1. [LINE Notify](https://notify-bot.line.me/ja/) にアクセス
2. トークンを発行
3. GitHub Secrets に `LINE_NOTIFY_TOKEN` として登録

### 4. GitHub Actions の有効化

GitHub リポジトリの Actions タブで、ワークフローを有効化します。

## ディレクトリ構造

```
market/
├── .github/
│   └── workflows/          # GitHub Actions ワークフロー（今後追加）
├── docs/                   # ドキュメント
│   ├── tickets/            # チケット管理
│   ├── requirements.md
│   ├── architecture.md
│   └── ...
├── src/                    # ソースコード（今後追加）
│   ├── config.py
│   ├── check_workday.py
│   ├── scrape_rankings.py
│   └── notify_line.py
├── data/                   # データ保存先
│   ├── morning/            # 朝のランキング
│   └── afternoon/          # 午後のランキング
├── requirements.txt        # Python依存関係
├── .gitignore
├── CLAUDE.md
└── README.md
```

## 技術スタック

- **Python 3.11+**
- **requests**: HTTP通信
- **Beautiful Soup**: HTMLパース
- **jpholiday**: 日本の祝日判定
- **GitHub Actions**: 定時実行
- **LINE Notify**: 通知サービス

## ドキュメント

詳細なドキュメントは [docs/](./docs/) を参照してください。

- [要件定義](./docs/requirements.md)
- [アーキテクチャ設計](./docs/architecture.md)
- [技術スタック](./docs/technical-stack.md)
- [実装ガイド](./docs/implementation-guide.md)
- [セットアップガイド](./docs/setup-guide.md)
- [チケット管理](./docs/tickets/TICKETS.md)

## 開発状況

現在開発中です。進捗は [チケット管理](./docs/tickets/TICKETS.md) で確認できます。

## ライセンス

MIT License

---

**注意**: このシステムは松井証券の公開情報を自動取得するものです。利用規約を遵守し、適切な間隔でアクセスしてください。
