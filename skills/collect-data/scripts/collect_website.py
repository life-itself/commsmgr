"""Collect website content using trafilatura."""

import argparse
import json
import os
import sys

def main():
    parser = argparse.ArgumentParser(description="Collect website content for audit")
    parser.add_argument("url", help="Website URL (e.g., https://example.org)")
    parser.add_argument("output_dir", help="Output directory")
    args = parser.parse_args()

    try:
        from trafilatura import sitemaps, fetch_url, bare_extraction
    except ImportError:
        print("trafilatura not installed. Run: pip install trafilatura")
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)
    output_path = os.path.join(args.output_dir, "website.jsonl")

    # Discover URLs via sitemap
    print(f"Discovering pages from {args.url} ...")
    urls = sitemaps.sitemap_search(args.url)

    if not urls:
        # Fallback: try crawl-based discovery
        print("No sitemap found, trying crawl discovery...")
        from trafilatura import crawls
        urls = crawls.focused_crawler(args.url, max_seen_urls=500, max_known_urls=1000)
        if urls:
            urls = list(urls[0])  # crawl returns (known, seen) tuple

    if not urls:
        print(f"Could not discover any pages at {args.url}")
        sys.exit(1)

    print(f"Found {len(urls)} pages. Extracting content...")

    count = 0
    with open(output_path, "w") as f:
        for i, url in enumerate(urls):
            html = fetch_url(url)
            if not html:
                continue

            result = bare_extraction(html, with_metadata=True)
            if not result:
                continue

            text = result.text or ""
            tags_raw = result.tags or ""
            entry = {
                "platform": "website",
                "content_type": "page",
                "title": result.title or "",
                "url": url,
                "published_date": result.date or "",
                "body_text": text,
                "metrics": {
                    "views": None,
                    "likes": None,
                    "comments": None,
                    "shares": None,
                },
                "metadata": {
                    "tags": tags_raw.split(",") if tags_raw else [],
                    "category": result.categories or "",
                    "word_count": len(text.split()) if text else 0,
                    "author": result.author or "",
                },
            }
            f.write(json.dumps(entry) + "\n")
            count += 1

            if (i + 1) % 20 == 0:
                print(f"  Processed {i + 1}/{len(urls)} pages...")

    print(f"Done. Collected {count} pages → {output_path}")


if __name__ == "__main__":
    main()
