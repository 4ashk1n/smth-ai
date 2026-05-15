import os
import time

import pytest

from ai_module.app.config import settings
from ai_module.app.logging import configure_logging
from ai_module.features.suggestions.llm_client import GigaChatProvider


def _live_test_enabled() -> bool:
    return os.getenv("RUN_GIGACHAT_LIVE_TEST", "").strip().lower() in {"1", "true", "yes"}


@pytest.mark.integration
def test_gigachat_live_connectivity() -> None:
    if not _live_test_enabled():
        pytest.skip("Set RUN_GIGACHAT_LIVE_TEST=1 to run live GigaChat connectivity test")

    configure_logging()

    if not settings.gigachat_credentials:
        pytest.skip("GIGACHAT_CREDENTIALS is empty")

    provider = GigaChatProvider()
    prompt = (
        "Return JSON without markdown: "
        '{"status":"ok","echo":"<short answer up to 10 words>"}\n'
        "Request: Reply with one word: OK"
    )

    started = time.perf_counter()
    response = provider.generate_json(prompt=prompt)
    latency_ms = int((time.perf_counter() - started) * 1000)

    assert isinstance(response, dict)
    assert response.get("status") == "ok"
    assert latency_ms >= 0

