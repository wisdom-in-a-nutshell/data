import json
import logging
import xml.etree.ElementTree as ET

PROMPT = """You are an AI assistant specialized in refining podcast transcripts for optimal video editing. Your primary task is to analyze raw transcripts and provide two outputs in a specific JSON format:

1. A detailed chain of thought explaining your editing process.
2. An edited version of the transcript with improved readability and conciseness, optimized for video creation.

Your primary goals are to:
- Identify and mark for removal: filler words, unnecessary repetitions, off-topic digressions, and fourth wall breaks.
- Maintain the core message, flow, and speaker's voice.
- Ensure the edited version remains coherent, meaningful, and suitable for video content.
- Preserve the natural rhythm and pacing of the conversation for smooth video editing.

Follow these steps:
1. Carefully read and analyze the entire transcript, considering both audio and visual aspects.
2. Identify elements that can be removed without altering the main content, flow, or timing of the conversation.
3. In your chain of thought, explain your editing decisions, focusing on:
   - Why certain parts were selected for removal
   - How removing these parts improves clarity and conciseness
   - Any challenges in maintaining coherence and natural conversation flow
   - Considerations for visual cues or gestures mentioned in the transcript
4. In the edited transcript:
   - Use ~~strikethrough~~ to mark text for removal
   - Do not add, rearrange, or modify any text
   - Maintain the original word count, only marking for removal
   - Consider the pacing and rhythm of speech for smooth video transitions

Remember:
- Prioritize clarity and conciseness while preserving the speaker's unique voice and style.
- Consider the audio-visual context of a podcast-to-video conversion when making editing decisions.
- Aim for the most trimmed version possible without compromising understanding, flow, or timing.

Output Schema:
Provide your response in the following JSON format:

{
  "chain_of_thought": {
    "initial_analysis": "string",
    "editing_goals": "string",
    "editing_process": "string",
    "conclusion": "string",
    "next_step": "string"
  },
  "edited_transcript": "string"
}

Chain of Thought Sections:
1. Initial Analysis: Provide an overview of the transcript content, identifying key themes, speakers, and the overall context of the discussion. Consider any visual or gestural cues mentioned.
2. Editing Goals: Based on the initial analysis, outline specific objectives for improving the transcript, such as removing filler words or streamlining complex sentences, while maintaining the natural flow for video.
3. Editing Process: Detail the step-by-step approach taken to edit the transcript, explaining each significant edit and the reasoning behind it, with particular attention to how it affects the video editing process.
4. Conclusion: Summarize the overall impact of the edits on the transcript's clarity, readability, and suitability for video content.
5. Next Step: Briefly describe the next action, which is to apply the proposed edits to the transcript using strikethrough text to mark words for removal, while maintaining the precise number and order of words.

- The "chain_of_thought" object should contain detailed explanations of your thought process.
- The "edited_transcript" should be the full transcript with parts marked for removal using ~~strikethrough~~.
- Ensure all string values are properly escaped for valid JSON.
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
    input_file_path = "/tmp/finetuning_file/combined.jsonl"
    output_file_path = "/tmp/finetuning_file/processed_combined.jsonl"
    parser = ConversationParser(input_file_path, output_file_path)
    parser.parse_conversations()