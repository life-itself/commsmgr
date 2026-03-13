"""Collect YouTube channel data: metrics via Data API, transcripts via youtube-transcript-api."""

import argparse
import json
import os
import re
import sys

def get_channel_id(youtube, channel_input):
    """Resolve a channel URL or name to a channel ID."""
    # Already a channel ID
    if channel_input.startswith("UC") and len(channel_input) == 24:
        return channel_input

    # Extract from URL patterns
    patterns = [
        r'youtube\.com/channel/(UC[\w-]+)',
        r'youtube\.com/@([\w.-]+)',
        r'youtube\.com/c/([\w.-]+)',
        r'youtube\.com/user/([\w.-]+)',
    ]
    handle = None
    for pattern in patterns:
        match = re.search(pattern, channel_input)
        if match:
            handle = match.group(1)
            if handle.startswith("UC"):
                return handle
            break

    if not handle:
        handle = channel_input.lstrip("@")

    # Search for the channel
    if handle.startswith("UC"):
        return handle

    # Try forHandle first
    resp = youtube.channels().list(part="id", forHandle=handle).execute()
    if resp.get("items"):
        return resp["items"][0]["id"]

    # Fallback to search
    resp = youtube.search().list(part="id", q=handle, type="channel", maxResults=1).execute()
    if resp.get("items"):
        return resp["items"][0]["id"]["channelId"]

    return None


def main():
    parser = argparse.ArgumentParser(description="Collect YouTube channel data for audit")
    parser.add_argument("channel", help="Channel URL, @handle, or channel ID")
    parser.add_argument("output_dir", help="Output directory")
    parser.add_argument("--transcripts-only", action="store_true",
                        help="Only collect transcripts (no API key needed)")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    output_path = os.path.join(args.output_dir, "youtube.jsonl")

    api_key = os.environ.get("YOUTUBE_API_KEY")
    has_api = bool(api_key) and not args.transcripts_only

    if has_api:
        try:
            from googleapiclient.discovery import build
            youtube = build("youtube", "v3", developerKey=api_key)
        except ImportError:
            print("google-api-python-client not installed. Run: pip install google-api-python-client")
            sys.exit(1)
    else:
        if not args.transcripts_only:
            print("No YOUTUBE_API_KEY set. Will collect transcripts only.")
            print("For metrics, set: export YOUTUBE_API_KEY=your_key")
            print("Get a key at: console.cloud.google.com → enable YouTube Data API v3 → create API key")
            print()
        youtube = None

    # Try to import transcript API
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        has_transcripts = True
    except ImportError:
        print("youtube-transcript-api not installed. Run: pip install youtube-transcript-api")
        print("Transcripts will be skipped.")
        has_transcripts = False

    video_ids = []
    video_data = {}  # id -> metadata dict

    if has_api:
        # Get channel info
        channel_id = get_channel_id(youtube, args.channel)
        if not channel_id:
            print(f"Could not find channel: {args.channel}")
            sys.exit(1)

        print(f"Fetching channel info for {channel_id} ...")
        ch_resp = youtube.channels().list(part="snippet,statistics", id=channel_id).execute()
        if not ch_resp.get("items"):
            print(f"Channel not found: {channel_id}")
            sys.exit(1)

        ch = ch_resp["items"][0]
        print(f"  {ch['snippet']['title']} — {ch['statistics'].get('subscriberCount', '?')} subscribers")

        # Save channel profile
        profile_path = os.path.join(args.output_dir, "youtube_profile.json")
        with open(profile_path, "w") as f:
            json.dump({
                "channel_id": channel_id,
                "title": ch["snippet"]["title"],
                "description": ch["snippet"]["description"],
                "subscriber_count": int(ch["statistics"].get("subscriberCount", 0)),
                "total_views": int(ch["statistics"].get("viewCount", 0)),
                "video_count": int(ch["statistics"].get("videoCount", 0)),
            }, f, indent=2)

        # Get all video IDs via uploads playlist
        uploads_id = "UU" + channel_id[2:]
        print("Fetching video list...")
        next_page = None
        while True:
            pl_resp = youtube.playlistItems().list(
                part="contentDetails,snippet",
                playlistId=uploads_id,
                maxResults=50,
                pageToken=next_page,
            ).execute()

            for item in pl_resp["items"]:
                vid = item["contentDetails"]["videoId"]
                video_ids.append(vid)
                video_data[vid] = {
                    "title": item["snippet"]["title"],
                    "published_date": item["snippet"]["publishedAt"],
                    "description": item["snippet"].get("description", ""),
                }

            next_page = pl_resp.get("nextPageToken")
            if not next_page:
                break
            print(f"  Found {len(video_ids)} videos so far...")

        # Get per-video metrics in batches of 50
        print("Fetching video metrics...")
        for i in range(0, len(video_ids), 50):
            batch = video_ids[i:i+50]
            v_resp = youtube.videos().list(
                part="statistics,contentDetails",
                id=",".join(batch),
            ).execute()

            for item in v_resp.get("items", []):
                vid = item["id"]
                stats = item.get("statistics", {})
                video_data[vid]["metrics"] = {
                    "views": int(stats.get("viewCount", 0)),
                    "likes": int(stats.get("likeCount", 0)),
                    "comments": int(stats.get("commentCount", 0)),
                    "shares": None,
                }
                # Parse duration
                duration_str = item.get("contentDetails", {}).get("duration", "")
                video_data[vid]["duration"] = duration_str
    else:
        # No API — user needs to provide video IDs or we skip metrics
        print("No API key available. Provide video IDs or URLs to collect transcripts.")
        print("Attempting to extract channel info from URL...")

        # Try to get video IDs using yt-dlp if available
        try:
            import subprocess
            result = subprocess.run(
                ["yt-dlp", "--flat-playlist", "--print", "id", args.channel],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode == 0:
                video_ids = [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]
                print(f"Found {len(video_ids)} videos via yt-dlp")
            else:
                print(f"yt-dlp failed: {result.stderr[:200]}")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            print("yt-dlp not available. Cannot list videos without API key.")
            if not has_transcripts:
                sys.exit(1)

    # Collect transcripts
    print(f"\nCollecting transcripts for {len(video_ids)} videos...")
    transcript_count = 0
    no_transcript = []

    count = 0
    with open(output_path, "w") as f:
        for i, vid in enumerate(video_ids):
            data = video_data.get(vid, {})
            body_text = ""

            if has_transcripts:
                try:
                    transcript = YouTubeTranscriptApi.get_transcript(vid)
                    body_text = " ".join(entry["text"] for entry in transcript)
                    transcript_count += 1
                except Exception:
                    no_transcript.append(vid)

            entry = {
                "platform": "youtube",
                "content_type": "video",
                "title": data.get("title", ""),
                "url": f"https://www.youtube.com/watch?v={vid}",
                "published_date": data.get("published_date", ""),
                "body_text": body_text,
                "metrics": data.get("metrics", {
                    "views": None, "likes": None, "comments": None, "shares": None,
                }),
                "metadata": {
                    "tags": [],
                    "category": "",
                    "word_count": len(body_text.split()) if body_text else 0,
                    "duration": data.get("duration", ""),
                    "description": data.get("description", ""),
                },
            }
            f.write(json.dumps(entry) + "\n")
            count += 1

            if (i + 1) % 20 == 0:
                print(f"  Processed {i + 1}/{len(video_ids)} videos...")

    print(f"\nDone. Collected {count} videos → {output_path}")
    print(f"  Transcripts: {transcript_count}/{len(video_ids)}")
    if no_transcript:
        print(f"  No transcript available for {len(no_transcript)} videos")

    if not has_api:
        print(f"\nFor richer data, set YOUTUBE_API_KEY and re-run.")
        print(f"For watch time/demographics, export CSV from YouTube Studio → Analytics → Advanced Mode → Export")


if __name__ == "__main__":
    main()
