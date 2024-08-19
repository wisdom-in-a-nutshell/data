import json
import logging
import xml.etree.ElementTree as ET

REASONING_PROMPT = {
  "role": "You are an AI assistant specialized in analyzing podcast transcripts for optimal video editing.",
  "task": "Analyze the given transcript and provide a detailed chain of thought explaining your editing process. Focus on identifying parts that can be removed to improve clarity and conciseness for video content.",
  "goals": [
    "Identify filler words, unnecessary repetitions, off-topic digressions, and fourth wall breaks.",
    "Maintain the core message, flow, and speaker's voice.",
    "Ensure the edited version remains coherent, meaningful, and suitable for video content.",
    "Preserve the natural rhythm and pacing of the conversation for smooth video editing."
  ],
  "output_format": {
    "type": "JSON",
    "structure": {
      "chain_of_thought": {
        "initial_analysis": "Overview of transcript content, key themes, speakers, and context.",
        "editing_goals": "Specific objectives for improving the transcript.",
        "editing_process": "Step-by-step approach, explaining each significant edit and reasoning.",
        "conclusion": "Summary of overall impact on clarity, readability, and video suitability.",
      }
    }
  },
  "instructions": [
    "Carefully read and analyze the entire transcript, considering the audio-visual nature of the final video product.",
    "Pay attention to speaker annotations marked with **<speaker>:** format.",
    "Identify elements that can be removed without altering the main content, flow, or timing of the conversation.",
    "Explain your editing decisions, focusing on why certain parts were selected for removal and how this improves the transcript for video content.",
    "Consider how edits might affect the pacing and flow of the conversation in a video format.",
    "Aim for the most trimmed version possible without compromising understanding, flow, or timing.",
    "Do not actually edit the transcript in this step, only provide the reasoning."
  ]
}


EDITING_PROMPT = {
  "role": "You are an AI assistant specialized in editing podcast transcripts for optimal video content.",
  "task": "Using the provided chain of thought reasoning, edit the given transcript by marking parts for removal using strikethrough.",
  "goals": [
    "Apply the editing decisions from the chain of thought reasoning.",
    "Maintain the core message, flow, and speaker's voice.",
    "Ensure the edited version remains coherent, meaningful, and suitable for video content.",
    "Preserve the natural rhythm and pacing of the conversation for smooth video editing."
  ],
  "output_format": {
    "type": "JSON",
    "structure": {
      "edited_transcript": "Full transcript with parts marked for removal using ~~strikethrough~~"
    }
  },
  "instructions": [
    "Use the chain of thought reasoning to guide your editing process.",
    "Mark text for removal using ~~strikethrough~~ syntax.",
    "Do not add, rearrange, or modify any text.",
    "Maintain the original word count and order, only marking for removal.",
    "Ensure the edited transcript reads coherently even with removed parts.",
    "Consider the pacing and rhythm of speech for smooth video transitions.",
    "Preserve speaker annotations marked with **<speaker>:** format.",
    "Aim for clarity and conciseness while preserving the speaker's unique voice and style.",
    "Pay special attention to maintaining the flow and coherence of the conversation in a video context."
  ],
  "constraints": [
    "You must not remove or re-order anything within the transcript.",
    "You can only suggest removals by using strikethrough.",
    "The edited transcript must maintain the exact order of the original text.",
    "Speaker annotations (**<speaker>:**) must always be preserved."
  ]
}
class ConversationParser:
    def __init__(self, input_file_path, reasoning_output_file_path, edited_transcript_output_file_path):
        self.input_file_path = input_file_path
        self.reasoning_output_file_path = reasoning_output_file_path
        self.edited_transcript_output_file_path = edited_transcript_output_file_path
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    def parse_conversations(self):
        self.logger.info(f"Parsing conversations from {self.input_file_path}")

        with open(self.input_file_path, 'r') as input_file, \
             open(self.reasoning_output_file_path, 'w') as reasoning_output_file, \
             open(self.edited_transcript_output_file_path, 'w') as edited_transcript_output_file:
            for line in input_file:
                try:
                    conversation = json.loads(line.strip())
                    reasoning_content, edited_transcript_content = self.process_conversation(conversation)
                    if reasoning_content and edited_transcript_content:
                        json.dump(reasoning_content, reasoning_output_file)
                        reasoning_output_file.write('\n')
                        json.dump(edited_transcript_content, edited_transcript_output_file)
                        edited_transcript_output_file.write('\n')
                except json.JSONDecodeError:
                    self.logger.error(f"Failed to parse JSON line: {line.strip()}")
                except Exception as e:
                    self.logger.error(f"Error processing conversation: {str(e)}")
    def process_conversation(self, conversation):
        messages = conversation.get('messages', [])
        if len(messages) != 4:
            self.logger.warning(f"Skipping conversation with unexpected number of messages: {len(messages)}")
            return None, None

        try:
            input_message = next(m for m in messages if m['role'] == 'user')
            reasoning_message = next(m for m in messages if m['role'] == 'reasoning')
            output_message = next(m for m in messages if m['role'] == 'assistant')

            reasoning_json = self.get_reasoning_json(reasoning_message['content'])
            reasoning_json_string = json.dumps(reasoning_json)
            # if "Based on the differences between the raw and edited versions" in reasoning_json_string:
            #     reasoning_json_string = reasoning_json_string.replace("Based on the differences between the raw and edited versions", "")


            raw_transcript = input_message['content']
            edited_transcript = output_message['content']

            reasoning_content = self.generate_reasoning_content(raw_transcript, reasoning_json_string)
            edited_transcript_content = self.generate_edited_transcript_content(raw_transcript, reasoning_json_string, edited_transcript)

            # Validate if the generated content is proper JSON
            for content in [reasoning_content, edited_transcript_content]:
                for message in content["messages"]:
                    try:
                        json.loads(message["content"])
                    except (TypeError, ValueError) as e:
                        self.logger.error(f"Generated message content is not valid JSON: {message['content']}")
                        raise e

            return reasoning_content, edited_transcript_content
        except StopIteration:
            self.logger.warning("Conversation missing one or more required message types")
        except ET.ParseError:
            self.logger.error("Failed to parse XML in reasoning message")
        except json.JSONDecodeError:
            self.logger.error("Failed to create valid JSON from merged content")
        except Exception as e:
            self.logger.error(f"Error processing conversation: {str(e)}")

        return None, None
    
    
    def get_reasoning_json(self, reasoning_content):
        reasoning_json = self.xml_to_json(ET.fromstring(f"<root>{reasoning_content}</root>"))
        if "chain_of_thought" in reasoning_json and "next_step" in reasoning_json["chain_of_thought"]:
            del reasoning_json["chain_of_thought"]["next_step"]
        return reasoning_json

    def xml_to_json(self, element):
        result = {}
        for child in element:
            if len(child) == 0:
                result[child.tag] = child.text.strip()
            else:
                result[child.tag] = self.xml_to_json(child)
        return result

    def generate_reasoning_content(self, input_transcript, reasoning_json_string):
        user_message_content = {
            "raw_transcript": input_transcript,
            "instructions": (
                "Analyze this raw transcript and provide a detailed chain of thought on how to edit it for video content. "
                "Focus on identifying parts that can be removed to improve clarity and conciseness while maintaining the core message and speaker's voice. "
                "Consider the audio-visual nature of the final product and how edits might affect pacing and flow."
            ),
            "additional_context": "This is a podcast transcript being prepared for video content. Speaker annotations are marked with **<speaker>:** format."
        }


        return {
            "messages": [
                {"role": "system", "content": json.dumps(REASONING_PROMPT)},
                {"role": "user", "content": json.dumps(user_message_content)},
                {"role": "assistant", "content": reasoning_json_string}
            ]
        }

    def generate_edited_transcript_content(self, input_transcript, reasoning_json_string, edited_transcript):
        user_message_content = {
            "raw_transcript": input_transcript,
            "chain_of_thought": reasoning_json_string,
            "instructions": (
                "Please apply the above chain of thought reasoning to edit the raw transcript provided. "
                "Follow the instructions in the system prompt, particularly regarding the use of strikethrough for marking removals and preserving the original order of the text. Return output in a JSON format with edited_transcript as the key."
            )
        }
        edited_transcript_content = {
            "edited_transcript": edited_transcript
        }

        return {
            "messages": [
                {"role": "system", "content": json.dumps(EDITING_PROMPT)},
                {"role": "user", "content": json.dumps(user_message_content)},
                {"role": "assistant", "content": json.dumps(edited_transcript_content)}
            ]
        }


# Example usage
if __name__ == "__main__":
    input_file_path = "/Users/adi/Documents/GitHub/data/tmp/finetuning_file/combined.jsonl"
    reasoning_output_file_path = "/Users/adi/Documents/GitHub/data/tmp/finetuning_file/reasoning_output.jsonl"
    edited_transcript_output_file_path = "/Users/adi/Documents/GitHub/data/tmp/finetuning_file/edited_transcript_output.jsonl"
    parser = ConversationParser(input_file_path, reasoning_output_file_path, edited_transcript_output_file_path)
    parser.parse_conversations()

