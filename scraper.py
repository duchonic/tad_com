"""
Scraper for trekamdienstag.de comments via WordPress REST API.
Fetches all posts and their comments, saves to JSON for analytics.
"""

import json
import sys
import time
import requests
from datetime import datetime
from pathlib import Path

# Force UTF-8 output on Windows
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_URL = "https://trekamdienstag.de/wp-json/wp/v2"
OUTPUT_DIR = Path("comments")
OUTPUT_DIR.mkdir(exist_ok=True)

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; comment-scraper/1.0)"
})


def fetch_all_pages(endpoint, params=None):
    """Fetch all pages of a paginated WP REST API endpoint."""
    params = params or {}
    params["per_page"] = 100
    page = 1
    results = []

    while True:
        params["page"] = page
        resp = session.get(f"{BASE_URL}/{endpoint}", params=params)
        if resp.status_code == 400:
            break  # No more pages
        resp.raise_for_status()

        data = resp.json()
        if not data:
            break

        results.extend(data)
        total_pages = int(resp.headers.get("X-WP-TotalPages", 1))
        print(f"  {endpoint}: page {page}/{total_pages} ({len(results)} so far)")

        if page >= total_pages:
            break
        page += 1
        time.sleep(0.3)  # Be polite

    return results


def main():
    print("Fetching all posts...")
    posts = fetch_all_pages(
        "posts",
        {"_fields": "id,slug,date,title,link,categories,tags"}
    )
    print(f"Found {len(posts)} posts total.\n")

    all_data = []
    all_comments = []

    print("Fetching comments for each post...")
    for i, post in enumerate(posts):
        post_id = post["id"]
        post_title = post["title"]["rendered"] if isinstance(post["title"], dict) else post["title"]
        post_date = post["date"]
        post_link = post["link"]

        print(f"[{i+1}/{len(posts)}] {post_title} ({post_date[:10]})")

        comments = fetch_all_pages(
            "comments",
            {"post": post_id, "_fields": "id,post,date,author_name,content,parent,status"}
        )

        post_data = {
            "post_id": post_id,
            "slug": post["slug"],
            "title": post_title,
            "date": post_date,
            "link": post_link,
            "comment_count": len(comments),
            "comments": [
                {
                    "comment_id": c["id"],
                    "date": c["date"],
                    "author_name": c["author_name"],
                    "content": c["content"]["rendered"] if isinstance(c.get("content"), dict) else c.get("content", ""),
                    "parent": c["parent"],
                    "status": c.get("status", "approved"),
                }
                for c in comments
            ]
        }

        all_data.append(post_data)

        # Also collect flat list for easy analytics
        for c in post_data["comments"]:
            all_comments.append({
                **c,
                "post_id": post_id,
                "post_slug": post["slug"],
                "post_title": post_title,
                "post_date": post_date,
            })

    # Save per-post files
    for post_data in all_data:
        filename = OUTPUT_DIR / f"{post_data['date'][:10]}_{post_data['slug']}.json"
        filename.write_text(json.dumps(post_data, ensure_ascii=False, indent=2), encoding="utf-8")

    # Save combined files
    combined_path = OUTPUT_DIR / "all_comments.json"
    combined_path.write_text(
        json.dumps(all_comments, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    posts_index_path = OUTPUT_DIR / "posts_index.json"
    posts_index_path.write_text(
        json.dumps(
            [{"post_id": p["post_id"], "slug": p["slug"], "title": p["title"],
              "date": p["date"], "link": p["link"], "comment_count": p["comment_count"]}
             for p in all_data],
            ensure_ascii=False, indent=2
        ),
        encoding="utf-8"
    )

    total_comments = sum(p["comment_count"] for p in all_data)
    posts_with_comments = sum(1 for p in all_data if p["comment_count"] > 0)

    print(f"\nDone!")
    print(f"  Posts scraped:         {len(all_data)}")
    print(f"  Posts with comments:   {posts_with_comments}")
    print(f"  Total comments:        {total_comments}")
    print(f"  Per-post files in:     {OUTPUT_DIR}/")
    print(f"  Combined file:         {combined_path}")
    print(f"  Posts index:           {posts_index_path}")
    print(f"\nScraped at: {datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
