# GitHub Actions セットアップ手順

このドキュメントは、松井証券ランキング自動取得システムをGitHub Actionsで動作させるためのセットアップ手順を説明します。

## 📋 前提条件

- ✅ ローカルテスト完了 (Ticket #8)
- ✅ GitHub Actions ワークフロー作成完了 (Ticket #7)
- ✅ Git リポジトリ初期化完了
- ✅ 初回コミット作成完了

## 🚀 セットアップ手順

### Step 1: GitHubリポジトリの作成

1. [GitHub](https://github.com) にログイン
2. 右上の `+` → `New repository` をクリック
3. リポジトリ情報を入力:
   - **Repository name**: `market` (または任意の名前)
   - **Description**: `松井証券ランキング自動取得システム`
   - **Visibility**: `Private` (推奨) または `Public`
   - **Initialize this repository**: すべて**チェックなし** (既にローカルで初期化済み)
4. `Create repository` をクリック

### Step 2: リモートリポジトリの設定とプッシュ

ローカルのターミナルで以下を実行:

```bash
# リモートリポジトリを追加（URLは自分のリポジトリに置き換える）
git remote add origin https://github.com/YOUR_USERNAME/market.git

# メインブランチにプッシュ
git push -u origin main
```

**認証方法:**
- HTTPS: GitHub Personal Access Token (PAT) を使用
- SSH: SSH鍵を設定済みの場合は `git@github.com:YOUR_USERNAME/market.git`

> **重要:** LINE Notify は 2025年3月31日に提供終了予定です。本手順は終了までの暫定対応であり、Messaging API への移行を別途進めてください。

### Step 3: LINE Notify トークンの取得

1. [LINE Notify](https://notify-bot.line.me/ja/) にアクセス
2. LINEアカウントでログイン
3. 右上のメニュー → `マイページ` をクリック
4. `トークンを発行する` をクリック
5. トークン情報を入力:
   - **トークン名**: `松井証券ランキング通知` (任意)
   - **通知を送信するトークルーム**: 通知を受け取りたいトークルームを選択
6. `発行する` をクリック
7. **表示されたトークンをコピー** (一度しか表示されないので注意！)

### Step 4: GitHub Secrets の設定

1. GitHubリポジトリページを開く
2. `Settings` タブをクリック
3. 左サイドバーの `Secrets and variables` → `Actions` をクリック
4. `New repository secret` をクリック
5. Secret情報を入力:
   - **Name**: `LINE_NOTIFY_TOKEN`
   - **Secret**: Step 3でコピーしたLINE Notifyトークンを貼り付け
6. `Add secret` をクリック

### Step 5: GitHub Actions ワークフローの確認

1. GitHubリポジトリページで `Actions` タブをクリック
2. `Scheduled Ranking Scrape` ワークフローが表示されることを確認
3. 緑色のチェックマークが表示されていれば、YAMLに問題なし

### Step 6: 手動実行テスト (workflow_dispatch)

1. `Actions` タブ → `Scheduled Ranking Scrape` をクリック
2. 右側の `Run workflow` ボタンをクリック
3. ブランチが `main` になっていることを確認
4. `Run workflow` をクリックして実行開始

### Step 7: 実行ログの確認

1. ワークフロー実行が開始されると、リストに新しい実行が表示される
2. 実行中の項目をクリック
3. `scrape` ジョブをクリック
4. 各Stepを展開してログを確認:

**確認すべきポイント:**
- ✅ `Checkout repository`: リポジトリのクローン成功
- ✅ `Set up Python`: Python 3.11 のセットアップ成功
- ✅ `Install dependencies`: 依存関係のインストール成功
- ✅ `Run scraper`: スクレイピング実行成功
- ✅ `Configure Git`: Git設定成功
- ✅ `Commit and push data`: データファイルのコミット・プッシュ成功

### Step 8: 取得データの確認

1. ワークフロー実行が完了したら、リポジトリのトップページに戻る
2. `data/morning/` または `data/afternoon/` ディレクトリを開く
3. 新しいJSONファイルが追加されていることを確認
4. ファイルをクリックして内容を確認:
   - ランキングデータが10件含まれているか
   - JSON形式が正しいか
   - 日本語が文字化けしていないか

### Step 9: LINE通知の確認

1. スマートフォンでLINEアプリを開く
2. Step 3で選択したトークルームに通知が届いていることを確認

**期待されるメッセージ例:**
```
✅ [成功] 20251021_0915
朝ランキング取得完了

📊 ベスト3:
1位: キオクシアホールディングス (285A)
2位: ソフトバンクグループ (9984)
3位: レーザーテック (6920)
```

### Step 10: Cron自動実行の確認 (任意)

手動実行が成功したら、自動実行の動作確認を行います。

**実行スケジュール (JST):**
- 朝: 09:15, 09:30, 12:00
- 午後: 12:45, 14:30

**確認方法:**
1. 上記の時刻になったら、`Actions` タブを確認
2. 新しいワークフロー実行が自動的に開始されているか確認
3. 実行完了後、データファイルとLINE通知を確認

**注意事項:**
- GitHub Actions の cron は数分遅延する可能性があります
- 土日祝日は実行されません（スクリプト内で判定）

## 🔍 トラブルシューティング

### ワークフローが実行されない

**原因:**
- YAML構文エラー
- ワークフローファイルが `.github/workflows/` にない

**対処法:**
```bash
# YAML構文チェック
yamllint .github/workflows/scrape_rankings.yml

# ファイルの存在確認
ls -la .github/workflows/
```

### スクレイピングが失敗する

**原因:**
- HTML構造の変更
- 403 Forbidden エラー
- ネットワークエラー

**対処法:**
1. ログでエラーメッセージを確認
2. ローカルで同じスクリプトを実行してみる
3. 松井証券のサイトが正常か確認

### LINE通知が届かない（LINE Notify）

**原因:**
- `LINE_NOTIFY_TOKEN` が未設定または間違っている
- トークンが無効化されている

**対処法:**
1. GitHub Secrets の設定を確認
2. LINE Notify のトークンを再発行
3. Secrets を更新

> LINE Notify は 2025-03-31 に終了予定です。Messaging API へ移行後はチャネルアクセストークンを用いた設定へ切り替えてください。

### Git push が失敗する

**原因:**
- `GITHUB_TOKEN` の権限不足
- ブランチ保護ルール

**対処法:**
1. リポジトリの `Settings` → `Actions` → `General` を開く
2. `Workflow permissions` を `Read and write permissions` に設定
3. `Save` をクリック

### 依存関係のインストールが失敗する

**原因:**
- `requirements.txt` の問題
- PyPIサーバーの一時的な問題

**対処法:**
1. ローカルで `pip install -r requirements.txt` を実行
2. エラーメッセージを確認
3. 必要に応じて `requirements.txt` を修正

## 📊 成功の確認チェックリスト

- [ ] GitHubリポジトリが作成されている
- [ ] ローカルのコードがプッシュされている
- [ ] `LINE_NOTIFY_TOKEN` が Secrets に設定されている
- [ ] 手動実行 (workflow_dispatch) が成功する
- [ ] すべてのStepが緑色のチェックマークになっている
- [ ] データファイルがリポジトリにコミットされている
- [ ] LINE通知が正しく送信されている
- [ ] JSONファイルの内容が正しい
- [ ] ログにエラーがない
- [ ] 実行時間が15分以内である

## 🎉 完了後

すべてのチェックリストが完了したら、システムの本番運用が開始されます！

定期的に以下を確認してください:
- データファイルが正しく保存されているか
- LINE通知が届いているか
- ワークフローが失敗していないか (Actions タブで確認)
- 松井証券のサイト構造に変更がないか

## 📚 関連ドキュメント

- [Ticket #7: GitHub Actions ワークフロー作成](./tickets/ticket-07-github-actions.md)
- [Ticket #9: GitHub Actions 統合テスト](./tickets/ticket-09-github-actions-test.md)
- [セットアップガイド](./setup-guide.md)
- [アーキテクチャ](./architecture.md)
