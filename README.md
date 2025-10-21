# 松井証券ランキング自動取得システム

[![GitHub Actions](https://github.com/username/market/workflows/Scheduled%20Ranking%20Scrape/badge.svg)](https://github.com/username/market/actions)

## 目次

- [概要](#概要)
- [機能](#機能)
- [取得対象](#取得対象)
- [セットアップ](#セットアップ)
- [使い方](#使い方)
- [ディレクトリ構造](#ディレクトリ構造)
- [技術スタック](#技術スタック)
- [ドキュメント](#ドキュメント)
- [トラブルシューティング](#トラブルシューティング)
- [開発状況](#開発状況)
- [ライセンス](#ライセンス)
- [貢献](#貢献)

## 概要

松井証券のデイトレードランキングページから、指定された時刻に自動的にランキングデータを取得し、JSON形式で保存するシステムです。GitHub Actions で定時実行し、結果を LINE で通知します。

## 重要なお知らせ（LINE Notify 終了予定）

LINE Notify は 2025年3月31日にサービス提供を終了します。現在の実装は引き続き利用できますが、終了日以降は通知が送れなくなるため、LINE Messaging API への移行計画を進めています。短期的な対応としては既存トークンを引き続き使用し、長期的には公式アカウントおよび Messaging API を用いた通知へ切り替える方針です。

## 機能

- 📊 **自動データ取得**: 平日の5回（09:15, 09:30, 12:00, 12:45, 14:30）に自動実行
- 💾 **データ保存**: ランキングデータをJSON形式でGitHubリポジトリに保存
- 📲 **LINE通知**: 取得成功・失敗を LINE（Messaging API への移行準備中）で通知
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

### 3. 通知設定（Messaging API移行準備中）

> **重要なお知らせ**  
> LINE Notify は 2025年3月31日で提供終了予定です。短期的には従来の LINE Notify を利用できますが、長期運用に向けては LINE 公式アカウントと **Messaging API** への移行が必要です。

#### 3-1. 短期: LINE Notify（サービス終了まで）

1. [LINE Notify](https://notify-bot.line.me/ja/) にログインし、`1:1でLINE Notifyから通知を受け取る` トークンを発行  
2. トークンを GitHub Secrets (`Settings → Secrets and variables → Actions`) に `LINE_NOTIFY_TOKEN` として登録  
3. Actions で `Test Secret Configuration` ワークフローを実行し、設定済みであることを確認

#### 3-2. 中長期: LINE Messaging API への移行

1. [LINE Developers](https://developers.line.biz/) でプロバイダとチャネル（Messaging API）を作成  
2. チャネルアクセストークン（長期）を取得し、安全に保管  
3. GitHub Secrets には `LINE_CHANNEL_ACCESS_TOKEN` 等の新しい名前で登録する予定  
4. `notify_line.py` を Messaging API の push メッセージ送信に対応させる（別チケットで対応予定）

詳しくは [docs/tickets/ticket-06-notify-line.md](./docs/tickets/ticket-06-notify-line.md) および [docs/tickets/ticket-10-github-secrets.md](./docs/tickets/ticket-10-github-secrets.md) を参照してください。

### 4. GitHub Actions の有効化

GitHub リポジトリの Actions タブで、ワークフローを有効化します。

## 使い方

### ローカルでのスクレイピング実行

```bash
cd src
python scrape_rankings.py
```

実行時刻が `config.TIME_SLOTS` に含まれない場合、処理はスキップされます。テスト目的で時間帯を強制したい場合は、コードを一時的に変更するか、`scrape_ranking()` を直接呼び出してください（テスト後は必ず元に戻すこと）。

### GitHub Actions での手動実行

1. GitHub リポジトリの **Actions** タブを開く
2. `Scheduled Ranking Scrape` ワークフローを選択
3. **Run workflow** をクリックすると即時実行されます

### 自動実行スケジュール (JST)

- 09:15 / 09:30 / 12:00 — 朝のランキング
- 12:45 / 14:30 — 午後のランキング

取得結果は `data/morning/` または `data/afternoon/` に `ranking_YYYYMMDD_HHMM.json` として保存されます。

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
- **LINE Messaging API（移行準備中）**: 通知サービス

## ドキュメント

詳細なドキュメントは [docs/](./docs/) を参照してください。

- [要件定義](./docs/requirements.md)
- [アーキテクチャ設計](./docs/architecture.md)
- [技術スタック](./docs/technical-stack.md)
- [実装ガイド](./docs/implementation-guide.md)
- [セットアップガイド](./docs/setup-guide.md)
- [チケット管理](./docs/tickets/TICKETS.md)

## トラブルシューティング

- **403 Forbidden が返る**  
  User-Agent がブロックされた可能性があります。`src/config.py` の `USER_AGENT` を最新のブラウザ識別子へ更新してください。

- **LINE通知が届かない**  
  GitHub Secrets に `LINE_NOTIFY_TOKEN` が設定されているか確認し、ローカルでテストする場合は環境変数に設定してから `notify_line.py` を実行します（チケット #6 参照）。

- **JSONが保存されない / 処理がスキップされる**  
  実行時刻が `TIME_SLOTS` に一致しているか、または祝日・週末でないかを確認してください。`python check_workday.py` で営業日かどうかを判定できます。

- **HTML構造の変更でデータが取得できない**  
  `scrape_ranking()` 内のテーブル解析ロジックを最新のページ構造に合わせて更新してください（チケット #5）。

## 開発状況

現在開発中です。進捗は [チケット管理](./docs/tickets/TICKETS.md) で確認できます。

## ライセンス

MIT License

## 貢献

Issue や Pull Request を歓迎します。大きな変更を行う前に、まず Issue を作成して提案内容を共有してください。

---

**注意**: このシステムは松井証券の公開情報を自動取得するものです。利用規約を遵守し、適切な間隔でアクセスしてください。
