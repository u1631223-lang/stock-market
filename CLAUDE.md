# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an automated stock ranking scraper that collects top 10 rankings from Matsui Securities (松井証券) at specific times during trading days. It runs on GitHub Actions and sends notifications via LINE Messaging API.

**Note:** LINE Notify was discontinued on March 31, 2025. This project has been migrated to LINE Messaging API.

**Target URLs:**
- Morning rankings: `https://finance.matsui.co.jp/ranking-day-trading-morning/index?condition=0&market=0`
- Afternoon rankings: `https://finance.matsui.co.jp/ranking-day-trading-afternoon/index?condition=0&market=0`

**Execution Schedule (JST, ±15分の許容範囲あり):**
- Morning: 09:17頃, 09:32頃, 12:02頃
- Afternoon: 12:47頃, 14:32頃
- Only runs on weekdays (excluding Japanese holidays)
- **注意**: GitHub Actions cronは混雑時間帯（UTC 00:00, 03:00など）を避けるため、数分ずらして設定しています

## Architecture

**Execution Flow:**
1. `check_workday.py` - Validates trading day (weekend/holiday check using jpholiday)
2. `scrape_rankings.py` - Main orchestrator: determines time slot, scrapes data, loads previous ranking, saves JSON
3. `notify_line.py` - Sends success/failure notifications to LINE with ranking changes
4. GitHub Actions commits results to `data/morning/` or `data/afternoon/`

**Module Responsibilities:**
- `config.py` - Central configuration (URLs, time slots, retry logic, User-Agent)
- `check_workday.py` - Trading day validation (土日祝判定)
- `scrape_rankings.py` - HTTP requests, HTML parsing, JSON storage, previous ranking loading, error handling
- `notify_line.py` - LINE Messaging API integration with message formatting and ranking change display

**Data Flow:**
```
GitHub Actions Cron → check_workday → scrape_rankings → load previous ranking
→ BeautifulSoup parsing → JSON save to data/{morning|afternoon}/
→ git commit/push → LINE notification with ranking changes
```

## Development Commands

### Local Testing

```bash
# Setup virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Test individual modules
cd src
python check_workday.py              # Test trading day logic

# Test LINE Messaging API notification
export LINE_CHANNEL_ACCESS_TOKEN="your_channel_access_token"
export LINE_TARGET_USER_ID="your_user_id"
python notify_line.py                # Test LINE notification

python scrape_rankings.py            # Test full scraping flow
```

### Testing Scraping Outside Scheduled Times

To test scraping when it's not one of the scheduled times, temporarily modify `scrape_rankings.py`:

```python
# In main() function, replace:
target = get_current_time_slot()
# With:
target = "morning"  # or "afternoon"
```

**Important:** Revert this change before committing.

### GitHub Actions

```bash
# Trigger manual workflow run
# Go to: Actions → Scheduled Ranking Scrape → Run workflow

# View logs
# Actions tab → Select workflow run → View step logs
```

## Critical Implementation Details

### HTML Structure Dependency

The `scrape_ranking()` function in `scrape_rankings.py` contains HTML parsing logic that **must be adjusted** based on actual page structure:

```python
# Multiple fallback patterns for finding the ranking table
table = soup.find("table", class_="ranking-table")  # Pattern 1
if not table:
    table = soup.find("table", id="rankingTable")   # Pattern 2
if not table:
    table = soup.find("table")                       # Pattern 3
```

**When HTML structure changes:**
1. Open target URL in browser
2. Use DevTools (F12) to inspect table structure
3. Update selectors in `scrape_ranking()` to match actual class names, IDs, and column indices
4. Test locally before pushing

### Anti-Scraping Measures

The site returns 403 errors without proper User-Agent. Current implementation:
- Sets browser-like User-Agent in `config.py`
- Implements retry logic (3 attempts with exponential backoff: 5s, 10s, 20s)
- Respects rate limits (only 1 request per scheduled time)

### Time Zone Handling

- GitHub Actions cron runs in UTC
- All cron times in workflow are UTC equivalents of JST times
- Python code uses `ZoneInfo("Asia/Tokyo")` for JST
- Current time comparison uses JST for matching TIME_SLOTS

### Error Handling Strategy

All exceptions in `scrape_rankings.py` trigger LINE notifications with error details. Common failures:
- `requests.exceptions.RequestException` → Network/HTTP errors → Retried
- `AttributeError` → HTML structure changed → Immediate notification
- Weekend/holiday execution → Silent skip (no notification)

## Configuration

### Environment Variables

**Required for LINE Messaging API (since March 31, 2025):**
- `LINE_CHANNEL_ACCESS_TOKEN` - Channel access token from LINE Developers
- `LINE_TARGET_USER_ID` - User ID to send notifications to

Set these in GitHub Secrets (Settings → Secrets and variables → Actions)

### Key Config Values (src/config.py)

- `URLS` - Target scraping URLs
- `TIME_SLOTS` - Valid execution times (HH:MM format in JST)
- `RETRY_COUNT` / `RETRY_DELAYS` - Retry behavior
- `USER_AGENT` - Browser identification string
- `DATA_DIR` - Output directory for JSON files

## Data Format

JSON files saved as `data/{morning|afternoon}/ranking_YYYYMMDD_HHMM.json`:

```json
{
  "datetime": "20251020_0915",
  "url": "https://...",
  "scraped_at": "2025-10-20T09:15:03+09:00",
  "rankings": [
    {
      "rank": "1",
      "code": "1234",
      "name": "Company Name",
      "price": "1,234",
      "change": "+56",
      "change_percent": "+4.76%",
      "volume": "12,345,678",
      "value": "1,234,567,890"
    }
  ]
}
```

**Note:** Actual fields depend on HTML structure and may need adjustment.

## Documentation

Comprehensive documentation in `docs/`:
- `requirements.md` - Full requirements and constraints
- `architecture.md` - System design, component responsibilities, operational procedures
- `technical-stack.md` - Technology choices and rationale
- `implementation-guide.md` - Complete code implementations with troubleshooting
- `setup-guide.md` - Step-by-step setup from scratch

## LINE Notification Format

**New format (2025-10-24):**
```
📊 2025-10-24 09:32
午前中資金流入ランキング

1位: [285A] キオクシアホールディングス +11.94% 🔺↑1
2位: [9984] ソフトバンクグループ +3.37% 🔻↓1
3位: [6920] レーザーテック +3.90% -
4位: [6857] アドバンテスト +3.23% 🔺↑1
5位: [3692] ＦＦＲＩセキュリティ +12.73% 🆕NEW
...
```

**Ranking change indicators:**
- 🔺↑N: Rank improved (moved up N positions)
- 🔻↓N: Rank declined (moved down N positions)
- -: No change from previous ranking
- 🆕NEW: New entry (not in previous top 10)

**Note:** First execution of the day (09:17) shows no ranking changes as there's no previous data to compare.

## System Status

**✅ Production Ready (2025-10-24)**

All components have been tested and verified:
- ✅ GitHub Actions automatic execution configured (cron adjusted to avoid congestion)
- ✅ Scraping functionality working correctly (top 10 rankings)
- ✅ LINE Messaging API notifications verified with ranking changes
- ✅ Git auto-commit with proper permissions
- ✅ Error handling and retry logic tested
- ✅ Ranking change detection implemented

**Next scheduled execution:** Weekdays at 09:17, 09:32, 12:02, 12:47, 14:32 JST (±15分)

## Common Issues

**"ランキングテーブルが見つかりません" error:**
- HTML structure has changed
- Inspect actual page structure and update `scrape_ranking()` table selectors

**LINE notification not working:**
- Verify `LINE_CHANNEL_ACCESS_TOKEN` and `LINE_TARGET_USER_ID` are set in GitHub Secrets
- User ID must be in format `Uxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` (33 characters starting with U)
- Test token validity locally with `notify_line.py`

**Execution on holidays:**
- Verify jpholiday is correctly installed
- Check `check_workday.py` logic for date in question

**403 Forbidden errors:**
- 松井証券 may have strengthened anti-scraping measures
- May need to adjust User-Agent or implement additional headers
- Consider adding referrer headers or cookies if needed

**GitHub Actions permission errors:**
- Settings → Actions → General → Workflow permissions
- Set to "Read and write permissions"