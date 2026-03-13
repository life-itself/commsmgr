# Design: Layer 1 — Data Collection & Audit

This document captures implementation design decisions for Layer 1 of the communications strategy tool, focusing on how data is collected from each platform.

## Data Access Strategy

There are three ways to get data from a platform, and different platforms support different combinations:

1. **Public API / crawl** — tool fetches public data directly, no user action needed
2. **OAuth flow** — user logs in via browser, grants access to richer analytics
3. **Manual export** — user downloads data from the platform and provides the file

We support all three, but **manual export is the primary path** for the initial implementation. It requires no API keys, no OAuth complexity, no rate limits, and no ongoing costs. The tool should always accept user-provided files. API-based collection is a convenience layer on top.

### User flow

```
Tool starts
  → Reads Layer 0 context (org info, platforms list)
  → For each platform, user chooses one of:
      a. Provide exported data file (CSV, JSON, ZIP)
      b. Provide a public URL/handle → tool fetches public data
      c. Connect via OAuth → tool fetches richer analytics
  → Tool normalizes all inputs to a common internal format
  → Proceeds with audit and visualization
```

## Platform-by-Platform Details

### Website

**Best approach:** Public crawl (no auth needed). Gets both content and basic metadata in one pass.

**How to collect (automated):**
1. Install: `pip install trafilatura`
2. Get all page URLs from the sitemap:
   ```bash
   trafilatura --sitemap "https://example.org" --list > urls.txt
   ```
3. If no sitemap exists, crawl by following links:
   ```bash
   trafilatura --crawl "https://example.org" --list > urls.txt
   ```
4. Extract all content with metadata as JSONL:
   ```bash
   trafilatura --json --input-file urls.txt > content.jsonl
   ```
   Each line: `{"title": "...", "author": "...", "date": "2024-03-15", "text": "...", "url": "..."}`

**How to collect (manual export):**
- For engagement data, ask the user to export from Google Analytics (Behavior > Site Content > All Pages, export as CSV).

**What you get:** Full article/page text, titles, dates, authors. No engagement metrics from the crawl itself (pair with analytics export for that).

---

### YouTube

**Best approach:** Public API for metrics + transcripts for content. No video downloads needed.

**How to collect metrics (automated, API key):**
1. Create a Google Cloud project at console.cloud.google.com
2. Enable the YouTube Data API v3
3. Create an API key (no OAuth needed for public data)
4. Get channel info and all video IDs:
   ```python
   from googleapiclient.discovery import build
   youtube = build('youtube', 'v3', developerKey='YOUR_API_KEY')

   # Get channel stats
   channel = youtube.channels().list(part='statistics,snippet', id='CHANNEL_ID').execute()

   # Get all video IDs via uploads playlist (cheap: 1 unit/call)
   # Replace "UC" prefix with "UU" in channel ID to get uploads playlist
   playlist_id = 'UU' + channel_id[2:]
   videos = []
   next_page = None
   while True:
       pl = youtube.playlistItems().list(part='contentDetails', playlistId=playlist_id,
                                          maxResults=50, pageToken=next_page).execute()
       videos.extend([item['contentDetails']['videoId'] for item in pl['items']])
       next_page = pl.get('nextPageToken')
       if not next_page: break

   # Get per-video metrics in batches of 50 (1 unit/call)
   for i in range(0, len(videos), 50):
       batch = ','.join(videos[i:i+50])
       stats = youtube.videos().list(part='statistics,snippet', id=batch).execute()
   ```
5. API quota: 10,000 units/day (free). A 500-video channel costs ~21 units. Very manageable.

**How to collect content (transcripts):**
1. Install: `pip install youtube-transcript-api`
2. For each video ID from step above:
   ```python
   from youtube_transcript_api import YouTubeTranscriptApi
   transcript = YouTubeTranscriptApi.get_transcript(video_id)
   text = " ".join([entry['text'] for entry in transcript])
   ```
3. Alternative via yt-dlp (downloads subtitle files, no video):
   ```bash
   yt-dlp --write-auto-sub --sub-lang en --skip-download \
     -o "%(upload_date)s_%(title)s.%(ext)s" \
     "https://www.youtube.com/@channelname"
   ```
4. Video titles, descriptions, and tags are also valuable content signals — these come from the API in step 4 above.

**How to collect (manual export, for richer analytics):**
1. Go to YouTube Studio → Analytics → Advanced Mode
2. Click "Export" (top right) → choose CSV
3. This gives watch time, impressions, CTR, traffic sources, subscriber changes — data not available via the public API
4. Alternatively, use Google Takeout (takeout.google.com) to export all channel data

**What you get:**
- *Public API:* video list, titles, descriptions, tags, publish dates, view/like/comment counts, subscriber count
- *Transcripts:* full text of what was said in each video (a few KB each)
- *Owner export:* watch time, demographics, traffic sources, subscriber growth over time

---

### Substack

**Best approach:** Undocumented public API for metrics + content, supplemented by owner CSV export for analytics.

**How to collect (automated, no auth):**
1. Get all posts with metadata by paginating the archive endpoint:
   ```python
   import requests, json

   publication_url = "https://yourpublication.substack.com"
   posts = []
   offset = 0
   while True:
       resp = requests.get(f"{publication_url}/api/v1/archive",
                           params={"sort": "new", "offset": offset, "limit": 50})
       batch = resp.json()
       if not batch: break
       posts.extend(batch)
       offset += len(batch)
   ```
   Each post includes: `title`, `subtitle`, `slug`, `post_date`, `canonical_url`, `word_count`, `reaction_count`, `audience` (free/paid).

2. Get full content and comment count for each post:
   ```python
   for post in posts:
       detail = requests.get(f"{publication_url}/api/v1/posts/{post['slug']}").json()
       # detail['body_html'] has the full post content (free posts only)
       # detail['comment_count'] has the comment count
   ```

3. Alternatively, get recent posts with full content via RSS:
   ```python
   import feedparser
   feed = feedparser.parse(f"{publication_url}/feed")
   # feed.entries has ~20-30 most recent posts with full HTML content
   ```
   RSS is not sufficient for a full audit (limited to recent posts) but useful as a supplement.

**How to collect (manual export, for richer analytics):**
1. Log in to Substack dashboard
2. Go to Settings → Exports
3. Export post data CSV — includes per-post views, reads, open rates
4. Export subscriber list CSV — includes subscriber count, dates, types
5. Place these files in the tool's input directory

**What you get:**
- *Public API:* all post titles, dates, full text (free posts), like counts, comment counts
- *Owner export:* subscriber count/growth, email open rates, per-post views, revenue

---

### Bluesky

**Best approach:** Public API — gets everything (metrics, content, engagement) in one pass, no auth needed.

**How to collect (automated, no auth):**
1. Install: `pip install atproto`
2. Get profile stats and full post history:
   ```python
   from atproto import Client

   client = Client(base_url='https://public.api.bsky.app')

   # Profile stats
   profile = client.app.bsky.actor.get_profile({'actor': 'yourhandle.bsky.social'})
   print(profile.followers_count, profile.posts_count)

   # All posts with engagement metrics
   all_posts = []
   cursor = None
   while True:
       resp = client.app.bsky.feed.get_author_feed({
           'actor': 'yourhandle.bsky.social',
           'limit': 100,
           'cursor': cursor,
       })
       all_posts.extend(resp.feed)
       if not resp.cursor: break
       cursor = resp.cursor

   # Each post has: text, timestamp, like_count, repost_count, reply_count
   for item in all_posts:
       p = item.post
       print(p.record.created_at, p.record.text, p.like_count, p.repost_count)
   ```
3. Rate limits: ~300 requests/5min unauthenticated, ~3,000/5min authenticated. For most org accounts, unauthenticated is fine.

**How to collect (manual export):**
- Not usually needed since everything is public. But the user can export their data via Bluesky settings if preferred.

**What you get:** Everything — profile stats, full post text, timestamps, and per-post engagement (likes, reposts, replies, quotes). All in one API call sequence.

---

### X / Twitter

**Best approach:** Manual export (user provides their Twitter archive). The API is too expensive for most use cases ($100/mo minimum for read access).

**How to collect (manual export — recommended):**
1. Log in to X/Twitter
2. Go to Settings → Your Account → Download an archive of your data
3. Confirm identity (may require email/phone verification)
4. Wait for the archive to be prepared (can take 24-48 hours; X sends a notification when ready)
5. Download the ZIP file
6. The archive contains `data/tweets.js` (or `data/tweet.js`) with all tweets as JSON:
   - Full tweet text
   - Timestamps
   - Engagement metrics (impressions, likes, retweets, replies)
   - Media URLs
   - Reply/thread relationships
7. Place the ZIP in the tool's input directory

**How to collect (API — if budget allows, $100/mo):**
1. Apply for a Basic developer account at developer.x.com ($100/mo)
2. Create an app and get a Bearer Token
3. Install: `pip install tweepy`
4. Fetch profile and tweets:
   ```python
   import tweepy
   client = tweepy.Client(bearer_token="YOUR_BEARER_TOKEN")

   # Profile stats
   user = client.get_user(username="targetuser",
                          user_fields=["public_metrics", "description"])
   print(user.data.public_metrics)  # followers, tweet count, etc.

   # Recent tweets with engagement
   tweets = client.get_users_tweets(user.data.id,
                                     tweet_fields=["public_metrics", "created_at"],
                                     max_results=100)
   ```
5. Limitations: 10,000 tweet reads/month, recent search limited to 7 days.

**What you get:**
- *Archive export:* complete history of all tweets, with text and engagement — the most complete source
- *API:* real-time profile stats and recent tweets, but limited volume and expensive

---

### Facebook

**Best approach:** Manual export. The Facebook API requires admin access to the page for almost everything useful — you cannot audit arbitrary public pages.

**How to collect (manual export — recommended):**

*For Facebook Pages (organizations):*
1. Log in as a page admin
2. Go to Meta Business Suite → Insights
3. Click "Export Data" (top right)
4. Choose date range (up to 2 years per export; repeat for older data)
5. Select "Post data" export — includes: post text, reach, engagement, clicks
6. Select "Page data" export — includes: follower growth, page views
7. Download as CSV
8. Place files in the tool's input directory

*For personal profiles:*
1. Go to Facebook Settings → Your Facebook Information → Download Your Information
2. Select format: JSON (easier to parse) or HTML
3. Select date range and categories (at minimum: Posts)
4. Download and place in input directory

**How to collect (API — requires page admin):**
1. Create a Meta developer app at developers.facebook.com
2. Go through App Review to get `pages_read_engagement` permission
3. Generate a Page Access Token (requires admin of the target page)
4. Install: `pip install facebook-sdk`
5. This path is complex and only viable if building a hosted service where page owners connect their accounts via OAuth

**What you get:**
- *Manual export:* post text, reach, engagement, follower growth — sufficient for audit
- *API:* same data but automated — only practical if the page owner connects via OAuth

---

## Content Acquisition

The audit and brand layers need actual *content* (what was said), not just metrics. The key insight is that **text is lightweight** — even a prolific organization's entire written output across all platforms is likely under 100MB of plain text.

### What content to collect per platform

| Platform | Content to collect | Format | How |
|----------|--------------------|--------|-----|
| **Website** | Full article/page text | Already handled by trafilatura | Same crawl as metrics |
| **YouTube** | **Transcripts only** (not video files) | SRT/VTT subtitle files → plain text | `yt-dlp --write-auto-sub --sub-lang en --skip-download` |
| **Substack** | Full post text (free posts) | HTML → plain text | Undocumented API returns body HTML; RSS has full content |
| **Bluesky** | Post text | Plain text | Already in `getAuthorFeed` response |
| **X/Twitter** | Tweet text | Plain text | In the archive ZIP (`tweets.js`) |
| **Facebook** | Post text | Plain text | In the export or Page Insights CSV |

### YouTube: transcripts not videos

Downloading actual video files is unnecessary and impractical (hundreds of GB). What the audit needs is **what was said** — the narrative, messaging, and topics. YouTube auto-generates captions for most videos, and manually uploaded captions are even better.

**Getting transcripts with yt-dlp:**
```bash
# Download auto-generated English subtitles for all videos on a channel, no video
yt-dlp --write-auto-sub --sub-lang en --skip-download \
  -o "%(upload_date)s_%(title)s.%(ext)s" \
  "https://www.youtube.com/@channelname"
```

This produces `.vtt` or `.srt` files (a few KB each) that can be converted to plain text by stripping timestamps.

**Alternative: YouTube transcript API.** The `youtube-transcript-api` Python package (`pip install youtube-transcript-api`) fetches transcripts directly without yt-dlp:
```python
from youtube_transcript_api import YouTubeTranscriptApi
transcript = YouTubeTranscriptApi.get_transcript("VIDEO_ID")
text = " ".join([entry['text'] for entry in transcript])
```

**What if no transcript exists?** Some videos may lack auto-captions (e.g., music-only, very short). The tool should flag these but not block on them. For a typical org channel, the vast majority of talking-head or presentation videos will have auto-captions.

**Video metadata is also content.** Titles, descriptions, and tags are often rich signals of messaging and themes — these come from the Data API and don't require transcripts.

### X/Twitter: the archive is the best source

The Twitter archive ZIP contains a `tweets.js` file (or `data/tweets.js`) with every tweet the account has ever posted, including:
- Full tweet text
- Timestamps
- Engagement metrics (impressions, likes, retweets, replies)
- Media URLs (images, but we don't need to download them)
- Reply/thread relationships

This is far more complete than what the API provides (which is limited to recent tweets at affordable tiers).

### Substack: full text is freely available

For free posts, the undocumented API returns the full HTML body. For paywalled posts, only the preview is available publicly — the owner would need to provide an export. Substack's export (Settings > Exports) includes all post content.

### Content we do NOT need to collect

- **Images and visual media** — not needed for text-based content analysis. Image URLs can be stored as references if needed later.
- **Video files** — transcripts are sufficient.
- **Comments/replies from others** — useful for engagement analysis but not for understanding the org's own brand and messaging. Collect counts; skip full comment text in the first pass.
- **Reshares/reposts of others' content** — can be filtered out to focus on original content.

### Content storage

All content is stored as plain text in the common internal format (see below). The `body_text` field holds the content. For YouTube, this is the transcript. For all other platforms, this is the post/article text.

Total expected size for a typical organization (5 years of content across all platforms): **10-50MB of plain text**. This is small enough to process entirely in memory or pass to an LLM for analysis.

## Common Internal Data Format

All platform data should be normalized to a common format for analysis. Proposed schema:

```json
{
  "platform": "youtube|substack|bluesky|twitter|facebook|website",
  "content_type": "post|video|article|page",
  "title": "...",
  "url": "...",
  "published_date": "2024-03-15T10:30:00Z",
  "body_text": "...",
  "metrics": {
    "views": null,
    "likes": 42,
    "comments": 5,
    "shares": 3,
    "subscribers_at_time": null
  },
  "metadata": {
    "tags": [],
    "category": "...",
    "word_count": 1200,
    "duration_seconds": null
  }
}
```

Not all fields will be populated for every platform — `views` isn't available for Bluesky, `duration_seconds` only applies to YouTube, etc. The analysis layer handles missing fields gracefully.

## Summary: Implementation Priority

| Priority | Platform | Method | Cost | Difficulty |
|----------|----------|--------|------|------------|
| 1 | Website | trafilatura crawl | Free | Easy |
| 2 | Bluesky | Public AT Protocol API | Free | Easy |
| 3 | YouTube | API key (public data) | Free | Easy |
| 4 | Substack | Undocumented API + RSS | Free | Easy |
| 5 | X/Twitter | User-provided archive ZIP | Free | Medium (parsing) |
| 6 | Facebook | User-provided CSV export | Free | Medium (parsing) |

The first four platforms can be fully automated with no user credentials and no cost. X and Facebook are best handled via user-provided exports.
