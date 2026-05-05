import os
from pathlib import Path

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except Exception: 
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
            self.database_url = _env("DATABASE_URL", "")
            self.reco_top_k = int(_env("RECO_TOP_K", "100"))
            self.reco_lookback_days = int(_env("RECO_LOOKBACK_DAYS", "180"))
            self.reco_half_life_days = float(_env("RECO_HALF_LIFE_DAYS", "30"))
            self.reco_max_items_per_user = int(_env("RECO_MAX_ITEMS_PER_USER", "200"))
            self.reco_neighbors_per_item = int(_env("RECO_NEIGHBORS_PER_ITEM", "100"))
            self.reco_min_score = float(_env("RECO_MIN_SCORE", "0"))
            self.reco_weight_cf = float(_env("RECO_WEIGHT_CF", "0.5"))
            self.reco_weight_category = float(_env("RECO_WEIGHT_CATEGORY", "0.25"))
            self.reco_weight_freshness = float(_env("RECO_WEIGHT_FRESHNESS", "0.15"))
            self.reco_weight_popularity = float(_env("RECO_WEIGHT_POPULARITY", "0.1"))
            self.reco_freshness_half_life_days = float(_env("RECO_FRESHNESS_HALF_LIFE_DAYS", "14"))
            self.reco_dirty_batch_size = int(_env("RECO_DIRTY_BATCH_SIZE", "200"))
            self.reco_dirty_poll_interval_seconds = float(_env("RECO_DIRTY_POLL_INTERVAL_SECONDS", "5"))
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
        database_url: str = ""
        reco_top_k: int = 100
        reco_lookback_days: int = 180
        reco_half_life_days: float = 30.0
        reco_max_items_per_user: int = 200
        reco_neighbors_per_item: int = 100
        reco_min_score: float = 0.0
        reco_weight_cf: float = 0.5
        reco_weight_category: float = 0.25
        reco_weight_freshness: float = 0.15
        reco_weight_popularity: float = 0.1
        reco_freshness_half_life_days: float = 14.0
        reco_dirty_batch_size: int = 200
        reco_dirty_poll_interval_seconds: float = 5.0

        model_config = SettingsConfigDict(
            env_file=str(ENV_FILE),
            env_file_encoding="utf-8",
            case_sensitive=False,
        )


settings = Settings()



