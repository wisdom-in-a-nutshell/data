import re
from datetime import datetime
import textwrap
import nltk
from src.data_processors.base_processor import BaseDataProcessor
from src.data_processors.context_extractor import ContextExtractor
from src.data_processors.file_processor import FileProcessor
from src.data_processors.paragraph_generator import ParagraphGenerator

nltk.download("punkt", quiet=True)


class VideoEditorProcessor(BaseDataProcessor):
    # Constants
    WORD_PERCENTAGE_THRESHOLD = 60
    MAX_WORDS_PER_PARAGRAPH = 12000
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
        self.context_extractor = ContextExtractor()

    def process_data(self):
        processed_files = self.file_processor.process_and_clean_files()
        paragraphs_dict = self.paragraph_generator.generate_paragraphs(processed_files)
        self.process_paragraphs(paragraphs_dict)

    def process_paragraphs(self, paragraphs_dict):
        for file, paragraphs in paragraphs_dict.items():
            print(f"Processing file: {file}")
            print(f"The number of paragraphs is: {len(paragraphs)}")
            
            context_data = self.context_extractor.extract_context(paragraphs)
            for paragraph_context in context_data:
                self._process_single_paragraph(paragraph_context)

    def _process_single_paragraph(self, paragraph_context):
        paragraph_data = {
            "input": self._clean_strikethrough(paragraph_context["paragraph"]),
            "output": paragraph_context["paragraph"].strip(),
            "context_before": paragraph_context["context_before"],
            "context_after": paragraph_context["context_after"],
        }

        strikethrough_percentage, _ = self._calculate_strikethrough_percentage(paragraph_data["output"])
        if strikethrough_percentage < self.WORD_PERCENTAGE_THRESHOLD:
            # print(f"Strikethrough percentage: {strikethrough_percentage}")
            self._process_valid_paragraph(paragraph_data, strikethrough_percentage)

    def _process_valid_paragraph(self, paragraph_data, strikethrough_percentage):
        merged_input = paragraph_data['input'].strip()
        merged_output = paragraph_data['output'].strip()

        if self.STRIKETHROUGH_MARKER not in paragraph_data['context_before']:
            merged_input = f"{paragraph_data['context_before']} {merged_input}"
            merged_output = f"{paragraph_data['context_before']} {merged_output}"

        if self.STRIKETHROUGH_MARKER not in paragraph_data['context_after']:
            merged_input = f"{merged_input} {paragraph_data['context_after']}"
            merged_output = f"{merged_output} {paragraph_data['context_after']}"



        if strikethrough_percentage > 40:
            print("<raw_transcript>")
            print(textwrap.fill(merged_input, width=80))
            print("</raw_transcript>")

            print("<edited_transcript>")
            print(textwrap.fill(merged_output, width=80))
            print("</edited_transcript>")


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