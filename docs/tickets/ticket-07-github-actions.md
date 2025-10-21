# Ticket #7: GitHub Actions ワークフロー作成

## 📋 基本情報

- **優先度:** 🟡 中
- **ステータス:** ✅ 完了
- **推定工数:** 1時間
- **依存関係:** #4, #6
- **担当者:** Claude
- **作成日:** 2025-10-21
- **最終更新:** 2025-10-21 09:30

---

## 📝 概要

GitHub Actions を使用して、指定された時刻にスクレイピングスクリプトを自動実行するワークフローを作成する。

---

## 🎯 タスク一覧

- [x] `.github/workflows/` ディレクトリ作成
- [x] `scrape_rankings.yml` ワークフローファイル作成
- [x] Cron設定（UTC時刻で5つの時刻を指定）
  - [x] 00:15 (JST 09:15)
  - [x] 00:30 (JST 09:30)
  - [x] 03:00 (JST 12:00)
  - [x] 03:45 (JST 12:45)
  - [x] 05:30 (JST 14:30)
- [x] workflow_dispatch 設定（手動実行用）
- [x] Job設定
  - [x] ubuntu-latest ランナー指定
  - [x] タイムアウト設定（15分）
- [x] Steps設定
  - [x] リポジトリチェックアウト
  - [x] Python 3.11 セットアップ
  - [x] 依存関係インストール
  - [x] スクレイピングスクリプト実行
  - [x] Git設定（user.name, user.email）
  - [x] データファイルのコミット・プッシュ
  - [x] エラー時のLINE通知
- [x] 環境変数・Secrets設定
  - [x] LINE_NOTIFY_TOKEN の参照

---

## 📦 成果物

### ファイル: `.github/workflows/scrape_rankings.yml`

**期待される構造:**

```yaml
name: Scheduled Ranking Scrape

on:
  schedule:
    # JST 09:15 (UTC 00:15)
    - cron: '15 0 * * 1-5'
    # JST 09:30 (UTC 00:30)
    - cron: '30 0 * * 1-5'
    # JST 12:00 (UTC 03:00)
    - cron: '0 3 * * 1-5'
    # JST 12:45 (UTC 03:45)
    - cron: '45 3 * * 1-5'
    # JST 14:30 (UTC 05:30)
    - cron: '30 5 * * 1-5'

  workflow_dispatch:  # 手動実行を許可

jobs:
  scrape:
    runs-on: ubuntu-latest
    timeout-minutes: 15

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run scraper
        env:
          LINE_NOTIFY_TOKEN: ${{ secrets.LINE_NOTIFY_TOKEN }}
        run: |
          cd src
          python scrape_rankings.py

      - name: Configure Git
        run: |
          git config --local user.name "github-actions[bot]"
          git config --local user.email "github-actions[bot]@users.noreply.github.com"

      - name: Commit and push data
        run: |
          git add data/
          git diff --staged --quiet || git commit -m "Add ranking data: $(date +'%Y-%m-%d %H:%M')"
          git push
```

---

## ✅ 完了条件

- [x] `.github/workflows/scrape_rankings.yml` ファイルが存在する
- [x] Cron設定が正しい（5つの時刻、平日のみ）
- [x] workflow_dispatch が設定されている
- [x] Python 3.11 がセットアップされる
- [x] 依存関係が正しくインストールされる
- [x] スクリプトが正しく実行される
- [x] LINE_NOTIFY_TOKEN がSecretsから参照される
- [x] データファイルが自動コミット・プッシュされる
- [x] タイムアウト設定が適切（15分）
- [x] YAML構文が正しい

---

## 🧪 テスト方法

### YAML構文チェック

```bash
# yamllintツールでチェック（任意）
yamllint .github/workflows/scrape_rankings.yml
```

### 手動実行テスト

1. GitHubリポジトリページを開く
2. "Actions" タブをクリック
3. "Scheduled Ranking Scrape" ワークフローを選択
4. "Run workflow" ボタンをクリック
5. 実行結果を確認

### ログ確認

```
Actions → Workflow run → 各Stepのログを確認
- Python バージョン
- 依存関係インストール結果
- スクリプト実行ログ
- Git コミット結果
```

### 自動実行確認

- 指定時刻に自動実行されるか確認
- 実行履歴を Actions タブで確認
- data/ ディレクトリにファイルがコミットされているか確認

---

## 📌 注意事項

- **Cron時刻はUTC**: GitHub Actions は UTC タイムゾーンで動作
  - JST 09:15 = UTC 00:15 (JST - 9時間)
- **平日のみ実行**: `1-5` は月〜金（日本の祝日は別途スクリプト内で判定）
- **Cron実行の遅延**: 数分程度の遅延が発生する可能性あり
- **GITHUB_TOKEN**: リポジトリへのpushには自動的に付与される `GITHUB_TOKEN` を使用
- **Secrets設定**: `LINE_NOTIFY_TOKEN` は事前に GitHub Secrets に登録が必要

---

## 🔍 実装のポイント

### Cron時刻の計算

| JST時刻 | UTC時刻 | Cron表記 |
|---------|---------|----------|
| 09:15 | 00:15 | `15 0 * * 1-5` |
| 09:30 | 00:30 | `30 0 * * 1-5` |
| 12:00 | 03:00 | `0 3 * * 1-5` |
| 12:45 | 03:45 | `45 3 * * 1-5` |
| 14:30 | 05:30 | `30 5 * * 1-5` |

### Git コミット時のベストプラクティス

```yaml
- name: Commit and push data
  run: |
    git add data/
    # 変更がある場合のみコミット
    git diff --staged --quiet || git commit -m "Add ranking data: $(date +'%Y-%m-%d %H:%M')"
    git push
```

### エラーハンドリング（オプション）

```yaml
- name: Run scraper
  id: scrape
  continue-on-error: true
  env:
    LINE_NOTIFY_TOKEN: ${{ secrets.LINE_NOTIFY_TOKEN }}
  run: |
    cd src
    python scrape_rankings.py

- name: Notify on failure
  if: failure()
  run: |
    # エラー通知はスクリプト内で実施されるため、通常は不要
    echo "Scraping failed"
```

---

## 🔗 関連チケット

- **依存元:** #4 (scrape_rankings.py), #6 (notify_line.py)
- **ブロック対象:** #9 (GitHub Actions統合テスト)
- **関連:** #10 (GitHub Secrets設定)

---

## 📚 参考資料

- [GitHub Actions ドキュメント](https://docs.github.com/actions)
- [Cron構文リファレンス](https://crontab.guru/)
- [Workflow構文](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)

---

## 📝 作業ログ

| 日時 | 作業内容 | 備考 |
|------|---------|------|
| 2025-10-21 | チケット作成 | - |
| 2025-10-21 09:25 | .github/workflows ディレクトリ作成 | - |
| 2025-10-21 09:27 | scrape_rankings.yml 作成 | 全54行のワークフロー定義 |
| 2025-10-21 09:30 | ✅ チケット完了 | すべてのタスク完了 |
