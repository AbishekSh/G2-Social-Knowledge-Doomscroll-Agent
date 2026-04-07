import logging
from typing import Any, Dict, List
from urllib.parse import urljoin

from playwright.sync_api import BrowserContext, Locator, Page, sync_playwright

from .config import settings
from .models import RawCollectedItem, utc_now_iso
from .utils import normalize_whitespace

logger = logging.getLogger(__name__)


REDDIT_SELECTORS = {
    "post_cards": ["shreddit-post", "article", "div[data-testid='post-container']"],
    "title": ["a[slot='title']", "h3", "a[data-testid='post-title']"],
    "author": ["faceplate-tracker[source='post_author']", "a[href*='/user/']", "span[slot='authorName']"],
    "comment_links": ["a[href*='/comments/']"],
    "comment_blocks": [
        "shreddit-comment[depth='0'] div[slot='comment']",
        "div[data-testid='comment']",
        "div.Comment div[data-testid='comment']",
    ],
    "comment_count": ["faceplate-number", "span[data-post-click-location='comments']"],
    "score": ["div[slot='vote-button'] faceplate-number", "faceplate-number[number]"],
}


def _first_text(node: Any, selectors: List[str]) -> str:
    for selector in selectors:
        try:
            element = node.locator(selector).first
            if element.count() == 0:
                continue
            text = normalize_whitespace(element.inner_text())
            if text:
                return text
            for attribute in ("content", "href", "number"):
                value = normalize_whitespace(element.get_attribute(attribute))
                if value:
                    return value
        except Exception:
            continue
    return ""


def _first_href(node: Any, selectors: List[str], base_url: str) -> str:
    for selector in selectors:
        try:
            element = node.locator(selector).first
            if element.count() == 0:
                continue
            href = normalize_whitespace(element.get_attribute("href"))
            if href:
                return urljoin(base_url, href)
        except Exception:
            continue
    return ""


class RedditCollector:
    """Public Reddit collector that extracts listing items and enriches them with top comments."""

    def __init__(self, headless: bool = True):
        self.headless = headless

    def collect(self) -> List[RawCollectedItem]:
        results: List[RawCollectedItem] = []
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=self.headless)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                )
            )
            try:
                for source_url in settings.target_urls:
                    results.extend(self._collect_listing(context, source_url))
            finally:
                browser.close()
        return results

    def _collect_listing(self, context: BrowserContext, source_url: str) -> List[RawCollectedItem]:
        page = context.new_page()
        results: List[RawCollectedItem] = []
        try:
            logger.info("Collecting public Reddit listing: %s", source_url)
            page.set_default_timeout(30_000)
            page.goto(source_url, wait_until="domcontentloaded")
            page.wait_for_timeout(2_500)
            page.evaluate("window.scrollBy(0, window.innerHeight)")
            page.wait_for_timeout(1_000)
            listing_text = page.inner_text("body")
            listing_html = page.content()
            post_cards = self._find_post_cards(page)
            logger.info("Found %d Reddit post candidates on %s", len(post_cards), source_url)

            for card in post_cards[: settings.max_videos_per_run]:
                extracted = self._extract_post_data(card, source_url)
                if not extracted.get("caption"):
                    continue
                post_url = extracted.get("post_url") or source_url
                extracted["comments"] = self._fetch_top_comments(context, post_url, settings.max_comments_per_video)
                extracted["comment_count"] = extracted.get("comment_count") or str(len(extracted["comments"]))
                results.append(
                    RawCollectedItem(
                        platform="reddit",
                        source_url=source_url,
                        page_text=normalize_whitespace(listing_text),
                        raw_html=listing_html,
                        extracted_fields=extracted,
                        collected_at=utc_now_iso(),
                    )
                )
        except Exception as exc:
            logger.warning("Failed to collect Reddit listing %s: %s", source_url, exc)
        finally:
            page.close()
        return results

    def _find_post_cards(self, page: Page) -> List[Locator]:
        for selector in REDDIT_SELECTORS["post_cards"]:
            try:
                cards = page.locator(selector)
                count = cards.count()
                if count:
                    return [cards.nth(index) for index in range(count)]
            except Exception:
                continue
        return []

    def _extract_post_data(self, card: Locator, source_url: str) -> Dict[str, Any]:
        post_url = _first_href(card, REDDIT_SELECTORS["comment_links"], source_url)
        score = _first_text(card, REDDIT_SELECTORS["score"])
        return {
            "platform": "reddit",
            "source_url": source_url,
            "post_url": post_url,
            "video_url": post_url,
            "caption": _first_text(card, REDDIT_SELECTORS["title"]),
            "creator_handle": _first_text(card, REDDIT_SELECTORS["author"]),
            "comments": [],
            "visible_tags": [],
            "likes": score,
            "shares": "0",
            "comment_count": _first_text(card, REDDIT_SELECTORS["comment_count"]),
        }

    def _fetch_top_comments(self, context: BrowserContext, post_url: str, limit: int) -> List[str]:
        if not post_url:
            return []

        page = context.new_page()
        comments: List[str] = []
        try:
            page.set_default_timeout(20_000)
            page.goto(post_url, wait_until="domcontentloaded")
            page.wait_for_timeout(1_500)
            for selector in REDDIT_SELECTORS["comment_blocks"]:
                try:
                    blocks = page.locator(selector)
                    count = blocks.count()
                    if not count:
                        continue
                    for index in range(min(count, limit * 2)):
                        text = normalize_whitespace(blocks.nth(index).inner_text())
                        if text and len(text) > 15:
                            comments.append(text[:280])
                        if len(comments) >= limit:
                            return comments
                except Exception:
                    continue
        except Exception as exc:
            logger.debug("Could not load Reddit comments from %s: %s", post_url, exc)
        finally:
            page.close()
        return comments
