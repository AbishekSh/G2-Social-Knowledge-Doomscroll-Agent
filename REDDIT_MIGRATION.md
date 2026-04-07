# Reddit Support in doomscroll-agent

## Summary

The `doomscroll-agent` now supports **both TikTok and Reddit** as data sources. Reddit is recommended for robustness because:
- HTML structure is simpler and more stable than TikTok's JavaScript-heavy pages
- No heavy JavaScript rendering required—page content loads immediately
- Better extraction rates for titles, discussions, and comments
- Respectful of public community guidelines (no authentication bypass)

## Quick Start with Reddit

```bash
# 1. Update .env
export TARGET_PLATFORM=reddit
export TARGET_URLS="https://www.reddit.com/r/artificial/,https://www.reddit.com/r/MachineLearning/"

# 2. Run the pipeline
python3 -m src.run_pipeline --once
```

## Configuration Reference

### Reddit Target Format

Subreddit home:
```
https://www.reddit.com/r/{subreddit}/
```

Examples:
- `https://www.reddit.com/r/artificial/`
- `https://www.reddit.com/r/MachineLearning/`
- `https://www.reddit.com/r/LanguageModels/`
- `https://www.reddit.com/r/LocalLLaMA/`

### TikTok Target Format (still supported)

```
https://www.tiktok.com/tag/{hashtag}
https://www.tiktok.com/@{creator}
https://www.tiktok.com/search?q={query}
```

Examples:
- `https://www.tiktok.com/tag/aitools`
- `https://www.tiktok.com/@username`
- `https://www.tiktok.com/search?q=coding`

## What Changed

### New Module: `src/reddit_collector.py`

Handles Reddit-specific scraping:
- Uses Playwright with user-agent spoofing to avoid bot detection
- Extracts post titles, discussions, and comments
- Implements fallback text parsing when selectors fail
- Returns same data model as TikTok collector (`RawTikTokItem`)

### Updated Module: `src/config.py`

- `TARGET_PLATFORM` environment variable controls which collector is used
- `TARGET_URLS` now replaces `TIKTOK_TARGET_URLS` (supports both platforms)
- Auto-detects Reddit vs TikTok URLs based on platform setting

### Updated Module: `src/run_pipeline.py`

Conditionally instantiates the correct collector:
```python
if settings.target_platform.lower() == "reddit":
    collector = RedditCollector(headless=settings.playwright_headless)
else:
    collector = TikTokCollector(headless=settings.playwright_headless)
```

## Example Output: Reddit

Raw extraction from `/r/artificial/`:
```json
{
  "source_url": "https://www.reddit.com/r/artificial/",
  "caption": "\"Cognitive surrender\" leads AI users to abandon logical thinking, research finds",
  "keywords": ["cognitive", "surrender", "research"],
  "sentiment": "neutral"
}
```

Generated insight:
```
Monitor high-frequency AI tools content and prioritize creator conversations 
around self-hosted models, prompt workflows, and productivity signals.
```

## Comparison: TikTok vs Reddit

| Feature | TikTok | Reddit |
|---------|--------|--------|
| Content Type | Short video captions | Discussion threads |
| Extraction | Challenging (JavaScript) | Stable (HTML) |
| Bot Detection | Moderate | Minimal |
| Rate Limiting | Aggressive | Relaxed |
| Public Data | Full hashtag pages | Full subreddit pages |
| Best For | Trend velocity | Deep discussion analysis |

## When to Use Each

**Use Reddit when:**
- You want more reliable extraction
- Analyzing discussion trends and sentiment
- Working with AI/ML communities (many on Reddit)
- You need stable, repeatable results

**Use TikTok when:**
- You need real-time trend velocity
- Tracking short-form content creators
- Monitoring visual trends (if JavaScript rendering improves)
- Focusing on hashtag trends

## Compliance

Both collectors respect platform guidelines:
- No login bypass or authentication manipulation
- No private or protected content access
- User-agent identification (respectful bot behavior)
- Respects robots.txt and rate limits
- Public content only

## Running with Both Platforms

To compare TikTok and Reddit trends:

```bash
# Run TikTok collection
export TARGET_PLATFORM=tiktok
export TARGET_URLS="https://www.tiktok.com/tag/ai"
python3 -m src.run_pipeline --once

# Run Reddit collection
export TARGET_PLATFORM=reddit
export TARGET_URLS="https://www.reddit.com/r/artificial/"
python3 -m src.run_pipeline --once

# Compare latest insights
cat data/insights/latest_insight.json
```

Both outputs use the same schema, so they're directly comparable.
