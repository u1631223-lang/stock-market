"""
SBI証券 業種別騰落率ランキング自動取得スクリプト

SBI証券の業種別株価平均ランキング（前日比）を取得し、LINE通知します。
GitHub Actionsから定期実行されることを想定しています。
"""

import datetime
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from config import (
    RETRY_COUNT,
    RETRY_DELAYS,
    REQUEST_TIMEOUT,
    SECTOR_DATA_DIR,
    SECTOR_TIME_SLOTS,
    SECTOR_URL,
    USER_AGENT,
)

# check_workday.py の is_trading_day をインポート
try:
    from check_workday import is_trading_day
    CHECK_WORKDAY_FALLBACK = False
except ImportError:
    CHECK_WORKDAY_FALLBACK = True
    import jpholiday

    def is_trading_day(target_date: datetime.date) -> bool:
        """簡易版: 土日祝を除外"""
        if target_date.weekday() >= 5:  # 土日
            return False
        if jpholiday.is_holiday(target_date):  # 祝日
            return False
        return True

# notify_line.py の send_line_message をインポート
try:
    from notify_line import send_line_message as send_line_notify
    LINE_NOTIFY_AVAILABLE = True
except ImportError:
    LINE_NOTIFY_AVAILABLE = False

    def send_line_notify(message: str) -> bool:
        """フォールバック: ログ出力のみ"""
        logging.info("[LINE通知] %s", message)
        return True

# ===========================
# ロギング設定
# ===========================

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ===========================
# 定数
# ===========================

JST = ZoneInfo("Asia/Tokyo")
DATA_ROOT = PROJECT_ROOT / SECTOR_DATA_DIR
DATETIME_FORMAT = "%Y%m%d_%H%M"

# ===========================
# セクター別ランキング取得
# ===========================


def scrape_sector_ranking(url: str) -> List[Dict[str, str]]:
    """
    SBI証券の業種別騰落率ランキングを取得する。

    Args:
        url: スクレイピング対象URL

    Returns:
        List[Dict]: 業種別ランキングデータのリスト
            [{"rank": "1", "sector": "...", "change_percent": "+1.23%", ...}, ...]

    Raises:
        requests.exceptions.RequestException: HTTP通信エラー
        AttributeError: HTML構造の解析失敗
    """
    headers = {"User-Agent": USER_AGENT}

    for attempt in range(1, RETRY_COUNT + 1):
        try:
            logger.info("セクター別ランキング取得を試行します（%d/%d）", attempt, RETRY_COUNT)
            response = requests.get(
                url, headers=headers, timeout=REQUEST_TIMEOUT, allow_redirects=True
            )
            response.raise_for_status()
            logger.info("HTTP %d: データ取得成功", response.status_code)
            break
        except requests.exceptions.RequestException as exc:
            logger.warning("HTTP通信エラー（試行 %d/%d）: %s", attempt, RETRY_COUNT, exc)
            if attempt < RETRY_COUNT:
                delay = RETRY_DELAYS[min(attempt - 1, len(RETRY_DELAYS) - 1)]
                logger.info("%d秒後にリトライします...", delay)
                import time
                time.sleep(delay)
            else:
                logger.error("最大リトライ回数に達しました。取得を中断します。")
                raise

    soup = BeautifulSoup(response.content, "lxml")

    # SBI証券の業種別テーブルを探す
    # 実際のHTML構造に合わせて調整が必要
    table = soup.find("table", class_="md-l-table-01")
    if not table:
        table = soup.find("table")

    if not table:
        raise AttributeError("業種別ランキングテーブルが見つかりません。HTML構造が変更された可能性があります。")

    rankings = []
    rows = table.find_all("tr")

    for row in rows[1:]:  # ヘッダー行をスキップ
        cols = row.find_all(["td", "th"])
        if len(cols) < 3:
            continue

        try:
            rank = cols[0].get_text(strip=True)
            sector = cols[1].get_text(strip=True)
            change_percent = cols[2].get_text(strip=True)

            # オプション: 追加の列があれば取得
            value = cols[3].get_text(strip=True) if len(cols) > 3 else ""
            change = cols[4].get_text(strip=True) if len(cols) > 4 else ""

            rankings.append({
                "rank": rank,
                "sector": sector,
                "change_percent": change_percent,
                "value": value,
                "change": change,
            })

            # トップ10のみ取得
            if len(rankings) >= 10:
                break

        except (IndexError, AttributeError) as exc:
            logger.warning("行の解析をスキップしました: %s", exc)
            continue

    if not rankings:
        raise ValueError("ランキングデータが取得できませんでした")

    logger.info("セクター別ランキングを %d 件取得しました", len(rankings))
    return rankings


# ===========================
# データ保存
# ===========================


def save_to_json(data: Dict[str, Any], slot: str) -> Path:
    """
    セクター別ランキングデータをJSON形式で保存する。

    Args:
        data: 保存するデータ（辞書形式）
        slot: タイムスロット識別子（"midday" or "close"）

    Returns:
        Path: 保存したファイルのパス
    """
    DATA_ROOT.mkdir(parents=True, exist_ok=True)

    datetime_str = data["datetime"]
    filename = f"sector_{datetime_str}.json"
    filepath = DATA_ROOT / filename

    with filepath.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    logger.info("データを保存しました: %s", filepath)
    return filepath


# ===========================
# LINE通知メッセージ作成
# ===========================


def format_success_message(
    datetime_str: str,
    slot: str,
    rankings: List[Dict[str, str]],
) -> str:
    """
    セクター別ランキング取得成功時のLINEメッセージを作成する。

    Args:
        datetime_str: 実行日時文字列
        slot: タイムスロット識別子
        rankings: ランキングデータ

    Returns:
        str: LINE通知用メッセージ
    """
    slot_names = {
        "midday": "前場終了時",
        "close": "大引け後",
    }
    slot_name = slot_names.get(slot, slot)

    dt = datetime.datetime.strptime(datetime_str, DATETIME_FORMAT)
    formatted_time = dt.strftime("%Y-%m-%d %H:%M")

    lines = [
        f"📊 {formatted_time}",
        f"業種別騰落率ランキング（{slot_name}）",
        "",
    ]

    for item in rankings[:10]:
        rank = item.get("rank", "?")
        sector = item.get("sector", "不明")
        change_pct = item.get("change_percent", "N/A")

        # 色インジケーター
        if "+" in change_pct:
            color = "🟢"
        elif "-" in change_pct:
            color = "🔴"
        else:
            color = "⚪"

        lines.append(f"{rank}位: {sector} {color}{change_pct}")

    return "\n".join(lines)


def format_error_message(
    datetime_str: str,
    slot: str,
    error_msg: str,
) -> str:
    """エラー発生時のLINEメッセージを作成する。"""
    dt = datetime.datetime.strptime(datetime_str, DATETIME_FORMAT)
    formatted_time = dt.strftime("%Y-%m-%d %H:%M")

    return f"""⚠️ セクター別ランキング取得エラー

時刻: {formatted_time}
スロット: {slot}
エラー: {error_msg}

システム管理者に連絡してください。"""


# ===========================
# 時刻判定
# ===========================


def get_current_time_slot() -> Optional[Tuple[str, str]]:
    """
    現在時刻から該当するタイムスロットを取得する。

    Returns:
        Optional[Tuple[str, str]]: (slot識別子, 時刻文字列) または None
    """
    now = datetime.datetime.now(JST)
    current_time = now.strftime("%H:%M")

    for slot_time, slot_id in SECTOR_TIME_SLOTS.items():
        logger.info(
            "現在時刻 %s は %s のセクター別実行時間帯として処理します（許容幅制限なし）",
            current_time,
            slot_time,
        )
        return (slot_id, slot_time)

    return None


# ===========================
# 重複実行チェック
# ===========================


def check_recent_execution(
    slot: str,
    slot_time: str,
    threshold_minutes: int = 10,
) -> bool:
    """
    指定スロットの実行有無を判定して重複取得を避ける。

    Args:
        slot: タイムスロット識別子
        slot_time: 予定スロット時刻（例: "11:45"）
        threshold_minutes: 時刻ベース判定のフォールバック閾値（分）

    Returns:
        bool: True=重複のためスキップ, False=実行すべき
    """
    if not DATA_ROOT.exists():
        return False

    json_files = sorted(
        DATA_ROOT.glob("sector_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    if not json_files:
        return False

    now = datetime.datetime.now(JST)
    today = now.date()

    for candidate in json_files:
        # ファイル名から日付を抽出（sector_YYYYMMDD_HHMM.json）
        try:
            name_parts = candidate.stem.split("_")
            if len(name_parts) >= 2:
                file_date_str = name_parts[1]  # YYYYMMDD
                file_date = datetime.datetime.strptime(file_date_str, "%Y%m%d").date()
            else:
                continue
        except (ValueError, IndexError):
            continue

        if file_date != today:
            continue

        try:
            with candidate.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (json.JSONDecodeError, OSError):
            continue

        if data.get("slot_time") == slot_time:
            logger.info(
                "スロット %s は既に %s に保存済みのため重複実行をスキップします。",
                slot_time,
                candidate.name,
            )
            return True

    # フォールバック: 直近10分以内のチェック
    latest_file = json_files[0]
    file_mtime = datetime.datetime.fromtimestamp(latest_file.stat().st_mtime, tz=JST)
    diff_minutes = (now - file_mtime).total_seconds() / 60

    if diff_minutes < threshold_minutes:
        logger.info(
            "%.1f分前に実行済みです（%s）。重複実行を防止するためスキップします。",
            diff_minutes,
            latest_file.name,
        )
        return True

    return False


# ===========================
# メイン処理
# ===========================


def main() -> None:
    """セクター別ランキング取得からLINE通知までのメイン処理を実行する。"""

    separator = "=" * 60
    logger.info(separator)
    logger.info("SBI証券 業種別騰落率ランキング取得 開始")

    today = datetime.datetime.now(JST).date()
    if CHECK_WORKDAY_FALLBACK:
        logger.warning("check_workday.py が未実装のため簡易営業日判定を使用します。")

    if not is_trading_day(today):
        logger.info("%s は取引日ではありません。処理を終了します。", today)
        logger.info(separator)
        return

    slot_info = get_current_time_slot()

    if slot_info is None:
        current_time = datetime.datetime.now(JST).strftime("%H:%M")
        logger.info(
            "現在時刻 %s はセクター別取得対象の時間帯ではありません。処理をスキップします。",
            current_time,
        )
        logger.info(separator)
        return

    slot, slot_time_str = slot_info

    # 重複実行チェック（10分以内に実行済みならスキップ）
    if check_recent_execution(slot, slot_time_str, threshold_minutes=10):
        logger.info("重複実行を防止するため処理を終了します。")
        logger.info(separator)
        return

    try:
        rankings = scrape_sector_ranking(SECTOR_URL)
    except Exception as exc:
        datetime_str = datetime.datetime.now(JST).strftime(DATETIME_FORMAT)
        error_message = format_error_message(datetime_str, slot, str(exc))
        success = send_line_notify(error_message)
        if not success:
            logger.error("LINE通知の送信に失敗しました（エラー通知）")
            raise RuntimeError("LINE通知の送信に失敗しました") from exc
        logger.error("スクレイピングに失敗しました: %s", exc)
        logger.info(separator)
        raise

    now = datetime.datetime.now(JST)
    datetime_str = now.strftime(DATETIME_FORMAT)
    data: Dict[str, Any] = {
        "datetime": datetime_str,
        "slot_time": slot_time_str,
        "slot": slot,
        "url": SECTOR_URL,
        "scraped_at": now.isoformat(),
        "rankings": rankings,
    }

    filepath = save_to_json(data, slot)

    message = format_success_message(datetime_str, slot, rankings)
    success = send_line_notify(message)
    if not success:
        logger.error("LINE通知の送信に失敗しました（成功通知）")
        raise RuntimeError("LINE通知の送信に失敗しました")

    if not LINE_NOTIFY_AVAILABLE:
        logger.info("LINE通知はログ出力のみ (notify_line.py 未実装)。")

    logger.info("JSONファイルを保存しました: %s", filepath)
    logger.info("SBI証券 業種別騰落率ランキング取得 完了")
    logger.info(separator)


if __name__ == "__main__":
    main()
