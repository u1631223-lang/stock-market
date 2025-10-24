"""
セクター別騰落ランキング スクレイピングモジュール

株探（kabutan.jp）のセクター別騰落ランキングを取得し、
上昇TOP5と下落TOP5をLINE通知する。
"""

import datetime
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

# 同じディレクトリのモジュールをインポート
from config import (
    SECTOR_RANKING_URL,
    SECTOR_TIME_SLOTS,
    SECTOR_DATA_DIR,
    USER_AGENT,
    REQUEST_TIMEOUT,
    RETRY_COUNT,
    RETRY_DELAYS,
)
from check_workday import is_trading_day

# JST タイムゾーン
JST = ZoneInfo("Asia/Tokyo")

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# 日時フォーマット
DATETIME_FORMAT = "%Y%m%d_%H%M"


def get_current_time_slot() -> Optional[str]:
    """
    現在時刻が属する取得対象を判定する。

    GitHub Actions の cron 実行には遅延が発生することがあるため、
    設定時刻の±15分以内であれば該当する時間帯として判定する。

    Returns:
        str: 取得対象 ("midday" or "closing")、該当なしの場合は None
    """
    now = datetime.datetime.now(JST)

    best_match = None
    min_diff = float('inf')

    # 各SECTOR_TIME_SLOTに対して、最も近い時刻を探す
    for time_str, target in SECTOR_TIME_SLOTS.items():
        slot_hour, slot_minute = map(int, time_str.split(":"))
        slot_time = now.replace(hour=slot_hour, minute=slot_minute, second=0, microsecond=0)

        # 現在時刻との差分を計算
        time_diff = abs((now - slot_time).total_seconds())

        # ±15分（900秒）以内で、かつ最も近い時刻を選択
        if time_diff <= 900 and time_diff < min_diff:
            min_diff = time_diff
            best_match = (time_str, target)

    if best_match:
        time_str, target = best_match
        logger.info(f"現在時刻 {now.strftime('%H:%M')} は {time_str} の実行時間帯です（許容範囲: ±15分）")
        return target

    return None


def scrape_sector_ranking(url: str) -> List[Dict[str, str]]:
    """
    セクター別騰落ランキングをスクレイピングする。

    Args:
        url: スクレイピング対象URL

    Returns:
        List[Dict]: セクターデータのリスト
            各要素は {"code": "0263", "name": "非鉄金属", "change_percent": "+3.06"}

    Raises:
        Exception: スクレイピング失敗時
    """
    headers = {"User-Agent": USER_AGENT}

    # リトライ処理
    for attempt in range(1, RETRY_COUNT + 1):
        try:
            logger.info(f"HTTP GET: {url} (試行 {attempt}/{RETRY_COUNT})")
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            logger.info(f"HTTP GET 成功: status={response.status_code}")
            break
        except requests.exceptions.RequestException as e:
            if attempt == RETRY_COUNT:
                logger.error(f"HTTP GET 失敗 (試行 {attempt}/{RETRY_COUNT}): {e}")
                raise
            else:
                delay_index = min(attempt - 1, len(RETRY_DELAYS) - 1)
                delay = RETRY_DELAYS[delay_index]
                logger.warning(f"HTTP GET 失敗 (試行 {attempt}/{RETRY_COUNT}): {e}")
                logger.info(f"{delay}秒後にリトライします...")
                time.sleep(delay)

    # HTML解析
    soup = BeautifulSoup(response.content, "lxml")

    # テーブルを探す（複数のパターンを試す）
    table = soup.find("table", class_="stock_kabuka_dwm")
    if not table:
        table = soup.find("table", class_="stock_table")
    if not table:
        table = soup.find("table")

    if not table:
        raise ValueError("ランキングテーブルが見つかりません")

    # tbody内の各行を解析
    tbody = table.find("tbody")
    if not tbody:
        raise ValueError("テーブルのtbodyが見つかりません")

    sectors = []
    rows = tbody.find_all("tr")

    for row in rows:
        try:
            cells = row.find_all(["td", "th"])
            if len(cells) < 7:  # 最低限の列数チェック
                continue

            # コード: 最初のtd内のaタグのテキスト
            code_cell = cells[0]
            code_link = code_cell.find("a")
            code = code_link.text.strip() if code_link else ""

            # セクター名: 2番目のth内のaタグのテキスト
            name_cell = cells[1]
            name_link = name_cell.find("a")
            name = name_link.text.strip() if name_link else ""

            # 前日比（%）: 7番目のtd内のspanのテキスト（%記号を除く）
            change_percent_cell = cells[6]
            change_span = change_percent_cell.find("span")
            if change_span:
                change_text = change_span.text.strip()
                # %記号を除去
                change_percent = change_text.replace("%", "").strip()
            else:
                change_percent = "0.00"

            if code and name and change_percent:
                sectors.append({
                    "code": code,
                    "name": name,
                    "change_percent": change_percent
                })

        except (IndexError, AttributeError) as e:
            logger.warning(f"行のパース失敗: {e}")
            continue

    if not sectors:
        raise ValueError("セクターデータが取得できませんでした")

    logger.info(f"セクターデータ取得: {len(sectors)}件")
    return sectors


def save_to_json(data: Dict[str, Any], target: str) -> str:
    """
    データをJSON形式で保存する。

    Args:
        data: 保存するデータ
        target: 取得対象 ("midday" or "closing")

    Returns:
        str: 保存先ファイルパス
    """
    # ディレクトリ作成
    sector_dir = Path(__file__).parent.parent / SECTOR_DATA_DIR
    sector_dir.mkdir(parents=True, exist_ok=True)

    # ファイル名生成
    datetime_str = data["datetime"]
    filename = f"ranking_{datetime_str}.json"
    filepath = sector_dir / filename

    # JSON保存
    logger.info(f"JSON保存: {filepath}")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info(f"JSONファイルを保存しました: {filepath}")
    return str(filepath)


def format_sector_message(datetime_str: str, target: str, top5: List[Dict], bottom5: List[Dict]) -> str:
    """
    セクター別ランキングのLINE通知メッセージをフォーマットする。

    Args:
        datetime_str: 日時文字列（例: "2025-10-27 12:00"）
        target: "midday" or "closing"
        top5: 上昇TOP5のリスト
        bottom5: 下落TOP5のリスト

    Returns:
        str: フォーマット済みメッセージ
    """
    # 日本語の時間帯名
    target_name = "昼休み" if target == "midday" else "大引け後"

    # 基本メッセージ
    message = f"📊 {datetime_str}\n"
    message += f"セクター別騰落ランキング ({target_name})\n"

    # 上昇TOP5
    message += "\n【上昇TOP5】🟢\n"
    for i, sector in enumerate(top5, 1):
        name = sector["name"]
        change = sector["change_percent"]
        # 符号を明示的に追加（プラスの場合）
        if not change.startswith(("+", "-")):
            change = f"+{change}"
        message += f"{i}位: {name} {change}%\n"

    # 下落TOP5
    message += "\n【下落TOP5】🔴\n"
    for i, sector in enumerate(bottom5, 1):
        name = sector["name"]
        change = sector["change_percent"]
        # 符号を明示的に追加（マイナスの場合）
        if not change.startswith(("+", "-")):
            change = f"-{change}"
        message += f"{i}位: {name} {change}%\n"

    # サマリー
    if top5:
        top_names = ", ".join([s["name"] for s in top5[:2]])
        message += f"\n💡 資金流入: {top_names}"
    if bottom5:
        bottom_names = ", ".join([s["name"] for s in bottom5[:2]])
        message += f"\n💡 資金流出: {bottom_names}"

    return message


def send_sector_line_notify(message: str) -> bool:
    """
    セクター別ランキングのLINE通知を送信する。

    Args:
        message: 送信するメッセージ

    Returns:
        bool: 送信成功時 True、失敗時 False
    """
    # notify_line.pyのsend_line_notifyを使用
    from notify_line import send_line_notify
    return send_line_notify(message)


def format_error_message(datetime_str: str, target: str, error: str) -> str:
    """
    エラー時のLINE通知メッセージをフォーマートする。

    Args:
        datetime_str: 日時文字列
        target: "midday" or "closing"
        error: エラー内容

    Returns:
        str: フォーマット済みメッセージ
    """
    target_name = "昼休み" if target == "midday" else "大引け後"

    message = f"❌ [エラー] {datetime_str}\n"
    message += f"セクター別ランキング取得失敗 ({target_name})\n"
    message += f"\nエラー内容:\n{error}"

    return message


def main() -> None:
    """セクター別ランキング取得からLINE通知までのメイン処理を実行する。"""

    separator = "=" * 60
    logger.info(separator)
    logger.info("セクター別騰落ランキング取得 開始")

    today = datetime.datetime.now(JST).date()

    if not is_trading_day(today):
        logger.info("%s は取引日ではありません。処理を終了します。", today)
        logger.info(separator)
        return

    target = get_current_time_slot()
    if target is None:
        current_time = datetime.datetime.now(JST).strftime("%H:%M")
        logger.info(
            "現在時刻 %s は取得対象の時間帯ではありません。処理をスキップします。",
            current_time,
        )
        logger.info(separator)
        return

    url = SECTOR_RANKING_URL

    try:
        sectors = scrape_sector_ranking(url)
    except Exception as exc:
        now = datetime.datetime.now(JST)
        datetime_str = now.strftime("%Y-%m-%d %H:%M")
        error_message = format_error_message(datetime_str, target, str(exc))
        success = send_sector_line_notify(error_message)
        if not success:
            logger.error("LINE通知の送信に失敗しました（エラー通知）")
            raise RuntimeError("LINE通知の送信に失敗しました") from exc
        logger.error("スクレイピングに失敗しました: %s", exc)
        logger.info(separator)
        raise

    # 前日比で降順ソート（上昇順）
    sectors_sorted_desc = sorted(sectors, key=lambda x: float(x["change_percent"]), reverse=True)
    top5 = sectors_sorted_desc[:5]

    # 前日比で昇順ソート（下落順）
    sectors_sorted_asc = sorted(sectors, key=lambda x: float(x["change_percent"]))
    bottom5 = sectors_sorted_asc[:5]

    # データ保存
    now = datetime.datetime.now(JST)
    datetime_str_file = now.strftime(DATETIME_FORMAT)
    datetime_str_display = now.strftime("%Y-%m-%d %H:%M")

    data: Dict[str, Any] = {
        "datetime": datetime_str_file,
        "url": url,
        "scraped_at": now.isoformat(),
        "sectors": sectors,
        "top5": top5,
        "bottom5": bottom5
    }

    filepath = save_to_json(data, target)

    # LINE通知
    message = format_sector_message(datetime_str_display, target, top5, bottom5)
    success = send_sector_line_notify(message)
    if not success:
        logger.error("LINE通知の送信に失敗しました（成功通知）")
        raise RuntimeError("LINE通知の送信に失敗しました")

    logger.info("JSONファイルを保存しました: %s", filepath)
    logger.info("セクター別騰落ランキング取得 完了")
    logger.info(separator)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"処理中にエラーが発生しました: {e}", exc_info=True)
        sys.exit(1)
