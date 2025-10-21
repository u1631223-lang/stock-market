# Task Completion Checklist
- Ensure relevant ticket in `docs/tickets/` has status/checkboxes updated to reflect progress.
- Run `cd src && python scrape_rankings.py` (or targeted scripts) when logic changes affect scraping/output; verify JSON files appear under `data/<target>`.
- If modifying business-day or notification logic, run corresponding module scripts (`python check_workday.py`, `python notify_line.py --test` once available).
- Review generated JSON to confirm top-10 structure and expected keys before finishing.
- Document notable limitations or manual steps (e.g., sandbox restrictions, pending modules) in the final response to the user.