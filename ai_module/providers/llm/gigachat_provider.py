import json
import re
from typing import Any

from ai_module.core.config import settings
from ai_module.core.errors import ProviderError
from ai_module.providers.llm.base import LLMProvider


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
        return self._parse_json_content(content)

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

        try:
            parsed = json.loads(normalized)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        # Fallback: extract first JSON object from mixed text.
        match = re.search(r"\{.*\}", normalized, flags=re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass

        raise ProviderError("GigaChat returned non-JSON response")
