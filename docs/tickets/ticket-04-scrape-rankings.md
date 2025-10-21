# Ticket #4: scrape_rankings.py 基本実装

## 📋 基本情報

- **優先度:** 🔴 高
- **ステータス:** ✅ 完了
- **推定工数:** 2時間
- **依存関係:** #2, #3
- **担当者:** codex
- **作成日:** 2025-10-21
- **最終更新:** 2025-10-21

---

## 📝 概要

ランキングデータを取得し、JSON形式で保存するメインスクリプトを実装する。時刻判定、HTTP リクエスト、HTML パース、データ保存を統合したオーケストレーションロジック。

---

## 🎯 タスク一覧

- [x] `src/scrape_rankings.py` ファイル作成
- [x] `get_current_time_slot()` 関数実装
  - [x] JST時刻取得（ZoneInfo("Asia/Tokyo")）
  - [x] 現在時刻と TIME_SLOTS のマッチング
  - [x] morning/afternoon 判定
  - [x] マッチしない場合は None を返す
- [x] `scrape_ranking(url: str)` 関数実装
  - [x] User-Agent設定したHTTPリクエスト
  - [x] リトライロジック（指数バックオフ）
  - [x] BeautifulSoup でHTMLパース
  - [x] テーブル要素の検索（複数パターンでフォールバック）
  - [x] ベスト10のデータ抽出
- [x] `save_to_json(data: dict, target: str)` 関数実装
  - [x] ファイル名生成（ranking_YYYYMMDD_HHMM.json）
  - [x] ディレクトリ自動作成
  - [x] JSON形式保存（indent=2, ensure_ascii=False）
- [x] `main()` 関数実装
  - [x] 営業日チェック呼び出し
  - [x] 時間帯判定
  - [x] スクレイピング実行
  - [x] データ保存
  - [x] エラーハンドリング
  - [x] LINE通知呼び出し
- [x] docstring 追加（すべての関数）
- [x] ロギング追加

---

## 📦 成果物

### ファイル: `src/scrape_rankings.py`

**主要関数のシグネチャ:**

```python
from typing import Optional, Dict, List
from datetime import datetime
from zoneinfo import ZoneInfo

def get_current_time_slot() -> Optional[str]:
    """
    現在時刻から取得対象を判定する

    Returns:
        str: "morning" or "afternoon"、該当しない場合は None
    """
    pass

def scrape_ranking(url: str) -> List[Dict]:
    """
    指定されたURLからランキングデータを取得する

    Args:
        url: 取得対象のURL

    Returns:
        List[Dict]: ランキングデータのリスト（最大10件）

    Raises:
        requests.exceptions.RequestException: HTTP通信エラー
        AttributeError: HTML構造が期待と異なる
    """
    pass

def save_to_json(data: Dict, target: str) -> str:
    """
    データをJSON形式で保存する

    Args:
        data: 保存するデータ
        target: "morning" or "afternoon"

    Returns:
        str: 保存したファイルパス
    """
    pass

def main():
    """
    メイン処理
    """
    pass

if __name__ == "__main__":
    main()
```

---

## ✅ 完了条件

- [x] `src/scrape_rankings.py` ファイルが存在する
- [x] すべての関数が実装されている
- [x] 営業日チェックが統合されている
- [x] 時刻判定が正しく動作する
- [x] HTTPリクエストが成功する（User-Agent設定済み）
- [x] リトライロジックが動作する（3回、指数バックオフ）
- [x] HTMLパースが実装されている（※HTML構造は仮実装）
- [x] JSONファイルが正しい場所に保存される
- [x] エラーハンドリングが実装されている
- [x] docstring が適切に記載されている
- [x] PEP 8 スタイルガイドに準拠している

---

## 🧪 テスト方法

### 基本実行テスト

```bash
# 仮想環境をアクティブ化
source venv/bin/activate

# スクリプト実行
cd src
python scrape_rankings.py
```

### 時間帯判定テスト

```python
# テスト用のモック時刻で確認
from scrape_rankings import get_current_time_slot

# 実際の実行時刻に応じて結果が変わる
result = get_current_time_slot()
print(f"現在の時間帯: {result}")
```

### リトライロジックテスト

```python
# 意図的に失敗するURLでリトライを確認
from scrape_rankings import scrape_ranking

try:
    scrape_ranking("https://invalid-url-for-test.example.com")
except Exception as e:
    print(f"リトライ後のエラー: {e}")
```

### ファイル保存テスト

```bash
# 実行後にファイルが生成されているか確認
ls -la ../data/morning/
ls -la ../data/afternoon/

# JSON形式の検証
cat ../data/morning/ranking_*.json | jq .
```

---

## 📌 注意事項

- **HTML構造は仮実装**: #5で実際の構造に合わせて調整が必要
- **時刻判定の誤差**: 実行時刻が TIME_SLOTS から数分ずれる可能性を考慮
- **エラー通知**: すべての例外をキャッチし、LINE通知を送信する
- **タイムゾーン**: 必ず `ZoneInfo("Asia/Tokyo")` を使用してJST判定
- **テスト時の注意**: スケジュール時間外にテストする場合、main()内で target を強制設定

---

## 🔍 実装のポイント

### リトライロジック例

```python
import time
import requests
from config import RETRY_COUNT, RETRY_DELAYS, REQUEST_TIMEOUT

for attempt in range(RETRY_COUNT):
    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        break
    except requests.exceptions.RequestException as e:
        if attempt < RETRY_COUNT - 1:
            time.sleep(RETRY_DELAYS[attempt])
        else:
            raise
```

### HTML パース例（仮実装）

```python
from bs4 import BeautifulSoup

soup = BeautifulSoup(response.content, "lxml")

# パターン1: クラス名で検索
table = soup.find("table", class_="ranking-table")

# パターン2: IDで検索
if not table:
    table = soup.find("table", id="rankingTable")

# パターン3: 最初のtableを取得
if not table:
    table = soup.find("table")

if not table:
    raise AttributeError("ランキングテーブルが見つかりません")
```

---

## 🔗 関連チケット

- **依存元:** #2 (check_workday.py), #3 (config.py)
- **ブロック対象:** #5 (HTML構造調整), #8 (ローカルテスト)
- **関連:** #6 (notify_line.py)

---

## 📚 参考資料

- [requests ドキュメント](https://requests.readthedocs.io/)
- [Beautiful Soup ドキュメント](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [zoneinfo ドキュメント](https://docs.python.org/3/library/zoneinfo.html)

---

## 📝 作業ログ

| 日時 | 作業内容 | 備考 |
|------|---------|------|
| 2025-10-21 | チケット作成 | - |
| 2025-10-21 | 基本実装完了 | scrape_rankings.py 実装とロギング整備 |
