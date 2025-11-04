"""
松井証券ランキングスクレイピング
ランキングデータを取得して保存するメインスクリプト。
"""

from __future__ import annotations

import datetime
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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

# GitHub Actions の cron 文字列と対象スロットの対応表
SCHEDULE_SLOT_OVERRIDES: Dict[str, Tuple[str, str]] = {
    "20 0 * * 1-5": ("morning", "09:20"),
    "35 0 * * 1-5": ("morning", "09:35"),
    "2 3 * * 1-5": ("morning", "12:02"),
    "47 3 * * 1-5": ("afternoon", "12:47"),
    "32 5 * * 1-5": ("afternoon", "14:32"),
}

# ランキング取得対象外の cron（セクター別ランキング専用）
SCHEDULE_SKIP_LIST = {
    "0 3 * * 1-5",
    "0 7 * * 1-5",
}


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
        datetime_str: str,
        target: str,
        rankings: List[Dict[str, str]],
        previous_rankings: Optional[List[Dict[str, str]]] = None,
        slot_time: Optional[str] = None,
    ) -> str:
        """成功通知の簡易フォーマット。"""

        summaries = [
            f"{item.get('rank', '?')}. {item.get('name', '')}"
            for item in rankings[:3]
        ]
        summary = ", ".join(summaries) if summaries else "ランキングデータなし"
        slot_note = f"（対象時刻: {slot_time}）" if slot_time else ""
        return f"[SUCCESS] {datetime_str} {target}{slot_note}: {summary}"

    def format_error_message(
        datetime_str: str,
        target: str,
        error: str,
        slot_time: Optional[str] = None,
    ) -> str:
        """エラー通知の簡易フォーマット。"""

        slot_note = f"（対象時刻: {slot_time}）" if slot_time else ""
        return f"[ERROR] {datetime_str} {target}{slot_note}: {error}"


RankingRecord = Dict[str, str]
RankingList = List[RankingRecord]


def get_current_time_slot() -> Optional[Tuple[str, str]]:
    """現在時刻にもっとも近い取得対象と設定時刻を返す。

    GitHub Actions の遅延により実行時刻が大きくずれても、同日のスロットを
    優先的に割り当てる。まだ最初のスロット前であれば ``None`` を返す。
    """

    now = datetime.datetime.now(JST)

    slots: List[Tuple[datetime.datetime, str, str]] = []
    for time_str, target in TIME_SLOTS.items():
        slot_hour, slot_minute = map(int, time_str.split(":"))
        slot_time = now.replace(
            hour=slot_hour,
            minute=slot_minute,
            second=0,
            microsecond=0,
        )
        slots.append((slot_time, time_str, target))

    if not slots:
        logger.warning("TIME_SLOTS が定義されていないため、実行時間帯を判定できません。")
        return None

    # 時刻順に並べたうえで、現在時刻以前の最新スロットのみ採用
    slots.sort(key=lambda item: item[0])
    past_slots = [item for item in slots if item[0] <= now]

    if not past_slots:
        next_slot_time, next_time_str, _ = slots[0]
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


def load_previous_ranking(target: str) -> Optional[RankingList]:
    """
    前回保存されたランキングデータを読み込む。
    
    Args:
        target: "morning" or "afternoon"
    
    Returns:
        RankingList: 前回のランキングデータ、存在しない場合はNone
    """
    target_dir = DATA_ROOT / target
    
    if not target_dir.exists():
        logger.info("前回のランキングデータが存在しません: %s", target_dir)
        return None
    
    # JSONファイルを新しい順に取得
    json_files = sorted(
        target_dir.glob("ranking_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    # 最新のファイルを読み込む（1つ目は現在実行中のため、2つ目を取得）
    # ただし、まだ保存されていない場合は1つ目を取得
    if len(json_files) >= 1:
        prev_file = json_files[0]
        try:
            with prev_file.open("r", encoding="utf-8") as file:
                data = json.load(file)
                rankings = data.get("rankings", [])
                logger.info("前回のランキングデータを読み込みました: %s (%d件)", prev_file.name, len(rankings))
                return rankings
        except (json.JSONDecodeError, IOError) as exc:
            logger.warning("前回のランキングデータの読み込みに失敗: %s", exc)
            return None
    
    logger.info("前回のランキングファイルが見つかりません")
    return None


def check_recent_execution(target: str, threshold_minutes: int = 10) -> bool:
    """
    指定時間内に実行済みかチェック。

    Args:
        target: "morning" or "afternoon"
        threshold_minutes: 閾値（分）、この時間以内の実行は重複とみなす

    Returns:
        bool: True=最近実行済み（スキップすべき）, False=実行すべき
    """
    target_dir = DATA_ROOT / target

    if not target_dir.exists():
        return False

    # JSONファイルを新しい順に取得
    json_files = sorted(
        target_dir.glob("ranking_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    if not json_files:
        return False

    # 最新ファイルの作成時刻を確認
    latest_file = json_files[0]
    file_mtime = datetime.datetime.fromtimestamp(latest_file.stat().st_mtime, tz=JST)
    now = datetime.datetime.now(JST)
    diff_minutes = (now - file_mtime).total_seconds() / 60

    if diff_minutes < threshold_minutes:
        logger.info(
            "%.1f分前に実行済みです（%s）。重複実行を防止するためスキップします。",
            diff_minutes,
            latest_file.name
        )
        return True

    return False


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

    slot_info: Optional[Tuple[str, str]] = None

    env_target = os.environ.get("RANKING_TARGET")
    env_slot = os.environ.get("RANKING_SLOT")
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
            if schedule_env in SCHEDULE_SKIP_LIST:
                logger.info(
                    "GitHubスケジュール '%s' はランキング取得対象外のため処理をスキップします。",
                    schedule_env,
                )
                logger.info(separator)
                return
            override = SCHEDULE_SLOT_OVERRIDES.get(schedule_env)
            if override:
                slot_info = override
                logger.info(
                    "GitHubスケジュール '%s' をスロット %s (%s) に割り当てます。",
                    schedule_env,
                    override[1],
                    override[0],
                )
            else:
                logger.info(
                    "GitHubスケジュール '%s' に対応するランキングスロットが未定義のため自動判定にフォールバックします。",
                    schedule_env,
                )

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

    # 重複実行チェック（10分以内に実行済みならスキップ）
    if check_recent_execution(target, threshold_minutes=10):
        logger.info("重複実行を防止するため処理を終了します。")
        logger.info(separator)
        return

    url = URLS.get(target)
    if url is None:
        raise KeyError(f"URL for target '{target}' is not defined in config.")

    # 前回のランキングを読み込む
    previous_rankings = load_previous_ranking(target)

    try:
        rankings = scrape_ranking(url)
    except Exception as exc:
        datetime_str = datetime.datetime.now(JST).strftime(DATETIME_FORMAT)
        error_message = format_error_message(
            datetime_str,
            target,
            str(exc),
            slot_time_str,
        )
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
        "target": target,
        "url": url,
        "scraped_at": now.isoformat(),
        "rankings": rankings,
    }

    filepath = save_to_json(data, target)

    # 前回のランキングと比較してメッセージを作成
    message = format_success_message(
        datetime_str,
        target,
        rankings,
        previous_rankings,
        slot_time_str,
    )
    success = send_line_notify(message)
    if not success:
        logger.error("LINE通知の送信に失敗しました（成功通知）")
        raise RuntimeError("LINE通知の送信に失敗しました")
    
    if not LINE_NOTIFY_AVAILABLE:
        logger.info("LINE通知はログ出力のみ (notify_line.py 未実装)。")

    logger.info("JSONファイルを保存しました: %s", filepath)
    logger.info("松井証券ランキング取得 完了")
    logger.info(separator)


if __name__ == "__main__":
    main()
