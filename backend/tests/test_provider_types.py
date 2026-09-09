from app.services.provider_types import ProviderError, ProviderModel


def test_provider_model_does_not_expose_secret_fields() -> None:
    model = ProviderModel(provider="kilo", id="kilo-auto/free", name="Auto Free", free=True)
    assert model.supports_chat is True
    assert "api_key" not in repr(model).lower()


def test_provider_error_exposes_only_safe_public_message() -> None:
    error = ProviderError("Provider is temporarily unavailable", retryable=True)
    assert str(error) == "Provider is temporarily unavailable"
    assert error.retryable is True
