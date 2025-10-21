"""
時間外テスト用スクリプト
targetを強制設定してスクレイピングをテストします
"""

import sys
sys.path.insert(0, 'src')

import datetime
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from scrape_rankings import (
    scrape_ranking,
    save_to_json,
    is_trading_day,
    format_success_message,
    format_error_message,
    send_line_notify,
    URLS,
    logger,
)

JST = ZoneInfo("Asia/Tokyo")

def test_scraping_with_override(target: str = "morning"):
    """targetを強制設定してスクレイピングをテスト"""

    separator = "=" * 60
    logger.info(separator)
    logger.info("【時間外テスト】松井証券ランキング取得 開始")
    logger.info(f"強制設定: target = '{target}'")

    # 営業日チェック
    today = datetime.datetime.now(JST).date()
    if not is_trading_day(today):
        logger.info("%s は取引日ではありません。処理を終了します。", today)
        logger.info(separator)
        return

    # URLを取得
    url = URLS.get(target)
    if url is None:
        raise KeyError(f"URL for target '{target}' is not defined in config.")

    logger.info(f"取得URL: {url}")

    try:
        # スクレイピング実行
        rankings = scrape_ranking(url)

        # データ作成
        now = datetime.datetime.now(JST)
        datetime_str = now.strftime("%Y%m%d_%H%M")
        data = {
            "datetime": datetime_str,
            "target": target,
            "url": url,
            "scraped_at": now.isoformat(),
            "rankings": rankings,
        }

        # JSON保存
        filepath = save_to_json(data, target)
        logger.info(f"JSONファイルを保存しました: {filepath}")

        # データ確認
        logger.info(f"取得件数: {len(rankings)}件")
        logger.info("ベスト3:")
        for i, item in enumerate(rankings[:3], 1):
            logger.info(f"  {i}. {item.get('name', '不明')} ({item.get('code', '----')})")

        # 成功メッセージ
        message = format_success_message(datetime_str, target, rankings)
        logger.info("LINE通知メッセージ:")
        logger.info(message)

        # 保存されたJSONの確認
        logger.info("\n保存されたJSON:")
        with open(filepath, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
            logger.info(json.dumps(saved_data, ensure_ascii=False, indent=2))

        logger.info("【時間外テスト】松井証券ランキング取得 完了")
        logger.info(separator)

    except Exception as exc:
        datetime_str = datetime.datetime.now(JST).strftime("%Y%m%d_%H%M")
        error_message = format_error_message(datetime_str, target, str(exc))
        logger.error("スクレイピングに失敗しました: %s", exc)
        logger.error("エラーメッセージ: %s", error_message)
        logger.info(separator)
        raise

if __name__ == "__main__":
    # 朝のランキングでテスト
    target = sys.argv[1] if len(sys.argv) > 1 else "morning"
    test_scraping_with_override(target)
