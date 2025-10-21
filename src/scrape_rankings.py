"""
松井証券ランキングスクレイピング
ランキングデータを取得して保存するメインスクリプト。
"""

from __future__ import annotations

import datetime
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup
from zoneinfo import ZoneInfo

from config import (
    DATA_DIR,
    REQUEST_TIMEOUT,
    RETRY_COUNT,
    RETRY_DELAYS,
    TIME_SLOTS,
    URLS,
    USER_AGENT,
)

JST = ZoneInfo("Asia/Tokyo")
DATETIME_FORMAT = "%Y%m%d_%H%M"
JSON_INDENT = 2
TOP_LIMIT = 10
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_ROOT = BASE_DIR / DATA_DIR


class JSTFormatter(logging.Formatter):
    """JSTタイムゾーンでログ時刻を整形するフォーマッタ。"""

    def formatTime(
        self, record: logging.LogRecord, datefmt: Optional[str] = None
    ) -> str:
        timestamp = datetime.datetime.fromtimestamp(record.created, JST)
        if datefmt:
            return timestamp.strftime(datefmt)
        return timestamp.isoformat(timespec="seconds")


logger = logging.getLogger("scrape_rankings")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        JSTFormatter(
            "[%(asctime)s] [%(levelname)s] %(message)s",
            "%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


CHECK_WORKDAY_FALLBACK = False
try:  # pragma: no cover - fallbackは後続チケットで置き換え予定
    from check_workday import is_trading_day  # type: ignore
except ImportError:
    CHECK_WORKDAY_FALLBACK = True

    try:
        import jpholiday
    except ImportError:  # pragma: no cover - インポート失敗時は週末のみ判定
        jpholiday = None  # type: ignore

    def is_trading_day(date: Optional[datetime.date] = None) -> bool:
        """check_workday.py がない場合の簡易的な営業日判定。"""

        if date is None:
            date = datetime.datetime.now(JST).date()

        if date.weekday() >= 5:
            return False

        if jpholiday is not None:
            try:
                return not jpholiday.is_holiday(date)
            except Exception:  # pragma: no cover - jpholidayの想定外エラー
                logger.debug("jpholiday の判定に失敗したため祝日判定をスキップします。")

        return True


LINE_NOTIFY_AVAILABLE = True
try:  # pragma: no cover - 後続チケットで正式実装予定
    from notify_line import (  # type: ignore
        format_error_message,
        format_success_message,
        send_line_notify,
    )
except ImportError:
    LINE_NOTIFY_AVAILABLE = False

    def send_line_notify(message: str) -> bool:
        """LINE Notify 未実装時のフォールバック。"""

        logger.info("LINE通知(未設定): %s", message)
        return False

    def format_success_message(
        datetime_str: str, target: str, rankings: List[Dict[str, str]]
    ) -> str:
        """成功通知の簡易フォーマット。"""

        summaries = [
            f"{item.get('rank', '?')}. {item.get('name', '')}"
            for item in rankings[:3]
        ]
        summary = ", ".join(summaries) if summaries else "ランキングデータなし"
        return f"[SUCCESS] {datetime_str} {target}: {summary}"

    def format_error_message(datetime_str: str, target: str, error: str) -> str:
        """エラー通知の簡易フォーマット。"""

        return f"[ERROR] {datetime_str} {target}: {error}"


RankingRecord = Dict[str, str]
RankingList = List[RankingRecord]


def get_current_time_slot() -> Optional[str]:
    """現在時刻が属する取得対象を判定する。"""

    now = datetime.datetime.now(JST)
    current_time = now.strftime("%H:%M")
    return TIME_SLOTS.get(current_time)


def scrape_ranking(url: str) -> RankingList:
    """指定URLからランキングデータを取得する。"""

    headers = {"User-Agent": USER_AGENT}
    response: Optional[requests.Response] = None

    for attempt in range(1, RETRY_COUNT + 1):
        try:
            logger.info(
                "HTTP GET: %s (試行 %d/%d)", url, attempt, RETRY_COUNT
            )
            response = requests.get(
                url, headers=headers, timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            logger.info("HTTP GET 成功: status=%s", response.status_code)
            break
        except requests.exceptions.RequestException as exc:
            logger.warning("HTTP通信エラー: %s", exc)
            if attempt == RETRY_COUNT:
                raise
            delay_index = min(attempt - 1, len(RETRY_DELAYS) - 1)
            delay = RETRY_DELAYS[delay_index]
            logger.info("%s 秒後にリトライします。", delay)
            time.sleep(delay)

    if response is None:
        raise requests.exceptions.RequestException("HTTPレスポンスを取得できませんでした。")

    soup = BeautifulSoup(response.text, "lxml")

    # テーブル検索（複数パターン）
    table = soup.find("table", class_="m-table")
    if table is None:
        table = soup.find("table", class_="ranking-table")
    if table is None:
        table = soup.find("table", id="rankingTable")
    if table is None:
        table = soup.find("table")

    if table is None:
        raise AttributeError("ランキングテーブルが見つかりません。HTML構造を確認してください。")

    rankings: RankingList = []
    rows = table.find_all("tr")

    for row in rows[1:]:  # ヘッダー行をスキップ
        cells = row.find_all(["td", "th"])
        if len(cells) < 2:
            continue

        # セルの構造: [順位, 銘柄名(コード/市場), 現在値, 変動額, 出来高, 概算売買代金, 株価変動率, 注文]
        rank_text = cells[0].get_text(strip=True)

        # 銘柄名とコードの分離
        name_code_text = cells[1].get_text(strip=True) if len(cells) > 1 else ""

        # 銘柄名とコードを分離（例: "ソフトバンクグループ9984 東P" or "キオクシアホールディングス285A 東P"）
        import re
        # パターン: 銘柄名 + (3-4桁の数字+文字 または 4桁の数字) + 市場コード
        match = re.search(r'^(.+?)([0-9]{3,4}[A-Z]?)\s+(.*)$', name_code_text)
        if match:
            name = match.group(1).strip()
            code = match.group(2).strip()
        else:
            # コードが見つからない場合は全体を銘柄名とする
            name = name_code_text
            code = ""

        record: RankingRecord = {
            "rank": rank_text,
            "code": code,
            "name": name,
        }

        # 現在値（index 2）
        if len(cells) > 2:
            record["price"] = cells[2].get_text(strip=True)

        # 変動額（index 3に含まれる）
        if len(cells) > 3:
            change_text = cells[3].get_text(strip=True)
            record["change"] = change_text

        # 出来高（index 4）
        if len(cells) > 4:
            volume_text = cells[4].get_text(strip=True)
            record["volume"] = volume_text

        # 概算売買代金（index 5）
        if len(cells) > 5:
            value_text = cells[5].get_text(strip=True)
            record["value"] = value_text

        # 株価変動率（index 6）
        if len(cells) > 6:
            change_percent_text = cells[6].get_text(strip=True)
            record["change_percent"] = change_percent_text

        rankings.append(record)
        if len(rankings) >= TOP_LIMIT:
            break

    if not rankings:
        raise AttributeError("ランキングデータが取得できませんでした。HTML構造を確認してください。")

    logger.info("ランキングデータ取得: %d件", len(rankings))
    return rankings


def save_to_json(data: Dict[str, Any], target: str) -> str:
    """取得データをJSON形式で保存する。"""

    target_dir = DATA_ROOT / target
    target_dir.mkdir(parents=True, exist_ok=True)

    timestamp = data.get("datetime")
    if not isinstance(timestamp, str) or not timestamp:
        timestamp = datetime.datetime.now(JST).strftime(DATETIME_FORMAT)
        data["datetime"] = timestamp

    filename = f"ranking_{timestamp}.json"
    filepath = target_dir / filename

    with filepath.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=JSON_INDENT)

    logger.info("JSON保存: %s", filepath)
    return str(filepath)


def main() -> None:
    """ランキング取得から保存までのメイン処理を実行する。"""

    separator = "=" * 60
    logger.info(separator)
    logger.info("松井証券ランキング取得 開始")

    today = datetime.datetime.now(JST).date()
    if CHECK_WORKDAY_FALLBACK:
        logger.warning("check_workday.py が未実装のため簡易営業日判定を使用します。")

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

    url = URLS.get(target)
    if url is None:
        raise KeyError(f"URL for target '{target}' is not defined in config.")

    try:
        rankings = scrape_ranking(url)
    except Exception as exc:
        datetime_str = datetime.datetime.now(JST).strftime(DATETIME_FORMAT)
        error_message = format_error_message(datetime_str, target, str(exc))
        send_line_notify(error_message)
        logger.error("スクレイピングに失敗しました: %s", exc)
        logger.info(separator)
        raise

    now = datetime.datetime.now(JST)
    datetime_str = now.strftime(DATETIME_FORMAT)
    data: Dict[str, Any] = {
        "datetime": datetime_str,
        "target": target,
        "url": url,
        "scraped_at": now.isoformat(),
        "rankings": rankings,
    }

    filepath = save_to_json(data, target)

    message = format_success_message(datetime_str, target, rankings)
    send_line_notify(message)
    if not LINE_NOTIFY_AVAILABLE:
        logger.info("LINE通知はログ出力のみ (notify_line.py 未実装)。")

    logger.info("JSONファイルを保存しました: %s", filepath)
    logger.info("松井証券ランキング取得 完了")
    logger.info(separator)


if __name__ == "__main__":
    main()

