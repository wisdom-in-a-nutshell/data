import json
import logging
from abc import ABC, abstractmethod

logging.basicConfig(level=logging.INFO)

class BaseDataCollection(ABC):
    def __init__(self):
        self.data_list = []

    @abstractmethod
    def get_data(self):
        pass

    @staticmethod
    def format_data(instruction, input_data, response):
        return {"instruction": str(instruction), "input": str(input_data), "response": str(response)}

    @staticmethod
    def format_data_jsonl(data, huggingface_format=False):
        if huggingface_format:
            return {
                "instruction": data["instruction"],
                "input": data["input"],
                "output": data["response"]
            }
        return {
            "messages": [
                {"role": "system", "content": data["instruction"]},
                {"role": "user", "content": data["input"]},
                {"role": "assistant", "content": data["response"]}
            ]
        }

    def append_data(self, instruction, input_data, response, token_limit=None):
        formatted_data = BaseDataCollection.format_data(instruction, input_data, response)
        formatted_data_in_jsonl = BaseDataCollection.format_data_jsonl(formatted_data)
        if token_limit is not None:
            if not self.check_token_count(json.dumps(formatted_data_in_jsonl), token_limit):
                logging.warning(f"Data with instruction {instruction} exceeds token limit. Skipping.")
                return
        self.data_list.append(formatted_data)

    def generate_jsonl(self, file_path, huggingface_format=False):
        with open(file_path, 'w') as f:
            for data in self.data_list:
                formatted_data = self.format_data_jsonl(data, huggingface_format)
                json.dump(formatted_data, f)
                f.write('\n')
