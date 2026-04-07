"""Mock data collector for demo purposes when live scraping is unavailable."""

import logging
from typing import List

from .models import RawTikTokItem, utc_now_iso

logger = logging.getLogger(__name__)

MOCK_TIKTOK_DATA = [
    {
        "caption": "Just deployed a new LLM fine-tuning pipeline using local models. Zero cloud costs, maximum privacy. #llm #ai #privacy",
        "creator_handle": "@ml_engineer",
        "video_url": "https://v.tiktok.com/mock1",
        "comments": [
            "How much faster is it compared to OpenAI API?",
            "This is exactly what I needed!",
            "Can you share the setup guide?",
        ],
        "likes": "2.3K",
        "shares": "450",
        "comment_count": "89",
        "visible_tags": ["llm", "ai", "privacy", "coding"],
    },
    {
        "caption": "Building an agentic workflow with local llama2. Automated research, writing, and refinement. All offline. #agents #automation",
        "creator_handle": "@ai_toolkit",
        "video_url": "https://v.tiktok.com/mock2",
        "comments": [
            "This is incredible for enterprise workflows",
            "How do you handle latency?",
            "Open sourcing this?",
        ],
        "likes": "5.1K",
        "shares": "812",
        "comment_count": "156",
        "visible_tags": ["agents", "automation", "ai", "workflow"],
    },
]


def collect_mock() -> List[RawTikTokItem]:
    logger.info("Using mock TikTok data for a no-network demo path.")
    items: List[RawTikTokItem] = []
    for data in MOCK_TIKTOK_DATA:
        items.append(
            RawTikTokItem(
                platform="tiktok",
                source_url="https://www.tiktok.com/tag/ai",
                page_text=" ".join([data["caption"], *data["comments"]]),
                raw_html="<html><!-- mock data --></html>",
                extracted_fields={"platform": "tiktok", "post_url": data["video_url"], **data},
                collected_at=utc_now_iso(),
            )
        )
    return items
