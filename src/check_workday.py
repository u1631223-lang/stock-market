"""
営業日（取引日）判定モジュール

土日・祝日を除外し、平日のみを営業日として判定します。
"""

import datetime
import jpholiday


def is_trading_day(target_date: datetime.date = None) -> bool:
    """
    指定された日付が営業日（取引日）かどうかを判定する

    営業日の定義:
    - 月曜日〜金曜日
    - 日本の祝日でない日

    Args:
        target_date: 判定対象の日付（省略時は今日）

    Returns:
        bool: 営業日の場合 True、それ以外は False

    Examples:
        >>> import datetime
        >>> # 平日（月曜日）
        >>> is_trading_day(datetime.date(2025, 10, 20))
        True
        >>> # 土曜日
        >>> is_trading_day(datetime.date(2025, 10, 25))
        False
        >>> # 日曜日
        >>> is_trading_day(datetime.date(2025, 10, 26))
        False
        >>> # 祝日（元日）
        >>> is_trading_day(datetime.date(2025, 1, 1))
        False
    """
    # 日付が指定されていない場合は今日を使用
    if target_date is None:
        target_date = datetime.date.today()

    # 土曜日（weekday=5）または日曜日（weekday=6）の場合は営業日ではない
    if target_date.weekday() in (5, 6):
        return False

    # 日本の祝日の場合は営業日ではない
    if jpholiday.is_holiday(target_date):
        return False

    # 上記以外は営業日
    return True


def main():
    """
    モジュール直接実行時の動作

    今日の日付で営業日判定を行い、結果を表示します。
    """
    today = datetime.date.today()
    is_trading = is_trading_day(today)

    # 曜日名の取得
    weekday_names = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
    weekday_name = weekday_names[today.weekday()]

    print(f"{today} ({weekday_name})")

    if is_trading:
        print("判定結果: ✅ 営業日です")
    else:
        # 理由を表示
        if today.weekday() == 5:
            print("判定結果: ❌ 休日です（土曜日）")
        elif today.weekday() == 6:
            print("判定結果: ❌ 休日です（日曜日）")
        elif jpholiday.is_holiday(today):
            holiday_name = jpholiday.is_holiday_name(today)
            print(f"判定結果: ❌ 休日です（祝日: {holiday_name}）")
        else:
            print("判定結果: ❌ 休日です")


if __name__ == "__main__":
    main()
