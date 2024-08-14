import pytest

from src.data_processors.file_processor import FileProcessor
from src.utils.content_cleaner import ContentCleaner

class TestContentCleaner:
    @pytest.fixture
    def cleaner(self):
        return FileProcessor("dummy_file.txt")

    def test_remove_timestamps(self, cleaner):
        content = "Hello [00:01:23] world [12:34:56]"
        cleaned = cleaner.clean_content(content)
        assert cleaned == "Hello world"

    def test_normalize_strikethrough(self, cleaner):
        content = "This is ~~ strikethrough ~~ text"
        cleaned = cleaner.clean_content(content)
        assert cleaned == "This is ~~strikethrough~~ text"

    def test_ensure_proper_spacing_strikethrough(self, cleaner):
        content = "This is~~strikethrough~~text"
        cleaned = cleaner.clean_content(content)
        assert cleaned == "This is ~~strikethrough~~ text"

    def test_remove_empty_strikethrough(self, cleaner):
        content = "This has ~~~~ empty strikethrough"
        cleaned = cleaner.clean_content(content)
        assert cleaned == "This has empty strikethrough"

    def test_remove_speaker_names(self, cleaner):
        content = "**John:** Hello **<Mary>:** Hi"
        cleaned = cleaner.clean_content(content)
        assert cleaned == "Hello Hi"

    def test_remove_single_line_comments(self, cleaner):
        content = "This is code\n# This is a comment\nMore code"
        cleaned = cleaner.clean_content(content)
        assert cleaned == "This is code\n\nMore code"

    def test_remove_section_headers(self, cleaner):
        content = "## Section 1\nContent\n## Section 2\nMore content"
        cleaned = cleaner.clean_content(content)
        assert cleaned == "Content\n\nMore content"

    def test_combined_cleaning(self, cleaner):
        content = """
        [00:01:23] **Speaker:** Hello ~~  world  ~~
        # This is a comment
        ## Section header
        This is~~text~~with issues and ~~~~ empty tags
        """
        expected = "Hello ~~world~~\n\nThis is ~~text~~ with issues and empty tags"
        cleaned = cleaner.clean_content(content)
        assert cleaned.strip() == expected.strip()

    def test_multiple_empty_lines(self, cleaner):
        content = "Hello\n\n\nWorld"
        cleaned = cleaner.clean_content(content)
        assert cleaned == "Hello\n\n\nWorld"  # Ensure multiple empty lines are reduced

    def test_empty_string(self, cleaner):
        content = ""
        cleaned = cleaner.clean_content(content)
        assert cleaned == ""  # Ensure empty string returns empty

    def test_only_timestamps(self, cleaner):
        content = "[00:01:23] [12:34:56]"
        cleaned = cleaner.clean_content(content)
        assert cleaned == ""  # Ensure only timestamps return empty

    def test_malformed_strikethrough(self, cleaner):
        content = "This is ~~strikethrough text without closing"
        cleaned = cleaner.clean_content(content)
        assert cleaned == "This is ~~strikethrough text without closing"  # Ensure it remains unchanged