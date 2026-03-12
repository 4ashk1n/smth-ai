import os

import pytest

from ai_module.providers.llm.gigachat_provider import GigaChatProvider


@pytest.mark.skipif(
    os.getenv("RUN_LIVE_GIGACHAT_TEST") != "1",
    reason="Set RUN_LIVE_GIGACHAT_TEST=1 for live GigaChat test",
)
def test_gigachat_live_json_response() -> None:
    provider = GigaChatProvider()
    result = provider.generate_json(
        prompt=(
            "Верни JSON без markdown: "
            '{"status":"ok","echo":"тест"}'
        )
    )
    assert isinstance(result, dict)
    assert result.get("status") == "ok"

