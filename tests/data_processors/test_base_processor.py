import pytest
from src.data_processors.base_processor import BaseDataProcessor

class TestProcessor(BaseDataProcessor):
    def process_file(self, input_file, output_file):
        pass  # Implement a dummy method for testing

def test_base_processor_initialization():
    processor = TestProcessor()
    assert isinstance(processor, BaseDataProcessor)

def test_base_processor_abstract_method():
    with pytest.raises(TypeError):
        BaseDataProcessor()