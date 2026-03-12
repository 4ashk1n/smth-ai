import os

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except Exception:  # pragma: no cover - fallback for local bootstrap
    BaseSettings = object
    SettingsConfigDict = dict


if BaseSettings is object:
    class Settings:
        def __init__(self) -> None:
            self.app_name = os.getenv("APP_NAME", "smth-ai-module")
            self.app_env = os.getenv("APP_ENV", "dev")
            self.app_debug = os.getenv("APP_DEBUG", "true").lower() == "true"

            self.llm_provider = os.getenv("LLM_PROVIDER", "gigachat")
            self.llm_model = os.getenv("LLM_MODEL", "GigaChat")
            self.llm_timeout_seconds = float(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
            self.llm_max_retries = int(os.getenv("LLM_MAX_RETRIES", "2"))
            self.gigachat_credentials = os.getenv("GIGACHAT_CREDENTIALS", "")
            self.gigachat_scope = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
            self.gigachat_verify_ssl_certs = (
                os.getenv("GIGACHAT_VERIFY_SSL_CERTS", "true").lower() == "true"
            )
            self.gigachat_ca_bundle_file = os.getenv("GIGACHAT_CA_BUNDLE_FILE")
else:
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
            env_file=".env",
            env_file_encoding="utf-8",
            case_sensitive=False,
        )


settings = Settings()
