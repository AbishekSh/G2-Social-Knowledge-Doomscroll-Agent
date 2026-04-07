import logging
import os
from glob import glob
from typing import Dict, List, Optional, Tuple

from .config import Settings
from .models import ProcessedItem
from .utils import load_json, unique_preserve_order

logger = logging.getLogger(__name__)


def get_settings() -> Settings:
    return Settings()


def load_all_processed_items() -> List[ProcessedItem]:
    current_settings = get_settings()
    items: List[ProcessedItem] = []
    if not os.path.exists(current_settings.processed_dir):
        return items

    for filepath in sorted(glob(os.path.join(current_settings.processed_dir, "processed_*.json"))):
        try:
            items.append(ProcessedItem(**load_json(filepath)))
        except Exception as exc:
            logger.warning("Failed to load processed item %s: %s", filepath, exc)
    return items


def _make_post_id(item: ProcessedItem) -> str:
    if item.video_url:
        return item.video_url.split("?")[0].strip().lower()
    if item.caption:
        return f"{item.platform}:{item.caption.strip().lower()[:120]}"
    return f"{item.platform}:{item.source_url.strip().lower()}"


def deduplicate_and_merge(
    new_items: List[ProcessedItem],
    old_items: Optional[List[ProcessedItem]] = None,
) -> Tuple[List[ProcessedItem], int]:
    old_items = old_items if old_items is not None else load_all_processed_items()
    seen_map: Dict[str, ProcessedItem] = {_make_post_id(item): item for item in old_items}

    deduplicated: List[ProcessedItem] = []
    merged_count = 0

    for new_item in new_items:
        post_id = _make_post_id(new_item)
        previous = seen_map.get(post_id)
        if previous is None:
            deduplicated.append(new_item)
            seen_map[post_id] = new_item
            continue

        merged_count += 1
        merged_item = ProcessedItem(
            platform=new_item.platform,
            source_url=new_item.source_url,
            video_url=new_item.video_url or previous.video_url,
            creator_handle=new_item.creator_handle or previous.creator_handle,
            caption=new_item.caption or previous.caption,
            hashtags=unique_preserve_order(previous.hashtags + new_item.hashtags),
            comments=unique_preserve_order(previous.comments + new_item.comments),
            transcript=new_item.transcript or previous.transcript,
            video_summary=new_item.video_summary or previous.video_summary,
            topic=new_item.topic or previous.topic,
            sentiment=new_item.sentiment or previous.sentiment,
            keywords=unique_preserve_order(previous.keywords + new_item.keywords),
            signal_tags=unique_preserve_order(previous.signal_tags + new_item.signal_tags),
            collected_at=max(previous.collected_at, new_item.collected_at),
        )
        deduplicated.append(merged_item)
        seen_map[post_id] = merged_item

    return deduplicated, merged_count
