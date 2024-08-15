import re
import nltk

class ContextExtractor:
    def __init__(self, context_word_limit=20, strikethrough_marker="~~"):
        self.context_word_limit = context_word_limit
        self.strikethrough_marker = strikethrough_marker
        self.last_known_speaker = ""

    def extract_context(self, paragraphs):
        self.last_known_speaker = ""
        return [self._process_paragraph(paragraphs, i) for i, paragraph in enumerate(paragraphs)]

    def _process_paragraph(self, paragraphs, index):
        current_paragraph = paragraphs[index]
        context_before = self._get_context(paragraphs, index, is_before=True)
        self._update_last_known_speaker(current_paragraph)
        context_after = self._get_context(paragraphs, index, is_before=False)
        return {
            "paragraph": current_paragraph,
            "context_before": context_before,
            "context_after": context_after,
            "cleanup_paragraph": self._remove_strikethrough_text(current_paragraph)
        }

    def _get_context(self, paragraphs, index, is_before):
        if is_before and index > 0:
            return self._extract_relevant_sentences(paragraphs[index - 1], from_start=False)
        elif not is_before and index < len(paragraphs) - 1:
            return self._extract_relevant_sentences(paragraphs[index + 1], from_start=True)
        return ""

    def _extract_relevant_sentences(self, paragraph, from_start):
        sentences = [self._remove_strikethrough_text(s) for s in nltk.sent_tokenize(paragraph)]
        if not from_start:
            sentences.reverse()

        relevant_sentences = []
        word_count = 0
        context_speaker = self._extract_speaker_tag(paragraph) or self.last_known_speaker

        for sentence in sentences:
            speaker = self._extract_speaker_tag(sentence)
            if speaker:
                context_speaker = speaker

            words = sentence.split()
            relevant_sentences.append(sentence)
            word_count += len(words)

            if word_count >= self.context_word_limit and len(relevant_sentences) > 1:
                break

        result = " ".join(relevant_sentences if from_start else reversed(relevant_sentences))
        
        if not self._starts_with_speaker_tag(result):
            result = f"**{context_speaker}:** {result}" if context_speaker else result

        return result.strip()

    def _remove_strikethrough_text(self, text):
        cleaned_text = re.sub(rf"{self.strikethrough_marker}(.*?){self.strikethrough_marker}", "", text)
        return re.sub(r"\s+", " ", cleaned_text).strip()

    def _extract_speaker_tag(self, text):
        match = re.match(r'\*\*(.*?):\*\*', text)
        return match.group(1) if match else ""

    def _starts_with_speaker_tag(self, text):
        return bool(re.match(r'\*\*.*?:\*\*', text))

    def _update_last_known_speaker(self, paragraph):
        speakers = re.findall(r'\*\*(.*?):\*\*', paragraph)
        if speakers:
            self.last_known_speaker = speakers[-1]