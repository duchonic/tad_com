# CLAUDE.md

## Workflow

### Update all data
```bash
python scraper.py
```

### Start the UI server
```bash
python -m http.server 8000
```
Then open http://localhost:8000 in the browser.

## Notes

- The HTML files use `fetch()` and must be served via HTTP — opening them directly as `file://` shows "Loading comments..." and never loads data.
- `scraper.py` re-fetches everything from scratch each run; it overwrites existing JSON files.
- `detect_ai.py` reads `comments/all_comments.json`, so run the scraper first.
