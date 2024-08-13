import pytest
from src.data_processors.video_editor_processor import VideoEditorProcessor

@pytest.fixture
def processor():
    return VideoEditorProcessor()

def test_remove_timestamps(processor):
    input_text = "00:00:01 Hello 00:00:05 World"
    expected_output = "Hello World"
    assert processor.remove_timestamps(input_text) == expected_output

def test_split_into_paragraphs(processor):
    input_text = "First sentence. Second sentence.\n\nThird sentence."
    expected_output = ["First sentence. Second sentence.", "Third sentence."]
    assert processor.split_into_paragraphs(input_text) == expected_output

def test_process_paragraph(processor):
    input_paragraph = "Um, this is like, you know, a test paragraph."
    expected_output = "This is a test paragraph."
    assert processor.process_paragraph(input_paragraph) == expected_output

def test_process_file(processor, tmp_path):
    input_file = tmp_path / "input.txt"
    input_file.write_text("00:00:01 Hello 00:00:05 World\n\nUm, this is a test.")
    
    output_file = tmp_path / "output.jsonl"
    processor.process_file(str(input_file), str(output_file))
    
    assert output_file.exists()
    content = output_file.read_text()
    assert "Hello World" in content
    assert "This is a test." in content