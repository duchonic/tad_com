# TAD Comments

Comment scraper and explorer for [trekamdienstag.de](https://trekamdienstag.de).

## Setup

```bash
pip install requests
```

## Usage

### 1. Scrape comments

```bash
python scraper.py
```

Fetches all posts and comments from the WordPress REST API and saves them to `comments/`.

Output files:
- `comments/<date>_<slug>.json` — one file per post
- `comments/all_comments.json` — flat list of all comments
- `comments/posts_index.json` — index of all posts

### 2. Detect AI-generated comments

```bash
python detect_ai.py
```

Scores comments on heuristic signals (AI phrases, list structure, sentence uniformity, etc.) and writes `comments/ki_suspects.json`.

### 3. Browse in the UI

The HTML files need to be served via HTTP (browsers block local `fetch()` calls):

```bash
python -m http.server 8000
```

Then open:
- http://localhost:8000 — Comment Explorer
- http://localhost:8000/ki_suspects.html — AI Suspect Viewer
