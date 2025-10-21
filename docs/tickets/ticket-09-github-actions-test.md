# Ticket #9: GitHub Actions 統合テスト

## 📋 基本情報

- **優先度:** 🟡 中
- **ステータス:** ⬜️ 未着手
- **推定工数:** 30分
- **依存関係:** #7, #8
- **担当者:** -
- **作成日:** 2025-10-21
- **最終更新:** 2025-10-21

---

## 📝 概要

GitHub Actions 環境で実際にワークフローを実行し、本番環境での動作確認を行う。

---

## 🎯 タスク一覧

- [ ] GitHub Secrets の設定確認
  - [ ] LINE_NOTIFY_TOKEN が設定されているか確認
- [ ] workflow_dispatch での手動実行
  - [ ] Actions タブから手動トリガー
  - [ ] 実行ログの確認
- [ ] 各Stepの動作確認
  - [ ] Checkout が成功するか
  - [ ] Python セットアップが成功するか
  - [ ] 依存関係インストールが成功するか
  - [ ] スクレイピングスクリプトが成功するか
  - [ ] Git コミット・プッシュが成功するか
- [ ] 取得データの確認
  - [ ] data/ ディレクトリにファイルが追加されているか
  - [ ] コミットメッセージが適切か
  - [ ] JSON形式が正しいか
- [ ] LINE通知の受信確認
  - [ ] 成功メッセージが届くか
  - [ ] メッセージ内容が適切か
- [ ] ログの確認
  - [ ] エラーログがないか
  - [ ] 実行時間は適切か（15分以内）
- [ ] Cron自動実行の確認（任意）
  - [ ] 指定時刻に自動実行されるか
  - [ ] 平日のみ実行されるか

---

## 📦 成果物

### テスト結果レポート

**ファイル:** `docs/github-actions-test-report.md`（任意）

```markdown
# GitHub Actions テスト結果レポート

## テスト実施日
2025-10-__

## テスト種別
- [x] 手動実行（workflow_dispatch）
- [ ] Cron自動実行

## テスト結果

### Workflow実行
- Run ID: #12345
- 実行時間: 2分30秒
- ステータス: ✅ Success

### 各Stepの結果
| Step | Status | Time |
|------|--------|------|
| Checkout repository | ✅ | 5s |
| Set up Python | ✅ | 15s |
| Install dependencies | ✅ | 30s |
| Run scraper | ✅ | 45s |
| Configure Git | ✅ | 2s |
| Commit and push data | ✅ | 10s |

### 取得データ確認
- ファイル: `data/morning/ranking_20251021_0915.json`
- サイズ: 5.2 KB
- 件数: 10件
- コミットID: abc1234

### LINE通知
- ✅ 受信確認
- メッセージ内容: 適切

## 問題点
なし

## 次のステップ
本番運用開始
```

---

## ✅ 完了条件

- [ ] GitHub Secrets が正しく設定されている
- [ ] 手動実行が成功する
- [ ] すべてのStepがエラーなく完了する
- [ ] データファイルが正しくコミットされる
- [ ] LINE通知が正しく送信される
- [ ] ログにエラーがない
- [ ] 実行時間が15分以内である
- [ ] テスト結果が記録されている

---

## 🧪 テスト方法

### 1. GitHub Secrets 確認

1. GitHubリポジトリページを開く
2. `Settings` → `Secrets and variables` → `Actions`
3. `LINE_NOTIFY_TOKEN` が存在するか確認

### 2. 手動実行

1. GitHubリポジトリページを開く
2. `Actions` タブをクリック
3. `Scheduled Ranking Scrape` ワークフローを選択
4. `Run workflow` ボタンをクリック
5. ブランチ（main）を選択
6. `Run workflow` を確定

### 3. ログ確認

```
Actions → Workflow runs → 最新のrun を選択

各Stepをクリックして詳細ログを確認:
- Checkout repository
  ✅ リポジトリがクローンされている

- Set up Python
  ✅ Python 3.11.x がインストールされている

- Install dependencies
  ✅ requests, beautifulsoup4, lxml, jpholiday がインストールされている

- Run scraper
  ✅ スクレイピングが成功している
  ✅ JSONファイルが保存されている
  ✅ LINE通知が送信されている

- Configure Git
  ✅ Git設定が完了している

- Commit and push data
  ✅ ファイルがコミットされている
  ✅ リモートリポジトリにプッシュされている
```

### 4. データファイル確認

```bash
# ローカルで最新のコミットをpull
git pull origin main

# データファイルの確認
ls -la data/morning/
ls -la data/afternoon/

# JSON内容の確認
cat data/morning/ranking_*.json | jq .

# コミット履歴の確認
git log --oneline data/
```

### 5. LINE通知確認

スマートフォンで LINE 通知を確認。

**期待されるメッセージ:**
```
✅ [成功] 2025-10-21 09:15
朝ランキング取得完了

📊 ベスト3:
1位: サンプル株式 (1234)
2位: テスト銘柄 (5678)
3位: デモ会社 (9012)
```

---

## 📌 注意事項

- **初回実行時**: 依存関係のインストールに時間がかかる可能性
- **時刻のずれ**: GitHub Actions の cron は数分遅延する可能性
- **Secrets の扱い**: ログには `***` としてマスクされる
- **コミット権限**: GITHUB_TOKEN は自動的に付与される
- **平日判定**: Cron は UTC で平日を判定、jpholiday で日本の祝日を除外

---

## 🔍 トラブルシューティング

### よくある問題と対処法

| 問題 | 原因候補 | 対処法 |
|------|---------|--------|
| Workflow実行失敗 | YAML構文エラー | yamllint で検証 |
| Python setup失敗 | バージョン指定ミス | 3.11 を明示 |
| 依存関係エラー | requirements.txt 問題 | ローカルで動作確認 |
| スクリプト失敗 | 環境差異 | ログを詳細確認 |
| LINE通知失敗 | Token未設定 | Secrets を確認 |
| Git push失敗 | 権限不足 | GITHUB_TOKEN の権限確認 |

### ログの見方

```
# 成功時
✅ マークがすべてのStepに付いている

# 失敗時
❌ マークが付いているStepを展開
エラーメッセージを確認
```

---

## 🔗 関連チケット

- **依存元:** #7 (GitHub Actions ワークフロー), #8 (ローカルテスト)
- **ブロック対象:** #11 (README.md充実化)
- **関連:** #10 (GitHub Secrets設定)

---

## 📚 参考資料

- [GitHub Actions ドキュメント](https://docs.github.com/actions)
- [Workflow実行ログの見方](https://docs.github.com/en/actions/monitoring-and-troubleshooting-workflows/using-workflow-run-logs)

---

## 📝 作業ログ

| 日時 | 作業内容 | 備考 |
|------|---------|------|
| 2025-10-21 | チケット作成 | - |
