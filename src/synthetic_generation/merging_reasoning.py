import json
import logging
import xml.etree.ElementTree as ET


PROMPT = """You are an AI assistant specialized in refining podcast transcripts for optimal video editing. Your task is to analyze raw transcripts and provide two outputs:

1. A detailed chain of thought explaining your editing process.
2. An edited version of the transcript with improved readability and conciseness.

Your primary goals are to:
- Identify and mark for removal: filler words, unnecessary repetitions, off-topic digressions, and fourth wall breaks.
- Maintain the core message, flow, and speaker's voice.
- Ensure the edited version remains coherent and meaningful.

Follow these steps:
1. Carefully read and analyze the entire transcript.
2. Identify elements that can be removed without altering the main content or flow.
3. In your chain of thought, explain your editing decisions, focusing on:
   - Why certain parts were selected for removal
   - How removing these parts improves clarity and conciseness
   - Any challenges or considerations in maintaining coherence
4. In the edited transcript:
   - Use ~~strikethrough~~ to mark text for removal
   - Do not add, rearrange, or modify any text
   - Maintain the original word count, only marking for removal

Remember:
- Prioritize clarity and conciseness while preserving the speaker's unique voice and style.
- Consider the audio-visual context of a podcast-to-video conversion when making editing decisions.
- Aim for the most trimmed version possible without compromising understanding or flow.

Your output should help guide video editors in creating a concise, engaging final product.
"""

class ConversationParser:
    def __init__(self, input_file_path, output_file_path):
        self.input_file_path = input_file_path
        self.output_file_path = output_file_path
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    def parse_conversations(self):
        self.logger.info(f"Parsing conversations from {self.input_file_path}")
        
        with open(self.input_file_path, 'r') as input_file, open(self.output_file_path, 'w') as output_file:
            for line in input_file:
                try:
                    conversation = json.loads(line.strip())
                    processed_conversation = self.process_conversation(conversation)
                    if processed_conversation:
                        json.dump(processed_conversation, output_file)
                        output_file.write('\n')
                except json.JSONDecodeError:
                    self.logger.error(f"Failed to parse JSON line: {line.strip()}")
                except Exception as e:
                    self.logger.error(f"Error processing conversation: {str(e)}")

    def process_conversation(self, conversation):
        messages = conversation.get('messages', [])
        if len(messages) != 4:
            self.logger.warning(f"Skipping conversation with unexpected number of messages: {len(messages)}")
            return None

        try:
            user_message = next(m for m in messages if m['role'] == 'user')
            reasoning_message = next(m for m in messages if m['role'] == 'reasoning')
            assistant_message = next(m for m in messages if m['role'] == 'assistant')

            reasoning_json = self.xml_to_json(ET.fromstring(f"<root>{reasoning_message['content']}</root>"))
            assistant_content = {"edited_transcript": assistant_message['content']}
            merged_content = {**reasoning_json, **assistant_content}

            # Ensure the merged content is a valid JSON string
            merged_content_json = json.dumps(merged_content)

            logging.info(reasoning_message['content'])
            # logging.info(reasoning_json)
            # logging.info(merged_content)

            return {
                "messages": [
                    {"role": "system", "content": PROMPT},
                    {"role": "user", "content": f"<raw_transcript>{user_message['content']}</raw_transcript>"},
                    {"role": "assistant", "content": merged_content_json}
                ]
            }
        except StopIteration:
            self.logger.warning("Conversation missing one or more required message types")
        except ET.ParseError:
            self.logger.error("Failed to parse XML in reasoning message")
        except json.JSONDecodeError:
            self.logger.error("Failed to create valid JSON from merged content")
        except Exception as e:
            self.logger.error(f"Error processing conversation: {str(e)}")
        
        return None

    def xml_to_json(self, element):
        result = {}
        for child in element:
            if len(child) == 0:
                result[child.tag] = child.text
            else:
                result[child.tag] = self.xml_to_json(child)
        return result

# Example usage
if __name__ == "__main__":
    input_file_path = "/Users/adi/Documents/GitHub/data/tmp/finetuning_file/combined.jsonl"
    output_file_path = "/Users/adi/Documents/GitHub/data/tmp/finetuning_file/processed_combined.jsonl"
    parser = ConversationParser(input_file_path, output_file_path)
    parser.parse_conversations()