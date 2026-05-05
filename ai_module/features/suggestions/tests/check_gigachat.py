import argparse
import time

from ai_module.app.config import settings
from ai_module.shared.exceptions import ProviderError
from ai_module.app.logging import configure_logging
from ai_module.features.suggestions.llm_client import GigaChatProvider


def main() -> int:
    configure_logging()

    parser = argparse.ArgumentParser(description="Live connectivity check for GigaChat")
    parser.add_argument(
        "--prompt",
        default="Reply with one word: OK",
        help="Prompt for live check",
    )
    args = parser.parse_args()

    if not settings.gigachat_credentials:
        print("ERROR: GIGACHAT_CREDENTIALS is empty. Set it in ai_module/.env")
        return 2

    provider = GigaChatProvider()

    wrapped_prompt = (
        "Return JSON without markdown: "
        '{"status":"ok","echo":"<short answer up to 10 words>"}\n'
        f"Request: {args.prompt}"
    )

    started = time.perf_counter()
    try:
        response = provider.generate_json(prompt=wrapped_prompt)
    except ProviderError as exc:
        print(f"ERROR: request failed: {exc}")
        return 1
    latency_ms = int((time.perf_counter() - started) * 1000)

    print("SUCCESS: GigaChat reachable")
    print(f"model={provider.model} latency_ms={latency_ms}")
    print(f"response={response}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



