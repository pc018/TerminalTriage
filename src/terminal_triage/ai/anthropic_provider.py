"""Anthropic Claude provider."""

from __future__ import annotations

from collections.abc import Iterator

from .base import AIProvider, ProviderError


class AnthropicProvider(AIProvider):
    name = "anthropic"

    def __init__(
        self,
        api_key: str,
        model: str,
        max_tokens: int = 4096,
        auth_token: str | None = None,
    ) -> None:
        super().__init__(api_key, model, max_tokens, auth_token=auth_token)
        try:
            from anthropic import Anthropic
        except ImportError as exc:  # pragma: no cover - exercised via monkeypatch
            raise ProviderError(
                "The 'anthropic' package is required for the Anthropic provider. "
                "Install it with: pip install 'terminal-triage[anthropic]'"
            ) from exc
        if auth_token:
            self._client = Anthropic(auth_token=auth_token)
        else:
            self._client = Anthropic(api_key=api_key)

    def stream(self, prompt: str) -> Iterator[str]:
        try:
            with self._client.messages.stream(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                yield from stream.text_stream
        except Exception as exc:  # pragma: no cover - network/runtime errors
            raise ProviderError(f"Anthropic API error: {exc}") from exc
