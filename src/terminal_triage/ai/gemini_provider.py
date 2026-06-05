"""Google Gemini provider."""

from __future__ import annotations

from collections.abc import Iterator

from .base import AIProvider, ProviderError


class GeminiProvider(AIProvider):
    name = "gemini"

    def __init__(self, api_key: str, model: str, max_tokens: int = 4096) -> None:
        super().__init__(api_key, model, max_tokens)
        try:
            import google.generativeai as genai
        except ImportError as exc:  # pragma: no cover - exercised via monkeypatch
            raise ProviderError(
                "The 'google-generativeai' package is required for the Gemini provider. "
                "Install it with: pip install 'terminal-triage[gemini]'"
            ) from exc
        genai.configure(api_key=api_key)
        self._genai = genai
        self._model = genai.GenerativeModel(model)

    def stream(self, prompt: str) -> Iterator[str]:
        try:
            generation_config = self._genai.types.GenerationConfig(
                max_output_tokens=self.max_tokens,
            )
            response = self._model.generate_content(
                prompt,
                stream=True,
                generation_config=generation_config,
            )
            for chunk in response:
                text = getattr(chunk, "text", None)
                if text:
                    yield text
        except Exception as exc:  # pragma: no cover - network/runtime errors
            raise ProviderError(f"Gemini API error: {exc}") from exc
