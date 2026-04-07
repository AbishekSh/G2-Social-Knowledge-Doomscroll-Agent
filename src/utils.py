import json
import re
from typing import Any, Iterable, List


HASHTAG_PATTERN = re.compile(r"#([A-Za-z0-9_]+)")
METRIC_PATTERN = re.compile(r"(?P<number>\d+(?:\.\d+)?)(?P<suffix>[KMB]?)", re.IGNORECASE)


def safe_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return " ".join(str(item) for item in value if item is not None)
    return str(value).strip()


def normalize_whitespace(text: Any) -> str:
    return re.sub(r"\s+", " ", safe_text(text)).strip()


def extract_hashtags(text: str) -> List[str]:
    return [tag.lower() for tag in HASHTAG_PATTERN.findall(safe_text(text))]


def unique_preserve_order(values: Iterable[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for value in values:
        normalized = normalize_whitespace(value)
        if not normalized:
            continue
        lowered = normalized.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        result.append(normalized)
    return result


def dedupe_comments(comments: Iterable[str]) -> List[str]:
    return unique_preserve_order(comments)


def parse_metric_count(text: str) -> int:
    normalized = normalize_whitespace(text).replace(",", "")
    if not normalized:
        return 0

    match = METRIC_PATTERN.search(normalized)
    if not match:
        return 0

    number = float(match.group("number"))
    suffix = match.group("suffix").lower()
    multiplier = {"": 1, "k": 1_000, "m": 1_000_000, "b": 1_000_000_000}[suffix]
    return int(number * multiplier)


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def dump_json(path: str, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
