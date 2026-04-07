import os
import tempfile

from src.models import ProcessedTikTokItem, RawTikTokItem
from src.storage import save_processed_items, save_raw_items


def test_storage_writes_raw_and_processed_files():
    raw_item = RawTikTokItem(
        platform="reddit",
        source_url="https://www.reddit.com/r/artificial/",
        page_text="text",
        raw_html="<html></html>",
        extracted_fields={"caption": "test"},
        collected_at="2026-04-07T20:00:00Z",
    )
    processed_item = ProcessedTikTokItem(
        platform="reddit",
        source_url="https://www.reddit.com/r/artificial/",
        video_url="https://www.reddit.com/r/artificial/comments/abc/post/",
        creator_handle="u/example",
        caption="test",
        hashtags=["ai"],
        comments=["nice"],
        transcript=None,
        video_summary="summary",
        topic="other",
        sentiment="neutral",
        keywords=["test"],
        signal_tags=["ai"],
        collected_at="2026-04-07T20:00:00Z",
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["OUTPUT_DIR"] = tmpdir
        raw_paths = save_raw_items([raw_item])
        processed_paths = save_processed_items([processed_item])
        assert len(raw_paths) == 1
        assert len(processed_paths) == 1
        assert os.path.exists(raw_paths[0])
        assert os.path.exists(processed_paths[0])
