import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_MAX_BYTES = 5 * 1024 * 1024
_BACKUP_COUNT = 5


def _make_rotating_file_handler(path: Path, handler_name: str) -> RotatingFileHandler:
    handler = RotatingFileHandler(
        filename=path,
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.set_name(handler_name)
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT, _DATE_FORMAT))
    return handler


def _ensure_handler(logger: logging.Logger, handler: logging.Handler) -> None:
    target_name = handler.get_name()
    for existing in logger.handlers:
        if existing.get_name() == target_name:
            return
    logger.addHandler(handler)


def _ensure_console_handler(logger: logging.Logger) -> None:
    for existing in logger.handlers:
        if existing.get_name() == "console":
            return

    console = logging.StreamHandler()
    console.set_name("console")
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(_LOG_FORMAT, _DATE_FORMAT))
    logger.addHandler(console)


def configure_logging() -> None:
    logs_dir = Path(__file__).resolve().parents[1] / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    app_logger = logging.getLogger("ai_module")
    app_logger.setLevel(logging.INFO)
    app_logger.propagate = False
    _ensure_console_handler(app_logger)
    _ensure_handler(
        app_logger,
        _make_rotating_file_handler(logs_dir / "app.log", "file:app"),
    )

    api_logger = logging.getLogger("ai_module.api")
    api_logger.setLevel(logging.INFO)
    api_logger.propagate = True
    _ensure_handler(
        api_logger,
        _make_rotating_file_handler(logs_dir / "api.log", "file:api"),
    )

    llm_logger = logging.getLogger("ai_module.llm")
    llm_logger.setLevel(logging.INFO)
    llm_logger.propagate = True
    _ensure_handler(
        llm_logger,
        _make_rotating_file_handler(logs_dir / "llm.log", "file:llm"),
    )

    httpx_logger = logging.getLogger("httpx")
    httpx_logger.setLevel(logging.INFO)
    httpx_logger.propagate = False
    _ensure_handler(
        httpx_logger,
        _make_rotating_file_handler(logs_dir / "httpx.log", "file:httpx"),
    )
