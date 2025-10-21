# Ticket #2: check_workday.py 実装

## 📋 基本情報

- **優先度:** 🔴 高
- **ステータス:** ✅ 完了
- **推定工数:** 30分
- **依存関係:** #1
- **担当者:** Claude
- **作成日:** 2025-10-21
- **最終更新:** 2025-10-21 08:18

---

## 📝 概要

営業日（取引日）を判定するモジュールを実装する。土日・祝日を除外し、平日のみ True を返す機能を提供。

---

## 🎯 タスク一覧

- [x] `src/check_workday.py` ファイル作成
- [x] `is_trading_day(target_date: datetime.date) -> bool` 関数実装
  - [x] 土曜日判定（weekday == 5）
  - [x] 日曜日判定（weekday == 6）
  - [x] 祝日判定（jpholiday.is_holiday()）
- [x] モジュール直接実行時の動作実装（`if __name__ == "__main__"`）
  - [x] 今日の日付で判定
  - [x] 結果を標準出力
- [x] docstring 追加（関数・モジュールレベル）
- [x] テストケースでの動作確認（10件のテストすべて成功）

---

## 📦 成果物

### ファイル: `src/check_workday.py`

**期待される機能:**
```python
import datetime
import jpholiday

def is_trading_day(target_date: datetime.date) -> bool:
    """
    指定された日付が営業日（取引日）かどうかを判定する

    Args:
        target_date: 判定対象の日付

    Returns:
        bool: 営業日の場合 True、それ以外は False

    Examples:
        >>> is_trading_day(datetime.date(2025, 10, 20))  # 月曜日
        True
        >>> is_trading_day(datetime.date(2025, 10, 25))  # 土曜日
        False
        >>> is_trading_day(datetime.date(2025, 1, 1))    # 元日
        False
    """
    # 実装内容
    pass
```

**実行例:**
```bash
$ cd src
$ python check_workday.py
2025-10-21 (火曜日)
判定結果: 営業日です

$ python check_workday.py
2025-10-26 (土曜日)
判定結果: 休日です（土曜日）
```

---

## ✅ 完了条件

- [x] `src/check_workday.py` ファイルが存在する
- [x] `is_trading_day()` 関数が実装されている
- [x] 土日を正しく判定できる
- [x] 祝日を正しく判定できる（jpholiday使用）
- [x] docstring が適切に記載されている
- [x] コマンドライン実行で今日の判定結果が表示される
- [x] PEP 8 スタイルガイドに準拠している
- [x] 10件のテストケースすべてが成功

---

## 🧪 テスト方法

### 手動テスト

```bash
# 仮想環境をアクティブ化
source venv/bin/activate

# モジュール実行
cd src
python check_workday.py
```

### テストケース

| 日付 | 曜日 | 祝日 | 期待結果 |
|------|------|------|---------|
| 2025-10-20 | 月 | - | True |
| 2025-10-21 | 火 | - | True |
| 2025-10-25 | 土 | - | False |
| 2025-10-26 | 日 | - | False |
| 2025-01-01 | 水 | 元日 | False |
| 2025-11-03 | 月 | 文化の日 | False |

### Pythonインタラクティブテスト

```python
import datetime
from check_workday import is_trading_day

# 平日テスト
assert is_trading_day(datetime.date(2025, 10, 20)) == True

# 土曜日テスト
assert is_trading_day(datetime.date(2025, 10, 25)) == False

# 日曜日テスト
assert is_trading_day(datetime.date(2025, 10, 26)) == False

# 祝日テスト
assert is_trading_day(datetime.date(2025, 1, 1)) == False
```

---

## 📌 注意事項

- `jpholiday` ライブラリは日本の祝日に対応
- 振替休日も自動的に考慮される
- タイムゾーンは考慮不要（日付のみ）
- GW、年末年始など連休も正しく判定される

---

## 🔗 関連チケット

- **依存元:** #1 (プロジェクト環境構築)
- **ブロック対象:** #4 (scrape_rankings.py)

---

## 📚 参考資料

- [jpholiday ドキュメント](https://pypi.org/project/jpholiday/)
- [datetime ドキュメント](https://docs.python.org/3/library/datetime.html)

---

## 📝 作業ログ

| 日時 | 作業内容 | 備考 |
|------|---------|------|
| 2025-10-21 08:00 | チケット作成 | - |
| 2025-10-21 08:16 | check_workday.py 作成 | is_trading_day()関数実装 |
| 2025-10-21 08:16 | main()関数追加 | 直接実行時の動作実装 |
| 2025-10-21 08:17 | 仮想環境作成・依存関係インストール | venv作成、requirements.txtからインストール |
| 2025-10-21 08:17 | 動作確認テスト実施 | 今日の日付で正常動作を確認 |
| 2025-10-21 08:18 | 総合テスト実施 | 10件のテストケースすべて成功 |
| 2025-10-21 08:18 | ✅ チケット完了 | すべてのタスク完了 |
