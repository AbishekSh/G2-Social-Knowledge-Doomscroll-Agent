import logging
from typing import Any, Dict, List

from playwright.sync_api import Page, sync_playwright

from .config import settings
from .models import RawCollectedItem, utc_now_iso
from .utils import normalize_whitespace

logger = logging.getLogger(__name__)


TIKTOK_SELECTORS = {
    "caption": [
        "div[data-e2e='video-desc']",
        "span[data-e2e='browse-video-desc']",
        "h1",
        "meta[property='og:description']",
        "meta[name='description']",
    ],
    "creator_handle": [
        "h3[data-e2e='author-name']",
        "span[data-e2e='user-title']",
        "a[href*='/@']",
    ],
    "comments": [
        "div[data-e2e='comment-text']",
        "p[data-testid*='comment']",
    ],
    "visible_tags": [
        "a[href*='/tag/']",
        "span[data-e2e='search-common-link']",
    ],
    "likes": ["strong[data-e2e='like-count']"],
    "shares": ["strong[data-e2e='share-count']"],
    "comment_count": ["strong[data-e2e='comment-count']"],
}


def _query_first_text(page: Page, selectors: List[str]) -> str:
    for selector in selectors:
        try:
            element = page.query_selector(selector)
            if not element:
                continue
            text = normalize_whitespace(element.inner_text())
            if text:
                return text
            content = normalize_whitespace(element.get_attribute("content"))
            if content:
                return content
        except Exception:
            continue
    return ""


def _query_all_text(page: Page, selectors: List[str]) -> List[str]:
    values: List[str] = []
    for selector in selectors:
        try:
            for element in page.query_selector_all(selector):
                text = normalize_whitespace(element.inner_text())
                if text:
                    values.append(text)
        except Exception:
            continue
    return values


class TikTokCollector:
    """Best-effort public TikTok collector scaffold.

    TikTok is intentionally kept isolated because public page rendering changes
    frequently. The project's current reliable implementation is Reddit.
    """

    def __init__(self, headless: bool = True):
        self.headless = headless

    def collect(self) -> List[RawCollectedItem]:
        items: List[RawCollectedItem] = []
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=self.headless)
            context = browser.new_context()
            try:
                for source_url in settings.target_urls:
                    page = context.new_page()
                    try:
                        logger.info("Collecting public TikTok page: %s", source_url)
                        page.set_default_timeout(30_000)
                        page.goto(source_url, wait_until="domcontentloaded")
                        page.wait_for_timeout(4_000)
                        page_text = normalize_whitespace(page.inner_text("body"))
                        raw_html = page.content()
                        extracted_fields = self._extract_fields(page, source_url)
                        items.append(
                            RawCollectedItem(
                                platform="tiktok",
                                source_url=source_url,
                                page_text=page_text,
                                raw_html=raw_html,
                                extracted_fields=extracted_fields,
                                collected_at=utc_now_iso(),
                            )
                        )
                    except Exception as exc:
                        logger.warning("TikTok collection failed for %s: %s", source_url, exc)
                    finally:
                        page.close()
            finally:
                browser.close()
        return items

    def _extract_fields(self, page: Page, source_url: str) -> Dict[str, Any]:
        return {
            "platform": "tiktok",
            "source_url": source_url,
            "post_url": source_url,
            "video_url": self._find_video_url(page) or source_url,
            "caption": _query_first_text(page, TIKTOK_SELECTORS["caption"]),
            "creator_handle": _query_first_text(page, TIKTOK_SELECTORS["creator_handle"]),
            "comments": _query_all_text(page, TIKTOK_SELECTORS["comments"]),
            "visible_tags": _query_all_text(page, TIKTOK_SELECTORS["visible_tags"]),
            "likes": _query_first_text(page, TIKTOK_SELECTORS["likes"]),
            "shares": _query_first_text(page, TIKTOK_SELECTORS["shares"]),
            "comment_count": _query_first_text(page, TIKTOK_SELECTORS["comment_count"]),
        }

    def _find_video_url(self, page: Page) -> str:
        try:
            for selector in ["meta[property='og:url']", "meta[property='og:video']", "video[src]", "source[src]"]:
                element = page.query_selector(selector)
                if not element:
                    continue
                attribute = element.get_attribute("content") or element.get_attribute("src") or ""
                if attribute:
                    return normalize_whitespace(attribute)
        except Exception:
            return ""
        return ""
