import json
import logging
import re
from typing import Any

from ai_module.core.config import settings
from ai_module.core.errors import ProviderError
from ai_module.providers.llm.base import LLMProvider

logger = logging.getLogger("ai_module.llm.gigachat")


class GigaChatProvider(LLMProvider):
    """Thin adapter over official GigaChat SDK."""

    def __init__(
        self,
        *,
        credentials: str | None = None,
        model: str | None = None,
        scope: str | None = None,
        verify_ssl_certs: bool | None = None,
        ca_bundle_file: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
    ) -> None:
        self.credentials = credentials or settings.gigachat_credentials
        self.model = model or settings.llm_model
        self.scope = scope or settings.gigachat_scope
        self.verify_ssl_certs = (
            settings.gigachat_verify_ssl_certs
            if verify_ssl_certs is None
            else verify_ssl_certs
        )
        self.ca_bundle_file = (
            settings.gigachat_ca_bundle_file if ca_bundle_file is None else ca_bundle_file
        )
        self.timeout = timeout or settings.llm_timeout_seconds
        self.max_retries = (
            settings.llm_max_retries if max_retries is None else max_retries
        )

    def generate_json(self, *, prompt: str) -> dict[str, Any]:
        if not self.credentials:
            raise ProviderError("GIGACHAT_CREDENTIALS is not configured")

        try:
            from gigachat import GigaChat
        except Exception as exc:
            raise ProviderError("gigachat package is not installed") from exc

        try:
            with GigaChat(
                credentials=self.credentials,
                scope=self.scope,
                model=self.model,
                verify_ssl_certs=self.verify_ssl_certs,
                ca_bundle_file=self.ca_bundle_file,
                timeout=self.timeout,
                max_retries=self.max_retries,
            ) as client:
                response = client.chat(prompt)
        except Exception as exc:
            raise ProviderError(f"GigaChat request failed: {exc}") from exc

        content = self._extract_content(response)
        logger.info("gigachat_raw_response model=%s content=%s", self.model, content)

        parsed = self._parse_json_content(content)
        logger.info("gigachat_parsed_response model=%s payload=%s", self.model, parsed)
        return parsed

    @staticmethod
    def _extract_content(response: Any) -> str:
        try:
            return response.choices[0].message.content
        except Exception as exc:
            raise ProviderError("Unexpected GigaChat response schema") from exc

    @staticmethod
    def _parse_json_content(content: str) -> dict[str, Any]:
        normalized = content.strip()

        # Common model format: ```json ... ```
        fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", normalized, flags=re.DOTALL)
        if fence:
            normalized = fence.group(1).strip()

        parsed = _try_parse_dict(normalized)
        if parsed is not None:
            return parsed

        candidate = _extract_balanced_json_object(normalized)
        if candidate is not None:
            parsed = _try_parse_dict(candidate)
            if parsed is not None:
                return parsed

            repaired = _repair_json_like(candidate)
            parsed = _try_parse_dict(repaired)
            if parsed is not None:
                logger.warning("gigachat_json_repaired original=%s repaired=%s", candidate, repaired)
                return parsed

        preview = normalized[:280].replace("\n", "\\n")
        raise ProviderError(f"GigaChat returned non-JSON response: {preview}")


def _try_parse_dict(raw: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _extract_balanced_json_object(text: str) -> str | None:
    start = text.find("{")
    if start < 0:
        return None

    depth = 0
    in_string = False
    escape = False

    for idx in range(start, len(text)):
        char = text[idx]

        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : idx + 1]

    return text[start:]


def _repair_json_like(raw: str) -> str:
    repaired = raw.strip()

    repaired = _collapse_duplicate_braces(repaired)

    # Remove trailing commas before object/array end.
    repaired = re.sub(r",\s*([}\]])", r"\1", repaired)

    # Close unbalanced braces/brackets outside strings.
    stack: list[str] = []
    in_string = False
    escape = False

    for char in repaired:
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char in "[{":
            stack.append(char)
        elif char == "]" and stack and stack[-1] == "[":
            stack.pop()
        elif char == "}" and stack and stack[-1] == "{":
            stack.pop()

    while stack:
        opener = stack.pop()
        repaired += "]" if opener == "[" else "}"

    return repaired


def _collapse_duplicate_braces(text: str) -> str:
    out: list[str] = []
    in_string = False
    escape = False

    for char in text:
        if in_string:
            out.append(char)
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
            out.append(char)
            continue

        if char in "{}" and out and out[-1] == char:
            continue

        out.append(char)

    return "".join(out)
