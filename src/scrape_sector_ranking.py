#!/usr/bin/env python3
"""SBI証券の業種別株価平均ランキングをスクレイピングするスクリプト

前日比上位1-5位と下位29-33位を取得してLINEに通知します。
"""

import datetime
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

from config import (
    DATA_DIR,
    LINE_MESSAGING_API_PUSH,
    REQUEST_TIMEOUT,
    RETRY_COUNT,
    RETRY_DELAYS,
    SECTOR_DATA_DIR,
    SECTOR_TIME_SLOTS,
    SECTOR_URL,
    USER_AGENT,
)
from notify_line import send_line_notify

# ===========================
# ロギング設定
# ===========================

JST = ZoneInfo("Asia/Tokyo")
logger = logging.getLogger(__name__)
DATETIME_FORMAT = "%Y%m%d_%H%M"


# ===========================
# 時間帯判定
# ===========================


def get_current_time_slot() -> Optional[Tuple[str, str]]:
    """現在時刻にもっとも近い取得対象と設定時刻を返す。

    最初のスロットより前の時間帯で呼び出された場合は ``None`` を返す。
    """

    now = datetime.datetime.now(JST)

    slots: List[Tuple[datetime.datetime, str, str]] = []
    for time_str, target in SECTOR_TIME_SLOTS.items():
        slot_hour, slot_minute = map(int, time_str.split(":"))
        slot_time = now.replace(
            hour=slot_hour,
            minute=slot_minute,
            second=0,
            microsecond=0,
        )
        slots.append((slot_time, time_str, target))

    if not slots:
        logger.warning("SECTOR_TIME_SLOTS が定義されていないため、実行時間帯を判定できません。")
        return None

    slots.sort(key=lambda item: item[0])
    past_slots = [item for item in slots if item[0] <= now]

    if not past_slots:
        _, next_time_str, _ = slots[0]
        logger.info(
            "現在時刻 %s は最初の実行時間帯 %s より前のためスキップします。",
            now.strftime("%H:%M"),
            next_time_str,
        )
        return None

    slot_time, time_str, target = past_slots[-1]

    logger.info(
        "現在時刻 %s は %s の実行時間帯として処理します(許容幅制限なし)",
        now.strftime("%H:%M"),
        time_str,
    )
    return target, time_str


# ===========================
# スクレイピング処理
# ===========================


def scrape_sector_ranking() -> List[Dict[str, str]]:
    """SBI証券の業種別株価平均ランキングをスクレイピング。

    Returns:
        業種ランキングのリスト。各要素は {rank, sector, price, change, prev_price} の辞書。

    Raises:
        requests.exceptions.RequestException: HTTP リクエスト失敗時
        ValueError: HTML パース失敗時
    """
    headers = {"User-Agent": USER_AGENT}

    for attempt in range(1, RETRY_COUNT + 1):
        try:
            logger.info("スクレイピング開始 (試行 %d/%d): %s", attempt, RETRY_COUNT, SECTOR_URL)
            response = requests.get(SECTOR_URL, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            response.encoding = "shift_jis"  # SBI証券はShift_JIS
            break

        except requests.exceptions.RequestException as e:
            logger.warning("HTTP リクエスト失敗 (試行 %d/%d): %s", attempt, RETRY_COUNT, e)
            logger.warning("ステータスコード: %s", getattr(e.response, 'status_code', 'N/A') if hasattr(e, 'response') else 'N/A')

            if attempt < RETRY_COUNT:
                delay = RETRY_DELAYS[min(attempt - 1, len(RETRY_DELAYS) - 1)]
                logger.info("%d 秒後にリトライします...", delay)
                time.sleep(delay)
            else:
                logger.error("最大リトライ回数に達しました。スクレイピングを中止します。")
                logger.error("最終エラー: %s", str(e))
                raise

    # HTML パース
    soup = BeautifulSoup(response.text, "html.parser")

    # ランキングテーブルを探す (class="md-table06")
    table = soup.find("table", class_="md-table06")

    if not table:
        logger.error("ランキングテーブルが見つかりません")
        # デバッグ情報
        all_tables = soup.find_all("table")
        logger.error(f"ページ内のテーブル数: {len(all_tables)}")
        if soup.title:
            logger.error(f"ページタイトル: {soup.title.get_text()}")
        raise ValueError("ランキングテーブルが見つかりません")

    # テーブルの行を取得
    rows = table.find_all("tr")
    if len(rows) < 2:
        logger.error("テーブルに十分な行がありません")
        raise ValueError("テーブルに十分な行がありません")

    rankings = []

    # ヘッダー行をスキップして、データ行を処理
    for row in rows[1:]:  # 最初の行はヘッダー
        cols = row.find_all("td")
        if len(cols) < 5:
            continue

        rank = cols[0].get_text(strip=True)
        sector = cols[1].get_text(strip=True)
        price = cols[2].get_text(strip=True)
        change = cols[3].get_text(strip=True)
        prev_price = cols[4].get_text(strip=True)

        rankings.append(
            {
                "rank": rank,
                "sector": sector,
                "price": price,
                "change": change,
                "prev_price": prev_price,
            }
        )

    logger.info("スクレイピング完了: %d 業種を取得", len(rankings))
    return rankings


# ===========================
# JSON 保存処理
# ===========================


def save_to_json(
    rankings: List[Dict[str, str]], target: str, time_str: str
) -> Path:
    """ランキングデータを JSON ファイルに保存。

    Args:
        rankings: 業種ランキングのリスト
        target: 取得対象 (例: "midday", "closing")
        time_str: 実行時刻文字列 (例: "12:00")

    Returns:
        保存した JSON ファイルのパス
    """
    now = datetime.datetime.now(JST)
    datetime_str = now.strftime(DATETIME_FORMAT)

    data = {
        "datetime": datetime_str,
        "url": SECTOR_URL,
        "target": target,
        "time_slot": time_str,
        "scraped_at": now.isoformat(),
        "rankings": rankings,
    }

    # データディレクトリ作成（プロジェクトルートからの相対パス）
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / SECTOR_DATA_DIR
    data_dir.mkdir(parents=True, exist_ok=True)

    # ファイル名: sector_ranking_YYYYMMDD_HHMM.json
    filename = f"sector_ranking_{datetime_str}.json"
    filepath = data_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info("データ保存完了: %s", filepath)
    return filepath


# ===========================
# LINE 通知処理
# ===========================


def format_sector_message(rankings: List[Dict[str, str]], time_str: str) -> str:
    """業種ランキングのLINE通知メッセージを作成。

    前日比上位1-5位と下位29-33位を表示。

    Args:
        rankings: 業種ランキングのリスト
        time_str: 実行時刻文字列 (例: "12:00")

    Returns:
        フォーマットされたメッセージ文字列
    """
    now = datetime.datetime.now(JST)
    date_str = now.strftime("%Y-%m-%d %H:%M")

    # ヘッダー
    lines = [
        f"📊 {date_str}",
        "業種別株価平均 前日比ランキング",
        "",
    ]

    # 上位5位
    lines.append("【上位 1-5位】🟢")
    for i in range(min(5, len(rankings))):
        rank = rankings[i]
        # changeから騰落率を抽出
        change_text = rank["change"]
        lines.append(f"{rank['rank']}位: {rank['sector']} {change_text}")

    lines.append("")

    # 下位29-33位
    if len(rankings) >= 29:
        lines.append("【下位 29-33位】🔴")
        for i in range(28, min(33, len(rankings))):
            rank = rankings[i]
            change_text = rank["change"]
            lines.append(f"{rank['rank']}位: {rank['sector']} {change_text}")

    return "\n".join(lines)


def send_sector_line_message(rankings: List[Dict[str, str]], time_str: str) -> None:
    """業種ランキングをLINEに通知。

    Args:
        rankings: 業種ランキングのリスト
        time_str: 実行時刻文字列
    """
    message = format_sector_message(rankings, time_str)
    send_line_notify(message)


def format_error_message(error: Exception) -> str:
    """エラーメッセージをフォーマット。

    Args:
        error: 例外オブジェクト

    Returns:
        フォーマットされたエラーメッセージ
    """
    now = datetime.datetime.now(JST)
    return f"❌ 業種ランキング取得失敗\n{now.strftime('%Y-%m-%d %H:%M')}\n\nエラー: {str(error)}"


# ===========================
# メイン処理
# ===========================


def main() -> None:
    """メイン処理。"""
    try:
        # 時間帯判定
        result = get_current_time_slot()
        if result is None:
            logger.info("実行時間帯外のため処理をスキップします。")
            return

        target, time_str = result
        logger.info("取得対象: %s (時刻: %s)", target, time_str)

        # スクレイピング実行
        rankings = scrape_sector_ranking()

        # JSON 保存
        save_to_json(rankings, target, time_str)

        # LINE 通知
        send_sector_line_message(rankings, time_str)

        logger.info("処理が正常に完了しました。")

    except Exception as e:
        logger.exception("予期しないエラーが発生しました: %s", e)
        # エラー通知
        try:
            error_message = format_error_message(e)
            send_line_notify(error_message)
        except Exception as notify_error:
            logger.error("LINE 通知の送信に失敗しました: %s", notify_error)
        sys.exit(1)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    main()
