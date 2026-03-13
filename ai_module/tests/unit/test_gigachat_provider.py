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
    content = 'Answer:\n{"status":"ok","echo":"OK"}\nThanks'
    result = GigaChatProvider._parse_json_content(content)
    assert result["status"] == "ok"


def test_parse_json_content_repairs_trailing_commas_and_unclosed_braces() -> None:
    content = (
        '{"summary":"ok","suggestions":[{"category":"style","severity":"minor","message":"m",'
        '"fragment":"f","proposed_fix":"p",}],"clean_rewrite":"text"'
    )
    result = GigaChatProvider._parse_json_content(content)
    assert result["summary"] == "ok"
    assert isinstance(result["suggestions"], list)


def test_parse_json_content_repairs_duplicate_braces() -> None:
    content = (
        '{"summary":"ok","score":2,"suggestions":[{{"category":"style","severity":"minor",'
        '"message":"m","fragment":"f","proposed_fix":"p"}}],"clean_rewrite":"text"}'
    )
    result = GigaChatProvider._parse_json_content(content)
    assert result["summary"] == "ok"
    assert result["suggestions"][0]["category"] == "style"


def test_parse_json_content_raises_on_invalid_payload() -> None:
    with pytest.raises(ProviderError):
        GigaChatProvider._parse_json_content("not json")
