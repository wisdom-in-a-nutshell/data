import os
import re

from src.utils.content_cleaner import ContentCleaner


class FileProcessor:
    def __init__(self, input_folder):
        self.input_folder = input_folder
        self.content_cleaner = ContentCleaner()

    def process_and_clean_files(self):
        processed_files = {}
        for root, dirs, files in os.walk(self.input_folder):
            for file in files:
                file_path = os.path.join(root, file)
                processed_content = self._process_single_file(file_path)
                processed_files[file] = processed_content
        return processed_files

    def _process_single_file(self, file_path):
        with open(file_path, "r") as f:
            content = f.read()

        cleaned_content = self.clean_content(content)
        return cleaned_content

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
        content = re.sub(r"#.*?$", "", content, flags=re.MULTILINE)

        # Remove any text between "##" and new line (section headers)
        content = re.sub(r"##.*?$", "", content, flags=re.MULTILINE)

        # Normalize spaces after cleaning (preserve newlines)
        content = re.sub(r'[ \t]+', ' ', content)  # Normalize multiple spaces to a single space
        content = re.sub(r' *\n *', '\n', content)  # Remove spaces around newlines

        return content.strip()  # Trim leading and trailing spaces and newlines