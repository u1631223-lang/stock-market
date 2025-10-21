# Ticket #5: HTML構造調査と調整

## 📋 基本情報

- **優先度:** 🔴 高
- **ステータス:** ✅ 完了
- **推定工数:** 1時間
- **依存関係:** #4
- **担当者:** Claude
- **作成日:** 2025-10-21
- **最終更新:** 2025-10-21 08:35

---

## 📝 概要

松井証券のランキングページの実際のHTML構造を調査し、`scrape_ranking()` 関数のセレクタとデータ抽出ロジックを調整する。

---

## 🎯 タスク一覧

- [x] 朝のランキングページのHTML構造確認
  - [x] スクリプトでページを取得
  - [x] BeautifulSoupでテーブル要素を調査
  - [x] テーブルのclass/id/構造を記録（class="m-table"）
  - [x] カラムの順序と内容を記録（8カラム構造）
- [x] 午後のランキングページのHTML構造確認
  - [x] 朝と同じ手順で調査
  - [x] 朝と午後で構造に差異がないか確認（同一構造）
- [x] 実際の構造に合わせた `scrape_ranking()` の調整
  - [x] テーブルセレクタの更新（m-table追加）
  - [x] カラムインデックスの調整
  - [x] データ抽出ロジックの修正（銘柄名+コード分離）
  - [x] 正規表現での銘柄コード抽出（3-4桁+文字対応）
- [x] フォールバックパターンの実装
  - [x] 複数のセレクタパターンを用意
  - [x] 構造変更時のエラーメッセージ改善
- [x] 実際のページでテスト実行（朝・午後両方）
- [x] 取得データの妥当性確認（10件、全フィールド取得確認）

---

## 📦 成果物

### HTML構造調査レポート

**調査対象URL:**
- 朝: https://finance.matsui.co.jp/ranking-day-trading-morning/index?condition=0&market=0
- 午後: https://finance.matsui.co.jp/ranking-day-trading-afternoon/index?condition=0&market=0

**記録すべき情報:**

```markdown
## 調査結果

### テーブル要素
- タグ: <table>
- クラス名: _______________
- ID: _______________
- 親要素: _______________

### テーブル構造
- ヘッダー行: あり / なし
- データ行の数: _______________

### カラム構成（左から順に）
1. _______________
2. _______________
3. _______________
4. _______________
...

### サンプルHTML
```html
<!-- 実際のHTMLをコピー -->
```

### 特記事項
- 朝と午後の構造差異: _______________
- 注意すべきポイント: _______________
```

### 更新された scrape_ranking() 関数

実際の構造に合わせてセレクタとデータ抽出ロジックを調整。

---

## ✅ 完了条件

- [ ] 朝のページのHTML構造が完全に把握されている
- [ ] 午後のページのHTML構造が完全に把握されている
- [ ] 構造調査レポートが作成されている
- [ ] `scrape_ranking()` が実際の構造に対応している
- [ ] ベスト10のデータが正しく取得できる
- [ ] すべてのカラム（順位、コード、銘柄名、株価等）が取得できる
- [ ] 実際のページで動作確認済み
- [ ] 取得したJSONデータが妥当である

---

## 🧪 テスト方法

### 1. ブラウザでの構造確認

```bash
# ブラウザでURLを開く
open "https://finance.matsui.co.jp/ranking-day-trading-morning/index?condition=0&market=0"

# DevTools (F12) を開き、Elements タブで調査
# 1. テーブル要素を右クリック → "検証"
# 2. class/id属性を確認
# 3. tr/td要素の構造を確認
# 4. 右クリック → "Copy" → "Copy outerHTML"
```

### 2. Pythonでの構造確認

```python
import requests
from bs4 import BeautifulSoup
from config import URLS, USER_AGENT

headers = {"User-Agent": USER_AGENT}
response = requests.get(URLS["morning"], headers=headers, timeout=30)
soup = BeautifulSoup(response.content, "lxml")

# すべてのtableを表示
tables = soup.find_all("table")
print(f"テーブル数: {len(tables)}")

for i, table in enumerate(tables):
    print(f"\n=== テーブル {i+1} ===")
    print(f"Class: {table.get('class')}")
    print(f"ID: {table.get('id')}")
    rows = table.find_all("tr")
    print(f"行数: {len(rows)}")

    # 最初の2行を表示
    for row in rows[:2]:
        cells = row.find_all(["td", "th"])
        print([cell.get_text(strip=True) for cell in cells])
```

### 3. データ抽出テスト

```bash
# 調整後のスクリプトを実行
cd src
python scrape_rankings.py

# 取得したJSONを確認
cat ../data/morning/ranking_*.json | jq .

# 期待されるデータが含まれているか確認
# - 10件のデータ
# - すべてのフィールドが埋まっている
# - 銘柄コードが4桁の数字
# - 銘柄名が日本語
```

---

## 📌 注意事項

- **営業時間外のアクセス**: ページ内容が異なる可能性あり
- **動的コンテンツ**: JavaScriptで生成される要素は取得できない（静的HTMLのみ）
- **403エラー対策**: User-Agent設定が必須
- **構造変更の可能性**: 将来的にHTML構造が変わる可能性を考慮してフォールバック実装
- **礼儀正しいアクセス**: 過度なリクエストを避け、テストは最小限に

---

## 🔍 予想される構造パターン

### パターン1: クラス名指定
```python
table = soup.find("table", class_="ranking-table")
```

### パターン2: ID指定
```python
table = soup.find("table", id="rankingTable")
```

### パターン3: 属性検索
```python
table = soup.find("table", attrs={"data-type": "ranking"})
```

### パターン4: 親要素からの検索
```python
container = soup.find("div", class_="ranking-container")
table = container.find("table")
```

---

## 🔗 関連チケット

- **依存元:** #4 (scrape_rankings.py基本実装)
- **ブロック対象:** #8 (ローカルテスト)

---

## 📚 参考資料

- [Beautiful Soup セレクタ](https://www.crummy.com/software/BeautifulSoup/bs4/doc/#searching-the-tree)
- [Chrome DevTools ガイド](https://developer.chrome.com/docs/devtools/)

---

## 📝 作業ログ

| 日時 | 作業内容 | 備考 |
|------|---------|------|
| 2025-10-21 08:00 | チケット作成 | - |
| 2025-10-21 08:31 | HTML構造調査スクリプト作成 | inspect_html.py |
| 2025-10-21 08:31 | 実際のHTML構造確認 | table class="m-table", 8カラム構造 |
| 2025-10-21 08:32 | scrape_rankings.py 調整 | m-tableセレクタ追加、データ抽出ロジック修正 |
| 2025-10-21 08:33 | 銘柄コード抽出改善 | 正規表現で3-4桁+文字のコード対応 |
| 2025-10-21 08:34 | 朝・午後両方のテスト実施 | 10件のデータ取得成功 |
| 2025-10-21 08:35 | ✅ チケット完了 | すべてのタスク完了 |
