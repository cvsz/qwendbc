from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProviderModel:
    """Normalized, non-secret metadata for a provider model."""

    provider: str
    id: str
    name: str
    free: bool
    supports_chat: bool = True
    context_length: int | None = None
    prompt_price_per_token: float | None = None
    completion_price_per_token: float | None = None


class ProviderError(Exception):
    """A provider failure safe to expose through application error handling."""

    def __init__(self, public_message: str, *, retryable: bool) -> None:
        self.public_message = public_message
        self.retryable = retryable
        super().__init__(public_message)
