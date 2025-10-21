# Code Style & Conventions
- Follow standard PEP 8 formatting with explicit type hints for function signatures (typing module usage).
- Provide Japanese docstrings explaining purpose/returns for each public function; include context when logic is non-trivial.
- Prefer clear constant definitions in `config.py`; avoid magic numbers scattered in code.
- Use timezone-aware timestamps via `ZoneInfo("Asia/Tokyo")` and format strings like `%Y%m%d_%H%M`.
- Logging should emit human-readable Japanese messages, including timestamps in JST.
- HTTP logic uses `requests` with custom User-Agent and retry/backoff parameters defined in config.
- JSON persistence uses UTF-8, `ensure_ascii=False`, and `indent=2` (matching constants set in scraper).