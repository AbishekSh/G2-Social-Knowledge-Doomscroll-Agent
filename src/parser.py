from typing import Any, Dict, Optional

from .models import ProcessedItem, RawCollectedItem
from .utils import dedupe_comments, extract_hashtags, normalize_whitespace, parse_metric_count


def _normalize_tags(caption: str, visible_tags: Any) -> list[str]:
    caption_tags = extract_hashtags(caption)
    if caption_tags:
        return caption_tags

    tags: list[str] = []
    for tag in visible_tags or []:
        normalized = normalize_whitespace(tag).lstrip("#").lower()
        if normalized:
            tags.append(normalized)
    return list(dict.fromkeys(tags))


def parse_collected_item(raw_item: RawCollectedItem, max_comments: int) -> Dict[str, Any]:
    fields = raw_item.extracted_fields
    caption = normalize_whitespace(fields.get("caption", ""))
    creator_handle = normalize_whitespace(fields.get("creator_handle", ""))
    post_url = normalize_whitespace(fields.get("post_url", ""))
    item_url = normalize_whitespace(fields.get("video_url") or post_url or raw_item.source_url)
    comments = dedupe_comments(fields.get("comments", []) or [])[:max_comments]
    hashtags = _normalize_tags(caption, fields.get("visible_tags", []))

    return {
        "platform": normalize_whitespace(fields.get("platform", raw_item.platform)).lower() or raw_item.platform,
        "source_url": raw_item.source_url,
        "video_url": item_url,
        "creator_handle": creator_handle,
        "caption": caption,
        "hashtags": hashtags,
        "comments": comments,
        "likes": parse_metric_count(fields.get("likes", "")),
        "shares": parse_metric_count(fields.get("shares", "")),
        "comment_count": parse_metric_count(fields.get("comment_count", "")),
        "collected_at": raw_item.collected_at,
    }


def parse_tiktok_raw_item(raw_item: RawCollectedItem, max_comments: int) -> Dict[str, Any]:
    return parse_collected_item(raw_item, max_comments)


def build_processed_item(
    parsed: Dict[str, Any],
    transcript: Optional[str],
    analysis: Dict[str, Any],
) -> ProcessedItem:
    return ProcessedItem(
        platform=parsed["platform"],
        source_url=parsed["source_url"],
        video_url=parsed["video_url"],
        creator_handle=parsed["creator_handle"],
        caption=parsed["caption"],
        hashtags=parsed["hashtags"],
        comments=parsed["comments"],
        transcript=transcript,
        video_summary=analysis["video_summary"],
        topic=analysis["topic"],
        sentiment=analysis["sentiment"],
        keywords=analysis["keywords"],
        signal_tags=analysis["signal_tags"],
        collected_at=parsed["collected_at"],
    )
