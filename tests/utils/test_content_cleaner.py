import pytest
from src.utils.content_cleaner import ContentCleaner

class TestContentCleaner:
    @pytest.fixture
    def cleaner(self):
        return ContentCleaner()

    def test_remove_timestamps(self, cleaner):
        content = "Hello [00:01:23] world [12:34:56]"
        cleaned = cleaner.clean_content(content)
        assert cleaned == "Hello  world "

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
        assert cleaned == "This has  empty strikethrough"

    def test_remove_speaker_names(self, cleaner):
        content = "**John:** Hello **<Mary>:** Hi"
        cleaned = cleaner.clean_content(content)
        assert cleaned == " Hello  Hi"

    def test_remove_single_line_comments(self, cleaner):
        content = "This is code\n# This is a comment\nMore code"
        cleaned = cleaner.clean_content(content)
        assert cleaned == "This is code\nMore code"

    def test_remove_section_headers(self, cleaner):
        content = "## Section 1\nContent\n## Section 2\nMore content"
        cleaned = cleaner.clean_content(content)
        assert cleaned == "Content\nMore content"

    def test_combined_cleaning(self, cleaner):
        content = """
        [00:01:23] **Speaker:** Hello ~~  world  ~~
        # This is a comment
        ## Section header
        This is~~text~~with issues and ~~~~ empty tags
        """
        expected = """
         Hello ~~world~~
        
        This is ~~text~~ with issues and  empty tags
        """
        cleaned = cleaner.clean_content(content)
        assert cleaned.strip() == expected.strip()
