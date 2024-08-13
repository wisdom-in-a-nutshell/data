import os
import re
from datetime import datetime
import nltk
from slugify import slugify
from src.data_processors.base_processor import BaseDataProcessor
from src.utils.file_utils import ensure_dir

nltk.download("punkt", quiet=True)

class VideoEditorProcessor(BaseDataProcessor):
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

    MAX_PARAGRAPH_LENGTH = 500
    WORD_PERCENTAGE_THRESHOLD = 30

    def __init__(self, input_folder, output_folder, intermediate_folder, test_mode=False):
        super().__init__()
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.intermediate_folder = intermediate_folder
        self.test_mode = test_mode

        ensure_dir(self.output_folder)
        ensure_dir(self.intermediate_folder)

    def process_data(self):
        self.remove_timestamps_and_save()
        paragraphs_dict = self.generate_paragraphs()
        self.process_paragraphs(paragraphs_dict)

    def remove_timestamps_and_save(self):
        for root, dirs, files in os.walk(self.input_folder):
            for file in files:
                self._process_single_file(os.path.join(root, file))

    def _process_single_file(self, file_path):
        with open(file_path, "r") as f:
            content = f.read()

        cleaned_content = self._clean_content(content)

        slugified_filename = slugify(f"cleaned_{os.path.basename(file_path)}")
        new_file_path = os.path.join(self.intermediate_folder, f"{slugified_filename}.md")
        
        with open(new_file_path, "w") as f:
            f.write(cleaned_content)
        print(f"Cleaned file saved to {new_file_path}")

    def _clean_content(self, content):
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

    def generate_paragraphs(self):
        all_paragraphs = {}
        for root, dirs, files in os.walk(self.intermediate_folder):
            for file in files:
                file_path = os.path.join(root, file)
                all_paragraphs.update(self._process_file_paragraphs(file_path))
                if self.test_mode:
                    break
        return all_paragraphs

    def _process_file_paragraphs(self, file_path):
        with open(file_path, "r") as f:
            content = f.read()

        sentences = [s.strip() for s in nltk.sent_tokenize(content) if s.strip()]
        paragraphs = self._split_into_paragraphs(sentences)

        return {f"{os.path.basename(file_path)}_normal": paragraphs}

    def _split_into_paragraphs(self, sentences):
        paragraphs = []
        current_paragraph = []
        word_count = 0
        in_strikethrough = False

        for sentence in sentences:
            words = sentence.split()
            current_strikethrough_count = sentence.count("~~")
            
            if current_strikethrough_count % 2 != 0:
                in_strikethrough = not in_strikethrough

            current_paragraph.append(sentence)
            word_count += len(words)

            if word_count > self.MAX_PARAGRAPH_LENGTH and not in_strikethrough:
                paragraphs.append(" ".join(current_paragraph))
                current_paragraph = []
                word_count = 0

        if current_paragraph:
            paragraphs.append(" ".join(current_paragraph))

        return paragraphs

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

    def _get_context_before(self, paragraphs, index):
        if index > 0:
            return self._extract_relevant_sentences_from_end(paragraphs[index - 1])
        return ""

    def _get_context_after(self, paragraphs, index):
        if index < len(paragraphs) - 1:
            return self._extract_relevant_sentences_from_start(paragraphs[index + 1])
        return ""

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
        strikethrough_count_in_output = merged_output.count("~~")
        strikethrough_count_in_input = merged_input.count("~~")

        return (
            strikethrough_count_in_output % 2 == 0
            and strikethrough_count_in_input == 0
            and total_words_merged_input < 2000
        )

    @staticmethod
    def _clean_strikethrough(text):
        return re.sub(r"~~", "", text)

    @staticmethod
    def _calculate_strikethrough_percentage(text):
        strikethrough_texts = re.findall(r"~~(.*?)~~", text)
        strikethrough_word_count = sum(len(text.split()) for text in strikethrough_texts)
        total_word_count = len(text.split())

        if total_word_count == 0:
            return 0, 0

        percentage = round((strikethrough_word_count / total_word_count) * 100, 2)
        return percentage, total_word_count

    def _remove_strikethrough_text(self, text):
        cleaned_text = re.sub(r"~~(.*?)~~", "", text)
        cleaned_text = re.sub(r"\s+", " ", cleaned_text)
        return cleaned_text.strip()

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
            
            if word_count + len(words) > 10:
                break
            word_count += len(words)
        
        return " ".join(relevant_sentences)

if __name__ == "__main__":
    # Example usage
    test_folder_path = "/Users/adi/Documents/GitHub/data/editor/original"
    output_folder_path = "/Users/adi/Documents/GitHub/data/editor/generated"
    further_output_folder_path = "/Users/adi/Documents/GitHub/data/editor/further_processed"
    date = datetime.now().strftime("%b%d_%H").lower()
    file_path = f"/Users/adi/Documents/GitHub/data/editor/finetune/editor_{date}.jsonl"

    processor = VideoEditorProcessor(
        test_folder_path,
        output_folder_path,
        further_output_folder_path,
        test_mode=False,
    )
    processor.process_data()
    processor.generate_jsonl(file_path, huggingface_format=False)