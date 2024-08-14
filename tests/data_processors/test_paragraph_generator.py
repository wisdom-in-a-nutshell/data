import pytest
from src.data_processors.paragraph_generator import ParagraphGenerator

class TestParagraphGenerator:
    @pytest.fixture
    def paragraph_generator(self):
        return ParagraphGenerator()

    def test_generate_paragraphs(self, paragraph_generator):
        processed_files = {
            "file1.txt": "This is a test sentence. Another sentence here. Yet another one.",
            "file2.txt": "Short sentence. " * (ParagraphGenerator.MAX_PARAGRAPH_LENGTH // 2)
        }
        result = paragraph_generator.generate_paragraphs(processed_files)
        
        assert "file1.txt_normal" in result
        assert "file2.txt_normal" in result
        assert len(result["file1.txt_normal"]) == 1
        assert len(result["file2.txt_normal"]) == 1

    def test_split_into_paragraphs_at_limit(self, paragraph_generator):
        words_per_sentence = 5
        sentences = ["Short sentence. "] * (ParagraphGenerator.MAX_PARAGRAPH_LENGTH // words_per_sentence)
        paragraphs = paragraph_generator._split_into_paragraphs(sentences)
        
        assert len(paragraphs) == 1
        assert len(paragraphs[0].split()) <= ParagraphGenerator.MAX_PARAGRAPH_LENGTH
        
    def test_split_into_paragraphs_exceed_limit(self, paragraph_generator):
        words_per_sentence = 5
        sentences = ["Short sentence. "] * (ParagraphGenerator.MAX_PARAGRAPH_LENGTH // words_per_sentence + 1)
        paragraphs = paragraph_generator._split_into_paragraphs(sentences)
        
        assert len(paragraphs) == 2
        assert len(paragraphs[0].split()) <= ParagraphGenerator.MAX_PARAGRAPH_LENGTH
        assert len(paragraphs[1].split()) <= ParagraphGenerator.MAX_PARAGRAPH_LENGTH
        assert len(paragraphs[1].split()) > 0

    def test_split_with_strikethrough(self, paragraph_generator):
        sentences = [
            "Normal sentence.",
            "~~Start strikethrough~~ middle ~~end strikethrough~~.",
            "Another normal sentence.",
            "~~Strikethrough~~ that ~~spans~~ multiple ~~sentences~~.",
            "Final sentence."
        ]
        paragraphs = paragraph_generator._split_into_paragraphs(sentences)
        
        assert len(paragraphs) == 1  # Should not split due to strikethrough
        assert "~~Start strikethrough~~ middle ~~end strikethrough~~." in paragraphs[0]
        assert "~~Strikethrough~~ that ~~spans~~ multiple ~~sentences~~." in paragraphs[0]

    def test_empty_input(self, paragraph_generator):
        processed_files = {}
        result = paragraph_generator.generate_paragraphs(processed_files)
        assert result == {}

    def test_single_sentence_per_file(self, paragraph_generator):
        processed_files = {
            "file1.txt": "Just one sentence.",
            "file2.txt": "Another single sentence."
        }
        result = paragraph_generator.generate_paragraphs(processed_files)
        assert len(result["file1.txt_normal"]) == 1
        assert len(result["file2.txt_normal"]) == 1

    def test_split_with_varying_sentence_lengths(self, paragraph_generator):
        sentences = [
            "This is a short sentence.",  # 5 words
            "This sentence is a bit longer and contains more words than the previous one.",  # 12 words
            "Now we have a very long sentence that almost reaches the maximum paragraph length limit set in our ParagraphGenerator class." * (ParagraphGenerator.MAX_PARAGRAPH_LENGTH // 20),  # Force split
            "Another short sentence.",  # 3 words
            "One more medium-length sentence to add some variety to our test case.",  # 11 words
            "Finally, we'll add another very long sentence to push the total word count over the limit." * (ParagraphGenerator.MAX_PARAGRAPH_LENGTH // 15)  # Force split
        ]
        
        paragraphs = paragraph_generator._split_into_paragraphs(sentences)
        
        assert len(paragraphs) >= 2
        
        for paragraph in paragraphs:
            assert len(paragraph.split()) <= ParagraphGenerator.MAX_PARAGRAPH_LENGTH

        total_words = sum(len(paragraph.split()) for paragraph in paragraphs)
        expected_word_count = sum(len(sentence.split()) for sentence in sentences)
        assert total_words == expected_word_count

    def test_split_with_speaker_tags_force_split(self, paragraph_generator):
        sentences = [
            "**Alice:** This is Alice speaking.",
            "She continues for a bit.",
            "**Bob:** Now Bob is talking.",
            "He says something else.",
            f"**Alice:** {'Alice speaks again. ' * 200}",  # Force split
            "**Bob:** Bob chimes in after the split.",
            "An untagged sentence follows.",
            "**Charlie:** Charlie joins the conversation."
        ]* 100
        paragraphs = paragraph_generator._split_into_paragraphs(sentences)
        
        for paragraph in paragraphs:
            assert len(paragraph.split()) <= ParagraphGenerator.MAX_PARAGRAPH_LENGTH
            assert paragraph.startswith("**Alice:**") or paragraph.startswith("**Bob:**") or paragraph.startswith("**Charlie:**")

    def test_multiple_speakers_multiple_splits(self, paragraph_generator):
        sequence = [
            "**Alice:** Alice speaks.",
            "She continues without a tag.",
            "**Bob:** Bob responds.",
            "An untagged sentence appears.",
            "**Charlie:** Charlie joins.",
            "More untagged content.",
            "**Alice:** Alice speaks again.",
            "**Bob:** Bob responds again.",
            "Yet another untagged sentence.",
            "**Charlie:** Charlie joins again.",
        ]
        sentences = sequence * 20  # Repeat this sequence 20 times to ensure multiple splits
        paragraphs = paragraph_generator._split_into_paragraphs(sentences)
        
        for paragraph in paragraphs:
            assert len(paragraph.split()) <= ParagraphGenerator.MAX_PARAGRAPH_LENGTH
            assert paragraph.startswith("**Alice:**") or paragraph.startswith("**Bob:**") or paragraph.startswith("**Charlie:**")

    def test_mix_of_tagged_and_untagged_sentences(self, paragraph_generator):
        sentences = [
            "**Alice:** Alice starts the conversation.",
            "This is an untagged sentence.",
            "**Bob:** Bob joins in.",
            "Another untagged sentence.",
            f"{'Yet another untagged sentence. ' * 100}",
            "**Charlie:** Charlie adds to the discussion.",
            f"{'More untagged content. ' * 100}",
            "**Alice:** Alice speaks again after the split.",
            "A final untagged sentence to conclude."
        ]
        paragraphs = paragraph_generator._split_into_paragraphs(sentences)
        
        for paragraph in paragraphs:
            assert len(paragraph.split()) <= ParagraphGenerator.MAX_PARAGRAPH_LENGTH
            assert paragraph.startswith("**Alice:**") or paragraph.startswith("**Bob:**") or paragraph.startswith("**Charlie:**")