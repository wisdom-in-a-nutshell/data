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
            context = self._extract_relevant_sentences(paragraphs[index - 1], from_start=False)
            if not self._extract_speaker_tag(context):
                self.last_known_speaker = self.last_known_speaker
            return context
        elif not is_before and index < len(paragraphs) - 1:
            return self._extract_relevant_sentences(paragraphs[index + 1], from_start=True)
        return ""

    def _extract_relevant_sentences(self, paragraph, from_start):
        sentences = nltk.sent_tokenize(paragraph)
        if not from_start:
            sentences.reverse()

        relevant_sentences = []
        word_count = 0
        context_speaker = None

        for sentence in sentences:
            cleaned_sentence = self._remove_strikethrough_text(sentence)
            
            if not context_speaker:
                context_speaker = self._extract_speaker_tag(cleaned_sentence)

            relevant_sentences.append(cleaned_sentence)
            word_count += len(cleaned_sentence.split())

            if word_count >= self.context_word_limit and len(relevant_sentences) > 1:
                break

        result = " ".join(relevant_sentences if from_start else reversed(relevant_sentences))
        
        # Add the speaker tag only if there isn't one at the beginning
        if not self._starts_with_speaker_tag(result):
            if context_speaker:
                result = f"**{context_speaker}:** {result}"
            elif self.last_known_speaker:
                result = f"**{self.last_known_speaker}:** {result}"

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
        elif self._extract_speaker_tag(paragraph):
            self.last_known_speaker = self._extract_speaker_tag(paragraph)