import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE_PATH = PROJECT_ROOT / ".env"

if ENV_FILE_PATH.exists():
    load_dotenv(dotenv_path=ENV_FILE_PATH, override=True)
else:
    load_dotenv(override=True)


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_list(name: str, default: List[str]) -> List[str]:
    value = os.getenv(name, "")
    if not value.strip():
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


def _default_target_urls() -> List[str]:
    platform = os.getenv("TARGET_PLATFORM", "reddit").strip().lower()
    if platform == "reddit":
        return _env_list(
            "TARGET_URLS",
            [
                "https://www.reddit.com/r/artificial/",
                "https://www.reddit.com/r/MachineLearning/",
            ],
        )
    return _env_list("TARGET_URLS", ["https://www.tiktok.com/tag/aitools"])


@dataclass(frozen=True)
class Settings:
    target_platform: str = os.getenv("TARGET_PLATFORM", "reddit").strip().lower()
    target_urls: List[str] = field(default_factory=_default_target_urls)
    max_videos_per_run: int = _env_int("MAX_VIDEOS_PER_RUN", 8)
    max_comments_per_video: int = _env_int("MAX_COMMENTS_PER_VIDEO", 5)
    analysis_mode: str = os.getenv("ANALYSIS_MODE", "heuristic").strip().lower()
    llm_base_url: str = os.getenv("LLM_BASE_URL", "").strip()
    llm_api_key: str = os.getenv("LLM_API_KEY", "").strip()
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini").strip()
    enable_transcript: bool = _env_bool("ENABLE_TRANSCRIPT", False)
    poll_interval_seconds: int = _env_int("POLL_INTERVAL_SECONDS", 300)
    output_dir: str = os.getenv("OUTPUT_DIR", "./data").strip()
    playwright_headless: bool = _env_bool("PLAYWRIGHT_HEADLESS", True)
    niche: str = os.getenv("NICHE", "ai_tools").strip().lower()

    @property
    def raw_dir(self) -> str:
        return os.path.join(self.output_dir, "raw")

    @property
    def processed_dir(self) -> str:
        return os.path.join(self.output_dir, "processed")

    @property
    def insights_dir(self) -> str:
        return os.path.join(self.output_dir, "insights")

    @property
    def tik_tok_target_urls(self) -> List[str]:
        return self.target_urls


settings = Settings()
