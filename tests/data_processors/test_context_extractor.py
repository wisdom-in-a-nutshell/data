import pytest
from src.data_processors.context_extractor import ContextExtractor

class TestContextExtractor:
    @pytest.fixture
    def extractor(self):
        return ContextExtractor()

    @pytest.fixture
    def long_paragraphs(self):
        return [
            "Artificial intelligence (AI) has become an integral part of our daily lives. From voice assistants to recommendation systems, AI technologies are reshaping how we interact with the world. Machine learning algorithms power these systems, constantly improving their performance through data analysis. Natural language processing enables machines to understand and generate human language. Computer vision allows AI to interpret and analyze visual information from the world. Deep learning, a subset of machine learning, has led to significant breakthroughs in various fields. AI is being applied in healthcare to assist with diagnosis and treatment planning. In finance, AI algorithms are used for fraud detection and risk assessment. The automotive industry is leveraging AI for the development of self-driving cars. AI is also transforming education, providing personalized learning experiences for students. However, the rapid advancement of AI also raises ethical concerns. Issues of privacy, bias, and job displacement are at the forefront of discussions. Researchers are working on developing explainable AI to increase transparency in decision-making processes. The potential of AI in scientific research is vast, from drug discovery to climate modeling. As AI continues to evolve, it's crucial to consider its societal impacts. Balancing innovation with responsible development is key to harnessing AI's full potential. The future of AI holds exciting possibilities, but also challenges that we must address.",
            "Climate change is one of the most pressing issues facing our planet today. Rising global temperatures are causing significant shifts in weather patterns worldwide. Melting polar ice caps are contributing to rising sea levels, threatening coastal communities. Extreme weather events, such as hurricanes and droughts, are becoming more frequent and intense. The impact of climate change on biodiversity is profound, with many species facing extinction. Deforestation and industrial activities continue to release large amounts of greenhouse gases. The ocean's ability to absorb carbon dioxide is decreasing, exacerbating the problem. Climate scientists are working tirelessly to model future scenarios and develop mitigation strategies. Renewable energy sources like solar and wind power are crucial in reducing our carbon footprint. Many countries are setting ambitious targets to achieve carbon neutrality in the coming decades. However, international cooperation is essential to address this global challenge effectively. The effects of climate change are not evenly distributed, with developing countries often bearing the brunt. Agriculture and food security are under threat as changing climates affect crop yields. Water scarcity is becoming a major concern in many parts of the world due to altered precipitation patterns. The health impacts of climate change, including the spread of infectious diseases, are a growing concern. Efforts to adapt to climate change are as important as those aimed at mitigation. Urban planning is evolving to create more resilient and sustainable cities. Conservation efforts are crucial to protect vulnerable ecosystems and wildlife. Public awareness and education play a vital role in driving climate action at all levels of society.",
            "The human brain remains one of the most complex and fascinating organs in the body. Neuroscientists are continually uncovering new insights into its structure and function. The brain contains billions of neurons, forming intricate networks that process information. Neuroplasticity, the brain's ability to form new connections, is key to learning and memory. Recent research has shed light on the importance of sleep in cognitive function and memory consolidation. The field of cognitive neuroscience is exploring how the brain gives rise to our thoughts and behaviors. Advances in brain imaging techniques have revolutionized our understanding of brain activity. The study of neurotransmitters has led to new treatments for various neurological disorders. Research into the aging brain is providing insights into maintaining cognitive health in later life. The relationship between gut health and brain function is an emerging area of study. Neurofeedback techniques are being developed to help individuals regulate their brain activity. The concept of brain-computer interfaces holds promise for assisting those with severe motor disabilities. Studies on meditation and mindfulness are revealing their effects on brain structure and function. The field of neuroeconomics is exploring how the brain makes decisions in economic contexts. Researchers are investigating the neural basis of consciousness, one of the greatest mysteries in neuroscience. Understanding the development of the brain from infancy to adulthood is crucial for education and child development. The impact of technology on brain function is a topic of increasing interest and concern. Neurodegenerative diseases like Alzheimer's continue to be a major focus of brain research. The interplay between genetics and environment in shaping brain function is a complex area of study. As our knowledge of the brain grows, so does the potential for new therapies and interventions."
        ]

    @pytest.fixture
    def paragraphs_with_speakers(self):
        return [
            "**Alice:** This is the first paragraph with a speaker.",
            "This is the second paragraph without a speaker tag.",
            "**Bob:** This is the third paragraph with a different speaker.",
            "**Alice:** This paragraph has the first speaker again.",
            "This is the last paragraph without a speaker tag."
        ]

    def test_extract_context_with_long_paragraphs(self, extractor, long_paragraphs):
        result = extractor.extract_context(long_paragraphs)
        assert len(result) == 3
        for i in range(3):
            assert result[i]["paragraph"] == long_paragraphs[i]
            if i > 0:
                assert result[i]["context_before"]
            if i < 2:
                assert result[i]["context_after"]

    @pytest.mark.parametrize("word_limit", [10, 20, 50, 100])
    def test_various_word_limits(self, long_paragraphs, word_limit):
        custom_extractor = ContextExtractor(context_word_limit=word_limit)
        result = custom_extractor.extract_context(long_paragraphs)
        for item in result:
            if item["context_before"]:
                assert len(item["context_before"].split()) >= word_limit
                assert len(item["context_before"].split()) <= word_limit + 20  # Allow some flexibility
            if item["context_after"]:
                assert len(item["context_after"].split()) >= word_limit
                assert len(item["context_after"].split()) <= word_limit + 20  # Allow some flexibility

    def test_edge_cases(self):
        extractor = ContextExtractor()
        # Very short paragraph
        short_result = extractor.extract_context(["Short."])
        assert short_result[0]["context_before"] == ""
        assert short_result[0]["context_after"] == ""

        # Very long sentence
        long_sentence = "This is a very long sentence " * 50
        long_result = extractor.extract_context([long_sentence])
        assert len(long_result[0]["cleanup_paragraph"].split()) >= 20

    def test_strikethrough_removal(self, extractor):
        paragraphs = [
            "This is a ~~strikethrough~~ test.",
            "Another ~~strikethrough~~ ~~test~~ paragraph.",
            "No strikethrough here."
        ]
        result = extractor.extract_context(paragraphs)
        assert "strikethrough" not in result[0]["cleanup_paragraph"]
        assert "strikethrough" not in result[1]["cleanup_paragraph"]
        assert "test" not in result[1]["cleanup_paragraph"]  # "test" should also be removed
        assert result[1]["cleanup_paragraph"] == "Another paragraph."
        assert result[2]["cleanup_paragraph"] == paragraphs[2]

    def test_context_extraction_positions(self, extractor, long_paragraphs):
        result = extractor.extract_context(long_paragraphs)
        
        # First paragraph
        assert result[0]["context_before"] == ""
        assert result[0]["context_after"].startswith("Climate change")
        
        # Middle paragraph
        assert "AI" in result[1]["context_before"]
        assert "The human brain" in result[1]["context_after"]
        
        # Last paragraph
        assert "Conservation efforts" in result[2]["context_before"]
        assert result[2]["context_after"] == ""

    def test_empty_input(self, extractor):
        assert extractor.extract_context([]) == []

    def test_speaker_tag_extraction(self, extractor, paragraphs_with_speakers):
        result = extractor.extract_context(paragraphs_with_speakers)
        
        # Check if speaker tags are correctly extracted and applied, and content is correct
        assert result[0]["context_after"] == "**Alice:** This is the second paragraph without a speaker tag."
        assert result[1]["context_before"] == "**Alice:** This is the first paragraph with a speaker."
        assert result[1]["context_after"] == "**Bob:** This is the third paragraph with a different speaker."
        assert result[2]["context_before"] == "**Alice:** This is the second paragraph without a speaker tag."
        assert result[2]["context_after"] == "**Alice:** This paragraph has the first speaker again."
        assert result[3]["context_before"] == "**Bob:** This is the third paragraph with a different speaker."
        assert result[3]["context_after"] == "**Alice:** This is the last paragraph without a speaker tag."
        assert result[4]["context_before"] == "**Alice:** This paragraph has the first speaker again."

        # Check if the original paragraphs are preserved
        for i, paragraph in enumerate(paragraphs_with_speakers):
            assert result[i]["paragraph"] == paragraph

    def test_speaker_tag_persistence(self, extractor, paragraphs_with_speakers):
        result = extractor.extract_context(paragraphs_with_speakers)
        
        # Check if speaker tags persist across paragraphs without speakers
        assert "**Alice:**" in result[1]["context_before"]
        assert "**Alice:**" in result[4]["context_before"]

    def test_speaker_tag_change(self, extractor):
        paragraphs = [
            "**Alice:** First speaker.",
            "**Bob:** Second speaker.",
            "No speaker here.",
            "**Charlie:** Third speaker."
        ]
        result = extractor.extract_context(paragraphs)
        
        # Check if speaker tags change correctly and content is preserved
        assert result[0]["context_after"] == "**Bob:** Second speaker."
        assert result[1]["context_before"] == "**Alice:** First speaker."
        assert result[1]["context_after"] == "**Bob:** No speaker here."
        assert result[2]["context_before"] == "**Bob:** Second speaker."
        assert result[2]["context_after"] == "**Charlie:** Third speaker."
        assert result[3]["context_before"] == "**Bob:** No speaker here."

        # Check if the original paragraphs are preserved
        for i, paragraph in enumerate(paragraphs):
            assert result[i]["paragraph"] == paragraph

    def test_speaker_tag_format(self, extractor):
        paragraphs = ["**Alice:** This is a test.", "This is another test."]
        result = extractor.extract_context(paragraphs)
        
        # Check if the speaker tag format is correct
        assert result[1]["context_before"].startswith("**Alice:**")
        assert "**Alice:**" in result[0]["context_after"]

    def test_no_speaker_tags(self, extractor):
        paragraphs = ["This is a test.", "This is another test."]
        result = extractor.extract_context(paragraphs)
        
        # Check if contexts are extracted correctly when no speaker tags are present
        assert result[0]["context_after"] == "This is another test."
        assert result[1]["context_before"] == "This is a test."

    def test_speaker_tags_and_strikethrough(self, extractor):
        paragraphs = [
            "**Alice:** This is a ~~strikethrough~~ test.",
            "**Bob:** Another ~~strikethrough~~ paragraph.",
            "**Charlie:** No strikethrough here.",
            "**Alice:** ~~This should be removed~~ but this should remain."
        ]
        result = extractor.extract_context(paragraphs)

        # Check if strikethrough text is removed and speaker tags are preserved
        assert result[0]["cleanup_paragraph"] == "**Alice:** This is a test."
        assert result[1]["cleanup_paragraph"] == "**Bob:** Another paragraph."
        assert result[2]["cleanup_paragraph"] == "**Charlie:** No strikethrough here."
        assert result[3]["cleanup_paragraph"] == "**Alice:** but this should remain."

        # Check if context extraction works correctly with speaker tags and strikethrough
        assert result[0]["context_after"] == "**Bob:** Another paragraph."
        assert result[1]["context_before"] == "**Alice:** This is a test."
        assert result[2]["context_before"] == "**Bob:** Another paragraph."
        assert result[2]["context_after"] == "**Alice:** but this should remain."
        assert result[3]["context_before"] == "**Charlie:** No strikethrough here."

        # Check if original paragraphs are preserved
        for i, paragraph in enumerate(paragraphs):
            assert result[i]["paragraph"] == paragraph