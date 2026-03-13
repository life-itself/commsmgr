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

**Best approach:** Public crawl (no auth needed).

**Tools:**
- **trafilatura** (Python, `pip install trafilatura`) — the standout tool. Handles sitemap discovery, crawling, and structured content extraction (title, date, author, body text) in one package.
- Sitemap-based discovery is the primary method; spider/crawl mode as fallback.

**Data available:**
- All page/post content, titles, dates, authors
- No engagement metrics (unless the site has public comment counts)

**Simplest flow:**
```bash
# Get all URLs from sitemap
trafilatura --sitemap "https://example.org" --list > urls.txt

# Extract content with metadata as JSONL
trafilatura --json --input-file urls.txt > content.jsonl
```

Each line of output: `{"title": "...", "author": "...", "date": "2024-03-15", "text": "...", "url": "..."}`

**Fallbacks:**
- No sitemap → use `trafilatura --crawl` (spider mode)
- Historical snapshots → Wayback Machine CDX API (`waybackpy` Python library)

**Manual export alternative:** User could provide a Google Analytics export for engagement data.

---

### YouTube

**Best approach:** Public API with API key (free), supplemented by owner export.

**Public data (API key only, no owner login):**
- Channel info: name, description, subscriber count, total views, video count
- All public videos: title, description, tags, publish date, duration
- Per-video metrics: view count, like count, comment count
- Comments on videos

**Owner-only data (requires OAuth or export):**
- Watch time, average view duration
- Traffic sources, demographics, audience retention
- Subscriber gain/loss over time (daily granularity)
- Impressions and click-through rate
- Revenue data

**Tools:**
- `google-api-python-client` — official Google Python client
- `python-youtube` — simpler wrapper
- `yt-dlp` — can extract metadata without using API quota (`yt-dlp --flat-playlist --dump-json`)

**API quota:** 10,000 units/day (free). A channel with 500 videos costs ~21 units to audit. Very manageable.

**Key technique:** Use `playlistItems.list` on the uploads playlist (channel ID with "UC" → "UU") instead of `search.list` — costs 1 unit vs 100 units per call.

**Manual export alternative:** YouTube Studio exports analytics as CSV. Google Takeout exports full channel data.

**OAuth flow:** Uses `google-auth-oauthlib`. Opens browser, user clicks "Allow", token cached locally. Standard Google OAuth.

---

### Substack

**Best approach:** Undocumented public API + owner CSV export.

**Public data (no auth):**
- All posts: titles, dates, slugs, URLs, word count, audience type (free/paid)
- Like/reaction counts per post
- Comment counts (via per-post endpoint)
- Full content of free posts (via RSS or API)

**Owner-only data (requires dashboard CSV export):**
- Subscriber count and growth
- Email open rates and click rates
- Per-post views and read counts
- Revenue data
- Traffic source data

**No official API.** But stable undocumented endpoints exist:
```
GET https://<publication>.substack.com/api/v1/archive?sort=new&offset=0&limit=50
```
Returns JSON with post metadata. Paginate with `offset`.

**RSS feed** at `https://<publication>.substack.com/feed` — gives recent ~20-30 posts with full content. Not sufficient for full audit.

**Tools:**
- `substack-api` (PyPI) — community Python wrapper
- `feedparser` — for RSS
- Simple `requests` + JSON is often enough given the straightforward API

**Manual export alternative:** Owner exports analytics CSV from Settings > Exports in Substack dashboard. This is the richest data source.

---

### Bluesky

**Best approach:** Public API (no auth needed for public data).

**Public data (no auth via `public.api.bsky.app`):**
- Profile: display name, handle, followers count, follows count, posts count
- Full post history with pagination
- Per-post engagement: like count, repost count, reply count, quote count
- Followers/following lists

**All useful audit data is public.** No OAuth needed unless you want higher rate limits.

**Tools:**
- `atproto` Python SDK (`pip install atproto`) — full AT Protocol support
- Public API base URL: `https://public.api.bsky.app/xrpc/`

**Key endpoints:**
- `app.bsky.actor.getProfile` — profile stats
- `app.bsky.feed.getAuthorFeed` — paginated post history with engagement
- `app.bsky.feed.getPosts` — specific posts with full metrics

**Rate limits:** ~300 requests/5min unauthenticated, ~3,000/5min authenticated. For authenticated access, user provides an App Password (not main password).

**Manual export alternative:** Not really needed since everything is public, but user could provide an AT Protocol data export.

---

### X / Twitter

**Best approach:** Manual export (user provides their Twitter archive).

**The problem:** X API is expensive.
- Free tier: write-only, useless for audit
- Basic tier: $100/month — gives 10,000 tweet reads/month
- Pro tier: $5,000/month

**If using the API (Basic tier, $100/mo):**
- Public profile: followers, following, tweet count
- Public tweets with engagement (likes, retweets, replies)
- Recent search (7 days only)
- Library: `tweepy` (`pip install tweepy`)

**Alternative approaches:**
- **snscrape**: broken since mid-2023
- **Nitter**: largely dead
- **Apify scrapers**: work but cost money and are ToS-grey

**Manual export (recommended primary path):**
- User requests their Twitter archive: Settings → Your Account → Download an archive of your data
- Produces a ZIP containing all tweets as JSON, with engagement metrics
- This is free, complete, and reliable

---

### Facebook

**Best approach:** Manual export (user provides Page Insights CSV).

**The problem:** Facebook Graph API requires admin access to the target page for almost everything useful. You cannot audit arbitrary public pages.

**With admin access (page owner connects via OAuth):**
- Page followers/fans
- All posts with engagement
- Page Insights analytics
- Requires app review + `pages_read_engagement` permission

**Without admin access:**
- Basic page name, ID, category only
- No posts, no engagement, no follower count

**Manual export (recommended primary path):**
- Page admin exports Insights from Meta Business Suite (CSV)
- Contains: post performance, reach, engagement, follower growth
- Or use the "Download your information" tool for personal profiles

**Tools:** `facebook-sdk` or `pyfacebook` (Python), but only useful if you have admin tokens.

---

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
