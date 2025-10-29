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
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
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

# GitHub Actions の cron 文字列とセクター別スロットの対応表
SECTOR_SCHEDULE_SLOT_OVERRIDES: Dict[str, Tuple[str, str]] = {
    "0 3 * * 1-5": ("midday", "12:00"),
    "0 7 * * 1-5": ("closing", "16:00"),
}


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
        "現在時刻 %s は %s の実行時間帯として処理します（許容幅制限なし）",
        now.strftime("%H:%M"),
        time_str,
    )
    return target, time_str


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

            # 前日比（%）: 6番目のtd内のspanのテキスト（%記号を除く）
            # 注意: cells[5] が前日比(%)、cells[6] は PER
            change_percent_cell = cells[5]
            change_span = change_percent_cell.find("span")
            if change_span:
                change_text = change_span.get_text(strip=True)
            else:
                change_text = change_percent_cell.get_text(strip=True)

            change_text = change_text.replace(",", "").replace("％", "%")
            change_text = change_text.replace("−", "-")
            change_text = change_text.replace("前日比", "")

            match = re.search(r"([-+]?\d+(?:\.\d+)?)", change_text)
            if not match:
                logger.warning(f"数値化できない前日比: {change_text}")
                continue

            change_percent = match.group(1)

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


def format_sector_message(
    datetime_str: str,
    target: str,
    top5: List[Dict],
    bottom5: List[Dict],
    slot_time: Optional[str] = None,
) -> str:
    """
    セクター別ランキングのLINE通知メッセージをフォーマットする。

    Args:
        datetime_str: 日時文字列（例: "2025-10-27 12:00"）
        target: "midday" or "closing"
        top5: 上昇TOP5のリスト
        bottom5: 下落TOP5のリスト
        slot_time: 取得対象の予定時刻（例: "12:00"）

    Returns:
        str: フォーマット済みメッセージ
    """
    # 日本語の時間帯名
    target_name = "昼休み" if target == "midday" else "大引け後"
    slot_note = f"（対象時刻: {slot_time}）" if slot_time else ""

    # 基本メッセージ
    message = f"📊 {datetime_str}\n"
    message += f"セクター別騰落ランキング ({target_name}){slot_note}\n"

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
        # 符号を明示的に追加（符号がない場合のみ、実際の値を見て判定）
        if not change.startswith(("+", "-")):
            try:
                # 数値として解釈して符号を判定
                val = float(change)
                if val >= 0:
                    change = f"+{change}"
                else:
                    # すでにマイナスなら符号は不要（-0.5 など）
                    pass
            except ValueError:
                # 数値化できない場合はそのまま
                pass
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


def format_error_message(
    datetime_str: str,
    target: str,
    error: str,
    slot_time: Optional[str] = None,
) -> str:
    """
    エラー時のLINE通知メッセージをフォーマートする。

    Args:
        datetime_str: 日時文字列
        target: "midday" or "closing"
        error: エラー内容
        slot_time: 取得対象の予定時刻（例: "12:00"）

    Returns:
        str: フォーマット済みメッセージ
    """
    target_name = "昼休み" if target == "midday" else "大引け後"

    slot_note = f"（対象時刻: {slot_time}）" if slot_time else ""

    message = f"❌ [エラー] {datetime_str}\n"
    message += f"セクター別ランキング取得失敗 ({target_name}){slot_note}\n"
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

    slot_info: Optional[Tuple[str, str]] = None

    env_target = os.environ.get("SECTOR_TARGET")
    env_slot = os.environ.get("SECTOR_SLOT")
    if env_target and env_slot:
        slot_info = (env_target, env_slot)
        logger.info(
            "環境変数オーバーライドを検出しました: target=%s, slot=%s",
            env_target,
            env_slot,
        )

    if slot_info is None:
        schedule_env = (
            os.environ.get("EVENT_SCHEDULE")
            or os.environ.get("GITHUB_EVENT_SCHEDULE")
            or ""
        ).strip()
        if schedule_env:
            override = SECTOR_SCHEDULE_SLOT_OVERRIDES.get(schedule_env)
            if override:
                slot_info = override
                logger.info(
                    "GitHubスケジュール '%s' をセクタースロット %s (%s) に割り当てます。",
                    schedule_env,
                    override[1],
                    override[0],
                )
            else:
                logger.info(
                    "GitHubスケジュール '%s' はセクター別ランキング取得の対象ではないため処理をスキップします。",
                    schedule_env,
                )
                logger.info(separator)
                return

    if slot_info is None:
        slot_info = get_current_time_slot()

    if slot_info is None:
        current_time = datetime.datetime.now(JST).strftime("%H:%M")
        logger.info(
            "現在時刻 %s は取得対象の時間帯ではありません。処理をスキップします。",
            current_time,
        )
        logger.info(separator)
        return

    target, slot_time_str = slot_info

    url = SECTOR_RANKING_URL

    try:
        sectors = scrape_sector_ranking(url)
    except Exception as exc:
        now = datetime.datetime.now(JST)
        datetime_str = now.strftime("%Y-%m-%d %H:%M")
        error_message = format_error_message(
            datetime_str,
            target,
            str(exc),
            slot_time_str,
        )
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
        "slot_time": slot_time_str,
        "url": url,
        "scraped_at": now.isoformat(),
        "sectors": sectors,
        "top5": top5,
        "bottom5": bottom5
    }

    filepath = save_to_json(data, target)

    # LINE通知
    message = format_sector_message(
        datetime_str_display,
        target,
        top5,
        bottom5,
        slot_time_str,
    )
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
