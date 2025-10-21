# 実装ガイド

## ファイル構成

```
market/
├── .github/
│   └── workflows/
│       └── scrape_rankings.yml       # GitHub Actions定義
├── src/
│   ├── __init__.py                   # パッケージ初期化
│   ├── check_workday.py              # 営業日判定モジュール
│   ├── scrape_rankings.py            # メインスクレイピングスクリプト
│   ├── notify_line.py                # LINE通知モジュール
│   └── config.py                     # 設定ファイル
├── data/                             # データ保存先（自動生成）
│   ├── morning/
│   └── afternoon/
├── tests/                            # テストコード（今後追加）
│   ├── test_check_workday.py
│   └── test_scrape_rankings.py
├── docs/                             # ドキュメント
│   ├── requirements.md
│   ├── architecture.md
│   ├── technical-stack.md
│   └── implementation-guide.md
├── .gitignore                        # Git除外設定
├── requirements.txt                  # Python依存パッケージ
└── README.md                         # プロジェクト説明
```

---

## 実装詳細

### 1. config.py - 設定管理

```python
"""
設定ファイル
全ての定数をここで管理
"""
import os

# スクレイピング対象URL
URLS = {
    "morning": "https://finance.matsui.co.jp/ranking-day-trading-morning/index?condition=0&market=0",
    "afternoon": "https://finance.matsui.co.jp/ranking-day-trading-afternoon/index?condition=0&market=0"
}

# 取得時間帯（JST）
TIME_SLOTS = {
    "morning": ["09:15", "09:30", "12:00"],
    "afternoon": ["12:45", "14:30"]
}

# HTTPリクエスト設定
REQUEST_TIMEOUT = 30  # 秒
RETRY_COUNT = 3
RETRY_DELAYS = [5, 10, 20]  # 秒（指数バックオフ）

# User-Agent（ブラウザの振る舞いを模倣）
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# データ保存設定
DATA_DIR = "data"
DATETIME_FORMAT = "%Y%m%d_%H%M"
JSON_INDENT = 2

# LINE Notify設定
LINE_NOTIFY_TOKEN = os.environ.get("LINE_NOTIFY_TOKEN", "")
LINE_NOTIFY_URL = "https://notify-api.line.me/api/notify"

# ログ設定
LOG_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
```

**ポイント**:
- 全ての定数を一箇所で管理
- 環境変数からトークンを取得
- 変更が必要な値は全てここに集約

---

### 2. check_workday.py - 営業日判定

```python
"""
営業日（取引日）判定モジュール
土日祝日を除いた平日かどうかを判定
"""
import datetime
import jpholiday


def is_trading_day(date: datetime.date = None) -> bool:
    """
    指定された日付が取引日（営業日）かどうかを判定

    Args:
        date: 判定する日付（Noneの場合は今日）

    Returns:
        bool: True=取引日, False=休日
    """
    if date is None:
        date = datetime.date.today()

    # 土曜日（weekday=5）または日曜日（weekday=6）
    if date.weekday() >= 5:
        return False

    # 日本の祝日
    if jpholiday.is_holiday(date):
        return False

    return True


def get_holiday_name(date: datetime.date = None) -> str:
    """
    祝日名を取得（デバッグ用）

    Args:
        date: 判定する日付

    Returns:
        str: 祝日名（祝日でない場合は空文字）
    """
    if date is None:
        date = datetime.date.today()

    holiday_name = jpholiday.is_holiday_name(date)
    return holiday_name if holiday_name else ""


if __name__ == "__main__":
    # テスト実行
    today = datetime.date.today()
    print(f"今日の日付: {today}")
    print(f"曜日: {['月', '火', '水', '木', '金', '土', '日'][today.weekday()]}")
    print(f"取引日: {is_trading_day(today)}")

    holiday_name = get_holiday_name(today)
    if holiday_name:
        print(f"祝日名: {holiday_name}")
```

**ポイント**:
- シンプルな関数設計
- デフォルト引数で今日を判定
- `__main__` でテスト実行可能

---

### 3. notify_line.py - LINE通知

```python
"""
LINE Notify通知モジュール
"""
import requests
from typing import Optional
from config import LINE_NOTIFY_TOKEN, LINE_NOTIFY_URL, REQUEST_TIMEOUT


def send_line_notify(message: str, token: Optional[str] = None) -> bool:
    """
    LINE Notifyにメッセージを送信

    Args:
        message: 送信するメッセージ
        token: LINE Notifyトークン（Noneの場合は環境変数から取得）

    Returns:
        bool: True=送信成功, False=送信失敗
    """
    if token is None:
        token = LINE_NOTIFY_TOKEN

    # トークンが設定されていない場合はスキップ
    if not token:
        print("[WARN] LINE_NOTIFY_TOKEN が設定されていません。通知をスキップします。")
        return False

    headers = {
        "Authorization": f"Bearer {token}"
    }
    data = {
        "message": message
    }

    try:
        response = requests.post(
            LINE_NOTIFY_URL,
            headers=headers,
            data=data,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        print(f"[INFO] LINE通知送信成功: {response.status_code}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] LINE通知送信失敗: {e}")
        return False


def format_success_message(datetime_str: str, target: str, rankings: list) -> str:
    """
    成功通知メッセージをフォーマット

    Args:
        datetime_str: 日時文字列（YYYYMMDD_HHMM）
        target: 'morning' or 'afternoon'
        rankings: ランキングデータ（リスト）

    Returns:
        str: フォーマットされたメッセージ
    """
    # 日時をフォーマット
    date_part = datetime_str[:8]  # YYYYMMDD
    time_part = datetime_str[9:]  # HHMM
    formatted_date = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
    formatted_time = f"{time_part[:2]}:{time_part[2:]}"

    # 朝/午後
    target_jp = "朝" if target == "morning" else "午後"

    # ベスト3を抽出
    top3 = rankings[:3] if len(rankings) >= 3 else rankings
    top3_text = "\n".join([
        f"{r['rank']}. {r['name']} ({r['code']})"
        for r in top3
    ])

    message = f"""[成功] {formatted_date} {formatted_time}
{target_jp}ランキング取得完了

ベスト3:
{top3_text}"""

    return message


def format_error_message(datetime_str: str, target: str, error: str) -> str:
    """
    エラー通知メッセージをフォーマット

    Args:
        datetime_str: 日時文字列
        target: 'morning' or 'afternoon'
        error: エラー内容

    Returns:
        str: フォーマットされたメッセージ
    """
    target_jp = "朝" if target == "morning" else "午後"

    message = f"""[エラー] {datetime_str}
{target_jp}ランキング取得失敗

エラー内容:
{error}"""

    return message


if __name__ == "__main__":
    # テスト実行
    test_message = "[TEST] LINE Notify接続テスト"
    result = send_line_notify(test_message)
    print(f"テスト結果: {'成功' if result else '失敗'}")
```

**ポイント**:
- メッセージフォーマット関数を分離
- トークン未設定時の安全な処理
- テスト実行機能

---

### 4. scrape_rankings.py - メインスクリプト

```python
"""
松井証券ランキングスクレイピング
メインスクリプト
"""
import datetime
import json
import os
import time
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

from config import (
    URLS, TIME_SLOTS, REQUEST_TIMEOUT, RETRY_COUNT, RETRY_DELAYS,
    USER_AGENT, DATA_DIR, DATETIME_FORMAT, JSON_INDENT
)
from check_workday import is_trading_day
from notify_line import send_line_notify, format_success_message, format_error_message


def log(message: str):
    """ログ出力"""
    timestamp = datetime.datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def get_current_time_slot() -> Optional[str]:
    """
    現在時刻から取得対象（morning/afternoon）を判定

    Returns:
        str: 'morning', 'afternoon', またはNone
    """
    now = datetime.datetime.now(ZoneInfo("Asia/Tokyo"))
    current_time = now.strftime("%H:%M")

    for target, time_list in TIME_SLOTS.items():
        if current_time in time_list:
            return target

    return None


def scrape_ranking(url: str) -> List[Dict]:
    """
    指定URLからランキングデータを取得

    Args:
        url: スクレイピング対象URL

    Returns:
        list: ランキングデータ（辞書のリスト）

    Raises:
        requests.exceptions.RequestException: HTTP通信エラー
        AttributeError: HTML構造が想定と異なる
    """
    headers = {
        "User-Agent": USER_AGENT
    }

    # リトライロジック
    for attempt in range(RETRY_COUNT):
        try:
            log(f"HTTP GET: {url} (試行 {attempt + 1}/{RETRY_COUNT})")
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            log(f"HTTP GET成功: {response.status_code}")
            break

        except requests.exceptions.RequestException as e:
            log(f"HTTP GETエラー: {e}")
            if attempt < RETRY_COUNT - 1:
                delay = RETRY_DELAYS[attempt]
                log(f"{delay}秒後にリトライします...")
                time.sleep(delay)
            else:
                raise

    # HTMLパース
    soup = BeautifulSoup(response.text, "lxml")

    # ランキングテーブルを探す
    # 注意: 実際のHTML構造に合わせて調整が必要
    # 以下は仮実装

    # パターン1: class="ranking-table"
    table = soup.find("table", class_="ranking-table")

    # パターン2: id="rankingTable"
    if not table:
        table = soup.find("table", id="rankingTable")

    # パターン3: 最初のtable要素
    if not table:
        table = soup.find("table")

    if not table:
        raise AttributeError("ランキングテーブルが見つかりません。HTML構造を確認してください。")

    log(f"テーブル発見: {table.name}")

    # データ抽出
    rankings = []
    rows = table.find_all("tr")

    # ヘッダー行をスキップ（通常は1行目）
    data_rows = rows[1:11]  # 2行目から11行目（ベスト10）

    for row in data_rows:
        cells = row.find_all(["td", "th"])
        if len(cells) < 3:  # 最低3列（順位、コード、名前）
            continue

        # セルからテキストを抽出
        # 注意: 列の順序は実際のページに合わせて調整
        rank_data = {
            "rank": cells[0].get_text(strip=True),
            "code": cells[1].get_text(strip=True),
            "name": cells[2].get_text(strip=True),
        }

        # 追加の列があれば取得
        if len(cells) > 3:
            rank_data["price"] = cells[3].get_text(strip=True)
        if len(cells) > 4:
            rank_data["change"] = cells[4].get_text(strip=True)
        if len(cells) > 5:
            rank_data["change_percent"] = cells[5].get_text(strip=True)
        if len(cells) > 6:
            rank_data["volume"] = cells[6].get_text(strip=True)
        if len(cells) > 7:
            rank_data["value"] = cells[7].get_text(strip=True)

        rankings.append(rank_data)

    log(f"ランキングデータ取得: {len(rankings)}件")

    if len(rankings) == 0:
        raise AttributeError("ランキングデータが取得できませんでした。HTML構造を確認してください。")

    return rankings


def save_to_json(data: Dict, target: str) -> str:
    """
    データをJSON形式で保存

    Args:
        data: 保存するデータ
        target: 'morning' or 'afternoon'

    Returns:
        str: 保存先ファイルパス
    """
    # ディレクトリ作成
    target_dir = os.path.join(DATA_DIR, target)
    os.makedirs(target_dir, exist_ok=True)

    # ファイル名生成
    filename = f"ranking_{data['datetime']}.json"
    filepath = os.path.join(target_dir, filename)

    # JSON書き込み
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=JSON_INDENT)

    log(f"JSON保存: {filepath}")
    return filepath


def main():
    """メイン処理"""
    log("=" * 60)
    log("松井証券ランキング取得 開始")

    # 1. 営業日チェック
    today = datetime.date.today()
    if not is_trading_day(today):
        log(f"{today} は取引日ではありません。処理をスキップします。")
        return

    log(f"{today} は取引日です。")

    # 2. 時間帯判定
    target = get_current_time_slot()
    if not target:
        current_time = datetime.datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%H:%M")
        log(f"現在時刻 {current_time} は取得対象の時間帯ではありません。処理をスキップします。")
        return

    log(f"取得対象: {target}")
    url = URLS[target]

    # 3. スクレイピング実行
    try:
        rankings = scrape_ranking(url)
    except Exception as e:
        log(f"スクレイピング失敗: {e}")
        # エラー通知
        datetime_str = datetime.datetime.now(ZoneInfo("Asia/Tokyo")).strftime(DATETIME_FORMAT)
        error_message = format_error_message(datetime_str, target, str(e))
        send_line_notify(error_message)
        raise

    # 4. データ保存
    now = datetime.datetime.now(ZoneInfo("Asia/Tokyo"))
    data = {
        "datetime": now.strftime(DATETIME_FORMAT),
        "url": url,
        "scraped_at": now.isoformat(),
        "rankings": rankings
    }

    filepath = save_to_json(data, target)

    # 5. 成功通知
    success_message = format_success_message(data["datetime"], target, rankings)
    send_line_notify(success_message)

    log("松井証券ランキング取得 完了")
    log("=" * 60)


if __name__ == "__main__":
    main()
```

**ポイント**:
- リトライロジックの実装
- 複数パターンのテーブル検索
- エラーハンドリングの徹底
- ログ出力で実行状況を可視化

**注意**:
`scrape_ranking()` 関数内のHTML構造解析部分は、実際のページに合わせて調整が必要です。

---

### 5. .github/workflows/scrape_rankings.yml - GitHub Actions

```yaml
name: Scheduled Ranking Scrape

on:
  # 定時実行（UTC時刻で指定）
  schedule:
    # JST 09:15 = UTC 00:15
    - cron: "15 0 * * *"
    # JST 09:30 = UTC 00:30
    - cron: "30 0 * * *"
    # JST 12:00 = UTC 03:00
    - cron: "0 3 * * *"
    # JST 12:45 = UTC 03:45
    - cron: "45 3 * * *"
    # JST 14:30 = UTC 05:30
    - cron: "30 5 * * *"

  # 手動実行
  workflow_dispatch:

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
          python-version: "3.11"
          cache: "pip"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run scraper
        env:
          LINE_NOTIFY_TOKEN: ${{ secrets.LINE_NOTIFY_TOKEN }}
        run: |
          cd src
          python scrape_rankings.py

      - name: Commit and push results
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add data/
          if ! git diff --cached --quiet; then
            git commit -m "chore: update rankings [skip ci]"
            git push
          else
            echo "No changes to commit."
          fi
```

**ポイント**:
- 5つの時刻でcron設定（UTCで指定）
- `workflow_dispatch` で手動実行可能
- `cache: "pip"` で依存関係のキャッシュ
- `[skip ci]` でコミット後の再実行を防止

---

### 6. requirements.txt

```txt
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=5.0.0
jpholiday>=0.1.10
```

---

### 7. .gitignore

```
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

# テストファイル
test_output/
```

---

## 実装手順

### ステップ1: リポジトリ作成
```bash
mkdir market
cd market
git init
git branch -M main
```

### ステップ2: ディレクトリ構造作成
```bash
mkdir -p .github/workflows
mkdir -p src
mkdir -p docs
mkdir -p data/morning
mkdir -p data/afternoon
```

### ステップ3: ファイル作成
上記の各ファイルを作成

### ステップ4: 依存関係インストール（ローカルテスト用）
```bash
python3 -m venv venv
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate
pip install -r requirements.txt
```

### ステップ5: ローカルテスト
```bash
cd src
python check_workday.py     # 営業日判定テスト
python notify_line.py        # LINE通知テスト（要トークン設定）
python scrape_rankings.py    # スクレイピングテスト
```

### ステップ6: GitHubにプッシュ
```bash
git add .
git commit -m "feat: initial implementation"
git remote add origin https://github.com/YOUR_USERNAME/market.git
git push -u origin main
```

### ステップ7: GitHub Secrets設定
1. GitHubリポジトリページを開く
2. Settings → Secrets and variables → Actions
3. `New repository secret` をクリック
4. Name: `LINE_NOTIFY_TOKEN`
5. Secret: （LINE Notifyで取得したトークン）
6. `Add secret` をクリック

### ステップ8: ワークフロー手動実行
1. Actions タブを開く
2. `Scheduled Ranking Scrape` を選択
3. `Run workflow` をクリック
4. ログを確認して動作確認

---

## トラブルシューティング

### 問題1: HTML構造が想定と異なる

**症状**:
```
AttributeError: ランキングテーブルが見つかりません
```

**対処法**:
1. ブラウザで対象ページを開く
2. 開発者ツール（F12）で要素を検査
3. テーブルの class, id を確認
4. `scrape_rankings.py` の `scrape_ranking()` 関数を修正

**確認コマンド**:
```python
# デバッグ用コード
soup = BeautifulSoup(response.text, "lxml")
print(soup.prettify())  # HTML全体を出力
```

---

### 問題2: LINE通知が届かない

**症状**:
LINE通知が送信されない

**チェックリスト**:
- [ ] LINE_NOTIFY_TOKEN がGitHub Secretsに正しく設定されているか
- [ ] トークンが有効か（LINE Notifyマイページで確認）
- [ ] ネットワークエラーが発生していないか（ログ確認）

**テスト方法**:
```bash
export LINE_NOTIFY_TOKEN="your_token_here"
python src/notify_line.py
```

---

### 問題3: 営業日判定が正しく動作しない

**症状**:
休日なのに実行される、または営業日なのに実行されない

**確認方法**:
```bash
python src/check_workday.py
```

**デバッグ**:
```python
import datetime
import jpholiday

date = datetime.date(2025, 10, 20)
print(f"曜日: {date.weekday()}")  # 0=月, 5=土, 6=日
print(f"祝日: {jpholiday.is_holiday(date)}")
```

---

## 次のステップ

実装完了後の推奨事項：

1. **1週間の動作監視**: 毎日のLINE通知を確認
2. **データ確認**: data/ディレクトリのJSONファイルをチェック
3. **エラー対応**: エラーが発生した場合はHTML構造を再確認
4. **ドキュメント更新**: 実際の構造に合わせて更新

---

## まとめ

この実装ガイドに従うことで、以下が実現できます：

✅ 平日の指定時刻に自動実行
✅ ランキングデータの自動取得
✅ JSON形式でのデータ保存
✅ LINE Notifyでのリアルタイム通知
✅ エラー時の自動通知
✅ リトライ機能による信頼性向上

実装後は定期的に動作確認を行い、必要に応じてHTML構造の変更に対応してください。
