"""Shared fixtures."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from terminal_triage.ai.base import AIProvider
from terminal_triage.config import Settings


class FakeProvider(AIProvider):
    """A provider that yields canned chunks without any network call."""

    name = "fake"

    def __init__(self, chunks: list[str] | None = None) -> None:
        super().__init__(api_key="test-key", model="fake-model")
        self.chunks = chunks if chunks is not None else ["Looks ", "fine."]
        self.prompts: list[str] = []

    def stream(self, prompt: str) -> Iterator[str]:
        self.prompts.append(prompt)
        yield from self.chunks


@pytest.fixture
def fake_provider() -> FakeProvider:
    return FakeProvider()


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        provider="fake",
        api_key="test-key",
        model="fake-model",
        history_file=tmp_path / "history",
    )


class Recorder:
    """Captures output() calls into a single string buffer."""

    def __init__(self) -> None:
        self.parts: list[str] = []

    def __call__(self, *args, **kwargs) -> None:
        self.parts.append(" ".join(str(a) for a in args))

    @property
    def text(self) -> str:
        return "\n".join(self.parts)


@pytest.fixture
def recorder() -> Recorder:
    return Recorder()
