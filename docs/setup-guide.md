# セットアップガイド

このガイドでは、松井証券ランキング自動取得システムをゼロからセットアップする手順を説明します。

---

## 前提条件

### 必要なもの
- [ ] GitHubアカウント
- [ ] LINEアカウント
- [ ] Python 3.11以上（ローカルテスト用）
- [ ] Git（ローカル開発用）

### 推奨環境
- **OS**: macOS / Windows / Linux
- **エディタ**: Visual Studio Code

---

## セットアップ手順

### ステップ1: LINE Notifyトークンの取得

#### 1-1. LINE Notify公式サイトにアクセス
https://notify-bot.line.me/

#### 1-2. LINEアカウントでログイン
右上の「ログイン」ボタンをクリック

#### 1-3. トークンを発行
1. 右上のアカウント名をクリック → 「マイページ」
2. 「トークンを発行する」ボタンをクリック
3. トークン名を入力（例: `松井証券ランキング通知`）
4. 通知を送信するトークルームを選択
   - **推奨**: `1:1でLINE Notifyから通知を受け取る`
5. 「発行する」ボタンをクリック

#### 1-4. トークンをコピー
発行されたトークンをコピーして保存（このトークンは一度しか表示されません）

```
例: abcdefghijklmnopqrstuvwxyz1234567890ABCD
```

⚠️ **重要**: このトークンは他人に見せないでください。

---

### ステップ2: GitHubリポジトリの作成

#### 2-1. GitHubにログイン
https://github.com/

#### 2-2. 新しいリポジトリを作成
1. 右上の「+」→「New repository」
2. リポジトリ名: `market`
3. 説明（任意）: `松井証券ランキング自動取得システム`
4. 可視性:
   - **Private** 推奨（スクレイピング対象を公開しないため）
   - Publicでも動作可能
5. 「Create repository」をクリック

#### 2-3. リポジトリURLをメモ
```
https://github.com/YOUR_USERNAME/market.git
```

---

### ステップ3: ローカル開発環境のセットアップ

#### 3-1. リポジトリをクローン（またはディレクトリ作成）

**既存リポジトリの場合**:
```bash
git clone https://github.com/YOUR_USERNAME/market.git
cd market
```

**新規作成の場合**:
```bash
mkdir market
cd market
git init
git branch -M main
```

#### 3-2. ディレクトリ構造を作成
```bash
mkdir -p .github/workflows
mkdir -p src
mkdir -p docs
mkdir -p data/morning
mkdir -p data/afternoon
```

確認:
```bash
tree -L 2
```

出力例:
```
.
├── .github
│   └── workflows
├── data
│   ├── afternoon
│   └── morning
├── docs
└── src
```

#### 3-3. Pythonバージョン確認
```bash
python3 --version
```

Python 3.11以上であることを確認。

#### 3-4. 仮想環境の作成（推奨）
```bash
python3 -m venv venv
```

**仮想環境の有効化**:

macOS/Linux:
```bash
source venv/bin/activate
```

Windows:
```cmd
venv\Scripts\activate
```

仮想環境が有効になると、プロンプトに `(venv)` が表示されます。

---

### ステップ4: 依存関係のインストール

#### 4-1. requirements.txt を作成
```bash
cat > requirements.txt << 'EOF'
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=5.0.0
jpholiday>=0.1.10
EOF
```

#### 4-2. パッケージをインストール
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4-3. インストール確認
```bash
pip list
```

以下が表示されればOK:
```
beautifulsoup4  4.12.x
jpholiday       0.1.x
lxml            5.x.x
requests        2.31.x
```

---

### ステップ5: ソースコードの作成

#### 5-1. config.py を作成
`src/config.py` を作成し、[implementation-guide.md](./implementation-guide.md#1-configpy---設定管理) の内容をコピー。

#### 5-2. check_workday.py を作成
`src/check_workday.py` を作成し、[implementation-guide.md](./implementation-guide.md#2-check_workdaypy---営業日判定) の内容をコピー。

#### 5-3. notify_line.py を作成
`src/notify_line.py` を作成し、[implementation-guide.md](./implementation-guide.md#3-notify_linepy---line通知) の内容をコピー。

#### 5-4. scrape_rankings.py を作成
`src/scrape_rankings.py` を作成し、[implementation-guide.md](./implementation-guide.md#4-scrape_rankingspy---メインスクリプト) の内容をコピー。

#### 5-5. __init__.py を作成
```bash
touch src/__init__.py
```

---

### ステップ6: ローカルテスト

#### 6-1. 営業日判定テスト
```bash
cd src
python check_workday.py
```

期待される出力:
```
今日の日付: 2025-10-20
曜日: 月
取引日: True
```

#### 6-2. LINE通知テスト
```bash
export LINE_NOTIFY_TOKEN="YOUR_TOKEN_HERE"  # Windowsの場合: set LINE_NOTIFY_TOKEN=...
python notify_line.py
```

LINEに「[TEST] LINE Notify接続テスト」が届けばOK。

#### 6-3. スクレイピングテスト（時間帯外でもテスト可能）

**一時的に時間帯判定を無効化してテスト**:

`scrape_rankings.py` の `main()` 関数内で以下を変更:
```python
# コメントアウト
# target = get_current_time_slot()
# if not target:
#     ...

# 手動で設定
target = "morning"  # または "afternoon"
```

実行:
```bash
export LINE_NOTIFY_TOKEN="YOUR_TOKEN_HERE"
python scrape_rankings.py
```

成功すると:
- `data/morning/ranking_YYYYMMDD_HHMM.json` が作成される
- LINEに成功通知が届く

⚠️ **テスト後は必ず元に戻すこと**

---

### ステップ7: GitHub Actionsワークフローの作成

#### 7-1. ワークフローファイルを作成
`.github/workflows/scrape_rankings.yml` を作成し、[implementation-guide.md](./implementation-guide.md#5-githubworkflowsscrape_rankingsyml---github-actions) の内容をコピー。

---

### ステップ8: .gitignore の作成

```bash
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
dist/
*.egg-info/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Environment variables
.env

# Test
test_output/
EOF
```

---

### ステップ9: READMEの作成

```bash
cat > README.md << 'EOF'
# 松井証券ランキング自動取得システム

## 概要
松井証券のデイトレードランキングを定時自動取得し、データ保存・LINE通知を行うシステム。

## 機能
- 平日の指定時刻に自動実行（09:15, 09:30, 12:00, 12:45, 14:30）
- ベスト10銘柄のデータを取得
- JSON形式でデータ保存
- LINE Notifyで取得完了通知

## 技術スタック
- Python 3.11+
- GitHub Actions
- LINE Notify

## セットアップ
詳細は [docs/setup-guide.md](./docs/setup-guide.md) を参照。

## ドキュメント
- [要件定義](./docs/requirements.md)
- [アーキテクチャ設計](./docs/architecture.md)
- [技術スタック](./docs/technical-stack.md)
- [実装ガイド](./docs/implementation-guide.md)
- [セットアップガイド](./docs/setup-guide.md)

## ライセンス
MIT
EOF
```

---

### ステップ10: GitHubにプッシュ

#### 10-1. 全ファイルをステージング
```bash
git add .
```

#### 10-2. コミット
```bash
git commit -m "feat: initial implementation of ranking scraper"
```

#### 10-3. リモートリポジトリを追加（新規作成の場合）
```bash
git remote add origin https://github.com/YOUR_USERNAME/market.git
```

#### 10-4. プッシュ
```bash
git push -u origin main
```

---

### ステップ11: GitHub Secretsの設定

#### 11-1. GitHubリポジトリページを開く
https://github.com/YOUR_USERNAME/market

#### 11-2. Settings → Secrets and variables → Actions
1. 「Settings」タブをクリック
2. 左メニューの「Secrets and variables」→「Actions」

#### 11-3. Secretを追加
1. 「New repository secret」ボタンをクリック
2. Name: `LINE_NOTIFY_TOKEN`
3. Secret: （ステップ1で取得したトークンを貼り付け）
4. 「Add secret」ボタンをクリック

#### 11-4. 確認
「LINE_NOTIFY_TOKEN」が一覧に表示されればOK。

---

### ステップ12: ワークフローの手動実行（初回テスト）

#### 12-1. Actionsタブを開く
https://github.com/YOUR_USERNAME/market/actions

#### 12-2. ワークフローを選択
左メニューから「Scheduled Ranking Scrape」をクリック

#### 12-3. 手動実行
1. 「Run workflow」ボタンをクリック
2. ブランチを選択（main）
3. 「Run workflow」ボタンをクリック

#### 12-4. 実行結果を確認
1. 実行中のワークフローが表示される
2. クリックして詳細ログを確認
3. 各ステップの成功/失敗を確認

**成功の確認**:
- ✅ すべてのステップが緑色のチェックマーク
- ✅ LINEに通知が届く
- ✅ `data/` ディレクトリに新しいコミットが追加される

---

## トラブルシューティング

### 問題1: ワークフロー実行時にLINE通知が届かない

**原因**:
- LINE_NOTIFY_TOKEN が正しく設定されていない
- トークンが無効

**対処法**:
1. GitHub Secrets を確認
2. トークンを再発行して再設定
3. ローカルでテスト実行して確認

---

### 問題2: HTML構造エラー

**エラーメッセージ**:
```
AttributeError: ランキングテーブルが見つかりません
```

**原因**:
- ページのHTML構造が想定と異なる

**対処法**:
1. ブラウザで対象ページを開く
2. 開発者ツール（F12）で要素を検査
3. `src/scrape_rankings.py` の `scrape_ranking()` 関数を修正

**デバッグ方法**:
```python
# scrape_rankings.py の scrape_ranking() 内に追加
print(soup.prettify()[:2000])  # HTML の先頭2000文字を出力
```

---

### 問題3: データが保存されない

**原因**:
- data/ ディレクトリが存在しない
- 権限エラー

**対処法**:
```bash
mkdir -p data/morning data/afternoon
git add data/.gitkeep  # 空ディレクトリを保持
git commit -m "chore: add data directories"
git push
```

---

### 問題4: cronが実行されない

**原因**:
- GitHub Actionsのcronは不安定（数分の遅延あり）
- リポジトリが長期間更新されていない

**対処法**:
1. 手動実行（workflow_dispatch）で動作確認
2. 数日間様子を見る
3. 必要に応じて cron の時刻を調整

---

## 運用開始後の確認事項

### 日次チェック
- [ ] LINE通知が届いているか
- [ ] data/ ディレクトリに新しいファイルが追加されているか
- [ ] GitHub Actions の実行履歴を確認

### 週次チェック
- [ ] エラーが発生していないか
- [ ] 取得データの内容が正しいか

### 月次チェック
- [ ] 依存パッケージのアップデート確認
- [ ] HTML構造の変更確認

---

## 次のステップ

セットアップ完了後、以下の拡張が可能です：

1. **データ分析**: 蓄積データから傾向分析
2. **可視化**: グラフ・ダッシュボード作成
3. **差分通知**: 前回からの順位変動を通知
4. **CSV出力**: データ分析用のCSV変換

---

## サポート

問題が解決しない場合は、以下を確認してください：

1. [実装ガイド](./implementation-guide.md)
2. [トラブルシューティング](./implementation-guide.md#トラブルシューティング)
3. GitHub Actionsのログ詳細

---

## まとめ

このガイドに従うことで、以下が完了します：

✅ LINE Notifyトークンの取得
✅ GitHubリポジトリの作成
✅ ローカル開発環境のセットアップ
✅ ソースコードの作成
✅ ローカルテストの実行
✅ GitHub Secretsの設定
✅ 自動実行の開始

おめでとうございます！システムは正常に動作しています。🎉
