import nltk
import re

class ParagraphGenerator:
    MAX_PARAGRAPH_LENGTH = 1000

    def __init__(self):
        self.max_paragraph_length = self.MAX_PARAGRAPH_LENGTH

    def generate_paragraphs(self, processed_files):
        all_paragraphs = {}
        for file, content in processed_files.items():
            all_paragraphs.update(self._process_file_paragraphs(file, content))
        return all_paragraphs

    def _process_file_paragraphs(self, file, content):
        sentences = [s.strip() for s in nltk.sent_tokenize(content) if s.strip()]
        paragraphs = self._split_into_paragraphs(sentences)
        return {f"{file}_normal": paragraphs}

    def _split_into_paragraphs(self, sentences):
        paragraphs = []
        current_paragraph = []
        word_count = 0
        in_strikethrough = False
        last_speaker = None

        for sentence in sentences:
            sentence_words = sentence.split()
            sentence_word_count = len(sentence_words)

            # Check for speaker tag
            speaker_match = re.match(r'\*\*(.*?):\*\*', sentence)
            if speaker_match:
                last_speaker = speaker_match.group(1)

            if word_count + sentence_word_count > self.max_paragraph_length and not in_strikethrough:
                # Add the current paragraph to the list
                paragraphs.append(" ".join(current_paragraph))
                # Start a new paragraph, adding the last known speaker if available
                current_paragraph = []
                if last_speaker and not sentence.startswith(f"**{last_speaker}:**"):
                    current_paragraph.append(f"**{last_speaker}:**")
                word_count = 0

            current_paragraph.append(sentence)
            word_count += sentence_word_count

            current_strikethrough_count = sentence.count("~~")
            if current_strikethrough_count % 2 != 0:
                in_strikethrough = not in_strikethrough

        if current_paragraph:
            paragraphs.append(" ".join(current_paragraph))

        return paragraphs