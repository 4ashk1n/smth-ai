import pytest

from ai_module.core.errors import ProviderError
from ai_module.providers.llm.gigachat_provider import GigaChatProvider


def test_parse_json_content_plain_json() -> None:
    result = GigaChatProvider._parse_json_content('{"status":"ok","echo":"OK"}')
    assert result["status"] == "ok"


def test_parse_json_content_markdown_fence() -> None:
    content = '```json\n{"status":"ok","echo":"OK"}\n```'
    result = GigaChatProvider._parse_json_content(content)
    assert result["echo"] == "OK"


def test_parse_json_content_json_inside_text() -> None:
    content = 'Ответ:\n{"status":"ok","echo":"OK"}\nСпасибо'
    result = GigaChatProvider._parse_json_content(content)
    assert result["status"] == "ok"


def test_parse_json_content_raises_on_invalid_payload() -> None:
    with pytest.raises(ProviderError):
        GigaChatProvider._parse_json_content("not json")

