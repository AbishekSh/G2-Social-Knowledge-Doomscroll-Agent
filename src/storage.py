import hashlib
import json
import logging
import os
from glob import glob
from typing import List, Optional

from .config import Settings
from .models import ProcessedItem, RawCollectedItem, TrendInsight
from .utils import dump_json, load_json

logger = logging.getLogger(__name__)


def get_settings() -> Settings:
    return Settings()


def ensure_directories() -> None:
    current_settings = get_settings()
    for path in (current_settings.raw_dir, current_settings.processed_dir, current_settings.insights_dir):
        os.makedirs(path, exist_ok=True)


def save_raw_items(raw_items: List[RawCollectedItem]) -> List[str]:
    current_settings = get_settings()
    ensure_directories()
    paths: List[str] = []
    for index, item in enumerate(raw_items):
        filename = os.path.join(
            current_settings.raw_dir,
            f"raw_{item.platform}_{item.collected_at.replace(':', '-')}_{index}.json",
        )
        dump_json(filename, item.to_dict())
        paths.append(filename)
    return paths


def save_processed_items(processed_items: List[ProcessedItem]) -> List[str]:
    current_settings = get_settings()
    ensure_directories()
    paths: List[str] = []
    for index, item in enumerate(processed_items):
        identifier_source = item.video_url or item.source_url or item.caption
        item_hash = hashlib.md5(identifier_source.encode("utf-8")).hexdigest()[:10]
        filename = os.path.join(
            current_settings.processed_dir,
            f"processed_{item.platform}_{item_hash}_{index}_{item.collected_at.replace(':', '-')}.json",
        )
        dump_json(filename, item.to_dict())
        paths.append(filename)
    return paths


def save_insight(insight: TrendInsight) -> str:
    current_settings = get_settings()
    ensure_directories()
    filename = os.path.join(current_settings.insights_dir, f"insight_{insight.generated_at.replace(':', '-')}.json")
    latest_path = os.path.join(current_settings.insights_dir, "latest_insight.json")
    dump_json(filename, insight.to_dict())
    dump_json(latest_path, insight.to_dict())
    return filename


def load_latest_insight() -> Optional[TrendInsight]:
    current_settings = get_settings()
    latest_path = os.path.join(current_settings.insights_dir, "latest_insight.json")
    if not os.path.exists(latest_path):
        return None
    return TrendInsight(**load_json(latest_path))


def load_previous_insight() -> Optional[TrendInsight]:
    current_settings = get_settings()
    entries = sorted(glob(os.path.join(current_settings.insights_dir, "insight_*.json")))
    if len(entries) < 2:
        return None
    with open(entries[-2], "r", encoding="utf-8") as handle:
        return TrendInsight(**json.load(handle))
