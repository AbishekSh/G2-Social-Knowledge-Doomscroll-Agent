import logging
from collections import Counter
from typing import Any, Dict, Iterable, List

from .config import settings
from .llm_client import call_llm
from .utils import normalize_whitespace, unique_preserve_order

logger = logging.getLogger(__name__)


TOPIC_KEYWORDS = {
    "ai_coding_tools": ["copilot", "cursor", "windsurf", "coding", "developer", "code assistant"],
    "local_llms": ["local llm", "self-hosted", "ollama", "llama", "offline model", "private ai"],
    "prompts_agents": ["prompt", "agent", "automation", "workflow", "multi-agent"],
    "productivity": ["productivity", "study", "focus", "task", "habit", "notes"],
    "business_marketing": ["marketing", "growth", "sales", "launch", "brand", "startup"],
    "politics": ["election", "congress", "senate", "president", "campaign", "policy"],
    "international": ["global", "international", "world", "diplomatic", "foreign"],
    "conflict": ["war", "military", "attack", "strike", "weapons", "conflict"],
    "justice": ["court", "judge", "lawsuit", "arrest", "charges", "legal"],
    "other": [],
}

SENTIMENT_KEYWORDS = {
    "positive": ["love", "helpful", "useful", "great", "fast", "excited", "impressive", "smart"],
    "negative": ["hate", "bad", "broken", "concern", "problem", "worse", "slow", "angry"],
}

STOPWORDS = {
    "about",
    "after",
    "again",
    "been",
    "from",
    "into",
    "just",
    "more",
    "over",
    "that",
    "their",
    "there",
    "these",
    "this",
    "with",
}


def _tokenize(text: str) -> List[str]:
    cleaned = normalize_whitespace(text).lower()
    return [token.strip(".,!?;:()[]{}\"'") for token in cleaned.split() if token]


def _pick_topic(text: str) -> str:
    normalized = normalize_whitespace(text).lower()
    best_topic = "other"
    best_score = 0
    for topic, keywords in TOPIC_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in normalized)
        if score > best_score:
            best_topic = topic
            best_score = score
    return best_topic


def _estimate_sentiment(texts: Iterable[str]) -> str:
    scores = Counter()
    for text in texts:
        normalized = normalize_whitespace(text).lower()
        for label, keywords in SENTIMENT_KEYWORDS.items():
            scores[label] += sum(1 for keyword in keywords if keyword in normalized)
    if scores["positive"] > scores["negative"]:
        return "positive"
    if scores["negative"] > scores["positive"]:
        return "negative"
    return "neutral"


def _extract_keywords(texts: Iterable[str], limit: int = 5) -> List[str]:
    counter: Counter[str] = Counter()
    for text in texts:
        for token in _tokenize(text):
            if len(token) < 4 or token.startswith("#") or token in STOPWORDS:
                continue
            counter[token] += 1
    return [token for token, _ in counter.most_common(limit)]


def _build_summary(item: Dict[str, Any], topic: str, keywords: List[str]) -> str:
    caption = normalize_whitespace(item.get("caption", ""))
    creator = normalize_whitespace(item.get("creator_handle", ""))
    keyword_phrase = ", ".join(keywords[:3]) if keywords else "emerging discussion"

    if caption:
        summary = caption[:180]
    else:
        summary = f"Public post discussing {topic.replace('_', ' ')} with emphasis on {keyword_phrase}."

    if creator:
        return f"{summary} Creator signal: {creator}."
    return summary


def heuristic_analysis(item: Dict[str, Any]) -> Dict[str, Any]:
    caption = normalize_whitespace(item.get("caption", ""))
    hashtags = item.get("hashtags", []) or []
    comments = item.get("comments", []) or []
    transcript = normalize_whitespace(item.get("transcript", ""))
    text_pool = [caption, " ".join(hashtags), " ".join(comments), transcript]
    topic = _pick_topic(" ".join(text_pool))
    sentiment = _estimate_sentiment([caption, transcript, *comments])
    keywords = _extract_keywords([caption, transcript, *comments])
    signal_tags = unique_preserve_order([*hashtags[:3], *keywords[:3], topic])[:5]

    return {
        "video_summary": _build_summary(item, topic, keywords),
        "topic": topic,
        "sentiment": sentiment,
        "keywords": keywords or hashtags[:3],
        "signal_tags": signal_tags,
    }


def _valid_llm_output(result: Dict[str, Any]) -> bool:
    return (
        isinstance(result, dict)
        and isinstance(result.get("video_summary"), str)
        and isinstance(result.get("topic"), str)
        and result.get("sentiment") in {"positive", "negative", "neutral"}
        and isinstance(result.get("keywords"), list)
        and isinstance(result.get("signal_tags"), list)
    )


def analyze_item(parsed_item: Dict[str, Any]) -> Dict[str, Any]:
    if settings.analysis_mode == "llm":
        llm_result = call_llm(parsed_item)
        if llm_result and _valid_llm_output(llm_result):
            return {
                "video_summary": normalize_whitespace(llm_result["video_summary"]),
                "topic": normalize_whitespace(llm_result["topic"]).lower() or "other",
                "sentiment": llm_result["sentiment"],
                "keywords": [normalize_whitespace(value).lower() for value in llm_result["keywords"] if value],
                "signal_tags": [normalize_whitespace(value).lower() for value in llm_result["signal_tags"] if value],
            }
        logger.info("Falling back to heuristic analysis.")
    return heuristic_analysis(parsed_item)
