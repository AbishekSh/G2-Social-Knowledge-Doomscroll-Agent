# doomscroll-agent

A practical Python agent for monitoring public social content, storing timestamped snapshots, and generating one actionable trend insight per run.

This project is implemented as a Reddit-first pipeline with a TikTok collector module for future expansion. That keeps the current path reliable while still supporting a broader social-monitoring design.

## Project objective

`doomscroll-agent` monitors a configurable public niche such as AI tools, productivity, or news, then:

- collects public post data from configured URLs
- parses titles/captions, handles, hashtags, visible comments, and engagement metadata
- optionally enriches items with transcript text when available
- classifies topic and sentiment
- stores raw and processed snapshots as JSON
- aggregates recurring themes into one actionable insight

The design is intentionally simple, reproducible, and n8n-ready.

## Why Reddit was chosen

I chose Reddit as the primary implementation because it provides public, discussion-rich content that is much more reliable to collect and parse for a first version. Subreddit listings and post pages are a good fit for extracting titles, comment signals, sentiment, and recurring themes without relying on login state or fragile private APIs.

TikTok was still relevant to the broader problem, so I kept a Playwright-based collector module in the repo as an extension path. In practice, public TikTok extraction was much less reliable because of anti-scraping protections and frequent selector/rendering changes.

Current implementation notes:

- Reddit is the dependable end-to-end implementation
- TikTok is included as a future expansion path, not as the primary shipped workflow

## What is collected

Phase 1 data extraction:

- source URL
- post URL
- caption or title text
- creator handle if visible
- hashtags from visible text
- visible top comments
- collected timestamp
- likes / comment count / shares when visible

Phase 2 enhancement:

- transcript text if available from page content
- if no transcript exists, the pipeline continues normally

## Architecture

```text
TARGET_URLS
  -> Collector (Reddit, TikTok extension path)
  -> Parser
  -> Optional Transcript Layer
  -> Analyzer (heuristic or LLM)
  -> JSON Storage
  -> Trend Aggregator
  -> latest_insight.json
```

Key modules:

- `src/reddit_collector.py`: public Reddit listing collector with post-detail comment enrichment
- `src/collector.py`: TikTok Playwright collector module with centralized selectors
- `src/parser.py`: platform-agnostic normalization into one processed item shape
- `src/analyzer.py`: heuristic topic, sentiment, keyword, and signal tag extraction
- `src/trends.py`: snapshot aggregation and actionable insight generation
- `src/storage.py`: writes `data/raw`, `data/processed`, and `data/insights`
- `src/run_pipeline.py`: one-shot and loop CLI entrypoint

## Setup

Requirements:

- Python 3.11+
- Playwright Chromium

Install:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
cp .env.example .env
```

## Example .env

```env
TARGET_PLATFORM=reddit
TARGET_URLS=https://www.reddit.com/r/artificial/,https://www.reddit.com/r/MachineLearning/
MAX_VIDEOS_PER_RUN=6
MAX_COMMENTS_PER_VIDEO=4
ANALYSIS_MODE=heuristic
LLM_BASE_URL=
LLM_API_KEY=
LLM_MODEL=gpt-4o-mini
ENABLE_TRANSCRIPT=false
POLL_INTERVAL_SECONDS=120
OUTPUT_DIR=./data
PLAYWRIGHT_HEADLESS=true
NICHE=ai_tools
```

## How to run locally

One-shot run:

```bash
python3 -m src.run_pipeline --once
```

Loop mode:

```bash
python3 -m src.run_pipeline --loop
```

Expected CLI output includes:

- files written
- number of items processed
- final actionable insight

## How to run on Linux

The runtime target is Linux. On a Linux host or container:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
cp .env.example .env
python3 -m src.run_pipeline --once
```

## How to use it with n8n

Recommended minimal workflow:

1. Add a `Schedule Trigger` node.
2. Add an `Execute Command` node:

```bash
cd /workspace/doomscroll-agent
python3 -m src.run_pipeline --once
```

3. Add a file-read node pointed at:

```text
/workspace/doomscroll-agent/data/insights/latest_insight.json
```

4. Forward the JSON to Slack, email, Sheets, or a webhook.

Why this is n8n-ready:

- the collector is not tightly coupled to orchestration
- `--once` is deterministic and easy to schedule
- `latest_insight.json` gives n8n one canonical output artifact
- the same pipeline can be triggered locally, by cron, or by n8n without code changes

## Sample output JSON

Processed item example:

```json
{
  "platform": "reddit",
  "source_url": "https://www.reddit.com/r/artificial/",
  "video_url": "https://www.reddit.com/r/artificial/comments/example/post_slug/",
  "creator_handle": "u/example_user",
  "caption": "Local AI coding tools are getting good enough for offline workflows",
  "hashtags": [],
  "comments": [
    "This is the first setup I've seen that feels practical for daily work.",
    "Offline privacy is the real selling point here."
  ],
  "transcript": null,
  "video_summary": "Local AI coding tools are getting good enough for offline workflows. Creator signal: u/example_user.",
  "topic": "local_llms",
  "sentiment": "positive",
  "keywords": ["offline", "privacy", "practical"],
  "signal_tags": ["offline", "privacy", "practical", "local_llms"],
  "collected_at": "2026-04-07T20:00:00Z"
}
```

Aggregate insight example:

```json
{
  "generated_at": "2026-04-07T20:00:00Z",
  "headline": "Top trend: local_llms",
  "actionable_insight": "Current coverage is led by local llms. Recurring signals include offline, privacy, practical and no dominant hashtags yet, with positive sentiment overall. Actionable insight: use this theme as the next monitoring or content priority.",
  "topic_summary": [
    { "topic": "local_llms", "count": 3 },
    { "topic": "ai_coding_tools", "count": 2 }
  ]
}
```

## Example actionable insight

“Discussion around local AI tooling is clustering around offline workflows and privacy benefits. Actionable insight: prioritize monitoring and content experiments around self-hosted developer tools.”

## Tests

Focused tests cover:

- hashtag extraction and metric parsing
- parser output shape
- analyzer output shape
- trend aggregation
- storage writes
- deduplication behavior

Run them with:

```bash
python3 -m pytest -q
```

## Limitations

- Reddit is the primary supported path today; TikTok is still an extension path rather than a completed extraction path.
- Public website structure can change and may require selector updates.
- The analyzer uses lightweight heuristics by default and is intentionally explainable rather than sophisticated.
- JSON files are simple and easy to inspect, but a database would be a better long-term store.

## Compliance note

This project targets public content only.

It does not attempt:

- login bypass
- CAPTCHA bypass
- session reuse or session theft
- scraping private or protected content
