from typing import Any, Dict, Optional

from .config import settings
from .utils import normalize_whitespace


def get_transcript_for_item(parsed_fields: Dict[str, Any]) -> Optional[str]:
    if not settings.enable_transcript:
        return None
    transcript = normalize_whitespace(parsed_fields.get("transcript"))
    return transcript or None
