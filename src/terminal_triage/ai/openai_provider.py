"""OpenAI provider."""

from __future__ import annotations

from collections.abc import Iterator

from .base import AIProvider, ProviderError


class OpenAIProvider(AIProvider):
    name = "openai"

    def __init__(
        self,
        api_key: str,
        model: str,
        max_tokens: int = 4096,
        auth_token: str | None = None,
    ) -> None:
        super().__init__(api_key, model, max_tokens, auth_token=auth_token)
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - exercised via monkeypatch
            raise ProviderError(
                "The 'openai' package is required for the OpenAI provider. "
                "Install it with: pip install 'terminal-triage[openai]'"
            ) from exc
        self._client = OpenAI(api_key=api_key)

    def stream(self, prompt: str) -> Iterator[str]:
        try:
            stream = self._client.chat.completions.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        except Exception as exc:  # pragma: no cover - network/runtime errors
            raise ProviderError(f"OpenAI API error: {exc}") from exc
