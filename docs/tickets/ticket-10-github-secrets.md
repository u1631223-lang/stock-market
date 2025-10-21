# Ticket #10: GitHub Secrets 設定

## 📋 基本情報

- **優先度:** 🟡 中
- **ステータス:** 🟢 進行中
- **推定工数:** 15分
- **依存関係:** なし
- **担当者:** -
- **作成日:** 2025-10-21
- **最終更新:** 2025-10-21

---

## 📝 概要

LINE Notify トークンを GitHub Secrets に安全に保存し、GitHub Actions から参照できるようにする。  
また、LINE Notify のサービス終了（2025-03-31）に備え、Messaging API 用のシークレット計画を立てる。

---

## 🎯 タスク一覧

- [ ] LINE Notify トークンの取得
  - [ ] LINE Notify サイトにアクセス
  - [ ] トークンを発行
  - [ ] トークンを安全に記録
- [ ] GitHub Secrets への登録
  - [ ] GitHubリポジトリの Settings を開く
  - [ ] Secrets and variables → Actions を選択
  - [ ] New repository secret をクリック
  - [ ] Name: `LINE_NOTIFY_TOKEN` を設定
  - [ ] Value: 取得したトークンを貼り付け
  - [ ] Add secret で保存
- [ ] 設定の確認
  - [ ] Secrets 一覧に表示されているか確認
  - [ ] 値がマスクされているか確認
- [ ] 動作確認
  - [ ] GitHub Actions で参照できるかテスト
- [ ] Messaging API への移行準備
  - [ ] LINE Developers でチャネルアクセストークンを発行
  - [ ] 新シークレット名（例: `LINE_CHANNEL_ACCESS_TOKEN`）を決定
  - [ ] Secrets 登録手順をREADME/Setup Guideに反映

---

## 📦 成果物

### LINE Notify トークン
- 発行済みトークン（安全に保管）
- GitHub Secrets への登録完了

---

## ✅ 完了条件

- [ ] LINE Notify トークンが発行されている
- [ ] トークンが GitHub Secrets に登録されている
- [ ] Secret名が `LINE_NOTIFY_TOKEN` である
- [ ] GitHub Actions から参照可能である
- [ ] トークンが漏洩していない（コードやログに含まれていない）
- [ ] Messaging API 用チャネルアクセストークンの登録計画がまとまっている

---

## 🧪 設定手順

### 1. LINE Notify トークン取得

1. **LINE Notify にアクセス**
   - URL: https://notify-bot.line.me/ja/

2. **ログイン**
   - LINEアカウントでログイン

3. **トークン発行**
   - 右上のメニュー → `マイページ`
   - `トークンを発行する` ボタンをクリック

4. **トークン設定**
   - トークン名: `市場ランキング通知` など、わかりやすい名前
   - 通知を送信するトークルーム: `1:1でLINE Notifyから通知を受け取る` を選択
   - `発行する` ボタンをクリック

5. **トークンをコピー**
   - 表示されたトークンをコピー
   - ⚠️ **重要**: この画面は二度と表示されないので、安全に記録

### 2. GitHub Secrets 登録（LINE Notify / Messaging API）

1. **GitHubリポジトリを開く**
   - ブラウザで自分のリポジトリページにアクセス

2. **Settings タブをクリック**

3. **Secrets and variables → Actions を選択**

4. **New repository secret をクリック**

5. **Secret を追加**
   - Name: `LINE_NOTIFY_TOKEN`
   - Secret: コピーしたトークンを貼り付け
   - `Add secret` ボタンをクリック

6. **確認**
   - Secrets 一覧に `LINE_NOTIFY_TOKEN` が表示される
   - 値は `***` でマスクされている

> Messaging API へ移行する際は、同じ手順で `LINE_CHANNEL_ACCESS_TOKEN` など新しい名称で登録します。

### 3. 動作確認

**方法1: GitHub Actions で確認**

`.github/workflows/test-secret.yml`（一時ファイル）
```yaml
name: Test Secret

on:
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Check secret exists
        env:
          TOKEN: ${{ secrets.LINE_NOTIFY_TOKEN }}
        run: |
          if [ -z "$TOKEN" ]; then
            echo "❌ SECRET not set"
            exit 1
          else
            echo "✅ SECRET is set (length: ${#TOKEN})"
          fi
```

手動実行して、ログに `✅ SECRET is set` が表示されることを確認。

**方法2: 実際のワークフローで確認**

#9 の GitHub Actions 統合テストで確認。

---

## 📌 注意事項

- **トークンは一度しか表示されない**: 発行時に必ず記録する
- **トークンを共有しない**: 他人に見せない、コードに含めない
- **Git コミットに含めない**: `.env` ファイルは `.gitignore` に追加
- **定期的な再発行**: セキュリティ向上のため、定期的にトークンを再発行
- **不要になったトークンは削除**: LINE Notify のマイページから削除可能

---

## 🔍 セキュリティベストプラクティス

### ❌ やってはいけないこと

```python
# コードにトークンを直接書く
LINE_TOKEN = "xxxxxxxxxxxxxxxxxxxxxxxxxxx"  # ❌ 絶対ダメ

# .env ファイルを Git にコミット
git add .env  # ❌ ダメ
```

### ✅ 正しい方法

```python
# 環境変数から取得
import os
LINE_TOKEN = os.getenv("LINE_NOTIFY_TOKEN")  # ✅ 正しい

# .gitignore に追加
# .gitignore
.env
```

### トークン漏洩時の対処

1. LINE Notify のマイページで該当トークンを削除
2. 新しいトークンを発行
3. GitHub Secrets を更新
4. 漏洩したトークンを使用していた箇所を確認

---

## 🔗 関連チケット

- **依存元:** なし（いつでも設定可能）
- **ブロック対象:** #9 (GitHub Actions統合テスト)
- **関連:** #6 (notify_line.py), #7 (GitHub Actions)

---

## 📚 参考資料

- [LINE Notify](https://notify-bot.line.me/ja/)
- [GitHub Secrets ドキュメント](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

---

## 📝 作業ログ

| 日時 | 作業内容 | 備考 |
|------|---------|------|
| 2025-10-21 | チケット作成 | - |
| 2025-10-21 | シークレット確認用テストワークフロー作成 | `.github/workflows/test-secret.yml` |
| 2025-10-21 | README.mdにLINE Notify設定手順を詳細化 | セットアップ手順を拡充 |
| 2025-10-21 | コードベースでのシークレット使用状況確認 | `notify_line.py:35,38,143,145,147,150` で正しく環境変数から取得 |
| 2025-10-21 | .gitignoreに.env除外設定を確認 | 既に設定済み（35-37行目） |
| 2025-10-21 | Messaging API 移行計画を追記 | Secrets命名と移行タスクを整理 |
