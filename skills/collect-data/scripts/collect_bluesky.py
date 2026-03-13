"""Collect Bluesky account data via public AT Protocol API."""

import argparse
import json
import os
import sys

def main():
    parser = argparse.ArgumentParser(description="Collect Bluesky account data for audit")
    parser.add_argument("handle", help="Bluesky handle (e.g., yourname.bsky.social)")
    parser.add_argument("output_dir", help="Output directory")
    args = parser.parse_args()

    try:
        from atproto import Client
    except ImportError:
        print("atproto not installed. Run: pip install atproto")
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)
    output_path = os.path.join(args.output_dir, "bluesky.jsonl")

    client = Client(base_url="https://public.api.bsky.app")

    # Get profile
    print(f"Fetching profile for {args.handle} ...")
    try:
        profile = client.app.bsky.actor.get_profile({"actor": args.handle})
    except Exception as e:
        print(f"Error fetching profile: {e}")
        sys.exit(1)

    print(f"  {profile.display_name} — {profile.followers_count} followers, {profile.posts_count} posts")

    # Save profile summary
    profile_path = os.path.join(args.output_dir, "bluesky_profile.json")
    with open(profile_path, "w") as f:
        json.dump({
            "handle": profile.handle,
            "display_name": profile.display_name,
            "description": profile.description,
            "followers_count": profile.followers_count,
            "follows_count": profile.follows_count,
            "posts_count": profile.posts_count,
        }, f, indent=2)

    # Fetch all posts
    print("Fetching all posts...")
    all_posts = []
    cursor = None
    while True:
        try:
            resp = client.app.bsky.feed.get_author_feed({
                "actor": args.handle,
                "limit": 100,
                "cursor": cursor,
            })
        except Exception as e:
            print(f"  Warning: error fetching feed page: {e}")
            break

        all_posts.extend(resp.feed)
        print(f"  Fetched {len(all_posts)} posts so far...")

        if not resp.cursor:
            break
        cursor = resp.cursor

    print(f"Found {len(all_posts)} posts. Writing output...")

    count = 0
    with open(output_path, "w") as f:
        for item in all_posts:
            post = item.post

            # Skip reposts (focus on original content)
            if item.reason is not None:
                continue

            entry = {
                "platform": "bluesky",
                "content_type": "post",
                "title": "",
                "url": f"https://bsky.app/profile/{profile.handle}/post/{post.uri.split('/')[-1]}",
                "published_date": getattr(post.record, 'created_at', ''),
                "body_text": getattr(post.record, 'text', ''),
                "metrics": {
                    "views": None,
                    "likes": post.like_count,
                    "comments": post.reply_count,
                    "shares": post.repost_count,
                },
                "metadata": {
                    "tags": [],
                    "category": "",
                    "word_count": len(getattr(post.record, 'text', '').split()),
                    "quote_count": post.quote_count if hasattr(post, 'quote_count') else None,
                },
            }
            f.write(json.dumps(entry) + "\n")
            count += 1

    print(f"Done. Collected {count} original posts → {output_path}")
    print(f"Profile saved → {profile_path}")


if __name__ == "__main__":
    main()
