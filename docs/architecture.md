# アーキテクチャ設計

## システム構成図

```
┌─────────────────────────────────────────────────────────────┐
│                     GitHub Actions (Scheduler)               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Cron Triggers (UTC)                                 │  │
│  │  • 00:15 (JST 09:15) - Morning                       │  │
│  │  • 00:30 (JST 09:30) - Morning                       │  │
│  │  • 03:00 (JST 12:00) - Morning                       │  │
│  │  • 03:45 (JST 12:45) - Afternoon                     │  │
│  │  • 05:30 (JST 14:30) - Afternoon                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                            ↓                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Python Runtime Environment                          │  │
│  │  • Python 3.11                                       │  │
│  │  • Dependencies from requirements.txt                │  │
│  └──────────────────────────────────────────────────────┘  │
│                            ↓                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  1. 営業日チェック (check_workday.py)                │  │
│  │     ├─ 土日判定                                       │  │
│  │     └─ 祝日判定 (jpholiday)                          │  │
│  └──────────────────────────────────────────────────────┘  │
│                            ↓                                 │
│                      [営業日の場合]                          │
│                            ↓                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  2. スクレイピング実行 (scrape_rankings.py)          │  │
│  │     ├─ 時刻判定 (朝 or 午後)                         │  │
│  │     ├─ HTTPリクエスト (User-Agent設定)               │  │
│  │     ├─ HTMLパース (BeautifulSoup)                    │  │
│  │     └─ データ抽出 (ベスト10)                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                            ↓                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  3. データ保存                                        │  │
│  │     └─ JSON形式で data/ 配下に保存                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                            ↓                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  4. Git操作                                           │  │
│  │     ├─ git add data/                                  │  │
│  │     ├─ git commit                                     │  │
│  │     └─ git push                                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                            ↓                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  5. 通知送信 (notify_line.py)                        │  │
│  │     └─ LINE Notify API                               │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
        ┌───────────────────┴───────────────────┐
        ↓                                       ↓
┌───────────────────┐                 ┌─────────────────┐
│  GitHub Repository│                 │   LINE Notify   │
│   (Data Storage)  │                 │  (User's Phone) │
│                   │                 │                 │
│  data/            │                 │  📱 通知メッセージ │
│  ├─ morning/      │                 │  「ランキング    │
│  └─ afternoon/    │                 │   取得完了」    │
└───────────────────┘                 └─────────────────┘
```

## コンポーネント設計

### 1. check_workday.py
**責務**: 営業日（取引日）の判定

```python
# 入力: datetime.date
# 出力: bool (True = 営業日, False = 休日)
```

**判定ロジック**:
1. 土曜日（weekday=5）→ False
2. 日曜日（weekday=6）→ False
3. jpholiday.is_holiday() → False
4. 上記以外 → True

**依存関係**:
- `datetime` (標準ライブラリ)
- `jpholiday` (外部ライブラリ)

---

### 2. scrape_rankings.py
**責務**: ランキングデータの取得とJSON保存

**主要関数**:

```python
def is_trading_day() -> bool
    """営業日かどうかを判定"""

def get_current_time_slot() -> Optional[str]
    """現在時刻から取得対象を判定 ('morning' or 'afternoon')"""

def scrape_ranking(url: str) -> List[Dict]
    """URLからランキングデータを取得"""
    # User-Agent設定
    # リトライロジック
    # HTMLパース
    # データ抽出

def save_to_json(data: Dict, target: str) -> str
    """JSONファイルとして保存"""
    # ファイルパス生成
    # ディレクトリ作成
    # JSON書き込み

def main()
    """メイン処理のオーケストレーション"""
```

**データフロー**:
```
1. is_trading_day() → 営業日チェック
2. get_current_time_slot() → 時間帯判定
3. scrape_ranking(url) → データ取得
4. save_to_json(data) → 保存
5. notify_line(message) → 通知
```

**エラーハンドリング**:
- `requests.exceptions.RequestException` → リトライ
- `requests.exceptions.Timeout` → リトライ
- `AttributeError` (HTML構造変更) → エラー通知
- その他の例外 → エラー通知

---

### 3. notify_line.py
**責務**: LINE Notifyへの通知送信

**主要関数**:

```python
def send_line_notify(message: str, token: str) -> bool
    """LINE Notifyにメッセージを送信"""
    # LINE Notify API呼び出し
    # ステータスコード確認
    # エラーハンドリング
```

**メッセージフォーマット**:
```
[成功] 2025-10-20 09:15
朝ランキング取得完了
ベスト3:
1. 銘柄A (1234)
2. 銘柄B (5678)
3. 銘柄C (9012)
```

---

### 4. GitHub Actions Workflow
**責務**: 定時実行のスケジューリング

**ファイル**: `.github/workflows/scrape_rankings.yml`

**主要設定**:
- **Trigger**: cron (5つの時刻)
- **Runner**: ubuntu-latest
- **Timeout**: 15分
- **Steps**:
  1. Checkout
  2. Python Setup (3.11)
  3. Install Dependencies
  4. Run Scraper
  5. Commit & Push
  6. (失敗時) Error Notification

---

## データストア設計

### ディレクトリ構造
```
data/
├── morning/
│   ├── ranking_20251020_0915.json
│   ├── ranking_20251020_0930.json
│   ├── ranking_20251020_1200.json
│   ├── ranking_20251021_0915.json
│   └── ...
└── afternoon/
    ├── ranking_20251020_1245.json
    ├── ranking_20251020_1430.json
    ├── ranking_20251021_1245.json
    └── ...
```

### JSONスキーマ

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "datetime": {
      "type": "string",
      "pattern": "^\\d{8}_\\d{4}$",
      "description": "YYYYMMdd_HHmm形式"
    },
    "url": {
      "type": "string",
      "format": "uri"
    },
    "scraped_at": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601形式（JST）"
    },
    "rankings": {
      "type": "array",
      "maxItems": 10,
      "items": {
        "type": "object",
        "properties": {
          "rank": {"type": "string"},
          "code": {"type": "string"},
          "name": {"type": "string"},
          "price": {"type": "string"},
          "change": {"type": "string"},
          "change_percent": {"type": "string"},
          "volume": {"type": "string"},
          "value": {"type": "string"}
        },
        "required": ["rank", "code", "name"]
      }
    }
  },
  "required": ["datetime", "url", "scraped_at", "rankings"]
}
```

---

## セキュリティ設計

### 1. 機密情報の管理

**GitHub Secrets**:
```
LINE_NOTIFY_TOKEN: xxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**環境変数として利用**:
```python
import os
LINE_TOKEN = os.environ.get('LINE_NOTIFY_TOKEN')
```

### 2. アクセス制御
- GitHub Actionsのワークフロー実行は main ブランチのみ
- Personal Access Token は使用しない（GITHUB_TOKEN を使用）

### 3. 入力検証
- URLは定数として定義（外部入力なし）
- HTMLパース時はエスケープ処理済みのBeautifulSoupを使用

---

## スケーラビリティ考慮

### 現在の制約
- GitHub Actions: 月2,000分まで無料
- 1回の実行: 約1-2分
- 1日5回 × 約20営業日/月 = 約100回/月
- **月間使用時間**: 約100-200分 → 十分に余裕あり

### 将来の拡張
1. **取得頻度の増加**: 分単位での取得も可能
2. **複数市場対応**: 東証以外の市場も追加可能
3. **データ分析機能**: 別ワークフローで集計・分析
4. **Webhook通知**: リアルタイムの差分通知

---

## 可用性・信頼性設計

### 1. リトライ戦略

```python
# 指数バックオフ
retry_delays = [5, 10, 20]  # 秒
max_retries = 3

for attempt in range(max_retries):
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        break
    except requests.exceptions.RequestException as e:
        if attempt < max_retries - 1:
            time.sleep(retry_delays[attempt])
        else:
            # エラー通知して終了
            raise
```

### 2. タイムアウト設定
- **HTTPリクエスト**: 30秒
- **GitHub Actionsジョブ全体**: 15分

### 3. エラー通知
- スクレイピング失敗 → LINE通知
- HTML構造変更検知 → LINE通知
- GitHub Actions失敗 → GitHubメール通知

### 4. ログ記録
- 標準出力に実行ログ出力
- GitHub Actions上で確認可能
- エラースタックトレースも記録

---

## モニタリング・運用

### 1. 実行結果の確認方法

**GitHub Actions画面**:
- Workflow runs で実行履歴確認
- ログ詳細の閲覧
- 失敗時のエラー内容確認

**LINE通知**:
- リアルタイムで成功・失敗を確認
- スマートフォンで即座に把握

**Gitコミット履歴**:
- data/ ディレクトリのコミット履歴で取得状況確認
- ファイル数 = 取得成功回数

### 2. アラート条件

| 条件 | アラート方法 | 優先度 |
|------|-------------|--------|
| スクレイピング失敗（3回リトライ後） | LINE通知 | 高 |
| HTML構造変更検知 | LINE通知 | 高 |
| GitHub Actions失敗 | GitHubメール | 中 |
| 営業日スキップ | ログのみ | 低 |

### 3. メンテナンス作業

**定期メンテナンス**:
- 月1回: ライブラリのアップデート確認
- 四半期1回: HTML構造の変更確認
- 年1回: 祝日データの更新確認（jpholidayが自動対応）

**障害発生時**:
1. LINE通知で気づく
2. GitHub Actions ログを確認
3. 原因特定（ネットワーク/HTML構造変更/その他）
4. 必要に応じてコード修正
5. 修正後、手動実行で動作確認

---

## パフォーマンス設計

### 1. 実行時間目標
- 営業日判定: < 0.1秒
- HTTPリクエスト: < 5秒
- HTMLパース: < 1秒
- JSON保存: < 0.5秒
- LINE通知: < 2秒
- **合計**: < 10秒（正常時）

### 2. 最適化ポイント
- **lxml パーサー使用**: html.parserより高速
- **必要な要素のみ抽出**: 全HTMLを保存しない
- **並列処理なし**: 1つのURLのみなので不要

### 3. リソース使用量
- **メモリ**: < 100MB
- **CPU**: 軽微（パース処理のみ）
- **ディスク**: 1ファイル約5-10KB
  - 1日5ファイル × 20営業日 × 12ヶ月 = 約1,200ファイル/年
  - 約6-12MB/年 → ストレージ問題なし

---

## テスト戦略

### 1. 単体テスト（今後追加検討）
- `check_workday.py`: 土日祝判定のテスト
- `scrape_rankings.py`: HTMLパースのテスト（モックHTML使用）
- `notify_line.py`: API呼び出しのテスト（モックレスポンス使用）

### 2. 統合テスト
- **手動実行**: workflow_dispatch で動作確認
- **実際のページ取得**: 本番URLで動作確認

### 3. 本番監視
- 毎日の実行結果を LINE通知 で確認
- 異常時は即座に対応

---

## 技術的制約・前提条件

### 1. GitHub Actions の制約
- cronは最短で1分間隔（今回は十分）
- 実行時刻に数分の遅延が発生する可能性
- タイムゾーンはUTCのみ（JSTに変換して指定）

### 2. スクレイピングの制約
- 松井証券のHTML構造に依存
- ページ構造変更時はコード修正が必要
- robots.txt は確認済み（問題なし想定）

### 3. LINE Notify の制約
- 1時間あたり1,000回まで（今回は十分）
- メッセージ長は最大1,000文字

---

## 運用開始までの手順

1. **リポジトリ作成**: GitHub上に market リポジトリ作成
2. **コード実装**: 全スクリプトとワークフローファイル作成
3. **LINE Notify設定**:
   - LINE Notifyでトークン発行
   - GitHub Secretsに登録
4. **初回テスト実行**: workflow_dispatch で手動実行
5. **HTML構造確認**: 取得データが正しいか確認
6. **本番運用開始**: cron自動実行の監視開始
