import openai

def get_response():
    client = openai.OpenAI(
        api_key="sk-5ce0c5c0-4079-11ef-9254-173e6ea885c7",            # litellm proxy api key
        base_url="http://192.168.2.210:4000" # litellm proxy base url
    )

    response = client.chat.completions.create(
        model="claude-3-5-sonnet",
        messages=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "You are an AI assistant tasked with analyzing literary works. Your goal is to provide insightful commentary on themes, characters, and writing style.\n",
                    },
                    {
                        "type": "text",
                        "text": "some word " * 1000,
                        "cache_control": {"type": "ephemeral"}
                    }
                ],
            },
            {
                "role": "user",
                "content": "what are the key terms and conditions in this agreement?",
            },
        ],
        extra_headers={
            "anthropic-version": "2023-06-01",
            "anthropic-beta": "prompt-caching-2024-07-31",
        },
    )
    return response


def main():
    response = get_response()
    assert response is not None, "Response should not be None"
    assert isinstance(response, openai.types.chat.ChatCompletion), "Response should be a ChatCompletion object"
    assert len(response.choices) > 0, "Response should have at least one choice"
    assert response.choices[0].message is not None, "First choice should have a message"
    assert response.choices[0].message.content is not None, "Message should have content"
    print("All tests passed.")
    print("Response content:")
    print(response.choices[0].message.content)

if __name__ == "__main__":
    main()

