from src.models import RawTikTokItem
from src.parser import parse_collected_item, parse_tiktok_raw_item


def test_parse_tiktok_raw_item_extracts_basic_fields():
    raw = RawTikTokItem(
        platform="tiktok",
        source_url="https://www.tiktok.com/@creator/video/123",
        page_text="",
        raw_html="",
        extracted_fields={
            "platform": "tiktok",
            "caption": "Check out this #ai tool",
            "creator_handle": "@creator",
            "video_url": "https://www.tiktok.com/@creator/video/123",
            "comments": ["Amazing!", "So cool"],
            "likes": "1.2K",
            "shares": "34",
            "comment_count": "10",
        },
        collected_at="2026-04-07T20:00:00Z",
    )
    parsed = parse_tiktok_raw_item(raw, max_comments=2)
    assert parsed["platform"] == "tiktok"
    assert parsed["creator_handle"] == "@creator"
    assert parsed["video_url"] == "https://www.tiktok.com/@creator/video/123"
    assert parsed["hashtags"] == ["ai"]
    assert parsed["comments"] == ["Amazing!", "So cool"]
    assert parsed["likes"] == 1200
    assert parsed["shares"] == 34
    assert parsed["comment_count"] == 10


def test_parse_collected_item_respects_platform_and_post_url():
    raw = RawTikTokItem(
        platform="reddit",
        source_url="https://www.reddit.com/r/artificial/",
        page_text="",
        raw_html="",
        extracted_fields={
            "platform": "reddit",
            "caption": "Local AI tools are trending",
            "creator_handle": "u/example",
            "post_url": "https://www.reddit.com/r/artificial/comments/abc/post/",
            "comments": ["Useful thread", "Useful thread", "Great comments"],
            "comment_count": "2.4K",
        },
        collected_at="2026-04-07T20:00:00Z",
    )
    parsed = parse_collected_item(raw, max_comments=5)
    assert parsed["platform"] == "reddit"
    assert parsed["video_url"] == "https://www.reddit.com/r/artificial/comments/abc/post/"
    assert parsed["comments"] == ["Useful thread", "Great comments"]
    assert parsed["comment_count"] == 2400
