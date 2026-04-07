from src.models import TrendInsight
from src.trends import build_insight


def test_build_insight_aggregates_topic_counts():
    items = [
        {"topic": "local_llms", "hashtags": ["ai"], "keywords": ["local", "llm"], "sentiment": "positive", "creator_handle": "@a"},
        {"topic": "local_llms", "hashtags": ["offline"], "keywords": ["privacy"], "sentiment": "positive", "creator_handle": "@b"},
        {"topic": "productivity", "hashtags": ["productivity"], "keywords": ["workflow"], "sentiment": "neutral", "creator_handle": "@a"},
    ]
    insight = build_insight(items)
    assert isinstance(insight, TrendInsight)
    assert insight.mention_count["local_llms"] == 2
    assert "ai" in insight.recurring_hashtags
    assert insight.dominant_sentiment == "positive"
    assert insight.creator_frequency["@a"] == 2


def test_build_insight_generates_actionable_insight():
    items = [{"topic": "ai_coding_tools", "hashtags": ["ai"], "keywords": ["code"], "sentiment": "positive", "creator_handle": "@x"}]
    insight = build_insight(items)
    assert "Actionable insight:" in insight.actionable_insight
