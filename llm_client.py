import anthropic
import logging
import time

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Claude-only LLM client with multi-pass support, prompt caching,
    and automatic model fallback.
    """

    # Current-gen models in priority order
    MODELS = [
        "claude-sonnet-4-6",              # Primary — best price/performance
        "claude-opus-4-6",                 # Premium fallback
        "claude-haiku-4-5",       # Budget / preprocessing
    ]

    def __init__(self, provider, api_key: str, model_name: str = None):
        if provider.lower() not in ["anthropic", "claude"]:
            raise ValueError("This system is now Claude-only.")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model_name or "claude-sonnet-4-6"

    # ── Core API call with retry & fallback ──────────────────────────

    def _call_claude(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 32000,
        use_cache: bool = False,
    ) -> str:
        """
        Low-level Claude call with model fallback and retry logic.
        """
        models_to_try = [self.model] if self.model not in self.MODELS else self.MODELS
        last_error = None

        for model_id in models_to_try:
            for attempt in range(3):
                try:
                    # Build system message (with optional caching)
                    if use_cache:
                        system_msg = [
                            {
                                "type": "text",
                                "text": system_prompt,
                                "cache_control": {"type": "ephemeral"},
                            }
                        ]
                    else:
                        system_msg = system_prompt

                    # NOTE: temperature is intentionally omitted — current-gen
                    # Claude models reject it with a 400. Defaults are used.
                    with self.client.messages.stream(
                        model=model_id,
                        max_tokens=max_tokens,
                        system=system_msg,
                        messages=[{"role": "user", "content": user_prompt}],
                    ) as stream:
                        content = ""
                        for text in stream.text_stream:
                            content += text

                    if content.strip():
                        logger.info(f"Success: {model_id} ({len(content)} chars)")
                        return content.strip()

                except Exception as e:
                    last_error = e
                    logger.warning(f"{model_id} attempt {attempt+1} failed: {e}")
                    time.sleep(2 * (attempt + 1))

        raise RuntimeError(f"All models failed. Last error: {last_error}")

    # ── Single-pass generation (backward compatible) ─────────────────

    def generate_style_guide_text(self, system_prompt: str, user_prompt: str, max_tokens: int = 32000) -> str:
        """
        Generate a style guide in a single pass.
        Kept for backward compatibility — multi-pass is preferred.
        """
        return self._call_claude(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            use_cache=True,
        )

    # ── Multi-pass generation ────────────────────────────────────────

    def generate_section(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 8000,
    ) -> str:
        """Generate a single section of the style guide."""
        return self._call_claude(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            use_cache=True,
        )

    def generate_preprocessing(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """Quick preprocessing call using faster/cheaper settings."""
        return self._call_claude(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=4000,
            use_cache=True,
        )

    def generate_review(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """Self-review and gap-filling pass."""
        return self._call_claude(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=16000,
            use_cache=True,
        )
