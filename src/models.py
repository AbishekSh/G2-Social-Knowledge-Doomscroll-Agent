from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class RawCollectedItem:
    platform: str
    source_url: str
    page_text: str
    raw_html: str
    extracted_fields: Dict[str, Any]
    collected_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ProcessedItem:
    platform: str
    source_url: str
    video_url: str
    creator_handle: str
    caption: str
    hashtags: List[str]
    comments: List[str]
    transcript: Optional[str]
    video_summary: str
    topic: str
    sentiment: str
    keywords: List[str]
    signal_tags: List[str]
    collected_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TrendInsight:
    generated_at: str
    headline: str
    actionable_insight: str
    topic_summary: List[Dict[str, Any]]
    mention_count: Dict[str, int]
    recurring_hashtags: List[str]
    recurring_keywords: List[str]
    dominant_sentiment: str
    creator_frequency: Dict[str, int]
    trend_score: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


# Backward-compatible aliases used by the existing tests and module imports.
RawTikTokItem = RawCollectedItem
ProcessedTikTokItem = ProcessedItem
