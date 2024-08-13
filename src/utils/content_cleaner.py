import re

class ContentCleaner:
    @staticmethod
    def clean_content(content):
        # Remove timestamps in the format [00:00:00]
        content = re.sub(r"\[\d{2}:\d{2}:\d{2}\]", "", content)

        # Normalize strikethrough text by removing extra spaces
        content = re.sub(r"~~\s+", "~~", content)  # Remove spaces after ~~
        content = re.sub(r"\s+~~", "~~", content)  # Remove spaces before ~~

        # Ensure proper spacing around strikethrough text
        content = re.sub(r"(?<!\s)~~(.*?)~~(?! )", r" ~~\1~~ ", content)

        # Remove empty strikethrough tags
        content = re.sub(r"~~~~", "", content)

        # Remove speaker names and any content between **<>**
        content = re.sub(r"\*\*.*?:\*\*", "", content)
        content = re.sub(r"<.*?>", "", content)

        # Remove any text between "#" and new line (single-line comments)
        content = re.sub(r"#.*?\n", "", content)

        # Remove any text between "##" and new line (section headers)
        content = re.sub(r"##.*?\n", "", content)

        return content