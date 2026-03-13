"""Collect Substack publication data via undocumented public API."""

import argparse
import json
import os
import sys
import time

def main():
    parser = argparse.ArgumentParser(description="Collect Substack publication data for audit")
    parser.add_argument("url", help="Publication URL (e.g., https://yourpub.substack.com)")
    parser.add_argument("output_dir", help="Output directory")
    args = parser.parse_args()

    try:
        import requests
    except ImportError:
        print("requests not installed. Run: pip install requests")
        sys.exit(1)

    # Normalize URL
    pub_url = args.url.rstrip("/")

    os.makedirs(args.output_dir, exist_ok=True)
    output_path = os.path.join(args.output_dir, "substack.jsonl")

    # Fetch all posts via archive endpoint
    print(f"Fetching posts from {pub_url} ...")
    posts = []
    offset = 0
    while True:
        resp = requests.get(
            f"{pub_url}/api/v1/archive",
            params={"sort": "new", "offset": offset, "limit": 50},
        )
        if resp.status_code != 200:
            print(f"Error fetching archive: HTTP {resp.status_code}")
            if not posts:
                sys.exit(1)
            break

        batch = resp.json()
        if not batch:
            break
        posts.extend(batch)
        offset += len(batch)
        print(f"  Fetched {len(posts)} posts so far...")
        time.sleep(0.5)  # Be polite

    print(f"Found {len(posts)} posts. Fetching full content...")

    count = 0
    with open(output_path, "w") as f:
        for i, post in enumerate(posts):
            # Get full post details (includes body and comment count)
            slug = post.get("slug", "")
            body_text = ""
            comment_count = 0

            if slug:
                try:
                    detail_resp = requests.get(f"{pub_url}/api/v1/posts/{slug}")
                    if detail_resp.status_code == 200:
                        detail = detail_resp.json()
                        # Extract plain text from HTML body
                        body_html = detail.get("body_html", "")
                        if body_html:
                            try:
                                from html.parser import HTMLParser
                                class TextExtractor(HTMLParser):
                                    def __init__(self):
                                        super().__init__()
                                        self.parts = []
                                    def handle_data(self, data):
                                        self.parts.append(data)
                                extractor = TextExtractor()
                                extractor.feed(body_html)
                                body_text = " ".join(extractor.parts).strip()
                            except Exception:
                                body_text = body_html
                        comment_count = detail.get("comment_count", 0)
                    time.sleep(0.3)
                except Exception as e:
                    print(f"  Warning: could not fetch detail for '{slug}': {e}")

            entry = {
                "platform": "substack",
                "content_type": "post",
                "title": post.get("title", ""),
                "url": post.get("canonical_url", f"{pub_url}/p/{slug}"),
                "published_date": post.get("post_date", ""),
                "body_text": body_text,
                "metrics": {
                    "views": None,  # Only available via owner export
                    "likes": post.get("reaction_count", post.get("reactions", {}).get("❤", 0)),
                    "comments": comment_count,
                    "shares": None,
                },
                "metadata": {
                    "tags": [],
                    "category": post.get("section_name", ""),
                    "word_count": post.get("word_count", len(body_text.split()) if body_text else 0),
                    "subtitle": post.get("subtitle", ""),
                    "audience": post.get("audience", "everyone"),  # "everyone" or "only_paid"
                },
            }
            f.write(json.dumps(entry) + "\n")
            count += 1

            if (i + 1) % 10 == 0:
                print(f"  Processed {i + 1}/{len(posts)} posts...")

    print(f"Done. Collected {count} posts → {output_path}")
    print(f"\nNote: View counts, open rates, and subscriber data require an owner export.")
    print(f"Export from: Substack dashboard → Settings → Exports")


if __name__ == "__main__":
    main()
