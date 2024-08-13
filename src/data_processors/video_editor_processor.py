import os
import re
from datetime import datetime

import nltk
from slugify import slugify

from src.data_processors.base_processor import BaseDataProcessor
from src.utils.file_utils import ensure_dir

nltk.download("punkt", quiet=True)

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

class VideoEditorProcessor(BaseDataProcessor):
    def __init__(
        self,
        input_folder,
        output_folder,
        intermediate_folder,
        test_mode=False,
    ):
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
        self.get_data(paragraphs_dict)

    def remove_timestamps_and_save(self):
        for root, dirs, files in os.walk(self.input_folder):
            for file in files:
                file_path = os.path.join(root, file)
                with open(file_path, "r") as f:
                    content = f.read()

                # Remove timestamps in the format [00:00:00]
                cleaned_content = re.sub(r"\[\d{2}:\d{2}:\d{2}\]", "", content)

                # Normalize strikethrough text
                cleaned_content = re.sub(r"~~\s+", "~~", cleaned_content)
                cleaned_content = re.sub(r"\s+~~", "~~", cleaned_content)

                # Ensure proper spacing around strikethrough text
                cleaned_content = re.sub(
                    r"(?<!\s)~~(.*?)~~(?! )", r" ~~\1~~ ", cleaned_content
                )

                # Remove all "~~" strings
                cleaned_content = re.sub(r"~~~~", "", cleaned_content)
                # Remove specific speaker names and any content between **<>**
                cleaned_content = re.sub(r"\*\*.*?:\*\*", "", cleaned_content)
                cleaned_content = re.sub(r"<.*?>", "", cleaned_content)
                # Remove any text between "#" and new line
                cleaned_content = re.sub(r"#.*?\n", "", cleaned_content)
                # Remove any text between "##" and new line
                cleaned_content = re.sub(r"##.*?\n", "", cleaned_content)

                # Save the cleaned content to a new file in the intermediate folder
                slugified_filename = slugify(f"cleaned_{file}")
                new_file_path = os.path.join(
                    self.intermediate_folder, f"{slugified_filename}.md"
                )
                with open(new_file_path, "w") as f:
                    f.write(cleaned_content)
                print(f"Cleaned file saved to {new_file_path}")

    def generate_paragraphs(self):
        MAX_PARAGRAPH_LENGTH = 500
        all_paragraphs = {}
        for root, dirs, files in os.walk(self.intermediate_folder):
            for file in files:
                file_path = os.path.join(root, file)
                with open(file_path, "r") as f:
                    content = f.read()

                sentences = nltk.sent_tokenize(content)
                sentences = [
                    " ".join(sentence.strip().split())
                    for sentence in sentences
                    if sentence.strip()
                ]

                # Process each file twice: once normally and once skipping the first sentence
                for suffix, offset in [
                    ("normal", 0),
                    # ("skipped_one", 1),
                    # ("skipped_two", 2),
                    # ("skipped_three", 3),
                    # ("skipped_four", 4),
                ]:
                    paragraphs = []
                    current_paragraph = []
                    word_count = 0
                    in_strikethrough = False

                    # Iterate over sentences, starting from 'offset' to handle skipping
                    for sentence in sentences[offset:]:
                        words = sentence.split()
                        current_strikethrough_count = sentence.count("~~")
                        if current_strikethrough_count > 0:
                            if current_strikethrough_count % 2 != 0:
                                in_strikethrough = not in_strikethrough

                        current_paragraph.append(sentence)
                        word_count += len(words)

                        # Ensure paragraphs do not exceed the max length unless in strikethrough
                        if word_count > MAX_PARAGRAPH_LENGTH and not in_strikethrough:
                            paragraphs.append(" ".join(current_paragraph))
                            current_paragraph = []
                            word_count = 0

                    # Add any remaining content in the current paragraph to paragraphs
                    if current_paragraph:
                        paragraphs.append(" ".join(current_paragraph))

                    # Store paragraphs in dictionary with a unique identifier using suffix
                    all_paragraphs[f"{file}_{suffix}"] = paragraphs

                if self.test_mode:
                    break

        return all_paragraphs

    def clean_strikethrough(self, text):
        return re.sub(r"~~", "", text)

    def calculate_strikethrough_percentage(self, text):
        strikethrough_texts = re.findall(r"~~(.*?)~~", text)
        strikethrough_word_count = sum(
            len(text.split()) for text in strikethrough_texts
        )
        total_word_count = len(text.split())

        if total_word_count == 0:
            return 0  # Avoid division by zero if the text is empty

        percentage = round((strikethrough_word_count / total_word_count) * 100, 2)
        return percentage, total_word_count

    def get_data(self, paragraphs_dict):
        WORD_PERCENTAGE_THRESHOLD = 30
        for file, paragraphs in paragraphs_dict.items():
            print("Processing file: ", file)
            print("The number of paragraphs is: ", len(paragraphs))
            for i, paragraph in enumerate(paragraphs):
                last_two_sentences_of_previous = ""
                first_two_sentences_of_next = ""

                if i > 0:
                    last_two_sentences_of_previous = (
                        self.extract_relevant_sentences_from_end(paragraphs[i - 1])
                    )

                if i < len(paragraphs) - 1:
                    first_two_sentences_of_next = (
                        self.extract_relevant_sentences_from_start(paragraphs[i + 1])
                    )

                paragraph_data = {
                    "input": self.clean_strikethrough(paragraph),
                    "output": paragraph.strip(),
                    "context_before": last_two_sentences_of_previous.strip(),
                    "context_after": first_two_sentences_of_next.strip(),
                }
                # print(json.dumps(paragraph_data, indent=4))

                (
                    strikethrough_percentage,
                    total_word_count,
                ) = self.calculate_strikethrough_percentage(paragraph_data["output"])

                if strikethrough_percentage < WORD_PERCENTAGE_THRESHOLD:
                    merged_input = f"{paragraph_data['context_before']} {paragraph_data['input']} {paragraph_data['context_after']}".strip()
                    merged_output = f"{paragraph_data['context_before']} {paragraph_data['output']} {paragraph_data['context_after']}".strip()

                    total_words_merged_input = len(merged_input.split())
                    total_words_merged_output = len(merged_output.split())
                    total_words = total_words_merged_input + total_words_merged_output

                    # print(f"\nStrikethrough Percentage : {strikethrough_percentage}%, Total Words: {total_word_count}\n")

                    strikethrough_count_in_output = merged_output.count("~~")
                    is_strikethrough_count_even = strikethrough_count_in_output % 2 == 0
                    strikethrough_count_in_input = merged_input.count("~~")

                    # print("Merged Input:", merged_input)
                    # print("\nMerged Output:", merged_output)

                    # print(f"Total number of words in merged input and output: {total_words}")

                    if (
                        is_strikethrough_count_even
                        and strikethrough_count_in_input == 0
                        and total_words_merged_input < 2000
                    ):
                        self.append_data(
                            instruction=PROMPT,
                            input_data=merged_input,
                            response=merged_output,
                        )

                # if i == 2:
                #     break

    def remove_strikethrough_text(self, text):
        cleaned_text = re.sub(r"~~(.*?)~~", "", text)
        cleaned_text = re.sub(r"\s+", " ", cleaned_text)
        return cleaned_text.strip()

    def extract_relevant_sentences_from_start(self, paragraph):
        sentences = nltk.sent_tokenize(paragraph)
        cleaned_sentences = [
            self.remove_strikethrough_text(sentence) for sentence in sentences
        ]
        relevant_sentences = []
        word_count = 0
        for sentence in cleaned_sentences:
            relevant_sentences.append(sentence)
            words = sentence.split()
            if word_count + len(words) > 10:
                break
            word_count += len(words)
        return " ".join(relevant_sentences)

    def extract_relevant_sentences_from_end(self, paragraph):
        sentences = nltk.sent_tokenize(paragraph)
        cleaned_sentences = [
            self.remove_strikethrough_text(sentence) for sentence in sentences
        ]
        relevant_sentences = []
        word_count = 0
        for sentence in reversed(cleaned_sentences):
            words = sentence.split()
            relevant_sentences.insert(
                0, sentence
            )  # Insert at the beginning to maintain order
            if word_count + len(words) > 10:
                break
            word_count += len(words)
        return " ".join(relevant_sentences)


if __name__ == "__main__":
    # Example folder paths
    test_folder_path = "/Users/adi/Documents/GitHub/data/editor/original"
    output_folder_path = (
        "/Users/adi/Documents/GitHub/data/editor/generated"
    )
    further_output_folder_path = (
        "/Users/adi/Documents/GitHub/data/editor/further_processed"
    )
    date = datetime.now().strftime("%b%d_%H").lower()
    file_path = f"/Users/adi/Documents/GitHub/data/editor/finetune/editor_{date}.jsonl"

    cleanup_instance = VideoEditorProcessor(
        test_folder_path,
        output_folder_path,
        further_output_folder_path,
        test_mode=False,
    )
    cleanup_instance.remove_timestamps_and_save()
    paragraphs_dict = cleanup_instance.generate_paragraphs()
    cleanup_instance.get_data(paragraphs_dict)
    cleanup_instance.generate_jsonl(file_path, huggingface_format=False)
