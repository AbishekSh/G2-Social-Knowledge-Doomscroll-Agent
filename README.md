# doomscroll-agent

A practical Python agent for monitoring public social content, storing timestamped snapshots, and generating one actionable trend insight per run.

This submission is implemented as a Reddit-first MVP with a TikTok collector scaffold for future expansion. That keeps the shipped path reliable while still demonstrating a broader social-monitoring design.

## Project objective

`doomscroll-agent` monitors a configurable public niche such as AI tools, productivity, or news, then:

- collects public post data from configured URLs
- parses titles/captions, handles, hashtags, visible comments, and engagement metadata
- optionally enriches items with transcript text when available
- classifies topic and sentiment
- stores raw and processed snapshots as JSON
- aggregates recurring themes into one actionable insight

The design is intentionally simple, reproducible, and n8n-ready.

## Why TikTok was chosen

TikTok is a strong fit for trend discovery because creator-driven short-form content tends to surface new workflows, products, and public sentiment quickly. In practice, public TikTok extraction is much more brittle than Reddit because rendering and selectors change often, so this repo ships with:

- a Reddit implementation that is stable enough for a demo
- a TikTok collector scaffold that keeps selectors isolated and non-blocking

That tradeoff keeps the submission honest: the architecture supports both, but the dependable demo path is Reddit.

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
  -> Collector (Reddit today, TikTok scaffold)
  -> Parser
  -> Optional Transcript Layer
  -> Analyzer (heuristic or LLM)
  -> JSON Storage
  -> Trend Aggregator
  -> latest_insight.json
```

Key modules:

- `src/reddit_collector.py`: public Reddit listing collector with post-detail comment enrichment
- `src/collector.py`: TikTok Playwright scaffold with centralized selectors
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

- Reddit is the reliable demo path today; TikTok is still a scaffold rather than a completed extraction path.
- Public website structure can change and may require selector updates.
- The analyzer uses lightweight heuristics by default and is intentionally explainable rather than sophisticated.
- JSON files are simple and demo-friendly, but a database would be a better long-term store.

## Compliance note

This project targets public content only.

It does not attempt:

- login bypass
- CAPTCHA bypass
- session reuse or session theft
- scraping private or protected content

## How to explain this in the interview

“This is a public-content trend monitoring agent built as a practical MVP. I used Playwright for collection, JSON snapshots for memory, heuristic analysis for explainable topic and sentiment tagging, and a simple one-shot CLI so n8n or any scheduler can orchestrate it. I scoped the final implementation around Reddit because it was the most reliable public source to demo end-to-end, while still keeping TikTok isolated as an expansion path.”

Useful talking points:

- I optimized for a complete, runnable system over a broad but fragile scraper.
- I kept the workflow orchestration outside the collector so the project works equally well with n8n, cron, or manual runs.
- I used simple JSON storage and heuristic analysis deliberately to keep the MVP easy to inspect and extend.
- I treated public-only collection as a hard product constraint, not an afterthought.
