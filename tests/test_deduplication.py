import pytest

from src.deduplication import _make_post_id, deduplicate_and_merge
from src.models import ProcessedTikTokItem


def make_test_item(
    caption: str,
    comments: list,
    collected_at: str = "2026-04-07T05:00:00Z",
    video_url: str = "",
) -> ProcessedTikTokItem:
    return ProcessedTikTokItem(
        platform="reddit",
        source_url="https://www.reddit.com/r/test/",
        video_url=video_url,
        creator_handle="",
        caption=caption,
        hashtags=[],
        comments=comments,
        transcript=None,
        video_summary="Test",
        topic="other",
        sentiment="neutral",
        keywords=[],
        signal_tags=[],
        collected_at=collected_at,
    )


def test_make_post_id_prefers_video_url():
    item = make_test_item("Test post about AI", [], video_url="https://reddit.com/comments/abc")
    post_id = _make_post_id(item)
    assert post_id == "https://reddit.com/comments/abc"


def test_deduplicate_no_duplicates():
    item1 = make_test_item("Post A", ["comment1"])
    item2 = make_test_item("Post B", ["comment2"])
    deduplicated, merged = deduplicate_and_merge([item1, item2], [])
    assert len(deduplicated) == 2
    assert merged == 0


def test_deduplicate_with_duplicate():
    old_item = make_test_item("Test post", ["old comment"], "2026-04-07T05:00:00Z", "https://reddit.com/comments/abc")
    new_item = make_test_item("Test post", ["new comment"], "2026-04-07T05:05:00Z", "https://reddit.com/comments/abc")
    deduplicated, merged = deduplicate_and_merge([new_item], [old_item])
    assert len(deduplicated) == 1
    assert merged == 1
    assert "old comment" in deduplicated[0].comments
    assert "new comment" in deduplicated[0].comments
    assert deduplicated[0].collected_at == "2026-04-07T05:05:00Z"


def test_deduplicate_merges_unique_comments():
    old_item = make_test_item("Post", ["comment1", "comment2"], "2026-04-07T05:00:00Z")
    new_item = make_test_item("Post", ["comment2", "comment3"], "2026-04-07T05:05:00Z")
    deduplicated, merged = deduplicate_and_merge([new_item], [old_item])
    assert len(deduplicated) == 1
    assert merged == 1
    assert len(deduplicated[0].comments) == 3
    assert set(deduplicated[0].comments) == {"comment1", "comment2", "comment3"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
