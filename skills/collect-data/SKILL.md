---
name: collect-data
description: Collect social media and website data for Layer 1 audit. Use when gathering content and metrics from YouTube, Substack, Bluesky, X/Twitter, Facebook, or a website. Handles both automated collection and guided manual export.
compatibility: Requires Python 3.10+, pip. Optional: yt-dlp for YouTube transcripts.
allowed-tools: Bash Read Write AskUserQuestion
---

# Collect Data

Collects content and metrics from a platform for the Layer 1 social media audit. See [docs/layer1-spec.md](../../docs/layer1-spec.md) for full platform details.

## Step 1: Ask what to collect

Ask the user which platform and what data they need:

**Platform:** Website, YouTube, Substack, Bluesky, X/Twitter, or Facebook

**Data type:** Content (text/transcripts), Metrics (engagement/analytics), or Both

**Input:** The URL, handle, or channel name to collect from — OR a file the user has already exported.

## Step 2: Run the appropriate collection

### Website

Automated. No auth needed.

1. Ensure trafilatura is installed: `pip install trafilatura`
2. Run the collection script:
   ```bash
   python skills/collect-data/scripts/collect_website.py <url> <output_dir>
   ```
3. Output: JSONL file with one entry per page (title, date, author, text, url).

### YouTube

Partially automated. Needs a YouTube Data API key for metrics. Transcripts are public.

**For transcripts (no API key needed):**
1. Ensure deps: `pip install youtube-transcript-api google-api-python-client`
2. Run:
   ```bash
   python skills/collect-data/scripts/collect_youtube.py <channel_url_or_id> <output_dir>
   ```
3. If no API key is set, the script collects transcripts only and tells the user what metrics it could not get.

**For metrics (API key needed):**
1. Tell the user: "To get YouTube metrics, you need a YouTube Data API key. Go to console.cloud.google.com, create a project, enable YouTube Data API v3, and create an API key. Then set it as an environment variable: `export YOUTUBE_API_KEY=your_key`"
2. Re-run the script with the key set.

**For richer analytics (owner export):**
1. Tell the user: "For watch time, demographics, and subscriber growth data, export from YouTube Studio: Analytics → Advanced Mode → Export (top right) → CSV. Place the CSV in the output directory."

### Substack

Automated for public data. No auth needed.

1. Run:
   ```bash
   python skills/collect-data/scripts/collect_substack.py <publication_url> <output_dir>
   ```
2. Gets all posts with titles, dates, text, like counts.

**For richer analytics (owner export):**
1. Tell the user: "For subscriber counts, open rates, and per-post views, log in to Substack → Settings → Exports → Export post data CSV. Place the CSV in the output directory."

### Bluesky

Fully automated. No auth needed.

1. Ensure deps: `pip install atproto`
2. Run:
   ```bash
   python skills/collect-data/scripts/collect_bluesky.py <handle> <output_dir>
   ```
3. Gets everything: profile stats, all posts with text, timestamps, and engagement.

### X / Twitter

Manual export. The API costs $100/mo so we default to the user-provided archive.

1. Tell the user: "To get your X/Twitter data, go to Settings → Your Account → Download an archive of your data. This can take 24-48 hours. Once downloaded, provide the path to the ZIP file."
2. When the user provides the ZIP:
   ```bash
   python skills/collect-data/scripts/collect_twitter.py <archive_zip_path> <output_dir>
   ```

### Facebook

Manual export. The API requires page admin access for anything useful.

1. Tell the user: "To get Facebook Page data: log in as a page admin → Meta Business Suite → Insights → Export Data → choose date range → download CSV. For a personal profile: Settings → Your Facebook Information → Download Your Information → select JSON format."
2. When the user provides the file:
   ```bash
   python skills/collect-data/scripts/collect_facebook.py <export_path> <output_dir>
   ```

## Output format

All scripts output JSONL to `<output_dir>/<platform>.jsonl`. Each line:

```json
{
  "platform": "youtube",
  "content_type": "video",
  "title": "...",
  "url": "...",
  "published_date": "2024-03-15T10:30:00Z",
  "body_text": "transcript or post text...",
  "metrics": {"views": 1234, "likes": 42, "comments": 5, "shares": null},
  "metadata": {"tags": [], "category": "", "word_count": 1200, "duration_seconds": 360}
}
```

## Step 3: Confirm results

After collection, report to the user:
- How many items were collected
- Date range covered
- Any gaps or errors (e.g., videos without transcripts, paywalled posts)
- What additional data they could get via manual export (if they haven't already)
