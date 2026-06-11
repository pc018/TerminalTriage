"""Provider selection."""

from __future__ import annotations

from ..config import Settings
from .base import AIProvider, ProviderError

# Provider name -> "module:ClassName". Modules are imported lazily so that a
# missing optional SDK only fails when that provider is actually selected.
_PROVIDERS: dict[str, str] = {
    "anthropic": "anthropic_provider:AnthropicProvider",
    "openai": "openai_provider:OpenAIProvider",
    "gemini": "gemini_provider:GeminiProvider",
}


def available_providers() -> list[str]:
    """Names of all known providers."""
    return sorted(_PROVIDERS)


def get_provider(settings: Settings) -> AIProvider:
    """Construct the :class:`AIProvider` selected by ``settings``.

    Raises :class:`ProviderError` for an unknown provider or missing API key.
    """
    spec = _PROVIDERS.get(settings.provider)
    if spec is None:
        raise ProviderError(
            f"Unknown AI provider '{settings.provider}'. "
            f"Choose one of: {', '.join(available_providers())}."
        )

    if not settings.api_key and not settings.auth_token:
        raise ProviderError(
            f"No API key set for provider '{settings.provider}'. "
            "Set the matching key in your environment or .env file."
        )

    module_name, class_name = spec.split(":")
    import importlib

    module = importlib.import_module(f"{__package__}.{module_name}")
    provider_cls = getattr(module, class_name)
    return provider_cls(
        api_key=settings.api_key or "",
        model=settings.model,
        max_tokens=settings.max_tokens,
        auth_token=settings.auth_token,
    )
