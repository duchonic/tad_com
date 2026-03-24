# TAD Comments

Comment scraper, AI detector, and browser-based explorer for [trekamdienstag.de](https://trekamdienstag.de).

**Live site:** https://duchonic.github.io/tad_com/

---

## Project structure

```
tad_comments/
├── scraper.py          # Fetches all posts + comments from WordPress REST API
├── detect_ai.py        # Heuristic AI-comment detector
├── index.html          # Comment Explorer UI
├── ki_suspects.html    # KI Suspects viewer UI
├── comments/
│   ├── all_comments.json       # Flat list of all comments (used by the UI)
│   ├── posts_index.json        # Index of all posts (used by the UI)
│   ├── ki_suspects.json        # AI suspect results (used by ki_suspects.html)
│   └── <date>_<slug>.json      # One file per post
```

---

## Setup

```bash
pip install requests
```

---

## Workflow

### 1. Update all data

Fetch the latest posts and comments from the site:

```bash
python scraper.py
```

Re-fetches everything from scratch and overwrites existing JSON files in `comments/`.
Outputs:
- `comments/<date>_<slug>.json` — one file per post
- `comments/all_comments.json` — flat list of all comments (~28 MB)
- `comments/posts_index.json` — index of all posts

### 2. Detect AI-generated comments

```bash
python detect_ai.py
```

Scores every comment using heuristic signals:
- German/English LLM phrase patterns
- Bullet/numbered list structure
- Section headers
- Uniform sentence length
- High transition word density
- HTML list tags

Writes results to `comments/ki_suspects.json` (score ≥ 20 flagged as suspect).
Run the scraper first — `detect_ai.py` reads `all_comments.json`.

### 3. Browse the UI locally

The HTML files use `fetch()` and must be served over HTTP — opening as `file://` will show "Loading comments…" and never load data.

```bash
python -m http.server 8000
```

Open in browser:
- http://localhost:8000 — Comment Explorer
- http://localhost:8000/ki_suspects.html — KI Suspects viewer

### 4. Deploy to GitHub Pages

Commit the updated JSON files and push:

```bash
git add comments/ && git commit -m "Update comment data" && git push
```

The live site at https://duchonic.github.io/tad_com/ updates automatically within ~1 minute.

---

## UI features

### Comment Explorer (`index.html`)

- **Authors panel** — ranked by total comments; click to filter by author
- **Episodes panel** — lists all posts; filters by episode title or date
- **Global search** — type a keyword (e.g. "Picard") to show only episodes that have a comment containing that word, with matching comment count in the pill badge
- **Comments panel** — shows comments for the selected episode, newest first; replies are indented
- **Chart tab** — comments over time, groupable by month/week/year, filterable by author, top-50 authors stacked view, cumulative toggle
- **KI Suspects tab** — links to `ki_suspects.html`

### KI Suspects (`ki_suspects.html`)

- Lists comments flagged as potentially AI-generated, sorted by score
- Shows signals that triggered the flag (phrase matches, structure, etc.)
- Filterable by score threshold, author, episode
