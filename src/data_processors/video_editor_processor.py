import re
from datetime import datetime
import nltk
from src.data_processors.base_processor import BaseDataProcessor
from src.data_processors.file_processor import FileProcessor
from src.data_processors.paragraph_generator import ParagraphGenerator
from src.utils.file_utils import ensure_dir

nltk.download("punkt", quiet=True)

class VideoEditorProcessor(BaseDataProcessor):
    # Constants
    WORD_PERCENTAGE_THRESHOLD = 90
    MAX_WORDS_PER_PARAGRAPH = 12000
    CONTEXT_WORD_LIMIT = 20
    STRIKETHROUGH_MARKER = "~~"

    PROMPT = """
    <role>
    You are an AI language model acting as an editor to refine podcast clip transcripts for smooth and coherent video creation. Your task is to remove unnecessary elements such as filler words, repeated words, phrases, and language that digress from the main content without contributing to the core message. The goal is to maintain the overall flow and understanding of the content.
    </role>

    <steps>
    1. Read the text and mark parts to remove using ~~strikethrough~~ (double tildes)
    2. Focus on taking out filler words, repeated words, and off-topic parts
    3. Make sure the edited text matches the original, with marked parts for removal
    4. Don't add, swap, or move words
    5. Keep the total word count the same for input and output
    6. Give the edited text with strikethrough, without comments
    </steps>

    <key_points>
    - Strikethrough helps guide precise video editing
    - Keeping word count is key for text accuracy and correct editing
    </key_points>

    <output>
    Give the edited text with strikethrough formatting.
    </output>
    """

    def __init__(self, input_folder):
        super().__init__()
        self.input_folder = input_folder
        self.file_processor = FileProcessor(input_folder)
        self.paragraph_generator = ParagraphGenerator()

    def process_data(self):
        processed_files = self.file_processor.process_and_clean_files()
        paragraphs_dict = self.paragraph_generator.generate_paragraphs(processed_files)
        self.process_paragraphs(paragraphs_dict)

    def process_paragraphs(self, paragraphs_dict):
        for file, paragraphs in paragraphs_dict.items():
            print(f"Processing file: {file}")
            print(f"The number of paragraphs is: {len(paragraphs)}")
            
            for i, paragraph in enumerate(paragraphs):
                self._process_single_paragraph(paragraphs, i)

    def _process_single_paragraph(self, paragraphs, index):
        paragraph = paragraphs[index]
        context_before = self._get_context_before(paragraphs, index)
        context_after = self._get_context_after(paragraphs, index)

        paragraph_data = {
            "input": self._clean_strikethrough(paragraph),
            "output": paragraph.strip(),
            "context_before": context_before,
            "context_after": context_after,
        }

        strikethrough_percentage, _ = self._calculate_strikethrough_percentage(paragraph_data["output"])

        if strikethrough_percentage < self.WORD_PERCENTAGE_THRESHOLD:
            self._process_valid_paragraph(paragraph_data)

    def _process_valid_paragraph(self, paragraph_data):
        merged_input = f"{paragraph_data['context_before']} {paragraph_data['input']} {paragraph_data['context_after']}".strip()
        merged_output = f"{paragraph_data['context_before']} {paragraph_data['output']} {paragraph_data['context_after']}".strip()

        if self._is_valid_for_processing(merged_input, merged_output):
            self.append_data(
                instruction=self.PROMPT,
                input_data=merged_input,
                response=merged_output,
            )

    def _is_valid_for_processing(self, merged_input, merged_output):
        total_words_merged_input = len(merged_input.split())
        strikethrough_count_in_output = merged_output.count(self.STRIKETHROUGH_MARKER)
        strikethrough_count_in_input = merged_input.count(self.STRIKETHROUGH_MARKER)

        return (
            strikethrough_count_in_output % 2 == 0
            and strikethrough_count_in_input == 0
            and total_words_merged_input < self.MAX_WORDS_PER_PARAGRAPH
        )

    @staticmethod
    def _clean_strikethrough(text):
        return re.sub(rf"{VideoEditorProcessor.STRIKETHROUGH_MARKER}", "", text)

    @staticmethod
    def _calculate_strikethrough_percentage(text):
        strikethrough_texts = re.findall(rf"{VideoEditorProcessor.STRIKETHROUGH_MARKER}(.*?){VideoEditorProcessor.STRIKETHROUGH_MARKER}", text)
        strikethrough_word_count = sum(len(text.split()) for text in strikethrough_texts)
        total_word_count = len(text.split())

        if total_word_count == 0:
            return 0, 0

        percentage = round((strikethrough_word_count / total_word_count) * 100, 2)
        return percentage, total_word_count

    def _remove_strikethrough_text(self, text):
        cleaned_text = re.sub(rf"{self.STRIKETHROUGH_MARKER}(.*?){self.STRIKETHROUGH_MARKER}", "", text)
        cleaned_text = re.sub(r"\s+", " ", cleaned_text)
        return cleaned_text.strip()

    def _get_context_before(self, paragraphs, index):
        if index > 0:
            return self._extract_relevant_sentences_from_end(paragraphs[index - 1])
        return ""

    def _get_context_after(self, paragraphs, index):
        if index < len(paragraphs) - 1:
            return self._extract_relevant_sentences_from_start(paragraphs[index + 1])
        return ""

    def _extract_relevant_sentences_from_start(self, paragraph):
        return self._extract_relevant_sentences(paragraph, from_start=True)

    def _extract_relevant_sentences_from_end(self, paragraph):
        return self._extract_relevant_sentences(paragraph, from_start=False)

    def _extract_relevant_sentences(self, paragraph, from_start=True):
        sentences = nltk.sent_tokenize(paragraph)
        cleaned_sentences = [self._remove_strikethrough_text(sentence) for sentence in sentences]
        
        if not from_start:
            cleaned_sentences = reversed(cleaned_sentences)

        relevant_sentences = []
        word_count = 0
        
        for sentence in cleaned_sentences:
            words = sentence.split()
            if from_start:
                relevant_sentences.append(sentence)
            else:
                relevant_sentences.insert(0, sentence)
            
            if word_count + len(words) > self.CONTEXT_WORD_LIMIT:
                break
            word_count += len(words)
        
        return " ".join(relevant_sentences)

if __name__ == "__main__":
    # Example usage
    test_folder_path = "/Users/adi/Documents/GitHub/data/editor/original"
    date = datetime.now().strftime("%b%d_%H").lower()
    file_path = f"/Users/adi/Documents/GitHub/data/editor/finetune/editor_{date}.jsonl"

    processor = VideoEditorProcessor(
        input_folder=test_folder_path,
    )
    processor.process_data()
    processor.generate_jsonl(file_path, huggingface_format=False)