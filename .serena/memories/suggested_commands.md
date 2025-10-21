# Suggested Commands
- `python3 -m venv venv && source venv/bin/activate` — create/activate local virtual environment (Darwin).
- `pip install -r requirements.txt` — install project dependencies.
- `cd src && python scrape_rankings.py` — run the main scraper locally (requires appropriate time slot or temporary overrides).
- `cd src && python check_workday.py` — test business-day detection once module exists.
- `python -m pip install --upgrade pip` — upgrade pip before dependency install (as used in CI docs).
- `ls -R docs/tickets` — inspect ticket specifications.
- `rg "pattern" -n` — fast code/document search (preferred over grep).
- `python -m unittest` (future) — placeholder for running tests when added (e.g., `test_scrape_rankings.py`).