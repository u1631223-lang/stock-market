# GitHub Secrets セットアップサマリー

## 完了した作業

### 1. テストワークフローの作成 ✅

**ファイル:** `.github/workflows/test-secret.yml`

シークレットが正しく設定されているか確認するための専用ワークフローを作成しました。

**実行方法:**
```bash
# GitHubリポジトリの Actions タブ
# → "Test Secret Configuration" を選択
# → "Run workflow" をクリック
```

**確認内容:**
- `LINE_NOTIFY_TOKEN` が設定されているか
- トークンの文字数
- LINE Notify APIへの実際の接続テスト

### 2. コードベースの確認 ✅

**確認結果:**

| 項目 | 状態 | 詳細 |
|------|------|------|
| 環境変数の取得 | ✅ 正しい | `notify_line.py` で `os.getenv("LINE_NOTIFY_TOKEN")` を使用 |
| .gitignore設定 | ✅ 完了 | `.env` ファイルが除外対象に含まれている |
| ワークフロー設定 | ✅ 完了 | `scrape_rankings.yml` で `secrets.LINE_NOTIFY_TOKEN` を参照 |

**使用箇所:**
- `src/notify_line.py:35` - 環境変数から取得
- `src/notify_line.py:38` - トークン未設定時のエラー処理
- `src/notify_line.py:143-150` - テスト実行時の確認処理
- `.github/workflows/scrape_rankings.yml:39` - GitHub Actions で参照

### 3. ドキュメント整備 ✅

**README.md の更新:**

セットアップ手順を詳細化しました:
- トークンの発行手順（6ステップ）
- GitHub Secrets への登録手順（6ステップ）
- 設定確認方法（テストワークフロー実行）

**参照リンク:**
- 詳細手順: [ticket-10-github-secrets.md](./tickets/ticket-10-github-secrets.md)

## ユーザーが実施する手動作業

以下の作業は、ユーザー自身が実施する必要があります:

### 1. LINE Notify トークンの発行

1. https://notify-bot.line.me/ja/ にアクセス
2. LINEアカウントでログイン
3. マイページ → `トークンを発行する`
4. トークン名: `市場ランキング通知`
5. 通知先: `1:1でLINE Notifyから通知を受け取る`
6. **トークンをコピー**（一度しか表示されない）

### 2. GitHub Secrets への登録

1. GitHubリポジトリ → `Settings` タブ
2. `Secrets and variables` → `Actions`
3. `New repository secret`
4. Name: `LINE_NOTIFY_TOKEN`
5. Secret: 発行したトークンを貼り付け
6. `Add secret` で保存

### 3. 動作確認

**方法1: テストワークフローで確認**
```bash
Actions タブ → "Test Secret Configuration" → Run workflow
```

期待される結果:
```
✅ LINE_NOTIFY_TOKEN is set (length: XX characters)
```

**方法2: ローカルでテスト**
```bash
export LINE_NOTIFY_TOKEN="your_actual_token"
cd src
python notify_line.py
```

LINE に通知が届けば成功です。

## セキュリティチェックリスト

- [x] `.env` が `.gitignore` に含まれている
- [x] コード内にトークンのハードコーディングがない
- [x] 環境変数から動的に取得している
- [x] GitHub Actions でシークレットを参照している
- [ ] **ユーザー作業:** LINE Notify トークンを発行
- [ ] **ユーザー作業:** GitHub Secrets に登録
- [ ] **ユーザー作業:** テストワークフローで確認

## トラブルシューティング

### トークンが設定されていないエラー

**エラーメッセージ:**
```
❌ LINE_NOTIFY_TOKEN is not set
```

**解決方法:**
1. GitHub Secrets に `LINE_NOTIFY_TOKEN` が登録されているか確認
2. Secret名のスペルが正確か確認（大文字小文字も一致）
3. ワークフローファイルで `secrets.LINE_NOTIFY_TOKEN` を参照しているか確認

### LINE 通知が届かない

**確認事項:**
1. トークンが正しく発行されているか
2. LINE Notify のマイページでトークンが有効か確認
3. トークンの通知先設定が正しいか確認

**再発行手順:**
1. LINE Notify マイページで古いトークンを削除
2. 新しいトークンを発行
3. GitHub Secrets を更新

## 関連ファイル

- `.github/workflows/test-secret.yml` - シークレット確認用テストワークフロー
- `.github/workflows/scrape_rankings.yml` - メインワークフロー（シークレット使用）
- `src/notify_line.py` - LINE Notify 実装
- `.gitignore` - 環境変数ファイル除外設定
- `README.md` - セットアップ手順
- `docs/tickets/ticket-10-github-secrets.md` - 詳細手順書

## 次のステップ

チケット #10 の残りの作業:

1. **ユーザー作業:** LINE Notify トークンを発行
2. **ユーザー作業:** GitHub Secrets に登録
3. **ユーザー作業:** テストワークフロー実行で確認
4. チケット #9 (GitHub Actions統合テスト) に進む

---

**作成日:** 2025-10-21
**最終更新:** 2025-10-21
