import argparse
import time

from ai_module.core.config import settings
from ai_module.core.errors import ProviderError
from ai_module.providers.llm.gigachat_provider import GigaChatProvider


def main() -> int:
    parser = argparse.ArgumentParser(description="Live connectivity check for GigaChat")
    parser.add_argument(
        "--prompt",
        default="Ответь одним словом: OK",
        help="Prompt for live check",
    )
    args = parser.parse_args()

    if not settings.gigachat_credentials:
        print("ERROR: GIGACHAT_CREDENTIALS is empty. Set it in ai_module/.env")
        return 2

    provider = GigaChatProvider()

    # Keep output contract compact and parseable.
    wrapped_prompt = (
        "Верни JSON без markdown: "
        '{"status":"ok","echo":"<краткий ответ не длиннее 10 слов>"}\n'
        f"Запрос: {args.prompt}"
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

