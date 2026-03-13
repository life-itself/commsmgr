"""Parse a Facebook data export (JSON or CSV) into the common JSONL format."""

import argparse
import csv
import json
import os
import sys
import zipfile

def parse_json_export(export_path, output_path):
    """Parse Facebook JSON export (from 'Download Your Information')."""
    posts_data = []

    # Could be a directory or a ZIP
    if zipfile.is_zipfile(export_path):
        with zipfile.ZipFile(export_path, "r") as zf:
            # Look for posts files
            for name in zf.namelist():
                if "posts" in name.lower() and name.endswith(".json"):
                    raw = zf.read(name).decode("utf-8")
                    data = json.loads(raw)
                    if isinstance(data, list):
                        posts_data.extend(data)
                    elif isinstance(data, dict):
                        posts_data.extend(data.get("data", data.get("posts", [data])))
    elif os.path.isdir(export_path):
        # Walk directory for posts JSON files
        for root, dirs, files in os.walk(export_path):
            for fname in files:
                if "posts" in fname.lower() and fname.endswith(".json"):
                    with open(os.path.join(root, fname)) as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            posts_data.extend(data)
                        elif isinstance(data, dict):
                            posts_data.extend(data.get("data", data.get("posts", [data])))
    else:
        # Single JSON file
        with open(export_path) as f:
            data = json.load(f)
            if isinstance(data, list):
                posts_data = data
            elif isinstance(data, dict):
                posts_data = data.get("data", data.get("posts", [data]))

    count = 0
    with open(output_path, "w") as f:
        for post in posts_data:
            # Facebook JSON export uses 'data' array with 'post' text
            text = ""
            if isinstance(post, dict):
                # Try various Facebook export formats
                if "data" in post:
                    for d in post["data"]:
                        if "post" in d:
                            text = d["post"]
                elif "message" in post:
                    text = post["message"]
                elif "text" in post:
                    text = post["text"]

            timestamp = post.get("timestamp", "")
            if isinstance(timestamp, (int, float)):
                from datetime import datetime, timezone
                timestamp = datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()

            entry = {
                "platform": "facebook",
                "content_type": "post",
                "title": post.get("title", ""),
                "url": post.get("url", post.get("permalink", "")),
                "published_date": timestamp,
                "body_text": text,
                "metrics": {
                    "views": None,
                    "likes": None,
                    "comments": None,
                    "shares": None,
                },
                "metadata": {
                    "tags": [],
                    "category": "",
                    "word_count": len(text.split()) if text else 0,
                },
            }
            f.write(json.dumps(entry) + "\n")
            count += 1

    return count


def parse_csv_export(csv_path, output_path):
    """Parse Facebook Page Insights CSV export."""
    count = 0
    with open(csv_path, newline="", encoding="utf-8-sig") as infile, \
         open(output_path, "w") as outfile:
        reader = csv.DictReader(infile)
        for row in reader:
            # Page Insights CSV has various column names depending on export type
            text = row.get("Post Message", row.get("Message", row.get("Description", "")))
            date = row.get("Post Created", row.get("Date", row.get("Created", "")))

            entry = {
                "platform": "facebook",
                "content_type": "post",
                "title": row.get("Title", ""),
                "url": row.get("Permalink", row.get("URL", "")),
                "published_date": date,
                "body_text": text,
                "metrics": {
                    "views": _int_or_none(row.get("Impressions", row.get("Reach"))),
                    "likes": _int_or_none(row.get("Likes", row.get("Reactions"))),
                    "comments": _int_or_none(row.get("Comments")),
                    "shares": _int_or_none(row.get("Shares")),
                },
                "metadata": {
                    "tags": [],
                    "category": row.get("Type", ""),
                    "word_count": len(text.split()) if text else 0,
                },
            }
            outfile.write(json.dumps(entry) + "\n")
            count += 1

    return count


def _int_or_none(val):
    if val is None or val == "":
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def main():
    parser = argparse.ArgumentParser(description="Parse Facebook export for audit")
    parser.add_argument("export_path", help="Path to Facebook export (ZIP, directory, JSON, or CSV)")
    parser.add_argument("output_dir", help="Output directory")
    args = parser.parse_args()

    if not os.path.exists(args.export_path):
        print(f"File not found: {args.export_path}")
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)
    output_path = os.path.join(args.output_dir, "facebook.jsonl")

    if args.export_path.endswith(".csv"):
        count = parse_csv_export(args.export_path, output_path)
    else:
        count = parse_json_export(args.export_path, output_path)

    print(f"Done. Collected {count} posts → {output_path}")


if __name__ == "__main__":
    main()
