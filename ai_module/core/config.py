import os
from pathlib import Path

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except Exception:  # pragma: no cover - fallback for local bootstrap
    BaseSettings = object
    SettingsConfigDict = dict


if BaseSettings is object:
    ENV_FILE = Path(__file__).resolve().parents[1] / ".env"

    def _env(name: str, default: str = "") -> str:
        value = os.getenv(name)
        if value is not None:
            return value
        if ENV_FILE.exists():
            for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, raw = line.split("=", 1)
                if key.strip() == name:
                    return raw.strip().strip('"').strip("'")
        return default

    class Settings:
        def __init__(self) -> None:
            self.app_name = _env("APP_NAME", "smth-ai-module")
            self.app_env = _env("APP_ENV", "dev")
            self.app_debug = _env("APP_DEBUG", "true").lower() == "true"

            self.llm_provider = _env("LLM_PROVIDER", "gigachat")
            self.llm_model = _env("LLM_MODEL", "GigaChat")
            self.llm_timeout_seconds = float(_env("LLM_TIMEOUT_SECONDS", "30"))
            self.llm_max_retries = int(_env("LLM_MAX_RETRIES", "2"))
            self.gigachat_credentials = _env("GIGACHAT_CREDENTIALS", "")
            self.gigachat_scope = _env("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
            self.gigachat_verify_ssl_certs = (
                _env("GIGACHAT_VERIFY_SSL_CERTS", "true").lower() == "true"
            )
            ca_bundle = _env("GIGACHAT_CA_BUNDLE_FILE", "")
            self.gigachat_ca_bundle_file = ca_bundle or None
else:
    ENV_FILE = Path(__file__).resolve().parents[1] / ".env"

    class Settings(BaseSettings):
        app_name: str = "smth-ai-module"
        app_env: str = "dev"
        app_debug: bool = True

        llm_provider: str = "gigachat"
        llm_model: str = "GigaChat"
        llm_timeout_seconds: float = 30.0
        llm_max_retries: int = 2
        gigachat_credentials: str = ""
        gigachat_scope: str = "GIGACHAT_API_PERS"
        gigachat_verify_ssl_certs: bool = True
        gigachat_ca_bundle_file: str | None = None

        model_config = SettingsConfigDict(
            env_file=str(ENV_FILE),
            env_file_encoding="utf-8",
            case_sensitive=False,
        )


settings = Settings()
