from collections import Counter
from typing import Any, Dict, Iterable, List, Optional

from .models import TrendInsight, utc_now_iso
from .utils import normalize_whitespace


def _count_topics(processed_items: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    return dict(Counter(item.get("topic", "other") for item in processed_items))


def _count_hashtags(processed_items: Iterable[Dict[str, Any]]) -> List[str]:
    counter: Counter[str] = Counter()
    for item in processed_items:
        counter.update(tag.lower() for tag in item.get("hashtags", []) if tag)
    return [tag for tag, _ in counter.most_common(10)]


def _count_keywords(processed_items: Iterable[Dict[str, Any]]) -> List[str]:
    counter: Counter[str] = Counter()
    for item in processed_items:
        counter.update(normalize_whitespace(keyword).lower() for keyword in item.get("keywords", []) if keyword)
    return [keyword for keyword, _ in counter.most_common(10)]


def _dominant_sentiment(processed_items: Iterable[Dict[str, Any]]) -> str:
    counter = Counter(item.get("sentiment", "neutral") for item in processed_items)
    return counter.most_common(1)[0][0] if counter else "neutral"


def _creator_frequency(processed_items: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    counter = Counter(item.get("creator_handle") for item in processed_items if item.get("creator_handle"))
    return dict(counter)


def _build_topic_summary(topic_counts: Dict[str, int]) -> List[Dict[str, Any]]:
    return [
        {"topic": topic, "count": count}
        for topic, count in sorted(topic_counts.items(), key=lambda item: item[1], reverse=True)
    ]


def _calculate_trend_score(topic_counts: Dict[str, int], hashtags: List[str], creators: Dict[str, int]) -> float:
    return round(sum(topic_counts.values()) + len(hashtags) * 0.5 + len(creators) * 0.25, 2)


def build_insight(
    processed_items: List[Dict[str, Any]],
    previous_insight: Optional[TrendInsight] = None,
) -> TrendInsight:
    topic_counts = _count_topics(processed_items)
    hashtags = _count_hashtags(processed_items)
    keywords = _count_keywords(processed_items)
    sentiment = _dominant_sentiment(processed_items)
    creator_frequency = _creator_frequency(processed_items)
    trend_score = _calculate_trend_score(topic_counts, hashtags, creator_frequency)

    top_topic = max(topic_counts, key=topic_counts.get) if topic_counts else "other"
    rising_topic = None
    if previous_insight:
        previous_counts = previous_insight.mention_count
        for topic, count in sorted(topic_counts.items(), key=lambda item: item[1], reverse=True):
            if count > previous_counts.get(topic, 0):
                rising_topic = topic
                break

    focus_topic = rising_topic or top_topic
    headline = f"Top trend: {focus_topic}"
    keyword_phrase = ", ".join(keywords[:3]) if keywords else "broad public discussion"
    hashtag_phrase = ", ".join(f"#{tag}" for tag in hashtags[:3]) if hashtags else "no dominant hashtags yet"

    if rising_topic:
        actionable_insight = (
            f"{rising_topic.replace('_', ' ')} is gaining share versus the previous snapshot. "
            f"Conversation is centered on {keyword_phrase} with {sentiment} sentiment overall. "
            f"Actionable insight: publish or investigate around {rising_topic.replace('_', ' ')} while momentum is rising."
        )
    else:
        actionable_insight = (
            f"Current coverage is led by {top_topic.replace('_', ' ')}. "
            f"Recurring signals include {keyword_phrase} and {hashtag_phrase}, with {sentiment} sentiment overall. "
            f"Actionable insight: use this theme as the next monitoring or content priority."
        )

    return TrendInsight(
        generated_at=utc_now_iso(),
        headline=headline,
        actionable_insight=actionable_insight,
        topic_summary=_build_topic_summary(topic_counts),
        mention_count=topic_counts,
        recurring_hashtags=hashtags,
        recurring_keywords=keywords,
        dominant_sentiment=sentiment,
        creator_frequency=creator_frequency,
        trend_score=trend_score,
    )
