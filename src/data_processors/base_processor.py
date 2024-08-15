import json
import logging
from abc import ABC, abstractmethod

logging.basicConfig(level=logging.INFO)

class BaseDataProcessor(ABC):
    def __init__(self):
        self.data_list = []

    @abstractmethod
    def process_data(self):
        pass

    @staticmethod
    def format_data(instruction, input_data, response):
        return {"instruction": str(instruction), "input": str(input_data), "response": str(response)}

    @staticmethod
    def format_data_jsonl(data):
        return {
            "messages": [
                {"role": "system", "content": data["instruction"]},
                {"role": "user", "content": data["input"]},
                {"role": "assistant", "content": data["response"]}
            ]
        }

    def append_data(self, instruction, input_data, response, token_limit=None):
        formatted_data = BaseDataProcessor.format_data(instruction, input_data, response)
        formatted_data_in_jsonl = BaseDataProcessor.format_data_jsonl(formatted_data)
        if token_limit is not None:
            if not self.check_token_count(json.dumps(formatted_data_in_jsonl), token_limit):
                logging.warning(f"Data with instruction {instruction} exceeds token limit. Skipping.")
                return
        self.data_list.append(formatted_data)

    def generate_jsonl(self, file_path):
        with open(file_path, 'w') as f:
            for data in self.data_list:
                formatted_data = self.format_data_jsonl(data)
                json.dump(formatted_data, f)
                f.write('\n')

    @staticmethod
    def check_token_count(text, token_limit):
        # Implement token counting logic here
        # For simplicity, we'll use a basic word count method
        return len(text.split()) <= token_limit