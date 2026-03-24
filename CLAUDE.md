# CLAUDE.md

## Key facts

- Static site deployed on GitHub Pages: https://duchonic.github.io/tad_com/
- Repo: git@github.com:duchonic/tad_com.git (SSH push requires manual `git push` — SSH key not set up in this environment)
- Data source: trekamdienstag.de WordPress REST API (`https://trekamdienstag.de/wp-json/wp/v2`)
- ~640 posts, ~17k comments, `all_comments.json` is ~28 MB

## Common tasks

### Update all data and deploy
```bash
python scraper.py        # re-scrapes everything (~5 min)
python detect_ai.py      # re-scores AI suspects
git add comments/
git commit -m "Update comment data"
git push                 # must be run manually (SSH issue)
```

### Start local server
```bash
python -m http.server 8000
```
Open http://localhost:8000 — the HTML files cannot be opened as `file://` (fetch() is blocked by the browser).

## File roles

| File | Purpose |
|------|---------|
| `scraper.py` | Fetches all posts + comments from WP REST API, writes `comments/` |
| `detect_ai.py` | Reads `all_comments.json`, writes `ki_suspects.json` |
| `index.html` | Explorer UI — authors, episodes, comments, chart, search |
| `ki_suspects.html` | AI suspect viewer |
| `comments/all_comments.json` | Flat comment list, loaded by the UI (~28 MB) |
| `comments/posts_index.json` | Post index, loaded by the UI |
| `comments/ki_suspects.json` | AI suspect results, loaded by ki_suspects.html |

## UI notes

- Comments are sorted **newest first** in all views
- Global search filters the **episode list** to only episodes with matching comments
- The "KI Suspects" tab in the header links to `ki_suspects.html`
- `ki_suspects.html` has a "← Explorer" back link

## Known issues / constraints

- SSH push is broken in this Claude Code session — always ask the user to run `git push` manually
- `scraper.py` overwrites all files on every run (no incremental update)
- `detect_ai.py` must be run after `scraper.py`
