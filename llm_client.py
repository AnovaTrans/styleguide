import anthropic

class LLMClient:
    def __init__(self, provider, api_key: str, model_name: str = None):
        """
        Claude-only LLM client.
        OpenAI has been fully removed from this system.
        """
        if provider.lower() not in ["anthropic", "claude"]:
            raise ValueError("This system is now Claude-only.")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model_name or "claude-sonnet-4-5-20250929"

    def generate_style_guide_text(self, system_prompt: str, user_prompt: str) -> str:
        """
        Generate a Word-style style guide using Claude.
        No JSON, only structured text output.
        """

        with self.client.messages.stream(
            model=self.model,
            max_tokens=8192,
            temperature=0.2,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ],
        ) as stream:

            content = ""
            for text in stream.text_stream:
                content += text

        return content.strip()
