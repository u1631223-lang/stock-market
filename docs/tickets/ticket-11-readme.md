# Ticket #11: README.md 充実化

## 📋 基本情報

- **優先度:** 🟢 低
- **ステータス:** ⬜️ 未着手
- **推定工数:** 30分
- **依存関係:** #9
- **担当者:** -
- **作成日:** 2025-10-21
- **最終更新:** 2025-10-21

---

## 📝 概要

プロジェクトの README.md を充実させ、第三者が理解・利用できるようにドキュメントを整備する。

---

## 🎯 タスク一覧

- [ ] プロジェクト概要の記載
- [ ] 機能説明の追加
- [ ] セットアップ手順の記載
- [ ] 使い方の説明
- [ ] ディレクトリ構造の説明
- [ ] スクリーンショットの追加（任意）
- [ ] トラブルシューティングセクション追加
- [ ] ライセンス情報の記載
- [ ] バッジの追加（任意）
- [ ] 貢献ガイドライン（任意）

---

## 📦 成果物

### ファイル: `README.md`

**期待される構成:**

```markdown
# 松井証券ランキング自動取得システム

[![GitHub Actions](https://github.com/username/market/workflows/Scheduled%20Ranking%20Scrape/badge.svg)](https://github.com/username/market/actions)

## 概要

松井証券のデイトレードランキングページから、指定された時刻に自動的にランキングデータを取得し、JSON形式で保存するシステムです。GitHub Actions で定時実行し、結果を LINE で通知します。

## 機能

- 📊 **自動データ取得**: 平日の5回（09:15, 09:30, 12:00, 12:45, 14:30）に自動実行
- 💾 **データ保存**: ランキングデータをJSON形式でGitHubリポジトリに保存
- 📲 **LINE通知**: 取得成功・失敗を LINE Notify で通知
- 🗓️ **営業日判定**: 土日祝日は自動的にスキップ
- 🔄 **リトライ機能**: ネットワークエラー時は自動リトライ

## 取得対象

- **朝のランキング**: https://finance.matsui.co.jp/ranking-day-trading-morning/
- **午後のランキング**: https://finance.matsui.co.jp/ranking-day-trading-afternoon/
- **取得データ**: ベスト10の銘柄情報（順位、コード、銘柄名、株価など）

## セットアップ

### 1. リポジトリのクローン

\```bash
git clone https://github.com/username/market.git
cd market
\```

### 2. 依存関係のインストール

\```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
\```

### 3. LINE Notify トークンの取得

1. [LINE Notify](https://notify-bot.line.me/ja/) にアクセス
2. トークンを発行
3. GitHub Secrets に `LINE_NOTIFY_TOKEN` として登録

### 4. GitHub Actions の有効化

GitHub リポジトリの Actions タブで、ワークフローを有効化します。

## 使い方

### ローカル実行

\```bash
cd src
python scrape_rankings.py
\```

**注意**: スケジュール時間外に実行する場合は、`main()` 内で `target` を強制指定してください。

### 手動実行（GitHub Actions）

1. GitHub リポジトリの Actions タブを開く
2. "Scheduled Ranking Scrape" を選択
3. "Run workflow" をクリック

### 自動実行

GitHub Actions が以下の時刻（JST）に自動実行します:
- 朝: 09:15, 09:30, 12:00
- 午後: 12:45, 14:30

## ディレクトリ構造

\```
market/
├── .github/
│   └── workflows/
│       └── scrape_rankings.yml  # GitHub Actions ワークフロー
├── docs/                         # ドキュメント
│   ├── tickets/                  # チケット管理
│   ├── requirements.md
│   ├── architecture.md
│   └── ...
├── src/                          # ソースコード
│   ├── config.py                 # 設定ファイル
│   ├── check_workday.py          # 営業日判定
│   ├── scrape_rankings.py        # メインスクリプト
│   └── notify_line.py            # LINE通知
├── data/                         # データ保存先
│   ├── morning/                  # 朝のランキング
│   └── afternoon/                # 午後のランキング
├── requirements.txt              # Python依存関係
├── .gitignore
├── CLAUDE.md
└── README.md
\```

## データ形式

JSONファイル例: `data/morning/ranking_20251020_0915.json`

\```json
{
  "datetime": "20251020_0915",
  "url": "https://finance.matsui.co.jp/...",
  "scraped_at": "2025-10-20T09:15:03+09:00",
  "rankings": [
    {
      "rank": "1",
      "code": "1234",
      "name": "サンプル株式会社",
      "price": "1,234",
      "change": "+56",
      "change_percent": "+4.76%",
      "volume": "12,345,678",
      "value": "1,234,567,890"
    }
  ]
}
\```

## トラブルシューティング

### "ランキングテーブルが見つかりません" エラー

**原因**: HTML構造が変更された可能性があります。

**対処法**:
1. ブラウザでランキングページを開く
2. DevTools (F12) でテーブル構造を確認
3. `src/scrape_rankings.py` の `scrape_ranking()` 関数を調整

### LINE通知が届かない

**原因**: トークンが正しく設定されていない可能性があります。

**対処法**:
1. GitHub Secrets で `LINE_NOTIFY_TOKEN` が設定されているか確認
2. ローカルで `export LINE_NOTIFY_TOKEN="token"` を設定してテスト

### 403 Forbidden エラー

**原因**: User-Agent が設定されていない、または拒否された可能性があります。

**対処法**:
- `src/config.py` の `USER_AGENT` を最新のブラウザ文字列に更新

## 技術スタック

- **Python 3.11+**
- **requests**: HTTP通信
- **Beautiful Soup**: HTMLパース
- **jpholiday**: 日本の祝日判定
- **GitHub Actions**: 定時実行
- **LINE Notify**: 通知サービス

## ライセンス

MIT License

## 作者

[Your Name]

## 貢献

Issue や Pull Request を歓迎します！

---

詳細なドキュメントは [docs/](./docs/) を参照してください。
\```

---

## ✅ 完了条件

- [ ] README.md が存在する
- [ ] プロジェクト概要が明確に記載されている
- [ ] セットアップ手順が詳細に記載されている
- [ ] 使い方が説明されている
- [ ] ディレクトリ構造が記載されている
- [ ] トラブルシューティングセクションがある
- [ ] ライセンス情報が記載されている
- [ ] Markdown形式が正しい
- [ ] リンクが正しく機能する

---

## 🧪 確認方法

### Markdown プレビュー

```bash
# VSCodeでプレビュー
code README.md
# Cmd+Shift+V でプレビュー

# ブラウザで確認
open README.md  # macOS
```

### リンクチェック

```bash
# markdownlintでチェック（任意）
npm install -g markdownlint-cli
markdownlint README.md
```

### GitHub での表示確認

1. README.md をコミット・プッシュ
2. GitHubリポジトリページで表示確認
3. レイアウトが崩れていないか確認

---

## 📌 注意事項

- **スクリーンショット**: 任意だが、あると理解しやすい
- **バッジ**: GitHub Actions のステータスバッジを追加すると見栄えが良い
- **個人情報**: メールアドレスなど公開したくない情報は記載しない
- **更新頻度**: プロジェクトの変更に合わせて適宜更新

---

## 🔍 オプション機能

### GitHub Actions ステータスバッジ

```markdown
[![GitHub Actions](https://github.com/username/market/workflows/Scheduled%20Ranking%20Scrape/badge.svg)](https://github.com/username/market/actions)
```

### 目次（Table of Contents）

```markdown
## 目次

- [概要](#概要)
- [機能](#機能)
- [セットアップ](#セットアップ)
- [使い方](#使い方)
- ...
```

---

## 🔗 関連チケット

- **依存元:** #9 (GitHub Actions統合テスト) - 全機能完成後に作成
- **ブロック対象:** なし

---

## 📚 参考資料

- [GitHub README ベストプラクティス](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes)
- [Markdown ガイド](https://www.markdownguide.org/)

---

## 📝 作業ログ

| 日時 | 作業内容 | 備考 |
|------|---------|------|
| 2025-10-21 | チケット作成 | - |
