import pytest

from ai_module.app.config import settings
from ai_module.features.suggestions.llm_client import GigaChatProvider
from ai_module.shared.exceptions import ProviderError


class _Msg:
    def __init__(self, content: str) -> None:
        self.content = content


class _Choice:
    def __init__(self, content: str) -> None:
        self.message = _Msg(content)


class _Response:
    def __init__(self, content: str) -> None:
        self.choices = [_Choice(content)]


def test_parse_json_content_supports_code_fence() -> None:
    payload = GigaChatProvider._parse_json_content("""```json\n{\"status\":\"ok\"}\n```""")
    assert payload == {"status": "ok"}


def test_extract_content_raises_on_invalid_schema() -> None:
    with pytest.raises(ProviderError):
        GigaChatProvider._extract_content(object())


def test_generate_json_raises_without_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "gigachat_credentials", "")
    provider = GigaChatProvider(credentials=None)
    with pytest.raises(ProviderError, match="GIGACHAT_CREDENTIALS"):
        provider.generate_json(prompt="{}")


def test_extract_content_happy_path() -> None:
    response = _Response('{"status":"ok"}')
    content = GigaChatProvider._extract_content(response)
    assert content == '{"status":"ok"}'
