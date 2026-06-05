"""Base class shared by all AI providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator


class ProviderError(RuntimeError):
    """Raised for configuration or runtime problems with an AI provider."""


class AIProvider(ABC):
    """A streaming AI backend.

    Subclasses wrap a vendor SDK and yield response text chunk-by-chunk so the
    terminal can print the answer as it arrives.
    """

    #: Short provider identifier, e.g. ``"anthropic"``.
    name: str = "base"

    def __init__(self, api_key: str, model: str, max_tokens: int = 4096) -> None:
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens

    @abstractmethod
    def stream(self, prompt: str) -> Iterator[str]:
        """Yield response text chunks for ``prompt``."""
        raise NotImplementedError
