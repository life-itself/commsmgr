"""Parse a Twitter/X archive ZIP into the common JSONL format."""

import argparse
import json
import os
import sys
import zipfile

def main():
    parser = argparse.ArgumentParser(description="Parse Twitter/X archive for audit")
    parser.add_argument("archive_path", help="Path to Twitter archive ZIP file")
    parser.add_argument("output_dir", help="Output directory")
    args = parser.parse_args()

    if not os.path.exists(args.archive_path):
        print(f"File not found: {args.archive_path}")
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)
    output_path = os.path.join(args.output_dir, "twitter.jsonl")

    # Find the tweets file inside the ZIP
    tweets_data = None
    tweets_filename = None

    with zipfile.ZipFile(args.archive_path, "r") as zf:
        # Look for common tweet file locations
        candidates = [
            "data/tweets.js",
            "data/tweet.js",
            "tweets.js",
            "tweet.js",
        ]

        for candidate in candidates:
            if candidate in zf.namelist():
                tweets_filename = candidate
                break

        if not tweets_filename:
            # Search for any file containing "tweet" in the name
            for name in zf.namelist():
                if "tweet" in name.lower() and name.endswith(".js"):
                    tweets_filename = name
                    break

        if not tweets_filename:
            print("Could not find tweets data in archive. Files in ZIP:")
            for name in sorted(zf.namelist())[:30]:
                print(f"  {name}")
            sys.exit(1)

        print(f"Found tweets at: {tweets_filename}")
        raw = zf.read(tweets_filename).decode("utf-8")

    # Twitter archive JS files start with a variable assignment like:
    # window.YTD.tweets.part0 = [ ... ]
    # Strip that prefix to get valid JSON
    json_start = raw.find("[")
    if json_start == -1:
        print("Could not parse tweets file — no JSON array found")
        sys.exit(1)

    tweets_data = json.loads(raw[json_start:])
    print(f"Found {len(tweets_data)} tweets")

    count = 0
    with open(output_path, "w") as f:
        for item in tweets_data:
            tweet = item.get("tweet", item)  # Handle both wrapper formats

            # Extract metrics
            metrics = {
                "views": None,
                "likes": int(tweet.get("favorite_count", 0)),
                "comments": int(tweet.get("reply_count", 0)) if "reply_count" in tweet else None,
                "shares": int(tweet.get("retweet_count", 0)),
            }

            # Check for impression count in newer archives
            if "impression_count" in tweet:
                metrics["views"] = int(tweet["impression_count"])

            entry = {
                "platform": "twitter",
                "content_type": "post",
                "title": "",
                "url": f"https://x.com/i/status/{tweet.get('id_str', tweet.get('id', ''))}",
                "published_date": tweet.get("created_at", ""),
                "body_text": tweet.get("full_text", tweet.get("text", "")),
                "metrics": metrics,
                "metadata": {
                    "tags": [ht["text"] for ht in tweet.get("entities", {}).get("hashtags", [])],
                    "category": "",
                    "word_count": len(tweet.get("full_text", tweet.get("text", "")).split()),
                    "in_reply_to": tweet.get("in_reply_to_screen_name", ""),
                    "is_retweet": tweet.get("full_text", "").startswith("RT @"),
                },
            }
            f.write(json.dumps(entry) + "\n")
            count += 1

    print(f"Done. Collected {count} tweets → {output_path}")

    # Count retweets vs original
    with open(output_path) as f:
        lines = f.readlines()
        rts = sum(1 for l in lines if json.loads(l)["metadata"]["is_retweet"])
        print(f"  Original tweets: {count - rts}")
        print(f"  Retweets: {rts}")


if __name__ == "__main__":
    main()
