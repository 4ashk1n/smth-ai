import builtins
import json
import sys
import types

import pytest

from ai_module.features.suggestions import llm_client
from ai_module.features.suggestions.llm_client import (
    GigaChatProvider,
    _collapse_duplicate_braces,
    _extract_balanced_json_object,
    _repair_json_like,
    _try_parse_dict,
)
from ai_module.shared.exceptions import ProviderError


def test_try_parse_dict_cases() -> None:
    assert _try_parse_dict('{"a":1}') == {"a": 1}
    assert _try_parse_dict("[1,2,3]") is None
    assert _try_parse_dict("{") is None


def test_extract_balanced_json_object_cases() -> None:
    assert _extract_balanced_json_object("prefix {\"a\": 1} suffix") == '{"a": 1}'
    assert _extract_balanced_json_object("no object here") is None
    assert _extract_balanced_json_object('x {"a":"{nested}"} tail') == '{"a":"{nested}"}'
    assert _extract_balanced_json_object('x {"a": 1') == '{"a": 1'


def test_collapse_duplicate_braces_keeps_string_content() -> None:
    assert _collapse_duplicate_braces('{{"a":1}}') == '{"a":1}'
    assert _collapse_duplicate_braces('{"txt":"{{keep}}"}') == '{"txt":"{{keep}}"}'


def test_repair_json_like_removes_trailing_comma_and_closes() -> None:
    repaired = _repair_json_like('{"a": 1, "b": [1,2,],')
    assert repaired.endswith("}")
    assert "[1,2]" in repaired


def test_parse_json_content_from_noisy_text_and_repair() -> None:
    parsed = GigaChatProvider._parse_json_content('Answer: {"ok": true,}')
    assert parsed == {"ok": True}


def test_parse_json_content_raises_on_non_json() -> None:
    with pytest.raises(ProviderError, match="non-JSON"):
        GigaChatProvider._parse_json_content("plain text only")


def test_generate_json_happy_path_with_mocked_sdk(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Msg:
        def __init__(self, content: str) -> None:
            self.content = content

    class _Choice:
        def __init__(self, content: str) -> None:
            self.message = _Msg(content)

    class _Response:
        def __init__(self, content: str) -> None:
            self.choices = [_Choice(content)]

    class _FakeClient:
        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def chat(self, prompt: str):
            assert "hello" in prompt
            return _Response('{"status":"ok"}')

    fake_module = types.SimpleNamespace(GigaChat=_FakeClient)
    monkeypatch.setitem(sys.modules, "gigachat", fake_module)

    provider = GigaChatProvider(credentials="token", model="GigaChat")
    result = provider.generate_json(prompt="hello json")
    assert result == {"status": "ok"}


def test_generate_json_sdk_request_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FakeClient:
        def __init__(self, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def chat(self, prompt: str):
            raise RuntimeError("boom")

    monkeypatch.setitem(sys.modules, "gigachat", types.SimpleNamespace(GigaChat=_FakeClient))

    provider = GigaChatProvider(credentials="token")
    with pytest.raises(ProviderError, match="request failed"):
        provider.generate_json(prompt="hello")


def test_generate_json_when_gigachat_package_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    original_import = builtins.__import__

    def _import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "gigachat":
            raise ImportError("missing")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", _import)
    monkeypatch.delitem(sys.modules, "gigachat", raising=False)

    provider = GigaChatProvider(credentials="token")
    with pytest.raises(ProviderError, match="not installed"):
        provider.generate_json(prompt="hello")


def test_generate_json_invalid_response_schema(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FakeClient:
        def __init__(self, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def chat(self, prompt: str):
            return object()

    monkeypatch.setitem(sys.modules, "gigachat", types.SimpleNamespace(GigaChat=_FakeClient))

    provider = GigaChatProvider(credentials="token")
    with pytest.raises(ProviderError, match="Unexpected GigaChat response schema"):
        provider.generate_json(prompt="hello")
