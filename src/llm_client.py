import json
import logging
from typing import Any, Dict, Optional

import requests

from .config import settings

logger = logging.getLogger(__name__)


def generate_llm_payload(item_data: Dict[str, Any]) -> Dict[str, Any]:
    platform = item_data.get("platform", "social")
    return {
        "model": settings.llm_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You analyze public social content and must respond with strict JSON only. "
                    "Return keys: video_summary, topic, sentiment, keywords, signal_tags. "
                    "Sentiment must be one of positive, negative, neutral."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Platform: {platform}\n"
                    f"Caption: {item_data.get('caption', '')}\n"
                    f"Hashtags: {', '.join(item_data.get('hashtags', []))}\n"
                    f"Comments: {', '.join(item_data.get('comments', [])[:5])}\n"
                    f"Transcript: {item_data.get('transcript', '')}\n"
                ),
            },
        ],
        "temperature": 0.2,
        "max_tokens": 300,
        "response_format": {"type": "json_object"},
    }


def call_llm(item_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not settings.llm_base_url or not settings.llm_api_key:
        logger.warning("LLM not configured; skipping enrichment.")
        return None

    try:
        response = requests.post(
            settings.llm_base_url,
            headers={
                "Authorization": f"Bearer {settings.llm_api_key}",
                "Content-Type": "application/json",
            },
            json=generate_llm_payload(item_data),
            timeout=20,
        )
        response.raise_for_status()
        return json.loads(_extract_text_from_response(response.json()))
    except Exception as exc:
        logger.warning("LLM enrichment failed: %s", exc)
        return None


def _extract_text_from_response(payload: Dict[str, Any]) -> str:
    if payload.get("choices"):
        return payload["choices"][0].get("message", {}).get("content", "")
    return payload.get("output", "")
