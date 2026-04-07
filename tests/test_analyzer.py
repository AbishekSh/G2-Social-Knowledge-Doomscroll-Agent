from src.analyzer import analyze_item


def test_analyzer_returns_expected_shape():
    item = {
        "platform": "reddit",
        "caption": "New local AI coding workflow with self-hosted model.",
        "hashtags": ["ai", "productivity"],
        "comments": ["Love this setup", "Very helpful"],
        "transcript": None,
    }
    analysis = analyze_item(item)
    assert set(analysis.keys()) == {"video_summary", "topic", "sentiment", "keywords", "signal_tags"}
    assert analysis["topic"] in {
        "ai_coding_tools",
        "local_llms",
        "prompts_agents",
        "productivity",
        "business_marketing",
        "politics",
        "international",
        "conflict",
        "justice",
        "other",
    }
    assert analysis["sentiment"] in {"positive", "negative", "neutral"}
    assert isinstance(analysis["keywords"], list)
    assert isinstance(analysis["signal_tags"], list)


def test_analyzer_detects_local_llm_signal():
    item = {
        "platform": "reddit",
        "caption": "Offline privacy-first llama workflow for developers",
        "hashtags": [],
        "comments": ["Very useful", "Love the self-hosted angle"],
        "transcript": None,
    }
    analysis = analyze_item(item)
    assert analysis["topic"] == "local_llms"
    assert analysis["sentiment"] == "positive"
