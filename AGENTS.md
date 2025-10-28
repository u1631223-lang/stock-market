# Repository Guidelines

## Project Structure & Module Organization
- `src/` hosts runtime code: `scrape_rankings.py` drives scraping and LINE notifications, `config.py` centralises time slots, URLs, and HTTP settings, and helpers such as `check_workday.py` and `notify_line.py` keep business-day logic and messaging isolated.
- `data/morning` and `data/afternoon` store committed JSON snapshots named `ranking_YYYYMMDD_HHMM.json`; never hand-edit these files.
- `docs/` contains architecture, setup, and ticket briefs that should be updated when behaviour changes; `.github/workflows/` defines the scheduled scraper and secret smoke tests.
- Utility scripts in the repo root (`inspect_html.py`, `test_scrape_time_override.py`) support manual debugging outside the cron schedule.

## Build, Test, and Development Commands
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python src/scrape_rankings.py           # run full scrape for the current slot
python test_scrape_time_override.py morning  # force morning workflow regardless of time
python inspect_html.py afternoon        # inspect live HTML structure before parser edits
```
- Keep `src` on `PYTHONPATH` or run commands from repo root so scripts can import config.

## Coding Style & Naming Conventions
- Follow PEP 8 with four-space indentation and annotate public functions with type hints; add concise Japanese docstrings when logic is non-trivial.
- Log messages in Japanese with JST timestamps via `ZoneInfo("Asia/Tokyo")`; keep retry, headers, and constants in `config.py` as uppercase names.
- Name modules and functions in `snake_case`; persist new data files using the existing timestamped JSON pattern.

## Testing Guidelines
- Use `test_scrape_time_override.py` to validate scraping branches (`morning` and `afternoon`) and confirm JSON output lands in the correct folder.
- When editing parsing logic, run `inspect_html.py` to snapshot upstream structure and add assertions to protect against layout changes.
- Ensure GitHub Actions workflows (`scrape_rankings.yml`, `test-secret.yml`) succeed locally by mirroring their steps when possible.

## Commit & Pull Request Workflow
- Follow Conventional Commits (`feat:`, `fix:`, `docs:`) with short Japanese summaries; automation will create `Add ranking data: YYYY-MM-DD HH:MM` commits—leave those untouched.
- Reference relevant tickets or docs updates in the body, and describe verification steps (manual run, script output, workflow link).
- For pull requests, include a concise summary, screenshots or log excerpts for notification changes, and confirm required secrets (`LINE_CHANNEL_ACCESS_TOKEN`, `LINE_TARGET_USER_ID`) remain configured.

## Secrets & Automation Notes
- Store messaging tokens in GitHub Secrets; never print them in logs or commit plaintext `.env` files.
- Review scheduling changes against `config.TIME_SLOTS` and the cron definitions in `.github/workflows/scrape_rankings.yml` to keep local and CI behaviour aligned.
