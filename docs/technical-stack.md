# 技術スタック詳細

## 開発言語

### Python 3.11+
**選定理由**:
- スクレイピングに最適なライブラリが豊富
- GitHub Actionsでの実行が容易
- 可読性が高く、メンテナンスしやすい
- データ処理（JSON、CSV）が標準ライブラリで対応可能

**バージョン**: 3.11以上
- 型ヒントの改善
- パフォーマンス向上
- GitHub Actions ubuntu-latest でサポート

---

## 依存ライブラリ

### 1. requests (2.31.0+)
**用途**: HTTPリクエスト

**機能**:
- URLからHTMLを取得
- User-Agentヘッダーのカスタマイズ
- タイムアウト設定
- リトライ制御

**インストール**:
```bash
pip install requests
```

**使用例**:
```python
import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}
response = requests.get(url, headers=headers, timeout=30)
```

**代替案**:
- `urllib3`: 低レベルAPI、複雑
- `httpx`: 非同期対応だが今回は不要

---

### 2. beautifulsoup4 (4.12.0+)
**用途**: HTMLパース・データ抽出

**機能**:
- HTML文書のDOM操作
- CSSセレクタでの要素検索
- テキスト抽出
- テーブルデータの取得

**インストール**:
```bash
pip install beautifulsoup4
```

**使用例**:
```python
from bs4 import BeautifulSoup

soup = BeautifulSoup(html, 'lxml')
table = soup.find('table', class_='ranking-table')
rows = table.find_all('tr')
```

**代替案**:
- `lxml` 単体: より高速だが使いにくい
- `parsel`: Scrapyベース、今回はオーバースペック

---

### 3. lxml (5.0.0+)
**用途**: BeautifulSoupのパーサー（高速化）

**機能**:
- HTMLの高速パース
- XPath対応
- メモリ効率が良い

**インストール**:
```bash
pip install lxml
```

**使用例**:
```python
# BeautifulSoupで自動的にlxmlパーサーを使用
soup = BeautifulSoup(html, 'lxml')  # 'html.parser'より高速
```

**代替案**:
- `html.parser`: 標準ライブラリだが遅い
- `html5lib`: 厳密だが非常に遅い

---

### 4. jpholiday (0.1.10+)
**用途**: 日本の祝日判定

**機能**:
- 指定日が祝日かどうか判定
- 祝日名の取得
- 年間の祝日リスト取得

**インストール**:
```bash
pip install jpholiday
```

**使用例**:
```python
import jpholiday
import datetime

date = datetime.date(2025, 10, 20)
if jpholiday.is_holiday(date):
    print(f"{date} は祝日です")
```

**祝日データ**:
- 国民の祝日（元日、成人の日、建国記念の日、天皇誕生日など）
- 振替休日
- 自動更新（新しい祝日にも対応）

**代替案**:
- 自前の祝日リスト: メンテナンスが大変
- `workalendar`: 海外対応だが重い

---

### 5. pytz または zoneinfo (タイムゾーン処理)
**用途**: 日本時間（JST）の扱い

**Python 3.9+**: zoneinfo（標準ライブラリ）を推奨
```python
from zoneinfo import ZoneInfo
from datetime import datetime

jst = ZoneInfo("Asia/Tokyo")
now = datetime.now(jst)
```

**Python 3.8以下**: pytz
```python
import pytz
from datetime import datetime

jst = pytz.timezone('Asia/Tokyo')
now = datetime.now(jst)
```

---

## インフラ・プラットフォーム

### GitHub Actions
**用途**: 定時実行基盤

**機能**:
- cronスケジュール実行
- 複数の時刻指定
- 手動実行（workflow_dispatch）
- シークレット管理
- ログ保存

**設定ファイル**: `.github/workflows/scrape_rankings.yml`

**料金**:
- Publicリポジトリ: 無料
- Privateリポジトリ: 月2,000分まで無料

**実行環境**:
- **OS**: ubuntu-latest (Ubuntu 22.04)
- **CPU**: 2コア
- **RAM**: 7GB
- **ストレージ**: 14GB

**代替案**:
- **AWS Lambda + EventBridge**: 有料、セットアップ複雑
- **Google Cloud Scheduler + Cloud Functions**: 有料、セットアップ複雑
- **Heroku Scheduler**: 無料枠縮小、不安定
- **cron + VPS**: サーバー管理が必要

---

### GitHub Repository
**用途**: コードとデータの管理

**機能**:
- バージョン管理
- データの永続化（data/ディレクトリ）
- コミット履歴で取得状況を追跡
- GitHub Pagesでの可視化（将来拡張）

**リポジトリ設定**:
- **可視性**: Private推奨（スクレイピング対象を公開しないため）
- **ブランチ保護**: mainブランチへの直接pushは許可（GitHub Actions用）

**ストレージ**:
- 無料枠: 500MB（十分）
- データ: 約10KB/日 → 年間約3.6MB

---

## 外部サービス

### LINE Notify
**用途**: リアルタイム通知

**公式サイト**: https://notify-bot.line.me/

**機能**:
- LINEへのメッセージ送信
- 画像・スタンプ送信（今回は未使用）
- トークンベース認証

**API エンドポイント**:
```
POST https://notify-api.line.me/api/notify
```

**リクエスト例**:
```python
import requests

def send_line_notify(message: str, token: str) -> bool:
    url = 'https://notify-api.line.me/api/notify'
    headers = {'Authorization': f'Bearer {token}'}
    data = {'message': message}
    response = requests.post(url, headers=headers, data=data)
    return response.status_code == 200
```

**料金**: 完全無料

**制限**:
- 1時間あたり1,000回まで
- メッセージ長: 最大1,000文字

**トークン取得手順**:
1. LINE Notify公式サイトにアクセス
2. LINEアカウントでログイン
3. 「マイページ」→「トークンを発行する」
4. トークン名を入力（例: 松井証券ランキング通知）
5. 通知先を選択（1:1でLINE Notifyから受信）
6. 発行されたトークンをコピー
7. GitHub Secretsに登録

**代替案**:
- **Slack**: ビジネス向け、個人利用には重い
- **Discord**: ゲーマー向け、日本での普及率低い
- **Email**: 遅延が大きい、見逃しやすい
- **Telegram**: 日本での普及率低い

---

## 開発ツール

### エディタ・IDE
- **Visual Studio Code**: 推奨
- **PyCharm**: Python専用IDE
- **vim/emacs**: 軽量エディタ

**推奨拡張機能（VSCode）**:
- Python (Microsoft)
- Pylance (型チェック)
- YAML (GitHub Actions編集)
- JSON (データ確認)

---

### バージョン管理
**Git + GitHub**:
- コミット粒度: 機能単位
- ブランチ戦略: mainブランチのみ（シンプル運用）
- コミットメッセージ:
  ```
  chore: update rankings [skip ci]
  feat: add retry logic
  fix: handle HTML structure change
  docs: update README
  ```

---

### パッケージ管理

#### requirements.txt
```txt
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=5.0.0
jpholiday>=0.1.10
```

**インストールコマンド**:
```bash
pip install -r requirements.txt
```

**アップデート確認**:
```bash
pip list --outdated
```

---

## 実行環境の違い

### ローカル開発環境
- **OS**: macOS / Windows / Linux
- **Python**: 3.11+（pyenv等で管理）
- **タイムゾーン**: システム依存
- **テスト方法**: `python src/scrape_rankings.py` で直接実行

### GitHub Actions環境
- **OS**: ubuntu-latest (Linux)
- **Python**: setup-pythonアクションで3.11指定
- **タイムゾーン**: UTC（cronもUTC指定）
- **実行方法**: ワークフローで自動実行

**環境差異の吸収**:
```python
# OSに依存しないパス指定
import os
data_dir = os.path.join('data', 'morning')

# タイムゾーン明示
from zoneinfo import ZoneInfo
jst = ZoneInfo('Asia/Tokyo')
now = datetime.now(jst)
```

---

## セキュリティツール・対策

### 1. シークレット管理
**GitHub Secrets**:
- UI: Settings → Secrets and variables → Actions
- 変数名: `LINE_NOTIFY_TOKEN`
- アクセス: `${{ secrets.LINE_NOTIFY_TOKEN }}`

### 2. 依存関係の脆弱性チェック
**Dependabot**（GitHub標準機能）:
- 自動的に脆弱性をチェック
- Pull Requestで更新提案

**手動チェック**:
```bash
pip install safety
safety check -r requirements.txt
```

### 3. コード品質
**Linter（今後追加検討）**:
- `flake8`: PEP8準拠チェック
- `black`: コード自動整形
- `mypy`: 型チェック

---

## パフォーマンス計測

### 実行時間の計測
```python
import time

start = time.time()
# 処理
end = time.time()
print(f"実行時間: {end - start:.2f}秒")
```

### メモリ使用量
```python
import psutil
import os

process = psutil.Process(os.getpid())
print(f"メモリ使用量: {process.memory_info().rss / 1024 / 1024:.2f} MB")
```

---

## ログ・デバッグ

### 標準出力ログ
```python
import datetime

def log(message: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

# 使用例
log("スクレイピング開始")
log("データ取得成功")
```

### GitHub Actions ログ
- 各ステップの出力を自動保存
- 90日間保持
- ダウンロード可能

---

## 今後の技術的拡張案

### 1. データベース導入
現在: JSON ファイル
将来: SQLite / PostgreSQL

**メリット**:
- クエリでの集計・分析が容易
- インデックスによる高速検索

### 2. データ可視化
**技術候補**:
- Matplotlib / Plotly（グラフ生成）
- Streamlit（Webダッシュボード）
- GitHub Pages（静的サイト公開）

### 3. 機械学習
**技術候補**:
- scikit-learn（ランキング予測）
- pandas（データ前処理）
- numpy（数値計算）

### 4. API化
**技術候補**:
- FastAPI（REST API）
- Uvicorn（ASGIサーバー）
- Railway / Render（ホスティング）

---

## まとめ

| カテゴリ | 技術 | 理由 |
|---------|------|------|
| 言語 | Python 3.11+ | スクレイピングに最適 |
| HTTPクライアント | requests | シンプルで実績豊富 |
| HTMLパーサー | BeautifulSoup + lxml | 高速で使いやすい |
| 祝日判定 | jpholiday | 日本の祝日に特化 |
| 実行基盤 | GitHub Actions | 無料で簡単 |
| 通知 | LINE Notify | 日本で普及、無料 |
| データ形式 | JSON | 柔軟性が高い |
| ストレージ | Git Repository | バージョン管理と保存を兼ねる |

この技術スタックにより、**低コスト・低メンテナンス・高信頼性**のシステムを構築可能です。
