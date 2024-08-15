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
        last_speaker = None

        for sentence in sentences:
            sentence_words = sentence.split()
            sentence_word_count = len(sentence_words)

            # Check for speaker tag anywhere in the sentence
            speaker_match = re.search(r'\*\*(.*?):\*\*', sentence)
            if speaker_match:
                last_speaker = speaker_match.group(1)

            # If starting a new paragraph, add the last known speaker
            if not current_paragraph and last_speaker:
                speaker_tag = f"**{last_speaker}:**"
                current_paragraph.append(speaker_tag)
                word_count = len(speaker_tag.split())

            # Check if adding this sentence would exceed the max length
            if word_count + sentence_word_count > self.max_paragraph_length:
                # End the current paragraph
                paragraphs.append(" ".join(current_paragraph))
                # Start a new paragraph with the last known speaker
                current_paragraph = [f"**{last_speaker}:**"] if last_speaker else []
                word_count = len(current_paragraph[0].split()) if current_paragraph else 0

            current_paragraph.append(sentence)
            word_count += sentence_word_count

            # If the current sentence alone exceeds the limit, force a paragraph break
            if sentence_word_count > self.max_paragraph_length:
                paragraphs.append(" ".join(current_paragraph))
                current_paragraph = []
                word_count = 0

        if current_paragraph:
            paragraphs.append(" ".join(current_paragraph))

        return paragraphs