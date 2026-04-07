import argparse
import logging
from typing import List, Sequence

from .analyzer import analyze_item
from .collector import TikTokCollector
from .config import settings
from .deduplication import deduplicate_and_merge
from .parser import build_processed_item, parse_collected_item
from .reddit_collector import RedditCollector
from .scheduler import run_loop
from .storage import load_previous_insight, save_insight, save_processed_items, save_raw_items
from .transcript import get_transcript_for_item
from .trends import build_insight

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _select_collector():
    if settings.target_platform == "reddit":
        return RedditCollector(headless=settings.playwright_headless)
    return TikTokCollector(headless=settings.playwright_headless)


def run_once() -> None:
    collector = _select_collector()
    raw_items = collector.collect()
    raw_files = save_raw_items(raw_items)

    processed_items = []
    for raw_item in raw_items[: settings.max_videos_per_run]:
        parsed = parse_collected_item(raw_item, settings.max_comments_per_video)
        transcript = get_transcript_for_item(raw_item.extracted_fields)
        parsed["transcript"] = transcript
        analysis = analyze_item(parsed)
        processed_items.append(build_processed_item(parsed, transcript, analysis))

    deduplicated_items, merged_count = deduplicate_and_merge(processed_items)
    processed_files = save_processed_items(deduplicated_items)
    insight = build_insight([item.to_dict() for item in deduplicated_items], load_previous_insight())
    insight_file = save_insight(insight)

    logger.info("Run completed for platform=%s", settings.target_platform)
    logger.info("Items processed: %d", len(deduplicated_items))
    logger.info("Merged duplicates: %d", merged_count)
    logger.info("Raw files: %s", raw_files)
    logger.info("Processed files: %s", processed_files)
    logger.info("Insight file: %s", insight_file)
    logger.info("Final actionable insight: %s", insight.actionable_insight)


def main(args: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="doomscroll-agent pipeline")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--once", action="store_true", help="Run the pipeline once")
    group.add_argument("--loop", action="store_true", help="Run the pipeline continuously")
    parsed_args = parser.parse_args(args=args)

    if parsed_args.once:
        run_once()
    else:
        run_loop(run_once)


if __name__ == "__main__":
    main()
